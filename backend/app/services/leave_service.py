"""
Leave Service
Business logic for leave management
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import date, datetime, timedelta
from typing import List, Dict

from app.repositories.leave_repository import LeaveRepository
from app.repositories.attendance_repository import AttendanceRepository
from app.models.models import Employee, UserRole

class LeaveService:
    """Handles leave management business logic"""
    
    def __init__(self, db: Session):
        self.db = db
        self.leave_repo = LeaveRepository(db)
        self.attendance_repo = AttendanceRepository(db)
    
    def create_leave_type(self, type_data: dict) -> Dict:
        """
        Create new leave type
        
        Args:
            type_data: Leave type information
            
        Returns:
            Success message
            
        Raises:
            HTTPException: If leave type already exists
        """
        existing = self.leave_repo.get_leave_type_by_name(type_data['name'])
        if existing:
            raise HTTPException(status_code=400, detail="Leave type already exists")
        
        self.leave_repo.create_leave_type(type_data)
        self.leave_repo.commit()
        
        return {"message": f"Leave type {type_data['name']} created"}
    
    def get_active_leave_types(self) -> List:
        """Get all active leave types"""
        return self.leave_repo.get_active_leave_types()
    
    def get_employee_balances(self, emp_id: str, year: int = None) -> List:
        """
        Get leave balances for employee
        
        Args:
            emp_id: Employee ID
            year: Year (defaults to current year)
            
        Returns:
            List of leave balances
        """
        if year is None:
            year = datetime.now().year
        
        balances = self.leave_repo.get_balances_by_emp(emp_id, year)
        
        # Initialize balances if they don't exist
        if not balances:
            balances = self._initialize_balances(emp_id, year)
        
        return balances
    
    def _initialize_balances(self, emp_id: str, year: int) -> List:
        """Initialize leave balances for employee"""
        types = self.leave_repo.get_active_leave_types()
        
        for leave_type in types:
            balance_data = {
                "emp_id": emp_id,
                "leave_type_id": leave_type.id,
                "year": year,
                "allocated": leave_type.annual_quota,
                "used": 0
            }
            self.leave_repo.create_balance(balance_data)
        
        self.leave_repo.commit()
        return self.leave_repo.get_balances_by_emp(emp_id, year)
    
    def apply_leave(self, user: Employee, leave_data: dict) -> Dict:
        """
        Apply for leave
        
        Args:
            user: Employee applying for leave
            leave_data: Leave application data
            
        Returns:
            Success message
            
        Raises:
            HTTPException: If validation fails
        """
        start_date = leave_data['start_date']
        end_date = leave_data['end_date']
        leave_type_id = leave_data['leave_type_id']
        reason = leave_data['reason']
        
        # Validation
        self._validate_leave_dates(start_date, end_date)
        
        # Calculate work days
        work_days = self._calculate_work_days(start_date, end_date)
        if work_days <= 0:
            raise HTTPException(
                status_code=400,
                detail="Requested range contains no work days"
            )
        
        # Check for overlaps
        overlap = self.leave_repo.get_overlapping_requests(user.emp_id, start_date, end_date)
        if overlap:
            raise HTTPException(
                status_code=400,
                detail="You already have a leave request overlapping these dates"
            )
        
        # Check balance
        year = start_date.year
        balance = self.leave_repo.get_balance(user.emp_id, leave_type_id, year)
        
        if not balance:
            # Initialize balance
            leave_type = self.leave_repo.get_leave_type_by_id(leave_type_id)
            if not leave_type:
                raise HTTPException(status_code=404, detail="Leave type not found")
            
            balance_data = {
                "emp_id": user.emp_id,
                "leave_type_id": leave_type.id,
                "year": year,
                "allocated": leave_type.annual_quota,
                "used": 0
            }
            balance = self.leave_repo.create_balance(balance_data)
            self.leave_repo.flush()
        
        # Check sufficient balance
        available = balance.allocated - balance.used
        if available < work_days:
            leave_type = self.leave_repo.get_leave_type_by_id(leave_type_id)
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient balance. Requested: {work_days}, Available: {available} ({leave_type.name if leave_type else 'Unknown'})"
            )
        
        # Create request
        is_super_admin = user.role == UserRole.SUPER_ADMIN
        request_data = {
            "emp_id": user.emp_id,
            "leave_type_id": leave_type_id,
            "start_date": start_date,
            "end_date": end_date,
            "total_days": work_days,
            "reason": reason,
            "status": "APPROVED" if is_super_admin else "PENDING"
        }
        
        new_request = self.leave_repo.create_request(request_data)
        
        # Auto-approve for super admin
        if is_super_admin:
            self.leave_repo.update_balance_used(balance, work_days)
            self.leave_repo.flush()
            self._sync_attendance_on_approval(new_request)
            self.leave_repo.commit()
            return {"message": "Leave applied and auto-approved for Super Admin"}
        
        self.leave_repo.commit()
        return {"message": "Leave application submitted successfully"}
    
    def get_my_requests(self, emp_id: str) -> List:
        """Get all leave requests for employee"""
        return self.leave_repo.get_requests_by_emp(emp_id)
    
    def get_pending_requests_for_hr(self) -> List:
        """Get pending requests for HR approval"""
        return self.leave_repo.get_pending_requests()
    
    def get_pending_requests_for_ceo(self) -> List:
        """Get requests pending CEO approval"""
        return self.leave_repo.get_hr_approved_requests()
    
    def approve_by_hr(self, request_id: int, hr: Employee, action: str, remarks: str = None) -> Dict:
        """
        HR approval/rejection
        
        Args:
            request_id: Leave request ID
            hr: HR employee
            action: APPROVE or REJECT
            remarks: Optional remarks
            
        Returns:
            Success message
        """
        request = self.leave_repo.get_request_by_id(request_id)
        if not request or request.status != "PENDING":
            raise HTTPException(status_code=404, detail="Pending request not found")
        
        if action == "APPROVE":
            self.leave_repo.update_request_status(request, "APPROVED_BY_HR")
            message = "Leave request forwarded to CEO for final approval"
        else:
            self.leave_repo.update_request_status(request, "REJECTED")
            message = "Leave request rejected by HR"
        
        # Log approval action
        log_data = {
            "request_id": request_id,
            "approver_id": hr.emp_id,
            "action": action,
            "remarks": remarks
        }
        self.leave_repo.create_approval_log(log_data)
        self.leave_repo.commit()
        
        return {"message": message}
    
    def approve_by_ceo(self, request_id: int, ceo: Employee, action: str, remarks: str = None) -> Dict:
        """
        CEO final approval/rejection
        
        Args:
            request_id: Leave request ID
            ceo: CEO employee
            action: APPROVE or REJECT
            remarks: Optional remarks
            
        Returns:
            Success message
        """
        request = self.leave_repo.get_request_by_id(request_id)
        if not request or request.status != "APPROVED_BY_HR":
            raise HTTPException(status_code=404, detail="HR-approved request not found")
        
        if action == "APPROVE":
            self.leave_repo.update_request_status(request, "APPROVED")
            
            # Update balance
            year = request.start_date.year
            balance = self.leave_repo.get_balance(request.emp_id, request.leave_type_id, year)
            if balance:
                self.leave_repo.update_balance_used(balance, request.total_days)
            
            # Sync attendance
            self._sync_attendance_on_approval(request)
            message = "Leave request approved by CEO"
        else:
            self.leave_repo.update_request_status(request, "REJECTED")
            message = "Leave request rejected by CEO"
        
        # Log approval action
        log_data = {
            "request_id": request_id,
            "approver_id": ceo.emp_id,
            "action": action,
            "remarks": remarks
        }
        self.leave_repo.create_approval_log(log_data)
        self.leave_repo.commit()
        
        return {"message": message}
    
    def _validate_leave_dates(self, start_date: date, end_date: date) -> None:
        """Validate leave dates"""
        if start_date < date.today():
            raise HTTPException(status_code=400, detail="Cannot apply for leave in the past")
        
        if start_date > end_date:
            raise HTTPException(status_code=400, detail="Start date cannot be after end date")
    
    def _calculate_work_days(self, start: date, end: date) -> int:
        """Calculate work days (excluding weekends)"""
        days = 0
        curr = start
        while curr <= end:
            if curr.weekday() < 5:  # Monday to Friday
                days += 1
            curr += timedelta(days=1)
        return days
    
    def _sync_attendance_on_approval(self, request) -> None:
        """Mark attendance as 'On Leave' for approved dates"""
        curr = request.start_date
        while curr <= request.end_date:
            if curr.weekday() < 5:
                existing = self.attendance_repo.get_by_emp_and_date(request.emp_id, curr)
                
                if existing:
                    self.attendance_repo.update(existing, {"attendance_status": "On Leave"})
                else:
                    attendance_data = {
                        "emp_id": request.emp_id,
                        "date": curr,
                        "attendance_status": "On Leave",
                        "source_file": "LEAVE_MODULE"
                    }
                    self.attendance_repo.create(attendance_data)
            
            curr += timedelta(days=1)

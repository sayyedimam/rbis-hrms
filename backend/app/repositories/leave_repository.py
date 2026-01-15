"""
Leave Repository
Database access layer for Leave-related models
"""
from sqlalchemy.orm import Session
from app.models.models import LeaveType, LeaveBalance, LeaveRequest, LeaveApprovalLog
from typing import List, Optional
from datetime import date

class LeaveRepository:
    """Handles all database operations for Leave models"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # LeaveType operations
    def get_leave_type_by_id(self, type_id: int) -> Optional[LeaveType]:
        """Get leave type by ID"""
        return self.db.query(LeaveType).filter(LeaveType.id == type_id).first()
    
    def get_leave_type_by_name(self, name: str) -> Optional[LeaveType]:
        """Get leave type by name"""
        return self.db.query(LeaveType).filter(LeaveType.name == name).first()
    
    def get_active_leave_types(self) -> List[LeaveType]:
        """Get all active leave types"""
        return self.db.query(LeaveType).filter(LeaveType.is_active == True).all()
    
    def create_leave_type(self, type_data: dict) -> LeaveType:
        """Create new leave type"""
        leave_type = LeaveType(**type_data)
        self.db.add(leave_type)
        return leave_type
    
    # LeaveBalance operations
    def get_balance(self, emp_id: str, leave_type_id: int, year: int) -> Optional[LeaveBalance]:
        """Get leave balance for employee"""
        return self.db.query(LeaveBalance).filter(
            LeaveBalance.emp_id == emp_id,
            LeaveBalance.leave_type_id == leave_type_id,
            LeaveBalance.year == year
        ).first()
    
    def get_balances_by_emp(self, emp_id: str, year: int) -> List[LeaveBalance]:
        """Get all leave balances for employee in a year"""
        return self.db.query(LeaveBalance).filter(
            LeaveBalance.emp_id == emp_id,
            LeaveBalance.year == year
        ).all()
    
    def create_balance(self, balance_data: dict) -> LeaveBalance:
        """Create new leave balance"""
        balance = LeaveBalance(**balance_data)
        self.db.add(balance)
        return balance
    
    def update_balance_used(self, balance: LeaveBalance, days: int) -> LeaveBalance:
        """Update used days in balance"""
        balance.used += days
        return balance
    
    # LeaveRequest operations
    def get_request_by_id(self, request_id: int) -> Optional[LeaveRequest]:
        """Get leave request by ID"""
        return self.db.query(LeaveRequest).filter(LeaveRequest.id == request_id).first()
    
    def get_requests_by_emp(self, emp_id: str) -> List[LeaveRequest]:
        """Get all leave requests for employee"""
        return self.db.query(LeaveRequest).filter(
            LeaveRequest.emp_id == emp_id
        ).order_by(LeaveRequest.created_at.desc()).all()

    def get_all_requests(self, limit: int = 50) -> List[LeaveRequest]:
        """Get all leave requests across system, ordered by date"""
        return self.db.query(LeaveRequest).order_by(
            LeaveRequest.created_at.desc()
        ).limit(limit).all()
    
    def get_overlapping_requests(
        self,
        emp_id: str,
        start_date: date,
        end_date: date
    ) -> Optional[LeaveRequest]:
        """Check for overlapping leave requests"""
        return self.db.query(LeaveRequest).filter(
            LeaveRequest.emp_id == emp_id,
            LeaveRequest.status != "REJECTED",
            LeaveRequest.status != "CANCELLED",
            ((LeaveRequest.start_date <= end_date) & (LeaveRequest.end_date >= start_date))
        ).first()
    
    def get_pending_requests(self) -> List[LeaveRequest]:
        """Get all pending leave requests"""
        return self.db.query(LeaveRequest).filter(LeaveRequest.status == "PENDING").all()
    
    def get_hr_approved_requests(self) -> List[LeaveRequest]:
        """Get requests approved by HR (pending CEO approval)"""
        return self.db.query(LeaveRequest).filter(
            LeaveRequest.status == "APPROVED_BY_HR"
        ).all()
    
    def create_request(self, request_data: dict) -> LeaveRequest:
        """Create new leave request"""
        request = LeaveRequest(**request_data)
        self.db.add(request)
        return request
    
    def update_request_status(self, request: LeaveRequest, status: str) -> LeaveRequest:
        """Update leave request status"""
        request.status = status
        return request
    
    # LeaveApprovalLog operations
    def create_approval_log(self, log_data: dict) -> LeaveApprovalLog:
        """Create approval log entry"""
        log = LeaveApprovalLog(**log_data)
        self.db.add(log)
        return log
    
    def flush(self) -> None:
        """Flush changes"""
        self.db.flush()
    
    def commit(self) -> None:
        """Commit transaction"""
        self.db.commit()
    
    def rollback(self) -> None:
        """Rollback transaction"""
        self.db.rollback()

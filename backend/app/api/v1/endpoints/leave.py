"""
Leave Management Endpoints (API v1)
Handles leave types, balances, applications, and approvals
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from typing import Optional, Dict, List

from app.api.dependencies import get_db, get_current_user, check_hr, check_ceo
from app.services.leave_service import LeaveService
from app.models.models import Employee
from app.utils.file_utils import normalize_emp_id

router = APIRouter()

# --- Pydantic Schemas ---
class LeaveTypeCreate(BaseModel):
    """Schema for creating leave type"""
    name: str
    annual_quota: int
    is_paid: bool = True
    allow_carry_forward: bool = False

class LeaveApplyRequest(BaseModel):
    """Schema for leave application"""
    leave_type_id: int
    start_date: date
    end_date: date
    reason: str

class ApprovalAction(BaseModel):
    """Schema for approval action"""
    request_id: int
    action: str  # APPROVE or REJECT
    remarks: Optional[str] = None

class HolidayCreate(BaseModel):
    """Schema for creating a holiday"""
    name: str
    date: date

class HolidayUpdate(BaseModel):
    """Schema for updating a holiday"""
    name: Optional[str] = None
    date: Optional[date] = None

# --- Holiday Endpoints ---

@router.get("/holidays", tags=["General"])
def get_holidays(
    year: int = date.today().year,
    db: Session = Depends(get_db)
):
    """Get list of holidays"""
    from app.models.models import Holiday
    holidays = db.query(Holiday).filter(Holiday.year == year).order_by(Holiday.date).all()
    return holidays

@router.post("/holidays", tags=["Admin/HR"])
def add_holiday(
    data: HolidayCreate,
    hr: Employee = Depends(check_hr),
    db: Session = Depends(get_db)
):
    """Add new holiday (Admin/HR Only)"""
    service = LeaveService(db)
    return service.add_holiday(data.dict())

@router.put("/holidays/{id}", tags=["Admin/HR"])
def update_holiday(
    id: int,
    data: HolidayUpdate,
    hr: Employee = Depends(check_hr),
    db: Session = Depends(get_db)
):
    """Update holiday (Admin/HR Only)"""
    service = LeaveService(db)
    return service.edit_holiday(id, data.dict(exclude_unset=True))

@router.delete("/holidays/{id}", tags=["Admin/HR"])
def delete_holiday(
    id: int,
    hr: Employee = Depends(check_hr),
    db: Session = Depends(get_db)
):
    """Delete holiday (Admin/HR Only)"""
    service = LeaveService(db)
    return service.remove_holiday(id)


# --- Leave Type Endpoints ---

@router.post("/types", tags=["Admin/HR"])
def create_leave_type(
    data: LeaveTypeCreate,
    hr: Employee = Depends(check_hr),
    db: Session = Depends(get_db)
):
    """
    Create new leave type
    
    - Creates new leave type with quota
    - Requires HR or Admin role
    - Returns success message
    """
    service = LeaveService(db)
    return service.create_leave_type(data.dict())

@router.get("/types")
def get_leave_types(
    user: Employee = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all active leave types
    
    - Returns list of available leave types
    - Accessible to all authenticated users
    """
    service = LeaveService(db)
    return service.get_active_leave_types()

# --- Leave Balance Endpoints ---

@router.get("/balances")
def get_my_balances(
    user: Employee = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get my leave balances
    
    - Returns current year leave balances
    - Auto-initializes if not exists
    - Shows allocated and used days
    """
    service = LeaveService(db)
    return service.get_employee_balances(user.emp_id)

# --- Leave Application Endpoints ---

@router.post("/apply")
def apply_leave(
    data: LeaveApplyRequest,
    user: Employee = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Apply for leave
    
    - Validates dates and balance
    - Checks for overlaps
    - Auto-approves for Super Admin
    - Creates pending request for others
    """
    service = LeaveService(db)
    return service.apply_leave(user, data.dict())

@router.get("/my-requests")
def get_my_requests(
    user: Employee = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get my leave requests
    
    - Returns all leave requests for current user
    - Ordered by most recent first
    """
    service = LeaveService(db)
    return service.get_my_requests(user.emp_id)

# --- HR Approval Endpoints ---

@router.get("/hr/pending", tags=["HR"])
def get_hr_pending(
    hr: Employee = Depends(check_hr),
    db: Session = Depends(get_db)
):
    """
    Get pending requests for HR approval
    
    - Returns all PENDING leave requests
    - Requires HR or Admin role
    """
    service = LeaveService(db)
    return service.get_pending_requests_for_hr()

@router.post("/approve-hr", tags=["HR"])
def approve_by_hr(
    data: ApprovalAction,
    hr: Employee = Depends(check_hr),
    db: Session = Depends(get_db)
):
    """
    HR approval/rejection
    
    - Approves: Forwards to CEO
    - Rejects: Marks as rejected
    - Logs approval action
    - Requires HR or Admin role
    """
    service = LeaveService(db)
    return service.approve_by_hr(data.request_id, hr, data.action, data.remarks)

# --- CEO Approval Endpoints ---

@router.get("/ceo/pending", tags=["CEO"])
def get_ceo_pending(
    ceo: Employee = Depends(check_ceo),
    db: Session = Depends(get_db)
):
    """
    Get requests pending CEO approval
    
    - Returns requests approved by HR
    - Requires CEO or Admin role
    """
    service = LeaveService(db)
    return service.get_pending_requests_for_ceo()

@router.post("/approve-ceo", tags=["CEO"])
def approve_by_ceo(
    data: ApprovalAction,
    ceo: Employee = Depends(check_ceo),
    db: Session = Depends(get_db)
):
    """
    CEO final approval/rejection
    
    - Approves: Updates balance, syncs attendance
    - Rejects: Marks as rejected
    - Logs approval action
    - Requires CEO or Admin role
    """
    service = LeaveService(db)
    return service.approve_by_ceo(data.request_id, ceo, data.action, data.remarks)

# --- Admin/HR Specific Endpoints ---

@router.get("/admin/summary", tags=["Admin/HR"])
def get_general_leave_summary(
    admin: Employee = Depends(check_hr),
    db: Session = Depends(get_db)
):
    """
    Get general leave summary (recent 5 requests)
    - Used by Leave Explorer for initial view
    """
    service = LeaveService(db)
    return service.get_employee_summary()

@router.get("/admin/employee-summary/{emp_id}", tags=["Admin/HR"])
def get_employee_leave_summary(
    emp_id: str,
    admin: Employee = Depends(check_hr),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive leave summary for an employee
    
    - Requires HR or Admin role
    - Used by Leave Explorer
    """
    service = LeaveService(db)
    normalized_id = normalize_emp_id(emp_id)
    return service.get_employee_summary(normalized_id)

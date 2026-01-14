"""
Leave Management Endpoints (API v1)
Handles leave types, balances, applications, and approvals
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import date

from app.api.dependencies import get_db, get_current_user, check_hr, check_ceo
from app.services.leave_service import LeaveService
from app.models.models import Employee

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

# --- Leave Type Endpoints ---

@router.post("/types", tags=["Admin/HR"])
async def create_leave_type(
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
async def get_leave_types(
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
async def get_my_balances(
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
async def apply_leave(
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
async def get_my_requests(
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
async def get_hr_pending(
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
async def approve_by_hr(
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
async def get_ceo_pending(
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
async def approve_by_ceo(
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

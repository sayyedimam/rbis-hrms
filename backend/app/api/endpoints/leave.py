from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime, timedelta
from app.core.database import get_db
from app.api.deps import get_current_user, check_hr, check_ceo
from app.models.models import (
    Employee, LeaveType, LeaveBalance, LeaveRequest, 
    LeaveApprovalLog, Attendance, UserRole
)
from pydantic import BaseModel

router = APIRouter()

# --- Pydantic Schemas ---
class LeaveTypeCreate(BaseModel):
    name: str
    annual_quota: int
    is_paid: bool = True
    allow_carry_forward: bool = False

class LeaveApplyRequest(BaseModel):
    leave_type_id: int
    start_date: date
    end_date: date
    reason: str

class ApprovalAction(BaseModel):
    request_id: int
    action: str # APPROVE or REJECT
    remarks: Optional[str] = None

# --- Helper Functions ---
def calculate_work_days(start: date, end: date) -> int:
    """Simple calculation of days (inclusive) excluding weekends."""
    days = 0
    curr = start
    while curr <= end:
        if curr.weekday() < 5: # Monday to Friday
            days += 1
        curr += timedelta(days=1)
    return days

def sync_attendance_on_approval(db: Session, request: LeaveRequest):
    """Marks attendance status as 'On Leave' for the approved range."""
    curr = request.start_date
    while curr <= request.end_date:
        if curr.weekday() < 5:
            # Check if record exists
            existing = db.query(Attendance).filter(
                Attendance.emp_id == request.emp_id, 
                Attendance.date == curr
            ).first()
            
            if existing:
                existing.attendance_status = "On Leave"
            else:
                new_att = Attendance(
                    emp_id=request.emp_id,
                    date=curr,
                    attendance_status="On Leave",
                    source_file="LEAVE_MODULE"
                )
                db.add(new_att)
        curr += timedelta(days=1)

# --- Endpoints ---

@router.post("/types", tags=["Admin/HR"])
async def create_leave_type(data: LeaveTypeCreate, db: Session = Depends(get_db), hr: Employee = Depends(check_hr)):
    existing = db.query(LeaveType).filter(LeaveType.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Leave type already exists")
    
    new_type = LeaveType(**data.dict())
    db.add(new_type)
    db.commit()
    return {"message": f"Leave type {data.name} created"}

@router.get("/types")
async def get_leave_types(db: Session = Depends(get_db), user: Employee = Depends(get_current_user)):
    return db.query(LeaveType).filter(LeaveType.is_active == True).all()

@router.get("/balances")
async def get_my_balances(db: Session = Depends(get_db), user: Employee = Depends(get_current_user)):
    year = datetime.now().year
    balances = db.query(LeaveBalance).filter(
        LeaveBalance.emp_id == user.emp_id,
        LeaveBalance.year == year
    ).all()
    
    # If no balances exist, initialize them from LeaveTypes
    if not balances:
        types = db.query(LeaveType).filter(LeaveType.is_active == True).all()
        for t in types:
            bal = LeaveBalance(
                emp_id=user.emp_id,
                leave_type_id=t.id,
                year=year,
                allocated=t.annual_quota,
                used=0
            )
            db.add(bal)
        db.commit()
        balances = db.query(LeaveBalance).filter(
            LeaveBalance.emp_id == user.emp_id,
            LeaveBalance.year == year
        ).all()
        
    return balances

@router.post("/apply")
async def apply_leave(data: LeaveApplyRequest, db: Session = Depends(get_db), user: Employee = Depends(get_current_user)):
    # 1. Validation
    if data.start_date < date.today():
        raise HTTPException(status_code=400, detail="Cannot apply for leave in the past")

    if data.start_date > data.end_date:
        raise HTTPException(status_code=400, detail="Start date cannot be after end date")
    
    work_days = calculate_work_days(data.start_date, data.end_date)
    if work_days <= 0:
        raise HTTPException(status_code=400, detail="Requested range contains no work days")

    # 2. Check Overlap
    overlap = db.query(LeaveRequest).filter(
        LeaveRequest.emp_id == user.emp_id,
        LeaveRequest.status != "REJECTED",
        LeaveRequest.status != "CANCELLED",
        ((LeaveRequest.start_date <= data.end_date) & (LeaveRequest.end_date >= data.start_date))
    ).first()
    if overlap:
        raise HTTPException(status_code=400, detail="You already have a leave request overlapping these dates")

    # 3. Check Balance
    year = data.start_date.year
    balance = db.query(LeaveBalance).filter(
        LeaveBalance.emp_id == user.emp_id,
        LeaveBalance.leave_type_id == data.leave_type_id,
        LeaveBalance.year == year
    ).first()
    
    if not balance:
        # Try to init
        ltype = db.query(LeaveType).get(data.leave_type_id)
        if not ltype: raise HTTPException(status_code=404, detail="Leave type not found")
        balance = LeaveBalance(emp_id=user.emp_id, leave_type_id=ltype.id, year=year, allocated=ltype.annual_quota, used=0)
        db.add(balance)
        db.flush()

    if (balance.allocated - balance.used) < work_days:
        ltype = db.query(LeaveType).get(data.leave_type_id)
        if ltype and ltype.is_paid:
            raise HTTPException(status_code=400, detail="Insufficient leave balance")

    # 4. Save Request
    is_super = user.role == UserRole.SUPER_ADMIN
    new_req = LeaveRequest(
        emp_id=user.emp_id,
        leave_type_id=data.leave_type_id,
        start_date=data.start_date,
        end_date=data.end_date,
        total_days=work_days,
        reason=data.reason,
        status="APPROVED" if is_super else "PENDING"
    )
    db.add(new_req)
    
    if is_super:
        balance.used += work_days
        db.flush() # Ensure request has an ID if needed by sync
        sync_attendance_on_approval(db, new_req)
        db.commit()
        return {"message": "Leave applied and auto-approved for Super Admin"}

    db.commit()
    return {"message": "Leave application submitted successfully"}

@router.get("/my-requests")
async def get_my_requests(db: Session = Depends(get_db), user: Employee = Depends(get_current_user)):
    return db.query(LeaveRequest).filter(LeaveRequest.emp_id == user.emp_id).order_by(LeaveRequest.created_at.desc()).all()

# --- Approval Workflow ---

@router.get("/hr/pending", tags=["HR"])
async def get_hr_pending(db: Session = Depends(get_db), hr: Employee = Depends(check_hr)):
    return db.query(LeaveRequest).filter(LeaveRequest.status == "PENDING").all()

@router.get("/ceo/pending", tags=["CEO"])
async def get_ceo_pending(db: Session = Depends(get_db), ceo: Employee = Depends(check_ceo)):
    return db.query(LeaveRequest).filter(LeaveRequest.status == "APPROVED_BY_HR").all()

@router.post("/approve-hr", tags=["HR"])
async def approve_by_hr(data: ApprovalAction, db: Session = Depends(get_db), hr: Employee = Depends(check_hr)):
    req = db.query(LeaveRequest).get(data.request_id)
    if not req or req.status != "PENDING":
        raise HTTPException(status_code=404, detail="Pending request not found")
    
    if data.action == "APPROVE":
        req.status = "APPROVED_BY_HR"
        req.hr_remarks = data.remarks
    else:
        req.status = "REJECTED"
        req.hr_remarks = data.remarks
    
    log = LeaveApprovalLog(request_id=req.id, approver_id=hr.emp_id, action=f"HR_{data.action}", remarks=data.remarks)
    db.add(log)
    db.commit()
    return {"message": f"Request {data.action}ed by HR"}

@router.post("/approve-ceo", tags=["CEO"])
async def approve_by_ceo(data: ApprovalAction, db: Session = Depends(get_db), ceo: Employee = Depends(check_ceo)):
    req = db.query(LeaveRequest).get(data.request_id)
    if not req or req.status != "APPROVED_BY_HR":
        raise HTTPException(status_code=404, detail="Request awaiting CEO approval not found")
    
    if data.action == "APPROVE":
        req.status = "APPROVED"
        req.ceo_remarks = data.remarks
        
        # 1. Update Balance
        balance = db.query(LeaveBalance).filter(
            LeaveBalance.emp_id == req.emp_id,
            LeaveBalance.leave_type_id == req.leave_type_id,
            LeaveBalance.year == req.start_date.year
        ).first()
        if balance:
            balance.used += req.total_days
            
        # 2. Sync Attendance
        sync_attendance_on_approval(db, req)
        
    else:
        req.status = "REJECTED"
        req.ceo_remarks = data.remarks
    
    log = LeaveApprovalLog(request_id=req.id, approver_id=ceo.emp_id, action=f"CEO_{data.action}", remarks=data.remarks)
    db.add(log)
    db.commit()
    return {"message": f"Request {data.action}ed by CEO"}

# --- Admin/CEO Explorer ---

@router.get("/admin/employee-summary/{emp_id}", tags=["Admin/CEO"])
async def get_employee_leave_summary(emp_id: str, db: Session = Depends(get_db), admin: Employee = Depends(check_ceo)):
    # 1. Verify employee exists
    emp = db.query(Employee).filter(Employee.emp_id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    year = datetime.now().year
    
    # 2. Get Balances
    balances = db.query(LeaveBalance).filter(
        LeaveBalance.emp_id == emp_id,
        LeaveBalance.year == year
    ).all()
    
    # If no balances exist, initialize them (similar to get_my_balances)
    if not balances:
        types = db.query(LeaveType).filter(LeaveType.is_active == True).all()
        for t in types:
            bal = LeaveBalance(
                emp_id=emp_id,
                leave_type_id=t.id,
                year=year,
                allocated=t.annual_quota,
                used=0
            )
            db.add(bal)
        db.commit()
        balances = db.query(LeaveBalance).filter(
            LeaveBalance.emp_id == emp_id,
            LeaveBalance.year == year
        ).all()
        
    # 3. Get Requests
    requests = db.query(LeaveRequest).filter(
        LeaveRequest.emp_id == emp_id
    ).order_by(LeaveRequest.created_at.desc()).all()
    
    return {
        "employee": {
            "emp_id": emp.emp_id,
            "full_name": emp.full_name,
            "designation": emp.designation
        },
        "balances": balances,
        "history": requests
    }

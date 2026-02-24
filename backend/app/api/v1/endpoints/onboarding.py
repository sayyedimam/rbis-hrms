"""
Onboarding Endpoints (API v1)
Handles employee onboarding process
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api.dependencies import get_db, check_hr
from app.repositories.employee_repository import EmployeeRepository
from app.models.employee import Employee, UserStatus

router = APIRouter()

class OnboardingData(BaseModel):
    """Schema for onboarding"""
    emp_id: str
    full_name: str
    first_name: str
    last_name: str
    phone_number: str
    designation: str
    email: str

@router.get("/next-id")
def get_next_employee_id(
    hr: Employee = Depends(check_hr),
    db: Session = Depends(get_db)
):
    """
    Get next available employee ID
    """
    # Use a more direct SQL approach to find the max numeric part
    from sqlalchemy import func
    
    # Query all emp_ids that start with RBIS (case-insensitive)
    result = db.query(Employee.emp_id).filter(Employee.emp_id.ilike("RBIS%")).all()
    
    max_num = 0
    for row in result:
        emp_id = row[0]
        if emp_id and len(emp_id) > 4:
            try:
                # Strip 'RBIS' (case insensitive) and try to get the integer
                num_part = emp_id.upper().replace("RBIS", "").strip()
                # Handle cases like RBIS0061 (clean) or RBIS 0061 (with space)
                num = int(''.join(filter(str.isdigit, num_part)))
                if num > max_num:
                    max_num = num
            except (ValueError, TypeError):
                continue
    
    next_num = max_num + 1
    # Use 4 digits padding as standard
    next_id = f"RBIS{next_num:04d}"
    
    return {"next_id": next_id}

@router.get("/pending")
def get_pending_onboarding(
    hr: Employee = Depends(check_hr),
    db: Session = Depends(get_db)
):
    """
    Get employees pending onboarding
    """
    pending = db.query(Employee).filter(
        Employee.status == UserStatus.PENDING
    ).all()
    return pending

@router.post("/complete/{email}")
@router.post("/onboard")
def complete_onboarding(
    data: OnboardingData,
    email: str = None,
    hr: Employee = Depends(check_hr),
    db: Session = Depends(get_db)
):
    """
    Complete employee onboarding with robust validation
    
    Validation order:
    1. Employee ID must be unique
    2. Phone number must be unique
    3. Email is auto-generated if a same-name conflict exists
    """
    repo = EmployeeRepository(db)
    
    # ── Step 1: Validate Employee ID ──────────────────────────────────
    if repo.exists_by_emp_id(data.emp_id):
        raise HTTPException(
            status_code=400,
            detail=f"Employee ID '{data.emp_id}' already exists in the system."
        )
    
    # ── Step 2: Validate Phone Number ─────────────────────────────────
    existing_by_phone = repo.get_by_phone(data.phone_number)
    if existing_by_phone and existing_by_phone.status == UserStatus.ACTIVE:
        raise HTTPException(
            status_code=400,
            detail=f"Phone number '{data.phone_number}' is already registered to employee {existing_by_phone.full_name} ({existing_by_phone.emp_id})."
        )
    
    # ── Step 3: Determine Email ───────────────────────────────────────
    # Always auto-generate a work email based on first_name + last_name initial.
    # If the base email is taken (same-name scenario), auto-increment.
    target_email = generate_unique_email(data.first_name, data.last_name, repo)
    
    # ── Step 4: Check for existing PENDING employee by generated email ─
    employee = repo.get_by_email(target_email)
    
    if employee and employee.status == UserStatus.ACTIVE:
        # This shouldn't happen since generate_unique_email finds a free slot,
        # but guard against edge cases.
        raise HTTPException(
            status_code=400,
            detail=f"Employee with email {target_email} is already active."
        )
    
    if not employee:
        # Create new employee record
        employee_data = data.dict()
        employee_data["email"] = target_email
        employee_data["status"] = UserStatus.PENDING
        employee = repo.create(employee_data)
    
    # ── Step 5: Finalize Onboarding ───────────────────────────────────
    employee.emp_id = data.emp_id
    employee.full_name = data.full_name
    employee.first_name = data.first_name
    employee.last_name = data.last_name
    employee.phone_number = data.phone_number
    employee.designation = data.designation
    employee.email = target_email
    employee.status = UserStatus.ACTIVE
    
    repo.update(employee)
    
    return {
        "message": f"Onboarding successful for {data.full_name} ({data.emp_id})",
        "assigned_email": target_email
    }

def generate_unique_email(first, last, repo):
    """
    Generate a unique work email for an employee.
    
    Pattern: {firstname}{lastname_initial}@rbistech.com
    If taken: {firstname}{lastname_initial}01@rbistech.com, 02, 03...
    
    Examples:
      - First "Girish Pardeshi"  → girishp@rbistech.com
      - Second "Girish Pardeshi" → girishp01@rbistech.com
      - Third "Girish Pardeshi"  → girishp02@rbistech.com
    """
    base = f"{first.lower()}{last[0].lower()}"
    domain = "@rbistech.com"
    
    # Try base first
    candidate = f"{base}{domain}"
    if not repo.get_by_email(candidate):
        return candidate
        
    # Try counters 01, 02, ...
    counter = 1
    while counter < 100:
        candidate = f"{base}{counter:02d}{domain}"
        if not repo.get_by_email(candidate):
            return candidate
        counter += 1
    
    raise HTTPException(status_code=500, detail="Exhausted email generation attempts")


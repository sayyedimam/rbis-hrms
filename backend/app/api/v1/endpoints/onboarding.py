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
    
    - Generates next sequential RBIS ID
    - Requires HR role
    """
    # Get all existing emp_ids that start with RBIS
    employees = db.query(Employee).filter(
        Employee.emp_id.like("RBIS%")
    ).all()
    
    if not employees:
        return {"next_id": "RBIS0001"}
    
    # Extract numeric parts and find max
    max_num = 0
    for emp in employees:
        if emp.emp_id and emp.emp_id.startswith("RBIS"):
            try:
                num = int(emp.emp_id[4:])  # Get number after "RBIS"
                if num > max_num:
                    max_num = num
            except ValueError:
                continue
    
    # Generate next ID
    next_num = max_num + 1
    next_id = f"RBIS{next_num:04d}"
    
    return {"next_id": next_id}

@router.get("/pending")
def get_pending_onboarding(
    hr: Employee = Depends(check_hr),
    db: Session = Depends(get_db)
):
    """
    Get employees pending onboarding
    
    - Returns employees with PENDING status
    - Requires HR role
    """
    pending = db.query(Employee).filter(
        Employee.status == UserStatus.PENDING
    ).all()
    return pending

@router.post("/complete/{email}")
@router.post("/onboard") # Alias for frontend call
def complete_onboarding(
    data: OnboardingData,
    email: str = None, # Make email optional if using /onboard with data
    hr: Employee = Depends(check_hr),
    db: Session = Depends(get_db)
):
    """
    Complete employee onboarding
    
    - Assigns emp_id and details
    - Changes status to ACTIVE
    - Requires HR role
    """
    repo = EmployeeRepository(db)
    
    # If using /onboard, email might be in data? Let's check frontend.
    # Frontend sends full employee object.
    target_email = email or data.email.lower()
    
    # Check for existing employee by email
    employee = repo.get_by_email(target_email)
    
    if employee:
        # CRITICAL: Prevent overwriting ACTIVE employees
        if employee.status == UserStatus.ACTIVE:
            # Try alternate email format: first_name.last_name@rbistech.com
            alt_email = f"{data.first_name}.{data.last_name}@rbistech.com".lower()
            
            # If alternate is same as original (rare but possible), it's a hard conflict
            if alt_email == target_email:
                 raise HTTPException(
                    status_code=400,
                    detail=f"Email {target_email} already exists and is active. Please use a different email."
                )
            
            # Check if alternate email is also taken
            conflict_check = repo.get_by_email(alt_email)
            if conflict_check:
                raise HTTPException(
                    status_code=400,
                    detail=f"Both primary ({target_email}) and alternate ({alt_email}) emails are already taken."
                )
            
            # Switch to alternate email
            target_email = alt_email
            data.email = alt_email # Update input data
            employee = None # Treat as NEW employee
        # If employee is PENDING, we proceed to update (valid onboarding flow)

    if not employee:
        # Create new employee if they don't exist
        employee_data = data.dict()
        employee_data["email"] = target_email # Ensure email is set
        employee_data["status"] = UserStatus.PENDING # Initial status
        employee = repo.create(employee_data)
    
    # Check if emp_id already exists
    if repo.exists_by_emp_id(data.emp_id):
        raise HTTPException(
            status_code=400,
            detail="Employee ID already exists"
        )
    
    # Update employee
    employee.emp_id = data.emp_id
    employee.full_name = data.full_name
    employee.first_name = data.first_name
    employee.last_name = data.last_name
    employee.phone_number = data.phone_number
    employee.designation = data.designation
    employee.status = UserStatus.ACTIVE
    
    repo.update(employee)
    
    return {"message": "Onboarding completed successfully"}

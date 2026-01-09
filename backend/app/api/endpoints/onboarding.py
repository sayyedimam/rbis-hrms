from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import re
from app.core.database import get_db
from app.api.deps import check_admin
from app.models.models import Employee, UserRole, UserStatus
from app.schemas.schemas import OnboardRequest

router = APIRouter()

@router.get("/next-id")
async def get_next_id(db: Session = Depends(get_db), admin: Employee = Depends(check_admin)):
    employees = db.query(Employee).all()
    max_num = 0
    for e in employees:
        if not e.emp_id:
            continue
        # Extract numeric part regardless of prefix (as long as it contains RBIS)
        match = re.search(r'RBIS0*(\d+)', e.emp_id, re.IGNORECASE)
        if match:
            num = int(match.group(1))
            if num > max_num:
                max_num = num
    
    next_num = max_num + 1
    return {"next_id": f"RBIS{str(next_num).zfill(4)}"}

@router.post("/onboard")
async def onboard_employee(data: OnboardRequest, db: Session = Depends(get_db), admin: Employee = Depends(check_admin)):
    existing = db.query(Employee).filter((Employee.emp_id == data.emp_id) | (Employee.email == data.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Employee ID or Email already exists.")
    
    new_emp = Employee(
        emp_id=data.emp_id,
        first_name=data.first_name,
        last_name=data.last_name,
        full_name=data.full_name,
        phone_number=data.phone_number,
        email=data.email,
        designation=data.designation,
        role=UserRole.EMPLOYEE,
        status=UserStatus.ACTIVE
    )
    db.add(new_emp)
    db.commit()
    return {"message": f"Employee {data.full_name} onboarded successfully."}

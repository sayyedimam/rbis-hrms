from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.api.deps import check_admin
from app.models.models import Employee, UserRole, UserStatus
from pydantic import BaseModel

router = APIRouter()

class EmployeeUpdate(BaseModel):
    full_name: str
    designation: str
    emp_id: str
    email: str
    phone_number: Optional[str] = None

@router.get("/employees")
async def get_employees(
    db: Session = Depends(get_db),
    admin: Employee = Depends(check_admin)
):
    """Fetch all employees for management table."""
    return db.query(Employee).all()

@router.put("/employees/{id}")
async def update_employee(
    id: int,
    emp_data: EmployeeUpdate,
    db: Session = Depends(get_db),
    admin: Employee = Depends(check_admin)
):
    """Update employee details."""
    emp = db.query(Employee).filter(Employee.id == id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Check for conflicts with other employees
    conflict = db.query(Employee).filter(
        (Employee.id != id) & 
        ((Employee.emp_id == emp_data.emp_id) | (Employee.email == emp_data.email))
    ).first()
    
    if conflict:
        raise HTTPException(status_code=400, detail="Employee ID or Email already exists.")

    emp.full_name = emp_data.full_name
    emp.designation = emp_data.designation
    emp.emp_id = emp_data.emp_id
    emp.email = emp_data.email
    emp.phone_number = emp_data.phone_number
    
    db.commit()
    return {"message": "Employee updated successfully"}

@router.delete("/employees/{id}")
async def delete_employee(
    id: int,
    db: Session = Depends(get_db),
    admin: Employee = Depends(check_admin)
):
    """Remove employee from system."""
    emp = db.query(Employee).filter(Employee.id == id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    db.delete(emp)
    db.commit()
    return {"message": "Employee deleted successfully"}

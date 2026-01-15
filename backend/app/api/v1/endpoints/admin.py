"""
Admin Endpoints (API v1)
Handles employee management operations
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.api.dependencies import get_db, check_admin
from app.services.admin_service import AdminService
from app.models.models import Employee

router = APIRouter()

class EmployeeUpdate(BaseModel):
    """Schema for employee update"""
    full_name: Optional[str] = None
    designation: Optional[str] = None
    emp_id: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None

@router.get("/employees")
async def get_employees(
    admin: Employee = Depends(check_admin),
    db: Session = Depends(get_db)
):
    """
    Get all employees
    
    - Returns list of all employees
    - Requires admin/HR/CEO role
    """
    service = AdminService(db)
    return service.get_all_employees()

@router.put("/employees/{id}")
async def update_employee(
    id: int,
    emp_data: EmployeeUpdate,
    admin: Employee = Depends(check_admin),
    db: Session = Depends(get_db)
):
    """
    Update employee details
    
    - Updates employee information
    - HR cannot edit (CEO/Admin only)
    - Checks for conflicts
    """
    service = AdminService(db)
    update_dict = emp_data.dict(exclude_unset=True)
    return service.update_employee(id, update_dict, admin)

@router.delete("/employees/{id}")
async def delete_employee(
    id: int,
    admin: Employee = Depends(check_admin),
    db: Session = Depends(get_db)
):
    """
    Delete employee
    
    - Deletes employee from system
    - HR cannot delete (CEO/Admin only)
    """
    service = AdminService(db)
    return service.delete_employee(id, admin)

@router.get("/employees/template")
async def download_master_template(
    admin: Employee = Depends(check_admin),
    db: Session = Depends(get_db)
):
    """Download employee master Excel template"""
    from fastapi.responses import Response
    service = AdminService(db)
    template_bytes = service.generate_master_template()
    return Response(
        content=template_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=Employee_Master_Template.xlsx"}
    )

@router.post("/employees/upload")
async def upload_master(
    file: UploadFile = File(...),
    admin: Employee = Depends(check_admin),
    db: Session = Depends(get_db)
):
    """Upload completed employee master Excel"""
    service = AdminService(db)
    return await service.process_employee_master(file, admin)

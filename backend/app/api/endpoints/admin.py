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
    user: Employee = Depends(check_admin)
):
    """Update employee details."""
    if user.role == UserRole.HR:
        raise HTTPException(status_code=403, detail="HR cannot perform edit actions")

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
    user: Employee = Depends(check_admin)
):
    """Remove employee from system."""
    if user.role == UserRole.HR:
        raise HTTPException(status_code=403, detail="HR cannot perform delete actions")
    emp = db.query(Employee).filter(Employee.id == id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    db.delete(emp)
    db.commit()
    return {"message": "Employee deleted successfully"}

# --- Master Sync Features ---

from fastapi.responses import StreamingResponse
import pandas as pd
import io
from fastapi import UploadFile, File

@router.get("/employees/template")
async def get_template(
    admin: Employee = Depends(check_admin)
):
    """Generate and download Employee Master Excel Template."""
    columns = ['Emp ID', 'Full Name', 'Email', 'Phone', 'Designation', 'Role']
    df = pd.DataFrame(columns=columns)
    
    # Optional: Add a sample row to guide the user
    df.loc[0] = ['RBIS0001', 'John Doe', 'john.doe@example.com', '9876543210', 'Software Engineer', 'EMPLOYEE']
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Employee_Master')
        
        # Adjust column width
        worksheet = writer.sheets['Employee_Master']
        for idx, col in enumerate(columns):
            worksheet.set_column(idx, idx, 20)
            
    output.seek(0)
    
    headers = {
        'Content-Disposition': 'attachment; filename="Employee_Master_Template.xlsx"'
    }
    return StreamingResponse(output, headers=headers, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@router.post("/employees/upload")
async def upload_employee_master(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: Employee = Depends(check_admin)
):
    """Bulk upload/update employees from Excel."""
    if user.role == UserRole.HR:
        raise HTTPException(status_code=403, detail="HR cannot perform bulk upload")
    try:
        content = await file.read()
        df = pd.read_excel(io.BytesIO(content))
        
        # Normalize headers to lowercase for easier matching
        df.columns = [str(c).lower().strip() for c in df.columns]
        
        required_map = {
            'emp id': 'emp_id',
            'full name': 'full_name',
            'email': 'email',
            'phone': 'phone_number',
            'designation': 'designation',
            'role': 'role'
        }
        
        # Verify required columns exist
        missing = [col for col in required_map.keys() if col not in df.columns]
        if missing:
            raise HTTPException(status_code=400, detail=f"Missing columns: {', '.join(missing)}")
            
        success_count = 0
        updated_count = 0
        
        for _, row in df.iterrows():
            emp_id = str(row['emp id']).strip()
            if not emp_id or emp_id.lower() == 'nan': continue
            
            # Find existing or create new
            emp = db.query(Employee).filter(Employee.emp_id == emp_id).first()
            is_new = False
            
            if not emp:
                emp = Employee(emp_id=emp_id)
                db.add(emp)
                is_new = True
                
            # Update fields
            emp.full_name = str(row['full name']).strip()
            emp.email = str(row['email']).strip()
            
            phone = str(row['phone']).strip()
            if phone and phone.lower() != 'nan':
                emp.phone_number = phone
                
            desig = str(row['designation']).strip()
            if desig and desig.lower() != 'nan':
                emp.designation = desig
                
            role_val = str(row['role']).upper().strip()
            if role_val in ['EMPLOYEE', 'HR', 'CEO', 'SUPER_ADMIN']:
                emp.role = UserRole[role_val]
            else:
                 emp.role = UserRole.EMPLOYEE # Default
                 
            if is_new:
                # Set default password for new users? Or leave to regular signup?
                # For now we assume they might sign up later or we set a default.
                # If using this for bulk creation, we might need a default password.
                # Logic: If emp exists in master, they can 'signup' and claim it.
                pass
                
            if is_new: success_count += 1
            else: updated_count += 1
            
        db.commit()
        return {"message": f"Processed successfully: {success_count} new, {updated_count} updated."}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Upload failed: {str(e)}")

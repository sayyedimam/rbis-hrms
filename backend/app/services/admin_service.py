"""
Admin Service
Business logic for admin operations
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import List, Dict

from app.repositories.employee_repository import EmployeeRepository
from app.models.models import Employee, UserRole

class AdminService:
    """Handles admin operations business logic"""
    
    def __init__(self, db: Session):
        self.db = db
        self.employee_repo = EmployeeRepository(db)
    
    def get_all_employees(self) -> List[Employee]:
        """Get all employees"""
        return self.employee_repo.get_all()
    
    def update_employee(
        self,
        emp_id: int,
        update_data: Dict,
        admin: Employee
    ) -> Dict:
        """
        Update employee details
        
        Args:
            emp_id: Employee database ID
            update_data: Fields to update
            admin: Admin performing update
            
        Returns:
            Success message
            
        Raises:
            HTTPException: If validation fails
        """
        # HR cannot edit
        if admin.role == UserRole.HR:
            raise HTTPException(
                status_code=403,
                detail="HR cannot perform edit actions"
            )
        
        # Get employee
        employee = self.employee_repo.get_by_db_id(emp_id)
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        # Check for conflicts
        if 'emp_id' in update_data or 'email' in update_data:
            conflict = self._check_conflicts(emp_id, update_data)
            if conflict:
                raise HTTPException(
                    status_code=400,
                    detail="Employee ID or Email already exists"
                )
        
        # Update fields
        for key, value in update_data.items():
            if hasattr(employee, key) and value is not None:
                setattr(employee, key, value)
        
        self.db.commit()
        return {"message": "Employee updated successfully"}
    
    def delete_employee(self, emp_id: int, admin: Employee) -> Dict:
        """
        Delete employee
        
        Args:
            emp_id: Employee database ID
            admin: Admin performing deletion
            
        Returns:
            Success message
        """
        if admin.role == UserRole.HR:
            raise HTTPException(
                status_code=403,
                detail="HR cannot delete employees"
            )
        
        employee = self.employee_repo.get_by_db_id(emp_id)
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        self.employee_repo.delete(employee)
        self.db.commit()
        
        return {"message": "Employee deleted successfully"}
    
    def _check_conflicts(self, current_id: int, update_data: Dict) -> bool:
        """Check for emp_id or email conflicts, excluding current employee"""
        if 'emp_id' in update_data:
            conflict = self.db.query(Employee).filter(
                Employee.id != current_id,
                Employee.emp_id == update_data['emp_id']
            ).first()
            if conflict:
                return True
        
        if 'email' in update_data:
            conflict = self.db.query(Employee).filter(
                Employee.id != current_id,
                Employee.email == update_data['email']
            ).first()
            if conflict:
                return True
        
        return False

    async def process_employee_master(self, file, admin: Employee) -> Dict:
        """Process uploaded employee master Excel file"""
        import pandas as pd
        import io
        
        # HR cannot perform sync
        if admin.role == UserRole.HR:
            raise HTTPException(status_code=403, detail="HR cannot perform sync actions")
            
        content = await file.read()
        df = pd.read_excel(io.BytesIO(content))
        
        required_cols = ['emp_id', 'full_name', 'email', 'designation']
        for col in required_cols:
            if col not in df.columns:
                raise HTTPException(status_code=400, detail=f"Missing required column: {col}")
        
        saved = 0
        updated = 0
        
        for _, row in df.iterrows():
            emp_id = str(row['emp_id']).strip()
            if not emp_id or emp_id == 'nan': continue
            
            existing = self.employee_repo.get_by_emp_id(emp_id)
            data = {
                "full_name": row['full_name'],
                "email": row['email'],
                "designation": row['designation'],
                "phone_number": str(row.get('phone_number', '')),
                "status": "ACTIVE"
            }
            
            if existing:
                for key, val in data.items():
                    setattr(existing, key, val)
                updated += 1
            else:
                data["emp_id"] = emp_id
                self.employee_repo.create(data)
                saved += 1
                
        self.db.commit()
        return {"message": f"Sync complete. Created: {saved}, Updated: {updated}"}

    def generate_master_template(self) -> bytes:
        """Generate sample Excel template for employee master"""
        import pandas as pd
        import io
        
        df = pd.DataFrame(columns=['emp_id', 'full_name', 'email', 'designation', 'phone_number'])
        # Add a sample row
        df.loc[0] = ['RBIS0001', 'John Doe', 'john@rbistech.com', 'Software Engineer', '1234567890']
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Employees')
        return output.getvalue()

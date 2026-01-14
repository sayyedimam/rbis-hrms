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
        employee = self.employee_repo.get_by_id(str(emp_id))
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
        
        employee = self.employee_repo.get_by_id(str(emp_id))
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        self.employee_repo.delete(employee)
        self.db.commit()
        
        return {"message": "Employee deleted successfully"}
    
    def _check_conflicts(self, current_id: int, update_data: Dict) -> bool:
        """Check for emp_id or email conflicts"""
        query = self.db.query(Employee).filter(Employee.id != current_id)
        
        if 'emp_id' in update_data:
            if self.employee_repo.exists_by_emp_id(update_data['emp_id']):
                return True
        
        if 'email' in update_data:
            if self.employee_repo.exists_by_email(update_data['email']):
                return True
        
        return False

"""
Employee Repository
Database access layer for Employee model
"""
from sqlalchemy.orm import Session
from app.models.models import Employee
from typing import Optional, List

class EmployeeRepository:
    """Handles all database operations for Employee model"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_email(self, email: str) -> Optional[Employee]:
        """
        Get employee by email address
        
        Args:
            email: Employee email
            
        Returns:
            Employee object or None if not found
        """
        return self.db.query(Employee).filter(Employee.email == email).first()
    
    def get_by_db_id(self, id: int) -> Optional[Employee]:
        """
        Get employee by database primary key ID
        
        Args:
            id: Database ID (integer)
            
        Returns:
            Employee object or None if not found
        """
        return self.db.query(Employee).get(id)

    def get_by_emp_id(self, emp_id: str) -> Optional[Employee]:
        """
        Get employee by employee ID (e.g., RBIS001)
        
        Args:
            emp_id: Employee ID
            
        Returns:
            Employee object or None if not found
        """
        return self.db.query(Employee).filter(Employee.emp_id == emp_id).first()
    
    def get_all(self) -> List[Employee]:
        """
        Get all employees
        
        Returns:
            List of all Employee objects
        """
        return self.db.query(Employee).all()
    
    def count(self) -> int:
        """
        Get total count of employees
        
        Returns:
            Total number of employees
        """
        return self.db.query(Employee).count()
    
    def create(self, employee_data: dict) -> Employee:
        """
        Create new employee
        
        Args:
            employee_data: Dictionary with employee fields
            
        Returns:
            Created Employee object
        """
        employee = Employee(**employee_data)
        self.db.add(employee)
        self.db.commit()
        self.db.refresh(employee)
        return employee
    
    def update(self, employee: Employee) -> Employee:
        """
        Update existing employee
        
        Args:
            employee: Employee object with updated fields
            
        Returns:
            Updated Employee object
        """
        self.db.commit()
        self.db.refresh(employee)
        return employee
    
    def delete(self, employee: Employee) -> None:
        """
        Delete employee
        
        Args:
            employee: Employee object to delete
        """
        self.db.delete(employee)
        self.db.commit()
    
    def exists_by_email(self, email: str) -> bool:
        """
        Check if employee exists by email
        
        Args:
            email: Email to check
            
        Returns:
            True if employee exists, False otherwise
        """
        return self.db.query(Employee).filter(Employee.email == email).first() is not None
    
    def exists_by_emp_id(self, emp_id: str) -> bool:
        """
        Check if employee exists by employee ID
        
        Args:
            emp_id: Employee ID to check
            
        Returns:
            True if employee exists, False otherwise
        """
        return self.db.query(Employee).filter(Employee.emp_id == emp_id).first() is not None

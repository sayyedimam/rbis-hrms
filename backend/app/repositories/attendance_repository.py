"""
Attendance Repository
Database access layer for Attendance model
"""
from sqlalchemy.orm import Session
from app.models.models import Attendance
from typing import List, Optional
from datetime import date

class AttendanceRepository:
    """Handles all database operations for Attendance model"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, attendance_id: int) -> Optional[Attendance]:
        """Get attendance record by ID"""
        return self.db.query(Attendance).filter(Attendance.id == attendance_id).first()
    
    def get_by_emp_and_date(self, emp_id: str, attendance_date: date) -> Optional[Attendance]:
        """
        Get attendance record for specific employee and date
        
        Args:
            emp_id: Employee ID
            attendance_date: Attendance date
            
        Returns:
            Attendance record or None
        """
        return self.db.query(Attendance).filter(
            Attendance.emp_id == emp_id,
            Attendance.date == attendance_date
        ).first()
    
    def get_by_emp_id(self, emp_id: str) -> List[Attendance]:
        """Get all attendance records for an employee"""
        from sqlalchemy.orm import joinedload
        return self.db.query(Attendance).options(joinedload(Attendance.owner)).filter(Attendance.emp_id == emp_id).all()
    
    def get_all(self) -> List[Attendance]:
        """Get all attendance records"""
        from sqlalchemy.orm import joinedload
        return self.db.query(Attendance).options(joinedload(Attendance.owner)).all()
    
    def create(self, attendance_data: dict) -> Attendance:
        """
        Create new attendance record
        
        Args:
            attendance_data: Dictionary with attendance fields
            
        Returns:
            Created Attendance object
        """
        record = Attendance(**attendance_data)
        self.db.add(record)
        return record
    
    def update(self, record: Attendance, update_data: dict) -> Attendance:
        """
        Update attendance record
        
        Args:
            record: Attendance record to update
            update_data: Dictionary with fields to update
            
        Returns:
            Updated Attendance object
        """
        for key, value in update_data.items():
            if hasattr(record, key) and value is not None:
                setattr(record, key, value)
        return record
    
    def delete(self, record: Attendance) -> None:
        """Delete attendance record"""
        self.db.delete(record)
    
    def commit(self) -> None:
        """Commit transaction"""
        self.db.commit()
    
    def rollback(self) -> None:
        """Rollback transaction"""
        self.db.rollback()

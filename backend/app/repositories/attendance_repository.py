"""
Attendance Repository
Database access layer for Attendance model
"""
from sqlalchemy.orm import Session
from app.models import Employee, Attendance
from typing import List, Optional
from datetime import date
from sqlalchemy import func
from sqlalchemy.orm import joinedload
import functools
import time

def simple_cache(ttl_seconds: int = 300):
    """Simple in-memory cache decorator"""
    def decorator(func):
        cache = {}
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            # Create cache key from function name and arguments
            key = f"{func.__name__}_{str(args)}_{str(sorted(kwargs.items()))}"

            # Check if cached and not expired
            if key in cache:
                result, timestamp = cache[key]
                if time.time() - timestamp < ttl_seconds:
                    return result

            # Execute function and cache result
            result = func(self, *args, **kwargs)
            cache[key] = (result, time.time())
            return result
        return wrapper
    return decorator

class AttendanceRepository:
    """Handles all database operations for Attendance model"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_latest_date(self) -> Optional[date]:
        """Get the most recent attendance date from the database"""
        return self.db.query(func.max(Attendance.date)).scalar()
    
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
    

    def get_by_date_range(self, emp_id: str = None, start_date: date = None, end_date: date = None) -> List[Attendance]:
        """
        Get attendance records within a date range
        
        Args:
            emp_id: Employee ID (if None, returns all employees)
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            
        Returns:
            List of Attendance records
        """
        from sqlalchemy.orm import joinedload
        query = self.db.query(Attendance).options(joinedload(Attendance.owner))
        
        if emp_id:
            query = query.filter(Attendance.emp_id == emp_id)
        
        if start_date:
            query = query.filter(Attendance.date >= start_date)
        
        if end_date:
            query = query.filter(Attendance.date <= end_date)
        
        return query.order_by(Attendance.date.desc()).all()
    
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

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add parent dir to path to import models
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.models.models import Employee, Attendance
from app.core.database import SessionLocal

def normalize_id(raw_id):
    if not raw_id: return raw_id
    s = str(raw_id).strip()
    if s.isdigit() and s != '0':
        return s.lstrip('0')
    return s

def run():
    db = SessionLocal()
    try:
        # 1. Fix Employees
        employees = db.query(Employee).all()
        for emp in employees:
            old_id = emp.emp_id
            new_id = normalize_id(old_id)
            if old_id != new_id:
                print(f"Updating Employee: {old_id} -> {new_id}")
                emp.emp_id = new_id
        
        # 2. Fix Attendance
        records = db.query(Attendance).all()
        for rec in records:
            old_id = rec.emp_id
            new_id = normalize_id(old_id)
            if old_id != new_id:
                print(f"Updating Attendance: {old_id} -> {new_id} ({rec.date})")
                rec.emp_id = new_id
        
        db.commit()
        print("Finalizing normalization...")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run()

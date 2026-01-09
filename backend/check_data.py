from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add parent dir to path to import models
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.models.models import Employee, Attendance
from app.core.database import SessionLocal

def run():
    db = SessionLocal()
    try:
        print("--- EMPLOYEES ---")
        emps = db.query(Employee).all()
        for e in emps:
            print(f"ID: {e.id} | EmpID: '{e.emp_id}' | Email: {e.email} | Name: {e.full_name}")
        
        print("\n--- ATTENDANCE (First 20) ---")
        recs = db.query(Attendance).limit(20).all()
        for r in recs:
            print(f"EmpID: '{r.emp_id}' | Date: {r.date} | Status: {r.attendance_status}")
            
    finally:
        db.close()

if __name__ == "__main__":
    run()

import sys
import os

# Add the project root to the python path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from sqlalchemy import text
from app.core.database import SessionLocal

def inspect_employee_table():
    db = SessionLocal()
    try:
        # Get count
        count = db.execute(text("SELECT COUNT(*) FROM employees")).scalar()
        print(f"Total Employees: {count}")

        # Get Columns (SQL Server specific, but works for general inspection)
        print("\nColumns:")
        columns = db.execute(text("SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'employees'")).fetchall()
        for col in columns:
            print(f"- {col[0]} ({col[1]}, {col[2] if col[2] else ''}) {'NULL' if col[3]=='YES' else 'NOT NULL'}")

        # Get Sample Data (First 5)
        print("\nSample Data (First 5):")
        samples = db.execute(text("SELECT TOP 5 emp_id, full_name, email, role, status FROM employees")).fetchall()
        for row in samples:
            print(f"- {row}")

        # check for duplicates just in case
        print("\nDuplicate Emails Check:")
        dupes = db.execute(text("SELECT email, COUNT(*) FROM employees GROUP BY email HAVING COUNT(*) > 1")).fetchall()
        if dupes:
            for d in dupes:
                print(f"!! Duplicate: {d[0]} (Count: {d[1]})")
        else:
            print("No duplicate emails found.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    inspect_employee_table()

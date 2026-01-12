from app.core.database import SessionLocal
from app.models.models import LeaveType

def rename_leave_type():
    db = SessionLocal()
    try:
        lt = db.query(LeaveType).filter(LeaveType.name == "Earned Leave").first()
        if lt:
            lt.name = "Paid Leave"
            db.commit()
            print("Successfully renamed 'Earned Leave' to 'Paid Leave'")
        else:
            print("'Earned Leave' not found in database")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    rename_leave_type()

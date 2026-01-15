from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.models import LeaveType

def update_leave_types():
    db = SessionLocal()
    try:
        # 1. Delete all types except "Paid Leave"
        db.query(LeaveType).filter(LeaveType.name != "Paid Leave").delete()
        print("Removed extraneous leave types.")

        # 2. Ensure "Paid Leave" exists
        paid_leave = db.query(LeaveType).filter(LeaveType.name == "Paid Leave").first()
        if not paid_leave:
            new_type = LeaveType(
                name="Paid Leave",
                annual_quota=12,  # Defaulting, can be changed
                is_paid=True,
                allow_carry_forward=True,
                is_active=True
            )
            db.add(new_type)
            print("Created 'Paid Leave' type.")
        else:
            print("'Paid Leave' already exists.")
        
        db.commit()
        print("Leave types updated successfully.")
    except Exception as e:
        print(f"Error updating leave types: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_leave_types()

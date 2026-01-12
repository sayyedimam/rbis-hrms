from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.models import LeaveType

def seed_leave_types():
    db = SessionLocal()
    leave_types = [
        {"name": "Casual Leave", "annual_quota": 12, "is_paid": True, "allow_carry_forward": False},
        {"name": "Sick Leave", "annual_quota": 8, "is_paid": True, "allow_carry_forward": True},
        {"name": "Paid Leave", "annual_quota": 15, "is_paid": True, "allow_carry_forward": True},
        {"name": "Unpaid Leave", "annual_quota": 0, "is_paid": False, "allow_carry_forward": False},
    ]

    for lt in leave_types:
        existing = db.query(LeaveType).filter(LeaveType.name == lt["name"]).first()
        if not existing:
            new_type = LeaveType(**lt)
            db.add(new_type)
            print(f"Added leave type: {lt['name']}")
        else:
            print(f"Leave type {lt['name']} already exists")
    
    db.commit()
    db.close()

if __name__ == "__main__":
    seed_leave_types()

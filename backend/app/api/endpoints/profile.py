from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.models.models import Employee

router = APIRouter()

@router.get("/")
async def get_profile(user: Employee = Depends(get_current_user)):
    return {
        "emp_id": user.emp_id,
        "email": user.email,
        "full_name": user.full_name,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone_number": user.phone_number,
        "designation": user.designation,
        "role": user.role,
        "joined_at": user.created_at
    }

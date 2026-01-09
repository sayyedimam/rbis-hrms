from fastapi import APIRouter
from app.api.endpoints import auth, attendance, onboarding, records, profile

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(attendance.router, prefix="/attendance", tags=["Attendance"])
api_router.include_router(onboarding.router, prefix="/onboarding", tags=["Onboarding"])
api_router.include_router(records.router, prefix="/records", tags=["Records"])
api_router.include_router(profile.router, prefix="/profile", tags=["Profile"])

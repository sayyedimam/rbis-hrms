"""
API v1 Endpoints Router
Registers all v1 API endpoints
"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, attendance, leave, admin, profile, records, onboarding, notice

api_router = APIRouter()

# Register all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(attendance.router, prefix="/attendance", tags=["Attendance"])
api_router.include_router(leave.router, prefix="/leave", tags=["Leave Management"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
api_router.include_router(profile.router, prefix="/profile", tags=["Profile"])
api_router.include_router(records.router, prefix="/records", tags=["Records"])
api_router.include_router(onboarding.router, prefix="/onboarding", tags=["Onboarding"])
api_router.include_router(notice.router, prefix="/notices", tags=["Notices"])


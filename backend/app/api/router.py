"""
Main API Router
Supports both v1 and legacy endpoints for smooth transition
"""
from fastapi import APIRouter
from app.api.v1 import router as v1_router

api_router = APIRouter()

# V1 API (Refactored - Clean Architecture)
# Recommended: Use /api/v1/* endpoints
api_router.include_router(v1_router.api_router, prefix="/api/v1")

# Legacy API (Backward Compatibility)
# Old endpoints (/auth/*, /attendance/*, etc.) redirect to v1
# This allows frontend to work without immediate changes
api_router.include_router(v1_router.api_router)  # Mount v1 routes at root level too

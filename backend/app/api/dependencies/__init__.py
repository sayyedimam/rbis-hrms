"""
API Dependencies Package
Contains all dependency injection functions for FastAPI
"""
from app.api.dependencies.auth import (
    get_current_user,
    check_admin,
    check_hr,
    check_ceo,
    oauth2_scheme
)
from app.api.dependencies.database import get_db

__all__ = [
    "get_current_user",
    "check_admin",
    "check_hr",
    "check_ceo",
    "oauth2_scheme",
    "get_db"
]

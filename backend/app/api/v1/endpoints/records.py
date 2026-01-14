"""
Records Endpoints (API v1)
Handles file records and history
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, check_admin
from app.repositories.file_repository import FileRepository
from app.models.models import Employee

router = APIRouter()

@router.get("/")
async def get_upload_history(
    admin: Employee = Depends(check_admin),
    db: Session = Depends(get_db)
):
    """
    Get file upload history
    
    - Returns all uploaded files
    - Shows filename, type, uploader, date
    - Requires admin role
    """
    repo = FileRepository(db)
    return repo.get_all()

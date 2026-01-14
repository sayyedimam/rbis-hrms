"""
Records Endpoints (API v1)
Handles file records and history
"""
from fastapi import APIRouter, Depends, HTTPException
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

@router.get("/download/{file_id}")
async def download_file(
    file_id: int,
    admin: Employee = Depends(check_admin),
    db: Session = Depends(get_db)
):
    """
    Download uploaded file from Azure
    - Requires admin role
    """
    repo = FileRepository(db)
    file_log = repo.get_by_id(file_id)
    
    if not file_log:
        raise HTTPException(status_code=404, detail="File record not found")
        
    from app.core.azure_utils import download_file_stream
    from fastapi.responses import Response
    
    content = await download_file_stream(file_log.file_path)
    
    return Response(
        content=content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={file_log.filename}"}
    )

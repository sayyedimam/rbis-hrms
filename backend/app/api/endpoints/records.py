from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
from app.core.database import get_db
from app.api.deps import check_admin
from app.models.models import FileUploadLog, Employee, UserRole
from app.core.azure_utils import download_file_stream

router = APIRouter()

@router.get("/")
async def get_records(db: Session = Depends(get_db), user: Employee = Depends(check_admin)):
    if user.role == UserRole.HR:
        raise HTTPException(status_code=403, detail="Access denied for HR role")
    return db.query(FileUploadLog).order_by(FileUploadLog.uploaded_at.desc()).all()

@router.get("/download/{file_id}")
async def download_record(file_id: int, db: Session = Depends(get_db), user: Employee = Depends(check_admin)):
    if user.role == UserRole.HR:
        raise HTTPException(status_code=403, detail="Access denied for HR role")
    log = db.query(FileUploadLog).filter(FileUploadLog.id == file_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="File record not found.")

    # Check if legacy local file
    if os.path.isabs(log.file_path) and os.path.exists(log.file_path):
        return FileResponse(path=log.file_path, filename=log.filename)
        
    # Assume Azure Blob - Now returns bytes
    try:
        data = await download_file_stream(log.file_path)
        return Response(
            content=data,
            media_type="application/octet-stream", 
            headers={"Content-Disposition": f"attachment; filename={log.filename}"}
        )
    except Exception as e:
        print(f"[ERROR] Download failed for {log.file_path}: {e}", flush=True)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

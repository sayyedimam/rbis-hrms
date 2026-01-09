from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
from app.core.database import get_db
from app.api.deps import check_admin
from app.models.models import FileUploadLog, Employee

router = APIRouter()

@router.get("/")
async def get_records(db: Session = Depends(get_db), admin: Employee = Depends(check_admin)):
    return db.query(FileUploadLog).order_by(FileUploadLog.uploaded_at.desc()).all()

@router.get("/download/{file_id}")
async def download_record(file_id: int, db: Session = Depends(get_db), admin: Employee = Depends(check_admin)):
    log = db.query(FileUploadLog).filter(FileUploadLog.id == file_id).first()
    if not log or not os.path.exists(log.file_path):
        raise HTTPException(status_code=404, detail="File not found on server.")
    return FileResponse(path=log.file_path, filename=log.filename)

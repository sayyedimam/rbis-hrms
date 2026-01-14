"""
Attendance Endpoints (API v1)
Handles attendance file upload and record management
"""
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from typing import Optional

from app.api.dependencies import get_db, get_current_user, check_admin
from app.services.attendance_service import AttendanceService
from app.models.models import Employee

router = APIRouter()

class AttendanceUpdate(BaseModel):
    """Schema for attendance record updates"""
    first_in: Optional[str] = None
    last_out: Optional[str] = None
    in_duration: Optional[str] = None
    out_duration: Optional[str] = None
    attendance_status: Optional[str] = None

@router.post("/upload/files")
async def upload_files(
    files: List[UploadFile] = File(...),
    admin: Employee = Depends(check_admin),
    db: Session = Depends(get_db)
):
    """
    Upload attendance files
    
    - Accepts Excel/CSV files
    - Detects duplicates by file hash
    - Processes attendance records
    - Uploads to Azure Blob Storage
    - Returns processing results
    
    Requires: Admin/HR/CEO role
    """
    service = AttendanceService(db)
    return await service.process_uploaded_files(files, admin)

@router.get("/")
async def get_attendance(
    user: Employee = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get attendance records
    
    - Employees see only their own records
    - Admin/HR/CEO see all records
    - Returns list of attendance records
    """
    service = AttendanceService(db)
    return service.get_attendance_records(user)

@router.put("/{id}")
async def update_attendance(
    id: int,
    data: AttendanceUpdate,
    admin: Employee = Depends(check_admin),
    db: Session = Depends(get_db)
):
    """
    Update attendance record
    
    - Updates specific attendance record
    - Allows modification of times and status
    - Returns success message
    
    Requires: Admin/HR/CEO role
    """
    service = AttendanceService(db)
    update_dict = data.dict(exclude_unset=True)
    return service.update_attendance_record(id, update_dict)

"""
Attendance Endpoints (API v1)
Handles attendance file upload and record management
"""
from app.core.azure_utils import logger
from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from typing import Optional
import io

from app.api.dependencies import get_db, get_current_user, check_admin
from app.services.attendance_service import AttendanceService
from app.models import Employee
import logging
logger = logging.getLogger(__name__)

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
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    admin: Employee = Depends(check_admin),
    db: Session = Depends(get_db)
):
    """
    Upload attendance files
    
    - Accepts Excel/CSV files
    - Processes in BACKGROUND (non-blocking)
    - Returns immediate "Processing started" message
    
    Requires: Admin/HR/CEO role
    """
    # 1. Read and VALIDATE all files synchronously
    from app.services.cleaner import detect_and_clean_memory
    from fastapi import HTTPException
    
    file_data_list = []
    for file in files:
        content = await file.read()
        
        # Synchronous Validation
        cleaned_data, detected_type = detect_and_clean_memory(content)
        if not cleaned_data:
            logger.error(f"Upload rejected for {file.filename}: {detected_type}")
            raise HTTPException(status_code=400, detail=f"File '{file.filename}' rejected: {detected_type}")
            
        file_data_list.append({
            "filename": file.filename,
            "content": content,
            "content_type": file.content_type,
            "cleaned_data": cleaned_data,
            "detected_type": detected_type
        })
    
    # 2. Add to background tasks only after validation passes for ALL files
    background_tasks.add_task(process_files_background, file_data_list, admin.email)
    
    return {"message": f"Successfully validated {len(files)} file(s). Processing has started."}

from app.core.database import SessionLocal
from app.models import Employee, Attendance
def process_files_background(file_data_list: List[dict], admin_email: str):
    """Background task to process files"""
    db = SessionLocal()
    try:
        # Re-fetch admin because object detaches
        admin = db.query(Employee).filter(Employee.email == admin_email).first()
        if not admin:
            print(f"Admin {admin_email} not found during background processing")
            return

        service = AttendanceService(db)
        
        # We need to mock UploadFile-like objects for the service
        # or refactor service to accept bytes.
        # Let's mock it to minimize service refactoring.
        class MockUploadFile:
            def __init__(self, filename, content, content_type, cleaned_data=None, detected_type=None):
                self.filename = filename
                self.content_type = content_type
                self.file = io.BytesIO(content) 
                self.cleaned_data = cleaned_data
                self.detected_type = detected_type
            
            async def read(self):
                return self.file.getvalue()

        mock_files = [
            MockUploadFile(
                f["filename"], 
                f["content"], 
                f["content_type"], 
                f.get("cleaned_data"), 
                f.get("detected_type")
            ) 
            for f in file_data_list
        ]
        
        # Call the synchronous service method
        service.process_uploaded_files(mock_files, admin)
        
    except Exception as e:
        print(f"Background processing error: {e}")
    finally:
        db.close()


@router.get("/")
def get_attendance(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user: Employee = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get attendance records
    
    - Employees see only their own records
    - Admin/HR/CEO see all records
    - Supports optional date range filtering
    - Returns list of attendance records
    """
    service = AttendanceService(db)
    return service.get_attendance_records(user, start_date, end_date)

@router.put("/{id}")
def update_attendance(
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

@router.delete("/{id}")
def delete_attendance(
    id: int,
    admin: Employee = Depends(check_admin),
    db: Session = Depends(get_db)
):
    """
    Delete attendance record
    
    - Deletes specific attendance record
    - Returns success message
    
    Requires: Admin/HR/CEO role
    """
    service = AttendanceService(db)
    return service.delete_attendance_record(id)

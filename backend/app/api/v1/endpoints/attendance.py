"""
Attendance Endpoints (API v1)
Handles attendance file upload and record management
"""
from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from typing import Optional
import io

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
    # 1. Read all files into memory immediately (Async I/O)
    # Be careful with huge files, but for attendance sheets (usually < 5MB), RAM is fine.
    # We need to recreate UploadFile objects or pass bytes to the service.
    # Since Service expects UploadFile, let's read bytes and mock/pass them.
    # Actually, better pattern: Pass the db session? No, db session is scoped to request.
    # We MUST create a new DB session for the background task or ensure the service handles it.
    # Dependency injection db session closes after request.
    
    # PROBLEM: 'db' session will close when this function returns.
    # SOLUTION: Background task must create its own DB session.
    # We need a wrapper function for the background task.
    
    # Let's simplify: Read content now.
    file_data_list = []
    for file in files:
        content = await file.read()
        file_data_list.append({
            "filename": file.filename,
            "content": content,
            "content_type": file.content_type
        })
    
    # Add to background tasks
    background_tasks.add_task(process_files_background, file_data_list, admin.email)
    
    return {"message": "Upload accepted. Processing started in background."}

from app.core.database import SessionLocal
from app.models.models import Employee

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
            def __init__(self, filename, content, content_type):
                self.filename = filename
                self.content_type = content_type
                self.file = io.BytesIO(content) # Sync file-like object
            
            async def read(self): # Keep async interface if service still has await (we removed it though)
                return self.file.getvalue()

        mock_files = [
            MockUploadFile(f["filename"], f["content"], f["content_type"]) 
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

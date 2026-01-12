from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import os
import hashlib
import datetime
import pandas as pd
from app.core.database import get_db
from app.api.deps import get_current_user, check_admin
from app.models.models import Employee, Attendance, FileUploadLog, UserRole, UserStatus
from app.services.cleaner import detect_and_clean_memory

from app.core.azure_utils import upload_bytes_to_azure

import logging

router = APIRouter()
print("[INIT] Attendance Endpoint Module Loaded", flush=True)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.post("/upload/files")
async def upload_files(
    files: List[UploadFile] = File(...),
    admin: Employee = Depends(check_admin),
    db: Session = Depends(get_db)
):
    results = []
    # Local storage dir removed in favor of Azure
    # storage_dir = os.path.join(os.getcwd(), "storage", "records")
    
    for file in files:
        logger.info(f"Received file for processing: {file.filename}")
        try:
            content = await file.read()
            file_hash = hashlib.sha256(content).hexdigest()
            existing_file = db.query(FileUploadLog).filter(FileUploadLog.file_hash == file_hash).first()
            
            if existing_file:
                logger.info(f"[SYSTEM] File {file.filename} already uploaded (Hash collision). Skipping Azure upload.")
                # We do NOT upload to Azure, preventing duplicates if DB record exists.
                # However, we proceed to re-process the content to update Attendance entries.
                pass 
            
            cleaned_data, detected_type = detect_and_clean_memory(content)
            logger.info(f"[DEBUG] Processing file: {file.filename} | Detected Type: {detected_type}")
            
            if not cleaned_data:
                logger.error(f"[ERROR] No data extracted from {file.filename} using {detected_type}")
                results.append({"filename": file.filename, "status": "error", "reason": "Unknown file format"})
                continue

            # Determine file path/blob name
            if not existing_file:
                safe_filename = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
                # Upload to Azure
                await upload_bytes_to_azure(content, safe_filename, file.content_type)
                file_path = safe_filename # Store blob name in file_path column
                
                upload_log = FileUploadLog(
                    filename=file.filename,
                    uploaded_by=admin.email,
                    report_type=detected_type,
                    file_hash=file_hash,
                    file_path=file_path
                )
            else:
                # If existing, we reuse the path for logging consistency or just update?
                # The logic seems to be creating a NEW log even if hash exists? 
                # Original code only did `if not existing_file` for writing to disk.
                # But FileUploadLog creation was inside `if not existing_file: ...`?
                # Wait, let's look at original code again.
                pass 
                
            if not existing_file:
                db.add(upload_log)
                db.flush() # Generate ID
                logger.info(f"Created file log ID: {upload_log.id}")
            else:
                logger.info(f"Using existing upload record for {file.filename}")

            # Simpler loop for unified report format
            logger.info(f"[INFO] Cleaner returned {len(cleaned_data)} records for {file.filename}")

            saved_count = 0
            updated_count = 0
            for rec in cleaned_data:
                raw_id = str(rec.get('EmpID', '')).strip()
                if not raw_id or raw_id.lower() == 'nan': 
                    continue

                # Normalize to RBIS0000 format
                if raw_id.upper().startswith('RBIS'):
                    num_part = ''.join(filter(str.isdigit, raw_id))
                    emp_id = f"RBIS{num_part.zfill(4)}"
                elif raw_id.isdigit():
                    emp_id = f"RBIS{raw_id.zfill(4)}"
                else:
                    emp_id = raw_id.upper()

                date_val = rec.get('Date')
                try:
                    date_obj = pd.to_datetime(date_val).date()
                except Exception as de:
                    logger.error(f"Could not parse date '{date_val}' for {emp_id}: {de}")
                    continue

                existing = db.query(Attendance).filter(Attendance.emp_id == emp_id, Attendance.date == date_obj).first()
                
                # Prepare update/insert data
                first_in = rec.get('First_In')
                last_out = rec.get('Last_Out')
                in_dur = rec.get('In_Duration')
                out_dur = rec.get('Out_Duration')
                total_dur = rec.get('Total_Duration')
                status = rec.get('Attendance')
                punches = rec.get('Punch_Records')

                if existing:
                    # Update existing record
                    existing.first_in = first_in
                    existing.last_out = last_out
                    existing.in_duration = in_dur
                    existing.out_duration = out_dur
                    existing.total_duration = total_dur
                    existing.punch_records = punches
                    existing.attendance_status = status
                    existing.source_file = file.filename
                    updated_count += 1
                    logger.info(f"[UPDATE] {emp_id} | {date_obj} | In: {first_in} | Out: {last_out}")
                else:
                    # Insert new record
                    new_att = Attendance(
                        emp_id=emp_id,
                        date=date_obj,
                        first_in=first_in,
                        last_out=last_out,
                        in_duration=in_dur,
                        out_duration=out_dur,
                        total_duration=total_dur,
                        punch_records=punches,
                        attendance_status=status,
                        source_file=file.filename
                    )
                    db.add(new_att)
                    saved_count += 1
                    logger.info(f"[INSERT] {emp_id} | {date_obj} | In: {first_in} | Out: {last_out}")

            db.commit()
            results.append({
                "filename": file.filename, 
                "status": "success", 
                "type": detected_type, 
                "details": f"Processed {len(cleaned_data)} records"
            })
            logger.info(f"Completed processing {file.filename}: Saved {saved_count}, Updated {updated_count}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error processing file {file.filename}: {e}", exc_info=True)
            results.append({"filename": file.filename, "status": "error", "reason": str(e)})

    return {"message": "Upload processing complete", "results": results}

from pydantic import BaseModel
from typing import Optional

class AttendanceUpdate(BaseModel):
    first_in: Optional[str] = None
    last_out: Optional[str] = None
    attendance_status: Optional[str] = None

@router.get("/")
async def get_attendance(
    user: Employee = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Attendance)
    # HR Role gets full access same as Admin/CEO
    if user.role == UserRole.EMPLOYEE:
        query = query.filter(Attendance.emp_id == user.emp_id)
        
    return query.all()

@router.put("/{id}")
async def update_attendance(
    id: int,
    data: AttendanceUpdate,
    db: Session = Depends(get_db),
    admin: Employee = Depends(check_admin)
):
    record = db.query(Attendance).filter(Attendance.id == id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")
        
    if data.first_in is not None:
        record.first_in = data.first_in
    if data.last_out is not None:
        record.last_out = data.last_out
    if data.attendance_status is not None:
        record.attendance_status = data.attendance_status
        
    record.is_manually_corrected = True
    record.corrected_by = admin.email
    
    # Recalculate duration if both times provided (Simple logic)
    # Ideally should share logic with cleaner, but for manual edit we might rely on admin.
    # We leave In/Out/Total Duration as-is unless we want to rebuild them.
    # For now, simplistic update.
    
    db.commit()
    return {"message": "Attendance updated successfully", "record": {
        "id": record.id,
        "first_in": record.first_in,
        "last_out": record.last_out,
        "status": record.attendance_status
    }}

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
    storage_dir = os.path.join(os.getcwd(), "storage", "records")
    if not os.path.exists(storage_dir):
        os.makedirs(storage_dir)

    for file in files:
        logger.info(f"Received file for processing: {file.filename}")
        try:
            content = await file.read()
            file_hash = hashlib.sha256(content).hexdigest()
            existing_file = db.query(FileUploadLog).filter(FileUploadLog.file_hash == file_hash).first()
            
            if existing_file:
                logger.info(f"[SYSTEM] File {file.filename} already uploaded (Hash collision). Re-processing to ensure data sync.")
                # results.append({"filename": file.filename, "status": "skipped", "reason": "File already exists in records"})
                # continue
 
            cleaned_data, detected_type = detect_and_clean_memory(content)
            logger.info(f"[DEBUG] Processing file: {file.filename} | Detected Type: {detected_type}")
            
            if not cleaned_data:
                logger.error(f"[ERROR] No data extracted from {file.filename} using {detected_type}")
                results.append({"filename": file.filename, "status": "error", "reason": "Unknown file format"})
                continue

            if not existing_file:
                safe_filename = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
                file_path = os.path.join(storage_dir, safe_filename)
                with open(file_path, "wb") as buffer:
                    buffer.write(content)

                upload_log = FileUploadLog(
                    filename=file.filename,
                    uploaded_by=admin.email,
                    report_type=detected_type,
                    file_hash=file_hash,
                    file_path=file_path
                )
                db.add(upload_log)
                db.flush()
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

@router.get("/")
async def get_attendance(
    user: Employee = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Attendance)
    if user.role == UserRole.EMPLOYEE:
        query = query.filter(Attendance.emp_id == user.emp_id)
    return query.all()

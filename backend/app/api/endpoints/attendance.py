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

router = APIRouter()

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
        try:
            content = await file.read()
            file_hash = hashlib.sha256(content).hexdigest()
            existing_file = db.query(FileUploadLog).filter(FileUploadLog.file_hash == file_hash).first()
            
            if existing_file:
                results.append({"filename": file.filename, "status": "skipped", "reason": "File already exists in records"})
                continue

            cleaned_data, detected_type = detect_and_clean_memory(content)
            
            if not cleaned_data:
                results.append({"filename": file.filename, "status": "error", "reason": "Unknown file format"})
                continue

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

            saved_count = 0
            if detected_type == "Employee Master":
                df = cleaned_data[0]['df']
                updated = 0
                for _, row in df.iterrows():
                    raw_id = str(row.get('EmpId', '')).strip()
                    if not raw_id or raw_id.lower() == 'nan': continue
                    
                    # Normalize to RBIS0000 format
                    if raw_id.upper().startswith('RBIS'):
                        num_part = ''.join(filter(str.isdigit, raw_id))
                        emp_id = f"RBIS{num_part.zfill(4)}"
                    elif raw_id.isdigit():
                        emp_id = f"RBIS{raw_id.zfill(4)}"
                    else:
                        emp_id = raw_id.upper()

                    email = str(row.get('Email', '')).strip()
                    emp = db.query(Employee).filter((Employee.emp_id == emp_id) | (Employee.email == email)).first()
                    if emp:
                        emp.emp_id = emp_id
                        emp.full_name = str(row.get('Name', emp.full_name))
                        emp.first_name = str(row.get('First Name', emp.first_name))
                        emp.last_name = str(row.get('Last Name', emp.last_name))
                        emp.phone_number = str(row.get('Phone Number', emp.phone_number))
                        emp.email = email
                        emp.designation = str(row.get('Designation', emp.designation))
                        updated += 1
                    else:
                        new_emp = Employee(
                            emp_id=emp_id,
                            full_name=str(row.get('Name', '')),
                            first_name=str(row.get('First Name', '')),
                            last_name=str(row.get('Last Name', '')),
                            phone_number=str(row.get('Phone Number', '')),
                            email=email if email.lower() != 'nan' else None,
                            designation=str(row.get('Designation', '')),
                            role=UserRole.EMPLOYEE,
                            status=UserStatus.ACTIVE
                        )
                        db.add(new_emp)
                        saved_count += 1
                results.append({"filename": file.filename, "status": "success", "type": "Master", "details": f"Added {saved_count}, Updated {updated}"})
            
            else:
                for rec in cleaned_data:
                    raw_id = str(rec.get('EmpID', '')).strip()
                    if not raw_id or raw_id.lower() == 'nan': continue

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
                        date_obj = datetime.date.fromisoformat(date_val)
                    except:
                        try: date_obj = pd.to_datetime(date_val).date()
                        except: continue

                    existing = db.query(Attendance).filter(Attendance.emp_id == emp_id, Attendance.date == date_obj).first()
                    if not existing:
                        new_att = Attendance(
                            emp_id=emp_id,
                            date=date_obj,
                            in_duration=rec.get('In_Duration'),
                            out_duration=rec.get('Out_Duration'),
                            attendance_status=rec.get('Attendance'),
                            source_file=file.filename
                        )
                        db.add(new_att)
                        saved_count += 1
                results.append({"filename": file.filename, "status": "success", "type": detected_type, "details": f"Saved {saved_count} records"})

            db.commit()
        except Exception as e:
            db.rollback()
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

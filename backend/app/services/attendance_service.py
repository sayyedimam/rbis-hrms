"""
Attendance Service
Business logic for attendance management and file processing
"""
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException
from typing import List, Dict
import logging
from datetime import date, datetime, timedelta

from app.repositories.attendance_repository import AttendanceRepository
from app.repositories.file_repository import FileRepository
from app.models import Attendance, Employee, UserRole
from app.utils.file_utils import calculate_file_hash, generate_safe_filename, normalize_emp_id
from app.utils.date_utils import parse_date, format_time
from app.services.cleaner import detect_and_clean_memory
from app.services.azure_storage_service import upload_bytes_to_azure_sync

logger = logging.getLogger(__name__)

class AttendanceService:
    """Handles attendance business logic"""
    
    def __init__(self, db: Session):
        self.db = db
        self.attendance_repo = AttendanceRepository(db)
        self.file_repo = FileRepository(db)
    
    def process_uploaded_files(
        self,
        files: List[UploadFile],
        admin: Employee
    ) -> Dict:
        """
        Process uploaded attendance files
        
        Args:
            files: List of uploaded files
            admin: Admin user uploading files
            
        Returns:
            Dictionary with processing results
        """
        results = []
        
        for file in files:
            logger.info(f"Received file for processing: {file.filename}")
            try:
                result = self._process_single_file(file, admin)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing file {file.filename}: {e}", exc_info=True)
                self.attendance_repo.rollback()
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "reason": str(e)
                })
        
        return {"message": "Upload processing complete", "results": results}
    
    def _process_single_file(
        self,
        file: UploadFile,
        admin: Employee
    ) -> Dict:
        """
        Process a single attendance file
        
        Args:
            file: Uploaded file
            admin: Admin user
            
        Returns:
            Processing result dictionary
        """
        # Read file content
        content = file.file.read() # Read directly from SpooledTemporaryFile synchronously
        
        # Calculate hash for duplicate detection
        file_hash = calculate_file_hash(content)
        existing_file = self.file_repo.get_by_hash(file_hash)
        
        if existing_file:
            logger.info(f"[SYSTEM] File {file.filename} already uploaded (Hash collision). Skipping Azure upload.")
        
        # Try to use pre-cleaned data if available (passed from API layer)
        if hasattr(file, 'cleaned_data') and file.cleaned_data:
            cleaned_data = file.cleaned_data
            detected_type = getattr(file, 'detected_type', "In/Out Duration Report")
            logger.info(f"Using pre-cleaned data for {file.filename}")
        else:
            # Clean and detect file format (fallback)
            cleaned_data, detected_type = detect_and_clean_memory(content)
            logger.info(f"[DEBUG] Processing file: {file.filename} | Detected Type: {detected_type}")
        
        if not cleaned_data:
            logger.error(f"[ERROR] Rejecting {file.filename}: {detected_type}")
            return {
                "filename": file.filename,
                "status": "error",
                "reason": detected_type
            }
        
        # 1. PRE-VALIDATION: Normalize IDs and filter out invalid records
        import re
        valid_records = []
        skipped_records = []
        for i, rec in enumerate(cleaned_data):
            raw_id = rec.get('EmpID', '')
            emp_id = normalize_emp_id(raw_id)
            
            # Check if the normalized ID is valid (RBIS followed by exactly 4 digits)
            if not emp_id or not re.match(r'^RBIS\d{4}$', emp_id):
                skipped_records.append(f"Record {i+1}: Skipped invalid ID '{raw_id}'")
                continue
            
            if not rec.get('Date'):
                skipped_records.append(f"Record {i+1}: Skipped — missing attendance date")
                continue
            
            # Update the record with the normalized ID
            rec['EmpID'] = emp_id
            valid_records.append(rec)
        
        if skipped_records:
            logger.warning(f"[WARN] {file.filename}: Skipped {len(skipped_records)} invalid records: {'; '.join(skipped_records[:5])}")
        
        if not valid_records:
            logger.error(f"[ERROR] {file.filename}: No valid records found after filtering")
            return {
                "filename": file.filename,
                "status": "error",
                "reason": "No valid attendance records found in the file. All records had invalid Employee IDs or missing dates."
            }
        
        # Replace cleaned_data with only the valid records
        cleaned_data = valid_records

        # 2. FILE LOGGING (DB Entry for the file)
        # We check if hash exists to avoid duplicate WORK, not just duplicate FILES.
        if not existing_file:
            safe_filename = generate_safe_filename(file.filename)
            
            # Create file upload log entry first (but don't commit yet)
            log_data = {
                "filename": file.filename,
                "uploaded_by": admin.email,
                "report_type": detected_type,
                "file_hash": file_hash,
                "file_path": safe_filename
            }
            upload_log = self.file_repo.create(log_data)
            logger.info(f"Created pending file log ID: {upload_log.id}")
            
            # 3. AZURE UPLOAD (Only if it's a new file)
            try:
                upload_bytes_to_azure_sync(content, safe_filename, getattr(file, 'content_type', "application/octet-stream"))
                logger.info(f"Successfully uploaded {safe_filename} to Azure")
            except Exception as e:
                logger.error(f"Azure upload failed: {e}")
                self.attendance_repo.rollback() # Rollback the log entry
                return {
                    "filename": file.filename,
                    "status": "error",
                    "reason": f"Azure Storage failure: {str(e)}"
                }
        else:
            logger.info(f"Using existing upload record for {file.filename}")
            safe_filename = existing_file.file_path
        
        # 4. DATABASE PROCESSING (Attendance Records)
        try:
            saved_count, updated_count = self._process_attendance_records(
                cleaned_data,
                file.filename
            )
            
            # Commit everything (File Log + Attendance Records)
            self.attendance_repo.commit()
            logger.info(f"Completed processing {file.filename}: Saved {saved_count}, Updated {updated_count}")
            
            skipped_count = len(skipped_records)
            details = f"Processed {len(cleaned_data)} records (Saved: {saved_count}, Updated: {updated_count})"
            if skipped_count:
                details += f", Skipped: {skipped_count} invalid records"
            
            return {
                "filename": file.filename,
                "status": "success",
                "type": detected_type,
                "details": details
            }
        except Exception as e:
            logger.error(f"Database error processing records for {file.filename}: {e}")
            self.attendance_repo.rollback()
            return {
                "filename": file.filename,
                "status": "error",
                "reason": f"Database processing error: {str(e)}"
            }
    
    def _process_attendance_records(
        self,
        cleaned_data: List[Dict],
        source_filename: str
    ) -> tuple:
        """
        Process attendance records from cleaned data
        
        Args:
            cleaned_data: List of cleaned attendance records
            source_filename: Source file name
            
        Returns:
            Tuple of (saved_count, updated_count)
        """
        saved_count = 0
        updated_count = 0
        
        logger.info(f"[INFO] Processing {len(cleaned_data)} records from {source_filename}")
        
        for rec in cleaned_data:
            # Normalize employee ID
            raw_id = str(rec.get('EmpID', '')).strip()
            emp_id = normalize_emp_id(raw_id)
            
            if not emp_id:
                continue
            
            # Parse date
            date_val = rec.get('Date')
            date_obj = parse_date(date_val)
            
            if not date_obj:
                logger.error(f"Could not parse date '{date_val}' for {emp_id}")
                continue
            
            # Check if record exists
            existing = self.attendance_repo.get_by_emp_and_date(emp_id, date_obj)
            
            # Prepare record data
            record_data = {
                "first_in": format_time(rec.get('First_In')),
                "last_out": format_time(rec.get('Last_Out')),
                "in_duration": format_time(rec.get('In_Duration')),
                "out_duration": format_time(rec.get('Out_Duration')),
                "total_duration": format_time(rec.get('Total_Duration')),
                "punch_records": rec.get('Punch_Records'),
                "attendance_status": rec.get('Attendance'),
                "employee_name": rec.get('Employee_Name'),
                "source_file": source_filename
            }
            
            if existing:
                # Update existing record
                self.attendance_repo.update(existing, record_data)
                updated_count += 1
                logger.info(f"[UPDATE] {emp_id} | {date_obj} | In: {record_data['first_in']} | Out: {record_data['last_out']}")
            else:
                # Create new record
                record_data.update({
                    "emp_id": emp_id,
                    "date": date_obj
                })
                self.attendance_repo.create(record_data)
                saved_count += 1
                logger.info(f"[INSERT] {emp_id} | {date_obj} | In: {record_data['first_in']} | Out: {record_data['last_out']}")
        
        return saved_count, updated_count
    
    def get_attendance_records(self, user: Employee, start_date: str = None, end_date: str = None) -> List:
        """
        Get attendance records within a date range.
        Handles role-based access and excludes non-present records on Sundays/Holidays.
        """
        # 1. Determine date objects
        start_obj = parse_date(start_date) if start_date else None
        end_obj = parse_date(end_date) if end_date else None
        
        # 2. Fetch Holidays for filtering
        from app.repositories.leave_repository import LeaveRepository
        leave_repo = LeaveRepository(self.db)
        # We need a range that covers the possible data window
        holidays = leave_repo.get_all_holidays() # Small table, okay to get all
        holiday_dates = {h.date.isoformat() if hasattr(h.date, 'isoformat') else str(h.date) for h in holidays}

        # 3. Default Range Logic
        if not start_obj and not end_obj:
            latest = self.attendance_repo.get_latest_date()
            end_obj = max(latest, date.today()) if latest else date.today()
            start_obj = end_obj - timedelta(days=31)
        elif not start_obj:
             start_obj = end_obj - timedelta(days=31)
        elif not end_obj:
             end_obj = start_obj + timedelta(days=31)

        # 4. Query based on role
        if user.role == UserRole.EMPLOYEE:
            records = self.attendance_repo.get_by_date_range(
                emp_id=user.emp_id,
                start_date=start_obj,
                end_date=end_obj
            )
        else:
            records = self.attendance_repo.get_by_date_range(
                start_date=start_obj,
                end_date=end_obj
            )
            
        # Helper: check if a date is a non-working day (Sunday, 1st/3rd Saturday, or public holiday)
        def is_non_working_day(d, holiday_set):
            if d.weekday() == 6:  # Sunday
                return True
            if d.weekday() == 5:  # Saturday
                if (1 <= d.day <= 7) or (15 <= d.day <= 21):  # 1st or 3rd Saturday
                    return True
            iso = d.isoformat() if hasattr(d, 'isoformat') else str(d)
            if iso in holiday_set:
                return True
            return False
        
        # 5. Enrich, Filter and Flatten
        result = []
        for r in records:
            date_iso = r.date.isoformat() if hasattr(r.date, 'isoformat') else str(r.date)
            
            # Skip non-working days where employee was not present
            if is_non_working_day(r.date, holiday_dates) and r.attendance_status != 'Present':
                continue
                
            data = {c.name: getattr(r, c.name) for c in r.__table__.columns}
            data['date'] = date_iso
            
            # Resolve name
            data['employee_name'] = (r.owner.full_name if r.owner else None) or r.employee_name
            
            # Classification helper (previously Type A vs Type B in frontend)
            # True if it has a duration string with ':'. 
            data['has_duration_details'] = bool(r.in_duration and ':' in r.in_duration)
            
            result.append(data)
        
        # 6. MACHINE ERROR DETECTION
        # If ALL employees were absent on a WORKING day, it's likely a machine error.
        # Group records by date and check.
        from collections import defaultdict
        date_groups = defaultdict(list)
        for rec in result:
            date_groups[rec['date']].append(rec)
        
        for dt, recs in date_groups.items():
            # Only check working days (non-working days were already filtered above)
            if len(recs) == 0:
                continue
                
            absent_count = sum(1 for r in recs if r.get('attendance_status') == 'Absent')
            absence_rate = absent_count / len(recs)
            
            # If more than 95% of employees are absent on a working day, it's likely a machine error.
            # This accounts for edge cases where 1 or 2 people (like security) might be marked Present/Manual.
            if absence_rate > 0.95:
                logger.warning(f"[MACHINE ERROR] {absent_count}/{len(recs)} ({absence_rate:.1%}) employees marked absent on {dt} — likely a machine error")
                for r in recs:
                    if r.get('attendance_status') == 'Absent':
                        r['attendance_status'] = 'Machine Error'
            
        return result
    
    def update_attendance_record(
        self,
        attendance_id: int,
        update_data: Dict
    ) -> Dict:
        """
        Update attendance record
        
        Args:
            attendance_id: Attendance record ID
            update_data: Fields to update
            
        Returns:
            Updated record data
            
        Raises:
            HTTPException: If record not found
        """
        record = self.attendance_repo.get_by_id(attendance_id)
        
        if not record:
            raise HTTPException(status_code=404, detail="Attendance record not found")
        
        # Update record
        self.attendance_repo.update(record, update_data)
        self.attendance_repo.commit()
        
        return {"message": "Attendance record updated successfully"}

    def delete_attendance_record(self, attendance_id: int) -> Dict:
        """
        Delete attendance record
        
        Args:
            attendance_id: Attendance record ID
            
        Returns:
            Success message
            
        Raises:
            HTTPException: If record not found
        """
        record = self.attendance_repo.get_by_id(attendance_id)
        if not record:
            raise HTTPException(status_code=404, detail="Attendance record not found")
        
        self.attendance_repo.delete(record)
        self.attendance_repo.commit()
        
        return {"message": "Attendance record deleted successfully"}

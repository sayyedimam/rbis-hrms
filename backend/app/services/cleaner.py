import pandas as pd
import io
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def detect_and_clean_memory(file_content):
    """
    Simplified cleaner: Only supports the 'In Out Duration Report' format.
    Returns (cleaned_data, detected_type)
    """
    try:
        # Try reading as Excel first
        try:
            df_raw = pd.read_excel(io.BytesIO(file_content), header=None)
        except:
            # Fallback to CSV with tab/comma/semicolon detection
            try:
                df_raw = pd.read_csv(io.BytesIO(file_content), header=None, sep=None, engine='python')
            except:
                return None, "Invalid Format"

        logger.info(f"Cleaner: Processing file with shape {df_raw.shape}")
        
        cleaned_data = []
        current_attendance_date = None
        header_found = False
        title_found = False
        col_map = {}

        # Keywords for dynamic column detection
        REQUIRED_COLS = {
            "sno": ["s.no", "sno", "serial"],
            "emp_id": ["employee code", "emp id", "employee id", "emp code", "id"],
            "emp_name": ["employee name", "name", "emp name"],
            "in_dur": ["in duration", "in_duration", "in(hrs)"],
            "out_dur": ["out_duration", "out duration", "out(hrs)"],
            "punches": ["punch records", "punches", "punch_records", "log"]
        }

        for index, row in df_raw.iterrows():
            row_list = [str(val).strip() if pd.notna(val) else "" for val in row.values]
            row_str = " ".join(row_list).lower()

            # 0. Strict Title Check: Must find "In Out Duration Report" in the first 10 rows
            if not title_found and index < 10:
                if 'in out duration report' in row_str:
                    logger.info("Cleaner: 'In Out Duration Report' title found.")
                    title_found = True
            
            # 1. Capture Date from header
            if 'attendance date-' in row_str:
                date_match = re.search(r'(\d{1,2}[-/][a-z]{3}[-/]\d{4})', row_str)
                if not date_match:
                    date_match = re.search(r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})', row_str)
                
                if date_match:
                    current_attendance_date = date_match.group(1)
                    try:
                        current_attendance_date = pd.to_datetime(current_attendance_date).strftime('%Y-%m-%d')
                    except: pass
                continue

            # 2. Detect Header Row (only after title or if title is on same row)
            if not header_found and title_found:
                temp_map = {}
                # Look for a row that has at least 4 of our required column labels
                for i, val in enumerate(row_list):
                    val_clean = val.lower()
                    for col_key, labels in REQUIRED_COLS.items():
                        # Use stricter matching for labels (exact or with spaces)
                        if any(label == val_clean or f" {label} " in f" {val_clean} " or val_clean.startswith(f"{label}(") for label in labels):
                            temp_map[col_key] = i
                
                if len(temp_map) >= 4:
                    col_map = temp_map
                    logger.info(f"Cleaner: Column map detected: {col_map}")
                    header_found = True
                    continue

            # 3. Process Data Rows
            if header_found and 'emp_id' in col_map:
                sno_idx = col_map.get('sno')
                if sno_idx is not None:
                    sno_val = row_list[sno_idx]
                    if sno_val and sno_val.replace('.','',1).isdigit() and float(sno_val) > 0:
                        try:
                            emp_id_raw = row_list[col_map['emp_id']]
                            emp_name = row_list[col_map['emp_name']] if 'emp_name' in col_map else "Unknown"
                            in_dur = row_list[col_map['in_dur']] if 'in_dur' in col_map else "00:00"
                            out_dur = row_list[col_map['out_dur']] if 'out_dur' in col_map else "00:00"
                            punch_log = row_list[col_map['punches']] if 'punches' in col_map else ""

                            # STRICT VALIDATION: If EmpID looks like a time string, it's a structural mismatch
                            if re.match(r'^\d{1,2}:\d{2}$', emp_id_raw):
                                logger.error(f"Cleaner: Structural Mismatch at row {index+1}. Detected EmpID '{emp_id_raw}' looks like a timestamp.")
                                return None, f"Structural Error: Column mismatch. Column detected as 'Employee ID' contains timestamps ('{emp_id_raw}'). Please check file format."

                            if not emp_id_raw or emp_id_raw.lower() == 'nan':
                                return None, f"Invalid Record at row {index+1}: Missing Employee ID"

                            # Parse First In / Last Out from Punches
                            first_in, last_out = "--:--", "--:--"
                            punch_count = 0
                            if punch_log and punch_log.lower() != 'nan':
                                clean_punches = re.sub(r'\(in\)|\(out\)', '', punch_log, flags=re.IGNORECASE)
                                times = [t.strip() for t in clean_punches.split(',') if ':' in t]
                                if times:
                                    first_in = times[0]
                                    last_out = times[-1]
                                    punch_count = len(times)

                            # Fallback
                            if first_in == "--:--" and ":" in in_dur: first_in = in_dur
                            if last_out == "--:--" and ":" in out_dur: last_out = out_dur

                            # Total Duration
                            total_duration = "00:00"
                            def to_min(ts):
                                if ':' not in str(ts): return 0
                                try:
                                    clean_ts = re.sub(r'\(.*?\)', '', str(ts)).strip()
                                    h, m = map(int, clean_ts.split(':')[:2])
                                    return h * 60 + m
                                except: return 0
                                
                            if first_in != "--:--" and last_out != "--:--":
                                span_min = to_min(last_out) - to_min(first_in)
                                if span_min < 0: span_min = 0
                                total_duration = f"{span_min // 60:02d}:{span_min % 60:02d}"
                            else:
                                total_min = to_min(in_dur) + to_min(out_dur)
                                total_duration = f"{total_min // 60:02d}:{total_min % 60:02d}"

                            if not current_attendance_date:
                                return None, f"Invalid State: Record found before Date header at row {index+1}"

                            is_absent = in_dur.lower() in ['00:00', '0:00', '', 'nan', 'none', 'nil', '-']
                            is_present = not is_absent and punch_count >= 4

                            cleaned_data.append({
                                'Date': current_attendance_date,
                                'EmpID': emp_id_raw,
                                'Employee_Name': emp_name,
                                'In_Duration': in_dur,
                                'Out_Duration': out_dur,
                                'Total_Duration': total_duration,
                                'First_In': first_in,
                                'Last_Out': last_out,
                                'Punch_Records': punch_log,
                                'Attendance': 'Present' if is_present else 'Absent'
                            })
                        except Exception as e:
                            logger.error(f"Cleaner: Error at row {index+1}: {e}")
                            return None, f"Data Error at row {index+1}: {str(e)}"

        if not title_found:
            return None, "Invalid Format: Title 'In Out Duration Report' not found. Only this specific format is supported."

        if not header_found:
            return None, "Invalid Structure: Could not find required headers (S.No, Employee Code, etc.)"

        if not cleaned_data:
            return None, "Invalid Content: No attendance records identified"

        return cleaned_data, "In/Out Duration Report"
    except Exception as e:
        logger.error(f"Cleaner Error: {e}")
        return None, "Processing Error"

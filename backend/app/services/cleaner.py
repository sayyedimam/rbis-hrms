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

        for index, row in df_raw.iterrows():
            row_list = [str(val).strip() if pd.notna(val) else "" for val in row.values]
            row_str = " ".join(row_list)
            
            # 1. Capture Date from header (e.g., Attendance Date- 01-Jan-2026)
            if 'Attendance Date-' in row_str:
                date_match = re.search(r'(\d{1,2}[-/][A-Za-z]{3}[-/]\d{4})', row_str)
                if not date_match:
                    date_match = re.search(r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})', row_str)
                
                if date_match:
                    current_attendance_date = date_match.group(1)
                    try:
                        current_attendance_date = pd.to_datetime(current_attendance_date).strftime('%Y-%m-%d')
                    except: pass
                continue

            # 2. Capture Employee Rows (Check if S.No is in Column 1 and is numeric)
            if len(row) > 10:
                sno_val = str(row[1]).strip()
                if sno_val and sno_val.replace('.','',1).isdigit():
                    try:
                        if float(sno_val) > 0:
                            emp_id_raw = str(row[3]).strip()       # Col 3
                            emp_name = str(row[5]).strip()         # Col 5
                            in_dur = str(row[7]).strip()           # Col 7 (In Duration)
                            out_dur = str(row[8]).strip()          # Col 8 (Out Duration)
                            punch_log = str(row[10]).strip()       # Col 10 (Punch Records)
                            
                            if not emp_id_raw or emp_id_raw.lower() == 'nan':
                                continue

                            # Absence check
                            is_absent = in_dur.lower() in ['00:00', '0:00', '', 'nan', 'none', 'nil', '-']
                            
                            # Parse First In / Last Out from Punches
                            first_in, last_out = "--:--", "--:--"
                            if punch_log and punch_log.lower() != 'nan':
                                # Strip tags like (in) or (out)
                                clean_punches = re.sub(r'\(in\)|\(out\)', '', punch_log, flags=re.IGNORECASE)
                                times = [t.strip() for t in clean_punches.split(',') if ':' in t]
                                if times:
                                    first_in = times[0]
                                    last_out = times[-1]

                            # Fallback if punches are empty but durations look like times
                            if first_in == "--:--" and ":" in in_dur: first_in = in_dur
                            if last_out == "--:--" and ":" in out_dur: last_out = out_dur

                            # Calculate Total Duration (Actual Span between First In and Last Out)
                            total_duration = "00:00"
                            try:
                                def to_min(ts):
                                    if ':' not in str(ts): return 0
                                    try:
                                        # Handle cases like "10:02(in)" or just "10:02"
                                        clean_ts = re.sub(r'\(.*?\)', '', str(ts)).strip()
                                        h, m = map(int, clean_ts.split(':')[:2])
                                        return h * 60 + m
                                    except: return 0
                                
                                # Use span between First In and Last Out for "Total Office Duration"
                                if first_in != "--:--" and last_out != "--:--":
                                    span_min = to_min(last_out) - to_min(first_in)
                                    if span_min < 0: span_min = 0 # Handle overnight if needed, but usually daily
                                    total_duration = f"{span_min // 60:02d}:{span_min % 60:02d}"
                                else:
                                    # Fallback to sum of provided durations
                                    total_min = to_min(in_dur) + to_min(out_dur)
                                    total_duration = f"{total_min // 60:02d}:{total_min % 60:02d}"
                            except: pass

                            if not current_attendance_date:
                                continue

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
                                'Attendance': 'Absent' if is_absent else 'Present'
                            })
                    except: continue

        return cleaned_data, "In/Out Duration Report"
    except Exception as e:
        logger.error(f"Cleaner Error: {e}")
        return None, "Processing Error"

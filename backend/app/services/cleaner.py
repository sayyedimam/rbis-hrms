import pandas as pd
import numpy as np
import io
import re

def clean_attendance_data_of_employee(file_content):
    """
    Cleans 'Employee In/Out Duration Daily Attendance' reports. (Type A)
    Returns a list of dicts or None.
    """
    try:
        # Try excel first
        df_raw = pd.read_excel(io.BytesIO(file_content), header=None)
    except:
        try:
            df_raw = pd.read_csv(io.BytesIO(file_content), header=None, encoding='latin1', on_bad_lines='skip', sep=None, engine='python')
        except:
            return None

    cleaned_data = []
    current_attendance_date = None

    for index, row in df_raw.iterrows():
        row_list = [str(val).strip() for val in row.values]
        row_str = " ".join(row_list)
        
        if 'Attendance Date' in row_str:
            for val in row_list:
                if any(char in val for char in ['-', '/']) and len(val) >= 6:
                    if 'Attendance' not in val and 'Date' not in val:
                        current_attendance_date = val
                        break
            continue
            
        for col_idx in range(min(3, len(row))):
            val = str(row[col_idx]).strip()
            if val.replace('.','',1).isdigit():
                try:
                    s_no = float(val)
                    if s_no > 0 and len(row) >= 9:
                        in_duration = str(row[7]).strip()
                        out_duration = str(row[8]).strip()
                        is_absent = in_duration.lower() in ['00:00', '0', '0:00', '', 'nan', 'none', 'nil', '-']
                        
                        # Normalize Date
                        final_date = current_attendance_date
                        try:
                            final_date = pd.to_datetime(current_attendance_date).strftime('%Y-%m-%d')
                        except: pass

                        record = {
                            'Date': final_date,
                            'EmpID': str(row[3]).strip(),
                            'Employee_Name': str(row[5]).strip(),
                            'In_Duration': in_duration,
                            'Out_Duration': out_duration,
                            'Attendance': 'Absent' if is_absent else 'Present'
                        }
                        cleaned_data.append(record)
                        break
                except: continue

    return cleaned_data if cleaned_data else None

def clean_daily_attendance(file_content):
    """
    Cleans 'Monthly Detailed Attendance Report'. (Type B)
    """
    try:
        df_raw = pd.read_excel(io.BytesIO(file_content), header=None)
    except:
        try:
            df_raw = pd.read_csv(io.BytesIO(file_content), header=None, encoding='latin1', on_bad_lines='skip', sep=None, engine='python')
        except:
            return None
        
    date_labels_row = -1
    for i in range(min(50, len(df_raw))):
        row_str = " ".join([str(v) for v in df_raw.iloc[i].values]).lower()
        if 'day1' in row_str or 'day 1' in row_str:
            date_labels_row = i
            break
            
    if date_labels_row == -1: return None

    # Capture the Month/Year if possible to make dates more robust
    header_str = " ".join([str(v) for v in df_raw.iloc[:10].values.flatten()]).lower()
    year_match = re.search(r'(20\d{2})', header_str)
    extracted_year = year_match.group(1) if year_match else str(pd.Timestamp.now().year)
    
    date_values_row = date_labels_row + 1
    date_labels = df_raw.iloc[date_labels_row].values
    date_values = df_raw.iloc[date_values_row].values
    
    date_map = {}
    for i in range(len(date_labels)):
        label, val = str(date_labels[i]).strip(), str(date_values[i]).strip()
        if 'Day' in label and 'Days' not in label and val != '' and val.lower() != 'nan':
            # Check row below if current is numeric only
            if not any(char in val for char in ['-', '/']):
                if date_labels_row + 2 < len(df_raw):
                    val = str(df_raw.iloc[date_labels_row + 2, i]).strip()
            
            # Robust normalization: if year is missing, append it
            if val and not re.search(r'\d{4}', val) and any(char in val for char in ['-', '/']):
                # val looks like "22-Dec", make it "22-Dec-2024"
                sep = '-' if '-' in val else '/'
                val = f"{val}{sep}{extracted_year}"

            # Normalize to ISO
            try:
                norm_date = pd.to_datetime(val, dayfirst=True).strftime('%Y-%m-%d')
                date_map[i] = norm_date
            except:
                if any(char in val for char in ['-', '/']):
                    date_map[i] = val

    cleaned_rows = []
    current_emp_id = None

    for i, row in df_raw.iterrows():
        row_list = [str(val).strip() for val in row.values]
        row_str = " ".join(row_list)
        
        # Robust Employee ID Capture
        lower_row_str = row_str.lower()
        if any(lbl in lower_row_str for lbl in ['employee code', 'emp code', 'emp. code', 'emp id', 'employee id']):
            for idx, val in enumerate(row_list):
                v_low = val.lower()
                if any(lbl in v_low for lbl in ['employee code', 'emp code', 'emp. code', 'emp id', 'employee id']):
                    # 1. Check current cell for something numeric or alphanumeric after the label
                    # Try to strip common separators
                    pot = v_low.replace('employee code', '').replace('emp code', '').replace('emp. code', '').replace('employee id', '').replace('emp id', '')
                    pot = pot.replace(':', '').replace('-', '').replace('=', '').strip()
                    
                    if pot and pot != 'nan' and len(pot) >= 1:
                        current_emp_id = pot.upper()
                        break
                        
                    # 2. Check subsequent cells in the same row
                    for next_val in row_list[idx+1:idx+6]:
                        clean_next = str(next_val).replace(':', '').replace('-', '').replace('=', '').strip()
                        if clean_next and clean_next.lower() != 'nan' and len(clean_next) >= 1:
                            # Avoid capturing other labels like "Employee Name"
                            if 'name' not in clean_next.lower() and 'dept' not in clean_next.lower():
                                current_emp_id = clean_next.upper()
                                break
                    if current_emp_id: break
            continue
        
        if 'In Time' in row_str:
            # Fallback: If we haven't found an EmpID yet, look at the first few cells of this row
            # or the row above to see if there's a standalone ID
            if not current_emp_id:
                for cand in row_list[:3]:
                    if cand.isdigit() and len(cand) >= 2:
                        current_emp_id = cand
                        break
            
            if not current_emp_id:
                # Still nothing? Use a placeholder so we can at least see the data
                current_emp_id = "UNKNOWN_ID"

            in_row = row
            # Try to find Out Time row - it's usually the next one
            for look_ahead in range(1, 4):
                if i + look_ahead < len(df_raw):
                    out_row_candidate = df_raw.iloc[i + look_ahead]
                    out_row_str = " ".join([str(v) for v in out_row_candidate.values])
                    if 'Out Time' in out_row_str:
                        out_row = out_row_candidate
                        for col_idx, date_val in date_map.items():
                            if col_idx < len(in_row):
                                in_time = str(in_row[col_idx]).strip()
                                out_time = str(out_row[col_idx]).strip() if col_idx < len(out_row) else ""
                                is_absent = in_time.lower() in ['a', 'none', 'nan', '', '00:00', '0:00', 'nil', '-', '0']
                                
                                cleaned_rows.append({
                                    'Date': date_val,
                                    'EmpID': current_emp_id,
                                    'In_Duration': in_time if not is_absent else '',
                                    'Out_Duration': out_time if not is_absent else '',
                                    'Attendance': 'Absent' if is_absent else 'Present'
                                })
                        print(f"Captured data for EmpID: {current_emp_id}")
                        break

    return cleaned_rows if cleaned_rows else None

def clean_employee_master(file_content):
    """
    Detects if the file is an Employee Master table.
    """
    try:
        df = pd.read_excel(io.BytesIO(file_content))
    except:
        return None
    
    cols = [str(c).lower() for c in df.columns]
    # Check for core columns
    if any('empid' in c for c in cols) and any('email' in c for c in cols):
        # We don't clean it here because the main.py upload_employees handles it, 
        # but we return a signal that it's a valid master file.
        return [{"is_master": True, "df": df}]
    return None

def detect_and_clean_memory(file_content):
    """
    Attempts to detect and clean from memory.
    """
    # 1. Check for Employee Master
    master_data = clean_employee_master(file_content)
    if master_data:
        return master_data, "Employee Master"

    # 2. Type B has day1
    b_data = clean_daily_attendance(file_content)
    if b_data:
        return b_data, "Monthly Detailed Report (Type B)"
    
    # 3. Type A
    a_data = clean_attendance_data_of_employee(file_content)
    if a_data:
        return a_data, "In/Out Duration Report (Type A)"
        
    return None, "Unknown format"

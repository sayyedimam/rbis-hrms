import pandas as pd
import sys

file_path = r"c:\Users\A\Girish\Angular\Attendix-main\backend\storage\records\20260110_160559_EmployeeInOutDurationDailyAttendance RBIS.xls"
try:
    df = pd.read_excel(file_path, header=None)
    print(f"File: {file_path}")
    print(f"Total Rows: {len(df)}")
    
    # Try to find the header row or some data row
    for i in range(min(50, len(df))):
        row = df.iloc[i].values
        row_str = " | ".join([str(x) for x in row[:15]])
        print(f"Row {i:2}: {row_str}")
        
except Exception as e:
    print(f"Error: {e}")

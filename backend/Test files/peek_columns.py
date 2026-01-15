import pandas as pd
import sys

file_path = r"c:\Users\A\Girish\Angular\Attendix-main\backend\storage\records\20260110_160559_EmployeeInOutDurationDailyAttendance RBIS.xls"
try:
    df = pd.read_excel(file_path, header=None)
    print(f"Shape: {df.shape}")
    # Print the first 20 rows of the first 15 columns
    print(df.iloc[:20, :15].to_string())
except Exception as e:
    print(f"Error: {e}")

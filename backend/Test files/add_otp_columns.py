"""
Database Migration Script: Add OTP columns to employees table
Run this script once to add the new OTP-related columns
"""
import pyodbc
from dotenv import load_dotenv
import os

load_dotenv()

# Extract connection details from DATABASE_URL
db_url = os.getenv("DATABASE_URL")
# Format: mssql+pyodbc://localhost/attendix_db?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes&TrustServerCertificate=yes

# For SQL Server with Windows Authentication
conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=attendix_db;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

try:
    print("Connecting to database...")
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    print("Adding OTP columns to employees table...")
    
    # Check if columns already exist
    cursor.execute("""
        SELECT COUNT(*) 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'employees' AND COLUMN_NAME = 'otp_code'
    """)
    
    if cursor.fetchone()[0] == 0:
        # Add otp_code column
        cursor.execute("""
            ALTER TABLE employees
            ADD otp_code NVARCHAR(10) NULL
        """)
        print("✅ Added otp_code column")
    else:
        print("⚠️  otp_code column already exists")
    
    # Check and add otp_created_at
    cursor.execute("""
        SELECT COUNT(*) 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'employees' AND COLUMN_NAME = 'otp_created_at'
    """)
    
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            ALTER TABLE employees
            ADD otp_created_at DATETIME NULL
        """)
        print("✅ Added otp_created_at column")
    else:
        print("⚠️  otp_created_at column already exists")
    
    # Check and add otp_purpose
    cursor.execute("""
        SELECT COUNT(*) 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'employees' AND COLUMN_NAME = 'otp_purpose'
    """)
    
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            ALTER TABLE employees
            ADD otp_purpose NVARCHAR(20) NULL
        """)
        print("✅ Added otp_purpose column")
    else:
        print("⚠️  otp_purpose column already exists")
    
    conn.commit()
    print("\n✅ Migration completed successfully!")
    print("You can now restart your backend server.")
    
except Exception as e:
    print(f"\n❌ Migration failed: {str(e)}")
    if 'conn' in locals():
        conn.rollback()
finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()

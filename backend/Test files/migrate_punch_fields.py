import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

def migrate():
    DEFAULT_URL = "mssql+pyodbc://localhost/attendix_db?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes&TrustServerCertificate=yes"
    raw_url = os.getenv("DATABASE_URL") or DEFAULT_URL
    conn_str = raw_url.replace("mssql+pyodbc://", "DRIVER={ODBC Driver 17 for SQL Server};")
    # Clean up the connection string for pyodbc
    if "DRIVER" not in conn_str:
        conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};{conn_str}"
    
    # Handle trusted_connection if present
    conn_str = conn_str.replace("trusted_connection=yes", "Trusted_Connection=yes")
    conn_str = conn_str.replace("TrustServerCertificate=yes", "TrustServerCertificate=yes")
    
    # Actually, SQLAlchemy URL format is different from pyodbc.
    # Let's just use the known format for this user's system.
    db_name = "attendix_db"
    conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER=localhost;DATABASE={db_name};Trusted_Connection=yes;TrustServerCertificate=yes"

    print(f"Connecting to {db_name}...")
    try:
        conn = pyodbc.connect(conn_str, autocommit=True)
        cursor = conn.cursor()
        
        print("Adding new columns to attendance table...")
        
        columns_to_add = [
            ("total_duration", "VARCHAR(100)"),
            ("punch_records", "VARCHAR(2000)")
        ]
        
        # Check and alter types for first_in/last_out if they were Time
        # In MSSQL, altering Time to VARCHAR needs care if data exists, but we can try direct alter.
        # However, let's just make sure they are correct.
        
        for col_name, col_type in columns_to_add:
            try:
                cursor.execute(f"ALTER TABLE attendance ADD {col_name} {col_type}")
                print(f"Added column: {col_name}")
            except Exception as e:
                if "already exists" in str(e).lower() or "Column names in each table must be unique" in str(e):
                    print(f"Column {col_name} already exists.")
                else:
                    print(f"Error adding {col_name}: {e}")

        # Update types of first_in and last_out to String to match new model
        # We'll drop and recreate if needed, or just alter. 
        # Altering from TIME to VARCHAR is usually fine in T-SQL.
        for col in ["first_in", "last_out"]:
            try:
                cursor.execute(f"ALTER TABLE attendance ALTER COLUMN {col} VARCHAR(50)")
                print(f"Updated type for: {col}")
            except Exception as e:
                print(f"Error updating {col}: {e}")

        conn.close()
        print("Migration complete!")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    migrate()

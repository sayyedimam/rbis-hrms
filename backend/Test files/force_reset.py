from database import engine
from sqlalchemy import text
import models

def force_reset():
    with engine.connect() as conn:
        print("Attempting to forcefully drop existing tables...")
        
        # Order matters for foreign keys
        tables = ["attendance", "employees", "file_uploads"]
        
        for table in tables:
            try:
                # Direct SQL check for table existence (more robust than IF EXISTS in some MSSQL versions)
                conn.execute(text(f"""
                IF OBJECT_ID('dbo.{table}', 'U') IS NOT NULL 
                DROP TABLE dbo.{table};
                """))
                print(f"Successfully dropped (if it existed): {table}")
            except Exception as e:
                print(f"Failed to drop {table}: {e}")
        
        conn.commit()

    print("Recreating tables with the NEW schema (No Foreign Keys)...")
    from database import Base
    models.Base.metadata.create_all(bind=engine)
    print("Database has been reset and updated.")

if __name__ == "__main__":
    force_reset()

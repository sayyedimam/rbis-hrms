from app.core.database import engine
from sqlalchemy import text

def mega_reset():
    print("--- MEGA RESET: Forcefully Cleaning SQL Server ---")
    confirm = input("This will drop ALL tables and ALL their constraints. Type 'RESET' to confirm: ")
    if confirm != 'RESET':
        print("Aborted.")
        return

    with engine.connect() as conn:
        # 1. Drop constraints first
        print("Searching for and dropping all Foreign Key constraints...")
        fk_sql = """
        DECLARE @sql NVARCHAR(MAX) = '';
        SELECT @sql += 'ALTER TABLE ' + QUOTENAME(OBJECT_SCHEMA_NAME(parent_object_id)) + '.' + QUOTENAME(OBJECT_NAME(parent_object_id)) + 
        ' DROP CONSTRAINT ' + QUOTENAME(name) + ';'
        FROM sys.foreign_keys;
        EXEC sp_executesql @sql;
        """
        try:
            conn.execute(text(fk_sql))
            conn.commit()
            print("Successfully dropped all foreign keys.")
        except Exception as e:
            print(f"No foreign keys to drop or error: {e}")

        # 2. Drop the tables
        tables = ["attendance", "employees", "file_uploads"]
        for table in tables:
            try:
                conn.execute(text(f"IF OBJECT_ID('dbo.{table}', 'U') IS NOT NULL DROP TABLE dbo.{table};"))
                print(f"Dropped table: {table}")
            except Exception as e:
                print(f"Error dropping {table}: {e}")
        
        conn.commit()
    
    print("\n--- Success! Recreating clean tables now... ---")
    from app.models import models
    models.Base.metadata.create_all(bind=engine)
    print("Tables recreated with the new flexible schema.")
    print("You can now start the backend and upload your files.")

if __name__ == "__main__":
    mega_reset()

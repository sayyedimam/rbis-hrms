from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import SessionLocal, engine

def cleanup_db():
    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                print("Starting cleanup...")
                
                # 1. Get Paid Leave ID or ensure it exists
                result = connection.execute(text("SELECT id FROM leave_types WHERE name = 'Paid Leave'"))
                paid_leave_row = result.fetchone()
                
                if not paid_leave_row:
                    print("'Paid Leave' not found. Creating it...")
                    connection.execute(text("INSERT INTO leave_types (name, annual_quota, is_paid, allow_carry_forward, is_active) VALUES ('Paid Leave', 20, 1, 1, 1)"))
                    result = connection.execute(text("SELECT id FROM leave_types WHERE name = 'Paid Leave'"))
                    paid_leave_row = result.fetchone()
                
                paid_leave_id = paid_leave_row[0]
                print(f"Keeping Leave Type ID: {paid_leave_id} (Paid Leave)")

                # 2. Delete extraneous Data (Balances, Requests, Types)
                # We use raw SQL to avoid model dependency issues and ensure direct execution
                
                print("Deleting old balances...")
                connection.execute(text(f"DELETE FROM leave_balances WHERE leave_type_id != {paid_leave_id}"))
                
                print("Deleting old requests...")
                connection.execute(text(f"DELETE FROM leave_requests WHERE leave_type_id != {paid_leave_id}"))
                
                print("Deleting old leave types...")
                connection.execute(text(f"DELETE FROM leave_types WHERE id != {paid_leave_id}"))
                
                transaction.commit()
                print("Cleanup complete! Only Paid Leave remains.")
                
            except Exception as e:
                transaction.rollback()
                print(f"Error during transaction: {e}")
                raise e
                
    except Exception as e:
        print(f"Database connection failed: {e}")

if __name__ == "__main__":
    cleanup_db()

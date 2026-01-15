from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import SessionLocal, engine

def sync_balances():
    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                print("Starting balance sync...")
                
                # 1. Get the current quota for "Paid Leave"
                result = connection.execute(text("SELECT id, annual_quota FROM leave_types WHERE name = 'Paid Leave'"))
                row = result.fetchone()
                
                if not row:
                    print("Paid Leave type not found!")
                    return

                paid_leave_id = row[0]
                new_quota = row[1]
                print(f"Paid Leave ID: {paid_leave_id}, Defined Quota: {new_quota}")

                # 2. Update all existing balances for this leave type to match the new quota
                # We update the 'allocated' column in leave_balances
                update_query = text(f"""
                    UPDATE leave_balances 
                    SET allocated = :quota 
                    WHERE leave_type_id = :lid
                """)
                
                result = connection.execute(update_query, {"quota": new_quota, "lid": paid_leave_id})
                print(f"Updated {result.rowcount} balance records to use quota: {new_quota}")
                
                transaction.commit()
                print("Sync complete.")
                
            except Exception as e:
                transaction.rollback()
                print(f"Error during sync: {e}")
                raise e
                
    except Exception as e:
        print(f"Database connection failed: {e}")

if __name__ == "__main__":
    sync_balances()

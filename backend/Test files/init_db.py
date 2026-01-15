from database import engine, Base
import models # Import models to ensure they are registered with Base

def init_db():
    print("Connecting to SQL Server and creating tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("Success! Tables created in attendix_db.")
    except Exception as e:
        print(f"Error during table creation: {e}")

if __name__ == "__main__":
    init_db()

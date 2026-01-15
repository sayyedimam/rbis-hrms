from database import engine, Base
import models

def reset_db():
    print("WARNING: This will delete ALL data in attendix_db.")
    confirm = input("Are you sure? (y/n): ")
    if confirm.lower() == 'y':
        print("Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        print("Recreating tables with new schema...")
        Base.metadata.create_all(bind=engine)
        print("Done! Database has been reset.")
    else:
        print("Aborted.")

if __name__ == "__main__":
    reset_db()

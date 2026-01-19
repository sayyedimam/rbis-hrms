"""
Database Dependencies
Provides database session for dependency injection
"""
from app.core.database import SessionLocal

def get_db():
    """
    Dependency to get database session
    
    Yields:
        Session: SQLAlchemy database session
        
    Note:
        Automatically closes session after request
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

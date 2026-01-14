"""
File Upload Repository
Database access layer for FileUploadLog model
"""
from sqlalchemy.orm import Session
from app.models.models import FileUploadLog
from typing import Optional, List

class FileRepository:
    """Handles all database operations for FileUploadLog model"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_hash(self, file_hash: str) -> Optional[FileUploadLog]:
        """
        Get file upload log by hash
        
        Args:
            file_hash: SHA-256 hash of file
            
        Returns:
            FileUploadLog or None if not found
        """
        return self.db.query(FileUploadLog).filter(
            FileUploadLog.file_hash == file_hash
        ).first()
    
    def get_by_id(self, log_id: int) -> Optional[FileUploadLog]:
        """Get file upload log by ID"""
        return self.db.query(FileUploadLog).filter(FileUploadLog.id == log_id).first()
    
    def get_all(self) -> List[FileUploadLog]:
        """Get all file upload logs"""
        return self.db.query(FileUploadLog).all()
    
    def create(self, log_data: dict) -> FileUploadLog:
        """
        Create new file upload log
        
        Args:
            log_data: Dictionary with log fields
            
        Returns:
            Created FileUploadLog object
        """
        log = FileUploadLog(**log_data)
        self.db.add(log)
        self.db.flush()  # Generate ID
        return log
    
    def exists_by_hash(self, file_hash: str) -> bool:
        """
        Check if file with hash already exists
        
        Args:
            file_hash: SHA-256 hash
            
        Returns:
            True if exists, False otherwise
        """
        return self.get_by_hash(file_hash) is not None
    
    def commit(self) -> None:
        """Commit transaction"""
        self.db.commit()
    
    def rollback(self) -> None:
        """Rollback transaction"""
        self.db.rollback()

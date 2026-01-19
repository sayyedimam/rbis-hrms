"""
File Upload Model
Contains file upload tracking model
"""
from sqlalchemy import Column, Integer, String, DateTime
from app.models.base import Base, get_ist_now

class FileUploadLog(Base):
    """File upload log model - tracks uploaded files"""
    __tablename__ = "file_uploads"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255))
    uploaded_at = Column(DateTime, default=get_ist_now)
    uploaded_by = Column(String(50))
    report_type = Column(String(100))
    file_hash = Column(String(64), unique=True, index=True)
    file_path = Column(String(500))

"""
Attendance Model
Contains Attendance tracking model
"""
from sqlalchemy import Column, Integer, String, Date, Boolean
from app.models.base import Base

class Attendance(Base):
    """Attendance model - tracks employee attendance records"""
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    emp_id = Column(String(50), index=True, nullable=False)
    date = Column(Date, index=True, nullable=False)
    first_in = Column(String(50), nullable=True)
    last_out = Column(String(50), nullable=True)
    in_duration = Column(String(100), nullable=True)
    out_duration = Column(String(100), nullable=True)
    total_duration = Column(String(100), nullable=True)
    punch_records = Column(String(2000), nullable=True)
    attendance_status = Column(String(50))
    source_file = Column(String(255))
    is_manually_corrected = Column(Boolean, default=False)
    corrected_by = Column(String(100), nullable=True)

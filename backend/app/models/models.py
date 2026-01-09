from sqlalchemy import Column, Integer, String, Date, Time, Enum, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
import datetime
import enum

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    HR = "HR"
    EMPLOYEE = "EMPLOYEE"

class UserStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    emp_id = Column(String(50), unique=True, index=True, nullable=True)
    full_name = Column(String(200), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    phone_number = Column(String(20), nullable=True)
    email = Column(String(150), unique=True, index=True, nullable=True)
    designation = Column(String(100), nullable=True)
    password_hash = Column(String(255), nullable=True)
    is_verified = Column(Boolean, default=False)
    verification_code = Column(String(10), nullable=True)
    role = Column(String(50), default="EMPLOYEE")
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    attendance_records = relationship(
        "Attendance", 
        primaryjoin="Employee.emp_id == Attendance.emp_id",
        foreign_keys="Attendance.emp_id",
        back_populates="owner"
    )

class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    emp_id = Column(String(50), index=True, nullable=False)
    date = Column(Date, index=True, nullable=False)
    first_in = Column(Time, nullable=True)
    last_out = Column(Time, nullable=True)
    in_duration = Column(String(100), nullable=True)
    out_duration = Column(String(100), nullable=True)
    attendance_status = Column(String(50))
    source_file = Column(String(255))
    is_manually_corrected = Column(Boolean, default=False)
    corrected_by = Column(String(100), nullable=True)
    
    owner = relationship(
        "Employee", 
        primaryjoin="Attendance.emp_id == Employee.emp_id",
        foreign_keys="Attendance.emp_id",
        back_populates="attendance_records"
    )

class FileUploadLog(Base):
    __tablename__ = "file_uploads"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255))
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)
    uploaded_by = Column(String(50))
    report_type = Column(String(100))
    file_hash = Column(String(64), unique=True, index=True)
    file_path = Column(String(500))

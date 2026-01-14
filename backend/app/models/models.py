from sqlalchemy import Column, Integer, String, Date, Time, Enum, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
import datetime
import enum
from datetime import timezone, timedelta

# IST Timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def get_ist_now():
    """Returns current datetime in IST timezone"""
    return datetime.datetime.now(IST)

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    HR = "HR"
    EMPLOYEE = "EMPLOYEE"
    CEO = "CEO"

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
    otp_code = Column(String(10), nullable=True)
    otp_created_at = Column(DateTime, nullable=True)
    otp_purpose = Column(String(20), nullable=True)  # SIGNUP or PASSWORD_RESET
    role = Column(String(50), default="EMPLOYEE")
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime, default=get_ist_now)

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
    uploaded_at = Column(DateTime, default=get_ist_now)
    uploaded_by = Column(String(50))
    report_type = Column(String(100))
    file_hash = Column(String(64), unique=True, index=True)
    file_path = Column(String(500))

class LeaveType(Base):
    __tablename__ = "leave_types"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True)
    annual_quota = Column(Integer, default=12)
    is_paid = Column(Boolean, default=True)
    allow_carry_forward = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

class LeaveBalance(Base):
    __tablename__ = "leave_balances"
    id = Column(Integer, primary_key=True, index=True)
    emp_id = Column(String(50), ForeignKey("employees.emp_id"), index=True)
    leave_type_id = Column(Integer, ForeignKey("leave_types.id"))
    year = Column(Integer, index=True)
    allocated = Column(Integer)
    used = Column(Integer, default=0)

class LeaveRequest(Base):
    __tablename__ = "leave_requests"
    id = Column(Integer, primary_key=True, index=True)
    emp_id = Column(String(50), ForeignKey("employees.emp_id"), index=True)
    leave_type_id = Column(Integer, ForeignKey("leave_types.id"))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    total_days = Column(Integer)
    reason = Column(String(500))
    status = Column(String(20), default="PENDING") # PENDING, APPROVED_BY_HR, APPROVED (Final by CEO), REJECTED
    hr_remarks = Column(String(500), nullable=True)
    ceo_remarks = Column(String(500), nullable=True)
    attachment_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=get_ist_now)

class LeaveApprovalLog(Base):
    __tablename__ = "leave_approval_logs"
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("leave_requests.id"))
    approver_id = Column(String(50), ForeignKey("employees.emp_id"))
    action = Column(String(20)) # HR_APPROVED, CEO_APPROVED, REJECTED
    remarks = Column(String(500), nullable=True)
    action_at = Column(DateTime, default=get_ist_now)

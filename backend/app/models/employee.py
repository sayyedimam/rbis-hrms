"""
Employee Model
Contains Employee model and related enums
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean
import enum
from app.models.base import Base, get_ist_now

class UserRole(str, enum.Enum):
    """User role enumeration"""
    SUPER_ADMIN = "SUPER_ADMIN"
    HR = "HR"
    EMPLOYEE = "EMPLOYEE"
    CEO = "CEO"

class UserStatus(str, enum.Enum):
    """User status enumeration"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    PENDING = "PENDING"

class Employee(Base):
    """Employee model - represents system users"""
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

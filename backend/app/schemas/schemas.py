from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import List, Optional
import datetime
import re

# ============================================================================
# AUTHENTICATION SCHEMAS
# ============================================================================

class SignupRequest(BaseModel):
    """User signup validation schema"""
    email: EmailStr  # Validates email format
    password: str = Field(
        ..., 
        min_length=8, 
        max_length=128,
        description="Password must be 8+ characters with uppercase, lowercase, and number"
    )
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength"""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        return v


class LoginRequest(BaseModel):
    """User login validation schema"""
    email: EmailStr
    password: str = Field(..., min_length=1, description="Password")


class VerifyOTPRequest(BaseModel):
    """OTP verification validation schema"""
    email: EmailStr
    otp_code: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")
    
    @field_validator('otp_code')
    @classmethod
    def validate_otp(cls, v: str) -> str:
        """Validate OTP is numeric"""
        if not v.isdigit():
            raise ValueError('OTP must contain only digits')
        return v


class PasswordResetRequest(BaseModel):
    """Password reset request validation"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation validation"""
    email: EmailStr
    otp_code: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(
        ..., 
        min_length=8, 
        max_length=128
    )
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate new password strength"""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        return v


# ============================================================================
# EMPLOYEE SCHEMAS
# ============================================================================

class OnboardRequest(BaseModel):
    """Employee onboarding validation schema"""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=200)
    phone_number: str = Field(..., min_length=10, max_length=20)
    email: EmailStr
    designation: str = Field(..., min_length=1, max_length=100)
    emp_id: str = Field(..., min_length=5, max_length=50, description="Must start with RBIS")
    
    @field_validator('emp_id')
    @classmethod
    def validate_emp_id(cls, v: str) -> str:
        """Validate employee ID format"""
        if not v.startswith('RBIS'):
            raise ValueError('Employee ID must start with RBIS prefix (e.g., RBIS001)')
        if not v[4:].isdigit() or len(v) < 8:
            raise ValueError('Invalid employee ID format')
        return v.upper()
    
    @field_validator('phone_number')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate phone number"""
        if not re.match(r'^\d{10,}$', v.replace('-', '').replace(' ', '')):
            raise ValueError('Phone number must contain at least 10 digits')
        return v


class EmployeeResponse(BaseModel):
    """Employee response schema"""
    emp_id: str
    email: str
    full_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    designation: Optional[str] = None
    role: str
    status: str
    
    model_config = ConfigDict(from_attributes=True)


class EmployeeUpdate(BaseModel):
    """Employee update validation schema"""
    full_name: Optional[str] = Field(None, max_length=200)
    phone_number: Optional[str] = Field(None, max_length=20)
    designation: Optional[str] = Field(None, max_length=100)


# ============================================================================
# LEAVE SCHEMAS
# ============================================================================

class LeaveTypeCreate(BaseModel):
    """Leave type creation validation"""
    name: str = Field(..., min_length=1, max_length=50)
    annual_quota: int = Field(..., ge=0, le=365, description="Must be between 0-365")
    is_paid: bool = True
    allow_carry_forward: bool = False


class LeaveRequestCreate(BaseModel):
    """Leave request creation validation"""
    leave_type_id: int = Field(..., gt=0)
    start_date: datetime.date
    end_date: datetime.date
    reason: str = Field(..., min_length=1, max_length=500)
    attachment_path: Optional[str] = None
    
    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v: str, info) -> str:
        """Validate end date is after start date"""
        if 'start_date' in info.data:
            if v < info.data['start_date']:
                raise ValueError('End date must be after start date')
        return v


class LeaveRequestResponse(BaseModel):
    """Leave request response schema"""
    id: int
    emp_id: str
    leave_type_id: int
    start_date: datetime.date
    end_date: datetime.date
    total_days: int
    reason: str
    status: str
    hr_remarks: Optional[str] = None
    ceo_remarks: Optional[str] = None
    created_at: datetime.datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# ATTENDANCE SCHEMAS
# ============================================================================

class AttendanceResponse(BaseModel):
    """Attendance record response schema"""
    id: int
    emp_id: str
    date: datetime.date
    first_in: Optional[str] = None
    last_out: Optional[str] = None
    total_duration: Optional[str] = None
    attendance_status: str
    is_manually_corrected: bool
    
    model_config = ConfigDict(from_attributes=True)


class AttendanceCorrectionRequest(BaseModel):
    """Attendance correction validation"""
    attendance_id: int = Field(..., gt=0)
    first_in: Optional[str] = None
    last_out: Optional[str] = None
    attendance_status: str = Field(..., description="PRESENT, ABSENT, ON_LEAVE")
    remarks: str = Field(..., min_length=1, max_length=500)
    
    @field_validator('attendance_status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate attendance status"""
        valid_statuses = ['PRESENT', 'ABSENT', 'ON_LEAVE', 'HALF_DAY']
        if v.upper() not in valid_statuses:
            raise ValueError(f'Status must be one of {valid_statuses}')
        return v.upper()


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class UserResponse(BaseModel):
    """User response schema"""
    emp_id: str
    email: str
    role: str
    full_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Authentication token response"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    expires_in: int = Field(default=604800, description="Token expiry in seconds (7 days)")


class MessageResponse(BaseModel):
    """Generic success message response"""
    message: str
    status: str = "success"


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str
    detail: Optional[str] = None
    status_code: int

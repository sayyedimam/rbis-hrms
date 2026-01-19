"""
Models Package
Exports all database models
"""
# Import Base and utilities
from app.models.base import Base, get_ist_now, IST

# Import Employee models
from app.models.employee import Employee, UserRole, UserStatus

# Import Attendance models
from app.models.attendance import Attendance

# Import File Upload models
from app.models.file_upload import FileUploadLog

# Import Leave models
from app.models.leave import (
    LeaveType,
    LeaveBalance,
    LeaveRequest,
    LeaveApprovalLog
)

# Export all models and utilities
__all__ = [
    # Base
    "Base",
    "get_ist_now",
    "IST",
    
    # Employee
    "Employee",
    "UserRole",
    "UserStatus",
    
    # Attendance
    "Attendance",
    
    # File Upload
    "FileUploadLog",
    
    # Leave
    "LeaveType",
    "LeaveBalance",
    "LeaveRequest",
    "LeaveApprovalLog",
]

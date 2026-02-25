"""
File Utilities
Helper functions for file operations
"""
import hashlib
from typing import Tuple
from fastapi import UploadFile

def calculate_file_hash(content: bytes) -> str:
    """
    Calculate SHA-256 hash of file content
    
    Args:
        content: File content as bytes
        
    Returns:
        64-character hexadecimal hash string
    """
    return hashlib.sha256(content).hexdigest()

def validate_file_type(file: UploadFile, allowed_extensions: Tuple[str, ...] = ('.xlsx', '.xls', '.csv')) -> bool:
    """
    Validate if file has allowed extension
    
    Args:
        file: Uploaded file
        allowed_extensions: Tuple of allowed extensions
        
    Returns:
        True if file type is valid, False otherwise
    """
    if not file.filename:
        return False
    return file.filename.lower().endswith(allowed_extensions)

def generate_safe_filename(original_filename: str) -> str:
    """
    Generate safe filename with timestamp prefix
    
    Args:
        original_filename: Original file name
        
    Returns:
        Safe filename with timestamp
    """
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{timestamp}_{original_filename}"

def normalize_emp_id(raw_id: str) -> str:
    """
    Normalize employee ID to RBIS0000 format
    
    Args:
        raw_id: Raw employee ID from file (e.g. '0058', 'RBIS0058', '58', '00100')
        
    Returns:
        Normalized employee ID in RBISxxxx format, or empty string if invalid
        
    Examples:
        'RBIS1'    -> 'RBIS0001'
        '0058'     -> 'RBIS0058'
        '123'      -> 'RBIS0123'
        'rbis0045' -> 'RBIS0045'
        '00100'    -> ''  (invalid: maps to 100, which is > 4 digits when the DB has 4-digit IDs only)
    """
    raw_id = str(raw_id).strip()
    
    if not raw_id or raw_id.lower() == 'nan':
        return ''
    
    # Already in RBIS format
    if raw_id.upper().startswith('RBIS'):
        num_part = ''.join(filter(str.isdigit, raw_id))
        if not num_part:
            return ''
        num = int(num_part)
        return f"RBIS{num:04d}"
    
    # Pure number — auto-prefix with RBIS
    elif raw_id.isdigit():
        num = int(raw_id)
        if num < 1 or num > 9999:
            return ''  # Out of valid range for 4-digit format
        return f"RBIS{num:04d}"
    
    # Other format — can't normalize
    else:
        return ''


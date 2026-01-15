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
        raw_id: Raw employee ID from file
        
    Returns:
        Normalized employee ID
        
    Examples:
        'RBIS1' -> 'RBIS0001'
        '123' -> 'RBIS0123'
        'rbis0045' -> 'RBIS0045'
    """
    raw_id = str(raw_id).strip()
    
    if not raw_id or raw_id.lower() == 'nan':
        return ''
    
    # Already in RBIS format
    if raw_id.upper().startswith('RBIS'):
        num_part = ''.join(filter(str.isdigit, raw_id))
        return f"RBIS{num_part.zfill(4)}"
    
    # Pure number
    elif raw_id.isdigit():
        return f"RBIS{raw_id.zfill(4)}"
    
    # Other format
    else:
        return raw_id.upper()

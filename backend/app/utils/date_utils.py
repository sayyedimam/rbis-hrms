"""
Date Utilities
Helper functions for date/time operations
"""
from datetime import date, datetime
import pandas as pd
from typing import Optional

def parse_date(date_val: any) -> Optional[date]:
    """
    Parse date from various formats
    
    Args:
        date_val: Date value (string, datetime, or date object)
        
    Returns:
        date object or None if parsing fails
    """
    if not date_val:
        return None
    
    try:
        if isinstance(date_val, date):
            return date_val
        elif isinstance(date_val, datetime):
            return date_val.date()
        else:
            return pd.to_datetime(date_val).date()
    except Exception:
        return None

def format_time(time_val: any) -> Optional[str]:
    """
    Format time value to string
    
    Args:
        time_val: Time value
        
    Returns:
        Formatted time string or None
    """
    if not time_val or str(time_val).strip().lower() in ['', 'nan', 'none']:
        return None
    return str(time_val).strip()

"""
Base Model Configuration
Contains base utilities and timezone helpers
"""
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone, timedelta

# Create Base class for all models
Base = declarative_base()

# IST Timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def get_ist_now():
    """Returns current datetime in IST timezone"""
    return datetime.now(IST)

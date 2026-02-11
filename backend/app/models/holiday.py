from sqlalchemy import Column, Integer, String, Date
from app.models.base import Base

class Holiday(Base):
    """Holiday model - list of public holidays"""
    __tablename__ = "holidays"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    date = Column(Date, nullable=False, unique=True)
    year = Column(Integer, nullable=False)
    day = Column(String(20), nullable=True) # e.g. "Monday"

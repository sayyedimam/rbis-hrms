from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "mssql+pyodbc://localhost/RBIS_HRMS?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes&TrustServerCertificate=yes")

engine = create_engine(
    DATABASE_URL,
    pool_size=20,          # Maintain 20 open connections
    max_overflow=10,       # Allow 10 extra connections during spikes
    pool_pre_ping=True,    # Check connection health before use
    pool_recycle=3600      # Recycle connections every hour
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

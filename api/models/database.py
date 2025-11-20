"""
Database models and connection
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://airflow:airflow@postgres:5432/devscout"
)

# Create engine
engine = create_engine(DATABASE_URL)

# Session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class
Base = declarative_base()


# Database dependency
def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

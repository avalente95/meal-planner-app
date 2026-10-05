"""Database connection and operations"""
from sqlalchemy import UUID, create_engine
from sqlalchemy.orm import sessionmaker
from app.config import get_settings
from pydantic import BaseModel


engine = create_engine(get_settings().database_url.get_secret_value(), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    """Get a database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
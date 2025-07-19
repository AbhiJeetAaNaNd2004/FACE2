"""
FastAPI dependencies for database sessions and other shared resources
"""

from typing import Generator
from sqlalchemy.orm import Session
from fastapi import Depends

from app.config import settings
from db.db_config import get_db

# Re-export the database dependency for backward compatibility
def get_database() -> Generator[Session, None, None]:
    """Get database session dependency"""
    return get_db()

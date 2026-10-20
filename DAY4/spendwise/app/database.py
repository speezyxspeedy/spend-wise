"""
Database configuration and session management for SpendWise.
Uses SQLite with SQLAlchemy ORM.
"""

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Base directory for the database
BASE_DIR = Path(__file__).resolve().parent.parent

# Database URL from environment or default local SQLite database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'spendwise.db'}")

# SQLite connection args for threading safety
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency for yielding database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    # Import models so they are registered with Base metadata
    from app import models  # noqa: F401
    Base.metadata.create_all(bind=engine)

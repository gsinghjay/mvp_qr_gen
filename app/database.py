"""
Database configuration and session management for the QR code generator application.
"""

import logging
import os
import time
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)

# Get PostgreSQL database URL from environment variables
PG_DATABASE_URL = os.getenv("PG_DATABASE_URL")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Check for required database URL
if not PG_DATABASE_URL:
    raise ValueError("PG_DATABASE_URL environment variable must be set")

# Check if the application is in testing mode
def is_testing_mode() -> bool:
    """
    Determine if the application is running in testing mode.
    
    Returns:
        bool: True if in testing mode, False otherwise
    """
    return os.getenv("TESTING_MODE", "").lower() == "true" or ENVIRONMENT.lower() == "test"

# Determine the current database URL to use based on environment
def get_database_url() -> str:
    """
    Get the appropriate database URL based on the current environment.
    
    Returns:
        str: The database URL to use
    """
    if is_testing_mode() and settings.TEST_DATABASE_URL:
        logger.info("Using test database URL for testing mode")
        return settings.TEST_DATABASE_URL
    
    logger.info(f"Using PostgreSQL database URL: {PG_DATABASE_URL}")
    return PG_DATABASE_URL

# Get the current database URL
CURRENT_DB_URL = get_database_url()

# Create engine with PostgreSQL settings
engine = create_engine(
    CURRENT_DB_URL,
    pool_pre_ping=True,  # Verify connections before using them
    pool_recycle=300,  # Recycle connections every 5 minutes
    pool_size=10,  # Maintain up to 10 connections in the pool
    max_overflow=20,  # Allow up to 20 extra connections when needed
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",  # Log SQL queries if enabled
)

# Create sessionmaker with timezone-aware settings
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)


# Define Base class using new SQLAlchemy 2.0 style
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


# Retry decorator for database operations
def with_retry(max_retries=3, retry_delay=0.1):
    """Decorator to retry database operations on transient errors."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except OperationalError as e:
                    # Only retry on PostgreSQL connection errors
                    retryable_error = "could not connect to server" in str(e)
                    
                    if retryable_error and retries < max_retries - 1:
                        retries += 1
                        logger.warning(f"Database error, retrying ({retries}/{max_retries}): {e}")
                        time.sleep(retry_delay * (2**retries))  # Exponential backoff
                    else:
                        raise
                except Exception:
                    # Don't retry on other errors
                    raise
            return func(*args, **kwargs)  # Last attempt

        return wrapper

    return decorator


# Replace the context manager with a generator function that can be used as a dependency
def get_db():
    """Get database session with proper cleanup for FastAPI dependency injection."""
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Database error in request: {e}")
        db.rollback()
        raise
    finally:
        db.close()


# Keep the context manager version for use in scripts
@contextmanager
def get_db_context():
    """Get database session with proper cleanup as a context manager."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_with_logging():
    """Get database session with proper error handling and logging."""
    db = None
    try:
        db = SessionLocal()
        yield db
    except Exception as e:
        logger.exception("Database session error", extra={"error": str(e)})
        if db:
            db.rollback()
        raise
    finally:
        if db:
            db.close()


def init_db():
    """
    Initialize database tables.
    Creates tables if they don't exist.
    """
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

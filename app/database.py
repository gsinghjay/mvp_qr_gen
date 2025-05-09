"""
Database configuration and session management for the QR code generator application.
"""

import logging
import os
import time
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

logger = logging.getLogger(__name__)

# Get database URLs and environment from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")
PG_DATABASE_URL = os.getenv("PG_DATABASE_URL")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Determine which database to use
# In Phase 2, we still use SQLite but prepare for PostgreSQL
USE_POSTGRES = PG_DATABASE_URL is not None and os.getenv("USE_POSTGRES", "false").lower() == "true"
CURRENT_DB_URL = PG_DATABASE_URL if USE_POSTGRES else DATABASE_URL

if not CURRENT_DB_URL:
    # If neither DATABASE_URL nor PG_DATABASE_URL is set, use in-memory for tests, file for development
    CURRENT_DB_URL = "sqlite:///:memory:" if ENVIRONMENT == "test" else "sqlite:///./data/qr_codes.db"

# Ensure data directory exists for SQLite file
if not USE_POSTGRES and CURRENT_DB_URL.startswith("sqlite:///./") and ENVIRONMENT != "test":
    data_path = Path(CURRENT_DB_URL.replace("sqlite:///./", "")).parent
    data_path.mkdir(parents=True, exist_ok=True)

logger.info(f"Using database URL: {CURRENT_DB_URL}")
logger.info(f"Database type: {'PostgreSQL' if USE_POSTGRES else 'SQLite'}")


def configure_sqlite_connection(dbapi_connection, connection_record):
    """Configure SQLite connection with appropriate PRAGMAs."""
    try:
        cursor = dbapi_connection.cursor()

        # Essential settings
        cursor.execute("PRAGMA foreign_keys=ON")

        # Performance optimizations
        cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging for better concurrency
        cursor.execute("PRAGMA synchronous=NORMAL")  # Balance between safety and performance

        # Additional optimizations
        cursor.execute("PRAGMA temp_store=MEMORY")  # Store temporary tables in memory
        cursor.execute("PRAGMA mmap_size=30000000")  # Use memory-mapped I/O (30MB)
        cursor.execute("PRAGMA cache_size=-6000")  # Use 6MB page cache (negative = kilobytes)

        # Production-specific settings
        if ENVIRONMENT == "production":
            cursor.execute("PRAGMA busy_timeout=30000")  # Wait up to 30 seconds for locks
            cursor.execute("PRAGMA wal_autocheckpoint=1000")  # Checkpoint WAL after 1000 pages
        else:
            cursor.execute("PRAGMA busy_timeout=5000")  # Wait up to 5 seconds for locks

        cursor.close()
    except Exception as e:
        logger.error(f"Error configuring SQLite connection: {e}")
        # Don't re-raise, let the connection attempt proceed


def add_sqlite_functions(dbapi_connection, connection_record):
    """Add custom functions to SQLite."""
    try:

        def utcnow():
            """Return current UTC datetime with timezone info."""
            return datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S.%f%z")

        def parse_datetime(dt_str):
            """Parse datetime string to UTC timezone-aware datetime."""
            if dt_str is None:
                return None
            try:
                # Handle 'Z' suffix by replacing with '+00:00'
                if isinstance(dt_str, str):
                    if dt_str.endswith("Z"):
                        dt_str = dt_str[:-1] + "+00:00"
                    dt = datetime.fromisoformat(dt_str)
                # If it's already a datetime, ensure it's timezone-aware
                elif isinstance(dt_str, datetime):
                    dt = dt_str if dt_str.tzinfo else dt_str.replace(tzinfo=UTC)
                else:
                    return None

                # Ensure timezone awareness and convert to UTC
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=UTC)
                return dt.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S.%f%z")
            except (ValueError, TypeError):
                return None

        def datetime_to_utc(dt_str):
            """Convert datetime to UTC timezone-aware datetime."""
            if dt_str is None:
                return None
            try:
                if isinstance(dt_str, str):
                    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                elif isinstance(dt_str, datetime):
                    dt = dt_str
                else:
                    return None

                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=UTC)
                return dt.astimezone(UTC)
            except (ValueError, TypeError):
                return None

        dbapi_connection.create_function("utcnow", 0, utcnow)
        dbapi_connection.create_function("datetime", 1, parse_datetime)
        dbapi_connection.create_function("datetime_to_utc", 1, datetime_to_utc)
    except Exception as e:
        logger.error(f"Error adding SQLite functions: {e}")
        # Don't re-raise, let the connection attempt proceed


# Create engine with proper settings based on database type
if USE_POSTGRES:
    # PostgreSQL settings
    engine = create_engine(
        CURRENT_DB_URL,
        pool_pre_ping=True,  # Verify connections before using them
        pool_recycle=300,  # Recycle connections every 5 minutes
        pool_size=10,  # Maintain up to 10 connections in the pool
        max_overflow=20,  # Allow up to 20 extra connections when needed
        echo=os.getenv("SQL_ECHO", "false").lower() == "true",  # Log SQL queries if enabled
    )
else:
    # SQLite settings (maintaining backward compatibility)
    engine = create_engine(
        CURRENT_DB_URL,
        connect_args={
            "check_same_thread": False,  # Allow cross-thread usage
            "isolation_level": None,  # Let SQLite handle transactions
            "timeout": 30,  # Wait up to 30 seconds for database locks
        },
        pool_pre_ping=True,  # Verify connections before using them
        pool_recycle=300,  # Recycle connections every 5 minutes
        pool_size=10,  # Maintain up to 10 connections in the pool
        max_overflow=20,  # Allow up to 20 extra connections when needed
        echo=os.getenv("SQL_ECHO", "false").lower() == "true",  # Log SQL queries if enabled
    )
    
    # Configure SQLite connection (only if using SQLite)
    event.listen(engine, "connect", configure_sqlite_connection)
    event.listen(engine, "connect", add_sqlite_functions)

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
                    # Only retry on database lock errors (SQLite) or connection errors (PostgreSQL)
                    retryable_error = (
                        ("database is locked" in str(e) and not USE_POSTGRES) or  # SQLite lock
                        ("could not connect to server" in str(e) and USE_POSTGRES)  # PostgreSQL connection
                    )
                    
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
        # Ensure the data directory exists
        db_path = CURRENT_DB_URL.replace("sqlite:///", "")
        if db_path.startswith("."):
            db_path = db_path[1:]  # Remove leading dot
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

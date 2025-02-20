"""
Database configuration and session management for the QR code generator application.
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
import os
import logging
from datetime import datetime, timezone
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Get database URL from environment variables
SQLITE_URL = os.getenv("DATABASE_URL")
if not SQLITE_URL:
    # If DATABASE_URL is not set, use in-memory for tests, file for development
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    SQLITE_URL = "sqlite:///:memory:" if ENVIRONMENT == "test" else "sqlite:///./data/qr_codes.db"

logger.info(f"Using database URL: {SQLITE_URL}")

def configure_sqlite_connection(dbapi_connection, connection_record):
    """Configure SQLite connection with appropriate PRAGMAs."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()

def add_sqlite_functions(dbapi_connection, connection_record):
    """Add custom functions to SQLite."""
    def utcnow():
        """Return current UTC datetime with timezone info."""
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f%z")
    
    def parse_datetime(dt_str):
        """Parse datetime string to UTC timezone-aware datetime."""
        if dt_str is None:
            return None
        try:
            # Handle 'Z' suffix by replacing with '+00:00'
            if isinstance(dt_str, str):
                if dt_str.endswith('Z'):
                    dt_str = dt_str[:-1] + '+00:00'
                dt = datetime.fromisoformat(dt_str)
            # If it's already a datetime, ensure it's timezone-aware
            elif isinstance(dt_str, datetime):
                dt = dt_str if dt_str.tzinfo else dt_str.replace(tzinfo=timezone.utc)
            else:
                return None
            
            # Ensure timezone awareness and convert to UTC
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f%z")
        except (ValueError, TypeError):
            return None
    
    def datetime_to_utc(dt_str):
        """Convert datetime to UTC timezone-aware datetime."""
        if dt_str is None:
            return None
        try:
            if isinstance(dt_str, str):
                dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            elif isinstance(dt_str, datetime):
                dt = dt_str
            else:
                return None
            
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except (ValueError, TypeError):
            return None
    
    dbapi_connection.create_function('utcnow', 0, utcnow)
    dbapi_connection.create_function('datetime', 1, parse_datetime)
    dbapi_connection.create_function('datetime_to_utc', 1, datetime_to_utc)

# Create engine with proper settings for SQLite
engine = create_engine(
    SQLITE_URL,
    connect_args={
        "check_same_thread": False,
        "isolation_level": None  # Let SQLite handle transactions
    },
    pool_pre_ping=True,
    pool_recycle=300
)

# Configure SQLite connection
event.listen(engine, "connect", configure_sqlite_connection)
event.listen(engine, "connect", add_sqlite_functions)

# Create sessionmaker with timezone-aware settings
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    class_=Session
)

# Define Base class using new SQLAlchemy 2.0 style
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass

@contextmanager
def get_db():
    """Get database session with proper cleanup."""
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
        db_path = SQLITE_URL.replace("sqlite:///", "")
        if db_path.startswith("."):
            db_path = db_path[1:]  # Remove leading dot
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise 
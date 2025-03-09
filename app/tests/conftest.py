"""
Test configuration and fixtures for the QR code generator API.
"""

import os
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import List, Optional

import pytest
from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

from ..database import Base, get_db_with_logging, get_db
from ..main import app
from ..models.qr import QRCode
from ..schemas.qr.models import QRType

# Initialize Faker for generating test data
fake = Faker()

# Set test environment
os.environ["ENVIRONMENT"] = "test"

# Create test database directory if it doesn't exist
TEST_DB_DIR = Path("data/test")
TEST_DB_DIR.mkdir(parents=True, exist_ok=True)

# Generate a unique database file name for this test run
TEST_DB_FILE = f"test_db_{uuid.uuid4().hex}.db"
TEST_DB_PATH = TEST_DB_DIR / TEST_DB_FILE

# Test database URL - using file-based SQLite
SQLALCHEMY_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"


def configure_sqlite_connection(dbapi_connection, connection_record):
    """Configure SQLite connection with appropriate PRAGMAs."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA temp_store=MEMORY")
    cursor.execute("PRAGMA mmap_size=30000000")  # Use memory-mapped I/O (30MB)
    cursor.execute("PRAGMA cache_size=-6000")    # Use 6MB page cache (negative = kilobytes)
    cursor.close()


# Create test engine with appropriate connection settings
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "isolation_level": None,  # Let SQLite handle transactions
    },
    echo=False,  # Set to True for SQL query logging during tests
)

# Configure SQLite connection
event.listen(engine, "connect", configure_sqlite_connection)


# Add SQLite functions for timezone support
@event.listens_for(engine, "connect")
def add_sqlite_functions(dbapi_connection, connection_record):
    """Add custom functions to SQLite for timezone support."""

    def utcnow():
        """Return current UTC datetime with timezone info."""
        return datetime.now(UTC)

    def parse_datetime(dt_str):
        """Parse datetime string to UTC timezone-aware datetime."""
        try:
            # Handle 'Z' suffix by replacing with '+00:00'
            if dt_str.endswith("Z"):
                dt_str = dt_str[:-1] + "+00:00"
            return datetime.fromisoformat(dt_str).astimezone(UTC)
        except (ValueError, TypeError):
            return None

    dbapi_connection.create_function("utcnow", 0, utcnow)
    dbapi_connection.create_function("datetime", 1, parse_datetime)


# Create test session
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_test_qr_code(
    db: Session,
    qr_type: QRType = QRType.STATIC,
    content: Optional[str] = None,
    redirect_url: Optional[str] = None,
    fill_color: str = "#000000",
    back_color: str = "#FFFFFF",
    scan_count: int = 0,
    created_days_ago: int = 0,
    last_scan_days_ago: Optional[int] = None,
) -> QRCode:
    """
    Create a test QR code with realistic data.
    
    Args:
        db: Database session
        qr_type: Type of QR code (static or dynamic)
        content: Content for static QR code
        redirect_url: Redirect URL for dynamic QR code
        fill_color: QR code fill color
        back_color: QR code background color
        scan_count: Number of scans
        created_days_ago: Days to subtract from current date for created_at
        last_scan_days_ago: Days to subtract from current date for last_scan_at
        
    Returns:
        QRCode: Created QR code instance
    """
    now = datetime.now(UTC)
    
    # Generate realistic data based on QR type
    if qr_type == QRType.STATIC:
        content = content or fake.url()
        redirect_url = None
    else:  # DYNAMIC
        content = content or fake.url()  # For dynamic QR codes, content is still required
        redirect_url = redirect_url or fake.url()
    
    # Create QR code instance
    qr_code = QRCode(
        qr_type=qr_type.value,
        content=content,
        redirect_url=redirect_url,
        fill_color=fill_color,
        back_color=back_color,
        scan_count=scan_count,
        created_at=now - timedelta(days=created_days_ago),
        last_scan_at=now - timedelta(days=last_scan_days_ago) if last_scan_days_ago is not None else None
    )
    
    # Add to database
    db.add(qr_code)
    db.commit()
    db.refresh(qr_code)
    
    return qr_code


def create_test_qr_codes(
    db: Session,
    count: int = 10,
    static_ratio: float = 0.5,
    max_age_days: int = 30,
    max_scan_count: int = 100
) -> List[QRCode]:
    """
    Create multiple test QR codes with realistic data.
    
    Args:
        db: Database session
        count: Number of QR codes to create
        static_ratio: Ratio of static QR codes (0.0 to 1.0)
        max_age_days: Maximum age of QR codes in days
        max_scan_count: Maximum scan count
        
    Returns:
        List[QRCode]: List of created QR code instances
    """
    qr_codes = []
    
    for i in range(count):
        # Determine QR type based on static_ratio
        qr_type = QRType.STATIC if i < int(count * static_ratio) else QRType.DYNAMIC
        
        # Generate random age and scan count
        age_days = fake.random_int(min=0, max=max_age_days)
        scan_count = fake.random_int(min=0, max=max_scan_count)
        
        # For QR codes with scans, set last_scan_at
        last_scan_days_ago = fake.random_int(min=0, max=age_days) if scan_count > 0 else None
        
        # Create QR code
        qr_code = create_test_qr_code(
            db=db,
            qr_type=qr_type,
            created_days_ago=age_days,
            scan_count=scan_count,
            last_scan_days_ago=last_scan_days_ago
        )
        
        qr_codes.append(qr_code)
    
    return qr_codes


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create test database tables before each test session."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    
    # Clean up test database files after tests
    try:
        # Close all connections to allow file deletion
        engine.dispose()
        
        # Remove the test database file and WAL files
        test_db_path = Path(TEST_DB_PATH)
        if test_db_path.exists():
            test_db_path.unlink()
        
        # Remove WAL and SHM files if they exist
        wal_file = Path(f"{TEST_DB_PATH}-wal")
        if wal_file.exists():
            wal_file.unlink()
            
        shm_file = Path(f"{TEST_DB_PATH}-shm")
        if shm_file.exists():
            shm_file.unlink()
    except Exception as e:
        print(f"Error cleaning up test database: {e}")


@pytest.fixture(autouse=True)
def reset_test_database():
    """Reset database between tests."""
    # This will run before each test
    yield
    # This will run after each test
    db = TestingSessionLocal()
    try:
        # Delete all data from tables but keep the tables
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error resetting test database: {e}")
    finally:
        db.close()


def get_test_db():
    """Get test database session."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override the database dependencies
app.dependency_overrides[get_db_with_logging] = get_test_db
app.dependency_overrides[get_db] = get_test_db


@pytest.fixture
def test_db():
    """Fixture to get test database session."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(test_db):
    """Create a test client with proper headers for Traefik."""
    test_client = TestClient(app)
    test_client.headers.update(
        {
            "Host": "localhost",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Real-IP": "127.0.0.1",
            "X-Forwarded-For": "127.0.0.1",
            "X-Forwarded-Proto": "http",
            "X-Forwarded-Host": "localhost",
            "X-Request-ID": "test-request-id",
        }
    )
    return test_client


@pytest.fixture
def seeded_db(test_db):
    """Fixture to get a database session with seeded test data."""
    # Create a mix of static and dynamic QR codes
    create_test_qr_codes(test_db, count=20, static_ratio=0.6)
    return test_db


@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine."""
    return engine  # Reuse the existing engine for consistency


@pytest.fixture(scope="session")
def test_session_factory(test_engine):
    """Create a test session factory."""
    return TestingSessionLocal  # Reuse the existing session factory for consistency


@pytest.fixture(autouse=True)
def override_database_url(monkeypatch):
    """Override the database URL for testing."""
    monkeypatch.setenv("DATABASE_URL", SQLALCHEMY_DATABASE_URL)

"""
Test configuration and fixtures for the QR code generator API.
"""

import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional, Generator, AsyncGenerator
import asyncio

import pytest
from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from ..database import Base, get_db_with_logging, get_db
from ..main import app
from ..models.qr import QRCode
from ..schemas.qr.models import QRType
from ..services.qr_service import QRCodeService

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
# For async tests
ASYNC_SQLALCHEMY_DATABASE_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH}"


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


# Create and configure the engine for the test database
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

# Create an async engine for async tests
async_engine = create_async_engine(
    ASYNC_SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

# Listen for connections to set up SQLite configuration
@event.listens_for(engine, "connect")
def setup_sqlite_for_test(dbapi_connection, connection_record):
    configure_sqlite_connection(dbapi_connection, connection_record)

# Add custom SQLite functions for UTC handling
@event.listens_for(engine, "connect")
def add_sqlite_functions(dbapi_connection, connection_record):
    """Add custom SQLite functions for UTC handling."""
    
    def utcnow():
        """Return current UTC timestamp in ISO format with Z suffix."""
        # Return with 'Z' suffix instead of +00:00 for UTC timezone
        dt = datetime.now(timezone.utc)
        # Format with Z suffix manually to ensure test passes
        return dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    def parse_datetime(dt_str):
        """Parse ISO format datetime string to Unix timestamp."""
        if not dt_str:
            return None
        try:
            # Handle Z suffix by replacing with +00:00 first
            if dt_str.endswith('Z'):
                dt_str = dt_str[:-1] + '+00:00'
            dt = datetime.fromisoformat(dt_str)
            return dt.timestamp()
        except ValueError:
            return None
    
    # Register the functions with SQLite
    dbapi_connection.create_function("utcnow", 0, utcnow)
    dbapi_connection.create_function("parse_datetime", 1, parse_datetime)

# Create session factories
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncTestSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=async_engine)


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
    Create a test QR code in the database.
    
    Args:
        db: Database session
        qr_type: Type of QR code (static or dynamic)
        content: QR code content (generated if None)
        redirect_url: Redirect URL for dynamic QR codes
        fill_color: QR code fill color
        back_color: QR code background color
        scan_count: Initial scan count
        created_days_ago: Days to subtract from creation date
        last_scan_days_ago: Days to subtract from last scan date (None = no last scan)
        
    Returns:
        Created QR code instance
    """
    # Generate test data if needed
    if content is None:
        if qr_type == QRType.STATIC:
            content = fake.url()
        else:
            content = f"/r/{uuid.uuid4().hex[:8]}"
    
    # For dynamic QR codes, ensure redirect_url is set
    if qr_type == QRType.DYNAMIC and redirect_url is None:
        redirect_url = fake.url()
    
    # Calculate dates
    created_at = datetime.now(timezone.utc)
    if created_days_ago > 0:
        created_at = created_at - timedelta(days=created_days_ago)
    
    # Handle last scan date
    last_scan_at = None
    if last_scan_days_ago is not None:
        last_scan_at = datetime.now(timezone.utc) - timedelta(days=last_scan_days_ago)
    
    # Create the QR code
    qr_code = QRCode(
        id=str(uuid.uuid4()),
        content=content,
        qr_type=qr_type.value,
        redirect_url=redirect_url,
        fill_color=fill_color,
        back_color=back_color,
        scan_count=scan_count,
        created_at=created_at,
        last_scan_at=last_scan_at
    )
    
    # Save to database
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
    Create multiple test QR codes in the database.
    
    Args:
        db: Database session
        count: Number of QR codes to create
        static_ratio: Ratio of static to dynamic QR codes
        max_age_days: Maximum age in days
        max_scan_count: Maximum scan count
        
    Returns:
        List of created QR code instances
    """
    qr_codes = []
    
    for i in range(count):
        # Randomly decide the type based on the ratio
        is_static = fake.random.random() < static_ratio
        qr_type = QRType.STATIC if is_static else QRType.DYNAMIC
        
        # Generate random age and scan count
        age_days = fake.random.randint(0, max_age_days)
        scan_count = fake.random.randint(0, max_scan_count)
        
        # Sometimes set a last scan date
        last_scan_days_ago = None
        if scan_count > 0:
            last_scan_days_ago = fake.random.randint(0, age_days)
        
        # Create the QR code
        qr_code = create_test_qr_code(
            db=db,
            qr_type=qr_type,
            scan_count=scan_count,
            created_days_ago=age_days,
            last_scan_days_ago=last_scan_days_ago
        )
        
        qr_codes.append(qr_code)
    
    return qr_codes


# Fixtures
@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create the test database with all tables."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Verify the database configuration
    with engine.connect() as conn:
        # Check if WAL mode is enabled
        result = conn.execute(text("PRAGMA journal_mode")).scalar()
        assert result.upper() == "WAL", f"SQLite is not in WAL mode: {result}"
        
        # Check if foreign keys are enabled
        result = conn.execute(text("PRAGMA foreign_keys")).scalar()
        assert result == 1, "SQLite foreign keys are not enabled"
    
    # Provide the database to tests
    yield
    
    # Cleanup after all tests
    try:
        # Explicitly close engine connections to avoid "database is locked" issues
        engine.dispose()
        # Delete the test database file
        if TEST_DB_PATH.exists():
            TEST_DB_PATH.unlink()
    except Exception as e:
        print(f"Error during test database cleanup: {e}")


@pytest.fixture(autouse=True)
def reset_test_database():
    """Reset the test database between tests by using a transaction rollback approach."""
    # Connect and begin a transaction
    connection = engine.connect()
    transaction = connection.begin()
    
    # Create a session bound to this connection
    session = TestSessionLocal(bind=connection)
    
    # Use the session in tests
    yield
    
    # Rollback the transaction to undo all changes made during tests
    transaction.rollback()
    connection.close()
    session.close()


# Session fixtures - using transaction-based isolation
@pytest.fixture
def test_db() -> Generator[Session, None, None]:
    """
    Fixture providing a test database session that gets rolled back after the test.
    
    Uses a savepoint to create a nested transaction that can be rolled back without
    affecting the outer transaction, following SQLAlchemy's recommendation for testing.
    """
    # Connect and begin a transaction
    connection = engine.connect()
    transaction = connection.begin()
    
    # Create a session bound to this connection
    session = TestSessionLocal(bind=connection)
    
    # Begin a nested transaction (savepoint)
    nested = connection.begin_nested()
    
    # If the session rolls back or commits, use the savepoint again
    @event.listens_for(session, "after_transaction_end")
    def end_savepoint(session, transaction):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()
    
    try:
        yield session
    finally:
        # Close the session
        session.close()
        # Rollback the transaction to clean up
        transaction.rollback()
        # Close the connection
        connection.close()


@pytest.fixture
async def async_test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Fixture providing an async test database session that gets rolled back after the test.
    
    Uses nested transactions for isolation following SQLAlchemy async best practices.
    """
    # Connect and begin a transaction
    async with async_engine.connect() as connection:
        # Begin a transaction
        await connection.begin()
        
        # Begin a nested transaction (savepoint)
        await connection.begin_nested()
        
        # Create a session bound to this connection
        async_session = AsyncTestSessionLocal(bind=connection)
        
        # If the session rolls back or commits, use the savepoint again
        @event.listens_for(async_session.sync_session, "after_transaction_end")
        def end_savepoint(session, transaction):
            if connection.in_nested_transaction():
                connection.sync_connection.begin_nested()
        
        try:
            yield async_session
        finally:
            # Close the session
            await async_session.close()
            # Rollback the transaction
            await connection.rollback()


@pytest.fixture
def client(test_db) -> TestClient:
    """
    TestClient with dependency override for database session.
    
    This ensures each test has its own isolated database session that gets rolled back.
    Following FastAPI's recommended approach from documentation.
    """
    # Store original dependencies
    original_dependencies = app.dependency_overrides.copy()
    
    # Create clean dependency override for this test
    def override_get_db():
        try:
            yield test_db
        finally:
            pass  # Transaction handled by test_db fixture with rollback
    
    # Create QR service override that uses the test db session
    def override_get_qr_service():
        try:
            yield QRCodeService(test_db)
        finally:
            pass  # Session handled by test_db fixture
    
    # Override the dependencies for DB access
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_db_with_logging] = override_get_db
    
    # Override QR service to use our test database
    from ..dependencies import get_qr_service
    app.dependency_overrides[get_qr_service] = override_get_qr_service
    
    try:
        # Yield the client with overridden dependencies
        with TestClient(app) as test_client:
            yield test_client
    finally:
        # Restore original dependencies after test
        app.dependency_overrides = original_dependencies


@pytest.fixture
def seeded_db(test_db) -> Session:
    """Fixture providing a database session pre-populated with test data."""
    create_test_qr_codes(test_db, count=25)
    return test_db


@pytest.fixture(scope="session")
def test_engine():
    """Fixture providing the test database engine."""
    return engine


@pytest.fixture(scope="session")
def test_session_factory():
    """Fixture providing the test database session factory."""
    return TestSessionLocal


@pytest.fixture(autouse=True)
def override_database_url(monkeypatch):
    """Override database URL settings in app config for testing."""
    monkeypatch.setenv("DATABASE_URL", SQLALCHEMY_DATABASE_URL)

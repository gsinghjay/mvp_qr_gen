"""
Test configuration and fixtures for the QR code generator API.
"""

import os
import uuid
from collections.abc import AsyncGenerator, Generator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio  # Import pytest_asyncio explicitly
from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from ..database import Base
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
# For async tests
ASYNC_SQLALCHEMY_DATABASE_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH}"

# Configure the default fixture loop scope for pytest-asyncio
pytest_asyncio.plugin.default_fixture_loop_scope = "function"


def configure_sqlite_connection(dbapi_connection, connection_record):
    """Configure SQLite connection with appropriate PRAGMAs."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA temp_store=MEMORY")
    cursor.execute("PRAGMA mmap_size=30000000")  # Use memory-mapped I/O (30MB)
    cursor.execute("PRAGMA cache_size=-6000")  # Use 6MB page cache (negative = kilobytes)
    cursor.close()


# Create and configure the engine for the test database
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}  # Needed for SQLite
)

# Create an async engine for async tests
async_engine = create_async_engine(
    ASYNC_SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}  # Needed for SQLite
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
        dt = datetime.now(UTC)
        # Format with Z suffix manually to ensure test passes
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    def parse_datetime(dt_str):
        """Parse ISO format datetime string to Unix timestamp."""
        if not dt_str:
            return None
        try:
            # Handle Z suffix by replacing with +00:00 first
            if dt_str.endswith("Z"):
                dt_str = dt_str[:-1] + "+00:00"
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
    content: str | None = None,
    redirect_url: str | None = None,
    fill_color: str = "#000000",
    back_color: str = "#FFFFFF",
    scan_count: int = 0,
    created_days_ago: int = 0,
    last_scan_days_ago: int | None = None,
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
    created_at = datetime.now(UTC)
    if created_days_ago > 0:
        created_at = created_at - timedelta(days=created_days_ago)

    # Handle last scan date
    last_scan_at = None
    if last_scan_days_ago is not None:
        last_scan_at = datetime.now(UTC) - timedelta(days=last_scan_days_ago)

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
        last_scan_at=last_scan_at,
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
    max_scan_count: int = 100,
) -> list[QRCode]:
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
            last_scan_days_ago=last_scan_days_ago,
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
    Get a database session for testing.

    This fixture provides an isolated database session that rolls back
    automatically after each test. It uses nested transactions (savepoints)
    to ensure test isolation.

    Returns:
        SQLAlchemy Session object
    """
    # Start a connection and a transaction
    connection = engine.connect()
    transaction = connection.begin()

    # Create a session bound to this connection
    session = TestSessionLocal(bind=connection)

    # Begin a nested transaction (savepoint)
    nested = connection.begin_nested()

    # If the outer transaction is committed, we need to create a new savepoint
    @event.listens_for(session, "after_transaction_end")
    def end_savepoint(session, transaction):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    try:
        yield session
    finally:
        # Roll back the transaction and close the connection
        session.close()
        transaction.rollback()
        connection.close()


@pytest_asyncio.fixture
async def async_test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get an async database session for testing.

    This fixture provides an isolated async database session that rolls back
    automatically after each test. It uses nested transactions (savepoints)
    to ensure test isolation.

    Returns:
        SQLAlchemy AsyncSession object
    """
    # Start an async connection
    async with async_engine.begin() as connection:
        # Begin a nested transaction (savepoint)
        await connection.begin_nested()

        # Create a session bound to this connection
        async_session = AsyncTestSessionLocal(bind=connection)

        # Set up the end_savepoint listener for the sync session
        @event.listens_for(async_session.sync_session, "after_transaction_end")
        def end_savepoint(session, transaction):
            if not connection.in_nested_transaction():
                connection.sync_connection.begin_nested()

        try:
            yield async_session
        finally:
            # Close the session
            await async_session.close()


@pytest.fixture
def client(test_db) -> TestClient:
    """
    Fixture providing a FastAPI test client with database overrides configured.

    This fixture automatically configures the application with test database
    dependencies using the DependencyOverrideManager.

    Args:
        test_db: The test database session (injected from the test_db fixture)

    Returns:
        TestClient: A configured FastAPI test client
    """
    from .helpers import DependencyOverrideManager

    # Create a dependency manager that overrides database dependencies
    with DependencyOverrideManager.create_db_override(app, test_db) as manager:
        # Create a test client with the dependencies overridden
        with TestClient(app) as client:
            yield client


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


# New fixtures for common test scenarios


@pytest.fixture
def static_qr(test_db) -> QRCode:
    """
    Fixture providing a basic static QR code for testing.

    Returns:
        A static QR code instance
    """
    return create_test_qr_code(
        db=test_db,
        qr_type=QRType.STATIC,
        content="https://example.com",
        fill_color="#000000",
        back_color="#FFFFFF",
    )


@pytest.fixture
def dynamic_qr(test_db) -> QRCode:
    """
    Fixture providing a basic dynamic QR code for testing.

    Returns:
        A dynamic QR code instance
    """
    return create_test_qr_code(
        db=test_db,
        qr_type=QRType.DYNAMIC,
        redirect_url="https://example.com/landing",
        fill_color="#000000",
        back_color="#FFFFFF",
    )


@pytest.fixture
def scanned_qr(test_db) -> QRCode:
    """
    Fixture providing a QR code with scan history for testing.

    Returns:
        A QR code instance with scan history
    """
    return create_test_qr_code(
        db=test_db,
        qr_type=QRType.DYNAMIC,
        redirect_url="https://example.com/scanned",
        scan_count=10,
        last_scan_days_ago=2,
    )


@pytest.fixture
def colored_qr(test_db) -> QRCode:
    """
    Fixture providing a QR code with custom colors for testing.

    Returns:
        A QR code instance with custom colors
    """
    return create_test_qr_code(
        db=test_db,
        qr_type=QRType.STATIC,
        content="https://example.com/colored",
        fill_color="#FF5733",
        back_color="#33FF57",
    )


@pytest.fixture
def historical_qr(test_db) -> QRCode:
    """
    Fixture providing an older QR code for testing date filtering.

    Returns:
        An older QR code instance
    """
    return create_test_qr_code(
        db=test_db, qr_type=QRType.STATIC, created_days_ago=30, scan_count=5, last_scan_days_ago=15
    )


# Fixtures for common API request payloads


@pytest.fixture
def static_qr_payload() -> dict[str, Any]:
    """
    Fixture providing a payload for creating a static QR code.

    Returns:
        Dict with static QR code creation parameters
    """
    return {
        "content": "https://example.com/test",
        "qr_type": "static",
        "fill_color": "#000000",
        "back_color": "#FFFFFF",
    }


@pytest.fixture
def dynamic_qr_payload() -> dict[str, Any]:
    """
    Fixture providing a payload for creating a dynamic QR code.

    Returns:
        Dict with dynamic QR code creation parameters
    """
    return {
        "redirect_url": "https://example.com/redirect",
        "qr_type": "dynamic",
        "fill_color": "#000000",
        "back_color": "#FFFFFF",
    }


@pytest.fixture
def invalid_color_payload() -> dict[str, Any]:
    """
    Fixture providing a payload with invalid color for testing validation.

    Returns:
        Dict with invalid color parameters
    """
    return {
        "content": "https://example.com/invalid-color",
        "qr_type": "static",
        "fill_color": "invalid-color",
        "back_color": "#FFFFFF",
    }


@pytest.fixture
def invalid_url_payload() -> dict[str, Any]:
    """
    Fixture providing a payload with invalid URL for testing validation.

    Returns:
        Dict with invalid URL parameters
    """
    return {
        "redirect_url": "not-a-valid-url",
        "qr_type": "dynamic",
        "fill_color": "#000000",
        "back_color": "#FFFFFF",
    }


# Fixtures for common client API requests


@pytest.fixture
def create_static_qr_request(client, static_qr_payload):
    """
    Fixture providing a function to create a static QR code via API.

    Returns:
        Function that returns response from creating a static QR code
    """

    def _create(payload_override=None):
        payload = static_qr_payload.copy()
        if payload_override:
            payload.update(payload_override)
        return client.post("/api/v1/qr-codes/", json=payload)

    return _create


@pytest.fixture
def create_dynamic_qr_request(client, dynamic_qr_payload):
    """
    Fixture providing a function to create a dynamic QR code via API.

    Returns:
        Function that returns response from creating a dynamic QR code
    """

    def _create(payload_override=None):
        payload = dynamic_qr_payload.copy()
        if payload_override:
            payload.update(payload_override)
        return client.post("/api/v1/qr-codes/", json=payload)

    return _create


@pytest.fixture
def get_qr_request(client):
    """
    Fixture providing a function to get a QR code by ID via API.

    Returns:
        Function that returns response from getting a QR code
    """

    def _get(qr_id):
        return client.get(f"/api/v1/qr-codes/{qr_id}")

    return _get


@pytest.fixture
def update_qr_request(client):
    """
    Fixture providing a function to update a QR code by ID via API.

    Returns:
        Function that returns response from updating a QR code
    """

    def _update(qr_id, payload):
        return client.patch(f"/api/v1/qr-codes/{qr_id}", json=payload)

    return _update


@pytest.fixture
def list_qr_request(client):
    """
    Fixture providing a function to list QR codes via API with pagination and filters.

    Returns:
        Function that returns response from listing QR codes
    """

    def _list(params=None):
        return client.get("/api/v1/qr-codes/", params=params)

    return _list


@pytest.fixture
def redirect_qr_request(client):
    """
    Fixture providing a function to test QR code redirects.

    Returns:
        Function that returns response from QR code redirect
    """

    def _redirect(path, follow_redirects=False):
        return client.get(f"/r/{path}", follow_redirects=follow_redirects)

    return _redirect

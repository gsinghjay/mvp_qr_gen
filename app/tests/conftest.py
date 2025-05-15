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
from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig
from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from ..core.config import settings
from ..database import Base, get_database_url, is_testing_mode
from ..main import app
from ..models.qr import QRCode
from ..schemas.qr.models import QRType
from .factories import QRCodeFactory

# Initialize Faker for generating test data
fake = Faker()

# Set test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["TESTING_MODE"] = "true"

# Ensure we're using the test database
if not is_testing_mode():
    raise RuntimeError("Not in testing mode, refusing to run tests")

# Get the test database URL
TEST_DB_URL = get_database_url()
if not TEST_DB_URL or "test" not in TEST_DB_URL:
    raise ValueError(f"Test database URL not configured correctly: {TEST_DB_URL}")

# Configure the default fixture loop scope for pytest-asyncio
pytest_asyncio.plugin.default_fixture_loop_scope = "function"

# Create engines for test database
engine = create_engine(
    TEST_DB_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    max_overflow=20,
)

# Create an async engine for async tests
async_engine = create_async_engine(
    TEST_DB_URL.replace("postgresql+psycopg2", "postgresql+asyncpg"),
    pool_pre_ping=True,
    pool_recycle=300,
    max_overflow=20,
)

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
    
    DEPRECATED: Use QRCodeFactory.create_with_params() instead.

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
    # Show deprecation warning
    import warnings
    warnings.warn(
        "create_test_qr_code is deprecated. Use QRCodeFactory.create_with_params() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
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
    
    DEPRECATED: Use QRCodeFactory.create_batch_mixed() instead.

    Args:
        db: Database session
        count: Number of QR codes to create
        static_ratio: Ratio of static to dynamic QR codes
        max_age_days: Maximum age in days
        max_scan_count: Maximum scan count

    Returns:
        List of created QR code instances
    """
    # Show deprecation warning
    import warnings
    warnings.warn(
        "create_test_qr_codes is deprecated. Use QRCodeFactory.create_batch_mixed() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
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
    """Create the test database schema using Alembic migrations."""
    # Get Alembic configuration
    alembic_cfg = AlembicConfig("alembic.ini")
    
    # Ensure alembic.ini uses the correct test database URL
    # This is handled by the dynamic URL selection in alembic/env.py
    
    # Log database setup
    print(f"Setting up test database with URL: {TEST_DB_URL}")
    
    # Run migrations to create schema
    alembic_command.upgrade(alembic_cfg, "head")
    
    # Yield to tests
    yield
    
    # We don't need to downgrade or drop tables since test transactions will be rolled back
    # and the database is dedicated for testing only


@pytest.fixture(autouse=True)
def reset_test_database(request):
    """Reset the test database between tests by truncating all tables."""
    # Skip for session-scoped fixtures
    if 'setup_test_database' in request.fixturenames:
        yield
        return
        
    # Get all table names
    with engine.connect() as conn:
        tables = conn.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
        )).fetchall()
        
        # Start a transaction
        with conn.begin():
            # Disable foreign key checks temporarily
            conn.execute(text("SET session_replication_role = 'replica';"))
            
            # Truncate all tables
            for table in tables:
                table_name = table[0]
                # Skip alembic_version table
                if table_name != 'alembic_version':
                    conn.execute(text(f'TRUNCATE TABLE "{table_name}" CASCADE;'))
            
            # Re-enable foreign key checks
            conn.execute(text("SET session_replication_role = 'origin';"))
    
    yield


@pytest.fixture
def test_db() -> Generator[Session, None, None]:
    """
    Create a database session for testing.
    
    This fixture uses nested transactions for test isolation.
    Each test gets its own transaction that is rolled back after the test.
    """
    # Connect to the database and begin a transaction
    connection = engine.connect()
    transaction = connection.begin()
    
    # Create a session bound to this connection
    session = TestSessionLocal(bind=connection)
    
    try:
        # Use the session in tests
        yield session
    finally:
        # Roll back the transaction after the test
        session.close()
        transaction.rollback()
        connection.close()


@pytest_asyncio.fixture
async def async_test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create an async database session for testing.
    
    This fixture uses nested transactions for test isolation.
    Each test gets its own transaction that is rolled back after the test.
    """
    # Connect to the database and begin a transaction
    # Use the proper async context manager for connection
    async with async_engine.connect() as connection:
        # Start a transaction
        transaction = await connection.begin()
        
        # Create a session bound to this connection
        session = AsyncTestSessionLocal(bind=connection)
        
        try:
            # Use the session in tests
            yield session
        finally:
            # Roll back the transaction after the test
            await session.close()
            await transaction.rollback()
            # No need to close connection - it's handled by the context manager


@pytest.fixture
def client(test_db) -> TestClient:
    """
    Create a FastAPI TestClient with dependency overrides for testing.
    
    This fixture overrides key dependencies to use test instances:
    - get_db_with_logging: Main database dependency used across the app
    - get_db: Backup direct database dependency (used in some places)
    
    Args:
        test_db: Database session fixture
        
    Returns:
        TestClient: FastAPI test client
    """
    # Store original dependencies to restore later
    original_dependencies = {}
    
    try:
        # Import dependencies here for clarity
        from ..database import get_db, get_db_with_logging
        from ..services.qr import get_qr_service
        from ..repositories.qr import get_qr_repository
        
        # Store original dependencies
        original_dependencies = app.dependency_overrides.copy()
        
        # Define override functions to use the test database session
        def override_get_db():
            """Override the standard database session with test session."""
            try:
                yield test_db
            finally:
                pass
        
        def override_get_db_with_logging():
            """Override the standard database session with test session."""
            try:
                yield test_db
            finally:
                pass
        
        # Configure dependency overrides
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_db_with_logging] = override_get_db_with_logging
        
        # Create and return the test client
        client = TestClient(app)
        return client
    
    except Exception as e:
        # Restore original dependencies if an error occurs during setup
        app.dependency_overrides = original_dependencies
        raise e


@pytest.fixture
def seeded_db(test_db: Session, qr_code_factory: QRCodeFactory) -> Session:
    """
    Create a database session with pre-populated test data.
    
    Args:
        test_db: Database session fixture
        qr_code_factory: QRCodeFactory instance
        
    Returns:
        Session: Database session with test data
    """
    qr_code_factory.create_batch_mixed(count=20)
    return test_db


@pytest.fixture(scope="session")
def test_engine():
    """Return the test database engine."""
    return engine


@pytest.fixture(scope="session")
def test_session_factory():
    """Return the test session factory."""
    return TestSessionLocal


@pytest.fixture
def qr_code_factory(test_db: Session) -> QRCodeFactory:
    """
    Fixture that provides a QRCodeFactory instance.
    
    Args:
        test_db: Database session
        
    Returns:
        Initialized QRCodeFactory with database session
    """
    return QRCodeFactory(db_session=test_db)


@pytest.fixture
def static_qr(qr_code_factory: QRCodeFactory) -> QRCode:
    """
    Create a static QR code for testing.
    
    Args:
        qr_code_factory: QRCodeFactory instance
        
    Returns:
        A static QR code instance
    """
    return qr_code_factory.create_static()


@pytest.fixture
def dynamic_qr(qr_code_factory: QRCodeFactory) -> QRCode:
    """
    Create a dynamic QR code for testing.
    
    Args:
        qr_code_factory: QRCodeFactory instance
        
    Returns:
        A dynamic QR code instance
    """
    return qr_code_factory.create_dynamic()


@pytest.fixture
def scanned_qr(qr_code_factory: QRCodeFactory) -> QRCode:
    """
    Create a dynamic QR code with scan history.
    
    Args:
        qr_code_factory: QRCodeFactory instance
        
    Returns:
        A dynamic QR code with scan history
    """
    return qr_code_factory.create_with_scans(
        scan_count=10,
        last_scan_days_ago=1,
        qr_type=QRType.DYNAMIC.value
    )


@pytest.fixture
def colored_qr(qr_code_factory: QRCodeFactory) -> QRCode:
    """
    Create a QR code with custom colors.
    
    Args:
        qr_code_factory: QRCodeFactory instance
        
    Returns:
        A QR code with custom colors
    """
    return qr_code_factory.create_static(
        fill_color="#FF0000",  # Red
        back_color="#0000FF",  # Blue
    )


@pytest.fixture
def historical_qr(qr_code_factory: QRCodeFactory) -> QRCode:
    """
    Create an older QR code.
    
    Args:
        qr_code_factory: QRCodeFactory instance
        
    Returns:
        A QR code created in the past
    """
    # Create a QR code from 30 days ago
    now = datetime.now(UTC)
    thirty_days_ago = now - timedelta(days=30)
    
    return qr_code_factory.create_static(
        created_at=thirty_days_ago
    )


@pytest.fixture
def static_qr_payload() -> dict[str, Any]:
    """
    Create a payload for creating a static QR code.
    
    Returns:
        dict: Static QR code creation payload
    """
    return {
        "qr_type": "static",
        "content": "https://example.com/test-create",
        "title": "Test Static QR",
        "description": "A test static QR code",
        "fill_color": "#000000",
        "back_color": "#FFFFFF",
    }


@pytest.fixture
def dynamic_qr_payload() -> dict[str, Any]:
    """
    Create a payload for creating a dynamic QR code.
    
    Returns:
        dict: Dynamic QR code creation payload
    """
    return {
        "qr_type": "dynamic",
        "redirect_url": "https://example.com/test-redirect",
        "title": "Test Dynamic QR",
        "description": "A test dynamic QR code",
        "fill_color": "#000000",
        "back_color": "#FFFFFF",
    }


@pytest.fixture
def invalid_color_payload() -> dict[str, Any]:
    """
    Create a payload with invalid color values.
    
    Returns:
        dict: QR code creation payload with invalid colors
    """
    return {
        "qr_type": "static",
        "content": "https://example.com/test-invalid",
        "title": "Invalid Color QR",
        "description": "A QR code with invalid colors",
        "fill_color": "invalid",  # Not a valid hex color
        "back_color": "#FFFFFF",
    }


@pytest.fixture
def invalid_url_payload() -> dict[str, Any]:
    """
    Create a payload with an invalid URL.
    
    Returns:
        dict: QR code creation payload with invalid URL
    """
    return {
        "qr_type": "static",
        "content": "not-a-valid-url",  # Not a valid URL
        "title": "Invalid URL QR",
        "description": "A QR code with an invalid URL",
        "fill_color": "#000000",
        "back_color": "#FFFFFF",
    }


@pytest.fixture
def create_static_qr_request(client, static_qr_payload):
    """
    Factory fixture for creating static QR codes in tests.
    
    Args:
        client: FastAPI test client
        static_qr_payload: Static QR code payload
        
    Returns:
        function: Function to create a static QR code
    """
    def _create(payload_override=None):
        """Create a static QR code with the given payload override."""
        payload = static_qr_payload.copy()
        if payload_override:
            payload.update(payload_override)
        return client.post("/api/v1/qr/static", json=payload)
    
    return _create


@pytest.fixture
def create_dynamic_qr_request(client, dynamic_qr_payload):
    """
    Factory fixture for creating dynamic QR codes in tests.
    
    Args:
        client: FastAPI test client
        dynamic_qr_payload: Dynamic QR code payload
        
    Returns:
        function: Function to create a dynamic QR code
    """
    def _create(payload_override=None):
        """Create a dynamic QR code with the given payload override."""
        payload = dynamic_qr_payload.copy()
        if payload_override:
            payload.update(payload_override)
        return client.post("/api/v1/qr/dynamic", json=payload)
    
    return _create


@pytest.fixture
def get_qr_request(client):
    """
    Factory fixture for getting QR codes in tests.
    
    Args:
        client: FastAPI test client
        
    Returns:
        function: Function to get a QR code
    """
    def _get(qr_id):
        """Get a QR code by ID."""
        return client.get(f"/api/v1/qr/{qr_id}")
    
    return _get


@pytest.fixture
def update_qr_request(client):
    """
    Factory fixture for updating QR codes in tests.
    
    Args:
        client: FastAPI test client
        
    Returns:
        function: Function to update a QR code
    """
    def _update(qr_id, payload):
        """Update a QR code by ID with the given payload."""
        return client.put(f"/api/v1/qr/{qr_id}", json=payload)
    
    return _update


@pytest.fixture
def list_qr_request(client):
    """
    Factory fixture for listing QR codes in tests.
    
    Args:
        client: FastAPI test client
        
    Returns:
        function: Function to list QR codes
    """
    def _list(params=None):
        """List QR codes with the given query parameters."""
        return client.get("/api/v1/qr", params=params)
    
    return _list


@pytest.fixture
def redirect_qr_request(client):
    """
    Factory fixture for testing QR code redirects.
    
    Args:
        client: FastAPI test client
        
    Returns:
        function: Function to test a QR code redirect
    """
    def _redirect(path, follow_redirects=False):
        """Test a QR code redirect with the given path."""
        return client.get(path, follow_redirects=follow_redirects)
    
    return _redirect


@pytest_asyncio.fixture
async def async_client(async_test_db) -> AsyncGenerator[TestClient, None]:
    """
    Create a FastAPI TestClient with dependency overrides for async testing.
    
    This fixture overrides key dependencies to use async test instances:
    - get_db_with_logging: Main database dependency used across the app
    - get_db: Backup direct database dependency (used in some places)
    
    Args:
        async_test_db: Async database session fixture
        
    Returns:
        TestClient: FastAPI test client
    """
    # Store original dependencies to restore later
    original_dependencies = {}
    
    try:
        # Import dependencies here for clarity
        from ..database import get_db, get_db_with_logging
        from ..services.qr import get_qr_service
        from ..repositories.qr import get_qr_repository
        
        # Store original dependencies
        original_dependencies = app.dependency_overrides.copy()
        
        # Define override functions to use the async test database session
        async def override_get_db():
            """Override the standard database session with async test session."""
            try:
                yield async_test_db
            finally:
                pass
        
        async def override_get_db_with_logging():
            """Override the standard database session with async test session."""
            try:
                yield async_test_db
            finally:
                pass
        
        # Configure dependency overrides
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_db_with_logging] = override_get_db_with_logging
        
        # Create and return the test client
        client = TestClient(app)
        yield client
    
    except Exception as e:
        # Restore original dependencies if an error occurs during setup
        app.dependency_overrides = original_dependencies
        raise e
    finally:
        # Restore original dependencies after the test
        app.dependency_overrides = original_dependencies


@pytest_asyncio.fixture
async def async_qr_code_factory(async_test_db) -> AsyncGenerator[QRCodeFactory, None]:
    """
    Fixture that provides a QRCodeFactory instance for async tests.
    
    Args:
        async_test_db: Async database session
        
    Returns:
        QRCodeFactory: Initialized factory with the async database session
    """
    # For now, we're using the standard QRCodeFactory with the async session
    # If needed, we could create an AsyncQRCodeFactory in the future
    yield QRCodeFactory(db_session=async_test_db)

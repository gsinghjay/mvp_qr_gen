"""
Test configuration and fixtures for the QR code generator API.
"""

import os
import uuid
import asyncio
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
from ..models.scan_log import ScanLog  # Add import for ScanLog model
from ..schemas.qr.models import QRType
from .factories import QRCodeFactory, ScanLogFactory  # Add ScanLogFactory import

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

# Create engine for schema management (with autocommit)
setup_engine = create_engine(
    TEST_DB_URL,
    isolation_level="AUTOCOMMIT",  # Important for DDL operations
)

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


def drop_all_tables():
    """
    Drop all tables in the test database.
    
    This function uses AUTOCOMMIT to ensure DDL changes are committed immediately.
    """
    print("--- Dropping all existing tables ---")
    
    # Use the setup_engine with AUTOCOMMIT
    with setup_engine.connect() as conn:
        # Disable foreign key constraints
        conn.execute(text("SET session_replication_role = 'replica'"))
        
        # Get list of all tables in public schema
        tables = conn.execute(text(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        )).scalars().all()
        
        if not tables:
            print("No tables found to drop")
            return
        
        print(f"Found tables: {tables}")
        
        # Drop each table
        for table in tables:
            try:
                print(f"Dropping table: {table}")
                conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
            except Exception as e:
                print(f"Error dropping table {table}: {e}")
        
        # Re-enable foreign key constraints
        conn.execute(text("SET session_replication_role = 'origin'"))
        
        print("Tables dropped successfully")


def create_schema_with_alembic():
    """
    Create the database schema using Alembic migrations.
    
    This gives us the benefit of having the alembic_version table
    with the latest migration version.
    """
    print("--- Creating schema with Alembic migrations ---")
    
    try:
        # Get Alembic configuration
        alembic_cfg = AlembicConfig("alembic.ini")
        
        # Run migrations
        alembic_command.upgrade(alembic_cfg, "head")
        print("Alembic migrations applied successfully")
        return True
    except Exception as e:
        print(f"Error applying Alembic migrations: {e}")
        return False


def create_schema_with_sqlalchemy():
    """
    Create the database schema using SQLAlchemy's metadata.create_all.
    
    This is a fallback if Alembic migrations fail. It won't create
    the alembic_version table.
    """
    print("--- Creating schema with SQLAlchemy metadata ---")
    
    try:
        # Create tables from SQLAlchemy models
        Base.metadata.create_all(bind=setup_engine)
        print("SQLAlchemy schema created successfully")
        return True
    except Exception as e:
        print(f"Error creating SQLAlchemy schema: {e}")
        return False


def verify_schema():
    """Verify that the required tables exist in the database."""
    print("--- Verifying schema ---")
    
    with setup_engine.connect() as conn:
        # Check for required tables
        qr_table_exists = conn.execute(text(
            "SELECT EXISTS (SELECT FROM pg_tables "
            "WHERE schemaname = 'public' AND tablename = 'qr_codes')"
        )).scalar()
        
        scan_table_exists = conn.execute(text(
            "SELECT EXISTS (SELECT FROM pg_tables "
            "WHERE schemaname = 'public' AND tablename = 'scan_logs')"
        )).scalar()
        
        # Check tables have expected columns
        if qr_table_exists:
            columns = conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = 'qr_codes'"
            )).scalars().all()
            print(f"qr_codes table columns: {columns}")
        
        tables_status = f"qr_codes: {qr_table_exists}, scan_logs: {scan_table_exists}"
        print(f"Schema verification: {tables_status}")
        
        return qr_table_exists and scan_table_exists


async def async_dispose_engines():
    """Properly dispose the async engine."""
    if async_engine is not None:
        await async_engine.dispose()


# Fixtures
@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Create the test database schema for the test session.
    
    This fixture runs once per test session and ensures that
    the database schema is properly created before any tests run.
    """
    print(f"\n--- Setting up test database: {TEST_DB_URL} ---")
    
    # Step 1: Drop all existing tables to start clean
    drop_all_tables()
    
    # Step 2: Create schema with Alembic (preferred method)
    alembic_success = create_schema_with_alembic()
    
    # Step 3: If Alembic fails, fall back to SQLAlchemy metadata
    if not alembic_success:
        print("Falling back to SQLAlchemy schema creation")
        create_schema_with_sqlalchemy()
    
    # Step 4: Verify schema was created correctly
    if not verify_schema():
        raise RuntimeError("Failed to create schema for testing. Verify database permissions.")
    
    # All good - yield to let tests run
    yield
    
    # Tests are done - dispose of engines
    print("\n--- Testing complete, disposing engines ---")
    setup_engine.dispose()
    engine.dispose()
    
    # Handle async engine disposal
    try:
        # Create an event loop if needed
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run the async disposal
        loop.run_until_complete(async_dispose_engines())
    except Exception as e:
        print(f"Warning: Could not properly dispose async engine: {e}")
        # This is not critical for tests, so continue


@pytest.fixture(autouse=True)
def reset_test_database_between_tests(request):
    """Reset the test database between tests by truncating all tables."""
    # Skip for session-scoped fixtures
    if 'setup_test_database' in request.fixturenames:
        yield
        return
        
    # Get all table names
    with engine.connect() as conn:
        tables = conn.execute(text(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        )).scalars().all()
        
        # Start a transaction
        with conn.begin():
            # Disable foreign key checks temporarily
            conn.execute(text("SET session_replication_role = 'replica'"))
            
            # Truncate all tables
            for table in tables:
                # Skip alembic_version table
                if table != 'alembic_version':
                    conn.execute(text(f'TRUNCATE TABLE "{table}" CASCADE'))
            
            # Re-enable foreign key checks
            conn.execute(text("SET session_replication_role = 'origin'"))
    
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
    - get_qr_repository: Repository for QR code operations
    - get_qr_service: Service for QR code business logic

    Args:
        test_db: Database session fixture

    Returns:
        TestClient: FastAPI test client
    """
    # Store original dependencies to restore later
    original_dependencies = {}

    try:
        # Import all application dependencies
        from app.database import get_db, get_db_with_logging
        from app.dependencies import get_qr_service, get_qr_repository
        
        # Import test-specific dependencies
        from app.tests.dependencies import (
            get_test_db,
            get_test_db_with_logging,
            get_qr_repository as get_test_qr_repository,
            get_qr_service as get_test_qr_service,
        )

        # Store original dependencies
        original_dependencies = app.dependency_overrides.copy()

        # Override database session dependencies with test-specific versions
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

        # Configure dependency overrides for database, repository, and service
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_db_with_logging] = override_get_db_with_logging
        app.dependency_overrides[get_qr_repository] = get_test_qr_repository
        app.dependency_overrides[get_qr_service] = get_test_qr_service

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
    Fixture to create QR code factory with test database session.
    
    Returns a QRCodeFactory instance with the current test database session for
    creating QR codes in tests. This factory encapsulates the logic for generating
    valid test QR codes with sensible defaults.
    
    Args:
        test_db: Current test database session
        
    Returns:
        QRCodeFactory instance with the test session
    """
    return QRCodeFactory(test_db)


@pytest.fixture
def scan_log_factory(test_db: Session) -> ScanLogFactory:
    """
    Fixture to create scan log factory with test database session.
    
    Returns a ScanLogFactory instance with the current test database session for
    creating scan logs in tests. This factory encapsulates the logic for generating
    valid test scan logs with sensible defaults.
    
    Args:
        test_db: Current test database session
        
    Returns:
        ScanLogFactory instance with the test session
    """
    return ScanLogFactory(test_db)


@pytest.fixture
def qr_with_scans(qr_code_factory: QRCodeFactory, scan_log_factory: ScanLogFactory) -> tuple[QRCode, list[ScanLog]]:
    """
    Fixture to create a QR code with associated scan logs.
    
    Creates a dynamic QR code with a mix of genuine and non-genuine scans
    for testing scan statistics and analytics features.
    
    Args:
        qr_code_factory: Factory for creating QR codes
        scan_log_factory: Factory for creating scan logs
        
    Returns:
        Tuple of (QRCode instance, list of ScanLog instances)
    """
    # Create a dynamic QR code
    qr_code = qr_code_factory.create_dynamic()
    
    # Create a mix of genuine and non-genuine scans
    scan_logs = scan_log_factory.create_batch_for_qr(
        qr_code=qr_code,
        count=20,  # 20 total scans
        genuine_ratio=0.7,  # 70% genuine scans
        max_days_ago=14,  # Up to 14 days old
    )
    
    # Update QR code scan statistics to match
    genuine_count = sum(1 for log in scan_logs if log.is_genuine_scan)
    
    # Update scan counts in QR code
    qr_code.scan_count = len(scan_logs)
    qr_code.genuine_scan_count = genuine_count
    
    # Set latest scan timestamps
    if scan_logs:
        # Find the most recent scan timestamp
        all_scan_timestamps = [log.scanned_at for log in scan_logs]
        last_scan_at = max(all_scan_timestamps)
        qr_code.last_scan_at = last_scan_at
        
        # Find most recent genuine scan timestamp
        genuine_scan_timestamps = [log.scanned_at for log in scan_logs if log.is_genuine_scan]
        if genuine_scan_timestamps:
            last_genuine_scan_at = max(genuine_scan_timestamps)
            qr_code.last_genuine_scan_at = last_genuine_scan_at
            
            # Set first genuine scan timestamp if not already set
            if not qr_code.first_genuine_scan_at:
                first_genuine_scan_at = min(genuine_scan_timestamps)
                qr_code.first_genuine_scan_at = first_genuine_scan_at
    
    # No need to commit - test transactions handle this
    
    return qr_code, scan_logs


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
    Create an asynchronous FastAPI TestClient with dependency overrides for testing.

    This fixture overrides key dependencies to use test instances:
    - get_db_with_logging: Main database dependency used across the app
    - get_db: Backup direct database dependency (used in some places)
    - get_qr_repository: Repository for QR code operations
    - get_qr_service: Service for QR code business logic

    Args:
        async_test_db: Async database session fixture

    Returns:
        TestClient: FastAPI test client
    """
    # Store original dependencies to restore later
    original_dependencies = {}

    try:
        # Import all application dependencies
        from app.database import get_db, get_db_with_logging
        from app.dependencies import get_qr_service, get_qr_repository
        
        # Import test-specific dependencies (will need async versions in the future)
        from app.tests.dependencies import (
            get_qr_repository as get_test_qr_repository,
            get_qr_service as get_test_qr_service,
        )

        # Store original dependencies
        original_dependencies = app.dependency_overrides.copy()

        # Override database session dependencies with async test-specific versions
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
            
        # We need special async repository/service overrides
        # For now, we're using the non-async versions, but these should be replaced
        # with properly async versions in the future

        # Configure dependency overrides for database, repository, and service
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_db_with_logging] = override_get_db_with_logging
        app.dependency_overrides[get_qr_repository] = get_test_qr_repository
        app.dependency_overrides[get_qr_service] = get_test_qr_service

        # Create and return the test client
        client = TestClient(app)
        yield client
    finally:
        # Restore original dependencies
        app.dependency_overrides = original_dependencies


@pytest_asyncio.fixture
async def async_qr_code_factory(async_test_db) -> AsyncGenerator[QRCodeFactory, None]:
    """
    Async fixture that provides a QRCodeFactory instance for async tests.
    
    Returns a QRCodeFactory instance with the current async test database session
    for creating QR codes in async tests.
    
    Args:
        async_test_db: Async test database session
        
    Yields:
        Initialized QRCodeFactory with async database session
    """
    factory = QRCodeFactory(async_test_db)
    yield factory


@pytest_asyncio.fixture
async def async_scan_log_factory(async_test_db) -> AsyncGenerator[ScanLogFactory, None]:
    """
    Async fixture that provides a ScanLogFactory instance for async tests.
    
    Returns a ScanLogFactory instance with the current async test database session
    for creating scan logs in async tests.
    
    Args:
        async_test_db: Async test database session
        
    Yields:
        Initialized ScanLogFactory with async database session
    """
    factory = ScanLogFactory(async_test_db)
    yield factory


@pytest_asyncio.fixture
async def async_qr_with_scans(
    async_qr_code_factory: QRCodeFactory, 
    async_scan_log_factory: ScanLogFactory
) -> AsyncGenerator[tuple[QRCode, list[ScanLog]], None]:
    """
    Async fixture to create a QR code with associated scan logs for async tests.
    
    Creates a dynamic QR code with a mix of genuine and non-genuine scans
    for testing scan statistics and analytics features in async tests.
    
    Args:
        async_qr_code_factory: Factory for creating QR codes in async context
        async_scan_log_factory: Factory for creating scan logs in async context
        
    Yields:
        Tuple of (QRCode instance, list of ScanLog instances)
    """
    # Create a dynamic QR code
    qr_code = await async_qr_code_factory.async_create_with_params(
        qr_type=QRType.DYNAMIC,
        redirect_url=fake.url()
    )
    
    # Create genuine scans (70%)
    genuine_count = 14  # 70% of 20
    genuine_scans = []
    for _ in range(genuine_count):
        days_ago = fake.random.randint(0, 14)
        hours_ago = fake.random.randint(0, 23)
        
        # Random device type distribution (mostly mobile for genuine scans)
        is_mobile = fake.random.random() < 0.7  # 70% mobile
        is_tablet = not is_mobile and fake.random.random() < 0.4  # 12% tablet (40% of non-mobile)
        is_pc = not (is_mobile or is_tablet)  # 18% PC
        
        scan_log = await async_scan_log_factory.async_create_for_qr(
            qr_code=qr_code,
            is_genuine_scan=True,
            days_ago=days_ago,
            hours_ago=hours_ago,
            is_mobile=is_mobile,
            is_tablet=is_tablet,
            is_pc=is_pc
        )
        genuine_scans.append(scan_log)
    
    # Create non-genuine scans (30%)
    non_genuine_count = 6  # 30% of 20
    non_genuine_scans = []
    for _ in range(non_genuine_count):
        days_ago = fake.random.randint(0, 14)
        hours_ago = fake.random.randint(0, 23)
        
        # Random device type distribution (mostly desktop for non-genuine)
        is_mobile = fake.random.random() < 0.2  # 20% mobile
        is_tablet = not is_mobile and fake.random.random() < 0.1  # 8% tablet
        is_pc = not (is_mobile or is_tablet)  # 72% PC
        
        scan_log = await async_scan_log_factory.async_create_for_qr(
            qr_code=qr_code,
            is_genuine_scan=False,
            days_ago=days_ago,
            hours_ago=hours_ago,
            is_mobile=is_mobile,
            is_tablet=is_tablet,
            is_pc=is_pc
        )
        non_genuine_scans.append(scan_log)
    
    # Combine all scan logs
    scan_logs = genuine_scans + non_genuine_scans
    
    # Update QR code scan statistics to match
    qr_code.scan_count = len(scan_logs)
    qr_code.genuine_scan_count = genuine_count
    
    # Set latest scan timestamps
    if scan_logs:
        # Find the most recent scan timestamp
        all_scan_timestamps = [log.scanned_at for log in scan_logs]
        last_scan_at = max(all_scan_timestamps)
        qr_code.last_scan_at = last_scan_at
        
        # Find most recent genuine scan timestamp
        genuine_scan_timestamps = [log.scanned_at for log in scan_logs if log.is_genuine_scan]
        if genuine_scan_timestamps:
            last_genuine_scan_at = max(genuine_scan_timestamps)
            qr_code.last_genuine_scan_at = last_genuine_scan_at
            
            # Set first genuine scan timestamp if not already set
            if not qr_code.first_genuine_scan_at:
                first_genuine_scan_at = min(genuine_scan_timestamps)
                qr_code.first_genuine_scan_at = first_genuine_scan_at
    
    # No need to commit - async tests handle transactions
    
    yield qr_code, scan_logs

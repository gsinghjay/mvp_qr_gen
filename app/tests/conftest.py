"""
Test configuration and fixtures for the QR code generator API.
"""

import os
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from ..database import Base, get_db_with_logging, get_db
from ..main import app

# Set test environment
os.environ["ENVIRONMENT"] = "test"

# Test database URL - using in-memory SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"


def configure_sqlite_connection(dbapi_connection, connection_record):
    """Configure SQLite connection with appropriate PRAGMAs."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()


# Create test engine with StaticPool for better in-memory database performance
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "isolation_level": None,  # Let SQLite handle transactions
    },
    poolclass=StaticPool,  # Use StaticPool for in-memory database
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


@pytest.fixture(autouse=True)
def setup_test_database():
    """Create test database tables before each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


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


# Enable foreign key support for SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable foreign key support for SQLite."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

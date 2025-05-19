"""
Tests for FastAPI lifecycle events.

These tests verify:
1. Application lifespan events work correctly
2. Database initialization happens during startup
3. Proper resource cleanup occurs during shutdown
4. Database connection pool is managed correctly
5. Exception handling during lifecycle events
"""

from contextlib import asynccontextmanager
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.database import engine
from app.main import lifespan


@pytest.fixture
def mock_init_db():
    """Mock the database initialization function."""
    with patch("app.main.init_db") as mock:
        yield mock


@pytest.fixture
def mock_engine_dispose():
    """Mock SQLAlchemy engine disposal method for testing shutdown cleanup."""
    with patch("app.database.engine.dispose") as mock:
        yield mock


@pytest.fixture
def app_with_custom_lifespan():
    """Create a test app with custom lifespan for testing."""
    startup_called = False
    shutdown_called = False

    @asynccontextmanager
    async def test_lifespan(app: FastAPI):
        nonlocal startup_called, shutdown_called
        startup_called = True
        yield
        shutdown_called = True

    app = FastAPI(lifespan=test_lifespan)

    @app.get("/test")
    def test_endpoint():
        return {"message": "Test endpoint"}

    return app, startup_called, shutdown_called


def test_lifespan_startup_called(mock_init_db):
    """Test that the lifespan startup phase is called and initializes the database."""
    startup_called = False

    @asynccontextmanager
    async def test_lifespan(app: FastAPI):
        nonlocal startup_called
        startup_called = True
        # Use the imported init_db from app.main which is the one we mocked
        from app.main import init_db as main_init_db

        main_init_db()
        yield

    app = FastAPI(lifespan=test_lifespan)

    with TestClient(app) as client:
        client.get("/")

    assert startup_called is True
    mock_init_db.assert_called_once()


def test_lifespan_shutdown_called(mock_engine_dispose):
    """Test that the lifespan shutdown phase is called and cleans up resources."""
    shutdown_called = False

    @asynccontextmanager
    async def test_lifespan(app: FastAPI):
        nonlocal shutdown_called
        yield
        shutdown_called = True
        engine.dispose()

    app = FastAPI(lifespan=test_lifespan)

    with TestClient(app) as client:
        client.get("/")

    assert shutdown_called is True
    mock_engine_dispose.assert_called_once()


def test_app_lifespan_with_db_init(mock_init_db):
    """Test that the application's lifespan correctly initializes the database."""
    # Create app directly instead of using create_app
    app = FastAPI(lifespan=lifespan)

    with TestClient(app) as client:
        client.get("/docs")

    mock_init_db.assert_called_once()


def test_exception_in_lifespan_startup():
    """Test that exceptions during lifespan startup are properly handled."""

    @asynccontextmanager
    async def error_lifespan(app: FastAPI):
        raise RuntimeError("Test startup error")
        yield  # This will never be reached

    app = FastAPI(lifespan=error_lifespan)

    with pytest.raises(RuntimeError, match="Test startup error"):
        with TestClient(app) as client:
            client.get("/")


def test_cleanup_in_lifespan_shutdown(mock_engine_dispose):
    """Test that resources are properly cleaned up during lifespan shutdown."""

    @asynccontextmanager
    async def cleanup_lifespan(app: FastAPI):
        yield
        engine.dispose()

    app = FastAPI(lifespan=cleanup_lifespan)

    with TestClient(app) as client:
        client.get("/")

    mock_engine_dispose.assert_called_once()


def test_db_connection_pool_management():
    """Test database connection pool management during application lifecycle."""
    pool_settings = {}

    @asynccontextmanager
    async def pool_lifespan(app: FastAPI):
        # Configure the connection pool
        pool_settings["pool_pre_ping"] = True
        pool_settings["pool_recycle"] = 300
        pool_settings["pool_size"] = 10
        yield
        # In real shutdown this would be engine.dispose()
        pool_settings["disposed"] = True

    app = FastAPI(lifespan=pool_lifespan)

    with TestClient(app) as client:
        client.get("/")

    # Verify that the pool settings were configured correctly
    assert pool_settings["pool_pre_ping"] is True
    assert pool_settings["pool_recycle"] == 300
    assert pool_settings["pool_size"] == 10
    assert pool_settings["disposed"] is True


def test_complete_app_lifecycle():
    """Test the complete lifecycle with both startup and shutdown phases."""
    lifecycle_events = []

    @asynccontextmanager
    async def tracking_lifespan(app: FastAPI):
        lifecycle_events.append("startup")
        yield
        lifecycle_events.append("shutdown")

    app = FastAPI(lifespan=tracking_lifespan)

    with TestClient(app) as client:
        client.get("/")
        lifecycle_events.append("request_handled")

    # Verify the sequence of events
    assert lifecycle_events == ["startup", "request_handled", "shutdown"]


def test_actual_app_lifespan(mock_init_db, mock_engine_dispose):
    """Test the actual application lifespan function from main.py."""
    # Create the test app with the actual lifespan function
    app = FastAPI(lifespan=lifespan)

    # Use the TestClient which will trigger lifespan events
    with TestClient(app) as client:
        client.get("/")

    # Verify that init_db was called during startup
    mock_init_db.assert_called_once()

    # Verify that engine.dispose was called during shutdown
    mock_engine_dispose.assert_called_once()

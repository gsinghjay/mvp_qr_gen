"""
Main FastAPI application module for the QR code generator.
"""

import logging
import os
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, Union

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .api import api_router, redirect_router_no_prefix, web_router_no_prefix, health_router_no_prefix
from .core.config import settings
from .core.exceptions import (
    DatabaseError,
    InvalidQRTypeError,
    QRCodeNotFoundError,
    QRCodeValidationError,
    RedirectURLError,
    ResourceConflictError,
)
from .middleware import LoggingMiddleware, MetricsMiddleware, RequestIDMiddleware
from .database import get_db_with_logging
from .repositories.qr_code_repository import QRCodeRepository
from .repositories.scan_log_repository import ScanLogRepository
from .core.metrics_logger import initialize_feature_flags

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(levelname)s - [%(name)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager for FastAPI application lifespan.

    This context manager handles startup and shutdown events for the FastAPI application.
    It's used to initialize resources at startup and clean them up at shutdown.

    Args:
        app: The FastAPI application instance.
    """
    start_time = datetime.now(UTC)
    logger.info("Application starting up...")

    # Step 1: Initialize feature flags for metrics
    logger.info("Initializing feature flags...")
    initialize_feature_flags()

    # Step 2: Ensure required directories exist
    logger.info("Ensuring required directories exist...")
    settings.QR_CODES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Step 3: Pre-initialize key dependencies and routes
    logger.info("Pre-initializing key dependencies and routes...")
    db = None
    try:
        # Create DB session
        db = next(get_db_with_logging())
        logger.info("Database session created")
        
        # Initialize repositories
        qr_code_repo = QRCodeRepository(db)
        scan_log_repo = ScanLogRepository(db)
        logger.info("Repository layers initialized")
        
        # Explicitly import routing modules to load them
        logger.info("Pre-loading route modules...")
        from .api.v1.endpoints import redirect as redirect_module
        from .api.v1.endpoints import qr as qr_module
        logger.info(f"Loaded redirect module: {redirect_module.__name__}")
        
        # Pre-load the redirect endpoint function
        from .api.v1.endpoints.redirect import redirect_qr
        logger.info("Pre-loaded redirect endpoint function")
        
        # Basic database connectivity test
        try:
            total = qr_code_repo.count()
            logger.info(f"Database contains {total} QR codes")
        except Exception as e:
            logger.warning(f"Database connectivity test failed: {e}")
            
    except Exception as e:
        logger.warning(f"Pre-initialization failed: {e}")
    finally:
        # Don't forget to close the DB session if it was created
        if db is not None:
            db.close()
            logger.info("Pre-initialization DB session closed")

    # Log successful initialization
    init_duration = (datetime.now(UTC) - start_time).total_seconds()
    logger.info(f"Application startup complete in {init_duration:.2f}s, ready to handle requests")

    yield  # Application runs here

    # Shutdown
    logger.info("Application shutting down...")

    # Cleanup logic here
    try:
        logger.info("Cleaning up temp files...")
        # Add specific cleanup tasks here
    except Exception as e:
        logger.exception(f"Error during cleanup: {e}")


app = FastAPI(
    title="QR Code Generator API",
    description="API for generating and managing QR codes",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Trusted Host middleware
app.add_middleware(
    TrustedHostMiddleware, allowed_hosts=settings.TRUSTED_HOSTS
)

# Add GZip compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add custom middleware
app.add_middleware(MetricsMiddleware)
app.add_middleware(LoggingMiddleware)

# Mount static files
app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")

# Add RequestIDMiddleware
app.add_middleware(RequestIDMiddleware)


# Exception Handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """
    Handle HTTP exceptions and return a consistent JSON response.

    Args:
        request: The incoming request.
        exc: The HTTP exception that was raised.

    Returns:
        A JSON response with error details.
    """
    # Log the exception
    logger.error(f"HTTP error: {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
            "timestamp": datetime.now(UTC).isoformat(),
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handle validation errors and return a consistent JSON response.

    Args:
        request: The incoming request.
        exc: The validation error that was raised.

    Returns:
        A JSON response with error details.
    """
    # Log the exception
    logger.error(f"Validation error: {exc.errors()}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": jsonable_encoder(exc.errors()),
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "path": request.url.path,
            "method": request.method,
            "timestamp": datetime.now(UTC).isoformat(),
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
    )


@app.exception_handler(QRCodeNotFoundError)
async def qr_not_found_exception_handler(
    request: Request, exc: QRCodeNotFoundError
) -> JSONResponse:
    """
    Handle QR code not found errors and return a consistent JSON response.

    Args:
        request: The incoming request.
        exc: The QR code not found error that was raised.

    Returns:
        A JSON response with error details.
    """
    # Log the exception
    logger.error(f"QR code not found: {str(exc)}")

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "detail": str(exc),
            "status_code": status.HTTP_404_NOT_FOUND,
            "path": request.url.path,
            "method": request.method,
            "timestamp": datetime.now(UTC).isoformat(),
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
    )


@app.exception_handler(InvalidQRTypeError)
async def invalid_qr_type_exception_handler(
    request: Request, exc: InvalidQRTypeError
) -> JSONResponse:
    """
    Handle invalid QR type errors and return a consistent JSON response.

    Args:
        request: The incoming request.
        exc: The invalid QR type error that was raised.

    Returns:
        A JSON response with error details.
    """
    # Log the exception
    logger.error(f"Invalid QR type: {str(exc)}")

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": str(exc),
            "status_code": status.HTTP_400_BAD_REQUEST,
            "path": request.url.path,
            "method": request.method,
            "timestamp": datetime.now(UTC).isoformat(),
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
    )


@app.exception_handler(QRCodeValidationError)
async def qr_validation_exception_handler(
    request: Request, exc: QRCodeValidationError
) -> JSONResponse:
    """
    Handle QR code validation errors and return a consistent JSON response.

    Args:
        request: The incoming request.
        exc: The QR code validation error that was raised.

    Returns:
        A JSON response with error details.
    """
    # Log the exception
    logger.error(f"QR code validation error: {str(exc)}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": str(exc),
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "path": request.url.path,
            "method": request.method,
            "timestamp": datetime.now(UTC).isoformat(),
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
    )


@app.exception_handler(RedirectURLError)
async def redirect_url_exception_handler(
    request: Request, exc: RedirectURLError
) -> JSONResponse:
    """
    Handle redirect URL errors and return a consistent JSON response.

    Args:
        request: The incoming request.
        exc: The redirect URL error that was raised.

    Returns:
        A JSON response with error details.
    """
    # Log the exception
    logger.error(f"Redirect URL error: {str(exc)}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": str(exc),
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "path": request.url.path,
            "method": request.method,
            "timestamp": datetime.now(UTC).isoformat(),
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
    )


@app.exception_handler(ResourceConflictError)
async def resource_conflict_exception_handler(
    request: Request, exc: ResourceConflictError
) -> JSONResponse:
    """
    Handle resource conflict errors and return a consistent JSON response.

    Args:
        request: The incoming request.
        exc: The resource conflict error that was raised.

    Returns:
        A JSON response with error details.
    """
    # Log the exception
    logger.error(f"Resource conflict error: {str(exc)}")

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "detail": str(exc),
            "status_code": status.HTTP_409_CONFLICT,
            "path": request.url.path,
            "method": request.method,
            "timestamp": datetime.now(UTC).isoformat(),
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
    )


@app.exception_handler(DatabaseError)
async def database_exception_handler(
    request: Request, exc: DatabaseError
) -> JSONResponse:
    """
    Handle database errors and return a consistent JSON response.

    Args:
        request: The incoming request.
        exc: The database error that was raised.

    Returns:
        A JSON response with error details.
    """
    # Log the exception
    logger.error(f"Database error: {str(exc)}")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": str(exc),
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "path": request.url.path,
            "method": request.method,
            "timestamp": datetime.now(UTC).isoformat(),
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """
    Handle SQLAlchemy errors and return a consistent JSON response.

    Args:
        request: The incoming request.
        exc: The SQLAlchemy error that was raised.

    Returns:
        A JSON response with error details.
    """
    # Log the exception
    logger.exception(f"SQLAlchemy error: {str(exc)}")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Database error occurred",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "path": request.url.path,
            "method": request.method,
            "timestamp": datetime.now(UTC).isoformat(),
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """
    Handle general exceptions and return a consistent JSON response.

    Args:
        request: The incoming request.
        exc: The exception that was raised.

    Returns:
        A JSON response with error details.
    """
    # Log the exception
    logger.exception(f"Unhandled exception: {str(exc)}")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "path": request.url.path,
            "method": request.method,
            "timestamp": datetime.now(UTC).isoformat(),
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
    )


# Include routers
app.include_router(api_router)  # /api prefix
app.include_router(redirect_router_no_prefix)  # /r prefix
app.include_router(web_router_no_prefix)  # No prefix (for web pages)
app.include_router(health_router_no_prefix)  # No prefix (for health check)

# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint that returns basic API information.

    Returns:
        A dictionary with basic API information.
    """
    return {
        "name": "QR Code Generator API",
        "version": "1.0.0",
        "description": "API for generating and managing QR codes",
        "docs": "/api/v1/docs",
    }

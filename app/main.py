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
from .services.qr_service import QRCodeService
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
        
        # Initialize repositories and services
        qr_code_repo = QRCodeRepository(db)
        scan_log_repo = ScanLogRepository(db)
        qr_service = QRCodeService(qr_code_repo=qr_code_repo, scan_log_repo=scan_log_repo)
        logger.info("Repository and service layers initialized")
        
        # Explicitly import routing modules to load them
        logger.info("Pre-loading route modules...")
        from .api.v1.endpoints import redirect as redirect_module
        from .api.v1.endpoints import qr as qr_module
        logger.info(f"Loaded redirect module: {redirect_module.__name__}")
        
        # Pre-load the redirect endpoint function
        from .api.v1.endpoints.redirect import redirect_qr
        logger.info("Pre-loaded redirect endpoint function")
        
        # Try to warm up the most common code paths
        try:
            # Initialize database query paths
            total = qr_code_repo.count()
            logger.info(f"Database contains {total} QR codes")
            
            # Initialize API endpoints and template rendering
            recent_qrs, _ = qr_code_repo.list_qr_codes(skip=0, limit=5)
            
            if recent_qrs:
                # Warm ORM model conversion paths
                logger.info(f"Warming up ORM paths for {len(recent_qrs)} QR codes...")
                _ = [qr.id for qr in recent_qrs]
                _ = [qr.to_dict() for qr in recent_qrs]
                
                # Warm up QR generation paths
                if len(recent_qrs) > 0:
                    first_qr = recent_qrs[0]
                    logger.info("Warming up QR image generation...")
                    # Generate a test QR image to warm up the image generation path
                    _ = qr_service.generate_qr(
                        data=first_qr.content,
                        size=10,
                        border=4,
                        fill_color=first_qr.fill_color,
                        back_color=first_qr.back_color,
                        image_format="png",
                        image_quality=90,
                        include_logo=False,
                        error_level="M"
                    )
                
                # Exercise the critical redirect path
                logger.info("Warming up redirect code paths...")
                dynamic_qrs = [qr for qr in recent_qrs if qr.qr_type == "dynamic"]
                if dynamic_qrs:
                    dynamic_qr = dynamic_qrs[0]
                    # Extract the short_id from the content
                    content = dynamic_qr.content
                    if content and "/r/" in content:
                        # Extract short_id from the URL path
                        short_id = content.split("/r/")[-1]
                        
                        # CRITICAL: Warm up the exact service method used by redirect endpoint
                        logger.info(f"Warming up get_qr_by_short_id with {short_id}...")
                        try:
                            # This uses direct lookup by short_id
                            found_qr = qr_service.get_qr_by_short_id(short_id)
                            logger.info(f"Successfully retrieved QR via short_id: {found_qr.id}")
                            
                            # Warm up redirect URL access
                            if found_qr.qr_type == "dynamic" and found_qr.redirect_url:
                                logger.info(f"Verifying redirect URL: {found_qr.redirect_url}")
                            
                            # Warm up the update_scan_statistics method (used in background task)
                            try:
                                # Call with minimal parameters since we're just warming up
                                qr_service.update_scan_statistics(
                                    qr_id=found_qr.id,
                                    timestamp=datetime.now(UTC)
                                )
                                logger.info("Warmed up scan statistics update path")
                            except Exception as e:
                                logger.warning(f"Scan statistics update warm-up failed: {e}")
                                
                        except Exception as e:
                            logger.warning(f"Service method warm-up failed: {e}")
                            
                            # Log the error but continue initialization
                            logger.warning(f"Unable to warm up QR redirect path: {e}")
                            logger.info("Application will continue to initialize")
            else:
                # If no QRs exist, create test ones to warm up paths
                logger.info("No QR codes found, creating test QRs for initialization...")
                
                # Create a static test QR
                test_static_qr = qr_service.create_static_qr({
                    "content": "warmup-test",
                    "size": 5,
                    "border": 1,
                    "fill_color": "#000000",
                    "back_color": "#FFFFFF"
                })
                
                # Create a dynamic test QR
                test_dynamic_qr = qr_service.create_dynamic_qr({
                    "redirect_url": "https://example.com",
                    "size": 5,
                    "border": 1,
                    "fill_color": "#000000",
                    "back_color": "#FFFFFF"
                })
                
                # CRITICAL: Exercise the exact service method used by redirect endpoint
                content = test_dynamic_qr.content
                if content and "/r/" in content:
                    short_id = content.split("/r/")[-1]
                    logger.info(f"Warming up get_qr_by_short_id with test QR {short_id}...")
                    try:
                        found_qr = qr_service.get_qr_by_short_id(short_id)
                        logger.info(f"Successfully retrieved test QR via short_id service method")
                        
                        # Warm up scan statistics with the test QR
                        qr_service.update_scan_statistics(qr_id=found_qr.id)
                        logger.info("Warmed up scan statistics with test QR")
                    except Exception as e:
                        logger.warning(f"Service method warm-up failed: {e}")
                        logger.info("Application will continue to initialize")
                
                # Generate test image
                _ = qr_service.generate_qr(
                    data=test_static_qr.content,
                    size=5,
                    border=1,
                    fill_color="#000000",
                    back_color="#FFFFFF",
                    image_format="png"
                )
                
                # Clean up test QRs - using correct delete method
                qr_code_repo.delete(test_static_qr.id)
                qr_code_repo.delete(test_dynamic_qr.id)
                logger.info("Cleaned up test QRs after initialization")
                
            # Warm up error handling code paths
            logger.info("Warming up error handling code paths...")
            
        except Exception as e:
            logger.warning(f"Pre-initialization operation failed: {e}")
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

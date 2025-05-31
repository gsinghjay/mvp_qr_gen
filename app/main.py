"""
Main FastAPI application module for the QR code generator.
"""

import logging
import os
from contextlib import asynccontextmanager
from datetime import timezone, datetime # Changed UTC import
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
# QRCodeService is still imported as it's the entry point for dependencies,
# but its internal structure has changed.
from .services.qr_service import QRCodeService
from .core.metrics_logger import initialize_feature_flags

# Import dependencies for lifespan, even if QRCodeService facade handles them
from .dependencies import get_qr_code_service # To get the facade
from .dependencies import get_db # To get db session for direct repo usage in lifespan if necessary

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
    start_time = datetime.now(timezone.utc) # Changed UTC
    logger.info("Application starting up...")

    # Step 1: Initialize feature flags for metrics
    logger.info("Initializing feature flags...")
    initialize_feature_flags()

    # Step 2: Ensure required directories exist
    logger.info("Ensuring required directories exist...")
    settings.QR_CODES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Step 3: Pre-initialize key dependencies and routes
    logger.info("Pre-initializing key dependencies and routes...")

    # The new way to get qr_service (facade) involves FastAPI's dependency injection.
    # For lifespan, direct instantiation or a simplified DI might be needed if app context isn't fully available.
    # However, the original code directly instantiated repositories and then QRCodeService.
    # We'll adapt this. The actual service instances are now built up by get_qr_code_service.
    # For warming up, we might need a way to get the dependent services or repos.

    db_gen = get_db_with_logging() # Get a generator for the DB session
    db = None
    try:
        db = next(db_gen) # Get an actual DB session
        logger.info("Database session created for lifespan")

        # Direct instantiation of repositories for lifespan tasks
        qr_code_repo = QRCodeRepository(db)
        # scan_log_repo = ScanLogRepository(db) # Not directly used by old qr_service for warmup here

        # We need a qr_service instance. The old code was:
        # qr_service = QRCodeService(qr_code_repo=qr_code_repo, scan_log_repo=scan_log_repo)
        # This needs to be adapted if the new QRCodeService facade has a different constructor signature
        # and relies on DI for its specialized services.
        # For lifespan, we might need to manually construct the facade with its dependencies if DI is tricky here.
        # Let's assume for now we can get an instance of the facade, or its relevant sub-services.
        # The current QRCodeService facade takes the specialized services.
        # For the warmup, we need methods like `generate_qr`, `get_qr_by_short_id`, `update_scan_statistics`,
        # `create_static_qr`, `create_dynamic_qr`. These are on the facade.

        # This part is tricky because get_qr_code_service is a FastAPI dependency.
        # We cannot easily call it here like a normal function without a request context.
        # The original code *directly* instantiated QRCodeService with repos.
        # The new QRCodeService facade requires the specialized services.
        # To replicate warmup, we might need to:
        # 1. Manually instantiate the specialized services and then the facade (complex).
        # 2. OR: Only warm up repository methods and assume service wiring is okay.
        # 3. OR: The warmup logic might need to be re-thought with the new service structure.

        # Option 2: Warm up repository methods (simplest for now)
        logger.info("Repository and service layers initialized (repos for now)")
        
        # Explicitly import routing modules to load them
        logger.info("Pre-loading route modules...")
        from .api.v1.endpoints import redirect as redirect_module
        from .api.v1.endpoints import qr as qr_module
        logger.info(f"Loaded redirect module: {redirect_module.__name__}")
        
        # Pre-load the redirect endpoint function
        from .api.v1.endpoints.redirect import redirect_qr
        logger.info("Pre-loaded redirect endpoint function")
        
        # Try to warm up the most common code paths using repositories
        try:
            total = qr_code_repo.count()
            logger.info(f"Database contains {total} QR codes (repo warmup)")
            
            recent_qrs, _ = qr_code_repo.list_qr_codes(skip=0, limit=5)
            
            if recent_qrs:
                logger.info(f"Warming up ORM paths for {len(recent_qrs)} QR codes...")
                _ = [qr.id for qr in recent_qrs]
                _ = [qr.to_dict() for qr in recent_qrs]
                
                # QR generation and redirect path warmup is harder without a full service instance easily.
                # The original code relied on qr_service methods.
                # For now, we'll skip the deeper service-level warmup in lifespan due to DI complexity.
                # This might mean the first few requests to those paths could be slower.
                logger.info("Skipping service-level QR generation and redirect warmup in lifespan due to new DI structure.")

                # Old warmup code that needs a full qr_service instance:
                # if len(recent_qrs) > 0:
                #     first_qr = recent_qrs[0]
                #     # ... qr_service.generate_qr(...) ...
                # dynamic_qrs = [qr for qr in recent_qrs if qr.qr_type == "dynamic"]
                # if dynamic_qrs:
                #     # ... qr_service.get_qr_by_short_id(...) ...
                #     # ... qr_service.update_scan_statistics(...) ...
            else:
                logger.info("No QR codes found, skipping some ORM warmup.")
                # Old test QR creation code also needs full qr_service instance.
                # logger.info("No QR codes found, creating test QRs for initialization...")
                # ... qr_service.create_static_qr(...) ...
                # ... qr_service.create_dynamic_qr(...) ...
                # ... qr_code_repo.delete(...) ...

            logger.info("Warming up error handling code paths (conceptual).")
            
        except Exception as e:
            logger.warning(f"Lifespan pre-initialization (repo warmup) operation failed: {e}")
    except Exception as e:
        logger.warning(f"Lifespan pre-initialization (DB setup) failed: {e}")
    finally:
        if db is not None:
            db.close()
            logger.info("Lifespan pre-initialization DB session closed")

    init_duration = (datetime.now(timezone.utc) - start_time).total_seconds() # Changed UTC
    logger.info(f"Application startup complete in {init_duration:.2f}s, ready to handle requests")

    yield  # Application runs here

    logger.info("Application shutting down...")
    try:
        logger.info("Cleaning up temp files...")
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
    logger.error(f"HTTP error: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
            "timestamp": datetime.now(timezone.utc).isoformat(), # Changed UTC
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": jsonable_encoder(exc.errors()),
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "path": request.url.path,
            "method": request.method,
            "timestamp": datetime.now(timezone.utc).isoformat(), # Changed UTC
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
    )


@app.exception_handler(QRCodeNotFoundError)
async def qr_not_found_exception_handler(
    request: Request, exc: QRCodeNotFoundError
) -> JSONResponse:
    logger.error(f"QR code not found: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "detail": str(exc),
            "status_code": status.HTTP_404_NOT_FOUND,
            "path": request.url.path,
            "method": request.method,
            "timestamp": datetime.now(timezone.utc).isoformat(), # Changed UTC
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
    )


@app.exception_handler(InvalidQRTypeError)
async def invalid_qr_type_exception_handler(
    request: Request, exc: InvalidQRTypeError
) -> JSONResponse:
    logger.error(f"Invalid QR type: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": str(exc),
            "status_code": status.HTTP_400_BAD_REQUEST,
            "path": request.url.path,
            "method": request.method,
            "timestamp": datetime.now(timezone.utc).isoformat(), # Changed UTC
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
    )


@app.exception_handler(QRCodeValidationError)
async def qr_validation_exception_handler(
    request: Request, exc: QRCodeValidationError
) -> JSONResponse:
    logger.error(f"QR code validation error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": str(exc),
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "path": request.url.path,
            "method": request.method,
            "timestamp": datetime.now(timezone.utc).isoformat(), # Changed UTC
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
    )


@app.exception_handler(RedirectURLError)
async def redirect_url_exception_handler(
    request: Request, exc: RedirectURLError
) -> JSONResponse:
    logger.error(f"Redirect URL error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": str(exc),
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "path": request.url.path,
            "method": request.method,
            "timestamp": datetime.now(timezone.utc).isoformat(), # Changed UTC
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
    )


@app.exception_handler(ResourceConflictError)
async def resource_conflict_exception_handler(
    request: Request, exc: ResourceConflictError
) -> JSONResponse:
    logger.error(f"Resource conflict error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "detail": str(exc),
            "status_code": status.HTTP_409_CONFLICT,
            "path": request.url.path,
            "method": request.method,
            "timestamp": datetime.now(timezone.utc).isoformat(), # Changed UTC
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
    )


@app.exception_handler(DatabaseError)
async def database_exception_handler(
    request: Request, exc: DatabaseError
) -> JSONResponse:
    logger.error(f"Database error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": str(exc),
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "path": request.url.path,
            "method": request.method,
            "timestamp": datetime.now(timezone.utc).isoformat(), # Changed UTC
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    logger.exception(f"SQLAlchemy error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Database error occurred",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "path": request.url.path,
            "method": request.method,
            "timestamp": datetime.now(timezone.utc).isoformat(), # Changed UTC
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    logger.exception(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "path": request.url.path,
            "method": request.method,
            "timestamp": datetime.now(timezone.utc).isoformat(), # Changed UTC
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

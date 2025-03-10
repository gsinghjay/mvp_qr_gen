"""
Main FastAPI application module for the QR code generator.
"""

import importlib
import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime

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

from .core.config import settings
from .core.exceptions import (
    AppBaseException,
    QRCodeNotFoundError,
    QRCodeValidationError,
    DatabaseError,
    InvalidQRTypeError,
    RedirectURLError,
    ResourceConflictError,
    RateLimitExceededError,
    ServiceUnavailableError,
)
from .database import init_db
from .middleware.logging import LoggingMiddleware
from .middleware.metrics import MetricsMiddleware
from .middleware.security import create_security_headers_middleware, create_cors_middleware, create_trusted_hosts_middleware
from .routers import routers

# Configure logging
logger = logging.getLogger(__name__)

# Configure static files - ensure correct directory in Docker context
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app/static")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for FastAPI application."""
    # Startup
    init_db()
    logger.info("Database initialized")
    yield
    # Shutdown (if needed)


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: The configured FastAPI application
    """
    # Create FastAPI app with lifespan
    app = FastAPI(
        title="QR Code Generator API",
        description="API for generating and managing QR codes",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        root_path="",  # Ensure root path is empty for Traefik
        lifespan=lifespan,
    )

    # Apply middleware directly - order is important (last added = first executed)
    
    # Logging should be last in chain (first to execute) to capture accurate timing
    if settings.ENABLE_LOGGING:
        app.add_middleware(LoggingMiddleware)
        logger.info("Initialized LoggingMiddleware")

    # Metrics collection
    if settings.ENABLE_METRICS:
        app.add_middleware(MetricsMiddleware)
        logger.info("Initialized MetricsMiddleware")
    
    # Security headers
    create_security_headers_middleware(app)
    logger.info("Initialized security headers middleware")
    
    # CORS - Note: In production, Traefik handles CORS, this is for development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=settings.CORS_HEADERS,
    )
    logger.info("Initialized CORS middleware")
    
    # Trusted hosts - Note: In production, Traefik handles host validation
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.TRUSTED_HOSTS,
    )
    logger.info("Initialized TrustedHost middleware")
    
    # GZip compression should be first in chain (last to execute)
    if settings.ENABLE_GZIP:
        app.add_middleware(
            GZipMiddleware,
            minimum_size=settings.GZIP_MIN_SIZE,
        )
        logger.info("Initialized GZip middleware")

    # Include all routers
    for router in routers:
        app.include_router(router)
    
    return app


# Create the application
app = create_app()

# Add middleware to force HTTPS for static files
@app.middleware("http")
async def force_https_static(request: Request, call_next):
    """Force HTTPS for static file URLs."""
    response = await call_next(request)
    if request.url.path.startswith("/static/"):
        response.headers["Content-Security-Policy"] = "upgrade-insecure-requests"
    return response


# Mount static files with HTTPS configuration
app.mount("/static", StaticFiles(directory=STATIC_DIR, html=True), name="static")

# Load environment variables
TRUSTED_HOSTS = os.getenv("TRUSTED_HOSTS", "localhost").split(",")


# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with detailed error messages."""
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(
            {
                "detail": exc.detail,
                "status_code": exc.status_code,
                "path": request.url.path,
            }
        ),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed error information."""
    # Check if this is a JSON decode error
    if len(exc.errors()) == 1 and exc.errors()[0]["type"] == "json_invalid":
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=jsonable_encoder(
                {
                    "detail": "Invalid JSON format",
                    "path": request.url.path,
                    "method": request.method,
                }
            ),
        )

    # For other validation errors, return 422 with detailed error information
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder(
            {
                "detail": exc.errors(),
                "body": exc.body,
                "path": request.url.path,
                "method": request.method,
            }
        ),
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError with proper error details."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder(
            {
                "detail": [{"loc": ["body"], "msg": str(exc), "type": "value_error"}],
                "path": request.url.path,
                "method": request.method,
            }
        ),
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle database errors safely without exposing internal details."""
    logger.error(f"Database error: {str(exc)}", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=jsonable_encoder(
            {
                "detail": "Database error occurred",
                "path": request.url.path,
                "method": request.method,
            }
        ),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors with proper logging."""
    logger.error("Unexpected error occurred", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=jsonable_encoder(
            {
                "detail": "Internal server error",
                "path": request.url.path,
                "method": request.method,
            }
        ),
    )


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add a unique request ID to each request."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(AppBaseException)
async def app_exception_handler(request: Request, exc: AppBaseException):
    """
    Handle all application-specific exceptions with a consistent response format.
    
    This handler processes all exceptions that inherit from AppBaseException,
    providing a consistent response format with status code, detail message,
    request path, timestamp, and request ID.
    
    Args:
        request: The request that caused the exception
        exc: The exception instance
        
    Returns:
        JSONResponse with error details
    """
    request_id = request.state.request_id if hasattr(request.state, "request_id") else None
    
    return JSONResponse(
        status_code=exc.status_code,
        headers=exc.headers,
        content=jsonable_encoder(
            {
                "detail": exc.detail,
                "status_code": exc.status_code,
                "path": request.url.path,
                "method": request.method,
                "timestamp": datetime.now(UTC).isoformat(),
                "request_id": request_id,
            }
        ),
    )


@app.exception_handler(QRCodeNotFoundError)
async def qr_code_not_found_exception_handler(request: Request, exc: QRCodeNotFoundError):
    """
    Handle QRCodeNotFoundError with a 404 response.
    
    Args:
        request: The request that caused the exception
        exc: The exception instance
        
    Returns:
        JSONResponse with error details
    """
    request_id = request.state.request_id if hasattr(request.state, "request_id") else None
    
    return JSONResponse(
        status_code=exc.status_code,
        headers=exc.headers,
        content=jsonable_encoder(
            {
                "detail": exc.detail,
                "status_code": exc.status_code,
                "path": request.url.path,
                "method": request.method,
                "timestamp": datetime.now(UTC).isoformat(),
                "request_id": request_id,
            }
        ),
    )


@app.exception_handler(QRCodeValidationError)
async def qr_code_validation_exception_handler(request: Request, exc: QRCodeValidationError):
    """
    Handle QRCodeValidationError with a 422 response.
    
    Args:
        request: The request that caused the exception
        exc: The exception instance
        
    Returns:
        JSONResponse with error details
    """
    request_id = request.state.request_id if hasattr(request.state, "request_id") else None
    
    return JSONResponse(
        status_code=exc.status_code,
        headers=exc.headers,
        content=jsonable_encoder(
            {
                "detail": exc.detail,
                "status_code": exc.status_code,
                "path": request.url.path,
                "method": request.method,
                "timestamp": datetime.now(UTC).isoformat(),
                "request_id": request_id,
            }
        ),
    )


@app.exception_handler(DatabaseError)
async def database_exception_handler(request: Request, exc: DatabaseError):
    """
    Handle DatabaseError with a 500 response.
    
    Args:
        request: The request that caused the exception
        exc: The exception instance
        
    Returns:
        JSONResponse with error details
    """
    request_id = request.state.request_id if hasattr(request.state, "request_id") else None
    logger.error(f"Database error: {str(exc.detail)}", exc_info=True)
    
    return JSONResponse(
        status_code=exc.status_code,
        headers=exc.headers,
        content=jsonable_encoder(
            {
                "detail": exc.detail,
                "status_code": exc.status_code,
                "path": request.url.path,
                "method": request.method,
                "timestamp": datetime.now(UTC).isoformat(),
                "request_id": request_id,
            }
        ),
    )


@app.exception_handler(InvalidQRTypeError)
async def invalid_qr_type_exception_handler(request: Request, exc: InvalidQRTypeError):
    """
    Handle InvalidQRTypeError with a 400 response.
    
    Args:
        request: The request that caused the exception
        exc: The exception instance
        
    Returns:
        JSONResponse with error details
    """
    request_id = request.state.request_id if hasattr(request.state, "request_id") else None
    
    return JSONResponse(
        status_code=exc.status_code,
        headers=exc.headers,
        content=jsonable_encoder(
            {
                "detail": exc.detail,
                "status_code": exc.status_code,
                "path": request.url.path,
                "method": request.method,
                "timestamp": datetime.now(UTC).isoformat(),
                "request_id": request_id,
            }
        ),
    )


@app.exception_handler(RedirectURLError)
async def redirect_url_exception_handler(request: Request, exc: RedirectURLError):
    """
    Handle RedirectURLError with a 422 response.
    
    Args:
        request: The request that caused the exception
        exc: The exception instance
        
    Returns:
        JSONResponse with error details
    """
    request_id = request.state.request_id if hasattr(request.state, "request_id") else None
    
    return JSONResponse(
        status_code=exc.status_code,
        headers=exc.headers,
        content=jsonable_encoder(
            {
                "detail": exc.detail,
                "status_code": exc.status_code,
                "path": request.url.path,
                "method": request.method,
                "timestamp": datetime.now(UTC).isoformat(),
                "request_id": request_id,
            }
        ),
    )


@app.exception_handler(ResourceConflictError)
async def resource_conflict_exception_handler(request: Request, exc: ResourceConflictError):
    """
    Handle ResourceConflictError with a 409 response.
    
    Args:
        request: The request that caused the exception
        exc: The exception instance
        
    Returns:
        JSONResponse with error details
    """
    request_id = request.state.request_id if hasattr(request.state, "request_id") else None
    
    return JSONResponse(
        status_code=exc.status_code,
        headers=exc.headers,
        content=jsonable_encoder(
            {
                "detail": exc.detail,
                "status_code": exc.status_code,
                "path": request.url.path,
                "method": request.method,
                "timestamp": datetime.now(UTC).isoformat(),
                "request_id": request_id,
            }
        ),
    )


@app.exception_handler(RateLimitExceededError)
async def rate_limit_exception_handler(request: Request, exc: RateLimitExceededError):
    """
    Handle RateLimitExceededError with a 429 response.
    
    Args:
        request: The request that caused the exception
        exc: The exception instance
        
    Returns:
        JSONResponse with error details
    """
    request_id = request.state.request_id if hasattr(request.state, "request_id") else None
    
    return JSONResponse(
        status_code=exc.status_code,
        headers=exc.headers,
        content=jsonable_encoder(
            {
                "detail": exc.detail,
                "status_code": exc.status_code,
                "path": request.url.path,
                "method": request.method,
                "timestamp": datetime.now(UTC).isoformat(),
                "request_id": request_id,
            }
        ),
    )


@app.exception_handler(ServiceUnavailableError)
async def service_unavailable_exception_handler(request: Request, exc: ServiceUnavailableError):
    """
    Handle ServiceUnavailableError with a 503 response.
    
    Args:
        request: The request that caused the exception
        exc: The exception instance
        
    Returns:
        JSONResponse with error details
    """
    request_id = request.state.request_id if hasattr(request.state, "request_id") else None
    logger.error(f"Service unavailable: {str(exc.detail)}", exc_info=True)
    
    return JSONResponse(
        status_code=exc.status_code,
        headers=exc.headers,
        content=jsonable_encoder(
            {
                "detail": exc.detail,
                "status_code": exc.status_code,
                "path": request.url.path,
                "method": request.method,
                "timestamp": datetime.now(UTC).isoformat(),
                "request_id": request_id,
            }
        ),
    )


"""
@app.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    db: Session = Depends(get_db_with_logging)
):
    # This endpoint has been moved to routers/web/pages.py
    try:
        # Get total QR code count for the dashboard
        total_qr_codes = db.query(QRCode).count()
        recent_qr_codes = db.query(QRCode).order_by(QRCode.created_at.desc()).limit(5).all()
        
        return templates.TemplateResponse(
            name="index.html",
            context={
                "request": request,  # Required by Jinja2Templates
                "total_qr_codes": total_qr_codes,
                "recent_qr_codes": recent_qr_codes,
            }
        )
    except SQLAlchemyError as e:
        logger.error("Database error in home page", extra={"error": str(e)})
        return templates.TemplateResponse(
            name="index.html",
            context={
                "request": request,  # Required by Jinja2Templates
                "total_qr_codes": 0,
                "recent_qr_codes": [],
                "error": "Unable to load QR code data"
            },
            status_code=500
        )
"""

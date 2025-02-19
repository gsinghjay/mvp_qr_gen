"""
Main FastAPI application module for the QR code generator.
"""
from fastapi import FastAPI, Depends, HTTPException, Query, Response, Request, status, BackgroundTasks, UploadFile, File
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
import logging
import uuid
import json
import asyncio
import os
import importlib
from typing import Optional, Dict, Any
from urllib.parse import urlparse
from sqlalchemy import update
from json.decoder import JSONDecodeError
from contextlib import asynccontextmanager
from PIL import Image
from io import BytesIO

from .core.config import settings, MIDDLEWARE_CONFIG
from .database import init_db, SessionLocal
from .models import QRCode
from .schemas import QRCodeCreate, QRCodeUpdate, QRCodeResponse, QRCodeList
from .qr_service import QRCodeService
from .middleware import logging as logging_middleware
from .middleware import metrics as metrics_middleware
from .middleware import security as security_middleware

# Configure logging
logger = logging.getLogger(__name__)

def setup_middleware(app: FastAPI) -> None:
    """
    Set up middleware in the correct order based on configuration.
    Middleware is added in reverse order (last added = first executed).
    """
    for middleware in reversed(MIDDLEWARE_CONFIG):
        if not middleware["enabled"]:
            continue
            
        try:
            middleware_class = middleware["class"]
            
            # Handle built-in FastAPI middleware
            if middleware_class == "fastapi.middleware.gzip.GZipMiddleware":
                app.add_middleware(
                    GZipMiddleware,
                    minimum_size=middleware["kwargs"].get("minimum_size", 1000)
                )
            elif middleware_class == "app.middleware.create_cors_middleware":
                app.add_middleware(
                    CORSMiddleware,
                    allow_origins=settings.CORS_ORIGINS,
                    allow_credentials=True,
                    allow_methods=["*"],
                    allow_headers=settings.CORS_HEADERS,
                )
            elif middleware_class == "app.middleware.create_trusted_hosts_middleware":
                app.add_middleware(
                    TrustedHostMiddleware,
                    allowed_hosts=settings.TRUSTED_HOSTS,
                )
            # Handle decorator-based middleware
            elif middleware.get("is_decorator"):
                module_path, function_name = middleware_class.rsplit(".", 1)
                module = importlib.import_module(module_path)
                middleware_func = getattr(module, function_name)
                middleware_func(app)  # Apply the decorator middleware
            # Handle class-based middleware
            elif middleware_class == "app.middleware.MetricsMiddleware":
                app.add_middleware(metrics_middleware.MetricsMiddleware)
            elif middleware_class == "app.middleware.LoggingMiddleware":
                app.add_middleware(logging_middleware.LoggingMiddleware)
            
            logger.info(
                f"Initialized middleware: {middleware_class}",
                extra={
                    "enabled": middleware["enabled"],
                    "is_decorator": middleware.get("is_decorator", False),
                    "args": middleware.get("args", []),
                    "kwargs": middleware.get("kwargs", {})
                }
            )
        except Exception as e:
            logger.error(f"Failed to initialize middleware {middleware_class}: {str(e)}")
            raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for FastAPI application."""
    # Startup
    init_db()
    logger.info("Database initialized")
    yield
    # Shutdown (if needed)

# Create FastAPI app with lifespan
app = FastAPI(
    title="QR Code Generator API",
    description="API for generating and managing QR codes",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    root_path=""  # Ensure root path is empty for Traefik
)

# Initialize middleware
setup_middleware(app)

# Configure templates with context processors
def get_base_template_context(request: Request) -> Dict[str, Any]:
    """
    Get base context for all templates.
    Includes common data like app version, environment info, etc.
    """
    return {
        "request": request,  # Required by Jinja2Templates
        "app_version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "current_year": datetime.now().year,
        "api_base_url": "/api/v1"
    }

templates = Jinja2Templates(
    directory="app/templates",
    context_processors=[get_base_template_context],
)

# Configure static files - ensure correct directory in Docker context
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app/static")
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app/templates")

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Load environment variables
TRUSTED_HOSTS = os.getenv("TRUSTED_HOSTS", "localhost").split(",")

# Initialize QR service
qr_service = QRCodeService()

# Database session dependency with error handling
def get_db_with_logging():
    """Get database session with proper error handling and logging."""
    db = None
    try:
        db = SessionLocal()
        yield db
    except Exception as e:
        logger.exception("Database session error", extra={"error": str(e)})
        if db:
            db.rollback()
        raise
    finally:
        if db:
            db.close()

# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with detailed error messages."""
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder({
            "detail": exc.detail,
            "status_code": exc.status_code,
            "path": request.url.path
        }),
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed error information."""
    # Check if this is a JSON decode error
    if len(exc.errors()) == 1 and exc.errors()[0]["type"] == "json_invalid":
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=jsonable_encoder({
                "detail": "Invalid JSON format",
                "path": request.url.path,
                "method": request.method
            }),
        )
    
    # For other validation errors, return 422 with detailed error information
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({
            "detail": exc.errors(),
            "body": exc.body,
            "path": request.url.path,
            "method": request.method
        }),
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError with proper error details."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({
            "detail": [{
                "loc": ["body"],
                "msg": str(exc),
                "type": "value_error"
            }],
            "path": request.url.path,
            "method": request.method
        }),
    )

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle database errors safely without exposing internal details."""
    logger.error(f"Database error: {str(exc)}", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=jsonable_encoder({
            "detail": "Database error occurred",
            "path": request.url.path,
            "method": request.method
        }),
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors with proper logging."""
    logger.error("Unexpected error occurred", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=jsonable_encoder({
            "detail": "Internal server error",
            "path": request.url.path,
            "method": request.method
        }),
    )

@app.get("/api/v1/qr", response_model=QRCodeList)
async def list_qr_codes(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    qr_type: Optional[str] = Query(default=None, pattern="^(static|dynamic)$"),
    db: Session = Depends(get_db_with_logging)
):
    """List QR codes with pagination and optional filtering."""
    try:
        query = db.query(QRCode)
        if qr_type:
            query = query.filter(QRCode.qr_type == qr_type)
        
        total = query.count()
        qr_codes = query.order_by(QRCode.created_at.desc()).offset(skip).limit(limit).all()
        
        response = QRCodeList(
            items=qr_codes,
            total=total,
            page=skip // limit + 1,
            page_size=limit
        )
        
        return response
    except SQLAlchemyError as e:
        logger.error("Database error listing QR codes", extra={"error": str(e)})
        raise HTTPException(
            status_code=500,
            detail="Error listing QR codes: database error"
        )
    except Exception as e:
        logger.exception("Unexpected error listing QR codes")
        raise HTTPException(
            status_code=500,
            detail="Error listing QR codes: unexpected error"
        )

@app.post("/api/v1/qr/static", response_model=QRCodeResponse)
async def create_static_qr(
    data: QRCodeCreate,
    db: Session = Depends(get_db_with_logging)
):
    """Create a new static QR code."""
    try:
        if data.redirect_url:
            raise HTTPException(
                status_code=422,
                detail="Static QR codes cannot have a redirect URL"
            )
            
        qr = QRCode(
            content=data.content,
            qr_type="static",
            fill_color=data.fill_color,
            back_color=data.back_color,
            size=data.size,
            border=data.border,
            created_at=datetime.now(timezone.utc)
        )
        db.add(qr)
        db.commit()
        db.refresh(qr)
        
        logger.info("Created static QR code", extra={"qr_id": qr.id})
        return qr
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("Database error creating static QR code", extra={"error": str(e)})
        raise HTTPException(
            status_code=500,
            detail="Error creating QR code: database error"
        )
    except Exception as e:
        db.rollback()
        logger.exception("Unexpected error creating static QR code")
        raise HTTPException(
            status_code=500,
            detail="Error creating QR code: unexpected error"
        )

@app.post("/api/v1/qr/dynamic", response_model=QRCodeResponse)
async def create_dynamic_qr(
    data: QRCodeCreate,
    db: Session = Depends(get_db_with_logging)
):
    """Create a new dynamic QR code."""
    try:
        if not data.redirect_url:
            raise HTTPException(
                status_code=422,
                detail="Dynamic QR codes must have a redirect URL"
            )
            
        # Generate a short unique identifier for the redirect path
        short_id = str(uuid.uuid4())[:8]
        qr = QRCode(
            content=f"/r/{short_id}",
            qr_type="dynamic",
            redirect_url=str(data.redirect_url),
            fill_color=data.fill_color,
            back_color=data.back_color,
            size=data.size,
            border=data.border,
            created_at=datetime.now(timezone.utc)
        )
        db.add(qr)
        db.commit()
        db.refresh(qr)
        
        logger.info(f"Created dynamic QR code with ID: {qr.id}")
        return qr
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating dynamic QR code: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating QR code")

@app.get("/r/{short_id}")
async def redirect_qr(
    short_id: str,
    request: Request,
    db: Session = Depends(get_db_with_logging)
):
    """Redirect endpoint for dynamic QR codes."""
    try:
        qr = db.query(QRCode).filter(QRCode.content == f"/r/{short_id}").first()
        if not qr:
            raise HTTPException(status_code=404, detail="QR code not found")
        
        if not qr.redirect_url:
            raise HTTPException(status_code=400, detail="No redirect URL set")
        
        # Validate redirect URL
        try:
            parsed_url = urlparse(str(qr.redirect_url))
            if not parsed_url.scheme or not parsed_url.netloc:
                raise HTTPException(status_code=400, detail="Invalid redirect URL")
        except Exception as e:
            logger.error(f"URL validation error: {str(e)}")
            raise HTTPException(status_code=400, detail="Invalid redirect URL")
        
        # Update scan statistics atomically using SQL update
        try:
            current_time = datetime.now(timezone.utc)
            stmt = update(QRCode).where(QRCode.id == qr.id).values(
                scan_count=QRCode.scan_count + 1,
                last_scan_at=current_time
            )
            db.execute(stmt)
            db.commit()
            
            # Refresh the QR code object to get updated values
            db.refresh(qr)
            
        except Exception as e:
            logger.error(f"Error updating scan statistics: {str(e)}")
            db.rollback()
            # Continue with redirect even if statistics update fails
        
        # Get client IP from various possible headers
        client_ip = request.headers.get("X-Real-IP") or \
                    request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or \
                    (request.client.host if request.client else "unknown")
        
        # Log scan event with metadata
        scan_metadata = {
            "qr_id": qr.id,
            "timestamp": current_time.isoformat(),
            "ip": client_ip,
            "user_agent": request.headers.get("user-agent"),
            "referer": request.headers.get("referer"),
        }
        logger.info(f"QR code scan: {json.dumps(scan_metadata)}")
        
        # Ensure HTTPS for production redirects
        redirect_url = str(qr.redirect_url)
        if settings.ENVIRONMENT == "production" and redirect_url.startswith("http://"):
            redirect_url = "https://" + redirect_url[7:]
        
        return RedirectResponse(
            url=redirect_url,
            status_code=status.HTTP_302_FOUND,
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing redirect: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing redirect")

@app.put("/api/v1/qr/{qr_id}", response_model=QRCodeResponse)
async def update_qr(
    qr_id: str,
    data: QRCodeUpdate,
    db: Session = Depends(get_db_with_logging)
):
    """Update a dynamic QR code's redirect URL."""
    try:
        qr = db.query(QRCode).filter(QRCode.id == qr_id).first()
        if not qr:
            raise HTTPException(status_code=404, detail="QR code not found")
        
        if qr.qr_type != "dynamic":
            raise HTTPException(status_code=400, detail="Cannot update static QR code")
        
        # Validate and update the redirect URL
        if not data.redirect_url:
            raise HTTPException(status_code=422, detail="Redirect URL is required")
        
        try:
            qr.redirect_url = str(data.redirect_url)
            # Update last_scan_at manually since we removed onupdate
            qr.last_scan_at = datetime.now(timezone.utc)
            db.add(qr)  # Explicitly add the modified object
            db.commit()
            db.refresh(qr)
            
            logger.info(f"Updated QR code {qr_id} with new redirect URL: {data.redirect_url}")
            return qr
            
        except Exception as e:
            db.rollback()
            logger.error(f"Database error updating QR code: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Database error while updating QR code"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating QR code: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Unexpected error while updating QR code"
        )

@app.get("/api/v1/qr/{qr_id}/image")
async def get_qr_image(
    qr_id: str,
    image_format: str = Query(default="png", pattern="^(png|jpeg|jpg|svg|webp)$"),
    image_quality: Optional[int] = Query(default=None, ge=1, le=100),
    db: Session = Depends(get_db_with_logging)
):
    """Get QR code image by ID."""
    try:
        qr = db.query(QRCode).filter(QRCode.id == qr_id).first()
        if not qr:
            raise HTTPException(status_code=404, detail="QR code not found")
        
        # Generate QR code
        return qr_service.generate_qr(
            data=qr.content,
            size=qr.size,
            border=qr.border,
            fill_color=qr.fill_color,
            back_color=qr.back_color,
            image_format=image_format,
            image_quality=image_quality
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating QR code image: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating QR code image")

@app.get("/api/v1/qr/{qr_id}", response_model=QRCodeResponse)
async def get_qr(
    qr_id: str,
    db: Session = Depends(get_db_with_logging)
):
    """Get QR code data by ID."""
    try:
        qr = db.query(QRCode).filter(QRCode.id == qr_id).first()
        if not qr:
            raise HTTPException(status_code=404, detail="QR code not found")
        return qr
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving QR code: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving QR code")

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add X-Request-ID header to all responses."""
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

@app.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    db: Session = Depends(get_db_with_logging)
):
    """
    Render the home page template with dynamic data.
    """
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
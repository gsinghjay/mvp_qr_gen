"""
Enhanced logging middleware for FastAPI application.
Implements structured JSON logging with proper rotation and level configuration.
Note: Complements Traefik's access logs by providing detailed application-level logging.
While Traefik handles edge-level access logs, this middleware captures internal application state and processing details.
"""
import json
import logging
import logging.handlers
import time
from pathlib import Path
from typing import Callable, Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from ..core.config import settings

# Constants
LOG_DIR = "/logs/api"
ACCESS_LOG = "access.log"
ERROR_LOG = "errors.log"
PERFORMANCE_LOG = "performance.log"
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5

# Configure JSON formatter for structured logging
class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S.%03dZ"),
            "level": record.levelname,
            "message": record.getMessage(),
            "source": "api_middleware",
            "type": "application_log"
        }
        # Add extra fields from record
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        # Add exception info if present
        if record.exc_info:
            log_data["error"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
        return json.dumps(log_data)

def setup_logging():
    """Configure logging with multiple handlers for different log types."""
    # Create logs directory
    log_dir = Path(LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create formatters
    json_formatter = JSONFormatter()
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Create and configure handlers
    handlers = {
        'access': logging.handlers.RotatingFileHandler(
            log_dir / ACCESS_LOG,
            maxBytes=MAX_LOG_SIZE,
            backupCount=LOG_BACKUP_COUNT
        ),
        'error': logging.handlers.RotatingFileHandler(
            log_dir / ERROR_LOG,
            maxBytes=MAX_LOG_SIZE,
            backupCount=LOG_BACKUP_COUNT
        ),
        'performance': logging.handlers.RotatingFileHandler(
            log_dir / PERFORMANCE_LOG,
            maxBytes=MAX_LOG_SIZE,
            backupCount=LOG_BACKUP_COUNT
        ),
        'console': logging.StreamHandler()
    }

    # Set formatters and levels
    for name, handler in handlers.items():
        handler.setFormatter(json_formatter if name != 'console' else console_formatter)
        handler.setLevel(logging.INFO)

    # Create specialized loggers
    loggers = {
        'access': logging.getLogger('api.access'),
        'error': logging.getLogger('api.error'),
        'performance': logging.getLogger('api.performance')
    }

    # Configure specialized loggers
    for name, logger in loggers.items():
        logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
        logger.addHandler(handlers[name])
        logger.addHandler(handlers['console'])
        logger.propagate = False

    return loggers

# Initialize loggers
loggers = setup_logging()

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start timer for request duration using perf_counter for more precision
        start_time = time.perf_counter()
        
        # Extract correlation IDs and request metadata
        request_id = request.headers.get("X-Request-ID", "")
        trace_id = request.headers.get("X-Trace-ID", "")  # For distributed tracing
        client_ip = request.headers.get("X-Real-IP") or \
                   request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or \
                   request.client.host if request.client else "unknown"
        
        # Prepare common log data
        log_data = {
            "request_id": request_id,
            "trace_id": trace_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "client_ip": client_ip,
            "user_agent": request.headers.get("user-agent"),
            "referer": request.headers.get("referer"),
            "host": request.headers.get("host"),
            "protocol": request.headers.get("x-forwarded-proto", "http"),
        }
        
        # Log request start
        loggers['access'].info(
            "Request started",
            extra={
                **log_data,
                "event": "request_start"
            }
        )
        
        # Process request and capture response
        try:
            response = await call_next(request)
            duration = time.perf_counter() - start_time
            
            # Add response data to log
            response_data = {
                **log_data,
                "status_code": response.status_code,
                "duration": f"{duration:.4f}",
                "content_length": response.headers.get("content-length"),
                "content_type": response.headers.get("content-type"),
                "event": "request_complete"
            }
            
            # Log successful response
            loggers['access'].info(
                "Request completed",
                extra=response_data
            )
            
            # Log performance metrics
            loggers['performance'].info(
                "Request performance",
                extra={
                    **log_data,
                    "duration": f"{duration:.4f}",
                    "status_code": response.status_code,
                    "event": "request_performance"
                }
            )
            
            return response
            
        except Exception as e:
            # Calculate duration even for failed requests
            duration = time.perf_counter() - start_time
            
            # Prepare error log data
            error_data = {
                **log_data,
                "error": str(e),
                "error_type": type(e).__name__,
                "duration": f"{duration:.4f}",
                "event": "request_error"
            }
            
            # Log error in both error and access logs
            loggers['error'].error(
                "Request failed",
                extra=error_data,
                exc_info=True  # Include stack trace
            )
            
            loggers['access'].error(
                "Request failed",
                extra=error_data
            )
            
            # Log performance for failed requests too
            loggers['performance'].info(
                "Failed request performance",
                extra={
                    **log_data,
                    "duration": f"{duration:.4f}",
                    "error": str(e),
                    "event": "request_error_performance"
                }
            )
            
            raise 
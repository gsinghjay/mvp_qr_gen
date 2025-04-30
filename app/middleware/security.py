"""
Enhanced security middleware for FastAPI application.
Implements security headers and request validation.

Note: Network-level security (IP filtering, TLS, CORS for production) is handled by Traefik.
This module provides application-level security measures only.
"""

import logging
from typing import List

from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import RequestResponseEndpoint

logger = logging.getLogger(__name__)

def create_security_headers_middleware(app):
    """
    Create security headers middleware using FastAPI's decorator pattern.
    
    This complements Traefik's security headers by adding application-specific headers
    that may need to be dynamically generated or are best set at the application level.
    """
    @app.middleware("http")
    async def security_headers_middleware(request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        
        # Add security headers not handled by Traefik or that need dynamic values
        headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
        }
        
        # Add CSP for static files
        if request.url.path.startswith("/static/"):
            headers["Content-Security-Policy"] = "upgrade-insecure-requests"
        
        # Add HSTS in production only - safely check environment with fallback
        try:
            # Get environment from settings if available, otherwise assume production for safety
            environment = getattr(request.app.state, "settings", None)
            if environment and hasattr(environment, "ENVIRONMENT"):
                is_production = environment.ENVIRONMENT == "production"
            else:
                # Default to production behavior if we can't determine environment
                is_production = True
                logger.warning("Could not determine environment from app state, defaulting to production security settings")
                
            if is_production:
                headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
                logger.debug("Added HSTS header for production environment")
        except Exception as e:
            # On any error, use a safer default (add HSTS)
            headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            logger.warning(f"Error determining environment, defaulting to HSTS header: {str(e)}")
            
        response.headers.update(headers)
        return response

    return security_headers_middleware

def create_cors_middleware(allowed_origins: List[str]) -> CORSMiddleware:
    """
    Create CORS middleware for development environments only. 
    
    In production, CORS is handled by Traefik.
    """
    return CORSMiddleware(
        app=None,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

def create_trusted_hosts_middleware(allowed_hosts: List[str]) -> TrustedHostMiddleware:
    """
    Create TrustedHost middleware for development environments only.
    
    In production, host validation is handled by Traefik's routing rules.
    """
    return TrustedHostMiddleware(
        app=None,
        allowed_hosts=allowed_hosts,
    )

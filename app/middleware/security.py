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
    
    As part of Phase III (Security Header Consolidation), standard security headers
    have been moved to Traefik configuration as the single source of truth.
    
    This middleware now only handles application-specific headers that need to be
    dynamically generated or are contextual to specific requests.
    """
    @app.middleware("http")
    async def security_headers_middleware(request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        
        # Initialize empty headers dictionary
        headers = {}
        
        # Add CSP for static files - this is a dynamic, path-specific header
        # that makes sense to keep at the application level
        if request.url.path.startswith("/static/"):
            headers["Content-Security-Policy"] = "upgrade-insecure-requests"
        
        # Standard security headers removed and now managed by Traefik:
        # - X-Content-Type-Options
        # - X-Frame-Options
        # - X-XSS-Protection
        # - Strict-Transport-Security (HSTS)
            
        # Only update headers if we have any to add
        if headers:
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

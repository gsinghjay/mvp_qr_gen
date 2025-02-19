"""
Enhanced security middleware for FastAPI application.
Implements security headers and request validation.
Note: Main security features are handled by Traefik, this is for additional security measures.
"""
from typing import Callable, List
from fastapi import Request, Response
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware
import os

def create_security_headers_middleware(app):
    """
    Create security headers middleware using FastAPI's decorator pattern.
    Note: These are additional headers not handled by Traefik.
    """
    @app.middleware("http")
    async def security_headers_middleware(request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers not handled by Traefik
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Only add HSTS header in production
        if os.getenv("ENVIRONMENT", "development") == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response
    
    return security_headers_middleware

def create_cors_middleware(allowed_origins: List[str]):
    """
    Create CORS middleware with the specified allowed origins.
    Note: In production, Traefik handles CORS, this is for development.
    """
    return CORSMiddleware(
        app=None,  # Will be set by FastAPI
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

def create_trusted_hosts_middleware(allowed_hosts: List[str]):
    """
    Create TrustedHost middleware with the specified allowed hosts.
    Note: In production, Traefik handles host validation.
    """
    return TrustedHostMiddleware(
        app=None,  # Will be set by FastAPI
        allowed_hosts=allowed_hosts,
    ) 
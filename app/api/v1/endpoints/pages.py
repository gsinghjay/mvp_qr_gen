"""
Router for web page endpoints.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Annotated

from fastapi import APIRouter, Depends, Request, status, Header
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.types import DbSessionDep, QRServiceDep
from app.core.config import settings
from app.core.exceptions import DatabaseError
from app.models import QRCode

# Configure logger
import logging
logger = logging.getLogger("app.web.pages")

# Configure templates with context processors
def get_base_template_context(request: Request) -> dict:
    """
    Get base context for all templates.
    Includes common data like app version, environment info, etc.
    """
    # Force HTTPS for all URLs
    request.scope["scheme"] = "https"

    return {
        "request": request,  # Required by Jinja2Templates
        "app_version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "current_year": datetime.now().year,
        "api_base_url": "/api/v1",
    }

# Configure templates
templates = Jinja2Templates(
    directory=str(settings.TEMPLATES_DIR),
    context_processors=[get_base_template_context],
)

router = APIRouter(
    tags=["pages"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, qr_service: QRServiceDep):
    """
    Render the home page template with dynamic data.
    """
    try:
        # Get dashboard data using the service
        dashboard_data = qr_service.get_dashboard_data()
        
        # Use the new HTMX-based dashboard template
        return templates.TemplateResponse(
            name="pages/dashboard.html",
            context={
                "request": request,  # Required by Jinja2Templates
                "total_qr_codes": dashboard_data["total_qr_codes"],
                "recent_qr_codes": dashboard_data["recent_qr_codes"],
            },
        )
    except DatabaseError as e:
        logger.error("Database error in home page", extra={"error": str(e)})
        return templates.TemplateResponse(
            name="pages/dashboard.html",
            context={
                "request": request,  # Required by Jinja2Templates
                "total_qr_codes": 0,
                "recent_qr_codes": [],
                "error": "Unable to load QR code data",
            },
            status_code=500,
        )


@router.get("/qr-list", response_class=HTMLResponse)
async def qr_list(request: Request, qr_service: QRServiceDep):
    """
    Render the QR code list page with filtering and sorting options.
    """
    try:
        # Get dashboard data using the service to get the total count
        dashboard_data = qr_service.get_dashboard_data()
        
        return templates.TemplateResponse(
            name="pages/qr_list.html",
            context={
                "request": request,
                "total_qr_codes": dashboard_data["total_qr_codes"],
            },
        )
    except DatabaseError as e:
        logger.error("Database error in QR list page", extra={"error": str(e)})
        return templates.TemplateResponse(
            name="pages/qr_list.html",
            context={
                "request": request,
                "total_qr_codes": 0,
                "error": "Unable to load QR code data",
            },
            status_code=500,
        )


@router.get("/qr-create", response_class=HTMLResponse)
async def qr_create(request: Request):
    """
    Render the QR code creation page.
    
    This endpoint displays a form for creating both static and dynamic QR codes,
    with a live preview and download options.
    
    Args:
        request: The FastAPI request object.
        
    Returns:
        HTMLResponse: The rendered QR code creation page.
    """
    try:
        return templates.TemplateResponse(
            name="pages/qr_create.html",
            context={
                "request": request,
                "is_authenticated": True,  # Network-level authentication is now used
            },
        )
    except Exception as e:
        logger.error("Error in QR creation page", extra={"error": str(e)})
        return templates.TemplateResponse(
            name="pages/qr_create.html",
            context={
                "request": request,
                "is_authenticated": True,  # Network-level authentication is now used
                "error": "An error occurred while loading the QR creation page",
            },
            status_code=500,
        )


@router.get("/qr-detail/{qr_id}", response_class=HTMLResponse)
async def qr_detail(
    request: Request, 
    qr_id: str, 
    qr_service: QRServiceDep
):
    """
    Render the QR code detail page.
    
    This endpoint displays detailed information about a specific QR code,
    including its metadata, statistics, and management options.
    
    Args:
        request: The FastAPI request object.
        qr_id: The ID of the QR code to display.
        qr_service: The QR code service.
        
    Returns:
        HTMLResponse: The rendered QR code detail page.
    """
    try:
        # Get the QR code using the service
        qr_code = qr_service.get_qr_by_id(qr_id)
        
        # Convert the QR code model to a dictionary for the template
        qr_data = qr_code.to_dict()
        
        # Add the base URL for the short URL display
        base_url = f"{settings.BASE_URL}/r/"
        
        return templates.TemplateResponse(
            name="pages/qr_detail.html",
            context={
                "request": request,
                "is_authenticated": True,  # Network-level authentication is now used
                "qr": qr_data,
                "base_url": base_url,
            },
        )
    except DatabaseError as e:
        logger.error(f"Database error in QR detail page for {qr_id}", extra={"error": str(e)})
        return templates.TemplateResponse(
            name="pages/qr_detail.html",
            context={
                "request": request,
                "is_authenticated": True,  # Network-level authentication is now used
                "error": "An error occurred while loading the QR code details",
                "qr_id": qr_id,
            },
            status_code=500,
        )
    except Exception as e:
        logger.error(f"Error in QR detail page for {qr_id}", extra={"error": str(e)})
        return templates.TemplateResponse(
            name="pages/qr_detail.html",
            context={
                "request": request,
                "is_authenticated": True,  # Network-level authentication is now used
                "error": "QR code not found",
                "qr_id": qr_id,
            },
            status_code=404,
        ) 


@router.get("/qr/{qr_id}/analytics", response_class=HTMLResponse)
async def qr_analytics_page(
    request: Request, 
    qr_id: str, 
    qr_service: QRServiceDep
):
    """
    Render the QR code analytics page.
    
    This endpoint displays comprehensive analytics data for a specific QR code,
    including scan statistics, device breakdown, and time-series visualizations.
    
    Args:
        request: The FastAPI request object.
        qr_id: The ID of the QR code to display analytics for.
        qr_service: The QR code service.
        
    Returns:
        HTMLResponse: The rendered QR code analytics page.
    """
    try:
        # Get the QR code using the service to fetch basic details
        qr_code = qr_service.get_qr_by_id(qr_id)
        
        # Convert the QR code model to a dictionary for the template
        qr_data = qr_code.to_dict()
        
        # Add the base URL for the short URL display if it's a dynamic QR code
        base_url = f"{settings.BASE_URL}/r/"
        
        return templates.TemplateResponse(
            name="pages/qr_analytics.html",
            context={
                "request": request,
                "is_authenticated": True,  # Network-level authentication is now used
                "qr": qr_data,
                "base_url": base_url,
                "page_title": f"Analytics for {qr_data.get('title', 'QR Code')}",
            },
        )
    except DatabaseError as e:
        logger.error(f"Database error in QR analytics page for {qr_id}", extra={"error": str(e)})
        return templates.TemplateResponse(
            name="pages/qr_analytics.html",
            context={
                "request": request,
                "is_authenticated": True,
                "error": "An error occurred while loading the QR code analytics",
                "qr_id": qr_id,
            },
            status_code=500,
        )
    except Exception as e:
        logger.error(f"Error in QR analytics page for {qr_id}", extra={"error": str(e)})
        return templates.TemplateResponse(
            name="pages/qr_analytics.html",
            context={
                "request": request,
                "is_authenticated": True,
                "error": "QR code not found",
                "qr_id": qr_id,
            },
            status_code=404,
        ) 


@router.get("/qr", response_class=RedirectResponse, include_in_schema=False)
async def redirect_qr_to_qr_list():
    """
    Redirects general /qr path to the main QR list page.
    
    This simplifies the URL structure by ensuring that the /qr path
    (without additional segments) redirects to the full QR list page.
    """
    return RedirectResponse(url="/qr-list", status_code=status.HTTP_301_MOVED_PERMANENTLY) 


@router.get("/hello-secure", response_class=HTMLResponse)
async def hello_secure(
    request: Request,
    x_forwarded_email: Optional[str] = Header(None, alias="X-Forwarded-Email"),
    x_forwarded_preferred_username: Optional[str] = Header(None, alias="X-Forwarded-Preferred-Username"),
    x_forwarded_groups: Optional[str] = Header(None, alias="X-Forwarded-Groups")
):
    """
    Protected page that displays authenticated user information.
    
    This endpoint will be secured by oauth2-proxy and will display the 
    authenticated user information passed in the headers.
    
    Args:
        request: The FastAPI request object.
        x_forwarded_email: Email address of the authenticated user (from oauth2-proxy).
        x_forwarded_preferred_username: Preferred username of the authenticated user (from oauth2-proxy).
        x_forwarded_groups: Group memberships of the authenticated user (from oauth2-proxy).
        
    Returns:
        HTMLResponse: The rendered secure hello page with user information.
    """
    try:
        # DEBUG: Log ALL headers to see what oauth2-proxy is sending
        all_headers = dict(request.headers)
        auth_headers = {k: v for k, v in all_headers.items() if k.lower().startswith('x-forwarded') or k.lower().startswith('x-auth')}
        logger.info(f"AUTH HEADERS: {auth_headers}")
        
        # Parse groups from comma-separated string
        groups_list = x_forwarded_groups.split(',') if x_forwarded_groups else []
        
        logger.info(f"Secure page accessed with auth headers: email={x_forwarded_email}, username={x_forwarded_preferred_username}, groups={groups_list}")
        
        return templates.TemplateResponse(
            name="pages/hello_secure.html",
            context={
                "request": request,
                "email": x_forwarded_email,
                "preferred_username": x_forwarded_preferred_username,
                "groups": groups_list,
                "page_title": "Secure Hello Page",
                "all_headers": auth_headers,  # Pass auth headers to template for debugging
            },
        )
    except Exception as e:
        logger.error(f"Error in secure hello page", extra={"error": str(e)})
        return templates.TemplateResponse(
            name="pages/hello_secure.html",
            context={
                "request": request,
                "error": "An error occurred while loading the secure page",
            },
            status_code=500,
        )


@router.get("/logout", response_class=HTMLResponse)
async def logout_success(request: Request):
    """
    Post-logout landing page.
    
    This endpoint provides a clean landing page after users have been logged out
    through the oauth2-proxy logout flow.
    
    Args:
        request: The FastAPI request object.
        
    Returns:
        HTMLResponse: A logout success page.
    """
    try:
        return templates.TemplateResponse(
            name="pages/logout_success.html",
            context={
                "request": request,
                "page_title": "Logged Out",
            },
        )
    except Exception as e:
        logger.error(f"Error in logout success page", extra={"error": str(e)})
        # Fallback to a simple redirect to home
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND) 


@router.get("/logout/oidc", response_class=RedirectResponse)
async def oidc_logout(
    request: Request,
    x_forwarded_access_token: Optional[str] = Header(None, alias="X-Forwarded-Access-Token"),
    x_forwarded_user: Optional[str] = Header(None, alias="X-Forwarded-User"),
    x_forwarded_email: Optional[str] = Header(None, alias="X-Forwarded-Email"),
    authorization: Optional[str] = Header(None)
):
    """
    OIDC logout endpoint that properly handles logout with id_token_hint.
    
    This endpoint:
    1. Extracts token information from OAuth2-Proxy headers
    2. Constructs the proper Keycloak logout URL with available parameters
    3. Redirects to OAuth2-Proxy sign_out with the proper OIDC logout URL
    
    Args:
        request: The FastAPI request object.
        x_forwarded_access_token: Access token from OAuth2-Proxy headers.
        x_forwarded_user: User ID from OAuth2-Proxy headers.
        x_forwarded_email: Email from OAuth2-Proxy headers.
        authorization: Authorization header containing Bearer token.
        
    Returns:
        RedirectResponse: Redirect to OAuth2-Proxy logout with proper OIDC parameters.
    """
    try:
        import base64
        import json
        from urllib.parse import quote, urlencode
        
        # Log all available headers for debugging
        all_headers = dict(request.headers)
        auth_headers = {k: v for k, v in all_headers.items() if k.lower().startswith('x-forwarded') or k.lower().startswith('x-auth')}
        logger.info(f"OIDC logout - Auth headers: {auth_headers}")
        logger.info(f"OIDC logout - Token info: access_token={bool(x_forwarded_access_token)}, user={x_forwarded_user}, email={x_forwarded_email}")
        
        # Try to extract ID token from various sources
        id_token = None
        
        # Method 1: Check Authorization header for ID token
        if authorization and "," in authorization:
            # OAuth2-proxy sometimes sends: "Basic ..., Bearer <id_token>"
            auth_parts = authorization.split(", Bearer ")
            if len(auth_parts) > 1:
                potential_id_token = auth_parts[1]
                logger.info(f"Found potential ID token from Authorization header: {potential_id_token[:50]}...")
                
                try:
                    # Decode and check if it's an ID token
                    if potential_id_token.count('.') == 2:
                        header, payload, signature = potential_id_token.split('.')
                        payload += '=' * (4 - len(payload) % 4)
                        decoded_payload = base64.urlsafe_b64decode(payload)
                        token_data = json.loads(decoded_payload)
                        
                        # ID tokens have typ: "ID" while access tokens have typ: "Bearer"
                        if token_data.get('typ') == 'ID':
                            id_token = potential_id_token
                            logger.info("Found valid ID token in Authorization header")
                        else:
                            logger.info(f"Token in Authorization header is type: {token_data.get('typ')}, not ID token")
                            
                except Exception as e:
                    logger.warning(f"Could not decode Authorization token: {e}")
        
        # Method 2: Skip access token as it's not an ID token
        # OAuth2-proxy access tokens are Bearer tokens, not ID tokens
        if x_forwarded_access_token:
            logger.info("Found X-Forwarded-Access-Token but skipping as it's an access token, not ID token")
        
        # If no ID token found, proceed without id_token_hint
        if not id_token:
            logger.info("No ID token found - proceeding with logout without id_token_hint")
        
        # Construct the base logout URL
        base_logout_url = "https://auth.hccc.edu/realms/hccc-apps-realm/protocol/openid-connect/logout"
        post_logout_redirect_uri = "https://web.hccc.edu/logout"
        
        # Build logout URL manually without encoding individual parameters
        # Include client_id so Keycloak knows which client is requesting logout
        keycloak_logout_url = f"{base_logout_url}?client_id=oauth2-proxy-client&post_logout_redirect_uri={post_logout_redirect_uri}"
        
        # Add id_token_hint if we have an ID token
        if id_token:
            keycloak_logout_url += f"&id_token_hint={id_token}"
            logger.info("OIDC logout with id_token_hint")
        else:
            logger.warning("OIDC logout without id_token_hint - may show confirmation page")
            # Add a hint about the user for better UX
            if x_forwarded_email:
                keycloak_logout_url += f"&login_hint={x_forwarded_email}"
        
        # Only URL encode the entire keycloak logout URL for OAuth2-Proxy redirect
        oauth2_proxy_logout_url = f"/oauth2/sign_out?rd={quote(keycloak_logout_url)}"
        
        logger.info(f"Keycloak logout URL: {keycloak_logout_url}")
        logger.info(f"OAuth2-Proxy logout URL: {oauth2_proxy_logout_url}")
        
        return RedirectResponse(url=oauth2_proxy_logout_url, status_code=status.HTTP_302_FOUND)
        
    except Exception as e:
        logger.error(f"Error in OIDC logout endpoint", extra={"error": str(e)})
        # Fallback to simple OAuth2-Proxy logout
        fallback_logout_url = f"/oauth2/sign_out?rd={quote('https://web.hccc.edu/logout')}"
        return RedirectResponse(url=fallback_logout_url, status_code=status.HTTP_302_FOUND) 
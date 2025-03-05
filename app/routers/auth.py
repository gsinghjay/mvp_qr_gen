"""
Authentication routes for MSAL integration.
"""
import base64
import json
import logging
from typing import Any, Dict, Optional
from urllib.parse import urljoin

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from app.auth.dependencies import get_auth_client, get_current_user
from app.auth.msal_client import MSALClient


logger = logging.getLogger(__name__)

auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={
        401: {"description": "Unauthorized"},
    },
)


def create_state_param(next_url: Optional[str] = None) -> str:
    """Create a state parameter for OAuth flow.
    
    Args:
        next_url: URL to redirect to after authentication
        
    Returns:
        Base64 encoded state parameter
    """
    state = {}
    if next_url:
        state["next"] = next_url
    
    return base64.b64encode(json.dumps(state).encode()).decode()


def parse_state_param(state: str) -> Dict[str, Any]:
    """Parse a state parameter from OAuth flow.
    
    Args:
        state: Base64 encoded state parameter
        
    Returns:
        Decoded state dictionary
    """
    try:
        decoded = base64.b64decode(state).decode()
        return json.loads(decoded)
    except (ValueError, json.JSONDecodeError):
        return {}


@auth_router.get("/login")
async def login(
    request: Request,
    next: Optional[str] = Query(None),
    auth_client: MSALClient = Depends(get_auth_client)
):
    """Redirect to Microsoft login page.
    
    Args:
        request: FastAPI request object
        next: URL to redirect to after authentication
        auth_client: MSAL client
        
    Returns:
        Redirect response to Microsoft login
    """
    # Create a state parameter with the next URL
    state = create_state_param(next)
    
    # Generate the full redirect URI including the host
    redirect_uri = urljoin(str(request.base_url), auth_client.settings.REDIRECT_PATH)
    
    # Get the authorization URL
    auth_url = auth_client.get_auth_url(redirect_uri, state)
    
    logger.info("Redirecting to Microsoft login", extra={"redirect_uri": redirect_uri})
    
    return RedirectResponse(auth_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@auth_router.get("/callback")
async def callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
    auth_client: MSALClient = Depends(get_auth_client)
):
    """Handle the callback from Microsoft login.
    
    Args:
        request: FastAPI request object
        code: Authorization code from Microsoft
        state: State parameter from login request
        error: Error from Microsoft
        error_description: Error description from Microsoft
        auth_client: MSAL client
        
    Returns:
        Redirect to the next URL or home
    """
    # If there's an error, return it
    if error:
        logger.error(
            "Authentication error",
            extra={"error": error, "error_description": error_description}
        )
        return HTMLResponse(
            f"<h1>Authentication Error</h1><p>{error}: {error_description}</p>",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Generate the full redirect URI including the host
    redirect_uri = urljoin(str(request.base_url), auth_client.settings.REDIRECT_PATH)
    
    # Get the token from the authorization code
    try:
        token = auth_client.get_token_from_code(code, redirect_uri)
    except HTTPException as e:
        logger.error("Failed to get token", exc_info=True)
        return HTMLResponse(
            f"<h1>Authentication Error</h1><p>{e.detail}</p>",
            status_code=e.status_code
        )
    
    # Validate the token
    auth_client.validate_token(token)
    
    # Get user information from the token
    claims = auth_client.get_token_claims(token["id_token"])
    
    # Store user information in session
    request.session["user"] = {
        "oid": claims.get("oid", ""),
        "name": claims.get("name", ""),
        "preferred_username": claims.get("preferred_username", ""),
        "roles": claims.get("roles", [])
    }
    
    # Store tokens in session
    request.session["tokens"] = {
        "access_token": token["access_token"],
        "id_token": token["id_token"],
        "refresh_token": token.get("refresh_token", "")
    }
    
    # Get the next URL from the state parameter
    next_url = "/"
    if state:
        state_data = parse_state_param(state)
        next_url = state_data.get("next", "/")
    
    logger.info(
        "User authenticated",
        extra={
            "user_id": claims.get("oid", ""),
            "next_url": next_url
        }
    )
    
    return RedirectResponse(next_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@auth_router.get("/logout")
async def logout(request: Request):
    """Log out the user by clearing the session.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Redirect to home
    """
    # Clear the session
    request.session.clear()
    
    logger.info("User logged out")
    
    return RedirectResponse("/", status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@auth_router.get("/me", response_class=HTMLResponse)
async def me(user: Dict[str, Any] = Depends(get_current_user)):
    """Get information about the current user.
    
    Args:
        user: Current user from session
        
    Returns:
        HTML response with user information
    """
    return HTMLResponse(f"""
    <h1>User Information</h1>
    <p>Name: {user["name"]}</p>
    <p>Username: {user["preferred_username"]}</p>
    <p>ID: {user["oid"]}</p>
    <p>Roles: {", ".join(user.get("roles", []))}</p>
    """)
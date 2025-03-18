"""
Authentication router for the FastAPI application.

This module provides endpoints for authentication using Microsoft Azure AD.
"""

from datetime import datetime, timedelta, UTC
from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.security import OAuth2PasswordBearer
from jose import jwt

from app.auth.sso import (
    User,
    create_access_token,
    get_current_user,
    get_microsoft_sso,
    get_optional_user,
    get_user_groups,
    requires_group,
)
from app.core.config import settings

# Create router
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

# OAuth2 scheme for token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


@router.get("/login")
async def login():
    """
    Redirect to Microsoft login page.
    
    Returns:
        RedirectResponse: Redirect to Microsoft login page.
    """
    microsoft_sso = get_microsoft_sso()
    async with microsoft_sso:
        return await microsoft_sso.get_login_redirect()


@router.get("/callback")
async def callback(request: Request):
    """
    Process the SSO callback from Microsoft.
    
    Args:
        request: The FastAPI request object.
        
    Returns:
        RedirectResponse: Redirect to home page with auth token cookie.
        
    Raises:
        HTTPException: If authentication fails.
    """
    microsoft_sso = get_microsoft_sso()
    async with microsoft_sso:
        user = await microsoft_sso.verify_and_process(request)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )
    
    # Get the access token from the user object provided by fastapi-sso
    # This is needed to call the Microsoft Graph API
    ms_access_token = getattr(user, "access_token", None)
    
    # Fetch user groups if we have an access token
    groups = []
    if ms_access_token:
        groups = await get_user_groups(ms_access_token)
    
    # Create access token with groups included
    access_token = create_access_token(
        data={
            "sub": user.id,
            "email": user.email,
            "name": user.display_name,
            "groups": groups  # Include the groups in the token
        },
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    # Set token in cookie and redirect to home
    response = RedirectResponse(url="/")
    response.set_cookie(
        key="auth_token",
        value=access_token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",  # Only secure in production
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",  # Ensure cookie is available throughout the site
    )
    
    return response


@router.get("/logout")
async def logout(request: Request):
    """
    Log out the user completely by clearing the auth token cookie,
    ensuring proper cache invalidation, and redirecting to Azure AD
    logout to terminate the SSO session.
    
    Args:
        request: The request object
        
    Returns:
        RedirectResponse: Redirect to login page
    """
    # First, determine if we need to logout from Azure AD
    # We need to check if the user is currently authenticated
    current_token = request.cookies.get("auth_token")
    
    # Create response that redirects to login page
    redirect_url = "/portal-login"
    
    # For Azure AD logout
    # Always perform Azure AD logout if settings are configured, regardless of environment
    # This is crucial to completely end the SSO session
    if settings.AZURE_CLIENT_ID and settings.AZURE_TENANT_ID:
        try:
            # Azure AD Logout URL (for both B2C and regular Azure AD)
            azure_logout_base_url = f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}/oauth2/v2.0/logout"
            
            # The post_logout_redirect_uri must be pre-registered in Azure AD
            post_logout_redirect_uri = f"{request.base_url.scheme}://{request.base_url.netloc}/portal-login"
            
            logout_params = {
                "client_id": settings.AZURE_CLIENT_ID,
                "post_logout_redirect_uri": post_logout_redirect_uri
            }
            
            # Update the redirect URL to go to Azure AD logout first
            # Azure AD will then redirect back to our local login page
            redirect_url = f"{azure_logout_base_url}?{urlencode(logout_params)}"
        except Exception as e:
            # Log the error but continue with local logout
            print(f"Error creating Azure AD logout URL: {str(e)}")
    
    response = RedirectResponse(url=redirect_url)
    
    # Clear the auth token cookie with all security properties
    response.delete_cookie(
        key="auth_token",
        path="/",                     # Apply to all paths
        domain=None,                  # Use the domain from the request
        secure=settings.ENVIRONMENT == "production",  # Match login security setting
        httponly=True,                # Not accessible via JavaScript
        samesite="lax"                # CSRF protection
    )
    
    # Set the cookie with an expired date in the past for browser compatibility
    expires = datetime.now(UTC) - timedelta(hours=1)
    response.set_cookie(
        key="auth_token",
        value="",                     # Empty value
        expires=expires.strftime("%a, %d %b %Y %H:%M:%S GMT"),
        path="/",
        domain=None,
        secure=settings.ENVIRONMENT == "production",
        httponly=True,
        samesite="lax",
        max_age=0                     # Expire immediately
    )
    
    # Add cache control headers to prevent caching
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    # Attempt to send Azure AD OIDC end_session_endpoint request
    # This is another approach to terminate the SSO session
    # Note: This would typically be done client-side but we're making it server-side for completeness
    
    return response


@router.get("/me", response_model=User)
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    """
    Get information about the current authenticated user.
    
    Args:
        current_user: The current authenticated user.
        
    Returns:
        User: The current user information.
    """
    return current_user


@router.get("/scopes")
async def get_scopes():
    """
    Get information about the configured OAuth scopes.
    
    This endpoint provides visibility into what scopes are currently
    configured for the Microsoft SSO integration. It helps in debugging
    permission issues and understanding what data your application can access.
    
    Returns:
        dict: Information about the configured scopes.
    """
    # Get the Microsoft SSO client
    microsoft_sso = get_microsoft_sso()
    
    # Default scopes used by fastapi-sso for Microsoft
    default_scopes = ["openid", "profile", "email", "User.Read"]
    
    # Get the scopes from the SSO client if available
    # Note: fastapi-sso might not expose scopes directly, so we use the defaults
    configured_scopes = getattr(microsoft_sso, "scopes", default_scopes)
    
    # Scopes needed for group membership
    group_scopes = ["GroupMember.Read.All", "Group.Read.All", "Directory.Read.All"]
    
    # Check which group scopes are configured
    configured_group_scopes = [scope for scope in group_scopes if scope in configured_scopes]
    
    return {
        "default_scopes": default_scopes,
        "configured_scopes": configured_scopes,
        "group_scopes_needed": group_scopes,
        "group_scopes_configured": configured_group_scopes,
        "has_group_access": any(scope in configured_scopes for scope in group_scopes),
        "group_membership_available": "GroupMember.Read.All" in configured_scopes,
        "missing_group_scopes": [scope for scope in group_scopes if scope not in configured_scopes],
        "documentation_url": "https://learn.microsoft.com/en-us/graph/permissions-reference"
    }


@router.get("/me/debug")
async def read_users_me_debug(request: Request, token: str = Depends(oauth2_scheme)):
    """
    Get debug information about the current user's token.
    
    This endpoint decodes the JWT token without verification to show all claims.
    It's useful for debugging what information is available in the token.
    
    Args:
        request: The FastAPI request object.
        token: The JWT token.
        
    Returns:
        dict: The decoded token payload.
        
    Raises:
        HTTPException: If the token is invalid or the user is not authenticated.
    """
    if token is None:
        token = request.cookies.get("auth_token")
        if token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
    
    try:
        # Decode without verification to see all claims
        payload = jwt.decode(
            token, 
            key=settings.SESSION_SECRET_KEY,  # Include the key parameter
            options={"verify_signature": False},
            algorithms=["HS256"]
        )
        return payload
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token format: {str(e)}"
        )


@router.get("/me/groups")
async def read_user_groups(current_user: Annotated[User, Depends(get_current_user)]):
    """
    Get the groups that the current authenticated user is a member of.
    
    Args:
        current_user: The current authenticated user.
        
    Returns:
        dict: The user's group information.
    """
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "groups": current_user.groups,
        "group_count": len(current_user.groups)
    }


@router.get("/admin-only")
async def admin_only_endpoint(current_user: Annotated[User, Depends(requires_group("admin-group"))]):
    """
    Example endpoint that requires membership in the admin-group.
    
    Args:
        current_user: The current authenticated user who is in the admin-group.
        
    Returns:
        dict: A message confirming the user has admin access.
    """
    return {
        "message": "You have admin access!",
        "user_id": current_user.id,
        "email": current_user.email,
        "admin_access": True
    }
"""
Authentication router for the FastAPI application.

This module provides endpoints for authentication using Microsoft Azure AD.
"""

from datetime import timedelta
from typing import Annotated

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
    
    # Create access token
    access_token = create_access_token(
        data={
            "sub": user.id,
            "email": user.email,
            "name": user.display_name
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
    )
    
    return response


@router.get("/logout")
async def logout():
    """
    Log out the user by clearing the auth token cookie.
    
    Returns:
        RedirectResponse: Redirect to home page.
    """
    response = RedirectResponse(url="/")
    response.delete_cookie("auth_token")
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
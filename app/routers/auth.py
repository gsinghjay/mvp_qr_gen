"""
Authentication router for the FastAPI application.

This module provides endpoints for authentication using Microsoft Azure AD.
"""

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer

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
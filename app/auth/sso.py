"""
SSO integration module for the FastAPI application.

This module provides integration with Microsoft Azure AD for Single Sign-On (SSO).
"""

from datetime import datetime, timedelta, UTC
from typing import Dict, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from fastapi_sso.sso.microsoft import MicrosoftSSO
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import settings


class User(BaseModel):
    """User model for authentication."""
    
    id: str
    email: str
    display_name: str
    
    @property
    def identity(self) -> str:
        """Return the user's identity."""
        return self.id


# OAuth2 scheme for token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


def get_microsoft_sso() -> MicrosoftSSO:
    """
    Get a configured Microsoft SSO client.
    
    Returns:
        MicrosoftSSO: A configured Microsoft SSO client.
    """
    return MicrosoftSSO(
        client_id=settings.AZURE_CLIENT_ID,
        client_secret=settings.AZURE_CLIENT_SECRET,
        tenant=settings.AZURE_TENANT_ID,
        redirect_uri=settings.REDIRECT_URI,
        allow_insecure_http=settings.ENVIRONMENT != "production",
    )


def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a new JWT token.
    
    Args:
        data: The data to encode in the token.
        expires_delta: The time until the token expires.
        
    Returns:
        str: The encoded JWT token.
    """
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SESSION_SECRET_KEY, algorithm="HS256")
    return encoded_jwt


async def get_current_user(request: Request, token: str = Depends(oauth2_scheme)) -> User:
    """
    Dependency to get the current authenticated user.
    
    Args:
        request: The FastAPI request object.
        token: The JWT token.
        
    Returns:
        User: The authenticated user.
        
    Raises:
        HTTPException: If the token is invalid or the user is not authenticated.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Try to get token from cookie if not in header
    if token is None:
        token = request.cookies.get("auth_token")
        if token is None:
            raise credentials_exception

    try:
        payload = jwt.decode(token, settings.SESSION_SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        email = payload.get("email")
        name = payload.get("name")
        
        if user_id is None or email is None:
            raise credentials_exception
            
        return User(id=user_id, email=email, display_name=name)
    except JWTError:
        raise credentials_exception


async def get_optional_user(request: Request, token: str = Depends(oauth2_scheme)) -> Optional[User]:
    """
    Dependency to get the current user if authenticated, otherwise None.
    
    Args:
        request: The FastAPI request object.
        token: The JWT token.
        
    Returns:
        Optional[User]: The authenticated user or None.
    """
    try:
        return await get_current_user(request, token)
    except HTTPException:
        return None 
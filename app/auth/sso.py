"""
SSO integration module for the FastAPI application.

This module provides integration with Microsoft Azure AD for Single Sign-On (SSO).
"""

from datetime import datetime, timedelta, UTC
from typing import Dict, Optional, List
import httpx
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
    groups: List[str] = []
    
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
    # Include GroupMember.Read.All in the scopes
    scope = "openid profile email User.Read GroupMember.Read.All"
    
    return MicrosoftSSO(
        client_id=settings.AZURE_CLIENT_ID,
        client_secret=settings.AZURE_CLIENT_SECRET,
        tenant=settings.AZURE_TENANT_ID,
        redirect_uri=settings.REDIRECT_URI,
        allow_insecure_http=settings.ENVIRONMENT != "production",
        scope=scope
    )


async def get_user_groups(access_token: str) -> List[str]:
    """
    Fetch the groups that the user is a member of using Microsoft Graph API.
    
    Args:
        access_token: The Microsoft Graph API access token.
        
    Returns:
        List[str]: List of group IDs the user is a member of.
        
    Raises:
        HTTPException: If the API request fails.
    """
    try:
        # Microsoft Graph API endpoint for user's group memberships
        graph_api_url = "https://graph.microsoft.com/v1.0/me/memberOf"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                graph_api_url,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code != 200:
                # Log the error but don't fail the authentication
                print(f"Failed to fetch user groups: {response.status_code}, {response.text}")
                return []
            
            data = response.json()
            
            # Extract group IDs from the response
            groups = []
            for item in data.get("value", []):
                if item.get("@odata.type", "").endswith("group"):
                    groups.append(item.get("id"))
            
            return groups
    except Exception as e:
        # Log the error but don't fail the authentication
        print(f"Error fetching user groups: {str(e)}")
        return []


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
        groups = payload.get("groups", [])
        
        if user_id is None or email is None:
            raise credentials_exception
            
        return User(id=user_id, email=email, display_name=name, groups=groups)
    except JWTError:
        raise credentials_exception


def is_user_in_group(user: User, group_id: str) -> bool:
    """
    Check if a user is a member of a specific group.
    
    Args:
        user: The user to check.
        group_id: The group ID to check membership for.
        
    Returns:
        bool: True if the user is a member of the group, False otherwise.
    """
    return group_id in user.groups


def requires_group(group_id: str):
    """
    Dependency factory to require membership in a specific group.
    
    Args:
        group_id: The group ID that is required for access.
        
    Returns:
        callable: A dependency that checks if the current user is in the specified group.
    """
    async def dependency(current_user: User = Depends(get_current_user)):
        if not is_user_in_group(current_user, group_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: User is not a member of the required group"
            )
        return current_user
    return dependency


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
"""
FastAPI authentication dependencies.
"""
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, Request, status

from app.auth.msal_client import MSALClient


def get_auth_client(request: Request) -> MSALClient:
    """Get the MSAL client from app state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        MSAL client instance
    """
    return request.app.state.auth_client


def get_current_user(
    request: Request,
    auth_client: MSALClient = Depends(get_auth_client)
) -> Dict[str, Any]:
    """Get the current authenticated user from session.
    
    This dependency can be used to protect routes that require authentication.
    
    Args:
        request: FastAPI request object
        auth_client: MSAL client instance
        
    Returns:
        User data dictionary from session
        
    Raises:
        HTTPException: If user is not authenticated
    """
    if "user" not in request.session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    return request.session["user"]


def get_user_with_role(role: str):
    """Create a dependency that checks if user has a specific role.
    
    Args:
        role: Role name to check for
        
    Returns:
        Dependency function that returns user if they have the role
        
    Raises:
        HTTPException: If user doesn't have the required role
    """
    
    def _get_user_with_role(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        """Check if user has a specific role.
        
        Args:
            user: User data from get_current_user dependency
            
        Returns:
            User data if they have the required role
            
        Raises:
            HTTPException: If user doesn't have the required role
        """
        user_roles = user.get("roles", [])
        if role not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User doesn't have required role: {role}"
            )
        return user
    
    return _get_user_with_role
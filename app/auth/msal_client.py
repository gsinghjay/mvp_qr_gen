"""
Microsoft Authentication Library (MSAL) client implementation.
"""
import logging
from typing import Any, Dict, List, Optional

import msal
from fastapi import HTTPException, status
from jose import jwt

from app.auth.config import AuthSettings, auth_settings


logger = logging.getLogger(__name__)


class MSALClient:
    """MSAL client for Microsoft Azure AD authentication."""
    
    def __init__(self, settings: Optional[AuthSettings] = None):
        """Initialize MSAL client with settings.
        
        Args:
            settings: Authentication settings, defaults to global auth_settings
        """
        self.settings = settings or auth_settings
        self.client_id = self.settings.CLIENT_ID
        self.client_secret = self.settings.CLIENT_SECRET
        self.tenant_id = self.settings.TENANT_ID
        self.authority = self.settings.AUTHORITY
        self.scope = self.settings.SCOPE
        
        self.msal_app = msal.ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=self.authority
        )
    
    def get_auth_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        """Generate authorization URL for user sign-in.
        
        Args:
            redirect_uri: URI to redirect after authentication
            state: Optional state to include in the request
            
        Returns:
            Authorization URL to redirect the user to
        """
        return self.msal_app.get_authorization_request_url(
            self.scope,
            redirect_uri=redirect_uri,
            state=state
        )
    
    def get_token_from_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Acquire tokens from authorization code.
        
        Args:
            code: Authorization code from callback
            redirect_uri: Redirect URI used in initial request
            
        Returns:
            Dict containing access_token, id_token, and other token data
            
        Raises:
            HTTPException: If token acquisition fails
        """
        result = self.msal_app.acquire_token_by_authorization_code(
            code,
            self.scope,
            redirect_uri=redirect_uri
        )
        
        if "error" in result:
            logger.error(
                "Token acquisition failed",
                extra={
                    "error": result.get("error"),
                    "error_description": result.get("error_description")
                }
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {result.get('error')} - {result.get('error_description')}"
            )
        
        return result
    
    def validate_token(self, token: Dict[str, Any]) -> bool:
        """Validate token data.
        
        Args:
            token: Token data to validate
            
        Returns:
            True if token is valid
            
        Raises:
            HTTPException: If token is invalid
        """
        if "error" in token:
            logger.error("Invalid token", extra={"error": token.get("error")})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {token.get('error')}"
            )
        
        # In a production app, we would do more validation here:
        # 1. Verify id_token signature using jwks_uri from tenant's OpenID configuration
        # 2. Validate claims (iss, aud, exp, nbf, etc.)
        # 3. Check for token revocation
        
        # For now, just check if required keys exist
        required_keys = ["access_token", "id_token"]
        if not all(key in token for key in required_keys):
            missing_keys = [key for key in required_keys if key not in token]
            logger.error(
                "Token missing required fields",
                extra={"missing_keys": missing_keys}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token missing required fields: {', '.join(missing_keys)}"
            )
        
        return True
    
    def get_token_claims(self, id_token: str) -> Dict[str, Any]:
        """Extract claims from ID token without validation.
        
        In a production environment, you should validate the token first.
        
        Args:
            id_token: JWT ID token
            
        Returns:
            Dict of claims from token
        """
        # Note: This doesn't validate the token signature, only decodes it
        # For production, use a proper validation method with the tenant's jwks_uri
        claims = jwt.decode(
            id_token,
            options={"verify_signature": False}
        )
        return claims
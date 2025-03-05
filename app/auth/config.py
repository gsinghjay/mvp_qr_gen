"""
Authentication configuration module for MSAL integration.
"""
import os
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSettings(BaseSettings):
    """Microsoft Authentication Library (MSAL) settings."""

    # Required Azure AD settings
    CLIENT_ID: str = Field(
        default="dummy-client-id" if os.environ.get("ENVIRONMENT") == "test" else ...,
        description="Azure AD application client ID"
    )
    CLIENT_SECRET: str = Field(
        default="dummy-client-secret" if os.environ.get("ENVIRONMENT") == "test" else ...,
        description="Azure AD application client secret"
    )
    TENANT_ID: str = Field(
        default="dummy-tenant-id" if os.environ.get("ENVIRONMENT") == "test" else ...,
        description="Azure AD tenant ID"
    )
    
    # Optional settings with reasonable defaults
    AUTHORITY: str = Field(
        default=None, 
        description="Azure AD authority URL"
    )
    REDIRECT_PATH: str = Field(
        default="/auth/callback", 
        description="Redirect URI path for authentication"
    )
    SCOPE: List[str] = Field(
        default=["User.Read", "profile", "email"],
        description="Requested OAuth scopes"
    )
    SESSION_TYPE: str = Field(
        default="filesystem", 
        description="Session storage type"
    )
    SESSION_COOKIE_NAME: str = Field(
        default="session", 
        description="Session cookie name"
    )
    SESSION_COOKIE_SECURE: bool = Field(
        default=True, 
        description="Secure flag for session cookie"
    )
    
    @field_validator("AUTHORITY", mode="before")
    def set_authority(cls, v, info):
        """Set default authority if not provided."""
        values = info.data
        if not v and values.get("TENANT_ID"):
            return f"https://login.microsoftonline.com/{values['TENANT_ID']}/oauth2/v2.0"
        return v
    
    @field_validator("SCOPE", mode="before")
    def parse_scope(cls, v):
        """Parse scope string into list if provided as string."""
        if isinstance(v, str):
            if not v:
                raise ValueError("Scope cannot be empty")
            return [s.strip() for s in v.split(",")]
        return v
    
    @field_validator("SCOPE")
    def validate_scope(cls, v):
        """Validate scope is not empty."""
        if not v:
            raise ValueError("Scope cannot be empty")
        return v
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_prefix="MSAL_",
        case_sensitive=True,
        extra="ignore"
    )


# Create singleton instance
auth_settings = AuthSettings()
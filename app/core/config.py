"""
Core configuration module for the FastAPI application.
"""

import os
from pathlib import Path
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Path configuration
# Default paths for Docker container
DOCKER_APP_ROOT = Path("/app/app")
# For local development, base on the location of this file
LOCAL_APP_ROOT = Path(__file__).parents[2]  # Go up two levels from core/config.py

# Determine application root based on environment
def get_app_root() -> Path:
    """
    Get the application root path, checking for Docker container first.
    
    Returns:
        Path: The application root path
    """
    if DOCKER_APP_ROOT.exists():
        return DOCKER_APP_ROOT
    return LOCAL_APP_ROOT

# Application paths
APP_ROOT = get_app_root()
STATIC_DIR = APP_ROOT / "static"
TEMPLATES_DIR = APP_ROOT / "templates"
QR_CODES_DIR = STATIC_DIR / "assets" / "images" / "qr_codes"
DEFAULT_LOGO_PATH = STATIC_DIR / "assets" / "images" / "hccc_logo_official.png"

# Create directories if they don't exist
QR_CODES_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    """Application settings using Pydantic v2."""

    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = True
    
    # Base URL for QR codes (full domain with protocol)
    # Override with BASE_URL environment variable in production
    BASE_URL: str = "http://localhost:8000"

    # Database URLs
    TEST_DATABASE_URL: str | None = os.getenv("TEST_DATABASE_URL")
    
    # Security
    TRUSTED_HOSTS: list[str] = ["*"]
    CORS_ORIGINS: list[str] = ["*"]
    CORS_HEADERS: list[str] = ["*"]

    # Allowed redirect domains for QR codes
    ALLOWED_REDIRECT_DOMAINS: str | List[str] = "hccc.edu,example.com,localhost"

    @field_validator("ALLOWED_REDIRECT_DOMAINS", mode="before")
    @classmethod
    def parse_allowed_domains(cls, v):
        """Parse comma-separated string of allowed domains from environment variable."""
        if isinstance(v, str):
            # Split by comma and strip whitespace
            domains = [domain.strip() for domain in v.split(",") if domain.strip()]
            return domains if domains else ["hccc.edu", "example.com", "localhost"]
        elif isinstance(v, list):
            return v
        else:
            # Return default if not string or list
            return ["hccc.edu", "example.com", "localhost"]

    # Middleware Configuration
    ENABLE_GZIP: bool = True
    GZIP_MIN_SIZE: int = 1000
    ENABLE_METRICS: bool = True
    ENABLE_LOGGING: bool = True

    # Metrics
    METRICS_ENDPOINT: str = "/metrics"

    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Cookie settings - used only for non-auth related functionality like CSRF
    COOKIE_DOMAIN: str = "10.1.6.12"

    # Feature Flags - Observatory-First Refactoring
    FEATURE_NEW_QR_SERVICE_ENABLED: bool = False
    FEATURE_ENHANCED_VALIDATION_ENABLED: bool = False
    FEATURE_PERFORMANCE_OPTIMIZATION_ENABLED: bool = False
    FEATURE_DEBUG_MODE_ENABLED: bool = False
    
    # Phase 0 Feature Flags
    USE_NEW_QR_GENERATION_SERVICE: bool = Field(default=False, env="USE_NEW_QR_GENERATION_SERVICE")
    USE_NEW_ANALYTICS_SERVICE: bool = Field(default=False, env="USE_NEW_ANALYTICS_SERVICE")
    USE_NEW_VALIDATION_SERVICE: bool = Field(default=False, env="USE_NEW_VALIDATION_SERVICE")
    
    # Canary Testing Configuration
    CANARY_TESTING_ENABLED: bool = Field(default=False, env="CANARY_TESTING_ENABLED")
    CANARY_PERCENTAGE: int = Field(default=0, ge=0, le=100, env="CANARY_PERCENTAGE")
    
    # Circuit Breaker Configuration
    QR_GENERATION_CB_FAIL_MAX: int = Field(default=5, env="QR_GENERATION_CB_FAIL_MAX")
    QR_GENERATION_CB_RESET_TIMEOUT: int = Field(default=60, env="QR_GENERATION_CB_RESET_TIMEOUT")

    # Path settings
    APP_ROOT: Path = APP_ROOT
    STATIC_DIR: Path = STATIC_DIR
    TEMPLATES_DIR: Path = TEMPLATES_DIR
    QR_CODES_DIR: Path = QR_CODES_DIR
    DEFAULT_LOGO_PATH: Path = DEFAULT_LOGO_PATH

    model_config = SettingsConfigDict(
        env_file=".env", 
        case_sensitive=True,
        extra="ignore"  # Ignore extra environment variables not defined in the model
    )


settings = Settings()

# Function to get settings for dependency injection
def get_settings():
    """
    Return the settings instance for dependency injection.
    
    This allows overriding settings in tests by patching this function.
    """
    return settings


def should_use_new_service(settings: Settings, user_identifier: str | None = None) -> bool:
    """
    Determine if new service implementation should be used based on flags and canary settings.
    
    Args:
        settings: Application settings instance
        user_identifier: Optional user identifier for canary testing (IP, session ID, etc.)
        
    Returns:
        bool: True if new service should be used, False for legacy service
    """
    # If canary testing is enabled, use deterministic percentage-based routing
    if settings.CANARY_TESTING_ENABLED:
        if user_identifier:
            # Use hash of user identifier for deterministic routing
            import hashlib
            hash_value = int(hashlib.md5(user_identifier.encode()).hexdigest()[:8], 16)
            return (hash_value % 100) < settings.CANARY_PERCENTAGE
        else:
            # Fallback to random routing if no user identifier
            import random
            return random.randint(0, 99) < settings.CANARY_PERCENTAGE
    
    # If canary is disabled, check specific feature flags
    # For now, return general QR generation service flag
    # This can be made more specific per service type in future iterations
    return settings.USE_NEW_QR_GENERATION_SERVICE

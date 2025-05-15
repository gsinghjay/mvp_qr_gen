"""
Core configuration module for the FastAPI application.
"""

import os
from pathlib import Path
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
DEFAULT_LOGO_PATH = STATIC_DIR / "assets" / "images" / "logo_hccc_qr.jpg"

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

    # Path settings
    APP_ROOT: Path = APP_ROOT
    STATIC_DIR: Path = STATIC_DIR
    TEMPLATES_DIR: Path = TEMPLATES_DIR
    QR_CODES_DIR: Path = QR_CODES_DIR
    DEFAULT_LOGO_PATH: Path = DEFAULT_LOGO_PATH

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()

# Function to get settings for dependency injection
def get_settings():
    """
    Return the settings instance for dependency injection.
    
    This allows overriding settings in tests by patching this function.
    """
    return settings

"""
Core configuration module for the FastAPI application.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings using Pydantic v2."""

    DATABASE_URL: str = "sqlite:///./data/qr_codes.db"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Base URL for QR codes (full domain with protocol)
    # Override with BASE_URL environment variable in production
    BASE_URL: str = "http://localhost:8000"

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

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()

# Function to get settings for dependency injection
def get_settings():
    """
    Return the settings instance for dependency injection.
    
    This allows overriding settings in tests by patching this function.
    """
    return settings

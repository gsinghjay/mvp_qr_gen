"""
Core configuration module for the FastAPI application.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings using Pydantic v2."""

    DATABASE_URL: str = "sqlite:///./data/qr_codes.db"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

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

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()

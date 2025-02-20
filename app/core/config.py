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

# Middleware configuration and order
MIDDLEWARE_CONFIG = [
    # GZip should be first to compress responses
    {
        "enabled": settings.ENABLE_GZIP,
        "class": "fastapi.middleware.gzip.GZipMiddleware",
        "kwargs": {"minimum_size": settings.GZIP_MIN_SIZE},
    },
    # Security middleware
    {
        "enabled": True,
        "class": "app.middleware.create_trusted_hosts_middleware",
        "args": [settings.TRUSTED_HOSTS],
    },
    {
        "enabled": True,
        "class": "app.middleware.create_cors_middleware",
        "args": [settings.CORS_ORIGINS],
    },
    {
        "enabled": True,
        "class": "app.middleware.create_security_headers_middleware",
        "is_decorator": True,
    },
    # Monitoring middleware
    {"enabled": settings.ENABLE_METRICS, "class": "app.middleware.MetricsMiddleware"},
    # Logging should be last to capture accurate timing
    {"enabled": settings.ENABLE_LOGGING, "class": "app.middleware.LoggingMiddleware"},
]

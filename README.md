## QR Code Generator Repository Documentation

### What is it?

This repository provides an API and web interface for generating and managing QR codes. It supports both static and dynamic QR codes. Dynamic QR codes offer redirect URLs and scan tracking. The API is built with FastAPI and uses a SQLite database.

### Quick Start

To run the QR Code Generator locally using Docker Compose:

1.  Ensure Docker and Docker Compose are installed.
2.  Clone the repository.
3.  Navigate to the repository directory in your terminal.
4.  Run: `docker-compose up --build`

This command builds the Docker image and starts the application along with Traefik.
Access the application at `https://localhost`.
The API documentation is available at `https://localhost/docs`.

### Configuration

The application can be configured via environment variables and configuration files.

#### Environment Variables

Environment variables are set in `.env` file or directly in your environment.

*   **`DATABASE_URL`**:  Database connection string. Defaults to `sqlite:///./data/qr_codes.db`. For in-memory testing use `sqlite:///:memory:`.
*   **`ENVIRONMENT`**:  Environment mode, `development` or `production`. Defaults to `development`.
*   **`DEBUG`**: Enable debug mode. Defaults to `False`.
*   **`TRUSTED_HOSTS`**:  List of trusted hosts. Defaults to `*`.
*   **`CORS_ORIGINS`**: List of allowed CORS origins. Defaults to `*`.
*   **`CORS_HEADERS`**: List of allowed CORS headers. Defaults to `*`.
*   **`ENABLE_GZIP`**: Enable GZip compression. Defaults to `True`.
*   **`GZIP_MIN_SIZE`**: Minimum size for GZip compression. Defaults to `1000`.
*   **`ENABLE_METRICS`**: Enable metrics endpoint. Defaults to `True`.
*   **`ENABLE_LOGGING`**: Enable request logging. Defaults to `True`.
*   **`METRICS_ENDPOINT`**: Metrics endpoint path. Defaults to `/metrics`.
*   **`LOG_LEVEL`**: Application log level. Defaults to `INFO`.

#### `app/core/config.py`

This file defines application settings using Pydantic. It loads settings from environment variables and `.env` file. Refer to this file for detailed configuration options and defaults.

#### `dynamic_conf.yml`

This Traefik dynamic configuration file defines routing rules and middleware. It sets up:

*   Routers for API and dashboard.
*   Middleware for HTTPS redirection.
*   Service for the API application.

#### `traefik.yml`

This Traefik static configuration file sets up:

*   Entrypoints for web (port 80), websecure (port 443), traefik (dashboard port 8080), and metrics (port 8082).
*   Providers for Docker and file-based dynamic configuration.
*   API dashboard and insecure access enabled (for development).
*   Access logs and Prometheus metrics enabled.
*   TLS configuration with a self-signed certificate for development.

### Package Summary

This repository provides a FastAPI application to generate and manage QR codes.
The core functionalities are encapsulated within the `app` directory, creating a single deployable package.

### API Documentation

The API is structured into several routers:

#### API Version 1 (`/api/v1`)

*   **`GET /api/v1/qr`**: List QR codes with pagination and optional filtering by `qr_type`.
    *   Query Parameters:
        *   `skip` (int, optional):  Number of items to skip for pagination.
        *   `limit` (int, optional): Maximum number of items per page.
        *   `qr_type` (str, optional): Filter by QR code type (`static` or `dynamic`).
    *   Response Model: `QRCodeList`
*   **`GET /api/v1/qr/{qr_id}`**: Get QR code data by ID.
    *   Path Parameter:
        *   `qr_id` (str):  QR code identifier.
    *   Response Model: `QRCodeResponse`
*   **`GET /api/v1/qr/{qr_id}/image`**: Get QR code image by ID.
    *   Path Parameter:
        *   `qr_id` (str): QR code identifier.
    *   Query Parameters:
        *   `image_format` (str, optional):  Image format (`png`, `jpeg`, `jpg`, `svg`, `webp`). Defaults to `png`.
        *   `image_quality` (int, optional): Image quality for JPEG and WebP (1-100).
*   **`PUT /api/v1/qr/{qr_id}`**: Update QR code data by ID. Currently only updates `redirect_url` for dynamic QR codes.
    *   Path Parameter:
        *   `qr_id` (str): QR code identifier.
    *   Request Body: `QRCodeUpdate`
    *   Response Model: `QRCodeResponse`

#### Dynamic QR Code Router (`/api/v1/qr/dynamic`)

*   **`POST /api/v1/qr/dynamic`**: Create a new dynamic QR code.
    *   Request Body: `QRCodeCreate` (must include `redirect_url`)
    *   Response Model: `QRCodeResponse`
*   **`PUT /api/v1/qr/dynamic/{qr_id}`**: Update a dynamic QR code's redirect URL.
    *   Path Parameter:
        *   `qr_id` (str): QR code identifier.
    *   Request Body: `QRCodeUpdate` (must include `redirect_url`)
    *   Response Model: `QRCodeResponse`

#### Static QR Code Router (`/api/v1/qr/static`)

*   **`POST /api/v1/qr/static`**: Create a new static QR code.
    *   Request Body: `QRCodeCreate` (`redirect_url` must be None)
    *   Response Model: `QRCodeResponse`

#### Redirect Router (`/r`)

*   **`GET /r/{short_id}`**: Redirect endpoint for dynamic QR codes.
    *   Path Parameter:
        *   `short_id` (str): Short identifier from the dynamic QR code content.

#### Web Pages Router (`/`)

*   **`GET /`**: Renders the home page with dashboard information.

### Dependencies and Requirements

*   Python 3.12+
*   Dependencies listed in `requirements.txt` or `pyproject.toml`:
    *   `alembic`
    *   `fastapi`
    *   `pydantic`
    *   `pydantic-settings`
    *   `prometheus-client`
    *   `qrcode`
    *   `SQLAlchemy`
    *   `uvicorn`

### Advanced Usage Examples

#### Database Management

The `app/scripts/manage_db.py` script provides tools for database management:

*   `--init`: Initializes a fresh database, removing existing data.
*   `--migrate`: Runs database migrations to the latest version.
*   `--check`: Checks if migrations are needed.
*   `--validate`: Validates the database structure.

These commands can be executed inside the Docker container. For example, to initialize the database:

```bash
docker-compose exec api /app/scripts/manage_db.py --init
```

#### Production Deployment with Traefik

The provided `docker-compose.yml`, `Dockerfile`, `dynamic_conf.yml`, and `traefik.yml` are configured for production deployment using Traefik as a reverse proxy and TLS termination.

To deploy in production:

1.  Set `ENVIRONMENT` environment variable to `production`.
2.  Ensure proper TLS certificate configuration in `traefik.yml` for HTTPS.
3.  Build and run the application using `docker-compose up --build -d`.

Traefik automatically handles routing and HTTPS, and the application runs with production settings (e.g., hot-reloading disabled, multiple workers).
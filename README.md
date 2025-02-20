## QR Code Generator API Documentation

### 1. Overview

This repository provides a REST API for generating and managing QR codes.
It supports both static and dynamic QR codes.
Dynamic QR codes offer redirect functionality and scan tracking.
The API is built with FastAPI and uses a SQLite database.
It includes features like middleware for logging, metrics, and security.

### 2. Quick Start

**Installation:**

1.  Ensure Docker and Docker Compose are installed.
2.  Clone the repository.
3.  Navigate to the repository directory in your terminal.
4.  Run `docker-compose up --build` to build and start the application.

**Basic Usage:**

1.  Access the API documentation at `http://localhost:8080/docs` (or `https://your-domain/docs` if deployed with Traefik).
2.  Use the `/api/v1/qr/static` endpoint to create static QR codes.
    -   Provide `content` in the request body.
    -   Optionally customize `fill_color`, `back_color`, `size`, and `border`.
3.  Use the `/api/v1/qr/dynamic` endpoint to create dynamic QR codes.
    -   Provide `redirect_url` in the request body.
    -   Optionally customize `fill_color`, `back_color`, `size`, and `border`.
4.  Retrieve QR code images using the `/api/v1/qr/{qr_id}/image` endpoint.
    -   Specify `qr_id` and optionally `image_format` and `image_quality` as query parameters.
5.  Access dynamic QR codes via the `/r/{short_id}` redirect endpoint.

### 3. Configuration

The application is configured via environment variables and configuration files.

**Environment Variables:**

*   `DATABASE_URL`:  Database connection string. Defaults to `sqlite:///./data/qr_codes.db`.
*   `ENVIRONMENT`:  Environment mode (`development` or `production`). Defaults to `development`.
*   `DEBUG`:  Debug mode for FastAPI. Defaults to `False`.
*   `TRUSTED_HOSTS`:  List of trusted hosts. Defaults to `*`.
*   `CORS_ORIGINS`:  List of allowed CORS origins. Defaults to `*`.
*   `CORS_HEADERS`:  List of allowed CORS headers. Defaults to `*`.
*   `ENABLE_GZIP`:  Enable GZip middleware. Defaults to `True`.
*   `GZIP_MIN_SIZE`:  Minimum size for GZip compression. Defaults to `1000`.
*   `ENABLE_METRICS`:  Enable metrics middleware. Defaults to `True`.
*   `ENABLE_LOGGING`:  Enable logging middleware. Defaults to `True`.
*   `METRICS_ENDPOINT`:  Metrics endpoint path. Defaults to `/metrics`.
*   `LOG_LEVEL`:  Application log level. Defaults to `INFO`.

**Configuration Files:**

*   `dynamic_conf.yml`: Traefik dynamic configuration for routing and services.
*   `traefik.yml`: Traefik static configuration for providers, entrypoints, and certificates.
*   `alembic.ini`: Alembic configuration for database migrations.
*   `pyproject.toml`: Python project configuration, including dependencies.
*   `package.json`: Node.js project configuration, mainly for development tools.

### 4. API Documentation

The API documentation is automatically generated using Swagger UI and is accessible at `/docs` endpoint of your application.

**API Endpoints:**

*   **`/api/v1/qr`**:
    *   `GET`: List QR codes with pagination and optional filtering by `qr_type`.
        *   Query parameters: `skip`, `limit`, `qr_type`.
    *   `GET /{qr_id}`: Get QR code data by ID.
    *   `GET /{qr_id}/image`: Get QR code image by ID.
        *   Query parameters: `image_format`, `image_quality`.
    *   `PUT /{qr_id}`: Update QR code data by ID (Dynamic QR codes only, updates `redirect_url`).
        *   Request body: `QRCodeUpdate` schema.

*   **`/api/v1/qr/static`**:
    *   `POST`: Create a new static QR code.
        *   Request body: `QRCodeCreate` schema.

*   **`/api/v1/qr/dynamic`**:
    *   `POST`: Create a new dynamic QR code.
        *   Request body: `QRCodeCreate` schema.
    *   `PUT /{qr_id}`: Update a dynamic QR code's redirect URL.
        *   Request body: `QRCodeUpdate` schema.

*   **`/r/{short_id}`**:
    *   `GET`: Redirect endpoint for dynamic QR codes.

*   **`/metrics`**:
    *   `GET`: Prometheus metrics endpoint.

*   **`/`**:
    *   `GET`: Home page, renders the web UI.

### 5. Dependencies and Requirements

**Python Dependencies:**

*   `fastapi`
*   `uvicorn`
*   `SQLAlchemy`
*   `alembic`
*   `qrcode`
*   `python-multipart`
*   `pydantic`
*   `pydantic-settings`
*   `prometheus-client`
*   `Jinja2`

These dependencies are listed in `requirements.txt` and `pyproject.toml`.

**Node.js Dependencies (Development Tools):**

*   `@browserbasehq/stagehand`
*   `playwright`
*   `cursor-tools`

These are listed in `package.json`.

**System Requirements:**

*   Docker
*   Docker Compose

### 6. Advanced Usage Examples

**Customizing QR Code Appearance:**

When creating static or dynamic QR codes, you can customize the appearance using the following parameters:

*   `fill_color`:  Set the color of the QR code pattern. Example: `#008000` (green).
*   `back_color`: Set the background color. Example: `#F0F0F0` (light gray).
*   `size`:  Adjust the size of the QR code by changing the box size. Values from 1 to 100.
*   `border`:  Control the border around the QR code. Values from 0 to 20.

**Example (using curl to create a customized static QR code):**

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
        "content": "Custom QR Code",
        "fill_color": "#0000FF",
        "back_color": "#F0F0F0",
        "size": 12,
        "border": 2
      }' \
  http://localhost:8000/api/v1/qr/static
```

**Monitoring and Metrics:**

The application exposes Prometheus metrics at the `/metrics` endpoint.
Traefik also provides its own metrics, offering a comprehensive monitoring solution.
Application-level metrics complement Traefik's edge-level metrics.

**Logging:**

Detailed application logs are available in JSON format within the `/logs/api` directory inside the Docker container.
Traefik access logs are also configured and stored in `/logs/traefik`.
Logging middleware captures request details, response status, and performance metrics.

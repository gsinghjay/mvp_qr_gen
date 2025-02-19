
--- Repository Documentation ---

## QR Code Generator API Documentation

### 1. Repository Purpose and Summary

This repository provides a REST API for generating and managing QR codes. It supports creating static and dynamic QR codes with customizable appearance. The API is built with FastAPI and uses a SQLite database. An admin dashboard is included for managing QR codes.

### 2. Quick Start

#### Installation

1.  **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Run with Docker Compose:**

    ```bash
    docker-compose up --build
    ```

    This command builds the Docker image and starts the application along with Traefik.

3.  **Access the application:**

    *   Admin Dashboard: <https://localhost> (or <http://localhost> for development)
    *   API Documentation: <https://localhost/docs> (or <http://localhost/docs> for development)

#### Basic Usage

1.  **Create a dynamic QR code:**
    - Navigate to the admin dashboard at <https://localhost>.
    - Fill in the "Create QR Code" form with a destination URL and submit.
    - A new dynamic QR code will be created and listed in the "Existing QR Codes" section.

2.  **View a QR code image:**
    - In the "Existing QR Codes" table, click the "View" button for a specific QR code.
    - The QR code image will be displayed in the "Generated QR Code" section.

### 3. Configuration Options

The application is configured using environment variables and a configuration file (`app/core/config.py`). Key configuration options include:

*   **`DATABASE_URL`**:  Specifies the database connection URL (default: `sqlite:///./data/qr_codes.db`).
*   **`ENVIRONMENT`**: Sets the environment (development/production), affecting hot-reload and security headers (default: `development`).
*   **`DEBUG`**: Enables debug mode (default: `False`).
*   **`TRUSTED_HOSTS`**:  List of trusted hosts for the application (default: `["*"]`).
*   **`CORS_ORIGINS`**: List of allowed CORS origins (default: `["*"]`).
*   **`CORS_HEADERS`**: List of allowed CORS headers (default: `["*"]`).
*   **`ENABLE_GZIP`**: Enables GZip compression for responses (default: `True`).
*   **`GZIP_MIN_SIZE`**: Minimum size for GZip compression (default: `1000`).
*   **`ENABLE_METRICS`**: Enables Prometheus metrics endpoint (default: `True`).
*   **`METRICS_ENDPOINT`**:  Path for the metrics endpoint (default: `/metrics`).
*   **`ENABLE_LOGGING`**: Enables structured JSON logging (default: `True`).
*   **`LOG_LEVEL`**:  Sets the application log level (default: `INFO`).

These settings can be configured via environment variables or by modifying the `.env` file.

### 4. Package Summary (`app` package)

The `app` package contains the core logic of the QR Code Generator API. It includes:

*   **`core/`**:  Configuration settings (`config.py`).
*   **`database.py`**: Database initialization and session management.
*   **`main.py`**: Main FastAPI application instance and API endpoints.
*   **`models.py`**: SQLAlchemy database models.
*   **`qr_service.py`**:  QR code generation and related services.
*   **`schemas.py`**: Pydantic schemas for request and response validation.
*   **`middleware/`**: Custom middleware components for logging, metrics, and security.
*   **`scripts/`**: Scripts for database management and initialization.
*   **`static/`**: Static files (CSS, JavaScript, images).
*   **`templates/`**: Jinja2 templates for the admin dashboard.
*   **`tests/`**: Unit tests for the API.

### 5. Installation and Import

This repository is designed to be run as a containerized application using Docker.  No direct Python package installation is intended for end-users.

To use the application, follow the Quick Start guide to run the Docker Compose setup.

### 6. Detailed Documentation of Public Features / API / Interface

The API is documented using OpenAPI and can be accessed at `<https://localhost/docs>` (or `<http://localhost/docs>` for development).

#### API Endpoints

*   **`GET /`**:
    *   **Description**: Renders the admin dashboard HTML page.
    *   **Response Type**: `HTMLResponse`
    *   **Usage**: Access the admin dashboard in a web browser.

*   **`GET /docs`**:
    *   **Description**:  Serves the Swagger UI documentation for the API.
    *   **Response Type**: `HTMLResponse`
    *   **Usage**: Access the API documentation in a web browser.

*   **`GET /redoc`**:
    *   **Description**: Serves the ReDoc documentation for the API.
    *   **Response Type**: `HTMLResponse`
    *   **Usage**: Access the API documentation in a web browser.

*   **`GET /openapi.json`**:
    *   **Description**:  Serves the OpenAPI JSON schema for the API.
    *   **Response Type**: `JSONResponse`
    *   **Usage**: Retrieve the OpenAPI schema in JSON format.

*   **`GET /api/v1/qr`**:
    *   **Description**: Lists QR codes with pagination and optional filtering by type.
    *   **Response Model**: `QRCodeList`
    *   **Parameters**:
        *   `skip` (query, integer, optional): Number of items to skip for pagination.
        *   `limit` (query, integer, optional): Maximum number of items to return per page.
        *   `qr_type` (query, string, optional): Filter by QR code type (`static` or `dynamic`).
    *   **Usage**: Retrieve a list of QR codes, optionally paginated and filtered.

*   **`POST /api/v1/qr/static`**:
    *   **Description**: Creates a new static QR code.
    *   **Request Model**: `QRCodeCreate`
    *   **Response Model**: `QRCodeResponse`
    *   **Request Body**:
        ```json
        {
          "content": "Static QR code content",
          "fill_color": "#000000",
          "back_color": "#FFFFFF",
          "size": 10,
          "border": 4
        }
        ```
    *   **Usage**: Create a static QR code encoding the provided content directly.

*   **`POST /api/v1/qr/dynamic`**:
    *   **Description**: Creates a new dynamic QR code.
    *   **Request Model**: `QRCodeCreate`
    *   **Response Model**: `QRCodeResponse`
    *   **Request Body**:
        ```json
        {
          "content": "Dynamic QR code description",
          "redirect_url": "https://example.com",
          "fill_color": "#000000",
          "back_color": "#FFFFFF",
          "size": 10,
          "border": 4
        }
        ```
    *   **Usage**: Create a dynamic QR code that redirects to the specified `redirect_url`.

*   **`GET /r/{short_id}`**:
    *   **Description**: Redirect endpoint for dynamic QR codes. Redirects to the configured URL for a dynamic QR code based on its short ID.
    *   **Path Parameters**:
        *   `short_id` (string): Short identifier part of the dynamic QR code's content.
    *   **Response Type**: `RedirectResponse` (302 Found)
    *   **Usage**:  Scan a dynamic QR code; this endpoint handles the redirect to the target URL and updates scan statistics.

*   **`PUT /api/v1/qr/{qr_id}`**:
    *   **Description**: Updates the redirect URL of a dynamic QR code.
    *   **Path Parameters**:
        *   `qr_id` (string): ID of the QR code to update.
    *   **Request Model**: `QRCodeUpdate`
    *   **Response Model**: `QRCodeResponse`
    *   **Request Body**:
        ```json
        {
          "redirect_url": "https://new-example.com"
        }
        ```
    *   **Usage**: Modify the destination URL of an existing dynamic QR code.

*   **`GET /api/v1/qr/{qr_id}/image`**:
    *   **Description**: Retrieves the QR code image as a streaming response.
    *   **Path Parameters**:
        *   `qr_id` (string): ID of the QR code.
    *   **Query Parameters**:
        *   `image_format` (string, optional): Image format for the QR code (`png`, `jpeg`, `jpg`, `svg`, `webp`). Default is `png`.
        *   `image_quality` (integer, optional): Quality for lossy image formats (JPEG, WebP), range 1-100.
    *   **Response Type**: `StreamingResponse` (image content)
    *   **Usage**: Download or display a QR code image in the specified format.

*   **`GET /api/v1/qr/{qr_id}`**:
    *   **Description**: Retrieves a specific QR code by its ID.
    *   **Path Parameters**:
        *   `qr_id` (string): ID of the QR code.
    *   **Response Model**: `QRCodeResponse`
    *   **Usage**: Fetch detailed information about a specific QR code.

### 7. Dependencies and Requirements

*   **Python 3.12+**
*   **FastAPI**
*   **SQLAlchemy 2.0**
*   **Uvicorn**
*   **qrcode**
*   **Pillow (PIL)**
*   **Pydantic**
*   **Alembic**
*   **pytest** (for testing)
*   **Docker**
*   **Docker Compose**
*   **Traefik** (optional, for reverse proxy and HTTPS)
*   **JavaScript** (for frontend)
*   **Bootstrap 5** (for frontend UI)

Dependencies are managed using `Poetry` (for backend) and `npm` (for frontend - listed in `package.json` for dev tooling).

### 8. Advanced Usage Examples

#### Customizing QR Code Appearance

You can customize the appearance of QR codes by modifying the following parameters when creating a QR code:

*   `fill_color`:  Set the color of the QR code modules (e.g., `"#007bff"` for blue).
*   `back_color`: Set the background color of the QR code (e.g., `"#f8f9fa"` for light gray).
*   `size`: Adjust the size of the QR code by increasing or decreasing the `size` parameter.
*   `border`: Change the width of the quiet zone (border) around the QR code using the `border` parameter.

Example (using `curl` to create a QR code with custom colors):

```bash
curl -X POST "https://localhost/api/v1/qr/static" \
     -H "Content-Type: application/json" \
     -d '{
           "content": "Custom QR Code",
           "qr_type": "static",
           "fill_color": "#28a745",
           "back_color": "#e0e0e0",
           "size": 12,
           "border": 2
         }'
```

#### Using Different Image Formats

You can retrieve QR code images in different formats by using the `image_format` query parameter when calling the `/api/v1/qr/{qr_id}/image` endpoint. Supported formats are `png`, `jpeg`, `svg`, and `webp`.

Example (retrieve a QR code image in SVG format):

```bash
<img src="https://localhost/api/v1/qr/{qr_id}/image?image_format=svg" alt="My QR Code in SVG">
```

#### Accessing Metrics and Logs

*   **Metrics:** Application metrics are exposed at the `/metrics` endpoint (e.g., `<https://localhost/metrics>`). These metrics are in Prometheus format and can be scraped by Prometheus for monitoring. Traefik also exposes its own metrics.
*   **Logs:**  Application logs are written in structured JSON format to `/logs/api` directory. Traefik access logs are written to `/logs/traefik`. Database operation logs are written to `/logs/database`. These logs can be accessed by mounting the `/logs` volume and inspecting the log files.

#### Configuring Security Settings

*   **CORS:** Cross-Origin Resource Sharing (CORS) is configured in `app/core/config.py` via `CORS_ORIGINS` and related settings.  By default, all origins are allowed (`["*"]`). In production, configure this to only allow your frontend domain.
*   **Trusted Hosts:** Trusted hosts middleware is enabled by default. Configure `TRUSTED_HOSTS` in `app/core/config.py` or via environment variables to specify allowed hostnames.
*   **HTTPS:** HTTPS is enabled via Traefik using Let's Encrypt for automatic certificate management (in production). For local development, self-signed certificates are used by default. Ensure your Traefik configuration (`traefik.yml` and `dynamic_conf.yml`) is set up correctly for HTTPS.

--- End of Documentation ---

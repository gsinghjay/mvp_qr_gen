## QR Code Generator API Documentation

### What is it?

This repository provides a REST API for generating and managing QR codes.
It supports creating both static and dynamic QR codes.
Dynamic QR codes offer redirect URLs and scan tracking.
The API is built with FastAPI and uses a SQLite database.

### Quick Start

1.  **Install Docker and Docker Compose.** Ensure Docker and Docker Compose are installed on your system.
2.  **Clone the repository.** Download or clone the repository to your local machine.
3.  **Navigate to the repository directory.** Open a terminal and navigate to the cloned repository's root directory.
4.  **Start the application.** Run `docker-compose up --build` to build and start the application using Docker Compose.
5.  **Access the API.** The API will be accessible at `http://localhost`.
6.  **View Documentation.** Access the interactive API documentation at `http://localhost/docs`.

### Configuration

The API is configured using environment variables and a `.env` file.
Configuration settings are defined in `app/core/config.py`.

**Available Configuration Options:**

*   **DATABASE_URL:**  Database connection string. Defaults to `sqlite:///./data/qr_codes.db`.
*   **ENVIRONMENT:**  Environment mode. Defaults to `development`. Can be set to `production` or `test`.
*   **DEBUG:**  Debug mode for FastAPI. Defaults to `False`.
*   **TRUSTED_HOSTS:**  List of trusted hosts. Defaults to `["*"]`.
*   **CORS_ORIGINS:**  List of allowed CORS origins. Defaults to `["*"]`.
*   **CORS_HEADERS:**  List of allowed CORS headers. Defaults to `["*"]`.
*   **ENABLE_GZIP:**  Enable GZip compression. Defaults to `True`.
*   **GZIP_MIN_SIZE:**  Minimum size for GZip compression. Defaults to `1000` bytes.
*   **ENABLE_METRICS:**  Enable metrics collection. Defaults to `True`.
*   **ENABLE_LOGGING:**  Enable request logging. Defaults to `True`.
*   **METRICS_ENDPOINT:**  Endpoint for Prometheus metrics. Defaults to `/metrics`.
*   **LOG_LEVEL:**  Application log level. Defaults to `INFO`.

**Configuration Methods:**

*   **Environment Variables:**  Set environment variables directly in your shell or Docker environment.
*   **.env File:** Create a `.env` file in the root directory with key-value pairs for configuration.

### API Endpoints

#### QR Code Operations

*   **`GET /api/v1/qr`**
    *   **Summary:** List QR codes with pagination and optional filtering.
    *   **Query Parameters:**
        *   `skip` (integer, optional):  Number of items to skip for pagination. Default: `0`.
        *   `limit` (integer, optional): Maximum number of items per page. Default: `10`.
        *   `qr_type` (string, optional): Filter by QR code type (`static` or `dynamic`).
    *   **Response:** Returns a list of `QRCodeResponse` objects with pagination metadata.

*   **`POST /api/v1/qr/static`**
    *   **Summary:** Create a new static QR code.
    *   **Request Body:** `QRCodeCreate` schema. `redirect_url` should be `null` or omitted.
    *   **Response:** Returns the created `QRCodeResponse` object.

*   **`POST /api/v1/qr/dynamic`**
    *   **Summary:** Create a new dynamic QR code.
    *   **Request Body:** `QRCodeCreate` schema. `redirect_url` is required.
    *   **Response:** Returns the created `QRCodeResponse` object.

*   **`GET /r/{short_id}`**
    *   **Summary:** Redirect to the URL associated with a dynamic QR code.
    *   **Path Parameter:**
        *   `short_id` (string): Short identifier from the QR code content.
    *   **Response:**  302 Redirect to the target URL.

*   **`PUT /api/v1/qr/{qr_id}`**
    *   **Summary:** Update the redirect URL of a dynamic QR code.
    *   **Path Parameter:**
        *   `qr_id` (string): ID of the QR code to update.
    *   **Request Body:** `QRCodeUpdate` schema.
    *   **Response:** Returns the updated `QRCodeResponse` object.

*   **`GET /api/v1/qr/{qr_id}/image`**
    *   **Summary:** Get the QR code image.
    *   **Path Parameter:**
        *   `qr_id` (string): ID of the QR code.
    *   **Query Parameters:**
        *   `image_format` (string, optional): Image format (`png`, `jpeg`, `jpg`, `svg`, `webp`). Default: `png`.
        *   `image_quality` (integer, optional): Image quality for lossy formats (1-100).
    *   **Response:** Returns the QR code image in the specified format.

*   **`GET /api/v1/qr/{qr_id}`**
    *   **Summary:** Get QR code data by ID.
    *   **Path Parameter:**
        *   `qr_id` (string): ID of the QR code.
    *   **Response:** Returns the `QRCodeResponse` object.

#### Home Page

*   **`GET /`**
    *   **Summary:** Render the admin dashboard HTML page.
    *   **Response:** Returns the HTML content of the dashboard.

### Dependencies and Requirements

*   **Python 3.12+**
*   **FastAPI**
*   **SQLAlchemy**
*   **Uvicorn**
*   **qrcode**
*   **Pillow (PIL)**
*   **Pydantic**
*   **Alembic**
*   **Docker**
*   **Docker Compose**

Dependencies are managed using `requirements.txt` and `pyproject.toml`.

### Advanced Usage Examples

**1. Create a Static QR Code using `curl`:**

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "content": "This is a static QR code example",
    "qr_type": "static",
    "fill_color": "#007bff",
    "back_color": "#f8f9fa",
    "size": 15,
    "border": 2
  }' \
  https://localhost/api/v1/qr/static
```

**2. Create a Dynamic QR Code using `httpie`:**

```bash
http POST https://localhost/api/v1/qr/dynamic \
  content="My Dynamic Link" \
  qr_type="dynamic" \
  redirect_url="https://example.com/your-redirect-url" \
  fill_color="#ffc107" \
  back_color="#343a40" \
  size=10 \
  border=3
```

**3. Update a Dynamic QR Code Redirect URL using `curl`:**

```bash
QR_ID="your_qr_code_id" # Replace with the actual QR code ID
curl -X PUT \
  -H "Content-Type: application/json" \
  -d '{
    "redirect_url": "https://new-destination.com"
  }' \
  https://localhost/api/v1/qr/$QR_ID
```

**4. Get a QR Code Image in WebP format using `wget`:**

```bash
QR_ID="your_qr_code_id" # Replace with the actual QR code ID
wget https://localhost/api/v1/qr/$QR_ID/image?image_format=webp -O qr_code.webp
```

**5. List QR Codes using `curl` and `jq` to parse JSON:**

```bash
curl https://localhost/api/v1/qr | jq '.items[] | {id, qr_type, created_at}'
```

These examples demonstrate basic interactions with the API for creating, updating, and retrieving QR codes and their images. You can adapt these examples and explore other API endpoints for more advanced use cases.

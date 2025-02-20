# Technical Specification

## System Overview
The system is a QR code management application built using FastAPI, SQLAlchemy 2.0, and PostgreSQL. It allows users to create, manage, and interact with both static and dynamic QR codes. The application is containerized using Docker and follows Test Driven Development (TDD) practices. It adheres to code quality tools like ruff, mypy, and black, and follows SOLID principles.

### Main Components
- **Frontend**: Handles user interactions and displays data.
- **Backend**: Implements business logic using FastAPI.
- **Database**: Stores QR code data using PostgreSQL.
- **Configuration Management**: Handles environment-specific configurations.
- **Logging**: Records events and errors using Python's `logging` module.
- **CI/CD**: Automates the release process using GitHub Actions and `python-semantic-release`.

## Core Functionality

### Primary Features

1. **Dynamic QR Code Handling**
   - **Function: `redirect_qr` (redirect.py)**
     - **Description:** Handles redirection logic for dynamic QR codes. Retrieves the QR code from the database, validates the redirect URL, updates scan statistics, logs the scan event, and performs the actual redirection.
     - **Importance Score:** 90

2. **Static QR Code Management**
   - **Function: `create_static_qr` (static.py)**
     - **Description:** Creates a new static QR code. Validates input data, creates a new `QRCode` instance, adds it to the database, and logs the creation event.
     - **Importance Score:** 80

3. **Dynamic QR Code Management**
   - **Function: `create_dynamic_qr` (dynamic.py)**
     - **Description:** Creates a new dynamic QR code. Validates input data, generates a short unique identifier for the redirect path, creates a new `QRCode` instance, adds it to the database, and logs the creation event.
     - **Importance Score:** 90
   - **Function: `update_dynamic_qr` (dynamic.py)**
     - **Description:** Updates an existing dynamic QR code's redirect URL. Retrieves the QR code by ID, validates input data, updates the redirect URL, and logs the update event.
     - **Importance Score:** 85

4. **QR Code Retrieval**
   - **Function: `get_qr_by_id` (common.py)**
     - **Description:** Retrieves a QR code by its ID from the database. Includes error handling for database errors and raises HTTP exceptions for not found scenarios.
     - **Importance Score:** 85

5. **Database Management**
   - **Function: `DatabaseManager.__init__` (manage_db.py)**
     - **Description:** Initializes the `DatabaseManager` with database path, backup directory, and Alembic INI file. Ensures directories exist and initializes loggers.
     - **Importance Score:** 90
   - **Function: `DatabaseManager.run_migrations` (manage_db.py)**
     - **Description:** Runs database migrations. Runs all migrations for a fresh database or pending migrations for an existing database.
     - **Importance Score:** 90

6. **API Endpoints**
   - **Function: `list_qr_codes` (api/v1.py)**
     - **Description:** Lists QR codes with pagination and optional filtering. Queries the database for QR codes, applies filters, and returns a paginated list.
     - **Importance Score:** 90
   - **Function: `get_qr` (api/v1.py)**
     - **Description:** Retrieves QR code data by ID. Uses `get_qr_by_id` to fetch QR code data from the database.
     - **Importance Score:** 85
   - **Function: `update_qr` (api/v1.py)**
     - **Description:** Updates QR code data by ID. Updates the `redirect_url` field for dynamic QR codes.
     - **Importance Score:** 85

### Complex Business Logic
- **URL Validation:** Ensures that URLs have a scheme and network location.
- **Atomic Updates:** Uses SQLAlchemy's ORM to atomically update QR code attributes.
- **Error Handling:** Comprehensive try-except blocks to handle various exceptions, log errors, and raise appropriate HTTP exceptions.
- **UUID Generation:** Generates a short unique identifier for dynamic QR codes using `uuid.uuid4()`.

## Architecture

### Data Flow
1. **User Request:** A user makes a request to create, update, or retrieve a QR code via the API.
2. **API Handling:** The request is handled by the appropriate FastAPI endpoint (e.g., `create_dynamic_qr`, `get_qr`).
3. **Database Interaction:** The endpoint interacts with the PostgreSQL database using SQLAlchemy ORM to perform CRUD operations.
4. **Business Logic Execution:** Complex business logic (e.g., URL validation, atomic updates) is executed within the endpoint functions.
5. **Response:** The endpoint returns a response to the user, which may include the created/updated QR code data or a list of QR codes.
6. **Logging:** All operations are logged using Python's `logging` module for auditing and debugging purposes.

### Containerization
- The application is containerized using Docker. The `Dockerfile` defines the steps to build the Docker image, and `docker-compose.yml` configures the services (e.g., API, Traefik) and their interactions.

### Configuration Management
- Environment-specific configurations are managed using `settings` and `dynamic_conf.yml` for Traefik. The `pyproject.toml` file configures various Python project tools (e.g., pytest, black, ruff, mypy).
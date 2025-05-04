# API Structure

This directory contains the new API structure for the QR Code Generator application. It follows modern FastAPI best practices with proper versioning and resource-based organization.

## Directory Structure

```
app/api/
├── __init__.py       # Main API router initialization
├── README.md         # This file
└── v1/               # API version 1
    ├── __init__.py   # Version 1 router initialization
    └── endpoints/    # API endpoints organized by resource
        ├── health.py # Health check endpoints
        ├── qr.py     # QR code related endpoints
        ├── pages.py  # Web page endpoints
        └── redirect.py # QR code redirect endpoint
```

## Organization

### API Versioning

The API is organized by version (currently v1) to allow for future changes without breaking backward compatibility. All versioned API routes are prefixed with `/api/v1/`.

### Resource-Based Organization

Endpoints are organized by resource rather than operation type:
- `health.py`: Health check endpoints
- `qr.py`: All QR code related endpoints (create, read, update, delete)
- `pages.py`: Web page endpoints
- `redirect.py`: QR code redirect endpoint

### Router Structure

The router hierarchy is as follows:
1. Top-level API router (`api_router` in `__init__.py`)
2. Version-specific router (`api_v1_router` in `v1/__init__.py`)
3. Resource-specific routers in each endpoint file

Additionally, there are non-API routers:
- `web_router`: For serving web pages
- `redirect_router`: For QR code redirects under `/r/{short_id}`

## Migration from Old Structure

This API structure replaces the old router organization in `app/routers/`. All endpoints have been migrated:

- `app/routers/health.py` → `app/api/v1/endpoints/health.py`
- `app/routers/api/v1.py` → `app/api/v1/endpoints/qr.py`
- `app/routers/qr/static.py` → `app/api/v1/endpoints/qr.py`
- `app/routers/qr/dynamic.py` → `app/api/v1/endpoints/qr.py`
- `app/routers/qr/redirect.py` → `app/api/v1/endpoints/redirect.py`
- `app/routers/web/pages.py` → `app/api/v1/endpoints/pages.py`

## Best Practices Implemented

- **Modern API Versioning**: Proper versioning structure with `/api/v1/` prefix
- **Resource-Based Organization**: Endpoints grouped logically by resource
- **Router Nesting**: Clean hierarchy of routers with appropriate prefixes
- **Path Consistency**: Maintained backward compatibility with existing paths
- **Separation of Concerns**: Clear distinction between API and non-API routes
- **Documentation**: Comprehensive docstrings and API metadata

## Key Features

- **Versioning**: API is properly versioned with `/api/v1/...` prefixes
- **Resource-Based Organization**: Endpoints are organized by resource type
- **Modern Dependency Injection**: Uses `Annotated[Type, Depends()]` syntax
- **Type Safety**: Leverages modern Python type hints for better IDE support and runtime checking
- **Clean Dependencies**: Uses simplified dependency injection approach
- **API Documentation**: Improved organization in Swagger UI and ReDoc

## Endpoints

### Health Check

- `GET /api/v1/health` - Comprehensive health check of the application

### QR Code Endpoints

- `GET /api/v1/qr` - List all QR codes with optional filtering and pagination
- `GET /api/v1/qr/{qr_id}` - Get a specific QR code by ID
- `GET /api/v1/qr/{qr_id}/image` - Get a QR code image with optional customization
- `POST /api/v1/qr/static` - Create a new static QR code
- `POST /api/v1/qr/dynamic` - Create a new dynamic QR code
- `PUT /api/v1/qr/{qr_id}` - Update a QR code
- `DELETE /api/v1/qr/{qr_id}` - Delete a QR code

## Migration

The migration to this new structure has been fully completed. The old router structure has been removed, and all endpoints are now served through this new structure.

For more details on the migration process, see the [API Restructure Migration Plan](../../docs/plans/api_restructure_migration_plan.md). 
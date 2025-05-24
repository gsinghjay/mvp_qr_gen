# Technical Context: QR Code Generator

## Technologies Used

### Backend
- **Python 3.12**: Primary programming language
- **FastAPI**: Web framework for API and web UI
- **SQLAlchemy**: ORM for database operations
- **Alembic**: Database migration tool
- **Pydantic**: Data validation and settings management
- **Jinja2**: Template engine for web UI
- **Segno**: QR code generation library
- **pytest**: Testing framework

### Frontend
- **HTMX**: Dynamic frontend interactions
- **Bootstrap 5**: CSS framework for responsive design
- **Alpine.js**: Reactive UI components (for analytics)
- **Chart.js**: Data visualization (for analytics)
- **Vanilla JavaScript**: Minimal client-side scripting

### Database
- **PostgreSQL 15**: Primary relational database
- **psycopg2-binary**: Synchronous database driver
- **asyncpg**: Asynchronous driver for testing
- **Dedicated Test Database**: Isolated PostgreSQL instance for testing

### Infrastructure
- **Docker**: Containerization
- **Docker Compose**: Container orchestration
- **Traefik**: Edge router, reverse proxy, and security gateway
- **TLS/HTTPS**: Wildcard certificate for *.hccc.edu
- **IP-based Access Control**: Network-level security via Traefik

### Observatory-First Monitoring Stack
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **Loki**: Log aggregation
- **Promtail**: Log collection agent
- **Alert System**: Comprehensive alerting for business, performance, and infrastructure

### Observatory-First Monitoring Stack
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **Loki**: Log aggregation
- **Promtail**: Log collection agent
- **Alert System**: Comprehensive alerting for business, performance, and infrastructure

### Observatory-First Monitoring Stack
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **Loki**: Log aggregation
- **Promtail**: Log collection agent
- **Alert System**: Comprehensive alerting for business, performance, and infrastructure
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **Loki**: Log aggregation
- **Promtail**: Log collection agent
- **Alert System**: Comprehensive alerting for business, performance, and infrastructure

## Development Setup

### Prerequisites
- Python 3.12
- Docker and Docker Compose
- Git

### Setup Steps
```bash
# Clone repository
git clone <repository-url>
cd qr-app

# Create .env file (sample provided as .env.example)
cp .env.example .env

# Start the application with Docker Compose
docker-compose up --build
```

### Configuration
- **Environment Variables**: Primary configuration method (`.env` file)
- **Config Classes**: Pydantic `BaseSettings` in `app/core/config.py`
- **Dependency Injection**: Configured in `app/dependencies.py`
- **Traefik Configuration**: Static config in `traefik.yml`, dynamic config in `dynamic_conf.yml`

## Technical Constraints

### Database Architecture
- **PostgreSQL-only**: Production and dedicated test databases
- **Transaction Isolation**: Test database uses transaction rollback for isolation
- **Synchronous Operations**: Excellent performance (<30ms) with current implementation

### Security Model: Edge Gateway Pattern
- **Traefik as Single Source of Truth**: All security decisions at edge gateway level
- **No Application Authentication**: Application accepts all requests that pass Traefik
- **Network-Level Controls**: IP allowlisting, basic auth, path-based restrictions
- **Security Headers**: Managed by Traefik middleware

### Container Networking
- **Docker Network**: `qr_generator_network` for internal service communication
- **Health Checks**: Container readiness verification
- **Non-root User**: Container runs as `appuser` for security

## Dependencies and Libraries

### Core Dependencies
```
fastapi[all]>=0.109.2
uvicorn>=0.23.2
sqlalchemy>=2.0.27
alembic>=1.12.0
pydantic>=2.6.1
jinja2>=3.1.2
segno[pil]>=1.6.0
pillow>=10.2.0
```

### Database Tools
```
psycopg2-binary>=2.9.9
asyncpg>=0.30.0  # For testing
```

### Testing Dependencies
```
pytest>=8.0.0
pytest-asyncio>=0.21.1
httpx>=0.25.0
factory-boy>=3.3.0
```

### Development Tools
```
black>=24.2.0
ruff>=0.3.0
mypy>=1.8.0
```

### Frontend Libraries (CDN)
- HTMX 1.9.10+
- Bootstrap 5.3.2+
- Alpine.js 3.13.3+
- Chart.js 4.4.1+

## Tool Usage Patterns

### Dependency Injection
- FastAPI's `Depends()` system with type aliases in `app/types.py`
- `Annotated` syntax for improved type hints
- Example: `qr_service: QRServiceDep`

### FastAPI Lifespan for Performance
- Pre-initializes dependencies during startup
- Eliminates cold-start performance penalties
- Triggers key code paths with minimal operations

### Repository Pattern
- `BaseRepository[ModelType]` for type-safe CRUD operations
- Specific repositories extend base for model-specific operations
- Services depend on repositories, not direct database access

### Path Handling
- `pathlib.Path` for platform-independent paths
- Context-aware resolution for Docker containers and local development

### Background Tasks
- FastAPI's `BackgroundTasks` for non-blocking operations
- Example: Scan logging happens in background during redirects

### Exception Handling
- Custom exceptions in `app/core/exceptions.py`
- Repository layer: SQLAlchemyError → DatabaseError translation
- Global handlers: Exception → HTTP response translation

### Security Pattern: Edge Gateway
- Traefik handles all security as single source of truth
- IP-based restrictions via Traefik middleware
- Path-based access control via routing rules
- Application focuses on business logic, not security

## Deployment and Infrastructure

### Docker Infrastructure
- Multi-stage Docker build for optimized container size
- Multiple containers: `api`, `traefik`, `postgres`, `postgres_test`, `prometheus`, `grafana`, `loki`, `promtail`
- Named volumes for persistent data storage
- Health checks for service readiness
- Observatory stack for comprehensive monitoring and alerting

### Traefik Configuration
- **Static config** (`traefik.yml`): Entrypoints, providers, metrics, logging
- **Dynamic config** (`dynamic_conf.yml`): Routing rules, middleware, services, TLS

### Networking and Domains
- **Internal network**: 10.1.6.12
- **Public IPs**: 
  - 130.156.44.52 (web.hccc.edu - Main application)
  - 130.156.44.53 (auth.hccc.edu - Prepared for Keycloak)
- **Wildcard certificate**: *.hccc.edu

### Security Implementation
- **IP Allowlisting**: Administrative endpoints protected by IP restrictions
- **Basic Authentication**: Protected routes require credentials via Traefik
- **Network Isolation**: Docker network restricts container communication
- **TLS Termination**: All external traffic encrypted via Traefik

### Authentication Flow
1. Traefik processes incoming requests
2. Security middleware applied based on path and IP
3. Protected paths require basic authentication headers
4. Admin endpoints require allowlisted IP addresses
5. Authenticated requests forwarded to FastAPI application

## Database Migration Practices

### Alembic Migration Pattern
- Manual migration creation for schema changes
- Non-destructive changes with default values
- Pre-migration backups stored in `/backups` directory
- Version control for all migration files

### Test Database Isolation
- **Implementation**: Dedicated PostgreSQL test service
- **Environment Detection**: `TESTING_MODE=true` and `TEST_DATABASE_URL`
- **Transaction Isolation**: Each test runs in rollback transaction
- **Benefits**: Clean state between tests, parallel execution support

## Test Execution

### Container-Based Testing
**CRITICAL**: All tests must be run inside the Docker container, not on the host system.

```bash
# Run all tests
docker-compose exec api pytest

# Run tests with coverage
docker-compose exec api pytest --cov=app

# Run specific test categories
docker-compose exec api pytest app/tests/integration/
docker-compose exec api pytest app/tests/unit/

# Run with short traceback for cleaner output
docker-compose exec api pytest --tb=short
```

### Test Environment Requirements
- **Docker containers must be running**: `docker-compose up -d`
- **Test database service**: `postgres_test` container provides isolated test database
- **Environment variables**: Automatically configured for container environment
- **Dependencies**: All Python packages and database connections available in container

## Code Style & Standards

### Python Code Guidelines
- Use **Python 3.12** features and type hints throughout
- Follow **PEP 8** with 100-character line length
- Use **SQLAlchemy 2.0** syntax (avoid legacy 1.x patterns)
- Prefer **Pydantic v2** for data validation and serialization
- Use **UTC timezone** for all datetime operations
- Implement proper **error handling** with custom exceptions

### FastAPI Patterns
- Use **dependency injection** for services and repositories
- Implement **repository pattern** for data access
- Create **service layer** for business logic
- Use **Pydantic models** for request/response validation
- Apply **router organization** by feature/domain

### Database Guidelines
- Use **timezone-aware timestamps** (UTCDateTime custom type)
- Implement **proper foreign keys** with CASCADE where appropriate
- Create **database migrations** using Alembic
- Use **repository pattern** to abstract database operations
- Apply **proper indexing** for performance

### Frontend Guidelines
- Use **HTMX** for dynamic interactions
- Implement **Alpine.js** for client-side reactivity
- Follow **Bootstrap 5** component patterns
- Create **reusable Jinja2 template fragments**
- Ensure **accessibility** with proper ARIA attributes

## Refactoring Implementation Patterns

### Service Layer Interface Pattern
```python
# Interface Definition
from abc import ABC, abstractmethod

class QRCodeGenerator(ABC):
    @abstractmethod
    def generate(self, content: str, **options) -> QRCodeData:
        pass

# Implementation
class SegnoQRCodeGenerator(QRCodeGenerator):
    def generate(self, content: str, **options) -> QRCodeData:
        # Implementation using Segno
        pass

# Service Using Interface
class QRGenerationService:
    def __init__(self, generator: QRCodeGenerator):
        self.generator = generator
```

### Feature Flag Pattern
```python
# In config.py
USE_NEW_SERVICE: bool = os.getenv("USE_NEW_SERVICE", "false").lower() == "true"

# In service implementation
if settings.USE_NEW_SERVICE:
    try:
        result = new_service.method()
        MetricsLogger.log_service_call("NewService", "method", duration, True)
        return result
    except Exception as e:
        logger.error(f"New service failed, falling back: {e}")
        # Fall through to old implementation
return old_service.method()
```

### Circuit Breaker Pattern
```python
try:
    result = new_service_method()
    return result
except Exception as e:
    logger.error(f"New service failed: {e}")
    return fallback_method()
```

## Segno Library Optimizations

### SVG Optimizations
```python
# Use these parameters for SVG generation
qr.save(output, kind="svg", 
        xmldecl=False,
        svgns=False, 
        svgclass=None,
        lineclass=None,
        omitsize=True,
        nl=False)
```

### Enhanced Color Controls
```python
# Support enhanced color options
qr.save(output, 
        dark="#000000",
        light="#FFFFFF", 
        data_dark="#333333",
        data_light="#CCCCCC")
```

### Physical Dimensions
```python
# Support unit-based sizing
qr.save(output, kind="svg", unit="mm", scale=2.0)
```

## Error Handling Patterns

### Custom Exceptions
```python
class QRCodeNotFoundError(AppBaseException):
    status_code = 404

class QRCodeValidationError(AppBaseException):
    status_code = 422
```

### Service Error Handling
```python
try:
    result = service_operation()
    return result
except ValidationError as e:
    raise QRCodeValidationError(detail=e.errors())
except DatabaseError as e:
    logger.error(f"Database error: {e}")
    raise
```

## Observatory-First Monitoring and Alerting

### Comprehensive Alert System
- **8 Critical Alert Rules**: Covering business, performance, and infrastructure
- **Business-Critical Alerts**: QR redirect failures (>10%), API errors (>5%), container health
- **Performance Alerts**: API latency (>1s), performance regression (>500ms), baseline deviation (>150%)
- **Infrastructure Alerts**: Memory usage (>90%), database issues, unusual traffic patterns
- **Alert Testing**: Automated validation via `scripts/test_alerts.sh`
- **Documentation**: Complete alert rationale in `docs/observatory-first-alerts.md`

### Monitoring Stack Configuration
```yaml
# Prometheus configuration
prometheus:
  scrape_configs:
    - job_name: 'traefik'
      targets: ['traefik:8082']
    - job_name: 'qr-app'
      targets: ['api:8000']
  rule_files:
    - "alerts.yml"

# Grafana dashboards
- QR System Health Overview
- QR System Refactoring Progress  
- QR Analytics Deep Dive
```

### Alert Rule Examples
```yaml
# Business-critical QR redirect monitoring
- alert: QRRedirectFailureRate
  expr: (non-30x responses / total responses) > 0.10
  for: 2m
  labels:
    severity: critical
    component: qr_redirects

# Performance regression detection
- alert: PerformanceRegression
  expr: histogram_quantile(0.95, response_time) > 0.5
  for: 5m
  labels:
    severity: warning
    component: performance
    refactoring: "true"
```

## Monitoring and Logging Patterns

### Structured Logging
```python
logger.info("QR code created", extra={
    "qr_id": qr.id,
    "qr_type": qr.qr_type,
    "user_ip": client_ip,
    "timestamp": datetime.now(UTC).isoformat()
})
```

### Performance Metrics
```python
MetricsLogger.log_service_call(
    service_name="QRGenerationService",
    method_name="create_static_qr", 
    duration=execution_time,
    success=True
)
```

## File Organization During Refactoring

### New Files to Create
- `app/services/interfaces/` - Abstract base classes
- `app/adapters/` - Implementation of interfaces
- `app/services/new_*_service.py` - New service implementations
- `app/utils/monitoring.py` - Metrics and performance logging

### Existing Files to Modify Carefully
- `app/services/qr_service.py` - Add feature flags, don't break existing
- `app/api/v1/endpoints/redirect.py` - CRITICAL: Don't break QR redirects
- `app/repositories/*.py` - Add new methods, don't modify existing


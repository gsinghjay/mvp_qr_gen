# QR Code Generator Infrastructure

## Architecture Overview

The QR Code Generator is deployed as a container-based application with the following components:

```mermaid
graph TD
    User["User (Browser)"] --> |HTTPS| Traefik["Traefik (Edge Gateway)"]
    
    subgraph "Docker Infrastructure"
        Traefik --> |Forward requests| FastAPI["FastAPI Application"]
        
        FastAPI --> |Read/Write| SQLiteVolume["SQLite Volume (qr_data)"]
    end
    
    Traefik --> |Enforces| Security["Security Controls:<br>- IP Allowlisting<br>- Path-Based Rules<br>- Rate Limiting<br>- TLS"]
```

## Infrastructure Components

### Containers and Services

| Service              | Image/Build                   | Main Purpose                               | Ports      | Volumes               |
|----------------------|-------------------------------|--------------------------------------------|-----------|-----------------------|
| `traefik`            | traefik:v2.10                 | Edge gateway, routing, TLS termination     | 80, 443   | traefik-certificates  |
| `qr-app`             | Built from Dockerfile         | QR code generation and management API      | None (internal) | qr_data          |

### Networks

| Network Name   | Purpose                                      | Connected Services           |
|----------------|----------------------------------------------|-----------------------------|
| `traefik_net`  | Communication between Traefik and services   | traefik, qr-app             |

### Volumes

| Volume Name           | Purpose                                         | Used By            |
|-----------------------|-------------------------------------------------|--------------------|
| `qr_data`             | Persistent storage for SQLite DB and QR images  | qr-app             |
| `traefik-certificates`| Storage for Let's Encrypt certificates          | traefik            |

## Security Model

The application uses a network-level security model:

1. **Edge Security at Traefik**:
   - IP allowlisting restricts access to administrative endpoints
   - Path-based rules control which endpoints are publicly accessible
   - TLS termination ensures encrypted traffic
   - Rate limiting protects against abuse
   - Security headers protect against common web vulnerabilities

2. **Application Access Control**:
   - Administrative endpoints are restricted to trusted network IPs
   - Public QR redirect endpoints (`/r/{short_id}`) are accessible to all
   - No user-level authentication is required

3. **Network Isolation**:
   - Container services communicate on internal networks only
   - Only Traefik is exposed to the host network

## Traefik Configuration

Traefik is configured using two files:

1. **`traefik.yml`** (static configuration):
   - Global settings, entrypoints, providers
   - TLS configuration and certificate storage
   - Logging and metrics

2. **`dynamic_conf.yml`** (dynamic configuration):
   - Router definitions for each service
   - Middleware chains
   - Service backends

### Middleware Stack

```mermaid
graph TD
    Request["HTTP Request"] --> TLS["TLS Termination"]
    TLS --> IPFilter["IP Allowlist<br>(for admin routes)"]
    IPFilter --> Headers["Security Headers"]
    Headers --> RateLimit["Rate Limiting<br>(per-client IP)"]
    RateLimit --> Compress["Compression"]
    Compress --> Service["QR App Service"]
```

## Database Management

The application uses SQLite for data persistence:

- Database file stored on `qr_data` volume
- WAL mode enabled for better concurrency
- Automated backups via scheduled tasks
- Migrations managed by Alembic

### Backup Strategy

- Hourly backups stored inside container
- Daily backups copied to the host via volume mapping to `./backups`
- Standard SQLite `.backup` command used
- Retention policy: 24 hourly backups, 7 daily backups

## Deployment Process

```mermaid
flowchart TD
    A[Code Changes] --> B[Build Image]
    B --> C[Test Image]
    C --> D[Push to Registry]
    D --> E[Deploy with Docker Compose]
    E --> F[Initialize Database if Needed]
    F --> G[Run Migrations]
    G --> H[Verify Health Endpoints]
```

### Initial Deployment

```bash
# Clone the repository
git clone https://github.com/your-org/qr-code-generator.git
cd qr-code-generator

# Set up environment variables
cp .env.example .env
# Edit .env with your environment-specific values

# Start the services
docker-compose up -d

# Verify deployment
curl http://localhost/health
```

### Updates

```bash
# Pull the latest changes
git pull

# Rebuild and restart the services
docker-compose down
docker-compose build
docker-compose up -d

# Run migrations if needed
docker-compose exec qr-app python -m app.scripts.manage_db migrate
```

## Monitoring and Maintenance

### Health Checks

- `/health` endpoint provides basic service health and database connectivity
- `/metrics` exposes Prometheus metrics

### Logging

- Structured JSON logging to stdout/stderr
- Log level configurable via environment variables
- Request logging includes request ID, path, method, status, duration

### Performance Considerations

- SQLite WAL mode improves concurrency
- QR code generation is CPU-intensive but quick
- Image caching reduces regeneration overhead
- Rate limiting prevents abuse

## Disaster Recovery

1. **Database Corruption**:
   - Restore from the latest backup in `./backups`
   - Run migrations to ensure schema is up-to-date

2. **Container Failure**:
   - Services will restart automatically (restart policy)
   - Data persists on named volumes

3. **Complete System Recovery**:
   - Reinstall Docker and Docker Compose
   - Clone repository and restore environment files
   - Restore database backup to the appropriate location
   - Restart services

## Future Improvements

1. **Monitoring Enhancement**:
   - Add Prometheus/Grafana integration
   - Set up alerting for critical metrics

2. **Security Hardening**:
   - Regular security scanning of Docker images
   - Implementation of more granular access controls

3. **Scalability**:
   - Consider database sharding for high-volume deployments
   - Implement caching layer for frequently accessed QR codes
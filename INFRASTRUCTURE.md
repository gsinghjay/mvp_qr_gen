# Docker Infrastructure Flow Diagram

```mermaid
flowchart TD
    %% External Users/Systems
    USER((External User)) --> ENTRY
    
    subgraph traefik["Traefik Routing"]
        direction LR
        ENTRY["EntryPoints: web(:80), websecure(:443), traefik(:8080), metrics(:8082)"]
        ROUTERS["Routers: api-rtr, keycloak-rtr (HTTP/HTTPS)"]
        SERVICES["Services: api-svc(:8000), keycloak-svc(:8080)"]
        ENTRY --> ROUTERS --> |"TLS"| SERVICES
    end
    
    traefik --> dockerfile
    traefik --> keycloak

    subgraph keycloak["Authentication System"]
        direction LR
        KC["Keycloak Service"] --> KC_DB[("PostgreSQL DB")]
        KC_DB --> KC_VOL["Volume: keycloak_postgres_data"]
        KC --> KC_REALM["Realm: qr_code_realm"]
        KC_REALM --> KC_CLIENTS["Client: qr_code_app"]
        KC_REALM --> KC_IDP["Identity Provider: Azure AD"]
    end

    subgraph dockerfile["Docker Build"]
        direction LR
        subgraph builder["Builder Stage"]
            B["python:3.12-slim + gcc, python3-dev + venv + requirements.txt"]
        end
        
        subgraph runtime["Runtime Stage"]
            R["python:3.12-slim + curl, sqlite3 + application code + scripts"]
            ENV["ENV: PORT=8000, WORKERS=4, PYTHONPATH=/app"]
            HEALTH["Healthcheck: /health endpoint (30s interval)"]
        end
        
        builder --> runtime
    end
    
    dockerfile --> compose
    
    subgraph compose["Docker Compose"]
        direction LR
        subgraph services["Services"]
            API["API Service"] 
            PROXY["Traefik Proxy"]
            AUTH["Keycloak Auth Service"]
            POSTGRES["PostgreSQL Database"]
        end
        
        subgraph env["Environment"]
            direction LR
            subgraph DEV["Development (default)"]
                DEV_FEATURES["Features: Hot reload, Debug, App mounting, Detailed logs"]
                TEST_MODE["Testing: In-memory SQLite, Coverage reporting"]
            end
            
            PROD["Production: No hot reload, Optimized perf, Enhanced security"]
        end
        
        subgraph storage["Storage & Network"]
            direction LR
            DB[("SQLite DB")] --- VOLUMES["Volumes: data, logs, keycloak_postgres_data"]
            NET["Network: qr_generator_network (bridge)"]
        end
        
        services --> env --> storage
    end
    
    SERVICES --> API
    SERVICES --> KC
    
    %% Logging Flow
    subgraph logs["Logging"]
        direction LR
        LOG_VOL["./logs → /logs"]
        LOG_DIRS["Subdirectories: api, database, traefik, keycloak"]
        API & DB & PROXY & KC -- "Logs" --> LOG_VOL --> LOG_DIRS
    end
```

# Environment Configuration Notes

## Development Mode (Default)
- Features:
  - Hot reloading and debug features enabled
  - App directory mounted for live changes
  - Detailed logging for development
  - Testing with in-memory SQLite (run with `docker compose exec api pytest --cov -v`)

## Production Mode
- Enable by changing `ENVIRONMENT=production` in docker-compose.yml
- Features:
  - Hot reloading disabled
  - Optimized performance settings
  - Enhanced security features
  - Production-level logging

## Directory Structure
- `data/`: Contains SQLite database and backups
  - `backups/`: Database backup files
  - `logs/`: Application data logs
- `logs/`: Container logs
  - `api/`: API service logs
  - `database/`: Database operation logs
  - `traefik/`: Traefik proxy logs
  - `keycloak/`: Keycloak authentication logs
- `certificates/`: TLS certificates for secure connections
- `certs/`: Keycloak-specific certificates

# Traefik Routing Configuration

## Naming Conventions
- **Router Naming**: Use `-rtr` suffix (e.g., `api-rtr`, `keycloak-rtr`)
- **Service Naming**: Use `-svc` suffix (e.g., `api-svc`, `keycloak-svc`) 
- **Explicit Binding**: Always bind routers to services explicitly:
  ```yaml
  traefik.http.routers.service-name-rtr.service=service-name-svc
  ```

## Priority Management
- Base services (API): Priority 10-50
- Specialized services (Auth): Priority 100-200
- Always set explicit priority to prevent routing conflicts

## Path-Based Routing
- API service: `PathPrefix(/) && !PathPrefix(/kc)`
- Keycloak service: `PathPrefix(/kc)`
- Use higher priority for more specific routes

## Required Headers
- Authentication services need specific headers:
  ```yaml
  traefik.http.middlewares.keycloak-headers.headers.customrequestheaders.X-Forwarded-Proto=https
  ```

# Authentication Architecture

## Keycloak as Identity Provider
- Keycloak acts as the central authentication service
- Handles all aspects of authentication and authorization
- Integrates with external identity providers (Azure AD)
- Provides token-based authentication

## Authentication Flow
1. User accesses application through Traefik
2. Authentication requests routed to Keycloak via `/kc` path
3. Keycloak authenticates user (direct or via Azure AD)
4. Authentication tokens returned to application
5. Application verifies tokens with Keycloak

## Security Notes
- TLS is enabled for secure connections
- Self-signed certificates are used for local development
- Production should use proper certificates from Let's Encrypt
- Non-root user (appuser) is used in the container for enhanced security
- Keycloak uses PostgreSQL for persistent user data and session management
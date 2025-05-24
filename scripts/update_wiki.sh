#!/bin/bash

# GitHub Wiki Update Script
# This script helps maintain the GitHub wiki by syncing documentation from the main repository

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
WIKI_DIR="wiki"
DOCS_DIR="docs"
MAIN_REPO_URL="https://github.com/gsinghjay/mvp_qr_gen"
WIKI_REPO_URL="https://github.com/gsinghjay/mvp_qr_gen.wiki.git"

echo -e "${BLUE}🚀 GitHub Wiki Update Script${NC}"
echo "=================================================="

# Function to print status
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Create wiki directory if it doesn't exist
if [ ! -d "$WIKI_DIR" ]; then
    print_status "Creating wiki directory..."
    mkdir -p "$WIKI_DIR"
    cd "$WIKI_DIR"
    git clone "$WIKI_REPO_URL" .
    cd ..
else
    print_status "Wiki directory exists, pulling latest changes..."
    cd "$WIKI_DIR"
    git pull origin master
    cd ..
fi

# Function to update wiki page from docs
update_wiki_page() {
    local source_file="$1"
    local wiki_file="$2"
    local description="$3"
    
    if [ -f "$source_file" ]; then
        print_status "Updating $wiki_file from $source_file"
        cp "$source_file" "$WIKI_DIR/$wiki_file"
    else
        print_warning "$source_file not found, skipping $description"
    fi
}

# Function to create wiki page from template
create_wiki_page() {
    local wiki_file="$1"
    local title="$2"
    local content="$3"
    
    if [ ! -f "$WIKI_DIR/$wiki_file" ]; then
        print_status "Creating new wiki page: $wiki_file"
        cat > "$WIKI_DIR/$wiki_file" << EOF
# $title

$content

---

*This page is automatically maintained. For the latest updates, see the [project repository]($MAIN_REPO_URL).*
EOF
    fi
}

# Update existing documentation
print_status "Syncing documentation from docs/ directory..."

# Direct copies from docs
update_wiki_page "$DOCS_DIR/traefik-configuration.md" "Traefik-Configuration.md" "Traefik Configuration"
update_wiki_page "$DOCS_DIR/traefik-quick-reference.md" "Traefik-Quick-Reference.md" "Traefik Quick Reference"
update_wiki_page "$DOCS_DIR/observatory-first-alerts.md" "Alert-System.md" "Alert System"
update_wiki_page "$DOCS_DIR/grafana-dashboard-suite.md" "Grafana-Dashboards.md" "Grafana Dashboards"

# Create placeholder pages for planned content
print_status "Creating placeholder pages for planned content..."

create_wiki_page "API-Documentation.md" "API Documentation" "
Complete API reference and examples for the QR Code Generator.

## Quick Start

Access the interactive API documentation at \`https://your-domain/docs\`

## Endpoints

### QR Code Management
- \`POST /api/v1/qr/static\` - Create static QR code
- \`POST /api/v1/qr/dynamic\` - Create dynamic QR code
- \`GET /api/v1/qr/{qr_id}\` - Get QR code details
- \`PUT /api/v1/qr/{qr_id}\` - Update QR code
- \`DELETE /api/v1/qr/{qr_id}\` - Delete QR code

### QR Code Redirects
- \`GET /r/{short_id}\` - QR code redirect (public)

### System
- \`GET /health\` - Health check
- \`GET /metrics\` - Prometheus metrics

For detailed examples and schemas, visit the interactive documentation.
"

create_wiki_page "System-Architecture.md" "System Architecture" "
Overview of the QR Code Generator system architecture and design patterns.

## Architecture Overview

The system follows a layered architecture with clear separation of concerns:

- **Presentation Layer**: Web UI (Jinja2/Bootstrap) and REST API (FastAPI)
- **Service Layer**: Business logic and QR code operations
- **Repository Layer**: Data access and database operations
- **Infrastructure Layer**: Docker, Traefik, PostgreSQL, Monitoring

## Key Design Patterns

- **Edge Gateway Security**: Traefik handles all security decisions
- **Repository Pattern**: Clean data access abstraction
- **Observatory-First**: Comprehensive monitoring before code changes
- **Dependency Injection**: FastAPI's built-in DI system

## Technology Stack

- **Backend**: FastAPI (Python 3.12)
- **Database**: PostgreSQL 15
- **Frontend**: HTMX + Bootstrap 5
- **Infrastructure**: Docker + Traefik
- **Monitoring**: Prometheus + Grafana + Loki
"

create_wiki_page "Security-Model.md" "Security Model" "
Comprehensive security architecture using the Edge Gateway pattern.

## Edge Gateway Security

All security decisions are made at the Traefik edge gateway:

- **Network-level Access Control**: IP allowlisting for admin functions
- **Path-based Security**: Different security levels for different endpoints
- **TLS Termination**: HTTPS enforcement with wildcard certificates
- **Basic Authentication**: Simple, effective authentication for admin access

## Security Layers

1. **Network Layer**: IP allowlisting and network isolation
2. **Transport Layer**: TLS encryption and HSTS
3. **Application Layer**: Basic authentication and security headers
4. **Content Layer**: CSP and frame protection

## Access Control

- **Public**: QR redirects (\`/r/*\`) with rate limiting
- **Internal**: Admin dashboard with IP + auth restrictions
- **Monitoring**: Grafana/Prometheus with same restrictions as admin

See [Traefik Configuration](Traefik-Configuration) for implementation details.
"

create_wiki_page "Performance-Monitoring.md" "Performance Monitoring" "
Observatory-First performance monitoring and optimization.

## Key Performance Metrics

- **QR Redirects**: <16ms average response time
- **API Operations**: <30ms for all endpoints
- **Error Rate**: <1% under normal conditions
- **Availability**: 99.9% uptime target

## Monitoring Stack

- **Prometheus**: Metrics collection and storage
- **Grafana**: 8 specialized dashboards for visualization
- **Alert System**: 8 critical alert rules for production safety

## Performance Optimization

- **FastAPI Lifespan**: Pre-initialization eliminates cold starts
- **PostgreSQL**: Optimized for concurrency and performance
- **Caching**: Strategic caching for frequently accessed data
- **Rate Limiting**: Protects against abuse while allowing legitimate use

See [Grafana Dashboards](Grafana-Dashboards) for detailed monitoring setup.
"

# Check for changes and commit
cd "$WIKI_DIR"

if [ -n "$(git status --porcelain)" ]; then
    print_status "Changes detected, committing to wiki..."
    
    # Add all changes
    git add .
    
    # Create commit message with timestamp
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    COMMIT_MSG="Update wiki documentation - $TIMESTAMP

    - Synced from main repository
    - Updated configuration documentation
    - Added/updated placeholder pages
    
    Source: $MAIN_REPO_URL"
    
    git commit -m "$COMMIT_MSG"
    
    # Push changes
    print_status "Pushing changes to GitHub wiki..."
    git push origin master
    
    print_status "Wiki updated successfully!"
    echo ""
    echo -e "${GREEN}📚 Wiki URL: https://github.com/gsinghjay/mvp_qr_gen/wiki${NC}"
    echo -e "${GREEN}🔗 Home Page: https://github.com/gsinghjay/mvp_qr_gen/wiki/Home${NC}"
    
else
    print_warning "No changes detected in wiki"
fi

cd ..

echo ""
echo "=================================================="
print_status "Wiki update complete!"

# Show next steps
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo "1. Visit the wiki: https://github.com/gsinghjay/mvp_qr_gen/wiki"
echo "2. Review the updated pages"
echo "3. Add content to placeholder pages as needed"
echo "4. Run this script regularly to keep wiki in sync"
echo ""
echo -e "${YELLOW}💡 Tip: Add this script to your CI/CD pipeline for automatic updates${NC}" 
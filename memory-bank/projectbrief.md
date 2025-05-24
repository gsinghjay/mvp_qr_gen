# Project Brief: QR Code Generator

## Overview
The QR Code Generator is a robust web application built with FastAPI and PostgreSQL that enables users to create, manage, and track QR codes. The system supports both static QR codes (with fixed content) and dynamic QR codes (with updatable redirect URLs). The application includes a web interface for easy management and a comprehensive RESTful API for programmatic access.

## Core Requirements

### Functional Requirements
1. **QR Code Generation**
   - Create static QR codes with permanent content
   - Create dynamic QR codes with updatable redirect URLs
   - Customize appearance (colors, size, border, etc.)
   - Support multiple image formats (PNG, SVG, JPEG, WebP)

2. **QR Code Management**
   - List, retrieve, update, and delete QR codes
   - Search and filter QR codes
   - Track usage of dynamic QR codes (scan count, last scan timestamp)

3. **User Interfaces**
   - Web UI built with Jinja2 templates and Bootstrap
   - RESTful API with comprehensive documentation

4. **Security & Access Control**
   - IP-based access restrictions for administrative functions
   - Rate limiting for public API endpoints
   - Network-level security through dedicated domain and IP
   - Secure HTTPS connections with TLS

### Technical Requirements
1. **Technology Stack**
   - Backend: FastAPI (Python)
   - Database: PostgreSQL
   - Frontend: Jinja2 templates, Bootstrap, Vanilla JS
   - Infrastructure: Docker, Traefik

2. **Performance & Scalability**
   - Leverage PostgreSQL for improved concurrency and performance
   - Implement caching where appropriate
   - Use asynchronous programming for improved concurrency

3. **Security**
   - IP-based access controls for administrative functions
   - Protection against common web vulnerabilities
   - Rate limiting and request validation
   - HTTPS enforcement

4. **Monitoring & Maintenance**
   - Structured logging for application activities
   - Health check endpoints
   - Prometheus metrics
   - Database backup mechanisms

## Project Goals
1. Create a reliable and user-friendly QR code generation service
2. Provide comprehensive API for integration with other systems
3. Ensure security through network-level controls and request validation
4. Maintain high performance and availability
5. Support both web interface and API access patterns
6. Simplify application architecture by removing authentication complexity
7. Implement proper error handling and user feedback
8. Ensure the application is containerized and ready for deployment

## Success Criteria
1. Users can successfully create, manage, and track QR codes
2. The system is secure, with administrative access restricted by IP and basic authentication
3. The application performs well, with fast response times (validated at ~0.016s for QR redirects)
4. The API is well-documented and easy to integrate with
5. The system is containerized and deployable with minimal configuration
6. Security is maintained through network controls and request validation
7. The application handles errors gracefully with standardized error patterns
8. All functionality is properly tested 
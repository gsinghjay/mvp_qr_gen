# Stage 1: Build dependencies and create virtual environment
FROM python:3.12-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Final runtime image
FROM python:3.12-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000 \
    WORKERS=4 \
    TIMEOUT_KEEP_ALIVE=65 \
    PATH="/app/venv/bin:$PATH"

# Install runtime dependencies including Docker CLI for container management
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        postgresql-client \
        ca-certificates \
        gnupg \
        lsb-release \
        libcairo2-dev \
        libgirepository1.0-dev \
        pkg-config \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update \
    && apt-get install -y --no-install-recommends docker-ce-cli \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user and required directories with proper permissions
RUN adduser --disabled-password --gecos '' appuser \
    && mkdir -p /app/data \
                /app/data/backups \
                /app/data/logs \
                /logs/api \
                /logs/database \
                /logs/traefik \
                /app/app/static/assets/images \
                /app/app/static/assets/images/qr_codes \
                /app/app/static/qr_codes \
                /app/app/templates \
                /app/test_advanced_qr_images \
                /app/tests/e2e \
    && chown -R appuser:appuser /app /logs \
    && chmod -R 755 /app \
    && chmod -R 775 /logs \
    && chmod -R 777 /app/data \
    && chmod 777 /app/test_advanced_qr_images \
    && chmod -R 777 /app/app/static/assets/images/qr_codes \
    && chmod -R 777 /app/app/static/qr_codes \
    && chmod -R 755 /app/tests  # Ensure tests directory is readable and executable

# Copy virtual environment from builder
COPY --from=builder /app/venv /app/venv

# Copy only configuration files and create placeholder directories
# App files will be mounted from host
COPY ./alembic /app/alembic
COPY ./alembic.ini /app/alembic.ini

# Create scripts directory (will be mounted in docker-compose)
RUN mkdir -p /app/scripts

# Set proper ownership for copied files
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE ${PORT}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Run the application with initialization
CMD ["/app/scripts/init.sh"] 
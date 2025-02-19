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

# Install runtime dependencies only
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        sqlite3 \
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
                /app/app/static/qr_codes \
                /app/app/templates \
    && chown -R appuser:appuser /app /logs \
    && chmod -R 755 /app \
    && chmod -R 775 /logs \
    && chmod -R 777 /app/data  # Ensure data directory is fully writable

# Copy virtual environment from builder
COPY --from=builder /app/venv /app/venv

# Copy application code and configuration
COPY ./app /app/app
COPY ./alembic /app/alembic
COPY ./alembic.ini /app/alembic.ini
COPY app/scripts/init.sh /app/scripts/
COPY app/scripts/manage_db.py /app/scripts/

# Set proper ownership for copied files
RUN chown -R appuser:appuser /app \
    && chmod +x /app/scripts/init.sh /app/scripts/manage_db.py

# Switch to non-root user
USER appuser

# Expose port
EXPOSE ${PORT}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Run the application with initialization
CMD ["/app/scripts/init.sh"] 
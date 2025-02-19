#!/bin/bash
set -e

# Function to initialize database
initialize_database() {
    echo "Initializing database..."
    # Ensure any existing database is completely removed
    rm -f "/app/data/qr_codes.db"
    /app/scripts/manage_db.py --init || exit 1
    echo "Running initial migrations..."
    /app/scripts/manage_db.py --migrate || exit 1
}

# Function to backup database
backup_database() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="/app/data/backups/qr_codes_${timestamp}.db"
    mkdir -p "/app/data/backups"
    if [ -f "/app/data/qr_codes.db" ]; then
        echo "Creating backup at ${backup_file}"
        cp "/app/data/qr_codes.db" "${backup_file}"
    fi
}

# Ensure data directory has correct permissions
mkdir -p "/app/data"
chmod -R 777 "/app/data"

# Check if database exists and is valid
if [ ! -f "/app/data/qr_codes.db" ]; then
    echo "Fresh installation detected."
    initialize_database
else
    echo "Existing database detected. Validating..."
    if ! /app/scripts/manage_db.py --validate; then
        echo "Database validation failed. Creating backup and reinitializing..."
        backup_database
        initialize_database
    else
        echo "Database validation successful. Checking for migrations..."
        if ! /app/scripts/manage_db.py --check; then
            echo "Running migrations..."
            backup_database
            /app/scripts/manage_db.py --migrate || exit 1
        fi
    fi
fi

# Start the FastAPI application
# echo "Starting FastAPI application..."
# exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --workers ${WORKERS:-4} --timeout-keep-alive ${TIMEOUT_KEEP_ALIVE:-65} 

# Start the FastAPI application with reload enabled for development
if [ "${ENVIRONMENT}" = "development" ]; then
    echo "Starting FastAPI application in development mode with hot-reload..."
    exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --reload --workers 1 --timeout-keep-alive ${TIMEOUT_KEEP_ALIVE:-65}
else
    echo "Starting FastAPI application in production mode..."
    exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --workers ${WORKERS:-4} --timeout-keep-alive ${TIMEOUT_KEEP_ALIVE:-65}
fi 
#!/bin/bash
set -e

# Function to initialize database
initialize_database() {
    echo "Initializing database..."
    # Make a backup of existing database if it exists instead of deleting it
    if [ -f "/app/data/qr_codes.db" ]; then
        local timestamp=$(date +%Y%m%d_%H%M%S)
        local backup_file="/app/data/backups/qr_codes_${timestamp}_before_init.db"
        mkdir -p "/app/data/backups"
        echo "Creating emergency backup at ${backup_file} before initialization"
        cp "/app/data/qr_codes.db" "${backup_file}"
    fi
    
    # Initialize the database without removing the file
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
echo "Setting up data directory..."
mkdir -p "/app/data"
chmod -R 777 "/app/data"

# Initialize or validate database before starting the application
echo "Checking database status..."
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

echo "Database setup complete."

# Start the FastAPI application based on environment
if [ "${ENVIRONMENT}" = "development" ]; then
    echo "Starting FastAPI application in development mode with hot-reload..."
    exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --reload --workers 1 --timeout-keep-alive ${TIMEOUT_KEEP_ALIVE:-65}
else
    echo "Starting FastAPI application in production mode..."
    exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --workers ${WORKERS:-4} --timeout-keep-alive ${TIMEOUT_KEEP_ALIVE:-65}
fi 
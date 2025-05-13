#!/bin/bash
set -e

# PostgreSQL is now the only database type
echo "PostgreSQL database system enabled"

# Function to initialize database
initialize_database() {
    echo "Initializing database..."
    
    # Ensure connection before initialization
    echo "Waiting for PostgreSQL to be ready..."
    # Add a timeout to prevent infinite waiting
    timeout=60
    counter=0
    
    # Keep checking until PostgreSQL is ready or timeout
    until PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "${POSTGRES_HOST}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c '\q' 2>/dev/null || [ $counter -eq $timeout ]; do
        echo "PostgreSQL not ready yet. Waiting..."
        sleep 1
        counter=$((counter+1))
    done
    
    if [ $counter -eq $timeout ]; then
        echo "Timed out waiting for PostgreSQL to be ready"
        exit 1
    fi
    
    echo "PostgreSQL is ready. Initializing..."
    
    # Initialize the database
    /app/scripts/manage_db.py --init || exit 1
    
    echo "Running initial migrations..."
    /app/scripts/manage_db.py --migrate || exit 1
}

# Function to backup database
backup_database() {
    # Use manage_db.py which uses pg_dump
    echo "Creating PostgreSQL backup before migration..."
    if [ -d "/app/backups" ]; then
        echo "External backups directory exists and will be used by manage_db.py"
    fi
    # Call the script with the --create-backup option
    /app/scripts/manage_db.py --create-backup || echo "Warning: Backup creation might have failed, but continuing anyway"
}

# Ensure data directory has correct permissions
echo "Setting up data directory..."
mkdir -p "/app/data"
chmod -R 777 "/app/data"

# Create external backups directory if it doesn't exist
if [ -d "/app/backups" ]; then
    echo "External backups directory exists"
else
    echo "External backups directory doesn't exist"
fi

# Initialize or validate database before starting the application
echo "Checking database status..."

# PostgreSQL initialization and validation
echo "Checking PostgreSQL database..."

# Verify PostgreSQL connection first
if ! PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "${POSTGRES_HOST}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c '\q' 2>/dev/null; then
    echo "Cannot connect to PostgreSQL. Waiting for database to be ready..."
    # Wait for PostgreSQL to be ready (handled in initialize_database)
    initialize_database
else
    echo "PostgreSQL connection successful. Validating database..."
    if ! /app/scripts/manage_db.py --validate; then
        echo "PostgreSQL database validation failed. Creating backup and reinitializing..."
        backup_database
        initialize_database
    else
        echo "PostgreSQL database validation successful. Checking for migrations..."
        if ! /app/scripts/manage_db.py --check; then
            echo "Running migrations for PostgreSQL..."
            backup_database
            /app/scripts/manage_db.py --migrate || exit 1
        fi
    fi
fi

echo "Database setup complete."

# Create a regular backup at startup if external backups directory exists
if [ -d "/app/backups" ]; then
    echo "Creating regular PostgreSQL backup at startup..."
    backup_database
fi

# Start the FastAPI application based on environment
if [ "${ENVIRONMENT}" = "development" ]; then
    echo "Starting FastAPI application in development mode with hot-reload..."
    exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --reload --workers 1 --timeout-keep-alive ${TIMEOUT_KEEP_ALIVE:-65}
else
    echo "Starting FastAPI application in production mode..."
    exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --workers ${WORKERS:-4} --timeout-keep-alive ${TIMEOUT_KEEP_ALIVE:-65}
fi 
#!/bin/bash
set -e

# Check if we're using PostgreSQL
if [ "${USE_POSTGRES}" = "true" ] && [ -n "${PG_DATABASE_URL}" ]; then
    echo "PostgreSQL mode enabled"
    DB_TYPE="postgresql"
else
    echo "SQLite mode enabled"
    DB_TYPE="sqlite"
fi

# Function to initialize database
initialize_database() {
    echo "Initializing database..."
    
    if [ "${DB_TYPE}" = "postgresql" ]; then
        # For PostgreSQL, ensure connection before initialization
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
    else
        # For SQLite, make a backup if it exists (existing functionality)
        if [ -f "/app/data/qr_codes.db" ]; then
            local timestamp=$(date +%Y%m%d_%H%M%S)
            local backup_file="/app/data/backups/qr_codes_${timestamp}_before_init.db"
            mkdir -p "/app/data/backups"
            echo "Creating emergency backup at ${backup_file} before initialization"
            cp "/app/data/qr_codes.db" "${backup_file}"
            
            # Copy the backup to the external backups directory if it exists
            if [ -d "/app/backups" ]; then
                echo "Copying backup to external directory"
                cp "${backup_file}" "/app/backups/"
            fi
        fi
    fi
    
    # Initialize the database
    if [ "${DB_TYPE}" = "postgresql" ]; then
        /app/scripts/manage_db.py --postgres --init || exit 1
    else
        /app/scripts/manage_db.py --init || exit 1
    fi
    
    echo "Running initial migrations..."
    if [ "${DB_TYPE}" = "postgresql" ]; then
        /app/scripts/manage_db.py --postgres --migrate || exit 1
    else
        /app/scripts/manage_db.py --migrate || exit 1
    fi
}

# Function to backup database
backup_database() {
    if [ "${DB_TYPE}" = "postgresql" ]; then
        # For PostgreSQL, use manage_db.py which uses pg_dump
        echo "Creating PostgreSQL backup before migration..."
        if [ -d "/app/backups" ]; then
            echo "External backups directory exists and will be used by manage_db.py"
        fi
        # Actually call the script with the --create-backup option
        /app/scripts/manage_db.py --postgres --create-backup || echo "Warning: Backup creation might have failed, but continuing anyway"
    else
        # For SQLite, follow existing procedure
        local timestamp=$(date +%Y%m%d_%H%M%S)
        local backup_file="/app/data/backups/qr_codes_${timestamp}.db"
        mkdir -p "/app/data/backups"
        if [ -f "/app/data/qr_codes.db" ]; then
            echo "Creating backup at ${backup_file}"
            cp "/app/data/qr_codes.db" "${backup_file}"
            
            # Copy the backup to the external backups directory if it exists
            if [ -d "/app/backups" ]; then
                echo "Copying backup to external directory"
                cp "${backup_file}" "/app/backups/"
            fi
        fi
    fi
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

if [ "${DB_TYPE}" = "postgresql" ]; then
    # PostgreSQL initialization and validation
    echo "Checking PostgreSQL database..."
    
    # Verify PostgreSQL connection first
    if ! PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "${POSTGRES_HOST}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c '\q' 2>/dev/null; then
        echo "Cannot connect to PostgreSQL. Waiting for database to be ready..."
        # Wait for PostgreSQL to be ready (handled in initialize_database)
        initialize_database
    else
        echo "PostgreSQL connection successful. Validating database..."
        if ! /app/scripts/manage_db.py --postgres --validate; then
            echo "PostgreSQL database validation failed. Creating backup and reinitializing..."
            backup_database
            initialize_database
        else
            echo "PostgreSQL database validation successful. Checking for migrations..."
            if ! /app/scripts/manage_db.py --postgres --check; then
                echo "Running migrations for PostgreSQL..."
                backup_database
                /app/scripts/manage_db.py --postgres --migrate || exit 1
            fi
        fi
    fi
else
    # SQLite initialization and validation (existing functionality)
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
fi

echo "Database setup complete."

# Create a test backup to verify external backup directory is working
if [ "${DB_TYPE}" = "sqlite" ] && [ -f "/app/data/qr_codes.db" ] && [ -d "/app/backups" ]; then
    echo "Creating test backup to verify external backup directory..."
    timestamp=$(date +%Y%m%d_%H%M%S)
    test_backup_file="/app/data/backups/qr_codes_${timestamp}_test.db"
    cp "/app/data/qr_codes.db" "${test_backup_file}"
    cp "${test_backup_file}" "/app/backups/"
    echo "Test backup created and copied to external directory."
elif [ "${DB_TYPE}" = "postgresql" ] && [ -d "/app/backups" ]; then
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
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
        
        # Copy the backup to the external backups directory if it exists
        if [ -d "/app/backups" ]; then
            echo "Copying backup to external directory"
            cp "${backup_file}" "/app/backups/"
        fi
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
        
        # Copy the backup to the external backups directory if it exists
        if [ -d "/app/backups" ]; then
            echo "Copying backup to external directory"
            cp "${backup_file}" "/app/backups/"
        fi
    fi
}

# Function to warm up routes by making initial requests
warmup_routes() {
    echo "Warming up routes to initialize code paths..."
    local port=${PORT:-8000}
    local max_attempts=10
    local attempt=1
    local wait_time=2
    
    # Wait for the application to be ready with retry logic
    echo "Waiting for application to be ready on port $port..."
    while [ $attempt -le $max_attempts ]; do
        echo "Attempt $attempt of $max_attempts..."
        if curl -s "http://127.0.0.1:$port/health" > /dev/null; then
            echo "Application is ready!"
            break
        else
            echo "Application not ready yet, waiting ${wait_time}s..."
            sleep $wait_time
            # Exponential backoff with a cap
            wait_time=$(( wait_time < 10 ? wait_time * 2 : 10 ))
            attempt=$((attempt + 1))
        fi
    done
    
    if [ $attempt -gt $max_attempts ]; then
        echo "Warning: Could not confirm application readiness after $max_attempts attempts"
        echo "Continuing anyway, first requests may be slow..."
    else
        # Warm up the health endpoint (initializes SQLAlchemy and DB connections)
        echo "Warming up health endpoint..."
        curl -s "http://127.0.0.1:$port/health" > /dev/null
        
        # Warm up QR code listing endpoint - this initializes the QR service and repository
        echo "Warming up QR listing endpoint..."
        curl -s "http://127.0.0.1:$port/api/v1/qr?limit=1" > /dev/null
        
        # Warm up a static QR endpoint to initialize more of the QR service
        echo "Warming up QR image endpoint (with a likely invalid ID)..."
        curl -s "http://127.0.0.1:$port/api/v1/qr/00000000-0000-0000-0000-000000000000" -o /dev/null 2>/dev/null || true
        
        # This will initialize the redirect path code without error logging
        echo "Warming up redirect code paths via web endpoint..."
        curl -s "http://127.0.0.1:$port/" > /dev/null
        
        echo "Route warmup complete"
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

# Create a test backup to verify external backup directory is working
if [ -f "/app/data/qr_codes.db" ] && [ -d "/app/backups" ]; then
    echo "Creating test backup to verify external backup directory..."
    timestamp=$(date +%Y%m%d_%H%M%S)
    test_backup_file="/app/data/backups/qr_codes_${timestamp}_test.db"
    cp "/app/data/qr_codes.db" "${test_backup_file}"
    cp "${test_backup_file}" "/app/backups/"
    echo "Test backup created and copied to external directory."
fi

# Start the FastAPI application based on environment
if [ "${ENVIRONMENT}" = "development" ]; then
    echo "Starting FastAPI application in development mode with hot-reload..."
    # Start the application in the background
    uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --reload --workers 1 --timeout-keep-alive ${TIMEOUT_KEEP_ALIVE:-65} &
    PID=$!
    
    # Warm up routes
    warmup_routes
    
    # Wait for the application process
    wait $PID
else
    echo "Starting FastAPI application in production mode..."
    # Start the application in the background
    uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --workers ${WORKERS:-4} --timeout-keep-alive ${TIMEOUT_KEEP_ALIVE:-65} &
    PID=$!
    
    # Warm up routes
    warmup_routes
    
    # Wait for the application process
    wait $PID
fi 
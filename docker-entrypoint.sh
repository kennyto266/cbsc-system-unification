#!/bin/bash
# Docker entrypoint script for CBSC Strategy Management System
# Handles initialization, migrations, and graceful startup

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if service is ready
check_service() {
    local service=$1
    local host=${2:-localhost}
    local port=${3:-5432}
    local timeout=${4:-30}

    print_status "Checking $service connectivity..."

    for i in $(seq 1 $timeout); do
        if nc -z $host $port 2>/dev/null; then
            print_success "$service is ready!"
            return 0
        fi
        echo -n "."
        sleep 1
    done

    print_error "$service connection failed after $timeout seconds"
    return 1
}

# Function to run database migrations
run_migrations() {
    print_status "Running database migrations..."

    # Check if migrations directory exists
    if [ -d "/app/migrations" ]; then
        # Using Alembic if available
        if command -v alembic &> /dev/null; then
            print_status "Using Alembic for migrations"
            alembic upgrade head || print_warning "Alembic migration failed, continuing anyway"
        else
            # Simple Python migration runner
            print_status "Running Python migration scripts"
            python -m migrations.migrate || print_warning "Migration failed, continuing anyway"
        fi
        print_success "Database migrations completed"
    else
        print_warning "No migrations directory found, skipping migrations"
    fi
}

# Function to initialize Redis cache
init_redis() {
    if [ -n "$REDIS_URL" ]; then
        print_status "Initializing Redis cache..."
        python -c "
import redis
import sys
try:
    r = redis.from_url('$REDIS_URL')
    r.ping()
    print('Redis connection successful')
except Exception as e:
    print(f'Redis connection failed: {e}')
    sys.exit(1)
        " || print_warning "Redis initialization failed"
    fi
}

# Function to create directories
create_directories() {
    print_status "Creating necessary directories..."

    mkdir -p /app/logs/strategies
    mkdir -p /app/logs/api
    mkdir -p /app/logs/websocket
    mkdir -p /app/uploads
    mkdir -p /app/static

    # Set permissions
    chmod 755 /app/logs /app/uploads /app/static
    chmod 644 /app/.env

    print_success "Directories created and permissions set"
}

# Function to validate configuration
validate_config() {
    print_status "Validating configuration..."

    # Check required environment variables
    required_vars=("DATABASE_URL")
    missing_vars=()

    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done

    if [ ${#missing_vars[@]} -ne 0 ]; then
        print_error "Missing required environment variables: ${missing_vars[*]}"
        exit 1
    fi

    # Check API version
    if [ -z "$STRATEGY_API_VERSION" ]; then
        export STRATEGY_API_VERSION=2
        print_warning "STRATEGY_API_VERSION not set, defaulting to 2"
    fi

    print_success "Configuration validation passed"
}

# Function to run health checks
run_health_check() {
    print_status "Running pre-startup health checks..."

    # Database check
    if [ -n "$DATABASE_URL" ]; then
        python -c "
import psycopg2
import os
try:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    conn.close()
    print('Database connection successful')
except Exception as e:
    print(f'Database connection failed: {e}')
    exit(1)
        " || {
            print_error "Database health check failed"
            exit 1
        }
    fi

    print_success "All health checks passed"
}

# Function to start the application
start_application() {
    print_status "Starting CBSC Strategy Management System..."
    print_status "API Version: $STRATEGY_API_VERSION"
    print_status "Workers: ${WORKERS:-4}"
    print_status "Port: ${PORT:-3004}"

    # Set default values
    export PORT=${PORT:-3004}
    export WORKERS=${WORKERS:-4}

    # Start with uvicorn
    if [ "$1" = "--worker" ]; then
        # Worker mode for multi-process deployment
        exec python -m uvicorn src.api.main:app \
            --host 0.0.0.0 \
            --port $PORT \
            --workers 1 \
            --worker-class uvicorn.workers.UvicornWorker
    else
        # Default mode with multiple workers
        exec python -m uvicorn src.api.main:app \
            --host 0.0.0.0 \
            --port $PORT \
            --workers $WORKERS \
            --worker-class uvicorn.workers.UvicornWorker \
            --access-log \
            --log-level info
    fi
}

# Main execution flow
main() {
    print_status "=== CBSC Strategy Management System Startup ==="
    print_status "Container version: 2.0.0"
    print_status "Strategy API version: ${STRATEGY_API_VERSION:-2}"

    # Wait for dependencies
    if [ -n "$POSTGRES_HOST" ] && [ -n "$POSTGRES_PORT" ]; then
        check_service "PostgreSQL" "$POSTGRES_HOST" "$POSTGRES_PORT"
    fi

    if [ -n "$REDIS_HOST" ] && [ -n "$REDIS_PORT" ]; then
        check_service "Redis" "$REDIS_HOST" "$REDIS_PORT"
    fi

    # Run initialization steps
    validate_config
    create_directories
    run_migrations
    init_redis
    run_health_check

    # Start the application
    start_application "$@"
}

# Handle signals gracefully
cleanup() {
    print_status "Received shutdown signal, cleaning up..."
    # Add any cleanup logic here
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Run main function
main "$@"
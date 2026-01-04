#!/bin/bash
# CBSC Strategy Management System - Production Docker Entrypoint Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if environment variables are set
check_env_vars() {
    print_status "Checking environment variables..."

    required_vars=(
        "DATABASE_URL"
        "REDIS_URL"
        "SECRET_KEY"
        "INFLUXDB_URL"
        "INFLUXDB_TOKEN"
    )

    missing_vars=()

    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done

    if [ ${#missing_vars[@]} -ne 0 ]; then
        print_error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        exit 1
    fi

    print_status "All required environment variables are set"
}

# Wait for database to be ready
wait_for_db() {
    print_status "Waiting for PostgreSQL database..."

    max_attempts=30
    attempt=0

    until pg_isready -d "$DATABASE_URL" || [ $attempt -eq $max_attempts ]; do
        attempt=$((attempt+1))
        print_warning "Attempt $attempt/$max_attempts: Database not ready, waiting..."
        sleep 2
    done

    if [ $attempt -eq $max_attempts ]; then
        print_error "Database connection failed after $max_attempts attempts"
        exit 1
    fi

    print_status "Database is ready"
}

# Wait for Redis to be ready
wait_for_redis() {
    print_status "Waiting for Redis..."

    max_attempts=30
    attempt=0

    # Extract Redis host and port from REDIS_URL
    redis_host=$(echo "$REDIS_URL" | sed -n 's/redis:\/\/\([^:]*\):.*/\1/p')
    redis_port=$(echo "$REDIS_URL" | sed -n 's/redis:\/\/[^:]*:\([0-9]*\).*/\1/p')

    until redis-cli -h "$redis_host" -p "$redis_port" ping || [ $attempt -eq $max_attempts ]; do
        attempt=$((attempt+1))
        print_warning "Attempt $attempt/$max_attempts: Redis not ready, waiting..."
        sleep 2
    done

    if [ $attempt -eq $max_attempts ]; then
        print_error "Redis connection failed after $max_attempts attempts"
        exit 1
    fi

    print_status "Redis is ready"
}

# Wait for InfluxDB to be ready
wait_for_influxdb() {
    print_status "Waiting for InfluxDB..."

    max_attempts=30
    attempt=0

    until curl -f "$INFLUXDB_URL/health" || [ $attempt -eq $max_attempts ]; do
        attempt=$((attempt+1))
        print_warning "Attempt $attempt/$max_attempts: InfluxDB not ready, waiting..."
        sleep 2
    done

    if [ $attempt -eq $max_attempts ]; then
        print_error "InfluxDB connection failed after $max_attempts attempts"
        exit 1
    fi

    print_status "InfluxDB is ready"
}

# Run database migrations
run_migrations() {
    print_status "Running database migrations..."

    # Check if migrations directory exists
    if [ -d "/app/migrations" ]; then
        # Using Alembic for migrations
        if command -v alembic &> /dev/null; then
            alembic upgrade head
        else
            # Fallback to custom migration script
            python -c "
import sys
sys.path.append('/app')
from src.core.database import engine, Base
Base.metadata.create_all(bind=engine)
print('Database tables created successfully')
"
        fi
    else
        print_warning "No migrations directory found, skipping migrations"
    fi
}

# Initialize application data
init_app_data() {
    print_status "Initializing application data..."

    # Create default admin user if needed
    python -c "
import sys
sys.path.append('/app')
import asyncio
from src.services.user_service_v2 import UserServiceV2
from src.core.database import get_db

async def create_admin():
    try:
        db = next(get_db())
        user_service = UserServiceV2(db)

        # Check if admin user exists
        admin_exists = await user_service.get_user_by_username('admin')
        if not admin_exists:
            # Create admin user with default password
            await user_service.create_user({
                'username': 'admin',
                'email': 'admin@cbsc.system',
                'password': 'admin123',  # Change this immediately!
                'is_active': True,
                'is_superuser': True
            })
            print('Default admin user created')
            print('IMPORTANT: Change default admin password immediately!')
        else:
            print('Admin user already exists')
    except Exception as e:
        print(f'Error creating admin user: {e}')

asyncio.run(create_admin())
"
}

# Create log directories
create_log_dirs() {
    print_status "Creating log directories..."

    mkdir -p /app/logs/strategies
    mkdir -p /app/logs/api
    mkdir -p /app/logs/websocket
    mkdir -p /app/logs/monitoring

    # Set proper permissions
    chmod 755 /app/logs
    chmod 755 /app/logs/*
}

# Health check endpoint setup
setup_health_check() {
    print_status "Setting up health check endpoints..."

    # Create health check file
    echo '{"status": "healthy", "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}' > /tmp/health.json
}

# Start application
start_application() {
    print_status "Starting CBSC Strategy Management System..."

    # If no arguments provided, use default Gunicorn command
    if [ $# -eq 0 ]; then
        exec gunicorn src.api.main:app \
            -w 4 \
            -k uvicorn.workers.UvicornWorker \
            --bind 0.0.0.0:8000 \
            --access-logfile - \
            --error-logfile - \
            --log-level info \
            --timeout 120 \
            --keep-alive 5 \
            --max-requests 1000 \
            --max-requests-jitter 100 \
            --worker-tmp-dir /dev/shm \
            --worker-connections 1000
    else
        # Execute provided command
        exec "$@"
    fi
}

# Main execution
main() {
    print_status "Starting CBSC Strategy Management System container..."
    print_status "Environment: $ENVIRONMENT"
    print_status "Python version: $(python --version)"
    print_status "Working directory: $(pwd)"

    # Run initialization steps
    check_env_vars
    create_log_dirs
    setup_health_check

    # Wait for dependencies
    wait_for_db
    wait_for_redis
    wait_for_influxdb

    # Initialize application
    run_migrations
    init_app_data

    print_status "Initialization complete. Starting application..."

    # Start the application
    start_application "$@"
}

# Trap signals for graceful shutdown
trap 'print_status "Received termination signal, shutting down..."; exit 0' SIGTERM SIGINT

# Run main function with all arguments
main "$@"
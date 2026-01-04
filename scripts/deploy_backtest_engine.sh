#!/bin/bash
# Deploy Backtest Engine Script
# ===========================
# This script sets up and deploys the enhanced backtest engine

set -e  # Exit on any error

# Configuration
POSTGRES_HOST=${POSTGRES_HOST:-localhost}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
POSTGRES_DB=${POSTGRES_DB:-cbsc_backtest}
POSTGRES_USER=${POSTGRES_USER:-cbsc_user}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-cbsc_password}

INFLUXDB_HOST=${INFLUXDB_HOST:-localhost}
INFLUXDB_PORT=${INFLUXDB_PORT:-8086}
INFLUXDB_ORG=${INFLUXDB_ORG:-cbsc}
INFLUXDB_BUCKET=${INFLUXDB_BUCKET:-backtest_metrics}

REDIS_HOST=${REDIS_HOST:-localhost}
REDIS_PORT=${REDIS_PORT:-6379}
REDIS_DB=${REDIS_DB:-0}

API_HOST=${API_HOST:-0.0.0.0}
API_PORT=${API_PORT:-3004}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Check dependencies
check_dependencies() {
    log "Checking dependencies..."

    # Check Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is required but not installed"
    fi

    # Check Node.js (for frontend)
    if ! command -v node &> /dev/null; then
        warn "Node.js is not installed (required for frontend)"
    fi

    # Check Docker (optional)
    if command -v docker &> /dev/null; then
        log "Docker found - can use containerized deployment"
        USE_DOCKER=true
    else
        log "Docker not found - using local deployment"
        USE_DOCKER=false
    fi

    # Check psql
    if ! command -v psql &> /dev/null; then
        warn "psql not found - cannot check PostgreSQL connection"
    fi
}

# Setup virtual environment
setup_venv() {
    log "Setting up Python virtual environment..."

    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi

    source venv/bin/activate

    # Upgrade pip
    pip install --upgrade pip

    # Install requirements
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        # Install core dependencies
        pip install \
            fastapi uvicorn \
            asyncpg aioredis \
            influxdb-client \
            pandas numpy \
            pytest pytest-asyncio \
            python-multipart
    fi

    log "Virtual environment setup complete"
}

# Setup databases
setup_databases() {
    log "Setting up databases..."

    # PostgreSQL
    if [ "$USE_DOCKER" = true ]; then
        log "Starting PostgreSQL with Docker..."
        docker run -d \
            --name cbsc-postgres \
            -e POSTGRES_DB=$POSTGRES_DB \
            -e POSTGRES_USER=$POSTGRES_USER \
            -e POSTGRES_PASSWORD=$POSTGRES_PASSWORD \
            -p $POSTGRES_PORT:5432 \
            postgres:15-alpine

        # Wait for PostgreSQL to start
        sleep 5
    fi

    # Create database schema
    log "Creating PostgreSQL schema..."
    PGPASSWORD=$POSTGRES_PASSWORD psql \
        -h $POSTGRES_HOST \
        -p $POSTGRES_PORT \
        -U $POSTGRES_USER \
        -d $POSTGRES_DB \
        -f src/backtest/database_schema.sql

    # InfluxDB
    if [ "$USE_DOCKER" = true ]; then
        log "Starting InfluxDB with Docker..."
        docker run -d \
            --name cbsc-influxdb \
            -p $INFLUXDB_PORT:8086 \
            -e DOCKER_INFLUXDB_INIT_MODE=setup \
            -e DOCKER_INFLUXDB_INIT_USERNAME=admin \
            -e DOCKER_INFLUXDB_INIT_PASSWORD=password123 \
            -e DOCKER_INFLUXDB_INIT_ORG=$INFLUXDB_ORG \
            -e DOCKER_INFLUXDB_INIT_BUCKET=$INFLUXDB_BUCKET \
            influxdb:2.7-alpine

        # Wait for InfluxDB to start
        sleep 10
    fi

    # Redis
    if [ "$USE_DOCKER" = true ]; then
        log "Starting Redis with Docker..."
        docker run -d \
            --name cbsc-redis \
            -p $REDIS_PORT:6379 \
            redis:7-alpine
    fi

    log "Database setup complete"
}

# Create environment file
create_env_file() {
    log "Creating environment file..."

    cat > .env << EOF
# Database Configuration
POSTGRES_DSN=postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_HOST:$POSTGRES_PORT/$POSTGRES_DB
INFLUXDB_URL=http://$INFLUXDB_HOST:$INFLUXDB_PORT
INFLUXDB_TOKEN=your-influxdb-token-here
INFLUXDB_ORG=$INFLUXDB_ORG
INFLUXDB_BUCKET=$INFLUXDB_BUCKET
REDIS_URL=redis://$REDIS_HOST:$REDIS_PORT/$REDIS_DB

# API Configuration
API_HOST=$API_HOST
API_PORT=$API_PORT
API_WORKERS=4

# Cache Configuration
CACHE_SIZE_MB=512
CACHE_TTL_HOURS=24

# Backtest Configuration
MAX_WORKERS=8
DEFAULT_INITIAL_CAPITAL=1000000
DEFAULT_COMMISSION_RATE=0.001
DEFAULT_SLIPPAGE_RATE=0.0005
EOF

    log "Environment file created at .env"
}

# Run tests
run_tests() {
    log "Running tests..."

    source venv/bin/activate

    # Run unit tests
    python -m pytest src/backtest/tests/ -v

    # Run integration tests if environment is set up
    if [ -f ".env" ]; then
        export $(cat .env | xargs)
        python -m pytest tests/integration/ -v || true
    fi

    log "Tests completed"
}

# Start services
start_services() {
    log "Starting backtest engine services..."

    source venv/bin/activate
    export $(cat .env | xargs)

    # Start API server
    log "Starting Backtest API on port $API_PORT..."
    cd src/api
    uvicorn backtest_api:app \
        --host $API_HOST \
        --port $API_PORT \
        --workers $API_WORKERS \
        --reload &
    API_PID=$!
    cd ../..

    # Store PIDs for cleanup
    echo $API_PID > .api_pid

    log "Services started successfully"
    log "API is available at: http://$API_HOST:$API_PORT"
    log "API Documentation: http://$API_HOST:$API_PORT/docs"
}

# Health check
health_check() {
    log "Performing health check..."

    # Wait for services to start
    sleep 5

    # Check API
    if curl -f http://localhost:$API_PORT/api/v1/health > /dev/null 2>&1; then
        log "API health check passed"
    else
        error "API health check failed"
    fi

    # Check database connections
    python -c "
import asyncio
import asyncpg
import aioredis
from influxdb_client import InfluxDBClient

async def check_dbs():
    # Check PostgreSQL
    try:
        conn = await asyncpg.connect('$POSTGRES_DSN')
        await conn.close()
        print('PostgreSQL: OK')
    except Exception as e:
        print(f'PostgreSQL: FAILED - {e}')

    # Check Redis
    try:
        redis = await aioredis.from_url('$REDIS_URL')
        await redis.ping()
        await redis.close()
        print('Redis: OK')
    except Exception as e:
        print(f'Redis: FAILED - {e}')

    # Check InfluxDB
    try:
        client = InfluxDBClient(url='$INFLUXDB_URL')
        health = client.health()
        print(f'InfluxDB: {health.status.upper()}')
        client.close()
    except Exception as e:
        print(f'InfluxDB: FAILED - {e}')

asyncio.run(check_dbs())
"
}

# Cleanup function
cleanup() {
    log "Cleaning up..."

    # Stop API server
    if [ -f ".api_pid" ]; then
        kill $(cat .api_pid) 2>/dev/null || true
        rm .api_pid
    fi

    # Stop Docker containers if used
    if [ "$USE_DOCKER" = true ]; then
        docker stop cbsc-postgres cbsc-influxdb cbsc-redis 2>/dev/null || true
        docker rm cbsc-postgres cbsc-influxdb cbsc-redis 2>/dev/null || true
    fi

    log "Cleanup complete"
}

# Main execution
main() {
    log "Starting Phase 5.1 Backtest Engine deployment..."

    # Set up cleanup trap
    trap cleanup EXIT

    # Check if already deployed
    if [ -f ".env" ] && [ -d "venv" ]; then
        warn "Backtest engine already deployed. Starting services..."
        start_services
        health_check
        exit 0
    fi

    # Full deployment
    check_dependencies
    setup_venv
    create_env_file

    if [ "$1" != "--no-db" ]; then
        setup_databases
    fi

    if [ "$1" != "--no-test" ]; then
        run_tests
    fi

    start_services
    health_check

    log "Deployment complete!"
    log ""
    log "Next steps:"
    log "1. Update InfluxDB token in .env file"
    log "2. Run: curl http://localhost:$API_PORT/api/v1/health"
    log "3. Visit: http://localhost:$API_PORT/docs for API documentation"
}

# Handle command line arguments
case "${1:-}" in
    --no-db)
        warn "Skipping database setup"
        main --no-db
        ;;
    --no-test)
        warn "Skipping tests"
        main --no-test
        ;;
    --cleanup)
        cleanup
        ;;
    --help)
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --no-db     Skip database setup"
        echo "  --no-test   Skip running tests"
        echo "  --cleanup   Stop services and cleanup"
        echo "  --help      Show this help"
        exit 0
        ;;
    *)
        main
        ;;
esac
#!/bin/bash

# Authentication Service Entrypoint
set -e

# Print configuration for debugging
echo "Starting CBSC Authentication Service..."
echo "======================================"
echo "Environment: ${CONFIG_PROFILE:-development}"
echo "Database URL: ${DATABASE_URL}"
echo "Redis URL: ${REDIS_URL}"
echo "======================================"

# Wait for database to be ready
if [ "$DATABASE_URL" ]; then
    echo "Waiting for database..."
    until python -c "from sqlalchemy import create_engine; engine = create_engine('${DATABASE_URL}'); engine.connect()" 2>/dev/null; do
        echo "Database is unavailable - sleeping"
        sleep 1
    done
    echo "Database is ready!"
fi

# Wait for Redis if configured
if [ "$REDIS_HOST" ]; then
    echo "Waiting for Redis..."
    until python -c "import redis; r = redis.Redis(host='${REDIS_HOST}', port=${REDIS_PORT:-6379}); r.ping()" 2>/dev/null; do
        echo "Redis is unavailable - sleeping"
        sleep 1
    done
    echo "Redis is ready!"
fi

# Run database migrations
echo "Running database migrations..."
python -m alembic upgrade head

# Create initial data if needed
echo "Checking initial data..."
python -c "
from src.auth.service import AuthService
from src.auth.config import load_config
config = load_config()
auth_service = AuthService(config.database_url, config.dict())
# Tables are created automatically by SQLAlchemy
print('Database tables ready')
"

# Start the application
echo "Starting authentication service..."
exec python -m uvicorn src.auth_service_main:app \
    --host 0.0.0.0 \
    --port ${PORT:-3006} \
    --workers ${WORKERS:-1} \
    ${ACCESS_LOG:+--access-log} \
    ${LOG_LEVEL:+--log-level $LOG_LEVEL}
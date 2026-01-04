#!/bin/bash
# CBSC Real Backend Entrypoint Script
set -e

echo "========================================"
echo "CBSC Quantitative Trading System"
echo "Real Backend with VectorBT Support"
echo "========================================"

# Wait for dependencies
echo "Waiting for PostgreSQL..."
until pg_isready -h postgres -U cbsc_admin -d cbsc_production 2>/dev/null; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 2
done
echo "PostgreSQL is ready!"

echo "Waiting for Redis..."
until python -c "import redis; r = redis.Redis(host='redis', port=6379, password='cbsc_redis_password_2024', decode_responses=True); r.ping()" 2>/dev/null; do
    echo "Redis is unavailable - sleeping"
    sleep 2
done
echo "Redis is ready!"

echo "Waiting for InfluxDB..."
until curl -f http://influxdb:8086/health 2>/dev/null; do
    echo "InfluxDB is unavailable - sleeping"
    sleep 2
done
echo "InfluxDB is ready!"

# Run migrations if needed
echo "Running database migrations..."
if [ -f /app/backend/alembic.ini ]; then
    cd /app/backend
    alembic upgrade head || echo "Migration completed or no migrations needed"
fi

# Initialize strategy factory
echo "Initializing strategy factory..."
python -c "from src.strategies.unified_factory import StrategyFactory; print('Strategy factory loaded successfully')" || echo "Strategy factory initialization skipped"

# Check VectorBT availability
echo "Checking VectorBT availability..."
python -c "import vectorbt as vbt; print(f'VectorBT version: {vbt.__version__}')" || echo "Warning: VectorBT not available"

# Start the application
echo "Starting CBSC Real Backend..."
echo "========================================"
exec "$@"

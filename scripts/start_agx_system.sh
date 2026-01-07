#!/bin/bash
#
# CBSC AGX Analytics System - Quick Start Script
#
# This script initializes and starts the AGX analytics system
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGX_DIR="$PROJECT_ROOT/agx"
SERVICE_DIR="$PROJECT_ROOT/ai-strategy-service"
LOG_DIR="$PROJECT_ROOT/logs"

echo "=================================================="
echo "CBSC AGX Analytics System - Quick Start"
echo "=================================================="
echo ""

# Create logs directory
mkdir -p "$LOG_DIR"

# Step 1: Check if AGX directory exists
echo "1. Checking AGX installation..."
if [ ! -d "$AGX_DIR" ]; then
    echo -e "${RED}❌ AGX directory not found: $AGX_DIR${NC}"
    echo ""
    echo "Please install AGX first:"
    echo "  git clone https://github.com/agnosticeng/agx.git agx"
    echo "  cd agx && docker compose up -d"
    exit 1
fi
echo -e "${GREEN}✅ AGX directory found${NC}"

# Step 2: Start AGX with ClickHouse
echo ""
echo "2. Starting AGX and ClickHouse..."
cd "$AGX_DIR"
if docker compose ps | grep -q "Up"; then
    echo -e "${YELLOW}⚠️  AGX containers already running${NC}"
else
    docker compose up -d
    echo -e "${GREEN}✅ AGX started successfully${NC}"
fi

# Step 3: Wait for ClickHouse to be ready
echo ""
echo "3. Waiting for ClickHouse to be ready..."
cd "$PROJECT_ROOT"
for i in {1..30}; do
    if docker exec agx-clickhouse-1 clickhouse-client --query "SELECT 1" &> /dev/null; then
        echo -e "${GREEN}✅ ClickHouse is ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ ClickHouse failed to start${NC}"
        exit 1
    fi
    sleep 1
done

# Step 4: Initialize ClickHouse schema
echo ""
echo "4. Initializing ClickHouse schema..."
cd "$SERVICE_DIR"
if python scripts/init_clickhouse.py; then
    echo -e "${GREEN}✅ Schema initialized${NC}"
else
    echo -e "${YELLOW}⚠️  Schema initialization failed (may already exist)${NC}"
fi

# Step 5: Import sample data
echo ""
echo "5. Importing sample data..."
if python scripts/import_sample_data.py; then
    echo -e "${GREEN}✅ Sample data imported${NC}"
else
    echo -e "${YELLOW}⚠️  Sample data import failed${NC}"
fi

# Step 6: Start ETL scheduler
echo ""
echo "6. Starting ETL scheduler..."
# Kill any existing scheduler
pkill -f "etl_scheduler.py" || true
sleep 2

# Start new scheduler
nohup python scripts/etl_scheduler.py > "$LOG_DIR/etl_scheduler.log" 2>&1 &
ETL_PID=$!
echo $ETL_PID > "$LOG_DIR/etl_scheduler.pid"
echo -e "${GREEN}✅ ETL scheduler started (PID: $ETL_PID)${NC}"

# Step 7: Display summary
echo ""
echo "=================================================="
echo -e "${GREEN}✅ AGX Analytics System started successfully!${NC}"
echo "=================================================="
echo ""
echo "📊 Access Points:"
echo "  • AGX Web Interface: http://localhost:8080"
echo "  • ClickHouse Port: 8123"
echo ""
echo "📁 Log Files:"
echo "  • ETL Scheduler: $LOG_DIR/etl_scheduler.log"
echo ""
echo "🔧 Management Commands:"
echo "  • View ETL logs: tail -f $LOG_DIR/etl_scheduler.log"
echo "  • Stop scheduler: kill $ETL_PID"
echo "  • Stop AGX: cd $AGX_DIR && docker compose down"
echo ""
echo "📖 Next Steps:"
echo "  1. Open AGX at http://localhost:8080"
echo "  2. Configure ClickHouse connection:"
echo "     - Host: localhost"
echo "     - Port: 8123"
echo "     - Database: analytics"
echo "     - User: default"
echo "     - Password: (empty)"
echo "  3. Import connection config from: agx/config/clickhouse_connection.json"
echo "  4. Start exploring your strategy data!"
echo ""

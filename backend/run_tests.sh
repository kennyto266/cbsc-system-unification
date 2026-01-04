#!/bin/bash
# Test runner script for CBSC Trading System

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "==================================="
echo "CBSC Trading System Test Runner"
echo "==================================="
echo ""

# Parse arguments
TEST_TYPE=${1:-"all"}
COVERAGE=${COVERAGE:-true}

# Activate virtual environment if exists
if [ -d "../.venv310" ]; then
    source ../.venv310/Scripts/activate 2>/dev/null || source ../.venv310/bin/activate
fi

# Install test dependencies if needed
echo -e "${YELLOW}Checking test dependencies...${NC}"
pip install -q pytest pytest-asyncio pytest-cov httpx aiosqlite 2>/dev/null

# Run tests based on type
case $TEST_TYPE in
    unit)
        echo -e "${YELLOW}Running unit tests...${NC}"
        pytest tests/unit/ -v -m "unit" --tb=short
        ;;
    integration)
        echo -e "${YELLOW}Running integration tests...${NC}"
        pytest tests/integration/ -v -m "integration" --tb=short
        ;;
    e2e)
        echo -e "${YELLOW}Running E2E tests...${NC}"
        pytest tests/e2e/ -v -m "e2e" --tb=short
        ;;
    all)
        echo -e "${YELLOW}Running all tests...${NC}"
        if [ "$COVERAGE" = "true" ]; then
            pytest tests/ -v --cov=. --cov-report=html --cov-report=term
            echo ""
            echo -e "${GREEN}Coverage report generated in htmlcov/ directory${NC}"
        else
            pytest tests/ -v --tb=short
        fi
        ;;
    *)
        echo -e "${RED}Unknown test type: $TEST_TYPE${NC}"
        echo "Usage: ./run_tests.sh [unit|integration|e2e|all]"
        exit 1
        ;;
esac

# Exit with appropriate code
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
fi

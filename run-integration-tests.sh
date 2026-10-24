#!/bin/bash

# Integration Test Runner Script for CBSC Quantitative Trading System

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TEST_TYPE=${1:-"all"}  # Options: frontend, backend, e2e, all
PARALLEL_WORKERS=${2:-4}
COVERAGE=${3:-true}
CLEANUP=${4:-true}

# Directories
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
BACKEND_DIR="$PROJECT_ROOT"
TEST_DIR="$PROJECT_ROOT/tests"
REPORT_DIR="$PROJECT_ROOT/test-reports"
COVERAGE_DIR="$PROJECT_ROOT/coverage"

# Create necessary directories
mkdir -p "$REPORT_DIR"
mkdir -p "$COVERAGE_DIR"

# Logging
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}✓ $1${NC}"
}

error() {
    echo -e "${RED}✗ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Cleanup function
cleanup() {
    if [ "$CLEANUP" = true ]; then
        log "Cleaning up test environment..."
        
        # Stop and remove test containers
        docker-compose -f docker-compose.test.yml down -v --remove-orphans
        
        # Clean up test data
        rm -rf "$TEST_DIR/__pycache__"
        rm -rf "$FRONTEND_DIR/node_modules/.cache"
        
        success "Cleanup completed"
    fi
}

# Setup test environment
setup() {
    log "Setting up test environment..."
    
    # Check Docker is running
    if ! docker info > /dev/null 2>&1; then
        error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    
    # Build test environment
    log "Building test Docker images..."
    docker-compose -f docker-compose.test.yml build
    
    # Start required services
    log "Starting test services..."
    docker-compose -f docker-compose.test.yml up -d postgres-test redis-test
    
    # Wait for services to be healthy
    log "Waiting for services to be ready..."
    timeout 60 bash -c 'until docker-compose -f docker-compose.test.yml ps postgres-test | grep -q "healthy"; do sleep 2; done'
    timeout 60 bash -c 'until docker-compose -f docker-compose.test.yml ps redis-test | grep -q "healthy"; do sleep 2; done'
    
    # Start application
    log "Starting application in test mode..."
    docker-compose -f docker-compose.test.yml up -d app-test
    
    # Wait for application to be ready
    timeout 60 bash -c 'until curl -f http://localhost:3004/health > /dev/null 2>&1; do sleep 5; done'
    
    success "Test environment setup completed"
}

# Run backend integration tests
run_backend_tests() {
    log "Running backend integration tests..."
    
    cd "$BACKEND_DIR"
    
    # Set environment variables
    export DATABASE_URL="postgresql://test_user:test_password@localhost:5433/cbsc_test"
    export REDIS_URL="redis://localhost:6380"
    export TESTING=true
    
    # Create virtual environment if not exists
    if [ ! -d "venv" ]; then
        python -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    pip install -r requirements.txt
    pip install pytest pytest-asyncio pytest-cov pytest-xdist httpx
    
    # Run tests
    if [ "$COVERAGE" = true ]; then
        pytest \
            tests/integration/ \
            -v \
            -n "$PARALLEL_WORKERS" \
            --cov=src \
            --cov-report=html:"$COVERAGE_DIR/backend" \
            --cov-report=xml:"$REPORT_DIR/backend-coverage.xml" \
            --cov-report=term-missing \
            --junitxml="$REPORT_DIR/backend-junit.xml" \
            --maxfail=5
    else
        pytest \
            tests/integration/ \
            -v \
            -n "$PARALLEL_WORKERS" \
            --junitxml="$REPORT_DIR/backend-junit.xml" \
            --maxfail=5
    fi
    
    # Save exit code
    BACKEND_EXIT_CODE=$?
    
    # Deactivate virtual environment
    deactivate
    
    if [ $BACKEND_EXIT_CODE -eq 0 ]; then
        success "Backend integration tests passed"
    else
        error "Backend integration tests failed"
    fi
    
    return $BACKEND_EXIT_CODE
}

# Run frontend integration tests
run_frontend_tests() {
    log "Running frontend integration tests..."
    
    cd "$FRONTEND_DIR"
    
    # Install dependencies
    npm ci
    
    # Start frontend in test mode
    npm run test:ci &
    FRONTEND_PID=$!
    
    # Wait a bit for tests to start
    sleep 5
    
    # Wait for frontend tests to complete
    wait $FRONTEND_PID
    FRONTEND_EXIT_CODE=$?
    
    if [ $FRONTEND_EXIT_CODE -eq 0 ]; then
        success "Frontend integration tests passed"
    else
        error "Frontend integration tests failed"
    fi
    
    return $FRONTEND_EXIT_CODE
}

# Run E2E tests
run_e2e_tests() {
    log "Running E2E tests..."
    
    # Start frontend if not already running
    docker-compose -f docker-compose.test.yml up -d frontend-test
    
    # Wait for frontend to be ready
    timeout 60 bash -c 'until curl -f http://localhost:3001 > /dev/null 2>&1; do sleep 5; done'
    
    cd "$PROJECT_ROOT"
    
    # Install Playwright if not already installed
    if ! command -v npx playwright &> /dev/null; then
        npm install -g @playwright/test
        npx playwright install
    fi
    
    # Run E2E tests
    npx playwright test \
        tests/e2e/ \
        --reporter=html,JUnit \
        --output="$REPORT_DIR/playwright" \
        --junitxml="$REPORT_DIR/e2e-junit.xml" \
        --workers="$PARALLEL_WORKERS" \
        --timeout=60000
    
    E2E_EXIT_CODE=$?
    
    if [ $E2E_EXIT_CODE -eq 0 ]; then
        success "E2E tests passed"
    else
        error "E2E tests failed"
    fi
    
    return $E2E_EXIT_CODE
}

# Generate test report
generate_report() {
    log "Generating test report..."
    
    REPORT_FILE="$REPORT_DIR/integration-test-report-$(date +%Y%m%d-%H%M%S).html"
    
    cat > "$REPORT_FILE" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>Integration Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { color: #333; border-bottom: 2px solid #ddd; padding-bottom: 10px; }
        .section { margin: 20px 0; }
        .success { color: green; }
        .error { color: red; }
        .warning { color: orange; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>CBSC Integration Test Report</h1>
        <p>Generated: $(date)</p>
    </div>
    
    <div class="section">
        <h2>Test Configuration</h2>
        <ul>
            <li>Test Type: $TEST_TYPE</li>
            <li>Parallel Workers: $PARALLEL_WORKERS</li>
            <li>Coverage: $COVERAGE</li>
        </ul>
    </div>
    
    <div class="section">
        <h2>Test Results</h2>
        <table>
            <tr>
                <th>Test Suite</th>
                <th>Status</th>
                <th>Report</th>
            </tr>
EOF

    # Add backend test results
    if [ "$TEST_TYPE" = "backend" ] || [ "$TEST_TYPE" = "all" ]; then
        if [ $BACKEND_EXIT_CODE -eq 0 ]; then
            echo "<tr><td>Backend Integration</td><td class='success'>PASSED</td><td><a href='backend-coverage.html'>Coverage Report</a></td></tr>" >> "$REPORT_FILE"
        else
            echo "<tr><td>Backend Integration</td><td class='error'>FAILED</td><td><a href='backend-junit.xml'>JUnit Report</a></td></tr>" >> "$REPORT_FILE"
        fi
    fi

    # Add frontend test results
    if [ "$TEST_TYPE" = "frontend" ] || [ "$TEST_TYPE" = "all" ]; then
        if [ $FRONTEND_EXIT_CODE -eq 0 ]; then
            echo "<tr><td>Frontend Integration</td><td class='success'>PASSED</td><td><a href='../frontend/coverage/lcov-report/index.html'>Coverage Report</a></td></tr>" >> "$REPORT_FILE"
        else
            echo "<tr><td>Frontend Integration</td><td class='error'>FAILED</td><td><a href='../frontend/test-results.html'>Test Results</a></td></tr>" >> "$REPORT_FILE"
        fi
    fi

    # Add E2E test results
    if [ "$TEST_TYPE" = "e2e" ] || [ "$TEST_TYPE" = "all" ]; then
        if [ $E2E_EXIT_CODE -eq 0 ]; then
            echo "<tr><td>E2E Tests</td><td class='success'>PASSED</td><td><a href='playwright/index.html'>Playwright Report</a></td></tr>" >> "$REPORT_FILE"
        else
            echo "<tr><td>E2E Tests</td><td class='error'>FAILED</td><td><a href='playwright/index.html'>Playwright Report</a></td></tr>" >> "$REPORT_FILE"
        fi
    fi

    cat >> "$REPORT_FILE" << EOF
        </table>
    </div>
    
    <div class="section">
        <h2>Summary</h2>
        <p>Total test time: $SECONDS seconds</p>
        <p>Reports directory: $REPORT_DIR</p>
    </div>
</body>
</html>
EOF

    success "Test report generated: $REPORT_FILE"
}

# Main execution
main() {
    log "Starting CBSC Integration Tests"
    log "Test type: $TEST_TYPE"
    log "Parallel workers: $PARALLEL_WORKERS"
    log "Coverage: $COVERAGE"
    
    # Track overall exit code
    OVERALL_EXIT_CODE=0
    
    # Set up cleanup on exit
    trap cleanup EXIT
    
    # Setup test environment
    setup
    
    # Run tests based on type
    case "$TEST_TYPE" in
        "backend")
            run_backend_tests
            OVERALL_EXIT_CODE=$BACKEND_EXIT_CODE
            ;;
        "frontend")
            run_frontend_tests
            OVERALL_EXIT_CODE=$FRONTEND_EXIT_CODE
            ;;
        "e2e")
            run_e2e_tests
            OVERALL_EXIT_CODE=$E2E_EXIT_CODE
            ;;
        "all")
            # Run all test suites
            run_backend_tests || OVERALL_EXIT_CODE=$?
            run_frontend_tests || { FRONTEND_EXIT_CODE=$?; OVERALL_EXIT_CODE=$?; }
            run_e2e_tests || { E2E_EXIT_CODE=$?; OVERALL_EXIT_CODE=$?; }
            ;;
        *)
            error "Invalid test type: $TEST_TYPE"
            echo "Usage: $0 [backend|frontend|e2e|all] [parallel_workers] [coverage:true|false] [cleanup:true|false]"
            exit 1
            ;;
    esac
    
    # Generate report
    generate_report
    
    # Print summary
    if [ $OVERALL_EXIT_CODE -eq 0 ]; then
        success "All tests passed!"
        log "Reports available in: $REPORT_DIR"
    else
        error "Some tests failed!"
        log "Check the reports in: $REPORT_DIR"
        exit $OVERALL_EXIT_CODE
    fi
}

# Run main function
main "$@"
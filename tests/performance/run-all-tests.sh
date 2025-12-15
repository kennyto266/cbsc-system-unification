#!/bin/bash
# CBSC Performance Test Runner
# Runs all performance tests and generates comprehensive report

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
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

# Check if required tools are installed
check_dependencies() {
    print_status "Checking dependencies..."

    # Check Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js is required but not installed"
        exit 1
    fi

    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi

    # Check if the services are running
    if ! curl -s http://localhost:3003/api/health &> /dev/null; then
        print_warning "Backend service not running on port 3003"
        print_status "Please start the backend service first"
        print_status "Run: cd src/api && python -m uvicorn main:app --reload --port 3003"
    fi

    if ! curl -s http://localhost:3000 &> /dev/null; then
        print_warning "Frontend service not running on port 3000"
        print_status "Please start the frontend service first"
        print_status "Run: cd frontend && npm run dev"
    fi

    print_success "Dependencies check completed"
}

# Install test dependencies
install_dependencies() {
    print_status "Installing test dependencies..."

    # Frontend dependencies
    if [ -f "tests/performance/package.json" ]; then
        cd tests/performance
        npm install
        cd ../..
    fi

    # Python dependencies
    if [ -f "tests/performance/requirements.txt" ]; then
        pip3 install -r tests/performance/requirements.txt
    fi

    # Load testing tools
    if ! command -v artillery &> /dev/null; then
        print_status "Installing Artillery..."
        npm install -g artillery
    fi

    if ! command -v locust &> /dev/null; then
        print_status "Installing Locust..."
        pip3 install locust
    fi

    print_success "Dependencies installation completed"
}

# Run frontend performance tests
run_frontend_tests() {
    print_status "Running frontend performance tests..."

    # Run Lighthouse tests
    if [ -f "frontend/tests/performance/lighthouse.config.js" ]; then
        print_status "Running Lighthouse audits..."
        cd frontend
        npx lhci autorun
        cd ..
    fi

    # Run Jest performance tests
    if [ -f "frontend/tests/performance/performance.spec.js" ]; then
        print_status "Running Jest performance tests..."
        cd frontend
        npm run test:performance || true
        cd ..
    fi

    # Analyze bundle size
    if [ -f "frontend/tests/performance/bundle-analyzer.js" ]; then
        print_status "Analyzing bundle size..."
        node frontend/tests/performance/bundle-analyzer.js
    fi

    # Memory leak detection
    if [ -f "frontend/tests/performance/memory-leak-detector.js" ]; then
        print_status "Running memory leak detection..."
        node frontend/tests/performance/memory-leak-detector.js
    fi

    print_success "Frontend performance tests completed"
}

# Run backend performance tests
run_backend_tests() {
    print_status "Running backend performance tests..."

    # Run API performance tests
    if [ -f "tests/performance/api-performance-test.py" ]; then
        print_status "Running API performance tests..."
        python3 tests/performance/api-performance-test.py
    fi

    print_success "Backend performance tests completed"
}

# Run load tests
run_load_tests() {
    print_status "Running load tests..."

    # Artillery tests
    if [ -f "tests/load/load-test-config.yml" ]; then
        print_status "Running Artillery load tests..."
        artillery run tests/load/load-test-config.yml
    fi

    # Locust tests (in background)
    if [ -f "tests/load/locustfile.py" ]; then
        print_status "Running Locust load tests..."
        # Run Locust with headless mode for automated testing
        locust -f tests/load/locustfile.py --headless --users 100 --spawn-rate 10 --run-time 60s --host http://localhost:3003
    fi

    print_success "Load tests completed"
}

# Run stress tests
run_stress_tests() {
    print_status "Running stress tests..."

    if [ -f "tests/stress/stress-test.py" ]; then
        print_status "Running stress tests..."
        python3 tests/stress/stress-test.py
    fi

    print_success "Stress tests completed"
}

# Collect benchmarks
collect_benchmarks() {
    print_status "Collecting performance benchmarks..."

    if [ -f "tests/performance/benchmark-collector.py" ]; then
        python3 tests/performance/benchmark-collector.py
    fi

    print_success "Benchmark collection completed"
}

# Generate comprehensive report
generate_report() {
    print_status "Generating comprehensive performance report..."

    REPORT_DIR="performance-reports-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$REPORT_DIR"

    # Copy all generated reports
    find . -name "*performance*.json" -type f -exec cp {} "$REPORT_DIR/" \;
    find . -name "*performance*.html" -type f -exec cp {} "$REPORT_DIR/" \;
    find . -name "*benchmark*.json" -type f -exec cp {} "$REPORT_DIR/" \;
    find . -name "*benchmark*.html" -type f -exec cp {} "$REPORT_DIR/" \;
    find . -name "*stress*.json" -type f -exec cp {} "$REPORT_DIR/" \;
    find . -name "*charts*.png" -type f -exec cp {} "$REPORT_DIR/" \;

    # Create summary report
    cat > "$REPORT_DIR/test-summary.md" << EOF
# CBSC Performance Test Summary

## Test Execution Date
$(date)

## Tests Run
1. Frontend Performance Tests
   - Lighthouse audits
   - Bundle size analysis
   - Memory leak detection

2. Backend Performance Tests
   - API response time measurements
   - Database query performance

3. Load Tests
   - Concurrent user simulation
   - Throughput measurement

4. Stress Tests
   - Maximum capacity testing
   - Resource exhaustion tests

5. Benchmarks
   - Performance baseline collection
   - Historical comparison

## Performance Targets
- API response time: <200ms (P95)
- Page load time: <3s
- Chart render time: <100ms for 10K points
- Memory usage: <100MB for dashboard
- Concurrent users: 1000+ without degradation

## Files Generated
EOF

    # List all files in the report directory
    ls -la "$REPORT_DIR" >> "$REPORT_DIR/test-summary.md"

    print_success "Comprehensive report generated in: $REPORT_DIR"
}

# Main execution
main() {
    echo "🚀 CBSC Quantitative Trading System - Performance Test Suite"
    echo "========================================================="

    # Create results directory
    mkdir -p performance-results

    # Check dependencies
    check_dependencies

    # Install dependencies if needed
    if [ "$1" = "--install" ]; then
        install_dependencies
    fi

    # Run tests
    echo -e "\n${BLUE}Starting Performance Tests...${NC}\n"

    # Run all test suites
    run_frontend_tests
    run_backend_tests
    run_load_tests
    run_stress_tests
    collect_benchmarks

    # Generate final report
    generate_report

    echo -e "\n${GREEN}✅ All performance tests completed successfully!${NC}\n"
}

# Display usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --install    Install all required dependencies"
    echo "  --frontend   Run only frontend performance tests"
    echo "  --backend    Run only backend performance tests"
    echo "  --load       Run only load tests"
    echo "  --stress     Run only stress tests"
    echo "  --benchmark  Run only benchmark collection"
    echo "  --help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                # Run all performance tests"
    echo "  $0 --install      # Install dependencies first"
    echo "  $0 --frontend     # Run only frontend tests"
}

# Parse command line arguments
case "$1" in
    --help)
        usage
        exit 0
        ;;
    --install)
        main --install
        ;;
    --frontend)
        check_dependencies
        run_frontend_tests
        ;;
    --backend)
        check_dependencies
        run_backend_tests
        ;;
    --load)
        check_dependencies
        run_load_tests
        ;;
    --stress)
        check_dependencies
        run_stress_tests
        ;;
    --benchmark)
        check_dependencies
        collect_benchmarks
        ;;
    *)
        main
        ;;
esac
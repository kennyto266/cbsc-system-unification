#!/bin/bash

# CBSC System Health Check Script
# Monitors the health of all deployed services

set -euo pipefail

# Default values
ENVIRONMENT=${1:-staging}
NAMESPACE="cbsc-${ENVIRONMENT}"
CONTINUOUS=false
INTERVAL=30
TIMEOUT=5
FAILURES=0
MAX_FAILURES=3
VERBOSE=false
OUTPUT_FORMAT="table"  # table, json, prometheus

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Service endpoints to check
declare -A SERVICES=(
    ["frontend"]="http://frontend:3000/health"
    ["api-gateway"]="http://api-gateway:8000/health"
    ["user-management"]="http://user-management:3004/health"
    ["strategy-dashboard"]="http://strategy-dashboard:3003/health"
    ["quant-system"]="http://quant-system:8001/health"
    ["config-service"]="http://config-service:3005/health"
    ["postgres"]=""
    ["redis"]=""
)

# Health check results
declare -A RESULTS

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

# Print usage
print_usage() {
    cat << EOF
Usage: $0 [ENVIRONMENT] [OPTIONS]

ENVIRONMENTS:
    dev         Check development environment
    staging     Check staging environment (default)
    production  Check production environment

OPTIONS:
    --continuous     Run continuous monitoring
    --interval N     Set check interval in seconds (default: 30)
    --timeout N      Set request timeout in seconds (max: 30)
    --max-failures N Max failures before alert (default: 3)
    --output FORMAT  Output format: table, json, prometheus
    --verbose        Enable verbose logging
    --help, -h       Show this help message

EXAMPLES:
    $0 staging --continuous --interval 60
    $0 production --output json
    $0 dev --verbose --timeout 10

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --continuous)
                CONTINUOUS=true
                shift
                ;;
            --interval)
                INTERVAL="$2"
                shift 2
                ;;
            --timeout)
                TIMEOUT="$2"
                shift 2
                ;;
            --max-failures)
                MAX_FAILURES="$2"
                shift 2
                ;;
            --output)
                OUTPUT_FORMAT="$2"
                shift 2
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --help|-h)
                print_usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                print_usage
                exit 1
                ;;
        esac
    done
}

# Check HTTP service health
check_http_service() {
    local service_name=$1
    local endpoint=$2
    local status="unknown"
    local response_time=0
    local error=""

    log_verbose "Checking $service_name at $endpoint"

    # Use kubectl exec to run curl from a pod
    local start_time=$(date +%s%N)
    local http_code=$(kubectl exec -n "$NAMESPACE" deployment/frontend -- \
        curl -s -o /dev/null -w "%{http_code}" \
        --max-time "$TIMEOUT" \
        "$endpoint" 2>&1 || echo "000")
    local end_time=$(date +%s%N)
    response_time=$(( (end_time - start_time) / 1000000 ))

    if [ "$http_code" = "200" ]; then
        status="healthy"
        RESULTS["$service_name-status"]="healthy"
        RESULTS["$service_name-response-time"]=$response_time
    elif [ "$http_code" = "000" ]; then
        status="unhealthy"
        error="Connection failed"
        RESULTS["$service_name-status"]="unhealthy"
        RESULTS["$service_name-error"]=$error
        RESULTS["$service_name-response-time"]=$TIMEOUT
    else
        status="degraded"
        error="HTTP $http_code"
        RESULTS["$service_name-status"]="degraded"
        RESULTS["$service_name-error"]=$error
        RESULTS["$service_name-response-time"]=$response_time
    fi

    if [ "$VERBOSE" = true ]; then
        echo "  Status: $status"
        echo "  Response Time: ${response_time}ms"
        [ -n "$error" ] && echo "  Error: $error"
    fi
}

# Check PostgreSQL health
check_postgres() {
    log_verbose "Checking PostgreSQL health"

    local status="unknown"
    local error=""
    local connections=0

    # Check pod status
    if kubectl get pod -n "$NAMESPACE" -l app=postgres --no-headers | grep -q "Running"; then
        # Check if database is accepting connections
        if kubectl exec -n "$NAMESPACE" deployment/postgres -- \
            pg_isready -U postgres -d cbsc &> /dev/null; then
            status="healthy"
            connections=$(kubectl exec -n "$NAMESPACE" deployment/postgres -- \
                psql -U postgres -d cbsc -t -c "SELECT count(*) FROM pg_stat_activity;" | tr -d ' ')
        else
            status="unhealthy"
            error="Database not ready"
        fi
    else
        status="unhealthy"
        error="Pod not running"
    fi

    RESULTS["postgres-status"]=$status
    RESULTS["postgres-connections"]=$connections
    [ -n "$error" ] && RESULTS["postgres-error"]=$error

    if [ "$VERBOSE" = true ]; then
        echo "  Status: $status"
        echo "  Active Connections: $connections"
        [ -n "$error" ] && echo "  Error: $error"
    fi
}

# Check Redis health
check_redis() {
    log_verbose "Checking Redis health"

    local status="unknown"
    local error=""
    local memory=0

    # Check pod status
    if kubectl get pod -n "$NAMESPACE" -l app=redis --no-headers | grep -q "Running"; then
        # Check if Redis is responding
        if kubectl exec -n "$NAMESPACE" deployment/redis -- \
            redis-cli ping | grep -q "PONG"; then
            status="healthy"
            memory=$(kubectl exec -n "$NAMESPACE" deployment/redis -- \
                redis-cli info memory | grep "used_memory_human" | cut -d: -f2 | tr -d '\r')
        else
            status="unhealthy"
            error="Redis not responding"
        fi
    else
        status="unhealthy"
        error="Pod not running"
    fi

    RESULTS["redis-status"]=$status
    RESULTS["redis-memory"]=$memory
    [ -n "$error" ] && RESULTS["redis-error"]=$error

    if [ "$VERBOSE" = true ]; then
        echo "  Status: $status"
        echo "  Memory Usage: $memory"
        [ -n "$error" ] && echo "  Error: $error"
    fi
}

# Format output as table
format_table() {
    echo -e "\n${BLUE}CBSC System Health Status - $ENVIRONMENT${NC}"
    echo -e "$(date '+%Y-%m-%d %H:%M:%S')"
    echo
    printf "%-20s %-12s %-15s %-12s %s\n" "SERVICE" "STATUS" "RESPONSE TIME" "ADDITIONAL" "ERROR"
    printf "%-20s %-12s %-15s %-12s %s\n" "--------" "------" "-------------" "----------" "-----"

    for service in "${!SERVICES[@]}"; do
        local status="${RESULTS[$service-status]:-unknown}"
        local response_time="${RESULTS[$service-response-time]:-0}ms"
        local additional=""
        local error="${RESULTS[$service-error]:-}"

        # Set color based on status
        case $status in
            healthy)
                status=$(echo -e "${GREEN}$status${NC}")
                ;;
            unhealthy)
                status=$(echo -e "${RED}$status${NC}")
                ;;
            degraded)
                status=$(echo -e "${YELLOW}$status${NC}")
                ;;
        esac

        # Add additional info for database services
        if [ "$service" = "postgres" ]; then
            additional="${RESULTS[postgres-connections]:-0} conn"
        elif [ "$service" = "redis" ]; then
            additional="${RESULTS[redis-memory]:-0B}"
        fi

        printf "%-20s %-12s %-15s %-12s %s\n" \
            "$service" "$status" "$response_time" "$additional" "$error"
    done

    echo
}

# Format output as JSON
format_json() {
    local json='{
        "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
        "environment": "'$ENVIRONMENT'",
        "services": {'

    local first=true
    for service in "${!SERVICES[@]}"; do
        if [ "$first" = false ]; then
            json+=','
        fi
        first=false

        json+='
            "'$service'": {
                "status": "'${RESULTS[$service-status]:-unknown}'",
                "response_time": '${RESULTS[$service-response-time]:-0}',
                "error": "'${RESULTS[$service-error]:-''}'"'

        if [ "$service" = "postgres" ]; then
            json+=',
                "connections": '${RESULTS[postgres-connections]:-0}
        elif [ "$service" = "redis" ]; then
            json+=',
                "memory": "'${RESULTS[redis-memory]:-0}'"
        fi

        json+='
        }'
    done

    json+='
        }
    }'

    echo "$json" | jq .
}

# Format output for Prometheus
format_prometheus() {
    local timestamp=$(date +%s)
    echo "# HELP cbsc_service_status Service status (1=healthy, 0.5=degraded, 0=unhealthy)"
    echo "# TYPE cbsc_service_status gauge"

    for service in "${!SERVICES[@]}"; do
        local status="${RESULTS[$service-status]:-unknown}"
        local value=0

        case $status in
            healthy) value=1 ;;
            degraded) value=0.5 ;;
            unhealthy) value=0 ;;
            *) value=0 ;;
        esac

        echo "cbsc_service_status{service=\"$service\",environment=\"$ENVIRONMENT\"} $value $timestamp"
    done

    echo
    echo "# HELP cbsc_service_response_seconds Service response time in milliseconds"
    echo "# TYPE cbsc_service_response_seconds gauge"

    for service in "${!SERVICES[@]}"; do
        local response_time="${RESULTS[$service-response-time]:-0}"
        echo "cbsc_service_response_seconds{service=\"$service\",environment=\"$ENVIRONMENT\"} $response_time $timestamp"
    done

    echo
    echo "# HELP cbsc_postgres_connections Active PostgreSQL connections"
    echo "# TYPE cbsc_postgres_connections gauge"
    echo "cbsc_postgres_connections{environment=\"$ENVIRONMENT\"} ${RESULTS[postgres-connections]:-0} $timestamp"
}

# Send alert
send_alert() {
    local message="CBSC System Health Alert - $ENVIRONMENT environment"

    # Check for unhealthy services
    local unhealthy_services=""
    for service in "${!SERVICES[@]}"; do
        local status="${RESULTS[$service-status]:-unknown}"
        if [ "$status" = "unhealthy" ]; then
            unhealthy_services+="$service "
        fi
    done

    if [ -n "$unhealthy_services" ]; then
        message+=" - Unhealthy services: $unhealthy_services"

        # Send Slack notification if webhook is configured
        if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
            curl -X POST -H 'Content-type: application/json' \
                --data "{\"text\":\"$message\"}" \
                "$SLACK_WEBHOOK_URL" &> /dev/null || true
        fi

        # Send email if configured
        if command -v mail &> /dev/null && [ -n "${ALERT_EMAIL:-}" ]; then
            echo "$message" | mail -s "CBSC Health Alert" "$ALERT_EMAIL" || true
        fi

        log_error "$message"
    fi
}

# Run health checks
run_checks() {
    # Clear previous results
    RESULTS=()

    # Check all services
    for service in "${!SERVICES[@]}"; do
        local endpoint="${SERVICES[$service]}"

        if [ -n "$endpoint" ]; then
            check_http_service "$service" "$endpoint"
        else
            if [ "$service" = "postgres" ]; then
                check_postgres
            elif [ "$service" = "redis" ]; then
                check_redis
            fi
        fi
    done

    # Format and output results
    case $OUTPUT_FORMAT in
        table)
            format_table
            ;;
        json)
            format_json
            ;;
        prometheus)
            format_prometheus
            ;;
        *)
            log_error "Unknown output format: $OUTPUT_FORMAT"
            exit 1
            ;;
    esac

    # Check for failures
    local current_failures=0
    for service in "${!SERVICES[@]}"; do
        local status="${RESULTS[$service-status]:-unknown}"
        if [ "$status" = "unhealthy" ]; then
            ((current_failures++))
        fi
    done

    if [ $current_failures -gt 0 ]; then
        ((FAILURES++))
        if [ $FAILURES -ge $MAX_FAILURES ]; then
            send_alert
            FAILURES=0  # Reset counter after sending alert
        fi
    else
        FAILURES=0
    fi
}

# Main execution
main() {
    log_info "Starting health check for $ENVIRONMENT environment..."

    # Parse arguments
    parse_args "${@:2}"

    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi

    # Check if namespace exists
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_error "Namespace $NAMESPACE does not exist"
        exit 1
    fi

    # Run initial check
    run_checks

    # Continuous monitoring if requested
    if [ "$CONTINUOUS" = true ]; then
        log_info "Starting continuous monitoring (interval: ${INTERVAL}s)"
        while true; do
            sleep "$INTERVAL"
            run_checks
        done
    fi
}

# Trap signals
trap 'log_info "Health check interrupted"; exit 0' INT TERM

# Run main function
main "$@"
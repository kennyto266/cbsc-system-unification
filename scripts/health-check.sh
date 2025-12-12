#!/bin/bash

# CBSC System Health Check Script
# Author: CBSC Development Team
# Description: Comprehensive health check for all CBSC services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.dev.yml"
PROJECT_NAME="cbsc-dev"
TIMEOUT=10

# Service endpoints to check
declare -A SERVICES=(
    ["API Gateway"]="http://localhost:8000/health"
    ["Frontend"]="http://localhost:3000"
    ["Unified Dashboard"]="http://localhost:3001"
    ["User Management"]="http://localhost:3004/health"
    ["Strategy Dashboard"]="http://localhost:3003/health"
    ["Config Service"]="http://localhost:3005/health"
    ["Quant System"]="http://localhost:8001/api/health"
    ["PgAdmin"]="http://localhost:5050"
    ["Redis Commander"]="http://localhost:8081"
    ["Grafana"]="http://localhost:3002"
    ["Prometheus"]="http://localhost:9090"
)

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

print_header() {
    echo -e "${PURPLE}$1${NC}"
}

# Function to check HTTP service
check_http_service() {
    local service_name="$1"
    local url="$2"

    if curl -f -s --max-time $TIMEOUT "$url" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to check Docker container
check_docker_container() {
    local service_name="$1"

    if docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME ps "$service_name" | grep -q "Up"; then
        return 0
    else
        return 1
    fi
}

# Function to get container status
get_container_status() {
    local service_name="$1"
    docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME ps "$service_name" --format "table {{.Status}}" | tail -n 1
}

# Function to check database connection
check_database() {
    print_status "Checking PostgreSQL connection..."

    if docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME exec -T postgres pg_isready -U cbsc_dev -d cbsc_dev > /dev/null 2>&1; then
        print_success "✅ PostgreSQL is healthy and accepting connections"

        # Get database stats
        local db_stats=$(docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME exec -T postgres psql -U cbsc_dev -d cbsc_dev -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d ' ')
        print_status "Database tables: $db_stats"

        return 0
    else
        print_error "❌ PostgreSQL is not responding"
        return 1
    fi
}

# Function to check Redis connection
check_redis() {
    print_status "Checking Redis connection..."

    if docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME exec -T redis redis-cli ping > /dev/null 2>&1; then
        print_success "✅ Redis is healthy and accepting connections"

        # Get Redis info
        local redis_info=$(docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME exec -T redis redis-cli info server 2>/dev/null | grep "redis_version" | cut -d: -f2 | tr -d '\r')
        print_status "Redis version: $redis_info"

        return 0
    else
        print_error "❌ Redis is not responding"
        return 1
    fi
}

# Function to check service logs for errors
check_service_logs() {
    local service_name="$1"
    local lines=10

    print_status "Checking recent logs for $service_name..."

    local error_count=$(docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME logs --tail=$lines "$service_name" 2>&1 | grep -i "error\|exception\|failed" | wc -l)

    if [ "$error_count" -gt 0 ]; then
        print_warning "⚠️ Found $error_count potential errors in recent logs for $service_name"
        docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME logs --tail=5 "$service_name" 2>&1 | grep -i "error\|exception\|failed" | tail -3
    else
        print_success "✅ No errors found in recent logs for $service_name"
    fi
}

# Function to get system resources
check_system_resources() {
    print_header "System Resources"

    # Docker system info
    print_status "Docker system usage:"
    docker system df --format "table {{.Type}}\t{{.TotalCount}}\t{{.Size}}\t{{.Reclaimable}}" | head -10

    echo ""
    print_status "Container resource usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
}

# Function to check port availability
check_ports() {
    print_header "Port Availability Check"

    declare -A PORTS=(
        ["8000"]="API Gateway"
        ["3000"]="Frontend"
        ["3001"]="Unified Dashboard"
        ["3004"]="User Management"
        ["3003"]="Strategy Dashboard"
        ["3005"]="Config Service"
        ["8001"]="Quant System"
        ["5432"]="PostgreSQL"
        ["6379"]="Redis"
        ["5050"]="PgAdmin"
        ["8081"]="Redis Commander"
    )

    for port in "${!PORTS[@]}"; do
        if netstat -tuln 2>/dev/null | grep -q ":$port "; then
            print_success "✅ Port $port (${PORTS[$port]}) is listening"
        else
            print_warning "⚠️ Port $port (${PORTS[$port]}) is not listening"
        fi
    done
}

# Main health check function
run_health_check() {
    print_header "🔍 CBSC System Health Check"
    echo ""

    local total_services=0
    local healthy_services=0
    local unhealthy_services=0
    local optional_services=0

    # Check core services first
    print_header "Core Services Health Check"

    # Database checks
    echo ""
    if check_database; then
        ((healthy_services++))
    else
        ((unhealthy_services++))
    fi
    ((total_services++))

    echo ""
    if check_redis; then
        ((healthy_services++))
    else
        ((unhealthy_services++))
    fi
    ((total_services++))

    # Check application services
    echo ""
    print_header "Application Services Health Check"

    for service_name in "${!SERVICES[@]}"; do
        url="${SERVICES[$service_name]}"

        # Skip optional services in main count
        if [[ "$service_name" == "PgAdmin" || "$service_name" == "Redis Commander" || "$service_name" == "Grafana" || "$service_name" == "Prometheus" ]]; then
            ((optional_services++))
        else
            ((total_services++))
        fi

        echo -n "Checking $service_name... "

        if check_http_service "$service_name" "$url"; then
            print_success "✅ Healthy"
            if [[ "$service_name" != "PgAdmin" && "$service_name" != "Redis Commander" && "$service_name" != "Grafana" && "$service_name" != "Prometheus" ]]; then
                ((healthy_services++))
            fi
        else
            # Check if container is running but service might be starting
            container_name=$(echo "$service_name" | tr '[:upper:]' '[:lower:]' | sed 's/ /-/g')
            if check_docker_container "$container_name"; then
                status=$(get_container_status "$container_name")
                print_warning "⚠️ Container running but service not responding ($status)"
            else
                print_error "❌ Unhealthy - Container not running"
                if [[ "$service_name" != "PgAdmin" && "$service_name" != "Redis Commander" && "$service_name" != "Grafana" && "$service_name" != "Prometheus" ]]; then
                    ((unhealthy_services++))
                fi
            fi
        fi
    done

    # Check container logs for critical services
    echo ""
    print_header "Service Logs Check"
    check_service_logs "api-gateway"
    check_service_logs "postgres"
    check_service_logs "redis"

    # System resources
    echo ""
    check_system_resources

    # Port availability
    echo ""
    check_ports

    # Summary
    echo ""
    print_header "📊 Health Check Summary"
    echo ""
    echo "Core Services:"
    echo -e "  Total: $total_services"
    echo -e "  ${GREEN}Healthy: $healthy_services${NC}"
    echo -e "  ${RED}Unhealthy: $unhealthy_services${NC}"
    echo ""
    echo "Optional Development Tools: $optional_services"
    echo ""

    # Calculate health percentage
    if [ "$total_services" -gt 0 ]; then
        health_percentage=$((healthy_services * 100 / total_services))
        echo -e "Overall System Health: ${health_percentage}%"

        if [ "$health_percentage" -ge 80 ]; then
            echo -e "${GREEN}✅ System is healthy${NC}"
        elif [ "$health_percentage" -ge 60 ]; then
            echo -e "${YELLOW}⚠️ System has some issues${NC}"
        else
            echo -e "${RED}❌ System has significant issues${NC}"
        fi
    fi

    echo ""

    # Recommendations
    if [ "$unhealthy_services" -gt 0 ]; then
        print_header "🔧 Recommendations"
        echo ""
        echo "1. Check service logs: docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME logs [service-name]"
        echo "2. Restart unhealthy services: docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME restart [service-name]"
        echo "3. Check resource usage: docker stats"
        echo "4. Verify port availability: netstat -tuln | grep [port]"
        echo "5. Run full restart: ./scripts/dev-start.sh --restart"
    fi

    return $unhealthy_services
}

# Function to watch health continuously
watch_health() {
    local interval=${1:-30}

    print_header "👁️ Watching CBSC System Health (interval: ${interval}s)"
    echo "Press Ctrl+C to stop watching"
    echo ""

    while true; do
        clear
        run_health_check
        echo ""
        print_status "Next check in ${interval} seconds... $(date)"
        sleep $interval
    done
}

# Function to show usage
show_usage() {
    echo -e "${BLUE}CBSC System Health Check Script${NC}"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --watch [seconds]  Watch health status continuously (default: 30s)"
    echo "  --quiet          Suppress detailed output, show summary only"
    echo "  --help           Show this help message"
    echo ""
}

# Parse command line arguments
case "${1:-}" in
    --watch)
        watch_health "${2:-30}"
        ;;
    --quiet)
        # Redirect all output except summary to /dev/null
        exec 3>&1
        exec 1>/dev/null
        run_health_check >&3
        exec 1>&3
        ;;
    --help|-h)
        show_usage
        ;;
    "")
        run_health_check
        ;;
    *)
        print_error "Unknown option: $1"
        show_usage
        exit 1
        ;;
esac
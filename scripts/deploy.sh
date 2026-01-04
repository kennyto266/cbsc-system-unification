#!/bin/bash

# CBSC 策略管理系統 - 統一部署腳本
# 支持開發、測試和生產環境的自動化部署

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$PROJECT_ROOT/.env"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"
COMPOSE_PROD_FILE="$PROJECT_ROOT/docker-compose.prod.yml"

# Default values
ENVIRONMENT="dev"
SKIP_BUILD=false
SKIP_MIGRATION=false
SKIP_BACKUP=false
VERBOSE=false
DRY_RUN=false
HEALTH_CHECK_TIMEOUT=300

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_help() {
    cat << EOF
CBSC Strategy Management System - Deployment Script

Usage:
    $0 [OPTIONS] COMMAND [ARGS]

Commands:
    deploy           Deploy the system (default)
    start            Start all services
    stop             Stop all services
    restart          Restart all services
    status           Show service status
    logs             Show service logs
    backup           Backup data
    restore          Restore data
    cleanup          Cleanup unused resources
    health           Health check all services

Options:
    -e, --env        Environment (dev|test|prod) [default: dev]
    -f, --file       Compose file path [default: docker-compose.yml]
    -b, --skip-build Skip building images
    -m, --skip-migration Skip database migrations
    -s, --skip-backup Skip backup before deployment
    -t, --timeout    Health check timeout in seconds [default: 300]
    -v, --verbose    Verbose output
    -d, --dry-run    Dry run (show commands only)
    -h, --help       Show this help

Examples:
    $0 deploy --env prod
    $0 start --env test
    $0 logs backend
    $0 backup --env prod
    $0 cleanup

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--env)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -f|--file)
                COMPOSE_FILE="$2"
                shift 2
                ;;
            -b|--skip-build)
                SKIP_BUILD=true
                shift
                ;;
            -m|--skip-migration)
                SKIP_MIGRATION=true
                shift
                ;;
            -s|--skip-backup)
                SKIP_BACKUP=true
                shift
                ;;
            -t|--timeout)
                HEALTH_CHECK_TIMEOUT="$2"
                shift 2
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            deploy|start|stop|restart|status|logs|backup|restore|cleanup|health)
                COMMAND="$1"
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Validate environment
validate_environment() {
    local valid_envs=("dev" "test" "prod")
    if [[ ! " ${valid_envs[@]} " =~ " ${ENVIRONMENT} " ]]; then
        log_error "Invalid environment: $ENVIRONMENT"
        log_info "Valid environments: ${valid_envs[*]}"
        exit 1
    fi
}

# Load configuration
load_config() {
    local env_file="$PROJECT_ROOT/.env.$ENVIRONMENT"
    if [[ -f "$env_file" ]]; then
        log_info "Loading environment from: $env_file"
        source "$env_file"
    elif [[ -f "$CONFIG_FILE" ]]; then
        log_info "Loading environment from: $CONFIG_FILE"
        source "$CONFIG_FILE"
    else
        log_warning "No environment file found, using defaults"
    fi

    # Export required variables
    export ENVIRONMENT
    export COMPOSE_PROJECT_NAME="cbsc-$ENVIRONMENT"
    export COMPOSE_FILE="$COMPOSE_FILE"

    # Use production compose file for production environment
    if [[ "$ENVIRONMENT" == "prod" ]]; then
        export COMPOSE_FILE="$COMPOSE_PROD_FILE"
        log_info "Using production compose file: $COMPOSE_FILE"
    fi
}

# Prepare Docker environment
prepare_docker() {
    log_info "Preparing Docker environment..."

    # Create necessary directories
    local directories=("logs" "uploads" "static" "data" "config" "ssl")
    for dir in "${directories[@]}"; do
        mkdir -p "$PROJECT_ROOT/$dir"
    done

    # Create log subdirectories
    mkdir -p "$PROJECT_ROOT/logs/nginx"
    mkdir -p "$PROJECT_ROOT/logs/strategies"
    mkdir -p "$PROJECT_ROOT/logs/backtest"

    # Set permissions
    chmod -R 755 "$PROJECT_ROOT/logs"
    chmod -R 755 "$PROJECT_ROOT/uploads"

    log_success "Docker environment prepared"
}

# Build Docker images
build_images() {
    if [[ "$SKIP_BUILD" == "true" ]]; then
        log_info "Skipping image build"
        return
    fi

    log_info "Building Docker images..."
    local build_cmd="docker-compose build"

    if [[ "$ENVIRONMENT" == "prod" ]]; then
        build_cmd="$build_cmd --parallel"
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] $build_cmd"
    else
        $build_cmd
        log_success "Docker images built successfully"
    fi
}

# Deploy services
deploy_services() {
    log_info "Deploying services to $ENVIRONMENT environment..."

    local deploy_cmd="docker-compose up -d"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] $deploy_cmd"
        return
    fi

    # Deploy services
    $deploy_cmd

    # Wait for services to be healthy
    wait_for_health

    log_success "Services deployed successfully"
}

# Wait for services to be healthy
wait_for_health() {
    log_info "Waiting for services to be healthy (timeout: ${HEALTH_CHECK_TIMEOUT}s)..."

    local services=("postgres" "redis" "influxdb" "cbsc-strategy-api")
    local start_time=$(date +%s)
    local timeout_time=$((start_time + HEALTH_CHECK_TIMEOUT))

    for service in "${services[@]}"; do
        local container_name="cbsc-$ENVIRONMENT-$service"
        if [[ "$ENVIRONMENT" == "prod" ]]; then
            container_name="cbsc-$service-prod"
        fi

        log_info "Checking health of: $service"

        while [[ $(date +%s) -lt $timeout_time ]]; do
            local health_status=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "none")

            if [[ "$health_status" == "healthy" ]]; then
                log_success "$service is healthy"
                break
            elif [[ "$health_status" == "none" ]]; then
                # Service doesn't have health check, just check if running
                if docker ps --format 'table {{.Names}}' | grep -q "$container_name"; then
                    log_success "$service is running"
                    break
                fi
            fi

            sleep 5
        done

        if [[ $(date +%s) -ge $timeout_time ]]; then
            log_error "Timeout waiting for $service to be healthy"
            docker logs "$container_name" --tail 50
            exit 1
        fi
    done
}

# Run database migrations
run_migrations() {
    if [[ "$SKIP_MIGRATION" == "true" ]]; then
        log_info "Skipping database migrations"
        return
    fi

    log_info "Running database migrations..."

    local migrate_cmd="docker-compose exec cbsc-strategy-api python -m alembic upgrade head"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] $migrate_cmd"
    else
        # Wait a bit for database to be ready
        sleep 10
        $migrate_cmd
        log_success "Database migrations completed"
    fi
}

# Backup data
backup_data() {
    if [[ "$SKIP_BACKUP" == "true" ]]; then
        log_info "Skipping backup"
        return
    fi

    local backup_dir="$PROJECT_ROOT/backups"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$backup_dir/cbsc_backup_$timestamp.tar.gz"

    log_info "Creating backup: $backup_file"

    mkdir -p "$backup_dir"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would create backup: $backup_file"
        return
    fi

    # Create backup of volumes and configurations
    local backup_items=(
        "postgres_data:/var/lib/postgresql/data"
        "redis_data:/data"
        "influxdb_data:/var/lib/influxdb2"
        "config:/app/config"
        "ssl:/etc/nginx/ssl"
    )

    # Create temporary container for backup
    docker run --rm \
        -v "$backup_dir:/backup" \
        -v "$PROJECT_ROOT:/source:ro" \
        alpine:latest \
        tar czf "/backup/$(basename "$backup_file")" \
        -C /source \
        .env* config/ ssl/

    log_success "Backup created: $backup_file"
}

# Show service status
show_status() {
    log_info "Service status:"
    docker-compose ps

    log_info "\nResource usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
}

# Show logs
show_logs() {
    local service="${1:-}"
    local log_cmd="docker-compose logs"

    if [[ -n "$service" ]]; then
        log_cmd="$log_cmd $service"
    fi

    if [[ "$VERBOSE" == "true" ]]; then
        log_cmd="$log_cmd --follow --tail=100"
    else
        log_cmd="$log_cmd --tail=50"
    fi

    $log_cmd
}

# Cleanup unused resources
cleanup_resources() {
    log_info "Cleaning up unused Docker resources..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would cleanup unused resources"
        return
    fi

    # Remove stopped containers
    docker container prune -f

    # Remove unused images
    docker image prune -f

    # Remove unused networks
    docker network prune -f

    # Remove unused volumes (be careful with this in production)
    if [[ "$ENVIRONMENT" != "prod" ]]; then
        docker volume prune -f
    fi

    log_success "Cleanup completed"
}

# Health check all services
health_check() {
    log_info "Performing health check..."

    local services=("postgres" "redis" "influxdb" "cbsc-strategy-api" "nginx" "prometheus" "grafana")
    local unhealthy_services=()

    for service in "${services[@]}"; do
        local container_name="cbsc-$ENVIRONMENT-$service"
        if [[ "$ENVIRONMENT" == "prod" ]]; then
            container_name="cbsc-$service-prod"
        fi

        if docker ps --format 'table {{.Names}}' | grep -q "$container_name"; then
            local health_status=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "none")

            if [[ "$health_status" == "healthy" ]]; then
                log_success "$service: healthy"
            elif [[ "$health_status" == "unhealthy" ]]; then
                log_error "$service: unhealthy"
                unhealthy_services+=("$service")
            else
                log_info "$service: running (no health check)"
            fi
        else
            log_warning "$service: not running"
            unhealthy_services+=("$service")
        fi
    done

    if [[ ${#unhealthy_services[@]} -gt 0 ]]; then
        log_error "Unhealthy services: ${unhealthy_services[*]}"
        return 1
    else
        log_success "All services are healthy"
        return 0
    fi
}

# Main execution
main() {
    # Parse arguments
    parse_args "$@"

    # Set default command
    COMMAND="${COMMAND:-deploy}"

    # Validate
    validate_environment

    # Load configuration
    load_config

    # Change to project directory
    cd "$PROJECT_ROOT"

    # Execute command
    case $COMMAND in
        deploy)
            prepare_docker
            build_images
            if [[ "$ENVIRONMENT" == "prod" ]]; then
                backup_data
            fi
            deploy_services
            run_migrations
            health_check
            show_status
            ;;
        start)
            prepare_docker
            deploy_services
            wait_for_health
            ;;
        stop)
            log_info "Stopping services..."
            docker-compose down
            ;;
        restart)
            log_info "Restarting services..."
            docker-compose restart
            wait_for_health
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "${1:-}"
            ;;
        backup)
            backup_data
            ;;
        restore)
            log_error "Restore command not implemented yet"
            exit 1
            ;;
        cleanup)
            cleanup_resources
            ;;
        health)
            health_check
            ;;
        *)
            log_error "Unknown command: $COMMAND"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
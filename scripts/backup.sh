#!/bin/bash

# CBSC Strategy Management System Backup Script
# CBSC 策略管理系統備份腳本

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEPLOY_DIR="/opt/cbsc"
BACKUP_DIR="/opt/cbsc/backups"
LOG_FILE="/var/log/cbsc-backup.log"
COMPOSE_FILE="docker-compose.prod.yml"
RETENTION_DAYS=30

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}✓ $1${NC}" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}⚠ $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}✗ $1${NC}" | tee -a "$LOG_FILE"
}

check_requirements() {
    log "Checking backup requirements..."

    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root"
        exit 1
    fi

    # Check if deployment directory exists
    if [[ ! -d "$DEPLOY_DIR" ]]; then
        error "Deployment directory $DEPLOY_DIR not found"
        exit 1
    fi

    # Check if docker-compose file exists
    if [[ ! -f "$DEPLOY_DIR/$COMPOSE_FILE" ]]; then
        error "Docker compose file $DEPLOY_DIR/$COMPOSE_FILE not found"
        exit 1
    fi

    success "Backup requirements satisfied"
}

create_backup_directory() {
    local backup_name="backup-$(date +%Y%m%d-%H%M%S)"
    local backup_path="$BACKUP_DIR/$backup_name"

    mkdir -p "$backup_path"
    echo "$backup_path"
}

backup_postgres() {
    local backup_path="$1"
    log "Backing up PostgreSQL database..."

    cd "$DEPLOY_DIR"

    # Load environment variables
    if [[ -f ".env" ]]; then
        source .env
    else
        error ".env file not found"
        return 1
    fi

    # Check if PostgreSQL is running
    if ! docker-compose -f "$COMPOSE_FILE" ps postgres | grep -q "Up"; then
        error "PostgreSQL is not running"
        return 1
    fi

    # Create database backup
    if docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > "$backup_path/postgres.sql"; then
        success "PostgreSQL backup completed"

        # Compress the backup
        gzip "$backup_path/postgres.sql"
        success "PostgreSQL backup compressed"
    else
        error "PostgreSQL backup failed"
        return 1
    fi
}

backup_redis() {
    local backup_path="$1"
    log "Backing up Redis data..."

    cd "$DEPLOY_DIR"

    # Check if Redis is running
    if ! docker-compose -f "$COMPOSE_FILE" ps redis | grep -q "Up"; then
        error "Redis is not running"
        return 1
    fi

    # Create Redis backup
    local redis_container=$(docker-compose -f "$COMPOSE_FILE" ps -q redis)
    if docker cp "$redis_container:/data" "$backup_path/redis"; then
        success "Redis backup completed"

        # Create compressed archive
        tar -czf "$backup_path/redis.tar.gz" -C "$backup_path" redis
        rm -rf "$backup_path/redis"
        success "Redis backup compressed"
    else
        error "Redis backup failed"
        return 1
    fi
}

backup_influxdb() {
    local backup_path="$1"
    log "Backing up InfluxDB data..."

    cd "$DEPLOY_DIR"

    # Load environment variables
    if [[ -f ".env" ]]; then
        source .env
    else
        error ".env file not found"
        return 1
    fi

    # Check if InfluxDB is running
    if ! docker-compose -f "$COMPOSE_FILE" ps influxdb | grep -q "Up"; then
        error "InfluxDB is not running"
        return 1
    fi

    # Create InfluxDB backup
    local influxdb_container=$(docker-compose -f "$COMPOSE_FILE" ps -q influxdb)

    # Create backup directory inside container
    docker exec "$influxdb_container" mkdir -p /tmp/backup

    # Run backup command
    if docker exec "$influxdb_container" influx backup -t "$INFLUXDB_TOKEN" -o "/tmp/backup" "/var/lib/influxdb2"; then
        # Copy backup from container
        docker cp "$influxdb_container:/tmp/backup" "$backup_path/influxdb"

        # Create compressed archive
        tar -czf "$backup_path/influxdb.tar.gz" -C "$backup_path" influxdb
        rm -rf "$backup_path/influxdb"
        success "InfluxDB backup completed and compressed"
    else
        error "InfluxDB backup failed"
        return 1
    fi
}

backup_application_data() {
    local backup_path="$1"
    log "Backing up application data..."

    cd "$DEPLOY_DIR"

    # Backup configuration files
    if [[ -f ".env" ]]; then
        cp .env "$backup_path/"
        success "Environment file backed up"
    fi

    # Backup SSL certificates
    if [[ -d "ssl" ]]; then
        cp -r ssl "$backup_path/"
        success "SSL certificates backed up"
    fi

    # Backup uploaded files
    if [[ -d "uploads" ]]; then
        cp -r uploads "$backup_path/"
        success "Upload files backed up"
    fi

    # Backup logs
    if [[ -d "logs" ]]; then
        mkdir -p "$backup_path/logs"
        # Only backup recent logs (last 7 days)
        find logs -name "*.log" -mtime -7 -exec cp {} "$backup_path/logs/" \;
        success "Recent logs backed up"
    fi
}

backup_docker_volumes() {
    local backup_path="$1"
    log "Backing up Docker volumes..."

    cd "$DEPLOY_DIR"

    # List of important volumes to backup
    local volumes=(
        "cbsc_postgres_data"
        "cbsc_redis_data"
        "cbsc_influxdb_data"
        "cbsc_prometheus_data"
        "cbsc_grafana_data"
    )

    for volume in "${volumes[@]}"; do
        if docker volume ls -q -f name="$volume" | grep -q .; then
            log "Backing up volume: $volume"

            # Create temporary container to access volume
            docker run --rm -v "$volume":/volume -v "$backup_path":/backup alpine tar -czf "/backup/volume-$volume.tar.gz" -C /volume .
            success "Volume $volume backed up"
        else
            warning "Volume $volume not found"
        fi
    done
}

verify_backup() {
    local backup_path="$1"
    log "Verifying backup integrity..."

    local files=(
        "postgres.sql.gz"
        "redis.tar.gz"
        "influxdb.tar.gz"
        ".env"
    )

    for file in "${files[@]}"; do
        if [[ -f "$backup_path/$file" ]]; then
            # Check if file is not empty and can be read
            if [[ -s "$backup_path/$file" ]] && [[ -r "$backup_path/$file" ]]; then
                success "Backup file $file is valid"
            else
                error "Backup file $file is invalid or empty"
                return 1
            fi
        else
            warning "Backup file $file not found"
        fi
    done

    success "Backup verification completed"
}

cleanup_old_backups() {
    log "Cleaning up old backups..."

    # Find and remove backups older than RETENTION_DAYS
    local old_backups=$(find "$BACKUP_DIR" -type d -name "backup-*" -mtime "+$RETENTION_DAYS")

    if [[ -n "$old_backups" ]]; then
        echo "$old_backups" | while read -r backup; do
            log "Removing old backup: $backup"
            rm -rf "$backup"
        done
        success "Old backups cleaned up"
    else
        success "No old backups to clean up"
    fi
}

calculate_backup_size() {
    local backup_path="$1"
    local backup_size=$(du -sh "$backup_path" | cut -f1)
    echo "$backup_size"
}

main() {
    log "Starting CBSC Strategy Management System backup..."

    check_requirements

    # Create backup directory
    local backup_path
    backup_path=$(create_backup_directory)
    log "Created backup directory: $backup_path"

    # Perform backups
    backup_postgres "$backup_path" || warning "PostgreSQL backup failed"
    backup_redis "$backup_path" || warning "Redis backup failed"
    backup_influxdb "$backup_path" || warning "InfluxDB backup failed"
    backup_application_data "$backup_path"
    backup_docker_volumes "$backup_path"

    # Verify backup
    if verify_backup "$backup_path"; then
        local backup_size=$(calculate_backup_size "$backup_path")
        success "Backup completed successfully!"
        success "Backup location: $backup_path"
        success "Backup size: $backup_size"

        # Cleanup old backups
        cleanup_old_backups
    else
        error "Backup verification failed"
        exit 1
    fi
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Backup CBSC Strategy Management System data"
        echo ""
        echo "Options:"
        echo "  --help, -h          Show this help message"
        echo "  --verify-only       Verify existing backups only"
        echo "  --cleanup-only      Cleanup old backups only"
        exit 0
        ;;
    --verify-only)
        log "Verifying existing backups..."
        if [[ -d "$BACKUP_DIR" ]]; then
            find "$BACKUP_DIR" -type d -name "backup-*" | while read -r backup; do
                echo "Verifying: $backup"
                verify_backup "$backup"
            done
        else
            warning "Backup directory $BACKUP_DIR not found"
        fi
        ;;
    --cleanup-only)
        cleanup_old_backups
        ;;
    "")
        main
        ;;
    *)
        error "Unknown option: $1"
        echo "Use --help for usage information"
        exit 1
        ;;
esac
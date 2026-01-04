#!/bin/bash

# CBSC Strategy Management System - Development Environment Startup Script
# CBSC 策略管理系統 - 開發環境啟動腳本

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}✓ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

error() {
    echo -e "${RED}✗ $1${NC}"
}

check_prerequisites() {
    log "檢查開發環境先決條件..."

    # Check if Docker is running
    if ! docker info &> /dev/null; then
        error "Docker 未運行或無法訪問"
        return 1
    fi

    # Check if Docker Compose is available
    if ! command -v docker-compose &> /dev/null; then
        error "docker-compose 未安裝"
        return 1
    fi

    # Check if .env.dev file exists
    if [[ ! -f ".env.dev" ]]; then
        warning ".env.dev 文件不存在，將使用默認配置"
    fi

    success "開發環境先決條件檢查完成"
}

start_services() {
    log "啟動CBSC開發環境..."

    # Load environment variables
    if [[ -f ".env.dev" ]]; then
        set -a
        source .env.dev
        set +a
    fi

    # Start services using Docker Compose
    docker-compose -f docker-compose.k8s-alternative.yml up -d

    success "服務啟動命令已執行"
}

wait_for_services() {
    log "等待服務啟動..."

    # Wait for PostgreSQL
    log "等待 PostgreSQL..."
    local postgres_ready=false
    for i in {1..30}; do
        if docker exec cbsc-postgres-dev pg_isready -U cbsc_admin -d cbsc_production &> /dev/null; then
            postgres_ready=true
            break
        fi
        sleep 2
    done

    if [[ "$postgres_ready" == true ]]; then
        success "PostgreSQL 已準備就緒"
    else
        error "PostgreSQL 啟動超時"
        return 1
    fi

    # Wait for Redis
    log "等待 Redis..."
    local redis_ready=false
    for i in {1..30}; do
        if docker exec cbsc-redis-dev redis-cli ping &> /dev/null; then
            redis_ready=true
            break
        fi
        sleep 2
    done

    if [[ "$redis_ready" == true ]]; then
        success "Redis 已準備就緒"
    else
        error "Redis 啟動超時"
        return 1
    fi

    # Wait for InfluxDB
    log "等待 InfluxDB..."
    local influxdb_ready=false
    for i in {1..45}; do
        if curl -f http://localhost:8086/health &> /dev/null; then
            influxdb_ready=true
            break
        fi
        sleep 3
    done

    if [[ "$influxdb_ready" == true ]]; then
        success "InfluxDB 已準備就緒"
    else
        warning "InfluxDB 啟動超時 (這可能不影響核心功能)"
    fi

    # Wait for Backend API
    log "等待 Backend API..."
    local backend_ready=false
    for i in {1..60}; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            backend_ready=true
            break
        fi
        sleep 3
    done

    if [[ "$backend_ready" == true ]]; then
        success "Backend API 已準備就緒"
    else
        error "Backend API 啟動超時"
        return 1
    fi

    # Wait for Frontend
    log "等待 Frontend..."
    local frontend_ready=false
    for i in {1..60}; do
        if curl -f http://localhost:3000 &> /dev/null; then
            frontend_ready=true
            break
        fi
        sleep 3
    done

    if [[ "$frontend_ready" == true ]]; then
        success "Frontend 已準備就緒"
    else
        warning "Frontend 啟動超時 (可能需要更長時間)"
    fi
}

show_service_status() {
    log "服務狀態:"
    echo ""

    echo "=== 核心服務 ==="
    docker-compose -f docker-compose.k8s-alternative.yml ps postgres redis influxdb backend frontend

    echo ""
    echo "=== 監控服務 ==="
    docker-compose -f docker-compose.k8s-alternative.yml ps prometheus grafana nginx

    echo ""
    echo "=== 導出器服務 ==="
    docker-compose -f docker-compose.k8s-alternative.yml ps redis-exporter postgres-exporter influxdb-exporter
}

show_access_urls() {
    log "服務訪問地址:"
    echo ""
    echo "🚀 核心應用:"
    echo "  Frontend (策略管理界面): http://localhost:3000"
    echo "  Backend API: http://localhost:8000"
    echo "  API 文檔: http://localhost:8000/docs"
    echo ""
    echo "📊 監控工具:"
    echo "  Prometheus: http://localhost:9090"
    echo "  Grafana: http://localhost:3001 (用戶名: admin, 密碼: ${GRAFANA_PASSWORD:-admin})"
    echo ""
    echo "🔧 數據庫:"
    echo "  PostgreSQL: localhost:5432"
    echo "  Redis: localhost:6379"
    echo "  InfluxDB: http://localhost:8086"
    echo ""
}

show_next_steps() {
    log "後續操作建議:"
    echo ""
    echo "1. 開發時使用:"
    echo "   - 查看日誌: docker-compose -f docker-compose.k8s-alternative.yml logs -f [service]"
    echo "   - 重啟服務: docker-compose -f docker-compose.k8s-alternative.yml restart [service]"
    echo "   - 進入容器: docker exec -it cbsc-backend-dev bash"
    echo ""
    echo "2. 數據庫操作:"
    echo "   - 連接 PostgreSQL: docker exec -it cbsc-postgres-dev psql -U cbsc_admin -d cbsc_production"
    echo "   - 連接 Redis: docker exec -it cbsc-redis-dev redis-cli"
    echo ""
    echo "3. 停止環境:"
    echo "   - 停止所有服務: docker-compose -f docker-compose.k8s-alternative.yml down"
    echo "   - 清除數據: docker-compose -f docker-compose.k8s-alternative.yml down -v"
    echo ""
}

main() {
    log "啟動 CBSC 策略管理系統開發環境..."
    echo ""

    # Execute startup steps
    check_prerequisites
    start_services
    wait_for_services
    show_service_status
    echo ""
    show_access_urls
    echo ""
    show_next_steps

    success "開發環境啟動完成！"
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "用法: $0 [選項]"
        echo ""
        echo "啟動CBSC策略管理系統的開發環境"
        echo ""
        echo "選項:"
        echo "  --help, -h          顯示此幫助信息"
        echo "  --check-only        僅檢查先決條件"
        echo "  --status-only       僅顯示服務狀態"
        echo "  --stop              停止所有服務"
        echo "  --restart           重啟所有服務"
        echo "  --logs              顯示所有服務日誌"
        exit 0
        ;;
    --check-only)
        check_prerequisites
        ;;
    --status-only)
        show_service_status
        show_access_urls
        ;;
    --stop)
        log "停止CBSC開發環境..."
        docker-compose -f docker-compose.k8s-alternative.yml down
        success "開發環境已停止"
        ;;
    --restart)
        log "重啟CBSC開發環境..."
        docker-compose -f docker-compose.k8s-alternative.yml restart
        success "開發環境已重啟"
        ;;
    --logs)
        docker-compose -f docker-compose.k8s-alternative.yml logs -f
        ;;
    "")
        main
        ;;
    *)
        error "未知選項: $1"
        echo "使用 --help 查看幫助信息"
        exit 1
        ;;
esac
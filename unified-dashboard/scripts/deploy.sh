#!/bin/bash

# CBSC Unified Dashboard Deployment Script
# 自動化部署腳本，支持開發、測試和生產環境

set -e  # Exit on any error

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日誌函數
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

# 檢查環境參數
ENVIRONMENT=${1:-development}
COMMIT_HASH=${2:-latest}

log_info "開始部署 CBSC Unified Dashboard"
log_info "環境: $ENVIRONMENT"
log_info "版本: $COMMIT_HASH"

# 檢查必要的工具
check_requirements() {
    log_info "檢查部署要求..."

    # 檢查 Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安裝"
        exit 1
    fi

    # 檢查 Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安裝"
        exit 1
    fi

    # 檢查 Node.js (本地開發)
    if [ "$ENVIRONMENT" = "development" ] && ! command -v node &> /dev/null; then
        log_error "Node.js 未安裝"
        exit 1
    fi

    log_success "所有要求已滿足"
}

# 設置環境變量
setup_environment() {
    log_info "設置環境變量..."

    case $ENVIRONMENT in
        "development")
            export NODE_ENV=development
            export API_BASE_URL=http://localhost:3003
            export REDIS_URL=redis://localhost:6379
            export DATABASE_URL=postgresql://postgres:password@localhost:5432/cbsc_dev
            ;;
        "staging")
            export NODE_ENV=staging
            export API_BASE_URL=https://api-staging.cbsc.com
            export REDIS_URL=redis://redis-staging.cbsc.com:6379
            export DATABASE_URL=postgresql://postgres:password@postgres-staging.cbsc.com:5432/cbsc_staging
            ;;
        "production")
            export NODE_ENV=production
            export API_BASE_URL=https://api.cbsc.com
            export REDIS_URL=redis://redis.cbsc.com:6379
            export DATABASE_URL=postgresql://postgres:password@postgres.cbsc.com:5432/cbsc
            ;;
        *)
            log_error "未知環境: $ENVIRONMENT"
            exit 1
            ;;
    esac

    log_success "環境變量設置完成"
}

# 構建應用
build_application() {
    log_info "構建應用..."

    if [ "$ENVIRONMENT" = "development" ]; then
        # 本地開發構建
        npm ci
        npm run build
    else
        # Docker 構建
        docker-compose build --build-arg ENVIRONMENT=$ENVIRONMENT
    fi

    log_success "應用構建完成"
}

# 運行測試
run_tests() {
    log_info "運行測試..."

    if [ "$ENVIRONMENT" != "production" ]; then
        npm test
        log_success "所有測試通過"
    else
        log_warning "生產環境跳過測試"
    fi
}

# 部署應用
deploy_application() {
    log_info "部署應用..."

    case $ENVIRONMENT in
        "development")
            # 本地開發部署
            npm run dev &
            ;;
        "staging"|"production")
            # Docker 部署
            docker-compose up -d

            # 等待服務啟動
            log_info "等待服務啟動..."
            sleep 30

            # 運行健康檢查
            health_check
            ;;
    esac

    log_success "應用部署完成"
}

# 健康檢查
health_check() {
    log_info "執行健康檢查..."

    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:3000/api/health &> /dev/null; then
            log_success "服務健康檢查通過"
            return 0
        fi

        log_warning "健康檢查失敗，重試 $attempt/$max_attempts..."
        sleep 10
        ((attempt++))
    done

    log_error "健康檢查失敗，部署終止"
    exit 1
}

# 清理資源
cleanup() {
    if [ "$ENVIRONMENT" != "development" ]; then
        log_info "清理未使用的 Docker 資源..."
        docker system prune -f
        log_success "清理完成"
    fi
}

# 回滾函數
rollback() {
    log_error "部署失敗，開始回滾..."

    if [ "$ENVIRONMENT" != "development" ]; then
        docker-compose down
        # 這裡可以添加回滾到上一個版本的邏輯
    fi

    log_info "回滾完成"
}

# 錯誤處理
trap 'rollback' ERR

# 主部署流程
main() {
    check_requirements
    setup_environment
    build_application
    run_tests
    deploy_application
    cleanup

    log_success "CBSC Unified Dashboard 部署成功！"

    if [ "$ENVIRONMENT" = "development" ]; then
        echo ""
        echo "開發服務已啟動："
        echo "Frontend: http://localhost:3016"
        echo "Backend:  http://localhost:3003"
        echo "API Docs: http://localhost:3003/docs"
    else
        echo ""
        echo "服務已部署："
        echo "Frontend: https://dashboard.cbsc.com"
        echo "Backend:  https://api.cbsc.com"
    fi
}

# 執行主函數
main "$@"
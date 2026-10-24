#!/bin/bash

# Configuration Service Production Deployment Script
# 配置服務生產環境部署腳本

set -e

echo "🚀 Deploying Configuration Service to Production..."
echo "🚀 正在部署配置服務到生產環境..."

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

# 檢查必要工具
check_prerequisites() {
    log_info "Checking prerequisites..."

    # 檢查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed."
        exit 1
    fi

    # 檢查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed."
        exit 1
    fi

    # 檢查kubectl（如果使用Kubernetes）
    if [ "$USE_KUBERNETES" = "true" ] && ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed but USE_KUBERNETES is enabled."
        exit 1
    fi

    log_success "Prerequisites check passed."
}

# 備份當前配置
backup_current_config() {
    log_info "Backing up current configuration..."

    BACKUP_DIR="backups/pre-deployment-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$BACKUP_DIR"

    # 備份數據庫
    if docker-compose ps postgres | grep -q "Up"; then
        log_info "Backing up database..."
        docker exec config_postgres pg_dump -U postgres config_service > "$BACKUP_DIR/database.sql"
        log_success "Database backed up."
    else
        log_warning "Database is not running. Skipping database backup."
    fi

    # 備份配置文件
    if [ -f ".env" ]; then
        cp .env "$BACKUP_DIR/"
        log_success "Environment file backed up."
    fi

    # 備份當前配置
    if [ -d "config" ]; then
        cp -r config "$BACKUP_DIR/"
        log_success "Configuration directory backed up."
    fi

    log_success "Configuration backed up to: $BACKUP_DIR"
}

# 構建生產鏡像
build_production_image() {
    log_info "Building production Docker image..."

    # 構建鏡像
    docker build -t config-service:latest .
    docker build -t config-service:$(date +%Y%m%d-%H%M%S) .

    log_success "Production image built successfully."
}

# 運行生產測試
run_production_tests() {
    log_info "Running production tests..."

    # 檢查鏡像是否正常運行
    if ! docker run --rm config-service:latest python -c "import main; print('Application starts successfully')"; then
        log_error "Production image failed to start."
        exit 1
    fi

    # 運行健康檢查
    log_info "Running health checks..."
    docker run --rm --name config-test -d -p 8006:8005 config-service:latest

    # 等待服務啟動
    sleep 10

    # 執行健康檢查
    if curl -f http://localhost:8006/health > /dev/null 2>&1; then
        log_success "Health check passed."
    else
        log_error "Health check failed."
        docker stop config-test
        exit 1
    fi

    # 清理測試容器
    docker stop config-test
    docker rm config-test

    log_success "Production tests passed."
}

# 部署到Docker Compose
deploy_docker_compose() {
    log_info "Deploying with Docker Compose..."

    # 設置生產環境變量
    export ENVIRONMENT=production
    export LOG_LEVEL=INFO
    export DEBUG=false

    # 停止當前服務
    log_info "Stopping current services..."
    docker-compose down

    # 拉取最新鏡像
    log_info "Pulling latest images..."
    docker-compose pull

    # 啟動服務
    log_info "Starting services..."
    docker-compose up -d

    # 等待服務啟動
    log_info "Waiting for services to be ready..."
    sleep 30

    # 驗證部署
    log_info "Verifying deployment..."
    if curl -f http://localhost:8005/health > /dev/null 2>&1; then
        log_success "Docker Compose deployment successful."
    else
        log_error "Docker Compose deployment failed."
        docker-compose logs config_service
        exit 1
    fi
}

# 部署到Kubernetes
deploy_kubernetes() {
    log_info "Deploying to Kubernetes..."

    # 檢查kubectl上下文
    if ! kubectl config current-context > /dev/null 2>&1; then
        log_error "No Kubernetes context configured."
        exit 1
    fi

    # 創建namespace（如果不存在）
    kubectl create namespace config-service --dry-run=client -o yaml | kubectl apply -f -

    # 應用配置映射
    if [ -f "k8s/configmap.yaml" ]; then
        kubectl apply -f k8s/configmap.yaml
    fi

    # 應用密鑰
    if [ -f "k8s/secret.yaml" ]; then
        kubectl apply -f k8s/secret.yaml
    fi

    # 應用部署
    if [ -f "k8s/deployment.yaml" ]; then
        kubectl apply -f k8s/deployment.yaml
    fi

    # 應用服務
    if [ -f "k8s/service.yaml" ]; then
        kubectl apply -f k8s/service.yaml
    fi

    # 應用入口
    if [ -f "k8s/ingress.yaml" ]; then
        kubectl apply -f k8s/ingress.yaml
    fi

    # 等待部署完成
    log_info "Waiting for deployment to complete..."
    kubectl rollout status deployment/config-service -n config-service --timeout=300s

    # 驗證部署
    log_info "Verifying Kubernetes deployment..."
    if kubectl get pods -n config-service -l app=config-service | grep -q "Running"; then
        log_success "Kubernetes deployment successful."
    else
        log_error "Kubernetes deployment failed."
        kubectl logs -n config-service -l app=config-service
        exit 1
    fi
}

# 配置監控
setup_monitoring() {
    log_info "Setting up monitoring..."

    # 檢查Prometheus配置
    if [ -f "prometheus.yml" ]; then
        log_info "Prometheus configuration found."
    else
        log_warning "Prometheus configuration not found."
    fi

    # 檢查Grafana配置
    if [ -f "monitoring/grafana/dashboards" ]; then
        log_info "Grafana dashboards found."
    else
        log_warning "Grafana dashboards not found."
    fi

    log_success "Monitoring setup completed."
}

# 配置日誌輪轉
setup_log_rotation() {
    log_info "Setting up log rotation..."

    # 創建logrotate配置
    cat > /etc/logrotate.d/config-service << EOF
/path/to/config-service/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        docker-compose restart config-service
    endscript
}
EOF

    log_success "Log rotation configured."
}

# 運行部署後測試
run_post_deployment_tests() {
    log_info "Running post-deployment tests..."

    # 基本連接測試
    if curl -f http://localhost:8005/health > /dev/null 2>&1; then
        log_success "Health endpoint is accessible."
    else
        log_error "Health endpoint is not accessible."
        exit 1
    fi

    # API功能測試
    if curl -f http://localhost:8005/metrics > /dev/null 2>&1; then
        log_success "Metrics endpoint is accessible."
    else
        log_warning "Metrics endpoint is not accessible."
    fi

    # 配置CRUD測試
    log_info "Testing configuration CRUD operations..."

    # 創建測試配置
    TEST_CONFIG=$(curl -s -X POST http://localhost:8005/config \
        -H "Content-Type: application/json" \
        -d '{
            "key": "deployment.test.config",
            "value": "test_value",
            "service": "global",
            "environment": "production"
        }')

    if echo "$TEST_CONFIG" | grep -q "Configuration set successfully"; then
        log_success "Configuration creation test passed."
    else
        log_error "Configuration creation test failed."
        exit 1
    fi

    # 獲取測試配置
    GET_TEST=$(curl -s http://localhost:8005/config/deployment.test.config?service=global&environment=production)

    if echo "$GET_TEST" | grep -q "test_value"; then
        log_success "Configuration retrieval test passed."
    else
        log_error "Configuration retrieval test failed."
        exit 1
    fi

    # 刪除測試配置
    DELETE_TEST=$(curl -s -X DELETE http://localhost:8005/config/deployment.test.config?service=global&environment=production)

    if echo "$DELETE_TEST" | grep -q "deleted successfully"; then
        log_success "Configuration deletion test passed."
    else
        log_error "Configuration deletion test failed."
        exit 1
    fi

    log_success "Post-deployment tests passed."
}

# 生成部署報告
generate_deployment_report() {
    log_info "Generating deployment report..."

    REPORT_FILE="deployment-report-$(date +%Y%m%d-%H%M%S).md"

    cat > "$REPORT_FILE" << EOF
# Configuration Service Deployment Report

## Deployment Information
- **Deployment Date**: $(date)
- **Environment**: Production
- **Version**: $(git describe --tags --always 2>/dev/null || echo "unknown")
- **Deployer**: $(whoami)

## Services Status
\`\`\`
$(docker-compose ps)
\`\`\`

## Service Health Check
\`\`\`
$(curl -s http://localhost:8005/health | python3 -m json.tool 2>/dev/null || echo "Health check failed")
\`\`\`

## Configuration Statistics
\`\`\`
$(curl -s http://localhost:8005/metrics | python3 -m json.tool 2>/dev/null || echo "Metrics unavailable")
\`\`\`

## Container Logs (Last 50 lines)
\`\`\`
$(docker-compose logs --tail=50 config_service)
\`\`\`

## System Resources
\`\`\`
$(docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}")
\`\`\`

## Backup Information
- **Backup Directory**: $BACKUP_DIR
- **Database Backup**: $([ -f "$BACKUP_DIR/database.sql" ] && echo "✅ Success" || echo "❌ Failed")
- **Config Backup**: $([ -f "$BACKUP_DIR/.env" ] && echo "✅ Success" || echo "❌ Failed")

## Next Steps
1. Monitor service logs: \`docker-compose logs -f config_service\`
2. Check metrics: Visit http://localhost:8005/metrics
3. Verify configuration access: Visit http://localhost:8005/docs
4. Set up monitoring alerts if needed

## Rollback Instructions
If deployment fails, rollback with:
\`\`\`bash
# Stop current services
docker-compose down

# Restore from backup
# (Instructions depend on backup method)

# Restart with previous version
docker-compose up -d
\`\`\`

EOF

    log_success "Deployment report generated: $REPORT_FILE"
}

# 主函數
main() {
    # 解析命令行參數
    SKIP_TESTS=false
    USE_KUBERNETES=false
    SKIP_BACKUP=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --use-kubernetes)
                USE_KUBERNETES=true
                shift
                ;;
            --skip-backup)
                SKIP_BACKUP=true
                shift
                ;;
            --help)
                echo "Usage: $0 [options]"
                echo "Options:"
                echo "  --skip-tests      Skip running tests"
                echo "  --use-kubernetes  Deploy to Kubernetes instead of Docker Compose"
                echo "  --skip-backup     Skip backup creation"
                echo "  --help            Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    # 確認部署
    echo "🚨 WARNING: This will deploy to PRODUCTION environment!"
    echo "🚨 警告：這將部署到生產環境！"
    echo ""
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Deployment cancelled."
        exit 0
    fi

    # 執行部署步驟
    check_prerequisites

    if [ "$SKIP_BACKUP" = false ]; then
        backup_current_config
    fi

    build_production_image

    if [ "$SKIP_TESTS" = false ]; then
        run_production_tests
    fi

    if [ "$USE_KUBERNETES" = true ]; then
        deploy_kubernetes
    else
        deploy_docker_compose
    fi

    setup_monitoring
    setup_log_rotation

    if [ "$SKIP_TESTS" = false ]; then
        run_post_deployment_tests
    fi

    generate_deployment_report

    echo ""
    log_success "🎉 Production deployment completed successfully!"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Monitor service logs: docker-compose logs -f config_service"
    echo "   2. Check service health: curl http://localhost:8005/health"
    echo "   3. Review deployment report: $(ls -1 deployment-report-*.md | tail -1)"
    echo "   4. Set up monitoring alerts"
    echo ""
    echo "🔧 Service URLs:"
    echo "   - API Documentation: http://localhost:8005/docs"
    echo "   - Metrics: http://localhost:8005/metrics"
    echo "   - Health Check: http://localhost:8005/health"
    echo ""
}

# 運行主函數
main "$@"
#!/bin/bash
# 0700.HK 參數優化系統部署腳本

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置變量
PROJECT_NAME="optimization-system"
DOCKER_COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"
LOG_FILE="deploy.log"

# 函數：打印彩色消息
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}[$(date +'%Y-%m-%d %H:%M:%S')] ${message}${NC}"
}

print_success() {
    print_message $GREEN "✅ $1"
}

print_error() {
    print_message $RED "❌ $1"
}

print_warning() {
    print_message $YELLOW "⚠️ $1"
}

print_info() {
    print_message $BLUE "ℹ️ $1"
}

# 函數：檢查系統要求
check_requirements() {
    print_info "檢查系統要求..."

    # 檢查 Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安裝，請先安裝 Docker"
        exit 1
    fi
    print_success "Docker 已安裝"

    # 檢查 Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose 未安裝，請先安裝 Docker Compose"
        exit 1
    fi
    print_success "Docker Compose 已安裝"

    # 檢查 GPU 支持（可選）
    if command -v nvidia-smi &> /dev/null; then
        print_success "NVIDIA GPU 驅動已安裝"
        nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits
    else
        print_warning "NVIDIA GPU 驅動未檢測到，將使用 CPU 模式"
    fi

    # 檢查磁盤空間
    available_space=$(df . | tail -1 | awk '{print $4}')
    required_space=5242880  # 5GB in KB
    if [ $available_space -lt $required_space ]; then
        print_error "磁盤空間不足，需要至少 5GB 可用空間"
        exit 1
    fi
    print_success "磁盤空間檢查通過"
}

# 函數：創建環境配置文件
create_env_file() {
    if [ ! -f "$ENV_FILE" ]; then
        print_info "創建環境配置文件..."

        cat > "$ENV_FILE" << EOF
# 數據庫配置
DATABASE_URL=postgresql://postgres:password@postgres:5432/optimization_db
DB_HOST=postgres
DB_PORT=5432
DB_NAME=optimization_db
DB_USER=postgres
DB_PASSWORD=password

# Redis 配置
REDIS_URL=redis://redis:6379/0
REDIS_HOST=redis
REDIS_PORT=6379

# 安全配置
SECRET_KEY=$(openssl rand -hex 32)
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# GPU 配置
CUDA_VISIBLE_DEVICES=0,1,2,3
GPU_MEMORY_LIMIT=8192
GPU_ENABLED=true

# API 配置
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# 日誌配置
LOG_LEVEL=INFO
LOG_FILE=/app/logs/api.log

# 監控配置
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
METRICS_ENABLED=true

# 限流配置
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REDIS_URL=redis://redis:6379/1

# CORS 配置
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:8080","https://yourdomain.com"]

# 生產環境配置
ENVIRONMENT=production
DEBUG=false
EOF

        print_success "環境配置文件已創建: $ENV_FILE"
        print_warning "請檢查並修改配置文件中的密碼和敏感信息"
    else
        print_info "環境配置文件已存在: $ENV_FILE"
    fi
}

# 函數：創建必要目錄
create_directories() {
    print_info "創建必要目錄..."

    directories=(
        "logs"
        "data"
        "temp"
        "monitoring"
        "nginx"
        "database"
        "backup"
    )

    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_success "創建目錄: $dir"
        fi
    done
}

# 函數：構建 Docker 鏡像
build_images() {
    print_info "構建 Docker 鏡像..."

    if docker-compose build; then
        print_success "Docker 鏡像構建成功"
    else
        print_error "Docker 鏡像構建失敗"
        exit 1
    fi
}

# 函數：啟動服務
start_services() {
    print_info "啟動服務..."

    # 先啟動基礎服務
    print_info "啟動基礎服務 (PostgreSQL, Redis)..."
    docker-compose up -d postgres redis

    # 等待基礎服務就緒
    print_info "等待基礎服務就緒..."
    sleep 10

    # 啟動應用服務
    print_info "啟動應用服務..."
    docker-compose up -d

    # 檢查服務狀態
    print_info "檢查服務狀態..."
    sleep 5

    if docker-compose ps | grep -q "Up"; then
        print_success "服務啟動成功"
    else
        print_error "服務啟動失敗"
        docker-compose logs
        exit 1
    fi
}

# 函數：初始化數據庫
init_database() {
    print_info "初始化數據庫..."

    # 等待數據庫就緒
    print_info "等待數據庫就緒..."
    for i in {1..30}; do
        if docker-compose exec postgres pg_isready -U postgres; then
            print_success "數據庫就緒"
            break
        fi
        sleep 1
    done

    # 運行數據庫遷移
    print_info "運行數據庫遷移..."
    if docker-compose exec api python -m alembic upgrade head; then
        print_success "數據庫遷移完成"
    else
        print_warning "數據庫遷移失敗，請手動執行"
    fi
}

# 函數：健康檢查
health_check() {
    print_info "執行健康檢查..."

    # 檢查 API 服務
    for i in {1..30}; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            print_success "API 服務健康檢查通過"
            break
        fi
        if [ $i -eq 30 ]; then
            print_error "API 服務健康檢查失敗"
            docker-compose logs api
            exit 1
        fi
        sleep 2
    done

    # 檢查其他服務
    services=("postgres:5432" "redis:6379" "prometheus:9090" "grafana:3000")
    for service in "${services[@]}"; do
        service_name=$(echo $service | cut -d: -f1)
        port=$(echo $service | cut -d: -f2)

        if curl -f "http://localhost:$port" &> /dev/null || \
           nc -z localhost $port &> /dev/null; then
            print_success "$service_name 服務運行正常"
        else
            print_warning "$service_name 服務可能未就緒"
        fi
    done
}

# 函數：顯示部署信息
show_deployment_info() {
    print_success "🎉 部署完成！"
    echo
    print_info "服務訪問地址："
    echo "  • API 服務:     http://localhost:8000"
    echo "  • API 文檔:     http://localhost:8000/api/docs"
    echo "  • Grafana:      http://localhost:3000 (admin/admin)"
    echo "  • Prometheus:   http://localhost:9090"
    echo "  • pgAdmin:      http://localhost:5050 (admin@example.com/admin)"
    echo "  • Redis GUI:    http://localhost:8081"
    echo
    print_info "管理命令："
    echo "  • 查看日誌:     docker-compose logs -f [service_name]"
    echo "  • 重啟服務:     docker-compose restart [service_name]"
    echo "  • 停止服務:     docker-compose down"
    echo "  • 更新服務:     docker-compose pull && docker-compose up -d"
    echo
    print_info "監控命令："
    echo "  • 系統資源:     docker stats"
    echo "  • 服務狀態:     docker-compose ps"
    echo "  • 健康檢查:     curl http://localhost:8000/health"
    echo "  • 指標數據:     curl http://localhost:8000/metrics"
}

# 函數：清理函數
cleanup() {
    if [ $? -ne 0 ]; then
        print_error "部署失敗，正在清理..."
        docker-compose down
    fi
}

# 主函數
main() {
    print_info "開始部署 $PROJECT_NAME..."
    print_info "部署日誌將保存到: $LOG_FILE"

    # 設置清理陷阱
    trap cleanup EXIT

    # 執行部署步驟
    check_requirements 2>&1 | tee -a "$LOG_FILE"
    create_env_file 2>&1 | tee -a "$LOG_FILE"
    create_directories 2>&1 | tee -a "$LOG_FILE"
    build_images 2>&1 | tee -a "$LOG_FILE"
    start_services 2>&1 | tee -a "$LOG_FILE"
    init_database 2>&1 | tee -a "$LOG_FILE"
    health_check 2>&1 | tee -a "$LOG_FILE"
    show_deployment_info 2>&1 | tee -a "$LOG_FILE"

    # 移除清理陷阱
    trap - EXIT

    print_success "部署成功完成！"
}

# 處理命令行參數
case "${1:-}" in
    "build")
        check_requirements
        create_directories
        build_images
        ;;
    "start")
        start_services
        health_check
        ;;
    "stop")
        print_info "停止所有服務..."
        docker-compose down
        print_success "服務已停止"
        ;;
    "restart")
        print_info "重啟所有服務..."
        docker-compose restart
        health_check
        ;;
    "logs")
        docker-compose logs -f "${2:-api}"
        ;;
    "status")
        docker-compose ps
        ;;
    "clean")
        print_warning "這將刪除所有容器、鏡像和數據卷！"
        read -p "確認嗎？(y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker-compose down -v --rmi all
            docker system prune -f
            print_success "清理完成"
        fi
        ;;
    "help"|"-h"|"--help")
        echo "用法: $0 [命令]"
        echo
        echo "命令:"
        echo "  build    - 構建 Docker 鏡像"
        echo "  start    - 啟動服務"
        echo "  stop     - 停止服務"
        echo "  restart  - 重啟服務"
        echo "  logs     - 查看日誌 [service_name]"
        echo "  status   - 查看服務狀態"
        echo "  clean    - 清理所有容器和鏡像"
        echo "  help     - 顯示此幫助信息"
        echo
        echo "不帶參數執行將執行完整部署流程"
        ;;
    "")
        main
        ;;
    *)
        print_error "未知命令: $1"
        echo "使用 '$0 help' 查看可用命令"
        exit 1
        ;;
esac
#!/bin/bash

# CBSC System Development Environment Startup Script
# Author: CBSC Development Team
# Description: Start all development services with proper ordering and health checks

set -e  # Exit on error

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
LOG_DIR="./logs"
TIMEOUT=300  # 5 minutes

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

# Function to check if Docker is running
check_docker() {
    print_status "检查Docker状态..."
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker未运行，请先启动Docker"
        exit 1
    fi
    print_success "Docker运行正常"
}

# Function to check if Docker Compose is available
check_docker_compose() {
    print_status "检查Docker Compose..."
    if ! command -v docker-compose > /dev/null 2>&1; then
        print_error "Docker Compose未安装"
        exit 1
    fi
    print_success "Docker Compose可用"
}

# Function to create necessary directories
create_directories() {
    print_status "创建必要的目录..."
    mkdir -p $LOG_DIR
    mkdir -p ./data/postgres
    mkdir -p ./data/redis
    mkdir -p ./data/uploads
    mkdir -p ./gateway/logs
    mkdir -p ./nginx/logs
    print_success "目录创建完成"
}

# Function to check environment variables
check_env_vars() {
    print_status "检查环境变量..."

    # Create .env file if it doesn't exist
    if [ ! -f .env ]; then
        print_warning ".env文件不存在，创建默认配置..."
        cat > .env << EOF
# CBSC Development Environment Variables
# 数据库配置
POSTGRES_PASSWORD=cbsc_dev_password
POSTGRES_DB=cbsc_dev
POSTGRES_USER=cbsc_dev

# Redis配置
REDIS_PASSWORD=redis_dev_password

# 网关配置
GATEWAY_SECRET_KEY=dev_secret_key_change_in_production
JWT_SECRET=dev_jwt_secret_change_in_production

# 应用配置
LOG_LEVEL=DEBUG
ENVIRONMENT=development

# CORS配置
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# 监控配置
GRAFANA_PASSWORD=admin123

# 端口配置
FRONTEND_PORT=3000
UNIFIED_DASHBOARD_PORT=3001
API_GATEWAY_PORT=8000
EOF
        print_success ".env文件已创建"
    fi

    print_success "环境变量检查完成"
}

# Function to stop existing services
stop_existing_services() {
    print_status "停止现有服务..."
    docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME down --remove-orphans 2>/dev/null || true
    print_success "现有服务已停止"
}

# Function to start core services
start_core_services() {
    print_header "启动核心服务 (PostgreSQL, Redis)..."
    docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME up -d postgres redis

    print_status "等待数据库服务启动..."
    sleep 10

    # Wait for PostgreSQL to be ready
    print_status "等待PostgreSQL就绪..."
    for i in {1..30}; do
        if docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME exec -T postgres pg_isready -U cbsc_dev -d cbsc_dev > /dev/null 2>&1; then
            print_success "PostgreSQL已就绪"
            break
        fi
        if [ $i -eq 30 ]; then
            print_error "PostgreSQL启动超时"
            exit 1
        fi
        sleep 2
    done

    # Wait for Redis to be ready
    print_status "等待Redis就绪..."
    for i in {1..15}; do
        if docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME exec -T redis redis-cli ping > /dev/null 2>&1; then
            print_success "Redis已就绪"
            break
        fi
        if [ $i -eq 15 ]; then
            print_error "Redis启动超时"
            exit 1
        fi
        sleep 2
    done

    print_success "核心服务启动完成"
}

# Function to start application services
start_application_services() {
    print_header "启动应用服务 (API Gateway, Frontend)..."
    docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME up -d api-gateway frontend unified-dashboard

    print_status "等待API网关启动..."
    sleep 15

    # Check API Gateway health
    for i in {1..30}; do
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            print_success "API网关已就绪"
            break
        fi
        if [ $i -eq 30 ]; then
            print_warning "API网关启动超时，请检查日志"
            break
        fi
        sleep 2
    done

    # Wait for frontend services
    sleep 10
    print_success "应用服务启动完成"
}

# Function to start optional services
start_optional_services() {
    print_header "启动可选开发工具..."
    docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME --profile tools up -d

    sleep 5
    print_success "开发工具启动完成"
}

# Function to start backend services (optional)
start_backend_services() {
    if [ "$1" = "--with-backend" ]; then
        print_header "启动后端服务..."
        docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME --profile backend up -d

        sleep 20
        print_success "后端服务启动完成"
    fi
}

# Function to display service status
show_service_status() {
    print_header "服务状态"
    docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME ps

    echo ""
    print_header "服务访问地址"
    echo -e "${CYAN}API Gateway:${NC}     http://localhost:8000"
    echo -e "${CYAN}API 文档:${NC}        http://localhost:8000/docs"
    echo -e "${CYAN}前端应用:${NC}        http://localhost:3000"
    echo -e "${CYAN}统一Dashboard:${NC}  http://localhost:3001"
    echo -e "${CYAN}Grafana监控:${NC}     http://localhost:8080"
    echo ""

    if docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME ps --services --filter "profile=tools" | grep -q .; then
        echo -e "${CYAN}PgAdmin:${NC}         http://localhost:5050"
        echo -e "${CYAN}Redis Commander:${NC} http://localhost:8081"
        echo ""
    fi

    echo -e "${CYAN}数据库连接:${NC}"
    echo -e "  PostgreSQL: localhost:5432"
    echo -e "  Redis:      localhost:6379"
    echo ""
}

# Function to run health check
run_health_check() {
    print_header "运行健康检查..."

    # Check API Gateway
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_success "✅ API Gateway健康"
    else
        print_error "❌ API Gateway不健康"
    fi

    # Check Frontend
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        print_success "✅ 前端应用健康"
    else
        print_warning "⚠️ 前端应用可能还在启动中"
    fi

    # Check Database
    if docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME exec -T postgres pg_isready -U cbsc_dev -d cbsc_dev > /dev/null 2>&1; then
        print_success "✅ PostgreSQL健康"
    else
        print_error "❌ PostgreSQL不健康"
    fi

    # Check Redis
    if docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME exec -T redis redis-cli ping > /dev/null 2>&1; then
        print_success "✅ Redis健康"
    else
        print_error "❌ Redis不健康"
    fi
}

# Function to show usage
show_usage() {
    echo -e "${BLUE}CBSC开发环境启动脚本${NC}"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --with-backend    同时启动后端服务"
    echo "  --stop           停止所有服务"
    echo "  --restart        重启所有服务"
    echo "  --logs           查看服务日志"
    echo "  --status         显示服务状态"
    echo "  --help           显示帮助信息"
    echo ""
}

# Function to stop services
stop_services() {
    print_header "停止所有服务..."
    docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME down --remove-orphans
    print_success "所有服务已停止"
}

# Function to restart services
restart_services() {
    stop_services
    sleep 5
    start_development_environment
}

# Function to show logs
show_logs() {
    print_header "显示服务日志..."
    docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME logs -f --tail=100
}

# Function to show status
show_status() {
    show_service_status
    run_health_check
}

# Main startup function
start_development_environment() {
    print_header "🚀 启动CBSC开发环境"
    echo ""

    check_docker
    check_docker_compose
    create_directories
    check_env_vars
    stop_existing_services
    start_core_services
    start_application_services
    start_optional_services
    start_backend_services $1
    show_service_status
    run_health_check

    print_header "🎉 开发环境启动完成！"
    echo ""
    print_status "使用 './scripts/dev-start.sh --logs' 查看实时日志"
    print_status "使用 './scripts/dev-start.sh --stop' 停止所有服务"
    echo ""
}

# Parse command line arguments
case "${1:-}" in
    --with-backend)
        start_development_environment --with-backend
        ;;
    --stop)
        stop_services
        ;;
    --restart)
        restart_services
        ;;
    --logs)
        show_logs
        ;;
    --status)
        show_status
        ;;
    --help|-h)
        show_usage
        ;;
    "")
        start_development_environment
        ;;
    *)
        print_error "未知选项: $1"
        show_usage
        exit 1
        ;;
esac
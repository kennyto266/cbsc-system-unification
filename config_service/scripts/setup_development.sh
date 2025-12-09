#!/bin/bash

# Configuration Service Development Setup Script
# 配置服務開發環境設置腳本

set -e

echo "🚀 Setting up Configuration Service Development Environment..."
echo "🚀 正在設置配置服務開發環境..."

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

# 檢查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 is not installed. Please install $1 first."
        return 1
    fi
    return 0
}

# 創建必要的目錄
create_directories() {
    log_info "Creating necessary directories..."

    mkdir -p logs
    mkdir -p backups
    mkdir -p data/postgres
    mkdir -p data/redis
    mkdir -p monitoring/prometheus
    mkdir -p monitoring/grafana
    mkdir -p monitoring/alertmanager

    log_success "Directories created successfully."
}

# 設置Python環境
setup_python() {
    log_info "Setting up Python environment..."

    # 檢查Python版本
    if ! check_command python3; then
        log_error "Python 3.9+ is required."
        exit 1
    fi

    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    required_version="3.9"

    if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
        log_error "Python $required_version or higher is required. Current version: $python_version"
        exit 1
    fi

    log_success "Python $python_version detected."

    # 創建虛擬環境
    if [ ! -d "venv" ]; then
        log_info "Creating Python virtual environment..."
        python3 -m venv venv
        log_success "Virtual environment created."
    else
        log_info "Virtual environment already exists."
    fi

    # 激活虛擬環境並安裝依賴
    log_info "Activating virtual environment and installing dependencies..."
    source venv/bin/activate

    # 升級pip
    pip install --upgrade pip

    # 安裝依賴
    pip install -r requirements.txt

    # 安裝開發依賴
    if [ -f "requirements.txt" ] && grep -q "dev" requirements.txt; then
        pip install pytest pytest-asyncio pytest-cov black flake8 mypy pre-commit
    fi

    log_success "Python environment setup completed."
}

# 設置Docker環境
setup_docker() {
    log_info "Setting up Docker environment..."

    # 檢查Docker
    if ! check_command docker; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    # 檢查Docker Compose
    if ! check_command docker-compose; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi

    log_success "Docker and Docker Compose detected."

    # 拉取基礎鏡像
    log_info "Pulling base Docker images..."
    docker pull postgres:15
    docker pull redis:7-alpine
    docker pull nginx:alpine

    log_success "Docker setup completed."
}

# 設置環境變量
setup_environment() {
    log_info "Setting up environment variables..."

    # 複製環境變量模板
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_success "Environment file created from template."

            # 生成加密密鑰
            encryption_key=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
            sed -i "s/your-32-character-encryption-key-here/$encryption_key/g" .env

            # 生成JWT密鑰
            jwt_secret=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
            sed -i "s/your-jwt-secret-key-here/$jwt_secret/g" .env

            log_warning "Please review and update the .env file with your specific settings."
        else
            log_error ".env.example file not found."
            exit 1
        fi
    else
        log_info "Environment file already exists."
    fi

    log_success "Environment setup completed."
}

# 初始化數據庫
init_database() {
    log_info "Initializing database..."

    # 啟動數據庫服務
    log_info "Starting database services..."
    docker-compose up -d postgres redis

    # 等待數據庫啟動
    log_info "Waiting for database to be ready..."
    sleep 10

    # 檢查數據庫連接
    max_attempts=30
    attempt=1

    while [ $attempt -le $max_attempts ]; do
        if docker exec config_postgres pg_isready -U postgres > /dev/null 2>&1; then
            log_success "Database is ready."
            break
        fi

        if [ $attempt -eq $max_attempts ]; then
            log_error "Database connection failed after $max_attempts attempts."
            exit 1
        fi

        log_info "Waiting for database... (attempt $attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done

    # 初始化數據庫模式
    log_info "Initializing database schema..."
    if [ -f "init.sql" ]; then
        docker exec -i config_postgres psql -U postgres -d config_service < init.sql
        log_success "Database schema initialized."
    else
        log_warning "init.sql file not found. Database schema will be created by the application."
    fi

    log_success "Database initialization completed."
}

# 運行測試
run_tests() {
    log_info "Running tests..."

    source venv/bin/activate

    # 運行單元測試
    if [ -d "tests" ]; then
        python -m pytest tests/ -v --cov=. --cov-report=html --cov-report=term-missing
        log_success "Tests completed successfully."
    else
        log_warning "No tests directory found."
    fi
}

# 設置pre-commit鉤子
setup_pre_commit() {
    log_info "Setting up pre-commit hooks..."

    source venv/bin/activate

    if [ -f ".pre-commit-config.yaml" ]; then
        pre-commit install
        log_success "Pre-commit hooks installed."
    else
        log_warning ".pre-commit-config.yaml not found."
    fi
}

# 啟動開發服務器
start_dev_server() {
    log_info "Starting development server..."

    source venv/bin/activate
    python main.py
}

# 主函數
main() {
    echo "Configuration Service Development Setup"
    echo "======================================="
    echo ""

    # 檢查是否在正確的目錄
    if [ ! -f "main.py" ]; then
        log_error "Please run this script from the config_service directory."
        exit 1
    fi

    # 解析命令行參數
    SKIP_DOCKER=false
    SKIP_TESTS=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-docker)
                SKIP_DOCKER=true
                shift
                ;;
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --help)
                echo "Usage: $0 [options]"
                echo "Options:"
                echo "  --skip-docker    Skip Docker setup"
                echo "  --skip-tests     Skip running tests"
                echo "  --help           Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    # 執行設置步驟
    create_directories
    setup_python

    if [ "$SKIP_DOCKER" = false ]; then
        setup_docker
    fi

    setup_environment

    if [ "$SKIP_DOCKER" = false ]; then
        init_database
    fi

    if [ "$SKIP_TESTS" = false ]; then
        run_tests
    fi

    setup_pre_commit

    echo ""
    log_success "🎉 Development environment setup completed successfully!"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Review and update .env file"
    echo "   2. Start the development server: python main.py"
    echo "   3. Or use Docker Compose: docker-compose up"
    echo "   4. Visit the API documentation: http://localhost:8005/docs"
    echo ""
    echo "🔧 Useful commands:"
    echo "   - Start services: docker-compose up -d"
    echo "   - Stop services: docker-compose down"
    echo "   - View logs: docker-compose logs -f config_service"
    echo "   - Run tests: python -m pytest tests/"
    echo ""
}

# 運行主函數
main "$@"
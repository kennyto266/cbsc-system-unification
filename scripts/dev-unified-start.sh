#!/bin/bash

# CBSC Unified Development Environment Startup Script
# 统一开发环境启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 配置
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.cbsc-unified.yml"
ENV_FILE="$PROJECT_ROOT/.env"
LOG_FILE="$PROJECT_ROOT/logs/startup.log"

# 创建日志目录
mkdir -p "$(dirname "$LOG_FILE")"

# 日志函数
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1${NC}" | tee -a "$LOG_FILE"
}

# 检查依赖
check_dependencies() {
    log "检查系统依赖..."

    # 检查Docker
    if ! command -v docker &> /dev/null; then
        error "Docker未安装，请先安装Docker"
        exit 1
    fi

    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi

    # 检查Node.js（用于前端开发）
    if ! command -v node &> /dev/null; then
        warn "Node.js未安装，前端服务可能无法正常运行"
    fi

    # 检查Python（用于API服务）
    if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
        warn "Python未安装，API服务可能无法正常运行"
    fi

    log "依赖检查完成"
}

# 创建环境文件
create_env_file() {
    if [ ! -f "$ENV_FILE" ]; then
        log "创建环境配置文件..."
        cat > "$ENV_FILE" << EOF
# CBSC系统环境配置
COMPOSE_PROJECT_NAME=cbsc-unified

# 数据库配置
POSTGRES_PASSWORD=cbsc_secure_2024_${RANDOM}
POSTGRES_USER=cbsc_admin
POSTGRES_DB=cbsc_system

# Redis配置
REDIS_PASSWORD=

# JWT配置
JWT_SECRET=cbsc_jwt_secret_$(date +%s)_${RANDOM}
GATEWAY_SECRET_KEY=cbsc_gateway_secret_$(date +%s)_${RANDOM}

# OAuth2配置
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=

# CSRF配置
CSRF_SECRET=cbsc_csrf_secret_$(date +%s)_${RANDOM}

# 监控配置
GRAFANA_PASSWORD=admin123

# 日志配置
LOG_LEVEL=INFO
ENVIRONMENT=development

# 网络配置
NETWORK_SUBNET=172.20.0.0/16

# 端口配置
API_GATEWAY_PORT=8000
USER_MANAGEMENT_PORT=3004
STRATEGY_DASHBOARD_PORT=3003
CONFIG_SERVICE_PORT=3005
FRONTEND_PORT=3000
UNIFIED_DASHBOARD_PORT=3001
NGINX_PORT=80
NGINX_SSL_PORT=443

# 监控端口
GRAFANA_PORT=3002
PROMETHEUS_PORT=9090
JAEGER_PORT=16686
KIBANA_PORT=5601
EOF
        log "环境配置文件已创建: $ENV_FILE"
        warn "请根据需要修改环境配置文件"
    else
        log "环境配置文件已存在: $ENV_FILE"
    fi
}

# 清理旧容器
cleanup_containers() {
    log "清理旧容器..."
    cd "$PROJECT_ROOT"

    # 使用docker-compose或docker compose
    if command -v docker-compose &> /dev/null; then
        docker-compose -f "$COMPOSE_FILE" down --remove-orphans 2>/dev/null || true
    else
        docker compose -f "$COMPOSE_FILE" down --remove-orphans 2>/dev/null || true
    fi

    # 清理悬挂的网络
    docker network prune -f 2>/dev/null || true

    log "容器清理完成"
}

# 创建网络
create_network() {
    log "创建Docker网络..."

    if ! docker network inspect cbsc-network &>/dev/null; then
        docker network create cbsc-network --subnet=172.20.0.0/16 || {
            warn "网络创建失败，可能已存在"
        }
    fi

    log "Docker网络已就绪"
}

# 启动基础设施服务
start_infrastructure() {
    log "启动基础设施服务..."
    cd "$PROJECT_ROOT"

    # 使用docker-compose或docker compose
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        COMPOSE_CMD="docker compose"
    fi

    # 启动基础服务（Redis, PostgreSQL）
    $COMPOSE_CMD -f "$COMPOSE_FILE" up -d redis postgres

    log "等待数据库启动..."
    sleep 10

    # 等待数据库就绪
    for i in {1..30}; do
        if docker exec cbsc-postgres pg_isready -U cbsc_admin -d cbsc_system &>/dev/null; then
            log "数据库已就绪"
            break
        fi
        if [ $i -eq 30 ]; then
            error "数据库启动超时"
            exit 1
        fi
        sleep 2
    done

    # 等待Redis就绪
    for i in {1..15}; do
        if docker exec cbsc-redis redis-cli ping &>/dev/null; then
            log "Redis已就绪"
            break
        fi
        if [ $i -eq 15 ]; then
            error "Redis启动超时"
            exit 1
        fi
        sleep 1
    done

    log "基础设施服务启动完成"
}

# 启动核心服务
start_core_services() {
    log "启动核心服务..."
    cd "$PROJECT_ROOT"

    # 使用docker-compose或docker compose
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        COMPOSE_CMD="docker compose"
    fi

    # 启动API网关和核心服务
    $COMPOSE_CMD -f "$COMPOSE_FILE" up -d api-gateway user-management strategy-dashboard config-service

    log "等待核心服务启动..."
    sleep 15

    # 检查API网关
    for i in {1..30}; do
        if curl -f http://localhost:8000/health &>/dev/null; then
            log "API网关已就绪"
            break
        fi
        if [ $i -eq 30 ]; then
            warn "API网关启动检查超时，但继续执行"
            break
        fi
        sleep 2
    done

    log "核心服务启动完成"
}

# 启动前端服务
start_frontend_services() {
    log "启动前端服务..."
    cd "$PROJECT_ROOT"

    # 使用docker-compose或docker compose
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        COMPOSE_CMD="docker compose"
    fi

    # 启动前端服务
    $COMPOSE_CMD -f "$COMPOSE_FILE" up -d frontend-dashboard unified-dashboard nginx

    log "前端服务启动完成"
}

# 启动监控服务
start_monitoring_services() {
    log "启动监控服务..."
    cd "$PROJECT_ROOT"

    # 使用docker-compose或docker compose
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        COMPOSE_CMD="docker compose"
    fi

    # 启动监控服务
    $COMPOSE_CMD -f "$COMPOSE_FILE" up -d prometheus grafana jaeger elasticsearch logstash kibana

    log "监控服务启动完成"
}

# 检查服务状态
check_services() {
    log "检查服务状态..."
    cd "$PROJECT_ROOT"

    # 使用docker-compose或docker compose
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        COMPOSE_CMD="docker compose"
    fi

    # 显示容器状态
    echo -e "\n${CYAN}=== 容器状态 ===${NC}"
    $COMPOSE_CMD -f "$COMPOSE_FILE" ps

    # 检查关键服务健康状态
    echo -e "\n${CYAN}=== 服务健康检查 ===${NC}"

    # API网关
    if curl -f http://localhost:8000/health &>/dev/null; then
        echo -e "${GREEN}✅ API网关: http://localhost:8000${NC}"
    else
        echo -e "${RED}❌ API网关: 不可访问${NC}"
    fi

    # 前端Dashboard
    if curl -f http://localhost:3000 &>/dev/null; then
        echo -e "${GREEN}✅ 前端Dashboard: http://localhost:3000${NC}"
    else
        echo -e "${RED}❌ 前端Dashboard: 不可访问${NC}"
    fi

    # 统一Dashboard
    if curl -f http://localhost:3001 &>/dev/null; then
        echo -e "${GREEN}✅ 统一Dashboard: http://localhost:3001${NC}"
    else
        echo -e "${RED}❌ 统一Dashboard: 不可访问${NC}"
    fi

    # Grafana
    if curl -f http://localhost:3002/api/health &>/dev/null; then
        echo -e "${GREEN}✅ Grafana: http://localhost:3002 (admin/admin123)${NC}"
    else
        echo -e "${YELLOW}⚠️  Grafana: 启动中...${NC}"
    fi

    # Prometheus
    if curl -f http://localhost:9090/-/healthy &>/dev/null; then
        echo -e "${GREEN}✅ Prometheus: http://localhost:9090${NC}"
    else
        echo -e "${YELLOW}⚠️  Prometheus: 启动中...${NC}"
    fi

    # Kibana
    if curl -f http://localhost:5601/api/status &>/dev/null; then
        echo -e "${GREEN}✅ Kibana: http://localhost:5601${NC}"
    else
        echo -e "${YELLOW}⚠️  Kibana: 启动中...${NC}"
    fi
}

# 显示访问信息
show_access_info() {
    echo -e "\n${PURPLE}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║                                                           ║${NC}"
    echo -e "${PURPLE}║           🚀 CBSC统一开发环境已启动完成                       ║${NC}"
    echo -e "${PURPLE}║                                                           ║${NC}"
    echo -e "${CYAN}║  🌐 主要服务访问地址:                                        ║${NC}"
    echo -e "${GREEN}║  • API网关:        http://localhost:8000                    ║${NC}"
    echo -e "${GREEN}║  • 前端Dashboard:  http://localhost:3000                    ║${NC}"
    echo -e "${GREEN}║  • 统一Dashboard:  http://localhost:3001                    ║${NC}"
    echo -e "${GREEN}║  • Nginx代理:       http://localhost:80                      ║${NC}"
    echo -e "${CYAN}║                                                             ║${NC}"
    echo -e "${CYAN}║  📊 监控服务访问地址:                                        ║${NC}"
    echo -e "${GREEN}║  • Grafana:        http://localhost:3002 (admin/admin123)    ║${NC}"
    echo -e "${GREEN}║  • Prometheus:     http://localhost:9090                    ║${NC}"
    echo -e "${GREEN}║  • Jaeger:         http://localhost:16686                   ║${NC}"
    echo -e "${GREEN}║  • Kibana:         http://localhost:5601                    ║${NC}"
    echo -e "${CYAN}║                                                             ║${NC}"
    echo -e "${CYAN}║  📚 API文档:                                                ║${NC}"
    echo -e "${GREEN}║  • API文档:         http://localhost:8000/docs              ║${NC}"
    echo -e "${GREEN}║  • ReDoc文档:       http://localhost:8000/redoc             ║${NC}"
    echo -e "${CYAN}║                                                             ║${NC}"
    echo -e "${CYAN}║  🔧 管理命令:                                                ║${NC}"
    echo -e "${GREEN}║  • 查看日志:         docker logs -f [container_name]        ║${NC}"
    echo -e "${GREEN}║  • 停止环境:         ./scripts/dev-unified-stop.sh          ║${NC}"
    echo -e "${GREEN}║  • 重启服务:         docker restart [container_name]         ║${NC}"
    echo -e "${CYAN}║                                                             ║${NC}"
    echo -e "${YELLOW}║  📝 配置文件: .env                                          ║${NC}"
    echo -e "${YELLOW}║  📋 启动日志: $LOG_FILE                                    ║${NC}"
    echo -e "${PURPLE}║                                                           ║${NC}"
    echo -e "${PURPLE}╚═══════════════════════════════════════════════════════════════╝${NC}"
}

# 主函数
main() {
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                                                           ║"
    echo "║        🚀 CBSC统一开发环境启动脚本                          ║"
    echo "║                                                           ║"
    echo "║  统一API网关 | 服务发现 | 监控系统 | 开发环境              ║"
    echo "║                                                           ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    # 检查是否在项目根目录
    if [ ! -f "$COMPOSE_FILE" ]; then
        error "未找到Docker Compose文件: $COMPOSE_FILE"
        error "请确保在项目根目录运行此脚本"
        exit 1
    fi

    # 执行启动步骤
    log "开始启动CBSC统一开发环境..."

    check_dependencies
    create_env_file
    cleanup_containers
    create_network
    start_infrastructure
    start_core_services
    start_frontend_services
    start_monitoring_services
    check_services
    show_access_info

    log "CBSC统一开发环境启动完成！"
}

# 信号处理
trap 'error "启动过程被中断"; exit 1' INT TERM

# 执行主函数
main "$@"
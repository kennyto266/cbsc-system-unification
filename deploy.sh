#!/bin/bash
# CBSC Strategy API Docker部署脚本

set -e  # 遇到错误立即退出

echo "=========================================="
echo "CBSC Strategy API Docker Deployment"
echo "=========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Docker是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi

    log_info "Docker环境检查通过"
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."

    mkdir -p logs/nginx
    mkdir -p data
    mkdir -p database
    mkdir -p redis
    mkdir -p nginx/ssl

    # 创建Redis配置文件
    if [ ! -f redis/redis.conf ]; then
        log_info "创建Redis配置文件..."
        cat > redis/redis.conf << EOF
# Redis配置文件
bind 0.0.0.0
port 6379
timeout 0
keepalive 300
databases 16

# 持久化配置
save 900 1
save 300 10
save 60 10000

# 日志配置
loglevel notice
logfile /var/log/redis/redis.log

# 安全配置
# requirepass your-redis-password

# 内存配置
maxmemory 256mb
maxmemory-policy allkeys-lru
EOF
    fi

    # 创建Nginx配置文件
    if [ ! -f nginx/nginx.conf ]; then
        log_info "创建Nginx配置文件..."
        cat > nginx/nginx.conf << EOF
events {
    worker_connections 1024;
}

http {
    upstream cbsc_api {
        server cbsc-strategy-api:3004;
    }

    server {
        listen 80;
        server_name localhost;

        location / {
            proxy_pass http://cbsc_api;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        location /health {
            proxy_pass http://cbsc_api/health;
        }
    }
}
EOF
    fi

    # 创建数据库初始化脚本
    if [ ! -f database/init.sql ]; then
        log_info "创建数据库初始化脚本..."
        cat > database/init.sql << EOF
-- CBSC Strategy API数据库初始化脚本

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建策略表
CREATE TABLE IF NOT EXISTS strategies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    strategy_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'inactive',
    risk_level VARCHAR(20) DEFAULT 'medium',
    parameters JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_strategies_user_id ON strategies(user_id);
CREATE INDEX IF NOT EXISTS idx_strategies_status ON strategies(status);
CREATE INDEX IF NOT EXISTS idx_strategies_type ON strategies(strategy_type);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- 插入示例数据
INSERT INTO users (username, email, password_hash, is_admin)
VALUES ('admin', 'admin@cbsc.com', '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.s5uO.G', true)
ON CONFLICT (username) DO NOTHING;
EOF
    fi
}

# 构建和启动服务
deploy_services() {
    log_info "构建Docker镜像..."
    docker build -t cbsc-api:latest .
    docker-compose -f docker-compose.cbsc-api.yml build

    log_info "启动服务..."
    docker-compose -f docker-compose.cbsc-api.yml up -d

    log_info "等待服务启动..."
    sleep 30
}

# 检查服务状态
check_services() {
    log_info "检查服务状态..."

    # 检查API服务
    if curl -f http://localhost:3004/health &> /dev/null; then
        log_info "✓ CBSC Strategy API服务运行正常"
    else
        log_error "✗ CBSC Strategy API服务启动失败"
        docker-compose -f docker-compose.cbsc-api.yml logs cbsc-strategy-api
    fi

    # 检查数据库连接
    if docker exec cbsc-postgres pg_isready -U cbsc_admin -d cbsc_production &> /dev/null; then
        log_info "✓ PostgreSQL数据库连接正常"
    else
        log_error "✗ PostgreSQL数据库连接失败"
    fi

    # 检查Redis连接
    if docker exec cbsc-redis redis-cli ping &> /dev/null; then
        log_info "✓ Redis缓存服务正常"
    else
        log_error "✗ Redis缓存服务连接失败"
    fi
}

# 显示服务信息
show_info() {
    log_info "服务部署完成！"
    echo ""
    echo "服务访问地址："
    echo "  - CBSC Strategy API: http://localhost:3004"
    echo "  - API文档: http://localhost:3004/docs"
    echo "  - 数据库: localhost:5432"
    echo "  - Redis: localhost:6379"
    echo ""
    echo "常用命令："
    echo "  - 查看日志: docker-compose -f docker-compose.cbsc-api.yml logs -f"
    echo "  - 停止服务: docker-compose -f docker-compose.cbsc-api.yml down"
    echo "  - 重启服务: docker-compose -f docker-compose.cbsc-api.yml restart"
    echo ""
}

# 主函数
main() {
    case "${1:-deploy}" in
        "deploy")
            check_docker
            create_directories
            deploy_services
            check_services
            show_info
            ;;
        "stop")
            log_info "停止所有服务..."
            docker-compose -f docker-compose.cbsc-api.yml down
            ;;
        "restart")
            log_info "重启所有服务..."
            docker-compose -f docker-compose.cbsc-api.yml restart
            ;;
        "logs")
            docker-compose -f docker-compose.cbsc-api.yml logs -f
            ;;
        "status")
            docker-compose -f docker-compose.cbsc-api.yml ps
            ;;
        *)
            echo "用法: $0 [deploy|stop|restart|logs|status]"
            echo "  deploy  - 部署服务（默认）"
            echo "  stop    - 停止服务"
            echo "  restart - 重启服务"
            echo "  logs    - 查看日志"
            echo "  status  - 查看状态"
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"

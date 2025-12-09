# 简化部署指南

## 🎯 功能概述
为个人独立使用提供简化的系统部署方案，支持本地开发、一键部署和基本运维功能。

## 📋 需求优先级：P0 (部署运维)

## 🔧 部署需求

### 1. 本地开发环境
- **一键启动**: 简单的开发环境配置
- **热重载**: 代码修改自动刷新
- **数据持久化**: 本地数据库和文件存储
- **调试支持**: 开发工具和日志查看

### 2. 生产部署
- **简单安装**: 最小化的依赖配置
- **自动化部署**: 脚本化的安装流程
- **数据备份**: 自动化的数据备份机制
- **更新维护**: 简单的系统更新流程

### 3. 基础监控
- **健康检查**: 系统状态监控
- **日志管理**: 简单的日志查看和搜索
- **性能指标**: 基础的系统性能监控
- **错误告警**: 重要错误的邮件通知

## 🚀 快速开始

### 1. 系统要求
```yaml
# 最低配置要求
system_requirements:
  cpu: "2核心"
  memory: "4GB RAM"
  storage: "20GB 可用空间"
  os: "Windows 10/11, macOS 10.15+, Ubuntu 20.04+"

# 软件依赖
software_dependencies:
  python: "3.8+"
  nodejs: "16.0+"
  docker: "20.10+ (可选)"
  git: "2.0+"
```

### 2. 一键安装脚本
```bash
#!/bin/bash
# install.sh - 一键安装脚本

set -e

echo "🚀 开始安装CBSC用户管理系统..."

# 检查系统要求
check_requirements() {
    echo "🔍 检查系统要求..."

    # 检查Python
    if ! command -v python3 &> /dev/null; then
        echo "❌ 需要安装 Python 3.8+"
        exit 1
    fi

    # 检查Node.js
    if ! command -v node &> /dev/null; then
        echo "❌ 需要安装 Node.js 16.0+"
        exit 1
    fi

    echo "✅ 系统要求检查通过"
}

# 安装Python依赖
install_python_deps() {
    echo "🐍 安装Python依赖..."

    # 创建虚拟环境
    python3 -m venv venv
    source venv/bin/activate  # Linux/macOS
    # source venv/Scripts/activate  # Windows

    # 安装依赖
    pip install --upgrade pip
    pip install -r requirements.txt

    echo "✅ Python依赖安装完成"
}

# 安装Node.js依赖
install_node_deps() {
    echo "📦 安装Node.js依赖..."

    cd frontend
    npm install
    cd ..

    echo "✅ Node.js依赖安装完成"
}

# 初始化数据库
init_database() {
    echo "🗄️ 初始化数据库..."

    # 运行数据库迁移
    python scripts/setup_database.py

    # 创建默认用户
    python scripts/create_default_user.py

    echo "✅ 数据库初始化完成"
}

# 创建配置文件
create_config() {
    echo "⚙️ 创建配置文件..."

    if [ ! -f .env ]; then
        cp .env.example .env
        echo "📝 已创建 .env 配置文件，请根据需要修改"
    fi

    if [ ! -f config/user_settings.json ]; then
        cp config/user_settings.example.json config/user_settings.json
    fi

    echo "✅ 配置文件创建完成"
}

# 主安装流程
main() {
    check_requirements
    install_python_deps
    install_node_deps
    init_database
    create_config

    echo ""
    echo "🎉 安装完成！"
    echo ""
    echo "🚀 启动服务："
    echo "  ./scripts/start.sh"
    echo ""
    echo "📱 访问地址："
    echo "  前端: http://localhost:3000"
    echo "  API:  http://localhost:3004"
    echo ""
    echo "📚 更多信息："
    echo "  查看文档: docs/README.md"
    echo "  帮助支持: ./scripts/help.sh"
}

main "$@"
```

### 3. 启动脚本
```bash
#!/bin/bash
# start.sh - 服务启动脚本

set -e

echo "🚀 启动CBSC用户管理系统..."

# 激活虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 检查配置
if [ ! -f .env ]; then
    echo "❌ 配置文件不存在，请先运行 ./install.sh"
    exit 1
fi

# 创建日志目录
mkdir -p logs

# 启动后端API服务
echo "🔧 启动后端API服务..."
cd src/api
python -m uvicorn main:app --reload --host 0.0.0.0 --port 3004 > ../../logs/api.log 2>&1 &
BACKEND_PID=$!
cd ..

# 等待后端启动
sleep 3

# 启动前端开发服务器
echo "🎨 启动前端服务..."
cd frontend
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# 保存进程ID
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

echo ""
echo "✅ 服务启动完成！"
echo ""
echo "📱 访问地址："
echo "  前端应用: http://localhost:3000"
echo "  API文档:  http://localhost:3004/docs"
echo ""
echo "🛠️ 管理命令："
echo "  查看状态: ./scripts/status.sh"
echo "  停止服务: ./scripts/stop.sh"
echo "  重启服务: ./scripts/restart.sh"
echo ""
echo "📊 日志位置："
echo "  API日志:  logs/api.log"
echo "  前端日志:  logs/frontend.log"

# 等待用户输入
echo "按 Ctrl+C 停止服务"
trap './scripts/stop.sh; exit' INT
wait
```

## 📦 Docker部署

### 1. Dockerfile
```dockerfile
# Dockerfile
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 复制Python依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建非root用户
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 3004

# 启动命令
CMD ["python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "3004"]
```

### 2. docker-compose.yml
```yaml
version: '3.8'

services:
  # 数据库服务
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: cbsc_user
      POSTGRES_USER: cbsc
      POSTGRES_PASSWORD: ${DB_PASSWORD:-default_password}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    restart: unless-stopped

  # Redis缓存
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  # 后端API服务
  api:
    build: .
    environment:
      DATABASE_URL: postgresql://cbsc:${DB_PASSWORD:-default_password}@postgres:5432/cbsc_user
      REDIS_URL: redis://redis:6379/0
      SECRET_KEY: ${SECRET_KEY:-your-secret-key-here}
      ENVIRONMENT: production
    depends_on:
      - postgres
      - redis
    ports:
      - "3004:3004"
    volumes:
      - ./logs:/app/logs
      - ./uploads:/app/uploads
    restart: unless-stopped

  # 前端服务
  frontend:
    image: node:16-alpine
    working_dir: /app
    command: npm run start
    environment:
      NODE_ENV: production
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "3000:3000"
    depends_on:
      - api
    restart: unless-stopped

  # Nginx反向代理
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - api
      - frontend
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### 3. 生产环境部署脚本
```bash
#!/bin/bash
# deploy.sh - 生产环境部署脚本

set -e

ENVIRONMENT=${1:-production}
VERSION=${2:-latest}

echo "🚀 部署到 $ENVIRONMENT 环境，版本: $VERSION"

# 环境检查
check_environment() {
    echo "🔍 检查部署环境..."

    # 检查Docker
    if ! command -v docker &> /dev/null; then
        echo "❌ 需要安装 Docker"
        exit 1
    fi

    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ 需要安装 Docker Compose"
        exit 1
    fi

    # 检查配置文件
    if [ ! -f .env.production ]; then
        echo "❌ 缺少生产环境配置文件 .env.production"
        exit 1
    fi

    echo "✅ 环境检查通过"
}

# 备份数据
backup_data() {
    echo "💾 备份现有数据..."

    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"

    # 备份数据库
    if docker-compose ps postgres | grep -q "Up"; then
        docker-compose exec postgres pg_dump -U cbsc cbsc_user > "$BACKUP_DIR/database.sql"
        echo "✅ 数据库备份完成"
    fi

    # 备份用户文件
    if [ -d "uploads" ]; then
        cp -r uploads "$BACKUP_DIR/"
        echo "✅ 用户文件备份完成"
    fi

    echo "📁 备份保存至: $BACKUP_DIR"
}

# 部署应用
deploy_application() {
    echo "🚀 部署应用..."

    # 停止现有服务
    docker-compose down

    # 拉取最新镜像
    docker-compose pull

    # 启动服务
    docker-compose up -d

    echo "✅ 应用部署完成"
}

# 健康检查
health_check() {
    echo "🏥 执行健康检查..."

    # 等待服务启动
    sleep 30

    # 检查API服务
    API_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3004/health)
    if [ "$API_HEALTH" = "200" ]; then
        echo "✅ API服务健康"
    else
        echo "❌ API服务异常 (HTTP $API_HEALTH)"
        return 1
    fi

    # 检查前端服务
    FRONTEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000)
    if [ "$FRONTEND_HEALTH" = "200" ]; then
        echo "✅ 前端服务健康"
    else
        echo "❌ 前端服务异常 (HTTP $FRONTEND_HEALTH)"
        return 1
    fi

    echo "✅ 健康检查通过"
}

# 主部署流程
main() {
    check_environment
    backup_data
    deploy_application

    if health_check; then
        echo ""
        echo "🎉 部署成功！"
        echo ""
        echo "📱 访问地址："
        echo "  前端: http://localhost:3000"
        echo "  API:  http://localhost:3004"
        echo ""
        echo "🛠️ 管理命令："
        echo "  查看状态: docker-compose ps"
        echo "  查看日志: docker-compose logs -f"
        echo "  停止服务: docker-compose down"
    else
        echo "❌ 部署失败，请检查日志"
        docker-compose logs
        exit 1
    fi
}

main "$@"
```

## 📊 监控和维护

### 1. 健康检查端点
```python
# src/api/health.py
from fastapi import APIRouter, HTTPException
import asyncpg
import redis
import psutil
import os

router = APIRouter()

@router.get("/health")
async def health_check():
    """综合健康检查"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "checks": {}
    }

    # 数据库检查
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        await conn.fetchval("SELECT 1")
        await conn.close()
        health_status["checks"]["database"] = {"status": "healthy"}
    except Exception as e:
        health_status["checks"]["database"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "unhealthy"

    # Redis检查
    try:
        r = redis.from_url(REDIS_URL)
        r.ping()
        health_status["checks"]["redis"] = {"status": "healthy"}
    except Exception as e:
        health_status["checks"]["redis"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "unhealthy"

    # 系统资源检查
    try:
        health_status["checks"]["system"] = {
            "status": "healthy",
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent
        }
    except Exception as e:
        health_status["checks"]["system"] = {"status": "unhealthy", "error": str(e)}

    return health_status

@router.get("/metrics")
async def get_metrics():
    """系统指标"""
    return {
        "cpu_usage": psutil.cpu_percent(),
        "memory_usage": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent,
        "active_connections": len(active_websockets),
        "timestamp": datetime.utcnow().isoformat()
    }
```

### 2. 日志管理
```python
# src/utils/logger.py
import logging
import sys
from pathlib import Path

def setup_logger(name: str, log_file: str = None, level: str = "INFO"):
    """设置日志记录器"""

    # 创建日志目录
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    # 配置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # 控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件输出
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

# 使用示例
logger = setup_logger("cbsc_app", "logs/app.log")
```

### 3. 自动备份脚本
```bash
#!/bin/bash
# backup.sh - 自动备份脚本

set -e

BACKUP_DIR="backups"
RETENTION_DAYS=30

echo "💾 开始自动备份..."

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 生成备份文件名
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/cbsc_backup_$TIMESTAMP.tar.gz"

# 备份数据库
echo "📊 备份数据库..."
docker-compose exec -T postgres pg_dump -U cbsc cbsc_user > "$BACKUP_DIR/database_$TIMESTAMP.sql"

# 备份用户文件
echo "📁 备份用户文件..."
if [ -d "uploads" ]; then
    cp -r uploads "$BACKUP_DIR/uploads_$TIMESTAMP"
fi

# 备份配置文件
echo "⚙️ 备份配置文件..."
cp .env "$BACKUP_DIR/env_$TIMESTAMP"
cp -r config "$BACKUP_DIR/config_$TIMESTAMP"

# 创建压缩包
echo "📦 创建压缩包..."
tar -czf "$BACKUP_FILE" -C "$BACKUP_DIR" \
    "database_$TIMESTAMP.sql" \
    "uploads_$TIMESTAMP" \
    "env_$TIMESTAMP" \
    "config_$TIMESTAMP"

# 清理临时文件
rm -f "$BACKUP_DIR/database_$TIMESTAMP.sql"
rm -rf "$BACKUP_DIR/uploads_$TIMESTAMP"
rm -f "$BACKUP_DIR/env_$TIMESTAMP"
rm -rf "$BACKUP_DIR/config_$TIMESTAMP"

# 清理旧备份
echo "🧹 清理旧备份..."
find "$BACKUP_DIR" -name "cbsc_backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete

echo "✅ 备份完成: $BACKUP_FILE"
echo "🗂️ 保留最近 $RETENTION_DAYS 天的备份"
```

## 🛠️ 常用管理脚本

### 1. 状态检查
```bash
#!/bin/bash
# status.sh - 系统状态检查

echo "📊 CBSC系统状态"
echo "=================="

# 检查进程状态
if [ -f .backend.pid ]; then
    BACKEND_PID=$(cat .backend.pid)
    if ps -p $BACKEND_PID > /dev/null; then
        echo "✅ 后端API服务运行中 (PID: $BACKEND_PID)"
    else
        echo "❌ 后端API服务未运行"
    fi
else
    echo "❌ 后端API服务未启动"
fi

if [ -f .frontend.pid ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null; then
        echo "✅ 前端服务运行中 (PID: $FRONTEND_PID)"
    else
        echo "❌ 前端服务未运行"
    fi
else
    echo "❌ 前端服务未启动"
fi

# 检查端口
echo ""
echo "🔌 端口状态:"
netstat -tlnp 2>/dev/null | grep -E ':(3000|3004|5432|6379)' || echo "未检测到服务端口"

# 检查系统资源
echo ""
echo "💻 系统资源:"
echo "CPU使用率: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "内存使用: $(free -h | awk '/^Mem:/ {printf "%.1f%%", $3/$2 * 100.0}')"
echo "磁盘使用: $(df -h . | awk 'NR==2 {printf "%s", $5}')"

# 检查日志错误
echo ""
echo "📝 最近的错误:"
if [ -f logs/api.log ]; then
    echo "API错误日志:"
    tail -n 5 logs/api.log | grep -i error || echo "无错误"
fi

if [ -f logs/frontend.log ]; then
    echo "前端错误日志:"
    tail -n 5 logs/frontend.log | grep -i error || echo "无错误"
fi
```

## 📋 验收标准

### 部署验收
- [ ] 一键安装脚本正常工作
- [ ] 服务启动和停止功能正常
- [ ] 健康检查端点可用
- [ ] 日志记录功能正常
- [ ] 数据备份功能可用

### 运维验收
- [ ] 监控指标收集正常
- [ ] 错误告警及时发送
- [ ] 系统资源使用合理
- [ ] 备份恢复流程有效

### 性能验收
- [ ] 系统启动时间 < 2分钟
- [ ] API响应时间 < 500ms
- [ ] 前端页面加载 < 3秒
- [ ] 数据库查询优化

## 🎯 成功指标

### 部署效率
- **安装时间**: < 10分钟
- **部署时间**: < 5分钟
- **故障恢复**: < 10分钟
- **备份时间**: < 2分钟

### 系统稳定性
- **可用性**: > 99%
- **平均故障间隔**: > 30天
- **数据安全**: 0数据丢失
- **监控覆盖率**: 100%

这个简化的部署方案专注于个人用户的使用场景，提供了完整的安装、部署、监控和维护功能，操作简单直观。
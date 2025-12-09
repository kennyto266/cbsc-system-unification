# 港股量化交易AI Agent系统 - 真实系统部署指南

## 概述

本指南详细介绍了港股量化交易AI Agent系统的部署流程，包括环境准备、系统安装、配置设置、启动验证等完整步骤。该系统集成了真实的市场数据源、回测引擎和Telegram Bot，提供完整的量化交易解决方案。

## 系统架构

### 核心组件

- **数据适配器层**：集成黑人RAW DATA数据源
- **回测引擎**：集成StockBacktest项目
- **AI Agent系统**：7个专业AI Agent
- **策略管理系统**：策略生命周期管理
- **监控告警系统**：实时监控和告警
- **Telegram集成**：CURSOR CLI项目集成

### 技术栈

- **后端**：Python 3.9+, FastAPI, asyncio
- **数据存储**：PostgreSQL, Redis
- **消息队列**：Redis Pub/Sub
- **监控**：Prometheus, Grafana
- **部署**：Docker, Docker Compose
- **外部集成**：Telegram Bot API, Cursor AI

## 环境要求

### 硬件要求

- **CPU**：8核心以上，支持AVX指令集
- **内存**：32GB以上
- **存储**：500GB以上SSD
- **网络**：稳定的互联网连接，低延迟

### 软件要求

- **操作系统**：Windows 10/11, Linux Ubuntu 20.04+, macOS 12+
- **Python**：3.9或更高版本
- **Docker**：20.10或更高版本
- **Docker Compose**：2.0或更高版本
- **Git**：2.30或更高版本

### 外部服务

- **PostgreSQL**：13或更高版本
- **Redis**：6.0或更高版本
- **Telegram Bot Token**：从@BotFather获取
- **Cursor API Key**：用于AI集成

## 安装步骤

### 1. 环境准备

#### 1.1 克隆项目

```bash
git clone https://github.com/your-org/hk-quantitative-trading-system.git
cd hk-quantitative-trading-system
```

#### 1.2 创建虚拟环境

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

#### 1.3 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 数据库设置

#### 2.1 安装PostgreSQL

**Windows:**
```bash
# 下载并安装PostgreSQL
# https://www.postgresql.org/download/windows/
```

**Linux (Ubuntu):**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

**macOS:**
```bash
brew install postgresql
```

#### 2.2 创建数据库

```bash
# 连接到PostgreSQL
psql -U postgres

# 创建数据库和用户
CREATE DATABASE trading_system;
CREATE USER trading_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE trading_system TO trading_user;
\q
```

#### 2.3 安装Redis

**Windows:**
```bash
# 下载Redis for Windows
# https://github.com/microsoftarchive/redis/releases
```

**Linux (Ubuntu):**
```bash
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**macOS:**
```bash
brew install redis
brew services start redis
```

### 3. 配置设置

#### 3.1 创建环境配置文件

```bash
cp .env.example .env
```

#### 3.2 编辑环境配置

```env
# 数据库配置
DATABASE_URL=postgresql://trading_user:your_password@localhost:5432/trading_system
REDIS_URL=redis://localhost:6379/0

# 系统配置
SYSTEM_ID=trading_system_001
SYSTEM_NAME=港股量化交易AI Agent系统
VERSION=1.0.0
ENVIRONMENT=production
DEBUG=false

# 数据源配置
RAW_DATA_PATH=C:\Users\Penguin8n\Desktop\黑人RAW DATA
STOCKBACKTEST_PATH=C:\Users\Penguin8n\Desktop\StockBacktest
CURSOR_CLI_PATH=C:\Users\Penguin8n\Desktop\CURSOR CLI

# Telegram Bot配置
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_ADMIN_CHAT_ID=your_chat_id_here
CURSOR_API_KEY=your_cursor_api_key_here

# 监控配置
MONITORING_ENABLED=true
ALERTING_ENABLED=true
LOG_LEVEL=INFO

# 交易配置
MAX_POSITION_SIZE=1000000.0
RISK_LIMIT=0.1
COMMISSION_RATE=0.001
SLIPPAGE_RATE=0.0005
```

#### 3.3 验证配置

```bash
python scripts/validate_config.py
```

### 4. 数据源集成

#### 4.1 配置黑人RAW DATA

```bash
# 确保数据路径正确
# 检查数据格式和权限
python scripts/validate_data_source.py --source raw_data
```

#### 4.2 配置StockBacktest

```bash
# 验证回测引擎
python scripts/validate_data_source.py --source stockbacktest
```

#### 4.3 配置CURSOR CLI

```bash
# 测试Telegram Bot连接
python scripts/validate_data_source.py --source cursor_cli
```

### 5. 系统启动

#### 5.1 初始化系统

```bash
python scripts/init_system.py
```

#### 5.2 启动核心服务

```bash
# 启动数据适配器
python -m src.data_adapters.data_service &

# 启动回测引擎
python -m src.backtest.stockbacktest_integration &

# 启动AI Agent系统
python -m src.agents.agent_coordinator &

# 启动策略管理
python -m src.strategy_management.strategy_manager &

# 启动监控系统
python -m src.monitoring.real_time_monitor &

# 启动Telegram集成
python -m src.telegram.integration_manager &
```

#### 5.3 使用Docker Compose（推荐）

```bash
# 构建镜像
docker-compose build

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 6. 系统验证

#### 6.1 健康检查

```bash
# 检查系统状态
curl http://localhost:8000/health

# 检查组件状态
curl http://localhost:8000/status

# 检查数据源连接
curl http://localhost:8000/data/status
```

#### 6.2 功能测试

```bash
# 运行集成测试
pytest tests/integration/ -v

# 运行端到端测试
pytest tests/integration/test_end_to_end_integration.py -v

# 运行性能测试
pytest tests/integration/test_performance_integration.py -v
```

#### 6.3 监控验证

```bash
# 访问监控仪表板
# http://localhost:3000 (Grafana)
# http://localhost:8000/dashboard (系统仪表板)

# 检查Telegram Bot
# 发送 /start 命令到你的Bot
```

## 生产环境部署

### 1. 服务器配置

#### 1.1 推荐配置

- **CPU**：16核心，3.0GHz以上
- **内存**：64GB以上
- **存储**：1TB NVMe SSD
- **网络**：1Gbps专线

#### 1.2 安全配置

```bash
# 配置防火墙
sudo ufw enable
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw allow 5432  # PostgreSQL
sudo ufw allow 6379  # Redis

# 配置SSL证书
sudo certbot --nginx -d your-domain.com
```

### 2. 高可用部署

#### 2.1 数据库集群

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  postgres-primary:
    image: postgres:13
    environment:
      POSTGRES_DB: trading_system
      POSTGRES_USER: trading_user
      POSTGRES_PASSWORD: your_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
  
  postgres-replica:
    image: postgres:13
    environment:
      POSTGRES_DB: trading_system
      POSTGRES_USER: trading_user
      POSTGRES_PASSWORD: your_password
    depends_on:
      - postgres-primary
    command: |
      bash -c "
      until pg_basebackup -h postgres-primary -D /var/lib/postgresql/data -U trading_user -v -P -W
      do
        echo 'Waiting for primary to connect...'
        sleep 1s
      done
      echo 'Backup done'
      "
```

#### 2.2 负载均衡

```yaml
# nginx.conf
upstream trading_system {
    server app1:8000;
    server app2:8000;
    server app3:8000;
}

server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://trading_system;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. 监控和告警

#### 3.1 Prometheus配置

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'trading-system'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s
```

#### 3.2 Grafana仪表板

```bash
# 导入预配置仪表板
curl -X POST \
  http://admin:admin@localhost:3000/api/dashboards/db \
  -H 'Content-Type: application/json' \
  -d @grafana/trading_system_dashboard.json
```

#### 3.3 告警规则

```yaml
# alert_rules.yml
groups:
  - name: trading_system
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
      
      - alert: HighMemoryUsage
        expr: process_resident_memory_bytes / 1024 / 1024 / 1024 > 8
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High memory usage detected"
```

## 故障排除

### 1. 常见问题

#### 1.1 数据库连接问题

**问题**：无法连接到PostgreSQL
```bash
# 检查PostgreSQL状态
sudo systemctl status postgresql

# 检查连接
psql -h localhost -U trading_user -d trading_system

# 检查防火墙
sudo ufw status
```

**解决方案**：
1. 确保PostgreSQL服务正在运行
2. 检查用户名和密码
3. 验证数据库存在
4. 检查网络连接

#### 1.2 Redis连接问题

**问题**：无法连接到Redis
```bash
# 检查Redis状态
redis-cli ping

# 检查Redis配置
redis-cli config get bind
redis-cli config get port
```

**解决方案**：
1. 确保Redis服务正在运行
2. 检查Redis配置
3. 验证网络连接
4. 检查内存使用

#### 1.3 数据源问题

**问题**：数据源连接失败
```bash
# 检查数据源状态
python scripts/validate_data_source.py --source all

# 检查文件权限
ls -la /path/to/data/source

# 检查数据格式
python scripts/validate_data_format.py
```

**解决方案**：
1. 验证数据路径正确
2. 检查文件权限
3. 验证数据格式
4. 检查网络连接

### 2. 性能问题

#### 2.1 内存使用过高

**监控**：
```bash
# 查看内存使用
free -h
ps aux --sort=-%mem | head

# 查看Python进程内存
ps -o pid,ppid,cmd,%mem,%cpu -p $(pgrep python)
```

**解决方案**：
1. 增加系统内存
2. 优化代码内存使用
3. 调整缓存大小
4. 重启服务

#### 2.2 CPU使用过高

**监控**：
```bash
# 查看CPU使用
top
htop

# 查看Python进程CPU
ps -o pid,ppid,cmd,%mem,%cpu -p $(pgrep python)
```

**解决方案**：
1. 优化算法性能
2. 增加CPU核心
3. 调整并发设置
4. 优化数据库查询

### 3. 日志分析

#### 3.1 查看系统日志

```bash
# 查看应用日志
tail -f logs/trading_system.log

# 查看错误日志
grep ERROR logs/trading_system.log

# 查看警告日志
grep WARNING logs/trading_system.log
```

#### 3.2 分析性能日志

```bash
# 查看性能指标
grep "performance" logs/trading_system.log

# 查看响应时间
grep "response_time" logs/trading_system.log

# 查看吞吐量
grep "throughput" logs/trading_system.log
```

## 维护和更新

### 1. 日常维护

#### 1.1 系统监控

```bash
# 检查系统状态
python scripts/system_health_check.py

# 检查数据质量
python scripts/data_quality_check.py

# 检查性能指标
python scripts/performance_check.py
```

#### 1.2 数据备份

```bash
# 备份数据库
pg_dump -h localhost -U trading_user trading_system > backup_$(date +%Y%m%d).sql

# 备份配置文件
tar -czf config_backup_$(date +%Y%m%d).tar.gz config/

# 备份日志
tar -czf logs_backup_$(date +%Y%m%d).tar.gz logs/
```

### 2. 系统更新

#### 2.1 代码更新

```bash
# 拉取最新代码
git pull origin main

# 安装新依赖
pip install -r requirements.txt

# 运行数据库迁移
python scripts/migrate_database.py

# 重启服务
docker-compose restart
```

#### 2.2 配置更新

```bash
# 备份当前配置
cp .env .env.backup

# 更新配置
# 编辑 .env 文件

# 验证配置
python scripts/validate_config.py

# 重启服务
docker-compose restart
```

### 3. 安全更新

#### 3.1 依赖更新

```bash
# 检查安全漏洞
pip-audit

# 更新依赖
pip install --upgrade -r requirements.txt

# 更新Docker镜像
docker-compose pull
docker-compose up -d
```

#### 3.2 系统更新

```bash
# Ubuntu/Debian
sudo apt update
sudo apt upgrade

# CentOS/RHEL
sudo yum update

# 重启系统
sudo reboot
```

## 支持和联系

### 1. 技术支持

- **文档**：查看完整文档
- **FAQ**：常见问题解答
- **社区**：GitHub Issues
- **邮件**：support@your-domain.com

### 2. 紧急联系

- **电话**：+86-xxx-xxxx-xxxx
- **微信**：your-wechat-id
- **Telegram**：@your-telegram-username

### 3. 贡献指南

- **代码贡献**：提交Pull Request
- **文档贡献**：改进文档
- **问题报告**：提交Issue
- **功能请求**：提交Feature Request

## 附录

### A. 配置文件模板

#### A.1 Docker Compose配置

```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://trading_user:password@db:5432/trading_system
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
  
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: trading_system
      POSTGRES_USER: trading_user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
  
  redis:
    image: redis:6
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

#### A.2 Nginx配置

```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream trading_system {
        server app:8000;
    }
    
    server {
        listen 80;
        server_name localhost;
        
        location / {
            proxy_pass http://trading_system;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
    }
}
```

### B. 环境变量说明

| 变量名 | 说明 | 默认值 | 必需 |
|--------|------|--------|------|
| DATABASE_URL | 数据库连接URL | - | 是 |
| REDIS_URL | Redis连接URL | redis://localhost:6379/0 | 是 |
| SYSTEM_ID | 系统ID | trading_system_001 | 是 |
| SYSTEM_NAME | 系统名称 | 港股量化交易AI Agent系统 | 是 |
| VERSION | 系统版本 | 1.0.0 | 是 |
| ENVIRONMENT | 环境 | development | 是 |
| DEBUG | 调试模式 | false | 否 |
| RAW_DATA_PATH | 原始数据路径 | - | 是 |
| STOCKBACKTEST_PATH | 回测引擎路径 | - | 是 |
| CURSOR_CLI_PATH | CURSOR CLI路径 | - | 是 |
| TELEGRAM_BOT_TOKEN | Telegram Bot Token | - | 是 |
| TELEGRAM_ADMIN_CHAT_ID | 管理员聊天ID | - | 是 |
| CURSOR_API_KEY | Cursor API密钥 | - | 是 |
| MONITORING_ENABLED | 启用监控 | true | 否 |
| ALERTING_ENABLED | 启用告警 | true | 否 |
| LOG_LEVEL | 日志级别 | INFO | 否 |
| MAX_POSITION_SIZE | 最大持仓大小 | 1000000.0 | 否 |
| RISK_LIMIT | 风险限制 | 0.1 | 否 |
| COMMISSION_RATE | 佣金率 | 0.001 | 否 |
| SLIPPAGE_RATE | 滑点率 | 0.0005 | 否 |

### C. 端口说明

| 端口 | 服务 | 说明 |
|------|------|------|
| 8000 | 主应用 | FastAPI应用 |
| 5432 | PostgreSQL | 数据库 |
| 6379 | Redis | 缓存和消息队列 |
| 3000 | Grafana | 监控仪表板 |
| 9090 | Prometheus | 指标收集 |

### D. 目录结构

```
hk-quantitative-trading-system/
├── src/                    # 源代码
│   ├── agents/            # AI Agent
│   ├── data_adapters/     # 数据适配器
│   ├── backtest/          # 回测引擎
│   ├── strategy_management/ # 策略管理
│   ├── monitoring/        # 监控系统
│   ├── telegram/          # Telegram集成
│   └── integration/       # 系统集成
├── tests/                 # 测试代码
├── docs/                  # 文档
├── scripts/               # 脚本
├── config/                # 配置文件
├── data/                  # 数据目录
├── logs/                  # 日志目录
├── docker-compose.yml     # Docker配置
├── requirements.txt       # Python依赖
├── .env.example          # 环境变量模板
└── README.md             # 项目说明
```

---

**注意**：本部署指南基于当前系统版本编写，请根据实际环境调整配置参数。如有问题，请参考故障排除部分或联系技术支持。

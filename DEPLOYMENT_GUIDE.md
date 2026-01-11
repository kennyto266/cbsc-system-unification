# CBSC系统开发环境和API网关部署指南

## 概述

本文档详细介绍了CBSC量化交易策略管理系统的开发环境搭建和API网关部署流程。该系统基于微服务架构，采用Docker容器化部署，提供了完整的开发、测试和生产环境支持。

## 系统架构

### 服务组件

- **API Gateway** (端口8000): 统一入口点，负责路由、认证、限流
- **PostgreSQL** (端口5432): 主数据库，存储用户、策略、配置等数据
- **Redis** (端口6379): 缓存和会话管理
- **Frontend** (端口3000): React前端应用
- **Unified Dashboard** (端口3001): 统一仪表板
- **Nginx** (端口80/443): 反向代理和负载均衡
- **Grafana** (端口8080): 监控仪表板
- **Prometheus** (端口9090): 指标收集
- **PgAdmin** (端口5050): 数据库管理工具
- **Redis Commander** (端口8081): Redis管理工具

### 端口分配

| 服务 | 端口 | 描述 |
|------|------|------|
| API Gateway | 8000 | 统一API入口 |
| PostgreSQL | 5432 | 数据库 |
| Redis | 6379 | 缓存 |
| Frontend | 3000 | React前端 |
| Unified Dashboard | 3001 | 统一仪表板 |
| Nginx HTTP | 80 | Web服务器 |
| Nginx HTTPS | 443 | SSL Web服务器 |
| Grafana | 8080 | 监控仪表板 |
| Prometheus | 9090 | 指标收集 |
| PgAdmin | 5050 | 数据库管理 |
| Redis Commander | 8081 | Redis管理 |

## 前置要求

### 系统要求

- **操作系统**: Linux/macOS/Windows 10+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **内存**: 最少8GB，推荐16GB
- **存储**: 最少20GB可用空间
- **网络**: 稳定的互联网连接

### 软件依赖

```bash
# 检查Docker版本
docker --version

# 检查Docker Compose版本
docker-compose --version

# 检查可用内存（Linux/macOS）
free -h

# 检查磁盘空间
df -h
```

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/your-org/cbsc-system.git
cd cbsc-system
```

### 2. 环境配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量（根据你的环境调整）
nano .env
```

### 3. 启动开发环境

#### Linux/macOS

```bash
# 给脚本执行权限
chmod +x scripts/dev-start.sh

# 启动开发环境
./scripts/dev-start.sh

# 或者同时启动后端服务
./scripts/dev-start.sh --with-backend
```

#### Windows

```cmd
# 启动开发环境
scripts\dev-start.bat

# 或者同时启动后端服务
scripts\dev-start.bat --with-backend
```

### 4. 验证安装

访问以下URL验证服务是否正常运行：

- **API Gateway**: http://localhost:8000/health
- **API 文档**: http://localhost:8000/docs
- **前端应用**: http://localhost:3000
- **统一Dashboard**: http://localhost:3001
- **Grafana监控**: http://localhost:8080 (admin/admin)

## 详细配置

### 开发环境配置

#### Docker Compose配置

开发环境使用`docker-compose.dev.yml`配置文件：

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: cbsc-dev-postgres
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: cbsc_dev
      POSTGRES_USER: cbsc_dev
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-cbsc_dev_password}
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data
      - ./database/dev/init:/docker-entrypoint-initdb.d
      - ./database/dev/postgres.conf:/etc/postgresql/postgresql.conf
```

#### 环境变量配置

开发环境的关键环境变量：

```bash
# 数据库配置
POSTGRES_DB=cbsc_dev
POSTGRES_USER=cbsc_dev
POSTGRES_PASSWORD=cbsc_dev_password

# API网关配置
GATEWAY_SECRET_KEY=dev_secret_key_change_in_production
JWT_SECRET=dev_jwt_secret_change_in_production

# 应用配置
ENVIRONMENT=development
LOG_LEVEL=DEBUG

# CORS配置（开发环境允许所有源）
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

### 生产环境配置

#### Docker Compose配置

生产环境使用`docker-compose.prod.yml`配置文件：

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: cbsc-prod-postgres
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_prod_data:/var/lib/postgresql/data
      - ./database/prod/init:/docker-entrypoint-initdb.d
    restart: always
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```

#### 安全配置

生产环境必须配置的安全项：

```bash
# 强密码（至少32位随机字符）
GATEWAY_SECRET_KEY=your_extremely_secure_secret_key_here
JWT_SECRET=your_jwt_secret_key_here

# SSL配置
SSL_ENABLED=true
SSL_CERT_PATH=/app/ssl/cert.pem
SSL_KEY_PATH=/app/ssl/key.pem

# 生产环境设置
ENVIRONMENT=production
LOG_LEVEL=INFO
RATE_LIMIT_ENABLED=true
```

#### Nginx生产配置

生产环境Nginx配置要点：

```nginx
# SSL配置
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;

# 安全头部
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;

# 限流配置
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/m;
```

## 服务管理

### 启动服务

```bash
# 启动所有服务
docker-compose -f docker-compose.dev.yml up -d

# 启动特定服务
docker-compose -f docker-compose.dev.yml up -d postgres redis

# 使用profile启动服务
docker-compose -f docker-compose.dev.yml --profile tools up -d
```

### 停止服务

```bash
# 停止所有服务
docker-compose -f docker-compose.dev.yml down

# 停止并删除数据卷
docker-compose -f docker-compose.dev.yml down -v
```

### 查看服务状态

```bash
# 查看服务状态
docker-compose -f docker-compose.dev.yml ps

# 查看服务日志
docker-compose -f docker-compose.dev.yml logs -f [service-name]

# 查看所有服务日志
docker-compose -f docker-compose.dev.yml logs -f
```

### 重启服务

```bash
# 重启特定服务
docker-compose -f docker-compose.dev.yml restart [service-name]

# 重启所有服务
docker-compose -f docker-compose.dev.yml restart
```

## 数据库管理

### 连接数据库

```bash
# 使用Docker exec连接PostgreSQL
docker-compose -f docker-compose.dev.yml exec postgres psql -U cbsc_dev -d cbsc_dev

# 使用外部工具连接
# Host: localhost
# Port: 5432
# Database: cbsc_dev
# Username: cbsc_dev
# Password: cbsc_dev_password
```

### 数据库初始化

开发环境会自动执行初始化脚本：

1. 创建扩展：`uuid-ossp`, `pg_stat_statements`, `pg_trgm`
2. 创建schema：`cbsc`, `auth`, `analytics`, `config`
3. 创建基础表：`users`, `strategies`, `performance_metrics`, `system_config`
4. 插入默认数据：管理员用户、示例策略

### 数据备份

```bash
# 备份数据库
docker-compose -f docker-compose.dev.yml exec postgres pg_dump -U cbsc_dev cbsc_dev > backup.sql

# 恢复数据库
docker-compose -f docker-compose.dev.yml exec -T postgres psql -U cbsc_dev cbsc_dev < backup.sql
```

## 监控和日志

### 监控配置

系统提供多层次的监控：

1. **应用级监控**: FastAPI内置健康检查
2. **容器级监控**: Docker健康检查
3. **基础设施监控**: Prometheus + Grafana
4. **日志聚合**: 结构化日志输出

### 访问监控仪表板

- **Grafana**: http://localhost:8080
  - 用户名: admin
  - 密码: admin123 (可在.env中修改)

- **Prometheus**: http://localhost:9090

### 日志查看

```bash
# 查看API网关日志
docker-compose -f docker-compose.dev.yml logs -f api-gateway

# 查看数据库日志
docker-compose -f docker-compose.dev.yml logs -f postgres

# 查看所有服务日志
docker-compose -f docker-compose.dev.yml logs -f
```

## 开发工具

### 数据库管理工具

- **PgAdmin**: http://localhost:5050
  - 可视化数据库管理
  - 查询编辑器
  - 备份/恢复功能

### Redis管理工具

- **Redis Commander**: http://localhost:8081
  - 可视化Redis数据
  - 键值对管理
  - 性能监控

## 故障排除

### 常见问题

#### 1. Docker启动失败

```bash
# 检查Docker状态
docker info

# 检查端口占用
netstat -tulpn | grep :8000

# 清理Docker资源
docker system prune -a
```

#### 2. 数据库连接失败

```bash
# 检查PostgreSQL状态
docker-compose -f docker-compose.dev.yml exec postgres pg_isready -U cbsc_dev

# 查看数据库日志
docker-compose -f docker-compose.dev.yml logs postgres
```

#### 3. Redis连接失败

```bash
# 检查Redis状态
docker-compose -f docker-compose.dev.yml exec redis redis-cli ping

# 查看Redis日志
docker-compose -f docker-compose.dev.yml logs redis
```

#### 4. 前端构建失败

```bash
# 重新构建前端
docker-compose -f docker-compose.dev.yml build frontend

# 清理前端缓存
docker-compose -f docker-compose.dev.yml exec frontend rm -rf node_modules/.cache
```

#### 5. API网关启动失败

```bash
# 检查网关日志
docker-compose -f docker-compose.dev.yml logs api-gateway

# 检查依赖服务状态
docker-compose -f docker-compose.dev.yml ps
```

### 性能优化

#### 内存优化

```yaml
# docker-compose.yml中的内存限制
services:
  postgres:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```

#### 磁盘优化

```bash
# 清理未使用的Docker镜像
docker image prune -a

# 清理未使用的卷
docker volume prune
```

## 部署检查清单

### 部署前检查

- [ ] 所有必需的软件已安装
- [ ] 环境变量已正确配置
- [ ] 防火墙规则已设置
- [ ] SSL证书已准备（生产环境）
- [ ] 备份策略已制定

### 部署后验证

- [ ] 所有服务正常启动
- [ ] 健康检查端点响应正常
- [ ] 数据库连接正常
- [ ] Redis缓存工作正常
- [ ] 前端应用可正常访问
- [ ] API文档可正常访问
- [ ] 监控仪表板数据正常

### 安全检查

- [ ] 默认密码已更改
- [ ] SSL证书配置正确
- [ ] 防火墙规则有效
- [ ] 敏感信息已加密
- [ ] 访问控制已配置

## 维护操作

### 日常维护

```bash
# 查看系统资源使用
docker stats

# 清理日志文件
docker-compose -f docker-compose.dev.yml exec api-gateway find /app/logs -name "*.log" -mtime +7 -delete

# 检查磁盘空间
df -h
```

### 更新部署

```bash
# 拉取最新代码
git pull origin main

# 重新构建镜像
docker-compose -f docker-compose.dev.yml build

# 重启服务
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml up -d
```

### 扩容服务

```bash
# 扩展API网关实例
docker-compose -f docker-compose.prod.yml up -d --scale api-gateway=3

# 扩展后端服务
docker-compose -f docker-compose.prod.yml up -d --scale user-management=2
```

## 总结

本部署指南提供了CBSC系统完整的开发环境搭建和部署流程。通过遵循本指南，您可以快速建立一个功能完整、安全可靠的开发和生产环境。

如需进一步的技术支持或有任何问题，请联系开发团队或查阅相关文档。

---

**文档版本**: 1.0
**最后更新**: 2025-12-11
**维护团队**: CBSC Development Team
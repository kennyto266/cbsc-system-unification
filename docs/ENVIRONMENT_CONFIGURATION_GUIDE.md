# 环境配置统一管理指南

## 概述

本文档说明 CBSC 量化交易策略管理系统的环境配置管理方案，旨在解决配置文件分散、重复和不一致的问题。

## 新的配置结构

### 环境文件

项目根目录包含以下环境配置文件：

```
CODEX--/
├── .env.example          # 配置模板（提交到版本控制）
├── .env.development      # 开发环境配置（提交到版本控制）
├── .env.test             # 测试环境配置（提交到版本控制）
└── .env.production       # 生产环境配置（不提交，包含敏感信息）
```

### 前端配置

前端使用 Vite 的环境变量系统：

```
frontend/
├── .env.example          # 前端配置模板
├── .env.development      # 开发环境
├── .env.test             # 测试环境
└── .env.production       # 生产环境
```

## 配置变量分类

### 1. 系统基础配置

| 变量名 | 说明 | 开发 | 测试 | 生产 |
|--------|------|------|------|------|
| `ENVIRONMENT` | 环境标识 | development | test | production |
| `APP_NAME` | 应用名称 | CBSC Quant Trading System | 同左 | 同左 |
| `APP_VERSION` | 应用版本 | 1.0.0 | 同左 | 同左 |
| `DEBUG` | 调试模式 | true | false | false |
| `LOG_LEVEL` | 日志级别 | DEBUG | WARNING | INFO |

### 2. 数据库配置

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `DATABASE_URL` | PostgreSQL 连接字符串 | `postgresql://user:pass@host:5432/db` |
| `POSTGRES_DB` | 数据库名称 | `cbsc_dev` / `cbsc_test` / `cbsc_production` |
| `POSTGRES_USER` | 数据库用户名 | - |
| `POSTGRES_PASSWORD` | 数据库密码 | - |
| `POSTGRES_HOST` | 数据库主机 | `localhost` / `prod-db.example.com` |
| `POSTGRES_PORT` | 数据库端口 | `5432` |
| `DB_POOL_SIZE` | 连接池大小 | `10` / `20` |

**重要提示**：不同环境必须使用不同的数据库！

### 3. Redis 配置

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `REDIS_URL` | Redis 连接字符串 | `redis://localhost:6379/0` |
| `REDIS_PASSWORD` | Redis 密码 | - |
| `REDIS_HOST` | Redis 主机 | - |
| `REDIS_PORT` | Redis 端口 | `6379` |
| `REDIS_DB` | Redis 数据库编号 | `0` / `1` (测试) |

**重要提示**：测试环境应使用不同的 Redis DB（如 DB 1）。

### 4. 安全配置

| 变量名 | 说明 | 生成方法 |
|--------|------|----------|
| `JWT_SECRET` | JWT 签名密钥 | `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `SECRET_KEY` | 应用密钥 | 同上 |
| `REFRESH_SECRET_KEY` | 刷新令牌密钥 | 同上 |
| `SESSION_SECRET` | 会话密钥 | 同上 |
| `ENCRYPTION_KEY` | 加密密钥 | 32 字节随机字符串 |

**安全要求**：
- 所有密钥必须至少 32 字符
- 生产环境必须使用强随机密钥
- 定期轮换密钥
- 不要提交到版本控制

### 5. API 配置

| 变量名 | 说明 | 开发 | 测试 | 生产 |
|--------|------|------|------|------|
| `API_HOST` | API 主机 | `0.0.0.0` | `127.0.0.1` | `0.0.0.0` |
| `API_PORT` | API 端口 | `3004` | 同左 | 同左 |
| `API_PREFIX` | API 路径前缀 | `/api/v1` | 同左 | 同左 |
| `API_WORKERS` | 工作进程数 | `1` | `1` | `8` |

### 6. CORS 配置

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `CORS_ORIGINS` | 允许的跨域来源 | `http://localhost:3000,http://localhost:3001` |

**开发环境**：允许本地地址
**生产环境**：仅允许信任的域名

### 7. 服务端口配置

| 服务 | 端口 | 说明 |
|------|------|------|
| `FRONTEND_PORT` | 3000 | 前端应用 |
| `UNIFIED_DASHBOARD_PORT` | 3001 | 统一仪表板 |
| `USER_MANAGEMENT_PORT` | 3004 | 用户管理 API |
| `WEBSOCKET_PORT` | 3006 | WebSocket 服务 |
| `POSTGRES_PORT` | 5432 | PostgreSQL |
| `REDIS_PORT` | 6379 | Redis |
| `GRAFANA_PORT` | 3002 | Grafana |
| `PROMETHEUS_PORT` | 9090 | Prometheus |

### 8. 前端环境变量

前端变量必须以 `VITE_` 开头：

| 变量名 | 说明 |
|--------|------|
| `VITE_API_BASE_URL` | 后端 API 地址 |
| `VITE_WS_URL` | WebSocket 地址 |
| `VITE_APP_TITLE` | 应用标题 |
| `VITE_ENABLE_WEBSOCKET` | 是否启用 WebSocket |
| `VITE_ENVIRONMENT` | 环境标识 |

## 使用指南

### 开发环境

1. **复制开发配置**：
   ```bash
   cp .env.development .env.local
   ```

2. **修改必要配置**（如需要）：
   ```bash
   # 编辑 .env.local
   nano .env.local
   ```

3. **启动服务**：
   ```bash
   # 后端
   python src/api/main.py

   # 前端
   cd frontend
   npm run dev
   ```

### 测试环境

测试环境配置自动加载，通常无需手动设置：

```bash
# 运行测试
pytest tests/
```

### 生产环境

1. **创建生产配置**：
   ```bash
   cp .env.production .env.local
   ```

2. **修改所有敏感配置**：
   - 更改所有数据库密码
   - 更改所有 JWT 密钥
   - 更改所有 API 密钥
   - 更新域名和 URL

3. **生成安全密钥**：
   ```bash
   # 生成 JWT 密钥
   python -c "import secrets; print(secrets.token_urlsafe(32))"

   # 生成加密密钥
   python -c "import secrets; print(secrets.token_bytes(32).hex())"
   ```

4. **设置文件权限**：
   ```bash
   chmod 600 .env.local
   ```

5. **启动服务**：
   ```bash
   docker-compose up -d
   ```

## 环境变量加载顺序

Python 应用按以下顺序加载环境变量：

1. 系统环境变量
2. `.env.local`（最高优先级，不提交）
3. `.env.{environment}`（如 `.env.development`）
4. `.env`（如果存在）
5. `.env.example`（作为默认值）

## 前端环境变量

Vite 在不同环境下的加载顺序：

1. `vite dev` → `.env.development`
2. `vite build` → `.env.production`
3. `vite test` → `.env.test`

**重要**：前端变量必须以 `VITE_` 开头才能在客户端代码中访问。

## 安全最佳实践

### 1. 密钥管理

**推荐方案**：
- 使用密钥管理服务（AWS Secrets Manager、Azure Key Vault）
- 避免在配置文件中硬编码密钥
- 使用环境变量注入

**示例**：
```python
# 不推荐
SECRET_KEY="hardcoded_secret_key"

# 推荐
SECRET_KEY = os.getenv("SECRET_KEY")
```

### 2. 密钥轮换

定期轮换密钥：
- JWT 密钥：每 90 天
- 数据库密码：每 90 天
- API 密钥：根据提供商要求

### 3. 访问控制

```bash
# 限制配置文件权限
chmod 600 .env.local
chmod 640 .env.development
```

### 4. Git 忽略规则

确保 `.gitignore` 包含：
```gitignore
# 环境配置
.env.local
.env.*.local
.env.production

# 备份文件
*.env.bak
*.env.backup

# 敏感信息
secrets/
*.pem
*.key
```

## 配置验证

### 检查必需变量

创建 `scripts/check_env.py`：

```python
#!/usr/bin/env python3
import os
import sys

required_vars = [
    "DATABASE_URL",
    "REDIS_URL",
    "JWT_SECRET",
    "SECRET_KEY",
]

missing = []
for var in required_vars:
    if not os.getenv(var):
        missing.append(var)

if missing:
    print(f"Missing required environment variables: {', '.join(missing)}")
    sys.exit(1)
else:
    print("All required environment variables are set.")
```

### 运行验证

```bash
python scripts/check_env.py
```

## 故障排查

### 问题：连接到错误的数据库

**原因**：环境变量未正确加载

**解决方案**：
1. 检查当前环境变量：
   ```bash
   echo $DATABASE_URL
   ```

2. 确认使用正确的配置文件：
   ```bash
   # 设置环境
   export ENVIRONMENT=development
   ```

3. 重启服务

### 问题：JWT 验证失败

**原因**：密钥不匹配

**解决方案**：
1. 确保所有服务使用相同的 `JWT_SECRET`
2. 检查密钥长度（至少 32 字符）
3. 清除浏览器缓存和 cookies

### 问题：CORS 错误

**原因**：`CORS_ORIGINS` 配置不正确

**解决方案**：
1. 检查前端 URL 是否在允许列表中
2. 确保使用正确的协议（http/https）
3. 检查端口号是否匹配

## 迁移指南

### 从旧配置迁移

如果您有旧的 `.env` 文件：

1. **备份旧配置**：
   ```bash
   cp .env .env.backup
   ```

2. **识别需要迁移的变量**：
   ```bash
   grep -v "^#" .env.backup | grep -v "^$"
   ```

3. **更新新配置文件**：
   ```bash
   # 复制模板
   cp .env.example .env.development

   # 编辑并添加您的值
   nano .env.development
   ```

4. **验证新配置**：
   ```bash
   python scripts/check_env.py
   ```

5. **测试应用**：
   ```bash
   python src/api/main.py
   ```

## Docker 部署

### 使用 Docker Compose

```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    env_file:
      - .env.development
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
```

### 生产部署

```bash
# 加载生产配置
export $(cat .env.production | xargs)

# 启动服务
docker-compose -f docker-compose.prod.yml up -d
```

## 参考资源

- [Python-dotenv 文档](https://github.com/theskumar/python-dotenv)
- [Vite 环境变量](https://vitejs.dev/guide/env-and-mode.html)
- [PostgreSQL 环境变量](https://www.postgresql.org/docs/current/libpq-envars.html)
- [Redis 配置](https://redis.io/topics/config)

## 更新日志

- **2025-01-04**: 创建统一的环境配置管理方案
- 整合 11 个不同的 .env 文件
- 创建标准化的配置模板
- 添加详细的安全指南

## 支持

如有问题，请：
1. 检查本文档的故障排查部分
2. 查看 `.env.example` 中的注释
3. 联系系统管理员

---

**最后更新**: 2025-01-04
**维护者**: CBSC 开发团队

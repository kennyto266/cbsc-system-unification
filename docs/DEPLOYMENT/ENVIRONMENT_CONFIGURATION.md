# 環境配置指南

## 概述

本文檔詳細說明CBS-C策略管理系統在各種環境（開發、測試、生產）中的配置要求和最佳實踐。

## 環境類型

### 1. 開發環境 (Development)

用於本地開發和功能測試。

#### 配置文件
- `.env.dev` - 開發環境變量
- `docker-compose.dev.yml` - 開發環境Docker配置
- `config/development/` - 開發環境特定配置

#### 特點
- 使用本地數據庫和緩存
- 開啟調試模式
- 詳細的日誌輸出
- 熱重載支持
- 模擬外部服務

#### 示例配置

```bash
# .env.dev
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# 數據庫
DATABASE_URL=postgresql://dev:dev@localhost:5432/cbsc_dev
REDIS_URL=redis://localhost:6379/0

# 安全（開發用）
SECRET_KEY=dev-secret-key-not-for-production
JWT_SECRET=dev-jwt-secret

# 外部服務（模擬）
MOCK_EXTERNAL_APIS=true
FUTU_API_MOCK=true
```

### 2. 測試環境 (Testing)

用於自動化測試和QA驗證。

#### 配置文件
- `.env.test` - 測試環境變量
- `docker-compose.test.yml` - 測試環境Docker配置
- `config/testing/` - 測試環境特定配置

#### 特點
- 使用測試數據庫
- 隔離的測試數據
- 自動化測試執行
- 性能測試支持
- 模擬生產環境

#### 示例配置

```bash
# .env.test
ENVIRONMENT=testing
DEBUG=false
LOG_LEVEL=INFO

# 測試數據庫
DATABASE_URL=postgresql://test:test@localhost:5432/cbsc_test
REDIS_URL=redis://localhost:6379/1

# 測試配置
TESTING=true
TEST_DATABASE_URL=postgresql://test:test@localhost:5432/cbsc_test_temp
```

### 3. 預發布環境 (Staging)

用於生發布前的最終驗證。

#### 配置文件
- `.env.staging` - 預發布環境變量
- `docker-compose.staging.yml` - 預發布環境Docker配置
- `config/staging/` - 預發布環境特定配置

#### 特點
- 使用生產環境配置
- 真實數據（脫敏）
- 完整功能測試
- 性能基準測試
- 安全測試

#### 示例配置

```bash
# .env.staging
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO

# 數據庫（與生產相同的配置）
DATABASE_URL=postgresql://staging_user:password@staging-db:5432/cbsc_staging
REDIS_URL=redis://staging-redis:6379/0

# 外部服務（測試環境）
FUTU_API_URL=https://sandbox.futunn.com
ALPHA_VANTAGE_API_KEY=staging_api_key
```

### 4. 生產環境 (Production)

用於正式運行環境。

#### 配置文件
- `.env.prod` - 生產環境變量
- `docker-compose.prod.yml` - 生產環境Docker配置
- `config/production/` - 生產環境特定配置

#### 特點
- 高可用配置
- 性能優化
- 安全加固
- 監控告警
- 備份恢復

#### 示例配置

```bash
# .env.prod
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING

# 數據庫（高可用）
DATABASE_URL=postgresql://prod_user:strong_password@postgres-master:5432/cbsc_prod
DATABASE_REPLICA_URL=postgresql://prod_user:strong_password@postgres-replica:5432/cbsc_prod
REDIS_URL=redis://:redis_password@redis-master:6379/0
REDIS_SENTINEL_URL=redis://redis-sentinel:26379

# 安全配置
SECRET_KEY=generated-strong-secret-key
JWT_SECRET=generated-strong-jwt-secret
SSL_CERT_PATH=/etc/ssl/certs/cbsc.crt
SSL_KEY_PATH=/etc/ssl/private/cbsc.key

# 性能配置
MAX_WORKERS=8
WORKER_CONNECTIONS=1000
KEEPALIVE_TIMEOUT=65

# 監控配置
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
SENTRY_DSN=your-sentry-dsn
```

## 配置管理

### 配置文件結構

```
config/
├── base/                 # 基礎配置
│   ├── database.py
│   ├── cache.py
│   ├── logging.py
│   └── security.py
├── development/          # 開發環境覆蓋
│   ├── database.py
│   └── logging.py
├── testing/             # 測試環境覆蓋
│   └── database.py
├── staging/             # 預發布環境覆蓋
│   ├── database.py
│   └── security.py
└── production/          # 生產環境覆蓋
    ├── database.py
    ├── security.py
    └── performance.py
```

### 配置加載順序

1. 加載基礎配置 (`config/base/`)
2. 加載環境特定配置 (`config/{ENVIRONMENT}/`)
3. 加載環境變量覆蓋
4. 加載命令行參數覆蓋

### 配置示例

#### 數據庫配置 (`config/base/database.py`)

```python
from pydantic import BaseSettings

class DatabaseSettings(BaseSettings):
    host: str = "localhost"
    port: int = 5432
    database: str = "cbsc"
    username: str = "cbsc_user"
    password: str = "cbsc_password"
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600

    class Config:
        env_prefix = "DB_"
```

#### 環境特定覆蓋 (`config/production/database.py`)

```python
from ..base.database import DatabaseSettings

class ProductionDatabaseSettings(DatabaseSettings):
    pool_size: int = 50
    max_overflow: int = 100
    pool_timeout: int = 60
    pool_recycle: int = 1800
    ssl_mode: str = "require"
    statement_timeout: int = 30000
```

## 安全配置

### 1. 密鑰管理

#### 生成安全密鑰

```bash
# 生成256位密鑰
openssl rand -base64 32

# 生成JWT密鑰
openssl rand -base64 64

# 生成數據庫密碼
openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
```

#### 密鑰存儲

- 開發環境: 環境變量或 `.env` 文件
- 測試環境: 環境變量或配置服務
- 生產環境: 密鑰管理服務（如AWS Secrets Manager、HashiCorp Vault）

### 2. SSL/TLS配置

#### 開發環境

```bash
# 生成自簽名證書
openssl req -x509 -newkey rsa:4096 -keyout dev-key.pem -out dev-cert.pem -days 365 -nodes
```

#### 生產環境

```bash
# 使用Let's Encrypt
certbot certonly --standalone -d your-domain.com

# 或使用商業證書
# 將證書文件放置在安全位置
```

### 3. 網絡安全

#### 防火牆配置

```bash
# Ubuntu UFW
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw deny 5432/tcp   # PostgreSQL (外部)
sudo ufw deny 6379/tcp   # Redis (外部)
sudo ufw enable
```

#### Nginx安全配置

```nginx
# 安全頭
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

# 隱藏版本信息
server_tokens off;

# 限制請求大小
client_max_body_size 10M;

# 速率限制
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req zone=api burst=20 nodelay;
```

## 性能配置

### 1. 應用服務器

#### Uvicorn配置

```python
# config/production/performance.py
UVICORN_CONFIG = {
    "host": "0.0.0.0",
    "port": 8000,
    "workers": 8,  # CPU核心數 * 2 + 1
    "worker_class": "uvicorn.workers.UvicornWorker",
    "worker_connections": 1000,
    "max_requests": 1000,
    "max_requests_jitter": 100,
    "timeout": 120,
    "keepalive": 5,
    "preload_app": True,
    "access_log": True,
    "use_loglevel": "info",
}
```

#### Gunicorn配置

```python
# gunicorn.conf.py
import multiprocessing

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 120
keepalive = 5
preload_app = True
accesslog = "-"
errorlog = "-"
loglevel = "info"
```

### 2. 數據庫

#### PostgreSQL配置

```sql
-- postgresql.conf
# 內存配置
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# 連接配置
max_connections = 200
shared_preload_libraries = 'pg_stat_statements'

# 日誌配置
log_statement = 'mod'
log_min_duration_statement = 1000
log_checkpoints = on
log_connections = on
log_disconnections = on
```

#### 連接池配置

```python
# config/base/database.py
DATABASE_POOL_CONFIG = {
    "pool_size": 20,
    "max_overflow": 30,
    "pool_timeout": 30,
    "pool_recycle": 3600,
    "pool_pre_ping": True,
}
```

### 3. 緩存配置

#### Redis配置

```conf
# redis.conf
# 內存配置
maxmemory 2gb
maxmemory-policy allkeys-lru

# 持久化配置
save 900 1
save 300 10
save 60 10000

# 網絡配置
tcp-keepalive 300
timeout 0

# 安全配置
requirepass your_redis_password
```

## 監控配置

### 1. 應用監控

#### Prometheus指標

```python
# config/monitoring.py
from prometheus_client import Counter, Histogram, Gauge

# 定義指標
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_USERS = Gauge('active_users_total', 'Number of active users')
```

#### 健康檢查

```python
# config/health.py
HEALTH_CHECK_CONFIG = {
    "database": {
        "timeout": 5,
        "query": "SELECT 1",
    },
    "redis": {
        "timeout": 5,
        "command": "ping",
    },
    "external_apis": {
        "timeout": 10,
        "endpoints": [
            "https://api.futunn.com/health",
            "https://api.marketdata.com/health",
        ],
    },
}
```

### 2. 日誌配置

#### 結構化日誌

```python
# config/logging.py
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/app/logs/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "json",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console", "file"],
            "level": "INFO",
        },
    },
}
```

## 部署腳本

### 環境初始化腳本

```bash
#!/bin/bash
# scripts/init-env.sh

set -e

ENVIRONMENT=${1:-development}

echo "初始化 ${ENVIRONMENT} 環境..."

# 創建環境配置文件
cp .env.example .env.${ENVIRONMENT}

# 生成密鑰
if [ "${ENVIRONMENT}" = "production" ]; then
    echo "生成生產環境密鑰..."
    export SECRET_KEY=$(openssl rand -base64 32)
    export JWT_SECRET=$(openssl rand -base64 64)
else
    echo "使用開發環境密鑰..."
    export SECRET_KEY="dev-secret-key"
    export JWT_SECRET="dev-jwt-secret"
fi

# 更新環境配置
sed -i "s/SECRET_KEY=.*/SECRET_KEY=${SECRET_KEY}/" .env.${ENVIRONMENT}
sed -i "s/JWT_SECRET=.*/JWT_SECRET=${JWT_SECRET}/" .env.${ENVIRONMENT}

# 創建必要目錄
mkdir -p logs uploads static ssl

# 設置權限
chmod 755 logs uploads static
chmod 700 ssl

echo "環境初始化完成!"
```

### 部署腳本

```bash
#!/bin/bash
# scripts/deploy.sh

set -e

ENVIRONMENT=${1:-staging}
VERSION=${2:-latest}

echo "部署到 ${ENVIRONMENT} 環境，版本: ${VERSION}"

# 加載環境配置
source .env.${ENVIRONMENT}

# 備份當前版本（僅生產環境）
if [ "${ENVIRONMENT}" = "production" ]; then
    echo "備份當前版本..."
    ./scripts/backup.sh
fi

# 拉取新版本
docker pull cbsc/backend:${VERSION}
docker pull cbsc/frontend:${VERSION}

# 停止舊服務
docker-compose -f docker-compose.${ENVIRONMENT}.yml down

# 啟動新服務
docker-compose -f docker-compose.${ENVIRONMENT}.yml up -d

# 等待服務啟動
sleep 30

# 健康檢查
./scripts/health-check.sh

echo "部署完成!"
```

## 配置驗證

### 配置檢查清單

- [ ] 環境變量已正確設置
- [ ] 數據庫連接正常
- [ ] Redis連接正常
- [ ] SSL證書有效
- [ ] 防火牆規則正確
- [ ] 監控指標正常
- [ ] 日誌輸出正常
- [ ] 健康檢查通過
- [ ] 備份策略已配置
- [ ] 告警規則已配置

### 配置驗證腳本

```bash
#!/bin/bash
# scripts/validate-config.sh

echo "驗證配置..."

# 檢查環境變量
required_vars=("DATABASE_URL" "REDIS_URL" "SECRET_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "錯誤: 環境變量 ${var} 未設置"
        exit 1
    fi
done

# 檢查數據庫連接
if ! pg_isready -d "$DATABASE_URL"; then
    echo "錯誤: 數據庫連接失敗"
    exit 1
fi

# 檢查Redis連接
if ! redis-cli -u "$REDIS_URL" ping; then
    echo "錯誤: Redis連接失敗"
    exit 1
fi

echo "配置驗證通過!"
```

## 最佳實踐

1. **配置分離**: 將不同環境的配置分離管理
2. **敏感信息**: 使用專業的密鑰管理服務
3. **版本控制**: 配置文件納入版本控制（除敏感信息）
4. **自動化**: 使用自動化腳本進行環境初始化和部署
5. **監控**: 配置監控和告警，及時發現配置問題
6. **文檔**: 維護詳細的配置文檔和操作手冊
7. **測試**: 在預發布環境充分測試配置
8. **備份**: 定期備份配置文件和數據
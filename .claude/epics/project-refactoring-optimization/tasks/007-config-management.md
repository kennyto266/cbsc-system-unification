---
name: config-management
title: 配置管理中心化與環境管理統一
status: backlog
phase: 5
priority: P0
created: 2025-12-24T12:05:52Z
updated: 2025-12-24T12:16:04Z
estimated_hours: 32
assignee: TBD
dependencies: ["004-frontend-structure", "005-backend-consolidation"]
github:
  issue: 79
  url: https://github.com/kennyto266/cbsc-system-unification/issues/79
---

# Task 007: 配置管理中心化與環境管理統一

## 概述

統一分散的配置文件，建立中心化的配置管理系統，支持多環境部署和配置驗證。

## 詳細描述

### 當前配置問題

```
分散的配置文件:
.env
.env.dev
.env.full
.env.prod
frontend/src/services/config.ts
backend/config/api_config.py
backend/config/database.py
src/core/config.py
docker-compose.yml
docker-compose.prod.yml
docker-compose.*.yml (多個版本)
```

### 新配置結構

```
config/
├── environments/                # 環境配置
│   ├── base.yml               # 基礎配置
│   ├── development.yml         # 開發環境
│   ├── staging.yml             # 測試環境
│   └── production.yml          # 生產環境
├── services/                    # 服務配置
│   ├── frontend.yml            # 前端配置
│   ├── backend.yml             # 後端配置
│   ├── database.yml            # 數據庫配置
│   └── cache.yml               # 緩存配置
└── shared/                      # 共享配置
    ├── api.yml                 # API 配置
    ├── features.yml            # 功能開關
    └── security.yml            # 安全配置

# 簡化的環境變量文件
.env                    # 本地開發 (不提交)
.env.example            # 環境變量模板
```

### 配置文件實現

#### 1. 基礎配置 (base.yml)

```yaml
# config/environments/base.yml
application:
  name: "cbsc-trading"
  version: "2.0.0"
  environment: "${APP_ENV:development}"

server:
  host: "0.0.0.0"
  port: 8000
  workers: 4
  reload: false

logging:
  level: "INFO"
  format: "json"
  outputs:
    - type: "console"
      level: "INFO"
    - type: "file"
      path: "logs/app.log"
      level: "DEBUG"
```

#### 2. 開發環境 (development.yml)

```yaml
# config/environments/development.yml
extends: "base.yml"

application:
  environment: "development"
  debug: true

server:
  port: 3004
  reload: true
  cors_origins:
    - "http://localhost:3000"
    - "http://localhost:5173"

database:
  url: "postgresql://cbsc:password@localhost:5432/cbsc_dev"
  pool_size: 5
  echo_sql: true

cache:
  backend: "redis"
  url: "redis://localhost:6379/0"
  ttl: 3600

features:
  unified_frontend: false
  api_v2: true
  new_config: true

security:
  secret_key: "${SECRET_KEY:dev-secret-key-change-in-production}"
  access_token_expire_minutes: 30
  refresh_token_expire_days: 7
```

#### 3. 生產環境 (production.yml)

```yaml
# config/environments/production.yml
extends: "base.yml"

application:
  environment: "production"
  debug: false

server:
  port: 8000
  workers: 8
  cors_origins:
    - "${FRONTEND_URL}"

database:
  url: "${DATABASE_URL}"
  pool_size: 20
  max_overflow: 10
  echo_sql: false

cache:
  backend: "redis"
  url: "${REDIS_URL}"
  ttl: 7200

features:
  unified_frontend: true
  api_v2: true
  new_config: true

security:
  secret_key: "${SECRET_KEY}"
  access_token_expire_minutes: 15
  refresh_token_expire_days: 30
  rate_limit:
    enabled: true
    requests_per_minute: 60
```

### 配置加載器

#### Python 配置管理

```python
# backend/core/config.py
import os
from pathlib import Path
from typing import Any, Dict
import yaml
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    """Application settings with validation"""

    # Application
    app_name: str = Field(default="cbsc-trading")
    app_version: str = Field(default="2.0.0")
    environment: str = Field(default="development")
    debug: bool = Field(default=False)

    # Server
    server_host: str = Field(default="0.0.0.0")
    server_port: int = Field(default=8000)
    server_workers: int = Field(default=4)

    # Database
    database_url: str = Field(...)
    database_pool_size: int = Field(default=20)
    database_echo: bool = Field(default=False)

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")
    redis_ttl: int = Field(default=3600)

    # Security
    secret_key: str = Field(...)
    access_token_expire_minutes: int = Field(default=30)
    refresh_token_expire_days: int = Field(default=7)

    # CORS
    cors_origins: list[str] = Field(default=["http://localhost:3000"])

    # Features
    feature_unified_frontend: bool = Field(default=False)
    feature_api_v2: bool = Field(default=True)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @classmethod
    def load_from_yaml(cls, config_path: str) -> "Settings":
        """Load settings from YAML file"""
        config_file = Path(config_path)

        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        # Flatten nested dict for environment variable resolution
        flat_config: Dict[str, Any] = {}

        def flatten_dict(d: Dict[str, Any], prefix: str = ""):
            for key, value in d.items():
                new_key = f"{prefix}_{key}" if prefix else key
                if isinstance(value, dict):
                    flatten_dict(value, new_key)
                else:
                    # Resolve environment variables
                    if isinstance(value, str) and value.startswith("${"):
                        env_var = value[2:-1].split(":")[0]
                        default_value = value[2:-1].split(":")[1] if ":" in value else None
                        flat_config[new_key] = os.getenv(env_var, default_value)
                    else:
                        flat_config[new_key] = value

        flatten_dict(config_data)

        return cls(**flat_config)

# Global settings instance
def get_settings() -> Settings:
    """Get application settings based on environment"""
    env = os.getenv("APP_ENV", "development")
    config_path = f"config/environments/{env}.yml"

    if Path(config_path).exists():
        return Settings.load_from_yaml(config_path)

    # Fallback to environment variables
    return Settings()

settings = get_settings()
```

#### TypeScript 配置管理

```typescript
// frontend/src/config/index.ts
interface AppConfig {
  application: {
    name: string;
    version: string;
    environment: string;
  };
  api: {
    baseUrl: string;
    timeout: number;
  };
  websocket: {
    url: string;
    reconnectInterval: number;
  };
  features: {
    unifiedFrontend: boolean;
    apiV2: boolean;
  };
}

class ConfigManager {
  private config: AppConfig;

  constructor() {
    this.config = this.loadConfig();
  }

  private loadConfig(): AppConfig {
    const env = import.meta.env.MODE || 'development';

    // Default configuration
    const defaultConfig: AppConfig = {
      application: {
        name: 'cbsc-frontend',
        version: '2.0.0',
        environment: env,
      },
      api: {
        baseUrl: import.meta.env.VITE_API_URL || 'http://localhost:3004',
        timeout: 30000,
      },
      websocket: {
        url: import.meta.env.VITE_WS_URL || 'ws://localhost:3004',
        reconnectInterval: 5000,
      },
      features: {
        unifiedFrontend: import.meta.env.VITE_FEATURE_UNIFIED_FRONTEND === 'true',
        apiV2: import.meta.env.VITE_FEATURE_API_V2 !== 'false',
      },
    };

    // Load environment-specific overrides if available
    try {
      const envConfig = require(`./environments/${env}.json`);
      return this.mergeDeep(defaultConfig, envConfig);
    } catch {
      return defaultConfig;
    }
  }

  private mergeDeep(target: any, source: any): any {
    const output = { ...target };
    if (this.isObject(target) && this.isObject(source)) {
      Object.keys(source).forEach(key => {
        if (this.isObject(source[key])) {
          if (!(key in target)) {
            Object.assign(output, { [key]: source[key] });
          } else {
            output[key] = this.mergeDeep(target[key], source[key]);
          }
        } else {
          Object.assign(output, { [key]: source[key] });
        }
      });
    }
    return output;
  }

  private isObject(item: any): boolean {
    return item && typeof item === 'object' && !Array.isArray(item);
  }

  public get<K extends keyof AppConfig>(key: K): AppConfig[K] {
    return this.config[key];
  }

  public getAll(): AppConfig {
    return { ...this.config };
  }
}

// Export singleton instance
export const config = new ConfigManager();

// Convenience exports
export const API_BASE_URL = config.get('api').baseUrl;
export const WS_BASE_URL = config.get('websocket').url;
export const IS_DEV = import.meta.env.DEV;
export const IS_PROD = import.meta.env.PROD;
```

### 環境變量模板

```bash
# .env.example (提交到版本控制)
# Application
APP_ENV=development
SECRET_KEY=your-secret-key-here

# Frontend
VITE_API_URL=http://localhost:3004
VITE_WS_URL=ws://localhost:3004
VITE_FEATURE_UNIFIED_FRONTEND=false
VITE_FEATURE_API_V2=true

# Backend
DATABASE_URL=postgresql://user:password@localhost:5432/cbsc
REDIS_URL=redis://localhost:6379/0

# External Services
SENTRY_DSN=
ANALYTICS_ID=

# Feature Flags
FEATURE_UNIFIED_FRONTEND=false
FEATURE_API_V2=true
FEATURE_NEW_CONFIG=true
```

### Docker Compose 統一

```yaml
# docker-compose.yml (統一版本)
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:80"
    environment:
      - VITE_API_URL=http://backend:8000
      - VITE_WS_URL=ws://backend:8000
    env_file:
      - .env
    depends_on:
      - backend

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "3004:8000"
    environment:
      - APP_ENV=${APP_ENV:-development}
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - .env
    depends_on:
      - postgres
      - redis
    volumes:
      - ./config:/app/config:ro

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres}
      - POSTGRES_DB=${POSTGRES_DB:-cbsc}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

volumes:
  postgres_data:
  redis_data:
```

## 驗收標準

### 交付物

- [ ] **配置文件結構**
  - config/environments/
  - config/services/
  - config/shared/

- [ ] **配置管理器**
  - Python Settings 類
  - TypeScript Config 類
  - 配置驗證

- [ ] **環境變量**
  - .env.example
  - .env 文件文檔
  - .gitignore 更新

- [ ] **Docker 配置**
  - 統一的 docker-compose.yml
  - 環境特定覆蓋

### 質量門檻

- 配置文件統一
- 環境切換正常
- 敏感信息加密
- 配置驗證通過

## 依賴關係

### 前置任務
- Task 004: 前端結構統一
- Task 005: 後端 API 統一

### 後續任務
- Task 008: 測試與質量保證

## 執行步驟

1. **第 1-2 天: 配置結構設計**
   - 設計配置文件層次
   - 創建目錄結構
   - 編寫配置模板

2. **第 3-5 天: 配置管理器實現**
   - Python Settings 類
   - TypeScript Config 類
   - 配置驗證邏輯

3. **第 6-7 天: 環境配置**
   - 各環境配置文件
   - Docker Compose 統一
   - 環境變量文檔

## 風險與緩解

| 風險 | 緩解措施 |
|------|----------|
| 配置遺漏 | 配置驗證，默認值 |
| 敏感信息洩露 | 加密存儲，.gitignore |
| 環境切換錯誤 | 自動檢測，明確標識 |

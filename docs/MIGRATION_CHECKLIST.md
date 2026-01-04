# CBSC 交易系統遷移檢查清單

**創建日期**: 2025-12-24T12:26:09Z
**狀態**: 草案
**版本**: 1.0

---

## 1. 概述

本文檔提供 CBSC 交易系統重構的詳細遷移檢查清單，包括文件遷移、API 端點映射、配置變更和數據模型遷移。

---

## 2. 文件遷移檢查清單

### 2.1 後端文件遷移

#### 2.1.1 API 路由遷移 (backend/ → src/api/v2/)

| 源文件 | 目標位置 | 操作 | 狀態 |
|--------|----------|------|------|
| `backend/api/auth.py` | `src/api/v2/auth/routes.py` | 合併 | □ |
| `backend/api/backtest.py` | `src/api/v2/backtest/routes.py` | 合併 | □ |
| `backend/api/data.py` | `src/api/v2/data/routes.py` | 合併 | □ |
| `backend/api/market_data.py` | `src/api/v2/market-data/routes.py` | 合併 | □ |
| `backend/api/portfolio.py` | `src/api/v2/portfolio/routes.py` | 合併 | □ |
| `backend/api/strategies.py` | `src/api/v2/strategies/routes.py` | 合併 | □ |
| `backend/api/users.py` | `src/api/v2/users/routes.py` | 合併 | □ |
| `backend/api/webhooks.py` | `src/api/v2/webhooks/routes.py` | 合併 | □ |
| `backend/api/analysis.py` | `src/api/v2/analysis/routes.py` | 合併 | □ |
| `backend/api/persistent_context.py` | `persistent-context-storage/api/` | 保留 | □ |

#### 2.1.2 模型遷移 (backend/models/ → src/models/)

| 源文件 | 目標位置 | 操作 | 狀態 |
|--------|----------|------|------|
| `backend/models/auth.py` | `src/models/auth.py` | 合併 | □ |
| `backend/models/api_keys.py` | `src/models/api_keys.py` | 合併 | □ |
| `backend/models/webhooks.py` | `src/models/webhooks.py` | 合併 | □ |

#### 2.1.3 服務層遷移

| 源文件 | 目標位置 | 操作 | 狀態 |
|--------|----------|------|------|
| `backend/services/webhook_service.py` | `src/services/webhook_service.py` | 合併 | □ |

#### 2.1.4 工具層遷移

| 源文件 | 目標位置 | 操作 | 狀態 |
|--------|----------|------|------|
| `backend/utils/api_keys.py` | `src/utils/api_keys.py` | 合併 | □ |
| `backend/utils/auth.py` | `src/utils/auth.py` | 合併 | □ |

#### 2.1.5 中間件遷移

| 源文件 | 目標位置 | 操作 | 狀態 |
|--------|----------|------|------|
| `backend/middleware/rate_limit.py` | `src/api/middleware/rate_limit.py` | 移動 | □ |

#### 2.1.6 配置遷移

| 源文件 | 目標位置 | 操作 | 狀態 |
|--------|----------|------|------|
| `backend/config/api_config.py` | `src/config/api.py` | 合併 | □ |

#### 2.1.7 入口文件遷移

| 源文件 | 目標位置 | 操作 | 狀態 |
|--------|----------|------|------|
| `backend/main.py` | `src/api/main.py` | 合併 | □ |

---

### 2.2 棄用文件刪除清單

#### 2.2.1 階段 6 可刪除的文件

**在確認所有功能正常後**:

```bash
# 舊後端目錄
rm -rf backend/

# 舊策略工廠版本
rm -f src/strategies/factory.py
rm -f src/strategies/enhanced_factory.py

# 舊交易模組
rm -f src/trading/order_manager.py
rm -f src/trading/position_manager.py

# 舊 WebSocket 實現
rm -f src/websocket/websocket_server.py
rm -f src/websocket/enhanced_websocket_server.py
rm -f src/websocket/production_websocket_manager.py

# 舊認證實現
rm -f src/api/auth_endpoints.py
rm -f src/api/auth/auth_simple.py

# 舊回測 API
rm -f src/api/backtest_api.py

# 獨立儀表板項目
rm -rf unified-dashboard/

# 保留策略儀表板作為嵌入式組件
# frontend/strategy-dashboard/ → frontend/src/components/StrategyDashboard/
```

#### 2.2.2 備份確認

在刪除前確認:

```bash
# 1. 創建完整備份
git add -A
git commit -m "Backup before cleanup"
git tag pre-cleanup-$(date +%Y%m%d)

# 2. 推送到遠程
git push origin refactor/unified-backend
git push origin --tags

# 3. 創建壓縮備份
tar -czf backup-$(date +%Y%m%d).tar.gz \
    backend/ \
    unified-dashboard/ \
    src/strategies/factory.py \
    src/strategies/enhanced_factory.py \
    src/trading/order_manager.py \
    src/trading/position_manager.py

# 4. 驗證備份完整性
tar -tzf backup-$(date +%Y%m%d).tar.gz | wc -l
```

---

### 2.3 前端文件遷移

#### 2.3.1 組件遷移 (unified-dashboard/ → frontend/)

| 源文件 | 目標位置 | 操作 | 狀態 |
|--------|----------|------|------|
| `unified-dashboard/src/components/Dashboard/*` | `frontend/src/components/Dashboard/` | 合併 | □ |
| `unified-dashboard/src/components/Strategies/*` | `frontend/src/components/Strategies/` | 合併 | □ |
| `unified-dashboard/src/components/Shared/*` | `frontend/src/components/Shared/` | 合併 | □ |
| `unified-dashboard/src/hooks/*` | `frontend/src/hooks/` | 合併 | □ |
| `unified-dashboard/src/pages/*` | `frontend/src/pages/` | 合併 | □ |
| `unified-dashboard/src/store/*` | `frontend/src/store/slices/` | 合併 | □ |

#### 2.3.2 狀態管理遷移 (Zustand → Redux Toolkit)

| Zustand Store | Redux Slice | 操作 | 狀態 |
|---------------|-------------|------|------|
| `useApiData` | `apiSlice` | 重寫 | □ |
| `useWebSocket` | `websocketSlice` | 重寫 | □ |

---

## 3. API 端點映射表

### 3.1 認證 API

| 舊端點 | 新端點 | 方法 | 變更 | 狀態 |
|--------|--------|------|------|------|
| `POST /api/auth/login` | `POST /api/v2/auth/login` | POST | 路徑更新 | □ |
| `POST /api/auth/register` | `POST /api/v2/auth/register` | POST | 路徑更新 | □ |
| `POST /api/auth/logout` | `POST /api/v2/auth/logout` | POST | 路徑更新 | □ |
| `POST /api/auth/refresh` | `POST /api/v2/auth/refresh` | POST | 路徑更新 | □ |
| `GET /api/auth/me` | `GET /api/v2/auth/me` | GET | 路徑更新 | □ |
| `PUT /api/auth/password` | `PUT /api/v2/auth/password` | PUT | 路徑更新 | □ |
| `POST /api/auth/mfa/enable` | `POST /api/v2/auth/mfa/enable` | POST | 路徑更新 | □ |
| `POST /api/auth/mfa/verify` | `POST /api/v2/auth/mfa/verify` | POST | 路徑更新 | □ |

**請求/響應變更**:

```typescript
// 舊格式
{
  "username": "user",
  "password": "pass"
}

// 新格式 (保持兼容)
{
  "username": "user",
  "password": "pass",
  "mfa_code": "123456"  // 新增可選字段
}
```

### 3.2 策略 API

| 舊端點 | 新端點 | 方法 | 變更 | 狀態 |
|--------|--------|------|------|------|
| `GET /api/strategies` | `GET /api/v2/strategies` | GET | 路徑更新 | □ |
| `POST /api/strategies` | `POST /api/v2/strategies` | POST | 路徑更新 | □ |
| `GET /api/strategies/{id}` | `GET /api/v2/strategies/{id}` | GET | 路徑更新 | □ |
| `PUT /api/strategies/{id}` | `PUT /api/v2/strategies/{id}` | PUT | 路徑更新 | □ |
| `DELETE /api/strategies/{id}` | `DELETE /api/v2/strategies/{id}` | DELETE | 路徑更新 | □ |
| `POST /api/strategies/{id}/activate` | `POST /api/v2/strategies/{id}/activate` | POST | 路徑更新 | □ |
| `POST /api/strategies/{id}/deactivate` | `POST /api/v2/strategies/{id}/deactivate` | POST | 路徑更新 | □ |
| `GET /api/strategies/v2/` | `GET /api/v2/strategies` | GET | 重複路徑 | □ |

**分頁參數變更**:

```typescript
// 舊格式
GET /api/strategies?limit=20&offset=0

// 新格式 (推薦)
GET /api/v2/strategies?page=1&page_size=20

// 兼容舊格式
GET /api/v2/strategies?limit=20&offset=0  // 自動轉換
```

### 3.3 回測 API

| 舊端點 | 新端點 | 方法 | 變更 | 狀態 |
|--------|--------|------|------|------|
| `POST /api/backtest` | `POST /api/v2/backtests` | POST | 路徑+複數 | □ |
| `GET /api/backtest/{id}` | `GET /api/v2/backtests/{id}` | GET | 路徑+複數 | □ |
| `GET /api/backtest` | `GET /api/v2/backtests` | GET | 路徑+複數 | □ |
| `DELETE /api/backtest/{id}` | `DELETE /api/v2/backtests/{id}` | DELETE | 路徑+複數 | □ |
| `POST /api/vectorbt/backtest` | `POST /api/v2/backtests/vectorbt` | POST | 路徑更新 | □ |
| `GET /api/backtest/v2/*` | `GET /api/v2/backtests/*` | GET | 重複路徑 | □ |

**請求體變更**:

```typescript
// 舊格式
{
  "strategy_id": 1,
  "start_date": "2024-01-01",
  "end_date": "2024-12-31"
}

// 新格式 (增強驗證)
{
  "strategy_id": 1,
  "config": {
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "initial_capital": 100000,
    "commission": 0.001
  },
  "options": {
    "parallel": true,
    "monte_carlo": true,
    "risk_metrics": true
  }
}
```

### 3.4 數據 API

| 舊端點 | 新端點 | 方法 | 變更 | 狀態 |
|--------|--------|------|------|------|
| `GET /api/data` | `GET /api/v2/market-data` | GET | 重命名 | □ |
| `GET /api/data/{symbol}` | `GET /api/v2/market-data/{symbol}` | GET | 重命名 | □ |
| `GET /api/market-data` | `GET /api/v2/market-data` | GET | 路徑更新 | □ |
| `POST /api/data/economic` | `POST /api/v2/economic-data` | POST | 路徑更新 | □ |
| `GET /api/data/historical` | `GET /api/v2/market-data/historical` | GET | 路徑更新 | □ |

### 3.5 投資組合 API

| 舊端點 | 新端點 | 方法 | 變更 | 狀態 |
|--------|--------|------|------|------|
| `GET /api/portfolio` | `GET /api/v2/portfolio` | GET | 路徑更新 | □ |
| `POST /api/portfolio` | `POST /api/v2/portfolio` | POST | 路徑更新 | □ |
| `GET /api/portfolio/{id}` | `GET /api/v2/portfolio/{id}` | GET | 路徑更新 | □ |
| `PUT /api/portfolio/{id}` | `PUT /api/v2/portfolio/{id}` | PUT | 路徑更新 | □ |

### 3.6 用戶 API

| 舊端點 | 新端點 | 方法 | 變更 | 狀態 |
|--------|--------|------|------|------|
| `GET /api/users` | `GET /api/v2/users` | GET | 路徑更新 | □ |
| `POST /api/users` | `POST /api/v2/users` | POST | 路徑更新 | □ |
| `GET /api/users/{id}` | `GET /api/v2/users/{id}` | GET | 路徑更新 | □ |
| `PUT /api/users/{id}` | `PUT /api/v2/users/{id}` | PUT | 路徑更新 | □ |
| `DELETE /api/users/{id}` | `DELETE /api/v2/users/{id}` | DELETE | 路徑更新 | □ |
| `GET /api/users/v2/*` | `GET /api/v2/users/*` | GET | 重複路徑 | □ |

### 3.7 WebSocket API

| 舊端點 | 新端點 | 變更 | 狀態 |
|--------|--------|------|------|
| `ws://localhost:3004/ws` | `ws://localhost:3004/api/v2/ws` | 路徑更新 | □ |
| `ws://localhost:3005/ws` | `ws://localhost:3004/api/v2/ws` | 統一端口 | □ |

**連接參數變更**:

```typescript
// 舊格式
const ws = new WebSocket('ws://localhost:3004/ws');

// 新格式 (支持更多選項)
const ws = new WebSocket('ws://localhost:3004/api/v2/ws?token=xxx&channels=strategies,backtests');

// 支持的消息類型
type WSMessage =
  | { type: 'subscribe'; channels: string[] }
  | { type: 'unsubscribe'; channels: string[] }
  | { type: 'ping' }
  | { type: 'data'; payload: any };
```

### 3.8 Webhook API

| 舊端點 | 新端點 | 方法 | 變更 | 狀態 |
|--------|--------|------|------|------|
| `POST /api/webhooks` | `POST /api/v2/webhooks` | POST | 路徑更新 | □ |
| `GET /api/webhooks` | `GET /api/v2/webhooks` | GET | 路徑更新 | □ |
| `DELETE /api/webhooks/{id}` | `DELETE /api/v2/webhooks/{id}` | DELETE | 路徑更新 | □ |
| `POST /api/webhooks/{id}/test` | `POST /api/v2/webhooks/{id}/test` | POST | 路徑更新 | □ |

---

## 4. 配置變更對照

### 4.1 環境變量映射

#### 4.1.1 數據庫配置

| 舊變量 | 新變量 | 默認值 | 說明 |
|--------|--------|--------|------|
| `DATABASE_URL` | `DB_URL` | `postgresql://localhost:5432/cbsc` | 統一命名 |
| `POSTGRES_HOST` | `DB_HOST` | `localhost` | 主機地址 |
| `POSTGRES_PORT` | `DB_PORT` | `5432` | 端口 |
| `POSTGRES_USER` | `DB_USER` | `cbsc` | 用戶名 |
| `POSTGRES_PASSWORD` | `DB_PASSWORD` | - | 密碼 |
| `POSTGRES_DB` | `DB_NAME` | `cbsc` | 數據庫名 |

#### 4.1.2 Redis 配置

| 舊變量 | 新變量 | 默認值 | 說明 |
|--------|--------|--------|------|
| `REDIS_URL` | `REDIS_URL` | `redis://localhost:6379/0` | 保持不變 |
| `REDIS_HOST` | `REDIS_HOST` | `localhost` | 主機地址 |
| `REDIS_PORT` | `REDIS_PORT` | `6379` | 端口 |
| `REDIS_DB` | `REDIS_DB` | `0` | 數據庫索引 |

#### 4.1.3 API 配置

| 舊變量 | 新變量 | 默認值 | 說明 |
|--------|--------|--------|------|
| `API_PORT` | `API_PORT` | `3004` | 統一端口 |
| `API_HOST` | `API_HOST` | `0.0.0.0` | 監聽地址 |
| `API_V1_PORT` | - | `3003` | 棄用 |
| `API_WORKERS` | `API_WORKERS` | `4` | 工作進程數 |

#### 4.1.4 認證配置

| 舊變量 | 新變量 | 默認值 | 說明 |
|--------|--------|--------|------|
| `JWT_SECRET` | `AUTH_JWT_SECRET` | - | JWT 密鑰 |
| `JWT_ALGORITHM` | `AUTH_JWT_ALGORITHM` | `HS256` | 加密算法 |
| `JWT_EXPIRATION` | `AUTH_ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | 過期時間(分鐘) |
| `REFRESH_EXPIRATION` | `AUTH_REFRESH_TOKEN_EXPIRE_DAYS` | `7` | 刷新令牌過期(天) |

#### 4.1.5 CORS 配置

| 舊變量 | 新變量 | 默認值 | 說明 |
|--------|--------|--------|------|
| `CORS_ORIGINS` | `CORS_ALLOWED_ORIGINS` | `*` | 允許的來源 |
| `CORS_CREDENTIALS` | `CORS_ALLOW_CREDENTIALS` | `true` | 允許憑證 |

#### 4.1.6 日誌配置

| 舊變量 | 新變量 | 默認值 | 說明 |
|--------|--------|--------|------|
| `LOG_LEVEL` | `LOG_LEVEL` | `INFO` | 日誌級別 |
| `LOG_FORMAT` | `LOG_FORMAT` | `json` | 日誌格式 |
| `LOG_FILE` | `LOG_FILE_PATH` | `logs/app.log` | 日誌文件 |

### 4.2 配置文件對比

#### 4.2.1 docker-compose.yml

**舊版 (需要兩個服務)**:

```yaml
version: '3.8'
services:
  backend-old:
    build: ./backend
    ports:
      - "3003:3003"
    environment:
      - PORT=3003

  backend-new:
    build: ./backend
    ports:
      - "3004:3004"
    environment:
      - PORT=3004
```

**新版 (單一服務)**:

```yaml
version: '3.8'
services:
  api:
    build: ./src/api
    ports:
      - "3004:3004"
    environment:
      - API_PORT=3004
      - DB_HOST=postgres
      - REDIS_HOST=redis
    depends_on:
      - postgres
      - redis
```

#### 4.2.2 Vite 配置

**舊版**:

```javascript
// frontend/vite.config.ts
export default {
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:3004',
        changeOrigin: true
      },
      '/legacy-api': {
        target: 'http://localhost:3003',
        changeOrigin: true
      }
    }
  }
}
```

**新版**:

```javascript
// frontend/vite.config.ts
export default {
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:3004',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api/v2')
      }
    }
  }
}
```

### 4.3 配置遷移腳本

```bash
#!/bin/bash
# scripts/migrate-config.sh

echo "開始配置遷移..."

# 1. 備份現有配置
cp .env .env.backup-$(date +%Y%m%d)

# 2. 創建新配置
cat > .env.new << 'EOF'
# CBSC Trading System - Unified Configuration

# Database
DB_URL=postgresql://localhost:5432/cbsc
DB_HOST=localhost
DB_PORT=5432
DB_USER=cbsc
DB_PASSWORD=your_password_here
DB_NAME=cbsc

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# API
API_PORT=3004
API_HOST=0.0.0.0
API_WORKERS=4

# Authentication
AUTH_JWT_SECRET=your_secret_key_here
AUTH_JWT_ALGORITHM=HS256
AUTH_ACCESS_TOKEN_EXPIRE_MINUTES=30
AUTH_REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ALLOWED_ORIGINS=*
CORS_ALLOW_CREDENTIALS=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE_PATH=logs/app.log

# Feature Flags
FEATURE_NEW_STRATEGY_UI=true
FEATURE_V2_BACKTEST=true
EOF

# 3. 遷移舊值
echo "遷移環境變量..."
while IFS='=' read -r key value; do
    # 跳過註釋和空行
    [[ $key =~ ^#.*$ ]] && continue
    [[ -z $key ]] && continue

    # 映射舊變量到新變量
    case $key in
        DATABASE_URL)
            sed -i "s|DB_URL=.*|DB_URL=$value|" .env.new
            ;;
        REDIS_URL)
            sed -i "s|REDIS_URL=.*|REDIS_URL=$value|" .env.new
            ;;
        JWT_SECRET)
            sed -i "s|AUTH_JWT_SECRET=.*|AUTH_JWT_SECRET=$value|" .env.new
            ;;
        # 添加更多映射...
    esac
done < .env

# 4. 應用新配置
echo "應用新配置..."
mv .env .env.old
mv .env.new .env

echo "配置遷移完成！"
echo "請檢查 .env 文件並更新敏感信息。"
```

---

## 5. 數據模型遷移

### 5.1 數據庫遷移腳本

#### 5.1.1 創建統一用戶表

```sql
-- migrations/001_unified_users.sql

-- 1. 創建新表（如果不存在）
CREATE TABLE IF NOT EXISTS users_v2 (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 2. 遷移數據
INSERT INTO users_v2 (id, username, email, password_hash, is_active, email_verified, created_at, updated_at)
SELECT
    id,
    username,
    email,
    password_hash,
    COALESCE(is_active, TRUE),
    COALESCE(email_verified, FALSE),
    COALESCE(created_at, NOW()),
    COALESCE(updated_at, NOW())
FROM users
ON CONFLICT (id) DO UPDATE SET
    username = EXCLUDED.username,
    email = EXCLUDED.email,
    password_hash = EXCLUDED.password_hash,
    is_active = EXCLUDED.is_active,
    email_verified = EXCLUDED.email_verified;

-- 3. 驗證遷移
DO $$
DECLARE
    old_count INTEGER;
    new_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO old_count FROM users;
    SELECT COUNT(*) INTO new_count FROM users_v2;

    IF old_count != new_count THEN
        RAISE EXCEPTION '遷移驗證失敗: 舊表 % 行，新表 % 行', old_count, new_count;
    END IF;

    RAISE NOTICE '遷移驗證成功: % 行', new_count;
END $$;

-- 4. 重命名表（在確認成功後）
-- ALTER TABLE users RENAME TO users_old;
-- ALTER TABLE users_v2 RENAME TO users;
```

#### 5.1.2 策略表遷移

```sql
-- migrations/002_unified_strategies.sql

-- 統一策略表結構
CREATE TABLE IF NOT EXISTS strategies_v2 (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type VARCHAR(50) NOT NULL,  -- 'momentum', 'fundamental', 'volume', 'technical'
    config JSONB NOT NULL,
    parameters JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_user_id (user_id),
    INDEX idx_type (type),
    INDEX idx_is_active (is_active)
);

-- 遷移策略數據
INSERT INTO strategies_v2 (user_id, name, description, type, config, parameters, is_active, created_at, updated_at)
SELECT
    user_id,
    name,
    description,
    type,
    config::jsonb,
    parameters::jsonb,
    is_active,
    created_at,
    updated_at
FROM strategies
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    config = EXCLUDED.config;
```

#### 5.1.3 回測結果表遷移

```sql
-- migrations/003_unified_backtests.sql

CREATE TABLE IF NOT EXISTS backtests_v2 (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    strategy_id INTEGER REFERENCES strategies(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    config JSONB NOT NULL,
    results JSONB,
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'running', 'completed', 'failed'
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_user_id (user_id),
    INDEX idx_strategy_id (strategy_id),
    INDEX idx_status (status)
);
```

### 5.2 數據驗證檢查清單

在每次遷移後執行:

```bash
#!/bin/bash
# scripts/validate-migration.sh

echo "驗證數據遷移..."

# 1. 檢查表行數
echo "檢查表行數..."
psql -d cbsc -c "
SELECT
    schemaname,
    tablename,
    n_tup_ins AS inserts,
    n_tup_upd AS updates,
    n_tup_del AS deletes,
    n_live_tup AS live_rows,
    n_dead_tup AS dead_rows
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY live_rows DESC;
"

# 2. 檢查外鍵約束
echo "檢查外鍵約束..."
psql -d cbsc -c "
SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY';
"

# 3. 檢查索引
echo "檢查索引..."
psql -d cbsc -c "
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
"

# 4. 數據完整性檢查
echo "檢查數據完整性..."
psql -d cbsc -c "
-- 檢查孤立記錄
SELECT 'strategies without users' AS check_type, COUNT(*) AS count
FROM strategies s
LEFT JOIN users u ON s.user_id = u.id
WHERE u.id IS NULL

UNION ALL

SELECT 'backtests without users', COUNT(*)
FROM backtests b
LEFT JOIN users u ON b.user_id = u.id
WHERE u.id IS NULL;
"

echo "驗證完成！"
```

### 5.3 回滾腳本

```sql
-- migrations/rollback_001_unified_users.sql

-- 回滾用戶表遷移
DROP TABLE IF EXISTS users_v2;

-- 或者如果已經重命名
-- ALTER TABLE users RENAME TO users_v2;
-- ALTER TABLE users_old RENAME TO users;
```

---

## 6. 前端遷移檢查清單

### 6.1 API 客戶端更新

#### 6.1.1 更新 API 基礎 URL

```typescript
// frontend/src/services/config.ts

// 舊配置
export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:3004/api';

// 新配置
export const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:3004/api/v2';
export const LEGACY_API_BASE_URL = process.env.VITE_LEGACY_API_URL || 'http://localhost:3004/api/v1';
```

#### 6.1.2 更新 API 調用

```typescript
// frontend/src/services/api/strategies.ts

// 舊方式
export const getStrategies = async () => {
  const response = await fetch('/api/strategies');
  return response.json();
};

// 新方式 (使用統一客戶端)
import apiClient from '../apiClient';

export const getStrategies = async (params?: PaginationParams) => {
  return apiClient.get('/strategies', { params });
};

// 使用 TypeScript 類型
export const getStrategies = async (params: PaginationParams = {}): Promise<StrategyListResponse> => {
  const response = await apiClient.get<StrategyListResponse>('/strategies', { params });
  return response.data;
};
```

### 6.2 組件遷移檢查

| 組件 | 依賴檢查 | API 調用更新 | 狀態管理遷移 | 測試更新 | 狀態 |
|------|----------|--------------|--------------|----------|------|
| Dashboard | □ | □ | □ | □ | □ |
| StrategyList | □ | □ | □ | □ | □ |
| BacktestForm | □ | □ | □ | □ | □ |
| PerformanceChart | □ | □ | □ | □ | □ |
| Login | □ | □ | □ | □ | □ |

### 6.3 路由更新

```typescript
// frontend/src/router/index.tsx

// 舊路由
const routes = [
  { path: '/dashboard', component: Dashboard },
  { path: '/strategies', component: Strategies },
  { path: '/backtest', component: Backtest }
];

// 新路由 (添加版本前綴)
const routes = [
  {
    path: '/dashboard',
    component: Dashboard,
    apiVersion: 'v2'  // 標記使用的 API 版本
  },
  {
    path: '/strategies',
    component: Strategies,
    apiVersion: 'v2'
  }
];
```

---

## 7. 測試檢查清單

### 7.1 API 測試更新

```typescript
// frontend/src/services/__tests__/strategies.test.ts

// 舊測試
describe('Strategy API', () => {
  test('should fetch strategies', async () => {
    const response = await fetch('/api/strategies');
    const data = await response.json();
    expect(data).toHaveLength(10);
  });
});

// 新測試 (使用 MSW)
import { rest } from 'msw';
import { setupServer } from 'msw/node';

const server = setupServer(
  rest.get('/api/v2/strategies', (req, res, ctx) => {
    return res(
      ctx.json({
        success: true,
        data: { items: [], total: 0 }
      })
    );
  })
);

describe('Strategy API v2', () => {
  beforeAll(() => server.listen());
  afterEach(() => server.resetHandlers());
  afterAll(() => server.close());

  test('should fetch strategies with v2 API', async () => {
    const response = await getStrategies();
    expect(response.success).toBe(true);
    expect(response.data.items).toEqual([]);
  });
});
```

### 7.2 集成測試檢查

```bash
# scripts/test-integration.sh

#!/bin/bash

echo "運行集成測試..."

# 1. 啟動測試環境
docker-compose -f docker-compose.test.yml up -d

# 2. 運行數據庫遷移
alembic upgrade head

# 3. 運行後端測試
pytest tests/integration/ -v --cov=src

# 4. 運行前端測試
cd frontend
npm run test:integration

# 5. 清理
docker-compose -f docker-compose.test.yml down

echo "集成測試完成！"
```

---

## 8. 部署檢查清單

### 8.1 部署前檢查

- [ ] 所有測試通過 (單元、集成、E2E)
- [ ] 代碼審查完成
- [ ] 性能測試通過
- [ ] 安全掃描通過
- [ ] 文檔更新完成
- [ ] 回滾腳本就緒
- [ ] 監控配置就緒
- [ ] 數據庫備份完成

### 8.2 部署步驟

```bash
#!/bin/bash
# scripts/deploy.sh

set -e

ENVIRONMENT=${1:-staging}
VERSION=$(git describe --tags --always)

echo "部署 $VERSION 到 $ENVIRONMENT..."

# 1. 構建 Docker 鏡像
docker build -t cbsc-api:$VERSION -f docker/Dockerfile .

# 2. 推送到倉庫
docker tag cbsc-api:$VERSION registry.example.com/cbsc-api:$VERSION
docker push registry.example.com/cbsc-api:$VERSION

# 3. 部署到 Kubernetes
kubectl set image deployment/cbsc-api \
    cbsc-api=registry.example.com/cbsc-api:$VERSION \
    -n $ENVIRONMENT

# 4. 等待滾動更新完成
kubectl rollout status deployment/cbsc-api -n $ENVIRONMENT

# 5. 運行冒煙測試
./scripts/smoke-test.sh https://api.$ENVIRONMENT.example.com

echo "部署完成！"
```

### 8.3 部署後驗證

```bash
#!/bin/bash
# scripts/post-deploy-check.sh

echo "部署後驗證..."

# 1. 檢查服務健康
curl -f http://localhost:3004/health || exit 1

# 2. 檢查 API 版本
VERSION=$(curl -s http://localhost:3004/api/v2/version | jq -r '.version')
echo "API 版本: $VERSION"

# 3. 檢查數據庫連接
DB_STATUS=$(curl -s http://localhost:3004/health | jq -r '.database')
if [ "$DB_STATUS" != "healthy" ]; then
    echo "❌ 數據庫連接失敗"
    exit 1
fi

# 4. 檢查關鍵端點
ENDPOINTS=(
    "/api/v2/strategies"
    "/api/v2/auth/health"
    "/api/v2/backtests"
)

for endpoint in "${ENDPOINTS[@]}"; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3004$endpoint)
    if [ "$STATUS" != "200" ]; then
        echo "❌ 端點 $endpoint 返回 $STATUS"
        exit 1
    fi
done

echo "✅ 所有檢查通過！"
```

---

## 9. 回滾檢查清單

詳細回滾程序請參考 `ROLLBACK_PROCEDURE.md`。

快速檢查:

```bash
# 回滾檢查清單
- [ ] 確認回滾觸發條件
- [ ] 執行回滾腳本
- [ ] 驗證服務恢復
- [ ] 驗證數據完整性
- [ ] 通知團隊
- [ ] 創建事故報告
```

---

## 10. 附錄

### 10.1 快速參考命令

```bash
# 查找所有舊 API 引用
grep -r "localhost:3003" src/ frontend/

# 查找所有 v1 API 調用
grep -r "/api/v1/" frontend/src/

# 批量替換 API 端點
find frontend/src -name "*.ts" -exec sed -i 's|/api/strategies|/api/v2/strategies|g' {} \;

# 運行所有測試
pytest tests/ -v && cd frontend && npm test

# 數據庫遷移
alembic upgrade head

# 回滾最後一個遷移
alembic downgrade -1
```

### 10.2 遷移日誌模板

```markdown
## 遷移日誌 - [日期]

### 完成任務
- [x] 任務1
- [x] 任務2

### 遇到的問題
1. 問題描述
   - 解決方案

### 明日計劃
- [ ] 任務3
- [ ] 任務4

### 阻塞問題
- 無 / 描述
```

---

**文檔版本**: 1.0
**最後更新**: 2025-12-24T12:26:09Z
**下次審視**: 每週一

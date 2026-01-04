# Task #006: 依賴分析報告

**生成時間**: 2025-12-25T02:00:00Z
**任務狀態**: 🟢 in_progress
**範圍**: 前端 + 後端依賴分析

---

## 📊 當前依賴狀態

### 前端依賴 (frontend/package.json)

#### 數量統計
```
dependencies:      54 個包
devDependencies:   43 個包
總計:              97 個包
```

#### 依賴分類

| 類別 | 包名稱 | 數量 | 狀態 |
|------|--------|------|------|
| **UI 組件庫** | antd, @headlessui/react, framer-motion | 3 | ⚠️ 多個UI庫並存 |
| **圖表庫** | chart.js, plotly.js, recharts, @ant-design/plots | 4 | ⚠️ 功能重疊 |
| **狀態管理** | @reduxjs/toolkit, @tanstack/react-query | 2 | ⚠️ 功能重疊 |
| **路由** | react-router-dom | 1 | ✅ 單一 |
| **樣式** | styled-components, tailwindcss | 2 | ⚠️ 重複 |
| **手勢** | @use-gesture/react, react-use-gesture | 2 | ❌ 重複 |
| **拖拽** | react-dnd, react-rnd, react-grid-layout | 3 | ⚠️ 功能重疊 |
| **通知** | react-toastify | 1 | ✅ |
| **HTTP** | axios | 1 | ✅ |
| **WebSocket** | socket.io-client | 1 | ✅ |
| **工具** | lodash, date-fns, dompurify, uuid | 4 | ✅ |

#### 發現的問題

1. **重複的 UI 組件庫** (3個)
   - `antd` - Ant Design 組件庫
   - `@headlessui/react` - Tailwind UI 組件
   - `framer-motion` - 動畫庫

2. **重複的圖表庫** (4個)
   - `chart.js` + `react-chartjs-2`
   - `plotly.js` + `react-plotly.js`
   - `recharts`
   - `@ant-design/plots`

3. **重複的手勢庫** (2個)
   - `@use-gesture/react`
   - `react-use-gesture`

4. **重複的拖拽庫** (3個)
   - `react-dnd`
   - `react-rnd`
   - `react-grid-layout`

5. **重複的樣式方案** (2個)
   - `styled-components`
   - `tailwindcss`

---

### 後端依賴 (src/requirements.txt)

#### 數量統計
```
生產依賴:    42 個包
開發依賴:    0 個包 (混在一起)
總計:        42 個包
```

#### 依賴分類

| 類別 | 包名稱 | 數量 | 狀態 |
|------|--------|------|------|
| **Web 框架** | fastapi, uvicorn | 2 | ✅ 單一 |
| **數據庫** | sqlalchemy, alembic, asyncpg, psycopg2-binary | 4 | ✅ 標準 |
| **Redis** | redis, aioredis | 2 | ❌ 功能重疊 |
| **認證** | python-jose, passlib | 2 | ✅ 標準 |
| **數據處理** | pandas, numpy, scipy | 3 | ✅ 標準 |
| **HTTP** | httpx, aiohttp | 2 | ⚠️ 功能重疊 |
| **後台任務** | celery, flower | 2 | ✅ 標準 |
| **配置** | pydantic, pydantic-settings | 2 | ✅ 相關 |
| **日誌** | structlog, prometheus-client | 2 | ✅ 標準 |

#### 發現的問題

1. **Redis 客戶端重複** (2個)
   - `redis==5.0.1`
   - `aioredis==2.0.1`
   - **問題**: aioredis 已被棄用，功能合併到 redis

2. **HTTP 客戶端重複** (2個)
   - `httpx==0.25.2`
   - `aiohttp==3.9.1`
   - **問題**: 功能重疊，httpx 更現代化

3. **開發依賴未分離**
   - 測試工具混在生產依賴中
   - 應該使用 `requirements-dev.txt`

---

## 🔍 循環依賴分析

### 已識別的循環依賴

```
1. frontend → backend/src 循環
   frontend/src/api/ → backend/api/
   frontend/src/api/ → src/api/
   src/strategies/ → backend/api/

2. 模型層循環
   backend/models/ → src/models/
   src/models/ → backend/models/

3. 服務層循環
   backend/services/ → src/services/
   src/services/ → backend/services/
```

---

## 💡 優化建議

### 前端優化

#### 1. 移除重複的 UI 組件庫
```diff
- antd (保留)
- @headlessui/react (移除 - 使用 antd 對應組件)
- framer-motion (保留 - 動畫功能)
```

#### 2. 統一圖表庫
```diff
- chart.js + react-chartjs-2 (保留 - 主要圖表)
- plotly.js + react-plotly.js (保留 - 3D/交互圖表)
- recharts (移除 - 使用 chart.js 替代)
- @ant-design/plots (移除 - 使用 chart.js 替代)
```

#### 3. 統一手勢庫
```diff
- @use-gesture/react (保留 - 更現代)
- react-use-gesture (移除 - 已棄用)
```

#### 4. 統一拖拽庫
```diff
- react-dnd (保留 - 主要拖拽)
- react-rnd (移除 - 使用 react-dnd 替代)
- react-grid-layout (保留 - 佈局功能)
```

#### 5. 統一樣式方案
```diff
- tailwindcss (保留 - 主要樣式)
- styled-components (移除 - 使用 tailwind 替代)
```

**預計節省**:
- 包數量: 97 → 75 (-22 個包)
- node_modules: ~350MB → ~280MB (-70MB)
- 構建時間: 減少 15-20%

---

### 後端優化

#### 1. 移除棄用的 Redis 客戶端
```diff
- redis==5.0.1 (保留)
- aioredis==2.0.1 (移除 - 已棄用)
```

#### 2. 統一 HTTP 客戶端
```diff
- httpx (保留 - 更現代化，支持 HTTP/2)
- aiohttp (移除 - 使用 httpx 替代)
```

#### 3. 分離開發依賴
```bash
# requirements-dev.txt
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
black==23.11.0
isort==5.12.0
flake8==6.1.0
mypy==1.7.1
```

**預計節省**:
- 包數量: 42 → 38 (-4 個包)
- 安裝時間: 減少 10-15%
- 減少安全漏洞風險

---

## 🎯 依賴注入架構設計

### 分層架構

```
┌─────────────────────────────────────┐
│         Frontend Layer              │
│  (React Components + Hooks)         │
└─────────────┬───────────────────────┘
              │ HTTP/WebSocket
              ▼
┌─────────────────────────────────────┐
│         API Layer                   │
│  (FastAPI Routes + Middleware)      │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│      Service Layer (DI Container)   │
│  ├─ AuthService                    │
│  ├─ StrategyService                 │
│  ├─ BacktestService                 │
│  └─ DataService                     │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│      Repository Layer               │
│  ├─ DatabaseRepository               │
│  ├─ CacheRepository                 │
│  └─ EventBusRepository              │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│      Data Layer                     │
│  ├─ PostgreSQL                      │
│  ├─ Redis                           │
│  └─ InfluxDB                        │
└─────────────────────────────────────┘
```

---

## 📋 實施計劃

### Phase 1: 依賴清理 (1-2天)
1. 移除前端重複依賴
2. 統一後端 HTTP 客戶端
3. 分離開發依賴
4. 更新 package.json 和 requirements.txt

### Phase 2: 依賴注入實現 (2-3天)
1. 創建 DI 容器
2. 定義服務接口
3. 實現事件總線
4. 重構現有服務

### Phase 3: 循環依賴消除 (2-3天)
1. 運行檢測腳本
2. 重構模塊邊界
3. 引入抽象層
4. 驗證無循環

### Phase 4: 驗證和測試 (1-2天)
1. 單元測試
2. 集成測試
3. 性能測試
4. CI/CD 集成

---

## ✅ 預期成果

- [ ] 前端依賴減少 20-25%
- [ ] 後端依賴減少 10-15%
- [ ] 構建時間減少 15-20%
- [ ] 零循環依賴
- [ ] 完整的 DI 容器
- [ ] 事件驅動架構
- [ ] 所有服務可獨立測試

---

*報告生成於 2025-12-25T02:00:00Z*

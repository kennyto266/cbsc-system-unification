# CBSC 量化交易策略管理系統 - 架構白板

> 自動生成於 2025-12-31
>
> 本文檔包含 CBSC 系統的完整架構視圖，使用 Mermaid 圖表格式。

## 📊 架構視圖導航

### 1. 系統上下文圖
**文件**: `system-context.mmd`

顯示系統與外部世界的交互：
- 用戶角色（交易員、管理員）
- 系統邊界（前端、後端、數據庫）
- 外部服務（市場數據源、券商 API）

**適用場景**:
- 向利益相關者介紹系統
- 理解系統整體範圍
- 識別外部依賴

### 2. 容器架構圖
**文件**: `container-architecture.mmd`

詳細展示系統內部結構：
- 前端模組（路由、功能、組件、狀態）
- 後端模組（路由、服務、中間件、核心）
- 數據層（PostgreSQL、Redis）

**適用場景**:
- 開發人員理解代碼組織
- 架構評審和技術討論
- 新成員入職培訓

### 3. 部署架構圖
**文件**: `deployment-architecture.mmd`

描述實際部署結構：
- 開發環境設置
- Docker 容器配置
- 端口映射和網絡
- 啟動順序和命令

**適用場景**:
- DevOps 配置
- 環境搭建指南
- 故障排查

### 4. 數據流圖
**文件**: `data-flow.mmd`

展示關鍵業務流程：
- 認證流程
- 策略管理流程
- 回測流程
- 實時監控流程

**適用場景**:
- 業務流程理解
- 性能優化分析
- 集成測試設計

## 🎯 技術棧總覽

### 前端技術棧
| 類別 | 技術 | 用途 |
|------|------|------|
| 框架 | React 18 | UI 框架 |
| 語言 | TypeScript | 類型安全 |
| 構建 | Vite | 開發服務器 |
| 路由 | React Router v6 | 頁面路由 |
| 狀態 | Redux Toolkit | 狀態管理 |
| API | RTK Query | 數據獲取 |
| UI | Ant Design | 組件庫 |
| 圖表 | Chart.js, Plotly.js | 數據可視化 |

### 後端技術棧
| 類別 | 技術 | 用途 |
|------|------|------|
| 框架 | FastAPI | Web 框架 |
| 異步 | asyncio, uvloop | 異步處理 |
| ORM | SQLAlchemy | 數據庫 ORM |
| 驗證 | Pydantic | 數據驗證 |
| 認證 | JWT | 令牌認證 |
| 回測 | VectorBT | 回測引擎 |
| 文檔 | Swagger/OpenAPI | API 文檔 |

### 基礎設施
| 類別 | 技術 | 用途 |
|------|------|------|
| 數據庫 | PostgreSQL 15 | 主數據庫 |
| 緩存 | Redis | 緩存層 |
| 容器 | Docker | 容器化 |
| 反向代理 | Vite Proxy | 開發代理 |
| 實時通信 | WebSocket | 實時推送 |

## 🔌 API 端點總覽

### 認證 API
```
POST   /api/v1/auth/login       - 用戶登入
POST   /api/v1/auth/logout      - 用戶登出
POST   /api/v1/auth/refresh     - 刷新 Token
GET    /api/v1/auth/me          - 獲取當前用戶
```

### 策略 API
```
GET    /api/v1/strategies       - 獲取策略列表
POST   /api/v1/strategies       - 創建新策略
GET    /api/v1/strategies/{id}  - 獲取策略詳情
PUT    /api/v1/strategies/{id}  - 更新策略
DELETE /api/v1/strategies/{id}  - 刪除策略
```

### 回測 API
```
POST   /api/backtest            - 執行回測
GET    /api/backtest/{id}       - 獲取回測報告
```

### 數據 API
```
GET    /api/data/market/{symbol} - 獲取市場數據
GET    /api/data/indicators      - 獲取技術指標
```

## 📁 數據庫結構

### 主要數據表
| 表名 | 用途 | 關鍵字段 |
|------|------|----------|
| `users` | 用戶信息 | id, username, email, password_hash |
| `stock_data` | 股票數據 | symbol, timestamp, open, high, low, close |
| `strategy_signals` | 策略信號 | strategy_id, symbol, action, timestamp |
| `market_indicators` | 市場指標 | symbol, indicator_name, value, timestamp |
| `hkex_raw_data` | 港交所數據 | symbol, trading_date, data_json |
| `ml_models` | ML 模型 | model_name, version, parameters, performance |

## 🚀 快速開始

### 前置要求
- Node.js 18+
- Python 3.11+
- Docker Desktop
- Git

### 啟動步驟

1. **啟動數據庫**
```bash
docker start cbsc-postgres
```

2. **啟動後端**
```bash
cd C:\Users\Penguin8n\CODEX--\src
python main.py
```

3. **啟動前端**
```bash
cd C:\Users\Penguin8n\CODEX--\frontend
npm run dev
```

4. **訪問應用**
- 前端: http://localhost:3000
- 後端: http://localhost:8001
- API 文檔: http://localhost:8001/docs

## 📈 性能指標

### 當前優化
- ✅ Redis 緩存（5分鐘 TTL）
- ✅ 前端代碼分割
- ✅ API 響應壓縮
- ✅ 數據庫連接池

### 未來改進
- 🔄 數據庫查詢優化
- 🔄 CDN 靜態資源
- 🔄 GraphQL 替代 REST
- 🔄 微服務架構

## 🔒 安全措施

### 已實施
- JWT 令牌認證
- RBAC 權限控制
- CORS 跨域保護
- SQL 注入防護
- XSS 防護

### 計劃中
- 多因子認證 (MFA)
- API 限流
- 審計日誌
- 數據加密

## 📞 支持

- **API 文檔**: http://localhost:8001/docs
- **GitHub Issues**: [項目 Issues]
- **文檔**: `docs/` 目錄

---

**生成工具**: Claude Code PM
**最後更新**: 2025-12-31
**版本**: 1.0.0

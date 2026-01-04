# Technology Stack

## Architecture

微服務架構 + 單體應用混合模式，支持從個人使用到企業部署的平滑擴展

### API Versioning Strategy
- **v2.0**: 新統一架構 (`/api/v2/`)
- **v1.0**: 當前穩定版本 (`/api/v1/`)
- **v0.x**: 向後兼容版本 (逐步廢棄)

## Core Technologies

### Backend
- **語言**: Python 3.10+ (數據處理) + TypeScript (前端)
- **框架**: FastAPI (後端API) + React 18 (前端)
- **運行時**: Node.js 20+ (前端), Python 3.10+ (後端)

### Frontend
- **框架**: React 18 + TypeScript
- **狀態管理**: Redux Toolkit + RTK Query
- **UI庫**: Ant Design + Tailwind CSS
- **圖表**: Chart.js + Plotly.js
- **構建工具**: Vite

### Database & Cache
- **主數據庫**: PostgreSQL (用戶、策略、歷史數據)
- **緩存**: Redis (會話、實時數據、API響應)
- **時序數據**: InfluxDB (市場數據、性能指標)

## Key Libraries

### Python Backend
```python
# 核心框架
fastapi==0.104.1          # API框架
uvicorn==0.24.0           # ASGI服務器
sqlalchemy==2.0.23        # ORM
alembic==1.13.0           # 數據庫遷移

# 數據處理
pandas==2.1.4             # 數據分析
numpy==1.25.2             # 數值計算
yfinance==0.2.28          # 金融數據
ta==0.10.2                # 技術指標

# 認證安全
python-jose==3.3.0       # JWT處理
passlib==1.7.4            # 密碼哈希
python-multipart==0.0.6   # 表單數據
```

### TypeScript Frontend
```typescript
// 核心依賴
"@reduxjs/toolkit": "^2.11.2"    // 狀態管理
"react": "^18.2.0"                // UI框架
"antd": "^6.1.0"                  // UI組件庫
"axios": "^1.6.2"                 // HTTP客戶端

// 圖表可視化
"chart.js": "^4.5.1"              // 圖表引擎
"plotly.js": "^3.3.1"             // 科學繪圖
"recharts": "^2.15.4"             // React圖表組件

// 實時通信
"socket.io-client": "^4.7.4"      // WebSocket客戶端
```

## Development Standards

### Type Safety
- **TypeScript嚴格模式**: 啟用所有嚴格檢查，禁用 `any` 類型
- **Python類型提示**: 使用 `typing` 模塊，強制類型檢查
- **API類型定義**: 自動生成 TypeScript 類型從 OpenAPI 規範

### Code Quality
```python
# Python: 使用 black + isort + flake8
black src/                 # 代碼格式化
isort src/                 # 導入排序
flake8 src/                # 代碼檢查

# TypeScript: ESLint + Prettier
npm run lint               # ESLint檢查
npm run format             # Prettier格式化
npm run type-check         # 類型檢查
```

### Testing
- **後端**: pytest + 覆蓋率報告 (>80%)
- **前端**: Jest + React Testing Library
- **API**: 自動化集成測試 + 文檔測試
- **E2E**: Playwright 端到端測試

## Development Environment

### Required Tools
- Python 3.10+ (建議使用 pyenv)
- Node.js 20+ (建議使用 nvm)
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

### Common Commands
```bash
# 後端開發
cd src/api && python -m uvicorn main:app --reload --port 3004

# 前端開發
cd frontend && npm run dev --port 3000

# 測試
npm run test               # 單元測試
npm run test:e2e          # E2E測試
pytest src/               # Python測試

# 數據庫
alembic upgrade head       # 遷移數據庫
alembic revision --autogenerate -m "desc"  # 創建遷移
```

## Key Technical Decisions

### API Design Philosophy
- **RESTful原則**: 清晰的資源路徑和HTTP動詞使用
- **版本控制**: URL路徑版本控制 (`/api/v1/`, `/api/v2/`)
- **統一響應格式**: 標準化的成功/錯誤響應結構
- **OpenAPI文檔**: 自動生成並維護API文檔

### State Management
- **後端無狀態**: 所有狀態存儲在數據庫或緩存
- **前端集中式**: Redux Toolkit 管理全局狀態
- **實時數據**: WebSocket + Server-Sent Events
- **緩存策略**: Redis多級緩存（應用、查詢、對象）

### Security Architecture
- **認證**: JWT + RS256 簽名
- **授權**: RBAC模型 + 資源級權限
- **數據保護**: 敏感數據加密存儲
- **通信安全**: HTTPS + CORS策略

### Performance Optimizations
- **前端**: 代碼分割、懶加載、虛擬滾動
- **後端**: 數據庫連接池、查詢優化、異步處理
- **網絡**: CDN靜態資源、HTTP/2、Gzip壓縮
- **緩存**: 多層緩存策略（CDN、應用、數據庫）

---
_關注核心模式，而非詳盡的依賴列表_
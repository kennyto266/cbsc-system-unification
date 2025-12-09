# 量化交易系統 - Localhost Interface

基於香港政府數據的非價格信號量化交易平台的本地Web介面。

## 📋 功能概述

### 🔐 認證與安全
- JWT令牌認證系統
- 基於角色的訪問控制（管理員、交易員、分析師、訪客）
- 會話管理和安全會話超時
- 輸入驗證和速率限制

### 📊 實時監控
- WebSocket實時數據流
- 多股票同時監控
- 交易信號實時推送
- 性能指標動態更新

### 🚀 核心功能
1. **非價格信號系統**: 6個香港政府數據源集成
2. **技術分析指標**: RSI, MACD, 布林帶等81種指標
3. **SR/MDD優化**: Sortino比率和最大回撤持續時間優化
4. **策略管理**: 動態策略配置和性能監控
5. **風險控制**: 實時風險監控和警報系統

## 🏗️ 系統架構

### 後端 (FastAPI + Python)
- **框架**: FastAPI, Uvicorn
- **認證**: JWT + OAuth2
- **實時通信**: WebSocket
- **數據庫**: SQLite (開發) / PostgreSQL (生產)
- **緩存**: Redis

### 前端 (React + TypeScript)
- **框架**: React 18, TypeScript 5
- **UI庫**: Material-UI v5
- **狀態管理**: Redux Toolkit + Zustand
- **圖表**: Recharts, Chart.js, Plotly
- **實時通信**: Socket.io Client

### 數據集成
- **香港金融管理局API**: HIBOR利率、匯率數據等
- **非價格信號轉換**: 經濟數據轉技術指標
- **VectorBT集成**: 專業回測引擎

## 🚀 快速開始

### 環境要求
- Python 3.8+
- Node.js 16+
- Redis (可選)

### 後端設置

1. **安裝依賴**
```bash
cd localhost_interface
pip install -r requirements.txt
```

2. **環境配置**
```bash
# 複製環境變量模板
cp .env.example .env

# 編輯配置文件
# 設置SECRET_KEY, DATABASE_URL等
```

3. **啟動後端服務器**
```bash
# 開發模式
cd localhost_interface
python main.py

# 或使用uvicorn
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

4. **訪問API文檔**
- Swagger UI: http://127.0.0.1:8000/api/docs
- ReDoc: http://127.0.0.1:8000/api/redoc

### 前端設置

1. **安裝依賴**
```bash
cd localhost_interface/frontend
npm install
```

2. **啟動開發服務器**
```bash
npm start
```

3. **訪問前端應用**
- 本地地址: http://localhost:3000

### 預設用戶賬戶

| 用戶名 | 密碼 | 角色 | 權限 |
|--------|------|------|------|
| admin | admin123!@# | 管理員 | 全部權限 |
| trader | trader123!@# | 交易員 | 讀寫、交易、回測 |
| analyst | analyst123!@# | 分析師 | 讀取、回測 |
| guest | guest123 | 訪客 | 只讀 |

## 📁 項目結構

```
localhost_interface/
├── backend/                    # 後端代碼
│   ├── api/                   # API路由
│   │   ├── auth.py           # 認證系統
│   │   └── routes/           # 業務路由
│   ├── core/                 # 核心配置
│   ├── services/             # 業務服務
│   ├── websocket/            # WebSocket管理
│   └── models/               # 數據模型
├── frontend/                  # 前端代碼
│   ├── src/
│   │   ├── components/       # React組件
│   │   ├── pages/           # 頁面組件
│   │   ├── hooks/           # 自定義鉤子
│   │   ├── services/        # API服務
│   │   ├── store/           # 狀態管理
│   │   └── types/           # TypeScript類型
│   └── public/              # 靜態資源
├── shared/                    # 共享代碼
│   └── models/               # 共享數據模型
├── main.py                    # 主應用入口
├── requirements.txt           # Python依賴
└── README.md                  # 項目文檔
```

## 🔧 API端點

### 認證
- `POST /api/auth/token` - 用戶登入
- `GET /api/auth/me` - 獲取當前用戶信息

### 交易信號
- `GET /api/trading/signals` - 獲取交易信號
- `GET /api/trading/indicators` - 獲取技術指標
- `POST /api/trading/signals/generate` - 生成交易信號

### 策略管理
- `GET /api/strategies` - 獲取策略列表
- `POST /api/strategies` - 創建新策略

### 回測分析
- `POST /api/backtest/run` - 運行回測
- `GET /api/backtest/results/{id}` - 獲取回測結果

### 風險管理
- `GET /api/risk/metrics` - 獲取風險指標
- `GET /api/risk/alerts` - 獲取風險警報

### 市場數據
- `GET /api/market/price` - 獲取市場價格數據
- `GET /api/market/non-price` - 獲取非價格數據

## 🔌 WebSocket連接

### 端點
- `ws://127.0.0.1:8000/ws/{client_id}`

### 消息類型
- `subscribe` - 訂閱實時數據
- `unsubscribe` - 取消訂閱
- `trading_signal` - 交易信號更新
- `market_data` - 市場數據更新
- `performance` - 性能指標更新

### 訂閱示例
```javascript
const ws = new WebSocket('ws://127.0.0.1:8000/ws/client123');

ws.onopen = function() {
    ws.send(JSON.stringify({
        type: 'subscribe',
        data: {
            symbol: '0700.HK',
            message_type: 'signals'
        }
    }));
};
```

## ⚙️ 配置選項

### 環境變量
```bash
# 應用配置
DEBUG=false
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 數據庫配置
DATABASE_URL=sqlite:///./trading_system.db
REDIS_URL=redis://localhost:6379/0

# API配置
HOST=127.0.0.1
PORT=8000
CORS_ORIGINS=http://localhost:3000

# 香港API配置
HKMA_API_BASE_URL=https://api.hkma.gov.hk/public
HKMA_RATE_LIMIT=100

# 交易配置
MAX_CONCURRENT_BACKTESTS=5
BACKTEST_TIMEOUT=600
```

## 🛡️ 安全特性

### 認證安全
- JWT令牌加密和簽名
- 訪問令牌短期有效（15分鐘）
- 刷新令牌長期有效（7天）
- 令牌黑名單機制

### API安全
- CORS配置限制來源
- 速率限制防止濫用
- 輸入驗證防止注入攻擊
- 敏感信息隱藏

### 會話安全
- 自動超時機制
- 異常登入檢測
- 活動監控和日誌記錄

## 📊 性能特性

### 後端性能
- 異步處理支持高並發
- Redis緩存提升響應速度
- 數據庫連接池優化
- WebSocket並發連接支持

### 前端性能
- React 18並發特性
- 組件懶加載
- 數據虛擬化
- 圖表性能優化

## 🔄 部署指南

### 開發環境
```bash
# 後端
python main.py

# 前端
cd frontend && npm start
```

### 生產環境
```bash
# 後端
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# 前端
cd frontend && npm run build

# 使用Nginx或其他Web服務器提供靜態文件
```

### Docker部署
```dockerfile
# 後端Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# 前端Dockerfile
FROM node:16-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
FROM nginx:alpine
COPY --from=0 /app/build /usr/share/nginx/html
```

## 🧪 測試

### 後端測試
```bash
# 安裝測試依賴
pip install pytest pytest-asyncio

# 運行測試
pytest tests/

# 覆蓋率報告
pytest --cov=backend tests/
```

### 前端測試
```bash
# 運行單元測試
npm test

# 運行端到端測試
npm run test:e2e
```

## 📝 日誌和監控

### 日誌配置
- 結構化日誌記錄
- 日誌級別動態調整
- 日誌文件輪轉
- 錯誤追蹤和報告

### 監控指標
- API響應時間
- WebSocket連接數
- 系統資源使用率
- 錯誤率和警報

## 🤝 貢獻指南

### 開發流程
1. Fork項目
2. 創建功能分支
3. 提交代碼
4. 創建Pull Request

### 代碼規範
- Python: PEP 8 + Black格式化
- TypeScript: ESLint + Prettier
- 提交信息: Conventional Commits
- 測試覆蓋率: >80%

## 📄 許可證

本項目採用MIT許可證，詳見LICENSE文件。

## 🆘 支持與幫助

### 常見問題
1. **端口衝突**: 修改配置文件中的端口設置
2. **依賴安裝失敗**: 檢查Python/Node.js版本
3. **API連接失敗**: 確認後端服務已啟動

### 技術支持
- 文檔: [項目Wiki](./docs/)
- 問題追蹤: [GitHub Issues](https://github.com/your-repo/issues)
- 郵件: support@trading-system.com

---

**注意**: 本系統僅供研究和學習使用，不構成投資建議。使用本系統進行實際交易需要自行承擔風險。
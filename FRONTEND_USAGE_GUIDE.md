# CBSC 前端系統使用指南

## 🚀 快速啟動

### 方法 1：雙擊批處理文件（推薦）
直接雙擊 `start_frontend.bat`

### 方法 2：PowerShell
```powershell
cd C:\Users\Penguin8n\CODEX--\frontend
npx vite --port 3000
```

### 方法 3：使用腳本
```powershell
.\start_frontend.ps1
```

---

## 📱 訪問地址

啟動後在瀏覽器中訪問：

- **本地**: http://localhost:3000
- **網絡**: http://10.5.0.2:3000
- **局域網**: http://192.168.1.5:3000

---

## 🔌 端口配置

- **前端端口**: 3000
- **後端 API**: 3003 (代理)
- **WebSocket**: 3003 (代理)

---

## 📦 系統組件

### 前端框架
- React 18
- TypeScript
- Vite 5.4
- Tailwind CSS

### 狀態管理
- Redux Toolkit
- RTK Query

### UI 組件
- Headless UI
- Chart.js
- Plotly.js

---

## 🛠️ 開發命令

```bash
# 啟動開發服務器
npm run dev

# 或直接使用 Vite
npx vite --port 3000

# 構建生產版本
npm run build

# 預覽構建結果
npm run preview
```

---

## 🔧 故障排除

### 端口被占用
```powershell
# 查找占用端口 3000 的進程
netstat -ano | findstr :3000

# 終止進程
taskkill /PID <進程ID> /F
```

### 依賴問題
```powershell
# 清除緩存並重新安裝
cd C:\Users\Penguin8n\CODEX--\frontend
rm -r node_modules
rm package-lock.json
npm install
```

### 節點版本不兼容
```powershell
# 使用 nvm 切換到 Node 18 或 20
nvm use 18
npm install
npm run dev
```

---

## 📁 項目結構

```
frontend/
├── src/
│   ├── api/           # API 客戶端
│   ├── components/    # React 組件
│   ├── pages/         # 頁面
│   ├── store/         # Redux store
│   ├── hooks/         # 自定義 hooks
│   ├── services/      # 服務層
│   └── utils/         # 工具函數
├── public/            # 靜態資源
└── vite.config.ts     # Vite 配置
```

---

## 🔗 API 端點

前端會自動代理以下請求到後端：

- `/api/*` → `http://localhost:3003/api/*`
- `/ws/*` → `ws://localhost:3003/ws/*`

---

## 📝 開發注意事項

1. **熱重載**: Vite 支持快速熱重載，修改代碼後會自動刷新
2. **類型檢查**: TypeScript 提供實時類型檢查
3. **代碼規範**: ESLint + Prettier 自動格式化
4. **代理配置**: 開發環境自動代理 API 請求

---

## 🎯 下一步

1. 確保後端服務器運行在端口 3003
2. 啟動前端開發服務器
3. 在瀏覽器中訪問 http://localhost:3000
4. 開始開發或測試功能

---

**系統狀態**: ✅ 前端已啟動在 http://localhost:3000

*CBSC Quant Team - 2025*

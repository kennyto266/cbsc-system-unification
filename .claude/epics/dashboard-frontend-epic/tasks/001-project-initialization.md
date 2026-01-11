---
name: task-001-project-initialization
status: open
created: 2025-12-13T09:33:34Z
updated: 2025-12-13T09:33:34Z
assignee: frontend-team
phase: 1
estimated_hours: 24
priority: high
---

# Task #1: 項目初始化

## 📋 任務描述
搭建 CBSC Dashboard 前端項目的基礎架構，包括 React + TypeScript 項目骨架、Vite 構建配置、開發環境 Docker 化以及 CI/CD 管道配置。

## 🎯 具體要求

### 1.1 項目結構搭建
- [ ] 使用 Vite 創建 React + TypeScript 項目
- [ ] 配置標準化的目錄結構
- [ ] 設置 ESLint 和 Prettier 配置
- [ ] 配置 TypeScript 嚴格模式
- [ ] 設置 Git hooks (husky + lint-staged)

### 1.2 核心依賴安裝
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@reduxjs/toolkit": "^1.9.7",
    "react-redux": "^8.1.3",
    "react-router-dom": "^6.8.0",
    "@headlessui/react": "^1.7.17",
    "@heroicons/react": "^2.0.18",
    "clsx": "^2.0.0",
    "chart.js": "^4.4.0",
    "react-chartjs-2": "^5.2.0",
    "plotly.js": "^2.27.0",
    "react-plotly.js": "^2.6.0",
    "socket.io-client": "^4.7.4"
  },
  "devDependencies": {
    "@types/react": "^18.2.37",
    "@types/react-dom": "^18.2.15",
    "@typescript-eslint/eslint-plugin": "^6.10.0",
    "@typescript-eslint/parser": "^6.10.0",
    "autoprefixer": "^10.4.16",
    "eslint": "^8.53.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.4",
    "postcss": "^8.4.31",
    "tailwindcss": "^3.3.5",
    "typescript": "^5.2.2",
    "vite": "^4.5.0",
    "vite-plugin-pwa": "^0.16.7",
    "workbox-window": "^6.6.0"
  }
}
```

### 1.3 Docker 開發環境
- [ ] 創建 Dockerfile 用於開發環境
- [ ] 配置 docker-compose.yml 包含前端、後端和數據庫服務
- [ ] 設置熱重載和代理配置
- [ ] 配置環境變量管理

### 1.4 CI/CD 管道
- [ ] 創建 GitHub Actions 工作流
- [ ] 配置自動化測試、構建和部署
- [ ] 設置代碼質量檢查 (SonarQube)
- [ ] 配置自動化部署到開發/測試環境

## ✅ 驗收標準

1. **功能驗收**
   - [ ] 項目可以正常啟動 (`npm run dev`)
   - [ ] 所有依賴正確安裝無衝突
   - [ ] Docker 環境可以正常運行
   - [ ] CI/CD 管道可以正常觸發

2. **質量標準**
   - [ ] TypeScript 編譯無錯誤無警告
   - [ ] ESLint 檢查通過
   - [ ] 代碼覆蓋率 > 80%
   - [ ] 構建時間 < 30 秒

3. **性能標準**
   - [ ] 首次加載時間 < 3 秒
   - [ ] 熱重載響應時間 < 1 秒
   - [ ] Docker 啟動時間 < 10 秒

## 🔧 技術要求

### 項目配置文件
```typescript
// vite.config.ts
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg}']
      }
    })
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:3003',
        changeOrigin: true
      }
    }
  }
});
```

### TypeScript 配置
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

## 📊 預估工作量
| 子任務 | 預估時間 | 負責人 |
|--------|----------|--------|
| 項目結構搭建 | 4小時 | 前端工程師 A |
| 依賴安裝與配置 | 6小時 | 前端工程師 A |
| Docker 環境配置 | 8小時 | 前端工程師 B |
| CI/CD 管道設置 | 6小時 | DevOps 工程師 |
| **總計** | **24小時** | |

## 🔗 依賴關係
- 前置任務：無
- 後續任務：Task #2 (設計系統實現)

## 📝 注意事項
1. 確保 Node.js 版本 >= 18.0.0
2. 使用 pnpm 作為包管理器以提高性能
3. 所有配置文件需要添加詳細註釋
4. 保持與現有後端 API 的兼容性

## 🚀 快速開始指南
```bash
# 克隆項目
git clone <repository-url>
cd cbsc-dashboard

# 安裝依賴
pnpm install

# 啟動開發環境
docker-compose up -d
pnpm dev

# 運行測試
pnpm test

# 構建生產版本
pnpm build
```

## 📚 相關文檔
- [Vite 官方文檔](https://vitejs.dev/)
- [React 18 文檔](https://react.dev/)
- [TypeScript 手冊](https://www.typescriptlang.org/docs/)
- [Tailwind CSS 文檔](https://tailwindcss.com/docs)
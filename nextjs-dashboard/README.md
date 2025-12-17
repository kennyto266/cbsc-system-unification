# CBSC Next.js Dashboard

基於Next.js 14+構建的現代化量化交易策略管理Dashboard，採用App Router、Server Components和最新的React生態系統。

## 功能特性

- 🚀 **Next.js 14+ App Router** - 利用最新的服務端渲染和代碼分割功能
- 📊 **實時數據監控** - WebSocket實時更新策略表現和市場數據
- 🎨 **現代化UI設計** - 基於Tailwind CSS和shadcn/ui的響應式設計
- 🔐 **完整的認證系統** - 支持JWT和NextAuth.js
- 📈 **477項技術指標** - 專業的量化分析工具
- 🐻 **CBSC牛熊證數據** - 實時牛熊證市場數據監控
- ⚡ **高性能優化** - SSR/SSG/ISR混合渲染，極致的加載速度
- 🌙 **深色模式** - 支持明暗主題切換
- 📱 **移動端適配** - 完全響應式設計
- 🔒 **類型安全** - 完整的TypeScript支持

## 技術棧

- **框架**: Next.js 14.2.5 (App Router)
- **語言**: TypeScript 5.5.3
- **樣式**: Tailwind CSS 3.4.6 + shadcn/ui
- **狀態管理**: Zustand + TanStack Query
- **圖表**: Chart.js + Plotly.js + Recharts
- **UI組件**: Ant Design 5.20.2 + Radix UI
- **認證**: NextAuth.js 5.0.0
- **實時通信**: Socket.io
- **數據庫**: PostgreSQL + Prisma
- **緩存**: Redis
- **測試**: Jest + Playwright
- **代碼質量**: ESLint + Prettier + Husky

## 快速開始

### 環境要求

- Node.js >= 18.0.0
- npm >= 8.0.0
- PostgreSQL >= 13
- Redis >= 6

### 安裝步驟

1. **克隆項目**
   ```bash
   git clone https://github.com/your-org/cbsc-nextjs-dashboard.git
   cd cbsc-nextjs-dashboard
   ```

2. **安裝依賴**
   ```bash
   npm install
   ```

3. **配置環境變量**
   ```bash
   cp .env.example .env.local
   # 編輯 .env.local 文件，填寫實際配置
   ```

4. **初始化數據庫**
   ```bash
   npx prisma db push
   npx prisma db seed
   ```

5. **啟動開發服務器**
   ```bash
   npm run dev
   ```

6. **訪問應用**

   打開瀏覽器訪問 [http://localhost:3000](http://localhost:3000)

## 項目結構

```
src/
├── app/                    # App Router目錄
│   ├── (auth)/            # 認證路由群組
│   ├── (dashboard)/       # Dashboard路由群組
│   ├── api/               # API Routes
│   ├── globals.css        # 全局樣式
│   └── layout.tsx         # 根佈局
├── components/            # 共享組件
│   ├── ui/               # shadcn/ui基礎組件
│   ├── dashboard/        # Dashboard組件
│   ├── forms/           # 表單組件
│   └── layout/          # 佈局組件
├── lib/                  # 工具函數
├── hooks/               # 自定義Hooks
├── store/               # 狀態管理
├── types/               # TypeScript類型
└── styles/              # 樣式文件
```

## 主要功能模塊

### 1. 策略管理
- 策略列表與詳情
- 實時策略監控
- 策略性能分析
- 策略參數配置

### 2. 數據分析
- 實時圖表展示
- 技術指標分析
- 風險評估報告
- 回測系統

### 3. CBSC牛熊證
- 實時牛熊證數據
- 溢價率分析
- 到期日提醒
- 交易建議

### 4. 系統監控
- 系統資源監控
- 錯誤日誌查看
- 性能指標追蹤
- 健康狀態檢查

## 開發指南

### 代碼規範

1. **命名規範**
   - 組件: PascalCase (如 `DashboardPage`)
   - 函數: camelCase (如 `fetchUserData`)
   - 常量: UPPER_SNAKE_CASE (如 `API_BASE_URL`)

2. **文件組織**
   - 每個組件一個文件夾
   - index.tsx作為入口
   - 相關的hooks、types、utils放在同一文件夾

3. **提交規範**
   ```
   feat: 新功能
   fix: 修復bug
   docs: 文檔更新
   style: 代碼格式化
   refactor: 重構
   test: 測試相關
   chore: 構建或輔助工具變動
   ```

### 組件開發

1. **Server Components**
   - 優先用於數據獲取
   - 不包含交互邏輯
   - 直接訪問數據庫

2. **Client Components**
   - 添加 `'use client'` 指令
   - 處理用戶交互
   - 使用React Hooks

3. **性能優化**
   - 使用 `dynamic()` 動態導入
   - 實現虛擬滾動
   - 合理使用 `memo` 和 `useMemo`

### API開發

1. **Route Handlers**
   ```typescript
   export async function GET(request: NextRequest) {
     // 處理GET請求
   }

   export async function POST(request: NextRequest) {
     // 處理POST請求
   }
   ```

2. **錯誤處理**
   ```typescript
   try {
     // API邏輯
     return NextResponse.json(data)
   } catch (error) {
     return NextResponse.json(
       { error: error.message },
       { status: 500 }
     )
   }
   ```

## 部署

### Docker部署

1. **構建鏡像**
   ```bash
   docker build -t cbsc-dashboard .
   ```

2. **運行容器**
   ```bash
   docker run -p 3000:3000 cbsc-dashboard
   ```

### Vercel部署

1. **安裝Vercel CLI**
   ```bash
   npm i -g vercel
   ```

2. **部署**
   ```bash
   vercel --prod
   ```

### 自有服務器部署

1. **構建項目**
   ```bash
   npm run build
   ```

2. **啟動生產服務器**
   ```bash
   npm start
   ```

## 性能指標

- **FCP**: < 1.5s
- **LCP**: < 2.5s
- **FID**: < 100ms
- **CLS**: < 0.1
- **TTI**: < 3s

## 監控和日誌

- 使用Sentry進行錯誤監控
- 集成Google Analytics進行用戶行為分析
- 使用Winston進行日誌記錄

## 測試

```bash
# 單元測試
npm run test

# E2E測試
npm run test:e2e

# 測試覆蓋率
npm run test:coverage
```

## 貢獻指南

1. Fork項目
2. 創建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟Pull Request

## 許可證

本項目採用MIT許可證 - 查看 [LICENSE](LICENSE) 文件了解詳情

## 支持

- 📧 Email: support@cbsc.com
- 📱 微信群: 掃描二維碼加入
- 📖 文檔: [https://docs.cbsc.com](https://docs.cbsc.com)
- 🐛 問題反饋: [GitHub Issues](https://github.com/your-org/cbsc-nextjs-dashboard/issues)

## 更新日誌

查看 [CHANGELOG.md](CHANGELOG.md) 了解版本更新詳情。
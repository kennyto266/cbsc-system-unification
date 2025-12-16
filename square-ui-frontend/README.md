# Square UI Frontend

基於 Next.js 14 的現代化 CBSC 策略管理前端系統。

## 🚀 技術棧

- **框架**: Next.js 14 (App Router)
- **語言**: TypeScript
- **樣式**: Tailwind CSS
- **狀態管理**: 準備中 (Zustand/Redux Toolkit)
- **UI 組件**: Shadcn/ui + Square 增強組件
- **圖表**: Chart.js / Recharts
- **構建工具**: Next.js 內建
- **代碼規範**: ESLint + Prettier

## 📋 項目結構

```
square-ui-frontend/
├── app/                    # App Router 頁面
│   ├── (auth)/            # 認證相關頁面
│   ├── dashboard/         # 儀表板頁面
│   ├── strategies/        # 策略管理頁面
│   ├── settings/          # 設置頁面
│   ├── globals.css        # 全局樣式
│   ├── layout.tsx         # 根佈局
│   └── page.tsx           # 首頁
├── components/            # 可復用組件
│   ├── ui/               # 基礎 UI 組件 (Shadcn/ui + Square)
│   │   ├── button.tsx    # 按鈕組件
│   │   ├── card.tsx      # 卡片組件
│   │   ├── badge.tsx     # 標籤組件
│   │   ├── input.tsx     # 輸入框組件
│   │   ├── square-*.tsx  # Square 增強組件
│   │   └── index.ts      # 組件導出
│   ├── forms/            # 表單組件
│   ├── charts/           # 圖表組件
│   └── layout/           # 佈局組件
├── lib/                  # 工具函數
│   ├── api.ts            # API 客戶端
│   ├── utils.ts          # 通用工具
│   └── square-theme.ts   # Square 主題配置
├── types/                # TypeScript 類型定義
├── hooks/                # 自定義 React Hooks
├── styles/               # 樣式文件
├── docs/                 # 項目文檔
└── scripts/              # 構建和部署腳本
```

## 🛠️ 開發設置

### 前置要求

- Node.js 18+
- npm 或 yarn
- PostgreSQL (可選)
- Redis (可選)

### 安裝依賴

```bash
npm install
```

### 環境變量

複製 `.env.example` 到 `.env.local`：

```bash
cp .env.example .env.local
```

編輯 `.env.local` 文件：

```env
# API 配置
NEXT_PUBLIC_API_URL=http://localhost:3003

# 數據庫配置
DATABASE_URL=postgresql://username:password@localhost:5432/cbsc_db

# Redis 配置
REDIS_URL=redis://localhost:6379

# WebSocket 配置
NEXT_PUBLIC_WS_URL=ws://localhost:3003
```

### 運行開發服務器

```bash
npm run dev
```

訪問 [http://localhost:3000](http://localhost:3000) 查看應用。

## 📜 可用腳本

```bash
# 開發
npm run dev

# 構建生產版本
npm run build

# 啟動生產服務器
npm run start

# 代碼檢查
npm run lint

# 自動修復 lint 問題
npm run lint:fix

# 類型檢查
npm run type-check

# 代碼格式化
npm run format

# 檢查代碼格式
npm run format:check

# 清理構建文件
npm run clean

# 分析構建包大小
npm run analyze
```

## 🎨 Square UI 組件庫

基於 Square 設計語言的現代化 UI 組件庫，提供專業的金融界面風格。

### 組件列表

#### 基礎組件
- **SquareButton** - 增強按鈕組件
  - 支持多種變體：primary, secondary, outline, ghost, destructive, link
  - 支持加載狀態
  - 支持左/右圖標
  - 三種尺寸：sm, md, lg

```tsx
import { SquareButton } from '@/components/ui';
import { Plus, Download } from 'lucide-react';

// 基礎用法
<SquareButton variant="primary">Primary Button</SquareButton>

// 帶圖標
<SquareButton icon={<Plus size={16} />} iconPosition="left">
  新增項目
</SquareButton>

// 加載狀態
<SquareButton loading>處理中...</SquareButton>
```

- **SquareCard** - 增強卡片組件
  - 四種變體：default, bordered, elevated, outlined
  - 支持自定義內邊距
  - 支持頭部和底部插槽

```tsx
<SquareCard variant="elevated" padding="md">
  <div>卡片內容</div>
</SquareCard>
```

- **SquareBadge** - 動態狀態標籤
  - 預設顏色和動態狀態顏色
  - 支持自定義狀態映射

```tsx
<SquareBadge status="active">Active</SquareBadge>
<SquareBadge variant="success">Success</SquareBadge>
```

- **SquareInput** - 增強輸入框
  - 支持標籤、錯誤提示、幫助文本
  - 支持左/右圖標

```tsx
<SquareInput
  label="電子郵件"
  placeholder="example@square.com"
  leftIcon={<Mail size={16} />}
  error="請輸入有效郵箱"
  required
/>
```

### 主題系統

位於 `lib/square-theme.ts`，提供：

- **顏色系統**：Square 品牌色、成功、警告、錯誤、中性色
- **字體系統**：Inter 字體族，完整的等級縮放
- **間距系統**：基於 4px 網格的一致間距
- **圓角系統**：從微妙到明顯的不同圓角選項
- **陰影系統**：分層的深度效果

```tsx
import { getSquareColor, getStatusColors } from '@/lib/square-theme';

// 使用主題顏色
const primaryColor = getSquareColor('primary', 500);
const statusColors = getStatusColors('success');
```

### 組件展示

訪問 `/showcase` 路由查看所有組件的實時演示。

## 🎯 功能模塊

### 1. 認證系統
- 用戶登錄/註冊
- JWT Token 管理
- 角色權限控制
- 受保護路由

### 2. 策略管理
- 策略列表和詳情
- 策略創建和編輯
- 策略參數配置
- 策略執行控制

### 3. 實時監控
- 策略性能指標
- 實時價格數據
- 系統警報通知
- 交互式圖表

### 4. 儀表板
- 個性化小組件
- 拖拽式佈局
- 響應式設計
- 數據可視化

## 🔧 配置說明

### API 代理

項目配置了 API 代理，將 `/api/*` 請求自動轉發到後端服務器（默認 `localhost:3003`）。

### TypeScript 配置

- 嚴格模式啟用
- 路徑別名配置 (`@/` 指向 `src/`)
- 類型檢查和智能提示

### ESLint 和 Prettier

- ESLint 使用 Next.js 推薦配置
- Prettier 統一代碼格式化
- Git hooks 可配置 pre-commit 檢查

## 🧪 測試

項目準備了測試框架配置，可以添加：

```bash
# 單元測試
npm run test

# 測試覆蓋率
npm run test:coverage

# E2E 測試
npm run test:e2e
```

## 📦 部署

### Vercel 部署

1. 推送代碼到 GitHub
2. 在 Vercel 中導入項目
3. 配置環境變量
4. 自動部署

### Docker 部署

```bash
# 構建 Docker 鏡像
docker build -t square-ui-frontend .

# 運行容器
docker run -p 3000:3000 square-ui-frontend
```

### 手動部署

```bash
# 構建生產版本
npm run build

# 啟動服務器
npm run start
```

## 🤝 貢獻指南

1. Fork 項目
2. 創建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 創建 Pull Request

## 📝 開發規範

- 使用 TypeScript 開發
- 遵循 ESLint 規則
- 組件採用函數式編程
- 使用自定義 Hooks 封裝邏輯
- 保持代碼簡潔和可讀性

## 🔗 相關連結

- [Next.js 文檔](https://nextjs.org/docs)
- [Tailwind CSS 文檔](https://tailwindcss.com/docs)
- [TypeScript 文檔](https://www.typescriptlang.org/docs/)
- [CBSC 後端 API](http://localhost:3003/docs)

## 📄 許可證

MIT License
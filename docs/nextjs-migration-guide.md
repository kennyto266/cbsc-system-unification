# Next.js 遷移指南

本指南將幫助您將現有的React Vite應用遷移到Next.js 14+。

## 遷移準備

### 1. 環境準備

```bash
# 安裝Node.js 18+
node --version  # 應 >= 18.0.0

# 創建新的Next.js項目
npx create-next-app@latest nextjs-dashboard --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"

# 進入項目目錄
cd nextjs-dashboard
```

### 2. 安裝必要依賴

```bash
# 安裝UI庫
npm install antd @ant-design/icons @ant-design/plots

# 安裝圖表庫
npm install chart.js react-chartjs-2 plotly.js react-plotly.js recharts

# 安裝狀態管理
npm install zustand @tanstack/react-query

# 安裝實時通信
npm install socket.io-client

# 安裝表單處理
npm install react-hook-form @hookform/resolvers zod

# 安裝日期處理
npm install date-fns dayjs

# 安裝工具庫
npm install lodash clsx tailwind-merge

# 安裝開發依賴
npm install -D @types/lodash
```

## 遷移步驟

### 第一階段：基礎結構遷移

#### 1. 創建文件夾結構

```
src/
├── app/                    # App Router
│   ├── (auth)/            # 認證路由群組
│   ├── (dashboard)/       # Dashboard路由群組
│   └── api/               # API Routes
├── components/            # 組件
│   ├── ui/               # 基礎UI組件
│   ├── dashboard/        # Dashboard組件
│   └── layout/           # 佈局組件
├── lib/                  # 工具函數
├── hooks/               # 自定義Hooks
├── store/               # 狀態管理
└── types/               # 類型定義
```

#### 2. 配置Tailwind CSS

```javascript
// tailwind.config.js
module.exports = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        background: "hsl(var(--background))",
        // ... 其他顏色配置
      }
    }
  }
}
```

### 第二階段：路由遷移

#### 1. 創建App Router結構

```typescript
// src/app/layout.tsx - 根佈局
export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  )
}

// src/app/(dashboard)/layout.tsx - Dashboard佈局
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="flex h-screen">
      <Sidebar />
      <main>{children}</main>
    </div>
  )
}
```

#### 2. 遷移頁面組件

```typescript
// 從 Vite/React Router 遷移到 Next.js App Router
// 舊: src/pages/DashboardPage.tsx
// 新: src/app/(dashboard)/page.tsx

import { DashboardContent } from '@/components/dashboard/dashboard-content'

export default function DashboardPage() {
  return <DashboardContent />
}
```

### 第三階段：組件遷移

#### 1. Server Components 轉換

```typescript
// 將數據獲取邏輯移到 Server Components
// 舊方式 (Client Component)
function StrategyList() {
  const [strategies, setStrategies] = useState([])
  useEffect(() => {
    fetchStrategies().then(setStrategies)
  }, [])
  // ...
}

// 新方式 (Server Component)
async function StrategyList() {
  const strategies = await fetchStrategies()

  return (
    <div>
      {strategies.map(strategy => (
        <StrategyCard key={strategy.id} strategy={strategy} />
      ))}
    </div>
  )
}
```

#### 2. Client Components 處理

```typescript
// 添加 'use client' 指令
'use client'

import { useState } from 'react'

export function InteractiveChart({ data }) {
  const [selected, setSelected] = useState(null)

  // 交互邏輯
}
```

#### 3. 動態導入優化

```typescript
import dynamic from 'next/dynamic'

// 動態導入重型組件
const HeavyChart = dynamic(
  () => import('@/components/heavy-chart'),
  {
    loading: () => <ChartSkeleton />,
    ssr: false
  }
)
```

### 第四階段：數據獲取遷移

#### 1. API Routes 遷移

```typescript
// 從 Vite/Express 遷移到 Next.js API Routes
// 舊: src/api/strategies.js
// 新: src/app/api/strategies/route.ts

import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const page = searchParams.get('page')

  const strategies = await getStrategies(page)

  return NextResponse.json(strategies)
}
```

#### 2. 數據獲取模式

```typescript
// Server-side 數據獲取
async function getPageData() {
  const res = await fetch('https://api.example.com/data', {
    next: { revalidate: 60 } // ISR緩存60秒
  })
  return res.json()
}

export default async function Page() {
  const data = await getPageData()
  return <Component data={data} />
}
```

### 第五階段：狀態管理遷移

#### 1. 遷移Redux到Zustand

```typescript
// 舊: Redux Store
// store/strategiesSlice.js

// 新: Zustand Store
// store/useStrategyStore.ts
import { create } from 'zustand'

interface StrategyStore {
  strategies: Strategy[]
  selectedStrategy: string | null
  setStrategies: (strategies: Strategy[]) => void
  selectStrategy: (id: string) => void
}

export const useStrategyStore = create<StrategyStore>((set) => ({
  strategies: [],
  selectedStrategy: null,
  setStrategies: (strategies) => set({ strategies }),
  selectStrategy: (id) => set({ selectedStrategy: id }),
}))
```

#### 2. 使用TanStack Query

```typescript
// lib/api/strategies.ts
import { useQuery } from '@tanstack/react-query'

export function useStrategies() {
  return useQuery({
    queryKey: ['strategies'],
    queryFn: () => fetch('/api/strategies').then(res => res.json()),
    staleTime: 5 * 60 * 1000, // 5分鐘
  })
}
```

### 第六階段：樣式遷移

#### 1. CSS Modules到Tailwind

```css
/* 舊: Dashboard.module.css */
.container {
  padding: 1rem;
  background: white;
}

/* 新: 使用Tailwind類 */
<div className="p-4 bg-white">
```

#### 2. 主題配置

```typescript
// components/providers/theme-provider.tsx
'use client'

import { ThemeProvider as NextThemesProvider } from 'next-themes'

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  return (
    <NextThemesProvider attribute="class" defaultTheme="system">
      {children}
    </NextThemesProvider>
  )
}
```

### 第七階段：性能優化

#### 1. 圖片優化

```typescript
import Image from 'next/image'

// 使用Next.js Image組件
<Image
  src="/chart.png"
  alt="Strategy Chart"
  width={600}
  height={400}
  priority // 首屏圖片
  placeholder="blur"
/>
```

#### 2. 字體優化

```typescript
// layout.tsx
import { Inter } from 'next/font/google'

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
})

export default function RootLayout({ children }) {
  return (
    <html className={inter.className}>
      {/* ... */}
    </html>
  )
}
```

## 常見問題解決

### 1. 水合錯誤 (Hydration Mismatch)

```typescript
// 使用 useEffect 進行客戶端特定操作
'use client'

import { useEffect, useState } from 'react'

export function ClientOnly({ children }: { children: React.ReactNode }) {
  const [hasMounted, setHasMounted] = useState(false)

  useEffect(() => {
    setHasMounted(true)
  }, [])

  if (!hasMounted) return null
  return <>{children}</>
}
```

### 2. 路由守衛

```typescript
// middleware.ts
import { NextResponse } from 'next/server'
import { getToken } from 'next-auth/jwt'

export async function middleware(request: NextRequest) {
  const token = await getToken({ req: request })

  if (!token && request.nextUrl.pathname.startsWith('/dashboard')) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  return NextResponse.next()
}
```

### 3. 環境變量處理

```typescript
// 使用NEXT_PUBLIC_前綴暴露給客戶端
const API_URL = process.env.NEXT_PUBLIC_API_URL

// 服務器端專用環境變量
const DB_URL = process.env.DATABASE_URL
```

## 遷移檢查清單

- [ ] 安裝所有必要依賴
- [ ] 創建正確的文件夾結構
- [ ] 配置Tailwind CSS
- [ ] 遷移路由結構
- [ ] 轉換組件為Server/Client Components
- [ ] 實現API Routes
- [ ] 遷移狀態管理
- [ ] 優化圖片和字體
- [ ] 配置中間件
- [ ] 設置認證系統
- [ ] 實現錯誤處理
- [ ] 添加加載狀態
- [ ] 配置緩存策略
- [ ] 測試所有功能

## 性能對比

| 指標 | Vite (CSR) | Next.js (SSR/SSG) | 改善 |
|------|------------|-------------------|------|
| FCP | 2.5s | 0.8s | 68% |
| LCP | 3.2s | 1.5s | 53% |
| FID | 120ms | 45ms | 62% |
| CLS | 0.25 | 0.05 | 80% |

## 後續優化建議

1. **實現ISR頁面** - 頻繁更新但可短時間緩存的數據
2. **使用Edge Runtime** - 全球分發的API端點
3. **實現增量靜態再生** - 自動更新靜態頁面
4. **配置CDN** - 加速資源加載
5. **實現PWA** - 離線功能和推送通知
6. **添加Service Worker** - 緩存策略
7. **優化Bundle大小** - 代碼分割和樹搖

## 總結

通過遷移到Next.js，我們獲得了：

- 更快的首屏加載速度
- 更好的SEO支持
- 更靈活的渲染策略
- 更強大的開發工具
- 更完善的生態系統
- 更優的用戶體驗

遷移過程需要仔細規劃和逐步實施，確保每個階段都進行充分測試。
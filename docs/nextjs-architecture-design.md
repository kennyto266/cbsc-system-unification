# Next.js應用架構設計文檔

## 概述

本文檔描述了將現有React Vite應用遷移到Next.js 14+的詳細架構設計，利用App Router、Server Components和現代化性能優化功能。

## 項目結構

```
nextjs-dashboard/
├── src/
│   ├── app/                          # App Router目錄
│   │   ├── (auth)/                   # 認證路由群組
│   │   │   ├── login/
│   │   │   │   └── page.tsx
│   │   │   └── register/
│   │   │       └── page.tsx
│   │   ├── (dashboard)/              # Dashboard路由群組
│   │   │   ├── layout.tsx            # Dashboard群組佈局
│   │   │   ├── page.tsx              # Dashboard主頁
│   │   │   ├── strategies/
│   │   │   │   ├── page.tsx
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx
│   │   │   ├── cbsc/
│   │   │   │   └── page.tsx
│   │   │   ├── analytics/
│   │   │   │   └── page.tsx
│   │   │   └── settings/
│   │   │       └── page.tsx
│   │   ├── api/                      # API Routes
│   │   │   ├── analytics/
│   │   │   │   └── route.ts
│   │   │   ├── strategies/
│   │   │   │   └── route.ts
│   │   │   ├── auth/
│   │   │   │   └── route.ts
│   │   │   └── websocket/
│   │   │       └── route.ts
│   │   ├── globals.css               # 全局樣式
│   │   ├── layout.tsx                # 根佈局
│   │   ├── loading.tsx               # 全局加載狀態
│   │   ├── error.tsx                 # 全局錯誤處理
│   │   ├── not-found.tsx             # 404頁面
│   │   └── route.ts                  # 路由配置
│   ├── components/                   # 共享組件
│   │   ├── ui/                       # shadcn/ui基礎組件
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── chart.tsx
│   │   │   └── ...
│   │   ├── dashboard/                # Dashboard組件
│   │   │   ├── metric-card.tsx
│   │   │   ├── strategy-performance-chart.tsx
│   │   │   ├── asset-allocation-chart.tsx
│   │   │   └── ...
│   │   ├── forms/                    # 表單組件
│   │   │   ├── strategy-form.tsx
│   │   │   └── ...
│   │   └── layout/                   # 佈局組件
│   │       ├── header.tsx
│   │       ├── sidebar.tsx
│   │       └── footer.tsx
│   ├── lib/                          # 工具函數和配置
│   │   ├── utils.ts                  # 通用工具函數
│   │   ├── db.ts                     # 數據庫連接
│   │   ├── auth.ts                   # 認證配置
│   │   ├── websocket.ts              # WebSocket客戶端
│   │   └── validations.ts            # 數據驗證
│   ├── hooks/                        # 自定義Hooks
│   │   ├── use-websocket.ts
│   │   ├── use-strategies.ts
│   │   └── use-analytics.ts
│   ├── store/                        # 狀態管理
│   │   ├── index.ts                  # Store配置
│   │   ├── slices/                   # Redux Slices
│   │   └── api/                      # RTK Query API
│   ├── types/                        # TypeScript類型定義
│   │   ├── index.ts
│   │   ├── strategy.ts
│   │   ├── analytics.ts
│   │   └── auth.ts
│   └── styles/                       # 樣式文件
│       ├── globals.css
│       └── components.css
├── public/                           # 靜態資源
│   ├── icons/
│   ├── images/
│   └── favicon.ico
├── docs/                             # 文檔
├── tests/                            # 測試文件
├── .env.local                        # 環境變量
├── .env.example                      # 環境變量示例
├── next.config.js                    # Next.js配置
├── tailwind.config.js                # Tailwind CSS配置
├── tsconfig.json                     # TypeScript配置
├── package.json                      # 依賴配置
└── README.md                         # 項目說明
```

## 核心特性

### 1. App Router與Server Components

#### Server Components優勢
- 減少客戶端JavaScript包大小
- 直接訪問後端資源（數據庫、API）
- 改善SEO和首屏加載性能
- 自動代碼分割

#### 混合渲染策略
```typescript
// Server Component - 數據獲取
async function StrategyList() {
  const strategies = await getStrategies()

  return (
    <div>
      {strategies.map(strategy => (
        <StrategyCard key={strategy.id} strategy={strategy} />
      ))}
    </div>
  )
}

// Client Component - 交互功能
'use client'
function StrategyCard({ strategy }: { strategy: Strategy }) {
  const [isActive, setIsActive] = useState(strategy.active)

  return (
    <Card>
      <h3>{strategy.name}</h3>
      <Switch
        checked={isActive}
        onChange={setIsActive}
      />
    </Card>
  )
}
```

### 2. 數據獲取策略

#### Server-side Rendering (SSR)
```typescript
// app/(dashboard)/page.tsx
async function getDashboardData() {
  const res = await fetch(`${process.env.API_BASE_URL}/analytics/dashboard`, {
    headers: {
      'Authorization': `Bearer ${process.env.API_TOKEN}`
    },
    next: { revalidate: 60 } // ISR: 60秒重新驗證
  })

  if (!res.ok) {
    throw new Error('Failed to fetch dashboard data')
  }

  return res.json()
}

export default async function DashboardPage() {
  const data = await getDashboardData()

  return <DashboardComponent data={data} />
}
```

#### Client-side Data Fetching
```typescript
// hooks/use-analytics.ts
'use client'
import { useQuery } from '@tanstack/react-query'

export function useAnalytics(timeRange: string) {
  return useQuery({
    queryKey: ['analytics', timeRange],
    queryFn: async () => {
      const res = await fetch(`/api/analytics?timeRange=${timeRange}`)
      return res.json()
    },
    staleTime: 30000, // 30秒內不重新請求
    refetchInterval: 60000, // 每分鐘自動刷新
  })
}
```

### 3. 路由中間件與認證

#### 中間件實現
```typescript
// middleware.ts
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import { verifyToken } from './lib/auth'

export function middleware(request: NextRequest) {
  const token = request.cookies.get('token')?.value

  // 保護路由
  if (request.nextUrl.pathname.startsWith('/dashboard')) {
    if (!token || !verifyToken(token)) {
      return NextResponse.redirect(new URL('/login', request.url))
    }
  }

  // 已登錄用戶重定向
  if (request.nextUrl.pathname === '/login' && token && verifyToken(token)) {
    return NextResponse.redirect(new URL('/dashboard', request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/dashboard/:path*', '/login', '/register']
}
```

### 4. 性能優化配置

#### 動態導入與代碼分割
```typescript
// 動態導入重型組件
const StrategyChart = dynamic(
  () => import('@/components/dashboard/strategy-chart'),
  {
    loading: () => <ChartSkeleton />,
    ssr: false // 僅客戶端渲染
  }
)

// 預加載關鍵資源
export default function HomePage() {
  return (
    <>
      <Head>
        <link rel="preload" href="/api/dashboard" as="fetch" />
      </Head>
      <StrategyChart />
    </>
  )
}
```

#### 圖片優化
```typescript
// 使用Next.js Image組件
import Image from 'next/image'

function StrategyLogo({ src, alt }: { src: string; alt: string }) {
  return (
    <Image
      src={src}
      alt={alt}
      width={64}
      height={64}
      priority // 優先加載
      placeholder="blur"
      blurDataURL="data:image/jpeg;base64,..."
    />
  )
}
```

### 5. API Routes集成

#### RESTful API端點
```typescript
// app/api/strategies/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'

export async function GET(request: NextRequest) {
  const session = await getServerSession(authOptions)

  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const { searchParams } = new URL(request.url)
  const page = parseInt(searchParams.get('page') || '1')
  const limit = parseInt(searchParams.get('limit') || '10')

  const strategies = await getStrategies(session.user.id, page, limit)

  return NextResponse.json(strategies)
}

export async function POST(request: NextRequest) {
  const session = await getServerSession(authOptions)

  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const body = await request.json()
  const strategy = await createStrategy(body, session.user.id)

  return NextResponse.json(strategy, { status: 201 })
}
```

#### WebSocket支持
```typescript
// app/api/websocket/route.ts
import { NextRequest } from 'next/server'
import { WebSocketServer } from 'ws'

export async function GET(request: NextRequest) {
  if (request.headers.get('upgrade') === 'websocket') {
    return new Response('Upgrade Required', { status: 426 })
  }

  // WebSocket握手處理
  const wss = new WebSocketServer({ port: 8080 })

  wss.on('connection', (ws) => {
    ws.on('message', (message) => {
      // 處理實時數據更新
      broadcastMessage(message)
    })
  })

  return new Response('WebSocket server running')
}
```

### 6. 狀態管理策略

#### Server State (使用TanStack Query)
```typescript
// lib/queries.ts
import { queryClient } from './query-client'

export function prefetchDashboardData() {
  queryClient.prefetchQuery({
    queryKey: ['dashboard'],
    queryFn: fetchDashboardData,
  })
}

// 在頁面中使用預取
export default async function Layout({ children }: { children: React.ReactNode }) {
  await prefetchDashboardData()

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}
```

#### Client State (使用Zustand)
```typescript
// store/ui-store.ts
import { create } from 'zustand'

interface UIState {
  sidebarOpen: boolean
  theme: 'light' | 'dark'
  toggleSidebar: () => void
  setTheme: (theme: 'light' | 'dark') => void
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  theme: 'light',
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setTheme: (theme) => set({ theme }),
}))
```

## 遷移計劃

### 第一階段：基礎架構搭建
1. 創建Next.js項目
2. 配置TypeScript和ESLint
3. 安裝必要依賴（shadcn/ui、TanStack Query等）
4. 設置基礎文件結構

### 第二階段：核心功能遷移
1. 遷移Dashboard頁面
2. 實現認證系統
3. 配置API Routes
4. 遷移核心組件

### 第三階段：性能優化
1. 實現SSR/SSG
2. 配置代碼分割
3. 優化圖片和資源
4. 實現緩存策略

### 第四階段：高級功能
1. 實現WebSocket實時更新
2. 添加PWA支持
3. 實現離線功能
4. 性能監控和分析

## 性能指標目標

- **FCP (First Contentful Paint)**: < 1.5s
- **LCP (Largest Contentful Paint)**: < 2.5s
- **FID (First Input Delay)**: < 100ms
- **CLS (Cumulative Layout Shift)**: < 0.1
- **TTI (Time to Interactive)**: < 3s

## 最佳實踐

1. **使用Server Components**: 優先使用Server Components，只在需要交互時使用Client Components
2. **數據獲取**: 盡可能在Server Component中獲取數據，減少客戶端請求
3. **代碼分割**: 使用dynamic()實現路由級和組件級代碼分割
4. **緩存策略**: 合理使用Next.js的緩存機制和TanStack Query的緩存
5. **SEO優化**: 使用metadata API實現動態SEO標籤
6. **錯誤處理**: 實現全局錯誤邊界和錯誤頁面

## 總結

通過遷移到Next.js，我們將獲得：
- 更優的首次加載性能
- 更好的SEO支持
- 更強的開發體驗
- 更靈活的渲染策略
- 更完善的生態系統支持

這個架構設計為現代化UI升級提供了堅實的基礎，同時保持了與現有系統的兼容性。
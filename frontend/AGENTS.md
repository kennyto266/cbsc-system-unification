# Frontend 项目知识库

**Generated:** 2025-01-03
**System:** React + TypeScript 交易仪表板

## OVERVIEW

React前端系统，提供实时交易数据可视化、策略管理、回测结果展示、用户界面等功能。使用Vite构建，Tailwind CSS样式，支持响应式设计和拖拽式布局。

## STRUCTURE

```
frontend/
├── 📦 配置
│   ├── package.json                                 # 依赖管理
│   ├── vite.config.ts                              # Vite配置
│   ├── tailwind.config.js                          # Tailwind配置
│   └── tsconfig.json                              # TypeScript配置
├── 📂 源代码
│   └── src/                                        # 源代码目录
│       ├── components/                               # 可复用组件
│       │   ├── common/                              # 通用组件
│       │   ├── trading/                             # 交易组件
│       │   └── charts/                              # 图表组件
│       ├── pages/                                   # 页面组件
│       │   ├── Dashboard/                           # 仪表板
│       │   ├── Strategies/                           # 策略管理
│       │   └── Backtest/                            # 回测页面
│       ├── services/                                # API服务
│       │   ├── api.ts                              # API客户端
│       │   ├── auth.ts                             # 认证服务
│       │   └── websocket.ts                        # WebSocket客户端
│       ├── hooks/                                   # 自定义Hooks
│       │   ├── useAuth.ts                          # 认证Hook
│       │   └── useWebSocket.ts                     # WebSocket Hook
│       ├── store/                                   # 状态管理
│       │   └── slices/                             # Redux slices
│       ├── types/                                   # TypeScript类型
│       │   └── index.ts                            # 类型定义
│       ├── utils/                                   # 工具函数
│       └── styles/                                  # 全局样式
├── 📊 资源
│   ├── public/                                     # 静态资源
│   └── assets/                                    # 编译资源
├── 🧪 测试
│   └── tests/                                      # 测试文件
│       ├── unit/                                    # 单元测试
│       ├── integration/                             # 集成测试
│       └── e2e/                                     # E2E测试
└── 📚 文档
    ├── docs/                                       # 文档目录
    └── README.md                                   # 前端指南
```

## WHERE TO LOOK

| Task        | Location                    | Notes                   |
| ----------- | --------------------------- | ----------------------- |
| 通用组件    | `src/components/common/`    | 按钮、输入框、卡片等    |
| 交易组件    | `src/components/trading/`   | 订单簿、交易列表等      |
| 图表组件    | `src/components/charts/`    | K线图、指标图等         |
| 页面组件    | `src/pages/`                | Dashboard、Strategies等 |
| API服务     | `src/services/api.ts`       | REST API客户端          |
| WebSocket   | `src/services/websocket.ts` | 实时数据连接            |
| 状态管理    | `src/store/`                | Redux Toolkit store     |
| 自定义Hooks | `src/hooks/`                | useAuth, useWebSocket等 |
| 类型定义    | `src/types/`                | TypeScript类型          |

## CONVENTIONS

**组件开发：**

- 函数式组件：优先使用函数组件 + Hooks
- TypeScript：严格模式，所有props必须定义类型
- Props解构：直接解构props，避免`props.xxx`
- 命名规范：PascalCase组件名，camelCase变量/函数

**代码风格：**

- 2空格缩进
- 单引号字符串（JSX属性除外）
- 尾随逗号：多行数组/对象必须
- 100字符行限制
- 2空行分隔顶层定义

**导入顺序：**

```typescript
// 1. 标准库
import React, { useState, useEffect } from 'react'

// 2. 第三方库
import { useNavigate } from 'react-router-dom'
import { useDispatch, useSelector } from 'react-redux'

// 3. 内部模块
import { useAuth } from '@/hooks/useAuth'
import type { Strategy } from '@/types/strategy'
```

## ANTI-PATTERNS (THIS PROJECT)

- ❌ **不要**使用`any`类型 - 必须明确定义类型
- ❌ **不要**直接修改props - props是只读的
- ❌ **不要**在组件外使用Hooks - Hooks只能在函数组件内使用
- ❌ **不要**忽略类型错误 - 必须修复所有TypeScript错误
- ❌ **不要**使用内联样式 - 优先使用Tailwind CSS类

## UNIQUE STYLES

**状态管理（Redux Toolkit）：**

```typescript
// 创建slice
import { createSlice, PayloadAction } from '@reduxjs/toolkit'

interface StrategyState {
  strategies: Strategy[]
  loading: boolean
}

const strategySlice = createSlice({
  name: 'strategy',
  initialState,
  reducers: {
    setStrategies: (state, action: PayloadAction<Strategy[]>) => {
      state.strategies = action.payload
    },
    addStrategy: (state, action: PayloadAction<Strategy>) => {
      state.strategies.push(action.payload)
    },
  },
})

export const { setStrategies, addStrategy } = strategySlice.actions
export default strategySlice.reducer
```

**自定义Hooks：**

```typescript
import { useState, useEffect } from 'react'
import type { User } from '@/types'

export function useAuth() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // 加载用户信息...
  }, [])

  return { user, loading, isAuthenticated: !!user }
}
```

**API服务：**

```typescript
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:3004',
  timeout: 10000,
})

// 拦截器：自动添加token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export const strategyAPI = {
  getAll: () => api.get('/api/strategies'),
  create: (data: StrategyCreate) => api.post('/api/strategies', data),
  update: (id: string, data: StrategyUpdate) => api.put(`/api/strategies/${id}`, data),
  delete: (id: string) => api.delete(`/api/strategies/${id}`),
}
```

**WebSocket连接：**

```typescript
import { useEffect, useRef } from 'react'

export function useWebSocket(url: string) {
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    wsRef.current = new WebSocket(url)

    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data)
      // 处理数据...
    }

    return () => {
      wsRef.current?.close()
    }
  }, [url])

  return wsRef.current
}
```

## COMMANDS

```bash
# 开发服务器（端口3000）
npm run dev

# 生产构建
npm run build

# 预览生产构建
npm run preview

# 运行所有测试
npm test

# 运行单元测试
npm run test:unit

# 运行集成测试
npm run test:integration

# 运行E2E测试
npm run test:e2e

# 测试监视模式
npm run test:watch

# 生成测试覆盖率
npm run test:coverage

# 代码检查
npm run lint

# 自动修复lint
npm run lint:fix

# 代码格式化
npm run format

# 检查格式
npm run format:check

# TypeScript类型检查
npm run type-check
```

## NOTES

**关键依赖：**

- React 18+：函数式组件 + Hooks
- TypeScript 5+：严格类型检查
- Vite 5+：构建工具
- Tailwind CSS：实用CSS框架
- Redux Toolkit：状态管理
- React Router DOM：路由
- Axios：HTTP客户端
- Chart.js / Plotly.js：图表库
- React Query：数据获取和缓存

**环境变量：**

```bash
VITE_API_URL=http://localhost:3004
VITE_WS_URL=ws://localhost:3004/ws
VITE_ENABLE_DEBUG=false
```

**路由配置：**

- `/dashboard` - 主仪表板
- `/strategies` - 策略管理
- `/backtest` - 回测页面
- `/login` - 登录页面
- `/register` - 注册页面

**组件库：**

- 优先使用Tailwind CSS类名
- 复杂UI组件可使用Headless UI
- 图表组件：Chart.js (简单) 或 Plotly.js (交互式)

**性能优化：**

- 代码分割：React.lazy + Suspense
- 虚拟滚动：大数据列表使用react-window
- 图片优化：懒加载 + WebP格式
- 防抖/节流：输入、滚动事件

**测试策略：**

- 单元测试：React Testing Library
- 集成测试：MSW (Mock Service Worker)
- E2E测试：Playwright或Cypress

**与后端集成：**

- API base URL：通过环境变量配置
- 认证：JWT存储在localStorage，请求自动添加token
- WebSocket：实时推送交易数据、系统状态
- CORS：后端必须配置允许前端origin

**开发工具：**

- VSCode：推荐使用Volar (Vue) 或 Volar (React)插件
- Chrome DevTools：React DevTools, Redux DevTools
- ESLint + Prettier：代码格式化

**部署：**

- 开发：`npm run dev` (http://localhost:3000)
- 生产：`npm run build` → 部署dist/目录
- Docker：使用Dockerfile构建镜像
- Kubernetes：使用部署配置（k8s/）

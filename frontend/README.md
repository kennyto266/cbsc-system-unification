# CBSC 量化交易策略管理系统 Frontend

## 项目简介

CBSC量化交易策略管理系统的前端应用，基于 React 18 + TypeScript + Vite 构建的现代化企业级前端解决方案。

## 技术栈

- **框架**: React 18 + TypeScript
- **构建工具**: Vite 5
- **状态管理**: Redux Toolkit + RTK Query
- **UI组件库**: Tailwind CSS + Headless UI + Ant Design
- **图表库**: Recharts + Chart.js
- **路由**: React Router v6
- **数据获取**: React Query (TanStack Query)
- **动画**: Framer Motion
- **测试**: Vitest + React Testing Library
- **代码质量**: ESLint + Prettier + Husky

## 快速开始

### 环境要求

- Node.js >= 20.x
- npm >= 10.x

### 安装依赖

```bash
npm install
```

### 开发环境

```bash
npm run dev
```

应用将在 http://localhost:3000 启动

### 构建生产版本

```bash
npm run build
```

### 预览生产构建

```bash
npm run preview
```

## 可用脚本

- `npm run dev` - 启动开发服务器
- `npm run build` - 构建生产版本
- `npm run preview` - 预览生产构建
- `npm run lint` - 运行 ESLint 检查
- `npm run lint:fix` - 自动修复 ESLint 问题
- `npm run type-check` - TypeScript 类型检查
- `npm run test` - 运行测试
- `npm run test:ui` - 运行测试并打开 UI 界面
- `npm run test:coverage` - 运行测试并生成覆盖率报告
- `npm run format` - 格式化代码
- `npm run format:check` - 检查代码格式

## 项目结构

```
frontend/
├── src/
│   ├── components/        # 可复用组件
│   │   ├── auth/         # 认证相关组件
│   │   ├── charts/       # 图表组件
│   │   ├── layout/       # 布局组件
│   │   └── ui/           # 基础UI组件
│   ├── pages/            # 页面组件
│   ├── hooks/            # 自定义Hooks
│   ├── services/         # API服务
│   ├── store/            # Redux store
│   │   └── slices/       # Redux slices
│   ├── types/            # TypeScript类型定义
│   ├── utils/            # 工具函数
│   ├── styles/           # 全局样式
│   ├── assets/           # 静态资源
│   ├── App.tsx           # 主应用组件
│   └── main.tsx          # 应用入口
├── public/               # 公共资源
├── .github/              # GitHub Actions
├── .vscode/              # VS Code配置
└── tests/                # 测试文件
```

## 环境变量

创建 `.env.local` 文件并配置以下变量：

```env
# API配置
VITE_API_BASE_URL=http://localhost:3004/api
VITE_WS_URL=ws://localhost:3004/ws

# 应用配置
VITE_APP_TITLE=CBSC 量化交易策略管理系统
VITE_APP_VERSION=1.0.0

# 功能开关
VITE_ENABLE_WEBSOCKET=true
VITE_ENABLE_ANALYTICS=false

# 环境
VITE_ENVIRONMENT=development
```

## 代码规范

项目使用 ESLint 和 Prettier 进行代码规范管理：

- ESLint：检查代码质量和潜在错误
- Prettier：统一代码格式
- Husky：Git hooks 管理
- lint-staged：提交前代码检查

## 组件开发规范

1. 使用函数式组件和 Hooks
2. 组件名使用 PascalCase
3. 文件名使用 PascalCase（组件）或 camelCase（工具函数）
4. 使用 TypeScript 进行类型约束
5. 遵循单一职责原则
6. 优先使用 Tailwind CSS 进行样式开发

## 提交规范

使用约定式提交格式：

```
type(scope): description

[optional body]

[optional footer(s)]
```

类型（type）：

- feat: 新功能
- fix: 修复
- docs: 文档更新
- style: 代码格式（不影响代码运行的变动）
- refactor: 重构（既不是新增功能，也不是修改bug的代码变动）
- test: 测试相关
- chore: 构建过程或辅助工具的变动

示例：

```bash
feat(dashboard): add performance chart component
fix(auth): resolve login redirect issue
docs(readme): update installation guide
```

## 测试

项目使用 Vitest 进行单元测试和集成测试：

```bash
# 运行所有测试
npm run test

# 监听模式
npm run test -- --watch

# 生成覆盖率报告
npm run test:coverage

# 打开测试UI
npm run test:ui
```

## 部署

### 构建生产版本

```bash
npm run build
```

构建产物将生成在 `dist` 目录下

### Docker 部署

```dockerfile
FROM node:20-alpine as builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 性能优化

- 使用 React 18 的并发特性
- 组件懒加载
- 路由级代码分割
- 图片资源优化
- 使用 Web Workers 处理复杂计算
- 缓存策略优化

## 浏览器支持

- Chrome >= 90
- Firefox >= 88
- Safari >= 14
- Edge >= 90

## 常见问题

### 1. 开发服务器启动失败

确保端口 3000 未被占用，或修改 `vite.config.ts` 中的端口配置

### 2. API 请求失败

检查 `.env.local` 中的 API_BASE_URL 配置是否正确

### 3. TypeScript 类型错误

运行 `npm run type-check` 查看详细的类型错误信息

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证

## 联系方式

- 项目维护者: CBSC开发团队
- 邮箱: dev-team@cbsc.com
- 问题反馈: [GitHub Issues](https://github.com/your-org/cbsc-frontend/issues)

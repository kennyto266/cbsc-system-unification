# CBSC Square UI Integration

现代化的CBSC量化交易策略管理系统前端界面，基于Square-UI设计系统和shadcn/ui组件库构建。

## 🚀 项目特性

- **现代化UI**: 基于Square-UI设计系统和shadcn/ui组件库
- **TypeScript**: 完整的类型安全支持
- **响应式设计**: 支持桌面、平板、移动设备
- **实时数据**: WebSocket实时数据更新
- **暗黑模式**: 内置亮色/暗色主题切换
- **国际化**: 中英文双语支持
- **PWA支持**: 可安装的渐进式Web应用
- **高性能**: Vite构建工具，极速热重载

## 📦 技术栈

- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **样式**: Tailwind CSS + shadcn/ui
- **状态管理**: Redux Toolkit + RTK Query
- **路由**: React Router v6
- **图表**: Recharts + Chart.js + Plotly.js
- **表单**: React Hook Form + Zod
- **测试**: Vitest + Testing Library
- **代码规范**: ESLint + Prettier + Husky

## 🛠️ 开发环境要求

- Node.js >= 18.17.0
- npm >= 9.0.0

## 🚀 快速开始

### 安装依赖

```bash
npm install
```

### 开发环境

```bash
# 启动开发服务器
npm run dev

# 高内存模式（大型项目）
npm run dev:high-mem
```

### 构建生产版本

```bash
npm run build

# 分析构建产物
npm run build:analyze
```

### 预览生产版本

```bash
npm run preview
```

### 代码规范

```bash
# 检查代码规范
npm run lint

# 自动修复
npm run lint:fix

# 类型检查
npm run type-check

# 代码格式化
npm run format

# 检查格式
npm run format:check
```

### 测试

```bash
# 运行测试
npm run test

# 监视模式
npm run test:watch

# 测试覆盖率
npm run test:coverage

# E2E测试
npm run test:e2e
```

### Storybook

```bash
# 启动Storybook
npm run storybook

# 构建Storybook
npm run build-storybook
```

## 📁 项目结构

```
src/
├── components/          # 可复用组件
│   ├── ui/             # 基础UI组件
│   ├── charts/         # 图表组件
│   ├── layout/         # 布局组件
│   └── forms/          # 表单组件
├── pages/              # 页面组件
├── hooks/              # 自定义Hooks
├── services/           # API服务
├── store/              # Redux状态管理
├── utils/              # 工具函数
├── types/              # TypeScript类型定义
├── styles/             # 样式文件
├── assets/             # 静态资源
├── config/             # 配置文件
└── lib/                # 第三方库封装
```

## 🎨 设计系统

### 颜色规范

- **主色调**: CBSC Blue (#0284c7)
- **辅助色**:
  - Success: #10b981
  - Warning: #f59e0b
  - Error: #ef4444
  - Info: #3b82f6

### 间距规范

基于Tailwind CSS的间距系统：
- xs: 0.5rem (8px)
- sm: 0.75rem (12px)
- md: 1rem (16px)
- lg: 1.5rem (24px)
- xl: 2rem (32px)

### 字体规范

- **主字体**: Inter
- **代码字体**: JetBrains Mono
- **中文**: system-ui, sans-serif

## 🔧 配置说明

### 环境变量

创建 `.env` 文件：

```env
# API配置
VITE_API_BASE_URL=http://localhost:3003
VITE_WS_URL=ws://localhost:3003

# 应用配置
VITE_APP_NAME=CBSC Square UI Dashboard
VITE_APP_VERSION=1.0.0

# 功能开关
VITE_ENABLE_ANALYTICS=false
VITE_ENABLE_PWA=true
```

### 代理配置

开发环境下，API请求会自动代理到后端服务器：

```typescript
// vite.config.ts
proxy: {
  '/api': {
    target: 'http://localhost:3003',
    changeOrigin: true,
  },
  '/ws': {
    target: 'ws://localhost:3003',
    ws: true,
  },
}
```

## 📊 性能指标

- **首次加载时间**: < 2s
- **构建时间**: < 30s
- **热重载**: < 1s
- **类型检查**: < 5s

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 提交规范

使用约定式提交规范：

- `feat:` 新功能
- `fix:` 修复bug
- `docs:` 文档更新
- `style:` 代码格式化
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建过程或辅助工具的变动

## 📝 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系方式

- 项目维护者: Claude Code Assistant
- 技术支持: dev-team@cbsc.com
- 问题反馈: [GitHub Issues](https://github.com/your-org/cbsc-square-ui/issues)

## 🙏 致谢

- [shadcn/ui](https://ui.shadcn.com/) - 优秀的组件库
- [Tailwind CSS](https://tailwindcss.com/) - 实用优先的CSS框架
- [Vite](https://vitejs.dev/) - 下一代前端构建工具
- [React](https://reactjs.org/) - 用户界面库
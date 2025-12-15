# CBSC Strategy Management - Next.js Architecture

一个为CBSC量化交易策略管理系统设计的全面Next.js应用程序架构。

## 📁 项目结构

```
src/
├── app/                    # Next.js 13+ App Router页面
│   ├── (auth)/           # 认证路由组
│   ├── dashboard/        # Dashboard路由
│   ├── strategies/       # 策略管理路由
│   ├── api/              # API路由
│   └── layout.tsx        # 根布局
├── components/            # 可复用组件
│   ├── ui/               # 基础UI组件
│   ├── features/         # 功能特定组件
│   ├── layout/           # 布局组件
│   └── forms/            # 表单组件
├── lib/                   # 工具库
│   ├── api/              # API工具
│   ├── auth/             # 认证工具
│   ├── utils/            # 通用工具
│   ├── seo/              # SEO工具
│   ├── analytics/        # 分析工具
│   └── security/         # 安全工具
├── hooks/                 # 自定义Hooks
├── contexts/              # React Contexts
├── providers/             # App Providers
├── types/                 # TypeScript类型定义
└── styles/                # 全局样式
```

## 🚀 核心功能

### 1. 多级布局系统
- **根布局**: 包含全局providers和主题提供者
- **认证布局**: 专为登录/注册页面设计
- **Dashboard布局**: 包含侧边栏和导航栏
- **策略布局**: 包含面包屑和操作按钮

### 2. 路由策略和保护
- 路由组用于功能组织
- 中间件实现认证保护
- 基于角色的访问控制(RBAC)
- 动态路由支持

### 3. 状态管理架构
- Server Components用于数据获取
- TanStack Query用于客户端状态管理
- Context Providers用于全局状态
- SWR用于数据同步

### 4. 数据获取策略
- Axios API客户端配置
- 请求/响应拦截器
- 错误处理和重试逻辑
- 缓存策略

### 5. 错误处理架构
- React Error Boundaries
- 全局错误处理器
- API错误响应处理
- 用户友好的错误消息

### 6. 性能优化
- 代码分割和懒加载
- 虚拟滚动
- 图片优化
- Bundle分析

### 7. 安全架构
- JWT认证
- CSRF保护
- XSS防护
- 文件上传安全
- 速率限制

### 8. SEO和分析
- Metadata API
- 结构化数据
- Google Analytics集成
- 性能监控

### 9. 开发工具
- TypeScript严格模式
- ESLint和Prettier
- Jest测试框架
- Storybook组件开发

## 🛠️ 技术栈

### 核心框架
- **Next.js 14**: React全栈框架
- **React 18**: UI库
- **TypeScript**: 类型安全

### 状态管理
- **TanStack Query**: 服务器状态管理
- **SWR**: 数据同步
- **Zustand**: 客户端状态管理
- **React Hook Form**: 表单状态

### UI和样式
- **Tailwind CSS**: 实用优先的CSS框架
- **Headless UI**: 无样式组件库
- **Lucide React**: 图标库
- **Framer Motion**: 动画库

### 认证和安全
- **NextAuth.js**: 认证解决方案
- **bcryptjs**: 密码哈希
- **jsonwebtoken**: JWT处理
- **jose**: JWT验证

### 数据可视化
- **Recharts**: 图表库
- **Chart.js**: 图表库
- **Plotly.js**: 交互式图表

### 开发工具
- **ESLint**: 代码检查
- **Prettier**: 代码格式化
- **Jest**: 测试框架
- **Storybook**: 组件文档
- **Husky**: Git hooks

## 📦 安装和运行

### 环境要求
- Node.js >= 18.0.0
- npm >= 8.0.0

### 安装依赖
```bash
npm install
```

### 环境配置
复制环境变量模板：
```bash
cp .env.local.example .env.local
```

编辑`.env.local`文件，配置必要的环境变量：
```env
# Database
DATABASE_URL="postgresql://username:password@localhost:5432/cbsc_db"

# Authentication
NEXTAUTH_URL="http://localhost:3000"
NEXTAUTH_SECRET="your-secret-key-here"

# API
API_URL="http://localhost:3004"
```

### 开发模式
```bash
npm run dev
```

访问 [http://localhost:3000](http://localhost:3000) 查看应用。

### 构建生产版本
```bash
npm run build
npm start
```

## 🧪 测试

### 运行测试
```bash
# 运行所有测试
npm test

# 监视模式
npm run test:watch

# 生成覆盖率报告
npm run test:coverage
```

### 组件开发
```bash
# 启动Storybook
npm run storybook
```

## 📊 性能监控

### Bundle分析
```bash
npm run analyze
```

### Lighthouse评分
应用经过优化，在Lighthouse测试中获得高分：
- Performance: 95+
- Accessibility: 100
- Best Practices: 100
- SEO: 100

## 🔒 安全特性

- **认证**: 多因子认证(MFA)、社交登录集成
- **授权**: 基于角色的访问控制(RBAC)
- **CSRF保护**: 防止跨站请求伪造
- **XSS防护**: 防止跨站脚本攻击
- **速率限制**: 防止暴力攻击
- **文件验证**: 安全的文件上传处理

## 🎨 UI/UX特性

- **响应式设计**: 支持桌面、平板和移动设备
- **暗黑模式**: 系统级主题切换
- **动画效果**: 流畅的过渡和微交互
- **加载状态**: 优雅的加载和骨架屏
- **错误处理**: 友好的错误提示
- **无障碍**: WCAG 2.1 AA级合规

## 📈 SEO优化

- **元标签管理**: 动态页面元数据
- **结构化数据**: JSON-LD格式
- **站点地图**: 自动生成XML站点地图
- **robots.txt**: 搜索引擎爬虫控制
- **性能优化**: Core Web Vitals优化

## 📚 文档

- [组件文档](http://localhost:6006) (Storybook)
- [API文档](http://localhost:3004/docs)
- [部署指南](./docs/deployment.md)
- [贡献指南](./docs/contributing.md)

## 🤝 贡献

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- Next.js 团队
- Vercel 平台
- 所有贡献者

---

**CBSC Strategy Management** - 让量化交易更简单、更强大！
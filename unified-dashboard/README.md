# CBSC Unified Dashboard

现代化量化交易策略管理平台，整合CBSC监控系统、策略管理界面和数据分析工具。

## 🚀 项目特性

### 核心功能
- **策略管理**: 完整的策略CRUD操作、执行监控、参数优化
- **实时监控**: WebSocket实时数据推送、系统状态监控、市场行情跟踪
- **数据分析**: 交互式图表、性能分析、风险评估、报告生成
- **用户管理**: 认证授权、权限控制、个人资料管理
- **响应式设计**: 完美支持桌面端和移动端

### 技术亮点
- **React 18 + TypeScript**: 最新的前端技术栈，类型安全
- **Redux Toolkit + RTK Query**: 现代化状态管理和数据获取
- **Ant Design + Tailwind CSS**: 企业级UI组件和原子化CSS
- **Chart.js + Plotly.js**: 丰富的数据可视化图表
- **WebSocket**: 实时数据推送和连接管理
- **PWA支持**: 离线可用、安装到桌面

## 🏗️ 项目架构

```
src/
├── components/          # 可复用组件
│   ├── auth/           # 认证相关组件
│   ├── charts/         # 图表组件
│   ├── dashboard/      # Dashboard组件
│   ├── layout/         # 布局组件
│   ├── strategies/     # 策略组件
│   └── ui/            # 基础UI组件
├── pages/              # 页面组件
│   ├── auth/          # 认证页面
│   ├── dashboard/     # Dashboard页面
│   ├── strategies/    # 策略管理页面
│   ├── monitoring/    # 监控页面
│   ├── analytics/     # 分析页面
│   ├── reports/       # 报告页面
│   ├── settings/      # 设置页面
│   └── profile/       # 个人资料页面
├── hooks/              # 自定义Hooks
├── services/           # 服务层
├── store/              # Redux状态管理
│   ├── api/          # RTK Query APIs
│   └── slices/       # Redux切片
├── styles/             # 样式文件
├── types/              # TypeScript类型定义
└── utils/              # 工具函数
```

## 🛠️ 技术栈

### 前端框架
- **React 18**: 最新版本React，支持并发特性
- **TypeScript 5.2**: 严格的类型检查和开发体验
- **Vite**: 快速的开发构建工具

### 状态管理
- **Redux Toolkit**: 现代化Redux工具集
- **RTK Query**: 数据获取和缓存
- **React Query**: 服务端状态管理

### UI组件
- **Ant Design 5**: 企业级UI组件库
- **Tailwind CSS**: 原子化CSS框架
- **Framer Motion**: 动画库

### 图表可视化
- **Chart.js**: 轻量级图表库
- **Plotly.js**: 科学计算图表
- **Recharts**: React图表组件

### 工具库
- **Day.js**: 日期处理
- **Lodash**: 工具函数库
- **Axios**: HTTP客户端
- **Socket.io**: WebSocket客户端

## 🚀 快速开始

### 环境要求
- Node.js >= 16.0.0
- npm >= 8.0.0

### 安装依赖
```bash
npm install
```

### 开发环境
```bash
npm run dev
```
访问: http://localhost:3000

### 构建生产版本
```bash
npm run build
```

### 预览生产版本
```bash
npm run preview
```

### 代码检查和格式化
```bash
npm run lint        # 代码检查
npm run lint:fix    # 自动修复
npm run format      # 代码格式化
```

### 类型检查
```bash
npm run type-check
```

### 测试
```bash
npm run test          # 运行测试
npm run test:watch    # 监听模式
npm run test:coverage # 测试覆盖率
```

## 🔧 配置说明

### 环境变量
创建`.env.local`文件：
```env
# API配置
VITE_API_BASE_URL=http://localhost:3004/api
VITE_WS_URL=ws://localhost:3004

# 应用配置
VITE_APP_NAME=CBSC Unified Dashboard
VITE_APP_VERSION=1.0.0

# 功能开关
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_PWA=true
VITE_ENABLE_DARK_MODE=true
```

### API代理配置
在`vite.config.ts`中配置API代理：
```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:3004',
      changeOrigin: true,
    },
    '/ws': {
      target: 'ws://localhost:3004',
      ws: true,
    },
  },
}
```

## 📊 功能模块

### 1. Dashboard概览
- 关键指标展示（总资产、收益率、夏普比率等）
- 投资组合表现图表
- 策略分配饼图
- 系统资源监控
- 最新信号和活动

### 2. 策略管理
- 策略列表和搜索过滤
- 策略创建和编辑
- 策略执行和监控
- 参数优化和回测
- 批量操作支持

### 3. 实时监控
- WebSocket实时数据推送
- 系统状态监控
- 市场行情跟踪
- 策略执行日志
- 告警和通知

### 4. 数据分析
- 交互式图表和报表
- 性能指标分析
- 风险评估报告
- 策略对比分析
- 市场情绪分析

### 5. 报告系统
- 自定义报告生成
- 多格式导出（PDF、Excel、JSON）
- 定时报告功能
- 历史报告管理

### 6. 设置管理
- 个人资料设置
- 安全设置（密码、MFA）
- 界面偏好设置
- API密钥管理
- 通知设置

## 🔐 安全特性

- **JWT认证**: 基于Token的认证机制
- **权限控制**: 基于角色的访问控制(RBAC)
- **多因子认证**: 支持TOTP和短信验证
- **安全传输**: HTTPS加密传输
- **输入验证**: 前端和后端双重验证
- **CSRF保护**: 跨站请求伪造防护

## 🎨 UI/UX特性

- **响应式设计**: 适配桌面、平板、手机
- **暗色模式**: 支持明暗主题切换
- **无障碍访问**: WCAG 2.1 AA级别标准
- **国际化支持**: 多语言界面
- **主题定制**: 可配置的颜色和样式
- **动画效果**: 流畅的页面过渡和交互动画

## 📱 PWA特性

- **离线支持**: 基于Service Worker的离线功能
- **桌面安装**: 可安装到桌面应用
- **推送通知**: 支持系统级通知
- **应用图标**: 自定义应用图标和启动画面
- **版本更新**: 自动检测和提示更新

## 🔌 API集成

### 策略管理API (18个端点)
- 策略CRUD操作
- 策略执行和控制
- 参数优化
- 批量操作
- 模板管理

### 监控API
- 系统状态查询
- 实时数据推送
- 告警管理
- 资源监控

### 分析API
- 性能数据查询
- 报告生成
- 数据导出
- 自定义查询

### 用户API
- 认证和授权
- 用户资料管理
- 安全设置
- 偏好配置

## 🚀 部署

### Docker部署
```bash
# 构建镜像
docker build -t cbsc-dashboard .

# 运行容器
docker run -p 3000:3000 cbsc-dashboard
```

### Nginx配置
```nginx
server {
    listen 80;
    server_name dashboard.cbsc.com;

    root /var/www/cbsc-dashboard;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:3004;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📈 性能优化

- **代码分割**: 基于路由的懒加载
- **图片优化**: WebP格式和响应式图片
- **缓存策略**: 浏览器缓存和CDN加速
- **包大小优化**: Tree shaking和压缩
- **预加载**: 关键资源预加载
- **性能监控**: Web Vitals指标监控

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开Pull Request

### 开发规范
- 遵循ESLint和Prettier配置
- 编写TypeScript类型
- 添加单元测试
- 更新文档

## 📄 许可证

本项目采用MIT许可证 - 查看[LICENSE](LICENSE)文件了解详情。

## 📞 支持

- 📧 Email: support@cbsc.com
- 💬 微信群: CBSC技术交流
- 📱 客服电话: 400-123-4567
- 🌐 官网: https://cbsc.com

---

**CBSC Unified Dashboard** - 让量化交易更简单、更智能、更高效！
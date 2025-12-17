# 用户管理系统前端开发指南

## 项目概述

基于现有的CBSC量化交易策略管理系统，搭建企业级用户管理前端系统。

## 技术栈

- **前端框架**: React 18 + TypeScript
- **状态管理**: Redux Toolkit + RTK Query
- **UI组件库**: Tailwind CSS + Headless UI
- **图表库**: Chart.js + Plotly.js
- **构建工具**: Vite
- **测试框架**: Jest + React Testing Library
- **后端API**: FastAPI + SQLAlchemy
- **数据库**: PostgreSQL + Redis
- **部署**: Docker + Kubernetes

## 现有系统集成

### 主系统架构
- **主系统**: CBSC量化交易策略管理系统 (端口3003)
- **技术栈**: FastAPI + Vanilla JavaScript + PostgreSQL + Redis
- **核心功能**: 策略管理、参数优化、回测分析、实时监控

### 集成策略
1. **渐进式集成**: 保持现有系统正常运行，逐步添加用户管理功能
2. **共享基础设施**: 复用现有数据库、缓存、监控系统
3. **API网关**: 统一入口管理和路由分发
4. **认证统一**: 升级现有JWT认证系统

## 开发工作流

### 1. 开发环境启动
```bash
# 启动开发环境
./ai/init.sh

# 手动启动服务
cd src/api && python -m uvicorn main:app --reload --port 3004
cd frontend && npm run dev --port 3000
cd monitoring && python app.py --port 3005
```

### 2. 功能开发流程
1. 查看 `ai/features/` 目录了解详细需求
2. 在 `src/components/` 开发UI组件
3. 在 `src/services/` 开发API服务
4. 在 `src/pages/` 组装页面
5. 编写单元测试和集成测试
6. 更新API文档

### 3. 代码规范
- 使用TypeScript严格模式
- 遵循ESLint和Prettier配置
- 组件使用函数式组件 + Hooks
- API使用RTK Query进行状态管理
- 样式使用Tailwind CSS类名

## 核心功能模块

### 1. 用户认证系统 (P0)
- **多因子认证**: 邮箱、短信、Google Authenticator
- **社交登录**: 微信、Google、GitHub集成
- **单点登录**: SAML 2.0、OAuth 2.0支持
- **权限控制**: RBAC模型、动态权限

**开发指南**: `ai/features/01-user-authentication.md`

### 2. 用户管理仪表板 (P0)
- **用户CRUD**: 完整的用户生命周期管理
- **高级搜索**: 多维度用户搜索和过滤
- **批量操作**: 批量启用/禁用/角色分配
- **实时监控**: 在线用户、活动监控

**开发指南**: `ai/features/02-user-management-dashboard.md`

### 3. 个人中心管理 (P1)
- **资料管理**: 个人信息、头像、联系方式
- **安全设置**: 密码修改、MFA设置、设备管理
- **通知偏好**: 邮件、短信、推送通知设置
- **界面偏好**: 主题、语言、时区设置

**开发指南**: `ai/features/03-user-profile-management.md`

### 4. 用户活动监控 (P1)
- **实时监控**: 在线状态、页面访问、功能使用
- **行为分析**: 用户画像、使用模式、留存分析
- **安全检测**: 异常登录、可疑行为、威胁识别
- **审计日志**: 完整的操作记录和合规报告

**开发指南**: `ai/features/04-user-activity-monitoring.md`

### 5. 系统集成部署 (P0)
- **无缝集成**: 与现有CBSC系统的平滑整合
- **渐进式部署**: 蓝绿部署、金丝雀发布
- **数据迁移**: 现有用户数据的平滑迁移
- **性能优化**: 数据库优化、缓存策略、API性能

**开发指南**: `ai/features/05-system-integration-deployment.md`

## API设计规范

### RESTful API设计
```typescript
// 用户管理API示例
GET    /api/users                    # 用户列表 (分页、过滤)
POST   /api/users                    # 创建用户
GET    /api/users/{id}               # 用户详情
PUT    /api/users/{id}               # 更新用户
DELETE /api/users/{id}               # 删除用户
PATCH  /api/users/{id}/status        # 状态变更

// 认证API示例
POST   /api/auth/login               # 用户登录
POST   /api/auth/logout              # 用户登出
POST   /api/auth/refresh             # Token刷新
POST   /api/auth/register            # 用户注册
```

### 响应格式标准
```typescript
// 成功响应
{
  "success": true,
  "data": {
    // 实际数据
  },
  "message": "操作成功",
  "timestamp": "2025-12-05T10:00:00Z"
}

// 错误响应
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "输入验证失败",
    "details": {
      "field": "email",
      "reason": "邮箱格式不正确"
    }
  },
  "timestamp": "2025-12-05T10:00:00Z"
}
```

## 数据库设计

### 核心表结构
```sql
-- 用户基础信息表
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 角色权限表
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    permissions JSON,
    is_system_role BOOLEAN DEFAULT FALSE
);

-- 用户角色关联表
CREATE TABLE user_roles (
    user_id INTEGER REFERENCES users(id),
    role_id INTEGER REFERENCES roles(id),
    assigned_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, role_id)
);
```

## 安全考虑

### 1. 认证安全
- 使用Argon2id进行密码哈希
- JWT token使用RS256签名
- 实施密码强度要求
- 支持多因子认证

### 2. 授权控制
- 基于角色的访问控制(RBAC)
- API级别的权限验证
- 前端路由权限守卫
- 数据级权限过滤

### 3. 数据保护
- 敏感数据加密存储
- API请求HTTPS传输
- 输入数据验证和清理
- SQL注入防护

## 性能优化

### 1. 前端优化
- 代码分割和懒加载
- 图片资源优化
- 缓存策略实施
- 虚拟滚动大数据列表

### 2. 后端优化
- 数据库查询优化
- Redis缓存策略
- API响应压缩
- 连接池管理

### 3. 网络优化
- CDN静态资源分发
- HTTP/2协议支持
- 请求去重和合并
- 服务端渲染(SSR)

## 测试策略

### 1. 单元测试
```typescript
// 组件测试示例
describe('UserList', () => {
  test('renders user list correctly', () => {
    render(<UserList users={mockUsers} />);
    expect(screen.getByText('John Doe')).toBeInTheDocument();
  });
});
```

### 2. 集成测试
```typescript
// API集成测试示例
describe('User API', () => {
  test('creates new user successfully', async () => {
    const response = await userAPI.createUser(userData);
    expect(response.status).toBe(201);
  });
});
```

### 3. E2E测试
```typescript
// 端到端测试示例
describe('User Management Flow', () => {
  test('admin can create and manage users', async () => {
    await page.goto('/admin/users');
    await page.click('[data-testid="create-user-btn"]');
    // ... 完整的用户操作流程
  });
});
```

## 部署运维

### 1. 环境配置
- **开发环境**: 本地Docker开发
- **测试环境**: Kubernetes集群测试
- **生产环境**: 高可用Kubernetes部署

### 2. CI/CD流程
```yaml
# GitHub Actions示例
name: Deploy User Management
on:
  push:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: npm run test
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to production
        run: ./scripts/deploy.sh
```

### 3. 监控告警
- **应用监控**: Prometheus + Grafana
- **日志聚合**: ELK Stack
- **错误追踪**: Sentry
- **性能监控**: New Relic

## 开发工具

### 1. 推荐IDE配置
```json
// .vscode/settings.json
{
  "typescript.preferences.importModuleSpecifier": "relative",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "emmet.includeLanguages": {
    "typescript": "html",
    "typescriptreact": "html"
  }
}
```

### 2. 调试配置
```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug React App",
      "type": "node",
      "request": "launch",
      "program": "${workspaceFolder}/node_modules/.bin/vite",
      "args": ["--mode", "development"]
    }
  ]
}
```

## 常见问题

### Q: 如何与现有CBSC系统集成？
A: 使用API网关进行路由分发，共享数据库和缓存系统，实施统一的认证机制。

### Q: 如何处理用户数据迁移？
A: 提供数据迁移脚本，支持增量迁移和数据验证，确保平滑过渡。

### Q: 如何保证系统性能？
A: 实施多层缓存策略，数据库查询优化，前端代码分割，CDN加速。

### Q: 如何确保安全合规？
A: 实施完整的安全框架，包括数据加密、权限控制、审计日志、合规检查。

## 文档资源

- **API文档**: `http://localhost:3004/docs`
- **功能需求**: `ai/features/` 目录
- **部署指南**: `docs/deployment/`
- **用户手册**: `docs/user-guide/`

## 联系方式

- **项目维护**: Claude Code Assistant
- **技术支持**: dev-team@cbsc.com
- **安全问题**: security@cbsc.com

---
*最后更新: 2025-12-05*
*版本: User Management System v1.0*
- 每次都要深思,優先用 Claude Code PM 執行任務流程
- 标准 Epic 流程：prd-new → prd-parse → epic-decompose → epic-sync
- 寫做策略管理架构分析报告.md
- keyring 中的有效 token,GITHUB_TOKEN環境變量干擾了GitHub CLI。讓我暫時清除它並使用本地認證

## 文档创建规则

默认情况下，不要创建任何新的说明文档或文档文件。

不要自动生成 http://README.md、设计文档、使用说明、架构说明等。

只有在我明确要求"编写文档 / 生成 README / 写说明文档"时，才允许创建或修改文档。

避免输出与代码无关的说明性文档。
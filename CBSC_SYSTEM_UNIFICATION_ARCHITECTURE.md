# CBSC System Unification Architecture
# CBSC系统统一架构文档

## 📋 概述

本文档描述了CBSC量化交易策略管理系统的统一架构设计，实现了从碎片化服务到统一企业级平台的转换。通过API网关、服务发现、统一认证和监控体系，建立了一个可扩展、高可用的微服务架构。

## 🏗️ 系统架构概览

### 架构原则

1. **统一入口**: 通过API网关提供单一访问点
2. **服务解耦**: 微服务架构，独立部署和扩展
3. **安全第一**: 统一认证授权，多层安全防护
4. **可观测性**: 全链路监控、日志、指标追踪
5. **高可用性**: 负载均衡、故障转移、健康检查
6. **开发友好**: 统一开发环境，简化部署流程

### 技术栈

- **API网关**: FastAPI + Nginx/Traefik
- **容器化**: Docker + Docker Compose
- **数据库**: PostgreSQL + Redis
- **监控**: Prometheus + Grafana + Jaeger
- **日志**: ELK Stack (Elasticsearch + Logstash + Kibana)
- **认证**: JWT + OAuth2
- **前端**: React 18 + TypeScript + Tailwind CSS

## 🌐 服务拓扑图

```
┌─────────────────────────────────────────────────────────────────┐
│                        外部访问层                                │
├─────────────────────────────────────────────────────────────────┤
│  http://localhost:80 (Nginx)                                     │
│  http://localhost:8000 (API Gateway)                            │
│  http://localhost:3000 (Frontend Dashboard)                     │
│  http://localhost:3001 (Unified Dashboard)                      │
│  http://localhost:3002 (Grafana Monitoring)                     │
└─────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────┐
│                      API网关层                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   负载均衡       │  │   路由管理       │  │   认证授权       │ │
│  │   (Nginx)       │  │  (FastAPI)      │  │  (JWT/OAuth2)   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────┐
│                       微服务层                                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │用户管理系统  │ │策略Dashboard│ │  量化系统    │ │ 配置管理服务 │ │
│ │   (3004)    │ │   (3003)    │ │   (8001)    │ │   (3005)    │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────┐
│                       基础设施层                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │ PostgreSQL  │ │    Redis    │ │   文件存储    │ │   消息队列   │ │
│  │  (5432)    │ │  (6379)    │ │   (NFS)     │ │  (RabbitMQ) │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 🔧 核心组件详解

### 1. API网关 (Gateway)

**位置**: `gateway/main.py`, `gateway/config/services.yaml`

**功能**:
- 统一入口点管理
- 智能路由和负载均衡
- 统一认证和授权
- 请求限流和安全防护
- 监控和日志收集

**路由规则**:
```
/api/quant/*      → 量化系统 (8001)
/api/users/*      → 用户管理 (3004)
/api/strategies/* → 策略Dashboard (3003)
/api/config/*     → 配置服务 (3005)
/ws/*             → WebSocket服务
/health           → 健康检查
/metrics          → Prometheus指标
```

**安全特性**:
- JWT令牌验证
- OAuth2授权码模式
- IP白名单机制
- 请求限流保护
- CORS跨域控制

### 2. 用户管理系统

**位置**: `src/api/main.py`

**功能**:
- 用户注册和认证
- 权限管理 (RBAC)
- 用户资料管理
- 会话管理

**用户角色**:
- `admin`: 系统管理员，拥有所有权限
- `analyst`: 量化分析师，策略分析和回测权限
- `user`: 普通用户，基础查看和操作权限
- `viewer`: 只读用户，仅查看权限

**权限体系**:
```yaml
permissions:
  - "*": 所有权限 (admin)
  - "strategies:read": 策略查看
  - "strategies:write": 策略修改
  - "backtest:execute": 回测执行
  - "data:read": 数据访问
  - "profile:read": 个人资料查看
  - "dashboard:access": Dashboard访问
```

### 3. 策略管理Dashboard

**位置**: `frontend/src/components/StrategyDashboard/`

**功能**:
- 策略创建和编辑
- 实时性能监控
- 参数优化界面
- 风险分析展示

**技术特性**:
- React 18 + TypeScript
- Chart.js图表集成
- WebSocket实时更新
- 响应式设计

### 4. 量化分析系统

**位置**: `src/quant/`

**功能**:
- 策略回测引擎
- 参数优化算法
- 风险管理模型
- 数据处理管道

**核心模块**:
- 回测引擎: `src/quant/backtest/`
- 策略库: `src/quant/strategies/`
- 数据适配器: `src/quant/adapters/`
- 风险模型: `src/quant/risk/`

## 🔐 安全架构

### 认证流程

```
用户登录 → JWT生成 → 网关验证 → 服务调用 → 响应返回
    ↓
OAuth2授权 (第三方集成) → 访问令牌 → 资源访问
```

### 权限控制

1. **网关层**: 统一认证和基本权限检查
2. **服务层**: 细粒度权限验证
3. **数据层**: 行级安全过滤

### 安全措施

- 密码强度要求和加密存储
- JWT令牌有效期管理
- 账户锁定机制
- 请求签名验证
- 敏感操作审计日志

## 📊 监控体系

### 指标监控

**Prometheus指标收集**:
- 应用性能指标 (响应时间、吞吐量)
- 系统资源指标 (CPU、内存、磁盘)
- 业务指标 (用户活跃度、策略执行数)
- 错误率和可用性指标

**Grafana仪表板**:
- 系统概览仪表板
- 服务性能仪表板
- 业务指标仪表板
- 告警管理仪表板

### 日志管理

**ELK Stack集成**:
- Elasticsearch: 日志存储和搜索
- Logstash: 日志收集和处理
- Kibana: 日志可视化和分析

**日志格式标准**:
```json
{
  "timestamp": "2025-01-01T12:00:00Z",
  "service": "api-gateway",
  "level": "INFO",
  "message": "Request processed",
  "request_id": "req_123456",
  "user_id": "user_789",
  "duration_ms": 150,
  "status_code": 200
}
```

### 链路追踪

**Jaeger分布式追踪**:
- 请求链路完整追踪
- 服务间调用关系图
- 性能瓶颈识别
- 错误根因分析

## 🚀 部署架构

### 容器编排

**Docker Compose配置**: `docker-compose.cbsc-unified.yml`

**服务编排**:
- 基础设施服务: Redis, PostgreSQL, Nginx
- 核心业务服务: API网关, 微服务
- 监控服务: Prometheus, Grafana, Jaeger
- 日志服务: ELK Stack

### 环境管理

**开发环境**:
```bash
# 启动完整开发环境
./scripts/dev-unified-start.sh  # Linux/Mac
./scripts/dev-unified-start.bat # Windows
```

**生产环境特性**:
- 多实例部署
- 负载均衡配置
- 自动扩缩容
- 滚动更新策略

### 配置管理

**环境变量配置**:
```yaml
# 数据库配置
POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
POSTGRES_USER: cbsc_admin
POSTGRES_DB: cbsc_system

# JWT配置
JWT_SECRET: ${JWT_SECRET}
GATEWAY_SECRET_KEY: ${GATEWAY_SECRET_KEY}

# 监控配置
GRAFANA_PASSWORD: ${GRAFANA_PASSWORD}
```

**服务发现配置**: `gateway/config/services.yaml`

## 📈 性能优化

### 网关优化

- 请求连接池复用
- 响应压缩和缓存
- 异步请求处理
- 智能负载均衡

### 数据库优化

- 连接池配置
- 查询索引优化
- 读写分离
- 分库分表策略

### 缓存策略

- Redis分布式缓存
- 应用级缓存
- CDN静态资源缓存
- 数据库查询缓存

## 🔧 开发工作流

### 本地开发

1. **环境准备**:
   ```bash
   git clone <repository>
   cd CODEX--
   cp .env.example .env
   ```

2. **启动开发环境**:
   ```bash
   ./scripts/dev-unified-start.sh
   ```

3. **访问服务**:
   - API网关: http://localhost:8000
   - 前端Dashboard: http://localhost:3000
   - 监控界面: http://localhost:3002

### 代码规范

- Python: PEP 8 + Black格式化
- TypeScript: ESLint + Prettier
- 提交规范: Conventional Commits
- 代码审查: Pull Request流程

### 测试策略

- 单元测试: pytest + jest
- 集成测试: docker-compose测试环境
- 端到端测试: Playwright自动化
- 性能测试: Locust压力测试

## 🚨 故障处理

### 健康检查

**服务健康端点**:
- `/health`: 基础健康检查
- `/ready`: 就绪状态检查
- `/live`: 存活状态检查

**自动故障恢复**:
- 服务自动重启
- 流量自动切换
- 降级服务机制
- 熔断器保护

### 监控告警

**告警规则**:
- 服务不可用
- 响应时间过长
- 错误率过高
- 资源使用率异常

**通知渠道**:
- 邮件通知
- Slack集成
- 短信告警
- 企业微信通知

## 🔮 未来规划

### 短期目标 (1-3个月)

- [ ] 完善监控系统覆盖
- [ ] 优化性能和稳定性
- [ ] 增强安全防护
- [ ] 完善文档和培训

### 中期目标 (3-6个月)

- [ ] 实现Kubernetes部署
- [ ] 集成CI/CD流水线
- [ ] 添加更多业务服务
- [ ] 实现多租户支持

### 长期目标 (6-12个月)

- [ ] 微服务治理平台
- [ ] 智能运维系统
- [ ] 云原生架构升级
- [ ] 国际化多语言支持

## 📚 相关文档

- [API文档](http://localhost:8000/docs)
- [开发指南](./DEVELOPMENT_GUIDE.md)
- [部署手册](./DEPLOYMENT_MANUAL.md)
- [故障排查](./TROUBLESHOOTING.md)
- [安全规范](./SECURITY_GUIDELINES.md)

## 👥 贡献指南

1. Fork项目仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

**版本**: v2.0.0
**最后更新**: 2025-01-01
**维护者**: CBSC开发团队
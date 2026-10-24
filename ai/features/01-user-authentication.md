# 用户认证与授权系统

## 🎯 功能概述
构建企业级用户认证系统，替代当前基础JWT认证，支持多种认证方式和细粒度权限控制。

## 📋 需求优先级：P0 (核心基础)

## 🔧 功能需求

### 1. 多因子认证 (MFA)
- **邮箱验证**: 基于TOTP的邮箱验证码
- **短信验证**: 集成第三方短信服务
- **Google Authenticator**: QR码设置与验证
- **硬件密钥**: YubiKey等FIDO2支持

### 2. 社交登录集成
- **微信登录**: 微信开放平台OAuth2.0
- **Google登录**: Google OAuth 2.0
- **GitHub登录**: 面向技术用户
- **LinkedIn登录**: 企业用户场景

### 3. 单点登录 (SSO)
- **SAML 2.0**: 企业级SSO支持
- **OAuth 2.0 Provider**: 为第三方应用提供认证
- **JWT刷新机制**: 无感知token续期
- **会话管理**: 多设备登录状态控制

### 4. 角色权限系统
- **RBAC模型**: 基于角色的访问控制
- **动态权限**: 运行时权限调整
- **资源级控制**: API/页面/按钮级别权限
- **权限继承**: 角色层次结构

## 🎨 UI/UX 设计

### 1. 登录界面
- **响应式设计**: 移动端优先
- **暗黑模式**: 系统主题适配
- **品牌化UI**: 与现有系统统一风格
- **多语言支持**: 中英文切换

### 2. 用户仪表板
- **快速概览**: 登录统计、活动记录
- **安全设置**: 密码修改、MFA设置
- **设备管理**: 登录设备查看与控制
- **权限视图**: 当前用户权限展示

## 🔗 API 设计

### 认证端点
```python
POST /api/auth/login          # 用户登录
POST /api/auth/logout         # 用户登出
POST /api/auth/refresh        # Token刷新
POST /api/auth/register       # 用户注册
POST /api/auth/verify-email   # 邮箱验证
POST /api/auth/reset-password # 密码重置
```

### MFA端点
```python
POST /api/auth/mfa/setup      # MFA设置
POST /api/auth/mfa/verify     # MFA验证
DELETE /api/auth/mfa/disable  # 禁用MFA
GET  /api/auth/mfa/backup-codes # 备份码
```

### 社交登录端点
```python
GET  /api/auth/oauth/{provider}  # OAuth授权
POST /api/auth/oauth/callback    # OAuth回调
POST /api/auth/oauth/link        # 关联账号
DELETE /api/auth/oauth/unlink    # 取消关联
```

### 权限管理端点
```python
GET  /api/users/permissions     # 用户权限查询
POST /api/admin/roles           # 角色创建
PUT  /api/admin/roles/{id}      # 角色更新
GET  /api/admin/audit-logs      # 审计日志
```

## 📊 数据模型

### User表扩展
```sql
ALTER TABLE users ADD COLUMN:
- email_verified BOOLEAN DEFAULT FALSE
- phone_number VARCHAR(20)
- phone_verified BOOLEAN DEFAULT FALSE
- mfa_enabled BOOLEAN DEFAULT FALSE
- mfa_secret VARCHAR(32)
- mfa_backup_codes JSON
- last_login_at TIMESTAMP
- login_count INTEGER DEFAULT 0
- failed_login_attempts INTEGER DEFAULT 0
- locked_until TIMESTAMP
```

### Roles表
```sql
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    permissions JSON,
    is_system_role BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### UserRoles关联表
```sql
CREATE TABLE user_roles (
    user_id INTEGER REFERENCES users(id),
    role_id INTEGER REFERENCES roles(id),
    assigned_by INTEGER REFERENCES users(id),
    assigned_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    PRIMARY KEY (user_id, role_id)
);
```

### AuditLog表
```sql
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id INTEGER,
    ip_address INET,
    user_agent TEXT,
    metadata JSON,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 🔒 安全考虑

### 1. 密码安全
- **强度要求**: 最少12位，包含大小写、数字、特殊字符
- **哈希算法**: Argon2id (内存困难函数)
- **盐值管理**: 每个用户独立盐值
- **密码历史**: 防止重复使用旧密码

### 2. 会话安全
- **JWT签名**: RS256非对称加密
- **Token有效期**: Access token 15分钟，Refresh token 7天
- **设备指纹**: 基于浏览器特征的设备识别
- **异常检测**: 异地登录、频繁失败等

### 3. 防护措施
- **速率限制**: 登录尝试、API调用频率限制
- **CSRF保护**: Double Submit Cookie模式
- **XSS防护**: Content Security Policy
- **SQL注入防护**: 参数化查询

## 🚀 集成策略

### 1. 渐进式迁移
- **Phase 1**: 保持现有认证，添加新用户表结构
- **Phase 2**: 实现MFA和社交登录
- **Phase 3**: 完全切换到新认证系统
- **Phase 4**: 添加SSO和企业功能

### 2. 向后兼容
- **Token升级**: 现有JWT用户自动迁移
- **API版本**: v1认证API继续支持
- **配置迁移**: 现有users_db配置文件迁移
- **数据同步**: 用户数据平滑转移

## 📈 性能指标

### 1. 认证性能
- **登录响应**: < 200ms (不含MFA)
- **Token验证**: < 10ms
- **权限检查**: < 5ms
- **并发用户**: 支持1000+同时在线

### 2. 可用性指标
- **系统可用性**: 99.9%
- **认证成功率**: 99.5%
- **MFA成功率**: 98%
- **故障恢复**: < 30秒

## 🧪 测试策略

### 1. 单元测试
- **认证逻辑**: 密码验证、Token生成
- **权限检查**: 各种权限场景测试
- **MFA流程**: 设置、验证、恢复流程
- **安全漏洞**: 常见攻击测试

### 2. 集成测试
- **OAuth流程**: 各第三方提供商
- **数据库操作**: 用户CRUD操作
- **API端点**: 完整认证流程
- **会话管理**: 多设备登录场景

### 3. 渗透测试
- **暴力破解**: 密码猜测防护
- **会话劫持**: Token安全测试
- **权限提升**: 角色权限绕过测试
- **数据泄露**: 敏感信息保护

## 📋 验收标准

### 功能验收
- [ ] 支持邮箱+密码登录
- [ ] 实现MFA功能
- [ ] 集成至少2个社交登录
- [ ] 完整的角色权限系统
- [ ] 审计日志记录

### 性能验收
- [ ] 登录响应时间 < 200ms
- [ ] 支持1000+并发用户
- [ ] 99.9%系统可用性
- [ ] 99.5%认证成功率

### 安全验收
- [ ] 通过安全渗透测试
- [ ] 符合OWASP安全标准
- [ ] 实现所有防护措施
- [ ] 完整审计功能

## 🎯 成功指标

### 业务指标
- **用户转化率**: 注册到首次使用 > 80%
- **用户留存率**: 7天留存 > 60%
- **支持工单**: 认证相关问题 < 5%
- **用户满意度**: NPS评分 > 8

### 技术指标
- **系统稳定性**: 无重大认证故障
- **性能表现**: 满足所有SLA要求
- **安全合规**: 通过所有安全审计
- **代码质量**: 测试覆盖率 > 90%
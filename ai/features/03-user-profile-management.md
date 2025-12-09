# 用户个人中心管理

## 🎯 功能概述
为终端用户提供完整的个人资料管理、偏好设置和安全配置功能，提升用户体验和账户安全性。

## 📋 需求优先级：P1 (高优先级)

## 🔧 功能需求

### 1. 个人资料管理
- **基本信息编辑**: 用户名、头像、个人简介
- **联系方式**: 邮箱、手机号码、地址信息
- **职业信息**: 公司、职位、部门、专业技能
- **社交链接**: LinkedIn、GitHub、个人网站等
- **隐私设置**: 信息可见性控制

### 2. 账户安全设置
- **密码管理**: 密码修改、强度检测、历史记录
- **多因子认证**: MFA设备管理、备份码
- **登录管理**: 活跃会话、设备管理、异常登录
- **安全日志**: 登录记录、重要操作日志
- **安全通知**: 邮件/短信提醒设置

### 3. 通知偏好设置
- **邮件通知**: 系统通知、安全提醒、营销邮件
- **短信通知**: 重要验证码、安全告警
- **推送通知**: 浏览器推送、移动端推送
- **通知频率**: 即时、每日汇总、每周汇总
- **通知内容**: 自定义通知模板

### 4. 界面偏好设置
- **主题设置**: 亮色/暗色/自动切换
- **语言设置**: 中文/英文界面语言
- **时区设置**: 本地时区、时间格式
- **界面布局**: 侧边栏位置、表格密度
- **图表设置**: 默认图表类型、颜色主题

## 🎨 UI/UX 设计

### 1. 导航结构
```typescript
// 个人中心导航菜单
const profileNavigation = [
  {
    key: 'overview',
    label: '概览',
    icon: 'User',
    path: '/profile/overview'
  },
  {
    key: 'personal-info',
    label: '个人信息',
    icon: 'Edit',
    path: '/profile/personal'
  },
  {
    key: 'security',
    label: '安全设置',
    icon: 'Shield',
    path: '/profile/security'
  },
  {
    key: 'notifications',
    label: '通知设置',
    icon: 'Bell',
    path: '/profile/notifications'
  },
  {
    key: 'preferences',
    label: '偏好设置',
    icon: 'Settings',
    path: '/profile/preferences'
  },
  {
    key: 'activity',
    label: '活动日志',
    icon: 'Clock',
    path: '/profile/activity'
  }
];
```

### 2. 概览页面设计
```typescript
// 个人概览页布局
const ProfileOverview = () => (
  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
    <div className="md:col-span-1">
      <UserProfileCard />
      <QuickActions />
    </div>
    <div className="md:col-span-2 space-y-6">
      <RecentActivity />
      <SecurityStatus />
      <NotificationSummary />
    </div>
  </div>
);
```

### 3. 表单设计模式
```typescript
// 分步表单组件
const ProfileForm = ({ section, onSave }) => {
  const [formData, setFormData] = useState(initialData);
  const [validation, setValidation] = useState({});
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm(formData)) return;

    setSaving(true);
    try {
      await onSave(formData);
      showSuccessToast('保存成功');
    } catch (error) {
      showErrorToast('保存失败');
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <FormField label="用户名" required>
        <Input
          value={formData.username}
          onChange={(v) => setFormData({...formData, username: v})}
          error={validation.username}
        />
      </FormField>
      {/* 更多表单字段 */}
      <FormActions>
        <Button type="submit" loading={saving}>
          保存更改
        </Button>
        <Button type="button" variant="outline" onClick={() => resetForm()}>
          取消
        </Button>
      </FormActions>
    </form>
  );
};
```

## 🔗 API 设计

### 个人资料端点
```python
GET    /api/profile                    # 获取个人资料
PUT    /api/profile                    # 更新个人资料
PATCH  /api/profile/avatar            # 上传头像
DELETE /api/profile/avatar            # 删除头像
GET    /api/profile/public/{userId}   # 获取公开资料
```

### 安全设置端点
```python
GET    /api/profile/security          # 获取安全设置
PUT    /api/profile/security/password # 修改密码
POST   /api/profile/security/mfa      # 设置MFA
DELETE /api/profile/security/mfa      # 禁用MFA
GET    /api/profile/security/sessions # 获取活跃会话
DELETE /api/profile/security/sessions/{sessionId} # 删除会话
```

### 通知设置端点
```python
GET    /api/profile/notifications     # 获取通知设置
PUT    /api/profile/notifications     # 更新通知设置
POST   /api/profile/notifications/test # 测试通知发送
GET    /api/profile/notifications/history # 通知历史
```

### 偏好设置端点
```python
GET    /api/profile/preferences       # 获取偏好设置
PUT    /api/profile/preferences       # 更新偏好设置
POST   /api/profile/preferences/reset # 重置默认设置
GET    /api/profile/preferences/export # 导出设置
POST   /api/profile/preferences/import # 导入设置
```

### 活动日志端点
```python
GET    /api/profile/activity          # 获取活动日志
GET    /api/profile/activity/export   # 导出活动日志
DELETE /api/profile/activity/clear    # 清除历史日志
```

## 📊 数据模型

### UserProfiles表扩展
```sql
CREATE TABLE user_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) UNIQUE,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    avatar_url VARCHAR(255),
    bio TEXT,
    phone VARCHAR(20),
    address TEXT,
    company VARCHAR(100),
    job_title VARCHAR(100),
    department VARCHAR(100),
    website VARCHAR(255),
    linkedin VARCHAR(255),
    github VARCHAR(255),
    privacy_settings JSON,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### UserPreferences表
```sql
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) UNIQUE,
    theme VARCHAR(20) DEFAULT 'light',
    language VARCHAR(10) DEFAULT 'zh-CN',
    timezone VARCHAR(50) DEFAULT 'Asia/Shanghai',
    date_format VARCHAR(20) DEFAULT 'YYYY-MM-DD',
    time_format VARCHAR(10) DEFAULT '24h',
    layout_settings JSON,
    chart_settings JSON,
    notification_settings JSON,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### UserSessions表
```sql
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    session_token VARCHAR(255) UNIQUE,
    device_info JSON,
    ip_address INET,
    user_agent TEXT,
    last_activity TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

### NotificationSettings表
```sql
CREATE TABLE notification_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) UNIQUE,
    email_notifications JSON,
    sms_notifications JSON,
    push_notifications JSON,
    frequency_settings JSON,
    content_preferences JSON,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## 🎨 组件实现

### 1. 头像上传组件
```typescript
const AvatarUpload = ({ currentAvatar, onUpload }) => {
  const [uploading, setUploading] = useState(false);
  const [preview, setPreview] = useState(currentAvatar);

  const handleFileSelect = async (file) => {
    if (!file) return;

    // 验证文件类型和大小
    if (!file.type.startsWith('image/')) {
      showErrorToast('请选择图片文件');
      return;
    }

    if (file.size > 5 * 1024 * 1024) { // 5MB
      showErrorToast('图片大小不能超过5MB');
      return;
    }

    // 生成预览
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target.result);
    reader.readAsDataURL(file);

    // 上传文件
    setUploading(true);
    try {
      const result = await onUpload(file);
      setPreview(result.url);
      showSuccessToast('头像更新成功');
    } catch (error) {
      showErrorToast('头像上传失败');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="flex flex-col items-center space-y-4">
      <div className="relative">
        <Avatar
          size="xl"
          src={preview}
          alt="用户头像"
          className="border-4 border-white shadow-lg"
        />
        <label htmlFor="avatar-upload" className="absolute bottom-0 right-0">
          <Button
            type="button"
            size="sm"
            variant="primary"
            className="rounded-full"
            loading={uploading}
          >
            <Camera className="w-4 h-4" />
          </Button>
        </label>
        <input
          id="avatar-upload"
          type="file"
          className="hidden"
          accept="image/*"
          onChange={(e) => handleFileSelect(e.target.files[0])}
        />
      </div>
      <p className="text-sm text-gray-500">
        支持 JPG、PNG 格式，文件大小不超过 5MB
      </p>
    </div>
  );
};
```

### 2. 密码强度检测组件
```typescript
const PasswordStrengthIndicator = ({ password }) => {
  const calculateStrength = (pwd) => {
    let score = 0;
    const checks = {
      length: pwd.length >= 8,
      uppercase: /[A-Z]/.test(pwd),
      lowercase: /[a-z]/.test(pwd),
      numbers: /\d/.test(pwd),
      special: /[!@#$%^&*(),.?":{}|<>]/.test(pwd)
    };

    score = Object.values(checks).filter(Boolean).length;

    return {
      score,
      level: score <= 2 ? 'weak' : score <= 4 ? 'medium' : 'strong',
      checks
    };
  };

  const { score, level, checks } = calculateStrength(password);

  const strengthConfig = {
    weak: { color: 'bg-red-500', text: '弱', width: '25%' },
    medium: { color: 'bg-yellow-500', text: '中', width: '60%' },
    strong: { color: 'bg-green-500', text: '强', width: '100%' }
  };

  const config = strengthConfig[level];

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">密码强度</span>
        <span className={`text-sm font-medium ${
          level === 'weak' ? 'text-red-500' :
          level === 'medium' ? 'text-yellow-500' : 'text-green-500'
        }`}>
          {config.text}
        </span>
      </div>

      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={`${config.color} h-2 rounded-full transition-all duration-300`}
          style={{ width: config.width }}
        />
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className={`flex items-center ${checks.length ? 'text-green-600' : 'text-gray-400'}`}>
          <Check className="w-3 h-3 mr-1" />
          至少8个字符
        </div>
        <div className={`flex items-center ${checks.uppercase ? 'text-green-600' : 'text-gray-400'}`}>
          <Check className="w-3 h-3 mr-1" />
          包含大写字母
        </div>
        <div className={`flex items-center ${checks.lowercase ? 'text-green-600' : 'text-gray-400'}`}>
          <Check className="w-3 h-3 mr-1" />
          包含小写字母
        </div>
        <div className={`flex items-center ${checks.numbers ? 'text-green-600' : 'text-gray-400'}`}>
          <Check className="w-3 h-3 mr-1" />
          包含数字
        </div>
        <div className={`flex items-center ${checks.special ? 'text-green-600' : 'text-gray-400'}`}>
          <Check className="w-3 h-3 mr-1" />
          包含特殊字符
        </div>
      </div>
    </div>
  );
};
```

### 3. 通知设置组件
```typescript
const NotificationSettings = () => {
  const [settings, setSettings] = useState({
    email: {
      security: true,
      marketing: false,
      updates: true,
      digest: 'weekly'
    },
    push: {
      enabled: true,
      security: true,
      trades: false,
      alerts: true
    },
    sms: {
      enabled: false,
      security: true,
      verification: true
    }
  });

  const handleSettingChange = (category, setting, value) => {
    setSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [setting]: value
      }
    }));
  };

  return (
    <div className="space-y-6">
      <Section>
        <SectionTitle>邮件通知</SectionTitle>
        <div className="space-y-4">
          <Toggle
            label="安全提醒"
            description="账户安全相关的重要通知"
            checked={settings.email.security}
            onChange={(checked) => handleSettingChange('email', 'security', checked)}
          />
          <Toggle
            label="产品更新"
            description="新功能和产品改进通知"
            checked={settings.email.updates}
            onChange={(checked) => handleSettingChange('email', 'updates', checked)}
          />
          <Toggle
            label="营销邮件"
            description="优惠活动和推广信息"
            checked={settings.email.marketing}
            onChange={(checked) => handleSettingChange('email', 'marketing', checked)}
          />
          <Select
            label="摘要频率"
            value={settings.email.digest}
            onChange={(value) => handleSettingChange('email', 'digest', value)}
            options={[
              { value: 'daily', label: '每日摘要' },
              { value: 'weekly', label: '每周摘要' },
              { value: 'never', label: '不发送' }
            ]}
          />
        </div>
      </Section>

      <Section>
        <SectionTitle>浏览器推送</SectionTitle>
        <div className="space-y-4">
          <Toggle
            label="启用推送通知"
            description="在浏览器中接收实时通知"
            checked={settings.push.enabled}
            onChange={(checked) => handleSettingChange('push', 'enabled', checked)}
          />
          <Toggle
            label="交易提醒"
            description="策略信号和执行通知"
            checked={settings.push.trades}
            onChange={(checked) => handleSettingChange('push', 'trades', checked)}
          />
        </div>
      </Section>
    </div>
  );
};
```

## 🔒 安全考虑

### 1. 数据验证
```typescript
// 输入验证中间件
const validateProfileData = (data) => {
  const schema = Joi.object({
    username: Joi.string().alphanum().min(3).max(30),
    email: Joi.string().email(),
    phone: Joi.string().pattern(/^[+]?[\d\s-()]+$/),
    website: Joi.string().uri(),
  });

  return schema.validate(data);
};
```

### 2. 权限控制
```typescript
// 用户只能修改自己的资料
const profileGuard = async (req, res, next) => {
  const { userId } = req.params;
  const currentUser = req.user;

  if (userId !== currentUser.id && !currentUser.hasPermission('admin')) {
    return res.status(403).json({ error: '无权访问他人资料' });
  }

  next();
};
```

### 3. 敏感操作确认
```typescript
// 敏感操作需要二次确认
const SensitiveOperation = ({ children, onConfirm, title, description }) => {
  const [showConfirm, setShowConfirm] = useState(false);

  const handleConfirm = async () => {
    const confirmed = await confirm({
      title,
      description,
      confirmText: '确认操作',
      cancelText: '取消'
    });

    if (confirmed) {
      await onConfirm();
    }
  };

  return (
    <>
      <div onClick={() => setShowConfirm(true)}>
        {children}
      </div>
      {showConfirm && (
        <ConfirmationDialog
          title={title}
          description={description}
          onConfirm={handleConfirm}
          onCancel={() => setShowConfirm(false)}
        />
      )}
    </>
  );
};
```

## 📱 移动端优化

### 1. 响应式布局
```typescript
const MobileProfileLayout = ({ children }) => (
  <div className="min-h-screen bg-gray-50">
    <MobileHeader title="个人中心" />
    <div className="pb-20">
      {children}
    </div>
    <MobileNavigation />
  </div>
);
```

### 2. 触摸优化
```scss
// 移动端触摸优化
.profile-section {
  @apply p-4 -mx-4;

  &:active {
    @apply bg-gray-100;
  }
}

.touch-target {
  @apply min-h-[44px] min-w-[44px] flex items-center justify-center;
}
```

## 🧪 测试策略

### 1. 表单验证测试
```typescript
describe('Profile Form Validation', () => {
  test('validates email format', () => {
    const invalidEmail = 'invalid-email';
    const { error } = validateProfileData({ email: invalidEmail });
    expect(error).toBeDefined();
  });

  test('validates phone number format', () => {
    const invalidPhone = 'abc123';
    const { error } = validateProfileData({ phone: invalidPhone });
    expect(error).toBeDefined();
  });
});
```

### 2. 安全功能测试
```typescript
describe('Security Features', () => {
  test('password strength indicator works correctly', () => {
    const weakPassword = '123';
    const { level } = calculatePasswordStrength(weakPassword);
    expect(level).toBe('weak');
  });

  test('MFA setup process works', async () => {
    const result = await enableMFA(userId);
    expect(result).toHaveProperty('secret');
    expect(result).toHaveProperty('qrCode');
  });
});
```

## 📋 验收标准

### 功能验收
- [ ] 完整的个人资料编辑功能
- [ ] 头像上传和裁剪功能
- [ ] 密码修改和强度检测
- [ ] MFA设置和管理
- [ ] 通知偏好设置
- [ ] 界面主题切换
- [ ] 活动日志查看

### 用户体验验收
- [ ] 响应式设计适配
- [ ] 无障碍访问支持
- [ ] 操作反馈及时
- [ ] 错误提示清晰
- [ ] 加载状态明确

### 安全验收
- [ ] 数据输入验证
- [ ] 权限控制正确
- [ ] 敏感操作确认
- [ ] 会话管理安全
- [ ] 审计日志完整

## 🎯 成功指标

### 用户满意度
- **功能使用率**: 80%用户使用个人中心功能
- **完成率**: 资料完善完成率 > 60%
- **易用性评分**: 用户满意度 > 8.0

### 系统性能
- **页面加载**: 个人中心页面加载 < 1.5秒
- **操作响应**: 设置保存响应时间 < 500ms
- **文件上传**: 头像上传成功率 > 95%

### 安全指标
- **安全事件**: 账户安全问题减少 > 70%
- **MFA启用率**: 多因子认证启用率 > 40%
- **密码强度**: 强密码使用率 > 80%
# 个人用户设置管理

## 🎯 功能概述
为个人使用者提供完整的系统设置管理功能，包括安全设置、通知偏好、界面主题和系统配置。

## 📋 需求优先级：P1 (个人配置)

## 🔧 功能需求

### 1. 安全设置
- **密码管理**: 修改密码、密码强度要求
- **登录记录**: 查看最近登录历史
- **设备管理**: 管理信任的登录设备
- **双重验证**: 简单的邮箱验证选项

### 2. 通知偏好
- **邮件通知**: 系统通知、安全提醒
- **浏览器通知**: 重要事件的桌面提醒
- **通知频率**: 即时通知或每日汇总
- **通知类型**: 可自定义的通知开关

### 3. 界面设置
- **主题切换**: 亮色/暗色/自动主题
- **语言设置**: 中文/英文界面
- **时区配置**: 本地时区设置
- **布局偏好**: 紧凑/舒适布局选项

### 4. 系统配置
- **数据备份**: 个人数据导出功能
- **隐私设置**: 数据可见性控制
- **性能优化**: 缓存清理和性能设置
- **关于信息**: 系统版本和更新信息

## 🎨 UI/UX 设计

### 1. 设置页面布局
```typescript
const UserSettings = () => {
  const [activeTab, setActiveTab] = useState('security');

  const tabs = [
    { id: 'security', label: '安全设置', icon: 'Shield' },
    { id: 'notifications', label: '通知设置', icon: 'Bell' },
    { id: 'appearance', label: '界面设置', icon: 'Palette' },
    { id: 'system', label: '系统配置', icon: 'Settings' }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">设置</h1>
          <p className="mt-2 text-gray-600">管理您的账户和系统偏好设置</p>
        </div>

        <div className="bg-white shadow rounded-lg">
          {/* 标签导航 */}
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center px-6 py-3 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon name={tab.icon} className="w-5 h-5 mr-2" />
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          {/* 内容区域 */}
          <div className="p-6">
            {activeTab === 'security' && <SecuritySettings />}
            {activeTab === 'notifications' && <NotificationSettings />}
            {activeTab === 'appearance' && <AppearanceSettings />}
            {activeTab === 'system' && <SystemSettings />}
          </div>
        </div>
      </div>
    </div>
  );
};
```

### 2. 安全设置组件
```typescript
const SecuritySettings = () => {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const handlePasswordChange = async (e) => {
    e.preventDefault();

    if (newPassword !== confirmPassword) {
      showToast('新密码和确认密码不匹配', 'error');
      return;
    }

    if (newPassword.length < 8) {
      showToast('密码长度至少8位', 'error');
      return;
    }

    try {
      await updatePassword(currentPassword, newPassword);
      showToast('密码修改成功', 'success');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (error) {
      showToast('密码修改失败', 'error');
    }
  };

  return (
    <div className="space-y-8">
      {/* 密码修改 */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">修改密码</h3>
        <form onSubmit={handlePasswordChange} className="space-y-4 max-w-md">
          <div>
            <label className="block text-sm font-medium text-gray-700">当前密码</label>
            <Input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">新密码</label>
            <Input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
            />
            <PasswordStrengthIndicator password={newPassword} />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">确认新密码</label>
            <Input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />
          </div>

          <Button type="submit">修改密码</Button>
        </form>
      </div>

      {/* 登录记录 */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">登录记录</h3>
        <LoginHistory />
      </div>

      {/* 设备管理 */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">设备管理</h3>
        <DeviceManagement />
      </div>
    </div>
  );
};

// 登录历史组件
const LoginHistory = () => {
  const [loginHistory, setLoginHistory] = useState([]);

  useEffect(() => {
    fetchLoginHistory().then(setLoginHistory);
  }, []);

  return (
    <div className="max-w-2xl">
      <div className="bg-gray-50 rounded-lg">
        {loginHistory.map((login) => (
          <div key={login.id} className="p-4 border-b border-gray-200 last:border-b-0">
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center space-x-2">
                  <Icon name="MapPin" className="w-4 h-4 text-gray-400" />
                  <span className="text-sm font-medium text-gray-900">
                    {login.location || '未知位置'}
                  </span>
                </div>
                <div className="flex items-center space-x-4 mt-1 text-xs text-gray-500">
                  <span>{login.ip_address}</span>
                  <span>{login.device}</span>
                  <span>{formatRelativeTime(login.timestamp)}</span>
                </div>
              </div>
              <div className={`flex items-center space-x-1 text-xs ${
                login.success ? 'text-green-600' : 'text-red-600'
              }`}>
                <Icon name={login.success ? 'CheckCircle' : 'XCircle'} />
                <span>{login.success ? '成功' : '失败'}</span>
              </div>
            </div>
          </div>
        ))}
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
      system_alerts: true,
      security_alerts: true,
      trade_alerts: false,
      weekly_summary: true
    },
    browser: {
      enabled: false,
      trade_alerts: true,
      system_alerts: true
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

  const saveSettings = async () => {
    try {
      await updateNotificationSettings(settings);
      showToast('通知设置已保存', 'success');
    } catch (error) {
      showToast('保存失败', 'error');
    }
  };

  return (
    <div className="space-y-8">
      {/* 邮件通知 */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">邮件通知</h3>
        <div className="space-y-4 max-w-md">
          <Toggle
            label="系统通知"
            description="系统更新和维护通知"
            checked={settings.email.system_alerts}
            onChange={(checked) => handleSettingChange('email', 'system_alerts', checked)}
          />
          <Toggle
            label="安全提醒"
            description="登录异常和安全事件"
            checked={settings.email.security_alerts}
            onChange={(checked) => handleSettingChange('email', 'security_alerts', checked)}
          />
          <Toggle
            label="交易提醒"
            description="策略执行和交易结果"
            checked={settings.email.trade_alerts}
            onChange={(checked) => handleSettingChange('email', 'trade_alerts', checked)}
          />
          <Toggle
            label="每周汇总"
            description="每周系统使用情况汇总"
            checked={settings.email.weekly_summary}
            onChange={(checked) => handleSettingChange('email', 'weekly_summary', checked)}
          />
        </div>
      </div>

      {/* 浏览器通知 */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">浏览器通知</h3>
        <div className="space-y-4 max-w-md">
          <Toggle
            label="启用桌面通知"
            description="在浏览器中显示实时通知"
            checked={settings.browser.enabled}
            onChange={async (checked) => {
              if (checked) {
                const permission = await Notification.requestPermission();
                if (permission !== 'granted') {
                  showToast('请允许浏览器通知权限', 'error');
                  return;
                }
              }
              handleSettingChange('browser', 'enabled', checked);
            }}
          />
          <Toggle
            label="交易提醒"
            description="重要交易事件的桌面提醒"
            checked={settings.browser.trade_alerts}
            onChange={(checked) => handleSettingChange('browser', 'trade_alerts', checked)}
            disabled={!settings.browser.enabled}
          />
        </div>
      </div>

      {/* 保存按钮 */}
      <div className="pt-4">
        <Button onClick={saveSettings}>保存设置</Button>
      </div>
    </div>
  );
};
```

### 4. 界面设置组件
```typescript
const AppearanceSettings = () => {
  const [theme, setTheme] = useState('light');
  const [language, setLanguage] = useState('zh-CN');
  const [timezone, setTimezone] = useState('Asia/Shanghai');
  const [layout, setLayout] = useState('comfortable');

  const themes = [
    { value: 'light', label: '亮色主题', preview: 'bg-white border-gray-200' },
    { value: 'dark', label: '暗色主题', preview: 'bg-gray-900 border-gray-700' },
    { value: 'auto', label: '自动主题', preview: 'bg-gradient-to-r from-white to-gray-900' }
  ];

  return (
    <div className="space-y-8">
      {/* 主题设置 */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">主题设置</h3>
        <div className="grid grid-cols-3 gap-4 max-w-lg">
          {themes.map((themeOption) => (
            <button
              key={themeOption.value}
              onClick={() => setTheme(themeOption.value)}
              className={`relative p-4 rounded-lg border-2 transition-all ${
                theme === themeOption.value
                  ? 'border-indigo-500 ring-2 ring-indigo-200'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className={`h-16 rounded ${themeOption.preview} mb-2`} />
              <div className="text-sm font-medium text-gray-900">{themeOption.label}</div>
              {theme === themeOption.value && (
                <div className="absolute top-2 right-2">
                  <Icon name="CheckCircle" className="w-5 h-5 text-indigo-600" />
                </div>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* 语言设置 */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">语言设置</h3>
        <div className="max-w-md">
          <Select
            value={language}
            onChange={setLanguage}
            options={[
              { value: 'zh-CN', label: '简体中文' },
              { value: 'en-US', label: 'English' }
            ]}
          />
        </div>
      </div>

      {/* 时区设置 */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">时区设置</h3>
        <div className="max-w-md">
          <Select
            value={timezone}
            onChange={setTimezone}
            options={[
              { value: 'Asia/Shanghai', label: '北京时间 (GMT+8)' },
              { value: 'America/New_York', label: '纽约时间 (GMT-5)' },
              { value: 'Europe/London', label: '伦敦时间 (GMT+0)' }
            ]}
          />
        </div>
      </div>

      {/* 布局设置 */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">布局设置</h3>
        <div className="space-y-3 max-w-md">
          {[
            { value: 'compact', label: '紧凑布局', description: '显示更多内容，节省空间' },
            { value: 'comfortable', label: '舒适布局', description: '内容宽松，阅读体验好' }
          ].map((layoutOption) => (
            <label key={layoutOption.value} className="flex items-start space-x-3">
              <input
                type="radio"
                name="layout"
                value={layoutOption.value}
                checked={layout === layoutOption.value}
                onChange={(e) => setLayout(e.target.value)}
                className="mt-1"
              />
              <div>
                <div className="font-medium text-gray-900">{layoutOption.label}</div>
                <div className="text-sm text-gray-500">{layoutOption.description}</div>
              </div>
            </label>
          ))}
        </div>
      </div>
    </div>
  );
};
```

## 🔗 API 设计

### 设置管理API
```python
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/api/settings", tags=["settings"])

@router.get("/security")
async def get_security_settings(current_user: User = Depends(get_current_user)):
    """获取安全设置"""
    return {
        "email": current_user.email,
        "phone": current_user.phone,
        "mfa_enabled": current_user.mfa_enabled,
        "last_password_change": current_user.last_password_change,
        "login_history": await get_login_history(current_user.id, limit=10)
    }

@router.get("/notifications")
async def get_notification_settings(current_user: User = Depends(get_current_user)):
    """获取通知设置"""
    settings = await get_user_notification_settings(current_user.id)
    return settings

@router.put("/notifications")
async def update_notification_settings(
    settings: NotificationSettings,
    current_user: User = Depends(get_current_user)
):
    """更新通知设置"""
    await save_notification_settings(current_user.id, settings)
    return {"message": "通知设置已更新"}

@router.get("/appearance")
async def get_appearance_settings(current_user: User = Depends(get_current_user)):
    """获取界面设置"""
    return {
        "theme": current_user.theme,
        "language": current_user.language,
        "timezone": current_user.timezone,
        "layout": current_user.layout
    }

@router.put("/appearance")
async def update_appearance_settings(
    settings: AppearanceSettings,
    current_user: User = Depends(get_current_user)
):
    """更新界面设置"""
    await save_appearance_settings(current_user.id, settings)
    return {"message": "界面设置已更新"}

@router.get("/system")
async def get_system_settings(current_user: User = Depends(get_current_user)):
    """获取系统设置"""
    return {
        "version": "1.0.0",
        "last_update": "2025-12-05",
        "data_usage": await get_user_data_usage(current_user.id),
        "storage_quota": await get_storage_quota(current_user.id)
    }

@router.post("/export-data")
async def export_user_data(current_user: User = Depends(get_current_user)):
    """导出用户数据"""
    data = await compile_user_data(current_user.id)

    # 生成导出文件
    export_file = f"user_data_{current_user.id}_{datetime.now().strftime('%Y%m%d')}.json"

    return {
        "download_url": f"/downloads/{export_file}",
        "expires_at": (datetime.now() + timedelta(hours=24)).isoformat()
    }

@router.post("/clear-cache")
async def clear_user_cache(current_user: User = Depends(get_current_user)):
    """清理用户缓存"""
    await clear_user_cache_data(current_user.id)
    return {"message": "缓存清理完成"}
```

## 📊 数据模型

### 用户设置表
```sql
CREATE TABLE user_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) UNIQUE,

    -- 安全设置
    mfa_enabled BOOLEAN DEFAULT FALSE,
    mfa_secret VARCHAR(32),
    last_password_change TIMESTAMP DEFAULT NOW(),

    -- 界面设置
    theme VARCHAR(20) DEFAULT 'light',
    language VARCHAR(10) DEFAULT 'zh-CN',
    timezone VARCHAR(50) DEFAULT 'Asia/Shanghai',
    layout VARCHAR(20) DEFAULT 'comfortable',

    -- 通知设置
    email_notifications JSON DEFAULT '{}',
    browser_notifications JSON DEFAULT '{}',

    -- 系统设置
    auto_backup BOOLEAN DEFAULT TRUE,
    data_retention_days INTEGER DEFAULT 365,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 登录记录表
CREATE TABLE login_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    ip_address INET,
    user_agent TEXT,
    device_info JSON,
    location VARCHAR(100),
    success BOOLEAN DEFAULT TRUE,
    failure_reason VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 用户数据使用统计
CREATE TABLE data_usage (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    usage_type VARCHAR(50), -- 'trades', 'strategies', 'reports'
    data_size BIGINT, -- 字节数
    record_count INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 🔧 实现细节

### 1. 密码强度验证
```python
def validate_password_strength(password: str) -> dict:
    """验证密码强度"""
    requirements = {
        'length': len(password) >= 8,
        'uppercase': bool(re.search(r'[A-Z]', password)),
        'lowercase': bool(re.search(r'[a-z]', password)),
        'numbers': bool(re.search(r'\d', password)),
        'special': bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
    }

    score = sum(requirements.values())

    if score <= 2:
        level = 'weak'
        color = 'red'
    elif score <= 4:
        level = 'medium'
        color = 'yellow'
    else:
        level = 'strong'
        color = 'green'

    return {
        'score': score,
        'level': level,
        'color': color,
        'requirements': requirements
    }

async def change_password(user_id: int, old_password: str, new_password: str) -> bool:
    """修改密码"""
    # 获取当前用户
    user = await get_user_by_id(user_id)

    # 验证旧密码
    if not verify_password(old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="当前密码错误")

    # 验证新密码强度
    validation = validate_password_strength(new_password)
    if validation['score'] < 3:
        raise HTTPException(status_code=400, detail="新密码强度不够")

    # 更新密码
    new_password_hash = hash_password(new_password)
    await update_user_password(user_id, new_password_hash)

    # 记录密码修改历史
    await record_password_change(user_id)

    return True
```

### 2. 通知系统实现
```python
async def send_notification(user_id: int, notification_type: str, message: str, data: dict = None):
    """发送通知"""
    user_settings = await get_user_notification_settings(user_id)

    # 邮件通知
    if user_settings['email'].get(notification_type, False):
        await send_email_notification(user_id, notification_type, message, data)

    # 浏览器通知
    if user_settings['browser'].get('enabled', False) and user_settings['browser'].get(notification_type, False):
        await send_browser_notification(user_id, notification_type, message, data)

async def send_browser_notification(user_id: int, notification_type: str, message: str, data: dict = None):
    """发送浏览器推送通知"""
    # 通过WebSocket实时推送
    if user_id in active_websockets:
        notification = {
            'type': 'notification',
            'notification_type': notification_type,
            'message': message,
            'data': data or {},
            'timestamp': datetime.utcnow().isoformat()
        }

        await active_websockets[user_id].send_json(notification)
```

## 🧪 测试功能

### 1. 设置页面测试
```typescript
describe('User Settings', () => {
  test('renders all setting tabs', () => {
    render(<UserSettings />);

    expect(screen.getByText('安全设置')).toBeInTheDocument();
    expect(screen.getByText('通知设置')).toBeInTheDocument();
    expect(screen.getByText('界面设置')).toBeInTheDocument();
    expect(screen.getByText('系统配置')).toBeInTheDocument();
  });

  test('changes active tab', () => {
    render(<UserSettings />);

    fireEvent.click(screen.getByText('通知设置'));
    expect(screen.getByText('邮件通知')).toBeInTheDocument();
  });

  test('updates password strength indicator', () => {
    render(<SecuritySettings />);

    const newPasswordInput = screen.getByLabelText('新密码');
    fireEvent.change(newPasswordInput, { target: { value: 'weak' } });

    expect(screen.getByText('弱')).toBeInTheDocument();
  });
});

describe('Settings API', () => {
  test('gets notification settings', async () => {
    const token = await getAuthToken();
    const response = await fetch('/api/settings/notifications', {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    expect(response.status).toBe(200);
    const data = await response.json();
    expect(data).toHaveProperty('email');
    expect(data).toHaveProperty('browser');
  });

  test('updates appearance settings', async () => {
    const token = await getAuthToken();
    const settings = {
      theme: 'dark',
      language: 'en-US',
      timezone: 'America/New_York'
    };

    const response = await fetch('/api/settings/appearance', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(settings)
    });

    expect(response.status).toBe(200);
  });
});
```

## 📋 验收标准

### 功能验收
- [ ] 密码修改和安全设置
- [ ] 通知偏好配置
- [ ] 界面主题和语言切换
- [ ] 系统配置和数据管理
- [ ] 登录记录和设备管理

### 用户体验验收
- [ ] 设置界面直观易用
- [ ] 实时保存和反馈
- [ ] 响应式设计
- [ ] 无障碍访问支持

### 安全验收
- [ ] 密码强度验证
- [ ] 敏感操作确认
- [ ] 数据隐私保护
- [ ] 权限控制正确

## 🎯 成功指标

### 用户满意度
- **设置易用性**: 用户满意度 > 8.0
- **功能完整性**: 个人设置覆盖率 > 95%
- **响应速度**: 设置保存响应 < 500ms

### 系统性能
- **页面加载**: 设置页面加载 < 2秒
- **数据准确**: 设置数据准确率 > 99%
- **稳定性**: 功能可用性 > 99.5%

这个简化的个人设置管理专注于个人用户的实际需求，提供了完整的安全、通知、界面和系统配置功能，界面简洁直观。
# 个人用户仪表板

## 🎯 功能概述
为个人使用者设计简洁实用的用户仪表板，用于管理系统设置、查看使用统计和配置个人偏好。

## 📋 需求优先级：P1 (个人管理)

## 🔧 功能需求

### 1. 个人信息管理
- **基本信息编辑**: 用户名、邮箱、个人简介
- **头像上传**: 简单的头像上传和裁剪
- **联系方式**: 电话、地址信息
- **个人设置**: 时区、语言、主题偏好

### 2. 账户安全设置
- **密码修改**: 带强度检测的安全密码更新
- **登录记录**: 查看最近的登录历史
- **设备管理**: 查看和信任登录设备
- **安全通知**: 重要安全事件的邮件提醒

### 3. 系统使用统计
- **登录统计**: 登录次数、活跃天数
- **功能使用**: 各功能模块使用频率
- **数据统计**: 交易策略使用情况
- **性能指标**: 系统响应时间统计

### 4. 快捷操作面板
- **常用功能**: 快速访问常用功能
- **最近活动**: 最近的操作记录
- **系统状态**: 当前系统运行状态
- **通知中心**: 系统通知和提醒

## 🎨 UI/UX 设计

### 1. 仪表板布局
```typescript
const PersonalDashboard = () => (
  <div className="min-h-screen bg-gray-50">
    <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      {/* 页面标题 */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">个人中心</h1>
        <p className="mt-2 text-gray-600">管理您的账户设置和个人偏好</p>
      </div>

      {/* 主要内容区域 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 左侧：个人信息卡片 */}
        <div className="lg:col-span-1 space-y-6">
          <ProfileCard />
          <QuickActions />
          <SystemStatus />
        </div>

        {/* 右侧：详细设置 */}
        <div className="lg:col-span-2 space-y-6">
          <UsageStatistics />
          <RecentActivity />
          <SettingsPanel />
        </div>
      </div>
    </div>
  </div>
);

// 个人信息卡片
const ProfileCard = () => (
  <div className="bg-white shadow rounded-lg p-6">
    <div className="flex flex-col items-center">
      <Avatar size="xl" className="mb-4" />
      <h2 className="text-xl font-semibold text-gray-900">张三</h2>
      <p className="text-gray-500">zhangsan@example.com</p>

      <div className="mt-4 flex space-x-4 text-sm text-gray-600">
        <div className="text-center">
          <div className="font-semibold text-gray-900">127</div>
          <div>登录次数</div>
        </div>
        <div className="text-center">
          <div className="font-semibold text-gray-900">45</div>
          <div>活跃天数</div>
        </div>
        <div className="text-center">
          <div className="font-semibold text-gray-900">8</div>
          <div>使用策略</div>
        </div>
      </div>

      <Button className="mt-4 w-full" variant="outline">
        编辑个人资料
      </Button>
    </div>
  </div>
);

// 快捷操作面板
const QuickActions = () => {
  const actions = [
    { icon: 'UserCog', label: '账户设置', color: 'blue' },
    { icon: 'Shield', label: '安全设置', color: 'green' },
    { icon: 'Settings', label: '系统偏好', color: 'gray' },
    { icon: 'Download', label: '数据导出', color: 'purple' }
  ];

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">快捷操作</h3>
      <div className="grid grid-cols-2 gap-4">
        {actions.map((action) => (
          <button
            key={action.label}
            className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Icon name={action.icon} className={`w-8 h-8 text-${action.color}-600 mb-2`} />
            <span className="text-sm text-gray-700">{action.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
};
```

### 2. 使用统计组件
```typescript
const UsageStatistics = () => {
  const [period, setPeriod] = useState('7d');

  const statistics = {
    logins: { current: 23, previous: 18, trend: 'up' },
    trades: { current: 156, previous: 142, trend: 'up' },
    strategies: { current: 8, previous: 6, trend: 'up' },
    performance: { current: 92.3, previous: 89.7, trend: 'up' }
  };

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-medium text-gray-900">使用统计</h3>
        <Select
          value={period}
          onChange={setPeriod}
          options={[
            { value: '7d', label: '最近7天' },
            { value: '30d', label: '最近30天' },
            { value: '90d', label: '最近90天' }
          ]}
        />
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="登录次数"
          value={statistics.logins.current}
          change={statistics.logins.current - statistics.logins.previous}
          icon="LogIn"
          color="blue"
        />
        <StatCard
          title="交易执行"
          value={statistics.trades.current}
          change={statistics.trades.current - statistics.trades.previous}
          icon="TrendingUp"
          color="green"
        />
        <StatCard
          title="活跃策略"
          value={statistics.strategies.current}
          change={statistics.strategies.current - statistics.strategies.previous}
          icon="Target"
          color="purple"
        />
        <StatCard
          title="系统评分"
          value={`${statistics.performance.current}%`}
          change={statistics.performance.current - statistics.performance.previous}
          icon="Activity"
          color="yellow"
        />
      </div>

      {/* 简单的图表 */}
      <div className="mt-6">
        <h4 className="text-sm font-medium text-gray-700 mb-3">活动趋势</h4>
        <div className="h-32">
          <LineChart
            data={generateMockActivityData(period)}
            options={{
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: { display: false }
              }
            }}
          />
        </div>
      </div>
    </div>
  );
};

const StatCard = ({ title, value, change, icon, color }) => (
  <div className="text-center">
    <div className={`inline-flex p-3 rounded-full bg-${color}-100 mb-3`}>
      <Icon name={icon} className={`w-6 h-6 text-${color}-600`} />
    </div>
    <div className="text-2xl font-bold text-gray-900">{value}</div>
    <div className="text-sm text-gray-500">{title}</div>
    {change !== 0 && (
      <div className={`text-xs mt-1 ${change > 0 ? 'text-green-600' : 'text-red-600'}`}>
        {change > 0 ? '+' : ''}{change}
      </div>
    )}
  </div>
);
```

### 3. 最近活动组件
```typescript
const RecentActivity = () => {
  const activities = [
    {
      id: 1,
      type: 'login',
      description: '从 Chrome 浏览器登录',
      timestamp: '10 分钟前',
      icon: 'LogIn',
      color: 'blue'
    },
    {
      id: 2,
      type: 'strategy',
      description: '执行 RSI 策略',
      timestamp: '2 小时前',
      icon: 'TrendingUp',
      color: 'green'
    },
    {
      id: 3,
      type: 'settings',
      description: '更新了交易参数',
      timestamp: '1 天前',
      icon: 'Settings',
      color: 'gray'
    },
    {
      id: 4,
      type: 'export',
      description: '导出了交易报告',
      timestamp: '3 天前',
      icon: 'Download',
      color: 'purple'
    }
  ];

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-medium text-gray-900">最近活动</h3>
        <Button variant="outline" size="sm">
          查看全部
        </Button>
      </div>

      <div className="space-y-4">
        {activities.map((activity) => (
          <div key={activity.id} className="flex items-start space-x-3">
            <div className={`flex-shrink-0 p-2 rounded-full bg-${activity.color}-100`}>
              <Icon name={activity.icon} className={`w-4 h-4 text-${activity.color}-600`} />
            </div>
            <div className="flex-1">
              <p className="text-sm text-gray-900">{activity.description}</p>
              <p className="text-xs text-gray-500">{activity.timestamp}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
```

## 🔗 API 设计

### 个人信息API
```python
from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.security import OAuth2PasswordBearer

router = APIRouter(prefix="/api/user", tags=["user"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

@router.get("/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    """获取个人资料"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "avatar_url": current_user.avatar_url,
        "bio": current_user.bio,
        "phone": current_user.phone,
        "timezone": current_user.timezone,
        "language": current_user.language,
        "created_at": current_user.created_at,
        "last_login": current_user.last_login
    }

@router.put("/profile")
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user)
):
    """更新个人资料"""
    # 更新用户信息
    await update_user_profile(current_user.id, profile_data)
    return {"message": "个人资料更新成功"}

@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """上传头像"""
    # 验证文件类型和大小
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="请上传图片文件")

    if file.size > 5 * 1024 * 1024:  # 5MB
        raise HTTPException(status_code=400, detail="图片大小不能超过5MB")

    # 保存头像文件
    avatar_url = await save_avatar_file(file, current_user.id)

    # 更新用户头像URL
    await update_user_avatar(current_user.id, avatar_url)

    return {"avatar_url": avatar_url}

@router.get("/statistics")
async def get_user_statistics(
    period: str = "7d",
    current_user: User = Depends(get_current_user)
):
    """获取用户使用统计"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7 if period == "7d" else 30 if period == "30d" else 90)

    stats = await get_user_activity_stats(current_user.id, start_date, end_date)

    return {
        "period": period,
        "login_count": stats.login_count,
        "trade_count": stats.trade_count,
        "strategy_count": stats.strategy_count,
        "performance_score": stats.performance_score,
        "activity_chart": stats.activity_data
    }

@router.get("/recent-activity")
async def get_recent_activity(
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """获取最近活动记录"""
    activities = await get_user_activities(current_user.id, limit)

    return {
        "activities": [
            {
                "id": activity.id,
                "type": activity.activity_type,
                "description": activity.description,
                "timestamp": activity.created_at.isoformat(),
                "metadata": activity.metadata
            }
            for activity in activities
        ]
    }
```

## 📊 数据模型

### 用户扩展信息表
```sql
CREATE TABLE user_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) UNIQUE,
    avatar_url VARCHAR(255),
    bio TEXT,
    phone VARCHAR(20),
    timezone VARCHAR(50) DEFAULT 'Asia/Shanghai',
    language VARCHAR(10) DEFAULT 'zh-CN',
    theme VARCHAR(20) DEFAULT 'light',
    notification_preferences JSON,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 用户活动记录
CREATE TABLE user_activities (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    activity_type VARCHAR(50), -- 'login', 'trade', 'settings', 'export'
    description TEXT,
    metadata JSON,
    ip_address INET,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 用户统计缓存
CREATE TABLE user_statistics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    stat_date DATE,
    login_count INTEGER DEFAULT 0,
    trade_count INTEGER DEFAULT 0,
    strategy_count INTEGER DEFAULT 0,
    performance_score DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, stat_date)
);
```

## 🔧 实现细节

### 1. 头像上传处理
```python
import os
import uuid
from fastapi import UploadFile

async def save_avatar_file(file: UploadFile, user_id: int) -> str:
    """保存用户头像文件"""
    # 生成唯一文件名
    file_extension = file.filename.split('.')[-1]
    unique_filename = f"{user_id}_{uuid.uuid4()}.{file_extension}"

    # 保存路径
    upload_dir = "uploads/avatars"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, unique_filename)

    # 保存文件
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    # 返回可访问的URL
    return f"/uploads/avatars/{unique_filename}"

async def update_user_avatar(user_id: int, avatar_url: str):
    """更新用户头像URL"""
    await execute_query(
        """
        INSERT INTO user_profiles (user_id, avatar_url)
        VALUES ($1, $2)
        ON CONFLICT (user_id)
        DO UPDATE SET avatar_url = $2, updated_at = NOW()
        """,
        user_id, avatar_url
    )
```

### 2. 统计数据计算
```python
async def get_user_activity_stats(user_id: int, start_date: datetime, end_date: datetime):
    """获取用户活动统计数据"""

    # 登录次数
    login_count = await fetch_val(
        """
        SELECT COUNT(*) FROM login_history
        WHERE user_id = $1 AND login_time BETWEEN $2 AND $3 AND success = TRUE
        """,
        user_id, start_date, end_date
    )

    # 交易次数
    trade_count = await fetch_val(
        """
        SELECT COUNT(*) FROM trades
        WHERE user_id = $1 AND created_at BETWEEN $2 AND $3
        """,
        user_id, start_date, end_date
    )

    # 策略使用数量
    strategy_count = await fetch_val(
        """
        SELECT COUNT(DISTINCT strategy_id) FROM strategy_usage
        WHERE user_id = $1 AND used_at BETWEEN $2 AND $3
        """,
        user_id, start_date, end_date
    )

    # 性能评分 (简化计算)
    performance_score = min(100.0, (trade_count * 0.6 + strategy_count * 5.0))

    # 活动图表数据
    activity_data = await generate_activity_chart_data(user_id, start_date, end_date)

    return {
        "login_count": login_count,
        "trade_count": trade_count,
        "strategy_count": strategy_count,
        "performance_score": performance_score,
        "activity_data": activity_data
    }

async def generate_activity_chart_data(user_id: int, start_date: datetime, end_date: datetime):
    """生成活动图表数据"""
    # 按日期分组的活动统计
    daily_stats = await fetch_all(
        """
        SELECT
            DATE(created_at) as date,
            COUNT(*) as activity_count
        FROM user_activities
        WHERE user_id = $1 AND created_at BETWEEN $2 AND $3
        GROUP BY DATE(created_at)
        ORDER BY date
        """,
        user_id, start_date, end_date
    )

    return [
        {
            "date": stat["date"].isoformat(),
            "count": stat["activity_count"]
        }
        for stat in daily_stats
    ]
```

## 🧪 测试功能

### 1. 仪表板组件测试
```typescript
describe('Personal Dashboard', () => {
  test('renders user profile card', () => {
    render(<ProfileCard />);
    expect(screen.getByText('编辑个人资料')).toBeInTheDocument();
  });

  test('displays usage statistics', () => {
    render(<UsageStatistics />);
    expect(screen.getByText('使用统计')).toBeInTheDocument();
    expect(screen.getByText('登录次数')).toBeInTheDocument();
  });

  test('shows recent activity', () => {
    render(<RecentActivity />);
    expect(screen.getByText('最近活动')).toBeInTheDocument();
  });
});

describe('User API', () => {
  test('gets user profile', async () => {
    const token = await getAuthToken();
    const response = await fetch('/api/user/profile', {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    expect(response.status).toBe(200);
    const data = await response.json();
    expect(data).toHaveProperty('username');
    expect(data).toHaveProperty('email');
  });

  test('updates user profile', async () => {
    const token = await getAuthToken();
    const updateData = {
      bio: '新的个人简介',
      timezone: 'Asia/Shanghai'
    };

    const response = await fetch('/api/user/profile', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(updateData)
    });

    expect(response.status).toBe(200);
  });
});
```

## 📋 验收标准

### 功能验收
- [ ] 个人信息查看和编辑
- [ ] 头像上传功能
- [ ] 使用统计展示
- [ ] 最近活动记录
- [ ] 系统状态显示
- [ ] 快捷操作面板

### 用户体验验收
- [ ] 界面简洁美观
- [ ] 响应式设计
- [ ] 加载状态明确
- [ ] 操作反馈及时

### 性能验收
- [ ] 页面加载时间 < 2秒
- [ ] 数据查询响应 < 500ms
- [ ] 统计图表渲染流畅

## 🎯 成功指标

### 用户满意度
- **界面易用性**: 用户满意度 > 8.0
- **功能完整性**: 覆盖个人管理需求 > 90%
- **操作效率**: 常用操作完成时间 < 30秒

### 系统性能
- **页面响应**: 交互响应时间 < 200ms
- **数据准确**: 统计数据准确率 > 95%
- **稳定性**: 功能可用性 > 99%

这个简化的个人仪表板专注于个人使用场景，去除了复杂的企业管理功能，提供了直观的个人信息管理和使用统计功能。
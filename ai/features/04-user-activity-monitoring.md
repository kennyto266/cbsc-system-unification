# 用户活动监控系统

## 🎯 功能概述
构建全面的用户活动监控系统，实时跟踪用户行为、分析使用模式、识别异常活动，为安全审计和系统优化提供数据支撑。

## 📋 需求优先级：P1 (高优先级)

## 🔧 功能需求

### 1. 实时活动监控
- **在线状态跟踪**: 实时显示在线用户数量和状态
- **页面访问监控**: 用户访问路径、停留时间、跳出率
- **功能使用统计**: 各功能模块使用频率和时长
- **交互行为记录**: 点击、滚动、表单填写等交互行为
- **性能指标监控**: 页面加载时间、API响应时间

### 2. 用户行为分析
- **用户画像构建**: 基于行为数据的用户分群
- **使用模式识别**: 用户的典型使用路径和习惯
- **活跃度分析**: 日活跃、周活跃、月活跃用户统计
- **留存分析**: 新用户留存率、老用户回访率
- **功能偏好分析**: 用户对各功能的使用偏好

### 3. 安全异常检测
- **异常登录检测**: 异地登录、非常用设备、异常时间
- **可疑行为识别**: 频繁操作、批量请求、爬虫行为
- **权限异常监控**: 越权访问尝试、权限提升行为
- **数据泄露监控**: 大量数据导出、敏感信息访问
- **攻击模式识别**: 暴力破解、SQL注入尝试

### 4. 审计日志系统
- **操作日志记录**: 用户所有关键操作的详细记录
- **系统事件日志**: 系统级事件和错误日志
- **合规性报告**: 满足数据保护法规的报告生成
- **日志查询检索**: 强大的日志搜索和过滤功能
- **日志归档管理**: 长期存储和定期清理策略

## 🎨 UI/UX 设计

### 1. 监控仪表板布局
```typescript
const MonitoringDashboard = () => (
  <div className="grid grid-cols-12 gap-6">
    {/* 实时指标卡片 */}
    <div className="col-span-12 grid grid-cols-1 md:grid-cols-4 gap-4">
      <MetricCard
        title="在线用户"
        value={onlineUsers}
        change={onlineChange}
        icon="Users"
        color="blue"
      />
      <MetricCard
        title="页面访问"
        value={pageViews}
        change={viewChange}
        icon="Eye"
        color="green"
      />
      <MetricCard
        title="异常事件"
        value={anomalies}
        change={anomalyChange}
        icon="AlertTriangle"
        color="red"
      />
      <MetricCard
        title="系统性能"
        value={performanceScore}
        change={perfChange}
        icon="Gauge"
        color="yellow"
      />
    </div>

    {/* 实时活动地图 */}
    <div className="col-span-12 md:col-span-8">
      <Card title="实时活动地图">
        <ActivityMap />
      </Card>
    </div>

    {/* 在线用户列表 */}
    <div className="col-span-12 md:col-span-4">
      <Card title="在线用户">
        <OnlineUserList />
      </Card>
    </div>

    {/* 用户行为图表 */}
    <div className="col-span-12 md:col-span-6">
      <Card title="用户活跃度趋势">
        <ActivityTrendChart />
      </Card>
    </div>

    {/* 功能使用统计 */}
    <div className="col-span-12 md:col-span-6">
      <Card title="功能使用统计">
        <FeatureUsageChart />
      </Card>
    </div>

    {/* 安全事件时间线 */}
    <div className="col-span-12">
      <Card title="安全事件时间线">
        <SecurityTimeline />
      </Card>
    </div>
  </div>
);
```

### 2. 用户详情页面
```typescript
const UserActivityDetail = ({ userId }) => (
  <div className="space-y-6">
    {/* 用户基本信息 */}
    <UserInfo userId={userId} />

    {/* 活动统计概览 */}
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      <StatCard label="总访问次数" value={totalVisits} />
      <StatCard label="平均停留时间" value={avgDuration} />
      <StatCard label="最后活动时间" value={lastActivity} />
      <StatCard label="风险评分" value={riskScore} />
    </div>

    {/* 活动时间线 */}
    <Card title="活动时间线">
      <ActivityTimeline userId={userId} />
    </Card>

    {/* 访问路径分析 */}
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <Card title="访问路径">
        <AccessPath userId={userId} />
      </Card>
      <Card title="功能使用">
        <FeatureUsage userId={userId} />
      </Card>
    </div>

    {/* 异常事件 */}
    <Card title="异常事件">
      <AnomalyEvents userId={userId} />
    </Card>
  </div>
);
```

## 🔗 API 设计

### 实时监控端点
```python
GET  /api/monitoring/realtime/overview   # 实时概览数据
GET  /api/monitoring/realtime/users      # 在线用户列表
GET  /api/monitoring/realtime/anomalies  # 实时异常事件
GET  /api/monitoring/realtime/performance # 系统性能指标
WebSocket /ws/monitoring/realtime         # 实时数据推送
```

### 用户行为端点
```python
GET  /api/monitoring/users/{id}/activity # 用户活动详情
GET  /api/monitoring/users/{id}/behavior # 用户行为分析
GET  /api/monitoring/users/{id}/sessions # 用户会话记录
GET  /api/monitoring/users/{id}/path     # 用户访问路径
GET  /api/monitoring/users/segments      # 用户分群数据
```

### 分析报告端点
```python
GET  /api/monitoring/reports/daily       # 日报数据
GET  /api/monitoring/reports/weekly      # 周报数据
GET  /api/monitoring/reports/monthly     # 月报数据
GET  /api/monitoring/reports/retention   # 留存分析
GET  /api/monitoring/reports/funnel      # 转化漏斗分析
```

### 安全监控端点
```python
GET  /api/monitoring/security/anomalies  # 异常事件列表
GET  /api/monitoring/security/threats    # 威胁情报
GET  /api/monitoring/security/incidents  # 安全事件
POST /api/monitoring/security/alert      # 创建安全告警
GET  /api/monitoring/security/risk-scores # 风险评分
```

### 审计日志端点
```python
GET  /api/monitoring/audit/logs          # 审计日志查询
GET  /api/monitoring/audit/export        # 导出审计日志
POST /api/monitoring/audit/search        # 高级日志搜索
GET  /api/monitoring/audit/compliance    # 合规性报告
```

## 📊 数据模型

### UserActivities表
```sql
CREATE TABLE user_activities (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    session_id VARCHAR(255),
    activity_type VARCHAR(50), -- 'page_view', 'click', 'form_submit', etc.
    resource_type VARCHAR(50), -- 'page', 'api', 'feature'
    resource_id VARCHAR(255),
    metadata JSON,
    ip_address INET,
    user_agent TEXT,
    duration INTEGER, -- 活动持续时间(毫秒)
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_user_activities_user_id (user_id),
    INDEX idx_user_activities_created_at (created_at),
    INDEX idx_user_activities_type (activity_type)
);
```

### UserSessions表扩展
```sql
CREATE TABLE user_sessions_extended (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    session_token VARCHAR(255) UNIQUE,
    device_info JSON,
    location_info JSON, -- 国家、城市、ISP
    start_time TIMESTAMP DEFAULT NOW(),
    last_activity TIMESTAMP DEFAULT NOW(),
    duration INTEGER, -- 会话持续时间
    page_views INTEGER DEFAULT 0,
    actions INTEGER DEFAULT 0,
    is_secure BOOLEAN DEFAULT TRUE,
    risk_score INTEGER DEFAULT 0,
    end_reason VARCHAR(50), -- 'logout', 'timeout', 'forced'
    created_at TIMESTAMP DEFAULT NOW()
);
```

### SecurityEvents表
```sql
CREATE TABLE security_events (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    event_type VARCHAR(50), -- 'failed_login', 'suspicious_activity', 'privilege_escalation'
    severity VARCHAR(20), -- 'low', 'medium', 'high', 'critical'
    description TEXT,
    metadata JSON,
    ip_address INET,
    user_agent TEXT,
    location_info JSON,
    status VARCHAR(20) DEFAULT 'open', -- 'open', 'investigating', 'resolved'
    resolved_by INTEGER REFERENCES users(id),
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_security_events_user_id (user_id),
    INDEX idx_security_events_type (event_type),
    INDEX idx_security_events_severity (severity),
    INDEX idx_security_events_created_at (created_at)
);
```

### AnalyticsMetrics表
```sql
CREATE TABLE analytics_metrics (
    id SERIAL PRIMARY KEY,
    metric_type VARCHAR(50), -- 'dau', 'mau', 'retention', 'feature_usage'
    metric_name VARCHAR(100),
    value DECIMAL(15,2),
    dimensions JSON, -- 透视维度
    period_start TIMESTAMP,
    period_end TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE KEY unique_metric (metric_type, metric_name, period_start, period_end)
);
```

## 🔧 实现细节

### 1. 实时数据收集
```typescript
// 客户端活动追踪
class ActivityTracker {
  private sessionId: string;
  private userId: string;
  private queue: ActivityEvent[] = [];

  constructor() {
    this.sessionId = this.generateSessionId();
    this.initializeEventListeners();
    this.startBatchSender();
  }

  trackPageView(page: string, metadata?: any) {
    this.enqueue({
      type: 'page_view',
      data: { page, url: window.location.href, ...metadata },
      timestamp: Date.now()
    });
  }

  trackClick(element: string, properties?: any) {
    this.enqueue({
      type: 'click',
      data: { element, ...properties },
      timestamp: Date.now()
    });
  }

  trackFormSubmit(form: string, data: any) {
    this.enqueue({
      type: 'form_submit',
      data: { form, ...data },
      timestamp: Date.now()
    });
  }

  private enqueue(event: ActivityEvent) {
    this.queue.push({
      ...event,
      sessionId: this.sessionId,
      userId: this.userId,
      userAgent: navigator.userAgent,
      timestamp: Date.now()
    });
  }

  private async sendBatch() {
    if (this.queue.length === 0) return;

    const events = this.queue.splice(0);
    try {
      await fetch('/api/monitoring/activities/batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ events })
      });
    } catch (error) {
      console.error('Failed to send activity events:', error);
      // 重新加入队列
      this.queue.unshift(...events);
    }
  }
}

// 全局初始化
const activityTracker = new ActivityTracker();

// React Hook集成
const useActivityTracker = () => {
  useEffect(() => {
    activityTracker.trackPageView(window.location.pathname);

    const handleRouteChange = () => {
      activityTracker.trackPageView(window.location.pathname);
    };

    // 监听路由变化
    window.addEventListener('popstate', handleRouteChange);
    return () => window.removeEventListener('popstate', handleRouteChange);
  }, []);

  return {
    trackClick: activityTracker.trackClick.bind(activityTracker),
    trackFormSubmit: activityTracker.trackFormSubmit.bind(activityTracker)
  };
};
```

### 2. 异常检测算法
```python
# 异常行为检测
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import numpy as np

class AnomalyDetector:
    def __init__(self):
        self.models = {
            'login_pattern': IsolationForest(contamination=0.1),
            'api_usage': IsolationForest(contamination=0.05),
            'session_duration': IsolationForest(contamination=0.1)
        }
        self.scalers = {
            model: StandardScaler() for model in self.models
        }

    def analyze_user_behavior(self, user_id: str, timeframe: str = '24h'):
        """分析用户行为是否异常"""
        # 获取用户历史行为数据
        historical_data = self.get_user_historical_data(user_id, timeframe)

        anomalies = {}

        # 登录模式异常检测
        login_features = self.extract_login_features(historical_data)
        if len(login_features) > 10:
            scaled_features = self.scalers['login_pattern'].fit_transform(login_features)
            anomaly_scores = self.models['login_pattern'].fit_predict(scaled_features)
            anomalies['login_pattern'] = np.mean(anomaly_scores == -1)

        # API使用模式检测
        api_features = self.extract_api_features(historical_data)
        if len(api_features) > 10:
            scaled_features = self.scalers['api_usage'].fit_transform(api_features)
            anomaly_scores = self.models['api_usage'].fit_predict(scaled_features)
            anomalies['api_usage'] = np.mean(anomaly_scores == -1)

        # 综合风险评分
        risk_score = self.calculate_risk_score(anomalies)

        return {
            'user_id': user_id,
            'risk_score': risk_score,
            'anomalies': anomalies,
            'recommendations': self.generate_recommendations(anomalies)
        }

    def extract_login_features(self, data):
        """提取登录行为特征"""
        features = []
        for login in data:
            feature = [
                login.get('hour_of_day', 0),
                login.get('day_of_week', 0),
                len(login.get('ip_address', '')), # IP地址变化
                login.get('device_changes', 0),
                login.get('failed_attempts', 0)
            ]
            features.append(feature)
        return np.array(features)

    def calculate_risk_score(self, anomalies):
        """计算综合风险评分"""
        weights = {
            'login_pattern': 0.3,
            'api_usage': 0.4,
            'session_duration': 0.3
        }

        risk_score = 0
        for anomaly_type, score in anomalies.items():
            risk_score += score * weights.get(anomaly_type, 0.1)

        return min(risk_score * 100, 100) # 转换为0-100分制
```

### 3. 实时数据流处理
```python
# WebSocket实时数据推送
import asyncio
import json
from fastapi import WebSocket
from typing import List

class RealtimeMonitoringManager:
    def __init__(self):
        self.connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.connections.remove(websocket)

    async def broadcast_metrics(self, metrics: dict):
        """广播实时指标"""
        message = {
            'type': 'metrics_update',
            'data': metrics,
            'timestamp': datetime.utcnow().isoformat()
        }

        await self._broadcast(message)

    async def broadcast_anomaly(self, anomaly: dict):
        """广播异常事件"""
        message = {
            'type': 'security_anomaly',
            'data': anomaly,
            'timestamp': datetime.utcnow().isoformat()
        }

        await self._broadcast(message)

    async def _broadcast(self, message: dict):
        """向所有连接的客户端广播消息"""
        if not self.connections:
            return

        disconnected = []
        for connection in self.connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                disconnected.append(connection)

        # 清理断开的连接
        for conn in disconnected:
            self.connections.remove(conn)

# 全局管理器实例
monitoring_manager = RealtimeMonitoringManager()

@router.websocket("/ws/monitoring/realtime")
async def websocket_endpoint(websocket: WebSocket):
    await monitoring_manager.connect(websocket)
    try:
        while True:
            # 保持连接活跃
            await websocket.receive_text()
    except Exception:
        monitoring_manager.disconnect(websocket)
```

## 📈 数据可视化

### 1. 实时指标卡片
```typescript
const MetricCard = ({ title, value, change, icon, color }) => {
  const changeColor = change >= 0 ? 'text-green-600' : 'text-red-600';
  const changeIcon = change >= 0 ? 'TrendingUp' : 'TrendingDown';

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
        </div>
        <div className={`p-3 rounded-full bg-${color}-100`}>
          <Icon name={icon} className={`w-6 h-6 text-${color}-600`} />
        </div>
      </div>

      {change !== undefined && (
        <div className={`flex items-center mt-2 text-sm ${changeColor}`}>
          <Icon name={changeIcon} className="w-4 h-4 mr-1" />
          {Math.abs(change)}% 较昨日
        </div>
      )}
    </div>
  );
};
```

### 2. 活动热力图
```typescript
const ActivityHeatmap = ({ data }) => {
  const hours = Array.from({ length: 24 }, (_, i) => i);
  const days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];

  const getColor = (intensity) => {
    const colors = [
      'bg-gray-100', 'bg-blue-100', 'bg-blue-300',
      'bg-blue-500', 'bg-blue-700'
    ];
    return colors[Math.min(intensity, colors.length - 1)];
  };

  return (
    <div className="p-4">
      <div className="grid grid-cols-25 gap-1">
        <div></div>
        {hours.map(hour => (
          <div key={hour} className="text-xs text-center text-gray-500">
            {hour}
          </div>
        ))}

        {days.map((day, dayIndex) => (
          <React.Fragment key={day}>
            <div className="text-xs text-gray-500 pr-2">{day}</div>
            {hours.map(hour => {
              const intensity = data[dayIndex]?.[hour] || 0;
              return (
                <div
                  key={hour}
                  className={`w-4 h-4 rounded-sm ${getColor(intensity)}`}
                  title={`${day} ${hour}:00 - 活跃度: ${intensity}`}
                />
              );
            })}
          </React.Fragment>
        ))}
      </div>

      <div className="flex items-center justify-center mt-4 space-x-2">
        <span className="text-xs text-gray-500">低</span>
        <div className="flex space-x-1">
          {['bg-gray-100', 'bg-blue-100', 'bg-blue-300', 'bg-blue-500', 'bg-blue-700'].map((color, i) => (
            <div key={i} className={`w-3 h-3 ${color} rounded-sm`} />
          ))}
        </div>
        <span className="text-xs text-gray-500">高</span>
      </div>
    </div>
  );
};
```

## 🔒 隐私保护

### 1. 数据匿名化
```python
# 敏感数据匿名化
class DataAnonymizer:
    @staticmethod
    def anonymize_ip(ip_address: str) -> str:
        """IP地址匿名化 - 保留前3位"""
        parts = ip_address.split('.')
        return '.'.join(parts[:3]) + '.0'

    @staticmethod
    def anonymize_user_agent(user_agent: str) -> str:
        """User Agent匿名化 - 移除唯一标识符"""
        # 移除版本号和唯一标识符
        import re
        return re.sub(r'\/[\d.]+', '', user_agent)

    @staticmethod
    def hash_user_id(user_id: str) -> str:
        """用户ID哈希化"""
        import hashlib
        return hashlib.sha256(user_id.encode()).hexdigest()[:16]
```

### 2. 数据保留策略
```python
# 数据生命周期管理
class DataRetentionPolicy:
    def __init__(self):
        self.retention_periods = {
            'user_activities': 90,      # 90天
            'session_data': 30,         # 30天
            'security_events': 365,     # 1年
            'audit_logs': 2555,         # 7年
            'analytics_metrics': 1095   # 3年
        }

    async def cleanup_old_data(self):
        """定期清理过期数据"""
        for table_name, days in self.retention_periods.items():
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            await self.database.execute(f"""
                DELETE FROM {table_name}
                WHERE created_at < '{cutoff_date}'
            """)

            logger.info(f"Cleaned up {table_name} data older than {days} days")
```

## 🧪 测试策略

### 1. 数据收集测试
```typescript
describe('Activity Tracking', () => {
  test('tracks page views correctly', async () => {
    const mockFetch = jest.fn();
    global.fetch = mockFetch;

    const tracker = new ActivityTracker();
    tracker.trackPageView('/dashboard');

    // 等待批量发送
    await new Promise(resolve => setTimeout(resolve, 1000));

    expect(mockFetch).toHaveBeenCalledWith(
      '/api/monitoring/activities/batch',
      expect.objectContaining({
        method: 'POST',
        body: expect.stringContaining('page_view')
      })
    );
  });

  test('handles failed network requests gracefully', async () => {
    const mockFetch = jest.fn(() => Promise.reject('Network error'));
    global.fetch = mockFetch;

    const tracker = new ActivityTracker();
    tracker.trackClick('button', { action: 'test' });

    await new Promise(resolve => setTimeout(resolve, 1000));

    // 应该重新加入队列而不是丢失数据
    expect(tracker.getQueueSize()).toBeGreaterThan(0);
  });
});
```

### 2. 异常检测测试
```python
class TestAnomalyDetector(unittest.TestCase):
    def test_detects_login_anomalies(self):
        detector = AnomalyDetector()

        # 正常登录模式
        normal_logins = [
            {'hour_of_day': 9, 'day_of_week': 1, 'ip_address': '192.168.1.1'},
            {'hour_of_day': 14, 'day_of_week': 2, 'ip_address': '192.168.1.1'},
        ]

        # 异常登录模式
        anomaly_logins = [
            {'hour_of_day': 3, 'day_of_week': 6, 'ip_address': '203.0.113.1'},
            {'hour_of_day': 4, 'day_of_week': 6, 'ip_address': '203.0.113.2'},
        ]

        normal_result = detector.analyze_login_pattern(normal_logins)
        anomaly_result = detector.analyze_login_pattern(anomaly_logins)

        self.assertLess(normal_result['risk_score'], anomaly_result['risk_score'])
```

## 📋 验收标准

### 功能验收
- [ ] 实时用户活动监控
- [ ] 用户行为分析报告
- [ ] 安全异常自动检测
- [ ] 完整的审计日志系统
- [ ] 数据可视化仪表板
- [ ] 隐私保护机制

### 性能验收
- [ ] 实时数据延迟 < 5秒
- [ ] 支持10000+并发用户监控
- [ ] 历史数据查询响应 < 2秒
- [ ] 异常检测准确率 > 90%

### 安全验收
- [ ] 数据加密存储
- [ ] 敏感信息匿名化
- [ ] 访问权限控制
- [ ] 合规性要求满足

## 🎯 成功指标

### 监控覆盖率
- **用户行为覆盖率**: > 95%的用户操作被记录
- **系统监控覆盖率**: > 90%的关键功能被监控
- **异常检测准确率**: > 85%的异常行为被识别

### 系统性能
- **数据收集延迟**: < 100ms
- **实时仪表板更新**: < 5秒
- **历史查询响应**: < 2秒
- **系统可用性**: 99.9%

### 安全效果
- **安全事件识别率**: > 90%
- **误报率**: < 10%
- **威胁响应时间**: < 5分钟
- **审计完整性**: 100%
# Alert System

综合的告警和通知系统，支持实时监控和主动响应关键事件。

## 功能特性

### 🔔 多渠道通知
- **浏览器推送通知** - 实时推送，支持操作按钮
- **邮件通知** - HTML模板，支持附件
- **短信通知** - 紧急告警直达手机
- **Webhook集成** - 支持Slack、Teams等
- **应用内通知** - 实时通知中心

### 📊 告警规则引擎
- 可视化规则构建器
- 支持复杂逻辑条件
- 多种操作符（等于、大于、包含等）
- 时间窗口聚合
- 自定义指标告警

### 🛡️ 高级功能
- 告警去重和分组
- 冷却期和静默时间
- 升级策略
- 速率限制
- 多语言支持

## 快速开始

### 1. 初始化告警管理器

```typescript
import { AlertManager, PushNotificationService, EmailService } from '@/services/alerts';

// 配置推送通知
const pushService = new PushNotificationService({
  vapidPublicKey: 'YOUR_VAPID_PUBLIC_KEY'
});

// 配置邮件服务
const emailService = new EmailService({
  smtp: {
    host: 'smtp.example.com',
    port: 587,
    secure: false,
    auth: {
      user: 'user@example.com',
      pass: 'password'
    }
  },
  from: {
    name: 'CBSC Alerts',
    email: 'alerts@cbsc.com'
  },
  throttling: {
    enabled: true,
    maxEmailsPerMinute: 10,
    maxEmailsPerHour: 500
  }
});

// 创建告警管理器
const alertManager = new AlertManager({
  alertEngine: new AlertEngine(),
  pushNotifications: pushService,
  email: emailService
});

// 初始化
await pushService.initialize();
```

### 2. 创建告警规则

```typescript
import { AlertRule, AlertSeverity, NotificationChannel, AlertOperator } from '@/services/alerts';

const rule: AlertRule = await alertManager.createRule({
  name: '策略P&L异常',
  description: '当策略日亏损超过阈值时触发',
  enabled: true,
  severity: AlertSeverity.WARNING,
  conditions: [
    {
      id: 'pnl-condition',
      type: 'metric',
      field: 'dailyPnl',
      operator: AlertOperator.LESS_THAN,
      value: -1000,
      timeWindow: 60 // 1小时窗口
    }
  ],
  notificationChannels: [
    NotificationChannel.BROWSER_PUSH,
    NotificationChannel.EMAIL,
    NotificationChannel.SMS
  ],
  cooldownPeriod: 30, // 30分钟冷却期
  quietHours: {
    enabled: true,
    startTime: '22:00',
    endTime: '07:00',
    timezone: 'UTC'
  },
  tags: ['strategy', 'pnl', 'risk']
});
```

### 3. 触发告警评估

```typescript
// 当策略数据更新时评估告警
const context = {
  timestamp: new Date(),
  source: 'strategy-updater',
  data: {
    id: 'strategy-001',
    name: 'Momentum Trading',
    dailyPnl: -1500, // 这会触发告警
    totalReturn: 12.5,
    active: true
  }
};

// 评估所有规则
const results = await alertManager.alertEngine.evaluateRules(undefined, context);

// 或评估特定规则
const specificResults = await alertManager.alertEngine.evaluateRules(
  [rule.id],
  context
);
```

### 4. 处理告警

```typescript
// 获取活动告警
const alerts = alertManager.getActiveAlerts({
  severity: [AlertSeverity.WARNING, AlertSeverity.CRITICAL]
});

// 确认告警
await alertManager.acknowledgeAlert(alert.id, 'user-123');

// 解决告警
await alertManager.resolveAlert(alert.id, 'user-123', 'Issue has been fixed');
```

## 通知渠道配置

### 浏览器推送通知

```typescript
// 请求权限
const permission = await pushService.requestPermission();
if (permission.granted) {
  // 订阅推送
  await pushService.subscribe('user-123');
}

// 监听通知点击事件
pushService.on('notification_clicked', (data) => {
  console.log('Notification clicked:', data);
  // 导航到相应页面
});
```

### 邮件通知

```typescript
// 发送自定义邮件
await emailService.sendCustomEmail({
  to: ['user@example.com'],
  subject: 'Custom Alert',
  template: 'custom-template',
  data: {
    alertName: 'Strategy Alert',
    message: 'Custom message',
    link: 'https://cbsc.com/alerts/123'
  }
});

// 测试邮件配置
const testResult = await emailService.testEmail('test@example.com');
console.log('Email test result:', testResult);
```

## 高级配置

### 去重设置

```typescript
const rule = {
  // ...
  deduplication: {
    enabled: true,
    windowMinutes: 30, // 30分钟内的重复告警会被合并
    key: ['source.type', 'field'] // 基于这些字段去重
  }
};
```

### 升级策略

```typescript
const rule = {
  // ...
  escalationPolicy: {
    enabled: true,
    levels: [
      {
        level: 1,
        delayMinutes: 5,
        severity: AlertSeverity.WARNING,
        channels: [NotificationChannel.BROWSER_PUSH]
      },
      {
        level: 2,
        delayMinutes: 15,
        severity: AlertSeverity.CRITICAL,
        channels: [NotificationChannel.EMAIL, NotificationChannel.SMS],
        additionalRecipients: ['manager@example.com']
      }
    ]
  }
};
```

### 速率限制

```typescript
const rule = {
  // ...
  throttle: {
    enabled: true,
    maxAlerts: 5, // 时间窗口内最多5个告警
    windowMinutes: 60 // 1小时窗口
  }
};
```

## 用户偏好设置

```typescript
const preferences: UserNotificationPreferences = {
  userId: 'user-123',
  channels: {
    browser_push: {
      enabled: true,
      quietHours: true,
      quietStartTime: '22:00',
      quietEndTime: '07:00'
    },
    email: {
      enabled: true,
      addresses: ['user@example.com'],
      frequency: 'immediate' // 'immediate', 'hourly', 'daily'
    },
    sms: {
      enabled: false,
      phoneNumber: '+1234567890',
      verified: true
    }
  },
  severityFilters: {
    [AlertSeverity.INFO]: false,
    [AlertSeverity.WARNING]: true,
    [AlertSeverity.CRITICAL]: true
  },
  quietHours: {
    enabled: true,
    startTime: '22:00',
    endTime: '07:00',
    timezone: 'America/New_York'
  }
};

// 更新用户偏好
await alertManager.updateUserPreferences('user-123', preferences);
```

## Webhook集成

```typescript
// Slack Webhook
const slackWebhook = {
  url: 'https://hooks.slack.com/services/...',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  }
};

// 在AlertManager中添加
alertManager.webhooks.set(NotificationChannel.SLACK, slackWebhook);

// 自定义Webhook处理
await alertManager.sendWebhookNotification(alert, NotificationChannel.WEBHOOK);
```

## 性能优化

### 批量处理
- 告警评估批量执行
- 通知并行发送
- 智能队列管理

### 缓存策略
- 规则评估结果缓存
- 用户偏好本地缓存
- 通知发送状态缓存

### 内存管理
- 定期清理历史数据
- 限制并发评估数量
- 优化事件监听器

## 监控和日志

### 告警统计

```typescript
const stats = alertManager.getStatistics();
console.log('Alert Statistics:', stats);
// 输出:
// {
//   total: 15,
//   active: 3,
//   acknowledged: 10,
//   resolved: 2,
//   bySeverity: { info: 5, warning: 8, critical: 2 }
// }
```

### 邮件统计

```typescript
const emailStats = emailService.getEmailStats();
console.log('Email Statistics:', emailStats);
// 输出:
// {
//   minute: 5,
//   hour: 45,
//   limitPerMinute: 10,
//   limitPerHour: 500
// }
```

### 事件监听

```typescript
// 监听告警事件
alertManager.on('alert_triggered', (data) => {
  // 发送到分析系统
  analytics.track('alert_triggered', {
    ruleId: data.rule.id,
    severity: data.alert.severity
  });
});

alertManager.on('alert_status_updated', (data) => {
  // 更新UI状态
  updateUIAlertStatus(data.alertId, data.status);
});
```

## 最佳实践

### 1. 规则设计
- 使用清晰的描述性名称
- 设置合理的冷却期
- 避免过于敏感的阈值
- 定期审查和优化规则

### 2. 通知管理
- 尊重用户通知偏好
- 避免通知轰炸
- 在非紧急时使用静默时间
- 提供清晰的操作指导

### 3. 性能考虑
- 限制活动告警数量
- 定期清理历史数据
- 使用批量操作
- 监控系统性能

### 4. 安全考虑
- 验证Webhook来源
- 限制敏感信息传输
- 使用HTTPS通信
- 审计日志记录

## 故障排除

### 常见问题

1. **推送通知不工作**
   - 检查浏览器权限
   - 确认Service Worker注册
   - 验证VAPID配置

2. **邮件发送失败**
   - 检查SMTP配置
   - 验证速率限制
   - 查看邮件服务日志

3. **告警不触发**
   - 检查规则条件
   - 验证数据格式
   - 查看告警引擎日志

4. **通知延迟**
   - 检查队列状态
   - 验证网络连接
   - 优化批处理大小

### 调试模式

```typescript
// 启用详细日志
if (process.env.NODE_ENV === 'development') {
  alertManager.on('alert_triggered', (data) => {
    console.log('[DEBUG] Alert triggered:', data);
  });
}
```

## API参考

详细的API文档请参考各个组件的TypeScript接口定义。主要接口包括：

- `AlertManager` - 主要管理类
- `AlertEngine` - 规则引擎
- `PushNotificationService` - 推送通知
- `EmailService` - 邮件服务
- `AlertRule` - 告警规则
- `Alert` - 告警实例
- `UserNotificationPreferences` - 用户偏好

## 版本更新

### v1.0.0
- 初始版本发布
- 基础告警引擎
- 多渠道通知支持
- 用户偏好管理

### 计划功能
- 机器学习告警预测
- 更多通知渠道集成
- 可视化告警分析
- 告警模板市场
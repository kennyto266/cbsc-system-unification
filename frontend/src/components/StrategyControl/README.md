# Strategy Control Components

这个包包含用于管理交易策略的React组件，提供策略启用/禁用、批量操作和实时状态管理功能。

## 组件概述

### 1. StrategyToggleEnhanced
增强的策略切换组件，支持单个策略的启用/禁用控制。

**特性：**
- 防抖机制，防止快速重复操作
- 操作确认对话框，防止误操作
- 加载状态指示
- 成功/失败Toast通知
- 键盘无障碍支持
- 多种尺寸（small/medium/large）

**使用示例：**
```tsx
import { StrategyToggleEnhanced } from '@/components/StrategyControl';

<StrategyToggleEnhanced
  strategyId="direct_rsi"
  strategyName="直接RSI情绪策略"
  isActive={false}
  status="inactive"
  onToggle={handleStrategyToggle}
  size="medium"
  showLabels={true}
/>
```

### 2. BatchOperationsPanel
批量操作面板，提供多个策略的批量管理功能。

**特性：**
- 智能选择功能（全选/按状态选择）
- 快速操作按钮（启用/禁用/暂停/停止）
- 操作确认对话框
- 批量操作结果展示
- 策略状态统计

**使用示例：**
```tsx
import { BatchOperationsPanel } from '@/components/StrategyControl';

<BatchOperationsPanel
  strategies={strategies}
  selectedStrategies={selectedStrategies}
  onSelectionChange={setSelectedStrategies}
  onBatchControl={handleBatchControl}
/>
```

### 3. StrategyControlDashboard
完整的策略控制仪表板，集成所有策略管理功能。

**特性：**
- 综合控制中心
- 实时状态监控
- 搜索和过滤功能
- 网格/列表视图切换
- 操作历史记录
- 响应式设计

**使用示例：**
```tsx
import { StrategyControlDashboard } from '@/components/StrategyControl';

<StrategyControlDashboard
  strategies={strategies}
  onStrategyUpdate={handleStrategyUpdate}
/>
```

## API 依赖

组件需要以下API端点（通过strategyControlAdapter服务调用）：

- `GET /api/strategies` - 获取所有策略
- `POST /api/strategies/{id}/toggle` - 切换策略状态
- `POST /api/strategies/batch-control` - 批量控制策略
- `GET /api/strategies/{id}/operation-history` - 获取操作历史

## 数据结构

### StrategyData
```typescript
interface StrategyData {
  id: string;
  name: string;
  isActive: boolean;
  status: 'active' | 'inactive' | 'paused' | 'stopped' | 'error';
  lastUpdated?: string;
  performance?: {
    sharpeRatio: number;
    maxDrawdown: number;
    totalReturn: number;
    winRate: number;
  };
}
```

## 状态管理

组件使用以下状态管理模式：

1. **本地状态** - 使用React useState管理组件内部状态
2. **API状态同步** - 通过回调函数通知父组件状态变更
3. **实时更新** - 支持WebSocket实时状态更新（可选）

## 样式定制

组件使用Tailwind CSS进行样式设计，支持：

- 深色/浅色主题切换
- 响应式布局
- 自定义尺寸
- 状态颜色映射

## 测试

组件包含完整的单元测试和集成测试：

```bash
# 运行测试
npm test StrategyControl

# 运行特定测试
npm test StrategyToggleEnhanced
npm test BatchOperationsPanel
npm test StrategyControlIntegration
```

## 测试覆盖率

- StrategyToggleEnhanced: 95%
- BatchOperationsPanel: 90%
- StrategyControlDashboard: 85%

## 最佳实践

1. **错误处理** - 所有API调用都有错误处理和用户反馈
2. **防抖保护** - 防止用户快速重复操作
3. **确认对话框** - 危险操作需要用户确认
4. **加载状态** - 提供清晰的加载指示
5. **无障碍性** - 支持键盘操作和屏幕阅读器

## 依赖包

- React 18+
- @headlessui/react - UI组件库
- react-toastify - 通知系统
- Tailwind CSS - 样式框架

## 版本历史

### v1.0.0
- 初始版本发布
- 实现基本的策略控制功能
- 支持批量操作
- 完整的测试覆盖

## 故障排除

### 常见问题

1. **策略切换失败**
   - 检查API连接
   - 验证用户权限
   - 查看浏览器控制台错误

2. **批量操作不工作**
   - 确保已选择策略
   - 检查网络连接
   - 验证API端点

3. **样式显示异常**
   - 确保已正确配置Tailwind CSS
   - 检查深色模式设置

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 许可证

MIT License
# Square-UI 现代化改造计划

## 项目概述
将现有的CBSC量化交易系统从Ant Design升级到Square-UI设计系统，打造现代化、企业级的用户界面。

## 技术栈升级方案

### 1. 设计系统升级
- **从**: Ant Design 5.x
- **到**: Square-UI + shadcn/ui
- **优势**:
  - 更现代的设计语言
  - 更好的可定制性
  - TypeScript原生支持
  - 更小的打包体积

### 2. 核心依赖更新
```json
{
  "dependencies": {
    "@square/ui": "latest",
    "@radix-ui/react-*": "latest",
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.6.0",
    "lucide-react": "^0.561.0",
    "framer-motion": "^10.18.0"
  }
}
```

### 3. 移除的依赖
```json
{
  "remove": [
    "@ant-design/icons",
    "@ant-design/colors",
    "@ant-design/plots",
    "antd"
  ]
}
```

## 改造阶段

### Phase 1: 基础设施搭建 ✅
- [x] 创建Square-UI集成配置
- [x] 设置Tailwind CSS 3.4+
- [x] 配置shadcn/ui组件系统
- [x] 建立设计令牌系统

### Phase 2: 核心组件迁移 (进行中)
- [ ] 替换MetricCard组件
- [ ] 升级图表组件系统
- [ ] 重构网格布局系统
- [ ] 更新表单组件

### Phase 3: 页面级重构
- [ ] Dashboard页面现代化
- [ ] 策略管理界面升级
- [ ] CBSC牛熊证页面改造
- [ ] 响应式布局优化

### Phase 4: 性能优化
- [ ] 代码分割优化
- [ ] 懒加载实现
- [ ] 打包体积优化
- [ ] 首屏加载优化

## 设计令牌系统

### 颜色系统
```css
:root {
  /* Primary Colors - Square-UI Blue */
  --square-primary-50: #f0f9ff;
  --square-primary-500: #3b82f6;
  --square-primary-600: #2563eb;
  --square-primary-700: #1d4ed8;

  /* Semantic Colors */
  --square-success: #10b981;
  --square-warning: #f59e0b;
  --square-error: #ef4444;
  --square-info: #06b6d4;

  /* Neutral Colors */
  --square-gray-50: #f9fafb;
  --square-gray-100: #f3f4f6;
  --square-gray-900: #111827;
}
```

### 间距系统
```css
:root {
  --square-space-1: 0.25rem;   /* 4px */
  --square-space-2: 0.5rem;    /* 8px */
  --square-space-3: 0.75rem;   /* 12px */
  --square-space-4: 1rem;      /* 16px */
  --square-space-6: 1.5rem;    /* 24px */
  --square-space-8: 2rem;      /* 32px */
}
```

### 字体系统
```css
:root {
  --square-font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --square-font-mono: 'JetBrains Mono', 'Fira Code', monospace;

  /* Font Sizes */
  --square-text-xs: 0.75rem;    /* 12px */
  --square-text-sm: 0.875rem;   /* 14px */
  --square-text-base: 1rem;     /* 16px */
  --square-text-lg: 1.125rem;   /* 18px */
  --square-text-xl: 1.25rem;    /* 20px */
}
```

## 组件映射表

### Ant Design → Square-UI
| Ant Design | Square-UI | shadcn/ui |
|-----------|-----------|-----------|
| Card      | Card      | Card      |
| Button    | Button    | Button    |
| Statistic | Metric    | Card/Metric |
| Progress  | Progress  | Progress  |
| Tag       | Badge     | Badge     |
| Tabs      | Tabs      | Tabs      |
| Row/Col   | Grid      | Grid      |
| Space     | Flex      | Flex      |
| Typography| Text      | Typography|

## 动画系统

### Framer Motion配置
```typescript
export const squareAnimations = {
  // 页面切换动画
  pageTransition: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -20 }
  },

  // 卡片悬浮效果
  cardHover: {
    hover: { scale: 1.02, y: -4 },
    transition: { type: "spring", stiffness: 300 }
  },

  // 淡入动画
  fadeIn: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    transition: { duration: 0.3 }
  }
}
```

## 迁移策略

### 1. 渐进式迁移
- 保持现有功能不变
- 逐个组件进行替换
- 确保向后兼容

### 2. 并行开发
- 创建新的组件库
- 在feature分支开发
- 通过A/B测试验证

### 3. 风险控制
- 充分的单元测试
- 视觉回归测试
- 性能基准测试

## 性能目标

### 加载性能
- 首屏时间 < 2秒
- 交互延迟 < 100ms
- 打包体积减少30%

### 运行时性能
- 组件渲染时间 < 16ms
- 内存占用优化
- 更流畅的动画效果

## 测试计划

### 单元测试
- 组件功能测试
- 交互行为测试
- 边界条件测试

### 集成测试
- 页面流程测试
- API集成测试
- WebSocket连接测试

### 视觉测试
- 设计一致性检查
- 响应式布局测试
- 主题切换测试

## 上线计划

### 预发布阶段
1. 内部测试 (1周)
2. Alpha版本发布 (内部用户)
3. Beta版本发布 (部分用户)
4. 全量发布

### 回滚方案
- 保留旧版本代码
- 快速切换机制
- 数据备份方案

## 资源需求

### 开发资源
- 前端开发: 2人 × 3周
- UI/UX设计: 1人 × 2周
- 测试: 1人 × 1周

### 技术资源
- 开发环境
- 测试环境
- 监控工具

## 风险评估

### 技术风险
- 组件兼容性问题 (中等)
- 性能下降风险 (低)
- 浏览器兼容性 (低)

### 业务风险
- 用户学习成本 (低)
- 功能缺失风险 (低)
- 数据迁移风险 (极低)

## 成功指标

### 技术指标
- [ ] 代码行数减少20%
- [ ] 打包体积减少30%
- [ ] 首屏加载时间 < 2秒

### 业务指标
- [ ] 用户满意度 > 90%
- [ ] 错误率 < 0.1%
- [ ] 性能分数 > 90

## 下一步行动

1. **本周任务**:
   - 完成Square-UI集成配置
   - 开始核心组件迁移
   - 建立组件库文档

2. **下周任务**:
   - 完成主要页面迁移
   - 性能优化实施
   - 测试用例编写

3. **月底目标**:
   - 完成全部迁移工作
   - 通过所有测试
   - 准备上线发布

---

*创建时间: 2025-01-17*
*负责人: Claude Code Assistant*
*版本: 1.0*
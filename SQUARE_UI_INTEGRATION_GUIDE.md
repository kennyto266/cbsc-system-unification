# Square-UI 现代化改造集成指南

## 项目概述

Square-UI是一个现代化的React组件库，专为量化交易系统设计。本指南将帮助您将现有的Ant Design系统迁移到Square-UI。

## 核心特性

### 🎨 设计系统
- **现代化设计语言** - 基于Material Design 3.0和Apple Human Interface Guidelines
- **CBSC品牌定制** - 专为量化交易系统优化的色彩方案
- **深色/明亮主题** - 完整的主题切换支持
- **响应式设计** - 移动优先的响应式布局

### ⚡ 性能优化
- **代码分割** - 自动按需加载组件
- **Tree Shaking** - 只打包使用的代码
- **轻量级** - 比Ant Design减少30%的打包体积
- **流畅动画** - 基于Framer Motion的高性能动画

### 🔧 开发体验
- **TypeScript原生支持** - 完整的类型定义
- **组件变体系统** - 基于CVA的灵活配置
- **直观的API** - 简单易用的组件接口
- **完整文档** - 详细的API文档和示例

## 快速开始

### 1. 安装依赖

```bash
# 核心依赖
npm install @radix-ui/react-slot @radix-ui/react-icons
npm install class-variance-authority clsx tailwind-merge
npm install lucide-react framer-motion

# 开发依赖
npm install -D tailwindcss-animate
```

### 2. 配置Tailwind CSS

更新`tailwind.config.js`:

```js
module.exports = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Square-UI Color System
        'square-primary': {
          50: '#f0f9ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
        // CBSC Brand Colors
        'cbsc': {
          cyan: '#06b6d4',
          blue: '#3b82f6',
          purple: '#7c3aed',
        },
        // Add more colors as needed
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'float': 'float 6s ease-in-out infinite',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
}
```

### 3. 配置CSS变量

在`src/styles/globals.css`中添加:

```css
:root {
  /* Square-UI Colors */
  --square-primary: #3b82f6;
  --square-primary-hover: #2563eb;
  --square-primary-active: #1d4ed8;

  /* CBSC Brand Colors */
  --cbsc-cyan: #06b6d4;
  --cbsc-blue: #3b82f6;
  --cbsc-purple: #7c3aed;

  /* Semantic Colors */
  --success: #22c55e;
  --warning: #f59e0b;
  --error: #ef4444;
  --info: #3b82f6;
}

/* Dark theme */
.dark {
  --background: #0f172a;
  --foreground: #f1f5f9;
  /* Add more dark theme variables */
}
```

## 组件迁移指南

### 1. 基础组件替换

#### Button 组件
```typescript
// Before (Ant Design)
import { Button } from 'antd'

<Button type="primary" size="large" loading={loading}>
  Submit
</Button>

// After (Square-UI)
import { Button } from '@/components/ui/button'

<Button variant="default" size="lg" loading={loading}>
  Submit
</Button>
```

#### Card 组件
```typescript
// Before
import { Card } from 'antd'

<Card title="Title" extra={<Button>Action</Button>}>
  <p>Content</p>
</Card>

// After
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'

<Card>
  <CardHeader>
    <div className="flex justify-between items-center">
      <CardTitle>Title</CardTitle>
      <Button>Action</Button>
    </div>
  </CardHeader>
  <CardContent>
    <p>Content</p>
  </CardContent>
</Card>
```

### 2. 布局系统替换

#### Grid 替换 Row/Col
```typescript
// Before
import { Row, Col } from 'antd'

<Row gutter={[16, 16]}>
  <Col xs={24} sm={12} lg={8}>
    <Card>Item 1</Card>
  </Col>
  <Col xs={24} sm={12} lg={8}>
    <Card>Item 2</Card>
  </Col>
</Row>

// After
import { Grid } from '@/components/square-ui'

<Grid cols={{ xs: 1, sm: 2, lg: 3 }} gap={4}>
  <Card>Item 1</Card>
  <Card>Item 2</Card>
</Grid>
```

### 3. 高级组件替换

#### MetricCard 替换 Statistic
```typescript
// Before
import { Statistic } from 'antd'

<Statistic
  title="Total Revenue"
  value={112893}
  precision={2}
  valueStyle={{ color: '#3f8600' }}
  prefix={<ArrowUpOutlined />}
  suffix="%"
/>

// After
import { MetricCard } from '@/components/square-ui'

<MetricCard
  title="Total Revenue"
  value={112893}
  precision={2}
  format="currency"
  trend={12.5}
  icon={<TrendingUp />}
  suffix="%"
/>
```

#### Tabs 组件
```typescript
// Before
import { Tabs } from 'antd'

<Tabs defaultActiveKey="1">
  <TabPane tab="Tab 1" key="1">
    Content 1
  </TabPane>
  <TabPane tab="Tab 2" key="2">
    Content 2
  </TabPane>
</Tabs>

// After
import { Tabs } from '@/components/square-ui'

<Tabs
  items={[
    {
      key: '1',
      label: 'Tab 1',
      content: <>Content 1</>,
    },
    {
      key: '2',
      label: 'Tab 2',
      content: <>Content 2</>,
    },
  ]}
  defaultActiveKey="1"
  type="pills"
/>
```

## 组件库结构

```
src/components/
├── ui/                 # shadcn/ui 基础组件
│   ├── button.tsx
│   ├── card.tsx
│   └── ...
├── square-ui/          # Square-UI 定制组件
│   ├── MetricCard.tsx
│   ├── Grid.tsx
│   ├── Tabs.tsx
│   └── index.ts
└── dashboard/          # 业务组件
    ├── MarketOverview.tsx
    └── ...
```

## 主题定制

### 1. 色彩系统
```typescript
// src/styles/theme.ts
export const theme = {
  colors: {
    primary: {
      50: '#f0f9ff',
      500: '#3b82f6',
      900: '#1e3a8a',
    },
    // CBSC品牌色
    cbsc: {
      cyan: '#06b6d4',
      blue: '#3b82f6',
      purple: '#7c3aed',
    },
  },
}
```

### 2. 组件变体
```typescript
// 使用 class-variance-authority
const buttonVariants = cva(
  "inline-flex items-center justify-center",
  {
    variants: {
      variant: {
        default: "bg-primary-600 text-white",
        cbsc: "bg-gradient-to-r from-cbsc-blue to-cbsc-cyan",
      },
      size: {
        sm: "h-8 px-3",
        lg: "h-12 px-8",
      },
    },
  }
)
```

## 动画系统

### 1. Framer Motion配置
```typescript
// 页面过渡动画
const pageVariants = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -20 },
}

// 组件动画
<motion.div
  variants={pageVariants}
  initial="initial"
  animate="animate"
  exit="exit"
  transition={{ duration: 0.3 }}
>
  Content
</motion.div>
```

### 2. 预设动画
```css
/* Tailwind动画类 */
@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
}

.animate-float {
  animation: float 6s ease-in-out infinite;
}
```

## 性能优化

### 1. 代码分割
```typescript
// 路由级别的代码分割
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Settings = lazy(() => import('./pages/Settings'))

// 组件级别的懒加载
const HeavyChart = lazy(() => import('./components/HeavyChart'))
```

### 2. 组件优化
```typescript
// 使用 React.memo 优化重渲染
export const MetricCard = React.memo<MetricCardProps>((props) => {
  // Component implementation
})

// 使用 useMemo 缓存计算
const expensiveValue = useMemo(() => {
  return computeExpensiveValue(data)
}, [data])
```

## 测试策略

### 1. 单元测试
```typescript
// 使用 @testing-library/react
import { render, screen } from '@testing-library/react'
import { MetricCard } from '@/components/square-ui'

test('renders metric card correctly', () => {
  render(<MetricCard title="Test" value={100} />)
  expect(screen.getByText('Test')).toBeInTheDocument()
  expect(screen.getByText('100')).toBeInTheDocument()
})
```

### 2. 视觉回归测试
```typescript
// 使用 Chromatic 或 Percy
import { Story } from '@storybook/react'

export const Default: Story = {
  render: () => <MetricCard title="Test" value={100} />,
}
```

## 迁移检查清单

### Phase 1: 基础设施
- [x] 安装Square-UI依赖
- [x] 配置Tailwind CSS
- [x] 设置CSS变量
- [x] 创建基础组件
- [ ] 配置路径别名

### Phase 2: 组件迁移
- [x] Button组件
- [x] Card组件
- [x] MetricCard组件
- [x] Grid布局系统
- [x] Tabs组件
- [ ] Input组件
- [ ] Select组件
- [ ] Modal组件
- [ ] Table组件

### Phase 3: 页面迁移
- [x] Dashboard页面
- [ ] Settings页面
- [ ] Profile页面
- [ ] CBSC页面
- [ ] Charts页面

### Phase 4: 优化和测试
- [ ] 性能优化
- [ ] 响应式测试
- [ ] 主题切换测试
- [ ] 可访问性测试
- [ ] 视觉回归测试

## 常见问题

### Q: 如何处理Ant Design特有的API？
A: Square-UI提供了兼容层，大部分API可以直接迁移。特殊功能需要自定义实现。

### Q: 如何处理主题切换？
A: 使用CSS变量和Tailwind的dark模式支持，可以实现平滑的主题切换。

### Q: 如何处理国际化？
A: Square-UI与react-intact等国际化库兼容，可以使用相同的i18n策略。

### Q: 如何处理表单验证？
A: 推荐使用react-hook-form与Zod或Yup结合，提供类型安全的表单验证。

## 下一步

1. **完成组件迁移** - 继续迁移剩余的Ant Design组件
2. **优化性能** - 实施代码分割和懒加载
3. **完善文档** - 创建完整的组件文档和示例
4. **测试覆盖** - 编写全面的单元测试和集成测试
5. **部署上线** - 逐步灰度发布新版本

## 贡献指南

欢迎为Square-UI项目贡献代码！请遵循以下步骤：

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 许可证

Square-UI采用MIT许可证 - 查看[LICENSE](LICENSE)文件了解详情。

---

*创建时间: 2025-01-17*
*维护者: Square-UI Team*
*版本: 1.0.0*
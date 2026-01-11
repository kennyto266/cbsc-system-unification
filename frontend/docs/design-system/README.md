# CBSC Design System - UI/UX设计系统

## 概述

CBSC设计系统是一套完整的企业级UI/UX设计语言，为量化交易策略管理系统Dashboard提供统一的视觉规范和交互体验。

## 核心特性

- 🎨 **统一的视觉语言** - 基于设计令牌的色彩、字体、间距系统
- 🌓 **主题切换** - 支持亮色/暗色主题，满足不同场景需求
- 📱 **响应式设计** - 适配桌面、平板、移动端等多种设备
- ♿ **无障碍支持** - 符合WCAG 2.1 AA标准，支持键盘导航
- ⚡ **高性能** - 优化的动画和交互，流畅的用户体验
- 🛠️ **易于定制** - 基于CSS变量和TypeScript，灵活可扩展

## 设计原则

### 一致性 (Consistency)
- 统一的视觉元素和交互模式
- 可预测的用户体验
- 降低学习成本

### 简洁性 (Simplicity)
- 清晰的信息层次
- 减少认知负担
- 聚焦核心功能

### 可访问性 (Accessibility)
- 键盘导航支持
- 屏幕阅读器友好
- 高对比度模式
- 动画减弱选项

### 可维护性 (Maintainability)
- 基于设计令牌的系统化方法
- 组件化开发
- 清晰的文档和指南

## 目录结构

```
frontend/src/
├── styles/
│   ├── tokens/           # 设计令牌
│   │   ├── colors.ts     # 色彩系统
│   │   ├── typography.ts # 字体系统
│   │   ├── spacing.ts    # 间距系统
│   │   ├── effects.ts    # 动效系统
│   │   └── index.ts      # 令牌导出
│   ├── themes/           # 主题配置
│   │   ├── light.ts      # 亮色主题
│   │   ├── dark.ts       # 暗色主题
│   │   └── index.ts      # 主题管理
│   └── globals.css       # 全局样式
├── components/ui/        # UI组件库
│   ├── Button.tsx        # 按钮组件
│   ├── ThemeToggle.tsx   # 主题切换
│   ├── Card.tsx          # 卡片组件
│   ├── Input.tsx         # 输入框组件
│   ├── Modal.tsx         # 模态框组件
│   └── index.ts          # 组件导出
└── docs/design-system/   # 设计文档
```

## 快速开始

### 1. 安装依赖

```bash
npm install clsx framer-motion
```

### 2. 导入样式

```tsx
// 在主入口文件导入全局样式
import '@/styles/globals.css'
```

### 3. 使用主题

```tsx
import { ThemeProvider, useTheme } from '@/styles/themes'

function App() {
  return (
    <ThemeProvider>
      <YourApp />
    </ThemeProvider>
  )
}

function YourComponent() {
  const { theme, setTheme } = useTheme()

  return (
    <div>
      <p>Current theme: {theme}</p>
      <button onClick={() => setTheme('dark')}>Switch to Dark</button>
    </div>
  )
}
```

### 4. 使用组件

```tsx
import { Button, Card, ThemeToggle } from '@/components/ui'

function Example() {
  return (
    <Card>
      <h2>Welcome to CBSC</h2>
      <Button variant="primary">Get Started</Button>
      <ThemeToggle showLabel />
    </Card>
  )
}
```

## 设计令牌

### 色彩系统

#### 主色调
- Primary Blue: `#0284c7`
- Primary Hover: `#0369a1`
- Primary Active: `#0284c7`

#### 语义色
- Success: `#22c55e`
- Warning: `#f59e0b`
- Error: `#ef4444`
- Info: `#3b82f6`

#### 中性色
- Gray Scale: `#ffffff` → `#0f172a` (11级)

### 字体系统

#### 字体族
- Sans: Inter (支持中英文)
- Mono: JetBrains Mono

#### 字号层级
- xs: 0.75rem (12px)
- sm: 0.875rem (14px)
- base: 1rem (16px)
- lg: 1.125rem (18px)
- xl: 1.25rem (20px)
- ...

### 间距系统

基于8px网格系统：
- xs: 0.5rem (8px)
- sm: 1rem (16px)
- md: 1.5rem (24px)
- lg: 2rem (32px)
- xl: 3rem (48px)

## 组件库

### Button 按钮

```tsx
import { Button, ButtonGroup } from '@/components/ui'

// 基础用法
<Button variant="primary">Primary Button</Button>
<Button variant="secondary">Secondary Button</Button>
<Button variant="outline">Outline Button</Button>
<Button variant="ghost">Ghost Button</Button>

// 不同尺寸
<Button size="sm">Small</Button>
<Button size="md">Medium</Button>
<Button size="lg">Large</Button>

// 带图标
<Button icon={<PlusIcon />} left>Add Item</Button>

// 加载状态
<Button loading>Loading...</Button>

// 按钮组
<ButtonGroup>
  <Button>Cancel</Button>
  <Button variant="primary">Submit</Button>
</ButtonGroup>
```

### Card 卡片

```tsx
import { Card } from '@/components/ui'

<Card>
  <Card.Header>
    <h3>Card Title</h3>
  </Card.Header>
  <Card.Body>
    <p>Card content goes here.</p>
  </Card.Body>
  <Card.Footer>
    <Button>Action</Button>
  </Card.Footer>
</Card>
```

### Input 输入框

```tsx
import { Input } from '@/components/ui'

<Input
  placeholder="Enter your name"
  label="Name"
  error="This field is required"
  disabled={false}
/>
```

### Modal 模态框

```tsx
import { Modal } from '@/components/ui'

const [isOpen, setIsOpen] = useState(false)

<Modal
  isOpen={isOpen}
  onClose={() => setIsOpen(false)}
  title="Modal Title"
>
  <p>Modal content</p>
</Modal>
```

### ThemeToggle 主题切换

```tsx
import { ThemeToggle, ThemeSelector } from '@/components/ui'

// 简单切换
<ThemeToggle />

// 带标签
<ThemeToggle showLabel />

// 下拉选择器
<ThemeSelector />
```

## 主题系统

### 使用主题

```tsx
import { useTheme } from '@/styles/themes'

function Component() {
  const { theme, themeConfig, setTheme, toggleTheme } = useTheme()

  return (
    <div style={{
      backgroundColor: themeConfig.colors.background.primary,
      color: themeConfig.colors.text.primary
    }}>
      Current theme: {theme}
      <button onClick={toggleTheme}>Toggle Theme</button>
    </div>
  )
}
```

### 自定义主题

```tsx
import { Theme } from '@/styles/themes'

const customTheme: Theme = {
  name: 'custom',
  colors: {
    // 自定义色彩
  },
  // ...其他配置
}
```

## 响应式设计

使用Tailwind CSS的响应式断点：
- Mobile: < 768px
- Tablet: 768px - 1024px
- Desktop: > 1024px

```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
  {/* 响应式布局 */}
</div>
```

## 无障碍支持

### 键盘导航
所有交互组件支持Tab键导航和Enter/Space激活。

### ARIA标签
```tsx
<Button
  aria-label="Close dialog"
  aria-describedby="dialog-description"
>
  Close
</Button>
```

### 焦点管理
```tsx
// 清晰的焦点指示器
:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}
```

## 最佳实践

### 1. 组件使用
- 优先使用设计系统组件
- 保持一致的变体和尺寸
- 使用语义化的颜色（success/error等）

### 2. 布局
- 遵循8px网格系统
- 使用合理的间距
- 保持视觉层次

### 3. 交互
- 提供即时反馈
- 使用适当的动画时长
- 支持加载状态

### 4. 代码
- 使用TypeScript类型
- 添加适当的注释
- 遵循命名约定

## 贡献指南

### 添加新组件

1. 在`/components/ui`创建组件文件
2. 使用TypeScript定义Props接口
3. 遵循现有的代码风格
4. 添加组件文档
5. 在`index.ts`中导出

### 更新设计令牌

1. 修改`/styles/tokens`中的相应文件
2. 更新相关组件
3. 测试所有使用该令牌的组件
4. 更新文档

## 相关资源

- [Tailwind CSS文档](https://tailwindcss.com/docs)
- [Inter字体](https://rsms.me/inter/)
- [Material Design](https://material.io/design)
- [Web无障碍指南](https://www.w3.org/WAI/WCAG21/quickref/)
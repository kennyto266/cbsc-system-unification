# CBSC前端系统UI/UX统一规范

## 设计原则

### 1. 一致性优先
- 所有页面使用统一的设计语言
- 交互行为保持一致
- 视觉元素遵循相同规范

### 2. 用户导向
- 基于用户工作流程设计
- 减少认知负担
- 提供清晰的操作反馈

### 3. 专业可信
- 体现金融系统的专业性
- 数据展示清晰准确
- 错误处理友好明确

## 设计系统

### 色彩规范

#### 主色调
```css
:root {
  /* 品牌色 - 深蓝色系 */
  --primary-1: #f0f5ff;  /* 背景色 */
  --primary-2: #d6e4ff;
  --primary-3: #adc6ff;
  --primary-4: #85a5ff;
  --primary-5: #597ef7;  /* 常规使用 */
  --primary-6: #3951e6;  /* 主色 */
  --primary-7: #2841c7;

  /* 成功色 - 绿色系 */
  --success-1: #f6ffed;
  --success-2: #d9f7be;
  --success-3: #b7eb8f;
  --success-4: #95de64;
  --success-5: #73d13d;
  --success-6: #52c41a;  /* 主成功色 */

  /* 警告色 - 橙色系 */
  --warning-1: #fffbe6;
  --warning-2: #fff1b8;
  --warning-3: #ffe58f;
  --warning-4: #ffd666;
  --warning-5: #ffc53d;
  --warning-6: #faad14;  /* 主警告色 */

  /* 错误色 - 红色系 */
  --error-1: #fff2f0;
  --error-2: #ffccc7;
  --error-3: #ffa39e;
  --error-4: #ff7875;
  --error-5: #ff4d4f;
  --error-6: #f5222d;  /* 主错误色 */

  /* 中性色 */
  --text-primary: #262626;
  --text-secondary: #595959;
  --text-disabled: #bfbfbf;
  --border-color: #d9d9d9;
  --background: #f5f5f5;
}
```

#### 金融数据专用色
```css
:root {
  /* 涨跌颜色 */
  --color-up: #f5222d;      /* 上涨/红色 */
  --color-down: #52c41a;    /* 下跌/绿色 */
  --color-flat: #8c8c8c;    /* 持平 */

  /* 风险等级 */
  --risk-low: #52c41a;      /* 低风险 */
  --risk-medium: #faad14;   /* 中风险 */
  --risk-high: #f5222d;     /* 高风险 */
}
```

### 字体规范

#### 字体族
```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
             'Helvetica Neue', Arial, 'Noto Sans', sans-serif;
```

#### 字号层级
```css
:root {
  /* 标题 */
  --font-size-h1: 38px;    /* 页面主标题 */
  --font-size-h2: 30px;    /* 区块标题 */
  --font-size-h3: 24px;    /* 小节标题 */
  --font-size-h4: 20px;    /* 组件标题 */

  /* 正文 */
  --font-size-lg: 16px;    /* 大号正文 */
  --font-size-md: 14px;    /* 常规正文 */
  --font-size-sm: 12px;    /* 小号文字 */

  /* 字重 */
  --font-weight-light: 300;
  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;
}
```

### 间距规范

#### 基础间距单位
```css
:root {
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
  --spacing-xxl: 48px;
}
```

#### 组件间距
- 页面边距: 24px
- 区块间距: 32px
- 组件间距: 16px
- 元素间距: 8px

## 组件规范

### 1. 布局组件

#### 页面布局
```
┌─────────────────────────────────┐
│              Header              │ 64px
├─────────────┬───────────────────┤
│             │                   │
│   Sidebar   │      Main         │
│   240px     │    flex-1         │
│             │                   │
└─────────────┴───────────────────┘
```

#### 卡片布局
```typescript
interface CardProps {
  title: string;
  extra?: React.ReactNode;
  children: React.ReactNode;
  bordered?: boolean;
  hoverable?: boolean;
  size?: 'default' | 'small';
}
```

### 2. 数据展示组件

#### 表格规范
- 斑马纹: 每3行交替
- 固定表头: 超过10行时
- 分页: 每页20/50/100条
- 排序: 数字、日期列默认支持
- 筛选: 关键字段支持快速筛选

#### 图表规范
```typescript
// 统一图表配置
interface ChartConfig {
  colors: {
    primary: string[];
    secondary: string[];
  };
  grid: {
    show: boolean;
    color: string;
  };
  tooltip: {
    trigger: 'axis' | 'item';
    backgroundColor: string;
  };
  animation: {
    duration: number;
    easing: string;
  };
}
```

### 3. 表单组件

#### 表单布局
- 标签位置: 左对齐，宽度120px
- 输入框高度: 32px（默认）/ 40px（大号）
- 错误提示: 输入框下方红色文字
- 必填标记: 红色星号(*)

#### 验证规则
- 实时验证: 失焦时触发
- 错误状态: 红色边框 + 错误图标
- 成功状态: 绿色边框 + 成功图标

## 交互规范

### 1. 导航交互

#### 面包屑
- 分隔符: "/"
- 可点击: 除当前页外都可点击
- 省略: 超过5项时省略中间

#### 菜单展开
- 默认展开: 一级菜单
- 悬停延迟: 300ms
- 动画时长: 200ms

### 2. 操作反馈

#### 加载状态
- 按钮加载: 显示loading图标
- 表格加载: 骨架屏
- 页面加载: 进度条

#### 操作结果
- 成功: 绿色toast提示
- 错误: 红色modal弹窗
- 警告: 橙色banner提示

### 3. 数据操作

#### 批量操作
- 选择: Checkbox列
- 操作栏: 固定底部
- 确认: 危险操作需二次确认

#### 搜索过滤
- 实时搜索: 500ms防抖
- 高级搜索: 折叠面板
- 保存条件: 常用搜索可保存

## 响应式设计

### 断点设置
```css
/* 移动端 */
@media (max-width: 768px) {
  /* 侧边栏折叠 */
  /* 表格横向滚动 */
  /* 卡片堆叠显示 */
}

/* 平板 */
@media (min-width: 769px) and (max-width: 1024px) {
  /* 侧边栏收缩 */
  /* 表格自适应 */
}

/* 桌面端 */
@media (min-width: 1025px) {
  /* 完整布局 */
}
```

### 适配规则
1. **导航适配**
   - 移动端: 底部标签栏
   - 桌面端: 左侧菜单

2. **表格适配**
   - 移动端: 卡片式展示
   - 桌面端: 标准表格

3. **表单适配**
   - 移动端: 单列布局
   - 桌面端: 多列布局

## 无障碍设计

### 1. 键盘导航
- Tab顺序: 逻辑清晰
- 快捷键: 常用功能支持
- 焦点指示: 明显可见

### 2. 屏幕阅读器
- 语义化HTML标签
- ARIA属性完善
- 图片alt文本

### 3. 视觉辅助
- 对比度: 符合WCAG AA标准
- 字体缩放: 支持200%缩放
- 色盲友好: 不仅依赖颜色区分

## 特殊场景设计

### 1. 数据异常
- 空状态: 友好的提示插图
- 加载失败: 重试按钮
- 无权限: 权限申请指引

### 2. 实时数据
- 更新动画: 淡入淡出
- 变化提示: 高亮闪烁
- 延迟说明: 超过3秒显示

### 3. 批量操作
- 进度指示: 实时进度条
- 结果汇总: 成功/失败统计
- 错误详情: 可展开查看

## 实施计划

### Phase 1: 基础组件（3天）
1. 创建基础组件库
2. 定义颜色、字体、间距
3. 实现布局组件

### Phase 2: 业务组件（5天）
1. 表格组件封装
2. 表单组件封装
3. 图表组件封装

### Phase 3: 页面改造（7天）
1. 首页改造
2. 列表页改造
3. 详情页改造
4. 表单页改造

### Phase 4: 验证优化（3天）
1. 设计review
2. 用户测试
3. 细节优化

## 质量保证

### 设计检查清单
- [ ] 颜色使用符合规范
- [ ] 字体层级正确
- [ ] 间距统一
- [ ] 交互一致
- [ ] 响应式适配
- [ ] 无障碍支持

### 代码规范
```typescript
// 组件命名: PascalCase
export const DataTable: React.FC<DataTableProps> = () => {};

// 样式类名: BEM命名法
.data-table {}
.data-table__header {}
.data-table__row--selected {}

// Props接口: 明确定义
interface DataTableProps {
  data: DataItem[];
  columns: ColumnConfig[];
  loading?: boolean;
  onPageChange?: (page: number) => void;
}
```

---

*文档版本: 1.0*
*最后更新: 2025-12-12*
*维护团队: Frontend Team*
# Strategy Visualization Components

混合策略可视化组件库，提供完整的策略分析和参数优化功能。

## 组件概览

### 1. DualAxisChart
双轴图表组件，支持同时展示价格、成交量、经济指标等多维度数据。

**主要功能：**
- 支持价格线和成交量柱状图组合展示
- 可配置的交易信号标记
- 移动平均线展示
- 经济指标叠加显示
- 自定义阈值线
- 响应式设计

**使用示例：**
```tsx
<DualAxisChart
  data={data}
  priceKey="price"
  volumeKey="volume"
  signalKey="signal"
  showVolume={true}
  showSignals={true}
  showThresholds={true}
  thresholds={{ upper: 110, lower: 90 }}
  height={400}
/>
```

### 2. MixedStrategyViewer
混合策略综合视图组件，集成时间范围选择、图表控制和统计信息。

**主要功能：**
- 多时间范围切换（1天、1周、1月、1年、全部）
- 自定义日期范围筛选
- 可切换的图表元素控制
- 实时统计信息展示
- 数据点详情弹窗
- 导出功能

**使用示例：**
```tsx
<MixedStrategyViewer
  data={data}
  title="混合策略视图"
  onTimeframeChange={handleTimeframeChange}
  onExport={handleExport}
  showVolume={true}
  showSignals={true}
/>
```

### 3. TimeframeSelector
时间范围选择器组件。

**使用示例：**
```tsx
<TimeframeSelector
  value="1m"
  onChange={handleTimeframeChange}
  label="时间范围"
  compact={false}
/>
```

### 4. WeightAnalysis
权重分析组件，提供权重分布可视化和贡献度分析。

**主要功能：**
- 饼图展示权重分布
- 柱状图展示贡献度
- 雷达图多维度分析
- 实时权重调整
- 性能指标计算
- 相关性矩阵展示

**使用示例：**
```tsx
<WeightAnalysis
  weights={weights}
  contributions={contributions}
  adjustable={true}
  showContributions={true}
  showMetrics={true}
  showRadar={true}
  onWeightChange={handleWeightChange}
/>
```

### 5. ParameterPreview
参数预览组件，支持实时参数调整和性能预览。

**主要功能：**
- 多种参数类型支持（数字、选择、布尔、滑块）
- 实时性能指标预览
- 参数影响分析
- 参数验证和约束
- 防抖优化
- 参数导出/导入

**使用示例：**
```tsx
<ParameterPreview
  parameters={parameters}
  parameterConfig={parameterConfig}
  previewResults={results}
  adjustable={true}
  onParameterChange={handleParameterChange}
  showImpact={true}
/>
```

### 6. SensitivityAnalysis
参数敏感性分析组件。

**主要功能：**
- 单参数敏感性曲线
- 双参数热力图分析
- 最优参数识别
- 参数优化建议
- 自定义范围分析

**使用示例：**
```tsx
<SensitivityAnalysis
  parameters={parameters}
  sensitivityData={sensitivityData}
  optimalParameters={optimal}
  recommendations={recommendations}
  onOptimize={handleOptimize}
/>
```

## 数据类型定义

### MixedStrategyData
```typescript
interface MixedStrategyData {
  date: string
  timestamp: number
  // 价格数据
  price?: number
  open?: number
  high?: number
  low?: number
  close?: number
  // 经济指标
  gdp?: number
  inflation?: number
  unemployment?: number
  interest_rate?: number
  // 成交量数据
  volume?: number
  // 信号数据
  signal?: number // 1: buy, -1: sell, 0: hold
  signal_strength?: number
  // 技术指标
  ma_short?: number
  ma_long?: number
  rsi?: number
  // 策略权重
  price_weight?: number
  economic_weight?: number
  volume_weight?: number
  technical_weight?: number
}
```

### StrategyWeights
```typescript
interface StrategyWeights {
  price: number
  economic: number
  volume: number
  technical: number
  [key: string]: number
}
```

### ParameterConfig
```typescript
interface ParameterConfig {
  type: 'number' | 'select' | 'boolean' | 'range'
  label: string
  min?: number
  max?: number
  step?: number
  options?: string[]
  unit?: string
  description?: string
  impact?: 'low' | 'medium' | 'high'
}
```

## 最佳实践

1. **性能优化**
   - 使用防抖处理参数变化
   - 大数据集时考虑虚拟滚动
   - 合理使用缓存机制

2. **响应式设计**
   - 所有组件都支持响应式布局
   - 移动端自动调整图表尺寸
   - 使用CSS变量实现主题适配

3. **数据验证**
   - 始终验证输入数据格式
   - 处理边界值和异常情况
   - 提供友好的错误提示

4. **可访问性**
   - 支持键盘导航
   - 提供ARIA标签
   - 确保颜色对比度

## 依赖要求

- React 18+
- Recharts 2.0+
- TypeScript 4.5+
- Tailwind CSS 3.0+

## 开发和测试

```bash
# 运行单元测试
npm test -- --testPathPatterns="StrategyVisualization"

# 运行特定组件测试
npm test DualAxisChart.test.tsx

# 生成测试覆盖率报告
npm test -- --coverage --testPathPatterns="StrategyVisualization"
```

## 更新日志

### v1.0.0
- 初始版本发布
- 实现所有核心功能组件
- 完整的TypeScript类型定义
- 单元测试覆盖率 > 90%
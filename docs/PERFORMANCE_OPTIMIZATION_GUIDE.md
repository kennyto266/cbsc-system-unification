# 技术指標Dashboard性能優化指南

## 概述

本指南详细说明了技术指标Dashboard的性能优化策略，针对477种技术指标同时渲染的性能挑战提供了全面的解决方案。

## 性能目標

- **圖表渲染時間** < 500ms
- **內存使用穩定**，無洩漏
- **支持100併發用戶**
- **實時更新延遲** < 100ms
- **首次加載時間** < 2s

## 核心優化策略

### 1. 組件級優化

#### React.memo 优化
```typescript
// 使用 memo 和自定义比较函数
const OptimizedIndicatorCard = memo(({ indicator, ...props }) => {
  // 组件实现
}, (prevProps, nextProps) => {
  // 只比较真正影响渲染的属性
  return prevProps.indicator.id === nextProps.indicator.id &&
         prevProps.indicator.favorite === nextProps.indicator.favorite
})
```

#### useMemo 和 useCallback 优化
```typescript
// 缓存计算结果
const optimizedData = useMemo(() => {
  return data.map(item => expensiveCalculation(item))
}, [data])

// 缓存函数引用
const handleClick = useCallback(() => {
  // 处理逻辑
}, [dependencies])
```

### 2. 渲染性能優化

#### 懒加載 (Lazy Loading)
```typescript
// 使用 Intersection Observer 实现懒加载
const { isIntersecting } = useIntersectionObserver(elementRef, {
  threshold: 0.1,
  rootMargin: '100px'
})

// 仅在可见时渲染
{isIntersecting ? <ExpensiveComponent /> : <Placeholder />}
```

#### 虛擬化列表 (Virtualization)
```typescript
// 使用 react-window 实现虚拟滚动
import { FixedSizeList as List } from 'react-window'

const VirtualizedList = ({ items }) => (
  <List
    height={600}
    itemCount={items.length}
    itemSize={120}
    overscanCount={5}
  >
    {({ index, style }) => (
      <div style={style}>
        <ItemComponent data={items[index]} />
      </div>
    )}
  </List>
)
```

### 3. 數據處理優化

#### Web Workers
```typescript
// 创建 Worker 池
const workerPool = new Array(navigator.hardwareConcurrency || 4)
  .fill(null)
  .map(() => new Worker('/dataWorker.js'))

// 分配任务到 Worker
const processLargeDataset = async (data) => {
  const worker = getAvailableWorker()
  return new Promise((resolve) => {
    worker.onmessage = (e) => resolve(e.data)
    worker.postMessage(data)
  })
}
```

#### 數據抽樣和聚合
```typescript
// 大数据集抽样
const sampleData = (data, maxPoints = 1000) => {
  if (data.length <= maxPoints) return data

  const step = Math.ceil(data.length / maxPoints)
  return data.filter((_, i) => i % step === 0)
}

// 数据聚合
const aggregateData = (data, windowSize) => {
  const result = []
  for (let i = 0; i < data.length; i += windowSize) {
    const window = data.slice(i, i + windowSize)
    const avg = window.reduce((sum, v) => sum + v, 0) / window.length
    result.push(avg)
  }
  return result
}
```

### 4. 內存管理

#### 組件卸載清理
```typescript
useEffect(() => {
  return () => {
    // 清理定时器
    if (timerRef.current) {
      clearInterval(timerRef.current)
    }

    // 清理图表实例
    if (chartInstanceRef.current) {
      chartInstanceRef.current.destroy()
    }

    // 清理事件监听器
    elementRef.current?.removeEventListener('click', handler)
  }
}, [])
```

#### 圖表實例管理
```typescript
// 图表实例缓存和清理
const chartCache = new Map<string, Chart>()

const getOrCreateChart = (id, config) => {
  if (chartCache.has(id)) {
    const chart = chartCache.get(id)
    chart.update()
    return chart
  }

  const newChart = new Chart(config)
  chartCache.set(id, newChart)
  return newChart
}

// 定期清理未使用的图表
const cleanupCharts = () => {
  const activeCharts = getActiveChartIds()
  for (const [id, chart] of chartCache.entries()) {
    if (!activeCharts.includes(id)) {
      chart.destroy()
      chartCache.delete(id)
    }
  }
}
```

### 5. 實時更新優化

#### WebSocket 連接優化
```typescript
// 使用单例 WebSocket 服务
class WebSocketService {
  private static instance: WebSocketService
  private ws: WebSocket | null = null
  private subscribers: Map<string, Set<(data: any) => void>> = new Map()

  static getInstance(): WebSocketService {
    if (!WebSocketService.instance) {
      WebSocketService.instance = new WebSocketService()
    }
    return WebSocketService.instance
  }

  subscribe(channel: string, callback: (data: any) => void) {
    if (!this.subscribers.has(channel)) {
      this.subscribers.set(channel, new Set())
    }
    this.subscribers.get(channel)!.add(callback)
  }

  unsubscribe(channel: string, callback: (data: any) => void) {
    this.subscribers.get(channel)?.delete(callback)
  }
}
```

#### 防抖和節流
```typescript
// 防抖处理
const useDebounce = (value, delay) => {
  const [debouncedValue, setDebouncedValue] = useState(value)

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => clearTimeout(handler)
  }, [value, delay])

  return debouncedValue
}

// 节流处理
const useThrottle = (callback, delay) => {
  const lastRun = useRef(Date.now())

  return (...args) => {
    if (Date.now() - lastRun.current >= delay) {
      callback(...args)
      lastRun.current = Date.now()
    }
  }
}
```

### 6. 圖表渲染優化

#### Chart.js 優化配置
```typescript
const optimizedChartOptions = {
  // 关闭动画提高性能
  animation: false,

  // 优化交互
  interaction: {
    intersect: false,
    mode: 'index'
  },

  // 采样减少渲染点数
  sampling: {
    enabled: true,
    algorithm: 'min-max'
  },

  // 优化缩放
  scales: {
    x: {
      ticks: {
        maxTicksLimit: 20, // 限制刻度数量
      },
      grid: {
        display: false // 隐藏网格线
      }
    }
  },

  // 优化插件
  plugins: {
    legend: {
      labels: {
        usePointStyle: true,
        boxWidth: 8 // 减小图例尺寸
      }
    },
    tooltip: {
      enabled: true,
      mode: 'index',
      intersect: false
    }
  }
}
```

#### Canvas 渲染優化
```typescript
// 使用离屏 Canvas
const offscreenCanvas = new OffscreenCanvas(width, height)
const offscreenContext = offscreenCanvas.getContext('2d')

// 批量渲染
const batchRender = () => {
  requestAnimationFrame(() => {
    // 批量更新所有图表
    charts.forEach(chart => chart.update('none'))
  })
}
```

### 7. 緩存策略

#### 數據緩存
```typescript
// 使用 React Query 缓存 API 数据
const { data } = useQuery({
  queryKey: ['indicators', category],
  queryFn: fetchIndicators,
  staleTime: 5 * 60 * 1000, // 5分钟
  cacheTime: 10 * 60 * 1000 // 10分钟
})

// 内存缓存计算结果
const memoizedCalculations = new Map<string, any>()

const getCachedCalculation = (key, calculator) => {
  if (memoizedCalculations.has(key)) {
    return memoizedCalculations.get(key)
  }

  const result = calculator()
  memoizedCalculations.set(key, result)
  return result
}
```

#### 組件緩存
```typescript
// 使用 React.lazy 和 Suspense
const LazyChart = React.lazy(() => import('./HeavyChart'))

<Suspense fallback={<ChartSkeleton />}>
  <LazyChart />
</Suspense>
```

## 性能監控

### 1. FPS 監控
```typescript
const useFPSMonitor = () => {
  const [fps, setFps] = useState(60)
  const frameCount = useRef(0)
  const lastTime = useRef(performance.now())

  useEffect(() => {
    const measureFPS = () => {
      frameCount.current++
      const currentTime = performance.now()
      const delta = currentTime - lastTime.current

      if (delta >= 1000) {
        setFps(Math.round((frameCount.current * 1000) / delta))
        frameCount.current = 0
        lastTime.current = currentTime
      }

      requestAnimationFrame(measureFPS)
    }

    measureFPS()
  }, [])

  return fps
}
```

### 2. 內存監控
```typescript
const monitorMemory = () => {
  if ('memory' in performance) {
    const memory = (performance as any).memory
    console.log({
      used: Math.round(memory.usedJSHeapSize / 1048576) + ' MB',
      total: Math.round(memory.totalJSHeapSize / 1048576) + ' MB',
      limit: Math.round(memory.jsHeapSizeLimit / 1048576) + ' MB'
    })
  }
}
```

### 3. 渲染性能分析
```typescript
// 使用 React DevTools Profiler
<Profiler id="StrategyChart" onRender={(id, phase, actualDuration) => {
  console.log('Chart render time:', actualDuration)
}}>
  <StrategyChart />
</Profiler>

// 使用 Performance API
performance.mark('chart-render-start')
// 渲染逻辑
performance.mark('chart-render-end')
performance.measure('chart-render', 'chart-render-start', 'chart-render-end')
```

## 最佳實踐

### 1. 組件設計原則
- 保持组件单一职责
- 避免过度嵌套
- 合理使用 memo
- 正确设置依赖项

### 2. 狀態管理
- 避免不必要的状态提升
- 使用 useReducer 复杂状态
- 考虑状态库缓存
- 批量更新状态

### 3. 事件處理
- 使用事件委托
- 防抖频繁触发事件
- 移除未使用的事件监听器
- 使用 passive 事件监听器

### 4. 資源加載
- 预加载关键资源
- 延迟加载非关键资源
- 使用 CDN 加速
- 压缩和优化资源

### 5. 錯誤處理
- 捕获并记录错误
- 提供降级方案
- 避免错误扩散
- 实现错误边界

## 性能測試

### 1. 加載性能測試
```javascript
// 使用 Web Vitals
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals'

getCLS(console.log)
getFID(console.log)
getFCP(console.log)
getLCP(console.log)
getTTFB(console.log)
```

### 2. 壓力測試
```javascript
// 模拟大量数据
const generateLargeDataset = (size) => {
  return Array.from({ length: size }, (_, i) => ({
    id: i,
    value: Math.random() * 100,
    timestamp: Date.now() + i
  }))
}

// 性能基准测试
const benchmark = (fn, iterations = 1000) => {
  const start = performance.now()
  for (let i = 0; i < iterations; i++) {
    fn()
  }
  const end = performance.now()
  return end - start
}
```

## 故障排除

### 常見問題

1. **內存洩漏**
   - 檢查未清理的定時器
   - 確認事件監聽器已移除
   - 驗證圖表實例已銷毀
   - 使用 Chrome DevTools 分析

2. **渲染卡頓**
   - 減少同時渲染的組件數量
   - 使用虛擬化列表
   - 開啟懶加載
   - 優化動畫效果

3. **數據加載慢**
   - 實施分頁和篩選
   - 使用數據緩存
   - 優化 API 響應
   - 考慮使用 GraphQL

4. **WebSocket 連接問題**
   - 實施重連機制
   - 設置心跳檢測
   - 優化消息批處理
   - 監控連接狀態

## 總結

通过以上优化策略，技术指标Dashboard能够高效地处理477种指标的渲染和交互，提供流畅的用户体验。关键在于：

1. **合理使用React优化技术**（memo、useMemo、useCallback）
2. **實施懶加載和虛擬化**減少初始渲染負擔
3. **使用Web Workers處理大量數據**避免阻塞主線程
4. **優化WebSocket和實時更新機制**提高響應速度
5. **建立完善的性能監控體系**及時發現和解決問題

持續監控和優化是保持高性能的關鍵，建議定期進行性能評估和改進。
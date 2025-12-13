---
name: task-005-real-time-data-visualization
status: open
created: 2025-12-13T09:33:34Z
updated: 2025-12-13T09:33:34Z
assignee: frontend-team
phase: 2
estimated_hours: 96
priority: high
---

# Task #5: 實時數據可視化

## 📋 任務描述
實現 CBSC Dashboard 的實時數據可視化功能，包括 Chart.js 圖表組件封裝、Plotly.js 高級圖表、實時數據更新機制和圖表交互功能，為用戶提供豐富、流暢的數據視覺化體驗。

## 🎯 具體要求

### 5.1 Chart.js 圖表組件封裝
- [ ] 折線圖組件（策略績效走勢）
- [ ] 柱狀圖組件（交易量統計）
- [ ] 餅圖組件（資產配置分布）
- [ ] 雷達圖組件（策略評分）
- [ ] 熱力圖組件（風險矩陣）
- [ ] 統一的主題適配

### 5.2 Plotly.js 高級圖表
- [ ] 3D 表面圖（波動率曲面）
- [ ] 燭台圖（K線圖）
- [ ] 散點圖矩陣（相關性分析）
- [ ] 桑基圖（資金流向）
- [ ] 地圖可視化（全球市場）
- [ ] 動畫效果支持

### 5.3 實時數據更新機制
- [ ] WebSocket 數據流集成
- [ ] 數據緩存管理
- [ ] 增量更新優化
- [ ] 數據採樣和聚合
- [ ] 性能監控和警告

### 5.4 圖表交互功能
- [ ] 縮放和平移
- [ ] 數據點懸停提示
- [ ] 圖表聯動
- [ ] 數據篩選
- [ ] 導出功能（PNG/SVG/CSV）

## ✅ 驗收標準

1. **功能驗收**
   - [ ] 所有圖表類型正確渲染
   - [ ] 實時數據更新流暢無卡頓
   - [ ] 交互功能響應及時
   - [ ] 圖表導出功能正常

2. **性能標準**
   - [ ] 初始渲染時間 < 500ms
   - [ ] 數據更新延遲 < 100ms
   - [ ] 支持 10000+ 數據點
   - [ ] 內存佔用穩定

3. **用戶體驗**
   - [ ] 圖表加載動畫流暢
   - [ ] 交互反饋及時
   - [ ] 錯誤處理優雅
   - [ ] 無障礙支持

## 🔧 技術要求

### Chart.js 組件封裝
```typescript
// components/charts/BaseChart.tsx
interface BaseChartProps {
  type: ChartType;
  data: ChartData;
  options?: ChartOptions;
  plugins?: Plugin[];
  width?: number;
  height?: number;
  className?: string;
  onDataPointClick?: (point: DataPoint) => void;
}

export const BaseChart: React.FC<BaseChartProps> = ({
  type,
  data,
  options = {},
  plugins = [],
  width,
  height = 300,
  className,
  onDataPointClick
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const chartRef = useRef<Chart | null>(null);
  const { theme } = useTheme();

  // 主題相關的默認選項
  const defaultOptions = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    animation: {
      duration: 300
    },
    interaction: {
      mode: 'nearest' as const,
      axis: 'x' as const,
      intersect: false
    },
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          color: theme.colors.text.primary,
          font: {
            size: 12
          }
        }
      },
      tooltip: {
        backgroundColor: theme.colors.background.tooltip,
        titleColor: theme.colors.text.primary,
        bodyColor: theme.colors.text.secondary,
        borderColor: theme.colors.border,
        borderWidth: 1
      }
    },
    scales: {
      x: {
        grid: {
          color: theme.colors.border
        },
        ticks: {
          color: theme.colors.text.secondary
        }
      },
      y: {
        grid: {
          color: theme.colors.border
        },
        ticks: {
          color: theme.colors.text.secondary
        }
      }
    }
  }), [theme]);

  // 創建圖表實例
  useEffect(() => {
    if (!canvasRef.current) return;

    const ctx = canvasRef.current.getContext('2d');
    if (!ctx) return;

    // 銷毀舊圖表
    if (chartRef.current) {
      chartRef.current.destroy();
    }

    // 創建新圖表
    chartRef.current = new Chart(ctx, {
      type,
      data,
      options: mergeDeep(defaultOptions, options),
      plugins: [
        ...plugins,
        {
          id: 'clickHandler',
          afterEvent: (chart, args) => {
            const event = args.event;
            if (event.type === 'click' && onDataPointClick) {
              const canvasPosition = Chart.helpers.getRelativePosition(event, chart);
              const dataX = chart.scales.x.getValueForPixel(canvasPosition.x);
              const dataY = chart.scales.y.getValueForPixel(canvasPosition.y);
              onDataPointClick({ x: dataX, y: dataY });
            }
          }
        }
      ]
    });

    return () => {
      if (chartRef.current) {
        chartRef.current.destroy();
      }
    };
  }, [type, data, defaultOptions, options, plugins, onDataPointClick]);

  return (
    <div className={`relative ${className}`} style={{ height }}>
      <canvas ref={canvasRef} />
    </div>
  );
};

// 使用示例：策略績效圖表
export const PerformanceChart: React.FC<PerformanceChartProps> = ({ data, timeRange }) => {
  const chartData = useMemo(() => ({
    labels: data.map(d => formatDateTime(d.timestamp)),
    datasets: [
      {
        label: '策略績效',
        data: data.map(d => d.value),
        borderColor: theme.colors.primary.main,
        backgroundColor: `${theme.colors.primary.main}20`,
        tension: 0.4,
        fill: true
      },
      {
        label: '基準',
        data: data.map(d => d.benchmark),
        borderColor: theme.colors.secondary.main,
        borderDash: [5, 5],
        fill: false
      }
    ]
  }), [data, theme]);

  const options = {
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          callback: (value: number) => formatPercent(value)
        }
      }
    },
    interaction: {
      intersect: false,
      mode: 'index'
    }
  };

  return <BaseChart type="line" data={chartData} options={options} />;
};
```

### Plotly.js 高級圖表組件
```typescript
// components/charts/PlotlyChart.tsx
interface PlotlyChartProps {
  data: Plotly.Data[];
  layout?: Partial<Plotly.Layout>;
  config?: Partial<Plotly.Config>;
  className?: string;
  onRelayout?: (event: Plotly.PlotRelayoutEvent) => void;
  onHover?: (event: Plotly.PlotHoverEvent) => void;
}

export const PlotlyChart: React.FC<PlotlyChartProps> = ({
  data,
  layout = {},
  config = {},
  className,
  onRelayout,
  onHover
}) => {
  const { theme } = useTheme();
  const plotRef = useRef<HTMLDivElement>(null);

  // 主題適配的默認佈局
  const defaultLayout = useMemo(() => ({
    autosize: true,
    showlegend: true,
    legend: {
      x: 1,
      y: 1,
      bgcolor: 'rgba(255,255,255,0)',
      bordercolor: theme.colors.border,
      borderwidth: 1
    },
    paper_bgcolor: theme.colors.background.default,
    plot_bgcolor: theme.colors.background.paper,
    font: {
      color: theme.colors.text.primary,
      family: theme.typography.fontFamily.sans
    },
    coloraxis: {
      colorbar: {
        tickfont: { color: theme.colors.text.secondary },
        title: { font: { color: theme.colors.text.primary } }
      }
    },
    xaxis: {
      gridcolor: theme.colors.border,
      zerolinecolor: theme.colors.border,
      tickfont: { color: theme.colors.text.secondary }
    },
    yaxis: {
      gridcolor: theme.colors.border,
      zerolinecolor: theme.colors.border,
      tickfont: { color: theme.colors.text.secondary }
    },
    margin: { l: 50, r: 50, t: 50, b: 50 }
  }), [theme]);

  // 響應式處理
  const updatePlotSize = useCallback(() => {
    if (plotRef.current) {
      Plotly.Plots.resize(plotRef.current);
    }
  }, []);

  useEffect(() => {
    window.addEventListener('resize', updatePlotSize);
    return () => window.removeEventListener('resize', updatePlotSize);
  }, [updatePlotSize]);

  // 渲染圖表
  useEffect(() => {
    if (!plotRef.current) return;

    const mergedLayout = mergeDeep(defaultLayout, layout);
    const mergedConfig = {
      responsive: true,
      displayModeBar: true,
      displaylogo: false,
      modeBarButtonsToRemove: ['pan2d', 'select2d', 'lasso2d', 'autoScale2d'],
      toImageButtonOptions: {
        format: 'png',
        filename: 'chart_export',
        height: 800,
        width: 1200,
        scale: 2
      },
      ...config
    };

    Plotly.newPlot(plotRef.current, data, mergedLayout, mergedConfig);

    // 事件綁定
    if (onRelayout) {
      plotRef.current.on('plotly_relayout', onRelayout);
    }
    if (onHover) {
      plotRef.current.on('plotly_hover', onHover);
    }

    return () => {
      if (plotRef.current) {
        Plotly.purge(plotRef.current);
      }
    };
  }, [data, defaultLayout, layout, config, onRelayout, onHover]);

  return (
    <div ref={plotRef} className={className} style={{ width: '100%', height: '100%' }} />
  );
};

// K線圖組件示例
export const CandlestickChart: React.FC<CandlestickChartProps> = ({ data }) => {
  const { theme } = useTheme();

  const plotData = useMemo(() => [{
    type: 'candlestick' as const,
    x: data.map(d => d.timestamp),
    open: data.map(d => d.open),
    high: data.map(d => d.high),
    low: data.map(d => d.low),
    close: data.map(d => d.close),
    increasing: { line: { color: theme.colors.success } },
    decreasing: { line: { color: theme.colors.error } }
  }], [data, theme]);

  const layout = {
    title: '價格走勢',
    yaxis: {
      title: '價格',
      autorange: true
    },
    xaxis: {
      title: '時間',
      rangeslider: { visible: false }
    }
  };

  return <PlotlyChart data={plotData} layout={layout} />;
};
```

### 實時數據管理
```typescript
// services/realtime/RealtimeDataManager.ts
export class RealtimeDataManager {
  private subscriptions = new Map<string, Set<RealtimeSubscription>>();
  private updateQueue = new Map<string, any[]>();
  private updateTimers = new Map<string, NodeJS.Timeout>();
  private wsService: WebSocketService;

  constructor(wsService: WebSocketService) {
    this.wsService = wsService;
    this.setupWebSocketListeners();
  }

  // 訂閱實時數據
  subscribe<T>(
    channel: string,
    callback: (data: T[]) => void,
    options: RealtimeOptions = {}
  ): () => void {
    const subscription: RealtimeSubscription = {
      id: generateId(),
      callback,
      options
    };

    if (!this.subscriptions.has(channel)) {
      this.subscriptions.set(channel, new Set());
      this.updateQueue.set(channel, []);
      this.wsService.subscribe(channel, this.handleDataUpdate.bind(this));
    }

    this.subscriptions.get(channel)!.add(subscription);

    // 返回取消訂閱函數
    return () => {
      this.unsubscribe(channel, subscription.id);
    };
  }

  // 處理 WebSocket 數據更新
  private handleDataUpdate = (channel: string, data: any) => {
    const queue = this.updateQueue.get(channel);
    if (!queue) return;

    // 添加到更新隊列
    queue.push(data);

    // 節流處理更新
    if (!this.updateTimers.has(channel)) {
      this.updateTimers.set(channel, setTimeout(() => {
        this.flushUpdates(channel);
      }, 50));
    }
  };

  // 批量處理更新
  private flushUpdates(channel: string) {
    const queue = this.updateQueue.get(channel);
    const subscriptions = this.subscriptions.get(channel);

    if (!queue || !subscriptions || queue.length === 0) return;

    // 數據聚合
    const aggregatedData = this.aggregateData(queue, subscriptions.values().next().value.options);

    // 通知所有訂閱者
    subscriptions.forEach(sub => {
      try {
        sub.callback(aggregatedData);
      } catch (error) {
        console.error('Error in subscription callback:', error);
      }
    });

    // 清理
    queue.length = 0;
    this.updateTimers.delete(channel);
  }

  // 數據聚合
  private aggregateData(data: any[], options: RealtimeOptions): any[] {
    if (!options.aggregate || data.length === 1) {
      return data;
    }

    // 實現各種聚合策略
    switch (options.aggregate.type) {
      case 'window':
        return this.windowAggregate(data, options.aggregate.windowSize);
      case 'sample':
        return this.sampleAggregate(data, options.aggregate.rate);
      case 'merge':
        return this.mergeAggregate(data, options.aggregate.key);
      default:
        return data;
    }
  }

  // 取消訂閱
  private unsubscribe(channel: string, subscriptionId: string) {
    const subscriptions = this.subscriptions.get(channel);
    if (subscriptions) {
      subscriptions.forEach(sub => {
        if (sub.id === subscriptionId) {
          subscriptions.delete(sub);
        }
      });

      // 如果沒有訂閱者了，清理資源
      if (subscriptions.size === 0) {
        this.subscriptions.delete(channel);
        this.updateQueue.delete(channel);
        if (this.updateTimers.has(channel)) {
          clearTimeout(this.updateTimers.get(channel));
          this.updateTimers.delete(channel);
        }
        this.wsService.unsubscribe(channel);
      }
    }
  }
}

// 使用 Hook
export const useRealtimeChart = <T>(
  channel: string,
  transformData: (rawData: any[]) => T[],
  options: RealtimeOptions = {}
) => {
  const [data, setData] = useState<T[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const wsService = useContext(WebSocketContext);
  const managerRef = useRef<RealtimeDataManager>();

  useEffect(() => {
    if (!wsService) return;

    managerRef.current = new RealtimeDataManager(wsService);

    const unsubscribe = managerRef.current.subscribe(
      channel,
      (newData: any[]) => {
        setData(transformData(newData));
      },
      options
    );

    wsService.on('connect', () => setIsConnected(true));
    wsService.on('disconnect', () => setIsConnected(false));

    return () => {
      unsubscribe();
    };
  }, [channel, transformData, options, wsService]);

  return { data, isConnected };
};
```

## 📊 預估工作量
| 子任務 | 預估時間 | 負責人 |
|--------|----------|--------|
| Chart.js 基礎組件 | 24小時 | 前端工程師 A |
| 高級圖表類型實現 | 16小時 | 前端工程師 A |
| Plotly.js 集成 | 24小時 | 前端工程師 B |
| 實時數據管理 | 16小時 | 前端工程師 A |
| 交互功能開發 | 16小時 | 前端工程師 B |
| **總計** | **96小時** | |

## 🔗 依賴關係
- 前置任務：Task #4 (Dashboard主界面), Task #7 (WebSocket實時通信)
- 後續任務：Task #6 (策略管理界面)

## 📝 注意事項
1. 實現圖表懶加載以提高性能
2. 處理大量數據點的渲染優化
3. 確保圖表在不同屏幕尺寸下正常顯示
4. 實現數據導出多格式支持
5. 考慮離線狀態的處理

## 🧪 測試要求
```typescript
// components/charts/__tests__/PerformanceChart.test.tsx
describe('PerformanceChart', () => {
  const mockData = [
    { timestamp: '2024-01-01', value: 100, benchmark: 100 },
    { timestamp: '2024-01-02', value: 105, benchmark: 102 }
  ];

  test('renders chart with data', () => {
    render(<PerformanceChart data={mockData} timeRange="1D" />);

    expect(screen.getByRole('img')).toBeInTheDocument();
    expect(screen.getByText('策略績效')).toBeInTheDocument();
  });

  test('handles data point clicks', () => {
    const handleClick = jest.fn();
    render(
      <PerformanceChart
        data={mockData}
        onDataPointClick={handleClick}
      />
    );

    // 模擬點擊數據點
    fireEvent.click(screen.getByRole('img'), {
      clientX: 100,
      clientY: 100
    });

    expect(handleClick).toHaveBeenCalled();
  });

  test('updates on data change', async () => {
    const { rerender } = render(<PerformanceChart data={mockData} />);

    const newData = [...mockData, { timestamp: '2024-01-03', value: 110, benchmark: 105 }];
    rerender(<PerformanceChart data={newData} />);

    await waitFor(() => {
      expect(screen.getByRole('img')).toBeInTheDocument();
    });
  });
});
```

## 📚 相關文檔
- [Chart.js 文檔](https://www.chartjs.org/)
- [Plotly.js 文檔](https://plotly.com/javascript/)
- [React Chart.js 2 文檔](https://github.com/reactchartjs/react-chartjs-2)
- [React Plotly.js 文檔](https://github.com/plotly/react-plotly.js)
- [D3.js 數據可視化](https://d3js.org/)
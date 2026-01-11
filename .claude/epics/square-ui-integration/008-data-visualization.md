---
name: task-008-data-visualization-components
title: 任務008：數據可視化組件開發
status: completed
assignee: frontend-developer
priority: P1
created: 2025-12-14T03:32:09Z
updated: 2025-12-17T14:02:48Z
estimated: 4 days
tags: [chart.js, plotly.js, data-visualization, realtime-charts]
dependsOn: [task-005-state-management-architecture, task-006-api-integration-layer]
blocks: []
---

## 📋 任務描述

集成Chart.js和Plotly.js，實現金融數據可視化組件，包括走勢圖、K線圖、資產配置圖等，開發實時數據更新機制，為策略管理系統提供豐富的數據展示能力。

## 🎯 具體要求

### 1. Chart.js組件開發
- [ ] 走勢圖組件（Line Chart）
- [ ] 柱狀圖組件（Bar Chart）
- [ ] 餅圖組件（Pie Chart）
- [ ] 面積圖組件（Area Chart）
- [ ] 雷達圖組件（Radar Chart）
- [ ] 圖表主題適配

### 2. Plotly.js高級圖表
- [ ] K線圖/燭台圖（Candlestick Chart）
- [ ] OHLC圖（Open-High-Low-Close）
- [ ] 交易量圖（Volume Chart）
- [ ] 散點圖（Scatter Plot）
- [ ] 3D可視化圖表
- [ ] 熱力圖（Heatmap）

### 3. 實時數據機制
- [ ] WebSocket數據訂閱
- [ ] 增量數據更新
- [ ] 數據緩存機制
- [ ] 斷線重連處理
- [ ] 數據去重和合併

### 4. 交互功能
- [ ] 圖表縮放和平移
- [ ] 數據提示框（Tooltip）
- [ ] 圖例篩選
- [ ] 數據導出功能
- [ ] 圖表快照功能
- [ ] 自定義時間範圍

### 5. 組件庫封裝
- [ ] 統一的API接口
- [ ] 響應式適配
- [ ] 性能優化
- [ ] 類型定義完整
- [ ] 文檔和示例

## 🔧 技術實施

### Chart.js封裝
```typescript
// BaseChart組件
interface BaseChartProps<T = any> {
  data: ChartData<T>;
  options?: ChartOptions<T>;
  type: ChartType;
  width?: number;
  height?: number;
  className?: string;
  onDataPointClick?: (point: DataPoint) => void;
}

// 使用示例
const TrendChart: React.FC<TrendChartProps> = ({
  data,
  timeRange,
  showVolume = false,
}) => {
  const chartData = useMemo(() => ({
    labels: data.timestamps,
    datasets: [
      {
        label: '價格',
        data: data.prices,
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.1)',
      },
      ...(showVolume ? [{
        label: '成交量',
        data: data.volumes,
        yAxisID: 'y1',
        type: 'bar' as const,
      }] : []),
    ],
  }), [data, showVolume]);
};
```

### Plotly.js封裝
```typescript
// CandlestickChart組件
interface CandlestickChartProps {
  data: OHLCData[];
  volume?: number[];
  indicators?: TechnicalIndicator[];
  onTimeRangeChange?: (range: [Date, Date]) => void;
}

const CandlestickChart: React.FC<CandlestickChartProps> = ({
  data,
  volume,
  indicators,
}) => {
  const traces = useMemo(() => [
    {
      type: 'candlestick',
      x: data.map(d => d.timestamp),
      open: data.map(d => d.open),
      high: data.map(d => d.high),
      low: data.map(d => d.low),
      close: data.map(d => d.close),
      name: '價格',
    },
    ...(volume ? [{
      type: 'bar' as const,
      x: data.map(d => d.timestamp),
      y: volume,
      name: '成交量',
      yaxis: 'y2',
    }] : []),
  ], [data, volume]);
};
```

### 實時數據管理
```typescript
// useRealtimeChart hook
const useRealtimeChart = (symbol: string, chartType: string) => {
  const [data, setData] = useState<ChartData>([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:3003/realtime/${symbol}`);

    ws.onmessage = (event) => {
      const newData = JSON.parse(event.data);
      setData(prev => updateChartData(prev, newData));
    };

    return () => ws.close();
  }, [symbol]);

  return { data, isConnected };
};
```

## 📁 文件結構

```
src/
├── components/
│   └── charts/
│       ├── base/
│       │   ├── BaseChart.tsx      # Chart.js基礎組件
│       │   ├── BasePlotly.tsx     # Plotly.js基礎組件
│       │   └── ChartContainer.tsx # 圖表容器
│       ├── chartjs/
│       │   ├── LineChart.tsx      # 走勢圖
│       │   ├── BarChart.tsx       # 柱狀圖
│       │   ├── PieChart.tsx       # 餅圖
│       │   └── RadarChart.tsx     # 雷達圖
│       ├── plotly/
│       │   ├── CandlestickChart.tsx # K線圖
│       │   ├── OHLCChart.tsx      # OHLC圖
│       │   ├── VolumeChart.tsx    # 成交量圖
│       │   ├── ScatterPlot.tsx    # 散點圖
│       │   └── Heatmap.tsx        # 熱力圖
│       ├── composite/
│       │   ├── TradingView.tsx    # 綜合交易視圖
│       │   ├── PortfolioChart.tsx # 投資組合圖
│       │   └── PerformanceChart.tsx # 績效圖表
│       └── utils/
│           ├── chartThemes.ts     # 圖表主題
│           ├── formatters.ts      # 數據格式化
│           └── indicators.ts      # 技術指標
├── hooks/
│   ├── useRealtimeChart.ts        # 實時圖表hook
│   ├── useChartResize.ts          # 響應式調整hook
│   └── useChartExport.ts          # 圖表導出hook
└── types/
    ├── chart.ts                   # 圖表類型定義
    └── market.ts                  # 市場數據類型
```

## 🎨 圖表主題設計

### Square-UI主題集成
```typescript
// chartThemes.ts
export const squareTheme = {
  backgroundColor: 'transparent',
  borderColor: '#e8e8e8',
  gridColor: '#f0f0f0',
  textColor: '#262626',
  colors: [
    '#1890ff', '#52c41a', '#faad14', '#f5222d',
    '#722ed1', '#13c2c2', '#eb2f96', '#fa8c16',
  ],
};

// 暗色主題
export const darkTheme = {
  backgroundColor: '#141414',
  borderColor: '#434343',
  gridColor: '#303030',
  textColor: '#ffffff',
  colors: [
    '#177ddc', '#49aa19', '#d89614', '#dc4446',
    '#642ab5', '#39a9c9', '#d32029', '#cf1322',
  ],
};
```

## 🔗 與現有系統集成

### CBSC數據源
- 對接實時行情接口
- 使用歷史數據API
- 集成策略執行數據
- 連接風控指標系統

### Square-UI組件庫
- 使用Square-UI的顏色系統
- 遵循Square-UI的設計規範
- 集成Square-UI的圖標

## ✅ 驗收標準

1. **功能完整性**
   - 所有圖表類型正常渲染
   - 實時數據更新流暢
   - 交互功能響應及時

2. **性能指標**
   - 1000數據點渲染 < 100ms
   - 實時更新延遲 < 200ms
   - 內存使用穩定

3. **用戶體驗**
   - 圖表加載動畫流暢
   - 縮放操作流暢無卡頓
   - 數據提示信息準確

4. **兼容性**
   - 支持現代瀏覽器（Chrome、Firefox、Safari、Edge）
   - 響應式設計適配
   - 觸摸設備支持

## 🧪 測試計劃

### 單元測試
- 圖表渲染測試
- 數據更新測試
- 事件處理測試
- 工具函數測試

### 集成測試
- WebSocket數據流測試
- 大數據量渲染測試
- 多圖表並發測試
- 主題切換測試

### 視覺回歸測試
- 圖表截圖對比
- 不同分辨率適配
- 主題變化測試
- 交互狀態測試

## 📝 注意事項

1. **性能優化**
   - 數據采樣和聚合
   - Canvas渲染優化
   - 防抖和節流處理
   - 內存清理機制

2. **可訪問性**
   - 鍵盤導航支持
   - 屏幕閱讀器兼容
   - 高對比度主題
   - 色盲友好配色

3. **國際化**
   - 日期時間格式本地化
   - 數字格式本地化
   - 貨幣符號支持
   - 時區處理

## 🚀 後續任務

完成後，可進行：
- 高級技術指標集成
- 圖表導出功能增強
- 自定義圖表編輯器
- 移動端手勢操作優化

---

**創建人**: Claude Code Assistant
**最後更新**: 2025-12-14T03:32:09Z
---
## Completion
This task has been completed on 2025-12-17T14:02:48Z

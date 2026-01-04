# 設計規範文檔

## 概述

本文檔提供將非價格數據策略（經濟數據、基本面數據）整合到 CBS-C 量化交易系統前端的詳細技術設計。設計遵循現有系統架構，確保與價格數據策略的無縫集成。

## 架構設計

### 1. 整體架構

```
Frontend Application (React 18 + TypeScript)
├── Pages
│   ├── EconomicDataDashboard (新建)
│   ├── NonPriceStrategyManagement (新建)
│   ├── MixedStrategyVisualization (新建)
│   └── EconomicBacktestReports (新建)
├── Components
│   ├── EconomicIndicators (已存在)
│   ├── EconomicDataCharts (新建)
│   ├── MixedStrategyViewer (新建)
│   ├── StrategyWizard (新建)
│   ├── EconomicAlerts (新建)
│   └── DataExport (新建)
├── Hooks
│   ├── useEconomicData (新建)
│   ├── useEconomicStrategy (新建)
│   ├── useWebSocketEconomic (新建)
│   └── useEconomicAlerts (新建)
├── Store/Redux
│   ├── economicDataSlice (新建)
│   ├── economicStrategySlice (新建)
│   ├── economicAlertsSlice (新建)
│   └── websocketSlice (擴展)
└── Services
    ├── economicDataApi (新建)
    ├── economicStrategyApi (新建)
    └── economicWebSocket (新建)
```

### 2. 混合數據可視化架構

```
Mixed Data Visualization Layer
├── Chart Components (擴展)
│   ├── DualAxisChart (新建) - 價格與經濟數據雙軸圖
│   ├── CorrelationHeatmap (新建) - 相關性熱力圖
│   ├── SignalOverlayChart (新建) - 信號疊加圖
│   └── MultiTimeframeChart (新建) - 多時間框架圖表
├── Data Processing Layer (新建)
│   ├── EconomicDataProcessor (新建)
│   ├── PriceDataNormalizer (擴展)
│   ├── SignalGenerator (新建)
│   └── CorrelationAnalyzer (新建)
└── Visualization Engine (擴展)
    ├── ChartRenderer (擴展)
    ├── InteractionHandler (新建)
    └── AnimationController (擴展)
```

## 組件結構設計

### 1. 經濟數據儀表板組件

```typescript
// EconomicDataDashboard.tsx
interface EconomicDataDashboardProps {
  selectedIndicators?: string[];
  timeRange?: TimeRange;
  viewMode?: 'overview' | 'detail' | 'comparison';
}

// 主要子組件
interface IndicatorCardProps {
  indicator: EconomicIndicator;
  historicalData: HistoricalDataPoint[];
  alerts?: Alert[];
}

interface IndicatorChartProps {
  indicatorId: string;
  chartType: 'line' | 'area' | 'bar' | 'scatter' | 'heatmap';
  timeRange: TimeRange;
  showSignals?: boolean;
}

interface EconomicSummaryProps {
  indicators: EconomicIndicator[];
  signals: TradingSignal[];
  marketStatus: MarketStatus;
}
```

### 2. 非價格策略管理組件

```typescript
// NonPriceStrategyManager.tsx
interface StrategyManagerProps {
  strategyTypes: EconomicStrategyType[];
  defaultParameters?: Record<string, any>;
}

// 主要子組件
interface StrategyWizardProps {
  steps: WizardStep[];
  onStrategyCreate: (strategy: EconomicStrategy) => void;
  onSaveDraft: (draft: StrategyDraft) => void;
}

interface StrategyConfigProps {
  strategy: EconomicStrategy;
  parameters: StrategyParameters;
  onParameterChange: (params: StrategyParameters) => void;
  previewMode?: boolean;
}

interface EconomicSignalDetectorProps {
  indicators: EconomicIndicator[];
  thresholdSettings: ThresholdSettings;
  onSignalDetected: (signal: EconomicSignal) => void;
}
```

### 3. 混合策略可視化組件

```typescript
// MixedStrategyViewer.tsx
interface MixedStrategyViewerProps {
  priceData: PriceData[];
  economicData: EconomicDataPoint[];
  signals: TradingSignal[];
  correlationData?: CorrelationData[];
}

// 主要子組件
interface DualAxisChartProps {
  primaryData: PriceData[];
  secondaryData: EconomicDataPoint[];
  signals?: TradingSignal[];
  timeRange: TimeRange;
}

interface CorrelationMatrixProps {
  indicators: EconomicIndicator[];
  assets: Asset[];
  correlationData: CorrelationData[];
}

interface StrategyPerformanceProps {
  performanceData: PerformanceData;
  attributionData: AttributionData[];
  timeRange: TimeRange;
}
```

## 狀態管理設計

### 1. Redux Store 擴展

```typescript
// economicDataSlice.ts
interface EconomicDataState {
  indicators: Record<string, EconomicIndicator>;
  timeSeriesData: Record<string, EconomicDataPoint[]>;
  loading: boolean;
  error: string | null;
  lastUpdated: string;
  subscriptions: string[];
}

// economicStrategySlice.ts
interface EconomicStrategyState {
  strategies: EconomicStrategy[];
  activeStrategies: string[];
  performance: Record<string, StrategyPerformance>;
  configurations: Record<string, StrategyConfig>;
  drafts: StrategyDraft[];
}

// economicAlertsSlice.ts
interface EconomicAlertsState {
  alerts: EconomicAlert[];
  alertRules: AlertRule[];
  notifications: Notification[];
  alertHistory: AlertHistory[];
}
```

### 2. 實時數據流設計

```typescript
// websocketSlice.ts (擴展)
interface WebSocketState {
  connections: {
    economicData: boolean;
    priceData: boolean;
    strategySignals: boolean;
    alerts: boolean;
  };
  subscriptions: {
    economicIndicators: string[];
    strategyIds: string[];
    alertRules: string[];
  };
  buffers: {
    economicData: EconomicDataPoint[];
    signals: TradingSignal[];
  };
}
```

### 3. 緩存策略

```typescript
// 使用 RTK Query 的緩存配置
export const economicDataApi = createApi({
  reducerPath: 'economicDataApi',
  baseQuery: fetchBaseQuery({
    baseUrl: '/api/v2/economic/',
    prepareHeaders: (headers, { getState }) => {
      // 認證標頭
    },
  }),
  tagTypes: ['EconomicIndicator', 'EconomicData', 'EconomicStrategy'],
  endpoints: (builder) => ({
    // 緩存 5 分鐘的指標數據
    getIndicators: builder.query<EconomicIndicator[], void>({
      query: () => 'indicators',
      providesTags: ['EconomicIndicator'],
      keepUnusedDataFor: 300,
    }),
    // 緩存 1 分鐘的時間序列數據
    getTimeSeries: builder.query<EconomicDataPoint[], {
      indicatorId: string;
      timeRange: TimeRange;
    }>({
      query: ({ indicatorId, timeRange }) => ({
        url: `indicators/${indicatorId}/data`,
        params: { timeRange },
      }),
      providesTags: (result, error, { indicatorId }) => [
        { type: 'EconomicData', id: indicatorId },
      ],
      keepUnusedDataFor: 60,
    }),
  }),
});
```

## API 集成模式

### 1. 經濟數據 API 設計

```typescript
// services/economicDataApi.ts
export interface EconomicDataApi {
  // 指標管理
  getIndicators(): Promise<EconomicIndicator[]>;
  getIndicator(id: string): Promise<EconomicIndicator>;
  updateIndicator(id: string, data: Partial<EconomicIndicator>): Promise<EconomicIndicator>;

  // 時間序列數據
  getTimeSeries(indicatorId: string, options: TimeSeriesOptions): Promise<EconomicDataPoint[]>;
  getRealTimeData(indicatorIds: string[]): Promise<RealTimeData[]>;

  // 數據導出
  exportData(options: ExportOptions): Promise<Blob>;

  // 相關性分析
  getCorrelationData(indicators: string[], assets: string[]): Promise<CorrelationData[]>;
}

// 響應格式標準
interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  timestamp: string;
  pagination?: {
    page: number;
    pageSize: number;
    total: number;
  };
}
```

### 2. WebSocket 集成

```typescript
// services/economicWebSocket.ts
export class EconomicWebSocket {
  private ws: WebSocket;
  private subscriptions: Map<string, Set<SubscriptionHandler>>;

  // 訂閱實時經濟數據
  subscribeToIndicators(indicatorIds: string[], handler: SubscriptionHandler): void;

  // 訂閱策略信號
  subscribeToStrategySignals(strategyIds: string[], handler: SubscriptionHandler): void;

  // 訂閱警報
  subscribeToAlerts(alertRuleIds: string[], handler: SubscriptionHandler): void;
}

// WebSocket 消息格式
interface WebSocketMessage {
  type: 'economic_data' | 'strategy_signal' | 'alert' | 'error';
  data: any;
  timestamp: string;
  id: string;
}
```

### 3. 數據轉換層

```typescript
// utils/dataTransformers.ts
export class EconomicDataTransformer {
  // 將後端數據轉換為前端格式
  transformIndicatorData(rawData: any): EconomicIndicator;

  // 標準化時間序列數據
  normalizeTimeSeries(data: any[]): EconomicDataPoint[];

  // 聚合數據（用於不同時間框架）
  aggregateData(data: EconomicDataPoint[], interval: string): EconomicDataPoint[];

  // 計算衍生指標
  calculateDerivedIndicators(indicators: EconomicIndicator[]): DerivedIndicator[];
}
```

## 實時數據流架構

### 1. 數據流設計

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Backend   │────▶│  WebSocket   │────▶│   Frontend  │
│   Server    │     │   Gateway    │     │   Client    │
└─────────────┘     └──────────────┘     └─────────────┘
                            │                      │
                            ▼                      ▼
                     ┌─────────────┐     ┌─────────────┐
                     │   Message   │     │    Redux    │
                     │   Buffer    │     │    Store    │
                     └─────────────┘     └─────────────┘
                            │                      │
                            ▼                      ▼
                     ┌─────────────┐     ┌─────────────┐
                     │   Update    │     │ Components  │
                     │   Queue     │     │  Re-render  │
                     └─────────────┘     └─────────────┘
```

### 2. 實時更新機制

```typescript
// hooks/useRealtimeEconomicData.ts
export function useRealtimeEconomicData(indicatorIds: string[]) {
  const dispatch = useDispatch();
  const { subscribe, unsubscribe } = useWebSocket();

  useEffect(() => {
    // 訂閱實時數據
    const handlers = indicatorIds.map(id => ({
      channel: `economic_data:${id}`,
      handler: (data: EconomicDataPoint) => {
        dispatch(updateEconomicData({ id, data }));
      },
    }));

    subscribe(handlers);

    return () => unsubscribe(handlers);
  }, [indicatorIds, dispatch, subscribe, unsubscribe]);
}

// 批量更新機制
const batchUpdate = createAsyncThunk(
  'economicData/batchUpdate',
  async (updates: Array<{ id: string; data: EconomicDataPoint }>) => {
    // 批量處理更新以減少渲染次數
    return updates;
  }
);
```

### 3. 離線緩存策略

```typescript
// services/economicDataCache.ts
export class EconomicDataCache {
  private cache: Map<string, CacheEntry>;
  private readonly CACHE_DURATION = 5 * 60 * 1000; // 5 分鐘

  async get(key: string): Promise<any | null> {
    const entry = this.cache.get(key);
    if (entry && Date.now() - entry.timestamp < this.CACHE_DURATION) {
      return entry.data;
    }
    return null;
  }

  set(key: string, data: any): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
    });
  }

  // 預加載常用數據
  async preloadCommonData(): Promise<void> {
    // 緩存常用指標的最新數據
  }
}
```

## 響應式設計考量

### 1. 移動端優化策略

```typescript
// 使用自定義 hook 響應式斷點
export function useResponsiveBreakpoint() {
  const [breakpoint, setBreakpoint] = useState<'mobile' | 'tablet' | 'desktop'>('desktop');

  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth;
      if (width < 768) setBreakpoint('mobile');
      else if (width < 1024) setBreakpoint('tablet');
      else setBreakpoint('desktop');
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return breakpoint;
}

// 響應式組件示例
const ResponsiveEconomicChart: React.FC<EconomicChartProps> = ({ data }) => {
  const breakpoint = useResponsiveBreakpoint();

  if (breakpoint === 'mobile') {
    // 移動端：簡化圖表，只顯示關鍵信息
    return <MobileEconomicSummary data={data} />;
  }

  if (breakpoint === 'tablet') {
    // 平板：中等詳細程度
    return <TabletEconomicChart data={data} />;
  }

  // 桌面：完整功能
  return <FullEconomicChart data={data} />;
};
```

### 2. 圖表響應式設計

```typescript
// 自適應圖表配置
export const getResponsiveChartConfig = (breakpoint: string) => {
  const baseConfig = {
    responsive: true,
    maintainAspectRatio: false,
  };

  switch (breakpoint) {
    case 'mobile':
      return {
        ...baseConfig,
        height: 200,
        plugins: {
          legend: { display: false },
          tooltip: { enabled: true },
        },
        scales: {
          x: { ticks: { maxTicksLimit: 5 } },
          y: { ticks: { maxTicksLimit: 4 } },
        },
      };

    case 'tablet':
      return {
        ...baseConfig,
        height: 300,
        plugins: {
          legend: { display: true, position: 'bottom' },
          tooltip: { enabled: true },
        },
        scales: {
          x: { ticks: { maxTicksLimit: 8 } },
          y: { ticks: { maxTicksLimit: 6 } },
        },
      };

    default:
      return {
        ...baseConfig,
        height: 400,
        plugins: {
          legend: { display: true, position: 'top' },
          tooltip: { enabled: true, intersect: false },
        },
      };
  }
};
```

### 3. 性能優化策略

```typescript
// 圖表虛擬化 - 處理大量數據點
export function useVirtualizedChart(data: DataPoint[], maxPoints: number = 1000) {
  return useMemo(() => {
    if (data.length <= maxPoints) return data;

    // 均勻採樣以減少數據點
    const step = Math.ceil(data.length / maxPoints);
    return data.filter((_, index) => index % step === 0);
  }, [data, maxPoints]);
}

// 圖表懶加載
const LazyEconomicChart = lazy(() => import('./EconomicChart'));

// 在組件中使用
<Suspense fallback={<Loading />}>
  <LazyEconomicChart data={data} />
</Suspense>
```

## 組件層級圖

```
App
└── EconomicDataDashboard
    ├── EconomicSummary
    │   ├── IndicatorCard (Multiple)
    │   ├── MarketStatus
    │   └── QuickStats
    ├── EconomicCharts
    │   ├── IndicatorChart
    │   │   ├── DualAxisChart
    │   │   ├── CorrelationHeatmap
    │   │   └── TimeSeriesChart
    │   └── ChartControls
    │       ├── TimeRangeSelector
    │       ├── IndicatorSelector
    │       └── ChartTypeSelector
    ├── EconomicAlerts
    │   ├── AlertList
    │   ├── AlertDetails
    │   └── AlertSettings
    └── DataExport
        ├── ExportModal
        ├── ExportOptions
        └── ExportPreview

NonPriceStrategyManager
├── StrategyList
│   ├── StrategyCard (Multiple)
│   └── StrategyFilters
├── StrategyWizard
│   ├── StepIndicator
│   ├── StrategyTypeSelection
│   ├── ParameterConfiguration
│   ├── BacktestSettings
│   └── ReviewAndSubmit
├── StrategyEditor
│   ├── ParameterForm
│   ├── SignalRules
│   ├── RiskSettings
│   └── PreviewPanel
└── StrategyMonitoring
    ├── RealTimeSignals
    ├── PerformanceMetrics
    └── AlertConfiguration

MixedStrategyViewer
├── PriceChart
│   ├── CandlestickChart
│   ├── VolumeChart
│   └── TechnicalIndicators
├── EconomicOverlay
│   ├── IndicatorOverlay
│   ├── SignalMarkers
│   └── CorrelationIndicators
├── StrategyControls
│   ├── TimeFrameSelector
│   ├── StrategyToggler
│   └── ViewModeSelector
└── AnalysisPanel
    ├── AttributionAnalysis
    ├── PerformanceComparison
    └── SignalHistory
```

## 數據流設計

### 1. 經濟數據流

```
Economic Data Sources
├── API Endpoints
│   ├── /api/v2/economic/indicators
│   ├── /api/v2/economic/data/{indicatorId}
│   └── /api/v2/economic/correlations
├── WebSocket Streams
│   ├── ws://localhost:3004/ws/economic-data
│   ├── ws://localhost:3004/ws/economic-signals
│   └── ws://localhost:3004/ws/economic-alerts
└── Cache Layer
    ├── Redis Cache (Server)
    ├── IndexedDB (Browser)
    └── Memory Cache (Component)

Data Processing Pipeline
├── Data Validation
│   ├── Schema Validation
│   ├── Range Checks
│   └── Consistency Checks
├── Data Transformation
│   ├── Normalization
│   ├── Aggregation
│   └── Derivative Calculation
└── Data Distribution
    ├── Redux Store Update
    ├── Component Propagation
    └── WebSocket Broadcast
```

### 2. 策略信號流

```
Strategy Engine
├── Economic Data Input
│   ├── Real-time Feed
│   ├── Historical Data
│   └── Derived Indicators
├── Signal Generation
│   ├── Threshold Crossing
│   ├── Pattern Recognition
│   └── Correlation Events
├── Signal Processing
│   ├── Signal Filtering
│   ├── Priority Ranking
│   └── Risk Assessment
└── Output Distribution
    ├── Trading Signals
    ├── Alert Notifications
    └── Dashboard Updates
```

### 3. 狀態同步流程

```
State Synchronization
├── Initial Load
│   ├── Fetch Configuration
│   ├── Load Historical Data
│   └── Initialize WebSocket
├── Real-time Updates
│   ├── Receive WebSocket Message
│   ├── Update Redux Store
│   └── Trigger Component Re-render
├── Conflict Resolution
│   ├── Optimistic Updates
│   ├── Rollback on Error
│   └── Server Reconciliation
└── Offline Handling
    ├── Cache Critical Data
    ├── Queue Actions
    └── Sync on Reconnect
```

## 與現有系統的集成點

### 1. 與策略管理系統集成

```typescript
// 擴展現有 StrategyType 枚舉
export enum StrategyType {
  // ... 現有類型
  ECONOMIC_INDICATOR = 'economic_indicator',
  FUNDAMENTAL_DATA = 'fundamental_data',
  MIXED_STRATEGY = 'mixed_strategy',
}

// 擴展策略接口
export interface Strategy {
  // ... 現有屬性
  economicIndicators?: string[];
  economicParameters?: EconomicParameters;
  correlationWeights?: Record<string, number>;
}

// 集成點：策略執行引擎
export class StrategyExecutionEngine {
  async executeMixedStrategy(strategy: MixedStrategy): Promise<ExecutionResult> {
    // 獲取價格數據
    const priceData = await this.getPriceData(strategy.symbols);

    // 獲取經濟數據
    const economicData = await this.getEconomicData(strategy.economicIndicators);

    // 生成混合信號
    const signals = this.generateMixedSignals(priceData, economicData, strategy.parameters);

    // 執行交易
    return this.executeTrades(signals);
  }
}
```

### 2. 與監控系統集成

```typescript
// 擴展現有監控組件
export const EnhancedStrategyMonitor: React.FC<{ strategyId: string }> = ({ strategyId }) => {
  const strategy = useSelector(selectStrategy(strategyId));
  const economicData = useSelector(selectEconomicDataForStrategy(strategyId));

  return (
    <div>
      {/* 現有監控組件 */}
      <StrategyPerformanceMonitor strategyId={strategyId} />

      {/* 新增經濟數據監控 */}
      {strategy.strategy_type === StrategyType.ECONOMIC_INDICATOR && (
        <EconomicDataMonitor
          indicators={strategy.economicIndicators}
          thresholds={strategy.economicParameters.thresholds}
        />
      )}

      {/* 混合策略監控 */}
      {strategy.strategy_type === StrategyType.MIXED_STRATEGY && (
        <MixedStrategyMonitor
          strategyId={strategyId}
          economicData={economicData}
        />
      )}
    </div>
  );
};
```

### 3. 與回測系統集成

```typescript
// 擴展回測請求
export interface BacktestRequest {
  // ... 現有屬性
  economicData?: EconomicDataConfig;
  correlationAnalysis?: boolean;
  attributionAnalysis?: boolean;
}

// 回測結果擴展
export interface BacktestResult {
  // ... 現有屬性
  economicMetrics?: EconomicMetrics;
  attribution?: AttributionResult;
  correlation?: CorrelationAnalysis;
}

// 集成點：回測服務
export const enhancedBacktestApi = createApi({
  // ... 現有配置
  endpoints: (builder) => ({
    runEconomicBacktest: builder.mutation<BacktestResult, EconomicBacktestRequest>({
      query: (request) => ({
        url: '/backtest/economic',
        method: 'POST',
        body: request,
      }),
    }),
  }),
});
```

## 安全與性能考量

### 1. 數據安全

```typescript
// 敏感數據加密
export class SecureDataHandler {
  private encryptionKey: string;

  encryptSensitiveData(data: any): string {
    // 使用 AES-256 加密敏感數據
  }

  decryptSensitiveData(encryptedData: string): any {
    // 解密數據
  }

  sanitizeDataForExport(data: any): any {
    // 移除或脫敏敏感信息
  }
}

// 權限控制
export const economicDataPermissions = {
  viewIndicators: 'economic:indicators:view',
  exportData: 'economic:data:export',
  createStrategies: 'economic:strategies:create',
  manageAlerts: 'economic:alerts:manage',
};
```

### 2. 性能優化

```typescript
// 數據懶加載
export function useLazyEconomicData(indicatorIds: string[]) {
  const [loadedData, setLoadedData] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState<Set<string>>(new Set());

  const loadIndicator = useCallback(async (id: string) => {
    if (loadedData[id] || loading.has(id)) return;

    setLoading(prev => new Set([...prev, id]));
    try {
      const data = await economicDataApi.getTimeSeries(id);
      setLoadedData(prev => ({ ...prev, [id]: data }));
    } finally {
      setLoading(prev => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }
  }, [loadedData, loading]);

  return { loadedData, loading, loadIndicator };
}

// 數據壓縮
export const compressDataForTransport = (data: EconomicDataPoint[]): string => {
  // 使用 gzip 壓縮大型數據集
  return compress(JSON.stringify(data));
};

// Web Workers 處理大型計算
export class EconomicDataWorker {
  private worker: Worker;

  constructor() {
    this.worker = new Worker('/workers/economicData.worker.js');
  }

  async calculateCorrelations(data: CorrelationRequest): Promise<CorrelationResult> {
    return new Promise((resolve, reject) => {
      this.worker.postMessage({ type: 'calculate_correlations', data });
      this.worker.onmessage = (e) => {
        if (e.data.type === 'correlation_result') {
          resolve(e.data.result);
        } else if (e.data.type === 'error') {
          reject(e.data.error);
        }
      };
    });
  }
}
```

## 總結

本設計規範提供了將非價格數據策略整合到 CBS-C 前端系統的全面技術方案。主要特點包括：

1. **模組化架構**：清晰的組件分層，易於維護和擴展
2. **實時數據流**：WebSocket 支持的實時更新機制
3. **響應式設計**：適配各種設備尺寸的優化方案
4. **性能優化**：懶加載、虛擬化、緩存策略
5. **無縫集成**：與現有系統的平滑整合

該設計遵循了現有系統的模式和最佳實踐，確保新功能能夠順利集成並提供良好的用戶體驗。
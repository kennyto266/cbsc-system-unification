# Performance Analysis Tab Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a comprehensive performance analysis tab with return attribution chart, risk radar chart, correlation heatmap, and stress test table using Plotly.js.

**Architecture:** Grid-based layout with 4 visualization modules. Backend API provides computed analytics data; frontend handles Plotly.js rendering and user interactions.

**Tech Stack:** React 18, TypeScript, Redux Toolkit, Plotly.js, Ant Design, Framer Motion

---

## Task 1: Create PerformanceAnalytics Redux Slice

**Files:**
- Create: `frontend/src/store/slices/performanceAnalyticsSlice.ts`
- Modify: `frontend/src/store/index.ts`

**Step 1: Write the Redux slice**

```typescript
/**
 * Performance Analytics Slice
 * Manages performance analysis data for charts
 */

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';

// Time range types
export type TimeRangePreset = '1w' | '1m' | '3m' | '1y';
export type TimeRange = TimeRangePreset | { start: string; end: string };

// Return attribution data
export interface AttributionData {
  total: number;
  breakdown: Array<{
    indicator: string;
    contribution: number;
    percentage: number;
  }>;
}

// Risk exposure data
export interface RiskData {
  systematic: number;
  interestRate: number;
  liquidity: number;
  economicGrowth: number;
  fx: number;
}

// Correlation matrix data
export interface CorrelationData {
  matrix: number[][];
  strategies: string[];
}

// Stress test result
export interface StressTestResult {
  scenario: string;
  expectedReturn: number;
  maxDrawdown: number;
  sharpeRatio: number;
}

// Performance analytics state
interface PerformanceAnalyticsState {
  // Selection
  selectedTimeRange: TimeRange;
  selectedStrategies: string[];

  // Data
  returnAttribution: AttributionData | null;
  riskExposure: RiskData | null;
  correlations: CorrelationData | null;
  stressTest: StressTestResult[] | null;

  // UI State
  isLoading: boolean;
  error: string | null;
  lastUpdate: Date | null;
}

const initialState: PerformanceAnalyticsState = {
  selectedTimeRange: '1m',
  selectedStrategies: [],
  returnAttribution: null,
  riskExposure: null,
  correlations: null,
  stressTest: null,
  isLoading: false,
  error: null,
  lastUpdate: null,
};

// Async thunk to fetch performance analytics
export const fetchPerformanceAnalytics = createAsyncThunk(
  'performanceAnalytics/fetch',
  async (params: { timeRange: TimeRange; strategies?: string[] }, { rejectWithValue }) => {
    try {
      // TODO: Replace with actual API call
      // const response = await apiClient.post('/api/analytics/performance', params);
      // return response.data;

      // Mock data fallback
      return {
        returnAttribution: {
          total: 15.5,
          breakdown: [
            { indicator: 'HIBOR', contribution: 5.2, percentage: 33.5 },
            { indicator: 'GDP', contribution: 3.8, percentage: 24.5 },
            { indicator: 'PMI', contribution: 2.9, percentage: 18.7 },
            { indicator: 'Visitors', contribution: 2.1, percentage: 13.5 },
            { indicator: 'Unemployment', contribution: 1.5, percentage: 9.7 },
          ],
        },
        riskExposure: {
          systematic: 0.65,
          interestRate: 0.72,
          liquidity: 0.45,
          economicGrowth: 0.58,
          fx: 0.32,
        },
        correlations: {
          matrix: [
            [1.0, 0.65, 0.42, 0.28],
            [0.65, 1.0, 0.55, 0.38],
            [0.42, 0.55, 1.0, 0.31],
            [0.28, 0.38, 0.31, 1.0],
          ],
          strategies: ['經濟動量策略', '流動性情緒策略', '宏觀平衡策略', 'HIBOR利率策略'],
        },
        stressTest: [
          { scenario: '基準', expectedReturn: 15.5, maxDrawdown: -8.2, sharpeRatio: 1.85 },
          { scenario: '利率上升200bp', expectedReturn: 8.3, maxDrawdown: -12.5, sharpeRatio: 0.92 },
          { scenario: '經濟衰退', expectedReturn: -5.2, maxDrawdown: -22.8, sharpeRatio: -0.45 },
          { scenario: '市場崩盤', expectedReturn: -18.5, maxDrawdown: -35.2, sharpeRatio: -1.25 },
        ],
      };
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

export const performanceAnalyticsSlice = createSlice({
  name: 'performanceAnalytics',
  initialState,
  reducers: {
    setTimeRange: (state, action: PayloadAction<TimeRange>) => {
      state.selectedTimeRange = action.payload;
    },
    setSelectedStrategies: (state, action: PayloadAction<string[]>) => {
      state.selectedStrategies = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchPerformanceAnalytics.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchPerformanceAnalytics.fulfilled, (state, action) => {
        state.isLoading = false;
        state.returnAttribution = action.payload.returnAttribution;
        state.riskExposure = action.payload.riskExposure;
        state.correlations = action.payload.correlations;
        state.stressTest = action.payload.stressTest;
        state.lastUpdate = new Date();
      })
      .addCase(fetchPerformanceAnalytics.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });
  },
});

export const { setTimeRange, setSelectedStrategies } = performanceAnalyticsSlice.actions;

export default performanceAnalyticsSlice.reducer;
```

**Step 2: Register slice in store**

Modify `frontend/src/store/index.ts`:

Add import at top:
```typescript
import performanceAnalyticsReducer from './slices/performanceAnalyticsSlice';
```

Add to reducer object:
```typescript
performanceAnalytics: performanceAnalyticsReducer,
```

**Step 3: Run build to verify**

Run: `cd frontend && npm run build`
Expected: Build succeeds, no TypeScript errors

**Step 4: Commit**

```bash
git add frontend/src/store/slices/performanceAnalyticsSlice.ts frontend/src/store/index.ts
git commit -m "feat: add performance analytics Redux slice with mock data"
```

---

## Task 2: Create PerformanceHeader Component

**Files:**
- Create: `frontend/src/components/Dashboard/PerformanceTab/PerformanceHeader.tsx`
- Create: `frontend/src/components/Dashboard/PerformanceTab/PerformanceHeader.css`

**Step 1: Write the component**

```typescript
/**
 * PerformanceHeader Component
 * Control bar with time range selector, strategy selector, and export
 */

import React from 'react';
import { Space, Button, Select, DatePicker } from 'antd';
import { Download, Calendar } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '../../../hooks/redux';
import { setTimeRange, fetchPerformanceAnalytics, TimeRange } from '../../../store/slices/performanceAnalyticsSlice';
import dayjs from 'dayjs';
import './PerformanceHeader.css';

const { RangePicker } = DatePicker;

export const PerformanceHeader: React.FC = () => {
  const dispatch = useAppDispatch();
  const selectedTimeRange = useAppSelector((state) => state.performanceAnalytics.selectedTimeRange);
  const isLoading = useAppSelector((state) => state.performanceAnalytics.isLoading);
  const lastUpdate = useAppSelector((state) => state.performanceAnalytics.lastUpdate);

  const isCustomRange = typeof selectedTimeRange === 'object' && 'start' in selectedTimeRange;

  const handleTimeRangeChange = (value: string) => {
    const newRange: TimeRange = value as any;
    dispatch(setTimeRange(newRange));
    dispatch(fetchPerformanceAnalytics({ timeRange: newRange }) as any);
  };

  const handleCustomRangeChange = (dates: any) => {
    if (dates && dates[0] && dates[1]) {
      const newRange: TimeRange = {
        start: dates[0].format('YYYY-MM-DD'),
        end: dates[1].format('YYYY-MM-DD'),
      };
      dispatch(setTimeRange(newRange));
      dispatch(fetchPerformanceAnalytics({ timeRange: newRange }) as any);
    }
  };

  const handleExport = () => {
    // TODO: Implement export functionality
    console.log('Exporting performance analytics...');
  };

  const formatLastUpdate = () => {
    if (!lastUpdate) return '未更新';
    const diff = Math.floor((Date.now() - lastUpdate.getTime()) / 1000 / 60);
    if (diff < 1) return '剛剛';
    if (diff < 60) return `${diff}分鐘前`;
    return lastUpdate.toLocaleTimeString('zh-HK', { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="performance-header">
      <Space size="large">
        {/* Time Range Selector */}
        <div className="performance-header-section">
          <span className="performance-header-label">時間範圍：</span>
          <Space.Compact>
            <Button
              type={!isCustomRange && selectedTimeRange === '1w' ? 'primary' : 'default'}
              size="small"
              onClick={() => handleTimeRangeChange('1w')}
            >
              1週
            </Button>
            <Button
              type={!isCustomRange && selectedTimeRange === '1m' ? 'primary' : 'default'}
              size="small"
              onClick={() => handleTimeRangeChange('1m')}
            >
              1月
            </Button>
            <Button
              type={!isCustomRange && selectedTimeRange === '3m' ? 'primary' : 'default'}
              size="small"
              onClick={() => handleTimeRangeChange('3m')}
            >
              3月
            </Button>
            <Button
              type={!isCustomRange && selectedTimeRange === '1y' ? 'primary' : 'default'}
              size="small"
              onClick={() => handleTimeRangeChange('1y')}
            >
              1年
            </Button>
          </Space.Compact>
        </div>

        {/* Custom Date Range */}
        <div className="performance-header-section">
          <RangePicker
            value={isCustomRange ? [dayjs(selectedTimeRange.start), dayjs(selectedTimeRange.end)] : null}
            onChange={handleCustomRangeChange}
            format="YYYY-MM-DD"
            size="small"
            allowClear={false}
          />
        </div>

        {/* Last Updated */}
        <div className="performance-header-meta">
          <span className="performance-header-label">更新時間：</span>
          <span>{formatLastUpdate()}</span>
        </div>

        {/* Export Button */}
        <Button
          icon={<Download size={14} />}
          size="small"
          onClick={handleExport}
          loading={isLoading}
        >
          導出報告
        </Button>
      </Space>
    </div>
  );
};

export default PerformanceHeader;
```

**Step 2: Write the CSS**

```css
/**
 * PerformanceHeader Styles
 */

.performance-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  margin-bottom: 20px;
  border-bottom: 1px solid #e5e7eb;
}

.dark .performance-header {
  border-bottom-color: #374151;
}

.performance-header-section {
  display: flex;
  align-items: center;
  gap: 8px;
}

.performance-header-label {
  font-size: 14px;
  color: #6b7280;
}

.dark .performance-header-label {
  color: #9ca3af;
}

.performance-header-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #6b7280;
}

.dark .performance-header-meta {
  color: #9ca3af;
}
```

**Step 3: Run build**

Run: `cd frontend && npm run build`
Expected: Build succeeds

**Step 4: Commit**

```bash
git add frontend/src/components/Dashboard/PerformanceTab/PerformanceHeader.tsx frontend/src/components/Dashboard/PerformanceTab/PerformanceHeader.css
git commit -m "feat: add performance header with time range selector and export"
```

---

## Task 3: Create ReturnAttribution Chart Component

**Files:**
- Create: `frontend/src/components/Dashboard/PerformanceTab/ReturnAttribution/ReturnAttributionChart.tsx`
- Create: `frontend/src/components/Dashboard/PerformanceTab/ReturnAttribution/index.ts`

**Step 1: Write the chart component**

```typescript
/**
 * ReturnAttributionChart Component
 * Stacked bar chart showing economic indicator contributions to total return
 */

import React, { useMemo } from 'react';
import { Card, Empty } from 'antd';
import Plot from 'react-plotly.js';
import { useAppSelector } from '../../../../hooks/redux';

export const ReturnAttributionChart: React.FC = () => {
  const attributionData = useAppSelector((state) => state.performanceAnalytics.returnAttribution);
  const isLoading = useAppSelector((state) => state.performanceAnalytics.isLoading);

  const plotData = useMemo(() => {
    if (!attributionData) return [];

    const indicators = attributionData.breakdown.map((d) => d.indicator);
    const contributions = attributionData.breakdown.map((d) => d.contribution);
    const colors = contributions.map((c) => (c >= 0 ? '#10b981' : '#ef4444'));

    return [
      {
        type: 'bar',
        x: indicators,
        y: contributions,
        marker: {
          color: colors,
        },
        text: contributions.map(
          (c) => `${c >= 0 ? '+' : ''}${c.toFixed(2)}%`
        ),
        textposition: 'outside',
        hoverinfo: 'x+y+text',
      },
    ];
  }, [attributionData]);

  const layout = {
    title: {
      text: '收益來源分解',
      font: { size: 16, color: '#111827' },
    },
    xaxis: {
      title: '經濟指標',
    },
    yaxis: {
      title: '貢獻 (%)',
      zeroline: true,
      gridcolor: '#e5e7eb',
    },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    margin: { l: 60, r: 30, t: 50, b: 60 },
    height: 350,
    showlegend: false,
  };

  const config = {
    responsive: true,
    displayModeBar: false,
  };

  if (!attributionData && !isLoading) {
    return (
      <Card>
        <Empty description="無數據" />
      </Card>
    );
  }

  return (
    <Card loading={isLoading} className="return-attribution-card">
      <Plot data={plotData} layout={layout} config={config} />
    </Card>
  );
};

export default ReturnAttributionChart;
```

**Step 2: Create export file**

```typescript
/**
 * ReturnAttribution Export
 */

export { ReturnAttributionChart } from './ReturnAttributionChart';
export { default as ReturnAttributionChart } from './ReturnAttributionChart';
```

**Step 3: Run build**

Run: `cd frontend && npm run build`
Expected: Build succeeds

**Step 4: Commit**

```bash
git add frontend/src/components/Dashboard/PerformanceTab/ReturnAttribution/
git commit -m "feat: add return attribution stacked bar chart with Plotly"
```

---

## Task 4: Create RiskRadarChart Component

**Files:**
- Create: `frontend/src/components/Dashboard/PerformanceTab/RiskAnalysis/RiskRadarChart.tsx`
- Create: `frontend/src/components/Dashboard/PerformanceTab/RiskAnalysis/index.ts`

**Step 1: Write the radar chart component**

```typescript
/**
 * RiskRadarChart Component
 * Radar chart showing 5-dimension risk exposure
 */

import React, { useMemo } from 'react';
import { Card, Empty } from 'antd';
import Plot from 'react-plotly.js';
import { useAppSelector } from '../../../../hooks/redux';

export const RiskRadarChart: React.FC = () => {
  const riskData = useAppSelector((state) => state.performanceAnalytics.riskExposure);
  const isLoading = useAppSelector((state) => state.performanceAnalytics.isLoading);

  const plotData = useMemo(() => {
    if (!riskData) return [];

    const dimensions = [
      '系統性風險',
      '利率風險',
      '流動性風險',
      '經濟增長風險',
      '匯率風險',
    ];

    const values = [
      riskData.systematic,
      riskData.interestRate,
      riskData.liquidity,
      riskData.economicGrowth,
      riskData.fx,
    ];

    return [
      {
        type: 'scatterpolar',
        r: values,
        theta: dimensions,
        fill: 'toself',
        name: '風險暴露',
        marker: {
          color: 'rgb(59, 130, 246)',
        },
        line: {
          color: 'rgb(59, 130, 246)',
        },
      },
    ];
  }, [riskData]);

  const layout = {
    title: {
      text: '風險歸因分析',
      font: { size: 16, color: '#111827' },
    },
    polar: {
      radialaxis: {
        visible: true,
        range: [0, 1],
        tickmode: 'linear',
        tick0: 0,
        dtick: 0.2,
      },
    },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    margin: { l: 60, r: 60, t: 50, b: 60 },
    height: 400,
    showlegend: false,
  };

  const config = {
    responsive: true,
    displayModeBar: false,
  };

  if (!riskData && !isLoading) {
    return (
      <Card>
        <Empty description="無數據" />
      </Card>
    );
  }

  return (
    <Card loading={isLoading} className="risk-radar-card">
      <Plot data={plotData} layout={layout} config={config} />
    </Card>
  );
};

export default RiskRadarChart;
```

**Step 2: Create export file**

```typescript
/**
 * RiskAnalysis Export
 */

export { RiskRadarChart } from './RiskRadarChart';
export { default as RiskRadarChart } from './RiskRadarChart';
```

**Step 3: Run build**

Run: `cd frontend && npm run build`
Expected: Build succeeds

**Step 4: Commit**

```bash
git add frontend/src/components/Dashboard/PerformanceTab/RiskAnalysis/
git commit -m "feat: add risk radar chart with Plotly scatterpolar"
```

---

## Task 5: Create CorrelationHeatmap Component

**Files:**
- Create: `frontend/src/components/Dashboard/PerformanceTab/CorrelationAnalysis/CorrelationHeatmap.tsx`
- Create: `frontend/src/components/Dashboard/PerformanceTab/CorrelationAnalysis/index.ts`

**Step 1: Write the heatmap component**

```typescript
/**
 * CorrelationHeatmap Component
 * Heatmap showing strategy correlation matrix
 */

import React, { useMemo } from 'react';
import { Card, Empty } from 'antd';
import Plot from 'react-plotly.js';
import { useAppSelector } from '../../../../hooks/redux';

export const CorrelationHeatmap: React.FC = () => {
  const correlationData = useAppSelector((state) => state.performanceAnalytics.correlations);
  const isLoading = useAppSelector((state) => state.performanceAnalytics.isLoading);

  const plotData = useMemo(() => {
    if (!correlationData) return [];

    return [
      {
        type: 'heatmap',
        z: correlationData.matrix,
        x: correlationData.strategies,
        y: correlationData.strategies,
        colorscale: [
          [0, '#10b981'],    // Green - low correlation
          [0.5, '#f59e0b'],  // Yellow - medium
          [1, '#ef4444'],    // Red - high correlation
        ],
        colorbar: {
          title: '相關性',
          titleside: 'right',
        },
        hovertemplate: '%{x} vs %{y}<br>相關性: %{z:.2f}<extra></extra>',
      },
    ];
  }, [correlationData]);

  const layout = {
    title: {
      text: '策略相關性矩陣',
      font: { size: 16, color: '#111827' },
    },
    xaxis: {
      side: 'bottom',
    },
    yaxis: {
      automargin: true,
    },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    margin: { l: 100, r: 30, t: 50, b: 80 },
    height: 400,
    showlegend: false,
  };

  const config = {
    responsive: true,
    displayModeBar: false,
  };

  if (!correlationData && !isLoading) {
    return (
      <Card>
        <Empty description="無數據" />
      </Card>
    );
  }

  return (
    <Card loading={isLoading} className="correlation-heatmap-card">
      <Plot data={plotData} layout={layout} config={config} />
    </Card>
  );
};

export default CorrelationHeatmap;
```

**Step 2: Create export file**

```typescript
/**
 * CorrelationAnalysis Export
 */

export { CorrelationHeatmap } from './CorrelationHeatmap';
export { default as CorrelationHeatmap } from './CorrelationHeatmap';
```

**Step 3: Run build**

Run: `cd frontend && npm run build`
Expected: Build succeeds

**Step 4: Commit**

```bash
git add frontend/src/components/Dashboard/PerformanceTab/CorrelationAnalysis/
git commit -m "feat: add correlation heatmap with Plotly"
```

---

## Task 6: Create StressTestTable Component

**Files:**
- Create: `frontend/src/components/Dashboard/PerformanceTab/StressTest/StressTestTable.tsx`
- Create: `frontend/src/components/Dashboard/PerformanceTab/StressTest/index.ts`

**Step 1: Write the table component**

```typescript
/**
 * StressTestTable Component
 * Table showing stress test results across 4 scenarios
 */

import React from 'react';
import { Table, Empty, Tag } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { useAppSelector } from '../../../../hooks/redux';

interface StressTestRecord {
  key: string;
  scenario: string;
  expectedReturn: number;
  maxDrawdown: number;
  sharpeRatio: number;
}

export const StressTestTable: React.FC = () => {
  const stressTest = useAppSelector((state) => state.performanceAnalytics.stressTest);
  const isLoading = useAppSelector((state) => state.performanceAnalytics.isLoading);

  const columns: ColumnsType<StressTestRecord> = [
    {
      title: '場景',
      dataIndex: 'scenario',
      key: 'scenario',
      width: 150,
    },
    {
      title: '預期收益',
      dataIndex: 'expectedReturn',
      key: 'expectedReturn',
      align: 'right',
      render: (value: number) => (
        <span className={`stress-value ${value >= 0 ? 'positive' : 'negative'}`}>
          {value >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
          {value >= 0 ? '+' : ''}{value.toFixed(2)}%
        </span>
      ),
    },
    {
      title: '最大回撤',
      dataIndex: 'maxDrawdown',
      key: 'maxDrawdown',
      align: 'right',
      render: (value: number) => (
        <span className="stress-value negative">
          {value.toFixed(2)}%
        </span>
      ),
    },
    {
      title: '夏普比率',
      dataIndex: 'sharpeRatio',
      key: 'sharpeRatio',
      align: 'right',
      render: (value: number) => {
        let color = 'default';
        if (value > 1) color = 'success';
        else if (value > 0) color = 'warning';
        else color = 'error';
        return <Tag color={color}>{value.toFixed(2)}</Tag>;
      },
    },
  ];

  const dataSource = React.useMemo(() => {
    if (!stressTest) return [];
    return stressTest.map((item, index) => ({
      key: index.toString(),
      ...item,
    }));
  }, [stressTest]);

  if (!stressTest && !isLoading) {
    return <Empty description="無數據" />;
  }

  return (
    <div className="stress-test-table">
      <Table
        columns={columns}
        dataSource={dataSource}
        loading={isLoading}
        pagination={false}
        size="middle"
      />
    </div>
  );
};

export default StressTestTable;
```

**Step 2: Create export file**

```typescript
/**
 * StressTest Export
 */

export { StressTestTable } from './StressTestTable';
export { default as StressTestTable } from './StressTestTable';
```

**Step 3: Run build**

Run: `cd frontend && npm run build`
Expected: Build succeeds

**Step 4: Commit**

```bash
git add frontend/src/components/Dashboard/PerformanceTab/StressTest/
git commit -m "feat: add stress test results table"
```

---

## Task 7: Create PerformanceTab Main Component

**Files:**
- Create: `frontend/src/components/Dashboard/PerformanceTab/PerformanceTab.tsx`
- Create: `frontend/src/components/Dashboard/PerformanceTab/PerformanceTab.css`
- Create: `frontend/src/components/Dashboard/PerformanceTab/index.ts`

**Step 1: Write the main component**

```typescript
/**
 * PerformanceTab Component
 * Performance analysis with charts and stress test
 */

import React, { useEffect } from 'react';
import { motion } from 'framer-motion';
import { Row, Col } from 'antd';
import { useAppDispatch } from '../../../hooks/redux';
import { fetchPerformanceAnalytics } from '../../../store/slices/performanceAnalyticsSlice';
import { PerformanceHeader } from './PerformanceHeader';
import { ReturnAttributionChart } from './ReturnAttribution';
import { RiskRadarChart } from './RiskAnalysis';
import { CorrelationHeatmap } from './CorrelationAnalysis';
import { StressTestTable } from './StressTest';
import './PerformanceTab.css';

export const PerformanceTab: React.FC = () => {
  const dispatch = useAppDispatch();

  // Load initial data
  useEffect(() => {
    dispatch(fetchPerformanceAnalytics({ timeRange: '1m' }) as any);
  }, [dispatch]);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="performance-tab"
    >
      {/* Control Header */}
      <PerformanceHeader />

      {/* Return Attribution Chart - Full Width */}
      <div className="performance-section">
        <ReturnAttributionChart />
      </div>

      {/* Risk Radar and Correlation Heatmap - Side by Side */}
      <Row gutter={[24, 24]}>
        <Col xs={24} lg={12}>
          <div className="performance-section">
            <RiskRadarChart />
          </div>
        </Col>
        <Col xs={24} lg={12}>
          <div className="performance-section">
            <CorrelationHeatmap />
          </div>
        </Col>
      </Row>

      {/* Stress Test Results - Full Width */}
      <div className="performance-section">
        <h3 className="performance-section-title">壓力測試結果</h3>
        <StressTestTable />
      </div>
    </motion.div>
  );
};

export default PerformanceTab;
```

**Step 2: Write the CSS**

```css
/**
 * PerformanceTab Styles
 */

.performance-tab {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.performance-section {
  margin-bottom: 0;
}

.performance-section-title {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}

.dark .performance-section-title {
  color: #f9fafb;
}

/* Return Attribution Card */
.return-attribution-card {
  width: 100%;
}

/* Risk Radar Card */
.risk-radar-card {
  width: 100%;
  height: 100%;
}

/* Correlation Heatmap Card */
.correlation-heatmap-card {
  width: 100%;
  height: 100%;
}

/* Stress Test Table */
.stress-test-table {
  width: 100%;
}

.stress-value {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-weight: 500;
}

.stress-value.positive {
  color: #10b981;
}

.stress-value.negative {
  color: #ef4444;
}

/* Responsive */
@media (max-width: 768px) {
  .performance-tab {
    gap: 16px;
  }
}
```

**Step 3: Create export file**

```typescript
/**
 * PerformanceTab Export
 */

export { PerformanceTab } from './PerformanceTab';
export { default as PerformanceTab } from './PerformanceTab';
```

**Step 4: Run build**

Run: `cd frontend && npm run build`
Expected: Build succeeds

**Step 5: Commit**

```bash
git add frontend/src/components/Dashboard/PerformanceTab/PerformanceTab.tsx frontend/src/components/Dashboard/PerformanceTab/PerformanceTab.css frontend/src/components/Dashboard/PerformanceTab/index.ts
git commit -m "feat: create main PerformanceTab component with all sub-components"
```

---

## Task 8: Integrate into UnifiedDashboardPage

**Files:**
- Modify: `frontend/src/pages/UnifiedDashboard/UnifiedDashboardPage.tsx`

**Step 1: Add PerformanceTab import**

Add at the top with other imports:
```typescript
import { PerformanceTab } from '../../components/Dashboard/PerformanceTab/PerformanceTab';
```

**Step 2: Add the performance tab pane**

Find the performance tab section (it should have placeholder content) and replace with:

```typescript
<TabPane
  tab={
    <span className="flex items-center gap-2">
      <TrendingUp size={18} />
      性能分析
    </span>
  }
  key="performance"
>
  <motion.div
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.3 }}
  >
    <PerformanceTab />
  </motion.div>
</TabPane>
```

**Step 3: Run build**

Run: `cd frontend && npm run build`
Expected: Build succeeds

**Step 4: Commit**

```bash
git add frontend/src/pages/UnifiedDashboard/UnifiedDashboardPage.tsx
git commit -m "feat: integrate PerformanceTab into UnifiedDashboardPage"
```

---

## Task 9: Browser Testing

**Step 1: Start dev server**

Run: `cd frontend && npm run dev`

**Step 2: Open browser**

Navigate to: `http://localhost:3000/`

**Step 3: Test PerformanceTab**

Checklist:
- [ ] Performance tab displays correctly
- [ ] Time range buttons (1w, 1m, 3m, 1y) work
- [ ] Custom date range picker works
- [ ] Return Attribution chart renders with correct colors
- [ ] Risk Radar chart shows 5 dimensions
- [ ] Correlation Heatmap displays correctly
- [ ] Stress Test table shows 4 scenarios
- [ ] Export button exists (functionality can be TODO)
- [ ] Last update timestamp displays
- [ ] No console errors

**Step 4: Test responsive design**

- Resize browser to tablet (768px)
- Resize browser to mobile (375px)
- Verify layout adapts correctly

---

## Task 10: Final Cleanup

**Step 1: Update design doc**

Add completion status to `docs/plans/2025-12-29-performance-analysis-tab.md`:

```markdown
## Completion Status

**Status:** ✅ COMPLETED (2025-12-29)

All components implemented and tested successfully.
```

**Step 2: Final commit**

```bash
git add docs/plans/2025-12-29-performance-analysis-tab.md
git commit -m "docs: update performance analysis tab with completion status"
```

**Step 3: Final build verification**

Run: `cd frontend && npm run build`
Expected: Production build succeeds

---

## Success Criteria

- [ ] All components build without errors
- [ ] Performance tab displays correctly in browser
- [ ] All 4 visualization modules render (charts + table)
- [ ] Time range switching triggers data reload
- [ ] Responsive design adapts to different screen sizes
- [ ] No console errors or warnings
- [ ] Documentation updated

---

## Notes

- **Plotly.js** is used for all charts (bar, radar, heatmap)
- **Mock data fallback** is implemented for development
- **API integration** is stubbed with TODO comments
- **Export functionality** is UI-only in this phase
- **TDD approach** can be added in optimization phase

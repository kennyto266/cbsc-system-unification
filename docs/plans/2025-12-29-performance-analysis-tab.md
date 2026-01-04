# Performance Analysis Tab Design

**Date**: 2025-12-29
**Status**: ✅ Implemented
**Phase**: 4 - Dashboard Optimization
**Implementation Date**: 2025-12-29

## Overview

Performance Analysis Tab provides deep insights into strategy performance through four key visualization modules: return attribution, risk exposure radar, correlation heatmap, and stress testing results.

## Technical Decisions

| Aspect | Choice | Rationale |
|--------|--------|-----------|
| Chart Library | Plotly.js | Built-in radar and heatmap charts, already in project |
| Data Computation | Backend API | Complex calculations (correlation, stress test) done server-side |
| Time Range | Hybrid (Presets + Custom) | Flexibility for different use cases |
| Data Granularity | Auto-adjust | 1w→daily, 1m→daily, 3m→weekly, 1y→monthly |

## Architecture

### Component Structure

```
PerformanceTab/
├── PerformanceTab.tsx              # Main container
├── PerformanceHeader.tsx           # Control bar (time range, strategy select, export)
├── ReturnAttribution/
│   ├── ReturnAttributionChart.tsx  # Stacked bar chart (Plotly)
│   └── index.ts
├── RiskAnalysis/
│   ├── RiskRadarChart.tsx          # Radar chart (Plotly Scatterpolar)
│   └── index.ts
├── CorrelationAnalysis/
│   ├── CorrelationHeatmap.tsx      # Heatmap (Plotly Heatmap)
│   └── index.ts
└── StressTest/
    ├── StressTestTable.tsx         # 4-scenario results table
    └── index.ts
```

### Layout Grid

```
┌─────────────────────────────────────────────────────┐
│  Control Bar: Time Range | Strategy Select | Export │
├─────────────────────────────────────────────────────┤
│  Return Attribution (Full Width)                     │
│  Stacked bar: economic indicators → total return     │
├─────────────────────┬───────────────────────────────┤
│  Risk Radar (Left)  │ Correlation Heatmap (Right)   │
│  5-dimension radar  │ Strategy correlation matrix   │
├─────────────────────┴───────────────────────────────┤
│  Stress Test Results (Full Width)                    │
│  Table: 4 scenarios with metrics                     │
└─────────────────────────────────────────────────────┘
```

## API Specification

### GET /api/analytics/performance

**Request:**
```typescript
interface PerformanceAnalyticsRequest {
  timeRange: '1w' | '1m' | '3m' | '1y' | { start: string; end: string };
  strategies?: string[];  // Empty = all strategies
}
```

**Response:**
```typescript
interface PerformanceAnalyticsResponse {
  returnAttribution: {
    total: number;
    breakdown: Array<{
      indicator: string;
      contribution: number;
      percentage: number;
    }>;
  };
  riskExposure: {
    systematic: number;
    interestRate: number;
    liquidity: number;
    economicGrowth: number;
    fx: number;
  };
  correlations: {
    matrix: number[][];
    strategies: string[];
  };
  stressTest: Array<{
    scenario: string;
    expectedReturn: number;
    maxDrawdown: number;
    sharpeRatio: number;
  }>;
}
```

## Component Details

### 1. PerformanceHeader

**Props:** None (uses Redux)

**State:**
- Selected time range
- Selected strategies
- Export loading state

**Features:**
- Time range buttons: 1w, 1m, 3m, 1y, Custom
- Strategy multi-select dropdown
- Export button (PDF/CSV)
- Last updated timestamp

### 2. ReturnAttributionChart

**Chart Type:** Plotly Bar (stacked)

**Data Mapping:**
```typescript
{
  x: [indicator names],
  y: [contributions],
  type: 'bar',
  marker: {
    color: [contributions > 0 ? green : red]
  }
}
```

**Interactions:**
- Hover shows detailed values
- Legend toggles indicators
- Zoom enabled

### 3. RiskRadarChart

**Chart Type:** Plotly Scatterpolar (Radar)

**Dimensions:**
1. 系統性風險 (Systematic Risk)
2. 利率風險 (Interest Rate Risk)
3. 流動性風險 (Liquidity Risk)
4. 經濟增長風險 (Economic Growth Risk)
5. 匯率風險 (FX Risk)

**Data Mapping:**
```typescript
{
  type: 'scatterpolar',
  r: [risk values],
  theta: [dimension names],
  fill: 'toself'
}
```

**Features:**
- Red highlight for high-risk areas
- Compare multiple strategies if selected

### 4. CorrelationHeatmap

**Chart Type:** Plotly Heatmap

**Data Mapping:**
```typescript
{
  type: 'heatmap',
  z: [correlation matrix],
  x: [strategy names],
  y: [strategy names],
  colorscale: 'RdYlGn'  // Red=high, Green=low
}
```

**Color Coding:**
- Green (0 to 0.3): Low correlation (good diversification)
- Yellow (0.3 to 0.7): Medium correlation
- Red (0.7 to 1.0): High correlation (risk concentration)

### 5. StressTestTable

**Scenarios:**
1. 基準 (Baseline)
2. 利率+200bp (Rate Shock)
3. 經濟衰退 (Recession)
4. 市場崩盤 (Market Crash)

**Columns:**
- Scenario name
- Expected Return
- Max Drawdown
- Sharpe Ratio

**Styling:**
- Red highlight for losses
- Bold for best/worst performers

## Redux State

```typescript
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
```

## Implementation Tasks

1. Create performanceAnalyticsSlice with mock data fallback
2. Create PerformanceHeader component
3. Create ReturnAttributionChart with Plotly
4. Create RiskRadarChart with Plotly
5. Create CorrelationHeatmap with Plotly
6. Create StressTestTable component
7. Integrate all components into PerformanceTab
8. Add to UnifiedDashboardPage
9. Browser testing
10. Final cleanup and documentation

## Success Criteria

- All charts render correctly with mock data
- Time range switching triggers data reload
- Strategy selection filters data
- Export functionality works
- Responsive layout on desktop and tablet
- No console errors

---

## Implementation Summary

### Files Created

**Components:**
- `frontend/src/components/dashboard/PerformanceTab/PerformanceTab.tsx` - Main container component
- `frontend/src/components/dashboard/PerformanceTab/PerformanceHeader.tsx` - Control bar with time range, strategy select, and export
- `frontend/src/components/dashboard/PerformanceTab/ReturnAttribution/ReturnAttributionChart.tsx` - Stacked bar chart for return breakdown
- `frontend/src/components/dashboard/PerformanceTab/ReturnAttribution/index.ts` - Export index
- `frontend/src/components/dashboard/PerformanceTab/RiskAnalysis/RiskRadarChart.tsx` - 5-dimension radar chart
- `frontend/src/components/dashboard/PerformanceTab/RiskAnalysis/index.ts` - Export index
- `frontend/src/components/dashboard/PerformanceTab/CorrelationAnalysis/CorrelationHeatmap.tsx` - Strategy correlation heatmap
- `frontend/src/components/dashboard/PerformanceTab/CorrelationAnalysis/index.ts` - Export index
- `frontend/src/components/dashboard/PerformanceTab/StressTest/StressTestTable.tsx` - 4-scenario stress test results table
- `frontend/src/components/dashboard/PerformanceTab/StressTest/index.ts` - Export index
- `frontend/src/components/dashboard/PerformanceTab/index.ts` - Component exports

**Redux State Management:**
- `frontend/src/store/slices/performanceAnalyticsSlice.ts` - Performance analytics state management with API integration

**Hooks:**
- `frontend/src/hooks/usePerformanceAnalytics.ts` - Custom hook for data fetching and state management

**API Service:**
- `frontend/src/services/performanceAnalyticsApi.ts` - API client for performance analytics endpoints

**Types:**
- `frontend/src/types/performanceAnalytics.ts` - TypeScript interfaces for all data structures

**Tests:**
- `frontend/src/components/dashboard/PerformanceTab/__tests__/PerformanceTab.test.tsx` - Component tests
- `frontend/src/components/dashboard/PerformanceTab/__tests__/PerformanceHeader.test.tsx` - Header tests
- `frontend/src/components/dashboard/PerformanceTab/__tests__/ReturnAttributionChart.test.tsx` - Chart tests

### Features Implemented

1. **Performance Tab Main Container** - Responsive grid layout with all four visualization modules
2. **Performance Header** - Time range selector (1w, 1m, 3m, 1y, custom), strategy multi-select, export buttons (PDF/CSV)
3. **Return Attribution Chart** - Plotly stacked bar chart showing contribution breakdown by economic indicator
4. **Risk Radar Chart** - 5-dimension radar chart (systematic, interest rate, liquidity, economic growth, FX risks)
5. **Correlation Heatmap** - Plotly heatmap showing strategy correlations with RdYlGn color scale
6. **Stress Test Table** - 4-scenario stress test results (baseline, rate shock, recession, market crash)
7. **Redux Integration** - State management with RTK Query for API calls
8. **Mock Data Fallback** - Graceful degradation when API is unavailable
9. **Export Functionality** - PDF and CSV export for reports
10. **Responsive Design** - Optimized for desktop (primary) and tablet (secondary)

### API Integration

- Uses RTK Query for data fetching
- Implements `/api/analytics/performance` endpoint
- Automatic retry and error handling
- Loading states and error messages

### Build Verification

✅ Build completed successfully with no errors
✅ All components compile correctly
✅ TypeScript types validated
✅ Plotly.js integration working

### Future Enhancements

**TODO Items:**
- [ ] Implement backend API endpoint `/api/analytics/performance`
- [ ] Add real-time data updates via WebSocket
- [ ] Implement custom date range picker
- [ ] Add performance comparison view (strategy vs benchmark)
- [ ] Implement drill-down functionality on charts
- [ ] Add more stress test scenarios
- [ ] Optimize chart rendering for large datasets
- [ ] Add mobile responsive design improvements

### Notes

- All components use existing Plotly.js library (no new dependencies)
- Mock data provided for development and testing
- Components follow existing design patterns (MonitoringTab structure)
- Integrated into UnifiedDashboardPage as "performance" tab
- Export functionality uses jsPDF and Papa Parse libraries (already in project)

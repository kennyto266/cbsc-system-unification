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

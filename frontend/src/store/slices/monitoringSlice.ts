/**
 * Monitoring Slice
 * Manages real-time monitoring state
 */

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';

// Alert types
export type AlertSeverity = 'info' | 'warning' | 'error' | 'critical';
export type AlertCategory = 'strategy' | 'market' | 'system';

interface Alert {
  id: string;
  severity: AlertSeverity;
  category: AlertCategory;
  message: string;
  details?: string;
  strategyId?: string;
  timestamp: Date;
  read: boolean;
  dismissed: boolean;
}

// Strategy execution status
export interface StrategyExecution {
  id: string;
  name: string;
  status: 'running' | 'paused' | 'stopped' | 'error';
  dailyPnl: number;
  dailyPnlPercent: number;
  positions: number;
  lastSignal: {
    type: 'buy' | 'sell' | 'hold';
    timestamp: Date;
    price?: number;
  } | null;
  activity: Array<{
    timestamp: Date;
    type: string;
    message: string;
  }>;
}

// Economic indicator data
export interface EconomicIndicator {
  id: string;
  name: string;
  nameEn: string;
  value: number;
  change: number;
  unit: string;
  trend: number[]; // Last 7 data points
}

// Economic calendar event
export interface CalendarEvent {
  id: string;
  name: string;
  date: Date;
  importance: 'low' | 'medium' | 'high';
  actual?: number;
  forecast?: number;
  previous?: number;
}

// Market sentiment data
export interface MarketSentiment {
  vix: number;
  vixChange: number;
  fundFlow: {
    inflow: number;
    outflow: number;
  };
}

// Monitoring state
interface MonitoringState {
  // Data
  strategies: StrategyExecution[];
  alerts: Alert[];
  economicIndicators: EconomicIndicator[];
  calendarEvents: CalendarEvent[];
  marketSentiment: MarketSentiment | null;

  // Connection status
  connectionStatus: 'connected' | 'delayed' | 'disconnected';
  lastUpdate: Date | null;

  // UI State
  isLoading: boolean;
  isRefreshing: boolean;
  error: string | null;

  // Alert preferences
  alertRules: {
    minSeverity: AlertSeverity;
    enabledCategories: AlertCategory[];
    strategyWhitelist: string[];
  };
}

const initialState: MonitoringState = {
  strategies: [],
  alerts: [],
  economicIndicators: [],
  calendarEvents: [],
  marketSentiment: null,
  connectionStatus: 'connected',
  lastUpdate: null,
  isLoading: false,
  isRefreshing: false,
  error: null,
  alertRules: {
    minSeverity: 'info',
    enabledCategories: ['strategy', 'market', 'system'],
    strategyWhitelist: [],
  },
};

// Async thunks
export const fetchMonitoringData = createAsyncThunk(
  'monitoring/fetchData',
  async (_, { rejectWithValue }) => {
    try {
      // API call will be added when backend is ready
      // const response = await apiClient.get('/monitoring/data');
      // return response.data;

      // Mock data fallback for demo
      return {
        strategies: [
          {
            id: '1',
            name: '經濟動量策略',
            status: 'running',
            dailyPnl: 23000,
            dailyPnlPercent: 2.3,
            positions: 3,
            lastSignal: { type: 'buy', timestamp: new Date(), price: 18500 },
            activity: []
          },
          {
            id: '2',
            name: '流動性情緒策略',
            status: 'running',
            dailyPnl: 8000,
            dailyPnlPercent: 0.8,
            positions: 1,
            lastSignal: { type: 'hold', timestamp: new Date() },
            activity: []
          },
          {
            id: '3',
            name: '宏觀平衡策略',
            status: 'paused',
            dailyPnl: -12000,
            dailyPnlPercent: -1.2,
            positions: 2,
            lastSignal: null,
            activity: []
          },
          {
            id: '4',
            name: 'HIBOR利率策略',
            status: 'running',
            dailyPnl: 15000,
            dailyPnlPercent: 1.5,
            positions: 2,
            lastSignal: { type: 'sell', timestamp: new Date(), price: 5.23 },
            activity: []
          }
        ],
        alerts: [],
        economicIndicators: [],
        calendarEvents: [],
        marketSentiment: null
      };
    } catch (error: any) {
      return rejectWithValue('Failed to fetch monitoring data');
    }
  }
);

export const monitoringSlice = createSlice({
  name: 'monitoring',
  initialState,
  reducers: {
    addAlert: (state, action: PayloadAction<Omit<Alert, 'id' | 'timestamp' | 'read' | 'dismissed'>>) => {
      const alert: Alert = {
        ...action.payload,
        id: Date.now().toString(),
        timestamp: new Date(),
        read: false,
        dismissed: false,
      };
      state.alerts.unshift(alert);
      // Keep only last 100 alerts
      if (state.alerts.length > 100) {
        state.alerts = state.alerts.slice(0, 100);
      }
    },
    markAlertAsRead: (state, action: PayloadAction<string>) => {
      const alert = state.alerts.find((a) => a.id === action.payload);
      if (alert) alert.read = true;
    },
    dismissAlert: (state, action: PayloadAction<string>) => {
      const alert = state.alerts.find((a) => a.id === action.payload);
      if (alert) alert.dismissed = true;
    },
    clearAlerts: (state) => {
      state.alerts = [];
    },
    setAlertRules: (state, action: PayloadAction<Partial<MonitoringState['alertRules']>>) => {
      state.alertRules = { ...state.alertRules, ...action.payload };
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchMonitoringData.pending, (state) => {
        state.isRefreshing = true;
      })
      .addCase(fetchMonitoringData.fulfilled, (state, action) => {
        state.isRefreshing = false;
        state.strategies = action.payload.strategies || [];
        state.economicIndicators = action.payload.economicIndicators || [];
        state.calendarEvents = action.payload.calendarEvents || [];
        state.marketSentiment = action.payload.marketSentiment || null;
        state.lastUpdate = new Date();
        state.connectionStatus = 'connected';
      })
      .addCase(fetchMonitoringData.rejected, (state) => {
        state.isRefreshing = false;
        state.connectionStatus = 'delayed';
      });
  },
});

export const {
  addAlert,
  markAlertAsRead,
  dismissAlert,
  clearAlerts,
  setAlertRules,
} = monitoringSlice.actions;

export default monitoringSlice.reducer;

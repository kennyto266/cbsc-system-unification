import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import { DashboardState, WidgetState, WidgetType, TimeRange, Alert, QuickAction, DashboardLayout } from '../../types/store'

// Initial state
const initialState: DashboardState = {
  layout: {
    columns: 24,
    rowHeight: 100,
    margin: [16, 16],
    containerPadding: [16, 16],
  },
  widgets: [
    // Default widgets
    {
      id: 'portfolio-value',
      type: 'metric-card',
      title: 'Portfolio Value',
      position: { x: 0, y: 0, w: 6, h: 4 },
      config: {
        metric: 'totalValue',
        format: 'currency',
        prefix: '¥',
        precision: 2,
        showTrend: true,
      },
    },
    {
      id: 'total-return',
      type: 'metric-card',
      title: 'Total Return',
      position: { x: 6, y: 0, w: 6, h: 4 },
      config: {
        metric: 'totalReturn',
        format: 'percentage',
        precision: 2,
        showTrend: true,
      },
    },
    {
      id: 'active-strategies',
      type: 'metric-card',
      title: 'Active Strategies',
      position: { x: 12, y: 0, w: 6, h: 4 },
      config: {
        metric: 'activeStrategies',
        format: 'number',
        showTrend: true,
      },
    },
    {
      id: 'sharpe-ratio',
      type: 'metric-card',
      title: 'Sharpe Ratio',
      position: { x: 18, y: 0, w: 6, h: 4 },
      config: {
        metric: 'sharpeRatio',
        format: 'number',
        precision: 2,
        showTrend: true,
      },
    },
    {
      id: 'performance-chart',
      type: 'chart',
      title: 'Portfolio Performance',
      position: { x: 0, y: 4, w: 16, h: 10 },
      config: {
        chartType: 'line',
        dataKey: 'portfolio',
        showBenchmark: true,
        showTooltip: true,
        showLegend: true,
      },
    },
    {
      id: 'allocation-chart',
      type: 'chart',
      title: 'Asset Allocation',
      position: { x: 16, y: 4, w: 8, h: 10 },
      config: {
        chartType: 'pie',
        showDetails: true,
        showTooltip: true,
      },
    },
    {
      id: 'strategy-list',
      type: 'strategy-list',
      title: 'Strategies',
      position: { x: 0, y: 14, w: 12, h: 10 },
      config: {
        showPerformance: true,
        showStatus: true,
        pageSize: 5,
      },
    },
    {
      id: 'recent-signals',
      type: 'recent-signals',
      title: 'Recent Signals',
      position: { x: 12, y: 14, w: 12, h: 10 },
      config: {
        showTimestamp: true,
        showConfidence: true,
        pageSize: 10,
      },
    },
  ],
  timeRange: '1M',
  refreshRate: 30000, // 30 seconds
  alerts: [],
  quickActions: [
    {
      id: 'create-strategy',
      label: 'Create Strategy',
      icon: 'PlusOutlined',
      action: 'openCreateStrategyModal',
    },
    {
      id: 'run-backtest',
      label: 'Run Backtest',
      icon: 'BarChartOutlined',
      action: 'openBacktestModal',
    },
    {
      id: 'export-data',
      label: 'Export Data',
      icon: 'DownloadOutlined',
      action: 'exportData',
    },
    {
      id: 'settings',
      label: 'Dashboard Settings',
      icon: 'SettingOutlined',
      action: 'openSettingsModal',
    },
  ],
}

// Async thunks
export const saveDashboardLayout = createAsyncThunk(
  'dashboard/saveLayout',
  async (layout: { widgets: WidgetState[]; layoutConfig: DashboardLayout }) => {
    const response = await fetch('/api/user/dashboard/layout', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('cbsc_token')}`,
      },
      body: JSON.stringify(layout),
    })

    if (!response.ok) {
      throw new Error('Failed to save dashboard layout')
    }

    return await response.json()
  }
)

export const loadDashboardLayout = createAsyncThunk(
  'dashboard/loadLayout',
  async () => {
    const response = await fetch('/api/user/dashboard/layout', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('cbsc_token')}`,
      },
    })

    if (!response.ok) {
      throw new Error('Failed to load dashboard layout')
    }

    return await response.json()
  }
)

export const fetchAlerts = createAsyncThunk(
  'dashboard/fetchAlerts',
  async (params?: { page?: number; pageSize?: number; unreadOnly?: boolean }) => {
    const queryParams = new URLSearchParams(params as any).toString()
    const response = await fetch(`/api/user/alerts?${queryParams}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('cbsc_token')}`,
      },
    })

    if (!response.ok) {
      throw new Error('Failed to fetch alerts')
    }

    return await response.json()
  }
)

export const markAlertAsRead = createAsyncThunk(
  'dashboard/markAlertAsRead',
  async (alertId: string) => {
    const response = await fetch(`/api/user/alerts/${alertId}/read`, {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('cbsc_token')}`,
      },
    })

    if (!response.ok) {
      throw new Error('Failed to mark alert as read')
    }

    return alertId
  }
)

export const dismissAlert = createAsyncThunk(
  'dashboard/dismissAlert',
  async (alertId: string) => {
    const response = await fetch(`/api/user/alerts/${alertId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('cbsc_token')}`,
      },
    })

    if (!response.ok) {
      throw new Error('Failed to dismiss alert')
    }

    return alertId
  }
)

// Slice
const dashboardSlice = createSlice({
  name: 'dashboard',
  initialState,
  reducers: {
    setLayout: (state, action: PayloadAction<DashboardLayout>) => {
      state.layout = { ...state.layout, ...action.payload }
    },
    addWidget: (state, action: PayloadAction<Omit<WidgetState, 'id'>>) => {
      const newWidget: WidgetState = {
        ...action.payload,
        id: `widget-${Date.now()}`,
      }
      state.widgets.push(newWidget)
    },
    updateWidget: (state, action: PayloadAction<{ id: string; updates: Partial<WidgetState> }>) => {
      const { id, updates } = action.payload
      const widgetIndex = state.widgets.findIndex(w => w.id === id)
      if (widgetIndex >= 0) {
        state.widgets[widgetIndex] = {
          ...state.widgets[widgetIndex],
          ...updates,
        }
      }
    },
    removeWidget: (state, action: PayloadAction<string>) => {
      state.widgets = state.widgets.filter(w => w.id !== action.payload)
    },
    updateWidgetPosition: (state, action: PayloadAction<{ id: string; position: WidgetState['position'] }>) => {
      const { id, position } = action.payload
      const widget = state.widgets.find(w => w.id === id)
      if (widget) {
        widget.position = position
      }
    },
    updateWidgetConfig: (state, action: PayloadAction<{ id: string; config: WidgetState['config'] }>) => {
      const { id, config } = action.payload
      const widget = state.widgets.find(w => w.id === id)
      if (widget) {
        widget.config = { ...widget.config, ...config }
      }
    },
    setTimeRange: (state, action: PayloadAction<TimeRange>) => {
      state.timeRange = action.payload
    },
    setRefreshRate: (state, action: PayloadAction<number>) => {
      state.refreshRate = action.payload
    },
    addAlert: (state, action: PayloadAction<Omit<Alert, 'id' | 'timestamp' | 'read'>>) => {
      const newAlert: Alert = {
        ...action.payload,
        id: `alert-${Date.now()}`,
        timestamp: new Date().toISOString(),
        read: false,
      }
      state.alerts.unshift(newAlert)

      // Keep only last 100 alerts
      if (state.alerts.length > 100) {
        state.alerts = state.alerts.slice(0, 100)
      }
    },
    updateAlert: (state, action: PayloadAction<{ id: string; updates: Partial<Alert> }>) => {
      const { id, updates } = action.payload
      const alertIndex = state.alerts.findIndex(a => a.id === id)
      if (alertIndex >= 0) {
        state.alerts[alertIndex] = {
          ...state.alerts[alertIndex],
          ...updates,
        }
      }
    },
    markAllAlertsAsRead: (state) => {
      state.alerts.forEach(alert => {
        alert.read = true
      })
    },
    clearAllAlerts: (state) => {
      state.alerts = []
    },
    addQuickAction: (state, action: PayloadAction<Omit<QuickAction, 'id'>>) => {
      const newAction: QuickAction = {
        ...action.payload,
        id: `action-${Date.now()}`,
      }
      state.quickActions.push(newAction)
    },
    updateQuickAction: (state, action: PayloadAction<{ id: string; updates: Partial<QuickAction> }>) => {
      const { id, updates } = action.payload
      const actionIndex = state.quickActions.findIndex(a => a.id === id)
      if (actionIndex >= 0) {
        state.quickActions[actionIndex] = {
          ...state.quickActions[actionIndex],
          ...updates,
        }
      }
    },
    removeQuickAction: (state, action: PayloadAction<string>) => {
      state.quickActions = state.quickActions.filter(a => a.id !== action.payload)
    },
    resetToDefaultLayout: (state) => {
      // Reset to default widget configuration
      state.widgets = initialState.widgets.map((widget, index) => ({
        ...widget,
        id: `widget-${Date.now()}-${index}`,
      }))
    },
    duplicateWidget: (state, action: PayloadAction<string>) => {
      const widget = state.widgets.find(w => w.id === action.payload)
      if (widget) {
        const duplicated: WidgetState = {
          ...widget,
          id: `widget-${Date.now()}`,
          title: `${widget.title} (Copy)`,
          position: {
            ...widget.position,
            x: widget.position.x + widget.position.w % state.layout.columns,
          },
        }
        state.widgets.push(duplicated)
      }
    },
  },
  extraReducers: (builder) => {
    // saveDashboardLayout
    builder
      .addCase(saveDashboardLayout.pending, (state) => {
        // Maybe add a saving state to specific widget
      })
      .addCase(saveDashboardLayout.fulfilled, (state, action) => {
        // Layout saved successfully
      })
      .addCase(saveDashboardLayout.rejected, (state, action) => {
        // Add error notification
        console.error('Failed to save dashboard layout:', action.error.message)
      })

    // loadDashboardLayout
    builder
      .addCase(loadDashboardLayout.pending, (state) => {
        // Show loading state
      })
      .addCase(loadDashboardLayout.fulfilled, (state, action) => {
        const { widgets, layout } = action.payload
        if (widgets) state.widgets = widgets
        if (layout) state.layout = layout
      })
      .addCase(loadDashboardLayout.rejected, (state, action) => {
        console.error('Failed to load dashboard layout:', action.error.message)
        // Keep using default layout
      })

    // fetchAlerts
    builder
      .addCase(fetchAlerts.fulfilled, (state, action) => {
        state.alerts = action.payload
      })
      .addCase(fetchAlerts.rejected, (state, action) => {
        console.error('Failed to fetch alerts:', action.error.message)
      })

    // markAlertAsRead
    builder
      .addCase(markAlertAsRead.fulfilled, (state, action) => {
        const alert = state.alerts.find(a => a.id === action.payload)
        if (alert) {
          alert.read = true
        }
      })

    // dismissAlert
    builder
      .addCase(dismissAlert.fulfilled, (state, action) => {
        state.alerts = state.alerts.filter(a => a.id !== action.payload)
      })
  },
})

export const {
  setLayout,
  addWidget,
  updateWidget,
  removeWidget,
  updateWidgetPosition,
  updateWidgetConfig,
  setTimeRange,
  setRefreshRate,
  addAlert,
  updateAlert,
  markAllAlertsAsRead,
  clearAllAlerts,
  addQuickAction,
  updateQuickAction,
  removeQuickAction,
  resetToDefaultLayout,
  duplicateWidget,
} = dashboardSlice.actions

export default dashboardSlice.reducer

// Selectors
export const selectDashboardLayout = (state: { dashboard: DashboardState }) => state.dashboard.layout
export const selectDashboardWidgets = (state: { dashboard: DashboardState }) => state.dashboard.widgets
export const selectDashboardWidget = (id: string) => (state: { dashboard: DashboardState }) =>
  state.dashboard.widgets.find(w => w.id === id)
export const selectTimeRange = (state: { dashboard: DashboardState }) => state.dashboard.timeRange
export const selectRefreshRate = (state: { dashboard: DashboardState }) => state.dashboard.refreshRate
export const selectDashboardAlerts = (state: { dashboard: DashboardState }) => state.dashboard.alerts
export const selectUnreadAlerts = (state: { dashboard: DashboardState }) =>
  state.dashboard.alerts.filter(a => !a.read)
export const selectUnreadAlertCount = (state: { dashboard: DashboardState }) =>
  state.dashboard.alerts.filter(a => !a.read).length
export const selectQuickActions = (state: { dashboard: DashboardState }) => state.dashboard.quickActions
export const selectWidgetsByType = (type: WidgetType) => (state: { dashboard: DashboardState }) =>
  state.dashboard.widgets.filter(w => w.type === type)
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'

// Enhanced interfaces for monitoring
interface SystemHealth {
  status: 'healthy' | 'warning' | 'error' | 'critical'
  cpuUsage: number
  memoryUsage: number
  diskUsage: number
  networkLatency: number
  activeConnections: number
  uptime: number
  lastUpdate: string
}

interface Alert {
  id: string
  type: 'info' | 'warning' | 'error' | 'critical'
  title: string
  message: string
  timestamp: string
  read: boolean
  strategyId?: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  source: 'system' | 'strategy' | 'market' | 'network'
}

interface NetworkActivity {
  service: string
  requestsPerSecond: number
  responseTime: number
  status: 'healthy' | 'warning' | 'error'
  uptime: number
}

interface PerformanceMetrics {
  responseTime: number
  throughput: number
  errorRate: number
  availability: number
}

interface MonitoringState {
  // System health
  systemHealth: SystemHealth | null

  // Alerts
  alerts: Alert[]
  unreadAlertsCount: number

  // Network monitoring
  networkActivity: NetworkActivity[]
  performanceMetrics: PerformanceMetrics | null

  // Real-time metrics
  realTimeMetrics: {
    cpu: number[]
    memory: number[]
    network: number[]
    timestamps: string[]
  }

  // Loading states
  loading: boolean
  error: string | null

  // Monitoring settings
  alertThresholds: {
    cpu: number
    memory: number
    disk: number
    responseTime: number
  }

  // Auto-refresh settings
  autoRefresh: boolean
  refreshInterval: number
}

const initialState: MonitoringState = {
  systemHealth: null,
  alerts: [],
  unreadAlertsCount: 0,
  networkActivity: [],
  performanceMetrics: null,
  realTimeMetrics: {
    cpu: [],
    memory: [],
    network: [],
    timestamps: [],
  },
  loading: false,
  error: null,
  alertThresholds: {
    cpu: 80,
    memory: 80,
    disk: 90,
    responseTime: 5000,
  },
  autoRefresh: true,
  refreshInterval: 5000,
}

// Async thunks
export const fetchSystemHealth = createAsyncThunk(
  'monitoring/fetchSystemHealth',
  async () => {
    const response = await fetch('/api/monitoring/system-health')
    if (!response.ok) {
      throw new Error('Failed to fetch system health')
    }
    return response.json()
  }
)

export const fetchAlerts = createAsyncThunk(
  'monitoring/fetchAlerts',
  async (params?: { unread?: boolean; severity?: string; limit?: number }) => {
    const queryString = new URLSearchParams(params as any).toString()
    const response = await fetch(`/api/monitoring/alerts?${queryString}`)
    if (!response.ok) {
      throw new Error('Failed to fetch alerts')
    }
    return response.json()
  }
)

export const fetchNetworkActivity = createAsyncThunk(
  'monitoring/fetchNetworkActivity',
  async () => {
    const response = await fetch('/api/monitoring/network')
    if (!response.ok) {
      throw new Error('Failed to fetch network activity')
    }
    return response.json()
  }
)

export const markAlertAsRead = createAsyncThunk(
  'monitoring/markAlertAsRead',
  async (alertId: string) => {
    const response = await fetch(`/api/monitoring/alerts/${alertId}/read`, {
      method: 'PATCH',
    })
    if (!response.ok) {
      throw new Error('Failed to mark alert as read')
    }
    return alertId
  }
)

export const clearAlerts = createAsyncThunk(
  'monitoring/clearAlerts',
  async (params?: { type?: string; olderThan?: string }) => {
    const queryString = new URLSearchParams(params as any).toString()
    const response = await fetch(`/api/monitoring/alerts/clear?${queryString}`, {
      method: 'DELETE',
    })
    if (!response.ok) {
      throw new Error('Failed to clear alerts')
    }
    return params
  }
)

const monitoringSlice = createSlice({
  name: 'monitoring',
  initialState,
  reducers: {
    updateSystemHealth: (state, action: PayloadAction<SystemHealth>) => {
      state.systemHealth = action.payload
    },
    addRealTimeMetric: (state, action) => {
      const { cpu, memory, network, timestamp } = action.payload

      // Keep only last 100 data points
      if (state.realTimeMetrics.cpu.length >= 100) {
        state.realTimeMetrics.cpu.shift()
        state.realTimeMetrics.memory.shift()
        state.realTimeMetrics.network.shift()
        state.realTimeMetrics.timestamps.shift()
      }

      state.realTimeMetrics.cpu.push(cpu)
      state.realTimeMetrics.memory.push(memory)
      state.realTimeMetrics.network.push(network)
      state.realTimeMetrics.timestamps.push(timestamp)
    },
    addAlert: (state, action: PayloadAction<Alert>) => {
      state.alerts.unshift(action.payload)
      if (!action.payload.read) {
        state.unreadAlertsCount += 1
      }
    },
    updateAlertThresholds: (state, action) => {
      state.alertThresholds = { ...state.alertThresholds, ...action.payload }
    },
    setAutoRefresh: (state, action: PayloadAction<boolean>) => {
      state.autoRefresh = action.payload
    },
    setRefreshInterval: (state, action: PayloadAction<number>) => {
      state.refreshInterval = action.payload
    },
    clearError: (state) => {
      state.error = null
    },
    // WebSocket real-time updates
    updateRealTimeData: (state, action) => {
      if (action.payload.systemHealth) {
        state.systemHealth = { ...state.systemHealth, ...action.payload.systemHealth }
      }
      if (action.payload.alert) {
        state.alerts.unshift(action.payload.alert)
        if (!action.payload.alert.read) {
          state.unreadAlertsCount += 1
        }
      }
      if (action.payload.metrics) {
        const { cpu, memory, network } = action.payload.metrics
        const timestamp = new Date().toISOString()

        if (state.realTimeMetrics.cpu.length >= 100) {
          state.realTimeMetrics.cpu.shift()
          state.realTimeMetrics.memory.shift()
          state.realTimeMetrics.network.shift()
          state.realTimeMetrics.timestamps.shift()
        }

        state.realTimeMetrics.cpu.push(cpu)
        state.realTimeMetrics.memory.push(memory)
        state.realTimeMetrics.network.push(network)
        state.realTimeMetrics.timestamps.push(timestamp)
      }
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch system health
      .addCase(fetchSystemHealth.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchSystemHealth.fulfilled, (state, action) => {
        state.loading = false
        state.systemHealth = action.payload
      })
      .addCase(fetchSystemHealth.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || 'Failed to fetch system health'
      })

      // Fetch alerts
      .addCase(fetchAlerts.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchAlerts.fulfilled, (state, action) => {
        state.loading = false
        state.alerts = action.payload
        state.unreadAlertsCount = action.payload.filter((alert: Alert) => !alert.read).length
      })
      .addCase(fetchAlerts.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || 'Failed to fetch alerts'
      })

      // Fetch network activity
      .addCase(fetchNetworkActivity.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchNetworkActivity.fulfilled, (state, action) => {
        state.loading = false
        state.networkActivity = action.payload
      })
      .addCase(fetchNetworkActivity.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || 'Failed to fetch network activity'
      })

      // Mark alert as read
      .addCase(markAlertAsRead.fulfilled, (state, action) => {
        const alertId = action.payload
        const alert = state.alerts.find(a => a.id === alertId)
        if (alert && !alert.read) {
          alert.read = true
          state.unreadAlertsCount = Math.max(0, state.unreadAlertsCount - 1)
        }
      })

      // Clear alerts
      .addCase(clearAlerts.fulfilled, (state, action) => {
        const { type, olderThan } = action.payload || {}

        if (type) {
          state.alerts = state.alerts.filter(alert => alert.type !== type)
        }

        if (olderThan) {
          const cutoffTime = new Date(olderThan)
          state.alerts = state.alerts.filter(alert => new Date(alert.timestamp) > cutoffTime)
        }

        if (!type && !olderThan) {
          state.alerts = []
          state.unreadAlertsCount = 0
        } else {
          state.unreadAlertsCount = state.alerts.filter(alert => !alert.read).length
        }
      })
  },
})

export const {
  updateSystemHealth,
  addRealTimeMetric,
  addAlert,
  updateAlertThresholds,
  setAutoRefresh,
  setRefreshInterval,
  clearError,
  updateRealTimeData,
} = monitoringSlice.actions

// Selectors
export const selectMonitoring = (state: { monitoring: MonitoringState }) => state.monitoring
export const selectSystemHealth = (state: { monitoring: MonitoringState }) => state.monitoring.systemHealth
export const selectAlerts = (state: { monitoring: MonitoringState }) => state.monitoring.alerts
export const selectRealTimeMetrics = (state: { monitoring: MonitoringState }) => state.monitoring.realTimeMetrics

export default monitoringSlice.reducer

import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { WebSocketStatus, StrategyUpdate, TradingSignal, SystemHealth } from '../../types'

interface UIState {
  theme: 'light' | 'dark'
  sidebarCollapsed: boolean
  loading: boolean
  // WebSocket相關狀態
  webSocketStatus: WebSocketStatus
  realtimeStrategies: StrategyUpdate[]
  realtimeSignals: TradingSignal[]
  systemHealth: SystemHealth | null
}

const initialState: UIState = {
  theme: 'light',
  sidebarCollapsed: false,
  loading: false,
  // WebSocket初始狀態
  webSocketStatus: {
    connected: false,
    reconnecting: false,
    reconnectAttempts: 0
  },
  realtimeStrategies: [],
  realtimeSignals: [],
  systemHealth: null
}

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    setTheme: (state, action: PayloadAction<'light' | 'dark'>) => {
      state.theme = action.payload
    },
    toggleSidebar: (state) => {
      state.sidebarCollapsed = !state.sidebarCollapsed
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload
    },
    // WebSocket相關actions
    setWebSocketStatus: (state, action: PayloadAction<Partial<WebSocketStatus>>) => {
      state.webSocketStatus = { ...state.webSocketStatus, ...action.payload }
    },
    updateStrategyData: (state, action: PayloadAction<StrategyUpdate[]>) => {
      state.realtimeStrategies = action.payload
    },
    updatePerformanceMetrics: (state, action: PayloadAction<any>) => {
      // 更新策略性能數據
      if (action.payload.updated_strategies) {
        action.payload.updated_strategies.forEach((updatedStrategy: StrategyUpdate) => {
          const index = state.realtimeStrategies.findIndex(s => s.id === updatedStrategy.id)
          if (index !== -1) {
            state.realtimeStrategies[index] = { ...state.realtimeStrategies[index], ...updatedStrategy }
          } else {
            state.realtimeStrategies.push(updatedStrategy)
          }
        })
      }
    },
    addNewSignal: (state, action: PayloadAction<TradingSignal>) => {
      // 限制信號數量，保持最新的100條
      state.realtimeSignals.unshift(action.payload)
      if (state.realtimeSignals.length > 100) {
        state.realtimeSignals = state.realtimeSignals.slice(0, 100)
      }
    },
    updateSystemHealth: (state, action: PayloadAction<SystemHealth>) => {
      state.systemHealth = action.payload
    },
    clearRealtimeData: (state) => {
      state.realtimeStrategies = []
      state.realtimeSignals = []
      state.systemHealth = null
    }
  },
})

export const {
  setTheme,
  toggleSidebar,
  setLoading,
  setWebSocketStatus,
  updateStrategyData,
  updatePerformanceMetrics,
  addNewSignal,
  updateSystemHealth,
  clearRealtimeData
} = uiSlice.actions

export default uiSlice.reducer

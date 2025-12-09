import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { MonitoringState, SystemStatus, MarketData, WebSocketMessage, Strategy } from '@types/index'

const initialState: MonitoringState = {
  isConnected: false,
  lastMessage: null,
  systemStatus: null,
  marketData: {},
  activeStrategies: [],
}

const monitoringSlice = createSlice({
  name: 'monitoring',
  initialState,
  reducers: {
    setWebSocketConnected: (state, action: PayloadAction<boolean>) => {
      state.isConnected = action.payload
    },
    setLastMessage: (state, action: PayloadAction<WebSocketMessage | null>) => {
      state.lastMessage = action.payload
    },
    setSystemStatus: (state, action: PayloadAction<SystemStatus>) => {
      state.systemStatus = action.payload
    },
    updateSystemStatus: (state, action: PayloadAction<Partial<SystemStatus>>) => {
      if (state.systemStatus) {
        state.systemStatus = { ...state.systemStatus, ...action.payload }
      }
    },
    setMarketData: (state, action: PayloadAction<Record<string, MarketData>>) => {
      state.marketData = action.payload
    },
    updateMarketData: (state, action: PayloadAction<{ symbol: string; data: MarketData }>) => {
      const { symbol, data } = action.payload
      state.marketData[symbol] = data
    },
    removeMarketData: (state, action: PayloadAction<string>) => {
      delete state.marketData[action.payload]
    },
    setActiveStrategies: (state, action: PayloadAction<Strategy[]>) => {
      state.activeStrategies = action.payload
    },
    addActiveStrategy: (state, action: PayloadAction<Strategy>) => {
      const exists = state.activeStrategies.find(s => s.id === action.payload.id)
      if (!exists) {
        state.activeStrategies.push(action.payload)
      }
    },
    updateActiveStrategy: (state, action: PayloadAction<{ id: string; updates: Partial<Strategy> }>) => {
      const { id, updates } = action.payload
      const index = state.activeStrategies.findIndex(strategy => strategy.id === id)
      if (index !== -1) {
        state.activeStrategies[index] = { ...state.activeStrategies[index], ...updates }
      }
    },
    removeActiveStrategy: (state, action: PayloadAction<string>) => {
      state.activeStrategies = state.activeStrategies.filter(strategy => strategy.id !== action.payload)
    },
    // WebSocket message handlers
    handlePerformanceUpdate: (state, action: PayloadAction<any>) => {
      // Handle performance update messages
      // This would update strategy performance data
    },
    handleSignalsUpdate: (state, action: PayloadAction<any>) => {
      // Handle signals update messages
      // This would update signals data
    },
    handleMarketDataUpdate: (state, action: PayloadAction<{ symbol: string; data: MarketData }>) => {
      const { symbol, data } = action.payload
      state.marketData[symbol] = data
    },
    handleSystemStatusUpdate: (state, action: PayloadAction<SystemStatus>) => {
      state.systemStatus = action.payload
    },
    handleStrategyExecutionUpdate: (state, action: PayloadAction<any>) => {
      // Handle strategy execution update messages
      // This would update execution data
    },
    // Clear monitoring data (for logout)
    clearMonitoringData: (state) => {
      return { ...initialState }
    },
  },
})

export const {
  setWebSocketConnected,
  setLastMessage,
  setSystemStatus,
  updateSystemStatus,
  setMarketData,
  updateMarketData,
  removeMarketData,
  setActiveStrategies,
  addActiveStrategy,
  updateActiveStrategy,
  removeActiveStrategy,
  handlePerformanceUpdate,
  handleSignalsUpdate,
  handleMarketDataUpdate,
  handleSystemStatusUpdate,
  handleStrategyExecutionUpdate,
  clearMonitoringData,
} = monitoringSlice.actions

export default monitoringSlice.reducer

// Selectors
export const selectWebSocketConnected = (state: { monitoring: MonitoringState }) => state.monitoring.isConnected
export const selectLastMessage = (state: { monitoring: MonitoringState }) => state.monitoring.lastMessage
export const selectSystemStatus = (state: { monitoring: MonitoringState }) => state.monitoring.systemStatus
export const selectMarketData = (state: { monitoring: MonitoringState }) => state.monitoring.marketData
export const selectMarketDataBySymbol = (state: { monitoring: MonitoringState }, symbol: string) =>
  state.monitoring.marketData[symbol]
export const selectActiveStrategies = (state: { monitoring: MonitoringState }) => state.monitoring.activeStrategies
export const selectActiveStrategyById = (state: { monitoring: MonitoringState }, id: string) =>
  state.monitoring.activeStrategies.find(strategy => strategy.id === id)
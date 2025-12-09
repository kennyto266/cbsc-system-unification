import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import {
  StrategyState,
  Strategy,
  StrategySignal,
  StrategyExecutionResult,
  CBSCStrategyTemplate,
  StrategyType
} from '@types/index'

const initialState: StrategyState = {
  list: [],
  templates: [],
  selectedStrategy: null,
  signals: [],
  executions: {},
  loading: false,
  error: null,
}

const strategiesSlice = createSlice({
  name: 'strategies',
  initialState,
  reducers: {
    setStrategies: (state, action: PayloadAction<Strategy[]>) => {
      state.list = action.payload
    },
    addStrategy: (state, action: PayloadAction<Strategy>) => {
      state.list.push(action.payload)
    },
    updateStrategy: (state, action: PayloadAction<{ id: string; updates: Partial<Strategy> }>) => {
      const { id, updates } = action.payload
      const index = state.list.findIndex(strategy => strategy.id === id)
      if (index !== -1) {
        state.list[index] = { ...state.list[index], ...updates }
      }
    },
    removeStrategy: (state, action: PayloadAction<string>) => {
      state.list = state.list.filter(strategy => strategy.id !== action.payload)
    },
    setSelectedStrategy: (state, action: PayloadAction<Strategy | null>) => {
      state.selectedStrategy = action.payload
    },
    setSignals: (state, action: PayloadAction<StrategySignal[]>) => {
      state.signals = action.payload
    },
    addSignal: (state, action: PayloadAction<StrategySignal>) => {
      state.signals.unshift(action.payload)
      // Keep only last 1000 signals
      if (state.signals.length > 1000) {
        state.signals = state.signals.slice(0, 1000)
      }
    },
    addExecution: (state, action: PayloadAction<StrategyExecutionResult>) => {
      state.executions[action.payload.executionId] = action.payload
    },
    updateExecution: (state, action: PayloadAction<{ executionId: string; updates: Partial<StrategyExecutionResult> }>) => {
      const { executionId, updates } = action.payload
      if (state.executions[executionId]) {
        state.executions[executionId] = { ...state.executions[executionId], ...updates }
      }
    },
    removeExecution: (state, action: PayloadAction<string>) => {
      delete state.executions[action.payload]
    },
    setTemplates: (state, action: PayloadAction<CBSCStrategyTemplate[]>) => {
      state.templates = action.payload
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
    },
    clearError: (state) => {
      state.error = null
    },
    // Filter strategies by type
    filterStrategiesByType: (state, action: PayloadAction<StrategyType | null>) => {
      if (action.payload === null) {
        // Show all strategies (handled at component level)
        return
      }
      // This would be handled at component level with a selector
    },
    // Batch operations
    batchUpdateStrategies: (state, action: PayloadAction<{ strategyIds: string[]; updates: Partial<Strategy> }>) => {
      const { strategyIds, updates } = action.payload
      strategyIds.forEach(id => {
        const index = state.list.findIndex(strategy => strategy.id === id)
        if (index !== -1) {
          state.list[index] = { ...state.list[index], ...updates }
        }
      })
    },
    batchDeleteStrategies: (state, action: PayloadAction<string[]>) => {
      const idsToDelete = new Set(action.payload)
      state.list = state.list.filter(strategy => !idsToDelete.has(strategy.id))
    },
    // Clear all data (for logout)
    clearStrategiesData: (state) => {
      return { ...initialState }
    },
  },
})

export const {
  setStrategies,
  addStrategy,
  updateStrategy,
  removeStrategy,
  setSelectedStrategy,
  setSignals,
  addSignal,
  addExecution,
  updateExecution,
  removeExecution,
  setTemplates,
  setLoading,
  setError,
  clearError,
  filterStrategiesByType,
  batchUpdateStrategies,
  batchDeleteStrategies,
  clearStrategiesData,
} = strategiesSlice.actions

export default strategiesSlice.reducer

// Selectors
export const selectStrategies = (state: { strategies: StrategyState }) => state.strategies.list
export const selectStrategyById = (state: { strategies: StrategyState }, id: string) =>
  state.strategies.list.find(strategy => strategy.id === id)
export const selectStrategiesByType = (state: { strategies: StrategyState }, type: StrategyType) =>
  state.strategies.list.filter(strategy => strategy.strategyType === type)
export const selectActiveStrategies = (state: { strategies: StrategyState }) =>
  state.strategies.list.filter(strategy => strategy.isActive)
export const selectSelectedStrategy = (state: { strategies: StrategyState }) => state.strategies.selectedStrategy
export const selectSignals = (state: { strategies: StrategyState }) => state.strategies.signals
export const selectRecentSignals = (state: { strategies: StrategyState }, limit: number = 50) =>
  state.strategies.signals.slice(0, limit)
export const selectExecutions = (state: { strategies: StrategyState }) => state.strategies.executions
export const selectExecutionById = (state: { strategies: StrategyState }, executionId: string) =>
  state.strategies.executions[executionId]
export const selectTemplates = (state: { strategies: StrategyState }) => state.strategies.templates
export const selectStrategiesLoading = (state: { strategies: StrategyState }) => state.strategies.loading
export const selectStrategiesError = (state: { strategies: StrategyState }) => state.strategies.error
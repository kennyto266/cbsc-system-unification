import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { Strategy } from '../../types/strategy'

// Extended strategy state interface
interface StrategyState {
  strategies: Strategy[]
  selectedStrategy: Strategy | null
  editingStrategy: Partial<Strategy> | null
  clonedStrategy: Partial<Strategy> | null
  isLoading: boolean
  error: string | null
  filters: {
    status: string[]
    category: string[]
    riskLevel: string[]
    search: string
  }
  sorting: {
    field: string
    order: 'asc' | 'desc'
  }
  pagination: {
    page: number
    pageSize: number
    total: number
  }
  execution: {
    [strategyId: string]: {
      isRunning: boolean
      lastExecution: string | null
      nextExecution: string | null
      executionHistory: Array<{
        id: string
        timestamp: string
        status: 'success' | 'error' | 'running'
        signals: number
        error?: string
      }>
    }
  }
  parameters: {
    [strategyId: string]: {
      current: Record<string, any>
      default: Record<string, any>
      validation: Record<string, any>
    }
  }
  backtest: {
    [strategyId: string]: {
      isRunning: boolean
      results: any | null
      error: string | null
      config: {
        startDate: string
        endDate: string
        initialCapital: number
        commission: number
        slippage: number
      }
    }
  }
}

const initialState: StrategyState = {
  strategies: [],
  selectedStrategy: null,
  editingStrategy: null,
  clonedStrategy: null,
  isLoading: false,
  error: null,
  filters: {
    status: [],
    category: [],
    riskLevel: [],
    search: '',
  },
  sorting: {
    field: 'updatedAt',
    order: 'desc',
  },
  pagination: {
    page: 1,
    pageSize: 20,
    total: 0,
  },
  execution: {},
  parameters: {},
  backtest: {},
}

export const strategySlice = createSlice({
  name: 'strategy',
  initialState,
  reducers: {
    // Basic CRUD operations
    setStrategies: (state, action: PayloadAction<Strategy[]>) => {
      state.strategies = action.payload
      state.pagination.total = action.payload.length
    },
    setSelectedStrategy: (state, action: PayloadAction<Strategy | null>) => {
      state.selectedStrategy = action.payload
      // Reset editing state when selecting a new strategy
      if (action.payload) {
        state.editingStrategy = null
      }
    },
    addStrategy: (state, action: PayloadAction<Strategy>) => {
      state.strategies.unshift(action.payload) // Add to beginning
      state.pagination.total += 1
    },
    updateStrategy: (state, action: PayloadAction<Strategy>) => {
      const index = state.strategies.findIndex((s) => s.id === action.payload.id)
      if (index !== -1) {
        state.strategies[index] = action.payload
        // Update selected strategy if it's the same one
        if (state.selectedStrategy?.id === action.payload.id) {
          state.selectedStrategy = action.payload
        }
      }
    },
    removeStrategy: (state, action: PayloadAction<string>) => {
      const id = action.payload
      state.strategies = state.strategies.filter((s) => s.id !== id)
      state.pagination.total = Math.max(0, state.pagination.total - 1)

      // Clean up related state
      delete state.execution[id]
      delete state.parameters[id]
      delete state.backtest[id]

      // Clear selected strategy if it was removed
      if (state.selectedStrategy?.id === id) {
        state.selectedStrategy = null
        state.editingStrategy = null
      }
    },

    // Editing operations
    startEditing: (state, action: PayloadAction<string>) => {
      const strategy = state.strategies.find((s) => s.id === action.payload)
      if (strategy) {
        state.editingStrategy = { ...strategy }
      }
    },
    updateEditingStrategy: (state, action: PayloadAction<Partial<Strategy>>) => {
      if (state.editingStrategy) {
        state.editingStrategy = { ...state.editingStrategy, ...action.payload }
      }
    },
    cancelEditing: (state) => {
      state.editingStrategy = null
    },
    saveEditingStrategy: (state) => {
      if (state.editingStrategy) {
        const index = state.strategies.findIndex((s) => s.id === state.editingStrategy!.id)
        if (index !== -1) {
          state.strategies[index] = state.editingStrategy as Strategy
          state.selectedStrategy = state.editingStrategy as Strategy
        }
        state.editingStrategy = null
      }
    },

    // Cloning operations
    startCloning: (state, action: PayloadAction<string>) => {
      const strategy = state.strategies.find((s) => s.id === action.payload)
      if (strategy) {
        state.clonedStrategy = {
          ...strategy,
          id: '',
          name: `${strategy.name} (Copy)`,
          status: 'inactive',
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        }
      }
    },
    updateClonedStrategy: (state, action: PayloadAction<Partial<Strategy>>) => {
      if (state.clonedStrategy) {
        state.clonedStrategy = { ...state.clonedStrategy, ...action.payload }
      }
    },
    cancelCloning: (state) => {
      state.clonedStrategy = null
    },

    // Loading and error states
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
    },
    clearError: (state) => {
      state.error = null
    },

    // Filtering and sorting
    setFilters: (state, action: PayloadAction<Partial<StrategyState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload }
      state.pagination.page = 1 // Reset to first page when filters change
    },
    clearFilters: (state) => {
      state.filters = {
        status: [],
        category: [],
        riskLevel: [],
        search: '',
      }
    },
    setSorting: (state, action: PayloadAction<Partial<StrategyState['sorting']>>) => {
      state.sorting = { ...state.sorting, ...action.payload }
    },
    setPagination: (state, action: PayloadAction<Partial<StrategyState['pagination']>>) => {
      state.pagination = { ...state.pagination, ...action.payload }
    },

    // Execution management
    startExecution: (state, action: PayloadAction<string>) => {
      const strategyId = action.payload
      if (!state.execution[strategyId]) {
        state.execution[strategyId] = {
          isRunning: false,
          lastExecution: null,
          nextExecution: null,
          executionHistory: [],
        }
      }
      state.execution[strategyId].isRunning = true
    },
    stopExecution: (state, action: PayloadAction<string>) => {
      const strategyId = action.payload
      if (state.execution[strategyId]) {
        state.execution[strategyId].isRunning = false
      }
    },
    addExecutionRecord: (state, action: PayloadAction<{
      strategyId: string
      record: {
        id: string
        timestamp: string
        status: 'success' | 'error' | 'running'
        signals: number
        error?: string
      }
    }>) => {
      const { strategyId, record } = action.payload
      if (!state.execution[strategyId]) {
        state.execution[strategyId] = {
          isRunning: false,
          lastExecution: null,
          nextExecution: null,
          executionHistory: [],
        }
      }
      state.execution[strategyId].executionHistory.unshift(record)
      state.execution[strategyId].lastExecution = record.timestamp
      state.execution[strategyId].isRunning = record.status === 'running'

      // Keep only last 50 execution records
      if (state.execution[strategyId].executionHistory.length > 50) {
        state.execution[strategyId].executionHistory = state.execution[strategyId].executionHistory.slice(0, 50)
      }
    },

    // Parameter management
    setStrategyParameters: (state, action: PayloadAction<{
      strategyId: string
      parameters: {
        current: Record<string, any>
        default: Record<string, any>
        validation: Record<string, any>
      }
    }>) => {
      const { strategyId, parameters } = action.payload
      state.parameters[strategyId] = parameters
    },
    updateParameter: (state, action: PayloadAction<{
      strategyId: string
      key: string
      value: any
    }>) => {
      const { strategyId, key, value } = action.payload
      if (state.parameters[strategyId]) {
        state.parameters[strategyId].current[key] = value
      }
    },
    resetParameters: (state, action: PayloadAction<string>) => {
      const strategyId = action.payload
      if (state.parameters[strategyId]) {
        state.parameters[strategyId].current = { ...state.parameters[strategyId].default }
      }
    },

    // Backtesting
    startBacktest: (state, action: PayloadAction<{
      strategyId: string
      config: Partial<StrategyState['backtest'][string]['config']>
    }>) => {
      const { strategyId, config } = action.payload
      if (!state.backtest[strategyId]) {
        state.backtest[strategyId] = {
          isRunning: false,
          results: null,
          error: null,
          config: {
            startDate: '',
            endDate: '',
            initialCapital: 100000,
            commission: 0.001,
            slippage: 0.0001,
          },
        }
      }
      state.backtest[strategyId].isRunning = true
      state.backtest[strategyId].config = { ...state.backtest[strategyId].config, ...config }
      state.backtest[strategyId].error = null
    },
    setBacktestResults: (state, action: PayloadAction<{
      strategyId: string
      results: any
    }>) => {
      const { strategyId, results } = action.payload
      if (state.backtest[strategyId]) {
        state.backtest[strategyId].results = results
        state.backtest[strategyId].isRunning = false
      }
    },
    setBacktestError: (state, action: PayloadAction<{
      strategyId: string
      error: string
    }>) => {
      const { strategyId, error } = action.payload
      if (state.backtest[strategyId]) {
        state.backtest[strategyId].error = error
        state.backtest[strategyId].isRunning = false
      }
    },
  },
})

// Export actions
export const {
  // Basic CRUD
  setStrategies,
  setSelectedStrategy,
  addStrategy,
  updateStrategy,
  removeStrategy,

  // Editing
  startEditing,
  updateEditingStrategy,
  cancelEditing,
  saveEditingStrategy,

  // Cloning
  startCloning,
  updateClonedStrategy,
  cancelCloning,

  // Loading and errors
  setLoading,
  setError,
  clearError,

  // Filtering and sorting
  setFilters,
  clearFilters,
  setSorting,
  setPagination,

  // Execution
  startExecution,
  stopExecution,
  addExecutionRecord,

  // Parameters
  setStrategyParameters,
  updateParameter,
  resetParameters,

  // Backtesting
  startBacktest,
  setBacktestResults,
  setBacktestError,
} = strategySlice.actions

// Selectors
export const selectStrategies = (state: { strategy: StrategyState }) => state.strategy.strategies
export const selectSelectedStrategy = (state: { strategy: StrategyState }) => state.strategy.selectedStrategy
export const selectEditingStrategy = (state: { strategy: StrategyState }) => state.strategy.editingStrategy
export const selectClonedStrategy = (state: { strategy: StrategyState }) => state.strategy.clonedStrategy
export const selectStrategyLoading = (state: { strategy: StrategyState }) => state.strategy.isLoading
export const selectStrategyError = (state: { strategy: StrategyState }) => state.strategy.error
export const selectStrategyFilters = (state: { strategy: StrategyState }) => state.strategy.filters
export const selectStrategySorting = (state: { strategy: StrategyState }) => state.strategy.sorting
export const selectStrategyPagination = (state: { strategy: StrategyState }) => state.strategy.pagination
export const selectStrategyExecution = (state: { strategy: StrategyState }) => state.strategy.execution
export const selectStrategyParameters = (state: { strategy: StrategyState }) => state.strategy.parameters
export const selectStrategyBacktest = (state: { strategy: StrategyState }) => state.strategy.backtest

// Computed selectors
export const selectFilteredStrategies = (state: { strategy: StrategyState }) => {
  const { strategies, filters } = state.strategy
  return strategies.filter((strategy) => {
    // Status filter
    if (filters.status.length > 0 && !filters.status.includes(strategy.status)) {
      return false
    }

    // Category filter
    if (filters.category.length > 0 && !filters.category.includes(strategy.category)) {
      return false
    }

    // Risk level filter
    if (filters.riskLevel.length > 0 && !filters.riskLevel.includes(strategy.riskLevel)) {
      return false
    }

    // Search filter
    if (filters.search) {
      const searchLower = filters.search.toLowerCase()
      return (
        strategy.name.toLowerCase().includes(searchLower) ||
        strategy.description.toLowerCase().includes(searchLower) ||
        strategy.type.toLowerCase().includes(searchLower)
      )
    }

    return true
  })
}

export const selectActiveStrategies = (state: { strategy: StrategyState }) => {
  return state.strategy.strategies.filter((strategy) => strategy.status === 'active')
}

export const selectStrategiesByCategory = (state: { strategy: StrategyState }) => {
  const strategies = state.strategy.strategies
  const categories = strategies.reduce((acc, strategy) => {
    if (!acc[strategy.category]) {
      acc[strategy.category] = []
    }
    acc[strategy.category].push(strategy)
    return acc
  }, {} as Record<string, Strategy[]>)
  return categories
}
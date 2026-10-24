import { createSlice, PayloadAction, createAsyncThunk } from '@reduxjs/toolkit'
import {
  Strategy,
  StrategiesState,
  StrategyStatus,
  StrategyType,
  RiskLevel,
  StrategyFilters,
  StrategySorting,
  StrategyPagination,
  ExecutionLog,
  Position,
  Order,
  PerformanceMetrics,
  BacktestRequest,
  BacktestResult,
} from '../../types/strategy'

// Initial state
const initialState: StrategiesState = {
  items: [],
  selected: null,
  editing: null,
  loading: false,
  error: null,
  filters: {
    status: [],
    type: [],
    riskLevel: [],
    searchTerm: '',
  },
  sorting: {
    field: 'updatedAt',
    direction: 'desc',
  },
  pagination: {
    page: 1,
    pageSize: 20,
    total: 0,
  },
  execution: {
    running: {},
    logs: [],
    positions: [],
    orders: [],
    performance: {
      totalTrades: 0,
      winRate: 0,
      profitFactor: 0,
      sharpeRatio: 0,
      maxDrawdown: 0,
      totalPnl: 0,
      dailyPnl: [],
    },
  },
  backtest: {
    results: [],
    running: false,
    progress: 0,
    config: null,
  },
}

const strategiesSlice = createSlice({
  name: 'strategies',
  initialState,
  reducers: {
    // Strategy management
    setStrategies: (state, action: PayloadAction<Strategy[]>) => {
      state.items = action.payload
      state.pagination.total = action.payload.length
    },
    addStrategy: (state, action: PayloadAction<Strategy>) => {
      state.items.unshift(action.payload)
      state.pagination.total = state.items.length
    },
    updateStrategy: (state, action: PayloadAction<{ id: string; updates: Partial<Strategy> }>) => {
      const { id, updates } = action.payload
      const index = state.items.findIndex(s => s.id === id)
      if (index !== -1) {
        state.items[index] = { ...state.items[index], ...updates }
      }
    },
    deleteStrategy: (state, action: PayloadAction<string>) => {
      state.items = state.items.filter(s => s.id !== action.payload)
      state.pagination.total = state.items.length
    },

    // Selection and editing
    selectStrategy: (state, action: PayloadAction<string | null>) => {
      state.selected = action.payload
      state.editing = null
    },
    startEditing: (state, action: PayloadAction<string | null>) => {
      state.editing = action.payload
      if (action.payload) {
        const strategy = state.items.find(s => s.id === action.payload)
        if (strategy) {
          state.selected = action.payload
        }
      }
    },
    cancelEditing: (state) => {
      state.editing = null
    },
    saveEditing: (state, action: PayloadAction<Partial<Strategy>>) => {
      if (state.editing && state.selected) {
        const index = state.items.findIndex(s => s.id === state.selected)
        if (index !== -1) {
          state.items[index] = { ...state.items[index], ...action.payload }
        }
      }
      state.editing = null
    },

    // Status management
    updateStrategyStatus: (state, action: PayloadAction<{ id: string; status: StrategyStatus }>) => {
      const { id, status } = action.payload
      const strategy = state.items.find(s => s.id === id)
      if (strategy) {
        strategy.status = status
      }
    },

    // Filtering and sorting
    setFilters: (state, action: PayloadAction<Partial<StrategyFilters>>) => {
      state.filters = { ...state.filters, ...action.payload }
    },
    clearFilters: (state) => {
      state.filters = {
        status: [],
        type: [],
        riskLevel: [],
        searchTerm: '',
      }
    },
    setSorting: (state, action: PayloadAction<StrategySorting>) => {
      state.sorting = action.payload
    },
    setPagination: (state, action: PayloadAction<Partial<StrategyPagination>>) => {
      state.pagination = { ...state.pagination, ...action.payload }
    },

    // Loading and error states
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
    },
    clearError: (state) => {
      state.error = null
    },

    // Execution management
    setExecutionState: (state, action: PayloadAction<{ strategyId: string; running: boolean }>) => {
      const { strategyId, running } = action.payload
      state.execution.running[strategyId] = running
    },
    addExecutionLog: (state, action: PayloadAction<ExecutionLog>) => {
      state.execution.logs.unshift(action.payload)
      // Keep only last 1000 logs
      if (state.execution.logs.length > 1000) {
        state.execution.logs = state.execution.logs.slice(0, 1000)
      }
    },
    updateExecutionLogs: (state, action: PayloadAction<ExecutionLog[]>) => {
      state.execution.logs = action.payload
    },
    updatePositions: (state, action: PayloadAction<Position[]>) => {
      state.execution.positions = action.payload
    },
    updateOrders: (state, action: PayloadAction<Order[]>) => {
      state.execution.orders = action.payload
    },
    updatePerformance: (state, action: PayloadAction<Partial<PerformanceMetrics>>) => {
      state.execution.performance = { ...state.execution.performance, ...action.payload }
    },
    addDailyPnl: (state, action: PayloadAction<{ date: string; pnl: number }>) => {
      const existingIndex = state.execution.performance.dailyPnl.findIndex(
        d => d.date === action.payload.date
      )
      if (existingIndex !== -1) {
        state.execution.performance.dailyPnl[existingIndex].pnl = action.payload.pnl
      } else {
        state.execution.performance.dailyPnl.push(action.payload)
      }
    },

    // Backtest management
    startBacktest: (state, action: PayloadAction<BacktestRequest>) => {
      state.backtest.running = true
      state.backtest.progress = 0
      state.backtest.config = action.payload
    },
    updateBacktestProgress: (state, action: PayloadAction<number>) => {
      state.backtest.progress = action.payload
    },
    completeBacktest: (state, action: PayloadAction<BacktestResult>) => {
      state.backtest.running = false
      state.backtest.progress = 100
      state.backtest.results.unshift(action.payload)
    },
    stopBacktest: (state) => {
      state.backtest.running = false
      state.backtest.progress = 0
    },
    setBacktestResults: (state, action: PayloadAction<BacktestResult[]>) => {
      state.backtest.results = action.payload
    },
    clearBacktestResults: (state) => {
      state.backtest.results = []
    },
  },
})

// Export actions
export const {
  // Strategy management
  setStrategies,
  addStrategy,
  updateStrategy,
  deleteStrategy,

  // Selection and editing
  selectStrategy,
  startEditing,
  cancelEditing,
  saveEditing,

  // Status management
  updateStrategyStatus,

  // Filtering and sorting
  setFilters,
  clearFilters,
  setSorting,
  setPagination,

  // Loading and error states
  setLoading,
  setError,
  clearError,

  // Execution management
  setExecutionState,
  addExecutionLog,
  updateExecutionLogs,
  updatePositions,
  updateOrders,
  updatePerformance,
  addDailyPnl,

  // Backtest management
  startBacktest,
  updateBacktestProgress,
  completeBacktest,
  stopBacktest,
  setBacktestResults,
  clearBacktestResults,
} = strategiesSlice.actions

export default strategiesSlice.reducer

// Selectors
export const selectStrategies = (state: { persisted: { strategies: StrategiesState } }) => state.persisted.strategies.items
export const selectSelectedStrategy = (state: { persisted: { strategies: StrategiesState } }) =>
  state.persisted.strategies.items.find(s => s.id === state.persisted.strategies.selected)
export const selectEditingStrategy = (state: { persisted: { strategies: StrategiesState } }) =>
  state.persisted.strategies.editing ? state.persisted.strategies.items.find(s => s.id === state.persisted.strategies.editing) : null
export const selectStrategiesLoading = (state: { persisted: { strategies: StrategiesState } }) => state.persisted.strategies.loading
export const selectStrategiesError = (state: { persisted: { strategies: StrategiesState } }) => state.persisted.strategies.error
export const selectStrategyFilters = (state: { persisted: { strategies: StrategiesState } }) => state.persisted.strategies.filters
export const selectStrategySorting = (state: { persisted: { strategies: StrategiesState } }) => state.persisted.strategies.sorting
export const selectStrategyPagination = (state: { persisted: { strategies: StrategiesState } }) => state.persisted.strategies.pagination
export const selectExecutionState = (state: { persisted: { strategies: StrategiesState } }) => state.persisted.strategies.execution
export const selectBacktestState = (state: { persisted: { strategies: StrategiesState } }) => state.persisted.strategies.backtest

// Memoized selectors for better performance
export const selectFilteredStrategies = (state: { persisted: { strategies: StrategiesState } }) => {
  const { items, filters } = state.persisted.strategies

  if (!filters || Object.keys(filters).length === 0) {
    return items
  }

  return items.filter(strategy => {
    // Status filter
    if (filters.status && filters.status.length > 0) {
      if (!filters.status.includes(strategy.status)) {
        return false
      }
    }

    // Type filter
    if (filters.type && filters.type.length > 0) {
      if (!filters.type.includes(strategy.type)) {
        return false
      }
    }

    // Risk level filter
    if (filters.riskLevel && filters.riskLevel.length > 0) {
      if (!filters.riskLevel.includes(strategy.riskLevel)) {
        return false
      }
    }

    // Search term filter
    if (filters.searchTerm) {
      const term = filters.searchTerm.toLowerCase()
      const searchFields = [strategy.name, strategy.description, strategy.category].filter(Boolean)
      if (!searchFields.some(field => field.toLowerCase().includes(term))) {
        return false
      }
    }

    return true
  })
}

export const selectSortedStrategies = (state: { persisted: { strategies: StrategiesState } }) => {
  const filteredStrategies = selectFilteredStrategies(state)
  const { sorting } = state.persisted.strategies

  if (!sorting || !sorting.field) {
    return filteredStrategies
  }

  return [...filteredStrategies].sort((a, b) => {
    const { field, direction } = sorting
    const aValue = getNestedValue(a, field)
    const bValue = getNestedValue(b, field)

    if (aValue === bValue) return 0
    if (aValue === null || aValue === undefined) return direction === 'asc' ? -1 : 1
    if (bValue === null || bValue === undefined) return direction === 'asc' ? 1 : -1

    let comparison = 0
    if (typeof aValue === 'string' && typeof bValue === 'string') {
      comparison = aValue.localeCompare(bValue)
    } else {
      comparison = (aValue as number) - (bValue as number)
    }

    return direction === 'asc' ? comparison : -comparison
  })
}

export const selectPaginatedStrategies = (state: { persisted: { strategies: StrategiesState } }) => {
  const sortedStrategies = selectSortedStrategies(state)
  const { pagination } = state.persisted.strategies

  const startIndex = (pagination.page - 1) * pagination.pageSize
  const endIndex = startIndex + pagination.pageSize

  return {
    strategies: sortedStrategies.slice(startIndex, endIndex),
    startIndex,
    endIndex,
  }
}

// Helper function to get nested property value
function getNestedValue(obj: any, path: string): any {
  return path.split('.').reduce((current, key) => {
    return current && current[key] !== undefined ? current[key] : null
  }, obj)
}

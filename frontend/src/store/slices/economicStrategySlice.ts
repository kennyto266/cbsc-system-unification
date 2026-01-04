/**
 * Economic Strategy Redux Slice
 * 經濟策略 Redux 狀態管理
 */

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import { economicStrategyApi } from '../../services/economicStrategyApi'

// TypeScript type definitions
export interface EconomicStrategy {
  id: string
  name: string
  type: 'interest_rate_arbitrage' | 'economic_data_correlation' | 'multi_indicator_momentum' | 'volatility_based' | 'seasonal_patterns'
  status: 'active' | 'paused' | 'stopped' | 'error' | 'testing'
  description: string
  parameters: Record<string, any>
  indicators: string[]
  createdAt: string
  updatedAt: string
  lastRun?: string
  nextRun?: string
  performance?: {
    totalReturn: number
    winRate: number
    sharpeRatio: number
    maxDrawdown: number
    totalTrades: number
    profitableTrades: number
  }
  error?: string
  configuration?: {
    autoRestart: boolean
    riskLimits: {
      maxPositionSize: number
      maxDailyLoss: number
      maxDrawdown: number
    }
    executionSettings: {
      slippageTolerance: number
      executionDelay: number
      retryAttempts: number
    }
  }
}

export interface EconomicStrategyState {
  strategies: EconomicStrategy[]
  currentStrategy: EconomicStrategy | null
  loading: boolean
  error: string | null
  history: Record<string, any[]>
  performance: Record<string, any>
  filters: {
    type: string
    status: string
    search: string
  }
}

// Initial state
const initialState: EconomicStrategyState = {
  strategies: [],
  currentStrategy: null,
  loading: false,
  error: null,
  history: {},
  performance: {},
  filters: {
    type: 'all',
    status: 'all',
    search: ''
  }
}

// Async thunks for strategy CRUD operations
export const fetchAllStrategies = createAsyncThunk(
  'economicStrategy/fetchAll',
  async (_, { rejectWithValue }) => {
    try {
      const response = await economicStrategyApi.getEconomicStrategies()
      return response.data
    } catch (error) {
      if (error instanceof Error) {
        return rejectWithValue(error.message)
      }
      return rejectWithValue('Failed to fetch strategies')
    }
  }
)

export const fetchStrategyById = createAsyncThunk(
  'economicStrategy/fetchById',
  async (strategyId: string, { rejectWithValue }) => {
    try {
      const response = await economicStrategyApi.getEconomicStrategyById(strategyId)
      return response.data
    } catch (error) {
      if (error instanceof Error) {
        return rejectWithValue(error.message)
      }
      return rejectWithValue('Failed to fetch strategy')
    }
  }
)

export const createEconomicStrategy = createAsyncThunk(
  'economicStrategy/create',
  async (strategyData: any, { rejectWithValue }) => {
    try {
      const response = await economicStrategyApi.createEconomicStrategy(strategyData)
      return response.data
    } catch (error) {
      if (error instanceof Error) {
        return rejectWithValue(error.message)
      }
      return rejectWithValue('Failed to create strategy')
    }
  }
)

export const updateEconomicStrategy = createAsyncThunk(
  'economicStrategy/update',
  async ({ id, data }: { id: string; data: any }, { rejectWithValue }) => {
    try {
      const response = await economicStrategyApi.updateEconomicStrategy(id, data)
      return response.data
    } catch (error) {
      if (error instanceof Error) {
        return rejectWithValue(error.message)
      }
      return rejectWithValue('Failed to update strategy')
    }
  }
)

export const deleteEconomicStrategy = createAsyncThunk(
  'economicStrategy/delete',
  async (strategyId: string, { rejectWithValue }) => {
    try {
      await economicStrategyApi.deleteEconomicStrategy(strategyId)
      return strategyId
    } catch (error) {
      if (error instanceof Error) {
        return rejectWithValue(error.message)
      }
      return rejectWithValue('Failed to delete strategy')
    }
  }
)

// Async thunks for strategy control operations
export const startEconomicStrategy = createAsyncThunk(
  'economicStrategy/start',
  async ({ strategyId, params }: { strategyId: string; params?: any }, { rejectWithValue }) => {
    try {
      const response = await economicStrategyApi.startEconomicStrategy(strategyId, params || {})
      return response.data
    } catch (error) {
      if (error instanceof Error) {
        return rejectWithValue(error.message)
      }
      return rejectWithValue('Failed to start strategy')
    }
  }
)

export const stopEconomicStrategy = createAsyncThunk(
  'economicStrategy/stop',
  async (strategyId: string, { rejectWithValue }) => {
    try {
      const response = await economicStrategyApi.stopEconomicStrategy(strategyId)
      return response.data
    } catch (error) {
      if (error instanceof Error) {
        return rejectWithValue(error.message)
      }
      return rejectWithValue('Failed to stop strategy')
    }
  }
)

// Pause and resume not yet implemented in backend API
export const pauseEconomicStrategy = createAsyncThunk(
  'economicStrategy/pause',
  async (strategyId: string, { rejectWithValue }) => {
    try {
      // Simulate pause by stopping - backend doesn't have pause endpoint yet
      const response = await economicStrategyApi.stopEconomicStrategy(strategyId)
      return { ...response.data, status: 'paused' as const }
    } catch (error) {
      if (error instanceof Error) {
        return rejectWithValue(error.message)
      }
      return rejectWithValue('Failed to pause strategy')
    }
  }
)

export const resumeEconomicStrategy = createAsyncThunk(
  'economicStrategy/resume',
  async ({ strategyId, params }: { strategyId: string; params?: any }, { rejectWithValue }) => {
    try {
      // Resume by starting again - backend doesn't have resume endpoint yet
      const response = await economicStrategyApi.startEconomicStrategy(strategyId, params || {})
      return response.data
    } catch (error) {
      if (error instanceof Error) {
        return rejectWithValue(error.message)
      }
      return rejectWithValue('Failed to resume strategy')
    }
  }
)

export const fetchStrategyHistory = createAsyncThunk(
  'economicStrategy/fetchHistory',
  async ({ strategyId, params }: { strategyId: string; params?: any }, { rejectWithValue }) => {
    try {
      const response = await economicStrategyApi.getStrategySignals(strategyId, params)
      return { strategyId, history: response.data }
    } catch (error) {
      if (error instanceof Error) {
        return rejectWithValue(error.message)
      }
      return rejectWithValue('Failed to fetch strategy history')
    }
  }
)

export const fetchStrategyPerformance = createAsyncThunk(
  'economicStrategy/fetchPerformance',
  async ({ strategyId, params }: { strategyId: string; params?: any }, { rejectWithValue }) => {
    try {
      const response = await economicStrategyApi.getStrategyPerformance(strategyId, params)
      return { strategyId, performance: response.data }
    } catch (error) {
      if (error instanceof Error) {
        return rejectWithValue(error.message)
      }
      return rejectWithValue('Failed to fetch strategy performance')
    }
  }
)

// Slice
const economicStrategySlice = createSlice({
  name: 'economicStrategy',
  initialState,
  reducers: {
    setFilter: (
      state,
      action: PayloadAction<{
        type: 'type' | 'status' | 'search'
        value: string
      }>
    ) => {
      state.filters[action.payload.type] = action.payload.value
    },

    clearError: (state) => {
      state.error = null
    },

    clearCurrentStrategy: (state) => {
      state.currentStrategy = null
    },

    updateStrategyInList: (
      state,
      action: PayloadAction<{
        id: string
        updates: Partial<EconomicStrategy>
      }>
    ) => {
      const { id, updates } = action.payload
      const index = state.strategies.findIndex(strategy => strategy.id === id)
      if (index !== -1) {
        state.strategies[index] = { ...state.strategies[index], ...updates }
      }
    },

    setStrategies: (
      state,
      action: PayloadAction<EconomicStrategy[]>
    ) => {
      state.strategies = action.payload
    }
  },

  extraReducers: (builder) => {
    // fetchAllStrategies
    builder
      .addCase(fetchAllStrategies.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchAllStrategies.fulfilled, (state, action) => {
        state.loading = false
        state.strategies = action.payload
        state.error = null
      })
      .addCase(fetchAllStrategies.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })

    // fetchStrategyById
    builder
      .addCase(fetchStrategyById.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchStrategyById.fulfilled, (state, action) => {
        state.loading = false
        state.currentStrategy = action.payload
        state.error = null
      })
      .addCase(fetchStrategyById.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })

    // createEconomicStrategy
    builder
      .addCase(createEconomicStrategy.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(createEconomicStrategy.fulfilled, (state, action) => {
        state.loading = false
        state.strategies.push(action.payload)
        state.error = null
      })
      .addCase(createEconomicStrategy.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })

    // updateEconomicStrategy
    builder
      .addCase(updateEconomicStrategy.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(updateEconomicStrategy.fulfilled, (state, action) => {
        state.loading = false
        const index = state.strategies.findIndex(strategy => strategy.id === action.payload.id)
        if (index !== -1) {
          state.strategies[index] = action.payload
        }
        if (state.currentStrategy?.id === action.payload.id) {
          state.currentStrategy = action.payload
        }
        state.error = null
      })
      .addCase(updateEconomicStrategy.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })

    // deleteEconomicStrategy
    builder
      .addCase(deleteEconomicStrategy.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(deleteEconomicStrategy.fulfilled, (state, action) => {
        state.loading = false
        state.strategies = state.strategies.filter(strategy => strategy.id !== action.payload)
        if (state.currentStrategy?.id === action.payload) {
          state.currentStrategy = null
        }
        state.error = null
      })
      .addCase(deleteEconomicStrategy.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })

    // Control operations (start, stop, pause, resume)
    builder
      .addCase(startEconomicStrategy.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(startEconomicStrategy.fulfilled, (state, action) => {
        state.loading = false
        const index = state.strategies.findIndex(s => s.id === action.payload.id)
        if (index !== -1) {
          state.strategies[index] = action.payload
        }
        if (state.currentStrategy?.id === action.payload.id) {
          state.currentStrategy = action.payload
        }
        state.error = null
      })
      .addCase(startEconomicStrategy.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })

    builder
      .addCase(stopEconomicStrategy.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(stopEconomicStrategy.fulfilled, (state, action) => {
        state.loading = false
        const index = state.strategies.findIndex(s => s.id === action.payload.id)
        if (index !== -1) {
          state.strategies[index] = action.payload
        }
        if (state.currentStrategy?.id === action.payload.id) {
          state.currentStrategy = action.payload
        }
        state.error = null
      })
      .addCase(stopEconomicStrategy.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })

    builder
      .addCase(pauseEconomicStrategy.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(pauseEconomicStrategy.fulfilled, (state, action) => {
        state.loading = false
        const index = state.strategies.findIndex(s => s.id === action.payload.id)
        if (index !== -1) {
          state.strategies[index] = action.payload
        }
        if (state.currentStrategy?.id === action.payload.id) {
          state.currentStrategy = action.payload
        }
        state.error = null
      })
      .addCase(pauseEconomicStrategy.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })

    builder
      .addCase(resumeEconomicStrategy.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(resumeEconomicStrategy.fulfilled, (state, action) => {
        state.loading = false
        const index = state.strategies.findIndex(s => s.id === action.payload.id)
        if (index !== -1) {
          state.strategies[index] = action.payload
        }
        if (state.currentStrategy?.id === action.payload.id) {
          state.currentStrategy = action.payload
        }
        state.error = null
      })
      .addCase(resumeEconomicStrategy.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })

    // fetchStrategyHistory
    builder
      .addCase(fetchStrategyHistory.fulfilled, (state, action) => {
        const { strategyId, history } = action.payload
        state.history[strategyId] = history
      })
      .addCase(fetchStrategyHistory.rejected, (state, action) => {
        state.error = action.payload as string
      })

    // fetchStrategyPerformance
    builder
      .addCase(fetchStrategyPerformance.fulfilled, (state, action) => {
        const { strategyId, performance } = action.payload
        state.performance[strategyId] = performance
      })
      .addCase(fetchStrategyPerformance.rejected, (state, action) => {
        state.error = action.payload as string
      })
  }
})

// Actions
export const {
  setFilter,
  clearError,
  clearCurrentStrategy,
  updateStrategyInList,
  setStrategies
} = economicStrategySlice.actions

// Selectors
export const selectEconomicStrategies = (state: { economicStrategy: EconomicStrategyState }) =>
  state.economicStrategy.strategies

export const selectEconomicStrategyById = (state: { economicStrategy: EconomicStrategyState }) =>
  state.economicStrategy.currentStrategy

export const selectEconomicStrategyLoading = (state: { economicStrategy: EconomicStrategyState }) =>
  state.economicStrategy.loading

export const selectEconomicStrategyError = (state: { economicStrategy: EconomicStrategyState }) =>
  state.economicStrategy.error

export const selectEconomicStrategyFilters = (state: { economicStrategy: EconomicStrategyState }) =>
  state.economicStrategy.filters

export const selectEconomicStrategyHistory = (state: { economicStrategy: EconomicStrategyState }) =>
  state.economicStrategy.history

export const selectEconomicStrategyPerformance = (state: { economicStrategy: EconomicStrategyState }) =>
  state.economicStrategy.performance

// Helper selectors
export const getStrategyById = (id: string) => (state: { economicStrategy: EconomicStrategyState }) =>
  state.economicStrategy.strategies.find(strategy => strategy.id === id)

export const getAllStrategies = (state: { economicStrategy: EconomicStrategyState }) =>
  state.economicStrategy.strategies

export const getActiveStrategies = (state: { economicStrategy: EconomicStrategyState }) =>
  state.economicStrategy.strategies.filter(strategy => strategy.status === 'active')

export const getStrategiesByType = (type: string) => (state: { economicStrategy: EconomicStrategyState }) =>
  state.economicStrategy.strategies.filter(strategy => strategy.type === type)

export const getStrategiesByStatus = (status: string) => (state: { economicStrategy: EconomicStrategyState }) =>
  state.economicStrategy.strategies.filter(strategy => strategy.status === status)

// Reducer
export default economicStrategySlice.reducer

// Export types
export type {
  EconomicStrategy,
  EconomicStrategyState
}
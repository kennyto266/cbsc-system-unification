import { createSlice, PayloadAction } from '@reduxjs/toolkit'

interface Strategy {
  id: string
  name: string
  description: string
  status: 'active' | 'inactive' | 'testing'
  createdAt: string
  updatedAt: string
  parameters: Record<string, any>
  performance: {
    totalReturn: number
    sharpeRatio: number
    maxDrawdown: number
    winRate: number
  }
}

interface StrategyState {
  strategies: Strategy[]
  selectedStrategy: Strategy | null
  isLoading: boolean
  error: string | null
}

const initialState: StrategyState = {
  strategies: [],
  selectedStrategy: null,
  isLoading: false,
  error: null,
}

export const strategySlice = createSlice({
  name: 'strategy',
  initialState,
  reducers: {
    setStrategies: (state, action: PayloadAction<Strategy[]>) => {
      state.strategies = action.payload
    },
    setSelectedStrategy: (state, action: PayloadAction<Strategy | null>) => {
      state.selectedStrategy = action.payload
    },
    addStrategy: (state, action: PayloadAction<Strategy>) => {
      state.strategies.push(action.payload)
    },
    updateStrategy: (state, action: PayloadAction<Strategy>) => {
      const index = state.strategies.findIndex((s) => s.id === action.payload.id)
      if (index !== -1) {
        state.strategies[index] = action.payload
      }
    },
    removeStrategy: (state, action: PayloadAction<string>) => {
      state.strategies = state.strategies.filter((s) => s.id !== action.payload)
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
    },
  },
})

export const {
  setStrategies,
  setSelectedStrategy,
  addStrategy,
  updateStrategy,
  removeStrategy,
  setLoading,
  setError,
} = strategySlice.actions
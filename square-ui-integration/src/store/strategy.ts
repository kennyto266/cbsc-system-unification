import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import type { Strategy, StrategyState } from '@/types/strategy'

const initialState: StrategyState = {
  strategies: [],
  activeStrategies: [],
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
    addStrategy: (state, action: PayloadAction<Strategy>) => {
      state.strategies.push(action.payload)
    },
    updateStrategy: (state, action: PayloadAction<{ id: string; data: Partial<Strategy> }>) => {
      const { id, data } = action.payload
      const index = state.strategies.findIndex(s => s.id === id)
      if (index !== -1) {
        state.strategies[index] = { ...state.strategies[index], ...data }
      }
    },
    deleteStrategy: (state, action: PayloadAction<string>) => {
      state.strategies = state.strategies.filter(s => s.id !== action.payload)
    },
    setActiveStrategies: (state, action: PayloadAction<string[]>) => {
      state.activeStrategies = action.payload
    },
    toggleStrategyActive: (state, action: PayloadAction<string>) => {
      const strategy = state.strategies.find(s => s.id === action.payload)
      if (strategy) {
        strategy.isActive = !strategy.isActive
      }
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
  addStrategy,
  updateStrategy,
  deleteStrategy,
  setActiveStrategies,
  toggleStrategyActive,
  setLoading,
  setError,
} = strategySlice.actions

export { strategySlice as default }
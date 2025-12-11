import { createSlice, PayloadAction } from '@reduxjs/toolkit'

interface Strategy {
  id: string
  name: string
  description?: string
  status: 'active' | 'inactive' | 'testing'
  createdAt: string
  updatedAt: string
}

interface StrategiesState {
  strategies: Strategy[]
  loading: boolean
  error: string | null
}

const initialState: StrategiesState = {
  strategies: [],
  loading: false,
  error: null,
}

const strategiesSlice = createSlice({
  name: 'strategies',
  initialState,
  reducers: {
    setStrategies: (state, action: PayloadAction<Strategy[]>) => {
      state.strategies = action.payload
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
    },
  },
})

export const { setStrategies, setLoading, setError } = strategiesSlice.actions
export default strategiesSlice.reducer

/**
 * Economic Data Redux Slice
 * 經濟數據 Redux 狀態管理
 */

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import { economicDataApi } from '../../services/economicDataApi'

// TypeScript type definitions
export interface HiborData {
  date: string
  rate: number
}

export interface GdpData {
  quarter: string
  gdp_growth: number
}

export interface PmiData {
  month: string
  pmi: number
}

export interface VisitorData {
  month: string
  visitors: number
}

export interface UnemploymentData {
  month: string
  rate: number
}

export interface EconomicDataState {
  data: {
    hibor: HiborData[]
    gdp: GdpData[]
    pmi: PmiData[]
    visitors: VisitorData[]
    unemployment: UnemploymentData[]
  }
  loading: boolean
  error: string | null
  filters: {
    indicators: string[]
    dateRange: {
      start: string
      end: string
    }
  }
  lastUpdated: string | null
  cacheStatus: {
    [key: string]: {
      lastFetch: number
      expiresAt: number
    }
  }
}

// Initial state
const initialState: EconomicDataState = {
  data: {
    hibor: [],
    gdp: [],
    pmi: [],
    visitors: [],
    unemployment: [],
  },
  loading: false,
  error: null,
  filters: {
    indicators: ['hibor', 'gdp', 'pmi', 'visitors', 'unemployment'],
    dateRange: {
      start: '',
      end: '',
    },
  },
  lastUpdated: null,
  cacheStatus: {},
}

// Async thunks
export const fetchEconomicIndicators = createAsyncThunk(
  'economicData/fetchIndicators',
  async (
    { type, params }: { type: keyof typeof initialState.data; params: any },
    { rejectWithValue }
  ) => {
    try {
      let response
      switch (type) {
        case 'hibor':
          response = await economicDataApi.getHiborData(params)
          break
        case 'gdp':
          response = await economicDataApi.getGdpData(params)
          break
        case 'pmi':
          response = await economicDataApi.getPmiData(params)
          break
        case 'visitors':
          response = await economicDataApi.getVisitorData(params)
          break
        case 'unemployment':
          response = await economicDataApi.getUnemploymentData(params)
          break
        default:
          throw new Error(`Unknown indicator type: ${type}`)
      }

      return {
        type,
        data: response.data,
      }
    } catch (error) {
      if (error instanceof Error) {
        return rejectWithValue(error.message)
      }
      return rejectWithValue('Unknown error occurred')
    }
  }
)

export const fetchAllEconomicIndicators = createAsyncThunk(
  'economicData/fetchAllIndicators',
  async (
    { dateRange }: { dateRange: { start: string; end: string } },
    { rejectWithValue }
  ) => {
    try {
      const response = await economicDataApi.getAllEconomicIndicators({
        dateRange,
      })
      return response
    } catch (error) {
      if (error instanceof Error) {
        return rejectWithValue(error.message)
      }
      return rejectWithValue('Unknown error occurred')
    }
  }
)

// Slice
const economicDataSlice = createSlice({
  name: 'economicData',
  initialState,
  reducers: {
    setFilter: (
      state,
      action: PayloadAction<{
        indicators?: string[]
        dateRange?: { start: string; end: string }
      }>
    ) => {
      if (action.payload.indicators) {
        state.filters.indicators = action.payload.indicators
      }
      if (action.payload.dateRange) {
        state.filters.dateRange = action.payload.dateRange
      }
    },

    setTimeRange: (
      state,
      action: PayloadAction<{ start: string; end: string }>
    ) => {
      state.filters.dateRange = action.payload
    },

    updateData: (
      state,
      action: PayloadAction<{
        type: keyof typeof initialState.data
        data: any[]
      }>
    ) => {
      state.data[action.payload.type] = action.payload.data as any
      state.lastUpdated = new Date().toISOString()
    },

    clearCache: (state) => {
      state.data = initialState.data
      state.error = null
      state.lastUpdated = null
      state.cacheStatus = {}
    },

    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload
    },

    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
    },

    updateCacheStatus: (
      state,
      action: PayloadAction<{
        key: string
        lastFetch: number
        expiresAt: number
      }>
    ) => {
      state.cacheStatus[action.payload.key] = {
        lastFetch: action.payload.lastFetch,
        expiresAt: action.payload.expiresAt,
      }
    },

    clearExpiredCache: (state) => {
      const now = Date.now()
      Object.keys(state.cacheStatus).forEach((key) => {
        if (state.cacheStatus[key].expiresAt < now) {
          delete state.cacheStatus[key]
        }
      })
    },
  },

  extraReducers: (builder) => {
    builder
      // fetchEconomicIndicators
      .addCase(fetchEconomicIndicators.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchEconomicIndicators.fulfilled, (state, action) => {
        state.loading = false
        state.data[action.payload.type] = action.payload.data as any
        state.lastUpdated = new Date().toISOString()
        state.error = null
      })
      .addCase(fetchEconomicIndicators.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })

      // fetchAllEconomicIndicators
      .addCase(fetchAllEconomicIndicators.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchAllEconomicIndicators.fulfilled, (state, action) => {
        state.loading = false
        state.data = action.payload as any
        state.lastUpdated = new Date().toISOString()
        state.error = null
      })
      .addCase(fetchAllEconomicIndicators.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })
  },
})

// Actions
export const {
  setFilter,
  setTimeRange,
  updateData,
  clearCache,
  setLoading,
  setError,
  updateCacheStatus,
  clearExpiredCache,
} = economicDataSlice.actions

// Selectors
export const selectEconomicData = (state: { economicData: EconomicDataState }) =>
  state.economicData.data

export const selectEconomicDataLoading = (state: { economicData: EconomicDataState }) =>
  state.economicData.loading

export const selectEconomicDataError = (state: { economicData: EconomicDataState }) =>
  state.economicData.error

export const selectEconomicDataFilters = (state: { economicData: EconomicDataState }) =>
  state.economicData.filters

export const selectFilteredEconomicData = (state: { economicData: EconomicDataState }) => {
  const { data, filters } = state.economicData
  const filtered: any = {}

  filters.indicators.forEach((indicator) => {
    if (data[indicator as keyof typeof data]) {
      filtered[indicator] = data[indicator as keyof typeof data]
    }
  })

  return filtered
}

export const selectLastUpdated = (state: { economicData: EconomicDataState }) =>
  state.economicData.lastUpdated

export const selectCacheStatus = (state: { economicData: EconomicDataState }) =>
  state.economicData.cacheStatus

// Helper selectors for specific indicators
export const selectHiborData = (state: { economicData: EconomicDataState }) =>
  state.economicData.data.hibor

export const selectGdpData = (state: { economicData: EconomicDataState }) =>
  state.economicData.data.gdp

export const selectPmiData = (state: { economicData: EconomicDataState }) =>
  state.economicData.data.pmi

export const selectVisitorData = (state: { economicData: EconomicDataState }) =>
  state.economicData.data.visitors

export const selectUnemploymentData = (state: { economicData: EconomicDataState }) =>
  state.economicData.data.unemployment

// Reducer
export default economicDataSlice.reducer
export const economicDataReducer = economicDataSlice.reducer

// Export types
export type {
  HiborData,
  GdpData,
  PmiData,
  VisitorData,
  UnemploymentData,
  EconomicDataState,
}
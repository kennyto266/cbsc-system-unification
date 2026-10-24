import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import {
  TechnicalIndicator,
  IndicatorConfiguration,
  IndicatorGroup,
  IndicatorPerformance,
  IndicatorLibraryState,
  IndicatorSearchFilter,
  IndicatorType,
  IndicatorCategory
} from '../../types/technical-indicators'
import { ALL_TECHNICAL_INDICATORS, POPULAR_COMBINATIONS } from '../../data/technical-indicators-library'

// Async thunks
export const fetchIndicators = createAsyncThunk(
  'technicalIndicators/fetchIndicators',
  async () => {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 500))
    return ALL_TECHNICAL_INDICATORS
  }
)

export const fetchUserConfigurations = createAsyncThunk(
  'technicalIndicators/fetchConfigurations',
  async (userId: string) => {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 300))
    return [] // Return empty for now
  }
)

export const saveConfiguration = createAsyncThunk(
  'technicalIndicators/saveConfiguration',
  async (config: IndicatorConfiguration) => {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 500))
    return config
  }
)

export const fetchIndicatorPerformance = createAsyncThunk(
  'technicalIndicators/fetchPerformance',
  async ({ indicatorId, symbol, timeframe }: {
    indicatorId: string
    symbol: string
    timeframe: string
  }) => {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 400))
    // Return mock performance data
    return {
      indicatorId,
      symbol,
      timeframe,
      period: {
        start: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString(),
        end: new Date().toISOString()
      },
      signals: [],
      statistics: {
        totalSignals: 0,
        successRate: 0,
        profitFactor: 0,
        maxDrawdown: 0,
        sharpeRatio: 0,
        averageHoldTime: 0
      }
    } as IndicatorPerformance
  }
)

const initialState: IndicatorLibraryState = {
  indicators: [],
  groups: [],
  configurations: [],
  performance: [],
  searchFilter: {},
  selectedIndicator: null,
  isLoading: false,
  error: null
}

const technicalIndicatorsSlice = createSlice({
  name: 'technicalIndicators',
  initialState,
  reducers: {
    // Search and filter actions
    setSearchFilter: (state, action: PayloadAction<Partial<IndicatorSearchFilter>>) => {
      state.searchFilter = { ...state.searchFilter, ...action.payload }
    },
    clearSearchFilter: (state) => {
      state.searchFilter = {}
    },

    // Indicator selection
    selectIndicator: (state, action: PayloadAction<TechnicalIndicator>) => {
      state.selectedIndicator = action.payload
    },
    clearSelectedIndicator: (state) => {
      state.selectedIndicator = null
    },

    // Favorite indicators
    toggleFavorite: (state, action: PayloadAction<string>) => {
      const indicator = state.indicators.find(ind => ind.id === action.payload)
      if (indicator) {
        indicator.favorite = !indicator.favorite
      }
    },

    // Configuration actions
    addConfiguration: (state, action: PayloadAction<IndicatorConfiguration>) => {
      state.configurations.push(action.payload)
    },
    updateConfiguration: (state, action: PayloadAction<IndicatorConfiguration>) => {
      const index = state.configurations.findIndex(
        config => config.id === action.payload.id
      )
      if (index !== -1) {
        state.configurations[index] = action.payload
      }
    },
    deleteConfiguration: (state, action: PayloadAction<string>) => {
      state.configurations = state.configurations.filter(
        config => config.id !== action.payload
      )
    },
    setActiveConfiguration: (state, action: PayloadAction<string>) => {
      // This could be used to set the active configuration for the panel
    },

    // Group actions
    createGroup: (state, action: PayloadAction<IndicatorGroup>) => {
      state.groups.push(action.payload)
    },
    updateGroup: (state, action: PayloadAction<IndicatorGroup>) => {
      const index = state.groups.findIndex(group => group.id === action.payload.id)
      if (index !== -1) {
        state.groups[index] = action.payload
      }
    },
    deleteGroup: (state, action: PayloadAction<string>) => {
      state.groups = state.groups.filter(group => group.id !== action.payload)
    },

    // Custom indicator actions
    createCustomIndicator: (state, action: PayloadAction<TechnicalIndicator>) => {
      const customIndicator = {
        ...action.payload,
        id: `custom-${Date.now()}`,
        custom: true
      }
      state.indicators.push(customIndicator)
    },
    updateCustomIndicator: (state, action: PayloadAction<TechnicalIndicator>) => {
      const index = state.indicators.findIndex(ind => ind.id === action.payload.id)
      if (index !== -1 && state.indicators[index].custom) {
        state.indicators[index] = action.payload
      }
    },
    deleteCustomIndicator: (state, action: PayloadAction<string>) => {
      const indicator = state.indicators.find(ind => ind.id === action.payload)
      if (indicator && indicator.custom) {
        state.indicators = state.indicators.filter(ind => ind.id !== action.payload)
      }
    },

    // Performance actions
    clearPerformance: (state) => {
      state.performance = []
    },

    // Bulk actions
    importConfigurations: (state, action: PayloadAction<IndicatorConfiguration[]>) => {
      state.configurations.push(...action.payload)
    },
    exportConfigurations: (state, action: PayloadAction<string[]>) => {
      // This would trigger an export action
    }
  },
  extraReducers: (builder) => {
    // Fetch indicators
    builder
      .addCase(fetchIndicators.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchIndicators.fulfilled, (state, action) => {
        state.isLoading = false
        state.indicators = action.payload
      })
      .addCase(fetchIndicators.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.error.message || 'Failed to fetch indicators'
      })

    // Fetch configurations
    builder
      .addCase(fetchUserConfigurations.pending, (state) => {
        state.isLoading = true
      })
      .addCase(fetchUserConfigurations.fulfilled, (state, action) => {
        state.isLoading = false
        state.configurations = action.payload
      })
      .addCase(fetchUserConfigurations.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.error.message || 'Failed to fetch configurations'
      })

    // Save configuration
    builder
      .addCase(saveConfiguration.pending, (state) => {
        state.isLoading = true
      })
      .addCase(saveConfiguration.fulfilled, (state, action) => {
        state.isLoading = false
        const index = state.configurations.findIndex(
          config => config.id === action.payload.id
        )
        if (index !== -1) {
          state.configurations[index] = action.payload
        } else {
          state.configurations.push(action.payload)
        }
      })
      .addCase(saveConfiguration.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.error.message || 'Failed to save configuration'
      })

    // Fetch performance
    builder
      .addCase(fetchIndicatorPerformance.pending, (state) => {
        state.isLoading = true
      })
      .addCase(fetchIndicatorPerformance.fulfilled, (state, action) => {
        state.isLoading = false
        const index = state.performance.findIndex(
          perf => perf.indicatorId === action.payload.indicatorId
        )
        if (index !== -1) {
          state.performance[index] = action.payload
        } else {
          state.performance.push(action.payload)
        }
      })
      .addCase(fetchIndicatorPerformance.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.error.message || 'Failed to fetch performance data'
      })
  }
})

export const {
  setSearchFilter,
  clearSearchFilter,
  selectIndicator,
  clearSelectedIndicator,
  toggleFavorite,
  addConfiguration,
  updateConfiguration,
  deleteConfiguration,
  setActiveConfiguration,
  createGroup,
  updateGroup,
  deleteGroup,
  createCustomIndicator,
  updateCustomIndicator,
  deleteCustomIndicator,
  clearPerformance,
  importConfigurations,
  exportConfigurations
} = technicalIndicatorsSlice.actions

// Selectors
export const selectAllIndicators = (state: { technicalIndicators: IndicatorLibraryState }) =>
  state.technicalIndicators.indicators

export const selectFilteredIndicators = (state: { technicalIndicators: IndicatorLibraryState }) => {
  const { indicators, searchFilter } = state.technicalIndicators

  return indicators.filter(indicator => {
    // Category filter
    if (searchFilter.category && indicator.category !== searchFilter.category) {
      return false
    }

    // Type filter
    if (searchFilter.type && indicator.type !== searchFilter.type) {
      return false
    }

    // Favorite filter
    if (searchFilter.favorite !== undefined && indicator.favorite !== searchFilter.favorite) {
      return false
    }

    // Custom filter
    if (searchFilter.custom !== undefined && indicator.custom !== searchFilter.custom) {
      return false
    }

    // Search term
    if (searchFilter.search) {
      const searchTerm = searchFilter.search.toLowerCase()
      const matchesName = indicator.name.toLowerCase().includes(searchTerm)
      const matchesDescription = indicator.description.toLowerCase().includes(searchTerm)
      const matchesTags = indicator.tags.some(tag => tag.toLowerCase().includes(searchTerm))

      if (!matchesName && !matchesDescription && !matchesTags) {
        return false
      }
    }

    // Tags filter
    if (searchFilter.tags && searchFilter.tags.length > 0) {
      const hasMatchingTag = searchFilter.tags.some(tag =>
        indicator.tags.includes(tag)
      )
      if (!hasMatchingTag) {
        return false
      }
    }

    return true
  })
}

export const selectIndicatorsByCategory = (state: { technicalIndicators: IndicatorLibraryState }) => {
  const { indicators } = state.technicalIndicators
  const grouped: Record<IndicatorCategory, TechnicalIndicator[]> = {} as any

  indicators.forEach(indicator => {
    if (!grouped[indicator.category]) {
      grouped[indicator.category] = []
    }
    grouped[indicator.category].push(indicator)
  })

  return grouped
}

export const selectFavoriteIndicators = (state: { technicalIndicators: IndicatorLibraryState }) =>
  state.technicalIndicators.indicators.filter(ind => ind.favorite)

export const selectCustomIndicators = (state: { technicalIndicators: IndicatorLibraryState }) =>
  state.technicalIndicators.indicators.filter(ind => ind.custom)

export const selectConfigurationsByUser = (userId: string) =>
  (state: { technicalIndicators: IndicatorLibraryState }) =>
    state.technicalIndicators.configurations.filter(config => config.userId === userId)

export const selectPerformanceByIndicator = (indicatorId: string) =>
  (state: { technicalIndicators: IndicatorLibraryState }) =>
    state.technicalIndicators.performance.find(perf => perf.indicatorId === indicatorId)

export const selectIsLoading = (state: { technicalIndicators: IndicatorLibraryState }) =>
  state.technicalIndicators.isLoading

export const selectError = (state: { technicalIndicators: IndicatorLibraryState }) =>
  state.technicalIndicators.error

export default technicalIndicatorsSlice.reducer
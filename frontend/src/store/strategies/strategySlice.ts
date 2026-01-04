/**
 * Strategy Management Redux Slice
 * 策略管理 Redux Slice
 */

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import {
  Strategy,
  StrategyConfig,
  StrategyCreateRequest,
  StrategyUpdateRequest,
  StrategyConfigCreateRequest,
  StrategyConfigUpdateRequest,
  PaginatedResponse,
  PerformanceMetricsResponse,
  StrategyType,
  RiskTolerance,
  StrategyFilter,
  StrategyListOptions
} from '../../types/strategyTypes';

import { strategyAPI } from '../../services/strategyManagementAPI';

/**
 * Async thunks for strategy operations
 * 策略操作的異步 thunks
 */

// Fetch strategies with pagination and filtering
export const fetchStrategies = createAsyncThunk(
  'strategies/fetchStrategies',
  async (options: StrategyListOptions = {}) => {
    const response = await strategyAPI.getStrategies(options);
    return response;
  }
);

// Fetch single strategy
export const fetchStrategy = createAsyncThunk(
  'strategies/fetchStrategy',
  async (strategyId: string) => {
    const response = await strategyAPI.getStrategy(strategyId);
    return response;
  }
);

// Create new strategy
export const createStrategy = createAsyncThunk(
  'strategies/createStrategy',
  async (strategyData: StrategyCreateRequest) => {
    const response = await strategyAPI.createStrategy(strategyData);
    return response;
  }
);

// Update strategy
export const updateStrategy = createAsyncThunk(
  'strategies/updateStrategy',
  async ({ id, data }: { id: string; data: StrategyUpdateRequest }) => {
    const response = await strategyAPI.updateStrategy(id, data);
    return response;
  }
);

// Delete strategy
export const deleteStrategy = createAsyncThunk(
  'strategies/deleteStrategy',
  async (strategyId: string) => {
    await strategyAPI.deleteStrategy(strategyId);
    return strategyId;
  }
);

// Fetch strategy configurations
export const fetchStrategyConfigs = createAsyncThunk(
  'strategies/fetchConfigs',
  async ({ strategyId, ...params }: { strategyId: string; [key: string]: any }) => {
    const response = await strategyAPI.getStrategyConfigs({ strategy_id: strategyId, ...params });
    return response;
  }
);

// Create strategy configuration
export const createStrategyConfig = createAsyncThunk(
  'strategies/createConfig',
  async ({ strategyId, configData }: { strategyId: string; configData: StrategyConfigCreateRequest }) => {
    const response = await strategyAPI.createStrategyConfig(strategyId, configData);
    return response;
  }
);

// Update strategy configuration
export const updateStrategyConfig = createAsyncThunk(
  'strategies/updateConfig',
  async ({
    strategyId,
    configId,
    updateData
  }: {
    strategyId: string;
    configId: string;
    updateData: StrategyConfigUpdateRequest
  }) => {
    const response = await strategyAPI.updateStrategyConfig(strategyId, configId, updateData);
    return response;
  }
);

// Delete strategy configuration
export const deleteStrategyConfig = createAsyncThunk(
  'strategies/deleteConfig',
  async ({ strategyId, configId }: { strategyId: string; configId: string }) => {
    await strategyAPI.deleteStrategyConfig(strategyId, configId);
    return { strategyId, configId };
  }
);

// Fetch strategy performance
export const fetchStrategyPerformance = createAsyncThunk(
  'strategies/fetchPerformance',
  async ({
    strategyId,
    timeRange,
    startDate,
    endDate
  }: {
    strategyId: string;
    timeRange?: string;
    startDate?: string;
    endDate?: string
  }) => {
    const params: any = {};
    if (timeRange) params.time_range = timeRange;
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;

    const response = await strategyAPI.getStrategyPerformance(strategyId, params);
    return response;
  }
);

// Execute strategy
export const executeStrategy = createAsyncThunk(
  'strategies/execute',
  async ({ strategyId, executionRequest }: { strategyId: string; executionRequest: any }) => {
    const response = await strategyAPI.executeStrategy(strategyId, executionRequest);
    return response;
  }
);

// Get execution status
export const getExecutionStatus = createAsyncThunk(
  'strategies/getExecutionStatus',
  async ({ strategyId, executionId }: { strategyId: string; executionId: string }) => {
    const response = await strategyAPI.getExecutionStatus(strategyId, executionId);
    return response;
  }
);

// Stop execution
export const stopExecution = createAsyncThunk(
  'strategies/stopExecution',
  async ({ strategyId, executionId }: { strategyId: string; executionId: string }) => {
    const response = await strategyAPI.stopExecution(strategyId, executionId);
    return response;
  }
);

// Batch operations
export const batchOperation = createAsyncThunk(
  'strategies/batchOperation',
  async ({ operation, strategyIds }: { operation: 'delete' | 'activate' | 'deactivate'; strategyIds: string[] }) => {
    const response = await strategyAPI.batchOperation(operation, strategyIds);
    return response;
  }
);

/**
 * State interface
 * 狀態接口
 */
interface StrategiesState {
  // Strategies data
  strategies: Strategy[];
  currentStrategy: Strategy | null;
  strategiesPagination: {
    page: number;
    pageSize: number;
    total: number;
    pages: number;
    hasNext: boolean;
    hasPrev: boolean;
  };

  // Strategy configurations
  configs: StrategyConfig[];
  configsPagination: {
    page: number;
    pageSize: number;
    total: number;
    pages: number;
    hasNext: boolean;
    hasPrev: boolean;
  };

  // Performance data
  performance: PerformanceMetricsResponse | null;
  performanceLoading: boolean;

  // Execution data
  executions: Record<string, any>;
  executionStatuses: Record<string, any>;

  // UI state
  loading: boolean;
  error: string | null;
  filter: StrategyFilter;
  selectedStrategies: string[];

  // Strategy types and categories
  strategyTypes: any[];
  riskTolerances: any[];
  categories: any[];
}

/**
 * Initial state
 * 初始狀態
 */
const initialState: StrategiesState = {
  strategies: [],
  currentStrategy: null,
  strategiesPagination: {
    page: 1,
    pageSize: 20,
    total: 0,
    pages: 0,
    hasNext: false,
    hasPrev: false,
  },

  configs: [],
  configsPagination: {
    page: 1,
    pageSize: 20,
    total: 0,
    pages: 0,
    hasNext: false,
    hasPrev: false,
  },

  performance: null,
  performanceLoading: false,

  executions: {},
  executionStatuses: {},

  loading: false,
  error: null,
  filter: {},
  selectedStrategies: [],

  strategyTypes: [],
  riskTolerances: [],
  categories: [],
};

/**
 * Strategies slice
 * 策略 slice
 */
const strategySlice = createSlice({
  name: 'strategies',
  initialState,
  reducers: {
    // Clear error
    clearError: (state) => {
      state.error = null;
    },

    // Set filter
    setFilter: (state, action: PayloadAction<StrategyFilter>) => {
      state.filter = action.payload;
    },

    // Clear filter
    clearFilter: (state) => {
      state.filter = {};
    },

    // Toggle strategy selection
    toggleStrategySelection: (state, action: PayloadAction<string>) => {
      const strategyId = action.payload;
      const index = state.selectedStrategies.indexOf(strategyId);
      if (index > -1) {
        state.selectedStrategies.splice(index, 1);
      } else {
        state.selectedStrategies.push(strategyId);
      }
    },

    // Clear selection
    clearSelection: (state) => {
      state.selectedStrategies = [];
    },

    // Select all strategies
    selectAllStrategies: (state) => {
      state.selectedStrategies = state.strategies.map(strategy => strategy.id);
    },

    // Clear current strategy
    clearCurrentStrategy: (state) => {
      state.currentStrategy = null;
    },

    // Clear performance data
    clearPerformance: (state) => {
      state.performance = null;
    },

    // Update local strategy (optimistic update)
    updateLocalStrategy: (state, action: PayloadAction<Strategy>) => {
      const index = state.strategies.findIndex(s => s.id === action.payload.id);
      if (index > -1) {
        state.strategies[index] = action.payload;
      }
      if (state.currentStrategy?.id === action.payload.id) {
        state.currentStrategy = action.payload;
      }
    },

    // Remove strategy from local state
    removeLocalStrategy: (state, action: PayloadAction<string>) => {
      const strategyId = action.payload;
      state.strategies = state.strategies.filter(s => s.id !== strategyId);
      if (state.currentStrategy?.id === strategyId) {
        state.currentStrategy = null;
      }
      state.selectedStrategies = state.selectedStrategies.filter(id => id !== strategyId);
    },
  },
  extraReducers: (builder) => {
    // Fetch strategies
    builder
      .addCase(fetchStrategies.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchStrategies.fulfilled, (state, action) => {
        state.loading = false;
        state.strategies = action.payload.items;
        state.strategiesPagination = {
          page: action.payload.page,
          pageSize: action.payload.pageSize,
          total: action.payload.total,
          pages: action.payload.pages,
          hasNext: action.payload.hasNext,
          hasPrev: action.payload.hasPrev,
        };
      })
      .addCase(fetchStrategies.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch strategies';
      });

    // Fetch single strategy
    builder
      .addCase(fetchStrategy.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchStrategy.fulfilled, (state, action) => {
        state.loading = false;
        state.currentStrategy = action.payload;
      })
      .addCase(fetchStrategy.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch strategy';
      });

    // Create strategy
    builder
      .addCase(createStrategy.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createStrategy.fulfilled, (state, action) => {
        state.loading = false;
        state.strategies.unshift(action.payload);
        state.strategiesPagination.total += 1;
      })
      .addCase(createStrategy.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to create strategy';
      });

    // Update strategy
    builder
      .addCase(updateStrategy.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(updateStrategy.fulfilled, (state, action) => {
        state.loading = false;
        const index = state.strategies.findIndex(s => s.id === action.payload.id);
        if (index > -1) {
          state.strategies[index] = action.payload;
        }
        if (state.currentStrategy?.id === action.payload.id) {
          state.currentStrategy = action.payload;
        }
      })
      .addCase(updateStrategy.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to update strategy';
      });

    // Delete strategy
    builder
      .addCase(deleteStrategy.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(deleteStrategy.fulfilled, (state, action) => {
        state.loading = false;
        const strategyId = action.payload;
        state.strategies = state.strategies.filter(s => s.id !== strategyId);
        state.strategiesPagination.total -= 1;
        if (state.currentStrategy?.id === strategyId) {
          state.currentStrategy = null;
        }
        state.selectedStrategies = state.selectedStrategies.filter(id => id !== strategyId);
      })
      .addCase(deleteStrategy.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to delete strategy';
      });

    // Fetch strategy configurations
    builder
      .addCase(fetchStrategyConfigs.fulfilled, (state, action) => {
        state.configs = action.payload.items;
        state.configsPagination = {
          page: action.payload.page,
          pageSize: action.payload.pageSize,
          total: action.payload.total,
          pages: action.payload.pages,
          hasNext: action.payload.hasNext,
          hasPrev: action.payload.hasPrev,
        };
      });

    // Create strategy configuration
    builder
      .addCase(createStrategyConfig.fulfilled, (state, action) => {
        state.configs.unshift(action.payload);
        state.configsPagination.total += 1;
      });

    // Update strategy configuration
    builder
      .addCase(updateStrategyConfig.fulfilled, (state, action) => {
        const index = state.configs.findIndex(c => c.id === action.payload.id);
        if (index > -1) {
          state.configs[index] = action.payload;
        }
      });

    // Delete strategy configuration
    builder
      .addCase(deleteStrategyConfig.fulfilled, (state, action) => {
        const { configId } = action.payload;
        state.configs = state.configs.filter(c => c.id !== configId);
        state.configsPagination.total -= 1;
      });

    // Fetch strategy performance
    builder
      .addCase(fetchStrategyPerformance.pending, (state) => {
        state.performanceLoading = true;
      })
      .addCase(fetchStrategyPerformance.fulfilled, (state, action) => {
        state.performanceLoading = false;
        state.performance = action.payload;
      })
      .addCase(fetchStrategyPerformance.rejected, (state) => {
        state.performanceLoading = false;
        state.error = action.error.message || 'Failed to fetch performance data';
      });

    // Execute strategy
    builder
      .addCase(executeStrategy.fulfilled, (state, action) => {
        state.executions[action.payload.execution_id] = action.payload;
      });

    // Get execution status
    builder
      .addCase(getExecutionStatus.fulfilled, (state, action) => {
        state.executionStatuses[action.payload.execution_id] = action.payload;
      });

    // Stop execution
    builder
      .addCase(stopExecution.fulfilled, (state, action) => {
        const executionId = action.payload.execution_id;
        if (state.executionStatuses[executionId]) {
          state.executionStatuses[executionId].status = 'stopped';
        }
      });

    // Batch operations
    builder
      .addCase(batchOperation.fulfilled, (state, action) => {
        // Handle batch operation results
        const { operation, results } = action.payload;
        results.forEach((result: any) => {
          if (result.status === 'success') {
            if (operation === 'delete') {
              state.strategies = state.strategies.filter(s => s.id !== result.id);
              state.selectedStrategies = state.selectedStrategies.filter(id => id !== result.id);
            } else {
              const index = state.strategies.findIndex(s => s.id === result.id);
              if (index > -1) {
                state.strategies[index].is_active = operation === 'activate';
              }
            }
          }
        });
      });
  },
});

// Export actions
export const {
  clearError,
  setFilter,
  clearFilter,
  toggleStrategySelection,
  clearSelection,
  selectAllStrategies,
  clearCurrentStrategy,
  clearPerformance,
  updateLocalStrategy,
  removeLocalStrategy,
} = strategySlice.actions;

// Export reducer
export default strategySlice.reducer;

// Export selectors
export const selectStrategies = (state: { strategies: StrategiesState }) => state.strategies.strategies;
export const selectCurrentStrategy = (state: { strategies: StrategiesState }) => state.strategies.currentStrategy;
export const selectStrategiesLoading = (state: { strategies: StrategiesState }) => state.strategies.loading;
export const selectStrategiesError = (state: { strategies: StrategiesState }) => state.strategies.error;
export const selectStrategiesPagination = (state: { strategies: StrategiesState }) => state.strategies.strategiesPagination;
export const selectConfigs = (state: { strategies: StrategiesState }) => state.strategies.configs;
export const selectPerformance = (state: { strategies: StrategiesState }) => state.strategies.performance;
export const selectPerformanceLoading = (state: { strategies: StrategiesState }) => state.strategies.performanceLoading;
export const selectFilter = (state: { strategies: StrategiesState }) => state.strategies.filter;
export const selectSelectedStrategies = (state: { strategies: StrategiesState }) => state.strategies.selectedStrategies;
export const selectExecutions = (state: { strategies: StrategiesState }) => state.strategies.executions;
export const selectExecutionStatuses = (state: { strategies: StrategiesState }) => state.strategies.executionStatuses;
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { StrategyData, StrategyStatus } from '../../features/strategies/types';

interface StrategiesState {
  strategies: StrategyData[];
  selectedStrategy: StrategyData | null;
  isLoading: boolean;
  error: string | null;
  filter: {
    status: StrategyStatus | 'all';
    searchTerm: string;
  };
}

const initialState: StrategiesState = {
  strategies: [],
  selectedStrategy: null,
  isLoading: false,
  error: null,
  filter: {
    status: 'all',
    searchTerm: ''
  }
};

// Async thunks
export const fetchStrategies = createAsyncThunk(
  'strategies/fetchStrategies',
  async () => {
    const response = await fetch('/api/strategies', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch strategies');
    }
    
    const data = await response.json();
    return data;
  }
);

export const fetchStrategyById = createAsyncThunk(
  'strategies/fetchStrategyById',
  async (id: string) => {
    const response = await fetch(`/api/strategies/${id}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch strategy');
    }
    
    const data = await response.json();
    return data;
  }
);

export const createStrategy = createAsyncThunk(
  'strategies/createStrategy',
  async (strategyData: Partial<StrategyData>) => {
    const response = await fetch('/api/strategies', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(strategyData)
    });
    
    if (!response.ok) {
      throw new Error('Failed to create strategy');
    }
    
    const data = await response.json();
    return data;
  }
);

export const updateStrategy = createAsyncThunk(
  'strategies/updateStrategy',
  async ({ id, ...strategyData }: Partial<StrategyData> & { id: string }) => {
    const response = await fetch(`/api/strategies/${id}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(strategyData)
    });
    
    if (!response.ok) {
      throw new Error('Failed to update strategy');
    }
    
    const data = await response.json();
    return data;
  }
);

export const deleteStrategy = createAsyncThunk(
  'strategies/deleteStrategy',
  async (id: string) => {
    const response = await fetch(`/api/strategies/${id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
    
    if (!response.ok) {
      throw new Error('Failed to delete strategy');
    }
    
    return id;
  }
);

export const toggleStrategy = createAsyncThunk(
  'strategies/toggleStrategy',
  async ({ id, isActive }: { id: string; isActive: boolean }) => {
    const response = await fetch(`/api/strategies/${id}/toggle`, {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ isActive })
    });
    
    if (!response.ok) {
      throw new Error('Failed to toggle strategy');
    }
    
    const data = await response.json();
    return data;
  }
);

const strategiesSlice = createSlice({
  name: 'strategies',
  initialState,
  reducers: {
    setSelectedStrategy: (state, action: PayloadAction<StrategyData | null>) => {
      state.selectedStrategy = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
    setFilter: (state, action: PayloadAction<Partial<StrategiesState['filter']>>) => {
      state.filter = { ...state.filter, ...action.payload };
    }
  },
  extraReducers: (builder) => {
    builder
      // Fetch strategies
      .addCase(fetchStrategies.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchStrategies.fulfilled, (state, action) => {
        state.isLoading = false;
        state.strategies = action.payload;
      })
      .addCase(fetchStrategies.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch strategies';
      })
      // Fetch strategy by ID
      .addCase(fetchStrategyById.fulfilled, (state, action) => {
        state.selectedStrategy = action.payload;
      })
      // Create strategy
      .addCase(createStrategy.fulfilled, (state, action) => {
        state.strategies.push(action.payload);
      })
      // Update strategy
      .addCase(updateStrategy.fulfilled, (state, action) => {
        const index = state.strategies.findIndex(s => s.id === action.payload.id);
        if (index !== -1) {
          state.strategies[index] = action.payload;
        }
        if (state.selectedStrategy?.id === action.payload.id) {
          state.selectedStrategy = action.payload;
        }
      })
      // Delete strategy
      .addCase(deleteStrategy.fulfilled, (state, action) => {
        state.strategies = state.strategies.filter(s => s.id !== action.payload);
        if (state.selectedStrategy?.id === action.payload) {
          state.selectedStrategy = null;
        }
      })
      // Toggle strategy
      .addCase(toggleStrategy.fulfilled, (state, action) => {
        const index = state.strategies.findIndex(s => s.id === action.payload.id);
        if (index !== -1) {
          state.strategies[index] = action.payload;
        }
        if (state.selectedStrategy?.id === action.payload.id) {
          state.selectedStrategy = action.payload;
        }
      });
  }
});

export const { setSelectedStrategy, clearError, setFilter } = strategiesSlice.actions;
export default strategiesSlice.reducer;

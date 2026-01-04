# Redux Toolkit + RTK Query Implementation Guide

## Overview

The CBSC Trading System uses Redux Toolkit (RTK) for state management and RTK Query for server state management. This guide explains the implementation patterns and best practices used in the application.

## Store Configuration

### Main Store Setup

Located at `frontend/src/store/index.ts`:

```typescript
import { configureStore, combineReducers } from '@reduxjs/toolkit';
import { setupListeners } from '@reduxjs/toolkit/query';

// Combine reducers
const rootReducer = combineReducers({
  auth: authSlice.reducer,
  strategies: strategiesSlice.reducer,
  strategy: strategySlice.reducer,
  dashboard: dashboardSlice.reducer,
  [apiSlice.reducerPath]: apiReducer,
});

// Configure store
export const store = configureStore({
  reducer: rootReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
        ignoredPaths: ['auth.token', 'auth.refreshToken'],
      },
    }).concat(apiMiddleware),
  devTools: import.meta.env.DEV,
});

// Enable refetchOnFocus/refetchOnReconnect
setupListeners(store.dispatch);
```

### TypeScript Types

```typescript
// Export types for use in components
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

// Typed hooks
export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: <T>(selector: (state: RootState) => T) => T =
  useSelector;
```

## Redux Slices

### Auth Slice

Located at `frontend/src/store/slices/authSlice.ts`:

```typescript
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { User, LoginCredentials, RegisterData } from '@/types/auth';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

const initialState: AuthState = {
  user: null,
  token: localStorage.getItem('token'),
  isAuthenticated: false,
  isLoading: false,
  error: null,
};

// Async thunks
export const loginUser = createAsyncThunk(
  'auth/login',
  async (credentials: LoginCredentials, { rejectWithValue }) => {
    try {
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.message);
      return data;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

export const registerUser = createAsyncThunk(
  'auth/register',
  async (userData: RegisterData, { rejectWithValue }) => {
    try {
      const response = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(userData),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.message);
      return data;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

// Slice
const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    logout: (state) => {
      state.user = null;
      state.token = null;
      state.isAuthenticated = false;
      localStorage.removeItem('token');
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Login
      .addCase(loginUser.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(loginUser.fulfilled, (state, action) => {
        state.isLoading = false;
        state.user = action.payload.user;
        state.token = action.payload.token;
        state.isAuthenticated = true;
        localStorage.setItem('token', action.payload.token);
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // Register
      .addCase(registerUser.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(registerUser.fulfilled, (state, action) => {
        state.isLoading = false;
        state.user = action.payload.user;
        state.token = action.payload.token;
        state.isAuthenticated = true;
        localStorage.setItem('token', action.payload.token);
      })
      .addCase(registerUser.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });
  },
});

export const { logout, clearError } = authSlice.actions;
export default authSlice.reducer;
```

### Strategies Slice

Located at `frontend/src/store/slices/strategiesSlice.ts`:

```typescript
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { Strategy, StrategyFilters } from '@/types/strategy';

interface StrategiesState {
  items: Strategy[];
  selectedId: number | null;
  filters: StrategyFilters;
  pagination: {
    page: number;
    pageSize: number;
    total: number;
  };
  isLoading: boolean;
  error: string | null;
}

const initialState: StrategiesState = {
  items: [],
  selectedId: null,
  filters: {
    status: 'all',
    category: 'all',
    search: '',
  },
  pagination: {
    page: 1,
    pageSize: 20,
    total: 0,
  },
  isLoading: false,
  error: null,
};

// Async thunks
export const fetchStrategies = createAsyncThunk(
  'strategies/fetch',
  async (params: { page?: number; pageSize?: number; filters?: StrategyFilters }) => {
    const response = await fetch(`/api/v1/strategies?page=${params.page}&limit=${params.pageSize}`);
    const data = await response.json();
    return data;
  }
);

// Slice
const strategiesSlice = createSlice({
  name: 'strategies',
  initialState,
  reducers: {
    setSelectedId: (state, action: PayloadAction<number | null>) => {
      state.selectedId = action.payload;
    },
    setFilters: (state, action: PayloadAction<Partial<StrategyFilters>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearFilters: (state) => {
      state.filters = initialState.filters;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchStrategies.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchStrategies.fulfilled, (state, action) => {
        state.isLoading = false;
        state.items = action.payload.data;
        state.pagination.total = action.payload.total;
      })
      .addCase(fetchStrategies.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch strategies';
      });
  },
});

export const { setSelectedId, setFilters, clearFilters } = strategiesSlice.actions;
export default strategiesSlice.reducer;
```

## RTK Query API

### API Slice Configuration

Located at `frontend/src/store/api/apiSlice.ts`:

```typescript
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

// Define a base query with authorization
const baseQuery = fetchBaseQuery({
  baseUrl: '/api/v1',
  prepareHeaders: (headers, { getState }) => {
    const token = (getState() as RootState).auth.token;
    if (token) {
      headers.set('authorization', `Bearer ${token}`);
    }
    return headers;
  },
});

// Create API slice
export const apiSlice = createApi({
  reducerPath: 'api',
  baseQuery,
  tagTypes: ['Strategy', 'User', 'Trade', 'Portfolio', 'Backtest'],
  endpoints: (builder) => ({
    // Strategy endpoints
    getStrategies: builder.query<StrategyResponse, StrategyParams>({
      query: (params) => ({
        url: '/strategies',
        params: {
          page: params.page,
          limit: params.limit,
          status: params.status,
          category: params.category,
        },
      }),
      providesTags: ['Strategy'],
    }),

    getStrategy: builder.query<Strategy, number>({
      query: (id) => `/strategies/${id}`,
      providesTags: (result, error, id) => [{ type: 'Strategy', id }],
    }),

    createStrategy: builder.mutation<Strategy, CreateStrategyRequest>({
      query: (data) => ({
        url: '/strategies',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['Strategy'],
    }),

    updateStrategy: builder.mutation<Strategy, { id: number; data: UpdateStrategyRequest }>({
      query: ({ id, data }) => ({
        url: `/strategies/${id}`,
        method: 'PUT',
        body: data,
      }),
      invalidatesTags: (result, error, { id }) => [
        'Strategy',
        { type: 'Strategy', id },
      ],
    }),

    deleteStrategy: builder.mutation<void, number>({
      query: (id) => ({
        url: `/strategies/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Strategy'],
    }),

    // Backtest endpoints
    runBacktest: builder.mutation<BacktestResult, BacktestRequest>({
      query: (data) => ({
        url: '/backtest/run',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['Backtest'],
    }),

    // Portfolio endpoints
    getPortfolio: builder.query<Portfolio, number>({
      query: (id) => `/portfolios/${id}`,
      providesTags: (result, error, id) => [{ type: 'Portfolio', id }],
    }),
  }),
});

// Export hooks
export const {
  useGetStrategiesQuery,
  useGetStrategyQuery,
  useCreateStrategyMutation,
  useUpdateStrategyMutation,
  useDeleteStrategyMutation,
  useRunBacktestMutation,
  useGetPortfolioQuery,
} = apiSlice;

// Export API slice and middleware
export const api = apiSlice;
export const apiReducer = apiSlice.reducer;
export const apiMiddleware = apiSlice.middleware;
```

### Using RTK Query Hooks in Components

```typescript
import { useGetStrategiesQuery, useCreateStrategyMutation } from '@/store/api/apiSlice';

export function StrategyList() {
  // Query hook - automatically fetches data
  const {
    data: strategiesData,
    isLoading,
    isError,
    refetch,
  } = useGetStrategiesQuery({ page: 1, limit: 20 });

  // Mutation hook - for creating strategies
  const [createStrategy, { isLoading: isCreating }] = useCreateStrategyMutation();

  const handleCreate = async (strategyData: CreateStrategyRequest) => {
    try {
      const result = await createStrategy(strategyData).unwrap();
      console.log('Strategy created:', result);
    } catch (error) {
      console.error('Failed to create strategy:', error);
    }
  };

  if (isLoading) return <Loading />;
  if (isError) return <ErrorMessage />;

  return (
    <div>
      {strategiesData?.data.map((strategy) => (
        <StrategyCard key={strategy.id} strategy={strategy} />
      ))}
    </div>
  );
}
```

## Advanced Patterns

### Optimistic Updates

```typescript
updateStrategy: builder.mutation<Strategy, { id: number; data: UpdateStrategyRequest }>({
  query: ({ id, data }) => ({
    url: `/strategies/${id}`,
    method: 'PUT',
    body: data,
  }),
  async onQueryStarted({ id, data }, { dispatch, queryFulfilled }) {
    // Optimistically update the cache
    const patchResult = dispatch(
      apiSlice.util.updateQueryData('getStrategy', id, (draft) => {
        Object.assign(draft, data);
      })
    );

    try {
      await queryFulfilled;
    } catch {
      // Rollback on error
      patchResult.undo();
    }
  },
  invalidatesTags: (result, error, { id }) => [
    'Strategy',
    { type: 'Strategy', id },
  ],
}),
```

### Cache Invalidation

```typescript
// Automatic invalidation with tags
createStrategy: builder.mutation<Strategy, CreateStrategyRequest>({
  query: (data) => ({
    url: '/strategies',
    method: 'POST',
    body: data,
  }),
  invalidatesTags: ['Strategy'], // Invalidates all queries with 'Strategy' tag
}),
```

```typescript
// Manual invalidation
import { api } from '@/store/api/apiSlice';

function manuallyInvalidate() {
  dispatch(api.util.invalidateTags(['Strategy']));
}
```

### Prefetching Data

```typescript
import { api } from '@/store/api/apiSlice';

function StrategyList() {
  const prefetchStrategy = useLazyGetStrategyQuery();

  const handleMouseEnter = (id: number) => {
    // Prefetch strategy data on hover
    prefetchStrategy(id, { preferCacheValue: true });
  };

  return (
    <div>
      {strategies.map((strategy) => (
        <div
          key={strategy.id}
          onMouseEnter={() => handleMouseEnter(strategy.id)}
        >
          {strategy.name}
        </div>
      ))}
    </div>
  );
}
```

## Middleware

### Custom Middleware Example

```typescript
// Logger middleware
const loggerMiddleware = (store: AppStore) => (next: any) => (action: any) => {
  console.log('Dispatching:', action);
  const result = next(action);
  console.log('Next state:', store.getState());
  return result;
};

// Add to store
export const store = configureStore({
  reducer: rootReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(loggerMiddleware).concat(apiMiddleware),
});
```

### Error Handling Middleware

```typescript
const errorMiddleware: Middleware<{}, RootState> = (store) => (next) => (action) => {
  if (action.type.endsWith('/rejected')) {
    // Handle API errors
    console.error('API Error:', action.payload);
    // Show toast notification
    toast.error(action.payload.message || 'An error occurred');
  }
  return next(action);
};
```

## Persistence

### Using Redux Persist

```typescript
import { persistStore, persistReducer } from 'redux-persist';
import storage from 'redux-persist/lib/storage';

// Persist configuration
const persistConfig = {
  key: 'root',
  storage,
  whitelist: ['auth'], // Only persist auth slice
  blacklist: ['api'], // Don't persist API cache
};

// Create persisted reducer
const persistedReducer = persistReducer(persistConfig, rootReducer);

// Configure store with persistence
export const store = configureStore({
  reducer: persistedReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
      },
    }).concat(apiMiddleware),
});

// Create persistor
export const persistor = persistStore(store);
```

## Testing

### Testing Redux Slices

```typescript
import authReducer, {
  loginUser,
  logout,
  clearError,
} from '../authSlice';

describe('authSlice', () => {
  const initialState = {
    user: null,
    token: null,
    isAuthenticated: false,
    isLoading: false,
    error: null,
  };

  test('should handle initial state', () => {
    expect(authReducer(undefined, { type: 'unknown' })).toEqual(initialState);
  });

  test('should handle logout', () => {
    const actual = authReducer(
      { ...initialState, isAuthenticated: true, token: 'test' },
      logout()
    );
    expect(actual.isAuthenticated).toEqual(false);
    expect(actual.token).toEqual(null);
  });

  test('should handle clearError', () => {
    const actual = authReducer(
      { ...initialState, error: 'Test error' },
      clearError()
    );
    expect(actual.error).toEqual(null);
  });

  test('should handle loginUser.pending', () => {
    const actual = authReducer(initialState, loginUser.pending('', {}));
    expect(actual.isLoading).toEqual(true);
    expect(actual.error).toEqual(null);
  });
});
```

### Testing RTK Query Endpoints

```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import { apiSlice } from '../apiSlice';
import { setupApiStore } from './testUtils';

describe('strategy API', () => {
  let store: any;

  beforeEach(() => {
    store = setupApiStore(apiSlice);
  });

  it('should fetch strategies', async () => {
    // Mock fetch
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ data: [], total: 0 }),
      })
    ) as any;

    const result = await store.dispatch(api.endpoints.getStrategies.initiate({}));

    expect(result.isSuccess).toBe(true);
    expect(result.data).toEqual({ data: [], total: 0 });
  });
});
```

## Best Practices

### 1. Use TypeScript for Type Safety

```typescript
// Define types for API responses
interface StrategyResponse {
  data: Strategy[];
  total: number;
  page: number;
  pageSize: number;
}

// Use types in endpoints
getStrategies: builder.query<StrategyResponse, StrategyParams>({
  query: (params) => ({
    url: '/strategies',
    params,
  }),
}),
```

### 2. Normalize State Structure

```typescript
// Instead of nested arrays, use normalized structure
interface NormalizedState {
  entities: {
    [id: string]: Strategy;
  };
  ids: string[];
}

// Use immer for immutable updates
import { current, produce } from 'immer';

const nextState = produce(currentState, (draft) => {
  draft.entities[id] = updatedEntity;
});
```

### 3. Selectors for Derived Data

```typescript
// Create selectors
export const selectAllStrategies = (state: RootState) =>
  state.strategies.items;

export const selectActiveStrategies = (state: RootState) =>
  state.strategies.items.filter((s) => s.status === 'active');

export const selectStrategyById = (state: RootState, id: number) =>
  state.strategies.items.find((s) => s.id === id);

// Use memoized selectors for performance
import { createSelector } from '@reduxjs/toolkit';

export const selectStrategiesByCategory = createSelector(
  [selectAllStrategies, (state, category: string) => category],
  (strategies, category) =>
    strategies.filter((s) => s.category === category)
);
```

### 4. Error Boundaries

```typescript
// Wrap components in error boundaries
import { ErrorBoundary } from 'react-error-boundary';

function ErrorFallback({ error }: { error: Error }) {
  return (
    <div role="alert">
      <p>Something went wrong:</p>
      <pre>{error.message}</pre>
    </div>
  );
}

<ErrorBoundary FallbackComponent={ErrorFallback}>
  <StrategyList />
</ErrorBoundary>
```

### 5. Loading States

```typescript
// Handle loading states consistently
function StrategyList() {
  const { data, isLoading, error } = useGetStrategiesQuery({ page: 1 });

  if (isLoading) {
    return <StrategyListSkeleton />;
  }

  if (error) {
    return <ErrorMessage error={error} />;
  }

  return <StrategyListContent strategies={data?.data || []} />;
}
```

---
*Document Version: 1.0*
*Created: 2025-12-25*
*Author: CBSC System Unification Team*

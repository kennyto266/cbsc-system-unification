# State Management Architecture Guide

## Overview

This guide explains the State Management architecture for the CBSC Trading Dashboard, built with Redux Toolkit and RTK Query.

## Architecture

### Core Components

1. **Redux Store** - Centralized state container
2. **Slices** - Modular state reducers for different domains
3. **APIs** - RTK Query endpoints for server communication
4. **Middleware** - Custom middleware for cross-cutting concerns
5. **Persistence** - State persistence with Redux Persist

### Store Structure

```typescript
interface RootState {
  auth: AuthState          // User authentication and session
  ui: UIState              // UI state and preferences
  market: MarketState      // Market data and WebSocket
  strategies: StrategiesState // Trading strategies
  monitoring: MonitoringState // System monitoring
  analytics: AnalyticsState // Analytics data
  dashboard: DashboardState // Dashboard configuration
  technicalIndicators: TechnicalIndicatorsState // 477 indicators
  api: ApiState           // RTK Query cache state
}
```

## State Slices

### Auth Slice

Manages user authentication, session tokens, and user profile data.

```typescript
// Usage
import { loginSuccess, logout, updateUser } from '../store/slices/authSlice'

// Login
dispatch(loginSuccess({ user, token }))

// Update user profile
dispatch(updateUser({ email: 'new@example.com' }))

// Logout
dispatch(logout())
```

### UI Slice

Controls UI state including theme, sidebar, notifications, and loading states.

```typescript
// Usage
import { setTheme, toggleSidebar, addNotification } from '../store/slices/uiSlice'

// Toggle theme
dispatch(setTheme('dark'))

// Toggle sidebar
dispatch(toggleSidebar())

// Add notification
dispatch(addNotification({
  type: 'success',
  title: 'Success',
  message: 'Action completed successfully'
}))
```

### Market Slice

Handles market data, WebSocket connections, and real-time updates.

```typescript
// Usage
import { fetchMarketData, updateRealTimeData } from '../store/slices/marketSlice'

// Fetch market data
const result = await dispatch(fetchMarketData({ symbol: 'BTC/USDT', interval: '1h' }))

// Real-time update (from WebSocket)
dispatch(updateRealTimeData({
  symbol: 'BTC/USDT',
  price: 45000,
  change: 500,
  changePercent: 1.12
}))
```

### Strategies Slice

Manages trading strategies, execution status, and backtest results.

```typescript
// Usage
import { createStrategy, startStrategy } from '../store/api/strategiesApi'

// Create new strategy
const result = await dispatch(createStrategy({
  name: 'RSI Strategy',
  type: 'technical',
  parameters: { rsiPeriod: 14 }
}))

// Start strategy execution
await dispatch(startStrategy({
  strategyId: result.data.id,
  mode: 'paper'
}))
```

### Dashboard Slice

Controls dashboard layout, widgets, and user preferences.

```typescript
// Usage
import { addWidget, updateWidgetPosition, setTimeRange } from '../store/slices/dashboardSlice'

// Add new widget
dispatch(addWidget({
  type: 'chart',
  title: 'Performance Chart',
  position: { x: 0, y: 0, w: 12, h: 8 }
}))

// Update widget position
dispatch(updateWidgetPosition({
  id: 'widget-123',
  position: { x: 12, y: 0, w: 12, h: 8 }
}))

// Set time range
dispatch(setTimeRange('1M'))
```

## API Integration

### RTK Query Best Practices

1. **Cache Management** - Use tags for intelligent cache invalidation
2. **Optimistic Updates** - Update UI immediately for better UX
3. **Error Handling** - Centralized error handling in middleware
4. **Background Refetch** - Automatic data refetch on focus/reconnect

```typescript
// Example API call with cache management
export const strategiesApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getStrategies: builder.query<Strategy[], void>({
      query: () => 'strategies',
      providesTags: ['Strategy'], // Cache tag
    }),
    createStrategy: builder.mutation<Strategy, Partial<Strategy>>({
      query: (strategy) => ({
        url: 'strategies',
        method: 'POST',
        body: strategy,
      }),
      invalidatesTags: ['Strategy'], // Invalidate cache
    }),
  }),
})
```

### Using API in Components

```typescript
import { useGetStrategiesQuery, useCreateStrategyMutation } from '../store/api/strategiesApi'

function StrategyList() {
  // Read data
  const { data: strategies, isLoading, error } = useGetStrategiesQuery({
    status: 'active',
    page: 1,
    pageSize: 10
  })

  // Write data
  const [createStrategy, { isLoading: isCreating }] = useCreateStrategyMutation()

  const handleCreate = async (strategyData) => {
    try {
      await createStrategy(strategyData).unwrap()
      message.success('Strategy created')
    } catch (error) {
      message.error('Failed to create strategy')
    }
  }

  // Render component...
}
```

## Middleware

### Error Middleware

Automatically handles API errors and displays notifications.

```typescript
// Automatically called on API errors
// Error details are added to UI state and displayed as notifications
```

### WebSocket Middleware

Routes WebSocket messages to appropriate slices.

```typescript
// WebSocket message handlers
{
  'market_data': (data) => dispatch(updateRealTimeData(data)),
  'strategy_update': (data) => dispatch(updateStrategy(data)),
  'execution_update': (data) => dispatch(updateExecution(data)),
  'system_alert': (data) => dispatch(addAlert(data))
}
```

### Performance Middleware

Monitors action performance for optimization.

```typescript
// Logs slow actions in development
// Helps identify performance bottlenecks
```

## Performance Optimization

### 1. Selectors

Use memoized selectors to prevent unnecessary re-renders.

```typescript
import { createSelector } from '@reduxjs/toolkit'

const selectActiveStrategies = createSelector(
  [selectStrategies],
  (strategies) => strategies.filter(s => s.status === 'active')
)
```

### 2. Component Optimization

```typescript
import { memo } from 'react'

const StrategyCard = memo(({ strategy }) => {
  // Only re-renders if strategy prop changes
  return <div>{strategy.name}</div>
})
```

### 3. Data Normalization

Use entity adapters for managing collections.

```typescript
import { createEntityAdapter } from '@reduxjs/toolkit'

const strategiesAdapter = createEntityAdapter<Strategy>({
  selectId: (strategy) => strategy.id,
  sortComparer: (a, b) => a.name.localeCompare(b.name),
})
```

## Persistence

State persistence is configured for critical data:

- **Auth state** - User session and preferences
- **UI state** - Theme, sidebar state, user preferences
- **Dashboard state** - Widget layout and configuration

```typescript
const authPersistConfig = {
  key: 'auth',
  storage: localStorage,
  whitelist: ['user', 'token', 'isAuthenticated'], // Only persist these fields
}
```

## Development Tools

### Redux DevTools

Configured with custom settings for better debugging:

- Action tracing enabled
- Serialization in production
- Limited history size

### Time Travel Debugging

All state changes are logged for easy debugging:

```typescript
// Enable in development
if (process.env.NODE_ENV === 'development') {
  window.__REDUX_STORE__ = store
}
```

## Testing

### Testing Redux Code

```typescript
// Test slice
import { reducer, actions } from '../store/slices/authSlice'

describe('authSlice', () => {
  it('should handle login success', () => {
    const initialState = { user: null, token: null }
    const action = actions.loginSuccess({ user: { id: '1' }, token: 'abc' })
    const state = reducer(initialState, action)

    expect(state.user).toEqual({ id: '1' })
    expect(state.token).toBe('abc')
  })
})
```

### Mocking API Calls

```typescript
import { setupApiStore } from '../test-utils'

const storeRef = setupApiStore(strategiesApi)

// Mock fetch
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve(mockData),
  })
)
```

## Common Patterns

### 1. Async Actions with Redux Toolkit

```typescript
// Using createAsyncThunk
export const fetchUserData = createAsyncThunk(
  'user/fetch',
  async (userId: string) => {
    const response = await userApi.getUser(userId)
    return response.data
  }
)
```

### 2. Handling Loading States

```typescript
// Using RTK Query hooks
const { data, isLoading, error } = useGetStrategiesQuery()

// Show loading indicator
if (isLoading) return <LoadingSpinner />

// Show error
if (error) return <ErrorMessage error={error} />
```

### 3. Optimistic Updates

```typescript
// Using RTK Query with onQueryStarted
const [updateStrategy] = useUpdateStrategyMutation()

const handleUpdate = async (updates) => {
  await updateStrategy({
    id,
    updates,
    // Optimistic update
    onQueryStarted: async ({ id, updates }, { dispatch, queryFulfilled }) => {
      const patchResult = dispatch(
        strategiesApi.util.updateQueryData('getStrategy', id, (draft) => {
          Object.assign(draft, updates)
        })
      )
      try {
        await queryFulfilled
      } catch {
        patchResult.undo()
      }
    }
  })
}
```

## Best Practices

### DO
- ✅ Use TypeScript for type safety
- ✅ Normalize data in reducers
- ✅ Use selectors for component data access
- ✅ Implement proper error boundaries
- ✅ Cache API responses appropriately
- ✅ Use memoization for expensive operations

### DON'T
- ❌ Put non-serializable data in state
- ❌ Mutate state directly (always use reducers)
- ❌ Call API actions in render methods
- ❌ Store large objects directly in state
- ❌ Ignore TypeScript warnings
- ❌ Forget to clean up subscriptions

## Troubleshooting

### Common Issues

1. **State Not Updating**
   - Check if action is being dispatched
   - Verify reducer handles the action
   - Check for immutable violations

2. **Performance Issues**
   - Use React.memo for components
   - Implement proper selectors
   - Check for unnecessary re-renders

3. **Memory Leaks**
   - Clean up subscriptions
   - Remove event listeners
   - Cancel pending requests

### Debugging Tools

- Redux DevTools Extension
- React Developer Tools
- Performance Profiler
- Network tab for API calls

## Migration Guide

### From Old State Management

1. **Identify state slices**
2. **Create Redux Toolkit slices**
3. **Set up RTK Query for API calls**
4. **Implement middleware**
5. **Update components to use hooks**
6. **Test thoroughly**
7. **Remove old state management code**

### Migration Checklist

- [ ] Create type definitions
- [ ] Set up Redux store
- [ ] Create slices
- [ ] Configure middleware
- [ ] Set up persistence
- [ ] Update components
- [ ] Add tests
- [ ] Performance testing
- [ ] Documentation

## References

- [Redux Toolkit Documentation](https://redux-toolkit.js.org/)
- [RTK Query Documentation](https://redux-toolkit.js.org/rtk-query/overview)
- [Redux Best Practices](https://redux.js.org/style-guide/style-guide)
- [React Redux Hooks](https://react-redux.js.org/api/hooks)
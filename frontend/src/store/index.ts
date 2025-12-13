import { configureStore } from '@reduxjs/toolkit'
import { authSlice } from './slices/authSlice'
import { strategySlice } from './slices/strategySlice'
import { dashboardSlice } from './slices/dashboardSlice'

export const store = configureStore({
  reducer: {
    auth: authSlice.reducer,
    strategy: strategySlice.reducer,
    dashboard: dashboardSlice.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
      },
    }),
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
import { configureStore } from '@reduxjs/toolkit'
import { authSlice } from './auth'
import { uiSlice } from './ui'
import { marketSlice } from './market'
import { strategySlice } from './strategy'

export const store = configureStore({
  reducer: {
    auth: authSlice.reducer,
    ui: uiSlice.reducer,
    market: marketSlice.reducer,
    strategy: strategySlice.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST'],
      },
    }),
  devTools: process.env.NODE_ENV !== 'production',
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch

export * from './auth'
export * from './ui'
export * from './market'
export * from './strategy'
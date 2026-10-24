import { combineReducers } from '@reduxjs/toolkit'
import { PersistConfig } from 'redux-persist'
import { persistReducer } from 'redux-persist'
import storage from 'redux-persist/lib/storage'

// Import all reducers
import authReducer from './slices/authSlice'
import uiReducer from './slices/uiSlice'
import strategiesReducer from './slices/strategiesSlice'
import monitoringReducer from './slices/monitoringSlice'
import analyticsReducer from './slices/analyticsSlice'
import technicalIndicatorsReducer from './slices/technicalIndicatorsSlice'

// Import RTK Query API reducers will be added by the store
const rootReducer = combineReducers({
  auth: authReducer,
  ui: uiReducer,
  strategies: strategiesReducer,
  monitoring: monitoringReducer,
  analytics: analyticsReducer,
  technicalIndicators: technicalIndicatorsReducer,
})

// Configuration for persisting auth state
const authPersistConfig: PersistConfig<any> = {
  key: 'auth',
  storage,
  whitelist: ['user', 'token', 'isAuthenticated'],
}

// Configuration for persisting UI state
const uiPersistConfig: PersistConfig<any> = {
  key: 'ui',
  storage,
  whitelist: ['theme', 'sidebarCollapsed', 'preferences'],
}

// Apply persistence to individual reducers
export const persistedReducer = combineReducers({
  auth: persistReducer(authPersistConfig, authReducer),
  ui: persistReducer(uiPersistConfig, uiReducer),
  strategies: strategiesReducer,
  monitoring: monitoringReducer,
  analytics: analyticsReducer,
  technicalIndicators: technicalIndicatorsReducer,
})

export default rootReducer

// Type exports for TypeScript
export type RootReducer = ReturnType<typeof persistedReducer>
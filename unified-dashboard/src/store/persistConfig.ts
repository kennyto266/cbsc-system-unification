import { persistConfig } from 'redux-persist'
import storage from 'redux-persist/lib/storage'
import { RootState } from '../types/store'

// Configuration for Redux Persist
export const persistConfig = {
  key: 'cbsc-root',
  version: 1,
  storage,
  whitelist: [
    // Auth state - persist user session
    'auth',

    // UI preferences - persist user settings
    'ui',

    // Do NOT persist:
    // - market: Real-time data, should be fetched fresh
    // - strategies: Execution state, should be fresh
    // - monitoring: Real-time monitoring data
    // - analytics: Cache should be managed by RTK Query
    // - dashboard: Widget positions can be persisted but data should be fresh
  ],
  blacklist: [
    // Sensitive data that shouldn't be persisted
    'auth.token',

    // Temporary states
    'ui.loading',
    'ui.notifications',
    'ui.activeModals',

    // Real-time data
    'market.websocket',
    'strategies.execution',
    'monitoring.marketData',
  ],

  // State transformer for custom serialization
  transforms: [
    // Add transforms here if needed for custom serialization
  ],

  // Migration config for state structure changes
  migrate: (state: any) => {
    // Handle migrations between versions
    if (state && state._persist && state._persist.version !== persistConfig.version) {
      console.log('Migrating Redux Persist state from version', state._persist.version, 'to', persistConfig.version)

      // Perform migrations here
      // Example: migrate from v0 to v1
      if (state._persist.version === 0) {
        // Migration logic
        if (state.auth) {
          // Update auth state structure if needed
        }
      }
    }

    return Promise.resolve(state)
  },

  // Write failure handler
  writeFailHandler: (error: Error) => {
    console.error('Redux Persist write failed:', error)
  },
}

// Persist configuration for specific slices
export const authPersistConfig = {
  key: 'auth',
  storage,
  whitelist: ['user', 'token', 'isAuthenticated'],
}

export const uiPersistConfig = {
  key: 'ui',
  storage,
  whitelist: [
    'theme',
    'themeMode',
    'sidebarCollapsed',
    'layoutDensity',
    'screenSize',
    'recentPages',
    'favoritePages',
    'preferences',
  ],
}

export const strategiesPersistConfig = {
  key: 'strategies',
  storage,
  whitelist: [
    'filters',
    'sorting',
    'pagination',
    'selected',
  ],
}

// Export utility functions for persist management
export const getPersistConfig = (key: string, storage = window.localStorage) => ({
  key,
  storage,
  whitelist: [],
  blacklist: [],
})

// Clear persist function for logout
export const clearPersist = () => {
  storage.removeItem('persist:cbsc-root')
  storage.removeItem('persist:auth')
  storage.removeItem('persist:ui')
  storage.removeItem('persist:strategies')
}
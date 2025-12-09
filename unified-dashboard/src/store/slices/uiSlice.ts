import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { UIState, Notification } from '@types/index'

const initialState: UIState = {
  theme: 'light',
  sidebarCollapsed: false,
  currentPath: '/',
  loading: {
    global: false,
    strategies: false,
    analytics: false,
    monitoring: false,
  },
  notifications: [],
  modals: {
    strategyDetail: false,
    createStrategy: false,
    settings: false,
  },
}

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    setTheme: (state, action: PayloadAction<'light' | 'dark' | 'auto'>) => {
      state.theme = action.payload
      // Apply theme to document
      if (action.payload === 'dark') {
        document.documentElement.classList.add('dark')
      } else {
        document.documentElement.classList.remove('dark')
      }
    },
    toggleSidebar: (state) => {
      state.sidebarCollapsed = !state.sidebarCollapsed
    },
    setSidebarCollapsed: (state, action: PayloadAction<boolean>) => {
      state.sidebarCollapsed = action.payload
    },
    setCurrentPath: (state, action: PayloadAction<string>) => {
      state.currentPath = action.payload
    },
    setGlobalLoading: (state, action: PayloadAction<boolean>) => {
      state.loading.global = action.payload
    },
    setStrategiesLoading: (state, action: PayloadAction<boolean>) => {
      state.loading.strategies = action.payload
    },
    setAnalyticsLoading: (state, action: PayloadAction<boolean>) => {
      state.loading.analytics = action.payload
    },
    setMonitoringLoading: (state, action: PayloadAction<boolean>) => {
      state.loading.monitoring = action.payload
    },
    addNotification: (state, action: PayloadAction<Omit<Notification, 'id' | 'timestamp' | 'read'>>) => {
      const notification: Notification = {
        ...action.payload,
        id: Date.now().toString(),
        timestamp: new Date().toISOString(),
        read: false,
      }
      state.notifications.unshift(notification)
      // Keep only last 50 notifications
      if (state.notifications.length > 50) {
        state.notifications = state.notifications.slice(0, 50)
      }
    },
    removeNotification: (state, action: PayloadAction<string>) => {
      state.notifications = state.notifications.filter(n => n.id !== action.payload)
    },
    markNotificationAsRead: (state, action: PayloadAction<string>) => {
      const notification = state.notifications.find(n => n.id === action.payload)
      if (notification) {
        notification.read = true
      }
    },
    markAllNotificationsAsRead: (state) => {
      state.notifications.forEach(n => {
        n.read = true
      })
    },
    clearNotifications: (state) => {
      state.notifications = []
    },
    openModal: (state, action: PayloadAction<keyof UIState['modals']>) => {
      state.modals[action.payload] = true
    },
    closeModal: (state, action: PayloadAction<keyof UIState['modals']>) => {
      state.modals[action.payload] = false
    },
    closeAllModals: (state) => {
      Object.keys(state.modals).forEach(key => {
        state.modals[key as keyof UIState['modals']] = false
      })
    },
    // Reset UI state (for logout)
    resetUIState: () => {
      return { ...initialState }
    },
  },
})

export const {
  setTheme,
  toggleSidebar,
  setSidebarCollapsed,
  setCurrentPath,
  setGlobalLoading,
  setStrategiesLoading,
  setAnalyticsLoading,
  setMonitoringLoading,
  addNotification,
  removeNotification,
  markNotificationAsRead,
  markAllNotificationsAsRead,
  clearNotifications,
  openModal,
  closeModal,
  closeAllModals,
  resetUIState,
} = uiSlice.actions

export default uiSlice.reducer

// Selectors
export const selectTheme = (state: { ui: UIState }) => state.ui.theme
export const selectSidebarCollapsed = (state: { ui: UIState }) => state.ui.sidebarCollapsed
export const selectCurrentPath = (state: { ui: UIState }) => state.ui.currentPath
export const selectGlobalLoading = (state: { ui: UIState }) => state.ui.loading.global
export const selectStrategiesLoading = (state: { ui: UIState }) => state.ui.loading.strategies
export const selectAnalyticsLoading = (state: { ui: UIState }) => state.ui.loading.analytics
export const selectMonitoringLoading = (state: { ui: UIState }) => state.ui.loading.monitoring
export const selectNotifications = (state: { ui: UIState }) => state.ui.notifications
export const selectUnreadNotifications = (state: { ui: UIState }) =>
  state.ui.notifications.filter(n => !n.read)
export const selectUnreadNotificationCount = (state: { ui: UIState }) =>
  state.ui.notifications.filter(n => !n.read).length
export const selectModals = (state: { ui: UIState }) => state.ui.modals
export const selectModal = (state: { ui: UIState }, modalName: keyof UIState['modals']) =>
  state.ui.modals[modalName]
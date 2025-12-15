import { createSlice, PayloadAction } from '@reduxjs/toolkit'

interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message: string
  duration?: number
  timestamp: number
}

interface UIState {
  theme: 'light' | 'dark'
  sidebarOpen: boolean
  notifications: Notification[]
  loading: Record<string, boolean>
  modals: Record<string, boolean>
  drawers: Record<string, boolean>
  pageSize: number
  language: 'zh-CN' | 'en-US'
}

const initialState: UIState = {
  theme: (localStorage.getItem('theme') as 'light' | 'dark') || 'light',
  sidebarOpen: true,
  notifications: [],
  loading: {},
  modals: {},
  drawers: {},
  pageSize: 20,
  language: (localStorage.getItem('language') as 'zh-CN' | 'en-US') || 'zh-CN',
}

export const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    setTheme: (state, action: PayloadAction<'light' | 'dark'>) => {
      state.theme = action.payload
      localStorage.setItem('theme', action.payload)
    },
    toggleSidebar: (state) => {
      state.sidebarOpen = !state.sidebarOpen
    },
    setSidebarOpen: (state, action: PayloadAction<boolean>) => {
      state.sidebarOpen = action.payload
    },
    addNotification: (state, action: PayloadAction<Omit<Notification, 'id' | 'timestamp'>>) => {
      const notification: Notification = {
        ...action.payload,
        id: Date.now().toString(),
        timestamp: Date.now(),
      }
      state.notifications.push(notification)
    },
    removeNotification: (state, action: PayloadAction<string>) => {
      state.notifications = state.notifications.filter(n => n.id !== action.payload)
    },
    clearNotifications: (state) => {
      state.notifications = []
    },
    setLoading: (state, action: PayloadAction<{ key: string; loading: boolean }>) => {
      state.loading[action.payload.key] = action.payload.loading
    },
    setModalOpen: (state, action: PayloadAction<{ key: string; open: boolean }>) => {
      state.modals[action.payload.key] = action.payload.open
    },
    setDrawerOpen: (state, action: PayloadAction<{ key: string; open: boolean }>) => {
      state.drawers[action.payload.key] = action.payload.open
    },
    closeAllModals: (state) => {
      state.modals = {}
    },
    closeAllDrawers: (state) => {
      state.drawers = {}
    },
    setPageSize: (state, action: PayloadAction<number>) => {
      state.pageSize = action.payload
    },
    setLanguage: (state, action: PayloadAction<'zh-CN' | 'en-US'>) => {
      state.language = action.payload
      localStorage.setItem('language', action.payload)
    },
  },
})

export const {
  setTheme,
  toggleSidebar,
  setSidebarOpen,
  addNotification,
  removeNotification,
  clearNotifications,
  setLoading,
  setModalOpen,
  setDrawerOpen,
  closeAllModals,
  closeAllDrawers,
  setPageSize,
  setLanguage,
} = uiSlice.actions
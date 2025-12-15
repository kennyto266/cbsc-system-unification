import { useDispatch, useSelector, TypedUseSelectorHook } from 'react-redux'
import type { RootState, AppDispatch } from './index'

// Use throughout your app instead of plain `useDispatch` and `useSelector`
export const useAppDispatch = () => useDispatch<AppDispatch>()
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector

// Custom hooks for common state operations
export const useAuth = () => {
  const auth = useAppSelector((state) => state.auth)
  const dispatch = useAppDispatch()

  return {
    ...auth,
    isAuthenticated: auth.isAuthenticated && !auth.isLoading,
    // Helper function to check if token is expired
    isTokenExpired: auth.tokenExpiresAt ? Date.now() >= auth.tokenExpiresAt : false,
    // Helper function to check user permissions
    hasPermission: (permission: string) =>
      auth.user?.permissions?.includes(permission) || false,
    // Helper function to check user role
    hasRole: (role: string) => auth.user?.role === role,
    // Helper functions for auth actions
    login: (credentials: any) => dispatch({ type: 'auth/loginStart', payload: credentials }),
    logout: () => dispatch({ type: 'auth/logout' }),
    clearError: () => dispatch({ type: 'auth/clearError' }),
  }
}

export const useUI = () => {
  const ui = useAppSelector((state) => state.ui)
  const dispatch = useAppDispatch()

  return {
    ...ui,
    // Theme helpers
    isDarkMode: ui.theme === 'dark',
    toggleTheme: () => dispatch({
      type: 'ui/setTheme',
      payload: ui.theme === 'light' ? 'dark' : 'light'
    }),
    // Sidebar helpers
    toggleSidebar: () => dispatch({ type: 'ui/toggleSidebar' }),
    setSidebarOpen: (open: boolean) => dispatch({
      type: 'ui/setSidebarOpen',
      payload: open
    }),
    // Notification helpers
    showNotification: (notification: Omit<any, 'id' | 'timestamp'>) =>
      dispatch({ type: 'ui/addNotification', payload: notification }),
    hideNotification: (id: string) =>
      dispatch({ type: 'ui/removeNotification', payload: id }),
    clearNotifications: () => dispatch({ type: 'ui/clearNotifications' }),
    // Loading helpers
    setLoading: (key: string, loading: boolean) =>
      dispatch({ type: 'ui/setLoading', payload: { key, loading } }),
    isLoading: (key: string) => ui.loading[key] || false,
    // Modal helpers
    openModal: (key: string) =>
      dispatch({ type: 'ui/setModalOpen', payload: { key, open: true } }),
    closeModal: (key: string) =>
      dispatch({ type: 'ui/setModalOpen', payload: { key, open: false } }),
    isModalOpen: (key: string) => ui.modals[key] || false,
    // Drawer helpers
    openDrawer: (key: string) =>
      dispatch({ type: 'ui/setDrawerOpen', payload: { key, open: true } }),
    closeDrawer: (key: string) =>
      dispatch({ type: 'ui/setDrawerOpen', payload: { key, open: false } }),
    isDrawerOpen: (key: string) => ui.drawers[key] || false,
    // Language helpers
    setLanguage: (language: 'zh-CN' | 'en-US') =>
      dispatch({ type: 'ui/setLanguage', payload: language }),
    // Page size helpers
    setPageSize: (pageSize: number) =>
      dispatch({ type: 'ui/setPageSize', payload: pageSize }),
  }
}

export const useStrategies = () => {
  const strategies = useAppSelector((state) => state.strategy)
  const dispatch = useAppDispatch()

  return {
    ...strategies,
    // Helper functions
    selectStrategy: (strategy: any) =>
      dispatch({ type: 'strategy/setSelectedStrategy', payload: strategy }),
    clearSelection: () =>
      dispatch({ type: 'strategy/setSelectedStrategy', payload: null }),
    updateLocalStrategy: (strategy: any) =>
      dispatch({ type: 'strategy/updateStrategy', payload: strategy }),
    removeLocalStrategy: (id: string) =>
      dispatch({ type: 'strategy/removeStrategy', payload: id }),
    // Computed values - using the existing Strategy interface fields
    activeStrategies: strategies.strategies.filter(s => s.status === 'active'),
    inactiveStrategies: strategies.strategies.filter(s => s.status === 'inactive'),
    testingStrategies: strategies.strategies.filter(s => s.status === 'testing'),
  }
}

export const useDashboard = () => {
  const dashboard = useAppSelector((state) => state.dashboard)
  const dispatch = useAppDispatch()

  return {
    ...dashboard,
    // Helper functions
    refreshData: () => dispatch({ type: 'dashboard/refreshData' }),
    setTimeRange: (timeRange: string) =>
      dispatch({ type: 'dashboard/setTimeRange', payload: timeRange }),
    setRefreshInterval: (interval: number) =>
      dispatch({ type: 'dashboard/setRefreshInterval', payload: interval }),
    // Computed values
    isRealTime: (dashboard as any).refreshInterval > 0,
  }
}

// Performance monitoring hooks
export const usePerformanceMonitor = () => {
  const dispatch = useAppDispatch()

  return {
    markRenderStart: (componentName: string) => {
      performance.mark(`${componentName}-render-start`)
    },
    markRenderEnd: (componentName: string) => {
      performance.mark(`${componentName}-render-end`)
      performance.measure(
        `${componentName}-render`,
        `${componentName}-render-start`,
        `${componentName}-render-end`
      )
    },
    markApiCall: (apiName: string) => {
      performance.mark(`${apiName}-api-start`)
    },
    markApiComplete: (apiName: string) => {
      performance.mark(`${apiName}-api-complete`)
      performance.measure(
        `${apiName}-api`,
        `${apiName}-api-start`,
        `${apiName}-api-complete`
      )
    },
  }
}

// Debounced hook for search/filter operations
import { useEffect, useState } from 'react'

export const useDebouncedValue = <T>(value: T, delay: number): T => {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => {
      clearTimeout(handler)
    }
  }, [value, delay])

  return debouncedValue
}

// Local storage hook
export const useLocalStorage = <T>(
  key: string,
  initialValue: T
): [T, (value: T) => void] => {
  // Get from local storage then parse stored json or return initialValue
  const readValue = (): T => {
    try {
      const item = window.localStorage.getItem(key)
      return item ? JSON.parse(item) : initialValue
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error)
      return initialValue
    }
  }

  const [storedValue, setStoredValue] = useState<T>(readValue)

  // Return a wrapped version of useState's setter function that persists the new value to localStorage
  const setValue = (value: T) => {
    try {
      // Allow value to be a function so we have same API as useState
      const valueToStore = value instanceof Function ? value(storedValue) : value
      setStoredValue(valueToStore)
      window.localStorage.setItem(key, JSON.stringify(valueToStore))
    } catch (error) {
      console.warn(`Error setting localStorage key "${key}":`, error)
    }
  }

  return [storedValue, setValue]
}
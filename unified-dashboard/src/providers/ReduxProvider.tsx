import React, { ReactNode, useEffect, useRef } from 'react'
import { Provider } from 'react-redux'
import { PersistGate } from 'redux-persist/integration/react'
import { store, persistor } from '../store'
import { useAppDispatch, useAppSelector } from '../hooks/redux'
import {
  checkAuthStart,
  checkAuthSuccess,
  selectIsAuthenticated,
  selectToken,
} from '../store/slices/authSlice'
import { setScreenSize } from '../store/slices/uiSlice'

interface ReduxProviderProps {
  children: ReactNode
}

// Main Redux provider component
export function ReduxProvider({ children }: ReduxProviderProps) {
  return (
    <Provider store={store}>
      <PersistGate loading={null} persistor={persistor}>
        <ReduxInitializer>{children}</ReduxInitializer>
      </PersistGate>
    </Provider>
  )
}

// Initialize app state after Redux is ready
function ReduxInitializer({ children }: { children: ReactNode }) {
  return <>{children}</>
}

// Custom hooks for app initialization
export function useAppInitializer() {
  const dispatch = useAppDispatch()
  const token = useAppSelector(selectToken)
  const initialized = useRef(false)

  useEffect(() => {
    if (!initialized.current) {
      // Check authentication if token exists
      if (token) {
        dispatch(checkAuthStart())
        // TODO: Implement actual auth check with API
        // For now, just simulate success
        setTimeout(() => {
          dispatch(checkAuthSuccess({
            id: '1',
            username: 'demo',
            email: 'demo@cbsc.com',
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
          }))
        }, 100)
      }

      // Set initial screen size
      const handleResize = () => {
        const width = window.innerWidth
        if (width < 768) {
          dispatch(setScreenSize('mobile'))
        } else if (width < 1024) {
          dispatch(setScreenSize('tablet'))
        } else if (width < 1440) {
          dispatch(setScreenSize('desktop'))
        } else {
          dispatch(setScreenSize('large-desktop'))
        }
      }

      handleResize()
      window.addEventListener('resize', handleResize)

      initialized.current = true

      return () => {
        window.removeEventListener('resize', handleResize)
      }
    }
  }, [dispatch, token])

  return { initialized: initialized.current }
}

// Re-export store and persistor for direct access
export { store, persistor }

// Re-export selectors for convenience
export {
  selectAuth,
  selectUser,
  selectIsAuthenticated,
  selectIsLoading,
  selectError,
  selectToken,
  selectHasPermission,
  selectHasRole,
  selectIsAdmin,
} from '../store/slices/authSlice'

export {
  selectUI,
  selectTheme,
  selectThemeMode,
  selectSidebarCollapsed,
  selectScreenSize,
  selectLayoutDensity,
  selectLoading,
  selectNotifications,
  selectUnreadNotifications,
  selectUnreadNotificationCount,
} from '../store/slices/uiSlice'

export {
  selectStrategies,
  selectSelectedStrategy,
  selectStrategiesLoading,
  selectStrategiesError,
  selectStrategyFilters,
  selectExecutionState,
  selectBacktestState,
} from '../store/slices/strategiesSlice'

// Re-export action creators for convenience
export {
  loginStart,
  loginSuccess,
  loginFailure,
  logout,
  updateUser,
  clearError,
  setToken,
  tokenRefreshed,
} from '../store/slices/authSlice'

export {
  toggleSidebar,
  setTheme,
  setThemeMode,
  toggleTheme,
  setScreenSize,
  setLoading,
  addNotification,
  removeNotification,
  markNotificationRead,
  clearNotifications,
  openModal,
  closeModal,
} from '../store/slices/uiSlice'

export {
  setStrategies,
  addStrategy,
  updateStrategy,
  deleteStrategy,
  selectStrategy,
  updateStrategyStatus,
  setFilters,
  clearFilters,
  setSorting,
} from '../store/slices/strategiesSlice'
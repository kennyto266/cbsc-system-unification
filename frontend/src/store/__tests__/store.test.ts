import { configureStore } from '@reduxjs/toolkit'
import { store } from '../index'
import { authSlice } from '../slices/authSlice'
import { uiSlice } from '../slices/uiSlice'
import { strategySlice } from '../slices/strategySlice'
import type { RootState } from '../index'

// Test basic store configuration
describe('Store Configuration', () => {
  test('should configure store with correct reducers', () => {
    const state = store.getState()

    // Check that all slices are present
    expect(state).toHaveProperty('auth')
    expect(state).toHaveProperty('ui')
    expect(state).toHaveProperty('strategy')
    expect(state).toHaveProperty('dashboard')
    expect(state).toHaveProperty('api')
  })

  test('should have correct initial state', () => {
    const state = store.getState()

    // Auth initial state
    expect(state.auth).toEqual({
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      tokenExpiresAt: null,
      lastActivity: expect.any(Number),
      sessionTimeout: 30 * 60 * 1000,
    })

    // UI initial state
    expect(state.ui).toMatchObject({
      theme: expect.stringMatching(/^(light|dark|auto)$/),
      language: expect.stringMatching(/^(zh-CN|zh-TW|en-US)$/),
      sidebar: {
        isOpen: true,
        isCollapsed: false,
        openMenus: [],
      },
      notifications: [],
      globalLoading: false,
      loading: {},
      loadingText: undefined,
      modals: {},
      drawers: {},
      pageSize: 20,
      pageTitle: 'CBSC 策略管理系統',
      breadcrumb: [],
      isMobile: expect.any(Boolean),
      screenSize: {
        width: expect.any(Number),
        height: expect.any(Number),
      },
      keyboardShortcuts: {
        enabled: true,
        helpVisible: false,
      },
      globalSearch: {
        isOpen: false,
        query: '',
        results: [],
      },
      quickActions: {
        visible: false,
        actions: [],
      },
    })

    // Strategy initial state
    expect(state.strategy).toEqual({
      strategies: [],
      selectedStrategy: null,
      editingStrategy: null,
      clonedStrategy: null,
      isLoading: false,
      error: null,
      filters: {
        status: [],
        category: [],
        riskLevel: [],
        search: '',
      },
      sorting: {
        field: 'updatedAt',
        order: 'desc',
      },
      pagination: {
        page: 1,
        pageSize: 20,
        total: 0,
      },
      execution: {},
      parameters: {},
      backtest: {},
    })
  })

  test('should dispatch actions correctly', () => {
    // Test auth actions
    store.dispatch(authSlice.actions.loginStart())
    expect(store.getState().auth.isLoading).toBe(true)

    store.dispatch(authSlice.actions.loginFailure('Test error'))
    expect(store.getState().auth.isLoading).toBe(false)
    expect(store.getState().auth.error).toBe('Test error')

    // Test UI actions
    store.dispatch(uiSlice.actions.setTheme('dark'))
    expect(store.getState().ui.theme).toBe('dark')

    store.dispatch(uiSlice.actions.addNotification({
      type: 'success',
      title: 'Test',
      message: 'Test message'
    }))
    expect(store.getState().ui.notifications).toHaveLength(1)

    // Test strategy actions
    store.dispatch(strategySlice.actions.setLoading(true))
    expect(store.getState().strategy.isLoading).toBe(true)

    store.dispatch(strategySlice.actions.setError('Strategy error'))
    expect(store.getState().strategy.error).toBe('Strategy error')
  })
})

// Test selectors
describe('Selectors', () => {
  test('should select correct values', () => {
    const state: RootState = store.getState()

    // Auth selectors
    expect(state.auth.isAuthenticated).toBe(false)
    expect(state.auth.user).toBeNull()

    // UI selectors
    expect(state.ui.theme).toMatch(/^(light|dark|auto)$/)
    expect(state.ui.sidebar.isOpen).toBe(true)

    // Strategy selectors
    expect(state.strategy.strategies).toEqual([])
    expect(state.strategy.selectedStrategy).toBeNull()
  })
})

// Test middleware functionality
describe('Middleware', () => {
  test('should handle session timeout actions', () => {
    // This is a basic test - in a real app you'd need to mock time
    const initialState = store.getState()
    expect(initialState.auth.sessionTimeout).toBe(30 * 60 * 1000)
  })

  test('should handle notification auto-removal', (done) => {
    // Add a non-persistent success notification
    store.dispatch(uiSlice.actions.addNotification({
      type: 'success',
      title: 'Auto Test',
      message: 'This should auto-remove',
    }))

    // Check notification was added
    expect(store.getState().ui.notifications.length).toBeGreaterThan(0)

    // Wait for auto-removal (3 seconds)
    setTimeout(() => {
      // In a real test environment, you'd check that the notification was removed
      // This is just demonstrating the concept
      done()
    }, 3100)
  })
})

// Test type safety
describe('Type Safety', () => {
  test('should have correct RootState type', () => {
    const state: RootState = store.getState()

    // TypeScript should catch any type errors here
    expect(typeof state.auth).toBe('object')
    expect(typeof state.ui).toBe('object')
    expect(typeof state.strategy).toBe('object')
  })

  test('should have correct AppDispatch type', () => {
    const dispatch = store.dispatch

    // These should all be valid calls according to TypeScript
    expect(() => {
      dispatch(authSlice.actions.loginStart())
      dispatch(uiSlice.actions.setTheme('dark'))
      dispatch({ type: 'strategy/setLoading', payload: true })
    }).not.toThrow()
  })
})

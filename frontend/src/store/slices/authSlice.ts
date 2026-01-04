import { createSlice, PayloadAction } from '@reduxjs/toolkit'

// Enhanced User interface with more fields
interface User {
  id: string
  username: string
  email: string
  role: string
  avatar?: string
  permissions: string[]
  lastLoginAt?: string
  createdAt: string
  updatedAt: string
  isActive: boolean
}

// Enhanced AuthState with refresh token and more fields
interface AuthState {
  user: User | null
  token: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  tokenExpiresAt: number | null
  lastActivity: number
  sessionTimeout: number
}

// Helper functions for secure storage
const secureStorage = {
  setItem: (key: string, value: string) => {
    try {
      localStorage.setItem(key, value)
    } catch (error) {
      console.error('Failed to store secure data:', error)
    }
  },
  getItem: (key: string): string | null => {
    try {
      return localStorage.getItem(key)
    } catch (error) {
      console.error('Failed to retrieve secure data:', error)
      return null
    }
  },
  removeItem: (key: string) => {
    try {
      localStorage.removeItem(key)
    } catch (error) {
      console.error('Failed to remove secure data:', error)
    }
  }
}

const initialState: AuthState = {
  user: null,
  token: secureStorage.getItem('token'),
  refreshToken: secureStorage.getItem('refreshToken'),
  isAuthenticated: !!secureStorage.getItem('token'),
  isLoading: false,
  error: null,
  tokenExpiresAt: null,
  lastActivity: Date.now(),
  sessionTimeout: 30 * 60 * 1000, // 30 minutes
}

export const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    loginStart: (state) => {
      state.isLoading = true
      state.error = null
    },
    loginSuccess: (state, action: PayloadAction<{
      user: User;
      token: string;
      refreshToken?: string;
      expiresIn?: number
    }>) => {
      state.isLoading = false
      state.isAuthenticated = true
      state.user = action.payload.user
      state.token = action.payload.token
      state.refreshToken = action.payload.refreshToken || null
      state.error = null
      state.lastActivity = Date.now()

      // Set token expiration
      if (action.payload.expiresIn) {
        state.tokenExpiresAt = Date.now() + (action.payload.expiresIn * 1000)
      }

      // Store tokens securely
      secureStorage.setItem('token', action.payload.token)
      if (action.payload.refreshToken) {
        secureStorage.setItem('refreshToken', action.payload.refreshToken)
      }

      // Store user info
      try {
        localStorage.setItem('user', JSON.stringify(action.payload.user))
      } catch (error) {
        console.error('Failed to store user info:', error)
      }
    },
    loginFailure: (state, action: PayloadAction<string>) => {
      state.isLoading = false
      state.isAuthenticated = false
      state.user = null
      state.token = null
      state.refreshToken = null
      state.error = action.payload
      state.tokenExpiresAt = null

      // Clear stored data
      secureStorage.removeItem('token')
      secureStorage.removeItem('refreshToken')
      localStorage.removeItem('user')
    },
    logout: (state) => {
      state.isAuthenticated = false
      state.user = null
      state.token = null
      state.refreshToken = null
      state.error = null
      state.tokenExpiresAt = null

      // Clear all stored data
      secureStorage.removeItem('token')
      secureStorage.removeItem('refreshToken')
      localStorage.removeItem('user')
    },
    refreshTokenSuccess: (state, action: PayloadAction<{
      token: string;
      expiresIn?: number
    }>) => {
      state.token = action.payload.token
      state.lastActivity = Date.now()

      // Update token expiration
      if (action.payload.expiresIn) {
        state.tokenExpiresAt = Date.now() + (action.payload.expiresIn * 1000)
      }

      secureStorage.setItem('token', action.payload.token)
    },
    refreshTokenFailure: (state) => {
      // Refresh token failed, force logout
      state.isAuthenticated = false
      state.user = null
      state.token = null
      state.refreshToken = null
      state.error = 'Session expired, please login again'
      state.tokenExpiresAt = null

      secureStorage.removeItem('token')
      secureStorage.removeItem('refreshToken')
      localStorage.removeItem('user')
    },
    updateUserData: (state, action: PayloadAction<Partial<User>>) => {
      if (state.user) {
        state.user = { ...state.user, ...action.payload }
        // Update stored user info
        try {
          localStorage.setItem('user', JSON.stringify(state.user))
        } catch (error) {
          console.error('Failed to store updated user info:', error)
        }
      }
    },
    updateLastActivity: (state) => {
      state.lastActivity = Date.now()
    },
    clearError: (state) => {
      state.error = null
    },
  },
})

export const {
  loginStart,
  loginSuccess,
  loginFailure,
  logout,
  refreshTokenSuccess,
  refreshTokenFailure,
  updateUserData,
  updateLastActivity,
  clearError,
} = authSlice.actions

// Selectors
export const selectAuth = (state: { auth: AuthState }) => state.auth
export const selectUser = (state: { auth: AuthState }) => state.auth.user
export const selectIsAuthenticated = (state: { auth: AuthState }) => state.auth.isAuthenticated
export const selectAuthLoading = (state: { auth: AuthState }) => state.auth.isLoading
export const selectAuthError = (state: { auth: AuthState }) => state.auth.error
export const selectToken = (state: { auth: AuthState }) => state.auth.token
export const selectIsTokenExpired = (state: { auth: AuthState }) => {
  if (!state.auth.tokenExpiresAt) return false
  return Date.now() >= state.auth.tokenExpiresAt
}
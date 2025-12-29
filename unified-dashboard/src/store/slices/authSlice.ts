import { createSlice, PayloadAction, createAsyncThunk } from '@reduxjs/toolkit'
import { AuthState, User } from '../../types/index'
import {
  LoginCredentials,
  LoginResponse,
  RegisterData,
  ChangePasswordData,
  UpdateProfileData,
  TwoFactorSetup,
  TwoFactorVerify,
  Session,
  ActivityLog,
  AuthError,
  AUTH_ERROR_CODES,
} from '../../types/auth'

// Initial state
const initialState: AuthState = {
  user: null,
  token: localStorage.getItem('cbsc_token'),
  isAuthenticated: false,
  isLoading: false,
  error: null,
  refreshToken: localStorage.getItem('cbsc_refresh_token'),
  tokenExpiresAt: null,
  permissions: [],
  roles: [],
}

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    // Login actions
    loginStart: (state) => {
      state.isLoading = true
      state.error = null
    },
    loginSuccess: (state, action: PayloadAction<LoginResponse>) => {
      state.isLoading = false
      state.isAuthenticated = true
      state.user = action.payload.user
      state.token = action.payload.token
      state.refreshToken = action.payload.refreshToken || null
      state.error = null

      // Store tokens in localStorage
      localStorage.setItem('cbsc_token', action.payload.token)
      if (action.payload.refreshToken) {
        localStorage.setItem('cbsc_refresh_token', action.payload.refreshToken)
      }

      // Set token expiration if provided
      if (action.payload.expiresIn) {
        state.tokenExpiresAt = Date.now() + action.payload.expiresIn * 1000
      }

      // Update permissions if provided
      if (action.payload.permissions) {
        state.permissions = action.payload.permissions
      }
    },
    loginFailure: (state, action: PayloadAction<AuthError>) => {
      state.isLoading = false
      state.isAuthenticated = false
      state.user = null
      state.token = null
      state.refreshToken = null
      state.error = action.payload.message
      state.tokenExpiresAt = null

      // Clear tokens from localStorage
      localStorage.removeItem('cbsc_token')
      localStorage.removeItem('cbsc_refresh_token')
    },

    // Logout action
    logout: (state) => {
      state.isAuthenticated = false
      state.user = null
      state.token = null
      state.refreshToken = null
      state.error = null
      state.permissions = []
      state.roles = []
      state.tokenExpiresAt = null

      // Clear tokens from localStorage
      localStorage.removeItem('cbsc_token')
      localStorage.removeItem('cbsc_refresh_token')
    },

    // User profile actions
    updateUser: (state, action: PayloadAction<Partial<User>>) => {
      if (state.user) {
        state.user = { ...state.user, ...action.payload }
      }
    },
    updateUserProfile: (state, action: PayloadAction<UpdateProfileData>) => {
      if (state.user) {
        state.user = { ...state.user, ...action.payload }
      }
    },

    // Permission and role management
    updatePermissions: (state, action: PayloadAction<any[]>) => {
      state.permissions = action.payload
    },
    updateRoles: (state, action: PayloadAction<any[]>) => {
      state.roles = action.payload
    },
    hasPermission: (state, action: PayloadAction<{ resource: string; action: string }>) => {
      // This is a selector-like reducer for checking permissions
      const { resource, action: permissionAction } = action.payload
      return state.permissions.some(p =>
        p.resource === resource && p.action === permissionAction
      )
    },

    // Token management
    setToken: (state, action: PayloadAction<{ token: string; expiresIn?: number }>) => {
      state.token = action.payload.token
      localStorage.setItem('cbsc_token', action.payload.token)

      if (action.payload.expiresIn) {
        state.tokenExpiresAt = Date.now() + action.payload.expiresIn * 1000
      }
    },
    setRefreshToken: (state, action: PayloadAction<string>) => {
      state.refreshToken = action.payload
      localStorage.setItem('cbsc_refresh_token', action.payload)
    },
    clearTokens: (state) => {
      state.token = null
      state.refreshToken = null
      state.tokenExpiresAt = null
      localStorage.removeItem('cbsc_token')
      localStorage.removeItem('cbsc_refresh_token')
    },
    tokenRefreshed: (state, action: PayloadAction<{ token: string; expiresIn?: number }>) => {
      state.token = action.payload.token
      localStorage.setItem('cbsc_token', action.payload.token)

      if (action.payload.expiresIn) {
        state.tokenExpiresAt = Date.now() + action.payload.expiresIn * 1000
      }
    },

    // Authentication status checks
    checkAuthStart: (state) => {
      state.isLoading = true
    },
    checkAuthSuccess: (state, action: PayloadAction<User>) => {
      state.isLoading = false
      state.isAuthenticated = true
      state.user = action.payload
      state.error = null
    },
    checkAuthFailure: (state) => {
      state.isLoading = false
      state.isAuthenticated = false
      state.user = null
      state.token = null
      state.refreshToken = null
      state.error = null
      state.tokenExpiresAt = null

      // Clear invalid tokens
      localStorage.removeItem('cbsc_token')
      localStorage.removeItem('cbsc_refresh_token')
    },

    // Error handling
    setError: (state, action: PayloadAction<string>) => {
      state.error = action.payload
    },
    clearError: (state) => {
      state.error = null
    },

    // Session management
    updateSession: (state, action: PayloadAction<Partial<Session>>) => {
      // Store session information (could be part of user metadata)
      if (state.user) {
        state.user.session = { ...state.user.session, ...action.payload }
      }
    },

    // Activity tracking
    trackActivity: (state, action: PayloadAction<Partial<ActivityLog>>) => {
      // This would typically be handled by middleware
      // The reducer just updates state if needed
    },
  },
})

export const {
  // Login actions
  loginStart,
  loginSuccess,
  loginFailure,

  // Logout action
  logout,

  // User profile actions
  updateUser,
  updateUserProfile,

  // Permission and role management
  updatePermissions,
  updateRoles,
  hasPermission,

  // Token management
  setToken,
  setRefreshToken,
  clearTokens,
  tokenRefreshed,

  // Authentication status checks
  checkAuthStart,
  checkAuthSuccess,
  checkAuthFailure,

  // Error handling
  setError,
  clearError,

  // Session management
  updateSession,

  // Activity tracking
  trackActivity,
} = authSlice.actions

export default authSlice.reducer

// Selectors
export const selectAuth = (state: { persisted: { auth: AuthState } }) => state.persisted.auth
export const selectUser = (state: { persisted: { auth: AuthState } }) => state.persisted.auth.user
export const selectUserId = (state: { persisted: { auth: AuthState } }) => state.persisted.auth.user?.id
export const selectUserName = (state: { persisted: { auth: AuthState } }) => state.persisted.auth.user?.username
export const selectUserEmail = (state: { persisted: { auth: AuthState } }) => state.persisted.auth.user?.email
export const selectIsAuthenticated = (state: { persisted: { auth: AuthState } }) => state.persisted.auth.isAuthenticated
export const selectIsLoading = (state: { persisted: { auth: AuthState } }) => state.persisted.auth.isLoading
export const selectError = (state: { persisted: { auth: AuthState } }) => state.persisted.auth.error
export const selectToken = (state: { persisted: { auth: AuthState } }) => state.persisted.auth.token
export const selectRefreshToken = (state: { persisted: { auth: AuthState } }) => state.persisted.auth.refreshToken
export const selectTokenExpiresAt = (state: { persisted: { auth: AuthState } }) => state.persisted.auth.tokenExpiresAt
export const selectPermissions = (state: { persisted: { auth: AuthState } }) => state.persisted.auth.permissions
export const selectRoles = (state: { persisted: { auth: AuthState } }) => state.persisted.auth.roles

// Derived selectors
export const selectIsTokenExpired = (state: { persisted: { auth: AuthState } }) => {
  const { tokenExpiresAt } = state.persisted.auth
  if (!tokenExpiresAt) return false
  return Date.now() >= tokenExpiresAt
}

export const selectIsTokenExpiringSoon = (state: { persisted: { auth: AuthState } }, bufferMinutes: number = 5) => {
  const { tokenExpiresAt } = state.persisted.auth
  if (!tokenExpiresAt) return false
  return Date.now() >= tokenExpiresAt - bufferMinutes * 60 * 1000
}

export const selectHasPermission = (resource: string, action: string) => (state: { persisted: { auth: AuthState } }) => {
  return state.persisted.auth.permissions.some(p =>
    p.resource === resource && p.action === action
  )
}

export const selectHasRole = (roleName: string) => (state: { persisted: { auth: AuthState } }) => {
  return state.persisted.auth.roles.some(r => r.name === roleName)
}

export const selectUserRole = (state: { persisted: { auth: AuthState } }) => {
  return state.persisted.auth.roles.length > 0 ? state.persisted.auth.roles[0].name : null
}

export const selectIsAdmin = (state: { persisted: { auth: AuthState } }) => {
  return selectHasRole('admin')(state)
}

// Utility selectors
export const selectAuthHeaders = (state: { persisted: { auth: AuthState } }) => {
  const token = state.persisted.auth.token
  return token ? { Authorization: `Bearer ${token}` } : {}
}
/**
 * Authentication Utilities
 * Helper functions for authentication management
 */

// Token storage keys
const TOKEN_KEY = 'auth_token'
const REFRESH_TOKEN_KEY = 'refresh_token'
const USER_KEY = 'user_info'

// Get auth token
export const getToken = (): string | null => {
  return localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(TOKEN_KEY)
}

// Save auth token
export const setToken = (token: string, rememberMe: boolean = false): void => {
  const storage = rememberMe ? localStorage : sessionStorage
  storage.setItem(TOKEN_KEY, token)
}

// Get refresh token
export const getRefreshToken = (): string | null => {
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

// Save refresh token
export const setRefreshToken = (refreshToken: string): void => {
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
}

// Remove tokens
export const removeToken = (): void => {
  localStorage.removeItem(TOKEN_KEY)
  sessionStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}

// Check if token exists
export const hasToken = (): boolean => {
  return !!getToken()
}

// Parse JWT token (without verification)
export const parseJWT = (token: string): any => {
  try {
    const base64Url = token.split('.')[1]
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    )
    return JSON.parse(jsonPayload)
  } catch (error) {
    console.error('Failed to parse JWT token:', error)
    return null
  }
}

// Check if token is expired
export const isTokenExpired = (token?: string): boolean => {
  const actualToken = token || getToken()
  if (!actualToken) return true

  const payload = parseJWT(actualToken)
  if (!payload || !payload.exp) return true

  const expirationTime = payload.exp * 1000 // Convert to milliseconds
  return Date.now() >= expirationTime
}

// Get token expiration time
export const getTokenExpiration = (token?: string): Date | null => {
  const actualToken = token || getToken()
  if (!actualToken) return null

  const payload = parseJWT(actualToken)
  if (!payload || !payload.exp) return null

  return new Date(payload.exp * 1000)
}

// Get user info from token
export const getUserFromToken = (): any => {
  const token = getToken()
  if (!token) return null

  const payload = parseJWT(token)
  return payload ? payload.user || payload.sub : null
}

// Save user info
export const setUserInfo = (user: any): void => {
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

// Get user info
export const getUserInfo = (): any => {
  const userInfo = localStorage.getItem(USER_KEY)
  return userInfo ? JSON.parse(userInfo) : null
}

// Remove user info
export const removeUserInfo = (): void => {
  localStorage.removeItem(USER_KEY)
}

// Check if user has permission
export const hasPermission = (permission: string): boolean => {
  const userInfo = getUserInfo()
  if (!userInfo || !userInfo.permissions) return false

  return userInfo.permissions.includes(permission)
}

// Check if user has role
export const hasRole = (role: string): boolean => {
  const userInfo = getUserInfo()
  if (!userInfo || !userInfo.roles) return false

  return userInfo.roles.some((r: any) => r.name === role)
}

// Get auth headers
export const getAuthHeaders = (): Record<string, string> => {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

// Initialize authentication from storage
export const initAuth = (): boolean => {
  const token = getToken()
  if (!token || isTokenExpired(token)) {
    removeToken()
    removeUserInfo()
    return false
  }

  // Load user info from storage if available
  const userInfo = getUserInfo()
  if (!userInfo) {
    const userFromToken = getUserFromToken()
    if (userFromToken) {
      setUserInfo(userFromToken)
    }
  }

  return true
}

// Clear all authentication data
export const clearAuth = (): void => {
  removeToken()
  removeUserInfo()
}

// Refresh token before expiry
export const refreshTokenIfNeeded = async (
  refreshFunction: () => Promise<{ token: string; refreshToken: string }>,
  thresholdMinutes: number = 5
): Promise<boolean> => {
  const token = getToken()
  if (!token) return false

  const expiration = getTokenExpiration(token)
  if (!expiration) return false

  const threshold = thresholdMinutes * 60 * 1000 // Convert to milliseconds
  const timeUntilExpiry = expiration.getTime() - Date.now()

  if (timeUntilExpiry <= threshold) {
    try {
      const response = await refreshFunction()
      setToken(response.token)
      setRefreshToken(response.refreshToken)
      return true
    } catch (error) {
      console.error('Failed to refresh token:', error)
      clearAuth()
      return false
    }
  }

  return true
}

// Create auth context value
export const createAuthContext = () => {
  return {
    isAuthenticated: hasToken() && !isTokenExpired(),
    user: getUserInfo(),
    token: getToken(),
    login: (token: string, refreshToken: string, user: any, rememberMe?: boolean) => {
      setToken(token, rememberMe)
      setRefreshToken(refreshToken)
      setUserInfo(user)
    },
    logout: () => {
      clearAuth()
    },
    updateToken: (token: string) => {
      const rememberMe = localStorage.getItem(TOKEN_KEY) === token
      setToken(token, rememberMe)
    },
    hasPermission,
    hasRole,
  }
}

// Export default auth utilities
export default {
  getToken,
  setToken,
  getRefreshToken,
  setRefreshToken,
  removeToken,
  hasToken,
  parseJWT,
  isTokenExpired,
  getTokenExpiration,
  getUserFromToken,
  setUserInfo,
  getUserInfo,
  removeUserInfo,
  hasPermission,
  hasRole,
  getAuthHeaders,
  initAuth,
  clearAuth,
  refreshTokenIfNeeded,
  createAuthContext,
}
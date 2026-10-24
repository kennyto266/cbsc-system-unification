import { User } from './index'

// Auth state interface
export interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  refreshToken: string | null
  tokenExpiresAt: number | null
  permissions: Permission[]
  roles: Role[]
}

// Login credentials interface
export interface LoginCredentials {
  email: string
  password: string
  rememberMe?: boolean
}

// Login response interface
export interface LoginResponse {
  user: User
  token: string
  refreshToken?: string
  expiresIn?: number
  permissions?: Permission[]
}

// Register data interface
export interface RegisterData {
  username: string
  email: string
  password: string
  confirmPassword: string
  firstName?: string
  lastName?: string
  acceptTerms: boolean
}

// Password reset interface
export interface PasswordResetData {
  email: string
}

// Password reset confirm interface
export interface PasswordResetConfirmData {
  token: string
  password: string
  confirmPassword: string
}

// Change password interface
export interface ChangePasswordData {
  currentPassword: string
  newPassword: string
  confirmPassword: string
}

// Update profile interface
export interface UpdateProfileData {
  username?: string
  email?: string
  firstName?: string
  lastName?: string
  avatar?: string
  bio?: string
}

// Permission interface
export interface Permission {
  id: string
  name: string
  description?: string
  resource: string
  action: string
  conditions?: Record<string, any>
}

// Role interface
export interface Role {
  id: string
  name: string
  description?: string
  permissions: Permission[]
  isSystemRole?: boolean
}

// Two-factor authentication
export interface TwoFactorSetup {
  secret: string
  qrCode: string
  backupCodes: string[]
}

export interface TwoFactorVerify {
  code: string
}

export interface TwoFactorEnable {
  code: string
  backupCodes?: string[]
}

// Session management
export interface Session {
  id: string
  device: string
  browser: string
  location?: string
  ipAddress: string
  createdAt: string
  lastActive: string
  current?: boolean
}

// Activity log
export interface ActivityLog {
  id: string
  userId: string
  action: string
  resource?: string
  resourceId?: string
  metadata?: Record<string, any>
  ipAddress: string
  userAgent: string
  timestamp: string
}

// Authentication error types
export interface AuthError {
  code: string
  message: string
  field?: string
}

// Common error codes
export const AUTH_ERROR_CODES = {
  INVALID_CREDENTIALS: 'INVALID_CREDENTIALS',
  TOKEN_EXPIRED: 'TOKEN_EXPIRED',
  TOKEN_INVALID: 'TOKEN_INVALID',
  USER_NOT_FOUND: 'USER_NOT_FOUND',
  EMAIL_ALREADY_EXISTS: 'EMAIL_ALREADY_EXISTS',
  USERNAME_ALREADY_EXISTS: 'USERNAME_ALREADY_EXISTS',
  WEAK_PASSWORD: 'WEAK_PASSWORD',
  INVALID_EMAIL: 'INVALID_EMAIL',
  ACCOUNT_LOCKED: 'ACCOUNT_LOCKED',
  ACCOUNT_SUSPENDED: 'ACCOUNT_SUSPENDED',
  EMAIL_NOT_VERIFIED: 'EMAIL_NOT_VERIFIED',
  TWO_FACTOR_REQUIRED: 'TWO_FACTOR_REQUIRED',
  TWO_FACTOR_INVALID: 'TWO_FACTOR_INVALID',
  SESSION_EXPIRED: 'SESSION_EXPIRED',
  RATE_LIMIT_EXCEEDED: 'RATE_LIMIT_EXCEEDED',
} as const

// Auth action types
export interface AuthActionType {
  LOGIN_REQUEST: 'auth/loginRequest'
  LOGIN_SUCCESS: 'auth/loginSuccess'
  LOGIN_FAILURE: 'auth/loginFailure'
  LOGOUT: 'auth/logout'
  REGISTER_REQUEST: 'auth/registerRequest'
  REGISTER_SUCCESS: 'auth/registerSuccess'
  REGISTER_FAILURE: 'auth/registerFailure'
  REFRESH_TOKEN: 'auth/refreshToken'
  TOKEN_REFRESH_SUCCESS: 'auth/tokenRefreshSuccess'
  TOKEN_REFRESH_FAILURE: 'auth/tokenRefreshFailure'
  CHECK_AUTH_REQUEST: 'auth/checkAuthRequest'
  CHECK_AUTH_SUCCESS: 'auth/checkAuthSuccess'
  CHECK_AUTH_FAILURE: 'auth/checkAuthFailure'
  UPDATE_USER: 'auth/updateUser'
  CLEAR_ERROR: 'auth/clearError'
  SET_TOKEN: 'auth/setToken'
  VERIFY_EMAIL_REQUEST: 'auth/verifyEmailRequest'
  VERIFY_EMAIL_SUCCESS: 'auth/verifyEmailSuccess'
  VERIFY_EMAIL_FAILURE: 'auth/verifyEmailFailure'
  SETUP_2FA_REQUEST: 'auth/setup2FARequest'
  SETUP_2FA_SUCCESS: 'auth/setup2FASuccess'
  SETUP_2FA_FAILURE: 'auth/setup2FAFailure'
  ENABLE_2FA_REQUEST: 'auth/enable2FARequest'
  ENABLE_2FA_SUCCESS: 'auth/enable2FASuccess'
  ENABLE_2FA_FAILURE: 'auth/enable2FAFailure'
  DISABLE_2FA_REQUEST: 'auth/disable2FARequest'
  DISABLE_2FA_SUCCESS: 'auth/disable2FASuccess'
  DISABLE_2FA_FAILURE: 'auth/disable2FAFailure'
}
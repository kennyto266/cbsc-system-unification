// Authentication related types

export interface User {
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
  profile?: {
    firstName?: string
    lastName?: string
    phone?: string
    timezone?: string
    language?: string
  }
}

export interface AuthState {
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

export interface LoginCredentials {
  username: string
  password: string
  rememberMe?: boolean
  captcha?: string
}

export interface RegisterData {
  username: string
  email: string
  password: string
  confirmPassword: string
  firstName?: string
  lastName?: string
  phone?: string
  agreeToTerms: boolean
  captcha?: string
}

export interface AuthResponse {
  user: User
  token: string
  refreshToken?: string
  expiresIn?: number
}

export interface ResetPasswordRequest {
  email: string
  captcha?: string
}

export interface ResetPasswordConfirm {
  token: string
  password: string
  confirmPassword: string
}

export interface ChangePasswordData {
  currentPassword: string
  newPassword: string
  confirmPassword: string
}

export interface UpdateProfileData {
  firstName?: string
  lastName?: string
  phone?: string
  avatar?: string
  timezone?: string
  language?: string
}

// Permission related types
export interface Permission {
  id: string
  name: string
  resource: string
  action: string
  description?: string
}

export interface Role {
  id: string
  name: string
  description: string
  permissions: Permission[]
  isSystemRole: boolean
  createdAt: string
  updatedAt: string
}

// Session management
export interface Session {
  id: string
  userId: string
  deviceInfo: {
    userAgent: string
    ip: string
    platform: string
    browser: string
  }
  createdAt: string
  lastActivity: string
  isActive: boolean
  expiresAt: string
}

// Two-factor authentication
export interface MFASetup {
  secret: string
  qrCode: string
  backupCodes: string[]
}

export interface MFAVerify {
  code: string
  backupCode?: string
}

export interface MFAEnableRequest {
  secret: string
  code: string
}

// Security audit
export interface SecurityLog {
  id: string
  userId: string
  action: string
  resource: string
  ipAddress: string
  userAgent: string
  success: boolean
  reason?: string
  timestamp: string
}
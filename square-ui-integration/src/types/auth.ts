/**
 * Authentication related types
 */

// User
export interface User {
  id: string
  username: string
  email: string
  avatar?: string
  displayName?: string
  role: UserRole
  permissions: Permission[]
  isActive: boolean
  isEmailVerified: boolean
  lastLoginAt?: Date | string
  createdAt: Date | string
  updatedAt: Date | string
}

// User Role
export interface UserRole {
  id: string
  name: string
  displayName: string
  description?: string
  isSystemRole: boolean
  permissions: Permission[]
}

// Permission
export interface Permission {
  id: string
  name: string
  resource: string
  action: string
  description?: string
}

// Auth State
export interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  accessToken: string | null
  refreshToken: string | null
  permissions: string[]
}

// Login Request
export interface LoginRequest {
  username: string
  password: string
  rememberMe?: boolean
  captcha?: string
}

// Login Response
export interface LoginResponse {
  user: User
  accessToken: string
  refreshToken: string
  expiresIn: number
}

// Register Request
export interface RegisterRequest {
  username: string
  email: string
  password: string
  confirmPassword: string
  displayName?: string
  agreeToTerms: boolean
}

// Reset Password Request
export interface ResetPasswordRequest {
  email: string
  token: string
  password: string
  confirmPassword: string
}

// Change Password Request
export interface ChangePasswordRequest {
  currentPassword: string
  newPassword: string
  confirmPassword: string
}

// Update Profile Request
export interface UpdateProfileRequest {
  displayName?: string
  avatar?: string
  email?: string
}

// MFA
export interface MfaSetup {
  secret: string
  qrCode: string
  backupCodes: string[]
}

export interface MfaVerifyRequest {
  token: string
  backupCode?: string
}

// Social Auth
export interface SocialAuth {
  provider: 'google' | 'github' | 'wechat'
  clientId: string
  redirectUri: string
}

// Auth Provider
export interface AuthProvider {
  id: string
  name: string
  type: 'oauth' | 'saml' | 'ldap'
  config: Record<string, any>
  isEnabled: boolean
}

// Session
export interface Session {
  id: string
  userId: string
  deviceInfo: {
    userAgent: string
    ip: string
    location?: string
  }
  createdAt: Date | string
  expiresAt: Date | string
  isActive: boolean
  lastActivityAt: Date | string
}
/**
 * Authentication API Types
 * Types related to authentication and authorization
 */

// User credentials for login
export interface LoginCredentials {
  email: string
  password: string
  rememberMe?: boolean
  captcha?: string
}

// Registration data
export interface RegisterData {
  email: string
  password: string
  confirmPassword: string
  username: string
  firstName: string
  lastName: string
  phone?: string
  agreedToTerms: boolean
  subscribedToNewsletter?: boolean
  captcha?: string
}

// Authentication response
export interface AuthResponse {
  user: User
  token: string
  refreshToken: string
  expiresIn: number
  tokenType: string
}

// Token refresh response
export interface TokenResponse {
  token: string
  refreshToken: string
  expiresIn: number
}

// User profile
export interface User {
  id: string
  email: string
  username: string
  firstName: string
  lastName: string
  avatar?: string
  phone?: string
  isActive: boolean
  isEmailVerified: boolean
  isPhoneVerified: boolean
  roles: Role[]
  permissions: Permission[]
  preferences: UserPreferences
  lastLoginAt?: string
  createdAt: string
  updatedAt: string
}

// Role definition
export interface Role {
  id: string
  name: string
  displayName: string
  description: string
  isSystemRole: boolean
  permissions: Permission[]
  createdAt: string
  updatedAt: string
}

// Permission definition
export interface Permission {
  id: string
  name: string
  resource: string
  action: string
  description: string
}

// User preferences
export interface UserPreferences {
  language: string
  timezone: string
  theme: 'light' | 'dark' | 'auto'
  dateFormat: string
  timeFormat: '12h' | '24h'
  currency: string
  notifications: NotificationPreferences
  dashboard: DashboardPreferences
}

// Notification preferences
export interface NotificationPreferences {
  email: boolean
  sms: boolean
  push: boolean
  trading: boolean
  marketing: boolean
  security: boolean
  system: boolean
}

// Dashboard preferences
export interface DashboardPreferences {
  layout: string[]
  widgets: Record<string, any>
  defaultTimeRange: string
  autoRefresh: boolean
  refreshInterval: number
}

// Password change request
export interface ChangePasswordRequest {
  currentPassword: string
  newPassword: string
  confirmPassword: string
}

// Password reset request
export interface ResetPasswordRequest {
  token: string
  newPassword: string
  confirmPassword: string
}

// Forgot password request
export interface ForgotPasswordRequest {
  email: string
}

// MFA setup response
export interface MFASetupResponse {
  secret: string
  qrCode: string
  backupCodes: string[]
}

// MFA verification request
export interface MFAVerificationRequest {
  code: string
  backupCode?: string
}

// Session information
export interface Session {
  id: string
  userId: string
  device: string
  browser: string
  os: string
  ipAddress: string
  location: string
  isActive: boolean
  lastActivity: string
  createdAt: string
}

// Device management
export interface Device {
  id: string
  name: string
  type: 'desktop' | 'mobile' | 'tablet'
  browser: string
  os: string
  isTrusted: boolean
  lastUsed: string
  createdAt: string
}

// Audit log entry
export interface AuthAuditLog {
  id: string
  userId: string
  action: 'login' | 'logout' | 'password_change' | 'mfa_enabled' | 'mfa_disabled'
  success: boolean
  ipAddress: string
  userAgent: string
  details?: any
  timestamp: string
}

// Security settings
export interface SecuritySettings {
  mfaEnabled: boolean
  mfaMethod: 'totp' | 'sms' | 'email'
  sessionTimeout: number
  passwordExpiry: number
  requireStrongPassword: boolean
  loginNotifications: boolean
  trustedDevices: boolean
  ipWhitelist: string[]
  ipBlacklist: string[]
}
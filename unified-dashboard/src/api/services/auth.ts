/**
 * Authentication API Service
 * Handles all authentication-related API calls
 */

import { apiRequest } from '../client'
import { API_ENDPOINTS } from '../config'
import {
  LoginCredentials,
  RegisterData,
  AuthResponse,
  TokenResponse,
  ChangePasswordRequest,
  ForgotPasswordRequest,
  ResetPasswordRequest,
  MFASetupResponse,
  MFAVerificationRequest,
  Session,
  Device,
  AuthAuditLog,
  ApiResponse,
  PaginatedResponse,
  BaseParams,
} from '../types/auth'

export class AuthService {
  /**
   * User login
   */
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    return apiRequest.post<AuthResponse>(API_ENDPOINTS.AUTH.LOGIN, credentials)
  }

  /**
   * User logout
   */
  async logout(): Promise<void> {
    return apiRequest.post<void>(API_ENDPOINTS.AUTH.LOGOUT)
  }

  /**
   * User registration
   */
  async register(data: RegisterData): Promise<AuthResponse> {
    return apiRequest.post<AuthResponse>(API_ENDPOINTS.AUTH.REGISTER, data)
  }

  /**
   * Refresh access token
   */
  async refreshToken(): Promise<TokenResponse> {
    return apiRequest.post<TokenResponse>(API_ENDPOINTS.AUTH.REFRESH, {
      refreshToken: localStorage.getItem('refreshToken'),
    })
  }

  /**
   * Verify email address
   */
  async verifyEmail(token: string): Promise<void> {
    return apiRequest.post<void>(API_ENDPOINTS.AUTH.VERIFY, { token })
  }

  /**
   * Request password reset
   */
  async forgotPassword(data: ForgotPasswordRequest): Promise<void> {
    return apiRequest.post<void>(API_ENDPOINTS.AUTH.FORGOT_PASSWORD, data)
  }

  /**
   * Reset password
   */
  async resetPassword(data: ResetPasswordRequest): Promise<void> {
    return apiRequest.post<void>(API_ENDPOINTS.AUTH.RESET_PASSWORD, data)
  }

  /**
   * Change password
   */
  async changePassword(data: ChangePasswordRequest): Promise<void> {
    return apiRequest.post<void>(API_ENDPOINTS.AUTH.CHANGE_PASSWORD, data)
  }

  /**
   * Setup Multi-Factor Authentication
   */
  async setupMFA(): Promise<MFASetupResponse> {
    return apiRequest.post<MFASetupResponse>(API_ENDPOINTS.AUTH.MFA_SETUP)
  }

  /**
   * Verify MFA code
   */
  async verifyMFA(data: MFAVerificationRequest): Promise<void> {
    return apiRequest.post<void>(API_ENDPOINTS.AUTH.MFA_VERIFY, data)
  }

  /**
   * Get user sessions
   */
  async getSessions(params?: BaseParams): Promise<PaginatedResponse<Session>> {
    return apiRequest.get<PaginatedResponse<Session>>(`/auth/sessions`, { params })
  }

  /**
   * Revoke a session
   */
  async revokeSession(sessionId: string): Promise<void> {
    return apiRequest.delete<void>(`/auth/sessions/${sessionId}`)
  }

  /**
   * Get user devices
   */
  async getDevices(params?: BaseParams): Promise<PaginatedResponse<Device>> {
    return apiRequest.get<PaginatedResponse<Device>>(`/auth/devices`, { params })
  }

  /**
   * Trust a device
   */
  async trustDevice(deviceId: string): Promise<void> {
    return apiRequest.post<void>(`/auth/devices/${deviceId}/trust`)
  }

  /**
   * Remove a device
   */
  async removeDevice(deviceId: string): Promise<void> {
    return apiRequest.delete<void>(`/auth/devices/${deviceId}`)
  }

  /**
   * Get audit logs
   */
  async getAuditLogs(params?: BaseParams): Promise<PaginatedResponse<AuthAuditLog>> {
    return apiRequest.get<PaginatedResponse<AuthAuditLog>>(`/auth/audit-logs`, { params })
  }

  /**
   * Check if email is available
   */
  async checkEmailAvailability(email: string): Promise<ApiResponse<{ available: boolean }>> {
    return apiRequest.get<ApiResponse<{ available: boolean }>>(`/auth/check-email`, {
      params: { email },
    })
  }

  /**
   * Check if username is available
   */
  async checkUsernameAvailability(username: string): Promise<ApiResponse<{ available: boolean }>> {
    return apiRequest.get<ApiResponse<{ available: boolean }>>(`/auth/check-username`, {
      params: { username },
    })
  }

  /**
   * Resend verification email
   */
  async resendVerificationEmail(email: string): Promise<void> {
    return apiRequest.post<void>(`/auth/resend-verification`, { email })
  }

  /**
   * Get current user info
   */
  async getCurrentUser(): Promise<any> {
    return apiRequest.get('/auth/me')
  }

  /**
   * Update user profile
   */
  async updateProfile(data: Partial<any>): Promise<any> {
    return apiRequest.put('/auth/me', data)
  }
}

// Create singleton instance
export const authService = new AuthService()
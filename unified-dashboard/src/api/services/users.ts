/**
 * User Management API Service
 * Handles all user-related API calls
 */

import { apiRequest } from '../client'
import { API_ENDPOINTS } from '../config'
import { ApiResponse, PaginatedResponse, BaseParams, UploadResponse } from '../types/common'
import {
  User,
  Role,
  Permission,
  UserPreferences,
  NotificationPreferences,
  DashboardPreferences,
  Device,
  ActivityLog,
  UserSearchResult,
} from '../types/auth'

export class UserService {
  /**
   * Get all users
   */
  async getUsers(params?: BaseParams & {
    role?: string
    status?: 'active' | 'inactive' | 'suspended'
    search?: string
    sortBy?: 'name' | 'email' | 'createdAt' | 'lastLogin'
    order?: 'asc' | 'desc'
  }): Promise<PaginatedResponse<User>> {
    return apiRequest.get<PaginatedResponse<User>>(API_ENDPOINTS.USERS.LIST, { params })
  }

  /**
   * Get user by ID
   */
  async getUser(id: string): Promise<ApiResponse<User>> {
    return apiRequest.get<ApiResponse<User>>(API_ENDPOINTS.USERS.DETAIL(id))
  }

  /**
   * Create new user
   */
  async createUser(data: {
    email: string
    username: string
    firstName: string
    lastName: string
    password: string
    roleIds: string[]
    phone?: string
    sendInvite?: boolean
  }): Promise<ApiResponse<User>> {
    return apiRequest.post<ApiResponse<User>>(API_ENDPOINTS.USERS.CREATE, data)
  }

  /**
   * Update user
   */
  async updateUser(id: string, data: Partial<User>): Promise<ApiResponse<User>> {
    return apiRequest.put<ApiResponse<User>>(API_ENDPOINTS.USERS.UPDATE(id), data)
  }

  /**
   * Delete user
   */
  async deleteUser(id: string): Promise<void> {
    return apiRequest.delete<void>(API_ENDPOINTS.USERS.DELETE(id))
  }

  /**
   * Bulk update users
   */
  async bulkUpdateUsers(userIds: string[], data: Partial<User>): Promise<ApiResponse<{ updated: number }>> {
    return apiRequest.put<ApiResponse<any>>('/users/bulk-update', { userIds, data })
  }

  /**
   * Bulk delete users
   */
  async bulkDeleteUsers(userIds: string[]): Promise<ApiResponse<{ deleted: number }>> {
    return apiRequest.delete<ApiResponse<any>>('/users/bulk-delete', { data: { userIds } })
  }

  /**
   * Get current user profile
   */
  async getProfile(): Promise<ApiResponse<User>> {
    return apiRequest.get<ApiResponse<User>>(API_ENDPOINTS.USERS.PROFILE)
  }

  /**
   * Update current user profile
   */
  async updateProfile(data: Partial<User>): Promise<ApiResponse<User>> {
    return apiRequest.put<ApiResponse<User>>(API_ENDPOINTS.USERS.PROFILE, data)
  }

  /**
   * Upload avatar
   */
  async uploadAvatar(file: File): Promise<ApiResponse<UploadResponse>> {
    const formData = new FormData()
    formData.append('avatar', file)
    return apiRequest.post<ApiResponse<UploadResponse>>(API_ENDPOINTS.USERS.AVATAR, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  }

  /**
   * Delete avatar
   */
  async deleteAvatar(): Promise<void> {
    return apiRequest.delete<void>(API_ENDPOINTS.USERS.AVATAR)
  }

  /**
   * Get user preferences
   */
  async getPreferences(): Promise<ApiResponse<UserPreferences>> {
    return apiRequest.get<ApiResponse<UserPreferences>>(API_ENDPOINTS.USERS.SETTINGS)
  }

  /**
   * Update user preferences
   */
  async updatePreferences(preferences: Partial<UserPreferences>): Promise<ApiResponse<UserPreferences>> {
    return apiRequest.put<ApiResponse<UserPreferences>>(API_ENDPOINTS.USERS.SETTINGS, preferences)
  }

  /**
   * Update notification preferences
   */
  async updateNotificationPreferences(preferences: Partial<NotificationPreferences>): Promise<void> {
    return apiRequest.put<void>(API_ENDPOINTS.USERS.SETTINGS + '/notifications', preferences)
  }

  /**
   * Update dashboard preferences
   */
  async updateDashboardPreferences(preferences: Partial<DashboardPreferences>): Promise<void> {
    return apiRequest.put<void>(API_ENDPOINTS.USERS.SETTINGS + '/dashboard', preferences)
  }

  /**
   * Search users
   */
  async searchUsers(query: string, params?: {
    limit?: number
    includeInactive?: boolean
  }): Promise<ApiResponse<UserSearchResult[]>> {
    return apiRequest.get<ApiResponse<UserSearchResult[]>>(API_ENDPOINTS.USERS.SEARCH, {
      params: { q: query, ...params },
    })
  }

  /**
   * Get user roles
   */
  async getRoles(): Promise<ApiResponse<Role[]>> {
    return apiRequest.get<ApiResponse<Role[]>>(API_ENDPOINTS.USERS.ROLES)
  }

  /**
   * Create role
   */
  async createRole(data: {
    name: string
    displayName: string
    description: string
    permissions: string[]
  }): Promise<ApiResponse<Role>> {
    return apiRequest.post<ApiResponse<Role>>(API_ENDPOINTS.USERS.ROLES, data)
  }

  /**
   * Update role
   */
  async updateRole(id: string, data: Partial<Role>): Promise<ApiResponse<Role>> {
    return apiRequest.put<ApiResponse<Role>>(`/users/roles/${id}`, data)
  }

  /**
   * Delete role
   */
  async deleteRole(id: string): Promise<void> {
    return apiRequest.delete<void>(`/users/roles/${id}`)
  }

  /**
   * Assign roles to user
   */
  async assignRoles(userId: string, roleIds: string[]): Promise<void> {
    return apiRequest.post<void>(`/users/${userId}/roles`, { roleIds })
  }

  /**
   * Remove roles from user
   */
  async removeRoles(userId: string, roleIds: string[]): Promise<void> {
    return apiRequest.delete<void>(`/users/${userId}/roles`, { data: { roleIds } })
  }

  /**
   * Get all permissions
   */
  async getPermissions(): Promise<ApiResponse<Permission[]>> {
    return apiRequest.get<ApiResponse<Permission[]>>(API_ENDPOINTS.USERS.PERMISSIONS)
  }

  /**
   * Check user permissions
   */
  async checkPermissions(resource: string, action: string): Promise<ApiResponse<{ allowed: boolean }>> {
    return apiRequest.get<ApiResponse<any>>(API_ENDPOINTS.USERS.PERMISSIONS + '/check', {
      params: { resource, action },
    })
  }

  /**
   * Get user activity logs
   */
  async getActivityLogs(userId: string, params?: BaseParams & {
    action?: string
    resource?: string
    startDate?: string
    endDate?: string
  }): Promise<PaginatedResponse<ActivityLog>> {
    return apiRequest.get<PaginatedResponse<ActivityLog>>(`/users/${userId}/activity`, { params })
  }

  /**
   * Get user devices
   */
  async getUserDevices(userId: string): Promise<ApiResponse<Device[]>> {
    return apiRequest.get<ApiResponse<Device[]>>(`/users/${userId}/devices`)
  }

  /**
   * Revoke user device
   */
  async revokeUserDevice(userId: string, deviceId: string): Promise<void> {
    return apiRequest.delete<void>(`/users/${userId}/devices/${deviceId}`)
  }

  /**
   * Enable/disable user
   */
  async toggleUserStatus(userId: string, isActive: boolean): Promise<void> {
    return apiRequest.patch<void>(`/users/${userId}/status`, { isActive })
  }

  /**
   * Reset user password
   */
  async resetUserPassword(userId: string, newPassword: string): Promise<void> {
    return apiRequest.post<void>(`/users/${userId}/reset-password`, { newPassword })
  }

  /**
   * Force user to change password
   */
  async forcePasswordChange(userId: string): Promise<void> {
    return apiRequest.post<void>(`/users/${userId}/force-password-change`)
  }

  /**
   * Send password reset email
   */
  async sendPasswordResetEmail(email: string): Promise<void> {
    return apiRequest.post<void>(`/users/send-password-reset`, { email })
  }

  /**
   * Export users
   */
  async exportUsers(params?: {
    format?: 'csv' | 'xlsx'
    fields?: string[]
    filters?: Record<string, any>
  }): Promise<ApiResponse<{ downloadUrl: string }>> {
    return apiRequest.get<ApiResponse<any>>('/users/export', { params })
  }

  /**
   * Import users
   */
  async importUsers(file: File, options?: {
    sendInvites?: boolean
    overwrite?: boolean
  }): Promise<ApiResponse<{
    imported: number
    failed: number
    errors: Array<{ row: number; error: string }>
  }>> {
    const formData = new FormData()
    formData.append('file', file)
    if (options) {
      Object.entries(options).forEach(([key, value]) => {
        formData.append(key, value.toString())
      })
    }
    return apiRequest.post<ApiResponse<any>>('/users/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  }

  /**
   * Get user statistics
   */
  async getUserStats(): Promise<ApiResponse<{
    total: number
    active: number
    inactive: number
    newThisMonth: number
    topRoles: Array<{ name: string; count: number }>
    recentActivity: number
  }>> {
    return apiRequest.get<ApiResponse<any>>('/users/stats')
  }

  /**
   * Verify user email
   */
  async verifyUserEmail(userId: string): Promise<void> {
    return apiRequest.post<void>(`/users/${userId}/verify-email`)
  }

  /**
   * Verify user phone
   */
  async verifyUserPhone(userId: string, code: string): Promise<void> {
    return apiRequest.post<void>(`/users/${userId}/verify-phone`, { code })
  }

  /**
   * Send phone verification code
   */
  async sendPhoneVerificationCode(userId: string, phone: string): Promise<void> {
    return apiRequest.post<void>(`/users/${userId}/send-phone-verification`, { phone })
  }
}

// Create singleton instance
export const userService = new UserService()
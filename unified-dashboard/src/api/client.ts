/**
 * API Client Configuration
 * Centralized API client with interceptors and error handling
 */

import axios, { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse } from 'axios'
import { message } from 'antd'
import { API_CONFIG } from './config'
import { getToken, removeToken } from '../utils/auth'

// Extend InternalAxiosRequestConfig to include metadata
declare module 'axios' {
  export interface InternalAxiosRequestConfig {
    metadata?: RequestMetadata
    _retry?: boolean
  }
}

interface RequestMetadata {
  startTime?: Date
}

// Create API client instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_CONFIG.baseURL,
  timeout: API_CONFIG.timeout,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
})

// Request interceptor
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Add auth token if available
    const token = getToken()
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // Add request timestamp
    if (config.metadata) {
      config.metadata.startTime = new Date()
    }

    return config
  },
  (error) => {
    console.error('Request interceptor error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // Log response time for monitoring
    if (response.config.metadata?.startTime) {
      const duration = new Date().getTime() - response.config.metadata.startTime.getTime()
      console.debug(`API Response: ${response.config.url} - ${duration}ms`)
    }

    // Return response data directly
    return response.data
  },
  async (error) => {
    const originalRequest = error.config

    // Handle network errors
    if (!error.response) {
      message.error('网络连接失败，请检查您的网络设置')
      return Promise.reject(error)
    }

    const { status, data } = error.response
    const errorMessage = data?.message || '请求失败'

    // Handle 401 - Unauthorized
    if (status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      // Try to refresh token
      try {
        const refreshResponse = await axios.post(`${API_CONFIG.baseURL}/auth/refresh`, {
          refreshToken: localStorage.getItem('refreshToken'),
        })

        const { token } = refreshResponse.data
        localStorage.setItem('token', token)

        // Retry original request with new token
        originalRequest.headers.Authorization = `Bearer ${token}`
        return apiClient(originalRequest)
      } catch (refreshError) {
        // Refresh failed, redirect to login
        removeToken()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    // Handle 403 - Forbidden
    if (status === 403) {
      message.error('您没有权限执行此操作')
      return Promise.reject(error)
    }

    // Handle 404 - Not Found
    if (status === 404) {
      message.error('请求的资源不存在')
      return Promise.reject(error)
    }

    // Handle 422 - Validation Error
    if (status === 422) {
      const validationErrors = data?.details
      if (validationErrors && Array.isArray(validationErrors)) {
        const errorMessages = validationErrors.map((err: any) => err.message).join(', ')
        message.error(`验证失败: ${errorMessages}`)
      } else {
        message.error(`验证失败: ${errorMessage}`)
      }
      return Promise.reject(error)
    }

    // Handle 429 - Rate Limit
    if (status === 429) {
      message.error('请求过于频繁，请稍后再试')
      return Promise.reject(error)
    }

    // Handle 500 - Server Error
    if (status >= 500) {
      message.error('服务器内部错误，请稍后再试')
      return Promise.reject(error)
    }

    // Handle other errors
    message.error(errorMessage)
    return Promise.reject(error)
  }
)

// Export typed request methods
export const apiRequest = {
  get: <T = any>(url: string, config?: InternalAxiosRequestConfig | any): Promise<T> =>
    apiClient.get(url, config),

  post: <T = any>(url: string, data?: any, config?: InternalAxiosRequestConfig | any): Promise<T> =>
    apiClient.post(url, data, config),

  put: <T = any>(url: string, data?: any, config?: InternalAxiosRequestConfig | any): Promise<T> =>
    apiClient.put(url, data, config),

  patch: <T = any>(url: string, data?: any, config?: InternalAxiosRequestConfig | any): Promise<T> =>
    apiClient.patch(url, data, config),

  delete: <T = any>(url: string, config?: InternalAxiosRequestConfig | any): Promise<T> =>
    apiClient.delete(url, config),
}

// Export the configured client and instance
export { apiClient }
export default apiClient
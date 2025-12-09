import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios'
import { message } from 'antd'
import type { ApiResponse } from '@types/index'

// API基础配置
const API_BASE_URL = process.env.NODE_ENV === 'production'
  ? `${window.location.protocol}//${window.location.host}/api`
  : 'http://localhost:3004/api'

// 创建axios实例
const createApiInstance = (): AxiosInstance => {
  const instance = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
    },
    withCredentials: true,
  })

  // 请求拦截器
  instance.interceptors.request.use(
    (config) => {
      // 从localStorage获取token
      const token = localStorage.getItem('cbsc_token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }

      // 添加请求时间戳
      config.metadata = { startTime: new Date() }

      // 打印请求信息（开发环境）
      if (process.env.NODE_ENV === 'development') {
        console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`, {
          params: config.params,
          data: config.data,
        })
      }

      return config
    },
    (error) => {
      console.error('Request interceptor error:', error)
      return Promise.reject(error)
    }
  )

  // 响应拦截器
  instance.interceptors.response.use(
    (response: AxiosResponse) => {
      // 计算请求耗时
      const endTime = new Date()
      const duration = endTime.getTime() - response.config.metadata?.startTime?.getTime()

      // 打印响应信息（开发环境）
      if (process.env.NODE_ENV === 'development') {
        console.log(`API Response: ${response.config.method?.toUpperCase()} ${response.config.url}`, {
          status: response.status,
          duration: `${duration}ms`,
          data: response.data,
        })
      }

      return response
    },
    (error: AxiosError) => {
      // 统一错误处理
      handleApiError(error)

      return Promise.reject(error)
    }
  )

  return instance
}

// 统一错误处理
const handleApiError = (error: AxiosError<ApiResponse>) => {
  const response = error.response
  const request = error.request

  if (response) {
    // 服务器返回了错误状态码
    const { status, data } = response

    switch (status) {
      case 401:
        // 未授权，清除token并跳转到登录页
        localStorage.removeItem('cbsc_token')
        message.error('登录已过期，请重新登录')
        // 使用react-router进行导航，这里需要根据实际情况调整
        window.location.href = '/login'
        break

      case 403:
        message.error('没有权限访问该资源')
        break

      case 404:
        message.error('请求的资源不存在')
        break

      case 422:
        // 验证错误
        const validationErrors = data?.error?.details
        if (validationErrors && typeof validationErrors === 'object') {
          const errorMessages = Object.entries(validationErrors)
            .map(([field, messages]) => {
              if (Array.isArray(messages)) {
                return `${field}: ${messages.join(', ')}`
              }
              return `${field}: ${messages}`
            })
            .join('; ')
          message.error(`输入验证失败: ${errorMessages}`)
        } else {
          message.error(data?.error?.message || '请求参数不正确')
        }
        break

      case 429:
        message.error('请求过于频繁，请稍后再试')
        break

      case 500:
        message.error('服务器内部错误，请稍后再试')
        break

      case 502:
      case 503:
      case 504:
        message.error('服务暂时不可用，请稍后再试')
        break

      default:
        message.error(data?.error?.message || `请求失败 (${status})`)
    }
  } else if (request) {
    // 请求已发出但没有收到响应
    if (error.code === 'ECONNABORTED') {
      message.error('请求超时，请检查网络连接')
    } else {
      message.error('网络连接失败，请检查网络设置')
    }
  } else {
    // 请求配置出错
    message.error('请求配置错误')
  }

  // 记录详细错误信息（开发环境）
  if (process.env.NODE_ENV === 'development') {
    console.error('API Error Details:', {
      message: error.message,
      code: error.code,
      config: error.config,
      response: error.response?.data,
    })
  }
}

// 创建API实例
export const apiInstance = createApiInstance()

// API请求方法的封装
export class ApiService {
  private instance: AxiosInstance

  constructor(axiosInstance: AxiosInstance = apiInstance) {
    this.instance = axiosInstance
  }

  // GET请求
  async get<T = any>(
    url: string,
    params?: Record<string, any>,
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    const response = await this.instance.get<ApiResponse<T>>(url, {
      params,
      ...config,
    })
    return response.data
  }

  // POST请求
  async post<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    const response = await this.instance.post<ApiResponse<T>>(url, data, config)
    return response.data
  }

  // PUT请求
  async put<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    const response = await this.instance.put<ApiResponse<T>>(url, data, config)
    return response.data
  }

  // PATCH请求
  async patch<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    const response = await this.instance.patch<ApiResponse<T>>(url, data, config)
    return response.data
  }

  // DELETE请求
  async delete<T = any>(
    url: string,
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    const response = await this.instance.delete<ApiResponse<T>>(url, config)
    return response.data
  }

  // 文件上传
  async upload<T = any>(
    url: string,
    file: File,
    additionalData?: Record<string, any>,
    onProgress?: (progress: number) => void
  ): Promise<ApiResponse<T>> {
    const formData = new FormData()
    formData.append('file', file)

    if (additionalData) {
      Object.entries(additionalData).forEach(([key, value]) => {
        formData.append(key, value as string)
      })
    }

    const response = await this.instance.post<ApiResponse<T>>(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      },
    })

    return response.data
  }

  // 文件下载
  async download(
    url: string,
    filename?: string,
    config?: AxiosRequestConfig
  ): Promise<void> {
    const response = await this.instance.get(url, {
      responseType: 'blob',
      ...config,
    })

    // 创建下载链接
    const blob = new Blob([response.data])
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = filename || 'download'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)
  }

  // 设置token
  setAuthToken(token: string) {
    localStorage.setItem('cbsc_token', token)
    this.instance.defaults.headers.Authorization = `Bearer ${token}`
  }

  // 清除token
  clearAuthToken() {
    localStorage.removeItem('cbsc_token')
    delete this.instance.defaults.headers.Authorization
  }

  // 获取当前token
  getAuthToken(): string | null {
    return localStorage.getItem('cbsc_token')
  }

  // 设置基础URL
  setBaseURL(baseURL: string) {
    this.instance.defaults.baseURL = baseURL
  }

  // 设置超时时间
  setTimeout(timeout: number) {
    this.instance.defaults.timeout = timeout
  }

  // 添加请求拦截器
  addRequestInterceptor(
    onFulfilled?: (config: AxiosRequestConfig) => AxiosRequestConfig,
    onRejected?: (error: any) => any
  ): number {
    return this.instance.interceptors.request.use(onFulfilled, onRejected)
  }

  // 添加响应拦截器
  addResponseInterceptor(
    onFulfilled?: (response: AxiosResponse) => AxiosResponse,
    onRejected?: (error: any) => any
  ): number {
    return this.instance.interceptors.response.use(onFulfilled, onRejected)
  }

  // 移除拦截器
  removeInterceptor(interceptorId: number): void {
    this.instance.interceptors.request.eject(interceptorId)
    this.instance.interceptors.response.eject(interceptorId)
  }
}

// 创建默认API服务实例
export const apiService = new ApiService()

// 导出类型和工具函数
export type { AxiosRequestConfig, AxiosResponse, AxiosError }

// API端点常量
export const API_ENDPOINTS = {
  // 认证相关
  AUTH: {
    LOGIN: '/auth/login',
    LOGOUT: '/auth/logout',
    REGISTER: '/auth/register',
    REFRESH: '/auth/refresh',
    ME: '/auth/me',
  },

  // 用户相关
  USERS: {
    LIST: '/users',
    CREATE: '/users',
    DETAIL: (id: string) => `/users/${id}`,
    UPDATE: (id: string) => `/users/${id}`,
    DELETE: (id: string) => `/users/${id}`,
  },

  // 策略相关
  STRATEGIES: {
    LIST: '/strategies',
    CREATE: '/strategies',
    DETAIL: (id: string) => `/strategies/${id}`,
    UPDATE: (id: string) => `/strategies/${id}`,
    DELETE: (id: string) => `/strategies/${id}`,
    EXECUTE: (id: string) => `/strategies/${id}/execute`,
    EXECUTIONS: (id: string) => `/strategies/${id}/executions`,
    SIGNALS: (id: string) => `/strategies/${id}/signals`,
    OPTIMIZE: (id: string) => `/strategies/${id}/optimize`,
    TEMPLATES: '/strategies/templates',
    BATCH: '/strategies/batch',
  },

  // 监控相关
  MONITORING: {
    STATUS: '/monitoring/status',
    HEALTH: '/monitoring/health',
    MARKET_DATA: '/monitoring/market-data',
    ACTIVE_STRATEGIES: '/monitoring/active-strategies',
    EXECUTION_LOGS: '/monitoring/execution-logs',
    PERFORMANCE_METRICS: '/monitoring/performance-metrics',
    ALERTS: '/monitoring/alerts',
    RESOURCE_USAGE: '/monitoring/resource-usage',
    WEBSOCKET_INFO: '/monitoring/websocket-info',
  },

  // 分析相关
  ANALYTICS: {
    DASHBOARD: '/analytics/dashboard',
    PORTFOLIO_PERFORMANCE: '/analytics/portfolio/performance',
    PORTFOLIO_ALLOCATION: '/analytics/portfolio/allocation',
    PORTFOLIO_METRICS: '/analytics/portfolio/metrics',
    STRATEGY_COMPARISON: '/analytics/strategies/comparison',
    STRATEGY_ANALYTICS: (id: string) => `/analytics/strategies/${id}`,
    MARKET_SENTIMENT: '/analytics/market/sentiment',
    MARKET_CORRELATION: '/analytics/market/correlation',
    RISK_ANALYSIS: '/analytics/risk/analysis',
    REPORTS_GENERATE: '/analytics/reports/generate',
    EXPORT: '/analytics/export',
    CUSTOM_QUERY: '/analytics/custom-query',
    SAVED_QUERIES: '/analytics/saved-queries',
  },
} as const

export default apiService
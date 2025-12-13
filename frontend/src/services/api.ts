import axios, { AxiosInstance, AxiosRequestConfig } from 'axios'
import { message } from 'antd'

// API configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3004/api'

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config: any) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers = config.headers || {}
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    if (error.response?.status === 401) {
      // Unauthorized - redirect to login
      localStorage.removeItem('token')
      window.location.href = '/login'
    } else if (error.response?.status >= 500) {
      // Server error
      message.error('服务器错误，请稍后重试')
    } else if (error.response?.data?.message) {
      // API error message
      message.error(error.response.data.message)
    } else if (error.message === 'Network Error') {
      // Network error
      message.error('网络连接失败，请检查网络设置')
    } else {
      // Other errors
      message.error('请求失败，请稍后重试')
    }

    return Promise.reject(error)
  }
)

// API service methods
export const apiService = {
  // Auth endpoints
  auth: {
    login: (credentials: { username: string; password: string }) =>
      api.post('/auth/login', credentials),
    logout: () => api.post('/auth/logout'),
    refreshToken: () => api.post('/auth/refresh'),
    getProfile: () => api.get('/auth/profile'),
  },

  // Strategy endpoints
  strategies: {
    getAll: (params?: any) => api.get('/strategies', { params }),
    getById: (id: string) => api.get(`/strategies/${id}`),
    create: (data: any) => api.post('/strategies', data),
    update: (id: string, data: any) => api.put(`/strategies/${id}`, data),
    delete: (id: string) => api.delete(`/strategies/${id}`),
    run: (id: string, params?: any) => api.post(`/strategies/${id}/run`, params),
    stop: (id: string) => api.post(`/strategies/${id}/stop`),
    getPerformance: (id: string) => api.get(`/strategies/${id}/performance`),
  },

  // Backtest endpoints
  backtest: {
    run: (data: any) => api.post('/backtest/run', data),
    getResults: (id: string) => api.get(`/backtest/results/${id}`),
    getHistory: () => api.get('/backtest/history'),
  },

  // Portfolio endpoints
  portfolio: {
    getOverview: () => api.get('/portfolio'),
    getPositions: () => api.get('/portfolio/positions'),
    getTransactions: (params?: any) => api.get('/portfolio/transactions', { params }),
    rebalance: (data: any) => api.post('/portfolio/rebalance', data),
  },

  // Market data endpoints
  market: {
    getQuote: (symbol: string) => api.get(`/market/quote/${symbol}`),
    getHistorical: (symbol: string, params: any) =>
      api.get(`/market/historical/${symbol}`, { params }),
    search: (query: string) => api.get('/market/search', { params: { q: query } }),
  },

  // Dashboard endpoints
  dashboard: {
    getStats: () => api.get('/dashboard/stats'),
    getRecentActivities: () => api.get('/dashboard/activities'),
  },

  // WebSocket endpoint
  getWebSocketUrl: () => {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsHost = API_BASE_URL.replace(/^https?:/, wsProtocol)
    return `${wsHost}/ws`
  },
}

export default api
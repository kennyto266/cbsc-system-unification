/**
 * CBSC System Adapter
 * Provides integration layer between new Dashboard and existing CBSC system
 */

import axios, { AxiosInstance, AxiosResponse } from 'axios'
import { message } from 'antd'

// Base configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:3004'
const WS_BASE_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:3004'

// API Response interface
interface APIResponse<T = any> {
  success: boolean
  data?: T
  error?: {
    code: string
    message: string
    details?: any
  }
  timestamp: string
}

// CBSC System adapter class
class CBSCAdapter {
  private apiClient: AxiosInstance
  private wsConnection: WebSocket | null = null
  private subscribers: Map<string, Set<Function>> = new Map()

  constructor() {
    // Initialize API client
    this.apiClient = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Request interceptor
    this.apiClient.interceptors.request.use(
      (config) => {
        // Add auth token if available
        const token = localStorage.getItem('cbsc_token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }

        // Add request timestamp
        config.headers['X-Request-Time'] = new Date().toISOString()

        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // Response interceptor
    this.apiClient.interceptors.response.use(
      (response: AxiosResponse<APIResponse>) => {
        const { data } = response

        if (data.success) {
          return response
        } else {
          const error = data.error || { code: 'UNKNOWN_ERROR', message: 'Unknown error' }
          throw new Error(error.message)
        }
      },
      (error) => {
        // Handle network errors
        if (error.response?.status === 401) {
          // Unauthorized - redirect to login
          localStorage.removeItem('cbsc_token')
          window.location.href = '/login'
        } else if (error.response?.status >= 500) {
          message.error('服務器錯誤，請稍後重試')
        } else if (error.code === 'NETWORK_ERROR') {
          message.error('網絡連接失敗，請檢查網絡設置')
        }

        return Promise.reject(error)
      }
    )
  }

  // API Methods
  async get<T = any>(endpoint: string, params?: any): Promise<T> {
    const response = await this.apiClient.get<APIResponse<T>>(endpoint, { params })
    return response.data.data!
  }

  async post<T = any>(endpoint: string, data?: any): Promise<T> {
    const response = await this.apiClient.post<APIResponse<T>>(endpoint, data)
    return response.data.data!
  }

  async put<T = any>(endpoint: string, data?: any): Promise<T> {
    const response = await this.apiClient.put<APIResponse<T>>(endpoint, data)
    return response.data.data!
  }

  async delete<T = any>(endpoint: string): Promise<T> {
    const response = await this.apiClient.delete<APIResponse<T>>(endpoint)
    return response.data.data!
  }

  // WebSocket Methods
  connectWebSocket(endpoint: string = '/ws/strategies'): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const wsUrl = `${WS_BASE_URL}${endpoint}`
        this.wsConnection = new WebSocket(wsUrl)

        this.wsConnection.onopen = () => {
          console.log('CBSC WebSocket connected')
          resolve()
        }

        this.wsConnection.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            this.handleWebSocketMessage(data)
          } catch (error) {
            console.error('Error parsing WebSocket message:', error)
          }
        }

        this.wsConnection.onclose = () => {
          console.log('CBSC WebSocket disconnected')
          this.wsConnection = null
        }

        this.wsConnection.onerror = (error) => {
          console.error('WebSocket error:', error)
          reject(error)
        }
      } catch (error) {
        reject(error)
      }
    })
  }

  disconnectWebSocket() {
    if (this.wsConnection) {
      this.wsConnection.close()
      this.wsConnection = null
    }
  }

  sendWebSocketMessage(message: any) {
    if (this.wsConnection?.readyState === WebSocket.OPEN) {
      this.wsConnection.send(JSON.stringify(message))
    }
  }

  subscribe(channel: string, callback: Function) {
    if (!this.subscribers.has(channel)) {
      this.subscribers.set(channel, new Set())
    }
    this.subscribers.get(channel)!.add(callback)

    // Send subscription message to server
    this.sendWebSocketMessage({
      type: 'subscribe',
      channel,
    })
  }

  unsubscribe(channel: string, callback?: Function) {
    if (this.subscribers.has(channel)) {
      const callbacks = this.subscribers.get(channel)!
      if (callback) {
        callbacks.delete(callback)
      } else {
        callbacks.clear()
      }

      if (callbacks.size === 0) {
        this.subscribers.delete(channel)
        // Send unsubscribe message to server
        this.sendWebSocketMessage({
          type: 'unsubscribe',
          channel,
        })
      }
    }
  }

  private handleWebSocketMessage(data: any) {
    const { channel, message } = data
    if (this.subscribers.has(channel)) {
      this.subscribers.get(channel)!.forEach(callback => {
        try {
          callback(message)
        } catch (error) {
          console.error('Error in WebSocket callback:', error)
        }
      })
    }
  }

  // Specific CBSC API methods
  // Strategies
  async getStrategies() {
    return this.get('/api/v1/strategies')
  }

  async getStrategy(id: string) {
    return this.get(`/api/v1/strategies/${id}`)
  }

  async createStrategy(strategyData: any) {
    return this.post('/api/v1/strategies', strategyData)
  }

  async updateStrategy(id: string, strategyData: any) {
    return this.put(`/api/v1/strategies/${id}`, strategyData)
  }

  async deleteStrategy(id: string) {
    return this.delete(`/api/v1/strategies/${id}`)
  }

  async executeStrategy(id: string, params: any) {
    return this.post(`/api/v1/strategies/${id}/execute`, params)
  }

  // Personal Strategies
  async getPersonalStrategies() {
    return this.get('/api/personal-strategies')
  }

  async createPersonalStrategy(strategyData: any) {
    return this.post('/api/personal-strategies', strategyData)
  }

  // CBSC Strategies
  async getCBSCStrategies() {
    return this.get('/api/strategies')
  }

  async getCBSCData() {
    return this.get('/api/cbsc/data')
  }

  // Technical Indicators
  async getTechnicalIndicators() {
    return this.get('/api/v1/indicators')
  }

  async calculateIndicator(symbol: string, indicator: string, params: any) {
    return this.post('/api/v1/indicators/calculate', {
      symbol,
      indicator,
      params,
    })
  }

  // Market Data
  async getMarketData(symbols?: string[]) {
    return this.get('/api/market/data', { symbols })
  }

  async getRealTimePrices(symbols: string[]) {
    return this.post('/api/market/realtime', { symbols })
  }

  // Portfolio
  async getPortfolio() {
    return this.get('/api/v1/portfolio')
  }

  async getPortfolioPerformance(period: string = '1M') {
    return this.get('/api/v1/portfolio/performance', { period })
  }

  // Analytics
  async getAnalytics(timeRange: string = '1M') {
    return this.get('/api/v1/analytics', { timeRange })
  }

  // Reports
  async getReports() {
    return this.get('/api/v1/reports')
  }

  async generateReport(type: string, params: any) {
    return this.post('/api/v1/reports/generate', { type, params })
  }

  // Health Check
  async healthCheck() {
    return this.get('/health')
  }

  // System Status
  async getSystemStatus() {
    return this.get('/api/v1/system/status')
  }
}

// Create singleton instance
const cbscAdapter = new CBSCAdapter()

export default cbscAdapter

// Export types
export type { APIResponse }

// Export hooks for easy integration
export const useCBSCAdapter = () => {
  return {
    adapter: cbscAdapter,

    // Strategy hooks
    getStrategies: () => cbscAdapter.getStrategies(),
    createStrategy: (data: any) => cbscAdapter.createStrategy(data),

    // Market data hooks
    getMarketData: (symbols?: string[]) => cbscAdapter.getMarketData(symbols),

    // WebSocket hooks
    subscribe: (channel: string, callback: Function) => cbscAdapter.subscribe(channel, callback),
    unsubscribe: (channel: string, callback?: Function) => cbscAdapter.unsubscribe(channel, callback),

    // Health check
    healthCheck: () => cbscAdapter.healthCheck(),
  }
}
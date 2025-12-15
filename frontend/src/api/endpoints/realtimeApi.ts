import { createApi } from '@reduxjs/toolkit/query/react'
import { useAppDispatch } from '../../store/hooks'
import {
  baseQueryWithReauth,
  createApiTag,
} from '../baseQuery'
import type { WebSocketConfig } from '../../types/api'
import * as React from 'react'

// Real-time data API slice
export const realtimeApi = createApi({
  reducerPath: 'realtimeApi',
  baseQuery: baseQueryWithReauth,
  tagTypes: ['WebSocket', 'MarketData', 'Signal', 'Execution', 'Notification', 'Portfolio', 'Performance', 'Risk'],
  keepUnusedDataFor: 5, // Keep real-time data for 5 seconds only
  endpoints: (builder) => ({
    // Get WebSocket connection status
    getWebSocketStatus: builder.query<any, void>({
      query: () => '/websocket/status',
      providesTags: ['WebSocket'],
    }),

    // Initialize WebSocket connection
    initWebSocket: builder.mutation<any, Partial<WebSocketConfig>>({
      query: (config) => ({
        url: '/websocket/init',
        method: 'POST',
        body: config,
      }),
    }),

    // Subscribe to strategy updates
    subscribeToStrategy: builder.mutation<any, {
      strategyId: string
      events?: string[]
    }>({
      query: ({ strategyId, events = ['all'] }) => ({
        url: '/websocket/subscribe/strategy',
        method: 'POST',
        body: { strategyId, events },
      }),
      invalidatesTags: ['WebSocket'],
    }),

    // Unsubscribe from strategy updates
    unsubscribeFromStrategy: builder.mutation<any, string>({
      query: (strategyId) => ({
        url: `/websocket/unsubscribe/strategy/${strategyId}`,
        method: 'POST',
      }),
      invalidatesTags: ['WebSocket'],
    }),

    // Subscribe to market data
    subscribeToMarketData: builder.mutation<any, {
      symbols: string[]
      types?: string[]
    }>({
      query: ({ symbols, types = ['price', 'volume'] }) => ({
        url: '/websocket/subscribe/market',
        method: 'POST',
        body: { symbols, types },
      }),
      invalidatesTags: ['WebSocket', 'MarketData'],
    }),

    // Unsubscribe from market data
    unsubscribeFromMarketData: builder.mutation<any, string[]>({
      query: (symbols) => ({
        url: '/websocket/unsubscribe/market',
        method: 'POST',
        body: { symbols },
      }),
      invalidatesTags: ['WebSocket', 'MarketData'],
    }),

    // Subscribe to notifications
    subscribeToNotifications: builder.mutation<any, {
      types?: string[]
      channels?: string[]
    }>({
      query: ({ types = ['all'], channels = ['all'] }) => ({
        url: '/websocket/subscribe/notifications',
        method: 'POST',
        body: { types, channels },
      }),
      invalidatesTags: ['WebSocket', 'Notification'],
    }),

    // Get market data snapshot
    getMarketDataSnapshot: builder.query<any, {
      symbols: string[]
      fields?: string[]
    }>({
      query: ({ symbols, fields = ['price', 'change', 'volume'] }) => ({
        url: '/market/snapshot',
        params: { symbols: symbols.join(','), fields: fields.join(',') },
      }),
      providesTags: ['MarketData'],
    }),

    // Get historical market data
    getHistoricalData: builder.query<any, {
      symbol: string
      interval: '1m' | '5m' | '15m' | '1h' | '1d'
      start: string
      end: string
      limit?: number
    }>({
      query: ({ symbol, interval, start, end, limit = 1000 }) => ({
        url: `/market/historical/${symbol}`,
        params: { interval, start, end, limit },
      }),
      providesTags: ['MarketData'],
    }),

    // Get real-time strategy execution status
    getExecutionUpdates: builder.query<any[], {
      strategyIds?: string[]
      limit?: number
    }>({
      query: ({ strategyIds, limit = 100 }) => ({
        url: '/execution/updates',
        params: {
          strategyIds: strategyIds?.join(','),
          limit
        },
      }),
      providesTags: ['Execution'],
    }),

    // Get system notifications
    getSystemNotifications: builder.query<any[], {
      limit?: number
      unread?: boolean
      types?: string[]
    }>({
      query: ({ limit = 50, unread = false, types }) => ({
        url: '/notifications',
        params: { limit, unread, types: types?.join(',') },
      }),
      providesTags: ['Notification'],
    }),

    // Mark notification as read
    markNotificationRead: builder.mutation<void, string>({
      query: (notificationId) => ({
        url: `/notifications/${notificationId}/read`,
        method: 'POST',
      }),
      invalidatesTags: ['Notification'],
    }),

    // Get real-time portfolio updates
    getPortfolioUpdates: builder.query<any, string>({
      query: (portfolioId) => `/portfolio/${portfolioId}/updates`,
      providesTags: ['Portfolio'],
    }),

    // Get performance metrics
    getPerformanceMetrics: builder.query<any, {
      strategyId?: string
      portfolioId?: string
      timeframe?: string
    }>({
      query: ({ strategyId, portfolioId, timeframe }) => ({
        url: '/performance/metrics',
        params: { strategyId, portfolioId, timeframe },
      }),
      providesTags: ['Performance'],
    }),

    // Get risk metrics
    getRiskMetrics: builder.query<any, {
      strategyId?: string
      portfolioId?: string
    }>({
      query: ({ strategyId, portfolioId }) => ({
        url: '/risk/metrics',
        params: { strategyId, portfolioId },
      }),
      providesTags: ['Risk'],
    }),

    // Subscribe to risk alerts
    subscribeToRiskAlerts: builder.mutation<any, {
      threshold?: number
      types?: string[]
    }>({
      query: ({ threshold, types = ['all'] }) => ({
        url: '/websocket/subscribe/risk',
        method: 'POST',
        body: { threshold, types },
      }),
      invalidatesTags: ['WebSocket', 'Risk'],
    }),

    // Get market news
    getMarketNews: builder.query<any[], {
      limit?: number
      categories?: string[]
      symbols?: string[]
    }>({
      query: ({ limit = 20, categories, symbols }) => ({
        url: '/market/news',
        params: {
          limit,
          categories: categories?.join(','),
          symbols: symbols?.join(',')
        },
      }),
      providesTags: ['MarketData'],
    }),

    // Get economic calendar
    getEconomicCalendar: builder.query<any[], {
      start?: string
      end?: string
      importance?: string[]
    }>({
      query: ({ start, end, importance }) => ({
        url: '/market/calendar',
        params: {
          start,
          end,
          importance: importance?.join(',')
        },
      }),
      providesTags: ['MarketData'],
    }),

    // Subscribe to economic events
    subscribeToEconomicEvents: builder.mutation<any, {
      importance?: string[]
      types?: string[]
    }>({
      query: ({ importance, types }) => ({
        url: '/websocket/subscribe/calendar',
        method: 'POST',
        body: { importance, types },
      }),
      invalidatesTags: ['WebSocket', 'MarketData'],
    }),
  }),
})

// Export hooks
export const {
  // WebSocket management
  useGetWebSocketStatusQuery,
  useInitWebSocketMutation,
  useSubscribeToStrategyMutation,
  useUnsubscribeFromStrategyMutation,
  useSubscribeToMarketDataMutation,
  useUnsubscribeFromMarketDataMutation,
  useSubscribeToNotificationsMutation,

  // Market data
  useGetMarketDataSnapshotQuery,
  useGetHistoricalDataQuery,
  useGetMarketNewsQuery,
  useGetEconomicCalendarQuery,
  useSubscribeToEconomicEventsMutation,

  // Real-time updates
  useGetExecutionUpdatesQuery,
  useGetSystemNotificationsQuery,
  useGetPortfolioUpdatesQuery,
  useGetPerformanceMetricsQuery,
  useGetRiskMetricsQuery,
  useSubscribeToRiskAlertsMutation,

  // Notifications
  useMarkNotificationReadMutation,
} = realtimeApi

// Custom WebSocket manager class
export class WebSocketManager {
  private ws: WebSocket | null = null
  private config: WebSocketConfig | null = null
  private subscriptions: Map<string, Set<string>> = new Map()
  private messageHandlers: Map<string, Function[]> = new Map()
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private heartbeatInterval: NodeJS.Timeout | null = null

  constructor(private dispatch: any) {}

  async connect(config: WebSocketConfig) {
    this.config = config
    await this.createConnection()
  }

  private async createConnection() {
    if (!this.config) return

    try {
      const url = `${this.config.url}?token=${this.getToken()}`
      this.ws = new WebSocket(url)

      this.ws.onopen = () => {
        console.log('WebSocket connected')
        this.reconnectAttempts = 0
        this.startHeartbeat()
        this.config?.onConnect?.()
      }

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          this.handleMessage(message)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      this.ws.onclose = () => {
        console.log('WebSocket disconnected')
        this.stopHeartbeat()
        this.config?.onDisconnect?.()
        this.attemptReconnect()
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        this.config?.onError?.(error)
      }
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      this.attemptReconnect()
    }
  }

  private getToken(): string {
    const state = this.dispatch((getState: any) => getState())
    return state.auth.token || ''
  }

  private handleMessage(message: any) {
    const { type, data, channel } = message

    // Handle specific message types
    if (this.messageHandlers.has(type)) {
      const handlers = this.messageHandlers.get(type)!
      handlers.forEach(handler => handler(data))
    }

    // Handle channel-specific messages
    if (channel && this.messageHandlers.has(channel)) {
      const handlers = this.messageHandlers.get(channel)!
      handlers.forEach(handler => handler(data))
    }

    // Update Redux store for specific message types
    switch (type) {
      case 'strategy_update':
        this.dispatch({
          type: 'strategy/updateStrategy',
          payload: data,
        })
        break

      case 'execution_update':
        this.dispatch({
          type: 'strategy/addExecutionRecord',
          payload: data,
        })
        break

      case 'market_update':
        this.dispatch({
          type: 'market/updateData',
          payload: data,
        })
        break

      case 'notification':
        this.dispatch({
          type: 'ui/addNotification',
          payload: {
            type: data.severity || 'info',
            title: data.title || 'System Notification',
            message: data.message,
            persistent: data.persistent || false,
          },
        })
        break

      case 'risk_alert':
        this.dispatch({
          type: 'ui/addNotification',
          payload: {
            type: 'warning',
            title: 'Risk Alert',
            message: data.message,
            persistent: true,
          },
        })
        break
    }

    // Call global message handler
    this.config?.onMessage?.(message)
  }

  subscribe(channel: string, handler: Function) {
    if (!this.messageHandlers.has(channel)) {
      this.messageHandlers.set(channel, [])
    }
    this.messageHandlers.get(channel)!.push(handler)

    // Add to subscription tracking
    if (!this.subscriptions.has(channel)) {
      this.subscriptions.set(channel, new Set())
    }
    this.subscriptions.get(channel)!.add(handler.toString())

    return () => {
      this.unsubscribe(channel, handler)
    }
  }

  unsubscribe(channel: string, handler: Function) {
    if (this.messageHandlers.has(channel)) {
      const handlers = this.messageHandlers.get(channel)!
      const index = handlers.indexOf(handler)
      if (index > -1) {
        handlers.splice(index, 1)
      }

      if (this.subscriptions.has(channel)) {
        this.subscriptions.get(channel)!.delete(handler.toString())
      }
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached')
      return
    }

    this.reconnectAttempts++
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)

    setTimeout(() => {
      console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
      this.createConnection()
    }, delay)
  }

  private startHeartbeat() {
    if (this.config?.heartbeatInterval) {
      this.heartbeatInterval = setInterval(() => {
        if (this.ws?.readyState === WebSocket.OPEN) {
          this.ws.send(JSON.stringify({
            type: 'heartbeat',
            timestamp: Date.now(),
          }))
        }
      }, this.config.heartbeatInterval)
    }
  }

  private stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
      this.heartbeatInterval = null
    }
  }

  disconnect() {
    this.stopHeartbeat()
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.subscriptions.clear()
    this.messageHandlers.clear()
  }

  send(message: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket not connected, message not sent:', message)
    }
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }

  getSubscriptionCount(): number {
    return Array.from(this.subscriptions.values())
      .reduce((total, set) => total + set.size, 0)
  }
}

// Utility hooks
export const useWebSocketManager = () => {
  const dispatch = useAppDispatch()
  const managerRef = React.useRef<WebSocketManager | null>(null)

  React.useEffect(() => {
    if (!managerRef.current) {
      managerRef.current = new WebSocketManager(dispatch)
    }

    return () => {
      managerRef.current?.disconnect()
    }
  }, [dispatch])

  return managerRef.current
}
import { io, Socket } from 'socket.io-client'
import type { RootState } from '@store/index'
import type { WebSocketMessage } from '@types/index'

class WebSocketService {
  private socket: Socket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectInterval = 3000
  private store: any
  private subscriptions = new Set<string>()

  constructor() {
    this.setupEventListeners()
  }

  setStore(store: any) {
    this.store = store
  }

  connect(token?: string): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const url = process.env.NODE_ENV === 'production'
          ? `${window.location.protocol}//${window.location.host}/ws`
          : 'http://localhost:3004'

        console.log('Connecting to WebSocket:', url)

        this.socket = io(url, {
          auth: token ? { token } : {},
          transports: ['websocket', 'polling'],
          timeout: 10000,
          reconnection: true,
          reconnectionAttempts: this.maxReconnectAttempts,
          reconnectionDelay: this.reconnectInterval,
        })

        this.socket.on('connect', () => {
          console.log('WebSocket connected successfully')
          this.reconnectAttempts = 0
          this.store?.dispatch({
            type: 'monitoring/setWebSocketConnected',
            payload: true,
          })
          resolve()
        })

        this.socket.on('disconnect', (reason) => {
          console.log('WebSocket disconnected:', reason)
          this.store?.dispatch({
            type: 'monitoring/setWebSocketConnected',
            payload: false,
          })

          if (reason === 'io server disconnect') {
            // Server initiated disconnect, don't reconnect automatically
            this.socket?.disconnect()
          }
        })

        this.socket.on('connect_error', (error) => {
          console.error('WebSocket connection error:', error)
          this.reconnectAttempts++

          if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached')
            this.store?.dispatch({
              type: 'ui/addNotification',
              payload: {
                type: 'error',
                title: 'WebSocket连接失败',
                message: '无法连接到实时数据服务，请检查网络连接或刷新页面',
              },
            })
            reject(error)
          }
        })

        // Handle incoming messages
        this.socket.on('message', (message: WebSocketMessage) => {
          this.handleMessage(message)
        })

        // Handle specific message types
        this.socket.on('performance_update', (data: any) => {
          this.handlePerformanceUpdate(data)
        })

        this.socket.on('signals_update', (data: any) => {
          this.handleSignalsUpdate(data)
        })

        this.socket.on('market_data', (data: any) => {
          this.handleMarketDataUpdate(data)
        })

        this.socket.on('system_status', (data: any) => {
          this.handleSystemStatusUpdate(data)
        })

        this.socket.on('strategy_execution', (data: any) => {
          this.handleStrategyExecutionUpdate(data)
        })

      } catch (error) {
        console.error('Failed to initialize WebSocket:', error)
        reject(error)
      }
    })
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
      this.subscriptions.clear()

      this.store?.dispatch({
        type: 'monitoring/setWebSocketConnected',
        payload: false,
      })
    }
  }

  isConnected(): boolean {
    return this.socket?.connected || false
  }

  subscribe(channel: string) {
    if (!this.subscriptions.has(channel)) {
      this.subscriptions.add(channel)
      this.socket?.emit('subscribe', { channel })
      console.log('Subscribed to channel:', channel)
    }
  }

  unsubscribe(channel: string) {
    if (this.subscriptions.has(channel)) {
      this.subscriptions.delete(channel)
      this.socket?.emit('unsubscribe', { channel })
      console.log('Unsubscribed from channel:', channel)
    }
  }

  sendMessage(message: any) {
    if (this.socket?.connected) {
      this.socket.emit('message', message)
    } else {
      console.warn('WebSocket not connected, cannot send message:', message)
    }
  }

  private setupEventListeners() {
    // Handle page visibility changes
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        // Page is hidden, reduce connection activity
        this.socket?.emit('pause_updates')
      } else {
        // Page is visible, resume connection activity
        this.socket?.emit('resume_updates')
      }
    })

    // Handle page unload
    window.addEventListener('beforeunload', () => {
      this.disconnect()
    })
  }

  private handleMessage(message: WebSocketMessage) {
    // Update last message in store
    this.store?.dispatch({
      type: 'monitoring/setLastMessage',
      payload: message,
    })

    // Route message to appropriate handler
    switch (message.type) {
      case 'performance_update':
        this.handlePerformanceUpdate(message.data)
        break
      case 'signals_update':
        this.handleSignalsUpdate(message.data)
        break
      case 'market_data':
        this.handleMarketDataUpdate(message.data)
        break
      case 'system_status':
        this.handleSystemStatusUpdate(message.data)
        break
      case 'strategy_execution':
        this.handleStrategyExecutionUpdate(message.data)
        break
      default:
        console.warn('Unknown message type:', message.type, message.data)
    }
  }

  private handlePerformanceUpdate(data: any) {
    this.store?.dispatch({
      type: 'monitoring/handlePerformanceUpdate',
      payload: data,
    })

    // Update analytics data if needed
    if (data.portfolio || data.strategies) {
      this.store?.dispatch({
        type: 'analytics/updatePortfolioMetrics',
        payload: data.portfolio || {},
      })
    }
  }

  private handleSignalsUpdate(data: any) {
    if (data.signals && Array.isArray(data.signals)) {
      data.signals.forEach((signal: any) => {
        this.store?.dispatch({
          type: 'strategies/addSignal',
          payload: signal,
        })
      })
    }

    this.store?.dispatch({
      type: 'monitoring/handleSignalsUpdate',
      payload: data,
    })
  }

  private handleMarketDataUpdate(data: any) {
    if (data.symbol && data.data) {
      this.store?.dispatch({
        type: 'monitoring/updateMarketData',
        payload: {
          symbol: data.symbol,
          data: data.data,
        },
      })
    }

    this.store?.dispatch({
      type: 'monitoring/handleMarketDataUpdate',
      payload: {
        symbol: data.symbol,
        data: data.data,
      },
    })
  }

  private handleSystemStatusUpdate(data: any) {
    this.store?.dispatch({
      type: 'monitoring/setSystemStatus',
      payload: data,
    })

    // Show notifications for important status changes
    if (data.status === 'error' || data.status === 'warning') {
      this.store?.dispatch({
        type: 'ui/addNotification',
        payload: {
          type: data.status === 'error' ? 'error' : 'warning',
          title: '系统状态更新',
          message: `系统状态变为${data.status}，请检查系统健康状况`,
        },
      })
    }
  }

  private handleStrategyExecutionUpdate(data: any) {
    if (data.executionId && data.strategyId) {
      this.store?.dispatch({
        type: 'strategies/updateExecution',
        payload: {
          executionId: data.executionId,
          updates: data,
        },
      })
    }

    // Show notifications for execution completion or errors
    if (data.status === 'completed') {
      this.store?.dispatch({
        type: 'ui/addNotification',
        payload: {
          type: 'success',
          title: '策略执行完成',
          message: `策略 ${data.strategyId} 执行完成`,
        },
      })
    } else if (data.status === 'error') {
      this.store?.dispatch({
        type: 'ui/addNotification',
        payload: {
          type: 'error',
          title: '策略执行失败',
          message: `策略 ${data.strategyId} 执行失败: ${data.error}`,
        },
      })
    }

    this.store?.dispatch({
      type: 'monitoring/handleStrategyExecutionUpdate',
      payload: data,
    })
  }

  // Reconnection management
  private attemptReconnection() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      console.log(`Attempting reconnection ${this.reconnectAttempts}/${this.maxReconnectAttempts}`)

      setTimeout(() => {
        const token = this.store?.getState()?.auth?.token
        this.connect(token).catch((error) => {
          console.error('Reconnection failed:', error)
        })
      }, this.reconnectInterval * this.reconnectAttempts)
    }
  }

  // Get connection statistics
  getConnectionStats() {
    return {
      connected: this.isConnected(),
      reconnectAttempts: this.reconnectAttempts,
      subscriptions: Array.from(this.subscriptions),
      socketId: this.socket?.id,
    }
  }
}

// Create singleton instance
const websocketService = new WebSocketService()

export default websocketService

// Export hook for React components
export const useWebSocket = () => {
  const [connectionStats, setConnectionStats] = useState(websocketService.getConnectionStats())

  useEffect(() => {
    const interval = setInterval(() => {
      setConnectionStats(websocketService.getConnectionStats())
    }, 1000)

    return () => clearInterval(interval)
  }, [])

  return {
    connectionStats,
    subscribe: websocketService.subscribe.bind(websocketService),
    unsubscribe: websocketService.unsubscribe.bind(websocketService),
    sendMessage: websocketService.sendMessage.bind(websocketService),
    connect: websocketService.connect.bind(websocketService),
    disconnect: websocketService.disconnect.bind(websocketService),
    isConnected: websocketService.isConnected.bind(websocketService),
  }
}

// Import useState for the hook
import { useState, useEffect } from 'react'
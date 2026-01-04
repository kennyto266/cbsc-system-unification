/**
 * Economic WebSocket Service
 * 經濟數據 WebSocket 服務
 *
 * 提供實時經濟數據推送和連接管理功能
 */

// TypeScript type definitions
export interface EconomicDataUpdate {
  type: 'hibor_update' | 'gdp_update' | 'pmi_update' | 'visitors_update' | 'unemployment_update'
  data: any
  timestamp: string
}

export interface StrategySignalUpdate {
  type: 'strategy_signal'
  data: {
    strategy_id: string
    signal: any
    timestamp: string
  }
}

export interface StrategyStatusUpdate {
  type: 'strategy_status'
  data: {
    strategy_id: string
    status: string
    timestamp: string
  }
}

export type WebSocketMessage = EconomicDataUpdate | StrategySignalUpdate | StrategyStatusUpdate

export type SubscriptionType = 'hibor' | 'gdp' | 'pmi' | 'visitors' | 'unemployment' | 'signals' | 'status'

export interface ConnectionStatus {
  status: 'disconnected' | 'connecting' | 'connected' | 'error'
  lastConnected?: Date
  errorCount: number
}

export interface WebSocketConfig {
  url?: string
  reconnectInterval: number
  maxReconnectAttempts: number
  heartbeatInterval: number
}

/**
 * Economic WebSocket Service Class
 */
class EconomicWebSocketService {
  private ws: WebSocket | null = null
  private subscriptions: Map<SubscriptionType, Set<Function>> = new Map()
  private reconnectAttempts = 0
  private reconnectTimer: NodeJS.Timeout | null = null
  private heartbeatTimer: NodeJS.Timeout | null = null
  private connectionStatus: ConnectionStatus = {
    status: 'disconnected',
    errorCount: 0,
  }

  private readonly config: WebSocketConfig = {
    url: this.getWebSocketUrl(),
    reconnectInterval: 5000, // 5 seconds
    maxReconnectAttempts: 10,
    heartbeatInterval: 30000, // 30 seconds
  }

  /**
   * Get WebSocket URL
   */
  private getWebSocketUrl(): string {
    if (typeof window !== 'undefined') {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const host = import.meta.env.VITE_WS_URL || window.location.host
      return `${protocol}//${host}/ws/economic`
    }
    return 'ws://localhost:3004/ws/economic'
  }

  /**
   * Connect to WebSocket
   */
  async connect(config: Partial<WebSocketConfig> = {}): Promise<WebSocket> {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return this.ws
    }

    if (this.ws && this.ws.readyState === WebSocket.CONNECTING) {
      return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error('Connection timeout'))
        }, 10000)

        const checkConnection = () => {
          if (this.ws?.readyState === WebSocket.OPEN) {
            clearTimeout(timeout)
            resolve(this.ws)
          } else if (this.ws?.readyState === WebSocket.CLOSED) {
            clearTimeout(timeout)
            reject(new Error('Connection failed'))
          } else {
            setTimeout(checkConnection, 100)
          }
        }
        checkConnection()
      })
    }

    this.config.url = config.url || this.config.url
    Object.assign(this.config, config)

    this.updateConnectionStatus('connecting')

    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.config.url!)

        this.ws.onopen = (event) => {
          console.log('WebSocket connected')
          this.reconnectAttempts = 0
          this.updateConnectionStatus('connected')
          this.startHeartbeat()
          this.resubscribeAll()
          resolve(this.ws!)
        }

        this.ws.onclose = (event) => {
          console.log('WebSocket disconnected', event.code, event.reason)
          this.updateConnectionStatus('disconnected')
          this.stopHeartbeat()
          this.handleReconnect()
        }

        this.ws.onmessage = (event) => {
          this.handleMessage(event.data)
        }

        this.ws.onerror = (event) => {
          console.error('WebSocket error:', event)
          this.connectionStatus.errorCount++
          this.updateConnectionStatus('error')
          reject(new Error('WebSocket connection error'))
        }

      } catch (error) {
        reject(error)
      }
    })
  }

  /**
   * Disconnect from WebSocket
   */
  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }

    this.stopHeartbeat()

    if (this.ws) {
      this.ws.close()
      this.ws = null
    }

    this.updateConnectionStatus('disconnected')
    this.subscriptions.clear()
  }

  /**
   * Subscribe to economic data updates
   */
  subscribe(type: SubscriptionType, callback: (data: any) => void): void {
    if (!this.isValidSubscriptionType(type)) {
      console.error(`Invalid subscription type: ${type}`)
      return
    }

    if (!this.subscriptions.has(type)) {
      this.subscriptions.set(type, new Set())
    }

    this.subscriptions.get(type)!.add(callback)

    // Send subscription message if connected
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.sendSubscriptionMessage(type, 'subscribe')
    }
  }

  /**
   * Unsubscribe from economic data updates
   */
  unsubscribe(type: SubscriptionType, callback: (data: any) => void): void {
    const callbacks = this.subscriptions.get(type)
    if (callbacks) {
      callbacks.delete(callback)
      if (callbacks.size === 0) {
        this.subscriptions.delete(type)
        // Send unsubscribe message if connected
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
          this.sendSubscriptionMessage(type, 'unsubscribe')
        }
      }
    }
  }

  /**
   * Get connection status
   */
  getConnectionStatus(): ConnectionStatus['status'] {
    return this.connectionStatus.status
  }

  /**
   * Get detailed connection info
   */
  getConnectionInfo(): ConnectionStatus {
    return { ...this.connectionStatus }
  }

  /**
   * Reconnect to WebSocket
   */
  async reconnect(): Promise<void> {
    if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached')
      return
    }

    this.reconnectAttempts++
    const delay = Math.min(
      this.config.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1),
      30000 // Max 30 seconds
    )

    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`)

    this.reconnectTimer = setTimeout(async () => {
      try {
        await this.connect()
      } catch (error) {
        console.error('Reconnection failed:', error)
        this.reconnect()
      }
    }, delay)
  }

  /**
   * Send message to WebSocket
   */
  private send(data: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }

  /**
   * Send subscription message
   */
  private sendSubscriptionMessage(type: SubscriptionType, action: 'subscribe' | 'unsubscribe'): void {
    this.send({
      type: 'subscription',
      action,
      data: { type },
    })
  }

  /**
   * Handle incoming message
   */
  private handleMessage(data: string): void {
    try {
      const message: WebSocketMessage = JSON.parse(data)

      switch (message.type) {
        case 'hibor_update':
        case 'gdp_update':
        case 'pmi_update':
        case 'visitors_update':
        case 'unemployment_update':
          this.notifySubscribers(this.getSubscriptionTypeFromUpdate(message.type), message.data)
          break

        case 'strategy_signal':
          this.notifySubscribers('signals', message.data)
          break

        case 'strategy_status':
          this.notifySubscribers('status', message.data)
          break

        default:
          console.warn('Unknown message type:', message.type)
      }
    } catch (error) {
      console.error('Error parsing WebSocket message:', error)
    }
  }

  /**
   * Notify subscribers
   */
  private notifySubscribers(type: SubscriptionType, data: any): void {
    const callbacks = this.subscriptions.get(type)
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(data)
        } catch (error) {
          console.error('Error in subscription callback:', error)
        }
      })
    }
  }

  /**
   * Resubscribe to all subscriptions after reconnection
   */
  private resubscribeAll(): void {
    this.subscriptions.forEach((_, type) => {
      this.sendSubscriptionMessage(type, 'subscribe')
    })
  }

  /**
   * Start heartbeat
   */
  private startHeartbeat(): void {
    this.heartbeatTimer = setInterval(() => {
      this.send({ type: 'ping', timestamp: Date.now() })
    }, this.config.heartbeatInterval)
  }

  /**
   * Stop heartbeat
   */
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  /**
   * Handle reconnection logic
   */
  private handleReconnect(): void {
    if (this.reconnectAttempts === 0) {
      this.reconnect()
    }
  }

  /**
   * Update connection status
   */
  private updateConnectionStatus(status: ConnectionStatus['status']): void {
    this.connectionStatus.status = status
    if (status === 'connected') {
      this.connectionStatus.lastConnected = new Date()
    }
  }

  /**
   * Check if subscription type is valid
   */
  private isValidSubscriptionType(type: string): type is SubscriptionType {
    return ['hibor', 'gdp', 'pmi', 'visitors', 'unemployment', 'signals', 'status'].includes(type)
  }

  /**
   * Get subscription type from update message type
   */
  private getSubscriptionTypeFromUpdate(updateType: string): SubscriptionType {
    const mapping: Record<string, SubscriptionType> = {
      hibor_update: 'hibor',
      gdp_update: 'gdp',
      pmi_update: 'pmi',
      visitors_update: 'visitors',
      unemployment_update: 'unemployment',
    }
    return mapping[updateType] || 'signals'
  }

  /**
   * Get subscription count
   */
  getSubscriptionCount(): number {
    let total = 0
    this.subscriptions.forEach(callbacks => {
      total += callbacks.size
    })
    return total
  }

  /**
   * Get active subscriptions
   */
  getActiveSubscriptions(): SubscriptionType[] {
    return Array.from(this.subscriptions.keys())
  }
}

// Export singleton instance
export const economicWebSocket = new EconomicWebSocketService()

// Export types
export type {
  EconomicDataUpdate,
  StrategySignalUpdate,
  StrategyStatusUpdate,
  WebSocketMessage,
  SubscriptionType,
  ConnectionStatus,
  WebSocketConfig,
}
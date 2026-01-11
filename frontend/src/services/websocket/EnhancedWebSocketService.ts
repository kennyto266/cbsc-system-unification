/**
 * Enhanced WebSocket Service
 * Provides real-time data streaming with automatic reconnection, caching, and performance optimization
 */

import {
  WSMessage,
  MessageType,
  ChannelType,
  ConnectionState,
  WebSocketConfig,
  ConnectionMetrics,
  SubscriptionRequest,
  WebSocketEventCallbacks,
  IWebSocketService
} from '../../types/websocket'

import { wsManager } from '../websocketManager'

// Default configuration
const DEFAULT_CONFIG: Partial<WebSocketConfig> = {
  url: 'ws://localhost:3004/ws',
  reconnectAttempts: 5,
  reconnectDelay: 1000,
  heartbeatInterval: 30000,
  connectionTimeout: 5000,
  enableLogging: true,
  bufferSize: 1000,
  throttleMessages: true
}

export class EnhancedWebSocketService implements IWebSocketService {
  private config: WebSocketConfig
  private state: ConnectionState = ConnectionState.DISCONNECTED
  private metrics: ConnectionMetrics = {
    reconnectCount: 0,
    messagesReceived: 0,
    messagesSent: 0,
    bytesReceived: 0,
    bytesSent: 0,
    errorCount: 0
  }
  private subscriptions: Map<string, Set<(data: any) => void>> = new Map()
  private callbacks: WebSocketEventCallbacks = {}
  private messageCache: Map<string, any> = new Map()
  private cacheTimestamps: Map<string, number> = new Map()
  private throttleMap: Map<string, number> = new Map()
  private reconnectTimer: NodeJS.Timeout | null = null
  private heartbeatTimer: NodeJS.Timeout | null = null

  constructor(config: Partial<WebSocketConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config } as WebSocketConfig
    this.setupEventListeners()
  }

  /**
   * Establish WebSocket connection
   */
  async connect(): Promise<void> {
    if (this.state === ConnectionState.CONNECTED || this.state === ConnectionState.CONNECTING) {
      return
    }

    this.setState(ConnectionState.CONNECTING)
    this.log('Attempting to connect to WebSocket...')

    try {
      await wsManager.connect()
      this.setState(ConnectionState.CONNECTED)
      this.metrics.connectedAt = Date.now()
      this.startHeartbeat()
      this.log('Connected successfully')
      this.callbacks.onConnect?.()
    } catch (error) {
      this.setState(ConnectionState.ERROR)
      this.metrics.errorCount++
      this.log('Connection failed:', error)
      this.callbacks.onError?.(error as Error)
      this.attemptReconnect()
    }
  }

  /**
   * Close WebSocket connection
   */
  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }

    this.stopHeartbeat()
    wsManager.disconnect()
    this.setState(ConnectionState.DISCONNECTED)
    this.subscriptions.clear()
    this.log('Disconnected manually')
    this.callbacks.onDisconnect?.(1000, 'Manual disconnect')
  }

  /**
   * Send a message through WebSocket
   */
  send(message: WSMessage): boolean {
    if (this.state !== ConnectionState.CONNECTED) {
      this.log('Cannot send message - not connected')
      return false
    }

    // Throttle messages if enabled
    if (this.config.throttleMessages) {
      const key = `${message.type}_${message.channel || ''}`
      if (this.isThrottled(key)) {
        return false
      }
      this.throttleMap.set(key, Date.now())
    }

    try {
      wsManager.send(message.type, message.data)
      this.metrics.messagesSent++
      this.metrics.bytesSent += JSON.stringify(message).length
      return true
    } catch (error) {
      this.metrics.errorCount++
      this.log('Failed to send message:', error)
      return false
    }
  }

  /**
   * Subscribe to a specific channel
   */
  subscribe(
    channel: ChannelType,
    callback: (data: any) => void,
    filters?: Record<string, any>
  ): () => void {
    const subscriptionKey = `${channel}_${JSON.stringify(filters || {})}`

    if (!this.subscriptions.has(subscriptionKey)) {
      this.subscriptions.set(subscriptionKey, new Set())

      // Send subscription request to server
      this.send({
        id: this.generateMessageId(),
        type: MessageType.SUBSCRIBE,
        channel,
        data: filters,
        timestamp: Date.now()
      })
    }

    this.subscriptions.get(subscriptionKey)!.add(callback)

    // Return unsubscribe function
    return () => {
      const callbacks = this.subscriptions.get(subscriptionKey)
      if (callbacks) {
        callbacks.delete(callback)
        if (callbacks.size === 0) {
          this.subscriptions.delete(subscriptionKey)
          this.send({
            id: this.generateMessageId(),
            type: MessageType.UNSUBSCRIBE,
            channel,
            timestamp: Date.now()
          })
        }
      }
    }
  }

  /**
   * Unsubscribe from a channel
   */
  unsubscribe(channel: ChannelType): void {
    // Find and remove all subscriptions for this channel
    for (const [key, callbacks] of this.subscriptions.entries()) {
      if (key.startsWith(channel)) {
        callbacks.clear()
        this.subscriptions.delete(key)
      }
    }

    this.send({
      id: this.generateMessageId(),
      type: MessageType.UNSUBSCRIBE,
      channel,
      timestamp: Date.now()
    })
  }

  /**
   * Get current connection state
   */
  getConnectionState(): ConnectionState {
    return this.state
  }

  /**
   * Get connection metrics
   */
  getConnectionMetrics(): ConnectionMetrics {
    return { ...this.metrics }
  }

  /**
   * Get network status (placeholder for actual implementation)
   */
  getNetworkStatus(): any {
    if (typeof navigator !== 'undefined' && 'connection' in navigator) {
      const connection = (navigator as any).connection
      return {
        online: navigator.onLine,
        effectiveType: connection?.effectiveType,
        downlink: connection?.downlink,
        rtt: connection?.rtt,
        saveData: connection?.saveData
      }
    }
    return {
      online: navigator.onLine
    }
  }

  /**
   * Evaluate connection quality based on metrics
   */
  getConnectionQuality(): 'excellent' | 'good' | 'fair' | 'poor' {
    const { latency } = this.metrics
    if (!latency) return 'unknown'

    if (latency < 50) return 'excellent'
    if (latency < 150) return 'good'
    if (latency < 300) return 'fair'
    return 'poor'
  }

  /**
   * Add event listener
   */
  addEventListener<K extends keyof WebSocketEventCallbacks>(
    event: K,
    callback: WebSocketEventCallbacks[K]
  ): void {
    this.callbacks[event] = callback
  }

  /**
   * Remove event listener
   */
  removeEventListener<K extends keyof WebSocketEventCallbacks>(
    event: K,
    callback: WebSocketEventCallbacks[K]
  ): void {
    if (this.callbacks[event] === callback) {
      delete this.callbacks[event]
    }
  }

  /**
   * Get cached data for a channel
   */
  getCachedData<T = any>(channel: string, maxAge: number = 60000): T | null {
    const timestamp = this.cacheTimestamps.get(channel)
    const data = this.messageCache.get(channel)

    if (timestamp && data && Date.now() - timestamp < maxAge) {
      return data
    }

    return null
  }

  /**
   * Cache data for a channel
   */
  cacheData(channel: string, data: any): void {
    this.messageCache.set(channel, data)
    this.cacheTimestamps.set(channel, Date.now())

    // Clean up old cache entries
    this.cleanCache()
  }

  // Private methods

  private setupEventListeners(): void {
    // Subscribe to WebSocket manager events
    wsManager.subscribe('strategy_update', (data) => {
      this.handleMessage({
        id: this.generateMessageId(),
        type: MessageType.STRATEGY_UPDATE,
        channel: ChannelType.STRATEGY_UPDATES,
        data,
        timestamp: Date.now()
      })
    })

    wsManager.subscribe('price_feed', (data) => {
      this.handleMessage({
        id: this.generateMessageId(),
        type: MessageType.PRICE_FEED,
        channel: ChannelType.PRICE_FEEDS,
        data,
        timestamp: Date.now()
      })
    })

    wsManager.subscribe('notification', (data) => {
      this.handleMessage({
        id: this.generateMessageId(),
        type: MessageType.NOTIFICATION,
        channel: ChannelType.NOTIFICATIONS,
        data,
        timestamp: Date.now()
      })
    })

    wsManager.subscribe('pong', () => {
      this.handlePong()
    })
  }

  private handleMessage(message: WSMessage): void {
    // Update metrics
    this.metrics.messagesReceived++
    this.metrics.bytesReceived += JSON.stringify(message).length

    // Cache important messages
    if (message.channel) {
      this.cacheData(message.channel, message.data)
    }

    // Notify subscribers
    if (message.channel) {
      const callbacks = this.subscriptions.get(message.channel)
      if (callbacks) {
        callbacks.forEach(callback => {
          try {
            callback(message.data)
          } catch (error) {
            console.error('Error in subscription callback:', error)
          }
        })
      }
    }

    // Global message handler
    this.callbacks.onMessage?.(message)
  }

  private handlePong(): void {
    this.metrics.lastPongTime = Date.now()
    if (this.metrics.lastPingTime) {
      this.metrics.latency = this.metrics.lastPongTime - this.metrics.lastPingTime
      this.callbacks.onLatencyUpdate?.(this.metrics.latency)
    }
  }

  private setState(newState: ConnectionState): void {
    const oldState = this.state
    this.state = newState
    this.callbacks.onStateChange?.(oldState, newState)
  }

  private startHeartbeat(): void {
    this.stopHeartbeat()
    this.heartbeatTimer = setInterval(() => {
      this.metrics.lastPingTime = Date.now()
      this.send({
        id: this.generateMessageId(),
        type: MessageType.PING,
        timestamp: Date.now()
      })
    }, this.config.heartbeatInterval!)
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  private attemptReconnect(): void {
    if (this.metrics.reconnectCount >= this.config.reconnectAttempts!) {
      this.log('Max reconnection attempts reached')
      this.setState(ConnectionState.ERROR)
      return
    }

    this.setState(ConnectionState.RECONNECTING)
    this.metrics.reconnectCount++

    const delay = this.config.reconnectDelay! * Math.pow(2, this.metrics.reconnectCount - 1)
    this.log(`Reconnecting in ${delay}ms... (attempt ${this.metrics.reconnectCount})`)

    this.callbacks.onReconnect?.(this.metrics.reconnectCount)

    this.reconnectTimer = setTimeout(() => {
      this.connect()
    }, delay)
  }

  private isThrottled(key: string): boolean {
    const lastSent = this.throttleMap.get(key)
    return lastSent ? Date.now() - lastSent < 100 : false
  }

  private generateMessageId(): string {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  private cleanCache(): void {
    const now = Date.now()
    const maxAge = 300000 // 5 minutes

    for (const [channel, timestamp] of this.cacheTimestamps.entries()) {
      if (now - timestamp > maxAge) {
        this.messageCache.delete(channel)
        this.cacheTimestamps.delete(channel)
      }
    }
  }

  private log(...args: any[]): void {
    if (this.config.enableLogging) {
      console.log('[EnhancedWebSocketService]', ...args)
    }
  }
}

// Create singleton instance
export const enhancedWS = new EnhancedWebSocketService()
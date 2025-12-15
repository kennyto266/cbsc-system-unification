// WebSocket utilities and manager
import * as React from 'react'

export interface WebSocketMessage {
  type: string
  data?: any
  channel?: string
  timestamp: number
  id?: string
  filters?: Record<string, any>
}

export interface WebSocketSubscription {
  channel: string
  handler: (message: WebSocketMessage) => void
  filters?: Record<string, any>
}

export interface WebSocketConfig {
  url: string
  protocols?: string[]
  reconnectInterval?: number
  maxReconnectAttempts?: number
  heartbeatInterval?: number
  heartbeatMessage?: any
  onMessage?: (message: WebSocketMessage) => void
  onConnect?: () => void
  onDisconnect?: () => void
  onError?: (error: Event) => void
}

export class WebSocketManager {
  private ws: WebSocket | null = null
  private config: WebSocketConfig | null = null
  private subscriptions: Map<string, Set<WebSocketSubscription>> = new Map()
  private reconnectAttempts = 0
  private heartbeatInterval: NodeJS.Timeout | null = null
  private messageQueue: WebSocketMessage[] = []
  private isConnecting = false

  // Public getter for isConnecting
  public getIsConnecting(): boolean {
    return this.isConnecting
  }
  private reconnectTimeout: NodeJS.Timeout | null = null

  constructor() {}

  connect(config: WebSocketConfig): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.isConnecting || this.isConnected()) {
        resolve()
        return
      }

      this.config = config
      this.isConnecting = true

      try {
        this.ws = new WebSocket(config.url, config.protocols)

        this.ws.onopen = () => {
          console.log('WebSocket connected')
          this.isConnecting = false
          this.reconnectAttempts = 0
          this.startHeartbeat()
          this.processMessageQueue()
          this.config?.onConnect?.()
          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data)
            this.handleMessage(message)
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error)
          }
        }

        this.ws.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason)
          this.isConnecting = false
          this.stopHeartbeat()
          this.config?.onDisconnect?.()
          this.attemptReconnect()
        }

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error)
          this.isConnecting = false
          this.config?.onError?.(error)
          reject(error)
        }
      } catch (error) {
        this.isConnecting = false
        reject(error)
      }
    })
  }

  disconnect(): void {
    this.stopReconnectAttempts()
    this.stopHeartbeat()

    if (this.ws) {
      this.ws.close(1000, 'User disconnect')
      this.ws = null
    }

    this.subscriptions.clear()
    this.messageQueue = []
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }

  send(message: WebSocketMessage | string): boolean {
    if (!this.isConnected()) {
      // Queue message for when connection is established
      if (typeof message === 'string') {
        try {
          message = JSON.parse(message)
        } catch (e) {
          console.error('Failed to parse message for queueing:', e)
          return false
        }
      }

      this.messageQueue.push({
        ...message,
        timestamp: Date.now(),
      })
      return false
    }

    try {
      const payload = typeof message === 'string' ? message : JSON.stringify(message)
      this.ws!.send(payload)
      return true
    } catch (error) {
      console.error('Failed to send WebSocket message:', error)
      return false
    }
  }

  subscribe(subscription: WebSocketSubscription): () => void {
    const { channel, handler, filters } = subscription

    if (!this.subscriptions.has(channel)) {
      this.subscriptions.set(channel, new Set())
    }

    const subscriptionWithFilters = {
      channel,
      handler,
      filters,
    }

    this.subscriptions.get(channel)!.add(subscriptionWithFilters)

    // Send subscription message to server if needed
    this.send({
      type: 'subscribe',
      channel,
      filters,
      timestamp: Date.now(),
    })

    // Return unsubscribe function
    return () => this.unsubscribe(subscription)
  }

  unsubscribe(subscription: Partial<WebSocketSubscription>): void {
    const { channel, handler } = subscription

    if (!channel) return

    const channelSubscriptions = this.subscriptions.get(channel)
    if (!channelSubscriptions) return

    // Find and remove matching subscriptions
    for (const sub of channelSubscriptions) {
      if (!handler || sub.handler === handler) {
        channelSubscriptions.delete(sub)
      }
    }

    // Remove channel if no subscriptions left
    if (channelSubscriptions.size === 0) {
      this.subscriptions.delete(channel)

      // Send unsubscribe message to server
      this.send({
        type: 'unsubscribe',
        channel,
        timestamp: Date.now(),
      })
    }
  }

  unsubscribeAll(): void {
    for (const [channel] of this.subscriptions) {
      this.unsubscribe({ channel })
    }
  }

  getSubscriptions(): Map<string, number> {
    const counts = new Map<string, number>()
    for (const [channel, subs] of this.subscriptions) {
      counts.set(channel, subs.size)
    }
    return counts
  }

  private handleMessage(message: WebSocketMessage): void {
    // Call global message handler
    this.config?.onMessage?.(message)

    // Call channel-specific handlers
    const channelSubscriptions = this.subscriptions.get(message.channel || '')
    if (channelSubscriptions) {
      for (const subscription of channelSubscriptions) {
        // Apply filters if present
        if (subscription.filters && !this.matchesFilters(message, subscription.filters)) {
          continue
        }

        try {
          subscription.handler(message)
        } catch (error) {
          console.error('Error in WebSocket subscription handler:', error)
        }
      }
    }
  }

  private matchesFilters(message: WebSocketMessage, filters: Record<string, any>): boolean {
    for (const [key, value] of Object.entries(filters)) {
      const messageValue = (message as any)[key]
      if (value !== messageValue &&
          !(Array.isArray(value) && value.includes(messageValue))) {
        return false
      }
    }
    return true
  }

  private startHeartbeat(): void {
    if (!this.config?.heartbeatInterval) return

    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected()) {
        const message = this.config.heartbeatMessage || {
          type: 'heartbeat',
          timestamp: Date.now(),
        }
        this.send(message)
      }
    }, this.config.heartbeatInterval)
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
      this.heartbeatInterval = null
    }
  }

  private attemptReconnect(): void {
    if (!this.config || this.reconnectAttempts >= (this.config.maxReconnectAttempts || 5)) {
      console.error('Max reconnection attempts reached')
      return
    }

    this.reconnectAttempts++
    const delay = (this.config.reconnectInterval || 1000) * Math.pow(2, this.reconnectAttempts - 1)

    console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.config.maxReconnectAttempts})`)

    this.reconnectTimeout = setTimeout(() => {
      if (this.config) {
        this.connect(this.config).catch((error) => {
          console.error('Reconnection failed:', error)
          this.attemptReconnect()
        })
      }
    }, delay)
  }

  private stopReconnectAttempts(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout)
      this.reconnectTimeout = null
    }
    this.reconnectAttempts = 0
  }

  private processMessageQueue(): void {
    while (this.messageQueue.length > 0 && this.isConnected()) {
      const message = this.messageQueue.shift()!
      this.send(message)
    }
  }
}

// Singleton WebSocket manager
export const wsManager = new WebSocketManager()

// Hook for using WebSocket manager
export function useWebSocket() {
  const [isConnected, setIsConnected] = React.useState(false)
  const [subscriptions, setSubscriptions] = React.useState<Map<string, number>>(new Map())

  React.useEffect(() => {
    const checkConnection = () => {
      setIsConnected(wsManager.isConnected())
      setSubscriptions(wsManager.getSubscriptions())
    }

    const interval = setInterval(checkConnection, 1000)
    checkConnection()

    return () => clearInterval(interval)
  }, [])

  const connect = React.useCallback((config: WebSocketConfig) => {
    return wsManager.connect(config)
  }, [])

  const disconnect = React.useCallback(() => {
    wsManager.disconnect()
  }, [])

  const subscribe = React.useCallback((subscription: WebSocketSubscription) => {
    const unsubscribe = wsManager.subscribe(subscription)
    setSubscriptions(wsManager.getSubscriptions())
    return unsubscribe
  }, [])

  const send = React.useCallback((message: WebSocketMessage | string) => {
    return wsManager.send(message)
  }, [])

  return {
    isConnected,
    subscriptions,
    connect,
    disconnect,
    subscribe,
    send,
  }
}

// Predefined subscription handlers
export const createStrategySubscription = (callback: (data: any) => void) => {
  return {
    channel: 'strategy-updates',
    handler: (message) => {
      if (message.channel === 'strategy-updates' && message.data) {
        callback(message.data)
      }
    },
  }
}

export const createMarketDataSubscription = (callback: (data: any) => void, symbols?: string[]) => {
  return {
    channel: 'market-data',
    filters: symbols ? { symbols } : undefined,
    handler: (message) => {
      if (message.channel === 'market-data' && message.data) {
        callback(message.data)
      }
    },
  }
}

export const createNotificationSubscription = (callback: (data: any) => void) => {
  return {
    channel: 'notifications',
    handler: (message) => {
      if (message.channel === 'notifications' && message.data) {
        callback(message.data)
      }
    },
  }
}

// WebSocket connection status hook
export function useWebSocketStatus() {
  const [status, setStatus] = React.useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected')
  const [lastError, setLastError] = React.useState<string | null>(null)

  React.useEffect(() => {
    let checkCount = 0

    const checkStatus = () => {
      checkCount++

      if (wsManager.isConnected()) {
        setStatus('connected')
        setLastError(null)
      } else if (wsManager.getIsConnecting()) {
        setStatus('connecting')
        setLastError(null)
      } else {
        if (checkCount > 5) {
          setStatus('error')
          setLastError('Connection failed')
        } else {
          setStatus('disconnected')
        }
      }
    }

    const interval = setInterval(checkStatus, 1000)
    return () => clearInterval(interval)
  }, [])

  return { status, lastError }
}

// WebSocket message queue for offline scenarios
export class WebSocketMessageQueue {
  private queue: WebSocketMessage[] = []
  private maxSize: number
  private storageKey: string

  constructor(maxSize: number = 1000, storageKey: string = 'ws_message_queue') {
    this.maxSize = maxSize
    this.storageKey = storageKey
    this.loadFromStorage()
  }

  add(message: WebSocketMessage): void {
    this.queue.push({ ...message, id: this.generateId() })

    // Keep queue within max size
    if (this.queue.length > this.maxSize) {
      this.queue.shift()
    }

    this.saveToStorage()
  }

  remove(id: string): WebSocketMessage | null {
    const index = this.queue.findIndex(msg => msg.id === id)
    if (index !== -1) {
      const message = this.queue.splice(index, 1)[0]
      this.saveToStorage()
      return message
    }
    return null
  }

  clear(): void {
    this.queue = []
    this.saveToStorage()
  }

  getAll(): WebSocketMessage[] {
    return [...this.queue]
  }

  private generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  }

  private saveToStorage(): void {
    try {
      localStorage.setItem(this.storageKey, JSON.stringify(this.queue))
    } catch (error) {
      console.warn('Failed to save WebSocket queue to storage:', error)
    }
  }

  private loadFromStorage(): void {
    try {
      const stored = localStorage.getItem(this.storageKey)
      if (stored) {
        this.queue = JSON.parse(stored)
      }
    } catch (error) {
      console.warn('Failed to load WebSocket queue from storage:', error)
    }
  }
}
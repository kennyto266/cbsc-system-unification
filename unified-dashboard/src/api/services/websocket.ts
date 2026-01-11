/**
 * WebSocket Service
 * Manages WebSocket connections for real-time data
 */

import { API_CONFIG, API_ENDPOINTS, WS_CHANNELS } from '../config'
import { WebSocketMessage, Notification } from '../types/common'
import { MarketPrice, TradeData, OrderBookUpdate, StrategyUpdate } from '../types/market'

// WebSocket event types
export type WSEventType = 'open' | 'close' | 'error' | 'message'

// WebSocket subscription types
export type SubscriptionType =
  | 'market_price'
  | 'market_trades'
  | 'market_depth'
  | 'strategy_updates'
  | 'system_notifications'
  | 'order_updates'

// Message handler type
export type MessageHandler<T = any> = (data: T) => void

// Connection status
export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'reconnecting'

class WebSocketService {
  private ws: WebSocket | null = null
  private url: string
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectInterval = 1000
  private heartbeatInterval: NodeJS.Timeout | null = null
  private messageQueue: any[] = []
  private subscriptions = new Map<string, Set<MessageHandler>>()
  private connectionStatus: ConnectionStatus = 'disconnected'
  private eventListeners = new Map<WSEventType, Set<Function>>()

  constructor() {
    this.url = API_CONFIG.wsURL
  }

  /**
   * Connect to WebSocket server
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        resolve()
        return
      }

      this.connectionStatus = 'connecting'
      this.ws = new WebSocket(this.url)

      this.ws.onopen = () => {
        console.log('WebSocket connected')
        this.connectionStatus = 'connected'
        this.reconnectAttempts = 0
        this.startHeartbeat()
        this.processMessageQueue()
        this.emit('open')
        resolve()
      }

      this.ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason)
        this.connectionStatus = 'disconnected'
        this.stopHeartbeat()
        this.emit('close', event)

        if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect()
        }
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        this.connectionStatus = 'disconnected'
        this.emit('error', error)
        reject(error)
      }

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          this.handleMessage(message)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }
    })
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.stopHeartbeat()
    this.connectionStatus = 'disconnected'
    this.subscriptions.clear()
    this.messageQueue = []
  }

  /**
   * Subscribe to a channel
   */
  subscribe<T = any>(channel: string, handler: MessageHandler<T>): void {
    if (!this.subscriptions.has(channel)) {
      this.subscriptions.set(channel, new Set())
    }
    this.subscriptions.get(channel)!.add(handler)

    // Send subscription message if connected
    if (this.connectionStatus === 'connected') {
      this.send({
        type: 'subscribe',
        channel,
        data: null,
      })
    }
  }

  /**
   * Unsubscribe from a channel
   */
  unsubscribe(channel: string, handler?: MessageHandler): void {
    if (handler) {
      this.subscriptions.get(channel)?.delete(handler)
    } else {
      this.subscriptions.delete(channel)
    }

    // Send unsubscribe message if connected
    if (this.connectionStatus === 'connected') {
      this.send({
        type: 'unsubscribe',
        channel,
        data: null,
      })
    }
  }

  /**
   * Send a message to the server
   */
  send(data: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    } else {
      this.messageQueue.push(data)
    }
  }

  /**
   * Add event listener
   */
  on(event: WSEventType, listener: Function): void {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, new Set())
    }
    this.eventListeners.get(event)!.add(listener)
  }

  /**
   * Remove event listener
   */
  off(event: WSEventType, listener: Function): void {
    this.eventListeners.get(event)?.delete(listener)
  }

  /**
   * Get connection status
   */
  getStatus(): ConnectionStatus {
    return this.connectionStatus
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.connectionStatus === 'connected'
  }

  // Private methods

  private handleMessage(message: WebSocketMessage): void {
    // Handle system messages
    if (message.type === 'system') {
      if (message.data.type === 'pong') {
        // Handle pong response
        return
      }
    }

    // Emit to subscribers
    const handlers = this.subscriptions.get(message.channel)
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(message.data)
        } catch (error) {
          console.error('Error in message handler:', error)
        }
      })
    }
  }

  private scheduleReconnect(): void {
    this.connectionStatus = 'reconnecting'
    const delay = this.reconnectInterval * Math.pow(2, this.reconnectAttempts)

    setTimeout(() => {
      this.reconnectAttempts++
      console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
      this.connect().catch(() => {
        // Reconnect failed, will retry if attempts remain
      })
    }, delay)
  }

  private startHeartbeat(): void {
    this.stopHeartbeat()
    this.heartbeatInterval = setInterval(() => {
      this.send({
        type: 'system',
        channel: 'heartbeat',
        data: { type: 'ping', timestamp: Date.now() },
      })
    }, 30000) // Send ping every 30 seconds
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
      this.heartbeatInterval = null
    }
  }

  private processMessageQueue(): void {
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift()
      this.send(message)
    }
  }

  private emit(event: WSEventType, data?: any): void {
    const listeners = this.eventListeners.get(event)
    if (listeners) {
      listeners.forEach(listener => {
        try {
          listener(data)
        } catch (error) {
          console.error('Error in event listener:', error)
        }
      })
    }
  }
}

// Create singleton instance
export const wsService = new WebSocketService()

// Convenience subscription methods
export class MarketWS {
  /**
   * Subscribe to price updates for symbols
   */
  static subscribePrices(symbols: string[], callback: (data: MarketPrice[]) => void): void {
    wsService.subscribe(`${WS_CHANNELS.MARKET_DATA}_price`, callback)
    wsService.send({
      type: 'subscribe',
      channel: WS_CHANNELS.MARKET_DATA,
      data: { type: 'price', symbols },
    })
  }

  /**
   * Subscribe to trade updates for a symbol
   */
  static subscribeTrades(symbol: string, callback: (data: TradeData) => void): void {
    const channel = `${WS_CHANNELS.TRADES}_${symbol}`
    wsService.subscribe(channel, callback)
    wsService.send({
      type: 'subscribe',
      channel: WS_CHANNELS.TRADES,
      data: { symbol },
    })
  }

  /**
   * Subscribe to order book updates for a symbol
   */
  static subscribeDepth(symbol: string, callback: (data: OrderBookUpdate) => void): void {
    const channel = `${WS_CHANNELS.ORDER_BOOK}_${symbol}`
    wsService.subscribe(channel, callback)
    wsService.send({
      type: 'subscribe',
      channel: WS_CHANNELS.ORDER_BOOK,
      data: { symbol },
    })
  }

  /**
   * Unsubscribe from price updates
   */
  static unsubscribePrices(symbols?: string[]): void {
    if (symbols) {
      wsService.send({
        type: 'unsubscribe',
        channel: WS_CHANNELS.MARKET_DATA,
        data: { type: 'price', symbols },
      })
    } else {
      wsService.unsubscribe(`${WS_CHANNELS.MARKET_DATA}_price`)
    }
  }

  /**
   * Unsubscribe from trade updates
   */
  static unsubscribeTrades(symbol: string): void {
    const channel = `${WS_CHANNELS.TRADES}_${symbol}`
    wsService.unsubscribe(channel)
    wsService.send({
      type: 'unsubscribe',
      channel: WS_CHANNELS.TRADES,
      data: { symbol },
    })
  }

  /**
   * Unsubscribe from order book updates
   */
  static unsubscribeDepth(symbol: string): void {
    const channel = `${WS_CHANNELS.ORDER_BOOK}_${symbol}`
    wsService.unsubscribe(channel)
    wsService.send({
      type: 'unsubscribe',
      channel: WS_CHANNELS.ORDER_BOOK,
      data: { symbol },
    })
  }
}

export class StrategyWS {
  /**
   * Subscribe to strategy updates
   */
  static subscribeStrategyUpdates(callback: (data: StrategyUpdate) => void): void {
    wsService.subscribe(WS_CHANNELS.STRATEGY_UPDATES, callback)
  }

  /**
   * Subscribe to specific strategy updates
   */
  static subscribeStrategy(strategyId: string, callback: (data: StrategyUpdate) => void): void {
    const channel = `${WS_CHANNELS.STRATEGY_UPDATES}_${strategyId}`
    wsService.subscribe(channel, callback)
    wsService.send({
      type: 'subscribe',
      channel: WS_CHANNELS.STRATEGY_UPDATES,
      data: { strategyId },
    })
  }

  /**
   * Unsubscribe from strategy updates
   */
  static unsubscribeStrategyUpdates(): void {
    wsService.unsubscribe(WS_CHANNELS.STRATEGY_UPDATES)
  }

  /**
   * Unsubscribe from specific strategy
   */
  static unsubscribeStrategy(strategyId: string): void {
    const channel = `${WS_CHANNELS.STRATEGY_UPDATES}_${strategyId}`
    wsService.unsubscribe(channel)
    wsService.send({
      type: 'unsubscribe',
      channel: WS_CHANNELS.STRATEGY_UPDATES,
      data: { strategyId },
    })
  }
}

export class NotificationWS {
  /**
   * Subscribe to system notifications
   */
  static subscribe(callback: (data: Notification) => void): void {
    wsService.subscribe(WS_CHANNELS.ALERTS, callback)
  }

  /**
   * Unsubscribe from notifications
   */
  static unsubscribe(): void {
    wsService.unsubscribe(WS_CHANNELS.ALERTS)
  }
}
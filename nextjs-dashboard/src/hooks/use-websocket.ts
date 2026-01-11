'use client'

import { useEffect, useState, useRef, useCallback } from 'react'
import { io, Socket } from 'socket.io-client'
import { WebSocketMessage } from '@/types'

interface UseWebSocketOptions {
  url?: string
  autoConnect?: boolean
  reconnectAttempts?: number
  reconnectDelay?: number
}

interface UseWebSocketReturn {
  isConnected: boolean
  lastMessage: WebSocketMessage | null
  send: (message: Omit<WebSocketMessage, 'timestamp'>) => void
  disconnect: () => void
  reconnect: () => void
}

export function useWebSocket({
  url = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:3004',
  autoConnect = true,
  reconnectAttempts = 5,
  reconnectDelay = 1000,
}: UseWebSocketOptions = {}): UseWebSocketReturn {
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const socketRef = useRef<Socket | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  const connect = useCallback(() => {
    if (socketRef.current?.connected) return

    try {
      socketRef.current = io(url, {
        transports: ['websocket'],
        upgrade: false,
        rememberUpgrade: false,
        timeout: 5000,
        forceNew: true,
      })

      socketRef.current.on('connect', () => {
        console.log('WebSocket connected')
        setIsConnected(true)
        reconnectAttemptsRef.current = 0
      })

      socketRef.current.on('disconnect', (reason) => {
        console.log('WebSocket disconnected:', reason)
        setIsConnected(false)

        // 自動重連
        if (reconnectAttemptsRef.current < reconnectAttempts) {
          reconnectAttemptsRef.current++
          console.log(`Reconnecting... Attempt ${reconnectAttemptsRef.current}`)

          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, reconnectDelay * reconnectAttemptsRef.current)
        }
      })

      socketRef.current.on('connect_error', (error) => {
        console.error('WebSocket connection error:', error)
        setIsConnected(false)
      })

      socketRef.current.on('message', (message: WebSocketMessage) => {
        setLastMessage(message)
      })

      // 監聽特定事件
      socketRef.current.on('price_update', (data) => {
        setLastMessage({
          type: 'price_update',
          data,
          timestamp: new Date().toISOString(),
        })
      })

      socketRef.current.on('signal', (data) => {
        setLastMessage({
          type: 'signal',
          data,
          timestamp: new Date().toISOString(),
        })
      })

      socketRef.current.on('execution', (data) => {
        setLastMessage({
          type: 'execution',
          data,
          timestamp: new Date().toISOString(),
        })
      })

      socketRef.current.on('alert', (data) => {
        setLastMessage({
          type: 'alert',
          data,
          timestamp: new Date().toISOString(),
        })
      })

      socketRef.current.on('system_status', (data) => {
        setLastMessage({
          type: 'system_status',
          data,
          timestamp: new Date().toISOString(),
        })
      })
    } catch (error) {
      console.error('Failed to connect WebSocket:', error)
      setIsConnected(false)
    }
  }, [url, reconnectAttempts, reconnectDelay])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (socketRef.current) {
      socketRef.current.disconnect()
      socketRef.current = null
    }

    setIsConnected(false)
  }, [])

  const reconnect = useCallback(() => {
    disconnect()
    reconnectAttemptsRef.current = 0
    setTimeout(() => {
      connect()
    }, 1000)
  }, [connect, disconnect])

  const send = useCallback((message: Omit<WebSocketMessage, 'timestamp'>) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit('message', {
        ...message,
        timestamp: new Date().toISOString(),
      })
    } else {
      console.warn('WebSocket not connected, message not sent:', message)
    }
  }, [])

  useEffect(() => {
    if (autoConnect) {
      connect()
    }

    return () => {
      disconnect()
    }
  }, [autoConnect, connect, disconnect])

  return {
    isConnected,
    lastMessage,
    send,
    disconnect,
    reconnect,
  }
}
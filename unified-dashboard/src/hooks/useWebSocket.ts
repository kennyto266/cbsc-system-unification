/**
 * WebSocket Hook for React Components
 * 為React組件提供WebSocket功能的Hook
 */

import { useEffect, useRef, useCallback } from 'react'
import { useSelector, useDispatch } from 'react-redux'
import { RootState } from '../store'
import { setWebSocketStatus, clearRealtimeData } from '../store/slices/uiSlice'
import { getWebSocketService, WebSocketService } from '../services/websocketService'

interface UseWebSocketOptions {
  autoConnect?: boolean
  token?: string
  reconnectInterval?: number
}

interface UseWebSocketReturn {
  connect: (token?: string) => Promise<void>
  disconnect: () => void
  send: (message: any) => void
  subscribe: (channel: string) => void
  unsubscribe: (channel: string) => void
  isConnected: boolean
  isReconnecting: boolean
  lastError?: string
  reconnectAttempts: number
}

export const useWebSocket = (options: UseWebSocketOptions = {}): UseWebSocketReturn => {
  const {
    autoConnect = true,
    token,
    reconnectInterval = 3000
  } = options

  const dispatch = useDispatch()
  const webSocketStatus = useSelector((state: RootState) => state.ui.webSocketStatus)
  const webSocketServiceRef = useRef<WebSocketService | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  // 初始化WebSocket服務
  const getWebSocketServiceInstance = useCallback(() => {
    if (!webSocketServiceRef.current) {
      webSocketServiceRef.current = getWebSocketService()
    }
    return webSocketServiceRef.current
  }, [])

  // 連接WebSocket
  const connect = useCallback(async (authToken?: string) => {
    try {
      const wsService = getWebSocketServiceInstance()
      const connectToken = authToken || token

      dispatch(setWebSocketStatus({
        connected: false,
        reconnecting: true,
        lastError: undefined,
        reconnectAttempts: 0
      }))

      await wsService.connect(connectToken)

    } catch (error) {
      console.error('WebSocket connection failed:', error)
      dispatch(setWebSocketStatus({
        connected: false,
        reconnecting: false,
        lastError: error instanceof Error ? error.message : 'Connection failed'
      }))

      // 自動重連
      if (autoConnect) {
        reconnectTimeoutRef.current = setTimeout(() => {
          connect(authToken)
        }, reconnectInterval)
      }
    }
  }, [token, autoConnect, reconnectInterval, dispatch, getWebSocketServiceInstance])

  // 斷開連接
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    const wsService = getWebSocketServiceInstance()
    wsService.disconnect()

    dispatch(clearRealtimeData())
    dispatch(setWebSocketStatus({
      connected: false,
      reconnecting: false,
      reconnectAttempts: 0
    }))
  }, [dispatch, getWebSocketServiceInstance])

  // 發送消息
  const send = useCallback((message: any) => {
    const wsService = getWebSocketServiceInstance()
    wsService.send(message)
  }, [getWebSocketServiceInstance])

  // 訂閱頻道
  const subscribe = useCallback((channel: string) => {
    const wsService = getWebSocketServiceInstance()
    wsService.subscribe(channel)
  }, [getWebSocketServiceInstance])

  // 取消訂閱頻道
  const unsubscribe = useCallback((channel: string) => {
    const wsService = getWebSocketServiceInstance()
    wsService.unsubscribe(channel)
  }, [getWebSocketServiceInstance])

  // 自動連接
  useEffect(() => {
    if (autoConnect) {
      connect(token)
    }

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
    }
  }, [autoConnect, connect, token])

  // 組件卸載時清理
  useEffect(() => {
    return () => {
      if (webSocketServiceRef.current) {
        webSocketServiceRef.current.cleanup()
        webSocketServiceRef.current = null
      }
    }
  }, [])

  return {
    connect,
    disconnect,
    send,
    subscribe,
    unsubscribe,
    isConnected: webSocketStatus.connected,
    isReconnecting: webSocketStatus.reconnecting,
    lastError: webSocketStatus.lastError,
    reconnectAttempts: webSocketStatus.reconnectAttempts
  }
}

export default useWebSocket

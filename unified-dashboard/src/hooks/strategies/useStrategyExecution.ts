import { useState, useEffect, useCallback, useRef } from 'react'
import { message, Modal } from 'antd'
import { useAppSelector, useAppDispatch } from '../../hooks/redux'
import {
  useStartStrategyMutation,
  useStopStrategyMutation,
  usePauseStrategyMutation,
  useResumeStrategyMutation,
  useGetExecutionStatusQuery,
  usePlaceManualOrderMutation,
  useCancelOrderMutation,
  useGetOrdersQuery,
  useGetPositionsQuery,
  useClosePositionMutation,
  useExecuteStrategyMutation,
} from '../../store/api/strategiesApi'
import { updateStrategyStatus } from '../../store/slices/strategiesSlice'
import { StrategyStatus, Order } from '../../types'

interface UseStrategyExecutionOptions {
  strategyId: string
  autoRefresh?: boolean
  refreshInterval?: number
}

interface ManualOrderParams {
  symbol: string
  side: 'BUY' | 'SELL'
  type: 'MARKET' | 'LIMIT' | 'STOP'
  quantity: number
  price?: number
  stopPrice?: number
  timeInForce?: 'GTC' | 'IOC' | 'FOK'
}

export const useStrategyExecution = (options: UseStrategyExecutionOptions) => {
  const { strategyId, autoRefresh = true, refreshInterval = 5000 } = options

  const dispatch = useAppDispatch()
  const { websocketStatus, connected } = useAppSelector(state => state.market)

  // State
  const [isExecuting, setIsExecuting] = useState(false)
  const [executionState, setExecutionState] = useState<'idle' | 'starting' | 'running' | 'pausing' | 'paused' | 'stopping' | 'stopped' | 'error'>('idle')
  const [lastError, setLastError] = useState<string | null>(null)
  const [realTimeData, setRealTimeData] = useState({
    orders: [],
    positions: [],
    pnl: 0,
    executionCount: 0,
  })

  // Refs
  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const wsSubscriptionRef = useRef<any>(null)

  // Mutations
  const [startStrategyMutation] = useStartStrategyMutation()
  const [stopStrategyMutation] = useStopStrategyMutation()
  const [pauseStrategyMutation] = usePauseStrategyMutation()
  const [resumeStrategyMutation] = useResumeStrategyMutation()
  const [executeStrategyMutation] = useExecuteStrategyMutation()
  const [placeManualOrderMutation] = usePlaceManualOrderMutation()
  const [cancelOrderMutation] = useCancelOrderMutation()
  const [closePositionMutation] = useClosePositionMutation()

  // Queries
  const {
    data: executionStatus,
    isLoading: isStatusLoading,
    error: statusError,
    refetch: refetchStatus,
  } = useGetExecutionStatusQuery(strategyId, {
    pollingInterval: autoRefresh && !connected ? refreshInterval : undefined,
    skip: !strategyId,
  })

  const {
    data: ordersData,
    isLoading: isOrdersLoading,
    refetch: refetchOrders,
  } = useGetOrdersQuery(
    { strategyId, page: 1, pageSize: 50 },
    {
      pollingInterval: autoRefresh && !connected ? refreshInterval : undefined,
      skip: !strategyId,
    }
  )

  const {
    data: positionsData,
    isLoading: isPositionsLoading,
    refetch: refetchPositions,
  } = useGetPositionsQuery(
    { strategyId, page: 1, pageSize: 50 },
    {
      pollingInterval: autoRefresh && !connected ? refreshInterval : undefined,
      skip: !strategyId,
    }
  )

  // Update execution state based on status
  useEffect(() => {
    if (executionStatus) {
      const newStatus = executionStatus.status?.toLowerCase()
      if (newStatus === 'running') {
        setExecutionState('running')
        setLastError(null)
      } else if (newStatus === 'stopped') {
        setExecutionState('stopped')
        setIsExecuting(false)
      } else if (newStatus === 'paused') {
        setExecutionState('paused')
      } else if (newStatus === 'error') {
        setExecutionState('error')
        setLastError(executionStatus.error || '未知錯誤')
      }
    }
  }, [executionStatus])

  // WebSocket integration for real-time updates
  useEffect(() => {
    if (!connected || !strategyId) return

    // Subscribe to strategy execution events
    const subscription = {
      type: 'subscribe',
      channel: 'strategy_execution',
      params: {
        strategyId,
      },
    }

    // This would be handled by the WebSocket middleware
    // wsSubscriptionRef.current = websocket.send(JSON.stringify(subscription))

    // Listen for real-time updates
    const handleRealTimeUpdate = (event: any) => {
      if (event.strategyId === strategyId) {
        switch (event.type) {
          case 'order_update':
            setRealTimeData(prev => ({
              ...prev,
              orders: [event.order, ...prev.orders.slice(0, 49)],
            }))
            break

          case 'position_update':
            setRealTimeData(prev => ({
              ...prev,
              positions: prev.positions.map(p =>
                p.id === event.position.id ? event.position : p
              ),
            }))
            break

          case 'trade':
            setRealTimeData(prev => ({
              ...prev,
              executionCount: prev.executionCount + 1,
              pnl: prev.pnl + (event.pnl || 0),
            }))
            break

          case 'execution_status':
            setExecutionState(event.status.toLowerCase())
            if (event.error) {
              setLastError(event.error)
            }
            break
        }
      }
    }

    // Register the event handler (this would be handled by WebSocket middleware)
    // websocket.on('message', handleRealTimeUpdate)

    return () => {
      // Cleanup
      if (wsSubscriptionRef.current) {
        // websocket.send(JSON.stringify({ type: 'unsubscribe', channel: 'strategy_execution' }))
      }
    }
  }, [connected, strategyId])

  // Refresh all execution data
  const refreshAll = useCallback(() => {
    refetchStatus()
    refetchOrders()
    refetchPositions()
  }, [refetchStatus, refetchOrders, refetchPositions])

  // Start strategy
  const startStrategy = useCallback(async (allocation?: number) => {
    setExecutionState('starting')
    setLastError(null)

    try {
      await startStrategyMutation({
        strategyId,
        mode: 'live',
        allocation,
      }).unwrap()

      setExecutionState('running')
      setIsExecuting(true)
      dispatch(updateStrategyStatus({ id: strategyId, status: StrategyStatus.ACTIVE }))

      message.success('策略啟動成功')
    } catch (error: any) {
      setExecutionState('error')
      setLastError(error.data?.message || error.message || '策略啟動失敗')

      const errorMessage = error.data?.message || error.message || '策略啟動失敗'
      message.error(errorMessage)
      throw error
    }
  }, [startStrategyMutation, strategyId, dispatch])

  // Stop strategy
  const stopStrategy = useCallback(async (reason?: string) => {
    setExecutionState('stopping')

    try {
      await stopStrategyMutation({
        strategyId,
        reason: reason || '手動停止',
      }).unwrap()

      setExecutionState('stopped')
      setIsExecuting(false)
      dispatch(updateStrategyStatus({ id: strategyId, status: StrategyStatus.INACTIVE }))

      message.success('策略已停止')
    } catch (error: any) {
      setExecutionState('error')
      setLastError(error.data?.message || error.message || '策略停止失敗')

      const errorMessage = error.data?.message || error.message || '策略停止失敗'
      message.error(errorMessage)
      throw error
    }
  }, [stopStrategyMutation, strategyId, dispatch])

  // Pause strategy
  const pauseStrategy = useCallback(async () => {
    setExecutionState('pausing')

    try {
      await pauseStrategyMutation({ id: strategyId }).unwrap()
      setExecutionState('paused')

      message.success('策略已暫停')
    } catch (error: any) {
      setExecutionState('error')
      setLastError(error.data?.message || error.message || '策略暫停失敗')

      const errorMessage = error.data?.message || error.message || '策略暫停失敗'
      message.error(errorMessage)
      throw error
    }
  }, [pauseStrategyMutation, strategyId])

  // Resume strategy
  const resumeStrategy = useCallback(async () => {
    try {
      await resumeStrategyMutation({ id: strategyId }).unwrap()
      setExecutionState('running')

      message.success('策略已恢復')
    } catch (error: any) {
      setExecutionState('error')
      setLastError(error.data?.message || error.message || '策略恢復失敗')

      const errorMessage = error.data?.message || error.message || '策略恢復失敗'
      message.error(errorMessage)
      throw error
    }
  }, [resumeStrategyMutation, strategyId])

  // Execute strategy once
  const executeOnce = useCallback(async (params?: any) => {
    try {
      await executeStrategyMutation({
        strategyId,
        params,
      }).unwrap()

      message.success('策略執行完成')
      refreshAll()
    } catch (error: any) {
      const errorMessage = error.data?.message || error.message || '策略執行失敗'
      message.error(errorMessage)
      throw error
    }
  }, [executeStrategyMutation, strategyId, refreshAll])

  // Place manual order
  const placeManualOrder = useCallback(async (orderParams: ManualOrderParams) => {
    try {
      const result = await placeManualOrderMutation({
        ...orderParams,
        strategyId,
      }).unwrap()

      message.success('訂單已提交')
      refreshOrders()
      return result
    } catch (error: any) {
      const errorMessage = error.data?.message || error.message || '訂單提交失敗'
      message.error(errorMessage)
      throw error
    }
  }, [placeManualOrderMutation, strategyId, refreshOrders])

  // Cancel order
  const cancelOrder = useCallback(async (orderId: string) => {
    Modal.confirm({
      title: '確認取消訂單',
      content: '確定要取消這個訂單嗎？',
      okText: '確定',
      cancelText: '取消',
      onOk: async () => {
        try {
          await cancelOrderMutation({ orderId }).unwrap()
          message.success('訂單已取消')
          refreshOrders()
        } catch (error: any) {
          const errorMessage = error.data?.message || error.message || '取消訂單失敗'
          message.error(errorMessage)
          throw error
        }
      },
    })
  }, [cancelOrderMutation, refreshOrders])

  // Close position
  const closePosition = useCallback(async (positionId: string) => {
    Modal.confirm({
      title: '確認平倉',
      content: '確定要平掉這個持倉嗎？',
      okText: '確定',
      cancelText: '取消',
      onOk: async () => {
        try {
          await closePositionMutation({ positionId }).unwrap()
          message.success('持倉已平倉')
          refreshPositions()
        } catch (error: any) {
          const errorMessage = error.data?.message || error.message || '平倉失敗'
          message.error(errorMessage)
          throw error
        }
      },
    })
  }, [closePositionMutation, refreshPositions])

  // Emergency stop
  const emergencyStop = useCallback(async () => {
    Modal.confirm({
      title: '緊急停止確認',
      content: '確定要緊急停止策略嗎？所有未成交訂單將被取消。',
      okText: '緊急停止',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        try {
          await stopStrategyMutation({
            strategyId,
            reason: '緊急停止',
          }).unwrap()

          setExecutionState('stopped')
          setIsExecuting(false)
          dispatch(updateStrategyStatus({ id: strategyId, status: StrategyStatus.INACTIVE }))

          message.warning('策略已緊急停止')
        } catch (error: any) {
          const errorMessage = error.data?.message || error.message || '緊急停止失敗'
          message.error(errorMessage)
          throw error
        }
      },
    })
  }, [stopStrategyMutation, strategyId, dispatch])

  // Combine real-time and queried data
  const orders = connected ? realTimeData.orders : (ordersData?.data || [])
  const positions = connected ? realTimeData.positions : (positionsData?.data || [])

  return {
    // State
    isExecuting,
    executionState,
    lastError,
    realTimeData,

    // Data
    executionStatus,
    orders,
    positions,

    // Loading states
    isStatusLoading,
    isOrdersLoading,
    isPositionsLoading,

    // Error states
    statusError,

    // Actions
    startStrategy,
    stopStrategy,
    pauseStrategy,
    resumeStrategy,
    executeOnce,
    placeManualOrder,
    cancelOrder,
    closePosition,
    emergencyStop,

    // Refresh
    refreshAll,
    refreshOrders,
    refreshPositions,
  }
}
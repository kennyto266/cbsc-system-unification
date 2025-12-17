import { useState, useEffect, useCallback } from 'react'
import { message } from 'antd'
import { useAppSelector } from '../../hooks/redux'
import {
  useGetStrategyQuery,
  useGetStrategyPerformanceQuery,
  useGetStrategyMetricsQuery,
  useGetExecutionStatusQuery,
  useGetRiskMetricsQuery,
  useGetExecutionLogsQuery,
  useGetOrdersQuery,
  useGetPositionsQuery,
} from '../../store/api/strategiesApi'

interface UseStrategyDetailOptions {
  strategyId: string
  autoFetch?: boolean
  performancePeriod?: string
  logsParams?: {
    level?: string
    startTime?: string
    endTime?: string
    page?: number
    pageSize?: number
  }
  ordersParams?: {
    status?: string
    page?: number
    pageSize?: number
  }
  positionsParams?: {
    page?: number
    pageSize?: number
  }
}

export const useStrategyDetail = (options: UseStrategyDetailOptions) => {
  const {
    strategyId,
    autoFetch = true,
    performancePeriod = '1M',
    logsParams = {},
    ordersParams = {},
    positionsParams = {},
  } = options

  const { websocketStatus } = useAppSelector(state => state.market)

  // Local state for refresh control
  const [refreshTrigger, setRefreshTrigger] = useState(0)
  const [realTimeEnabled, setRealTimeEnabled] = useState(true)

  // Base strategy query
  const {
    data: strategy,
    isLoading: isStrategyLoading,
    error: strategyError,
    refetch: refetchStrategy,
  } = useGetStrategyQuery(strategyId, {
    skip: !autoFetch || !strategyId,
  })

  // Performance data
  const {
    data: performance,
    isLoading: isPerformanceLoading,
    error: performanceError,
    refetch: refetchPerformance,
  } = useGetStrategyPerformanceQuery(
    { id: strategyId, period: performancePeriod },
    {
      skip: !autoFetch || !strategyId,
    }
  )

  // Strategy metrics
  const {
    data: metrics,
    isLoading: isMetricsLoading,
    error: metricsError,
    refetch: refetchMetrics,
  } = useGetStrategyMetricsQuery(strategyId, {
    skip: !autoFetch || !strategyId,
  })

  // Execution status
  const {
    data: executionStatus,
    isLoading: isExecutionLoading,
    error: executionError,
    refetch: refetchExecutionStatus,
  } = useGetExecutionStatusQuery(strategyId, {
    skip: !autoFetch || !strategyId,
  })

  // Risk metrics
  const {
    data: riskMetrics,
    isLoading: isRiskLoading,
    error: riskError,
    refetch: refetchRiskMetrics,
  } = useGetRiskMetricsQuery(strategyId, {
    skip: !autoFetch || !strategyId,
  })

  // Execution logs
  const {
    data: logsData,
    isLoading: isLogsLoading,
    error: logsError,
    refetch: refetchLogs,
  } = useGetExecutionLogsQuery(
    {
      strategyId,
      ...logsParams,
    },
    {
      skip: !autoFetch || !strategyId,
    }
  )

  // Orders
  const {
    data: ordersData,
    isLoading: isOrdersLoading,
    error: ordersError,
    refetch: refetchOrders,
  } = useGetOrdersQuery(
    {
      strategyId,
      ...ordersParams,
    },
    {
      skip: !autoFetch || !strategyId,
    }
  )

  // Positions
  const {
    data: positionsData,
    isLoading: isPositionsLoading,
    error: positionsError,
    refetch: refetchPositions,
  } = useGetPositionsQuery(
    {
      strategyId,
      ...positionsParams,
    },
    {
      skip: !autoFetch || !strategyId,
    }
  )

  // Refresh all data
  const refreshAll = useCallback(() => {
    setRefreshTrigger(prev => prev + 1)
    refetchStrategy()
    refetchPerformance()
    refetchMetrics()
    refetchExecutionStatus()
    refetchRiskMetrics()
    refetchLogs()
    refetchOrders()
    refetchPositions()
  }, [
    refetchStrategy,
    refetchPerformance,
    refetchMetrics,
    refetchExecutionStatus,
    refetchRiskMetrics,
    refetchLogs,
    refetchOrders,
    refetchPositions,
  ])

  // Refresh individual data
  const refreshPerformance = useCallback(() => {
    refetchPerformance()
  }, [refetchPerformance])

  const refreshMetrics = useCallback(() => {
    refetchMetrics()
  }, [refetchMetrics])

  const refreshExecutionStatus = useCallback(() => {
    refetchExecutionStatus()
  }, [refetchExecutionStatus])

  const refreshRiskMetrics = useCallback(() => {
    refetchRiskMetrics()
  }, [refetchRiskMetrics])

  const refreshLogs = useCallback(() => {
    refetchLogs()
  }, [refetchLogs])

  const refreshOrders = useCallback(() => {
    refetchOrders()
  }, [refetchOrders])

  const refreshPositions = useCallback(() => {
    refetchPositions()
  }, [refetchPositions])

  // Effect for real-time updates
  useEffect(() => {
    if (!realTimeEnabled || !strategyId || websocketStatus.connected !== true) {
      return
    }

    // Set up real-time refresh interval
    const interval = setInterval(() => {
      // Only refresh execution-critical data
      refetchExecutionStatus()
      refetchOrders()
      refetchPositions()
    }, 5000) // Refresh every 5 seconds

    return () => clearInterval(interval)
  }, [realTimeEnabled, strategyId, websocketStatus.connected, refetchExecutionStatus, refetchOrders, refetchPositions])

  // Extract data from paginated responses
  const logs = logsData?.data || []
  const logsPagination = logsData?.pagination

  const orders = ordersData?.data || []
  const ordersPagination = ordersData?.pagination

  const positions = positionsData?.data || []
  const positionsPagination = positionsData?.pagination

  // Computed values
  const isLoading = isStrategyLoading || isPerformanceLoading || isMetricsLoading ||
                   isExecutionLoading || isRiskLoading || isLogsLoading ||
                   isOrdersLoading || isPositionsLoading

  const hasError = strategyError || performanceError || metricsError ||
                  executionError || riskError || logsError ||
                  ordersError || positionsError

  const isRealTimeActive = realTimeEnabled && websocketStatus.connected

  return {
    // Data
    strategy,
    performance,
    metrics,
    executionStatus,
    riskMetrics,
    logs,
    orders,
    positions,

    // Pagination
    logsPagination,
    ordersPagination,
    positionsPagination,

    // Loading states
    isLoading,
    isStrategyLoading,
    isPerformanceLoading,
    isMetricsLoading,
    isExecutionLoading,
    isRiskLoading,
    isLogsLoading,
    isOrdersLoading,
    isPositionsLoading,

    // Error states
    hasError,
    strategyError,
    performanceError,
    metricsError,
    executionError,
    riskError,
    logsError,
    ordersError,
    positionsError,

    // Refresh functions
    refreshAll,
    refreshPerformance,
    refreshMetrics,
    refreshExecutionStatus,
    refreshRiskMetrics,
    refreshLogs,
    refreshOrders,
    refreshPositions,

    // Real-time control
    realTimeEnabled,
    setRealTimeEnabled,
    isRealTimeActive,

    // Internal state
    refreshTrigger,
  }
}
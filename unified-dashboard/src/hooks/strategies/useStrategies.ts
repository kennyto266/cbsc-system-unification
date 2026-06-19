import { useState, useEffect, useCallback } from 'react'
import { message } from 'antd'
import { useAppDispatch, useAppSelector } from '../../hooks/redux'
import {
  useGetStrategiesQuery,
  useGetStrategyQuery,
  useCreateStrategyMutation,
  useUpdateStrategyMutation,
  usePatchStrategyMutation,
  useDeleteStrategyMutation,
  useStartStrategyMutation,
  useStopStrategyMutation,
  usePauseStrategyMutation,
  useResumeStrategyMutation,
  useGetStrategyPerformanceQuery,
  useExecuteStrategyMutation,
  useBatchOperationMutation,
} from '../../store/api/strategiesApi'
import {
  setFilters as setStrategiesFilter,
  setPagination as setStrategiesPagination,
  clearFilters as clearStrategiesData
} from '../../store/slices/strategiesSlice'
import { Strategy, StrategyStatus, PaginationParams } from '../../types'

interface UseStrategiesOptions {
  autoFetch?: boolean
  filters?: {
    status?: StrategyStatus | 'all'
    type?: string | 'all'
    riskLevel?: string | 'all'
    search?: string
  }
  pagination?: PaginationParams
}

interface UseStrategiesReturn {
  // Data
  strategies: Strategy[] | undefined
  currentStrategy: Strategy | undefined
  pagination: {
    current: number
    pageSize: number
    total: number
  } | undefined

  // Loading states
  isLoading: boolean
  isCreating: boolean
  isUpdating: boolean
  isDeleting: boolean
  isStarting: boolean
  isStopping: boolean
  isPausing: boolean
  isResuming: boolean

  // Error states
  error?: any
  createError?: any
  updateError?: any
  deleteError?: any

  // Actions
  refetch: () => void
  fetchStrategy: (id: string) => void
  createStrategy: (data: Partial<Strategy>) => Promise<Strategy | undefined>
  updateStrategy: (id: string, data: Partial<Strategy>) => Promise<Strategy | undefined>
  patchStrategy: (id: string, data: Partial<Strategy>) => Promise<Strategy | undefined>
  deleteStrategy: (id: string) => Promise<void>
  startStrategy: (id: string, allocation?: number) => Promise<void>
  stopStrategy: (id: string, reason?: string) => Promise<void>
  pauseStrategy: (id: string) => Promise<void>
  resumeStrategy: (id: string) => Promise<void>
  executeStrategy: (id: string, params?: any) => Promise<void>

  // Batch operations
  batchOperation: (strategyIds: string[], operation: string, params?: any) => Promise<void>

  // Filters and pagination
  setFilter: (filters: any) => void
  setPagination: (pagination: any) => void
  clearData: () => void
}

export const useStrategies = (options: UseStrategiesOptions = {}): UseStrategiesReturn => {
  const { autoFetch = true, filters: initialFilters = {}, pagination: initialPagination } = options

  const dispatch = useAppDispatch()
  const { filters: storeFilters, pagination: storePagination } = useAppSelector(state => state.strategies)

  const [localFilters, setLocalFilters] = useState(initialFilters)
  const [localPagination, setLocalPagination] = useState(initialPagination || { current: 1, pageSize: 10 })

  // Combine filters from props and store
  const combinedFilters = { ...storeFilters, ...localFilters }
  const combinedPagination = storePagination || localPagination

  // Query params
  const queryParams = {
    ...combinedPagination,
    ...combinedFilters,
  }

  // RTK Query hooks
  const {
    data: strategiesData,
    isLoading,
    error,
    refetch,
  } = useGetStrategiesQuery(queryParams, {
    skip: !autoFetch,
  })

  const [createStrategyMutation, { isLoading: isCreating, error: createError }] = useCreateStrategyMutation()
  const [updateStrategyMutation, { isLoading: isUpdating, error: updateError }] = useUpdateStrategyMutation()
  const [patchStrategyMutation, { isLoading: isPatching }] = usePatchStrategyMutation()
  const [deleteStrategyMutation, { isLoading: isDeleting, error: deleteError }] = useDeleteStrategyMutation()
  const [startStrategyMutation, { isLoading: isStarting }] = useStartStrategyMutation()
  const [stopStrategyMutation, { isLoading: isStopping }] = useStopStrategyMutation()
  const [pauseStrategyMutation, { isLoading: isPausing }] = usePauseStrategyMutation()
  const [resumeStrategyMutation, { isLoading: isResuming }] = useResumeStrategyMutation()
  const [executeStrategyMutation] = useExecuteStrategyMutation()
  const [batchOperationMutation] = useBatchOperationMutation()

  // State for current strategy
  const [currentStrategyId, setCurrentStrategyId] = useState<string | null>(null)

  // Get current strategy
  const { data: currentStrategy } = useGetStrategyQuery(currentStrategyId!, {
    skip: !currentStrategyId,
  })

  // Extract data from paginated response
  const strategies = strategiesData?.data || []
  const pagination = strategiesData?.pagination ? {
    current: strategiesData.pagination.current,
    pageSize: strategiesData.pagination.pageSize,
    total: strategiesData.pagination.total,
  } : undefined

  // Actions
  const createStrategy = useCallback(async (data: Partial<Strategy>) => {
    try {
      const result = await createStrategyMutation(data as any).unwrap()
      message.success('策略創建成功')
      refetch()
      return result
    } catch (error: any) {
      message.error(error.data?.message || '策略創建失敗')
      throw error
    }
  }, [createStrategyMutation, refetch])

  const updateStrategy = useCallback(async (id: string, data: Partial<Strategy>) => {
    try {
      const result = await updateStrategyMutation({ id, updates: data as any }).unwrap()
      message.success('策略更新成功')
      refetch()
      return result
    } catch (error: any) {
      message.error(error.data?.message || '策略更新失敗')
      throw error
    }
  }, [updateStrategyMutation, refetch])

  const patchStrategy = useCallback(async (id: string, data: Partial<Strategy>) => {
    try {
      const result = await patchStrategyMutation({ id, updates: data as any }).unwrap()
      message.success('策略更新成功')
      refetch()
      return result
    } catch (error: any) {
      message.error(error.data?.message || '策略更新失敗')
      throw error
    }
  }, [patchStrategyMutation, refetch])

  const deleteStrategy = useCallback(async (id: string) => {
    try {
      await deleteStrategyMutation(id).unwrap()
      message.success('策略刪除成功')
      refetch()
    } catch (error: any) {
      message.error(error.data?.message || '策略刪除失敗')
      throw error
    }
  }, [deleteStrategyMutation, refetch])

  const startStrategy = useCallback(async (id: string, allocation?: number) => {
    try {
      await startStrategyMutation({ strategyId: id, mode: 'live', allocation }).unwrap()
      message.success('策略啟動成功')
      refetch()
    } catch (error: any) {
      message.error(error.data?.message || '策略啟動失敗')
      throw error
    }
  }, [startStrategyMutation, refetch])

  const stopStrategy = useCallback(async (id: string, reason?: string) => {
    try {
      await stopStrategyMutation({ strategyId: id, reason: reason || '手動停止' }).unwrap()
      message.success('策略停止成功')
      refetch()
    } catch (error: any) {
      message.error(error.data?.message || '策略停止失敗')
      throw error
    }
  }, [stopStrategyMutation, refetch])

  const pauseStrategy = useCallback(async (id: string) => {
    try {
      await pauseStrategyMutation({ id }).unwrap()
      message.success('策略暫停成功')
      refetch()
    } catch (error: any) {
      message.error(error.data?.message || '策略暫停失敗')
      throw error
    }
  }, [pauseStrategyMutation, refetch])

  const resumeStrategy = useCallback(async (id: string) => {
    try {
      await resumeStrategyMutation({ id }).unwrap()
      message.success('策略恢復成功')
      refetch()
    } catch (error: any) {
      message.error(error.data?.message || '策略恢復失敗')
      throw error
    }
  }, [resumeStrategyMutation, refetch])

  const executeStrategy = useCallback(async (id: string, params?: any) => {
    try {
      await executeStrategyMutation({ strategyId: id, params }).unwrap()
      message.success('策略執行成功')
      refetch()
    } catch (error: any) {
      message.error(error.data?.message || '策略執行失敗')
      throw error
    }
  }, [executeStrategyMutation, refetch])

  const batchOperation = useCallback(async (strategyIds: string[], operation: string, params?: any) => {
    try {
      await batchOperationMutation({ strategyIds, operation: operation as any, params }).unwrap()
      message.success(`批量${operation}操作成功`)
      refetch()
    } catch (error: any) {
      message.error(error.data?.message || `批量${operation}操作失敗`)
      throw error
    }
  }, [batchOperationMutation, refetch])

  const fetchStrategy = useCallback((id: string) => {
    setCurrentStrategyId(id)
  }, [])

  const setFilter = useCallback((filters: any) => {
    dispatch(setStrategiesFilter(filters))
  }, [dispatch])

  const setPagination = useCallback((pagination: any) => {
    dispatch(setStrategiesPagination(pagination))
  }, [dispatch])

  const clearData = useCallback(() => {
    dispatch(clearStrategiesData())
    setCurrentStrategyId(null)
  }, [dispatch])

  // Convenience methods that match the existing interface
  const handleStart = startStrategy
  const handleStop = stopStrategy
  const handlePause = pauseStrategy
  const handleResume = resumeStrategy
  const handleDelete = deleteStrategy

  return {
    // Data
    strategies,
    currentStrategy,
    pagination,

    // Loading states
    isLoading,
    isCreating,
    isUpdating,
    isDeleting,
    isPatching,
    isStarting,
    isStopping,
    isPausing,
    isResuming,

    // Error states
    error,
    createError,
    updateError,
    deleteError,

    // Actions
    refetch,
    fetchStrategy,
    createStrategy,
    updateStrategy,
    patchStrategy,
    deleteStrategy,
    startStrategy,
    stopStrategy,
    pauseStrategy,
    resumeStrategy,
    executeStrategy,

    // Batch operations
    batchOperation,

    // Filters and pagination
    setFilter,
    setPagination,
    clearData,

    // Convenience methods
    handleStart,
    handleStop,
    handlePause,
    handleResume,
    handleDelete,
  }
}
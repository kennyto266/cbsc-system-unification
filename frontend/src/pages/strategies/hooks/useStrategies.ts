import { useState, useEffect, useCallback } from 'react'
import { message } from 'antd'
import strategyAPI, { type Strategy, type StrategyFilter } from '../services/strategyAPI'

// Custom hook for strategy management - 策略管理自定义Hook
export const useStrategies = (initialFilter?: StrategyFilter) => {
  const [strategies, setStrategies] = useState<Strategy[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [filter, setFilter] = useState<StrategyFilter>(initialFilter || {})

  // Fetch strategies
  const fetchStrategies = useCallback(async () => {
    setLoading(true)
    try {
      const response = await strategyAPI.getStrategies({
        ...filter,
        page: currentPage,
        pageSize,
      })
      setStrategies(response.strategies)
      setTotal(response.total)
    } catch (error) {
      message.error('获取策略列表失败')
    } finally {
      setLoading(false)
    }
  }, [filter, currentPage, pageSize])

  // Initial fetch
  useEffect(() => {
    fetchStrategies()
  }, [fetchStrategies])

  // Update filter
  const updateFilter = useCallback((newFilter: Partial<StrategyFilter>) => {
    setFilter(prev => ({ ...prev, ...newFilter }))
    setCurrentPage(1)
  }, [])

  // Reset filter
  const resetFilter = useCallback(() => {
    setFilter({})
    setCurrentPage(1)
  }, [])

  // Create strategy
  const createStrategy = useCallback(async (data: any) => {
    try {
      const newStrategy = await strategyAPI.createStrategy(data)
      message.success('策略创建成功')
      fetchStrategies()
      return newStrategy
    } catch (error) {
      message.error('创建策略失败')
      throw error
    }
  }, [fetchStrategies])

  // Update strategy
  const updateStrategy = useCallback(async (id: string, data: any) => {
    try {
      const updated = await strategyAPI.updateStrategy(id, data)
      message.success('策略更新成功')
      fetchStrategies()
      return updated
    } catch (error) {
      message.error('更新策略失败')
      throw error
    }
  }, [fetchStrategies])

  // Delete strategy
  const deleteStrategy = useCallback(async (id: string) => {
    try {
      await strategyAPI.deleteStrategy(id)
      message.success('策略删除成功')
      fetchStrategies()
    } catch (error) {
      message.error('删除策略失败')
      throw error
    }
  }, [fetchStrategies])

  // Run strategy
  const runStrategy = useCallback(async (id: string) => {
    try {
      await strategyAPI.runStrategy({ strategyId: id })
      message.success('策略启动成功')
      fetchStrategies()
    } catch (error) {
      message.error('启动策略失败')
      throw error
    }
  }, [fetchStrategies])

  // Stop strategy
  const stopStrategy = useCallback(async (id: string) => {
    try {
      await strategyAPI.stopStrategy(id)
      message.success('策略停止成功')
      fetchStrategies()
    } catch (error) {
      message.error('停止策略失败')
      throw error
    }
  }, [fetchStrategies])

  // Batch operation
  const batchOperation = useCallback(async (action: string, ids: string[]) => {
    try {
      await strategyAPI.batchOperation({
        action: action as any,
        strategyIds: ids,
      })
      message.success(`批量${action}成功`)
      fetchStrategies()
    } catch (error) {
      message.error(`批量${action}失败`)
      throw error
    }
  }, [fetchStrategies])

  return {
    strategies,
    loading,
    total,
    currentPage,
    pageSize,
    filter,
    setCurrentPage,
    setPageSize,
    updateFilter,
    resetFilter,
    fetchStrategies,
    createStrategy,
    updateStrategy,
    deleteStrategy,
    runStrategy,
    stopStrategy,
    batchOperation,
  }
}

export default useStrategies
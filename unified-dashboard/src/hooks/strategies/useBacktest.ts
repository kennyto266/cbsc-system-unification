import { useState, useCallback } from 'react'
import { message, Modal } from 'antd'
import {
  useRunBacktestMutation,
  useGetBacktestResultQuery,
  useGetBacktestListQuery,
  useDeleteBacktestMutation,
  useOptimizeStrategyMutation,
  useGetOptimizationResultsQuery,
  useCompareStrategiesQuery,
} from '../../store/api/strategiesApi'
import { BacktestRequest, BacktestResponse } from '../../types/api'

interface UseBacktestOptions {
  strategyId?: string
  autoFetch?: boolean
}

export const useBacktest = (options: UseBacktestOptions = {}) => {
  const { strategyId, autoFetch = true } = options

  const [isRunning, setIsRunning] = useState(false)
  const [runningBacktestId, setRunningBacktestId] = useState<string | null>(null)
  const [progress, setProgress] = useState(0)
  const [currentStep, setCurrentStep] = useState('')

  // Mutations
  const [runBacktestMutation] = useRunBacktestMutation()
  const [deleteBacktestMutation] = useDeleteBacktestMutation()
  const [optimizeStrategyMutation] = useOptimizeStrategyMutation()

  // Queries
  const {
    data: backtestList,
    isLoading: isListLoading,
    error: listError,
    refetch: refetchList,
  } = useGetBacktestListQuery(
    { page: 1, pageSize: 20 },
    { skip: !autoFetch }
  )

  const {
    data: backtestResult,
    isLoading: isResultLoading,
    error: resultError,
    refetch: refetchResult,
  } = useGetBacktestResultQuery(runningBacktestId!, {
    skip: !runningBacktestId || !autoFetch,
  })

  const {
    data: optimizationResults,
    isLoading: isOptimizationLoading,
    error: optimizationError,
    refetch: refetchOptimization,
  } = useGetOptimizationResultsQuery(runningBacktestId!, {
    skip: !runningBacktestId,
  })

  // Run backtest
  const runBacktest = useCallback(async (request: BacktestRequest) => {
    setIsRunning(true)
    setProgress(0)
    setCurrentStep('準備回測...')

    try {
      setCurrentStep('提交回測任務...')
      const result = await runBacktestMutation(request).unwrap()

      setRunningBacktestId(result.id)
      setCurrentStep('回測任務已提交')

      // Simulate progress (in real app, this would come from WebSocket or polling)
      const progressInterval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval)
            return 90
          }
          return prev + Math.random() * 10
        })
      }, 1000)

      message.success('回測已開始運行')
      return result
    } catch (error: any) {
      setIsRunning(false)
      setProgress(0)
      setCurrentStep('')

      const errorMessage = error.data?.message || error.message || '回測啟動失敗'
      message.error(errorMessage)
      throw error
    }
  }, [runBacktestMutation])

  // Optimize strategy
  const optimizeStrategy = useCallback(async (
    strategyId: string,
    parameters: string[],
    objective: string,
    constraints?: any
  ) => {
    setIsRunning(true)
    setProgress(0)
    setCurrentStep('準備優化...')

    try {
      setCurrentStep('提交優化任務...')
      const result = await optimizeStrategyMutation({
        strategyId,
        parameters,
        objective,
        constraints,
      }).unwrap()

      setRunningBacktestId(result.jobId)
      setCurrentStep('優化任務已提交')

      message.success('策略優化已開始')
      return result
    } catch (error: any) {
      setIsRunning(false)
      setProgress(0)
      setCurrentStep('')

      const errorMessage = error.data?.message || error.message || '策略優化失敗'
      message.error(errorMessage)
      throw error
    }
  }, [optimizeStrategyMutation])

  // Delete backtest
  const deleteBacktest = useCallback(async (backtestId: string) => {
    Modal.confirm({
      title: '確認刪除',
      content: '確定要刪除這個回測結果嗎？此操作無法撤銷。',
      okText: '確定',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        try {
          await deleteBacktestMutation(backtestId).unwrap()
          message.success('回測結果已刪除')
          refetchList()

          // If deleted the currently running backtest, reset state
          if (runningBacktestId === backtestId) {
            setRunningBacktestId(null)
            setIsRunning(false)
            setProgress(0)
            setCurrentStep('')
          }
        } catch (error: any) {
          const errorMessage = error.data?.message || error.message || '刪除失敗'
          message.error(errorMessage)
          throw error
        }
      },
    })
  }, [deleteBacktestMutation, refetchList, runningBacktestId])

  // Compare strategies
  const compareStrategies = useCallback(async (
    strategyIds: string[],
    period: string,
    metrics: string[]
  ) => {
    try {
      const result = await useCompareStrategiesQuery({
        strategies: strategyIds,
        period,
        metrics,
      }).unwrap()

      message.success('策略比較完成')
      return result
    } catch (error: any) {
      const errorMessage = error.data?.message || error.message || '策略比較失敗'
      message.error(errorMessage)
      throw error
    }
  }, [])

  // Export backtest results
  const exportResults = useCallback(async (backtestId: string, format: 'csv' | 'json' | 'pdf' = 'csv') => {
    try {
      // This would be an API endpoint to export results
      const exportUrl = `/api/strategies/backtest/${backtestId}/export?format=${format}`

      // Create download link
      const link = document.createElement('a')
      link.href = exportUrl
      link.download = `backtest-${backtestId}.${format}`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)

      message.success(`回測結果已導出為 ${format.toUpperCase()} 格式`)
    } catch (error: any) {
      const errorMessage = error.data?.message || error.message || '導出失敗'
      message.error(errorMessage)
      throw error
    }
  }, [])

  // Load backtest result
  const loadBacktest = useCallback((backtestId: string) => {
    setRunningBacktestId(backtestId)
  }, [])

  // Reset state
  const reset = useCallback(() => {
    setIsRunning(false)
    setRunningBacktestId(null)
    setProgress(0)
    setCurrentStep('')
  }, [])

  return {
    // State
    isRunning,
    runningBacktestId,
    progress,
    currentStep,

    // Data
    backtestList,
    backtestResult,
    optimizationResults,

    // Loading states
    isListLoading,
    isResultLoading,
    isOptimizationLoading,

    // Error states
    listError,
    resultError,
    optimizationError,

    // Actions
    runBacktest,
    optimizeStrategy,
    deleteBacktest,
    compareStrategies,
    exportResults,
    loadBacktest,
    reset,

    // Refetch
    refetchList,
    refetchResult,
    refetchOptimization,
  }
}
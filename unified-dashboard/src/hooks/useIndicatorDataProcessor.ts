import { useRef, useCallback, useState } from 'react'

// Worker 实例管理
const workerPool: Worker[] = []
const MAX_WORKERS = navigator.hardwareConcurrency || 4

// 获取或创建 Worker 实例
function getWorker(): Worker {
  if (workerPool.length < MAX_WORKERS) {
    const worker = new Worker(
      new URL('../workers/indicatorDataWorker.ts', import.meta.url),
      { type: 'module' }
    )
    workerPool.push(worker)
    return worker
  }

  // 轮询分配任务
  const index = Math.floor(Math.random() * workerPool.length)
  return workerPool[index]
}

interface UseIndicatorDataProcessorOptions {
  onError?: (error: Error) => void
  onSuccess?: (result: any) => void
}

interface UseIndicatorDataProcessorReturn {
  processIndicatorData: (
    indicators: any[],
    operation: 'aggregate' | 'smooth' | 'resample' | 'calculate-signals',
    params?: any
  ) => Promise<any[]>

  calculatePerformance: (
    indicatorId: string,
    priceData: number[],
    signals: Array<{ timestamp: number; type: 'buy' | 'sell'; price: number }>
  ) => Promise<any>

  filterIndicators: (
    indicators: any[],
    filters: {
      dateRange?: [number, number]
      valueRange?: [number, number]
      tags?: string[]
    }
  ) => Promise<any[]>

  isProcessing: boolean
}

export const useIndicatorDataProcessor = (
  options: UseIndicatorDataProcessorOptions = {}
): UseIndicatorDataProcessorReturn => {
  const [isProcessing, setIsProcessing] = useState(false)
  const processingRef = useRef<Set<string>>(new Set())

  // 通用的 Worker 任务执行器
  const executeWorkerTask = useCallback((
    type: string,
    payload: any,
    taskId: string
  ): Promise<any> => {
    return new Promise((resolve, reject) => {
      const worker = getWorker()

      // 检查任务是否已在处理中
      if (processingRef.current.has(taskId)) {
        reject(new Error('Task is already being processed'))
        return
      }

      processingRef.current.add(taskId)
      setIsProcessing(true)

      const handleMessage = (event: MessageEvent) => {
        const { type: messageType, payload: resultPayload } = event.data

        if (messageType === 'ERROR') {
          processingRef.current.delete(taskId)
          setIsProcessing(processingRef.current.size > 0)
          worker.removeEventListener('message', handleMessage)
          reject(new Error(resultPayload.error))
          return
        }

        if (
          messageType === 'PROCESSING_COMPLETE' ||
          messageType === 'PERFORMANCE_CALCULATED' ||
          messageType === 'FILTERING_COMPLETE'
        ) {
          processingRef.current.delete(taskId)
          setIsProcessing(processingRef.current.size > 0)
          worker.removeEventListener('message', handleMessage)

          if (options.onSuccess) {
            options.onSuccess(resultPayload)
          }

          resolve(resultPayload)
        }
      }

      worker.addEventListener('message', handleMessage)
      worker.postMessage({ type, payload })

      // 设置超时
      setTimeout(() => {
        if (processingRef.current.has(taskId)) {
          processingRef.current.delete(taskId)
          setIsProcessing(processingRef.current.size > 0)
          worker.removeEventListener('message', handleMessage)
          reject(new Error('Task timeout'))
        }
      }, 30000) // 30秒超时
    })
  }, [options])

  // 处理指标数据
  const processIndicatorData = useCallback((
    indicators: any[],
    operation: 'aggregate' | 'smooth' | 'resample' | 'calculate-signals',
    params?: any
  ): Promise<any[]> => {
    const taskId = `process-${Date.now()}-${Math.random()}`

    return executeWorkerTask('PROCESS_INDICATOR_DATA', {
      indicators,
      operation,
      params
    }, taskId) as Promise<any[]>
  }, [executeWorkerTask])

  // 计算性能指标
  const calculatePerformance = useCallback((
    indicatorId: string,
    priceData: number[],
    signals: Array<{ timestamp: number; type: 'buy' | 'sell'; price: number }>
  ): Promise<any> => {
    const taskId = `performance-${indicatorId}-${Date.now()}`

    return executeWorkerTask('CALCULATE_PERFORMANCE', {
      indicatorId,
      priceData,
      signals
    }, taskId).then(result => result.performance)
  }, [executeWorkerTask])

  // 过滤指标
  const filterIndicators = useCallback((
    indicators: any[],
    filters: {
      dateRange?: [number, number]
      valueRange?: [number, number]
      tags?: string[]
    }
  ): Promise<any[]> => {
    const taskId = `filter-${Date.now()}-${Math.random()}`

    return executeWorkerTask('FILTER_INDICATORS', {
      indicators,
      filters
    }, taskId) as Promise<any[]>
  }, [executeWorkerTask])

  // 清理函数
  const cleanup = useCallback(() => {
    workerPool.forEach(worker => {
      worker.terminate()
    })
    workerPool.length = 0
  }, [])

  // 组件卸载时清理
  React.useEffect(() => {
    return cleanup
  }, [cleanup])

  return {
    processIndicatorData,
    calculatePerformance,
    filterIndicators,
    isProcessing
  }
}

// 批量处理工具函数
export const batchProcessIndicators = async (
  indicators: any[],
  operation: 'aggregate' | 'smooth' | 'resample' | 'calculate-signals',
  params?: any,
  batchSize = 50
): Promise<any[]> => {
  const results: any[] = []

  for (let i = 0; i < indicators.length; i += batchSize) {
    const batch = indicators.slice(i, i + batchSize)
    const processor = useIndicatorDataProcessor()

    try {
      const batchResult = await processor.processIndicatorData(batch, operation, params)
      results.push(...batchResult)
    } catch (error) {
      console.error(`Batch processing failed for indicators ${i}-${i + batchSize}:`, error)
      // 继续处理下一批
    }
  }

  return results
}

// 数据压缩工具
export const compressIndicatorData = (data: number[]): string => {
  // 简单的差分编码
  const diff: number[] = []
  for (let i = 0; i < data.length; i++) {
    if (i === 0) {
      diff.push(data[i])
    } else {
      diff.push(data[i] - data[i - 1])
    }
  }

  // 转换为 Base64
  const jsonString = JSON.stringify(diff)
  return btoa(jsonString)
}

// 数据解压缩工具
export const decompressIndicatorData = (compressedData: string): number[] => {
  // 从 Base64 解码
  const jsonString = atob(compressedData)
  const diff: number[] = JSON.parse(jsonString)

  // 还原原始数据
  const data: number[] = []
  for (let i = 0; i < diff.length; i++) {
    if (i === 0) {
      data.push(diff[i])
    } else {
      data.push(data[i - 1] + diff[i])
    }
  }

  return data
}
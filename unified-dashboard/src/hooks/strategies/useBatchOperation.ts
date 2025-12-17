import { useState, useCallback } from 'react'
import { message, Modal } from 'antd'
import { useBatchOperationMutation } from '../../store/api/strategiesApi'

interface BatchOperationOptions {
  onSuccess?: (results: any) => void
  onError?: (error: any) => void
  confirmations?: {
    start?: boolean
    stop?: boolean
    pause?: boolean
    resume?: boolean
    delete?: boolean
  }
  confirmationMessages?: {
    start?: string
    stop?: string
    pause?: string
    resume?: string
    delete?: string
  }
}

export const useBatchOperation = (options: BatchOperationOptions = {}) => {
  const [isBatchOperating, setIsBatchOperating] = useState(false)
  const [batchOperationMutation] = useBatchOperationMutation()

  const {
    onSuccess,
    onError,
    confirmations = {
      delete: true,
      start: false,
      stop: false,
      pause: false,
      resume: false,
    },
    confirmationMessages = {
      start: '確定要啟動選中的策略嗎？',
      stop: '確定要停止選中的策略嗎？',
      pause: '確定要暫停選中的策略嗎？',
      resume: '確定要恢復選中的策略嗎？',
      delete: '確定要刪除選中的策略嗎？此操作無法撤銷。',
    },
  } = options

  const showConfirmation = useCallback((operation: string, count: number): Promise<boolean> => {
    return new Promise((resolve) => {
      if (!confirmations[operation as keyof typeof confirmations]) {
        resolve(true)
        return
      }

      const confirmMessage = confirmationMessages[operation as keyof typeof confirmationMessages] ||
        `確定要對選中的 ${count} 個策略執行 ${operation} 操作嗎？`

      Modal.confirm({
        title: '批量操作確認',
        content: confirmMessage,
        okText: '確定',
        cancelText: '取消',
        okType: operation === 'delete' ? 'danger' : 'primary',
        onOk: () => resolve(true),
        onCancel: () => resolve(false),
      })
    })
  }, [confirmations, confirmationMessages])

  const handleBatchOperation = useCallback(async (
    strategyIds: string[],
    operation: 'start' | 'stop' | 'pause' | 'resume' | 'delete',
    params?: any
  ) => {
    if (strategyIds.length === 0) {
      message.warning('請選擇要操作的策略')
      return
    }

    // Show confirmation if required
    const confirmed = await showConfirmation(operation, strategyIds.length)
    if (!confirmed) {
      return
    }

    setIsBatchOperating(true)

    try {
      // Show progress message
      const progressMessage = message.loading(
        `正在批量${operation === 'delete' ? '刪除' :
                    operation === 'start' ? '啟動' :
                    operation === 'stop' ? '停止' :
                    operation === 'pause' ? '暫停' : '恢復'} ${strategyIds.length} 個策略...`,
        0
      )

      const result = await batchOperationMutation({
        strategyIds,
        operation,
        params,
      }).unwrap()

      progressMessage()

      // Show success message
      message.success(
        `成功${operation === 'delete' ? '刪除' :
                    operation === 'start' ? '啟動' :
                    operation === 'stop' ? '停止' :
                    operation === 'pause' ? '暫停' : '恢復'} ${result.successCount || strategyIds.length} 個策略${
          result.failureCount > 0 ? `，${result.failureCount} 個失敗` : ''
        }`
      )

      // Call success callback
      if (onSuccess) {
        onSuccess(result)
      }

      return result
    } catch (error: any) {
      console.error('Batch operation error:', error)

      // Show error message
      const errorMessage = error.data?.message ||
                          error.message ||
                          `批量${operation}操作失敗`
      message.error(errorMessage)

      // Call error callback
      if (onError) {
        onError(error)
      }

      throw error
    } finally {
      setIsBatchOperating(false)
    }
  }, [batchOperationMutation, showConfirmation, onSuccess, onError])

  // Convenience methods for specific operations
  const batchStart = useCallback((strategyIds: string[], allocation?: number) => {
    return handleBatchOperation(strategyIds, 'start', { allocation })
  }, [handleBatchOperation])

  const batchStop = useCallback((strategyIds: string[], reason?: string) => {
    return handleBatchOperation(strategyIds, 'stop', { reason })
  }, [handleBatchOperation])

  const batchPause = useCallback((strategyIds: string[]) => {
    return handleBatchOperation(strategyIds, 'pause')
  }, [handleBatchOperation])

  const batchResume = useCallback((strategyIds: string[]) => {
    return handleBatchOperation(strategyIds, 'resume')
  }, [handleBatchOperation])

  const batchDelete = useCallback((strategyIds: string[]) => {
    return handleBatchOperation(strategyIds, 'delete')
  }, [handleBatchOperation])

  return {
    isBatchOperating,
    handleBatchOperation,
    batchStart,
    batchStop,
    batchPause,
    batchResume,
    batchDelete,
  }
}
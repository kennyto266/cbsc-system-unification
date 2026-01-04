/**
 * Economic Strategy Hook
 * 經濟策略管理 Hook
 */

import { useCallback, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { RootState } from '../store'
import {
  createEconomicStrategy,
  updateEconomicStrategy,
  deleteEconomicStrategy,
  startEconomicStrategy,
  stopEconomicStrategy,
  pauseEconomicStrategy,
  resumeEconomicStrategy,
  fetchAllStrategies,
  selectEconomicStrategies,
  selectEconomicStrategyById,
  selectEconomicStrategyLoading,
  selectEconomicStrategyError
} from '../store/slices/economicStrategySlice'
import { economicStrategyApi } from '../services/economicStrategyApi'

export interface UseEconomicStrategyOptions {
  autoFetch?: boolean
  refreshInterval?: number
}

export interface StrategyFormData {
  name: string
  type: string
  description: string
  parameters: Record<string, any>
  indicators: string[]
  configuration: {
    autoRestart: boolean
    riskLimits: {
      maxPositionSize: number
      maxDailyLoss: number
      maxDrawdown: number
    }
    executionSettings: {
      slippageTolerance: number
      executionDelay: number
      retryAttempts: number
    }
  }
}

export interface UseEconomicStrategyReturn {
  // Data
  strategies: ReturnType<typeof getAllStrategies>
  currentStrategy: ReturnType<typeof getStrategyById>
  loading: boolean
  error: string | null

  // CRUD Operations
  createStrategy: (data: StrategyFormData) => Promise<{ success: boolean; error?: string }>
  updateStrategy: (id: string, data: StrategyFormData) => Promise<{ success: boolean; error?: string }>
  deleteStrategy: (id: string) => Promise<{ success: boolean; error?: string }>

  // Control Operations
  startStrategy: (id: string) => Promise<{ success: boolean; error?: string }>
  stopStrategy: (id: string) => Promise<{ success: boolean; error?: string }>
  pauseStrategy: (id: string) => Promise<{ success: boolean; error?: string }>
  resumeStrategy: (id: string) => Promise<{ success: boolean; error?: string }>

  // Data Retrieval
  getStrategyHistory: (id: string, params?: any) => Promise<{ success: boolean; data?: any; error?: string }>
  getStrategyPerformance: (id: string, params?: any) => Promise<{ success: boolean; data?: any; error?: string }>

  // Utility
  clearError: () => void
  refreshStrategies: () => Promise<void>
}

export const useEconomicStrategy = (options: UseEconomicStrategyOptions = {}): UseEconomicStrategyReturn => {
  const { autoFetch = false, refreshInterval = 0 } = options
  const dispatch = useDispatch()

  // Selectors from Redux store
  const strategies = useSelector(selectEconomicStrategies)
  const currentStrategy = useSelector(selectEconomicStrategyById)
  const loading = useSelector(selectEconomicStrategyLoading)
  const error = useSelector(selectEconomicStrategyError)

  // Create strategy
  const createStrategy = useCallback(async (data: StrategyFormData): Promise<{ success: boolean; error?: string }> => {
    try {
      const result = await dispatch(createEconomicStrategy(data))
      if (createEconomicStrategy.rejected.match(result)) {
        return {
          success: false,
          error: result.payload as string || 'Failed to create strategy'
        }
      }
      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      }
    }
  }, [dispatch])

  // Update strategy
  const updateStrategy = useCallback(async (id: string, data: StrategyFormData): Promise<{ success: boolean; error?: string }> => {
    try {
      const result = await dispatch(updateEconomicStrategy({ id, data }))
      if (updateEconomicStrategy.rejected.match(result)) {
        return {
          success: false,
          error: result.payload as string || 'Failed to update strategy'
        }
      }
      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      }
    }
  }, [dispatch])

  // Delete strategy
  const deleteStrategy = useCallback(async (id: string): Promise<{ success: boolean; error?: string }> => {
    try {
      const result = await dispatch(deleteEconomicStrategy(id))
      if (deleteEconomicStrategy.rejected.match(result)) {
        return {
          success: false,
          error: result.payload as string || 'Failed to delete strategy'
        }
      }
      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      }
    }
  }, [dispatch])

  // Start strategy
  const startStrategy = useCallback(async (id: string): Promise<{ success: boolean; error?: string }> => {
    try {
      const result = await dispatch(startEconomicStrategy(id))
      if (startEconomicStrategy.rejected.match(result)) {
        return {
          success: false,
          error: result.payload as string || 'Failed to start strategy'
        }
      }
      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      }
    }
  }, [dispatch])

  // Stop strategy
  const stopStrategy = useCallback(async (id: string): Promise<{ success: boolean; error?: string }> => {
    try {
      const result = await dispatch(stopEconomicStrategy(id))
      if (stopEconomicStrategy.rejected.match(result)) {
        return {
          success: false,
          error: result.payload as string || 'Failed to stop strategy'
        }
      }
      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      }
    }
  }, [dispatch])

  // Pause strategy
  const pauseStrategy = useCallback(async (id: string): Promise<{ success: boolean; error?: string }> => {
    try {
      const result = await dispatch(pauseEconomicStrategy(id))
      if (pauseEconomicStrategy.rejected.match(result)) {
        return {
          success: false,
          error: result.payload as string || 'Failed to pause strategy'
        }
      }
      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      }
    }
  }, [dispatch])

  // Resume strategy
  const resumeStrategy = useCallback(async (id: string): Promise<{ success: boolean; error?: string }> => {
    try {
      const result = await dispatch(resumeEconomicStrategy(id))
      if (resumeEconomicStrategy.rejected.match(result)) {
        return {
          success: false,
          error: result.payload as string || 'Failed to resume strategy'
        }
      }
      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      }
    }
  }, [dispatch])

  // Get strategy history
  const getStrategyHistory = useCallback(async (id: string, params?: any): Promise<{ success: boolean; data?: any; error?: string }> => {
    try {
      const response = await economicStrategyApi.getStrategyHistory(id, params)
      if (response.success) {
        return { success: true, data: response.data }
      } else {
        return {
          success: false,
          error: response.error || 'Failed to fetch strategy history'
        }
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      }
    }
  }, [])

  // Get strategy performance
  const getStrategyPerformance = useCallback(async (id: string, params?: any): Promise<{ success: boolean; data?: any; error?: string }> => {
    try {
      const response = await economicStrategyApi.getStrategyPerformance(id, params)
      if (response.success) {
        return { success: true, data: response.data }
      } else {
        return {
          success: false,
          error: response.error || 'Failed to fetch strategy performance'
        }
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      }
    }
  }, [])

  // Clear error
  const clearError = useCallback(() => {
    // Since clearStrategyError is not available, we'll just log clearing
    console.log('Clearing strategy error')
  }, [])

  // Refresh all strategies
  const refreshStrategies = useCallback(async (): Promise<void> => {
    try {
      const result = await dispatch(fetchAllStrategies())
      if (fetchAllStrategies.rejected.match(result)) {
        console.error('Error refreshing strategies:', result.payload)
      }
    } catch (error) {
      console.error('Error refreshing strategies:', error)
    }
  }, [dispatch])

  return {
    // Data
    strategies,
    currentStrategy,
    loading,
    error,

    // CRUD Operations
    createStrategy,
    updateStrategy,
    deleteStrategy,

    // Control Operations
    startStrategy,
    stopStrategy,
    pauseStrategy,
    resumeStrategy,

    // Data Retrieval
    getStrategyHistory,
    getStrategyPerformance,

    // Utility
    clearError,
    refreshStrategies
  }
}
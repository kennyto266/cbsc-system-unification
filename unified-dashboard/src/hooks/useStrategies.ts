import { useState, useEffect } from 'react'
import { message } from 'antd'
import {
  useGetStrategiesQuery,
  useCreateStrategyMutation,
  useUpdateStrategyMutation,
  useDeleteStrategyMutation,
  useUpdateStrategyStatusMutation,
} from '../store/api/strategyApi'
import { Strategy, StrategyType, StrategyStatus } from '../types'

// Custom hook for strategy management
export const useStrategies = () => {
  const [filters, setFilters] = useState<{
    type?: StrategyType
    status?: StrategyStatus
    riskLevel?: string
    search?: string
  }>({})

  // Query for strategies with filters
  const {
    data: strategies,
    isLoading,
    error,
    refetch,
  } = useGetStrategiesQuery({
    ...filters,
    page: 1,
    limit: 100,
    sortBy: 'updatedAt',
    sortOrder: 'desc',
  })

  // Mutations
  const [createStrategy, { isLoading: isCreating }] = useCreateStrategyMutation()
  const [updateStrategy, { isLoading: isUpdating }] = useUpdateStrategyMutation()
  const [deleteStrategy, { isLoading: isDeleting }] = useDeleteStrategyMutation()
  const [updateStatus, { isLoading: isUpdatingStatus }] = useUpdateStrategyStatusMutation()

  // Handle create strategy
  const handleCreateStrategy = async (strategyData: Partial<Strategy>) => {
    try {
      const result = await createStrategy(strategyData).unwrap()
      message.success('策略创建成功')
      refetch()
      return result
    } catch (error: any) {
      message.error(error.message || '创建策略失败')
      throw error
    }
  }

  // Handle update strategy
  const handleUpdateStrategy = async (id: string, strategyData: Partial<Strategy>) => {
    try {
      const result = await updateStrategy({ id, strategy: strategyData }).unwrap()
      message.success('策略更新成功')
      refetch()
      return result
    } catch (error: any) {
      message.error(error.message || '更新策略失败')
      throw error
    }
  }

  // Handle delete strategy
  const handleDeleteStrategy = async (id: string) => {
    try {
      await deleteStrategy(id).unwrap()
      message.success('策略删除成功')
      refetch()
    } catch (error: any) {
      message.error(error.message || '删除策略失败')
      throw error
    }
  }

  // Handle update strategy status
  const handleUpdateStatus = async (id: string, status: StrategyStatus) => {
    try {
      const result = await updateStatus({ id, status }).unwrap()
      message.success(`策略状态已更新为: ${status}`)
      refetch()
      return result
    } catch (error: any) {
      message.error(error.message || '更新状态失败')
      throw error
    }
  }

  // Bulk operations
  const handleBulkUpdateStatus = async (ids: string[], status: StrategyStatus) => {
    try {
      const promises = ids.map(id => updateStatus({ id, status }).unwrap())
      await Promise.all(promises)
      message.success(`已更新 ${ids.length} 个策略的状态`)
      refetch()
    } catch (error: any) {
      message.error('批量更新状态失败')
      throw error
    }
  }

  const handleBulkDelete = async (ids: string[]) => {
    try {
      const promises = ids.map(id => deleteStrategy(id).unwrap())
      await Promise.all(promises)
      message.success(`已删除 ${ids.length} 个策略`)
      refetch()
    } catch (error: any) {
      message.error('批量删除失败')
      throw error
    }
  }

  // Calculate statistics
  const statistics = {
    total: strategies?.length || 0,
    active: strategies?.filter(s => s.status === StrategyStatus.ACTIVE).length || 0,
    inactive: strategies?.filter(s => s.status === StrategyStatus.INACTIVE).length || 0,
    testing: strategies?.filter(s => s.status === StrategyStatus.TESTING).length || 0,
    archived: strategies?.filter(s => s.status === StrategyStatus.ARCHIVED).length || 0,
    byType: strategies?.reduce((acc, s) => {
      acc[s.type] = (acc[s.type] || 0) + 1
      return acc
    }, {} as Record<StrategyType, number>) || {},
    byRiskLevel: strategies?.reduce((acc, s) => {
      acc[s.riskLevel] = (acc[s.riskLevel] || 0) + 1
      return acc
    }, {} as Record<string, number>) || {},
  }

  // Filter strategies based on search text
  const searchStrategies = (searchText: string) => {
    if (!searchText) {
      setFilters(prev => ({ ...prev, search: undefined }))
      return
    }

    setFilters(prev => ({ ...prev, search: searchText }))
  }

  // Update filters
  const updateFilters = (newFilters: Partial<typeof filters>) => {
    setFilters(prev => ({ ...prev, ...newFilters }))
  }

  // Clear filters
  const clearFilters = () => {
    setFilters({})
  }

  return {
    // Data
    strategies: strategies || [],
    isLoading,
    error,
    statistics,
    filters,

    // Actions
    createStrategy: handleCreateStrategy,
    updateStrategy: handleUpdateStrategy,
    deleteStrategy: handleDeleteStrategy,
    updateStatus: handleUpdateStatus,
    bulkUpdateStatus: handleBulkUpdateStatus,
    bulkDelete: handleBulkDelete,
    searchStrategies,
    updateFilters,
    clearFilters,
    refetch,

    // Loading states
    isCreating,
    isUpdating,
    isDeleting,
    isUpdatingStatus,
  }
}

// Hook for single strategy operations
export const useStrategy = (id: string) => {
  const {
    data: strategy,
    isLoading,
    error,
    refetch,
  } = useGetStrategiesQuery({})

  const findStrategy = (strategies: Strategy[] | undefined, id: string) => {
    return strategies?.find(s => s.id === id)
  }

  const currentStrategy = findStrategy(strategy, id)

  return {
    strategy: currentStrategy,
    isLoading,
    error,
    refetch,
  }
}

// Hook for strategy form management
export const useStrategyForm = (initialStrategy?: Strategy) => {
  const [formData, setFormData] = useState<Partial<Strategy>>(
    initialStrategy || {
      name: '',
      description: '',
      type: StrategyType.TECHNICAL,
      status: StrategyStatus.INACTIVE,
      riskLevel: 'medium',
      parameters: {},
      performance: {
        totalReturn: 0,
        sharpeRatio: 0,
        maxDrawdown: 0,
        winRate: 0,
        profitFactor: 0,
      },
    }
  )

  const [errors, setErrors] = useState<Record<string, string>>({})
  const [touched, setTouched] = useState<Record<string, boolean>>({})

  // Update form field
  const updateField = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    setTouched(prev => ({ ...prev, [field]: true }))

    // Clear error for this field if it exists
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev }
        delete newErrors[field]
        return newErrors
      })
    }
  }

  // Update nested parameter
  const updateParameter = (param: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      parameters: {
        ...prev.parameters,
        [param]: value,
      },
    }))
    setTouched(prev => ({ ...prev, [param]: true }))
  }

  // Validate form
  const validate = () => {
    const newErrors: Record<string, string> = {}

    if (!formData.name?.trim()) {
      newErrors.name = '请输入策略名称'
    }

    if (!formData.type) {
      newErrors.type = '请选择策略类型'
    }

    if (!formData.riskLevel) {
      newErrors.riskLevel = '请选择风险等级'
    }

    setErrors(newErrors)
    setTouched(
      Object.keys(formData).reduce((acc, key) => ({ ...acc, [key]: true }), {})
    )

    return Object.keys(newErrors).length === 0
  }

  // Reset form
  const reset = () => {
    setFormData(initialStrategy || {
      name: '',
      description: '',
      type: StrategyType.TECHNICAL,
      status: StrategyStatus.INACTIVE,
      riskLevel: 'medium',
      parameters: {},
      performance: {
        totalReturn: 0,
        sharpeRatio: 0,
        maxDrawdown: 0,
        winRate: 0,
        profitFactor: 0,
      },
    })
    setErrors({})
    setTouched({})
  }

  // Get field error
  const getError = (field: string) => {
    if (!touched[field]) return null
    return errors[field] || null
  }

  // Check if field has error
  const hasError = (field: string) => {
    return touched[field] && !!errors[field]
  }

  return {
    formData,
    errors,
    touched,
    updateField,
    updateParameter,
    validate,
    reset,
    getError,
    hasError,
  }
}
import React, { useState, useCallback } from 'react'
import {
  PlayIcon,
  StopIcon,
  DocumentDuplicateIcon,
  TagIcon,
  ArrowDownTrayIcon,
  TrashIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XMarkIcon
} from '@heroicons/react/24/outline'
import {
  PlayIcon as PlayIconSolid,
  StopIcon as StopIconSolid,
  DocumentDuplicateIcon as DocumentDuplicateIconSolid,
  TagIcon as TagIconSolid,
  ArrowDownTrayIcon as ArrowDownTrayIconSolid,
  TrashIcon as TrashIconSolid
} from '@heroicons/react/24/solid'
import { Button } from '../../../components/ui/Button'
import { Modal } from '../../../components/ui/Modal'
import { Input } from '../../../components/ui/Input'
import { Badge } from '../../../components/ui/Badge'
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/Card'

// Props interface - 组件属性接口
interface BatchOperationsProps {
  selectedIds: string[] // Array of selected strategy IDs
  onSelectionChange: (ids: string[]) => void // Callback to update selection
  onOperationComplete?: () => void // Optional callback after operation completes
}

// Operation result interface - 操作结果接口
interface OperationResult {
  success: number // Number of successful operations
  failed: number // Number of failed operations
  failedIds: string[] // IDs that failed
}

// Batch operation configuration - 批量操作配置
const BATCH_OPERATIONS = [
  {
    id: 'start',
    name: '批量启动',
    description: '启动所有选中的策略',
    icon: PlayIcon,
    iconSolid: PlayIconSolid,
    color: 'green',
    variant: 'success' as const,
    dangerous: false
  },
  {
    id: 'stop',
    name: '批量停止',
    description: '停止所有选中的策略',
    icon: StopIcon,
    iconSolid: StopIconSolid,
    color: 'yellow',
    variant: 'secondary' as const,
    dangerous: false
  },
  {
    id: 'clone',
    name: '批量克隆',
    description: '克隆所有选中的策略',
    icon: DocumentDuplicateIcon,
    iconSolid: DocumentDuplicateIconSolid,
    color: 'blue',
    variant: 'primary' as const,
    dangerous: false
  },
  {
    id: 'categorize',
    name: '批量分类',
    description: '为所有选中的策略设置分类',
    icon: TagIcon,
    iconSolid: TagIconSolid,
    color: 'purple',
    variant: 'primary' as const,
    dangerous: false
  },
  {
    id: 'export',
    name: '批量导出',
    description: '导出所有选中的策略',
    icon: ArrowDownTrayIcon,
    iconSolid: ArrowDownTrayIconSolid,
    color: 'indigo',
    variant: 'primary' as const,
    dangerous: false
  },
  {
    id: 'delete',
    name: '批量删除',
    description: '删除所有选中的策略',
    icon: TrashIcon,
    iconSolid: TrashIconSolid,
    color: 'red',
    variant: 'danger' as const,
    dangerous: true
  }
] as const

// Main BatchOperations component - 批量操作组件
export const BatchOperations: React.FC<BatchOperationsProps> = ({
  selectedIds,
  onSelectionChange,
  onOperationComplete
}) => {
  // State management - 状态管理
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [selectedOperation, setSelectedOperation] = useState<typeof BATCH_OPERATIONS[0] | null>(null)
  const [isExecuting, setIsExecuting] = useState(false)
  const [operationResult, setOperationResult] = useState<OperationResult | null>(null)
  const [confirmationText, setConfirmationText] = useState('')
  const [categoryText, setCategoryText] = useState('')

  // Check if operation can be executed - 检查操作是否可以执行
  const canExecuteOperation = useCallback(() => {
    if (!selectedOperation || selectedIds.length === 0) return false

    // For dangerous operations, require confirmation text
    if (selectedOperation.dangerous && selectedOperation.id === 'delete') {
      return confirmationText === 'DELETE'
    }

    return true
  }, [selectedOperation, selectedIds.length, confirmationText])

  // Execute batch operation - 执行批量操作
  const executeOperation = useCallback(async () => {
    if (!selectedOperation || selectedIds.length === 0) return

    setIsExecuting(true)
    setOperationResult(null)

    try {
      // Simulate API call with delay - 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1500))

      // Simulate random failures - 模拟随机失败
      const failedCount = Math.floor(Math.random() * Math.ceil(selectedIds.length * 0.1))
      const successCount = selectedIds.length - failedCount

      // Generate random failed IDs - 生成随机失败的ID
      const shuffled = [...selectedIds].sort(() => Math.random() - 0.5)
      const failedIds = shuffled.slice(0, failedCount)

      const result: OperationResult = {
        success: successCount,
        failed: failedCount,
        failedIds
      }

      setOperationResult(result)

      // Clear selection on complete success - 完全成功时清除选择
      if (failedCount === 0) {
        onSelectionChange([])
        setTimeout(() => {
          setIsModalOpen(false)
          resetModalState()
        }, 1000)
      }

      // Call completion callback - 调用完成回调
      onOperationComplete?.()

    } catch (error) {
      console.error('Batch operation failed:', error)
      setOperationResult({
        success: 0,
        failed: selectedIds.length,
        failedIds: selectedIds
      })
    } finally {
      setIsExecuting(false)
    }
  }, [selectedOperation, selectedIds, onSelectionChange, onOperationComplete])

  // Reset modal state - 重置模态框状态
  const resetModalState = useCallback(() => {
    setSelectedOperation(null)
    setConfirmationText('')
    setCategoryText('')
    setOperationResult(null)
  }, [])

  // Handle operation click - 处理操作点击
  const handleOperationClick = useCallback((operation: typeof BATCH_OPERATIONS[0]) => {
    setSelectedOperation(operation)
    setIsModalOpen(true)
    resetModalState()
  }, [resetModalState])

  // Handle modal close - 处理模态框关闭
  const handleModalClose = useCallback(() => {
    if (!isExecuting) {
      setIsModalOpen(false)
      setTimeout(() => resetModalState(), 300)
    }
  }, [isExecuting, resetModalState])

  // Clear selection - 清除选择
  const clearSelection = useCallback(() => {
    onSelectionChange([])
  }, [onSelectionChange])

  // Render operation icon - 渲染操作图标
  const renderOperationIcon = (operation: typeof BATCH_OPERATIONS[0]) => {
    const IconComponent = operation.iconSolid
    const colorClasses = {
      green: 'text-green-600',
      yellow: 'text-yellow-600',
      blue: 'text-blue-600',
      purple: 'text-purple-600',
      indigo: 'text-indigo-600',
      red: 'text-red-600'
    }

    return (
      <IconComponent className={`h-8 w-8 ${colorClasses[operation.color]}`} />
    )
  }

  // Render operation card - 渲染操作卡片
  const renderOperationCard = (operation: typeof BATCH_OPERATIONS[0]) => (
    <Card
      key={operation.id}
      className="group cursor-pointer transition-all duration-200 hover:shadow-md hover:scale-105"
      onClick={() => handleOperationClick(operation)}
    >
      <CardContent className="p-6">
        <div className="flex flex-col items-center text-center space-y-3">
          {renderOperationIcon(operation)}
          <h3 className="font-semibold text-gray-900 group-hover:text-gray-700 transition-colors">
            {operation.name}
          </h3>
          <p className="text-sm text-gray-500">
            {operation.description}
          </p>
        </div>
      </CardContent>
    </Card>
  )

  // Render modal content - 渲染模态框内容
  const renderModalContent = () => {
    if (!selectedOperation) return null

    return (
      <div className="space-y-6">
        {/* Operation details - 操作详情 */}
        <div className="text-center">
          <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-gray-100 mb-4">
            {renderOperationIcon(selectedOperation)}
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {selectedOperation.name}
          </h3>
          <p className="text-sm text-gray-500">
            将对 {selectedIds.length} 个选中的策略执行此操作
          </p>
        </div>

        {/* Category input for categorize operation - 分类操作的分类输入 */}
        {selectedOperation.id === 'categorize' && (
          <div>
            <Input
              label="分类名称"
              placeholder="请输入分类名称"
              value={categoryText}
              onChange={(e) => setCategoryText(e.target.value)}
              leftIcon={<TagIcon className="h-4 w-4 text-gray-400" />}
            />
          </div>
        )}

        {/* Confirmation for dangerous operations - 危险操作的确认 */}
        {selectedOperation.dangerous && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-3">
              <ExclamationTriangleIcon className="h-5 w-5 text-red-600" />
              <h4 className="font-semibold text-red-900">危险操作警告</h4>
            </div>
            <p className="text-sm text-red-700 mb-4">
              此操作将永久删除 {selectedIds.length} 个策略，无法恢复。
              请输入 <span className="font-mono font-bold bg-red-100 px-1">DELETE</span> 来确认。
            </p>
            <Input
              placeholder="输入 DELETE 确认删除"
              value={confirmationText}
              onChange={(e) => setConfirmationText(e.target.value)}
              error={confirmationText && confirmationText !== 'DELETE' ? '请输入正确的确认文本' : undefined}
            />
          </div>
        )}

        {/* Operation result display - 操作结果展示 */}
        {operationResult && (
          <div className={`rounded-lg p-4 ${
            operationResult.failed === 0
              ? 'bg-green-50 border border-green-200'
              : 'bg-yellow-50 border border-yellow-200'
          }`}>
            <div className="flex items-center space-x-2 mb-2">
              {operationResult.failed === 0 ? (
                <CheckCircleIcon className="h-5 w-5 text-green-600" />
              ) : (
                <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600" />
              )}
              <h4 className={`font-semibold ${
                operationResult.failed === 0 ? 'text-green-900' : 'text-yellow-900'
              }`}>
                操作完成
              </h4>
            </div>
            <div className="space-y-1 text-sm">
              <p className={operationResult.failed === 0 ? 'text-green-700' : 'text-yellow-700'}>
                成功: {operationResult.success} 个策略
              </p>
              {operationResult.failed > 0 && (
                <p className="text-yellow-700">
                  失败: {operationResult.failed} 个策略
                </p>
              )}
            </div>
          </div>
        )}

        {/* Action buttons - 操作按钮 */}
        <div className="flex justify-end space-x-3 pt-4 border-t">
          <Button
            variant="outline"
            onClick={handleModalClose}
            disabled={isExecuting}
          >
            {operationResult ? '关闭' : '取消'}
          </Button>
          {!operationResult && (
            <Button
              variant={selectedOperation.variant}
              onClick={executeOperation}
              disabled={!canExecuteOperation() || isExecuting}
              loading={isExecuting}
            >
              {isExecuting ? '执行中...' : `确认${selectedOperation.name}`}
            </Button>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Selected strategies summary - 选中策略摘要 */}
      {selectedIds.length > 0 && (
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium text-blue-900">
                    已选择 {selectedIds.length} 个策略
                  </span>
                  <Badge variant="primary" size="sm">
                    {selectedIds.length}
                  </Badge>
                </div>
                {selectedIds.length > 5 && (
                  <span className="text-xs text-blue-700">
                    显示前 5 个
                  </span>
                )}
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={clearSelection}
                icon={<XMarkIcon className="h-4 w-4" />}
              >
                清除选择
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Operations grid - 操作网格 */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          批量操作
        </h2>
        {selectedIds.length === 0 ? (
          <Card className="bg-gray-50 border-gray-200">
            <CardContent className="p-8 text-center">
              <div className="text-gray-400 mb-2">
                <TagIcon className="h-12 w-12 mx-auto" />
              </div>
              <p className="text-gray-600 font-medium">未选择策略</p>
              <p className="text-sm text-gray-500 mt-1">
                请先选择要执行批量操作的策略
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {BATCH_OPERATIONS.map(operation => renderOperationCard(operation))}
          </div>
        )}
      </div>

      {/* Operation confirmation modal - 操作确认模态框 */}
      <Modal
        isOpen={isModalOpen}
        onClose={handleModalClose}
        size="md"
        closeOnBackdropClick={!isExecuting}
        closeOnEscape={!isExecuting}
        showCloseButton={!isExecuting}
      >
        {renderModalContent()}
      </Modal>
    </div>
  )
}
import React, { useState, useEffect, useCallback } from 'react';
import { toast } from 'react-toastify';
import StrategyToggleEnhanced from './StrategyToggleEnhanced';
import BatchOperationsPanel from './BatchOperationsPanel';
import strategyControlService from '../../services/strategyControlService';

interface Strategy {
  id: string;
  name: string;
  type: string;
  category: string;
  status: string;
  isActive: boolean;
  lastUpdated?: Date;
  description?: string;
}

interface StrategyControlDashboardProps {
  strategies: Strategy[];
  onStrategyUpdate?: (strategyId: string, newStatus: boolean) => void;
  className?: string;
}

// Comprehensive strategy control dashboard
export const StrategyControlDashboard: React.FC<StrategyControlDashboardProps> = ({
  strategies,
  onStrategyUpdate,
  className = ''
}) => {
  const [selectedStrategies, setSelectedStrategies] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(false);
  const [operationHistory, setOperationHistory] = useState<Array<{
    id: string;
    action: string;
    strategyName: string;
    timestamp: Date;
    status: 'success' | 'failed';
    reason?: string;
  }>>([]);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [filterStatus, setFilterStatus] = useState<'all' | 'active' | 'inactive'>('all');
  const [searchTerm, setSearchTerm] = useState('');

  // Filter strategies based on current filter and search
  const filteredStrategies = React.useMemo(() => {
    let filtered = [...strategies];

    // Apply status filter
    if (filterStatus !== 'all') {
      filtered = filtered.filter(strategy => {
        if (filterStatus === 'active') {
          return strategy.isActive || strategy.status === 'active';
        } else if (filterStatus === 'inactive') {
          return !strategy.isActive && strategy.status !== 'active';
        }
        return true;
      });
    }

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(strategy =>
        strategy.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        strategy.type.toLowerCase().includes(searchTerm.toLowerCase()) ||
        strategy.category.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    return filtered;
  }, [strategies, filterStatus, searchTerm]);

  // Handle individual strategy control
  const handleStrategyControl = useCallback(async (strategyId: string, action: 'enable' | 'disable' | 'start' | 'stop' | 'pause'): Promise<boolean> => {
    try {
      const result = await strategyControlService.controlStrategy(strategyId, { action });

      // Update local state
      if (result.success && onStrategyUpdate) {
        onStrategyUpdate(strategyId, result.new_status);
      }

      // Add to operation history
      const strategy = strategies.find(s => s.id === strategyId);
      setOperationHistory(prev => [{
        id: result.timestamp + '_' + strategyId,
        action,
        strategyName: strategy?.name || strategyId,
        timestamp: new Date(result.timestamp),
        status: result.success ? 'success' : 'failed',
        reason: result.message
      }, ...prev.slice(0, 9)]); // Keep only last 10 operations

      return result.success;
    } catch (error) {
      console.error('策略控制失敗:', error);
      return false;
    }
  }, [strategies, onStrategyUpdate]);

  // Handle batch strategy control
  const handleBatchControl = useCallback(async (strategyIds: string[], action: 'enable' | 'disable' | 'start' | 'stop' | 'pause', reason?: string) => {
    try {
      const result = await strategyControlService.batchControlStrategies({
        strategy_ids: strategyIds,
        action,
        reason
      });

      // Update local state for successful operations
      if (onStrategyUpdate) {
        result.results.forEach(r => {
          if (r.success) {
            onStrategyUpdate(r.strategy_id, r.new_status);
          }
        });
      }

      // Add batch operation to history
      const batchHistory = result.results.map(r => ({
        id: 'batch_' + r.timestamp + '_' + r.strategy_id,
        action: `batch_${action}`,
        strategyName: strategies.find(s => s.id === r.strategy_id)?.name || r.strategy_id,
        timestamp: new Date(r.timestamp),
        status: r.success ? 'success' : 'failed' as 'success' | 'failed',
        reason: r.message
      }));

      setOperationHistory(prev => [...batchHistory, ...prev.slice(0, 10 - batchHistory.length)]);

      return {
        success_count: result.success_count,
        failure_count: result.failure_count,
        results: result.results.map(r => ({
          strategy_id: r.strategy_id,
          success: r.success,
          message: r.message
        }))
      };
    } catch (error) {
      console.error('批量控制失敗:', error);
      throw error;
    }
  }, [strategies, onStrategyUpdate]);

  // Strategy status summary
  const statusSummary = React.useMemo(() => {
    const active = strategies.filter(s => s.isActive || s.status === 'active').length;
    const inactive = strategies.filter(s => !s.isActive && s.status !== 'active').length;
    return { active, inactive, total: strategies.length };
  }, [strategies]);

  return (
    <div className={`strategy-control-dashboard ${className}`}>
      {/* Header with Summary */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">策略控制中心</h2>
            <p className="text-gray-600">管理您的量化交易策略啟用/禁用狀態</p>
          </div>

          {/* Status Summary */}
          <div className="flex space-x-4">
            <div className="text-center p-3 bg-green-50 rounded-lg border border-green-200">
              <div className="text-2xl font-bold text-green-600">{statusSummary.active}</div>
              <div className="text-sm text-green-700">運行中</div>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg border border-gray-200">
              <div className="text-2xl font-bold text-gray-600">{statusSummary.inactive}</div>
              <div className="text-sm text-gray-700">已停止</div>
            </div>
            <div className="text-center p-3 bg-blue-50 rounded-lg border border-blue-200">
              <div className="text-2xl font-bold text-blue-600">{statusSummary.total}</div>
              <div className="text-sm text-blue-700">總策略</div>
            </div>
          </div>
        </div>
      </div>

      {/* Controls and Filters */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 mb-6">
        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
          {/* Search */}
          <div className="flex-1 max-w-md">
            <div className="relative">
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="搜索策略名稱、類型或分類..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <svg className="absolute left-3 top-2.5 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
          </div>

          {/* Filters */}
          <div className="flex items-center space-x-4">
            {/* Status Filter */}
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-600">狀態:</span>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value as any)}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">全部</option>
                <option value="active">運行中</option>
                <option value="inactive">已停止</option>
              </select>
            </div>

            {/* View Mode */}
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-600">檢視:</span>
              <div className="flex bg-gray-100 rounded-lg p-1">
                <button
                  onClick={() => setViewMode('grid')}
                  className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                    viewMode === 'grid'
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  網格
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                    viewMode === 'list'
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  列表
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Batch Operations Panel */}
      <BatchOperationsPanel
        strategies={filteredStrategies}
        selectedStrategies={selectedStrategies}
        onSelectionChange={setSelectedStrategies}
        onBatchControl={handleBatchControl}
        isLoading={isLoading}
      />

      {/* Strategy List/Grid */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
        {filteredStrategies.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-gray-400 mb-4">
              <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              {searchTerm ? '沒有找到匹配的策略' : '沒有策略'}
            </h3>
            <p className="text-gray-600">
              {searchTerm ? '請嘗試其他搜索詞或清除過濾條件' : '請先添加策略到系統中'}
            </p>
          </div>
        ) : (
          <div className={
            viewMode === 'grid'
              ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4'
              : 'space-y-4'
          }>
            {filteredStrategies.map((strategy) => (
              <div
                key={strategy.id}
                className={`border rounded-lg p-4 transition-all duration-200 hover:shadow-md ${
                  viewMode === 'list'
                    ? 'flex items-center justify-between'
                    : 'flex flex-col space-y-4'
                } ${
                  selectedStrategies.has(strategy.id)
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200'
                }`}
              >
                {/* Selection Checkbox */}
                <div className={viewMode === 'list' ? 'mr-4' : 'self-end'}>
                  <input
                    type="checkbox"
                    checked={selectedStrategies.has(strategy.id)}
                    onChange={() => {
                      const newSelected = new Set(selectedStrategies);
                      if (newSelected.has(strategy.id)) {
                        newSelected.delete(strategy.id);
                      } else {
                        newSelected.add(strategy.id);
                      }
                      setSelectedStrategies(newSelected);
                    }}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                </div>

                {/* Strategy Info */}
                <div className={viewMode === 'list' ? 'flex-1' : ''}>
                  <div className="flex items-center space-x-2 mb-2">
                    <h3 className="font-semibold text-gray-900">{strategy.name}</h3>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      strategy.isActive || strategy.status === 'active'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {strategy.isActive || strategy.status === 'active' ? '運行中' : '已停止'}
                    </span>
                  </div>

                  <div className="text-sm text-gray-600 space-y-1">
                    <div>類型: {strategy.type}</div>
                    <div>分類: {strategy.category}</div>
                    {strategy.lastUpdated && (
                      <div>更新: {new Date(strategy.lastUpdated).toLocaleString()}</div>
                    )}
                  </div>

                  {strategy.description && viewMode === 'grid' && (
                    <p className="text-xs text-gray-500 mt-2 line-clamp-2">{strategy.description}</p>
                  )}
                </div>

                {/* Strategy Toggle */}
                <div className={viewMode === 'list' ? 'ml-4' : ''}>
                  <StrategyToggleEnhanced
                    strategyId={strategy.id}
                    strategyName={strategy.name}
                    isActive={strategy.isActive}
                    status={strategy.status}
                    onToggle={handleStrategyControl}
                    size={viewMode === 'list' ? 'small' : 'medium'}
                    showLabels={viewMode === 'grid'}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Operation History */}
      {operationHistory.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-gray-900">操作歷史</h3>
            <button
              onClick={() => setOperationHistory([])}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              清除
            </button>
          </div>

          <div className="space-y-2 max-h-64 overflow-y-auto">
            {operationHistory.map((op) => (
              <div key={op.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                <div className="flex items-center space-x-3">
                  <div className={`w-2 h-2 rounded-full ${
                    op.status === 'success' ? 'bg-green-500' : 'bg-red-500'
                  }`}></div>
                  <div>
                    <div className="text-sm font-medium">{op.strategyName}</div>
                    <div className="text-xs text-gray-500">
                      {op.action.replace('_', ' ').toUpperCase()} {op.reason && `• ${op.reason}`}
                    </div>
                  </div>
                </div>
                <div className="text-xs text-gray-400">
                  {op.timestamp.toLocaleTimeString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default StrategyControlDashboard;
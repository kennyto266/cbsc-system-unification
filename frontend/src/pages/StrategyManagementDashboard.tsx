/**
 * Strategy Management Dashboard
 * 策略管理儀表板主頁面
 */

import React, { useEffect, useState, useMemo } from 'react';
import {
  PlusIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  Cog6ToothIcon,
  ChartBarIcon,
  PlayIcon,
  StopIcon,
  TrashIcon,
  PencilIcon,
  EyeIcon
} from '@heroicons/react/24/outline';
import { useDispatch, useSelector } from 'react-redux';

// Import components
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Modal } from '../components/ui/Modal';
import { Alert } from '../components/ui/Alert';
import { Loading } from '../components/ui/Loading';
import { Pagination } from '../components/ui/Pagination';
import { Badge } from '../components/ui/Badge';
import { Card } from '../components/ui/Card';
import StrategyCreateForm from '../components/StrategyCreateForm';
import StrategyEditForm from '../components/StrategyEditForm';
import StrategyDetail from '../components/StrategyDetail';

// Import hooks and utilities
import { useDebounce } from '../hooks/useDebounce';
import { formatDate } from '../utils/dateUtils';

// Import types and actions
import {
  Strategy,
  StrategyType,
  StrategyStatus,
  RiskTolerance,
  TimeRange
} from '../types/strategyTypes';

import {
  fetchStrategies,
  deleteStrategy,
  executeStrategy,
  toggleStrategySelection,
  clearSelection,
  selectAllStrategies,
  setFilter,
  clearFilter
} from '../store/strategies/strategySlice';

import {
  selectStrategies,
  selectStrategiesLoading,
  selectStrategiesError,
  selectStrategiesPagination,
  selectSelectedStrategies,
  selectFilter
} from '../store/strategies/strategySlice';

/**
 * Strategy status badge component
 * 策略狀態徽章組件
 */
const StrategyStatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const statusConfig = {
    active: {
      color: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
      label: '活躍'
    },
    inactive: {
      color: 'bg-gray-100 text-gray-800 dark:bg-gray-800/50 dark:text-gray-300',
      label: '非活躍'
    },
    draft: {
      color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
      label: '草稿'
    },
    testing: {
      color: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
      label: '測試中'
    },
    archived: {
      color: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
      label: '已歸檔'
    }
  };

  const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.draft;

  return (
    <Badge className={config.color}>
      {config.label}
    </Badge>
  );
};

/**
 * Strategy type badge component
 * 策略類型徽章組件
 */
const StrategyTypeBadge: React.FC<{ type: StrategyType }> = ({ type }) => {
  const typeConfig = {
    technical_indicators: {
      color: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
      label: '技術指標'
    },
    momentum: {
      color: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400',
      label: '動量'
    },
    mean_reversion: {
      color: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-400',
      label: '均值回歸'
    },
    volume: {
      color: 'bg-pink-100 text-pink-800 dark:bg-pink-900/30 dark:text-pink-400',
      label: '成交量'
    },
    volatility: {
      color: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400',
      label: '波動率'
    },
    fundamental: {
      color: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
      label: '基本面'
    },
    portfolio: {
      color: 'bg-teal-100 text-teal-800 dark:bg-teal-900/30 dark:text-teal-400',
      label: '投資組合'
    },
    arbitrage: {
      color: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
      label: '套利'
    },
    macro: {
      color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
      label: '宏觀'
    }
  };

  const config = typeConfig[type] || typeConfig.technical_indicators;

  return (
    <Badge className={config.color}>
      {config.label}
    </Badge>
  );
};

/**
 * Risk tolerance badge component
 * 風險承受度徽章組件
 */
const RiskToleranceBadge: React.FC<{ tolerance: RiskTolerance }> = ({ tolerance }) => {
  const toleranceConfig = {
    low: {
      color: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
      label: '低風險'
    },
    medium: {
      color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
      label: '中等風險'
    },
    high: {
      color: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400',
      label: '高風險'
    },
    extreme: {
      color: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
      label: '極高風險'
    }
  };

  const config = toleranceConfig[tolerance] || toleranceConfig.medium;

  return (
    <Badge className={config.color}>
      {config.label}
    </Badge>
  );
};

/**
 * Strategy Management Dashboard Component
 * 策略管理儀表板組件
 */
export const StrategyManagementDashboard: React.FC = () => {
  const dispatch = useDispatch();

  // State from Redux store
  const strategies = useSelector(selectStrategies);
  const loading = useSelector(selectStrategiesLoading);
  const error = useSelector(selectStrategiesError);
  const pagination = useSelector(selectStrategiesPagination);
  const selectedStrategies = useSelector(selectSelectedStrategies);
  const currentFilter = useSelector(selectFilter);

  // Local state
  const [searchTerm, setSearchTerm] = useState('');
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [strategyToDelete, setStrategyToDelete] = useState<Strategy | null>(null);
  const [showExecuteModal, setShowExecuteModal] = useState(false);
  const [strategyToExecute, setStrategyToExecute] = useState<Strategy | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  // Form states
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);
  const [editingStrategyId, setEditingStrategyId] = useState<string | null>(null);
  const [showDetail, setShowDetail] = useState(false);
  const [detailStrategyId, setDetailStrategyId] = useState<string | null>(null);

  // Debounced search term
  const debouncedSearchTerm = useDebounce(searchTerm, 500);

  // Fetch strategies on mount and when dependencies change
  useEffect(() => {
    dispatch(fetchStrategies({
      page: currentPage,
      pageSize,
      search: debouncedSearchTerm,
      ...currentFilter
    }));
  }, [dispatch, currentPage, pageSize, debouncedSearchTerm, currentFilter]);

  // Handle search
  const handleSearch = (term: string) => {
    setSearchTerm(term);
    setCurrentPage(1); // Reset to first page when searching
  };

  // Handle pagination
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  const handlePageSizeChange = (size: number) => {
    setPageSize(size);
    setCurrentPage(1);
  };

  // Handle strategy selection
  const handleSelectStrategy = (strategyId: string) => {
    dispatch(toggleStrategySelection(strategyId));
  };

  const handleSelectAll = () => {
    if (selectedStrategies.length === strategies.length) {
      dispatch(clearSelection());
    } else {
      dispatch(selectAllStrategies());
    }
  };

  // Handle strategy deletion
  const handleDeleteStrategy = (strategy: Strategy) => {
    setStrategyToDelete(strategy);
    setShowDeleteModal(true);
  };

  const confirmDelete = async () => {
    if (strategyToDelete) {
      try {
        await dispatch(deleteStrategy(strategyToDelete.id)).unwrap();
        setShowDeleteModal(false);
        setStrategyToDelete(null);
      } catch (error) {
        console.error('Failed to delete strategy:', error);
      }
    }
  };

  // Handle strategy execution
  const handleExecuteStrategy = (strategy: Strategy) => {
    setStrategyToExecute(strategy);
    setShowExecuteModal(true);
  };

  const confirmExecute = async () => {
    if (strategyToExecute) {
      try {
        await dispatch(executeStrategy({
          strategyId: strategyToExecute.id,
          executionRequest: {
            config_id: strategyToExecute.id, // Use strategy ID as config ID for now
            backtest_type: 'simple'
          }
        })).unwrap();
        setShowExecuteModal(false);
        setStrategyToExecute(null);
      } catch (error) {
        console.error('Failed to execute strategy:', error);
      }
    }
  };

  // Handle filtering
  const handleFilter = (filterKey: string, value: any) => {
    dispatch(setFilter({ ...currentFilter, [filterKey]: value }));
    setCurrentPage(1);
  };

  const clearAllFilters = () => {
    dispatch(clearFilter());
    setCurrentPage(1);
  };

  // Filter options
  const strategyTypes = Object.values(StrategyType);
  const statusOptions = Object.values(StrategyStatus);

  // Render loading state
  if (loading && strategies.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loading size="lg" text="載入策略中..." />
      </div>
    );
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white">策略管理</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            管理和監控您的量化交易策略
          </p>
        </div>
        <Button
          variant="primary"
          icon={<PlusIcon />}
          onClick={() => {
            setShowCreateForm(true);
          }}
          className="w-full sm:w-auto"
        >
          創建策略
        </Button>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert
          variant="error"
          title="錯誤"
          description={error}
          onClose={() => {
            // Clear error - would need to implement clearError action
          }}
        />
      )}

      {/* Search and Filters */}
      <Card className="p-3 sm:p-4">
        <div className="flex flex-col space-y-3 lg:flex-row lg:space-y-0 lg:space-x-4">
          {/* Search */}
          <div className="flex-1">
            <Input
              placeholder="搜索策略名稱或描述..."
              value={searchTerm}
              onChange={(e) => handleSearch(e.target.value)}
              icon={<MagnifyingGlassIcon />}
              className="w-full"
            />
          </div>

          {/* Filters */}
          <div className="flex flex-col sm:flex-row gap-2 lg:flex-row lg:gap-2">
            <select
              className="block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              value={currentFilter.strategy_type || ''}
              onChange={(e) => handleFilter('strategy_type', e.target.value || undefined)}
            >
              <option value="">所有類型</option>
              {strategyTypes.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>

            <select
              className="block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              value={currentFilter.is_active?.toString() || ''}
              onChange={(e) => handleFilter('is_active', e.target.value === 'true' ? true : e.target.value === 'false' ? false : undefined)}
            >
              <option value="">所有狀態</option>
              <option value="true">活躍</option>
              <option value="false">非活躍</option>
            </select>

            {(Object.keys(currentFilter).length > 0) && (
              <Button
                variant="outline"
                size="sm"
                onClick={clearAllFilters}
                className="w-full sm:w-auto"
              >
                清除篩選
              </Button>
            )}
          </div>
        </div>
      </Card>

      {/* Actions Bar */}
      {selectedStrategies.length > 0 && (
        <Card className="p-3 sm:p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <span className="text-sm text-blue-800 dark:text-blue-200">
              已選擇 {selectedStrategies.length} 個策略
            </span>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={clearSelection}
                className="w-full sm:w-auto"
              >
                取消選擇
              </Button>
              {/* Add batch action buttons here */}
            </div>
          </div>
        </Card>
      )}

      {/* Strategies Table - Desktop */}
      <Card className="hidden md:block">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  <input
                    type="checkbox"
                    checked={selectedStrategies.length === strategies.length && strategies.length > 0}
                    onChange={handleSelectAll}
                    className="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500 dark:focus:ring-blue-400"
                  />
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  策略名稱
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  類型
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  狀態
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  創建時間
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
              {strategies.map((strategy) => (
                <tr key={strategy.id} className="hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <input
                      type="checkbox"
                      checked={selectedStrategies.includes(strategy.id)}
                      onChange={() => handleSelectStrategy(strategy.id)}
                      className="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500 dark:focus:ring-blue-400"
                    />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900 dark:text-white">
                        {strategy.name}
                      </div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        {strategy.version}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <StrategyTypeBadge type={strategy.strategy_type} />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <StrategyStatusBadge status={strategy.is_active ? 'active' : 'inactive'} />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    {formatDate(strategy.created_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex space-x-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        icon={<EyeIcon />}
                        onClick={() => {
                          setDetailStrategyId(strategy.id);
                          setShowDetail(true);
                        }}
                      >
                        查看
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        icon={<PencilIcon />}
                        onClick={() => {
                          setEditingStrategyId(strategy.id);
                          setShowEditForm(true);
                        }}
                      >
                        編輯
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        icon={<PlayIcon />}
                        onClick={() => handleExecuteStrategy(strategy)}
                      >
                        執行
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        icon={<TrashIcon />}
                        onClick={() => handleDeleteStrategy(strategy)}
                        className="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300"
                      >
                        刪除
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="mt-4 px-6 pb-4">
          <Pagination
            currentPage={currentPage}
            pageSize={pageSize}
            total={pagination.total}
            onPageChange={handlePageChange}
            onPageSizeChange={handlePageSizeChange}
          />
        </div>
      </Card>

      {/* Strategies Grid - Mobile */}
      <Card className="md:hidden p-4">
        <div className="space-y-4">
          {strategies.map((strategy) => (
            <div
              key={strategy.id}
              className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 space-y-3"
            >
              {/* Strategy Header */}
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3">
                  <input
                    type="checkbox"
                    checked={selectedStrategies.includes(strategy.id)}
                    onChange={() => handleSelectStrategy(strategy.id)}
                    className="mt-1 rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
                  />
                  <div>
                    <h3 className="text-sm font-medium text-gray-900 dark:text-white">
                      {strategy.name}
                    </h3>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {strategy.version}
                    </p>
                  </div>
                </div>
                <StrategyStatusBadge status={strategy.is_active ? 'active' : 'inactive'} />
              </div>

              {/* Strategy Info */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500 dark:text-gray-400">類型:</span>
                  <StrategyTypeBadge type={strategy.strategy_type} />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500 dark:text-gray-400">創建時間:</span>
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {formatDate(strategy.created_at)}
                  </span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="grid grid-cols-4 gap-2 pt-2">
                <Button
                  variant="ghost"
                  size="sm"
                  icon={<EyeIcon />}
                  onClick={() => {
                    setDetailStrategyId(strategy.id);
                    setShowDetail(true);
                  }}
                  className="flex flex-col items-center justify-center py-2 text-xs"
                >
                  查看
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  icon={<PencilIcon />}
                  onClick={() => {
                    setEditingStrategyId(strategy.id);
                    setShowEditForm(true);
                  }}
                  className="flex flex-col items-center justify-center py-2 text-xs"
                >
                  編輯
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  icon={<PlayIcon />}
                  onClick={() => handleExecuteStrategy(strategy)}
                  className="flex flex-col items-center justify-center py-2 text-xs"
                >
                  執行
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  icon={<TrashIcon />}
                  onClick={() => handleDeleteStrategy(strategy)}
                  className="flex flex-col items-center justify-center py-2 text-xs text-red-600 dark:text-red-400"
                >
                  刪除
                </Button>
              </div>
            </div>
          ))}
        </div>

        {/* Mobile Pagination */}
        <div className="mt-6">
          <Pagination
            currentPage={currentPage}
            pageSize={pageSize}
            total={pagination.total}
            onPageChange={handlePageChange}
            onPageSizeChange={handlePageSizeChange}
          />
        </div>
      </Card>

      {/* Empty State */}
      {!loading && strategies.length === 0 && (
        <Card className="p-6 sm:p-8 text-center">
          <div className="space-y-4">
            <ChartBarIcon className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-600" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">沒有找到策略</h3>
            <p className="text-gray-500 dark:text-gray-400">
              開始創建您的第一個量化交易策略吧！
            </p>
            <Button
              variant="primary"
              icon={<PlusIcon />}
              onClick={() => {
                setShowCreateForm(true);
              }}
              className="w-full sm:w-auto"
            >
              創建策略
            </Button>
          </div>
        </Card>
      )}

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={showDeleteModal}
        onClose={() => {
          setShowDeleteModal(false);
          setStrategyToDelete(null);
        }}
        title="刪除策略"
      >
        <div className="space-y-4">
          <p className="text-gray-700">
            確定要刪除策略 "{strategyToDelete?.name}" 嗎？此操作無法撤銷。
          </p>
          <div className="flex justify-end space-x-2">
            <Button
              variant="outline"
              onClick={() => {
                setShowDeleteModal(false);
                setStrategyToDelete(null);
              }}
            >
              取消
            </Button>
            <Button
              variant="danger"
              onClick={confirmDelete}
            >
              刪除
            </Button>
          </div>
        </div>
      </Modal>

      {/* Execute Confirmation Modal */}
      <Modal
        isOpen={showExecuteModal}
        onClose={() => {
          setShowExecuteModal(false);
          setStrategyToExecute(null);
        }}
        title="執行策略"
      >
        <div className="space-y-4">
          <p className="text-gray-700">
            確定要執行策略 "{strategyToExecute?.name}" 嗎？
          </p>
          <div className="flex justify-end space-x-2">
            <Button
              variant="outline"
              onClick={() => {
                setShowExecuteModal(false);
                setStrategyToExecute(null);
              }}
            >
              取消
            </Button>
            <Button
              variant="primary"
              onClick={confirmExecute}
            >
              執行
            </Button>
          </div>
        </div>
      </Modal>

      {/* Strategy Create Form Modal */}
      <StrategyCreateForm
        isOpen={showCreateForm}
        onClose={() => {
          setShowCreateForm(false);
          // Refresh the strategies list after creating
          dispatch(fetchStrategies({
            page: currentPage,
            pageSize,
            search: debouncedSearchTerm,
            ...currentFilter
          }));
        }}
        onSuccess={(strategy) => {
          console.log('Strategy created successfully:', strategy);
        }}
      />

      {/* Strategy Edit Form Modal */}
      {editingStrategyId && (
        <StrategyEditForm
          isOpen={showEditForm}
          onClose={() => {
            setShowEditForm(false);
            setEditingStrategyId(null);
            // Refresh the strategies list after editing
            dispatch(fetchStrategies({
              page: currentPage,
              pageSize,
              search: debouncedSearchTerm,
              ...currentFilter
            }));
          }}
          strategyId={editingStrategyId}
          onSuccess={(strategy) => {
            console.log('Strategy updated successfully:', strategy);
          }}
        />
      )}

      {/* Strategy Detail Modal */}
      {detailStrategyId && (
        <Modal
          isOpen={showDetail}
          onClose={() => {
            setShowDetail(false);
            setDetailStrategyId(null);
          }}
          title="策略詳情"
          size="full"
        >
          <StrategyDetail
            strategyId={detailStrategyId}
            onEdit={(strategy) => {
              setShowDetail(false);
              setDetailStrategyId(null);
              setEditingStrategyId(strategy.id);
              setShowEditForm(true);
            }}
            onExecute={(strategy) => {
              setShowDetail(false);
              setDetailStrategyId(null);
              handleExecuteStrategy(strategy);
            }}
            onClose={() => {
              setShowDetail(false);
              setDetailStrategyId(null);
            }}
          />
        </Modal>
      )}
    </div>
  );
};

export default StrategyManagementDashboard;
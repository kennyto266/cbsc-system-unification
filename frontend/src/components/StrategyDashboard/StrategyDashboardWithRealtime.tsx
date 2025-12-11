import React, { useState, useEffect, useCallback, useRef } from 'react';
import { StrategyCard } from './StrategyCard';
import { StrategyFilters } from './StrategyFilters';
import { PerformanceSummary } from './PerformanceSummary';
import { RealTimeMonitor } from './RealTimeMonitor';
import { RefreshControl, AutoRefreshToggle } from './RefreshControl';
import { LoadingProvider, LoadingOverlay, RefetchLoadingIndicator } from './LoadingManager';
import { getRealtimeManager } from '../../services/realtimeManager';
import { Strategy, StrategyFilter, PerformanceMetrics } from '../../types/index';
import BatchStrategyControls from '../StrategyControl/BatchStrategyControls';
import strategyControlService from '../../services/strategyControlService';
import { ChartsDashboard } from '../Charts';

interface StrategyDashboardProps {
  apiUrl?: string;
  wsUrl?: string;
  refreshInterval?: number;
  enableRealtime?: boolean;
}

export const StrategyDashboardWithRealtime: React.FC<StrategyDashboardProps> = ({
  apiUrl = '/api',
  wsUrl = 'ws://localhost:3003/ws',
  refreshInterval = 10000, // 10 seconds
  enableRealtime = true
}) => {
  // State management
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [filteredStrategies, setFilteredStrategies] = useState<Strategy[]>([]);
  const [filters, setFilters] = useState<StrategyFilter>({
    category: 'all',
    status: 'all',
    performance: 'all'
  });
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedStrategies, setSelectedStrategies] = useState<Set<string>>(new Set());
  const [batchMode, setBatchMode] = useState(false);
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(true);
  const [refreshIntervalState, setRefreshIntervalState] = useState(refreshInterval);

  // Real-time manager instance
  const realtimeManagerRef = useRef(getRealtimeManager({
    updateInterval: refreshIntervalState,
    enableWebSocket: enableRealtime,
    enablePeriodicRefresh: true
  }));

  // Initialize real-time manager
  useEffect(() => {
    const realtimeManager = realtimeManagerRef.current;

    // Set up callbacks for real-time updates
    const callbacks = {
      onStrategyUpdate: (updatedStrategies: Strategy[]) => {
        setStrategies(prevStrategies => {
          const newStrategies = [...prevStrategies];

          updatedStrategies.forEach(updatedStrategy => {
            const index = newStrategies.findIndex(s => s.id === updatedStrategy.id);
            if (index >= 0) {
              newStrategies[index] = { ...newStrategies[index], ...updatedStrategy };
            } else {
              newStrategies.push(updatedStrategy);
            }
          });

          return newStrategies;
        });
      },

      onPerformanceUpdate: (performanceUpdates: PerformanceMetrics[]) => {
        setStrategies(prevStrategies =>
          prevStrategies.map(strategy => {
            const perfUpdate = performanceUpdates.find(p => p.strategyId === strategy.id);
            if (perfUpdate) {
              return {
                ...strategy,
                performance: {
                  ...strategy.performance,
                  ...perfUpdate,
                  lastUpdated: perfUpdate.lastUpdated
                }
              };
            }
            return strategy;
          })
        );
      },

      onError: (error: Error, context: string) => {
        console.error(`Realtime error in ${context}:`, error);

        // Set error state for critical errors
        if (context === 'initialization' || context === 'data_sync') {
          setError(error.message);
        }
      },

      onNetworkChange: (status) => {
        console.log('Network status changed:', status);

        // Update UI based on network status
        if (!status.isOnline) {
          setError('網路連線中斷，請檢查您的網路連線');
        } else if (error?.includes('網路連線中斷')) {
          setError(null);
        }
      },

      onSyncStart: () => {
        console.log('Data sync started');
      },

      onSyncComplete: (duration: number) => {
        console.log(`Data sync completed in ${duration}ms`);

        // Log performance metrics
        if (duration > 500) {
          console.warn(`Slow sync detected: ${duration}ms`);
        }
      }
    };

    // Initialize real-time manager
    realtimeManager.initialize(callbacks)
      .then(() => {
        console.log('Real-time manager initialized successfully');
        setIsLoading(false);
        setError(null);
      })
      .catch(err => {
        console.error('Failed to initialize real-time manager:', err);
        setError(err.message);
        setIsLoading(false);
      });

    // Start real-time updates
    if (autoRefreshEnabled) {
      realtimeManager.start();
    }

    // Cleanup
    return () => {
      realtimeManager.destroy();
    };
  }, [enableRealtime, autoRefreshEnabled]);

  // Handle auto-refresh toggle
  const handleAutoRefreshToggle = useCallback((enabled: boolean) => {
    setAutoRefreshEnabled(enabled);
    const realtimeManager = realtimeManagerRef.current;

    if (enabled) {
      realtimeManager.start();
    } else {
      realtimeManager.pause();
    }
  }, []);

  // Handle refresh interval change
  const handleIntervalChange = useCallback((newInterval: number) => {
    setRefreshIntervalState(newInterval);
    // Note: Would need to recreate real-time manager with new interval
    // For now, we'll just update the state
  }, []);

  // Manual refresh handler
  const handleManualRefresh = useCallback(async () => {
    try {
      const realtimeManager = realtimeManagerRef.current;
      await realtimeManager.triggerManualRefresh();
    } catch (error) {
      console.error('Manual refresh failed:', error);
      setError('重新整理失敗，請稍後再試');
    }
  }, []);

  // Filter strategies based on selected filters
  useEffect(() => {
    let filtered = [...strategies];

    // Category filter
    if (filters.category !== 'all') {
      filtered = filtered.filter(strategy => strategy.category === filters.category);
    }

    // Status filter
    if (filters.status !== 'all') {
      filtered = filtered.filter(strategy => strategy.status === filters.status);
    }

    // Performance filter
    if (filters.performance !== 'all') {
      filtered = filtered.filter(strategy => {
        const sharpe = strategy.performance?.sharpeRatio || 0;
        switch (filters.performance) {
          case 'excellent':
            return sharpe >= 1.5;
          case 'good':
            return sharpe >= 0.8 && sharpe < 1.5;
          case 'average':
            return sharpe >= 0.3 && sharpe < 0.8;
          case 'poor':
            return sharpe < 0.3;
          default:
            return true;
        }
      });
    }

    setFilteredStrategies(filtered);
  }, [strategies, filters]);

  // Load initial data (fallback if real-time manager fails)
  useEffect(() => {
    if (!enableRealtime) {
      const loadInitialData = async () => {
        try {
          setIsLoading(true);
          setError(null);

          const response = await fetch(`${apiUrl}/strategies`);
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          const data = await response.json();
          const strategiesData: Strategy[] = data.strategies.map((strategy: any) => ({
            id: strategy.type,
            name: strategy.name || getStrategyDisplayName(strategy.type),
            type: strategy.type,
            category: getStrategyCategory(strategy.type),
            status: strategy.active ? 'active' : 'inactive',
            performance: strategy.performance ? {
              totalReturn: strategy.performance.total_return,
              sharpeRatio: strategy.performance.sharpe_ratio,
              maxDrawdown: strategy.performance.max_drawdown,
              volatility: strategy.performance.volatility,
              winRate: strategy.performance.win_rate,
              profitFactor: strategy.performance.profit_factor,
              calmarRatio: strategy.performance.calmar_ratio,
              var95: strategy.performance.var_95,
              cvar95: strategy.performance.cvar_95,
              lastUpdated: new Date(strategy.performance.last_updated),
              dataQualityScore: strategy.performance.data_quality_score || 100
            } : undefined,
            parameters: strategy.parameters || {},
            latestSignal: null,
            description: getStrategyDescription(strategy.type)
          }));

          setStrategies(strategiesData);
        } catch (err) {
          console.error('Failed to load strategy data:', err);
          setError(err instanceof Error ? err.message : 'Failed to load strategy data');
        } finally {
          setIsLoading(false);
        }
      };

      loadInitialData();
    }
  }, [apiUrl, enableRealtime]);

  // Strategy display name mapping
  const getStrategyDisplayName = (type: string): string => {
    const names: Record<string, string> = {
      'direct_rsi': '直接RSI情绪策略',
      'sentiment_momentum': '情绪动量策略',
      'composite_index': '复合指标策略',
      'volatility_adjusted': '波动率调整策略'
    };
    return names[type] || type;
  };

  // Strategy category mapping
  const getStrategyCategory = (type: string): string => {
    const categories: Record<string, string> = {
      'direct_rsi': 'core_cbsc',
      'sentiment_momentum': 'core_cbsc',
      'composite_index': 'multi_factor',
      'volatility_adjusted': 'multi_factor'
    };
    return categories[type] || 'other';
  };

  // Strategy description
  const getStrategyDescription = (type: string): string => {
    const descriptions: Record<string, string> = {
      'direct_rsi': '基于牛熊比例的RSI计算，识别极端情绪信号',
      'sentiment_momentum': 'MACD风格的情绪变化率分析，捕捉情绪转折点',
      'composite_index': '多维度情绪综合，布林带风格的情绪区间分析',
      'volatility_adjusted': '成交量加权的情绪分析，考虑市场信心度'
    };
    return descriptions[type] || '量化交易策略';
  };

  // Handle filter changes
  const handleFilterChange = (newFilters: Partial<StrategyFilter>) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
  };

  // Handle strategy selection
  const handleStrategySelect = (strategy: Strategy) => {
    setSelectedStrategy(strategy);
  };

  // Handle strategy status change
  const handleStrategyStatusChange = useCallback((strategyId: string, newStatus: boolean) => {
    setStrategies(prev =>
      prev.map(strategy =>
        strategy.id === strategyId
          ? {
              ...strategy,
              status: newStatus ? 'active' : 'inactive'
            }
          : strategy
      )
    );
  }, []);

  // Handle batch control
  const handleBatchControl = useCallback(async (strategyIds: string[], action: string, reason?: string) => {
    try {
      let result;

      switch (action) {
        case 'enable':
          result = await strategyControlService.batchEnableStrategies(strategyIds, reason);
          break;
        case 'disable':
          result = await strategyControlService.batchDisableStrategies(strategyIds, reason);
          break;
        case 'start':
          result = await strategyControlService.batchEnableStrategies(strategyIds, reason);
          break;
        case 'stop':
          result = await strategyControlService.batchStopStrategies(strategyIds, reason);
          break;
        case 'pause':
          result = await strategyControlService.batchPauseStrategies(strategyIds, reason);
          break;
        default:
          throw new Error(`未知的批量操作类型: ${action}`);
      }

      setStrategies(prev =>
        prev.map(strategy => {
          if (strategyIds.includes(strategy.id)) {
            const successResult = result.results.find(r => r.strategy_id === strategy.id && r.success);
            if (successResult) {
              return {
                ...strategy,
                status: successResult.new_status ? 'active' : 'inactive'
              };
            }
          }
          return strategy;
        })
      );

      return result;
    } catch (error) {
      console.error('批量控制失败:', error);
      throw error;
    }
  }, []);

  // Render loading state
  if (isLoading) {
    return (
      <LoadingProvider>
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">正在加载策略数据...</p>
          </div>
        </div>
      </LoadingProvider>
    );
  }

  // Render error state
  if (error) {
    return (
      <LoadingProvider>
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center max-w-md">
            <div className="text-red-600 mb-4">
              <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.314 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">加载失败</h3>
            <p className="text-gray-600 mb-4">{error}</p>
            <div className="space-x-4">
              <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                重新加载
              </button>
              <button
                onClick={handleManualRefresh}
                className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
              >
                重试连接
              </button>
            </div>
          </div>
        </div>
      </LoadingProvider>
    );
  }

  return (
    <LoadingProvider>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow-sm border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">CBSC策略管理Dashboard</h1>
                <p className="text-sm text-gray-500">实时监控和管理量化交易策略</p>
              </div>

              <div className="flex items-center space-x-4">
                {/* Real-time Monitor */}
                <RealTimeMonitor showDetails={false} />

                {/* Auto-refresh Toggle */}
                {enableRealtime && (
                  <AutoRefreshToggle
                    interval={refreshIntervalState / 1000}
                    onIntervalChange={(seconds) => handleIntervalChange(seconds * 1000)}
                  />
                )}

                {/* Manual Refresh Button */}
                <RefreshControl
                  onRefresh={handleManualRefresh}
                  size="md"
                  showText={true}
                />

                {/* Batch Mode Toggle */}
                <button
                  onClick={() => {
                    setBatchMode(!batchMode);
                    setSelectedStrategies(new Set());
                  }}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    batchMode
                      ? 'bg-blue-600 text-white hover:bg-blue-700'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  {batchMode ? '退出批量操作' : '批量操作'}
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Performance Summary */}
          <PerformanceSummary strategies={filteredStrategies} />

          {/* Charts Dashboard */}
          <div className="mb-8">
            <ChartsDashboard
              strategies={filteredStrategies}
              height={350}
              showControls={true}
              defaultLayout="grid"
            />
          </div>

          {/* Batch Controls */}
          {batchMode && (
            <div className="mb-6">
              <BatchStrategyControls
                strategies={filteredStrategies}
                selectedStrategies={selectedStrategies}
                onSelectionChange={setSelectedStrategies}
                onBatchControl={handleBatchControl}
                isLoading={isLoading}
              />
            </div>
          )}

          {/* Filters */}
          <div className="mb-8">
            <StrategyFilters
              filters={filters}
              onFilterChange={handleFilterChange}
              strategyCount={filteredStrategies.length}
            />
          </div>

          {/* Strategy Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredStrategies.map((strategy) => (
              <div
                key={strategy.id}
                className={`relative ${batchMode ? 'cursor-pointer' : ''}`}
                onClick={() => {
                  if (batchMode) {
                    handleStrategySelect(strategy);
                  }
                }}
              >
                {/* Selection Checkbox in Batch Mode */}
                {batchMode && (
                  <div className="absolute top-2 left-2 z-10">
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
                      className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500 cursor-pointer"
                      onClick={(e) => e.stopPropagation()}
                    />
                  </div>
                )}

                <StrategyCard
                  strategy={strategy}
                  onSelect={handleStrategySelect}
                  isSelected={selectedStrategy?.id === strategy.id}
                  onStatusChange={handleStrategyStatusChange}
                  showControls={!batchMode}
                />
              </div>
            ))}
          </div>

          {/* Empty State */}
          {filteredStrategies.length === 0 && !isLoading && (
            <div className="text-center py-12">
              <div className="text-gray-400 mb-4">
                <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">没有找到匹配的策略</h3>
              <p className="text-gray-600">尝试调整筛选条件或检查网络连接</p>
            </div>
          )}
        </main>

        {/* Strategy Detail Modal */}
        {selectedStrategy && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto m-4">
              <div className="p-6 border-b border-gray-200">
                <div className="flex justify-between items-center">
                  <h2 className="text-xl font-semibold text-gray-900">{selectedStrategy.name}</h2>
                  <button
                    onClick={() => setSelectedStrategy(null)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>
              <div className="p-6">
                <p>策略详情内容...</p>
              </div>
            </div>
          </div>
        )}

        {/* Loading Overlay */}
        <LoadingOverlay />

        {/* Refetch Indicator */}
        <RefetchLoadingIndicator />
      </div>
    </LoadingProvider>
  );
};

export default StrategyDashboardWithRealtime;
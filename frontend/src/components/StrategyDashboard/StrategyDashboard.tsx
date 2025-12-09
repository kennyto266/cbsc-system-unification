import React, { useState, useEffect, useCallback } from 'react';
import { StrategyCard } from './StrategyCard';
import { StrategyFilters } from './StrategyFilters';
import { PerformanceSummary } from './PerformanceSummary';
import { RealTimeMonitor } from './RealTimeMonitor';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useStrategyData } from '../../hooks/useStrategyData';
import { Strategy, StrategyFilter, PerformanceMetrics } from '../../types/strategy';

interface StrategyDashboardProps {
  apiUrl?: string;
  wsUrl?: string;
  refreshInterval?: number;
}

export const StrategyDashboard: React.FC<StrategyDashboardProps> = ({
  apiUrl = '/api',
  wsUrl = 'ws://localhost:3003/ws',
  refreshInterval = 30000
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

  // Custom hooks
  const {
    connectionStatus,
    lastMessage,
    sendMessage,
    connect,
    disconnect
  } = useWebSocket(wsUrl);

  const {
    strategies: apiStrategies,
    performance,
    loading: strategiesLoading,
    error: strategiesError,
    refetch
  } = useStrategyData(apiUrl);

  // WebSocket message handling
  useEffect(() => {
    if (lastMessage) {
      try {
        const data = JSON.parse(lastMessage.data);

        switch (data.type) {
          case 'strategy_update':
            handleStrategyUpdate(data.strategy);
            break;
          case 'performance_update':
            handlePerformanceUpdate(data.performance);
            break;
          case 'new_signals':
            handleNewSignals(data.signals);
            break;
          default:
            console.log('Unknown message type:', data.type);
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    }
  }, [lastMessage]);

  // Handle strategy updates from WebSocket
  const handleStrategyUpdate = useCallback((updatedStrategy: Strategy) => {
    setStrategies(prev =>
      prev.map(strategy =>
        strategy.id === updatedStrategy.id
          ? { ...strategy, ...updatedStrategy }
          : strategy
      )
    );
  }, []);

  // Handle performance updates
  const handlePerformanceUpdate = useCallback((performanceData: PerformanceMetrics) => {
    setStrategies(prev =>
      prev.map(strategy =>
        strategy.id === performanceData.strategy_id
          ? {
              ...strategy,
              performance: {
                ...strategy.performance,
                ...performanceData,
                lastUpdated: new Date(performanceData.last_updated)
              }
            }
          : strategy
      )
    );
  }, []);

  // Handle new trading signals
  const handleNewSignals = useCallback((signals: Record<string, any>) => {
    setStrategies(prev =>
      prev.map(strategy => {
        const signal = signals[strategy.type];
        if (signal) {
          return {
            ...strategy,
            latestSignal: {
              type: signal.signal_type,
              strength: signal.strength,
              confidence: signal.confidence,
              timestamp: new Date(signal.timestamp)
            }
          };
        }
        return strategy;
      })
    );
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

  // Load initial data
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        setIsLoading(true);
        setError(null);

        // Fetch strategies from API
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

        // Connect to WebSocket for real-time updates
        connect();

      } catch (err) {
        console.error('Failed to load strategy data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load strategy data');
      } finally {
        setIsLoading(false);
      }
    };

    loadInitialData();

    // Set up periodic refresh
    const interval = setInterval(() => {
      refetch();
    }, refreshInterval);

    return () => {
      clearInterval(interval);
      disconnect();
    };
  }, [apiUrl, connect, disconnect, refetch, refreshInterval]);

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

  // Render loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">正在加载策略数据...</p>
        </div>
      </div>
    );
  }

  // Render error state
  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center max-w-md">
          <div className="text-red-600 mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.314 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">加载失败</h3>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            重新加载
          </button>
        </div>
      </div>
    );
  }

  return (
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
              <RealTimeMonitor
                connectionStatus={connectionStatus}
                lastUpdate={new Date()}
              />
              <button
                onClick={() => refetch()}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                刷新数据
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Performance Summary */}
        <PerformanceSummary strategies={filteredStrategies} />

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
            <StrategyCard
              key={strategy.id}
              strategy={strategy}
              onSelect={handleStrategySelect}
              isSelected={selectedStrategy?.id === strategy.id}
            />
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
              {/* Strategy detail content will be implemented in StrategyDetail component */}
              <p>策略详情内容...</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
/**
 * Strategy Detail Component
 * 策略詳情查看組件
 */

import React, { useState, useEffect } from 'react';
import {
  ArrowPathIcon,
  CogIcon,
  ChartBarIcon,
  DocumentTextIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon
} from '@heroicons/react/24/outline';

import { Button } from './ui/Button';
import { Card } from './ui/Card';
import { Badge } from './ui/Badge';
import { Alert } from './ui/Alert';
import { Loading } from './ui/Loading';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';

import {
  Strategy,
  StrategyConfig,
  PerformanceMetricsResponse,
  StrategyType,
  RiskTolerance
} from '../types/strategyTypes';

import { useDispatch, useSelector } from 'react-redux';
import {
  fetchStrategy,
  fetchStrategyConfigs,
  fetchStrategyPerformance,
  selectCurrentStrategy,
  selectStrategiesLoading,
  selectStrategiesError,
  selectConfigs,
  selectPerformance,
  selectPerformanceLoading
} from '../store/strategies/strategySlice';

interface StrategyDetailProps {
  strategyId: string;
  onEdit?: (strategy: Strategy) => void;
  onExecute?: (strategy: Strategy) => void;
  onClose?: () => void;
}

// Strategy type descriptions
const strategyTypeDescriptions = {
  [StrategyType.TECHNICAL_INDICATORS]: '基於技術指標的量化策略，如MA、RSI、MACD等',
  [StrategyType.MOMENTUM]: '基於動量因子的策略，捕捉價格趨勢',
  [StrategyType.MEAN_REVERSION]: '均值回歸策略，基於價格回歸均值的特性',
  [StrategyType.VOLUME]: '基於成交量分析的策略',
  [StrategyType.VOLATILITY]: '基於波動率的策略，如VIX指標',
  [StrategyType.FUNDAMENTAL]: '基於基本面分析的策略',
  [StrategyType.PORTFOLIO]: '投資組合管理策略',
  [StrategyType.ARBITRAGE]: '套利策略，捕捉市場定價偏差',
  [StrategyType.MACRO]: '基於宏觀經濟因素的策略'
};

// Risk tolerance descriptions
const riskToleranceDescriptions = {
  [RiskTolerance.LOW]: '低風險承受度，追求穩定收益，最大回撤控制在5%以內',
  [RiskTolerance.MEDIUM]: '中等風險承受度，平衡收益與風險，最大回撤控制在10%以內',
  [RiskTolerance.HIGH]: '高風險承受度，追求高收益，最大回撤控制在20%以內',
  [RiskTolerance.EXTREME]: '極高風險承受度，追求極高收益，能承受較大回撤'
};

export const StrategyDetail: React.FC<StrategyDetailProps> = ({
  strategyId,
  onEdit,
  onExecute,
  onClose
}) => {
  const dispatch = useDispatch();
  const strategy = useSelector(selectCurrentStrategy);
  const loading = useSelector(selectStrategiesLoading);
  const error = useSelector(selectStrategiesError);
  const configs = useSelector(selectConfigs);
  const performance = useSelector(selectPerformance);
  const performanceLoading = useSelector(selectPerformanceLoading);

  const [activeTab, setActiveTab] = useState('overview');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Load strategy data
  useEffect(() => {
    if (strategyId) {
      loadStrategyData();
    }
  }, [strategyId]);

  const loadStrategyData = async () => {
    try {
      // Load basic strategy info
      await dispatch(fetchStrategy(strategyId)).unwrap();

      // Load configurations
      await dispatch(fetchStrategyConfigs({ strategy_id: strategyId })).unwrap();

      // Load performance data
      await dispatch(fetchStrategyPerformance({
        strategyId,
        timeRange: '1M'
      })).unwrap();
    } catch (error) {
      console.error('Failed to load strategy data:', error);
    }
  };

  const handleRefresh = () => {
    loadStrategyData();
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-TW', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatNumber = (num: number, decimals: number = 2) => {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }).format(num);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount);
  };

  if (loading && !strategy) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loading size="lg" text="載入策略詳情中..." />
      </div>
    );
  }

  if (error) {
    return (
      <Alert
        variant="error"
        title="載入失敗"
        description={error}
        action={
          <Button variant="outline" size="sm" onClick={handleRefresh}>
            <ArrowPathIcon className="h-4 w-4 mr-1" />
            重試
          </Button>
        }
      />
    );
  }

  if (!strategy) {
    return (
      <Alert
        variant="warning"
        title="策略不存在"
        description="找不到指定的策略"
      />
    );
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header - Desktop */}
      <div className="hidden sm:flex items-center justify-between">
        <div className="min-w-0 flex-1">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white truncate">
            {strategy.name}
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">
            {strategy.description}
          </p>
        </div>
        <div className="flex items-center space-x-3 ml-4">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={loading}
            aria-label="刷新"
          >
            <ArrowPathIcon className={`h-4 w-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
            <span className="hidden lg:inline">刷新</span>
          </Button>
          {onEdit && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onEdit(strategy)}
              aria-label="編輯"
            >
              <CogIcon className="h-4 w-4 mr-1" />
              <span className="hidden lg:inline">編輯</span>
            </Button>
          )}
          {onExecute && (
            <Button
              variant="primary"
              size="sm"
              onClick={() => onExecute(strategy)}
              disabled={!strategy.is_active}
              aria-label="執行"
            >
              <ChartBarIcon className="h-4 w-4 mr-1" />
              <span className="hidden lg:inline">執行</span>
            </Button>
          )}
          {onClose && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              aria-label="關閉"
            >
              <XCircleIcon className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>

      {/* Header - Mobile */}
      <div className="sm:hidden space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white truncate">
            {strategy.name}
          </h2>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="選項"
          >
            {mobileMenuOpen ? (
              <XCircleIcon className="h-5 w-5" />
            ) : (
              <CogIcon className="h-5 w-5" />
            )}
          </Button>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          {strategy.description}
        </p>

        {/* Mobile Action Menu */}
        {mobileMenuOpen && (
          <div className="flex flex-col gap-2 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={loading}
              className="w-full justify-start"
            >
              <ArrowPathIcon className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              刷新
            </Button>
            {onEdit && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onEdit(strategy)}
                className="w-full justify-start"
              >
                <CogIcon className="h-4 w-4 mr-2" />
                編輯
              </Button>
            )}
            {onExecute && (
              <Button
                variant="primary"
                size="sm"
                onClick={() => onExecute(strategy)}
                disabled={!strategy.is_active}
                className="w-full justify-start"
              >
                <ChartBarIcon className="h-4 w-4 mr-2" />
                執行
              </Button>
            )}
            {onClose && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                className="w-full justify-start"
              >
                <XCircleIcon className="h-4 w-4 mr-2" />
                關閉
              </Button>
            )}
          </div>
        )}
      </div>

      {/* Status and Badges */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center space-x-2">
          {strategy.is_active ? (
            <CheckCircleIcon className="h-5 w-5 text-green-500 dark:text-green-400" />
          ) : (
            <XCircleIcon className="h-5 w-5 text-red-500 dark:text-red-400" />
          )}
          <span className={`font-medium ${
            strategy.is_active ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
          }`}>
            {strategy.is_active ? '活躍' : '非活躍'}
          </span>
        </div>

        <Badge className="bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400">
          {strategy.strategy_type}
        </Badge>

        <Badge className={
          strategy.risk_tolerance === 'low' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
          strategy.risk_tolerance === 'medium' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400' :
          strategy.risk_tolerance === 'high' ? 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400' :
          'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
        }>
          {strategy.risk_tolerance}
        </Badge>

        <Badge className="bg-gray-100 text-gray-800 dark:bg-gray-800/50 dark:text-gray-300">
          {strategy.version}
        </Badge>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4 bg-gray-100 dark:bg-gray-800">
          <TabsTrigger
            value="overview"
            className="data-[state=active]:bg-white dark:data-[state=active]:bg-gray-900 data-[state=active]:shadow-sm"
          >
            概覽
          </TabsTrigger>
          <TabsTrigger
            value="configurations"
            className="data-[state=active]:bg-white dark:data-[state=active]:bg-gray-900 data-[state=active]:shadow-sm"
          >
            配置
          </TabsTrigger>
          <TabsTrigger
            value="performance"
            className="data-[state=active]:bg-white dark:data-[state=active]:bg-gray-900 data-[state=active]:shadow-sm"
          >
            性能
          </TabsTrigger>
          <TabsTrigger
            value="logs"
            className="data-[state=active]:bg-white dark:data-[state=active]:bg-gray-900 data-[state=active]:shadow-sm"
          >
            日誌
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4 sm:space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
            {/* Basic Information */}
            <Card className="p-4 sm:p-6 bg-white dark:bg-gray-800">
              <h3 className="text-lg font-medium mb-4 text-gray-900 dark:text-white">基本資訊</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">策略ID:</span>
                  <span className="text-sm font-mono text-gray-900 dark:text-white">{strategy.id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">策略類型:</span>
                  <span className="text-sm text-gray-900 dark:text-white">{strategy.strategy_type}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">風險承受度:</span>
                  <span className="text-sm text-gray-900 dark:text-white">{strategy.risk_tolerance}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">創建時間:</span>
                  <span className="text-sm text-gray-900 dark:text-white">{formatDate(strategy.created_at)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">最後更新:</span>
                  <span className="text-sm text-gray-900 dark:text-white">{formatDate(strategy.updated_at)}</span>
                </div>
              </div>
            </Card>

            {/* Strategy Description */}
            <Card className="p-4 sm:p-6 bg-white dark:bg-gray-800">
              <h3 className="text-lg font-medium mb-4 text-gray-900 dark:text-white">策略描述</h3>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                {strategy.description}
              </p>

              {strategy.tags && strategy.tags.length > 0 && (
                <div className="mt-4">
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">標籤:</h4>
                  <div className="flex flex-wrap gap-2">
                    {strategy.tags.map((tag) => (
                      <Badge
                        key={tag}
                        className="bg-gray-100 text-gray-800 dark:bg-gray-700/50 dark:text-gray-300"
                      >
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </Card>
          </div>

          {/* Strategy Details */}
          <Card className="p-4 sm:p-6 bg-white dark:bg-gray-800">
            <h3 className="text-lg font-medium mb-4 text-gray-900 dark:text-white">策略詳情</h3>
            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">策略類型說明:</h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {strategyTypeDescriptions[strategy.strategy_type]}
                </p>
              </div>

              <div>
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">風險承受度說明:</h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {riskToleranceDescriptions[strategy.risk_tolerance]}
                </p>
              </div>

              {strategy.parameters && Object.keys(strategy.parameters).length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">策略參數:</h4>
                  <pre className="bg-gray-50 dark:bg-gray-900 p-3 rounded-md text-xs overflow-x-auto text-gray-900 dark:text-gray-300">
                    {JSON.stringify(strategy.parameters, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </Card>
        </TabsContent>

        {/* Configurations Tab */}
        <TabsContent value="configurations" className="space-y-6">
          {performanceLoading ? (
            <Loading text="載入配置中..." />
          ) : configs.length > 0 ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {configs.map((config) => (
                <Card key={config.id} className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-medium">{config.name}</h3>
                    <Badge className={
                      config.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }>
                      {config.is_active ? '活躍' : '非活躍'}
                    </Badge>
                  </div>

                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">配置ID:</span>
                      <span className="text-sm font-mono">{config.id}</span>
                    </div>

                    {config.description && (
                      <div>
                        <span className="text-sm text-gray-600">描述:</span>
                        <p className="text-sm text-gray-700 mt-1">{config.description}</p>
                      </div>
                    )}

                    {config.parameters && Object.keys(config.parameters).length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-1">參數配置:</h4>
                        <pre className="bg-gray-50 p-3 rounded-md text-xs overflow-x-auto">
                          {JSON.stringify(config.parameters, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                </Card>
              ))}
            </div>
          ) : (
            <Card className="p-8 text-center">
              <CogIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">無配置</h3>
              <p className="text-gray-500">
                此策略尚未配置任何參數配置
              </p>
            </Card>
          )}
        </TabsContent>

        {/* Performance Tab */}
        <TabsContent value="performance" className="space-y-6">
          {performanceLoading ? (
            <Loading text="載入性能數據中..." />
          ) : performance ? (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <Card className="p-6">
                <h3 className="text-lg font-medium mb-4">收益指標</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">總收益:</span>
                    <span className={`text-sm font-medium ${
                      performance.total_return >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {formatNumber(performance.total_return * 100, 2)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">年化收益:</span>
                    <span className={`text-sm font-medium ${
                      performance.annualized_return >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {formatNumber(performance.annualized_return * 100, 2)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">最大回撤:</span>
                    <span className="text-sm font-medium text-red-600">
                      {formatNumber(performance.max_drawdown * 100, 2)}%
                    </span>
                  </div>
                </div>
              </Card>

              <Card className="p-6">
                <h3 className="text-lg font-medium mb-4">風險指標</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">夏普比率:</span>
                    <span className="text-sm font-medium">
                      {formatNumber(performance.sharpe_ratio, 2)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">波動率:</span>
                    <span className="text-sm font-medium">
                      {formatNumber(performance.volatility * 100, 2)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">勝率:</span>
                    <span className="text-sm font-medium">
                      {formatNumber(performance.win_rate * 100, 1)}%
                    </span>
                  </div>
                </div>
              </Card>

              <Card className="p-6">
                <h3 className="text-lg font-medium mb-4">交易統計</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">總交易次數:</span>
                    <span className="text-sm font-medium">
                      {performance.total_trades || 0}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">盈利交易:</span>
                    <span className="text-sm font-medium text-green-600">
                      {performance.winning_trades || 0}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">虧損交易:</span>
                    <span className="text-sm font-medium text-red-600">
                      {performance.losing_trades || 0}
                    </span>
                  </div>
                </div>
              </Card>
            </div>
          ) : (
            <Card className="p-8 text-center">
              <ChartBarIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">無性能數據</h3>
              <p className="text-gray-500">
                此策略尚未執行或無性能數據
              </p>
            </Card>
          )}
        </TabsContent>

        {/* Logs Tab */}
        <TabsContent value="logs" className="space-y-6">
          <Card className="p-8 text-center">
            <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">日誌功能開發中</h3>
            <p className="text-gray-500">
              策略執行日誌功能正在開發中，敬請期待
            </p>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default StrategyDetail;
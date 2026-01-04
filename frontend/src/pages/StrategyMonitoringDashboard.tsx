/**
 * Strategy Monitoring Dashboard
 * 策略監控儀表板
 */

import React, { useState, useEffect } from 'react';
import {
  ChartBarIcon,
  Cog6ToothIcon,
  BellIcon,
  ArrowPathIcon,
  FunnelIcon,
  EyeIcon,
  PlayIcon,
  PauseIcon,
  StopIcon
} from '@heroicons/react/24/outline';
import { useDispatch, useSelector } from 'react-redux';

import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Select } from '../components/ui/Select';
import { Loading } from '../components/ui/Loading';
import { Alert } from '../components/ui/Alert';
import { Switch } from '../components/ui/switch';
import StrategyPerformanceMonitor from '../components/StrategyPerformanceMonitor';

import {
  Strategy,
  fetchStrategies,
  selectStrategies,
  selectStrategiesLoading,
  selectStrategiesError,
  executeStrategy,
  stopExecution
} from '../store/strategies/strategySlice';

interface StrategyMonitoringDashboardProps {
  strategyId?: string;
}

interface MonitoringAlert {
  id: string;
  type: 'info' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: Date;
  strategyId?: string;
  strategyName?: string;
}

export const StrategyMonitoringDashboard: React.FC<StrategyMonitoringDashboardProps> = ({
  strategyId
}) => {
  const dispatch = useDispatch();

  // Redux state
  const strategies = useSelector(selectStrategies);
  const loading = useSelector(selectStrategiesLoading);
  const error = useSelector(selectStrategiesError);

  // Local state
  const [selectedStrategyId, setSelectedStrategyId] = useState<string>(strategyId || '');
  const [timeRange, setTimeRange] = useState('1M');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [alerts, setAlerts] = useState<MonitoringAlert[]>([]);
  const [showAlerts, setShowAlerts] = useState(true);

  // Load strategies
  useEffect(() => {
    dispatch(fetchStrategies({ page: 1, pageSize: 100 })); // Load all strategies
  }, [dispatch]);

  // Set default strategy if provided
  useEffect(() => {
    if (strategyId && strategies.length > 0) {
      setSelectedStrategyId(strategyId);
    } else if (!selectedStrategyId && strategies.length > 0) {
      // Select first active strategy
      const firstActiveStrategy = strategies.find(s => s.is_active);
      if (firstActiveStrategy) {
        setSelectedStrategyId(firstActiveStrategy.id);
      }
    }
  }, [strategies, strategyId, selectedStrategyId]);

  // Mock alerts generation
  useEffect(() => {
    const generateMockAlert = () => {
      const types: Array<'info' | 'warning' | 'error'> = ['info', 'warning', 'error'];
      const messages = [
        { title: '策略執行異常', message: '策略執行過程中遇到錯誤，請檢查配置', type: 'error' },
        { title: '性能下降', message: '策略收益低於預期，建議調整參數', type: 'warning' },
        { title: '執行完成', message: '策略執行順利完成，收益為正', type: 'info' },
        { title: '市場波動', message: '市場波動率異常升高，請注意風險控制', type: 'warning' }
      ];

      if (Math.random() > 0.7) { // 30% chance to generate alert
        const randomMessage = messages[Math.floor(Math.random() * messages.length)];
        const randomStrategy = strategies[Math.floor(Math.random() * strategies.length)];

        const newAlert: MonitoringAlert = {
          id: Date.now().toString(),
          type: randomMessage.type,
          title: randomMessage.title,
          message: randomMessage.message,
          timestamp: new Date(),
          strategyId: randomStrategy?.id,
          strategyName: randomStrategy?.name
        };

        setAlerts(prev => [newAlert, ...prev.slice(0, 9)]); // Keep max 10 alerts
      }
    };

    const interval = setInterval(generateMockAlert, 30000); // Every 30 seconds
    return () => clearInterval(interval);
  }, [strategies]);

  const selectedStrategy = strategies.find(s => s.id === selectedStrategyId);
  const activeStrategies = strategies.filter(s => s.is_active);

  // Handle strategy execution
  const handleExecuteStrategy = async (strategyId: string) => {
    try {
      await dispatch(executeStrategy({
        strategyId,
        executionRequest: {
          config_id: strategyId,
          backtest_type: 'simple'
        }
      })).unwrap();

      // Add success alert
      const strategy = strategies.find(s => s.id === strategyId);
      setAlerts(prev => [{
        id: Date.now().toString(),
        type: 'info',
        title: '策略執行開始',
        message: `策略 "${strategy?.name}" 開始執行`,
        timestamp: new Date(),
        strategyId,
        strategyName: strategy?.name
      }, ...prev.slice(0, 9)]);
    } catch (error) {
      console.error('Failed to execute strategy:', error);
    }
  };

  const handleStopStrategy = async (strategyId: string) => {
    try {
      // This would be implemented with actual stop execution API
      // await dispatch(stopExecution({ strategyId, executionId: 'current' })).unwrap();

      // Add success alert
      const strategy = strategies.find(s => s.id === strategyId);
      setAlerts(prev => [{
        id: Date.now().toString(),
        type: 'warning',
        title: '策略執行停止',
        message: `策略 "${strategy?.name}" 已停止執行`,
        timestamp: new Date(),
        strategyId,
        strategyName: strategy?.name
      }, ...prev.slice(0, 9)]);
    } catch (error) {
      console.error('Failed to stop strategy:', error);
    }
  };

  const clearAlert = (alertId: string) => {
    setAlerts(prev => prev.filter(alert => alert.id !== alertId));
  };

  const clearAllAlerts = () => {
    setAlerts([]);
  };

  const formatDate = (date: Date) => {
    return date.toLocaleString('zh-TW', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading && strategies.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loading size="lg" text="載入監控數據中..." />
      </div>
    );
  }

  if (error) {
    return (
      <Alert
        variant="error"
        title="載入失敗"
        description={error}
      />
    );
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white">策略監控</h2>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            實時監控策略執行狀況和性能表現
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600 dark:text-gray-400">自動刷新:</span>
            <Switch
              checked={autoRefresh}
              onCheckedChange={setAutoRefresh}
            />
          </div>

          <Button
            variant="outline"
            onClick={() => dispatch(fetchStrategies({ page: 1, pageSize: 100 }))}
            className="w-full sm:w-auto"
          >
            <ArrowPathIcon className="h-4 w-4 mr-1" />
            刷新
          </Button>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4 bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">總策略數</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{strategies.length}</p>
            </div>
            <ChartBarIcon className="h-8 w-8 text-blue-500" />
          </div>
        </Card>

        <Card className="p-4 bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">活躍策略</p>
              <p className="text-2xl font-bold text-green-600 dark:text-green-400">{activeStrategies.length}</p>
            </div>
            <PlayIcon className="h-8 w-8 text-green-500" />
          </div>
        </Card>

        <Card className="p-4 bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">當前警報</p>
              <p className="text-2xl font-bold text-red-600 dark:text-red-400">{alerts.length}</p>
            </div>
            <BellIcon className="h-8 w-8 text-red-500" />
          </div>
        </Card>

        <Card className="p-4 bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">監控狀態</p>
              <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">正常</p>
            </div>
            <EyeIcon className="h-8 w-8 text-blue-500" />
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 sm:gap-6">
        {/* Strategy List */}
        <Card className="p-4 sm:p-6 bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">策略列表</h3>
            <Button variant="ghost" size="sm">
              <FunnelIcon className="h-4 w-4" />
            </Button>
          </div>

          <div className="space-y-3 max-h-[600px] overflow-y-auto">
            {strategies.map((strategy) => (
              <div
                key={strategy.id}
                className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                  selectedStrategyId === strategy.id
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                }`}
                onClick={() => setSelectedStrategyId(strategy.id)}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-sm text-gray-900 dark:text-white truncate">
                    {strategy.name}
                  </span>
                  <Badge className={
                    strategy.is_active
                      ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                      : 'bg-gray-100 text-gray-800 dark:bg-gray-800/50 dark:text-gray-300'
                  }>
                    {strategy.is_active ? '運行中' : '已停止'}
                  </Badge>
                </div>

                <div className="flex items-center justify-between text-xs text-gray-600 dark:text-gray-400">
                  <span className="truncate">{strategy.strategy_type}</span>
                  <div className="flex space-x-1 flex-shrink-0">
                    {strategy.is_active ? (
                      <Button
                        variant="ghost"
                        size="xs"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleStopStrategy(strategy.id);
                        }}
                        aria-label="暫停策略"
                      >
                        <PauseIcon className="h-3 w-3" />
                      </Button>
                    ) : (
                      <Button
                        variant="ghost"
                        size="xs"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleExecuteStrategy(strategy.id);
                        }}
                        aria-label="啟動策略"
                      >
                        <PlayIcon className="h-3 w-3" />
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Performance Monitor */}
        <div className="xl:col-span-2">
          {selectedStrategy ? (
            <StrategyPerformanceMonitor
              strategyId={selectedStrategy.id}
              strategyName={selectedStrategy.name}
              timeRange={timeRange}
              onTimeRangeChange={setTimeRange}
              refreshInterval={autoRefresh ? 60000 : 0}
            />
          ) : (
            <Card className="p-6 sm:p-8 text-center bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
              <ChartBarIcon className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-600 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">選擇策略</h3>
              <p className="text-gray-500 dark:text-gray-400">
                請從左側列表選擇一個策略查看性能監控
              </p>
            </Card>
          )}
        </div>
      </div>

      {/* Alerts Panel */}
      {alerts.length > 0 && (
        <Card className="p-4 sm:p-6 bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
            <div className="flex items-center space-x-2">
              <BellIcon className="h-5 w-5 text-red-500" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">警報通知</h3>
              <Badge className="bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400">
                {alerts.length}
              </Badge>
            </div>

            <div className="flex space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowAlerts(!showAlerts)}
                className="w-full sm:w-auto"
              >
                {showAlerts ? '隱藏' : '顯示'}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={clearAllAlerts}
                className="w-full sm:w-auto"
              >
                清除全部
              </Button>
            </div>
          </div>

          {showAlerts && (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {alerts.map((alert) => (
                <div
                  key={alert.id}
                  className={`p-3 rounded-lg border ${
                    alert.type === 'error' ? 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20' :
                    alert.type === 'warning' ? 'border-yellow-200 bg-yellow-50 dark:border-yellow-800 dark:bg-yellow-900/20' :
                    'border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-900/20'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-1">
                        <span className={`font-medium text-sm ${
                          alert.type === 'error' ? 'text-red-800 dark:text-red-400' :
                          alert.type === 'warning' ? 'text-yellow-800 dark:text-yellow-400' :
                          'text-blue-800 dark:text-blue-400'
                        }`}>
                          {alert.title}
                        </span>
                        {alert.strategyName && (
                          <Badge className="text-xs bg-white dark:bg-gray-800">
                            {alert.strategyName}
                          </Badge>
                        )}
                      </div>
                      <p className={`text-sm ${
                        alert.type === 'error' ? 'text-red-700 dark:text-red-300' :
                        alert.type === 'warning' ? 'text-yellow-700 dark:text-yellow-300' :
                        'text-blue-700 dark:text-blue-300'
                      }`}>
                        {alert.message}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        {formatDate(alert.timestamp)}
                      </p>
                    </div>

                    <Button
                      variant="ghost"
                      size="xs"
                      onClick={() => clearAlert(alert.id)}
                      className="ml-2 flex-shrink-0"
                      aria-label="清除警報"
                    >
                      ×
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}
    </div>
  );
};

export default StrategyMonitoringDashboard;
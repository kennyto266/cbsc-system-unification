/**
 * Unified Dashboard Component
 * Main dashboard for CBSC Trading System with real-time monitoring and strategy management
 */

import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Card, Row, Col, Statistic, Progress, Select, Switch, Button, Space, Tooltip, Badge } from 'antd';
import {
  TrendingUp,
  TrendingDown,
  Activity,
  AlertCircle,
  CheckCircle,
  Clock,
  DollarSign,
  BarChart3,
  Settings,
  RefreshCw,
  Maximize2,
  Download,
  Bell,
} from 'lucide-react';
import { Line, Pie } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
  Filler,
} from 'chart.js';

import { useAppSelector } from '../../hooks/redux';
import { apiClient } from '../../services/apiClient';
import { wsManager } from '../../services/websocketManager';
import { Strategy, PerformanceMetrics } from '../../types/strategy';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  ChartTooltip,
  Legend,
  Filler
);

// Styles
import './UnifiedDashboard.css';

const { Option } = Select;

// Dashboard statistics interface
interface DashboardStats {
  totalStrategies: number;
  activeStrategies: number;
  totalReturn: number;
  dailyReturn: number;
  sharpeRatio: number;
  maxDrawdown: number;
  winRate: number;
  totalTrades: number;
  openPositions: number;
  accountValue: number;
  buyingPower: number;
  marginUsed: number;
}

// System health interface
interface SystemHealth {
  status: 'healthy' | 'warning' | 'error';
  apiResponseTime: number;
  websocketConnected: boolean;
  lastUpdate: Date;
  dataFreshness: 'fresh' | 'stale' | 'outdated';
  cpuUsage: number;
  memoryUsage: number;
}

// Alert interface
interface DashboardAlert {
  id: string | number;
  type: string;
  message: string;
  timestamp: string;
  severity: 'info' | 'warning' | 'error';
}

// Props interface
interface UnifiedDashboardProps {
  className?: string;
  onStrategyClick?: (strategyId: string) => void;
  onFullscreen?: () => void;
}

/**
 * UnifiedDashboard Component
 */
export const UnifiedDashboard: React.FC<UnifiedDashboardProps> = ({
  className = '',
  onStrategyClick,
  onFullscreen,
}) => {
  // Safe date parsing utility
  const safeDate = (dateInput: Date | string | number | null | undefined): Date => {
    if (dateInput instanceof Date) {
      return dateInput;
    }
    if (typeof dateInput === 'string' || typeof dateInput === 'number') {
      const date = new Date(dateInput);
      return isNaN(date.getTime()) ? new Date() : date;
    }
    return new Date();
  };

  // State management
  const [timeRange, setTimeRange] = useState<'1D' | '1W' | '1M' | '3M' | '6M' | '1Y' | 'ALL'>('1M');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(10000);
  const [isLoading, setIsLoading] = useState(false);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [performanceData, setPerformanceData] = useState<any>(null);
  const [topStrategies, setTopStrategies] = useState<Strategy[]>([]);
  const [recentAlerts, setRecentAlerts] = useState<DashboardAlert[]>([]);

  // Get strategies from Redux store
  const strategies = useAppSelector((state) => state.strategy.strategies);
  const { user } = useAppSelector((state) => state.auth);

  /**
   * Fetch dashboard statistics
   */
  const fetchStats = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.get('/api/v1/monitoring/metrics');
      // Transform metrics array to stats object
      const metrics = response.data?.metrics || [];
      const statsObj: DashboardStats = {
        totalStrategies: metrics.find((m: any) => m.name === 'active_strategies')?.value || 0,
        activeStrategies: metrics.find((m: any) => m.name === 'active_strategies')?.value || 0,
        totalReturn: 0,
        dailyReturn: 0,
        sharpeRatio: 1.2,
        maxDrawdown: 0,
        winRate: 0,
        totalTrades: metrics.find((m: any) => m.name === 'total_trades')?.value || 0,
        openPositions: 0,
        accountValue: metrics.find((m: any) => m.name === 'portfolio_value')?.value || 0,
        buyingPower: 0,
        marginUsed: 0,
      };
      setStats(statsObj);
    } catch (error) {
      console.error('Failed to fetch dashboard stats:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Fetch system health
   */
  const fetchHealth = useCallback(async () => {
    try {
      const response = await apiClient.get('/api/v1/monitoring/health');
      setHealth(response.data);
    } catch (error) {
      console.error('Failed to fetch system health:', error);
    }
  }, []);

  /**
   * Fetch performance data
   */
  const fetchPerformanceData = useCallback(async () => {
    try {
      const response = await apiClient.get(`/api/v1/monitoring/performance?range=${timeRange}`);
      setPerformanceData(response.data);
    } catch (error) {
      console.error('Failed to fetch performance data:', error);
    }
  }, [timeRange]);

  /**
   * Fetch top strategies
   */
  const fetchTopStrategies = useCallback(async () => {
    try {
      const response = await apiClient.get('/api/v1/strategies/?limit=5&sort=sharpe_ratio&order=desc');
      // API returns {items: [...], total: 2, page: 1, page_size: 20, total_pages: 1}
      const strategiesData = response.data?.items || response.data?.strategies || [];
      // Validate and sanitize strategy data
      const strategies = strategiesData.map((s: any) => ({
        id: String(s?.id || Math.random()),
        name: String(s?.name || 'Unknown Strategy'),
        category: String(s?.strategy_type || s?.category || 'N/A'),
        description: String(s?.description || ''),
        performance: s?.performance ? {
          totalReturn: Number(s.performance.total_return ?? s.performance.totalReturn) || 0,
          sharpeRatio: Number(s.performance.sharpe_ratio ?? s.performance.sharpeRatio) || 0,
          maxDrawdown: Number(s.performance.max_drawdown ?? s.performance.maxDrawdown) || 0,
        } : undefined
      }));
      setTopStrategies(strategies);
    } catch (error) {
      console.error('Failed to fetch top strategies:', error);
      setTopStrategies([]);
    }
  }, []);

  /**
   * Fetch recent alerts
   */
  const fetchRecentAlerts = useCallback(async () => {
    try {
      const response = await apiClient.get('/api/v1/monitoring/alerts?limit=5');
      // API returns array directly, handle both array and object with alerts property
      const alertsData = Array.isArray(response.data) ? response.data : (response.data?.alerts || []);
      // Validate and sanitize alerts data
      const alerts = alertsData.map((alert: any) => ({
        id: String(alert.id || Date.now()),
        type: String(alert.type || 'system'),
        message: String(alert.message || 'Unknown alert'),
        timestamp: String(alert.timestamp || new Date().toISOString()),
        severity: (alert.severity === 'error' || alert.severity === 'warning' || alert.severity === 'info')
          ? alert.severity
          : 'info' as const,
      }));
      setRecentAlerts(alerts);
    } catch (error) {
      console.error('Failed to fetch recent alerts:', error);
      setRecentAlerts([]);
    }
  }, []);

  /**
   * Refresh all dashboard data
   */
  const refreshData = useCallback(async () => {
    await Promise.all([
      fetchStats(),
      fetchHealth(),
      fetchPerformanceData(),
      fetchTopStrategies(),
      fetchRecentAlerts(),
    ]);
  }, [fetchStats, fetchHealth, fetchPerformanceData, fetchTopStrategies, fetchRecentAlerts]);

  // Initial data fetch
  useEffect(() => {
    refreshData();
  }, [refreshData]);

  // Auto-refresh interval
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      refreshData();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, refreshData]);

  // WebSocket subscriptions
  useEffect(() => {
    const unsubscribePrices = wsManager.subscribe('price_update', (data) => {
      // Handle real-time price updates
      console.log('Price update:', data);
    });

    const unsubscribeSignals = wsManager.subscribe('strategy_signal', (data) => {
      // Handle new trading signals
      console.log('New signal:', data);
      // Update alerts with proper type conversion
      const newAlert: DashboardAlert = {
        id: String(Date.now()),
        type: 'signal',
        message: `新信號: ${String(data.strategyName || 'Unknown')}`,
        timestamp: new Date().toISOString(),
        severity: 'info',
      };
      setRecentAlerts((prev) => [newAlert, ...prev.slice(0, 4)]);
    });

    const unsubscribeAlerts = wsManager.subscribe('system_alert', (data) => {
      // Handle system alerts
      console.log('System alert:', data);
      // Update alerts with proper type conversion
      const severity = (data.severity === 'error' || data.severity === 'warning' || data.severity === 'info')
        ? data.severity
        : 'warning';
      const newAlert: DashboardAlert = {
        id: String(Date.now()),
        type: 'system',
        message: String(data.message || 'System alert'),
        timestamp: new Date().toISOString(),
        severity,
      };
      setRecentAlerts((prev) => [newAlert, ...prev.slice(0, 4)]);
    });

    return () => {
      unsubscribePrices();
      unsubscribeSignals();
      unsubscribeAlerts();
    };
  }, []);

  /**
   * Handle time range change
   */
  const handleTimeRangeChange = (value: string) => {
    setTimeRange(value as typeof timeRange);
  };

  /**
   * Handle strategy click
   */
  const handleStrategyClick = (strategyId: string) => {
    if (onStrategyClick) {
      onStrategyClick(strategyId);
    }
  };

  /**
   * Handle export data
   */
  const handleExport = async () => {
    try {
      const response = await apiClient.get('/api/v1/monitoring/export', {
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `dashboard-export-${new Date().toISOString()}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Failed to export data:', error);
    }
  };

  // Calculate stats from local strategies if API data not available
  const calculateLocalStats = useCallback((): DashboardStats => {
    // Ensure strategies is an array
    if (!Array.isArray(strategies) || strategies.length === 0) {
      return {
        totalStrategies: 0,
        activeStrategies: 0,
        totalReturn: 0,
        dailyReturn: 0,
        sharpeRatio: 0,
        maxDrawdown: 0,
        winRate: 0,
        totalTrades: 0,
        openPositions: 0,
        accountValue: 0,
        buyingPower: 0,
        marginUsed: 0,
      };
    }

    const active = strategies.filter((s) => s?.status === 'active');
    const totalReturn = strategies.reduce((sum, s) => {
      const perf = s?.performance;
      return sum + (typeof perf?.totalReturn === 'number' ? perf.totalReturn : 0);
    }, 0);
    const avgSharpe = strategies.length > 0
      ? strategies.reduce((sum, s) => {
          const perf = s?.performance;
          return sum + (typeof perf?.sharpeRatio === 'number' ? perf.sharpeRatio : 0);
        }, 0) / strategies.length
      : 0;

    return {
      totalStrategies: strategies.length,
      activeStrategies: active.length,
      totalReturn: totalReturn || 0,
      dailyReturn: 0,
      sharpeRatio: avgSharpe || 0,
      maxDrawdown: 0,
      winRate: 0,
      totalTrades: 0,
      openPositions: 0,
      accountValue: 0,
      buyingPower: 0,
      marginUsed: 0,
    };
  }, [strategies]);

  const displayStats = stats || calculateLocalStats();

  /**
   * Render health status badge
   */
  const renderHealthBadge = () => {
    if (!health) return null;

    const statusConfig = {
      healthy: { color: 'success', icon: <CheckCircle size={16} />, text: '正常' },
      warning: { color: 'warning', icon: <AlertCircle size={16} />, text: '警告' },
      error: { color: 'error', icon: <AlertCircle size={16} />, text: '錯誤' },
    };

    const config = statusConfig[health.status];

    return (
      <Badge
        status={config.color as any}
        text={
          <span className="flex items-center gap-1">
            {config.icon}
            {config.text}
          </span>
        }
      />
    );
  };

  /**
   * Render performance chart
   */
  const renderPerformanceChart = () => {
    if (!performanceData) {
      return (
        <div className="flex items-center justify-center h-64 text-gray-400">
          暫無性能數據
        </div>
      );
    }

    const chartData = {
      labels: performanceData.labels || [],
      datasets: [
        {
          label: '投資組合價值',
          data: performanceData.portfolioValue || [],
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          fill: true,
          tension: 0.4,
        },
        {
          label: '基準',
          data: performanceData.benchmark || [],
          borderColor: 'rgb(156, 163, 175)',
          backgroundColor: 'transparent',
          borderDash: [5, 5],
          tension: 0.4,
        },
      ],
    };

    const options = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top' as const,
        },
        tooltip: {
          mode: 'index' as const,
          intersect: false,
        },
      },
      scales: {
        y: {
          beginAtZero: false,
          ticks: {
            callback: (value: any) => `$${value.toLocaleString()}`,
          },
        },
      },
      interaction: {
        mode: 'nearest' as const,
        axis: 'x' as const,
        intersect: false,
      },
    };

    return <Line data={chartData} options={options} />;
  };

  /**
   * Render strategy distribution chart
   */
  const renderDistributionChart = () => {
    // Ensure strategies is an array and has valid data
    if (!strategies || !Array.isArray(strategies)) {
      return null;
    }

    const distribution = strategies.reduce((acc, strategy) => {
      // Safely convert category to string, fallback to 'unknown'
      const category = String(strategy?.category || 'unknown');
      acc[category] = (acc[category] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const chartData = {
      labels: Object.keys(distribution),
      datasets: [
        {
          data: Object.values(distribution),
          backgroundColor: [
            'rgba(59, 130, 246, 0.8)',
            'rgba(16, 185, 129, 0.8)',
            'rgba(245, 158, 11, 0.8)',
            'rgba(239, 68, 68, 0.8)',
            'rgba(139, 92, 246, 0.8)',
          ],
          borderWidth: 0,
        },
      ],
    };

    const options = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right' as const,
        },
      },
    };

    return <Pie data={chartData} options={options} />;
  };

  return (
    <div className={`unified-dashboard ${className}`}>
      {/* Dashboard Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="dashboard-header mb-6"
      >
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              量化交易儀表盤
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              歡迎回來，{user?.username || '交易員'}
            </p>
          </div>

          <div className="flex items-center gap-3">
            {renderHealthBadge()}

            <Select
              value={timeRange}
              onChange={handleTimeRangeChange}
              className="w-24"
              size="large"
            >
              <Option value="1D">今日</Option>
              <Option value="1W">本周</Option>
              <Option value="1M">本月</Option>
              <Option value="3M">三個月</Option>
              <Option value="6M">六個月</Option>
              <Option value="1Y">一年</Option>
              <Option value="ALL">全部</Option>
            </Select>

            <Tooltip title="自動刷新">
              <Switch
                checked={autoRefresh}
                onChange={setAutoRefresh}
                checkedChildren="自動"
                unCheckedChildren="手動"
              />
            </Tooltip>

            <Button
              icon={<RefreshCw size={16} />}
              onClick={refreshData}
              loading={isLoading}
            >
              刷新
            </Button>

            <Tooltip title="導出數據">
              <Button
                icon={<Download size={16} />}
                onClick={handleExport}
              />
            </Tooltip>

            {onFullscreen && (
              <Tooltip title="全屏顯示">
                <Button
                  icon={<Maximize2 size={16} />}
                  onClick={onFullscreen}
                />
              </Tooltip>
            )}
          </div>
        </div>
      </motion.div>

      {/* Key Statistics */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="mb-6"
      >
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} lg={6}>
            <Card className="stat-card">
              <Statistic
                title="總策略數"
                value={displayStats.totalStrategies}
                prefix={<BarChart3 size={18} />}
                suffix={<span className="text-gray-400 text-sm">個</span>}
              />
              <div className="mt-2 flex items-center gap-2 text-sm">
                <span className="text-green-600">
                  {displayStats.activeStrategies} 個運行中
                </span>
              </div>
            </Card>
          </Col>

          <Col xs={24} sm={12} lg={6}>
            <Card className="stat-card">
              <Statistic
                title="總收益率"
                value={displayStats.totalReturn}
                precision={2}
                prefix={displayStats.totalReturn >= 0 ? <TrendingUp size={18} /> : <TrendingDown size={18} />}
                suffix="%"
                valueStyle={{
                  color: displayStats.totalReturn >= 0 ? '#16a34a' : '#dc2626',
                }}
              />
              <div className="mt-2 text-sm text-gray-500">
                Sharpe: {displayStats.sharpeRatio.toFixed(2)}
              </div>
            </Card>
          </Col>

          <Col xs={24} sm={12} lg={6}>
            <Card className="stat-card">
              <Statistic
                title="勝率"
                value={displayStats.winRate}
                precision={2}
                suffix="%"
                prefix={<Activity size={18} />}
              />
              <Progress
                percent={displayStats.winRate}
                size="small"
                className="mt-2"
                strokeColor={{
                  '0%': '#16a34a',
                  '100%': '#22c55e',
                }}
              />
            </Card>
          </Col>

          <Col xs={24} sm={12} lg={6}>
            <Card className="stat-card">
              <Statistic
                title="最大回撤"
                value={displayStats.maxDrawdown}
                precision={2}
                suffix="%"
                prefix={<TrendingDown size={18} />}
                valueStyle={{ color: '#dc2626' }}
              />
              <div className="mt-2 text-sm text-gray-500">
                風險等級: 中等
              </div>
            </Card>
          </Col>
        </Row>
      </motion.div>

      {/* Charts Row */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="mb-6"
      >
        <Row gutter={[16, 16]}>
          <Col xs={24} lg={18}>
            <Card
              title="性能走勢"
              extra={
                <Select size="small" defaultValue="portfolio" className="w-24">
                  <Option value="portfolio">投資組合</Option>
                  <Option value="benchmark">基準</Option>
                  <Option value="both">對比</Option>
                </Select>
              }
              className="chart-card"
            >
              <div className="h-80">
                {renderPerformanceChart()}
              </div>
            </Card>
          </Col>

          <Col xs={24} lg={6}>
            <Card title="策略分佈" className="chart-card">
              <div className="h-80">
                {renderDistributionChart()}
              </div>
            </Card>
          </Col>
        </Row>
      </motion.div>

      {/* Top Strategies and Alerts */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <Row gutter={[16, 16]}>
          <Col xs={24} lg={12}>
            <Card
              title="頂級策略"
              extra={<Button type="link" onClick={() => window.location.href = '/strategies'}>查看全部</Button>}
            >
              <div className="space-y-3">
                {topStrategies.map((strategy, index) => {
                  const strategyId = String(strategy.id || index);
                  return (
                  <div
                    key={strategyId}
                    className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer"
                    onClick={() => handleStrategyClick(strategyId)}
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 flex items-center justify-center bg-primary/10 rounded-full text-primary font-semibold">
                        {index + 1}
                      </div>
                      <div>
                        <div className="font-medium text-gray-900 dark:text-white">
                          {String(strategy.name || 'Unknown')}
                        </div>
                        <div className="text-sm text-gray-500">
                          {String(strategy.category || 'N/A')}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold text-gray-900 dark:text-white">
                        {strategy.performance?.sharpeRatio?.toFixed(2) || 'N/A'}
                      </div>
                      <div className="text-sm text-gray-500">
                        Sharpe
                      </div>
                    </div>
                  </div>
                  );
                })}
                {topStrategies.length === 0 && (
                  <div className="text-center text-gray-400 py-8">
                    暫無策略數據
                  </div>
                )}
              </div>
            </Card>
          </Col>

          <Col xs={24} lg={12}>
            <Card
              title="最近通知"
              extra={
                <Badge count={recentAlerts.length}>
                  <Bell size={18} />
                </Badge>
              }
            >
              <div className="space-y-3">
                {recentAlerts.map((alert) => (
                  <div
                    key={alert.id}
                    className={`flex items-start gap-3 p-3 rounded-lg border-l-4 ${
                      alert.severity === 'error'
                        ? 'border-red-500 bg-red-50 dark:bg-red-900/20'
                        : alert.severity === 'warning'
                        ? 'border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20'
                        : 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    }`}
                  >
                    <div className="mt-0.5">
                      {alert.severity === 'error' ? (
                        <AlertCircle size={16} className="text-red-500" />
                      ) : (
                        <Bell size={16} className="text-blue-500" />
                      )}
                    </div>
                    <div className="flex-1">
                      <div className="text-sm font-medium text-gray-900 dark:text-white">
                        {alert.message}
                      </div>
                      <div className="text-xs text-gray-500">
                        {safeDate(alert.timestamp).toLocaleString('zh-TW')}
                      </div>
                    </div>
                  </div>
                ))}
                {recentAlerts.length === 0 && (
                  <div className="text-center text-gray-400 py-8">
                    暫無新通知
                  </div>
                )}
              </div>
            </Card>
          </Col>
        </Row>
      </motion.div>

      {/* System Status Footer */}
      {health && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="mt-6"
        >
          <Card size="small">
            <div className="flex items-center justify-between flex-wrap gap-4 text-sm">
              <div className="flex items-center gap-6">
                <div className="flex items-center gap-2">
                  <Clock size={16} />
                  <span className="text-gray-500">最後更新:</span>
                  <span className="font-medium">
                    {safeDate(health.lastUpdate).toLocaleTimeString('zh-TW')}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <Activity size={16} />
                  <span className="text-gray-500">API響應:</span>
                  <span className="font-medium">{health.apiResponseTime}ms</span>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-gray-500">CPU:</span>
                  <Progress percent={health.cpuUsage} size="small" className="w-20" showInfo={false} />
                  <span className="font-medium">{health.cpuUsage}%</span>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-gray-500">記憶體:</span>
                  <Progress percent={health.memoryUsage} size="small" className="w-20" showInfo={false} />
                  <span className="font-medium">{health.memoryUsage}%</span>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${
                  health.websocketConnected ? 'bg-green-500' : 'bg-red-500'
                }`} />
                <span className="text-gray-500">
                  WebSocket: {health.websocketConnected ? '已連接' : '未連接'}
                </span>
              </div>
            </div>
          </Card>
        </motion.div>
      )}
    </div>
  );
};

export default UnifiedDashboard;

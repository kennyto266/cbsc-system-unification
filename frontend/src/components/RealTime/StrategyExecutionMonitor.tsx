/**
 * Phase 8.1 WebSocket實時推送系統 - 策略執行監控組件
 * Strategy Execution Monitor Component
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  CardHeader,
  CardContent,
  Typography,
  Box,
  Chip,
  LinearProgress,
  Grid,
  Alert,
  Switch,
  FormControlLabel,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  PlayArrow,
  Pause,
  Stop,
  Refresh,
  Settings,
  Timeline,
  TrendingUp,
  TrendingDown
} from '@mui/icons-material';
import { useStrategyExecution } from '../../hooks/useRealtimeWebSocket';
import { formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';

interface StrategyData {
  strategy_id: string;
  status: 'running' | 'paused' | 'stopped' | 'error';
  execution_time: number;
  performance: {
    total_return: number;
    daily_return: number;
    win_rate: number;
  };
  signals: Array<{
    symbol: string;
    action: 'BUY' | 'SELL' | 'HOLD';
    price: number;
    confidence: number;
  }>;
  positions: Array<{
    symbol: string;
    quantity: number;
    avg_price: number;
    current_price: number;
    pnl: number;
  }>;
  progress: number;
  error_message?: string;
}

interface StrategyExecutionMonitorProps {
  strategyId: string;
  strategyName?: string;
  height?: number;
  showSignals?: boolean;
  showPositions?: boolean;
}

const StrategyExecutionMonitor: React.FC<StrategyExecutionMonitorProps> = ({
  strategyId,
  strategyName,
  height = 400,
  showSignals = true,
  showPositions = true
}) => {
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const {
    isConnected,
    lastMessage,
    subscribeToStrategy,
    unsubscribeFromStrategy,
    error
  } = useStrategyExecution();

  const [strategyData, setStrategyData] = useState<StrategyData | null>(null);

  // Subscribe to strategy updates
  useEffect(() => {
    if (isConnected) {
      subscribeToStrategy(strategyId, {
        onMessage: (message) => {
          if (message.data.strategy_id === strategyId) {
            setStrategyData(message.data);
            setLastUpdate(new Date());
          }
        }
      });
    }

    return () => {
      unsubscribeFromStrategy();
    };
  }, [isConnected, strategyId, subscribeToStrategy, unsubscribeFromStrategy]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'success';
      case 'paused':
        return 'warning';
      case 'stopped':
        return 'default';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <PlayArrow />;
      case 'paused':
        return <Pause />;
      case 'stopped':
        return <Stop />;
      default:
        return null;
    }
  };

  const getActionColor = (action: string) => {
    switch (action) {
      case 'BUY':
        return 'success';
      case 'SELL':
        return 'error';
      case 'HOLD':
        return 'default';
      default:
        return 'default';
    }
  };

  const formatNumber = (num: number, decimals: number = 2) => {
    return new Intl.NumberFormat('zh-CN', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }).format(num);
  };

  const formatPercent = (num: number) => {
    return `${num > 0 ? '+' : ''}${formatNumber(num * 100, 2)}%`;
  };

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        連接錯誤: {error}
      </Alert>
    );
  }

  return (
    <Card sx={{ height }}>
      <CardHeader
        title={
          <Box display="flex" alignItems="center" gap={1}>
            <Typography variant="h6">
              {strategyName || `策略 ${strategyId}`}
            </Typography>
            <Chip
              label={isConnected ? '已連接' : '未連接'}
              color={isConnected ? 'success' : 'default'}
              size="small"
            />
          </Box>
        }
        action={
          <Box display="flex" alignItems="center" gap={1}>
            <FormControlLabel
              control={
                <Switch
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  size="small"
                />
              }
              label="自動刷新"
            />
            <Tooltip title="手動刷新">
              <IconButton onClick={() => window.location.reload()}>
                <Refresh />
              </IconButton>
            </Tooltip>
            <Tooltip title="設置">
              <IconButton>
                <Settings />
              </IconButton>
            </Tooltip>
          </Box>
        }
        subheader={
          lastUpdate && (
            <Typography variant="caption" color="textSecondary">
              最後更新: {formatDistanceToNow(lastUpdate, { addSuffix: true, locale: zhCN })}
            </Typography>
          )
        }
      />

      <CardContent sx={{ height: 'calc(100% - 80px)', overflow: 'auto' }}>
        {strategyData ? (
          <Grid container spacing={2}>
            {/* Status Card */}
            <Grid item xs={12} md={6}>
              <Box mb={2}>
                <Typography variant="subtitle2" gutterBottom>
                  執行狀態
                </Typography>
                <Box display="flex" alignItems="center" gap={1} mb={1}>
                  {getStatusIcon(strategyData.status)}
                  <Chip
                    label={strategyData.status.toUpperCase()}
                    color={getStatusColor(strategyData.status)}
                    variant="outlined"
                  />
                </Box>
                <Box display="flex" justifyContent="space-between" mb={1}>
                  <Typography variant="body2" color="textSecondary">
                    執行進度
                  </Typography>
                  <Typography variant="body2">
                    {formatNumber(strategyData.progress * 100, 1)}%
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={strategyData.progress * 100}
                  sx={{ mb: 1 }}
                />
                <Typography variant="body2" color="textSecondary">
                  執行時間: {strategyData.execution_time}ms
                </Typography>
                {strategyData.error_message && (
                  <Alert severity="error" sx={{ mt: 1 }}>
                    {strategyData.error_message}
                  </Alert>
                )}
              </Box>
            </Grid>

            {/* Performance Card */}
            <Grid item xs={12} md={6}>
              <Box mb={2}>
                <Typography variant="subtitle2" gutterBottom>
                  性能指標
                </Typography>
                <Grid container spacing={1}>
                  <Grid item xs={6}>
                    <Box>
                      <Typography variant="body2" color="textSecondary">
                        總回報
                      </Typography>
                      <Typography
                        variant="h6"
                        color={strategyData.performance.total_return >= 0 ? 'success.main' : 'error.main'}
                        display="flex"
                        alignItems="center"
                        gap={0.5}
                      >
                        {strategyData.performance.total_return >= 0 ? <TrendingUp /> : <TrendingDown />}
                        {formatPercent(strategyData.performance.total_return)}
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6}>
                    <Box>
                      <Typography variant="body2" color="textSecondary">
                        日回報
                      </Typography>
                      <Typography
                        variant="h6"
                        color={strategyData.performance.daily_return >= 0 ? 'success.main' : 'error.main'}
                      >
                        {formatPercent(strategyData.performance.daily_return)}
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6}>
                    <Box>
                      <Typography variant="body2" color="textSecondary">
                        勝率
                      </Typography>
                      <Typography variant="h6">
                        {formatPercent(strategyData.performance.win_rate)}
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6}>
                    <Box>
                      <Typography variant="body2" color="textSecondary">
                        更新時間
                      </Typography>
                      <Typography variant="body2">
                        {lastUpdate?.toLocaleTimeString('zh-CN')}
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
              </Box>
            </Grid>

            {/* Signals */}
            {showSignals && strategyData.signals.length > 0 && (
              <Grid item xs={12}>
                <Box mb={2}>
                  <Typography variant="subtitle2" gutterBottom>
                    最新信號
                  </Typography>
                  {strategyData.signals.map((signal, index) => (
                    <Box
                      key={index}
                      p={1}
                      mb={1}
                      borderRadius={1}
                      bgcolor="background.paper"
                      border={1}
                      borderColor="divider"
                    >
                      <Box display="flex" justifyContent="space-between" alignItems="center">
                        <Box>
                          <Typography variant="body1" fontWeight="bold">
                            {signal.symbol}
                          </Typography>
                          <Typography variant="body2" color="textSecondary">
                            價格: ¥{formatNumber(signal.price)}
                          </Typography>
                        </Box>
                        <Box textAlign="right">
                          <Chip
                            label={signal.action}
                            color={getActionColor(signal.action)}
                            size="small"
                          />
                          <Typography variant="body2" color="textSecondary">
                            置信度: {formatNumber(signal.confidence * 100, 1)}%
                          </Typography>
                        </Box>
                      </Box>
                    </Box>
                  ))}
                </Box>
              </Grid>
            )}

            {/* Positions */}
            {showPositions && strategyData.positions && strategyData.positions.length > 0 && (
              <Grid item xs={12}>
                <Box mb={2}>
                  <Typography variant="subtitle2" gutterBottom>
                    持倉狀況
                  </Typography>
                  {strategyData.positions.map((position, index) => (
                    <Box
                      key={index}
                      p={1}
                      mb={1}
                      borderRadius={1}
                      bgcolor="background.paper"
                      border={1}
                      borderColor="divider"
                    >
                      <Box display="flex" justifyContent="space-between" alignItems="center">
                        <Box>
                          <Typography variant="body1" fontWeight="bold">
                            {position.symbol}
                          </Typography>
                          <Typography variant="body2" color="textSecondary">
                            數量: {position.quantity}
                          </Typography>
                          <Typography variant="body2" color="textSecondary">
                            成本: ¥{formatNumber(position.avg_price)}
                          </Typography>
                        </Box>
                        <Box textAlign="right">
                          <Typography variant="body2">
                            現價: ¥{formatNumber(position.current_price)}
                          </Typography>
                          <Typography
                            variant="body2"
                            color={position.pnl >= 0 ? 'success.main' : 'error.main'}
                          >
                            盈虧: {formatPercent(position.pnl)}
                          </Typography>
                        </Box>
                      </Box>
                    </Box>
                  ))}
                </Box>
              </Grid>
            )}
          </Grid>
        ) : (
          <Box
            display="flex"
            flexDirection="column"
            alignItems="center"
            justifyContent="center"
            height="100%"
          >
            <Timeline sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
            <Typography variant="body1" color="textSecondary">
              等待策略執行數據...
            </Typography>
            {!isConnected && (
              <Typography variant="body2" color="error" sx={{ mt: 1 }}>
                WebSocket未連接
              </Typography>
            )}
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default StrategyExecutionMonitor;
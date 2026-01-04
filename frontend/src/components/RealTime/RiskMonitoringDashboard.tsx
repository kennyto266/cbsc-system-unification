/**
 * Phase 8.1 WebSocket實時推送系統 - 風險監控儀表板
 * Risk Monitoring Dashboard Component
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  CardHeader,
  CardContent,
  Typography,
  Box,
  Grid,
  Alert,
  Chip,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
  IconButton,
  Badge
} from '@mui/material';
import {
  Warning,
  Error,
  Info,
  Security,
  Assessment,
  TrendingUp,
  TrendingDown,
  Refresh,
  NotificationsActive,
  PieChart,
  DonutLarge
} from '@mui/icons-material';
import { useRiskMonitoring } from '../../hooks/useRealtimeWebSocket';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  BarChart,
  Bar
} from 'recharts';
import { formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';

interface RiskData {
  portfolio_id: string;
  risk_metrics: {
    var_95: number;
    var_99: number;
    cvar_95: number;
    cvar_99: number;
    volatility: number;
    beta: number;
    tracking_error: number;
  };
  exposure: {
    equity: number;
    fixed_income: number;
    alternatives: number;
    cash: number;
  };
  concentration: {
    top_10_holdings: number;
    sector_concentration: number;
    geographic_concentration: number;
  };
  alerts: Array<{
    type: string;
    message: string;
    severity: 'LOW' | 'MEDIUM' | 'HIGH';
  }>;
  risk_score: number;
  stop_loss_triggered: boolean;
}

interface RiskMonitoringDashboardProps {
  portfolioId?: string;
  portfolioName?: string;
  showAlerts?: boolean;
  showExposure?: boolean;
  showConcentration?: boolean;
}

const RiskMonitoringDashboard: React.FC<RiskMonitoringDashboardProps> = ({
  portfolioId,
  portfolioName = '投資組合',
  showAlerts = true,
  showExposure = true,
  showConcentration = true
}) => {
  const [riskHistory, setRiskHistory] = useState<any[]>([]);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const {
    isConnected,
    lastMessage,
    subscribeToRisk,
    unsubscribeFromRisk,
    error
  } = useRiskMonitoring();

  const [riskData, setRiskData] = useState<RiskData | null>(null);

  // Colors for risk levels
  const getRiskColor = (value: number, thresholds: { low: number; medium: number; high: number }) => {
    if (value <= thresholds.low) return 'success.main';
    if (value <= thresholds.medium) return 'warning.main';
    return 'error.main';
  };

  const getRiskScoreColor = (score: number) => {
    if (score <= 30) return 'success.main';
    if (score <= 60) return 'warning.main';
    return 'error.main';
  };

  const getAlertIcon = (severity: string) => {
    switch (severity) {
      case 'HIGH':
        return <Error color="error" />;
      case 'MEDIUM':
        return <Warning color="warning" />;
      default:
        return <Info color="info" />;
    }
  };

  const formatPercent = (num: number) => {
    return `${num > 0 ? '+' : ''}${(num * 100).toFixed(2)}%`;
  };

  const formatNumber = (num: number, decimals: number = 2) => {
    return new Intl.NumberFormat('zh-CN', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }).format(num);
  };

  // Subscribe to risk updates
  useEffect(() => {
    if (isConnected) {
      subscribeToRisk(portfolioId, {
        onMessage: (message) => {
          if (!portfolioId || message.data.portfolio_id === portfolioId) {
            setRiskData(message.data);
            setLastUpdate(new Date());

            // Update risk history
            setRiskHistory(prev => {
              const newHistory = [
                ...prev,
                {
                  timestamp: new Date(message.timestamp),
                  riskScore: message.data.risk_score,
                  var95: message.data.risk_metrics.var_95,
                  volatility: message.data.risk_metrics.volatility
                }
              ].slice(-50); // Keep last 50 data points
              return newHistory;
            });
          }
        }
      });
    }

    return () => {
      unsubscribeFromRisk();
    };
  }, [isConnected, portfolioId, subscribeToRisk, unsubscribeFromRisk]);

  const exposureColors = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300'];
  const exposureData = riskData ? [
    { name: '股票', value: riskData.exposure.equity, color: exposureColors[0] },
    { name: '固定收益', value: riskData.exposure.fixed_income, color: exposureColors[1] },
    { name: '另類投資', value: riskData.exposure.alternatives, color: exposureColors[2] },
    { name: '現金', value: riskData.exposure.cash, color: exposureColors[3] }
  ] : [];

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        連接錯誤: {error}
      </Alert>
    );
  }

  return (
    <Grid container spacing={2}>
      {/* Risk Score Card */}
      <Grid item xs={12} md={3}>
        <Card>
          <CardHeader
            title="風險評分"
            subheader="綜合風險評估"
            action={
              <Badge
                color={riskData?.risk_score && riskData.risk_score > 70 ? 'error' : 'default'}
                variant="dot"
              >
                <IconButton size="small">
                  <Security />
                </IconButton>
              </Badge>
            }
          />
          <CardContent>
            <Box textAlign="center" py={2}>
              <Typography
                variant="h2"
                color={riskData ? getRiskScoreColor(riskData.risk_score) : 'text.secondary'}
              >
                {riskData ? riskData.risk_score : '--'}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                {riskData && riskData.risk_score <= 30 ? '低風險' :
                 riskData && riskData.risk_score <= 60 ? '中等風險' : '高風險'}
              </Typography>
              {riskData?.stop_loss_triggered && (
                <Alert severity="error" sx={{ mt: 1 }}>
                  止損已觸發！
                </Alert>
              )}
            </Box>
          </CardContent>
        </Card>
      </Grid>

      {/* VaR Metrics Card */}
      <Grid item xs={12} md={4}>
        <Card>
          <CardHeader
            title="風險價值 (VaR)"
            subheader="置信水平95%/99%"
          />
          <CardContent>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Box textAlign="center">
                  <Typography variant="h5" color="primary">
                    {riskData ? formatPercent(riskData.risk_metrics.var_95) : '--'}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    VaR (95%)
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6}>
                <Box textAlign="center">
                  <Typography variant="h5" color="primary">
                    {riskData ? formatPercent(riskData.risk_metrics.var_99) : '--'}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    VaR (99%)
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6}>
                <Box textAlign="center">
                  <Typography variant="body1">
                    {riskData ? formatPercent(riskData.risk_metrics.cvar_95) : '--'}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    CVaR (95%)
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6}>
                <Box textAlign="center">
                  <Typography variant="body1">
                    {riskData ? formatPercent(riskData.risk_metrics.cvar_99) : '--'}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    CVaR (99%)
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Grid>

      {/* Risk Metrics Card */}
      <Grid item xs={12} md={5}>
        <Card>
          <CardHeader
            title="其他風險指標"
            action={
              <Tooltip title="更新時間">
                <Typography variant="caption" color="textSecondary">
                  {lastUpdate ? formatDistanceToNow(lastUpdate, { addSuffix: true, locale: zhCN }) : '--'}
                </Typography>
              </Tooltip>
            }
          />
          <CardContent>
            <Grid container spacing={2}>
              <Grid item xs={4}>
                <Box>
                  <Typography variant="body2" color="textSecondary">
                    波動率
                  </Typography>
                  <Typography variant="h6" color={riskData && riskData.risk_metrics.volatility > 0.2 ? 'error.main' : 'text.primary'}>
                    {riskData ? formatPercent(riskData.risk_metrics.volatility) : '--'}
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={4}>
                <Box>
                  <Typography variant="body2" color="textSecondary">
                    Beta
                  </Typography>
                  <Typography variant="h6">
                    {riskData ? formatNumber(riskData.risk_metrics.beta, 2) : '--'}
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={4}>
                <Box>
                  <Typography variant="body2" color="textSecondary">
                    跟蹤誤差
                  </Typography>
                  <Typography variant="h6" color={riskData && riskData.risk_metrics.tracking_error > 0.05 ? 'warning.main' : 'text.primary'}>
                    {riskData ? formatPercent(riskData.risk_metrics.tracking_error) : '--'}
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Grid>

      {/* Risk History Chart */}
      <Grid item xs={12} md={8}>
        <Card>
          <CardHeader
            title="風險趨勢"
            action={
              <IconButton size="small">
                <Refresh />
              </IconButton>
            }
          />
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={riskHistory}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={(value) => new Date(value).toLocaleTimeString('zh-CN')}
                />
                <YAxis />
                <RechartsTooltip
                  labelFormatter={(value) => new Date(value).toLocaleString('zh-CN')}
                  formatter={(value: any, name: string) => [
                    typeof value === 'number' ? formatPercent(value) : value,
                    name === 'riskScore' ? '風險評分' :
                    name === 'var95' ? 'VaR (95%)' :
                    name === 'volatility' ? '波動率' : name
                  ]}
                />
                <Line
                  type="monotone"
                  dataKey="riskScore"
                  stroke="#8884d8"
                  name="riskScore"
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="var95"
                  stroke="#82ca9d"
                  name="var95"
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="volatility"
                  stroke="#ffc658"
                  name="volatility"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </Grid>

      {/* Exposure Chart */}
      {showExposure && (
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader
              title="資產配置"
              avatar={<PieChart />}
            />
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <RechartsPieChart>
                  <Pie
                    data={exposureData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {exposureData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <RechartsTooltip formatter={(value: any) => formatPercent(value)} />
                </RechartsPieChart>
              </ResponsiveContainer>
              <Box mt={2}>
                {exposureData.map((item, index) => (
                  <Box key={item.name} display="flex" alignItems="center" mb={0.5}>
                    <Box
                      width={12}
                      height={12}
                      borderRadius={1}
                      bgcolor={item.color}
                      mr={1}
                    />
                    <Typography variant="body2">
                      {item.name}: {formatPercent(item.value)}
                    </Typography>
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      )}

      {/* Concentration Metrics */}
      {showConcentration && riskData && (
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader
              title="集中度風險"
              avatar={<DonutLarge />}
            />
            <CardContent>
              <TableContainer>
                <Table>
                  <TableBody>
                    <TableRow>
                      <TableCell>前十大持倉</TableCell>
                      <TableCell align="right">
                        <Typography
                          color={riskData.concentration.top_10_holdings > 0.5 ? 'error.main' : 'text.primary'}
                        >
                          {formatPercent(riskData.concentration.top_10_holdings)}
                        </Typography>
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>行業集中度</TableCell>
                      <TableCell align="right">
                        <Typography
                          color={riskData.concentration.sector_concentration > 0.6 ? 'error.main' : 'text.primary'}
                        >
                          {formatPercent(riskData.concentration.sector_concentration)}
                        </Typography>
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>地理集中度</TableCell>
                      <TableCell align="right">
                        <Typography
                          color={riskData.concentration.geographic_concentration > 0.5 ? 'warning.main' : 'text.primary'}
                        >
                          {formatPercent(riskData.concentration.geographic_concentration)}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
      )}

      {/* Alerts */}
      {showAlerts && riskData && riskData.alerts.length > 0 && (
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader
              title="風險警報"
              avatar={
                <Badge badgeContent={riskData.alerts.length} color="error">
                  <NotificationsActive />
                </Badge>
              }
            />
            <CardContent>
              <List>
                {riskData.alerts.map((alert, index) => (
                  <React.Fragment key={index}>
                    <ListItem>
                      <ListItemIcon>
                        {getAlertIcon(alert.severity)}
                      </ListItemIcon>
                      <ListItemText
                        primary={alert.message}
                        secondary={
                          <Chip
                            label={alert.type}
                            size="small"
                            color={alert.severity === 'HIGH' ? 'error' :
                                   alert.severity === 'MEDIUM' ? 'warning' : 'default'}
                          />
                        }
                      />
                    </ListItem>
                    {index < riskData.alerts.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>
      )}

      {/* No Data State */}
      {!riskData && (
        <Grid item xs={12}>
          <Box
            display="flex"
            flexDirection="column"
            alignItems="center"
            justifyContent="center"
            height={300}
          >
            <Assessment sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="textSecondary" gutterBottom>
              等待風險監控數據...
            </Typography>
            {!isConnected && (
              <Typography variant="body2" color="error">
                WebSocket未連接
              </Typography>
            )}
          </Box>
        </Grid>
      )}
    </Grid>
  );
};

export default RiskMonitoringDashboard;
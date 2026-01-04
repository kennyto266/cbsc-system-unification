import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Activity,
  AlertTriangle,
  CheckCircle,
  Play,
  Pause,
  Square,
  Settings,
  FileText,
  BarChart3,
  Shield,
  Zap
} from 'lucide-react';

// Mock data - would be fetched from API
const mockStrategyData = {
  id: '1',
  name: '動量策略',
  status: 'active',
  performance: {
    totalReturn: 12.5,
    sharpeRatio: 1.8,
    maxDrawdown: -8.3,
    winRate: 0.65,
    totalTrades: 156,
    winRate: 65,
    profitFactor: 1.8,
  },
  portfolio: {
    totalValue: 112500,
    initialCapital: 100000,
    cash: 15000,
    positions: [
      { symbol: '0700.HK', quantity: 1000, value: 35000, pnl: 2500, pnlPercent: 7.7 },
      { symbol: '0939.HK', quantity: 2000, value: 28000, pnl: -800, pnlPercent: -2.8 },
      { symbol: '1398.HK', quantity: 1500, value: 34500, pnl: 1800, pnlPercent: 5.5 },
    ],
    unrealizedPnl: 3500,
    dailyPnl: 1250,
  },
  riskMetrics: {
    var95: 2450,
    es99: 3800,
    volatility: 15.2,
    beta: 0.85,
    correlation: 0.42,
  },
  recentTrades: [
    { id: '1', symbol: '0700.HK', side: 'BUY', quantity: 500, price: 35.2, time: '10:30' },
    { id: '2', symbol: '0939.HK', side: 'SELL', quantity: 1000, price: 14.5, time: '10:15' },
    { id: '3', symbol: '1398.HK', side: 'BUY', quantity: 300, price: 23.0, time: '09:45' },
  ],
  alerts: [
    { level: 'warning', message: '0700.HK 波動率超過閾值', time: '11:20' },
    { level: 'info', message: '投資組合風險指標更新', time: '11:00' },
  ],
  backtestHistory: [
    { date: '2024-01', return: 2.1 },
    { date: '2024-02', return: 1.8 },
    { date: '2024-03', return: 3.2 },
    { date: '2024-04', return: -1.5 },
    { date: '2024-05', return: 2.8 },
    { date: '2024-06', return: 4.1 },
  ],
  riskHistory: [
    { date: '2024-01', var: 1800, drawdown: -2.1 },
    { date: '2024-02', var: 2200, drawdown: -4.3 },
    { date: '2024-03', var: 1950, drawdown: -1.8 },
    { date: '2024-04', var: 2800, drawdown: -6.5 },
    { date: '2024-05', var: 2100, drawdown: -3.2 },
    { date: '2024-06', var: 2450, drawdown: -8.3 },
  ],
};

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const StrategyDashboardPage: React.FC = () => {
  const { strategyId } = useParams();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('overview');
  const [isTrading, setIsTrading] = useState(true);
  const [selectedTimeframe, setSelectedTimeframe] = useState('1M');

  const handleStartTrading = async () => {
    // API call to start trading
    setIsTrading(true);
  };

  const handleStopTrading = async () => {
    // API call to stop trading
    setIsTrading(false);
  };

  const handleRunBacktest = () => {
    navigate(`/strategies/${strategyId}/backtest`);
  };

  const renderOverviewTab = () => (
    <div className="space-y-6">
      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">總回報率</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              +{mockStrategyData.performance.totalReturn}%
            </div>
            <p className="text-xs text-muted-foreground">
              相比初始資金
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Sharpe比率</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {mockStrategyData.performance.sharpeRatio}
            </div>
            <p className="text-xs text-muted-foreground">
              年化比率 (Rf=3%)
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">最大回撤</CardTitle>
            <TrendingDown className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {mockStrategyData.performance.maxDrawdown}%
            </div>
            <p className="text-xs text-muted-foreground">
              歷史最大回撤
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">勝率</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {mockStrategyData.performance.winRate}%
            </div>
            <p className="text-xs text-muted-foreground">
              {mockStrategyData.performance.totalTrades} 筆交易
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Portfolio and Performance Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Portfolio Performance */}
        <Card>
          <CardHeader>
            <CardTitle>投資組合表現</CardTitle>
            <CardDescription>策略執行以來的回報走勢</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={mockStrategyData.backtestHistory}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip formatter={(value) => [`${value}%`, '回報率']} />
                <Area
                  type="monotone"
                  dataKey="return"
                  stroke="#8884d8"
                  fill="#8884d8"
                  fillOpacity={0.3}
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Portfolio Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>持倉分布</CardTitle>
            <CardDescription>當前持倉價值分布</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={mockStrategyData.portfolio.positions}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => `${entry.symbol}: ${((entry.value / mockStrategyData.portfolio.totalValue) * 100).toFixed(1)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {mockStrategyData.portfolio.positions.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => [`$${value.toLocaleString()}`, '價值']} />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Position Details */}
      <Card>
        <CardHeader>
          <CardTitle>當前持倉</CardTitle>
          <CardDescription>實時持倉詳情和盈虧狀況</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {mockStrategyData.portfolio.positions.map((position, index) => (
              <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                    <span className="text-lg font-bold text-blue-600">
                      {position.symbol.substring(0, 2)}
                    </span>
                  </div>
                  <div>
                    <p className="font-medium">{position.symbol}</p>
                    <p className="text-sm text-muted-foreground">
                      {position.quantity.toLocaleString()} 股 @ ${(position.value / position.quantity).toFixed(2)}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-medium">${position.value.toLocaleString()}</p>
                  <p className={`text-sm ${position.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {position.pnl >= 0 ? '+' : ''}{position.pnl.toLocaleString()} ({position.pnlPercent >= 0 ? '+' : ''}{position.pnlPercent}%)
                  </p>
                </div>
              </div>
            ))}
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <p className="font-medium">現金</p>
                <p className="text-sm text-muted-foreground">可用資金</p>
              </div>
              <p className="font-medium">${mockStrategyData.portfolio.cash.toLocaleString()}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderRiskTab = () => (
    <div className="space-y-6">
      {/* Risk Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">VaR (95%)</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${mockStrategyData.riskMetrics.var95.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              日風險價值
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Expected Shortfall</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${mockStrategyData.riskMetrics.es99.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              99% ES
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">波動率</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {mockStrategyData.riskMetrics.volatility}%
            </div>
            <p className="text-xs text-muted-foreground">
              年化波動率
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Beta</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {mockStrategyData.riskMetrics.beta}
            </div>
            <p className="text-xs text-muted-foreground">
              相對市場
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Risk Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* VaR History */}
        <Card>
          <CardHeader>
            <CardTitle>風險價值走勢</CardTitle>
            <CardDescription>每日VaR和最大回撤變化</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={mockStrategyData.riskHistory}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Legend />
                <Bar yAxisId="right" dataKey="var" fill="#8884d8" name="VaR" />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="drawdown"
                  stroke="#ff7300"
                  name="回撤"
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Risk Alerts */}
        <Card>
          <CardHeader>
            <CardTitle>風險警報</CardTitle>
            <CardDescription>實時風險監控提醒</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {mockStrategyData.alerts.map((alert, index) => (
                <Alert key={index} variant={alert.level === 'warning' ? 'destructive' : 'default'}>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertTitle className="text-sm">
                    {alert.level === 'warning' ? '警告' : '信息'}
                  </AlertTitle>
                  <AlertDescription className="text-sm">
                    {alert.message}
                    <span className="ml-2 text-xs text-muted-foreground">{alert.time}</span>
                  </AlertDescription>
                </Alert>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );

  const renderTradingTab = () => (
    <div className="space-y-6">
      {/* Trading Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            交易控制
            <div className="flex items-center space-x-2">
              <Badge variant={isTrading ? "default" : "secondary"}>
                {isTrading ? '交易中' : '已停止'}
              </Badge>
            </div>
          </CardTitle>
          <CardDescription>
            策略實時交易控制和監控
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-4">
            {!isTrading ? (
              <Button onClick={handleStartTrading} className="bg-green-600 hover:bg-green-700">
                <Play className="w-4 h-4 mr-2" />
                開始交易
              </Button>
            ) : (
              <Button onClick={handleStopTrading} variant="destructive">
                <Square className="w-4 h-4 mr-2" />
                停止交易
              </Button>
            )}
            <Button variant="outline" onClick={handleRunBacktest}>
              <FileText className="w-4 h-4 mr-2" />
              運行回測
            </Button>
            <Button variant="outline">
              <Settings className="w-4 h-4 mr-2" />
              策略設置
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Recent Trades */}
      <Card>
        <CardHeader>
          <CardTitle>最近交易</CardTitle>
          <CardDescription>實時交易記錄</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {mockStrategyData.recentTrades.map((trade, index) => (
              <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-4">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                    trade.side === 'BUY' ? 'bg-green-100' : 'bg-red-100'
                  }`}>
                    <span className={`text-sm font-bold ${
                      trade.side === 'BUY' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {trade.side[0]}
                    </span>
                  </div>
                  <div>
                    <p className="font-medium">{trade.symbol}</p>
                    <p className="text-sm text-muted-foreground">
                      {trade.quantity.toLocaleString()} 股 @ ${trade.price}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm text-muted-foreground">{trade.time}</p>
                  <p className="font-medium">
                    ${(trade.quantity * trade.price).toLocaleString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Performance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">今日盈虧</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              +${mockStrategyData.portfolio.dailyPnl.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              日度表現
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">未實現盈虧</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              +${mockStrategyData.portfolio.unrealizedPnl.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              當前持倉
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">總資產</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${mockStrategyData.portfolio.totalValue.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              投資組合價值
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">{mockStrategyData.name}</h1>
          <p className="text-muted-foreground">策略管理控制台</p>
        </div>
        <div className="flex items-center space-x-4">
          <Badge variant={mockStrategyData.status === 'active' ? 'default' : 'secondary'}>
            {mockStrategyData.status === 'active' ? '運行中' : '已停止'}
          </Badge>
        </div>
      </div>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="overview" className="flex items-center space-x-2">
            <Activity className="w-4 h-4" />
            <span>總覽</span>
          </TabsTrigger>
          <TabsTrigger value="risk" className="flex items-center space-x-2">
            <Shield className="w-4 h-4" />
            <span>風險管理</span>
          </TabsTrigger>
          <TabsTrigger value="trading" className="flex items-center space-x-2">
            <Zap className="w-4 h-4" />
            <span>實時交易</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-6">
          {renderOverviewTab()}
        </TabsContent>

        <TabsContent value="risk" className="mt-6">
          {renderRiskTab()}
        </TabsContent>

        <TabsContent value="trading" className="mt-6">
          {renderTradingTab()}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default StrategyDashboardPage;
/**
 * BacktestReport Page - 回測報告頁面
 * 
 * 顯示單個回測的詳細報告，包括：
 * - 績效指標
 * - 交易記錄
 * - 資金曲線
 * - 風險分析
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Download, TrendingUp, TrendingDown, Activity, DollarSign } from 'lucide-react';
import { Card, Row, Col, Button, Table, Tag, Progress, Tabs } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

const { TabPane } = Tabs;

// Types
interface PerformanceMetrics {
  total_return: number;
  annual_return: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  max_drawdown: number;
  win_rate: number;
  profit_factor: number;
  avg_trade: number;
  total_trades: number;
  profitable_trades: number;
  losing_trades: number;
}

interface TradeRecord {
  id: string;
  symbol: string;
  type: 'long' | 'short';
  entry_price: number;
  exit_price: number;
  quantity: number;
  entry_time: string;
  exit_time: string;
  profit_loss: number;
  profit_loss_percent: number;
}

interface EquityPoint {
  timestamp: string;
  equity: number;
  drawdown: number;
}

interface BacktestReportData {
  id: string;
  strategy_name: string;
  symbol: string;
  status: string;
  start_date: string;
  end_date: string;
  performance: PerformanceMetrics;
  trades: TradeRecord[];
  equity_curve: EquityPoint[];
  initial_capital: number;
  final_capital: number;
}

export const BacktestReport: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [reportData, setReportData] = useState<BacktestReportData | null>(null);

  useEffect(() => {
    // Fetch backtest report data
    const fetchReport = async () => {
      setLoading(true);
      try {
        // TODO: Replace with actual API call
        // const response = await backtestApi.getBacktestById(id);
        
        // Mock data for now
        setTimeout(() => {
          setReportData({
            id: id || '1',
            strategy_name: 'MA Crossover Strategy',
            symbol: 'AAPL',
            status: 'completed',
            start_date: '2024-01-01',
            end_date: '2024-12-31',
            initial_capital: 100000,
            final_capital: 125000,
            performance: {
              total_return: 25.0,
              annual_return: 25.0,
              sharpe_ratio: 1.85,
              sortino_ratio: 2.45,
              max_drawdown: -12.5,
              win_rate: 58.5,
              profit_factor: 1.92,
              avg_trade: 325.5,
              total_trades: 77,
              profitable_trades: 45,
              losing_trades: 32,
            },
            trades: [],
            equity_curve: [],
          });
          setLoading(false);
        }, 500);
      } catch (error) {
        console.error('Failed to fetch backtest report:', error);
        setLoading(false);
      }
    };

    if (id) {
      fetchReport();
    }
  }, [id]);

  const handleExport = (format: 'pdf' | 'csv' | 'json') => {
    console.log(`Exporting backtest report as ${format}`);
    // TODO: Implement export functionality
  };

  const handleRunAgain = () => {
    console.log('Running backtest again');
    // TODO: Implement run again functionality
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!reportData) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <p className="text-gray-500">回測報告未找到</p>
          <Button onClick={() => navigate('/backtests')} className="mt-4">
            返回回測列表
          </Button>
        </div>
      </div>
    );
  }

  // Performance metrics cards
  const metricCards = [
    {
      title: '總回報',
      value: `${reportData.performance.total_return.toFixed(2)}%`,
      icon: reportData.performance.total_return >= 0 ? TrendingUp : TrendingDown,
      color: reportData.performance.total_return >= 0 ? 'green' : 'red',
    },
    {
      title: '夏普比率',
      value: reportData.performance.sharpe_ratio.toFixed(2),
      icon: Activity,
      color: 'blue',
    },
    {
      title: '最大回撤',
      value: `${reportData.performance.max_drawdown.toFixed(2)}%`,
      icon: TrendingDown,
      color: 'orange',
    },
    {
      title: '勝率',
      value: `${reportData.performance.win_rate.toFixed(1)}%`,
      icon: DollarSign,
      color: 'purple',
    },
  ];

  // Trade table columns
  const tradeColumns: ColumnsType<TradeRecord> = [
    {
      title: '交易ID',
      dataIndex: 'id',
      key: 'id',
      width: 100,
    },
    {
      title: '類型',
      dataIndex: 'type',
      key: 'type',
      width: 80,
      render: (type: string) => (
        <Tag color={type === 'long' ? 'green' : 'red'}>
          {type === 'long' ? '做多' : '做空'}
        </Tag>
      ),
    },
    {
      title: '入場價',
      dataIndex: 'entry_price',
      key: 'entry_price',
      render: (price: number) => `$${price.toFixed(2)}`,
    },
    {
      title: '出場價',
      dataIndex: 'exit_price',
      key: 'exit_price',
      render: (price: number) => `$${price.toFixed(2)}`,
    },
    {
      title: '數量',
      dataIndex: 'quantity',
      key: 'quantity',
    },
    {
      title: '入場時間',
      dataIndex: 'entry_time',
      key: 'entry_time',
    },
    {
      title: '出場時間',
      dataIndex: 'exit_time',
      key: 'exit_time',
    },
    {
      title: '盈虧',
      dataIndex: 'profit_loss',
      key: 'profit_loss',
      render: (pl: number) => (
        <span className={pl >= 0 ? 'text-green-600' : 'text-red-600'}>
          ${pl.toFixed(2)}
        </span>
      ),
    },
    {
      title: '盈虧%',
      dataIndex: 'profit_loss_percent',
      key: 'profit_loss_percent',
      render: (pct: number) => (
        <span className={pct >= 0 ? 'text-green-600' : 'text-red-600'}>
          {pct.toFixed(2)}%
        </span>
      ),
    },
  ];

  return (
    <div className="p-6 bg-gray-50 dark:bg-gray-900 min-h-screen">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Button
              icon={<ArrowLeft className="h-4 w-4" />}
              onClick={() => navigate('/backtests')}
            >
              返回
            </Button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                {reportData.strategy_name}
              </h1>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {reportData.symbol} • {reportData.start_date} 至 {reportData.end_date}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Button onClick={handleRunAgain}>
              再次運行
            </Button>
            <Button
              icon={<Download className="h-4 w-4" />}
              onClick={() => handleExport('pdf')}
            >
              導出 PDF
            </Button>
          </div>
        </div>
      </div>

      {/* Status Banner */}
      <div className="mb-6">
        <Tag color={reportData.status === 'completed' ? 'green' : 'blue'} className="px-4 py-2 text-sm">
          {reportData.status === 'completed' ? '✓ 完成' : '運行中'}
        </Tag>
      </div>

      {/* Performance Metrics */}
      <Row gutter={[16, 16]} className="mb-6">
        {metricCards.map((metric, index) => {
          const Icon = metric.icon;
          return (
            <Col xs={24} sm={12} lg={6} key={index}>
              <Card>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">{metric.title}</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {metric.value}
                    </p>
                  </div>
                  <div className={`p-3 rounded-lg bg-${metric.color}-100 dark:bg-${metric.color}-900`}>
                    <Icon className={`h-6 w-6 text-${metric.color}-600 dark:text-${metric.color}-400`} />
                  </div>
                </div>
              </Card>
            </Col>
          );
        })}
      </Row>

      {/* Detailed Metrics */}
      <Card className="mb-6" title="詳細指標">
        <Row gutter={[16, 16]}>
          <Col xs={12} sm={8}>
            <div className="text-center">
              <p className="text-sm text-gray-500 dark:text-gray-400">年化回報</p>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                {reportData.performance.annual_return.toFixed(2)}%
              </p>
            </div>
          </Col>
          <Col xs={12} sm={8}>
            <div className="text-center">
              <p className="text-sm text-gray-500 dark:text-gray-400">索提諾比率</p>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                {reportData.performance.sortino_ratio.toFixed(2)}
              </p>
            </div>
          </Col>
          <Col xs={12} sm={8}>
            <div className="text-center">
              <p className="text-sm text-gray-500 dark:text-gray-400">盈利因子</p>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                {reportData.performance.profit_factor.toFixed(2)}
              </p>
            </div>
          </Col>
          <Col xs={12} sm={8}>
            <div className="text-center">
              <p className="text-sm text-gray-500 dark:text-gray-400">平均交易</p>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                ${reportData.performance.avg_trade.toFixed(2)}
              </p>
            </div>
          </Col>
          <Col xs={12} sm={8}>
            <div className="text-center">
              <p className="text-sm text-gray-500 dark:text-gray-400">盈利交易</p>
              <p className="text-lg font-semibold text-green-600">
                {reportData.performance.profitable_trades}
              </p>
            </div>
          </Col>
          <Col xs={12} sm={8}>
            <div className="text-center">
              <p className="text-sm text-gray-500 dark:text-gray-400">虧損交易</p>
              <p className="text-lg font-semibold text-red-600">
                {reportData.performance.losing_trades}
              </p>
            </div>
          </Col>
        </Row>
      </Card>

      {/* Tabs for Charts and Trades */}
      <Card>
        <Tabs defaultActiveKey="equity">
          <TabPane tab="資金曲線" key="equity">
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={reportData.equity_curve}>
                  <defs>
                    <linearGradient id="colorEquity" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="equity"
                    stroke="#3b82f6"
                    fillOpacity={1}
                    fill="url(#colorEquity)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </TabPane>

          <TabPane tab="回撤分析" key="drawdown">
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={reportData.equity_curve}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="drawdown"
                    stroke="#ef4444"
                    fill="#ef4444"
                    fillOpacity={0.3}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </TabPane>

          <TabPane tab="交易記錄" key="trades">
            <Table
              columns={tradeColumns}
              dataSource={reportData.trades}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              scroll={{ x: 1000 }}
            />
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default BacktestReport;

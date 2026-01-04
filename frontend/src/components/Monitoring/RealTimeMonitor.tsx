/**
 * Real-Time Monitor Component
 * Live monitoring dashboard for trading activities
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion } from 'framer-motion';
import { Card, Row, Col, Table, Tag, Space, Button, Select, Badge, Tooltip } from 'antd';
import {
  Activity,
  TrendingUp,
  TrendingDown,
  Pause,
  Play,
  Maximize2,
  Download,
  Filter,
  RefreshCw,
} from 'lucide-react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
  Filler,
} from 'chart.js';

import { wsManager } from '../../services/websocketManager';
import { apiClient } from '../../services/apiClient';

import './RealTimeMonitor.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  ChartTooltip,
  Legend,
  Filler
);

const { Option } = Select;

// Trading activity interface
interface TradingActivity {
  id: string;
  timestamp: string;
  strategy: string;
  symbol: string;
  type: 'buy' | 'sell' | 'signal';
  price: number;
  quantity: number;
  value: number;
  status: 'pending' | 'executed' | 'failed';
}

// Price data interface
interface PriceData {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  high: number;
  low: number;
  timestamp: string;
}

// Props interface
interface RealTimeMonitorProps {
  className?: string;
  symbols?: string[];
  maxDataPoints?: number;
}

/**
 * RealTimeMonitor Component
 */
export const RealTimeMonitor: React.FC<RealTimeMonitorProps> = ({
  className = '',
  symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA'],
  maxDataPoints = 100,
}) => {
  // State management
  const [isMonitoring, setIsMonitoring] = useState(true);
  const [selectedSymbol, setSelectedSymbol] = useState(symbols[0]);
  const [priceData, setPriceData] = useState<Record<string, PriceData[]>>({});
  const [activities, setActivities] = useState<TradingActivity[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting');
  const [filterType, setFilterType] = useState<'all' | 'buy' | 'sell' | 'signal'>('all');
  const updateTimerRef = useRef<NodeJS.Timeout | null>(null);

  /**
   * Initialize WebSocket connection
   */
  useEffect(() => {
    const connectWebSocket = async () => {
      try {
        await wsManager.connect();
        setConnectionStatus('connected');

        // Subscribe to price updates
        const unsubscribePrices = wsManager.subscribe('price_update', (data) => {
          handlePriceUpdate(data);
        });

        // Subscribe to trading signals
        const unsubscribeSignals = wsManager.subscribe('trading_signal', (data) => {
          handleTradingSignal(data);
        });

        // Subscribe to order updates
        const unsubscribeOrders = wsManager.subscribe('order_update', (data) => {
          handleOrderUpdate(data);
        });

        return () => {
          unsubscribePrices();
          unsubscribeSignals();
          unsubscribeOrders();
        };
      } catch (error) {
        console.error('WebSocket connection failed:', error);
        setConnectionStatus('disconnected');
      }
    };

    const cleanup = connectWebSocket();

    return () => {
      cleanup.then((unsub) => unsub && unsub());
    };
  }, [symbols]);

  /**
   * Handle price updates
   */
  const handlePriceUpdate = useCallback((data: any) => {
    const { symbol, price, change, volume, high, low } = data;

    setPriceData((prev) => {
      const symbolData = prev[symbol] || [];
      const newDataPoint: PriceData = {
        symbol,
        price,
        change: change || 0,
        changePercent: ((change || 0) / price) * 100,
        volume: volume || 0,
        high: high || price,
        low: low || price,
        timestamp: new Date().toISOString(),
      };

      const updated = [...symbolData, newDataPoint].slice(-maxDataPoints);
      return {
        ...prev,
        [symbol]: updated,
      };
    });
  }, [maxDataPoints]);

  /**
   * Handle trading signals
   */
  const handleTradingSignal = useCallback((data: any) => {
    const activity: TradingActivity = {
      id: `signal-${Date.now()}-${Math.random()}`,
      timestamp: new Date().toISOString(),
      strategy: data.strategyName || 'Unknown',
      symbol: data.symbol,
      type: 'signal',
      price: data.price || 0,
      quantity: 0,
      value: 0,
      status: 'pending',
    };

    setActivities((prev) => [activity, ...prev].slice(0, 50));
  }, []);

  /**
   * Handle order updates
   */
  const handleOrderUpdate = useCallback((data: any) => {
    const activity: TradingActivity = {
      id: data.orderId || `order-${Date.now()}`,
      timestamp: data.timestamp || new Date().toISOString(),
      strategy: data.strategyName || 'Unknown',
      symbol: data.symbol,
      type: data.side === 'buy' ? 'buy' : 'sell',
      price: data.price || 0,
      quantity: data.quantity || 0,
      value: (data.price || 0) * (data.quantity || 0),
      status: data.status || 'executed',
    };

    setActivities((prev) => [activity, ...prev].slice(0, 50));
  }, []);

  /**
   * Toggle monitoring
   */
  const toggleMonitoring = () => {
    setIsMonitoring((prev) => !prev);
  };

  /**
   * Fetch initial price data
   */
  const fetchInitialPrices = useCallback(async () => {
    try {
      const response = await apiClient.get('/market/prices', {
        params: { symbols: symbols.join(',') },
      });

      const initialData: Record<string, PriceData[]> = {};
      Object.entries(response.data.prices || {}).forEach(([symbol, priceInfo]: [string, any]) => {
        initialData[symbol] = [{
          symbol,
          price: priceInfo.price,
          change: priceInfo.change || 0,
          changePercent: priceInfo.changePercent || 0,
          volume: priceInfo.volume || 0,
          high: priceInfo.high || priceInfo.price,
          low: priceInfo.low || priceInfo.price,
          timestamp: new Date().toISOString(),
        }];
      });

      setPriceData(initialData);
    } catch (error) {
      console.error('Failed to fetch initial prices:', error);
    }
  }, [symbols]);

  useEffect(() => {
    fetchInitialPrices();
  }, [fetchInitialPrices]);

  /**
   * Get current price for symbol
   */
  const getCurrentPrice = (symbol: string): PriceData | null => {
    const data = priceData[symbol];
    return data && data.length > 0 ? data[data.length - 1] : null;
  };

  /**
   * Render price card
   */
  const renderPriceCard = (symbol: string) => {
    const current = getCurrentPrice(symbol);
    if (!current) return null;

    const isPositive = current.changePercent >= 0;

    return (
      <Col xs={12} sm={8} md={6} lg={4} key={symbol}>
        <Card
          size="small"
          className={`price-card ${selectedSymbol === symbol ? 'selected' : ''}`}
          hoverable
          onClick={() => setSelectedSymbol(symbol)}
        >
          <div className="text-center">
            <div className="text-lg font-bold mb-1">{symbol}</div>
            <div className="text-2xl font-bold mb-1">
              ${current.price.toFixed(2)}
            </div>
            <div className={`flex items-center justify-center gap-1 text-sm ${
              isPositive ? 'text-green-600' : 'text-red-600'
            }`}>
              {isPositive ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
              <span>{isPositive ? '+' : ''}{current.changePercent.toFixed(2)}%</span>
            </div>
            <div className="text-xs text-gray-500 mt-1">
              Vol: {current.volume.toLocaleString()}
            </div>
          </div>
        </Card>
      </Col>
    );
  };

  /**
   * Render price chart
   */
  const renderPriceChart = () => {
    const data = priceData[selectedSymbol] || [];
    if (data.length < 2) {
      return (
        <div className="flex items-center justify-center h-64 text-gray-400">
          暫無價格數據
        </div>
      );
    }

    const chartData = {
      labels: data.map((d) => new Date(d.timestamp).toLocaleTimeString('zh-TW')),
      datasets: [
        {
          label: `${selectedSymbol} 價格`,
          data: data.map((d) => d.price),
          borderColor: data[data.length - 1].changePercent >= 0 ? 'rgb(34, 197, 94)' : 'rgb(239, 68, 68)',
          backgroundColor: data[data.length - 1].changePercent >= 0
            ? 'rgba(34, 197, 94, 0.1)'
            : 'rgba(239, 68, 68, 0.1)',
          fill: true,
          tension: 0.4,
          pointRadius: 0,
          pointHoverRadius: 6,
        },
      ],
    };

    const options = {
      responsive: true,
      maintainAspectRatio: false,
      animation: {
        duration: 0,
      },
      plugins: {
        legend: {
          display: false,
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
            callback: (value: any) => `$${value.toFixed(2)}`,
          },
        },
        x: {
          display: true,
          ticks: {
            maxTicksLimit: 10,
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
   * Get filtered activities
   */
  const getFilteredActivities = () => {
    if (filterType === 'all') return activities;
    return activities.filter((a) => a.type === filterType);
  };

  /**
   * Activity table columns
   */
  const activityColumns = [
    {
      title: '時間',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 150,
      render: (timestamp: string) => new Date(timestamp).toLocaleTimeString('zh-TW'),
    },
    {
      title: '策略',
      dataIndex: 'strategy',
      key: 'strategy',
      ellipsis: true,
    },
    {
      title: '股票',
      dataIndex: 'symbol',
      key: 'symbol',
      render: (symbol: string) => <Tag color="blue">{symbol}</Tag>,
    },
    {
      title: '類型',
      dataIndex: 'type',
      key: 'type',
      width: 80,
      render: (type: string) => {
        const config = {
          buy: { color: 'green', text: '買入' },
          sell: { color: 'red', text: '賣出' },
          signal: { color: 'blue', text: '信號' },
        };
        const { color, text } = config[type as keyof typeof config];
        return <Tag color={color}>{text}</Tag>;
      },
    },
    {
      title: '價格',
      dataIndex: 'price',
      key: 'price',
      width: 100,
      align: 'right' as const,
      render: (price: number) => (price > 0 ? `$${price.toFixed(2)}` : '-'),
    },
    {
      title: '數量',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 100,
      align: 'right' as const,
      render: (quantity: number) => (quantity > 0 ? quantity.toLocaleString() : '-'),
    },
    {
      title: '狀態',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const config = {
          pending: { color: 'orange', text: '待執行' },
          executed: { color: 'green', text: '已執行' },
          failed: { color: 'red', text: '失敗' },
        };
        const { color, text } = config[status as keyof typeof config];
        return <Tag color={color}>{text}</Tag>;
      },
    },
  ];

  /**
   * Handle export
   */
  const handleExport = async () => {
    try {
      const response = await apiClient.get('/monitoring/export', {
        params: { symbol: selectedSymbol },
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `monitoring-${selectedSymbol}-${new Date().toISOString()}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Failed to export data:', error);
    }
  };

  return (
    <div className={`realtime-monitor ${className}`}>
      {/* Header */}
      <Card className="monitor-header mb-4">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-4">
            <h2 className="text-xl font-bold">實時監控</h2>
            <Badge
              status={connectionStatus === 'connected' ? 'processing' : 'error'}
              text={connectionStatus === 'connected' ? '已連接' : connectionStatus === 'connecting' ? '連接中' : '未連接'}
            />
          </div>

          <Space>
            <Select
              value={filterType}
              onChange={setFilterType}
              className="w-32"
              size="large"
            >
              <Option value="all">全部活動</Option>
              <Option value="buy">買入</Option>
              <Option value="sell">賣出</Option>
              <Option value="signal">信號</Option>
            </Select>

            <Button
              icon={isMonitoring ? <Pause size={16} /> : <Play size={16} />}
              onClick={toggleMonitoring}
              type={isMonitoring ? 'default' : 'primary'}
            >
              {isMonitoring ? '暫停' : '繼續'}
            </Button>

            <Button
              icon={<RefreshCw size={16} />}
              onClick={fetchInitialPrices}
            >
              刷新
            </Button>

            <Tooltip title="導出數據">
              <Button
                icon={<Download size={16} />}
                onClick={handleExport}
              />
            </Tooltip>
          </Space>
        </div>
      </Card>

      {/* Price Cards */}
      <Row gutter={[12, 12]} className="mb-4">
        {symbols.map(renderPriceCard)}
      </Row>

      {/* Price Chart and Activities */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <Card
            title={`${selectedSymbol} 價格走勢`}
            className="chart-card"
          >
            <div className="h-80">
              {renderPriceChart()}
            </div>
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <Card
            title="交易活動"
            className="activity-card"
            bodyStyle={{ padding: 0 }}
          >
            <Table
              columns={activityColumns}
              dataSource={getFilteredActivities()}
              rowKey="id"
              size="small"
              pagination={false}
              scroll={{ y: 300 }}
              className="activity-table"
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default RealTimeMonitor;

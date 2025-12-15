import React, { useState, useEffect } from 'react';
import { Card, Statistic, Row, Col, Tag, Tooltip, Switch } from 'antd';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Area, AreaChart } from 'recharts';
import {
  TrendingUpOutlined,
  TrendingDownOutlined,
  MinusOutlined,
  InfoCircleOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { nonPriceService } from '../../Common/NonPriceDataProvider';

interface HIBORData {
  timestamp: string;
  rate: number;
  change: number;
  trend: 'UP' | 'DOWN' | 'STABLE';
}

interface HIBORDisplayProps {
  symbol?: string;
  timeframe?: '1D' | '1W' | '1M' | '3M';
  showRealTime?: boolean;
  height?: number;
}

const HIBORDisplay: React.FC<HIBORDisplayProps> = ({
  symbol = 'HIBOR',
  timeframe = '1M',
  showRealTime = true,
  height = 300
}) => {
  const [data, setData] = useState<HIBORData[]>([]);
  const [currentRate, setCurrentRate] = useState<number>(0);
  const [change, setChange] = useState<number>(0);
  const [trend, setTrend] = useState<'UP' | 'DOWN' | 'STABLE'>('STABLE');
  const [loading, setLoading] = useState<boolean>(true);
  const [autoRefresh, setAutoRefresh] = useState<boolean>(true);

  // 生成模擬HIBOR數據
  const generateMockData = () => {
    setLoading(true);

    const now = new Date();
    const periods = timeframe === '1D' ? 24 : timeframe === '1W' ? 7 : timeframe === '1M' ? 30 : 90;
    const interval = timeframe === '1D' ? 'hour' : 'day';

    const mockData: HIBORData[] = [];
    let baseRate = 5.5 + Math.random() * 0.5; // 基準利率 5.5-6.0%

    for (let i = periods; i >= 0; i--) {
      const timestamp = new Date(now);

      if (interval === 'hour') {
        timestamp.setHours(timestamp.getHours() - i);
      } else {
        timestamp.setDate(timestamp.getDate() - i);
      }

      // 添加隨機波動
      const volatility = 0.05; // 0.05% 標準差
      baseRate = baseRate + (Math.random() - 0.5) * volatility;
      baseRate = Math.max(5.0, Math.min(6.5, baseRate)); // 限制在 5.0-6.5%

      const rate = parseFloat(baseRate.toFixed(2));
      const prevRate = mockData.length > 0 ? mockData[mockData.length - 1].rate : rate;
      const change = rate - prevRate;

      let trend: 'UP' | 'DOWN' | 'STABLE';
      if (change > 0.01) {
        trend = 'UP';
      } else if (change < -0.01) {
        trend = 'DOWN';
      } else {
        trend = 'STABLE';
      }

      mockData.push({
        timestamp: timestamp.toISOString(),
        rate,
        change: parseFloat(change.toFixed(2)),
        trend
      });
    }

    // 設置當前值
    const latest = mockData[mockData.length - 1];
    setCurrentRate(latest.rate);
    setChange(latest.change);
    setTrend(latest.trend);
    setData(mockData);

    setLoading(false);
  };

  useEffect(() => {
    generateMockData();

    if (autoRefresh && showRealTime) {
      const interval = setInterval(generateMockData, 60000); // 每分鐘更新
      return () => clearInterval(interval);
    }
  }, [timeframe, autoRefresh, showRealTime]);

  // 獲取趨勢顏色
  const getTrendColor = (trend: 'UP' | 'DOWN' | 'STABLE') => {
    switch (trend) {
      case 'UP': return '#f5222d';
      case 'DOWN': return '#52c41a';
      default: return '#1890ff';
    }
  };

  // 獲取趨勢圖標
  const getTrendIcon = (trend: 'UP' | 'DOWN' | 'STABLE') => {
    switch (trend) {
      case 'UP': return <TrendingUpOutlined />;
      case 'DOWN': return <TrendingDownOutlined />;
      default: return <MinusOutlined />;
    }
  };

  // 獲取趨勢標籤
  const getTrendTag = (trend: 'UP' | 'DOWN' | 'STABLE') => {
    const colors = {
      'UP': 'red',
      'DOWN': 'green',
      'STABLE': 'blue'
    };

    const labels = {
      'UP': '上升',
      'DOWN': '下降',
      'STABLE': '穩定'
    };

    return (
      <Tag color={colors[trend]}>
        {getTrendIcon(trend)} {labels[trend]}
      </Tag>
    );
  };

  // 格式化時間戳
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    if (timeframe === '1D') {
      return date.toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' });
    } else {
      return date.toLocaleDateString('zh-TW', { month: '2-digit', day: '2-digit' });
    }
  };

  return (
    <Card
      title={
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span>HIBOR 利率</span>
            <Tooltip title="香港銀行同業拆息利率">
              <InfoCircleOutlined className="text-gray-400" />
            </Tooltip>
          </div>
          <div className="flex items-center gap-4">
            <Switch
              checked={autoRefresh}
              onChange={setAutoRefresh}
              size="small"
              checkedChildren="自動"
              unCheckedChildren="手動"
            />
            <Tooltip title="刷新數據">
              <ReloadOutlined
                onClick={generateMockData}
                className="cursor-pointer hover:text-blue-500"
              />
            </Tooltip>
          </div>
        </div>
      }
      className="hibor-display"
    >
      {/* 當前利率顯示 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Statistic
            title="當前利率"
            value={currentRate}
            precision={2}
            suffix="%"
            valueStyle={{
              color: getTrendColor(trend),
              fontSize: '28px',
              fontWeight: 'bold'
            }}
          />
        </Col>
        <Col span={8}>
          <Statistic
            title="變動"
            value={change}
            precision={2}
            suffix="%"
            valueStyle={{
              color: change > 0 ? '#f5222d' : change < 0 ? '#52c41a' : '#1890ff',
              fontSize: '20px'
            }}
            prefix={change > 0 ? '+' : ''}
          />
        </Col>
        <Col span={8}>
          <div className="text-center">
            <div className="text-gray-500 mb-2">趨勢狀態</div>
            {getTrendTag(trend)}
          </div>
        </Col>
      </Row>

      {/* 圖表 */}
      <div style={{ height: height }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id="colorRate" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#1890ff" stopOpacity={0.8}/>
                <stop offset="95%" stopColor="#1890ff" stopOpacity={0.1}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              dataKey="timestamp"
              tickFormatter={formatTimestamp}
              tick={{ fontSize: 12 }}
            />
            <YAxis
              domain={['dataMin - 0.1', 'dataMax + 0.1']}
              tickFormatter={(value) => `${value}%`}
              tick={{ fontSize: 12 }}
            />
            <Tooltip
              formatter={(value: any, name: string) => [
                `${value}%`,
                'HIBOR利率'
              ]}
              labelFormatter={(label) => {
                const date = new Date(label);
                return date.toLocaleString('zh-TW');
              }}
              contentStyle={{
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                border: '1px solid #d9d9d9',
                borderRadius: '6px'
              }}
            />
            <Area
              type="monotone"
              dataKey="rate"
              stroke="#1890ff"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorRate)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* 統計信息 */}
      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={6}>
          <div className="text-center">
            <div className="text-gray-500 text-sm">最高值</div>
            <div className="text-lg font-semibold text-red-500">
              {Math.max(...data.map(d => d.rate)).toFixed(2)}%
            </div>
          </div>
        </Col>
        <Col span={6}>
          <div className="text-center">
            <div className="text-gray-500 text-sm">最低值</div>
            <div className="text-lg font-semibold text-green-500">
              {Math.min(...data.map(d => d.rate)).toFixed(2)}%
            </div>
          </div>
        </Col>
        <Col span={6}>
          <div className="text-center">
            <div className="text-gray-500 text-sm">平均值</div>
            <div className="text-lg font-semibold text-blue-500">
              {(data.reduce((sum, d) => sum + d.rate, 0) / data.length).toFixed(2)}%
            </div>
          </div>
        </Col>
        <Col span={6}>
          <div className="text-center">
            <div className="text-gray-500 text-sm">波動率</div>
            <div className="text-lg font-semibold text-orange-500">
              {data.length > 1 ?
                (Math.sqrt(data.reduce((sum, d) => sum + Math.pow(d.rate - (data.reduce((s, x) => s + x.rate, 0) / data.length), 2), 0) / data.length) * 100).toFixed(2)
                : '0.00'}%
            </div>
          </div>
        </Col>
      </Row>

      {/* 更新時間 */}
      <div className="text-center text-gray-400 text-xs mt-4">
        最後更新: {new Date().toLocaleString('zh-TW')}
      </div>
    </Card>
  );
};

export default HIBORDisplay;
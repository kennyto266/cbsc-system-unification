import React, { useState, useEffect } from 'react';
import { Card, Statistic, Row, Col, Tag, Tooltip, Select, Switch } from 'antd';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, ResponsiveContainer, BarChart, Bar } from 'recharts';
import {
  DollarCircleOutlined,
  InfoCircleOutlined,
  ReloadOutlined,
  TrendingUpOutlined,
  TrendingDownOutlined
} from '@ant-design/icons';
import { nonPriceService } from '../../Common/NonPriceDataProvider';

interface MonetaryBaseData {
  timestamp: string;
  value: number;
  change: number;
  trend: 'UP' | 'DOWN' | 'STABLE';
}

interface MonetaryBaseChartProps {
  timeframe?: '1W' | '1M' | '3M' | '6M' | '1Y';
  showComparison?: boolean;
  showRealTime?: boolean;
  height?: number;
}

const MonetaryBaseChart: React.FC<MonetaryBaseChartProps> = ({
  timeframe = '3M',
  showComparison = false,
  showRealTime = true,
  height = 350
}) => {
  const [data, setData] = useState<MonetaryBaseData[]>([]);
  const [currentValue, setCurrentValue] = useState<number>(0);
  const [change, setChange] = useState<number>(0);
  const [changePercent, setChangePercent] = useState<number>(0);
  const [trend, setTrend] = useState<'UP' | 'DOWN' | 'STABLE'>('STABLE');
  const [loading, setLoading] = useState<boolean>(true);
  const [chartType, setChartType] = useState<'area' | 'bar'>('area');
  const [autoRefresh, setAutoRefresh] = useState<boolean>(true);

  // 生成模擬貨幣基礎數據
  const generateMockData = () => {
    setLoading(true);

    const now = new Date();
    const periods = timeframe === '1W' ? 7 : timeframe === '1M' ? 30 : timeframe === '3M' ? 90 : timeframe === '6M' ? 180 : 365;

    const mockData: MonetaryBaseData[] = [];
    let baseValue = 1850 + Math.random() * 50; // 基準值 1850-1900 (億港元)

    for (let i = periods; i >= 0; i--) {
      const timestamp = new Date(now);
      timestamp.setDate(timestamp.getDate() - i);

      // 添加市場波動和趨勢
      const trendFactor = 0.5 + (periods - i) * 0.01; // 隨時間增長的趨勢因子
      const volatility = 10 + Math.random() * 20; // 10-30 億的波動
      baseValue = baseValue + (Math.random() - 0.3) * volatility * trendFactor;
      baseValue = Math.max(1750, Math.min(2000, baseValue)); // 限制在合理範圍

      const value = parseFloat(baseValue.toFixed(2));
      const prevValue = mockData.length > 0 ? mockData[mockData.length - 1].value : value;
      const change = value - prevValue;
      const changePercent = (change / prevValue) * 100;

      let trend: 'UP' | 'DOWN' | 'STABLE';
      if (change > 2) {
        trend = 'UP';
      } else if (change < -2) {
        trend = 'DOWN';
      } else {
        trend = 'STABLE';
      }

      mockData.push({
        timestamp: timestamp.toISOString(),
        value,
        change: parseFloat(change.toFixed(2)),
        trend
      });
    }

    // 設置當前值
    const latest = mockData[mockData.length - 1];
    const first = mockData[0];
    setCurrentValue(latest.value);
    setChange(latest.value - first.value);
    setChangePercent(((latest.value - first.value) / first.value) * 100);
    setTrend(latest.trend);
    setData(mockData);

    setLoading(false);
  };

  useEffect(() => {
    generateMockData();

    if (autoRefresh && showRealTime) {
      const interval = setInterval(generateMockData, 120000); // 每2分鐘更新
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

  // 獲取變動顏色
  const getChangeColor = (change: number) => {
    return change > 0 ? '#f5222d' : change < 0 ? '#52c41a' : '#1890ff';
  };

  // 格式化時間戳
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    if (timeframe === '1W') {
      return date.toLocaleDateString('zh-TW', { month: '2-digit', day: '2-digit' });
    } else {
      return date.toLocaleDateString('zh-TW', { month: '2-digit', day: '2-digit' });
    }
  };

  // 格式化大數字
  const formatLargeNumber = (value: number) => {
    if (value >= 1000) {
      return `${(value / 1000).toFixed(2)}K`;
    }
    return value.toFixed(2);
  };

  return (
    <Card
      title={
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <DollarCircleOutlined />
            <span>香港貨幣基礎</span>
            <Tooltip title="香港金管局貨幣基礎總額 (億港元)">
              <InfoCircleOutlined className="text-gray-400" />
            </Tooltip>
          </div>
          <div className="flex items-center gap-4">
            <Select
              value={chartType}
              onChange={setChartType}
              size="small"
              style={{ width: 80 }}
            >
              <Select.Option value="area">面積</Select.Option>
              <Select.Option value="bar">柱狀</Select.Option>
            </Select>
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
      className="monetary-base-chart"
    >
      {/* 統計信息 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Statistic
            title="當前值"
            value={currentValue}
            precision={2}
            suffix="億港元"
            valueStyle={{ fontSize: '24px', fontWeight: 'bold' }}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="總變動"
            value={change}
            precision={2}
            suffix="億港元"
            valueStyle={{
              color: getChangeColor(change),
              fontSize: '20px'
            }}
            prefix={change > 0 ? <TrendingUpOutlined /> : change < 0 ? <TrendingDownOutlined /> : null}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="變動百分比"
            value={changePercent}
            precision={2}
            suffix="%"
            valueStyle={{
              color: getChangeColor(changePercent),
              fontSize: '20px'
            }}
            prefix={changePercent > 0 ? '+' : ''}
          />
        </Col>
        <Col span={6}>
          <div className="text-center">
            <div className="text-gray-500 mb-2">趨勢狀態</div>
            <Tag color={trend === 'UP' ? 'red' : trend === 'DOWN' ? 'green' : 'blue'}>
              {trend === 'UP' ? '上升' : trend === 'DOWN' ? '下降' : '穩定'}
            </Tag>
          </div>
        </Col>
      </Row>

      {/* 圖表 */}
      <div style={{ height: height }}>
        <ResponsiveContainer width="100%" height="100%">
          {chartType === 'area' ? (
            <AreaChart data={data}>
              <defs>
                <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#52c41a" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#52c41a" stopOpacity={0.1}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis
                dataKey="timestamp"
                tickFormatter={formatTimestamp}
                tick={{ fontSize: 12 }}
              />
              <YAxis
                domain={['dataMin - 20', 'dataMax + 20']}
                tickFormatter={(value) => formatLargeNumber(value)}
                tick={{ fontSize: 12 }}
              />
              <Tooltip
                formatter={(value: any, name: string) => [
                  `${parseFloat(value).toFixed(2)} 億港元`,
                  '貨幣基礎'
                ]}
                labelFormatter={(label) => {
                  const date = new Date(label);
                  return date.toLocaleDateString('zh-TW');
                }}
                contentStyle={{
                  backgroundColor: 'rgba(255, 255, 255, 0.95)',
                  border: '1px solid #d9d9d9',
                  borderRadius: '6px'
                }}
              />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#52c41a"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#colorValue)"
              />
            </AreaChart>
          ) : (
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis
                dataKey="timestamp"
                tickFormatter={formatTimestamp}
                tick={{ fontSize: 12 }}
              />
              <YAxis
                domain={['dataMin - 20', 'dataMax + 20']}
                tickFormatter={(value) => formatLargeNumber(value)}
                tick={{ fontSize: 12 }}
              />
              <Tooltip
                formatter={(value: any, name: string) => [
                  `${parseFloat(value).toFixed(2)} 億港元`,
                  '貨幣基礎'
                ]}
                labelFormatter={(label) => {
                  const date = new Date(label);
                  return date.toLocaleDateString('zh-TW');
                }}
                contentStyle={{
                  backgroundColor: 'rgba(255, 255, 255, 0.95)',
                  border: '1px solid #d9d9d9',
                  borderRadius: '6px'
                }}
              />
              <Bar
                dataKey="value"
                fill="#52c41a"
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>

      {/* 統計摘要 */}
      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={8}>
          <div className="text-center p-3 bg-gray-50 rounded">
            <div className="text-gray-500 text-sm">期間最高</div>
            <div className="text-xl font-semibold text-red-500">
              {formatLargeNumber(Math.max(...data.map(d => d.value)))} 億
            </div>
          </div>
        </Col>
        <Col span={8}>
          <div className="text-center p-3 bg-gray-50 rounded">
            <div className="text-gray-500 text-sm">期間最低</div>
            <div className="text-xl font-semibold text-green-500">
              {formatLargeNumber(Math.min(...data.map(d => d.value)))} 億
            </div>
          </div>
        </Col>
        <Col span={8}>
          <div className="text-center p-3 bg-gray-50 rounded">
            <div className="text-gray-500 text-sm">期間平均</div>
            <div className="text-xl font-semibold text-blue-500">
              {formatLargeNumber(data.reduce((sum, d) => sum + d.value, 0) / data.length)} 億
            </div>
          </div>
        </Col>
      </Row>

      {/* 市場分析 */}
      <div className="mt-4 p-3 bg-blue-50 rounded">
        <div className="text-sm text-gray-700">
          <p className="mb-1">
            <strong>市場分析:</strong>
            {changePercent > 2 ? ' 貨幣基礎顯著增加，流動性充裕' :
             changePercent < -2 ? ' 貨幣基礎收縮，流動性趨緊' :
             ' 貨幣基礎保持穩定'}
          </p>
          <p className="text-xs text-gray-500">
            * 貨幣基礎是衡量市場流動性的重要指標，影響銀行間利率和資產價格
          </p>
        </div>
      </div>

      {/* 更新時間 */}
      <div className="text-center text-gray-400 text-xs mt-3">
        最後更新: {new Date().toLocaleString('zh-TW')}
      </div>
    </Card>
  );
};

export default MonetaryBaseChart;
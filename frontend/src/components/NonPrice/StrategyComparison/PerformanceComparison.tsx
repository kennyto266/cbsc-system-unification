import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Select, Switch, Button, Tag, Tooltip } from 'antd';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ScatterChart,
  Scatter
} from 'recharts';
import {
  TrophyOutlined,
  LineChartOutlined,
  ReloadOutlined,
  SettingOutlined,
  InfoCircleOutlined,
  ThunderboltOutlined
} from '@ant-design/icons';
import { nonPriceService, StrategyPerformance } from '../Common/NonPriceDataProvider';

interface PerformanceComparisonProps {
  defaultPeriod?: string;
  showSettings?: boolean;
  height?: number;
}

const PerformanceComparison: React.FC<PerformanceComparisonProps> = ({
  defaultPeriod = '3M',
  showSettings = true,
  height = 400
}) => {
  const [performanceData, setPerformanceData] = useState<StrategyPerformance[]>([]);
  const [selectedPeriod, setSelectedPeriod] = useState<string>(defaultPeriod);
  const [chartType, setChartType] = useState<'bar' | 'radar' | 'scatter'>('bar');
  const [showDetails, setShowDetails] = useState<boolean>(true);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>(['totalReturn', 'sharpeRatio', 'winRate']);

  // 獲取策略性能數據
  const fetchPerformanceData = async () => {
    setLoading(true);

    try {
      const data = await nonPriceService.getStrategyPerformance(selectedPeriod);
      setPerformanceData(data);
    } catch (error) {
      console.error('Failed to fetch performance data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPerformanceData();
  }, [selectedPeriod]);

  // 準備柱狀圖數據
  const prepareBarChartData = () => {
    return performanceData.map(strategy => ({
      name: strategy.name,
      totalReturn: (strategy.totalReturn * 100).toFixed(2),
      sharpeRatio: strategy.sharpeRatio.toFixed(2),
      winRate: (strategy.winRate * 100).toFixed(2),
      maxDrawdown: (strategy.maxDrawdown * 100).toFixed(2),
      volatility: (strategy.volatility * 100).toFixed(2),
      alpha: (strategy.alpha * 100).toFixed(2),
      beta: strategy.beta.toFixed(2)
    }));
  };

  // 準備雷達圖數據
  const prepareRadarData = () => {
    const metrics = ['總收益', '夏普比率', '勝率', '最大回撤', '穩定性', 'Alpha'];

    return metrics.map(metric => {
      const dataPoint: any = { metric };

      performanceData.forEach(strategy => {
        switch (metric) {
          case '總收益':
            dataPoint[strategy.name] = (strategy.totalReturn * 100).toFixed(1);
            break;
          case '夏普比率':
            dataPoint[strategy.name] = (strategy.sharpeRatio * 20).toFixed(1); // 縮放以適應雷達圖
            break;
          case '勝率':
            dataPoint[strategy.name] = (strategy.winRate * 100).toFixed(1);
            break;
          case '最大回撤':
            dataPoint[strategy.name] = ((1 - strategy.maxDrawdown) * 100).toFixed(1); // 反向指標
            break;
          case '穩定性':
            dataPoint[strategy.name] = ((1 - strategy.volatility) * 100).toFixed(1); // 反向指標
            break;
          case 'Alpha':
            dataPoint[strategy.name] = (strategy.alpha * 100).toFixed(1);
            break;
        }
      });

      return dataPoint;
    });
  };

  // 準備散點圖數據 (風險vs回報)
  const prepareScatterData = () => {
    return performanceData.map(strategy => ({
      name: strategy.name,
      risk: strategy.volatility * 100,
      return: strategy.totalReturn * 100,
      sharpe: strategy.sharpeRatio,
      type: strategy.type,
      color: strategy.type === 'price' ? '#1890ff' :
             strategy.type === 'non-price' ? '#52c41a' : '#fa8c16'
    }));
  };

  // 獲取策略類型標籤
  const getStrategyTypeTag = (type: string) => {
    const colors = {
      'price': 'blue',
      'non-price': 'green',
      'combined': 'orange'
    };

    const labels = {
      'price': '價格策略',
      'non-price': '非價格策略',
      'combined': '組合策略'
    };

    return (
      <Tag color={colors[type as keyof typeof colors]}>
        {labels[type as keyof typeof labels]}
      </Tag>
    );
  };

  // 格式化百分比
  const formatPercent = (value: number | string, decimals: number = 2) => {
    const num = typeof value === 'string' ? parseFloat(value) : value;
    return `${num.toFixed(decimals)}%`;
  };

  const barChartData = prepareBarChartData();
  const radarData = prepareRadarData();
  const scatterData = prepareScatterData();

  return (
    <Card
      title={
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <TrophyOutlined />
            <span>策略性能比較</span>
            <Tooltip title="比較不同策略類型的關鍵性能指標">
              <InfoCircleOutlined className="text-gray-400" />
            </Tooltip>
          </div>
          <div className="flex items-center gap-3">
            <Select
              value={chartType}
              onChange={setChartType}
              size="small"
              style={{ width: 100 }}
            >
              <Select.Option value="bar">柱狀圖</Select.Option>
              <Select.Option value="radar">雷達圖</Select.Option>
              <Select.Option value="scatter">散點圖</Select.Option>
            </Select>
            <Select
              value={selectedPeriod}
              onChange={setSelectedPeriod}
              size="small"
              style={{ width: 80 }}
            >
              <Select.Option value="1M">1月</Select.Option>
              <Select.Option value="3M">3月</Select.Option>
              <Select.Option value="6M">6月</Select.Option>
              <Select.Option value="1Y">1年</Select.Option>
            </Select>
            <Tooltip title="刷新數據">
              <ReloadOutlined
                onClick={fetchPerformanceData}
                className="cursor-pointer hover:text-blue-500"
              />
            </Tooltip>
          </div>
        </div>
      }
      extra={
        showSettings && (
          <div className="flex items-center gap-2">
            <span className="text-sm">顯示詳情</span>
            <Switch
              checked={showDetails}
              onChange={setShowDetails}
              size="small"
            />
          </div>
        )
      }
      className="performance-comparison"
      loading={loading}
    >
      {/* 關鍵指標統計 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Statistic
            title="最佳總回報"
            value={Math.max(...performanceData.map(s => s.totalReturn)) * 100}
            precision={2}
            suffix="%"
            valueStyle={{ color: '#52c41a' }}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="最高夏普比率"
            value={Math.max(...performanceData.map(s => s.sharpeRatio))}
            precision={2}
            valueStyle={{ color: '#1890ff' }}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="最高勝率"
            value={Math.max(...performanceData.map(s => s.winRate)) * 100}
            precision={1}
            suffix="%"
            valueStyle={{ color: '#fa8c16' }}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="最低最大回撤"
            value={Math.min(...performanceData.map(s => s.maxDrawdown)) * 100}
            precision={2}
            suffix="%"
            valueStyle={{ color: '#f5222d' }}
            prefix="-"
          />
        </Col>
      </Row>

      {/* 圖表 */}
      <div style={{ height: height }}>
        <ResponsiveContainer width="100%" height="100%">
          {chartType === 'bar' ? (
            <BarChart data={barChartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip
                formatter={(value: any, name: string) => {
                  const labels: Record<string, string> = {
                    totalReturn: '總回報',
                    sharpeRatio: '夏普比率',
                    winRate: '勝率',
                    maxDrawdown: '最大回撤',
                    volatility: '波動率',
                    alpha: 'Alpha',
                    beta: 'Beta'
                  };
                  const suffix = ['totalReturn', 'winRate', 'maxDrawdown', 'volatility', 'alpha'].includes(name) ? '%' : '';
                  return [`${value}${suffix}`, labels[name] || name];
                }}
              />
              <Legend />
              {selectedMetrics.includes('totalReturn') && (
                <Bar dataKey="totalReturn" fill="#52c41a" name="總回報" />
              )}
              {selectedMetrics.includes('sharpeRatio') && (
                <Bar dataKey="sharpeRatio" fill="#1890ff" name="夏普比率" />
              )}
              {selectedMetrics.includes('winRate') && (
                <Bar dataKey="winRate" fill="#fa8c16" name="勝率" />
              )}
            </BarChart>
          ) : chartType === 'radar' ? (
            <RadarChart data={radarData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="metric" tick={{ fontSize: 11 }} />
              <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 10 }} />
              {performanceData.map((strategy, index) => (
                <Radar
                  key={strategy.name}
                  name={strategy.name}
                  dataKey={strategy.name}
                  stroke={['#1890ff', '#52c41a', '#fa8c16', '#722ed1'][index]}
                  fill={['#1890ff', '#52c41a', '#fa8c16', '#722ed1'][index]}
                  fillOpacity={0.3}
                />
              ))}
              <Legend />
              <Tooltip />
            </RadarChart>
          ) : (
            <ScatterChart data={scatterData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="risk"
                name="風險"
                unit="%"
                tick={{ fontSize: 11 }}
                label={{ value: '風險 (波動率 %)', position: 'insideBottom', offset: -10 }}
              />
              <YAxis
                dataKey="return"
                name="回報"
                unit="%"
                tick={{ fontSize: 11 }}
                label={{ value: '回報 (%)', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip
                cursor={{ strokeDasharray: '3 3' }}
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload;
                    return (
                      <div className="bg-white p-3 border rounded shadow">
                        <p className="font-medium">{data.name}</p>
                        <p>風險: {data.risk.toFixed(2)}%</p>
                        <p>回報: {data.return.toFixed(2)}%</p>
                        <p>夏普比率: {data.sharpe.toFixed(2)}</p>
                        {getStrategyTypeTag(data.type)}
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Scatter name="策略" data={scatterData}>
                {scatterData.map((entry, index) => (
                  <Scatter
                    key={`cell-${index}`}
                    fill={entry.color}
                  />
                ))}
              </Scatter>
              <Legend />
            </ScatterChart>
          )}
        </ResponsiveContainer>
      </div>

      {/* 詳細性能指標 */}
      {showDetails && (
        <div className="mt-6">
          <div className="text-sm font-medium mb-3 flex items-center gap-2">
            <LineChartOutlined />
            詳細性能指標
          </div>
          <Row gutter={[16, 16]}>
            {performanceData.map((strategy) => (
              <Col xs={24} sm={12} md={6} key={strategy.name}>
                <div className="bg-gray-50 rounded p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-sm">{strategy.name}</span>
                    {getStrategyTypeTag(strategy.type)}
                  </div>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between">
                      <span className="text-gray-600">總回報:</span>
                      <span className={strategy.totalReturn > 0 ? 'text-green-600 font-medium' : 'text-red-600'}>
                        {formatPercent(strategy.totalReturn)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">夏普比率:</span>
                      <span className="font-medium">{strategy.sharpeRatio.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">勝率:</span>
                      <span className="font-medium">{formatPercent(strategy.winRate)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">最大回撤:</span>
                      <span className="text-red-600 font-medium">
                        -{formatPercent(strategy.maxDrawdown)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">波動率:</span>
                      <span className="font-medium">{formatPercent(strategy.volatility)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Alpha:</span>
                      <span className={strategy.alpha > 0 ? 'text-green-600 font-medium' : 'text-red-600'}>
                        {formatPercent(strategy.alpha)}
                      </span>
                    </div>
                  </div>
                </div>
              </Col>
            ))}
          </Row>
        </div>
      )}

      {/* 性能洞察 */}
      <div className="mt-4 p-3 bg-blue-50 rounded">
        <div className="text-sm font-medium mb-2 flex items-center gap-2">
          <ThunderboltOutlined />
          性能洞察
        </div>
        <div className="text-xs text-gray-700 space-y-1">
          {(() => {
            const bestStrategy = performanceData.reduce((best, current) =>
              current.totalReturn > best.totalReturn ? current : best
            );
            const bestSharpe = performanceData.reduce((best, current) =>
              current.sharpeRatio > best.sharpeRatio ? current : best
            );
            const lowestRisk = performanceData.reduce((best, current) =>
              current.volatility < best.volatility ? current : best
            );

            return (
              <>
                <p>• 最佳回報策略: <strong>{bestStrategy.name}</strong> ({formatPercent(bestStrategy.totalReturn)})</p>
                <p>• 最高夏普比率: <strong>{bestSharpe.name}</strong> ({bestSharpe.sharpeRatio.toFixed(2)})</p>
                <p>• 最低風險策略: <strong>{lowestRisk.name}</strong> ({formatPercent(lowestRisk.volatility)})</p>
              </>
            );
          })()}
        </div>
      </div>

      {/* 更新時間 */}
      <div className="text-center text-gray-400 text-xs mt-3">
        最後更新: {new Date().toLocaleString('zh-TW')}
      </div>
    </Card>
  );
};

export default PerformanceComparison;
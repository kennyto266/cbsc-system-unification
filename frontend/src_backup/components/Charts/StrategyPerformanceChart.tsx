import React, { useState, useEffect, useRef } from 'react';
import { Card, Row, Col, Select, Button, Space, Typography, Switch, Tooltip } from 'antd';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ScatterChart,
  Scatter
} from 'recharts';
import {
  FullscreenOutlined,
  DownloadOutlined,
  SettingOutlined,
  ReloadOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import { Strategy } from '../../types/index';
import './StrategyPerformanceChart.css';

const { Title, Text } = Typography;
const { Option } = Select;

interface StrategyPerformanceChartProps {
  strategies?: Strategy[];
  height?: number;
  showControls?: boolean;
}

interface ChartDataPoint {
  date: string;
  [key: string]: any;
}

interface PerformanceData {
  period: string;
  benchmark: number;
  strategies: { [strategyName: string]: number };
}

const StrategyPerformanceChart: React.FC<StrategyPerformanceChartProps> = ({
  strategies = [],
  height = 400,
  showControls = true
}) => {
  const chartRef = useRef<HTMLDivElement>(null);

  const [chartType, setChartType] = useState<'line' | 'area' | 'bar' | 'scatter' | 'radar'>('line');
  const [timeRange, setTimeRange] = useState<'1M' | '3M' | '6M' | '1Y' | 'ALL'>('6M');
  const [selectedStrategies, setSelectedStrategies] = useState<string[]>([]);
  const [showBenchmark, setShowBenchmark] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [loading, setLoading] = useState(false);

  // 模擬性能數據
  const [performanceData, setPerformanceData] = useState<PerformanceData[]>([]);
  const [riskReturnData, setRiskReturnData] = useState<any[]>([]);

  // 生成模擬數據
  const generateMockData = () => {
    setLoading(true);

    try {
      // 時間序列數據
      const periods = [];
      const now = new Date();
      const days = timeRange === '1M' ? 30 : timeRange === '3M' ? 90 : timeRange === '6M' ? 180 : timeRange === '1Y' ? 365 : 730;

      for (let i = days; i >= 0; i -= 7) { // 週度數據
        const date = new Date(now);
        date.setDate(date.getDate() - i);
        periods.push(date.toISOString().split('T')[0]);
      }

      const newPerformanceData: PerformanceData[] = periods.map(period => {
        const benchmarkValue = 100 * (1 + Math.sin((days - periods.indexOf(period)) * 0.02) * 0.1 + (days - periods.indexOf(period)) * 0.001);

        const strategiesValues: { [key: string]: number } = {};

        // 為每個策略生成數據
        if (strategies.length > 0) {
          const selectedStrategyData = strategies.slice(0, 5); // 最多顯示5個策略
          selectedStrategyData.forEach((strategy, index) => {
            const baseValue = 100;
            const trend = (strategy.annual_return || 0.1) / 365 * 7; // 週度收益
            const volatility = strategy.volatility || 0.15;
            const noise = (Math.random() - 0.5) * volatility * Math.sqrt(7) * 0.01;

            strategiesValues[strategy.name] = baseValue * (1 + trend * (days - periods.indexOf(period)) + noise);
          });
        } else {
          // 模擬策略數據
          for (let i = 0; i < 3; i++) {
            const trend = (0.08 + i * 0.04) / 365 * 7;
            const volatility = 0.1 + i * 0.05;
            const noise = (Math.random() - 0.5) * volatility * Math.sqrt(7) * 0.01;
            strategiesValues[`策略 ${i + 1}`] = 100 * (1 + trend * (days - periods.indexOf(period)) + noise);
          }
        }

        return {
          period,
          benchmark: benchmarkValue,
          strategies: strategiesValues
        };
      });

      setPerformanceData(newPerformanceData);

      // 風險收益散點圖數據
      const riskData = strategies.length > 0 ? strategies : [
        { name: '策略 1', annual_return: 0.15, sharpe_ratio: 1.2, max_drawdown: 0.08, volatility: 0.12 },
        { name: '策略 2', annual_return: 0.18, sharpe_ratio: 1.5, max_drawdown: 0.12, volatility: 0.15 },
        { name: '策略 3', annual_return: 0.12, sharpe_ratio: 0.9, max_drawdown: 0.06, volatility: 0.10 },
      ];

      setRiskReturnData(riskData);

      // 初始化選中的策略
      if (selectedStrategies.length === 0 && strategies.length > 0) {
        setSelectedStrategies(strategies.slice(0, 3).map(s => s.name));
      }

    } catch (error) {
      console.error('Error generating mock data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    generateMockData();
  }, [timeRange, strategies]);

  // 準備圖表數據
  const prepareChartData = (): ChartDataPoint[] => {
    return performanceData.map(item => {
      const dataPoint: ChartDataPoint = {
        date: item.period,
        benchmark: item.benchmark
      };

      // 添加選中的策略數據
      Object.entries(item.strategies).forEach(([name, value]) => {
        if (selectedStrategies.includes(name)) {
          dataPoint[name] = value;
        }
      });

      return dataPoint;
    });
  };

  // 準備雷達圖數據
  const prepareRadarData = () => {
    const metrics = ['年化收益', '夏普比率', '勝率', '最大回撤(反向)', '穩定性'];
    const data = selectedStrategies.map(strategyName => {
      const strategy = strategies.find(s => s.name === strategyName);
      if (!strategy) return null;

      return {
        strategy: strategyName,
        年化收益: (strategy.annual_return || 0) * 100,
        夏普比率: (strategy.sharpe_ratio || 0) * 20,
        勝率: (strategy.win_rate || 0) * 100,
        最大回撤: (1 - (strategy.max_drawdown || 0)) * 100,
        穩定性: (1 - (strategy.volatility || 0)) * 100
      };
    }).filter(Boolean);

    return data;
  };

  // 獲取圖表顏色
  const getChartColor = (index: number) => {
    const colors = ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1'];
    return colors[index % colors.length];
  };

  // 導出圖表
  const exportChart = () => {
    // 這裡可以實現圖表導出功能
    console.log('Export chart functionality');
  };

  // 全屏切換
  const toggleFullscreen = () => {
    if (!isFullscreen && chartRef.current) {
      chartRef.current.requestFullscreen?.();
    } else {
      document.exitFullscreen?.();
    }
    setIsFullscreen(!isFullscreen);
  };

  const chartData = prepareChartData();
  const radarData = prepareRadarData();

  return (
    <div ref={chartRef} className={`strategy-performance-chart ${isFullscreen ? 'fullscreen' : ''}`}>
      <Card
        title="策略性能圖表"
        extra={
          showControls && (
            <Space>
              <Tooltip title="重新加載數據">
                <Button
                  icon={<ReloadOutlined />}
                  onClick={generateMockData}
                  loading={loading}
                />
              </Tooltip>
              <Tooltip title="導出圖表">
                <Button icon={<DownloadOutlined />} onClick={exportChart} />
              </Tooltip>
              <Tooltip title="全屏">
                <Button icon={<FullscreenOutlined />} onClick={toggleFullscreen} />
              </Tooltip>
            </Space>
          )
        }
      >
        {showControls && (
          <div className="chart-controls">
            <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
              <Col xs={24} sm={8}>
                <div className="control-item">
                  <Text>圖表類型:</Text>
                  <Select
                    value={chartType}
                    onChange={setChartType}
                    style={{ width: '100%', marginTop: 4 }}
                  >
                    <Option value="line">折線圖</Option>
                    <Option value="area">面積圖</Option>
                    <Option value="bar">柱狀圖</Option>
                    <Option value="scatter">散點圖</Option>
                    <Option value="radar">雷達圖</Option>
                  </Select>
                </div>
              </Col>

              <Col xs={24} sm={8}>
                <div className="control-item">
                  <Text>時間範圍:</Text>
                  <Select
                    value={timeRange}
                    onChange={setTimeRange}
                    style={{ width: '100%', marginTop: 4 }}
                  >
                    <Option value="1M">1個月</Option>
                    <Option value="3M">3個月</Option>
                    <Option value="6M">6個月</Option>
                    <Option value="1Y">1年</Option>
                    <Option value="ALL">全部</Option>
                  </Select>
                </div>
              </Col>

              <Col xs={24} sm={8}>
                <div className="control-item">
                  <Text>
                    顯示基準
                    <Tooltip title="顯示市場基準對比">
                      <InfoCircleOutlined style={{ marginLeft: 4 }} />
                    </Tooltip>
                  </Text>
                  <Switch
                    checked={showBenchmark}
                    onChange={setShowBenchmark}
                    style={{ marginTop: 8 }}
                  />
                </div>
              </Col>
            </Row>

            {/* 策略選擇 */}
            {chartType !== 'radar' && (
              <Row style={{ marginBottom: 16 }}>
                <Col span={24}>
                  <Text>選擇策略:</Text>
                  <Select
                    mode="multiple"
                    value={selectedStrategies}
                    onChange={setSelectedStrategies}
                    placeholder="選擇要顯示的策略"
                    style={{ width: '100%', marginTop: 4 }}
                    maxTagCount={3}
                  >
                    {(strategies.length > 0 ? strategies : [
                      { name: '策略 1' },
                      { name: '策略 2' },
                      { name: '策略 3' }
                    ]).map((strategy, index) => (
                      <Option key={strategy.name} value={strategy.name}>
                        {strategy.name}
                      </Option>
                    ))}
                  </Select>
                </Col>
              </Row>
            )}
          </div>
        )}

        {/* 圖表渲染區域 */}
        <div className="chart-container" style={{ height: height }}>
          {chartType === 'radar' ? (
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={radarData}>
                <PolarGrid />
                <PolarAngleAxis dataKey="strategy" />
                <PolarRadiusAxis angle={90} domain={[0, 100]} />
                <Radar
                  name="年化收益"
                  dataKey="年化收益"
                  stroke={getChartColor(0)}
                  fill={getChartColor(0)}
                  fillOpacity={0.3}
                />
                <Radar
                  name="夏普比率"
                  dataKey="夏普比率"
                  stroke={getChartColor(1)}
                  fill={getChartColor(1)}
                  fillOpacity={0.3}
                />
                <Radar
                  name="勝率"
                  dataKey="勝率"
                  stroke={getChartColor(2)}
                  fill={getChartColor(2)}
                  fillOpacity={0.3}
                />
                <Legend />
                <Tooltip />
              </RadarChart>
            </ResponsiveContainer>
          ) : chartType === 'scatter' ? (
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart data={riskReturnData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="volatility"
                  name="波動率"
                  unit="%"
                  domain={['dataMin - 0.01', 'dataMax + 0.01']}
                />
                <YAxis
                  dataKey="annual_return"
                  name="年化收益"
                  unit="%"
                  domain={['dataMin - 0.01', 'dataMax + 0.01']}
                />
                <Tooltip
                  cursor={{ strokeDasharray: '3 3' }}
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      return (
                        <div className="custom-tooltip">
                          <p><strong>{data.name}</strong></p>
                          <p>年化收益: {(data.annual_return * 100).toFixed(2)}%</p>
                          <p>夏普比率: {data.sharpe_ratio?.toFixed(2)}</p>
                          <p>最大回撤: {(data.max_drawdown * 100).toFixed(2)}%</p>
                          <p>波動率: {(data.volatility * 100).toFixed(2)}%</p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Scatter
                  name="策略"
                  data={riskReturnData}
                  fill="#1890ff"
                />
              </ScatterChart>
            </ResponsiveContainer>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              {chartType === 'line' ? (
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  {showBenchmark && (
                    <Line
                      type="monotone"
                      dataKey="benchmark"
                      stroke="#8c8c8c"
                      strokeDasharray="5 5"
                      name="基準"
                    />
                  )}
                  {selectedStrategies.map((strategyName, index) => (
                    <Line
                      key={strategyName}
                      type="monotone"
                      dataKey={strategyName}
                      stroke={getChartColor(index)}
                      name={strategyName}
                      strokeWidth={2}
                    />
                  ))}
                </LineChart>
              ) : chartType === 'area' ? (
                <AreaChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  {showBenchmark && (
                    <Area
                      type="monotone"
                      dataKey="benchmark"
                      stroke="#8c8c8c"
                      strokeDasharray="5 5"
                      fill="#8c8c8c"
                      fillOpacity={0.3}
                      name="基準"
                    />
                  )}
                  {selectedStrategies.map((strategyName, index) => (
                    <Area
                      key={strategyName}
                      type="monotone"
                      dataKey={strategyName}
                      stroke={getChartColor(index)}
                      fill={getChartColor(index)}
                      fillOpacity={0.3}
                      name={strategyName}
                    />
                  ))}
                </AreaChart>
              ) : (
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  {showBenchmark && (
                    <Bar dataKey="benchmark" fill="#8c8c8c" name="基準" />
                  )}
                  {selectedStrategies.map((strategyName, index) => (
                    <Bar
                      key={strategyName}
                      dataKey={strategyName}
                      fill={getChartColor(index)}
                      name={strategyName}
                    />
                  ))}
                </BarChart>
              )}
            </ResponsiveContainer>
          )}
        </div>

        {/* 圖表統計信息 */}
        {riskReturnData.length > 0 && (
          <div className="chart-stats">
            <Row gutter={16} style={{ marginTop: 16 }}>
              <Col span={6}>
                <div className="stat-item">
                  <Text type="secondary">平均年化收益</Text>
                  <div className="stat-value">
                    {(riskReturnData.reduce((sum, item) => sum + (item.annual_return || 0), 0) / riskReturnData.length * 100).toFixed(2)}%
                  </div>
                </div>
              </Col>
              <Col span={6}>
                <div className="stat-item">
                  <Text type="secondary">平均夏普比率</Text>
                  <div className="stat-value">
                    {(riskReturnData.reduce((sum, item) => sum + (item.sharpe_ratio || 0), 0) / riskReturnData.length).toFixed(2)}
                  </div>
                </div>
              </Col>
              <Col span={6}>
                <div className="stat-item">
                  <Text type="secondary">平均最大回撤</Text>
                  <div className="stat-value" style={{ color: '#ff4d4f' }}>
                    -{(riskReturnData.reduce((sum, item) => sum + (item.max_drawdown || 0), 0) / riskReturnData.length * 100).toFixed(2)}%
                  </div>
                </div>
              </Col>
              <Col span={6}>
                <div className="stat-item">
                  <Text type="secondary">平均波動率</Text>
                  <div className="stat-value">
                    {(riskReturnData.reduce((sum, item) => sum + (item.volatility || 0), 0) / riskReturnData.length * 100).toFixed(2)}%
                  </div>
                </div>
              </Col>
            </Row>
          </div>
        )}
      </Card>
    </div>
  );
};

export default StrategyPerformanceChart;
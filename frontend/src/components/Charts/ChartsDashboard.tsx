import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Switch, Button, Select, Space, Tooltip } from 'antd';
import {
  ChartManagerProvider,
  useChartManager,
  useChartPerformance
} from './ChartManager';
import SharpeRatioChart from './SharpeRatioChart';
import MaxDrawdownChart from './MaxDrawdownChart';
import StrategyRadarChart from './StrategyRadarChart';
import { Strategy } from '../../types/index';
import {
  LineChartOutlined,
  BarChartOutlined,
  RadarChartOutlined,
  SettingOutlined,
  ReloadOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined
} from '@ant-design/icons';

const { Option } = Select;

// Props for the charts dashboard
interface ChartsDashboardProps {
  strategies: Strategy[];
  height?: number;
  showControls?: boolean;
  defaultLayout?: 'grid' | 'stacked';
}

// Main Charts Dashboard Component
export const ChartsDashboard: React.FC<ChartsDashboardProps> = ({
  strategies,
  height = 400,
  showControls = true,
  defaultLayout = 'grid'
}) => {
  const [realTimeEnabled, setRealTimeEnabled] = useState(false);
  const [updateInterval, setUpdateInterval] = useState(10000);
  const [layout, setLayout] = useState<'grid' | 'stacked'>(defaultLayout);
  const [selectedCharts, setSelectedCharts] = useState({
    sharpe: true,
    drawdown: true,
    radar: true
  });

  return (
    <ChartManagerProvider>
      <ChartsDashboardContent
        strategies={strategies}
        height={height}
        showControls={showControls}
        layout={layout}
        selectedCharts={selectedCharts}
        setLayout={setLayout}
        setSelectedCharts={setSelectedCharts}
        realTimeEnabled={realTimeEnabled}
        setRealTimeEnabled={setRealTimeEnabled}
        updateInterval={updateInterval}
        setUpdateInterval={setUpdateInterval}
      />
    </ChartManagerProvider>
  );
};

// Internal component that uses the chart manager context
const ChartsDashboardContent: React.FC<ChartsDashboardProps & {
  layout: 'grid' | 'stacked';
  selectedCharts: { sharpe: boolean; drawdown: boolean; radar: boolean };
  setLayout: (layout: 'grid' | 'stacked') => void;
  setSelectedCharts: (charts: { sharpe: boolean; drawdown: boolean; radar: boolean }) => void;
  realTimeEnabled: boolean;
  setRealTimeEnabled: (enabled: boolean) => void;
  updateInterval: number;
  setUpdateInterval: (interval: number) => void;
}> = ({
  strategies,
  height,
  showControls,
  layout,
  selectedCharts,
  setLayout,
  setSelectedCharts,
  realTimeEnabled,
  setRealTimeEnabled,
  updateInterval,
  setUpdateInterval
}) => {
  const {
    resizeCharts,
    enableRealTimeUpdates,
    setUpdateInterval: setChartUpdateInterval,
    destroyAllCharts
  } = useChartManager();

  const { performanceData, chartCount } = useChartPerformance();

  // Handle real-time updates
  useEffect(() => {
    enableRealTimeUpdates(realTimeEnabled);
  }, [realTimeEnabled, enableRealTimeUpdates]);

  // Handle update interval changes
  useEffect(() => {
    setChartUpdateInterval(updateInterval);
  }, [updateInterval, setChartUpdateInterval]);

  // Handle strategy selection
  const handleStrategySelect = (strategy: Strategy) => {
    console.log('Strategy selected:', strategy.name);
    // Here you could show more details about the selected strategy
  };

  // Handle bar click in Sharpe ratio chart
  const handleBarClick = (strategy: Strategy) => {
    console.log('Bar clicked for strategy:', strategy.name);
    // Here you could show detailed performance metrics
  };

  // Refresh all charts
  const handleRefresh = () => {
    resizeCharts();
  };

  // Toggle chart visibility
  const toggleChart = (chartType: 'sharpe' | 'drawdown' | 'radar') => {
    setSelectedCharts(prev => ({
      ...prev,
      [chartType]: !prev[chartType]
    }));
  };

  // Render controls panel
  const renderControls = () => {
    if (!showControls) return null;

    return (
      <Card size="small" className="mb-4">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-4">
            <span className="text-sm font-medium">實時更新:</span>
            <Switch
              checked={realTimeEnabled}
              onChange={setRealTimeEnabled}
              checkedChildren={<PlayCircleOutlined />}
              unCheckedChildren={<PauseCircleOutlined />}
            />

            {realTimeEnabled && (
              <Select
                value={updateInterval}
                onChange={setUpdateInterval}
                style={{ width: 120 }}
                size="small"
              >
                <Option value={5000}>5秒</Option>
                <Option value={10000}>10秒</Option>
                <Option value={30000}>30秒</Option>
                <Option value={60000}>1分鐘</Option>
              </Select>
            )}
          </div>

          <div className="flex items-center gap-4">
            <span className="text-sm font-medium">佈局:</span>
            <Select
              value={layout}
              onChange={setLayout}
              style={{ width: 100 }}
              size="small"
            >
              <Option value="grid">網格</Option>
              <Option value="stacked">堆疊</Option>
            </Select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">圖表:</span>
            <Space>
              <Tooltip title="Sharpe比率圖">
                <Button
                  type={selectedCharts.sharpe ? 'primary' : 'default'}
                  size="small"
                  icon={<BarChartOutlined />}
                  onClick={() => toggleChart('sharpe')}
                />
              </Tooltip>
              <Tooltip title="最大回撤圖">
                <Button
                  type={selectedCharts.drawdown ? 'primary' : 'default'}
                  size="small"
                  icon={<LineChartOutlined />}
                  onClick={() => toggleChart('drawdown')}
                />
              </Tooltip>
              <Tooltip title="雷達圖">
                <Button
                  type={selectedCharts.radar ? 'primary' : 'default'}
                  size="small"
                  icon={<RadarChartOutlined />}
                  onClick={() => toggleChart('radar')}
                />
              </Tooltip>
            </Space>
          </div>

          <div className="flex items-center gap-2">
            <Button
              size="small"
              icon={<ReloadOutlined />}
              onClick={handleRefresh}
            >
              刷新
            </Button>

            {process.env.NODE_ENV === 'development' && (
              <Tooltip title={`性能: ${chartCount} 個圖表`}>
                <Button
                  size="small"
                  icon={<SettingOutlined />}
                  onClick={() => console.log('Performance data:', performanceData)}
                />
              </Tooltip>
            )}
          </div>
        </div>
      </Card>
    );
  };

  // Render charts based on layout
  const renderCharts = () => {
    if (layout === 'stacked') {
      return (
        <div className="space-y-6">
          {selectedCharts.sharpe && (
            <Card title="Sharpe比率排名" size="small">
              <SharpeRatioChart
                strategies={strategies}
                height={height}
                onBarClick={handleBarClick}
              />
            </Card>
          )}
          {selectedCharts.drawdown && (
            <Card title="最大回撤趨勢" size="small">
              <MaxDrawdownChart
                strategies={strategies}
                height={height}
                onStrategyClick={handleStrategySelect}
              />
            </Card>
          )}
          {selectedCharts.radar && (
            <Card title="策略多維度對比" size="small">
              <StrategyRadarChart
                strategies={strategies}
                height={height}
                onStrategySelect={handleStrategySelect}
              />
            </Card>
          )}
        </div>
      );
    }

    return (
      <Row gutter={[16, 16]}>
        {selectedCharts.sharpe && (
          <Col xs={24} lg={12}>
            <Card title="Sharpe比率排名" size="small">
              <SharpeRatioChart
                strategies={strategies}
                height={height}
                onBarClick={handleBarClick}
              />
            </Card>
          </Col>
        )}
        {selectedCharts.drawdown && (
          <Col xs={24} lg={12}>
            <Card title="最大回撤趨勢" size="small">
              <MaxDrawdownChart
                strategies={strategies}
                height={height}
                onStrategyClick={handleStrategySelect}
              />
            </Card>
          </Col>
        )}
        {selectedCharts.radar && (
          <Col xs={24} lg={selectedCharts.sharpe || selectedCharts.drawdown ? 24 : 24}>
            <Card title="策略多維度對比" size="small">
              <StrategyRadarChart
                strategies={strategies}
                height={height}
                onStrategySelect={handleStrategySelect}
              />
            </Card>
          </Col>
        )}
      </Row>
    );
  };

  // Empty state when no strategies are available
  if (strategies.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="text-gray-400 mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">沒有策略數據</h3>
          <p className="text-gray-600">請先添加策略或檢查數據源連接</p>
        </div>
      </div>
    );
  }

  return (
    <div className="charts-dashboard">
      {renderControls()}
      {renderCharts()}

      {/* Real-time status indicator */}
      {realTimeEnabled && (
        <div className="fixed bottom-4 right-4 bg-green-100 border border-green-400 text-green-700 px-3 py-1 rounded-md text-sm flex items-center gap-2">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          實時更新中 ({updateInterval / 1000}秒)
        </div>
      )}
    </div>
  );
};

export default ChartsDashboard;
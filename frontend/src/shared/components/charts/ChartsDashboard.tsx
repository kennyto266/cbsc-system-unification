import React, { useState } from 'react';
import { Card, Row, Col, Switch, Button, Select, Space, Tooltip } from 'antd';
import PerformanceChart from './PerformanceChart';
import RealTimeChart from './RealTimeChart';
import { StrategyChartData } from './types';

const { Option } = Select;

interface ChartsDashboardProps {
  strategies?: StrategyChartData[];
  height?: number;
  showControls?: boolean;
  defaultLayout?: 'grid' | 'stacked';
}

export const ChartsDashboard: React.FC<ChartsDashboardProps> = ({
  strategies = [],
  height = 400,
  showControls = true,
  defaultLayout = 'grid'
}) => {
  const [realTimeEnabled, setRealTimeEnabled] = useState(false);
  const [updateInterval, setUpdateInterval] = useState(10000);
  const [layout, setLayout] = useState<'grid' | 'stacked'>(defaultLayout);
  const [selectedCharts, setSelectedCharts] = useState({
    performance: true,
    realtime: true
  });

  // Mock data source for real-time chart
  const mockDataSource = async (): Promise<number> => {
    return Math.random() * 100;
  };

  // Toggle chart visibility
  const toggleChart = (chartType: 'performance' | 'realtime') => {
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
              <Tooltip title="績效圖表">
                <Button
                  type={selectedCharts.performance ? 'primary' : 'default'}
                  size="small"
                  onClick={() => toggleChart('performance')}
                >
                  績效
                </Button>
              </Tooltip>
              <Tooltip title="實時圖表">
                <Button
                  type={selectedCharts.realtime ? 'primary' : 'default'}
                  size="small"
                  onClick={() => toggleChart('realtime')}
                >
                  實時
                </Button>
              </Tooltip>
            </Space>
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
          {selectedCharts.performance && (
            <Card title="策略績效" size="small">
              <PerformanceChart height={height} />
            </Card>
          )}
          {selectedCharts.realtime && (
            <Card title="實時數據" size="small">
              <RealTimeChart
                title="實時價格"
                dataSource={mockDataSource}
                updateInterval={updateInterval}
                height={height}
              />
            </Card>
          )}
        </div>
      );
    }

    return (
      <Row gutter={[16, 16]}>
        {selectedCharts.performance && (
          <Col xs={24} lg={12}>
            <Card title="策略績效" size="small">
              <PerformanceChart height={height} />
            </Card>
          </Col>
        )}
        {selectedCharts.realtime && (
          <Col xs={24} lg={12}>
            <Card title="實時數據" size="small">
              <RealTimeChart
                title="實時價格"
                dataSource={mockDataSource}
                updateInterval={updateInterval}
                height={height}
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

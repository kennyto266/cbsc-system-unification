import React from 'react'
import { Card, Alert, Space, Button } from 'antd'
import {
  StrategyPerformanceChart,
  AssetAllocationChart,
  StrategyComparisonChart,
  RiskReturnScatterChart,
  RealTimePriceChart
} from './index'
import { Strategy, StrategyType } from '../../types'

// 簡單測試數據
const testStrategies: Strategy[] = [
  {
    id: 'test1',
    name: '測試策略1',
    type: StrategyType.SENTIMENT,
    status: 'active',
    riskLevel: 'low',
    description: '測試用策略',
    parameters: {},
    performance: {
      totalReturn: 0.15,
      sharpeRatio: 1.2,
      maxDrawdown: -0.05,
      winRate: 0.65,
      profitFactor: 1.8
    },
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-12-10T00:00:00Z'
  },
  {
    id: 'test2',
    name: '測試策略2',
    type: StrategyType.TECHNICAL,
    status: 'active',
    riskLevel: 'medium',
    description: '測試用策略',
    parameters: {},
    performance: {
      totalReturn: 0.25,
      sharpeRatio: 1.8,
      maxDrawdown: -0.12,
      winRate: 0.58,
      profitFactor: 2.1
    },
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-12-10T00:00:00Z'
  }
]

const ChartTestComponent: React.FC = () => {
  return (
    <div className="p-4 space-y-4">
      <Alert
        message="Chart.js 圖表組件測試"
        description="這是一個測試頁面，用於驗證所有圖表組件是否正常工作"
        type="info"
        showIcon
      />

      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 測試策略性能圖表 */}
        <Card title="策略性能圖表測試" size="small">
          <div style={{ height: '300px' }}>
            <StrategyPerformanceChart
              strategies={testStrategies}
              timeRange="1M"
              onTimeRangeChange={(range) => console.log('時間範圍變更:', range)}
            />
          </div>
        </Card>

        {/* 測試資產配置圖表 */}
        <Card title="資產配置圖表測試" size="small">
          <div style={{ height: '400px' }}>
            <AssetAllocationChart
              strategies={testStrategies}
              totalValue={50000}
              showDetails={true}
            />
          </div>
        </Card>

        {/* 測試策略對比圖表 */}
        <Card title="策略對比圖表測試" size="small">
          <div style={{ height: '400px' }}>
            <StrategyComparisonChart
              strategies={testStrategies}
              metric="totalReturn"
              onMetricChange={(metric) => console.log('指標變更:', metric)}
              sortBy="value"
              showTopN={5}
            />
          </div>
        </Card>

        {/* 測試風險收益散點圖 */}
        <Card title="風險收益散點圖測試" size="small">
          <div style={{ height: '500px' }}>
            <RiskReturnScatterChart
              strategies={testStrategies}
              showQuadrants={true}
              showEfficientFrontier={true}
              filterType="all"
              onFilterChange={(type) => console.log('類型過濾:', type)}
            />
          </div>
        </Card>

        {/* 測試實時價格圖表 */}
        <Card title="實時價格圖表測試" size="small">
          <div style={{ height: '500px' }}>
            <RealTimePriceChart
              strategy={testStrategies[0]}
              symbol="BTC/USDT"
              timeFrame="1h"
              showVolume={true}
              showIndicators={true}
              autoUpdate={false}
            />
          </div>
        </Card>
      </Space>

      <Alert
        message="測試完成"
        description="如果所有圖表都正常顯示，說明Chart.js集成成功！"
        type="success"
        showIcon
      />
    </div>
  )
}

export default ChartTestComponent
import React, { useState } from 'react'
import { Card, Row, Col, Typography, Space, Button, Alert, Divider } from 'antd'
import { FullscreenOutlined, DownloadOutlined, SettingOutlined } from '@ant-design/icons'
import {
  StrategyPerformanceChart,
  AssetAllocationChart,
  StrategyComparisonChart,
  RiskReturnScatterChart,
  RealTimePriceChart
} from '../../components/Charts'
import { Strategy, StrategyType } from '../../types'

const { Title, Text } = Typography

const ChartsShowcasePage: React.FC = () => {
  // 狀態管理
  const [timeRange, setTimeRange] = useState<'1D' | '1W' | '1M' | '3M' | '6M' | '1Y'>('1M')
  const [comparisonMetric, setComparisonMetric] = useState<'totalReturn' | 'sharpeRatio' | 'maxDrawdown' | 'winRate' | 'profitFactor'>('totalReturn')
  const [filterType, setFilterType] = useState<StrategyType | 'all'>('all')

  // 模擬策略數據
  const mockStrategies: Strategy[] = [
    {
      id: '1',
      name: 'RSI均值回歸策略',
      type: StrategyType.MEAN_REVERSION,
      status: 'active',
      riskLevel: 'medium',
      description: '基於相對強弱指數的均值回歸交易策略，適合震荡行情',
      parameters: { rsiPeriod: 14, oversoldLevel: 30, overboughtLevel: 70 },
      performance: {
        totalReturn: 0.185,
        sharpeRatio: 1.45,
        maxDrawdown: -0.08,
        winRate: 0.65,
        profitFactor: 1.8
      },
      createdAt: '2024-01-01T00:00:00Z',
      updatedAt: '2024-12-10T00:00:00Z'
    },
    {
      id: '2',
      name: 'MACD動量策略',
      type: StrategyType.MOMENTUM,
      status: 'active',
      riskLevel: 'high',
      description: '基於MACD指標的動量追蹤策略，適合趋势行情',
      parameters: { fastPeriod: 12, slowPeriod: 26, signalPeriod: 9 },
      performance: {
        totalReturn: 0.242,
        sharpeRatio: 1.78,
        maxDrawdown: -0.15,
        winRate: 0.58,
        profitFactor: 2.1
      },
      createdAt: '2024-02-01T00:00:00Z',
      updatedAt: '2024-12-10T00:00:00Z'
    },
    {
      id: '3',
      name: '情感分析策略',
      type: StrategyType.SENTIMENT,
      status: 'active',
      riskLevel: 'low',
      description: '基於市場情感分析的交易策略，利用市场情绪变化',
      parameters: { sentimentSource: 'twitter', threshold: 0.6 },
      performance: {
        totalReturn: 0.123,
        sharpeRatio: 1.12,
        maxDrawdown: -0.05,
        winRate: 0.72,
        profitFactor: 1.5
      },
      createdAt: '2024-03-01T00:00:00Z',
      updatedAt: '2024-12-10T00:00:00Z'
    },
    {
      id: '4',
      name: '布林帶突破策略',
      type: StrategyType.TECHNICAL,
      status: 'active',
      riskLevel: 'medium',
      description: '基於布林帶的突破交易策略，捕捉价格突破机会',
      parameters: { period: 20, stdDev: 2 },
      performance: {
        totalReturn: 0.156,
        sharpeRatio: 1.34,
        maxDrawdown: -0.10,
        winRate: 0.61,
        profitFactor: 1.7
      },
      createdAt: '2024-04-01T00:00:00Z',
      updatedAt: '2024-12-10T00:00:00Z'
    },
    {
      id: '5',
      name: '統計套利策略',
      type: StrategyType.ARBITRAGE,
      status: 'active',
      riskLevel: 'low',
      description: '基於統計分析的套利策略，寻找价格偏差机会',
      parameters: { lookbackPeriod: 30, zScoreThreshold: 2 },
      performance: {
        totalReturn: 0.089,
        sharpeRatio: 2.15,
        maxDrawdown: -0.03,
        winRate: 0.78,
        profitFactor: 1.9
      },
      createdAt: '2024-05-01T00:00:00Z',
      updatedAt: '2024-12-10T00:00:00Z'
    },
    {
      id: '6',
      name: '網格交易策略',
      type: StrategyType.MEAN_REVERSION,
      status: 'active',
      riskLevel: 'medium',
      description: '基於網格交易的均值回歸策略，适合震荡行情',
      parameters: { gridLevels: 10, gridSpacing: 0.02 },
      performance: {
        totalReturn: 0.145,
        sharpeRatio: 1.28,
        maxDrawdown: -0.09,
        winRate: 0.68,
        profitFactor: 1.6
      },
      createdAt: '2024-06-01T00:00:00Z',
      updatedAt: '2024-12-10T00:00:00Z'
    },
    {
      id: '7',
      name: '移動平均線策略',
      type: StrategyType.TECHNICAL,
      status: 'active',
      riskLevel: 'low',
      description: '基於移動平均線的趨勢跟蹤策略',
      parameters: { fastMA: 20, slowMA: 50 },
      performance: {
        totalReturn: 0.167,
        sharpeRatio: 1.52,
        maxDrawdown: -0.07,
        winRate: 0.64,
        profitFactor: 1.8
      },
      createdAt: '2024-07-01T00:00:00Z',
      updatedAt: '2024-12-10T00:00:00Z'
    },
    {
      id: '8',
      name: '相對強度策略',
      type: StrategyType.MOMENTUM,
      status: 'active',
      riskLevel: 'high',
      description: '基於相對強度指標的動量策略',
      parameters: { lookbackPeriod: 252, topPercentile: 80 },
      performance: {
        totalReturn: 0.223,
        sharpeRatio: 1.65,
        maxDrawdown: -0.18,
        winRate: 0.55,
        profitFactor: 1.9
      },
      createdAt: '2024-08-01T00:00:00Z',
      updatedAt: '2024-12-10T00:00:00Z'
    }
  ]

  return (
    <div className="space-y-6 p-6">
      {/* 頁面標題和說明 */}
      <div className="text-center mb-8">
        <Title level={2} className="mb-4">
          Chart.js 圖表組件展示
        </Title>
        <Text type="secondary" className="text-lg">
          專業級金融圖表組件庫 - 支持實時數據、交互式操作和響應式設計
        </Text>
      </div>

      {/* 功能說明 */}
      <Alert
        message="圖表功能特性"
        description={
          <div className="space-y-2">
            <div>🎯 <strong>多種圖表類型</strong>: 線圖、柱狀圖、餅圖、散點圖、K線圖等</div>
            <div>📊 <strong>實時數據更新</strong>: 支持WebSocket實時數據推送和動態更新</div>
            <div>🎨 <strong>高度可定制</strong>: 主題、顏色、動畫、交互效果均可自定義</div>
            <div>📱 <strong>響應式設計</strong>: 完美適配桌面、平板和手機端</div>
            <div>💾 <strong>導出功能</strong>: 支持PNG、JPG、SVG等格式導出</div>
            <div>⚡ <strong>性能優化</strong>: 大數據集渲染優化，流暢的動畫效果</div>
          </div>
        }
        type="info"
        showIcon
        className="mb-6"
      />

      {/* 第一行：策略性能走勢圖和資產配置圖 */}
      <Row gutter={[24, 24]}>
        <Col xs={24} lg={16}>
          <StrategyPerformanceChart
            strategies={mockStrategies}
            timeRange={timeRange}
            onTimeRangeChange={setTimeRange}
          />
        </Col>
        <Col xs={24} lg={8}>
          <AssetAllocationChart
            strategies={mockStrategies}
            totalValue={100000}
            showDetails={true}
          />
        </Col>
      </Row>

      {/* 第二行：策略對比圖和風險收益散點圖 */}
      <Row gutter={[24, 24]}>
        <Col xs={24} lg={12}>
          <StrategyComparisonChart
            strategies={mockStrategies}
            metric={comparisonMetric}
            onMetricChange={setComparisonMetric}
            sortBy="value"
            showTopN={8}
          />
        </Col>
        <Col xs={24} lg={12}>
          <RiskReturnScatterChart
            strategies={mockStrategies}
            showQuadrants={true}
            showEfficientFrontier={true}
            filterType={filterType}
            onFilterChange={setFilterType}
          />
        </Col>
      </Row>

      {/* 第三行：實時價格圖表 */}
      <Row gutter={[24, 24]}>
        <Col xs={24}>
          <RealTimePriceChart
            strategy={mockStrategies[0]}
            symbol="BTC/USDT"
            timeFrame="1h"
            showVolume={true}
            showIndicators={true}
            autoUpdate={true}
          />
        </Col>
      </Row>

      {/* 圖表統計信息 */}
      <Divider orientation="left">
        <Title level={4}>圖表統計信息</Title>
      </Divider>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} md={6}>
          <Card size="small">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{mockStrategies.length}</div>
              <div className="text-gray-600">總策略數</div>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card size="small">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {mockStrategies.filter(s => s.status === 'active').length}
              </div>
              <div className="text-gray-600">活躍策略</div>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card size="small">
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {Object.values(StrategyType).length}
              </div>
              <div className="text-gray-600">策略類型</div>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card size="small">
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {mockStrategies.reduce((sum, s) => sum + s.performance.totalReturn, 0) > 0 ? '+' : ''}
                {(mockStrategies.reduce((sum, s) => sum + s.performance.totalReturn, 0) * 100).toFixed(1)}%
              </div>
              <div className="text-gray-600">總回報率</div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 使用說明 */}
      <Divider orientation="left">
        <Title level={4}>使用說明</Title>
      </Divider>

      <Card title="圖表組件使用指南" className="bg-gray-50">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-semibold mb-3">📈 策略性能走勢圖</h4>
            <ul className="space-y-1 text-sm text-gray-600">
              <li>• 支持多策略對比顯示</li>
              <li>• 可切換不同時間範圍（1日-1年）</li>
              <li>• 支持導出PNG格式圖片</li>
              <li>• 全屏顯示功能</li>
              <li>• 實時數據更新</li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold mb-3">🥧 資產配置餅圖</h4>
            <ul className="space-y-1 text-sm text-gray-600">
              <li>• 顯示策略資產分配比例</li>
              <li>• 風險級別可視化（低/中/高）</li>
              <li>• 詳細統計信息面板</li>
              <li>• 點擊圖表查看詳情</li>
              <li>• 動態權重計算</li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold mb-3">📊 策略對比柱狀圖</h4>
            <ul className="space-y-1 text-sm text-gray-600">
              <li>• 多種性能指標對比</li>
              <li>• 支持按名稱或數值排序</li>
              <li>• 風險級別顏色區分</li>
              <li>• 可設置顯示數量</li>
              <li>• 詳細tooltip信息</li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold mb-3">📈 風險收益散點圖</h4>
            <ul className="space-y-1 text-sm text-gray-600">
              <li>• 風險vs收益可視化</li>
              <li>• 有效前沿線顯示</li>
              <li>• 四象限分析</li>
              <li>• 策略類型過濾</li>
              <li>• 統計信息展示</li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold mb-3">💹 實時價格K線圖</h4>
            <ul className="space-y-1 text-sm text-gray-600">
              <li>• 實時價格數據更新</li>
              <li>• 技術指標疊加（SMA、EMA、RSI等）</li>
              <li>• 成交量圖表</li>
              <li>• 多時間框架支持</li>
              <li>• 播放/暫停控制</li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold mb-3">🛠️ 技術特性</h4>
            <ul className="space-y-1 text-sm text-gray-600">
              <li>• 基於Chart.js 4.x</li>
              <li>• TypeScript完整類型支持</li>
              <li>• React Hooks集成</li>
              <li>• 響應式設計</li>
              <li>• 無障礙支持</li>
            </ul>
          </div>
        </div>
      </Card>

      {/* 底部操作按鈕 */}
      <div className="flex justify-center space-x-4">
        <Button type="primary" size="large" icon={<DownloadOutlined />}>
          導出所有圖表
        </Button>
        <Button size="large" icon={<FullscreenOutlined />}>
          全屏模式
        </Button>
        <Button size="large" icon={<SettingOutlined />}>
          圖表設置
        </Button>
      </div>
    </div>
  )
}

export default ChartsShowcasePage
import React, { useState } from 'react'
import {
  Card,
  Row,
  Col,
  Statistic,
  Progress,
  Tag,
  Button,
  Space,
  Table,
  DatePicker,
  Select,
  InputNumber,
  Form,
  Alert,
  Spin,
  Empty,
  Tooltip,
  Badge,
  Descriptions,
  Tabs,
  Switch,
  Modal,
  message,
  Divider,
  Typography,
} from 'antd'
import {
  PlayCircleOutlined,
  StopOutlined,
  DownloadOutlined,
  SyncOutlined,
  TrophyOutlined,
  LineChartOutlined,
  BarChartOutlined,
  SettingOutlined,
  HistoryOutlined,
  SwapOutlined,
} from '@ant-design/icons'
import { motion } from 'framer-motion'
import dayjs, { Dayjs } from 'dayjs'
import { Line, Column, DualAxes } from '@ant-design/plots'

import { useBacktest } from '../../hooks/strategies'

// Styles
import './BacktestPanel.css'

const { RangePicker } = DatePicker
const { Option } = Select
const { TabPane } = Tabs
const { Text } = Typography

interface BacktestPanelProps {
  strategyId: string
  embedded?: boolean
}

interface BacktestConfig {
  startDate: Dayjs
  endDate: Dayjs
  initialCapital: number
  commission: number
  slippage: number
  benchmark: string
  parameters: Record<string, any>
}

const BacktestPanel: React.FC<BacktestPanelProps> = ({
  strategyId,
  embedded = false,
}) => {
  const [activeTab, setActiveTab] = useState('config')
  const [form] = Form.useForm()
  const [backtestConfig, setBacktestConfig] = useState<Partial<BacktestConfig>>({
    initialCapital: 100000,
    commission: 0.001,
    slippage: 0.0001,
    benchmark: 'SPY',
  })

  const {
    isRunning,
    runningBacktestId,
    progress,
    currentStep,
    backtestList,
    backtestResult,
    runBacktest,
    deleteBacktest,
    compareStrategies,
    exportResults,
    reset,
  } = useBacktest({ strategyId })

  // Handle backtest configuration
  const handleConfigChange = (changedFields: any, allFields: any) => {
    setBacktestConfig({ ...backtestConfig, ...allFields })
  }

  // Run backtest
  const handleRunBacktest = async () => {
    try {
      const values = await form.validateFields()
      const config = {
        ...backtestConfig,
        ...values,
        strategyId,
        startDate: values.dateRange?.[0].toISOString(),
        endDate: values.dateRange?.[1].toISOString(),
      }

      await runBacktest(config as any)
      setActiveTab('results')
      message.success('回測已開始運行')
    } catch (error) {
      // Error is handled in the hook
    }
  }

  // Export backtest results
  const handleExport = (format: 'csv' | 'json' | 'pdf') => {
    if (runningBacktestId) {
      exportResults(runningBacktestId, format)
    } else {
      message.warning('沒有可導出的回測結果')
    }
  }

  // Performance metrics
  const getPerformanceMetrics = () => {
    if (!backtestResult) return []

    return [
      {
        label: '總回報率',
        value: `${(backtestResult.totalReturn * 100).toFixed(2)}%`,
        color: backtestResult.totalReturn >= 0 ? '#52c41a' : '#f5222d',
      },
      {
        label: '年化收益率',
        value: `${(backtestResult.annualReturn * 100).toFixed(2)}%`,
        color: backtestResult.annualReturn >= 0 ? '#52c41a' : '#f5222d',
      },
      {
        label: '夏普比率',
        value: backtestResult.sharpeRatio?.toFixed(2) || 'N/A',
        color: '#1890ff',
      },
      {
        label: '最大回撤',
        value: `${(backtestResult.maxDrawdown * 100).toFixed(2)}%`,
        color: '#ff4d4f',
      },
      {
        label: '勝率',
        value: `${(backtestResult.winRate * 100).toFixed(1)}%`,
        color: '#52c41a',
      },
      {
        label: '盈虧比',
        value: backtestResult.profitLossRatio?.toFixed(2) || 'N/A',
        color: '#1890ff',
      },
      {
        label: '交易次數',
        value: backtestResult.totalTrades || 0,
        color: '#666',
      },
      {
        label: '卡爾瑪比率',
        value: backtestResult.calmarRatio?.toFixed(2) || 'N/A',
        color: '#1890ff',
      },
    ]
  }

  // Prepare chart data
  const getEquityCurveData = () => {
    if (!backtestResult?.equityCurve) return []
    return backtestResult.equityCurve.map((item: any) => ({
      date: dayjs(item.date).format('YYYY-MM-DD'),
      strategy: item.value,
      benchmark: item.benchmark,
    }))
  }

  const getDrawdownData = () => {
    if (!backtestResult?.drawdown) return []
    return backtestResult.drawdown.map((item: any) => ({
      date: dayjs(item.date).format('YYYY-MM-DD'),
      value: item.value,
    }))
  }

  const getMonthlyReturnsData = () => {
    if (!backtestResult?.monthlyReturns) return []
    return backtestResult.monthlyReturns.map((item: any) => ({
      month: item.month,
      return: item.return * 100,
    }))
  }

  // Trade history columns
  const tradeColumns = [
    {
      title: '時間',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (time: string) => dayjs(time).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '品種',
      dataIndex: 'symbol',
      key: 'symbol',
    },
    {
      title: '方向',
      dataIndex: 'side',
      key: 'side',
      render: (side: string) => (
        <Tag color={side === 'BUY' ? 'green' : 'red'}>
          {side === 'BUY' ? '買入' : '賣出'}
        </Tag>
      ),
    },
    {
      title: '數量',
      dataIndex: 'quantity',
      key: 'quantity',
      align: 'right' as const,
    },
    {
      title: '價格',
      dataIndex: 'price',
      key: 'price',
      align: 'right' as const,
      render: (price: number) => price.toFixed(4),
    },
    {
      title: '手續費',
      dataIndex: 'commission',
      key: 'commission',
      align: 'right' as const,
      render: (fee: number) => fee.toFixed(2),
    },
    {
      title: '滑點',
      dataIndex: 'slippage',
      key: 'slippage',
      align: 'right' as const,
      render: (slippage: number) => slippage.toFixed(4),
    },
  ]

  return (
    <div className={`backtest-panel ${embedded ? 'embedded' : ''}`}>
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane
          tab={
            <span>
              <SettingOutlined />
              回測配置
            </span>
          }
          key="config"
        >
          <Card title="回測參數設置">
            <Form
              form={form}
              layout="vertical"
              onValuesChange={handleConfigChange}
              initialValues={{
                dateRange: [dayjs().subtract(1, 'year'), dayjs().subtract(1, 'day')],
                initialCapital: 100000,
                commission: 0.001,
                slippage: 0.0001,
                benchmark: 'SPY',
              }}
            >
              <Row gutter={[16, 16]}>
                <Col xs={24} sm={12}>
                  <Form.Item
                    label="回測時間範圍"
                    name="dateRange"
                    rules={[{ required: true, message: '請選擇回測時間範圍' }]}
                  >
                    <RangePicker style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col xs={24} sm={12}>
                  <Form.Item
                    label="基準指數"
                    name="benchmark"
                  >
                    <Select>
                      <Option value="SPY">S&P 500</Option>
                      <Option value="QQQ">NASDAQ</Option>
                      <Option value="HSI">恆生指數</Option>
                      <Option value="000001.SH">上證指數</Option>
                      <Option value="399001.SZ">深證成指</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col xs={24} sm={8}>
                  <Form.Item
                    label="初始資金"
                    name="initialCapital"
                    rules={[{ required: true, message: '請輸入初始資金' }]}
                  >
                    <InputNumber
                      style={{ width: '100%' }}
                      min={1000}
                      max={10000000}
                      formatter={value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                      parser={value => value!.replace(/\$\s?|(,*)/g, '')}
                    />
                  </Form.Item>
                </Col>
                <Col xs={24} sm={8}>
                  <Form.Item
                    label="手續費率"
                    name="commission"
                    rules={[{ required: true, message: '請輸入手續費率' }]}
                  >
                    <InputNumber
                      style={{ width: '100%' }}
                      min={0}
                      max={0.01}
                      step={0.0001}
                      formatter={value => `${(Number(value) * 100).toFixed(2)}%`}
                      parser={value => (Number(value!.replace('%', '')) / 100).toString()}
                    />
                  </Form.Item>
                </Col>
                <Col xs={24} sm={8}>
                  <Form.Item
                    label="滑點"
                    name="slippage"
                    rules={[{ required: true, message: '請輸入滑點' }]}
                  >
                    <InputNumber
                      style={{ width: '100%' }}
                      min={0}
                      max={0.001}
                      step={0.0001}
                      formatter={value => `${(Number(value) * 100).toFixed(2)}bps`}
                      parser={value => (Number(value!.replace('bps', '')) / 100).toString()}
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Divider />

              <Row gutter={[16, 16]}>
                <Col span={24}>
                  <Form.Item label="高級設置">
                    <Space direction="vertical" style={{ width: '100%' }}>
                      <Form.Item name="enableOptimization" valuePropName="checked">
                        <Switch /> 啟用參數優化
                      </Form.Item>
                      <Form.Item name="enableMonteCarlo" valuePropName="checked">
                        <Switch /> 啟用蒙特卡羅模擬
                      </Form.Item>
                      <Form.Item name="enableStressTest" valuePropName="checked">
                        <Switch /> 啟用壓力測試
                      </Form.Item>
                    </Space>
                  </Form.Item>
                </Col>
              </Row>

              <Divider />

              <Space>
                <Button
                  type="primary"
                  icon={<PlayCircleOutlined />}
                  onClick={handleRunBacktest}
                  loading={isRunning}
                  size="large"
                >
                  開始回測
                </Button>
                <Button icon={<HistoryOutlined />}>
                  加載歷史回測
                </Button>
                <Button icon={<SwapOutlined />}>
                  策略比較
                </Button>
              </Space>
            </Form>
          </Card>

          {/* Running Progress */}
          {isRunning && (
            <Card title="回測運行中" style={{ marginTop: 16 }}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <div>
                  <Text>當前進度: {currentStep}</Text>
                  <Progress percent={progress} status="active" />
                </div>
                <div>
                  <Text>預計剩餘時間: 計算中...</Text>
                </div>
              </Space>
            </Card>
          )}
        </TabPane>

        <TabPane
          tab={
            <span>
              <LineChartOutlined />
              結果分析
            </span>
          }
          key="results"
          disabled={!backtestResult}
        >
          {!backtestResult ? (
            <Empty description="暫無回測結果" />
          ) : (
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              {/* Performance Metrics */}
              <Card title="績效指標">
                <Row gutter={[16, 16]}>
                  {getPerformanceMetrics().map((metric, index) => (
                    <Col xs={24} sm={12} md={6} key={index}>
                      <Statistic
                        title={metric.label}
                        value={metric.value}
                        valueStyle={{ color: metric.color }}
                      />
                    </Col>
                  ))}
                </Row>
              </Card>

              {/* Equity Curve */}
              <Card title="資金曲線">
                <DualAxes
                  data={[getEquityCurveData(), getDrawdownData()]}
                  xField="date"
                  yField={['strategy', 'value']}
                  geometryOptions={[
                    {
                      geometry: 'line',
                      color: '#1890ff',
                      smooth: true,
                    },
                    {
                      geometry: 'area',
                      color: '#ff4d4f',
                    },
                  ]}
                />
              </Card>

              {/* Monthly Returns */}
              <Card title="月度收益">
                <Column
                  data={getMonthlyReturnsData()}
                  xField="month"
                  yField="return"
                  color={(data: any) => data.return >= 0 ? '#52c41a' : '#f5222d'}
                />
              </Card>
            </Space>
          )}
        </TabPane>

        <TabPane
          tab={
            <span>
              <HistoryOutlined />
              交易記錄
            </span>
          }
          key="trades"
          disabled={!backtestResult}
        >
          {backtestResult?.trades ? (
            <Table
              columns={tradeColumns}
              dataSource={backtestResult.trades}
              rowKey="id"
              pagination={{
                pageSize: 20,
                showSizeChanger: true,
                showQuickJumper: true,
              }}
              scroll={{ x: 1000 }}
            />
          ) : (
            <Empty description="暫無交易記錄" />
          )}
        </TabPane>

        <TabPane
          tab={
            <span>
              <BarChartOutlined />
              風險分析
            </span>
          }
          key="risk"
          disabled={!backtestResult}
        >
          {backtestResult?.riskAnalysis ? (
            <Descriptions bordered column={2}>
              <Descriptions.Item label="VaR (95%)">
                {(backtestResult.riskAnalysis.var95 * 100).toFixed(2)}%
              </Descriptions.Item>
              <Descriptions.Item label="VaR (99%)">
                {(backtestResult.riskAnalysis.var99 * 100).toFixed(2)}%
              </Descriptions.Item>
              <Descriptions.Item label="最大連續虧損">
                {backtestResult.riskAnalysis.maxConsecutiveLosses} 天
              </Descriptions.Item>
              <Descriptions.Item label="最大連續盈利">
                {backtestResult.riskAnalysis.maxConsecutiveWins} 天
              </Descriptions.Item>
              <Descriptions.Item label="波動率">
                {(backtestResult.riskAnalysis.volatility * 100).toFixed(2)}%
              </Descriptions.Item>
              <Descriptions.Item label="Beta">
                {backtestResult.riskAnalysis.beta?.toFixed(2) || 'N/A'}
              </Descriptions.Item>
            </Descriptions>
          ) : (
            <Empty description="暫無風險分析數據" />
          )}
        </TabPane>
      </Tabs>

      {/* Export Actions */}
      {backtestResult && (
        <Card title="導出報告" style={{ marginTop: 16 }}>
          <Space>
            <Button icon={<DownloadOutlined />} onClick={() => handleExport('csv')}>
              導出 CSV
            </Button>
            <Button icon={<DownloadOutlined />} onClick={() => handleExport('json')}>
              導出 JSON
            </Button>
            <Button icon={<DownloadOutlined />} onClick={() => handleExport('pdf')}>
              導出 PDF 報告
            </Button>
          </Space>
        </Card>
      )}
    </div>
  )
}

export default BacktestPanel
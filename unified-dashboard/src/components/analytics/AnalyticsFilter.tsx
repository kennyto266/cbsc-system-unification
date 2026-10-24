import React, { useState } from 'react'
import { Card, Form, Select, DatePicker, Button, Space, Row, Col, Typography, Tag } from 'antd'
import { FilterOutlined, ClearOutlined, SaveOutlined } from '@ant-design/icons'

const { RangePicker } = DatePicker
const { Option } = Select
const { Text } = Typography

interface AnalyticsFilterProps {
  onFilterChange?: (filters: any) => void
  onReset?: () => void
  onSaveFilter?: (name: string, filters: any) => void
  savedFilters?: Array<{ name: string; filters: any }>
}

const AnalyticsFilter: React.FC<AnalyticsFilterProps> = ({
  onFilterChange,
  onReset,
  onSaveFilter,
  savedFilters = [],
}) => {
  const [form] = Form.useForm()
  const [showAdvanced, setShowAdvanced] = useState(false)

  const strategies = [
    { id: 'all', name: '所有策略' },
    { id: '1', name: 'RSI策略' },
    { id: '2', name: 'MACD策略' },
    { id: '3', name: '布林帶策略' },
    { id: '4', name: '情感分析策略' },
    { id: '5', name: '多因子策略' },
  ]

  const benchmarks = [
    { id: 'HS300', name: '滬深300' },
    { id: 'CSI500', name: '中證500' },
    { id: 'SZSE', name: '深證成指' },
    { id: 'BTC', name: '比特幣' },
  ]

  const sectors = [
    { id: 'all', name: '所有行業' },
    { id: 'tech', name: '科技' },
    { id: 'finance', name: '金融' },
    { id: 'consumer', name: '消費' },
    { id: 'healthcare', name: '醫療' },
    { id: 'energy', name: '能源' },
  ]

  const handleValuesChange = (changedValues: any, allValues: any) => {
    onFilterChange?.(allValues)
  }

  const handleReset = () => {
    form.resetFields()
    onReset?.()
  }

  const handleSaveFilter = () => {
    const values = form.getFieldsValue()
    const name = `過濾器 ${new Date().toLocaleString('zh-CN')}`
    onSaveFilter?.(name, values)
  }

  const loadSavedFilter = (filter: any) => {
    form.setFieldsValue(filter.filters)
    onFilterChange?.(filter.filters)
  }

  return (
    <Card title="分析過濾器" size="small">
      <Form
        form={form}
        layout="vertical"
        onValuesChange={handleValuesChange}
        initialValues={{
          timeRange: '6M',
          strategy: 'all',
          benchmark: 'HS300',
          sector: 'all',
        }}
      >
        <Row gutter={[16, 16]}>
          {/* Basic Filters */}
          <Col xs={24} sm={12} md={6}>
            <Form.Item label="時間範圍" name="timeRange">
              <Select placeholder="選擇時間範圍">
                <Option value="1M">1個月</Option>
                <Option value="3M">3個月</Option>
                <Option value="6M">6個月</Option>
                <Option value="1Y">1年</Option>
                <Option value="ALL">全部</Option>
              </Select>
            </Form.Item>
          </Col>

          <Col xs={24} sm={12} md={6}>
            <Form.Item label="策略選擇" name="strategy">
              <Select placeholder="選擇策略">
                {strategies.map(strategy => (
                  <Option key={strategy.id} value={strategy.id}>
                    {strategy.name}
                  </Option>
                ))}
              </Select>
            </Form.Item>
          </Col>

          <Col xs={24} sm={12} md={6}>
            <Form.Item label="基準指數" name="benchmark">
              <Select placeholder="選擇基準指數">
                {benchmarks.map(benchmark => (
                  <Option key={benchmark.id} value={benchmark.id}>
                    {benchmark.name}
                  </Option>
                ))}
              </Select>
            </Form.Item>
          </Col>

          <Col xs={24} sm={12} md={6}>
            <Form.Item label="行業篩選" name="sector">
              <Select placeholder="選擇行業">
                {sectors.map(sector => (
                  <Option key={sector.id} value={sector.id}>
                    {sector.name}
                  </Option>
                ))}
              </Select>
            </Form.Item>
          </Col>

          {/* Custom Date Range */}
          <Col xs={24} sm={12} md={6}>
            <Form.Item label="自定義時間" name="customDateRange">
              <RangePicker
                style={{ width: '100%' }}
                placeholder={['開始日期', '結束日期']}
              />
            </Form.Item>
          </Col>

          {/* Advanced Filters */}
          {showAdvanced && (
            <>
              <Col xs={24} sm={12} md={6}>
                <Form.Item label="最小收益率" name="minReturn">
                  <Select placeholder="選擇最小收益率">
                    <Option value="-10">-10%</Option>
                    <Option value="-5">-5%</Option>
                    <Option value="0">0%</Option>
                    <Option value="5">5%</Option>
                    <Option value="10">10%</Option>
                  </Select>
                </Form.Item>
              </Col>

              <Col xs={24} sm={12} md={6}>
                <Form.Item label="最大回撤" name="maxDrawdown">
                  <Select placeholder="選擇最大回撤">
                    <Option value="5">5%</Option>
                    <Option value="10">10%</Option>
                    <Option value="15">15%</Option>
                    <Option value="20">20%</Option>
                  </Select>
                </Form.Item>
              </Col>

              <Col xs={24} sm={12} md={6}>
                <Form.Item label="最小夏普比率" name="minSharpe">
                  <Select placeholder="選擇最小夏普比率">
                    <Option value="0">0</Option>
                    <Option value="0.5">0.5</Option>
                    <Option value="1">1</Option>
                    <Option value="1.5">1.5</Option>
                    <Option value="2">2</Option>
                  </Select>
                </Form.Item>
              </Col>

              <Col xs={24} sm={12} md={6}>
                <Form.Item label="數據頻率" name="frequency">
                  <Select placeholder="選擇數據頻率">
                    <Option value="daily">每日</Option>
                    <Option value="weekly">每週</Option>
                    <Option value="monthly">每月</Option>
                  </Select>
                </Form.Item>
              </Col>

              <Col xs={24} sm={12} md={6}>
                <Form.Item label="風險等級" name="riskLevel">
                  <Select placeholder="選擇風險等級">
                    <Option value="low">低風險</Option>
                    <Option value="medium">中等風險</Option>
                    <Option value="high">高風險</Option>
                  </Select>
                </Form.Item>
              </Col>

              <Col xs={24} sm={12} md={6}>
                <Form.Item label="交易頻率" name="tradingFrequency">
                  <Select placeholder="選擇交易頻率">
                    <Option value="high">高頻</Option>
                    <Option value="medium">中頻</Option>
                    <Option value="low">低頻</Option>
                  </Select>
                </Form.Item>
              </Col>
            </>
          )}
        </Row>

        {/* Action Buttons */}
        <Row gutter={[8, 8]}>
          <Col>
            <Button
              type="link"
              icon={<FilterOutlined />}
              onClick={() => setShowAdvanced(!showAdvanced)}
            >
              {showAdvanced ? '隱藏高級選項' : '顯示高級選項'}
            </Button>
          </Col>
          <Col>
            <Button
              icon={<ClearOutlined />}
              onClick={handleReset}
            >
              重置
            </Button>
          </Col>
          <Col>
            <Button
              type="primary"
              icon={<SaveOutlined />}
              onClick={handleSaveFilter}
            >
              保存過濾器
            </Button>
          </Col>
        </Row>

        {/* Saved Filters */}
        {savedFilters.length > 0 && (
          <div className="mt-4">
            <Text className="block mb-2">已保存的過濾器:</Text>
            <Space wrap>
              {savedFilters.map((filter, index) => (
                <Tag
                  key={index}
                  className="cursor-pointer"
                  onClick={() => loadSavedFilter(filter)}
                >
                  {filter.name}
                </Tag>
              ))}
            </Space>
          </div>
        )}
      </Form>
    </Card>
  )
}

export default AnalyticsFilter
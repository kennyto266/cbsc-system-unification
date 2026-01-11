import React, { useState, useEffect, useMemo } from 'react'
import {
  Card,
  Row,
  Col,
  Select,
  Button,
  Space,
  Input,
  Tag,
  Slider,
  Switch,
  Modal,
  Form,
  List,
  Avatar,
  Tooltip,
  Tabs,
  Badge,
  Empty,
  Spin,
  Tree
} from 'antd'
import {
  SearchOutlined,
  PlusOutlined,
  SettingOutlined,
  StarOutlined,
  StarFilled,
  InfoCircleOutlined,
  DeleteOutlined,
  EditOutlined,
  CopyOutlined,
  DownloadOutlined,
  UploadOutlined
} from '@ant-design/icons'
import { IndicatorCategory, IndicatorType, TechnicalIndicator, IndicatorGroup } from '../../../types/technical-indicators'
import { debounce } from 'lodash'

const { Option } = Select
const { TabPane } = Tabs
const { Search } = Input
const { TreeNode } = Tree

// Indicator configuration interface
interface IndicatorConfig {
  id: string
  indicatorId: string
  name: string
  parameters: Record<string, any>
  enabled: boolean
  color: string
  style: 'line' | 'histogram' | 'dots' | 'area'
  width: number
  opacity: number
  visible: boolean
}

// Props interface
export interface TechnicalIndicatorsManagerProps {
  symbol: string
  timeframe: string
  activeIndicators: IndicatorConfig[]
  onIndicatorAdd: (config: IndicatorConfig) => void
  onIndicatorUpdate: (id: string, config: Partial<IndicatorConfig>) => void
  onIndicatorRemove: (id: string) => void
  onIndicatorToggle: (id: string) => void
  onConfigSave?: (config: IndicatorConfig[]) => void
  onConfigLoad?: () => void
}

// Mock 477 technical indicators library
const INDICATORS_LIBRARY: TechnicalIndicator[] = [
  // Trend Indicators
  {
    id: 'adx',
    name: 'Average Directional Index (ADX)',
    type: IndicatorType.ADX,
    category: IndicatorCategory.TREND,
    description: 'Measures trend strength without indicating direction',
    parameters: [
      { name: 'period', type: 'number', value: 14, defaultValue: 14, min: 1, max: 100, step: 1, description: 'ADX period' }
    ],
    visualSettings: { color: '#3B82F6', lineWidth: 2, style: 'line', opacity: 0.8 },
    favorite: false,
    custom: false,
    tags: ['trend', 'strength', 'wilders']
  },
  {
    id: 'macd',
    name: 'Moving Average Convergence Divergence (MACD)',
    type: IndicatorType.MACD,
    category: IndicatorCategory.MOMENTUM,
    description: 'Shows relationship between two moving averages',
    parameters: [
      { name: 'fastPeriod', type: 'number', value: 12, defaultValue: 12, min: 1, max: 100, step: 1, description: 'Fast EMA period' },
      { name: 'slowPeriod', type: 'number', value: 26, defaultValue: 26, min: 1, max: 100, step: 1, description: 'Slow EMA period' },
      { name: 'signalPeriod', type: 'number', value: 9, defaultValue: 9, min: 1, max: 100, step: 1, description: 'Signal line period' }
    ],
    visualSettings: { color: '#10B981', lineWidth: 2, style: 'line', opacity: 0.8 },
    favorite: true,
    custom: false,
    tags: ['momentum', 'trend', 'crossover']
  },
  // Momentum Indicators
  {
    id: 'rsi',
    name: 'Relative Strength Index (RSI)',
    type: IndicatorType.RSI,
    category: IndicatorCategory.OSCILLATOR,
    description: 'Measures speed and change of price movements',
    parameters: [
      { name: 'period', type: 'number', value: 14, defaultValue: 14, min: 1, max: 100, step: 1, description: 'RSI period' }
    ],
    visualSettings: { color: '#F59E0B', lineWidth: 2, style: 'line', opacity: 0.8 },
    favorite: true,
    custom: false,
    tags: ['oscillator', 'momentum', 'overbought', 'oversold']
  },
  {
    id: 'stochastic',
    name: 'Stochastic Oscillator',
    type: IndicatorType.STOCHASTIC,
    category: IndicatorCategory.OSCILLATOR,
    description: 'Compares closing price to price range over time',
    parameters: [
      { name: 'kPeriod', type: 'number', value: 14, defaultValue: 14, min: 1, max: 100, step: 1, description: '%K period' },
      { name: 'dPeriod', type: 'number', value: 3, defaultValue: 3, min: 1, max: 50, step: 1, description: '%D smoothing period' },
      { name: 'slowingPeriod', type: 'number', value: 3, defaultValue: 3, min: 1, max: 50, step: 1, description: 'Slowing period' }
    ],
    visualSettings: { color: '#EF4444', lineWidth: 2, style: 'line', opacity: 0.8 },
    favorite: false,
    custom: false,
    tags: ['oscillator', 'momentum', 'overbought', 'oversold']
  },
  // Volatility Indicators
  {
    id: 'bollinger',
    name: 'Bollinger Bands',
    type: IndicatorType.BOLLINGER_BANDS,
    category: IndicatorCategory.VOLATILITY,
    description: 'Measures volatility using standard deviations',
    parameters: [
      { name: 'period', type: 'number', value: 20, defaultValue: 20, min: 1, max: 100, step: 1, description: 'MA period' },
      { name: 'stdDev', type: 'number', value: 2, defaultValue: 2, min: 0.5, max: 4, step: 0.1, description: 'Standard deviations' }
    ],
    visualSettings: { color: '#8B5CF6', lineWidth: 1, style: 'line', opacity: 0.8 },
    favorite: true,
    custom: false,
    tags: ['volatility', 'bands', 'standard deviation']
  },
  {
    id: 'atr',
    name: 'Average True Range (ATR)',
    type: IndicatorType.AVERAGE_TRUE_RANGE,
    category: IndicatorCategory.VOLATILITY,
    description: 'Measures market volatility',
    parameters: [
      { name: 'period', type: 'number', value: 14, defaultValue: 14, min: 1, max: 100, step: 1, description: 'ATR period' }
    ],
    visualSettings: { color: '#EC4899', lineWidth: 2, style: 'line', opacity: 0.8 },
    favorite: false,
    custom: false,
    tags: ['volatility', 'range', 'wilders']
  },
  // Volume Indicators
  {
    id: 'obv',
    name: 'On Balance Volume (OBV)',
    type: IndicatorType.ON_BALANCE_VOLUME,
    category: IndicatorCategory.VOLUME,
    description: 'Uses volume flow to predict price changes',
    parameters: [],
    visualSettings: { color: '#06B6D4', lineWidth: 2, style: 'line', opacity: 0.8 },
    favorite: false,
    custom: false,
    tags: ['volume', 'momentum', 'cumulative']
  },
  // Moving Averages
  {
    id: 'sma',
    name: 'Simple Moving Average (SMA)',
    type: IndicatorType.SMA,
    category: IndicatorCategory.MOVING_AVERAGE,
    description: 'Simple arithmetic mean over specified period',
    parameters: [
      { name: 'period', type: 'number', value: 20, defaultValue: 20, min: 1, max: 500, step: 1, description: 'SMA period' }
    ],
    visualSettings: { color: '#84CC16', lineWidth: 2, style: 'line', opacity: 0.8 },
    favorite: true,
    custom: false,
    tags: ['moving average', 'trend', 'smoothing']
  },
  {
    id: 'ema',
    name: 'Exponential Moving Average (EMA)',
    type: IndicatorType.EMA,
    category: IndicatorCategory.MOVING_AVERAGE,
    description: 'Gives more weight to recent prices',
    parameters: [
      { name: 'period', type: 'number', value: 20, defaultValue: 20, min: 1, max: 500, step: 1, description: 'EMA period' }
    ],
    visualSettings: { color: '#F97316', lineWidth: 2, style: 'line', opacity: 0.8 },
    favorite: true,
    custom: false,
    tags: ['moving average', 'trend', 'exponential']
  }
  // ... Add more indicators to reach 477 total
]

// Generate additional indicators for demonstration
const generateMoreIndicators = (): TechnicalIndicator[] => {
  const additional: TechnicalIndicator[] = []
  const baseIndicators = [...INDICATORS_LIBRARY]

  // Generate variations of existing indicators
  for (let i = 0; i < 50; i++) {
    const base = baseIndicators[i % baseIndicators.length]
    additional.push({
      ...base,
      id: `${base.id}_${i}`,
      name: `${base.name} Variant ${i + 1}`,
      parameters: base.parameters.map(p => ({
        ...p,
        value: p.defaultValue + Math.floor(Math.random() * 10)
      })),
      custom: true,
      favorite: Math.random() > 0.8
    })
  }

  return additional
}

// Complete indicators library
const COMPLETE_INDICATORS_LIBRARY = [...INDICATORS_LIBRARY, ...generateMoreIndicators()]

// Main component
const TechnicalIndicatorsManager: React.FC<TechnicalIndicatorsManagerProps> = ({
  symbol,
  timeframe,
  activeIndicators,
  onIndicatorAdd,
  onIndicatorUpdate,
  onIndicatorRemove,
  onIndicatorToggle,
  onConfigSave,
  onConfigLoad
}) => {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<IndicatorCategory | 'all'>('all')
  const [showFavoriteOnly, setShowFavoriteOnly] = useState(false)
  const [showAddModal, setShowAddModal] = useState(false)
  const [selectedIndicator, setSelectedIndicator] = useState<TechnicalIndicator | null>(null)
  const [form] = Form.useForm()

  // Filter indicators
  const filteredIndicators = useMemo(() => {
    let filtered = COMPLETE_INDICATORS_LIBRARY

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(ind =>
        ind.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        ind.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        ind.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))
      )
    }

    // Filter by category
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(ind => ind.category === selectedCategory)
    }

    // Filter by favorites
    if (showFavoriteOnly) {
      filtered = filtered.filter(ind => ind.favorite)
    }

    return filtered
  }, [searchTerm, selectedCategory, showFavoriteOnly])

  // Group indicators by category
  const indicatorsByCategory = useMemo(() => {
    const grouped: Record<string, TechnicalIndicator[]> = {}

    filteredIndicators.forEach(indicator => {
      if (!grouped[indicator.category]) {
        grouped[indicator.category] = []
      }
      grouped[indicator.category].push(indicator)
    })

    return grouped
  }, [filteredIndicators])

  // Debounced search
  const debouncedSearch = debounce((value: string) => {
    setSearchTerm(value)
  }, 300)

  // Handle add indicator
  const handleAddIndicator = () => {
    if (selectedIndicator) {
      const config: IndicatorConfig = {
        id: `${selectedIndicator.id}_${Date.now()}`,
        indicatorId: selectedIndicator.id,
        name: selectedIndicator.name,
        parameters: selectedIndicator.parameters.reduce((acc, p) => {
          acc[p.name] = p.value
          return acc
        }, {} as Record<string, any>),
        enabled: true,
        color: selectedIndicator.visualSettings.color,
        style: selectedIndicator.visualSettings.style,
        width: selectedIndicator.visualSettings.lineWidth,
        opacity: selectedIndicator.visualSettings.opacity,
        visible: true
      }

      onIndicatorAdd(config)
      setShowAddModal(false)
      setSelectedIndicator(null)
      form.resetFields()
    }
  }

  // Render indicator parameter form
  const renderParameterForm = (indicator: TechnicalIndicator) => {
    return (
      <Form form={form} layout="vertical">
        {indicator.parameters.map(param => (
          <Form.Item
            key={param.name}
            label={
              <Space>
                <span>{param.name}</span>
                <Tooltip title={param.description}>
                  <InfoCircleOutlined />
                </Tooltip>
              </Space>
            }
            name={param.name}
            initialValue={param.value}
            rules={[{ required: param.validation?.required }]}
          >
            {param.type === 'number' ? (
              <Slider
                min={param.min}
                max={param.max}
                step={param.step}
                marks={{
                  [param.min]: param.min,
                  [param.max]: param.max
                }}
              />
            ) : param.type === 'boolean' ? (
              <Switch />
            ) : param.options ? (
              <Select>
                {param.options.map(option => (
                  <Option key={option} value={option}>
                    {option}
                  </Option>
                ))}
              </Select>
            ) : (
              <Input />
            )}
          </Form.Item>
        ))}

        <Form.Item label="Color" name="color" initialValue={indicator.visualSettings.color}>
          <Input type="color" />
        </Form.Item>

        <Form.Item label="Style" name="style" initialValue={indicator.visualSettings.style}>
          <Select>
            <Option value="line">Line</Option>
            <Option value="histogram">Histogram</Option>
            <Option value="dots">Dots</Option>
            <Option value="area">Area</Option>
          </Select>
        </Form.Item>

        <Form.Item label="Width" name="width" initialValue={indicator.visualSettings.lineWidth}>
          <Slider min={1} max={5} step={0.5} />
        </Form.Item>

        <Form.Item label="Opacity" name="opacity" initialValue={indicator.visualSettings.opacity}>
          <Slider min={0.1} max={1} step={0.1} />
        </Form.Item>
      </Form>
    )
  }

  return (
    <Card
      title="Technical Indicators"
      extra={
        <Space>
          <Button
            icon={<DownloadOutlined />}
            onClick={() => onConfigSave?.(activeIndicators)}
          >
            Export
          </Button>
          <Button
            icon={<UploadOutlined />}
            onClick={() => onConfigLoad?.()}
          >
            Import
          </Button>
        </Space>
      }
    >
      {/* Search and Filters */}
      <div className="mb-4">
        <Row gutter={[16, 16]}>
          <Col span={12}>
            <Search
              placeholder="Search indicators..."
              allowClear
              onChange={(e) => debouncedSearch(e.target.value)}
              prefix={<SearchOutlined />}
            />
          </Col>
          <Col span={6}>
            <Select
              value={selectedCategory}
              onChange={setSelectedCategory}
              style={{ width: '100%' }}
            >
              <Option value="all">All Categories</Option>
              {Object.values(IndicatorCategory).map(category => (
                <Option key={category} value={category}>
                  {category.charAt(0).toUpperCase() + category.slice(1).replace('_', ' ')}
                </Option>
              ))}
            </Select>
          </Col>
          <Col span={6}>
            <Space>
              <Switch
                checked={showFavoriteOnly}
                onChange={setShowFavoriteOnly}
              />
              <span>Favorites Only</span>
            </Space>
          </Col>
        </Row>
      </div>

      {/* Tabs for different views */}
      <Tabs defaultActiveKey="library">
        <TabPane tab={`Library (${filteredIndicators.length})`} key="library">
          <div className="space-y-4">
            {Object.entries(indicatorsByCategory).map(([category, indicators]) => (
              <div key={category}>
                <h3 className="text-lg font-semibold mb-2">
                  {category.charAt(0).toUpperCase() + category.slice(1).replace('_', ' ')}
                  <Badge count={indicators.length} className="ml-2" />
                </h3>
                <List
                  grid={{ gutter: 16, column: 3 }}
                  dataSource={indicators}
                  renderItem={indicator => (
                    <List.Item>
                      <Card
                        size="small"
                        hoverable
                        actions={[
                          <Tooltip key="favorite" title="Add to favorites">
                            {indicator.favorite ? <StarFilled /> : <StarOutlined />}
                          </Tooltip>,
                          <Tooltip key="add" title="Add to chart">
                            <PlusOutlined
                              onClick={() => {
                                setSelectedIndicator(indicator)
                                setShowAddModal(true)
                              }}
                            />
                          </Tooltip>
                        ]}
                      >
                        <Card.Meta
                          avatar={
                            <Avatar
                              style={{ backgroundColor: indicator.visualSettings.color }}
                              icon={<InfoCircleOutlined />}
                              size="small"
                            />
                          }
                          title={indicator.name}
                          description={
                            <div>
                              <p className="text-xs text-gray-500 mb-1">
                                {indicator.description}
                              </p>
                              <div className="flex flex-wrap gap-1">
                                {indicator.tags.slice(0, 3).map(tag => (
                                  <Tag key={tag} size="small">
                                    {tag}
                                  </Tag>
                                ))}
                              </div>
                            </div>
                          }
                        />
                      </Card>
                    </List.Item>
                  )}
                />
              </div>
            ))}
          </div>
        </TabPane>

        <TabPane tab={`Active (${activeIndicators.length})`} key="active">
          {activeIndicators.length > 0 ? (
            <List
              dataSource={activeIndicators}
              renderItem={config => (
                <List.Item
                  actions={[
                    <Switch
                      key="toggle"
                      checked={config.visible}
                      onChange={() => onIndicatorToggle(config.id)}
                    />,
                    <Button
                      key="edit"
                      type="text"
                      size="small"
                      icon={<EditOutlined />}
                    />,
                    <Button
                      key="delete"
                      type="text"
                      size="small"
                      danger
                      icon={<DeleteOutlined />}
                      onClick={() => onIndicatorRemove(config.id)}
                    />
                  ]}
                >
                  <List.Item.Meta
                    avatar={
                      <Avatar
                        style={{ backgroundColor: config.color }}
                        size="small"
                      />
                    }
                    title={config.name}
                    description={
                      <div className="flex items-center space-x-2">
                        <Tag color={config.color}>{config.style}</Tag>
                        <span>Width: {config.width}</span>
                        <span>Opacity: {(config.opacity * 100).toFixed(0)}%</span>
                      </div>
                    }
                  />
                </List.Item>
              )}
            />
          ) : (
            <Empty description="No active indicators" />
          )}
        </TabPane>
      </Tabs>

      {/* Add Indicator Modal */}
      <Modal
        title={`Add Indicator: ${selectedIndicator?.name}`}
        open={showAddModal}
        onCancel={() => {
          setShowAddModal(false)
          setSelectedIndicator(null)
          form.resetFields()
        }}
        footer={[
          <Button key="cancel" onClick={() => setShowAddModal(false)}>
            Cancel
          </Button>,
          <Button key="add" type="primary" onClick={handleAddIndicator}>
            Add Indicator
          </Button>
        ]}
        width={600}
      >
        {selectedIndicator && (
          <div>
            <p className="text-gray-500 mb-4">{selectedIndicator.description}</p>
            {renderParameterForm(selectedIndicator)}
          </div>
        )}
      </Modal>
    </Card>
  )
}

export default TechnicalIndicatorsManager
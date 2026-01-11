import React, { useState, useEffect, useMemo } from 'react'
import {
  Row,
  Col,
  Card,
  Input,
  Select,
  Button,
  Tag,
  Space,
  Typography,
  Tabs,
  Badge,
  Tooltip,
  Pagination,
  Empty,
  Spin,
  message,
  Drawer,
  Modal,
  Form
} from 'antd'
import {
  SearchOutlined,
  StarOutlined,
  StarFilled,
  FilterOutlined,
  SettingOutlined,
  PlusOutlined,
  DownloadOutlined,
  UploadOutlined,
  HeartOutlined,
  CodeOutlined,
  BookOutlined,
  ThunderboltOutlined,
  LineChartOutlined
} from '@ant-design/icons'

// Components
import IndicatorCard from '../../components/technical-indicators/IndicatorCard'
import IndicatorDetails from '../../components/technical-indicators/IndicatorDetails'
import IndicatorParameterForm from '../../components/technical-indicators/IndicatorParameterForm'
import ConfigurationPanel from '../../components/technical-indicators/ConfigurationPanel'

// Hooks and Redux
import { useAppDispatch, useAppSelector } from '../../hooks/redux'
import {
  fetchIndicators,
  selectFilteredIndicators,
  selectAllIndicators,
  selectIndicatorsByCategory,
  selectFavoriteIndicators,
  selectCustomIndicators,
  selectIsLoading,
  selectError,
  setSearchFilter,
  clearSearchFilter,
  toggleFavorite,
  selectIndicator,
  clearSelectedIndicator
} from '../../store/slices/technicalIndicatorsSlice'

// Types and Data
import {
  TechnicalIndicator,
  IndicatorCategory,
  IndicatorSearchFilter,
  IndicatorConfiguration
} from '../../types/technical-indicators'
import { INDICATOR_CATEGORIES, POPULAR_COMBINATIONS } from '../../data/technical-indicators-library'

const { Title, Text, Paragraph } = Typography
const { Search } = Input
const { TabPane } = Tabs

const IndicatorLibraryPage: React.FC = () => {
  const dispatch = useAppDispatch()

  // Redux state
  const indicators = useAppSelector(selectAllIndicators)
  const filteredIndicators = useAppSelector(selectFilteredIndicators)
  const indicatorsByCategory = useAppSelector(selectIndicatorsByCategory)
  const favoriteIndicators = useAppSelector(selectFavoriteIndicators)
  const customIndicators = useAppSelector(selectCustomIndicators)
  const isLoading = useAppSelector(selectIsLoading)
  const error = useAppSelector(selectError)

  // Local state
  const [activeTab, setActiveTab] = useState('all')
  const [showFilter, setShowFilter] = useState(false)
  const [showDetails, setShowDetails] = useState(false)
  const [showParameterForm, setShowParameterForm] = useState(false)
  const [showConfigPanel, setShowConfigPanel] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedIndicator, setSelectedIndicator] = useState<TechnicalIndicator | null>(null)
  const [filterForm] = Form.useForm()

  // Effects
  useEffect(() => {
    dispatch(fetchIndicators())
  }, [dispatch])

  // Search and filter handlers
  const handleSearch = (value: string) => {
    setSearchTerm(value)
    dispatch(setSearchFilter({ search: value }))
  }

  const handleFilterChange = (filters: Partial<IndicatorSearchFilter>) => {
    dispatch(setSearchFilter(filters))
  }

  const clearFilters = () => {
    dispatch(clearSearchFilter())
    setSearchTerm('')
    filterForm.resetFields()
  }

  // Indicator actions
  const handleSelectIndicator = (indicator: TechnicalIndicator) => {
    setSelectedIndicator(indicator)
    dispatch(selectIndicator(indicator))
    setShowDetails(true)
  }

  const handleToggleFavorite = (indicatorId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    dispatch(toggleFavorite(indicatorId))
    message.success('已更新收藏状态')
  }

  const handleAddToConfiguration = (indicator: TechnicalIndicator) => {
    setSelectedIndicator(indicator)
    setShowConfigPanel(true)
  }

  const handleCreateCustom = () => {
    setShowParameterForm(true)
  }

  // Pagination
  const paginatedIndicators = useMemo(() => {
    const start = (currentPage - 1) * pageSize
    const end = start + pageSize
    return filteredIndicators.slice(start, end)
  }, [filteredIndicators, currentPage, pageSize])

  // Tab content
  const getTabContent = () => {
    switch (activeTab) {
      case 'all':
        return paginatedIndicators
      case 'favorites':
        return favoriteIndicators
      case 'custom':
        return customIndicators
      default:
        // Category tabs
        const indicators = indicatorsByCategory[activeTab as IndicatorCategory] || []
        return indicators.slice(0, pageSize)
    }
  }

  const currentIndicators = getTabContent()

  if (error) {
    return (
      <div className="p-6">
        <Alert
          message="加载失败"
          description={error}
          type="error"
          showIcon
          action={
            <Button size="small" onClick={() => dispatch(fetchIndicators())}>
              重试
            </Button>
          }
        />
      </div>
    )
  }

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="mb-6">
        <div className="flex justify-between items-start">
          <div>
            <Title level={2} className="!mb-2">
              技术指标库
            </Title>
            <Paragraph className="text-gray-600 text-lg">
              探索和配置 477 种专业技术指标，构建您的交易策略
            </Paragraph>
          </div>
          <Space>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleCreateCustom}
            >
              创建自定义指标
            </Button>
            <Button icon={<FilterOutlined />} onClick={() => setShowFilter(true)}>
              高级筛选
            </Button>
          </Space>
        </div>

        {/* Quick Stats */}
        <Row gutter={16} className="mt-6">
          <Col span={6}>
            <Card size="small">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {indicators.length}
                </div>
                <Text type="secondary">总指标数</Text>
              </div>
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-600">
                  {favoriteIndicators.length}
                </div>
                <Text type="secondary">已收藏</Text>
              </div>
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {customIndicators.length}
                </div>
                <Text type="secondary">自定义指标</Text>
              </div>
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {Object.keys(indicatorsByCategory).length}
                </div>
                <Text type="secondary">指标类别</Text>
              </div>
            </Card>
          </Col>
        </Row>
      </div>

      {/* Search and Quick Filters */}
      <Card className="mb-4">
        <Row gutter={16} align="middle">
          <Col flex="auto">
            <Search
              placeholder="搜索指标名称、描述或标签..."
              value={searchTerm}
              onChange={(e) => handleSearch(e.target.value)}
              onSearch={handleSearch}
              allowClear
              size="large"
              prefix={<SearchOutlined />}
            />
          </Col>
          <Col>
            <Space>
              <Select
                placeholder="选择类别"
                style={{ width: 150 }}
                allowClear
                onChange={(value) => handleFilterChange({ category: value as IndicatorCategory })}
              >
                {Object.entries(INDICATOR_CATEGORIES).map(([key, category]) => (
                  <Select.Option key={key} value={key}>
                    <Space>
                      {category.icon && <span>{category.icon}</span>}
                      {category.name}
                    </Space>
                  </Select.Option>
                ))}
              </Select>
              <Button onClick={clearFilters} disabled={!searchTerm}>
                清除筛选
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Tabs */}
      <Card>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          tabBarExtraContent={
            <Space>
              <Badge count={filteredIndicators.length} showZero>
                <Text type="secondary">共 {filteredIndicators.length} 个结果</Text>
              </Badge>
            </Space>
          }
        >
          <TabPane
            tab={
              <span>
                <LineChartOutlined />
                全部指标
              </span>
            }
            key="all"
          />
          <TabPane
            tab={
              <span>
                <StarFilled style={{ color: '#faad14' }} />
                我的收藏
              </span>
            }
            key="favorites"
          />
          <TabPane
            tab={
              <span>
                <CodeOutlined />
                自定义指标
              </span>
            }
            key="custom"
          />

          {/* Category Tabs */}
          {Object.entries(INDICATOR_CATEGORIES).map(([key, category]) => (
            <TabPane
              tab={
                <span>
                  <span style={{ color: category.color }}>{category.icon}</span>
                  {category.name}
                  <Badge
                    count={indicatorsByCategory[key as IndicatorCategory]?.length || 0}
                    size="small"
                    className="ml-2"
                  />
                </span>
              }
              key={key}
            />
          ))}
        </Tabs>

        {/* Indicators Grid */}
        <Spin spinning={isLoading}>
          {currentIndicators.length > 0 ? (
            <>
              <Row gutter={[16, 16]}>
                {currentIndicators.map((indicator) => (
                  <Col xs={24} sm={12} lg={8} xl={6} key={indicator.id}>
                    <IndicatorCard
                      indicator={indicator}
                      onSelect={() => handleSelectIndicator(indicator)}
                      onToggleFavorite={(e) => handleToggleFavorite(indicator.id, e)}
                      onAddToConfiguration={() => handleAddToConfiguration(indicator)}
                    />
                  </Col>
                ))}
              </Row>

              {/* Pagination */}
              {activeTab === 'all' && (
                <div className="mt-6 flex justify-center">
                  <Pagination
                    current={currentPage}
                    total={filteredIndicators.length}
                    pageSize={pageSize}
                    showSizeChanger
                    showQuickJumper
                    showTotal={(total, range) =>
                      `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
                    }
                    onChange={setCurrentPage}
                    onShowSizeChange={(_, size) => setPageSize(size)}
                  />
                </div>
              )}
            </>
          ) : (
            <Empty
              description="未找到匹配的指标"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          )}
        </Spin>
      </Card>

      {/* Popular Combinations */}
      <Card title="热门组合" className="mt-4">
        <Row gutter={16}>
          {POPULAR_COMBINATIONS.map((combo) => (
            <Col xs={24} sm={12} lg={6} key={combo.id}>
              <Card
                size="small"
                hoverable
                className="h-full"
                onClick={() => {
                  // Handle combination selection
                }}
              >
                <Title level={5}>{combo.name}</Title>
                <Paragraph type="secondary" ellipsis={{ rows: 2 }}>
                  {combo.description}
                </Paragraph>
                <Space wrap>
                  {combo.indicators.map((id) => {
                    const indicator = indicators.find(ind => ind.id === id)
                    return indicator ? (
                      <Tag key={id} color="blue" size="small">
                        {indicator.name}
                      </Tag>
                    ) : null
                  })}
                </Space>
              </Card>
            </Col>
          ))}
        </Row>
      </Card>

      {/* Drawers and Modals */}
      <Drawer
        title="高级筛选"
        placement="right"
        onClose={() => setShowFilter(false)}
        open={showFilter}
        width={400}
      >
        <Form
          form={filterForm}
          layout="vertical"
          onFinish={(values) => {
            handleFilterChange(values)
            setShowFilter(false)
          }}
        >
          {/* Filter form fields */}
          <Form.Item name="favorite" valuePropName="checked">
            <Checkbox>仅显示收藏</Checkbox>
          </Form.Item>
          <Form.Item name="custom" valuePropName="checked">
            <Checkbox>仅显示自定义</Checkbox>
          </Form.Item>
          <Form.Item name="tags">
            <Select
              mode="multiple"
              placeholder="选择标签"
              options={[]}
            />
          </Form.Item>
        </Form>
      </Drawer>

      <Drawer
        title="指标详情"
        placement="right"
        onClose={() => setShowDetails(false)}
        open={showDetails}
        width={600}
      >
        {selectedIndicator && (
          <IndicatorDetails
            indicator={selectedIndicator}
            onClose={() => setShowDetails(false)}
          />
        )}
      </Drawer>

      <Modal
        title="创建自定义指标"
        open={showParameterForm}
        onCancel={() => setShowParameterForm(false)}
        footer={null}
        width={800}
      >
        <IndicatorParameterForm
          onSubmit={(indicator) => {
            // Handle custom indicator creation
            setShowParameterForm(false)
          }}
          onCancel={() => setShowParameterForm(false)}
        />
      </Modal>

      <Drawer
        title="配置面板"
        placement="right"
        onClose={() => setShowConfigPanel(false)}
        open={showConfigPanel}
        width={500}
      >
        {selectedIndicator && (
          <ConfigurationPanel
            indicators={[selectedIndicator]}
            onClose={() => setShowConfigPanel(false)}
          />
        )}
      </Drawer>
    </div>
  )
}

export default IndicatorLibraryPage
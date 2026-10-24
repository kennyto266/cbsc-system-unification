import React, { useState } from 'react'
import { Row, Col, Select, Input, DatePicker, Button, Space, AutoComplete, Tag } from 'antd'
import { SearchOutlined, FilterOutlined, ClearOutlined, DownOutlined, UpOutlined } from '@ant-design/icons'
import { StrategyStatus, StrategyType, RiskLevel } from '../../types'
import dayjs, { Dayjs } from 'dayjs'

// Styles
import './StrategyFilters.css'

const { Option } = Select
const { Search } = Input
const { RangePicker } = DatePicker

interface StrategyFiltersProps {
  filters: {
    status: StrategyStatus | 'all'
    type: StrategyType | 'all'
    riskLevel: RiskLevel | 'all'
    search: string
    dateRange: [Dayjs, Dayjs] | null
  }
  onFiltersChange: (filters: any) => void
}

const StrategyFilters: React.FC<StrategyFiltersProps> = ({
  filters,
  onFiltersChange,
}) => {
  const [expanded, setExpanded] = useState(false)
  const [quickSearchOptions, setQuickSearchOptions] = useState<string[]>([])

  // Status options
  const statusOptions = [
    { value: 'all', label: '全部狀態' },
    { value: StrategyStatus.ACTIVE, label: '運行中' },
    { value: StrategyStatus.INACTIVE, label: '已停止' },
    { value: StrategyStatus.TESTING, label: '測試中' },
    { value: StrategyStatus.ARCHIVED, label: '已歸檔' },
  ]

  // Type options
  const typeOptions = [
    { value: 'all', label: '全部類型' },
    { value: StrategyType.SENTIMENT, label: '情感分析' },
    { value: StrategyType.TECHNICAL, label: '技術分析' },
    { value: StrategyType.MOMENTUM, label: '動量策略' },
    { value: StrategyType.MEAN_REVERSION, label: '均值回歸' },
    { value: StrategyType.ARBITRAGE, label: '套利策略' },
  ]

  // Risk level options
  const riskOptions = [
    { value: 'all', label: '全部風險級別' },
    { value: RiskLevel.LOW, label: '低風險' },
    { value: RiskLevel.MEDIUM, label: '中風險' },
    { value: RiskLevel.HIGH, label: '高風險' },
  ]

  // Quick search suggestions
  const handleSearchChange = (value: string) => {
    if (value.length > 0) {
      // Simulate search suggestions
      const suggestions = [
        `${value} 策略`,
        `${value} 技術指標`,
        `${value} 回測`,
      ]
      setQuickSearchOptions(suggestions)
    } else {
      setQuickSearchOptions([])
    }
  }

  // Handle filter change
  const handleFilterChange = (key: string, value: any) => {
    onFiltersChange({
      ...filters,
      [key]: value,
    })
  }

  // Clear all filters
  const clearAllFilters = () => {
    onFiltersChange({
      status: 'all',
      type: 'all',
      riskLevel: 'all',
      search: '',
      dateRange: null,
    })
  }

  // Check if any filters are active
  const hasActiveFilters = filters.status !== 'all' ||
                          filters.type !== 'all' ||
                          filters.riskLevel !== 'all' ||
                          filters.search.length > 0 ||
                          filters.dateRange !== null

  // Render active filter tags
  const renderActiveFilters = () => {
    const tags = []

    if (filters.status !== 'all') {
      const statusLabel = statusOptions.find(o => o.value === filters.status)?.label
      tags.push(
        <Tag key="status" closable onClose={() => handleFilterChange('status', 'all')}>
          狀態: {statusLabel}
        </Tag>
      )
    }

    if (filters.type !== 'all') {
      const typeLabel = typeOptions.find(o => o.value === filters.type)?.label
      tags.push(
        <Tag key="type" closable onClose={() => handleFilterChange('type', 'all')}>
          類型: {typeLabel}
        </Tag>
      )
    }

    if (filters.riskLevel !== 'all') {
      const riskLabel = riskOptions.find(o => o.value === filters.riskLevel)?.label
      tags.push(
        <Tag key="risk" closable onClose={() => handleFilterChange('riskLevel', 'all')}>
          風險: {riskLabel}
        </Tag>
      )
    }

    if (filters.search) {
      tags.push(
        <Tag key="search" closable onClose={() => handleFilterChange('search', '')}>
          搜索: {filters.search}
        </Tag>
      )
    }

    if (filters.dateRange) {
      const [start, end] = filters.dateRange
      tags.push(
        <Tag key="date" closable onClose={() => handleFilterChange('dateRange', null)}>
          日期: {start.format('YYYY-MM-DD')} ~ {end.format('YYYY-MM-DD')}
        </Tag>
      )
    }

    return tags
  }

  return (
    <div className="strategy-filters">
      {/* Basic Filters */}
      <Row gutter={[16, 16]} className="filters-row">
        <Col xs={24} sm={12} md={6}>
          <Search
            placeholder="搜索策略名稱..."
            value={filters.search}
            onChange={(e) => {
              handleFilterChange('search', e.target.value)
              handleSearchChange(e.target.value)
            }}
            onSearch={(value) => handleFilterChange('search', value)}
            allowClear
            enterButton
          />
        </Col>

        <Col xs={24} sm={12} md={4}>
          <Select
            value={filters.status}
            onChange={(value) => handleFilterChange('status', value)}
            style={{ width: '100%' }}
            placeholder="選擇狀態"
          >
            {statusOptions.map(option => (
              <Option key={option.value} value={option.value}>
                {option.label}
              </Option>
            ))}
          </Select>
        </Col>

        <Col xs={24} sm={12} md={4}>
          <Select
            value={filters.type}
            onChange={(value) => handleFilterChange('type', value)}
            style={{ width: '100%' }}
            placeholder="選擇類型"
          >
            {typeOptions.map(option => (
              <Option key={option.value} value={option.value}>
                {option.label}
              </Option>
            ))}
          </Select>
        </Col>

        <Col xs={24} sm={12} md={4}>
          <Select
            value={filters.riskLevel}
            onChange={(value) => handleFilterChange('riskLevel', value)}
            style={{ width: '100%' }}
            placeholder="選擇風險級別"
          >
            {riskOptions.map(option => (
              <Option key={option.value} value={option.value}>
                {option.label}
              </Option>
            ))}
          </Select>
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Space>
            <Button
              type="link"
              icon={expanded ? <UpOutlined /> : <DownOutlined />}
              onClick={() => setExpanded(!expanded)}
            >
              {expanded ? '收起' : '更多篩選'}
            </Button>
            {hasActiveFilters && (
              <Button
                type="link"
                icon={<ClearOutlined />}
                onClick={clearAllFilters}
              >
                清除篩選
              </Button>
            )}
          </Space>
        </Col>
      </Row>

      {/* Expanded Filters */}
      {expanded && (
        <Row gutter={[16, 16]} className="expanded-filters">
          <Col xs={24} sm={12} md={8}>
            <label className="filter-label">創建日期範圍:</label>
            <RangePicker
              value={filters.dateRange}
              onChange={(dates) => handleFilterChange('dateRange', dates)}
              style={{ width: '100%' }}
              format="YYYY-MM-DD"
            />
          </Col>

          <Col xs={24} sm={12} md={8}>
            <label className="filter-label">性能指標:</label>
            <Select
              mode="multiple"
              placeholder="選擇性能指標"
              style={{ width: '100%' }}
              // value={filters.metrics}
              onChange={(value) => handleFilterChange('metrics', value)}
            >
              <Option value="total_return">總回報率</Option>
              <Option value="sharpe_ratio">夏普比率</Option>
              <Option value="max_drawdown">最大回撤</Option>
              <Option value="win_rate">勝率</Option>
              <Option value="profit_factor">盈利因子</Option>
            </Select>
          </Col>

          <Col xs={24} sm={12} md={8}>
            <label className="filter-label">排序方式:</label>
            <Select
              defaultValue="updated_at"
              style={{ width: '100%' }}
              // value={filters.sortBy}
              onChange={(value) => handleFilterChange('sortBy', value)}
            >
              <Option value="updated_at">最後更新時間</Option>
              <Option value="created_at">創建時間</Option>
              <Option value="total_return">總回報率</Option>
              <Option value="sharpe_ratio">夏普比率</Option>
              <Option value="win_rate">勝率</Option>
              <Option value="name">策略名稱</Option>
            </Select>
          </Col>
        </Row>
      )}

      {/* Active Filter Tags */}
      {hasActiveFilters && (
        <Row className="active-filters">
          <Col span={24}>
            <Space wrap>
              <span className="filter-label">當前篩選:</span>
              {renderActiveFilters()}
            </Space>
          </Col>
        </Row>
      )}
    </div>
  )
}

export default StrategyFilters
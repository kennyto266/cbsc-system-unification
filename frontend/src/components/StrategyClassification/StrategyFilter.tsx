import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Select,
  Slider,
  Button,
  Tag,
  Space,
  Divider,
  Collapse,
  Checkbox,
  InputNumber
} from 'antd';
import {
  FilterOutlined,
  ClearOutlined,
  SearchOutlined
} from '@ant-design/icons';
import { StrategyGrade, StrategyCategory } from '../../types/index';
import './StrategyFilter.css';

interface FilterOptions {
  categories: string[];
  grades: string[];
  risk_levels: string[];
  trading_frequencies: string[];
  min_sharpe: number | null;
  min_return: number | null;
  search_term: string;
}

interface StrategyFilterProps {
  onFilterChange: (filters: FilterOptions) => void;
  totalStrategies?: number;
  filteredCount?: number;
}

const StrategyFilter: React.FC<StrategyFilterProps> = ({
  onFilterChange,
  totalStrategies = 0,
  filteredCount = 0
}) => {
  const [filters, setFilters] = useState<FilterOptions>({
    categories: [],
    grades: [],
    risk_levels: [],
    trading_frequencies: [],
    min_sharpe: null,
    min_return: null,
    search_term: ''
  });

  const [activeFilters, setActiveFilters] = useState<string[]>([]);

  const categoryOptions = [
    { label: '月度低頻策略', value: 'monthly_low_frequency' },
    { label: '多策略驗證系統', value: 'multi_strategy_validation' },
    { label: '多因子模型', value: 'multi_factor_model' },
    { label: '核心CBSC技術分析', value: 'core_cbsc_technical' },
    { label: '核心CBSC情緒分析', value: 'core_cbsc_sentiment' },
    { label: '核心CBSC激進策略', value: 'core_cbsc_aggressive' },
    { label: '投資組合優化', value: 'portfolio_optimization' }
  ];

  const gradeOptions = [
    { label: 'A+', value: 'A+' },
    { label: 'A', value: 'A' },
    { label: 'B+', value: 'B+' },
    { label: 'B', value: 'B' },
    { label: 'C+', value: 'C+' },
    { label: 'C', value: 'C' },
    { label: 'D+', value: 'D+' },
    { label: 'D', value: 'D' },
    { label: 'F', value: 'F' }
  ];

  const riskLevelOptions = [
    { label: '低風險', value: 'low' },
    { label: '中風險', value: 'medium' },
    { label: '高風險', value: 'high' }
  ];

  const tradingFrequencyOptions = [
    { label: '低頻', value: 'low' },
    { label: '中頻', value: 'medium' },
    { label: '高頻', value: 'high' }
  ];

  useEffect(() => {
    // 通知父組件篩選變化
    onFilterChange(filters);

    // 更新活躍篩選列表
    const active = [];
    if (filters.categories.length > 0) active.push(`類別: ${filters.categories.length}`);
    if (filters.grades.length > 0) active.push(`評級: ${filters.grades.length}`);
    if (filters.risk_levels.length > 0) active.push(`風險: ${filters.risk_levels.length}`);
    if (filters.trading_frequencies.length > 0) active.push(`頻率: ${filters.trading_frequencies.length}`);
    if (filters.min_sharpe !== null) active.push(`夏普比率 ≥ ${filters.min_sharpe}`);
    if (filters.min_return !== null) active.push(`年化收益 ≥ ${(filters.min_return * 100).toFixed(0)}%`);
    if (filters.search_term) active.push(`搜索: ${filters.search_term}`);

    setActiveFilters(active);
  }, [filters, onFilterChange]);

  const handleFilterChange = (key: keyof FilterOptions, value: any) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
  };

  const clearAllFilters = () => {
    setFilters({
      categories: [],
      grades: [],
      risk_levels: [],
      trading_frequencies: [],
      min_sharpe: null,
      min_return: null,
      search_term: ''
    });
  };

  const clearFilter = (key: keyof FilterOptions) => {
    const defaultValues: Partial<FilterOptions> = {
      categories: [],
      grades: [],
      risk_levels: [],
      trading_frequencies: [],
      min_sharpe: null,
      min_return: null,
      search_term: ''
    };
    handleFilterChange(key, defaultValues[key] || (key === 'search_term' ? '' : null));
  };

  const getFilterCount = () => {
    let count = 0;
    if (filters.categories.length > 0) count += filters.categories.length;
    if (filters.grades.length > 0) count += filters.grades.length;
    if (filters.risk_levels.length > 0) count += filters.risk_levels.length;
    if (filters.trading_frequencies.length > 0) count += filters.trading_frequencies.length;
    if (filters.min_sharpe !== null) count += 1;
    if (filters.min_return !== null) count += 1;
    if (filters.search_term) count += 1;
    return count;
  };

  const presetFilters = [
    {
      name: '優質策略',
      description: '夏普比率 > 1.0 的策略',
      filters: {
        categories: [],
        grades: ['A+', 'A', 'B+'],
        risk_levels: [],
        trading_frequencies: [],
        min_sharpe: 1.0,
        min_return: null,
        search_term: ''
      }
    },
    {
      name: '低風險策略',
      description: '風險級別為低的策略',
      filters: {
        categories: [],
        grades: [],
        risk_levels: ['low'],
        trading_frequencies: [],
        min_sharpe: null,
        min_return: null,
        search_term: ''
      }
    },
    {
      name: '高收益策略',
      description: '年化收益率 > 15% 的策略',
      filters: {
        categories: [],
        grades: [],
        risk_levels: [],
        trading_frequencies: [],
        min_sharpe: null,
        min_return: 0.15,
        search_term: ''
      }
    }
  ];

  const applyPreset = (preset: typeof presetFilters[0]) => {
    setFilters(preset.filters);
  };

  const presetColors = {
    '優質策略': '#52c41a',
    '低風險策略': '#1890ff',
    '高收益策略': '#faad14'
  };

  return (
    <div className="strategy-filter">
      <Card>
        <div className="filter-header">
          <div className="filter-title">
            <FilterOutlined />
            <span>策略篩選</span>
            {getFilterCount() > 0 && (
              <Tag color="blue" className="filter-count">
                {getFilterCount()} 個篩選條件
              </Tag>
            )}
          </div>
          <div className="filter-actions">
            <Button
              type="text"
              icon={<ClearOutlined />}
              onClick={clearAllFilters}
              disabled={getFilterCount() === 0}
            >
              清除全部
            </Button>
          </div>
        </div>

        <div className="filter-content">
          {/* 快速篩選 */}
          <div className="quick-filters">
            <div className="quick-filters-title">快速篩選:</div>
            <div className="preset-buttons">
              {presetFilters.map((preset) => (
                <Button
                  key={preset.name}
                  size="small"
                  onClick={() => applyPreset(preset)}
                  style={{
                    borderColor: presetColors[preset.name],
                    color: presetColors[preset.name]
                  }}
                >
                  {preset.name}
                </Button>
              ))}
            </div>
          </div>

          <Divider />

          {/* 篩選條件 */}
          <Collapse
            items={[
              {
                key: 'basic',
                label: '基本篩選',
                children: (
                  <div className="filter-section">
                    <Row gutter={[16, 16]}>
                      <Col xs={24} sm={12} md={8}>
                        <div className="filter-item">
                          <label className="filter-label">類別</label>
                          <Select
                            mode="multiple"
                            placeholder="選擇策略類別"
                            value={filters.categories}
                            onChange={(value) => handleFilterChange('categories', value)}
                            style={{ width: '100%' }}
                            options={categoryOptions}
                          />
                        </div>
                      </Col>
                      <Col xs={24} sm={12} md={8}>
                        <div className="filter-item">
                          <label className="filter-label">評級</label>
                          <Select
                            mode="multiple"
                            placeholder="選擇策略評級"
                            value={filters.grades}
                            onChange={(value) => handleFilterChange('grades', value)}
                            style={{ width: '100%' }}
                            options={gradeOptions}
                          />
                        </div>
                      </Col>
                      <Col xs={24} sm={12} md={8}>
                        <div className="filter-item">
                          <label className="filter-label">風險級別</label>
                          <Select
                            mode="multiple"
                            placeholder="選擇風險級別"
                            value={filters.risk_levels}
                            onChange={(value) => handleFilterChange('risk_levels', value)}
                            style={{ width: '100%' }}
                            options={riskLevelOptions}
                          />
                        </div>
                      </Col>
                    </Row>
                    <Row gutter={[16, 16]}>
                      <Col xs={24} sm={12}>
                        <div className="filter-item">
                          <label className="filter-label">交易頻率</label>
                          <Select
                            mode="multiple"
                            placeholder="選擇交易頻率"
                            value={filters.trading_frequencies}
                            onChange={(value) => handleFilterChange('trading_frequencies', value)}
                            style={{ width: '100%' }}
                            options={tradingFrequencyOptions}
                          />
                        </div>
                      </Col>
                      <Col xs={24} sm={12}>
                        <div className="filter-item">
                          <label className="filter-label">搜索策略</label>
                          <input
                            type="text"
                            placeholder="搜索策略名稱..."
                            value={filters.search_term}
                            onChange={(e) => handleFilterChange('search_term', e.target.value)}
                            style={{ width: '100%' }}
                            className="search-input"
                          />
                        </div>
                      </Col>
                    </Row>
                  </div>
                )
              },
              {
                key: 'performance',
                label: '性能指標',
                children: (
                  <div className="filter-section">
                    <Row gutter={[16, 16]}>
                      <Col xs={24} md={12}>
                        <div className="filter-item">
                          <label className="filter-label">
                            最小夏普比率: {filters.min_sharpe ? filters.min_sharpe.toFixed(2) : '不限'}
                          </label>
                          <Slider
                            min={-2}
                            max={5}
                            step={0.1}
                            value={filters.min_sharpe || 0}
                            onChange={(value) => handleFilterChange('min_sharpe', value)}
                            marks={{
                              '-2': '-2',
                              '0': '0',
                              '1': '1',
                              '2': '2',
                              '3': '3',
                              '4': '4',
                              '5': '5'
                            }}
                          />
                        </div>
                      </Col>
                      <Col xs={24} md={12}>
                        <div className="filter-item">
                          <label className="filter-label">
                            最小年化收益: {filters.min_return ? `${(filters.min_return * 100).toFixed(0)}%` : '不限'}
                          </label>
                          <Slider
                            min={-0.5}
                            max={1.0}
                            step={0.01}
                            value={filters.min_return || 0}
                            onChange={(value) => handleFilterChange('min_return', value)}
                            marks={{
                              '-0.5': '-50%',
                              '0': '0%',
                              '0.1': '10%',
                              '0.2': '20%',
                              '0.3': '30%',
                              '0.5': '50%',
                              '1.0': '100%'
                            }}
                          />
                        </div>
                      </Col>
                    </Row>
                  </div>
                )
              }
            ]}
          />
        </div>

        {/* 活躍篩選標籤 */}
        {activeFilters.length > 0 && (
          <div className="active-filters">
            <div className="active-filters-title">當前篩選:</div>
            <div className="active-filter-tags">
              {activeFilters.map((filter, index) => (
                <Tag
                  key={index}
                  closable
                  color="blue"
                  onClose={() => {
                    // 根據標籤內容確定要清除的篩選
                    if (filter.includes('類別:')) {
                      handleFilterChange('categories', []);
                    } else if (filter.includes('評級:')) {
                      handleFilterChange('grades', []);
                    } else if (filter.includes('風險:')) {
                      handleFilterChange('risk_levels', []);
                    } else if (filter.includes('頻率:')) {
                      handleFilterChange('trading_frequencies', []);
                    } else if (filter.includes('夏普比率')) {
                      handleFilterChange('min_sharpe', null);
                    } else if (filter.includes('年化收益')) {
                      handleFilterChange('min_return', null);
                    } else if (filter.includes('搜索:')) {
                      handleFilterChange('search_term', '');
                    }
                  }}
                >
                  {filter}
                </Tag>
              ))}
            </div>
          </div>
        )}

        {/* 篩選結果統計 */}
        <div className="filter-summary">
          <Space size="large">
            <div className="summary-item">
              <span className="summary-label">總策略數:</span>
              <span className="summary-value">{totalStrategies}</span>
            </div>
            <div className="summary-item">
              <span className="summary-label">篩選結果:</span>
              <span className="summary-value filtered-count">{filteredCount}</span>
            </div>
            {totalStrategies > 0 && (
              <div className="summary-item">
                <span className="summary-label">篩選比例:</span>
                <span className="summary-value">
                  {((filteredCount / totalStrategies) * 100).toFixed(1)}%
                </span>
              </div>
            )}
          </Space>
        </div>
      </Card>
    </div>
  );
};

export default StrategyFilter;
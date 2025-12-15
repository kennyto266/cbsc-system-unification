import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Tag, Button, Tooltip } from 'antd';
import {
  CalendarOutlined,
  VerifiedOutlined,
  AnalyticsOutlined,
  RiseOutlined,
  PsychologyOutlined,
  SpeedOutlined,
  PieChartOutlined,
  FilterOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import './StrategyCategories.css';

interface Strategy {
  name: string;
  grade: string;
  annual_return: number;
  sharpe_ratio: number;
  risk_level: string;
}

interface Category {
  category: string;
  display_name: string;
  description: string;
  color: string;
  icon: string;
  strategies_count: number;
  strategies: Strategy[];
  statistics?: {
    avg_annual_return: number;
    avg_sharpe_ratio: number;
    grade_distribution: Record<string, number>;
    best_strategy: string;
  };
}

interface StrategyCategoriesProps {
  onCategorySelect?: (category: string) => void;
  onFilterChange?: (filters: any) => void;
}

const StrategyCategories: React.FC<StrategyCategoriesProps> = ({
  onCategorySelect,
  onFilterChange
}) => {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    fetchCategories();
  }, []);

  const fetchCategories = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/strategies/classification/categories');
      const data = await response.json();

      if (data.success) {
        setCategories(data.data);
      }
    } catch (error) {
      console.error('Failed to fetch categories:', error);
    } finally {
      setLoading(false);
    }
  };

  const getGradeColor = (grade: string): string => {
    const gradeColors: Record<string, string> = {
      'A+': '#52c41a',
      'A': '#73d13d',
      'B+': '#95de64',
      'B': '#b7eb8f',
      'C+': '#ffd666',
      'C': '#ffccc7',
      'D+': '#ff9c6e',
      'D': '#ff7875',
      'F': '#ff4d4f'
    };
    return gradeColors[grade] || '#d9d9d9';
  };

  const getRiskLevelColor = (level: string): string => {
    const riskColors: Record<string, string> = {
      'low': '#52c41a',
      'medium': '#faad14',
      'high': '#f5222d'
    };
    return riskColors[level] || '#d9d9d9';
  };

  const getRiskLevelText = (level: string): string => {
    const riskText: Record<string, string> = {
      'low': '低風險',
      'medium': '中風險',
      'high': '高風險'
    };
    return riskText[level] || '未知';
  };

  const getIcon = (iconName: string) => {
    const icons: Record<string, React.ReactNode> = {
      'calendar_month': <CalendarOutlined />,
      'verified': <VerifiedOutlined />,
      'analytics': <AnalyticsOutlined />,
      'trending_up': <RiseOutlined />,
      'psychology': <PsychologyOutlined />,
      'speed': <SpeedOutlined />,
      'pie_chart': <PieChartOutlined />
    };
    return icons[iconName] || <AnalyticsOutlined />;
  };

  const handleCategoryClick = (category: Category) => {
    const newSelected = selectedCategories.includes(category.category)
      ? selectedCategories.filter(c => c !== category.category)
      : [...selectedCategories, category.category];

    setSelectedCategories(newSelected);

    // 通知父組件篩選變化
    if (onFilterChange) {
      onFilterChange({
        categories: newSelected,
        strategies: newSelected.length === 1 ? category.strategies.map(s => s.name) : []
      });
    }
  };

  const handleStrategyClick = (strategyName: string) => {
    if (onCategorySelect) {
      onCategorySelect(strategyName);
    } else {
      navigate(`/strategies/${strategyName}`);
    }
  };

  const getTopStrategies = (category: Category): Strategy[] => {
    return category.strategies
      .filter(s => s.sharpe_ratio > 0 && s.sharpe_ratio < 100)
      .sort((a, b) => b.sharpe_ratio - a.sharpe_ratio)
      .slice(0, 3);
  };

  const renderStatistics = (statistics: Category['statistics']) => {
    if (!statistics) return null;

    return (
      <div className="category-statistics">
        <Row gutter={[8, 8]}>
          <Col span={8}>
            <Statistic
              title="平均年化收益"
              value={statistics.avg_annual_return * 100}
              precision={2}
              suffix="%"
              valueStyle={{ color: '#3f8600' }}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="平均夏普比率"
              value={statistics.avg_sharpe_ratio}
              precision={2}
              valueStyle={{ color: '#3f8600' }}
            />
          </Col>
          <Col span={8}>
            <div className="best-strategy">
              <div className="statistic-title">最佳策略</div>
              <div className="best-strategy-name">
                <Tooltip title={statistics.best_strategy}>
                  {statistics.best_strategy.length > 15
                    ? `${statistics.best_strategy.substring(0, 15)}...`
                    : statistics.best_strategy
                  }
                </Tooltip>
              </div>
            </div>
          </Col>
        </Row>
      </div>
    );
  };

  const renderGradeDistribution = (gradeDistribution: Record<string, number>) => {
    const grades = ['A+', 'A', 'B+', 'B', 'C+', 'C', 'D+', 'D', 'F'];
    const total = Object.values(gradeDistribution).reduce((sum, count) => sum + count, 0);

    return (
      <div className="grade-distribution">
        <div className="statistic-title">評級分佈</div>
        <div className="grade-bars">
          {grades.map(grade => {
            const count = gradeDistribution[grade] || 0;
            const percentage = total > 0 ? (count / total) * 100 : 0;

            return (
              <div key={grade} className="grade-bar-item">
                <div className="grade-bar-label">
                  <Tag color={getGradeColor(grade)}>{grade}</Tag>
                  <span className="count">{count}</span>
                </div>
                <div className="grade-bar-track">
                  <div
                    className="grade-bar-fill"
                    style={{
                      width: `${percentage}%`,
                      backgroundColor: getGradeColor(grade)
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const renderTopStrategies = (category: Category) => {
    const topStrategies = getTopStrategies(category);

    return (
      <div className="top-strategies">
        <div className="statistic-title">熱門策略</div>
        <div className="strategy-list">
          {topStrategies.map((strategy, index) => (
            <div
              key={strategy.name}
              className="strategy-item"
              onClick={() => handleStrategyClick(strategy.name)}
            >
              <div className="strategy-rank">#{index + 1}</div>
              <div className="strategy-info">
                <div className="strategy-name">{strategy.name}</div>
                <div className="strategy-metrics">
                  <Tag color="green">夏普: {strategy.sharpe_ratio.toFixed(2)}</Tag>
                  <Tag color="blue">收益: {(strategy.annual_return * 100).toFixed(1)}%</Tag>
                  <Tag color={getRiskLevelColor(strategy.risk_level)}>
                    {getRiskLevelText(strategy.risk_level)}
                  </Tag>
                </div>
              </div>
              <div className="strategy-grade">
                <Tag color={getGradeColor(strategy.grade)}>{strategy.grade}</Tag>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  if (loading) {
    return <div className="strategy-categories-loading">載入中...</div>;
  }

  return (
    <div className="strategy-categories">
      <div className="categories-header">
        <div className="header-title">
          <h2>策略分類</h2>
          <p className="header-description">
            按類別查看所有CBSC量化交易策略，了解不同類型策略的表現和特點
          </p>
        </div>
        <div className="header-actions">
          <Button
            type="primary"
            icon={<FilterOutlined />}
            onClick={() => onFilterChange?.({ categories: [], strategies: [] })}
          >
            清除篩選
          </Button>
          <Button
            type="default"
            onClick={() => navigate('/strategies/all')}
          >
            查看全部策略
          </Button>
        </div>
      </div>

      <div className="categories-grid">
        {categories.map((category, index) => {
          const isSelected = selectedCategories.includes(category.category);

          return (
            <Card
              key={category.category}
              className={`category-card ${isSelected ? 'selected' : ''}`}
              hoverable
              onClick={() => handleCategoryClick(category)}
            >
              <div className="category-header">
                <div className="category-icon" style={{ color: category.color }}>
                  {getIcon(category.icon)}
                </div>
                <div className="category-title">
                  <h3>{category.display_name}</h3>
                  <div className="category-count">
                    {category.strategies_count} 個策略
                  </div>
                </div>
                <div className="category-selection">
                  {isSelected && <Tag color="blue">已選擇</Tag>}
                </div>
              </div>

              <div className="category-description">
                {category.description}
              </div>

              {category.statistics && renderStatistics(category.statistics)}

              {category.statistics?.grade_distribution &&
                renderGradeDistribution(category.statistics.grade_distribution)}

              {category.strategies.length > 0 && renderTopStrategies(category)}

              <div className="category-footer">
                <Button
                  type="link"
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation();
                    navigate(`/categories/${category.category}`);
                  }}
                >
                  查看詳情 →
                </Button>
              </div>
            </Card>
          );
        })}
      </div>

      {selectedCategories.length > 0 && (
        <div className="selected-summary">
          <div className="summary-content">
            <h3>已選擇 {selectedCategories.length} 個類別</h3>
            <div className="selected-categories">
              {selectedCategories.map(cat => (
                <Tag
                  key={cat}
                  closable
                  onClose={() => handleCategoryClick(
                    categories.find(c => c.category === cat)!
                  )}
                >
                  {categories.find(c => c.category === cat)?.display_name || cat}
                </Tag>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StrategyCategories;
import React, { useState, useEffect } from 'react';
import { Layout, Row, Col, Card, Typography, Space, message } from 'antd';
import { BrowserRouter as Router, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import StrategyCategories from '../components/StrategyClassification/StrategyCategories';
import StrategyFilter from '../components/StrategyClassification/StrategyFilter';
import StrategyList from '../components/StrategyClassification/StrategyList';
import { useStrategyClassification } from '../hooks/useStrategyClassification';
import './StrategyClassificationPage.css';

const { Header, Content, Sider } = Layout;
const { Title } = Typography;

const StrategyClassificationPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [activeFilters, setActiveFilters] = useState<any>({});

  const {
    categories,
    summary,
    filteredStrategies,
    loading,
    error,
    refetchData
  } = useStrategyClassification();

  useEffect(() => {
    // 根據URL參數初始化狀態
    const params = new URLSearchParams(location.search);
    const categoryParam = params.get('category');
    const strategyParam = params.get('strategy');

    if (categoryParam) {
      setSelectedCategory(categoryParam);
    }
    if (strategyParam) {
      navigate(`/strategies/${strategyParam}`);
    }
  }, [location.search, navigate]);

  const handleCategorySelect = (categoryOrStrategy: string) => {
    // 檢查是否為策略名稱或類別
    const isStrategy = categories.some(cat =>
      cat.strategies.some(strategy => strategy.name === categoryOrStrategy)
    );

    if (isStrategy) {
      navigate(`/strategies/${categoryOrStrategy}`, {
        state: { from: 'classification' }
      });
    } else {
      setSelectedCategory(categoryOrStrategy);
      navigate(`/classification?category=${categoryOrStrategy}`, {
        state: { from: 'classification' }
      });
    }
  };

  const handleFilterChange = (filters: any) => {
    setActiveFilters(filters);

    // 更新URL參數
    const params = new URLSearchParams();

    if (filters.categories?.length > 0) {
      params.set('categories', filters.categories.join(','));
    }
    if (filters.grades?.length > 0) {
      params.set('grades', filters.grades.join(','));
    }
    if (filters.risk_levels?.length > 0) {
      params.set('risk_levels', filters.risk_levels.join(','));
    }
    if (filters.trading_frequencies?.length > 0) {
      params.set('frequencies', filters.trading_frequencies.join(','));
    }
    if (filters.min_sharpe !== null) {
      params.set('min_sharpe', filters.min_sharpe.toString());
    }
    if (filters.min_return !== null) {
      params.set('min_return', filters.min_return.toString());
    }
    if (filters.search_term) {
      params.set('search', filters.search_term);
    }

    const newUrl = params.toString();
    navigate(`/classification${newUrl ? '?' + newUrl : ''}`, { replace: true });
  };

  const handleBackToCategories = () => {
    setSelectedCategory(null);
    navigate('/classification');
  };

  const handleViewAllStrategies = () => {
    navigate('/strategies/all');
  };

  const handleExportData = () => {
    // 實現數據導出功能
    if (filteredStrategies.length === 0) {
      message.warning('沒有可導出的策略數據');
      return;
    }

    const csvContent = [
      ['策略名稱', '類別', '子類別', '年化收益', '夏普比率', '最大回撤', '勝率', '風險級別', '評級'],
      ...filteredStrategies.map(strategy => [
        strategy.name,
        strategy.category,
        strategy.subcategory,
        (strategy.annual_return * 100).toFixed(2) + '%',
        strategy.sharpe_ratio?.toFixed(2) || 'N/A',
        (strategy.max_drawdown * 100).toFixed(2) + '%',
        (strategy.win_rate * 100).toFixed(1) + '%',
        strategy.risk_level,
        strategy.grade
      ])
    ].map(row => row.join(','));

    const blob = new Blob([csvContent.join('\n')], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `strategies_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    URL.revokeObjectURL(url);

    message.success('策略數據已導出');
  };

  const handleRefresh = () => {
    refetchData();
    message.success('數據已刷新');
  };

  const getBreadcrumbs = () => {
    const crumbs = [
      { title: '首頁', path: '/' },
      { title: '策略分類', path: '/classification' }
    ];

    if (selectedCategory) {
      crumbs.push({
        title: selectedCategory,
        path: `/classification?category=${selectedCategory}`
      });
    }

    return crumbs;
  };

  return (
    <Router>
      <Layout className="strategy-classification-page">
        <Sider
          trigger={null}
          collapsible
          collapsed={collapsed}
          onCollapse={setCollapsed}
          width={250}
          theme={{
            token: {
              colorBgContainer: '#ffffff',
            },
          }}
          className="classification-sider"
        >
          <div className="sider-content">
            <div className="sider-header">
              <div className="sider-title">
                <Title level={4} style={{ color: '#1890ff', margin: 0 }}>
                  策略分類
                </Title>
                {summary && (
                  <div className="sider-summary">
                    <div className="summary-item">
                      <span className="summary-label">總策略</span>
                      <span className="summary-value">{summary.total_strategies}</span>
                    </div>
                    <div className="summary-item">
                      <span className="summary-label">最佳策略</span>
                      <span className="summary-value best-strategy">
                        {summary.performance_stats.best_overall_strategy}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="sider-actions">
              <button
                className="sider-action-btn"
                onClick={handleViewAllStrategies}
              >
                查看全部策略
              </button>
              <button
                className="sider-action-btn"
                onClick={handleExportData}
              >
                導出數據
              </button>
              <button
                className="sider-action-btn"
                onClick={handleRefresh}
              >
                刷新
              </button>
            </div>

            {summary?.grade_distribution && (
              <div className="sider-stats">
                <Title level={5}>評級分佈</Title>
                <div className="grade-stats">
                  {Object.entries(summary.grade_distribution).map(([grade, count]) => (
                    <div key={grade} className="grade-stat-item">
                      <div className={`grade-indicator grade-${grade.toLowerCase()}`}>
                        <span className="grade-label">{grade}</span>
                      </div>
                      <div className="grade-count">{count}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {summary?.category_distribution && (
              <div className="sider-stats">
                <Title level={5}>類別分佈</Title>
                <div className="category-stats">
                  {Object.entries(summary.category_distribution).map(([category, count]) => (
                    <div key={category} className="category-stat-item">
                      <span className="category-name">{category}</span>
                      <span className="category-count">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </Sider>

        <Layout className="classification-layout">
          <Content className="classification-content">
            <div className="content-header">
              <div className="header-breadcrumbs">
                {getBreadcrumbs().map((crumb, index) => (
                  <React.Fragment key={index}>
                    {index > 0 && <span className="breadcrumb-separator">/</span>}
                    <button
                      className="breadcrumb-item"
                      onClick={() => navigate(crumb.path)}
                    >
                      {crumb.title}
                    </button>
                  </React.Fragment>
                ))}
              </div>
            </div>

            <div className="content-body">
              <Row gutter={[24, 24]}>
                <Col span={24}>
                  <StrategyFilter
                    onFilterChange={handleFilterChange}
                    totalStrategies={summary?.total_strategies || 0}
                    filteredCount={filteredStrategies.length}
                  />
                </Col>
              </Row>

              <Row gutter={[24, 24]}>
                <Col span={24}>
                  {selectedCategory ? (
                    <StrategyList
                      category={selectedCategory}
                      filters={activeFilters}
                      onBack={handleBackToCategories}
                    />
                  ) : (
                    <StrategyCategories
                      onCategorySelect={handleCategorySelect}
                      onFilterChange={handleFilterChange}
                    />
                  )}
                </Col>
              </Row>
            </div>
          </Content>
        </Layout>
      </Layout>
    </Router>
  );
};

export default StrategyClassificationPage;
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Strategy, PersonalStrategyConfig, UserPortfolio, DashboardMetrics, StrategyFilter } from '../../types/index';
import { useStrategyData } from '../../hooks/useStrategyData';
import { useWebSocket } from '../../hooks/useWebSocket';

// Components
import { PortfolioOverview } from './PortfolioOverview';
import { StrategyGrid } from './StrategyGrid';
import { PersonalStrategyCard } from './PersonalStrategyCard';
import { PerformanceChart } from './PerformanceChart';
import { RiskAnalysis } from './RiskAnalysis';
import { PersonalizationPanel } from './PersonalizationPanel';
import { QuickActions } from './QuickActions';
import { NotificationCenter } from './NotificationCenter';

// UI Components
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { Card } from '../ui/Card';
import { Input } from '../ui/Input';
import { Select } from '../ui/Select';
import { Modal } from '../ui/Modal';
import { LoadingSpinner } from '../ui/LoadingSpinner';

interface PersonalStrategyDashboardProps {
  userId: string;
  apiUrl?: string;
  wsUrl?: string;
  theme?: 'light' | 'dark' | 'auto';
  onThemeChange?: (theme: 'light' | 'dark' | 'auto') => void;
}

export const PersonalStrategyDashboard: React.FC<PersonalStrategyDashboardProps> = ({
  userId,
  apiUrl = '/api',
  wsUrl = 'ws://localhost:3003/ws',
  theme = 'light',
  onThemeChange
}) => {
  // State Management
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [personalStrategies, setPersonalStrategies] = useState<Strategy[]>([]);
  const [portfolio, setPortfolio] = useState<UserPortfolio | null>(null);
  const [filters, setFilters] = useState<StrategyFilter>({
    category: 'all',
    status: 'active',
    performance: 'all',
    riskLevel: 'all'
  });
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null);
  const [isPersonalizationOpen, setIsPersonalizationOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [timeRange, setTimeRange] = useState<'1d' | '1w' | '1m' | '3m'>('1m');

  // Custom Hooks
  const {
    strategies: apiStrategies,
    performance,
    loading: strategiesLoading,
    error: strategiesError,
    refetch
  } = useStrategyData(`${apiUrl}/strategies`);

  const {
    connectionStatus,
    lastMessage,
    sendMessage
  } = useWebSocket(`${wsUrl}/personal/${userId}`);

  // WebSocket Message Handling
  useEffect(() => {
    if (lastMessage) {
      try {
        const data = JSON.parse(lastMessage.data);

        switch (data.type) {
          case 'personal_strategy_update':
            handlePersonalStrategyUpdate(data.strategy);
            break;
          case 'portfolio_update':
            handlePortfolioUpdate(data.portfolio);
            break;
          case 'new_personal_signal':
            handleNewPersonalSignal(data.signal);
            break;
          case 'risk_alert':
            handleRiskAlert(data.alert);
            break;
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    }
  }, [lastMessage]);

  // Data Processing
  const dashboardMetrics = useMemo((): DashboardMetrics => {
    if (!portfolio) return {
      totalValue: 0,
      dailyChange: 0,
      dailyChangePercent: 0,
      totalReturn: 0,
      sharpeRatio: 0,
      activeStrategies: 0,
      totalSignals: 0,
      winRate: 0,
      portfolioHealth: 'fair'
    };

    const activeStrategies = personalStrategies.filter(s => s.status === 'active').length;
    const totalReturn = portfolio.performanceHistory[portfolio.performanceHistory.length - 1]?.cumulativeReturn || 0;
    const dailyReturn = portfolio.performanceHistory[portfolio.performanceHistory.length - 1]?.dailyReturn || 0;

    return {
      totalValue: portfolio.totalValue,
      dailyChange: dailyReturn * portfolio.totalValue,
      dailyChangePercent: dailyReturn * 100,
      totalReturn: totalReturn * 100,
      sharpeRatio: portfolio.riskMetrics.sharpeRatio || 0,
      activeStrategies,
      totalSignals: 0, // Calculate from signal history
      winRate: 0, // Calculate from execution history
      portfolioHealth: totalReturn > 0.1 ? 'excellent' : totalReturn > 0 ? 'good' : 'fair'
    };
  }, [portfolio, personalStrategies]);

  // Filtered Strategies
  const filteredStrategies = useMemo(() => {
    let filtered = personalStrategies.filter(strategy => strategy.personalConfig);

    if (searchTerm) {
      filtered = filtered.filter(strategy =>
        strategy.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        strategy.description.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (filters.category !== 'all') {
      filtered = filtered.filter(strategy => strategy.category === filters.category);
    }

    if (filters.status !== 'all') {
      filtered = filtered.filter(strategy => strategy.status === filters.status);
    }

    if (filters.riskLevel !== 'all') {
      filtered = filtered.filter(strategy => strategy.riskLevel === filters.riskLevel);
    }

    return filtered;
  }, [personalStrategies, searchTerm, filters]);

  // Event Handlers
  const handlePersonalStrategyUpdate = useCallback((updatedStrategy: Strategy) => {
    setPersonalStrategies(prev =>
      prev.map(strategy =>
        strategy.id === updatedStrategy.id
          ? { ...strategy, ...updatedStrategy }
          : strategy
      )
    );
  }, []);

  const handlePortfolioUpdate = useCallback((updatedPortfolio: UserPortfolio) => {
    setPortfolio(updatedPortfolio);
  }, []);

  const handleNewPersonalSignal = useCallback((signal: any) => {
    // Handle new personal trading signals
    console.log('New personal signal:', signal);
  }, []);

  const handleRiskAlert = useCallback((alert: any) => {
    // Handle risk alerts
    console.log('Risk alert:', alert);
  }, []);

  const handleStrategyPersonalization = useCallback((strategy: Strategy) => {
    setSelectedStrategy(strategy);
    setIsPersonalizationOpen(true);
  }, []);

  const handleFilterChange = useCallback((newFilters: Partial<StrategyFilter>) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
  }, []);

  // Data Loading
  useEffect(() => {
    const loadPersonalData = async () => {
      try {
        setIsLoading(true);
        setError(null);

        // Load available strategies
        if (apiStrategies) {
          setStrategies(apiStrategies);
        }

        // Load user's personalized strategies
        const personalResponse = await fetch(`${apiUrl}/users/${userId}/strategies`);
        if (personalResponse.ok) {
          const personalData = await personalResponse.json();
          setPersonalStrategies(personalData.strategies);
        }

        // Load portfolio data
        const portfolioResponse = await fetch(`${apiUrl}/users/${userId}/portfolio`);
        if (portfolioResponse.ok) {
          const portfolioData = await portfolioResponse.json();
          setPortfolio(portfolioData);
        }

      } catch (err) {
        console.error('Failed to load personal data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load data');
      } finally {
        setIsLoading(false);
      }
    };

    loadPersonalData();
  }, [userId, apiUrl, apiStrategies]);

  // Loading State
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-neutral-50">
        <div className="text-center">
          <LoadingSpinner size="lg" className="mx-auto mb-4" />
          <p className="text-neutral-600">加载个人策略数据中...</p>
        </div>
      </div>
    );
  }

  // Error State
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-neutral-50">
        <Card className="max-w-md text-center">
          <div className="text-error-600 mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.314 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-neutral-900 mb-2">加载失败</h3>
          <p className="text-neutral-600 mb-4">{error}</p>
          <Button onClick={() => window.location.reload()} className="btn-primary">
            重新加载
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-neutral-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div>
              <h1 className="text-2xl font-bold text-neutral-900">个人策略管理</h1>
              <p className="text-sm text-neutral-500">定制和管理您的个人量化交易策略</p>
            </div>
            <div className="flex items-center space-x-4">
              <Badge
                variant={connectionStatus === 'connected' ? 'success' : 'error'}
              >
                {connectionStatus === 'connected' ? '实时连接' : '连接断开'}
              </Badge>
              <QuickActions
                onRefresh={() => refetch()}
                onPersonalize={() => setIsPersonalizationOpen(true)}
              />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Portfolio Overview */}
        <PortfolioOverview
          portfolio={portfolio}
          metrics={dashboardMetrics}
          onTimeRangeChange={setTimeRange}
          currentRange={timeRange}
        />

        {/* Performance Chart */}
        <div className="mb-8">
          <PerformanceChart
            portfolio={portfolio}
            timeRange={timeRange}
          />
        </div>

        {/* Search and Filters */}
        <div className="mb-6 space-y-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <Input
                placeholder="搜索策略..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full"
              />
            </div>
            <div className="flex gap-2">
              <Select
                value={filters.category}
                onChange={(value) => handleFilterChange({ category: value })}
                options={[
                  { value: 'all', label: '所有类别' },
                  { value: 'core_cbsc', label: '核心CBSC' },
                  { value: 'multi_factor', label: '多因子' },
                  { value: 'other', label: '其他' }
                ]}
              />
              <Select
                value={filters.status}
                onChange={(value) => handleFilterChange({ status: value })}
                options={[
                  { value: 'all', label: '所有状态' },
                  { value: 'active', label: '活跃' },
                  { value: 'inactive', label: '暂停' },
                  { value: 'testing', label: '测试' }
                ]}
              />
              <Select
                value={filters.riskLevel}
                onChange={(value) => handleFilterChange({ riskLevel: value })}
                options={[
                  { value: 'all', label: '所有风险' },
                  { value: 'low', label: '低风险' },
                  { value: 'medium', label: '中等风险' },
                  { value: 'high', label: '高风险' }
                ]}
              />
            </div>
          </div>
        </div>

        {/* Personal Strategy Grid */}
        <div className="grid-responsive mb-8">
          {filteredStrategies.map((strategy) => (
            <PersonalStrategyCard
              key={strategy.id}
              strategy={strategy}
              onPersonalize={handleStrategyPersonalization}
              onSelect={setSelectedStrategy}
            />
          ))}
        </div>

        {/* Empty State */}
        {filteredStrategies.length === 0 && !isLoading && (
          <div className="text-center py-12">
            <div className="text-neutral-400 mb-4">
              <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-neutral-900 mb-2">
              {searchTerm ? '未找到匹配的策略' : '还没有个性化策略'}
            </h3>
            <p className="text-neutral-600 mb-4">
              {searchTerm ? '尝试调整搜索条件或筛选器' : '开始创建您的第一个个性化策略'}
            </p>
            {!searchTerm && (
              <Button
                onClick={() => setIsPersonalizationOpen(true)}
                className="btn-primary"
              >
                创建个性化策略
              </Button>
            )}
          </div>
        )}

        {/* Risk Analysis */}
        <RiskAnalysis
          portfolio={portfolio}
          strategies={personalStrategies}
        />

        {/* Notification Center */}
        <NotificationCenter
          userId={userId}
          apiUrl={apiUrl}
        />
      </main>

      {/* Personalization Modal */}
      <Modal
        isOpen={isPersonalizationOpen}
        onClose={() => setIsPersonalizationOpen(false)}
        title="策略个性化设置"
        size="lg"
      >
        <PersonalizationPanel
          strategy={selectedStrategy}
          userId={userId}
          apiUrl={apiUrl}
          onSave={(config) => {
            // Handle save
            setIsPersonalizationOpen(false);
          }}
          onCancel={() => setIsPersonalizationOpen(false)}
        />
      </Modal>
    </div>
  );
};
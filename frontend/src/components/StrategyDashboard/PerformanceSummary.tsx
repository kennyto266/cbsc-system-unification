import React from 'react';
import { Strategy, PerformanceSummary } from '../../types/strategy';

interface PerformanceSummaryProps {
  strategies: Strategy[];
}

export const PerformanceSummary: React.FC<PerformanceSummaryProps> = ({ strategies }) => {
  // Calculate summary metrics
  const calculateSummary = (): PerformanceSummary => {
    const activeStrategies = strategies.filter(s => s.status === 'active');
    const strategiesWithPerformance = strategies.filter(s => s.performance);

    if (strategiesWithPerformance.length === 0) {
      return {
        totalStrategies: strategies.length,
        activeStrategies: activeStrategies.length,
        averageSharpeRatio: 0,
        averageReturn: 0,
        bestPerforming: {
          strategyId: '',
          strategyName: 'N/A',
          sharpeRatio: 0,
        },
        worstPerforming: {
          strategyId: '',
          strategyName: 'N/A',
          sharpeRatio: 0,
        },
      };
    }

    const performances = strategiesWithPerformance.map(s => s.performance!);
    const avgSharpe = performances.reduce((sum, p) => sum + p.sharpeRatio, 0) / performances.length;
    const avgReturn = performances.reduce((sum, p) => sum + p.annualReturn, 0) / performances.length;

    const bestPerformer = strategiesWithPerformance.reduce((best, current) =>
      (current.performance!.sharpeRatio > best.performance!.sharpeRatio) ? current : best
    );

    const worstPerformer = strategiesWithPerformance.reduce((worst, current) =>
      (current.performance!.sharpeRatio < worst.performance!.sharpeRatio) ? current : worst
    );

    return {
      totalStrategies: strategies.length,
      activeStrategies: activeStrategies.length,
      averageSharpeRatio: avgSharpe,
      averageReturn: avgReturn,
      bestPerforming: {
        strategyId: bestPerformer.id,
        strategyName: bestPerformer.name,
        sharpeRatio: bestPerformer.performance!.sharpeRatio,
      },
      worstPerforming: {
        strategyId: worstPerformer.id,
        strategyName: worstPerformer.name,
        sharpeRatio: worstPerformer.performance!.sharpeRatio,
      },
    };
  };

  const summary = calculateSummary();

  const formatPercentage = (value: number): string => {
    return `${(value * 100).toFixed(2)}%`;
  };

  const getMetricColor = (value: number, type: 'sharpe' | 'return'): string => {
    if (type === 'sharpe') {
      if (value >= 1.5) return 'text-green-600';
      if (value >= 1.0) return 'text-blue-600';
      if (value >= 0.5) return 'text-yellow-600';
      return 'text-red-600';
    } else {
      if (value >= 0.15) return 'text-green-600';
      if (value >= 0.08) return 'text-blue-600';
      if (value >= 0) return 'text-yellow-600';
      return 'text-red-600';
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      {/* Total Strategies */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">总策略数</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">{summary.totalStrategies}</p>
          </div>
          <div className="bg-blue-100 p-3 rounded-full">
            <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </div>
        </div>
        <div className="mt-4 flex items-center text-sm">
          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
            summary.activeStrategies > 0 ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
          }`}>
            {summary.activeStrategies} 运行中
          </span>
          <span className="text-gray-500 ml-2">
            ({summary.totalStrategies > 0 ? Math.round((summary.activeStrategies / summary.totalStrategies) * 100) : 0}% 活跃)
          </span>
        </div>
      </div>

      {/* Average Sharpe Ratio */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">平均夏普比率</p>
            <p className={`text-2xl font-bold mt-1 ${getMetricColor(summary.averageSharpeRatio, 'sharpe')}`}>
              {summary.averageSharpeRatio.toFixed(2)}
            </p>
          </div>
          <div className="bg-purple-100 p-3 rounded-full">
            <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
        </div>
        <div className="mt-4 text-sm text-gray-600">
          风险调整后收益指标
        </div>
      </div>

      {/* Average Return */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">平均年化收益</p>
            <p className={`text-2xl font-bold mt-1 ${getMetricColor(summary.averageReturn, 'return')}`}>
              {formatPercentage(summary.averageReturn)}
            </p>
          </div>
          <div className="bg-green-100 p-3 rounded-full">
            <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          </div>
        </div>
        <div className="mt-4 text-sm text-gray-600">
          策略平均年化回报率
        </div>
      </div>

      {/* Top Performer */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <p className="text-sm font-medium text-gray-600">最佳表现策略</p>
            <p className="text-lg font-bold text-gray-900 mt-1 truncate">
              {summary.bestPerforming.strategyName}
            </p>
            <p className={`text-sm font-medium mt-1 ${getMetricColor(summary.bestPerforming.sharpeRatio, 'sharpe')}`}>
              Sharpe: {summary.bestPerforming.sharpeRatio.toFixed(2)}
            </p>
          </div>
          <div className="bg-yellow-100 p-3 rounded-full ml-4">
            <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
};
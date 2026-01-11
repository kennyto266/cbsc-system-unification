import React from 'react';
import { UserPortfolio, Strategy } from '../../types/index';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';

interface RiskAnalysisProps {
  portfolio: UserPortfolio | null;
  strategies: Strategy[];
}

export const RiskAnalysis: React.FC<RiskAnalysisProps> = ({
  portfolio,
  strategies
}) => {
  if (!portfolio) {
    return (
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-neutral-900 mb-4">风险分析</h3>
        <p className="text-neutral-600">暂无投资组合数据</p>
      </Card>
    );
  }

  const getRiskLevel = (value: number, thresholds: { low: number; medium: number; high: number }) => {
    if (value <= thresholds.low) return { level: 'low', text: '低风险', color: 'success' };
    if (value <= thresholds.medium) return { level: 'medium', text: '中等风险', color: 'warning' };
    if (value <= thresholds.high) return { level: 'high', text: '高风险', color: 'error' };
    return { level: 'extreme', text: '极高风险', color: 'error' };
  };

  const varRisk = getRiskLevel(portfolio.riskMetrics.var95 * 100, { low: 2, medium: 5, high: 10 });
  const concentrationRisk = getRiskLevel(portfolio.riskMetrics.concentration * 100, { low: 20, medium: 40, high: 60 });
  const leverageRisk = getRiskLevel(portfolio.riskMetrics.leverage * 100, { low: 50, medium: 100, high: 150 });

  const riskMetrics = [
    {
      name: 'VaR (95%)',
      value: `${(portfolio.riskMetrics.var95 * 100).toFixed(2)}%`,
      description: '95%置信度下的最大可能损失',
      risk: varRisk
    },
    {
      name: '集中度风险',
      value: `${(portfolio.riskMetrics.concentration * 100).toFixed(1)}%`,
      description: '最大单一策略占比',
      risk: concentrationRisk
    },
    {
      name: '杠杆率',
      value: `${portfolio.riskMetrics.leverage.toFixed(2)}x`,
      description: '总资产与净资产的比率',
      risk: leverageRisk
    },
    {
      name: 'Beta系数',
      value: portfolio.riskMetrics.beta.toFixed(2),
      description: '相对市场的系统性风险',
      risk: getRiskLevel(Math.abs(portfolio.riskMetrics.beta - 1) * 100, { low: 10, medium: 20, high: 30 })
    }
  ];

  const activeStrategies = strategies.filter(s => s.status === 'active');
  const riskDistribution = {
    low: activeStrategies.filter(s => s.riskLevel === 'low').length,
    medium: activeStrategies.filter(s => s.riskLevel === 'medium').length,
    high: activeStrategies.filter(s => s.riskLevel === 'high').length,
    extreme: activeStrategies.filter(s => s.riskLevel === 'extreme').length
  };

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold text-neutral-900 mb-6">风险分析</h3>

      {/* Risk Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {riskMetrics.map((metric, index) => (
          <div key={index} className="border border-neutral-200 rounded-lg p-4">
            <div className="flex justify-between items-start mb-2">
              <h4 className="font-medium text-neutral-900">{metric.name}</h4>
              <Badge variant={metric.risk.color as any} size="sm">
                {metric.risk.text}
              </Badge>
            </div>
            <div className="text-2xl font-bold text-neutral-900 mb-1">{metric.value}</div>
            <p className="text-sm text-neutral-600">{metric.description}</p>
          </div>
        ))}
      </div>

      {/* Strategy Risk Distribution */}
      <div className="mb-6">
        <h4 className="font-medium text-neutral-900 mb-3">策略风险分布</h4>
        <div className="grid grid-cols-4 gap-4">
          <div className="text-center p-3 bg-success-50 rounded-lg">
            <div className="text-2xl font-bold text-success-900">{riskDistribution.low}</div>
            <div className="text-sm text-success-700">低风险</div>
          </div>
          <div className="text-center p-3 bg-warning-50 rounded-lg">
            <div className="text-2xl font-bold text-warning-900">{riskDistribution.medium}</div>
            <div className="text-sm text-warning-700">中等风险</div>
          </div>
          <div className="text-center p-3 bg-error-50 rounded-lg">
            <div className="text-2xl font-bold text-error-900">{riskDistribution.high}</div>
            <div className="text-sm text-error-700">高风险</div>
          </div>
          <div className="text-center p-3 bg-error-100 rounded-lg">
            <div className="text-2xl font-bold text-error-900">{riskDistribution.extreme}</div>
            <div className="text-sm text-error-700">极高风险</div>
          </div>
        </div>
      </div>

      {/* Risk Recommendations */}
      <div className="bg-neutral-50 rounded-lg p-4">
        <h4 className="font-medium text-neutral-900 mb-2">风险建议</h4>
        <ul className="space-y-2 text-sm text-neutral-700">
          {varRisk.level === 'high' && (
            <li className="flex items-start">
              <span className="text-warning-600 mr-2">⚠️</span>
              VaR值较高，建议降低仓位或增加对冲
            </li>
          )}
          {concentrationRisk.level === 'high' && (
            <li className="flex items-start">
              <span className="text-warning-600 mr-2">⚠️</span>
              集中度风险过高，建议分散投资到多个策略
            </li>
          )}
          {leverageRisk.level === 'high' && (
            <li className="flex items-start">
              <span className="text-warning-600 mr-2">⚠️</span>
              杠杆率偏高，建议降低杠杆以控制风险
            </li>
          )}
          {activeStrategies.length === 0 && (
            <li className="flex items-start">
              <span className="text-primary-600 mr-2">ℹ️</span>
              当前没有活跃策略，考虑启动适合的策略
            </li>
          )}
          {varRisk.level === 'low' && concentrationRisk.level === 'low' && leverageRisk.level === 'low' && (
            <li className="flex items-start">
              <span className="text-success-600 mr-2">✅</span>
              当前风险水平良好，继续保持现有配置
            </li>
          )}
        </ul>
      </div>
    </Card>
  );
};
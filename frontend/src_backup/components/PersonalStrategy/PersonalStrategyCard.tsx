import React from 'react';
import { Strategy, PersonalStrategyConfig } from '../../types/index';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';

interface PersonalStrategyCardProps {
  strategy: Strategy;
  onPersonalize?: (strategy: Strategy) => void;
  onSelect?: (strategy: Strategy) => void;
  isSelected?: boolean;
}

export const PersonalStrategyCard: React.FC<PersonalStrategyCardProps> = ({
  strategy,
  onPersonalize,
  onSelect,
  isSelected = false
}) => {
  const getRiskLevelColor = (risk: string) => {
    switch (risk) {
      case 'low': return 'success';
      case 'medium': return 'warning';
      case 'high': return 'error';
      case 'extreme': return 'error';
      default: return 'neutral';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'inactive': return 'neutral';
      case 'testing': return 'warning';
      case 'archived': return 'neutral';
      default: return 'neutral';
    }
  };

  const formatPercentage = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  return (
    <Card
      className={`cursor-pointer transition-all duration-200 ${
        isSelected ? 'ring-2 ring-primary-500 border-primary-500' : ''
      }`}
      onClick={() => onSelect?.(strategy)}
    >
      {/* Card Header */}
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-neutral-900 mb-1">
            {strategy.personalConfig?.customName || strategy.name}
          </h3>
          <p className="text-sm text-neutral-600 line-clamp-2">
            {strategy.description}
          </p>
        </div>
        <div className="flex flex-col items-end space-y-2">
          <Badge
            variant={getStatusColor(strategy.status)}
            size="sm"
          >
            {strategy.status === 'active' ? '运行中' :
             strategy.status === 'inactive' ? '已暂停' :
             strategy.status === 'testing' ? '测试中' : '已归档'}
          </Badge>
          <Badge
            variant={getRiskLevelColor(strategy.riskLevel)}
            size="sm"
          >
            {strategy.riskLevel === 'low' ? '低风险' :
             strategy.riskLevel === 'medium' ? '中等风险' :
             strategy.riskLevel === 'high' ? '高风险' : '极高风险'}
          </Badge>
        </div>
      </div>

      {/* Performance Metrics */}
      {strategy.performance && (
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="text-center p-3 bg-neutral-50 rounded-lg">
            <div className={`text-lg font-bold ${
              strategy.performance.totalReturn >= 0 ? 'text-success-600' : 'text-error-600'
            }`}>
              {formatPercentage(strategy.performance.totalReturn)}
            </div>
            <div className="text-xs text-neutral-600">总收益率</div>
          </div>
          <div className="text-center p-3 bg-neutral-50 rounded-lg">
            <div className="text-lg font-bold text-neutral-900">
              {strategy.performance.sharpeRatio.toFixed(2)}
            </div>
            <div className="text-xs text-neutral-600">夏普比率</div>
          </div>
        </div>
      )}

      {/* Personal Configuration Info */}
      {strategy.personalConfig && (
        <div className="mb-4 p-3 bg-primary-50 border border-primary-200 rounded-lg">
          <div className="text-xs font-medium text-primary-900 mb-2">个性化配置</div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="flex justify-between">
              <span className="text-neutral-600">风险偏好:</span>
              <span className="font-medium">
                {strategy.personalConfig.riskTolerance === 'conservative' ? '保守' :
                 strategy.personalConfig.riskTolerance === 'moderate' ? '适中' : '激进'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-neutral-600">资金分配:</span>
              <span className="font-medium">
                {formatCurrency(strategy.personalConfig.capitalAllocation)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-neutral-600">止损:</span>
              <span className="font-medium">
                {strategy.personalConfig.stopLoss}%
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-neutral-600">止盈:</span>
              <span className="font-medium">
                {strategy.personalConfig.takeProfit}%
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Strategy Tags */}
      {strategy.tags && strategy.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-4">
          {strategy.tags.slice(0, 3).map((tag, index) => (
            <Badge
              key={index}
              variant="neutral"
              size="xs"
            >
              {tag}
            </Badge>
          ))}
          {strategy.tags.length > 3 && (
            <Badge variant="neutral" size="xs">
              +{strategy.tags.length - 3}
            </Badge>
          )}
        </div>
      )}

      {/* Latest Signal */}
      {strategy.latestSignal && (
        <div className="mb-4 p-2 bg-neutral-50 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${
                strategy.latestSignal.type === 'buy' ? 'bg-success-500' :
                strategy.latestSignal.type === 'sell' ? 'bg-error-500' : 'bg-neutral-500'
              }`} />
              <span className="text-sm font-medium text-neutral-900">
                {strategy.latestSignal.type === 'buy' ? '买入信号' :
                 strategy.latestSignal.type === 'sell' ? '卖出信号' : '持有信号'}
              </span>
            </div>
            <div className="text-xs text-neutral-500">
              {new Date(strategy.latestSignal.timestamp).toLocaleTimeString()}
            </div>
          </div>
          <div className="mt-1 text-xs text-neutral-600">
            强度: {(strategy.latestSignal.strength * 100).toFixed(0)}% |
            置信度: {(strategy.latestSignal.confidence * 100).toFixed(0)}%
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex space-x-2">
        <Button
          size="sm"
          variant="outline"
          className="flex-1"
          onClick={(e) => {
            e.stopPropagation();
            onSelect?.(strategy);
          }}
        >
          查看详情
        </Button>
        <Button
          size="sm"
          variant="primary"
          className="flex-1"
          onClick={(e) => {
            e.stopPropagation();
            onPersonalize?.(strategy);
          }}
        >
          {strategy.personalConfig ? '调整配置' : '个性化'}
        </Button>
      </div>

      {/* Auto-trading Indicator */}
      {strategy.personalConfig?.autoTrading && (
        <div className="absolute top-2 right-2">
          <div className="flex items-center space-x-1 bg-success-100 text-success-800 px-2 py-1 rounded-full text-xs">
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <span>自动交易</span>
          </div>
        </div>
      )}
    </Card>
  );
};
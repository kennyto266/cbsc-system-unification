/**
 * Smart Suggestions Component
 * 智能建議組件
 */

import React, { useState, useEffect } from 'react';
import {
  LightBulbIcon,
  SparklesIcon,
  TrendingUpIcon,
  ShieldCheckIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';
import { StrategyType, RiskTolerance } from '../../../types/strategyTypes';
import { useStrategies } from '../../../hooks/useStrategies';

interface Suggestion {
  id: string;
  title: string;
  description: string;
  strategyType: StrategyType;
  parameters: Record<string, any>;
  riskLevel: RiskTolerance;
  expectedReturn: number;
  confidence: number;
  tags: string[];
  icon: React.ComponentType<any>;
  basis: 'historical' | 'market_trend' | 'user_preference' | 'popular';
}

interface SmartSuggestionsProps {
  onSuggestionSelect: (suggestion: Partial<Suggestion>) => void;
  currentStep: number;
  userData?: {
    riskTolerance?: RiskTolerance;
    previousStrategies?: string[];
    preferredTypes?: StrategyType[];
  };
}

export const SmartSuggestions: React.FC<SmartSuggestionsProps> = ({
  onSuggestionSelect,
  currentStep,
  userData
}) => {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSuggestion, setSelectedSuggestion] = useState<string | null>(null);
  const { strategies } = useStrategies();

  // Generate suggestions based on historical data and user preferences
  useEffect(() => {
    const generateSuggestions = async () => {
      setLoading(true);

      // Mock AI-powered suggestions (in real implementation, this would call an AI service)
      const generatedSuggestions: Suggestion[] = [
        {
          id: 'momentum_rsi',
          title: 'RSI 動量策略',
          description: '基於 RSI 指標的動量策略，適合捕捉短期價格波動',
          strategyType: StrategyType.MOMENTUM,
          parameters: {
            rsi_period: 14,
            rsi_oversold: 30,
            rsi_overbought: 70,
            lookback: 20
          },
          riskLevel: RiskTolerance.MEDIUM,
          expectedReturn: 0.15,
          confidence: 0.85,
          tags: ['動量', 'RSI', '短期'],
          icon: TrendingUpIcon,
          basis: 'historical'
        },
        {
          id: 'mean_reversion_bollinger',
          title: '布林帶均值回歸',
          description: '利用布林帶進行均值回歸交易，適合震盪市場',
          strategyType: StrategyType.MEAN_REVERSION,
          parameters: {
            bb_period: 20,
            bb_std: 2,
            entry_threshold: 0.02,
            exit_threshold: 0.01
          },
          riskLevel: RiskTolerance.LOW,
          expectedReturn: 0.12,
          confidence: 0.78,
          tags: ['均值回歸', '布林帶', '震盪'],
          icon: ChartBarIcon,
          basis: 'market_trend'
        },
        {
          id: 'volume_breakout',
          title: '成交量突破策略',
          description: '基於成交量放大的突破策略，捕捉價格突破點',
          strategyType: StrategyType.VOLUME,
          parameters: {
            volume_ma_period: 20,
            volume_multiplier: 1.5,
            price_change_threshold: 0.02
          },
          riskLevel: RiskTolerance.HIGH,
          expectedReturn: 0.20,
          confidence: 0.72,
          tags: ['成交量', '突破', '高風險'],
          icon: SparklesIcon,
          basis: 'popular'
        },
        {
          id: 'safe_haven',
          title: '避險資產組合',
          description: '配置避險資產的低風險策略，適合保守投資者',
          strategyType: StrategyType.PORTFOLIO,
          parameters: {
            bond_allocation: 0.6,
            gold_allocation: 0.2,
            cash_allocation: 0.2,
            rebalance_frequency: 'monthly'
          },
          riskLevel: RiskTolerance.LOW,
          expectedReturn: 0.08,
          confidence: 0.90,
          tags: ['避險', '資產配置', '低風險'],
          icon: ShieldCheckIcon,
          basis: 'user_preference'
        }
      ];

      // Filter and rank suggestions based on user data
      if (userData) {
        // Prioritize based on risk tolerance
        if (userData.riskTolerance) {
          generatedSuggestions.sort((a, b) => {
            const aRiskScore = getRiskScore(a.riskLevel);
            const bRiskScore = getRiskScore(b.riskLevel);
            const userRiskScore = getRiskScore(userData.riskTolerance!);

            const aDiff = Math.abs(aRiskScore - userRiskScore);
            const bDiff = Math.abs(bRiskScore - userRiskScore);

            return aDiff - bDiff;
          });
        }

        // Boost previously successful strategy types
        if (userData.preferredTypes?.length) {
          generatedSuggestions.forEach(s => {
            if (userData.preferredTypes!.includes(s.strategyType)) {
              s.confidence = Math.min(s.confidence + 0.1, 1);
            }
          });
        }
      }

      // Sort by confidence score
      generatedSuggestions.sort((a, b) => b.confidence - a.confidence);

      setSuggestions(generatedSuggestions.slice(0, 4)); // Show top 4 suggestions
      setLoading(false);
    };

    if (currentStep === 1) {
      generateSuggestions();
    }
  }, [currentStep, userData]);

  // Only show on step 1
  if (currentStep !== 1) {
    return null;
  }

  const handleSuggestionClick = (suggestion: Suggestion) => {
    setSelectedSuggestion(suggestion.id);
    onSuggestionSelect({
      strategy_type: suggestion.strategyType,
      parameters: suggestion.parameters,
      risk_tolerance: suggestion.riskLevel
    });
  };

  const getRiskScore = (risk: RiskTolerance): number => {
    const scores = {
      [RiskTolerance.LOW]: 1,
      [RiskTolerance.MEDIUM]: 2,
      [RiskTolerance.HIGH]: 3,
      [RiskTolerance.EXTREME]: 4
    };
    return scores[risk];
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 dark:text-green-400';
    if (confidence >= 0.6) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  const getBasisLabel = (basis: string) => {
    const labels = {
      historical: '歷史數據',
      market_trend: '市場趨勢',
      user_preference: '用戶偏好',
      popular: '熱門策略'
    };
    return labels[basis as keyof typeof labels] || basis;
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <LightBulbIcon className="w-5 h-5 text-yellow-500" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">
            智能推薦策略
          </h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="animate-pulse">
              <div className="h-32 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <LightBulbIcon className="w-5 h-5 text-yellow-500" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">
            智能推薦策略
          </h3>
        </div>
        <span className="text-sm text-gray-500 dark:text-gray-400">
          基於 {strategies.length} 個策略的歷史數據
        </span>
      </div>

      {/* Suggestions Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {suggestions.map((suggestion) => {
          const Icon = suggestion.icon;
          return (
            <div
              key={suggestion.id}
              className={`
                relative p-4 rounded-lg border-2 cursor-pointer transition-all
                ${selectedSuggestion === suggestion.id
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                }
              `}
              onClick={() => handleSuggestionClick(suggestion)}
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <div className={`
                    p-2 rounded-lg
                    ${selectedSuggestion === suggestion.id
                      ? 'bg-blue-100 dark:bg-blue-800'
                      : 'bg-gray-100 dark:bg-gray-800'
                    }
                  `}>
                    <Icon className="w-5 h-5 text-gray-700 dark:text-gray-300" />
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900 dark:text-white">
                      {suggestion.title}
                    </h4>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {suggestion.strategyType}
                    </p>
                  </div>
                </div>

                {/* Confidence Score */}
                <div className="text-right">
                  <div className={`text-sm font-medium ${getConfidenceColor(suggestion.confidence)}`}>
                    {(suggestion.confidence * 100).toFixed(0)}%
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    置信度
                  </div>
                </div>
              </div>

              {/* Description */}
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                {suggestion.description}
              </p>

              {/* Tags */}
              <div className="flex flex-wrap gap-1 mb-3">
                {suggestion.tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-2 py-1 text-xs rounded-full bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400"
                  >
                    {tag}
                  </span>
                ))}
              </div>

              {/* Metrics */}
              <div className="flex items-center justify-between text-sm">
                <div>
                  <span className="text-gray-500 dark:text-gray-400">預期回報: </span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {(suggestion.expectedReturn * 100).toFixed(1)}%
                  </span>
                </div>
                <div>
                  <span className="text-gray-500 dark:text-gray-400">風險等級: </span>
                  <span className={`
                    font-medium
                    ${suggestion.riskLevel === RiskTolerance.LOW ? 'text-green-600' : ''}
                    ${suggestion.riskLevel === RiskTolerance.MEDIUM ? 'text-yellow-600' : ''}
                    ${suggestion.riskLevel === RiskTolerance.HIGH ? 'text-orange-600' : ''}
                    ${suggestion.riskLevel === RiskTolerance.EXTREME ? 'text-red-600' : ''}
                  `}>
                    {suggestion.riskLevel.toUpperCase()}
                  </span>
                </div>
              </div>

              {/* Basis Badge */}
              <div className="mt-2">
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  基於: {getBasisLabel(suggestion.basis)}
                </span>
              </div>

              {/* Selected Indicator */}
              {selectedSuggestion === suggestion.id && (
                <div className="absolute top-2 right-2">
                  <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
                    <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Tips */}
      <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
        <div className="flex items-start space-x-2">
          <LightBulbIcon className="w-4 h-4 text-blue-600 dark:text-blue-400 mt-0.5" />
          <div className="text-sm text-blue-800 dark:text-blue-200">
            <p className="font-medium mb-1">智能提示</p>
            <ul className="list-disc list-inside space-y-1 text-xs">
              <li>推薦策略基於歷史表現和當前市場條件</li>
              <li>您可以選擇推薦並根據需要調整參數</li>
              <li>置信度越高，策略在當前市場環境下成功概率越大</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};
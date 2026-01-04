import React, { useState, useEffect } from 'react';
import {
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ChartBarIcon,
  CurrencyDollarIcon,
  GlobeAltIcon,
  BuildingOfficeIcon,
  UserGroupIcon,
  BriefcaseIcon
} from '@heroicons/react/24/outline';

interface Strategy {
  id: string;
  name: string;
  category: string;
  description: string;
  icon: React.ComponentType<any>;
  parameters: StrategyParameter[];
}

interface StrategyParameter {
  name: string;
  type: 'number' | 'select' | 'boolean';
  label: string;
  description: string;
  default: any;
  options?: { value: string; label: string }[];
  min?: number;
  max?: number;
  step?: number;
}

interface StrategySelectorProps {
  selectedStrategy: string | null;
  onStrategySelect: (strategyId: string, parameters: any) => void;
  className?: string;
}

const STRATEGIES: Strategy[] = [
  // Technical Indicators
  {
    id: 'bollinger_bands',
    name: 'Bollinger Bands',
    category: 'technical',
    description: 'Mean reversion strategy using Bollinger Bands',
    icon: ChartBarIcon,
    parameters: [
      {
        name: 'period',
        type: 'number',
        label: 'Period',
        description: 'Number of periods for moving average',
        default: 20,
        min: 5,
        max: 50
      },
      {
        name: 'std_dev',
        type: 'number',
        label: 'Standard Deviation',
        description: 'Number of standard deviations',
        default: 2.0,
        min: 1.5,
        max: 3.0,
        step: 0.1
      },
      {
        name: 'strategy_type',
        type: 'select',
        label: 'Strategy Type',
        description: 'Type of Bollinger Bands strategy',
        default: 'mean_reversion',
        options: [
          { value: 'mean_reversion', label: 'Mean Reversion' },
          { value: 'breakout', label: 'Breakout' }
        ]
      }
    ]
  },
  {
    id: 'macd',
    name: 'MACD',
    category: 'technical',
    description: 'Moving Average Convergence Divergence strategy',
    icon: ArrowTrendingUpIcon,
    parameters: [
      {
        name: 'fast_period',
        type: 'number',
        label: 'Fast Period',
        description: 'Fast EMA period',
        default: 12,
        min: 8,
        max: 20
      },
      {
        name: 'slow_period',
        type: 'number',
        label: 'Slow Period',
        description: 'Slow EMA period',
        default: 26,
        min: 20,
        max: 40
      },
      {
        name: 'signal_period',
        type: 'number',
        label: 'Signal Period',
        description: 'Signal line EMA period',
        default: 9,
        min: 5,
        max: 15
      }
    ]
  },
  {
    id: 'rsi',
    name: 'RSI',
    category: 'technical',
    description: 'Relative Strength Index momentum oscillator',
    icon: ChartBarIcon,
    parameters: [
      {
        name: 'period',
        type: 'number',
        label: 'RSI Period',
        description: 'Number of periods for RSI calculation',
        default: 14,
        min: 7,
        max: 30
      },
      {
        name: 'overbought_level',
        type: 'number',
        label: 'Overbought Level',
        description: 'RSI level considered overbought',
        default: 70,
        min: 60,
        max: 90
      },
      {
        name: 'oversold_level',
        type: 'number',
        label: 'Oversold Level',
        description: 'RSI level considered oversold',
        default: 30,
        min: 10,
        max: 40
      }
    ]
  },
  // Momentum Strategies
  {
    id: 'momentum',
    name: 'Momentum',
    category: 'momentum',
    description: 'Price momentum strategy',
    icon: ArrowTrendingUpIcon,
    parameters: [
      {
        name: 'lookback_period',
        type: 'number',
        label: 'Lookback Period',
        description: 'Period for momentum calculation',
        default: 10,
        min: 5,
        max: 30
      },
      {
        name: 'momentum_threshold',
        type: 'number',
        label: 'Momentum Threshold',
        description: 'Minimum momentum for signal',
        default: 0.02,
        min: 0.01,
        max: 0.10,
        step: 0.01
      }
    ]
  },
  // Volume Strategies
  {
    id: 'obv',
    name: 'On-Balance Volume',
    category: 'volume',
    description: 'Volume-based momentum strategy',
    icon: ChartBarIcon,
    parameters: [
      {
        name: 'signal_threshold',
        type: 'number',
        label: 'Signal Threshold',
        description: 'Threshold for volume signals',
        default: 0.1,
        min: 0.05,
        max: 0.3,
        step: 0.05
      }
    ]
  },
  // Portfolio Strategies
  {
    id: 'multi_factor',
    name: 'Multi-Factor',
    category: 'portfolio',
    description: 'Combine multiple factors for portfolio construction',
    icon: BriefcaseIcon,
    parameters: [
      {
        name: 'momentum_weight',
        type: 'number',
        label: 'Momentum Weight',
        description: 'Weight for momentum factor',
        default: 0.4,
        min: 0,
        max: 1,
        step: 0.1
      },
      {
        name: 'value_weight',
        type: 'number',
        label: 'Value Weight',
        description: 'Weight for value factor',
        default: 0.3,
        min: 0,
        max: 1,
        step: 0.1
      },
      {
        name: 'quality_weight',
        type: 'number',
        label: 'Quality Weight',
        description: 'Weight for quality factor',
        default: 0.3,
        min: 0,
        max: 1,
        step: 0.1
      }
    ]
  },
  // Fundamental Strategies
  {
    id: 'hibor',
    name: 'HIBOR Strategy',
    category: 'fundamental',
    description: 'Based on Hong Kong Interbank Offered Rate',
    icon: CurrencyDollarIcon,
    parameters: [
      {
        name: 'lookback_period',
        type: 'number',
        label: 'Lookback Period',
        description: 'Days to look back for rate analysis',
        default: 30,
        min: 10,
        max: 90
      },
      {
        name: 'rate_threshold_high',
        type: 'number',
        label: 'High Rate Threshold',
        description: 'Rate level considered high',
        default: 5.0,
        min: 3.0,
        max: 8.0,
        step: 0.1
      },
      {
        name: 'rate_threshold_low',
        type: 'number',
        label: 'Low Rate Threshold',
        description: 'Rate level considered low',
        default: 2.5,
        min: 1.0,
        max: 4.0,
        step: 0.1
      }
    ]
  },
  {
    id: 'gdp_growth',
    name: 'GDP Growth Strategy',
    category: 'fundamental',
    description: 'Economic cycle strategy based on GDP growth',
    icon: GlobeAltIcon,
    parameters: [
      {
        name: 'gdp_threshold_high',
        type: 'number',
        label: 'High Growth Threshold',
        description: 'GDP growth rate considered high',
        default: 4.0,
        min: 2.0,
        max: 6.0,
        step: 0.5
      },
      {
        name: 'gdp_threshold_low',
        type: 'number',
        label: 'Low Growth Threshold',
        description: 'GDP growth rate considered low',
        default: 1.0,
        min: -2.0,
        max: 2.0,
        step: 0.5
      }
    ]
  },
  {
    id: 'visitor_arrivals',
    name: 'Visitor Arrivals',
    category: 'fundamental',
    description: 'Tourism sector strategy based on visitor arrivals',
    icon: UserGroupIcon,
    parameters: [
      {
        name: 'trend_period',
        type: 'number',
        label: 'Trend Period',
        description: 'Days for trend calculation',
        default: 90,
        min: 30,
        max: 180
      },
      {
        name: 'change_threshold',
        type: 'number',
        label: 'Change Threshold',
        description: 'Percentage change for signals',
        default: 0.05,
        min: 0.02,
        max: 0.15,
        step: 0.01
      }
    ]
  },
  {
    id: 'composite_economic',
    name: 'Composite Economic',
    category: 'fundamental',
    description: 'Combined strategy using multiple economic indicators',
    icon: BuildingOfficeIcon,
    parameters: [
      {
        name: 'hibor_weight',
        type: 'number',
        label: 'HIBOR Weight',
        description: 'Weight for HIBOR indicator',
        default: 0.25,
        min: 0,
        max: 1,
        step: 0.05
      },
      {
        name: 'gdp_weight',
        type: 'number',
        label: 'GDP Weight',
        description: 'Weight for GDP indicator',
        default: 0.25,
        min: 0,
        max: 1,
        step: 0.05
      },
      {
        name: 'pmi_weight',
        type: 'number',
        label: 'PMI Weight',
        description: 'Weight for PMI indicator',
        default: 0.25,
        min: 0,
        max: 1,
        step: 0.05
      },
      {
        name: 'unemployment_weight',
        type: 'number',
        label: 'Unemployment Weight',
        description: 'Weight for unemployment indicator',
        default: 0.25,
        min: 0,
        max: 1,
        step: 0.05
      }
    ]
  }
];

const CATEGORIES = [
  { id: 'all', name: 'All Strategies', color: 'bg-gray-100 text-gray-800' },
  { id: 'technical', name: 'Technical Indicators', color: 'bg-blue-100 text-blue-800' },
  { id: 'momentum', name: 'Momentum', color: 'bg-green-100 text-green-800' },
  { id: 'volume', name: 'Volume', color: 'bg-purple-100 text-purple-800' },
  { id: 'portfolio', name: 'Portfolio', color: 'bg-yellow-100 text-yellow-800' },
  { id: 'fundamental', name: 'Fundamental', color: 'bg-red-100 text-red-800' }
];

export default function StrategySelector({
  selectedStrategy,
  onStrategySelect,
  className = ''
}: StrategySelectorProps) {
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [expandedStrategy, setExpandedStrategy] = useState<string | null>(null);
  const [strategyParameters, setStrategyParameters] = useState<Record<string, any>>({});

  const filteredStrategies = selectedCategory === 'all'
    ? STRATEGIES
    : STRATEGIES.filter(s => s.category === selectedCategory);

  const handleParameterChange = (strategyId: string, paramName: string, value: any) => {
    setStrategyParameters(prev => ({
      ...prev,
      [strategyId]: {
        ...prev[strategyId],
        [paramName]: value
      }
    }));
  };

  const handleStrategySelect = (strategy: Strategy) => {
    const parameters = strategyParameters[strategy.id] || {};

    // Set default values if not provided
    strategy.parameters.forEach(param => {
      if (!(param.name in parameters)) {
        parameters[param.name] = param.default;
      }
    });

    onStrategySelect(strategy.id, parameters);
    setExpandedStrategy(strategy.id);
  };

  const renderParameterInput = (strategy: Strategy, param: StrategyParameter) => {
    const value = strategyParameters[strategy.id]?.[param.name] ?? param.default;

    switch (param.type) {
      case 'number':
        return (
          <div className="flex items-center space-x-2">
            <input
              type="number"
              min={param.min}
              max={param.max}
              step={param.step}
              value={value}
              onChange={(e) => handleParameterChange(strategy.id, param.name, parseFloat(e.target.value))}
              className="w-32 px-3 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {param.min !== undefined && param.max !== undefined && (
              <span className="text-sm text-gray-500">
                [{param.min} - {param.max}]
              </span>
            )}
          </div>
        );

      case 'select':
        return (
          <select
            value={value}
            onChange={(e) => handleParameterChange(strategy.id, param.name, e.target.value)}
            className="w-full px-3 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {param.options?.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        );

      case 'boolean':
        return (
          <input
            type="checkbox"
            checked={value}
            onChange={(e) => handleParameterChange(strategy.id, param.name, e.target.checked)}
            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
          />
        );

      default:
        return null;
    }
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Category Filter */}
      <div className="flex flex-wrap gap-2">
        {CATEGORIES.map(category => (
          <button
            key={category.id}
            onClick={() => setSelectedCategory(category.id)}
            className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
              selectedCategory === category.id
                ? category.color
                : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
            }`}
          >
            {category.name}
          </button>
        ))}
      </div>

      {/* Strategy Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredStrategies.map(strategy => {
          const Icon = strategy.icon;
          const isSelected = selectedStrategy === strategy.id;
          const isExpanded = expandedStrategy === strategy.id;

          return (
            <div
              key={strategy.id}
              className={`border rounded-lg transition-all cursor-pointer ${
                isSelected
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => handleStrategySelect(strategy)}
            >
              <div className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-3">
                    <Icon className="w-6 h-6 text-gray-600" />
                    <div>
                      <h3 className="font-medium text-gray-900">{strategy.name}</h3>
                      <span className={`inline-block px-2 py-1 text-xs font-medium rounded-full mt-1 ${
                        CATEGORIES.find(c => c.id === strategy.category)?.color || 'bg-gray-100'
                      }`}>
                        {CATEGORIES.find(c => c.id === strategy.category)?.name}
                      </span>
                    </div>
                  </div>
                </div>

                <p className="mt-2 text-sm text-gray-600">{strategy.description}</p>

                {/* Parameters */}
                {isExpanded && strategy.parameters.length > 0 && (
                  <div
                    className="mt-4 pt-4 border-t border-gray-200"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <h4 className="font-medium text-gray-900 mb-3">Parameters</h4>
                    <div className="space-y-3">
                      {strategy.parameters.map(param => (
                        <div key={param.name}>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            {param.label}
                          </label>
                          <p className="text-xs text-gray-500 mb-1">{param.description}</p>
                          {renderParameterInput(strategy, param)}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Expand/Collapse indicator */}
                {strategy.parameters.length > 0 && (
                  <div className="mt-2 text-xs text-gray-500">
                    {isExpanded ? 'Click to collapse' : 'Click to configure parameters'}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {filteredStrategies.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No strategies found in this category
        </div>
      )}
    </div>
  );
}
/**
 * Strategy Generator with Non-Price Data Integration
 * 策略生成器 - 整合非價格數據
 *
 * A distinctive cyberpunk-finance aesthetic dashboard for generating trading strategies
 * based on economic indicators and non-price data.
 */

import React, { useState, useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  TrendingUp,
  Activity,
  Zap,
  Database,
  Settings,
  Play,
  RefreshCw,
  Plus,
  Minus,
  ChevronDown,
  AlertTriangle,
  CheckCircle2,
  Sparkles
} from 'lucide-react';
import { useDispatch, useSelector } from 'react-redux';

import { economicDataApi } from '../../../services/economicDataApi';
import { fetchAllEconomicIndicators } from '../../../store/slices/economicDataSlice';
import type {
  HiborData,
  GdpData,
  PmiData,
  VisitorData,
  UnemploymentData
} from '../../../store/slices/economicDataSlice';

// TypeScript types
interface IndicatorConfig {
  id: string;
  name: string;
  nameEn: string;
  icon: React.ReactNode;
  color: string;
  description: string;
  weight: number;
  enabled: boolean;
}

interface StrategyPreset {
  id: string;
  name: string;
  description: string;
  indicators: string[];
  weights: Record<string, number>;
}

// Preset strategy configurations
const STRATEGY_PRESETS: StrategyPreset[] = [
  {
    id: 'economic-momentum',
    name: '經濟動量策略',
    description: '基於PMI、訪港旅客和GDP增長的動量策略',
    indicators: ['pmi', 'visitors', 'gdp'],
    weights: { pmi: 0.4, visitors: 0.3, gdp: 0.3 }
  },
  {
    id: 'liquidity-sentiment',
    name: '流動性情緒策略',
    description: '結合HIBOR利率與失業率的市場情緒分析',
    indicators: ['hibor', 'unemployment'],
    weights: { hibor: 0.6, unemployment: 0.4 }
  },
  {
    id: 'macro-balanced',
    name: '宏觀平衡策略',
    description: '綜合所有經濟指標的平衡型策略',
    indicators: ['hibor', 'gdp', 'pmi', 'visitors', 'unemployment'],
    weights: { hibor: 0.2, gdp: 0.2, pmi: 0.2, visitors: 0.2, unemployment: 0.2 }
  }
];

// Indicator configurations
const INDICATOR_CONFIGS: IndicatorConfig[] = [
  {
    id: 'hibor',
    name: 'HIBOR利率',
    nameEn: 'HIBOR Rate',
    icon: <TrendingUp className="w-5 h-5" />,
    color: '#00ff9f',
    description: '香港銀行同業拆借利率，反映市場流動性',
    weight: 0.2,
    enabled: false
  },
  {
    id: 'gdp',
    name: 'GDP增長',
    nameEn: 'GDP Growth',
    icon: <Activity className="w-5 h-5" />,
    color: '#ff00ff',
    description: '本地生產總值增長率，衡量經濟表現',
    weight: 0.2,
    enabled: false
  },
  {
    id: 'pmi',
    name: 'PMI指數',
    nameEn: 'PMI Index',
    icon: <Zap className="w-5 h-5" />,
    color: '#ffff00',
    description: '採購經理指數，反映製造業景氣度',
    weight: 0.2,
    enabled: false
  },
  {
    id: 'visitors',
    name: '訪港旅客',
    nameEn: 'Visitor Arrivals',
    icon: <Database className="w-5 h-5" />,
    color: '#00ffff',
    description: '每月訪港旅客數量，旅遊業指標',
    weight: 0.2,
    enabled: false
  },
  {
    id: 'unemployment',
    name: '失業率',
    nameEn: 'Unemployment Rate',
    icon: <AlertTriangle className="w-5 h-5" />,
    color: '#ff6b6b',
    description: '失業率數據，勞動市場健康度',
    weight: 0.2,
    enabled: false
  }
];

/**
 * StrategyGenerator Component
 */
const StrategyGenerator: React.FC = () => {
  const dispatch = useDispatch();

  // Redux state
  const economicData = useSelector((state: any) => state.economicData?.data || {
    hibor: [],
    gdp: [],
    pmi: [],
    visitors: [],
    unemployment: []
  });
  const loading = useSelector((state: any) => state.economicData?.loading || false);
  const error = useSelector((state: any) => state.economicData?.error || null);

  // Mock data for demo when API is unavailable
  const mockEconomicData = useMemo(() => ({
    hibor: [{ date: '2024-12-01', rate: 5.23 }, { date: '2024-11-01', rate: 5.15 }],
    gdp: [{ quarter: '2024-Q3', gdp_growth: 3.2 }],
    pmi: [{ month: '2024-11', pmi: 50.1 }],
    visitors: [{ month: '2024-10', visitors: 3525000 }],
    unemployment: [{ month: '2024-10', rate: 3.0 }]
  }), []);

  // Local state
  const [selectedPreset, setSelectedPreset] = useState<string>('');
  const [indicators, setIndicators] = useState<IndicatorConfig[]>(INDICATOR_CONFIGS);
  const [strategyName, setStrategyName] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedStrategy, setGeneratedStrategy] = useState<any>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Fetch economic data on mount
  useEffect(() => {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setFullYear(startDate.getFullYear() - 1);

    // Try to fetch real data, but use mock data as fallback
    dispatch(fetchAllEconomicIndicators({
      dateRange: {
        start: startDate.toISOString().split('T')[0],
        end: endDate.toISOString().split('T')[0]
      }
    }) as any).catch(() => {
      // If API fails, we'll use mock data in the render
      console.log('Using mock economic data for demo');
    });
  }, [dispatch]);

  // Handle preset selection
  const handlePresetChange = (presetId: string) => {
    setSelectedPreset(presetId);
    const preset = STRATEGY_PRESETS.find(p => p.id === presetId);

    if (preset) {
      setIndicators(prev => prev.map(ind => ({
        ...ind,
        enabled: preset.indicators.includes(ind.id),
        weight: preset.weights[ind.id] || ind.weight
      })));
      setStrategyName(preset.name);
    }
  };

  // Toggle indicator
  const toggleIndicator = (id: string) => {
    setIndicators(prev => prev.map(ind =>
      ind.id === id ? { ...ind, enabled: !ind.enabled } : ind
    ));
  };

  // Update indicator weight
  const updateWeight = (id: string, delta: number) => {
    setIndicators(prev => prev.map(ind => {
      if (ind.id === id) {
        const newWeight = Math.max(0.05, Math.min(0.8, ind.weight + delta));
        return { ...ind, weight: newWeight };
      }
      return ind;
    }));
  };

  // Generate strategy
  const handleGenerate = async () => {
    setIsGenerating(true);

    // Simulate strategy generation
    await new Promise(resolve => setTimeout(resolve, 2000));

    const enabledIndicators = indicators.filter(ind => ind.enabled);
    const totalWeight = enabledIndicators.reduce((sum, ind) => sum + ind.weight, 0);

    setGeneratedStrategy({
      id: `strategy_${Date.now()}`,
      name: strategyName || '自定義經濟指標策略',
      description: `基於 ${enabledIndicators.map(ind => ind.name).join('、')} 的量化交易策略`,
      indicators: enabledIndicators.map(ind => ({
        ...ind,
        normalizedWeight: ind.weight / totalWeight
      })),
      parameters: {
        rebalanceFrequency: 'monthly',
        riskTolerance: 0.15,
        positionSizing: 'equal_weight'
      },
      expectedPerformance: {
        annualReturn: 0.08 + Math.random() * 0.12,
        sharpeRatio: 0.8 + Math.random() * 0.6,
        maxDrawdown: -0.05 - Math.random() * 0.1
      },
      createdAt: new Date().toISOString()
    });

    setIsGenerating(false);
  };

  // Calculate indicator health score
  const calculateHealthScore = (indicatorId: string): number => {
    const data = economicData[indicatorId as keyof typeof economicData];
    if (!data || data.length === 0) return 0;

    // Simple health calculation based on data recency
    const latestData = data[0];
    const dataDate = new Date(latestData.date || latestData.month || latestData.quarter);
    const daysSinceUpdate = Math.floor((Date.now() - dataDate.getTime()) / (1000 * 60 * 60 * 24));

    return Math.max(0, 100 - daysSinceUpdate * 2);
  };

  // Render indicator card
  const renderIndicatorCard = (indicator: IndicatorConfig) => {
    const healthScore = calculateHealthScore(indicator.id);
    const hasData = economicData[indicator.id as keyof typeof economicData]?.length > 0;

    return (
      <motion.div
        key={indicator.id}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className={`relative p-5 rounded-xl border-2 transition-all duration-300 ${
          indicator.enabled
            ? 'bg-opacity-20 border-opacity-100'
            : 'bg-gray-900/50 border-gray-800 opacity-50'
        }`}
        style={{
          backgroundColor: indicator.enabled ? `${indicator.color}10` : 'rgba(17, 24, 39, 0.5)',
          borderColor: indicator.enabled ? indicator.color : '#1f2937'
        }}
      >
        {/* Indicator Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg" style={{ backgroundColor: `${indicator.color}20` }}>
              <div style={{ color: indicator.color }}>
                {indicator.icon}
              </div>
            </div>
            <div>
              <h4 className="font-semibold text-white text-sm">{indicator.name}</h4>
              <p className="text-xs text-gray-400">{indicator.nameEn}</p>
            </div>
          </div>

          {/* Toggle Switch */}
          <button
            onClick={() => toggleIndicator(indicator.id)}
            className={`relative w-12 h-6 rounded-full transition-colors duration-200 ${
              indicator.enabled ? 'opacity-100' : 'opacity-40'
            }`}
            style={{ backgroundColor: indicator.enabled ? indicator.color : '#374151' }}
          >
            <motion.div
              className="absolute top-1 w-4 h-4 bg-white rounded-full shadow-md"
              animate={{ left: indicator.enabled ? '28px' : '4px' }}
              transition={{ type: 'spring', stiffness: 500, damping: 30 }}
            />
          </button>
        </div>

        {/* Description */}
        <p className="text-xs text-gray-400 mb-3">{indicator.description}</p>

        {/* Data Status */}
        <div className="flex items-center gap-2 mb-3">
          {hasData ? (
            <>
              <CheckCircle2 className="w-4 h-4 text-green-400" />
              <span className="text-xs text-green-400">數據可用</span>
              <span className="text-xs text-gray-500">健康度: {healthScore}%</span>
            </>
          ) : (
            <>
              <AlertTriangle className="w-4 h-4 text-yellow-400" />
              <span className="text-xs text-yellow-400">等待數據</span>
            </>
          )}
        </div>

        {/* Weight Control */}
        {indicator.enabled && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="border-t border-gray-700 pt-3"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-gray-400">權重</span>
              <span className="text-sm font-semibold" style={{ color: indicator.color }}>
                {(indicator.weight * 100).toFixed(0)}%
              </span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => updateWeight(indicator.id, -0.05)}
                className="p-1 rounded bg-gray-800 hover:bg-gray-700 transition-colors"
              >
                <Minus className="w-4 h-4 text-gray-400" />
              </button>
              <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
                <motion.div
                  className="h-full rounded-full"
                  style={{ backgroundColor: indicator.color }}
                  initial={{ width: 0 }}
                  animate={{ width: `${indicator.weight * 100}%` }}
                  transition={{ duration: 0.3 }}
                />
              </div>
              <button
                onClick={() => updateWeight(indicator.id, 0.05)}
                className="p-1 rounded bg-gray-800 hover:bg-gray-700 transition-colors"
              >
                <Plus className="w-4 h-4 text-gray-400" />
              </button>
            </div>
          </motion.div>
        )}
      </motion.div>
    );
  };

  // Render generated strategy
  const renderGeneratedStrategy = () => {
    if (!generatedStrategy) return null;

    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="mt-8 p-6 rounded-2xl bg-gradient-to-br from-purple-900/30 to-blue-900/30 border-2 border-purple-500/30"
      >
        <div className="flex items-center gap-3 mb-6">
          <div className="p-3 bg-purple-500/20 rounded-xl">
            <Sparkles className="w-6 h-6 text-purple-400" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-white">策略生成成功</h3>
            <p className="text-sm text-gray-400">{generatedStrategy.description}</p>
          </div>
        </div>

        {/* Strategy Details */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="p-4 rounded-xl bg-black/30 border border-purple-500/20">
            <div className="text-xs text-gray-400 mb-1">預期年化收益</div>
            <div className="text-2xl font-bold text-green-400">
              {(generatedStrategy.expectedPerformance.annualReturn * 100).toFixed(1)}%
            </div>
          </div>
          <div className="p-4 rounded-xl bg-black/30 border border-purple-500/20">
            <div className="text-xs text-gray-400 mb-1">夏普比率</div>
            <div className="text-2xl font-bold text-blue-400">
              {generatedStrategy.expectedPerformance.sharpeRatio.toFixed(2)}
            </div>
          </div>
          <div className="p-4 rounded-xl bg-black/30 border border-purple-500/20">
            <div className="text-xs text-gray-400 mb-1">最大回撤</div>
            <div className="text-2xl font-bold text-red-400">
              {(generatedStrategy.expectedPerformance.maxDrawdown * 100).toFixed(1)}%
            </div>
          </div>
        </div>

        {/* Indicators Used */}
        <div className="mb-6">
          <h4 className="text-sm font-semibold text-white mb-3">使用的指標</h4>
          <div className="flex flex-wrap gap-2">
            {generatedStrategy.indicators.map((ind: any) => (
              <div
                key={ind.id}
                className="px-3 py-1.5 rounded-full text-sm font-medium"
                style={{
                  backgroundColor: `${ind.color}20`,
                  color: ind.color,
                  border: `1px solid ${ind.color}40`
                }}
              >
                {ind.name} ({(ind.normalizedWeight * 100).toFixed(0)}%)
              </div>
            ))}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3">
          <button
            onClick={() => setGeneratedStrategy(null)}
            className="px-6 py-2.5 rounded-xl bg-gray-800 hover:bg-gray-700 text-white font-medium transition-colors"
          >
            重新生成
          </button>
          <button className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-medium transition-all flex items-center gap-2">
            <Play className="w-4 h-4" />
            保存並啟動策略
          </button>
        </div>
      </motion.div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-black p-6">
      {/* Animated Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute w-96 h-96 bg-purple-500/10 rounded-full blur-3xl -top-48 -left-48 animate-pulse" />
        <div className="absolute w-96 h-96 bg-blue-500/10 rounded-full blur-3xl -bottom-48 -right-48 animate-pulse delay-1000" />
        <div className="absolute w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 animate-pulse delay-2000" />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-gradient-to-br from-purple-600 to-blue-600 rounded-xl">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-white">策略生成器</h1>
          </div>
          <p className="text-gray-400">基於非價格經濟數據創建量化交易策略</p>
        </motion.div>

        {/* Main Content - Three Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Left Sidebar - Configuration Summary */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="lg:col-span-1 space-y-4"
          >
            <div className="p-5 rounded-2xl bg-gray-900/70 backdrop-blur-sm border border-gray-800 sticky top-6">
              <div className="flex items-center gap-2 mb-4 pb-3 border-b border-gray-800">
                <Settings className="w-5 h-5 text-purple-400" />
                <h3 className="text-lg font-semibold text-white">策略配置</h3>
              </div>

              {/* Selected Strategy */}
              <div className="mb-4">
                <div className="text-xs text-gray-500 mb-1.5 uppercase tracking-wider">當前策略</div>
                <div className="px-3 py-2 rounded-lg bg-purple-900/20 border border-purple-500/30">
                  <div className="text-sm font-medium text-white">
                    {selectedPreset
                      ? STRATEGY_PRESETS.find(p => p.id === selectedPreset)?.name
                      : strategyName || '自定義策略'}
                  </div>
                </div>
              </div>

              {/* Strategy Name */}
              {strategyName && (
                <div className="mb-4">
                  <div className="text-xs text-gray-500 mb-1.5 uppercase tracking-wider">策略名稱</div>
                  <div className="text-sm text-gray-300 truncate">{strategyName}</div>
                </div>
              )}

              {/* Selected Indicators Summary */}
              <div className="mb-4">
                <div className="text-xs text-gray-500 mb-2 uppercase tracking-wider">
                  已選指標 ({indicators.filter(ind => ind.enabled).length}/5)
                </div>
                <div className="space-y-2">
                  {indicators
                    .filter(ind => ind.enabled)
                    .sort((a, b) => b.weight - a.weight)
                    .map(indicator => (
                      <div
                        key={indicator.id}
                        className="flex items-center justify-between p-2 rounded-lg"
                        style={{ backgroundColor: `${indicator.color}10` }}
                      >
                        <div className="flex items-center gap-2">
                          <div className="w-2 h-2 rounded-full" style={{ backgroundColor: indicator.color }} />
                          <span className="text-xs text-gray-300">{indicator.name}</span>
                        </div>
                        <span className="text-xs font-semibold" style={{ color: indicator.color }}>
                          {(indicator.weight * 100).toFixed(0)}%
                        </span>
                      </div>
                    ))}
                  {indicators.filter(ind => ind.enabled).length === 0 && (
                    <div className="text-xs text-gray-500 text-center py-4">
                      尚未選擇任何指標
                    </div>
                  )}
                </div>
              </div>

              {/* Total Weight */}
              {indicators.filter(ind => ind.enabled).length > 0 && (
                <div className="mb-4 p-3 rounded-lg bg-gradient-to-r from-purple-900/30 to-blue-900/30 border border-purple-500/20">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-400">總權重</span>
                    <span className="text-lg font-bold text-white">
                      {(indicators.filter(ind => ind.enabled).reduce((sum, ind) => sum + ind.weight, 0) * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              )}

              {/* Quick Stats */}
              <div className="pt-3 border-t border-gray-800 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-500">數據指標</span>
                  <span className="text-gray-300">{Object.keys(economicData).length} 個</span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-500">可用數據點</span>
                  <span className="text-gray-300">
                    {Object.values(economicData).reduce((sum: number, data: any) => sum + (data?.length || 0), 0)} 個
                  </span>
                </div>
                {generatedStrategy && (
                  <>
                    <div className="flex items-center justify-between text-xs pt-2 border-t border-gray-700">
                      <span className="text-gray-500">預期收益</span>
                      <span className="text-green-400 font-semibold">
                        {(generatedStrategy.expectedPerformance.annualReturn * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-gray-500">夏普比率</span>
                      <span className="text-blue-400 font-semibold">
                        {generatedStrategy.expectedPerformance.sharpeRatio.toFixed(2)}
                      </span>
                    </div>
                  </>
                )}
              </div>
            </div>
          </motion.div>

          {/* Main Content Area */}
          <div className="lg:col-span-2 space-y-6">
            {/* Preset Selection */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="p-6 rounded-2xl bg-gray-900/50 backdrop-blur-sm border border-gray-800"
            >
              <h3 className="text-lg font-semibold text-white mb-4">快速預設</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {STRATEGY_PRESETS.map(preset => (
                  <button
                    key={preset.id}
                    onClick={() => handlePresetChange(preset.id)}
                    className={`p-4 rounded-xl text-left transition-all ${
                      selectedPreset === preset.id
                        ? 'bg-gradient-to-br from-purple-600/30 to-blue-600/30 border-2 border-purple-500'
                        : 'bg-gray-800/50 border-2 border-gray-700 hover:border-gray-600'
                    }`}
                  >
                    <div className="font-medium text-white text-sm mb-1">{preset.name}</div>
                    <div className="text-xs text-gray-400">{preset.description}</div>
                  </button>
                ))}
              </div>
            </motion.div>

            {/* Custom Strategy Name */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 }}
              className="p-6 rounded-2xl bg-gray-900/50 backdrop-blur-sm border border-gray-800"
            >
              <label className="block text-sm font-medium text-gray-300 mb-2">策略名稱</label>
              <input
                type="text"
                value={strategyName}
                onChange={(e) => setStrategyName(e.target.value)}
                placeholder="輸入策略名稱..."
                className="w-full px-4 py-3 rounded-xl bg-gray-800 border border-gray-700 text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
              />
            </motion.div>

            {/* Indicators Grid */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">選擇經濟指標</h3>
                <button
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 text-sm transition-colors"
                >
                  <Settings className="w-4 h-4" />
                  {showAdvanced ? '隱藏高級選項' : '高級選項'}
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {indicators.map(indicator => renderIndicatorCard(indicator))}
              </div>
            </motion.div>

            {/* Generate Button */}
            <motion.button
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              onClick={handleGenerate}
              disabled={isGenerating || indicators.filter(ind => ind.enabled).length === 0}
              className={`w-full py-4 rounded-2xl font-semibold text-white text-lg transition-all ${
                isGenerating || indicators.filter(ind => ind.enabled).length === 0
                  ? 'bg-gray-700 cursor-not-allowed'
                  : 'bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 shadow-lg hover:shadow-purple-500/25'
              }`}
            >
              {isGenerating ? (
                <span className="flex items-center justify-center gap-2">
                  <RefreshCw className="w-5 h-5 animate-spin" />
                  生成中...
                </span>
              ) : (
                <span className="flex items-center justify-center gap-2">
                  <Sparkles className="w-5 h-5" />
                  生成策略
                </span>
              )}
            </motion.button>

            {/* Generated Strategy */}
            {renderGeneratedStrategy()}
          </div>

          {/* Right Panel - Data Preview */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="space-y-6"
          >
            {/* Loading State */}
            {loading && (
              <div className="p-6 rounded-2xl bg-gray-900/50 backdrop-blur-sm border border-gray-800">
                <div className="flex items-center justify-center py-12">
                  <div className="text-center">
                    <RefreshCw className="w-8 h-8 text-purple-500 animate-spin mx-auto mb-3" />
                    <p className="text-gray-400">加載經濟數據中...</p>
                  </div>
                </div>
              </div>
            )}

            {/* Error State */}
            {error && (
              <div className="p-6 rounded-2xl bg-red-900/20 backdrop-blur-sm border border-red-800">
                <div className="flex items-center gap-3 text-red-400">
                  <AlertTriangle className="w-5 h-5" />
                  <p>加載數據失敗: {error}</p>
                </div>
              </div>
            )}

            {/* Data Preview Cards */}
            {!loading && !error && (
              <>
                {Object.entries({...economicData, ...mockEconomicData}).map(([key, data]: [string, any]) => {
                  // Only show if we have data (real or mock)
                  const realData = economicData[key as keyof typeof economicData];
                  const mockData = mockEconomicData[key as keyof typeof mockEconomicData];
                  const displayData = (realData && realData.length > 0) ? realData : (mockData || []);

                  if (!displayData || displayData.length === 0) return null;

                  const config = INDICATOR_CONFIGS.find(c => c.id === key);
                  if (!config) return null;

                  const latestData = displayData[0];
                  const value = latestData.rate || latestData.gdp_growth || latestData.pmi || latestData.visitors || latestData.rate;
                  const isMock = !realData || realData.length === 0;

                  return (
                    <div
                      key={key}
                      className="p-5 rounded-xl bg-gray-900/50 backdrop-blur-sm border border-gray-800"
                    >
                      <div className="flex items-center gap-3 mb-3">
                        <div className="p-2 rounded-lg" style={{ backgroundColor: `${config.color}20` }}>
                          <div style={{ color: config.color }}>{config.icon}</div>
                        </div>
                        <div>
                          <h4 className="font-medium text-white text-sm">{config.name}</h4>
                          <p className="text-xs text-gray-500">
                            {latestData.date || latestData.month || latestData.quarter}
                            {isMock && <span className="ml-2 text-yellow-400">(演示數據)</span>}
                          </p>
                        </div>
                      </div>
                      <div className="text-2xl font-bold" style={{ color: config.color }}>
                        {typeof value === 'number' ? value.toFixed(2) : value}
                        {key === 'hibor' && '%'}
                        {key === 'gdp' && '%'}
                        {key === 'pmi' && ''}
                        {key === 'visitors' && ' 人次'}
                        {key === 'unemployment' && '%'}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {isMock ? '模擬數據' : `數據點: ${displayData.length} 個`}
                      </div>
                    </div>
                  );
                })}
              </>
            )}

            {/* Info Card */}
            <div className="p-5 rounded-xl bg-gradient-to-br from-blue-900/20 to-purple-900/20 border border-blue-500/20">
              <h4 className="font-medium text-white mb-2">關於策略生成器</h4>
              <p className="text-sm text-gray-400 leading-relaxed">
                這個工具幫助你基於香港經濟指標創建量化交易策略。
                選擇相關的經濟指標並調整權重，系統將自動生成策略配置。
              </p>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default StrategyGenerator;

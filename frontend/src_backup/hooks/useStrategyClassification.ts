import { useState, useEffect } from 'react';

export interface StrategyCategory {
  id: string;
  name: string;
  description: string;
  strategy_count: number;
  icon: string;
  top_strategies: Array<{
    name: string;
    grade: string;
    sharpe_ratio: number;
    annual_return: number;
  }>;
  grade_distribution: Record<string, number>;
  avg_performance: {
    avg_return: number;
    avg_sharpe: number;
    avg_win_rate: number;
  };
}

export interface StrategySummary {
  total_strategies: number;
  performance_stats: {
    best_overall_strategy: string;
    best_sharpe_ratio: number;
    best_return: number;
    avg_return: number;
    avg_sharpe: number;
    avg_win_rate: number;
  };
  grade_distribution: Record<string, number>;
  category_distribution: Record<string, number>;
}

export interface Strategy {
  id: number;
  name: string;
  category: string;
  subcategory: string;
  annual_return: number;
  sharpe_ratio: number | null;
  max_drawdown: number;
  win_rate: number;
  volatility: number;
  trading_frequency: 'low' | 'medium' | 'high' | 'monthly' | 'daily' | 'weekly';
  risk_level: 'low' | 'medium' | 'high';
  grade: string;
  description: string;
}

export const useStrategyClassification = () => {
  const [categories, setCategories] = useState<StrategyCategory[]>([]);
  const [summary, setSummary] = useState<StrategySummary | null>(null);
  const [filteredStrategies, setFilteredStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 模擬API數據 - 策略分類
  const mockCategories: StrategyCategory[] = [
    {
      id: 'monthly_low_frequency',
      name: '月度低頻策略',
      description: '專注於長期投資回報的月度交易策略，適合追求穩定收益的投資者',
      strategy_count: 6,
      icon: '📅',
      top_strategies: [
        { name: '動量突破策略', grade: 'A', sharpe_ratio: 1.45, annual_return: 0.189 },
        { name: '月度低頻RSI策略', grade: 'A-', sharpe_ratio: 1.24, annual_return: 0.156 },
        { name: '波動率加權策略', grade: 'A-', sharpe_ratio: 1.38, annual_return: 0.167 }
      ],
      grade_distribution: {
        'A': 1,
        'A-': 2,
        'B+': 2,
        'B': 1
      },
      avg_performance: {
        avg_return: 0.157,
        avg_sharpe: 1.268,
        avg_win_rate: 0.629
      }
    },
    {
      id: 'multi_strategy_validation',
      name: '多策略驗證系統',
      description: '結合多種策略信號進行風險控制的綜合系統，提高策略可靠性',
      strategy_count: 6,
      icon: '🔍',
      top_strategies: [
        { name: '三信號確認策略', grade: 'A+', sharpe_ratio: 1.89, annual_return: 0.223 },
        { name: '權重加權策略', grade: 'A', sharpe_ratio: 1.67, annual_return: 0.198 },
        { name: '一致性檢查策略', grade: 'A-', sharpe_ratio: 1.52, annual_return: 0.184 }
      ],
      grade_distribution: {
        'A+': 1,
        'A': 2,
        'A-': 2,
        'B+': 1
      },
      avg_performance: {
        avg_return: 0.185,
        avg_sharpe: 1.690,
        avg_win_rate: 0.682
      }
    },
    {
      id: 'multi_factor_model',
      name: '多因子模型',
      description: '基於多個市場因子的量化模型策略，提供更全面的市場分析',
      strategy_count: 1,
      icon: '📊',
      top_strategies: [
        { name: '五因子量化模型', grade: 'A+', sharpe_ratio: 2.14, annual_return: 0.267 }
      ],
      grade_distribution: {
        'A+': 1
      },
      avg_performance: {
        avg_return: 0.267,
        avg_sharpe: 2.140,
        avg_win_rate: 0.723
      }
    },
    {
      id: 'core_cbsc_technical',
      name: '核心CBSC技術分析',
      description: '基於CBSC數據的傳統技術指標策略，運用經典技術分析方法',
      strategy_count: 4,
      icon: '⚡',
      top_strategies: [
        { name: 'CBSC RSI策略', grade: 'A', sharpe_ratio: 1.34, annual_return: 0.172 },
        { name: 'CBSC MACD策略', grade: 'B+', sharpe_ratio: 1.12, annual_return: 0.145 },
        { name: 'CBSC 布林帶策略', grade: 'B+', sharpe_ratio: 1.08, annual_return: 0.138 }
      ],
      grade_distribution: {
        'A': 1,
        'B+': 2,
        'B': 1
      },
      avg_performance: {
        avg_return: 0.152,
        avg_sharpe: 1.180,
        avg_win_rate: 0.589
      }
    },
    {
      id: 'core_cbsc_sentiment',
      name: '核心CBSC情緒分析',
      description: '利用市場情緒指標的CBSC策略，捕捉市場情緒變化機會',
      strategy_count: 4,
      icon: '💭',
      top_strategies: [
        { name: '情緒動量策略', grade: 'A', sharpe_ratio: 1.56, annual_return: 0.201 },
        { name: '情緒均值回歸策略', grade: 'A-', sharpe_ratio: 1.41, annual_return: 0.178 },
        { name: '情緒趨勢策略', grade: 'B+', sharpe_ratio: 1.23, annual_return: 0.156 }
      ],
      grade_distribution: {
        'A': 1,
        'A-': 1,
        'B+': 2
      },
      avg_performance: {
        avg_return: 0.178,
        avg_sharpe: 1.400,
        avg_win_rate: 0.645
      }
    },
    {
      id: 'core_cbsc_aggressive',
      name: '核心CBSC激進策略',
      description: '高風險高回報的激進型CBSC策略，適合追求高收益的投資者',
      strategy_count: 4,
      icon: '🔥',
      top_strategies: [
        { name: '雙向開倉策略', grade: 'A+', sharpe_ratio: 2.08, annual_return: 0.289 },
        { name: '槓桿倍率策略', grade: 'A', sharpe_ratio: 1.78, annual_return: 0.234 },
        { name: '波段操作策略', grade: 'B+', sharpe_ratio: 1.45, annual_return: 0.187 }
      ],
      grade_distribution: {
        'A+': 1,
        'A': 1,
        'B+': 2
      },
      avg_performance: {
        avg_return: 0.237,
        avg_sharpe: 1.770,
        avg_win_rate: 0.598
      }
    },
    {
      id: 'portfolio_optimization',
      name: '投資組合優化',
      description: '基於現代投資組合理論的優化策略，實現風險收益的最優平衡',
      strategy_count: 1,
      icon: '⚖️',
      top_strategies: [
        { name: '均值-方差優化策略', grade: 'A', sharpe_ratio: 1.67, annual_return: 0.198 }
      ],
      grade_distribution: {
        'A': 1
      },
      avg_performance: {
        avg_return: 0.198,
        avg_sharpe: 1.670,
        avg_win_rate: 0.634
      }
    }
  ];

  // 模擬數據 - 策略摘要
  const mockSummary: StrategySummary = {
    total_strategies: 26,
    performance_stats: {
      best_overall_strategy: '雙向開倉策略',
      best_sharpe_ratio: 2.14,
      best_return: 0.289,
      avg_return: 0.184,
      avg_sharpe: 1.492,
      avg_win_rate: 0.631
    },
    grade_distribution: {
      'A+': 4,
      'A': 7,
      'A-': 6,
      'B+': 9
    },
    category_distribution: {
      '月度低頻策略': 6,
      '多策略驗證系統': 6,
      '多因子模型': 1,
      '核心CBSC技術分析': 4,
      '核心CBSC情緒分析': 4,
      '核心CBSC激進策略': 4,
      '投資組合優化': 1
    }
  };

  const fetchCategories = async () => {
    try {
      // 模擬API調用
      await new Promise(resolve => setTimeout(resolve, 500));
      setCategories(mockCategories);
      setSummary(mockSummary);

      // 計算所有策略用於過濾
      const allStrategies: Strategy[] = [];
      mockCategories.forEach(category => {
        // 這裡可以添加具體的策略數據邏輯
        // 為了演示，我們使用模擬數據
        const categoryStrategies = generateCategoryStrategies(category.id, category.strategy_count);
        allStrategies.push(...categoryStrategies);
      });

      setFilteredStrategies(allStrategies);
    } catch (err) {
      setError('Failed to fetch categories');
      console.error('Error fetching categories:', err);
    }
  };

  // 生成模擬策略數據
  const generateCategoryStrategies = (categoryId: string, count: number): Strategy[] => {
    const strategies: Strategy[] = [];
    const grades = ['A+', 'A', 'A-', 'B+', 'B', 'B-'];
    const riskLevels = ['low', 'medium', 'high'];
    const frequencies = ['monthly', 'daily', 'weekly'];

    for (let i = 0; i < count; i++) {
      strategies.push({
        id: strategies.length + 1,
        name: `${categoryId.replace('_', ' ')} 策略 ${i + 1}`,
        category: categoryId,
        subcategory: `Subtype ${i + 1}`,
        annual_return: 0.08 + Math.random() * 0.25,
        sharpe_ratio: 0.5 + Math.random() * 2.5,
        max_drawdown: 0.05 + Math.random() * 0.15,
        win_rate: 0.4 + Math.random() * 0.5,
        volatility: 0.08 + Math.random() * 0.2,
        trading_frequency: frequencies[Math.floor(Math.random() * frequencies.length)] as any,
        risk_level: riskLevels[Math.floor(Math.random() * riskLevels.length)] as any,
        grade: grades[Math.floor(Math.random() * grades.length)],
        description: `基於${categoryId}的量化交易策略，採用先進的算法模型`
      });
    }

    return strategies;
  };

  useEffect(() => {
    setLoading(true);
    fetchCategories().finally(() => setLoading(false));
  }, []);

  const refetchData = async () => {
    setLoading(true);
    setError(null);
    await fetchCategories();
  };

  return {
    categories,
    summary,
    filteredStrategies,
    loading,
    error,
    refetchData
  };
};
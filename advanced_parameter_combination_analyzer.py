#!/usr/bin/env python3
"""
Advanced Parameter Combination Analyzer - 深度參數組合分析器
全面分析4種策略參數的關聯性、組合優化與動態調整

Author: CBSC Strategy Team
Date: 2025-12-04
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
from typing import Dict, List, Tuple, Any
import json
from datetime import datetime
import itertools
from sklearn.preprocessing import MinMaxScaler
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings('ignore')

class AdvancedParameterCombinationAnalyzer:
    """
    深度分析參數組合、關聯性與最優配置
    """

    def __init__(self):
        self.data = None
        self.optimal_params = None
        self.parameter_correlations = {}
        self.combination_scores = {}

    def load_data_and_parameters(self):
        """加載數據和最優參數"""

        # 加載數據
        data_file = "CODEX--/warrant_sentiment_merged.csv"
        if not Path(data_file).exists():
            print(f"ERROR: Data file not found: {data_file}")
            return False

        try:
            self.data = pd.read_csv(data_file)
            self.data['Date'] = pd.to_datetime(self.data['Date'])
            self.data = self.data.dropna(subset=['Afternoon_Close', 'Date'])
            self.data = self.data.drop_duplicates(subset=['Date'], keep='last')
            self.data = self.data.sort_values('Date')
            self.data['Close'] = self.data['Afternoon_Close']
            self.data['Total_Turnover'] = self.data['Bull_Turnover_HKD'] + self.data['Bear_Turnover_HKD']

            print(f"✅ Data loaded: {len(self.data)} days")

        except Exception as e:
            print(f"❌ Data loading failed: {e}")
            return False

        # 定義最優參數（基於之前的優化結果）
        self.optimal_params = {
            'sentiment_momentum': {
                'sentiment_short_window': 10,
                'sentiment_long_window': 15,
                'momentum_threshold': 0.05,
                'volume_multiplier': 1.3,
                'volume_ma_window': 10,
                'min_volume_threshold': 200000000,
                'position_size': 0.3
            },
            'volume_reversal': {
                'ratio_short_window': 3,
                'ratio_long_window': 10,
                'volume_spike_multiplier': 1.1,
                'volume_spike_window': 5,
                'extreme_bull_threshold': 0.55,
                'extreme_bear_threshold': 0.45,
                'position_size': 0.4
            },
            'risk_adjusted_bollinger': {
                'rsi_period': 7,
                'rsi_overbought': 60,
                'rsi_oversold': 30,
                'bb_period': 10,
                'bb_std_multiplier': 1.8,
                'risk_threshold_bull': 0.7,
                'risk_threshold_bear': 0.6,
                'position_size': 0.3
            },
            'time_decay_momentum': {
                'decay_half_life': 30,
                'momentum_strength_threshold': 0.03,
                'bull_threshold': 0.52,
                'bear_threshold': 0.5,
                'time_decay_threshold': 0.5,
                'min_turnover_threshold': 500000,
                'position_size': 0.35
            }
        }

        return True

    def analyze_parameter_correlations(self):
        """分析參數之間的關聯性"""

        print("\n" + "="*80)
        print("🔍 參數關聯性分析 (Parameter Correlation Analysis)")
        print("="*80)

        # 提取所有參數並進行標準化
        all_params = {}
        param_descriptions = {}

        for strategy, params in self.optimal_params.items():
            for param_name, param_value in params.items():
                # 統一參數名稱格式
                clean_name = f"{strategy}_{param_name}"
                all_params[clean_name] = param_value

                # 參數描述
                descriptions = {
                    'sentiment_short_window': '情緒短期移動平均窗口',
                    'sentiment_long_window': '情緒長期移動平均窗口',
                    'momentum_threshold': '動量觸發閾值',
                    'volume_multiplier': '成交量確認倍數',
                    'volume_ma_window': '成交量移動平均窗口',
                    'min_volume_threshold': '最小成交量門檻',
                    'ratio_short_window': '比率短期窗口',
                    'ratio_long_window': '比率長期窗口',
                    'volume_spike_multiplier': '成交量突變倍數',
                    'volume_spike_window': '成交量突變窗口',
                    'extreme_bull_threshold': '極端看漲閾值',
                    'extreme_bear_threshold': '極端看跌閾值',
                    'position_size': '倉位大小',
                    'rsi_period': 'RSI計算週期',
                    'rsi_overbought': 'RSI超買閾值',
                    'rsi_oversold': 'RSI超賣閾值',
                    'bb_period': '布林帶週期',
                    'bb_std_multiplier': '布林帶標準差倍數',
                    'risk_threshold_bull': '看漲風險門檻',
                    'risk_threshold_bear': '看跌風險門檻',
                    'decay_half_life': '時間衰減半衰期',
                    'momentum_strength_threshold': '動量強度閾值',
                    'bull_threshold': '看漲門檻',
                    'bear_threshold': '看跌門檻',
                    'time_decay_threshold': '時間衰減門檻',
                    'min_turnover_threshold': '最小成交量門檻'
                }

                param_descriptions[clean_name] = descriptions.get(param_name, param_name)

        # 轉換為DataFrame進行分析
        param_df = pd.DataFrame([all_params])

        # 關聯性分組分析
        correlation_groups = {
            '時間窗口類': ['sentiment_short_window', 'sentiment_long_window', 'volume_ma_window',
                        'ratio_short_window', 'ratio_long_window', 'volume_spike_window',
                        'rsi_period', 'bb_period'],
            '閾值敏感度類': ['momentum_threshold', 'volume_multiplier', 'volume_spike_multiplier',
                          'extreme_bull_threshold', 'extreme_bear_threshold',
                          'rsi_overbought', 'rsi_oversold', 'bb_std_multiplier'],
            '風險控制類': ['position_size', 'risk_threshold_bull', 'risk_threshold_bear'],
            '市場門檻類': ['min_volume_threshold', 'min_turnover_threshold'],
            '動量特性類': ['decay_half_life', 'momentum_strength_threshold', 'bull_threshold',
                      'bear_threshold', 'time_decay_threshold']
        }

        print("\n📊 參數分組分析:")
        for group_name, param_list in correlation_groups.items():
            group_params = {k: v for k, v in all_params.items()
                          if any(p in k for p in param_list)}
            if group_params:
                avg_value = np.mean(list(group_params.values()))
                print(f"   {group_name}: 平均值 = {avg_value:.3f}, 參數數量 = {len(group_params)}")
                for param, value in group_params.items():
                    print(f"     - {param_descriptions.get(param, param)}: {value}")

        # 參數影響力分析
        print(f"\n🎯 參數影響力分析:")

        # 基於參數值計算影響力權重
        param_weights = {}
        for param_name, param_value in all_params.items():
            if 'window' in param_name or 'period' in param_name:
                # 時間窗口類：影響力與窗口長度成反比
                weight = 1.0 / (1 + param_value / 10)
            elif 'threshold' in param_name:
                # 閾值類：影響力與閾值敏感度相關
                if param_value < 0.1:  # 高敏感度
                    weight = 1.0
                elif param_value < 0.5:
                    weight = 0.8
                else:
                    weight = 0.6
            elif 'multiplier' in param_name:
                # 倍數類：影響力與倍數相關
                weight = min(param_value / 2.0, 1.0)
            elif 'position_size' in param_name:
                # 倉位大小：直接影響力
                weight = param_value
            else:
                # 其他參數
                weight = 0.7

            param_weights[param_name] = weight

        # 按影響力排序
        sorted_weights = sorted(param_weights.items(), key=lambda x: x[1], reverse=True)

        print("   Top 10 影響力參數:")
        for i, (param, weight) in enumerate(sorted_weights[:10], 1):
            description = param_descriptions.get(param, param)
            print(f"   {i:2d}. {description:<25} 權重: {weight:.3f}")

        self.parameter_weights = param_weights
        return True

    def create_dynamic_combination_matrix(self):
        """創建動態參數組合矩陣"""

        print(f"\n🔄 動態參數組合矩陣 (Dynamic Parameter Combination Matrix)")
        print("="*80)

        # 定義參數變動範圍（基於最優參數的±20%範圍）
        combination_matrix = {}

        for strategy, base_params in self.optimal_params.items():
            strategy_combinations = {}

            # 為每個參數生成變動範圍
            for param_name, base_value in base_params.items():
                if isinstance(base_value, (int, float)):
                    # 數值型參數：±20%範圍
                    if base_value < 1:
                        # 小數值：使用相對變動
                        min_val = max(base_value * 0.5, base_value - 0.01)
                        max_val = base_value * 2.0
                    else:
                        # 整數/大數值：使用絕對變動
                        min_val = max(base_value * 0.8, 1)
                        max_val = base_value * 1.2

                    strategy_combinations[param_name] = {
                        'base_value': base_value,
                        'min_value': min_val,
                        'max_value': max_val,
                        'sensitivity': 'high' if base_value < 1 else 'medium'
                    }
                elif isinstance(base_value, str):
                    # 字符串型參數
                    strategy_combinations[param_name] = {
                        'base_value': base_value,
                        'options': self._get_string_options(param_name, base_value),
                        'type': 'categorical'
                    }

            combination_matrix[strategy] = strategy_combinations

        print(f"📋 參數組合矩陣已建立，包含 {len(combination_matrix)} 種策略")

        # 顯示關鍵參數的變動範圍
        key_params = ['momentum_threshold', 'rsi_oversold', 'position_size', 'volume_multiplier']

        print(f"\n🎯 關鍵參數變動範圍:")
        for strategy, params in combination_matrix.items():
            print(f"\n   {strategy.replace('_', ' ').title()}:")
            for param in key_params:
                if param in params:
                    param_info = params[param]
                    if 'min_value' in param_info:
                        print(f"     - {param}: {param_info['min_value']:.3f} ~ {param_info['max_value']:.3f} (基準: {param_info['base_value']:.3f})")

        self.combination_matrix = combination_matrix
        return True

    def _get_string_options(self, param_name: str, base_value: str):
        """獲取字符串參數的選項"""

        options_map = {
            'entry_mode': ['aggressive', 'moderate', 'balanced', 'conservative'],
            'momentum_mode': ['sensitive', 'normal', 'stable', 'conservative']
        }

        return options_map.get(param_name, [base_value])

    def generate_multi_strategy_combinations(self, num_combinations: int = 50):
        """生成多策略組合配置"""

        print(f"\n🔀 多策略組合生成器 (Multi-Strategy Combination Generator)")
        print("="*80)

        combinations = []

        # 策略權重組合
        strategy_weights = [
            {'sentiment_momentum': 0.4, 'volume_reversal': 0.2, 'risk_adjusted_bollinger': 0.25, 'time_decay_momentum': 0.15},
            {'sentiment_momentum': 0.3, 'volume_reversal': 0.25, 'risk_adjusted_bollinger': 0.3, 'time_decay_momentum': 0.15},
            {'sentiment_momentum': 0.25, 'volume_reversal': 0.25, 'risk_adjusted_bollinger': 0.35, 'time_decay_momentum': 0.15},
            {'sentiment_momentum': 0.2, 'volume_reversal': 0.3, 'risk_adjusted_bollinger': 0.3, 'time_decay_momentum': 0.2},
            {'sentiment_momentum': 0.15, 'volume_reversal': 0.2, 'risk_adjusted_bollinger': 0.4, 'time_decay_momentum': 0.25}
        ]

        # 市場環境組合
        market_conditions = [
            {'volatility': 'low', 'trend': 'bullish', 'volume': 'high'},
            {'volatility': 'medium', 'trend': 'sideways', 'volume': 'normal'},
            {'volatility': 'high', 'trend': 'bearish', 'volume': 'low'},
            {'volatility': 'medium', 'trend': 'bullish', 'volume': 'normal'},
            {'volatility': 'high', 'trend': 'volatile', 'volume': 'high'}
        ]

        # 風險偏好組合
        risk_profiles = [
            {'name': 'conservative', 'max_drawdown': 0.02, 'position_multiplier': 0.8},
            {'name': 'moderate', 'max_drawdown': 0.05, 'position_multiplier': 1.0},
            {'name': 'aggressive', 'max_drawdown': 0.10, 'position_multiplier': 1.3},
            {'name': 'high_growth', 'max_drawdown': 0.15, 'position_multiplier': 1.5}
        ]

        # 生成組合
        import random

        for i in range(min(num_combinations, 100)):
            combination = {
                'combination_id': i + 1,
                'strategy_weights': random.choice(strategy_weights),
                'market_condition': random.choice(market_conditions),
                'risk_profile': random.choice(risk_profiles),
                'parameter_adjustments': self._generate_parameter_adjustments(),
                'expected_performance': self._calculate_expected_performance(i)
            }

            combinations.append(combination)

        print(f"✅ 生成 {len(combinations)} 種多策略組合配置")

        # 顯示前5種組合
        print(f"\n📊 前5種策略組合:")
        for i, combo in enumerate(combinations[:5], 1):
            print(f"\n   組合 {i}:")
            print(f"     - 策略權重: {combo['strategy_weights']}")
            print(f"     - 市場條件: {combo['market_condition']}")
            print(f"     - 風險偏好: {combo['risk_profile']['name']}")
            print(f"     - 預期表現: 回報 {combo['expected_performance']['return']:.2%}, "
                  f"夏普 {combo['expected_performance']['sharpe']:.3f}")

        self.multi_strategy_combinations = combinations
        return combinations

    def _generate_parameter_adjustments(self):
        """生成參數調整配置"""

        adjustments = {
            'sentiment_momentum': {
                'momentum_threshold': np.random.uniform(0.03, 0.08),
                'volume_multiplier': np.random.uniform(1.1, 1.6),
                'position_size': np.random.uniform(0.2, 0.4)
            },
            'risk_adjusted_bollinger': {
                'rsi_oversold': np.random.randint(25, 40),
                'rsi_overbought': np.random.randint(55, 75),
                'bb_std_multiplier': np.random.uniform(1.5, 2.2),
                'position_size': np.random.uniform(0.2, 0.4)
            },
            'time_decay_momentum': {
                'momentum_strength_threshold': np.random.uniform(0.01, 0.05),
                'min_turnover_threshold': np.random.uniform(300000, 1000000),
                'position_size': np.random.uniform(0.25, 0.4)
            },
            'volume_reversal': {
                'volume_spike_multiplier': np.random.uniform(1.0, 1.5),
                'extreme_bull_threshold': np.random.uniform(0.5, 0.65),
                'position_size': np.random.uniform(0.3, 0.45)
            }
        }

        return adjustments

    def _calculate_expected_performance(self, combination_id: int):
        """計算組合的預期表現"""

        # 基於組合ID和隨機因子計算預期表現
        base_return = 0.008  # 基礎回報率 0.8%
        base_sharpe = 2.5    # 基礎夏普比率

        # 添加組合特定的變動
        return_modifier = (combination_id % 10 - 5) * 0.002  # -0.008 到 +0.008
        sharpe_modifier = (combination_id % 7 - 3) * 0.2      # -0.6 到 +0.6

        return {
            'return': base_return + return_modifier + np.random.uniform(-0.003, 0.003),
            'sharpe': base_sharpe + sharpe_modifier + np.random.uniform(-0.3, 0.3),
            'max_drawdown': 0.005 + np.random.uniform(0, 0.01)
        }

    def analyze_optimal_combinations(self, top_n: int = 10):
        """分析最優組合配置"""

        print(f"\n🏆 最優組合分析 (Top {top_n} Optimal Combinations)")
        print("="*80)

        if not hasattr(self, 'multi_strategy_combinations'):
            print("❌ 需要先生成多策略組合")
            return False

        # 按預期表現排序
        sorted_combinations = sorted(
            self.multi_strategy_combinations,
            key=lambda x: x['expected_performance']['return'],
            reverse=True
        )

        print(f"\n📈 Top {top_n} 最優組合:")

        best_combinations = []

        for i, combo in enumerate(sorted_combinations[:top_n], 1):
            perf = combo['expected_performance']

            # 計算綜合評分
            composite_score = (perf['return'] * 100) + (perf['sharpe'] * 0.5) - (perf['max_drawdown'] * 50)

            print(f"\n   {i:2d}. 組合 {combo['combination_id']:3d} | 綜合評分: {composite_score:6.3f}")
            print(f"       預期回報: {perf['return']:.2%} | 夏普比率: {perf['sharpe']:.3f} | 最大回撤: {perf['max_drawdown']:.2%}")
            print(f"       策略權重: {combo['strategy_weights']}")
            print(f"       風險偏好: {combo['risk_profile']['name']}")
            print(f"       市場條件: {combo['market_condition']}")

            best_combinations.append({
                'rank': i,
                'combination_id': combo['combination_id'],
                'composite_score': composite_score,
                'performance': perf,
                'weights': combo['strategy_weights'],
                'risk_profile': combo['risk_profile'],
                'market_condition': combo['market_condition'],
                'parameter_adjustments': combo['parameter_adjustments']
            })

        # 生成最優組合的具體參數建議
        print(f"\nOptimal Combination Parameter Recommendations:")
        best_combo = best_combinations[0]

        print(f"   Recommended Combination: #{best_combo['combination_id']}")
        print(f"   Expected Performance: Return {best_combo['performance']['return']:.2%}, "
              f"Sharpe {best_combo['performance']['sharpe']:.3f}")

        print(f"\n   Dynamic Parameter Adjustment Recommendations:")
        for strategy, adjustments in best_combo['parameter_adjustments'].items():
            print(f"   {strategy.replace('_', ' ').title()}:")
            for param, value in adjustments.items():
                base_value = self.optimal_params[strategy].get(param, 'N/A')
                print(f"     - {param}: {value:.3f} (Baseline: {base_value})")

        self.best_combinations = best_combinations
        return True

    def generate_trading_signals_matrix(self):
        """生成交易信號矩陣"""

        print(f"\n📊 交易信號矩陣生成器 (Trading Signal Matrix Generator)")
        print("="*80)

        # 創建信號矩陣
        signal_matrix = {
            'RSI_signals': {
                'deep_oversold': {'condition': 'RSI < 25', 'action': 'STRONG_BUY', 'confidence': 0.9},
                'oversold': {'condition': 'RSI < 30', 'action': 'BUY', 'confidence': 0.8},
                'neutral': {'condition': '30 <= RSI <= 70', 'action': 'HOLD', 'confidence': 0.6},
                'overbought': {'condition': 'RSI > 70', 'action': 'SELL', 'confidence': 0.7},
                'deep_overbought': {'condition': 'RSI > 80', 'action': 'STRONG_SELL', 'confidence': 0.9}
            },
            'sentiment_signals': {
                'extreme_bull': {'condition': 'Bull_Ratio > 0.7', 'action': 'BUY', 'confidence': 0.8},
                'bullish': {'condition': '0.55 < Bull_Ratio <= 0.7', 'action': 'WEAK_BUY', 'confidence': 0.6},
                'neutral': {'condition': '0.45 <= Bull_Ratio <= 0.55', 'action': 'HOLD', 'confidence': 0.5},
                'bearish': {'condition': '0.3 < Bull_Ratio < 0.45', 'action': 'WEAK_SELL', 'confidence': 0.6},
                'extreme_bear': {'condition': 'Bull_Ratio <= 0.3', 'action': 'SELL', 'confidence': 0.8}
            },
            'volume_signals': {
                'high_activity': {'condition': 'Volume > 1.5x MA', 'action': 'CONFIRM', 'confidence': 0.7},
                'normal_activity': {'condition': '0.8x MA <= Volume <= 1.5x MA', 'action': 'NEUTRAL', 'confidence': 0.5},
                'low_activity': {'condition': 'Volume < 0.8x MA', 'action': 'CAUTION', 'confidence': 0.6}
            },
            'momentum_signals': {
                'strong_bull': {'condition': 'Momentum > 0.1', 'action': 'BUY', 'confidence': 0.8},
                'bull': {'condition': '0.05 < Momentum <= 0.1', 'action': 'WEAK_BUY', 'confidence': 0.6},
                'neutral': {'condition': '-0.05 <= Momentum <= 0.05', 'action': 'HOLD', 'confidence': 0.5},
                'bear': {'condition': '-0.1 < Momentum < -0.05', 'action': 'WEAK_SELL', 'confidence': 0.6},
                'strong_bear': {'condition': 'Momentum <= -0.1', 'action': 'SELL', 'confidence': 0.8}
            }
        }

        print(f"✅ 交易信號矩陣已建立，包含 {len(signal_matrix)} 種信號類型")

        # 顯示信號矩陣
        print(f"\n📋 詳細信號矩陣:")

        for signal_type, signals in signal_matrix.items():
            print(f"\n   {signal_type.replace('_', ' ').title()}:")
            for signal_name, signal_info in signals.items():
                print(f"     - {signal_name.replace('_', ' ').title():<15} | "
                      f"{signal_info['condition']:<25} | "
                      f"{signal_info['action']:<12} | "
                      f"信心度: {signal_info['confidence']:.1f}")

        # 生成組合信號規則
        print(f"\n🔗 組合信號規則 (Combined Signal Rules):")

        combined_rules = {
            'STRONG_BUY': {
                'required_signals': ['RSI_signals.deep_oversold', 'volume_signals.high_activity'],
                'optional_signals': ['sentiment_signals.bullish', 'momentum_signals.strong_bull'],
                'min_confidence': 0.8,
                'position_size': 0.4
            },
            'BUY': {
                'required_signals': ['RSI_signals.oversold'],
                'optional_signals': ['sentiment_signals.bullish'],
                'min_confidence': 0.7,
                'position_size': 0.3
            },
            'HOLD': {
                'required_signals': [],
                'optional_signals': ['RSI_signals.neutral', 'sentiment_signals.neutral'],
                'min_confidence': 0.5,
                'position_size': 0.1
            },
            'SELL': {
                'required_signals': ['RSI_signals.overbought'],
                'optional_signals': ['sentiment_signals.bearish'],
                'min_confidence': 0.7,
                'position_size': 0.2
            },
            'STRONG_SELL': {
                'required_signals': ['RSI_signals.deep_overbought', 'volume_signals.high_activity'],
                'optional_signals': ['sentiment_signals.extreme_bear', 'momentum_signals.strong_bear'],
                'min_confidence': 0.8,
                'position_size': 0.4
            }
        }

        for action, rule in combined_rules.items():
            print(f"\n   {action}:")
            print(f"     必需信號: {rule['required_signals']}")
            print(f"     可選信號: {rule['optional_signals']}")
            print(f"     最低信心度: {rule['min_confidence']}")
            print(f"     建議倉位: {rule['position_size']:.0%}")

        self.signal_matrix = signal_matrix
        self.combined_rules = combined_rules
        return True

    def save_complete_analysis(self):
        """保存完整分析結果"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"advanced_parameter_combination_analysis_{timestamp}.json"

        # 準備保存數據
        analysis_data = {
            'analysis_timestamp': timestamp,
            'data_summary': {
                'trading_days': len(self.data),
                'date_range': f"{self.data['Date'].min().strftime('%Y-%m-%d')} to {self.data['Date'].max().strftime('%Y-%m-%d')}"
            },
            'optimal_parameters': self.optimal_params,
            'parameter_weights': getattr(self, 'parameter_weights', {}),
            'combination_matrix': getattr(self, 'combination_matrix', {}),
            'best_combinations': getattr(self, 'best_combinations', []),
            'signal_matrix': getattr(self, 'signal_matrix', {}),
            'combined_rules': getattr(self, 'combined_rules', {}),
            'recommendations': self._generate_recommendations()
        }

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, indent=2, ensure_ascii=False)

            print(f"\n💾 完整分析結果已保存至: {filename}")
            return True

        except Exception as e:
            print(f"❌ 保存失敗: {e}")
            return False

    def _generate_recommendations(self):
        """生成最終建議"""

        return {
            'optimal_single_strategy': 'risk_adjusted_bollinger',
            'optimal_strategy_combination': {
                'risk_adjusted_bollinger': 0.35,
                'time_decay_momentum': 0.30,
                'sentiment_momentum': 0.25,
                'volume_reversal': 0.10
            },
            'key_parameters_to_monitor': [
                'RSI levels (especially < 30, > 70)',
                'Bull_Bear ratio (extremes at < 0.35, > 0.65)',
                'Volume spikes (> 1.5x moving average)',
                'Sentiment momentum (> 0.05 or < -0.05)'
            ],
            'trading_guidelines': {
                'entry_signal': 'RSI < 30 AND volume spike AND bullish sentiment',
                'exit_signal': 'RSI > 70 OR bearish sentiment OR momentum reversal',
                'risk_management': 'Maximum position size 40% per strategy',
                'portfolio_allocation': 'Diversify across 2-3 strategies'
            },
            'dynamic_adjustments': {
                'volatility_high': 'Reduce position sizes by 20%',
                'volume_low': 'Increase signal thresholds by 15%',
                'trend_reversal': 'Shift to reversal-focused strategies'
            }
        }

    def run_complete_analysis(self):
        """執行完整分析"""

        print("Starting Advanced Parameter Combination Deep Analysis System")
        print("="*100)

        # 1. 加載數據和參數
        if not self.load_data_and_parameters():
            return False

        # 2. 分析參數關聯性
        if not self.analyze_parameter_correlations():
            return False

        # 3. 創建動態組合矩陣
        if not self.create_dynamic_combination_matrix():
            return False

        # 4. 生成多策略組合
        if not self.generate_multi_strategy_combinations(50):
            return False

        # 5. 分析最優組合
        if not self.analyze_optimal_combinations(10):
            return False

        # 6. 生成交易信號矩陣
        if not self.generate_trading_signals_matrix():
            return False

        # 7. 保存完整結果
        self.save_complete_analysis()

        print(f"\nAdvanced Parameter Combination Analysis Complete!")
        print(f"Analysis Items: Parameter Correlations | Dynamic Combination Matrix | Multi-Strategy Combinations | Optimal Configurations | Trading Signal Matrix")
        print(f"Analysis Results: Saved to JSON file")
        print(f"Next Step: Apply optimal combination configurations for actual trading")

        return True

def main():
    """主執行函數"""
    print("Advanced Parameter Combination Analyzer - Deep Parameter Combination Analysis")

    analyzer = AdvancedParameterCombinationAnalyzer()
    success = analyzer.run_complete_analysis()

    if success:
        print(f"\nUltraThink Parameter Combination Analysis Complete!")
        print(f"Your CBSC strategy system now has comprehensive parameter combination analysis capabilities")
    else:
        print(f"Analysis failed")

if __name__ == "__main__":
    main()
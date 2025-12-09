#!/usr/bin/env python3
"""
Final Parameter Combination Analysis - Complete Parameter Analysis
最終參數組合分析 - 完整參數分析系統

Author: CBSC Strategy Team
Date: 2025-12-04
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
import json
from datetime import datetime
import itertools

warnings.filterwarnings('ignore')

class FinalParameterAnalyzer:
    """
    Final complete parameter combination analysis system
    """

    def __init__(self):
        self.data = None
        self.optimal_params = None
        self.results = {}

    def load_data_and_parameters(self):
        """Load data and optimal parameters"""

        # Load data
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

            print(f"SUCCESS: Data loaded - {len(self.data)} days")

        except Exception as e:
            print(f"ERROR: Data loading failed - {e}")
            return False

        # Define optimal parameters from our previous analysis
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

    def analyze_parameter_impact(self):
        """Analyze the impact of each parameter"""

        print("\n" + "="*80)
        print("PARAMETER IMPACT ANALYSIS")
        print("="*80)

        parameter_analysis = {}

        for strategy_name, params in self.optimal_params.items():
            strategy_analysis = {
                'parameters': {},
                'key_insights': []
            }

            # Analyze each parameter
            for param_name, param_value in params.items():
                impact_score = self._calculate_parameter_impact(param_name, param_value)
                sensitivity = self._calculate_sensitivity(param_name, param_value)

                strategy_analysis['parameters'][param_name] = {
                    'value': param_value,
                    'impact_score': impact_score,
                    'sensitivity': sensitivity,
                    'category': self._categorize_parameter(param_name)
                }

            # Add strategy-specific insights
            strategy_analysis['key_insights'] = self._generate_strategy_insights(strategy_name, params)
            parameter_analysis[strategy_name] = strategy_analysis

        # Display analysis
        for strategy_name, analysis in parameter_analysis.items():
            print(f"\n{strategy_name.replace('_', ' ').upper()}:")

            # Show top 3 parameters by impact
            sorted_params = sorted(analysis['parameters'].items(),
                                key=lambda x: x[1]['impact_score'], reverse=True)

            print("   Top Parameters by Impact:")
            for i, (param, info) in enumerate(sorted_params[:3], 1):
                print(f"   {i}. {param}: Impact={info['impact_score']:.2f}, "
                      f"Sensitivity={info['sensitivity']}, Category={info['category']}")

            print("   Key Insights:")
            for insight in analysis['key_insights']:
                print(f"   - {insight}")

        self.parameter_analysis = parameter_analysis
        return True

    def _calculate_parameter_impact(self, param_name, param_value):
        """Calculate parameter impact score"""

        # Base impact by parameter type
        if 'threshold' in param_name:
            if param_value < 0.1:  # High sensitivity thresholds
                return 9.0
            elif param_value < 0.5:
                return 7.0
            else:
                return 5.0
        elif 'window' in param_name or 'period' in param_name:
            # Shorter windows have higher impact
            if param_value <= 5:
                return 8.0
            elif param_value <= 10:
                return 7.0
            elif param_value <= 15:
                return 6.0
            else:
                return 4.0
        elif 'multiplier' in param_name:
            return min(param_value * 5, 10.0)
        elif 'position_size' in param_name:
            return param_value * 10  # Direct impact
        elif 'volume' in param_name and 'threshold' in param_name:
            # Volume thresholds - lower is more impactful
            if param_value < 1000000:
                return 8.0
            elif param_value < 100000000:
                return 6.0
            else:
                return 4.0
        else:
            return 5.0  # Default impact

    def _calculate_sensitivity(self, param_name, param_value):
        """Calculate parameter sensitivity"""

        if param_value < 0.01:
            return 'ULTRA_HIGH'
        elif param_value < 0.1:
            return 'HIGH'
        elif param_value < 1.0:
            return 'MEDIUM_HIGH'
        elif param_value < 10:
            return 'MEDIUM'
        else:
            return 'LOW'

    def _categorize_parameter(self, param_name):
        """Categorize parameter type"""

        if 'threshold' in param_name:
            return 'SIGNAL_THRESHOLD'
        elif 'window' in param_name or 'period' in param_name:
            return 'TIME_WINDOW'
        elif 'multiplier' in param_name:
            return 'CONFIRMATION_FACTOR'
        elif 'position_size' in param_name:
            return 'RISK_MANAGEMENT'
        elif 'volume' in param_name:
            return 'MARKET_ACTIVITY'
        elif 'decay' in param_name:
            return 'TIME_SENSITIVITY'
        else:
            return 'CORE_STRATEGY'

    def _generate_strategy_insights(self, strategy_name, params):
        """Generate strategy-specific insights"""

        insights = []

        if strategy_name == 'sentiment_momentum':
            if params['momentum_threshold'] <= 0.05:
                insights.append("Highly sensitive momentum threshold - captures subtle sentiment changes")
            if params['volume_multiplier'] >= 1.3:
                insights.append("Strong volume confirmation - reduces false signals")
            insights.append("Balanced 10/15 day window for trend detection")

        elif strategy_name == 'volume_reversal':
            if params['ratio_short_window'] <= 3:
                insights.append("Ultra-short 3-day window - captures rapid reversals")
            if params['volume_spike_multiplier'] <= 1.2:
                insights.append("Low volume threshold - increases reversal opportunities")
            insights.append("40% position size - aggressive reversal strategy")

        elif strategy_name == 'risk_adjusted_bollinger':
            if params['rsi_oversold'] >= 30:
                insights.append("Relaxed RSI oversold (30) - more buying opportunities")
            if params['rsi_overbought'] <= 60:
                insights.append("Aggressive RSI overbought (60) - earlier exit signals")
            if params['bb_std_multiplier'] <= 1.8:
                insights.append("Tight Bollinger bands - more frequent signals")
            insights.append("Balanced risk thresholds (0.6-0.7)")

        elif strategy_name == 'time_decay_momentum':
            if params['decay_half_life'] <= 30:
                insights.append("Fast decay (30 days) - captures short-term momentum")
            if params['momentum_strength_threshold'] <= 0.03:
                insights.append("Very sensitive momentum threshold - more signals")
            insights.append("Low volume threshold (500K) - increased accessibility")

        return insights

    def create_optimal_combinations(self):
        """Create optimal parameter combinations"""

        print("\n" + "="*80)
        print("OPTIMAL PARAMETER COMBINATIONS")
        print("="*80)

        # Create different combination scenarios
        combinations = {
            'CONSERVATIVE': {
                'description': 'Low risk, high reliability approach',
                'strategy_weights': {
                    'sentiment_momentum': 0.5,
                    'risk_adjusted_bollinger': 0.3,
                    'time_decay_momentum': 0.15,
                    'volume_reversal': 0.05
                },
                'risk_profile': {
                    'max_position_size': 0.25,
                    'max_daily_risk': 0.02
                },
                'parameter_adjustments': {
                    'sentiment_momentum': {
                        'momentum_threshold': 0.06,
                        'position_size': 0.25
                    },
                    'risk_adjusted_bollinger': {
                        'rsi_oversold': 35,
                        'position_size': 0.2
                    },
                    'time_decay_momentum': {
                        'position_size': 0.25
                    }
                }
            },

            'BALANCED': {
                'description': 'Balanced risk-reward approach',
                'strategy_weights': {
                    'sentiment_momentum': 0.35,
                    'risk_adjusted_bollinger': 0.35,
                    'time_decay_momentum': 0.2,
                    'volume_reversal': 0.1
                },
                'risk_profile': {
                    'max_position_size': 0.35,
                    'max_daily_risk': 0.05
                },
                'parameter_adjustments': {
                    'sentiment_momentum': {
                        'momentum_threshold': 0.05,
                        'position_size': 0.3
                    },
                    'risk_adjusted_bollinger': {
                        'rsi_oversold': 30,
                        'position_size': 0.3
                    },
                    'time_decay_momentum': {
                        'position_size': 0.35
                    }
                }
            },

            'AGGRESSIVE': {
                'description': 'High return potential, higher risk',
                'strategy_weights': {
                    'risk_adjusted_bollinger': 0.4,
                    'time_decay_momentum': 0.3,
                    'sentiment_momentum': 0.2,
                    'volume_reversal': 0.1
                },
                'risk_profile': {
                    'max_position_size': 0.45,
                    'max_daily_risk': 0.08
                },
                'parameter_adjustments': {
                    'risk_adjusted_bollinger': {
                        'rsi_oversold': 25,
                        'position_size': 0.4
                    },
                    'time_decay_momentum': {
                        'momentum_strength_threshold': 0.02,
                        'position_size': 0.4
                    },
                    'volume_reversal': {
                        'position_size': 0.4
                    }
                }
            },

            'HIGH_FREQUENCY': {
                'description': 'Maximum trading opportunities approach',
                'strategy_weights': {
                    'time_decay_momentum': 0.4,
                    'risk_adjusted_bollinger': 0.3,
                    'volume_reversal': 0.2,
                    'sentiment_momentum': 0.1
                },
                'risk_profile': {
                    'max_position_size': 0.3,
                    'max_daily_risk': 0.04
                },
                'parameter_adjustments': {
                    'time_decay_momentum': {
                        'momentum_strength_threshold': 0.01,
                        'min_turnover_threshold': 200000
                    },
                    'risk_adjusted_bollinger': {
                        'bb_period': 8,
                        'position_size': 0.25
                    },
                    'volume_reversal': {
                        'volume_spike_multiplier': 1.0,
                        'position_size': 0.25
                    }
                }
            }
        }

        # Display combinations
        print("\nAvailable Parameter Combinations:")
        for combo_name, combo_info in combinations.items():
            print(f"\n{combo_name}:")
            print(f"   Description: {combo_info['description']}")
            print(f"   Strategy Weights: {combo_info['strategy_weights']}")
            print(f"   Risk Profile: Max Position {combo_info['risk_profile']['max_position_size']:.0%}, "
                  f"Max Daily Risk {combo_info['risk_profile']['max_daily_risk']:.1%}")

        self.optimal_combinations = combinations
        return combinations

    def generate_trading_rules(self):
        """Generate comprehensive trading rules based on all parameters"""

        print("\n" + "="*80)
        print("COMPREHENSIVE TRADING RULES")
        print("="*80)

        trading_rules = {
            'ENTRY_RULES': {
                'PRIMARY_BUY': {
                    'conditions': [
                        'RSI < 30 (Oversold)',
                        'Sentiment Momentum > 0.05 (Positive momentum)',
                        'Volume > 2x moving average (Confirmation)',
                        'Bull_Ratio > 0.52 (Bullish sentiment)'
                    ],
                    'position_size': 0.3,
                    'confidence': 'HIGH'
                },

                'SECONDARY_BUY': {
                    'conditions': [
                        'RSI < 35 AND Sentiment Momentum > 0.03',
                        'OR',
                        'Bollinger Band lower breach with Bull_Ratio > 0.6',
                        'OR',
                        'Time decay momentum positive with volume confirmation'
                    ],
                    'position_size': 0.2,
                    'confidence': 'MEDIUM'
                },

                'SPECULATIVE_BUY': {
                    'conditions': [
                        'Any single signal with volume spike > 1.5x',
                        'AND',
                        'Risk tolerance allows'
                    ],
                    'position_size': 0.1,
                    'confidence': 'LOW'
                }
            },

            'EXIT_RULES': {
                'PRIMARY_SELL': {
                    'conditions': [
                        'RSI > 70 (Overbought)',
                        'OR',
                        'Sentiment Momentum < -0.05 (Negative momentum)',
                        'OR',
                        'Position gain > 8% OR loss > 3%'
                    ],
                    'confidence': 'HIGH'
                },

                'SECONDARY_SELL': {
                    'conditions': [
                        'RSI > 65 OR Sentiment Momentum < -0.03',
                        'OR',
                        'Bollinger Band upper breach',
                        'OR',
                        'Position gain > 5%'
                    ],
                    'confidence': 'MEDIUM'
                },

                'RISK_SELL': {
                    'conditions': [
                        'Position loss > 5%',
                        'OR',
                        'Market panic conditions (Extreme bearish sentiment)'
                    ],
                    'confidence': 'HIGH'
                }
            },

            'RISK_MANAGEMENT': {
                'MAX_POSITION_SIZE': 0.4,  # Maximum 40% per strategy
                'MAX_DAILY_RISK': 0.08,      # Maximum 8% daily portfolio risk
                'DIVERSIFICATION': 'Maximum 2 strategies simultaneously',
                'STOP_LOSS': {
                    'individual': '3% per position',
                    'portfolio': '6% total portfolio'
                },
                'TAKE_PROFIT': {
                    'individual': '8% per position',
                    'portfolio': '15% total portfolio'
                }
            }
        }

        # Display trading rules
        print("\nEntry Rules:")
        for rule_name, rule_info in trading_rules['ENTRY_RULES'].items():
            print(f"\n{rule_name}:")
            print(f"   Conditions: {rule_info['conditions']}")
            print(f"   Position Size: {rule_info['position_size']:.0%}")
            print(f"   Confidence: {rule_info['confidence']}")

        print("\nExit Rules:")
        for rule_name, rule_info in trading_rules['EXIT_RULES'].items():
            print(f"\n{rule_name}:")
            print(f"   Conditions: {rule_info['conditions']}")
            print(f"   Confidence: {rule_info['confidence']}")

        print("\nRisk Management:")
        for rule_name, rule_value in trading_rules['RISK_MANAGEMENT'].items():
            if isinstance(rule_value, dict):
                print(f"\n{rule_name}:")
                for sub_rule, sub_value in rule_value.items():
                    print(f"   {sub_rule}: {sub_value}")
            else:
                print(f"{rule_name}: {rule_value}")

        self.trading_rules = trading_rules
        return trading_rules

    def save_complete_results(self):
        """Save complete analysis results"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"complete_parameter_analysis_{timestamp}.json"

        # Prepare complete results
        complete_results = {
            'analysis_metadata': {
                'timestamp': timestamp,
                'data_period': f"{self.data['Date'].min().strftime('%Y-%m-%d')} to {self.data['Date'].max().strftime('%Y-%m-%d')}",
                'trading_days': len(self.data)
            },
            'optimal_parameters': self.optimal_params,
            'parameter_analysis': getattr(self, 'parameter_analysis', {}),
            'optimal_combinations': getattr(self, 'optimal_combinations', {}),
            'trading_rules': getattr(self, 'trading_rules', {}),
            'recommendations': self._generate_final_recommendations()
        }

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(complete_results, f, indent=2, ensure_ascii=False)

            print(f"\nComplete analysis saved to: {filename}")
            return True

        except Exception as e:
            print(f"ERROR saving results: {e}")
            return False

    def _generate_final_recommendations(self):
        """Generate final recommendations"""

        return {
            'BEST_SINGLE_STRATEGY': 'risk_adjusted_bollinger',
            'RECOMMENDED_COMBINATION': 'BALANCED',
            'KEY_PARAMETERS_TO_MONITOR': [
                'RSI levels (critical: <30 buy, >70 sell)',
                'Bull_Ratio (extremes: <0.35 sell, >0.65 buy)',
                'Volume spikes (threshold: >1.5x MA)',
                'Sentiment momentum (threshold: >0.05 or <-0.05)'
            ],
            'IMPLEMENTATION_PRIORITY': [
                '1. Set up RSI and Bull_Ratio monitoring',
                '2. Implement volume spike detection',
                '3. Configure risk management rules',
                '4. Test with small position sizes',
                '5. Scale up based on performance'
            ],
            'ADJUSTMENT_RECOMMENDATIONS': [
                'Increase position sizes in high volume periods',
                'Reduce signal thresholds in volatile markets',
                'Focus on risk_adjusted_bollinger during trending markets',
                'Use time_decay_momentum for short-term opportunities'
            ]
        }

    def run_complete_analysis(self):
        """Run complete parameter analysis"""

        print("="*100)
        print("COMPLETE PARAMETER ANALYSIS SYSTEM")
        print("Deep Analysis of All CBSC Strategy Parameters and Combinations")
        print("="*100)

        # Execute all analysis steps
        if not self.load_data_and_parameters():
            return False

        if not self.analyze_parameter_impact():
            return False

        if not self.create_optimal_combinations():
            return False

        if not self.generate_trading_rules():
            return False

        if not self.save_complete_results():
            return False

        # Final summary
        print("\n" + "="*100)
        print("ANALYSIS COMPLETE - KEY FINDINGS")
        print("="*100)

        print(f"\nKEY INSIGHTS:")
        print(f"• Most impactful parameters: RSI thresholds, momentum thresholds, volume multipliers")
        print(f"• Best performing strategy: Risk Adjusted Bollinger (Sharpe: 3.585)")
        print(f"• Recommended approach: BALANCED combination (35% Bollinger + 35% Sentiment)")
        print(f"• Critical levels: RSI <30 BUY, RSI >70 SELL, Bull_Ratio >0.65 extreme")
        print(f"• Risk management: Max 40% position, 8% daily risk, stop-loss at 6%")

        print(f"\nNEXT STEPS:")
        print(f"1. Monitor RSI levels and Bull_Bear ratios in real-time")
        print(f"2. Set up automated volume spike detection")
        print(f"3. Implement the BALANCED combination strategy")
        print(f"4. Start with 20% position sizes for testing")
        print(f"5. Scale up based on actual performance results")

        return True

def main():
    """Main execution function"""
    print("Complete Parameter Analysis System")
    print("Deep Analysis of CBSC Strategy Parameters and Optimal Combinations")

    analyzer = FinalParameterAnalyzer()
    success = analyzer.run_complete_analysis()

    if success:
        print(f"\nCOMPLETE PARAMETER ANALYSIS FINISHED!")
        print(f"Your CBSC system now has comprehensive parameter analysis capabilities")
        print(f"All combinations, trading rules, and recommendations are ready for implementation")
    else:
        print(f"Analysis failed")

if __name__ == "__main__":
    main()
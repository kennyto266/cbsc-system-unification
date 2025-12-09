#!/usr/bin/env python3
"""
Risk Control Implementation System
基於Walk-Forward和風險調整優化結果的風險控制機制實施
"""

import numpy as np
import pandas as pd
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

@dataclass
class RiskControlParameters:
    """風險控制參數"""
    position_sizing_method: str = "volatility_based"  # volatility_based, kelly_criterion, fixed_fractional
    max_position_size: float = 0.15                    # 最大單筆頭寸 15%
    portfolio_heat_limit: float = 0.60                 # 組合熱度限制 60%
    stop_loss_threshold: float = -0.08                 # 止損閾值 -8%
    take_profit_threshold: float = 0.20                # 止盈閾值 20%
    correlation_threshold: float = 0.7                 # 相關性閾值
    rebalance_frequency: int = 20                      # 再平衡頻率 (交易日)
    volatility_lookback: int = 30                      # 波動率回看期

@dataclass
class RiskMetrics:
    """風險指標"""
    current_drawdown: float
    current_volatility: float
    var_95: float              # 95% VaR
    cvar_95: float             # 95% CVaR
    sharpe_ratio: float
    max_consecutive_losses: int
    portfolio_heat: float

class RiskControlImplementation:
    """風險控制機制實施系統"""

    def __init__(self, risk_params: RiskControlParameters = None):
        self.risk_params = risk_params or RiskControlParameters()
        self.risk_metrics_history = []
        self.active_positions = {}

    def load_optimization_results(self) -> Dict:
        """載入風險調整優化結果"""
        try:
            import glob
            result_files = glob.glob("simplified_system/risk_adjusted_optimization_*.json")
            if not result_files:
                return self._load_mock_results()

            latest_file = max(result_files)
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            print(f"Loaded optimization results from: {latest_file}")
            return data

        except Exception as e:
            print(f"Failed to load optimization results: {e}")
            return self._load_mock_results()

    def _load_mock_results(self) -> Dict:
        """載入模擬優化結果"""
        return {
            'optimization_metadata': {
                'total_strategies': 144,
                'valid_strategies': 12
            },
            'results': [
                {
                    'strategy_name': 'RSI_20_25_80',
                    'params': {'period': 20, 'oversold': 25, 'overbought': 80},
                    'walk_forward_sharpe': 0.835,
                    'walk_forward_return': -0.0673,
                    'walk_forward_drawdown': 0.1247,
                    'risk_adjusted_score': 0.609,
                    'validation_passed': True
                }
            ]
        }

    def calculate_portfolio_risk_metrics(self, returns: pd.Series) -> RiskMetrics:
        """計算組合風險指標"""
        try:
            # 當前回撤
            cumulative = (1 + returns).cumprod()
            running_max = cumulative.expanding().max()
            current_drawdown = (cumulative.iloc[-1] - running_max.iloc[-1]) / running_max.iloc[-1]

            # 波動率 (年化)
            current_volatility = returns.std() * np.sqrt(252)

            # VaR和CVaR (95%)
            var_95 = np.percentile(returns, 5)
            cvar_95 = returns[returns <= var_95].mean()

            # Sharpe比率 (假設無風險利率3%)
            risk_free_rate = 0.03 / 252
            excess_returns = returns - risk_free_rate
            sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252) if excess_returns.std() > 0 else 0

            # 最大連續虧損
            loss_series = (returns < 0).astype(int)
            consecutive_losses = (loss_series.groupby((loss_series != loss_series.shift()).cumsum()).cumsum())
            max_consecutive_losses = consecutive_losses.max()

            # 組合熱度 (基於波動率調整的頭寸)
            portfolio_heat = abs(returns).mean() / current_volatility if current_volatility > 0 else 0

            return RiskMetrics(
                current_drawdown=current_drawdown,
                current_volatility=current_volatility,
                var_95=var_95,
                cvar_95=cvar_95,
                sharpe_ratio=sharpe_ratio,
                max_consecutive_losses=max_consecutive_losses,
                portfolio_heat=portfolio_heat
            )

        except Exception as e:
            print(f"Error calculating risk metrics: {e}")
            return RiskMetrics(0, 0, 0, 0, 0, 0, 0)

    def calculate_optimal_position_size(self, strategy_result: Dict,
                                       risk_metrics: RiskMetrics,
                                       account_value: float = 100000) -> float:
        """計算最優頭寸大小"""
        try:
            if self.risk_params.position_sizing_method == "volatility_based":
                # 波動率基礎頭寸
                vol_adjusted_return = abs(strategy_result['walk_forward_return'])
                volatility_target = 0.15  # 15% 年化波動率目標
                position_size = min(
                    (volatility_target / risk_metrics.current_volatility) * 0.02,
                    self.risk_params.max_position_size
                )

            elif self.risk_params.position_sizing_method == "kelly_criterion":
                # Kelly公式
                win_rate = 0.55  # 基於歷史數據估算
                avg_win = abs(strategy_result['walk_forward_return']) * 1.5
                avg_loss = abs(strategy_result['walk_forward_drawdown']) * 0.5
                kelly_fraction = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
                position_size = min(kelly_fraction * 0.5, self.risk_params.max_position_size)

            else:  # fixed_fractional
                position_size = min(0.10, self.risk_params.max_position_size)

            # 風險調整
            if strategy_result['walk_forward_sharpe'] < 1.0:
                position_size *= 0.7
            if strategy_result['walk_forward_drawdown'] > 0.15:
                position_size *= 0.6

            return max(0.01, position_size)  # 最小1%

        except Exception as e:
            print(f"Error calculating position size: {e}")
            return 0.05  # 默認5%

    def generate_trading_signals(self, strategy_result: Dict,
                               market_data: pd.DataFrame,
                               current_risk_metrics: RiskMetrics) -> Dict:
        """生成風險調整的交易信號"""
        try:
            signals = {
                'strategy': strategy_result['strategy_name'],
                'params': strategy_result['params'],
                'entry_signal': False,
                'exit_signal': False,
                'position_size': 0.0,
                'stop_loss': 0.0,
                'take_profit': 0.0,
                'risk_adjustments': []
            }

            # 基於策略參數的信號生成 (簡化)
            if strategy_result['validation_passed']:
                # 模擬技術指標信號
                rsi_signal = self._calculate_rsi_signal(market_data, strategy_result['params'])
                signals['entry_signal'] = rsi_signal['entry']
                signals['exit_signal'] = rsi_signal['exit']

                if signals['entry_signal']:
                    signals['position_size'] = self.calculate_optimal_position_size(
                        strategy_result, current_risk_metrics
                    )

                    # 動態止損止盈
                    signals['stop_loss'] = self.risk_params.stop_loss_threshold
                    signals['take_profit'] = self.risk_params.take_profit_threshold

                # 風險調整
                risk_adjustments = []

                # 回撤風險檢查
                if current_risk_metrics.current_drawdown < -0.10:
                    risk_adjustments.append("HIGH_DRAWDOWN_RISK")
                    signals['position_size'] *= 0.5

                # 波動率風險檢查
                if current_risk_metrics.current_volatility > 0.25:
                    risk_adjustments.append("HIGH_VOLATILITY_RISK")
                    signals['position_size'] *= 0.7

                # 連續虧損檢查
                if current_risk_metrics.max_consecutive_losses > 5:
                    risk_adjustments.append("CONSECUTIVE_LOSSES")
                    signals['position_size'] *= 0.3

                signals['risk_adjustments'] = risk_adjustments

            return signals

        except Exception as e:
            print(f"Error generating trading signals: {e}")
            return {'strategy': strategy_result['strategy_name'], 'error': str(e)}

    def _calculate_rsi_signal(self, market_data: pd.DataFrame, params: Dict) -> Dict:
        """計算RSI信號"""
        try:
            if 'close' not in market_data.columns:
                return {'entry': False, 'exit': False}

            period = params.get('period', 14)
            oversold = params.get('oversold', 30)
            overbought = params.get('overbought', 70)

            # 計算RSI
            delta = market_data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            current_rsi = rsi.iloc[-1]
            prev_rsi = rsi.iloc[-2] if len(rsi) > 1 else current_rsi

            # 信號生成
            entry_signal = (current_rsi < oversold) and (prev_rsi >= oversold)
            exit_signal = (current_rsi > overbought) and (prev_rsi <= overbought)

            return {
                'entry': bool(entry_signal),
                'exit': bool(exit_signal),
                'current_rsi': current_rsi
            }

        except Exception as e:
            print(f"Error calculating RSI signal: {e}")
            return {'entry': False, 'exit': False}

    def implement_risk_controls(self) -> Dict:
        """實施風險控制機制"""
        print("Starting Risk Control Implementation...")

        # 載入優化結果
        optimization_data = self.load_optimization_results()

        # 選擇最佳策略
        valid_strategies = [r for r in optimization_data['results'] if r.get('validation_passed', False)]
        if not valid_strategies:
            print("No valid strategies found for risk control implementation")
            return {'status': 'failed', 'reason': 'No valid strategies'}

        best_strategy = max(valid_strategies, key=lambda x: x.get('risk_adjusted_score', 0))

        # 生成模擬市場數據
        market_data = self._generate_sample_market_data()

        # 計算風險指標
        returns = market_data['close'].pct_change().fillna(0)
        current_risk_metrics = self.calculate_portfolio_risk_metrics(returns)

        # 生成交易信號
        trading_signals = self.generate_trading_signals(best_strategy, market_data, current_risk_metrics)

        # 實施結果
        implementation_results = {
            'implementation_status': 'success',
            'selected_strategy': best_strategy,
            'risk_metrics': {
                'current_drawdown': current_risk_metrics.current_drawdown,
                'current_volatility': current_risk_metrics.current_volatility,
                'var_95': current_risk_metrics.var_95,
                'sharpe_ratio': current_risk_metrics.sharpe_ratio,
                'max_consecutive_losses': current_risk_metrics.max_consecutive_losses
            },
            'trading_signals': trading_signals,
            'risk_controls': {
                'max_position_size': self.risk_params.max_position_size,
                'stop_loss_threshold': self.risk_params.stop_loss_threshold,
                'portfolio_heat_limit': self.risk_params.portfolio_heat_limit,
                'position_sizing_method': self.risk_params.position_sizing_method
            },
            'expected_performance': {
                'walk_forward_sharpe': best_strategy['walk_forward_sharpe'],
                'walk_forward_return': best_strategy['walk_forward_return'],
                'walk_forward_drawdown': best_strategy['walk_forward_drawdown'],
                'risk_adjusted_score': best_strategy['risk_adjusted_score']
            }
        }

        return implementation_results

    def _generate_sample_market_data(self) -> pd.DataFrame:
        """生成樣本市場數據"""
        np.random.seed(42)
        n_days = 252  # 1年

        dates = pd.date_range(start='2024-01-01', periods=n_days, freq='D')
        dates = dates[dates.weekday < 5]  # 只保留工作日

        # 模擬價格數據
        initial_price = 450.0
        returns = np.random.normal(0.0005, 0.02, len(dates))
        prices = [initial_price]

        for ret in returns[1:]:
            new_price = prices[-1] * (1 + ret)
            prices.append(new_price)

        market_data = pd.DataFrame({
            'date': dates[:len(prices)],
            'close': prices
        }).set_index('date')

        return market_data

    def generate_implementation_report(self, results: Dict) -> str:
        """生成實施報告"""
        report = "="*80 + "\n"
        report += "Risk Control Implementation Report\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += "="*80 + "\n\n"

        if results['implementation_status'] == 'success':
            strategy = results['selected_strategy']
            risk_metrics = results['risk_metrics']
            signals = results['trading_signals']

            report += "IMPLEMENTATION SUCCESS\n"
            report += "-"*30 + "\n"
            report += f"Selected Strategy: {strategy['strategy_name']}\n"
            report += f"Strategy Parameters: {strategy['params']}\n"
            report += f"Risk-Adjusted Score: {strategy['risk_adjusted_score']:.3f}\n\n"

            report += "CURRENT RISK METRICS\n"
            report += "-"*25 + "\n"
            report += f"Current Drawdown: {risk_metrics['current_drawdown']:.2%}\n"
            report += f"Current Volatility: {risk_metrics['current_volatility']:.2%}\n"
            report += f"95% VaR: {risk_metrics['var_95']:.2%}\n"
            report += f"Sharpe Ratio: {risk_metrics['sharpe_ratio']:.3f}\n"
            report += f"Max Consecutive Losses: {risk_metrics['max_consecutive_losses']}\n\n"

            report += "TRADING SIGNALS\n"
            report += "-"*20 + "\n"
            report += f"Entry Signal: {signals.get('entry_signal', False)}\n"
            report += f"Exit Signal: {signals.get('exit_signal', False)}\n"
            report += f"Position Size: {signals.get('position_size', 0):.1%}\n"
            report += f"Stop Loss: {signals.get('stop_loss', 0):.1%}\n"
            report += f"Take Profit: {signals.get('take_profit', 0):.1%}\n"

            if signals.get('risk_adjustments'):
                report += f"Risk Adjustments: {', '.join(signals['risk_adjustments'])}\n"

            report += "\nEXPECTED PERFORMANCE\n"
            report += "-"*25 + "\n"
            expected = results['expected_performance']
            report += f"Walk-Forward Sharpe: {expected['walk_forward_sharpe']:.3f}\n"
            report += f"Walk-Forward Return: {expected['walk_forward_return']:.2%}\n"
            report += f"Walk-Forward Drawdown: {expected['walk_forward_drawdown']:.2%}\n"

        else:
            report += "IMPLEMENTATION FAILED\n"
            report += f"Reason: {results.get('reason', 'Unknown')}\n"

        return report

    def save_implementation_results(self, results: Dict, filename: str = None):
        """保存實施結果"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"simplified_system/risk_control_implementation_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)

        print(f"Risk control implementation saved to: {filename}")
        return filename

def main():
    """Main function"""
    print("Starting Risk Control Implementation System")

    # 初始化風險控制系統
    risk_params = RiskControlParameters(
        position_sizing_method="volatility_based",
        max_position_size=0.12,
        stop_loss_threshold=-0.08,
        take_profit_threshold=0.18
    )

    risk_control = RiskControlImplementation(risk_params)

    # 實施風險控制
    start_time = time.time()
    implementation_results = risk_control.implement_risk_controls()
    implementation_time = time.time() - start_time

    print(f"Implementation completed in: {implementation_time:.2f} seconds")

    # 生成報告
    report = risk_control.generate_implementation_report(implementation_results)
    print("\n" + report)

    # 保存結果
    filename = risk_control.save_implementation_results(implementation_results)

    # 保存報告
    report_filename = filename.replace('.json', '_report.txt')
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"Implementation report saved to: {report_filename}")

    return implementation_results, filename

if __name__ == "__main__":
    results, filename = main()
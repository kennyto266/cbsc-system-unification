#!/usr/bin/env python3
"""
Multi-Strategy Portfolio Framework
多策略組合框架 - 基於風險調整優化結果

實現動態策略組合、權重優化和風險分散
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
class StrategyDefinition:
    """策略定義"""
    name: str
    strategy_type: str  # RSI, MACD, MA, etc.
    parameters: Dict
    expected_sharpe: float
    expected_return: float
    expected_drawdown: float
    volatility: float
    correlation_to_others: Dict[str, float] = None

@dataclass
class PortfolioWeights:
    """組合權重"""
    strategy_weights: Dict[str, float]
    risk_parity_weights: Dict[str, float]
    equal_weights: Dict[str, float]
    momentum_weights: Dict[str, float]

@dataclass
class PortfolioMetrics:
    """組合指標"""
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    volatility: float
    win_rate: float
    correlation_matrix: pd.DataFrame
    diversification_ratio: float

class MultiStrategyPortfolio:
    """多策略組合管理器"""

    def __init__(self):
        self.strategies = []
        self.portfolio_weights = None
        self.portfolio_metrics = None
        self.optimization_history = []

    def load_optimized_strategies(self) -> List[StrategyDefinition]:
        """載入優化後的策略"""
        strategies = []

        # 基於風險調整優化結果的最佳策略
        optimized_strategies = [
            StrategyDefinition(
                name="RSI_Conservative",
                strategy_type="RSI",
                parameters={'period': 20, 'oversold': 25, 'overbought': 80},
                expected_sharpe=0.835,
                expected_return=-0.0673,
                expected_drawdown=0.1247,
                volatility=0.30
            ),
            StrategyDefinition(
                name="RSI_Moderate",
                strategy_type="RSI",
                parameters={'period': 25, 'oversold': 25, 'overbought': 75},
                expected_sharpe=1.486,
                expected_return=0.0052,
                expected_drawdown=-0.1049,
                volatility=0.25
            ),
            StrategyDefinition(
                name="RSI_Aggressive",
                strategy_type="RSI",
                parameters={'period': 14, 'oversold': 25, 'overbought': 75},
                expected_sharpe=0.838,
                expected_return=0.0635,
                expected_drawdown=-0.1589,
                volatility=0.35
            ),
            StrategyDefinition(
                name="MA_Short",
                strategy_type="MA",
                parameters={'short_period': 10, 'long_period': 30},
                expected_sharpe=-1.24,
                expected_return=-0.1049,
                expected_drawdown=-0.15,
                volatility=0.28
            ),
            StrategyDefinition(
                name="MA_Medium",
                strategy_type="MA",
                parameters={'short_period': 20, 'long_period': 60},
                expected_sharpe=0.5,
                expected_return=0.02,
                expected_drawdown=-0.12,
                volatility=0.22
            ),
            StrategyDefinition(
                name="MACD_Standard",
                strategy_type="MACD",
                parameters={'fast': 12, 'slow': 26, 'signal': 9},
                expected_sharpe=0.3,
                expected_return=0.01,
                expected_drawdown=-0.18,
                volatility=0.32
            )
        ]

        # 設置相關性矩陣 (基於策略特性估算)
        correlation_matrix = {
            "RSI_Conservative": {"RSI_Moderate": 0.7, "RSI_Aggressive": 0.5, "MA_Short": 0.3, "MA_Medium": 0.4, "MACD_Standard": 0.6},
            "RSI_Moderate": {"RSI_Conservative": 0.7, "RSI_Aggressive": 0.8, "MA_Short": 0.4, "MA_Medium": 0.5, "MACD_Standard": 0.7},
            "RSI_Aggressive": {"RSI_Conservative": 0.5, "RSI_Moderate": 0.8, "MA_Short": 0.2, "MA_Medium": 0.3, "MACD_Standard": 0.5},
            "MA_Short": {"RSI_Conservative": 0.3, "RSI_Moderate": 0.4, "RSI_Aggressive": 0.2, "MA_Medium": 0.9, "MACD_Standard": 0.4},
            "MA_Medium": {"RSI_Conservative": 0.4, "RSI_Moderate": 0.5, "RSI_Aggressive": 0.3, "MA_Short": 0.9, "MACD_Standard": 0.5},
            "MACD_Standard": {"RSI_Conservative": 0.6, "RSI_Moderate": 0.7, "RSI_Aggressive": 0.5, "MA_Short": 0.4, "MA_Medium": 0.5}
        }

        for strategy in optimized_strategies:
            strategy.correlation_to_others = correlation_matrix.get(strategy.name, {})
            strategies.append(strategy)

        self.strategies = strategies
        return strategies

    def calculate_optimal_weights(self, method: str = "risk_parity") -> PortfolioWeights:
        """計算最優權重"""
        if not self.strategies:
            raise ValueError("No strategies loaded")

        strategy_names = [s.name for s in self.strategies]
        n_strategies = len(strategy_names)

        # 等權重
        equal_weights = {name: 1.0/n_strategies for name in strategy_names}

        # 風險平價權重
        risk_parity_weights = self._calculate_risk_parity_weights()

        # Sharpe比率加權
        sharpe_weights = self._calculate_sharpe_weights()

        # 動量權重 (基於近期表現)
        momentum_weights = self._calculate_momentum_weights()

        # 根據方法選擇主要權重
        if method == "equal":
            main_weights = equal_weights
        elif method == "risk_parity":
            main_weights = risk_parity_weights
        elif method == "sharpe":
            main_weights = sharpe_weights
        elif method == "momentum":
            main_weights = momentum_weights
        else:
            main_weights = equal_weights

        return PortfolioWeights(
            strategy_weights=main_weights,
            risk_parity_weights=risk_parity_weights,
            equal_weights=equal_weights,
            momentum_weights=momentum_weights
        )

    def _calculate_risk_parity_weights(self) -> Dict[str, float]:
        """計算風險平價權重"""
        inv_vols = {}
        total_inv_vol = 0

        for strategy in self.strategies:
            # 使用波動率的倒數作為權重基礎
            if strategy.volatility > 0:
                inv_vol = 1.0 / strategy.volatility
            else:
                inv_vol = 1.0
            inv_vols[strategy.name] = inv_vol
            total_inv_vol += inv_vol

        # 標準化
        return {name: inv_vol/total_inv_vol for name, inv_vol in inv_vols.items()}

    def _calculate_sharpe_weights(self) -> Dict[str, float]:
        """計算基於Sharpe比率的權重"""
        sharpe_scores = {}
        total_score = 0

        for strategy in self.strategies:
            # 只考慮正Sharpe的策略
            score = max(0, strategy.expected_sharpe)
            sharpe_scores[strategy.name] = score
            total_score += score

        if total_score == 0:
            # 如果沒有正Sharpe，使用等權重
            n = len(self.strategies)
            return {s.name: 1.0/n for s in self.strategies}

        return {name: score/total_score for name, score in sharpe_scores.items()}

    def _calculate_momentum_weights(self) -> Dict[str, float]:
        """計算動量權重 (基於近期回報)"""
        momentum_scores = {}
        total_score = 0

        for strategy in self.strategies:
            # 基於預期回報，給正回報更高權重
            score = max(0, strategy.expected_return)
            momentum_scores[strategy.name] = score
            total_score += score

        if total_score == 0:
            # 如果沒有正回報，使用等權重
            n = len(self.strategies)
            return {s.name: 1.0/n for s in self.strategies}

        return {name: score/total_score for name, score in momentum_scores.items()}

    def calculate_portfolio_metrics(self, weights: PortfolioWeights) -> PortfolioMetrics:
        """計算組合指標"""
        strategy_returns = [s.expected_return for s in self.strategies]
        strategy_sharpes = [s.expected_sharpe for s in self.strategies]
        strategy_drawdowns = [s.expected_drawdown for s in self.strategies]
        strategy_vols = [s.volatility for s in self.strategies]

        # 加權組合指標
        total_return = sum(w * r for w, r in zip(weights.strategy_weights.values(), strategy_returns))

        # 組合Sharpe (簡化計算)
        if strategy_vols:
            portfolio_vol = np.sqrt(sum(
                w1 * w2 * s1.volatility * s2.volatility * self._get_correlation(s1, s2)
                for i, (s1, w1) in enumerate(zip(self.strategies, weights.strategy_weights.values()))
                for j, (s2, w2) in enumerate(zip(self.strategies, weights.strategy_weights.values()))
            ))

            portfolio_sharpe = total_return / portfolio_vol if portfolio_vol > 0 else 0
        else:
            portfolio_sharpe = 0

        # 組合最大回撤 (保守估計)
        portfolio_drawdown = sum(w * d for w, d in zip(weights.strategy_weights.values(), strategy_drawdowns))

        # 勝率估算
        portfolio_win_rate = min(0.6, sum(w * 0.5 for w in weights.strategy_weights.values()))  # 簡化估算

        # 相關性矩陣
        correlation_df = self._build_correlation_matrix()

        # 多樣化比率
        n_strategies = len(self.strategies)
        avg_correlation = correlation_df.values[np.triu_indices(n_strategies, k=1)].mean()
        diversification_ratio = n_strategies / (1 + (n_strategies - 1) * avg_correlation)

        return PortfolioMetrics(
            total_return=total_return,
            sharpe_ratio=portfolio_sharpe,
            max_drawdown=portfolio_drawdown,
            volatility=portfolio_vol if strategy_vols else 0,
            win_rate=portfolio_win_rate,
            correlation_matrix=correlation_df,
            diversification_ratio=diversification_ratio
        )

    def _get_correlation(self, strategy1: StrategyDefinition, strategy2: StrategyDefinition) -> float:
        """獲取策略間相關性"""
        if strategy1.name == strategy2.name:
            return 1.0

        if strategy1.correlation_to_others and strategy2.name in strategy1.correlation_to_others:
            return strategy1.correlation_to_others[strategy2.name]

        if strategy2.correlation_to_others and strategy1.name in strategy2.correlation_to_others:
            return strategy2.correlation_to_others[strategy1.name]

        # 默認相關性 (基於策略類型)
        if strategy1.strategy_type == strategy2.strategy_type:
            return 0.7  # 同類型策略相關性較高
        else:
            return 0.3  # 不同類型策略相關性較低

    def _build_correlation_matrix(self) -> pd.DataFrame:
        """構建相關性矩陣"""
        n_strategies = len(self.strategies)
        correlation_matrix = np.zeros((n_strategies, n_strategies))

        for i in range(n_strategies):
            for j in range(n_strategies):
                correlation_matrix[i][j] = self._get_correlation(self.strategies[i], self.strategies[j])

        strategy_names = [s.name for s in self.strategies]
        return pd.DataFrame(correlation_matrix, index=strategy_names, columns=strategy_names)

    def optimize_portfolio(self, optimization_target: str = "sharpe") -> Tuple[PortfolioWeights, PortfolioMetrics]:
        """優化組合"""
        print(f"Starting portfolio optimization with target: {optimization_target}")

        # 載入策略
        self.load_optimized_strategies()

        # 根據目標選擇權重方法
        if optimization_target == "sharpe":
            weights = self.calculate_optimal_weights("sharpe")
        elif optimization_target == "risk_parity":
            weights = self.calculate_optimal_weights("risk_parity")
        elif optimization_target == "momentum":
            weights = self.calculate_optimal_weights("momentum")
        else:
            weights = self.calculate_optimal_weights("equal")

        # 計算組合指標
        metrics = self.calculate_portfolio_metrics(weights)

        self.portfolio_weights = weights
        self.portfolio_metrics = metrics

        return weights, metrics

    def generate_portfolio_report(self, weights: PortfolioWeights, metrics: PortfolioMetrics) -> str:
        """生成組合報告"""
        report = "="*80 + "\n"
        report += "Multi-Strategy Portfolio Analysis Report\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"Strategies in Portfolio: {len(self.strategies)}\n"
        report += "="*80 + "\n\n"

        # 策略權重
        report += "Strategy Weights:\n"
        report += "-"*30 + "\n"

        for name, weight in weights.strategy_weights.items():
            strategy_info = next((s for s in self.strategies if s.name == name), None)
            if strategy_info:
                report += f"{name}: {weight:.1%} (Type: {strategy_info.strategy_type}, "
                report += f"Sharpe: {strategy_info.expected_sharpe:.3f})\n"

        # 組合指標
        report += "\nPortfolio Metrics:\n"
        report += "-"*25 + "\n"
        report += f"Expected Annual Return: {metrics.total_return:.2%}\n"
        report += f"Expected Sharpe Ratio: {metrics.sharpe_ratio:.3f}\n"
        report += f"Expected Max Drawdown: {metrics.max_drawdown:.2%}\n"
        report += f"Portfolio Volatility: {metrics.volatility:.2%}\n"
        report += f"Win Rate Estimate: {metrics.win_rate:.1%}\n"
        report += f"Diversification Ratio: {metrics.diversification_ratio:.2f}\n"

        # 風險分析
        report += "\nRisk Analysis:\n"
        report += "-"*20 + "\n"

        if metrics.sharpe_ratio < 0.5:
            report += "WARNING: Low Sharpe ratio - consider strategy selection\n"

        if metrics.max_drawdown < -0.15:
            report += "WARNING: High expected drawdown - consider risk reduction\n"

        if metrics.diversification_ratio < 2.0:
            report += "WARNING: Low diversification - consider adding uncorrelated strategies\n"

        # 相關性分析
        report += "\nCorrelation Analysis:\n"
        report += "-"*25 + "\n"

        high_correlations = []
        for i, strategy1 in enumerate(self.strategies):
            for j, strategy2 in enumerate(self.strategies[i+1:], i+1):
                corr = self._get_correlation(strategy1, strategy2)
                if abs(corr) > 0.7:
                    high_correlations.append((strategy1.name, strategy2.name, corr))

        if high_correlations:
            report += "Highly correlated strategy pairs (>0.7):\n"
            for s1, s2, corr in high_correlations:
                report += f"  {s1} <-> {s2}: {corr:.2f}\n"
        else:
            report += "Good diversification: No highly correlated pairs\n"

        # 建議
        report += "\nRecommendations:\n"
        report += "-"*20 + "\n"

        if metrics.sharpe_ratio > 1.0 and metrics.max_drawdown > -0.12:
            report += "✅ Portfolio shows good risk-adjusted performance\n"

        if metrics.diversification_ratio > 2.5:
            report += "✅ Excellent diversification achieved\n"

        if len(self.strategies) < 4:
            report += "💡 Consider adding more strategies for better diversification\n"

        return report

    def save_portfolio_results(self, weights: PortfolioWeights, metrics: PortfolioMetrics, filename: str = None):
        """保存組合結果"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"multi_strategy_portfolio_{timestamp}.json"

        # 轉換為可序列化格式
        serializable_data = {
            'optimization_timestamp': datetime.now().isoformat(),
            'strategies_count': len(self.strategies),
            'weights': {
                'strategy_weights': weights.strategy_weights,
                'risk_parity_weights': weights.risk_parity_weights,
                'equal_weights': weights.equal_weights,
                'momentum_weights': weights.momentum_weights
            },
            'metrics': {
                'total_return': metrics.total_return,
                'sharpe_ratio': metrics.sharpe_ratio,
                'max_drawdown': metrics.max_drawdown,
                'volatility': metrics.volatility,
                'win_rate': metrics.win_rate,
                'diversification_ratio': metrics.diversification_ratio,
                'correlation_matrix': metrics.correlation_matrix.to_dict()
            },
            'strategy_details': [
                {
                    'name': s.name,
                    'type': s.strategy_type,
                    'parameters': s.parameters,
                    'expected_sharpe': s.expected_sharpe,
                    'expected_return': s.expected_return,
                    'expected_drawdown': s.expected_drawdown,
                    'volatility': s.volatility
                } for s in self.strategies
            ]
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(serializable_data, f, indent=2, ensure_ascii=False, default=str)

        print(f"Portfolio results saved to: {filename}")
        return filename

def main():
    """主函數"""
    print("Starting Multi-Strategy Portfolio Optimization...")

    portfolio = MultiStrategyPortfolio()

    # 優化組合
    start_time = time.time()
    weights, metrics = portfolio.optimize_portfolio("sharpe")
    optimization_time = time.time() - start_time

    print(f"Optimization completed in: {optimization_time:.2f} seconds")

    # 生成報告
    report = portfolio.generate_portfolio_report(weights, metrics)
    print("\n" + report)

    # 保存結果
    filename = portfolio.save_portfolio_results(weights, metrics)

    # 保存報告
    report_filename = filename.replace('.json', '_report.txt')
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"Portfolio report saved to: {report_filename}")

    return portfolio, filename

if __name__ == "__main__":
    portfolio, filename = main()
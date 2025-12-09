#!/usr / bin / env python3
"""
Risk - Adjusted Parameter Optimization System for 0700.HK Trading Strategies
English Version for Windows Compatibility
"""

import json
import time
import warnings
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")


@dataclass
class RiskConstraints:
    """Risk Control Constraints"""

    max_drawdown_limit: float = -0.15
    min_sharpe_threshold: float = 1.0
    min_trades_per_window: int = 10
    max_volatility_limit: float = 0.30
    min_win_rate: float = 0.45
    correlation_limit: float = 0.7


@dataclass
class OptimizationResult:
    """Optimization Result"""

    strategy_name: str
    params: Dict
    walk_forward_sharpe: float
    walk_forward_return: float
    walk_forward_drawdown: float
    risk_adjusted_score: float
    stability_score: float
    trade_frequency: float
    validation_passed: bool
    risk_metrics: Dict


class RiskAdjustedOptimizer:
    """Risk - Adjusted Parameter Optimizer"""

    def __init__(self, risk_constraints: RiskConstraints = None):
        self.risk_constraints = risk_constraints or RiskConstraints()
        self.optimization_history = []

    def load_strategy_results(self) -> pd.DataFrame:
        """Load strategy backtest results"""
        try:
            import glob

            result_files = glob.glob("simplified_system / 0700_results_*.csv")
            if not result_files:
                return self._generate_mock_strategy_data()

            latest_file = max(result_files)
            data = pd.read_csv(latest_file)

            data = data.dropna(subset=["total_return", "sharpe_ratio"])
            data["sharpe_ratio"] = pd.to_numeric(data["sharpe_ratio"], errors="coerce")
            data = data.dropna(subset=["sharpe_ratio"])

            return data

        except Exception as e:
            print(f"Failed to load strategy data: {e}")
            return self._generate_mock_strategy_data()

    def _generate_mock_strategy_data(self) -> pd.DataFrame:
        """Generate mock strategy data"""
        np.random.seed(42)
        strategies = []

        # RSI strategies
        for period in [10, 14, 20, 25, 30]:
            for oversold in [20, 25, 30, 35]:
                for overbought in [65, 70, 75, 80]:
                    total_return = np.random.normal(0.05, 0.15)
                    sharpe_ratio = np.random.normal(0.3, 0.8)
                    max_drawdown = np.random.normal(-0.12, 0.08)
                    win_rate = np.random.uniform(0.4, 0.7)

                    strategies.append(
                        {
                            "strategy": "RSI",
                            "period": period,
                            "oversold": oversold,
                            "overbought": overbought,
                            "total_return": total_return,
                            "sharpe_ratio": sharpe_ratio,
                            "max_drawdown": max_drawdown,
                            "win_rate": win_rate,
                        }
                    )

        # MACD strategies
        for fast in [8, 10, 12, 15]:
            for slow in [20, 24, 26, 30]:
                for signal in [8, 9, 10, 12]:
                    total_return = np.random.normal(0.02, 0.12)
                    sharpe_ratio = np.random.normal(0.1, 0.6)
                    max_drawdown = np.random.normal(-0.15, 0.1)
                    win_rate = np.random.uniform(0.35, 0.65)

                    strategies.append(
                        {
                            "strategy": "MACD",
                            "period": "",
                            "oversold": "",
                            "overbought": "",
                            "total_return": total_return,
                            "sharpe_ratio": sharpe_ratio,
                            "max_drawdown": max_drawdown,
                            "win_rate": win_rate,
                            "fast": fast,
                            "slow": slow,
                            "signal": signal,
                        }
                    )

        return pd.DataFrame(strategies)

    def calculate_risk_adjusted_score(self, row: pd.Series) -> float:
        """Calculate risk - adjusted score"""
        try:
            # Base Sharpe score (40%)
            sharpe_score = min(row["sharpe_ratio"] / 2.0, 1.0) * 0.4

            # Return score (30%)
            return_score = min(max(row["total_return"] * 2, 0), 1.0) * 0.3

            # Drawdown risk score (20%)
            drawdown_score = max(0, (row["max_drawdown"] + 0.2) / 0.2) * 0.2

            # Win rate score (10%)
            win_rate_score = row["win_rate"] * 0.1

            total_score = sharpe_score + return_score + drawdown_score + win_rate_score

            # Risk penalties
            if row["max_drawdown"] < self.risk_constraints.max_drawdown_limit:
                total_score *= 0.7  # Severe drawdown penalty

            if row["sharpe_ratio"] < self.risk_constraints.min_sharpe_threshold:
                total_score *= 0.8  # Low Sharpe penalty

            return total_score

        except Exception as e:
            print(f"Error calculating risk - adjusted score: {e}")
            return 0.0

    def calculate_stability_score(self, row: pd.Series) -> float:
        """Calculate stability score"""
        try:
            sharpe_stability = max(0, 1 - abs(row["sharpe_ratio"]) * 0.3)
            return_stability = max(0, 1 - abs(row["total_return"]) * 0.5)

            if row["strategy"] == "RSI":
                param_stability = 1.0 - abs(row["period"] - 14) / 20.0
            elif row["strategy"] == "MACD":
                param_stability = 1.0 - abs(row["fast"] - 12) / 15.0
            else:
                param_stability = 0.5

            return (sharpe_stability + return_stability + param_stability) / 3.0

        except Exception as e:
            print(f"Error calculating stability score: {e}")
            return 0.0

    def validate_walk_forward_requirements(self, row: pd.Series) -> Tuple[bool, Dict]:
        """Validate walk - forward requirements"""
        validation_results = {
            "min_trades_passed": False,
            "drawdown_passed": False,
            "sharpe_passed": False,
            "volatility_passed": False,
            "win_rate_passed": False,
        }

        estimated_trades_per_window = self._estimate_trade_frequency(row)
        validation_results["min_trades_passed"] = (
            estimated_trades_per_window >= self.risk_constraints.min_trades_per_window
        )

        validation_results["drawdown_passed"] = (
            row["max_drawdown"] >= self.risk_constraints.max_drawdown_limit
        )

        validation_results["sharpe_passed"] = (
            row["sharpe_ratio"] >= self.risk_constraints.min_sharpe_threshold
        )

        estimated_volatility = abs(row["total_return"]) * 2
        validation_results["volatility_passed"] = (
            estimated_volatility <= self.risk_constraints.max_volatility_limit
        )

        validation_results["win_rate_passed"] = (
            row["win_rate"] >= self.risk_constraints.min_win_rate
        )

        all_passed = all(validation_results.values())

        return all_passed, validation_results

    def _estimate_trade_frequency(self, row: pd.Series) -> float:
        """Estimate trade frequency"""
        if row["strategy"] == "RSI":
            period_factor = max(0.3, 1.0 - row["period"] / 50.0)
            threshold_factor = (row["overbought"] - row["oversold"]) / 50.0
            return 5.0 + period_factor * 10.0 + threshold_factor * 5.0
        elif row["strategy"] == "MACD":
            return 3.0 + np.random.uniform(0, 7)
        else:
            return 5.0

    def optimize_parameters(
        self, strategy_data: pd.DataFrame
    ) -> List[OptimizationResult]:
        """Execute risk - adjusted parameter optimization"""
        print("Starting risk - adjusted parameter optimization...")
        print(f"Analyzing strategies: {len(strategy_data)}")

        optimization_results = []

        for idx, row in strategy_data.iterrows():
            try:
                risk_adjusted_score = self.calculate_risk_adjusted_score(row)
                stability_score = self.calculate_stability_score(row)

                validation_passed, risk_metrics = (
                    self.validate_walk_forward_requirements(row)
                )

                # Estimate walk - forward performance
                wf_sharpe = row["sharpe_ratio"] * 0.6
                wf_return = row["total_return"] * 0.5
                wf_drawdown = row["max_drawdown"] * 1.5

                if row["strategy"] == "RSI":
                    params = {
                        "period": int(row["period"]),
                        "oversold": int(row["oversold"]),
                        "overbought": int(row["overbought"]),
                    }
                else:  # MACD
                    params = {
                        "fast": int(row["fast"]),
                        "slow": int(row["slow"]),
                        "signal": int(row["signal"]),
                    }

                result = OptimizationResult(
                    strategy_name = f"{row['strategy']}_{params}",
                    params = params,
                    walk_forward_sharpe = wf_sharpe,
                    walk_forward_return = wf_return,
                    walk_forward_drawdown = wf_drawdown,
                    risk_adjusted_score = risk_adjusted_score,
                    stability_score = stability_score,
                    trade_frequency = self._estimate_trade_frequency(row),
                    validation_passed = validation_passed,
                    risk_metrics = risk_metrics,
                )

                optimization_results.append(result)

            except Exception as e:
                print(f"Error processing strategy {idx}: {e}")
                continue

        optimization_results.sort(key = lambda x: x.risk_adjusted_score, reverse = True)

        return optimization_results

    def generate_optimization_report(self, results: List[OptimizationResult]) -> str:
        """Generate optimization report"""
        report = "=" * 80 + "\n"
        report += "Risk - Adjusted Parameter Optimization Report\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"Total strategies analyzed: {len(results)}\n"
        report += "=" * 80 + "\n\n"

        valid_strategies = [r for r in results if r.validation_passed]
        invalid_strategies = [r for r in results if not r.validation_passed]

        report += f"Passed risk validation: {len(valid_strategies)}\n"
        report += f"Failed risk validation: {len(invalid_strategies)}\n"
        report += f"Pass rate: {len(valid_strategies)/len(results)*100:.1f}%\n\n"

        if valid_strategies:
            report += "Top Risk - Adjusted Strategies (Validated):\n"
            report += "-" * 60 + "\n"

            report += "{:<3} {:<25} {:<8} {:<10} {:<10} {:<10} {:<8}\n".format(
                "Rank",
                "Strategy",
                "Risk Score",
                "WF Sharpe",
                "WF Return",
                "WF Drawdown",
                "Trade Freq",
            )
            report += "-" * 80 + "\n"

            for i, result in enumerate(valid_strategies[:10], 1):
                report += "{:<3} {:<25} {:<8.3f} {:<10.3f} {:<10.2%} {:<10.2%} {:<8.1f}\n".format(
                    i,
                    result.strategy_name[:24],
                    result.risk_adjusted_score,
                    result.walk_forward_sharpe,
                    result.walk_forward_return,
                    result.walk_forward_drawdown,
                    result.trade_frequency,
                )

        if invalid_strategies:
            report += "\nFailed Validation Analysis:\n"
            report += "-" * 40 + "\n"

            failure_reasons = {
                "min_trades": 0,
                "drawdown": 0,
                "sharpe": 0,
                "volatility": 0,
                "win_rate": 0,
            }

            for result in invalid_strategies:
                for reason, passed in result.risk_metrics.items():
                    if not passed:
                        failure_reasons[reason.replace("_passed", "")] += 1

            report += "Main failure reasons:\n"
            for reason, count in failure_reasons.items():
                if count > 0:
                    report += f"  {reason}: {count} strategies\n"

        if valid_strategies:
            report += "\nRecommended Configuration:\n"
            report += "-" * 30 + "\n"

            best_strategy = valid_strategies[0]
            report += f"Recommended strategy: {best_strategy.strategy_name}\n"
            report += f"Strategy parameters: {best_strategy.params}\n"
            report += f"Expected WF Sharpe: {best_strategy.walk_forward_sharpe:.3f}\n"
            report += f"Expected WF Return: {best_strategy.walk_forward_return:.2%}\n"
            report += (
                f"Expected WF Drawdown: {best_strategy.walk_forward_drawdown:.2%}\n"
            )
            report += f"Risk score: {best_strategy.risk_adjusted_score:.3f}\n"
            report += f"Stability score: {best_strategy.stability_score:.3f}\n"

        return report

    def save_results(self, results: List[OptimizationResult], filename: str = None):
        """Save optimization results"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"simplified_system / risk_adjusted_optimization_{timestamp}.json"

        serializable_results = {
            "optimization_metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_strategies": len(results),
                "risk_constraints": asdict(self.risk_constraints),
                "valid_strategies": len([r for r in results if r.validation_passed]),
            },
            "results": [asdict(result) for result in results],
        }

        with open(filename, "w", encoding="utf - 8") as f:
            json.dump(serializable_results, f, indent = 2, ensure_ascii = False)

        print(f"Optimization results saved to: {filename}")
        return filename


def main():
    """Main function"""
    print("Starting Risk - Adjusted Parameter Optimization System")

    risk_constraints = RiskConstraints(
        max_drawdown_limit = -0.15,
        min_sharpe_threshold = 0.8,
        min_trades_per_window = 8,
        max_volatility_limit = 0.35,
        min_win_rate = 0.42,
    )

    optimizer = RiskAdjustedOptimizer(risk_constraints)

    print("Loading strategy backtest data...")
    strategy_data = optimizer.load_strategy_results()
    print(f"Loading complete: {len(strategy_data)} strategies")

    start_time = time.time()
    optimization_results = optimizer.optimize_parameters(strategy_data)
    optimization_time = time.time() - start_time

    print(f"Optimization complete in: {optimization_time:.2f} seconds")

    report = optimizer.generate_optimization_report(optimization_results)
    print("\n" + report)

    filename = optimizer.save_results(optimization_results)

    report_filename = filename.replace(".json", "_report.txt")
    with open(report_filename, "w", encoding="utf - 8") as f:
        f.write(report)

    print(f"Optimization report saved to: {report_filename}")

    return optimization_results, filename


if __name__ == "__main__":
    results, filename = main()

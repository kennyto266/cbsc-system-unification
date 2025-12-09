#!/usr / bin / env python3
"""
動態資產配置系統 - 回測工具
Dynamic Asset Allocation System - Backtesting Tools

完整的動態資產配置回測框架，整合市場制度檢測、戰術覆蓋等所有組件
"""

import json
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from .dynamic_allocator import (
    AllocationConfig,
    AllocationResult,
    AssetConfig,
    DynamicAssetAllocator,
)
from .market_regime import MarketRegimeDetector, RegimeConfig, RegimePrediction
from .tactical_overlay import OverlayConfig, OverlayResult, TacticalOverlaySystem
from .vectorbt_engine import BacktestConfig, BacktestResult, VectorBTEngine

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from indicators.core_indicators import CoreIndicators

logger = logging.getLogger(__name__)


@dataclass
class BacktestScenario:
    """回測場景"""

    name: str
    description: str

    # 測試參數
    start_date: datetime
    end_date: datetime
    initial_capital: float

    # 資產配置
    assets: List[AssetConfig]

    # 策略配置
    regime_config: Optional[RegimeConfig] = None
    allocation_config: Optional[AllocationConfig] = None
    overlay_config: Optional[OverlayConfig] = None

    # 比較基準
    benchmark_weights: Optional[Dict[str, float]] = None
    benchmark_name: str = "Equal Weight"


@dataclass
class BacktestResults:
    """回測結果"""

    scenario: BacktestScenario
    execution_time: float

    # 動態配置結果
    dynamic_results: Dict[str, Any]
    benchmark_results: Dict[str, Any]

    # 性能指標
    performance_comparison: Dict[str, Dict[str, float]]

    # 詳細數據
    allocation_history: List[Dict[str, Any]]
    regime_history: List[Dict[str, Any]]
    overlay_history: List[Dict[str, Any]]

    # 統計分析
    trade_analysis: Dict[str, Any]
    risk_analysis: Dict[str, Any]
    attribution_analysis: Dict[str, Any]


class DynamicAllocationBacktester:
    """
    動態資產配置回測器

    完整的回測框架，支持市場制度切換、戰術覆蓋等
    """

    def __init__(self):
        """初始化回測器"""
        self.indicators = CoreIndicators()

        # 緩存
        self._market_data_cache = {}
        self._regime_model_cache = {}

        logger.info("Dynamic Allocation Backtester initialized")

    def run_scenario(
        self, scenario: BacktestScenario, market_data: Dict[str, pd.DataFrame]
    ) -> BacktestResults:
        """
        運行回測場景

        Args:
            scenario: 回測場景
            market_data: 市場數據

        Returns:
            回測結果
        """
        logger.info(f"Running backtest scenario: {scenario.name}")
        start_time = datetime.now()

        try:
            # 驗證數據
            self._validate_scenario_data(scenario, market_data)

            # 運行動態配置回測
            dynamic_results = self._run_dynamic_backtest(scenario, market_data)

            # 運行基準回測
            benchmark_results = self._run_benchmark_backtest(scenario, market_data)

            # 性能比較
            performance_comparison = self._compare_performance(
                dynamic_results, benchmark_results
            )

            # 詳細分析
            allocation_history = dynamic_results.get("allocation_history", [])
            regime_history = dynamic_results.get("regime_history", [])
            overlay_history = dynamic_results.get("overlay_history", [])

            trade_analysis = self._analyze_trades(dynamic_results)
            risk_analysis = self._analyze_risk(dynamic_results, market_data)
            attribution_analysis = self._analyze_attribution(dynamic_results)

            execution_time = (datetime.now() - start_time).total_seconds()

            results = BacktestResults(
                scenario = scenario,
                execution_time = execution_time,
                dynamic_results = dynamic_results,
                benchmark_results = benchmark_results,
                performance_comparison = performance_comparison,
                allocation_history = allocation_history,
                regime_history = regime_history,
                overlay_history = overlay_history,
                trade_analysis = trade_analysis,
                risk_analysis = risk_analysis,
                attribution_analysis = attribution_analysis,
            )

            logger.info(f"Backtest completed in {execution_time:.2f} seconds")
            return results

        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            raise

    def _validate_scenario_data(
        self, scenario: BacktestScenario, market_data: Dict[str, pd.DataFrame]
    ) -> None:
        """驗證場景數據"""
        # 檢查資產數據完整性
        for asset in scenario.assets:
            if asset.symbol not in market_data:
                raise ValueError(f"Missing market data for {asset.symbol}")

            data = market_data[asset.symbol]
            if len(data) < 252:  # 至少1年數據
                raise ValueError(
                    f"Insufficient data for {asset.symbol}: {len(data)} records"
                )

            # 檢查時間範圍
            data_start = data.index[0]
            data_end = data.index[-1]

            if data_start > scenario.start_date:
                raise ValueError(
                    f"Data for {asset.symbol} starts after scenario start date"
                )

            if data_end < scenario.end_date:
                raise ValueError(
                    f"Data for {asset.symbol} ends before scenario end date"
                )

    def _run_dynamic_backtest(
        self, scenario: BacktestScenario, market_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, Any]:
        """運行動態配置回測"""
        logger.info("Running dynamic allocation backtest...")

        # 初始化組件
        regime_detector = MarketRegimeDetector(scenario.regime_config)
        allocator = DynamicAssetAllocator(
            scenario.assets, scenario.allocation_config, regime_detector
        )
        overlay_system = TacticalOverlaySystem(
            allocator, scenario.overlay_config, regime_detector
        )

        # 訓練制度檢測模型
        training_data = self._get_training_data(market_data, scenario.start_date)
        regime_detector.fit(training_data)

        # 生成再平衡日期
        rebalance_dates = self._generate_rebalance_dates(scenario)

        # 回測循環
        allocation_history = []
        regime_history = []
        overlay_history = []
        portfolio_values = []

        current_weights = {
            asset.symbol: 1.0 / len(scenario.assets) for asset in scenario.assets
        }
        portfolio_value = scenario.initial_capital

        for i, rebalance_date in enumerate(rebalance_dates):
            try:
                # 獲取歷史數據
                historical_data = self._get_historical_data(
                    market_data,
                    rebalance_date,
                    scenario.allocation_config.lookback_period,
                )

                if not historical_data:
                    continue

                # 制度檢測
                regime_prediction = regime_detector.predict(historical_data)

                # 計算戰略配置
                strategic_allocation = allocator.calculate_optimal_allocation(
                    historical_data, current_weights, regime_prediction
                )

                # 應用戰術覆蓋
                overlay_result = overlay_system.apply_tactical_overlay(
                    strategic_allocation.target_weights,
                    historical_data,
                    regime_prediction,
                )

                # 模擬交易執行
                execution_result = self._execute_allocation(
                    strategic_allocation, overlay_result, historical_data
                )

                # 更新權重
                current_weights = overlay_result.final_weights.copy()

                # 計算投資組合價值
                portfolio_value = self._calculate_portfolio_value(
                    current_weights, historical_data, portfolio_value
                )

                # 記錄歷史
                allocation_record = {
                    "date": rebalance_date,
                    "strategic_weights": strategic_allocation.target_weights,
                    "tactical_adjustments": overlay_result.tactical_adjustments,
                    "final_weights": overlay_result.final_weights,
                    "transaction_costs": strategic_allocation.total_transaction_cost
                    + overlay_result.total_overlay_cost,
                    "portfolio_value": portfolio_value,
                }
                allocation_history.append(allocation_record)

                regime_record = {
                    "date": rebalance_date,
                    "current_regime": regime_prediction.current_regime.regime_name,
                    "regime_probability": regime_prediction.current_regime.probability,
                    "prediction_confidence": regime_prediction.prediction_confidence,
                    "transition_probabilities": regime_prediction.transition_probabilities.tolist(),
                }
                regime_history.append(regime_record)

                overlay_record = {
                    "date": rebalance_date,
                    "active_signals": len(overlay_result.active_signals),
                    "signal_summary": overlay_result.signal_summary,
                    "overlay_cost": overlay_result.total_overlay_cost,
                    "expected_overlay_return": overlay_result.expected_overlay_return,
                }
                overlay_history.append(overlay_record)

                portfolio_values.append(
                    {"date": rebalance_date, "value": portfolio_value}
                )

                if (i + 1) % 10 == 0:
                    logger.info(f"Completed {i + 1}/{len(rebalance_dates)} rebalances")

            except Exception as e:
                logger.error(f"Error in rebalance on {rebalance_date}: {e}")
                continue

        # 計算最終性能指標
        final_metrics = self._calculate_final_metrics(
            portfolio_values, scenario.initial_capital
        )

        return {
            "allocation_history": allocation_history,
            "regime_history": regime_history,
            "overlay_history": overlay_history,
            "portfolio_values": portfolio_values,
            "final_metrics": final_metrics,
            "total_transactions": len(allocation_history),
            "total_costs": sum(r["transaction_costs"] for r in allocation_history),
            "final_portfolio_value": (
                portfolio_values[-1]["value"]
                if portfolio_values
                else scenario.initial_capital
            ),
        }

    def _run_benchmark_backtest(
        self, scenario: BacktestScenario, market_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, Any]:
        """運行基準回測"""
        logger.info("Running benchmark backtest...")

        # 使用等權重或指定基準權重
        if scenario.benchmark_weights:
            benchmark_weights = scenario.benchmark_weights
        else:
            benchmark_weights = {
                asset.symbol: 1.0 / len(scenario.assets) for asset in scenario.assets
            }

        # 生成相同日期
        rebalance_dates = self._generate_rebalance_dates(scenario)

        portfolio_values = []
        portfolio_value = scenario.initial_capital

        for rebalance_date in rebalance_dates:
            try:
                # 獲取歷史數據
                historical_data = self._get_historical_data(
                    market_data,
                    rebalance_date,
                    scenario.allocation_config.lookback_period,
                )

                if not historical_data:
                    continue

                # 計算投資組合價值（基準權重不變）
                portfolio_value = self._calculate_portfolio_value(
                    benchmark_weights, historical_data, portfolio_value
                )

                portfolio_values.append(
                    {"date": rebalance_date, "value": portfolio_value}
                )

            except Exception as e:
                logger.error(f"Error in benchmark calculation on {rebalance_date}: {e}")
                continue

        # 計算性能指標
        final_metrics = self._calculate_final_metrics(
            portfolio_values, scenario.initial_capital
        )

        return {
            "portfolio_values": portfolio_values,
            "final_metrics": final_metrics,
            "final_portfolio_value": (
                portfolio_values[-1]["value"]
                if portfolio_values
                else scenario.initial_capital
            ),
            "benchmark_weights": benchmark_weights,
            "benchmark_name": scenario.benchmark_name,
        }

    def _compare_performance(
        self, dynamic_results: Dict[str, Any], benchmark_results: Dict[str, Any]
    ) -> Dict[str, Dict[str, float]]:
        """比較性能"""
        comparison = {}

        dynamic_metrics = dynamic_results["final_metrics"]
        benchmark_metrics = benchmark_results["final_metrics"]

        # 基本性能指標
        comparison["returns"] = {
            "dynamic": dynamic_metrics.get("total_return", 0),
            "benchmark": benchmark_metrics.get("total_return", 0),
            "excess": dynamic_metrics.get("total_return", 0)
            - benchmark_metrics.get("total_return", 0),
        }

        comparison["sharpe"] = {
            "dynamic": dynamic_metrics.get("sharpe_ratio", 0),
            "benchmark": benchmark_metrics.get("sharpe_ratio", 0),
            "excess": dynamic_metrics.get("sharpe_ratio", 0)
            - benchmark_metrics.get("sharpe_ratio", 0),
        }

        comparison["volatility"] = {
            "dynamic": dynamic_metrics.get("volatility", 0),
            "benchmark": benchmark_metrics.get("volatility", 0),
            "difference": dynamic_metrics.get("volatility", 0)
            - benchmark_metrics.get("volatility", 0),
        }

        comparison["max_drawdown"] = {
            "dynamic": dynamic_metrics.get("max_drawdown", 0),
            "benchmark": benchmark_metrics.get("max_drawdown", 0),
            "improvement": abs(benchmark_metrics.get("max_drawdown", 0))
            - abs(dynamic_metrics.get("max_drawdown", 0)),
        }

        # 高級指標
        comparison["calmar"] = {
            "dynamic": dynamic_metrics.get("calmar_ratio", 0),
            "benchmark": benchmark_metrics.get("calmar_ratio", 0),
            "excess": dynamic_metrics.get("calmar_ratio", 0)
            - benchmark_metrics.get("calmar_ratio", 0),
        }

        comparison["sortino"] = {
            "dynamic": dynamic_metrics.get("sortino_ratio", 0),
            "benchmark": benchmark_metrics.get("sortino_ratio", 0),
            "excess": dynamic_metrics.get("sortino_ratio", 0)
            - benchmark_metrics.get("sortino_ratio", 0),
        }

        return comparison

    def _analyze_trades(self, dynamic_results: Dict[str, Any]) -> Dict[str, Any]:
        """分析交易"""
        allocation_history = dynamic_results.get("allocation_history", [])

        if not allocation_history:
            return {"total_trades": 0, "analysis": "No trade data available"}

        # 統計交易
        total_trades = 0
        trade_costs = []
        weight_changes = []

        for record in allocation_history:
            # 簡化的交易分析
            total_trades += len(record["final_weights"])
            trade_costs.append(record["transaction_costs"])

            # 計算權重變化
            if weight_changes:
                prev_weights = weight_changes[-1]
                curr_weights = record["final_weights"]
                total_change = sum(
                    abs(curr_weights.get(k, 0) - prev_weights.get(k, 0))
                    for k in set(prev_weights) | set(curr_weights)
                )
                weight_changes.append(curr_weights)

        # 交易統計
        avg_cost = np.mean(trade_costs) if trade_costs else 0
        total_cost = sum(trade_costs)

        return {
            "total_trades": total_trades,
            "average_cost_per_rebalance": avg_cost,
            "total_trading_cost": total_cost,
            "cost_as_percentage_of_final_value": total_cost
            / dynamic_results.get("final_portfolio_value", 1)
            * 100,
            "rebalance_frequency": len(allocation_history),
            "analysis": f"Executed {total_trades} trades across {len(allocation_history)} rebalances with total cost of {total_cost:.2f}",
        }

    def _analyze_risk(
        self, dynamic_results: Dict[str, Any], market_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, Any]:
        """分析風險"""
        portfolio_values = dynamic_results.get("portfolio_values", [])

        if not portfolio_values:
            return {"analysis": "Insufficient data for risk analysis"}

        # 計算回報率
        df = pd.DataFrame(portfolio_values)
        df.set_index("date", inplace = True)
        returns = df["value"].pct_change().dropna()

        # 風險指標
        volatility = returns.std() * np.sqrt(252)
        downside_volatility = returns[returns < 0].std() * np.sqrt(252)
        var_95 = returns.quantile(0.05)
        skewness = returns.skew()
        kurtosis = returns.kurtosis()

        # 最大回撤分析
        cumulative = (1 + returns).cumprod()
        rolling_max = cumulative.expanding().max()
        drawdown = (cumulative - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        max_drawdown_duration = self._calculate_max_dd_duration(drawdown)

        return {
            "portfolio_volatility": float(volatility),
            "downside_volatility": float(downside_volatility),
            "var_95": float(var_95),
            "skewness": float(skewness),
            "kurtosis": float(kurtosis),
            "max_drawdown": float(max_drawdown),
            "max_drawdown_duration": max_drawdown_duration,
            "value_at_risk_1y": float(var_95 * np.sqrt(252)),
            "conditional_var_95": (
                float(returns[returns <= var_95].mean() * np.sqrt(252))
                if len(returns[returns <= var_95]) > 0
                else 0
            ),
        }

    def _analyze_attribution(self, dynamic_results: Dict[str, Any]) -> Dict[str, Any]:
        """分析收益歸因"""
        allocation_history = dynamic_results.get("allocation_history", [])
        regime_history = dynamic_results.get("regime_history", [])

        if not allocation_history or not regime_history:
            return {"analysis": "Insufficient data for attribution analysis"}

        # 按制度歸因
        regime_performance = {}
        for alloc_record, regime_record in zip(allocation_history, regime_history):
            regime = regime_record["current_regime"]
            performance_change = (
                alloc_record["portfolio_value"] / 100000 - 1
            )  # 假設基準100k

            if regime not in regime_performance:
                regime_performance[regime] = []
            regime_performance[regime].append(performance_change)

        # 計算制度表現
        regime_stats = {}
        for regime, returns in regime_performance.items():
            if returns:
                regime_stats[regime] = {
                    "total_return": sum(returns),
                    "average_return": np.mean(returns),
                    "volatility": np.std(returns),
                    "periods": len(returns),
                }

        # 覆蓋貢獻分析
        overlay_history = dynamic_results.get("overlay_history", [])
        overlay_contribution = 0

        for overlay_record in overlay_history:
            overlay_contribution += overlay_record.get("expected_overlay_return", 0)

        return {
            "regime_attribution": regime_stats,
            "total_overlay_contribution": overlay_contribution,
            "average_overlay_per_period": (
                overlay_contribution / len(overlay_history) if overlay_history else 0
            ),
            "regime_switching_frequency": len(
                set(r["current_regime"] for r in regime_history)
            )
            / len(regime_history),
            "analysis": f"Performance attributed across {len(regime_stats)} market regimes with overlay contribution of {overlay_contribution:.2%}",
        }

    def _get_training_data(
        self, market_data: Dict[str, pd.DataFrame], scenario_start: datetime
    ) -> Dict[str, pd.DataFrame]:
        """獲取訓練數據"""
        training_data = {}

        for symbol, data in market_data.items():
            # 使用場景開始前的數據進行訓練
            training_period = data[data.index < scenario_start]
            if len(training_period) >= 504:  # 至少2年訓練數據
                training_data[symbol] = training_period.tail(504)

        return training_data

    def _generate_rebalance_dates(self, scenario: BacktestScenario) -> List[datetime]:
        """生成再平衡日期"""
        if scenario.allocation_config:
            freq = scenario.allocation_config.rebalance_frequency
        else:
            freq = "monthly"

        dates = []
        current_date = scenario.start_date

        if freq == "daily":
            delta = timedelta(days = 1)
        elif freq == "weekly":
            delta = timedelta(weeks = 1)
        elif freq == "monthly":
            delta = timedelta(days = 30)
        else:  # quarterly
            delta = timedelta(days = 90)

        while current_date <= scenario.end_date:
            dates.append(current_date)
            current_date += delta

        return dates

    def _get_historical_data(
        self,
        market_data: Dict[str, pd.DataFrame],
        current_date: datetime,
        lookback_period: int,
    ) -> Dict[str, pd.DataFrame]:
        """獲取歷史數據"""
        historical_data = {}

        for symbol, data in market_data.items():
            # 篩選截至當前日期的數據
            mask = data.index <= current_date
            filtered_data = data[mask].copy()

            if len(filtered_data) >= lookback_period:
                historical_data[symbol] = filtered_data.tail(lookback_period)

        return historical_data

    def _execute_allocation(
        self,
        strategic_allocation: AllocationResult,
        overlay_result: OverlayResult,
        market_data: Dict[str, pd.DataFrame],
    ) -> Dict[str, Any]:
        """模擬執行配置"""
        # 簡化的執行模擬
        return {
            "strategic_cost": strategic_allocation.total_transaction_cost,
            "overlay_cost": overlay_result.total_overlay_cost,
            "total_cost": strategic_allocation.total_transaction_cost
            + overlay_result.total_overlay_cost,
            "execution_time": datetime.now(),
        }

    def _calculate_portfolio_value(
        self,
        weights: Dict[str, float],
        market_data: Dict[str, pd.DataFrame],
        current_value: float,
    ) -> float:
        """計算投資組合價值"""
        total_return = 0

        for symbol, weight in weights.items():
            if symbol in market_data and len(market_data[symbol]) > 1:
                # 計算單日回報率
                returns = market_data[symbol]["close"].pct_change().iloc[-1]
                total_return += weight * returns

        return current_value * (1 + total_return)

    def _calculate_final_metrics(
        self, portfolio_values: List[Dict], initial_capital: float
    ) -> Dict[str, float]:
        """計算最終性能指標"""
        if len(portfolio_values) < 2:
            return {
                "total_return": 0,
                "annualized_return": 0,
                "volatility": 0,
                "sharpe_ratio": 0,
                "max_drawdown": 0,
                "calmar_ratio": 0,
                "sortino_ratio": 0,
            }

        # 轉換為DataFrame
        df = pd.DataFrame(portfolio_values)
        df.set_index("date", inplace = True)

        # 計算回報率
        portfolio_returns = df["value"].pct_change().dropna()

        # 基本指標
        total_return = (df["value"].iloc[-1] / initial_capital) - 1
        days = (df.index[-1] - df.index[0]).days
        annualized_return = (1 + total_return) ** (365 / days) - 1 if days > 0 else 0
        volatility = portfolio_returns.std() * np.sqrt(365)

        # Sharpe比率
        risk_free_rate = 0.03
        sharpe_ratio = (
            (annualized_return - risk_free_rate) / volatility if volatility > 0 else 0
        )

        # 最大回撤
        cumulative = (1 + portfolio_returns).cumprod()
        rolling_max = cumulative.expanding().max()
        drawdown = (cumulative - rolling_max) / rolling_max
        max_drawdown = drawdown.min()

        # Calmar比率
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0

        # Sortino比率
        downside_returns = portfolio_returns[portfolio_returns < 0]
        downside_volatility = (
            downside_returns.std() * np.sqrt(365) if len(downside_returns) > 0 else 0
        )
        sortino_ratio = (
            (annualized_return - risk_free_rate) / downside_volatility
            if downside_volatility > 0
            else 0
        )

        return {
            "total_return": float(total_return),
            "annualized_return": float(annualized_return),
            "volatility": float(volatility),
            "sharpe_ratio": float(sharpe_ratio),
            "max_drawdown": float(max_drawdown),
            "calmar_ratio": float(calmar_ratio),
            "sortino_ratio": float(sortino_ratio),
        }

    def _calculate_max_dd_duration(self, drawdown: pd.Series) -> int:
        """計算最大回撤持續時間"""
        is_drawdown = drawdown < 0

        if not is_drawdown.any():
            return 0

        # 計算連續回撤期
        current_period = 0
        max_duration = 0

        for dd in is_drawdown:
            if dd:
                current_period += 1
                max_duration = max(max_duration, current_period)
            else:
                current_period = 0

        return max_duration

    def save_results(self, results: BacktestResults, filepath: str) -> None:
        """保存回測結果"""
        # 轉換為可序列化格式
        serializable_results = {
            "scenario": {
                "name": results.scenario.name,
                "description": results.scenario.description,
                "start_date": results.scenario.start_date.isoformat(),
                "end_date": results.scenario.end_date.isoformat(),
                "initial_capital": results.scenario.initial_capital,
                "benchmark_name": results.scenario.benchmark_name,
            },
            "execution_time": results.execution_time,
            "performance_comparison": results.performance_comparison,
            "dynamic_summary": {
                "final_portfolio_value": results.dynamic_results.get(
                    "final_portfolio_value", 0
                ),
                "total_transactions": results.dynamic_results.get(
                    "total_transactions", 0
                ),
                "total_costs": results.dynamic_results.get("total_costs", 0),
                "final_metrics": results.dynamic_results.get("final_metrics", {}),
            },
            "benchmark_summary": {
                "final_portfolio_value": results.benchmark_results.get(
                    "final_portfolio_value", 0
                ),
                "final_metrics": results.benchmark_results.get("final_metrics", {}),
                "benchmark_weights": results.benchmark_results.get(
                    "benchmark_weights", {}
                ),
            },
            "trade_analysis": results.trade_analysis,
            "risk_analysis": results.risk_analysis,
            "attribution_analysis": results.attribution_analysis,
        }

        # 保存詳細數據到單獨文件
        base_path = Path(filepath)
        detailed_path = base_path.with_suffix(".detailed.json")

        detailed_data = {
            "allocation_history": results.allocation_history,
            "regime_history": results.regime_history,
            "overlay_history": results.overlay_history,
        }

        # 保存文件
        with open(filepath, "w") as f:
            json.dump(serializable_results, f, indent = 2, default = str)

        with open(detailed_path, "w") as f:
            json.dump(detailed_data, f, indent = 2, default = str)

        logger.info(f"Results saved to {filepath} and {detailed_path}")


# 便利函數
def run_dynamic_allocation_backtest(
    scenario_name: str,
    assets: List[AssetConfig],
    market_data: Dict[str, pd.DataFrame],
    start_date: datetime,
    end_date: datetime,
    initial_capital: float = 1000000,
    **kwargs,
) -> BacktestResults:
    """便利函數：運行動態配置回測"""
    scenario = BacktestScenario(
        name = scenario_name,
        description = f"Dynamic allocation backtest for {scenario_name}",
        start_date = start_date,
        end_date = end_date,
        initial_capital = initial_capital,
        assets = assets,
        **kwargs,
    )

    backtester = DynamicAllocationBacktester()
    return backtester.run_scenario(scenario, market_data)


def compare_multiple_scenarios(
    scenarios: List[BacktestScenario], market_data: Dict[str, pd.DataFrame]
) -> Dict[str, BacktestResults]:
    """便利函數：比較多個場景"""
    backtester = DynamicAllocationBacktester()
    results = {}

    for scenario in scenarios:
        logger.info(f"Running scenario: {scenario.name}")
        results[scenario.name] = backtester.run_scenario(scenario, market_data)

    return results

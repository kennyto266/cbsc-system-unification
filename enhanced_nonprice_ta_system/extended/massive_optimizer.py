#!/usr/bin/env python3
"""
Phase 3 Complete: Massive Parameter Optimization System
完整大規模參數優化系統

Integration of Parameter Space, Parallel Optimizer, and Performance Evaluator
Complete Phase 3 implementation for massive scale optimization
"""

import json
import logging
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Callable
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd
from tqdm import tqdm

# Import Phase 3 components
from .parameter_space import ExtendedParameterSpace
from .parallel_optimizer import ParallelParameterOptimizer, OptimizationTask, OptimizationResult
from .performance_evaluator import PerformanceEvaluator, EvaluationResult

# Import existing indicators
from ..data_manager import GovernmentDataManager
from ..indicator_engine import EnhancedIndicatorEngine

logger = logging.getLogger(__name__)

@dataclass
class OptimizationConfig:
    """優化配置"""
    # Data configuration
    symbol: str = "0700.HK"
    data_period: int = 365  # days
    use_government_data: bool = True

    # Parameter space configuration
    indicators: List[str] = field(default_factory=list)
    max_combinations_per_indicator: int = 1000
    enable_smart_sampling: bool = True

    # Parallel configuration
    num_workers: int = 32
    use_multiprocessing: bool = True
    enable_progress_bar: bool = True

    # Evaluation configuration
    risk_free_rate: float = 0.03
    enable_overfitting_detection: bool = True
    min_trades_for_evaluation: int = 30

    # Output configuration
    output_dir: str = "results"
    export_top_n: int = 100
    generate_report: bool = True

@dataclass
class OptimizationSummary:
    """優化摘要"""
    config: OptimizationConfig
    total_combinations: int
    executed_combinations: int
    cached_combinations: int
    error_combinations: int
    execution_time: float
    best_result: Optional[EvaluationResult] = None
    top_results: List[EvaluationResult] = field(default_factory=list)
    pareto_frontier: List[EvaluationResult] = field(default_factory=list)

class MassiveParameterOptimizer:
    """大規模參數優化器"""

    def __init__(self, config: OptimizationConfig = None):
        """
        初始化大規模參數優化器

        Args:
            config: 優化配置，如果為None則使用默認配置
        """
        self.config = config or OptimizationConfig()

        # 初始化組件
        self.param_space = ExtendedParameterSpace()
        self.evaluator = PerformanceEvaluator(
            risk_free_rate=self.config.risk_free_rate,
            enable_overfitting_detection=self.config.enable_overfitting_detection,
            min_trades_for_evaluation=self.config.min_trades_for_evaluation
        )

        # 數據管理器
        self.data_manager = GovernmentDataManager()
        self.indicator_engine = EnhancedIndicatorEngine()

        # 市場數據
        self.market_data = None
        self.government_data = None

        # 統計信息
        self.optimization_summary = None

        # 創建輸出目錄
        Path(self.config.output_dir).mkdir(exist_ok=True)

        logger.info("MassiveParameterOptimizer initialized")

    def prepare_data(self) -> bool:
        """準備優化數據"""
        logger.info(f"Preparing market data for {self.config.symbol}")

        try:
            # 獲取市場數據
            self.market_data = self.data_manager.get_market_data(
                self.config.symbol,
                period=self.config.data_period
            )

            if self.market_data is None or len(self.market_data) == 0:
                logger.error(f"No market data available for {self.config.symbol}")
                return False

            logger.info(f"Loaded {len(self.market_data)} market data points")

            # 獲取政府數據
            if self.config.use_government_data:
                self.government_data = self.data_manager.get_all_government_data()
                logger.info(f"Loaded government data from {len(self.government_data)} sources")

            return True

        except Exception as e:
            logger.error(f"Failed to prepare data: {e}")
            return False

    def run_optimization(self) -> OptimizationSummary:
        """執行完整的大規模優化"""
        start_time = time.time()

        logger.info("Starting massive parameter optimization")
        logger.info(f"Configuration: {self.config}")

        # 準備數據
        if not self.prepare_data():
            raise RuntimeError("Failed to prepare optimization data")

        # 準備指標列表
        if not self.config.indicators:
            # 使用所有啟用的指標
            self.config.indicators = list(self.param_space.indicator_configs.keys())

        logger.info(f"Optimizing {len(self.config.indicators)} indicators")

        # 生成參數組合
        indicator_tasks = self._generate_parameter_tasks()

        total_combinations = sum(len(tasks) for _, tasks in indicator_tasks)
        logger.info(f"Generated {total_combinations} parameter combinations")

        # 創建並行優化器
        parallel_optimizer = ParallelParameterOptimizer(
            objective_function=self._evaluate_single_combination,
            num_workers=self.config.num_workers,
            use_multiprocessing=self.config.use_multiprocessing,
            enable_progress_bar=self.config.enable_progress_bar
        )

        # 執行並行優化
        optimization_results = parallel_optimizer.optimize_indicators(
            indicator_tasks,
            max_tasks_per_indicator=self.config.max_combinations_per_indicator
        )

        # 轉換結果為評估結果
        evaluation_results = self._convert_to_evaluation_results(optimization_results)

        # 排名和分析結果
        ranked_results = self.evaluator.rank_results(evaluation_results)
        pareto_frontier = self.evaluator.get_pareto_frontier(evaluation_results)

        # 創建優化摘要
        execution_time = time.time() - start_time
        best_result = ranked_results[0] if ranked_results else None
        top_results = ranked_results[:self.config.export_top_n]

        self.optimization_summary = OptimizationSummary(
            config=self.config,
            total_combinations=total_combinations,
            executed_combinations=len(evaluation_results),
            cached_combinations=parallel_optimizer.cached_tasks,
            error_combinations=parallel_optimizer.error_tasks,
            execution_time=execution_time,
            best_result=best_result,
            top_results=top_results,
            pareto_frontier=pareto_frontier
        )

        # 導出結果
        self._export_results()

        # 生成報告
        if self.config.generate_report:
            self._generate_optimization_report()

        logger.info(f"Optimization completed in {execution_time:.2f}s")
        logger.info(f"Best strategy: {best_result.indicator_name if best_result else 'None'} "
                   f"with score {best_result.composite_score:.3f}" if best_result else "")

        return self.optimization_summary

    def _generate_parameter_tasks(self) -> List[Tuple[str, List[Dict]]]:
        """生成參數任務列表"""
        indicator_tasks = []

        for indicator_name in self.config.indicators:
            config = self.param_space.get_indicator_config(indicator_name)
            if not config or not config.enabled:
                logger.warning(f"Skipping disabled indicator: {indicator_name}")
                continue

            # 生成參數組合
            parameter_combinations = self.param_space.generate_parameter_combinations(
                indicator_name,
                max_combinations=self.config.max_combinations_per_indicator if self.config.enable_smart_sampling else None
            )

            indicator_tasks.append((indicator_name, parameter_combinations))

            logger.info(f"Generated {len(parameter_combinations)} combinations for {indicator_name}")

        return indicator_tasks

    def _evaluate_single_combination(self, indicator_name: str, parameters: Dict) -> Dict[str, float]:
        """評估單個參數組合"""
        try:
            # 計算技術指標
            indicator_values = self._calculate_indicator(indicator_name, parameters)

            if indicator_values is None or len(indicator_values) == 0:
                raise ValueError("Failed to calculate indicator values")

            # 生成交易信號
            signals = self._generate_trading_signals(indicator_name, indicator_values, parameters)

            if signals is None or len(signals) == 0:
                raise ValueError("Failed to generate trading signals")

            # 計算收益序列
            returns = self._calculate_returns(signals)

            if len(returns) < self.config.min_trades_for_evaluation:
                raise ValueError(f"Insufficient trades: {len(returns)}")

            # 模擬交易數據
            trades_data = self._simulate_trades(signals, returns)

            # 評估性能
            evaluation_result = self.evaluator.evaluate_strategy(
                indicator_name=indicator_name,
                parameters=parameters,
                returns_data=returns,
                trades_data=trades_data
            )

            # 返回性能指標字典
            metrics = evaluation_result.performance_metrics
            return {
                "sharpe_ratio": metrics.sharpe_ratio,
                "total_return": metrics.total_return,
                "max_drawdown": metrics.max_drawdown,
                "annualized_return": metrics.annualized_return,
                "volatility": metrics.volatility,
                "calmar_ratio": metrics.calmar_ratio,
                "win_rate": metrics.win_rate,
                "profit_factor": metrics.profit_factor,
                "stability_score": metrics.stability_score,
                "consistency_score": metrics.consistency_score,
                "composite_score": evaluation_result.composite_score
            }

        except Exception as e:
            logger.warning(f"Failed to evaluate {indicator_name} with parameters {parameters}: {e}")
            # 返回最差可能的指標
            return {
                "sharpe_ratio": -999.0,
                "total_return": -1.0,
                "max_drawdown": -1.0,
                "annualized_return": -1.0,
                "volatility": 999.0,
                "calmar_ratio": -999.0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "stability_score": 0.0,
                "consistency_score": 0.0,
                "composite_score": -999.0
            }

    def _calculate_indicator(self, indicator_name: str, parameters: Dict) -> Optional[np.ndarray]:
        """計算技術指標"""
        try:
            # 根據指標類型選擇計算方法
            if indicator_name in ["RSI", "MACD", "KDJ", "BOLLINGER_BANDS", "SMA_CROSS", "EMA_CROSS"]:
                # 價格技術指標
                close_prices = self.market_data['close'].values
                return self.indicator_engine.calculate_technical_indicator(indicator_name, close_prices, parameters)

            elif indicator_name in ["MOMENTUM", "ROC", "CCI", "WILLIAMS_R", "STOCH"]:
                # 動量指標
                close_prices = self.market_data['close'].values
                high_prices = self.market_data['high'].values
                low_prices = self.market_data['low'].values
                return self.indicator_engine.calculate_momentum_indicator(indicator_name, close_prices, high_prices, low_prices, parameters)

            elif indicator_name in ["ATR", "VIX_STYLE"]:
                # 波動率指標
                close_prices = self.market_data['close'].values
                high_prices = self.market_data['high'].values
                low_prices = self.market_data['low'].values
                return self.indicator_engine.calculate_volatility_indicator(indicator_name, close_prices, high_prices, low_prices, parameters)

            elif indicator_name.startswith("MB_") or indicator_name.startswith("HIBOR_") or \
                 indicator_name.startswith("PROPERTY_") or indicator_name.startswith("UNIFIED_"):
                # 專業化指標（需要政府數據）
                if self.government_data:
                    return self.indicator_engine.calculate_specialized_indicator(
                        indicator_name, self.market_data, self.government_data, parameters
                    )
                else:
                    logger.warning(f"Government data required for {indicator_name} but not available")
                    return None

            else:
                logger.warning(f"Unknown indicator: {indicator_name}")
                return None

        except Exception as e:
            logger.error(f"Error calculating {indicator_name}: {e}")
            return None

    def _generate_trading_signals(self, indicator_name: str, indicator_values: np.ndarray, parameters: Dict) -> Optional[np.ndarray]:
        """生成交易信號"""
        try:
            signals = np.zeros(len(indicator_values))

            if indicator_name == "RSI":
                period = parameters.get("period", 14)
                oversold = parameters.get("oversold", 30)
                overbought = parameters.get("overbought", 70)

                # RSI均值回歸策略
                buy_signals = indicator_values < oversold
                sell_signals = indicator_values > overbought

                signals[buy_signals] = 1   # 買入信號
                signals[sell_signals] = -1  # 賣出信號

            elif indicator_name == "MACD":
                # MACD交叉策略
                if len(indicator_values.shape) > 1 and indicator_values.shape[1] >= 2:
                    macd_line = indicator_values[:, 0]
                    signal_line = indicator_values[:, 1]

                    signals[macd_line > signal_line] = 1
                    signals[macd_line < signal_line] = -1

            elif indicator_name == "KDJ":
                # KDJ策略
                if len(indicator_values.shape) > 1 and indicator_values.shape[1] >= 2:
                    k_line = indicator_values[:, 0]
                    d_line = indicator_values[:, 1]

                    signals[(k_line < 20) & (d_line < 20)] = 1  # 超賣買入
                    signals[(k_line > 80) & (d_line > 80)] = -1  # 超買賣出

            elif indicator_name in ["SMA_CROSS", "EMA_CROSS"]:
                # 移動平均交叉策略
                if len(indicator_values.shape) > 1 and indicator_values.shape[1] >= 2:
                    short_ma = indicator_values[:, 0]
                    long_ma = indicator_values[:, 1]

                    signals[short_ma > long_ma] = 1
                    signals[short_ma < long_ma] = -1

            elif indicator_name.startswith("MB_KDJ"):
                # 貨幣基礎KDJ策略
                signal_threshold = parameters.get("signal_threshold", 0.5)
                signals[indicator_values > signal_threshold] = 1
                signals[indicator_values < -signal_threshold] = -1

            else:
                # 默認策略：指標正值買入，負值賣出
                signals[indicator_values > 0] = 1
                signals[indicator_values < 0] = -1

            return signals

        except Exception as e:
            logger.error(f"Error generating signals for {indicator_name}: {e}")
            return None

    def _calculate_returns(self, signals: np.ndarray) -> List[float]:
        """計算收益序列"""
        try:
            price_returns = self.market_data['close'].pct_change().values
            strategy_returns = []

            for i in range(1, len(signals)):
                if signals[i-1] == 1:  # 買入
                    strategy_returns.append(price_returns[i])
                elif signals[i-1] == -1:  # 賣出
                    strategy_returns.append(-price_returns[i])
                else:  # 持有現金
                    strategy_returns.append(0.0)

            return strategy_returns

        except Exception as e:
            logger.error(f"Error calculating returns: {e}")
            return []

    def _simulate_trades(self, signals: np.ndarray, returns: List[float]) -> List[Dict]:
        """模擬交易"""
        trades = []
        current_position = 0
        entry_price = None
        entry_date = None

        for i, (signal, ret) in enumerate(zip(signals[1:], returns)):
            if signal == 1 and current_position <= 0:
                # 開倉買入
                current_position = 1
                entry_price = self.market_data['close'].iloc[i+1]
                entry_date = self.market_data.index[i+1]

            elif signal == -1 and current_position > 0:
                # 平倉
                exit_price = self.market_data['close'].iloc[i+1]
                trade_return = (exit_price - entry_price) / entry_price

                trades.append({
                    "entry_date": str(entry_date),
                    "exit_date": str(self.market_data.index[i+1]),
                    "return": trade_return,
                    "entry_price": entry_price,
                    "exit_price": exit_price
                })

                current_position = 0
                entry_price = None
                entry_date = None

        return trades

    def _convert_to_evaluation_results(self, optimization_results: List[OptimizationResult]) -> List[EvaluationResult]:
        """轉換優化結果為評估結果"""
        evaluation_results = []

        for opt_result in optimization_results:
            # 重構PerformanceMetrics
            metrics = PerformanceMetrics(
                sharpe_ratio=opt_result.performance_metrics.get("sharpe_ratio", -999),
                total_return=opt_result.performance_metrics.get("total_return", 0),
                max_drawdown=opt_result.performance_metrics.get("max_drawdown", 0),
                annualized_return=opt_result.performance_metrics.get("annualized_return", 0),
                volatility=opt_result.performance_metrics.get("volatility", 0),
                calmar_ratio=opt_result.performance_metrics.get("calmar_ratio", 0),
                win_rate=opt_result.performance_metrics.get("win_rate", 0),
                profit_factor=opt_result.performance_metrics.get("profit_factor", 0),
                stability_score=opt_result.performance_metrics.get("stability_score", 0),
                consistency_score=opt_result.performance_metrics.get("consistency_score", 0)
            )

            # 創建EvaluationResult
            eval_result = EvaluationResult(
                indicator_name=opt_result.indicator_name,
                parameters=opt_result.parameters,
                performance_metrics=metrics,
                overfitting_detection=self.evaluator._detect_overfitting(
                    opt_result.indicator_name,
                    opt_result.parameters,
                    metrics,
                    []  # 簡化版，不傳入完整收益數據
                ),
                composite_score=opt_result.performance_metrics.get("composite_score", 0)
            )

            evaluation_results.append(eval_result)

        return evaluation_results

    def _export_results(self):
        """導出優化結果"""
        if not self.optimization_summary:
            logger.warning("No optimization results to export")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 導出Top結果
        top_results_file = Path(self.config.output_dir) / f"top_results_{timestamp}.json"
        top_data = []
        for result in self.optimization_summary.top_results:
            top_data.append({
                "rank": result.rank,
                "indicator": result.indicator_name,
                "parameters": result.parameters,
                "composite_score": result.composite_score,
                "sharpe_ratio": result.performance_metrics.sharpe_ratio,
                "total_return": result.performance_metrics.total_return,
                "max_drawdown": result.performance_metrics.max_drawdown,
                "is_overfitted": result.overfitting_detection.is_overfitted
            })

        with open(top_results_file, 'w', encoding='utf-8') as f:
            json.dump(top_data, f, indent=2, ensure_ascii=False)

        # 導出帕累托前沿
        pareto_file = Path(self.config.output_dir) / f"pareto_frontier_{timestamp}.json"
        pareto_data = []
        for result in self.optimization_summary.pareto_frontier:
            pareto_data.append({
                "indicator": result.indicator_name,
                "parameters": result.parameters,
                "composite_score": result.composite_score,
                "sharpe_ratio": result.performance_metrics.sharpe_ratio,
                "total_return": result.performance_metrics.total_return,
                "max_drawdown": result.performance_metrics.max_drawdown
            })

        with open(pareto_file, 'w', encoding='utf-8') as f:
            json.dump(pareto_data, f, indent=2, ensure_ascii=False)

        # 導出優化摘要
        summary_file = Path(self.config.output_dir) / f"optimization_summary_{timestamp}.json"
        summary_data = {
            "config": {
                "symbol": self.config.symbol,
                "data_period": self.config.data_period,
                "indicators": self.config.indicators,
                "max_combinations_per_indicator": self.config.max_combinations_per_indicator,
                "num_workers": self.config.num_workers
            },
            "statistics": {
                "total_combinations": self.optimization_summary.total_combinations,
                "executed_combinations": self.optimization_summary.executed_combinations,
                "cached_combinations": self.optimization_summary.cached_combinations,
                "error_combinations": self.optimization_summary.error_combinations,
                "execution_time": self.optimization_summary.execution_time
            },
            "best_strategy": {
                "indicator": self.optimization_summary.best_result.indicator_name if self.optimization_summary.best_result else None,
                "parameters": self.optimization_summary.best_result.parameters if self.optimization_summary.best_result else None,
                "composite_score": self.optimization_summary.best_result.composite_score if self.optimization_summary.best_result else 0,
                "sharpe_ratio": self.optimization_summary.best_result.performance_metrics.sharpe_ratio if self.optimization_summary.best_result else 0
            }
        }

        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Results exported to {self.config.output_dir}")

    def _generate_optimization_report(self):
        """生成優化報告"""
        if not self.optimization_summary:
            logger.warning("No optimization results for report generation")
            return

        # 生成詳細評估報告
        evaluation_results = self.optimization_summary.top_results + self.optimization_summary.pareto_frontier
        report_file = self.evaluator.generate_evaluation_report(
            evaluation_results,
            str(Path(self.config.output_dir) / f"detailed_evaluation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        )

        logger.info(f"Detailed evaluation report generated: {report_file}")

# Quick test function
def quick_test():
    """快速測試大規模優化器"""
    logging.basicConfig(level=logging.INFO)

    # 創建測試配置
    config = OptimizationConfig(
        symbol="0700.HK",
        data_period=180,  # 6個月數據
        indicators=["RSI", "MACD"],  # 只測試兩個指標
        max_combinations_per_indicator=10,
        num_workers=2,  # 使用較少的工作線程進行測試
        use_multiprocessing=False,  # 使用多線程以避免進程問題
        output_dir="test_results"
    )

    # 創建優化器
    optimizer = MassiveParameterOptimizer(config)

    try:
        # 執行優化
        summary = optimizer.run_optimization()

        print("\n=== Test Results ===")
        print(f"Total combinations: {summary.total_combinations}")
        print(f"Executed: {summary.executed_combinations}")
        print(f"Cached: {summary.cached_combinations}")
        print(f"Errors: {summary.error_combinations}")
        print(f"Execution time: {summary.execution_time:.2f}s")

        if summary.best_result:
            print(f"\nBest strategy: {summary.best_result.indicator_name}")
            print(f"Parameters: {summary.best_result.parameters}")
            print(f"Composite score: {summary.best_result.composite_score:.3f}")
            print(f"Sharpe ratio: {summary.best_result.performance_metrics.sharpe_ratio:.3f}")

    except Exception as e:
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    quick_test()
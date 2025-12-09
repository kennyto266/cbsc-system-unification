#!/usr / bin / env python3
"""
大規模參數優化系統 - 統一入口
Massive Parameter Optimization System - Unified Entry Point

Phase 3 完整實現，提供：
- 百萬級參數組合優化
- 32核高性能並行處理
- 綜合性能評估和過擬合檢測
- 詳細的優化報告生成

使用示例：
    python massive_optimizer.py --strategy RSI_MEAN_REVERSION --symbol 0700.HK --combinations 50000
"""

import argparse
import json
import logging
import os
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

from .parallel_optimizer import (
    OptimizationConfig,
    ParallelOptimizer,
    parallel_optimizer,
)
from .parameter_space import ParameterSpaceManager, parameter_space_manager
from .performance_evaluator import PerformanceEvaluator, performance_evaluator

# 導入系統模塊
from .vectorbt_engine import VectorBTEngine

# 導入數據接口
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from src.api.government_data import get_hibor_data
from src.api.stock_api import get_hk_stock_data

logger = logging.getLogger(__name__)


class MassiveOptimizer:
    """
    大規模參數優化系統

    整合Phase 3所有組件，提供統一的優化入口：
    - 參數空間定義和管理
    - 高性能並行優化
    - 綜合性能評估
    - 過擬合檢測和防護
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化大規模優化系統

        Args:
            config: 系統配置
        """
        self.config = self._load_config(config)

        # 初始化核心組件
        self.parameter_space = ParameterSpaceManager()
        self.parallel_optimizer = ParallelOptimizer(
            OptimizationConfig(**self.config.get("parallel", {}))
        )
        self.performance_evaluator = PerformanceEvaluator(
            risk_free_rate = self.config.get("risk_free_rate", 0.03)
        )

        # 優化配置
        self.results_dir = self.config.get(
            "results_dir", "massive_optimization_results"
        )
        Path(self.results_dir).mkdir(parents = True, exist_ok = True)

        logger.info("Massive optimizer initialized with full Phase 3 capabilities")

    def optimize_single_strategy(
        self,
        strategy_name: str,
        symbol: str,
        data: Optional[pd.DataFrame] = None,
        max_combinations: int = 10000,
        optimization_metric: str = "sharpe_ratio",
        include_overfitting_analysis: bool = True,
        validation_split: float = 0.2,
    ) -> Dict[str, Any]:
        """
        單策略大規模優化

        Args:
            strategy_name: 策略名稱
            symbol: 股票代碼
            data: OHLCV數據（可選，會自動獲取）
            max_combinations: 最大參數組合數
            optimization_metric: 優化目標
            include_overfitting_analysis: 是否包含過擬合分析
            validation_split: 驗證集比例

        Returns:
            完整的優化結果
        """
        logger.info(f"Starting massive optimization for {strategy_name} on {symbol}")

        start_time = time.time()

        try:
            # 獲取數據
            if data is None:
                data = self._get_market_data(symbol)

            # 數據分割（用於過擬合檢測）
            train_data, validation_data = self._split_data(data, validation_split)

            # 生成參數組合
            param_space = self.parameter_space.get_strategy_space(strategy_name)
            if param_space is None:
                raise ValueError(f"Strategy {strategy_name} not supported")

            param_space.max_combinations = max_combinations
            parameter_combinations = param_space.generate_parameter_combinations()

            logger.info(
                f"Generated {len(parameter_combinations)} parameter combinations"
            )

            # 執行並行優化
            optimization_results = self.parallel_optimizer.optimize_strategy(
                strategy_name = strategy_name,
                data = train_data,
                symbol = symbol,
                param_space = param_space,
                optimization_metric = optimization_metric,
                max_combinations = max_combinations,
            )

            # 獲取最佳回測結果
            best_result = self._get_best_backtest_result(
                optimization_results, train_data, strategy_name, symbol
            )

            # 過擬合分析
            overfitting_analysis = None
            if include_overfitting_analysis and validation_data is not None:
                all_results = self._get_all_backtest_results(
                    optimization_results, train_data, strategy_name, symbol
                )
                overfitting_analysis = self.performance_evaluator.detect_overfitting(
                    all_results, validation_data
                )

            # 生成綜合性能報告
            performance_report = self.performance_evaluator.generate_performance_report(
                backtest_result = best_result,
                optimization_results = self._get_all_backtest_results(
                    optimization_results, train_data, strategy_name, symbol
                ),
                benchmark_data = data,  # 使用全部數據作為基準
                include_overfitting_analysis = include_overfitting_analysis,
            )

            # 組合最終結果
            final_results = {
                "optimization_summary": {
                    "strategy_name": strategy_name,
                    "symbol": symbol,
                    "optimization_metric": optimization_metric,
                    "max_combinations": max_combinations,
                    "actual_combinations": optimization_results.get(
                        "successful_combinations", 0
                    ),
                    "execution_time": time.time() - start_time,
                    "parallel_config": self.parallel_optimizer.config.__dict__,
                },
                "best_strategy": {
                    "parameters": optimization_results.get("best_parameters", {}),
                    "performance_metrics": optimization_results.get(
                        "best_performance", {}
                    ),
                    "backtest_result": best_result.to_dict() if best_result else None,
                },
                "optimization_statistics": optimization_results.get(
                    "performance_statistics", {}
                ),
                "top_strategies": optimization_results.get("top_results", [])[:10],
                "performance_report": performance_report,
                "overfitting_analysis": (
                    overfitting_analysis.to_dict() if overfitting_analysis else None
                ),
                "parameter_space_analysis": {
                    "total_possible_combinations": param_space.get_total_combinations(),
                    "efficiency_ratio": len(parameter_combinations)
                    / param_space.get_total_combinations(),
                    "parameter_importance": self._analyze_parameter_importance(
                        optimization_results
                    ),
                },
                "system_performance": {
                    "parallel_efficiency": self.parallel_optimizer.stats.get(
                        "parallel_efficiency", 0
                    ),
                    "tasks_per_second": self.parallel_optimizer.stats.get(
                        "tasks_per_second", 0
                    ),
                    "cache_hit_rate": self.parallel_optimizer.stats.get(
                        "cache_hit_rate", 0
                    ),
                },
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "data_period": {
                        "start_date": (
                            data.index[0].strftime("%Y-%m-%d")
                            if len(data) > 0
                            else None
                        ),
                        "end_date": (
                            data.index[-1].strftime("%Y-%m-%d")
                            if len(data) > 0
                            else None
                        ),
                        "total_days": len(data),
                    },
                    "system_version": "Phase 3 - Massive Optimizer v1.0",
                },
            }

            # 保存結果
            self._save_optimization_results(strategy_name, symbol, final_results)

            # 生成報告
            self._generate_html_report(strategy_name, symbol, final_results)

            logger.info(
                f"Massive optimization completed for {strategy_name} on {symbol}"
            )
            return final_results

        except Exception as e:
            logger.error(f"Error in massive optimization: {e}")
            return {
                "error": str(e),
                "strategy_name": strategy_name,
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
            }

    def optimize_multiple_strategies(
        self,
        strategy_names: List[str],
        symbol: str,
        data: Optional[pd.DataFrame] = None,
        max_combinations_per_strategy: int = 5000,
        optimization_metric: str = "sharpe_ratio",
    ) -> Dict[str, Any]:
        """
        多策略並行優化

        Args:
            strategy_names: 策略名稱列表
            symbol: 股票代碼
            data: OHLCV數據
            max_combinations_per_strategy: 每策略最大組合數
            optimization_metric: 優化目標

        Returns:
            多策略優化結果
        """
        logger.info(
            f"Starting multi - strategy massive optimization for {len(strategy_names)} strategies"
        )

        start_time = time.time()

        try:
            # 獲取數據
            if data is None:
                data = self._get_market_data(symbol)

            # 執行多策略優化
            multi_strategy_results = (
                self.parallel_optimizer.optimize_multiple_strategies(
                    strategy_names = strategy_names,
                    data = data,
                    symbol = symbol,
                    max_combinations_per_strategy = max_combinations_per_strategy,
                    optimization_metric = optimization_metric,
                )
            )

            # 分析各策略性能
            strategy_analysis = {}
            best_overall_strategy = None
            best_overall_metric = float("-inf")

            for strategy_name, results in multi_strategy_results.items():
                if results.get("successful_combinations", 0) > 0:
                    strategy_analysis[strategy_name] = {
                        "best_parameters": results.get("best_parameters", {}),
                        "best_metric": results.get("best_metric", 0),
                        "total_combinations": results.get("total_combinations", 0),
                        "successful_combinations": results.get(
                            "successful_combinations", 0
                        ),
                        "performance_stats": results.get("performance_statistics", {}),
                    }

                    # 找到整體最佳策略
                    if results.get("best_metric", 0) > best_overall_metric:
                        best_overall_metric = results.get("best_metric", 0)
                        best_overall_strategy = strategy_name

            # 生成綜合報告
            final_results = {
                "multi_strategy_summary": {
                    "symbol": symbol,
                    "strategies_tested": strategy_names,
                    "total_combinations": sum(
                        r.get("total_combinations", 0)
                        for r in multi_strategy_results.values()
                    ),
                    "total_successful": sum(
                        r.get("successful_combinations", 0)
                        for r in multi_strategy_results.values()
                    ),
                    "execution_time": time.time() - start_time,
                    "best_strategy": best_overall_strategy,
                    "best_metric": best_overall_metric,
                },
                "individual_results": multi_strategy_results,
                "strategy_comparison": strategy_analysis,
                "system_performance": self.parallel_optimizer.get_optimization_report(),
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "data_period": {
                        "start_date": (
                            data.index[0].strftime("%Y-%m-%d")
                            if len(data) > 0
                            else None
                        ),
                        "end_date": (
                            data.index[-1].strftime("%Y-%m-%d")
                            if len(data) > 0
                            else None
                        ),
                        "total_days": len(data),
                    },
                },
            }

            # 保存結果
            self._save_multi_strategy_results(symbol, final_results)

            logger.info(f"Multi - strategy massive optimization completed for {symbol}")
            return final_results

        except Exception as e:
            logger.error(f"Error in multi - strategy massive optimization: {e}")
            return {
                "error": str(e),
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
            }

    def run_million_parameter_challenge(
        self,
        strategy_name: str,
        symbol: str,
        target_combinations: int = 1000000,
        optimization_metric: str = "sharpe_ratio",
    ) -> Dict[str, Any]:
        """
        百萬參數挑戰 - 測試系統極限性能

        Args:
            strategy_name: 策略名稱
            symbol: 股票代碼
            target_combinations: 目標組合數（百萬級）
            optimization_metric: 優化目標

        Returns:
            百萬參數挑戰結果
        """
        logger.info(
            f"Starting MILLION PARAMETER CHALLENGE: {target_combinations:,} combinations"
        )

        challenge_start = time.time()

        try:
            # 獲取數據
            data = self._get_market_data(symbol)

            # 獲取策略參數空間
            param_space = self.parameter_space.get_strategy_space(strategy_name)
            if param_space is None:
                raise ValueError(f"Strategy {strategy_name} not supported")

            # 擴展參數範圍以達到目標組合數
            total_possible = param_space.get_total_combinations()
            if total_possible < target_combinations:
                logger.warning(
                    f"Strategy only supports {total_possible:,} combinations, "
                    f"less than target {target_combinations:,}"
                )
                target_combinations = total_possible

            # 優化並行配置以達到最大性能
            optimized_config = OptimizationConfig(
                max_workers = 32,  # 最大化並行
                use_processes = True,
                chunk_size = 50,  # 增大批次大小
                enable_gpu = True,
                cache_results = True,
                save_intermediate = True,
                progress_update_interval = 10.0,
            )

            # 創建高性能優化器
            high_performance_optimizer = ParallelOptimizer(optimized_config)

            # 執行百萬參數優化
            logger.info(f"Executing {target_combinations:,} parameter combinations...")

            optimization_results = high_performance_optimizer.optimize_strategy(
                strategy_name = strategy_name,
                data = data,
                symbol = symbol,
                param_space = param_space,
                optimization_metric = optimization_metric,
                max_combinations = target_combinations,
            )

            # 計算性能指標
            challenge_time = time.time() - challenge_start
            combinations_per_second = (
                optimization_results.get("successful_combinations", 0) / challenge_time
            )
            parallel_efficiency = high_performance_optimizer.stats.get(
                "parallel_efficiency", 0
            )

            # 挑戰結果評估
            challenge_results = {
                "challenge_summary": {
                    "strategy": strategy_name,
                    "symbol": symbol,
                    "target_combinations": target_combinations,
                    "actual_combinations": optimization_results.get(
                        "successful_combinations", 0
                    ),
                    "challenge_time_seconds": challenge_time,
                    "combinations_per_second": combinations_per_second,
                    "parallel_efficiency_percent": parallel_efficiency,
                    "best_metric_found": optimization_results.get(
                        "best_performance", {}
                    ).get(optimization_metric, 0),
                },
                "performance_breakdown": {
                    "total_execution_time": challenge_time,
                    "average_task_time": high_performance_optimizer.stats.get(
                        "average_task_time", 0
                    ),
                    "cache_hit_rate": high_performance_optimizer.stats.get(
                        "cache_hit_rate", 0
                    ),
                    "system_resources": {
                        "max_workers": optimized_config.max_workers,
                        "use_processes": optimized_config.use_processes,
                        "gpu_enabled": optimized_config.enable_gpu,
                    },
                },
                "optimization_results": optimization_results,
                "challenge_grade": self._calculate_challenge_grade(
                    combinations_per_second, parallel_efficiency, target_combinations
                ),
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "challenge_name": "Million Parameter Challenge",
                    "system_version": "Phase 3 - Massive Optimizer v1.0",
                },
            }

            # 保存挑戰結果
            challenge_filename = f"million_challenge_{strategy_name}_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            challenge_path = os.path.join(self.results_dir, challenge_filename)
            with open(challenge_path, "w", encoding="utf - 8") as f:
                json.dump(
                    challenge_results, f, indent = 2, ensure_ascii = False, default = str
                )

            logger.info(f"MILLION PARAMETER CHALLENGE COMPLETED!")
            logger.info(
                f"Performance: {combinations_per_second:,.1f} combinations / second"
            )
            logger.info(f"Efficiency: {parallel_efficiency:.1f}%")
            logger.info(f"Results saved to: {challenge_path}")

            return challenge_results

        except Exception as e:
            logger.error(f"Million parameter challenge failed: {e}")
            return {
                "error": str(e),
                "challenge_name": "Million Parameter Challenge",
                "timestamp": datetime.now().isoformat(),
            }

    # 私有方法
    def _load_config(self, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """加載配置"""
        default_config = {
            "risk_free_rate": 0.03,
            "results_dir": "massive_optimization_results",
            "parallel": {
                "max_workers": 16,
                "use_processes": True,
                "enable_gpu": True,
                "cache_results": True,
                "save_intermediate": True,
                "progress_update_interval": 5.0,
            },
            "data_source": {"preferred_period": "3y", "cache_data": True},  # 3年數據
        }

        if config:
            default_config.update(config)

        return default_config

    def _get_market_data(self, symbol: str) -> pd.DataFrame:
        """獲取市場數據"""
        try:
            # 使用簡化系統的股票API
            data = get_hk_stock_data(symbol, duration_days = 1095)  # 3年數據

            # 轉換為OHLCV格式
            if isinstance(data, dict) and "data" in data:
                df_data = data["data"]
                if "close" in df_data:
                    # 重構DataFrame
                    dates = list(df_data["close"].keys())
                    close_prices = list(df_data["close"].values())

                    df = pd.DataFrame(
                        {"close": close_prices}, index = pd.to_datetime(dates)
                    )

                    # 如果有其他價格數據，添加進去
                    for field in ["open", "high", "low"]:
                        if field in df_data:
                            df[field] = list(df_data[field].values())
                        else:
                            df[field] = df["close"]  # 如果沒有，使用收盤價

                    # 添加成交量（默認值）
                    df["volume"] = 1000000  # 默認成交量

                    return df

            raise ValueError("Invalid data format received")

        except Exception as e:
            logger.error(f"Failed to get market data for {symbol}: {e}")
            # 創建模擬數據
            return self._create_synthetic_data(symbol)

    def _create_synthetic_data(self, symbol: str) -> pd.DataFrame:
        """創建模擬數據（後備方案）"""
        logger.warning(f"Creating synthetic data for {symbol}")

        # 生成3年的模擬數據
        dates = pd.date_range(end = datetime.now(), periods = 756, freq="D")  # 3年交易日
        np.random.seed(42)

        # 模擬股價走勢
        initial_price = 100
        returns = np.random.normal(0.0005, 0.02, len(dates))  # 日回報
        prices = [initial_price]

        for ret in returns[1:]:
            new_price = prices[-1] * (1 + ret)
            prices.append(max(new_price, 1))  # 確保價格為正

        prices = np.array(prices[: len(dates)])

        # 生成OHLCV數據
        df = pd.DataFrame(
            {
                "open": prices * (1 + np.random.normal(0, 0.005, len(dates))),
                "high": prices * (1 + np.abs(np.random.normal(0, 0.01, len(dates)))),
                "low": prices * (1 - np.abs(np.random.normal(0, 0.01, len(dates)))),
                "close": prices,
                "volume": np.random.randint(100000, 10000000, len(dates)),
            },
            index = dates,
        )

        return df

    def _split_data(
        self, data: pd.DataFrame, validation_split: float
    ) -> Tuple[pd.DataFrame, Optional[pd.DataFrame]]:
        """分割訓練和驗證數據"""
        if validation_split <= 0 or len(data) < 100:
            return data, None

        split_point = int(len(data) * (1 - validation_split))
        train_data = data.iloc[:split_point]
        validation_data = data.iloc[split_point:]

        return train_data, validation_data

    def _get_best_backtest_result(
        self,
        optimization_results: Dict[str, Any],
        data: pd.DataFrame,
        strategy_name: str,
        symbol: str,
    ) -> Any:
        """獲取最佳回測結果"""
        best_params = optimization_results.get("best_parameters", {})
        if not best_params:
            return None

        try:
            engine = VectorBTEngine()
            result = engine.backtest_strategy(
                data = data, strategy = strategy_name, parameters = best_params, symbol = symbol
            )
            return result
        except Exception as e:
            logger.error(f"Failed to get best backtest result: {e}")
            return None

    def _get_all_backtest_results(
        self,
        optimization_results: Dict[str, Any],
        data: pd.DataFrame,
        strategy_name: str,
        symbol: str,
    ) -> List[Any]:
        """獲取所有回測結果（用於過擬合分析）"""
        all_results = []
        top_results = optimization_results.get("top_results", [])[:50]  # 限制數量

        for result_info in top_results:
            try:
                params = result_info.get("parameters", {})
                if params:
                    engine = VectorBTEngine()
                    result = engine.backtest_strategy(
                        data = data,
                        strategy = strategy_name,
                        parameters = params,
                        symbol = symbol,
                    )
                    all_results.append(result)
            except Exception as e:
                logger.warning(
                    f"Failed to get backtest result for params {params}: {e}"
                )
                continue

        return all_results

    def _analyze_parameter_importance(
        self, optimization_results: Dict[str, Any]
    ) -> Dict[str, float]:
        """分析參數重要性"""
        # 簡化實現 - 實際需要更複雜的統計分析
        top_results = optimization_results.get("top_results", [])[:100]

        if not top_results:
            return {}

        # 統計參數出現頻率
        param_frequency = {}
        param_importance = {}

        for result in top_results:
            params = result.get("parameters", {})
            for param_name, param_value in params.items():
                if param_name not in param_frequency:
                    param_frequency[param_name] = {}
                if param_value not in param_frequency[param_name]:
                    param_frequency[param_name][param_value] = 0
                param_frequency[param_name][param_value] += 1

        # 計算參數重要性（基於值的分佈）
        for param_name, value_counts in param_frequency.items():
            # 使用熵來衡量參數的重要性
            total_count = sum(value_counts.values())
            entropy = -sum(
                (count / total_count) * np.log2(count / total_count)
                for count in value_counts.values()
            )
            param_importance[param_name] = entropy

        # 標準化到0 - 1
        if param_importance:
            max_importance = max(param_importance.values())
            if max_importance > 0:
                param_importance = {
                    k: v / max_importance for k, v in param_importance.items()
                }

        return param_importance

    def _calculate_challenge_grade(
        self,
        combinations_per_second: float,
        parallel_efficiency: float,
        target_combinations: int,
    ) -> Dict[str, Any]:
        """計算百萬參數挑戰等級"""
        performance_score = 0

        # 性能得分（每秒組合數）
        if combinations_per_second >= 1000:
            performance_score += 40
        elif combinations_per_second >= 500:
            performance_score += 30
        elif combinations_per_second >= 200:
            performance_score += 20
        elif combinations_per_second >= 100:
            performance_score += 10

        # 效率得分
        if parallel_efficiency >= 80:
            performance_score += 30
        elif parallel_efficiency >= 60:
            performance_score += 20
        elif parallel_efficiency >= 40:
            performance_score += 10

        # 規模得分
        if target_combinations >= 1000000:
            performance_score += 30
        elif target_combinations >= 500000:
            performance_score += 20
        elif target_combinations >= 100000:
            performance_score += 10

        # 等級評定
        if performance_score >= 90:
            grade = "S+ (EXCEPTIONAL)"
            description = "世界級性能表現"
        elif performance_score >= 80:
            grade = "S (OUTSTANDING)"
            description = "卓越性能表現"
        elif performance_score >= 70:
            grade = "A+ (EXCELLENT)"
            description = "優秀性能表現"
        elif performance_score >= 60:
            grade = "A (VERY GOOD)"
            description = "良好性能表現"
        elif performance_score >= 50:
            grade = "B+ (GOOD)"
            description = "不錯的性能表現"
        elif performance_score >= 40:
            grade = "B (AVERAGE)"
            description = "平均性能表現"
        else:
            grade = "C (NEEDS IMPROVEMENT)"
            description = "性能有待提升"

        return {
            "grade": grade,
            "description": description,
            "performance_score": performance_score,
            "combinations_per_second": combinations_per_second,
            "parallel_efficiency": parallel_efficiency,
            "target_combinations": target_combinations,
        }

    def _save_optimization_results(
        self, strategy_name: str, symbol: str, results: Dict[str, Any]
    ):
        """保存優化結果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{strategy_name}_{symbol}_{timestamp}.json"
        filepath = os.path.join(self.results_dir, filename)

        try:
            with open(filepath, "w", encoding="utf - 8") as f:
                json.dump(results, f, indent = 2, ensure_ascii = False, default = str)
            logger.info(f"Optimization results saved to: {filepath}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")

    def _save_multi_strategy_results(self, symbol: str, results: Dict[str, Any]):
        """保存多策略優化結果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"multi_strategy_{symbol}_{timestamp}.json"
        filepath = os.path.join(self.results_dir, filename)

        try:
            with open(filepath, "w", encoding="utf - 8") as f:
                json.dump(results, f, indent = 2, ensure_ascii = False, default = str)
            logger.info(f"Multi - strategy results saved to: {filepath}")
        except Exception as e:
            logger.error(f"Failed to save multi - strategy results: {e}")

    def _generate_html_report(
        self, strategy_name: str, symbol: str, results: Dict[str, Any]
    ):
        """生成HTML報告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{strategy_name}_{symbol}_{timestamp}.html"
        filepath = os.path.join(self.results_dir, filename)

        try:
            html_content = self._create_html_report_content(results)
            with open(filepath, "w", encoding="utf - 8") as f:
                f.write(html_content)
            logger.info(f"HTML report generated: {filepath}")
        except Exception as e:
            logger.error(f"Failed to generate HTML report: {e}")

    def _create_html_report_content(self, results: Dict[str, Any]) -> str:
        """創建HTML報告內容"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>大規模參數優化報告</title>
            <meta charset="utf - 8">
            <style>
                body { font - family: Arial, sans - serif; margin: 40px; }
                .header { background - color: #f0f0f0; padding: 20px; border - radius: 5px; }
                .section { margin: 20px 0; padding: 15px; border - left: 4px solid #007cba; }
                .metric { display: inline - block; margin: 10px; padding: 10px; background - color: #f9f9f9; border - radius: 3px; }
                table { width: 100%; border - collapse: collapse; margin: 10px 0; }
                th, td { border: 1px solid #ddd; padding: 8px; text - align: left; }
                th { background - color: #f2f2f2; }
                .excellent { color: #28a745; }
                .good { color: #17a2b8; }
                .average { color: #ffc107; }
                .poor { color: #dc3545; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚀 大規模參數優化報告</h1>
                <p><strong>策略:</strong> {strategy}</p>
                <p><strong>股票:</strong> {symbol}</p>
                <p><strong>生成時間:</strong> {timestamp}</p>
            </div>

            <div class="section">
                <h2>📊 優化摘要</h2>
                <div class="metric"><strong>總組合數:</strong> {total_combinations:,}</div>
                <div class="metric"><strong>成功組合數:</strong> {successful_combinations:,}</div>
                <div class="metric"><strong>執行時間:</strong> {execution_time:.2f}秒</div>
                <div class="metric"><strong>處理速度:</strong> {combinations_per_second:.1f} 組合 / 秒</div>
            </div>

            <div class="section">
                <h2>🏆 最佳策略表現</h2>
                <div class="metric"><strong>最佳Sharpe比率:</strong> {best_sharpe:.3f}</div>
                <div class="metric"><strong>總回報:</strong> {total_return:.2%}</div>
                <div class="metric"><strong>最大回撤:</strong> {max_drawdown:.2%}</div>
                <div class="metric"><strong>勝率:</strong> {win_rate:.1%}</div>
            </div>

            <div class="section">
                <h2>⚙️ 最佳參數</h2>
                {best_parameters_html}
            </div>

            <div class="section">
                <h2>🎯 綜合評分</h2>
                <div class="metric"><strong>總評分:</strong> {total_score}</div>
                <div class="metric"><strong>等級:</strong> {grade}</div>
                <div class="metric"><strong>建議:</strong> {recommendation}</div>
            </div>

            <div class="section">
                <h2>💻 系統性能</h2>
                <div class="metric"><strong>並行效率:</strong> {parallel_efficiency:.1f}%</div>
                <div class="metric"><strong>緩存命中率:</strong> {cache_hit_rate:.1f}%</div>
                <div class="metric"><strong>平均任務時間:</strong> {avg_task_time:.3f}秒</div>
            </div>

            {overfitting_section}

        </body>
        </html>
        """

        # 提取數據並填充模板
        optimization_summary = results.get("optimization_summary", {})
        best_strategy = results.get("best_strategy", {})
        performance_report = results.get("performance_report", {})
        system_performance = results.get("system_performance", {})

        # 生成參數HTML
        best_params = best_strategy.get("parameters", {})
        params_html = ""
        for param, value in best_params.items():
            params_html += (
                f'<div class="metric"><strong>{param}:</strong> {value}</div>'
            )

        # 過擬合分析部分
        overfitting_section = ""
        if results.get("overfitting_analysis"):
            overfitting = results["overfitting_analysis"]
            risk_level = overfitting.get("overfitting_assessment", {}).get(
                "risk_level", "UNKNOWN"
            )
            risk_score = overfitting.get("overfitting_assessment", {}).get(
                "overfitting_risk_score", 0
            )

            overfitting_section = f"""
            <div class="section">
                <h2>🔍 過擬合分析</h2>
                <div class="metric"><strong>過擬合風險:</strong> {risk_level}</div>
                <div class="metric"><strong>風險評分:</strong> {risk_score:.1f}</div>
                <div class="metric"><strong>樣本內外Sharpe衰減:</strong> {overfitting.get('sample_stability', {}).get('sharpe_decay', 0):.2%}</div>
            </div>
            """

        return html_template.format(
            strategy = optimization_summary.get("strategy_name", "Unknown"),
            symbol = optimization_summary.get("symbol", "Unknown"),
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_combinations = optimization_summary.get("actual_combinations", 0),
            successful_combinations = optimization_summary.get("actual_combinations", 0),
            execution_time = optimization_summary.get("execution_time", 0),
            combinations_per_second = system_performance.get("tasks_per_second", 0),
            best_sharpe = best_strategy.get("performance_metrics", {}).get(
                "sharpe_ratio", 0
            ),
            total_return = best_strategy.get("performance_metrics", {}).get(
                "total_return", 0
            ),
            max_drawdown = best_strategy.get("performance_metrics", {}).get(
                "max_drawdown", 0
            ),
            win_rate = best_strategy.get("performance_metrics", {}).get("win_rate", 0),
            best_parameters_html = params_html,
            total_score = performance_report.get("multi_objective_score", {}).get(
                "total_score", 0
            ),
            grade = performance_report.get("multi_objective_score", {}).get(
                "grade", "N / A"
            ),
            recommendation = performance_report.get("investment_recommendation", {}).get(
                "recommendation", "N / A"
            ),
            parallel_efficiency = system_performance.get("parallel_efficiency", 0),
            cache_hit_rate = system_performance.get("cache_hit_rate", 0),
            avg_task_time = system_performance.get("average_task_time", 0),
            overfitting_section = overfitting_section,
        )


# 全局實例
massive_optimizer = MassiveOptimizer()


# 便利函數
def run_massive_optimization(
    strategy: str, symbol: str, combinations: int = 10000, metric: str = "sharpe_ratio"
) -> Dict[str, Any]:
    """便利函數：運行大規模優化"""
    return massive_optimizer.optimize_single_strategy(
        strategy_name = strategy,
        symbol = symbol,
        max_combinations = combinations,
        optimization_metric = metric,
    )


def run_million_parameter_challenge(
    strategy: str, symbol: str, target_combinations: int = 1000000
) -> Dict[str, Any]:
    """便利函數：運行百萬參數挑戰"""
    return massive_optimizer.run_million_parameter_challenge(
        strategy_name = strategy, symbol = symbol, target_combinations = target_combinations
    )


if __name__ == "__main__":
    # 命令行入口
    parser = argparse.ArgumentParser(description="大規模參數優化系統")
    parser.add_argument("--strategy", type = str, required = True, help="策略名稱")
    parser.add_argument("--symbol", type = str, required = True, help="股票代碼")
    parser.add_argument("--combinations", type = int, default = 10000, help="參數組合數")
    parser.add_argument("--metric", type = str, default="sharpe_ratio", help="優化指標")
    parser.add_argument(
        "--million - challenge", action="store_true", help="運行百萬參數挑戰"
    )
    parser.add_argument(
        "--target - combinations", type = int, default = 1000000, help="百萬挑戰目標組合數"
    )

    args = parser.parse_args()

    # 設置日誌
    logging.basicConfig(
        level = logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    if args.million_challenge:
        # 運行百萬參數挑戰
        results = run_million_parameter_challenge(
            strategy = args.strategy,
            symbol = args.symbol,
            target_combinations = args.target_combinations,
        )
    else:
        # 常規大規模優化
        results = run_massive_optimization(
            strategy = args.strategy,
            symbol = args.symbol,
            combinations = args.combinations,
            metric = args.metric,
        )

    # 輸出結果摘要
    print("\n" + "=" * 80)
    print("🚀 大規模參數優化完成")
    print("=" * 80)

    if "error" in results:
        print(f"❌ 優化失敗: {results['error']}")
    else:
        if args.million_challenge:
            challenge_summary = results.get("challenge_summary", {})
            print(f"📊 挑戰結果:")
            print(f"   實際組合數: {challenge_summary.get('actual_combinations', 0):,}")
            print(
                f"   處理速度: {challenge_summary.get('combinations_per_second', 0):,.1f} 組合 / 秒"
            )
            print(
                f"   並行效率: {challenge_summary.get('parallel_efficiency_percent', 0):.1f}%"
            )
            print(
                f"   挑戰等級: {results.get('challenge_grade', {}).get('grade', 'N / A')}"
            )
        else:
            optimization_summary = results.get("optimization_summary", {})
            best_strategy = results.get("best_strategy", {})

            print(f"📊 優化摘要:")
            print(f"   策略: {args.strategy}")
            print(f"   股票: {args.symbol}")
            print(
                f"   測試組合數: {optimization_summary.get('actual_combinations', 0):,}"
            )
            print(f"   執行時間: {optimization_summary.get('execution_time', 0):.2f}秒")

            print(f"\n🏆 最佳策略表現:")
            best_metrics = best_strategy.get("performance_metrics", {})
            print(f"   Sharpe比率: {best_metrics.get('sharpe_ratio', 0):.3f}")
            print(f"   總回報: {best_metrics.get('total_return', 0):.2%}")
            print(f"   最大回撤: {best_metrics.get('max_drawdown', 0):.2%}")
            print(f"   勝率: {best_metrics.get('win_rate', 0):.1%}")

            print(f"\n⚙️ 最佳參數:")
            best_params = best_strategy.get("parameters", {})
            for param, value in best_params.items():
                print(f"   {param}: {value}")

            performance_report = results.get("performance_report", {})
            if performance_report:
                score_info = performance_report.get("multi_objective_score", {})
                print(
                    f"\n🎯 綜合評分: {score_info.get('total_score', 0):.1f} ({score_info.get('grade', 'N / A')})"
                )

                investment_info = performance_report.get(
                    "investment_recommendation", {}
                )
                if investment_info:
                    print(
                        f"💡 投資建議: {investment_info.get('recommendation', 'N / A')}"
                    )
                    print(
                        f"📊 建議倉位: {investment_info.get('allocation_suggestion', 'N / A')}"
                    )

    print("=" * 80)

#!/usr/bin/env python3
"""
Phase 4 參數優化集成系統
Parameter Optimization Integration System for Phase 4

專為互動式量化交易平台設計的高級參數優化模組
Advanced parameter optimization module designed for interactive quantitative trading platform

Features:
- 大規模參數優化 (Massive Parameter Optimization)
- 實時進度顯示 (Real-time Progress Display)
- 多策略並行優化 (Multi-strategy Parallel Optimization)
- 結果分析和可視化 (Result Analysis and Visualization)
- 最佳策略展示 (Best Strategy Showcase)
- GPU加速支持 (GPU Acceleration Support)
"""

import sys
import os
import time
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from concurrent.futures import ProcessPoolExecutor, as_completed, ThreadPoolExecutor
import multiprocessing as mp
import threading
import queue

# 數據處理
import pandas as pd
import numpy as np

# 嘗試導入可視化庫
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

try:
    from tabulate import tabulate
    TABULATE_AVAILABLE = True
except ImportError:
    TABULATE_AVAILABLE = False

# 導入項目模塊 - 修復導入路徑
project_root = Path(__file__).parent.parent.parent
simplified_system_path = project_root / "simplified_system" / "src"
sys.path.insert(0, str(simplified_system_path))

# 安全導入，避免相對導入錯誤
try:
    from backtest.vectorbt_engine import VectorBTEngine, BacktestResult
except ImportError as e:
    print(f"Warning: Cannot import VectorBTEngine: {e}")
    VectorBTEngine = None
    BacktestResult = None

try:
    from api.stock_api import get_hk_stock_data
except ImportError as e:
    print(f"Warning: Cannot import get_hk_stock_data: {e}")
    get_hk_stock_data = None

try:
    from indicators.core_indicators import CoreIndicators
except ImportError as e:
    print(f"Warning: Cannot import CoreIndicators: {e}")
    CoreIndicators = None

# 導入配置和依賴管理
utils_path = project_root / "src" / "utils"
sys.path.insert(0, str(utils_path))
try:
    from dependency_manager import DependencyManager
except ImportError:
    DependencyManager = None

# 配置管理器
try:
    from config_manager import ConfigManager
except ImportError:
    ConfigManager = None

logger = logging.getLogger(__name__)

@dataclass
class OptimizationConfig:
    """優化配置"""
    # 基本配置
    symbol: str = "0700.HK"
    duration: int = 252
    strategy: str = "RSI_MEAN_REVERSION"

    # 優化參數
    optimization_metric: str = "sharpe_ratio"  # sharpe_ratio, total_return, max_drawdown, calmar_ratio
    max_combinations: int = 1000
    use_gpu: bool = True
    parallel_cores: int = -1  # -1表示使用所有核心

    # 進度顯示
    show_progress: bool = True
    save_intermediate: bool = True
    output_dir: str = "optimization_results"

    # 高級選項
    use_vectorbt_opt: bool = True
    multi_objective: bool = False
    objectives: List[str] = None

    def __post_init__(self):
        if self.objectives is None:
            self.objectives = ["sharpe_ratio", "max_drawdown", "total_return"]
        if self.parallel_cores == -1:
            self.parallel_cores = mp.cpu_count()

@dataclass
class OptimizationResult:
    """優化結果"""
    # 基本信息
    symbol: str
    strategy: str
    optimization_config: OptimizationConfig

    # 優化統計
    total_combinations: int
    successful_combinations: int
    optimization_time: float

    # 最佳結果
    best_parameters: Dict[str, Any]
    best_performance: Dict[str, float]

    # 所有結果（前N個）
    top_results: List[Dict[str, Any]]

    # 性能統計
    performance_statistics: Dict[str, float]

    # 元數據
    timestamp: str
    optimization_method: str
    gpu_accelerated: bool

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return asdict(self)

class ProgressTracker:
    """進度追蹤器"""

    def __init__(self, total_tasks: int, show_progress: bool = True):
        self.total_tasks = total_tasks
        self.completed_tasks = 0
        self.start_time = time.time()
        self.show_progress = show_progress and TQDM_AVAILABLE
        self.progress_bar = None
        self.status_queue = queue.Queue()

        if self.show_progress:
            self.progress_bar = tqdm(
                total=total_tasks,
                desc="優化進度",
                unit="組合",
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]"
            )

    def update(self, increment: int = 1):
        """更新進度"""
        self.completed_tasks += increment
        if self.progress_bar:
            self.progress_bar.update(increment)

    def close(self):
        """關閉進度條"""
        if self.progress_bar:
            self.progress_bar.close()

    def get_status(self) -> Dict[str, Any]:
        """獲取當前狀態"""
        elapsed = time.time() - self.start_time
        progress_pct = (self.completed_tasks / self.total_tasks * 100) if self.total_tasks > 0 else 0

        # 估計剩餘時間
        if self.completed_tasks > 0:
            avg_time_per_task = elapsed / self.completed_tasks
            remaining_tasks = self.total_tasks - self.completed_tasks
            eta_seconds = avg_time_per_task * remaining_tasks
            eta = str(int(eta_seconds // 60)) + "m " + str(int(eta_seconds % 60)) + "s"
        else:
            eta = "N/A"

        return {
            "completed": self.completed_tasks,
            "total": self.total_tasks,
            "progress_pct": progress_pct,
            "elapsed_time": str(int(elapsed // 60)) + "m " + str(int(elapsed % 60)) + "s",
            "eta": eta,
            "tasks_per_second": self.completed_tasks / elapsed if elapsed > 0 else 0
        }

class ParameterOptimizer:
    """參數優化器主類"""

    def __init__(self, config: Optional[OptimizationConfig] = None):
        """
        初始化優化器

        Args:
            config: 優化配置
        """
        self.config = config or OptimizationConfig()

        # 初始化系統組件
        self._init_system_components()

        # 創建輸出目錄
        self.output_dir = Path(self.config.output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # 初始化優化引擎
        self._init_optimization_engine()

        logger.info(f"Parameter Optimizer initialized for {self.config.symbol}")

    def _init_system_components(self):
        """初始化系統組件"""
        try:
            # 配置管理器
            self.config_manager = ConfigManager()

            # 依賴管理器
            self.dependency_manager = DependencyManager()

            # 檢查GPU可用性
            self.gpu_available = (
                self.config.use_gpu and
                self.dependency_manager.gpu_available
            )

            # 檢查VectorBT可用性
            self.vectorbt_available = (
                self.dependency_manager.vectorbt_available
            )

            logger.info(f"GPU Available: {self.gpu_available}")
            logger.info(f"VectorBT Available: {self.vectorbt_available}")

        except Exception as e:
            logger.error(f"System components initialization failed: {e}")
            # 使用默認設置
            self.gpu_available = False
            self.vectorbt_available = False

    def _init_optimization_engine(self):
        """初始化優化引擎"""
        try:
            # VectorBT引擎配置
            backtest_config = {
                'initial_cash': 100000.0,
                'fees': 0.001,
                'slippage': 0.0005,
                'risk_free_rate': 0.03
            }

            self.vbt_engine = VectorBTEngine(
                use_gpu=self.gpu_available
            )

            logger.info("VectorBT engine initialized successfully")

        except Exception as e:
            logger.error(f"Optimization engine initialization failed: {e}")
            self.vbt_engine = None

    def get_parameter_ranges(self, strategy: str) -> Dict[str, Union[List, range]]:
        """
        獲取策略的參數範圍

        Args:
            strategy: 策略名稱

        Returns:
            參數範圍字典
        """
        parameter_ranges = {
            "RSI_MEAN_REVERSION": {
                'period': range(5, 51, 2),
                'oversold': [20, 25, 30, 35, 40],
                'overbought': [60, 65, 70, 75, 80]
            },
            "MACD_CROSSOVER": {
                'fast': range(5, 21, 2),
                'slow': range(21, 41, 3),
                'signal': range(5, 16, 2)
            },
            "BOLLINGER_BANDS": {
                'period': range(10, 31, 2),
                'std_dev': [1.5, 2.0, 2.5, 3.0]
            },
            "DUAL_MOVING_AVERAGE": {
                'short_period': range(5, 21, 2),
                'long_period': range(21, 61, 4)
            },
            "MOMENTUM_BREAKOUT": {
                'lookback': range(5, 31, 3),
                'threshold': [0.01, 0.015, 0.02, 0.025, 0.03]
            },
            "VOLATILITY_BREAKOUT": {
                'atr_period': range(10, 26, 2),
                'multiplier': [1.5, 2.0, 2.5, 3.0, 3.5]
            }
        }

        return parameter_ranges.get(strategy, {})

    def run_optimization(self,
                        symbol: Optional[str] = None,
                        strategy: Optional[str] = None,
                        param_ranges: Optional[Dict[str, Union[List, range]]] = None) -> OptimizationResult:
        """
        運行參數優化

        Args:
            symbol: 股票代碼
            strategy: 策略名稱
            param_ranges: 參數範圍

        Returns:
            優化結果
        """
        # 使用配置或傳入的參數
        symbol = symbol or self.config.symbol
        strategy = strategy or self.config.strategy
        param_ranges = param_ranges or self.get_parameter_ranges(strategy)

        logger.info(f"Starting optimization for {symbol} - {strategy}")

        # 獲取數據
        data = self._get_market_data(symbol, self.config.duration)
        if data is None or len(data) == 0:
            raise ValueError(f"Failed to get market data for {symbol}")

        # 執行優化
        if self.config.multi_objective:
            result = self._run_multi_objective_optimization(data, strategy, param_ranges, symbol)
        else:
            result = self._run_single_objective_optimization(data, strategy, param_ranges, symbol)

        # 保存結果
        self._save_results(result)

        logger.info("Optimization completed successfully")
        return result

    def _run_single_objective_optimization(self,
                                          data: pd.DataFrame,
                                          strategy: str,
                                          param_ranges: Dict[str, Union[List, range]],
                                          symbol: str) -> OptimizationResult:
        """運行單目標優化"""
        start_time = time.time()

        # 選擇優化方法
        if self.vectorbt_available and self.config.use_vectorbt_opt:
            optimization_result = self.vbt_engine.optimize_parameters(
                data=data,
                strategy=strategy,
                param_ranges=param_ranges,
                symbol=symbol,
                optimization_metric=self.config.optimization_metric,
                max_combinations=self.config.max_combinations,
                use_vectorbt_opt=True
            )
        else:
            optimization_result = self.vbt_engine.optimize_parameters(
                data=data,
                strategy=strategy,
                param_ranges=param_ranges,
                symbol=symbol,
                optimization_metric=self.config.optimization_metric,
                max_combinations=self.config.max_combinations,
                use_vectorbt_opt=False
            )

        optimization_time = time.time() - start_time

        # 轉換結果格式
        result = OptimizationResult(
            symbol=symbol,
            strategy=strategy,
            optimization_config=self.config,
            total_combinations=optimization_result.get('total_combinations', 0),
            successful_combinations=optimization_result.get('successful_combinations', 0),
            optimization_time=optimization_time,
            best_parameters=optimization_result.get('best_parameters', {}),
            best_performance=optimization_result.get('best_performance', {}),
            top_results=optimization_result.get('all_results', [])[:10],
            performance_statistics=optimization_result.get('performance_statistics', {}),
            timestamp=datetime.now().isoformat(),
            optimization_method=optimization_result.get('optimization_method', 'Unknown'),
            gpu_accelerated=self.gpu_available
        )

        return result

    def _run_multi_objective_optimization(self,
                                         data: pd.DataFrame,
                                         strategy: str,
                                         param_ranges: Dict[str, Union[List, range]],
                                         symbol: str) -> OptimizationResult:
        """運行多目標優化"""
        start_time = time.time()

        if self.vbt_engine:
            optimization_result = self.vbt_engine.multi_objective_optimize(
                data=data,
                strategy=strategy,
                param_ranges=param_ranges,
                symbol=symbol,
                objectives=self.config.objectives,
                use_vectorbt_opt=self.config.use_vectorbt_opt
            )
        else:
            # 降級到單目標優化
            logger.warning("Multi-objective optimization not available, falling back to single objective")
            return self._run_single_objective_optimization(data, strategy, param_ranges, symbol)

        optimization_time = time.time() - start_time

        # 處理多目標結果
        best_compromise = optimization_result.get('best_compromise', {})
        solution = best_compromise.get('solution', {})

        result = OptimizationResult(
            symbol=symbol,
            strategy=strategy,
            optimization_config=self.config,
            total_combinations=optimization_result.get('total_optimization_time', 0),  # 這裡需要調整
            successful_combinations=len(optimization_result.get('pareto_frontier', [])),
            optimization_time=optimization_time,
            best_parameters=solution.get('parameters', {}),
            best_performance=solution.get('objectives', {}),
            top_results=optimization_result.get('pareto_frontier', [])[:10],
            performance_statistics=best_compromise,
            timestamp=datetime.now().isoformat(),
            optimization_method=optimization_result.get('optimization_method', 'Multi-Objective'),
            gpu_accelerated=self.gpu_available
        )

        return result

    def _get_market_data(self, symbol: str, duration: int) -> Optional[pd.DataFrame]:
        """獲取市場數據"""
        try:
            # 首先嘗試從simplified_system獲取數據
            data = get_hk_stock_data(symbol, duration)

            if data is not None and len(data) > 0:
                logger.info(f"Successfully retrieved {len(data)} data points for {symbol}")
                return data
            else:
                logger.warning(f"No data retrieved from simplified_system for {symbol}")

                # 可以在這裡添加備用數據源
                return None

        except Exception as e:
            logger.error(f"Failed to get market data for {symbol}: {e}")
            return None

    def _save_results(self, result: OptimizationResult):
        """保存優化結果"""
        try:
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{result.symbol}_{result.strategy}_{timestamp}.json"
            filepath = self.output_dir / filename

            # 保存為JSON
            result_dict = result.to_dict()
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result_dict, f, ensure_ascii=False, indent=2, default=str)

            logger.info(f"Results saved to {filepath}")

            # 同時保存最新結果
            latest_filepath = self.output_dir / f"latest_{result.symbol}_{result.strategy}.json"
            with open(latest_filepath, 'w', encoding='utf-8') as f:
                json.dump(result_dict, f, ensure_ascii=False, indent=2, default=str)

        except Exception as e:
            logger.error(f"Failed to save results: {e}")

    def load_results(self, filepath: str) -> Optional[OptimizationResult]:
        """加載優化結果"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                result_dict = json.load(f)

            # 重構OptimizationConfig
            if 'optimization_config' in result_dict:
                config_dict = result_dict['optimization_config']
                config = OptimizationConfig(**config_dict)
                result_dict['optimization_config'] = config

            result = OptimizationResult(**result_dict)
            logger.info(f"Results loaded from {filepath}")
            return result

        except Exception as e:
            logger.error(f"Failed to load results from {filepath}: {e}")
            return None

    def display_results(self, result: OptimizationResult, detailed: bool = True):
        """顯示優化結果"""
        print(f"\n{'='*80}")
        print(f"🎯 參數優化結果報告 / PARAMETER OPTIMIZATION REPORT")
        print(f"{'='*80}")

        # 基本信息
        print(f"📊 股票代碼: {result.symbol}")
        print(f"🔧 策略名稱: {result.strategy}")
        print(f"⏱️  優化時間: {result.optimization_time:.2f}秒")
        print(f"🔢 測試組合: {result.successful_combinations}/{result.total_combinations}")
        print(f"🚀 加速方式: {'GPU' if result.gpu_accelerated else 'CPU'}")
        print(f"📅 優化時間: {result.timestamp}")

        # 最佳參數
        print(f"\n🏆 最佳參數組合:")
        if result.best_parameters:
            for param, value in result.best_parameters.items():
                print(f"  • {param}: {value}")
        else:
            print("  • 無可用參數")

        # 最佳性能
        print(f"\n📈 最佳性能指標:")
        if result.best_performance:
            for metric, value in result.best_performance.items():
                if metric in ['sharpe_ratio', 'sortino_ratio', 'calmar_ratio']:
                    print(f"  • {metric}: {value:.3f}")
                elif metric in ['total_return', 'max_drawdown', 'annual_return']:
                    print(f"  • {metric}: {value:.2%}")
                else:
                    print(f"  • {metric}: {value}")
        else:
            print("  • 無可用性能數據")

        if detailed:
            # 前5個結果
            print(f"\n🔝 前5個最佳結果:")
            if result.top_results and len(result.top_results) > 0:
                table_data = []
                headers = ["排名", "參數", f"{self.config.optimization_metric}"]

                for i, item in enumerate(result.top_results[:5], 1):
                    params_str = ", ".join([f"{k}={v}" for k, v in item.get('parameters', {}).items()])
                    metric_value = item.get('metric', 0)

                    if self.config.optimization_metric in ['sharpe_ratio', 'sortino_ratio', 'calmar_ratio']:
                        metric_str = f"{metric_value:.3f}"
                    elif self.config.optimization_metric in ['total_return', 'max_drawdown']:
                        metric_str = f"{metric_value:.2%}"
                    else:
                        metric_str = str(metric_value)

                    table_data.append([i, params_str, metric_str])

                if TABULATE_AVAILABLE:
                    print(tabulate(table_data, headers=headers, tablefmt="grid"))
                else:
                    for row in table_data:
                        print(f"  {row[0]}. {row[1]} -> {row[2]}")
            else:
                print("  • 無可用結果數據")

            # 性能統計
            print(f"\n📊 性能統計:")
            if result.performance_statistics:
                for stat, value in result.performance_statistics.items():
                    print(f"  • {stat}: {value:.4f}")
            else:
                print("  • 無可用統計數據")

        print(f"\n{'='*80}")

    def compare_strategies(self,
                          symbol: str,
                          strategies: List[str],
                          param_ranges: Optional[Dict[str, Dict[str, Union[List, range]]]] = None) -> Dict[str, OptimizationResult]:
        """
        比較多個策略的優化結果

        Args:
            symbol: 股票代碼
            strategies: 策略列表
            param_ranges: 每個策略的參數範圍

        Returns:
            策略比較結果
        """
        results = {}

        print(f"\n🔄 開始多策略比較優化...")
        print(f"股票: {symbol}")
        print(f"策略: {', '.join(strategies)}")

        for strategy in strategies:
            print(f"\n🔧 正在優化策略: {strategy}")

            # 獲取策略參數範圍
            strategy_params = None
            if param_ranges and strategy in param_ranges:
                strategy_params = param_ranges[strategy]
            else:
                strategy_params = self.get_parameter_ranges(strategy)

            try:
                result = self.run_optimization(symbol, strategy, strategy_params)
                results[strategy] = result

                # 顯示简要結果
                print(f"  ✅ 完成 - 最佳Sharpe: {result.best_performance.get('sharpe_ratio', 'N/A'):.3f}")

            except Exception as e:
                logger.error(f"Failed to optimize strategy {strategy}: {e}")
                print(f"  ❌ 失敗 - {str(e)}")

        # 顯示比較結果
        self._display_strategy_comparison(results)

        return results

    def _display_strategy_comparison(self, results: Dict[str, OptimizationResult]):
        """顯示策略比較結果"""
        print(f"\n{'='*80}")
        print(f"📊 策略比較結果 / STRATEGY COMPARISON RESULTS")
        print(f"{'='*80}")

        if not results:
            print("  • 無可用比較結果")
            return

        table_data = []
        headers = ["策略", "最佳Sharpe", "總回報", "最大回撤", "交易次數", "優化時間(秒)"]

        for strategy, result in results.items():
            perf = result.best_performance
            sharpe = perf.get('sharpe_ratio', 0)
            total_return = perf.get('total_return', 0)
            max_dd = perf.get('max_drawdown', 0)
            trades = perf.get('total_trades', 0)
            opt_time = result.optimization_time

            table_data.append([
                strategy,
                f"{sharpe:.3f}",
                f"{total_return:.2%}",
                f"{max_dd:.2%}",
                str(trades),
                f"{opt_time:.2f}"
            ])

        if TABULATE_AVAILABLE:
            print(tabulate(table_data, headers=headers, tablefmt="grid"))
        else:
            for row in table_data:
                print(f"  {' | '.join(row)}")

        # 找出最佳策略
        best_strategy = max(results.items(), key=lambda x: x[1].best_performance.get('sharpe_ratio', 0))
        print(f"\n🏆 最佳策略: {best_strategy[0]} (Sharpe: {best_strategy[1].best_performance.get('sharpe_ratio', 0):.3f})")
        print(f"{'='*80}")

# 便利函數
def quick_optimize(symbol: str = "0700.HK",
                  strategy: str = "RSI_MEAN_REVERSION",
                  max_combinations: int = 500) -> OptimizationResult:
    """
    快速優化便利函數

    Args:
        symbol: 股票代碼
        strategy: 策略名稱
        max_combinations: 最大組合數

    Returns:
        優化結果
    """
    config = OptimizationConfig(
        symbol=symbol,
        strategy=strategy,
        max_combinations=max_combinations,
        show_progress=True,
        save_intermediate=True
    )

    optimizer = ParameterOptimizer(config)
    result = optimizer.run_optimization()
    optimizer.display_results(result)

    return result

def compare_all_strategies(symbol: str = "0700.HK") -> Dict[str, OptimizationResult]:
    """
    比較所有策略便利函數

    Args:
        symbol: 股票代碼

    Returns:
        策略比較結果
    """
    strategies = [
        "RSI_MEAN_REVERSION",
        "MACD_CROSSOVER",
        "BOLLINGER_BANDS",
        "DUAL_MOVING_AVERAGE",
        "MOMENTUM_BREAKOUT",
        "VOLATILITY_BREAKOUT"
    ]

    optimizer = ParameterOptimizer()
    return optimizer.compare_strategies(symbol, strategies)
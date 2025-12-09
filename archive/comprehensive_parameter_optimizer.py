#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
0700.HK 0-300全參數範圍綜合優化引擎
Comprehensive Parameter Optimization Engine for 0-300 Range

實現完整的0-300參數空間搜索，發現最優交易策略組合
Implements complete 0-300 parameter space search to discover optimal trading strategy combinations
"""

import numpy as np
import pandas as pd
import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
import time
import concurrent.futures
from itertools import product
import asyncio

# 導入我們的核心模塊
from simplified_system.src.backtest.vectorbt_engine import VectorBTEngine, BacktestResult
from simplified_system.src.indicators.gpu_indicators import GPUTechnicalIndicators
from simplified_system.src.utils.gpu_detector import get_gpu_environment
from simplified_system.src.api.government_data import GovernmentDataAPI
from simplified_system.src.api.stock_api import get_hk_stock_data

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ParameterSpace:
    """參數空間定義"""
    strategy_type: str
    parameters: Dict[str, List[int]]
    total_combinations: int = field(init=False)

    def __post_init__(self):
        # 計算總組合數
        self.total_combinations = 1
        for param_values in self.parameters.values():
            self.total_combinations *= len(param_values)

@dataclass
class OptimizationConfig:
    """優化配置"""
    # 搜索配置
    max_workers: int = 32  # 並行工作線程數
    batch_size: int = 1000  # 批處理大小
    early_stopping_patience: int = 50  # 早停耐心值
    early_stopping_threshold: float = 0.001  # 早停閾值

    # 目標函數權重
    sharpe_weight: float = 0.4
    calmar_weight: float = 0.3
    win_rate_weight: float = 0.2
    drawdown_control_weight: float = 0.1

    # 篩選標準
    min_sharpe_ratio: float = 1.0
    max_max_drawdown: float = 0.25  # 25%
    min_win_rate: float = 0.45  # 45%

    # GPU配置
    use_gpu: bool = True
    gpu_memory_limit: float = 0.8  # GPU內存使用限制

@dataclass
class OptimizationResult:
    """優化結果"""
    timestamp: str
    strategy_type: str
    total_combinations: int
    successful_combinations: int
    optimization_time: float

    # 最優參數
    top_parameters: List[Dict[str, Any]]
    performance_metrics: List[Dict[str, float]]

    # 統計信息
    performance_statistics: Dict[str, float]
    convergence_info: Optional[Dict[str, Any]] = None

    # GPU信息
    gpu_info: Optional[Dict[str, Any]] = None

class ComprehensiveParameterOptimizer:
    """
    0-300全參數範圍綜合優化引擎

    實現完整的參數空間搜索，支持：
    - HIBOR-RSI策略: 528,000個參數組合
    - Monetary-MACD策略: 345,000個參數組合
    - GPU加速並行處理
    - 多維性能評估
    - 智能早停機制
    """

    def __init__(self, config: Optional[OptimizationConfig] = None):
        """
        初始化綜合參數優化器

        Args:
            config: 優化配置
        """
        self.config = config or OptimizationConfig()

        # 初始化核心組件
        self.vectorbt_engine = VectorBTEngine(use_gpu=self.config.use_gpu)
        self.gpu_indicators = GPUTechnicalIndicators(use_gpu=self.config.use_gpu) if self.config.use_gpu else None
        self.gpu_env = get_gpu_environment()

        # 性能統計
        self.optimization_stats = {
            'total_optimizations': 0,
            'total_combinations_tested': 0,
            'total_execution_time': 0.0,
            'best_sharpe_found': 0.0,
            'gpu_acceleration_used': False
        }

        # 早停機制狀態
        self.early_stopping_counter = 0
        self.last_best_score = 0.0

        logger.info(f"Comprehensive Parameter Optimizer initialized")
        logger.info(f"GPU Available: {self.gpu_env.is_gpu_available()}")
        logger.info(f"Max Workers: {self.config.max_workers}")

    def define_parameter_spaces(self) -> Dict[str, ParameterSpace]:
        """
        定義完整的0-300參數空間

        Returns:
            參數空間字典
        """
        logger.info("Defining comprehensive 0-300 parameter spaces...")

        # HIBOR-RSI策略參數空間
        hibor_rsi_params = {
            'rsi_period': list(range(1, 301)),        # RSI週期: 1-300
            'rsi_oversold': list(range(10, 50)),       # RSI超賣: 10-49
            'rsi_overbought': list(range(51, 95))      # RSI超買: 51-94
        }

        # Monetary-MACD策略參數空間
        monetary_macd_params = {
            'macd_fast': list(range(5, 51)),           # MACD快線: 5-50
            'macd_slow': list(range(51, 301)),         # MACD慢線: 51-300
            'macd_signal': list(range(1, 31))          # MACD信號: 1-30
        }

        parameter_spaces = {
            'HIBOR_RSI': ParameterSpace('HIBOR_RSI', hibor_rsi_params),
            'MONETARY_MACD': ParameterSpace('MONETARY_MACD', monetary_macd_params)
        }

        # 記錄參數空間統計
        for strategy, space in parameter_spaces.items():
            logger.info(f"{strategy}: {space.total_combinations:,} parameter combinations")

        return parameter_spaces

    def validate_parameter_combination(self, params: Dict[str, Any], strategy_type: str) -> bool:
        """
        驗證參數組合的有效性

        Args:
            params: 參數字典
            strategy_type: 策略類型

        Returns:
            是否有效
        """
        if strategy_type == 'HIBOR_RSI':
            period = params.get('rsi_period', 14)
            oversold = params.get('rsi_oversold', 30)
            overbought = params.get('rsi_overbought', 70)

            # 驗證邏輯關係
            if not (1 <= period <= 300):
                return False
            if not (10 <= oversold <= 49):
                return False
            if not (51 <= overbought <= 94):
                return False
            if oversold >= overbought:
                return False
            return True

        elif strategy_type == 'MONETARY_MACD':
            fast = params.get('macd_fast', 12)
            slow = params.get('macd_slow', 26)
            signal = params.get('macd_signal', 9)

            # 驗證邏輯關係
            if not (5 <= fast <= 50):
                return False
            if not (51 <= slow <= 300):
                return False
            if not (1 <= signal <= 30):
                return False
            if fast >= slow:
                return False
            return True

        return False

    def calculate_composite_score(self, result: BacktestResult) -> float:
        """
        計算綜合評分（多目標優化）

        Args:
            result: 回測結果

        Returns:
            綜合評分
        """
        # 標準化各項指標到0-1範圍
        sharpe_score = min(max(result.sharpe_ratio / 3.0, 0), 1)  # 假設Sharpe最大為3
        calmar_score = min(max(result.calmar_ratio / 2.0, 0), 1)  # 假設Calmar最大為2
        win_rate_score = result.win_rate  # 已經是0-1範圍

        # 最大回撤控制（越小越好，轉換為0-1範圍）
        drawdown_score = max(0, 1 - (result.max_drawdown / self.config.max_max_drawdown))

        # 計算加權綜合評分
        composite_score = (
            sharpe_score * self.config.sharpe_weight +
            calmar_score * self.config.calmar_weight +
            win_rate_score * self.config.win_rate_weight +
            drawdown_score * self.config.drawdown_control_weight
        )

        return composite_score

    def should_early_stop(self, current_best_score: float) -> bool:
        """
        判斷是否應該早停

        Args:
            current_best_score: 當前最佳評分

        Returns:
            是否早停
        """
        score_improvement = current_best_score - self.last_best_score

        if score_improvement < self.config.early_stopping_threshold:
            self.early_stopping_counter += 1
        else:
            self.early_stopping_counter = 0
            self.last_best_score = current_best_score

        return self.early_stopping_counter >= self.config.early_stopping_patience

    def optimize_strategy(
        self,
        strategy_type: str,
        data: pd.DataFrame,
        government_data: Optional[pd.DataFrame] = None,
        max_combinations: Optional[int] = None
    ) -> OptimizationResult:
        """
        優化單個策略

        Args:
            strategy_type: 策略類型
            data: 股票數據
            government_data: 政府數據
            max_combinations: 最大測試組合數

        Returns:
            優化結果
        """
        logger.info(f"Starting comprehensive optimization for {strategy_type}")
        start_time = time.time()

        # 獲取參數空間
        parameter_spaces = self.define_parameter_spaces()
        if strategy_type not in parameter_spaces:
            raise ValueError(f"Unknown strategy type: {strategy_type}")

        param_space = parameter_spaces[strategy_type]

        # 限制搜索範圍（如果指定）
        if max_combinations and max_combinations < param_space.total_combinations:
            logger.info(f"Limiting search to {max_combinations:,} combinations out of {param_space.total_combinations:,}")

        # 重置早停機制
        self.early_stopping_counter = 0
        self.last_best_score = 0.0

        # 生成所有有效參數組合
        valid_combinations = self._generate_valid_combinations(param_space, max_combinations)
        total_combinations = len(valid_combinations)

        logger.info(f"Generated {total_combinations:,} valid parameter combinations")

        # 執行並行優化
        results = self._parallel_parameter_optimization(
            strategy_type, valid_combinations, data, government_data
        )

        # 計算綜合評分和排序
        scored_results = self._score_and_sort_results(results)

        # 提取Top N結果
        top_results = scored_results[:100]  # 前100個最優參數

        # 計算統計信息
        optimization_time = time.time() - start_time
        performance_stats = self._calculate_performance_statistics(scored_results)

        # 準備結果
        optimization_result = OptimizationResult(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            strategy_type=strategy_type,
            total_combinations=total_combinations,
            successful_combinations=len(results),
            optimization_time=optimization_time,
            top_parameters=[r['parameters'] for r in top_results],
            performance_metrics=[r['metrics'] for r in top_results],
            performance_statistics=performance_stats,
            gpu_info=self.gpu_env.get_system_info() if self.config.use_gpu else None
        )

        # 更新統計
        self._update_optimization_stats(optimization_result)

        logger.info(f"Optimization completed for {strategy_type}")
        logger.info(f"Best Sharpe: {top_results[0]['metrics']['sharpe_ratio']:.3f}")
        logger.info(f"Optimization speed: {len(results) / optimization_time:.1f} combos/sec")

        return optimization_result

    def _generate_valid_combinations(
        self,
        param_space: ParameterSpace,
        max_combinations: Optional[int]
    ) -> List[Dict[str, Any]]:
        """生成有效的參數組合"""
        logger.info("Generating valid parameter combinations...")

        # 生成所有組合
        param_names = list(param_space.parameters.keys())
        param_values = list(param_space.parameters.values())

        all_combinations = []
        valid_count = 0

        for combo in product(*param_values):
            params = dict(zip(param_names, combo))

            # 驗證參數組合
            if self.validate_parameter_combination(params, param_space.strategy_type):
                all_combinations.append(params)
                valid_count += 1

                # 限制組合數量
                if max_combinations and valid_count >= max_combinations:
                    break

        logger.info(f"Generated {valid_count:,} valid combinations out of {param_space.total_combinations:,} possible")
        return all_combinations

    def _parallel_parameter_optimization(
        self,
        strategy_type: str,
        combinations: List[Dict[str, Any]],
        data: pd.DataFrame,
        government_data: Optional[pd.DataFrame]
    ) -> List[BacktestResult]:
        """並行參數優化"""
        logger.info(f"Starting parallel optimization with {self.config.max_workers} workers")

        results = []
        batch_size = self.config.batch_size

        # 分批處理
        for batch_start in range(0, len(combinations), batch_size):
            batch_end = min(batch_start + batch_size, len(combinations))
            batch_combinations = combinations[batch_start:batch_end]

            logger.info(f"Processing batch {batch_start//batch_size + 1}: {len(batch_combinations)} combinations")

            # 並行處理當前批次
            batch_results = self._process_parameter_batch(
                strategy_type, batch_combinations, data, government_data
            )

            results.extend(batch_results)

            # 早停檢查
            if results:
                current_best = max(results, key=lambda r: self.calculate_composite_score(r))
                best_score = self.calculate_composite_score(current_best)

                if self.should_early_stop(best_score):
                    logger.info(f"Early stopping triggered after {len(results)} combinations")
                    break

        return results

    def _process_parameter_batch(
        self,
        strategy_type: str,
        combinations: List[Dict[str, Any]],
        data: pd.DataFrame,
        government_data: Optional[pd.DataFrame]
    ) -> List[BacktestResult]:
        """處理參數批次"""
        batch_results = []

        # 使用線程池並行處理
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(self.config.max_workers, len(combinations))) as executor:
            # 提交所有任務
            future_to_params = {
                executor.submit(self._test_single_combination, strategy_type, params, data, government_data): params
                for params in combinations
            }

            # 收集結果
            for future in concurrent.futures.as_completed(future_to_params):
                params = future_to_params[future]
                try:
                    result = future.result()
                    if result:  # 成功的結果
                        batch_results.append(result)
                except Exception as e:
                    logger.warning(f"Failed to test parameters {params}: {e}")
                    continue

        return batch_results

    def _test_single_combination(
        self,
        strategy_type: str,
        params: Dict[str, Any],
        data: pd.DataFrame,
        government_data: Optional[pd.DataFrame]
    ) -> Optional[BacktestResult]:
        """測試單個參數組合"""
        try:
            # 根據策略類型生成信號
            if strategy_type == 'HIBOR_RSI':
                return self._test_hibor_rsi_combination(params, data, government_data)
            elif strategy_type == 'MONETARY_MACD':
                return self._test_monetary_macd_combination(params, data, government_data)
            else:
                logger.warning(f"Unknown strategy type: {strategy_type}")
                return None
        except Exception as e:
            logger.warning(f"Error testing combination {params}: {e}")
            return None

    def _test_hibor_rsi_combination(
        self,
        params: Dict[str, Any],
        data: pd.DataFrame,
        government_data: Optional[pd.DataFrame]
    ) -> Optional[BacktestResult]:
        """測試HIBOR-RSI參數組合"""
        # 轉換參數格式
        strategy_params = {
            'period': params['rsi_period'],
            'oversold': params['rsi_oversold'],
            'overbought': params['rsi_overbought']
        }

        # 執行回測
        return self.vectorbt_engine.backtest_strategy(
            data=data,
            strategy="RSI_MEAN_REVERSION",
            parameters=strategy_params,
            symbol="0700.HK"
        )

    def _test_monetary_macd_combination(
        self,
        params: Dict[str, Any],
        data: pd.DataFrame,
        government_data: Optional[pd.DataFrame]
    ) -> Optional[BacktestResult]:
        """測試Monetary-MACD參數組合"""
        # 轉換參數格式
        strategy_params = {
            'fast': params['macd_fast'],
            'slow': params['macd_slow'],
            'signal': params['macd_signal']
        }

        # 執行回測
        return self.vectorbt_engine.backtest_strategy(
            data=data,
            strategy="MACD_CROSSOVER",
            parameters=strategy_params,
            symbol="0700.HK"
        )

    def _score_and_sort_results(self, results: List[BacktestResult]) -> List[Dict[str, Any]]:
        """為結果評分並排序"""
        scored_results = []

        for result in results:
            # 應用篩選標準
            if (result.sharpe_ratio < self.config.min_sharpe_ratio or
                abs(result.max_drawdown) > self.config.max_max_drawdown or
                result.win_rate < self.config.min_win_rate):
                continue

            # 計算綜合評分
            composite_score = self.calculate_composite_score(result)

            scored_results.append({
                'parameters': result.parameters,
                'metrics': {
                    'sharpe_ratio': result.sharpe_ratio,
                    'max_drawdown': result.max_drawdown,
                    'win_rate': result.win_rate,
                    'calmar_ratio': result.calmar_ratio,
                    'total_return': result.total_return,
                    'total_trades': result.total_trades,
                    'composite_score': composite_score
                },
                'backtest_result': result
            })

        # 按綜合評分排序
        scored_results.sort(key=lambda x: x['metrics']['composite_score'], reverse=True)

        return scored_results

    def _calculate_performance_statistics(self, scored_results: List[Dict[str, Any]]) -> Dict[str, float]:
        """計算性能統計"""
        if not scored_results:
            return {}

        sharpe_values = [r['metrics']['sharpe_ratio'] for r in scored_results]
        drawdown_values = [abs(r['metrics']['max_drawdown']) for r in scored_results]
        win_rate_values = [r['metrics']['win_rate'] for r in scored_results]
        composite_values = [r['metrics']['composite_score'] for r in scored_results]

        return {
            'total_successful': len(scored_results),
            'sharpe_mean': np.mean(sharpe_values),
            'sharpe_std': np.std(sharpe_values),
            'sharpe_max': np.max(sharpe_values),
            'drawdown_mean': np.mean(drawdown_values),
            'drawdown_std': np.std(drawdown_values),
            'drawdown_min': np.min(drawdown_values),
            'win_rate_mean': np.mean(win_rate_values),
            'composite_mean': np.mean(composite_values),
            'composite_max': np.max(composite_values)
        }

    def _update_optimization_stats(self, result: OptimizationResult) -> None:
        """更新優化統計"""
        self.optimization_stats['total_optimizations'] += 1
        self.optimization_stats['total_combinations_tested'] += result.successful_combinations
        self.optimization_stats['total_execution_time'] += result.optimization_time

        if result.performance_metrics:
            best_sharpe = max(m['sharpe_ratio'] for m in result.performance_metrics)
            self.optimization_stats['best_sharpe_found'] = max(
                self.optimization_stats['best_sharpe_found'], best_sharpe
            )

        self.optimization_stats['gpu_acceleration_used'] = self.config.use_gpu

    def get_optimization_summary(self) -> Dict[str, Any]:
        """獲取優化總結"""
        return {
            'optimization_statistics': self.optimization_stats,
            'configuration': {
                'max_workers': self.config.max_workers,
                'batch_size': self.config.batch_size,
                'use_gpu': self.config.use_gpu,
                'min_sharpe_ratio': self.config.min_sharpe_ratio,
                'max_max_drawdown': self.config.max_max_drawdown,
                'min_win_rate': self.config.min_win_rate
            },
            'gpu_environment': self.gpu_env.get_system_info() if self.config.use_gpu else None
        }

    def save_results(self, result: OptimizationResult, output_path: str) -> None:
        """保存優化結果"""
        output_file = Path(output_path)

        # 準備保存的數據
        save_data = {
            'timestamp': result.timestamp,
            'strategy_type': result.strategy_type,
            'optimization_summary': {
                'total_combinations': result.total_combinations,
                'successful_combinations': result.successful_combinations,
                'optimization_time': result.optimization_time,
                'success_rate': result.successful_combinations / result.total_combinations if result.total_combinations > 0 else 0
            },
            'top_parameters': result.top_parameters[:20],  # 只保存前20個
            'performance_metrics': result.performance_metrics[:20],
            'performance_statistics': result.performance_statistics,
            'configuration': self.get_optimization_summary(),
            'gpu_info': result.gpu_info
        }

        # 保存到JSON文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Results saved to: {output_file}")

    def run_comprehensive_optimization(
        self,
        symbol: str = "0700.HK",
        data_period: int = 365,
        max_combinations_per_strategy: Optional[int] = None
    ) -> Dict[str, OptimizationResult]:
        """
        運行全面的參數優化

        Args:
            symbol: 股票代碼
            data_period: 數據天數
            max_combinations_per_strategy: 每個策略的最大組合數

        Returns:
            所有策略的優化結果
        """
        logger.info(f"Starting comprehensive parameter optimization for {symbol}")

        # 獲取數據
        logger.info(f"Loading {data_period} days of stock data for {symbol}")
        stock_data = get_hk_stock_data(symbol, data_period)

        logger.info("Loading government data")
        try:
            # 獲取最新的政府數據
            gov_api = GovernmentDataAPI()
            gov_data = gov_api.get_hibor_data(100)
            if gov_data and len(gov_data) > 0:
                government_data = pd.DataFrame(gov_data)
            else:
                government_data = None
        except Exception as e:
            logger.warning(f"Failed to load government data: {e}")
            government_data = None

        # 運行所有策略的優化
        all_results = {}

        for strategy_type in ['HIBOR_RSI', 'MONETARY_MACD']:
            try:
                logger.info(f"Optimizing {strategy_type} strategy...")
                result = self.optimize_strategy(
                    strategy_type, stock_data, government_data, max_combinations_per_strategy
                )
                all_results[strategy_type] = result

                # 保存結果
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"comprehensive_optimization_{strategy_type}_{timestamp}.json"
                self.save_results(result, filename)

            except Exception as e:
                logger.error(f"Failed to optimize {strategy_type}: {e}")
                continue

        # 生成總結報告
        self._generate_summary_report(all_results)

        return all_results

    def _generate_summary_report(self, results: Dict[str, OptimizationResult]) -> None:
        """生成優化總結報告"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        report_lines = [
            "# 0700.HK 0-300全參數範圍綜合優化報告",
            f"生成時間: {timestamp}",
            "",
            "## 總體概況",
            ""
        ]

        for strategy_type, result in results.items():
            report_lines.extend([
                f"### {strategy_type} 策略",
                f"- 總參數組合: {result.total_combinations:,}",
                f"- 成功測試: {result.successful_combinations:,}",
                f"- 成功率: {result.successful_combinations/result.total_combinations*100:.2f}%",
                f"- 優化時間: {result.optimization_time:.2f}秒",
                f"- 處理速度: {result.successful_combinations/result.optimization_time:.1f} 組合/秒",
                ""
            ])

            if result.performance_metrics:
                best = result.performance_metrics[0]
                report_lines.extend([
                    f"- **最佳Sharpe比率**: {best['sharpe_ratio']:.3f}",
                    f"- **最佳最大回撤**: {best['max_drawdown']*100:.2f}%",
                    f"- **最佳勝率**: {best['win_rate']*100:.2f}%",
                    f"- **最佳綜合評分**: {best['composite_score']:.3f}",
                    ""
                ])

        # 添加最佳參數
        report_lines.extend(["## 最佳參數組合", ""])

        for strategy_type, result in results.items():
            if result.top_parameters:
                report_lines.append(f"### {strategy_type} Top 5 參數")
                for i, (params, metrics) in enumerate(zip(result.top_parameters[:5], result.performance_metrics[:5]), 1):
                    report_lines.append(f"{i}. Sharpe: {metrics['sharpe_ratio']:.3f}, 參數: {params}")
                report_lines.append("")

        # 保存報告
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"comprehensive_optimization_report_{timestamp_str}.md"

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))

        logger.info(f"Summary report saved to: {report_file}")
        print(f"\n🎯 優化完成！報告已保存至: {report_file}")

# 便利函數
def quick_optimize_0700(
    max_combinations: Optional[int] = 10000,
    use_gpu: bool = True
) -> Dict[str, OptimizationResult]:
    """
    快速優化0700.HK的參數

    Args:
        max_combinations: 每個策略的最大測試組合數
        use_gpu: 是否使用GPU加速

    Returns:
        優化結果
    """
    config = OptimizationConfig(
        max_workers=16,
        batch_size=500,
        use_gpu=use_gpu,
        min_sharpe_ratio=0.8,  # 稍微降低標準以獲得更多結果
        max_max_drawdown=0.3
    )

    optimizer = ComprehensiveParameterOptimizer(config)
    return optimizer.run_comprehensive_optimization(
        symbol="0700.HK",
        data_period=365,
        max_combinations_per_strategy=max_combinations
    )

if __name__ == "__main__":
    # 運行快速優化示例
    print("開始0700.HK全參數範圍綜合優化...")
    results = quick_optimize_0700(max_combinations=5000, use_gpu=True)

    for strategy, result in results.items():
        print(f"\n{strategy} 最優結果:")
        if result.performance_metrics:
            best = result.performance_metrics[0]
            print(f"  Sharpe比率: {best['sharpe_ratio']:.3f}")
            print(f"  最大回撤: {best['max_drawdown']*100:.2f}%")
            print(f"  勝率: {best['win_rate']*100:.2f}%")
            print(f"  最佳參數: {result.top_parameters[0]}")
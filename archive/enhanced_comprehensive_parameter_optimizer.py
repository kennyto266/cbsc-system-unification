#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增強版綜合參數優化器 - 整合所有OpenSpec增強功能
Enhanced Comprehensive Parameter Optimizer - Integrating All OpenSpec Enhancements

整合四個核心增強組件：
1. GPU內存管理器 - 動態批量大小和內存池管理
2. 智能搜索引擎 - 遺傳算法、貝葉斯優化、多臂老虎機
3. 實時性能監控器 - 動態監控和智能警報
4. 高級統計驗證器 - 交叉驗證和顯著性檢驗
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

# 導入現有系統
from comprehensive_parameter_optimizer import (
    ComprehensiveParameterOptimizer, OptimizationConfig, OptimizationResult,
    ParameterSpace, quick_optimize_0700
)
from simplified_system.src.backtest.vectorbt_engine import VectorBTEngine, BacktestResult
from simplified_system.src.utils.gpu_detector import get_gpu_environment
from simplified_system.src.api.government_data import GovernmentDataAPI
from simplified_system.src.api.stock_api import get_hk_stock_data

# 導入新的增強組件
from gpu_memory_manager import GPUMemoryManager, create_gpu_memory_manager
from intelligent_search_engine import IntelligentSearchEngine, SearchResult
from real_time_performance_monitor import RealTimePerformanceMonitor, AlertConfig
from advanced_statistical_validator import AdvancedStatisticalValidator, ValidationResult

# 簡單的警報數據結構
@dataclass
class SimpleAlert:
    """簡化的警報數據結構"""
    timestamp: float
    alert_type: str
    message: str
    severity: str
    metrics: Dict[str, Any] = field(default_factory=dict)

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class EnhancedOptimizationConfig(OptimizationConfig):
    """增強版優化配置"""
    # 搜索算法配置
    use_intelligent_search: bool = True
    search_algorithm_priority: List[str] = field(default_factory=lambda: ['genetic', 'bayesian', 'multi_armed_bandit'])
    max_iterations_per_algorithm: int = 100

    # 監控配置
    enable_real_time_monitoring: bool = True
    monitoring_interval: float = 5.0  # 秒
    enable_performance_alerts: bool = True

    # 統計驗證配置
    enable_statistical_validation: bool = True
    validation_folds: int = 5
    require_significance_testing: bool = True
    significance_level: float = 0.05

    # GPU內存管理配置
    enable_gpu_memory_management: bool = True
    gpu_memory_fraction: float = 0.8
    dynamic_batch_sizing: bool = True

@dataclass
class EnhancedOptimizationResult(OptimizationResult):
    """增強版優化結果"""
    # 搜索算法結果
    search_algorithm_performance: Dict[str, List[SearchResult]] = field(default_factory=dict)

    # 實時監控結果
    monitoring_summary: Optional[Dict[str, Any]] = None
    performance_alerts: List[SimpleAlert] = field(default_factory=list)

    # 統計驗證結果
    statistical_validation: Optional[ValidationResult] = None
    parameter_stability: Optional[Dict[str, Any]] = None

    # GPU內存管理結果
    memory_optimization_report: Optional[Dict[str, Any]] = None

class EnhancedComprehensiveParameterOptimizer(ComprehensiveParameterOptimizer):
    """
    增強版綜合參數優化器

    整合四個核心增強組件：
    1. GPU內存管理器 - 解決大規模搜索的內存限制
    2. 智能搜索引擎 - 高效參數搜索算法
    3. 實時性能監控器 - 動態性能監控和警報
    4. 高級統計驗證器 - 確保結果統計嚴謹性
    """

    def __init__(self, config: Optional[EnhancedOptimizationConfig] = None):
        """
        初始化增強版綜合參數優化器

        Args:
            config: 增強版優化配置
        """
        # 初始化基礎配置
        enhanced_config = config or EnhancedOptimizationConfig()
        super().__init__(enhanced_config)

        self.config = enhanced_config  # 類型轉換為增強版配置

        # 初始化四個增強組件
        self._initialize_enhanced_components()

        logger.info("Enhanced Comprehensive Parameter Optimizer initialized")
        logger.info(f"GPU Memory Management: {self.config.enable_gpu_memory_management}")
        logger.info(f"Intelligent Search: {self.config.use_intelligent_search}")
        logger.info(f"Real-time Monitoring: {self.config.enable_real_time_monitoring}")
        logger.info(f"Statistical Validation: {self.config.enable_statistical_validation}")

    def _initialize_enhanced_components(self) -> None:
        """初始化四個增強組件"""

        # 1. GPU內存管理器
        if self.config.enable_gpu_memory_management:
            self.gpu_memory_manager = create_gpu_memory_manager(
                memory_fraction=self.config.gpu_memory_fraction
            )
            logger.info("GPU Memory Manager initialized")
        else:
            self.gpu_memory_manager = None

        # 2. 智能搜索引擎 - 延遲初始化
        self.intelligent_search_engine = None
        if self.config.use_intelligent_search:
            logger.info("Intelligent Search Engine will be initialized on demand")
        else:
            logger.info("Intelligent Search Engine disabled")

        # 3. 實時性能監控器
        if self.config.enable_real_time_monitoring:
            alert_config = AlertConfig() if self.config.enable_performance_alerts else None
            self.performance_monitor = RealTimePerformanceMonitor(
                monitoring_interval=self.config.monitoring_interval,
                alert_config=alert_config
            )
            logger.info("Real-time Performance Monitor initialized")
        else:
            self.performance_monitor = None

        # 4. 高級統計驗證器
        if self.config.enable_statistical_validation:
            self.statistical_validator = AdvancedStatisticalValidator()
            logger.info("Advanced Statistical Validator initialized")
        else:
            self.statistical_validator = None

    def optimize_strategy_enhanced(
        self,
        strategy_type: str,
        data: pd.DataFrame,
        government_data: Optional[pd.DataFrame] = None,
        max_combinations: Optional[int] = None
    ) -> EnhancedOptimizationResult:
        """
        使用增強功能優化策略

        Args:
            strategy_type: 策略類型
            data: 股票數據
            government_data: 政府數據
            max_combinations: 最大測試組合數

        Returns:
            增強版優化結果
        """
        logger.info(f"Starting enhanced optimization for {strategy_type}")
        start_time = time.time()

        # 啟動實時監控
        if self.performance_monitor:
            self.performance_monitor.start_monitoring()

        try:
            # 獲取參數空間
            parameter_spaces = self.define_parameter_spaces()
            if strategy_type not in parameter_spaces:
                raise ValueError(f"Unknown strategy type: {strategy_type}")

            param_space = parameter_spaces[strategy_type]

            # 使用智能搜索引擎或傳統方法
            if self.intelligent_search_engine:
                search_results = self._intelligent_parameter_search(
                    strategy_type, param_space, data, government_data, max_combinations
                )
            else:
                # 回退到傳統方法
                traditional_result = super().optimize_strategy(
                    strategy_type, data, government_data, max_combinations
                )
                search_results = {'traditional': [SearchResult(
                    parameters=traditional_result.top_parameters[0] if traditional_result.top_parameters else {},
                    score=traditional_result.performance_metrics[0]['sharpe_ratio'] if traditional_result.performance_metrics else 0.0,
                    metrics=traditional_result.performance_metrics[0] if traditional_result.performance_metrics else {},
                    execution_time=traditional_result.optimization_time,
                    algorithm='traditional'
                )]}

            # 執行統計驗證
            validation_result = None
            parameter_stability = None
            if self.statistical_validator and search_results:
                best_result = max(
                    (r for results in search_results.values() for r in results),
                    key=lambda x: x.score
                )
                validation_result = self.statistical_validator.validate_parameters(
                    data, strategy_type, best_result.parameters
                )
                parameter_stability = self.statistical_validator.analyze_parameter_stability(
                    data, strategy_type, best_result.parameters
                )

            # 準備增強版結果
            optimization_time = time.time() - start_time

            # 獲取監控總結和警報
            monitoring_summary = None
            performance_alerts = []
            if self.performance_monitor:
                monitoring_summary = self.performance_monitor.get_performance_summary()
                performance_alerts = self.performance_monitor.get_active_alerts()

            # 獲取GPU內存優化報告
            memory_optimization_report = None
            if self.gpu_memory_manager:
                memory_optimization_report = self.gpu_memory_manager.get_optimization_report()

            # 構建增強版結果
            enhanced_result = self._build_enhanced_result(
                strategy_type, search_results, validation_result,
                monitoring_summary, performance_alerts,
                parameter_stability, memory_optimization_report, optimization_time
            )

            logger.info(f"Enhanced optimization completed for {strategy_type}")
            return enhanced_result

        finally:
            # 停止監控
            if self.performance_monitor:
                self.performance_monitor.stop_monitoring()

    def _intelligent_parameter_search(
        self,
        strategy_type: str,
        param_space: ParameterSpace,
        data: pd.DataFrame,
        government_data: Optional[pd.DataFrame],
        max_combinations: Optional[int]
    ) -> Dict[str, List[SearchResult]]:
        """使用智能搜索引擎進行參數搜索"""
        logger.info("Using intelligent search engine for parameter optimization")

        # 轉換參數空間格式
        param_ranges = {}
        for param_name, param_values in param_space.parameters.items():
            param_ranges[param_name] = (min(param_values), max(param_values))

        # 使用智能搜索引擎
        search_results = self.intelligent_search_engine.adaptive_search_strategy(
            problem_complexity='high',  # 0-300範圍是複雜問題
            max_iterations_per_algorithm=self.config.max_iterations_per_algorithm,
            param_ranges=param_ranges,
            data=data,
            strategy_func=lambda d, p: self._execute_backtest(strategy_type, d, p)
        )

        return search_results

    def _execute_backtest(self, strategy_type: str, data: pd.DataFrame, parameters: Dict[str, Any]) -> BacktestResult:
        """執行單次回測"""
        try:
            if strategy_type == 'HIBOR_RSI':
                strategy_params = {
                    'period': parameters.get('rsi_period', 14),
                    'oversold': parameters.get('rsi_oversold', 30),
                    'overbought': parameters.get('rsi_overbought', 70)
                }
                return self.vectorbt_engine.backtest_strategy(
                    data=data, strategy="RSI_MEAN_REVERSION",
                    parameters=strategy_params, symbol="0700.HK"
                )
            elif strategy_type == 'MONETARY_MACD':
                strategy_params = {
                    'fast': parameters.get('macd_fast', 12),
                    'slow': parameters.get('macd_slow', 26),
                    'signal': parameters.get('macd_signal', 9)
                }
                return self.vectorbt_engine.backtest_strategy(
                    data=data, strategy="MACD_CROSSOVER",
                    parameters=strategy_params, symbol="0700.HK"
                )
        except Exception as e:
            logger.warning(f"Backtest failed for parameters {parameters}: {e}")
            # 返回一個默認的失敗結果
            return BacktestResult(
                parameters=parameters,
                total_return=0.0,
                sharpe_ratio=0.0,
                max_drawdown=1.0,
                calmar_ratio=0.0,
                win_rate=0.0,
                total_trades=0
            )

    def _build_enhanced_result(
        self,
        strategy_type: str,
        search_results: Dict[str, List[SearchResult]],
        validation_result: Optional[ValidationResult],
        monitoring_summary: Optional[Dict[str, Any]],
        performance_alerts: List[SimpleAlert],
        parameter_stability: Optional[Dict[str, Any]],
        memory_optimization_report: Optional[Dict[str, Any]],
        optimization_time: float
    ) -> EnhancedOptimizationResult:
        """構建增強版優化結果"""

        # 提取最優參數和性能指標
        all_results = []
        for algorithm, results in search_results.items():
            for result in results:
                all_results.append(result)

        # 按評分排序
        all_results.sort(key=lambda x: x.score, reverse=True)

        top_parameters = [r.parameters for r in all_results[:100]]
        performance_metrics = []

        for r in all_results[:100]:
            metrics = r.metrics.copy()
            metrics['algorithm'] = r.algorithm
            metrics['execution_time'] = r.execution_time
            performance_metrics.append(metrics)

        # 計算統計信息
        scores = [r.score for r in all_results]
        performance_statistics = {
            'total_successful': len(all_results),
            'score_mean': np.mean(scores) if scores else 0,
            'score_std': np.std(scores) if scores else 0,
            'score_max': np.max(scores) if scores else 0,
            'algorithms_tested': list(search_results.keys()),
            'best_algorithm': all_results[0].algorithm if all_results else None
        }

        # 構建增強版結果
        enhanced_result = EnhancedOptimizationResult(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            strategy_type=strategy_type,
            total_combinations=sum(len(results) for results in search_results.values()),
            successful_combinations=len(all_results),
            optimization_time=optimization_time,
            top_parameters=top_parameters,
            performance_metrics=performance_metrics,
            performance_statistics=performance_statistics,
            search_algorithm_performance=search_results,
            monitoring_summary=monitoring_summary,
            performance_alerts=performance_alerts,
            statistical_validation=validation_result,
            parameter_stability=parameter_stability,
            memory_optimization_report=memory_optimization_report,
            gpu_info=self.gpu_env.get_system_info() if self.config.use_gpu else None
        )

        return enhanced_result

    def run_enhanced_comprehensive_optimization(
        self,
        symbol: str = "0700.HK",
        data_period: int = 365,
        max_combinations_per_strategy: Optional[int] = None
    ) -> Dict[str, EnhancedOptimizationResult]:
        """
        運行增強版綜合參數優化

        Args:
            symbol: 股票代碼
            data_period: 數據天數
            max_combinations_per_strategy: 每個策略的最大組合數

        Returns:
            所有策略的增強版優化結果
        """
        logger.info(f"Starting enhanced comprehensive parameter optimization for {symbol}")

        # 獲取數據
        logger.info(f"Loading {data_period} days of stock data for {symbol}")
        stock_data = get_hk_stock_data(symbol, data_period)

        logger.info("Loading government data")
        try:
            gov_api = GovernmentDataAPI()
            gov_data = gov_api.get_hibor_data(100)
            if gov_data and len(gov_data) > 0:
                government_data = pd.DataFrame(gov_data)
            else:
                government_data = None
        except Exception as e:
            logger.warning(f"Failed to load government data: {e}")
            government_data = None

        # 運行所有策略的增強優化
        all_results = {}

        for strategy_type in ['HIBOR_RSI', 'MONETARY_MACD']:
            try:
                logger.info(f"Enhanced optimizing {strategy_type} strategy...")
                result = self.optimize_strategy_enhanced(
                    strategy_type, stock_data, government_data, max_combinations_per_strategy
                )
                all_results[strategy_type] = result

                # 保存增強版結果
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"enhanced_optimization_{strategy_type}_{timestamp}.json"
                self.save_enhanced_results(result, filename)

            except Exception as e:
                logger.error(f"Failed to enhance optimize {strategy_type}: {e}")
                continue

        # 生成增強版總結報告
        self._generate_enhanced_summary_report(all_results)

        return all_results

    def save_enhanced_results(self, result: EnhancedOptimizationResult, output_path: str) -> None:
        """保存增強版優化結果"""
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

            # 增強功能結果
            'search_algorithm_performance': {
                algo: [
                    {
                        'parameters': r.parameters,
                        'score': r.score,
                        'metrics': r.metrics,
                        'execution_time': r.execution_time,
                        'algorithm': r.algorithm
                    } for r in results
                ] for algo, results in result.search_algorithm_performance.items()
            },

            'monitoring_summary': result.monitoring_summary,
            'performance_alerts': [
                {
                    'timestamp': alert.timestamp,
                    'alert_type': alert.alert_type,
                    'message': alert.message,
                    'severity': alert.severity,
                    'metrics': alert.metrics
                } for alert in result.performance_alerts
            ],

            'statistical_validation': None,
            'parameter_stability': result.parameter_stability,
            'memory_optimization_report': result.memory_optimization_report,
            'gpu_info': result.gpu_info
        }

        # 添加統計驗證結果
        if result.statistical_validation:
            save_data['statistical_validation'] = {
                'is_valid': result.statistical_validation.is_valid,
                'validation_score': result.statistical_validation.validation_score,
                'cross_validation_results': result.statistical_validation.cross_validation_results,
                'significance_test_results': result.statistical_validation.significance_test_results,
                'overfitting_risk': result.statistical_validation.overfitting_risk
            }

        # 保存到JSON文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Enhanced results saved to: {output_file}")

    def _generate_enhanced_summary_report(self, results: Dict[str, EnhancedOptimizationResult]) -> None:
        """生成增強版優化總結報告"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        report_lines = [
            "# 0700.HK 0-300全參數範圍增強綜合優化報告",
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
                    f"- **最佳算法**: {best.get('algorithm', 'N/A')}",
                    ""
                ])

            # 添加統計驗證結果
            if result.statistical_validation:
                validation = result.statistical_validation
                report_lines.extend([
                    "### 統計驗證結果",
                    f"- **驗證通過**: {'✅' if validation.is_valid else '❌'}",
                    f"- **驗證評分**: {validation.validation_score:.3f}",
                    f"- **過擬合風險**: {validation.overfitting_risk}",
                    ""
                ])

            # 添加搜索算法性能
            if result.search_algorithm_performance:
                report_lines.extend(["### 搜索算法性能", ""])
                for algorithm, algo_results in result.search_algorithm_performance.items():
                    if algo_results:
                        best_score = max(r.score for r in algo_results)
                        avg_score = np.mean([r.score for r in algo_results])
                        report_lines.extend([
                            f"- **{algorithm}**: 最佳 {best_score:.3f}, 平均 {avg_score:.3f}, 測試 {len(algo_results)} 組合"
                        ])
                report_lines.append("")

            # 添加性能警報
            if result.performance_alerts:
                report_lines.extend([
                    f"### 性能警報 ({len(result.performance_alerts)} 個)",
                    *[f"- {alert.severity}: {alert.message}" for alert in result.performance_alerts[:5]],
                    ""
                ])

        # 保存報告
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"enhanced_optimization_report_{timestamp_str}.md"

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))

        logger.info(f"Enhanced summary report saved to: {report_file}")
        print(f"\n🎯 增強優化完成！報告已保存至: {report_file}")

# 便利函數
def quick_enhanced_optimize_0700(
    max_combinations: Optional[int] = 5000,
    use_gpu: bool = True,
    enable_all_enhancements: bool = True
) -> Dict[str, EnhancedOptimizationResult]:
    """
    快速增強優化0700.HK的參數

    Args:
        max_combinations: 每個策略的最大測試組合數
        use_gpu: 是否使用GPU加速
        enable_all_enhancements: 是否啟用所有增強功能

    Returns:
        增強版優化結果
    """
    config = EnhancedOptimizationConfig(
        max_workers=16,
        batch_size=500,
        use_gpu=use_gpu,
        min_sharpe_ratio=0.8,
        max_max_drawdown=0.3,

        # 增強功能配置
        use_intelligent_search=enable_all_enhancements,
        enable_real_time_monitoring=enable_all_enhancements,
        enable_statistical_validation=enable_all_enhancements,
        enable_gpu_memory_management=enable_all_enhancements,

        # 搜索算法配置
        max_iterations_per_algorithm=50,  # 快速模式使用較少迭代
        monitoring_interval=2.0,  # 更頻繁的監控
        validation_folds=3  # 較少的驗證折疊以加快速度
    )

    optimizer = EnhancedComprehensiveParameterOptimizer(config)
    return optimizer.run_enhanced_comprehensive_optimization(
        symbol="0700.HK",
        data_period=365,
        max_combinations_per_strategy=max_combinations
    )

if __name__ == "__main__":
    # 運行快速增強優化示例
    print("開始0700.HK增強綜合參數優化...")
    results = quick_enhanced_optimize_0700(
        max_combinations=2000,
        use_gpu=True,
        enable_all_enhancements=True
    )

    for strategy, result in results.items():
        print(f"\n{strategy} 增強優化結果:")
        if result.performance_metrics:
            best = result.performance_metrics[0]
            print(f"  Sharpe比率: {best['sharpe_ratio']:.3f}")
            print(f"  最大回撤: {best['max_drawdown']*100:.2f}%")
            print(f"  勝率: {best['win_rate']*100:.2f}%")
            print(f"  最佳算法: {best.get('algorithm', 'N/A')}")
            print(f"  最佳參數: {result.top_parameters[0]}")

        if result.statistical_validation:
            print(f"  統計驗證: {'✅ 通過' if result.statistical_validation.is_valid else '❌ 失敗'}")

        if result.performance_alerts:
            print(f"  性能警報: {len(result.performance_alerts)} 個")
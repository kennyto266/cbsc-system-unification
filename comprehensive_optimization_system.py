#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
0700.HK 0-300全參數範圍綜合優化系統
Comprehensive 0-300 Parameter Optimization System for 0700.HK

完整的端到端參數優化系統，集成所有組件：
- GPU加速並行搜索
- 多維性能評估
- 參數穩定性驗證
- 自動化報告生成
- 生產部署準備
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
import warnings
warnings.filterwarnings('ignore')

# 導入我們的核心模塊
from comprehensive_parameter_optimizer import (
    ComprehensiveParameterOptimizer, OptimizationConfig, OptimizationResult
)
from gpu_parallel_search_engine import (
    GPUParallelSearchEngine, GPUSearchConfig
)
from multi_objective_performance_evaluator import (
    MultiObjectivePerformanceEvaluator, PerformanceMetrics
)
from parameter_stability_validator import (
    ParameterStabilityValidator, StabilityTestConfig
)
from simplified_system.src.api.stock_api import get_hk_stock_data
from simplified_system.src.api.government_data import get_latest_government_data

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('comprehensive_optimization.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class SystemConfig:
    """系統配置"""
    # 搜索配置
    max_combinations_per_strategy: int = 10000
    search_strategy: str = "hybrid"  # "grid", "random", "genetic", "hybrid"
    enable_gpu: bool = True
    max_workers: int = 16

    # 性能要求
    min_sharpe_ratio: float = 1.0
    max_drawdown: float = 0.25
    min_win_rate: float = 0.45

    # 驗證配置
    enable_stability_validation: bool = True
    stability_threshold: float = 70.0

    # 輸出配置
    generate_reports: bool = True
    save_intermediate_results: bool = True
    create_visualizations: bool = True

@dataclass
class OptimizationPipelineResult:
    """優化流水線結果"""
    timestamp: str
    symbol: str
    total_execution_time: float
    optimization_results: Dict[str, Any]
    performance_evaluation: Dict[str, Any]
    stability_validation: Dict[str, Any]
    final_recommendations: List[Dict[str, Any]]
    system_performance_metrics: Dict[str, Any]

class ComprehensiveOptimizationSystem:
    """
    0700.HK 0-300全參數範圍綜合優化系統

    完整的端到端優化流水線：
    1. GPU加速參數搜索
    2. 多維性能評估
    3. 參數穩定性驗證
    4. 綜合分析和推薦
    5. 報告生成和部署準備
    """

    def __init__(self, config: Optional[SystemConfig] = None):
        """
        初始化綜合優化系統

        Args:
            config: 系統配置
        """
        self.config = config or SystemConfig()

        # 初始化所有組件
        self._initialize_components()

        # 系統統計
        self.system_stats = {
            'total_optimizations': 0,
            'total_execution_time': 0.0,
            'successful_optimizations': 0,
            'average_execution_time': 0.0,
            'best_sharpe_found': 0.0,
            'gpu_utilization_time': 0.0
        }

        logger.info("Comprehensive Optimization System initialized")
        logger.info(f"GPU Enabled: {self.config.enable_gpu}")
        logger.info(f"Max Combinations per Strategy: {self.config.max_combinations_per_strategy}")
        logger.info(f"Search Strategy: {self.config.search_strategy}")

    def _initialize_components(self) -> None:
        """初始化所有系統組件"""
        # 參數優化器配置
        optimizer_config = OptimizationConfig(
            max_workers=self.config.max_workers,
            use_gpu=self.config.enable_gpu,
            min_sharpe_ratio=self.config.min_sharpe_ratio,
            max_max_drawdown=self.config.max_drawdown,
            min_win_rate=self.config.min_win_rate
        )

        # GPU搜索引擎配置
        gpu_config = GPUSearchConfig(
            use_gpu=self.config.enable_gpu,
            search_strategy=self.config.search_strategy,
            max_cpu_workers=self.config.max_workers
        )

        # 穩定性驗證配置
        stability_config = StabilityTestConfig()

        # 初始化組件
        self.optimizer = ComprehensiveParameterOptimizer(optimizer_config)
        self.gpu_engine = GPUParallelSearchEngine(gpu_config)
        self.performance_evaluator = MultiObjectivePerformanceEvaluator()
        self.stability_validator = ParameterStabilityValidator(stability_config)

        logger.info("All components initialized successfully")

    def run_comprehensive_optimization(
        self,
        symbol: str = "0700.HK",
        data_period: int = 365,
        strategies: List[str] = None
    ) -> OptimizationPipelineResult:
        """
        運行綜合優化流水線

        Args:
            symbol: 股票代碼
            data_period: 數據期間
            strategies: 要優化的策略列表

        Returns:
            優化流水線結果
        """
        logger.info(f"Starting comprehensive optimization for {symbol}")
        start_time = time.time()

        if strategies is None:
            strategies = ["HIBOR_RSI", "MONETARY_MACD"]

        # 階段1: 數據準備
        logger.info("Phase 1: Data preparation...")
        data, government_data = self._prepare_data(symbol, data_period)

        # 階段2: GPU加速參數搜索
        logger.info("Phase 2: GPU-accelerated parameter search...")
        optimization_results = self._run_parameter_optimization(
            strategies, data, government_data
        )

        # 階段3: 性能評估
        logger.info("Phase 3: Multi-objective performance evaluation...")
        performance_evaluation = self._evaluate_performance(
            optimization_results, data, government_data
        )

        # 階段4: 穩定性驗證
        stability_validation = {}
        if self.config.enable_stability_validation:
            logger.info("Phase 4: Parameter stability validation...")
            stability_validation = self._validate_stability(
                optimization_results, symbol
            )

        # 階段5: 綜合分析和推薦
        logger.info("Phase 5: Comprehensive analysis and recommendations...")
        final_recommendations = self._generate_final_recommendations(
            optimization_results, performance_evaluation, stability_validation
        )

        # 階段6: 系統性能指標
        system_metrics = self._calculate_system_metrics(
            time.time() - start_time, len(optimization_results)
        )

        # 更新系統統計
        self._update_system_stats(system_metrics)

        # 生成最終結果
        pipeline_result = OptimizationPipelineResult(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            symbol=symbol,
            total_execution_time=time.time() - start_time,
            optimization_results=optimization_results,
            performance_evaluation=performance_evaluation,
            stability_validation=stability_validation,
            final_recommendations=final_recommendations,
            system_performance_metrics=system_metrics
        )

        # 保存結果
        self._save_pipeline_results(pipeline_result)

        logger.info(f"Comprehensive optimization completed in {pipeline_result.total_execution_time:.2f} seconds")
        return pipeline_result

    def _prepare_data(self, symbol: str, data_period: int) -> Tuple[pd.DataFrame, Optional[pd.DataFrame]]:
        """準備數據"""
        logger.info(f"Loading {data_period} days of stock data for {symbol}")
        stock_data = get_hk_stock_data(symbol, data_period)

        logger.info("Loading government data...")
        try:
            gov_data = get_latest_government_data("hibor_rates", 100)
            if gov_data and gov_data.get('records'):
                government_data = pd.DataFrame(gov_data['records'])
                logger.info(f"Loaded {len(government_data)} government data records")
            else:
                government_data = None
                logger.warning("No government data available")
        except Exception as e:
            logger.warning(f"Failed to load government data: {e}")
            government_data = None

        return stock_data, government_data

    def _run_parameter_optimization(
        self,
        strategies: List[str],
        data: pd.DataFrame,
        government_data: Optional[pd.DataFrame]
    ) -> Dict[str, Any]:
        """運行參數優化"""
        optimization_results = {}

        for strategy in strategies:
            try:
                logger.info(f"Optimizing {strategy} strategy...")
                start_time = time.time()

                if self.config.enable_gpu:
                    # 使用GPU並行搜索
                    if strategy == "HIBOR_RSI":
                        result = self.gpu_engine.hibor_rsi_grid_search(
                            data, government_data, self.config.max_combinations_per_strategy
                        )
                    else:  # MONETARY_MACD
                        result = self.gpu_engine.monetary_macd_grid_search(
                            data, government_data, self.config.max_combinations_per_strategy
                        )
                else:
                    # 使用CPU優化器
                    result = self.optimizer.optimize_strategy(
                        strategy, data, government_data, self.config.max_combinations_per_strategy
                    )

                execution_time = time.time() - start_time
                result['execution_time'] = execution_time
                result['combinations_per_second'] = result.get('successful_combinations', 0) / execution_time

                optimization_results[strategy] = result

                logger.info(f"{strategy} optimization completed in {execution_time:.2f} seconds")
                logger.info(f"Successful combinations: {result.get('successful_combinations', 0)}")

                # 保存中間結果
                if self.config.save_intermediate_results:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    self._save_optimization_result(result, strategy, timestamp)

            except Exception as e:
                logger.error(f"Failed to optimize {strategy}: {e}")
                continue

        return optimization_results

    def _evaluate_performance(
        self,
        optimization_results: Dict[str, Any],
        data: pd.DataFrame,
        government_data: Optional[pd.DataFrame]
    ) -> Dict[str, Any]:
        """評估性能"""
        performance_evaluation = {}

        for strategy, result in optimization_results.items():
            try:
                logger.info(f"Evaluating performance for {strategy}...")

                # 提取最優參數
                top_results = result.get('top_results', [])
                if not top_results:
                    logger.warning(f"No top results found for {strategy}")
                    continue

                # 轉換為BacktestResult格式（模擬）
                backtest_results = []
                for i, top_result in enumerate(top_results[:20]):  # 評估前20個結果
                    # 這裡需要重新運行回測以獲取完整的BacktestResult
                    try:
                        strategy_params = top_result['parameters']
                        strategy_name = "RSI_MEAN_REVERSION" if strategy == "HIBOR_RSI" else "MACD_CROSSOVER"

                        backtest_result = self.vectorbt_engine.backtest_strategy(
                            data=data,
                            strategy=strategy_name,
                            parameters=strategy_params,
                            symbol="0700.HK"
                        )

                        backtest_results.append(backtest_result)

                    except Exception as e:
                        logger.warning(f"Failed to run backtest for result {i}: {e}")
                        continue

                if backtest_results:
                    # 評估批量策略
                    evaluated_strategies = self.performance_evaluator.evaluate_strategy_batch(
                        backtest_results, government_data
                    )

                    # 計算帕累托前沿
                    pareto_analysis = self.performance_evaluator.calculate_pareto_frontier(
                        evaluated_strategies
                    )

                    performance_evaluation[strategy] = {
                        'evaluated_strategies': evaluated_strategies,
                        'pareto_analysis': pareto_analysis,
                        'top_performers': sorted(
                            evaluated_strategies,
                            key=lambda x: x['composite_score'],
                            reverse=True
                        )[:10]
                    }

                    logger.info(f"Performance evaluation completed for {strategy}")
                    logger.info(f"Top performer Sharpe: {performance_evaluation[strategy]['top_performers'][0]['performance_metrics'].sharpe_ratio:.3f}")

            except Exception as e:
                logger.error(f"Failed to evaluate performance for {strategy}: {e}")
                continue

        return performance_evaluation

    def _validate_stability(
        self,
        optimization_results: Dict[str, Any],
        symbol: str
    ) -> Dict[str, Any]:
        """驗證參數穩定性"""
        stability_validation = {}

        for strategy, result in optimization_results.items():
            try:
                logger.info(f"Validating stability for {strategy}...")

                # 提取最優參數
                top_results = result.get('top_results', [])
                if not top_results:
                    continue

                # 取前5個最優參數進行穩定性驗證
                optimal_params = [r['parameters'] for r in top_results[:5]]

                # 運行穩定性驗證
                validation_result = self.stability_validator.validate_parameter_stability(
                    optimal_params, strategy, symbol
                )

                stability_validation[strategy] = validation_result

                # 記錄穩定參數數量
                stable_count = len(validation_result.get('stable_parameters', []))
                logger.info(f"Found {stable_count} stable parameter sets for {strategy}")

            except Exception as e:
                logger.error(f"Failed to validate stability for {strategy}: {e}")
                continue

        return stability_validation

    def _generate_final_recommendations(
        self,
        optimization_results: Dict[str, Any],
        performance_evaluation: Dict[str, Any],
        stability_validation: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成最終推薦"""
        logger.info("Generating final recommendations...")

        recommendations = []

        for strategy in optimization_results.keys():
            try:
                # 獲取性能評估結果
                perf_eval = performance_evaluation.get(strategy, {})
                top_performers = perf_eval.get('top_performers', [])

                # 獲取穩定性驗證結果
                stability_val = stability_validation.get(strategy, {})
                stable_params = stability_val.get('stable_parameters', [])

                if not top_performers:
                    continue

                # 找到既優秀又穩定的參數
                recommended_strategies = []
                for performer in top_performers[:10]:  # 檢查前10個
                    params = performer['parameters']
                    metrics = performer['performance_metrics']

                    # 檢查是否在穩定參數列表中
                    is_stable = any(
                        self._parameters_match(params, stable_param['parameter_set'])
                        for stable_param in stable_params
                    )

                    # 檢查是否滿足基本要求
                    meets_requirements = (
                        metrics.sharpe_ratio >= self.config.min_sharpe_ratio and
                        abs(metrics.max_drawdown) <= self.config.max_drawdown and
                        metrics.win_rate >= self.config.min_win_rate
                    )

                    if meets_requirements:
                        recommendation = {
                            'strategy_type': strategy,
                            'parameters': params,
                            'performance_metrics': {
                                'sharpe_ratio': metrics.sharpe_ratio,
                                'max_drawdown': metrics.max_drawdown,
                                'win_rate': metrics.win_rate,
                                'total_return': metrics.total_return,
                                'calmar_ratio': metrics.calmar_ratio,
                                'composite_score': performer['composite_score']
                            },
                            'is_stable': is_stable,
                            'stability_score': None,
                            'risk_level': performer['risk_assessment']['risk_level'],
                            'recommendation_strength': 'HIGH' if is_stable else 'MEDIUM'
                        }

                        # 添加穩定性評分
                        if is_stable:
                            stable_param = next(
                                (sp for sp in stable_params
                                 if self._parameters_match(params, sp['parameter_set'])),
                                None
                            )
                            if stable_param:
                                recommendation['stability_score'] = stable_param['overall_stability_score']

                        recommended_strategies.append(recommendation)

                # 按綜合評分排序
                recommended_strategies.sort(
                    key=lambda x: (
                        x['performance_metrics']['composite_score'],
                        x['stability_score'] or 0
                    ),
                    reverse=True
                )

                if recommended_strategies:
                    recommendations.extend(recommended_strategies[:3])  # 每個策略最多推薦3個

            except Exception as e:
                logger.error(f"Failed to generate recommendations for {strategy}: {e}")
                continue

        # 生成部署建議
        deployment_recommendations = self._generate_deployment_recommendations(recommendations)

        # 添加部署建議到推薦列表
        for i, rec in enumerate(recommendations):
            rec['deployment_recommendations'] = deployment_recommendations.get('general', [])
            if rec['recommendation_strength'] == 'HIGH':
                rec['deployment_recommendations'].extend(deployment_recommendations.get('high_confidence', []))

        return recommendations

    def _parameters_match(self, params1: Dict[str, Any], params2: Dict[str, Any]) -> bool:
        """檢查兩組參數是否匹配"""
        for key, value in params1.items():
            if key not in params2 or params2[key] != value:
                return False
        return True

    def _generate_deployment_recommendations(self, recommendations: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """生成部署建議"""
        general = [
            "實施實時監控系統，跟踪策略表現",
            "設置風險控制閾值，自動觸發止損",
            "建立定期參數重新優化機制",
            "實施多策略分散投資組合"
        ]

        high_confidence = [
            "可以開始小額實盤測試",
            "優先考慮生產環境部署",
            "建立完整的風險管理框架",
            "實施實時性能監控警報"
        ]

        return {
            'general': general,
            'high_confidence': high_confidence
        }

    def _calculate_system_metrics(
        self,
        execution_time: float,
        total_combinations: int
    ) -> Dict[str, Any]:
        """計算系統性能指標"""
        return {
            'execution_time': execution_time,
            'total_combinations_tested': total_combinations,
            'combinations_per_second': total_combinations / execution_time if execution_time > 0 else 0,
            'system_efficiency': 'HIGH' if execution_time < 300 else 'MEDIUM' if execution_time < 600 else 'LOW',
            'memory_usage': 'N/A',  # 可以添加內存使用監控
            'cpu_utilization': 'N/A',  # 可以添加CPU使用率監控
            'gpu_utilization': 'ENABLED' if self.config.enable_gpu else 'DISABLED'
        }

    def _update_system_stats(self, metrics: Dict[str, Any]) -> None:
        """更新系統統計"""
        self.system_stats['total_optimizations'] += 1
        self.system_stats['total_execution_time'] += metrics['execution_time']
        self.system_stats['successful_optimizations'] += 1
        self.system_stats['average_execution_time'] = (
            self.system_stats['total_execution_time'] / self.system_stats['total_optimizations']
        )

        if self.config.enable_gpu:
            self.system_stats['gpu_utilization_time'] += metrics['execution_time']

    def _save_pipeline_results(self, result: OptimizationPipelineResult) -> None:
        """保存流水線結果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = Path("comprehensive_optimization_results")
        output_dir.mkdir(exist_ok=True)

        # 保存主要結果
        main_file = output_dir / f"optimization_pipeline_{timestamp}.json"

        # 準備保存的數據（轉換為可序列化格式）
        save_data = {
            'timestamp': result.timestamp,
            'symbol': result.symbol,
            'total_execution_time': result.total_execution_time,
            'system_performance_metrics': result.system_performance_metrics,
            'final_recommendations': result.final_recommendations,
            'optimization_summary': {
                strategy: {
                    'total_combinations': opt_result.get('total_combinations', 0),
                    'successful_combinations': opt_result.get('successful_combinations', 0),
                    'execution_time': opt_result.get('execution_time', 0),
                    'top_sharpe': opt_result.get('top_results', [{}])[0].get('sharpe_ratio', 0) if opt_result.get('top_results') else 0
                }
                for strategy, opt_result in result.optimization_results.items()
            }
        }

        with open(main_file, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False, default=str)

        # 保存詳細結果
        if self.config.save_intermediate_results:
            detailed_file = output_dir / f"detailed_results_{timestamp}.json"
            with open(detailed_file, 'w', encoding='utf-8') as f:
                json.dump(result.__dict__, f, indent=2, ensure_ascii=False, default=str)

        # 生成報告
        if self.config.generate_reports:
            report_file = output_dir / f"optimization_report_{timestamp}.md"
            self._generate_optimization_report(result, report_file)

        logger.info(f"Pipeline results saved to: {output_dir}")

    def _generate_optimization_report(self, result: OptimizationPipelineResult, report_file: Path) -> None:
        """生成優化報告"""
        report_lines = [
            f"# 0700.HK 0-300全參數範圍綜合優化報告",
            f"生成時間: {result.timestamp}",
            f"執行時間: {result.total_execution_time:.2f}秒",
            "",
            "## 執行概況",
            f"- 股票代碼: {result.symbol}",
            f"- 系統效率: {result.system_performance_metrics['system_efficiency']}",
            f"- 測試組合數: {result.system_performance_metrics['total_combinations_tested']:,}",
            f"- 處理速度: {result.system_performance_metrics['combinations_per_second']:.1f} 組合/秒",
            f"- GPU加速: {result.system_performance_metrics['gpu_utilization']}",
            "",
        ]

        # 添加最優推薦
        if result.final_recommendations:
            report_lines.extend([
                "## 最優推薦策略",
                ""
            ])

            for i, rec in enumerate(result.final_recommendations[:5], 1):
                metrics = rec['performance_metrics']
                report_lines.extend([
                    f"### {i}. {rec['strategy_type']} - {rec['recommendation_strength']} CONFIDENCE",
                    f"- **參數**: {rec['parameters']}",
                    f"- **Sharpe比率**: {metrics['sharpe_ratio']:.3f}",
                    f"- **最大回撤**: {metrics['max_drawdown']*100:.2f}%",
                    f"- **勝率**: {metrics['win_rate']*100:.2f}%",
                    f"- **總回報**: {metrics['total_return']*100:.2f}%",
                    f"- **綜合評分**: {metrics['composite_score']:.2f}",
                    f"- **風險等級**: {rec['risk_level']}",
                    f"- **穩定性**: {'通過' if rec.get('is_stable') else '未驗證'}",
                    ""
                ])

                if rec.get('deployment_recommendations'):
                    report_lines.extend([
                        "**部署建議**:",
                        *[f"- {rec}" for rec in rec['deployment_recommendations']],
                        ""
                    ])

        # 添加系統性能分析
        report_lines.extend([
            "## 系統性能分析",
            "",
            f"- **總執行時間**: {result.total_execution_time:.2f}秒",
            f"- **平均處理速度**: {result.system_performance_metrics['combinations_per_second']:.1f} 組合/秒",
            f"- **系統效率評級**: {result.system_performance_metrics['system_efficiency']}",
            f"- **GPU加速狀態**: {result.system_performance_metrics['gpu_utilization']}",
            ""
        ])

        # 添加建議和下一步
        report_lines.extend([
            "## 建議和下一步",
            "",
            "### 立即行動",
            "1. 實施推薦的最優策略進行紙面交易測試",
            "2. 建立實時監控和警報系統",
            "3. 設置風險控制和止損機制",
            "",
            "### 中期改進",
            "1. 擴展到更多港股標的",
            "2. 實施多策略組合優化",
            "3. 建立機器學習參數調整系統",
            "",
            "### 長期目標",
            "1. 發展為完整的量化投資平台",
            "2. 集成更多數據源和信號源",
            "3. 實現自動化交易執行系統",
            ""
        ])

        report_content = '\n'.join(report_lines)

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)

        logger.info(f"Optimization report generated: {report_file}")

    def _save_optimization_result(self, result: Dict[str, Any], strategy: str, timestamp: str) -> None:
        """保存優化結果"""
        output_file = f"intermediate_optimization_{strategy}_{timestamp}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)

    def get_system_status(self) -> Dict[str, Any]:
        """獲取系統狀態"""
        return {
            'system_statistics': self.system_stats,
            'configuration': {
                'max_combinations_per_strategy': self.config.max_combinations_per_strategy,
                'search_strategy': self.config.search_strategy,
                'enable_gpu': self.config.enable_gpu,
                'max_workers': self.config.max_workers,
                'enable_stability_validation': self.config.enable_stability_validation,
                'generate_reports': self.config.generate_reports
            },
            'component_status': {
                'optimizer': 'READY',
                'gpu_engine': 'READY' if self.config.enable_gpu else 'DISABLED',
                'performance_evaluator': 'READY',
                'stability_validator': 'READY'
            }
        }

# 便利函數
def run_complete_optimization(
    symbol: str = "0700.HK",
    data_period: int = 365,
    max_combinations: int = 5000,
    enable_gpu: bool = True
) -> Dict[str, Any]:
    """
    運行完整的綜合優化

    Args:
        symbol: 股票代碼
        data_period: 數據期間
        max_combinations: 最大組合數
        enable_gpu: 是否啟用GPU

    Returns:
        優化結果
    """
    # 配置系統
    config = SystemConfig(
        max_combinations_per_strategy=max_combinations,
        enable_gpu=enable_gpu,
        enable_stability_validation=True,
        generate_reports=True
    )

    # 運行優化
    system = ComprehensiveOptimizationSystem(config)
    result = system.run_comprehensive_optimization(symbol, data_period)

    # 返回關鍵結果
    return {
        'execution_summary': {
            'symbol': result.symbol,
            'execution_time': result.total_execution_time,
            'total_combinations': result.system_performance_metrics['total_combinations_tested'],
            'processing_speed': result.system_performance_metrics['combinations_per_second']
        },
        'final_recommendations': result.final_recommendations,
        'system_performance': result.system_performance_metrics,
        'system_status': system.get_system_status()
    }

if __name__ == "__main__":
    # 運行完整優化示例
    print("開始0700.HK全參數範圍綜合優化系統...")
    print("這將執行完整的端到端優化流水線")
    print("包括：GPU參數搜索、性能評估、穩定性驗證")
    print("")

    # 運行優化
    result = run_complete_optimization(
        symbol="0700.HK",
        data_period=365,
        max_combinations=3000,  # 較小的數值用於演示
        enable_gpu=True
    )

    # 顯示結果
    print("\n🎯 優化完成！")
    print(f"執行時間: {result['execution_summary']['execution_time']:.2f}秒")
    print(f"測試組合數: {result['execution_summary']['total_combinations']:,}")
    print(f"處理速度: {result['execution_summary']['processing_speed']:.1f} 組合/秒")
    print(f"推薦策略數: {len(result['final_recommendations'])}")

    if result['final_recommendations']:
        print("\n🏆 最佳推薦策略:")
        best = result['final_recommendations'][0]
        print(f"策略: {best['strategy_type']}")
        print(f"參數: {best['parameters']}")
        print(f"Sharpe: {best['performance_metrics']['sharpe_ratio']:.3f}")
        print(f"回撤: {best['performance_metrics']['max_drawdown']*100:.2f}%")
        print(f"勝率: {best['performance_metrics']['win_rate']*100:.2f}%")
        print(f"信心等級: {best['recommendation_strength']}")

    print(f"\n📊 詳細報告已保存到 comprehensive_optimization_results/ 目錄")
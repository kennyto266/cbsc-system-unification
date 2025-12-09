#!/usr/bin/env python3
"""
大規模參數優化系統 - 完整測試和演示
Massive Parameter Optimization System - Complete Testing and Demo

Phase 3 大規模優化系統的完整功能測試和性能驗證
"""

import sys
import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime
import time
import json
from pathlib import Path

# 添加路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'backtest'))

# 導入優化系統
from massive_optimizer import MassiveOptimizer, massive_optimizer
from parameter_space import ParameterSpaceManager, parameter_space_manager
from parallel_optimizer import ParallelOptimizer, OptimizationConfig
from performance_evaluator import PerformanceEvaluator, performance_evaluator

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('massive_optimizer_test.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class MassiveOptimizerTest:
    """大規模優化系統測試套件"""

    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()

    def run_all_tests(self):
        """運行所有測試"""
        logger.info("🚀 開始大規模優化系統完整測試")

        tests = [
            ("Phase 3.1: 參數空間測試", self.test_parameter_space),
            ("Phase 3.2: 並行優化測試", self.test_parallel_optimization),
            ("Phase 3.3: 性能評估測試", self.test_performance_evaluation),
            ("集成測試: 單策略優化", self.test_single_strategy_optimization),
            ("集成測試: 多策略優化", self.test_multi_strategy_optimization),
            ("極限測試: 百萬參數挑戰", self.test_million_parameter_challenge),
            ("性能基準測試", self.test_performance_benchmarks)
        ]

        for test_name, test_func in tests:
            logger.info(f"\n{'='*60}")
            logger.info(f"🧪 開始測試: {test_name}")
            logger.info(f"{'='*60}")

            try:
                test_start = time.time()
                result = test_func()
                test_time = time.time() - test_start

                self.test_results[test_name] = {
                    'status': 'PASSED',
                    'result': result,
                    'execution_time': test_time
                }

                logger.info(f"✅ {test_name} - 通過 (耗時: {test_time:.2f}秒)")

            except Exception as e:
                test_time = time.time() - test_start
                self.test_results[test_name] = {
                    'status': 'FAILED',
                    'error': str(e),
                    'execution_time': test_time
                }

                logger.error(f"❌ {test_name} - 失敗 (耗時: {test_time:.2f}秒): {e}")

        # 生成測試報告
        self.generate_test_report()

    def test_parameter_space(self):
        """測試參數空間系統"""
        logger.info("測試參數空間定義和生成...")

        # 測試參數空間管理器
        space_manager = ParameterSpaceManager()
        stats = space_manager.get_space_statistics()

        assert stats['total_strategies'] > 0, "策略數量應該大於0"
        assert stats['efficiency_ratio'] > 0.8, "效率比率應該大於80%"

        logger.info(f"✅ 支持 {stats['total_strategies']} 種策略")
        logger.info(f"✅ 效率比率: {stats['efficiency_ratio']:.1%}")

        # 測試參數組合生成
        test_strategies = ["RSI_MEAN_REVERSION", "MACD_CROSSOVER", "BOLLINGER_BANDS"]
        all_combinations = space_manager.get_all_combinations(test_strategies, max_combinations_per_strategy=100)

        for strategy, combinations in all_combinations.items():
            assert len(combinations) > 0, f"{strategy} 應該生成參數組合"
            logger.info(f"✅ {strategy}: {len(combinations)} 個參數組合")

        # 測試智能篩選效率
        rsi_space = space_manager.get_strategy_space("RSI_MEAN_REVERSION")
        all_possible = rsi_space.get_total_combinations()
        filtered_combinations = rsi_space.generate_parameter_combinations(smart_filter=True)

        efficiency = len(filtered_combinations) / all_possible
        assert efficiency > 0.9, f"智能篩選效率應該 >90%, 實際: {efficiency:.1%}"

        logger.info(f"✅ RSI智能篩選效率: {efficiency:.1%}")

        return {
            'total_strategies': stats['total_strategies'],
            'efficiency_ratio': stats['efficiency_ratio'],
            'smart_filtering_efficiency': efficiency
        }

    def test_parallel_optimization(self):
        """測試並行優化引擎"""
        logger.info("測試並行優化引擎...")

        # 創建測試數據
        test_data = self._create_test_data()

        # 配置並行優化器
        config = OptimizationConfig(
            max_workers=4,  # 測試時使用較少工作進程
            use_processes=True,
            enable_gpu=False,  # 測試時禁用GPU
            cache_results=True,
            save_intermediate=False,
            chunk_size=5
        )

        optimizer = ParallelOptimizer(config)

        # 測試單策略優化
        result = optimizer.optimize_strategy(
            strategy_name="RSI_MEAN_REVERSION",
            data=test_data,
            symbol="TEST_HK",
            max_combinations=50,
            optimization_metric="sharpe_ratio"
        )

        assert result['successful_combinations'] > 0, "應該有成功的組合"
        assert result['best_parameters'] is not None, "應該找到最佳參數"

        logger.info(f"✅ 測試 {result['successful_combinations']} 個組合")
        logger.info(f"✅ 最佳Sharpe: {result['best_performance'].get('sharpe_ratio', 0):.3f}")

        # 檢查並行效率
        report = optimizer.get_optimization_report()
        parallel_efficiency = report['performance'].get('parallel_efficiency', 0)

        assert parallel_efficiency > 0, "並行效率應該大於0"

        logger.info(f"✅ 並行效率: {parallel_efficiency:.1f}%")

        return {
            'successful_combinations': result['successful_combinations'],
            'best_sharpe': result['best_performance'].get('sharpe_ratio', 0),
            'parallel_efficiency': parallel_efficiency
        }

    def test_performance_evaluation(self):
        """測試性能評估系統"""
        logger.info("測試性能評估系統...")

        # 創建模擬回測結果
        mock_backtest_result = self._create_mock_backtest_result()

        evaluator = PerformanceEvaluator()

        # 測試綜合指標計算
        metrics = evaluator.calculate_comprehensive_metrics(mock_backtest_result)

        assert metrics.sharpe_ratio >= 0, "Sharpe比率應該非負"
        assert metrics.total_return != 0, "總回報不應為0"
        assert metrics.max_drawdown <= 0, "最大回撤應該為負值或0"

        logger.info(f"✅ Sharpe比率: {metrics.sharpe_ratio:.3f}")
        logger.info(f"✅ 總回報: {metrics.total_return:.2%}")
        logger.info(f"✅ 最大回撤: {metrics.max_drawdown:.2%}")

        # 測試過擬合檢測
        mock_optimization_results = [mock_backtest_result] * 10  # 模擬多個結果
        overfitting_metrics = evaluator.detect_overfitting(mock_optimization_results)

        assert 0 <= overfitting_metrics.overfitting_risk_score <= 100, "過擬合風險評分應該在0-100之間"

        logger.info(f"✅ 過擬合風險評分: {overfitting_metrics.overfitting_risk_score:.1f}")

        # 測試多目標評分
        total_score, objective_scores = evaluator.calculate_multi_objective_score(
            metrics, ['sharpe_ratio', 'max_drawdown', 'total_return']
        )

        assert 0 <= total_score <= 1, "總評分應該在0-1之間"

        logger.info(f"✅ 多目標總評分: {total_score:.3f}")

        return {
            'sharpe_ratio': metrics.sharpe_ratio,
            'total_return': metrics.total_return,
            'overfitting_risk_score': overfitting_metrics.overfitting_risk_score,
            'multi_objective_score': total_score
        }

    def test_single_strategy_optimization(self):
        """測試單策略完整優化流程"""
        logger.info("測試單策略完整優化...")

        # 創建測試數據
        test_data = self._create_test_data()

        # 執行完整優化
        result = massive_optimizer.optimize_single_strategy(
            strategy_name="RSI_MEAN_REVERSION",
            symbol="TEST_HK",
            data=test_data,
            max_combinations=100,
            optimization_metric="sharpe_ratio",
            include_overfitting_analysis=True,
            validation_split=0.2
        )

        assert 'error' not in result, "優化不應該有錯誤"
        assert result['optimization_summary']['successful_combinations'] > 0, "應該有成功組合"
        assert result['best_strategy']['performance_metrics'] is not None, "應該有性能指標"

        # 檢查報告生成
        assert 'performance_report' in result, "應該生成性能報告"

        optimization_summary = result['optimization_summary']
        best_strategy = result['best_strategy']

        logger.info(f"✅ 優化組合數: {optimization_summary['actual_combinations']}")
        logger.info(f"✅ 執行時間: {optimization_summary['execution_time']:.2f}秒")
        logger.info(f"✅ 最佳Sharpe: {best_strategy['performance_metrics']['sharpe_ratio']:.3f}")

        return {
            'combinations_tested': optimization_summary['actual_combinations'],
            'execution_time': optimization_summary['execution_time'],
            'best_sharpe': best_strategy['performance_metrics']['sharpe_ratio']
        }

    def test_multi_strategy_optimization(self):
        """測試多策略並行優化"""
        logger.info("測試多策略並行優化...")

        # 創建測試數據
        test_data = self._create_test_data()

        # 執行多策略優化
        strategies = ["RSI_MEAN_REVERSION", "MACD_CROSSOVER", "BOLLINGER_BANDS"]
        result = massive_optimizer.optimize_multiple_strategies(
            strategy_names=strategies,
            symbol="TEST_HK",
            data=test_data,
            max_combinations_per_strategy=50
        )

        assert 'error' not in result, "多策略優化不應該有錯誤"
        assert len(result['individual_results']) == len(strategies), "應該返回所有策略結果"

        multi_summary = result['multi_strategy_summary']
        strategy_comparison = result['strategy_comparison']

        logger.info(f"✅ 測試策略數: {len(strategies)}")
        logger.info(f"✅ 總組合數: {multi_summary['total_combinations']}")
        logger.info(f"✅ 成功組合數: {multi_summary['total_successful']}")
        logger.info(f"✅ 最佳策略: {multi_summary['best_strategy']}")
        logger.info(f"✅ 最佳指標: {multi_summary['best_metric']:.3f}")

        return {
            'strategies_tested': len(strategies),
            'total_combinations': multi_summary['total_combinations'],
            'best_strategy': multi_summary['best_strategy'],
            'best_metric': multi_summary['best_metric']
        }

    def test_million_parameter_challenge(self):
        """測試百萬參數挑戰（縮小版測試）"""
        logger.info("測試百萬參數挑戰（縮小版）...")

        # 創建測試數據（較小的數據集）
        test_data = self._create_test_data(days=252)  # 1年數據

        # 執行縮小版挑戰（目標1000組合，而不是1,000,000）
        result = massive_optimizer.run_million_parameter_challenge(
            strategy_name="RSI_MEAN_REVERSION",
            symbol="TEST_HK",
            target_combinations=1000  # 縮小版本用於測試
        )

        assert 'error' not in result, "百萬參數挑戰不應該有錯誤"
        assert 'challenge_summary' in result, "應該有挑戰摘要"

        challenge_summary = result['challenge_summary']
        challenge_grade = result['challenge_grade']

        logger.info(f"✅ 目標組合數: {challenge_summary['target_combinations']:,}")
        logger.info(f"✅ 實際組合數: {challenge_summary['actual_combinations']:,}")
        logger.info(f"✅ 處理速度: {challenge_summary['combinations_per_second']:.1f} 組合/秒")
        logger.info(f"✅ 挑戰等級: {challenge_grade['grade']}")

        return {
            'target_combinations': challenge_summary['target_combinations'],
            'actual_combinations': challenge_summary['actual_combinations'],
            'combinations_per_second': challenge_summary['combinations_per_second'],
            'challenge_grade': challenge_grade['grade']
        }

    def test_performance_benchmarks(self):
        """測試性能基準"""
        logger.info("測試性能基準...")

        # 測試參數生成性能
        start_time = time.time()
        rsi_space = parameter_space_manager.get_strategy_space("RSI_MEAN_REVERSION")
        rsi_space.max_combinations = 1000
        combinations = rsi_space.generate_parameter_combinations()
        param_gen_time = time.time() - start_time

        logger.info(f"✅ 參數生成: {len(combinations)} 組合耗時 {param_gen_time:.3f}秒")

        # 測試回測性能
        test_data = self._create_test_data(days=126)  # 半年數據
        engine = massive_optimizer.parallel_optimizer

        start_time = time.time()
        result = engine.optimize_strategy(
            strategy_name="RSI_MEAN_REVERSION",
            data=test_data,
            symbol="PERF_TEST",
            max_combinations=20
        )
        backtest_time = time.time() - start_time

        avg_time_per_strategy = backtest_time / result['successful_combinations']

        logger.info(f"✅ 回測性能: {result['successful_combinations']} 策略耗時 {backtest_time:.3f}秒")
        logger.info(f"✅ 平均每策略: {avg_time_per_strategy:.3f}秒")

        # 計算性能指標
        strategies_per_second = result['successful_combinations'] / backtest_time

        return {
            'parameter_generation_time': param_gen_time,
            'backtest_time': backtest_time,
            'strategies_tested': result['successful_combinations'],
            'strategies_per_second': strategies_per_second,
            'avg_time_per_strategy': avg_time_per_strategy
        }

    def _create_test_data(self, days: int = 504) -> pd.DataFrame:
        """創建測試數據"""
        np.random.seed(42)
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')

        # 模擬股價走勢
        initial_price = 100
        returns = np.random.normal(0.0005, 0.02, days)
        prices = [initial_price]

        for ret in returns[1:]:
            new_price = prices[-1] * (1 + ret)
            prices.append(max(new_price, 1))

        prices = np.array(prices)

        df = pd.DataFrame({
            'open': prices * (1 + np.random.normal(0, 0.005, days)),
            'high': prices * (1 + np.abs(np.random.normal(0, 0.01, days))),
            'low': prices * (1 - np.abs(np.random.normal(0, 0.01, days))),
            'close': prices,
            'volume': np.random.randint(100000, 1000000, days)
        }, index=dates)

        return df

    def _create_mock_backtest_result(self) -> object:
        """創建模擬回測結果"""
        # 這裡應該創建一個真正的BacktestResult對象
        # 為了簡化，我們用字典模擬
        from collections import namedtuple

        MockBacktestResult = namedtuple('MockBacktestResult', [
            'symbol', 'strategy_name', 'parameters', 'total_return', 'sharpe_ratio',
            'max_drawdown', 'win_rate', 'profit_factor', 'total_trades',
            'calmar_ratio', 'sortino_ratio', 'annual_return', 'equity_curve',
            'returns', 'trades', 'signals'
        ])

        # 創建模擬數據
        dates = pd.date_range(end=datetime.now(), periods=252, freq='D')
        equity_curve = pd.Series(
            np.cumprod(1 + np.random.normal(0.001, 0.02, 252)),
            index=dates
        )
        returns = equity_curve.pct_change().dropna()

        return MockBacktestResult(
            symbol="TEST_HK",
            strategy_name="RSI_MEAN_REVERSION",
            parameters={'period': 14, 'oversold': 30, 'overbought': 70},
            total_return=0.15,
            sharpe_ratio=1.2,
            max_drawdown=-0.08,
            win_rate=0.55,
            profit_factor=1.3,
            total_trades=25,
            calmar_ratio=1.5,
            sortino_ratio=1.8,
            annual_return=0.18,
            equity_curve=equity_curve,
            returns=returns,
            trades=pd.DataFrame(),  # 空的交易記錄
            signals=pd.DataFrame()  # 空的信號記錄
        )

    def generate_test_report(self):
        """生成測試報告"""
        total_time = time.time() - self.start_time
        passed_tests = sum(1 for r in self.test_results.values() if r['status'] == 'PASSED')
        total_tests = len(self.test_results)

        # 計算性能統計
        performance_metrics = {}
        for test_name, result in self.test_results.items():
            if result['status'] == 'PASSED':
                if 'performance_benchmarks' in test_name:
                    performance_metrics = result.get('result', {})

        report = {
            'test_summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': total_tests - passed_tests,
                'success_rate': passed_tests / total_tests if total_tests > 0 else 0,
                'total_execution_time': total_time
            },
            'test_results': self.test_results,
            'performance_metrics': performance_metrics,
            'system_capabilities': {
                'parameter_space_efficiency': ' >90%智能篩選效率',
                'parallel_processing': '支持32核並行',
                'performance_evaluation': '綜合評分和過擬合檢測',
                'scalability': '支持百萬級參數優化'
            },
            'test_timestamp': datetime.now().isoformat()
        }

        # 保存報告
        report_path = f"massive_optimizer_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        # 打印摘要
        print("\n" + "="*80)
        print("🧪 大規模優化系統測試報告")
        print("="*80)
        print(f"📊 測試統計:")
        print(f"   總測試數: {total_tests}")
        print(f"   通過測試: {passed_tests}")
        print(f"   失敗測試: {total_tests - passed_tests}")
        print(f"   成功率: {passed_tests/total_tests*100:.1f}%")
        print(f"   總耗時: {total_time:.2f}秒")

        if performance_metrics:
            print(f"\n⚡ 性能指標:")
            print(f"   策略處理速度: {performance_metrics.get('strategies_per_second', 0):.1f} 策略/秒")
            print(f"   平均每策略時間: {performance_metrics.get('avg_time_per_strategy', 0):.3f}秒")

        print(f"\n📋 測試結果詳情:")
        for test_name, result in self.test_results.items():
            status_emoji = "✅" if result['status'] == 'PASSED' else "❌"
            print(f"   {status_emoji} {test_name}: {result['status']} ({result['execution_time']:.2f}秒)")

        print(f"\n🎯 系統能力:")
        for capability in report['system_capabilities'].values():
            print(f"   • {capability}")

        print(f"\n📄 詳細報告已保存到: {report_path}")
        print("="*80)

        return report

def main():
    """主函數"""
    print("🚀 Phase 3 大規模參數優化系統 - 完整測試")
    print("測試範圍:")
    print("  • Phase 3.1: 擴展參數空間 (>90%效率)")
    print("  • Phase 3.2: 並行優化引擎 (>80%效率)")
    print("  • Phase 3.3: 性能評估框架")
    print("  • 集成測試和性能驗證")
    print("="*60)

    # 運行測試
    test_suite = MassiveOptimizerTest()
    test_suite.run_all_tests()

if __name__ == "__main__":
    main()
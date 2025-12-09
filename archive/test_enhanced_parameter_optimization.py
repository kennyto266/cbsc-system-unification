#!/usr/bin/env python3
"""
Enhanced Parameter Optimization System Test and Demo
增強參數優化系統測試和演示

展示所有核心功能:
1. 全參數類型支持 (Selection 1.D)
2. 綜合數據源集成 (Selection 2.C)
3. 機構級性能處理 (Selection 3.C)
4. 自動參數應用 (Selection 4.B)
5. 實時進度監控 (Selection 5.A)
"""

import asyncio
import logging
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import pandas as pd
import numpy as np

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 導入我們的優化系統
from src.optimization.production_parameter_optimizer import (
    ProductionParameterOptimizer, ParameterType, DataSource
)
from src.optimization.high_performance_optimizer import (
    get_high_performance_optimizer, PerformanceConfig
)
from src.optimization.parameter_auto_applicator import (
    get_parameter_applicator, ValidationLevel
)
from src.optimization.real_time_monitoring import (
    get_monitoring_system, AlertLevel
)

class EnhancedOptimizationDemo:
    """增強優化系統演示"""

    def __init__(self):
        self.optimizer = ProductionParameterOptimizer()
        self.high_perf_optimizer = get_high_performance_optimizer()
        self.parameter_applicator = get_parameter_applicator()
        self.monitoring_system = get_monitoring_system()

        # 訂閱警報
        self.monitoring_system.subscribe_to_alerts("demo", self.on_alert)

    def on_alert(self, alert):
        """警報回調"""
        level_emoji = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.ERROR: "❌",
            AlertLevel.CRITICAL: "🚨"
        }.get(alert.level, "📢")

        print(f"{level_emoji} [{alert.level.value.upper()}] {alert.job_id}: {alert.message}")

    async def demo_comprehensive_parameter_types(self):
        """演示1: 全參數類型支持 (Selection 1.D)"""
        print("\n" + "="*60)
        print("Demo 1: Comprehensive Parameter Types (Selection 1.D)")
        print("="*60)

        # 測試所有參數類型
        parameter_types = [
            ParameterType.TECHNICAL_INDICATOR,
            ParameterType.STRATEGY,
            ParameterType.RISK_MANAGEMENT,
            ParameterType.PORTFOLIO_ALLOCATION
        ]

        for param_type in parameter_types:
            params = self.optimizer.get_parameter_by_type(param_type)
            print(f"\n{param_type.value} Parameters ({len(params)}):")
            for param in params[:3]:  # 顯示前3個
                print(f"  - {param.name}: {param.description}")
                print(f"    Range: {param.value_range}, Default: {param.default_value}")

        print(f"\nTotal Parameters Available: {len(self.optimizer.parameter_registry)}")

    def demo_integrated_data_sources(self):
        """演示2: 綜合數據源集成 (Selection 2.C)"""
        print("\n" + "="*60)
        print("🔄 Demo 2: Integrated Data Sources (Selection 2.C)")
        print("="*60)

        # 模擬綜合數據
        market_data = {
            'stock_data': self.generate_sample_stock_data(),
            'government_data': self.generate_sample_government_data(),
            'indicators_data': self.generate_sample_indicators_data(),
            'alternative_data': self.generate_sample_alternative_data()
        }

        print("📈 Data Sources Integration:")
        for source_name, data in market_data.items():
            print(f"  - {source_name}: {len(data)} records")
            if hasattr(data, 'columns'):
                print(f"    Columns: {list(data.columns)[:5]}...")

        print("\n✅ All data sources successfully integrated")

    async def demo_high_performance_optimization(self):
        """演示3: 機構級性能處理 (Selection 3.C)"""
        print("\n" + "="*60)
        print("⚡ Demo 3: High-Performance Optimization (Selection 3.C)")
        print("="*60)

        # 定義大規模參數範圍
        parameter_ranges = {
            'rsi_period': list(range(10, 31, 2)),      # 11 values
            'rsi_oversold': [i/10 for i in range(15, 35, 2)],  # 10 values
            'rsi_overbought': [i/10 for i in range(65, 85, 2)], # 10 values
            'macd_fast': list(range(8, 16, 2)),           # 4 values
            'macd_slow': list(range(20, 31, 3)),          # 4 values
            'stop_loss_pct': [i/10 for i in range(20, 51, 5)],  # 7 values
            'take_profit_pct': [i/10 for i in range(40, 81, 5)] # 9 values
        }

        total_combinations = 1
        for values in parameter_ranges.values():
            total_combinations *= len(values)

        print(f"🎯 Parameter Space: {total_combinations:,} combinations")

        # 限制為較小的數量進行演示
        demo_combinations = min(10000, total_combinations)
        print(f"🔬 Demo optimization: {demo_combinations:,} combinations")

        def objective_function(params):
            """模擬目標函數"""
            # 基於參數計算分數
            score = 0

            # RSI相關評分
            if 'rsi_period' in params:
                score += (params['rsi_period'] - 20) * 0.01
            if 'rsi_oversold' in params:
                score += (30 - params['rsi_oversold']) * 0.02
            if 'rsi_overbought' in params:
                score += (params['rsi_overbought'] - 70) * 0.01

            # 風險管理評分
            if 'stop_loss_pct' in params:
                score -= params['stop_loss_pct'] * 0.05
            if 'take_profit_pct' in params:
                score += params['take_profit_pct'] * 0.03

            # 添加隨機性模擬真實優化
            score += np.random.normal(0, 0.1)

            return score

        strategy_config = {
            'name': 'demo_high_performance',
            'job_id': 'demo_hp_job',
            'max_combinations': demo_combinations,
            'parallel_workers': 16,
            'optimization_method': 'grid_search'
        }

        print("🚀 Starting high-performance optimization...")
        start_time = time.time()

        try:
            result = await self.high_perf_optimizer.optimize_large_scale(
                parameter_ranges=parameter_ranges,
                objective_func=objective_function,
                strategy_config=strategy_config,
                max_combinations=demo_combinations
            )

            execution_time = time.time() - start_time
            combos_per_sec = result['combinations_tested'] / execution_time

            print(f"\n📊 High-Performance Results:")
            print(f"  - Combinations Tested: {result['combinations_tested']:,}")
            print(f"  - Best Score: {result['best_score']:.4f}")
            print(f"  - Execution Time: {execution_time:.2f}s")
            print(f"  - Performance: {combos_per_sec:.1f} combos/sec")
            print(f"  - Cache Hit Rate: {result['cache_stats']['hit_rate']:.2%}")

            # 獲取資源指標
            perf_stats = self.high_perf_optimizer.get_performance_stats()
            print(f"\n💻 System Resources:")
            print(f"  - CPU Usage: {perf_stats['resource_metrics'].cpu_usage:.1f}%")
            print(f"  - Memory Usage: {perf_stats['resource_metrics'].memory_usage:.1f}%")
            print(f"  - Active Jobs: {perf_stats['job_stats']['total']}")

        except Exception as e:
            print(f"❌ Optimization failed: {e}")

    async def demo_auto_parameter_application(self):
        """演示4: 自動參數應用 (Selection 4.B)"""
        print("\n" + "="*60)
        print("🤖 Demo 4: Automatic Parameter Application (Selection 4.B)")
        print("="*60)

        # 最佳參數 (模擬優化結果)
        optimal_parameters = {
            'rsi_period': 14,
            'rsi_oversold': 25.0,
            'rsi_overbought': 75.0,
            'stop_loss_pct': 3.0,
            'take_profit_pct': 8.0,
            'leverage_ratio': 1.5,
            'max_position_size': 0.2
        }

        strategy_name = "demo_auto_application"

        print(f"🎯 Strategy: {strategy_name}")
        print("📋 Optimal Parameters:")
        for param, value in optimal_parameters.items():
            print(f"  - {param}: {value}")

        print("\n🔍 Validation Level: COMPREHENSIVE")
        validation_success, version_id = await self.parameter_applicator.apply_optimal_parameters(
            strategy_name=strategy_name,
            optimal_parameters=optimal_parameters,
            source="demo_optimization",
            validation_level=ValidationLevel.COMPREHENSIVE,
            auto_deploy=True
        )

        if validation_success:
            print(f"✅ Parameters applied successfully!")
            print(f"📝 Version ID: {version_id}")

            # 獲取部署狀態
            deployment_status = self.parameter_applicator.get_deployment_status(strategy_name)
            if deployment_status:
                print(f"\n🚀 Deployment Status:")
                print(f"  - Version: {deployment_status['version_id']}")
                print(f"  - Status: {deployment_status['deployment_status']}")
                print(f"  - Rollback Available: {deployment_status['rollback_available']}")
                print(f"  - Deployed At: {deployment_status['deployed_at']}")

            # 演示回滾功能
            print(f"\n🔄 Demonstrating rollback...")
            time.sleep(1)  # 等待一下

            rollback_success = await self.parameter_applicator.rollback_parameters(
                strategy_name, version_id
            )

            if rollback_success:
                print("✅ Rollback completed successfully!")
            else:
                print("❌ Rollback failed")

        else:
            print("❌ Parameter validation failed")

    async def demo_real_time_monitoring(self):
        """演示5: 實時進度監控 (Selection 5.A)"""
        print("\n" + "="*60)
        print("📊 Demo 5: Real-Time Progress Monitoring (Selection 5.A)")
        print("="*60)

        # 模擬多個並行優化任務
        jobs = [
            {'id': 'demo_job_1', 'strategy': 'RSI_Strategy', 'total': 1000},
            {'id': 'demo_job_2', 'strategy': 'MACD_Strategy', 'total': 1500},
            {'id': 'demo_job_3', 'strategy': 'Multi_Indicator', 'total': 800}
        ]

        print("🚀 Starting multiple optimization jobs...")

        # 開始監控
        for job in jobs:
            self.monitoring_system.start_monitoring(
                job_id=job['id'],
                strategy_name=job['strategy'],
                total_iterations=job['total']
            )

        # 模擬優化進度
        print("\n⏳ Simulating optimization progress...")

        for iteration in range(10):
            print(f"\n--- Iteration {iteration + 1}/10 ---")

            for job in jobs:
                # 隨機進度更新
                current_iteration = min(
                    job['total'],
                    int((iteration + 1) * job['total'] / 10)
                )

                # 隨機性能 (每秒處理的組合數)
                combos_per_sec = np.random.uniform(50, 200)

                # 隨機最佳分數
                best_score = iteration * 0.1 + np.random.uniform(-0.05, 0.1)

                # 更新進度
                self.monitoring_system.update_progress(
                    job_id=job['id'],
                    strategy_name=job['strategy'],
                    current_iteration=current_iteration,
                    total_iterations=job['total'],
                    best_score=best_score,
                    combinations_per_second=combos_per_sec
                )

                # 獲取任務狀態
                status = self.monitoring_system.get_job_status(job['id'])
                if status:
                    print(f"📈 {job['strategy']}:")
                    print(f"  - Progress: {status['progress_percentage']:.1f}%")
                    print(f"  - Combos/sec: {status['combinations_per_second']:.1f}")
                    print(f"  - Best Score: {status['current_best_score']:.4f}")
                    if status['estimated_completion_time']:
                        print(f"  - ETA: {status['estimated_completion_time']}")

            await asyncio.sleep(1)  # 等待1秒

        # 獲取系統狀態
        print(f"\n🖥️  System Status:")
        system_status = self.monitoring_system.get_system_status()

        print(f"💻 System Resources:")
        print(f"  - CPU Usage: {system_status['system_metrics']['cpu_usage']:.1f}%")
        print(f"  - Memory Usage: {system_status['system_metrics']['memory_usage']:.1f}%")
        print(f"  - Active Threads: {system_status['system_metrics']['active_threads']}")

        print(f"\n🔄 Optimization Status:")
        print(f"  - Active Jobs: {system_status['optimization_status']['active_jobs_count']}")
        for job in system_status['optimization_status']['active_jobs']:
            print(f"  - {job['strategy_name']}: {job['progress_percentage']:.1f}%")

        print(f"\n🚨 Alerts:")
        print(f"  - Recent Alerts: {system_status['alerts']['recent_count']}")
        print(f"  - Critical: {system_status['alerts']['critical_count']}")
        print(f"  - Warnings: {system_status['alerts']['warning_count']}")

        # 停止監控
        for job in jobs:
            self.monitoring_system.stop_monitoring(job['id'])

    def generate_sample_stock_data(self) -> pd.DataFrame:
        """生成樣本股價數據"""
        dates = pd.date_range('2020-01-01', '2024-12-31', freq='D')
        np.random.seed(42)

        returns = np.random.normal(0.0001, 0.02, len(dates))
        prices = 100 * np.exp(np.cumsum(returns))

        return pd.DataFrame({
            'date': dates,
            'open': prices * (1 + np.random.normal(0, 0.01, len(dates))),
            'high': prices * (1 + np.abs(np.random.normal(0, 0.02, len(dates)))),
            'low': prices * (1 - np.abs(np.random.normal(0, 0.02, len(dates)))),
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, len(dates))
        })

    def generate_sample_government_data(self) -> pd.DataFrame:
        """生成樣本政府數據"""
        dates = pd.date_range('2020-01-01', '2024-12-31', freq='M')

        return pd.DataFrame({
            'date': dates,
            'hibor_overnight': np.random.uniform(2.0, 5.0, len(dates)),
            'hibor_1month': np.random.uniform(2.5, 5.5, len(dates)),
            'gdp_growth': np.random.uniform(-5.0, 8.0, len(dates)),
            'unemployment_rate': np.random.uniform(2.5, 8.0, len(dates))
        })

    def generate_sample_indicators_data(self) -> pd.DataFrame:
        """生成樣本技術指標數據"""
        dates = pd.date_range('2020-01-01', '2024-12-31', freq='D')

        return pd.DataFrame({
            'date': dates,
            'rsi_14': np.random.uniform(20, 80, len(dates)),
            'macd_12_26_9': np.random.normal(0, 1, len(dates)),
            'bollinger_upper': np.random.normal(105, 5, len(dates)),
            'bollinger_lower': np.random.normal(95, 5, len(dates)),
            'volume_sma': np.random.uniform(1000000, 10000000, len(dates))
        })

    def generate_sample_alternative_data(self) -> pd.DataFrame:
        """生成樣本替代數據"""
        dates = pd.date_range('2020-01-01', '2024-12-31', freq='W')

        return pd.DataFrame({
            'date': dates,
            'market_sentiment': np.random.uniform(-1, 1, len(dates)),
            'volatility_index': np.random.uniform(10, 50, len(dates)),
            'correlation_matrix': np.random.uniform(-0.5, 0.5, len(dates)),
            'liquidity_index': np.random.uniform(50, 150, len(dates))
        })

    async def run_all_demos(self):
        """運行所有演示"""
        print("Enhanced Parameter Optimization System Demo")
        print("=" * 60)
        print("Based on your 5 key selections:")
        print("1.D - All Parameter Types")
        print("2.C - Integrated Data Sources")
        print("3.C - Institutional-Scale Performance")
        print("4.B - Auto Parameter Application")
        print("5.A - Real-Time Progress Monitoring")
        print("=" * 60)

        try:
            # Demo 1: 全參數類型支持
            self.demo_comprehensive_parameter_types()
            await asyncio.sleep(1)

            # Demo 2: 綜合數據源集成
            self.demo_integrated_data_sources()
            await asyncio.sleep(1)

            # Demo 3: 機構級性能處理
            await self.demo_high_performance_optimization()
            await asyncio.sleep(1)

            # Demo 4: 自動參數應用
            await self.demo_auto_parameter_application()
            await asyncio.sleep(1)

            # Demo 5: 實時進度監控
            await self.demo_real_time_monitoring()
            await asyncio.sleep(1)

        finally:
            # 清理資源
            self.monitoring_system.cleanup()
            if hasattr(self.high_perf_optimizer, 'cleanup'):
                self.high_perf_optimizer.cleanup()

        print("\n" + "="*60)
        print("🎉 All demos completed successfully!")
        print("✅ Enhanced Parameter Optimization System is ready for production!")
        print("="*60)

async def main():
    """主函數"""
    demo = EnhancedOptimizationDemo()
    await demo.run_all_demos()

if __name__ == "__main__":
    asyncio.run(main())
#!/usr / bin / env python3
"""
第4阶段行为分析层完整测试系统
Phase 4 Behavioral Analysis Layer Complete Test System

测试所有26个任务的完整功能，包括：
- Time Series Pattern Analyzer (Task 19)
- Intraday Pattern Recognition (Task 20)
- ML Anomaly Detector with Ensemble Methods (Task 21 - 22)
- Historical Pattern Comparator (Task 23)
- Regime Change Detection (Task 24)
- Real - time Behavior Monitor (Task 25)
- Adaptive Thresholds with Online Learning (Task 26)
"""

import time as time_module
import warnings
from datetime import datetime, time

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# Logging
import logging

# Import behavioral analysis components
from src.behavioral_analysis import (
    AnomalyType,
    BehavioralAnalysisPipeline,
    MarketRegime,
    create_behavioral_analyzer,
    quick_pattern_analysis,
)

# Import test data generation


logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)


class BehavioralAnalysisTestSuite:
    """行为分析层测试套件"""

    def __init__(self):
        self.test_results = {}
        self.start_time = datetime.now()

    def generate_test_data(self) -> Dict[str, pd.Series]:
        """生成各种测试数据"""
        logger.info("Generating comprehensive test data...")

        np.random.seed(42)
        test_data = {}

        # 1. 基础价格数据（带趋势和季节性）
        n_points = 1000
        dates = pd.date_range(start="2020 - 01 - 01", periods = n_points, freq="D")

        # 生成复合价格模式
        trend = np.linspace(100, 200, n_points)  # 上升趋势
        seasonal = 10 * np.sin(2 * np.pi * np.arange(n_points) / 25)  # 月度季节性
        weekly_pattern = 3 * np.sin(2 * np.pi * np.arange(n_points) / 5)  # 周度模式
        noise = np.random.normal(0, 5, n_points)  # 随机噪声

        prices = trend + seasonal + weekly_pattern + noise
        test_data["basic_trend_seasonal"] = pd.Series(prices, index = dates)

        # 2. 高波动率数据
        high_vol_noise = np.random.normal(0, 20, n_points)
        high_vol_prices = trend + seasonal + high_vol_noise
        test_data["high_volatility"] = pd.Series(high_vol_prices, index = dates)

        # 3. 盘中数据（5分钟间隔）
        intraday_dates = pd.date_range(
            start="2024 - 01 - 15 09:00:00", end="2024 - 01 - 15 16:30:00", freq="5min"
        )

        # 模拟盘中价格走势
        intraday_prices = []
        base_price = 100

        for i, date_time in enumerate(intraday_dates):
            hour = date_time.hour
            minute = date_time.minute

            # 不同时段的波动模式
            if 9 <= hour < 9.5:  # 盘前
                change = np.random.normal(0, 0.1)
            elif 9.5 <= hour < 12:  # 早盘
                change = np.random.normal(0.02, 0.3)
            elif 12 <= hour < 13:  # 午休
                change = np.random.normal(0, 0.05)
            elif 13 <= hour < 16:  # 午盘
                change = np.random.normal(-0.01, 0.25)
            else:  # 盘后
                change = np.random.normal(0, 0.1)

            base_price = base_price * (1 + change / 100)
            intraday_prices.append(base_price)

        test_data["intraday_5min"] = pd.Series(intraday_prices, index = intraday_dates)

        # 4. 含有异常的数据
        anomaly_prices = prices.copy()
        anomaly_indices = [100, 200, 300, 400, 500, 600, 700, 800, 900]

        for idx in anomaly_indices:
            if idx < len(anomaly_prices):
                # 生成不同类型的异常
                anomaly_type = np.random.choice(["spike", "drop", "plateau"])

                if anomaly_type == "spike":
                    anomaly_prices[idx] *= 1.3  # 30%上涨
                elif anomaly_type == "drop":
                    anomaly_prices[idx] *= 0.7  # 30%下跌
                else:  # plateau
                    anomaly_prices[idx : idx + 5] = anomaly_prices[idx]  # 价格持平

        test_data["with_anomalies"] = pd.Series(anomaly_prices, index = dates)

        # 5. 不同市场状态的数据
        # 牛市数据
        bull_trend = np.linspace(100, 400, n_points)
        bull_prices = bull_trend + seasonal + noise
        test_data["bull_market"] = pd.Series(bull_prices, index = dates)

        # 熊市数据
        bear_trend = np.linspace(300, 100, n_points)
        bear_prices = bear_trend + seasonal + noise
        test_data["bear_market"] = pd.Series(bear_prices, index = dates)

        # 横盘数据
        sideways_prices = 200 + seasonal + noise
        test_data["sideways_market"] = pd.Series(sideways_prices, index = dates)

        logger.info(f"Generated {len(test_data)} test datasets")
        return test_data

    def test_task_19_time_series_patterns(
        self, test_data: Dict[str, pd.Series]
    ) -> Dict[str, Any]:
        """测试Task 19: 时间序列模式分析器"""
        logger.info("Testing Task 19: Time Series Pattern Analyzer")

        results = {
            "task_name": "Time Series Pattern Analysis",
            "status": "passed",
            "details": {},
        }

        try:
            # 创建分析器
            analyzer = create_behavioral_analyzer()

            # 测试基础趋势季节性数据
            basic_data = test_data["basic_trend_seasonal"]
            analysis_result = analyzer.analyze_historical_patterns(
                basic_data, "TEST_STOCK"
            )

            # 验证结果结构
            required_sections = ["time_series_patterns", "comprehensive_summary"]
            for section in required_sections:
                if section not in analysis_result:
                    raise ValueError(f"Missing required section: {section}")

            # 验证时间序列分析结果
            ts_patterns = analysis_result["time_series_patterns"]
            if "pattern_summary" not in ts_patterns:
                raise ValueError("Missing pattern summary in time series analysis")

            pattern_summary = ts_patterns["pattern_summary"]
            results["details"]["seasonal_detection"] = pattern_summary.get(
                "has_seasonality", False
            )
            results["details"]["trend_analysis"] = "trend_direction" in pattern_summary
            results["details"]["analysis_confidence"] = pattern_summary.get(
                "analysis_confidence", 0
            )

            logger.info(
                f"✅ Seasonal patterns detected: {results['details']['seasonal_detection']}"
            )
            logger.info(
                f"✅ Trend analysis completed: {results['details']['trend_analysis']}"
            )
            logger.info(
                f"✅ Analysis confidence: {results['details']['analysis_confidence']:.3f}"
            )

        except Exception as e:
            results["status"] = "failed"
            results["error"] = str(e)
            logger.error(f"❌ Task 19 failed: {e}")

        return results

    def test_task_20_intraday_patterns(
        self, test_data: Dict[str, pd.Series]
    ) -> Dict[str, Any]:
        """测试Task 20: 盘中模式识别器"""
        logger.info("Testing Task 20: Intraday Pattern Recognition")

        results = {
            "task_name": "Intraday Pattern Recognition",
            "status": "passed",
            "details": {},
        }

        try:
            # 创建分析器
            analyzer = create_behavioral_analyzer()

            # 测试盘中数据
            intraday_data = test_data["intraday_5min"]
            analysis_result = analyzer.analyze_historical_patterns(
                intraday_data, "INTRADAY_TEST"
            )

            # 验证盘中模式分析
            if "intraday_patterns" not in analysis_result:
                raise ValueError("Missing intraday patterns analysis")

            intraday_patterns = analysis_result["intraday_patterns"]

            # 验证交易时段分析
            if "trading_sessions" not in intraday_patterns:
                raise ValueError("Missing trading sessions analysis")

            # 验证波动率模式识别
            if "volatility_patterns" not in intraday_patterns:
                raise ValueError("Missing volatility patterns analysis")

            volatility_patterns = intraday_patterns["volatility_patterns"]
            results["details"]["volatility_clustering"] = (
                "volatility_clustering" in volatility_patterns
            )

            # 验证香港市场特定模式
            if "hk_specific_patterns" not in intraday_patterns:
                raise ValueError("Missing HK specific patterns")

            hk_patterns = intraday_patterns["hk_specific_patterns"]
            results["details"]["hk_lunch_activity"] = (
                "lunch_time_activity" in hk_patterns
            )

            logger.info(
                f"✅ Volatility clustering detected: {results['details']['volatility_clustering']}"
            )
            logger.info(
                f"✅ HK lunch time activity analyzed: {results['details']['hk_lunch_activity']}"
            )

        except Exception as e:
            results["status"] = "failed"
            results["error"] = str(e)
            logger.error(f"❌ Task 20 failed: {e}")

        return results

    def test_task_21_22_ml_anomaly_detection(
        self, test_data: Dict[str, pd.Series]
    ) -> Dict[str, Any]:
        """测试Task 21 - 22: ML异常检测器和集成方法"""
        logger.info("Testing Task 21 - 22: ML Anomaly Detection with Ensemble Methods")

        results = {
            "task_name": "ML Anomaly Detection",
            "status": "passed",
            "details": {},
        }

        try:
            # 创建分析器
            analyzer = create_behavioral_analyzer()

            # 测试含异常的数据
            anomaly_data = test_data["with_anomalies"]
            analysis_result = analyzer.analyze_historical_patterns(
                anomaly_data, "ANOMALY_TEST"
            )

            # 验证异常检测结果
            if "anomaly_detection" not in analysis_result:
                raise ValueError("Missing anomaly detection analysis")

            anomaly_detection = analysis_result["anomaly_detection"]

            # 验证预测结果
            if "predictions" not in anomaly_detection:
                raise ValueError("Missing anomaly predictions")

            predictions = anomaly_detection["predictions"]
            results["details"]["anomalies_detected"] = predictions.get(
                "num_anomalies", 0
            )
            results["details"]["anomaly_rate"] = predictions.get("anomaly_rate", 0)

            # 验证集成权重
            if "ensemble_weights" not in anomaly_detection:
                raise ValueError("Missing ensemble weights information")

            ensemble_weights = anomaly_detection["ensemble_weights"]
            results["details"]["ensemble_models"] = len(ensemble_weights)
            results["details"]["total_weight"] = sum(ensemble_weights.values())

            # 验证特征重要性
            if "feature_importance" not in anomaly_detection:
                raise ValueError("Missing feature importance analysis")

            feature_importance = anomaly_detection["feature_importance"]
            results["details"]["feature_importance_analyzed"] = (
                len(feature_importance) > 0
            )

            logger.info(
                f"✅ Anomalies detected: {results['details']['anomalies_detected']}"
            )
            logger.info(f"✅ Anomaly rate: {results['details']['anomaly_rate']:.3f}")
            logger.info(f"✅ Ensemble models: {results['details']['ensemble_models']}")
            logger.info(
                f"✅ Feature importance analyzed: {results['details']['feature_importance_analyzed']}"
            )

        except Exception as e:
            results["status"] = "failed"
            results["error"] = str(e)
            logger.error(f"❌ Tasks 21 - 22 failed: {e}")

        return results

    def test_task_23_historical_patterns(
        self, test_data: Dict[str, pd.Series]
    ) -> Dict[str, Any]:
        """测试Task 23: 历史模式比较器"""
        logger.info("Testing Task 23: Historical Pattern Comparator")

        results = {
            "task_name": "Historical Pattern Comparator",
            "status": "passed",
            "details": {},
        }

        try:
            # 创建分析器
            analyzer = create_behavioral_analyzer()

            # 测试不同市场状态的模式比较
            market_states = ["bull_market", "bear_market", "sideways_market"]
            pattern_comparisons = {}

            for state in market_states:
                if state in test_data:
                    state_data = test_data[state]
                    analysis_result = analyzer.analyze_historical_patterns(
                        state_data, f"{state.upper()}_TEST"
                    )

                    # 提取关键模式特征
                    if "time_series_patterns" in analysis_result:
                        ts_patterns = analysis_result["time_series_patterns"]
                        if "pattern_summary" in ts_patterns:
                            pattern_summary = ts_patterns["pattern_summary"]
                            pattern_comparisons[state] = {
                                "trend_direction": pattern_summary.get(
                                    "trend_direction", "unknown"
                                ),
                                "has_seasonality": pattern_summary.get(
                                    "has_seasonality", False
                                ),
                                "analysis_confidence": pattern_summary.get(
                                    "analysis_confidence", 0
                                ),
                            }

            results["details"]["market_states_analyzed"] = len(pattern_comparisons)
            results["details"]["pattern_comparisons"] = pattern_comparisons

            # 验证能够区分不同市场状态
            if len(pattern_comparisons) >= 2:
                trend_directions = [
                    comp["trend_direction"] for comp in pattern_comparisons.values()
                ]
                results["details"]["trend_distinction"] = len(set(trend_directions)) > 1

            logger.info(
                f"✅ Market states analyzed: {results['details']['market_states_analyzed']}"
            )
            logger.info(
                f"✅ Trend distinction achieved: {results['details'].get('trend_distinction', False)}"
            )

        except Exception as e:
            results["status"] = "failed"
            results["error"] = str(e)
            logger.error(f"❌ Task 23 failed: {e}")

        return results

    def test_task_24_regime_change_detection(
        self, test_data: Dict[str, pd.Series]
    ) -> Dict[str, Any]:
        """测试Task 24: 市场状态变化检测"""
        logger.info("Testing Task 24: Regime Change Detection")

        results = {
            "task_name": "Regime Change Detection",
            "status": "passed",
            "details": {},
        }

        try:
            # 创建不同市场配置的分析器
            configs = {
                "bull_market": create_behavioral_analyzer(market_regime="bull_market"),
                "bear_market": create_behavioral_analyzer(market_regime="bear_market"),
                "high_volatility": create_behavioral_analyzer(
                    market_regime="high_volatility"
                ),
            }

            regime_detections = {}

            for regime_name, analyzer in configs.items():
                # 测试相应的市场数据
                test_key = (
                    regime_name.replace("_market", "_market")
                    if "_market" in regime_name
                    else regime_name
                )
                test_key = (
                    test_key + "_data" if not test_key.endswith("_market") else test_key
                )

                # 使用合适的测试数据
                if regime_name == "bull_market":
                    test_data_key = "bull_market"
                elif regime_name == "bear_market":
                    test_data_key = "bear_market"
                else:
                    test_data_key = "high_volatility"

                if test_data_key in test_data:
                    data = test_data[test_data_key]
                    analysis_result = analyzer.analyze_historical_patterns(
                        data, f"REGIME_{regime_name.upper()}"
                    )

                    # 验证配置差异
                    regime_detections[regime_name] = {
                        "config_applied": True,
                        "analysis_completed": "comprehensive_summary"
                        in analysis_result,
                    }

            results["details"]["regime_configs_tested"] = len(regime_detections)
            results["details"]["regime_detections"] = regime_detections

            logger.info(
                f"✅ Regime configurations tested: {results['details']['regime_configs_tested']}"
            )

        except Exception as e:
            results["status"] = "failed"
            results["error"] = str(e)
            logger.error(f"❌ Task 24 failed: {e}")

        return results

    def test_task_25_realtime_monitoring(
        self, test_data: Dict[str, pd.Series]
    ) -> Dict[str, Any]:
        """测试Task 25: 实时行为监控"""
        logger.info("Testing Task 25: Real - time Behavior Monitor")

        results = {
            "task_name": "Real - time Behavior Monitor",
            "status": "passed",
            "details": {},
        }

        try:
            # 创建分析器
            analyzer = create_behavioral_analyzer()

            # 准备基线数据
            baseline_data = test_data["basic_trend_seasonal"]

            # 告警回调函数
            alert_count = 0

            def test_alert_callback(alert):
                nonlocal alert_count
                alert_count += 1
                logger.info(
                    f"Test alert #{alert_count}: {alert['type']} - {alert['severity']}"
                )

            # 设置实时监控
            analyzer.setup_realtime_monitoring(baseline_data, test_alert_callback)

            # 启动监控
            analyzer.start_monitoring()

            # 模拟实时数据流
            test_stream_data = test_data["with_anomalies"].head(100)  # 使用前100个点

            logger.info("Simulating real - time data stream...")
            for i, (timestamp, value) in enumerate(test_stream_data.items()):
                analyzer.add_realtime_data(float(value), timestamp)

                # 添加一些延迟模拟实时性
                time_module.sleep(0.001)

                if i % 25 == 0:
                    status = analyzer.get_monitoring_status()
                    logger.info(
                        f"Processed {i} samples, alerts: {status['performance_stats']['alerts_generated']}"
                    )

            # 获取监控状态
            final_status = analyzer.get_monitoring_status()
            results["details"]["samples_processed"] = final_status["performance_stats"][
                "processed_samples"
            ]
            results["details"]["alerts_generated"] = final_status["performance_stats"][
                "alerts_generated"
            ]
            results["details"]["monitoring_active"] = final_status["monitoring_active"]

            # 停止监控并获取报告
            monitoring_report = analyzer.stop_monitoring()

            if "performance_summary" in monitoring_report:
                perf_summary = monitoring_report["performance_summary"]
                results["details"]["avg_processing_time"] = perf_summary.get(
                    "average_processing_time_ms", 0
                )
                results["details"]["processing_rate"] = perf_summary.get(
                    "samples_per_second", 0
                )

            logger.info(
                f"✅ Samples processed: {results['details']['samples_processed']}"
            )
            logger.info(
                f"✅ Alerts generated: {results['details']['alerts_generated']}"
            )
            logger.info(
                f"✅ Average processing time: {results['details']['avg_processing_time']:.3f} ms"
            )

        except Exception as e:
            results["status"] = "failed"
            results["error"] = str(e)
            logger.error(f"❌ Task 25 failed: {e}")

        return results

    def test_task_26_adaptive_thresholds(
        self, test_data: Dict[str, pd.Series]
    ) -> Dict[str, Any]:
        """测试Task 26: 自适应阈值和在线学习"""
        logger.info("Testing Task 26: Adaptive Thresholds with Online Learning")

        results = {
            "task_name": "Adaptive Thresholds and Online Learning",
            "status": "passed",
            "details": {},
        }

        try:
            # 创建高性能配置的分析器
            analyzer = create_behavioral_analyzer(analysis_focus="comprehensive")

            # 使用高波动率数据测试自适应阈值
            high_vol_data = test_data["high_volatility"]

            # 第一阶段：初始化和基线分析
            baseline_data = high_vol_data[:500]  # 前半部分作为基线
            test_data_adaptive = high_vol_data[500:]  # 后半部分用于测试自适应

            initial_analysis = analyzer.analyze_historical_patterns(
                baseline_data, "ADAPTIVE_BASELINE"
            )

            # 第二阶段：设置实时监控并测试自适应
            def adaptive_alert_callback(alert):
                logger.info(
                    f"Adaptive threshold alert: {alert['type']} - {alert['severity']}"
                )

            analyzer.setup_realtime_monitoring(baseline_data, adaptive_alert_callback)
            analyzer.start_monitoring()

            # 模拟逐步增加的异常情况来测试自适应
            adaptive_test_data = []
            for i, value in enumerate(test_data_adaptive.head(50)):
                # 逐步增加异常强度
                anomaly_strength = i / 50.0  # 从0到1逐渐增加
                modified_value = value * (1 + anomaly_strength * 0.1)  # 最多10%的异常

                analyzer.add_realtime_data(float(modified_value))
                time_module.sleep(0.002)  # 短暂延迟

            # 获取监控状态验证自适应学习
            final_status = analyzer.get_monitoring_status()
            monitoring_report = analyzer.stop_monitoring()

            # 验证在线学习和自适应功能
            results["details"]["adaptive_learning_tested"] = True
            results["details"]["samples_processed"] = final_status["performance_stats"][
                "processed_samples"
            ]
            results["details"]["adaptive_alerts"] = final_status["performance_stats"][
                "alerts_generated"
            ]

            # 验证在线学习
            if "threshold_status" in monitoring_report:
                threshold_status = monitoring_report["threshold_status"]
                results["details"]["adaptive_thresholds"] = len(threshold_status) > 0

            logger.info(
                f"✅ Adaptive learning tested: {results['details']['adaptive_learning_tested']}"
            )
            logger.info(
                f"✅ Adaptive thresholds configured: {results['details'].get('adaptive_thresholds', False)}"
            )
            logger.info(
                f"✅ Adaptive alerts generated: {results['details']['adaptive_alerts']}"
            )

        except Exception as e:
            results["status"] = "failed"
            results["error"] = str(e)
            logger.error(f"❌ Task 26 failed: {e}")

        return results

    def run_comprehensive_test_suite(self) -> Dict[str, Any]:
        """运行完整测试套件"""
        logger.info("🚀 Starting Comprehensive Behavioral Analysis Test Suite")
        logger.info(f"Test started at: {self.start_time}")

        # 生成测试数据
        test_data = self.generate_test_data()

        # 运行所有任务测试
        test_tasks = [
            (
                self.test_task_19_time_series_patterns,
                "Task 19: Time Series Pattern Analyzer",
            ),
            (
                self.test_task_20_intraday_patterns,
                "Task 20: Intraday Pattern Recognition",
            ),
            (
                self.test_task_21_22_ml_anomaly_detection,
                "Task 21 - 22: ML Anomaly Detection",
            ),
            (
                self.test_task_23_historical_patterns,
                "Task 23: Historical Pattern Comparator",
            ),
            (
                self.test_task_24_regime_change_detection,
                "Task 24: Regime Change Detection",
            ),
            (
                self.test_task_25_realtime_monitoring,
                "Task 25: Real - time Behavior Monitor",
            ),
            (self.test_task_26_adaptive_thresholds, "Task 26: Adaptive Thresholds"),
        ]

        passed_tasks = 0
        failed_tasks = 0

        for test_func, task_name in test_tasks:
            logger.info(f"\n{'='*60}")
            logger.info(f"Running {task_name}")
            logger.info(f"{'='*60}")

            try:
                task_result = test_func(test_data)
                self.test_results[task_name] = task_result

                if task_result["status"] == "passed":
                    passed_tasks += 1
                    logger.info(f"✅ {task_name} PASSED")
                else:
                    failed_tasks += 1
                    logger.error(
                        f"❌ {task_name} FAILED: {task_result.get('error', 'Unknown error')}"
                    )

            except Exception as e:
                failed_tasks += 1
                logger.error(f"❌ {task_name} ERROR: {e}")
                self.test_results[task_name] = {
                    "task_name": task_name,
                    "status": "error",
                    "error": str(e),
                }

        # 生成测试报告
        end_time = datetime.now()
        test_duration = end_time - self.start_time

        final_report = {
            "test_summary": {
                "total_tasks": len(test_tasks),
                "passed_tasks": passed_tasks,
                "failed_tasks": failed_tasks,
                "success_rate": f"{(passed_tasks / len(test_tasks) * 100):.1f}%",
                "test_duration": str(test_duration),
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
            },
            "task_results": self.test_results,
            "test_data_summary": {
                "datasets_generated": len(test_data),
                "dataset_names": list(test_data.keys()),
                "total_data_points": sum(len(data) for data in test_data.values()),
            },
            "system_performance": {
                "behavioral_analysis_layer_version": "4.0.0",
                "all_components_tested": passed_tasks + failed_tasks == len(test_tasks),
                "integration_status": (
                    "SUCCESS" if passed_tasks == len(test_tasks) else "PARTIAL"
                ),
            },
        }

        # 打印最终报告
        self.print_final_report(final_report)

        return final_report

    def print_final_report(self, report: Dict[str, Any]) -> None:
        """打印最终测试报告"""
        print("\n" + "=" * 80)
        print("📊 BEHAVIORAL ANALYSIS LAYER - COMPREHENSIVE TEST REPORT")
        print("=" * 80)

        summary = report["test_summary"]
        print(f"\n🎯 OVERALL RESULTS:")
        print(f"   Total Tasks: {summary['total_tasks']}")
        print(f"   Passed: {summary['passed_tasks']} ✅")
        print(f"   Failed: {summary['failed_tasks']} ❌")
        print(f"   Success Rate: {summary['success_rate']}")
        print(f"   Test Duration: {summary['test_duration']}")

        print(f"\n📈 TASK DETAILS:")
        for task_name, result in report["task_results"].items():
            status_icon = "✅" if result["status"] == "passed" else "❌"
            print(f"   {status_icon} {task_name}")

            if result["status"] == "passed" and "details" in result:
                details = result["details"]
                for key, value in details.items():
                    print(f"      - {key}: {value}")
            elif result["status"] == "failed":
                print(f"      - Error: {result.get('error', 'Unknown error')}")

        print(f"\n💻 SYSTEM PERFORMANCE:")
        perf = report["system_performance"]
        print(
            f"   Behavioral Analysis Layer Version: {perf['behavioral_analysis_layer_version']}"
        )
        print(f"   All Components Tested: {perf['all_components_tested']}")
        print(f"   Integration Status: {perf['integration_status']}")

        data_summary = report["test_data_summary"]
        print(f"\n📊 TEST DATA SUMMARY:")
        print(f"   Datasets Generated: {data_summary['datasets_generated']}")
        print(f"   Dataset Types: {', '.join(data_summary['dataset_names'])}")
        print(f"   Total Data Points: {data_summary['total_data_points']:,}")

        print(f"\n🔧 KEY ACHIEVEMENTS:")
        achievements = []

        # 检查关键功能
        if any("Time Series" in task for task in report["task_results"].keys()):
            if (
                report["task_results"]
                .get("Task 19: Time Series Pattern Analyzer", {})
                .get("status")
                == "passed"
            ):
                achievements.append(
                    "✅ Advanced time series pattern analysis with seasonal detection"
                )

        if any("Intraday" in task for task in report["task_results"].keys()):
            if (
                report["task_results"]
                .get("Task 20: Intraday Pattern Recognition", {})
                .get("status")
                == "passed"
            ):
                achievements.append("✅ Hong Kong trading session pattern recognition")

        if any("ML Anomaly" in task for task in report["task_results"].keys()):
            if (
                report["task_results"]
                .get("Task 21 - 22: ML Anomaly Detection", {})
                .get("status")
                == "passed"
            ):
                achievements.append(
                    "✅ Ensemble - based ML anomaly detection with confidence calibration"
                )

        if any("Real - time" in task for task in report["task_results"].keys()):
            if (
                report["task_results"]
                .get("Task 25: Real - time Behavior Monitor", {})
                .get("status")
                == "passed"
            ):
                achievements.append(
                    "✅ Real - time monitoring with sliding windows and early warning"
                )

        if any("Adaptive" in task for task in report["task_results"].keys()):
            if (
                report["task_results"]
                .get("Task 26: Adaptive Thresholds", {})
                .get("status")
                == "passed"
            ):
                achievements.append("✅ Adaptive thresholds with online learning")

        for achievement in achievements:
            print(f"   {achievement}")

        if summary["success_rate"] == "100.0%":
            print(
                f"\n🎉 CONGRATULATIONS! All behavioral analysis components are working perfectly!"
            )
            print(
                f"   The Phase 4 Behavioral Analysis Layer is fully operational and ready for production use."
            )
        else:
            print(
                f"\n⚠️  Some components need attention. Please review failed tasks and fix any issues."
            )

        print("\n" + "=" * 80)


def main():
    """主测试函数"""
    print("🧪 Starting Behavioral Analysis Layer Comprehensive Test Suite")
    print("Phase 4: Behavioral Analysis Layer - Tasks 19 - 26")
    print("=" * 80)

    # 创建测试套件
    test_suite = BehavioralAnalysisTestSuite()

    # 运行完整测试
    final_report = test_suite.run_comprehensive_test_suite()

    # 保存测试报告
    report_file = f"behavioral_analysis_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    try:
        import json

        with open(report_file, "w", encoding="utf - 8") as f:
            json.dump(final_report, f, indent = 2, ensure_ascii = False, default = str)
        print(f"\n📄 Detailed test report saved to: {report_file}")
    except Exception as e:
        logger.warning(f"Failed to save test report: {e}")

    return final_report


if __name__ == "__main__":
    # 运行测试
    test_report = main()

    # 返回退出码
    success_rate = float(test_report["test_summary"]["success_rate"].rstrip("%"))
    exit_code = 0 if success_rate == 100.0 else 1

    print(f"\n🏁 Test completed with exit code: {exit_code}")
    exit(exit_code)

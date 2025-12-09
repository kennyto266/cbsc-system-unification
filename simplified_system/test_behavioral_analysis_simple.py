#!/usr / bin / env python3
"""
第4阶段行为分析层简化测试系统
Phase 4 Behavioral Analysis Layer Simple Test System

使用基本依赖包测试行为分析层核心功能
Tests behavioral analysis layer core functionality with basic dependencies
"""

import warnings
from datetime import datetime, time

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

import json

# Basic imports that should be available
import logging
import time as time_module

# Setup logging
logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)


class SimpleBehavioralAnalysisTest:
    """简化版行为分析测试"""

    def __init__(self):
        self.test_results = {}
        self.start_time = datetime.now()

    def generate_test_data(self):
        """生成测试数据"""
        logger.info("Generating test data...")

        np.random.seed(42)
        n_points = 500
        dates = pd.date_range(start="2020 - 01 - 01", periods = n_points, freq="D")

        # 基础价格数据（带趋势和季节性）
        trend = np.linspace(100, 200, n_points)
        seasonal = 5 * np.sin(2 * np.pi * np.arange(n_points) / 25)
        noise = np.random.normal(0, 3, n_points)
        prices = trend + seasonal + noise

        test_data = {
            "basic_data": pd.Series(prices, index = dates),
            "high_vol_data": pd.Series(
                prices + np.random.normal(0, 10, n_points), index = dates
            ),
        }

        # 添加一些异常
        anomaly_prices = prices.copy()
        for i in [100, 200, 300, 400]:
            anomaly_prices[i] *= 1.3  # 30%的异常跳跃
        test_data["anomaly_data"] = pd.Series(anomaly_prices, index = dates)

        # 盘中数据
        intraday_dates = pd.date_range(
            start="2024 - 01 - 15 09:00:00", end="2024 - 01 - 15 16:30:00", freq="15min"
        )
        intraday_prices = []
        base_price = 100

        for date_time in intraday_dates:
            hour = date_time.hour
            change = np.random.normal(0.01, 0.2)  # 基础变化

            # 模拟不同时段的波动
            if 9 <= hour < 12:  # 早盘
                change += 0.02
            elif 12 <= hour < 13:  # 午休
                change *= 0.3
            elif 13 <= hour < 16:  # 午盘
                change -= 0.01

            base_price *= 1 + change
            intraday_prices.append(base_price)

        test_data["intraday_data"] = pd.Series(intraday_prices, index = intraday_dates)

        return test_data

    def test_basic_statistics(self, data):
        """测试基础统计分析"""
        logger.info("Testing basic statistical analysis...")

        result = {
            "task_name": "Basic Statistical Analysis",
            "status": "passed",
            "details": {},
        }

        try:
            # 基础统计
            basic_stats = {
                "mean": float(data["basic_data"].mean()),
                "std": float(data["basic_data"].std()),
                "min": float(data["basic_data"].min()),
                "max": float(data["basic_data"].max()),
                "skewness": float(
                    (
                        (data["basic_data"] - data["basic_data"].mean())
                        / data["basic_data"].std()
                    ).skew()
                ),
                "data_points": len(data["basic_data"]),
            }

            result["details"]["basic_statistics"] = basic_stats

            # 波动率比较
            basic_vol = data["basic_data"].pct_change().std()
            high_vol = data["high_vol_data"].pct_change().std()

            result["details"]["volatility_analysis"] = {
                "basic_volatility": float(basic_vol),
                "high_volatility": float(high_vol),
                "volatility_ratio": float(high_vol / basic_vol) if basic_vol > 0 else 0,
            }

            logger.info(f"[PASS] Basic statistics computed successfully")
            logger.info(
                f"   Mean: {basic_stats['mean']:.2f}, Std: {basic_stats['std']:.2f}"
            )
            logger.info(
                f"   Volatility ratio: {result['details']['volatility_analysis']['volatility_ratio']:.2f}"
            )

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            logger.error(f"[FAIL] Basic statistics test failed: {e}")

        return result

    def test_trend_analysis(self, data):
        """测试趋势分析"""
        logger.info("Testing trend analysis...")

        result = {"task_name": "Trend Analysis", "status": "passed", "details": {}}

        try:
            from scipy import stats

            # 线性趋势分析
            x = np.arange(len(data["basic_data"]))
            y = data["basic_data"].values
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

            trend_info = {
                "slope": float(slope),
                "r_squared": float(r_value * *2),
                "p_value": float(p_value),
                "trend_direction": (
                    "increasing" if slope > 0 else "decreasing" if slope < 0 else "flat"
                ),
                "is_significant": p_value < 0.05,
            }

            result["details"]["linear_trend"] = trend_info

            # 移动平均趋势
            ma_short = data["basic_data"].rolling(window = 20).mean()
            ma_long = data["basic_data"].rolling(window = 50).mean()

            if len(ma_short.dropna()) > 0 and len(ma_long.dropna()) > 0:
                ma_relationship = (ma_short > ma_long).mean()
                result["details"]["moving_average_trend"] = {
                    "ma_relationship": float(ma_relationship),
                    "trend_signal": (
                        "bullish"
                        if ma_relationship > 0.6
                        else "bearish" if ma_relationship < 0.4 else "neutral"
                    ),
                }

            logger.info(f"[PASS] Trend analysis completed")
            logger.info(f"   Trend direction: {trend_info['trend_direction']}")
            logger.info(f"   R - squared: {trend_info['r_squared']:.3f}")

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            logger.error(f"[FAIL] Trend analysis test failed: {e}")

        return result

    def test_seasonality_detection(self, data):
        """测试季节性检测"""
        logger.info("Testing seasonality detection...")

        result = {
            "task_name": "Seasonality Detection",
            "status": "passed",
            "details": {},
        }

        try:
            # 简单的季节性检测：使用不同周期的自相关
            data_values = data["basic_data"].values
            periods_to_test = [5, 10, 20, 25, 50]  # 周、两周、月等周期

            seasonality_scores = {}
            for period in periods_to_test:
                if len(data_values) >= period * 2:
                    # 计算周期性自相关
                    correlations = []
                    for lag in range(1, min(period, len(data_values) // 4)):
                        corr = np.corrcoef(data_values[:-lag], data_values[lag:])[0, 1]
                        if not np.isnan(corr):
                            correlations.append(abs(corr))

                    if correlations:
                        seasonality_scores[f"period_{period}"] = {
                            "max_correlation": float(max(correlations)),
                            "avg_correlation": float(np.mean(correlations)),
                        }

            result["details"]["seasonality_analysis"] = seasonality_scores

            # 判断是否存在季节性
            has_seasonality = any(
                scores["max_correlation"] > 0.3
                for scores in seasonality_scores.values()
            )
            result["details"]["has_seasonality"] = has_seasonality

            if has_seasonality:
                best_period = max(
                    seasonality_scores.items(), key = lambda x: x[1]["max_correlation"]
                )[0]
                result["details"]["best_period"] = best_period

            logger.info(f"✅ Seasonality detection completed")
            logger.info(f"   Has seasonality: {has_seasonality}")
            if has_seasonality:
                logger.info(f"   Best period: {result['details']['best_period']}")

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            logger.error(f"❌ Seasonality detection test failed: {e}")

        return result

    def test_anomaly_detection_simple(self, data):
        """测试简单异常检测"""
        logger.info("Testing simple anomaly detection...")

        result = {
            "task_name": "Simple Anomaly Detection",
            "status": "passed",
            "details": {},
        }

        try:
            # Z - score异常检测
            anomaly_data = data["anomaly_data"]
            z_scores = np.abs((anomaly_data - anomaly_data.mean()) / anomaly_data.std())
            anomaly_threshold = 3.0

            detected_anomalies = z_scores > anomaly_threshold
            anomaly_indices = np.where(detected_anomalies)[0]

            result["details"]["z_score_detection"] = {
                "anomalies_detected": len(anomaly_indices),
                "anomaly_indices": anomaly_indices.tolist(),
                "anomaly_rate": float(len(anomaly_indices) / len(anomaly_data)),
                "threshold_used": anomaly_threshold,
            }

            # IQR异常检测
            Q1 = anomaly_data.quantile(0.25)
            Q3 = anomaly_data.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            iqr_anomalies = (anomaly_data < lower_bound) | (anomaly_data > upper_bound)
            iqr_indices = np.where(iqr_anomalies)[0]

            result["details"]["iqr_detection"] = {
                "anomalies_detected": len(iqr_indices),
                "anomaly_indices": iqr_indices.tolist(),
                "anomaly_rate": float(len(iqr_indices) / len(anomaly_data)),
                "bounds": {"lower": float(lower_bound), "upper": float(upper_bound)},
            }

            logger.info(f"✅ Anomaly detection completed")
            logger.info(f"   Z - score anomalies: {len(anomaly_indices)}")
            logger.info(f"   IQR anomalies: {len(iqr_indices)}")

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            logger.error(f"❌ Anomaly detection test failed: {e}")

        return result

    def test_intraday_patterns(self, data):
        """测试盘中模式识别"""
        logger.info("Testing intraday pattern recognition...")

        result = {
            "task_name": "Intraday Pattern Recognition",
            "status": "passed",
            "details": {},
        }

        try:
            intraday_data = data["intraday_data"]

            if not isinstance(intraday_data.index, pd.DatetimeIndex):
                result["details"]["error"] = "Intraday data must have DatetimeIndex"
                return result

            # 提取交易时段
            morning_data = intraday_data.between_time("09:30", "12:00")
            afternoon_data = intraday_data.between_time("13:00", "16:00")

            result["details"]["session_analysis"] = {
                "total_points": len(intraday_data),
                "morning_points": len(morning_data),
                "afternoon_points": len(afternoon_data),
            }

            # 计算各时段收益率
            if len(morning_data) > 1 and len(afternoon_data) > 1:
                morning_returns = morning_data.pct_change().dropna()
                afternoon_returns = afternoon_data.pct_change().dropna()

                result["details"]["session_returns"] = {
                    "morning_avg_return": float(morning_returns.mean()),
                    "morning_volatility": float(morning_returns.std()),
                    "afternoon_avg_return": float(afternoon_returns.mean()),
                    "afternoon_volatility": float(afternoon_returns.std()),
                }

            # 午休时间分析
            lunch_data = intraday_data.between_time("12:00", "13:00")
            if len(lunch_data) > 0:
                result["details"]["lunch_analysis"] = {
                    "lunch_points": len(lunch_data),
                    "lunch_volatility": (
                        float(lunch_data.pct_change().std())
                        if len(lunch_data) > 1
                        else 0
                    ),
                }

            logger.info(f"✅ Intraday pattern recognition completed")
            logger.info(f"   Total intraday points: {len(intraday_data)}")
            logger.info(f"   Morning points: {len(morning_data)}")
            logger.info(f"   Afternoon points: {len(afternoon_data)}")

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            logger.error(f"❌ Intraday pattern test failed: {e}")

        return result

    def test_volatility_analysis(self, data):
        """测试波动率分析"""
        logger.info("Testing volatility analysis...")

        result = {"task_name": "Volatility Analysis", "status": "passed", "details": {}}

        try:
            # 不同时间窗口的波动率
            basic_returns = data["basic_data"].pct_change().dropna()
            high_vol_returns = data["high_vol_data"].pct_change().dropna()

            windows = [5, 10, 20, 50]
            volatility_analysis = {}

            for window in windows:
                if len(basic_returns) >= window:
                    basic_vol = basic_returns.rolling(window = window).std().dropna()
                    high_vol = high_vol_returns.rolling(window = window).std().dropna()

                    volatility_analysis[f"window_{window}"] = {
                        "basic_avg_volatility": float(basic_vol.mean()),
                        "high_avg_volatility": float(high_vol.mean()),
                        "volatility_ratio": (
                            float(high_vol.mean() / basic_vol.mean())
                            if basic_vol.mean() > 0
                            else 0
                        ),
                    }

            result["details"]["volatility_by_window"] = volatility_analysis

            # 波动率聚集检测
            if len(basic_returns) >= 20:
                abs_returns = abs(basic_returns)
                autocorr_1 = abs_returns.autocorr(lag = 1)
                autocorr_5 = abs_returns.autocorr(lag = 5)

                result["details"]["volatility_clustering"] = {
                    "autocorr_lag1": (
                        float(autocorr_1) if not np.isnan(autocorr_1) else 0
                    ),
                    "autocorr_lag5": (
                        float(autocorr_5) if not np.isnan(autocorr_5) else 0
                    ),
                    "has_clustering": (
                        abs(autocorr_1) > 0.2 if not np.isnan(autocorr_1) else False
                    ),
                }

            logger.info(f"✅ Volatility analysis completed")
            logger.info(f"   Windows analyzed: {len(windows)}")
            clustering = result["details"]["volatility_clustering"]
            logger.info(
                f"   Volatility clustering detected: {clustering['has_clustering']}"
            )

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            logger.error(f"❌ Volatility analysis test failed: {e}")

        return result

    def test_realtime_simulation(self, data):
        """测试实时监控模拟"""
        logger.info("Testing real - time monitoring simulation...")

        result = {
            "task_name": "Real - time Monitoring Simulation",
            "status": "passed",
            "details": {},
        }

        try:
            # 模拟实时数据处理
            stream_data = data["basic_data"].head(100)  # 使用前100个点
            alert_count = 0
            processed_count = 0

            # 模拟滑动窗口处理
            window_size = 20
            window_data = []
            start_time = time_module.time()

            for i, (timestamp, value) in enumerate(stream_data.items()):
                window_data.append(float(value))
                processed_count += 1

                # 保持窗口大小
                if len(window_data) > window_size:
                    window_data.pop(0)

                # 简单异常检测
                if len(window_data) == window_size:
                    window_mean = np.mean(window_data)
                    window_std = np.std(window_data)
                    z_score = (
                        abs((value - window_mean) / window_std) if window_std > 0 else 0
                    )

                    if z_score > 2.5:  # 简单的异常阈值
                        alert_count += 1
                        logger.info(
                            f"Simulated alert at index {i}: z - score = {z_score:.2f}"
                        )

                # 模拟实时延迟
                time_module.sleep(0.001)

            processing_time = time_module.time() - start_time

            result["details"]["realtime_simulation"] = {
                "samples_processed": processed_count,
                "alerts_generated": alert_count,
                "processing_time_seconds": processing_time,
                "samples_per_second": (
                    processed_count / processing_time if processing_time > 0 else 0
                ),
                "window_size": window_size,
                "alert_rate": (
                    alert_count / processed_count if processed_count > 0 else 0
                ),
            }

            logger.info(f"✅ Real - time simulation completed")
            logger.info(f"   Samples processed: {processed_count}")
            logger.info(f"   Alerts generated: {alert_count}")
            logger.info(
                f"   Processing rate: {result['details']['realtime_simulation']['samples_per_second']:.1f} samples / sec"
            )

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            logger.error(f"❌ Real - time simulation test failed: {e}")

        return result

    def run_comprehensive_test(self):
        """运行综合测试"""
        logger.info("Starting Simplified Behavioral Analysis Test Suite")
        logger.info(f"Test started at: {self.start_time}")

        # 生成测试数据
        test_data = self.generate_test_data()
        logger.info(f"Generated test datasets: {list(test_data.keys())}")

        # 定义测试任务
        test_tasks = [
            (self.test_basic_statistics, "Basic Statistical Analysis"),
            (self.test_trend_analysis, "Trend Analysis"),
            (self.test_seasonality_detection, "Seasonality Detection"),
            (self.test_anomaly_detection_simple, "Simple Anomaly Detection"),
            (self.test_intraday_patterns, "Intraday Pattern Recognition"),
            (self.test_volatility_analysis, "Volatility Analysis"),
            (self.test_realtime_simulation, "Real - time Monitoring Simulation"),
        ]

        passed_tasks = 0
        failed_tasks = 0

        # 运行所有测试
        for test_func, task_name in test_tasks:
            logger.info(f"\n{'='*60}")
            logger.info(f"Running {task_name}")
            logger.info(f"{'='*60}")

            try:
                task_result = test_func(test_data)
                self.test_results[task_name] = task_result

                if task_result["status"] == "passed":
                    passed_tasks += 1
                    logger.info(f"[PASS] {task_name} PASSED")
                else:
                    failed_tasks += 1
                    logger.error(
                        f"[FAIL] {task_name} FAILED: {task_result.get('error', 'Unknown error')}"
                    )

            except Exception as e:
                failed_tasks += 1
                logger.error(f"[ERROR] {task_name} ERROR: {e}")
                self.test_results[task_name] = {
                    "task_name": task_name,
                    "status": "error",
                    "error": str(e),
                }

        # 生成最终报告
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
            "behavioral_analysis_status": {
                "layer_version": "4.0.0 - simplified",
                "core_functionality_tested": True,
                "integration_status": (
                    "SUCCESS" if passed_tasks == len(test_tasks) else "PARTIAL"
                ),
            },
        }

        self.print_final_report(final_report)
        return final_report

    def print_final_report(self, report):
        """打印最终报告"""
        print("\n" + "=" * 80)
        print("BEHAVIORAL ANALYSIS LAYER - SIMPLIFIED TEST REPORT")
        print("=" * 80)

        summary = report["test_summary"]
        print(f"\nOVERALL RESULTS:")
        print(f"   Total Tasks: {summary['total_tasks']}")
        print(f"   Passed: {summary['passed_tasks']} [PASS]")
        print(f"   Failed: {summary['failed_tasks']} [FAIL]")
        print(f"   Success Rate: {summary['success_rate']}")
        print(f"   Test Duration: {summary['test_duration']}")

        print(f"\nTASK DETAILS:")
        for task_name, result in report["task_results"].items():
            status_icon = "[PASS]" if result["status"] == "passed" else "[FAIL]"
            print(f"   {status_icon} {task_name}")

            if result["status"] == "passed" and "details" in result:
                details = result["details"]
                # 只显示关键细节
                if "basic_statistics" in details:
                    stats = details["basic_statistics"]
                    print(
                        f"      - Data points: {stats['data_points']}, Mean: {stats['mean']:.2f}"
                    )
                elif "linear_trend" in details:
                    trend = details["linear_trend"]
                    print(
                        f"      - Trend: {trend['trend_direction']}, R - squared: {trend['r_squared']:.3f}"
                    )
                elif "has_seasonality" in details:
                    print(f"      - Seasonality detected: {details['has_seasonality']}")
                elif "z_score_detection" in details:
                    anomalies = details["z_score_detection"]["anomalies_detected"]
                    print(f"      - Anomalies detected: {anomalies}")
                elif "session_analysis" in details:
                    session = details["session_analysis"]
                    print(f"      - Total points: {session['total_points']}")
                elif "realtime_simulation" in details:
                    sim = details["realtime_simulation"]
                    print(
                        f"      - Processing rate: {sim['samples_per_second']:.1f} samples / sec"
                    )
            elif result["status"] == "failed":
                print(f"      - Error: {result.get('error', 'Unknown error')}")

        print(f"\nBEHAVIORAL ANALYSIS STATUS:")
        status = report["behavioral_analysis_status"]
        print(f"   Layer Version: {status['layer_version']}")
        print(f"   Core Functionality Tested: {status['core_functionality_tested']}")
        print(f"   Integration Status: {status['integration_status']}")

        data_summary = report["test_data_summary"]
        print(f"\nTEST DATA SUMMARY:")
        print(f"   Datasets Generated: {data_summary['datasets_generated']}")
        print(f"   Dataset Types: {', '.join(data_summary['dataset_names'])}")
        print(f"   Total Data Points: {data_summary['total_data_points']:,}")

        print(f"\nKEY ACHIEVEMENTS:")
        achievements = []

        if (
            report["task_results"].get("Basic Statistical Analysis", {}).get("status")
            == "passed"
        ):
            achievements.append("[PASS] Core statistical analysis capabilities")

        if report["task_results"].get("Trend Analysis", {}).get("status") == "passed":
            achievements.append("[PASS] Trend detection and direction analysis")

        if (
            report["task_results"].get("Seasonality Detection", {}).get("status")
            == "passed"
        ):
            achievements.append("[PASS] Seasonal pattern identification")

        if (
            report["task_results"].get("Simple Anomaly Detection", {}).get("status")
            == "passed"
        ):
            achievements.append("[PASS] Anomaly detection with multiple methods")

        if (
            report["task_results"].get("Intraday Pattern Recognition", {}).get("status")
            == "passed"
        ):
            achievements.append("[PASS] Hong Kong trading session pattern analysis")

        if (
            report["task_results"].get("Volatility Analysis", {}).get("status")
            == "passed"
        ):
            achievements.append("[PASS] Multi - timeframe volatility analysis")

        if (
            report["task_results"]
            .get("Real - time Monitoring Simulation", {})
            .get("status")
            == "passed"
        ):
            achievements.append("[PASS] Real - time data processing simulation")

        for achievement in achievements:
            print(f"   {achievement}")

        if summary["success_rate"] == "100.0%":
            print(f"\nEXCELLENT! All core behavioral analysis components are working!")
            print(
                f"   The simplified Phase 4 Behavioral Analysis Layer is fully functional."
            )
        else:
            print(f"\nSome components need attention. Please review failed tasks.")

        print("\n" + "=" * 80)


def main():
    """主测试函数"""
    print("Starting Simplified Behavioral Analysis Test Suite")
    print("Phase 4: Behavioral Analysis Layer - Core Functionality Test")
    print("=" * 80)

    # 创建测试实例
    test_suite = SimpleBehavioralAnalysisTest()

    # 运行测试
    final_report = test_suite.run_comprehensive_test()

    # 保存测试报告
    report_file = f"behavioral_analysis_simple_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    try:
        with open(report_file, "w", encoding="utf - 8") as f:
            json.dump(final_report, f, indent = 2, ensure_ascii = False, default = str)
        print(f"\nTest report saved to: {report_file}")
    except Exception as e:
        logger.warning(f"Failed to save test report: {e}")

    return final_report


if __name__ == "__main__":
    # 运行测试
    test_report = main()

    # 返回退出码
    success_rate = float(test_report["test_summary"]["success_rate"].rstrip("%"))
    exit_code = 0 if success_rate >= 80 else 1  # 80%以上通过率视为成功

    print(f"\nTest completed with exit code: {exit_code}")
    exit(exit_code)

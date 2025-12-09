#!/usr / bin / env python3
"""
简单仪表板测试
Simple Dashboard Test

测试仪表板的基本功能
"""

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)


def create_test_data():
    """创建测试数据"""
    dates = pd.date_range(start="2023 - 01 - 01", periods = 100, freq="D")
    np.random.seed(42)

    # 生成模拟价格数据
    base_price = 100.0
    returns = np.random.normal(0.001, 0.02, 100)
    prices = [base_price]

    for ret in returns[1:]:
        new_price = prices[-1] * (1 + ret)
        prices.append(max(new_price, base_price * 0.5))

    data = pd.DataFrame(
        {
            "open": prices,
            "high": [p * 1.02 for p in prices],
            "low": [p * 0.98 for p in prices],
            "close": prices,
            "volume": np.random.uniform(1000000, 5000000, 100),
        },
        index = dates,
    )

    return data


def test_imports():
    """测试模块导入"""
    try:
        logger.info("Testing dashboard imports...")

        from src.dashboard import PerformanceCharts, QuantDashboard, RealTimeUpdater

        logger.info("Dashboard modules imported successfully")

        return True
    except ImportError as e:
        logger.error(f"Import error: {e}")
        return False


def test_performance_charts():
    """测试图表组件"""
    try:
        logger.info("Testing PerformanceCharts...")

        from src.dashboard import PerformanceCharts

        charts = PerformanceCharts()

        # 创建测试数据
        test_data = create_test_data()

        # 测试各种图表
        charts.create_price_chart(test_data)
        logger.info("Price chart created")

        charts.create_performance_radar()
        logger.info("Performance radar created")

        charts.create_returns_distribution(test_data)
        logger.info("Returns distribution created")

        charts.create_drawdown_chart(test_data)
        logger.info("Drawdown chart created")

        return True
    except Exception as e:
        logger.error(f"PerformanceCharts test failed: {e}")
        return False


def test_real_time_updater():
    """测试实时更新器"""
    try:
        logger.info("Testing RealTimeUpdater...")

        from src.dashboard import create_real_time_updater

        updater = create_real_time_updater(update_interval = 1)

        # 测试基本功能
        stats = updater.get_statistics()
        logger.info(f"Updater stats: {stats}")

        # 测试添加 / 移除符号
        updater.add_symbol("TEST.HK")
        updater.remove_symbol("TEST.HK")
        logger.info("Symbol management works")

        return True
    except Exception as e:
        logger.error(f"RealTimeUpdater test failed: {e}")
        return False


def test_dashboard_creation():
    """测试仪表板创建"""
    try:
        logger.info("Testing dashboard creation...")

        from src.dashboard import create_dashboard

        dashboard = create_dashboard(debug = False, port = 8051)
        logger.info("Dashboard created successfully")

        return True
    except Exception as e:
        logger.error(f"Dashboard creation test failed: {e}")
        return False


def main():
    """主测试函数"""
    print("Simple Dashboard Test")
    print("=" * 50)

    tests = [
        ("Import Test", test_imports),
        ("PerformanceCharts Test", test_performance_charts),
        ("RealTimeUpdater Test", test_real_time_updater),
        ("Dashboard Creation Test", test_dashboard_creation),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        result = test_func()
        results.append(result)
        print(f"Status: {'PASS' if result else 'FAIL'}")

    # 总结
    passed = sum(results)
    total = len(results)

    print(f"\n{'=' * 50}")
    print(f"Test Summary: {passed}/{total} tests passed")

    if passed == total:
        print("All tests passed! Dashboard is ready to use.")
        return 0
    else:
        print("Some tests failed. Please check the error messages above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

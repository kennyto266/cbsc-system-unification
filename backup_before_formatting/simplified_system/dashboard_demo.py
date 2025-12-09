#!/usr/bin/env python3
"""
仪表板演示脚本
Dashboard Demo Script

演示量化交易仪表板的功能和使用方法
"""

import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path
import logging
import time

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_demo_data():
    """创建演示数据"""
    logger.info("Creating demo data...")

    # 创建时间序列
    dates = pd.date_range(start='2023-01-01', end='2024-11-01', freq='D')
    n_days = len(dates)

    # 生成价格数据
    np.random.seed(42)
    base_price = 100.0
    returns = np.random.normal(0.0005, 0.02, n_days)  # 日收益率

    # 添加趋势和周期性
    trend = np.linspace(0, 0.3, n_days)  # 30%增长趋势
    seasonal = 0.02 * np.sin(2 * np.pi * np.arange(n_days) / 60)  # 季节性

    # 组合收益率
    total_returns = returns + trend / n_days + seasonal / n_days
    prices = [base_price]

    for ret in total_returns[1:]:
        new_price = prices[-1] * (1 + ret)
        prices.append(max(new_price, base_price * 0.5))

    prices = np.array(prices[:n_days])

    # 创建OHLCV数据
    data = pd.DataFrame({
        'open': prices * (1 + np.random.normal(0, 0.005, n_days)),
        'high': prices * (1 + np.abs(np.random.normal(0, 0.01, n_days))),
        'low': prices * (1 - np.abs(np.random.normal(0, 0.01, n_days))),
        'close': prices,
        'volume': np.random.uniform(1000000, 5000000, n_days)
    }, index=dates)

    # 确保OHLC关系正确
    data['high'] = np.maximum(data['high'], np.maximum(data['open'], data['close']))
    data['low'] = np.minimum(data['low'], np.minimum(data['open'], data['close']))

    logger.info(f"Demo data created: {len(data)} records")
    return data

def test_dashboard_components():
    """测试仪表板组件"""
    logger.info("Testing dashboard components...")

    try:
        # 导入组件
        from src.dashboard import PerformanceCharts, RealTimeUpdater, create_dashboard

        # 测试图表组件
        logger.info("Testing PerformanceCharts...")
        charts = PerformanceCharts()

        # 创建测试数据
        demo_data = create_demo_data()

        # 测试各种图表
        price_chart = charts.create_price_chart(demo_data)
        logger.info("✓ Price chart created successfully")

        performance_radar = charts.create_performance_radar()
        logger.info("✓ Performance radar created successfully")

        returns_dist = charts.create_returns_distribution(demo_data)
        logger.info("✓ Returns distribution created successfully")

        drawdown_chart = charts.create_drawdown_chart(demo_data)
        logger.info("✓ Drawdown chart created successfully")

        correlation_heatmap = charts.create_correlation_heatmap(demo_data)
        logger.info("✓ Correlation heatmap created successfully")

        monthly_heatmap = charts.create_monthly_returns_heatmap(demo_data)
        logger.info("✓ Monthly returns heatmap created successfully")

        # 测试实时更新器
        logger.info("Testing RealTimeUpdater...")
        updater = create_real_time_updater(update_interval=5)

        # 添加测试符号
        updater.add_symbol('0700.HK')
        updater.add_symbol('09988.HK')

        # 测试获取数据
        stats = updater.get_statistics()
        logger.info(f"✓ Updater stats: {stats}")

        logger.info("All dashboard components tested successfully")

        return True

    except Exception as e:
        logger.error(f"Error testing dashboard components: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_demo_dashboard():
    """运行演示仪表板"""
    logger.info("Starting demo dashboard...")

    try:
        from src.dashboard import create_dashboard

        # 创建仪表板
        dashboard = create_dashboard(debug=True, port=8050)

        logger.info("Dashboard created successfully")
        logger.info("Starting dashboard on http://127.0.0.1:8050")
        logger.info("Press Ctrl+C to stop")

        # 运行仪表板
        dashboard.run()

    except KeyboardInterrupt:
        logger.info("Dashboard stopped by user")
    except Exception as e:
        logger.error(f"Error running demo dashboard: {e}")
        import traceback
        traceback.print_exc()

def test_system_integration():
    """测试系统集成"""
    logger.info("Testing system integration...")

    try:
        # 测试API集成
        from src.api.stock_api import get_hk_stock_data, get_multiple_stocks

        # 尝试获取真实数据（如果API可用）
        try:
            real_data = get_hk_stock_data('0700.HK', 30)
            logger.info(f"✓ Real stock data obtained: {len(real_data)} records")
            data_to_use = real_data
        except Exception as e:
            logger.warning(f"Could not get real data: {e}, using demo data")
            data_to_use = create_demo_data()

        # 测试技术指标集成
        from src.indicators.core_indicators import CoreIndicators
        indicators = CoreIndicators()

        rsi = indicators.calculate_rsi(data_to_use['close'], 14)
        logger.info(f"✓ RSI calculated: {rsi.iloc[-1]:.2f}")

        sma = indicators.calculate_sma(data_to_use['close'], 20)
        logger.info(f"✓ SMA calculated: {sma.iloc[-1]:.2f}")

        # 测试回测引擎集成
        from src.backtest.vectorbt_engine import VectorBTEngine
        engine = VectorBTEngine()

        result = engine.backtest_strategy(
            data=data_to_use,
            strategy="RSI_MEAN_REVERSION",
            parameters={'period': 14, 'oversold': 30, 'overbought': 70},
            symbol="DEMO_STOCK"
        )

        logger.info(f"✓ Backtest completed: Return={result.total_return:.2%}, Sharpe={result.sharpe_ratio:.3f}")

        # 测试图表组件与真实数据的集成
        from src.dashboard import PerformanceCharts
        charts = PerformanceCharts()

        test_chart = charts.create_price_chart(data_to_use)
        logger.info("✓ Price chart created with real data")

        logger.info("System integration test passed")

        return True

    except Exception as e:
        logger.error(f"Error in system integration test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("=" * 80)
    print("Quantitative Trading Dashboard Demo")
    print("=" * 80)

    # 测试组件
    print("\n1. Testing dashboard components...")
    components_ok = test_dashboard_components()

    # 测试系统集成
    print("\n2. Testing system integration...")
    integration_ok = test_system_integration()

    if components_ok and integration_ok:
        print("\n✓ All tests passed!")
        print("\n3. Starting demo dashboard...")
        print("   URL: http://127.0.0.1:8050")
        print("   Press Ctrl+C to stop")
        print("\nDashboard Features:")
        print("   - Real-time price charts")
        print("   - Technical indicator analysis")
        print("   - Performance metrics monitoring")
        print("   - Backtest results display")
        print("   - Risk analysis charts")
        print("   - Interactive data exploration")

        # 启动仪表板
        run_demo_dashboard()
    else:
        print("\n✗ Tests failed, please check error messages")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
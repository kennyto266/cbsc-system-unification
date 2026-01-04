"""
Risk Monitor Demo

This demo shows how to use the real-time risk monitoring system.
"""

import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from src.risk_monitor import RiskEngine, RiskConfig
from src.risk_monitor.risk_calculators import (
    VaRCalculator,
    ExpectedShortfallCalculator,
    MaxDrawdownCalculator,
    VolatilityCalculator
)


async def demo_risk_calculations():
    """Demonstrate risk calculation features"""
    print("\n=== 風險計算演示 ===\n")

    # Generate sample portfolio data
    np.random.seed(42)
    dates = pd.date_range(end=datetime.now(), periods=500, freq="D")
    returns = pd.Series(
        np.random.normal(0.001, 0.02, 500),
        index=dates
    )

    # Initialize calculators
    var_calc = VaRCalculator(confidence_levels=[0.95, 0.99])
    es_calc = ExpectedShortfallCalculator(confidence_levels=[0.95, 0.99])
    dd_calc = MaxDrawdownCalculator()
    vol_calc = VolatilityCalculator()

    # Calculate VaR
    var_95_hist = var_calc.calculate_historical_var(returns, 0.95)
    var_99_hist = var_calc.calculate_historical_var(returns, 0.99)
    var_95_param = var_calc.calculate_parametric_var(returns, 0.95, "normal")
    var_mc = var_calc.calculate_monte_carlo_var(returns, 0.95, n_simulations=10000)

    print(f"VaR (95% - Historical): {var_95_hist:.2%}")
    print(f"VaR (99% - Historical): {var_99_hist:.2%}")
    print(f"VaR (95% - Parametric): {var_95_param:.2%}")
    print(f"VaR (95% - Monte Carlo): {var_mc:.2%}")

    # Calculate Expected Shortfall
    es_95_hist = es_calc.calculate_historical_es(returns, 0.95)
    es_99_hist = es_calc.calculate_historical_es(returns, 0.99)

    print(f"\nExpected Shortfall (95%): {es_95_hist:.2%}")
    print(f"Expected Shortfall (99%): {es_99_hist:.2%}")

    # Calculate volatility
    vol_20d = vol_calc.calculate_returns_volatility(returns, window=20)
    vol_60d = vol_calc.calculate_returns_volatility(returns, window=60)
    vol_252d = vol_calc.calculate_returns_volatility(returns, window=252)

    print(f"\n波動率 (20日): {vol_20d:.2%}")
    print(f"波動率 (60日): {vol_60d:.2%}")
    print(f"波動率 (252日): {vol_252d:.2%}")

    # Calculate max drawdown
    prices = pd.Series(100 * np.exp(np.cumsum(returns)))
    dd_metrics = dd_calc.calculate_max_drawdown(prices)

    print(f"\n最大回撤: {dd_metrics['max_drawdown']:.2%}")
    print(f"當前回撤: {dd_metrics['current_drawdown']:.2%}")
    print(f"回撤持續天數: {dd_metrics['max_drawdown_duration']}")


async def demo_risk_engine():
    """Demonstrate risk engine functionality"""
    print("\n=== 風險引擎演示 ===\n")

    # Create configuration
    config = RiskConfig()
    config.calculation_interval = 2  # 2 seconds for demo
    config.alert_enabled = True

    # Create risk engine
    engine = RiskEngine(config)

    # Add sample portfolios
    portfolios = {
        "tech_portfolio": {
            "name": "科技股投資組合",
            "positions": {
                "AAPL": 0.4,
                "MSFT": 0.3,
                "GOOGL": 0.3
            }
        },
        "balanced_portfolio": {
            "name": "平衡型投資組合",
            "positions": {
                "SPY": 0.5,
                "AGG": 0.3,
                "GLD": 0.2
            }
        }
    }

    for portfolio_id, info in portfolios.items():
        engine.add_portfolio(portfolio_id, info)
        print(f"已添加投資組合: {info['name']} ({portfolio_id})")

    # Simulate some risk calculations
    for portfolio_id in portfolios.keys():
        # Generate sample data
        returns = pd.Series(
            np.random.normal(0.001, 0.015, 100),
            index=pd.date_range(end=datetime.now(), periods=100, freq="D")
        )

        portfolio_data = pd.DataFrame({"returns": returns})

        # Calculate risk metrics
        metrics = await engine._calculate_risk_metrics(portfolio_id, portfolio_data)

        print(f"\n{portfolios[portfolio_id]['name']} 風險指標:")
        print(f"  VaR (95%): {metrics.get('var_95_historical', 0):.2%}")
        print(f"  波動率 (20日): {metrics.get('volatility_20d', 0):.2%}")
        print(f"  最大回撤: {metrics.get('max_drawdown', 0):.2%}")

    # Display risk summary
    summary = engine.get_risk_summary()
    print(f"\n系統概要:")
    print(f"  監控投資組合數: {summary['monitored_portfolios']}")
    print(f"  活躍警報數: {summary['active_alerts']}")
    print(f"  計算間隔: {summary['calculation_interval']}秒")


async def demo_alerts():
    """Demonstrate alert system"""
    print("\n=== 警報系統演示 ===\n")

    from src.risk_monitor.alert_system import AlertSystem, AlertLevel, AlertType

    # Create alert system
    alert_system = AlertSystem()

    # Generate some sample alerts
    sample_metrics = {
        "var_95": 0.06,  # 6% - exceeds warning threshold
        "max_drawdown": 0.25,  # 25% - exceeds error threshold
        "volatility": 0.45  # 45% - exceeds critical threshold
    }

    print("檢查風險指標並生成警報...")
    alerts = alert_system.check_metrics(
        metrics=sample_metrics,
        portfolio_id="demo_portfolio"
    )

    print(f"\n生成 {len(alerts)} 個警報:")
    for alert in alerts:
        print(f"\n  [{alert.level.value.upper()}] {alert.title}")
        print(f"  消息: {alert.message}")
        print(f"  指標: {alert.metric_name}")
        print(f"  數值: {alert.metric_value:.2%}")
        print(f"  閾值: {alert.threshold_value:.2%}")

    # Display alert statistics
    stats = alert_system.get_alert_statistics()
    print(f"\n警報統計:")
    print(f"  活躍警報: {stats['active_alerts']}")
    print(f"  警告級別: {stats['active_by_level']['warning']}")
    print(f"  錯誤級別: {stats['active_by_level']['error']}")
    print(f"  嚴重級別: {stats['active_by_level']['critical']}")


async def main():
    """Main demo function"""
    print("=" * 50)
    print("實時風險監控系統演示")
    print("=" * 50)

    # Run demos
    await demo_risk_calculations()
    await demo_risk_engine()
    await demo_alerts()

    print("\n" + "=" * 50)
    print("演示完成！")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
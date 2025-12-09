"""
Analysis Engines Usage Example
分析引擎使用示例

Demonstrates how to use the newly refactored analysis engines.
展示如何使用新重構的分析引擎。
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from engines.technical.technical_analysis_engine import TechnicalAnalysisEngine
from engines.backtest.backtest_engine import BacktestEngine, BacktestConfig
from engines.backtest.strategy import SMACrossoverStrategy, RSIStrategy
from engines.risk.risk_assessment_engine import RiskAssessmentEngine


async def technical_analysis_example():
    """Example of using Technical Analysis Engine."""
    print("=== Technical Analysis Engine Example ===")

    # Initialize the engine
    tech_engine = TechnicalAnalysisEngine()

    # Sample market data
    sample_data = {
        "symbol": "EXAMPLE",
        "data": [
            {"timestamp": "2024-01-01", "open": 100, "high": 105, "low": 95, "close": 102, "volume": 1000000},
            {"timestamp": "2024-01-02", "open": 102, "high": 108, "low": 100, "close": 106, "volume": 1200000},
            # ... Add more data points for proper analysis
        ] * 30  # Repeat to have enough data points
    }

    # Execute technical analysis
    result = await tech_engine.execute(sample_data, include_patterns=True)

    if result.success:
        print("✓ Technical analysis completed successfully")
        print(f"  - Latest price: {result.data['latest_price']}")
        print(f"  - Trend: {result.data['trend_analysis']['direction']} ({result.data['trend_analysis']['strength']})")
        print(f"  - Overall signal: {result.data['signals']['overall_signal']} (Confidence: {result.data['signals']['confidence']}%)")

        # Display some indicators
        indicators = result.data.get('indicators', {})
        if 'sma_20' in indicators:
            print(f"  - SMA(20): {indicators['sma_20']:.2f}")
        if 'rsi' in indicators:
            print(f"  - RSI: {indicators['rsi']:.2f}")
    else:
        print(f"✗ Technical analysis failed: {result.error}")

    print()


async def backtest_engine_example():
    """Example of using Backtest Engine."""
    print("=== Backtest Engine Example ===")

    # Initialize the engine with custom configuration
    backtest_config = BacktestConfig(
        initial_capital=100000,
        commission_rate=0.001,
        position_sizing_method="percentage"
    )

    backtest_engine = BacktestEngine(backtest_config=backtest_config)

    # Create sample strategies
    sma_strategy = SMACrossoverStrategy(fast_period=10, slow_period=30)
    rsi_strategy = RSIStrategy(period=14, oversold=30, overbought=70)

    # Sample market data (would normally come from a data source)
    market_data = {
        "AAPL": [
            {"timestamp": "2024-01-01", "open": 150, "high": 155, "low": 148, "close": 152, "volume": 50000000},
            {"timestamp": "2024-01-02", "open": 152, "high": 158, "low": 150, "close": 156, "volume": 55000000},
        ] * 60  # 60 days of data
    }

    # Execute backtest
    backtest_data = {
        "market_data": market_data,
        "strategies": [sma_strategy, rsi_strategy]
    }

    result = await backtest_engine.execute(backtest_data)

    if result.success:
        summary = result.data["summary"]
        print("✓ Backtest completed successfully")
        print(f"  - Final equity: ${summary['final_equity']:,.2f}")
        print(f"  - Total return: {summary['total_return']:.2f}%")
        print(f"  - Total trades: {summary['total_trades']}")
        print(f"  - Win rate: {summary['win_rate']:.2f}%")
        print(f"  - Max drawdown: {summary['max_drawdown']:.2f}%")
        print(f"  - Sharpe ratio: {summary['sharpe_ratio']:.4f}")

        # Show recent trades
        trades = result.data["trades"]
        if trades:
            print(f"  - Recent trades: {len(trades)}")
    else:
        print(f"✗ Backtest failed: {result.error}")

    print()


async def risk_assessment_example():
    """Example of using Risk Assessment Engine."""
    print("=== Risk Assessment Engine Example ===")

    # Initialize the engine
    risk_engine = RiskAssessmentEngine()

    # Sample portfolio data
    portfolio_data = {
        "portfolio": {
            "AAPL": {"value": 50000, "quantity": 300},
            "GOOGL": {"value": 30000, "quantity": 200},
            "MSFT": {"value": 20000, "quantity": 150}
        },
        "market_data": {
            "AAPL": [
                {"timestamp": "2024-01-01", "close": 150, "volume": 50000000},
                {"timestamp": "2024-01-02", "close": 152, "volume": 55000000},
            ] * 30
        },
        "benchmark_data": {
            "close": [100, 101, 99, 102, 103, 98, 105] * 10  # Sample benchmark returns
        }
    }

    # Execute risk assessment
    result = await risk_engine.execute(
        portfolio_data,
        include_stress_test=True,
        risk_tolerance="medium"
    )

    if result.success:
        assessment_data = result.data
        portfolio_summary = assessment_data["portfolio_summary"]
        risk_metrics = assessment_data["risk_metrics"]

        print("✓ Risk assessment completed successfully")
        print(f"  - Total portfolio value: ${portfolio_summary['total_value']:,.2f}")
        print(f"  - Risk level: {portfolio_summary['risk_level']}")
        print(f"  - Risk score: {portfolio_summary['risk_score']}/100")

        # Market risk metrics
        market_risk = risk_metrics["market_risk"]
        print(f"  - VaR (95%, 1-day): {market_risk['var_1day_95']:.2f}%")
        print(f"  - VaR (99%, 1-day): {market_risk['var_1day_99']:.2f}%")

        # Drawdown risk
        drawdown_risk = risk_metrics["drawdown_risk"]
        print(f"  - Current drawdown: {drawdown_risk['current']:.2f}%")
        print(f"  - Maximum drawdown: {drawdown_risk['maximum']:.2f}%")

        # Risk alerts
        alerts = assessment_data["risk_alerts"]
        if alerts:
            print(f"  - Risk alerts generated: {len(alerts)}")
            for alert in alerts[:2]:  # Show first 2 alerts
                print(f"    * {alert['message']}")

        # Recommendations
        recommendations = assessment_data["recommendations"]
        if recommendations:
            print(f"  - Recommendations: {len(recommendations)}")
            for rec in recommendations[:2]:  # Show first 2 recommendations
                print(f"    * {rec}")
    else:
        print(f"✗ Risk assessment failed: {result.error}")

    print()


async def engine_health_check_example():
    """Example of performing health checks on engines."""
    print("=== Engine Health Check Example ===")

    engines = [
        TechnicalAnalysisEngine(),
        BacktestEngine(),
        RiskAssessmentEngine()
    ]

    for engine in engines:
        health = await engine.health_check()
        status = health["status"]

        if status == "healthy":
            print(f"✓ {engine.config.name} - Healthy")
        else:
            print(f"✗ {engine.config.name} - Unhealthy: {health.get('error', 'Unknown error')}")

    print()


async def main():
    """Main function to run all examples."""
    print("Analysis Engines Usage Examples")
    print("=" * 50)
    print()

    try:
        await technical_analysis_example()
        await backtest_engine_example()
        await risk_assessment_example()
        await engine_health_check_example()

        print("All examples completed successfully!")

    except Exception as e:
        print(f"Example execution failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
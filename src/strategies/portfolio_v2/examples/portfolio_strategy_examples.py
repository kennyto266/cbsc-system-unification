"""
Portfolio Strategy Usage Examples
組合策略使用示例

This file demonstrates how to use the portfolio management strategies.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List

# Import strategies
from ..multi_factor_strategy import MultiFactorStrategy
from ..risk_parity_strategy import RiskParityStrategy
from ..dynamic_allocation_strategy import DynamicAllocationStrategy
from ...enhanced_factory import StrategyMetadata, StrategyType
from ...enhanced_factory_v2 import StrategyFactoryV2, create_strategy
from uuid import uuid4


def create_sample_portfolio_data(days: int = 252) -> Dict[str, pd.DataFrame]:
    """
    創建投資組合樣本數據

    Args:
        days: Number of days of data

    Returns:
        Dictionary of asset data
    """
    # 定義資產列表
    assets = ["SPY", "QQQ", "IWM", "EFA", "EEM", "GLD", "TLT", "HYG"]

    dates = pd.date_range(start=datetime.now() - timedelta(days=days),
                          periods=days, freq="D")

    data = {}
    np.random.seed(42)  # 確保可重複性

    # 為每個資產創建不同的特徵
    asset_params = {
        "SPY": {"trend": 0.0005, "vol": 0.015, "initial_price": 100},
        "QQQ": {"trend": 0.0008, "vol": 0.020, "initial_price": 120},
        "IWM": {"trend": 0.0003, "vol": 0.018, "initial_price": 80},
        "EFA": {"trend": 0.0002, "vol": 0.012, "initial_price": 50},
        "EEM": {"trend": 0.0004, "vol": 0.022, "initial_price": 40},
        "GLD": {"trend": -0.0001, "vol": 0.015, "initial_price": 150},
        "TLT": {"trend": 0.0001, "vol": 0.010, "initial_price": 100},
        "HYG": {"trend": 0.0003, "vol": 0.008, "initial_price": 90}
    }

    for symbol, params in asset_params.items():
        # 生成價格數據
        prices = [params["initial_price"]]
        returns = []

        for i in range(days - 1):
            # 生成收益率
            daily_return = np.random.normal(params["trend"], params["vol"])
            returns.append(daily_return)
            prices.append(prices[-1] * (1 + daily_return))

        # 創建OHLCV數據
        ohlcv_data = []
        for i, date in enumerate(dates):
            close_price = prices[i]
            # 添加一些隨機性到OHLC
            high = close_price * (1 + abs(np.random.normal(0, 0.01)))
            low = close_price * (1 - abs(np.random.normal(0, 0.01)))
            open_price = close_price * (1 + np.random.normal(0, 0.005))
            volume = np.random.randint(1000000, 10000000)

            ohlcv_data.append({
                "open": open_price,
                "high": high,
                "low": low,
                "close": close_price,
                "volume": volume
            })

        df = pd.DataFrame(ohlcv_data, index=dates)
        data[symbol] = df

    return data


def example_1_multi_factor_strategy():
    """示例1: 多因子組合策略"""
    print("\n=== 示例1: 多因子組合策略 ===")

    # 創建策略元數據
    metadata = StrategyMetadata(
        name="multi_factor_portfolio",
        strategy_type=StrategyType.PORTFOLIO,
        description="Multi-factor portfolio combining MA, RSI, and ADX",
        version="2.0.0",
        author="Portfolio Manager",
        parameters={}
    )

    # 配置多因子策略
    config = {
        "factors": [
            {
                "name": "ma_crossover",
                "weight": 0.4,
                "config": {
                    "fast_period": 10,
                    "slow_period": 20,
                    "symbols": ["SPY", "QQQ", "IWM", "EFA"]
                }
            },
            {
                "name": "rsi",
                "weight": 0.3,
                "config": {
                    "period": 14,
                    "oversold_threshold": 30,
                    "overbought_threshold": 70,
                    "symbols": ["SPY", "QQQ", "IWM", "EFA"]
                }
            },
            {
                "name": "adx",
                "weight": 0.3,
                "config": {
                    "period": 14,
                    "trend_threshold": 25,
                    "symbols": ["SPY", "QQQ", "IWM", "EFA"]
                }
            }
        ],
        "rebalance_frequency": "M",
        "min_positions": 2,
        "max_positions": 6,
        "signal_threshold": 0.5
    }

    # 創建策略實例
    strategy = MultiFactorStrategy(
        instance_id=uuid4(),
        config=config,
        metadata=metadata
    )

    print(f"創建多因子策略: {strategy.STRATEGY_NAME}")
    print(f"因子數量: {len(strategy.factor_strategies)}")
    print(f"因子列表: {list(strategy.factor_strategies.keys())}")

    # 生成數據
    data = create_sample_portfolio_data(100)
    filtered_data = {k: v for k, v in data.items() if k in ["SPY", "QQQ", "IWM", "EFA"]}

    # 執行策略
    result = strategy.execute(filtered_data)

    print(f"\n執行結果:")
    print(f"- 策略ID: {result['strategy_id']}")
    print(f"- 執行時間: {result['execution_time']:.4f}秒")

    if '_portfolio' in result['results']:
        portfolio = result['results']['_portfolio']
        if 'status' in portfolio:
            status = portfolio['status']
            print(f"- 當前權重: {status.get('current_weights', {})}")
            print(f"- 活躍持倉: {status.get('active_positions', 0)}")

    # 獲取因子分析
    analysis = strategy.get_factor_analysis()
    print(f"\n因子分析:")
    print(f"- 因子數量: {analysis['factor_count']}")
    print(f"- 組合方法: {analysis['combination_method']}")
    for factor in analysis['factors']:
        print(f"  - {factor['name']}: 權重={factor['weight']:.2f}")


def example_2_risk_parity_strategy():
    """示例2: 風險平價策略"""
    print("\n=== 示例2: 風險平價策略 ===")

    # 創建策略元數據
    metadata = StrategyMetadata(
        name="risk_parity_portfolio",
        strategy_type=StrategyType.PORTFOLIO,
        description="Risk parity portfolio with equal risk contributions",
        version="2.0.0",
        author="Risk Manager",
        parameters={}
    )

    # 配置風險平價策略
    config = {
        "assets": [
            ("SPY", {}),
            ("QQQ", {}),
            ("IWM", {}),
            ("EFA", {}),
            ("GLD", {}),
            ("TLT", {})
        ],
        "rebalance_frequency": "M",
        "risk_target": 0.15,
        "lookback_period": 60,
        "max_weight": 0.4,
        "min_weight": 0.05,
        "risk_parity_method": "iterative",
        "correlation_adjustment": True
    }

    # 創建策略實例
    strategy = RiskParityStrategy(
        instance_id=uuid4(),
        config=config,
        metadata=metadata
    )

    print(f"創建風險平價策略: {strategy.STRATEGY_NAME}")
    print(f"資產數量: {len(strategy.asset_symbols)}")
    print(f"目標波動率: {strategy.risk_target:.1%}")
    print(f"風險平價方法: {strategy.risk_parity_method}")

    # 生成數據
    data = create_sample_portfolio_data(100)
    filtered_data = {k: v for k, v in data.items() if k in strategy.asset_symbols}

    # 執行策略
    result = strategy.execute(filtered_data)

    print(f"\n執行結果:")
    print(f"- 策略ID: {result['strategy_id']}")
    print(f"- 執行時間: {result['execution_time']:.4f}秒")

    if '_portfolio' in result['results']:
        portfolio = result['results']['_portfolio']
        if 'status' in portfolio:
            status = portfolio['status']
            print(f"- 當前權重: {status.get('current_weights', {})}")

        # 獲取風險指標
        risk_metrics = strategy.get_risk_metrics(filtered_data)
        if risk_metrics:
            print(f"\n風險指標:")
            print(f"- 組合波動率: {risk_metrics.get('portfolio_volatility', 0):.2%}")
            print(f"- 多樣化比率: {risk_metrics.get('diversification_ratio', 0):.2f}")
            print(f"- 有效投注數: {risk_metrics.get('effective_number_of_bets', 0):.1f}")


def example_3_dynamic_allocation_strategy():
    """示例3: 動態資產配置策略"""
    print("\n=== 示例3: 動態資產配置策略 ===")

    # 創建策略元數據
    metadata = StrategyMetadata(
        name="dynamic_allocation_portfolio",
        strategy_type=StrategyType.PORTFOLIO,
        description="Dynamic asset allocation with regime detection",
        version="2.0.0",
        author="Dynamic Allocator",
        parameters={}
    )

    # 配置動態配置策略
    config = {
        "assets": [
            ("SPY", {}),
            ("QQQ", {}),
            ("IWM", {}),
            ("EFA", {}),
            ("EEM", {}),
            ("GLD", {}),
            ("TLT", {})
        ],
        "rebalance_frequency": "W",
        "volatility_window": 20,
        "momentum_window": 60,
        "aggressive_vol_threshold": 0.25,
        "defensive_vol_threshold": 0.15,
        "momentum_threshold": 0.02,
        "max_concentration": 0.5,
        "min_diversification": 5,
        "trend_following_weight": 0.6,
        "mean_reversion_weight": 0.4,
        "regime_detection_method": "combined"
    }

    # 創建策略實例
    strategy = DynamicAllocationStrategy(
        instance_id=uuid4(),
        config=config,
        metadata=metadata
    )

    print(f"創建動態配置策略: {strategy.STRATEGY_NAME}")
    print(f"資產數量: {len(config['assets'])}")
    print(f"再平衡頻率: {strategy.rebalance_frequency}")
    print(f"動量窗口: {strategy.mom_window}天")
    print(f"波動率窗口: {strategy.vol_window}天")

    # 生成數據
    data = create_sample_portfolio_data(150)

    # 執行策略
    result = strategy.execute(data)

    print(f"\n執行結果:")
    print(f"- 策略ID: {result['strategy_id']}")
    print(f"- 執行時間: {result['execution_time']:.4f}秒")

    # 獲取體系分析
    regime_analysis = strategy.get_regime_analysis()
    print(f"\n體系分析:")
    print(f"- 當前體系: {regime_analysis.get('current_regime', 'unknown')}")
    print(f"- 體系變化次數: {regime_analysis.get('regime_changes', 0)}")

    if 'regime_distribution' in regime_analysis:
        print("- 體系分布:")
        for regime, pct in regime_analysis['regime_distribution'].items():
            print(f"  - {regime}: {pct:.1%}")

    # 獲取動量分數
    momentum_scores = strategy.calculate_momentum_scores(data)
    print(f"\n動量分數 (前5個資產):")
    for symbol, scores in list(momentum_scores.items())[:5]:
        print(f"- {symbol}:")
        print(f"  - 價格動量: {scores.get('price_momentum', 0):.2%}")
        print(f"  - 收益率動量: {scores.get('return_momentum', 0):.2%}")
        print(f"  - 趨勢強度: {scores.get('trend_strength', 0):.3f}")


def example_4_portfolio_comparison():
    """示例4: 組合策略比較"""
    print("\n=== 示例4: 組合策略比較 ===")

    # 生成共享數據
    data = create_sample_portfolio_data(100)
    asset_list = ["SPY", "QQQ", "IWM", "EFA", "GLD", "TLT"]
    filtered_data = {k: v for k, v in data.items() if k in asset_list}

    # 定義策略配置
    strategies_config = [
        {
            "name": "Multi-Factor",
            "class": MultiFactorStrategy,
            "config": {
                "factors": [
                    {"name": "ma_crossover", "weight": 0.5, "config": {"fast_period": 10, "slow_period": 20}},
                    {"name": "rsi", "weight": 0.5, "config": {"period": 14, "oversold_threshold": 30, "overbought_threshold": 70}}
                ],
                "rebalance_frequency": "M"
            }
        },
        {
            "name": "Risk Parity",
            "class": RiskParityStrategy,
            "config": {
                "assets": [(s, {}) for s in asset_list[:4]],
                "risk_target": 0.12,
                "rebalance_frequency": "M"
            }
        },
        {
            "name": "Dynamic Allocation",
            "class": DynamicAllocationStrategy,
            "config": {
                "assets": [(s, {}) for s in asset_list],
                "rebalance_frequency": "W",
                "momentum_threshold": 0.015
            }
        }
    ]

    # 執行所有策略
    results = {}
    for strategy_config in strategies_config:
        metadata = StrategyMetadata(
            name=strategy_config["name"].lower().replace(" ", "_"),
            strategy_type=StrategyType.PORTFOLIO,
            description=f"{strategy_config['name']} portfolio strategy",
            version="2.0.0",
            author="Portfolio Manager",
            parameters={}
        )

        strategy = strategy_config["class"](
            instance_id=uuid4(),
            config=strategy_config["config"],
            metadata=metadata
        )

        result = strategy.execute(filtered_data)
        results[strategy_config["name"]] = {
            "strategy": strategy,
            "result": result
        }

        print(f"\n{strategy_config['name']}:")
        print(f"- 執行時間: {result['execution_time']:.4f}秒")

        if '_portfolio' in result['results']:
            portfolio = result['results']['_portfolio']
            if 'status' in portfolio and 'current_weights' in portfolio['status']:
                weights = portfolio['status']['current_weights']
                print(f"- 持倉數量: {len(weights)}")
                print(f"- 最大權重: {max(weights.values()) if weights else 0:.2%}")

    # 比較結果
    print("\n=== 策略比較總結 ===")
    print("\n持倉分布:")
    for name, data in results.items():
        if '_portfolio' in data['result']['results']:
            portfolio = data['result']['results']['_portfolio']
            if 'status' in portfolio and 'current_weights' in portfolio['status']:
                weights = portfolio['status']['current_weights']
                top_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)[:3]
                print(f"\n{name}:")
                for asset, weight in top_weights:
                    print(f"  - {asset}: {weight:.2%}")


def example_5_using_factory():
    """示例5: 使用策略工廠創建組合策略"""
    print("\n=== 示例5: 使用策略工廠創建組合策略 ===")

    # 使用工廠創建風險平價策略
    factory = StrategyFactoryV2()

    # 獲取所有組合策略
    portfolio_strategies = factory.get_strategies_by_type(StrategyType.PORTFOLIO)
    print(f"可用的組合策略: {list(portfolio_strategies.keys())}")

    # 創建風險平價策略
    risk_parity = factory.create_strategy("risk_parity", {
        "assets": [
            ("SPY", {}),
            ("QQQ", {}),
            ("IWM", {}),
            ("EFA", {})
        ],
        "risk_target": 0.15,
        "rebalance_frequency": "M"
    })

    print(f"\n創建策略: {risk_parity.STRATEGY_NAME}")
    print(f"策略類型: {risk_parity.STRATEGY_TYPE}")

    # 執行策略
    data = create_sample_portfolio_data(50)
    filtered_data = {k: v for k, v in data.items() if k in ["SPY", "QQQ", "IWM", "EFA"]}

    result = risk_parity.execute(filtered_data)
    print(f"\n執行完成，耗時: {result['execution_time']:.4f}秒")


def run_all_examples():
    """運行所有示例"""
    print("🚀 Portfolio Strategy Usage Examples")
    print("=" * 50)

    try:
        example_1_multi_factor_strategy()
        example_2_risk_parity_strategy()
        example_3_dynamic_allocation_strategy()
        example_4_portfolio_comparison()
        example_5_using_factory()

        print("\n✅ 所有示例執行完成")

    except Exception as e:
        print(f"\n❌ 示例執行失敗: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_examples()
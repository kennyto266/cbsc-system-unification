#!/usr/bin/env python3
"""
動態資產配置系統 - 使用示例
Dynamic Asset Allocation System - Usage Examples

展示如何使用動態資產配置系統的完整示例
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List

# 添加項目路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.backtest.dynamic_allocator import (
    DynamicAssetAllocator,
    AssetConfig,
    AllocationConfig,
    AllocationResult
)
from src.backtest.market_regime import (
    MarketRegimeDetector,
    RegimeConfig,
    RegimePrediction
)
from src.backtest.tactical_overlay import (
    TacticalOverlaySystem,
    OverlayConfig,
    OverlayResult
)
from src.backtest.dynamic_allocation_backtest import (
    DynamicAllocationBacktester,
    BacktestScenario,
    BacktestResults
)
from src.api.stock_api import get_hk_stock_data

def create_sample_market_data() -> Dict[str, pd.DataFrame]:
    """創建示例市場數據"""
    print("Creating sample market data...")

    # 香港主要股票
    symbols = ["0700.HK", "0941.HK", "1398.HK", "1299.HK", "2318.HK"]
    market_data = {}

    for symbol in symbols:
        try:
            data = get_hk_stock_data(symbol, 730)  # 2年數據
            if data is not None and len(data) > 100:
                # 確保數據格式正確
                data.index = pd.to_datetime(data.index)
                market_data[symbol] = data
                print(f"Loaded {len(data)} records for {symbol}")
            else:
                print(f"Failed to load data for {symbol}")
        except Exception as e:
            print(f"Error loading {symbol}: {e}")
            # 創建模擬數據作為備用
            dates = pd.date_range(end=datetime.now(), periods=730, freq='D')
            np.random.seed(hash(symbol) % 2**32)

            price = 100 * np.cumprod(1 + np.random.normal(0.0005, 0.02, len(dates)))
            high = price * (1 + np.abs(np.random.normal(0, 0.01, len(dates))))
            low = price * (1 - np.abs(np.random.normal(0, 0.01, len(dates))))
            open_price = price + np.random.normal(0, 0.5, len(dates))
            volume = np.random.uniform(1e6, 1e8, len(dates))

            market_data[symbol] = pd.DataFrame({
                'open': open_price,
                'high': high,
                'low': low,
                'close': price,
                'volume': volume
            }, index=dates)
            print(f"Created synthetic data for {symbol}")

    return market_data

def create_asset_configs() -> List[AssetConfig]:
    """創建資產配置"""
    return [
        AssetConfig(
            symbol="0700.HK",
            name="Tencent Holdings",
            asset_class="equity",
            min_weight=0.0,
            max_weight=0.4,
            commission_rate=0.001,
            bid_ask_spread=0.0005,
            expected_volatility=0.25,
            max_drawdown_limit=0.30
        ),
        AssetConfig(
            symbol="0941.HK",
            name="China Mobile",
            asset_class="equity",
            min_weight=0.0,
            max_weight=0.4,
            commission_rate=0.001,
            bid_ask_spread=0.0005,
            expected_volatility=0.20,
            max_drawdown_limit=0.25
        ),
        AssetConfig(
            symbol="1398.HK",
            name="ICBC",
            asset_class="equity",
            min_weight=0.0,
            max_weight=0.4,
            commission_rate=0.001,
            bid_ask_spread=0.0005,
            expected_volatility=0.18,
            max_drawdown_limit=0.20
        ),
        AssetConfig(
            symbol="1299.HK",
            name="AIA",
            asset_class="equity",
            min_weight=0.0,
            max_weight=0.4,
            commission_rate=0.001,
            bid_ask_spread=0.0005,
            expected_volatility=0.22,
            max_drawdown_limit=0.25
        ),
        AssetConfig(
            symbol="2318.HK",
            name="Ping An Insurance",
            asset_class="equity",
            min_weight=0.0,
            max_weight=0.4,
            commission_rate=0.001,
            bid_ask_spread=0.0005,
            expected_volatility=0.24,
            max_drawdown_limit=0.30
        )
    ]

def example_1_basic_allocation():
    """示例1：基礎動態配置"""
    print("\n" + "="*60)
    print("示例1：基礎動態資產配置")
    print("="*60)

    # 創建示例數據
    market_data = create_sample_market_data()
    asset_configs = create_asset_configs()

    # 初始化配置器
    allocator = DynamicAssetAllocator(asset_configs)

    # 計算當前配置
    allocation = allocator.calculate_optimal_allocation(market_data)

    # 顯示結果
    print(f"\n配置時間: {allocation.timestamp}")
    print(f"當前制度: {allocation.current_regime.regime_name if allocation.current_regime else '未檢測'}")
    print(f"配置策略: {allocation.allocation_strategy}")

    print("\n目標權重:")
    for symbol, weight in allocation.target_weights.items():
        asset = allocator.assets[symbol]
        print(f"  {asset.name} ({symbol}): {weight:.2%}")

    print(f"\n預期交易成本: {allocation.total_transaction_cost:.4f}")
    print(f"投資組合波動率: {allocation.portfolio_volatility:.2%}")
    print(f"預期年化回報: {allocation.expected_return:.2%}")
    print(f"Sharpe比率: {allocation.sharpe_ratio:.3f}")

def example_2_regime_detection():
    """示例2：市場制度檢測"""
    print("\n" + "="*60)
    print("示例2：市場制度檢測")
    print("="*60)

    # 創建市場數據
    market_data = create_sample_market_data()

    # 配置制度檢測器
    regime_config = RegimeConfig(
        n_regimes=3,
        volatility_window=20,
        trend_window=50,
        prediction_horizon=5
    )

    detector = MarketRegimeDetector(regime_config)

    # 訓練模型
    print("訓練制度檢測模型...")
    detector.fit(market_data)

    # 預測當前制度
    prediction = detector.predict(market_data)

    # 顯示結果
    print(f"\n當前制度: {prediction.current_regime.regime_name}")
    print(f"制度概率: {prediction.current_regime.probability:.3f}")
    print(f"預測置信度: {prediction.prediction_confidence:.3f}")

    print(f"\n制度特徵:")
    print(f"  波動率水平: {prediction.current_regime.volatility_level}")
    print(f"  趨勢強度: {prediction.current_regime.trend_strength}")
    print(f"  動量方向: {prediction.current_regime.momentum_direction}")
    print(f"  制度穩定性: {prediction.regime_stability:.3f}")

    print(f"\n未來制度預測:")
    for i, (regime, prob) in enumerate(prediction.predicted_regimes[:3]):
        print(f"  {i+1}. {regime.regime_name}: {prob:.3f}")

def example_3_tactical_overlay():
    """示例3：戰術覆蓋系統"""
    print("\n" + "="*60)
    print("示例3：戰術覆蓋系統")
    print("="*60)

    # 創建組件
    market_data = create_sample_market_data()
    asset_configs = create_asset_configs()

    # 基礎配置器
    base_allocator = DynamicAssetAllocator(asset_configs)

    # 覆蓋配置
    overlay_config = OverlayConfig(
        signal_generation_frequency="daily",
        max_signals_per_asset=3,
        min_signal_confidence=0.6,
        max_overlay_adjustment=0.15
    )

    # 戰術覆蓋系統
    overlay_system = TacticalOverlaySystem(base_allocator, overlay_config)

    # 戰略權重（等權重）
    strategic_weights = {asset.symbol: 1.0/len(asset_configs) for asset in asset_configs}

    # 應用戰術覆蓋
    print("應用戰術覆蓋...")
    overlay_result = overlay_system.apply_tactical_overlay(strategic_weights, market_data)

    # 顯示結果
    print(f"\n戰略權重 vs 最終權重:")
    for symbol in strategic_weights.keys():
        strategic = strategic_weights[symbol]
        final = overlay_result.final_weights[symbol]
        adjustment = overlay_result.tactical_adjustments[symbol]

        print(f"  {symbol}: {strategic:.2%} -> {final:.2%} ({adjustment:+.2%})")

    print(f"\n活躍信號數量: {len(overlay_result.active_signals)}")
    print(f"覆蓋成本: {overlay_result.total_overlay_cost:.4f}")
    print(f"預期覆蓋回報: {overlay_result.expected_overlay_return:.2%}")

    print(f"\n信號摘要:")
    for symbol, summary in overlay_result.signal_summary.items():
        print(f"  {symbol}: {summary['signal_count']}個信號, 平均置信度: {summary['avg_confidence']:.3f}")

def example_4_full_backtest():
    """示例4：完整回測示例"""
    print("\n" + "="*60)
    print("示例4：完整動態配置回測")
    print("="*60)

    # 準備數據
    market_data = create_sample_market_data()
    asset_configs = create_asset_configs()

    # 創建回測場景
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    scenario = BacktestScenario(
        name="Hong Kong Equities Dynamic Allocation",
        description="動態配置香港主要股票的回測",
        start_date=start_date,
        end_date=end_date,
        initial_capital=1000000,
        assets=asset_configs,
        regime_config=RegimeConfig(n_regimes=3),
        allocation_config=AllocationConfig(
            rebalance_frequency="monthly",
            volatility_target=0.15,
            max_position_change=0.2
        ),
        overlay_config=OverlayConfig(
            max_overlay_adjustment=0.1,
            min_signal_confidence=0.6
        ),
        benchmark_weights={asset.symbol: 1.0/len(asset_configs) for asset in asset_configs},
        benchmark_name="Equal Weight"
    )

    # 運行回測
    print(f"運行回測: {scenario.start_date.strftime('%Y-%m-%d')} 到 {scenario.end_date.strftime('%Y-%m-%d')}")
    backtester = DynamicAllocationBacktester()
    results = backtester.run_scenario(scenario, market_data)

    # 顯示性能比較
    print(f"\n性能比較:")
    perf = results.performance_comparison

    print(f"\n總回報:")
    print(f"  動態配置: {perf['returns']['dynamic']:.2%}")
    print(f"  基準: {perf['returns']['benchmark']:.2%}")
    print(f"  超額回報: {perf['returns']['excess']:.2%}")

    print(f"\nSharpe比率:")
    print(f"  動態配置: {perf['sharpe']['dynamic']:.3f}")
    print(f"  基準: {perf['sharpe']['benchmark']:.3f}")
    print(f"  超額Sharpe: {perf['sharpe']['excess']:.3f}")

    print(f"\n最大回撤:")
    print(f"  動態配置: {perf['max_drawdown']['dynamic']:.2%}")
    print(f"  基準: {perf['max_drawdown']['benchmark']:.2%}")
    print(f"  改善程度: {perf['max_drawdown']['improvement']:.2%}")

    # 交易分析
    print(f"\n交易分析:")
    trade = results.trade_analysis
    print(f"  總交易次數: {trade['total_trades']}")
    print(f"  總交易成本: {trade['total_trading_cost']:.2f}")
    print(f"  成本佔比: {trade['cost_as_percentage_of_final_value']:.2f}%")

    # 風險分析
    print(f"\n風險分析:")
    risk = results.risk_analysis
    print(f"  投資組合波動率: {risk['portfolio_volatility']:.2%}")
    print(f"  下行波動率: {risk['downside_volatility']:.2%}")
    print(f"  VaR(95%): {risk['var_95']:.2%}")
    print(f"  最大回撤持續時間: {risk['max_drawdown_duration']}天")

    # 制度分析
    print(f"\n制度歸因分析:")
    attribution = results.attribution_analysis
    regime_attribution = attribution.get('regime_attribution', {})

    for regime, stats in regime_attribution.items():
        print(f"  {regime}:")
        print(f"    平均回報: {stats['average_return']:.2%}")
        print(f"    波動率: {stats['volatility']:.2%}")
        print(f"    期間數: {stats['periods']}")

    print(f"\n執行時間: {results.execution_time:.2f}秒")
    print(f"最終投資組合價值: ${results.dynamic_results['final_portfolio_value']:,.2f}")

def example_5_multiple_scenarios():
    """示例5：多場景比較"""
    print("\n" + "="*60)
    print("示例5：多策略場景比較")
    print("="*60)

    # 準備數據
    market_data = create_sample_market_data()
    asset_configs = create_asset_configs()

    # 創建多個場景
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    scenarios = [
        BacktestScenario(
            name="Conservative",
            description="保守策略",
            start_date=start_date,
            end_date=end_date,
            initial_capital=1000000,
            assets=asset_configs,
            allocation_config=AllocationConfig(
                rebalance_frequency="quarterly",
                volatility_target=0.10,
                max_position_change=0.1
            ),
            benchmark_weights={asset.symbol: 1.0/len(asset_configs) for asset in asset_configs}
        ),
        BacktestScenario(
            name="Balanced",
            description="平衡策略",
            start_date=start_date,
            end_date=end_date,
            initial_capital=1000000,
            assets=asset_configs,
            allocation_config=AllocationConfig(
                rebalance_frequency="monthly",
                volatility_target=0.15,
                max_position_change=0.2
            ),
            overlay_config=OverlayConfig(max_overlay_adjustment=0.1),
            benchmark_weights={asset.symbol: 1.0/len(asset_configs) for asset in asset_configs}
        ),
        BacktestScenario(
            name="Aggressive",
            description="激進策略",
            start_date=start_date,
            end_date=end_date,
            initial_capital=1000000,
            assets=asset_configs,
            allocation_config=AllocationConfig(
                rebalance_frequency="weekly",
                volatility_target=0.20,
                max_position_change=0.3
            ),
            overlay_config=OverlayConfig(max_overlay_adjustment=0.2),
            benchmark_weights={asset.symbol: 1.0/len(asset_configs) for asset in asset_configs}
        )
    ]

    # 運行所有場景
    print("運行多場景比較...")
    backtester = DynamicAllocationBacktester()
    results = {}

    for scenario in scenarios:
        print(f"\n運行場景: {scenario.name}")
        try:
            results[scenario.name] = backtester.run_scenario(scenario, market_data)
        except Exception as e:
            print(f"場景 {scenario.name} 失敗: {e}")
            continue

    # 比較結果
    print(f"\n場景性能比較:")
    print(f"{'策略':<12} {'總回報':<10} {'Sharpe':<8} {'最大回撤':<10} {'波動率':<8}")
    print("-" * 60)

    for name, result in results.items():
        perf = result.performance_comparison
        dynamic = perf['returns']['dynamic']
        sharpe = perf['sharpe']['dynamic']
        max_dd = perf['max_drawdown']['dynamic']
        vol = perf['volatility']['dynamic']

        print(f"{name:<12} {dynamic:<10.2%} {sharpe:<8.3f} {max_dd:<10.2%} {vol:<8.2%}")

def main():
    """主函數"""
    print("動態資產配置系統使用示例")
    print("="*60)

    try:
        # 運行所有示例
        example_1_basic_allocation()
        example_2_regime_detection()
        example_3_tactical_overlay()
        example_4_full_backtest()
        example_5_multiple_scenarios()

        print(f"\n" + "="*60)
        print("所有示例運行完成！")
        print("="*60)

    except Exception as e:
        print(f"示例運行失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
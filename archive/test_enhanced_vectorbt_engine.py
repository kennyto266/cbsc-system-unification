#!/usr/bin/env python3
"""
測試增強VectorBT引擎
Test Enhanced VectorBT Engine
"""

import pandas as pd
import numpy as np
from simplified_system.src.backtest.enhanced_vectorbt_engine import (
    EnhancedVectorBTEngine,
    EnhancedBacktestConfig,
    create_enhanced_engine,
    run_portfolio_backtest,
    run_walk_forward_analysis
)

def create_sample_data():
    """創建樣本數據"""
    np.random.seed(42)

    # 生成模擬股價數據
    dates = pd.date_range(start='2022-01-01', end='2024-12-31', freq='D')

    # 生成5年的模擬數據（約730個交易日）
    n_days = len(dates)

    # 模擬0700.HK的價格模式
    initial_price = 450.0
    returns = np.random.normal(0.0008, 0.02, n_days)  # 日均回報約0.08%，波動率2%

    # 添加趨勢成分
    trend = np.linspace(0, 0.5, n_days)  # 約50%的總趨勢
    returns = returns + trend / n_days

    # 計算價格
    prices = initial_price * np.exp(np.cumsum(returns))

    # 生成OHLCV數據
    high = prices * (1 + np.abs(np.random.normal(0, 0.01, n_days)))
    low = prices * (1 - np.abs(np.random.normal(0, 0.01, n_days)))
    open_price = prices + np.random.normal(0, prices * 0.005, n_days)
    volume = np.random.randint(1000000, 5000000, n_days)

    # 確保OHLC邏輯正確
    high = np.maximum(high, np.maximum(open_price, prices))
    low = np.minimum(low, np.minimum(open_price, prices))

    data = pd.DataFrame({
        'open': open_price,
        'high': high,
        'low': low,
        'close': prices,
        'volume': volume
    }, index=dates)

    return data

def test_enhanced_strategies():
    """測試增強策略"""
    print("=" * 80)
    print("測試增強VectorBT引擎")
    print("=" * 80)

    # 創建樣本數據
    data = create_sample_data()
    print(f"生成樣本數據: {len(data)} 天，價格範圍: {data['close'].min():.2f} - {data['close'].max():.2f}")

    # 創建增強引擎
    config = EnhancedBacktestConfig(
        initial_cash=100000,
        fees=0.001,
        enable_parallel=True,
        max_workers=2
    )
    engine = create_enhanced_engine(config)

    # 測試可用策略
    available_strategies = engine.get_performance_summary()['available_strategies']
    print(f"可用策略數量: {len(available_strategies)}")
    print(f"策略列表: {available_strategies}")

    # 測試基礎策略
    print("\n" + "="*60)
    print("測試基礎策略")
    print("="*60)

    basic_strategies = ['RSI_MEAN_REVERSION', 'MACD_CROSSOVER', 'BOLLINGER_BANDS']

    for strategy in basic_strategies:
        try:
            result = engine.backtest_strategy(
                data=data,
                strategy=strategy,
                parameters={'period': 14, 'oversold': 30, 'overbought': 70} if 'RSI' in strategy else {},
                symbol='TEST_HK'
            )

            print(f"\n{strategy}:")
            print(f"  總回報: {result.total_return:.2%}")
            print(f"  年化回報: {result.annual_return:.2%}")
            print(f"  Sharpe比率: {result.sharpe_ratio:.3f}")
            print(f"  最大回撤: {result.max_drawdown:.2%}")
            print(f"  總交易次數: {result.total_trades}")

        except Exception as e:
            print(f"\n{strategy}: 錯誤 - {e}")

    # 測試進階策略
    print("\n" + "="*60)
    print("測試進階策略")
    print("="*60)

    advanced_strategies = ['ADVANCED_MEAN_REVERSION', 'DUAL_RSI_CONFLUENCE', 'ICHIMOKU_CLOUD']

    for strategy in advanced_strategies:
        try:
            result = engine.backtest_strategy(
                data=data,
                strategy=strategy,
                parameters={
                    'rsi_period': 14,
                    'bb_period': 20,
                    'bb_std': 2.0,
                    'atr_period': 14,
                    'volatility_threshold': 0.02
                } if 'ADVANCED' in strategy or 'DUAL' in strategy else {},
                symbol='TEST_HK'
            )

            print(f"\n{strategy}:")
            print(f"  總回報: {result.total_return:.2%}")
            print(f"  年化回報: {result.annual_return:.2%}")
            print(f"  Sharpe比率: {result.sharpe_ratio:.3f}")
            print(f"  最大回撤: {result.max_drawdown:.2%}")
            print(f"  總交易次數: {result.total_trades}")

        except Exception as e:
            print(f"\n{strategy}: 錯誤 - {e}")

def test_parameter_optimization():
    """測試參數優化"""
    print("\n" + "="*60)
    print("測試並行參數優化")
    print("="*60)

    # 創建樣本數據
    data = create_sample_data()

    # 創建引擎
    config = EnhancedBacktestConfig(enable_parallel=True, max_workers=2)
    engine = create_enhanced_engine(config)

    # RSI參數優化
    param_ranges = {
        'period': range(10, 31, 5),
        'oversold': [20, 25, 30, 35],
        'overbought': [65, 70, 75, 80]
    }

    print("開始RSI參數優化...")
    try:
        result = engine.optimize_parameters_parallel(
            data=data,
            strategy='RSI_MEAN_REVERSION',
            param_ranges=param_ranges,
            symbol='TEST_HK',
            optimization_metric='sharpe_ratio',
            max_combinations=50
        )

        print(f"優化完成！")
        print(f"測試組合數: {result['total_combinations']}")
        print(f"成功組合數: {result['successful_combinations']}")
        print(f"優化時間: {result['optimization_time']:.3f}秒")
        print(f"最佳參數: {result['best_parameters']}")
        print(f"最佳Sharpe比率: {result['best_performance']['performance']['sharpe_ratio']:.3f}")
        print(f"最佳年化回報: {result['best_performance']['performance']['annual_return']:.2%}")

        # 性能統計
        stats = result['performance_statistics']
        print(f"\n性能統計:")
        print(f"  平均Sharpe: {stats['mean']:.3f}")
        print(f"  標準差: {stats['std']:.3f}")
        print(f"  最大Sharpe: {stats['max']:.3f}")
        print(f"  最小Sharpe: {stats['min']:.3f}")

    except Exception as e:
        print(f"參數優化錯誤: {e}")

def test_portfolio_backtest():
    """測試投資組合回測"""
    print("\n" + "="*60)
    print("測試多資產投資組合回測")
    print("="*60)

    # 創建多個資產的樣本數據
    np.random.seed(42)
    assets = ['STOCK_A', 'STOCK_B', 'STOCK_C']

    data_dict = {}
    for asset in assets:
        # 為每個資產創建略微不同的數據
        np.random.seed(hash(asset) % 1000)
        asset_data = create_sample_data()
        # 添加資產特有的漂移
        drift = np.random.normal(0.0002, 0.01, len(asset_data))
        asset_data['close'] = asset_data['close'] * (1 + np.cumsum(drift))
        data_dict[asset] = asset_data

    print(f"創建 {len(data_dict)} 個資產的數據")

    # 創建引擎
    engine = create_enhanced_engine()

    # 測試投資組合回測
    weights = {'STOCK_A': 0.4, 'STOCK_B': 0.3, 'STOCK_C': 0.3}

    try:
        portfolio_results = engine.backtest_portfolio(
            data_dict=data_dict,
            strategy='RSI_MEAN_REVERSION',
            parameters={'period': 14, 'oversold': 30, 'overbought': 70},
            weights=weights
        )

        print("投資組合回測結果:")
        for asset, result in portfolio_results.items():
            print(f"\n{asset}:")
            print(f"  總回報: {result.total_return:.2%}")
            print(f"  年化回報: {result.annual_return:.2%}")
            print(f"  Sharpe比率: {result.sharpe_ratio:.3f}")
            print(f"  最大回撤: {result.max_drawdown:.2%}")

    except Exception as e:
        print(f"投資組合回測錯誤: {e}")

def test_walk_forward_analysis():
    """測試走前分析"""
    print("\n" + "="*60)
    print("測試走前分析框架")
    print("="*60)

    # 創建更長的樣本數據
    np.random.seed(42)
    dates = pd.date_range(start='2020-01-01', end='2024-12-31', freq='D')
    n_days = len(dates)

    # 生成模擬數據
    initial_price = 450.0
    returns = np.random.normal(0.0005, 0.025, n_days)
    trend = np.linspace(0, 0.8, n_days)  # 80%的總趨勢
    returns = returns + trend / n_days
    prices = initial_price * np.exp(np.cumsum(returns))

    data = pd.DataFrame({
        'close': prices,
        'open': prices + np.random.normal(0, prices * 0.01, n_days),
        'high': prices * (1 + np.abs(np.random.normal(0, 0.015, n_days))),
        'low': prices * (1 - np.abs(np.random.normal(0, 0.015, n_days))),
        'volume': np.random.randint(1000000, 5000000, n_days)
    }, index=dates)

    print(f"創建走前分析數據: {len(data)} 天")

    # 創建引擎
    engine = create_enhanced_engine()

    # 設置參數範圍
    param_ranges = {
        'period': [10, 14, 20, 25],
        'oversold': [20, 30, 40],
        'overbought': [60, 70, 80]
    }

    try:
        print("開始走前分析...")
        result = engine.walk_forward_analysis(
            data=data,
            strategy='RSI_MEAN_REVERSION',
            param_ranges=param_ranges,
            window_size=126,  # 約6個月
            step_size=63,    # 約3個月
            test_size=42,     # 約2個月
            symbol='TEST_HK'
        )

        print(f"走前分析完成！")
        print(f"總週期數: {result['total_periods']}")
        print(f"優化窗口大小: {result['window_size']} 天")
        print(f"測試窗口大小: {result['test_size']} 天")

        # 樣外樣本性能
        oos_perf = result['out_of_sample_performance']
        print(f"\n樣本外性能:")
        print(f"  平均回報: {oos_perf['mean_return']:.2%}")
        print(f"  回報標準差: {oos_perf['std_return']:.2%}")
        print(f"  平均Sharpe: {oos_perf['mean_sharpe']:.3f}")
        print(f"  Sharpe標準差: {oos_perf['std_sharpe']:.3f}")
        print(f"  正收益週期數: {oos_perf['positive_periods']}/{result['total_periods']}")
        print(f"  正收益比例: {oos_perf['positive_periods_ratio']:.2%}")

    except Exception as e:
        print(f"走前分析錯誤: {e}")

def test_performance_summary():
    """測試性能總結"""
    print("\n" + "="*60)
    print("引擎性能總結")
    print("="*60)

    engine = create_enhanced_engine()
    summary = engine.get_performance_summary()

    print("引擎統計:")
    for key, value in summary['engine_statistics'].items():
        print(f"  {key}: {value}")

    print(f"\n可用策略: {len(summary['available_strategies'])}")
    print(f"緩存大小: {summary['cache_size']}")

    print("\n配置:")
    for key, value in summary['config'].items():
        print(f"  {key}: {value}")

def main():
    """主測試函數"""
    print("開始測試增強VectorBT引擎...")

    try:
        # 測試基礎功能
        test_enhanced_strategies()

        # 測試參數優化
        test_parameter_optimization()

        # 測試投資組合回測
        test_portfolio_backtest()

        # 測試走前分析
        test_walk_forward_analysis()

        # 性能總結
        test_performance_summary()

        print("\n" + "="*80)
        print("✅ 所有測試完成！增強VectorBT引擎運行正常。")
        print("="*80)

    except Exception as e:
        print(f"\n❌ 測試過程出錯: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Phase 2 快速測試 - 驗證四大策略基本功能
"""

import pandas as pd
import numpy as np
import time
from datetime import datetime

# 導入核心組件
from strategy_backtest_implementations import StrategyBacktestImplementations
from relaxed_data_integration import DataIntegrationManager

def generate_test_data(days=120):
    """生成測試數據"""
    np.random.seed(42)
    dates = pd.date_range(end=pd.Timestamp.now(), periods=days, freq='D')
    initial_price = 450

    # 生成價格數據
    returns = np.random.normal(0.0005, 0.025, days)
    prices = [initial_price]

    for i in range(1, days):
        prices.append(prices[-1] * (1 + returns[i]))

    # 創建OHLCV數據
    volatility = 0.025
    data = {
        'open': [p * (1 + np.random.normal(0, volatility * 0.5)) for p in prices],
        'high': [p * (1 + abs(np.random.normal(0, volatility))) for p in prices],
        'low': [p * (1 - abs(np.random.normal(0, volatility))) for p in prices],
        'close': prices,
        'volume': [int(1000000 * (1 + abs(np.random.normal(0, 0.4)))) for _ in range(days)]
    }

    df = pd.DataFrame(data, index=dates)

    # 確保OHLC邏輯正確
    df['high'] = np.maximum(df['high'], np.maximum(df['open'], df['close']))
    df['low'] = np.minimum(df['low'], np.minimum(df['open'], df['close']))

    return df

def test_all_strategies():
    """測試所有四大策略"""

    print("="*70)
    print("PHASE 2 QUICK TEST - Four Strategy Validation")
    print("="*70)

    # 生成測試數據
    print("\n[STEP 1] Generating test data...")
    test_data = generate_test_data(120)
    print(f"Test data: {len(test_data)} records")
    print(f"Price range: {test_data['close'].min():.2f} - {test_data['close'].max():.2f}")

    # 創建策略實現器
    strategy_impl = StrategyBacktestImplementations()

    # 測試結果
    test_results = {}

    # 測試1: RSI策略
    print("\n[STEP 2] Testing RSI Strategy...")
    rsi_params = {
        'strategy': 'RSI',
        'period': 14,
        'oversold': 30,
        'overbought': 70,
        'condition_type': 'moderate'
    }

    try:
        rsi_result = strategy_impl.backtest_rsi_strategy(rsi_params, test_data)
        test_results['RSI'] = {
            'success': rsi_result.success,
            'sharpe': rsi_result.sharpe_ratio,
            'return': rsi_result.total_return,
            'drawdown': rsi_result.max_drawdown,
            'frequency': rsi_result.trade_frequency,
            'error': rsi_result.error_message if not rsi_result.success else None
        }
        print(f"[OK] RSI: Sharpe={rsi_result.sharpe_ratio:.3f}, Return={rsi_result.total_return:.2%}, Success={rsi_result.success}")
    except Exception as e:
        test_results['RSI'] = {'success': False, 'error': str(e)}
        print(f"[FAIL] RSI Failed: {str(e)}")

    # 測試2: MACD策略
    print("\n[STEP 3] Testing MACD Strategy...")
    macd_params = {
        'strategy': 'MACD',
        'fast': 12,
        'slow': 26,
        'signal': 9,
        'condition_type': 'standard'
    }

    try:
        macd_result = strategy_impl.backtest_macd_strategy(macd_params, test_data)
        test_results['MACD'] = {
            'success': macd_result.success,
            'sharpe': macd_result.sharpe_ratio,
            'return': macd_result.total_return,
            'drawdown': macd_result.max_drawdown,
            'frequency': macd_result.trade_frequency,
            'error': macd_result.error_message if not macd_result.success else None
        }
        print(f"[OK] MACD: Sharpe={macd_result.sharpe_ratio:.3f}, Return={macd_result.total_return:.2%}, Success={macd_result.success}")
    except Exception as e:
        test_results['MACD'] = {'success': False, 'error': str(e)}
        print(f"[FAIL] MACD Failed: {str(e)}")

    # 測試3: KDJ策略
    print("\n[STEP 4] Testing KDJ Strategy...")
    kdj_params = {
        'strategy': 'KDJ',
        'k_period': 9,
        'd_period': 3,
        'condition_type': 'standard'
    }

    try:
        kdj_result = strategy_impl.backtest_kdj_strategy(kdj_params, test_data)
        test_results['KDJ'] = {
            'success': kdj_result.success,
            'sharpe': kdj_result.sharpe_ratio,
            'return': kdj_result.total_return,
            'drawdown': kdj_result.max_drawdown,
            'frequency': kdj_result.trade_frequency,
            'error': kdj_result.error_message if not kdj_result.success else None
        }
        print(f"[OK] KDJ: Sharpe={kdj_result.sharpe_ratio:.3f}, Return={kdj_result.total_return:.2%}, Success={kdj_result.success}")
    except Exception as e:
        test_results['KDJ'] = {'success': False, 'error': str(e)}
        print(f"[FAIL] KDJ Failed: {str(e)}")

    # 測試4: 布林帶策略
    print("\n[STEP 5] Testing Bollinger Bands Strategy...")
    bb_params = {
        'strategy': 'BOLLINGER_BANDS',
        'period': 20,
        'std_dev': 2.0,
        'condition_type': 'moderate'
    }

    try:
        bb_result = strategy_impl.backtest_bollinger_bands_strategy(bb_params, test_data)
        test_results['BOLLINGER_BANDS'] = {
            'success': bb_result.success,
            'sharpe': bb_result.sharpe_ratio,
            'return': bb_result.total_return,
            'drawdown': bb_result.max_drawdown,
            'frequency': bb_result.trade_frequency,
            'error': bb_result.error_message if not bb_result.success else None
        }
        print(f"[OK] BB: Sharpe={bb_result.sharpe_ratio:.3f}, Return={bb_result.total_return:.2%}, Success={bb_result.success}")
    except Exception as e:
        test_results['BOLLINGER_BANDS'] = {'success': False, 'error': str(e)}
        print(f"[FAIL] BB Failed: {str(e)}")

    # 生成測試摘要
    print("\n" + "="*70)
    print("PHASE 2 QUICK TEST SUMMARY")
    print("="*70)

    total_strategies = len(test_results)
    successful_strategies = sum(1 for r in test_results.values() if r['success'])

    print(f"\nTotal Strategies Tested: {total_strategies}")
    print(f"Successful: {successful_strategies}")
    print(f"Failed: {total_strategies - successful_strategies}")
    print(f"Success Rate: {successful_strategies/total_strategies*100:.1f}%")

    print(f"\nStrategy Performance Summary:")
    for strategy, result in test_results.items():
        if result['success']:
            print(f"  {strategy}:")
            print(f"    Sharpe: {result['sharpe']:.3f}")
            print(f"    Return: {result['return']:.2%}")
            print(f"    Drawdown: {result['drawdown']:.2%}")
            print(f"    Trade Frequency: {result['frequency']:.2%}")
        else:
            print(f"  {strategy}: FAILED - {result.get('error', 'Unknown error')}")

    # 結論
    success = successful_strategies == total_strategies
    print(f"\n{'='*70}")
    print(f"PHASE 2 QUICK TEST {'PASSED' if success else 'FAILED'}")
    print(f"{'='*70}")

    if success:
        print("[SUCCESS] All four strategies implemented successfully!")
        print("Phase 2 core functionality is working correctly.")
    else:
        print("[WARNING] Some strategies failed. Please check the errors above.")

    return success

def test_real_data():
    """測試真實數據集成"""

    print(f"\n[STEP 6] Testing real data integration...")

    try:
        # 創建數據管理器
        data_manager = DataIntegrationManager()

        # 準備回測數據
        stock_data, gov_data = data_manager.prepare_backtest_data("0700.HK", 60)

        if not stock_data.empty:
            print(f"[OK] Real data integration successful!")
            print(f"  Stock records: {len(stock_data)}")
            print(f"  Date range: {stock_data.index[0].date()} to {stock_data.index[-1].date()}")
            print(f"  Price range: {stock_data['close'].min():.2f} - {stock_data['close'].max():.2f}")
            return True, stock_data
        else:
            print("[FAIL] No stock data loaded")
            return False, None

    except Exception as e:
        print(f"[FAIL] Real data integration failed: {str(e)}")
        return False, None

if __name__ == "__main__":
    # 運行快速測試
    print(f"[START] Phase 2 Quick Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 測試所有策略
    strategy_success = test_all_strategies()

    # 測試真實數據
    data_success, real_data = test_real_data()

    # 如果真實數據可用，進行額外測試
    if data_success and real_data is not None:
        print(f"\n[STEP 7] Testing strategies with real data...")
        strategy_impl = StrategyBacktestImplementations()

        # 用真實數據測試RSI策略
        try:
            rsi_params = {
                'strategy': 'RSI',
                'period': 14,
                'oversold': 25,
                'overbought': 75,
                'condition_type': 'strict'
            }
            rsi_result = strategy_impl.backtest_rsi_strategy(rsi_params, real_data)
            print(f"[OK] Real data RSI test: Sharpe={rsi_result.sharpe_ratio:.3f}, Success={rsi_result.success}")
        except Exception as e:
            print(f"[FAIL] Real data RSI test failed: {str(e)}")

    # 最終結果
    overall_success = strategy_success and data_success

    print(f"\n[RESULT] Phase 2 Quick Test {'PASSED' if overall_success else 'FAILED'}")

    if overall_success:
        print("[SUCCESS] Phase 2 is ready for full deployment!")
    else:
        print("[WARNING] Phase 2 needs additional fixes before full deployment.")
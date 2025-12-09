#!/usr/bin/env python3
"""
測試修正後的優化器
"""

import sys
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')

from massive_nonprice_ta_optimizer import MassiveNonPriceTAOptimizer

def test_corrected_sharpe_calculation():
    """測試修正後的夏普比率計算"""
    print("Testing Corrected Sharpe Ratio Calculation")
    print("=" * 50)

    # 創建優化器實例
    optimizer = MassiveNonPriceTAOptimizer()

    # 模擬回報數據
    np.random.seed(42)
    test_returns = np.random.normal(0.001, 0.02, 100)  # 100個交易日回報

    # 模擬價格數據
    price = 100
    prices = [price]
    for ret in test_returns:
        price *= (1 + ret)
        prices.append(price)

    optimizer.price_data = {'close': prices}

    # 測試一個簡單策略
    strategy_params = ('MB', 'KDJ', [10, 2])

    try:
        result = optimizer.backtest_nonprice_ta_strategy(strategy_params)

        print(f"Strategy: {result['strategy_id']}")
        print(f"Sharpe Ratio: {result['sharpe_ratio']:.4f}")
        print(f"Annual Return: {result['annual_return']:.2%}")
        print(f"Max Drawdown: {result['max_drawdown']:.2%}")
        print(f"Volatility: {result['volatility']:.4f}")
        print(f"Quality Score: {result['quality_score']:.1f}")
        print(f"Success: {result['success']}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_corrected_sharpe_calculation()
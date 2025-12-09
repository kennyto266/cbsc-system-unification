#!/usr/bin/env python3
"""
Clean Real Data Test
"""

import requests
import numpy as np

def clean_real_test():
    """Clean real data test"""
    print("Clean Real Data Test")
    print("=" * 60)

    try:
        # 1. Get stock data
        print("\nStep 1: Get real stock data")
        stock_url = "http://18.180.162.113:9191/inst/getInst"
        params = {"symbol": "0700.hk", "duration": 365}

        response = requests.get(stock_url, params=params, timeout=30)
        response.raise_for_status()
        stock_data = response.json()

        prices = list(stock_data['data']['close'].values())

        print(f"[OK] Got {len(prices)} real 0700.HK price records")
        print(f"Price range: {min(prices):.2f} - {max(prices):.2f} HKD")

        # 2. Simple strategy test using real data
        print("\nStep 2: Simple strategy test")

        # Simple moving average strategy
        def calculate_returns(prices):
            returns = []
            for i in range(1, len(prices)):
                ret = (prices[i] - prices[i-1]) / prices[i-1]
                returns.append(ret)
            return returns

        returns = calculate_returns(prices)

        # Calculate performance metrics
        total_return = sum(returns)
        annual_return = (1 + total_return) ** (252/len(returns)) - 1
        volatility = np.std(returns) * np.sqrt(252)
        sharpe = (annual_return - 0.03) / volatility if volatility > 0 else 0

        print(f"[OK] Strategy performance calculated")
        print(f"Total return: {total_return:.2%}")
        print(f"Annual return: {annual_return:.2%}")
        print(f"Volatility: {volatility:.2%}")
        print(f"Sharpe ratio: {sharpe:.3f}")

        # 3. Simple comparison with random strategy
        print("\nStep 3: Comparison with random data")
        np.random.seed(42)
        random_returns = np.random.normal(0, 0.02, len(returns))

        random_total = sum(random_returns)
        random_annual = (1 + random_total) ** (252/len(random_returns)) - 1
        random_vol = np.std(random_returns) * np.sqrt(252)
        random_sharpe = (random_annual - 0.03) / random_vol if random_vol > 0 else 0

        print(f"Random strategy - Sharpe: {random_sharpe:.3f}")
        print(f"Real data strategy - Sharpe: {sharpe:.3f}")

        if sharpe > random_sharpe:
            print("[SUCCESS] Real data strategy outperforms random")
        else:
            print("[WARNING] Random data strategy outperforms")

        print("\n[COMPLETE] Real data backtest finished")
        return True

    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    clean_real_test()
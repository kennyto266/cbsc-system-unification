#!/usr/bin/env python3
"""
Check VectorBT Portfolio API
檢查VectorBT投資組合API
"""

import pandas as pd
import numpy as np

def test_vectorbt_portfolio_api():
    """Test VectorBT portfolio API to understand return formats"""
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
    prices = 100 + np.cumsum(np.random.normal(0.1, 2, len(dates)))

    try:
        import vectorbt as vbt
        print("Testing VectorBT Portfolio API")

        # Create simple signals
        entries = pd.Series(False, index=dates)
        entries.iloc[0] = True
        exits = pd.Series(False, index=dates)

        # Create portfolio
        portfolio = vbt.Portfolio.from_signals(
            close=pd.Series(prices, index=dates),
            entries=entries,
            exits=exits,
            init_cash=100000
        )

        # Test different return methods
        print("Portfolio methods:")
        print(f"  portfolio.total_return() type: {type(portfolio.total_return())}")
        print(f"  portfolio.total_return() shape: {portfolio.total_return().shape if hasattr(portfolio.total_return(), 'shape') else 'No shape'}")
        print(f"  portfolio.sharpe_ratio() type: {type(portfolio.sharpe_ratio())}")
        print(f"  portfolio.max_drawdown() type: {type(portfolio.max_drawdown())}")

        # Get final values
        total_return = portfolio.total_return()
        if hasattr(total_return, 'iloc'):
            final_return = total_return.iloc[-1]
        else:
            final_return = total_return

        print(f"  Final return: {final_return}")
        print(f"  Sharpe: {portfolio.sharpe_ratio()}")
        print(f"  Max drawdown: {portfolio.max_drawdown()}")

        return True

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_vectorbt_portfolio_api()
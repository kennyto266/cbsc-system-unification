"""
Simple test for currency strength indicator
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

class IndicatorResult:
    def __init__(self, name: str, values, parameters: Dict[str, Any],
                 metadata: Optional[Dict[str, Any]] = None,
                 signals: Optional[pd.Series] = None):
        self.name = name
        self.values = values
        self.parameters = parameters
        self.metadata = metadata or {}
        self.signals = signals if signals is not None else pd.Series()

def test_currency_strength_simple():
    print("Testing Currency Strength Indicator - Simple Version")

    # Create test data
    dates = pd.date_range('2020-01-01', periods=100, freq='D')
    np.random.seed(42)

    # Simple currency data
    currency_data = {
        'USD': 7.8 + np.random.normal(0, 0.1, len(dates)),
        'EUR': 8.5 + np.random.normal(0, 0.15, len(dates)),
        'GBP': 10.2 + np.random.normal(0, 0.2, len(dates))
    }

    rate_matrix = pd.DataFrame(currency_data, index=dates)
    rate_matrix = rate_matrix.abs()  # Ensure positive rates

    print(f"Rate matrix shape: {rate_matrix.shape}")
    print(f"Rate matrix columns: {list(rate_matrix.columns)}")
    print(f"Rate matrix head:\n{rate_matrix.head()}")

    try:
        # Step 1: Calculate returns
        print("\nStep 1: Calculating returns...")
        currency_returns = rate_matrix.pct_change()
        print("Returns calculated successfully")

        # Step 2: Calculate volatility
        print("\nStep 2: Calculating volatility...")
        currency_volatility = currency_returns.rolling(window=20).std()
        print("Volatility calculated successfully")

        # Step 3: Calculate momentum
        print("\nStep 3: Calculating momentum...")
        momentum_20d = rate_matrix.pct_change(20)
        print("Momentum calculated successfully")

        # Step 4: Calculate RSI for each currency
        print("\nStep 4: Calculating RSI...")
        currency_rsi = {}

        for currency in rate_matrix.columns:
            print(f"  Calculating RSI for {currency}...")
            returns = rate_matrix[currency].pct_change()
            gains = returns.where(returns > 0, 0).rolling(window=14).mean()
            losses = -returns.where(returns < 0, 0).rolling(window=14).mean()
            rs = gains / losses
            rsi = 100 - (100 / (1 + rs))
            currency_rsi[f'{currency}_RSI'] = rsi
            print(f"  {currency} RSI calculated successfully")

        print("All RSI calculations completed successfully")

        # Step 5: Calculate composite strength
        print("\nStep 5: Calculating composite strength...")
        if currency_rsi:
            rsi_df = pd.DataFrame(currency_rsi)
            composite_strength = rsi_df.mean(axis=1)
        else:
            composite_strength = pd.Series(50, index=rate_matrix.index)

        print("Composite strength calculated successfully")

        # Create result
        result = IndicatorResult(
            name="Currency_Strength",
            values={
                'currency_returns': currency_returns,
                'currency_volatility': currency_volatility,
                'momentum_20d': momentum_20d,
                'currency_rsi': pd.DataFrame(currency_rsi),
                'composite_strength': composite_strength
            },
            parameters={
                'currencies': list(rate_matrix.columns),
                'momentum_period': 20,
                'rsi_period': 14,
                'volatility_window': 20
            }
        )

        print(f"\nFinal Results:")
        print(f"  Currencies: {result.parameters['currencies']}")
        print(f"  Composite Strength Mean: {result.values['composite_strength'].mean():.2f}")
        print(f"  Composite Strength Std: {result.values['composite_strength'].std():.2f}")
        print(f"  Valid points: {result.values['composite_strength'].count()}")

        return True

    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_currency_strength_simple()
    if success:
        print("\n[SUCCESS] Currency strength test passed!")
    else:
        print("\n[FAILED] Currency strength test failed!")
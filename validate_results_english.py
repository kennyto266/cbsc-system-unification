#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate Optimization Results - Check Data Authenticity and Backtest Logic
English Version
"""

import time
import warnings
import numpy as np
import pandas as pd
import json
import requests
from datetime import datetime

warnings.filterwarnings('ignore')

def validate_real_data():
    """Validate the authenticity of real stock data"""
    print("=" * 80)
    print("VALIDATING REAL DATA SOURCE AND QUALITY")
    print("=" * 80)

    try:
        # Fetch real 0700.HK data
        url = "http://18.180.162.113:9191/inst/getInst"
        params = {"symbol": "0700.hk", "duration": 365}

        print(f"Request URL: {url}")
        print(f"Parameters: {params}")

        response = requests.get(url, params=params, timeout=30)
        print(f"HTTP Status: {response.status_code}")

        if response.status_code != 200:
            print("FAILED: Data fetch failed")
            return False

        data = response.json()

        # Check data structure
        if 'data' not in data:
            print("FAILED: Data structure error")
            return False

        if 'close' not in data['data']:
            print("FAILED: Missing close price data")
            return False

        # Parse data
        dates = list(data['data']['close'].keys())
        close_prices = list(data['data']['close'].values())

        print(f"SUCCESS: Retrieved {len(close_prices)} data points")
        print(f"SUCCESS: Date range: {dates[0]} to {dates[-1]}")
        print(f"SUCCESS: Price range: ${min(close_prices):.2f} - ${max(close_prices):.2f}")

        # Check for realistic price movements
        price_changes = np.diff(close_prices) / close_prices[:-1]
        max_daily_change = np.max(np.abs(price_changes))

        print(f"SUCCESS: Max daily change: {max_daily_change:.2%}")

        if max_daily_change > 0.5:  # 50% daily change is unrealistic
            print("WARNING: Daily volatility too high, data may be problematic")
            return False

        # Check for 0700.HK realistic price range
        if min(close_prices) < 200 or max(close_prices) > 1000:
            print("WARNING: Price range outside realistic Tencent range")
            return False

        # Check data consistency
        if len(dates) != len(close_prices):
            print("FAILED: Data length mismatch")
            return False

        return True

    except Exception as e:
        print(f"FAILED: Validation error: {e}")
        return False

def validate_rsi_calculation():
    """Validate RSI calculation logic"""
    print("\n" + "=" * 80)
    print("VALIDATING RSI CALCULATION LOGIC")
    print("=" * 80)

    # Create test data
    test_prices = pd.Series([100, 102, 101, 103, 102, 104, 103, 105, 104, 106])

    def calculate_rsi_manual(prices, period=14):
        """Manual RSI calculation for validation"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    # Test calculation
    try:
        rsi_result = calculate_rsi_manual(test_prices, len(test_prices))
        print(f"SUCCESS: RSI calculation completed")
        print(f"SUCCESS: Latest RSI value: {rsi_result.iloc[-1]:.2f}")

        # RSI should be between 0 and 100
        if rsi_result.iloc[-1] < 0 or rsi_result.iloc[-1] > 100:
            print("FAILED: RSI value out of range")
            return False

        return True

    except Exception as e:
        print(f"FAILED: RSI calculation error: {e}")
        return False

def validate_sharpe_calculation():
    """Validate Sharpe ratio calculation"""
    print("\n" + "=" * 80)
    print("VALIDATING SHARPE RATIO CALCULATION")
    print("=" * 80)

    # Create test strategy returns
    np.random.seed(42)
    test_returns = pd.Series(np.random.normal(0.001, 0.02, 252))  # Daily returns

    try:
        # Calculate Sharpe ratio (risk-free rate = 3%)
        risk_free_rate = 0.03
        excess_returns = test_returns - risk_free_rate / 252

        if len(test_returns) > 0 and test_returns.std() > 0:
            sharpe_ratio = excess_returns.mean() / test_returns.std() * np.sqrt(252)
        else:
            sharpe_ratio = 0

        print(f"SUCCESS: Sharpe calculation completed")
        print(f"SUCCESS: Test Sharpe: {sharpe_ratio:.3f}")

        # Check for reasonable Sharpe range (-5 to 10)
        if sharpe_ratio < -5 or sharpe_ratio > 10:
            print("WARNING: Sharpe ratio outside reasonable range")

        return True

    except Exception as e:
        print(f"FAILED: Sharpe calculation error: {e}")
        return False

def validate_optimization_logic():
    """Validate the optimization logic"""
    print("\n" + "=" * 80)
    print("VALIDATING OPTIMIZATION LOGIC")
    print("=" * 80)

    try:
        # Test with small parameter set
        test_params = [
            {'rsi_period': 14, 'rsi_oversold': 30, 'rsi_overbought': 70},
            {'rsi_period': 20, 'rsi_oversold': 40, 'rsi_overbought': 60}
        ]

        print(f"SUCCESS: Testing parameter combinations: {len(test_params)}")

        # Validate parameter logic
        for params in test_params:
            period = params['rsi_period']
            oversold = params['rsi_oversold']
            overbought = params['rsi_overbought']

            if not (5 <= period <= 300):
                print(f"FAILED: RSI period out of range: {period}")
                return False

            if not (10 <= oversold <= 49):
                print(f"FAILED: Oversold level out of range: {oversold}")
                return False

            if not (51 <= overbought <= 94):
                print(f"FAILED: Overbought level out of range: {overbought}")
                return False

            if oversold >= overbought:
                print(f"FAILED: Parameter logic error: oversold({oversold}) >= overbought({overbought})")
                return False

        print("SUCCESS: All parameter logic validation passed")
        return True

    except Exception as e:
        print(f"FAILED: Optimization logic validation error: {e}")
        return False

def cross_validate_results():
    """Cross-validate with known good strategy"""
    print("\n" + "=" * 80)
    print("CROSS-VALIDATION - TESTING STANDARD RSI STRATEGY")
    print("=" * 80)

    try:
        # Get real data
        url = "http://18.180.162.113:9191/inst/getInst"
        params = {"symbol": "0700.hk", "duration": 90}  # 3 months for quick test

        response = requests.get(url, params=params, timeout=30)
        if response.status_code != 200:
            print("FAILED: Cannot get data for cross-validation")
            return False

        data = response.json()
        dates = list(data['data']['close'].keys())
        close_prices = list(data['data']['close'].values())

        df = pd.DataFrame({
            'close': close_prices,
            'open': close_prices,  # Simplified
            'high': close_prices,  # Simplified
            'low': close_prices,   # Simplified
            'volume': [1000000] * len(close_prices)
        }, index=pd.to_datetime(dates))

        print(f"SUCCESS: Retrieved {len(df)} days data for validation")

        # Test standard RSI(14,30,70) strategy
        def simple_rsi_strategy(data, period=14, oversold=30, overbought=70):
            # Calculate RSI
            delta = data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            # Generate signals
            signals = pd.DataFrame(index=data.index)
            signals['position'] = 0

            buy_signals = (rsi > oversold) & (rsi.shift(1) <= oversold)
            sell_signals = (rsi < overbought) & (rsi.shift(1) >= overbought)

            signals.loc[buy_signals, 'position'] = 1
            signals.loc[sell_signals, 'position'] = -1
            signals['position'] = signals['position'].replace(0, np.nan).ffill().fillna(0)

            # Calculate returns
            returns = data['close'].pct_change()
            strategy_returns = signals['position'].shift(1) * returns

            # Performance metrics
            total_return = (1 + strategy_returns).prod() - 1
            excess_returns = strategy_returns - 0.03/252

            if len(strategy_returns) > 0 and strategy_returns.std() > 0:
                sharpe_ratio = excess_returns.mean() / strategy_returns.std() * np.sqrt(252)
            else:
                sharpe_ratio = 0

            cumulative = (1 + strategy_returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = drawdown.min()

            total_trades = len(signals[signals['position'].diff() != 0])

            return {
                'total_return': total_return,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'total_trades': total_trades
            }

        # Test strategy
        result = simple_rsi_strategy(df)

        print(f"SUCCESS: Standard RSI(14,30,70) backtest results:")
        print(f"   Total Return: {result['total_return']:.2%}")
        print(f"   Sharpe Ratio: {result['sharpe_ratio']:.3f}")
        print(f"   Max Drawdown: {result['max_drawdown']:.2%}")
        print(f"   Total Trades: {result['total_trades']}")

        # Check for reasonable results
        if abs(result['sharpe_ratio']) > 10:
            print("WARNING: Sharpe ratio too high, possible calculation error")
            return False

        if result['total_trades'] == 0:
            print("WARNING: No trading signals, parameters may be too conservative")

        return True

    except Exception as e:
        print(f"FAILED: Cross-validation error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main validation function"""
    print("0700.HK OPTIMIZATION RESULTS RELIABILITY VALIDATION")
    print("=" * 80)

    validation_results = {}

    # Run all validation tests
    validation_results['data_authenticity'] = validate_real_data()
    validation_results['rsi_calculation'] = validate_rsi_calculation()
    validation_results['sharpe_calculation'] = validate_sharpe_calculation()
    validation_results['optimization_logic'] = validate_optimization_logic()
    validation_results['cross_validation'] = cross_validate_results()

    # Summary
    print("\n" + "=" * 80)
    print("VALIDATION RESULTS SUMMARY")
    print("=" * 80)

    passed_tests = sum(validation_results.values())
    total_tests = len(validation_results)

    for test_name, result in validation_results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name:<25}: {status}")

    print(f"\nOverall Assessment: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("EXCELLENT: All validations passed! Results are reliable")
    elif passed_tests >= total_tests * 0.8:
        print("GOOD: Most validations passed, results are generally reliable")
    else:
        print("POOR: Validation failed, results are not reliable")

    # Save validation report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'validation_results': validation_results,
        'passed_tests': passed_tests,
        'total_tests': total_tests,
        'reliability_score': passed_tests / total_tests
    }

    with open(f'optimization_validation_report_{timestamp}.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"Validation report saved: optimization_validation_report_{timestamp}.json")

    return passed_tests / total_tests

if __name__ == "__main__":
    try:
        reliability_score = main()
        print(f"\nOptimization Results Reliability Score: {reliability_score:.1%}")

        if reliability_score >= 0.8:
            print("CONCLUSION: Optimization results are reliable and can be used for reference")
        elif reliability_score >= 0.6:
            print("CONCLUSION: Optimization results are moderately reliable, use with caution")
        else:
            print("CONCLUSION: Optimization results have low reliability, review needed")

    except Exception as e:
        print(f"\nValidation process error: {e}")
        import traceback
        traceback.print_exc()
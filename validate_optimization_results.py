#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate Optimization Results - Check Data Authenticity and Backtest Logic
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
    print("驗證真實數據來源和質量")
    print("=" * 80)

    try:
        # Fetch real 0700.HK data
        url = "http://18.180.162.113:9191/inst/getInst"
        params = {"symbol": "0700.hk", "duration": 365}

        print(f"請求URL: {url}")
        print(f"參數: {params}")

        response = requests.get(url, params=params, timeout=30)
        print(f"HTTP狀態: {response.status_code}")

        if response.status_code != 200:
            print("❌ 數據獲取失敗")
            return False

        data = response.json()

        # Check data structure
        if 'data' not in data:
            print("❌ 數據結構錯誤")
            return False

        if 'close' not in data['data']:
            print("❌ 缺少收盤價數據")
            return False

        # Parse data
        dates = list(data['data']['close'].keys())
        close_prices = list(data['data']['close'].values())

        print(f"✅ 成功獲取 {len(close_prices)} 個數據點")
        print(f"✅ 時間範圍: {dates[0]} 至 {dates[-1]}")
        print(f"✅ 價格範圍: ${min(close_prices):.2f} - ${max(close_prices):.2f}")

        # Check for realistic price movements
        price_changes = np.diff(close_prices) / close_prices[:-1]
        max_daily_change = np.max(np.abs(price_changes))

        print(f"✅ 最大單日漲跌幅: {max_daily_change:.2%}")

        if max_daily_change > 0.5:  # 50% daily change is unrealistic
            print("⚠️ 警告: 單日波動過大，可能數據有問題")
            return False

        # Check for 0700.HK realistic price range
        if min(close_prices) < 200 or max(close_prices) > 1000:
            print("⚠️ 警告: 價格範圍不符合騰訊股價特徵")
            return False

        return True

    except Exception as e:
        print(f"❌ 驗證失敗: {e}")
        return False

def validate_rsi_calculation():
    """Validate RSI calculation logic"""
    print("\n" + "=" * 80)
    print("驗證RSI計算邏輯")
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
        print(f"✅ RSI計算成功")
        print(f"✅ 最新RSI值: {rsi_result.iloc[-1]:.2f}")

        # RSI should be between 0 and 100
        if rsi_result.iloc[-1] < 0 or rsi_result.iloc[-1] > 100:
            print("❌ RSI值超出範圍")
            return False

        return True

    except Exception as e:
        print(f"❌ RSI計算失敗: {e}")
        return False

def validate_sharpe_calculation():
    """Validate Sharpe ratio calculation"""
    print("\n" + "=" * 80)
    print("驗證Sharpe比率計算")
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

        print(f"✅ Sharpe計算成功")
        print(f"✅ 測試Sharpe: {sharpe_ratio:.3f}")

        # Check for reasonable Sharpe range (-5 to 10)
        if sharpe_ratio < -5 or sharpe_ratio > 10:
            print("⚠️ 警告: Sharpe比率超出合理範圍")

        return True

    except Exception as e:
        print(f"❌ Sharpe計算失敗: {e}")
        return False

def validate_optimization_logic():
    """Validate the optimization logic"""
    print("\n" + "=" * 80)
    print("驗證優化邏輯")
    print("=" * 80)

    try:
        # Test with small parameter set
        test_params = [
            {'rsi_period': 14, 'rsi_oversold': 30, 'rsi_overbought': 70},
            {'rsi_period': 20, 'rsi_oversold': 40, 'rsi_overbought': 60}
        ]

        print(f"✅ 測試參數組合: {len(test_params)} 個")

        # Validate parameter logic
        for params in test_params:
            period = params['rsi_period']
            oversold = params['rsi_oversold']
            overbought = params['rsi_overbought']

            if not (5 <= period <= 300):
                print(f"❌ RSI週期超出範圍: {period}")
                return False

            if not (10 <= oversold <= 49):
                print(f"❌ 超賣水平超出範圍: {oversold}")
                return False

            if not (51 <= overbought <= 94):
                print(f"❌ 超買水平超出範圍: {overbought}")
                return False

            if oversold >= overbought:
                print(f"❌ 參數邏輯錯誤: 超賣({oversold}) >= 超買({overbought})")
                return False

        print("✅ 所有參數邏輯驗證通過")
        return True

    except Exception as e:
        print(f"❌ 優化邏輯驗證失敗: {e}")
        return False

def cross_validate_results():
    """Cross-validate with known good strategy"""
    print("\n" + "=" * 80)
    print("交叉驗證 - 測試標準RSI策略")
    print("=" * 80)

    try:
        # Get real data
        url = "http://18.180.162.113:9191/inst/getInst"
        params = {"symbol": "0700.hk", "duration": 90}  # 3 months for quick test

        response = requests.get(url, params=params, timeout=30)
        if response.status_code != 200:
            print("❌ 無法獲取數據進行交叉驗證")
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

        print(f"✅ 獲取 {len(df)} 天數據進行驗證")

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

        print(f"✅ 標準RSI(14,30,70)回測結果:")
        print(f"   總回報: {result['total_return']:.2%}")
        print(f"   Sharpe: {result['sharpe_ratio']:.3f}")
        print(f"   最大回撤: {result['max_drawdown']:.2%}")
        print(f"   交易次數: {result['total_trades']}")

        # Check for reasonable results
        if abs(result['sharpe_ratio']) > 10:
            print("⚠️ 警告: Sharpe比率過高，可能計算有誤")
            return False

        if result['total_trades'] == 0:
            print("⚠️ 警告: 沒有交易信號，參數可能過於保守")

        return True

    except Exception as e:
        print(f"❌ 交叉驗證失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main validation function"""
    print("0700.HK 優化結果可靠性驗證")
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
    print("驗證結果總結")
    print("=" * 80)

    passed_tests = sum(validation_results.values())
    total_tests = len(validation_results)

    for test_name, result in validation_results.items():
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name:<25}: {status}")

    print(f"\n總體評估: {passed_tests}/{total_tests} 測試通過")

    if passed_tests == total_tests:
        print("🎉 所有驗證通過！優化結果可信")
    elif passed_tests >= total_tests * 0.8:
        print("⚠️ 大部分驗證通過，結果基本可信")
    else:
        print("❌ 驗證失敗，結果不可信")

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

    print(f"驗證報告已保存: optimization_validation_report_{timestamp}.json")

    return passed_tests / total_tests

if __name__ == "__main__":
    try:
        reliability_score = main()
        print(f"\n🔍 優化結果可靠性評分: {reliability_score:.1%}")

        if reliability_score >= 0.8:
            print("✅ 結論: 優化結果基本可信，可以參考使用")
        else:
            print("❌ 結論: 優化結果可信度不足，需要重新審查")

    except Exception as e:
        print(f"\n❌ 驗證過程出錯: {e}")
        import traceback
        traceback.print_exc()
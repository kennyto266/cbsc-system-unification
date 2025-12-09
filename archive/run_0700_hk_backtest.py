#!/usr/bin/env python3
"""
0700.HK Backtest Runner
騰訊股票回測運行器

Clean backtest runner for 0700.HK using the refactored system
"""

import sys
import json
import time
import requests
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
sys.path.append('.')

from refactored_tech_analysis import (
    DataRepository,
    IndicatorFactory,
    BacktestEngine,
    OptimizationConfig,
    OptimizationOrchestrator
)


def run_0700_hk_backtest():
    """Run clean backtest for 0700.HK"""
    print("0700.HK BACKTEST RUNNER")
    print("騰訊股票回測運行器")
    print("=" * 50)

    try:
        # Step 1: Get stock data
        print("\n1. LOADING 0700.HK DATA")
        print("-" * 30)

        repo = DataRepository()
        stock_data = repo.get_stock_data('0700.HK', 365)

        print(f"[OK] Stock data loaded: {len(stock_data)} records")

        # Verify API data
        url = "http://18.180.162.113:9191/inst/getInst"
        response = requests.get(url, params={"symbol": "0700.hk", "duration": 365}, timeout=10)

        if response.status_code == 200:
            api_data = response.json()
            api_points = len(api_data['data']['close'])
            print(f"[OK] API data: {api_points} points")
            dates = list(api_data['data']['close'].keys())
            prices = list(api_data['data']['close'].values())
            print(f"    Date range: {dates[0]} to {dates[-1]}")
            print(f"    Price range: {min(prices):.2f} - {max(prices):.2f}")

        # Step 2: Create simple indicators
        print("\n2. CREATING TECHNICAL INDICATORS")
        print("-" * 30)

        factory = IndicatorFactory(repo)

        # Simple RSI strategies
        rsi_strategies = [
            {'strategy': 'RSI', 'data_source': 'stock', 'params': {'period': 14}},
            {'strategy': 'RSI', 'data_source': 'stock', 'params': {'period': 21}},
            {'strategy': 'RSI', 'data_source': 'stock', 'params': {'period': 30}},
        ]

        indicators = {}
        for i, strategy_config in enumerate(rsi_strategies):
            try:
                indicator = factory.create_indicator(
                    strategy_config['strategy'],
                    strategy_config['data_source'],
                    strategy_config['params']
                )
                if indicator is not None and len(indicator) > 0:
                    strategy_name = f"RSI_{strategy_config['params']['period']}"
                    indicators[strategy_name] = indicator
                    print(f"[OK] {strategy_name}: {len(indicator)} values")
                else:
                    print(f"[WARN] {strategy_config['params']['period']}: No data")
            except Exception as e:
                print(f"[ERROR] RSI {strategy_config['params']['period']}: {e}")

        # Step 3: Run backtests
        print("\n3. RUNNING BACKTESTS")
        print("-" * 30)

        engine = BacktestEngine()

        # Get price data for backtesting
        if hasattr(stock_data, 'close'):
            prices = stock_data['close']
        else:
            prices = stock_data

        all_results = []

        for strategy_name, indicator in indicators.items():
            try:
                # Convert indicator to trading signals
                if len(indicator) == len(prices):
                    # Simple signal: buy when RSI < 30, sell when RSI > 70
                    signals = pd.Series(0, index=prices.index)

                    # Get period from strategy name
                    if 'RSI_14' in strategy_name:
                        signals = (indicator < 30).astype(int) - (indicator > 70).astype(int)
                    elif 'RSI_21' in strategy_name:
                        signals = (indicator < 25).astype(int) - (indicator > 75).astype(int)
                    elif 'RSI_30' in strategy_name:
                        signals = (indicator < 20).astype(int) - (indicator > 80).astype(int)

                    # Run backtest
                    result = engine.backtest_strategy(signals, prices, f"0700_HK_{strategy_name}")

                    print(f"[OK] {strategy_name}:")
                    print(f"    Return: {result.total_return:.2%}")
                    print(f"    Sharpe: {result.sharpe_ratio:.3f}")
                    print(f"    Max DD: {result.max_drawdown:.2%}")
                    print(f"    Quality: {result.quality_score:.1f}")

                    all_results.append({
                        'strategy': strategy_name,
                        'total_return': result.total_return,
                        'sharpe_ratio': result.sharpe_ratio,
                        'max_drawdown': result.max_drawdown,
                        'quality_score': result.quality_score,
                        'success': True
                    })
                else:
                    print(f"[WARN] {strategy_name}: Length mismatch")

            except Exception as e:
                print(f"[ERROR] {strategy_name}: {e}")
                all_results.append({
                    'strategy': strategy_name,
                    'error': str(e),
                    'success': False
                })

        # Step 4: Generate summary
        print("\n4. BACKTEST SUMMARY")
        print("-" * 30)

        successful_results = [r for r in all_results if r['success']]

        print(f"Total strategies tested: {len(all_results)}")
        print(f"Successful strategies: {len(successful_results)}")
        print(f"Success rate: {len(successful_results)/len(all_results)*100:.1f}%")

        if successful_results:
            # Find best strategy
            best_strategy = max(successful_results, key=lambda x: x['sharpe_ratio'])
            print(f"\nBest performing strategy:")
            print(f"  Strategy: {best_strategy['strategy']}")
            print(f"  Return: {best_strategy['total_return']:.2%}")
            print(f"  Sharpe: {best_strategy['sharpe_ratio']:.3f}")
            print(f"  Max Drawdown: {best_strategy['max_drawdown']:.2%}")
            print(f"  Quality Score: {best_strategy['quality_score']:.1f}")

            # Validate Sharpe ratio
            if 0.5 <= best_strategy['sharpe_ratio'] <= 3.0:
                print(f"  [OK] Sharpe ratio is in expected range")
            else:
                print(f"  [WARN] Sharpe ratio outside expected range")

        # Step 5: Save results
        print("\n5. SAVING RESULTS")
        print("-" * 30)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"0700_hk_backtest_results_{timestamp}.json"

        results_data = {
            'stock_symbol': '0700.HK',
            'backtest_timestamp': timestamp,
            'data_points': len(prices),
            'api_data_points': api_points if 'api_points' in locals() else 0,
            'strategies_tested': len(all_results),
            'successful_strategies': len(successful_results),
            'best_strategy': best_strategy if successful_results else None,
            'all_results': all_results,
            'summary': {
                'total_return': best_strategy['total_return'] if successful_results else 0,
                'sharpe_ratio': best_strategy['sharpe_ratio'] if successful_results else 0,
                'max_drawdown': best_strategy['max_drawdown'] if successful_results else 0,
                'quality_score': best_strategy['quality_score'] if successful_results else 0
            }
        }

        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)

        print(f"[OK] Results saved: {results_file}")

        # Step 6: Final assessment
        print(f"\n" + "=" * 50)
        print(f"0700.HK BACKTEST COMPLETED")
        print(f"=" * 50)

        if successful_results:
            print(f"[SUCCESS] Backtest completed successfully!")
            print(f"Best strategy: {best_strategy['strategy']}")
            print(f"Sharpe ratio: {best_strategy['sharpe_ratio']:.3f}")
            return True
        else:
            print(f"[FAILED] No successful strategies found")
            return False

    except Exception as e:
        print(f"[ERROR] Backtest failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main backtest execution"""
    print("Starting 0700.HK backtest with refactored system...")

    success = run_0700_hk_backtest()

    if success:
        print(f"\n[SUCCESS] 0700.HK backtest completed successfully!")
        print("Refactored system is working correctly.")
        return True
    else:
        print(f"\n[FAILED] 0700.HK backtest failed!")
        print("Check logs for errors.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
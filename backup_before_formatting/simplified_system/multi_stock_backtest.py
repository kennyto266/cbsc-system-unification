#!/usr/bin/env python3
"""
多股票量化回測分析
Multi-Stock Quantitative Backtest Analysis
"""

import sys
import os
import json
from datetime import datetime

sys.path.append('src')

try:
    from api.stock_api import get_hk_stock_data
    from backtest.vectorbt_engine import VectorBTEngine

    def run_multi_stock_analysis():
        """運行多股票量化分析"""
        symbols = ['0700.HK', '0941.HK', '1398.HK', '0388.HK', '1299.HK']
        results = {}

        print("=" * 80)
        print("港股多股票量化回測分析")
        print("HONG KONG STOCKS QUANTITATIVE BACKTEST ANALYSIS")
        print("=" * 80)

        engine = VectorBTEngine()

        for symbol in symbols:
            print(f"\n=== 測試 {symbol} ===")

            try:
                # 獲取股票數據
                data = get_hk_stock_data(symbol, 252)  # 1年數據

                if data is not None and not data.empty:
                    print(f"[OK] 獲取數據: {len(data)} 條記錄")
                    print(f"價格範圍: ${data['low'].min():.2f} - ${data['high'].max():.2f}")

                    # 測試最佳策略
                    strategies = [
                        ('RSI_MEAN_REVERSION', {'period': 18, 'oversold': 25, 'overbought': 70}),
                        ('DUAL_MOVING_AVERAGE', {'short_period': 10, 'long_period': 70}),
                        ('MACD_CROSSOVER', {'fast': 8, 'slow': 30, 'signal': 12})
                    ]

                    symbol_results = []

                    for strategy_name, params in strategies:
                        try:
                            result = engine.backtest_strategy(data, strategy_name, params)
                            if result:
                                symbol_results.append({
                                    'strategy': strategy_name,
                                    'total_return': result.get('total_return', 0),
                                    'sharpe_ratio': result.get('sharpe_ratio', 0),
                                    'max_drawdown': result.get('max_drawdown', 0),
                                    'win_rate': result.get('win_rate', 0),
                                    'trades': result.get('total_trades', 0)
                                })
                                print(f"  {strategy_name}: 回報 {result.get('total_return', 0):.1%}, Sharpe {result.get('sharpe_ratio', 0):.3f}")
                            else:
                                print(f"  {strategy_name}: 測試失敗")
                        except Exception as e:
                            print(f"  {strategy_name}: 錯誤 - {str(e)}")

                    # 找到最佳策略
                    if symbol_results:
                        best_strategy = max(symbol_results, key=lambda x: x['sharpe_ratio'])
                        results[symbol] = {
                            'best_strategy': best_strategy,
                            'all_results': symbol_results,
                            'data_points': len(data)
                        }
                        print(f"  [OK] 最佳策略: {best_strategy['strategy']} (Sharpe: {best_strategy['sharpe_ratio']:.3f})")
                    else:
                        results[symbol] = {'error': 'No successful strategies'}
                        print(f"  [FAIL] 無有效策略")
                else:
                    print(f"[FAIL] 無法獲取 {symbol} 數據")
                    results[symbol] = {'error': 'No data available'}

            except Exception as e:
                print(f"[ERROR] {symbol}: {str(e)}")
                results[symbol] = {'error': str(e)}

        # 生成綜合報告
        print("\n" + "=" * 80)
        print("綜合分析報告")
        print("COMPREHENSIVE ANALYSIS REPORT")
        print("=" * 80)

        valid_results = {k: v for k, v in results.items() if 'best_strategy' in v}

        if valid_results:
            print(f"成功測試股票: {len(valid_results)}")

            # 按Sharpe比率排序
            sorted_stocks = sorted(valid_results.items(), key=lambda x: x[1]['best_strategy']['sharpe_ratio'], reverse=True)

            print("\n股票排名 (按Sharpe比率):")
            print("-" * 60)
            for i, (symbol, data) in enumerate(sorted_stocks, 1):
                best = data['best_strategy']
                print(f"{i}. {symbol}: Sharpe {best['sharpe_ratio']:.3f}, 回報 {best['total_return']:.1%}, {best['strategy']}")

            # 最佳策略統計
            strategy_counts = {}
            for symbol, data in valid_results.items():
                strategy_name = data['best_strategy']['strategy']
                strategy_counts[strategy_name] = strategy_counts.get(strategy_name, 0) + 1

            print(f"\n最佳策略分布:")
            for strategy, count in strategy_counts.items():
                print(f"  {strategy}: {count}隻股票")

            # 保存結果
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            with open(f"multi_stock_backtest_{timestamp}.json", 'w') as f:
                json.dump({
                    'test_timestamp': datetime.now().isoformat(),
                    'results': results,
                    'valid_stocks': len(valid_results),
                    'best_performer': sorted_stocks[0] if sorted_stocks else None
                }, f, indent=2, default=str)

            print(f"\n結果已保存: multi_stock_backtest_{timestamp}.json")

        else:
            print("無成功測試的股票")

        print("\n" + "=" * 80)
        return results

    if __name__ == "__main__":
        run_multi_stock_analysis()

except ImportError as e:
    print(f"[IMPORT ERROR] {e}")
    print("請確保所有必需模塊已正確安裝")
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
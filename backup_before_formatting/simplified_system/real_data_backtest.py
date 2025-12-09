#!/usr/bin/env python3
"""
真實數據量化回測
Real Data Quantitative Backtest
"""

import sys
import os
import time
import json
from datetime import datetime

sys.path.append('src')

try:
    from api.stock_api import get_hk_stock_data
    from backtest.vectorbt_engine import VectorBTEngine
    import pandas as pd

    def convert_dict_to_dataframe(data_dict):
        """將API返回的字典數據轉換為DataFrame"""
        if not isinstance(data_dict, dict) or 'data' not in data_dict:
            return None

        data = data_dict['data']
        if 'close' not in data:
            return None

        # 構建DataFrame
        df_data = []
        for date in data['close'].keys():
            row = {
                'date': date,
                'open': data.get('open', {}).get(date, data['close'][date]),
                'high': data.get('high', {}).get(date, data['close'][date]),
                'low': data.get('low', {}).get(date, data['close'][date]),
                'close': data['close'][date],
                'volume': data.get('volume', {}).get(date, 1000000)
            }
            df_data.append(row)

        df = pd.DataFrame(df_data)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        return df

    def run_real_data_backtest():
        """運行真實數據回測"""
        print("=" * 80)
        print("0700.HK TENCENT - 真實數據量化回測")
        print("0700.HK TENCENT - REAL DATA QUANTITATIVE BACKTEST")
        print("=" * 80)
        print("這將使用真實市場數據，可能需要較長時間...")

        # 獲取真實數據
        print("\n=== 獲取真實市場數據 ===")
        start_time = time.time()

        try:
            raw_data = get_hk_stock_data('0700.HK', 365)
            data_fetch_time = time.time() - start_time

            if raw_data is not None:
                print(f"[OK] 數據獲取成功，耗時: {data_fetch_time:.2f} 秒")

                # 轉換數據格式
                df = convert_dict_to_dataframe(raw_data)

                if df is not None and len(df) > 0:
                    print(f"[OK] 數據轉換成功: {len(df)} 條記錄")
                    print(f"日期範圍: {df.index[0]} 到 {df.index[-1]}")
                    print(f"價格範圍: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
                    print(f"最新價格: ${df['close'].iloc[-1]:.2f}")
                else:
                    print("[FAIL] 數據轉換失敗")
                    return
            else:
                print("[FAIL] 無法獲取數據")
                return

        except Exception as e:
            print(f"[ERROR] 數據獲取失敗: {e}")
            return

        # 初始化回測引擎
        print("\n=== 初始化回測引擎 ===")
        try:
            engine = VectorBTEngine()
            print("[OK] VectorBT引擎初始化成功")
        except Exception as e:
            print(f"[ERROR] 引擎初始化失敗: {e}")
            return

        # 測試多個策略
        print("\n=== 開始策略回測 ===")
        strategies = [
            ('RSI_MEAN_REVERSION', {'period': 18, 'oversold': 25, 'overbought': 70}),
            ('DUAL_MOVING_AVERAGE', {'short_period': 10, 'long_period': 70}),
            ('MACD_CROSSOVER', {'fast': 8, 'slow': 30, 'signal': 12}),
            ('RSI_MEAN_REVERSION', {'period': 21, 'oversold': 35, 'overbought': 70}),
            ('DUAL_MOVING_AVERAGE', {'short_period': 20, 'long_period': 50})
        ]

        results = []
        total_start_time = time.time()

        for i, (strategy_name, params) in enumerate(strategies, 1):
            print(f"\n測試策略 {i}/{len(strategies)}: {strategy_name}")
            strategy_start_time = time.time()

            try:
                result = engine.backtest_strategy(df, strategy_name, params)
                strategy_time = time.time() - strategy_start_time

                if result:
                    results.append({
                        'strategy': strategy_name,
                        'params': params,
                        'total_return': result.get('total_return', 0),
                        'sharpe_ratio': result.get('sharpe_ratio', 0),
                        'max_drawdown': result.get('max_drawdown', 0),
                        'win_rate': result.get('win_rate', 0),
                        'trades': result.get('total_trades', 0),
                        'calculation_time': strategy_time
                    })
                    print(f"  [OK] 總回報: {result.get('total_return', 0):.1%}")
                    print(f"       Sharpe比率: {result.get('sharpe_ratio', 0):.3f}")
                    print(f"       最大回撤: {result.get('max_drawdown', 0):.1%}")
                    print(f"       計算時間: {strategy_time:.3f}秒")
                else:
                    print(f"  [FAIL] 策略測試失敗")

            except Exception as e:
                print(f"  [ERROR] 策略測試錯誤: {e}")

        total_time = time.time() - total_start_time

        # 生成報告
        print("\n" + "=" * 80)
        print("真實數據回測結果報告")
        print("REAL DATA BACKTEST REPORT")
        print("=" * 80)

        if results:
            print(f"成功測試策略: {len(results)}")
            print(f"總執行時間: {total_time:.2f} 秒")
            print(f"數據獲取時間: {data_fetch_time:.2f} 秒")
            print(f"回測計算時間: {total_time - data_fetch_time:.2f} 秒")

            # 按Sharpe比率排序
            sorted_results = sorted(results, key=lambda x: x['sharpe_ratio'], reverse=True)

            print(f"\n策略排名 (按Sharpe比率):")
            print("-" * 70)
            for i, result in enumerate(sorted_results, 1):
                params_str = str(result['params'])
                print(f"{i}. {result['strategy']}")
                print(f"   參數: {params_str}")
                print(f"   Sharpe: {result['sharpe_ratio']:.3f}, 回報: {result['total_return']:.1%}, 回撤: {result['max_drawdown']:.1%}")

            # 保存結果
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report = {
                'test_info': {
                    'symbol': '0700.HK',
                    'test_date': datetime.now().isoformat(),
                    'data_source': 'REAL_API_DATA',
                    'data_fetch_time': data_fetch_time,
                    'total_calculation_time': total_time,
                    'data_records': len(df),
                    'price_range': {
                        'min': float(df['low'].min()),
                        'max': float(df['high'].max()),
                        'latest': float(df['close'].iloc[-1])
                    }
                },
                'results': results,
                'best_strategy': sorted_results[0] if sorted_results else None,
                'performance_summary': {
                    'total_strategies_tested': len(strategies),
                    'successful_strategies': len(results),
                    'average_sharpe': sum(r['sharpe_ratio'] for r in results) / len(results) if results else 0
                }
            }

            report_file = f'real_data_backtest_{timestamp}.json'
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)

            print(f"\n報告已保存: {report_file}")

        else:
            print("[FAIL] 無成功的策略測試")

        print("\n" + "=" * 80)
        print("真實數據回測完成")
        print("REAL DATA BACKTEST COMPLETED")
        print("=" * 80)

    if __name__ == "__main__":
        run_real_data_backtest()

except ImportError as e:
    print(f"[IMPORT ERROR] {e}")
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
#!/usr / bin / env python3
"""
大規模參數優化器
Massive Parameter Optimizer
測試上萬個策略組合
"""

import json
import multiprocessing as mp
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime

import numpy as np


def calculate_correct_sharpe_ratio(returns, risk_free_rate = 0.03):
    """
    計算正確的Sharpe比率

    Args:
        returns: 收益率列表 (日收益率)
        risk_free_rate: 年化無風險利率 (默認3%)

    Returns:
        float: 正確的年化Sharpe比率
    """
    if not returns or len(returns) < 2:
        return 0.0

    # 過濾無效值
    returns = [r for r in returns if r is not None and not np.isnan(r) and not np.isinf(r)]

    if len(returns) < 2:
        return 0.0

    # 轉換為numpy數組
    returns_array = np.array(returns)

    # 計算日化無風險利率
    daily_rf_rate = risk_free_rate / 252

    # 計算超額收益
    excess_returns = returns_array - daily_rf_rate

    # 計算標準差
    std_excess = excess_returns.std()

    # 如果標準差為0，返回0 (避免除零錯誤)
    if std_excess == 0:
        return 0.0

    # 計算正確的年化Sharpe比率
    sharpe_ratio = excess_returns.mean() / std_excess * np.sqrt(252)

    # 限制在合理範圍內 (-10 到 10)
    sharpe_ratio = np.clip(sharpe_ratio, -10.0, 10.0)

    return sharpe_ratio

sys.path.append('src')

try:
    import pandas as pd

    from api.stock_api import get_hk_stock_data

    def calculate_rsi(prices, period):
        """計算RSI指標"""
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        # 使用指數移動平均
        alpha = 1.0 / period
        avg_gain = gains[0]
        avg_loss = losses[0]

        rsi_values = []
        for i in range(len(gains)):
            if i == 0:
                avg_gain = gains[0]
                avg_loss = losses[0]
            else:
                avg_gain = alpha * gains[i] + (1 - alpha) * avg_gain
                avg_loss = alpha * losses[i] + (1 - alpha) * avg_loss

            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            rsi_values.append(rsi)

        return [50] + rsi_values  # 第一個值用50

    def calculate_macd(prices, fast, slow, signal):
        """計算MACD指標"""
        # 計算EMA
        def ema(data, period):
            alpha = 2.0 / (period + 1)
            ema_values = [data[0]]
            for i in range(1, len(data)):
                ema_values.append(alpha * data[i] + (1 - alpha) * ema_values[-1])
            return ema_values

        fast_ema = ema(prices, fast)
        slow_ema = ema(prices, slow)

        # 對齊長度
        min_len = min(len(fast_ema), len(slow_ema))
        fast_ema = fast_ema[-min_len:]
        slow_ema = slow_ema[-min_len:]

        macd_line = [f - s for f, s in zip(fast_ema, slow_ema)]
        signal_line = ema(macd_line, signal)

        return macd_line, signal_line

    def calculate_sma(prices, period):
        """計算簡單移動平均"""
        sma_values = []
        for i in range(len(prices)):
            if i < period - 1:
                sma_values.append(np.mean(prices[:i + 1]))
            else:
                sma_values.append(np.mean(prices[i - period + 1:i + 1]))
        return sma_values

    def backtest_rsi_strategy(params):
        """RSI策略回測"""
        prices, period, oversold, overbought = params
        rsi = calculate_rsi(prices, period)

        trades = []
        position = False
        entry_price = 0

        for i in range(1, len(prices)):
            if not position and rsi[i] < oversold:
                position = True
                entry_price = prices[i]
            elif position and rsi[i] > overbought:
                position = False
                if entry_price > 0:
                    return_pct = (prices[i] - entry_price) / entry_price
                    trades.append(return_pct)
                    entry_price = 0

        if trades:
            total_return = sum(trades)
            avg_return = np.mean(trades)
            win_rate = len([t for t in trades if t > 0]) / len(trades)
            # 使用正確的Sharpe比率計算
            sharpe_ratio = calculate_correct_sharpe_ratio(trades, risk_free_rate = 0.03)
            max_drawdown = min(trades) if trades else 0
        else:
            total_return = avg_return = win_rate = sharpe_ratio = max_drawdown = 0

        return {
            'strategy': 'RSI_MEAN_REVERSION',
            'params': {'period': period, 'oversold': oversold, 'overbought': overbought},
            'total_return': total_return,
            'avg_return': avg_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'trades': len(trades)
        }

    def backtest_macd_strategy(params):
        """MACD策略回測"""
        prices, fast, slow, signal = params
        try:
            macd_line, signal_line = calculate_macd(prices, fast, slow, signal)

            trades = []
            position = False
            entry_price = 0

            min_len = min(len(macd_line), len(signal_line), len(prices))

            for i in range(1, min_len):
                if not position and macd_line[i] > signal_line[i] and macd_line[i - 1] <= signal_line[i - 1]:
                    position = True
                    entry_price = prices[i]
                elif position and macd_line[i] < signal_line[i] and macd_line[i - 1] >= signal_line[i - 1]:
                    position = False
                    if entry_price > 0:
                        return_pct = (prices[i] - entry_price) / entry_price
                        trades.append(return_pct)
                        entry_price = 0

            if trades:
                total_return = sum(trades)
                avg_return = np.mean(trades)
                win_rate = len([t for t in trades if t > 0]) / len(trades)
                # 使用正確的Sharpe比率計算
            sharpe_ratio = calculate_correct_sharpe_ratio(trades, risk_free_rate = 0.03)
            max_drawdown = min(trades) if trades else 0
            else:
                total_return = avg_return = win_rate = sharpe_ratio = max_drawdown = 0

            return {
                'strategy': 'MACD_CROSSOVER',
                'params': {'fast': fast, 'slow': slow, 'signal': signal},
                'total_return': total_return,
                'avg_return': avg_return,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'win_rate': win_rate,
                'trades': len(trades)
            }
        except Exception as e:
            return None

    def backtest_ma_strategy(params):
        """移動平均策略回測"""
        prices, short_period, long_period = params
        short_ma = calculate_sma(prices, short_period)
        long_ma = calculate_sma(prices, long_period)

        trades = []
        position = False
        entry_price = 0

        for i in range(1, len(prices)):
            if not position and short_ma[i] > long_ma[i] and short_ma[i - 1] <= long_ma[i - 1]:
                position = True
                entry_price = prices[i]
            elif position and short_ma[i] < long_ma[i] and short_ma[i - 1] >= long_ma[i - 1]:
                position = False
                if entry_price > 0:
                    return_pct = (prices[i] - entry_price) / entry_price
                    trades.append(return_pct)
                    entry_price = 0

        if trades:
            total_return = sum(trades)
            avg_return = np.mean(trades)
            win_rate = len([t for t in trades if t > 0]) / len(trades)
            # 使用正確的Sharpe比率計算
            sharpe_ratio = calculate_correct_sharpe_ratio(trades, risk_free_rate = 0.03)
            max_drawdown = min(trades) if trades else 0
        else:
            total_return = avg_return = win_rate = sharpe_ratio = max_drawdown = 0

        return {
            'strategy': 'DUAL_MOVING_AVERAGE',
            'params': {'short_period': short_period, 'long_period': long_period},
            'total_return': total_return,
            'avg_return': avg_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'trades': len(trades)
        }

    def generate_parameter_combinations():
        """生成大量參數組合"""
        print("生成參數組合...")

        # RSI參數組合
        rsi_params = []
        rsi_periods = range(5, 51, 2)  # 5 - 50，步長2
        oversold_levels = range(10, 36, 5)  # 10 - 35，步長5
        overbought_levels = range(65, 86, 5)  # 65 - 85，步長5

        for period in rsi_periods:
            for oversold in oversold_levels:
                for overbought in overbought_levels:
                    if oversold < overbought:
                        rsi_params.append((period, oversold, overbought))

        # MACD參數組合
        macd_params = []
        fast_periods = range(5, 21, 3)  # 5 - 20，步長3
        slow_periods = range(20, 51, 5)  # 20 - 50，步長5
        signal_periods = range(5, 16, 3)  # 5 - 15，步長3

        for fast in fast_periods:
            for slow in slow_periods:
                for signal in signal_periods:
                    if fast < slow:
                        macd_params.append((fast, slow, signal))

        # 移動平均參數組合
        ma_params = []
        short_periods = range(5, 31, 3)  # 5 - 30，步長3
        long_periods = range(20, 101, 5)  # 20 - 100，步長5

        for short in short_periods:
            for long in long_periods:
                if short < long:
                    ma_params.append((short, long))

        total_combinations = len(rsi_params) + len(macd_params) + len(ma_params)
        print(f"參數組合生成完成:")
        print(f"  RSI策略: {len(rsi_params):,} 組合")
        print(f"  MACD策略: {len(macd_params):,} 組合")
        print(f"  移動平均策略: {len(ma_params):,} 組合")
        print(f"  總計: {total_combinations:,} 組合")

        return rsi_params, macd_params, ma_params

    def run_massive_optimization():
        """運行大規模優化"""
        print("=" * 80)
        print("大規模參數優化系統")
        print("MASSIVE PARAMETER OPTIMIZATION SYSTEM")
        print("=" * 80)
        print("準備測試上萬個策略組合...")

        # 獲取真實數據
        print("\n[1 / 5] 獲取真實市場數據...")
        start_time = time.time()

        try:
            raw_data = get_hk_stock_data('0700.HK', 730)  # 2年數據

            if raw_data and 'data' in raw_data and 'close' in raw_data['data']:
                close_data = raw_data['data']['close']
                prices = list(close_data.values())

                data_time = time.time() - start_time
                print(f"   [OK] 獲取真實數據: {len(prices):,} 條記錄")
                print(f"   數據獲取耗時: {data_time:.2f} 秒")

                # 生成參數組合
                rsi_params, macd_params, ma_params = generate_parameter_combinations()

                # 準備測試參數
                test_params = []
                for params in rsi_params:
                    test_params.append(('RSI', (prices,) + params))
                for params in macd_params:
                    test_params.append(('MACD', (prices,) + params))
                for params in ma_params:
                    test_params.append(('MA', (prices,) + params))

                total_tests = len(test_params)
                print(f"\n[2 / 5] 準備測試 {total_tests:,} 個策略組合...")

                # 多進程執行
                print("\n[3 / 5] 開始大規模並行測試...")
                print(f"使用 {mp.cpu_count()} 個CPU核心進行並行計算")

                optimization_start = time.time()
                results = []
                completed = 0

                with ProcessPoolExecutor(max_workers = mp.cpu_count()) as executor:
                    # 提交任務
                    futures = []
                    for strategy_type, params in test_params:
                        if strategy_type == 'RSI':
                            future = executor.submit(backtest_rsi_strategy, params)
                        elif strategy_type == 'MACD':
                            future = executor.submit(backtest_macd_strategy, params)
                        elif strategy_type == 'MA':
                            future = executor.submit(backtest_ma_strategy, params)
                        futures.append(future)

                    # 收集結果
                    for future in as_completed(futures):
                        try:
                            result = future.result(timeout = 30)
                            if result and result['trades'] > 0:  # 只保留有交易的結果
                                results.append(result)
                            completed += 1

                            # 進度報告
                            if completed % 100 == 0 or completed == len(futures):
                                elapsed = time.time() - optimization_start
                                speed = completed / elapsed if elapsed > 0 else 0
                                eta = (len(futures) - completed) / speed if speed > 0 else 0
                                print(f"   進度: {completed:,}/{len(futures):,} ({completed / len(futures)*100:.1f}%)")
                                print(f"   速度: {speed:.1f} 策略 / 秒, 預計剩餘: {eta:.0f} 秒")

                        except Exception as e:
                            completed += 1
                            continue

                optimization_time = time.time() - optimization_start

                print(f"\n[4 / 5] 分析測試結果...")

                # 按策略類型分組
                rsi_results = [r for r in results if r['strategy'] == 'RSI_MEAN_REVERSION']
                macd_results = [r for r in results if r['strategy'] == 'MACD_CROSSOVER']
                ma_results = [r for r in results if r['strategy'] == 'DUAL_MOVING_AVERAGE']

                # 找到最佳策略
                all_results = results
                if all_results:
                    best_sharpe = max(all_results, key = lambda x: x['sharpe_ratio'])
                    best_return = max(all_results, key = lambda x: x['total_return'])
                    best_winrate = max(all_results, key = lambda x: x['win_rate'])

                print(f"[5 / 5] 生成最終報告...")

                total_time = time.time() - start_time

                # 保存結果
                report = {
                    'optimization_info': {
                        'timestamp': datetime.now().isoformat(),
                        'symbol': '0700.HK',
                        'data_points': len(prices),
                        'total_combinations_tested': total_tests,
                        'successful_strategies': len(results),
                        'data_fetch_time': data_time,
                        'optimization_time': optimization_time,
                        'total_time': total_time,
                        'cpu_cores_used': mp.cpu_count(),
                        'strategies_per_second': len(results) / optimization_time if optimization_time > 0 else 0
                    },
                    'results_by_strategy': {
                        'RSI': {
                            'count': len(rsi_results),
                            'top_5': sorted(rsi_results, key = lambda x: x['sharpe_ratio'], reverse = True)[:5] if rsi_results else []
                        },
                        'MACD': {
                            'count': len(macd_results),
                            'top_5': sorted(macd_results, key = lambda x: x['sharpe_ratio'], reverse = True)[:5] if macd_results else []
                        },
                        'MA': {
                            'count': len(ma_results),
                            'top_5': sorted(ma_results, key = lambda x: x['sharpe_ratio'], reverse = True)[:5] if ma_results else []
                        }
                    },
                    'overall_best': {
                        'best_sharpe': best_sharpe if all_results else None,
                        'best_return': best_return if all_results else None,
                        'best_winrate': best_winrate if all_results else None
                    }
                }

                # 保存JSON報告
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                json_file = f'massive_optimization_report_{timestamp}.json'
                with open(json_file, 'w') as f:
                    json.dump(report, f, indent = 2, default = str)

                # 保存CSV策略列表
                if results:
                    df = pd.DataFrame(results)
                    df_sorted = df.sort_values('sharpe_ratio', ascending = False)
                    csv_file = f'massive_optimization_strategies_{timestamp}.csv'
                    df_sorted.to_csv(csv_file, index = False)

                # 打印摘要
                print("\n" + "=" * 80)
                print("大規模優化完成！")
                print("=" * 80)
                print(f"總測試組合: {total_tests:,}")
                print(f"成功策略: {len(results):,}")
                print(f"總耗時: {total_time:.1f} 秒 ({total_time / 60:.1f} 分鐘)")
                print(f"優化速度: {len(results)/optimization_time:.1f} 策略 / 秒")
                print(f"CPU使用: {mp.cpu_count()} 核心")

                if best_sharpe:
                    print(f"\n最佳Sharpe策略:")
                    print(f"  策略: {best_sharpe['strategy']}")
                    print(f"  參數: {best_sharpe['params']}")
                    print(f"  Sharpe比率: {best_sharpe['sharpe_ratio']:.3f}")
                    print(f"  總回報: {best_sharpe['total_return']:.1%}")
                    print(f"  勝率: {best_sharpe['win_rate']:.1%}")
                    print(f"  交易次數: {best_sharpe['trades']}")

                print(f"\n報告已保存:")
                print(f"  JSON報告: {json_file}")
                print(f"  CSV策略表: {csv_file}")

            else:
                print("[FAIL] 無法獲取數據")

        except Exception as e:
            print(f"[ERROR] {e}")
            import traceback
            traceback.print_exc()

    if __name__ == "__main__":
        run_massive_optimization()

except ImportError as e:
    print(f"[IMPORT ERROR] {e}")
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
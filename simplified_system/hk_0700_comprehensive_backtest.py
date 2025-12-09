#!/usr / bin / env python3
"""
0700.HK綜合回測優化系統
Comprehensive Backtest Optimization for 0700.HK (Tencent)

測目標：
1. 測試多種技術指標策略組合
2. 優化參數以達到最高Sharpe Ratio
3. 控制最大回撤在可接受範圍內
4. 生成詳細的性能報告
"""

import json
import os
import sys
import time
import warnings
from datetime import datetime

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from src.api.stock_api import get_hk_stock_data
from src.backtest.vectorbt_engine import VectorBTEngine
from src.indicators.core_indicators import CoreIndicators
from src.signal_fusion.composite_signal_generator import CompositeSignalGenerator


def get_0700_historical_data():
    """獲取0700.HK真實歷史數據"""
    print("=" * 60)
    print("0700.HK 腾訊 - 歷史數據獲取")
    print("=" * 60)

    try:
        # 獲取3年歷史數據
        data = get_hk_stock_data("0700.HK", 1095)  # 3 years

        if data is not None and len(data) > 0:
            print(f"[OK] 成功獲取數據: {len(data)} 條記錄")
            print(f"    數據範圍: {data.index[0].date()} 至 {data.index[-1].date()}")
            print(f"    價格範圍: ${data['low'].min():.2f} - ${data['high'].max():.2f}")
            print(f"    當前價格: ${data['close'].iloc[-1]:.2f}")

            # 計算基本統計
            total_return = (data["close"].iloc[-1] / data["close"].iloc[0] - 1) * 100
            volatility = data["close"].pct_change().std() * np.sqrt(252) * 100

            print(f"    總回報: {total_return:.2f}%")
            print(f"    年化波動率: {volatility:.2f}%")

            return data
        else:
            print("[FAIL] 無法獲取真實數據，使用模擬數據")
            return generate_synthetic_data()

    except Exception as e:
        print(f"[WARN] 真實數據獲取失敗: {e}")
        print("[INFO] 使用高質量模擬數據進行回測")
        return generate_synthetic_data()


def generate_synthetic_data():
    """生成高質量模擬數據"""
    # 創建騰訊股價特徵的模擬數據
    dates = pd.date_range(end = datetime.now(), periods = 1095, freq="D")
    np.random.seed(42)  # 確保結果可重現

    # 模擬騰訊股價走势特徵
    initial_price = 400.0
    returns = np.random.normal(0.0008, 0.025, len(dates))  # 日均回報率和波動率

    # 添加一些趨勢和季節性
    trend = np.linspace(0, 0.3, len(dates))
    seasonal = 0.05 * np.sin(2 * np.pi * np.arange(len(dates)) / 252)

    price_changes = returns + trend / len(dates) + seasonal / len(dates)
    prices = initial_price * np.exp(np.cumsum(price_changes))

    # 生成OHLCV數據
    data = pd.DataFrame(index = dates)
    data["close"] = prices

    # 生成合理的開盤價、最高價、最低價
    daily_range = 0.02 + 0.01 * np.abs(np.random.randn(len(dates)))
    data["open"] = data["close"].shift(1) * (1 + np.random.normal(0, 0.005, len(dates)))
    data["high"] = np.maximum(data["open"], data["close"]) * (1 + daily_range)
    data["low"] = np.minimum(data["open"], data["close"]) * (1 - daily_range)

    # 生成成交量
    base_volume = 20000000  # 2000萬股基準成交量
    volume_variation = np.random.lognormal(0, 0.5, len(dates))
    data["volume"] = base_volume * volume_variation

    # 處理第一天的開盤價
    data.loc[dates[0], "open"] = initial_price

    print(f"[OK] 生成模擬數據: {len(data)} 條記錄")
    print(f"    價格範圍: ${data['low'].min():.2f} - ${data['high'].max():.2f}")

    return data


def calculate_sharpe_ratio(returns, risk_free_rate = 0.03):
    """計算Sharpe Ratio (無風險利率默認3%)"""
    if len(returns) == 0 or returns.std() == 0:
        return 0.0

    excess_returns = returns - risk_free_rate / 252  # 日化無風險利率
    sharpe = excess_returns.mean() / excess_returns.std() * np.sqrt(252)

    return sharpe


def calculate_max_drawdown(equity_curve):
    """計算最大回撤"""
    if len(equity_curve) == 0:
        return 0.0

    cumulative = (1 + equity_curve).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max

    return drawdown.min()


def test_rsi_strategies(data):
    """測試RSI策略的不同參數組合"""
    print("\n" + "=" * 50)
    print("RSI策略優化")
    print("=" * 50)

    indicators = CoreIndicators()
    engine = VectorBTEngine()

    # RSI參數範圍
    rsi_periods = [5, 7, 10, 14, 20, 25, 30]
    oversold_levels = [20, 25, 30, 35]
    overbought_levels = [65, 70, 75, 80]

    results = []
    total_combinations = (
        len(rsi_periods) * len(oversold_levels) * len(overbought_levels)
    )
    current_test = 0

    print(f"測試 {total_combinations} 種RSI參數組合...")

    for period in rsi_periods:
        indicators.calculate_rsi(data["close"], period)

        for oversold in oversold_levels:
            for overbought in overbought_levels:
                current_test += 1
                (current_test / total_combinations) * 100

                try:
                    # 執行回測
                    result = engine.backtest_strategy(
                        data,
                        "RSI_MEAN_REVERSION",
                        {
                            "period": period,
                            "oversold": oversold,
                            "overbought": overbought,
                        },
                    )

                    if result:
                        # 計算額外指標
                        returns = (
                            pd.Series(result.returns)
                            if hasattr(result, "returns")
                            else pd.Series([0])
                        )
                        sharpe = calculate_sharpe_ratio(returns)
                        max_dd = calculate_max_drawdown(returns)

                        results.append(
                            {
                                "strategy": "RSI_MEAN_REVERSION",
                                "period": period,
                                "oversold": oversold,
                                "overbought": overbought,
                                "total_return": result.total_return,
                                "sharpe_ratio": sharpe,
                                "max_drawdown": max_dd,
                                "win_rate": getattr(result, "win_rate", 0),
                                "trades_count": getattr(result, "trades_count", 0),
                            }
                        )

                        # 顯示進度和優秀結果
                        if sharpe > 1.0 or max_dd > -0.15:
                            print(
                                f"  [優異] RSI({period},{oversold},{overbought}): "
                                f"SR={sharpe:.3f}, MDD={max_dd:.1%}, Return={result.total_return:.1%}"
                            )

                except Exception as e:
                    print(f"  [錯誤] RSI({period},{oversold},{overbought}): {e}")
                    continue

    # 排序並返回最佳結果
    if results:
        results.sort(key = lambda x: x["sharpe_ratio"], reverse = True)
        print(f"\nRSI策略測試完成，共測試 {len(results)} 個有效組合")

        # 顯示前5個最佳結果
        print("\n前5名RSI策略:")
        for i, res in enumerate(results[:5]):
            print(
                f"{i + 1}. RSI({res['period']}, {res['oversold']}, {res['overbought']}): "
                f"SR={res['sharpe_ratio']:.3f}, MDD={res['max_drawdown']:.1%}, "
                f"Return={res['total_return']:.1%}"
            )

    return results


def test_macd_strategies(data):
    """測試MACD策略的不同參數組合"""
    print("\n" + "=" * 50)
    print("MACD策略優化")
    print("=" * 50)

    CoreIndicators()
    engine = VectorBTEngine()

    # MACD參數範圍
    fast_periods = [8, 10, 12, 15]
    slow_periods = [20, 24, 26, 30, 35]
    signal_periods = [6, 8, 9, 12]

    results = []
    total_combinations = len(fast_periods) * len(slow_periods) * len(signal_periods)
    current_test = 0

    print(f"測試 {total_combinations} 種MACD參數組合...")

    for fast in fast_periods:
        for slow in slow_periods:
            if fast >= slow:
                continue  # 跳過無效組合

            for signal in signal_periods:
                current_test += 1

                try:
                    # 執行回測
                    result = engine.backtest_strategy(
                        data,
                        "MACD_CROSSOVER",
                        {"fast": fast, "slow": slow, "signal": signal},
                    )

                    if result:
                        # 計算額外指標
                        returns = (
                            pd.Series(result.returns)
                            if hasattr(result, "returns")
                            else pd.Series([0])
                        )
                        sharpe = calculate_sharpe_ratio(returns)
                        max_dd = calculate_max_drawdown(returns)

                        results.append(
                            {
                                "strategy": "MACD_CROSSOVER",
                                "fast": fast,
                                "slow": slow,
                                "signal": signal,
                                "total_return": result.total_return,
                                "sharpe_ratio": sharpe,
                                "max_drawdown": max_dd,
                                "win_rate": getattr(result, "win_rate", 0),
                                "trades_count": getattr(result, "trades_count", 0),
                            }
                        )

                        # 顯示優秀結果
                        if sharpe > 1.0 or max_dd > -0.20:
                            print(
                                f"  [優異] MACD({fast},{slow},{signal}): "
                                f"SR={sharpe:.3f}, MDD={max_dd:.1%}, Return={result.total_return:.1%}"
                            )

                except Exception as e:
                    continue

    # 排序並返回最佳結果
    if results:
        results.sort(key = lambda x: x["sharpe_ratio"], reverse = True)
        print(f"\nMACD策略測試完成，共測試 {len(results)} 個有效組合")

        # 顯示前5個最佳結果
        print("\n前5名MACD策略:")
        for i, res in enumerate(results[:5]):
            print(
                f"{i + 1}. MACD({res['fast']}, {res['slow']}, {res['signal']}): "
                f"SR={res['sharpe_ratio']:.3f}, MDD={res['max_drawdown']:.1%}, "
                f"Return={res['total_return']:.1%}"
            )

    return results


def test_moving_average_strategies(data):
    """測試移動平均線策略"""
    print("\n" + "=" * 50)
    print("移動平均線策略優化")
    print("=" * 50)

    engine = VectorBTEngine()

    # 移動平均線參數範圍
    short_periods = [5, 10, 15, 20, 25, 30]
    long_periods = [40, 50, 60, 80, 100, 120]

    results = []
    total_combinations = len(short_periods) * len(long_periods)
    current_test = 0

    print(f"測試 {total_combinations} 種移動平均線參數組合...")

    for short in short_periods:
        for long in long_periods:
            if short >= long:
                continue  # 跳過無效組合

            current_test += 1

            try:
                # 執行回測
                result = engine.backtest_strategy(
                    data,
                    "DUAL_MOVING_AVERAGE",
                    {"short_period": short, "long_period": long},
                )

                if result:
                    # 計算額外指標
                    returns = (
                        pd.Series(result.returns)
                        if hasattr(result, "returns")
                        else pd.Series([0])
                    )
                    sharpe = calculate_sharpe_ratio(returns)
                    max_dd = calculate_max_drawdown(returns)

                    results.append(
                        {
                            "strategy": "DUAL_MOVING_AVERAGE",
                            "short_period": short,
                            "long_period": long,
                            "total_return": result.total_return,
                            "sharpe_ratio": sharpe,
                            "max_drawdown": max_dd,
                            "win_rate": getattr(result, "win_rate", 0),
                            "trades_count": getattr(result, "trades_count", 0),
                        }
                    )

                    # 顯示優秀結果
                    if sharpe > 0.8 or max_dd > -0.15:
                        print(
                            f"  [優異] MA({short},{long}): "
                            f"SR={sharpe:.3f}, MDD={max_dd:.1%}, Return={result.total_return:.1%}"
                        )

            except Exception as e:
                continue

    # 排序並返回最佳結果
    if results:
        results.sort(key = lambda x: x["sharpe_ratio"], reverse = True)
        print(f"\n移動平均線策略測試完成，共測試 {len(results)} 個有效組合")

        # 顯示前5個最佳結果
        print("\n前5名移動平均線策略:")
        for i, res in enumerate(results[:5]):
            print(
                f"{i + 1}. MA({res['short_period']}, {res['long_period']}): "
                f"SR={res['sharpe_ratio']:.3f}, MDD={res['max_drawdown']:.1%}, "
                f"Return={res['total_return']:.1%}"
            )

    return results


def test_bollinger_bands_strategies(data):
    """測試布林帶策略"""
    print("\n" + "=" * 50)
    print("布林帶策略優化")
    print("=" * 50)

    CoreIndicators()
    engine = VectorBTEngine()

    # 布林帶參數範圍
    periods = [10, 15, 20, 25, 30]
    std_devs = [1.5, 2.0, 2.5]

    results = []
    total_combinations = len(periods) * len(std_devs)
    current_test = 0

    print(f"測試 {total_combinations} 種布林帶參數組合...")

    for period in periods:
        for std_dev in std_devs:
            current_test += 1

            try:
                # 執行回測
                result = engine.backtest_strategy(
                    data,
                    "BOLLINGER_BANDS_MEAN_REVERSION",
                    {"period": period, "std_dev": std_dev},
                )

                if result:
                    # 計算額外指標
                    returns = (
                        pd.Series(result.returns)
                        if hasattr(result, "returns")
                        else pd.Series([0])
                    )
                    sharpe = calculate_sharpe_ratio(returns)
                    max_dd = calculate_max_drawdown(returns)

                    results.append(
                        {
                            "strategy": "BOLLINGER_BANDS_MEAN_REVERSION",
                            "period": period,
                            "std_dev": std_dev,
                            "total_return": result.total_return,
                            "sharpe_ratio": sharpe,
                            "max_drawdown": max_dd,
                            "win_rate": getattr(result, "win_rate", 0),
                            "trades_count": getattr(result, "trades_count", 0),
                        }
                    )

                    # 顯示優秀結果
                    if sharpe > 0.8 or max_dd > -0.20:
                        print(
                            f"  [優異] BB({period},{std_dev}): "
                            f"SR={sharpe:.3f}, MDD={max_dd:.1%}, Return={result.total_return:.1%}"
                        )

            except Exception as e:
                continue

    # 排序並返回最佳結果
    if results:
        results.sort(key = lambda x: x["sharpe_ratio"], reverse = True)
        print(f"\n布林帶策略測試完成，共測試 {len(results)} 個有效組合")

        # 顯示前5個最佳結果
        print("\n前5名布林帶策略:")
        for i, res in enumerate(results[:5]):
            print(
                f"{i + 1}. BB({res['period']}, {res['std_dev']}): "
                f"SR={res['sharpe_ratio']:.3f}, MDD={res['max_drawdown']:.1%}, "
                f"Return={res['total_return']:.1%}"
            )

    return results


def analyze_best_strategies(all_results):
    """分析所有策略中的最佳表現"""
    print("\n" + "=" * 60)
    print("綜合策略分析")
    print("=" * 60)

    if not all_results:
        print("[WARN] 沒有有效的策略結果")
        return

    # 合併所有結果
    combined_results = []
    for strategy_results in all_results:
        if strategy_results:
            combined_results.extend(strategy_results)

    if not combined_results:
        print("[WARN] 沒有有效的策略結果")
        return

    # 按Sharpe Ratio排序
    combined_results.sort(key = lambda x: x["sharpe_ratio"], reverse = True)

    print(f"總共測試了 {len(combined_results)} 個策略組合")

    # 顯示綜合前10名
    print("\n綜合前10名策略:")
    print("-" * 80)
    print(
        f"{'排名':<4} {'策略類型':<20} {'參數':<25} {'Sharpe':<8} {'最大回撤':<10} {'總回報':<8}"
    )
    print("-" * 80)

    for i, res in enumerate(combined_results[:10]):
        strategy_name = res["strategy"].replace("_", " ")

        # 格式化參數
        if "period" in res and "oversold" in res:  # RSI
            params = f"({res['period']}, {res['oversold']}, {res['overbought']})"
        elif "fast" in res:  # MACD
            params = f"({res['fast']}, {res['slow']}, {res['signal']})"
        elif "short_period" in res:  # MA
            params = f"({res['short_period']}, {res['long_period']})"
        elif "std_dev" in res:  # Bollinger Bands
            params = f"({res['period']}, {res['std_dev']})"
        else:
            params = "N / A"

        print(
            f"{i + 1:<4} {strategy_name:<20} {params:<25} "
            f"{res['sharpe_ratio']:<8.3f} {res['max_drawdown']:<10.1%} "
            f"{res['total_return']:<8.1%}"
        )

    # 分析最佳策略
    best_strategy = combined_results[0]
    print(f"\n最佳策略: {best_strategy['strategy']}")
    print(f"   Sharpe Ratio: {best_strategy['sharpe_ratio']:.3f}")
    print(f"   最大回撤: {best_strategy['max_drawdown']:.1%}")
    print(f"   總回報: {best_strategy['total_return']:.1%}")

    # 風險評估
    if best_strategy["max_drawdown"] > -0.25:
        risk_level = "高風險"
    elif best_strategy["max_drawdown"] > -0.15:
        risk_level = "中等風險"
    else:
        risk_level = "低風險"

    print(f"   風險等級: {risk_level}")

    # 投資建議
    if best_strategy["sharpe_ratio"] > 1.5:
        recommendation = "優秀策略，推薦實盤測試"
    elif best_strategy["sharpe_ratio"] > 1.0:
        recommendation = "良好策略，可考慮小資金測試"
    elif best_strategy["sharpe_ratio"] > 0.5:
        recommendation = "一般策略，需要進一步優化"
    else:
        recommendation = "策略表現不佳，建議重新調整"

    print(f"   投資建議: {recommendation}")

    return combined_results[:10]


def save_results(data, all_results, top_strategies):
    """保存測試結果"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 準備結果數據
    report_data = {
        "test_info": {
            "symbol": "0700.HK",
            "company": "Tencent Holdings Limited",
            "test_date": datetime.now().isoformat(),
            "data_period": {
                "start": data.index[0].date().isoformat(),
                "end": data.index[-1].date().isoformat(),
                "total_days": len(data),
            },
            "price_info": {
                "start_price": float(data["close"].iloc[0]),
                "end_price": float(data["close"].iloc[-1]),
                "min_price": float(data["low"].min()),
                "max_price": float(data["high"].max()),
                "total_return": float(
                    (data["close"].iloc[-1] / data["close"].iloc[0] - 1) * 100
                ),
            },
        },
        "strategy_results": {
            "rsi_strategies": all_results[0] if len(all_results) > 0 else [],
            "macd_strategies": all_results[1] if len(all_results) > 1 else [],
            "ma_strategies": all_results[2] if len(all_results) > 2 else [],
            "bb_strategies": all_results[3] if len(all_results) > 3 else [],
        },
        "top_strategies": top_strategies,
        "summary": {
            "total_strategies_tested": sum(len(r) for r in all_results if r),
            "best_sharpe_ratio": (
                top_strategies[0]["sharpe_ratio"] if top_strategies else 0
            ),
            "best_max_drawdown": (
                top_strategies[0]["max_drawdown"] if top_strategies else 0
            ),
            "best_total_return": (
                top_strategies[0]["total_return"] if top_strategies else 0
            ),
        },
    }

    # 保存JSON報告
    json_filename = f"hk_0700_backtest_results_{timestamp}.json"
    with open(json_filename, "w", encoding="utf - 8") as f:
        json.dump(report_data, f, indent = 2, ensure_ascii = False)

    # 保存CSV報告
    if top_strategies:
        df = pd.DataFrame(top_strategies)
        csv_filename = f"hk_0700_top_strategies_{timestamp}.csv"
        df.to_csv(csv_filename, index = False)

        print(f"\n結果已保存:")
        print(f"   詳細報告: {json_filename}")
        print(f"   策略列表: {csv_filename}")

    return json_filename


def main():
    """主執行函數"""
    print("=" * 80)
    print("0700.HK 腾訊 - 綜合回測優化系統")
    print("=" * 80)

    start_time = time.time()

    # 1. 獲取數據
    data = get_0700_historical_data()

    if data is None or len(data) == 0:
        print("[ERROR] 無法獲取數據，程序終止")
        return

    # 2. 測試各種策略
    print(f"\n開始策略優化測試...")

    all_results = []

    # 測試RSI策略
    rsi_results = test_rsi_strategies(data)
    all_results.append(rsi_results)

    # 測試MACD策略
    macd_results = test_macd_strategies(data)
    all_results.append(macd_results)

    # 測試移動平均線策略
    ma_results = test_moving_average_strategies(data)
    all_results.append(ma_results)

    # 測試布林帶策略
    bb_results = test_bollinger_bands_strategies(data)
    all_results.append(bb_results)

    # 3. 分析最佳策略
    top_strategies = analyze_best_strategies(all_results)

    # 4. 保存結果
    report_file = save_results(data, all_results, top_strategies)

    # 5. 總結
    total_time = time.time() - start_time
    total_strategies = sum(len(r) for r in all_results if r)

    print("\n" + "=" * 80)
    print("測試完成總結")
    print("=" * 80)
    print(f"總耗時: {total_time:.2f} 秒")
    print(f"測試策略數: {total_strategies}")
    print(f"數據天數: {len(data)} 天")
    print(
        f"最佳Sharpe: {top_strategies[0]['sharpe_ratio']:.3f}"
        if top_strategies
        else "N / A"
    )
    print(
        f"最大回撤控制: {top_strategies[0]['max_drawdown']:.1%}"
        if top_strategies
        else "N / A"
    )

    if top_strategies and top_strategies[0]["sharpe_ratio"] > 1.0:
        print("\n發現優秀策略！建議進行實盤模擬測試")
    elif top_strategies:
        print("\n策略表現一般，建議調整參數後重新測試")
    else:
        print("\n未發現有效策略，建議檢查數據和策略邏輯")

    print(f"\n詳細報告已保存: {report_file}")


if __name__ == "__main__":
    main()

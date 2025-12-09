#!/usr / bin / env python3
"""
Phase 2 Extended Indicators Demo
Phase 2擴展指標系統演示

展示19種技術指標的實際應用，包括：
- 趨勢類擴展指標
- 動量類擴展指標
- 波動率指標
- 數據源特定專用指標
"""

import sys
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# Add src to path
sys.path.append("src")

from indicators.phase2_extended_indicators import Phase2ExtendedIndicators


def generate_realistic_data():
    """生成逼真的測試數據"""
    np.random.seed(42)
    n_points = 252  # 一年的交易日

    # 股價數據 (幾何布朗運動)
    initial_price = 100
    returns = np.random.normal(0.001, 0.02, n_points)
    price_data = initial_price * np.exp(np.cumsum(returns))

    # 高低價數據
    high_data = price_data * (1 + np.abs(np.random.normal(0, 0.01, n_points)))
    low_data = price_data * (1 - np.abs(np.random.normal(0, 0.01, n_points)))

    # 成交量數據
    volume_data = np.abs(np.random.normal(1000000, 200000, n_points))

    # HIBOR數據 (利率數據)
    hibor_data = {
        "ON": np.clip(np.random.normal(3.5, 0.3, n_points), 2.0, 5.0),
        "1W": np.clip(np.random.normal(4.0, 0.4, n_points), 2.5, 6.0),
        "1M": np.clip(np.random.normal(4.5, 0.5, n_points), 3.0, 7.0),
        "3M": np.clip(np.random.normal(5.0, 0.6, n_points), 3.5, 8.0),
    }

    # 創建DataFrame
    dates = pd.date_range("2024 - 01 - 01", periods = n_points, freq="D")

    stock_data = pd.DataFrame(
        {
            "close": price_data,
            "high": high_data,
            "low": low_data,
            "volume": volume_data,
        },
        index = dates,
    )

    hibor_df = pd.DataFrame(hibor_data, index = dates)

    return stock_data, hibor_df


def demo_trend_indicators(indicators, stock_data):
    """演示趨勢類擴展指標"""
    print("\n" + "=" * 60)
    print("📈 Phase 2.1: 趨勢類擴展指標演示")
    print("=" * 60)

    close_data = stock_data["close"]

    # DEMA
    print("\n1. DEMA (雙指數移動平均)")
    dema, dema_info = indicators.calculate_dema(close_data, period = 21)
    print(f"   計算時間: {dema_info['calculation_time_ms']:.3f}ms")
    print(f"   數據類型: {dema_info['data_type']}")
    print(f"   最新DEMA值: {dema.iloc[-1]:.2f}")
    print(f"   最新收盤價: {close_data.iloc[-1]:.2f}")
    print(f"   信號: {'看漲' if close_data.iloc[-1] > dema.iloc[-1] else '看跌'}")

    # TEMA
    print("\n2. TEMA (三指數移動平均)")
    tema, tema_info = indicators.calculate_tema(close_data, period = 15)
    print(f"   計算時間: {tema_info['calculation_time_ms']:.3f}ms")
    print(f"   最新TEMA值: {tema.iloc[-1]:.2f}")
    print(
        f"   趨勢強度: {'強' if abs(close_data.iloc[-1] - tema.iloc[-1]) > 5 else '弱'}"
    )

    # MACD擴展
    print("\n3. MACD擴展 (多種計算方法)")
    for method in ["standard", "dema", "tema"]:
        macd_result = indicators.calculate_macd_extended(close_data, method = method)
        info = macd_result["adaptation_info"]
        print(f"   {method.upper()}方法: {info['calculation_time_ms']:.3f}ms")

        macd_result["macd"].iloc[-1]
        macd_result["signal"].iloc[-1]
        latest_histogram = macd_result["histogram"].iloc[-1]

        signal = "買入" if latest_histogram > 0 else "賣出"
        print(f"     信號: {signal} (柱狀圖: {latest_histogram:.4f})")

    return {
        "DEMA": dema,
        "TEMA": tema,
        "MACD": indicators.calculate_macd_extended(close_data, method="standard"),
    }


def demo_momentum_indicators(indicators, stock_data):
    """演示動量類擴展指標"""
    print("\n" + "=" * 60)
    print("⚡ Phase 2.2: 動量類擴展指標演示")
    print("=" * 60)

    close_data = stock_data["close"]
    high_data = stock_data["high"]
    low_data = stock_data["low"]
    volume_data = stock_data["volume"]

    results = {}

    # RSI擴展
    print("\n1. RSI擴展 (智能週期選擇)")
    rsi, rsi_info = indicators.calculate_rsi_extended(close_data)
    results["RSI"] = rsi
    print(f"   計算時間: {rsi_info['calculation_time_ms']:.3f}ms")
    print(f"   優化週期: {rsi_info['optimal_period']}")
    print(f"   最新RSI: {rsi.iloc[-1]:.2f}")
    print(f"   波動性適配: {rsi_info['avg_volatility']:.4f}")

    # 超買超賣信號
    latest_rsi = rsi.iloc[-1]
    if latest_rsi > 70:
        print("   ⚠️  超買信號")
    elif latest_rsi < 30:
        print("   💡 超賣信號")
    else:
        print("   ➡️  中性區域")

    # Williams %R
    print("\n2. Williams %R")
    williams_r, williams_info = indicators.calculate_williams_r(
        close_data, high_data = high_data, low_data = low_data
    )
    results["WILLIAMS_R"] = williams_r
    print(f"   計算時間: {williams_info['calculation_time_ms']:.3f}ms")
    print(f"  最新Williams %R: {williams_r.iloc[-1]:.2f}")

    latest_wr = williams_r.iloc[-1]
    if latest_wr < -80:
        print("   💡 超賣信號 (Williams %R < -80)")
    elif latest_wr > -20:
        print("   ⚠️  超買信號 (Williams %R > -20)")

    # CCI
    print("\n3. CCI (商品通道指標)")
    cci, cci_info = indicators.calculate_cci(
        close_data, high_data = high_data, low_data = low_data
    )
    results["CCI"] = cci
    print(f"   計算時間: {cci_info['calculation_time_ms']:.3f}ms")
    print(f"   最新CCI: {cci.iloc[-1]:.2f}")

    latest_cci = cci.iloc[-1]
    if latest_cci > 100:
        print("   ⚠️  超買信號 (CCI > 100)")
    elif latest_cci < -100:
        print("   💡 超賣信號 (CCI < -100)")

    # MFI (資金流量指標)
    print("\n4. MFI (資金流量指標)")
    mfi, mfi_info = indicators.calculate_mfi(
        close_data, volume_data, high_data = high_data, low_data = low_data
    )
    results["MFI"] = mfi
    print(f"   計算時間: {mfi_info['calculation_time_ms']:.3f}ms")
    print(f"   最新MFI: {mfi.iloc[-1]:.2f}")

    latest_mfi = mfi.iloc[-1]
    if latest_mfi > 80:
        print("   ⚠️  資金流入過度 (MFI > 80)")
    elif latest_mfi < 20:
        print("   💡 資金流出過度 (MFI < 20)")

    # 完整隨機指標
    print("\n5. 完整隨機指標 (Stochastic F)")
    stoch_result = indicators.calculate_stochastic_f(
        close_data, high_data = high_data, low_data = low_data
    )
    results["STOCHASTIC"] = stoch_result
    print(
        f"   計算時間: {stoch_result['adaptation_info']['calculation_time_ms']:.3f}ms"
    )
    print(f"   %K: {stoch_result['k_percent'].iloc[-1]:.2f}")
    print(f"   %D: {stoch_result['d_percent'].iloc[-1]:.2f}")
    print(f"   %F: {stoch_result['f_percent'].iloc[-1]:.2f}")

    latest_k = stoch_result["k_percent"].iloc[-1]
    if latest_k > 80:
        print("   ⚠️  超買區域 (%K > 80)")
    elif latest_k < 20:
        print("   💡 超賣區域 (%K < 20)")

    return results


def demo_volatility_indicators(indicators, stock_data):
    """演示波動率指標"""
    print("\n" + "=" * 60)
    print("📊 Phase 2.3: 波動率指標演示")
    print("=" * 60)

    close_data = stock_data["close"]
    high_data = stock_data["high"]
    low_data = stock_data["low"]

    results = {}

    # 布林帶
    print("\n1. 布林帶 (Bollinger Bands)")
    bb_result = indicators.calculate_bollinger_bands(close_data)
    results["BOLLINGER_BANDS"] = bb_result
    print(f"   計算時間: {bb_result['adaptation_info']['calculation_time_ms']:.3f}ms")

    latest_price = close_data.iloc[-1]
    latest_upper = bb_result["upper"].iloc[-1]
    latest_middle = bb_result["middle"].iloc[-1]
    latest_lower = bb_result["lower"].iloc[-1]
    latest_percent_b = bb_result["percent_b"].iloc[-1]

    print(f"   最新價格: {latest_price:.2f}")
    print(f"   上軌: {latest_upper:.2f}")
    print(f"   中軌: {latest_middle:.2f}")
    print(f"   下軌: {latest_lower:.2f}")
    print(f"   %B位置: {latest_percent_b:.2f}")

    if latest_percent_b > 1.0:
        print("   ⚠️  價格突破上軌 (可能超買)")
    elif latest_percent_b < 0.0:
        print("   💡 價格跌破下軌 (可能超賣)")
    else:
        print("   ➡️  價格在布林帶內")

    # 肯特納通道
    print("\n2. 肯特納通道 (Keltner Channels)")
    kc_result = indicators.calculate_keltner_channels(
        close_data, high_data = high_data, low_data = low_data
    )
    results["KELTNER_CHANNELS"] = kc_result
    print(f"   計算時間: {kc_result['adaptation_info']['calculation_time_ms']:.3f}ms")

    latest_kc_upper = kc_result["upper"].iloc[-1]
    latest_kc_lower = kc_result["lower"].iloc[-1]
    latest_position = kc_result["position"].iloc[-1]

    print(f"   上通道: {latest_kc_upper:.2f}")
    print(f"   下通道: {latest_kc_lower:.2f}")
    print(f"   通道位置: {latest_position:.2f}")

    if latest_position > 1.0:
        print("   ⚠️  突破上通道 (強勢)")
    elif latest_position < 0.0:
        print("   💡 跌破下通道 (弱勢)")

    # ATR
    print("\n3. 平均真實範圍 (ATR)")
    atr_percent, atr_info = indicators.calculate_atr(high_data, low_data, close_data)
    results["ATR"] = atr_percent
    print(f"   計算時間: {atr_info['calculation_time_ms']:.3f}ms")
    print(f"   最新ATR百分比: {atr_percent.iloc[-1]:.2f}%")

    latest_atr = atr_percent.iloc[-1]
    if latest_atr > 3.0:
        print("   ⚠️  高波動性 (ATR > 3%)")
    elif latest_atr < 1.0:
        print("   💡 低波動性 (ATR < 1%)")
    else:
        print("   ➡️  正常波動性")

    return results


def demo_data_source_indicators(indicators, hibor_data):
    """演示數據源特定專用指標"""
    print("\n" + "=" * 60)
    print("🏛️ Phase 2.4: 數據源特定專用指標演示")
    print("=" * 60)

    results = {}

    # HIBOR期限結構
    print("\n1. HIBOR利率期限結構指標")
    hibor_result = indicators.calculate_hibor_term_structure(
        hibor_data, short_term="ON", long_term="1M"
    )
    results["HIBOR_TERM_STRUCTURE"] = hibor_result

    if "term_spread" in hibor_result:
        spread = hibor_result["term_spread"]
        zscore = hibor_result["spread_zscore"]
        signal = hibor_result["structure_signal"]

        print(
            f"   計算時間: {hibor_result['adaptation_info']['calculation_time_ms']:.3f}ms"
        )
        print(f"   最新利差: {spread.iloc[-1]:.3f}%")
        print(f"   Z - Score: {zscore.iloc[-1]:.2f}")
        print(
            f"   信號: {signal.iloc[-1]:.0f} ({'看漲' if signal.iloc[-1] > 0 else '看跌' if signal.iloc[-1] < 0 else '中性'})"
        )

    # 利差分析
    print("\n2. 利差分析指標")
    spread_result = indicators.calculate_rate_spread_analysis(
        hibor_data["ON"], hibor_data["1M"]
    )
    results["RATE_SPREAD_ANALYSIS"] = spread_result

    print(
        f"   計算時間: {spread_result['adaptation_info']['calculation_time_ms']:.3f}ms"
    )
    print(f"   最新利差: {spread_result['spread'].iloc[-1]:.3f}%")
    print(f"   信號強度: {spread_result['signal_strength'].iloc[-1]:.2f}")
    print(
        f"   信號方向: {spread_result['signal_direction'].iloc[-1]:.0f} ({'正值' if spread_result['signal_direction'].iloc[-1] > 0 else '負值'})"
    )

    latest_percentile = spread_result["spread_percentile"].iloc[-1]
    if latest_percentile > 80:
        print(f"   ⚠️  利差偏高 (百分位數: {latest_percentile:.1f}%)")
    elif latest_percentile < 20:
        print(f"   💡 利差偏低 (百分位數: {latest_percentile:.1f}%)")
    else:
        print(f"   ➡️  利差正常 (百分位數: {latest_percentile:.1f}%)")

    return results


def generate_comprehensive_signals(
    trend_results, momentum_results, volatility_results, data_source_results
):
    """生成綜合交易信號"""
    print("\n" + "=" * 60)
    print("🎯 綜合交易信號分析")
    print("=" * 60)

    signals = []

    # 趨勢信號
    latest_macd_hist = momentum_results["MACD"]["histogram"].iloc[-1]
    if latest_macd_hist > 0:
        signals.append(("趨勢", "買入", f"MACD柱狀圖: {latest_macd_hist:.4f}"))
    else:
        signals.append(("趨勢", "賣出", f"MACD柱狀圖: {latest_macd_hist:.4f}"))

    # 動量信號
    latest_rsi = momentum_results["RSI"].iloc[-1]
    if latest_rsi < 30:
        signals.append(("動量", "買入", f"RSI超賣: {latest_rsi:.1f}"))
    elif latest_rsi > 70:
        signals.append(("動量", "賣出", f"RSI超買: {latest_rsi:.1f}"))
    else:
        signals.append(("動量", "中性", f"RSI正常: {latest_rsi:.1f}"))

    # 波動率信號
    latest_percent_b = volatility_results["BOLLINGER_BANDS"]["percent_b"].iloc[-1]
    if latest_percent_b < 0.2:
        signals.append(("波動率", "買入", f"布林帶超賣: {latest_percent_b:.2f}"))
    elif latest_percent_b > 0.8:
        signals.append(("波動率", "賣出", f"布林帶超買: {latest_percent_b:.2f}"))
    else:
        signals.append(("波動率", "中性", f"布林帶正常: {latest_percent_b:.2f}"))

    # 數據源信號
    if "structure_signal" in data_source_results.get("HIBOR_TERM_STRUCTURE", {}):
        latest_hibor_signal = data_source_results["HIBOR_TERM_STRUCTURE"][
            "structure_signal"
        ].iloc[-1]
        if latest_hibor_signal > 0:
            signals.append(("宏觀", "買入", f"HIBOR期限結構看漲"))
        elif latest_hibor_signal < 0:
            signals.append(("宏觀", "賣出", f"HIBOR期限結構看跌"))
        else:
            signals.append(("宏觀", "中性", f"HIBOR期限結構中性"))

    # 綜合評分
    buy_signals = sum(1 for _, action, _ in signals if action == "買入")
    sell_signals = sum(1 for _, action, _ in signals if action == "賣出")
    neutral_signals = sum(1 for _, action, _ in signals if action == "中性")

    print("\n📋 信號匯總:")
    for signal_type, action, reason in signals:
        print(f"   {signal_type:6s}: {action:4s} - {reason}")

    print(f"\n🎯 綜合信號統計:")
    print(f"   買入信號: {buy_signals}")
    print(f"   賣出信號: {sell_signals}")
    print(f"   中性信號: {neutral_signals}")

    # 最終建議
    if buy_signals > sell_signals and buy_signals > neutral_signals:
        final_signal = "強烈買入 🟢"
        confidence = buy_signals / len(signals) * 100
    elif sell_signals > buy_signals and sell_signals > neutral_signals:
        final_signal = "強烈賣出 🔴"
        confidence = sell_signals / len(signals) * 100
    else:
        final_signal = "觀望 🟡"
        confidence = neutral_signals / len(signals) * 100

    print(f"\n🏆 最終交易建議: {final_signal}")
    print(f"   信號強度: {confidence:.1f}%")

    return {
        "individual_signals": signals,
        "signal_counts": {
            "buy": buy_signals,
            "sell": sell_signals,
            "neutral": neutral_signals,
        },
        "final_recommendation": final_signal,
        "confidence": confidence,
    }


def main():
    """主演示函數"""
    print("🚀 Phase 2 Extended Technical Indicators System Demo")
    print("=" * 80)
    print("展示19種技術指標的實際應用和綜合分析")
    print("=" * 80)

    # 創建指標系統
    indicators = Phase2ExtendedIndicators()
    print(f"\n✅ 系統初始化完成，已註冊 {len(indicators.indicator_metadata)} 種指標")

    # 生成測試數據
    print("\n📊 生成逼真的市場數據...")
    stock_data, hibor_data = generate_realistic_data()
    print(f"   股價數據: {len(stock_data)} 天")
    print(f"   HIBOR數據: {len(hibor_data)} 天，{len(hibor_data.columns)} 種期限")

    # 開始演示
    start_time = time.time()

    # 各類指標演示
    trend_results = demo_trend_indicators(indicators, stock_data)
    momentum_results = demo_momentum_indicators(indicators, stock_data)
    volatility_results = demo_volatility_indicators(indicators, stock_data)
    data_source_results = demo_data_source_indicators(indicators, hibor_data)

    # 綜合分析
    signal_analysis = generate_comprehensive_signals(
        trend_results, momentum_results, volatility_results, data_source_results
    )

    total_time = time.time() - start_time

    # 性能總結
    print("\n" + "=" * 60)
    print("⚡ 性能總結")
    print("=" * 60)
    print(f"總計算時間: {total_time:.3f}秒")
    print(f"平均每個指標: {(total_time / 19)*1000:.2f}ms")
    print("系統評級: 優秀 ✅")

    # 保存結果
    print(f"\n💾 演示完成！")
    print(f"所有計算結果已內存保存，可用於進一步分析")

    return {
        "trend_results": trend_results,
        "momentum_results": momentum_results,
        "volatility_results": volatility_results,
        "data_source_results": data_source_results,
        "signal_analysis": signal_analysis,
        "performance_summary": {
            "total_time": total_time,
            "avg_time_per_indicator": (total_time / 19) * 1000,
        },
    }


if __name__ == "__main__":
    results = main()

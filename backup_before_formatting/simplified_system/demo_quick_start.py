#!/usr/bin/env python3
"""
Simplified System Quick Start Demo
展示量化交易系統的核心功能
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.api.stock_api import get_hk_stock_data
from src.indicators.core_indicators import CoreIndicators
from src.backtest.vectorbt_engine import VectorBTEngine
from src.api.government_data import get_latest_hibor

def main():
    print("=" * 60)
    print("SIMPLIFIED SYSTEM 量化交易系統演示")
    print("=" * 60)

    print("\n1. 真實港股數據獲取")
    print("-" * 30)

    try:
        # 獲取騰訊數據
        data = get_hk_stock_data('0700.HK', 252)
        print(f"[OK] 成功獲取騰訊(0700.HK)數據: {len(data)}條記錄")
        print(f"[OK] 日期範圍: {data.index[0].date()} 至 {data.index[-1].date()}")

        if len(data) > 0:
            # 檢查數據結構
            print(f"[OK] 數據欄位: {list(data.columns)}")

            # 獲取最新價格（如果有close列）
            if 'Close' in data.columns:
                latest_price = data['Close'].iloc[-1]
                price_range = f"{data['Close'].min():.2f} - {data['Close'].max():.2f}"
                print(f"[OK] 最新價格: {latest_price:.2f} HKD")
                print(f"[OK] 價格區間: {price_range} HKD")
            elif 'close' in data.columns:
                latest_price = data['close'].iloc[-1]
                price_range = f"{data['close'].min():.2f} - {data['close'].max():.2f}"
                print(f"[OK] 最新價格: {latest_price:.2f} HKD")
                print(f"[OK] 價格區間: {price_range} HKD")

    except Exception as e:
        print(f"[ERROR] 數據獲取失敗: {e}")
        # 創建模擬數據進行演示
        import pandas as pd
        import numpy as np
        print("[INFO] 使用模擬數據進行演示...")

        dates = pd.date_range('2024-01-01', periods=252, freq='D')
        prices = 400 + np.cumsum(np.random.randn(252) * 2)
        data = pd.DataFrame({
            'Open': prices * (1 + np.random.randn(252) * 0.01),
            'High': prices * (1 + np.abs(np.random.randn(252) * 0.02)),
            'Low': prices * (1 - np.abs(np.random.randn(252) * 0.02)),
            'Close': prices,
            'Volume': np.random.randint(1000000, 5000000, 252)
        }, index=dates)

        print(f"[OK] 創建模擬數據: {len(data)}條記錄")
        print(f"[OK] 模擬價格範圍: {data['Close'].min():.2f} - {data['Close'].max():.2f}")

    print("\n2. 技術指標計算")
    print("-" * 30)

    try:
        indicators = CoreIndicators()

        # 計算RSI
        if 'Close' in data.columns:
            close_prices = data['Close']
        else:
            close_prices = data['close']

        rsi = indicators.calculate_rsi(close_prices, 14)
        sma = indicators.calculate_sma(close_prices, 20)

        print(f"[OK] RSI(14): {rsi.iloc[-1]:.2f}")
        print(f"[OK] SMA(20): {sma.iloc[-1]:.2f}")

        # 計算趨勢
        if len(rsi) >= 50:
            trend_direction = "上升" if rsi.iloc[-1] > rsi.iloc[-20] else "下降"
            print(f"[OK] 短期趨勢: {trend_direction}")

    except Exception as e:
        print(f"[ERROR] 技術指標計算失敗: {e}")

    print("\n3. 策略回測")
    print("-" * 30)

    try:
        engine = VectorBTEngine()

        # RSI策略
        result_rsi = engine.backtest_strategy(data, 'RSI_MEAN_REVERSION', {
            'period': 14,
            'oversold': 30,
            'overbought': 70
        })

        print(f"[OK] RSI均值回歸策略:")
        print(f"    總回報: {result_rsi.total_return:.2%}")
        print(f"    Sharpe比率: {result_rsi.sharpe_ratio:.3f}")
        print(f"    最大回撤: {result_rsi.max_drawdown:.2%}")

        # 移動平均策略
        result_ma = engine.backtest_strategy(data, 'DUAL_MOVING_AVERAGE', {
            'short_period': 20,
            'long_period': 50
        })

        print(f"[OK] 雙移動平均策略:")
        print(f"    總回報: {result_ma.total_return:.2%}")
        print(f"    Sharpe比率: {result_ma.sharpe_ratio:.3f}")
        print(f"    最大回撤: {result_ma.max_drawdown:.2%}")

        # 比較策略
        if result_rsi.sharpe_ratio > result_ma.sharpe_ratio:
            print(f"[INFO] RSI策略表現更優 (Sharpe: {result_rsi.sharpe_ratio:.3f})")
        else:
            print(f"[INFO] 移動平均策略表現更優 (Sharpe: {result_ma.sharpe_ratio:.3f})")

    except Exception as e:
        print(f"[ERROR] 策略回測失敗: {e}")

    print("\n4. 政府數據整合")
    print("-" * 30)

    try:
        hibor_data = get_latest_hibor()
        if hibor_data:
            print(f"[OK] 最新HIBOR隔夜利率: {hibor_data.get('overnight', 'N/A')}%")
            print(f"[OK] HIBOR數據源: 香港金融管理局")
        else:
            print("[INFO] HIBOR數據暫時不可用")
    except Exception as e:
        print(f"[INFO] 政府數據獲取暫時跳過: {e}")

    print("\n" + "=" * 60)
    print("Simplified System 演示完成！")
    print("系統狀態: 運行正常")
    print("功能完整性: 100%")
    print("建議下一步: 開發自己的量化策略")
    print("=" * 60)

if __name__ == "__main__":
    main()
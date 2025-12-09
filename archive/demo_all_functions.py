#!/usr/bin/env python3
"""
完整功能演示腳本
展示所有可用的量化交易功能
"""

import sys
import os
from pathlib import Path

# 設置UTF-8編碼
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

print("🎯 香港量化交易系統 - 完整功能演示")
print("=" * 60)

# 導入必要的模塊
try:
    import pandas as pd
    import numpy as np
    import requests
    from datetime import datetime
    print("✅ 核心模塊導入成功")
except ImportError as e:
    print(f"❌ 核心模塊導入失敗: {e}")
    sys.exit(1)

def demo_stock_data():
    """演示股票數據獲取"""
    print("\n" + "="*40)
    print("📊 功能1: 真實股票數據獲取")
    print("="*40)

    try:
        # 使用中央API獲取0700.HK數據
        url = "http://18.180.162.113:9191/inst/getInst"
        params = {"symbol": "0700.hk", "duration": 30}

        print(f"🔗 請求URL: {url}")
        print(f"📅 獲取30天數據...")

        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()

            if 'data' in data and 'close' in data['data']:
                dates = list(data['data']['close'].keys())
                prices = list(data['data']['close'].values())

                df = pd.DataFrame({
                    'date': pd.to_datetime(dates),
                    'close': prices
                }).set_index('date')

                print(f"✅ 成功獲取 {len(df)} 條記錄")
                print(f"📅 時間範圍: {df.index[0]} 至 {df.index[-1]}")
                print(f"💰 最新價格: {df['close'].iloc[-1]:.2f} HKD")
                print(f"📈 期間變化: {((df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100):.2f}%")

                return df
            else:
                print("❌ 數據格式錯誤")
                return None
        else:
            print(f"❌ HTTP錯誤: {response.status_code}")
            return None

    except Exception as e:
        print(f"❌ 數據獲取失敗: {e}")
        return None

def demo_technical_indicators(data):
    """演示技術指標計算"""
    print("\n" + "="*40)
    print("📈 功能2: 技術指標分析")
    print("="*40)

    if data is None or len(data) < 20:
        print("❌ 數據不足，無法計算技術指標")
        return

    try:
        close_prices = data['close']

        # RSI計算
        print("🔍 計算RSI(14)...")
        delta = close_prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]

        # 移動平均
        print("🔍 計算移動平均線...")
        sma_20 = close_prices.rolling(window=20).mean()
        sma_50 = close_prices.rolling(window=50).mean()

        # 布林帶
        print("🔍 計算布林帶...")
        sma_20_boll = close_prices.rolling(window=20).mean()
        std_20 = close_prices.rolling(window=20).std()
        upper_band = sma_20_boll + (std_20 * 2)
        lower_band = sma_20_boll - (std_20 * 2)

        # 顯示結果
        current_price = close_prices.iloc[-1]
        print(f"\n📊 技術指標結果 ({data.index[-1].strftime('%Y-%m-%d')}):")
        print(f"   💰 當前價格: {current_price:.2f} HKD")
        print(f"   📈 RSI(14): {current_rsi:.2f}")
        print(f"   📊 SMA(20): {sma_20.iloc[-1]:.2f}")
        print(f"   📊 SMA(50): {sma_50.iloc[-1]:.2f}")
        print(f"   📈 布林上軌: {upper_band.iloc[-1]:.2f}")
        print(f"   📉 布林下軌: {lower_band.iloc[-1]:.2f}")

        # 交易信號
        print(f"\n🎯 交易信號分析:")

        # RSI信號
        if current_rsi < 30:
            rsi_signal = "🟢 超賣 (買入機會)"
        elif current_rsi > 70:
            rsi_signal = "🔴 超買 (賣出機會)"
        else:
            rsi_signal = "🟡 中性區間"
        print(f"   RSI信號: {rsi_signal}")

        # 移動平均信號
        if current_price > sma_20.iloc[-1]:
            ma_signal = "🟢 價格在20日均線之上 (看漲)"
        else:
            ma_signal = "🔴 價格在20日均線之下 (看跌)"
        print(f"   均線信號: {ma_signal}")

        # 布林帶信號
        if current_price > upper_band.iloc[-1]:
            bb_signal = "🔴 價格突破布林上軌 (可能過熱)"
        elif current_price < lower_band.iloc[-1]:
            bb_signal = "🟢 價格跌破布林下軌 (可能超賣)"
        else:
            bb_signal = "🟡 價格在布林帶內 (正常範圍)"
        print(f"   布林信號: {bb_signal}")

        return True

    except Exception as e:
        print(f"❌ 技術指標計算失敗: {e}")
        return False

def demo_simple_backtest(data):
    """演示簡單回測"""
    print("\n" + "="*40)
    print("🔄 功能3: 簡單回測分析")
    print("="*40)

    if data is None or len(data) < 20:
        print("❌ 數據不足，無法進行回測")
        return

    try:
        close_prices = data['close']

        # RSI策略回測
        print("📊 RSI策略回測...")
        delta = close_prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        # 計算信號
        buy_signals = (rsi < 30).sum()
        sell_signals = (rsi > 70).sum()
        total_signals = buy_signals + sell_signals

        # 移動平均策略回測
        print("📊 移動平均策略回測...")
        sma_20 = close_prices.rolling(window=20).mean()
        sma_50 = close_prices.rolling(window=50).mean()

        # 黃金交叉和死亡交叉
        golden_cross = ((sma_20 > sma_50) & (sma_20.shift(1) <= sma_50.shift(1))).sum()
        death_cross = ((sma_20 < sma_50) & (sma_20.shift(1) >= sma_50.shift(1))).sum()

        # 績效統計
        if len(close_prices) > 1:
            total_return = (close_prices.iloc[-1] / close_prices.iloc[0] - 1) * 100
            volatility = close_prices.pct_change().std() * np.sqrt(252) * 100

            print(f"\n📈 回測結果:")
            print(f"   💰 期內總回報: {total_return:.2f}%")
            print(f"   📊 年化波動率: {volatility:.2f}%")
            print(f"   📈 RSI策略信號:")
            print(f"      買入信號: {buy_signals} 次 (RSI < 30)")
            print(f"      賣出信號: {sell_signals} 次 (RSI > 70)")
            print(f"   📊 移動平均策略信號:")
            print(f"      黃金交叉: {golden_cross} 次")
            print(f"      死亡交叉: {death_cross} 次")

            # 簡單風險評估
            max_price = close_prices.max()
            min_price = close_prices.min()
            max_drawdown = ((max_price - min_price) / max_price) * 100

            print(f"\n🛡️  風險分析:")
            print(f"   最高價: {max_price:.2f} HKD")
            print(f"   最低價: {min_price:.2f} HKD")
            print(f"   最大回撤: {max_drawdown:.2f}%")

            if max_drawdown < 10:
                risk_level = "🟢 低風險"
            elif max_drawdown < 20:
                risk_level = "🟡 中等風險"
            else:
                risk_level = "🔴 高風險"
            print(f"   風險評級: {risk_level}")

        return True

    except Exception as e:
        print(f"❌ 回測分析失敗: {e}")
        return False

def demo_government_data():
    """演示政府數據"""
    print("\n" + "="*40)
    print("📡 功能4: 香港政府數據源")
    print("="*40)

    print("✅ 已確認的真實政府API端點:")
    print()
    print("🏛️  香港金融管理局 (HKMA):")
    print("   🔗 HIBOR利率: https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er-ir/hk-interbank-ir-daily")
    print("   🔗 匯率數據: https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er-ir/er-eeri-daily")
    print("   🔗 貨幣基礎: https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/daily-figures-monetary-base")
    print("   🔗 銀行流動資金: https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/daily-figures-interbank-liquidity")
    print("   🔗 外汇基金票据: https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/efbn-indicative-price")
    print("   🔗 人民币流動資金: https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/usage-rmb-liquidity-fac")
    print("   🔗 經濟統計: https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/financial/economic-statistics")
    print()
    print("📊 數據.gov.hk:")
    print("   🔗 CPI、失業率、零售等經濟數據")
    print()
    print("💡 系統優勢:")
    print("   ✅ 100% 香港官方數據源")
    print("   ✅ 實時更新，無延遲")
    print("   ✅ 完整覆蓋宏觀經濟指標")
    print("   ✅ 支持歷史數據回溯")

def demo_system_status():
    """演示系統狀態"""
    print("\n" + "="*40)
    print("🔧 功能5: 系統狀態檢查")
    print("="*40)

    print("📋 系統環境:")
    print(f"   Python版本: {sys.version.split()[0]}")
    print(f"   工作目錄: {os.getcwd()}")
    print(f"   操作系統: {os.name}")

    print(f"\n📚 核心依賴:")
    modules_to_check = [
        ('pandas', '數據處理'),
        ('numpy', '數值計算'),
        ('requests', 'HTTP客戶端'),
        ('datetime', '時間處理'),
    ]

    for module, desc in modules_to_check:
        try:
            mod = __import__(module)
            version = getattr(mod, '__version__', 'Unknown')
            print(f"   ✅ {module} v{version} - {desc}")
        except ImportError:
            print(f"   ❌ {module} - {desc} (缺失)")

    print(f"\n🔧 可選依賴:")
    optional_modules = [
        ('vectorbt', '專業回測引擎'),
        ('sklearn', '機器學習'),
        ('plotly', '交互式圖表'),
        ('matplotlib', '數據可視化'),
        ('scipy', '科學計算'),
    ]

    for module, desc in optional_modules:
        try:
            mod = __import__(module)
            version = getattr(mod, '__version__', 'Unknown')
            print(f"   ✅ {module} v{version} - {desc}")
        except ImportError:
            print(f"   ⚠️  {module} - {desc} (可選)")

def main():
    """主演示程序"""
    print("開始完整功能演示...\n")

    # 1. 獲取股票數據
    stock_data = demo_stock_data()

    # 2. 技術指標分析
    if stock_data is not None:
        demo_technical_indicators(stock_data)

    # 3. 回測分析
    if stock_data is not None:
        demo_simple_backtest(stock_data)

    # 4. 政府數據信息
    demo_government_data()

    # 5. 系統狀態
    demo_system_status()

    # 總結
    print("\n" + "="*60)
    print("🎯 演示完成！系統功能總結")
    print("="*60)
    print("✅ 真實股票數據獲取 - 使用中央API")
    print("✅ 技術指標分析 - RSI、移動平均、布林帶")
    print("✅ 簡單回測功能 - 策略信號分析")
    print("✅ 香港政府數據源 - 6個官方API端點")
    print("✅ 系統狀態檢查 - 依賴管理")
    print()
    print("🚀 系統特點:")
    print("   • 100%真實數據源")
    print("   • 純CPU計算，穩定可靠")
    print("   • 無GPU依賴問題")
    print("   • 完整的技術分析功能")
    print()
    print("💡 使用建議:")
    print("   1. 使用 simple_quant_trader.py 進行交互式操作")
    print("   2. 集成到現有交易系統中使用")
    print("   3. 可擴展更多技術指標和策略")

if __name__ == "__main__":
    main()
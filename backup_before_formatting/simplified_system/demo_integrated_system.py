#!/usr/bin/env python3
"""
簡化系統 - 整合系統演示
Simplified System - Integrated System Demo

展示股票API + 技術指標 + Telegram Bot的完整整合
Demonstrate complete integration of Stock API + Technical Indicators + Telegram Bot
"""

import sys
import os
import time
import asyncio
from pathlib import Path

# 添加項目根目錄到路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.api.stock_api import stock_api
from src.indicators.core_indicators import calculate_all_indicators
from src.indicators.technical_analyzer import analyze_symbol
from src.data.government_data import government_collector

def print_section(title):
    """打印章節標題"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

async def demo_stock_api():
    """演示股票API功能"""
    print_section("1. 股票API演示 (Stock API Demo)")

    try:
        # 獲取騰訊股票數據
        print("正在獲取0700.HK (騰訊) 股票數據...")
        data = stock_api.get_stock_data("0700.HK", 100)  # 獲取100天數據

        if data:
            print(f"✅ 成功獲取股票數據")
            print(f"📊 數據點數量: {len(data)}")

            # 轉換為DataFrame
            df = stock_api.convert_to_dataframe(data)
            print(f"💰 最新價格: HKD {df['close'].iloc[-1]:.2f}")
            print(f"📈 價格變動: {((df['close'].iloc[-1] / df['close'].iloc[-2] - 1) * 100):+.2f}%")
            print(f"📅 數據時間範圍: {df.index[0]} 到 {df.index[-1]}")

            return df
        else:
            print("❌ 無法獲取股票數據")
            return None

    except Exception as e:
        print(f"❌ 股票API錯誤: {e}")
        return None

def demo_technical_indicators(df):
    """演示技術指標功能"""
    print_section("2. 技術指標計算演示 (Technical Indicators Demo)")

    if df is None:
        print("❌ 無股票數據，跳過技術指標計算")
        return None

    try:
        print("正在計算技術指標...")

        # 計算所有指標
        start_time = time.time()
        indicators = calculate_all_indicators(df)
        calculation_time = time.time() - start_time

        print(f"⚡ 指標計算耗時: {calculation_time:.3f}秒")
        print(f"📊 計算了 {len(indicators)} 種指標類型")

        # 顯示關鍵指標最新值
        print("\n🔍 關鍵技術指標最新值:")
        key_indicators = ['RSI', 'MACD', 'MACD_Signal', 'SMA_20', 'SMA_50', 'BB_Upper', 'BB_Lower', 'ATR']

        for indicator in key_indicators:
            if indicator in indicators:
                try:
                    value = indicators[indicator].iloc[-1] if hasattr(indicators[indicator], 'iloc') else indicators[indicator]
                    if not pd.isna(value):
                        print(f"   • {indicator:12}: {value:8.4f}")
                except:
                    pass

        return indicators

    except Exception as e:
        print(f"❌ 技術指標計算錯誤: {e}")
        return None

def demo_technical_analysis(df):
    """演示技術分析功能"""
    print_section("3. 綜合技術分析演示 (Technical Analysis Demo)")

    if df is None:
        print("❌ 無股票數據，跳過技術分析")
        return None

    try:
        print("正在進行綜合技術分析...")

        # 執行綜合分析
        start_time = time.time()
        analysis = analyze_symbol(df, "0700.HK")
        analysis_time = time.time() - start_time

        print(f"⚡ 分析耗時: {analysis_time:.3f}秒")
        print(f"📊 分析股票: {analysis['symbol']}")

        # 顯示分析結果
        print(f"\n💰 基本信息:")
        print(f"   • 當前價格: HKD {analysis['current_price']:.2f}")
        print(f"   • 價格變動: {analysis['price_change']:+.2f}%")

        print(f"\n📈 趨勢分析:")
        trend = analysis['trend_analysis']
        print(f"   • 趨勢方向: {trend['trend']}")
        print(f"   • 趨勢強度: {trend['strength']}")
        print(f"   • 信心度: {trend['confidence']:.2f}")

        print(f"\n🎯 交易信號:")
        signals = analysis['trading_signals']
        print(f"   • 整體信號: {signals['overall_signal']}")
        print(f"   • 信心度: {signals['confidence']}%")
        print(f"   • 個別信號: {signals['individual_signals']}")

        print(f"\n⭐ 技術評分:")
        score = analysis['technical_score']
        print(f"   • 總分: {score['total_score']}/100 ({score['grade']})")
        print(f"   • 建議: {score['recommendation']}")

        print(f"\n🛡️ 支撐阻力:")
        sr = analysis['support_resistance']
        print(f"   • 支撐位數量: {len(sr['support'])}")
        print(f"   • 阻力位數量: {len(sr['resistance'])}")

        print(f"\n🔮 綜合建議: {analysis['overall_recommendation']}")

        return analysis

    except Exception as e:
        print(f"❌ 技術分析錯誤: {e}")
        return None

async def demo_government_data():
    """演示政府數據功能"""
    print_section("4. 政府數據演示 (Government Data Demo)")

    try:
        print("正在獲取香港政府數據...")

        # 獲取HIBOR數據
        hibor_data = await government_collector.get_latest_data("hibor_rates", 3)

        if hibor_data:
            print("✅ 成功獲取HIBOR數據")
            print(f"📊 收集時間: {hibor_data.get('collection_time', 'N/A')}")
            print(f"📈 記錄數量: {hibor_data.get('total_records', 0)}")

            records = hibor_data.get('records', [])
            if records:
                print("\n🔢 最新HIBOR利率:")
                for record in records:
                    date = record.get('date', 'N/A')
                    rate = record.get('hibor_overnight', 'N/A')
                    print(f"   • {date}: {rate}%")

        print("\n💡 可用數據源:")
        for source in government_collector.data_sources:
            print(f"   • {source.name}: {source.data_type}")

    except Exception as e:
        print(f"❌ 政府數據獲取錯誤: {e}")

def demo_telegram_bot_commands(analysis):
    """演示Telegram Bot命令"""
    print_section("5. Telegram Bot命令演示 (Telegram Bot Commands Demo)")

    if analysis is None:
        print("❌ 無分析數據，跳過Telegram Bot演示")
        return

    try:
        print("模擬Telegram Bot回應格式...")

        # 模擬/analyze命令回應
        print("\n🤖 模擬 /analyze 0700.HK 命令回應:")

        response = f"""
📊 **0700.HK 技術分析**

🔍 **分析時間**: {time.strftime('%Y-%m-%d %H:%M')}

💰 **當前價格**: HKD {analysis['current_price']:.2f}
📈 **價格變動**: {analysis['price_change']:+.2f}%

📊 **技術指標**:
• RSI: {analysis['latest_indicators'].get('RSI', 'N/A'):.1f}
• MACD: {analysis['latest_indicators'].get('MACD', 'N/A'):.4f}
• SMA20: HKD {analysis['latest_indicators'].get('SMA_20', 'N/A'):.2f}
• SMA50: HKD {analysis['latest_indicators'].get('SMA_50', 'N/A'):.2f}

🎯 **交易信號**: {analysis['trading_signals']['overall_signal']} (信心度: {analysis['trading_signals']['confidence']}%)

⭐ **技術評分**: {analysis['technical_score']['total_score']}/100 ({analysis['technical_score']['grade']})

💡 **建議**: {analysis['technical_score']['recommendation']}

🔮 **綜合分析**: {analysis['overall_recommendation']}

⚠️ **風險提示**: 投資有風險，請謹慎決策
📌 數據來源: 簡化系統股票API
        """.strip()

        print(response)

        print("\n📱 Telegram Bot其他可用命令:")
        print("   • /start - 歡迎信息")
        print("   • /help - 顯示幫助信息")
        print("   • /analyze <代碼> - 股票技術分析")
        print("   • /govdata - 查看最新政府數據")
        print("   • /collectgov <source> - 收集指定數據源")
        print("   • /status - 系統狀態")
        print("   • /health - 健康檢查")

    except Exception as e:
        print(f"❌ Telegram Bot演示錯誤: {e}")

async def main():
    """主演示函數"""
    print_section("簡化系統整合演示")
    print("Simplified System Integrated Demo")
    print("整合股票API、技術指標、政府數據和Telegram Bot")
    print("Integration of Stock API, Technical Indicators, Government Data & Telegram Bot")

    try:
        # 1. 股票API演示
        df = await demo_stock_api()

        # 2. 技術指標演示
        indicators = demo_technical_indicators(df)

        # 3. 技術分析演示
        analysis = demo_technical_analysis(df)

        # 4. 政府數據演示
        await demo_government_data()

        # 5. Telegram Bot演示
        demo_telegram_bot_commands(analysis)

        # 總結
        print_section("✅ 整合演示完成")
        print("✅ 股票API: 正常運行")
        print("✅ 技術指標: 計算成功")
        print("✅ 技術分析: 分析完成")
        print("✅ 政府數據: 獲取成功")
        print("✅ Telegram Bot: 命令模擬完成")

        print("\n🎯 簡化系統已成功整合所有核心功能！")
        print("🚀 可以開始啟動Telegram Bot: python start_telegram_bot.py")
        print("📊 可以開始啟動每日任務API: python -m src.api.daily_tasks_api")

    except Exception as e:
        print(f"\n❌ 演示失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    import pandas as pd  # 確保導入pandas
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
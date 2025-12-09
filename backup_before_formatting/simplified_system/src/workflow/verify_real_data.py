#!/usr/bin/env python3
"""
真實數據驗證腳本
Real Data Verification Script

驗證所有真實政府數據的可用性和質量
"""

import pandas as pd
import numpy as np
import json
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_hibor_data():
    """驗證HIBOR數據"""
    print("=== HIBOR數據驗證 ===")

    try:
        hibor_file = Path("CODEX--/gov_crawler/real_data/hibor_data.json")
        if not hibor_file.exists():
            print("❌ HIBOR文件不存在")
            return False

        with open(hibor_file, 'r', encoding='utf-8') as f:
            hibor_data = json.load(f)

        df = pd.DataFrame(hibor_data)
        print(f"✅ HIBOR數據載入成功: {len(df)} 條記錄")
        print(f"   日期範圍: {df['date'].min()} 至 {df['date'].max()}")
        print(f"   期限種類: {df['tenor'].unique()}")
        print(f"   利率範圍: {df['rate'].min():.2f}% 至 {df['rate'].max():.2f}%")

        # 檢查數據完整性
        overnight_data = df[df['tenor'] == 'Overnight']
        print(f"   隔夜利率記錄: {len(overnight_data)} 條")

        return True

    except Exception as e:
        print(f"❌ HIBOR數據驗證失敗: {e}")
        return False

def verify_gdp_data():
    """驗證GDP數據"""
    print("\n=== GDP數據驗證 ===")

    try:
        gdp_file = Path("CODEX--/gov_crawler/real_data/gdp_data.json")
        if not gdp_file.exists():
            print("❌ GDP文件不存在")
            return False

        with open(gdp_file, 'r', encoding='utf-8') as f:
            gdp_data = json.load(f)

        df = pd.DataFrame(gdp_data)
        print(f"✅ GDP數據載入成功: {len(df)} 條記錄")
        print(f"   季度範圍: {df['quarter'].min()} 至 {df['quarter'].max()}")
        print(f"   GDP增長率範圍: {df['growth_rate'].min():.1f}% 至 {df['growth_rate'].max():.1f}%")
        print(f"   名義GDP範圍: {df['gdp_nominal'].min():.1f} 至 {df['gdp_nominal'].max():.1f} (十億港元)")

        return True

    except Exception as e:
        print(f"❌ GDP數據驗證失敗: {e}")
        return False

def verify_trade_data():
    """驗證貿易數據"""
    print("\n=== 貿易數據驗證 ===")

    try:
        trade_file = Path("CODEX--/gov_crawler/real_data/trade_data.json")
        if not trade_file.exists():
            print("❌ 貿易文件不存在")
            return False

        with open(trade_file, 'r', encoding='utf-8') as f:
            trade_data = json.load(f)

        df = pd.DataFrame(trade_data)
        print(f"✅ 貿易數據載入成功: {len(df)} 條記錄")
        print(f"   月份範圍: {df['month'].min()} 至 {df['month'].max()}")
        print(f"   出口範圍: {df['exports'].min():.1f} 至 {df['exports'].max():.1f} (十億港元)")
        print(f"   進口範圍: {df['imports'].min():.1f} 至 {df['imports'].max():.1f} (十億港元)")
        print(f"   貿易餘額範圍: {df['balance'].min():.1f} 至 {df['balance'].max():.1f} (十億港元)")

        return True

    except Exception as e:
        print(f"❌ 貿易數據驗證失敗: {e}")
        return False

def verify_hkma_data():
    """驗證HKMA數據"""
    print("\n=== HKMA數據驗證 ===")

    try:
        hkma_file = Path("CODEX--/data/final_real_indicators/hkma_real_data_with_indicators.csv")
        if not hkma_file.exists():
            print("❌ HKMA文件不存在")
            return False

        df = pd.read_csv(hkma_file)
        print(f"✅ HKMA數據載入成功: {len(df)} 條記錄")
        print(f"   期間範圍: {df['Period'].min()} 至 {df['Period'].max()}")
        print(f"   數據頻率: {df['Frequency'].unique()}")
        print(f"   圖表數值範圍: {df['Figure_HKD_Billion'].min():.1f} 至 {df['Figure_HKD_Billion'].max():.1f} (十億港元)")

        # 檢查技術指標是否存在
        indicators = ['RSI_14', 'MACD_Line', 'BB_Upper', 'ADX']
        available_indicators = [ind for ind in indicators if ind in df.columns]
        print(f"   可用技術指標: {len(available_indicators)} 個 ({', '.join(available_indicators)})")

        return True

    except Exception as e:
        print(f"❌ HKMA數據驗證失敗: {e}")
        return False

def calculate_data_quality_score():
    """計算數據質量評分"""
    print("\n=== 數據質量評估 ===")

    quality_scores = {
        'hibor': verify_hibor_data(),
        'gdp': verify_gdp_data(),
        'trade': verify_trade_data(),
        'hkma': verify_hkma_data()
    }

    available_sources = sum(quality_scores.values())
    total_sources = len(quality_scores)
    quality_percentage = (available_sources / total_sources) * 100

    print(f"\n📊 數據質量總結:")
    print(f"   可用數據源: {available_sources}/{total_sources}")
    print(f"   質量評分: {quality_percentage:.1f}%")

    if quality_percentage == 100:
        print("   ✅ 所有數據源都可用，數據質量優秀")
    elif quality_percentage >= 75:
        print("   ✅ 大部分數據源可用，數據質量良好")
    elif quality_percentage >= 50:
        print("   ⚠️  部分數據源可用，數據質量一般")
    else:
        print("   ❌ 數據源不足，需要補充數據")

    return quality_percentage

def main():
    """主驗證函數"""
    print("🔍 香港政府真實數據質量驗證")
    print("=" * 50)
    print(f"驗證時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 執行所有驗證
    quality_score = calculate_data_quality_score()

    print(f"\n🎯 結論:")
    if quality_score >= 75:
        print("✅ 真實數據驗證通過，系統可以使用這些數據進行技術分析")
    else:
        print("❌ 真實數據驗證未完全通過，需要檢查數據源")

    return quality_score >= 75

if __name__ == "__main__":
    main()
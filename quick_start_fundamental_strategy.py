#!/usr/bin/env python3
"""
Quick Start Fundamental Strategy
快速啟動基本面策略

專門針對非價格數據（經濟指標、基本面數據）策略的快速啟動工具
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

def print_banner():
    """打印啟動橫幅"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    CBS-C 基本面/經濟數據策略系統                            ║
║    Fundamental & Economic Data Strategy System               ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)

async def show_fundamental_strategies():
    """展示可用的基本面策略"""
    print("\n📊 可用的基本面/經濟數據策略:")
    print("-" * 60)

    strategies = {
        "1. HIBOR策略": {
            "描述": "基於香港銀行同業拆息率的貨幣政策策略",
            "邏輯": "低利率 = 寬鬆貨幣政策 = 看漲",
            "數據": "HIBOR利率",
            "適用": "利率敏感型資產（港股、REITs）"
        },
        "2. GDP增長策略": {
            "描述": "基於GDP增長率的經濟周期策略",
            "邏輯": "高GDP增長 = 經濟擴張 = 看漲",
            "數據": "GDP季度/年度增長率",
            "適用": "大盤指數、周期性股票"
        },
        "3. PMI策略": {
            "描述": "基於採購經理人指數的經濟活動策略",
            "邏輯": "PMI > 50 = 經濟擴張 = 看漲",
            "數據": "製造業/服務業PMI",
            "適用": "製造業、服務業相關股票"
        },
        "4. 訪客到港策略": {
            "描述": "基於香港訪客數據的旅遊業策略",
            "邏輯": "訪客增加 = 旅遊業繁榮 = 看漲相關股票",
            "數據": "月度訪客數量",
            "適用": "零售、酒店、旅遊股"
        },
        "5. 失業率策略": {
            "描述": "基於失業率的就業市場策略",
            "邏輯": "失業率下降 = 就業改善 = 看漲",
            "數據": "失業率月度數據",
            "適用": "消費類、金融類股票"
        },
        "6. 綜合經濟策略": {
            "描述": "結合多個經濟指標的綜合策略",
            "邏輯": "多指標共識 = 更可靠的信號",
            "數據": "綜合經濟數據",
            "適用": "大盤、多元化投資組合"
        },
        "7. 智能混合策略": {
            "描述": "價格數據 + 經濟數據的智能組合",
            "邏輯": "根據經濟環境動態調整技術策略權重",
            "數據": "價格 + 經濟數據",
            "適用": "全市場、多資產類別"
        }
    }

    for key, info in strategies.items():
        print(f"\n{key}")
        print(f"  描述: {info['描述']}")
        print(f"  邏輯: {info['邏輯']}")
        print(f"  數據: {info['數據']}")
        print(f"  適用: {info['適用']}")

async def run_hibor_example():
    """運行HIBOR策略示例"""
    print("\n🚀 運行HIBOR策略示例...")

    from examples.mixed_data_strategy_example import main as mixed_example

    # 修改配置以專注HIBOR策略
    print("""
    HIBOR策略配置示例:
    - 觀察期: 30天
    - 高利率閾值: 5%
    - 低利率閾值: 2%
    - 使用動量: 是

    信號生成邏輯:
    1. HIBOR < 2% → 強烈看漲信號
    2. HIBOR下降 → 看漲信號
    3. HIBOR > 5% → 強烈看跌信號
    4. HIBOR上升 → 看跌信號
    """)

async def run_composite_example():
    """運行綜合經濟策略示例"""
    print("\n🚀 運行綜合經濟策略示例...")

    from examples.mixed_data_strategy_example import main as mixed_example
    await mixed_example()

async def run_mixed_strategy_example():
    """運行混合策略示例"""
    print("\n🚀 運行智能混合策略示例...")

    from examples.mixed_data_strategy_example import main as mixed_example
    await mixed_example()

def show_data_sources():
    """顯示數據源信息"""
    print("\n📡 經濟數據源:")
    print("-" * 60)

    sources = {
        "HIBOR": {
            "頻率": "每日",
            "來源": "香港金管局",
            "延遲": "T+0",
            "可靠性": "高"
        },
        "GDP": {
            "頻率": "季度",
            "來源": "政府統計處",
            "延遲": "T+45天",
            "可靠性": "高"
        },
        "PMI": {
            "頻率": "每月",
            "來源": "採購與供應管理學會",
            "延遲": "T+1天",
            "可靠性": "高"
        },
        "訪客數據": {
            "頻率": "每月",
            "來源": "香港旅遊發展局",
            "延遲": "T+7天",
            "可靠性": "中"
        },
        "失業率": {
            "頻率": "每月",
            "來源": "政府統計處",
            "延遲": "T+15天",
            "可靠性": "高"
        }
    }

    for indicator, info in sources.items():
        print(f"\n{indicator}:")
        for key, value in info.items():
            print(f"  {key}: {value}")

def show_best_practices():
    """顯示最佳實踐"""
    print("\n💡 基本面策略最佳實踐:")
    print("-" * 60)

    practices = [
        {
            "原則": "數據質量優先",
            "說明": "優先使用官方、可靠數據源，注意數據修訂"
        },
        {
            "原則": "理解數據特性",
            "說明": "不同經濟指標有不同的更新頻率和延遲"
        },
        {
            "原則": "避免未來函數",
            "說明": "確保在策略執行時才能獲取到的數據"
        },
        {
            "原則": "結合多維度",
            "說明": "單一指標可能產生誤導，多指標共識更可靠"
        },
        {
            "原則": "考慮市場預期",
            "說明": "重要的是數據與預期的差異，而非絕對值"
        },
        {
            "原則": "長期视角",
            "說明": "經濟數據反映長期趨勢，不宜過度交易"
        }
    ]

    for i, practice in enumerate(practices, 1):
        print(f"\n{i}. {practice['原則']}")
        print(f"   {practice['說明']}")

async def main():
    """主函數"""
    print_banner()

    # 顯示可用策略
    await show_fundamental_strategies()

    # 顯示數據源信息
    show_data_sources()

    # 顯示最佳實踐
    show_best_practices()

    # 選擇操作
    print("\n" + "="*60)
    print("請選擇操作:")
    print("1. 運行HIBOR策略示例")
    print("2. 運行綜合經濟策略示例")
    print("3. 運行智能混合策略示例")
    print("4. 查看策略配置指南")
    print("5. 退出")

    try:
        choice = input("\n請輸入選項 (1-5): ").strip()

        if choice == '1':
            await run_hibor_example()
        elif choice == '2':
            await run_composite_example()
        elif choice == '3':
            await run_mixed_strategy_example()
        elif choice == '4':
            show_configuration_guide()
        elif choice == '5':
            print("\n再見！")
        else:
            print("\n無效選項")

    except KeyboardInterrupt:
        print("\n\n操作已取消")
    except Exception as e:
        print(f"\n發生錯誤: {str(e)}")

def show_configuration_guide():
    """顯示配置指南"""
    print("\n" + "="*60)
    print("策略配置指南")
    print("="*60)

    guide = """
    1. HIBOR策略配置:
       - lookback_period: 觀察期（天），建議 20-60
       - rate_threshold_high: 高利率閾值，建議 4.5-6.0
       - rate_threshold_low: 低利率閾值，建議 1.5-3.0
       - use_momentum: 是否使用動量，建議 True

    2. GDP策略配置:
       - growth_threshold_high: 高增長閾值，建議 4-6%
       - growth_threshold_low: 低增長閾值，建議 1-2%
       - lookback_quarters: 回看季度，建議 4-8
       - use_acceleration: 是否考慮加速度，建議 True

    3. PMI策略配置:
       - expansion_threshold: 擴張閾值，建議 52-58
       - contraction_threshold: 收縮閾值，建議 42-48
       - trend_periods: 趨勢週期，建議 2-4
       - combine_manufacturing_services: 是否綜合製造業和服務業

    4. 綜合策略配置:
       - indicator_weights: 各指標權重，總和應為1.0
       - hibor_weight: HIBOR權重，建議 0.2-0.4
       - gdp_weight: GDP權重，建議 0.2-0.4
       - pmi_weight: PMI權重，建議 0.2-0.3
       - visitor_weight: 訪客權重，建議 0.1-0.2

    5. 風險管理配置:
       - max_position_size: 最大倉位，建議 0.2-0.4
       - risk_limit: 風險限額，建議 0.02-0.05
       - stop_loss: 止損比例，可選
       - take_profit: 止盈比例，可選

    使用示例:
    ```python
    config = create_strategy_config(
        name="我的HIBOR策略",
        strategy_type=StrategyType.STATISTICAL,
        symbols=["0700.HK"],
        timeframe="1d",
        lookback_period=30,
        rate_threshold_high=5.0,
        rate_threshold_low=2.0
    )
    ```
    """

    print(guide)

if __name__ == "__main__":
    # 設置控制台編碼（Windows）
    if sys.platform == "win32":
        os.system('chcp 65001')

    asyncio.run(main())
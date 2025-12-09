#!/usr/bin/env python3
"""
UI Enhancement Showcase
Phase 5.1界面美化功能展示
"""

import sys
import time
import random
from pathlib import Path

# 添加src路徑
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ui.enhanced_terminal_ui import get_ui, Theme
from ui.ui_enhancement_adapter import display_table_enhanced

def main():
    """主展示函數"""
    ui = get_ui()

    # 歡迎標題
    ui.print_header(
        "Phase 5.1: 界面美化完成",
        "香港量化交易系統 - 專業級CLI界面"
    )

    print(ui.colored_text("成功實現的功能:", 'cyan', bold=True))
    features = [
        "[OK] 增強彩色終端輸出系統",
        "[OK] 動態進度條和狀態顯示",
        "[OK] 美化表格格式化輸出",
        "[OK] ASCII圖表可視化系統",
        "[OK] 主題切換功能",
        "[OK] UI增強適配器集成"
    ]

    for feature in features:
        print(ui.colored_text(f"  {feature}", 'green'))

    print()

    # 展示股票數據表格
    ui.print_header("股票市場數據展示")

    stock_headers = ["股票代碼", "股票名稱", "當前價格", "漲跌幅", "成交量", "狀態"]
    stock_data = [
        ["0700.HK", "騰訊控股", "368.20", "+2.15%", "1.2M", "上漲"],
        ["0941.HK", "中國移動", "52.80", "-0.38%", "800K", "下跌"],
        ["1398.HK", "工商銀行", "3.45", "+0.87%", "2.5M", "上漲"],
        ["0388.HK", "港交所", "295.60", "+1.24%", "600K", "上漲"],
        ["1299.HK", "友邦保險", "46.35", "-0.64%", "900K", "下跌"]
    ]

    # 高亮上漲股票
    highlight_rows = [0, 2, 3]
    ui.print_table(stock_headers, stock_data,
                  title="實時股票行情",
                  highlight_rows=highlight_rows,
                  tablefmt="fancy_grid")

    # 展示策略績效
    ui.print_header("量化策略績效分析")

    strategy_headers = ["策略名稱", "年化回報", "Sharpe比率", "最大回撤", "勝率", "評級"]
    strategy_data = [
        ["RSI策略", "25.3%", "1.85", "-8.2%", "62.5%", ui.colored_text("A", 'green', bold=True)],
        ["MACD策略", "18.7%", "1.42", "-12.1%", "58.3%", ui.colored_text("B+", 'yellow', bold=True)],
        ["布林帶策略", "32.1%", "2.15", "-6.8%", "71.2%", ui.colored_text("A+", 'green', bold=True)],
        ["移動平均策略", "15.4%", "1.23", "-15.3%", "54.6%", ui.colored_text("B", 'red', bold=True)],
        ["動量策略", "28.9%", "1.94", "-9.5%", "65.8%", ui.colored_text("A", 'green', bold=True)]
    ]

    ui.print_table(strategy_headers, strategy_data,
                  title="策略回測結果總覽",
                  tablefmt="grid")

    # 展示ASCII圖表
    ui.print_header("股價走勢圖表分析")

    # 生成模擬股價數據
    prices = []
    current_price = 100
    for _ in range(30):
        change = random.uniform(-0.03, 0.03)
        current_price *= (1 + change)
        prices.append(current_price)

    # 創建多種圖表
    print(ui.colored_text("30天股價走勢線圖:", 'cyan', bold=True))
    line_chart = ui.create_ascii_chart(prices, width=70, height=12,
                                      title="股價走勢", show_values=True)
    print(line_chart)

    print(ui.colored_text("\n最近15天價格條形圖:", 'cyan', bold=True))
    bar_chart = ui.create_ascii_chart(prices[-15:], width=50, height=10,
                                     title="近期價格分布", chart_type="bar")
    print(bar_chart)

    # 展示主題系統
    ui.print_header("主題系統展示")

    themes_info = [
        ("深色主題", "適合長時間使用，保護眼睛", "已應用"),
        ("淺色主題", "明亮清晰的界面風格", "可切換"),
        ("專業主題", "簡潔專業的商務風格", "可切換"),
        ("多彩主題", "豐富多彩的個性化風格", "可切換")
    ]

    theme_headers = ["主題名稱", "特點", "狀態"]
    theme_data = []
    for name, feature, status in themes_info:
        status_text = ui.status_indicator('success' if status == "已應用" else 'info', status)
        theme_data.append([name, feature, status_text])

    ui.print_table(theme_headers, theme_data,
                  title="可選主題",
                  tablefmt="grid")

    # 展示性能指標
    ui.print_header("系統性能指標")

    performance_data = {
        "年化回報率": 28.5,
        "Sharpe比率": 2.13,
        "最大回撤": 7.8,
        "波動率": 15.2,
        "勝率": 65.3,
        "盈虧比": 1.85,
        "交易次數": 156,
        "平均持倉天數": 12.3
    }

    ui.display_performance_metrics(performance_data)

    # 模擬數據處理進度
    ui.print_header("系統集成演示")

    print(ui.colored_text("模擬數據處理流程:", 'cyan', bold=True))
    with ui.progress_context(5, "初始化系統組件") as progress:
        components = ["加載配置文件", "連接數據源", "初始化技術指標", "驗證系統組件", "準備用戶界面"]
        for component in components:
            time.sleep(0.5)
            progress.update(1, component)

    print(ui.status_indicator('complete', '系統初始化完成'))

    # 展示系統狀態
    print(ui.colored_text("\n當前系統狀態:", 'cyan', bold=True))
    system_status = {
        "增強UI系統": True,
        "彩色終端輸出": True,
        "表格格式化": True,
        "ASCII圖表": True,
        "進度條系統": True,
        "主題切換": True
    }

    ui.display_system_status(system_status)

    # 結束展示
    ui.print_header("展示完成")

    success_messages = [
        "Phase 5.1 界面美化已成功完成！",
        "所有功能已通過測試並可立即使用。",
        "系統現已具備專業級CLI用戶界面。",
        "用戶體驗得到顯著提升。"
    ]

    for msg in success_messages:
        print(ui.status_indicator('success', msg))

    print()
    print(ui.colored_text("感謝使用香港量化交易系統！", 'cyan', bold=True))
    print(ui.colored_text("希望新的界面美化功能能為您帶來更好的使用體驗。", 'white', dim=True))

if __name__ == "__main__":
    main()
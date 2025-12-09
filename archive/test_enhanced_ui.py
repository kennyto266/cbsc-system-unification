#!/usr/bin/env python3
"""
Enhanced Terminal UI Demo
展示Phase 5.1界面美化功能
"""

import sys
import time
import random
import numpy as np
from pathlib import Path

# 添加src路徑
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ui.enhanced_terminal_ui import (
    EnhancedTerminalUI,
    Theme,
    get_ui,
    colored_text,
    status_indicator,
    print_header,
    print_table
)

def demo_colored_text(ui: EnhancedTerminalUI):
    """演示彩色文本系統"""
    print_header("彩色文本系統演示", "展示各種顏色和樣式效果")

    print(ui.colored_text("基礎顏色演示：", 'white', bold=True))
    colors = ['red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white']
    for color in colors:
        text = ui.colored_text(f"這是{color}顏色文本", color)
        print(f"  {text}")

    print("\n" + ui.colored_text("效果演示：", 'white', bold=True))
    effects = [
        ("粗體文本", {'bold': True}),
        ("暗色文本", {'dim': True}),
        ("下劃線文本", {'underline': True}),
        ("背景色文本", {'bg_color': 'blue'}),
        ("組合效果", {'bold': True, 'underline': True, 'color': 'yellow', 'bg_color': 'blue'})
    ]

    for text, kwargs in effects:
        print(f"  {ui.colored_text(text, **kwargs)}")

    print("\n" + ui.colored_text("狀態指示器：", 'white', bold=True))
    statuses = ['success', 'error', 'warning', 'info', 'loading', 'complete', 'pending', 'running']
    for status in statuses:
        indicator = ui.status_indicator(status, f"{status.title()} 狀態")
        print(f"  {indicator}")

    print()

def demo_progress_bars(ui: EnhancedTerminalUI):
    """演示進度條系統"""
    print_header("進度條系統演示", "展示各種進度條效果")

    # 模擬數據處理進度
    print(ui.colored_text("模擬數據加載：", 'cyan', bold=True))
    progress_id = ui.create_progress_bar(100, "加載數據中", show_eta=True)

    for i in range(101):
        ui.update_progress(progress_id, 1)
        time.sleep(0.02)

    print()

    # 使用上下文管理器
    print(ui.colored_text("使用上下文管理器：", 'cyan', bold=True))
    with ui.progress_context(50, "計算中") as progress:
        for i in range(50):
            progress.update(1)
            time.sleep(0.03)

    print()

def demo_tables(ui: EnhancedTerminalUI):
    """演示表格系統"""
    print_header("表格格式化演示", "展示各種表格樣式和效果")

    # 基本表格數據
    headers = ["股票代碼", "股票名稱", "當前價格", "漲跌幅", "成交量", "狀態"]
    data = [
        ["0700.HK", "騰訊控股", "368.20", "+2.15%", "1.2M", "上漲"],
        ["0941.HK", "中國移動", "52.80", "-0.38%", "800K", "下跌"],
        ["1398.HK", "工商銀行", "3.45", "+0.87%", "2.5M", "上漲"],
        ["0388.HK", "港交所", "295.60", "+1.24%", "600K", "上漲"],
        ["1299.HK", "友邦保險", "46.35", "-0.64%", "900K", "下跌"]
    ]

    # 基本表格
    print(ui.colored_text("基本表格：", 'cyan', bold=True))
    ui.print_table(headers, data, tablefmt="grid")
    print()

    # 高亮行的表格
    print(ui.colored_text("高亮顯示上漲股票：", 'cyan', bold=True))
    highlight_rows = [i for i, row in enumerate(data) if row[5] == "上漲"]
    ui.print_table(headers, data, tablefmt="fancy_grid", highlight_rows=highlight_rows)
    print()

    # 列顏色表格
    print(ui.colored_text("列顏色標記：", 'cyan', bold=True))
    col_colors = ['white', 'white', 'cyan', 'green' if data[0][3].startswith('+') else 'red', 'yellow', 'white']
    ui.print_table(headers, data, tablefmt="rounded_grid", col_colors=col_colors)
    print()

    # 性能指標表格
    perf_headers = ["策略名稱", "年化回報", "Sharpe比率", "最大回撤", "勝率", "評級"]
    perf_data = [
        ["RSI策略", "25.3%", "1.85", "-8.2%", "62.5%", "A"],
        ["MACD策略", "18.7%", "1.42", "-12.1%", "58.3%", "B+"],
        ["布林帶策略", "32.1%", "2.15", "-6.8%", "71.2%", "A+"],
        ["移動平均策略", "15.4%", "1.23", "-15.3%", "54.6%", "B"],
        ["動量策略", "28.9%", "1.94", "-9.5%", "65.8%", "A"]
    ]

    print(ui.colored_text("量化策略績效表格：", 'cyan', bold=True))
    ui.print_table(perf_headers, perf_data, title="策略回測結果", tablefmt="grid")
    print()

def demo_ascii_charts(ui: EnhancedTerminalUI):
    """演示ASCII圖表系統"""
    print_header("ASCII圖表演示", "展示各種ASCII圖表效果")

    # 生成模擬股價數據
    days = 30
    prices = []
    current_price = 100
    for _ in range(days):
        change = random.uniform(-0.03, 0.03)
        current_price *= (1 + change)
        prices.append(current_price)

    # 線圖
    print(ui.colored_text("股價走勢線圖：", 'cyan', bold=True))
    line_chart = ui.create_ascii_chart(prices, width=70, height=12,
                                      title="30天股價走勢", show_values=True)
    print(line_chart)
    print()

    # 條形圖
    print(ui.colored_text("條形圖：", 'cyan', bold=True))
    bar_chart = ui.create_ascii_chart(prices[-15:], width=50, height=10,
                                     title="最近15天股價條形圖", chart_type="bar")
    print(bar_chart)
    print()

    # 面積圖
    print(ui.colored_text("面積圖：", 'cyan', bold=True))
    area_chart = ui.create_ascii_chart(prices, width=70, height=10,
                                     title="股價變化面積圖", chart_type="area")
    print(area_chart)
    print()

    # 蠟燭圖
    print(ui.colored_text("蠟燭圖：", 'cyan', bold=True))
    # 生成OHLC數據
    ohlc_data = []
    for price in prices[-10:]:
        high = price * random.uniform(1.0, 1.02)
        low = price * random.uniform(0.98, 1.0)
        open_price = price * random.uniform(0.99, 1.01)
        close_price = price
        ohlc_data.append((open_price, high, low, close_price))

    candlestick = ui.create_candlestick_chart(ohlc_data, width=40, height=10,
                                             title="蠟燭圖演示")
    print(candlestick)
    print()

def demo_themes(ui: EnhancedTerminalUI):
    """演示主題切換"""
    print_header("主題系統演示", "展示不同主題效果")

    themes = [Theme.DARK, Theme.LIGHT, Theme.PROFESSIONAL, Theme.COLORFUL]

    for theme in themes:
        ui.set_theme(theme)
        print(f"\n{ui.colored_text(f'當前主題: {ui.theme_config.name}',
                                 ui.theme_config.primary_color, bold=True)}")

        demo_text = f"這是{ui.theme_config.name}的效果演示"
        print(ui.colored_text(demo_text, ui.theme_config.primary_color))

        status_text = f"{ui.theme_config.name}狀態指示器"
        print(ui.status_indicator('success', status_text))

        ui.print_separator("-", 50, ui.theme_config.secondary_color)

def demo_performance_metrics(ui: EnhancedTerminalUI):
    """演示性能指標顯示"""
    print_header("性能指標顯示演示", "展示量化系統性能指標")

    # 模擬性能數據
    metrics = {
        "年化回報率": 28.5,
        "Sharpe比率": 2.13,
        "最大回撤": 7.8,
        "波動率": 15.2,
        "勝率": 65.3,
        "盈虧比": 1.85,
        "交易次數": 156,
        "平均持倉天數": 12.3
    }

    ui.display_performance_metrics(metrics)
    print()

def demo_system_status(ui: EnhancedTerminalUI):
    """演示系統狀態顯示"""
    print_header("系統狀態顯示演示", "展示量化系統組件狀態")

    # 模擬系統信息
    system_info = {
        "Simplified System": True,
        "GPU加速": False,
        "VectorBT引擎": True,
        "Real Data API": True,
        "Telegram Bot": True,
        "回測功能": True,
        "優化引擎": True,
        "風險管理": True
    }

    ui.display_system_status(system_info)
    print()

def demo_pagination(ui: EnhancedTerminalUI):
    """演示表格分頁功能"""
    print_header("表格分頁演示", "展示大數據集分頁效果")

    # 生成大量模擬數據
    headers = ["策略ID", "策略名稱", "回報率", "Sharpe", "最大回撤", "評級"]

    data = []
    strategies = ["RSI", "MACD", "布林帶", "移動平均", "KDJ", "CCI", "威廉姆斯", "RSI+MACD"]

    for i in range(50):  # 生成50條記錄
        strategy = random.choice(strategies)
        returns = random.uniform(-10, 40)
        sharpe = random.uniform(0.5, 3.0)
        max_drawdown = random.uniform(-25, -2)

        if sharpe > 2.0:
            grade = "A+"
        elif sharpe > 1.5:
            grade = "A"
        elif sharpe > 1.0:
            grade = "B+"
        else:
            grade = "B"

        data.append([f"ST_{i:03d}", strategy, f"{returns:.1f}%",
                    f"{sharpe:.2f}", f"{max_drawdown:.1f}%", grade])

    # 分頁顯示（每頁10行）
    ui.paginate_table(headers, data, rows_per_page=10,
                     title="策略回測結果總覽 (共50條記錄)",
                     tablefmt="grid")

def main():
    """主演示函數"""
    # 創建UI實例
    ui = get_ui()

    # 歡迎界面
    print_header("Enhanced Terminal UI 演示", "Phase 5.1 界面美化功能展示")

    print(ui.colored_text("歡迎使用增強終端UI系統！", 'cyan', bold=True))
    print(ui.colored_text("本演示將展示以下功能：", 'white'))

    features = [
        "✓ 增強彩色終端輸出",
        "✓ 動態進度條和狀態顯示",
        "✓ 美化表格格式化輸出",
        "✓ ASCII圖表選項",
        "✓ 主題切換系統",
        "✓ 性能指標顯示",
        "✓ 系統狀態監控",
        "✓ 表格分頁功能"
    ]

    for feature in features:
        print(f"  {ui.colored_text(feature, 'green')}")

    print()

    # 詢問是否開始演示
    try:
        choice = input("按Enter開始演示，或輸入'q'退出: ").strip().lower()
        if choice == 'q':
            return
    except KeyboardInterrupt:
        print("\n" + ui.status_indicator('info', '演示結束'))
        return

    # 開始各項功能演示
    demos = [
        ("彩色文本系統", demo_colored_text),
        ("進度條系統", demo_progress_bars),
        ("表格格式化", demo_tables),
        ("ASCII圖表", demo_ascii_charts),
        ("主題系統", demo_themes),
        ("性能指標顯示", demo_performance_metrics),
        ("系統狀態", demo_system_status),
        ("表格分頁", demo_pagination)
    ]

    for demo_name, demo_func in demos:
        print_header(f"開始演示: {demo_name}")

        try:
            demo_func(ui)
        except Exception as e:
            print(ui.status_indicator('error', f"演示 {demo_name} 時出錯: {e}"))

        if demo_name != demos[-1][0]:  # 不是最後一個演示
            try:
                choice = input("\n按Enter繼續下一個演示，或輸入'q'退出: ").strip().lower()
                if choice == 'q':
                    break
            except KeyboardInterrupt:
                print("\n" + ui.status_indicator('info', '演示中斷'))
                break

        # 清屏
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')

    # 結束演示
    print_header("演示完成", "感謝使用Enhanced Terminal UI系統")
    print(ui.colored_text("所有功能已成功演示！", 'green', bold=True))
    print(ui.colored_text("您現在可以在量化交易系統中使用這些增強的界面功能。", 'cyan'))

if __name__ == "__main__":
    main()
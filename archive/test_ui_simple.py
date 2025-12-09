#!/usr/bin/env python3
"""
Simple UI Test
簡化版UI功能測試，避免編碼問題
"""

import sys
import time
import random
from pathlib import Path

# 添加src路徑
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_basic_ui():
    """測試基本UI功能"""
    print("=" * 60)
    print("Enhanced Terminal UI Demo - Phase 5.1")
    print("=" * 60)
    print()

    try:
        from ui.enhanced_terminal_ui import get_ui

        ui = get_ui()
        print("UI System initialized successfully")

        # 測試彩色文本（避免Unicode字符）
        print("\n=== Colored Text Test ===")
        print(ui.colored_text("This is red text", 'red'))
        print(ui.colored_text("This is green text", 'green'))
        print(ui.colored_text("This is blue text", 'blue'))
        print(ui.colored_text("This is bold text", 'white', bold=True))

        # 測試狀態指示器（避免Unicode字符）
        print("\n=== Status Indicator Test ===")
        print(ui.status_indicator('success', 'Operation completed'))
        print(ui.status_indicator('error', 'Operation failed'))
        print(ui.status_indicator('warning', 'Warning message'))
        print(ui.status_indicator('info', 'Information'))

        print("\n=== Basic Test Passed ===")
        return True

    except Exception as e:
        print(f"Error in basic UI test: {e}")
        return False

def test_table_display():
    """測試表格顯示"""
    print("\n" + "=" * 60)
    print("Table Display Test")
    print("=" * 60)

    try:
        from ui.enhanced_terminal_ui import get_ui

        ui = get_ui()

        # 創建測試數據
        headers = ["Stock Code", "Name", "Price", "Change %", "Status"]
        data = [
            ["0700.HK", "Tencent", "368.20", "+2.15", "UP"],
            ["0941.HK", "China Mobile", "52.80", "-0.38", "DOWN"],
            ["1398.HK", "ICBC", "3.45", "+0.87", "UP"],
            ["0388.HK", "HKEX", "295.60", "+1.24", "UP"],
            ["1299.HK", "AIA", "46.35", "-0.64", "DOWN"]
        ]

        # 基本表格
        print("\nBasic Table:")
        ui.print_table(headers, data, title="Stock Market Data")

        # 高亮行
        print("\nHighlighted Table (UP stocks):")
        highlight_rows = [0, 2, 3]  # Highlight rows with UP status
        ui.print_table(headers, data, highlight_rows=highlight_rows)

        print("\n=== Table Test Passed ===")
        return True

    except Exception as e:
        print(f"Error in table test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_progress_bar():
    """測試進度條"""
    print("\n" + "=" * 60)
    print("Progress Bar Test")
    print("=" * 60)

    try:
        from ui.enhanced_terminal_ui import get_ui

        ui = get_ui()

        # 基本進度條
        print("\nBasic Progress Bar:")
        progress_id = ui.create_progress_bar(50, "Processing data", show_eta=True)

        for i in range(51):
            ui.update_progress(progress_id, 1)
            time.sleep(0.02)

        # 上下文管理器
        print("\nContext Manager Progress Bar:")
        with ui.progress_context(30, "Calculating") as progress:
            for i in range(30):
                progress.update(1)
                time.sleep(0.03)

        print("\n=== Progress Bar Test Passed ===")
        return True

    except Exception as e:
        print(f"Error in progress test: {e}")
        return False

def test_ascii_chart():
    """測試ASCII圖表"""
    print("\n" + "=" * 60)
    print("ASCII Chart Test")
    print("=" * 60)

    try:
        from ui.enhanced_terminal_ui import get_ui

        ui = get_ui()

        # 生成測試數據
        prices = []
        current_price = 100
        for _ in range(20):
            change = random.uniform(-0.02, 0.02)
            current_price *= (1 + change)
            prices.append(current_price)

        # 線圖
        print("\nLine Chart:")
        chart = ui.create_ascii_chart(prices, width=50, height=10, title="Price Trend")
        print(chart)

        # 條形圖
        print("\nBar Chart:")
        bar_chart = ui.create_ascii_chart(prices[-10:], width=40, height=8,
                                         title="Recent Prices", chart_type="bar")
        print(bar_chart)

        print("\n=== ASCII Chart Test Passed ===")
        return True

    except Exception as e:
        print(f"Error in chart test: {e}")
        return False

def test_themes():
    """測試主題系統"""
    print("\n" + "=" * 60)
    print("Theme System Test")
    print("=" * 60)

    try:
        from ui.enhanced_terminal_ui import get_ui, Theme

        ui = get_ui()
        themes = [Theme.DARK, Theme.LIGHT, Theme.PROFESSIONAL, Theme.COLORFUL]

        for theme in themes:
            ui.set_theme(theme)
            print(f"\nCurrent Theme: {ui.theme_config.name}")
            print(ui.colored_text(f"This is {ui.theme_config.name} theme demo",
                                 ui.theme_config.primary_color))
            ui.print_separator("-", 40, ui.theme_config.secondary_color)

        # 恢復默認主題
        ui.set_theme(Theme.DARK)

        print("\n=== Theme Test Passed ===")
        return True

    except Exception as e:
        print(f"Error in theme test: {e}")
        return False

def test_adapter():
    """測試適配器"""
    print("\n" + "=" * 60)
    print("UI Adapter Test")
    print("=" * 60)

    try:
        from ui.ui_enhancement_adapter import get_ui_adapter, display_table_enhanced

        adapter = get_ui_adapter()

        # 測試適配器功能
        headers = ["Strategy", "Return %", "Sharpe", "Max DD %"]
        data = [
            ["RSI", "25.3", "1.85", "-8.2"],
            ["MACD", "18.7", "1.42", "-12.1"],
            ["Bollinger", "32.1", "2.15", "-6.8"]
        ]

        print("\nAdapter Table Display:")
        display_table_enhanced(data, headers, title="Strategy Performance")

        print("\n=== Adapter Test Passed ===")
        return True

    except Exception as e:
        print(f"Error in adapter test: {e}")
        return False

def main():
    """主測試函數"""
    print("Starting Enhanced Terminal UI Tests...")
    print("Phase 5.1 Interface Enhancement")

    tests = [
        ("Basic UI Functions", test_basic_ui),
        ("Table Display", test_table_display),
        ("Progress Bars", test_progress_bar),
        ("ASCII Charts", test_ascii_chart),
        ("Theme System", test_themes),
        ("UI Adapter", test_adapter)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Running: {test_name}")
        print('='*60)

        try:
            if test_func():
                passed += 1
                print(f"[+] {test_name} PASSED")
            else:
                print(f"[-] {test_name} FAILED")
        except Exception as e:
            print(f"[!] {test_name} ERROR: {e}")

    # 總結
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")

    if passed == total:
        print("\n[SUCCESS] All tests passed! Phase 5.1 UI Enhancement is working correctly.")
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed. Please check the implementation.")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
UI Integration Test
測試UI增強適配器與現有交互式界面的集成
"""

import sys
import time
import random
from pathlib import Path

# 添加src路徑
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ui.ui_enhancement_adapter import (
    UIEnhancementAdapter,
    enhance_class,
    display_results_enhanced,
    show_progress_enhanced,
    display_table_enhanced,
    get_ui_adapter
)

from ui.enhanced_terminal_ui import get_ui

class MockInteractiveTrader:
    """模擬的交互式交易者類"""

    def __init__(self):
        self.version = "2.0.0"
        self.simplified_system_available = True
        self.gpu_available = False
        self.vectorbt_available = True

    def _get_colored_text(self, text: str, color: str = 'white') -> str:
        """原始彩色文本方法"""
        return f"[{color}] {text} [/{color}]"

    def _print_header(self):
        """原始標題打印方法"""
        print("=== 原始標題 ===")
        print(f"版本: {self.version}")

    def _print_main_menu(self):
        """原始主菜單方法"""
        print("=== 原始主菜單 ===")
        print("1. 數據分析")
        print("2. 技術指標")
        print("3. 回測引擎")

    def analyze_stocks(self):
        """模擬股票分析"""
        print("執行股票分析...")
        time.sleep(1)
        return True

    def backtest_strategies(self):
        """模擬策略回測"""
        print("執行策略回測...")
        time.sleep(2)
        return True

    def get_stock_data(self):
        """獲取股票數據"""
        # 模擬股票數據
        data = []
        for i in range(30):
            price = 100 + random.uniform(-10, 10)
            data.append(price)
        return data

    def get_strategy_results(self):
        """獲取策略回測結果"""
        strategies = []
        strategy_names = ["RSI策略", "MACD策略", "布林帶策略", "移動平均策略"]

        for name in strategy_names:
            strategy = {
                'name': name,
                'returns': random.uniform(-5, 35),
                'sharpe': random.uniform(0.5, 2.5),
                'max_drawdown': random.uniform(-20, -3),
                'win_rate': random.uniform(40, 80)
            }
            strategies.append(strategy)

        return strategies

def test_basic_ui_functions():
    """測試基本UI功能"""
    print("\n=== 測試基本UI功能 ===")

    ui = get_ui()
    ui.print_header("基本UI功能測試", "測試彩色文本、狀態指示器等基本功能")

    # 測試彩色文本
    print(ui.colored_text("這是彩色文本測試", 'cyan', bold=True))

    # 測試狀態指示器
    print(ui.status_indicator('success', '操作成功'))
    print(ui.status_indicator('error', '操作失敗'))
    print(ui.status_indicator('warning', '警告信息'))
    print(ui.status_indicator('info', '信息提示'))

    print()

def test_ui_adapter():
    """測試UI適配器"""
    print("\n=== 測試UI適配器 ===")

    # 創建適配器
    adapter = get_ui_adapter()

    # 測試增強類
    EnhancedTrader = enhance_class(MockInteractiveTrader)
    enhanced_trader = EnhancedTrader()

    # 測試增強的標題
    print("測試增強的標題顯示:")
    enhanced_trader._print_header()

    # 測試增強的主菜單
    print("\n測試增強的主菜單顯示:")
    enhanced_trader._print_main_menu()

    print()

def test_enhanced_table_display():
    """測試增強的表格顯示"""
    print("\n=== 測試增強表格顯示 ===")

    # 創建測試數據
    headers = ["股票代碼", "名稱", "價格", "漲跌幅", "成交量", "狀態"]
    data = [
        ["0700.HK", "騰訊控股", 368.20, 2.15, 1200000, "上漲"],
        ["0941.HK", "中國移動", 52.80, -0.38, 800000, "下跌"],
        ["1398.HK", "工商銀行", 3.45, 0.87, 2500000, "上漲"],
        ["0388.HK", "港交所", 295.60, 1.24, 600000, "上漲"],
        ["1299.HK", "友邦保險", 46.35, -0.64, 900000, "下跌"]
    ]

    # 測試基本表格
    print("基本表格顯示:")
    display_table_enhanced(data, headers, title="股票行情")

    # 測試條件高亮（高亮上漲股票）
    def highlight_up_stocks(row):
        return len(row) > 5 and row[5] == "上漲"

    print("\n條件高亮表格（高亮上漲股票）:")
    display_table_enhanced(data, headers, title="股票行情（高亮上漲）",
                          highlight_condition=highlight_up_stocks)

    print()

def test_enhanced_results_display():
    """測試增強的結果顯示"""
    print("\n=== 測試增強結果顯示 ===")

    # 模擬交易者
    EnhancedTrader = enhance_class(MockInteractiveTrader)
    trader = EnhancedTrader()

    # 準備結果數據
    strategies = trader.get_strategy_results()
    stock_data = trader.get_stock_data()

    results = {
        'strategies': strategies,
        'charts': {
            '股票價格走勢': stock_data,
            '策略性能曲線': [random.uniform(0, 100) for _ in range(20)]
        }
    }

    # 顯示增強的結果
    trader._enhanced_display_results(results, "策略回測結果")

    print()

def test_progress_display():
    """測試進度顯示"""
    print("\n=== 測試進度顯示 ===")

    # 模擬數據處理
    def process_data_step(i):
        time.sleep(0.1)  # 模擬處理時間
        return True

    print("測試基本進度條:")
    show_progress_enhanced("處理數據中", 20)

    print("\n測試帶更新函數的進度條:")
    show_progress_enhanced("計算策略指標", 15, process_data_step)

    print()

def test_theme_switching():
    """測試主題切換"""
    print("\n=== 測試主題切換 ===")

    adapter = get_ui_adapter()

    # 測試主題切換邏輯
    print("測試主題切換命令識別:")

    test_inputs = ['theme', '主題', 't', 'Theme', 'THEME', 'other']
    for input_val in test_inputs:
        result = adapter.handle_theme_switching(input_val)
        print(f"輸入: '{input_val}' -> 主題切換: {'是' if result else '否'}")

    # 展示不同主題效果
    from ui.enhanced_terminal_ui import Theme
    themes_to_test = [Theme.DARK, Theme.PROFESSIONAL, Theme.COLORFUL]

    for theme in themes_to_test:
        adapter.ui.set_theme(theme)
        print(f"\n當前主題: {adapter.ui.theme_config.name}")
        print(adapter.ui.colored_text(f"這是 {adapter.ui.theme_config.name} 主題的效果演示",
                                     adapter.ui.theme_config.primary_color))

    # 恢復默認主題
    adapter.ui.set_theme(Theme.DARK)

    print()

def test_error_and_success_messages():
    """測試錯誤和成功信息顯示"""
    print("\n=== 測試信息顯示 ===")

    adapter = get_ui_adapter()

    print("測試各種信息顯示:")

    adapter.show_success_message("操作成功完成", "所有數據已正確保存")
    adapter.show_warning_message("警告", "數據可能不完整")
    adapter.show_error_message("操作失敗", "無法連接到數據庫")

    print()

def test_integration_workflow():
    """測試完整的工作流程集成"""
    print("\n=== 測試完整工作流程 ===")

    # 創建增強的交易者
    EnhancedTrader = enhance_class(MockInteractiveTrader)
    trader = EnhancedTrader()

    # 顯示標題
    trader._print_header()

    # 模擬數據加載進程
    print("\n正在加載系統組件...")
    with trader.ui.progress_context(5, "初始化系統") as progress:
        components = ["加載配置", "連接數據源", "初始化指標", "檢查GPU", "準備界面"]
        for component in components:
            time.sleep(0.3)
            progress.update(1, component)

    # 顯示主菜單
    print("\n")
    trader._print_main_menu()

    # 模擬選擇功能
    trader.enhance_menu_choice_display("1", "數據分析")

    # 執行數據分析
    print("\n執行數據分析...")
    with trader.ui.progress_context(10, "分析股票數據") as progress:
        for i in range(10):
            time.sleep(0.1)
            progress.update(1, f"分析步驟 {i+1}/10")

    # 顯示分析結果
    strategies = trader.get_strategy_results()
    results = {'strategies': strategies}
    trader._enhanced_display_results(results, "數據分析結果")

    print("\n工作流程測試完成！")

def main():
    """主測試函數"""
    print("UI增強適配器集成測試")
    print("=" * 50)

    try:
        # 運行各項測試
        test_basic_ui_functions()
        test_ui_adapter()
        test_enhanced_table_display()
        test_enhanced_results_display()
        test_progress_display()
        test_theme_switching()
        test_error_and_success_messages()
        test_integration_workflow()

        print("\n" + "=" * 50)
        print("所有測試完成！")
        print("UI增強功能已成功集成到交互式量化交易界面中。")

    except Exception as e:
        print(f"\n測試過程中出現錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
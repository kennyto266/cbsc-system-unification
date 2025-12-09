#!/usr/bin/env python3
"""
UI Enhancement Adapter
為現有的交互式量化交易界面提供UI增強功能
"""

import sys
import time
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

# 添加src路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from ui.enhanced_terminal_ui import EnhancedTerminalUI, Theme, get_ui

class UIEnhancementAdapter:
    """UI增強適配器，為現有界面提供增強功能"""

    def __init__(self, config_dir: str = "config"):
        self.ui = get_ui()
        self.original_methods = {}
        self.enhanced_mode = True

    def enhance_interactive_trader(self, trader_class):
        """增強交互式交易者類"""
        # 保存原始方法
        self.original_methods = {
            '_get_colored_text': getattr(trader_class, '_get_colored_text', None),
            '_print_header': getattr(trader_class, '_print_header', None),
            '_print_main_menu': getattr(trader_class, '_print_main_menu', None)
        }

        # 增強方法
        enhanced_trader = type(
            f'Enhanced{trader_class.__name__}',
            (trader_class,),
            {
                '_get_colored_text': self._enhanced_get_colored_text,
                '_print_header': self._enhanced_print_header,
                '_print_main_menu': self._enhanced_print_main_menu,
                '_enhanced_display_results': self._enhanced_display_results,
                '_show_enhanced_progress': self._show_enhanced_progress,
                '_display_enhanced_table': self._display_enhanced_table
            }
        )

        return enhanced_trader

    def _enhanced_get_colored_text(self, text: str, color: str = 'white') -> str:
        """增強的彩色文本方法"""
        return self.ui.colored_text(text, color)

    def _enhanced_print_header(self):
        """增強的標題打印方法"""
        self.ui.print_header(
            "香港量化交易系統 - 增強版CLI界面",
            f"版本: {getattr(self, 'version', '1.0.0')} | 增強UI模式"
        )

        # 顯示系統狀態
        status_items = []

        # 檢查各種系統狀態
        system_status = {}

        # 檢查Simplified System
        if hasattr(self, 'simplified_system_available'):
            status = 'success' if self.simplified_system_available else 'error'
            text = 'Simplified System'
            status_items.append((status, text))
            system_status['Simplified System'] = self.simplified_system_available

        # 檢查GPU
        if hasattr(self, 'gpu_available'):
            status = 'success' if self.gpu_available else 'warning'
            text = 'GPU加速' if self.gpu_available else 'CPU模式'
            status_items.append((status, text))
            system_status['GPU加速'] = self.gpu_available

        # 檢查VectorBT
        if hasattr(self, 'vectorbt_available'):
            status = 'success' if self.vectorbt_available else 'warning'
            text = '回測引擎'
            status_items.append((status, text))
            system_status['VectorBT引擎'] = self.vectorbt_available

        # 顯示狀態欄
        self.ui.print_status_bar(status_items)

        # 主題切換選項
        theme_text = f"當前主題: {self.ui.theme_config.name}"
        self.ui.print_separator("-", 60, self.ui.theme_config.info_color)
        print(self.ui.colored_text(f"  {theme_text}", self.ui.theme_config.info_color))
        print(self.ui.colored_text("  輸入 'theme' 切換主題", self.ui.theme_config.secondary_color, dim=True))
        self.ui.print_separator("-", 60, self.ui.theme_config.info_color)

    def _enhanced_print_main_menu(self):
        """增強的主菜單顯示"""
        menu_items = [
            ("1", "數據分析", "獲取和分析股票數據"),
            ("2", "技術指標", "計算和顯示技術指標"),
            ("3", "回測引擎", "執行策略回測"),
            ("4", "優化系統", "參數優化"),
            ("5", "實時監控", "實時數據監控"),
            ("6", "系統設置", "系統配置和設置"),
            ("7", "幫助信息", "查看幫助和文檔"),
            ("0", "退出系統", "退出量化交易系統"),
        ]

        # 創建菜單表格
        headers = ["選項", "功能", "說明"]
        data = []

        for option, feature, description in menu_items:
            colored_option = self.ui.colored_text(option, self.ui.theme_config.primary_color, bold=True)
            colored_feature = self.ui.colored_text(feature, self.ui.theme_config.secondary_color)
            data.append([colored_option, colored_feature, description])

        print(self.ui.colored_text("主菜單:", 'white', bold=True))
        self.ui.print_table(headers, data, tablefmt="grid", show_headers=False)
        print()

        # 添加主題切換提示
        theme_hint = self.ui.colored_text("提示", 'yellow') + ": 輸入 " + \
                    self.ui.colored_text("theme", 'cyan', bold=True) + \
                    " 切換界面主題"
        print(theme_hint)

    def _enhanced_display_results(self, results: Dict[str, Any], title: str = "分析結果"):
        """增強的結果顯示"""
        self.ui.print_header(title)

        if 'strategies' in results:
            # 策略結果表格
            strategies = results['strategies']
            if strategies:
                headers = ['策略名稱', '年化回報', 'Sharpe比率', '最大回撤', '勝率', '評級']
                data = []

                for strategy in strategies:
                    name = strategy.get('name', 'Unknown')
                    returns = strategy.get('returns', 0)
                    sharpe = strategy.get('sharpe', 0)
                    max_drawdown = strategy.get('max_drawdown', 0)
                    win_rate = strategy.get('win_rate', 0)

                    # 根據Sharpe比率確定評級
                    if sharpe > 2.0:
                        rating = self.ui.colored_text('A+', 'green', bold=True)
                    elif sharpe > 1.5:
                        rating = self.ui.colored_text('A', 'green')
                    elif sharpe > 1.0:
                        rating = self.ui.colored_text('B+', 'yellow')
                    else:
                        rating = self.ui.colored_text('B', 'red')

                    data.append([name, f"{returns:.2%}", f"{sharpe:.2f}",
                               f"{max_drawdown:.2%}", f"{win_rate:.1%}", rating])

                self.ui.print_table(headers, data, tablefmt="fancy_grid")

        if 'charts' in results:
            # 顯示圖表
            for chart_name, chart_data in results['charts'].items():
                if chart_data:
                    chart = self.ui.create_ascii_chart(
                        chart_data,
                        title=chart_name,
                        width=70,
                        height=15
                    )
                    print(chart)
                    print()

    def _show_enhanced_progress(self, description: str, total: int, update_func=None):
        """顯示增強的進度條"""
        progress_id = self.ui.create_progress_bar(total, description, show_eta=True)

        if update_func:
            # 如果提供了更新函數，調用它並更新進度
            for i in range(total):
                result = update_func(i)
                self.ui.update_progress(progress_id, 1)
                if result is False:  # 允許提前終止
                    break
        else:
            # 模擬進度
            for i in range(total + 1):
                self.ui.update_progress(progress_id, 1)
                time.sleep(0.05)

    def _display_enhanced_table(self, data: List[List[Any]], headers: List[str],
                               title: str = "", highlight_condition=None):
        """顯示增強的表格"""
        if highlight_condition:
            highlight_rows = []
            for i, row in enumerate(data):
                if highlight_condition(row):
                    highlight_rows.append(i)
            self.ui.print_table(headers, data, title=title,
                              highlight_rows=highlight_rows, tablefmt="fancy_grid")
        else:
            self.ui.print_table(headers, data, title=title, tablefmt="fancy_grid")

    def handle_theme_switching(self, theme_input: str):
        """處理主題切換"""
        if theme_input.lower() in ['theme', '主題', 't']:
            self._show_theme_menu()
            return True
        return False

    def _show_theme_menu(self):
        """顯示主題選擇菜單"""
        self.ui.print_header("主題選擇")

        themes = [
            (Theme.DARK, "深色主題", "適合長時間使用，保護眼睛"),
            (Theme.LIGHT, "淺色主題", "明亮清晰的界面風格"),
            (Theme.PROFESSIONAL, "專業主題", "簡潔專業的商務風格"),
            (Theme.COLORFUL, "多彩主題", "豐富多彩的個性化風格")
        ]

        print("請選擇界面主題:")
        for i, (theme, name, description) in enumerate(themes, 1):
            current_marker = " (當前)" if self.ui.current_theme == theme else ""
            print(f"{i}. {self.ui.colored_text(name, self.ui.theme_config.primary_color)}")
            print(f"   {description}{current_marker}")

        try:
            choice = input("請輸入選項 (1-4): ").strip()
            if choice.isdigit() and 1 <= int(choice) <= 4:
                selected_theme = themes[int(choice) - 1][0]
                self.ui.set_theme(selected_theme)

                print(self.ui.status_indicator('success', f"主題已切換為: {self.ui.theme_config.name}"))
                time.sleep(1)

                # 重新顯示標題
                if hasattr(self, '_print_header'):
                    self._print_header()
        except (ValueError, KeyboardInterrupt):
            print(self.ui.status_indicator('warning', "主題切換取消"))

    def enhance_menu_choice_display(self, choice: str, description: str):
        """增強菜單選擇顯示"""
        choice_text = self.ui.colored_text(f"選擇: {choice}", self.ui.theme_config.primary_color, bold=True)
        desc_text = self.ui.colored_text(description, self.ui.theme_config.info_color)
        print(f"{choice_text} - {desc_text}")

    def show_error_message(self, error_msg: str, details: str = ""):
        """顯示錯誤信息"""
        print(self.ui.status_indicator('error', error_msg))
        if details:
            print(self.ui.colored_text(f"詳情: {details}", 'red', dim=True))

    def show_success_message(self, success_msg: str, details: str = ""):
        """顯示成功信息"""
        print(self.ui.status_indicator('success', success_msg))
        if details:
            print(self.ui.colored_text(f"詳情: {details}", 'green', dim=True))

    def show_warning_message(self, warning_msg: str, details: str = ""):
        """顯示警告信息"""
        print(self.ui.status_indicator('warning', warning_msg))
        if details:
            print(self.ui.colored_text(f"詳情: {details}", 'yellow', dim=True))

# 全局適配器實例
_adapter_instance = None

def get_ui_adapter() -> UIEnhancementAdapter:
    """獲取全局UI適配器實例"""
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = UIEnhancementAdapter()
    return _adapter_instance

def enhance_class(original_class):
    """裝飾器：增強現有類的UI功能"""
    adapter = get_ui_adapter()
    return adapter.enhance_interactive_trader(original_class)

# 便捷函數
def display_results_enhanced(results: Dict[str, Any], title: str = "分析結果"):
    """便捷函數：顯示增強的結果"""
    adapter = get_ui_adapter()
    adapter._enhanced_display_results(results, title)

def show_progress_enhanced(description: str, total: int, update_func=None):
    """便捷函數：顯示增強的進度條"""
    adapter = get_ui_adapter()
    adapter._show_enhanced_progress(description, total, update_func)

def display_table_enhanced(data: List[List[Any]], headers: List[str],
                          title: str = "", highlight_condition=None):
    """便捷函數：顯示增強的表格"""
    adapter = get_ui_adapter()
    adapter._display_enhanced_table(data, headers, title, highlight_condition)
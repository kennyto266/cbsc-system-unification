"""
主菜单界面
======================================

Author: CBSC Quant Team
Version: 1.0.0
"""

from textual.containers import Vertical, Container
from textual.widgets import Header, Footer, Button, Static
from textual.screen import Screen
from typing import TYPE_CHECKING

from services.api_client import APIClient

if TYPE_CHECKING:
    from ..main import TradingApp


class MainScreen(Screen):
    """
    主菜单界面
    """

    # Add screen description for screen readers
    SCREEN_DESCRIPTION = "CBSC量化交易系统主菜单，提供策略管理、回测提交、结果查看和系统配置功能"

    BINDINGS = [
        ("q", "app.quit", "退出"),
        ("1", "switch_strategies", "策略管理"),
        ("2", "switch_backtest", "回测提交"),
        ("3", "switch_results", "结果查看"),
        ("4", "switch_config", "系统配置"),
        ("shift+?", "show_help", "显示帮助"),  # Accessibility: Help shortcut
    ]

    def __init__(self, api_client: APIClient, logger):
        super().__init__()
        self.api_client = api_client
        self.logger = logger

    def compose(self):
        """构建UI布局"""
        yield Header()

        with Vertical(id="main-menu"):
            with Container(id="welcome-container"):
                # Accessibility: Add aria-label for screen readers
                yield Static(
                    "欢迎使用 CBSC 量化交易系统",
                    id="welcome-title",
                    aria_label="系统主标题"
                )
                yield Static(
                    "v2.0 - Textual TUI",
                    id="welcome-subtitle",
                    aria_label="系统版本信息"
                )

            with Container(id="menu-container"):
                yield Static(
                    "请选择功能：",
                    id="menu-title",
                    aria_label="菜单选项提示"
                )
                # Accessibility: Add descriptive labels for all buttons
                yield Button("1. 策略管理", id="strategies-btn", aria_label="打开策略管理界面")
                yield Button("2. 回测提交", id="backtest-btn", aria_label="打开回测提交界面")
                yield Button("3. 结果查看", id="results-btn", aria_label="打开回测结果查看界面")
                yield Button("4. 系统配置", id="config-btn", aria_label="打开系统配置界面")
                yield Static("", id="spacer")
                yield Button("Q. 退出系统", id="quit-btn", aria_label="退出应用程序")

        yield Footer()

    def on_button_pressed(self, event):
        """按钮点击事件"""
        button_id = event.button.id

        if button_id == "strategies-btn":
            from .strategies_screen import StrategyScreen

            self.app.push_screen(StrategyScreen(self.api_client, self.logger))

        elif button_id == "backtest-btn":
            from .backtest_submission_screen import BacktestSubmissionScreen

            self.app.push_screen(BacktestSubmissionScreen(self.api_client))

        elif button_id == "results-btn":
            from .results_screen import ResultsScreen

            self.app.push_screen(ResultsScreen(self.api_client, self.logger))

        elif button_id == "config-btn":
            from .config_screen import ConfigScreen

            self.app.push_screen(ConfigScreen(self.api_client, self.logger))

        elif button_id == "quit-btn":
            import sys

            sys.exit(0)

    def action_switch_strategies(self):
        """切换到策略管理"""
        from .strategies_screen import StrategyScreen

        self.app.push_screen(StrategyScreen(self.api_client, self.logger))

    def action_switch_backtest(self):
        """切换到回测提交"""
        from .backtest_submission_screen import BacktestSubmissionScreen

        self.app.push_screen(BacktestSubmissionScreen(self.api_client))

    def action_switch_results(self):
        """切换到结果查看"""
        from .results_screen import ResultsScreen

        self.app.push_screen(ResultsScreen(self.api_client, self.logger))

    def action_switch_config(self):
        """切换到系统配置"""
        from .config_screen import ConfigScreen

        self.app.push_screen(ConfigScreen(self.api_client, self.logger))

    def action_show_help(self):
        """显示帮助信息"""
        # Accessibility: Provide help for screen reader users
        help_text = """
CBSC量化交易系统 - 键盘快捷键帮助
=====================================

主菜单快捷键:
- 1: 打开策略管理
- 2: 打开回测提交
- 3: 打开结果查看
- 4: 打开系统配置
- Q: 退出系统

通用快捷键:
- Shift+?: 显示此帮助
- Esc: 返回上一级
- Ctrl+C: 退出程序

注意: 所有按钮都可以通过Tab键导航，使用Enter键激活。
"""
        self.app.notify(help_text, title="键盘快捷键帮助")
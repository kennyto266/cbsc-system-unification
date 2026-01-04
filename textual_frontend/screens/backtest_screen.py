"""
回测屏幕（主入口）
======================================

Author: CBSC Quant Team
Version: 1.0.0
"""

from textual.containers import Vertical, Container
from textual.widgets import Header, Footer, Static, Button

from textual.screen import Screen

from services.api_client import APIClient


class BacktestScreen(Screen):
    """
    回测屏幕（主入口）
    """

    # Accessibility: Screen description
    SCREEN_DESCRIPTION = "回测管理主菜单，可以提交回测任务或查看进度"

    BINDINGS = [
        ("q", "app.quit", "退出"),
        ("esc", "app.pop_screen", "返回"),
        ("1", "go_submission", "回测提交"),
        ("2", "go_monitor", "进度监控"),
        ("shift+?", "show_help", "帮助"),  # Accessibility: Help
    ]

    def __init__(self, api_client: APIClient, logger):
        """
        初始化回测屏幕
        """
        super().__init__()
        self.api_client = api_client
        self.logger = logger

    def compose(self):
        """构建UI布局"""
        yield Header()

        with Vertical(id="backtest-menu"):
            with Container(id="backtest-title-container"):
                # Accessibility: Add aria-label
                yield Static(
                    "回测管理",
                    id="backtest-title",
                    aria_label="回测管理菜单标题"
                )

            with Container(id="backtest-options"):
                # Accessibility: Add descriptive labels
                yield Button(
                    "1. 提交回测",
                    id="submission-btn",
                    aria_label="创建并提交新的回测任务"
                )
                yield Button(
                    "2. 监控进度",
                    id="monitor-btn",
                    aria_label="查看运行中回测任务的进度"
                )
                yield Static("", id="spacer")
                yield Button(
                    "返回主菜单",
                    id="return-btn",
                    aria_label="返回系统主菜单"
                )

        yield Footer()

    def on_button_pressed(self, event):
        """按钮点击事件"""
        button_id = event.button.id

        if button_id == "submission-btn":
            from .backtest_submission_screen import BacktestSubmissionScreen

            self.app.push_screen(BacktestSubmissionScreen(self.api_client))

        elif button_id == "monitor-btn":
            from .progress_screen import ProgressScreen

            self.app.push_screen(ProgressScreen(self.api_client, self.logger))

        elif button_id == "return-btn":
            from .main_screen import MainScreen

            self.app.push_screen(MainScreen(self.api_client, self.logger))

    def action_go_submission(self):
        """切换到回测提交"""
        from .backtest_submission_screen import BacktestSubmissionScreen

        self.app.push_screen(BacktestSubmissionScreen(self.api_client))

    def action_go_monitor(self):
        """切换到进度监控"""
        from .progress_screen import ProgressScreen

        self.app.push_screen(ProgressScreen(self.api_client, self.logger))

    def action_show_help(self):
        """显示帮助信息"""
        help_text = """
回测管理帮助
================

快捷键:
- 1: 打开回测提交
- 2: 打开进度监控
- Esc: 返回主菜单
- Shift+?: 显示此帮助

功能说明:
- 提交回测: 创建新的量化策略回测任务
- 监控进度: 查看运行中任务的实时进度
"""
        self.app.notify(help_text, title="回测管理帮助")
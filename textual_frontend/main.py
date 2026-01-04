"""
Textual TUI 界面主文件
======================================

CBSC 量化交易系统的终端用户界面

Author: CBSC Quant Team
Version: 1.0.0
"""

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Header, Footer

from screens.main_screen import MainScreen
from screens.strategies_screen import StrategyScreen
from screens.backtest_screen import BacktestScreen
from screens.results_screen import ResultsScreen
from screens.config_screen import ConfigScreen
from services.api_client import APIClient
from utils.logger import TUILogger


class TradingApp(App):
    """
    CBSC 量化交易系统主应用

    特性：
    - 策略管理（CRUD）
    - 多进程回测提交
    - 实时进度监控
    - 回测结果查看
    - 系统配置管理
    """

    TITLE = "CBSC 量化交易系统"
    SUB_TITLE = "v2.0 - Textual TUI"
    CSS_PATH = "styles.css"

    BINDINGS = [
        ("q", "quit", "退出"),
        ("ctrl+c", "quit", "退出"),
    ]

    def __init__(self):
        super().__init__()
        self.api_client = APIClient()
        self.logger = TUILogger()

    def on_mount(self) -> None:
        """应用挂载时调用"""
        self.logger.info("应用启动")
        self.logger.info(f"API地址: {self.api_client.base_url}")

        # 显示主屏幕
        main_screen = MainScreen(self.api_client, self.logger)
        self.push_screen(main_screen)

    def compose(self) -> ComposeResult:
        """构建UI布局"""
        yield Header()
        yield Container(id="main_content")
        yield Footer()

    async def on_unmount(self) -> None:
        """应用卸载时关闭资源"""
        await self.api_client.close()
        self.logger.info("应用关闭")


# 便捷函数
def run_app():
    """启动 TUI 应用"""
    app = TradingApp()
    app.run()


if __name__ == "__main__":
    run_app()

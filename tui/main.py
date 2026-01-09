# tui/main.py
import asyncio
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from api.client import CBSCAPIClient
from api.websocket_client import CBSCWebSocketClient
from screens.main_menu import MainMenuScreen

class CBSCApp(App):
    """CBSC Textual TUI 主應用"""

    CSS_PATH = "styles/base.css"
    TITLE = "CBSC 量化交易系統"

    def __init__(self):
        super().__init__()
        self.api_client = CBSCAPIClient()
        self.ws_client = CBSCWebSocketClient()

    def compose(self) -> ComposeResult:
        """構建 UI 組件"""
        yield Header()
        yield Footer()

    async def on_mount(self) -> None:
        """應用啟動時"""
        # 顯示主菜單
        await self.push_screen(MainMenuScreen())

        # 連接 WebSocket
        await self.ws_client.connect()

        # 註冊消息處理器
        self.ws_client.on_message(self.handle_ws_message)

        # 啟動監聽
        asyncio.create_task(self.ws_client.listen())

    async def handle_ws_message(self, data: dict):
        """處理 WebSocket 消息"""
        # 可以根據消息類型更新 UI
        pass

    def action_show_main_menu(self):
        """顯示主菜單"""
        self.push_screen(MainMenuScreen())

    def action_show_strategies(self):
        """顯示策略管理"""
        from screens.strategies import StrategyScreen
        self.push_screen(StrategyScreen(self.api_client))

    def action_show_monitor(self):
        """顯示系統監控"""
        from screens.monitor import MonitorScreen
        self.push_screen(MonitorScreen(self.api_client))

    def action_show_logs(self):
        """顯示日誌查看"""
        from screens.logs import LogScreen
        self.push_screen(LogScreen())

    def action_show_database(self):
        """顯示數據庫瀏覽"""
        from screens.database import DatabaseScreen
        self.push_screen(DatabaseScreen(self.api_client))

if __name__ == "__main__":
    app = CBSCApp()
    app.run()

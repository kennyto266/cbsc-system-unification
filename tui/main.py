# tui/main.py
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.containers import Container
from api.client import CBSCAPIClient
from api.websocket_client import CBSCWebSocketClient

class CBSCApp(App):
    """CBSC Textual TUI 主應用"""

    CSS_PATH = "styles/base.css"

    def __init__(self):
        super().__init__()
        self.api_client = CBSCAPIClient()
        self.ws_client = CBSCWebSocketClient()
        self.title = "CBSC 量化交易系統"

    def compose(self) -> ComposeResult:
        """構建 UI 組件"""
        yield Header()
        yield Container(Static("歡迎使用 CBSC TUI", id="welcome"))
        yield Footer()

    async def on_mount(self) -> None:
        """應用啟動時"""
        # 連接 WebSocket
        await self.ws_client.connect()

        # 註冊消息處理器
        self.ws_client.on_message(self.handle_ws_message)

        # 啟動監聽
        asyncio.create_task(self.ws_client.listen())

    async def handle_ws_message(self, data: dict):
        """處理 WebSocket 消息"""
        # 更新 UI
        self.query_one("#welcome", Static).update(
            f"收到更新: {data.get('type', 'unknown')}"
        )

if __name__ == "__main__":
    app = CBSCApp()
    app.run()

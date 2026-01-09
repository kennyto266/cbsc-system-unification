# tui/screens/strategies.py
from textual.screen import Screen
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Header, Footer
from api.client import CBSCAPIClient
from widgets.strategy_list import StrategyList

class StrategyScreen(Screen):
    """策略管理界面"""

    def __init__(self, api_client: CBSCAPIClient):
        super().__init__()
        self.api_client = api_client

    def compose(self):
        """構建 UI"""
        yield Header()
        with Vertical():
            yield StrategyList(self.api_client)
            with Horizontal():
                yield Button("刷新", id="refresh")
                yield Button("創建", id="create")
                yield Button("編輯", id="edit")
                yield Button("刪除", id="delete")
        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """按鈕處理"""
        if event.button.id == "refresh":
            await self.query_one(StrategyList).load_strategies()
            self.app.notify("已刷新", severity="information")

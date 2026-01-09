# tui/screens/monitor.py
import asyncio
from textual.screen import Screen
from textual.widgets import Header, Footer
from api.client import CBSCAPIClient
from widgets.system_metrics import SystemMetrics

class MonitorScreen(Screen):
    """系統監控界面"""

    def __init__(self, api_client: CBSCAPIClient):
        super().__init__()
        self.api_client = api_client

    def compose(self):
        """構建 UI"""
        yield Header()
        yield SystemMetrics()
        yield Footer()

    async def on_mount(self):
        """定時更新"""
        while True:
            await self.query_one(SystemMetrics).update_metrics()
            await asyncio.sleep(5)

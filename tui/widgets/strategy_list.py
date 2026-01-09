# tui/widgets/strategy_list.py
from textual.widgets import DataTable
from api.client import CBSCAPIClient

class StrategyList(DataTable):
    """策略列表表格"""

    def __init__(self, api_client: CBSCAPIClient):
        super().__init__()
        self.api_client = api_client

    async def on_mount(self) -> None:
        """加載策略列表"""
        self.cursor_type = "row"
        self.zebra_stripes = True

        # 添加列
        self.add_columns("ID", "名稱", "狀態", "收益率", "風險")

        # 加載數據
        await self.load_strategies()

    async def load_strategies(self):
        """從 API 加載策略"""
        try:
            strategies = await self.api_client.get_strategies()

            # 清空現有行
            self.clear()

            # 添加數據
            for strategy in strategies:
                self.add_row(
                    str(strategy.get("id")),
                    strategy.get("name", "-"),
                    strategy.get("status", "-"),
                    f"{strategy.get('returns', 0):.2f}%",
                    f"{strategy.get('risk', 0):.2f}"
                )
        except Exception as e:
            self.app.bell()
            self.app.notify(f"加載失敗: {e}", severity="error")

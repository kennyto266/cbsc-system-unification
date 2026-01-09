# tui/widgets/table_browser.py
from textual.widgets import DataTable
from api.client import CBSCAPIClient
from typing import Any, Dict

class TableBrowser(DataTable):
    """數據庫表瀏覽器"""

    def __init__(self, api_client: CBSCAPIClient):
        super().__init__()
        self.api_client = api_client
        self.current_table = None

    async def on_mount(self) -> None:
        """初始化"""
        self.cursor_type = "row"
        self.zebra_stripes = True

    async def load_table(self, table_name: str, limit: int = 100):
        """加載表數據"""
        try:
            self.current_table = table_name
            # 調用 API 獲取表數據
            data = await self.api_client.get(f"/api/database/table/{table_name}", params={"limit": limit})

            # 清空現有行
            self.clear()

            # 添加列
            if data.get("columns"):
                self.add_columns(*data["columns"])

            # 添加數據行
            for row in data.get("rows", []):
                self.add_row(*[str(v) for v in row])

        except Exception as e:
            self.app.bell()
            self.app.notify(f"加載表失敗: {e}", severity="error")

    async def list_tables(self):
        """列出所有表"""
        try:
            tables = await self.api_client.get("/api/database/tables")

            self.clear()
            self.add_columns("表名", "行數", "大小", "最後修改")

            for table in tables:
                self.add_row(
                    table.get("name", "-"),
                    str(table.get("row_count", 0)),
                    table.get("size", "-"),
                    table.get("last_modified", "-")
                )

        except Exception as e:
            self.app.notify(f"獲取表列表失敗: {e}", severity="error")

    async def execute_query(self, query: str):
        """執行 SQL 查詢"""
        try:
            result = await self.api_client.post("/api/database/query", {"query": query})

            self.clear()

            # 添加列
            if result.get("columns"):
                self.add_columns(*result["columns"])

            # 添加數據
            for row in result.get("rows", []):
                self.add_row(*[str(v) if v is not None else "NULL" for v in row])

        except Exception as e:
            self.app.notify(f"查詢失敗: {e}", severity="error")

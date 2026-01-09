# tui/screens/database.py
from textual.screen import Screen
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Header, Footer, Input, TabbedContent, Tab, Pane
from api.client import CBSCAPIClient
from widgets.table_browser import TableBrowser

class DatabaseScreen(Screen):
    """數據庫瀏覽界面"""

    def __init__(self, api_client: CBSCAPIClient):
        super().__init__()
        self.api_client = api_client
        self.table_browser = None

    def compose(self):
        """構建 UI"""
        yield Header()

        with TabbedContent(id="db_tabs"):
            with Tab("表列表", id="tables_tab"):
                with Vertical():
                    yield TableBrowser(self.api_client, id="table_list")
                    with Horizontal():
                        yield Button("刷新", id="refresh_tables")
                        yield Button("查看數據", id="view_data")

            with Tab("SQL 查詢", id="query_tab"):
                with Vertical():
                    yield Input(placeholder="輸入 SQL 查詢...", id="sql_input", password=False)
                    with Horizontal():
                        yield Button("執行", id="execute_query")
                        yield Button("清空", id="clear_query")
                    yield TableBrowser(self.api_client, id="query_result")

        yield Footer()

    def on_mount(self):
        """初始化"""
        # 加載表列表
        table_list = self.query_one("#table_list", TableBrowser)
        self.table_browser = table_list
        self.run_task(table_list.list_tables())

    async def on_button_pressed(self, event: Button.Pressed):
        """按鈕處理"""
        if event.button.id == "refresh_tables":
            table_list = self.query_one("#table_list", TableBrowser)
            await table_list.list_tables()
            self.app.notify("已刷新", severity="information")

        elif event.button.id == "view_data":
            table_list = self.query_one("#table_list", TableBrowser)
            row = table_list.cursor_row
            if row:
                cell = table_list.get_cell(row, 0)
                if cell:
                    table_name = cell.plain
                    self.app.notify(f"加載表: {table_name}", severity="information")
                    await table_list.load_table(table_name)

        elif event.button.id == "execute_query":
            query_input = self.query_one("#sql_input", Input)
            query = query_input.value.strip()

            if query:
                result_browser = self.query_one("#query_result", TableBrowser)
                await result_browser.execute_query(query)
            else:
                self.app.notify("請輸入 SQL 查詢", severity="warning")

        elif event.button.id == "clear_query":
            query_input = self.query_one("#sql_input", Input)
            query_input.value = ""

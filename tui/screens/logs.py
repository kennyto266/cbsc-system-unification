# tui/screens/logs.py
from textual.screen import Screen
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Header, Footer, Input, Select
from widgets.log_viewer import LogViewer

class LogScreen(Screen):
    """日誌查看界面"""

    def __init__(self):
        super().__init__()
        self.log_viewer = None

    def compose(self):
        """構建 UI"""
        yield Header()
        with Vertical():
            # 過濾控制
            with Horizontal():
                yield Input(placeholder="搜索日誌...", id="search_input")
                yield Select(
                    [("DEBUG", "DEBUG"), ("INFO", "INFO"), ("WARNING", "WARNING"),
                     ("ERROR", "ERROR"), ("CRITICAL", "CRITICAL")],
                    value="INFO",
                    id="level_filter"
                )
                yield Button("清空", id="clear_btn")
            # 日誌顯示
            yield LogViewer(id="log_viewer")
        yield Footer()

    def on_mount(self):
        """初始化"""
        self.log_viewer = self.query_one("#log_viewer", LogViewer)

        # 添加測試日誌
        self.log_viewer.add_log("INFO", "日誌查看器已啟動", "LogScreen")
        self.log_viewer.add_log("DEBUG", "系統正在初始化...", "System")
        self.log_viewer.add_log("WARNING", "這是一個警告訊息", "Test")
        self.log_viewer.add_log("ERROR", "這是一個錯誤訊息示例", "Test")

    def on_select_changed(self, event: Select.Changed):
        """過濾等級變化"""
        if event.select.id == "level_filter":
            self.log_viewer.filter_level = event.value

    def on_button_pressed(self, event: Button.Pressed):
        """按鈕處理"""
        if event.button.id == "clear_btn":
            self.log_viewer.clear_logs()

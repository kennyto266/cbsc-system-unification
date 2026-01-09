# tui/widgets/log_viewer.py
from textual.widgets import RichLog
from textual.reactive import reactive
from datetime import datetime

class LogViewer(RichLog):
    """日誌查看器"""

    filter_level = reactive("INFO")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auto_scroll = True

    def on_mount(self):
        """初始化"""
        self.write("=== CBSC 日誌查看器 ===\n", style="bold")

    def add_log(self, level: str, message: str, source: str = "SYSTEM"):
        """添加日誌"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        # 根據等級設置顏色
        style_map = {
            "DEBUG": "dim",
            "INFO": "blue",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold red"
        }

        style = style_map.get(level, "white")

        # 過濾
        if self.should_show(level):
            log_line = f"[{timestamp}] [{level}] [{source}] {message}"
            self.write(log_line, style=style)

    def should_show(self, level: str) -> bool:
        """判斷是否顯示該等級日誌"""
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        try:
            filter_idx = levels.index(self.filter_level)
            log_idx = levels.index(level)
            return log_idx >= filter_idx
        except ValueError:
            return True

    def clear_logs(self):
        """清空日誌"""
        self.clear()
        self.write("=== 日誌已清空 ===\n", style="dim")

    def watch_filter_level(self, old_level: str, new_level: str):
        """過濾等級變化"""
        self.write(f"\n=== 過濾等級: {old_level} → {new_level} ===\n", style="bold yellow")

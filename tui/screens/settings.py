# tui/screens/settings.py
from textual.screen import Screen
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Header, Footer, Input, Select, Switch
from utils.config import Config

class SettingsScreen(Screen):
    """設置界面"""

    def __init__(self):
        super().__init__()
        self.config = Config()

    def compose(self):
        """構建 UI"""
        yield Header()

        with Vertical():
            # API 設置
            yield Input(
                value=self.config.get("api_url"),
                placeholder="API URL",
                id="api_url",
                label="API URL: "
            )

            yield Input(
                value=self.config.get("ws_url"),
                placeholder="WebSocket URL",
                id="ws_url",
                label="WebSocket URL: "
            )

            # 主題設置
            yield Select(
                [("dark", "dark"), ("light", "light")],
                value=self.config.get("theme"),
                id="theme",
                label="主題: "
            )

            # 刷新設置
            yield Switch(
                value=self.config.get("auto_refresh", True),
                label="自動刷新",
                id="auto_refresh"
            )

            # 日誌等級
            yield Select(
                [("DEBUG", "DEBUG"), ("INFO", "INFO"), ("WARNING", "WARNING"), ("ERROR", "ERROR")],
                value=self.config.get("log_level", "INFO"),
                id="log_level",
                label="日誌等級: "
            )

            # 按鈕
            with Horizontal():
                yield Button("保存", id="save_btn", variant="primary")
                yield Button("重置", id="reset_btn")
                yield Button("取消", id="cancel_btn")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed):
        """按鈕處理"""
        if event.button.id == "save_btn":
            self.save_settings()
        elif event.button.id == "reset_btn":
            self.reset_settings()
        elif event.button.id == "cancel_btn":
            self.app.pop_screen()

    def save_settings(self):
        """保存設置"""
        try:
            # API URL
            api_url = self.query_one("#api_url", Input).value
            self.config.set("api_url", api_url)

            # WebSocket URL
            ws_url = self.query_one("#ws_url", Input).value
            self.config.set("ws_url", ws_url)

            # 主題
            theme = self.query_one("#theme", Select).value
            self.config.set("theme", theme)

            # 自動刷新
            auto_refresh = self.query_one("#auto_refresh", Switch).value
            self.config.set("auto_refresh", auto_refresh)

            # 日誌等級
            log_level = self.query_one("#log_level", Select).value
            self.config.set("log_level", log_level)

            self.app.notify("設置已保存", severity="information")
            self.app.pop_screen()

        except Exception as e:
            self.app.notify(f"保存失敗: {e}", severity="error")

    def reset_settings(self):
        """重置設置"""
        if self.config.reset():
            self.app.notify("已重置為默認設置", severity="information")
            # 重新加載界面
            self.app.pop_screen()
            self.app.push_screen(SettingsScreen())
        else:
            self.app.notify("重置失敗", severity="error")

# tui/screens/main_menu.py
from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Header, Footer, Static

class MainMenuScreen(Screen):
    """主菜單界面"""

    def compose(self) -> ComposeResult:
        """構建 UI"""
        yield Header()

        with Vertical():
            # 歡迎標題
            yield Static(
                "CBSC 量化交易系統 - TUI 控制台",
                id="title"
            )
            yield Static("", id="spacer")

            # 菜單選項
            yield Button("📊 策略管理", id="nav_strategies", classes="menu_item")
            yield Button("📈 系統監控", id="nav_monitor", classes="menu_item")
            yield Button("📝 日誌查看", id="nav_logs", classes="menu_item")
            yield Button("🗄️  數據庫瀏覽", id="nav_database", classes="menu_item")
            yield Button("⚙️  設置", id="nav_settings", classes="menu_item")
            yield Button("❌ 退出", id="nav_exit", classes="menu_item")

        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """按鈕處理"""
        button_id = event.button.id

        if button_id == "nav_strategies":
            from screens.strategies import StrategyScreen
            from api.client import CBSCAPIClient
            self.app.push_screen(StrategyScreen(self.app.api_client))

        elif button_id == "nav_monitor":
            from screens.monitor import MonitorScreen
            from api.client import CBSCAPIClient
            self.app.push_screen(MonitorScreen(self.app.api_client))

        elif button_id == "nav_logs":
            from screens.logs import LogScreen
            self.app.push_screen(LogScreen())

        elif button_id == "nav_database":
            from screens.database import DatabaseScreen
            from api.client import CBSCAPIClient
            self.app.push_screen(DatabaseScreen(self.app.api_client))

        elif button_id == "nav_settings":
            from screens.settings import SettingsScreen
            self.app.push_screen(SettingsScreen())

        elif button_id == "nav_exit":
            self.app.exit()

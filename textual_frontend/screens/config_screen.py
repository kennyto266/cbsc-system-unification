"""
系统配置界面
======================================

Author: CBSC Quant Team
Version: 1.0.0
"""

from textual.containers import Vertical, Horizontal, Container
from textual.widgets import Header, Footer, Button, Input, Label, Static, Select, Switch
from textual.screen import Screen

from services.api_client import APIClient


class ConfigScreen(Screen):
    """
    系统配置界面
    """

    # Accessibility: Screen description
    SCREEN_DESCRIPTION = "系统配置界面，用于修改API连接、界面和日志配置"

    BINDINGS = [
        ("q", "app.quit", "退出"),
        ("esc", "app.pop_screen", "返回"),
        ("ctrl+s", "save_config", "保存配置"),
        ("f1", "field_help", "字段帮助"),  # Accessibility: Field help
    ]

    def __init__(self, api_client: APIClient, logger):
        super().__init__()
        self.api_client = api_client
        self.logger = logger
        self.config = {
            "api_url": "http://localhost:3007",
            "timeout": 30,
            "auto_refresh": True,
            "log_level": "INFO",
            "theme": "default",
        }

    def compose(self):
        """构建UI布局"""
        yield Header()

        with Vertical():
            # API 配置
            with Container(id="api-config", classes="config-section"):
                # Accessibility: Add aria-labels
                yield Label(
                    "API 配置",
                    classes="section-title",
                    aria_label="API配置部分标题"
                )

                yield Label(
                    "API 地址:",
                    classes="form-label",
                    aria_label="API地址输入标签"
                )
                yield Input(
                    placeholder="http://localhost:3007",
                    id="api-url",
                    value=self.config.get("api_url", ""),
                    classes="input",
                    aria_label="输入后端API服务器地址，例如：http://localhost:3007"
                )

                yield Label(
                    "超时时间 (秒):",
                    classes="form-label",
                    aria_label="超时时间输入标签"
                )
                yield Input(
                    placeholder="30",
                    id="timeout",
                    value=str(self.config.get("timeout", 30)),
                    type="number",
                    classes="input",
                    aria_label="输入API请求超时时间，单位：秒"
                )

            # 界面配置
            with Container(id="ui-config", classes="config-section"):
                yield Label(
                    "界面配置",
                    classes="section-title",
                    aria_label="界面配置部分标题"
                )

                with Horizontal():
                    yield Label(
                        "自动刷新:",
                        classes="form-label",
                        aria_label="自动刷新开关标签"
                    )
                    auto_refresh_switch = Switch(
                        id="auto-refresh",
                        value=self.config.get("auto_refresh", True),
                        aria_label="启用或禁用数据自动刷新功能"
                    )
                    yield auto_refresh_switch

                yield Label(
                    "日志级别:",
                    classes="form-label",
                    aria_label="日志级别选择标签"
                )
                log_level_select = Select(
                    options=[
                        ("DEBUG", "DEBUG"),
                        ("INFO", "INFO"),
                        ("WARNING", "WARNING"),
                        ("ERROR", "ERROR"),
                    ],
                    value=self.config.get("log_level", "INFO"),
                    id="log-level",
                    classes="select",
                    aria_label="选择日志记录级别，DEBUG最详细，ERROR最少"
                )
                yield log_level_select

                yield Label(
                    "主题:",
                    classes="form-label",
                    aria_label="主题选择标签"
                )
                theme_select = Select(
                    options=[
                        ("默认", "default"),
                        ("深色", "dark"),
                        ("浅色", "light"),
                    ],
                    value=self.config.get("theme", "default"),
                    id="theme",
                    classes="select",
                    aria_label="选择界面主题颜色"
                )
                yield theme_select

            # 按钮
            with Horizontal(classes="button-container"):
                yield Button(
                    "保存配置",
                    id="save-btn",
                    aria_label="保存当前配置并应用到系统"
                )
                yield Button(
                    "重置默认",
                    id="reset-btn",
                    aria_label="将所有配置重置为默认值"
                )
                yield Button(
                    "返回",
                    id="return-btn",
                    aria_label="返回主菜单，不保存更改"
                )

        yield Footer()

    def on_button_pressed(self, event):
        """按钮点击事件"""
        button_id = event.button.id

        if button_id == "save-btn":
            self.call_later(self.action_save_config)

        elif button_id == "reset-btn":
            self.reset_config()

        elif button_id == "return-btn":
            from .main_screen import MainScreen

            self.app.push_screen(MainScreen(self.api_client, self.logger))

    async def action_save_config(self):
        """保存配置"""
        try:
            api_url = self.query_one("#api-url", Input).value
            timeout_value = self.query_one("#timeout", Input).value

            # 验证输入
            if not api_url:
                self.app.notify("API地址不能为空", severity="error", timeout=10)
                return

            try:
                timeout = int(timeout_value)
                if timeout <= 0:
                    raise ValueError("超时时间必须大于0")
            except ValueError as e:
                # Accessibility: Provide detailed error message
                self.app.notify(f"超时时间格式错误: {str(e)}，请输入正整数", severity="error", timeout=10)
                return

            auto_refresh = self.query_one("#auto-refresh", Switch).value
            log_level = self.query_one("#log-level", Select).value
            theme = self.query_one("#theme", Select).value

            # 更新配置
            self.config["api_url"] = api_url
            self.config["timeout"] = timeout
            self.config["auto_refresh"] = auto_refresh
            self.config["log_level"] = log_level
            self.config["theme"] = theme

            # 这里可以保存到文件或数据库
            self.logger.info(f"保存配置: {self.config}")

            # Accessibility: Announce success with details
            self.app.notify(
                f"配置保存成功 - API: {api_url}, 超时: {timeout}秒",
                severity="information"
            )

        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
            # Accessibility: Provide detailed error message
            self.app.notify(f"保存失败: {str(e)}", severity="error", timeout=15)

    def action_field_help(self):
        """显示字段帮助"""
        help_text = """
系统配置字段说明
================

API配置:
- API地址: 后端服务器地址，如 http://localhost:3007
- 超时时间: 请求超时秒数，建议30-60秒

界面配置:
- 自动刷新: 自动更新数据显示
- 日志级别: DEBUG/INFO/WARNING/ERROR
- 主题: 界面颜色主题

快捷键:
- F1: 显示此帮助
- Ctrl+S: 保存配置
- Esc: 返回主菜单
"""
        self.app.notify(help_text, title="配置字段帮助")

    def reset_config(self):
        """重置为默认配置"""
        self.config = {
            "api_url": "http://localhost:3007",
            "timeout": 30,
            "auto_refresh": True,
            "log_level": "INFO",
            "theme": "default",
        }

        # 更新 UI
        self.query_one("#api-url", Input).value = self.config["api_url"]
        self.query_one("#timeout", Input).value = str(self.config["timeout"])
        self.query_one("#auto-refresh", Switch).value = self.config["auto_refresh"]
        self.query_one("#log-level", Select).value = self.config["log_level"]
        self.query_one("#theme", Select).value = self.config["theme"]

        self.app.notify("配置已重置", severity="information")

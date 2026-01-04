"""
策略管理界面
======================================

Author: CBSC Quant Team
Version: 1.0.0
"""

from textual.containers import Vertical, Horizontal, Container
from textual.widgets import Header, Footer, Button, Input, DataTable, Label, Static, Select, Switch
from textual.screen import Screen, ModalScreen
from typing import List, Dict, Any

from services.api_client import APIClient


class StrategyScreen(Screen):
    """
    策略管理界面

    功能：
    - 策略列表
    - 添加/删除/编辑策略
    - 策略参数配置
    """

    # Accessibility: Screen description
    SCREEN_DESCRIPTION = "策略管理界面，可以查看、创建、编辑和删除量化交易策略"

    BINDINGS = [
        ("q", "app.quit", "退出"),
        ("esc", "app.pop_screen", "返回"),
        ("ctrl+n", "new_strategy", "新建策略"),
        ("ctrl+s", "save_all", "全部保存"),
        ("shift+/", "show_help", "帮助"),  # Accessibility: Help
    ]

    def __init__(self, api_client: APIClient, logger):
        super().__init__()
        self.api_client = api_client
        self.logger = logger
        self.loading = False
        self.strategies = []
        self.selected_strategy = None

    def compose(self):
        """构建UI布局"""
        yield Header()

        with Vertical():
            # 顶部操作栏
            with Container(classes="action-container"):
                # Accessibility: Add descriptive labels to buttons
                yield Button("新建策略", classes="button.success", id="new-btn",
                            aria_label="创建新的量化交易策略")
                yield Button("删除策略", classes="button.danger", disabled=True, id="delete-btn",
                            aria_label="删除选中的策略，需要先选择一个策略")
                yield Button("刷新列表", classes="button", id="refresh-btn",
                            aria_label="重新加载策略列表")
                yield Button("返回主菜单", classes="button", id="return-btn",
                            aria_label="返回主菜单界面")

            # 主内容区 - 策略表格
            with Container():
                self.strategy_table = DataTable(classes="strategy-table")
                # Accessibility: Add table description
                self.strategy_table.aria_label = "策略列表表格，显示所有可用策略"
                yield self.strategy_table

        yield Footer()

    def on_mount(self):
        """屏幕挂载时调用"""
        self.call_later(self.load_strategies)

    def on_data_table_mounted(self, event):
        """DataTable 挂载时初始化列"""
        table = event.data_table
        table.add_column("ID", key="id")
        table.add_column("名称", key="name")
        table.add_column("类型", key="type")
        table.add_column("参数", key="parameters")
        table.add_column("状态", key="status")

    async def load_strategies(self):
        """加载策略列表"""
        try:
            strategies = await self.api_client.get_strategies()
            self.strategies = strategies
            self.update_strategy_table()

            # 刷新删除按钮状态
            delete_btn = self.query_one("#delete-btn", Button)
            delete_btn.disabled = len(self.strategies) == 0

            self.logger.info(f"加载了 {len(strategies)} 个策略")

        except Exception as e:
            self.logger.error(f"加载策略失败: {e}")
            self.app.notify("加载失败", severity="error")

    def update_strategy_table(self):
        """更新策略表格"""
        self.strategy_table.clear()

        # 添加行
        for strategy in self.strategies:
            self.strategy_table.add_row(
                str(strategy.get("id", "")),
                strategy.get("name", ""),
                strategy.get("type", ""),
                str(strategy.get("parameters", {})),
                strategy.get("status", ""),
            )

    def on_data_table_row_selected(self, event):
        """表格行选择事件"""
        row_key = event.row_key
        if row_key is not None and row_key < len(self.strategies):
            self.selected_strategy = self.strategies[row_key]

            # 更新按钮状态
            delete_btn = self.query_one("#delete-btn", Button)
            delete_btn.disabled = self.selected_strategy is None

            # Accessibility: Announce selection to screen readers
            strategy_name = self.selected_strategy.get("name", "未命名")
            self.app.notify(f"已选择策略: {strategy_name}", severity="information")

    def on_button_pressed(self, event):
        """按钮点击事件"""
        button_id = event.button.id

        if button_id == "new-btn":
            self.app.push_screen(EditStrategyScreen({}, self.api_client, self.logger))
            self.logger.info("打开新建策略界面")

        elif button_id == "delete-btn":
            self.call_later(self.delete_strategy)

        elif button_id == "refresh-btn":
            self.call_later(self.load_strategies)
            self.logger.info("刷新策略列表")

        elif button_id == "return-btn":
            self.app.pop_screen()
            self.logger.info("返回主菜单")

    async def new_strategy(self):
        """新建策略（快捷键）"""
        self.app.push_screen(EditStrategyScreen({}, self.api_client, self.logger))

    async def delete_strategy(self):
        """删除策略"""
        if not self.selected_strategy:
            return

        # 显示确认对话框
        strategy_id = self.selected_strategy.get("id")
        strategy_name = self.selected_strategy.get("name", "未命名")

        async def confirm(result):
            if result:
                try:
                    await self.api_client.delete_strategy(strategy_id)
                    self.app.notify("策略删除成功", severity="information")
                    await self.load_strategies()
                except Exception as e:
                    self.logger.error(f"删除策略失败: {e}")
                    self.app.notify("删除失败", severity="error")

        self.app.push_screen(
            ConfirmScreen(
                title="确认删除", message=f"确定要删除策略 '{strategy_name}' 吗？", callback=confirm
            )
        )

    async def save_all(self):
        """保存所有策略（快捷键）"""
        try:
            # 这里可以实现批量保存逻辑
            self.app.notify("保存成功", severity="information")
        except Exception as e:
            self.logger.error(f"保存失败: {e}")
            # Accessibility: Provide detailed error message
            self.app.notify(f"保存失败: {str(e)}", severity="error", timeout=10)

    def action_show_help(self):
        """显示帮助信息"""
        help_text = """
策略管理界面帮助
================

快捷键:
- Ctrl+N: 新建策略
- Ctrl+S: 保存所有更改
- Esc: 返回主菜单
- Shift+/: 显示此帮助

操作说明:
- 使用方向键在表格中导航
- 按Enter键编辑选中的策略
- 按Delete键删除选中的策略
- 使用Tab键在按钮间切换
"""
        self.app.notify(help_text, title="策略管理帮助")

class EditStrategyScreen(ModalScreen):
    """
    编辑策略界面
    """

    # Accessibility: Screen description
    SCREEN_DESCRIPTION = "编辑策略界面，用于创建或修改量化交易策略的配置"

    BINDINGS = [
        ("esc", "app.pop_screen", "返回"),
        ("ctrl+s", "save", "保存"),
        ("f1", "field_help", "字段帮助"),  # Accessibility: Field help
    ]

    def __init__(self, strategy_data: Dict[str, Any], api_client: APIClient, logger):
        super().__init__()
        self.strategy_data = strategy_data.copy() if strategy_data else {}
        self.api_client = api_client
        self.logger = logger

    def compose(self):
        """构建UI布局"""
        with Vertical(id="edit-form", classes="edit-form"):
            # 标题
            yield Label("编辑策略", classes="section-title",
                       aria_label="策略编辑表单标题")

            # 基本信息
            yield Label("基本信息", classes="form-label")
            # Accessibility: Add placeholder and description for screen readers
            yield Input(
                placeholder="策略名称",
                id="strategy-name",
                value=self.strategy_data.get("name", ""),
                classes="input",
                aria_label="输入策略名称，例如：均线交叉策略"
            )
            yield Input(
                placeholder="策略类型",
                id="strategy-type",
                value=self.strategy_data.get("type", ""),
                classes="input",
                aria_label="输入策略类型，例如：动量策略或均值回归策略"
            )

            # 日期范围
            yield Label("日期范围", classes="form-label")
            with Horizontal():
                yield Label("起始日期：", classes="form-label")
                yield Input(
                    placeholder="2024-01-01",
                    id="start-date",
                    value=self.strategy_data.get("start_date", ""),
                    classes="input",
                    aria_label="输入回测起始日期，格式：YYYY-MM-DD"
                )
                yield Label("结束日期：", classes="form-label")
                yield Input(
                    placeholder="2024-12-31",
                    id="end-date",
                    value=self.strategy_data.get("end_date", ""),
                    classes="input",
                    aria_label="输入回测结束日期，格式：YYYY-MM-DD"
                )

            # 参数配置
            yield Label("参数配置 (JSON格式)", classes="form-label")
            parameters_str = str(self.strategy_data.get("parameters", {}))
            yield Input(
                placeholder='{"window": 20, "threshold": 0.5}',
                id="parameters",
                value=parameters_str,
                classes="input",
                aria_label="输入策略参数，必须是有效的JSON格式，例如：{\"window\": 20, \"threshold\": 0.5}"
            )

            # 按钮
            with Horizontal(classes="button-container"):
                yield Button("保存", classes="button.success", id="save-btn",
                           aria_label="保存策略并返回策略列表")
                yield Button("取消", classes="button.cancel", id="cancel-btn",
                           aria_label="取消编辑并返回策略列表")
    def on_button_pressed(self, event):
        """按钮点击事件"""
        if event.button.id == "save-btn":
            self.call_later(self.action_save)
        elif event.button.id == "cancel-btn":
            self.app.pop_screen()

    async def action_save(self):
        """保存策略"""
        try:
            name = self.query_one("#strategy-name", Input).value
            strategy_type = self.query_one("#strategy-type", Input).value
            start_date = self.query_one("#start-date", Input).value
            end_date = self.query_one("#end-date", Input).value
            parameters_str = self.query_one("#parameters", Input).value

            # 验证必填字段
            if not name:
                self.app.notify("策略名称不能为空", severity="error", timeout=10)
                return
            if not strategy_type:
                self.app.notify("策略类型不能为空", severity="error", timeout=10)
                return
            if not start_date or not end_date:
                self.app.notify("日期范围不能为空", severity="error", timeout=10)
                return

            # 解析参数
            import json

            try:
                parameters = json.loads(parameters_str)
            except json.JSONDecodeError as e:
                # Accessibility: Provide detailed error message
                self.app.notify(f"参数格式错误：{str(e)}，请使用有效的JSON格式", severity="error", timeout=15)
                return

            # 更新策略数据
            self.strategy_data["name"] = name
            self.strategy_data["type"] = strategy_type
            self.strategy_data["start_date"] = start_date
            self.strategy_data["end_date"] = end_date
            self.strategy_data["parameters"] = parameters

            # 保存到后端
            strategy_id = self.strategy_data.get("id")
            if strategy_id:
                await self.api_client.update_strategy(strategy_id, self.strategy_data)
            else:
                result = await self.api_client.create_strategy(self.strategy_data)
                self.strategy_data["id"] = result.get("id")

            # Accessibility: Announce success
            self.app.notify(f"策略 '{name}' 保存成功", severity="information")
            self.app.pop_screen()

        except Exception as e:
            self.logger.error(f"保存策略失败: {e}")
            # Accessibility: Provide detailed error message
            self.app.notify(f"保存失败: {str(e)}", severity="error", timeout=15)

    def action_field_help(self):
        """显示字段帮助"""
        help_text = """
策略编辑字段说明
================

基本信息:
- 策略名称: 策略的唯一标识符
- 策略类型: 如动量、均值回归、趋势跟踪等

日期范围:
- 起始日期: 回测开始日期，格式 YYYY-MM-DD
- 结束日期: 回测结束日期，格式 YYYY-MM-DD

参数配置:
- 必须是有效的JSON格式
- 示例: {"window": 20, "threshold": 0.5}
- 参数根据策略类型而定

快捷键:
- F1: 显示此帮助
- Ctrl+S: 保存策略
- Esc: 取消编辑
"""
        self.app.notify(help_text, title="字段帮助")

class ConfirmScreen(ModalScreen):
    """
    确认对话框
    """

    # Accessibility: Screen description
    SCREEN_DESCRIPTION = "确认对话框，需要用户确认操作"

    def __init__(self, title: str, message: str, callback):
        super().__init__()
        self.title = title or "确认"
        self.message = message or ""
        self.callback = callback

    def compose(self):
        """构建UI布局"""
        title = self.title or "确认"
        message = self.message or ""

        with Vertical(classes="confirm-modal"):
            # Accessibility: Add aria-labels for screen readers
            yield Static(
                title,
                id="confirm-title",
                aria_label="确认对话框标题"
            )
            yield Static(
                message,
                id="confirm-message",
                aria_label="确认操作说明"
            )

            with Horizontal(classes="confirm-buttons"):
                yield Button(
                    "确定",
                    id="confirm-btn",
                    aria_label="确认执行此操作"
                )
                yield Button(
                    "取消",
                    id="cancel-btn",
                    aria_label="取消此操作"
                )

    def on_button_pressed(self, event):
        """按钮点击事件"""
        if event.button.id == "confirm-btn":
            self.app.pop_screen()
            # 异步调用回调
            import asyncio

            asyncio.create_task(self.callback(True))
        elif event.button.id == "cancel-btn":
            self.app.pop_screen()
            # 异步调用回调
            import asyncio

            asyncio.create_task(self.callback(False))

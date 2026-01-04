"""
结果查看界面
======================================

Author: CBSC Quant Team
Version: 1.0.0
"""

from textual.containers import Vertical, Horizontal, Container
from textual.widgets import Header, Footer, DataTable, Button, Static, Label
from textual.screen import Screen
from typing import List, Dict, Any

from services.api_client import APIClient


class ResultsScreen(Screen):
    """
    结果查看界面
    """

    # Accessibility: Screen description
    SCREEN_DESCRIPTION = "回测结果查看界面，显示已完成的回测任务结果"

    BINDINGS = [
        ("q", "app.quit", "退出"),
        ("esc", "app.pop_screen", "返回"),
        ("r", "refresh", "刷新"),
        ("enter", "view_detail", "查看详情"),  # Accessibility: Quick detail view
        ("shift+?", "show_help", "帮助"),  # Accessibility: Help
    ]

    def __init__(self, api_client: APIClient, logger):
        super().__init__()
        self.api_client = api_client
        self.logger = logger
        self.results = []
        self.selected_result = None

    def compose(self):
        """构建UI布局"""
        yield Header()

        with Vertical():
            # 顶部操作栏
            with Container(classes="action-container"):
                # Accessibility: Add aria-labels
                yield Label(
                    "回测结果列表",
                    classes="section-title",
                    aria_label="回测结果列表标题"
                )
                yield Button(
                    "刷新",
                    id="refresh-btn",
                    aria_label="重新加载回测结果列表"
                )
                yield Button(
                    "查看详情",
                    id="detail-btn",
                    disabled=True,
                    aria_label="查看选中回测结果的详细信息，需要先选择一个结果"
                )
                yield Button(
                    "导出",
                    id="export-btn",
                    disabled=True,
                    aria_label="导出选中的回测结果，需要先选择一个结果"
                )
                yield Button(
                    "返回",
                    id="return-btn",
                    aria_label="返回主菜单"
                )

            # 结果表格
            with Container():
                self.results_table = DataTable(classes="results-table")
                # Accessibility: Add table description
                self.results_table.aria_label = "回测结果表格，显示所有已完成的回测任务"
                yield self.results_table

            # 详情面板（默认隐藏）
            with Container(id="detail-panel", classes="detail-panel hidden"):
                yield Label(
                    "结果详情",
                    id="detail-title",
                    aria_label="回测结果详情标题"
                )
                self.detail_content = Static(
                    "",
                    id="detail-content",
                    aria_label="回测结果详细内容"
                )
                yield self.detail_content

        yield Footer()

    def on_mount(self):
        """屏幕挂载时调用"""
        self.call_later(self.load_results)

    def on_data_table_mounted(self, event):
        """DataTable 挂载时初始化列"""
        table = event.data_table
        table.add_column("任务ID", key="task_id")
        table.add_column("策略", key="strategy")
        table.add_column("开始时间", key="start_time")
        table.add_column("状态", key="status")
        table.add_column("收益率", key="return_rate")
        table.add_column("夏普比率", key="sharpe")

    async def load_results(self):
        """加载回测结果"""
        try:
            # 这里应该从 API 获取结果列表
            # 暂时使用模拟数据
            self.results = [
                {
                    "task_id": "task_001",
                    "strategy": "MA_Crossover",
                    "start_time": "2024-01-01 10:00:00",
                    "status": "completed",
                    "return_rate": "15.3%",
                    "sharpe": "1.85",
                },
                {
                    "task_id": "task_002",
                    "strategy": "RSI_Strategy",
                    "start_time": "2024-01-02 10:00:00",
                    "status": "completed",
                    "return_rate": "8.7%",
                    "sharpe": "1.23",
                },
            ]

            self.update_results_table()
            self.logger.info(f"加载了 {len(self.results)} 个结果")

        except Exception as e:
            self.logger.error(f"加载结果失败: {e}")
            self.app.notify("加载失败", severity="error")

    def update_results_table(self):
        """更新结果表格"""
        self.results_table.clear()

        # 添加行
        for result in self.results:
            self.results_table.add_row(
                result.get("task_id", ""),
                result.get("strategy", ""),
                result.get("start_time", ""),
                result.get("status", ""),
                result.get("return_rate", ""),
                result.get("sharpe", ""),
            )

    def on_data_table_row_selected(self, event):
        """表格行选择事件"""
        row_key = event.row_key
        if row_key is not None and row_key < len(self.results):
            self.selected_result = self.results[row_key]

            # 启用详情和导出按钮
            detail_btn = self.query_one("#detail-btn", Button)
            detail_btn.disabled = False

            export_btn = self.query_one("#export-btn", Button)
            export_btn.disabled = False

            # Accessibility: Announce selection to screen readers
            strategy_name = self.selected_result.get("strategy", "未命名")
            self.app.notify(f"已选择回测结果: {strategy_name}", severity="information")

    def on_button_pressed(self, event):
        """按钮点击事件"""
        button_id = event.button.id

        if button_id == "refresh-btn":
            self.call_later(self.load_results)

        elif button_id == "detail-btn":
            if self.selected_result:
                self.show_detail(self.selected_result)

        elif button_id == "export-btn":
            if self.selected_result:
                self.export_result(self.selected_result)

        elif button_id == "return-btn":
            from .main_screen import MainScreen

            self.app.push_screen(MainScreen(self.api_client, self.logger))

    async def action_refresh(self):
        """刷新结果列表（快捷键）"""
        await self.load_results()

    def show_detail(self, result: Dict[str, Any]):
        """显示结果详情"""
        detail_text = f"""
任务ID: {result.get("task_id", "")}
策略: {result.get("strategy", "")}
开始时间: {result.get("start_time", "")}
状态: {result.get("status", "")}
收益率: {result.get("return_rate", "")}
夏普比率: {result.get("sharpe", "")}
"""
        self.detail_content.update(detail_text)

        # 显示详情面板
        detail_panel = self.query_one("#detail-panel")
        detail_panel.remove_class("hidden")

    def export_result(self, result: Dict[str, Any]):
        """导出结果"""
        # 这里可以实现导出为 JSON、CSV 等格式
        # Accessibility: Announce export action
        task_id = result.get("task_id", "未知")
        self.app.notify(f"导出功能开发中，任务ID: {task_id}", severity="information", timeout=10)

    async def action_view_detail(self):
        """查看详情（快捷键）"""
        if self.selected_result:
            self.show_detail(self.selected_result)
        else:
            # Accessibility: Inform user to select first
            self.app.notify("请先选择一个回测结果", severity="warning", timeout=5)

    def action_show_help(self):
        """显示帮助信息"""
        help_text = """
回测结果查看帮助
==================

快捷键:
- R: 刷新结果列表
- Enter: 查看选中结果的详情
- Esc: 返回主菜单
- Shift+?: 显示此帮助

操作说明:
- 使用方向键在结果列表中导航
- 按Enter键或点击"查看详情"按钮查看详情
- 按E键或点击"导出"按钮导出结果
"""
        self.app.notify(help_text, title="结果查看帮助")
"""
进度监控界面
======================================

Author: CBSC Quant Team
Version: 1.0.0
"""

from textual.containers import Vertical, Horizontal, Container
from textual.widgets import Header, Footer, DataTable, Button, Static, Label, ProgressBar
from textual.screen import Screen
from typing import List, Dict, Any

from services.api_client import APIClient


class ProgressScreen(Screen):
    """
    进度监控界面
    """

    # Accessibility: Screen description
    SCREEN_DESCRIPTION = "回测进度监控界面，实时显示运行中任务的执行进度"

    BINDINGS = [
        ("q", "app.quit", "退出"),
        ("esc", "app.pop_screen", "返回"),
        ("r", "refresh", "刷新"),
        ("shift+?", "show_help", "帮助"),  # Accessibility: Help
    ]

    def __init__(self, api_client: APIClient, logger):
        super().__init__()
        self.api_client = api_client
        self.logger = logger
        self.tasks = []
        self.selected_task = None

    def compose(self):
        """构建UI布局"""
        yield Header()

        with Vertical():
            # 顶部状态栏
            with Container(classes="status-container"):
                # Accessibility: Add aria-labels
                yield Label(
                    "运行中任务",
                    classes="section-title",
                    aria_label="运行中任务计数标题"
                )
                self.task_count = Static(
                    "0 个任务",
                    id="task-count",
                    aria_label="当前运行任务数量"
                )
                yield self.task_count
                yield Button(
                    "刷新",
                    id="refresh-btn",
                    aria_label="重新加载任务列表和进度"
                )
                yield Button(
                    "返回",
                    id="return-btn",
                    aria_label="返回回测管理菜单"
                )

            # 任务列表
            with Container():
                self.tasks_table = DataTable(classes="tasks-table")
                # Accessibility: Add table description
                self.tasks_table.aria_label = "运行中任务表格，显示所有正在执行的回测任务"
                yield self.tasks_table

            # 进度详情
            with Container(id="progress-detail", classes="progress-detail hidden"):
                yield Label(
                    "任务详情",
                    id="detail-title",
                    aria_label="选中任务的详细信息"
                )
                self.progress_bar = ProgressBar(
                    total=100, show_eta=True, show_percentage=True, id="progress-bar"
                )
                # Accessibility: Add label to progress bar
                self.progress_bar.aria_label = "任务执行进度条"
                yield self.progress_bar

                self.progress_status = Static(
                    "",
                    id="progress-status",
                    aria_label="任务进度详细信息"
                )
                yield self.progress_status

        yield Footer()

    def on_mount(self):
        """屏幕挂载时调用"""
        self.call_later(self.load_tasks)

    def on_data_table_mounted(self, event):
        """DataTable 挂载时初始化列"""
        table = event.data_table
        table.add_column("任务ID", key="task_id")
        table.add_column("策略", key="strategy")
        table.add_column("开始时间", key="start_time")
        table.add_column("进度", key="progress")
        table.add_column("状态", key="status")

    async def load_tasks(self):
        """加载任务列表"""
        try:
            # 这里应该从 API 获取任务列表
            # 暂时使用模拟数据
            self.tasks = [
                {
                    "task_id": "task_001",
                    "strategy": "MA_Crossover",
                    "start_time": "2024-01-01 10:00:00",
                    "progress": 75,
                    "status": "running",
                },
                {
                    "task_id": "task_002",
                    "strategy": "RSI_Strategy",
                    "start_time": "2024-01-02 10:00:00",
                    "progress": 30,
                    "status": "running",
                },
            ]

            self.update_tasks_table()
            self.task_count.update(f"{len(self.tasks)} 个任务")
            self.logger.info(f"加载了 {len(self.tasks)} 个任务")

        except Exception as e:
            self.logger.error(f"加载任务失败: {e}")
            self.app.notify("加载失败", severity="error")

    def update_tasks_table(self):
        """更新任务表格"""
        self.tasks_table.clear()

        # 添加行
        for task in self.tasks:
            self.tasks_table.add_row(
                task.get("task_id", ""),
                task.get("strategy", ""),
                task.get("start_time", ""),
                f"{task.get('progress', 0)}%",
                task.get("status", ""),
            )

    def on_data_table_row_selected(self, event):
        """表格行选择事件"""
        row_key = event.row_key
        if row_key is not None and row_key < len(self.tasks):
            self.selected_task = self.tasks[row_key]

            # 更新进度详情
            self.show_progress_detail(self.selected_task)

            # Accessibility: Announce selection to screen readers
            strategy_name = self.selected_task.get("strategy", "未命名")
            progress = self.selected_task.get("progress", 0)
            self.app.notify(f"已选择任务: {strategy_name}，进度: {progress}%", severity="information")

    def on_button_pressed(self, event):
        """按钮点击事件"""
        button_id = event.button.id

        if button_id == "refresh-btn":
            self.call_later(self.load_tasks)

        elif button_id == "return-btn":
            from .backtest_screen import BacktestScreen

            self.app.push_screen(BacktestScreen(self.api_client, self.logger))

    async def action_refresh(self):
        """刷新任务列表（快捷键）"""
        await self.load_tasks()

    def show_progress_detail(self, task: Dict[str, Any]):
        """显示进度详情"""
        # 更新进度条
        self.progress_bar.progress = task.get("progress", 0)

        # 更新状态信息
        status_text = f"""
任务ID: {task.get("task_id", "")}
策略: {task.get("strategy", "")}
开始时间: {task.get("start_time", "")}
进度: {task.get("progress", 0)}%
状态: {task.get("status", "")}
"""
        self.progress_status.update(status_text)

        # 显示进度详情面板
        progress_detail = self.query_one("#progress-detail")
        progress_detail.remove_class("hidden")

    def action_show_help(self):
        """显示帮助信息"""
        help_text = """
进度监控帮助
==============

快捷键:
- R: 刷新任务列表
- Esc: 返回回测管理菜单
- Shift+?: 显示此帮助

操作说明:
- 使用方向键在任务列表中导航
- 选择任务后自动显示进度详情
- 进度条显示完成百分比和预计完成时间
"""
        self.app.notify(help_text, title="进度监控帮助")
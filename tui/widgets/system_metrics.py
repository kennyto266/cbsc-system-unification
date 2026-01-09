# tui/widgets/system_metrics.py
from textual.containers import Horizontal
from textual.widgets import Static, ProgressBar
from textual.reactive import reactive

class SystemMetrics(Horizontal):
    """系統指標顯示"""

    cpu_usage = reactive(0.0)
    memory_usage = reactive(0.0)

    def compose(self):
        yield Static("CPU: ", classes="label")
        yield ProgressBar(total=100, show_eta=False, id="cpu-bar")
        yield Static("0%", id="cpu-text", classes="value")

        yield Static("內存: ", classes="label")
        yield ProgressBar(total=100, show_eta=False, id="mem-bar")
        yield Static("0%", id="mem-text", classes="value")

    def watch_cpu_usage(self, value: float):
        """CPU 使用率變化"""
        self.query_one("#cpu-bar", ProgressBar).advance = value
        self.query_one("#cpu-text", Static).update(f"{value:.1f}%")

    def watch_memory_usage(self, value: float):
        """內存使用率變化"""
        self.query_one("#mem-bar", ProgressBar).advance = value
        self.query_one("#mem-text", Static).update(f"{value:.1f}%")

    async def update_metrics(self):
        """更新系統指標"""
        try:
            status = await self.app.api_client.get_system_status()
            self.cpu_usage = status.get("cpu", 0)
            self.memory_usage = status.get("memory", 0)
        except Exception:
            pass

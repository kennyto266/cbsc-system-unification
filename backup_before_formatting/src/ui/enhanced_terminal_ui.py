#!/usr/bin/env python3
"""
Enhanced Terminal UI System
專業級CLI界面美化系統，實現Phase 5.1的所有要求

核心功能：
1. 增強彩色終端輸出
2. 進度條和狀態顯示
3. 表格格式化輸出
4. ASCII圖表選項
"""

import sys
import os
import time
import json
import math
from typing import Dict, List, Optional, Any, Tuple, Union
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

# 核心UI庫
try:
    from rich.console import Console
    from rich.progress import Progress, TaskID, BarColumn, TextColumn, TimeRemainingColumn, SpinnerColumn
    from rich.table import Table
    from rich.panel import Panel
    from rich.align import Align
    from rich.layout import Layout
    from rich.live import Live
    from rich.text import Text
    from rich.style import Style
    from rich.color import Color
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

import colorama
from colorama import Fore, Back, Style
import tabulate
from tabulate import tabulate

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

class Theme(Enum):
    """界面主題枚舉"""
    DARK = "dark"
    LIGHT = "light"
    PROFESSIONAL = "professional"
    COLORFUL = "colorful"

@dataclass
class UITheme:
    """UI主題配置"""
    name: str
    primary_color: str
    secondary_color: str
    success_color: str
    warning_color: str
    error_color: str
    info_color: str
    background_color: str
    text_color: str
    border_style: str

class EnhancedTerminalUI:
    """增強終端UI系統"""

    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "ui_settings.json"

        # 初始化colorama
        colorama.init()

        # 設置主題
        self.themes = self._init_themes()
        self.current_theme = Theme.DARK
        self.theme_config = self.themes[self.current_theme]

        # 初始化Rich Console（如果可用）
        if RICH_AVAILABLE:
            self.console = Console()
            self.rich_progress = None
        else:
            self.console = None

        # 加載用戶設置
        self._load_settings()

        # ASCII圖表字符集 - 使用ASCII字符避免編碼問題
        self.chart_chars = {
            'block': '#',
            'light_block': '.',
            'medium_block': ':',
            'heavy_block': '@',
            'up': '^',
            'down': 'v',
            'up_triangle': '^',
            'down_triangle': 'v',
            'circle': 'o',
            'empty_circle': 'O',
            'star': '*',
            'dash': '-',
            'pipe': '|',
            'corner': '+',
            'corner_top_right': '+',
            'corner_bottom_left': '+',
            'corner_bottom_right': '+'
        }

        # 進度條配置
        self.progress_active = {}
        self.progress_start_times = {}

    def _init_themes(self) -> Dict[Theme, UITheme]:
        """初始化主題配置"""
        return {
            Theme.DARK: UITheme(
                name="深色主題",
                primary_color="cyan",
                secondary_color="blue",
                success_color="green",
                warning_color="yellow",
                error_color="red",
                info_color="magenta",
                background_color="black",
                text_color="white",
                border_style="double"
            ),
            Theme.LIGHT: UITheme(
                name="淺色主題",
                primary_color="blue",
                secondary_color="cyan",
                success_color="green",
                warning_color="yellow",
                error_color="red",
                info_color="purple",
                background_color="white",
                text_color="black",
                border_style="single"
            ),
            Theme.PROFESSIONAL: UITheme(
                name="專業主題",
                primary_color="blue",
                secondary_color="white",
                success_color="green",
                warning_color="yellow",
                error_color="red",
                info_color="blue",
                background_color="black",
                text_color="white",
                border_style="single"
            ),
            Theme.COLORFUL: UITheme(
                name="多彩主題",
                primary_color="magenta",
                secondary_color="cyan",
                success_color="bright_green",
                warning_color="bright_yellow",
                error_color="bright_red",
                info_color="bright_blue",
                background_color="black",
                text_color="white",
                border_style="rounded"
            )
        }

    def _load_settings(self):
        """加載UI設置"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)

                # 應用主題設置
                theme_name = settings.get('theme', 'dark')
                for theme in Theme:
                    if theme.value == theme_name:
                        self.current_theme = theme
                        self.theme_config = self.themes[theme]
                        break

        except Exception as e:
            print(f"Warning: Failed to load UI settings: {e}")

    def save_settings(self):
        """保存UI設置"""
        try:
            self.config_dir.mkdir(exist_ok=True)
            settings = {
                'theme': self.current_theme.value,
                'last_updated': datetime.now().isoformat()
            }

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"Warning: Failed to save UI settings: {e}")

    def set_theme(self, theme: Theme):
        """設置主題"""
        self.current_theme = theme
        self.theme_config = self.themes[theme]
        self.save_settings()

    # ============= 彩色文本系統 =============

    def get_color_code(self, color_name: str) -> str:
        """獲取顏色代碼"""
        color_map = {
            'red': Fore.RED,
            'green': Fore.GREEN,
            'yellow': Fore.YELLOW,
            'blue': Fore.BLUE,
            'magenta': Fore.MAGENTA,
            'cyan': Fore.CYAN,
            'white': Fore.WHITE,
            'black': Fore.BLACK,
            'bright_red': Fore.LIGHTRED_EX,
            'bright_green': Fore.LIGHTGREEN_EX,
            'bright_yellow': Fore.LIGHTYELLOW_EX,
            'bright_blue': Fore.LIGHTBLUE_EX,
            'bright_magenta': Fore.LIGHTMAGENTA_EX,
            'bright_cyan': Fore.LIGHTCYAN_EX,
            'bright_white': Fore.LIGHTWHITE_EX,
            'reset': Style.RESET_ALL
        }
        return color_map.get(color_name, '')

    def colored_text(self, text: str, color: str = None, bg_color: str = None, bold: bool = False,
                    dim: bool = False, underline: bool = False, blink: bool = False) -> str:
        """獲取彩色文本（增強版）"""
        if color is None:
            color = self.theme_config.text_color

        result = self.get_color_code(color)

        if bg_color:
            bg_color_map = {
                'red': Back.RED,
                'green': Back.GREEN,
                'yellow': Back.YELLOW,
                'blue': Back.BLUE,
                'magenta': Back.MAGENTA,
                'cyan': Back.CYAN,
                'white': Back.WHITE,
                'black': Back.BLACK
            }
            result += bg_color_map.get(bg_color, '')

        if bold:
            result += Style.BRIGHT
        if dim:
            result += Style.DIM
        if underline:
            result += Style.UNDERLINE
        if blink:
            result += Style.BLINK

        result += text + self.get_color_code('reset')

        return result

    def status_indicator(self, status: str, text: str = "") -> str:
        """獲取狀態指示器"""
        # 使用ASCII字符替代Unicode字符以避免編碼問題
        indicators = {
            'success': f"{self.colored_text('[OK]', 'bright_green')} {text}",
            'error': f"{self.colored_text('[ERROR]', 'bright_red')} {text}",
            'warning': f"{self.colored_text('[WARNING]', 'bright_yellow')} {text}",
            'info': f"{self.colored_text('[INFO]', 'bright_blue')} {text}",
            'loading': f"{self.colored_text('[LOADING]', 'cyan')} {text}",
            'complete': f"{self.colored_text('[DONE]', 'green')} {text}",
            'pending': f"{self.colored_text('[PENDING]', 'yellow')} {text}",
            'running': f"{self.colored_text('[RUNNING]', 'cyan')} {text}"
        }
        return indicators.get(status.lower(), f"{self.colored_text('[?]', 'yellow')} {text}")

    def print_header(self, title: str, subtitle: str = "", width: int = 80):
        """打印美化的標題"""
        if RICH_AVAILABLE and self.console:
            # 使用Rich創建漂亮的標題
            panel_content = f"[bold]{title}[/bold]"
            if subtitle:
                panel_content += f"\n[dim]{subtitle}[/dim]"

            panel = Panel(
                panel_content,
                title="香港量化交易系統",
                border_style=self.theme_config.primary_color,
                padding=(1, 2)
            )
            self.console.print(panel)
        else:
            # 使用普通ANSI顏色
            border_char = self.chart_chars['dash']
            border_line = border_char * width

            print()
            print(self.colored_text(border_line, self.theme_config.primary_color))
            print(self.colored_text(f"  {title}", self.theme_config.primary_color, bold=True))
            if subtitle:
                print(self.colored_text(f"  {subtitle}", self.theme_config.secondary_color, dim=True))
            print(self.colored_text(border_line, self.theme_config.primary_color))
            print()

    def print_separator(self, char: str = "-", width: int = 80, color: str = None):
        """打印分隔線"""
        if color is None:
            color = self.theme_config.secondary_color

        line = char * width
        print(self.colored_text(line, color))

    def print_status_bar(self, items: List[Tuple[str, str]], width: int = 80):
        """打印狀態欄"""
        if not items:
            return

        # 計算每個項目的寬度
        item_width = width // len(items)

        status_line = ""
        for i, (status, text) in enumerate(items):
            # 限制文本長度
            truncated_text = text[:item_width-3] + "..." if len(text) > item_width-3 else text
            status_text = self.status_indicator(status, truncated_text)

            status_line += status_text

            if i < len(items) - 1:
                status_line += " │ "

        print(self.colored_text(status_line.ljust(width), self.theme_config.info_color))

    # ============= 進度條系統 =============

    def create_progress_bar(self, total: int, description: str = "Processing",
                           show_eta: bool = True, show_percentage: bool = True) -> str:
        """創建進度條ID"""
        progress_id = f"progress_{len(self.progress_active)}"

        self.progress_active[progress_id] = {
            'total': total,
            'current': 0,
            'description': description,
            'start_time': time.time(),
            'show_eta': show_eta,
            'show_percentage': show_percentage
        }

        return progress_id

    def update_progress(self, progress_id: str, increment: int = 1, description: str = None):
        """更新進度條"""
        if progress_id not in self.progress_active:
            return

        progress = self.progress_active[progress_id]
        progress['current'] = min(progress['current'] + increment, progress['total'])

        if description:
            progress['description'] = description

        self._display_progress(progress_id)

    def _display_progress(self, progress_id: str):
        """顯示進度條"""
        if progress_id not in self.progress_active:
            return

        progress = self.progress_active[progress_id]
        current = progress['current']
        total = progress['total']
        description = progress['description']

        # 計算百分比
        percentage = (current / total) * 100 if total > 0 else 0

        # 計算ETA
        elapsed_time = time.time() - progress['start_time']
        if current > 0 and progress['show_eta']:
            eta_seconds = (elapsed_time / current) * (total - current)
            eta_str = f" ETA: {timedelta(seconds=int(eta_seconds))}"
        else:
            eta_str = ""

        # 創建進度條
        bar_width = 40
        filled_chars = int((percentage / 100) * bar_width)
        empty_chars = bar_width - filled_chars

        bar = (self.chart_chars['block'] * filled_chars +
               self.chart_chars['light_block'] * empty_chars)

        # 格式化輸出
        if progress['show_percentage']:
            progress_text = f"{description}: [{self.colored_text(bar, 'green')}] {percentage:.1f}%{eta_str}"
        else:
            progress_text = f"{description}: [{self.colored_text(bar, 'green')}]{eta_str}"

        # 使用\r回到行首
        print(f"\r{progress_text}", end="", flush=True)

        # 完成時換行
        if current >= total:
            print()
            del self.progress_active[progress_id]

    def progress_context(self, total: int, description: str = "Processing"):
        """進度條上下文管理器"""
        return ProgressBarContext(self, total, description)

    # ============= 表格系統 =============

    def create_table(self, headers: List[str], data: List[List[Any]],
                    tablefmt: str = "grid", show_headers: bool = True,
                    highlight_rows: List[int] = None, highlight_cols: List[int] = None,
                    col_colors: List[str] = None) -> str:
        """創建美化的表格"""
        if not data:
            return "No data to display"

        # 如果指定了行高亮，處理顏色
        if highlight_rows:
            colored_data = []
            for i, row in enumerate(data):
                if i in highlight_rows:
                    colored_row = [self.colored_text(str(cell), self.theme_config.primary_color, bold=True)
                                 for cell in row]
                else:
                    colored_row = [str(cell) for cell in row]
                colored_data.append(colored_row)
            data = colored_data
        else:
            data = [[str(cell) for cell in row] for row in data]

        # 處理列顏色
        if col_colors and highlight_cols is None:
            highlight_cols = list(range(len(col_colors)))

        if highlight_cols:
            for row_idx in range(len(data)):
                for col_idx in highlight_cols:
                    if col_idx < len(data[row_idx]):
                        if col_colors and col_idx < len(col_colors):
                            color = col_colors[col_idx]
                        else:
                            color = self.theme_config.secondary_color
                        data[row_idx][col_idx] = self.colored_text(data[row_idx][col_idx], color)

        # 創建表格
        table = tabulate(
            data,
            headers=headers if show_headers else [],
            tablefmt=tablefmt,
            stralign="center",
            numalign="right"
        )

        return table

    def print_table(self, headers: List[str], data: List[List[Any]],
                   title: str = "", tablefmt: str = "grid", max_rows: int = None,
                   **kwargs):
        """打印表格"""
        if title:
            print(self.colored_text(title, self.theme_config.primary_color, bold=True))
            print()

        # 限制行數
        if max_rows and len(data) > max_rows:
            print(f"Showing {max_rows} of {len(data)} rows:")
            data = data[:max_rows]

        table_str = self.create_table(headers, data, tablefmt=tablefmt, **kwargs)
        print(table_str)

    def paginate_table(self, headers: List[str], data: List[List[Any]],
                      rows_per_page: int = 20, title: str = "", **kwargs):
        """分頁顯示表格"""
        if not data:
            print("No data to display")
            return

        total_rows = len(data)
        total_pages = (total_rows + rows_per_page - 1) // rows_per_page
        current_page = 0

        while current_page < total_pages:
            # 清屏
            os.system('cls' if os.name == 'nt' else 'clear')

            # 計算當前頁的數據範圍
            start_idx = current_page * rows_per_page
            end_idx = min(start_idx + rows_per_page, total_rows)
            page_data = data[start_idx:end_idx]

            # 顯示標題和頁碼
            if title:
                page_title = f"{title} (Page {current_page + 1}/{total_pages})"
                print(self.colored_text(page_title, self.theme_config.primary_color, bold=True))
            else:
                print(self.colored_text(f"Page {current_page + 1}/{total_pages}",
                                      self.theme_config.secondary_color))
            print()

            # 顯示表格
            self.print_table(headers, page_data, **kwargs)

            # 顯示導航選項
            print()
            nav_options = []
            if current_page > 0:
                nav_options.append("P: Previous")
            if current_page < total_pages - 1:
                nav_options.append("N: Next")
            nav_options.extend(["H: Home", "E: End", "Q: Quit"])

            print("Options: " + " | ".join(nav_options))

            # 獲取用戶輸入
            choice = input("Enter choice: ").upper()

            if choice == 'N' and current_page < total_pages - 1:
                current_page += 1
            elif choice == 'P' and current_page > 0:
                current_page -= 1
            elif choice == 'H':
                current_page = 0
            elif choice == 'E':
                current_page = total_pages - 1
            elif choice == 'Q':
                break

    # ============= ASCII圖表系統 =============

    def create_ascii_chart(self, data: List[float], width: int = 60, height: int = 15,
                          title: str = "", show_values: bool = True,
                          chart_type: str = "line") -> str:
        """創建ASCII圖表"""
        if not data:
            return "No data to display"

        if title:
            chart_lines = [self.colored_text(title, self.theme_config.primary_color, bold=True)]
        else:
            chart_lines = []

        # 計算數據範圍
        min_val = min(data)
        max_val = max(data)
        range_val = max_val - min_val

        if range_val == 0:
            range_val = 1  # 避免除零

        # 創建圖表網格
        chart_grid = [[' ' for _ in range(width)] for _ in range(height)]

        # 數據點到圖表坐標的映射
        for i, value in enumerate(data):
            x = int((i / (len(data) - 1)) * (width - 1)) if len(data) > 1 else 0
            y = int(((value - min_val) / range_val) * (height - 1))
            y = height - 1 - y  # 翻轉Y坐標

            if chart_type == "line":
                chart_grid[y][x] = self.chart_chars['circle']
            elif chart_type == "bar":
                for bar_y in range(y, height):
                    chart_grid[bar_y][x] = self.chart_chars['block']
            elif chart_type == "area":
                for area_y in range(y, height):
                    if area_y == y:
                        chart_grid[area_y][x] = self.chart_chars['circle']
                    else:
                        chart_grid[area_y][x] = self.chart_chars['light_block']

        # 添加網格線
        for i in range(height):
            if i % 3 == 0:
                for j in range(width):
                    if chart_grid[i][j] == ' ':
                        chart_grid[i][j] = self.chart_chars['light_block']

        # 構建圖表字符串
        for i, row in enumerate(chart_grid):
            line = ''.join(row)
            # 添加Y軸標籤
            if show_values and i % 3 == 0:
                value = max_val - (i / (height - 1)) * range_val
                label = f"{value:8.2f} "
                chart_lines.append(self.colored_text(label, self.theme_config.info_color) + line)
            else:
                chart_lines.append("         " + line)

        # 添加X軸
        if show_values:
            x_labels = []
            for i in range(0, len(data), max(1, len(data) // 10)):
                label = f"{i:4d}"
                x_pos = int((i / (len(data) - 1)) * (width - 1)) if len(data) > 1 else 0
                # 對齊標籤
                x_labels.append(f"{' ' * x_pos}{label}")

            chart_lines.append("         " + self.chart_chars['dash'] * width)
            if x_labels:
                chart_lines.append("         " + " ".join(x_labels))

        return '\n'.join(chart_lines)

    def create_candlestick_chart(self, ohlc_data: List[Tuple], width: int = 60, height: int = 15,
                                title: str = "") -> str:
        """創建ASCII蠟燭圖"""
        if not ohlc_data:
            return "No OHLC data to display"

        if title:
            chart_lines = [self.colored_text(title, self.theme_config.primary_color, bold=True)]
        else:
            chart_lines = []

        # 提取高低價
        highs = [row[2] for row in ohlc_data]  # High
        lows = [row[3] for row in ohlc_data]   # Low

        min_val = min(lows)
        max_val = max(highs)
        range_val = max_val - min_val

        if range_val == 0:
            range_val = 1

        # 創建圖表網格
        chart_grid = [[' ' for _ in range(width)] for _ in range(height)]

        # 繪製蠟燭
        for i, (open_price, high, low, close_price) in enumerate(ohlc_data):
            x = int((i / (len(ohlc_data) - 1)) * (width - 1)) if len(ohlc_data) > 1 else 0

            # 計算價格對應的Y坐標
            open_y = height - 1 - int(((open_price - min_val) / range_val) * (height - 1))
            close_y = height - 1 - int(((close_price - min_val) / range_val) * (height - 1))
            high_y = height - 1 - int(((high - min_val) / range_val) * (height - 1))
            low_y = height - 1 - int(((low - min_val) / range_val) * (height - 1))

            # 確定顏色（綠色上漲，紅色下跌）
            if close_price >= open_price:
                color_char = self.chart_chars['block']  # 實心表示上漲
            else:
                color_char = self.chart_chars['medium_block']  # 半透明表示下跌

            # 繪製高低線
            for y in range(min(high_y, low_y), max(high_y, low_y) + 1):
                if y < height:
                    chart_grid[y][x] = self.chart_chars['pipe']

            # 繪製開盤收盤價之間的實體
            start_y = min(open_y, close_y)
            end_y = max(open_y, close_y)
            for y in range(start_y, end_y + 1):
                if y < height:
                    chart_grid[y][x] = color_char

        # 轉換為字符串
        for row in chart_grid:
            line = ''.join(row)
            chart_lines.append("    " + line)

        # 添加價格標籤
        chart_lines.insert(1, self.colored_text(f"H: {max_val:.2f}", 'green'))
        chart_lines.append(self.colored_text(f"L: {min_val:.2f}", 'red'))

        return '\n'.join(chart_lines)

    # ============= Rich庫集成（如果可用） =============

    def rich_table(self, headers: List[str], data: List[List[Any]],
                   title: str = "", show_header: bool = True, **kwargs) -> None:
        """使用Rich創建高級表格"""
        if not RICH_AVAILABLE or not self.console:
            # 回退到普通表格
            self.print_table(headers, data, title, **kwargs)
            return

        table = Table(
            title=title if title else None,
            show_header=show_header,
            box=None,
            padding=(0, 1)
        )

        # 添加列
        for header in headers:
            table.add_column(header, justify="center")

        # 添加行
        for row in data:
            table.add_row(*[str(cell) for cell in row])

        self.console.print(table)

    def rich_progress(self, tasks: List[Tuple[str, int]], total: int = None) -> None:
        """使用Rich顯示進度"""
        if not RICH_AVAILABLE or not self.console:
            return

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
        ) as progress:

            task_ids = []
            for description, task_total in tasks:
                task_id = progress.add_task(description, total=task_total)
                task_ids.append(task_id)

            # 這裡需要與實際任務集成
            # 可以通過回調函數來更新進度

    # ============= 系統信息顯示 =============

    def display_system_status(self, system_info: Dict[str, Any]):
        """顯示系統狀態"""
        print(self.colored_text("System Status", 'cyan', bold=True))
        self.print_separator()

        status_items = []

        for key, value in system_info.items():
            if isinstance(value, bool):
                status = 'success' if value else 'error'
                text = f"{key}: {'Enabled' if value else 'Disabled'}"
            elif isinstance(value, (int, float)):
                status = 'info'
                text = f"{key}: {value}"
            else:
                status = 'info'
                text = f"{key}: {str(value)[:50]}"

            status_items.append((status, text))

        self.print_status_bar(status_items)

    def display_performance_metrics(self, metrics: Dict[str, Any]):
        """顯示性能指標"""
        headers = ['Metric', 'Value', 'Status']
        data = []

        for metric, value in metrics.items():
            if isinstance(value, (int, float)):
                # 根據值的大小確定狀態
                if 'sharpe' in metric.lower():
                    status = 'Excellent' if value > 2 else 'Good' if value > 1 else 'Poor'
                    status_color = 'green' if value > 2 else 'yellow' if value > 1 else 'red'
                elif 'drawdown' in metric.lower():
                    status = 'Low Risk' if value < 5 else 'Medium Risk' if value < 10 else 'High Risk'
                    status_color = 'green' if value < 5 else 'yellow' if value < 10 else 'red'
                else:
                    status = 'Normal'
                    status_color = 'blue'

                data.append([metric, f"{value:.3f}", self.colored_text(status, status_color)])
            else:
                data.append([metric, str(value), 'Normal'])

        self.print_table(headers, data, title="Performance Metrics", tablefmt="grid")

    def __del__(self):
        """清理資源"""
        # 重置colorama
        if hasattr(colorama, 'deinit'):
            colorama.deinit()

class ProgressBarContext:
    """進度條上下文管理器"""

    def __init__(self, ui: EnhancedTerminalUI, total: int, description: str):
        self.ui = ui
        self.total = total
        self.description = description
        self.progress_id = None
        self.current = 0

    def __enter__(self):
        self.progress_id = self.ui.create_progress_bar(self.total, self.description)
        return self

    def update(self, increment: int = 1, description: str = None):
        """更新進度"""
        self.current += increment
        if description:
            self.description = description
        self.ui.update_progress(self.progress_id, increment, description)

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 確保進度條完成
        if self.current < self.total:
            self.ui.update_progress(self.progress_id, self.total - self.current)
        return False

# 全局UI實例
_ui_instance = None

def get_ui() -> EnhancedTerminalUI:
    """獲取全局UI實例"""
    global _ui_instance
    if _ui_instance is None:
        _ui_instance = EnhancedTerminalUI()
    return _ui_instance

def colored_text(text: str, color: str = None, **kwargs) -> str:
    """便捷函數：獲取彩色文本"""
    return get_ui().colored_text(text, color, **kwargs)

def status_indicator(status: str, text: str = "") -> str:
    """便捷函數：獲取狀態指示器"""
    return get_ui().status_indicator(status, text)

def print_header(title: str, subtitle: str = "", width: int = 80):
    """便捷函數：打印標題"""
    return get_ui().print_header(title, subtitle, width)

def print_table(headers: List[str], data: List[List[Any]], title: str = "", **kwargs):
    """便捷函數：打印表格"""
    return get_ui().print_table(headers, data, title, **kwargs)
#!/usr / bin / env python3
"""
HTML格式導出器
生成交互式報告，支持響應式設計和圖表集成
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class HTMLExporter:
    """HTML導出器類"""

    def __init__(self, config: Dict):
        self.config = config
        self.template = config.get("template", "professional")
        self.include_css = config.get("include_css", True)
        self.include_javascript = config.get("include_javascript", True)
        self.responsive = config.get("responsive", True)
        self.theme = config.get("theme", "bootstrap")
        self.interactive_charts = config.get("interactive_charts", True)

    def export(self, data: Any, output_path: Path, options: Dict = None) -> bool:
        """
        導出數據到HTML文件

        Args:
            data: 要導出的數據
            output_path: 輸出文件路徑
            options: 導出選項

        Returns:
            bool: 是否成功
        """
        try:
            # 生成HTML內容
            html_content = self._generate_html_content(data, options)

            # 寫入文件
            with open(output_path, "w", encoding="utf - 8") as f:
                f.write(html_content)

            # 複製依賴文件（CSS、JS等）
            if self.include_css or self.include_javascript:
                self._copy_dependencies(output_path.parent)

            file_size = (
                os.path.getsize(output_path) if os.path.exists(output_path) else 0
            )
            logger.info(f"✅ HTML文件導出成功: {output_path} ({file_size} bytes)")
            return True

        except Exception as e:
            logger.error(f"❌ HTML導出失敗: {e}")
            return False

    def _generate_html_content(self, data: Any, options: Dict = None) -> str:
        """生成HTML內容"""
        html = f"""<!DOCTYPE html>
<html lang="zh - CN">
<head>
    <meta charset="UTF - 8">
    <meta name="viewport" content="width = device - width, initial - scale = 1.0">
    <title>量化交易報告</title>
    {self._generate_head_content()}
</head>
<body>
    {self._generate_header()}

    <div class="container - fluid">
        {self._generate_content_sections(data, options)}
    </div>

    {self._generate_footer()}
    {self._generate_javascript()}
</body>
</html>"""
        return html

    def _generate_head_content(self) -> str:
        """生成HTML頭部內容"""
        css_links = ""

        if self.include_css:
            if self.theme == "bootstrap":
                css_links = """
    <link href="https://cdn.jsdelivr.net / npm / bootstrap@5.1.3 / dist / css / bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.datatables.net / 1.13.4 / css / dataTables.bootstrap5.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net / npm / chart.js@3.9.1 / dist / chart.min.css" rel="stylesheet">"""
            else:
                css_links = """
    <link href="assets / css / styles.css" rel="stylesheet">"""

        return f"""
    <link href="https://cdnjs.cloudflare.com / ajax / libs / font - awesome / 6.0.0 / css / all.min.css" rel="stylesheet">
    {css_links}
    <style>
        {self._generate_custom_css()}
    </style>"""

    def _generate_custom_css(self) -> str:
        """生成自定義CSS樣式"""
        return """
        .navbar {{
            background: linear - gradient(135deg, #667eea 0%, #764ba2 100%);
            box - shadow: 0 2px 4px rgba(0,0,0,.1);
        }}

        .navbar - brand {{
            font - weight: bold;
            font - size: 1.5rem;
        }}

        .metric - card {{
            background: white;
            border - radius: 10px;
            box - shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 20px;
            margin - bottom: 20px;
            transition: transform 0.2s;
        }}

        .metric - card:hover {{
            transform: translateY(-2px);
            box - shadow: 0 4px 20px rgba(0,0,0,0.15);
        }}

        .metric - value {{
            font - size: 2rem;
            font - weight: bold;
            color: #4472C4;
        }}

        .metric - label {{
            color: #666;
            font - size: 0.9rem;
            margin - top: 5px;
        }}

        .chart - container {{
            position: relative;
            height: 400px;
            margin - bottom: 30px;
        }}

        .data - table {{
            border - radius: 8px;
            overflow: hidden;
            box - shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

        .section - header {{
            border - left: 4px solid #4472C4;
            padding - left: 15px;
            margin - bottom: 20px;
            margin - top: 30px;
        }}

        .footer {{
            background - color: #f8f9fa;
            padding: 30px 0;
            margin - top: 50px;
            border - top: 1px solid #dee2e6;
        }}

        .positive {{
            color: #28a745;
        }}

        .negative {{
            color: #dc3545;
        }}

        .neutral {{
            color: #6c757d;
        }}

        @media (max - width: 768px) {{
            .metric - value {{
                font - size: 1.5rem;
            }}

            .chart - container {{
                height: 300px;
            }}
        }}
        """

    def _generate_header(self) -> str:
        """生成頁面頭部"""
        return (
            """
    <nav class="navbar navbar - dark">
        <div class="container">
            <span class="navbar - brand">
                <i class="fas fa - chart - line me - 2"></i>
                量化交易報告
            </span>
            <span class="navbar - text text - white">
                <i class="fas fa - clock me - 1"></i>
                生成時間: """
            + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            + """
            </span>
        </div>
    </nav>"""
        )

    def _generate_content_sections(self, data: Any, options: Dict = None) -> str:
        """生成內容區塊"""
        content = ""

        if isinstance(data, dict):
            # 摘要信息
            if "summary" in data:
                content += self._generate_summary_cards(data["summary"])

            # 性能指標
            if "performance_metrics" in data:
                content += self._generate_performance_section(
                    data["performance_metrics"]
                )

            # 交易記錄
            if "trades" in data and not data["trades"].empty:
                content += self._generate_trades_section(data["trades"])

            # 圖表數據
            if (
                self.interactive_charts
                and options
                and options.get("include_charts", True)
            ):
                content += self._generate_charts_section(data)

            # 其他數據
            for key, value in data.items():
                if key not in ["summary", "performance_metrics", "trades", "metadata"]:
                    content += self._generate_data_section(key, value)
        else:
            content += self._generate_simple_data_section(data)

        return content

    def _generate_summary_cards(self, summary: Dict) -> str:
        """生成摘要卡片"""
        if not isinstance(summary, dict):
            return ""

        cards = []
        for key, value in summary.items():
            color_class = self._get_value_color_class(value, key)
            icon_class = self._get_metric_icon(key)

            card = f"""
            <div class="col - md - 3 col - sm - 6 mb - 3">
                <div class="metric - card">
                    <div class="d - flex justify - content - between align - items - center">
                        <div>
                            <div class="metric - value {color_class}">
                                {self._format_value(value, key)}
                            </div>
                            <div class="metric - label">
                                <i class="{icon_class} me - 1"></i>
                                {self._translate_key(key)}
                            </div>
                        </div>
                    </div>
                </div>
            </div>"""
            cards.append(card)

        return f"""
        <div class="row mb - 4">
            <div class="col - 12">
                <h2 class="section - header">
                    <i class="fas fa - tachometer - alt me - 2"></i>策略摘要
                </h2>
            </div>
            {''.join(cards)}
        </div>"""

    def _generate_performance_section(self, performance: Dict) -> str:
        """生成性能指標區塊"""
        if not isinstance(performance, dict):
            return ""

        table_rows = []
        for key, value in performance.items():
            color_class = self._get_value_color_class(value, key)
            table_rows.append(
                f"""
            <tr>
                <td><i class="{self._get_metric_icon(key)} me - 2"></i>{self._translate_key(key)}</td>
                <td class="{color_class} fw - bold">{self._format_value(value, key)}</td>
            </tr>"""
            )

        return f"""
        <div class="row">
            <div class="col - 12">
                <h2 class="section - header">
                    <i class="fas fa - chart - bar me - 2"></i>性能指標
                </h2>
                <div class="card data - table">
                    <div class="card - body">
                        <div class="table - responsive">
                            <table class="table table - hover">
                                <thead class="table - light">
                                    <tr>
                                        <th>指標</th>
                                        <th>數值</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {''.join(table_rows)}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>"""

    def _generate_trades_section(self, trades: pd.DataFrame) -> str:
        """生成交易記錄區塊"""
        if trades.empty:
            return ""

        # 限制顯示的記錄數量
        display_trades = trades.head(100)  # 最多顯示100條

        # 轉換為HTML表格
        table_html = display_trades.to_html(
            classes="table table - striped table - hover",
            table_id="trades - table",
            escape = False,
            index = False,
        )

        return f"""
        <div class="row">
            <div class="col - 12">
                <h2 class="section - header">
                    <i class="fas fa - exchange - alt me - 2"></i>交易記錄
                </h2>
                <div class="card data - table">
                    <div class="card - body">
                        <div class="table - responsive">
                            {table_html}
                        </div>
                        {self._generate_table_script('trades - table')}
                    </div>
                </div>
            </div>
        </div>"""

    def _generate_charts_section(self, data: Dict) -> str:
        """生成圖表區塊"""
        if not self.interactive_charts:
            return ""

        charts = []

        # 資產曲線圖
        if "portfolio_value" in data:
            charts.append(self._create_portfolio_chart(data["portfolio_value"]))

        # 回撤圖
        if "drawdowns" in data:
            charts.append(self._create_drawdown_chart(data["drawdowns"]))

        # 收益分布圖
        if "returns" in data:
            charts.append(self._create_returns_distribution_chart(data["returns"]))

        if not charts:
            return ""

        return f"""
        <div class="row">
            <div class="col - 12">
                <h2 class="section - header">
                    <i class="fas fa - chart - area me - 2"></i>圖表分析
                </h2>
                {''.join(charts)}
            </div>
        </div>"""

    def _create_portfolio_chart(self, portfolio_data) -> str:
        """創建組合價值圖表"""
        return f"""
        <div class="col - lg - 6 mb - 4">
            <div class="card">
                <div class="card - header">
                    <h5><i class="fas fa - chart - line me - 2"></i>組合價值曲線</h5>
                </div>
                <div class="card - body">
                    <div class="chart - container">
                        <canvas id="portfolioChart"></canvas>
                    </div>
                </div>
            </div>
        </div>"""

    def _create_drawdown_chart(self, drawdown_data) -> str:
        """創建回撤圖表"""
        return f"""
        <div class="col - lg - 6 mb - 4">
            <div class="card">
                <div class="card - header">
                    <h5><i class="fas fa - chart - area me - 2"></i>回撤分析</h5>
                </div>
                <div class="card - body">
                    <div class="chart - container">
                        <canvas id="drawdownChart"></canvas>
                    </div>
                </div>
            </div>
        </div>"""

    def _create_returns_distribution_chart(self, returns_data) -> str:
        """創建收益分布圖表"""
        return f"""
        <div class="col - lg - 6 mb - 4">
            <div class="card">
                <div class="card - header">
                    <h5><i class="fas fa - chart - bar me - 2"></i>收益分布</h5>
                </div>
                <div class="card - body">
                    <div class="chart - container">
                        <canvas id="returnsDistributionChart"></canvas>
                    </div>
                </div>
            </div>
        </div>"""

    def _generate_data_section(self, title: str, data: Any) -> str:
        """生成數據區塊"""
        if isinstance(data, pd.DataFrame):
            if not data.empty:
                table_html = data.to_html(
                    classes="table table - striped table - hover", escape = False, index = False
                )
                return f"""
                <div class="row">
                    <div class="col - 12">
                        <h2 class="section - header">
                            <i class="fas fa - table me - 2"></i>{self._translate_key(title)}
                        </h2>
                        <div class="card data - table">
                            <div class="card - body">
                                <div class="table - responsive">
                                    {table_html}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>"""
        else:
            return f"""
            <div class="row">
                <div class="col - 12">
                    <h2 class="section - header">
                        <i class="fas fa - info - circle me - 2"></i>{self._translate_key(title)}
                    </h2>
                    <div class="card">
                        <div class="card - body">
                            <pre>{json.dumps(data, indent = 2, ensure_ascii = False)}</pre>
                        </div>
                    </div>
                </div>
            </div>"""

        return ""

    def _generate_simple_data_section(self, data: Any) -> str:
        """生成簡單數據區塊"""
        return f"""
        <div class="row">
            <div class="col - 12">
                <div class="card">
                    <div class="card - body">
                        <pre>{json.dumps(data, indent = 2, ensure_ascii = False, default = str)}</pre>
                    </div>
                </div>
            </div>
        </div>"""

    def _generate_table_script(self, table_id: str) -> str:
        """生成數據表格腳本"""
        if self.include_javascript:
            return f"""
            <script>
                $(document).ready(function() {{
                    $('#{table_id}').DataTable({{
                        responsive: true,
                        pageLength: 25,
                        lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, "All"]],
                        language: {{
                            url: '//cdn.datatables.net / plug - ins / 1.13.4 / i18n / zh.json'
                        }}
                    }});
                }});
            </script>"""
        return ""

    def _generate_footer(self) -> str:
        """生成頁面尾部"""
        return f"""
    <footer class="footer">
        <div class="container">
            <div class="row">
                <div class="col - md - 6">
                    <h5>量化交易報告</h5>
                    <p>由簡化系統量化交易平台生成</p>
                </div>
                <div class="col - md - 6 text - md - end">
                    <p>
                        <i class="fas fa - calendar me - 1"></i>
                        生成時間: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}
                    </p>
                    <p>
                        <i class="fas fa - code me - 1"></i>
                        版本: 1.0.0
                    </p>
                </div>
            </div>
        </div>
    </footer>"""

    def _generate_javascript(self) -> str:
        """生成JavaScript代碼"""
        if not self.include_javascript:
            return ""

        return """
    <script src="https://code.jquery.com / jquery - 3.6.0.min.js"></script>
    <script src="https://cdn.jsdelivr.net / npm / bootstrap@5.1.3 / dist / js / bootstrap.bundle.min.js"></script>
    <script src="https://cdn.datatables.net / 1.13.4 / js / jquery.dataTables.min.js"></script>
    <script src="https://cdn.datatables.net / 1.13.4 / js / dataTables.bootstrap5.min.js"></script>
    <script src="https://cdn.jsdelivr.net / npm / chart.js@3.9.1 / dist / chart.min.js"></script>
    <script>
        // 初始化圖表
        document.addEventListener('DOMContentLoaded', function() {
            // 這裡可以添加圖表初始化代碼
            initializeCharts();
        });

        function initializeCharts() {
            // 資產曲線圖
            const portfolioCtx = document.getElementById('portfolioChart');
            if (portfolioCtx) {
                // 圖表配置
                const config = {
                    type: 'line',
                    data: {
                        labels: [], // 需要從數據中獲取
                        datasets: [{
                            label: '組合價值',
                            data: [], // 需要從數據中獲取
                            borderColor: '#4472C4',
                            backgroundColor: 'rgba(68, 114, 196, 0.1)',
                            fill: true
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                display: true
                            }
                        }
                    }
                };
                new Chart(portfolioCtx, config);
            }
        }
    </script>"""

    def _get_value_color_class(self, value: Any, key: str) -> str:
        """根據數值獲取顏色類"""
        try:
            num_value = float(value) if isinstance(value, (int, float, str)) else 0

            if "drawdown" in key.lower() or key.lower().endswith("_loss"):
                return "negative"
            elif num_value > 0:
                return "positive"
            elif num_value < 0:
                return "negative"
            else:
                return "neutral"
        except Exception:
            return "neutral"

    def _get_metric_icon(self, key: str) -> str:
        """根據指標獲取圖標"""
        icon_map = {
            "return": "fas fa - chart - line",
            "sharpe": "fas fa - balance - scale",
            "drawdown": "fas fa - arrow - down",
            "volatility": "fas fa - chart - area",
            "win_rate": "fas fa - percentage",
            "trades": "fas fa - exchange - alt",
            "profit": "fas fa - dollar - sign",
            "loss": "fas fa - minus - circle",
        }

        for k, icon in icon_map.items():
            if k in key.lower():
                return icon

        return "fas fa - info - circle"

    def _translate_key(self, key: str) -> str:
        """翻譯鍵名為中文"""
        translations = {
            "total_return": "總回報率",
            "annual_return": "年化回報率",
            "sharpe_ratio": "Sharpe比率",
            "max_drawdown": "最大回撤",
            "volatility": "波動率",
            "win_rate": "勝率",
            "trade_count": "交易次數",
            "profit_factor": "盈利因子",
            "calmar_ratio": "Calmar比率",
            "sortino_ratio": "Sortino比率",
            "trades": "交易記錄",
            "summary": "策略摘要",
            "performance_metrics": "性能指標",
        }

        return translations.get(key, key.replace("_", " ").title())

    def _format_value(self, value: Any, key: str) -> str:
        """格式化數值"""
        try:
            if isinstance(value, float):
                if "rate" in key.lower() or key.lower().endswith("_ratio"):
                    return f"{value:.4f}"
                elif "return" in key.lower():
                    return f"{value:.2%}"
                else:
                    return f"{value:.4f}"
            elif isinstance(value, int):
                return f"{value:,}"
            else:
                return str(value)
        except Exception:
            return str(value)

    def _copy_dependencies(self, output_dir: Path):
        """複製依賴文件"""
        try:
            assets_dir = output_dir / "assets"
            assets_dir.mkdir(exist_ok = True)

            css_dir = assets_dir / "css"
            js_dir = assets_dir / "js"

            css_dir.mkdir(exist_ok = True)
            js_dir.mkdir(exist_ok = True)

            # 這裡可以添加複製自定義CSS和JS文件的邏輯
            logger.debug("依賴文件目錄已創建")

        except Exception as e:
            logger.warning(f"依賴文件複製失敗: {e}")

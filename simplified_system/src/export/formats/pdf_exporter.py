#!/usr / bin / env python3
"""
PDF格式導出器
生成專業的PDF報告，包含圖表、表格和分析結果
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class PDFExporter:
    """PDF導出器類"""

    def __init__(self, config: Dict):
        self.config = config
        self.page_size = config.get("page_size", "A4")
        self.orientation = config.get("orientation", "portrait")
        self.margin = config.get("margin", "1cm")
        self.font_family = config.get("font_family", "Arial")
        self.font_size = config.get("font_size", 10)
        self.include_toc = config.get("include_toc", True)
        self.include_page_numbers = config.get("include_page_numbers", True)

        # 檢查可用的PDF庫
        self.pdf_engine = self._detect_pdf_engine()

    def _detect_pdf_engine(self) -> str:
        """檢測可用的PDF生成引擎"""
        try:
            import weasyprint

            return "weasyprint"
        except ImportError:
            pass

        try:
            import reportlab

            return "reportlab"
        except ImportError:
            pass

        try:
            import pdfkit

            return "pdfkit"
        except ImportError:
            pass

        logger.warning("⚠️ 沒有可用的PDF生成庫，PDF導出功能不可用")
        return None

    def export(self, data: Any, output_path: Path, options: Dict = None) -> bool:
        """
        導出數據到PDF文件

        Args:
            data: 要導出的數據
            output_path: 輸出文件路徑
            options: 導出選項

        Returns:
            bool: 是否成功
        """
        if self.pdf_engine is None:
            logger.error("❌ PDF引擎不可用")
            return False

        try:
            if self.pdf_engine == "weasyprint":
                return self._export_with_weasyprint(data, output_path, options)
            elif self.pdf_engine == "reportlab":
                return self._export_with_reportlab(data, output_path, options)
            elif self.pdf_engine == "pdfkit":
                return self._export_with_pdfkit(data, output_path, options)
            else:
                logger.error(f"❌ 不支持的PDF引擎: {self.pdf_engine}")
                return False

        except Exception as e:
            logger.error(f"❌ PDF導出失敗: {e}")
            return False

    def _export_with_weasyprint(
        self, data: Any, output_path: Path, options: Dict = None
    ) -> bool:
        """使用WeasyPrint導出PDF"""
        try:
            from weasyprint import CSS, HTML
            from weasyprint.text.fonts import FontConfiguration

            # 生成HTML內容
            html_content = self._generate_html_content(data, options)

            # 添加CSS樣式
            css_content = self._generate_css_styles()

            # 創建PDF
            html = HTML(string = html_content)
            css = CSS(string = css_content)
            font_config = FontConfiguration()

            html.write_pdf(str(output_path), stylesheets=[css], font_config = font_config)

            logger.info(f"✅ WeasyPrint PDF導出成功: {output_path}")
            return True

        except Exception as e:
            logger.error(f"❌ WeasyPrint PDF導出失敗: {e}")
            return False

    def _export_with_reportlab(
        self, data: Any, output_path: Path, options: Dict = None
    ) -> bool:
        """使用ReportLab導出PDF"""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4, letter
            from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
            from reportlab.lib.units import inch
            from reportlab.platypus import (
                Paragraph,
                SimpleDocTemplate,
                Spacer,
                Table,
                TableStyle,
            )

            # 創建PDF文檔
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize = A4,
                rightMargin = 72,
                leftMargin = 72,
                topMargin = 72,
                bottomMargin = 18,
            )

            # 獲取樣式
            styles = getSampleStyleSheet()
            story = []

            # 添加標題
            title_style = ParagraphStyle(
                "CustomTitle",
                parent = styles["Heading1"],
                fontSize = 24,
                spaceAfter = 30,
                alignment = 1,  # 居中
            )

            story.append(Paragraph("量化交易報告", title_style))
            story.append(Spacer(1, 20))

            # 添加內容
            story.extend(self._generate_reportlab_content(data, styles))

            # 生成PDF
            doc.build(story)

            logger.info(f"✅ ReportLab PDF導出成功: {output_path}")
            return True

        except Exception as e:
            logger.error(f"❌ ReportLab PDF導出失敗: {e}")
            return False

    def _export_with_pdfkit(
        self, data: Any, output_path: Path, options: Dict = None
    ) -> bool:
        """使用PDFKit導出PDF"""
        try:
            import pdfkit

            # 生成HTML內容
            html_content = self._generate_html_content(data, options)

            # PDFKit選項
            pdf_options = {
                "page - size": self.page_size,
                "orientation": self.orientation,
                "margin - top": self.margin,
                "margin - right": self.margin,
                "margin - bottom": self.margin,
                "margin - left": self.margin,
                "encoding": "UTF - 8",
                "no - outline": None,
                "enable - local - file - access": None,
            }

            # 轉換為PDF
            pdfkit.from_string(html_content, str(output_path), options = pdf_options)

            logger.info(f"✅ PDFKit PDF導出成功: {output_path}")
            return True

        except Exception as e:
            logger.error(f"❌ PDFKit PDF導出失敗: {e}")
            return False

    def _generate_html_content(self, data: Any, options: Dict = None) -> str:
        """生成HTML內容"""
        html = f"""
<!DOCTYPE html>
<html lang="zh - CN">
<head>
    <meta charset="UTF - 8">
    <meta name="viewport" content="width = device - width, initial - scale = 1.0">
    <title>量化交易報告</title>
</head>
<body>
    <div class="container">
        <header>
            <h1>量化交易報告</h1>
            <p class="report - date">生成時間: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}</p>
        </header>

        <main>
            {self._generate_content_sections(data)}
        </main>

        <footer>
            <p>由簡化系統量化交易平台生成</p>
        </footer>
    </div>
</body>
</html>
        """
        return html

    def _generate_css_styles(self) -> str:
        """生成CSS樣式"""
        return f"""
        @page {{
            size: {self.page_size} {self.orientation};
            margin: {self.margin};
        }}

        body {{
            font - family: {self.font_family}, sans - serif;
            font - size: {self.font_size}pt;
            line - height: 1.6;
            color: #333;
            margin: 0;
            padding: 20px;
        }}

        .container {{
            max - width: 100%;
            margin: 0 auto;
        }}

        header {{
            text - align: center;
            margin - bottom: 40px;
            border - bottom: 2px solid #4472C4;
            padding - bottom: 20px;
        }}

        h1 {{
            color: #4472C4;
            margin: 0;
            font - size: 28pt;
        }}

        .report - date {{
            color: #666;
            font - size: 12pt;
            margin - top: 10px;
        }}

        h2 {{
            color: #4472C4;
            border - bottom: 1px solid #ddd;
            padding - bottom: 5px;
            margin - top: 30px;
        }}

        table {{
            width: 100%;
            border - collapse: collapse;
            margin: 20px 0;
        }}

        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text - align: left;
        }}

        th {{
            background - color: #4472C4;
            color: white;
            font - weight: bold;
        }}

        tr:nth - child(even) {{
            background - color: #f9f9f9;
        }}

        .summary - grid {{
            display: grid;
            grid - template - columns: repeat(auto - fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}

        .summary - item {{
            background - color: #f8f9fa;
            padding: 15px;
            border - radius: 5px;
            border - left: 4px solid #4472C4;
        }}

        .summary - label {{
            font - weight: bold;
            color: #666;
            margin - bottom: 5px;
        }}

        .summary - value {{
            font - size: 1.2em;
            color: #333;
        }}

        footer {{
            margin - top: 40px;
            padding - top: 20px;
            border - top: 1px solid #ddd;
            text - align: center;
            color: #666;
            font - size: 10pt;
        }}

        @page {{
            @top - right {{
                content: counter(page);
                font - size: 10pt;
                color: #666;
            }}
        }}
        """

    def _generate_content_sections(self, data: Any) -> str:
        """生成內容區塊"""
        content = ""

        if isinstance(data, dict):
            # 摘要信息
            if "summary" in data:
                content += self._generate_summary_section(data["summary"])

            # 性能指標
            if "performance_metrics" in data:
                content += self._generate_performance_section(
                    data["performance_metrics"]
                )

            # 交易記錄
            if "trades" in data and not data["trades"].empty:
                content += self._generate_trades_section(data["trades"])

            # 其他數據
            for key, value in data.items():
                if key not in ["summary", "performance_metrics", "trades", "metadata"]:
                    content += self._generate_data_section(key, value)

        else:
            content += (
                f"<div class='data - section'><h2>數據</h2><p>{str(data)}</p></div>"
            )

        return content

    def _generate_summary_section(self, summary: Dict) -> str:
        """生成摘要區塊"""
        if not isinstance(summary, dict):
            return ""

        items = []
        for key, value in summary.items():
            items.append(
                f"""
            <div class="summary - item">
                <div class="summary - label">{self._translate_key(key)}</div>
                <div class="summary - value">{self._format_value(value)}</div>
            </div>
            """
            )

        return f"""
        <section>
            <h2>策略摘要</h2>
            <div class="summary - grid">
                {''.join(items)}
            </div>
        </section>
        """

    def _generate_performance_section(self, performance: Dict) -> str:
        """生成性能指標區塊"""
        if not isinstance(performance, dict):
            return ""

        table_rows = []
        for key, value in performance.items():
            table_rows.append(
                f"""
            <tr>
                <td>{self._translate_key(key)}</td>
                <td>{self._format_value(value)}</td>
            </tr>
            """
            )

        return f"""
        <section>
            <h2>性能指標</h2>
            <table>
                <thead>
                    <tr>
                        <th>指標</th>
                        <th>數值</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(table_rows)}
                </tbody>
            </table>
        </section>
        """

    def _generate_trades_section(self, trades: pd.DataFrame) -> str:
        """生成交易記錄區塊"""
        if trades.empty:
            return ""

        # 轉換DataFrame為HTML表格
        table_html = trades.to_html(
            classes="trades - table", table_id="trades", escape = False, index = False
        )

        return f"""
        <section>
            <h2>交易記錄</h2>
            {table_html}
        </section>
        """

    def _generate_data_section(self, title: str, data: Any) -> str:
        """生成數據區塊"""
        if isinstance(data, pd.DataFrame):
            if not data.empty:
                table_html = data.to_html(
                    classes="data - table", escape = False, index = False
                )
                return f"""
                <section>
                    <h2>{self._translate_key(title)}</h2>
                    {table_html}
                </section>
                """
        else:
            return f"""
            <section>
                <h2>{self._translate_key(title)}</h2>
                <p>{str(data)}</p>
            </section>
            """

        return ""

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
        }

        return translations.get(key, key.replace("_", " ").title())

    def _format_value(self, value: Any) -> str:
        """格式化數值"""
        if isinstance(value, float):
            if abs(value) < 1:  # 小於1的數值（如比率）
                return f"{value:.4f}"
            else:  # 大於等於1的數值（如百分比）
                return f"{value:.2%}" if value < 100 else f"{value:.2f}"
        elif isinstance(value, int):
            return f"{value:,}"
        else:
            return str(value)

    def _generate_reportlab_content(self, data: Any, styles) -> List:
        """生成ReportLab內容"""
        content = []

        if isinstance(data, dict):
            # 摘要表格
            if "summary" in data:
                content.extend(
                    self._create_summary_table_reportlab(data["summary"], styles)
                )

            # 性能指標表格
            if "performance_metrics" in data:
                content.extend(
                    self._create_performance_table_reportlab(
                        data["performance_metrics"], styles
                    )
                )

            # 交易記錄表格
            if "trades" in data and not data["trades"].empty:
                content.extend(
                    self._create_trades_table_reportlab(data["trades"], styles)
                )

        return content

    def _create_summary_table_reportlab(self, summary: Dict, styles) -> List:
        """創建摘要表格（ReportLab）"""
        content = []

        # 添加標題
        content.append(Paragraph("策略摘要", styles["Heading2"]))

        # 創建表格數據
        table_data = [["指標", "數值"]]
        for key, value in summary.items():
            table_data.append([self._translate_key(key), self._format_value(value)])

        # 創建表格
        table = Table(table_data)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica - Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8F9FA")),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )

        content.append(table)
        content.append(Spacer(1, 20))

        return content

    def _create_performance_table_reportlab(self, performance: Dict, styles) -> List:
        """創建性能指標表格（ReportLab）"""
        content = []

        # 添加標題
        content.append(Paragraph("性能指標", styles["Heading2"]))

        # 創建表格數據
        table_data = [["指標", "數值"]]
        for key, value in performance.items():
            table_data.append([self._translate_key(key), self._format_value(value)])

        # 創建表格
        table = Table(table_data)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica - Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8F9FA")),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )

        content.append(table)
        content.append(Spacer(1, 20))

        return content

    def _create_trades_table_reportlab(self, trades: pd.DataFrame, styles) -> List:
        """創建交易記錄表格（ReportLab）"""
        content = []

        # 添加標題
        content.append(Paragraph("交易記錄", styles["Heading2"]))

        # 限制顯示的記錄數量
        max_trades = 50
        display_trades = trades.head(max_trades)

        # 轉換DataFrame為表格數據
        table_data = [list(display_trades.columns)]
        for _, row in display_trades.iterrows():
            table_data.append([str(cell) for cell in row])

        # 創建表格
        table = Table(table_data)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica - Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8F9FA")),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )

        content.append(table)
        content.append(Spacer(1, 20))

        return content

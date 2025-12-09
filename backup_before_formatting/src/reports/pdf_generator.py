"""
PDF报告生成器 - 核心模块

基于ReportLab实现专业PDF报告生成，支持：
- 多页报告自动分页
- 动态内容填充
- 响应式布局
- 数据绑定
- 模板系统
"""

from __future__ import annotations

import logging
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from jinja2 import Template
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, inch
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

from .pdf_branding import BrandingManager
from .pdf_charts import ChartManager
from .pdf_templates import ReportTemplates
from .pdf_toc import TableOfContentsManager

# 配置日志
logger = logging.getLogger(__name__)


class PDFReportGenerator:
    """
    PDF报告生成器主类

    提供完整的PDF报告生成功能，包括：
    - 文档创建和管理
    - 页面布局控制
    - 内容动态填充
    - 品牌和样式管理
    """

    # 默认页面大小
    DEFAULT_PAGESIZE = A4

    # 默认页边距
    DEFAULT_MARGIN = {
        "top": 2 * cm,
        "bottom": 2 * cm,
        "left": 2 * cm,
        "right": 2 * cm,
    }

    def __init__(
        self,
        output_path: Union[str, Path],
        title: str = "量化交易分析报告",
        author: str = "HK Quant System",
        pagesize: tuple = DEFAULT_PAGESIZE,
        margin: Optional[Dict[str, float]] = None,
    ):
        """
        初始化PDF报告生成器

        Args:
            output_path: 输出文件路径
            title: 报告标题
            author: 报告作者
            pagesize: 页面大小 (width, height)
            margin: 页边距字典 {'top', 'bottom', 'left', 'right'}
        """
        self.output_path = Path(output_path)
        self.title = title
        self.author = author
        self.pagesize = pagesize
        self.margin = margin or self.DEFAULT_MARGIN.copy()

        # 初始化组件
        self.branding_manager = BrandingManager()
        self.toc_manager = TableOfContentsManager()
        self.chart_manager = ChartManager()
        self.templates = ReportTemplates()

        # 文档和样式
        self.doc: Optional[SimpleDocTemplate] = None
        self.styles = getSampleStyleSheet()
        self.custom_styles: Dict[str, ParagraphStyle] = {}

        # 内容存储
        self.story: List = []
        self.toc_entries: List[Dict] = []

        # 创建文档
        self._create_document()

        # 创建自定义样式
        self._create_custom_styles()

        logger.info(f"PDF报告生成器初始化完成: {self.output_path}")

    def _create_document(self) -> None:
        """创建PDF文档"""
        self.doc = SimpleDocTemplate(
            str(self.output_path),
            pagesize=self.pagesize,
            rightMargin=self.margin["right"],
            leftMargin=self.margin["left"],
            topMargin=self.margin["top"],
            bottomMargin=self.margin["bottom"],
        )
        logger.debug("PDF文档创建完成")

    def _create_custom_styles(self) -> None:
        """创建自定义段落样式"""

        # 报告标题样式
        self.custom_styles["report_title"] = ParagraphStyle(
            "ReportTitle",
            parent=self.styles["Title"],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#2C3E50"),
        )

        # 章节标题样式
        self.custom_styles["chapter_title"] = ParagraphStyle(
            "ChapterTitle",
            parent=self.styles["Heading1"],
            fontSize=18,
            spaceAfter=20,
            spaceBefore=20,
            textColor=colors.HexColor("#34495E"),
            borderWidth=0,
            borderColor=colors.HexColor("#3498DB"),
            borderPadding=10,
        )

        # 子章节标题样式
        self.custom_styles["section_title"] = ParagraphStyle(
            "SectionTitle",
            parent=self.styles["Heading2"],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=12,
            textColor=colors.HexColor("#7F8C8D"),
        )

        # 正文样式
        self.custom_styles["body"] = ParagraphStyle(
            "Body",
            parent=self.styles["Normal"],
            fontSize=11,
            leading=16,
            spaceAfter=6,
            alignment=TA_JUSTIFY,
        )

        # 表格标题样式
        self.custom_styles["table_title"] = ParagraphStyle(
            "TableTitle",
            parent=self.styles["Normal"],
            fontSize=12,
            fontName="Helvetica - Bold",
            spaceAfter=8,
            spaceBefore=8,
            alignment=TA_CENTER,
        )

        # 指标值样式
        self.custom_styles["metric_value"] = ParagraphStyle(
            "MetricValue",
            parent=self.styles["Normal"],
            fontSize=14,
            fontName="Helvetica - Bold",
            textColor=colors.HexColor("#27AE60"),
            alignment=TA_RIGHT,
        )

        # 警告样式
        self.custom_styles["warning"] = ParagraphStyle(
            "Warning",
            parent=self.styles["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#E74C3C"),
            borderWidth=1,
            borderColor=colors.HexColor("#E74C3C"),
            borderPadding=8,
            backColor=colors.HexColor("#FADBD8"),
        )

        logger.debug("自定义样式创建完成")

    def add_cover_page(
        self,
        subtitle: Optional[str] = None,
        date: Optional[datetime] = None,
        logo_path: Optional[Union[str, Path]] = None,
        company_name: str = "香港量化交易系统",
    ) -> None:
        """
        添加封面页

        Args:
            subtitle: 副标题
            date: 报告日期，默认当前时间
            logo_path: Logo文件路径
            company_name: 公司名称
        """
        if date is None:
            date = datetime.now()

        # 添加品牌Logo
        if logo_path and Path(logo_path).exists():
            logo = Image(str(logo_path), width=3 * inch, height=1 * inch)
            logo.hAlign = "CENTER"
            self.story.append(logo)
            self.story.append(Spacer(1, 0.5 * inch))

        # 公司名称
        self.story.append(Paragraph(company_name, self.custom_styles["report_title"]))
        self.story.append(Spacer(1, 0.3 * inch))

        # 报告标题
        self.story.append(Paragraph(self.title, self.custom_styles["report_title"]))
        self.story.append(Spacer(1, 0.3 * inch))

        # 副标题
        if subtitle:
            self.story.append(Paragraph(subtitle, self.custom_styles["section_title"]))
            self.story.append(Spacer(1, 0.5 * inch))

        # 添加水印
        self.branding_manager.add_watermark(self.story, "CONFIDENTIAL", opacity=0.1)
        self.story.append(Spacer(1, 1 * inch))

        # 报告信息
        info_data = [
            ["报告日期:", date.strftime("%Y年 % m月 % d日")],
            ["报告作者:", self.author],
            ["版本:", "v1.0"],
        ]
        info_table = Table(info_data, colWidths=[2 * inch, 3 * inch])
        info_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        self.story.append(info_table)

        # 添加页分隔
        self.story.append(PageBreak())

        logger.info("封面页添加完成")

    def add_executive_summary(
        self,
        data: Dict[str, Any],
        key_metrics: Optional[List[Dict]] = None,
    ) -> None:
        """
        添加执行摘要

        Args:
            data: 摘要数据
            key_metrics: 关键指标列表 [{'name': 'Name', 'value': 'Value', 'change': '+5%'}]
        """
        # 章节标题
        self.add_chapter_title("执行摘要")

        # 摘要文本
        if "summary_text" in data:
            self.story.append(
                Paragraph(data["summary_text"], self.custom_styles["body"])
            )
            self.story.append(Spacer(1, 0.2 * inch))

        # 关键指标
        if key_metrics:
            self.story.append(
                Paragraph("关键指标", self.custom_styles["section_title"])
            )

            # 创建指标表格
            metrics_data = [["指标", "数值", "变化"]] + [
                [m["name"], m["value"], m.get("change", "-")] for m in key_metrics
            ]

            metrics_table = Table(
                metrics_data, colWidths=[2.5 * inch, 1.5 * inch, 1 * inch]
            )
            metrics_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3498DB")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica - Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 12),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#ECF0F1")),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )

            self.story.append(metrics_table)

        self.story.append(Spacer(1, 0.2 * inch))
        logger.info("执行摘要添加完成")

    def add_chapter_title(self, title: str, level: int = 1) -> None:
        """
        添加章节标题

        Args:
            title: 标题文本
            level: 标题级别 (1=章节, 2=子章节)
        """
        if level == 1:
            # 添加到目录
            self.toc_entries.append(
                {
                    "title": title,
                    "level": 1,
                    "page": None,  # 在生成时计算
                }
            )

            # 添加标题
            self.story.append(Paragraph(title, self.custom_styles["chapter_title"]))
        else:
            self.story.append(Paragraph(title, self.custom_styles["section_title"]))

    def add_section_content(
        self,
        title: str,
        content: Union[str, List[Union[str, Dict]]],
        level: int = 2,
    ) -> None:
        """
        添加章节内容

        Args:
            title: 章节标题
            content: 内容（文本或内容块列表）
            level: 标题级别
        """
        # 添加标题
        if level == 2:
            self.toc_entries.append(
                {
                    "title": title,
                    "level": 2,
                    "page": None,
                }
            )

        self.story.append(Paragraph(title, self.custom_styles["section_title"]))

        # 添加内容
        if isinstance(content, str):
            self.story.append(Paragraph(content, self.custom_styles["body"]))
        else:
            for item in content:
                if isinstance(item, str):
                    self.story.append(Paragraph(item, self.custom_styles["body"]))
                elif isinstance(item, dict):
                    self._add_content_block(item)

        self.story.append(Spacer(1, 0.15 * inch))

    def _add_content_block(self, block: Dict[str, Any]) -> None:
        """添加内容块"""
        block_type = block.get("type", "text")

        if block_type == "text":
            self.story.append(Paragraph(block["content"], self.custom_styles["body"]))

        elif block_type == "list":
            for item in block["items"]:
                self.story.append(Paragraph(f"• {item}", self.custom_styles["body"]))

        elif block_type == "warning":
            self.story.append(
                Paragraph(block["content"], self.custom_styles["warning"])
            )

        elif block_type == "table":
            self._add_table(block)

        elif block_type == "chart":
            self._add_chart(block)

    def _add_table(self, table_block: Dict[str, Any]) -> None:
        """添加表格"""
        if "title" in table_block:
            self.story.append(
                Paragraph(table_block["title"], self.custom_styles["table_title"])
            )

        data = table_block["data"]
        col_widths = table_block.get("col_widths", [2 * inch] * len(data[0]))

        table = Table(data, colWidths=col_widths)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3498DB")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica - Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#ECF0F1")),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                ]
            )
        )

        self.story.append(table)
        self.story.append(Spacer(1, 0.1 * inch))

    def _add_chart(self, chart_block: Dict[str, Any]) -> None:
        """添加图表"""
        chart_data = self.chart_manager.create_chart(
            chart_type=chart_block["chart_type"],
            data=chart_block["data"],
            options=chart_block.get("options", {}),
        )

        if chart_data["image_path"]:
            img = Image(chart_data["image_path"])
            # 自适应大小
            img.drawHeight = 4 * inch
            img.drawWidth = 6 * inch
            img.hAlign = "CENTER"
            self.story.append(img)

            # 添加图表标题
            if "title" in chart_block:
                self.story.append(
                    Paragraph(chart_block["title"], self.custom_styles["table_title"])
                )

            self.story.append(Spacer(1, 0.1 * inch))

    def add_page_break(self) -> None:
        """添加分页符"""
        self.story.append(PageBreak())

    def add_table_of_contents(self) -> None:
        """添加目录"""
        self.add_chapter_title("目录", level=1)

        # 生成目录
        toc_html = self.toc_manager.generate_toc_html(self.toc_entries)

        # 将HTML转换为PDF元素
        for entry in self.toc_entries:
            level = entry["level"]
            indent = "  " * (level - 1)
            page_num = entry.get("page", "XX")

            toc_line = f"{indent}{entry['title']} {'.' * (50 - len(indent) - len(entry['title']))} {page_num}"
            self.story.append(Paragraph(toc_line, self.custom_styles["body"]))

        self.story.append(PageBreak())
        logger.info("目录添加完成")

    def generate(
        self,
        clean: bool = True,
        with_toc: bool = True,
    ) -> Path:
        """
        生成PDF报告

        Args:
            clean: 是否清理临时文件
            with_toc: 是否包含目录

        Returns:
            输出文件路径
        """
        if not self.doc:
            raise RuntimeError("文档未初始化")

        try:
            # 构建文档
            if with_toc:
                # 在封面后添加目录
                self.add_table_of_contents()

            # 添加页脚
            self._add_page_footer()

            # 生成PDF
            self.doc.build(
                self.story,
                onFirstPage=self._on_first_page,
                onLaterPages=self._on_later_pages,
            )

            logger.info(f"PDF报告生成完成: {self.output_path}")

            return self.output_path

        except Exception as e:
            logger.error(f"PDF生成失败: {e}")
            raise

    def _on_first_page(self, canvas, doc):
        """首页页面设置"""
        # 添加页眉
        self.branding_manager.add_header(
            canvas, doc, "量化交易分析报告", page_type="first"
        )

        # 添加页脚
        self.branding_manager.add_footer(canvas, doc, page_type="first")

    def _on_later_pages(self, canvas, doc):
        """后续页面设置"""
        # 添加页眉
        self.branding_manager.add_header(canvas, doc, self.title, page_type="later")

        # 添加页脚
        self.branding_manager.add_footer(canvas, doc, page_type="later")

    def _add_page_footer(self) -> None:
        """添加页脚信息"""
        # 可以添加页脚相关内容
        pass

    def use_template(
        self,
        template_name: str,
        data: Dict[str, Any],
    ) -> None:
        """
        使用预定义模板

        Args:
            template_name: 模板名称
            data: 模板数据
        """
        template = self.templates.get_template(template_name)
        if template:
            rendered = template.render(**data)
            self.story.append(Paragraph(rendered, self.custom_styles["body"]))

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        if exc_type is None:
            self.generate()

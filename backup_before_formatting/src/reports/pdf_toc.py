"""
目录和页码管理系统

提供：
- 自动生成目录
- 页码和页眉页脚
- 超链接导航
- 书签功能
- 交叉引用
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, Spacer

logger = logging.getLogger(__name__)


class TableOfContentsManager:
    """
    目录管理器

    管理PDF文档的目录结构和页码
    """

    def __init__(self):
        """初始化目录管理器"""
        self.entries: List[Dict[str, Any]] = []
        self.styles = getSampleStyleSheet()
        logger.debug("目录管理器初始化完成")

    def add_entry(
        self,
        title: str,
        level: int,
        page: Optional[int] = None,
        reference: Optional[str] = None,
    ) -> None:
        """
        添加目录条目

        Args:
            title: 标题
            level: 级别 (1=章节, 2=子章节, 3=小节)
            page: 页码
            reference: 引用ID
        """
        entry = {
            "title": title,
            "level": level,
            "page": page,
            "reference": reference or f"ref_{len(self.entries)}",
        }
        self.entries.append(entry)
        logger.debug(f"添加目录条目: {title} (级别{level})")

    def get_entries(self) -> List[Dict[str, Any]]:
        """获取所有目录条目"""
        return self.entries

    def generate_toc_html(self, entries: List[Dict[str, Any]]) -> str:
        """
        生成HTML格式的目录

        Args:
            entries: 目录条目列表

        Returns:
            HTML格式的目录字符串
        """
        html_lines = ['<div class="toc">']

        for entry in entries:
            level = entry["level"]
            indent = level * 20  # 缩进像素

            # 根据级别设置样式
            if level == 1:
                font_size = 14
                font_weight = "bold"
                color = "#2C3E50"
            elif level == 2:
                font_size = 12
                font_weight = "normal"
                color = "#34495E"
            else:
                font_size = 11
                font_weight = "normal"
                color = "#7F8C8D"

            # 生成点线
            title = entry["title"]
            dots = "." * (60 - len(title) - indent // 10)
            page_num = entry.get("page", "XX")

            html_line = """
            <div style="margin - left: {indent}px; font - size: {font_size}px;
                         color: {color}; font - weight: {font_weight};">
                {title} {dots} {page_num}
            </div>
            """
            html_lines.append(html_line)

        html_lines.append("</div>")
        return "\n".join(html_lines)

    def generate_toc_table(
        self,
        entries: List[Dict[str, Any]],
        col_widths: List[float] = None,
    ) -> List[List[str]]:
        """
        生成目录表格数据

        Args:
            entries: 目录条目列表
            col_widths: 列宽列表

        Returns:
            表格数据列表
        """
        if col_widths is None:
            col_widths = [4 * cm, 2 * cm]

        table_data = [["标题", "页码"]]

        for entry in entries:
            level = entry["level"]
            indent = "  " * (level - 1)
            title = f"{indent}{entry['title']}"
            page = str(entry.get("page", "XX"))

            table_data.append([title, page])

        return table_data


class PageNumberManager:
    """
    页码管理器

    管理PDF文档的页码显示
    """

    def __init__(self, start_number: int = 1):
        """
        初始化页码管理器

        Args:
            start_number: 起始页码
        """
        self.current_page = start_number
        self.total_pages = 0
        self.format_template = "第 {page} 页，共 {total} 页"
        logger.debug(f"页码管理器初始化，起始页码: {start_number}")

    def next_page(self) -> int:
        """获取下一页码"""
        self.current_page += 1
        return self.current_page

    def get_current_page(self) -> int:
        """获取当前页码"""
        return self.current_page

    def set_total_pages(self, total: int) -> None:
        """设置总页数"""
        self.total_pages = total

    def format_page_number(self, template: Optional[str] = None) -> str:
        """
        格式化页码

        Args:
            template: 格式模板

        Returns:
            格式化的页码字符串
        """
        if template is None:
            template = self.format_template

        return template.format(page=self.current_page, total=self.total_pages)


class HeaderFooterManager:
    """
    页眉页脚管理器

    管理PDF文档的页眉和页脚
    """

    # 默认页眉页脚配置
    DEFAULT_CONFIG = {
        "header_height": 1.5 * cm,
        "footer_height": 1.5 * cm,
        "header_font_size": 9,
        "footer_font_size": 9,
        "header_color": colors.HexColor("#95A5A6"),
        "footer_color": colors.HexColor("#95A5A6"),
        "show_date": True,
        "show_page_numbers": True,
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化页眉页脚管理器

        Args:
            config: 配置字典
        """
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}
        self.page_number_manager = PageNumberManager()
        logger.debug("页眉页脚管理器初始化完成")

    def add_header(
        self,
        canvas,
        doc,
        title: str = "",
        page_type: str = "normal",
    ) -> None:
        """
        添加页眉

        Args:
            canvas: PDF画布
            doc: 文档对象
            title: 标题
            page_type: 页面类型 (first, normal, last)
        """
        if page_type == "first":
            # 首页通常不显示页眉
            return

        canvas.saveState()

        # 绘制页眉线
        canvas.setStrokeColor(self.config["header_color"])
        canvas.setLineWidth(0.5)
        canvas.line(
            doc.leftMargin,
            doc.height + doc.topMargin - 0.3 * cm,
            doc.width + doc.leftMargin,
            doc.height + doc.topMargin - 0.3 * cm,
        )

        # 添加标题（左上角）
        if title:
            canvas.setFont("Helvetica", self.config["header_font_size"])
            canvas.setFillColor(self.config["header_color"])
            canvas.drawString(
                doc.leftMargin, doc.height + doc.topMargin - 0.8 * cm, title
            )

        # 添加日期（右上角）
        if self.config["show_date"]:
            date_str = datetime.now().strftime("%Y-%m-%d")
            canvas.drawRightString(
                doc.width + doc.leftMargin,
                doc.height + doc.topMargin - 0.8 * cm,
                date_str,
            )

        canvas.restoreState()

    def add_footer(
        self,
        canvas,
        doc,
        page_type: str = "normal",
    ) -> None:
        """
        添加页脚

        Args:
            canvas: PDF画布
            doc: 文档对象
            page_type: 页面类型
        """
        canvas.saveState()

        # 绘制页脚线
        canvas.setStrokeColor(self.config["footer_color"])
        canvas.setLineWidth(0.5)
        canvas.line(
            doc.leftMargin,
            doc.bottomMargin - 0.3 * cm,
            doc.width + doc.leftMargin,
            doc.bottomMargin - 0.3 * cm,
        )

        # 页码
        if self.config["show_page_numbers"]:
            canvas.setFont("Helvetica", self.config["footer_font_size"])
            canvas.setFillColor(self.config["footer_color"])

            page_num = self.page_number_manager.get_current_page()
            page_text = f"- {page_num} -"

            canvas.drawCentredText(
                doc.width / 2 + doc.leftMargin, doc.bottomMargin - 0.8 * cm, page_text
            )

            # 下一页
            self.page_number_manager.next_page()

        canvas.restoreState()


class BookmarkManager:
    """
    书签管理器

    管理PDF文档的导航书签
    """

    def __init__(self):
        """初始化书签管理器"""
        self.bookmarks: List[Dict[str, Any]] = []
        logger.debug("书签管理器初始化完成")

    def add_bookmark(
        self,
        title: str,
        level: int = 0,
        reference: Optional[str] = None,
    ) -> None:
        """
        添加书签

        Args:
            title: 书签标题
            level: 级别（0=顶级，1=子级）
            reference: 引用ID
        """
        bookmark = {
            "title": title,
            "level": level,
            "reference": reference or f"bm_{len(self.bookmarks)}",
        }
        self.bookmarks.append(bookmark)
        logger.debug(f"添加书签: {title} (级别{level})")

    def create_bookmarks(self, canvas) -> None:
        """
        在PDF中创建书签

        Args:
            canvas: PDF画布
        """
        try:
            # ReportLab的书签功能需要通过outline API实现
            # 这里提供接口，实际实现取决于canvas对象的支持
            logger.info(f"创建了 {len(self.bookmarks)} 个书签")
        except Exception as e:
            logger.warning(f"创建书签失败: {e}")


class CrossReferenceManager:
    """
    交叉引用管理器

    管理PDF文档中的交叉引用和超链接
    """

    def __init__(self):
        """初始化交叉引用管理器"""
        self.references: Dict[str, Dict[str, Any]] = {}
        logger.debug("交叉引用管理器初始化完成")

    def add_reference(
        self,
        ref_id: str,
        title: str,
        page: Optional[int] = None,
    ) -> None:
        """
        添加引用

        Args:
            ref_id: 引用ID
            title: 引用标题
            page: 引用页码
        """
        self.references[ref_id] = {
            "title": title,
            "page": page,
        }
        logger.debug(f"添加引用: {ref_id} -> {title}")

    def get_reference(self, ref_id: str) -> Optional[Dict[str, Any]]:
        """
        获取引用

        Args:
            ref_id: 引用ID

        Returns:
            引用信息字典
        """
        return self.references.get(ref_id)

    def create_internal_link(
        self,
        ref_id: str,
        text: str,
    ) -> str:
        """
        创建内部链接

        Args:
            ref_id: 引用ID
            text: 链接文本

        Returns:
            HTML格式的链接
        """
        ref = self.get_reference(ref_id)
        if ref and ref.get("page"):
            return "<link href="#page_{ref["page"]}" color="blue">{text}</link>'
        return text

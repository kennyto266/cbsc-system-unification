"""
品牌和水印管理系统

提供：
- 公司Logo添加
- 品牌色彩管理
- 水印背景
- 报告标识
- 版本信息
"""

from __future__ import annotations

import logging
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, inch
from reportlab.pdfgen import canvas
from reportlab.platypus import Image as RLImage
from reportlab.platypus import Paragraph

logger = logging.getLogger(__name__)


class BrandingManager:
    """
    品牌管理器

    管理PDF报告的品牌元素，包括Logo、颜色、样式等
    """

    # 品牌色彩定义
    BRAND_COLORS = {
        "primary": colors.HexColor("#2C3E50"),  # 深蓝灰
        "secondary": colors.HexColor("#3498DB"),  # 亮蓝
        "accent": colors.HexColor("#E74C3C"),  # 红色
        "success": colors.HexColor("#27AE60"),  # 绿色
        "warning": colors.HexColor("#F39C12"),  # 橙色
        "info": colors.HexColor("#1ABC9C"),  # 青色
        "light": colors.HexColor("#ECF0F1"),  # 浅灰
        "dark": colors.HexColor("#34495E"),  # 深灰
        "white": colors.white,
        "black": colors.black,
    }

    # 默认品牌配置
    DEFAULT_CONFIG = {
        "company_name": "香港量化交易系统",
        "company_name_en": "HK Quant Trading System",
        "logo_path": None,
        "primary_color": "primary",
        "secondary_color": "secondary",
        "accent_color": "accent",
        "show_logo_on_cover": True,
        "show_logo_on_every_page": False,
        "show_company_name_on_cover": True,
        "show_company_name_on_header": True,
    }

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        logo_path: Optional[Union[str, Path]] = None,
    ):
        """
        初始化品牌管理器

        Args:
            config: 品牌配置
            logo_path: Logo文件路径
        """
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}
        self.logo_path = Path(logo_path) if logo_path else None
        self.logo_loaded = False
        self.logo_image = None

        # 尝试加载Logo
        if self.logo_path and self.logo_path.exists():
            self._load_logo()

        logger.info("品牌管理器初始化完成")

    def _load_logo(self) -> None:
        """加载Logo图像"""
        try:
            self.logo_image = RLImage(str(self.logo_path))
            self.logo_loaded = True
            logger.info(f"Logo加载成功: {self.logo_path}")
        except Exception as e:
            logger.warning(f"Logo加载失败: {e}")
            self.logo_loaded = False

    def get_color(self, color_name: str) -> colors.Color:
        """
        获取品牌颜色

        Args:
            color_name: 颜色名称

        Returns:
            颜色对象
        """
        return self.BRAND_COLORS.get(color_name, self.BRAND_COLORS["primary"])

    def add_logo(
        self,
        canvas,
        x: float,
        y: float,
        width: float = 2 * inch,
        height: float = 0.5 * inch,
    ) -> None:
        """
        在指定位置添加Logo

        Args:
            canvas: PDF画布
            x: X坐标
            y: Y坐标
            width: 宽度
            height: 高度
        """
        if not self.logo_loaded or not self.logo_image:
            logger.warning("Logo未加载，无法添加")
            return

        try:
            canvas.drawImage(
                str(self.logo_path),
                x,
                y,
                width=width,
                height=height,
                preserveAspectRatio=True,
                mask="auto",
            )
            logger.debug(f"Logo已添加到位置 ({x}, {y})")
        except Exception as e:
            logger.error(f"添加Logo失败: {e}")

    def add_company_name(
        self,
        canvas,
        x: float,
        y: float,
        fontsize: int = 16,
        color_name: str = "primary",
    ) -> None:
        """
        添加公司名称

        Args:
            canvas: PDF画布
            x: X坐标
            y: Y坐标
            fontsize: 字体大小
            color_name: 颜色名称
        """
        canvas.setFont("Helvetica - Bold", fontsize)
        canvas.setFillColor(self.get_color(color_name))
        canvas.drawString(x, y, self.config["company_name"])
        logger.debug(f"公司名称已添加: {self.config['company_name']}")

    def add_watermark(
        self,
        story,
        text: str = "CONFIDENTIAL",
        opacity: float = 0.1,
        angle: float = 45,
        fontsize: int = 60,
    ) -> None:
        """
        添加水印

        Args:
            story: 故事流列表
            text: 水印文本
            opacity: 透明度 (0 - 1)
            angle: 旋转角度
            fontsize: 字体大小
        """
        from io import BytesIO

        from reportlab.pdfgen import canvas as pdfcanvas
        from reportlab.platypus import KeepTogether

        # 创建临时画布
        buffer = BytesIO()
        watermark_canvas = pdfcanvas.Canvas(buffer, pagesize=A4)

        # 设置水印样式
        watermark_canvas.setFont("Helvetica - Bold", fontsize)
        watermark_canvas.setFillColor(colors.grey)

        # 计算水印位置
        page_width, page_height = A4
        x = page_width / 2
        y = page_height / 2

        # 旋转和绘制水印
        watermark_canvas.saveState()
        watermark_canvas.translate(x, y)
        watermark_canvas.rotate(angle)
        watermark_canvas.drawCentredText(0, 0, text)
        watermark_canvas.restoreState()

        # 添加到故事流
        from reportlab.platypus import Image

        img = Image(buffer)
        img.drawHeight = page_height
        img.drawWidth = page_width
        img.hAlign = "CENTER"

        story.append(img)
        logger.debug(f"水印已添加: {text}")

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
            title: 页面标题
            page_type: 页面类型
        """
        canvas.saveState()

        y_position = doc.height + doc.topMargin - 0.5 * cm

        # 左侧：公司名称或Logo
        if self.config["show_company_name_on_header"]:
            canvas.setFont("Helvetica", 9)
            canvas.setFillColor(self.BRAND_COLORS["light"])
            canvas.drawString(doc.leftMargin, y_position, self.config["company_name"])

            # 添加Logo（如果需要）
            if self.config["show_logo_on_every_page"] and self.logo_loaded:
                self.add_logo(
                    canvas,
                    doc.leftMargin,
                    y_position + 0.1 * cm,
                    width=1 * inch,
                    height=0.3 * inch,
                )

        # 右侧：页面标题
        if title:
            canvas.setFont("Helvetica", 9)
            canvas.setFillColor(self.BRAND_COLORS["light"])
            text_width = canvas.stringWidth(title, "Helvetica", 9)
            canvas.drawString(
                doc.width + doc.leftMargin - text_width, y_position, title
            )

        # 绘制分割线
        canvas.setStrokeColor(self.BRAND_COLORS["light"])
        canvas.setLineWidth(0.5)
        canvas.line(
            doc.leftMargin,
            y_position - 0.2 * cm,
            doc.width + doc.leftMargin,
            y_position - 0.2 * cm,
        )

        canvas.restoreState()

    def add_footer(
        self,
        canvas,
        doc,
        page_type: str = "normal",
        page_number: Optional[int] = None,
    ) -> None:
        """
        添加页脚

        Args:
            canvas: PDF画布
            doc: 文档对象
            page_type: 页面类型
            page_number: 页码
        """
        canvas.saveState()

        y_position = doc.bottomMargin - 0.5 * cm

        # 左侧：版本信息
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(self.BRAND_COLORS["light"])
        version_text = f"版本: v1.0 | {datetime.now().strftime('%Y-%m-%d')}"
        canvas.drawString(doc.leftMargin, y_position, version_text)

        # 右侧：联系方式
        contact_text = "info@hkquant.com | +852 - XXXX - XXXX"
        text_width = canvas.stringWidth(contact_text, "Helvetica", 8)
        canvas.drawString(
            doc.width + doc.leftMargin - text_width, y_position, contact_text
        )

        # 中间：页码
        if page_number is not None:
            page_text = f"- {page_number} -"
            canvas.setFont("Helvetica", 9)
            canvas.setFillColor(self.BRAND_COLORS["primary"])
            canvas.drawCentredText(
                doc.width / 2 + doc.leftMargin, y_position, page_text
            )

        # 绘制分割线
        canvas.setStrokeColor(self.BRAND_COLORS["light"])
        canvas.setLineWidth(0.5)
        canvas.line(
            doc.leftMargin,
            y_position + 0.2 * cm,
            doc.width + doc.leftMargin,
            y_position + 0.2 * cm,
        )

        canvas.restoreState()

    def create_cover_design(
        self,
        story,
        title: str,
        subtitle: Optional[str] = None,
        logo_width: float = 3 * inch,
        logo_height: float = 1 * inch,
    ) -> None:
        """
        创建封面设计

        Args:
            story: 故事流列表
            title: 报告标题
            subtitle: 副标题
            logo_width: Logo宽度
            logo_height: Logo高度
        """
        from reportlab.lib.units import inch
        from reportlab.platypus import Paragraph, Spacer

        # 添加Logo
        if self.config["show_logo_on_cover"] and self.logo_loaded:
            self.logo_image.drawHeight = logo_height
            self.logo_image.drawWidth = logo_width
            self.logo_image.hAlign = "CENTER"
            story.append(self.logo_image)
            story.append(Spacer(1, 0.5 * inch))

        # 公司名称
        if self.config["show_company_name_on_cover"]:
            company_name = Paragraph(
                self.config["company_name"],
                ParagraphStyle(
                    "CompanyName",
                    fontSize=24,
                    textColor=self.BRAND_COLORS["primary"],
                    alignment=TA_CENTER,
                    spaceAfter=20,
                ),
            )
            story.append(company_name)

        # 报告标题
        report_title = Paragraph(
            title,
            ParagraphStyle(
                "ReportTitle",
                fontSize=28,
                textColor=self.BRAND_COLORS["dark"],
                alignment=TA_CENTER,
                spaceAfter=30,
            ),
        )
        story.append(report_title)

        # 副标题
        if subtitle:
            sub_title = Paragraph(
                subtitle,
                ParagraphStyle(
                    "SubTitle",
                    fontSize=16,
                    textColor=self.BRAND_COLORS["secondary"],
                    alignment=TA_CENTER,
                    spaceAfter=40,
                ),
            )
            story.append(sub_title)

        # 添加水印
        self.add_watermark(story, "CONFIDENTIAL")

        story.append(Spacer(1, 1 * inch))

    def add_section_header(
        self,
        story,
        section_title: str,
        level: int = 1,
    ) -> None:
        """
        添加章节页眉

        Args:
            story: 故事流列表
            section_title: 章节标题
            level: 标题级别
        """
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.platypus import Paragraph, Spacer

        styles = getSampleStyleSheet()

        if level == 1:
            # 一级标题
            style = ParagraphStyle(
                "ChapterTitle",
                parent=styles["Heading1"],
                fontSize=20,
                textColor=self.BRAND_COLORS["primary"],
                spaceAfter=20,
                spaceBefore=20,
                borderWidth=2,
                borderColor=self.BRAND_COLORS["secondary"],
                borderPadding=10,
            )
        else:
            # 二级标题
            style = ParagraphStyle(
                "SectionTitle",
                parent=styles["Heading2"],
                fontSize=16,
                textColor=self.BRAND_COLORS["dark"],
                spaceAfter=15,
                spaceBefore=15,
            )

        story.append(Paragraph(section_title, style))
        story.append(Spacer(1, 0.2 * inch))

    def create_color_palette(self) -> Dict[str, str]:
        """
        获取品牌色彩调色板

        Returns:
            颜色名称到十六进制值的字典
        """
        return {
            name: color.rgb.__str__() if hasattr(color, "rgb") else str(color)
            for name, color in self.BRAND_COLORS.items()
        }

    def apply_brand_style(
        self,
        element,
        style_type: str = "default",
    ) -> None:
        """
        应用品牌样式

        Args:
            element: 要应用样式的元素
            style_type: 样式类型
        """
        style_configs = {
            "default": {
                "fontName": "Helvetica",
                "fontSize": 11,
                "textColor": self.BRAND_COLORS["dark"],
            },
            "title": {
                "fontName": "Helvetica - Bold",
                "fontSize": 18,
                "textColor": self.BRAND_COLORS["primary"],
            },
            "subtitle": {
                "fontName": "Helvetica",
                "fontSize": 14,
                "textColor": self.BRAND_COLORS["secondary"],
            },
            "highlight": {
                "fontName": "Helvetica - Bold",
                "textColor": self.BRAND_COLORS["accent"],
            },
            "success": {
                "textColor": self.BRAND_COLORS["success"],
            },
            "warning": {
                "textColor": self.BRAND_COLORS["warning"],
            },
        }

        if style_type in style_configs:
            config = style_configs[style_type]
            for attr, value in config.items():
                if hasattr(element, attr):
                    setattr(element, attr, value)


class ReportIdentifier:
    """
    报告标识符

    为报告添加唯一标识和版本信息
    """

    def __init__(
        self,
        report_type: str = "量化分析报告",
        version: str = "1.0",
        author: str = "HK Quant System",
    ):
        """
        初始化报告标识符

        Args:
            report_type: 报告类型
            version: 版本号
            author: 作者
        """
        self.report_type = report_type
        self.version = version
        self.author = author
        self.report_id = self._generate_report_id()
        logger.info(f"报告标识符创建: {self.report_id}")

    def _generate_report_id(self) -> str:
        """生成唯一报告ID"""
        timestamp = datetime.now().strftime("%Y % m % d_ % H % M % S")
        return f"{self.report_type}_{timestamp}_{self.version}"

    def get_header_info(self) -> Dict[str, str]:
        """获取报告头部信息"""
        return {
            "report_id": self.report_id,
            "report_type": self.report_type,
            "version": self.version,
            "author": self.author,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

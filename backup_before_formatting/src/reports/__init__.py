"""
PDF报告生成系统

提供专业的PDF报告生成功能，包括：
- 多页报告自动分页
- 动态内容填充
- 响应式布局
- 数据绑定
- 图表嵌入
- 品牌和水印
- 目录和页码

主要模块：
- pdf_generator: 核心PDF生成器
- pdf_templates: 报告模板系统
- pdf_charts: 图表嵌入功能
- pdf_toc: 目录和页码管理
- pdf_branding: 品牌和水印管理

使用示例：
    from src.reports import PDFReportGenerator

    # 创建报告生成器
    generator = PDFReportGenerator(
        output_path="report.pdf",
        title="量化交易分析报告"
    )

    # 添加内容
    generator.add_cover_page(
        subtitle="2024年第四季度",
        date=datetime.now()
    )

    generator.add_executive_summary(
        data={'summary_text': '...'},
        key_metrics=[...]
    )

    generator.add_section_content(
        title="市场分析",
        content="..."
    )

    # 生成PDF
    generator.generate()
"""

from .pdf_branding import (
    BrandingManager,
    ReportIdentifier,
)
from .pdf_charts import ChartManager
from .pdf_generator import PDFReportGenerator
from .pdf_templates import ReportTemplates
from .pdf_toc import (
    BookmarkManager,
    CrossReferenceManager,
    HeaderFooterManager,
    PageNumberManager,
    TableOfContentsManager,
)

__all__ = [
    "PDFReportGenerator",
    "ReportTemplates",
    "ChartManager",
    "TableOfContentsManager",
    "PageNumberManager",
    "HeaderFooterManager",
    "BookmarkManager",
    "CrossReferenceManager",
    "BrandingManager",
    "ReportIdentifier",
]

__version__ = "1.0.0"
__author__ = "HK Quant System"
__email__ = "info@hkquant.com"

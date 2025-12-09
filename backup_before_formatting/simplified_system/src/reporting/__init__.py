#!/usr/bin/env python3
"""
Enhanced Reporting System
專業級報告生成系統

Institutional-grade reporting system for quantitative trading analysis
機構級量化交易分析報告系統

Features:
- Interactive HTML reports with advanced visualizations
- PDF export functionality
- Multi-language support (Chinese/English)
- Executive summary generation
- Custom report templates
- Batch report generation
- Collaboration and sharing tools
"""

from .report_generator import ReportGenerator, ReportType, ReportLanguage, ReportConfig, ReportData
from .executive_summary_fixed import ExecutiveSummaryGenerator
from .pdf_exporter import PDFExporter
from .template_manager import TemplateManager

__version__ = "1.0.0"
__author__ = "Enhanced Reporting System"

# Main exports
__all__ = [
    "ReportGenerator",
    "ExecutiveSummaryGenerator",
    "PDFExporter",
    "TemplateManager",
    "ReportType",
    "ReportLanguage"
]
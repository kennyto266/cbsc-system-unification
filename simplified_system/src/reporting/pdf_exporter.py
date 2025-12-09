#!/usr / bin / env python3
"""
PDF Exporter
PDF導出器

Professional PDF export functionality for trading reports
專業級量化交易報告PDF導出功能
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

logger = logging.getLogger(__name__)


class PDFExporter:
    """PDF導出器"""

    def __init__(self):
        """初始化PDF導出器"""
        self.logger = logging.getLogger(__name__)
        self.pdf_engine = self._initialize_pdf_engine()

    def _initialize_pdf_engine(self):
        """初始化PDF引擎"""
        try:
            # Try to import weasyprint
            import weasyprint

            self.logger.info("Using WeasyPrint for PDF generation")
            return "weasyprint"
        except ImportError:
            try:
                # Try to import pdfkit (wkhtmltopdf)
                import pdfkit

                self.logger.info("Using pdfkit (wkhtmltopdf) for PDF generation")
                return "pdfkit"
            except ImportError:
                try:
                    # Try to import reportlab
                    from reportlab.lib.pagesizes import A4, letter
                    from reportlab.lib.styles import getSampleStyleSheet
                    from reportlab.pdfgen import canvas
                    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

                    self.logger.info("Using ReportLab for PDF generation")
                    return "reportlab"
                except ImportError:
                    self.logger.warning(
                        "No PDF library found. Please install weasyprint, pdfkit, or reportlab"
                    )
                    return None

    def export(
        self,
        html_file: Union[str, Path],
        output_file: Union[str, Path],
        options: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        導出HTML文件為PDF

        Args:
            html_file: HTML文件路徑
            output_file: 輸出PDF文件路徑
            options: PDF生成選項

        Returns:
            bool: 導出是否成功
        """
        try:
            html_path = Path(html_file)
            output_path = Path(output_file)

            if not html_path.exists():
                raise FileNotFoundError(f"HTML file not found: {html_file}")

            # Ensure output directory exists
            output_path.parent.mkdir(parents = True, exist_ok = True)

            if self.pdf_engine == "weasyprint":
                return self._export_with_weasyprint(html_path, output_path, options)
            elif self.pdf_engine == "pdfkit":
                return self._export_with_pdfkit(html_path, output_path, options)
            elif self.pdf_engine == "reportlab":
                return self._export_with_reportlab(html_path, output_path, options)
            else:
                self.logger.error("No PDF engine available")
                return False

        except Exception as e:
            self.logger.error(f"Error exporting PDF: {e}")
            return False

    def _export_with_weasyprint(
        self,
        html_path: Path,
        output_path: Path,
        options: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """使用WeasyPrint導出PDF"""
        try:
            import weasyprint

            # Default options
            pdf_options = {
                "optimize_size": True,
                "fonts": 'Arial, SimHei, "Microsoft YaHei"',
                "javascript_enabled": False,
                "forms": False,
            }

            if options:
                pdf_options.update(options)

            # Read HTML content
            with open(html_path, "r", encoding="utf - 8") as f:
                html_content = f.read()

            # Generate PDF
            html_doc = weasyprint.HTML(
                string = html_content, base_url = str(html_path.parent)
            )
            html_doc.write_pdf(output_path, **pdf_options)

            self.logger.info(
                f"PDF exported successfully with WeasyPrint: {output_path}"
            )
            return True

        except Exception as e:
            self.logger.error(f"WeasyPrint export failed: {e}")
            return False

    def _export_with_pdfkit(
        self,
        html_path: Path,
        output_path: Path,
        options: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """使用pdfkit導出PDF"""
        try:
            import pdfkit

            # Default options for wkhtmltopdf
            pdf_options = {
                "page - size": "A4",
                "margin - top": "0.75in",
                "margin - right": "0.75in",
                "margin - bottom": "0.75in",
                "margin - left": "0.75in",
                "encoding": "UTF - 8",
                "no - outline": None,
                "enable - local - file - access": None,
                "javascript - delay": 1000,
                "load - error - handling": "ignore",
                "load - media - error - handling": "ignore",
            }

            if options:
                pdf_options.update(options)

            # Convert HTML to PDF
            pdfkit.from_file(str(html_path), str(output_path), options = pdf_options)

            self.logger.info(f"PDF exported successfully with pdfkit: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"pdfkit export failed: {e}")
            return False

    def _export_with_reportlab(
        self,
        html_path: Path,
        output_path: Path,
        options: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """使用ReportLab導出PDF（基礎實現）"""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import inch
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.pdfgen import canvas

            # Create PDF
            c = canvas.Canvas(str(output_path), pagesize = A4)
            width, height = A4

            # Set up fonts (try to use Chinese fonts)
            try:
                # Try to register Chinese fonts
                font_paths = [
                    "C:/Windows / Fonts / simhei.ttf",  # Windows
                    "/System / Library / Fonts / PingFang.ttc",  # macOS
                    "/usr / share / fonts / truetype / dejavu / DejaVuSans.ttf",  # Linux
                ]

                for font_path in font_paths:
                    if os.path.exists(font_path):
                        try:
                            pdfmetrics.registerFont(TTFont("Chinese", font_path))
                            break
                        except Exception:
                            continue
            except Exception:
                pass

            # Add title
            c.setFont("Helvetica - Bold", 16)
            title = "Trading Strategy Report"
            title_width = c.stringWidth(title, "Helvetica - Bold", 16)
            c.drawString((width - title_width) / 2, height - 1 * inch, title)

            # Add timestamp
            c.setFont("Helvetica", 10)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.drawString(width - 2 * inch, height - 0.5 * inch, timestamp)

            # Add note about HTML content
            c.setFont("Helvetica", 12)
            note = "This is a basic PDF export. For full HTML - to - PDF conversion, please install weasyprint or wkhtmltopdf."
            c.drawString(1 * inch, height - 2 * inch, note)

            # Add HTML file reference
            c.setFont("Helvetica", 10)
            c.drawString(
                1 * inch, height - 2.5 * inch, f"Source HTML: {html_path.name}"
            )

            # Save PDF
            c.save()

            self.logger.info(f"PDF exported successfully with ReportLab: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"ReportLab export failed: {e}")
            return False

    def export_from_html_string(
        self,
        html_content: str,
        output_file: Union[str, Path],
        options: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        從HTML字符串導出PDF

        Args:
            html_content: HTML字符串內容
            output_file: 輸出PDF文件路徑
            options: PDF生成選項

        Returns:
            bool: 導出是否成功
        """
        try:
            # Create temporary HTML file
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".html", delete = False, encoding="utf - 8"
            ) as temp_file:
                temp_file.write(html_content)
                temp_html_path = temp_file.name

            # Export to PDF
            result = self.export(temp_html_path, output_file, options)

            # Clean up temporary file
            os.unlink(temp_html_path)

            return result

        except Exception as e:
            self.logger.error(f"Error exporting PDF from HTML string: {e}")
            return False

    def create_pdf_with_header_footer(
        self,
        html_content: str,
        output_file: Union[str, Path],
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        創建帶有頁眉頁腳的PDF

        Args:
            html_content: HTML內容
            output_file: 輸出PDF文件路徑
            header_text: 頁眉文本
            footer_text: 頁腳文本
            options: PDF生成選項

        Returns:
            bool: 導出是否成功
        """
        try:
            # Add HTML for header and footer
            enhanced_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf - 8">
                <style>
                    @page {{
                        margin: 2cm;
                        @top - center {{
                            content: "{header_text or 'Trading Strategy Report'}";
                            font - size: 10pt;
                            color: #666;
                        }}
                        @bottom - center {{
                            content: "{footer_text or 'Confidential - Internal Use Only'}";
                            font - size: 10pt;
                            color: #666;
                        }}
                    }}
                    body {{
                        font - family: Arial, SimHei, "Microsoft YaHei", sans - serif;
                        line - height: 1.6;
                        margin: 0;
                        padding: 0;
                    }}
                    .page - break {{
                        page - break - before: always;
                    }}
                </style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """

            return self.export_from_html_string(enhanced_html, output_file, options)

        except Exception as e:
            self.logger.error(f"Error creating PDF with header / footer: {e}")
            return False

    def optimize_pdf(self, pdf_path: Union[str, Path]) -> bool:
        """
        優化PDF文件大小

        Args:
            pdf_path: PDF文件路徑

        Returns:
            bool: 優化是否成功
        """
        try:
            pdf_file = Path(pdf_path)

            if not pdf_file.exists():
                raise FileNotFoundError(f"PDF file not found: {pdf_file}")

            # Get original file size
            original_size = pdf_file.stat().st_size

            if self.pdf_engine == "weasyprint":
                # WeasyPrint typically generates optimized PDFs by default
                self.logger.info("PDF already optimized with WeasyPrint")
                return True

            # For other engines, we could implement additional optimization
            # This would require additional libraries like PyPDF2
            self.logger.info("PDF optimization not implemented for current engine")

            # Log file size
            new_size = pdf_file.stat().st_size
            self.logger.info(
                f"PDF size: {new_size / 1024:.2f} KB (original: {original_size / 1024:.2f} KB)"
            )

            return True

        except Exception as e:
            self.logger.error(f"Error optimizing PDF: {e}")
            return False

    def merge_pdfs(self, pdf_files: list, output_file: Union[str, Path]) -> bool:
        """
        合併多個PDF文件

        Args:
            pdf_files: PDF文件路徑列表
            output_file: 輸出PDF文件路徑

        Returns:
            bool: 合併是否成功
        """
        try:
            from PyPDF2 import PdfMerger

            merger = PdfMerger()

            for pdf_file in pdf_files:
                pdf_path = Path(pdf_file)
                if pdf_path.exists():
                    merger.append(str(pdf_path))
                else:
                    self.logger.warning(f"PDF file not found: {pdf_file}")

            # Write merged PDF
            output_path = Path(output_file)
            output_path.parent.mkdir(parents = True, exist_ok = True)

            merger.write(str(output_path))
            merger.close()

            self.logger.info(f"PDFs merged successfully: {output_path}")
            return True

        except ImportError:
            self.logger.error("PyPDF2 not available for PDF merging")
            return False
        except Exception as e:
            self.logger.error(f"Error merging PDFs: {e}")
            return False

    def add_watermark(
        self,
        pdf_path: Union[str, Path],
        watermark_text: str,
        output_path: Union[str, Path],
    ) -> bool:
        """
        添加PDF水印

        Args:
            pdf_path: 原始PDF文件路徑
            watermark_text: 水印文本
            output_path: 輸出PDF文件路徑

        Returns:
            bool: 添加水印是否成功
        """
        try:
            import io

            from PyPDF2 import PdfReader, PdfWriter
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas

            # Create watermark
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize = letter)
            can.setFont("Helvetica", 40)
            can.setFillColorRGB(
                0.9, 0.9, 0.9, alpha = 0.3
            )  # Light gray, semi - transparent

            # Add watermark text diagonally
            can.saveState()
            can.translate(300, 300)
            can.rotate(45)
            can.drawCentredString(0, 0, watermark_text)
            can.restoreState()

            can.save()

            # Read existing PDF
            reader = PdfReader(str(pdf_path))
            writer = PdfWriter()

            # Get watermark
            packet.seek(0)
            watermark = PdfReader(packet)
            watermark_page = watermark.pages[0]

            # Add watermark to each page
            for page in reader.pages:
                page.merge_page(watermark_page)
                writer.add_page(page)

            # Save watermarked PDF
            output_file = Path(output_path)
            output_file.parent.mkdir(parents = True, exist_ok = True)

            with open(output_file, "wb") as f:
                writer.write(f)

            self.logger.info(f"Watermark added successfully: {output_path}")
            return True

        except ImportError:
            self.logger.error("PyPDF2 not available for watermarking")
            return False
        except Exception as e:
            self.logger.error(f"Error adding watermark: {e}")
            return False


# Utility functions
def export_html_to_pdf(
    html_file: Union[str, Path],
    output_file: Union[str, Path],
    options: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    便利函數：導出HTML到PDF

    Args:
        html_file: HTML文件路徑
        output_file: 輸出PDF文件路徑
        options: PDF生成選項

    Returns:
        bool: 導出是否成功
    """
    exporter = PDFExporter()
    return exporter.export(html_file, output_file, options)


def export_html_string_to_pdf(
    html_content: str,
    output_file: Union[str, Path],
    options: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    便利函數：從HTML字符串導出PDF

    Args:
        html_content: HTML字符串內容
        output_file: 輸出PDF文件路徑
        options: PDF生成選項

    Returns:
        bool: 導出是否成功
    """
    exporter = PDFExporter()
    return exporter.export_from_html_string(html_content, output_file, options)

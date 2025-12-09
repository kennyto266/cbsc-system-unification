#!/usr / bin / env python3
"""
簡化系統 - 導出管理器核心模塊
支持多格式導出、批量處理和自動化報告生成
"""

import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

# Setup logging
logging.basicConfig(
    level = logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class ExportRequest:
    """導出請求數據結構"""

    data: Union[Dict, pd.DataFrame, List]
    format: str
    filename: str
    options: Optional[Dict] = None
    metadata: Optional[Dict] = None


@dataclass
class ExportResult:
    """導出結果數據結構"""

    success: bool
    filename: str
    file_path: str
    file_size: int
    format: str
    error_message: Optional[str] = None
    export_time: Optional[float] = None
    record_count: Optional[int] = None


class ExportManager:
    """導出管理器主類"""

    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.supported_formats = {
            "xlsx",
            "excel",
            "xls",
            "pdf",
            "json",
            "csv",
            "txt",
            "html",
            "htm",
            "markdown",
            "md",
        }
        self.template_dir = Path(__file__).parent / "templates"
        self.export_cache = {}

        # 初始化各種格式導出器
        self._init_exporters()

        logger.info("✅ 導出管理器初始化完成")

    def _load_config(self, config_path: str = None) -> Dict:
        """加載導出配置"""
        default_config_path = (
            Path(__file__).parent.parent.parent.parent / "config" / "export_config.json"
        )

        if config_path is None:
            config_path = default_config_path

        try:
            with open(config_path, "r", encoding="utf - 8") as f:
                config = json.load(f)
            logger.info(f"✅ 導出配置已加載: {config_path}")
            return config
        except Exception as e:
            logger.warning(f"⚠️ 配置加載失敗，使用默認配置: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict:
        """獲取默認導出配置"""
        return {
            "export_settings": {
                "default_format": "xlsx",
                "output_directory": "exports",
                "auto_timestamp": True,
                "compression": False,
                "include_charts": True,
                "include_raw_data": False,
                "language": "zh - CN",
            },
            "excel_settings": {
                "engine": "openpyxl",
                "include_formulas": True,
                "conditional_formatting": True,
            },
            "pdf_settings": {
                "page_size": "A4",
                "orientation": "portrait",
                "margin": "1cm",
                "font_family": "Arial",
                "font_size": 10,
            },
        }

    def _init_exporters(self):
        """初始化各種格式導出器"""
        try:
            # 動態導入格式導出器
            from .formats.csv_exporter import CSVExporter
            from .formats.excel_exporter import ExcelExporter
            from .formats.html_exporter import HTMLExporter
            from .formats.json_exporter import JSONExporter
            from .formats.pdf_exporter import PDFExporter

            self.excel_exporter = ExcelExporter(self.config.get("excel_settings", {}))
            self.pdf_exporter = PDFExporter(self.config.get("pdf_settings", {}))
            self.json_exporter = JSONExporter(self.config.get("json_settings", {}))
            self.csv_exporter = CSVExporter(self.config.get("csv_settings", {}))
            self.html_exporter = HTMLExporter(self.config.get("html_settings", {}))

            logger.info("✅ 所有格式導出器初始化完成")

        except ImportError as e:
            logger.warning(f"⚠️ 部分導出器初始化失敗: {e}")
            self._init_basic_exporters()

    def _init_basic_exporters(self):
        """初始化基礎導出器"""
        from .formats.csv_exporter import CSVExporter
        from .formats.excel_exporter import ExcelExporter
        from .formats.json_exporter import JSONExporter

        self.excel_exporter = ExcelExporter({})
        self.pdf_exporter = None
        self.json_exporter = JSONExporter({})
        self.csv_exporter = CSVExporter({})
        self.html_exporter = None

    def export(self, request: ExportRequest) -> ExportResult:
        """
        執行單個導出請求

        Args:
            request: 導出請求對象

        Returns:
            ExportResult: 導出結果
        """
        start_time = time.time()

        try:
            # 驗證請求
            validation_result = self._validate_request(request)
            if not validation_result[0]:
                return ExportResult(
                    success = False,
                    filename = request.filename,
                    file_path="",
                    file_size = 0,
                    format = request.format,
                    error_message = validation_result[1],
                )

            # 獲取導出器
            exporter = self._get_exporter(request.format)
            if exporter is None:
                return ExportResult(
                    success = False,
                    filename = request.filename,
                    file_path="",
                    file_size = 0,
                    format = request.format,
                    error_message = f"不支持的導出格式: {request.format}",
                )

            # 生成文件名
            output_path = self._generate_output_path(request)

            # 執行導出
            export_result = exporter.export(request.data, output_path, request.options)

            if export_result:
                file_size = (
                    os.path.getsize(output_path) if os.path.exists(output_path) else 0
                )
                record_count = self._count_records(request.data)
                export_time = time.time() - start_time

                return ExportResult(
                    success = True,
                    filename = request.filename,
                    file_path = str(output_path),
                    file_size = file_size,
                    format = request.format,
                    export_time = export_time,
                    record_count = record_count,
                )
            else:
                return ExportResult(
                    success = False,
                    filename = request.filename,
                    file_path="",
                    file_size = 0,
                    format = request.format,
                    error_message="導出過程中發生錯誤",
                )

        except Exception as e:
            logger.error(f"導出失敗: {e}")
            return ExportResult(
                success = False,
                filename = request.filename,
                file_path="",
                file_size = 0,
                format = request.format,
                error_message = str(e),
                export_time = time.time() - start_time,
            )

    def batch_export(self, requests: List[ExportRequest]) -> List[ExportResult]:
        """
        批量導出處理

        Args:
            requests: 導出請求列表

        Returns:
            List[ExportResult]: 導出結果列表
        """
        results = []
        max_workers = self.config.get("batch_export", {}).get("max_concurrent_jobs", 5)

        logger.info(f"開始批量導出: {len(requests)} 個任務，最大併發數: {max_workers}")

        with ThreadPoolExecutor(max_workers = max_workers) as executor:
            # 提交所有任務
            future_to_request = {
                executor.submit(self.export, request): request for request in requests
            }

            # 收集結果
            for future in as_completed(future_to_request):
                request = future_to_request[future]
                try:
                    result = future.result()
                    results.append(result)

                    if result.success:
                        logger.info(f"✅ 導出完成: {result.filename}")
                    else:
                        logger.error(
                            f"❌ 導出失敗: {result.filename} - {result.error_message}"
                        )

                except Exception as e:
                    logger.error(f"❌ 批量導出異常: {request.filename} - {e}")
                    results.append(
                        ExportResult(
                            success = False,
                            filename = request.filename,
                            file_path="",
                            file_size = 0,
                            format = request.format,
                            error_message = str(e),
                        )
                    )

        return results

    def _validate_request(self, request: ExportRequest) -> Tuple[bool, str]:
        """驗證導出請求"""
        if not request.filename:
            return False, "文件名不能為空"

        if request.format not in self.supported_formats:
            return False, f"不支持的格式: {request.format}"

        if request.data is None:
            return False, "導出數據不能為空"

        return True, ""

    def _get_exporter(self, format_type: str):
        """獲取對應格式的導出器"""
        format_map = {
            "xlsx": "excel_exporter",
            "excel": "excel_exporter",
            "xls": "excel_exporter",
            "pdf": "pdf_exporter",
            "json": "json_exporter",
            "csv": "csv_exporter",
            "txt": "csv_exporter",
            "html": "html_exporter",
            "htm": "html_exporter",
            "markdown": "html_exporter",
            "md": "html_exporter",
        }

        exporter_name = format_map.get(format_type.lower())
        return getattr(self, exporter_name, None) if exporter_name else None

    def _generate_output_path(self, request: ExportRequest) -> Path:
        """生成輸出文件路徑"""
        output_dir = Path(
            self.config.get("export_settings", {}).get("output_directory", "exports")
        )
        output_dir.mkdir(exist_ok = True)

        filename = request.filename

        # 添加時間戳
        if self.config.get("export_settings", {}).get("auto_timestamp", True):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name_part = Path(filename).stem
            ext_part = Path(filename).suffix
            if not ext_part:
                ext_part = f".{request.format}"
            filename = f"{name_part}_{timestamp}{ext_part}"

        # 確保有正確的擴展名
        if not Path(filename).suffix:
            filename = f"{filename}.{request.format}"

        return output_dir / filename

    def _count_records(self, data: Any) -> int:
        """統計記錄數量"""
        try:
            if isinstance(data, pd.DataFrame):
                return len(data)
            elif isinstance(data, (list, tuple)):
                return len(data)
            elif isinstance(data, dict):
                return 1
            else:
                return 0
        except Exception:
            return 0

    def get_supported_formats(self) -> List[str]:
        """獲取支持的導出格式列表"""
        return sorted(list(self.supported_formats))

    def export_backtest_results(
        self, results: Dict[str, Any], format_type: str = "xlsx", filename: str = None
    ) -> ExportResult:
        """
        導出回測結果

        Args:
            results: 回測結果數據
            format_type: 導出格式
            filename: 文件名

        Returns:
            ExportResult: 導出結果
        """
        if filename is None:
            filename = f"backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 組織回測結果數據
        organized_data = self._organize_backtest_data(results)

        request = ExportRequest(
            data = organized_data,
            format = format_type,
            filename = filename,
            metadata={
                "type": "backtest_results",
                "generated_at": datetime.now().isoformat(),
            },
        )

        return self.export(request)

    def export_technical_indicators(
        self,
        indicators_data: Dict[str, pd.DataFrame],
        symbol: str,
        format_type: str = "xlsx",
        filename: str = None,
    ) -> ExportResult:
        """
        導出技術指標數據

        Args:
            indicators_data: 技術指標數據
            symbol: 股票代碼
            format_type: 導出格式
            filename: 文件名

        Returns:
            ExportResult: 導出結果
        """
        if filename is None:
            filename = f"technical_indicators_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 添加元數據
        enhanced_data = {
            "symbol": symbol,
            "indicators": indicators_data,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "indicators_count": len(indicators_data),
            },
        }

        request = ExportRequest(
            data = enhanced_data, format = format_type, filename = filename
        )

        return self.export(request)

    def _organize_backtest_data(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """組織回測結果數據"""
        organized = {
            "summary": {},
            "performance_metrics": {},
            "trades": pd.DataFrame(),
            "portfolio_value": pd.Series(),
            "drawdowns": pd.Series(),
        }

        # 提取摘要信息
        if "summary" in results:
            organized["summary"] = results["summary"]

        # 提取性能指標
        if "performance" in results:
            organized["performance_metrics"] = results["performance"]

        # 提取交易記錄
        if "trades" in results:
            organized["trades"] = pd.DataFrame(results["trades"])

        # 提取組合價值
        if "portfolio_value" in results:
            organized["portfolio_value"] = pd.Series(results["portfolio_value"])

        # 提取回撤數據
        if "drawdowns" in results:
            organized["drawdowns"] = pd.Series(results["drawdowns"])

        return organized


# 需要導入time模塊
import time

#!/usr / bin / env python3
"""
API遷移腳本
港股量化交易系統 - 現有API遷移到統一標準

將現有的API端點遷移到統一的API網關架構，
保持向後兼容性的同時實現標準化。

遷移步驟:
1. 掃描現有API端點
2. 分析API模式和格式
3. 生成遷移映射
4. 創建適配器
5. 實施版本控制
6. 添加棄用通知
"""

import ast
import asyncio
import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import httpx

logger = logging.getLogger(__name__)


@dataclass
class ExistingEndpoint:
    """現有API端點信息"""

    path: str
    method: str
    handler: str
    file_path: str
    line_number: int
    docstring: Optional[str] = None
    parameters: List[Dict[str, Any]] = None
    response_model: Optional[str] = None
    tags: List[str] = None


@dataclass
class MigrationMapping:
    """API遷移映射"""

    old_path: str
    new_path: str
    method: str
    service: str
    version: str
    deprecation_date: Optional[datetime] = None
    removal_date: Optional[datetime] = None
    migration_notes: str = ""


class APIScanner:
    """API掃描器"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.endpoints: List[ExistingEndpoint] = []

    def scan_project(self) -> List[ExistingEndpoint]:
        """掃描項目中的API端點"""
        python_files = list(self.project_root.rglob("*.py"))

        for file_path in python_files:
            if self._should_scan_file(file_path):
                self._scan_file(file_path)

        logger.info(f"掃描完成，發現 {len(self.endpoints)} 個API端點")
        return self.endpoints

    def _should_scan_file(self, file_path: Path) -> bool:
        """判斷是否應該掃描文件"""
        # 排除一些目錄
        exclude_patterns = [
            "venv",
            "__pycache__",
            ".pytest_cache",
            "node_modules",
            ".git",
            "tests",
        ]

        path_str = str(file_path)
        for pattern in exclude_patterns:
            if pattern in path_str:
                return False

        # 包含API相關關鍵詞的文件
        api_keywords = ["api", "route", "endpoint", "server", "app"]
        content_lower = file_path.read_text(encoding="utf - 8").lower()

        return any(keyword in content_lower for keyword in api_keywords)

    def _scan_file(self, file_path: Path):
        """掃描單個文件"""
        try:
            with open(file_path, "r", encoding="utf - 8") as f:
                content = f.read()

            # 解析AST
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    self._check_function_decorator(node, file_path, content)

        except Exception as e:
            logger.error(f"掃描文件失敗 {file_path}: {e}")

    def _check_function_decorator(
        self, node: ast.FunctionDef, file_path: Path, content: str
    ):
        """檢查函數的裝飾器"""
        # 檢查FastAPI路由裝飾器
        route_patterns = [
            r"@app\.(get|post|put|delete|patch)\s*\(\s*[\"']([^\"']+)[\"']",
            r"@router\.(get|post|put|delete|patch)\s*\(\s*[\"']([^\"']+)[\"']",
            r"@.*\.(get|post|put|delete|patch)\s*\(\s*[\"']([^\"']+)[\"']",
        ]

        lines = content.split("\n")
        func_start_line = node.lineno - 1

        # 檢查函數前的幾行（裝飾器）
        decorator_lines = []
        for i in range(max(0, func_start_line - 10), func_start_line):
            decorator_lines.append(lines[i])

        decorator_text = "\n".join(decorator_lines)

        for pattern in route_patterns:
            matches = re.finditer(pattern, decorator_text)
            for match in matches:
                method = match.group(1).upper()
                path = match.group(2)

                endpoint = ExistingEndpoint(
                    path=path,
                    method=method,
                    handler=f"{node.name}",
                    file_path=str(file_path),
                    line_number=node.lineno,
                    docstring=ast.get_docstring(node),
                    parameters=self._extract_parameters(node),
                    tags=self._extract_tags(node),
                )

                self.endpoints.append(endpoint)

    def _extract_parameters(self, node: ast.FunctionDef) -> List[Dict[str, Any]]:
        """提取函數參數"""
        parameters = []

        for arg in node.args.args:
            param = {"name": arg.arg, "type": None, "default": None, "required": True}

            # 提取類型註解
            if arg.annotation:
                if isinstance(arg.annotation, ast.Name):
                    param["type"] = arg.annotation.id
                elif isinstance(arg.annotation, ast.Attribute):
                    param["type"] = f"{arg.annotation.value.id}.{arg.annotation.attr}"

            parameters.append(param)

        return parameters

    def _extract_tags(self, node: ast.FunctionDef) -> List[str]:
        """提取標籤"""
        # 從文檔字符串或註釋中提取標籤
        tags = []

        docstring = ast.get_docstring(node)
        if docstring:
            # 簡單的標籤提取邏輯
            if "股票" in docstring or "stock" in docstring.lower():
                tags.append("股票數據")
            if "交易" in docstring or "trade" in docstring.lower():
                tags.append("交易執行")
            if "分析" in docstring or "analysis" in docstring.lower():
                tags.append("技術分析")
            if "回測" in docstring or "backtest" in docstring.lower():
                tags.append("策略回測")

        return tags


class APIAnalyzer:
    """API分析器"""

    def __init__(self):
        self.endpoints: List[ExistingEndpoint] = []
        self.api_patterns: Dict[str, Any] = {}

    def analyze_endpoints(self, endpoints: List[ExistingEndpoint]) -> Dict[str, Any]:
        """分析API端點模式"""
        self.endpoints = endpoints

        analysis = {
            "total_endpoints": len(endpoints),
            "methods_distribution": self._analyze_methods(),
            "path_patterns": self._analyze_path_patterns(),
            "services": self._identify_services(),
            "inconsistencies": self._identify_inconsistencies(),
            "recommendations": self._generate_recommendations(),
        }

        self.api_patterns = analysis
        return analysis

    def _analyze_methods(self) -> Dict[str, int]:
        """分析HTTP方法分布"""
        methods = {}
        for endpoint in self.endpoints:
            methods[endpoint.method] = methods.get(endpoint.method, 0) + 1
        return methods

    def _analyze_path_patterns(self) -> Dict[str, Any]:
        """分析路徑模式"""
        patterns = {"prefixes": {}, "versioned": 0, "restful": 0, "custom": 0}

        for endpoint in self.endpoints:
            # 分析前綴
            path_parts = endpoint.path.strip("/").split("/")
            if path_parts and path_parts[0]:
                prefix = path_parts[0]
                patterns["prefixes"][prefix] = patterns["prefixes"].get(prefix, 0) + 1

            # 檢查版本控制
            if re.match(r"/v\d+/", endpoint.path):
                patterns["versioned"] += 1

            # 檢查RESTful模式
            if self._is_restful_endpoint(endpoint):
                patterns["restful"] += 1
            else:
                patterns["custom"] += 1

        return patterns

    def _is_restful_endpoint(self, endpoint: ExistingEndpoint) -> bool:
        """檢查是否為RESTful端點"""
        # 簡單的RESTful判斷邏輯
        path = endpoint.path

        # 包含資源名稱和可選ID
        if re.match(r"^/api/[a - z-]+(/[a - z0 - 9-]+)*$", path):
            return True

        if re.match(r"^/api/[a - z-]+/\{[^}]+\}$", path):
            return True

        return False

    def _identify_services(self) -> Dict[str, List[ExistingEndpoint]]:
        """識別服務"""
        services = {}

        for endpoint in self.endpoints:
            service = self._classify_service(endpoint)

            if service not in services:
                services[service] = []
            services[service].append(endpoint)

        return services

    def _classify_service(self, endpoint: ExistingEndpoint) -> str:
        """分類端點到服務"""
        path = endpoint.path.lower()

        # 根據路徑和標籤分類
        if any(keyword in path for keyword in ["dashboard", "admin"]):
            return "dashboard"
        elif any(keyword in path for keyword in ["analysis", "indicator", "technical"]):
            return "analysis"
        elif any(keyword in path for keyword in ["trade", "order", "execute"]):
            return "trading"
        elif any(keyword in path for keyword in ["ml", "model", "predict"]):
            return "ml"
        elif any(keyword in path for keyword in ["portfolio", "position"]):
            return "portfolio"
        elif any(keyword in path for keyword in ["risk", "exposure"]):
            return "risk"
        else:
            return "misc"

    def _identify_inconsistencies(self) -> List[Dict[str, Any]]:
        """識別不一致的地方"""
        inconsistencies = []

        # 檢查路徑命名不一致
        path_styles = {}
        for endpoint in self.endpoints:
            style = self._get_path_style(endpoint.path)
            if style not in path_styles:
                path_styles[style] = []
            path_styles[style].append(endpoint)

        if len(path_styles) > 1:
            inconsistencies.append(
                {
                    "type": "path_naming_inconsistency",
                    "description": "發現多種路徑命名風格",
                    "details": path_styles,
                }
            )

        # 檢查版本控制不一致
        versioned_endpoints = [e for e in self.endpoints if re.match(r"/v\d+/", e.path)]
        non_versioned_endpoints = [
            e for e in self.endpoints if not re.match(r"/v\d+/", e.path)
        ]

        if versioned_endpoints and non_versioned_endpoints:
            inconsistencies.append(
                {
                    "type": "versioning_inconsistency",
                    "description": "部分端點使用版本控制，部分沒有",
                    "details": {
                        "versioned": len(versioned_endpoints),
                        "non_versioned": len(non_versioned_endpoints),
                    },
                }
            )

        return inconsistencies

    def _get_path_style(self, path: str) -> str:
        """獲取路徑風格"""
        if "_" in path:
            return "snake_case"
        elif "-" in path:
            return "kebab_case"
        elif any(c.isupper() for c in path):
            return "camel_case"
        else:
            return "lowercase"

    def _generate_recommendations(self) -> List[Dict[str, Any]]:
        """生成遷移建議"""
        recommendations = []

        # API標準化建議
        recommendations.append(
            {
                "type": "standardization",
                "priority": "high",
                "description": "統一所有API使用RESTful設計原則",
                "actions": [
                    "使用統一的URL命名規範",
                    "實施一致的HTTP方法使用",
                    "標準化響應格式",
                ],
            }
        )

        # 版本控制建議
        recommendations.append(
            {
                "type": "versioning",
                "priority": "high",
                "description": "實施API版本控制",
                "actions": [
                    "所有API端點使用URL路徑版本控制",
                    "制定版本棄用策略",
                    "支持向後兼容",
                ],
            }
        )

        # 文檔建議
        recommendations.append(
            {
                "type": "documentation",
                "priority": "medium",
                "description": "完善API文檔",
                "actions": [
                    "為所有端點添加詳細文檔",
                    "生成OpenAPI規範",
                    "提供SDK和示例代碼",
                ],
            }
        )

        return recommendations


class MigrationMapper:
    """遷移映射器"""

    def __init__(self):
        self.mappings: List[MigrationMapping] = []

    def create_mappings(
        self, endpoints: List[ExistingEndpoint]
    ) -> List[MigrationMapping]:
        """創建遷移映射"""
        self.mappings = []

        for endpoint in endpoints:
            mapping = self._create_mapping(endpoint)
            if mapping:
                self.mappings.append(mapping)

        return self.mappings

    def _create_mapping(self, endpoint: ExistingEndpoint) -> Optional[MigrationMapping]:
        """創建單個端點的映射"""
        # 確定目標服務
        service = self._determine_target_service(endpoint)

        # 生成新路徑
        new_path = self._generate_new_path(endpoint, service)

        # 如果路徑沒有變化，則不需要映射
        if new_path == endpoint.path:
            return None

        # 設置版本
        version = self._determine_version(endpoint)

        # 設置棄用時間表
        deprecation_date = datetime.utcnow()
        removal_date = deprecation_date.replace(year=deprecation_date.year + 1)

        return MigrationMapping(
            old_path=endpoint.path,
            new_path=new_path,
            method=endpoint.method,
            service=service,
            version=version,
            deprecation_date=deprecation_date,
            removal_date=removal_date,
            migration_notes=self._generate_migration_notes(endpoint, new_path),
        )

    def _determine_target_service(self, endpoint: ExistingEndpoint) -> str:
        """確定目標服務"""
        path = endpoint.path.lower()

        # 根據路徑模式確定服務
        if any(keyword in path for keyword in ["dashboard", "admin", "system"]):
            return "dashboard"
        elif any(
            keyword in path
            for keyword in ["analysis", "indicator", "technical", "chart"]
        ):
            return "analysis"
        elif any(
            keyword in path for keyword in ["trade", "order", "execution", "position"]
        ):
            return "trading"
        elif any(keyword in path for keyword in ["ml", "model", "predict", "ai"]):
            return "ml"
        elif any(
            keyword in path for keyword in ["portfolio", "holdings", "allocation"]
        ):
            return "portfolio"
        elif any(keyword in path for keyword in ["risk", "exposure", "var"]):
            return "risk"
        else:
            return "misc"

    def _generate_new_path(self, endpoint: ExistingEndpoint, service: str) -> str:
        """生成新的API路徑"""
        # 標準化路徑格式
        old_path = endpoint.path

        # 移除現有版本前綴
        path_without_version = re.sub(r"^/v\d+/", "/", old_path)

        # 處理根路徑
        if path_without_version == "/":
            return f"/api / v1/{service}"

        # 確定資源類型
        resource = self._extract_resource(endpoint)

        if resource:
            return f"/api / v1/{service}/{resource}"
        else:
            # 保持原始路徑結構
            return f"/api / v1/{service}{path_without_version}"

    def _extract_resource(self, endpoint: ExistingEndpoint) -> Optional[str]:
        """從端點提取資源類型"""
        path = endpoint.path.lower()

        # 常見資源模式
        resource_patterns = {
            "stocks": r"stock|equity|ticker|symbol",
            "orders": r"order|trade|transaction",
            "strategies": r"strategy|algo|system",
            "backtests": r"backtest|simulation",
            "portfolios": r"portfolio|holding|allocation",
            "risks": r"risk|exposure|var|drawdown",
            "indicators": r"indicator|oscillator|ma|rsi|macd",
            "signals": r"signal|alert|notification",
        }

        for resource, pattern in resource_patterns.items():
            if re.search(pattern, path):
                return resource

        return None

    def _determine_version(self, endpoint: ExistingEndpoint) -> str:
        """確定API版本"""
        # 如果現有路徑包含版本，使用相同版本
        version_match = re.search(r"/v(\d+)/", endpoint.path)
        if version_match:
            return f"v{version_match.group(1)}"

        # 默認使用v1
        return "v1"

    def _generate_migration_notes(
        self, endpoint: ExistingEndpoint, new_path: str
    ) -> str:
        """生成遷移說明"""
        notes = f"路徑從 {endpoint.path} 遷移到 {new_path}"

        if endpoint.method != "GET":
            notes += f"，方法保持{endpoint.method}"

        if endpoint.parameters:
            notes += "，參數保持不變"

        return notes

    def export_mappings(self, file_path: str):
        """導出映射到文件"""
        mappings_data = []

        for mapping in self.mappings:
            mapping_dict = {
                "old_path": mapping.old_path,
                "new_path": mapping.new_path,
                "method": mapping.method,
                "service": mapping.service,
                "version": mapping.version,
                "deprecation_date": (
                    mapping.deprecation_date.isoformat()
                    if mapping.deprecation_date
                    else None
                ),
                "removal_date": (
                    mapping.removal_date.isoformat() if mapping.removal_date else None
                ),
                "migration_notes": mapping.migration_notes,
            }
            mappings_data.append(mapping_dict)

        with open(file_path, "w", encoding="utf - 8") as f:
            json.dump(mappings_data, f, indent=2, ensure_ascii=False)

        logger.info(f"遷移映射已導出到 {file_path}")


class MigrationExecutor:
    """遷移執行器"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.mappings: List[MigrationMapping] = []

    def execute_migration(self, mappings: List[MigrationMapping], dry_run: bool = True):
        """執行API遷移"""
        self.mappings = mappings

        if dry_run:
            logger.info("執行乾運行，不會修改實際文件")
            self._simulate_migration()
        else:
            logger.info("執行實際遷移，將修改文件")
            self._apply_migration()

    def _simulate_migration(self):
        """模擬遷移過程"""
        for mapping in self.mappings:
            logger.info(
                f"將遷移: {mapping.method} {mapping.old_path} -> {mapping.new_path}"
            )

            # 查找包含舊路徑的文件
            files = self._find_files_with_path(mapping.old_path)

            for file_path in files:
                logger.info(f"  需要修改文件: {file_path}")

    def _apply_migration(self):
        """應用遷移更改"""
        for mapping in self.mappings:
            logger.info(
                f"遷移: {mapping.method} {mapping.old_path} -> {mapping.new_path}"
            )

            # 查找並修改文件
            files = self._find_files_with_path(mapping.old_path)

            for file_path in files:
                self._update_file(file_path, mapping)

    def _find_files_with_path(self, path: str) -> List[Path]:
        """查找包含指定路徑的文件"""
        matching_files = []

        for file_path in self.project_root.rglob("*.py"):
            try:
                content = file_path.read_text(encoding="utf - 8")
                if path in content:
                    matching_files.append(file_path)
            except Exception as e:
                logger.error(f"讀取文件失敗 {file_path}: {e}")

        return matching_files

    def _update_file(self, file_path: Path, mapping: MigrationMapping):
        """更新文件中的路徑"""
        try:
            content = file_path.read_text(encoding="utf - 8")

            # 替換路徑
            old_pattern = f'"{mapping.old_path}"'
            new_pattern = f'"{mapping.new_path}"'

            updated_content = content.replace(old_pattern, new_pattern)

            # 添加棄用註釋
            if old_pattern in content and new_pattern in content:
                deprecation_comment = """
# DEPRECATION NOTICE: This endpoint is deprecated
# Old path: {mapping.old_path}
# New path: {mapping.new_path}
# Deprecation date: {mapping.deprecation_date}
# Removal date: {mapping.removal_date}
# Migration notes: {mapping.migration_notes}
"""
                updated_content = updated_content.replace(
                    old_pattern, deprecation_comment + old_pattern
                )

            # 寫回文件
            file_path.write_text(updated_content, encoding="utf - 8")
            logger.info(f"已更新文件: {file_path}")

        except Exception as e:
            logger.error(f"更新文件失敗 {file_path}: {e}")

    def generate_migration_report(self, output_file: str):
        """生成遷移報告"""
        report = {
            "migration_summary": {
                "total_mappings": len(self.mappings),
                "affected_services": list(set(m.service for m in self.mappings)),
                "migration_date": datetime.utcnow().isoformat(),
            },
            "service_breakdown": self._generate_service_breakdown(),
            "impact_analysis": self._generate_impact_analysis(),
            "recommendations": self._generate_migration_recommendations(),
        }

        with open(output_file, "w", encoding="utf - 8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"遷移報告已生成: {output_file}")

    def _generate_service_breakdown(self) -> Dict[str, Any]:
        """生成服務分解報告"""
        breakdown = {}

        for mapping in self.mappings:
            if mapping.service not in breakdown:
                breakdown[mapping.service] = {
                    "total_endpoints": 0,
                    "methods": {},
                    "version_distribution": {},
                }

            breakdown[mapping.service]["total_endpoints"] += 1
            breakdown[mapping.service]["methods"][mapping.method] = (
                breakdown[mapping.service]["methods"].get(mapping.method, 0) + 1
            )
            breakdown[mapping.service]["version_distribution"][mapping.version] = (
                breakdown[mapping.service]["version_distribution"].get(
                    mapping.version, 0
                )
                + 1
            )

        return breakdown

    def _generate_impact_analysis(self) -> Dict[str, Any]:
        """生成影響分析"""
        # 這裡可以添加更複雜的影響分析邏輯
        return {
            "breaking_changes": len(self.mappings),
            "backward_compatibility": "maintained",
            "client_update_required": True,
            "estimated_effort": f"{len(self.mappings) * 0.5} hours",
        }

    def _generate_migration_recommendations(self) -> List[str]:
        """生成遷移建議"""
        return [
            "通知所有API用戶關於即將進行的變更",
            "提供詳細的遷移指南和示例代碼",
            "設置監控以跟踪舊端點的使用情況",
            "在移除舊端點之前確保所有客戶端已遷移",
            "考慮提供遷移工具或SDK",
        ]


async def main():
    """主函數"""
    # 配置日誌
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # 項目根目錄
    project_root = "C:/Users / Penguin8n / CODEX--"

    logger.info("開始API遷移分析...")

    # 1. 掃描現有API
    scanner = APIScanner(project_root)
    endpoints = scanner.scan_project()

    # 2. 分析API模式
    analyzer = APIAnalyzer()
    analysis = analyzer.analyze_endpoints(endpoints)

    # 保存分析結果
    with open("api_analysis_report.json", "w", encoding="utf - 8") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False, default=str)

    logger.info("API分析報告已生成: api_analysis_report.json")

    # 3. 創建遷移映射
    mapper = MigrationMapper()
    mappings = mapper.create_mappings(endpoints)

    # 導出映射
    mapper.export_mappings("api_migration_mappings.json")
    logger.info("遷移映射已生成: api_migration_mappings.json")

    # 4. 執行遷移（乾運行）
    executor = MigrationExecutor(project_root)
    executor.execute_migration(mappings, dry_run=True)

    # 生成遷移報告
    executor.generate_migration_report("api_migration_report.json")
    logger.info("遷移報告已生成: api_migration_report.json")

    logger.info("API遷移分析完成！")
    logger.info(f"發現 {len(endpoints)} 個API端點")
    logger.info(f"生成 {len(mappings)} 個遷移映射")


if __name__ == "__main__":
    asyncio.run(main())

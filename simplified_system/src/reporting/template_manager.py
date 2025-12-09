#!/usr / bin / env python3
"""
Template Manager
模板管理器

Professional report template management system
專業級報告模板管理系統
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class TemplateType(Enum):
    """模板類型枚舉"""

    STRATEGY_ANALYSIS = "strategy_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    PORTFOLIO_REPORT = "portfolio_report"
    EXECUTIVE_BRIEFING = "executive_briefing"
    COMPLIANCE_REPORT = "compliance_report"
    RESEARCH_REPORT = "research_report"
    CUSTOM = "custom"


@dataclass
class TemplateConfig:
    """模板配置"""

    name: str
    template_type: TemplateType
    description: str
    author: str
    version: str
    created_at: datetime
    updated_at: datetime
    file_path: str
    preview_image: Optional[str] = None
    css_files: List[str] = field(default_factory = list)
    js_files: List[str] = field(default_factory = list)
    variables: Dict[str, Any] = field(default_factory = dict)
    sections: List[str] = field(default_factory = list)
    is_default: bool = False
    is_active: bool = True


class TemplateManager:
    """模板管理器"""

    def __init__(self, templates_dir: Optional[str] = None):
        """
        初始化模板管理器

        Args:
            templates_dir: 模板目錄路徑
        """
        self.logger = logging.getLogger(__name__)

        if templates_dir is None:
            templates_dir = Path(__file__).parent / "html_templates"
        self.templates_dir = Path(templates_dir)

        # Create directories if they don't exist
        self.templates_dir.mkdir(parents = True, exist_ok = True)
        (self.templates_dir / "css").mkdir(exist_ok = True)
        (self.templates_dir / "js").mkdir(exist_ok = True)
        (self.templates_dir / "images").mkdir(exist_ok = True)

        # Initialize templates
        self.templates: Dict[str, TemplateConfig] = {}
        self.load_templates()

        # Create default templates if needed
        self._create_default_templates()

    def load_templates(self) -> None:
        """加載所有模板"""
        try:
            self.logger.info("Loading report templates")

            template_files = list(self.templates_dir.glob("*.json"))

            for template_file in template_files:
                try:
                    with open(template_file, "r", encoding="utf - 8") as f:
                        template_data = json.load(f)

                    # Convert string dates to datetime objects
                    if "created_at" in template_data:
                        template_data["created_at"] = datetime.fromisoformat(
                            template_data["created_at"]
                        )
                    if "updated_at" in template_data:
                        template_data["updated_at"] = datetime.fromisoformat(
                            template_data["updated_at"]
                        )

                    # Convert template_type string to enum
                    if "template_type" in template_data:
                        template_data["template_type"] = TemplateType(
                            template_data["template_type"]
                        )

                    config = TemplateConfig(**template_data)
                    self.templates[config.name] = config

                except Exception as e:
                    self.logger.error(f"Error loading template {template_file}: {e}")

            self.logger.info(f"Loaded {len(self.templates)} templates")

        except Exception as e:
            self.logger.error(f"Error loading templates: {e}")

    def get_template(self, name: str) -> Optional[TemplateConfig]:
        """
        獲取模板配置

        Args:
            name: 模板名稱

        Returns:
            TemplateConfig or None
        """
        return self.templates.get(name)

    def list_templates(
        self, template_type: Optional[TemplateType] = None
    ) -> List[TemplateConfig]:
        """
        列出模板

        Args:
            template_type: 模板類型過濾器

        Returns:
            模板配置列表
        """
        templates = list(self.templates.values())

        if template_type:
            templates = [t for t in templates if t.template_type == template_type]

        return sorted(templates, key = lambda x: x.name)

    def get_default_template(
        self, template_type: TemplateType
    ) -> Optional[TemplateConfig]:
        """
        獲取默認模板

        Args:
            template_type: 模板類型

        Returns:
            默認模板配置或None
        """
        for template in self.templates.values():
            if template.template_type == template_type and template.is_default:
                return template

        # Fallback to first active template of that type
        for template in self.templates.values():
            if template.template_type == template_type and template.is_active:
                return template

        return None

    def create_template(
        self,
        name: str,
        template_type: TemplateType,
        description: str,
        html_content: str,
        author: str = "System",
        css_files: Optional[List[str]] = None,
        js_files: Optional[List[str]] = None,
        variables: Optional[Dict[str, Any]] = None,
        sections: Optional[List[str]] = None,
    ) -> TemplateConfig:
        """
        創建新模板

        Args:
            name: 模板名稱
            template_type: 模板類型
            description: 模板描述
            html_content: HTML內容
            author: 作者
            css_files: CSS文件列表
            js_files: JavaScript文件列表
            variables: 模板變量
            sections: 模板段落

        Returns:
            創建的模板配置
        """
        try:
            # Generate template file path
            template_file_name = f"{name.lower().replace(' ', '_')}_template.html"
            template_file_path = self.templates_dir / template_file_name

            # Save HTML template
            with open(template_file_path, "w", encoding="utf - 8") as f:
                f.write(html_content)

            # Create template config
            config = TemplateConfig(
                name = name,
                template_type = template_type,
                description = description,
                author = author,
                version="1.0.0",
                created_at = datetime.now(),
                updated_at = datetime.now(),
                file_path = template_file_name,
                css_files = css_files or [],
                js_files = js_files or [],
                variables = variables or {},
                sections = sections or [],
            )

            # Save template config
            self._save_template_config(config)

            # Add to templates dictionary
            self.templates[name] = config

            self.logger.info(f"Template created: {name}")
            return config

        except Exception as e:
            self.logger.error(f"Error creating template {name}: {e}")
            raise

    def update_template(self, name: str, updates: Dict[str, Any]) -> bool:
        """
        更新模板

        Args:
            name: 模板名稱
            updates: 更新內容

        Returns:
            更新是否成功
        """
        try:
            if name not in self.templates:
                raise ValueError(f"Template not found: {name}")

            config = self.templates[name]

            # Update allowed fields
            allowed_fields = [
                "description",
                "version",
                "css_files",
                "js_files",
                "variables",
                "sections",
                "is_active",
            ]

            for field, value in updates.items():
                if field in allowed_fields:
                    setattr(config, field, value)

            # Update timestamp
            config.updated_at = datetime.now()

            # Save updated config
            self._save_template_config(config)

            self.logger.info(f"Template updated: {name}")
            return True

        except Exception as e:
            self.logger.error(f"Error updating template {name}: {e}")
            return False

    def delete_template(self, name: str) -> bool:
        """
        刪除模板

        Args:
            name: 模板名稱

        Returns:
            刪除是否成功
        """
        try:
            if name not in self.templates:
                raise ValueError(f"Template not found: {name}")

            config = self.templates[name]

            # Delete HTML file
            template_file = self.templates_dir / config.file_path
            if template_file.exists():
                template_file.unlink()

            # Delete config file
            config_file = self.templates_dir / f"{name}.json"
            if config_file.exists():
                config_file.unlink()

            # Remove from templates dictionary
            del self.templates[name]

            self.logger.info(f"Template deleted: {name}")
            return True

        except Exception as e:
            self.logger.error(f"Error deleting template {name}: {e}")
            return False

    def duplicate_template(
        self, source_name: str, new_name: str, description: Optional[str] = None
    ) -> Optional[TemplateConfig]:
        """
        複製模板

        Args:
            source_name: 源模板名稱
            new_name: 新模板名稱
            description: 新模板描述

        Returns:
            新模板配置或None
        """
        try:
            if source_name not in self.templates:
                raise ValueError(f"Source template not found: {source_name}")

            if new_name in self.templates:
                raise ValueError(f"Template already exists: {new_name}")

            source_config = self.templates[source_name]

            # Read source HTML content
            source_file = self.templates_dir / source_config.file_path
            with open(source_file, "r", encoding="utf - 8") as f:
                html_content = f.read()

            # Create new template
            new_config = self.create_template(
                name = new_name,
                template_type = source_config.template_type,
                description = description or f"Copy of {source_config.description}",
                html_content = html_content,
                author = f"Copy of {source_config.author}",
                css_files = source_config.css_files.copy(),
                js_files = source_config.js_files.copy(),
                variables = source_config.variables.copy(),
                sections = source_config.sections.copy(),
            )

            self.logger.info(f"Template duplicated: {source_name} -> {new_name}")
            return new_config

        except Exception as e:
            self.logger.error(f"Error duplicating template: {e}")
            return None

    def preview_template(
        self, name: str, sample_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        預覽模板

        Args:
            name: 模板名稱
            sample_data: 示例數據

        Returns:
            HTML預覽內容
        """
        try:
            if name not in self.templates:
                raise ValueError(f"Template not found: {name}")

            config = self.templates[name]

            # Read template HTML
            template_file = self.templates_dir / config.file_path
            with open(template_file, "r", encoding="utf - 8") as f:
                html_template = f.read()

            # Use sample data if provided, otherwise create default sample data
            if sample_data is None:
                sample_data = self._create_sample_data(config.template_type)

            # Simple template rendering (could be enhanced with Jinja2)
            html_content = self._render_template(html_template, sample_data)

            return html_content

        except Exception as e:
            self.logger.error(f"Error previewing template {name}: {e}")
            return f"<html><body><h1>Error previewing template: {e}</h1></body></html>"

    def _save_template_config(self, config: TemplateConfig) -> None:
        """保存模板配置"""
        config_file = self.templates_dir / f"{config.name}.json"

        config_data = {
            "name": config.name,
            "template_type": config.template_type.value,
            "description": config.description,
            "author": config.author,
            "version": config.version,
            "created_at": config.created_at.isoformat(),
            "updated_at": config.updated_at.isoformat(),
            "file_path": config.file_path,
            "preview_image": config.preview_image,
            "css_files": config.css_files,
            "js_files": config.js_files,
            "variables": config.variables,
            "sections": config.sections,
            "is_default": config.is_default,
            "is_active": config.is_active,
        }

        with open(config_file, "w", encoding="utf - 8") as f:
            json.dump(config_data, f, indent = 2, ensure_ascii = False)

    def _render_template(self, template: str, data: Dict[str, Any]) -> str:
        """簡單的模板渲染（可替換為Jinja2）"""
        result = template

        # Simple variable replacement
        for key, value in data.items():
            placeholder = f"{{{{ {key} }}}}"
            if isinstance(value, (str, int, float)):
                result = result.replace(placeholder, str(value))

        return result

    def _create_sample_data(self, template_type: TemplateType) -> Dict[str, Any]:
        """創建示例數據"""
        base_data = {
            "report_title": "Sample Trading Strategy Report",
            "generation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "strategy_name": "Sample Strategy",
            "total_return": "15.5%",
            "sharpe_ratio": "1.85",
            "max_drawdown": "-8.2%",
            "win_rate": "62.3%",
        }

        if template_type == TemplateType.STRATEGY_ANALYSIS:
            base_data.update(
                {
                    "analysis_period": "2024 - 01 - 01 to 2024 - 12 - 31",
                    "total_trades": 156,
                    "profit_factor": 1.85,
                }
            )
        elif template_type == TemplateType.RISK_ASSESSMENT:
            base_data.update({"var_95": "-2.5%", "var_99": "-4.8%", "beta": 0.95})

        return base_data

    def _create_default_templates(self) -> None:
        """創建默認模板"""
        try:
            # Check if templates already exist
            if self.templates:
                return

            self.logger.info("Creating default templates")

            # Professional template
            self._create_professional_template()

            # Executive template
            self._create_executive_template()

            # Technical template
            self._create_technical_template()

        except Exception as e:
            self.logger.error(f"Error creating default templates: {e}")

    def _create_professional_template(self) -> None:
        """創建專業模板"""
        html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF - 8">
    <meta name="viewport" content="width = device - width, initial - scale = 1.0">
    <title>{{ report_title }}</title>
    <style>
        body {
            font - family: 'Segoe UI', Tahoma, Geneva, Verdana, sans - serif;
            line - height: 1.6;
            margin: 0;
            padding: 20px;
            color: #333;
            background - color: #f9f9f9;
        }
        .container {
            max - width: 1200px;
            margin: 0 auto;
            background - color: white;
            padding: 30px;
            border - radius: 8px;
            box - shadow: 0 0 20px rgba(0,0,0,0.1);
        }
        .header {
            text - align: center;
            margin - bottom: 40px;
            border - bottom: 3px solid #2c3e50;
            padding - bottom: 20px;
        }
        .header h1 {
            color: #2c3e50;
            margin: 0;
            font - size: 2.5em;
        }
        .header p {
            color: #7f8c8d;
            font - size: 1.1em;
            margin: 10px 0;
        }
        .section {
            margin: 30px 0;
        }
        .section h2 {
            color: #34495e;
            border - left: 4px solid #3498db;
            padding - left: 15px;
            margin - bottom: 20px;
        }
        .metrics - grid {
            display: grid;
            grid - template - columns: repeat(auto - fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .metric - card {
            background: linear - gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border - radius: 8px;
            text - align: center;
            box - shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .metric - card h3 {
            margin: 0 0 10px 0;
            font - size: 1.1em;
            opacity: 0.9;
        }
        .metric - value {
            font - size: 2.2em;
            font - weight: bold;
            margin: 10px 0;
        }
        .chart - container {
            background - color: #f8f9fa;
            border - radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }
        .footer {
            margin - top: 40px;
            padding - top: 20px;
            border - top: 1px solid #ecf0f1;
            text - align: center;
            color: #7f8c8d;
        }
        table {
            width: 100%;
            border - collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            padding: 12px;
            text - align: left;
            border - bottom: 1px solid #ecf0f1;
        }
        th {
            background - color: #34495e;
            color: white;
            font - weight: 600;
        }
        tr:hover {
            background - color: #f8f9fa;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ report_title }}</h1>
            <p>Generated on {{ generation_time }}</p>
        </div>

        <div class="section">
            <h2>Performance Overview</h2>
            <div class="metrics - grid">
                <div class="metric - card">
                    <h3>Total Return</h3>
                    <div class="metric - value">{{ total_return }}</div>
                </div>
                <div class="metric - card">
                    <h3>Sharpe Ratio</h3>
                    <div class="metric - value">{{ sharpe_ratio }}</div>
                </div>
                <div class="metric - card">
                    <h3>Max Drawdown</h3>
                    <div class="metric - value">{{ max_drawdown }}</div>
                </div>
                <div class="metric - card">
                    <h3>Win Rate</h3>
                    <div class="metric - value">{{ win_rate }}</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Strategy Details</h2>
            <table>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
                <tr>
                    <td>Strategy Name</td>
                    <td>{{ strategy_name }}</td>
                </tr>
                <tr>
                    <td>Analysis Period</td>
                    <td>{{ analysis_period }}</td>
                </tr>
                <tr>
                    <td>Total Trades</td>
                    <td>{{ total_trades }}</td>
                </tr>
                <tr>
                    <td>Profit Factor</td>
                    <td>{{ profit_factor }}</td>
                </tr>
            </table>
        </div>

        <div class="section">
            <h2>Charts</h2>
            <div class="chart - container">
                <p>Interactive charts will be embedded here</p>
            </div>
        </div>

        <div class="footer">
            <p>© 2024 Quant Trading System. Confidential - Internal Use Only.</p>
        </div>
    </div>
</body>
</html>
        """

        self.create_template(
            name="Professional",
            template_type = TemplateType.STRATEGY_ANALYSIS,
            description="Professional trading strategy report template",
            html_content = html_content,
            author="System",
            css_files=["professional.css"],
            sections=[
                "Header",
                "Performance Overview",
                "Strategy Details",
                "Charts",
                "Footer",
            ],
        )

    def _create_executive_template(self) -> None:
        """創建執行摘要模板"""
        html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF - 8">
    <meta name="viewport" content="width = device - width, initial - scale = 1.0">
    <title>{{ report_title }}</title>
    <style>
        body {
            font - family: Georgia, serif;
            line - height: 1.8;
            margin: 0;
            padding: 40px;
            color: #2c3e50;
            background: linear - gradient(to bottom, #ffffff, #f8f9fa);
        }
        .executive - header {
            text - align: center;
            margin - bottom: 50px;
            border - bottom: 2px solid #e74c3c;
            padding - bottom: 30px;
        }
        .executive - header h1 {
            color: #2c3e50;
            font - size: 3em;
            margin: 0;
            text - transform: uppercase;
            letter - spacing: 2px;
        }
        .executive - summary {
            font - size: 1.2em;
            font - style: italic;
            color: #34495e;
            margin: 30px 0;
            padding: 20px;
            background - color: #ecf0f1;
            border - left: 4px solid #e74c3c;
            border - radius: 4px;
        }
        .key - metrics {
            display: flex;
            justify - content: space - around;
            margin: 40px 0;
        }
        .key - metric {
            text - align: center;
            padding: 20px;
        }
        .key - metric .value {
            font - size: 2.5em;
            font - weight: bold;
            color: #e74c3c;
            display: block;
        }
        .key - metric .label {
            font - size: 1.1em;
            color: #7f8c8d;
            margin - top: 10px;
        }
        .recommendations {
            background - color: #ffffff;
            border: 1px solid #ecf0f1;
            border - radius: 8px;
            padding: 30px;
            margin: 30px 0;
        }
        .recommendations h2 {
            color: #e74c3c;
            border - bottom: 2px solid #e74c3c;
            padding - bottom: 10px;
        }
        .recommendations ul {
            list - style - type: none;
            padding: 0;
        }
        .recommendations li {
            margin: 15px 0;
            padding - left: 25px;
            position: relative;
        }
        .recommendations li:before {
            content: "▶";
            color: #e74c3c;
            position: absolute;
            left: 0;
        }
    </style>
</head>
<body>
    <div class="executive - header">
        <h1>{{ report_title }}</h1>
        <p>Executive Briefing | {{ generation_time }}</p>
    </div>

    <div class="executive - summary">
        <strong>Executive Summary:</strong> The {{ strategy_name }} strategy has demonstrated strong performance with a total return of {{ total_return }} and a Sharpe ratio of {{ sharpe_ratio }}. Key indicators suggest continued opportunity with manageable risk exposure.
    </div>

    <div class="key - metrics">
        <div class="key - metric">
            <span class="value">{{ total_return }}</span>
            <span class="label">Total Return</span>
        </div>
        <div class="key - metric">
            <span class="value">{{ sharpe_ratio }}</span>
            <span class="label">Sharpe Ratio</span>
        </div>
        <div class="key - metric">
            <span class="value">{{ win_rate }}</span>
            <span class="label">Win Rate</span>
        </div>
    </div>

    <div class="recommendations">
        <h2>Key Recommendations</h2>
        <ul>
            <li>Maintain current strategy parameters given strong performance metrics</li>
            <li>Monitor market conditions for potential optimization opportunities</li>
            <li>Consider gradual position scaling based on continued positive results</li>
            <li>Implement enhanced risk monitoring protocols for drawdown control</li>
        </ul>
    </div>
</body>
</html>
        """

        self.create_template(
            name="Executive",
            template_type = TemplateType.EXECUTIVE_BRIEFING,
            description="Executive briefing template for senior management",
            html_content = html_content,
            author="System",
            sections=["Executive Header", "Summary", "Key Metrics", "Recommendations"],
        )

    def _create_technical_template(self) -> None:
        """創建技術分析模板"""
        html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF - 8">
    <meta name="viewport" content="width = device - width, initial - scale = 1.0">
    <title>{{ report_title }}</title>
    <style>
        body {
            font - family: 'Courier New', monospace;
            background - color: #1e1e1e;
            color: #d4d4d4;
            margin: 0;
            padding: 20px;
        }
        .tech - header {
            background - color: #252526;
            padding: 20px;
            border - radius: 4px;
            margin - bottom: 20px;
        }
        .tech - header h1 {
            color: #569cd6;
            margin: 0;
        }
        .metrics - table {
            width: 100%;
            border - collapse: collapse;
            margin: 20px 0;
        }
        .metrics - table th {
            background - color: #094771;
            color: #ffffff;
            padding: 12px;
            text - align: left;
            border: 1px solid #3c3c3c;
        }
        .metrics - table td {
            background - color: #252526;
            padding: 10px;
            border: 1px solid #3c3c3c;
        }
        .code - block {
            background - color: #1e1e1e;
            border: 1px solid #3c3c3c;
            border - radius: 4px;
            padding: 15px;
            margin: 20px 0;
            overflow - x: auto;
        }
        .positive { color: #4ec9b0; }
        .negative { color: #f44747; }
        .neutral { color: #dcdcaa; }
    </style>
</head>
<body>
    <div class="tech - header">
        <h1>{{ report_title }}</h1>
        <p>Technical Analysis Report | {{ generation_time }}</p>
    </div>

    <table class="metrics - table">
        <thead>
            <tr>
                <th>Parameter</th>
                <th>Value</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Strategy Name</td>
                <td>{{ strategy_name }}</td>
                <td class="neutral">ACTIVE</td>
            </tr>
            <tr>
                <td>Total Return</td>
                <td>{{ total_return }}</td>
                <td class="positive">POSITIVE</td>
            </tr>
            <tr>
                <td>Sharpe Ratio</td>
                <td>{{ sharpe_ratio }}</td>
                <td class="positive">EXCELLENT</td>
            </tr>
            <tr>
                <td>Max Drawdown</td>
                <td>{{ max_drawdown }}</td>
                <td class="negative">MONITOR</td>
            </tr>
            <tr>
                <td>Win Rate</td>
                <td>{{ win_rate }}</td>
                <td class="positive">GOOD</td>
            </tr>
        </tbody>
    </table>

    <div class="code - block">
        <h3>Technical Parameters</h3>
        <pre>
Strategy Configuration:
- Name: {{ strategy_name }}
- Period: {{ analysis_period }}
- Total Trades: {{ total_trades }}
- Profit Factor: {{ profit_factor }}

Risk Metrics:
- VaR (95%): {{ var_95 }}
- Beta: {{ beta }}
        </pre>
    </div>
</body>
</html>
        """

        self.create_template(
            name="Technical",
            template_type = TemplateType.RESEARCH_REPORT,
            description="Technical analysis report for quantitative analysts",
            html_content = html_content,
            author="System",
            sections=["Technical Header", "Metrics Table", "Parameters"],
        )

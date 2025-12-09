"""
提示词管理系统
支持模板管理、版本控制和效果评估
"""

import hashlib
import json
import logging
import os
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class PromptTemplate:
    """提示词模板"""

    def __init__(
        self,
        name: str,
        template: str,
        variables: List[str] = None,
        metadata: Dict[str, Any] = None,
    ):
        self.name = name
        self.template = template
        self.variables = variables or []
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def render(self, **kwargs) -> str:
        """渲染模板"""
        try:
            prompt = self.template
            for var_name, var_value in kwargs.items():
                placeholder = f"{{{var_name}}}"
                prompt = prompt.replace(placeholder, str(var_value))
            return prompt
        except Exception as e:
            logger.error(f"渲染提示词模板失败: {e}")
            return self.template

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "template": self.template,
            "variables": self.variables,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PromptTemplate":
        """从字典创建"""
        template = cls(
            name=data["name"],
            template=data["template"],
            variables=data.get("variables", []),
            metadata=data.get("metadata", {}),
        )
        template.created_at = datetime.fromisoformat(data["created_at"])
        template.updated_at = datetime.fromisoformat(data["updated_at"])
        return template


class PromptVersion:
    """提示词版本"""

    def __init__(
        self,
        template_name: str,
        version: str,
        content: str,
        performance_score: float = 0.0,
    ):
        self.template_name = template_name
        self.version = version
        self.content = content
        self.performance_score = performance_score
        self.created_at = datetime.now()
        self.usage_count = 0
        self.feedback = []

    def add_feedback(self, score: float, comment: str = ""):
        """添加反馈"""
        self.feedback.append(
            {
                "score": score,
                "comment": comment,
                "timestamp": datetime.now().isoformat(),
            }
        )

    def update_performance(self):
        """更新性能分数"""
        if self.feedback:
            self.performance_score = sum(f["score"] for f in self.feedback) / len(
                self.feedback
            )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "template_name": self.template_name,
            "version": self.version,
            "content": self.content,
            "performance_score": self.performance_score,
            "created_at": self.created_at.isoformat(),
            "usage_count": self.usage_count,
            "feedback": self.feedback,
        }


class PromptManager:
    """提示词管理器"""

    def __init__(self, storage_dir: str = "data / prompts"):
        self.storage_dir = storage_dir
        self.templates: Dict[str, PromptTemplate] = {}
        self.versions: Dict[str, List[PromptVersion]] = {}
        self.current_versions: Dict[str, str] = {}
        self.usage_stats: Dict[str, Any] = {}

        # 确保存储目录存在
        os.makedirs(storage_dir, exist_ok=True)

        # 加载现有模板
        self.load_templates()

    def load_templates(self):
        """加载提示词模板"""
        try:
            # 加载模板文件
            templates_file = os.path.join(self.storage_dir, "templates.json")
            if os.path.exists(templates_file):
                with open(templates_file, "r", encoding="utf - 8") as f:
                    templates_data = json.load(f)
                    for data in templates_data:
                        template = PromptTemplate.from_dict(data)
                        self.templates[template.name] = template

            # 加载版本文件
            versions_file = os.path.join(self.storage_dir, "versions.json")
            if os.path.exists(versions_file):
                with open(versions_file, "r", encoding="utf - 8") as f:
                    versions_data = json.load(f)
                    for template_name, versions_list in versions_data.items():
                        self.versions[template_name] = []
                        for data in versions_list:
                            version = PromptVersion(
                                template_name=data["template_name"],
                                version=data["version"],
                                content=data["content"],
                                performance_score=data.get("performance_score", 0.0),
                            )
                            version.created_at = datetime.fromisoformat(
                                data["created_at"]
                            )
                            version.usage_count = data.get("usage_count", 0)
                            version.feedback = data.get("feedback", [])
                            self.versions[template_name].append(version)

            # 加载当前版本映射
            current_file = os.path.join(self.storage_dir, "current_versions.json")
            if os.path.exists(current_file):
                with open(current_file, "r", encoding="utf - 8") as f:
                    self.current_versions = json.load(f)

            logger.info(f"加载了 {len(self.templates)} 个提示词模板")

        except Exception as e:
            logger.error(f"加载提示词模板失败: {e}")

    def save_templates(self):
        """保存提示词模板"""
        try:
            # 保存模板
            templates_data = [
                template.to_dict() for template in self.templates.values()
            ]
            templates_file = os.path.join(self.storage_dir, "templates.json")
            with open(templates_file, "w", encoding="utf - 8") as f:
                json.dump(templates_data, f, ensure_ascii=False, indent=2)

            # 保存版本
            versions_data = {}
            for template_name, versions_list in self.versions.items():
                versions_data[template_name] = [v.to_dict() for v in versions_list]
            versions_file = os.path.join(self.storage_dir, "versions.json")
            with open(versions_file, "w", encoding="utf - 8") as f:
                json.dump(versions_data, f, ensure_ascii=False, indent=2)

            # 保存当前版本映射
            current_file = os.path.join(self.storage_dir, "current_versions.json")
            with open(current_file, "w", encoding="utf - 8") as f:
                json.dump(self.current_versions, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"保存提示词模板失败: {e}")

    def create_template(
        self,
        name: str,
        template: str,
        variables: List[str] = None,
        metadata: Dict[str, Any] = None,
    ) -> bool:
        """创建新模板"""
        try:
            if name in self.templates:
                logger.warning(f"模板 {name} 已存在")
                return False

            prompt_template = PromptTemplate(name, template, variables, metadata)
            self.templates[name] = prompt_template

            # 创建初始版本
            version_id = self._generate_version_id(name, template)
            version = PromptVersion(name, version_id, template)
            self.versions[name] = [version]

            # 设置为当前版本
            self.current_versions[name] = version_id

            self.save_templates()
            logger.info(f"创建提示词模板: {name}")
            return True

        except Exception as e:
            logger.error(f"创建模板失败: {e}")
            return False

    def update_template(
        self, name: str, new_template: str, variables: List[str] = None
    ) -> bool:
        """更新模板"""
        try:
            if name not in self.templates:
                logger.warning(f"模板 {name} 不存在")
                return False

            template = self.templates[name]
            template.template = new_template
            template.variables = variables or template.variables
            template.updated_at = datetime.now()

            # 创建新版本
            version_id = self._generate_version_id(name, new_template)
            version = PromptVersion(name, version_id, new_template)
            self.versions[name].append(version)

            # 更新当前版本
            self.current_versions[name] = version_id

            self.save_templates()
            logger.info(f"更新提示词模板: {name}")
            return True

        except Exception as e:
            logger.error(f"更新模板失败: {e}")
            return False

    def get_current_template(self, name: str) -> Optional[PromptTemplate]:
        """获取当前模板"""
        return self.templates.get(name)

    def get_template_versions(self, name: str) -> List[PromptVersion]:
        """获取模板的所有版本"""
        return self.versions.get(name, [])

    def set_current_version(self, name: str, version_id: str) -> bool:
        """设置当前版本"""
        try:
            if name not in self.templates:
                return False

            versions = self.versions.get(name, [])
            if not any(v.version == version_id for v in versions):
                return False

            self.current_versions[name] = version_id
            self.save_templates()
            return True

        except Exception as e:
            logger.error(f"设置当前版本失败: {e}")
            return False

    def render_template(self, name: str, **kwargs) -> str:
        """渲染模板"""
        try:
            template = self.get_current_template(name)
            if not template:
                logger.warning(f"模板 {name} 不存在")
                return ""

            # 记录使用统计
            self._record_usage(name)

            return template.render(**kwargs)

        except Exception as e:
            logger.error(f"渲染模板失败: {e}")
            return ""

    def add_version_feedback(
        self, template_name: str, version_id: str, score: float, comment: str = ""
    ) -> bool:
        """添加版本反馈"""
        try:
            versions = self.versions.get(template_name, [])
            for version in versions:
                if version.version == version_id:
                    version.add_feedback(score, comment)
                    version.update_performance()
                    self.save_templates()
                    return True
            return False

        except Exception as e:
            logger.error(f"添加反馈失败: {e}")
            return False

    def get_best_version(self, template_name: str) -> Optional[PromptVersion]:
        """获取表现最好的版本"""
        try:
            versions = self.versions.get(template_name, [])
            if not versions:
                return None

            # 按性能分数排序
            best_version = max(versions, key=lambda v: v.performance_score)
            return best_version

        except Exception as e:
            logger.error(f"获取最佳版本失败: {e}")
            return None

    def get_usage_stats(self) -> Dict[str, Any]:
        """获取使用统计"""
        return self.usage_stats.copy()

    def _generate_version_id(self, template_name: str, content: str) -> str:
        """生成版本ID"""
        content_hash = hashlib.sha256(content.encode("utf - 8")).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y % m % d_ % H % M % S")
        return f"v{timestamp}_{content_hash}"

    def _record_usage(self, template_name: str):
        """记录模板使用"""
        now = datetime.now()
        date_key = now.strftime("%Y-%m-%d")

        if template_name not in self.usage_stats:
            self.usage_stats[template_name] = {}

        if date_key not in self.usage_stats[template_name]:
            self.usage_stats[template_name][date_key] = 0

        self.usage_stats[template_name][date_key] += 1

        # 清理旧数据（保留30天）
        cutoff_date = (now - timedelta(days=30)).strftime("%Y-%m-%d")
        for template in self.usage_stats:
            dates_to_remove = [d for d in self.usage_stats[template] if d < cutoff_date]
            for date in dates_to_remove:
                del self.usage_stats[template][date]

    def export_templates(self, export_path: str) -> bool:
        """导出所有模板"""
        try:
            export_data = {
                "templates": [t.to_dict() for t in self.templates.values()],
                "versions": {},
                "current_versions": self.current_versions,
                "usage_stats": self.usage_stats,
                "exported_at": datetime.now().isoformat(),
            }

            for template_name, versions_list in self.versions.items():
                export_data["versions"][template_name] = [
                    v.to_dict() for v in versions_list
                ]

            with open(export_path, "w", encoding="utf - 8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            logger.info(f"导出模板到: {export_path}")
            return True

        except Exception as e:
            logger.error(f"导出模板失败: {e}")
            return False

    def import_templates(self, import_path: str) -> bool:
        """导入模板"""
        try:
            with open(import_path, "r", encoding="utf - 8") as f:
                import_data = json.load(f)

            # 导入模板
            for template_data in import_data.get("templates", []):
                template = PromptTemplate.from_dict(template_data)
                self.templates[template.name] = template

            # 导入版本
            for template_name, versions_list in import_data.get("versions", {}).items():
                self.versions[template_name] = []
                for version_data in versions_list:
                    version = PromptVersion(
                        template_name=version_data["template_name"],
                        version=version_data["version"],
                        content=version_data["content"],
                        performance_score=version_data.get("performance_score", 0.0),
                    )
                    version.created_at = datetime.fromisoformat(
                        version_data["created_at"]
                    )
                    version.usage_count = version_data.get("usage_count", 0)
                    version.feedback = version_data.get("feedback", [])
                    self.versions[template_name].append(version)

            # 导入当前版本映射
            if "current_versions" in import_data:
                self.current_versions.update(import_data["current_versions"])

            # 导入使用统计
            if "usage_stats" in import_data:
                self.usage_stats.update(import_data["usage_stats"])

            self.save_templates()
            logger.info(f"从 {import_path} 导入模板成功")
            return True

        except Exception as e:
            logger.error(f"导入模板失败: {e}")
            return False


# 创建全局实例
prompt_manager = PromptManager()

# 预定义的代理提示词模板
DEFAULT_AGENT_TEMPLATES = {
    "fundamental_analyst": {
        "name": "fundamental_analyst",
        "template": """你是一位专门针对港股的量化分析AI代理，角色为「基本面分析代理（Fundamental Analyst）」。
你的目标是追求高Sharpe Ratio的交易策略，强调风险调整后回报最大化（Sharpe Ratio > 1.5）。
专注恒生指数成分股（如腾讯0700.HK、汇丰0005.HK），考虑中国大陆经济、地缘政治和港股监管因素。

任务：
1. 分析输入港股数据：计算关键基本面指标，如PE比率（市盈率，使用Close价格除以预估EPS）、ROE（股东权益报酬率）、盈利成长率（YoY变化）
2. 识别低估 / 高估股票：筛选PE < 行业中位数30 % 的股票作为买入候选；避免高债务股票（Debt / Equity > 1）
3. 评估风险：计算指标对Sharpe Ratio的贡献（e.g., 低波动基本面股票贡献正向），建议仓位调整以控制drawdown < 10%
4. 输出：使用JSON格式，包含「undervalued_stocks」（低估股票清单，包含代码和PE）、「pe_avg」（平均PE）、「sharpe_contribution」（Sharpe贡献）、「recommendations」（具体建议列表）

输入数据：{stock_data}
当前股票：{current_symbol}

请提供专业的分析结果，确保输出格式正确。""",
        "variables": ["stock_data", "current_symbol"],
        "metadata": {
            "agent_type": "fundamental_analyst",
            "description": "基本面分析代理提示词模板",
            "target_sharpe_ratio": 1.5,
            "focus_stocks": ["0700.HK", "0005.HK", "0941.HK"],
        },
    },
    "technical_analyst": {
        "name": "technical_analyst",
        "template": """你是一位专门针对港股的量化分析AI代理，角色为「技术分析代理（Technical Analyst）」。
你的目标是追求高Sharpe Ratio的交易策略，强调风险调整后回报最大化（Sharpe Ratio > 1.5）。
专注技术指标信号，考虑港股流动性特点。

任务：
1. 分析输入港股数据：计算MA(5,20)、RSI(14)、MACD等技术指标
2. 识别技术信号：MA上穿为买入信号，MA下穿为卖出信号；RSI<30超卖，RSI>70超买
3. 评估信号强度：结合成交量确认信号有效性，计算信号Sharpe贡献
4. 输出：使用JSON格式，包含「signals」（信号列表，包含日期、类型、强度）、「rsi_avg」（平均RSI）、「macd_signals」（MACD信号数量）、「sharpe_contribution」（Sharpe贡献）、「recommendations」（技术建议列表）

输入数据：{stock_data}
当前股票：{current_symbol}

请提供专业的分析结果，确保输出格式正确。""",
        "variables": ["stock_data", "current_symbol"],
        "metadata": {
            "agent_type": "technical_analyst",
            "description": "技术分析代理提示词模板",
            "target_sharpe_ratio": 1.5,
            "indicators": ["MA5", "MA20", "RSI", "MACD"],
        },
    },
}


# 初始化默认模板
def initialize_default_templates():
    """初始化默认提示词模板"""
    for template_data in DEFAULT_AGENT_TEMPLATES.values():
        prompt_manager.create_template(
            name=template_data["name"],
            template=template_data["template"],
            variables=template_data["variables"],
            metadata=template_data["metadata"],
        )


if __name__ == "__main__":
    # 初始化默认模板
    initialize_default_templates()
    print("默认提示词模板已初始化")

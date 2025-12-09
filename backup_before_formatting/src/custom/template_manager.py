"""
模板管理系统
实现模板的导入导出、分类管理、搜索过滤和版本控制
"""

import json
import logging
import shutil
import zipfile
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .strategy_template import (
    StrategyTemplate,
    StrategyTemplateEngine,
    TemplateStatus,
    TemplateType,
)

logger = logging.getLogger(__name__)


class ExportFormat(Enum):
    """导出格式枚举"""

    JSON = "json"
    YAML = "yaml"
    ZIP = "zip"


class SortField(Enum):
    """排序字段枚举"""

    NAME = "name"
    CREATED = "created_at"
    UPDATED = "updated_at"
    AUTHOR = "author"
    TYPE = "type"


class SortOrder(Enum):
    """排序顺序枚举"""

    ASC = "asc"
    DESC = "desc"


class TemplateManager:
    """策略模板管理器"""

    def __init__(self, engine: StrategyTemplateEngine):
        """初始化模板管理器"""
        self.engine = engine
        self.export_dir = Path("data / template_exports")
        self.import_dir = Path("data / template_imports")
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.import_dir.mkdir(parents=True, exist_ok=True)

    def save_template(
        self,
        template_id: str,
        category: str = None,
        tags: List[str] = None,
        notes: str = None,
    ) -> bool:
        """保存模板到本地"""
        try:
            template = self.engine.get_template(template_id)
            if not template:
                logger.error(f"模板不存在: {template_id}")
                return False

            # 添加元数据
            if category:
                template.metadata["category"] = category
            if tags:
                template.metadata["tags"] = tags
            if notes:
                template.metadata["notes"] = notes

            # 保存到文件
            filename = f"{template.name}_{template.id[:8]}.json"
            filepath = self.export_dir / filename

            data = {
                "template": self.engine.export_template(template_id),
                "metadata": {
                    "exported_at": datetime.now().isoformat(),
                    "exported_by": "user",
                    "category": category,
                    "tags": tags,
                    "notes": notes,
                },
            }

            with open(filepath, "w", encoding="utf - 8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"模板已保存: {filename}")
            return True

        except Exception as e:
            logger.error(f"保存模板失败: {e}")
            return False

    def export_template(
        self,
        template_id: str,
        format: ExportFormat = ExportFormat.ZIP,
        include_history: bool = False,
        output_path: str = None,
    ) -> Optional[str]:
        """导出模板"""
        try:
            template = self.engine.get_template(template_id)
            if not template:
                raise ValueError(f"模板不存在: {template_id}")

            if not output_path:
                timestamp = datetime.now().strftime("%Y % m % d_ % H % M % S")
                filename = f"{template.name}_{template_id[:8]}_{timestamp}"
                output_path = f"data / exports/{filename}"

            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            if format == ExportFormat.ZIP:
                return self._export_as_zip(template_id, output_path, include_history)
            elif format == ExportFormat.JSON:
                return self._export_as_json(template_id, output_path)
            elif format == ExportFormat.YAML:
                return self._export_as_yaml(template_id, output_path)
            else:
                raise ValueError(f"不支持的格式: {format}")

        except Exception as e:
            logger.error(f"导出模板失败: {e}")
            return None

    def _export_as_zip(
        self, template_id: str, output_path: str, include_history: bool
    ) -> str:
        """导出为ZIP格式"""
        zip_path = f"{output_path}.zip"

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # 导出主模板
            template_data = self.engine.export_template(template_id, "json")
            zf.writestr("template.json", template_data)

            # 导出元数据
            metadata = {
                "exported_at": datetime.now().isoformat(),
                "include_history": include_history,
            }
            zf.writestr("metadata.json", json.dumps(metadata, indent=2))

            # 可选：包含版本历史
            if include_history:
                history = self.engine.get_template_history(template_id)
                zf.writestr("history.json", json.dumps(history, indent=2))

                # 导出所有历史版本
                for i, version in enumerate(history):
                    zf.writestr(
                        f"versions / version_{i}.json", json.dumps(version, indent=2)
                    )

        logger.info(f"模板已导出为ZIP: {zip_path}")
        return zip_path

    def _export_as_json(self, template_id: str, output_path: str) -> str:
        """导出为JSON格式"""
        data = self.engine.export_template(template_id, "json")
        with open(output_path, "w", encoding="utf - 8") as f:
            f.write(data)
        logger.info(f"模板已导出为JSON: {output_path}")
        return output_path

    def _export_as_yaml(self, template_id: str, output_path: str) -> str:
        """导出为YAML格式"""
        data = self.engine.export_template(template_id, "yaml")
        with open(output_path, "w", encoding="utf - 8") as f:
            f.write(data)
        logger.info(f"模板已导出为YAML: {output_path}")
        return output_path

    def import_template(
        self,
        file_path: str,
        format: ExportFormat = ExportFormat.ZIP,
        overwrite: bool = False,
    ) -> Optional[str]:
        """导入模板"""
        try:
            if format == ExportFormat.ZIP:
                return self._import_from_zip(file_path, overwrite)
            elif format == ExportFormat.JSON:
                return self._import_from_json(file_path, overwrite)
            elif format == ExportFormat.YAML:
                return self._import_from_yaml(file_path, overwrite)
            else:
                raise ValueError(f"不支持的格式: {format}")

        except Exception as e:
            logger.error(f"导入模板失败: {e}")
            return None

    def _import_from_zip(self, zip_path: str, overwrite: bool) -> str:
        """从ZIP文件导入"""
        with zipfile.ZipFile(zip_path, "r") as zf:
            # 读取主模板
            template_json = zf.read("template.json").decode("utf - 8")
            metadata_json = zf.read("metadata.json").decode("utf - 8")

            # 导入模板
            template_id = self.engine.import_template(template_json, "json")

            # 可选：导入版本历史
            if "history.json" in zf.namelist():
                history_json = zf.read("history.json").decode("utf - 8")
                # 处理历史数据...

            logger.info(f"从ZIP导入模板: {template_id}")
            return template_id

    def _import_from_json(self, json_path: str, overwrite: bool) -> str:
        """从JSON文件导入"""
        with open(json_path, "r", encoding="utf - 8") as f:
            data = json.load(f)

        if "template" in data:
            # 新格式（包含元数据）
            template_id = self.engine.import_template(data["template"], "json")
        else:
            # 旧格式（纯模板）
            template_id = self.engine.import_template(json.dumps(data), "json")

        logger.info(f"从JSON导入模板: {template_id}")
        return template_id

    def _import_from_yaml(self, yaml_path: str, overwrite: bool) -> str:
        """从YAML文件导入"""
        with open(yaml_path, "r", encoding="utf - 8") as f:
            data = yaml.safe_load(f)

        if isinstance(data, dict) and "variables" in data:
            template_id = self.engine.import_template(yaml.dump(data), "yaml")
        else:
            template_id = self.engine.import_template(yaml.dump(data), "yaml")

        logger.info(f"从YAML导入模板: {template_id}")
        return template_id

    def search_templates(
        self,
        query: str = None,
        template_type: TemplateType = None,
        status: TemplateStatus = None,
        category: str = None,
        tags: List[str] = None,
        author: str = None,
        date_from: str = None,
        date_to: str = None,
        sort_by: SortField = SortField.UPDATED,
        sort_order: SortOrder = SortOrder.DESC,
        limit: int = 100,
    ) -> List[StrategyTemplate]:
        """搜索模板"""
        templates = self.engine.list_templates()

        # 文本搜索
        if query:
            query_lower = query.lower()
            templates = [
                t
                for t in templates
                if query_lower in t.name.lower()
                or query_lower in t.description.lower()
                or any(query_lower in tag.lower() for tag in t.metadata.get("tags", []))
            ]

        # 类型过滤
        if template_type:
            templates = [t for t in templates if t.type == template_type]

        # 状态过滤
        if status:
            templates = [t for t in templates if t.status == status]

        # 分类过滤
        if category:
            templates = [t for t in templates if t.metadata.get("category") == category]

        # 标签过滤
        if tags:
            template_tags = set(tags)
            templates = [
                t
                for t in templates
                if template_tags.intersection(set(t.metadata.get("tags", [])))
            ]

        # 作者过滤
        if author:
            templates = [t for t in templates if author.lower() in t.author.lower()]

        # 日期过滤
        if date_from:
            templates = [t for t in templates if t.created_at >= date_from]

        if date_to:
            templates = [t for t in templates if t.created_at <= date_to]

        # 排序
        if sort_by == SortField.NAME:
            templates.sort(key=lambda t: t.name, reverse=(sort_order == SortOrder.DESC))
        elif sort_by == SortField.CREATED:
            templates.sort(
                key=lambda t: t.created_at, reverse=(sort_order == SortOrder.DESC)
            )
        elif sort_by == SortField.UPDATED:
            templates.sort(
                key=lambda t: t.updated_at, reverse=(sort_order == SortOrder.DESC)
            )
        elif sort_by == SortField.AUTHOR:
            templates.sort(
                key=lambda t: t.author, reverse=(sort_order == SortOrder.DESC)
            )
        elif sort_by == SortField.TYPE:
            templates.sort(
                key=lambda t: t.type.value, reverse=(sort_order == SortOrder.DESC)
            )

        # 限制结果数量
        return templates[:limit]

    def get_categories(self) -> List[str]:
        """获取所有分类"""
        categories = set()
        for template in self.engine.templates.values():
            if "category" in template.metadata:
                categories.add(template.metadata["category"])
        return sorted(list(categories))

    def get_tags(self) -> List[str]:
        """获取所有标签"""
        tags = set()
        for template in self.engine.templates.values():
            if "tags" in template.metadata:
                tags.update(template.metadata["tags"])
        return sorted(list(tags))

    def get_authors(self) -> List[str]:
        """获取所有作者"""
        authors = set()
        for template in self.engine.templates.values():
            authors.add(template.author)
        return sorted(list(authors))

    def bulk_export(
        self,
        template_ids: List[str],
        output_path: str,
        format: ExportFormat = ExportFormat.ZIP,
    ) -> Optional[str]:
        """批量导出模板"""
        try:
            timestamp = datetime.now().strftime("%Y % m % d_ % H % M % S")
            output_path = f"{output_path}_{timestamp}.zip"

            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for template_id in template_ids:
                    template = self.engine.get_template(template_id)
                    if template:
                        # 导出每个模板
                        template_data = self.engine.export_template(template_id, "json")
                        zf.writestr(
                            f"templates/{template.name}_{template_id[:8]}.json",
                            template_data,
                        )

                # 导出清单
                manifest = {
                    "exported_at": datetime.now().isoformat(),
                    "total_templates": len(template_ids),
                    "templates": [
                        {"id": tid, "name": self.engine.get_template(tid).name}
                        for tid in template_ids
                        if self.engine.get_template(tid)
                    ],
                }
                zf.writestr("manifest.json", json.dumps(manifest, indent=2))

            logger.info(f"批量导出完成: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"批量导出失败: {e}")
            return None

    def backup_templates(self, output_path: str = None) -> str:
        """备份所有模板"""
        if not output_path:
            timestamp = datetime.now().strftime("%Y % m % d_ % H % M % S")
            output_path = f"data / backups / templates_backup_{timestamp}.zip"

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        template_ids = list(self.engine.templates.keys())
        return self.bulk_export(template_ids, output_path, ExportFormat.ZIP)

    def restore_templates(self, backup_path: str) -> List[str]:
        """恢复模板"""
        imported_ids = []

        try:
            with zipfile.ZipFile(backup_path, "r") as zf:
                # 读取清单
                manifest = json.loads(zf.read("manifest.json").decode("utf - 8"))

                # 恢复每个模板
                for template_info in manifest["templates"]:
                    # 这里需要解析文件名...
                    for filename in zf.namelist():
                        if filename.startswith("templates/") and filename.endswith(
                            ".json"
                        ):
                            template_json = zf.read(filename).decode("utf - 8")
                            template_id = self.engine.import_template(
                                template_json, "json"
                            )
                            imported_ids.append(template_id)

            logger.info(f"恢复完成，共 {len(imported_ids)} 个模板")
            return imported_ids

        except Exception as e:
            logger.error(f"恢复失败: {e}")
            return []

    def get_template_analytics(self) -> Dict[str, Any]:
        """获取模板分析数据"""
        stats = self.engine.get_statistics()

        # 按分类统计
        by_category = {}
        for template in self.engine.templates.values():
            category = template.metadata.get("category", "未分类")
            by_category[category] = by_category.get(category, 0) + 1

        # 最近的模板
        recent_templates = sorted(
            self.engine.templates.values(), key=lambda t: t.updated_at, reverse=True
        )[:10]

        # 使用频率（基于创建次数）
        usage_stats = {}
        for template in self.engine.templates.values():
            usage_stats[template.name] = {
                "created": template.created_at,
                "updated": template.updated_at,
                "author": template.author,
            }

        return {
            "summary": stats,
            "by_category": by_category,
            "recent_templates": [
                {
                    "id": t.id,
                    "name": t.name,
                    "type": t.type.value,
                    "updated": t.updated_at,
                }
                for t in recent_templates
            ],
            "usage": usage_stats,
        }

    def validate_import(self, file_path: str) -> Dict[str, Any]:
        """验证导入文件"""
        result = {"valid": False, "errors": [], "warnings": [], "template_info": None}

        try:
            # 检查文件是否存在
            if not Path(file_path).exists():
                result["errors"].append("文件不存在")
                return result

            # 尝试解析
            with open(file_path, "r", encoding="utf - 8") as f:
                if file_path.endswith(".json"):
                    data = json.load(f)
                elif file_path.endswith(".yaml") or file_path.endswith(".yml"):
                    data = yaml.safe_load(f)
                else:
                    result["errors"].append("不支持的文件格式")
                    return result

            # 验证模板结构
            required_fields = ["name", "type", "description", "version"]
            for field in required_fields:
                if field not in data:
                    result["errors"].append(f"缺少必需字段: {field}")

            # 提取模板信息
            result["template_info"] = {
                "name": data.get("name"),
                "type": data.get("type"),
                "version": data.get("version"),
                "author": data.get("author"),
                "created_at": data.get("created_at"),
            }

            result["valid"] = len(result["errors"]) == 0

        except json.JSONDecodeError as e:
            result["errors"].append(f"JSON解析错误: {e}")
        except yaml.YAMLError as e:
            result["errors"].append(f"YAML解析错误: {e}")
        except Exception as e:
            result["errors"].append(f"验证错误: {e}")

        return result

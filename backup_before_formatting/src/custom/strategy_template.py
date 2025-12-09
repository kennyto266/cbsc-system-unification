"""
策略模板引擎
实现策略结构定义、模板变量替换、配置管理和版本控制
"""

import json
import logging
import sqlite3
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import jinja2
import yaml

logger = logging.getLogger(__name__)


class TemplateType(Enum):
    """模板类型枚举"""

    INDICATOR = "indicator"
    SIGNAL = "signal"
    COMBINATION = "combination"
    RISK_MANAGEMENT = "risk_management"
    FULL_STRATEGY = "full_strategy"


class TemplateStatus(Enum):
    """模板状态枚举"""

    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


@dataclass
class TemplateVariable:
    """模板变量定义"""

    name: str
    type: str  # int, float, string, boolean, list, dict
    default: Any
    description: str
    required: bool = False
    validation: Optional[Dict[str, Any]] = None


@dataclass
class StrategyNode:
    """策略节点定义"""

    id: str
    type: str  # indicator, filter, signal, action
    name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    position: Dict[str, float] = field(default_factory=lambda: {"x": 0, "y": 0})


@dataclass
class StrategyTemplate:
    """策略模板定义"""

    id: str
    name: str
    type: TemplateType
    description: str
    version: str
    author: str
    created_at: str
    updated_at: str
    status: TemplateStatus
    variables: List[TemplateVariable] = field(default_factory=list)
    nodes: List[StrategyNode] = field(default_factory=list)
    edges: List[Dict[str, Any]] = field(default_factory=list)
    code_template: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_template_id: Optional[str] = None


class StrategyTemplateEngine:
    """策略模板引擎核心类"""

    def __init__(self, db_path: str = "data / strategy_templates.db"):
        """初始化模板引擎"""
        self.db_path = db_path
        self.templates: Dict[str, StrategyTemplate] = {}
        self.jinja_env = jinja2.Environment(
            loader=jinja2.DictLoader({}),
            autoescape=jinja2.select_autoescape(["html", "xml"]),
        )
        self._init_database()
        self._load_templates()

    def _init_database(self):
        """初始化SQLite数据库"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS templates (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                description TEXT,
                version TEXT NOT NULL,
                author TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                status TEXT NOT NULL,
                variables_json TEXT,
                nodes_json TEXT,
                edges_json TEXT,
                code_template TEXT,
                metadata_json TEXT,
                parent_template_id TEXT,
                FOREIGN KEY (parent_template_id) REFERENCES templates(id)
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS template_versions (
                id TEXT PRIMARY KEY,
                template_id TEXT NOT NULL,
                version TEXT NOT NULL,
                data_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (template_id) REFERENCES templates(id)
            )
        """
        )

        conn.commit()
        conn.close()

    def _load_templates(self):
        """从数据库加载所有模板"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM templates")
        rows = cursor.fetchall()

        for row in rows:
            template_dict = {
                "id": row[0],
                "name": row[1],
                "type": TemplateType(row[2]),
                "description": row[3],
                "version": row[4],
                "author": row[5],
                "created_at": row[6],
                "updated_at": row[7],
                "status": TemplateStatus(row[8]),
                "variables": json.loads(row[9]) if row[9] else [],
                "nodes": (
                    [StrategyNode(**node) for node in json.loads(row[10])]
                    if row[10]
                    else []
                ),
                "edges": json.loads(row[11]) if row[11] else [],
                "code_template": row[12] or "",
                "metadata": json.loads(row[13]) if row[13] else {},
                "parent_template_id": row[14],
            }
            template = StrategyTemplate(**template_dict)
            self.templates[template.id] = template

        conn.close()
        logger.info(f"已加载 {len(self.templates)} 个策略模板")

    def create_template(
        self,
        name: str,
        template_type: TemplateType,
        description: str,
        author: str,
        variables: List[TemplateVariable] = None,
        nodes: List[StrategyNode] = None,
        edges: List[Dict] = None,
        code_template: str = "",
        metadata: Dict = None,
        parent_template_id: str = None,
    ) -> str:
        """创建新模板"""
        template_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        template = StrategyTemplate(
            id=template_id,
            name=name,
            type=template_type,
            description=description,
            version="1.0.0",
            author=author,
            created_at=now,
            updated_at=now,
            status=TemplateStatus.DRAFT,
            variables=variables or [],
            nodes=nodes or [],
            edges=edges or [],
            code_template=code_template,
            metadata=metadata or {},
            parent_template_id=parent_template_id,
        )

        self.templates[template_id] = template
        self._save_template(template)
        logger.info(f"创建新模板: {name} (ID: {template_id})")
        return template_id

    def _save_template(self, template: StrategyTemplate):
        """保存模板到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO templates
            (id, name, type, description, version, author, created_at, updated_at,
             status, variables_json, nodes_json, edges_json, code_template,
             metadata_json, parent_template_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                template.id,
                template.name,
                template.type.value,
                template.description,
                template.version,
                template.author,
                template.created_at,
                template.updated_at,
                template.status.value,
                json.dumps([asdict(v) for v in template.variables]),
                json.dumps([asdict(n) for n in template.nodes]),
                json.dumps(template.edges),
                template.code_template,
                json.dumps(template.metadata),
                template.parent_template_id,
            ),
        )

        # 保存版本历史
        version_id = str(uuid.uuid4())
        cursor.execute(
            """
            INSERT INTO template_versions
            (id, template_id, version, data_json, created_at)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                version_id,
                template.id,
                template.version,
                json.dumps(asdict(template)),
                template.updated_at,
            ),
        )

        conn.commit()
        conn.close()

    def get_template(self, template_id: str) -> Optional[StrategyTemplate]:
        """获取模板"""
        return self.templates.get(template_id)

    def update_template(self, template_id: str, **kwargs) -> bool:
        """更新模板"""
        if template_id not in self.templates:
            logger.error(f"模板不存在: {template_id}")
            return False

        template = self.templates[template_id]
        for key, value in kwargs.items():
            if hasattr(template, key):
                setattr(template, key, value)

        template.updated_at = datetime.now().isoformat()
        self._save_template(template)
        logger.info(f"更新模板: {template.name}")
        return True

    def delete_template(self, template_id: str) -> bool:
        """删除模板"""
        if template_id not in self.templates:
            logger.error(f"模板不存在: {template_id}")
            return False

        template = self.templates[template_id]
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM templates WHERE id = ?", (template_id,))
        cursor.execute(
            "DELETE FROM template_versions WHERE template_id = ?", (template_id,)
        )

        conn.commit()
        conn.close()

        del self.templates[template_id]
        logger.info(f"删除模板: {template.name}")
        return True

    def list_templates(
        self,
        template_type: Optional[TemplateType] = None,
        status: Optional[TemplateStatus] = None,
    ) -> List[StrategyTemplate]:
        """列出模板"""
        templates = list(self.templates.values())

        if template_type:
            templates = [t for t in templates if t.type == template_type]

        if status:
            templates = [t for t in templates if t.status == status]

        return sorted(templates, key=lambda t: t.updated_at, reverse=True)

    def instantiate_template(
        self, template_id: str, variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """实例化模板（替换变量）"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"模板不存在: {template_id}")

        # 验证必需变量
        for var in template.variables:
            if var.required and var.name not in variables:
                raise ValueError(f"缺少必需变量: {var.name}")

        # 执行变量替换
        context = {"variables": variables, "metadata": template.metadata}

        instantiated = {
            "id": str(uuid.uuid4()),
            "name": template.name,
            "type": template.type.value,
            "version": template.version,
            "nodes": [asdict(node) for node in template.nodes],
            "edges": template.edges,
            "code": template.code_template,
            "parameters": variables,
        }

        # 如果有代码模板，使用 Jinja2 渲染
        if template.code_template:
            try:
                jinja_template = self.jinja_env.from_string(template.code_template)
                instantiated["generated_code"] = jinja_template.render(**context)
            except Exception as e:
                logger.error(f"代码模板渲染失败: {e}")
                instantiated["generated_code"] = template.code_template

        return instantiated

    def export_template(
        self, template_id: str, format: str = "json"
    ) -> Union[str, Dict]:
        """导出模板"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"模板不存在: {template_id}")

        data = asdict(template)

        if format.lower() == "json":
            return json.dumps(data, indent=2, default=str)
        elif format.lower() == "yaml":
            return yaml.dump(data, default_flow_style=False)
        else:
            raise ValueError(f"不支持的格式: {format}")

    def import_template(self, data: Union[str, Dict], format: str = "json") -> str:
        """导入模板"""
        if isinstance(data, str):
            if format.lower() == "json":
                template_dict = json.loads(data)
            elif format.lower() == "yaml":
                template_dict = yaml.safe_load(data)
            else:
                raise ValueError(f"不支持的格式: {format}")
        else:
            template_dict = data

        # 生成新ID避免冲突
        template_dict["id"] = str(uuid.uuid4())
        template_dict["created_at"] = datetime.now().isoformat()
        template_dict["updated_at"] = template_dict["created_at"]
        template_dict["status"] = TemplateStatus.DRAFT.value

        template = StrategyTemplate(**template_dict)
        self.templates[template.id] = template
        self._save_template(template)

        logger.info(f"导入模板: {template.name}")
        return template.id

    def clone_template(self, template_id: str, new_name: str, author: str) -> str:
        """克隆模板"""
        original = self.get_template(template_id)
        if not original:
            raise ValueError(f"模板不存在: {template_id}")

        return self.create_template(
            name=new_name,
            template_type=original.type,
            description=original.description,
            author=author,
            variables=original.variables,
            nodes=original.nodes,
            edges=original.edges,
            code_template=original.code_template,
            metadata=original.metadata.copy(),
            parent_template_id=original.id,
        )

    def get_template_history(self, template_id: str) -> List[Dict]:
        """获取模板版本历史"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM template_versions
            WHERE template_id = ?
            ORDER BY created_at DESC
        """,
            (template_id,),
        )

        history = []
        for row in cursor.fetchall():
            history.append(
                {
                    "version_id": row[0],
                    "version": row[2],
                    "data": json.loads(row[3]),
                    "created_at": row[4],
                }
            )

        conn.close()
        return history

    def validate_template(self, template: StrategyTemplate) -> List[str]:
        """验证模板有效性"""
        errors = []

        # 检查必需字段
        if not template.name:
            errors.append("模板名称不能为空")

        if not template.description:
            errors.append("模板描述不能为空")

        # 检查节点连接
        node_ids = {node.id for node in template.nodes}
        for edge in template.edges:
            if edge.get("source") not in node_ids:
                errors.append(f"边的源节点不存在: {edge.get('source')}")
            if edge.get("target") not in node_ids:
                errors.append(f"边的目标节点不存在: {edge.get('target')}")

        # 检查循环依赖
        if self._has_circular_dependency(template.nodes, template.edges):
            errors.append("检测到循环依赖")

        return errors

    def _has_circular_dependency(
        self, nodes: List[StrategyNode], edges: List[Dict]
    ) -> bool:
        """检查是否存在循环依赖"""
        graph = {node.id: [] for node in nodes}
        for edge in edges:
            graph.get(edge.get("source"), []).append(edge.get("target"))

        visited = set()
        rec_stack = set()

        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)

            for neighbor in graph.get(node_id, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node_id)
            return False

        for node_id in graph:
            if node_id not in visited:
                if dfs(node_id):
                    return True

        return False

    def get_statistics(self) -> Dict[str, Any]:
        """获取模板统计信息"""
        stats = {
            "total_templates": len(self.templates),
            "by_type": {},
            "by_status": {},
            "total_versions": 0,
        }

        for template in self.templates.values():
            # 按类型统计
            type_name = template.type.value
            stats["by_type"][type_name] = stats["by_type"].get(type_name, 0) + 1

            # 按状态统计
            status_name = template.status.value
            stats["by_status"][status_name] = stats["by_status"].get(status_name, 0) + 1

        # 统计版本数
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM template_versions")
        stats["total_versions"] = cursor.fetchone()[0]
        conn.close()

        return stats


# 预定义策略模板
def create_predefined_templates(engine: StrategyTemplateEngine):
    """创建预定义策略模板"""

    # 1. 简单移动平均策略
    ma_template_id = engine.create_template(
        name="简单移动平均策略",
        template_type=TemplateType.FULL_STRATEGY,
        description="基于双移动平均线的经典趋势跟踪策略",
        author="System",
        variables=[
            TemplateVariable("short_period", "int", 5, "短期均线周期", True),
            TemplateVariable("long_period", "int", 20, "长期均线周期", True),
            TemplateVariable("symbol", "string", "0700.HK", "交易标的", True),
        ],
        code_template="""
def {{ name }}_strategy(data, short_period={{ short_period }}, long_period={{ long_period }}):
    \"\"\"
    {{ name }} - 简单移动平均策略
    参数: short_period={{ short_period }}, long_period={{ long_period }}
    \"\"\"
    import pandas as pd

    # 计算移动平均线
    data['MA_short'] = data['close'].rolling(window=short_period).mean()
    data['MA_long'] = data['close'].rolling(window=long_period).mean()

    # 生成信号
    signals = []
    position = 0

    for i in range(len(data)):
        if data['MA_short'].iloc[i] > data['MA_long'].iloc[i] and position == 0:
            signals.append(('BUY', data.index[i], data['close'].iloc[i]))
            position = 1
        elif data['MA_short'].iloc[i] < data['MA_long'].iloc[i] and position == 1:
            signals.append(('SELL', data.index[i], data['close'].iloc[i]))
            position = 0

    return signals
        """,
        metadata={"category": "趋势跟踪", "risk_level": "medium"},
    )

    # 2. RSI反转策略
    rsi_template_id = engine.create_template(
        name="RSI反转策略",
        template_type=TemplateType.SIGNAL,
        description="基于RSI指标的超买超卖反转策略",
        author="System",
        variables=[
            TemplateVariable("period", "int", 14, "RSI计算周期", True),
            TemplateVariable("oversold", "int", 30, "超卖阈值", True),
            TemplateVariable("overbought", "int", 70, "超买阈值", True),
        ],
        code_template="""
def rsi_strategy(data, period={{ period }}, oversold={{ oversold }}, overbought={{ overbought }}):
    \"\"\"
    RSI反转策略
    参数: period={{ period }}, oversold={{ oversold }}, overbought={{ overbought }}
    \"\"\"
    import pandas as pd

    # 计算RSI
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))

    # 生成信号
    signals = []
    for i in range(len(data)):
        if data['RSI'].iloc[i] < oversold:
            signals.append(('BUY', data.index[i], data['close'].iloc[i]))
        elif data['RSI'].iloc[i] > overbought:
            signals.append(('SELL', data.index[i], data['close'].iloc[i]))

    return signals
        """,
        metadata={"category": "反转策略", "risk_level": "high"},
    )

    # 3. 动量突破策略
    momentum_template_id = engine.create_template(
        name="动量突破策略",
        template_type=TemplateType.SIGNAL,
        description="基于价格突破的动量策略",
        author="System",
        variables=[
            TemplateVariable("lookback", "int", 20, "回看周期", True),
            TemplateVariable("multiplier", "float", 2.0, "突破倍数", True),
        ],
        code_template="""
def momentum_strategy(data, lookback={{ lookback }}, multiplier={{ multiplier }}):
    \"\"\"
    动量突破策略
    参数: lookback={{ lookback }}, multiplier={{ multiplier }}
    \"\"\"
    # 计算布林带
    data['SMA'] = data['close'].rolling(window=lookback).mean()
    data['STD'] = data['close'].rolling(window=lookback).std()
    data['Upper'] = data['SMA'] + (multiplier * data['STD'])
    data['Lower'] = data['SMA'] - (multiplier * data['STD'])

    # 生成信号
    signals = []
    for i in range(1, len(data)):
        if data['close'].iloc[i] > data['Upper'].iloc[i - 1]:
            signals.append(('BUY', data.index[i], data['close'].iloc[i]))
        elif data['close'].iloc[i] < data['Lower'].iloc[i - 1]:
            signals.append(('SELL', data.index[i], data['close'].iloc[i]))

    return signals
        """,
        metadata={"category": "突破策略", "risk_level": "medium"},
    )

    logger.info("已创建3个预定义策略模板")
    return [ma_template_id, rsi_template_id, momentum_template_id]

"""
基於屬性的訪問控制 (ABAC) 系統
實現基於用戶、資源、環境和操作屬性的動態訪問控制
"""

import json
import logging
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class AttributeType(Enum):
    """屬性類型"""

    USER = "user"
    RESOURCE = "resource"
    ENVIRONMENT = "environment"
    ACTION = "action"


class PolicyEffect(Enum):
    """策略效果"""

    PERMIT = "permit"
    DENY = "deny"


class PolicyType(Enum):
    """策略類型"""

    ALLOW = "allow"
    DENY = "deny"
    REQUIRE = "require"
    OBLIGATE = "obligate"


@dataclass
class Attribute:
    """屬性定義"""

    name: str
    type: AttributeType
    value: Any
    source: str  # 屬性來源 (user, resource, env, action)
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type.value,
            "value": self.value,
            "source": self.source,
            "metadata": self.metadata,
        }


@dataclass
class Condition:
    """條件定義"""

    attribute: str
    operator: str  # ==, !=, >, <, >=, <=, in, not in, contains, matches
    value: Any
    description: str

    def evaluate(self, attributes: Dict[str, Any]) -> bool:
        """評估條件"""
        attr_value = attributes.get(self.attribute)

        try:
            if self.operator == "==":
                return attr_value == self.value
            elif self.operator == "!=":
                return attr_value != self.value
            elif self.operator == ">":
                return attr_value > self.value
            elif self.operator == "<":
                return attr_value < self.value
            elif self.operator == ">=":
                return attr_value >= self.value
            elif self.operator == "<=":
                return attr_value <= self.value
            elif self.operator == "in":
                return attr_value in self.value
            elif self.operator == "not in":
                return attr_value not in self.value
            elif self.operator == "contains":
                if isinstance(attr_value, str) and isinstance(self.value, str):
                    return self.value in attr_value
                return False
            elif self.operator == "matches":
                if isinstance(attr_value, str) and isinstance(self.value, str):
                    return bool(re.search(self.value, attr_value))
                return False
            else:
                logger.warning(f"未知操作符: {self.operator}")
                return False
        except Exception as e:
            logger.error(f"條件評估錯誤: {e}")
            return False


@dataclass
class Policy:
    """策略定義"""

    id: str
    name: str
    description: str
    effect: PolicyEffect
    type: PolicyType
    conditions: List[Condition]
    target_resources: List[str]
    target_actions: List[str]
    target_users: List[str]
    target_environments: List[str]
    is_active: bool
    priority: int
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "effect": self.effect.value,
            "type": self.type.value,
            "conditions": [
                {
                    "attribute": c.attribute,
                    "operator": c.operator,
                    "value": c.value,
                    "description": c.description,
                }
                for c in self.conditions
            ],
            "target_resources": self.target_resources,
            "target_actions": self.target_actions,
            "target_users": self.target_users,
            "target_environments": self.target_environments,
            "is_active": self.is_active,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Policy":
        conditions = [
            Condition(
                attribute=c["attribute"],
                operator=c["operator"],
                value=c["value"],
                description=c["description"],
            )
            for c in data.get("conditions", [])
        ]

        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            effect=PolicyEffect(data["effect"]),
            type=PolicyType(data["type"]),
            conditions=conditions,
            target_resources=data.get("target_resources", []),
            target_actions=data.get("target_actions", []),
            target_users=data.get("target_users", []),
            target_environments=data.get("target_environments", []),
            is_active=data.get("is_active", True),
            priority=data.get("priority", 0),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Context:
    """訪問上下文"""

    user_id: str
    user_attributes: Dict[str, Any]
    resource: str
    resource_attributes: Dict[str, Any]
    action: str
    action_attributes: Dict[str, Any]
    environment: str
    environment_attributes: Dict[str, Any]
    timestamp: datetime
    request_id: str

    def get_all_attributes(self) -> Dict[str, Any]:
        """獲取所有屬性"""
        all_attrs = {}
        all_attrs.update({f"user.{k}": v for k, v in self.user_attributes.items()})
        all_attrs.update(
            {f"resource.{k}": v for k, v in self.resource_attributes.items()}
        )
        all_attrs.update({f"action.{k}": v for k, v in self.action_attributes.items()})
        all_attrs.update(
            {f"env.{k}": v for k, v in self.environment_attributes.items()}
        )
        return all_attrs


class PolicyEngine:
    """策略引擎"""

    def __init__(self):
        self.policies: List[Policy] = []

    def add_policy(self, policy: Policy):
        """添加策略"""
        self.policies.append(policy)
        self.policies.sort(key=lambda p: p.priority, reverse=True)

    def remove_policy(self, policy_id: str):
        """移除策略"""
        self.policies = [p for p in self.policies if p.id != policy_id]

    def evaluate(self, context: Context) -> PolicyEffect:
        """評估上下文並返回策略效果"""
        all_attrs = context.get_all_attributes()

        for policy in self.policies:
            if not policy.is_active:
                continue

            # 檢查目標匹配
            if not self._matches_target(policy, context, all_attrs):
                continue

            # 評估條件
            all_conditions_met = all(
                condition.evaluate(all_attrs) for condition in policy.conditions
            )

            if all_conditions_met:
                logger.debug(f"策略匹配: {policy.id} - {policy.effect}")
                return policy.effect

        # 沒有匹配策略，默認拒絕
        return PolicyEffect.DENY

    def _matches_target(
        self, policy: Policy, context: Context, all_attrs: Dict[str, Any]
    ) -> bool:
        """檢查是否匹配策略目標"""
        # 檢查資源匹配
        if policy.target_resources:
            if context.resource not in policy.target_resources:
                # 檢查通配符或模式匹配
                resource_match = False
                for target in policy.target_resources:
                    if target == "*" or target == context.resource:
                        resource_match = True
                        break
                    # 支持正則表達式
                    if target.startswith("regex:"):
                        pattern = target[6:]
                        if re.search(pattern, context.resource):
                            resource_match = True
                            break
                if not resource_match:
                    return False

        # 檢查操作匹配
        if policy.target_actions and context.action not in policy.target_actions:
            return False

        # 檢查用戶匹配
        if policy.target_users:
            if context.user_id not in policy.target_users:
                # 檢查用戶屬性匹配
                user_match = False
                for target in policy.target_users:
                    if target == "*":
                        user_match = True
                        break
                    if target.startswith("attr:"):
                        attr_name = target[5:]
                        user_attr_value = context.user_attributes.get(attr_name)
                        if user_attr_value:
                            user_match = True
                            break
                if not user_match:
                    return False

        # 檢查環境匹配
        if policy.target_environments:
            if context.environment not in policy.target_environments:
                return False

        return True

    def get_policies(self) -> List[Policy]:
        """獲取所有策略"""
        return self.policies


class AttributeProvider:
    """屬性提供器"""

    def __init__(self):
        self.providers: Dict[str, Callable] = {}

    def register_provider(self, name: str, provider_func: Callable):
        """註冊屬性提供器"""
        self.providers[name] = provider_func

    async def get_attributes(
        self, source: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """獲取指定來源的屬性"""
        if source in self.providers:
            return await self.providers[source](context)
        return {}


class ABACManager:
    """ABAC管理器"""

    def __init__(self, storage_path: str = "abac_policies.json"):
        self.storage_path = storage_path
        self.engine = PolicyEngine()
        self.attribute_provider = AttributeProvider()
        self._init_default_policies()
        self._load_policies()

    def _init_default_policies(self):
        """初始化默認策略"""

        # 策略1: 工作時間內允許管理員訪問
        policy1 = Policy(
            id="policy_001",
            name="工作時間管理員訪問",
            description="工作時間(9 - 18點)內允許管理員進行管理操作",
            effect=PolicyEffect.PERMIT,
            type=PolicyType.ALLOW,
            conditions=[
                Condition(
                    attribute="user.role",
                    operator="==",
                    value="admin",
                    description="用戶角色為管理員",
                ),
                Condition(
                    attribute="env.hour",
                    operator=">=",
                    value=9,
                    description="工作時間開始",
                ),
                Condition(
                    attribute="env.hour",
                    operator="<",
                    value=18,
                    description="工作時間結束",
                ),
            ],
            target_resources=["*"],
            target_actions=["*"],
            target_users=[],
            target_environments=["prod", "dev"],
            is_active=True,
            priority=10,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata={},
        )

        # 策略2: 禁止非工作時間訪問敏感數據
        policy2 = Policy(
            id="policy_002",
            name="非工作時間敏感數據訪問限制",
            description="非工作時間禁止訪問敏感數據",
            effect=PolicyEffect.DENY,
            type=PolicyType.DENY,
            conditions=[
                Condition(
                    attribute="resource.classification",
                    operator="==",
                    value="sensitive",
                    description="資源為敏感數據",
                ),
                Condition(
                    attribute="env.hour",
                    operator="<",
                    value=9,
                    description="非工作時間",
                ),
            ],
            target_resources=["trade_data", "user_data", "financial_data"],
            target_actions=["read", "export"],
            target_users=[],
            target_environments=["prod"],
            is_active=True,
            priority=20,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata={},
        )

        # 策略3: 基於IP白名單的訪問控制
        policy3 = Policy(
            id="policy_003",
            name="IP白名單訪問",
            description="僅允許白名單IP訪問系統",
            effect=PolicyEffect.PERMIT,
            type=PolicyType.REQUIRE,
            conditions=[
                Condition(
                    attribute="env.client_ip",
                    operator="in",
                    value=["192.168.1.0 / 24", "10.0.0.0 / 8"],
                    description="IP在白名單中",
                )
            ],
            target_resources=["*"],
            target_actions=["*"],
            target_users=[],
            target_environments=["prod"],
            is_active=True,
            priority=30,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata={},
        )

        # 策略4: 地理限制
        policy4 = Policy(
            id="policy_004",
            name="地理訪問限制",
            description="限制特定地區的訪問",
            effect=PolicyEffect.DENY,
            type=PolicyType.DENY,
            conditions=[
                Condition(
                    attribute="env.country",
                    operator="in",
                    value=["CN", "RU"],
                    description="來自受限國家",
                )
            ],
            target_resources=["*"],
            target_actions=["*"],
            target_users=[],
            target_environments=["prod"],
            is_active=True,
            priority=25,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata={},
        )

        # 策略5: 設備信任度控制
        policy5 = Policy(
            id="policy_005",
            name="設備信任度控制",
            description="僅允許信任設備進行高風險操作",
            effect=PolicyEffect.PERMIT,
            type=PolicyType.REQUIRE,
            conditions=[
                Condition(
                    attribute="action.risk_level",
                    operator=">=",
                    value=3,
                    description="高風險操作",
                ),
                Condition(
                    attribute="env.device_trusted",
                    operator="==",
                    value=True,
                    description="設備已信任",
                ),
            ],
            target_resources=["*"],
            target_actions=["trade_execute", "data_export", "system_config"],
            target_users=[],
            target_environments=["prod"],
            is_active=True,
            priority=15,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata={},
        )

        for policy in [policy1, policy2, policy3, policy4, policy5]:
            self.engine.add_policy(policy)

    def _load_policies(self):
        """從文件加載策略"""
        try:
            if Path(self.storage_path).exists():
                with open(self.storage_path, "r", encoding="utf - 8") as f:
                    data = json.load(f)
                    for policy_data in data.get("policies", []):
                        policy = Policy.from_dict(policy_data)
                        self.engine.add_policy(policy)
                logger.info(f"已加載 {len(data.get('policies', []))} 個ABAC策略")
        except Exception as e:
            logger.error(f"加載策略失敗: {e}")

    def save_policies(self):
        """保存策略到文件"""
        try:
            policies_data = {
                "policies": [p.to_dict() for p in self.engine.policies],
                "version": "1.0",
                "last_updated": datetime.now().isoformat(),
            }
            with open(self.storage_path, "w", encoding="utf - 8") as f:
                json.dump(policies_data, f, indent=2, ensure_ascii=False)
            logger.info("ABAC策略已保存")
        except Exception as e:
            logger.error(f"保存策略失敗: {e}")

    async def evaluate_access(self, context: Context) -> PolicyEffect:
        """評估訪問請求"""
        result = self.engine.evaluate(context)
        logger.info(
            f"ABAC評估: 用戶={context.user_id}, 資源={context.resource}, "
            f"操作={context.action}, 結果={result.value}"
        )
        return result

    def add_policy(self, policy: Policy):
        """添加策略"""
        self.engine.add_policy(policy)
        self.save_policies()

    def remove_policy(self, policy_id: str):
        """移除策略"""
        self.engine.remove_policy(policy_id)
        self.save_policies()

    def get_policies(self) -> List[Policy]:
        """獲取所有策略"""
        return self.engine.get_policies()

    def register_attribute_provider(self, name: str, provider_func: Callable):
        """註冊屬性提供器"""
        self.attribute_provider.register_provider(name, provider_func)

    def get_policy_summary(self) -> Dict[str, Any]:
        """獲取策略摘要"""
        return {
            "total_policies": len(self.engine.policies),
            "active_policies": sum(1 for p in self.engine.policies if p.is_active),
            "inactive_policies": sum(
                1 for p in self.engine.policies if not p.is_active
            ),
            "policy_types": {
                pt.value: sum(1 for p in self.engine.policies if p.type == pt)
                for pt in PolicyType
            },
            "policy_effects": {
                pe.value: sum(1 for p in self.engine.policies if p.effect == pe)
                for pe in PolicyEffect
            },
        }

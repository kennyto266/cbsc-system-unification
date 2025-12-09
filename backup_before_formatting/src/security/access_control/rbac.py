"""
基於角色的訪問控制 (RBAC) 系統
實現完整的角色層次結構、權限繼承和動態角色管理
"""

import hashlib
import json
import logging
import re
import secrets
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

logger = logging.getLogger(__name__)


class RoleType(Enum):
    """角色類型"""

    ADMIN = "admin"
    TRADER = "trader"
    ANALYST = "analyst"
    VIEWER = "viewer"
    GUEST = "guest"
    AUDITOR = "auditor"
    RISK_MANAGER = "risk_manager"


class PermissionScope(Enum):
    """權限範圍"""

    GLOBAL = "global"
    DEPARTMENT = "department"
    PROJECT = "project"
    RESOURCE = "resource"
    OWN = "own"


@dataclass
class Role:
    """角色定義"""

    id: Optional[int]
    name: str
    role_type: RoleType
    description: str
    parent_role_id: Optional[int]
    is_system_role: bool
    permissions: Set[str]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]

    def __post_init__(self):
        if isinstance(self.permissions, list):
            self.permissions = set(self.permissions)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Role":
        if "role_type" in data and isinstance(data["role_type"], str):
            data["role_type"] = RoleType(data["role_type"])
        if "permissions" in data and isinstance(data["permissions"], list):
            data["permissions"] = set(data["permissions"])
        return cls(**data)


@dataclass
class Permission:
    """權限定義"""

    id: Optional[int]
    name: str
    code: str
    description: str
    resource: str
    action: str
    scope: PermissionScope
    conditions: Dict[str, Any]
    created_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Permission":
        if "scope" in data and isinstance(data["scope"], str):
            data["scope"] = PermissionScope(data["scope"])
        return cls(**data)


@dataclass
class UserRole:
    """用戶角色關聯"""

    id: Optional[int]
    user_id: str
    role_id: int
    assigned_at: datetime
    assigned_by: str
    expires_at: Optional[datetime]
    is_active: bool
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserRole":
        return cls(**data)


@dataclass
class RolePermission:
    """角色權限關聯"""

    id: Optional[int]
    role_id: int
    permission_id: int
    granted_at: datetime
    granted_by: str
    is_active: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RolePermission":
        return cls(**data)


class RoleHierarchy:
    """角色層次結構管理"""

    def __init__(self):
        self.hierarchy: Dict[str, List[str]] = {
            "admin": ["trader", "analyst", "auditor", "risk_manager", "viewer"],
            "trader": ["viewer"],
            "analyst": ["viewer"],
            "risk_manager": ["viewer"],
            "auditor": ["viewer"],
            "viewer": [],
            "guest": [],
        }

    def get_inherited_roles(self, role_name: str) -> Set[str]:
        """獲取角色繼承的所有角色"""
        inherited = set()
        to_process = [role_name]

        while to_process:
            current = to_process.pop(0)
            if current in self.hierarchy:
                for child in self.hierarchy[current]:
                    if child not in inherited:
                        inherited.add(child)
                        to_process.append(child)

        return inherited

    def has_role_permission(self, role_name: str, target_role: str) -> bool:
        """檢查角色是否有目標角色的權限"""
        if role_name == target_role:
            return True

        inherited = self.get_inherited_roles(role_name)
        return target_role in inherited

    def get_all_permissions(self, role_name: str) -> Set[str]:
        """獲取角色及其繼承角色的所有權限"""
        all_roles = {role_name} | self.get_inherited_roles(role_name)
        return all_roles


class RBACManager:
    """RBAC管理器"""

    def __init__(self, db_path: str = "rbac.db"):
        self.db_path = db_path
        self.hierarchy = RoleHierarchy()
        self._init_database()
        self._create_default_roles()

    def _init_database(self):
        """初始化數據庫"""
        with self._get_connection() as conn:
            # 角色表
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    role_type TEXT NOT NULL,
                    description TEXT,
                    parent_role_id INTEGER,
                    is_system_role BOOLEAN DEFAULT FALSE,
                    permissions TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    FOREIGN KEY (parent_role_id) REFERENCES roles(id)
                )
            """
            )

            # 權限表
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS permissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    code TEXT UNIQUE NOT NULL,
                    description TEXT,
                    resource TEXT NOT NULL,
                    action TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    conditions TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # 用戶角色關聯表
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    role_id INTEGER NOT NULL,
                    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    assigned_by TEXT NOT NULL,
                    expires_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    metadata TEXT,
                    FOREIGN KEY (role_id) REFERENCES roles(id),
                    UNIQUE(user_id, role_id)
                )
            """
            )

            # 角色權限關聯表
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS role_permissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role_id INTEGER NOT NULL,
                    permission_id INTEGER NOT NULL,
                    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    granted_by TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (role_id) REFERENCES roles(id),
                    FOREIGN KEY (permission_id) REFERENCES permissions(id),
                    UNIQUE(role_id, permission_id)
                )
            """
            )

            # 創建索引
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON user_roles(user_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_user_roles_role_id ON user_roles(role_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_role_permissions_role_id ON role_permissions(role_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_role_permissions_permission_id ON role_permissions(permission_id)"
            )

            conn.commit()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _create_default_roles(self):
        """創建默認角色"""
        default_roles = [
            Role(
                id=None,
                name="admin",
                role_type=RoleType.ADMIN,
                description="系統管理員 - 擁有所有權限",
                parent_role_id=None,
                is_system_role=True,
                permissions=set(),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                metadata={},
            ),
            Role(
                id=None,
                name="trader",
                role_type=RoleType.TRADER,
                description="交易員 - 執行交易操作",
                parent_role_id=None,
                is_system_role=True,
                permissions={
                    "trade:execute",
                    "trade:view",
                    "portfolio:view",
                    "portfolio:modify",
                    "strategy:execute",
                    "strategy:view",
                    "data:read",
                    "data:export",
                },
                created_at=datetime.now(),
                updated_at=datetime.now(),
                metadata={},
            ),
            Role(
                id=None,
                name="analyst",
                role_type=RoleType.ANALYST,
                description="分析師 - 進行數據分析和策略研究",
                parent_role_id=None,
                is_system_role=True,
                permissions={
                    "data:read",
                    "data:export",
                    "analysis:view",
                    "analysis:create",
                    "strategy:view",
                    "strategy:create",
                    "backtest:execute",
                    "report:view",
                },
                created_at=datetime.now(),
                updated_at=datetime.now(),
                metadata={},
            ),
            Role(
                id=None,
                name="viewer",
                role_type=RoleType.VIEWER,
                description="查看者 - 僅查看權限",
                parent_role_id=None,
                is_system_role=True,
                permissions={"data:read", "report:view"},
                created_at=datetime.now(),
                updated_at=datetime.now(),
                metadata={},
            ),
            Role(
                id=None,
                name="guest",
                role_type=RoleType.GUEST,
                description="訪客 - 有限公開數據訪問",
                parent_role_id=None,
                is_system_role=True,
                permissions={"data:read:public"},
                created_at=datetime.now(),
                updated_at=datetime.now(),
                metadata={},
            ),
            Role(
                id=None,
                name="auditor",
                role_type=RoleType.AUDITOR,
                description="審計員 - 審計和監控",
                parent_role_id=None,
                is_system_role=True,
                permissions={
                    "audit:view",
                    "audit:export",
                    "log:view",
                    "report:view",
                    "user:view",
                    "permission:view",
                    "session:view",
                },
                created_at=datetime.now(),
                updated_at=datetime.now(),
                metadata={},
            ),
            Role(
                id=None,
                name="risk_manager",
                role_type=RoleType.RISK_MANAGER,
                description="風險管理員 - 管理風險和合規",
                parent_role_id=None,
                is_system_role=True,
                permissions={
                    "risk:view",
                    "risk:modify",
                    "compliance:view",
                    "compliance:modify",
                    "alert:view",
                    "alert:modify",
                    "limit:view",
                    "limit:modify",
                    "trade:view",
                    "portfolio:view",
                    "data:read",
                },
                created_at=datetime.now(),
                updated_at=datetime.now(),
                metadata={},
            ),
        ]

        for role in default_roles:
            if not self.get_role_by_name(role.name):
                self.create_role(role)

    def create_role(self, role: Role) -> int:
        """創建角色"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO roles (
                    name, role_type, description, parent_role_id,
                    is_system_role, permissions, created_at, updated_at, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    role.name,
                    role.role_type.value,
                    role.description,
                    role.parent_role_id,
                    role.is_system_role,
                    json.dumps(list(role.permissions)),
                    role.created_at.isoformat(),
                    role.updated_at.isoformat(),
                    json.dumps(role.metadata),
                ),
            )
            conn.commit()
            role_id = cursor.lastrowid
            logger.info(f"創建角色: {role.name} (ID: {role_id})")
            return role_id

    def get_role_by_id(self, role_id: int) -> Optional[Role]:
        """根據ID獲取角色"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM roles WHERE id = ?", (role_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_role(row)
            return None

    def get_role_by_name(self, role_name: str) -> Optional[Role]:
        """根據名稱獲取角色"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM roles WHERE name = ?", (role_name,))
            row = cursor.fetchone()
            if row:
                return self._row_to_role(row)
            return None

    def get_all_roles(self) -> List[Role]:
        """獲取所有角色"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM roles ORDER BY name")
            return [self._row_to_role(row) for row in cursor.fetchall()]

    def _row_to_role(self, row: sqlite3.Row) -> Role:
        """數據庫行轉Role對象"""
        permissions = set()
        if row["permissions"]:
            permissions = set(json.loads(row["permissions"]))

        metadata = {}
        if row["metadata"]:
            metadata = json.loads(row["metadata"])

        return Role(
            id=row["id"],
            name=row["name"],
            role_type=RoleType(row["role_type"]),
            description=row["description"],
            parent_role_id=row["parent_role_id"],
            is_system_role=bool(row["is_system_role"]),
            permissions=permissions,
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            metadata=metadata,
        )

    def assign_role_to_user(
        self,
        user_id: str,
        role_id: int,
        assigned_by: str,
        expires_at: Optional[datetime] = None,
    ) -> int:
        """分配角色給用戶"""
        # 檢查角色是否存在
        if not self.get_role_by_id(role_id):
            raise ValueError(f"角色ID {role_id} 不存在")

        # 檢查是否已分配
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT id FROM user_roles WHERE user_id = ? AND role_id = ?",
                (user_id, role_id),
            )
            if cursor.fetchone():
                # 更新現有分配
                conn.execute(
                    """
                    UPDATE user_roles
                    SET is_active = TRUE, expires_at = ?
                    WHERE user_id = ? AND role_id = ?
                    """,
                    (expires_at.isoformat() if expires_at else None, user_id, role_id),
                )
            else:
                # 創建新分配
                cursor = conn.execute(
                    """
                    INSERT INTO user_roles (
                        user_id, role_id, assigned_at, assigned_by,
                        expires_at, is_active, metadata
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        role_id,
                        datetime.now().isoformat(),
                        assigned_by,
                        expires_at.isoformat() if expires_at else None,
                        True,
                        json.dumps({}),
                    ),
                )
            conn.commit()
            return cursor.lastrowid

    def remove_role_from_user(self, user_id: str, role_id: int) -> bool:
        """移除用戶角色"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "UPDATE user_roles SET is_active = FALSE WHERE user_id = ? AND role_id = ?",
                (user_id, role_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_user_roles(self, user_id: str) -> List[Role]:
        """獲取用戶的所有角色"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT r.* FROM roles r
                JOIN user_roles ur ON r.id = ur.role_id
                WHERE ur.user_id = ? AND ur.is_active = TRUE
                AND (ur.expires_at IS NULL OR ur.expires_at > ?)
                """,
                (user_id, datetime.now().isoformat()),
            )
            return [self._row_to_role(row) for row in cursor.fetchall()]

    def user_has_permission(
        self, user_id: str, permission: str, resource: str = None
    ) -> bool:
        """檢查用戶是否有指定權限"""
        user_roles = self.get_user_roles(user_id)

        if not user_roles:
            return False

        # 收集所有權限（包括繼承的）
        all_permissions = set()
        for role in user_roles:
            all_permissions.update(self.hierarchy.get_all_permissions(role.name))
            all_permissions.update(role.permissions)

        # 檢查權限
        if permission in all_permissions:
            # 如果權限需要資源，檢查資源匹配
            if resource:
                perm_parts = permission.split(":")
                if len(perm_parts) >= 2:
                    resource_pattern = perm_parts[0]
                    action = perm_parts[1]
                    # 實現資源匹配邏輯
                    if resource_pattern == "*" or resource_pattern == resource:
                        return True
            else:
                return True

        return False

    def create_permission(self, permission: Permission) -> int:
        """創建權限"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO permissions (
                    name, code, description, resource, action,
                    scope, conditions, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    permission.name,
                    permission.code,
                    permission.description,
                    permission.resource,
                    permission.action,
                    permission.scope.value,
                    json.dumps(permission.conditions),
                    permission.created_at.isoformat(),
                ),
            )
            conn.commit()
            permission_id = cursor.lastrowid
            logger.info(f"創建權限: {permission.name} (ID: {permission_id})")
            return permission_id

    def assign_permission_to_role(
        self, role_id: int, permission_id: int, granted_by: str
    ) -> int:
        """分配權限給角色"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT OR REPLACE INTO role_permissions (
                    role_id, permission_id, granted_at, granted_by, is_active
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (role_id, permission_id, datetime.now().isoformat(), granted_by, True),
            )
            conn.commit()
            return cursor.lastrowid

    def get_role_permissions(self, role_id: int) -> List[Permission]:
        """獲取角色的所有權限"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT p.* FROM permissions p
                JOIN role_permissions rp ON p.id = rp.permission_id
                WHERE rp.role_id = ? AND rp.is_active = TRUE
                """,
                (role_id,),
            )
            return [self._row_to_permission(row) for row in cursor.fetchall()]

    def _row_to_permission(self, row: sqlite3.Row) -> Permission:
        """數據庫行轉Permission對象"""
        conditions = {}
        if row["conditions"]:
            conditions = json.loads(row["conditions"])

        return Permission(
            id=row["id"],
            name=row["name"],
            code=row["code"],
            description=row["description"],
            resource=row["resource"],
            action=row["action"],
            scope=PermissionScope(row["scope"]),
            conditions=conditions,
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def delete_role(self, role_id: int) -> bool:
        """刪除角色（僅非系統角色）"""
        role = self.get_role_by_id(role_id)
        if not role:
            return False

        if role.is_system_role:
            raise ValueError("不能刪除系統角色")

        with self._get_connection() as conn:
            # 檢查是否有用戶使用此角色
            cursor = conn.execute(
                "SELECT COUNT(*) FROM user_roles WHERE role_id = ? AND is_active = TRUE",
                (role_id,),
            )
            count = cursor.fetchone()[0]
            if count > 0:
                raise ValueError("無法刪除正在使用的角色")

            # 刪除角色權限關聯
            conn.execute("DELETE FROM role_permissions WHERE role_id = ?", (role_id,))

            # 刪除角色
            conn.execute("DELETE FROM roles WHERE id = ?", (role_id,))
            conn.commit()

            logger.info(f"刪除角色 ID: {role_id}")
            return True

    def get_permission_matrix(self) -> Dict[str, Dict[str, bool]]:
        """獲取權限矩陣"""
        roles = self.get_all_roles()
        permissions = self._get_all_permissions()

        matrix = {}
        for role in roles:
            role_name = role.name
            matrix[role_name] = {}
            for perm in permissions:
                matrix[role_name][perm.code] = self._has_role_permission(
                    role_name, perm.code
                )

        return matrix

    def _get_all_permissions(self) -> List[Permission]:
        """獲取所有權限"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM permissions")
            return [self._row_to_permission(row) for row in cursor.fetchall()]

    def _has_role_permission(self, role_name: str, permission_code: str) -> bool:
        """檢查角色是否有權限"""
        role = self.get_role_by_name(role_name)
        if not role:
            return False

        # 檢查直接權限
        if permission_code in role.permissions:
            return True

        # 檢查繼承權限
        inherited_roles = self.hierarchy.get_inherited_roles(role_name)
        for inherited_role in inherited_roles:
            role_obj = self.get_role_by_name(inherited_role)
            if role_obj and permission_code in role_obj.permissions:
                return True

        return False

    def export_policy(self) -> Dict[str, Any]:
        """導出RBAC策略"""
        return {
            "roles": [role.to_dict() for role in self.get_all_roles()],
            "permissions": [perm.to_dict() for perm in self._get_all_permissions()],
            "hierarchy": self.hierarchy.hierarchy,
        }

    def import_policy(self, policy: Dict[str, Any]):
        """導入RBAC策略"""
        with self._get_connection() as conn:
            # 清除現有數據
            conn.execute("DELETE FROM role_permissions")
            conn.execute("DELETE FROM user_roles")
            conn.execute("DELETE FROM permissions")
            conn.execute("DELETE FROM roles")

            # 導入角色
            role_map = {}
            for role_data in policy.get("roles", []):
                role = Role.from_dict(role_data)
                role_id = self.create_role(role)
                role_map[role.id] = role_id

            # 導入權限
            perm_map = {}
            for perm_data in policy.get("permissions", []):
                permission = Permission.from_dict(perm_data)
                perm_id = self.create_permission(permission)
                perm_map[permission.id] = perm_id

            conn.commit()
            logger.info("RBAC策略導入完成")

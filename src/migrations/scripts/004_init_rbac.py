"""
Initialize RBAC System
初始化RBAC系統

創建默認角色和權限。
"""

import sys
import os
from datetime import datetime, timezone

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from sqlalchemy.orm import Session
from core.database import engine
from models.user import User, Role, Permission
from models.rbac_models import (
    DynamicPermission, TemporaryAuthorization, PermissionAuditLog,
    PermissionLevel, ResourceType, ResourceAction
)


def create_default_permissions(db: Session):
    """創建默認權限"""
    permissions = [
        # System permissions
        {
            "code": "system:admin",
            "name": "系統管理",
            "description": "完整的系統管理權限",
            "category": "system",
            "resource": "system",
            "action": "admin",
            "level": 100,
            "is_system_permission": True
        },
        {
            "code": "system:monitor",
            "name": "系統監控",
            "description": "查看系統狀態和監控信息",
            "category": "system",
            "resource": "system",
            "action": "read",
            "level": 50,
            "is_system_permission": True
        },

        # User management permissions
        {
            "code": "user:create",
            "name": "創建用戶",
            "description": "創建新用戶賬戶",
            "category": "user",
            "resource": "user",
            "action": "create",
            "level": 80,
            "is_system_permission": True
        },
        {
            "code": "user:read",
            "name": "查看用戶",
            "description": "查看用戶信息",
            "category": "user",
            "resource": "user",
            "action": "read",
            "level": 40,
            "is_system_permission": True
        },
        {
            "code": "user:update",
            "name": "更新用戶",
            "description": "更新用戶信息",
            "category": "user",
            "resource": "user",
            "action": "update",
            "level": 60,
            "is_system_permission": True
        },
        {
            "code": "user:delete",
            "name": "刪除用戶",
            "description": "刪除用戶賬戶",
            "category": "user",
            "resource": "user",
            "action": "delete",
            "level": 90,
            "is_system_permission": True
        },

        # Role management permissions
        {
            "code": "role:create",
            "name": "創建角色",
            "description": "創建新角色",
            "category": "role",
            "resource": "role",
            "action": "create",
            "level": 80,
            "is_system_permission": True
        },
        {
            "code": "role:read",
            "name": "查看角色",
            "description": "查看角色信息",
            "category": "role",
            "resource": "role",
            "action": "read",
            "level": 40,
            "is_system_permission": True
        },
        {
            "code": "role:update",
            "name": "更新角色",
            "description": "更新角色權限",
            "category": "role",
            "resource": "role",
            "action": "update",
            "level": 70,
            "is_system_permission": True
        },
        {
            "code": "role:delete",
            "name": "刪除角色",
            "description": "刪除角色",
            "category": "role",
            "resource": "role",
            "action": "delete",
            "level": 90,
            "is_system_permission": True
        },

        # Strategy permissions
        {
            "code": "strategy:create",
            "name": "創建策略",
            "description": "創建新的交易策略",
            "category": "strategy",
            "resource": "strategy",
            "action": "create",
            "level": 30
        },
        {
            "code": "strategy:read",
            "name": "查看策略",
            "description": "查看策略詳情",
            "category": "strategy",
            "resource": "strategy",
            "action": "read",
            "level": 20
        },
        {
            "code": "strategy:update",
            "name": "更新策略",
            "description": "修改策略參數",
            "category": "strategy",
            "resource": "strategy",
            "action": "update",
            "level": 40
        },
        {
            "code": "strategy:delete",
            "name": "刪除策略",
            "description": "刪除策略",
            "category": "strategy",
            "resource": "strategy",
            "action": "delete",
            "level": 50
        },
        {
            "code": "strategy:execute",
            "name": "執行策略",
            "description": "運行策略",
            "category": "strategy",
            "resource": "strategy",
            "action": "execute",
            "level": 50
        },
        {
            "code": "strategy:approve",
            "name": "批准策略",
            "description": "批准策略上線",
            "category": "strategy",
            "resource": "strategy",
            "action": "approve",
            "level": 70,
            "is_system_permission": True
        },

        # Backtest permissions
        {
            "code": "backtest:create",
            "name": "創建回測",
            "description": "創建回測任務",
            "category": "backtest",
            "resource": "backtest",
            "action": "create",
            "level": 30
        },
        {
            "code": "backtest:read",
            "name": "查看回測",
            "description": "查看回測結果",
            "category": "backtest",
            "resource": "backtest",
            "action": "read",
            "level": 20
        },
        {
            "code": "backtest:update",
            "name": "更新回測",
            "description": "修改回測參數",
            "category": "backtest",
            "resource": "backtest",
            "action": "update",
            "level": 40
        },
        {
            "code": "backtest:delete",
            "name": "刪除回測",
            "description": "刪除回測記錄",
            "category": "backtest",
            "resource": "backtest",
            "action": "delete",
            "level": 50
        },
        {
            "code": "backtest:execute",
            "name": "執行回測",
            "description": "運行回測",
            "category": "backtest",
            "resource": "backtest",
            "action": "execute",
            "level": 40
        },

        # Trading permissions
        {
            "code": "trading:create",
            "name": "創建訂單",
            "description": "創建交易訂單",
            "category": "trading",
            "resource": "trading",
            "action": "create",
            "level": 60
        },
        {
            "code": "trading:read",
            "name": "查看交易",
            "description": "查看交易記錄",
            "category": "trading",
            "resource": "trading",
            "action": "read",
            "level": 30
        },
        {
            "code": "trading:update",
            "name": "更新訂單",
            "description": "修改交易訂單",
            "category": "trading",
            "resource": "trading",
            "action": "update",
            "level": 70
        },
        {
            "code": "trading:delete",
            "name": "取消訂單",
            "description": "取消交易訂單",
            "category": "trading",
            "resource": "trading",
            "action": "delete",
            "level": 70
        },
        {
            "code": "trading:execute",
            "name": "執行交易",
            "description": "執行交易操作",
            "category": "trading",
            "resource": "trading",
            "action": "execute",
            "level": 80
        },
        {
            "code": "trading:approve",
            "name": "批准交易",
            "description": "批准大額交易",
            "category": "trading",
            "resource": "trading",
            "action": "approve",
            "level": 90,
            "is_system_permission": True
        },

        # Portfolio permissions
        {
            "code": "portfolio:create",
            "name": "創建投資組合",
            "description": "創建投資組合",
            "category": "portfolio",
            "resource": "portfolio",
            "action": "create",
            "level": 30
        },
        {
            "code": "portfolio:read",
            "name": "查看投資組合",
            "description": "查看投資組合詳情",
            "category": "portfolio",
            "resource": "portfolio",
            "action": "read",
            "level": 20
        },
        {
            "code": "portfolio:update",
            "name": "更新投資組合",
            "description": "調整投資組合",
            "category": "portfolio",
            "resource": "portfolio",
            "action": "update",
            "level": 40
        },
        {
            "code": "portfolio:delete",
            "name": "刪除投資組合",
            "description": "刪除投資組合",
            "category": "portfolio",
            "resource": "portfolio",
            "action": "delete",
            "level": 50
        },

        # Report permissions
        {
            "code": "report:create",
            "name": "創建報告",
            "description": "生成分析報告",
            "category": "report",
            "resource": "report",
            "action": "create",
            "level": 40
        },
        {
            "code": "report:read",
            "name": "查看報告",
            "description": "查看分析報告",
            "category": "report",
            "resource": "report",
            "action": "read",
            "level": 20
        },
        {
            "code": "report:update",
            "name": "更新報告",
            "description": "修改報告內容",
            "category": "report",
            "resource": "report",
            "action": "update",
            "level": 50
        },
        {
            "code": "report:delete",
            "name": "刪除報告",
            "description": "刪除報告",
            "category": "report",
            "resource": "report",
            "action": "delete",
            "level": 60
        },
        {
            "code": "report:export",
            "name": "導出報告",
            "description": "導出報告數據",
            "category": "report",
            "resource": "report",
            "action": "export",
            "level": 50
        },

        # Market data permissions
        {
            "code": "market_data:read",
            "name": "查看市場數據",
            "description": "訪問市場數據",
            "category": "market_data",
            "resource": "market_data",
            "action": "read",
            "level": 10
        },
        {
            "code": "market_data:export",
            "name": "導出市場數據",
            "description": "導出歷史市場數據",
            "category": "market_data",
            "resource": "market_data",
            "action": "export",
            "level": 40
        }
    ]

    created_permissions = []
    for perm_data in permissions:
        # Check if permission already exists
        existing = db.query(Permission).filter(
            Permission.code == perm_data["code"]
        ).first()

        if not existing:
            permission = Permission(**perm_data)
            db.add(permission)
            created_permissions.append(perm_data["code"])

    db.commit()
    return created_permissions


def create_default_roles(db: Session):
    """創建默認角色"""
    roles = [
        {
            "name": "super_admin",
            "display_name": "超級管理員",
            "description": "擁有所有權限的超級管理員",
            "level": 100,
            "is_system_role": True,
            "permissions": [
                "system:admin",
                "system:monitor",
                "user:create",
                "user:read",
                "user:update",
                "user:delete",
                "role:create",
                "role:read",
                "role:update",
                "role:delete",
                "strategy:create",
                "strategy:read",
                "strategy:update",
                "strategy:delete",
                "strategy:execute",
                "strategy:approve",
                "backtest:create",
                "backtest:read",
                "backtest:update",
                "backtest:delete",
                "backtest:execute",
                "trading:create",
                "trading:read",
                "trading:update",
                "trading:delete",
                "trading:execute",
                "trading:approve",
                "portfolio:create",
                "portfolio:read",
                "portfolio:update",
                "portfolio:delete",
                "report:create",
                "report:read",
                "report:update",
                "report:delete",
                "report:export",
                "market_data:read",
                "market_data:export"
            ]
        },
        {
            "name": "admin",
            "display_name": "管理員",
            "description": "系統管理員，擁有大部分管理權限",
            "level": 90,
            "is_system_role": True,
            "permissions": [
                "system:monitor",
                "user:create",
                "user:read",
                "user:update",
                "role:read",
                "strategy:create",
                "strategy:read",
                "strategy:update",
                "strategy:delete",
                "strategy:execute",
                "strategy:approve",
                "backtest:create",
                "backtest:read",
                "backtest:update",
                "backtest:delete",
                "backtest:execute",
                "trading:read",
                "trading:approve",
                "portfolio:create",
                "portfolio:read",
                "portfolio:update",
                "portfolio:delete",
                "report:create",
                "report:read",
                "report:update",
                "report:delete",
                "report:export",
                "market_data:read",
                "market_data:export"
            ]
        },
        {
            "name": "strategy_admin",
            "display_name": "策略管理員",
            "description": "負責策略管理和批准",
            "level": 70,
            "is_system_role": True,
            "permissions": [
                "system:monitor",
                "user:read",
                "strategy:create",
                "strategy:read",
                "strategy:update",
                "strategy:delete",
                "strategy:execute",
                "strategy:approve",
                "backtest:create",
                "backtest:read",
                "backtest:update",
                "backtest:delete",
                "backtest:execute",
                "trading:read",
                "trading:approve",
                "portfolio:read",
                "portfolio:update",
                "report:create",
                "report:read",
                "report:export",
                "market_data:read"
            ]
        },
        {
            "name": "analyst",
            "display_name": "分析師",
            "description": "數據分析和報告生成",
            "level": 50,
            "is_system_role": True,
            "permissions": [
                "user:read",
                "strategy:read",
                "backtest:read",
                "backtest:execute",
                "trading:read",
                "portfolio:read",
                "report:create",
                "report:read",
                "report:export",
                "market_data:read",
                "market_data:export"
            ]
        },
        {
            "name": "trader",
            "display_name": "交易員",
            "description": "執行交易操作",
            "level": 60,
            "is_system_role": True,
            "permissions": [
                "strategy:read",
                "strategy:execute",
                "backtest:read",
                "backtest:execute",
                "trading:create",
                "trading:read",
                "trading:update",
                "trading:delete",
                "trading:execute",
                "portfolio:create",
                "portfolio:read",
                "portfolio:update",
                "report:read",
                "market_data:read"
            ]
        },
        {
            "name": "user",
            "display_name": "普通用戶",
            "description": "標準用戶權限",
            "level": 30,
            "is_system_role": True,
            "permissions": [
                "strategy:create",
                "strategy:read",
                "strategy:update",
                "strategy:delete",
                "strategy:execute",
                "backtest:create",
                "backtest:read",
                "backtest:update",
                "backtest:delete",
                "backtest:execute",
                "portfolio:create",
                "portfolio:read",
                "portfolio:update",
                "portfolio:delete",
                "report:read",
                "market_data:read"
            ]
        }
    ]

    created_roles = []
    for role_data in roles:
        # Check if role already exists
        existing = db.query(Role).filter(Role.name == role_data["name"]).first()

        if not existing:
            permissions = role_data.pop("permissions")
            role = Role(**role_data)
            db.add(role)
            db.flush()  # Get role ID without committing

            # Assign permissions to role
            for perm_code in permissions:
                permission = db.query(Permission).filter(
                    Permission.code == perm_code
                ).first()
                if permission:
                    role.permissions.append(permission)

            created_roles.append(role_data["name"])

    db.commit()
    return created_roles


def main():
    """主函數"""
    print("Initializing RBAC system...")

    # Create database session
    db = Session(engine)

    try:
        # Create default permissions
        print("Creating default permissions...")
        created_permissions = create_default_permissions(db)
        print(f"Created {len(created_permissions)} permissions")

        # Create default roles
        print("Creating default roles...")
        created_roles = create_default_roles(db)
        print(f"Created {len(created_roles)} roles")

        # Print summary
        print("\nRBAC System Initialization Complete!")
        print("\nCreated Permissions:")
        for perm in created_permissions:
            print(f"  - {perm}")

        print("\nCreated Roles:")
        for role in created_roles:
            print(f"  - {role}")

        print("\nRole Hierarchy:")
        print("  1. super_admin (Level 100) - Full system access")
        print("  2. admin (Level 90) - System administration")
        print("  3. strategy_admin (Level 70) - Strategy management")
        print("  4. trader (Level 60) - Trading operations")
        print("  5. analyst (Level 50) - Data analysis")
        print("  6. user (Level 30) - Basic user access")

    except Exception as e:
        print(f"Error initializing RBAC system: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
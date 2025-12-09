"""
港股量化交易系統 - 訪問控制系統測試
測試RBAC、ABAC、MFA、會話管理和API訪問控制
"""

import asyncio
import json
import os
import sqlite3
import tempfile
from datetime import datetime, timedelta
from typing import Any, Dict

import pytest

from src.security.access_control.abac import (
    ABACManager,
    Condition,
    Context,
    Policy,
    PolicyEffect,
    PolicyType,
)
from src.security.access_control.api_access import (
    APIAccessManager,
    APIKey,
    APIKeyStatus,
    EndpointPermission,
)
from src.security.access_control.mfa import DeviceTrustLevel, MFAManager, MFAMethodType
from src.security.access_control.rbac import (
    Permission,
    PermissionScope,
    RBACManager,
    Role,
    RoleType,
)
from src.security.access_control.session import (
    SessionManager,
    SessionStatus,
    TokenManager,
)


class TestRBAC:
    """測試RBAC系統"""

    @pytest.fixture
    def rbac_manager(self):
        """創建RBAC管理器"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test_rbac.db")
            manager = RBACManager(db_path)
            yield manager

    def test_create_role(self, rbac_manager):
        """測試創建角色"""
        role = Role(
            id=None,
            name="test_role",
            role_type=RoleType.VIEWER,
            description="測試角色",
            parent_role_id=None,
            is_system_role=False,
            permissions={"data:read"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata={},
        )

        role_id = rbac_manager.create_role(role)
        assert role_id is not None

        retrieved_role = rbac_manager.get_role_by_id(role_id)
        assert retrieved_role is not None
        assert retrieved_role.name == "test_role"
        assert retrieved_role.role_type == RoleType.VIEWER

    def test_assign_role_to_user(self, rbac_manager):
        """測試分配角色給用戶"""
        # 獲取現有角色
        viewer_role = rbac_manager.get_role_by_name("viewer")
        assert viewer_role is not None

        # 分配角色
        assignment_id = rbac_manager.assign_role_to_user(
            user_id="test_user", role_id=viewer_role.id, assigned_by="admin"
        )
        assert assignment_id is not None

        # 驗證用戶角色
        user_roles = rbac_manager.get_user_roles("test_user")
        assert len(user_roles) == 1
        assert user_roles[0].name == "viewer"

    def test_user_permission_check(self, rbac_manager):
        """測試用戶權限檢查"""
        # 分配viewer角色
        viewer_role = rbac_manager.get_role_by_name("viewer")
        rbac_manager.assign_role_to_user("test_user", viewer_role.id, "admin")

        # 檢查權限
        has_read = rbac_manager.user_has_permission("test_user", "data:read")
        has_write = rbac_manager.user_has_permission("test_user", "data:write")

        assert has_read is True
        assert has_write is False

    def test_role_hierarchy(self, rbac_manager):
        """測試角色層次結構"""
        # Admin應該有trader的所有權限
        admin_role = rbac_manager.get_role_by_name("admin")
        trader_role = rbac_manager.get_role_by_name("trader")

        assert admin_role is not None
        assert trader_role is not None

        # 檢查繼承
        inherited = rbac_manager.hierarchy.get_inherited_roles("admin")
        assert "trader" in inherited


class TestABAC:
    """測試ABAC系統"""

    @pytest.fixture
    def abac_manager(self):
        """創建ABAC管理器"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            policy_path = os.path.join(tmp_dir, "test_abac.json")
            manager = ABACManager(policy_path)
            yield manager

    def test_create_policy(self, abac_manager):
        """測試創建ABAC策略"""
        policy = Policy(
            id="test_policy",
            name="測試策略",
            description="這是一個測試策略",
            effect=PolicyEffect.PERMIT,
            type=PolicyType.ALLOW,
            conditions=[
                Condition(
                    attribute="user.role",
                    operator="==",
                    value="admin",
                    description="用戶角色為admin",
                )
            ],
            target_resources=["*"],
            target_actions=["*"],
            target_users=[],
            target_environments=[],
            is_active=True,
            priority=10,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata={},
        )

        abac_manager.add_policy(policy)
        policies = abac_manager.get_policies()

        assert len(policies) >= 1
        assert any(p.id == "test_policy" for p in policies)

    async def test_evaluate_access(self, abac_manager):
        """測試訪問評估"""
        # 創建測試上下文
        context = Context(
            user_id="test_user",
            user_attributes={"role": "admin"},
            resource="/api / data",
            resource_attributes={},
            action="read",
            action_attributes={},
            environment="prod",
            environment_attributes={"hour": 10},
            timestamp=datetime.now(),
            request_id="test_req_001",
        )

        # 評估訪問
        result = await abac_manager.evaluate_access(context)

        # Admin在工作時間應該被允許
        assert result == PolicyEffect.PERMIT

    def test_policy_summary(self, abac_manager):
        """測試策略摘要"""
        summary = abac_manager.get_policy_summary()

        assert "total_policies" in summary
        assert "active_policies" in summary
        assert summary["total_policies"] > 0


class TestMFA:
    """測試MFA系統"""

    @pytest.fixture
    def mfa_manager(self):
        """創建MFA管理器"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test_mfa.db")
            manager = MFAManager(db_path)
            yield manager

    async def test_setup_totp(self, mfa_manager):
        """測試設置TOTP"""
        secret, qr_code = await mfa_manager.setup_totp("test_user", "test@example.com")

        assert secret is not None
        assert len(secret) > 0
        assert qr_code is not None
        assert len(qr_code) > 0

    async def test_verify_totp(self, mfa_manager):
        """測試驗證TOTP"""
        # 設置TOTP
        secret, _ = await mfa_manager.setup_totp("test_user", "test@example.com")

        # 生成有效令牌（使用pyotp）
        import pyotp

        totp = pyotp.TOTP(secret)
        valid_token = totp.now()

        # 驗證令牌
        is_valid = await mfa_manager.verify_totp("test_user", valid_token)
        assert is_valid is True

        # 驗證無效令牌
        is_valid = await mfa_manager.verify_totp("test_user", "000000")
        assert is_valid is False

    def test_generate_backup_codes(self, mfa_manager):
        """測試生成備份代碼"""
        codes = mfa_manager.generate_backup_codes("test_user", 5)

        assert len(codes) == 5
        assert all(len(code) == 8 for code in codes)

    def test_verify_backup_code(self, mfa_manager):
        """測試驗證備份代碼"""
        # 生成備份代碼
        codes = mfa_manager.generate_backup_codes("test_user", 10)
        first_code = codes[0]

        # 驗證備份代碼
        is_valid = mfa_manager.verify_backup_code("test_user", first_code)
        assert is_valid is True

        # 再次使用同一個代碼應該失敗
        is_valid = mfa_manager.verify_backup_code("test_user", first_code)
        assert is_valid is False

    def test_register_device(self, mfa_manager):
        """測試註冊設備"""
        device_info = {
            "device_id": "device_001",
            "device_name": "Test Device",
            "device_type": "desktop",
            "browser": "Chrome",
            "os": "Windows",
            "ip_address": "192.168.1.1",
            "location": "HK",
            "fingerprint": "abc123",
        }

        device = mfa_manager.register_device("test_user", device_info)

        assert device.device_id == "device_001"
        assert device.user_id == "test_user"
        assert device.device_name == "Test Device"

    def test_trust_device(self, mfa_manager):
        """測試信任設備"""
        # 註冊設備
        device_info = {"device_id": "device_001"}
        mfa_manager.register_device("test_user", device_info)

        # 信任設備
        success = mfa_manager.trust_device("test_user", "device_001")
        assert success is True

        # 獲取設備列表
        devices = mfa_manager.get_user_devices("test_user")
        assert len(devices) == 1
        assert devices[0].is_trusted is True


class TestSession:
    """測試會話管理"""

    @pytest.fixture
    def session_manager(self):
        """創建會話管理器"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test_sessions.db")
            token_manager = TokenManager("test_secret_key")
            manager = SessionManager(
                db_path=db_path,
                token_manager=token_manager,
                idle_timeout=1800,
                absolute_timeout=86400,
                max_concurrent_sessions=5,
            )
            yield manager

    def test_create_session(self, session_manager):
        """測試創建會話"""
        session, access_token, refresh_token, id_token = session_manager.create_session(
            user_id="test_user",
            ip_address="192.168.1.1",
            user_agent="Test Browser",
            device_id="device_001",
            device_name="Test Device",
        )

        assert session.session_id is not None
        assert session.user_id == "test_user"
        assert access_token is not None
        assert refresh_token is not None
        assert id_token is not None

    def test_get_session(self, session_manager):
        """測試獲取會話"""
        # 創建會話
        created_session, _, _, _ = session_manager.create_session(
            user_id="test_user",
            ip_address="192.168.1.1",
            user_agent="Test Browser",
            device_id="device_001",
            device_name="Test Device",
        )

        # 獲取會話
        retrieved_session = session_manager.get_session(created_session.session_id)
        assert retrieved_session is not None
        assert retrieved_session.session_id == created_session.session_id
        assert retrieved_session.user_id == "test_user"

    def test_update_activity(self, session_manager):
        """測試更新活動時間"""
        # 創建會話
        session, _, _, _ = session_manager.create_session(
            user_id="test_user",
            ip_address="192.168.1.1",
            user_agent="Test Browser",
            device_id="device_001",
            device_name="Test Device",
        )

        # 更新活動
        success = session_manager.update_activity(session.session_id)
        assert success is True

    def test_terminate_session(self, session_manager):
        """測試終止會話"""
        # 創建會話
        session, _, _, _ = session_manager.create_session(
            user_id="test_user",
            ip_address="192.168.1.1",
            user_agent="Test Browser",
            device_id="device_001",
            device_name="Test Device",
        )

        # 終止會話
        success = session_manager.terminate_session(
            session.session_id, "test_termination"
        )
        assert success is True

        # 驗證會話已終止
        terminated_session = session_manager.get_session(session.session_id)
        assert terminated_session is not None
        assert terminated_session.status == SessionStatus.TERMINATED

    def test_concurrent_session_limit(self, session_manager):
        """測試並發會話限制"""
        user_id = "test_user"

        # 創建多個會話
        sessions = []
        for i in range(6):  # 超過限制
            session, _, _, _ = session_manager.create_session(
                user_id=user_id,
                ip_address=f"192.168.1.{i}",
                user_agent="Test Browser",
                device_id=f"device_{i:03d}",
                device_name=f"Device {i}",
            )
            sessions.append(session)

        # 檢查會話數量（應該被限制）
        user_sessions = session_manager.get_user_sessions(user_id)
        assert len(user_sessions) <= 5  # 最大並發數

    def test_token_verification(self, session_manager):
        """測試令牌驗證"""
        # 創建會話
        session, access_token, _, _ = session_manager.create_session(
            user_id="test_user",
            ip_address="192.168.1.1",
            user_agent="Test Browser",
            device_id="device_001",
            device_name="Test Device",
        )

        # 驗證令牌
        payload = session_manager.token_manager.verify_token(access_token)
        assert payload is not None
        assert payload.get("user_id") == "test_user"
        assert payload.get("session_id") == session.session_id

    def test_session_stats(self, session_manager):
        """測試會話統計"""
        # 創建一些會話
        for i in range(3):
            session_manager.create_session(
                user_id=f"user_{i}",
                ip_address="192.168.1.1",
                user_agent="Test Browser",
                device_id=f"device_{i:03d}",
                device_name=f"Device {i}",
            )

        # 獲取統計
        stats = session_manager.get_session_stats()
        assert stats["active_sessions"] == 3
        assert stats["active_users"] == 3


class TestAPIAccess:
    """測試API訪問控制"""

    @pytest.fixture
    def api_manager(self):
        """創建API訪問管理器"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test_api.db")
            manager = APIAccessManager(db_path)
            yield manager

    def test_generate_api_key(self, api_manager):
        """測試生成API密鑰"""
        api_key, api_key_obj = api_manager.generate_api_key(
            user_id="test_user",
            name="Test API Key",
            scopes=["data:read", "data:write"],
            rate_limit=100,
        )

        assert api_key is not None
        assert "_" in api_key  # 應該有前綴
        assert api_key_obj.user_id == "test_user"
        assert api_key_obj.name == "Test API Key"
        assert "data:read" in api_key_obj.scopes
        assert api_key_obj.rate_limit == 100

    def test_validate_api_key(self, api_manager):
        """測試驗證API密鑰"""
        # 生成API密鑰
        api_key, _ = api_manager.generate_api_key(
            user_id="test_user", name="Test API Key", scopes=["data:read"]
        )

        # 驗證API密鑰
        validated_key = api_manager.validate_api_key(api_key)
        assert validated_key is not None
        assert validated_key.user_id == "test_user"
        assert "data:read" in validated_key.scopes

        # 驗證無效API密鑰
        invalid_key = api_manager.validate_api_key("invalid_key_123")
        assert invalid_key is None

    def test_check_endpoint_permission(self, api_manager):
        """測試檢查端點權限"""
        # 檢查公開端點
        has_perm, _ = api_manager.check_endpoint_permission("GET", "/api / v1 / health")
        assert has_perm is True

        # 檢查需要權限的端點（無API密鑰）
        has_perm, error = api_manager.check_endpoint_permission(
            "GET", "/api / v1 / data / test"
        )
        assert has_perm is True  # 將在後續RBAC檢查中拒絕

    def test_rate_limit(self, api_manager):
        """測試速率限制"""
        # 生成API密鑰
        api_key, api_key_obj = api_manager.generate_api_key(
            user_id="test_user",
            name="Test API Key",
            scopes=["data:read"],
            rate_limit=5,  # 低速率限制用於測試
        )

        validated_key = api_manager.validate_api_key(api_key)

        # 模擬多次請求
        for i in range(10):
            is_limited, rate_info = api_manager.check_rate_limit(
                validated_key, "/api / v1 / data / test", "GET"
            )

            if i < 5:
                assert is_limited is False
            else:
                assert is_limited is True
                assert rate_info["remaining"] == 0

    def test_revoke_api_key(self, api_manager):
        """測試撤銷API密鑰"""
        # 生成API密鑰
        api_key, api_key_obj = api_manager.generate_api_key(
            user_id="test_user", name="Test API Key", scopes=["data:read"]
        )

        # 撤銷API密鑰
        success = api_manager.revoke_api_key(api_key_obj.key_id)
        assert success is True

        # 驗證API密鑰已撤銷
        validated_key = api_manager.validate_api_key(api_key)
        assert validated_key is None

    def test_get_user_api_keys(self, api_manager):
        """測試獲取用戶的API密鑰"""
        # 為用戶生成多個API密鑰
        for i in range(3):
            api_manager.generate_api_key(
                user_id="test_user", name=f"Test API Key {i + 1}", scopes=["data:read"]
            )

        # 獲取用戶的API密鑰
        keys = api_manager.get_user_api_keys("test_user")
        assert len(keys) == 3

    def test_add_endpoint_permission(self, api_manager):
        """測試添加端點權限"""
        endpoint = EndpointPermission(
            method="POST",
            path_pattern="/api / v1 / custom/.*",
            required_scopes={"custom:access"},
            required_roles=set(),
            rate_limit=30,
            is_public=False,
            metadata={},
        )

        # 添加端點權限
        api_manager.add_endpoint_permission(endpoint)

        # 檢查是否已添加
        has_perm, _ = api_manager.check_endpoint_permission(
            "POST", "/api / v1 / custom / test"
        )
        assert has_perm is True


class TestIntegration:
    """集成測試"""

    @pytest.fixture
    def full_access_control(self):
        """創建完整的訪問控制系統"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            rbac_db = os.path.join(tmp_dir, "rbac.db")
            mfa_db = os.path.join(tmp_dir, "mfa.db")
            session_db = os.path.join(tmp_dir, "session.db")
            api_db = os.path.join(tmp_dir, "api.db")
            abac_policy = os.path.join(tmp_dir, "abac.json")

            rbac = RBACManager(rbac_db)
            mfa = MFAManager(mfa_db)
            session = SessionManager(session_db, token_manager=TokenManager("test_key"))
            api = APIAccessManager(api_db)
            abac = ABACManager(abac_policy)

            return {
                "rbac": rbac,
                "mfa": mfa,
                "session": session,
                "api": api,
                "abac": abac,
            }

    async def test_full_authentication_flow(self, full_access_control):
        """測試完整的認證流程"""
        rbac = full_access_control["rbac"]
        mfa = full_access_control["mfa"]
        session = full_access_control["session"]

        # 1. 用戶登錄
        session_obj, access_token, refresh_token, id_token = session.create_session(
            user_id="test_user",
            ip_address="192.168.1.1",
            user_agent="Test Browser",
            device_id="device_001",
            device_name="Test Device",
        )

        assert session_obj is not None
        assert access_token is not None

        # 2. 分配角色
        trader_role = rbac.get_role_by_name("trader")
        rbac.assign_role_to_user(
            user_id="test_user", role_id=trader_role.id, assigned_by="admin"
        )

        # 3. 驗證角色
        user_roles = rbac.get_user_roles("test_user")
        assert len(user_roles) > 0
        assert any(r.name == "trader" for r in user_roles)

        # 4. 設置MFA
        secret, qr_code = await mfa.setup_totp("test_user", "test@example.com")
        assert secret is not None

        # 5. 驗證權限
        has_trade_perm = rbac.user_has_permission("test_user", "trade:execute")
        assert has_trade_perm is True

        # 6. 更新會話活動
        updated = session.update_activity(session_obj.session_id)
        assert updated is True

    async def test_full_api_access_flow(self, full_access_control):
        """測試完整的API訪問流程"""
        rbac = full_access_control["rbac"]
        session = full_access_control["session"]
        api = full_access_control["api"]
        abac = full_access_control["abac"]

        # 1. 創建會話
        session_obj, access_token, _, _ = session.create_session(
            user_id="api_user",
            ip_address="192.168.1.1",
            user_agent="API Client",
            device_id="api_device",
            device_name="API Client",
        )

        # 2. 分配角色
        analyst_role = rbac.get_role_by_name("analyst")
        rbac.assign_role_to_user(
            user_id="api_user", role_id=analyst_role.id, assigned_by="admin"
        )

        # 3. 生成API密鑰
        api_key, api_key_obj = api.generate_api_key(
            user_id="api_user",
            name="Analyst API Key",
            scopes=["data:read", "analysis:view"],
            rate_limit=60,
        )

        # 4. 驗證API密鑰
        validated_key = api.validate_api_key(api_key)
        assert validated_key is not None

        # 5. 檢查端點權限
        has_perm, _ = api.check_endpoint_permission("GET", "/api / v1 / data / test")
        assert has_perm is True

        # 6. 檢查速率限制
        is_limited, rate_info = api.check_rate_limit(
            validated_key, "/api / v1 / data / test", "GET"
        )
        assert is_limited is False
        assert rate_info["limit"] == 60

        # 7. 測試ABAC策略
        context = Context(
            user_id="api_user",
            user_attributes={"role": "analyst"},
            resource="/api / v1 / data / test",
            resource_attributes={},
            action="read",
            action_attributes={},
            environment="prod",
            environment_attributes={"hour": 10},
            timestamp=datetime.now(),
            request_id="api_test_001",
        )

        abac_result = await abac.evaluate_access(context)
        assert abac_result == PolicyEffect.PERMIT

    def test_end_to_end_user_journey(self, full_access_control):
        """測試端到端用戶旅程"""
        rbac = full_access_control["rbac"]
        session = full_access_control["session"]
        api = full_access_control["api"]

        # 1. 新用戶註冊（模擬）
        user_id = "new_user"

        # 2. 分配默認角色
        viewer_role = rbac.get_role_by_name("viewer")
        rbac.assign_role_to_user(
            user_id=user_id, role_id=viewer_role.id, assigned_by="admin"
        )

        # 3. 升級角色（模擬升級流程）
        trader_role = rbac.get_role_by_name("trader")
        rbac.assign_role_to_user(
            user_id=user_id, role_id=trader_role.id, assigned_by="admin"
        )

        # 4. 創建會話
        session_obj, access_token, _, _ = session.create_session(
            user_id=user_id,
            ip_address="192.168.1.100",
            user_agent="Chrome Browser",
            device_id="workstation_001",
            device_name="Workstation 1",
        )

        # 5. 驗證權限
        assert rbac.user_has_permission(user_id, "data:read")
        assert rbac.user_has_permission(user_id, "trade:execute")
        assert not rbac.user_has_permission(user_id, "user:manage")

        # 6. 生成API密鑰
        api_key, _ = api.generate_api_key(
            user_id=user_id,
            name="Production API",
            scopes=["data:read", "portfolio:view", "strategy:execute"],
            rate_limit=100,
        )

        # 7. 驗證API密鑰工作
        validated_key = api.validate_api_key(api_key)
        assert validated_key is not None
        assert "data:read" in validated_key.scopes

        # 8. 檢查用戶的API密鑰
        user_keys = api.get_user_api_keys(user_id)
        assert len(user_keys) == 1
        assert user_keys[0].user_id == user_id

        # 9. 模擬多設備登錄
        session2, _, _, _ = session.create_session(
            user_id=user_id,
            ip_address="192.168.1.101",
            user_agent="Mobile Safari",
            device_id="mobile_001",
            device_name="iPhone",
        )

        # 10. 檢查並發會話
        all_sessions = session.get_user_sessions(user_id)
        assert len(all_sessions) == 2

        # 11. 登出一個設備
        session.terminate_session(session2.session_id, "user_logout")

        # 12. 驗證只剩一個會話
        remaining_sessions = session.get_user_sessions(user_id)
        assert len(remaining_sessions) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

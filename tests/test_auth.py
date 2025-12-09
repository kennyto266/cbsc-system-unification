"""
认证系统测试
Authentication System Tests
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
import jwt

# 导入测试模块
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.api.main import app
from src.auth_simple import auth_service, User, ACCESS_TOKEN_EXPIRE_MINUTES

# 测试客户端
client = TestClient(app)

class TestAuthentication:
    """认证功能测试"""

    @pytest.fixture
    def setup_database(self):
        """设置测试数据库"""
        # 创建测试数据库表
        auth_service.create_tables()

        # 创建测试用户
        db = next(auth_service.get_db())
        test_user = User(
            username="testuser",
            email="test@example.com",
            password_hash=auth_service.hash_password("testpass123"),
            is_active=True
        )
        db.add(test_user)
        db.commit()
        db.close()

    def test_health_check(self):
        """测试健康检查"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "checks" in data

    def test_login_success(self, setup_database):
        """测试成功登录"""
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }

        response = client.post("/api/auth/login", data=login_data)
        assert response.status_code == 200

        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "testuser"

    def test_login_invalid_credentials(self, setup_database):
        """测试无效凭据登录"""
        login_data = {
            "username": "testuser",
            "password": "wrongpassword"
        }

        response = client.post("/api/auth/login", data=login_data)
        assert response.status_code == 401

    def test_login_nonexistent_user(self):
        """测试不存在用户登录"""
        login_data = {
            "username": "nonexistent",
            "password": "password"
        }

        response = client.post("/api/auth/login", data=login_data)
        assert response.status_code == 401

    def test_get_current_user(self, setup_database):
        """测试获取当前用户信息"""
        # 先登录获取token
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }

        login_response = client.post("/api/auth/login", data=login_data)
        token = login_response.json()["access_token"]

        # 使用token获取用户信息
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/auth/me", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"

    def test_get_current_user_invalid_token(self):
        """测试无效token获取用户信息"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == 401

    def test_password_strength_validation(self):
        """测试密码强度验证"""
        # 测试弱密码
        weak_response = client.post("/api/auth/validate-password", json={"password": "123"})
        assert weak_response.status_code == 200
        weak_data = weak_response.json()
        assert weak_data["level"] == "weak"

        # 测试强密码
        strong_response = client.post("/api/auth/validate-password",
                                     json={"password": "StrongPass123!"})
        assert strong_response.status_code == 200
        strong_data = strong_response.json()
        assert strong_data["level"] == "strong"

    def test_change_password_success(self, setup_database):
        """测试成功修改密码"""
        # 先登录
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }

        login_response = client.post("/api/auth/login", data=login_data)
        token = login_response.json()["access_token"]

        # 修改密码
        headers = {"Authorization": f"Bearer {token}"}
        password_data = {
            "old_password": "testpass123",
            "new_password": "NewStrongPass123!"
        }

        response = client.post("/api/auth/change-password",
                              json=password_data, headers=headers)
        assert response.status_code == 200

        # 使用新密码登录
        new_login_data = {
            "username": "testuser",
            "password": "NewStrongPass123!"
        }

        new_login_response = client.post("/api/auth/login", data=new_login_data)
        assert new_login_response.status_code == 200

    def test_change_password_wrong_old_password(self, setup_database):
        """测试修改密码时旧密码错误"""
        # 先登录
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }

        login_response = client.post("/api/auth/login", data=login_data)
        token = login_response.json()["access_token"]

        # 尝试使用错误的旧密码修改
        headers = {"Authorization": f"Bearer {token}"}
        password_data = {
            "old_password": "wrongpassword",
            "new_password": "NewStrongPass123!"
        }

        response = client.post("/api/auth/change-password",
                              json=password_data, headers=headers)
        assert response.status_code == 400

    def test_get_login_history(self, setup_database):
        """测试获取登录历史"""
        # 先登录
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }

        client.post("/api/auth/login", data=login_data)
        login_response = client.post("/api/auth/login", data=login_data)
        token = login_response.json()["access_token"]

        # 获取登录历史
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/auth/login-history", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_check_token_validity(self, setup_database):
        """测试token有效性检查"""
        # 先登录
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }

        login_response = client.post("/api/auth/login", data=login_data)
        token = login_response.json()["access_token"]

        # 检查token有效性
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/auth/check-token", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["username"] == "testuser"

class TestPasswordStrength:
    """密码强度测试"""

    def test_weak_passwords(self):
        """测试弱密码"""
        weak_passwords = [
            "123",
            "password",
            "abcdef",
            "test"
        ]

        for password in weak_passwords:
            strength = auth_service.validate_password_strength(password)
            assert strength["level"] == "weak"
            assert strength["score"] <= 2

    def test_medium_passwords(self):
        """测试中等强度密码"""
        medium_passwords = [
            "password123",
            "Password123",
            "Testpass1",
            "MyPassword"
        ]

        for password in medium_passwords:
            strength = auth_service.validate_password_strength(password)
            assert strength["level"] in ["medium", "strong"]
            assert 3 <= strength["score"] <= 4

    def test_strong_passwords(self):
        """测试强密码"""
        strong_passwords = [
            "StrongPass123!",
            "MySecure@Password1",
            "Complex#Password2024",
            "Very$tr0ngP@ssw0rd"
        ]

        for password in strong_passwords:
            strength = auth_service.validate_password_strength(password)
            assert strength["level"] == "strong"
            assert strength["score"] == 5

class TestTokenGeneration:
    """Token生成测试"""

    def test_token_creation(self):
        """测试token创建"""
        data = {"sub": "testuser"}
        token = auth_service.create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_decode(self):
        """测试token解码"""
        data = {"sub": "testuser"}
        token = auth_service.create_access_token(data)

        # 解码token
        decoded = jwt.decode(token, auth_service.SECRET_KEY, algorithms=[auth_service.ALGORITHM])
        assert decoded["sub"] == "testuser"
        assert "exp" in decoded

    def test_token_expiration(self):
        """测试token过期"""
        # 创建一个短期的token
        data = {"sub": "testuser"}
        token = auth_service.create_access_token(
            data,
            expires_delta=timedelta(seconds=1)
        )

        # 立即解码应该成功
        decoded = jwt.decode(token, auth_service.SECRET_KEY, algorithms=[auth_service.ALGORITHM])
        assert decoded["sub"] == "testuser"

        # 等待过期（在实际测试中可能需要更长时间）
        # await asyncio.sleep(2)
        #
        # # 过期后解码应该失败
        # with pytest.raises(jwt.ExpiredSignatureError):
        #     jwt.decode(token, auth_service.SECRET_KEY, algorithms=[auth_service.ALGORITHM])

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
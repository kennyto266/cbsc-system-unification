"""
个人仪表板测试
Personal Dashboard Tests
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.api.main import app
from src.user_profile import user_profile_service
from src.auth_simple import User

# 测试客户端
client = TestClient(app)

class TestUserProfileAPI:
    """用户资料API测试"""

    @pytest.fixture
    def setup_database(self):
        """设置测试数据库"""
        # 创建测试数据库表
        user_profile_service.create_tables()

        # 创建测试用户
        db = next(user_profile_service.get_db())
        test_user = User(
            username="dashboarduser",
            email="dashboard@example.com",
            password_hash=user_profile_service.hash_password("testpass123"),
            is_active=True
        )
        db.add(test_user)
        db.commit()
        db.close()

    def get_auth_headers(self):
        """获取认证头"""
        # 登录获取token
        login_data = {
            "username": "dashboarduser",
            "password": "testpass123"
        }

        response = client.post("/api/auth/login", data=login_data)
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def test_get_profile(self, setup_database):
        """测试获取用户资料"""
        headers = self.get_auth_headers()
        response = client.get("/api/user/profile", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["user"]["username"] == "dashboarduser"
        assert "avatar_url" in data
        assert "bio" in data
        assert "timezone" in data

    def test_update_profile(self, setup_database):
        """测试更新用户资料"""
        headers = self.get_auth_headers()

        update_data = {
            "bio": "这是一个测试简介",
            "phone": "13800138000",
            "timezone": "Asia/Shanghai",
            "language": "zh-CN"
        }

        response = client.put("/api/user/profile", json=update_data, headers=headers)
        assert response.status_code == 200

        # 验证更新结果
        get_response = client.get("/api/user/profile", headers=headers)
        profile_data = get_response.json()
        assert profile_data["bio"] == "这是一个测试简介"
        assert profile_data["phone"] == "13800138000"

    def test_upload_avatar(self, setup_database):
        """测试上传头像"""
        headers = self.get_auth_headers()

        # 创建模拟图片文件
        avatar_content = b"fake_image_data"

        response = client.post(
            "/api/user/avatar",
            headers=headers,
            files={"file": ("avatar.jpg", avatar_content, "image/jpeg")}
        )

        assert response.status_code == 200
        data = response.json()
        assert "avatar_url" in data
        assert data["message"] == "头像上传成功"

    def test_upload_invalid_file_type(self, setup_database):
        """测试上传无效文件类型"""
        headers = self.get_auth_headers()

        # 上传非图片文件
        invalid_file_content = b"not_an_image"

        response = client.post(
            "/api/user/avatar",
            headers=headers,
            files={"file": ("document.txt", invalid_file_content, "text/plain")}
        )

        assert response.status_code == 400
        assert "请上传图片文件" in response.json()["detail"]

    def test_get_statistics(self, setup_database):
        """测试获取用户统计"""
        headers = self.get_auth_headers()

        # 记录一些测试统计数据
        user_profile_service.record_daily_statistics(1, {
            "login_count": 5,
            "trade_count": 10,
            "strategy_count": 3,
            "performance_score": 85.5,
            "active_minutes": 120
        })

        response = client.get("/api/user/statistics", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert "period" in data
        assert "login_count" in data
        assert "trade_count" in data
        assert "performance_score" in data
        assert "recent_activities" in data

    def test_get_recent_activity(self, setup_database):
        """测试获取最近活动"""
        headers = self.get_auth_headers()

        # 记录一些测试活动
        user_profile_service.record_activity(
            1,
            "test",
            "测试活动记录",
            {"test": True}
        )

        response = client.get("/api/user/recent-activity", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert "activities" in data
        assert isinstance(data["activities"], list)

    def test_get_user_settings(self, setup_database):
        """测试获取用户设置"""
        headers = self.get_auth_headers()

        response = client.get("/api/user/settings", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert "email_notifications" in data
        assert "browser_notifications" in data
        assert "privacy_settings" in data

    def test_update_notification_settings(self, setup_database):
        """测试更新通知设置"""
        headers = self.get_auth_headers()

        settings_data = {
            "email_notifications": {
                "system_alerts": True,
                "security_alerts": True,
                "trade_alerts": False
            },
            "browser_notifications": {
                "enabled": True,
                "trade_alerts": True
            }
        }

        response = client.put(
            "/api/user/settings/notifications",
            json=settings_data,
            headers=headers
        )

        assert response.status_code == 200
        assert response.json()["message"] == "通知设置更新成功"

    def test_update_appearance_settings(self, setup_database):
        """测试更新外观设置"""
        headers = self.get_auth_headers()

        settings_data = {
            "theme": "dark",
            "language": "en-US",
            "timezone": "America/New_York"
        }

        response = client.put(
            "/api/user/settings/appearance",
            json=settings_data,
            headers=headers
        )

        assert response.status_code == 200
        assert response.json()["message"] == "外观设置更新成功"

    def test_export_user_data(self, setup_database):
        """测试导出用户数据"""
        headers = self.get_auth_headers()

        response = client.post("/api/user/export-data", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert "user_info" in data
        assert "profile" in data
        assert "statistics" in data
        assert "settings" in data
        assert "export_date" in data

    def test_clear_cache(self, setup_database):
        """测试清理用户缓存"""
        headers = self.get_auth_headers()

        response = client.post("/api/user/clear-cache", headers=headers)
        assert response.status_code == 200
        assert "缓存清理完成" in response.json()["message"]

    def test_get_quick_actions(self, setup_database):
        """测试获取快捷操作"""
        headers = self.get_auth_headers()

        response = client.get("/api/user/quick-actions", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert "actions" in data
        assert isinstance(data["actions"], list)

        # 检查快捷操作结构
        actions = data["actions"]
        for action in actions:
            assert "id" in action
            assert "title" in action
            assert "description" in action
            assert "icon" in action
            assert "url" in action

class TestUserProfileService:
    """用户资料服务测试"""

    def test_create_tables(self):
        """测试创建数据库表"""
        user_profile_service.create_tables()

        # 验证表是否创建成功
        db = next(user_profile_service.get_db())
        # 这里可以添加更多的验证逻辑
        db.close()

    def test_get_or_create_profile(self):
        """测试获取或创建用户资料"""
        # 创建测试用户
        db = next(user_profile_service.get_db())
        test_user = User(
            username="testuser",
            email="test@example.com",
            password_hash=user_profile_service.hash_password("testpass123"),
            is_active=True
        )
        db.add(test_user)
        db.commit()
        user_id = test_user.id
        db.close()

        # 获取或创建资料
        profile = user_profile_service.get_or_create_profile(user_id)
        assert profile is not None
        assert profile.user_id == user_id

    def test_update_profile(self):
        """测试更新用户资料"""
        # 创建测试用户
        db = next(user_profile_service.get_db())
        test_user = User(
            username="updatetest",
            email="update@example.com",
            password_hash=user_profile_service.hash_password("testpass123"),
            is_active=True
        )
        db.add(test_user)
        db.commit()
        user_id = test_user.id
        db.close()

        # 更新资料
        update_data = {
            "bio": "更新的简介",
            "phone": "13900139000",
            "timezone": "Asia/Shanghai"
        }

        success = user_profile_service.update_profile(user_id, update_data)
        assert success is True

        # 验证更新结果
        db = next(user_profile_service.get_db())
        profile = user_profile_service.get_or_create_profile(user_id, db)
        assert profile.bio == "更新的简介"
        assert profile.phone == "13900139000"
        db.close()

    def test_record_activity(self):
        """测试记录用户活动"""
        # 创建测试用户
        db = next(user_profile_service.get_db())
        test_user = User(
            username="activitytest",
            email="activity@example.com",
            password_hash=user_profile_service.hash_password("testpass123"),
            is_active=True
        )
        db.add(test_user)
        db.commit()
        user_id = test_user.id
        db.close()

        # 记录活动
        user_profile_service.record_activity(
            user_id,
            "test",
            "测试活动",
            {"test": True}
        )

        # 验证活动是否记录成功
        stats = user_profile_service.get_user_statistics(user_id, 30)
        assert len(stats["recent_activities"]) > 0

    def test_get_user_statistics(self):
        """测试获取用户统计"""
        # 创建测试用户
        db = next(user_profile_service.get_db())
        test_user = User(
            username="statstest",
            email="stats@example.com",
            password_hash=user_profile_service.hash_password("testpass123"),
            is_active=True
        )
        db.add(test_user)
        db.commit()
        user_id = test_user.id
        db.close()

        # 记录一些测试统计数据
        user_profile_service.record_daily_statistics(user_id, {
            "login_count": 10,
            "trade_count": 25,
            "strategy_count": 5,
            "performance_score": 88.5
        })

        # 获取统计
        stats = user_profile_service.get_user_statistics(user_id, 30)
        assert stats["login_count"] == 10
        assert stats["trade_count"] == 25
        assert stats["strategy_count"] == 5
        assert stats["performance_score"] == 88.5

    def test_get_user_settings(self):
        """测试获取用户设置"""
        # 创建测试用户
        db = next(user_profile_service.get_db())
        test_user = User(
            username="settingstest",
            email="settings@example.com",
            password_hash=user_profile_service.hash_password("testpass123"),
            is_active=True
        )
        db.add(test_user)
        db.commit()
        user_id = test_user.id
        db.close()

        # 获取设置
        settings = user_profile_service.get_user_settings(user_id)
        assert "email_notifications" in settings
        assert "browser_notifications" in settings
        assert "privacy_settings" in settings

    def test_update_user_settings(self):
        """测试更新用户设置"""
        # 创建测试用户
        db = next(user_profile_service.get_db())
        test_user = User(
            username="updatetest2",
            email="update2@example.com",
            password_hash=user_profile_service.hash_password("testpass123"),
            is_active=True
        )
        db.add(test_user)
        db.commit()
        user_id = test_user.id
        db.close()

        # 更新设置
        settings_data = {
            "email_notifications": {
                "system_alerts": True,
                "trade_alerts": False
            },
            "browser_notifications": {
                "enabled": True
            }
        }

        success = user_profile_service.update_user_settings(user_id, settings_data)
        assert success is True

        # 验证更新结果
        settings = user_profile_service.get_user_settings(user_id)
        assert settings["email_notifications"]["system_alerts"] == True
        assert settings["email_notifications"]["trade_alerts"] == False
        assert settings["browser_notifications"]["enabled"] == True

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
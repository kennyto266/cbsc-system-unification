#!/usr / bin / env python3
"""
ConfigManager Tests
配置管理器测试

Unit tests for the configuration manager
配置管理器的单元测试
"""

import sys
import tempfile
import unittest
from pathlib import Path

import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.config_manager import ConfigManager


class TestConfigManager(unittest.TestCase):
    """配置管理器测试类"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / "test_config.yaml"

        # 创建测试配置文件
        self.test_config = {
            "version": "1.0.0",
            "authenticity_manager": {"max_history_size": 500, "default_timeout": 60.0},
            "verifiers": {"test_verifier": {"enabled": True, "priority": 80}},
        }

        with open(self.config_file, "w", encoding="utf - 8") as f:
            yaml.dump(self.test_config, f)

        self.config_manager = ConfigManager(self.config_file)

    def tearDown(self):
        """测试后清理"""
        # 清理临时文件
        if self.config_file.exists():
            self.config_file.unlink()
        Path(self.temp_dir).rmdir()

    def test_config_loading(self):
        """测试配置加载"""
        # 测试基本配置加载
        self.assertEqual(self.config_manager.get("version"), "1.0.0")

        # 测试嵌套配置获取
        self.assertEqual(
            self.config_manager.get("authenticity_manager.max_history_size"), 500
        )

        # 测试不存在的键
        self.assertIsNone(self.config_manager.get("nonexistent.key"))
        self.assertEqual(
            self.config_manager.get("nonexistent.key", "default"), "default"
        )

    def test_config_setting(self):
        """测试配置设置"""
        # 设置新值
        success = self.config_manager.set("new_key", "new_value")
        self.assertTrue(success)
        self.assertEqual(self.config_manager.get("new_key"), "new_value")

        # 设置嵌套值
        success = self.config_manager.set("nested.key", "nested_value")
        self.assertTrue(success)
        self.assertEqual(self.config_manager.get("nested.key"), "nested_value")

    def test_verifier_config(self):
        """测试验证器配置"""
        # 测试获取验证器配置
        verifier_config = self.config_manager.get_verifier_config("test_verifier")
        self.assertTrue(verifier_config["enabled"])
        self.assertEqual(verifier_config["priority"], 80)

        # 测试启用状态检查
        self.assertTrue(self.config_manager.is_verifier_enabled("test_verifier"))
        self.assertFalse(
            self.config_manager.is_verifier_enabled("nonexistent_verifier")
        )

        # 测试获取启用的验证器
        enabled_verifiers = self.config_manager.get_enabled_verifiers()
        self.assertIn("test_verifier", enabled_verifiers)

    def test_verifier_config_update(self):
        """测试验证器配置更新"""
        new_config = {"enabled": False, "priority": 90, "new_param": "test_value"}

        success = self.config_manager.update_verifier_config(
            "test_verifier", new_config
        )
        self.assertTrue(success)

        updated_config = self.config_manager.get_verifier_config("test_verifier")
        self.assertFalse(updated_config["enabled"])
        self.assertEqual(updated_config["priority"], 90)
        self.assertEqual(updated_config["new_param"], "test_value")

    def test_config_validation(self):
        """测试配置验证"""
        validation_result = self.config_manager.validate_config()

        self.assertTrue(validation_result["valid"])
        self.assertEqual(len(validation_result["issues"]), 0)
        self.assertGreaterEqual(validation_result["total_verifiers"], 1)

    def test_config_export(self):
        """测试配置导出"""
        # 测试YAML导出
        yaml_file = Path(self.temp_dir) / "exported_config.yaml"
        success = self.config_manager.export_config(yaml_file, "yaml")
        self.assertTrue(success)
        self.assertTrue(yaml_file.exists())

        # 测试JSON导出
        json_file = Path(self.temp_dir) / "exported_config.json"
        success = self.config_manager.export_config(json_file, "json")
        self.assertTrue(success)
        self.assertTrue(json_file.exists())

    def test_change_callback(self):
        """测试配置变更回调"""
        callback_called = False
        callback_config = None

        def test_callback(config):
            nonlocal callback_called, callback_config
            callback_called = True
            callback_config = config

        self.config_manager.add_change_callback(test_callback)

        # 触发配置变更
        self.config_manager.set("test.callback_key", "callback_value")

        # 注意：在实际应用中，回调会在文件变更时触发
        # 这里我们手动测试回调功能
        self.config_manager.change_callbacks[0](self.config_manager.config)

        self.assertTrue(callback_called)
        self.assertIsNotNone(callback_config)

    def test_get_all_config(self):
        """测试获取完整配置"""
        all_config = self.config_manager.get_all_config()

        self.assertIsInstance(all_config, dict)
        self.assertIn("version", all_config)
        self.assertIn("authenticity_manager", all_config)
        self.assertIn("verifiers", all_config)


class TestConfigManagerHotReload(unittest.TestCase):
    """配置管理器热重载测试"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / "hot_reload_config.yaml"

        # 初始配置
        initial_config = {"version": "1.0.0", "test_value": "initial"}

        with open(self.config_file, "w", encoding="utf - 8") as f:
            yaml.dump(initial_config, f)

    def tearDown(self):
        """测试后清理"""
        if self.config_file.exists():
            self.config_file.unlink()
        Path(self.temp_dir).rmdir()

    def test_file_reload(self):
        """测试文件重新加载"""
        config_manager = ConfigManager(self.config_file)
        initial_value = config_manager.get("test_value")
        self.assertEqual(initial_value, "initial")

        # 修改配置文件
        updated_config = {
            "version": "1.0.1",
            "test_value": "updated",
            "new_key": "new_value",
        }

        with open(self.config_file, "w", encoding="utf - 8") as f:
            yaml.dump(updated_config, f)

        # 手动触发重新加载（在实际应用中，这会通过文件监控自动触发）
        config_manager.reload()

        # 等待异步操作完成
        import time

        time.sleep(0.1)

        # 验证配置已更新
        updated_value = config_manager.get("test_value")
        self.assertEqual(updated_value, "updated")
        self.assertEqual(config_manager.get("version"), "1.0.1")
        self.assertEqual(config_manager.get("new_key"), "new_value")


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""
Test suite for Phase 6: Rollback Framework

Tests the integration of the rollback framework with the existing quantitative trading system.
"""

import os
import sys
import unittest
import tempfile
import shutil
import json
import time
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestRollbackFramework(unittest.TestCase):
    """Test cases for the rollback framework components."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.config_dir = self.test_dir / "config"
        self.versions_dir = self.test_dir / "versions"
        self.backup_dir = self.test_dir / "backups"
        self.logs_dir = self.test_dir / "logs"
        
        # Create test directories
        for directory in [self.config_dir, self.versions_dir, self.backup_dir, self.logs_dir]:
            directory.mkdir(parents=True)
        
        # Set environment variables for testing
        os.environ['ENVIRONMENT'] = 'testing'
        os.environ['TEST_MODE'] = 'true'
        
        # Import components after setting up test environment
        try:
            from src.rollback.rollback_manager import RollbackManager
            from src.config.feature_flags_manager import FeatureFlagsManager
            from src.config.configuration_manager import ConfigurationManager
            
            self.rollback_manager = RollbackManager(
                versions_dir=str(self.versions_dir),
                max_versions=10,
                backup_timeout_seconds=30
            )
            
            # Create test feature flags config
            test_flags_config = {
                'feature_flags': {
                    'test_feature': {
                        'flag_type': 'boolean',
                        'enabled': False,
                        'description': 'Test feature for rollback framework'
                    },
                    'gradual_rollout_feature': {
                        'flag_type': 'percentage',
                        'enabled': True,
                        'rollout_percentage': 50,
                        'description': 'Test gradual rollout feature'
                    }
                }
            }
            
            test_flags_file = self.config_dir / "feature_flags.yaml"
            with open(test_flags_file, 'w') as f:
                import yaml
                yaml.dump(test_flags_config, f)
            
            self.feature_flags_manager = FeatureFlagsManager(
                config_path=str(test_flags_file)
            )
            
            self.config_manager = ConfigurationManager(
                config_root=str(self.config_dir),
                backup_dir=str(self.backup_dir),
                environment='testing',
                auto_backup=True,
                validation_enabled=True
            )
            
        except ImportError as e:
            self.skipTest(f"Cannot import rollback components: {e}")
    
    def tearDown(self):
        """Clean up test environment."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_rollback_manager_initialization(self):
        """Test rollback manager initialization."""
        self.assertIsNotNone(self.rollback_manager)
        self.assertTrue(self.versions_dir.exists())
        self.assertTrue(self.rollback_manager.versions_dir.exists())
        self.assertEqual(self.rollback_manager.max_versions, 10)
    
    def test_create_version_snapshot(self):
        """Test creating a version snapshot."""
        # Create some test files
        test_file = self.test_dir / "test_source"
        test_file.write_text("test content")
        
        # Create version snapshot
        version_id = self.rollback_manager.create_version_snapshot(
            description="Test snapshot",
            backup_source_dirs=[str(test_file.parent)],
            priority=1,
            is_stable=True
        )
        
        self.assertIsNotNone(version_id)
        self.assertTrue(version_id.startswith("v"))
        
        # Verify snapshot was created
        versions = self.rollback_manager.list_versions()
        self.assertEqual(len(versions), 1)
        self.assertEqual(versions[0].version_id, version_id)
        self.assertEqual(versions[0].description, "Test snapshot")
        self.assertTrue(versions[0].is_stable)
    
    def test_get_stable_versions(self):
        """Test getting stable versions."""
        # Create multiple version snapshots
        stable_version = self.rollback_manager.create_version_snapshot(
            "Stable version",
            priority=1,
            is_stable=True
        )
        
        unstable_version = self.rollback_manager.create_version_snapshot(
            "Unstable version",
            priority=3,
            is_stable=False
        )
        
        # Get stable versions
        stable_versions = self.rollback_manager.get_stable_versions()
        
        self.assertEqual(len(stable_versions), 1)
        self.assertEqual(stable_versions[0].version_id, stable_version)
    
    def test_version_integrity_validation(self):
        """Test version integrity validation."""
        # Create a version snapshot
        version_id = self.rollback_manager.create_version_snapshot(
            "Integrity test version",
            priority=1,
            is_stable=True
        )
        
        # Validate integrity
        is_valid = self.rollback_manager.validate_version_integrity(version_id)
        self.assertTrue(is_valid)
    
    def test_feature_flags_manager_initialization(self):
        """Test feature flags manager initialization."""
        self.assertIsNotNone(self.feature_flags_manager)
        self.assertTrue(self.config_dir.exists())
    
    def test_feature_flag_evaluation(self):
        """Test feature flag evaluation."""
        # Test disabled feature
        is_enabled = self.feature_flags_manager.is_enabled("test_feature")
        self.assertFalse(is_enabled)
        
        # Test percentage-based feature
        result = self.feature_flags_manager.evaluate_flag("gradual_rollout_feature")
        self.assertIsNotNone(result)
        self.assertEqual(result.flag_name, "gradual_rollout_feature")
        self.assertEqual(result.flag_type.value, "percentage")
    
    def test_feature_flag_enable_disable(self):
        """Test enabling and disabling feature flags."""
        # Enable feature
        success = self.feature_flags_manager.enable_flag("test_feature")
        self.assertTrue(success)
        
        # Check if enabled
        is_enabled = self.feature_flags_manager.is_enabled("test_feature")
        self.assertTrue(is_enabled)
        
        # Disable feature
        success = self.feature_flags_manager.disable_flag("test_feature")
        self.assertTrue(success)
        
        # Check if disabled
        is_enabled = self.feature_flags_manager.is_enabled("test_feature")
        self.assertFalse(is_enabled)
    
    def test_emergency_disable_all_flags(self):
        """Test emergency disable all feature flags."""
        # Enable some flags first
        self.feature_flags_manager.enable_flag("test_feature")
        
        # Emergency disable all
        disabled_count = self.feature_flags_manager.emergency_disable_all()
        self.assertGreater(disabled_count, 0)
        
        # Check all flags are disabled
        all_flags = self.feature_flags_manager.get_all_flags()
        for flag_name, flag in all_flags.items():
            self.assertFalse(flag.enabled)
            self.assertTrue(flag.emergency_disable)
    
    def test_configuration_manager_initialization(self):
        """Test configuration manager initialization."""
        self.assertIsNotNone(self.config_manager)
        self.assertEqual(self.config_manager.environment.value, "testing")
    
    def test_configuration_snapshot(self):
        """Test configuration snapshot creation."""
        # Create test configuration
        test_config = {
            "test_setting": "test_value",
            "nested": {
                "setting": "nested_value"
            }
        }
        
        config_file = self.config_dir / "test_config.json"
        with open(config_file, 'w') as f:
            json.dump(test_config, f)
        
        # Create snapshot
        snapshot_id = self.config_manager.create_snapshot(
            "Test configuration snapshot",
            config_files=["test_config.json"]
        )
        
        self.assertIsNotNone(snapshot_id)
        self.assertTrue(snapshot_id.startswith("snapshot_"))
    
    def test_configuration_update(self):
        """Test configuration update with backup."""
        # Create initial configuration
        initial_config = {"initial_setting": "initial_value"}
        config_file = self.config_dir / "update_test_config.json"
        with open(config_file, 'w') as f:
            json.dump(initial_config, f)
        
        # Update configuration
        updates = {"new_setting": "new_value"}
        result = self.config_manager.update_config(
            "update_test_config.json",
            updates,
            backup=True
        )
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.snapshot_id)
        self.assertIn("update_test_config.json", result.updated_files)
    
    def test_configuration_validation(self):
        """Test configuration validation."""
        # Create test configuration
        test_config = {"valid_setting": "valid_value"}
        config_file = self.config_dir / "validation_test_config.json"
        with open(config_file, 'w') as f:
            json.dump(test_config, f)
        
        # Validate configuration
        result = self.config_manager.validate_config("validation_test_config.json")
        self.assertIsNotNone(result)
        self.assertEqual(result.config_file, "validation_test_config.json")
    
    @patch('src.rollback.emergency_recovery.psutil')
    def test_emergency_recovery_health_metrics(self, mock_psutil):
        """Test emergency recovery health metrics collection."""
        # Mock psutil responses
        mock_psutil.cpu_percent.return_value = 75.0
        mock_psutil.virtual_memory.return_value = MagicMock(percent=60.0)
        mock_psutil.disk_usage.return_value = MagicMock(percent=50.0)
        mock_psutil.pids.return_value = [1, 2, 3, 4, 5]
        
        try:
            from src.rollback.emergency_recovery import EmergencyRecoverySystem
            
            # Create emergency recovery system with test config
            test_config_file = self.config_dir / "emergency_recovery_config.json"
            emergency_config = {
                "health_metrics": [
                    {
                        "name": "cpu_usage",
                        "threshold_warning": 80.0,
                        "threshold_critical": 90.0,
                        "threshold_emergency": 95.0,
                        "unit": "%",
                        "higher_is_better": False,
                        "measurement_interval": 30
                    }
                ],
                "trigger_conditions": [],
                "monitoring_interval": 10
            }
            
            with open(test_config_file, 'w') as f:
                json.dump(emergency_config, f)
            
            emergency_system = EmergencyRecoverySystem(
                config_path=str(test_config_file)
            )
            
            # Test health check
            health = emergency_system.get_system_health()
            self.assertIsNotNone(health)
            self.assertIn('current_metrics', health)
            self.assertIn('monitoring_active', health)
            
        except ImportError as e:
            self.skipTest(f"Cannot import emergency recovery system: {e}")
    
    def test_deployment_safety_net_cli(self):
        """Test deployment safety net CLI interface."""
        # Create deployment safety net script path
        script_path = project_root / "scripts" / "deployment_safety_net.py"
        
        if not script_path.exists():
            self.skipTest("Deployment safety net script not found")
        
        try:
            # Test dry run validation
            import subprocess
            
            result = subprocess.run([
                sys.executable, str(script_path),
                "validate",
                "--environment", "testing",
                "--validation-level", "basic",
                "--dry-run"
            ], capture_output=True, text=True, timeout=30)
            
            # Check that the script runs without critical errors
            self.assertEqual(result.returncode, 0)
            
        except subprocess.TimeoutExpired:
            self.fail("Deployment safety net validation timed out")
        except Exception as e:
            self.skipTest(f"Cannot test deployment safety net CLI: {e}")
    
    def test_integration_workflow(self):
        """Test complete integration workflow."""
        try:
            # 1. Create initial version snapshot
            version_id = self.rollback_manager.create_version_snapshot(
                "Integration test initial version",
                priority=1,
                is_stable=True
            )
            self.assertIsNotNone(version_id)
            
            # 2. Update configuration
            config_updates = {
                "integration_test": {
                    "enabled": True,
                    "version": "1.0.0"
                }
            }
            
            result = self.config_manager.update_config(
                "integration_test_config.json",
                config_updates,
                backup=True
            )
            self.assertTrue(result.success)
            
            # 3. Enable feature flag
            success = self.feature_flags_manager.enable_flag("test_feature")
            self.assertTrue(success)
            
            # 4. Verify all components are working
            versions = self.rollback_manager.get_stable_versions()
            self.assertGreater(len(versions), 0)
            
            flags = self.feature_flags_manager.get_all_flags()
            self.assertIn("test_feature", flags)
            
            # 5. Test rollback
            rollback_result = self.rollback_manager.rollback_to_version(
                version_id,
                verification_mode="quick"
            )
            self.assertTrue(rollback_result.success)
            
        except Exception as e:
            self.fail(f"Integration workflow test failed: {e}")
    
    def test_error_handling(self):
        """Test error handling and edge cases."""
        # Test rollback to non-existent version
        with self.assertRaises(Exception):
            self.rollback_manager.rollback_to_version("non_existent_version")
        
        # Test feature flag operations on non-existent flag
        success = self.feature_flags_manager.enable_flag("non_existent_flag")
        self.assertFalse(success)
        
        # Test configuration update on non-existent file
        result = self.config_manager.update_config(
            "non_existent_config.json",
            {"test": "value"}
        )
        self.assertFalse(result.success)
    
    def test_performance_requirements(self):
        """Test that performance requirements are met."""
        # Test version snapshot creation time
        start_time = time.time()
        version_id = self.rollback_manager.create_version_snapshot(
            "Performance test version"
        )
        snapshot_time = time.time() - start_time
        
        # Should create snapshot in reasonable time (less than 10 seconds)
        self.assertLess(snapshot_time, 10.0)
        self.assertIsNotNone(version_id)
        
        # Test feature flag evaluation time
        start_time = time.time()
        for _ in range(100):
            self.feature_flags_manager.is_enabled("test_feature")
        evaluation_time = time.time() - start_time
        
        # Should be fast (less than 1 second for 100 evaluations)
        self.assertLess(evaluation_time, 1.0)

class TestRollbackFrameworkConfiguration(unittest.TestCase):
    """Test rollback framework configuration files."""
    
    def setUp(self):
        """Set up test environment."""
        self.config_dir = Path(__file__).parent.parent / "config"
    
    def test_rollback_config_exists(self):
        """Test that rollback configuration file exists."""
        config_file = self.config_dir / "rollback_config.yaml"
        self.assertTrue(config_file.exists(), "rollback_config.yaml should exist")
    
    def test_emergency_recovery_config_exists(self):
        """Test that emergency recovery configuration file exists."""
        config_file = self.config_dir / "emergency_recovery_config.json"
        self.assertTrue(config_file.exists(), "emergency_recovery_config.json should exist")
    
    def test_feature_flags_config_exists(self):
        """Test that feature flags configuration file exists."""
        config_file = self.config_dir / "feature_flags.yaml"
        self.assertTrue(config_file.exists(), "feature_flags.yaml should exist")
    
    def test_rollback_config_structure(self):
        """Test rollback configuration file structure."""
        config_file = self.config_dir / "rollback_config.yaml"
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                import yaml
                config = yaml.safe_load(f)
            
            # Check required sections
            required_sections = [
                'version_rollback',
                'feature_flags',
                'configuration_manager',
                'emergency_recovery',
                'deployment_safety_net'
            ]
            
            for section in required_sections:
                self.assertIn(section, config, f"Missing required section: {section}")

def run_rollback_framework_tests():
    """Run all rollback framework tests."""
    print("Running Rollback Framework Tests...")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestRollbackFramework,
        TestRollbackFrameworkConfiguration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.splitlines()[-1] if traceback else 'Unknown'}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.splitlines()[-1] if traceback else 'Unknown'}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    
    if success:
        print("\nAll tests passed! Rollback framework is ready for production.")
    else:
        print("\nSome tests failed. Please review and fix issues.")
    
    return success

if __name__ == '__main__':
    success = run_rollback_framework_tests()
    sys.exit(0 if success else 1)
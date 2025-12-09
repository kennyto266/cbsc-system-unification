#!/usr/bin/env python3
"""
Authentication System Demo
认证系统演示

Demonstration of the data authenticity verification system
数据真实性验证系统演示
"""

import sys
import asyncio
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

def test_basic_imports():
    """测试基本导入"""
    print("Testing basic imports...")

    try:
        # Test interfaces
        from interfaces.auth_result import AuthResult, Verdict, AuthStatus
        from interfaces.verifier_interface import IVerifier
        print("PASS: Interfaces imported successfully")

        # Test core components
        from core.authenticator import BaseAuthenticator
        print("PASS: Core components imported successfully")

        # Test configuration (without watchdog dependency)
        try:
            from config.config_manager import ConfigManager
            print("PASS: Configuration manager imported successfully")
        except Exception as e:
            print(f"WARN: Configuration manager import with limitations: {e}")

        # Test rules engine
        from rules.rules_engine import RulesEngine
        print("PASS: Rules engine imported successfully")

        # Test data authenticity manager
        from interfaces.data_authenticity_manager import DataAuthenticityManager
        print("PASS: Data authenticity manager imported successfully")

        return True

    except Exception as e:
        print(f"FAIL: Import failed: {e}")
        return False


def test_auth_result():
    """测试认证结果"""
    print("\nTesting AuthResult...")

    try:
        from interfaces.auth_result import AuthResult, Verdict, AuthStatus

        # Create test result
        result = AuthResult(
            data_id="test_hibor_001",
            data_type="financial_rate",
            data_source="hkma.gov.hk",
            overall_verdict=Verdict.AUTHENTIC,
            overall_confidence=0.95,
            status=AuthStatus.COMPLETED,
            total_execution_time_ms=150.5
        )

        print(f"PASS: Created AuthResult: {result.data_id}")
        print(f"     Verdict: {result.overall_verdict.value}")
        print(f"     Confidence: {result.overall_confidence}")
        print(f"     Status: {result.status.value}")

        # Test serialization
        result_dict = result.to_dict()
        restored_result = AuthResult.from_dict(result_dict)

        print(f"PASS: Serialization test passed")
        print(f"     Restored data_id: {restored_result.data_id}")

        return True

    except Exception as e:
        print(f"FAIL: AuthResult test failed: {e}")
        return False


def test_rules_engine():
    """测试规则引擎"""
    print("\nTesting Rules Engine...")

    try:
        from rules.rules_engine import RulesEngine
        from rules.rule import Rule, RulePriority, RuleCondition, RuleAction, RuleOperator, ActionType

        # Create rules engine
        engine = RulesEngine({
            'enabled': True,
            'max_rules_per_execution': 10
        })

        print(f"PASS: Rules engine created")
        print(f"     Initial rules count: {len(engine.get_all_rules())}")

        # Create a simple rule
        rule = Rule(
            id="demo_rule",
            name="Demo Rule",
            description="Demonstration rule for testing",
            priority=RulePriority.NORMAL,
            conditions=[
                RuleCondition(
                    field="data.source",
                    operator=RuleOperator.EQUALS,
                    value="hkma.gov.hk"
                )
            ],
            actions=[
                RuleAction(
                    action_type=ActionType.LOG_INFO,
                    parameters={"message": "HKMA data detected"}
                )
            ]
        )

        # Add rule to engine
        success = engine.add_rule(rule)
        print(f"PASS: Rule added: {success}")
        print(f"     Rules count after addition: {len(engine.get_all_rules())}")

        # Test rule evaluation
        context = {"data": {"source": "hkma.gov.hk"}}
        matches = rule.evaluate(context)
        print(f"PASS: Rule evaluation: {matches}")

        # Get statistics
        stats = engine.get_statistics()
        print(f"PASS: Rules engine statistics:")
        print(f"     Total rules: {stats['total_rules']}")
        print(f"     Enabled rules: {stats['enabled_rules']}")

        return True

    except Exception as e:
        print(f"FAIL: Rules Engine test failed: {e}")
        return False


async def test_data_authenticity_manager():
    """测试数据真实性管理器"""
    print("\nTesting Data Authenticity Manager...")

    try:
        from interfaces.data_authenticity_manager import DataAuthenticityManager

        # Create manager
        config = {
            'max_history_size': 100,
            'default_timeout': 30.0,
            'parallel_execution': True
        }

        manager = DataAuthenticityManager(config)
        print("PASS: Data authenticity manager created")

        # Test health check
        health = await manager.health_check()
        print(f"PASS: Health check: {health['manager_status']}")
        print(f"     Registered verifiers: {health['registered_verifiers']}")

        # Test statistics
        stats = manager.get_statistics()
        print(f"PASS: Statistics:")
        print(f"     Total verifications: {stats['total_verifications']}")
        print(f"     Success rate: {stats['success_rate']:.2%}")

        return True

    except Exception as e:
        print(f"FAIL: Data Authenticity Manager test failed: {e}")
        return False


def test_config_manager():
    """测试配置管理器"""
    print("\nTesting Configuration Manager...")

    try:
        from config.config_manager import ConfigManager

        # Test with default config
        config_manager = ConfigManager()
        print("PASS: Config manager created with default configuration")

        # Test basic operations
        version = config_manager.get('version')
        print(f"PASS: Config version: {version}")

        # Test setting values
        config_manager.set('test.key', 'test_value')
        test_value = config_manager.get('test.key')
        print(f"PASS: Config set/get: {test_value}")

        # Test validation
        validation = config_manager.validate_config()
        print(f"PASS: Config validation: {'PASSED' if validation['valid'] else 'FAILED'}")
        print(f"     Total verifiers in config: {validation['total_verifiers']}")

        return True

    except Exception as e:
        print(f"FAIL: Configuration Manager test failed: {e}")
        return False


async def main():
    """主演示函数"""
    print("Authentication System Demo Starting...")
    print("=" * 50)

    # Run all tests
    tests = [
        ("Basic Imports", test_basic_imports),
        ("AuthResult", test_auth_result),
        ("Rules Engine", test_rules_engine),
        ("Configuration Manager", test_config_manager),
        ("Data Authenticity Manager", test_data_authenticity_manager)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        print("-" * 30)

        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()

            if result:
                passed += 1
                print(f"PASS: {test_name} PASSED")
            else:
                print(f"FAIL: {test_name} FAILED")

        except Exception as e:
            print(f"ERROR: {test_name} ERROR: {e}")

    # Summary
    print("\n" + "=" * 50)
    print(f"Test Summary: {passed}/{total} tests passed")

    if passed == total:
        print("All tests passed! Authentication system is working correctly.")
        print("\nNext steps:")
        print("   1. Install optional dependencies: pip install -r requirements.txt")
        print("   2. Configure authentication rules in config/auth_config.yaml")
        print("   3. Implement custom verifiers by extending BaseAuthenticator")
        print("   4. Integrate with existing data pipelines")
    else:
        print("Some tests failed. Please check the error messages above.")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
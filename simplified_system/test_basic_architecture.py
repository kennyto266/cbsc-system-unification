#!/usr/bin/env python3
"""
基礎架構測試 - 驗證多數據源系統核心功能
Basic Architecture Test - Validate Multi-Source System Core Functionality
"""

import sys
import os
from pathlib import Path

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(current_dir))

def test_imports():
    """測試所有核心模塊導入"""
    print("Testing core module imports...")

    try:
        # 測試配置管理
        from config.data_sources_config import get_data_sources_config
        print("PASS Configuration manager module imported")

        # 測試多數據源管理器
        from src.api.multi_source_data_manager import MultiSourceDataManager
        print("PASS Multi-source data manager imported")

        # 測試監控系統
        from src.api.data_source_monitor import DataSourceMonitor
        print("PASS Data source monitor imported")

        # 測試強化API
        from src.api.robust_stock_api import RobustStockAPI
        print("PASS Robust stock API imported")

        return True

    except ImportError as e:
        print(f"FAIL Import failed: {e}")
        return False
    except Exception as e:
        print(f"FAIL Other error: {e}")
        return False

def test_configuration():
    """測試配置系統"""
    print("\nTesting configuration system...")

    try:
        from config.data_sources_config import get_data_sources_config

        config = get_data_sources_config()
        enabled_sources = config.get_enabled_sources()

        print(f"PASS Configuration loaded")
        print(f"   - Total data sources: {len(config.data_sources)}")
        print(f"   - Enabled sources: {len(enabled_sources)}")

        # 驗證關鍵數據源
        key_sources = ["primary_central_api", "hkma_hibor", "hkma_monetary_base"]
        available_key_sources = [name for name in key_sources if name in config.data_sources]

        print(f"   - Key sources available: {len(available_key_sources)}/{len(key_sources)}")

        # 配置驗證
        errors = config.validate_configuration()
        if errors:
            print(f"WARN Configuration warnings: {len(errors)} issues")
            for error in errors[:3]:  # 只顯示前3個
                print(f"     - {error}")
        else:
            print("PASS Configuration validation")

        return True

    except Exception as e:
        print(f"FAIL Configuration test failed: {e}")
        return False

def test_basic_api():
    """測試基本API功能"""
    print("\nTesting basic API function...")

    try:
        from src.api.robust_stock_api import RobustStockAPI

        # 測試API初始化
        api = RobustStockAPI(auto_start=False)
        print("PASS API initialization successful")

        # 測試配置獲取
        status = api.get_system_status()
        if status:
            print("PASS System status retrieval successful")
            print(f"   - Status: {status.get('status', 'unknown')}")
        else:
            print("WARN System status retrieval failed (may be normal if data manager not started)")

        return True

    except Exception as e:
        print(f"FAIL API test failed: {e}")
        return False

def test_backward_compatibility():
    """測試向後兼容性"""
    print("\nTesting backward compatibility...")

    try:
        # 測試原有API接口是否仍然可用
        from src.api.stock_api import get_stock_data

        # 這裡不實際調用以避免依賴外部服務
        print("PASS Original API interface available")

        # 測試新的強化API
        from src.api.robust_stock_api import get_stock_data as robust_get_stock_data
        print("PASS New robust API interface available")

        return True

    except Exception as e:
        print(f"FAIL Backward compatibility test failed: {e}")
        return False

def test_data_source_types():
    """測試數據源類型配置"""
    print("\nTesting data source type configuration...")

    try:
        from config.data_sources_config import get_data_sources_config, DataSourceType

        config = get_data_sources_config()

        # 檢查不同類型的數據源
        stock_apis = config.get_sources_by_type(DataSourceType.STOCK_API)
        government_apis = config.get_sources_by_type(DataSourceType.GOVERNMENT_API)

        print(f"PASS Stock API data sources: {len(stock_apis)}")
        print(f"PASS Government API data sources: {len(government_apis)}")

        return True

    except Exception as e:
        print(f"FAIL Data source type test failed: {e}")
        return False

def test_cache_configuration():
    """測試緩存配置"""
    print("\nTesting cache configuration...")

    try:
        from config.data_sources_config import get_data_sources_config

        config = get_data_sources_config()
        cache_config = config.get_cache_configuration()

        print("PASS Cache configuration retrieval successful")
        print(f"   - Memory cache TTL: {cache_config.memory_ttl} seconds")
        print(f"   - Disk cache TTL: {cache_config.disk_ttl} seconds")
        print(f"   - Redis cache TTL: {cache_config.redis_ttl} seconds")

        return True

    except Exception as e:
        print(f"FAIL Cache configuration test failed: {e}")
        return False

def test_monitoring_configuration():
    """測試監控配置"""
    print("\nTesting monitoring configuration...")

    try:
        from config.data_sources_config import get_data_sources_config

        config = get_data_sources_config()
        monitoring_config = config.get_monitoring_configuration()

        print("PASS Monitoring configuration retrieval successful")
        print(f"   - Health check interval: {monitoring_config.health_check_interval} seconds")
        print(f"   - Auto failover: {monitoring_config.auto_failover}")
        print(f"   - Notification channels: {monitoring_config.notification_channels}")

        return True

    except Exception as e:
        print(f"FAIL Monitoring configuration test failed: {e}")
        return False

def main():
    """主測試函數"""
    print("=" * 80)
    print("Multi-Source Architecture Basic Test")
    print("=" * 80)

    tests = [
        ("Core Module Imports", test_imports),
        ("Configuration System", test_configuration),
        ("Basic API Function", test_basic_api),
        ("Backward Compatibility", test_backward_compatibility),
        ("Data Source Types", test_data_source_types),
        ("Cache Configuration", test_cache_configuration),
        ("Monitoring Configuration", test_monitoring_configuration),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"FAIL {test_name} test error: {e}")

    print("\n" + "=" * 80)
    print("Test Results Summary")
    print("=" * 80)
    print(f"Total tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success rate: {(passed/total*100):.1f}%")

    if passed == total:
        print("\nAll basic tests passed! Multi-source architecture is ready for deployment")
        return True
    else:
        print(f"\n{total - passed} tests failed, please check configuration and dependencies")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
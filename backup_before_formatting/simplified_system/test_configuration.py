#!/usr/bin/env python3
"""
Simplified System - Configuration Test
简化系统 - 配置测试

测试新的配置管理系统是否正常工作。
"""

import sys
import os
import logging
from pathlib import Path

# Add the simplified_system path
sys.path.append(str(Path(__file__).parent))

def test_config_manager():
    """测试配置管理器"""
    print("Testing Configuration Manager...")

    try:
        from config import get_config_manager, get_config, get_data_source_config, get_performance_config

        # 获取配置管理器
        manager = get_config_manager()
        print(f"Configuration Manager initialized successfully")

        # 测试系统配置
        system_config = get_config()
        print(f"✅ System Config: Environment={system_config.environment}, Debug={system_config.debug}")

        # 测试数据源配置
        data_config = get_data_source_config()
        print(f"✅ Data Source Config: API URL={data_config.stock_api['base_url']}")
        print(f"✅ Government Data Sources: {len(data_config.government_data)} configured")

        # 测试性能配置
        perf_config = get_performance_config()
        print(f"✅ Performance Config: GPU Enabled={perf_config.gpu['enabled']}")
        print(f"✅ Caching Enabled={perf_config.caching['enabled']}")

        return True

    except Exception as e:
        print(f"❌ Configuration Manager test failed: {e}")
        return False

def test_stock_api():
    """测试股票API配置"""
    print("\n🧪 Testing Stock API with New Configuration...")

    try:
        from src.api.stock_api import StockDataAPI

        # 初始化API
        api = StockDataAPI()
        print(f"✅ Stock API initialized successfully")
        print(f"✅ Base URL: {api.api_base_url}")
        print(f"✅ Request Timeout: {api.request_timeout}")
        print(f"✅ Cache Timeout: {api.cache_timeout}")

        return True

    except Exception as e:
        print(f"❌ Stock API test failed: {e}")
        return False

def test_strategy_manager():
    """测试策略管理器"""
    print("\n🧪 Testing Strategy Manager...")

    try:
        from src.strategies import get_strategy_manager

        # 获取策略管理器
        manager = get_strategy_manager()
        print(f"✅ Strategy Manager initialized successfully")

        # 列出可用策略
        strategies = manager.list_strategies()
        print(f"✅ Available Strategies: {len(strategies)} strategies")
        for strategy in strategies:
            print(f"   - {strategy}")

        # 获取策略摘要
        summary = manager.get_strategy_summary()
        print(f"✅ Strategy Summary: {summary}")

        return True

    except Exception as e:
        print(f"❌ Strategy Manager test failed: {e}")
        return False

def main():
    """主测试函数"""
    print("Starting Simplified System Configuration Tests")
    print("=" * 60)

    # 设置日志级别
    logging.basicConfig(level=logging.INFO)

    # 运行测试
    tests = [
        test_config_manager,
        test_stock_api,
        test_strategy_manager
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print("\n" + "=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("All configuration tests passed successfully!")
        return True
    else:
        print("Some tests failed. Please check the configuration setup.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
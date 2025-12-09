#!/usr / bin / env python3
"""
Simple Configuration Test
简化配置测试
"""

import sys
from pathlib import Path

# Add the simplified_system path
sys.path.append(str(Path(__file__).parent))


def test_config():
    """测试配置管理"""
    print("Testing configuration system...")

    try:
        from config import get_config_manager

        get_config_manager()
        print("Config manager initialized successfully")

        # Test system config
        from config import get_config, get_data_source_config

        system_config = get_config()
        data_config = get_data_source_config()

        print(f"Environment: {system_config.environment}")
        print(f"Debug: {system_config.debug}")
        print(f"Stock API URL: {data_config.stock_api['base_url']}")
        print("Configuration test PASSED")
        return True

    except Exception as e:
        print(f"Configuration test FAILED: {e}")
        return False


if __name__ == "__main__":
    success = test_config()
    sys.exit(0 if success else 1)

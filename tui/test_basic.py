#!/usr/bin/env python
"""
CBSC TUI 基礎測試腳本
測試所有模組可以正確導入
"""
import sys
import asyncio

def test_imports():
    """測試所有模組導入"""
    print("[TEST] Testing module imports...")

    try:
        # API 模組
        print("  [OK] API clients...")
        from api.client import CBSCAPIClient
        from api.websocket_client import CBSCWebSocketClient

        # Widgets 模組
        print("  [OK] Widgets...")
        from widgets.strategy_list import StrategyList
        from widgets.system_metrics import SystemMetrics
        from widgets.log_viewer import LogViewer
        from widgets.table_browser import TableBrowser

        # Screens 模組
        print("  [OK] Screens...")
        from screens.main_menu import MainMenuScreen
        from screens.strategies import StrategyScreen
        from screens.monitor import MonitorScreen
        from screens.logs import LogScreen
        from screens.database import DatabaseScreen
        from screens.settings import SettingsScreen

        # Utils 模組
        print("  [OK] Utils...")
        from utils.config import Config

        print("[PASS] All modules imported successfully!\n")
        return True

    except ImportError as e:
        print(f"[FAIL] Import failed: {e}\n")
        return False
    except Exception as e:
        print(f"[FAIL] Error: {e}\n")
        return False

def test_api_client():
    """測試 API 客戶端初始化"""
    print("[TEST] Testing API client...")

    try:
        from api.client import CBSCAPIClient
        client = CBSCAPIClient()
        assert client.base_url is not None
        print(f"  [OK] API URL: {client.base_url}")
        print("[PASS] API client test passed!\n")
        return True
    except Exception as e:
        print(f"[FAIL] API client test failed: {e}\n")
        return False

def test_config():
    """測試配置管理"""
    print("[TEST] Testing config manager...")

    try:
        from utils.config import Config
        config = Config()
        assert config.get("api_url") is not None
        print(f"  [OK] API URL: {config.get('api_url')}")
        print(f"  [OK] Theme: {config.get('theme')}")
        print("[PASS] Config manager test passed!\n")
        return True
    except Exception as e:
        print(f"[FAIL] Config manager test failed: {e}\n")
        return False

async def test_websocket_client():
    """測試 WebSocket 客戶端初始化"""
    print("[TEST] Testing WebSocket client...")

    try:
        from api.websocket_client import CBSCWebSocketClient
        client = CBSCWebSocketClient()
        assert client.ws_url is not None
        print(f"  [OK] WS URL: {client.ws_url}")
        print("[PASS] WebSocket client test passed!\n")
        return True
    except Exception as e:
        print(f"[FAIL] WebSocket client test failed: {e}\n")
        return False

def main():
    """運行所有測試"""
    print("=" * 50)
    print("CBSC TUI Basic Tests")
    print("=" * 50)
    print()

    results = []

    # 測試導入
    results.append(test_imports())

    # 測試 API 客戶端
    results.append(test_api_client())

    # 測試配置管理
    results.append(test_config())

    # 測試 WebSocket 客戶端
    results.append(asyncio.run(test_websocket_client()))

    # 總結
    print("=" * 50)
    if all(results):
        print("[PASS] All tests passed!")
        print("=" * 50)
        return 0
    else:
        print("[FAIL] Some tests failed")
        print("=" * 50)
        return 1

if __name__ == "__main__":
    sys.exit(main())

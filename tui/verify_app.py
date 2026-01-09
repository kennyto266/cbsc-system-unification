#!/usr/bin/env python
"""
驗證 TUI 應用可以正常啟動
"""
import sys

def test_app_can_start():
    """測試應用初始化"""
    print("[TEST] Testing CBSCApp initialization...")

    try:
        from main import CBSCApp
        app = CBSCApp()

        # 驗證基本屬性
        assert app.TITLE == "CBSC 量化交易系統"
        assert app.CSS_PATH == "styles/base.css"
        assert hasattr(app, 'api_client')
        assert hasattr(app, 'ws_client')

        print(f"  [OK] App title: {app.TITLE}")
        print(f"  [OK] CSS path: {app.CSS_PATH}")
        print(f"  [OK] API client: {type(app.api_client).__name__}")
        print(f"  [OK] WebSocket client: {type(app.ws_client).__name__}")

        print("[PASS] CBSCApp initialization successful!\n")
        return True

    except Exception as e:
        print(f"[FAIL] CBSCApp initialization failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def test_screens():
    """測試所有屏幕可以初始化"""
    print("[TEST] Testing all screens...")

    try:
        from screens.main_menu import MainMenuScreen
        from screens.strategies import StrategyScreen
        from screens.monitor import MonitorScreen
        from screens.logs import LogScreen
        from screens.database import DatabaseScreen
        from screens.settings import SettingsScreen

        print("  [OK] MainMenuScreen")
        print("  [OK] StrategyScreen")
        print("  [OK] MonitorScreen")
        print("  [OK] LogScreen")
        print("  [OK] DatabaseScreen")
        print("  [OK] SettingsScreen")

        print("[PASS] All screens can be imported!\n")
        return True

    except Exception as e:
        print(f"[FAIL] Screen import failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def main():
    """運行驗證"""
    print("=" * 50)
    print("CBSC TUI Application Verification")
    print("=" * 50)
    print()

    results = []

    # 測試應用初始化
    results.append(test_app_can_start())

    # 測試屏幕
    results.append(test_screens())

    # 總結
    print("=" * 50)
    if all(results):
        print("[PASS] Application is ready to run!")
        print("\nTo start the TUI, run:")
        print("  cd tui")
        print("  python main.py")
        print("\nNote: The TUI requires an interactive terminal.")
        print("=" * 50)
        return 0
    else:
        print("[FAIL] Some checks failed")
        print("=" * 50)
        return 1

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
快速修復啟動器 - 繞過複雜依賴問題
直接使用可用的Simplified System
"""

import sys
import os
from pathlib import Path

# 設置UTF-8編碼
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

print("🚀 正在啟動量化交易系統...")
print("=" * 60)

def check_simplified_system():
    """檢查Simplified System是否可用"""
    try:
        # 檢查simplified_system目錄
        ss_path = Path("simplified_system")
        if not ss_path.exists():
            print("❌ Simplified System目錄不存在")
            return False

        # 檢查核心模塊
        core_files = [
            "src/api/stock_api.py",
            "src/indicators/core_indicators.py",
            "src/backtest/vectorbt_engine.py",
            "integration_test.py"
        ]

        for file_path in core_files:
            full_path = ss_path / file_path
            if not full_path.exists():
                print(f"❌ 缺失核心文件: {file_path}")
                return False

        print("✅ Simplified System核心文件檢查通過")
        return True

    except Exception as e:
        print(f"❌ 檢查Simplified System失敗: {e}")
        return False

def test_basic_imports():
    """測試基本導入"""
    try:
        # 測試基本模塊
        import pandas as pd
        import numpy as np
        import requests
        print("✅ 基本Python模塊導入成功")

        # 測試Simplified System
        sys.path.insert(0, str(Path("simplified_system")))
        from src.api.stock_api import get_hk_stock_data
        print("✅ Simplified System股票API導入成功")

        return True

    except Exception as e:
        print(f"❌ 導入測試失敗: {e}")
        return False

def show_simple_menu():
    """顯示簡化菜單"""
    print("\n" + "=" * 60)
    print("🎯 香港量化交易系統 - 簡化版")
    print("=" * 60)
    print("可用功能:")
    print("  1. 📊 獲取股票數據 (0700.HK)")
    print("  2. 📈 技術指標分析")
    print("  3. 🔄 VectorBT回測")
    print("  4. 📡 政府數據查看")
    print("  5. 🔧 系統狀態")
    print("  6. 🧪 集成測試")
    print("  0. 🚪 退出")
    print("-" * 60)

def get_stock_data_demo():
    """獲取股票數據演示"""
    try:
        print("\n📊 正在獲取0700.HK股票數據...")
        from src.api.stock_api import get_hk_stock_data

        data = get_hk_stock_data("0700.HK", 30)  # 獲取30天數據
        if data is not None and not data.empty:
            print(f"✅ 成功獲取 {len(data)} 條數據記錄")
            print(f"📅 數據範圍: {data.index[0]} 至 {data.index[-1]}")
            print(f"💰 最新收盤價: {data['close'].iloc[-1]:.2f} HKD")
            print("\n最近5天數據:")
            print(data[['open', 'high', 'low', 'close', 'volume']].tail())
        else:
            print("❌ 獲取數據失敗")

    except Exception as e:
        print(f"❌ 股票數據獲取失敗: {e}")

def technical_analysis_demo():
    """技術分析演示"""
    try:
        print("\n📈 正在進行技術指標分析...")
        from src.api.stock_api import get_hk_stock_data
        from src.indicators.core_indicators import CoreIndicators

        # 獲取數據
        data = get_hk_stock_data("0700.HK", 100)
        if data is None or data.empty:
            print("❌ 無法獲取股票數據")
            return

        # 計算技術指標
        indicators = CoreIndicators()
        close_prices = data['close']

        # RSI
        rsi = indicators.calculate_rsi(close_prices, 14)
        print(f"📊 RSI(14): {rsi.iloc[-1]:.2f}")

        # 移動平均
        sma_20 = indicators.calculate_sma(close_prices, 20)
        print(f"📊 SMA(20): {sma_20.iloc[-1]:.2f}")

        # MACD
        macd_line, signal_line, histogram = indicators.calculate_macd(close_prices)
        print(f"📊 MACD: {macd_line.iloc[-1]:.4f}")
        print(f"📊 Signal: {signal_line.iloc[-1]:.4f}")

        print("✅ 技術指標計算完成")

    except Exception as e:
        print(f"❌ 技術分析失敗: {e}")

def vectorbt_backtest_demo():
    """VectorBT回測演示"""
    try:
        print("\n🔄 正在進行VectorBT回測...")
        from src.api.stock_api import get_hk_stock_data
        from src.backtest.vectorbt_engine import VectorBTEngine

        # 獲取數據
        data = get_hk_stock_data("0700.HK", 252)  # 1年數據
        if data is None or data.empty:
            print("❌ 無法獲取股票數據")
            return

        # 創建回測引擎
        engine = VectorBTEngine()

        # 執行RSI均值回歸策略回測
        result = engine.backtest_strategy(
            data,
            "RSI_MEAN_REVERSION",
            {'period': 14, 'oversold': 30, 'overbought': 70}
        )

        if result:
            print(f"📊 回測結果:")
            print(f"   總回報: {result.total_return:.2%}")
            print(f"   Sharpe比率: {result.sharpe_ratio:.3f}")
            print(f"   最大回撤: {result.max_drawdown:.2%}")
            print(f"   交易次數: {result.total_trades}")
        else:
            print("❌ 回測執行失敗")

    except Exception as e:
        print(f"❌ VectorBT回測失敗: {e}")

def government_data_demo():
    """政府數據演示"""
    try:
        print("\n📡 正在獲取香港政府數據...")
        from src.api.government_data import get_latest_hibor

        # 獲取最新HIBOR數據
        hibor_data = get_latest_hibor()
        if hibor_data:
            print("✅ HIBOR數據:")
            for tenor, rate in hibor_data.items():
                print(f"   {tenor}: {rate}%")
        else:
            print("⚠️  HIBOR數據暫時不可用")

    except Exception as e:
        print(f"❌ 政府數據獲取失敗: {e}")

def system_status():
    """系統狀態"""
    print("\n🔧 系統狀態檢查:")

    # 檢查Python版本
    print(f"   Python版本: {sys.version}")

    # 檢查核心依賴
    try:
        import pandas as pd
        print(f"   Pandas: ✅ v{pd.__version__}")
    except:
        print("   Pandas: ❌")

    try:
        import numpy as np
        print(f"   NumPy: ✅ v{np.__version__}")
    except:
        print("   NumPy: ❌")

    try:
        import requests
        print(f"   Requests: ✅ v{requests.__version__}")
    except:
        print("   Requests: ❌")

    # 檢查可選依賴
    try:
        import vectorbt
        print(f"   VectorBT: ✅ v{vectorbt.__version__}")
    except:
        print("   VectorBT: ⚠️  未安裝")

    try:
        import sklearn
        print(f"   Scikit-learn: ✅ v{sklearn.__version__}")
    except:
        print("   Scikit-learn: ⚠️  未安裝")

def integration_test():
    """集成測試"""
    try:
        print("\n🧪 正在運行集成測試...")

        # 安全運行Simplified System集成測試
        return safe_run_integration_test()

    except Exception as e:
        print(f"❌ 集成測試失敗: {e}")
        return False

def safe_run_integration_test():
    """Safely run integration test without exec()"""
    import importlib.util

    test_dir = "simplified_system"
    test_module = "integration_test"

    try:
        # Check if directory exists
        if not os.path.exists(test_dir):
            print(f"❌ 測試目錄不存在: {test_dir}")
            return False

        # Change to test directory
        original_dir = os.getcwd()
        os.chdir(test_dir)

        # Check if module file exists
        if not os.path.exists(f"{test_module}.py"):
            print(f"❌ 測試模塊不存在: {test_module}.py")
            os.chdir(original_dir)
            return False

        # Import the module safely
        spec = importlib.util.spec_from_file_location(test_module, f"{test_module}.py")
        if spec is None or spec.loader is None:
            print(f"❌ 無法加載測試模塊: {test_module}")
            os.chdir(original_dir)
            return False

        module = importlib.util.module_from_spec(spec)

        # Execute the module safely
        spec.loader.exec_module(module)

        print(f"✅ 集成測試成功完成: {test_module}")
        os.chdir(original_dir)
        return True

    except ImportError as e:
        print(f"❌ 導入錯誤: {e}")
        os.chdir(original_dir)
        return False
    except Exception as e:
        print(f"❌ 執行集成測試時發生錯誤: {e}")
        os.chdir(original_dir)
        return False

def main():
    """主程序"""
    print("正在檢查系統環境...")

    # 檢查Simplified System
    if not check_simplified_system():
        print("❌ Simplified System不可用，無法啟動")
        return

    # 測試基本導入
    if not test_basic_imports():
        print("❌ 基本導入失敗，無法啟動")
        return

    print("✅ 系統檢查通過，可以開始使用")

    # 主菜單循環
    while True:
        show_simple_menu()

        try:
            choice = input("\n請選擇功能 (0-6): ").strip()

            if choice == '0':
                print("👋 再見！")
                break
            elif choice == '1':
                get_stock_data_demo()
            elif choice == '2':
                technical_analysis_demo()
            elif choice == '3':
                vectorbt_backtest_demo()
            elif choice == '4':
                government_data_demo()
            elif choice == '5':
                system_status()
            elif choice == '6':
                integration_test()
            else:
                print("❌ 無效選擇，請輸入0-6")

        except KeyboardInterrupt:
            print("\n\n👋 用戶中斷，再見！")
            break
        except Exception as e:
            print(f"❌ 發生錯誤: {e}")

        # 暫停等待用戶
        input("\n按Enter鍵繼續...")

if __name__ == "__main__":
    main()
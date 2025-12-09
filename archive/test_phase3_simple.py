#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 3 技術分析功能簡化測試腳本
"""

import sys
import os
from pathlib import Path

# 添加項目根目錄到Python路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "simplified_system"))

def test_imports():
    """測試核心模塊導入"""
    print("=" * 50)
    print("Phase 3 Technical Analysis Test")
    print("=" * 50)

    try:
        # 測試核心指標導入
        print("Testing CoreIndicators import...")
        from simplified_system.src.indicators.core_indicators import CoreIndicators
        print("CoreIndicators: PASS")

        # 測試技術分析器導入
        print("Testing TechnicalAnalyzer import...")
        from simplified_system.src.indicators.technical_analyzer import TechnicalAnalyzer
        print("TechnicalAnalyzer: PASS")

        # 測試配置管理器導入
        print("Testing ConfigManager import...")
        from config.config_manager import ConfigManager
        print("ConfigManager: PASS")

        # 測試主界面類導入
        print("Testing InteractiveQuantitativeTrader import...")
        from interactive_quantitative_trader import InteractiveQuantitativeTrader
        print("InteractiveQuantitativeTrader: PASS")

        return True

    except Exception as e:
        print(f"Import failed: {e}")
        return False

def test_basic_functionality():
    """測試基本功能"""
    print("\n" + "=" * 50)
    print("Testing Basic Functionality")
    print("=" * 50)

    try:
        import pandas as pd
        import numpy as np

        # 生成測試數據
        from datetime import datetime, timedelta
        dates = pd.date_range(end=datetime.now(), periods=100, freq='D')

        # 生成價格數據
        base_price = 450.0
        price_data = []

        for i in range(100):
            trend = i * 0.5
            noise = np.random.normal(0, 5)
            close_price = base_price + trend + noise
            high_price = close_price + abs(np.random.normal(0, 3))
            low_price = close_price - abs(np.random.normal(0, 3))
            open_price = close_price + np.random.normal(0, 2)
            volume = np.random.randint(1000000, 5000000)
            price_data.append([open_price, high_price, low_price, close_price, volume])

        df = pd.DataFrame(price_data, index=dates, columns=['open', 'high', 'low', 'close', 'volume'])
        print(f"Test data generated: {len(df)} records")

        # 測試指標計算
        from simplified_system.src.indicators.core_indicators import CoreIndicators
        indicators = CoreIndicators()

        # RSI
        rsi = indicators.calculate_rsi(df['close'], 14)
        print(f"RSI(14): {rsi.iloc[-1]:.2f}")

        # SMA
        sma = indicators.calculate_sma(df['close'], 20)
        print(f"SMA(20): {sma.iloc[-1]:.2f}")

        # MACD
        macd = indicators.calculate_macd(df['close'])
        print(f"MACD: {macd['macd'].iloc[-1]:.4f}")

        # 布林帶
        bb = indicators.calculate_bollinger_bands(df['close'])
        print(f"Bollinger Upper: {bb['upper'].iloc[-1]:.2f}")
        print(f"Bollinger Lower: {bb['lower'].iloc[-1]:.2f}")

        return True

    except Exception as e:
        print(f"Basic functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_configuration():
    """測試配置功能"""
    print("\n" + "=" * 50)
    print("Testing Configuration System")
    print("=" * 50)

    try:
        from config.config_manager import ConfigManager

        config_manager = ConfigManager()

        # 測試獲取配置
        rsi_config = config_manager.get('indicators.rsi', {})
        sma_config = config_manager.get('indicators.sma', {})

        print(f"RSI config: {rsi_config}")
        print(f"SMA config: {sma_config}")

        # 測試設置配置
        config_manager.set('test.value', 'test_data')
        test_value = config_manager.get('test.value')
        print(f"Config set/get test: {test_value}")

        return True

    except Exception as e:
        print(f"Configuration test failed: {e}")
        return False

def main():
    """主測試函數"""
    print("Phase 3 Technical Analysis Implementation Test")
    print("=" * 70)

    tests = [
        ("Module Imports", test_imports),
        ("Basic Functionality", test_basic_functionality),
        ("Configuration System", test_configuration)
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "PASS" if result else "FAIL"
            print(f"{test_name}: {status}")
        except Exception as e:
            print(f"{test_name}: ERROR - {e}")
            results.append((test_name, False))

    # 總結
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("SUCCESS: All Phase 3 tests passed!")
        print("Technical Analysis Features Implemented Successfully!")
        return 0
    else:
        print("FAILURE: Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
簡化的VectorBT多進程引擎測試 - 無外部依賴
"""

import sys
import os
import asyncio
from datetime import date
from typing import Dict, Any

# 添加項目路徑
sys.path.append('.')

def test_basic_import():
    """測試基本導入（無外部依賴版本）"""
    try:
        # 測試核心數據結構導入
        from src.backtest.vectorbt_multiprocess_engine import (
            MultiprocessMode,
            VectorBTMultiprocessConfig
        )
        print("✓ 核心配置模組導入成功")
        return True
    except ImportError as e:
        print(f"✗ 導入失敗: {e}")
        return False

def test_config_creation():
    """測試配置創建"""
    try:
        from src.backtest.vectorbt_multiprocess_engine import (
            VectorBTMultiprocessConfig,
            MultiprocessMode
        )

        config = VectorBTMultiprocessConfig(
            symbols=["0700.HK", "0388.HK"],
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            execution_mode=MultiprocessMode.PORTFOLIO_LEVEL,
            max_workers=4
        )

        print(f"✓ 配置創建成功: {len(config.symbols)} 個股票, 模式: {config.execution_mode}")
        return config
    except Exception as e:
        print(f"✗ 配置創建失敗: {e}")
        return None

def test_multiprocess_modes():
    """測試多進程模式枚舉"""
    try:
        from src.backtest.vectorbt_multiprocess_engine import MultiprocessMode

        # 測試所有模式
        modes = [
            MultiprocessMode.PORTFOLIO_LEVEL,
            MultiprocessMode.STRATEGY_LEVEL,
            MultiprocessMode.SYMBOL_LEVEL,
            MultiprocessMode.PARAMETER_LEVEL,
            MultiprocessMode.HYBRID
        ]

        print(f"✓ 支持的執行模式: {[mode.value for mode in modes]}")
        return True
    except Exception as e:
        print(f"✗ 模式測試失敗: {e}")
        return False

def test_mock_engine_functionality():
    """測試Mock引擎功能"""
    try:
        from src.backtest.vectorbt_multiprocess_engine import (
            VectorBTMultiprocessConfig,
            MultiprocessMode
        )

        # 創建基本配置
        config = VectorBTMultiprocessConfig(
            symbols=["0700.HK"],
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31)
        )

        # 測試配置序列化
        config_dict = {
            'symbols': config.symbols,
            'start_date': config.start_date.isoformat(),
            'end_date': config.end_date.isoformat(),
            'execution_mode': config.execution_mode,
            'max_workers': config.max_workers
        }

        print(f"✓ 配置序列化: {config_dict}")
        return True
    except Exception as e:
        print(f"✗ Mock引擎測試失敗: {e}")
        return False

def test_basic_strategy_logic():
    """測試基本策略邏輯"""
    try:
        import numpy as np
        import pandas as pd

        # 創建模擬數據
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        prices = np.random.randn(100).cumsum() + 100
        data = pd.Series(prices, index=dates)

        # 簡單的RSI策略邏輯測試
        def simple_rsi_strategy(prices, window=14):
            """簡單RSI策略"""
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi

        rsi = simple_rsi_strategy(data)
        print(f"✓ RSI計算成功: 最終值 {rsi.iloc[-1]:.2f}")
        return True
    except Exception as e:
        print(f"✗ 策略邏輯測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("開始VectorBT多進程引擎簡化測試...")
    print("=" * 50)

    tests = [
        ("基本導入測試", test_basic_import),
        ("配置創建測試", test_config_creation),
        ("多進程模式測試", test_multiprocess_modes),
        ("Mock引擎功能測試", test_mock_engine_functionality),
        ("基本策略邏輯測試", test_basic_strategy_logic)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n執行測試: {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"✓ {test_name} 通過")
            else:
                print(f"✗ {test_name} 失敗")
        except Exception as e:
            print(f"✗ {test_name} 異常: {e}")

    print(f"\n測試完成！通過率: {passed}/{total} ({passed/total*100:.1f}%)")
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
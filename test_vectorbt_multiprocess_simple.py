#!/usr/bin/env python3
"""
簡單的VectorBT多進程引擎測試
"""

import sys
import os
import asyncio
from datetime import date

# 添加項目路徑
sys.path.append('.')

def test_basic_import():
    """測試基本導入"""
    try:
        from src.backtest.vectorbt_multiprocess_engine import (
            VectorBTMultiprocessEngine,
            VectorBTMultiprocessConfig,
            MultiprocessMode
        )
        print("VectorBT多進程引擎模組導入成功")
        return True
    except ImportError as e:
        print(f"導入失敗: {e}")
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

        print(f"配置創建成功: {len(config.symbols)} 個股票, 模式: {config.execution_mode}")
        return config
    except Exception as e:
        print(f"配置創建失敗: {e}")
        return None

async def test_engine_initialization():
    """測試引擎初始化"""
    try:
        from src.backtest.vectorbt_multiprocess_engine import (
            VectorBTMultiprocessEngine,
            VectorBTMultiprocessConfig,
            MultiprocessMode
        )

        config = VectorBTMultiprocessConfig(
            symbols=["0700.HK"],
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            execution_mode=MultiprocessMode.PORTFOLIO_LEVEL,
            max_workers=2
        )

        print("開始初始化引擎...")
        engine = VectorBTMultiprocessEngine(config)

        # 測試初始化
        success = await engine.initialize()

        if success:
            print(f"引擎初始化成功: {engine.engine_id}")
            return engine
        else:
            print("引擎初始化失敗")
            return None

    except Exception as e:
        print(f"引擎初始化失敗: {e}")
        return None

def main():
    """主測試函數"""
    print("開始VectorBT多進程引擎測試...")
    print("=" * 50)

    # 測試1: 基本導入
    print("測試1: 基本導入")
    if not test_basic_import():
        return False

    # 測試2: 配置創建
    print("\n測試2: 配置創建")
    config = test_config_creation()
    if not config:
        return False

    # 測試3: 引擎初始化
    print("\n測試3: 引擎初始化")
    engine = asyncio.run(test_engine_initialization())
    if not engine:
        return False

    # 測試4: 狀態監控
    print("\n測試4: 狀態監控")
    try:
        status = asyncio.run(engine.get_engine_status())
        print(f"引擎狀態: {status['config']['execution_mode']}")
        print(f"最大工作進程: {status['config']['max_workers']}")
        print(f"股票數量: {status['config']['symbols_count']}")
    except Exception as e:
        print(f"狀態監控失敗: {e}")

    # 清理
    try:
        asyncio.run(engine.shutdown())
        print("\n引擎已關閉")
    except Exception as e:
        print(f"關閉失敗: {e}")

    print("\n測試完成！")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
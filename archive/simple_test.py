#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最簡單的測試腳本 - 新手友好版本
運行方式: python simple_test.py
"""

print("=== 增強版綜合優化器 - 簡單測試 ===")

try:
    # 導入增強版優化器
    from enhanced_comprehensive_parameter_optimizer import EnhancedComprehensiveParameterOptimizer, EnhancedOptimizationConfig
    print("[OK] 成功導入增強版優化器")

    # 創建最簡配置
    config = EnhancedOptimizationConfig(
        max_workers=2,           # 2個工作線程
        use_gpu=False,           # 不用GPU，避免兼容問題
        use_intelligent_search=False,      # 不用智能搜索
        enable_real_time_monitoring=False, # 不用實時監控
        enable_statistical_validation=False, # 不用統計驗證
        enable_gpu_memory_management=False   # 不用GPU內存管理
    )
    print("[OK] 配置創建成功")

    # 創建優化器
    optimizer = EnhancedComprehensiveParameterOptimizer(config)
    print("[OK] 增強版優化器創建成功")

    # 檢查參數空間
    spaces = optimizer.define_parameter_spaces()
    print("\n=== 參數空間分析 ===")

    total_combinations = 0
    for strategy, space in spaces.items():
        print(f"{strategy}: {space.total_combinations:,} 個組合")
        total_combinations += space.total_combinations

    print(f"\n總計: {total_combinations:,} 個參數組合")

    # 檢查系統狀態
    print(f"\n=== 系統信息 ===")
    print(f"GPU可用: {'是' if optimizer.gpu_env.is_gpu_available() else '否'}")
    print(f"工作線程: {config.max_workers}")
    print(f"批量大小: {config.batch_size}")

    # 展示參數範圍
    print(f"\n=== 參數範圍 ===")
    for strategy, space in spaces.items():
        print(f"\n{strategy} 策略參數:")
        for param, values in space.parameters.items():
            print(f"  {param}: {min(values)} - {max(values)} (共{len(values)}個值)")

    print(f"\n🎉 測試完成! 系統完全就緒")
    print(f"💡 下一步: 您可以開始進行參數優化")

except ImportError as e:
    print(f"[導入錯誤] {e}")
    print("請確保在正確的項目目錄中運行此腳本")
except Exception as e:
    print(f"[錯誤] {e}")
    print("這是一個簡單的測試，請不要擔心")
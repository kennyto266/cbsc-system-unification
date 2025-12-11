#!/usr/bin/env python3
"""
CBSC數據遷移系統測試腳本

測試遷移系統的基本功能和準備情況。
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

def test_system_prerequisites():
    """測試系統先決條件"""
    print("=== CBSC數據遷移系統測試 ===")
    print(f"測試時間: {datetime.now()}")
    print()

    success_count = 0
    total_tests = 0

    # 1. 檢查Python版本
    total_tests += 1
    if sys.version_info >= (3, 8):
        print("[OK] Python版本檢查通過")
        print(f"  當前版本: {sys.version}")
        success_count += 1
    else:
        print("[ERROR] Python版本檢查失敗")
        print(f"  需要Python 3.8+, 當前版本: {sys.version}")

    # 2. 檢查必要目錄
    required_dirs = ['src', 'src/migrations', 'src/models', 'src/database']
    for dir_path in required_dirs:
        total_tests += 1
        if os.path.exists(dir_path):
            print(f"[OK] 目錄存在: {dir_path}")
            success_count += 1
        else:
            print(f"[ERROR] 目錄缺失: {dir_path}")

    # 3. 检查必要文件
    required_files = [
        'src/migrations/data_migration_executor.py',
        'src/migrations/migration_manager.py',
        'src/migrations/scripts/migration_001_create_unified_schema.py',
        'run_data_migration.py'
    ]
    for file_path in required_files:
        total_tests += 1
        if os.path.exists(file_path):
            print(f"[OK] 文件存在: {file_path}")
            success_count += 1
        else:
            print(f"[ERROR] 文件缺失: {file_path}")

    # 4. 檢查數據源文件
    print("\n--- 數據源檢查 ---")
    data_patterns = [
        "*_backtest_results_*.json",
        "*optimization_results_*.json",
        "*.csv"
    ]

    data_files_found = 0
    for pattern in data_patterns:
        files = list(Path('.').glob(pattern))
        if files:
            print(f"[OK] 找到 {len(files)} 個 {pattern} 文件")
            data_files_found += len(files)

            # 顯示前幾個文件
            for file_path in files[:3]:
                size_kb = file_path.stat().st_size / 1024
                print(f"  - {file_path.name} ({size_kb:.1f}KB)")

            if len(files) > 3:
                print(f"  ... 還有 {len(files) - 3} 個文件")

    if data_files_found == 0:
        print("[WARNING] 未找到數據源文件")
    else:
        total_tests += 1
        success_count += 1
        print(f"[OK] 總共找到 {data_files_found} 個數據源文件")

    # 5. 檢查配置文件
    print("\n--- 配置文件檢查 ---")
    config_files = ['.env', 'requirements.txt']
    for config_file in config_files:
        total_tests += 1
        if os.path.exists(config_file):
            print(f"[OK] 配置文件存在: {config_file}")
            success_count += 1
        else:
            print(f"[WARNING] 配置文件缺失: {config_file}")

    # 總結
    print(f"\n=== 測試結果總結 ===")
    print(f"通過測試: {success_count}/{total_tests}")
    print(f"成功率: {success_count/total_tests*100:.1f}%")

    if success_count == total_tests:
        print("[SUCCESS] 所有測試通過！遷移系統準備就緒。")
        return True
    elif success_count >= total_tests * 0.8:
        print("[WARNING] 大部分測試通過，可以嘗試遷移，但建議先解決失敗項。")
        return True
    else:
        print("[ERROR] 多項測試失敗，請先解決問題再執行遷移。")
        return False

def analyze_data_sources():
    """分析數據源"""
    print("\n=== 數據源詳細分析 ===")

    # 分析回測結果文件
    backtest_files = list(Path('.').glob("*_backtest_results_*.json"))
    if backtest_files:
        print(f"\n找到 {len(backtest_files)} 個回測結果文件:")

        for file_path in backtest_files[:5]:  # 只分析前5個
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                print(f"\n[FILE] {file_path.name}:")

                # 基本信息
                if 'symbol' in data:
                    print(f"  股票代碼: {data['symbol']}")
                if 'timestamp' in data:
                    print(f"  生成時間: {data['timestamp']}")

                # 策略信息
                if 'summary' in data:
                    summary = data['summary']
                    print(f"  總策略數: {summary.get('total_strategies', 'N/A')}")
                    print(f"  成功測試: {summary.get('successful_tests', 'N/A')}")
                    print(f"  最佳夏普比率: {summary.get('best_sharpe', 'N/A')}")

                # 文件大小
                size_kb = file_path.stat().st_size / 1024
                print(f"  文件大小: {size_kb:.1f}KB")

            except Exception as e:
                print(f"  [ERROR] 讀取失敗: {e}")

        if len(backtest_files) > 5:
            print(f"\n... 還有 {len(backtest_files) - 5} 個回測文件")

    # 分析CSV文件
    csv_files = list(Path('.').glob("*.csv"))
    if csv_files:
        print(f"\n找到 {len(csv_files)} 個CSV文件:")
        for file_path in csv_files[:3]:
            size_kb = file_path.stat().st_size / 1024
            print(f"  [CSV] {file_path.name} ({size_kb:.1f}KB)")

        if len(csv_files) > 3:
            print(f"  ... 還有 {len(csv_files) - 3} 個CSV文件")

def show_migration_plan():
    """顯示遷移計劃"""
    print("\n=== 遷移執行計劃 ===")

    migrations = [
        {
            "step": 1,
            "name": "創建統一數據庫模式",
            "description": "建立6大核心模組的表結構和索引",
            "file": "migration_001_create_unified_schema.py"
        },
        {
            "step": 2,
            "name": "遷移策略數據",
            "description": "遷移回測結果、策略配置和性能數據",
            "file": "migration_002_migrate_strategy_data.py"
        },
        {
            "step": 3,
            "name": "遷移市場數據",
            "description": "遷移價格數據、技術指標和情緒數據",
            "file": "migration_003_migrate_market_data.py"
        },
        {
            "step": 4,
            "name": "遷移用戶和系統數據",
            "description": "創建默認用戶、遷移配置和審計日誌",
            "file": "migration_004_migrate_user_data.py"
        }
    ]

    for migration in migrations:
        print(f"\n步驟 {migration['step']}: {migration['name']}")
        print(f"  描述: {migration['description']}")
        print(f"  文件: {migration['file']}")

def show_next_steps():
    """顯示下一步操作"""
    print("\n=== 下一步操作 ===")
    print("1. 執行完整遷移:")
    print("   python run_data_migration.py")
    print("   然後選擇選項 1")
    print()
    print("2. 或者直接執行:")
    print("   python run_data_migration.py --full")
    print()
    print("3. 查看遷移狀態:")
    print("   python run_data_migration.py")
    print("   然後選擇選項 7")
    print()
    print("4. 驗證遷移結果:")
    print("   python run_data_migration.py")
    print("   然後選擇選項 6")

def main():
    """主測試函數"""
    try:
        # 測試系統準備情況
        is_ready = test_system_prerequisites()

        if is_ready:
            # 分析數據源
            analyze_data_sources()

            # 顯示遷移計劃
            show_migration_plan()

            # 顯示下一步操作
            show_next_steps()
        else:
            print("\n請先解決上述問題，然後重新運行測試。")
            return 1

        print(f"\n=== 測試完成 ===")
        print(f"測試時間: {datetime.now()}")
        return 0

    except Exception as e:
        print(f"\n[ERROR] 測試執行失敗: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
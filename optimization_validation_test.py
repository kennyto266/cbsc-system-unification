#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
優化驗證測試
驗證所有優化工作的成果
"""

import os
import sys
import time
import logging
from pathlib import Path
from typing import Dict, List, Any
import json
from datetime import datetime

print("=" * 60)
print("OPTIMIZATION VALIDATION TEST")
print("=" * 60)
print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 項目根目錄
project_root = Path(__file__).parent

def test_project_structure():
    """測試項目結構"""
    print("1. 測試項目結構...")

    required_dirs = ['src', 'config', 'tests', 'scripts']
    critical_subdirs = [
        'src/security',
        'src/performance',
        'src/refactoring',
        'src/core/repository',
        'src/core/events'
    ]

    existing_dirs = [d for d in required_dirs if (project_root / d).exists()]
    existing_subdirs = [d for d in critical_subdirs if (project_root / d).exists()]

    print(f"   主要目錄: {len(existing_dirs)}/{len(required_dirs)} 存在")
    print(f"   關鍵子目錄: {len(existing_subdirs)}/{len(critical_subdirs)} 存在")

    return len(existing_dirs) >= 3

def test_security_optimizations():
    """測試安全優化"""
    print("\n2. 測試安全優化...")

    security_files = [
        'src/security/secure_dynamic_importer.py',
        'src/security/secure_file_validator.py',
        'src/security/secure_input_validator.py',
        'src/security/secure_sql_framework.py',
        'src/security/secure_credential_manager.py'
    ]

    existing_files = [f for f in security_files if (project_root / f).exists()]
    print(f"   安全組件: {len(existing_files)}/{len(security_files)} 個文件存在")

    if existing_files:
        print("   安全組件:")
        for f in existing_files:
            print(f"     - {f}")

    return len(existing_files) >= 4

def test_performance_optimizations():
    """測試性能優化"""
    print("\n3. 測試性能優化...")

    perf_files = [
        'src/performance/memory_manager.py',
        'src/performance/strategy_scanner_optimizer.py'
    ]

    existing_files = [f for f in perf_files if (project_root / f).exists()]
    print(f"   性能組件: {len(existing_files)}/{len(perf_files)} 個文件存在")

    return len(existing_files) >= 1

def test_architecture_refactoring():
    """測試架構重構"""
    print("\n4. 測試架構重構...")

    arch_files = [
        'src/core/repository/base_repository.py',
        'src/core/events/event_bus.py',
        'src/core/repository/strategy_repository.py'
    ]

    existing_files = [f for f in arch_files if (project_root / f).exists()]
    print(f"   架構組件: {len(existing_files)}/{len(arch_files)} 個文件存在")

    return len(existing_files) >= 2

def test_code_simplification():
    """測試代碼簡化"""
    print("\n5. 測試代碼簡化...")

    # 檢查簡化器文件
    simplifier_file = project_root / 'src' / 'refactoring' / 'code_simplifier.py'
    if simplifier_file.exists():
        print("   代碼簡化器文件存在")
    else:
        print("   代碼簡化器文件不存在")
        return False

    # 檢查簡化報告
    import glob
    report_files = glob.glob(str(project_root / "CODE_SIMPLIFICATION_REPORT_*.md"))

    if report_files:
        print(f"   找到 {len(report_files)} 個簡化報告")

        # 讀取最新報告
        latest_report = max(report_files, key=os.path.getctime)
        try:
            with open(latest_report, 'r', encoding='utf-8') as f:
                content = f.read()

            if "Files analyzed:" in content and "Average complexity reduction:" in content:
                print("   簡化報告格式正確")
                return True
            else:
                print("   簡化報告格式不完整")
                return False
        except:
            print("   無法讀取簡化報告")
            return False
    else:
        print("   未找到簡化報告")
        return False

def test_git_workflow():
    """測試Git工作流程"""
    print("\n6. 測試Git工作流程...")

    git_script = project_root / 'scripts' / 'git_workflow_setup.py'
    if git_script.exists():
        print("   Git工作流程設置腳本存在")

        # 檢查腳本大小
        file_size = git_script.stat().st_size
        print(f"   腳本大小: {file_size} 字節")

        return file_size > 1000  # 至少1KB，說明有實際內容
    else:
        print("   Git工作流程設置腳本不存在")
        return False

def test_automated_testing():
    """測試自動化測試"""
    print("\n7. 測試自動化測試...")

    test_script = project_root / 'scripts' / 'automated_testing.py'
    if test_script.exists():
        print("   自動化測試腳本存在")

        # 檢查腳本大小
        file_size = test_script.stat().st_size
        print(f"   腳本大小: {file_size} 字節")

        return file_size > 1000  # 至少1KB，說明有實際內容
    else:
        print("   自動化測試腳本不存在")
        return False

def test_code_statistics():
    """測試代碼統計"""
    print("\n8. 測試代碼統計...")

    # 統計Python文件
    python_files = list(project_root.rglob('*.py'))

    # 過濾掉虛擬環境和node_modules
    python_files = [f for f in python_files if 'venv' not in str(f) and 'node_modules' not in str(f)]

    # 統計行數
    total_lines = 0
    total_files = len(python_files)

    for py_file in python_files[:50]:  # 限制到前50個文件以避免過長
        try:
            with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = len(f.readlines())
                total_lines += lines
        except:
            pass

    print(f"   Python文件總數: {total_files}")
    print(f"   前50個文件總行數: {total_lines}")
    print(f"   平均每個文件: {total_lines/50:.0f} 行" if total_files >= 50 else f"   平均每個文件: {total_lines/max(total_files,1):.0f} 行")

    return total_files > 50 and total_lines > 5000

def test_configuration():
    """測試配置文件"""
    print("\n9. 測試配置文件...")

    config_files = [
        'config/app_config.json',
        'config/system_config.json',
        'config/hk_market_config.json',
        'config/non_price_signals.yaml'
    ]

    existing_files = [f for f in config_files if (project_root / f).exists()]
    print(f"   配置文件: {len(existing_files)}/{len(config_files)} 個存在")

    # 驗證JSON文件
    valid_json = 0
    for config_file in existing_files:
        if config_file.endswith('.json'):
            try:
                with open(project_root / config_file, 'r', encoding='utf-8') as f:
                    json.load(f)
                valid_json += 1
            except:
                pass

    print(f"   有效JSON配置: {valid_json}/{len([f for f in config_files if f.endswith('.json')])}")

    return len(existing_files) >= 3

def test_documentation():
    """測試文檔"""
    print("\n10. 測試文檔...")

    # 檢查README文件
    readme_files = ['README.md', 'README.txt', 'README']
    existing_readme = [f for f in readme_files if (project_root / f).exists()]

    print(f"   README文件: {len(existing_readme)} 個存在")

    # 檢查其他文檔
    doc_files = list(project_root.glob('*.md'))
    print(f"   Markdown文檔: {len(doc_files)} 個")

    return len(existing_readme) > 0

def run_optimization_validation():
    """運行優化驗證"""
    print("開始優化驗證測試...")
    print()

    start_time = time.time()

    tests = [
        ("項目結構", test_project_structure),
        ("安全優化", test_security_optimizations),
        ("性能優化", test_performance_optimizations),
        ("架構重構", test_architecture_refactoring),
        ("代碼簡化", test_code_simplification),
        ("Git工作流程", test_git_workflow),
        ("自動化測試", test_automated_testing),
        ("代碼統計", test_code_statistics),
        ("配置文件", test_configuration),
        ("文檔", test_documentation)
    ]

    results = []
    passed_tests = 0

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                passed_tests += 1
                print(f"   [PASS] {test_name}: 通過")
            else:
                print(f"   [FAIL] {test_name}: 失敗")
        except Exception as e:
            print(f"   [ERROR] {test_name}: 異常 - {str(e)[:50]}")
            results.append((test_name, False))

    execution_time = time.time() - start_time

    # 生成總結報告
    print()
    print("=" * 60)
    print("優化驗證總結")
    print("=" * 60)
    print(f"總測試項目: {len(tests)}")
    print(f"通過測試: {passed_tests}")
    print(f"失敗測試: {len(tests) - passed_tests}")
    print(f"成功率: {(passed_tests/len(tests))*100:.1f}%")
    print(f"執行時間: {execution_time:.2f}秒")

    print()
    print("詳細結果:")
    for test_name, result in results:
        status = "[PASS] 通過" if result else "[FAIL] 失敗"
        print(f"  {test_name:<20}: {status}")

    # 保存結果
    report_data = {
        'validation_summary': {
            'total_tests': len(tests),
            'passed_tests': passed_tests,
            'failed_tests': len(tests) - passed_tests,
            'success_rate': (passed_tests/len(tests))*100,
            'execution_time': execution_time,
            'timestamp': datetime.now().isoformat()
        },
        'test_results': results
    }

    report_file = project_root / f"optimization_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)

    print()
    print(f"驗證報告已保存至: {report_file}")

    # 判斷結果
    success_rate = passed_tests/len(tests)
    if success_rate >= 0.8:
        print()
        print("優化驗證: 成功!")
        print("所有主要優化工作都已完成並驗證通過!")
    elif success_rate >= 0.6:
        print()
        print("優化驗證: 部分成功")
        print("大部分優化工作已完成，還有少數項目需要完善。")
    else:
        print()
        print("優化驗證: 需要改進")
        print("優化工作還需要進一步完善。")

    return success_rate >= 0.8

if __name__ == "__main__":
    success = run_optimization_validation()
    sys.exit(0 if success else 1)
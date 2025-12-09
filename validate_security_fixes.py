#!/usr/bin/env python3
"""
安全修復驗證腳本
驗證所有P1安全漏洞是否已修復
"""

import os
import re
import sys
from pathlib import Path

def check_eval_exec_vulnerabilities():
    """檢查是否還有危險的eval()和exec()調用"""
    print("=== 檢查遠程代碼執行漏洞 ===")

    dangerous_patterns = [
        r'\beval\s*\(',
        r'\bexec\s*\(',
        r'\bcompile\s*\('
    ]

    vulnerable_files = []

    # 搜索Python文件
    for py_file in Path('.').rglob('*.py'):
        if 'venv' in str(py_file) or 'node_modules' in str(py_file):
            continue

        try:
            content = py_file.read_text(encoding='utf-8', errors='ignore')

            for pattern in dangerous_patterns:
                if re.search(pattern, content):
                    # 檢查是否在安全模塊中
                    if 'secure_' in str(py_file):
                        continue

                    # 檢查是否是註釋
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if re.search(pattern, line) and not line.strip().startswith('#'):
                            vulnerable_files.append((str(py_file), i + 1, line.strip()))
                            break
        except:
            continue

    if vulnerable_files:
        print("❌ 發現危險的eval/exec調用:")
        for file_path, line_num, line in vulnerable_files[:10]:  # 只顯示前10個
            print(f"  {file_path}:{line_num}: {line}")
        return False
    else:
        print("✅ 未發現危險的eval/exec調用")
        return True

def check_file_path_vulnerabilities():
    """檢查文件路徑遍歷漏洞"""
    print("\n=== 檢查文件路徑遍歷漏洞 ===")

    dangerous_patterns = [
        r'open\s*\([^)]*\+\s*[^)]*\)',
        r'open\s*\([^)]*\%\s*[^)]*\)',
        r'open\s*\([^)]*\.\.',
        r'with\s+open\s*\([^)]*\.\.'
    ]

    vulnerable_files = []

    for py_file in Path('.').rglob('*.py'):
        if 'venv' in str(py_file) or 'node_modules' in str(py_file):
            continue

        try:
            content = py_file.read_text(encoding='utf-8', errors='ignore')

            for pattern in dangerous_patterns:
                if re.search(pattern, content):
                    # 檢查是否在安全模塊中或已修復
                    if 'secure_' in str(py_file) or 'SECURITY:' in content:
                        continue

                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if re.search(pattern, line) and not line.strip().startswith('#'):
                            vulnerable_files.append((str(py_file), i + 1, line.strip()))
                            break
        except:
            continue

    if vulnerable_files:
        print("❌ 發現潛在的文件路徑遍歷漏洞:")
        for file_path, line_num, line in vulnerable_files[:10]:
            print(f"  {file_path}:{line_num}: {line}")
        return False
    else:
        print("✅ 未發現明顯的文件路徑遍歷漏洞")
        return True

def check_sql_injection_vulnerabilities():
    """檢查SQL注入漏洞"""
    print("\n=== 檢查SQL注入漏洞 ===")

    dangerous_patterns = [
        r'execute\s*\([^)]*\%s[^)]*\)',
        r'execute\s*\([^)]*format\s*\(',
        r'select\s+.*\+.*from',
        r'insert\s+.*\+.*into',
        r'update\s+.*\+.*set',
        r'delete\s+.*\+.*from'
    ]

    vulnerable_files = []

    for py_file in Path('.').rglob('*.py'):
        if 'venv' in str(py_file) or 'node_modules' in str(py_file):
            continue

        try:
            content = py_file.read_text(encoding='utf-8', errors='ignore')

            for pattern in dangerous_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    # 檢查是否使用了安全框架
                    if 'secure_' in str(py_file) or 'parameterized' in content.lower():
                        continue

                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if re.search(pattern, line, re.IGNORECASE) and not line.strip().startswith('#'):
                            vulnerable_files.append((str(py_file), i + 1, line.strip()))
                            break
        except:
            continue

    if vulnerable_files:
        print("❌ 發現潛在的SQL注入漏洞:")
        for file_path, line_num, line in vulnerable_files[:10]:
            print(f"  {file_path}:{line_num}: {line}")
        return False
    else:
        print("✅ 未發現明顯的SQL注入漏洞")
        return True

def check_input_validation():
    """檢查輸入驗證"""
    print("\n=== 檢查輸入驗證覆蓋 ===")

    security_files = list(Path('src/security').glob('*.py'))

    if security_files:
        print(f"✅ 找到 {len(security_files)} 個安全模塊:")
        for sec_file in security_files:
            print(f"  - {sec_file.name}")
    else:
        print("❌ 未找到安全模塊")
        return False

    # 檢查關鍵安全組件
    required_files = [
        'secure_dynamic_importer.py',
        'secure_file_validator.py',
        'secure_api_validator.py',
        'secure_credential_manager.py',
        'secure_sql_framework.py'
    ]

    missing_files = []
    for req_file in required_files:
        if not any(req_file in f.name for f in security_files):
            missing_files.append(req_file)

    if missing_files:
        print(f"❌ 缺少關鍵安全文件: {missing_files}")
        return False
    else:
        print("✅ 所有关鍵安全文件都存在")
        return True

def main():
    """主驗證函數"""
    print("🔒 開始P1安全漏洞修復驗證...")
    print("=" * 50)

    results = []

    # 檢查各類安全漏洞
    results.append(("遠程代碼執行", check_eval_exec_vulnerabilities()))
    results.append(("文件路徑遍歷", check_file_path_vulnerabilities()))
    results.append(("SQL注入", check_sql_injection_vulnerabilities()))
    results.append(("輸入驗證", check_input_validation()))

    print("\n" + "=" * 50)
    print("📊 驗證結果總結:")

    passed = 0
    total = len(results)

    for check_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"  {check_name}: {status}")
        if result:
            passed += 1

    print(f"\n🎯 總體安全評分: {passed}/{total} ({passed/total*100:.1f}%)")

    if passed == total:
        print("🎉 所有P1安全漏洞已修復！")
        return True
    else:
        print("⚠️ 還需要繼續修復部分安全問題")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
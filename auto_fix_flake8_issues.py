#!/usr/bin/env python3
"""
Auto-fix flake8 issues script
自動修復Flake8代碼風格問題
"""

import os
import re
import subprocess
from pathlib import Path

def fix_unused_imports(file_path):
    """修復未使用的導入"""
    try:
        result = subprocess.run(
            ['autoflake', '--in-place', '--remove-unused-variables', str(file_path)],
            capture_output=True, text=True
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error fixing unused imports in {file_path}: {e}")
        return False

def fix_missing_whitespace(file_path):
    """修復空格缺失問題"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # 修復算術運算符周圍的空格
        content = re.sub(r'(\w)([+\-*/=])(\w)', r'\1 \2 \3', content)
        content = re.sub(r'(\w)([+\-*/=])([+\-*/])', r'\1 \2 \3', content)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return True
    except Exception as e:
        print(f"Error fixing whitespace in {file_path}: {e}")
        return False

def fix_bare_except(file_path):
    """修復裸露的except語句"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # 替換裸露的except為except Exception
        content = re.sub(r'except:\s*\n', 'except Exception:\n', content)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return True
    except Exception as e:
        print(f"Error fixing bare except in {file_path}: {e}")
        return False

def fix_module_imports(file_path):
    """修復模塊級導入順序問題"""
    try:
        # 使用isort修復導入順序
        result = subprocess.run(
            ['isort', str(file_path)],
            capture_output=True, text=True
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error fixing module imports in {file_path}: {e}")
        return False

def process_directory(directory):
    """處理整個目錄中的Python文件"""
    directory = Path(directory)
    fixed_count = 0
    total_count = 0

    for py_file in directory.rglob("*.py"):
        if any(skip in str(py_file) for skip in ['backup_before_formatting', 'archive', '__pycache__']):
            continue

        total_count += 0
        file_fixed = False

        print(f"Processing: {py_file}")

        # 應用各種修復
        if fix_unused_imports(py_file):
            file_fixed = True

        if fix_missing_whitespace(py_file):
            file_fixed = True

        if fix_bare_except(py_file):
            file_fixed = True

        if fix_module_imports(py_file):
            file_fixed = True

        if file_fixed:
            fixed_count += 1

    print(f"\nSummary:")
    print(f"Total files processed: {total_count}")
    print(f"Files fixed: {fixed_count}")

def main():
    """主函數"""
    print("開始自動修復Flake8代碼風格問題...")
    print("=" * 50)

    # 處理主要目錄
    directories = [
        "simplified_system",
        "src",
        "config",
        "scripts",
        "tests"
    ]

    for directory in directories:
        if os.path.exists(directory):
            print(f"\n處理目錄: {directory}")
            process_directory(directory)

    print("\n" + "=" * 50)
    print("代碼風格修復完成！")

if __name__ == "__main__":
    main()
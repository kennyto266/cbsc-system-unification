#!/usr / bin / env python3
"""
API測試運行腳本

用法:
    python scripts / run_api_tests.py
    python scripts / run_api_tests.py --verbose
    python scripts / run_api_tests.py --coverage
"""

import subprocess
import sys
import argparse


def run_tests(args):
    """運行API測試"""
    cmd = ["pytest", "tests / api/"]

    if args.verbose:
        cmd.append("-v")

    if args.coverage:
        cmd.extend([
            "--cov=src / dashboard",
            "--cov - report=term - missing",
            "--cov - report=html:htmlcov"
        ])

    if args.test_file:
        cmd.append(args.test_file)

    print("=" * 60)
    print("運行API測試")
    print("=" * 60)
    print(f"命令: {' '.join(cmd)}")
    print()

    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("\n✅ 所有測試通過!")
    else:
        print("\n❌ 部分測試失敗!")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="運行API測試")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="詳細輸出")
    parser.add_argument("--coverage", "-c", action="store_true",
                        help="生成覆蓋率報告")
    parser.add_argument("--test - file", "-f", type=str,
                        help="運行特定測試文件")

    args = parser.parse_args()
    run_tests(args)


if __name__ == "__main__":
    main()

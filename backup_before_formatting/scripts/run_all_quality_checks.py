#!/usr / bin / env python3
"""
运行所有代码质量检查
===================

一键运行所有质量检查工具，生成综合报告。

用法:
    python scripts / run_all_quality_checks.py [--target TARGET] [--output - dir DIR]
"""

import argparse
import sys
from pathlib import Path
from code_quality_checker import CodeQualityChecker
from security_scanner import SecurityScanner
from complexity_analyzer import ComplexityAnalyzer
from tech_debt_tracker import TechnicalDebtTracker


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="运行所有代码质量检查")
    parser.add_argument(
        "--target",
        default="src",
        help="检查目标目录 (default: src)"
    )
    parser.add_argument(
        "--output - dir",
        default="reports",
        help="输出目录 (default: reports)"
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="并行运行检查 (default: True)"
    )
    parser.add_argument(
        "--sequential",
        dest="parallel",
        action="store_false",
        help="顺序运行检查"
    )
    parser.set_defaults(parallel=True)

    args = parser.parse_args()

    # 检查目标目录
    if not Path(args.target).exists():
        print("错误: 目录 "{args.target}' 不存在")
        sys.exit(1)

    print("=" * 70)
    print("代码质量全面检查")
    print("=" * 70)
    print(f"目标目录: {args.target}")
    print(f"输出目录: {args.output_dir}")
    print()

    # 创建报告目录
    Path(args.output_dir).mkdir(exist_ok=True)

    # 1. 代码质量综合检查
    print("1. 运行代码质量综合检查...")
    quality_checker = CodeQualityChecker(target=args.target, output_dir=args.output_dir)
    quality_checker.run_all_checks(parallel=args.parallel)

    # 2. 安全扫描
    print("\n2. 运行安全扫描...")
    security_scanner = SecurityScanner(target=args.target, output_dir=args.output_dir)
    security_scanner.run_bandit()
    security_scanner.run_safety()
    security_scanner.scan_secrets()
    security_scanner.generate_report(output_format="json")

    # 3. 复杂度分析
    print("\n3. 运行复杂度分析...")
    complexity_analyzer = ComplexityAnalyzer(target=args.target, output_dir=args.output_dir)
    complexity_analyzer.analyze_cyclomatic_complexity()
    complexity_analyzer.analyze_maintainability()
    complexity_analyzer.generate_report(output_format="json")

    # 4. 技术债务跟踪
    print("\n4. 运行技术债务跟踪...")
    debt_tracker = TechnicalDebtTracker(target=args.target)
    debt_tracker.scan_directory()
    debt_tracker.generate_report(output_format="json")

    # 5. 生成质量仪表板
    print("\n5. 启动质量仪表板...")
    print("请访问 http://localhost:8888 查看实时质量监控")
    print("提示: 运行 'python scripts / quality_dashboard.py --port 8888' 启动仪表板")

    print("\n" + "=" * 70)
    print("所有检查完成!")
    print("=" * 70)
    print("\n查看报告:")
    print(f"  - 综合质量报告: {args.output_dir}/quality_summary_*.json")
    print(f"  - 安全扫描报告: {args.output_dir}/security_report_*.json")
    print(f"  - 复杂度报告: {args.output_dir}/complexity_report_*.json")
    print(f"  - 技术债务报告: {args.output_dir}/tech_debt_*.json")
    print("\n启动仪表板:")
    print("  python scripts / quality_dashboard.py --port 8888")
    print("  然后访问: http://localhost:8888")


if __name__ == "__main__":
    main()

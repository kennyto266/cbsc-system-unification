#!/usr/bin/env python3
"""
Performance Analysis Script
分析性能測試結果並檢測回歸
"""

import json
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import numpy as np


class PerformanceAnalyzer:
    """性能分析器"""

    def __init__(self, threshold: float = 10.0):
        """
        初始化性能分析器

        Args:
            threshold: 性能回歸閾值（百分比）
        """
        self.threshold = threshold
        self.results: Dict[str, Any] = {}

    def load_current_results(self, file_path: str) -> Dict[str, Any]:
        """加載當前測試結果"""
        with open(file_path, 'r') as f:
            return json.load(f)

    def load_baseline_results(self, file_path: str = "baseline.json") -> Dict[str, Any]:
        """加載基準測試結果"""
        baseline_path = Path(file_path)
        if baseline_path.exists():
            with open(baseline_path, 'r') as f:
                return json.load(f)
        return {}

    def analyze_performance(self, current: Dict[str, Any], baseline: Dict[str, Any]) -> Dict[str, Any]:
        """分析性能差異"""
        analysis = {
            "regressions": [],
            "improvements": [],
            "no_changes": [],
            "summary": {
                "total_tests": 0,
                "regressions_count": 0,
                "improvements_count": 0,
                "regression_threshold": self.threshold
            }
        }

        if not baseline:
            analysis["summary"]["status"] = "no_baseline"
            return analysis

        # 分析benchmarks
        benchmarks = current.get("benchmarks", {})
        baseline_benchmarks = baseline.get("benchmarks", {})

        for name, result in benchmarks.items():
            if name not in baseline_benchmarks:
                continue

            baseline_result = baseline_benchmarks[name]
            current_mean = result.get("stats", {}).get("mean", 0)
            baseline_mean = baseline_result.get("stats", {}).get("mean", 0)

            if baseline_mean == 0:
                continue

            # 計算百分比變化
            percent_change = ((current_mean - baseline_mean) / baseline_mean) * 100

            test_result = {
                "name": name,
                "current": current_mean,
                "baseline": baseline_mean,
                "percent_change": percent_change,
                "status": "unknown"
            }

            analysis["summary"]["total_tests"] += 1

            if percent_change > self.threshold:
                test_result["status"] = "regression"
                analysis["regressions"].append(test_result)
                analysis["summary"]["regressions_count"] += 1
            elif percent_change < -self.threshold:
                test_result["status"] = "improvement"
                analysis["improvements"].append(test_result)
                analysis["summary"]["improvements_count"] += 1
            else:
                test_result["status"] = "no_change"
                analysis["no_changes"].append(test_result)

        # 確定整體狀態
        if analysis["summary"]["regressions_count"] > 0:
            analysis["summary"]["status"] = "failed"
        elif analysis["summary"]["improvements_count"] > 0:
            analysis["summary"]["status"] = "improved"
        else:
            analysis["summary"]["status"] = "stable"

        return analysis

    def save_baseline(self, results: Dict[str, Any], file_path: str = "baseline.json"):
        """保存基準測試結果"""
        with open(file_path, 'w') as f:
            json.dump(results, f, indent=2)

    def generate_report(self, analysis: Dict[str, Any], output_file: str = "performance_report.txt"):
        """生成性能分析報告"""
        with open(output_file, 'w') as f:
            f.write("Performance Analysis Report\n")
            f.write("=" * 50 + "\n\n")

            summary = analysis["summary"]
            f.write(f"Summary:\n")
            f.write(f"  Total tests: {summary['total_tests']}\n")
            f.write(f"  Regressions: {summary['regressions_count']}\n")
            f.write(f"  Improvements: {summary['improvements_count']}\n")
            f.write(f"  Regression threshold: {summary['regression_threshold']}%\n")
            f.write(f"  Status: {summary['status']}\n\n")

            if analysis["regressions"]:
                f.write("Performance Regressions:\n")
                f.write("-" * 25 + "\n")
                for regression in analysis["regressions"]:
                    f.write(f"  {regression['name']}\n")
                    f.write(f"    Current: {regression['current']:.4f}s\n")
                    f.write(f"    Baseline: {regression['baseline']:.4f}s\n")
                    f.write(f"    Change: {regression['percent_change']:+.2f}%\n\n")

            if analysis["improvements"]:
                f.write("Performance Improvements:\n")
                f.write("-" * 25 + "\n")
                for improvement in analysis["improvements"]:
                    f.write(f"  {improvement['name']}\n")
                    f.write(f"    Current: {improvement['current']:.4f}s\n")
                    f.write(f"    Baseline: {improvement['baseline']:.4f}s\n")
                    f.write(f"    Change: {improvement['percent_change']:+.2f}%\n\n")

            if analysis["no_changes"]:
                f.write("No Significant Changes:\n")
                f.write("-" * 25 + "\n")
                for no_change in analysis["no_changes"]:
                    f.write(f"  {no_change['name']}: {no_change['percent_change']:+.2f}%\n")

    def generate_charts(self, analysis: Dict[str, Any], output_dir: str = "charts"):
        """生成性能圖表"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # 回歸分析圖表
        if analysis["regressions"] or analysis["improvements"]:
            names = []
            changes = []
            colors = []

            for regression in analysis["regressions"]:
                names.append(regression["name"])
                changes.append(regression["percent_change"])
                colors.append("red")

            for improvement in analysis["improvements"]:
                names.append(improvement["name"])
                changes.append(improvement["percent_change"])
                colors.append("green")

            if names:
                plt.figure(figsize=(12, 6))
                bars = plt.bar(range(len(names)), changes, color=colors)
                plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
                plt.axhline(y=analysis["summary"]["regression_threshold"], color='red', linestyle='--', alpha=0.5, label='Regression Threshold')
                plt.axhline(y=-analysis["summary"]["regression_threshold"], color='green', linestyle='--', alpha=0.5, label='Improvement Threshold')

                plt.xlabel('Test Cases')
                plt.ylabel('Performance Change (%)')
                plt.title('Performance Changes Analysis')
                plt.xticks(range(len(names)), names, rotation=45, ha='right')
                plt.legend()
                plt.tight_layout()
                plt.savefig(output_path / "performance_changes.png", dpi=300, bbox_inches='tight')
                plt.close()

        # 總體統計圖表
        if analysis["summary"]["total_tests"] > 0:
            labels = ['Regressions', 'Improvements', 'No Change']
            sizes = [
                analysis["summary"]["regressions_count"],
                analysis["summary"]["improvements_count"],
                analysis["summary"]["total_tests"] - analysis["summary"]["regressions_count"] - analysis["summary"]["improvements_count"]
            ]
            colors = ['red', 'green', 'blue']

            plt.figure(figsize=(8, 6))
            plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            plt.title('Performance Test Results Distribution')
            plt.axis('equal')
            plt.savefig(output_path / "performance_distribution.png", dpi=300, bbox_inches='tight')
            plt.close()

    def check_ci_status(self, analysis: Dict[str, Any]) -> int:
        """檢查CI狀態並返回退出碼"""
        if analysis["summary"]["status"] == "failed":
            return 1
        return 0


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="Analyze performance test results")
    parser.add_argument("--current", required=True, help="Current test results JSON file")
    parser.add_argument("--baseline", default="baseline.json", help="Baseline test results JSON file")
    parser.add_argument("--threshold", type=float, default=10.0, help="Regression threshold in percentage")
    parser.add_argument("--output-dir", default=".", help="Output directory for reports and charts")
    parser.add_argument("--save-baseline", action="store_true", help="Save current results as new baseline")
    parser.add_argument("--charts", action="store_true", help="Generate performance charts")

    args = parser.parse_args()

    # 初始化分析器
    analyzer = PerformanceAnalyzer(threshold=args.threshold)

    # 加載測試結果
    print("Loading current test results...")
    current_results = analyzer.load_current_results(args.current)

    print("Loading baseline results...")
    baseline_results = analyzer.load_baseline_results(args.baseline)

    # 分析性能
    print("Analyzing performance changes...")
    analysis = analyzer.analyze_performance(current_results, baseline_results)

    # 生成報告
    print("Generating performance report...")
    report_file = Path(args.output_dir) / "performance_report.txt"
    analyzer.generate_report(analysis, str(report_file))
    print(f"Performance report saved to: {report_file}")

    # 生成圖表
    if args.charts:
        print("Generating performance charts...")
        analyzer.generate_charts(analysis, Path(args.output_dir) / "charts")
        print(f"Charts saved to: {Path(args.output_dir) / 'charts'}")

    # 保存基準
    if args.save_baseline:
        print("Saving current results as baseline...")
        baseline_file = Path(args.output_dir) / "baseline.json"
        analyzer.save_baseline(current_results, str(baseline_file))
        print(f"Baseline saved to: {baseline_file}")

    # 輸出摘要
    summary = analysis["summary"]
    print(f"\nPerformance Analysis Summary:")
    print(f"  Status: {summary['status']}")
    print(f"  Total tests: {summary['total_tests']}")
    print(f"  Regressions: {summary['regressions_count']}")
    print(f"  Improvements: {summary['improvements_count']}")

    if analysis["regressions"]:
        print(f"\nRegressions detected:")
        for regression in analysis["regressions"][:5]:  # 只顯示前5個
            print(f"  - {regression['name']}: {regression['percent_change']:+.2f}%")

    # 返回CI狀態
    exit_code = analyzer.check_ci_status(analysis)
    print(f"\nCI Status: {'PASS' if exit_code == 0 else 'FAIL'}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
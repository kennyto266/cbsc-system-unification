#!/usr / bin / env python3
"""
代码复杂度分析器 (Code Complexity Analyzer)
==========================================

使用Radon和自定义指标分析代码复杂度。

用法:
    python scripts / complexity_analyzer.py [--target TARGET] [--output FORMAT]
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import subprocess
from dataclasses import dataclass, asdict


@dataclass
class ComplexityMetric:
    """复杂度指标"""
    file: str
    function: str
    line: int
    complexity: int
    rank: str
    type: str  # cyclomatic or maintainability
    raw_score: float = 0.0


class ComplexityAnalyzer:
    """代码复杂度分析器"""

    COMPLEXITY_THRESHOLDS = {
        "A": 5,   # 简单
        "B": 10,  # 适中
        "C": 20,  # 复杂
        "D": 30,  # 非常复杂
        "F": 100  # 无法理解
    }

    MAINTAINABILITY_THRESHOLDS = {
        "A": 80,  # 非常可维护
        "B": 70,  # 可维护
        "C": 50,  # 难以维护
        "D": 30,  # 难以维护
        "F": 0    # 几乎不可维护
    }

    def __init__(self, target: str = "src", output_dir: str = "reports"):
        self.target = target
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y % m % d_ % H % M % S")
        self.complexity_metrics: List[ComplexityMetric] = []

    def analyze_cyclomatic_complexity(self) -> None:
        """分析圈复杂度"""
        output_file = self.output_dir / f"radon_cc_{self.timestamp}.json"
        cmd = ["radon", "cc", self.target, "-j", "-o", str(output_file), "--min=A"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            if output_file.exists():
                with open(output_file) as f:
                    data = json.load(f)
                    for item in data:
                        self.complexity_metrics.append(ComplexityMetric(
                            file=item.get("path", ""),
                            function=item.get("name", ""),
                            line=item.get("lineno", 0),
                            complexity=item.get("complexity", 0),
                            rank=item.get("rank", "A"),
                            type="cyclomatic_complexity"
                        ))
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Radon CC分析失败: {e}")

    def analyze_maintainability(self) -> None:
        """分析可维护性指数"""
        output_file = self.output_dir / f"radon_mi_{self.timestamp}.json"
        cmd = ["radon", "mi", self.target, "-j", "-o", str(output_file), "--min=A"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            if output_file.exists():
                with open(output_file) as f:
                    data = json.load(f)
                    for item in data:
                        self.complexity_metrics.append(ComplexityMetric(
                            file=item.get("path", ""),
                            function=item.get("name", ""),
                            line=item.get("lineno", 0),
                            complexity=0,
                            rank=item.get("rank", "A"),
                            type="maintainability_index",
                            raw_score=item.get("mi", 0.0)
                        ))
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Radon MI分析失败: {e}")

    def analyze_raw_metrics(self) -> None:
        """分析原始指标"""
        output_file = self.output_dir / f"radon_raw_{self.timestamp}.json"
        cmd = ["radon", "raw", self.target, "-j", "-o", str(output_file)]

        raw_data = {}
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            if output_file.exists():
                with open(output_file) as f:
                    raw_data = json.load(f)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Radon RAW分析失败: {e}")

        return raw_data

    def get_complexity_distribution(self) -> Dict[str, int]:
        """获取复杂度分布"""
        distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        for metric in self.complexity_metrics:
            if metric.type == "cyclomatic_complexity":
                distribution[metric.rank] = distribution.get(metric.rank, 0) + 1
        return distribution

    def get_maintainability_distribution(self) -> Dict[str, int]:
        """获取可维护性分布"""
        distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        for metric in self.complexity_metrics:
            if metric.type == "maintainability_index":
                distribution[metric.rank] = distribution.get(metric.rank, 0) + 1
        return distribution

    def get_top_complex_functions(self, limit: int = 10) -> List[ComplexityMetric]:
        """获取最复杂的函数"""
        return sorted(
            [m for m in self.complexity_metrics if m.type == "cyclomatic_complexity"],
            key=lambda x: x.complexity,
            reverse=True
        )[:limit]

    def get_least_maintainable_functions(self, limit: int = 10) -> List[ComplexityMetric]:
        """获取可维护性最低的函数"""
        return sorted(
            [m for m in self.complexity_metrics if m.type == "maintainability_index"],
            key=lambda x: x.raw_score
        )[:limit]

    def calculate_overall_score(self) -> float:
        """计算整体复杂度评分"""
        cc_metrics = [m for m in self.complexity_metrics if m.type == "cyclomatic_complexity"]
        mi_metrics = [m for m in self.complexity_metrics if m.type == "maintainability_index"]

        if not cc_metrics and not mi_metrics:
            return 100.0

        score = 100.0

        # 圈复杂度扣分
        for metric in cc_metrics:
            if metric.rank == "A":
                score -= 0
            elif metric.rank == "B":
                score -= 2
            elif metric.rank == "C":
                score -= 5
            elif metric.rank == "D":
                score -= 10
            else:  # F
                score -= 20

        # 可维护性扣分
        for metric in mi_metrics:
            if metric.rank == "A":
                score -= 0
            elif metric.rank == "B":
                score -= 3
            elif metric.rank == "C":
                score -= 7
            elif metric.rank == "D":
                score -= 12
            else:  # F
                score -= 20

        return max(0, score)

    def generate_report(self, output_format: str = "console") -> None:
        """生成报告"""
        if output_format == "console":
            self._print_console_report()
        elif output_format == "json":
            self._save_json_report()
        elif output_format == "html":
            self._save_html_report()

    def _print_console_report(self) -> None:
        """打印控制台报告"""
        print("=" * 70)
        print("代码复杂度分析报告")
        print("=" * 70)
        print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"目标目录: {self.target}")
        print(f"分析项目数: {len(self.complexity_metrics)}")
        print()

        # 整体评分
        overall_score = self.calculate_overall_score()
        print(f"整体复杂度评分: {overall_score:.2f}/100")

        if overall_score >= 90:
            print("评级: A (优秀)")
        elif overall_score >= 80:
            print("评级: B (良好)")
        elif overall_score >= 70:
            print("评级: C (中等)")
        elif overall_score >= 60:
            print("评级: D (较差)")
        else:
            print("评级: F (不合格)")
        print()

        # 圈复杂度分布
        cc_dist = self.get_complexity_distribution()
        print("圈复杂度分布:")
        for rank, count in sorted(cc_dist.items()):
            print(f"  {rank}: {count} 个函数")
        print()

        # 可维护性分布
        mi_dist = self.get_maintainability_distribution()
        print("可维护性分布:")
        for rank, count in sorted(mi_dist.items()):
            print(f"  {rank}: {count} 个函数")
        print()

        # Top 10 最复杂函数
        top_complex = self.get_top_complex_functions(10)
        if top_complex:
            print("最复杂的函数 (Top 10):")
            print("-" * 70)
            for metric in top_complex:
                print(f"  {metric.file}:{metric.function} (L{metric.line})")
                print(f"    复杂度: {metric.complexity} ({metric.rank})")
            print()

        # Top 10 可维护性最低的函数
        least_maintainable = self.get_least_maintainable_functions(10)
        if least_maintainable:
            print("可维护性最低的函数 (Top 10):")
            print("-" * 70)
            for metric in least_maintainable:
                print(f"  {metric.file}:{metric.function} (L{metric.line})")
                print(f"    可维护性指数: {metric.raw_score:.2f} ({metric.rank})")
            print()

        # 建议
        print("改进建议:")
        print("-" * 70)
        if cc_dist["D"] + cc_dist["F"] > 0:
            print(f"⚠️  发现 {cc_dist['D'] + cc_dist['F']} 个高度复杂的函数，建议重构")
        if mi_dist["D"] + mi_dist["F"] > 0:
            print(f"⚠️  发现 {mi_dist['D'] + mi_dist['F']} 个可维护性差的函数，建议优化")
        if overall_score < 70:
            print("⚠️  整体复杂度较高，建议进行全面重构")
        print("💡 将大函数拆分为小函数")
        print("💡 减少嵌套层级")
        print("💡 提取重复代码为独立函数")
        print("💡 使用更简单的算法")

    def _save_json_report(self) -> None:
        """保存JSON报告"""
        output_file = self.output_dir / f"complexity_report_{self.timestamp}.json"

        report = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "target_directory": self.target,
                "total_items": len(self.complexity_metrics)
            },
            "summary": {
                "overall_score": self.calculate_overall_score(),
                "cyclomatic_complexity": self.get_complexity_distribution(),
                "maintainability_index": self.get_maintainability_distribution(),
                "top_complex_functions": [asdict(m) for m in self.get_top_complex_functions(10)],
                "least_maintainable_functions": [asdict(m) for m in self.get_least_maintainable_functions(10)]
            },
            "metrics": [asdict(m) for m in self.complexity_metrics]
        }

        with open(output_file, "w", encoding="utf - 8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"JSON报告已保存到: {output_file}")

    def _save_html_report(self) -> None:
        """保存HTML报告"""
        output_file = self.output_dir / f"complexity_report_{self.timestamp}.html"

        cc_dist = self.get_complexity_distribution()
        mi_dist = self.get_maintainability_distribution()
        top_complex = self.get_top_complex_functions(10)
        least_maintainable = self.get_least_maintainable_functions(10)
        overall_score = self.calculate_overall_score()

        html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF - 8">
    <title>代码复杂度分析报告</title>
    <style>
        body {{ font - family: Arial, sans - serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max - width: 1200px; margin: 0 auto; background: white; padding: 20px; border - radius: 8px; box - shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1, h2 {{ color: #333; }}
        .score {{ font - size: 48px; font - weight: bold; text - align: center; padding: 30px; background: linear - gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border - radius: 8px; margin: 20px 0; }}
        .score.A {{ background: linear - gradient(135deg, #11998e 0%, #38ef7d 100%); }}
        .score.B {{ background: linear - gradient(135deg, #f093fb 0%, #f5576c 100%); }}
        .score.C {{ background: linear - gradient(135deg, #fa709a 0%, #fee140 100%); }}
        .score.D {{ background: linear - gradient(135deg, #ff9a56 0%, #ff6a88 100%); }}
        .score.F {{ background: linear - gradient(135deg, #f54ea2 0%, #ff7676 100%); }}
        .section {{ margin: 30px 0; }}
        .chart {{ display: flex; gap: 20px; margin: 20px 0; }}
        .bar {{ flex: 1; background: #f8f9fa; padding: 15px; border - radius: 5px; }}
        .bar - label {{ font - weight: bold; margin - bottom: 10px; }}
        .bar - value {{ font - size: 24px; color: #007bff; }}
        table {{ width: 100%; border - collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text - align: left; border - bottom: 1px solid #ddd; }}
        th {{ background - color: #f8f9fa; font - weight: bold; }}
        tr:hover {{ background - color: #f5f5f5; }}
        .complexity - A {{ color: #28a745; font - weight: bold; }}
        .complexity - B {{ color: #17a2b8; font - weight: bold; }}
        .complexity - C {{ color: #ffc107; font - weight: bold; }}
        .complexity - D {{ color: #fd7e14; font - weight: bold; }}
        .complexity - F {{ color: #dc3545; font - weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>代码复杂度分析报告</h1>
        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>目标目录: {self.target}</p>

        <div class="score {'A' if overall_score >= 90 else 'B' if overall_score >= 80 else 'C' if overall_score >= 70 else 'D' if overall_score >= 60 else 'F'}">
            {overall_score:.2f}/100
        </div>

        <div class="section">
            <h2>圈复杂度分布</h2>
            <div class="chart">
                <div class="bar">
                    <div class="bar - label">A (简单)</div>
                    <div class="bar - value">{cc_dist['A']}</div>
                </div>
                <div class="bar">
                    <div class="bar - label">B (适中)</div>
                    <div class="bar - value">{cc_dist['B']}</div>
                </div>
                <div class="bar">
                    <div class="bar - label">C (复杂)</div>
                    <div class="bar - value">{cc_dist['C']}</div>
                </div>
                <div class="bar">
                    <div class="bar - label">D (非常复杂)</div>
                    <div class="bar - value">{cc_dist['D']}</div>
                </div>
                <div class="bar">
                    <div class="bar - label">F (无法理解)</div>
                    <div class="bar - value">{cc_dist['F']}</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>可维护性分布</h2>
            <div class="chart">
                <div class="bar">
                    <div class="bar - label">A (非常可维护)</div>
                    <div class="bar - value">{mi_dist['A']}</div>
                </div>
                <div class="bar">
                    <div class="bar - label">B (可维护)</div>
                    <div class="bar - value">{mi_dist['B']}</div>
                </div>
                <div class="bar">
                    <div class="bar - label">C (难以维护)</div>
                    <div class="bar - value">{mi_dist['C']}</div>
                </div>
                <div class="bar">
                    <div class="bar - label">D (难以维护)</div>
                    <div class="bar - value">{mi_dist['D']}</div>
                </div>
                <div class="bar">
                    <div class="bar - label">F (几乎不可维护)</div>
                    <div class="bar - value">{mi_dist['F']}</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>最复杂的函数 (Top 10)</h2>
            <table>
                <tr>
                    <th>文件</th>
                    <th>函数</th>
                    <th>行号</th>
                    <th>复杂度</th>
                    <th>评级</th>
                </tr>
"""

        for metric in top_complex:
            html_content += """
                <tr>
                    <td>{metric.file}</td>
                    <td>{metric.function}</td>
                    <td>{metric.line}</td>
                    <td>{metric.complexity}</td>
                    <td class="complexity-{metric.rank}">{metric.rank}</td>
                </tr>
"""

        html_content += """
            </table>
        </div>

        <div class="section">
            <h2>可维护性最低的函数 (Top 10)</h2>
            <table>
                <tr>
                    <th>文件</th>
                    <th>函数</th>
                    <th>行号</th>
                    <th>可维护性指数</th>
                    <th>评级</th>
                </tr>
"""

        for metric in least_maintainable:
            html_content += """
                <tr>
                    <td>{metric.file}</td>
                    <td>{metric.function}</td>
                    <td>{metric.line}</td>
                    <td>{metric.raw_score:.2f}</td>
                    <td class="complexity-{metric.rank}">{metric.rank}</td>
                </tr>
"""

        html_content += """
            </table>
        </div>
    </div>
</body>
</html>
"""

        with open(output_file, "w", encoding="utf - 8") as f:
            f.write(html_content)

        print(f"HTML报告已保存到: {output_file}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="代码复杂度分析器")
    parser.add_argument(
        "--target",
        default="src",
        help="分析目标目录 (default: src)"
    )
    parser.add_argument(
        "--output",
        default="console",
        choices=["console", "json", "html"],
        help="输出格式 (default: console)"
    )

    args = parser.parse_args()

    analyzer = ComplexityAnalyzer(target=args.target)

    print("正在分析圈复杂度...")
    analyzer.analyze_cyclomatic_complexity()

    print("正在分析可维护性指数...")
    analyzer.analyze_maintainability()

    print("正在生成报告...")
    analyzer.generate_report(output_format=args.output)


if __name__ == "__main__":
    main()

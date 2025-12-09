#!/usr / bin / env python3
"""
Code Quality Checker - 综合代码质量检查工具
===========================================

整合所有代码质量工具的检查，提供统一的报告界面。

用法:
    python scripts / code_quality_checker.py [--target TARGET] [--output FORMAT]

参数:
    --target: 检查目标 (default: src)
    --output: 输出格式 (console, json, html)
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import concurrent.futures
from dataclasses import dataclass, asdict


@dataclass
class QualityCheckResult:
    """代码质量检查结果"""
    tool: str
    status: str  # PASS, FAIL, WARNING
    score: Optional[float]
    issues: List[Dict[str, Any]]
    execution_time: float
    output_file: Optional[str]


class CodeQualityChecker:
    """代码质量检查器主类"""

    def __init__(self, target: str = "src", output_dir: str = "reports"):
        self.target = target
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y % m % d_ % H % M % S")
        self.results: List[QualityCheckResult] = []

    def run_command(
        self,
        cmd: List[str],
        timeout: int = 300,
        capture_output: bool = True
    ) -> subprocess.CompletedProcess:
        """执行命令并返回结果"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                cwd=Path.cwd()
            )
            return result
        except subprocess.TimeoutExpired:
            print(f"命令超时: {' '.join(cmd)}")
            return subprocess.CompletedProcess(
                cmd, -1, "", "命令执行超时", ""
            )

    def check_mypy(self) -> QualityCheckResult:
        """MyPy类型检查"""
        start_time = time.time()
        output_file = self.output_dir / f"mypy_{self.timestamp}.json"
        cmd = [
            "mypy", self.target,
            "--config - file=mypy.ini",
            "--show - error - codes",
            "--show - column - numbers",
            f"--output - json={output_file}"
        ]

        result = self.run_command(cmd)
        execution_time = time.time() - start_time

        # 解析结果
        issues = []
        if result.stdout:
            try:
                data = json.loads(result.stdout)
                if isinstance(data, list):
                    for item in data:
                        issues.append({
                            "file": item.get("file", ""),
                            "line": item.get("line", 0),
                            "column": item.get("column", 0),
                            "message": item.get("message", ""),
                            "code": item.get("code", "")
                        })
            except json.JSONDecodeError:
                pass

        status = "PASS" if result.returncode == 0 else "FAIL"
        score = max(0, 100 - len(issues) * 5) if issues else 100

        return QualityCheckResult(
            tool="mypy",
            status=status,
            score=score,
            issues=issues,
            execution_time=execution_time,
            output_file=str(output_file)
        )

    def check_bandit(self) -> QualityCheckResult:
        """Bandit安全检查"""
        start_time = time.time()
        output_file = self.output_dir / f"bandit_{self.timestamp}.json"
        cmd = [
            "bandit", "-r", self.target,
            "-", "json",
            "-o", str(output_file),
            "-x", "tests/"
        ]

        result = self.run_command(cmd)
        execution_time = time.time() - start_time

        # 读取输出文件
        issues = []
        if output_file.exists():
            try:
                with open(output_file) as f:
                    data = json.load(f)
                    results = data.get("results", [])
                    for issue in results:
                        issues.append({
                            "filename": issue.get("filename", ""),
                            "line": issue.get("line_number", 0),
                            "test_id": issue.get("test_id", ""),
                            "message": issue.get("issue_text", ""),
                            "severity": issue.get("issue_severity", ""),
                            "confidence": issue.get("issue_confidence", "")
                        })
            except (json.JSONDecodeError, FileNotFoundError):
                pass

        status = "PASS" if not issues else "WARNING" if len(issues) < 5 else "FAIL"
        score = max(0, 100 - len(issues) * 10)

        return QualityCheckResult(
            tool="bandit",
            status=status,
            score=score,
            issues=issues,
            execution_time=execution_time,
            output_file=str(output_file)
        )

    def check_flake8(self) -> QualityCheckResult:
        """Flake8代码风格检查"""
        start_time = time.time()
        output_file = self.output_dir / f"flake8_{self.timestamp}.txt"
        cmd = [
            "flake8", self.target,
            "--max - line - length=88",
            "--extend - ignore=E203,W503",
            "--output - file", str(output_file),
            "--count",
            "--statistics"
        ]

        result = self.run_command(cmd)
        execution_time = time.time() - start_time

        # 解析结果
        issues = []
        if output_file.exists():
            with open(output_file) as f:
                for line in f:
                    parts = line.split(":")
                    if len(parts) >= 4:
                        issues.append({
                            "file": parts[0],
                            "line": parts[1],
                            "column": parts[2],
                            "code": parts[3].strip(),
                            "message": ":".join(parts[4:]).strip() if len(parts) > 4 else ""
                        })

        status = "PASS" if not issues else "FAIL"
        score = max(0, 100 - len(issues) * 2)

        return QualityCheckResult(
            tool="flake8",
            status=status,
            score=score,
            issues=issues,
            execution_time=execution_time,
            output_file=str(output_file)
        )

    def check_pylint(self) -> QualityCheckResult:
        """Pylint代码质量检查"""
        start_time = time.time()
        output_file = self.output_dir / f"pylint_{self.timestamp}.json"
        cmd = [
            "pylint", self.target,
            "--output - format=json",
            f"--output={output_file}",
            "--score=yes"
        ]

        result = self.run_command(cmd)
        execution_time = time.time() - start_time

        # 读取输出文件
        issues = []
        score = None
        if output_file.exists():
            try:
                with open(output_file) as f:
                    data = json.load(f)
                    for item in data:
                        issues.append({
                            "file": item.get("path", ""),
                            "line": item.get("line", 0),
                            "column": item.get("column", 0),
                            "message": item.get("message", ""),
                            "symbol": item.get("symbol", ""),
                            "type": item.get("type", "")
                        })
            except (json.JSONDecodeError, FileNotFoundError):
                pass

        # 提取评分
        if result.stdout:
            for line in result.stdout.split("\n"):
                if "rated at" in line:
                    try:
                        score = float(line.split()[-2])
                    except (IndexError, ValueError):
                        pass

        if score is None:
            # 根据问题数量估算评分
            score = max(0, 100 - len(issues) * 0.5)

        status = "PASS" if score >= 8.0 else "WARNING" if score >= 6.0 else "FAIL"

        return QualityCheckResult(
            tool="pylint",
            status=status,
            score=score,
            issues=issues,
            execution_time=execution_time,
            output_file=str(output_file)
        )

    def check_radon(self) -> QualityCheckResult:
        """Radon复杂度检查"""
        start_time = time.time()
        cc_file = self.output_dir / f"radon_cc_{self.timestamp}.json"
        mi_file = self.output_dir / f"radon_mi_{self.timestamp}.json"
        cmd_cc = ["radon", "cc", self.target, "-j", "-o", str(cc_file), "--min=B"]
        cmd_mi = ["radon", "mi", self.target, "-j", "-o", str(mi_file), "--min=B"]

        result_cc = self.run_command(cmd_cc)
        result_mi = self.run_command(cmd_mi)
        execution_time = time.time() - start_time

        # 解析结果
        issues = []
        high_complexity_count = 0

        # 读取CC结果
        if cc_file.exists():
            try:
                with open(cc_file) as f:
                    data = json.load(f)
                    for item in data:
                        complexity = item.get("complexity", 0)
                        if complexity > 10:
                            high_complexity_count += 1
                            issues.append({
                                "file": item.get("path", ""),
                                "function": item.get("name", ""),
                                "line": item.get("lineno", 0),
                                "complexity": complexity,
                                "rank": item.get("rank", ""),
                                "type": "cyclomatic_complexity"
                            })
            except (json.JSONDecodeError, FileNotFoundError):
                pass

        # 读取MI结果
        if mi_file.exists():
            try:
                with open(mi_file) as f:
                    data = json.load(f)
                    for item in data:
                        if item.get("rank", "A") in ["C", "D", "E", "F"]:
                            issues.append({
                                "file": item.get("path", ""),
                                "function": item.get("name", ""),
                                "line": item.get("lineno", 0),
                                "maintainability_index": item.get("mi", 0),
                                "rank": item.get("rank", ""),
                                "type": "maintainability_index"
                            })
            except (json.JSONDecodeError, FileNotFoundError):
                pass

        status = "PASS" if high_complexity_count == 0 else "WARNING" if high_complexity_count < 5 else "FAIL"
        score = max(0, 100 - high_complexity_count * 20)

        return QualityCheckResult(
            tool="radon",
            status=status,
            score=score,
            issues=issues,
            execution_time=execution_time,
            output_file=str(cc_file)
        )

    def check_todos(self) -> QualityCheckResult:
        """技术债务检查 - TODO和FIXME标记"""
        start_time = time.time()
        output_file = self.output_dir / f"tech_debt_{self.timestamp}.json"

        cmd = [
            "grep", "-r", "--include=*.py",
            "-n", "-i",
            "TODO\\|FIXME\\|XXX\\|HACK\\|BUG",
            self.target
        ]

        result = self.run_command(cmd)
        execution_time = time.time() - start_time

        # 解析结果
        issues = []
        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                if line.strip():
                    parts = line.split(":", 2)
                    if len(parts) >= 3:
                        issues.append({
                            "file": parts[0],
                            "line": parts[1],
                            "type": "TODO" if "TODO" in parts[2] else
                                   "FIXME" if "FIXME" in parts[2] else
                                   "XXX" if "XXX" in parts[2] else
                                   "HACK" if "HACK" in parts[2] else
                                   "BUG" if "BUG" in parts[2] else "UNKNOWN",
                            "message": parts[2].strip()
                        })

        # 按优先级分类
        priority_issues = {
            "CRITICAL": 0,  # BUG
            "HIGH": 0,      # FIXME
            "MEDIUM": 0,    # TODO, XXX
            "LOW": 0        # HACK
        }

        for issue in issues:
            if issue["type"] in priority_issues:
                priority_issues[issue["type"]] += 1
            else:
                priority_issues["MEDIUM"] += 1

        status = "WARNING" if sum(priority_issues.values()) > 0 else "PASS"
        score = 100 - sum(priority_issues.values()) * 5

        # 保存结果
        with open(output_file, "w") as f:
            json.dump(priority_issues, f, indent=2)

        return QualityCheckResult(
            tool="technical_debt",
            status=status,
            score=score,
            issues=issues,
            execution_time=execution_time,
            output_file=str(output_file)
        )

    def run_all_checks(self, parallel: bool = True) -> None:
        """运行所有检查"""
        print("=" * 60)
        print("代码质量综合检查")
        print("=" * 60)
        print(f"目标目录: {self.target}")
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        checks = [
            ("MyPy类型检查", self.check_mypy),
            ("Bandit安全检查", self.check_bandit),
            ("Flake8代码风格", self.check_flake8),
            ("Pylint代码质量", self.check_pylint),
            ("Radon复杂度分析", self.check_radon),
            ("技术债务跟踪", self.check_todos)
        ]

        if parallel:
            with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
                futures = {executor.submit(func): name for name, func in checks}
                for future in concurrent.futures.as_completed(futures):
                    name = futures[future]
                    try:
                        result = future.result()
                        self.results.append(result)
                        self._print_result(result)
                    except Exception as e:
                        print(f"✗ {name} 执行失败: {e}")
        else:
            for name, func in checks:
                result = func()
                self.results.append(result)
                self._print_result(result)

        self._print_summary()

    def _print_result(self, result: QualityCheckResult) -> None:
        """打印检查结果"""
        status_symbol = {
            "PASS": "✓",
            "WARNING": "⚠",
            "FAIL": "✗"
        }

        symbol = status_symbol.get(result.status, "?")
        print(f"{symbol} {result.tool}")
        print(f"  状态: {result.status}")
        print(f"  评分: {result.score:.2f}/100" if result.score is not None else "  评分: N / A")
        print(f"  问题数: {len(result.issues)}")
        print(f"  执行时间: {result.execution_time:.2f}s")
        if result.issues:
            top_issues = result.issues[:3]
            for issue in top_issues:
                print(f"    - {issue}")
        print()

    def _print_summary(self) -> None:
        """打印总结报告"""
        print("=" * 60)
        print("检查总结")
        print("=" * 60)

        total_issues = sum(len(r.issues) for r in self.results)
        avg_score = sum(r.score for r in self.results if r.score) / len(self.results) if self.results else 0
        total_time = sum(r.execution_time for r in self.results)

        pass_count = sum(1 for r in self.results if r.status == "PASS")
        warning_count = sum(1 for r in self.results if r.status == "WARNING")
        fail_count = sum(1 for r in self.results if r.status == "FAIL")

        print(f"总平均分: {avg_score:.2f}/100")
        print(f"总问题数: {total_issues}")
        print(f"总执行时间: {total_time:.2f}s")
        print()
        print("工具状态分布:")
        print(f"  ✓ 通过: {pass_count}")
        print(f"  ⚠ 警告: {warning_count}")
        print(f"  ✗ 失败: {fail_count}")
        print()

        # 质量评级
        if avg_score >= 95:
            grade = "A+ (优秀)"
        elif avg_score >= 90:
            grade = "A (良好)"
        elif avg_score >= 80:
            grade = "B (中等)"
        elif avg_score >= 70:
            grade = "C (需改进)"
        elif avg_score >= 60:
            grade = "D (较差)"
        else:
            grade = "F (不合格)"

        print(f"质量评级: {grade}")
        print()

        # 保存汇总报告
        self._save_summary_report()

    def _save_summary_report(self) -> None:
        """保存汇总报告"""
        report = {
            "timestamp": self.timestamp,
            "target": self.target,
            "summary": {
                "total_checks": len(self.results),
                "passed": sum(1 for r in self.results if r.status == "PASS"),
                "warnings": sum(1 for r in self.results if r.status == "WARNING"),
                "failed": sum(1 for r in self.results if r.status == "FAIL"),
                "total_issues": sum(len(r.issues) for r in self.results),
                "average_score": sum(r.score for r in self.results if r.score) / len(self.results) if self.results else 0,
                "total_execution_time": sum(r.execution_time for r in self.results)
            },
            "results": [asdict(r) for r in self.results]
        }

        output_file = self.output_dir / f"quality_summary_{self.timestamp}.json"
        with open(output_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        print(f"详细报告已保存到: {output_file}")

    def generate_html_report(self) -> None:
        """生成HTML报告"""
        html_file = self.output_dir / f"quality_report_{self.timestamp}.html"

        html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF - 8">
    <title>代码质量检查报告</title>
    <style>
        body {{ font - family: Arial, sans - serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .summary {{ background: #f5f5f5; padding: 15px; border - radius: 5px; }}
        .tool {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border - radius: 5px; }}
        .pass {{ background - color: #d4edda; border - color: #c3e6cb; }}
        .warning {{ background - color: #fff3cd; border - color: #ffeaa7; }}
        .fail {{ background - color: #f8d7da; border - color: #f5c6cb; }}
        .issues {{ margin - top: 10px; }}
        .issue {{ padding: 5px; margin: 5px 0; background: #fff; border - left: 3px solid #007bff; }}
        .score {{ font - size: 24px; font - weight: bold; }}
    </style>
</head>
<body>
    <h1>代码质量检查报告</h1>
    <div class="summary">
        <h2>总体情况</h2>
        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>目标目录: {self.target}</p>
        <p>检查工具数: {len(self.results)}</p>
    </div>
"""

        for result in self.results:
            status_class = result.status.lower()
            html_content += """
    <div class="tool {status_class}">
        <h3>{result.tool}</h3>
        <p>状态: {result.status}</p>
        <p class="score">评分: {result.score:.2f}/100</p>
        <p>问题数: {len(result.issues)}</p>
        <p>执行时间: {result.execution_time:.2f}s</p>
        <div class="issues">
"""

            for issue in result.issues[:10]:  # 只显示前10个问题
                html_content += "            <div class="issue'>{issue}</div>\n"

            if len(result.issues) > 10:
                html_content += "            <div class="issue'>...还有 {len(result.issues) - 10} 个问题</div>\n"

            html_content += """
        </div>
    </div>
"""

        html_content += """
</body>
</html>
"""

        with open(html_file, "w", encoding="utf - 8") as f:
            f.write(html_content)

        print(f"HTML报告已生成: {html_file}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="代码质量检查工具")
    parser.add_argument(
        "--target",
        default="src",
        help="检查目标目录 (default: src)"
    )
    parser.add_argument(
        "--output",
        default="console",
        choices=["console", "json", "html"],
        help="输出格式 (default: console)"
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="并行执行检查 (default: True)"
    )
    parser.add_argument(
        "--sequential",
        dest="parallel",
        action="store_false",
        help="顺序执行检查"
    )
    parser.set_defaults(parallel=True)

    args = parser.parse_args()

    checker = CodeQualityChecker(target=args.target)
    checker.run_all_checks(parallel=args.parallel)

    if args.output == "html":
        checker.generate_html_report()


if __name__ == "__main__":
    main()

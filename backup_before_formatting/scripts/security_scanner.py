#!/usr / bin / env python3
"""
安全扫描器 (Security Scanner)
============================

使用多种工具进行代码安全检查。

用法:
    python scripts / security_scanner.py [--target TARGET] [--output FORMAT]
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
class SecurityIssue:
    """安全漏洞"""
    tool: str
    file: str
    line: int
    test_id: str
    message: str
    severity: str  # LOW, MEDIUM, HIGH
    confidence: str  # LOW, MEDIUM, HIGH
    cwe_id: str = ""


class SecurityScanner:
    """安全扫描器"""

    def __init__(self, target: str = "src", output_dir: str = "reports"):
        self.target = target
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y % m % d_ % H % M % S")
        self.issues: List[SecurityIssue] = []

    def run_bandit(self) -> None:
        """运行Bandit安全扫描"""
        print("运行 Bandit 安全扫描...")
        output_file = self.output_dir / f"bandit_{self.timestamp}.json"
        cmd = [
            "bandit", "-r", self.target,
            "-", "json",
            "-o", str(output_file),
            "-x", "tests/"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)

            if output_file.exists():
                with open(output_file) as f:
                    data = json.load(f)
                    results = data.get("results", [])
                    for issue in results:
                        self.issues.append(SecurityIssue(
                            tool="bandit",
                            file=issue.get("filename", ""),
                            line=issue.get("line_number", 0),
                            test_id=issue.get("test_id", ""),
                            message=issue.get("issue_text", ""),
                            severity=issue.get("issue_severity", ""),
                            confidence=issue.get("issue_confidence", ""),
                            cwe_id=issue.get("cwe_id", "")
                        ))
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Bandit扫描失败: {e}")

    def run_safety(self) -> None:
        """运行Safety依赖检查"""
        print("运行 Safety 依赖漏洞检查...")
        output_file = self.output_dir / f"safety_{self.timestamp}.json"
        cmd = ["safety", "check", "--json", "--output", str(output_file)]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)

            if output_file.exists():
                with open(output_file) as f:
                    data = json.load(f)
                    for vuln in data:
                        self.issues.append(SecurityIssue(
                            tool="safety",
                            file=f"依赖: {vuln.get('package_name', '')}",
                            line=0,
                            test_id=vuln.get("vulnerability_id", ""),
                            message=f"{vuln.get('advisory', '')}",
                            severity=vuln.get("severity", ""),
                            confidence="MEDIUM",
                            cwe_id=vuln.get("vulnerability_id", "")
                        ))
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Safety扫描失败: {e}")

    def scan_secrets(self) -> None:
        """扫描密钥泄露"""
        print("扫描密钥泄露...")
        secrets_patterns = [
            r"api[_-]?key\s*[:=]\s*['\"]([a - zA - Z0 - 9_\-]{20,})['\"]",
            r"secret[_-]?key\s*[:=]\s*['\"]([a - zA - Z0 - 9_\-]{20,})['\"]",
            r"password\s*[:=]\s*['\"]([^\s'\"]{8,})['\"]",
            r"token\s*[:=]\s*['\"]([a - zA - Z0 - 9_\-]{20,})['\"]",
            r"-----BEGIN [A - Z ]*PRIVATE KEY-----",
            r"AKIA[0 - 9A - Z]{16}",
            r"[a - zA - Z0 - 9]{32}",  # 可能是MD5
            r"[0 - 9a - f]{40}",  # 可能是SHA1
        ]

        for file_path in Path(self.target).rglob("*.py"):
            try:
                with open(file_path, "r", encoding="utf - 8", errors="ignore") as f:
                    lines = f.readlines()
                    for line_num, line in enumerate(lines, 1):
                        for pattern in secrets_patterns:
                            import re
                            if re.search(pattern, line, re.IGNORECASE):
                                self.issues.append(SecurityIssue(
                                    tool="secret_scanner",
                                    file=str(file_path.relative_to(self.target)),
                                    line=line_num,
                                    test_id="S001",
                                    message=f"可能泄露的敏感信息: {line.strip()[:80]}",
                                    severity="HIGH",
                                    confidence="MEDIUM"
                                ))
            except Exception as e:
                continue

    def get_issues_by_severity(self) -> Dict[str, List[SecurityIssue]]:
        """按严重程度分组问题"""
        return {
            "HIGH": [i for i in self.issues if i.severity == "HIGH"],
            "MEDIUM": [i for i in self.issues if i.severity == "MEDIUM"],
            "LOW": [i for i in self.issues if i.severity == "LOW"]
        }

    def get_issues_by_tool(self) -> Dict[str, List[SecurityIssue]]:
        """按工具分组问题"""
        groups = {}
        for issue in self.issues:
            if issue.tool not in groups:
                groups[issue.tool] = []
            groups[issue.tool].append(issue)
        return groups

    def calculate_security_score(self) -> float:
        """计算安全评分"""
        if not self.issues:
            return 100.0

        score = 100.0
        for issue in self.issues:
            if issue.severity == "HIGH":
                score -= 20
            elif issue.severity == "MEDIUM":
                score -= 10
            else:
                score -= 5

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
        print("安全扫描报告")
        print("=" * 70)
        print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"目标目录: {self.target}")
        print(f"发现问题数: {len(self.issues)}")
        print()

        # 安全评分
        security_score = self.calculate_security_score()
        print(f"安全评分: {security_score:.2f}/100")

        if security_score >= 90:
            print("安全等级: A (安全)")
        elif security_score >= 80:
            print("安全等级: B (较安全)")
        elif security_score >= 70:
            print("安全等级: C (一般)")
        elif security_score >= 60:
            print("安全等级: D (较危险)")
        else:
            print("安全等级: F (危险)")
        print()

        # 按严重程度统计
        severity_groups = self.get_issues_by_severity()
        print("问题分布:")
        for severity in ["HIGH", "MEDIUM", "LOW"]:
            count = len(severity_groups[severity])
            print(f"  {severity:6} {count:3} 个")
        print()

        # 按工具统计
        tool_groups = self.get_issues_by_tool()
        print("工具发现问题:")
        for tool, issues in tool_groups.items():
            print(f"  {tool:15} {len(issues):3} 个")
        print()

        # 详细问题列表
        if self.issues:
            print("安全问题详情:")
            print("-" * 70)
            for issue in self.issues:
                severity_icon = "🔴" if issue.severity == "HIGH" else "🟡" if issue.severity == "MEDIUM" else "🟢"
                print(f"{severity_icon} [{issue.severity}] {issue.tool}")
                print(f"  文件: {issue.file}")
                if issue.line > 0:
                    print(f"  行号: {issue.line}")
                print(f"  问题: {issue.message}")
                print(f"  测试ID: {issue.test_id}")
                if issue.cwe_id:
                    print(f"  CWE ID: {issue.cwe_id}")
                print()

        # 建议
        print("安全建议:")
        print("-" * 70)
        high_count = len(severity_groups["HIGH"])
        medium_count = len(severity_groups["MEDIUM"])

        if high_count > 0:
            print(f"🚨 紧急: 发现 {high_count} 个高危漏洞，需要立即修复")
        if medium_count > 0:
            print(f"⚠️  警告: 发现 {medium_count} 个中危漏洞，建议尽快修复")
        if high_count == 0 and medium_count == 0:
            print("✅ 未发现严重安全问题")

        print("\n常见安全最佳实践:")
        print("1. 使用环境变量存储敏感信息")
        print("2. 定期更新依赖包到最新版本")
        print("3. 避免在代码中硬编码密钥和密码")
        print("4. 对用户输入进行验证和清理")
        print("5. 使用HTTPS和安全的加密算法")
        print("6. 启用适当的安全头")
        print("7. 定期进行安全审计")

    def _save_json_report(self) -> None:
        """保存JSON报告"""
        output_file = self.output_dir / f"security_report_{self.timestamp}.json"

        report = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "target_directory": self.target,
                "total_issues": len(self.issues)
            },
            "summary": {
                "security_score": self.calculate_security_score(),
                "by_severity": {k: len(v) for k, v in self.get_issues_by_severity().items()},
                "by_tool": {k: len(v) for k, v in self.get_issues_by_tool().items()}
            },
            "issues": [asdict(issue) for issue in self.issues]
        }

        with open(output_file, "w", encoding="utf - 8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"JSON报告已保存到: {output_file}")

    def _save_html_report(self) -> None:
        """保存HTML报告"""
        output_file = self.output_dir / f"security_report_{self.timestamp}.html"

        severity_groups = self.get_issues_by_severity()
        tool_groups = self.get_issues_by_tool()
        security_score = self.calculate_security_score()
        score_grade = "A" if security_score >= 90 else "B" if security_score >= 80 else "C" if security_score >= 70 else "D" if security_score >= 60 else "F"

        html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF - 8">
    <title>安全扫描报告</title>
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
        .summary - grid {{ display: grid; grid - template - columns: repeat(3, 1fr); gap: 20px; margin: 20px 0; }}
        .summary - card {{ background: #f8f9fa; padding: 20px; border - radius: 5px; text - align: center; }}
        .summary - card h3 {{ margin: 0 0 10px 0; font - size: 14px; color: #666; }}
        .summary - card .value {{ font - size: 36px; font - weight: bold; }}
        .value.HIGH {{ color: #dc3545; }}
        .value.MEDIUM {{ color: #ffc107; }}
        .value.LOW {{ color: #28a745; }}
        table {{ width: 100%; border - collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text - align: left; border - bottom: 1px solid #ddd; }}
        th {{ background - color: #f8f9fa; font - weight: bold; }}
        tr:hover {{ background - color: #f5f5f5; }}
        .severity - HIGH {{ color: #dc3545; font - weight: bold; }}
        .severity - MEDIUM {{ color: #ffc107; font - weight: bold; }}
        .severity - LOW {{ color: #28a745; font - weight: bold; }}
        .tag {{ display: inline - block; padding: 4px 8px; border - radius: 3px; font - size: 12px; font - weight: bold; }}
        .tag - BANDIT {{ background: #e3f2fd; color: #1976d2; }}
        .tag - SAFETY {{ background: #fff3e0; color: #f57c00; }}
        .tag - SECRET {{ background: #ffebee; color: #c2185b; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>安全扫描报告</h1>
        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>目标目录: {self.target}</p>

        <div class="score {score_grade}">
            {security_score:.2f}/100
            <div style="font - size: 24px; margin - top: 10px;">等级: {score_grade}</div>
        </div>

        <div class="summary - grid">
            <div class="summary - card">
                <h3>高危漏洞</h3>
                <div class="value HIGH">{len(severity_groups['HIGH'])}</div>
            </div>
            <div class="summary - card">
                <h3>中危漏洞</h3>
                <div class="value MEDIUM">{len(severity_groups['MEDIUM'])}</div>
            </div>
            <div class="summary - card">
                <h3>低危漏洞</h3>
                <div class="value LOW">{len(severity_groups['LOW'])}</div>
            </div>
        </div>

        <div class="section">
            <h2>按工具分类</h2>
            <table>
                <tr>
                    <th>工具</th>
                    <th>问题数</th>
                </tr>
"""

        for tool, issues in tool_groups.items():
            html_content += """
                <tr>
                    <td>{tool}</td>
                    <td>{len(issues)}</td>
                </tr>
"""

        html_content += """
            </table>
        </div>

        <div class="section">
            <h2>安全问题详情</h2>
            <table>
                <tr>
                    <th>工具</th>
                    <th>严重程度</th>
                    <th>文件</th>
                    <th>行号</th>
                    <th>问题描述</th>
                    <th>测试ID</th>
                </tr>
"""

        for issue in self.issues:
            tool_class = f"tag-{issue.tool.upper()}"
            html_content += """
                <tr>
                    <td><span class="{tool_class}">{issue.tool}</span></td>
                    <td class="severity-{issue.severity}">{issue.severity}</td>
                    <td>{issue.file}</td>
                    <td>{issue.line if issue.line > 0 else '-'}</td>
                    <td>{issue.message[:100]}{'...' if len(issue.message) > 100 else ''}</td>
                    <td>{issue.test_id}</td>
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
    parser = argparse.ArgumentParser(description="安全扫描器")
    parser.add_argument(
        "--target",
        default="src",
        help="扫描目标目录 (default: src)"
    )
    parser.add_argument(
        "--output",
        default="console",
        choices=["console", "json", "html"],
        help="输出格式 (default: console)"
    )

    args = parser.parse_args()

    scanner = SecurityScanner(target=args.target)
    scanner.run_bandit()
    scanner.run_safety()
    scanner.scan_secrets()
    scanner.generate_report(output_format=args.output)


if __name__ == "__main__":
    main()

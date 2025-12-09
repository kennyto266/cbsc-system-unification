#!/usr / bin / env python3
"""
技术债务跟踪器 (Technical Debt Tracker)
======================================

跟踪和分析代码中的技术债务，包括TODO、FIXME等标记。

用法:
    python scripts / tech_debt_tracker.py [--target TARGET] [--output FORMAT]
"""

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict


class TechnicalDebtTracker:
    """技术债务跟踪器"""

    # 技术债务标记正则表达式
    DEBT_PATTERNS = {
        "TODO": r"TODO[:\s]*(.+)?",
        "FIXME": r"FIXME[:\s]*(.+)?",
        "XXX": r"XXX[:\s]*(.+)?",
        "HACK": r"HACK[:\s]*(.+)?",
        "BUG": r"BUG[:\s]*(.+)?",
        "DEPRECATED": r"DEPRECATED[:\s]*(.+)?",
        "NOTE": r"NOTE[:\s]*(.+)?",
        "WARNING": r"WARNING[:\s]*(.+)?"
    }

    # 优先级定义
    PRIORITY = {
        "BUG": "CRITICAL",
        "FIXME": "HIGH",
        "TODO": "MEDIUM",
        "XXX": "MEDIUM",
        "HACK": "LOW",
        "DEPRECATED": "HIGH",
        "NOTE": "LOW",
        "WARNING": "MEDIUM"
    }

    # 支持的文件扩展名
    FILE_EXTENSIONS = {".py", ".js", ".ts", ".vue", ".java", ".c", ".cpp", ".h", ".cs", ".php"}

    def __init__(self, target: str = "src"):
        self.target = Path(target)
        self.debt_items: List[Dict] = []

    def scan_directory(self) -> None:
        """扫描目录查找技术债务"""
        for file_path in self.target.rglob("*"):
            if file_path.is_file() and file_path.suffix in self.FILE_EXTENSIONS:
                self._scan_file(file_path)

    def _scan_file(self, file_path: Path) -> None:
        """扫描单个文件"""
        try:
            with open(file_path, "r", encoding="utf - 8", errors="ignore") as f:
                lines = f.readlines()

                for line_num, line in enumerate(lines, 1):
                    for debt_type, pattern in self.DEBT_PATTERNS.items():
                        match = re.search(pattern, line, re.IGNORECASE)
                        if match:
                            self._add_debt_item(
                                file_path=file_path,
                                line_number=line_num,
                                debt_type=debt_type,
                                content=line.strip(),
                                description=match.group(1).strip() if match.group(1) else ""
                            )
        except Exception as e:
            print(f"扫描文件失败 {file_path}: {e}")

    def _add_debt_item(
        self,
        file_path: Path,
        line_number: int,
        debt_type: str,
        content: str,
        description: str
    ) -> None:
        """添加技术债务项"""
        item = {
            "file": str(file_path.relative_to(self.target)) if file_path.is_relative_to(self.target) else str(file_path),
            "line": line_number,
            "type": debt_type,
            "priority": self.PRIORITY.get(debt_type, "UNKNOWN"),
            "content": content,
            "description": description,
            "age_days": 0  # 可以通过git blame计算
        }
        self.debt_items.append(item)

    def categorize(self) -> Dict[str, List[Dict]]:
        """按类别分组债务"""
        categorized = defaultdict(list)
        for item in self.debt_items:
            categorized[item["type"]].append(item)
        return dict(categorized)

    def prioritize(self) -> Dict[str, List[Dict]]:
        """按优先级分组债务"""
        priority_groups = {
            "CRITICAL": [],
            "HIGH": [],
            "MEDIUM": [],
            "LOW": [],
            "UNKNOWN": []
        }
        for item in self.debt_items:
            priority_groups[item["priority"]].append(item)
        return priority_groups

    def analyze_files(self) -> List[Tuple[str, int]]:
        """分析每个文件的债务数量"""
        file_debt = defaultdict(int)
        for item in self.debt_items:
            file_debt[item["file"]] += 1
        return sorted(file_debt.items(), key=lambda x: x[1], reverse=True)

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
        print("技术债务跟踪报告")
        print("=" * 70)
        print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"扫描目录: {self.target}")
        print(f"债务总数: {len(self.debt_items)}")
        print()

        # 按类型统计
        categorized = self.categorize()
        print("按类型统计:")
        for debt_type, items in sorted(categorized.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"  {debt_type:15} {len(items):5} 项")
        print()

        # 按优先级统计
        priority_groups = self.prioritize()
        print("按优先级统计:")
        for priority, items in priority_groups.items():
            if items:
                print(f"  {priority:10} {len(items):5} 项")
        print()

        # Top 10 问题文件
        file_debt = self.analyze_files()
        if file_debt:
            print("问题最多的文件 (Top 10):")
            for file_path, count in file_debt[:10]:
                print(f"  {file_path:50} {count} 项")
            print()

        # 详细列表
        print("详细债务列表:")
        print("-" * 70)
        for item in self.debt_items:
            print(f"{item['type']:10} | {item['priority']:8} | {item['file']:30} | L{item['line']:3} | {item['description']}")

    def _save_json_report(self) -> None:
        """保存JSON报告"""
        timestamp = datetime.now().strftime("%Y % m % d_ % H % M % S")
        output_file = Path(f"reports / tech_debt_{timestamp}.json")

        report = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "target_directory": str(self.target),
                "total_items": len(self.debt_items)
            },
            "summary": {
                "by_type": {k: len(v) for k, v in self.categorize().items()},
                "by_priority": {k: len(v) for k, v in self.prioritize().items()},
                "by_file": dict(self.analyze_files())
            },
            "items": self.debt_items
        }

        output_file.parent.mkdir(exist_ok=True)
        with open(output_file, "w", encoding="utf - 8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"JSON报告已保存到: {output_file}")

    def _save_html_report(self) -> None:
        """保存HTML报告"""
        timestamp = datetime.now().strftime("%Y % m % d_ % H % M % S")
        output_file = Path(f"reports / tech_debt_{timestamp}.html")

        categorized = self.categorize()
        priority_groups = self.prioritize()
        file_debt = self.analyze_files()

        html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF - 8">
    <title>技术债务跟踪报告</title>
    <style>
        body {{ font - family: Arial, sans - serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max - width: 1200px; margin: 0 auto; background: white; padding: 20px; border - radius: 8px; box - shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1, h2 {{ color: #333; }}
        .summary {{ display: grid; grid - template - columns: repeat(auto - fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .summary - card {{ background: #f8f9fa; padding: 15px; border - radius: 5px; border - left: 4px solid #007bff; }}
        .summary - card h3 {{ margin: 0 0 10px 0; font - size: 16px; color: #666; }}
        .summary - card .value {{ font - size: 32px; font - weight: bold; color: #007bff; }}
        .section {{ margin: 30px 0; }}
        table {{ width: 100%; border - collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 10px; text - align: left; border - bottom: 1px solid #ddd; }}
        th {{ background - color: #f8f9fa; font - weight: bold; }}
        tr:hover {{ background - color: #f5f5f5; }}
        .priority - CRITICAL {{ color: #dc3545; font - weight: bold; }}
        .priority - HIGH {{ color: #fd7e14; font - weight: bold; }}
        .priority - MEDIUM {{ color: #ffc107; }}
        .priority - LOW {{ color: #28a745; }}
        .tag {{ display: inline - block; padding: 3px 8px; border - radius: 3px; font - size: 12px; font - weight: bold; }}
        .tag - TODO {{ background: #e3f2fd; color: #1976d2; }}
        .tag - FIXME {{ background: #fff3e0; color: #f57c00; }}
        .tag - XXX {{ background: #fce4ec; color: #c2185b; }}
        .tag - HACK {{ background: #f3e5f5; color: #7b1fa2; }}
        .tag - BUG {{ background: #ffebee; color: #d32f2f; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>技术债务跟踪报告</h1>
        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>扫描目录: {self.target}</p>

        <div class="summary">
            <div class="summary - card">
                <h3>债务总数</h3>
                <div class="value">{len(self.debt_items)}</div>
            </div>
            <div class="summary - card">
                <h3>Critical</h3>
                <div class="value" style="color: #dc3545;">{len(priority_groups['CRITICAL'])}</div>
            </div>
            <div class="summary - card">
                <h3>High</h3>
                <div class="value" style="color: #fd7e14;">{len(priority_groups['HIGH'])}</div>
            </div>
            <div class="summary - card">
                <h3>Medium</h3>
                <div class="value" style="color: #ffc107;">{len(priority_groups['MEDIUM'])}</div>
            </div>
            <div class="summary - card">
                <h3>Low</h3>
                <div class="value" style="color: #28a745;">{len(priority_groups['LOW'])}</div>
            </div>
        </div>

        <div class="section">
            <h2>按类型分布</h2>
            <table>
                <tr>
                    <th>类型</th>
                    <th>数量</th>
                    <th>占比</th>
                </tr>
"""

        for debt_type, items in sorted(categorized.items(), key=lambda x: len(x[1]), reverse=True):
            percentage = (len(items) / len(self.debt_items) * 100) if self.debt_items else 0
            html_content += """
                <tr>
                    <td><span class="tag tag-{debt_type}">{debt_type}</span></td>
                    <td>{len(items)}</td>
                    <td>{percentage:.1f}%</td>
                </tr>
"""

        html_content += """
            </table>
        </div>

        <div class="section">
            <h2>Top 10 问题文件</h2>
            <table>
                <tr>
                    <th>文件</th>
                    <th>问题数</th>
                </tr>
"""

        for file_path, count in file_debt[:10]:
            html_content += """
                <tr>
                    <td>{file_path}</td>
                    <td>{count}</td>
                </tr>
"""

        html_content += """
            </table>
        </div>

        <div class="section">
            <h2>债务列表</h2>
            <table>
                <tr>
                    <th>类型</th>
                    <th>优先级</th>
                    <th>文件</th>
                    <th>行号</th>
                    <th>描述</th>
                </tr>
"""

        for item in self.debt_items:
            html_content += """
                <tr>
                    <td><span class="tag tag-{item['type']}">{item['type']}</span></td>
                    <td class="priority-{item['priority']}">{item['priority']}</td>
                    <td>{item['file']}</td>
                    <td>{item['line']}</td>
                    <td>{item['description']}</td>
                </tr>
"""

        html_content += """
            </table>
        </div>
    </div>
</body>
</html>
"""

        output_file.parent.mkdir(exist_ok=True)
        with open(output_file, "w", encoding="utf - 8") as f:
            f.write(html_content)

        print(f"HTML报告已保存到: {output_file}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="技术债务跟踪器")
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

    tracker = TechnicalDebtTracker(target=args.target)
    tracker.scan_directory()
    tracker.generate_report(output_format=args.output)

    # 如果有债务，退出码为1
    if tracker.debt_items:
        print(f"\n发现 {len(tracker.debt_items)} 个技术债务项")
        print("建议及时清理或添加到待办事项")


if __name__ == "__main__":
    main()

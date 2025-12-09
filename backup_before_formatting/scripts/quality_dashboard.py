#!/usr / bin / env python3
"""
代码质量仪表板 (Code Quality Dashboard)
======================================

提供代码质量指标的实时监控和可视化展示。

用法:
    python scripts / quality_dashboard.py [--port PORT] [--update - interval SECONDS]
"""

import argparse
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading


class QualityDashboard:
    """代码质量仪表板"""

    def __init__(self, reports_dir: str = "reports"):
        self.reports_dir = Path(reports_dir)
        self.data = self._load_latest_reports()

    def _load_latest_reports(self) -> Dict[str, Any]:
        """加载最新的报告"""
        data = {
            "last_updated": datetime.now().isoformat(),
            "quality_summary": None,
            "security_report": None,
            "complexity_report": None,
            "tech_debt": None,
            "coverage": None
        }

        # 查找最新的质量总结报告
        quality_files = list(self.reports_dir.glob("quality_summary_*.json"))
        if quality_files:
            latest = max(quality_files, key=lambda p: p.stat().st_mtime)
            try:
                with open(latest) as f:
                    data["quality_summary"] = json.load(f)
            except Exception:
                pass

        # 查找最新的安全报告
        security_files = list(self.reports_dir.glob("security_report_*.json"))
        if security_files:
            latest = max(security_files, key=lambda p: p.stat().st_mtime)
            try:
                with open(latest) as f:
                    data["security_report"] = json.load(f)
            except Exception:
                pass

        # 查找最新的复杂度报告
        complexity_files = list(self.reports_dir.glob("complexity_report_*.json"))
        if complexity_files:
            latest = max(complexity_files, key=lambda p: p.stat().st_mtime)
            try:
                with open(latest) as f:
                    data["complexity_report"] = json.load(f)
            except Exception:
                pass

        # 查找最新的技术债务报告
        debt_files = list(self.reports_dir.glob("tech_debt_*.json"))
        if debt_files:
            latest = max(debt_files, key=lambda p: p.stat().st_mtime)
            try:
                with open(latest) as f:
                    data["tech_debt"] = json.load(f)
            except Exception:
                pass

        # 查找覆盖率报告
        coverage_files = list(self.reports_dir.glob("coverage.xml"))
        if coverage_files:
            latest = max(coverage_files, key=lambda p: p.stat().st_mtime)
            # 简单解析覆盖率
            try:
                import xml.etree.ElementTree as ET
                tree = ET.parse(latest)
                root = tree.getroot()
                coverage_pct = root.get('line - rate')
                if coverage_pct:
                    data["coverage"] = {
                        "percentage": float(coverage_pct) * 100,
                        "timestamp": datetime.fromtimestamp(latest.stat().st_mtime).isoformat()
                    }
            except Exception:
                pass

        return data

    def _generate_html(self) -> str:
        """生成HTML仪表板"""
        quality = self.data.get("quality_summary")
        security = self.data.get("security_report")
        complexity = self.data.get("complexity_report")
        tech_debt = self.data.get("tech_debt")
        coverage = self.data.get("coverage")

        # 获取质量分数
        quality_score = quality["summary"]["average_score"] if quality else 0
        security_score = security["summary"]["security_score"] if security else 0
        complexity_score = complexity["summary"]["overall_score"] if complexity else 0
        coverage_pct = coverage["percentage"] if coverage else 0

        # 计算整体健康度
        overall_score = (quality_score + security_score + complexity_score + coverage_pct) / 4

        html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF - 8">
    <meta http - equiv="refresh" content="30">
    <title>代码质量仪表板</title>
    <style>
        * {{ margin: 0; padding: 0; box - sizing: border - box; }}
        body {{ font - family: 'Segoe UI', Tahoma, Geneva, Verdana, sans - serif; background: #1a1a2e; color: #eee; }}
        .header {{ background: linear - gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text - align: center; }}
        .header h1 {{ font - size: 36px; margin - bottom: 10px; }}
        .header p {{ font - size: 18px; opacity: 0.9; }}
        .container {{ max - width: 1400px; margin: 0 auto; padding: 20px; }}
        .metrics - grid {{ display: grid; grid - template - columns: repeat(auto - fit, minmax(250px, 1fr)); gap: 20px; margin: 30px 0; }}
        .metric - card {{ background: #16213e; border - radius: 10px; padding: 25px; box - shadow: 0 4px 6px rgba(0,0,0,0.3); transition: transform 0.3s; }}
        .metric - card:hover {{ transform: translateY(-5px); }}
        .metric - card h3 {{ font - size: 16px; color: #aaa; margin - bottom: 15px; }}
        .metric - value {{ font - size: 48px; font - weight: bold; margin - bottom: 10px; }}
        .metric - status {{ font - size: 14px; color: #aaa; }}
        .score - EXCELLENT {{ color: #38ef7d; }}
        .score - GOOD {{ color: #11998e; }}
        .score - MEDIUM {{ color: #ffc107; }}
        .score - POOR {{ color: #fd7e14; }}
        .score - FAIL {{ color: #dc3545; }}
        .sections {{ display: grid; grid - template - columns: repeat(auto - fit, minmax(400px, 1fr)); gap: 20px; margin: 30px 0; }}
        .section {{ background: #16213e; border - radius: 10px; padding: 25px; box - shadow: 0 4px 6px rgba(0,0,0,0.3); }}
        .section h2 {{ font - size: 20px; margin - bottom: 20px; color: #fff; }}
        .progress - bar {{ width: 100%; height: 30px; background: #0f3460; border - radius: 15px; overflow: hidden; margin: 10px 0; }}
        .progress - fill {{ height: 100%; background: linear - gradient(90deg, #667eea 0%, #764ba2 100%); display: flex; align - items: center; justify - content: center; color: white; font - weight: bold; transition: width 0.5s; }}
        .detail - item {{ padding: 10px; background: #0f3460; border - radius: 5px; margin: 5px 0; display: flex; justify - content: space - between; align - items: center; }}
        .detail - label {{ color: #aaa; }}
        .detail - value {{ font - weight: bold; }}
        .issue - badge {{ display: inline - block; padding: 5px 10px; border - radius: 5px; font - size: 12px; font - weight: bold; }}
        .badge - HIGH {{ background: #dc3545; color: white; }}
        .badge - MEDIUM {{ background: #ffc107; color: #000; }}
        .badge - LOW {{ background: #28a745; color: white; }}
        .status - EXCELLENT {{ color: #38ef7d; }}
        .status - GOOD {{ color: #11998e; }}
        .status - MEDIUM {{ color: #ffc107; }}
        .status - POOR {{ color: #fd7e14; }}
        .status - FAIL {{ color: #dc3545; }}
        .footer {{ text - align: center; padding: 20px; color: #aaa; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 代码质量监控仪表板</h1>
        <p>实时监控代码质量、安全性和可维护性</p>
        <p style="font - size: 14px; margin - top: 10px;">最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div class="container">
        <div class="metrics - grid">
            <div class="metric - card">
                <h3>整体质量</h3>
                <div class="metric - value score-{'EXCELLENT' if quality_score >= 90 else 'GOOD' if quality_score >= 80 else 'MEDIUM' if quality_score >= 70 else 'POOR' if quality_score >= 60 else 'FAIL'}">
                    {quality_score:.1f}
                </div>
                <div class="metric - status">
                    {'🟢 优秀' if quality_score >= 90 else '🟡 良好' if quality_score >= 80 else '🟠 中等' if quality_score >= 70 else '🔴 较差'}
                </div>
            </div>

            <div class="metric - card">
                <h3>安全性</h3>
                <div class="metric - value score-{'EXCELLENT' if security_score >= 90 else 'GOOD' if security_score >= 80 else 'MEDIUM' if security_score >= 70 else 'POOR' if security_score >= 60 else 'FAIL'}">
                    {security_score:.1f}
                </div>
                <div class="metric - status">
                    {'🟢 安全' if security_score >= 90 else '🟡 较安全' if security_score >= 80 else '🟠 一般' if security_score >= 70 else '🔴 危险'}
                </div>
            </div>

            <div class="metric - card">
                <h3>复杂度</h3>
                <div class="metric - value score-{'EXCELLENT' if complexity_score >= 90 else 'GOOD' if complexity_score >= 80 else 'MEDIUM' if complexity_score >= 70 else 'POOR' if complexity_score >= 60 else 'FAIL'}">
                    {complexity_score:.1f}
                </div>
                <div class="metric - status">
                    {'🟢 良好' if complexity_score >= 90 else '🟡 适中' if complexity_score >= 80 else '🟠 复杂' if complexity_score >= 70 else '🔴 过于复杂'}
                </div>
            </div>

            <div class="metric - card">
                <h3>测试覆盖率</h3>
                <div class="metric - value score-{'EXCELLENT' if coverage_pct >= 90 else 'GOOD' if coverage_pct >= 80 else 'MEDIUM' if coverage_pct >= 70 else 'POOR' if coverage_pct >= 60 else 'FAIL'}">
                    {coverage_pct:.1f}%
                </div>
                <div class="metric - status">
                    {'🟢 充分' if coverage_pct >= 90 else '🟡 良好' if coverage_pct >= 80 else '🟠 不足' if coverage_pct >= 70 else '🔴 严重不足'}
                </div>
            </div>
        </div>

        <div class="sections">
            <div class="section">
                <h2>🔍 代码质量问题</h2>
"""

        if quality and "results" in quality:
            for result in quality["results"]:
                status = result["status"]
                status_icon = "✅" if status == "PASS" else "⚠️" if status == "WARNING" else "❌"
                score = result.get("score", 0)
                html += """
                <div class="detail - item">
                    <span class="detail - label">{status_icon} {result["tool"]}</span>
                    <span class="detail - value">{score:.1f}/100</span>
                </div>
                """
        else:
            html += '<div class="detail - item"><span class="detail - label">暂无数据</span></div>'

        html += """
            </div>

            <div class="section">
                <h2>🔒 安全问题</h2>
"""

        if security and "issues" in security:
            high_count = sum(1 for i in security["issues"] if i.get("severity") == "HIGH")
            medium_count = sum(1 for i in security["issues"] if i.get("severity") == "MEDIUM")
            low_count = sum(1 for i in security["issues"] if i.get("severity") == "LOW")
            html += """
                <div class="detail - item">
                    <span class="detail - label">🔴 高危</span>
                    <span class="detail - value">{high_count}</span>
                </div>
                <div class="detail - item">
                    <span class="detail - label">🟡 中危</span>
                    <span class="detail - value">{medium_count}</span>
                </div>
                <div class="detail - item">
                    <span class="detail - label">🟢 低危</span>
                    <span class="detail - value">{low_count}</span>
                </div>
                """
        else:
            html += '<div class="detail - item"><span class="detail - label">暂无数据</span></div>'

        html += """
            </div>

            <div class="section">
                <h2>📈 复杂度分析</h2>
"""

        if complexity and "summary" in complexity:
            cc_dist = complexity["summary"].get("cyclomatic_complexity", {})
            html += """
                <div class="detail - item">
                    <span class="detail - label">A级 (简单)</span>
                    <span class="detail - value">{cc_dist.get('A', 0)}</span>
                </div>
                <div class="detail - item">
                    <span class="detail - label">B级 (适中)</span>
                    <span class="detail - value">{cc_dist.get('B', 0)}</span>
                </div>
                <div class="detail - item">
                    <span class="detail - label">C级及以上 (复杂)</span>
                    <span class="detail - value">{cc_dist.get('C', 0) + cc_dist.get('D', 0) + cc_dist.get('F', 0)}</span>
                </div>
                """
        else:
            html += '<div class="detail - item"><span class="detail - label">暂无数据</span></div>'

        html += """
            </div>

            <div class="section">
                <h2>📝 技术债务</h2>
"""

        if tech_debt and "summary" in tech_debt:
            by_priority = tech_debt["summary"].get("by_priority", {})
            html += """
                <div class="detail - item">
                    <span class="detail - label">🚨 Critical</span>
                    <span class="detail - value">{by_priority.get('CRITICAL', 0)}</span>
                </div>
                <div class="detail - item">
                    <span class="detail - label">⚠️ High</span>
                    <span class="detail - value">{by_priority.get('HIGH', 0)}</span>
                </div>
                <div class="detail - item">
                    <span class="detail - label">💡 Medium</span>
                    <span class="detail - value">{by_priority.get('MEDIUM', 0)}</span>
                </div>
                <div class="detail - item">
                    <span class="detail - label">ℹ️ Low</span>
                    <span class="detail - value">{by_priority.get('LOW', 0)}</span>
                </div>
                """
        else:
            html += '<div class="detail - item"><span class="detail - label">暂无数据</span></div>'

        html += """
            </div>
        </div>

        <div class="section" style="margin - top: 20px;">
            <h2>📊 质量趋势</h2>
            <div class="progress - bar">
                <div class="progress - fill" style="width: {overall_score:.1f}%">
                    整体健康度: {overall_score:.1f}%
                </div>
            </div>
        </div>
    </div>

    <div class="footer">
        <p>代码质量监控仪表板 | 自动更新间隔: 30秒</p>
        <p>数据来源: reports/ 目录下的最新报告</p>
    </div>

    <script>
        setTimeout(() => {{
            window.location.reload();
        }}, 30000);
    </script>
</body>
</html>
"""
        return html


class DashboardHandler(BaseHTTPRequestHandler):
    """HTTP请求处理器"""

    dashboard = None

    def do_GET(self):
        """处理GET请求"""
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content - type", "text / html; charset=utf - 8")
            self.end_headers()
            html = self.dashboard._generate_html()
            self.wfile.write(html.encode("utf - 8"))
        elif self.path == "/api / data":
            self.send_response(200)
            self.send_header("Content - type", "application / json")
            self.send_header("Access - Control - Allow - Origin", "*")
            self.end_headers()
            data = json.dumps(self.dashboard.data, indent=2, default=str)
            self.wfile.write(data.encode("utf - 8"))
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        """禁用日志输出"""
        pass


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="代码质量仪表板")
    parser.add_argument(
        "--port",
        type=int,
        default=8888,
        help="HTTP服务端口 (default: 8888)"
    )
    parser.add_argument(
        "--update - interval",
        type=int,
        default=30,
        help="数据更新间隔(秒) (default: 30)"
    )
    parser.add_argument(
        "--reports - dir",
        default="reports",
        help="报告目录 (default: reports)"
    )

    args = parser.parse_args()

    # 创建仪表板实例
    dashboard = QualityDashboard(reports_dir=args.reports_dir)
    DashboardHandler.dashboard = dashboard

    # 启动HTTP服务器
    server = HTTPServer(("0.0.0.0", args.port), DashboardHandler)

    print("=" * 70)
    print("代码质量仪表板")
    print("=" * 70)
    print(f"服务地址: http://localhost:{args.port}")
    print(f"报告目录: {args.reports_dir}")
    print(f"更新间隔: {args.update_interval}秒")
    print()
    print("访问仪表板: http://localhost:8888")
    print("按 Ctrl + C 停止服务")
    print("=" * 70)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n正在停止服务器...")
        server.shutdown()
        print("服务器已停止")


if __name__ == "__main__":
    main()

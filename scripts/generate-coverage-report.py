#!/usr/bin/env python3
"""
测试覆盖率报告生成脚本
自动生成前后端测试的覆盖率报告并合并
"""

import os
import sys
import json
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
import argparse

class CoverageReporter:
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.coverage_dir = self.project_root / "coverage"
        self.coverage_dir.mkdir(exist_ok=True)

    def generate_frontend_coverage(self):
        """生成前端覆盖率报告"""
        print("🔧 Generating frontend coverage report...")

        frontend_dir = self.project_root / "frontend"
        if not frontend_dir.exists():
            print("❌ Frontend directory not found")
            return False

        # 切换到前端目录并运行测试
        os.chdir(frontend_dir)

        try:
            # 生成覆盖率报告
            result = subprocess.run(
                ["npm", "run", "test:coverage"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                print("✅ Frontend coverage generated successfully")
                # 复制覆盖率文件到统一目录
                coverage_json = frontend_dir / "coverage" / "coverage-final.json"
                if coverage_json.exists():
                    shutil.copy2(coverage_json, self.coverage_dir / "frontend-coverage.json")
                return True
            else:
                print(f"❌ Frontend coverage failed: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Error generating frontend coverage: {e}")
            return False
        finally:
            os.chdir(self.project_root)

    def generate_backend_coverage(self):
        """生成后端覆盖率报告"""
        print("🔧 Generating backend coverage report...")

        try:
            # 生成pytest覆盖率报告
            result = subprocess.run(
                [
                    sys.executable, "-m", "pytest",
                    "--cov=src",
                    "--cov-report=json",
                    "--cov-report=html",
                    "--cov-report=term",
                    "-q"
                ],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                print("✅ Backend coverage generated successfully")
                # 移动覆盖率文件到统一目录
                if Path("coverage.json").exists():
                    shutil.move("coverage.json", self.coverage_dir / "backend-coverage.json")
                if Path("htmlcov").exists():
                    shutil.move("htmlcov", self.coverage_dir / "backend-html")
                return True
            else:
                print(f"❌ Backend coverage failed: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Error generating backend coverage: {e}")
            return False

    def merge_coverage_reports(self):
        """合并前后端覆盖率报告"""
        print("🔧 Merging coverage reports...")

        frontend_cov_file = self.coverage_dir / "frontend-coverage.json"
        backend_cov_file = self.coverage_dir / "backend-coverage.json"

        if not frontend_cov_file.exists() or not backend_cov_file.exists():
            print("❌ Coverage files not found")
            return False

        try:
            with open(frontend_cov_file) as f:
                frontend_cov = json.load(f)
            with open(backend_cov_file) as f:
                backend_cov = json.load(f)

            # 合并覆盖率数据
            merged = self.merge_coverage_data(frontend_cov, backend_cov)

            # 保存合并后的报告
            merged_file = self.coverage_dir / "merged-coverage.json"
            with open(merged_file, 'w') as f:
                json.dump(merged, f, indent=2)

            # 生成HTML报告
            self.generate_html_report(merged)

            print(f"✅ Coverage merged successfully")
            print(f"📊 Total coverage: {merged['summary']['total']['pct']}%")

            return True

        except Exception as e:
            print(f"❌ Error merging coverage: {e}")
            return False

    def merge_coverage_data(self, frontend_cov, backend_cov):
        """合并前端和后端的覆盖率数据"""
        merged = {
            "summary": {
                "total": {"covered": 0, "total": 0, "pct": 0},
                "frontend": {"covered": 0, "total": 0, "pct": 0},
                "backend": {"covered": 0, "total": 0, "pct": 0}
            },
            "files": {},
            "timestamp": datetime.now().isoformat()
        }

        # 处理前端覆盖率
        if "total" in frontend_cov:
            merged["summary"]["frontend"]["total"] = frontend_cov["total"]["lines"]
            merged["summary"]["frontend"]["covered"] = frontend_cov["total"]["coveredLines"]
            merged["summary"]["frontend"]["pct"] = frontend_cov["total"]["lines"]["pct"]

        # 处理后端覆盖率
        if "totals" in backend_cov:
            merged["summary"]["backend"]["total"] = backend_cov["totals"]["num_statements"]
            merged["summary"]["backend"]["covered"] = backend_cov["totals"]["covered_statements"]
            merged["summary"]["backend"]["pct"] = backend_cov["totals"]["percent_covered"]

        # 计算总体覆盖率
        total_statements = merged["summary"]["frontend"]["total"] + merged["summary"]["backend"]["total"]
        total_covered = merged["summary"]["frontend"]["covered"] + merged["summary"]["backend"]["covered"]

        merged["summary"]["total"]["total"] = total_statements
        merged["summary"]["total"]["covered"] = total_covered
        merged["summary"]["total"]["pct"] = round(
            (total_covered / total_statements * 100) if total_statements > 0 else 0, 2
        )

        # 合并文件级别的覆盖率
        merged["files"]["frontend"] = frontend_cov.get("files", {})
        merged["files"]["backend"] = backend_cov.get("files", {})

        return merged

    def generate_html_report(self, merged_data):
        """生成HTML格式的覆盖率报告"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>CBSC 测试覆盖率报告</title>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .metric {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 6px;
            text-align: center;
        }}
        .metric-value {{
            font-size: 36px;
            font-weight: bold;
            margin: 10px 0;
        }}
        .metric-label {{
            color: #6c757d;
            font-size: 14px;
        }}
        .progress-bar {{
            width: 100%;
            height: 20px;
            background: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #28a745, #20c997);
            transition: width 0.3s ease;
        }}
        .good {{ color: #28a745; }}
        .warning {{ color: #ffc107; }}
        .danger {{ color: #dc3545; }}
        .timestamp {{
            color: #6c757d;
            font-size: 12px;
            text-align: right;
            margin-top: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 30px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: 600;
        }}
        .badge {{
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 CBSC 量化交易策略管理系统 - 测试覆盖率报告</h1>

        <div class="summary">
            <div class="metric">
                <div class="metric-label">总体覆盖率</div>
                <div class="metric-value {self.get_coverage_class(merged_data['summary']['total']['pct'])}">
                    {merged_data['summary']['total']['pct']}%
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {merged_data['summary']['total']['pct']}%"></div>
                </div>
            </div>

            <div class="metric">
                <div class="metric-label">前端覆盖率</div>
                <div class="metric-value {self.get_coverage_class(merged_data['summary']['frontend']['pct'])}">
                    {merged_data['summary']['frontend']['pct']}%
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {merged_data['summary']['frontend']['pct']}%"></div>
                </div>
            </div>

            <div class="metric">
                <div class="metric-label">后端覆盖率</div>
                <div class="metric-value {self.get_coverage_class(merged_data['summary']['backend']['pct'])}">
                    {merged_data['summary']['backend']['pct']}%
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {merged_data['summary']['backend']['pct']}%"></div>
                </div>
            </div>
        </div>

        <table>
            <thead>
                <tr>
                    <th>模块</th>
                    <th>覆盖率</th>
                    <th>状态</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>总覆盖率</td>
                    <td>{merged_data['summary']['total']['pct']}%</td>
                    <td><span class="badge {self.get_coverage_class(merged_data['summary']['total']['pct'])}">{self.get_status(merged_data['summary']['total']['pct'])}</span></td>
                </tr>
                <tr>
                    <td>前端 (React/TypeScript)</td>
                    <td>{merged_data['summary']['frontend']['pct']}%</td>
                    <td><span class="badge {self.get_coverage_class(merged_data['summary']['frontend']['pct'])}">{self.get_status(merged_data['summary']['frontend']['pct'])}</span></td>
                </tr>
                <tr>
                    <td>后端 (Python/FastAPI)</td>
                    <td>{merged_data['summary']['backend']['pct']}%</td>
                    <td><span class="badge {self.get_coverage_class(merged_data['summary']['backend']['pct'])}">{self.get_status(merged_data['summary']['backend']['pct'])}</span></td>
                </tr>
            </tbody>
        </table>

        <div class="timestamp">
            生成时间: {merged_data['timestamp']}
        </div>
    </div>
</body>
</html>
"""

        html_file = self.coverage_dir / "coverage-report.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def get_coverage_class(self, pct):
        """根据覆盖率返回CSS类"""
        if pct >= 80:
            return "good"
        elif pct >= 60:
            return "warning"
        else:
            return "danger"

    def get_status(self, pct):
        """根据覆盖率返回状态"""
        if pct >= 80:
            return "✅ 优秀"
        elif pct >= 60:
            return "⚠️ 良好"
        else:
            return "❌ 需改进"

    def check_coverage_thresholds(self):
        """检查覆盖率是否达到阈值"""
        merged_file = self.coverage_dir / "merged-coverage.json"
        if not merged_file.exists():
            return False

        with open(merged_file) as f:
            data = json.load(f)

        thresholds = {
            "total": 80,
            "frontend": 80,
            "backend": 80
        }

        all_passed = True
        for module, threshold in thresholds.items():
            coverage = data["summary"][module]["pct"]
            if coverage < threshold:
                print(f"❌ {module} coverage ({coverage}%) is below threshold ({threshold}%)")
                all_passed = False
            else:
                print(f"✅ {module} coverage ({coverage}%) meets threshold ({threshold}%)")

        return all_passed

    def generate_report(self, frontend=True, backend=True, merge=True):
        """生成完整的覆盖率报告"""
        print(f"\n{'='*60}")
        print("🚀 开始生成测试覆盖率报告")
        print(f"{'='*60}\n")

        success = True

        if frontend:
            success &= self.generate_frontend_coverage()

        if backend:
            success &= self.generate_backend_coverage()

        if merge and frontend and backend:
            success &= self.merge_coverage_reports()
            self.check_coverage_thresholds()

        if success:
            print(f"\n✅ 覆盖率报告生成完成!")
            print(f"📁 报告位置: {self.coverage_dir.absolute()}")
            print(f"🌐 HTML报告: {self.coverage_dir / 'coverage-report.html'}")
        else:
            print(f"\n❌ 部分报告生成失败，请检查错误信息")
            return False

        return True


def main():
    parser = argparse.ArgumentParser(description="生成测试覆盖率报告")
    parser.add_argument("--frontend", action="store_true", default=True, help="生成前端覆盖率")
    parser.add_argument("--backend", action="store_true", default=True, help="生成后端覆盖率")
    parser.add_argument("--merge", action="store_true", default=True, help="合并覆盖率报告")
    parser.add_argument("--no-frontend", dest="frontend", action="store_false", help="跳过前端覆盖率")
    parser.add_argument("--no-backend", dest="backend", action="store_false", help="跳过后端覆盖率")
    parser.add_argument("--no-merge", dest="merge", action="store_false", help="不合并报告")

    args = parser.parse_args()

    # 获取项目根目录
    project_root = Path(__file__).parent.parent

    # 创建报告生成器
    reporter = CoverageReporter(project_root)

    # 生成报告
    success = reporter.generate_report(
        frontend=args.frontend,
        backend=args.backend,
        merge=args.merge
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
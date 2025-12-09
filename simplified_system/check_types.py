#!/usr/bin/env python3
"""
Phase 3 Automated Type Checking Script
Phase 3 自動化類型檢查腳本
運行mypy檢查並生成詳細報告
"""

import subprocess
import sys
import os
from pathlib import Path
from typing import List, Dict, Any
import json
from datetime import datetime

class TypeChecker:
    """自動化類型檢查器"""

    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent
        self.mypy_config = self.project_root / "mypy.ini"
        self.src_dir = self.project_root / "src" / "realtime"
        self.reports_dir = self.project_root / "type_reports"
        self.reports_dir.mkdir(exist_ok=True)

    def run_mypy_check(self) -> Dict[str, Any]:
        """運行mypy檢查"""
        print("🔍 Running Mypy Type Checking...")
        print("=" * 60)

        # 檢查mypy是否可用
        try:
            subprocess.run([sys.executable, "-m", "mypy", "--version"],
                         capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Mypy not found. Installing...")
            subprocess.run([sys.executable, "-m", "pip", "install", "mypy"],
                         check=True)

        # 構建mypy命令
        cmd = [
            sys.executable, "-m", "mypy",
            "--config-file", str(self.mypy_config),
            "--html-report", str(self.reports_dir / "html_report"),
            "--junit-xml", str(self.reports_dir / "junit_report.xml"),
            str(self.src_dir)
        ]

        print(f"Command: {' '.join(cmd)}")
        print()

        # 運行mypy
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root
            )

            # 解析結果
            return self.parse_mypy_output(result.stdout, result.stderr, result.returncode)

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": "",
                "return_code": 1
            }

    def parse_mypy_output(self, stdout: str, stderr: str, return_code: int) -> Dict[str, Any]:
        """解析mypy輸出"""
        lines = stdout.split('\n')
        errors = []
        warnings = []
        notes = []

        for line in lines:
            if not line.strip():
                continue

            if line.startswith('error:'):
                errors.append(line)
            elif line.startswith('warning:'):
                warnings.append(line)
            elif line.startswith('note:'):
                notes.append(line)
            elif '.py:' in line and any(keyword in line for keyword in ['error', 'warning']):
                # 解析錯誤位置和消息
                if 'error:' in line:
                    errors.append(line)
                elif 'warning:' in line:
                    warnings.append(line)

        return {
            "success": return_code == 0,
            "return_code": return_code,
            "errors": errors,
            "warnings": warnings,
            "notes": notes,
            "stdout": stdout,
            "stderr": stderr
        }

    def generate_report(self, mypy_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成詳細報告"""
        timestamp = datetime.now().isoformat()

        report = {
            "timestamp": timestamp,
            "project_root": str(self.project_root),
            "summary": {
                "success": mypy_results["success"],
                "total_errors": len(mypy_results["errors"]),
                "total_warnings": len(mypy_results["warnings"]),
                "return_code": mypy_results["return_code"]
            },
            "details": mypy_results,
            "files_analyzed": self.get_analyzed_files(),
            "recommendations": self.generate_recommendations(mypy_results)
        }

        # 保存JSON報告
        report_file = self.reports_dir / f"type_check_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        return report

    def get_analyzed_files(self) -> List[str]:
        """獲取分析的文件列表"""
        files = []
        if self.src_dir.exists():
            for py_file in self.src_dir.rglob("*.py"):
                if not py_file.name.startswith('__'):
                    files.append(str(py_file.relative_to(self.project_root)))
        return sorted(files)

    def generate_recommendations(self, mypy_results: Dict[str, Any]) -> List[str]:
        """生成改進建議"""
        recommendations = []

        if not mypy_results["success"]:
            recommendations.append(
                "🔧 Fix all type errors before proceeding to production"
            )

        if mypy_results["errors"]:
            recommendations.append(
                f"📝 Add missing type annotations for {len(mypy_results['errors'])} errors"
            )

        if mypy_results["warnings"]:
            recommendations.append(
                f"⚠️ Review and address {len(mypy_results['warnings'])} warnings"
            )

        # 基於具體錯誤類型的建議
        error_text = ' '.join(mypy_results["errors"] + mypy_results["warnings"])

        if "Argument 1 has incompatible type" in error_text:
            recommendations.append(
                "🔄 Review function argument types and return types"
            )

        if "missing return statement" in error_text:
            recommendations.append(
                "📄 Add return statements or annotate with -> None"
            )

        if "has no attribute" in error_text:
            recommendations.append(
                "🏗️ Review class attribute definitions and type annotations"
            )

        if "Module has no attribute" in error_text:
            recommendations.append(
                "📦 Check import statements and module availability"
            )

        return recommendations

    def print_summary(self, report: Dict[str, Any]) -> None:
        """打印測試摘要"""
        print("\n" + "=" * 60)
        print("📊 Phase 3 Type Check Summary")
        print("=" * 60)

        summary = report["summary"]

        print(f"Status: {'✅ PASSED' if summary['success'] else '❌ FAILED'}")
        print(f"Errors: {summary['total_errors']}")
        print(f"Warnings: {summary['total_warnings']}")
        print(f"Return Code: {summary['return_code']}")
        print(f"Files Analyzed: {len(report['files_analyzed'])}")

        if summary['total_errors'] > 0:
            print(f"\n❌ Errors ({summary['total_errors']}):")
            for i, error in enumerate(report['details']['errors'][:10], 1):  # Show first 10
                print(f"  {i}. {error}")
            if len(report['details']['errors']) > 10:
                print(f"  ... and {len(report['details']['errors']) - 10} more")

        if summary['total_warnings'] > 0:
            print(f"\n⚠️ Warnings ({summary['total_warnings']}):")
            for i, warning in enumerate(report['details']['warnings'][:5], 1):  # Show first 5
                print(f"  {i}. {warning}")
            if len(report['details']['warnings']) > 5:
                print(f"  ... and {len(report['details']['warnings']) - 5} more")

        if report['recommendations']:
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"  {i}. {rec}")

        print(f"\n📁 Detailed reports saved to: {self.reports_dir}")
        print("=" * 60)

    def run_integration_test(self) -> bool:
        """運行集成測試"""
        print("\n🧪 Running Type Safety Integration Test...")

        test_file = self.src_dir / "test_type_safety.py"
        if test_file.exists():
            try:
                result = subprocess.run(
                    [sys.executable, str(test_file)],
                    capture_output=True,
                    text=True,
                    cwd=self.project_root
                )

                if result.returncode == 0:
                    print("✅ Type safety integration test passed")
                    return True
                else:
                    print("❌ Type safety integration test failed")
                    print("STDOUT:", result.stdout)
                    print("STDERR:", result.stderr)
                    return False
            except Exception as e:
                print(f"❌ Failed to run integration test: {e}")
                return False
        else:
            print("⚠️ Type safety integration test not found")
            return True  # Don't fail if test doesn't exist

def main():
    """主函數"""
    print("🚀 Phase 3 Automated Type Checking")
    print("=" * 60)

    checker = TypeChecker()

    # 運行mypy檢查
    mypy_results = checker.run_mypy_check()

    # 生成報告
    report = checker.generate_report(mypy_results)

    # 打印摘要
    checker.print_summary(report)

    # 運行集成測試
    integration_passed = checker.run_integration_test()

    # 最終結果
    overall_success = report["summary"]["success"] and integration_passed

    if overall_success:
        print("\n🎉 Type checking completed successfully!")
        print("✅ Phase 3 type safety improvements are working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Type checking failed!")
        print("🔧 Please address the issues above before proceeding.")
        sys.exit(1)

if __name__ == "__main__":
    main()
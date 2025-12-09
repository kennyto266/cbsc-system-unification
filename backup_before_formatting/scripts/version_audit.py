#!/usr / bin / env python3
"""
版本审计脚本 - 生成详细的版本报告
Version Audit Script - Generate Detailed Version Report

此脚本检查系统中所有组件的版本状态，生成完整的审计报告，
包括版本一致性检查、依赖分析、安全评估等。

使用方法:
python scripts / version_audit.py [--report - format=json|markdown|html] [--output=filename]
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

# 添加src目录到路径
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root / "src"))

try:
    from version import get_version_manager, VersionInfo
except ImportError:
    print("❌ 无法导入版本管理模块")
    sys.exit(1)


@dataclass
class VersionAuditResult:
    """版本审计结果"""
    timestamp: str
    project_root: str
    target_version: str
    version_info: Dict
    consistency_check: Dict
    dependency_analysis: Dict
    security_assessment: Dict
    recommendations: List[str]
    summary: Dict


class VersionAuditor:
    """版本审计器"""

    def __init__(self):
        """初始化审计器"""
        self.version_manager = get_version_manager()
        self.project_root = self.version_manager.project_root

    def run_full_audit(self) -> VersionAuditResult:
        """运行完整的版本审计"""
        print("🔍 开始版本审计...")
        print(f"📋 项目根目录: {self.project_root}")

        # 执行各项审计检查
        version_info = self.version_manager.get_build_info()
        consistency_check = self._check_version_consistency()
        dependency_analysis = self._analyze_dependencies()
        security_assessment = self._assess_security()
        recommendations = self._generate_recommendations(consistency_check, dependency_analysis, security_assessment)
        summary = self._generate_summary(consistency_check, dependency_analysis, security_assessment)

        result = VersionAuditResult(
            timestamp=datetime.now().isoformat(),
            project_root=str(self.project_root),
            target_version=self.version_manager.get_current_version(),
            version_info=version_info,
            consistency_check=consistency_check,
            dependency_analysis=dependency_analysis,
            security_assessment=security_assessment,
            recommendations=recommendations,
            summary=summary
        )

        print("✅ 版本审计完成")
        return result

    def _check_version_consistency(self) -> Dict:
        """检查版本一致性"""
        print("   🔎 检查版本一致性...")

        issues = self.version_manager.check_version_consistency()

        # 添加更多检查项
        additional_checks = self._perform_additional_consistency_checks()
        issues.update(additional_checks)

        return issues

    def _perform_additional_consistency_checks(self) -> Dict:
        """执行额外的一致性检查"""
        additional = {
            "git_tag_mismatch": [],
            "docker_version_mismatch": [],
            "documentation_mismatch": []
        }

        # 检查Git标签
        current_version = self.version_manager.get_current_version()
        git_tag = self._get_current_git_tag()
        if git_tag and git_tag != f"v{current_version}":
            additional["git_tag_mismatch"].append({
                "git_tag": git_tag,
                "expected": f"v{current_version}",
                "file": "Git Repository"
            })

        # 检查Docker文件
        docker_files = ["Dockerfile", "docker - compose.yml"]
        for docker_file in docker_files:
            full_path = self.project_root / docker_file
            if full_path.exists():
                docker_version = self._extract_docker_version(full_path)
                if docker_version and docker_version != current_version:
                    additional["docker_version_mismatch"].append({
                        "file": docker_file,
                        "docker_version": docker_version,
                        "expected": current_version
                    })

        # 检查文档文件
        doc_files = ["README.md", "docs / README.md"]
        for doc_file in doc_files:
            full_path = self.project_root / doc_file
            if full_path.exists():
                doc_versions = self._extract_documentation_versions(full_path)
                for doc_version_info in doc_versions:
                    if doc_version_info["version"] != current_version:
                        additional["documentation_mismatch"].append({
                            "file": doc_file,
                            "context": doc_version_info["context"],
                            "doc_version": doc_version_info["version"],
                            "expected": current_version
                        })

        return additional

    def _get_current_git_tag(self) -> Optional[str]:
        """获取当前Git标签"""
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'describe', '--tags', '--abbrev=0'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None

    def _extract_docker_version(self, docker_file: Path) -> Optional[str]:
        """从Docker文件中提取版本"""
        try:
            with open(docker_file, 'r', encoding='utf - 8') as f:
                content = f.read()

            import re
            # 查找常见的版本模式
            patterns = [
                r'VERSION\s*=\s*["\']([^"\']+)["\']',
                r'ENV\s + VERSION\s*["\']?([^"\'\s]+)["\']?',
                r'label\s + version\s*=\s*["\']([^"\']+)["\']',
            ]

            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    return match.group(1)
        except Exception:
            pass
        return None

    def _extract_documentation_versions(self, doc_file: Path) -> List[Dict]:
        """从文档文件中提取版本信息"""
        versions = []
        try:
            with open(doc_file, 'r', encoding='utf - 8') as f:
                content = f.read()

            import re
            # 查找文档中的版本引用
            patterns = [
                (r'版本[:\s]+([0 - 9]+\.[0 - 9]+\.[0 - 9]+)', "文档版本"),
                (r'version[:\s]+([0 - 9]+\.[0 - 9]+\.[0 - 9]+)', "英文版本"),
                (r'v([0 - 9]+\.[0 - 9]+\.[0 - 9]+)', "版本标签"),
            ]

            for pattern, context in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    versions.append({
                        "version": match.group(1),
                        "context": context,
                        "line": content[:match.start()].count('\n') + 1
                    })
        except Exception:
            pass
        return versions

    def _analyze_dependencies(self) -> Dict:
        """分析依赖关系"""
        print("   🔍 分析依赖关系...")

        analysis = {
            "python_dependencies": self._analyze_python_dependencies(),
            "frontend_dependencies": self._analyze_frontend_dependencies(),
            "system_dependencies": self._analyze_system_dependencies(),
            "circular_dependencies": [],
            "outdated_dependencies": []
        }

        # 检查循环依赖
        analysis["circular_dependencies"] = self._check_circular_dependencies()

        # 检查过时依赖
        analysis["outdated_dependencies"] = self._check_outdated_dependencies()

        return analysis

    def _analyze_python_dependencies(self) -> Dict:
        """分析Python依赖"""
        python_files = [
            "requirements.txt",
            "pyproject.toml",
            "setup.py",
        ]

        dependencies = {}
        for file_path in python_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    if file_path == "requirements.txt":
                        deps = self._parse_requirements_txt(full_path)
                    elif file_path == "pyproject.toml":
                        deps = self._parse_pyproject_toml(full_path)
                    elif file_path == "setup.py":
                        deps = self._parse_setup_py(full_path)
                    else:
                        deps = {}

                    dependencies[file_path] = {
                        "count": len(deps),
                        "dependencies": deps,
                        "last_modified": datetime.fromtimestamp(full_path.stat().st_mtime).isoformat()
                    }
                except Exception as e:
                    dependencies[file_path] = {
                        "error": str(e),
                        "count": 0,
                        "dependencies": []
                    }

        return dependencies

    def _parse_requirements_txt(self, file_path: Path) -> List[Dict]:
        """解析requirements.txt文件"""
        dependencies = []
        try:
            with open(file_path, 'r', encoding='utf - 8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # 解析依赖格式: package>=1.0.0
                        parts = line.split('>=') if '>=' in line else line.split('==') if '==' in line else [line]
                        dependencies.append({
                            "name": parts[0].strip(),
                            "version_constraint": parts[1].strip() if len(parts) > 1 else None,
                            "line": line_num
                        })
        except Exception:
            pass
        return dependencies

    def _parse_pyproject_toml(self, file_path: Path) -> List[Dict]:
        """解析pyproject.toml文件"""
        dependencies = []
        try:
            # 简单的TOML解析
            with open(file_path, 'r', encoding='utf - 8') as f:
                content = f.read()

            import re
            # 查找dependencies部分
            deps_section = re.search(r'dependencies\s*=\s*\[(.*?)\]', content, re.DOTALL)
            if deps_section:
                deps_content = deps_section.group(1)
                # 提取每个依赖
                for match in re.finditer(r'"([^"]+)"', deps_content):
                    dep_str = match.group(1)
                    parts = dep_str.split('>=') if '>=' in dep_str else dep_str.split('==') if '==' in dep_str else [dep_str]
                    dependencies.append({
                        "name": parts[0].strip(),
                        "version_constraint": parts[1].strip() if len(parts) > 1 else None
                    })
        except Exception:
            pass
        return dependencies

    def _parse_setup_py(self, file_path: Path) -> List[Dict]:
        """解析setup.py文件"""
        dependencies = []
        try:
            with open(file_path, 'r', encoding='utf - 8') as f:
                content = f.read()

            import re
            # 查找install_requires
            install_requires = re.search(r'install_requires\s*=\s*\[(.*?)\]', content, re.DOTALL)
            if install_requires:
                req_content = install_requires.group(1)
                for match in re.finditer(r'"([^"]+)"', req_content):
                    dep_str = match.group(1)
                    parts = dep_str.split('>=') if '>=' in dep_str else dep_str.split('==') if '==' in dep_str else [dep_str]
                    dependencies.append({
                        "name": parts[0].strip(),
                        "version_constraint": parts[1].strip() if len(parts) > 1 else None
                    })
        except Exception:
            pass
        return dependencies

    def _analyze_frontend_dependencies(self) -> Dict:
        """分析前端依赖"""
        frontend_files = [
            "frontend / package.json",
            "frontend_old / package.json",
        ]

        dependencies = {}
        for file_path in frontend_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf - 8') as f:
                        package_data = json.load(f)

                    dependencies[file_path] = {
                        "dependencies": package_data.get("dependencies", {}),
                        "dev_dependencies": package_data.get("devDependencies", {}),
                        "last_modified": datetime.fromtimestamp(full_path.stat().st_mtime).isoformat()
                    }
                except Exception as e:
                    dependencies[file_path] = {"error": str(e)}

        return dependencies

    def _analyze_system_dependencies(self) -> Dict:
        """分析系统级依赖"""
        system_deps = {
            "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
            "platform": os.name,
            "architecture": os.uname().machine if hasattr(os, 'uname') else "unknown",
            "required_tools": ["git", "docker", "node", "npm"],
            "tool_status": {}
        }

        # 检查工具状态
        import shutil
        for tool in system_deps["required_tools"]:
            system_deps["tool_status"][tool] = {
                "available": shutil.which(tool) is not None,
                "path": shutil.which(tool)
            }

        return system_deps

    def _check_circular_dependencies(self) -> List[Dict]:
        """检查循环依赖（简化版本）"""
        # 这里可以实现更复杂的循环依赖检测
        # 目前返回空列表，实际项目中可能需要静态分析工具
        return []

    def _check_outdated_dependencies(self) -> List[Dict]:
        """检查过时依赖（简化版本）"""
        # 这里可以实现依赖版本检查
        # 目前返回空列表，实际项目中可能需要调用package registry API
        return []

    def _assess_security(self) -> Dict:
        """评估安全性"""
        print("   🔍 评估安全性...")

        security_issues = {
            "version_security": self._check_version_security(),
            "dependency_vulnerabilities": self._check_dependency_vulnerabilities(),
            "configuration_security": self._check_configuration_security(),
            "file_permissions": self._check_file_permissions()
        }

        return security_issues

    def _check_version_security(self) -> List[Dict]:
        """检查版本安全性"""
        issues = []
        version_info = self.version_manager.get_version_info()

        # 检查是否为开发版本
        if version_info.prerelease:
            issues.append({
                "type": "development_version",
                "severity": "medium",
                "description": f"使用预发布版本: {version_info.prerelease}",
                "recommendation": "生产环境应使用正式发布版本"
            })

        # 检查版本号是否过旧
        if version_info.minor < 1:
            issues.append({
                "type": "outdated_major_version",
                "severity": "high",
                "description": f"主版本号过低: {version_info.major}.{version_info.minor}",
                "recommendation": "考虑升级到最新的主版本"
            })

        return issues

    def _check_dependency_vulnerabilities(self) -> List[Dict]:
        """检查依赖漏洞（简化版本）"""
        # 这里可以实现已知漏洞检查
        # 目前返回常见的安全建议
        return [
            {
                "type": "general_recommendation",
                "severity": "info",
                "description": "定期更新依赖包以修复已知漏洞",
                "recommendation": "使用 `pip - audit` 或 `safety` 检查依赖漏洞"
            }
        ]

    def _check_configuration_security(self) -> List[Dict]:
        """检查配置安全性"""
        issues = []
        config_files = [
            ".env",
            "config.json",
            "secrets.json"
        ]

        for config_file in config_files:
            config_path = self.project_root / config_file
            if config_path.exists():
                # 检查文件权限
                stat_info = config_path.stat()
                mode = oct(stat_info.st_mode)[-3:]

                if mode != "600":  # 只有所有者可读写
                    issues.append({
                        "type": "file_permissions",
                        "severity": "high",
                        "file": config_file,
                        "current_permissions": mode,
                        "description": f"配置文件权限过于宽松: {mode}",
                        "recommendation": "设置为600 (仅所有者可读写)"
                    })

        return issues

    def _check_file_permissions(self) -> Dict:
        """检查关键文件权限"""
        critical_files = [
            "VERSION",
            "src / version.py",
            "scripts / sync_versions.py"
        ]

        permissions = {}
        for file_path in critical_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                stat_info = full_path.stat()
                permissions[file_path] = {
                    "mode": oct(stat_info.st_mode)[-3:],
                    "owner": stat_info.st_uid,
                    "group": stat_info.st_gid,
                    "writable_by_others": bool(stat_info.st_mode & 0o002)
                }

        return permissions

    def _generate_recommendations(self, consistency: Dict, dependencies: Dict, security: Dict) -> List[str]:
        """生成改进建议"""
        recommendations = []

        # 基于一致性检查的建议
        if any(consistency.values()):
            recommendations.append("📋 发现版本不一致问题，请运行 `python scripts / sync_versions.py` 进行修复")

        # 基于依赖分析的建议
        total_python_deps = sum(
            deps.get("count", 0) for deps in dependencies.get("python_dependencies", {}).values()
        )
        if total_python_deps > 100:
            recommendations.append("📦 Python依赖数量较多，考虑定期清理未使用的依赖")

        # 基于安全评估的建议
        security_issues = sum(len(issues) for issues in security.values() if isinstance(issues, list))
        if security_issues > 0:
            recommendations.append("🔒 发现安全问题，请查看详细报告并及时修复")

        # 通用建议
        recommendations.extend([
            "🔄 定期运行版本审计以确保系统健康",
            "📝 在发布新版本前运行完整的版本检查",
            "🏷️  使用Git标签标记重要的发布版本"
        ])

        return recommendations

    def _generate_summary(self, consistency: Dict, dependencies: Dict, security: Dict) -> Dict:
        """生成摘要信息"""
        return {
            "version_consistency_score": self._calculate_consistency_score(consistency),
            "dependency_health_score": self._calculate_dependency_score(dependencies),
            "security_score": self._calculate_security_score(security),
            "overall_health": "good"  # 可以基于各分数计算
        }

    def _calculate_consistency_score(self, consistency: Dict) -> str:
        """计算一致性评分"""
        total_issues = sum(len(issues) if isinstance(issues, list) else (1 if issues else 0)
                          for issues in consistency.values())

        if total_issues == 0:
            return "excellent"
        elif total_issues <= 3:
            return "good"
        elif total_issues <= 7:
            return "fair"
        else:
            return "poor"

    def _calculate_dependency_score(self, dependencies: Dict) -> str:
        """计算依赖健康评分"""
        # 简化的评分逻辑
        total_deps = sum(
            deps.get("count", 0) for deps in dependencies.get("python_dependencies", {}).values()
        )

        if total_deps < 20:
            return "excellent"
        elif total_deps < 50:
            return "good"
        elif total_deps < 100:
            return "fair"
        else:
            return "poor"

    def _calculate_security_score(self, security: Dict) -> str:
        """计算安全评分"""
        total_issues = sum(len(issues) if isinstance(issues, list) else 0 for issues in security.values())

        if total_issues == 0:
            return "excellent"
        elif total_issues <= 2:
            return "good"
        elif total_issues <= 5:
            return "fair"
        else:
            return "poor"


def format_report(result: VersionAuditResult, format_type: str = "markdown") -> str:
    """格式化审计报告"""
    if format_type == "json":
        return json.dumps(asdict(result), indent=2, ensure_ascii=False)

    elif format_type == "markdown":
        return """
# 香港量化交易系统 - 版本审计报告
# Hong Kong Quantitative Trading System - Version Audit Report

**审计时间:** {result.timestamp}
**项目根目录:** {result.project_root}
**目标版本:** {result.target_version}

## 📊 执行摘要

| 指标 | 状态 | 分数 |
|------|------|------|
| 版本一致性 | {result.summary['version_consistency_score'].upper()} |
| 依赖健康度 | {result.summary['dependency_health_score'].upper()} |
| 安全状况 | {result.summary['security_score'].upper()} |
| 整体健康度 | {result.summary['overall_health'].upper()} |

## 🔄 版本一致性检查

### 检查结果
- 版本不匹配: {len(result.consistency_check.get('version_mismatches', []))}
- 缺少版本信息: {len(result.consistency_check.get('missing_versions', []))}
- 解析错误: {len(result.consistency_check.get('parse_errors', []))}

### 详细问题
{json.dumps(result.consistency_check, indent=2, ensure_ascii=False)}

## 📦 依赖分析

### Python依赖
{json.dumps(result.dependency_analysis.get('python_dependencies', {}), indent=2, ensure_ascii=False)}

### 前端依赖
{json.dumps(result.dependency_analysis.get('frontend_dependencies', {}), indent=2, ensure_ascii=False)}

## 🔒 安全评估

### 安全问题
{json.dumps(result.security_assessment, indent=2, ensure_ascii=False)}

## 💡 改进建议

{chr(10).join(f"- {rec}" for rec in result.recommendations)}

## 📋 详细构建信息

{json.dumps(result.version_info, indent=2, ensure_ascii=False)}
"""

    else:  # HTML format
        return """
<!DOCTYPE html>
<html>
<head>
    <title>版本审计报告 - {result.target_version}</title>
    <style>
        body {{ font - family: Arial, sans - serif; margin: 40px; }}
        .header {{ background - color: #f8f9fa; padding: 20px; border - radius: 5px; }}
        .section {{ margin: 20px 0; }}
        .good {{ color: green; }}
        .warning {{ color: orange; }}
        .error {{ color: red; }}
        pre {{ background - color: #f5f5f5; padding: 10px; border - radius: 3px; overflow - x: auto; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>香港量化交易系统 - 版本审计报告</h1>
        <p><strong>审计时间:</strong> {result.timestamp}</p>
        <p><strong>项目根目录:</strong> {result.project_root}</p>
        <p><strong>目标版本:</strong> {result.target_version}</p>
    </div>

    <div class="section">
        <h2>执行摘要</h2>
        <ul>
            <li>版本一致性: {result.summary['version_consistency_score']}</li>
            <li>依赖健康度: {result.summary['dependency_health_score']}</li>
            <li>安全状况: {result.summary['security_score']}</li>
        </ul>
    </div>

    <div class="section">
        <h2>改进建议</h2>
        <ul>
            {"".join(f"<li>{rec}</li>" for rec in result.recommendations)}
        </ul>
    </div>

    <div class="section">
        <h2>详细信息</h2>
        <pre>{json.dumps(asdict(result), indent=2, ensure_ascii=False)}</pre>
    </div>
</body>
</html>
"""


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="版本审计工具")
    parser.add_argument("--report - format", choices=["json", "markdown", "html"],
                       default="markdown", help="报告格式")
    parser.add_argument("--output", help="输出文件路径")
    parser.add_argument("--version", action="version",
                       version=f"版本审计工具 v{get_version_manager().get_current_version()}")

    args = parser.parse_args()

    # 运行审计
    auditor = VersionAuditor()
    result = auditor.run_full_audit()

    # 生成报告
    report = format_report(result, args.report_format)

    # 输出报告
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w', encoding='utf - 8') as f:
            f.write(report)
        print(f"📄 报告已保存到: {output_path}")
    else:
        print("\n" + report)


if __name__ == "__main__":
    main()
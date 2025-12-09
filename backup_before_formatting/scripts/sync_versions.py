#!/usr / bin / env python3
"""
版本同步脚本 - 统一所有组件版本号
Version Sync Script - Unify All Component Version Numbers

此脚本将系统中所有组件的版本号统一到VERSION文件中的版本。
支持Python模块、前端包、配置文件等的版本同步。

使用方法:
python scripts / sync_versions.py [--check] [--dry - run]
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# 添加src目录到路径
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root / "src"))

try:
    from version import get_version_manager, VersionInfo
except ImportError:
    print("❌ 无法导入版本管理模块，请检查src / version.py是否存在")
    sys.exit(1)


class VersionSync:
    """版本同步器"""

    def __init__(self, dry_run: bool = False):
        """初始化同步器

        Args:
            dry_run: 是否为试运行模式（不实际修改文件）
        """
        self.dry_run = dry_run
        self.version_manager = get_version_manager()
        self.target_version = self.version_manager.get_current_version()
        self.target_version_info = self.version_manager.get_version_info()

        # 统计信息
        self.stats = {
            "updated": 0,
            "skipped": 0,
            "errors": 0,
            "total": 0
        }

    def sync_all(self) -> Dict:
        """同步所有组件版本"""
        print("🚀 开始版本同步")
        print(f"📋 目标版本: {self.target_version}")
        print(f"📍 项目根目录: {self.version_manager.project_root}")

        if self.dry_run:
            print("🧪 试运行模式 - 不会实际修改文件")

        print("-" * 60)

        # 同步不同类型的文件
        sync_groups = [
            ("Python模块", self._sync_python_modules),
            ("前端包", self._sync_frontend_packages),
            ("Python项目配置", self._sync_python_projects),
            ("其他配置文件", self._sync_other_configs),
        ]

        for group_name, sync_func in sync_groups:
            print(f"\n📦 同步 {group_name}:")
            sync_func()

        # 生成报告
        print("\n" + "=" * 60)
        print("📊 版本同步完成")
        self._print_summary()

        return self.stats

    def _sync_python_modules(self):
        """同步Python模块版本"""
        python_files = [
            "src / __init__.py",
            "backend / __init__.py",
            "shared / __init__.py",
            "codex / src / __init__.py",
        ]

        patterns = [
            # __version__ = "x.x.x"
            (r'__version__\s*=\s*["\']([^"\']+)["\']', '__version__ = "{}"'),
            # version = "x.x.x"
            (r'version\s*=\s*["\']([^"\']+)["\']', 'version = "{}"'),
        ]

        for file_path in python_files:
            self._sync_file(file_path, patterns, "Python模块")

    def _sync_frontend_packages(self):
        """同步前端包版本"""
        package_files = [
            "frontend / package.json",
            "frontend_old / package.json",
            "chrome - devtools - mcp / package.json",
        ]

        for file_path in package_files:
            self._sync_json_version(file_path, "version", "前端包")

    def _sync_python_projects(self):
        """同步Python项目配置"""
        project_files = [
            "pyproject.toml",
            "pyo3 - bindings / pyproject.toml",
            "shared / pyproject.toml",
            "CODEX--/Hephaestus / pyproject.toml",
        ]

        for file_path in project_files:
            self._sync_toml_version(file_path, "project.version", "Python项目")

    def _sync_other_configs(self):
        """同步其他配置文件"""
        other_files = [
            "package.json",  # 根目录package.json
            "docker - compose.yml",
            "update_versions.py",
        ]

        # 处理package.json
        self._sync_json_version("package.json", "version", "根配置")

        # 处理Docker Compose（如果有版本标签）
        self._sync_docker_compose()

        # 更新版本同步脚本自身
        self._sync_update_script()

    def _sync_file(self, file_path: str, patterns: List[Tuple[str, str]], file_type: str):
        """同步单个文件的版本

        Args:
            file_path: 文件路径
            patterns: 版本匹配模式列表 (pattern, replacement_template)
            file_type: 文件类型描述
        """
        full_path = self.version_manager.project_root / file_path

        if not full_path.exists():
            self._log_result(file_path, "文件不存在", "skipped")
            return

        try:
            with open(full_path, 'r', encoding='utf - 8') as f:
                content = f.read()

            original_content = content
            updated = False

            for pattern, replacement_template in patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    current_version = match.group(1)
                    if current_version != self.target_version:
                        # 检查主版本号是否匹配（避免不兼容的更新）
                        try:
                            current_major = int(current_version.split('.')[0])
                            target_major = self.target_version_info.major

                            # 如果主版本号不同，询问用户确认
                            if current_major != target_major:
                                if not self._confirm_major_version_change(
                                    file_path, current_version, self.target_version
                                ):
                                    continue
                        except (ValueError, IndexError):
                            pass  # 版本格式错误，直接更新

                        # 替换版本号
                        new_version_str = replacement_template.format(self.target_version)
                        content = content.replace(match.group(0), new_version_str)
                        updated = True

            if updated:
                if not self.dry_run:
                    with open(full_path, 'w', encoding='utf - 8') as f:
                        f.write(content)
                self._log_result(file_path, f"更新到 {self.target_version}", "updated")
            else:
                self._log_result(file_path, "已是最新版本", "skipped")

        except Exception as e:
            self._log_result(file_path, f"错误: {e}", "error")

    def _sync_json_version(self, file_path: str, version_key: str, file_type: str):
        """同步JSON文件中的版本号"""
        full_path = self.version_manager.project_root / file_path

        if not full_path.exists():
            self._log_result(file_path, "文件不存在", "skipped")
            return

        try:
            with open(full_path, 'r', encoding='utf - 8') as f:
                data = json.load(f)

            if version_key in data:
                current_version = data[version_key]
                if current_version != self.target_version:
                    if not self.dry_run:
                        data[version_key] = self.target_version
                        with open(full_path, 'w', encoding='utf - 8') as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                    self._log_result(file_path, f"更新 {version_key} 到 {self.target_version}", "updated")
                else:
                    self._log_result(file_path, "已是最新版本", "skipped")
            else:
                self._log_result(file_path, f"未找到 {version_key} 字段", "skipped")

        except Exception as e:
            self._log_result(file_path, f"JSON解析错误: {e}", "error")

    def _sync_toml_version(self, file_path: str, version_path: str, file_type: str):
        """同步TOML文件中的版本号"""
        full_path = self.version_manager.project_root / file_path

        if not full_path.exists():
            self._log_result(file_path, "文件不存在", "skipped")
            return

        try:
            with open(full_path, 'r', encoding='utf - 8') as f:
                content = f.read()

            # 简单的TOML版本匹配
            version_pattern = r'version\s*=\s*["\']([^"\']+)["\']'
            match = re.search(version_pattern, content)

            if match:
                current_version = match.group(1)
                if current_version != self.target_version:
                    # 替换版本号
                    new_version_line = "version = "{self.target_version}"'
                    content = content.replace(match.group(0), new_version_line)

                    if not self.dry_run:
                        with open(full_path, 'w', encoding='utf - 8') as f:
                            f.write(content)

                    self._log_result(file_path, f"更新到 {self.target_version}", "updated")
                else:
                    self._log_result(file_path, "已是最新版本", "skipped")
            else:
                self._log_result(file_path, "未找到version字段", "skipped")

        except Exception as e:
            self._log_result(file_path, f"TOML解析错误: {e}", "error")

    def _sync_docker_compose(self):
        """同步Docker Compose中的版本标签"""
        file_path = "docker - compose.yml"
        full_path = self.version_manager.project_root / file_path

        if not full_path.exists():
            self._log_result(file_path, "文件不存在", "skipped")
            return

        try:
            with open(full_path, 'r', encoding='utf - 8') as f:
                content = f.read()

            # 查找版本标签模式
            version_label_pattern = r'(VERSION|version):\s*["\']?([^"\'\s]+)["\']?'
            matches = list(re.finditer(version_label_pattern, content))

            if matches:
                updated = False
                for match in matches:
                    current_version = match.group(2)
                    if current_version != self.target_version:
                        new_label = f"{match.group(1)}: {self.target_version}"
                        content = content.replace(match.group(0), new_label)
                        updated = True

                if updated:
                    if not self.dry_run:
                        with open(full_path, 'w', encoding='utf - 8') as f:
                            f.write(content)
                    self._log_result(file_path, f"更新版本标签到 {self.target_version}", "updated")
                else:
                    self._log_result(file_path, "版本标签已是最新", "skipped")
            else:
                self._log_result(file_path, "未找到版本标签", "skipped")

        except Exception as e:
            self._log_result(file_path, f"Docker Compose解析错误: {e}", "error")

    def _sync_update_script(self):
        """更新版本同步脚本中的目标版本"""
        file_path = "scripts / sync_versions.py"
        full_path = self.version_manager.project_root / file_path

        try:
            with open(full_path, 'r', encoding='utf - 8') as f:
                content = f.read()

            # 这里不需要特别处理，因为脚本从VERSION文件读取版本
            self._log_result(file_path, "无需更新（动态读取版本）", "skipped")

        except Exception as e:
            self._log_result(file_path, f"错误: {e}", "error")

    def _confirm_major_version_change(self, file_path: str, current: str, target: str) -> bool:
        """确认主版本号更改"""
        if self.dry_run:
            return True  # 试运行模式下总是确认

        print(f"\n⚠️  主版本号不匹配: {file_path}")
        print(f"   当前版本: {current}")
        print(f"   目标版本: {target}")
        print("   这可能包含不兼容的更改！")

        response = input("   是否继续更新？(y / N): ").lower().strip()
        return response in ('y', 'yes', '是')

    def _log_result(self, file_path: str, message: str, result_type: str):
        """记录同步结果"""
        self.stats["total"] += 1
        self.stats[result_type] += 1

        status_icons = {
            "updated": "✅",
            "skipped": "⏭️",
            "error": "❌"
        }

        icon = status_icons.get(result_type, "📝")
        print(f"   {icon} {file_path}: {message}")

    def _print_summary(self):
        """打印同步摘要"""
        print("📈 统计摘要:")
        print(f"   总计文件: {self.stats['total']}")
        print(f"   已更新:   {self.stats['updated']}")
        print(f"   已跳过:   {self.stats['skipped']}")
        print(f"   错误:     {self.stats['errors']}")

        if self.dry_run:
            print("\n🧪 这是试运行结果，没有文件被实际修改。")
            print("   如需实际更新，请移除 --dry - run 参数。")


def check_version_consistency():
    """检查版本一致性"""
    print("🔍 检查版本一致性...")

    version_manager = get_version_manager()
    consistency_issues = version_manager.check_version_consistency()

    if not any(consistency_issues.values()):
        print("🎉 所有组件版本一致！")
        return True

    print("⚠️ 发现版本不一致问题:")

    if consistency_issues["version_mismatches"]:
        print("\n📋 版本不匹配:")
        for mismatch in consistency_issues["version_mismatches"]:
            print(f"   ❌ {mismatch['file']}: 期望 {mismatch['expected']}, 实际 {mismatch['found']}")

    if consistency_issues["missing_versions"]:
        print("\n📋 缺少版本信息:")
        for missing in consistency_issues["missing_versions"]:
            print(f"   ⚠️  {missing}")

    if consistency_issues["parse_errors"]:
        print("\n📋 解析错误:")
        for error in consistency_issues["parse_errors"]:
            print(f"   ❌ {error['file']}: {error['error']}")

    return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="版本同步工具")
    parser.add_argument("--check", action="store_true", help="只检查版本一致性，不进行同步")
    parser.add_argument("--dry - run", action="store_true", help="试运行模式，不实际修改文件")
    parser.add_argument("--version", action="version", version=f"香港量化交易系统版本同步工具 v{get_version_manager().get_current_version()}")

    args = parser.parse_args()

    if args.check:
        # 只检查版本一致性
        success = check_version_consistency()
        sys.exit(0 if success else 1)

    # 执行版本同步
    sync = VersionSync(dry_run=args.dry_run)
    stats = sync.sync_all()

    # 根据统计结果决定退出码
    if stats["errors"] > 0:
        sys.exit(1)  # 有错误发生
    elif stats["updated"] == 0:
        sys.exit(0)  # 没有需要更新的文件
    else:
        sys.exit(0)  # 成功更新了一些文件


if __name__ == "__main__":
    main()
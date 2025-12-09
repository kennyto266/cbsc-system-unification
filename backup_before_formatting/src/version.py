"""
香港量化交易系统 - 统一版本管理
Hong Kong Quantitative Trading System - Unified Version Management

这是系统的权威版本控制模块，所有组件都应从此模块读取版本信息。

版本格式遵循语义化版本控制 (Semantic Versioning): MAJOR.MINOR.PATCH
- MAJOR: 重大架构变更或不兼容更新
- MINOR: 新功能添加或重大改进
- PATCH: Bug修复或小幅改进

当前版本: 2.1.0 (企业级量化交易平台)
"""

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class VersionInfo:
    """版本信息数据类"""

    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None
    build_metadata: Optional[str] = None

    def __str__(self) -> str:
        """返回标准版本字符串"""
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        if self.build_metadata:
            version += f"+{self.build_metadata}"
        return version

    def to_tuple(self) -> Tuple[int, int, int]:
        """返回版本号元组"""
        return (self.major, self.minor, self.patch)

    def is_compatible(self, other: "VersionInfo") -> bool:
        """检查版本兼容性（相同主版本号）"""
        return self.major == other.major


class VersionManager:
    """统一版本管理器"""

    # 系统当前版本信息
    CURRENT_VERSION = VersionInfo(
        major=2, minor=1, patch=0, prerelease=None, build_metadata=None
    )

    # 版本历史
    VERSION_HISTORY = {
        "1.0.0": "基础量化交易系统完成 - 三层架构、多智能体系统",
        "1.1.0": "RSI优化器集成 - 多进程并行优化、专业可视化",
        "2.0.0": "企业级升级 - 完整API、安全框架、监控体系",
        "2.1.0": "AI增强版本 - GLM4.6集成、智能分析、Telegram Bot增强",
    }

    def __init__(self, project_root: Optional[Path] = None):
        """初始化版本管理器

        Args:
            project_root: 项目根目录路径，默认自动检测
        """
        if project_root is None:
            self.project_root = self._find_project_root()
        else:
            self.project_root = Path(project_root)

        self.version_file = self.project_root / "VERSION"
        self.version_config_file = self.project_root / "VERSION_CONFIG.json"

    def _find_project_root(self) -> Path:
        """自动检测项目根目录"""
        current = Path(__file__).parent

        # 查找包含VERSION文件的根目录
        while current.parent != current:
            if (current / "VERSION").exists() or (current / "pyproject.toml").exists():
                return current
            current = current.parent

        # 如果找不到，返回当前文件所在目录的上级
        return Path(__file__).parent.parent

    def get_current_version(self) -> str:
        """获取当前版本字符串"""
        # 优先从VERSION文件读取
        if self.version_file.exists():
            try:
                with open(self.version_file, "r", encoding="utf - 8") as f:
                    version_content = f.read().strip()
                    # 如果文件有额外内容，只取第一行的版本号
                    version_line = version_content.split("\n")[0]
                    if version_line and not version_line.startswith("#"):
                        return version_line
            except Exception:
                pass

        # 回退到硬编码版本
        return str(self.CURRENT_VERSION)

    def get_version_info(self) -> VersionInfo:
        """获取详细版本信息对象"""
        version_str = self.get_current_version()
        return self._parse_version_string(version_str)

    def _parse_version_string(self, version_str: str) -> VersionInfo:
        """解析版本字符串为VersionInfo对象"""
        # 移除v前缀
        if version_str.startswith("v"):
            version_str = version_str[1:]

        # 分离构建元数据
        if "+" in version_str:
            version_str, build_metadata = version_str.split("+", 1)
        else:
            build_metadata = None

        # 分离预发布版本
        if "-" in version_str:
            version_str, prerelease = version_str.split("-", 1)
        else:
            prerelease = None

        # 解析主版本号
        parts = version_str.split(".")
        if len(parts) < 3:
            parts.extend(["0"] * (3 - len(parts)))

        try:
            major = int(parts[0]) if parts[0] else 0
            minor = int(parts[1]) if parts[1] else 0
            patch = int(parts[2]) if parts[2] else 0
        except ValueError:
            # 如果解析失败，使用默认版本
            major, minor, patch = self.CURRENT_VERSION.to_tuple()

        return VersionInfo(
            major=major,
            minor=minor,
            patch=patch,
            prerelease=prerelease,
            build_metadata=build_metadata,
        )

    def get_build_info(self) -> Dict:
        """获取完整构建信息"""
        version_info = self.get_version_info()

        return {
            "version": str(version_info),
            "version_tuple": version_info.to_tuple(),
            "version_info": {
                "major": version_info.major,
                "minor": version_info.minor,
                "patch": version_info.patch,
                "prerelease": version_info.prerelease,
                "build_metadata": version_info.build_metadata,
            },
            "build_time": datetime.now().isoformat(),
            "build_environment": os.getenv("PYTHON_ENV", "development"),
            "project_root": str(self.project_root),
            "git_branch": self._get_git_branch(),
            "git_commit": self._get_git_commit(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "features": self._get_system_features(),
            "history": self.VERSION_HISTORY,
        }

    def _get_git_branch(self) -> Optional[str]:
        """获取当前Git分支"""
        try:
            import subprocess

            result = subprocess.run(
                ["git", "rev - parse", "--abbrev - re", "HEAD"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None

    def _get_git_commit(self) -> Optional[str]:
        """获取当前Git提交哈希"""
        try:
            import subprocess

            result = subprocess.run(
                ["git", "rev - parse", "HEAD"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()[:8]  # 只取前8位
        except Exception:
            pass
        return None

    def _get_system_features(self) -> List[str]:
        """获取系统功能列表"""
        features = [
            "三层架构设计",
            "RSI策略优化器",
            "多智能体协作系统",
            "实时数据集成",
            "专业可视化界面",
            "企业级安全框架",
            "AI智能分析",
            "Telegram Bot集成",
        ]

        # 检查可选功能
        feature_files = {
            "Rust性能引擎": "rust - core / Cargo.toml",
            "AI Agent系统": "CODEX--/Hephaestus / pyproject.toml",
            "Docker部署": "docker - compose.yml",
            "监控系统": "src / monitoring",
            "安全审计": "src / security",
        }

        for feature, file_path in feature_files.items():
            if (self.project_root / file_path).exists():
                features.append(feature)

        return features

    def update_version(self, new_version: str, reason: str = "") -> bool:
        """更新系统版本号

        Args:
            new_version: 新版本号字符串
            reason: 更新原因说明

        Returns:
            bool: 是否更新成功
        """
        try:
            # 验证新版本格式
            new_version_info = self._parse_version_string(new_version)

            # 更新VERSION文件
            with open(self.version_file, "w", encoding="utf - 8") as f:
                f.write(f"{new_version}\n")
                if reason:
                    f.write(f"# 更新原因: {reason}\n")
                    f.write(
                        f"# 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    )

            # 更新版本历史
            self.VERSION_HISTORY[new_version] = reason or f"版本更新至 {new_version}"

            # 保存版本配置
            self._save_version_config()

            return True

        except Exception as e:
            print(f"版本更新失败: {e}")
            return False

    def _save_version_config(self) -> None:
        """保存版本配置到JSON文件"""
        config = {
            "current_version": str(self.CURRENT_VERSION),
            "version_history": self.VERSION_HISTORY,
            "last_updated": datetime.now().isoformat(),
            "project_root": str(self.project_root),
        }

        try:
            with open(self.version_config_file, "w", encoding="utf - 8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception:
            pass  # 配置文件保存失败不影响主要功能

    def check_version_consistency(self) -> Dict[str, List[str]]:
        """检查项目各组件版本一致性

        Returns:
            Dict: 包含不一致版本的文件列表
        """
        current_version = self.get_current_version()
        issues: Dict[str, List[str]] = {"version_mismatches": [], "missing_versions": [], "parse_errors": []}

        # 检查文件列表
        files_to_check = [
            ("src / __init__.py", r'__version__\s*=\s*["\']([^"\']+)["\']'),
            ("frontend / package.json", r'"version"\s*:\s*"([^"]+)"'),
            ("pyproject.toml", r'version\s*=\s*["\']([^"\']+)["\']'),
            ("chrome - devtools - mcp / package.json", r'"version"\s*:\s*"([^"]+)"'),
            ("shared / pyproject.toml", r'version\s*=\s*["\']([^"\']+)["\']'),
        ]

        import re

        for file_path, pattern in files_to_check:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    with open(full_path, "r", encoding="utf - 8") as f:
                        content = f.read()

                    match = re.search(pattern, content)
                    if match:
                        file_version = match.group(1)
                        # 只检查主版本号是否匹配
                        if file_version.split(".")[0] != current_version.split(".")[0]:
                            issues["version_mismatches"].append(
                                {
                                    "file": file_path,
                                    "expected": current_version,
                                    "found": file_version,
                                }
                            )
                    else:
                        issues["missing_versions"].append(file_path)

                except Exception as e:
                    issues["parse_errors"].append({"file": file_path, "error": str(e)})
            else:
                issues["missing_versions"].append(file_path)

        return issues

    def generate_version_report(self) -> str:
        """生成版本一致性报告"""
        consistency = self.check_version_consistency()
        current_version = self.get_current_version()

        report = """
# 香港量化交易系统 - 版本报告
# Hong Kong Quantitative Trading System - Version Report

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
当前版本: {current_version}

## 版本一致性检查结果

### ✅ 版本匹配
所有核心组件版本号一致

### ⚠️ 发现的问题
"""

        if consistency["version_mismatches"]:
            report += "\n#### 版本不匹配:\n"
            for mismatch in consistency["version_mismatches"]:
                if isinstance(mismatch, dict):
                    report += f"- {mismatch.get('file', 'unknown')}: 期望 {mismatch.get('expected', 'unknown')}, 实际 {mismatch.get('found', 'unknown')}\n"
                else:
                    report += f"- {mismatch}\n"

        if consistency["missing_versions"]:
            report += "\n#### 缺少版本信息:\n"
            for missing in consistency["missing_versions"]:
                report += f"- {missing}\n"

        if consistency["parse_errors"]:
            report += "\n#### 解析错误:\n"
            for error in consistency["parse_errors"]:
                if isinstance(error, dict):
                    report += f"- {error.get('file', 'unknown')}: {error.get('error', 'unknown error')}\n"
                else:
                    report += f"- {error}\n"

        if not any(consistency.values()):
            report += "\n🎉 所有组件版本一致！\n"

        report += """
## 详细构建信息

{json.dumps(self.get_build_info(), ensure_ascii=False, indent=2)}
"""

        return report


# 全局版本管理器实例
_version_manager = None


def get_version_manager() -> VersionManager:
    """获取全局版本管理器实例"""
    global _version_manager
    if _version_manager is None:
        _version_manager = VersionManager()
    return _version_manager


# 便捷函数
def get_version() -> str:
    """获取当前版本字符串"""
    return get_version_manager().get_current_version()


def get_version_tuple() -> Tuple[int, int, int]:
    """获取版本号元组"""
    return get_version_manager().get_version_info().to_tuple()


def get_build_info() -> Dict:
    """获取完整构建信息"""
    return get_version_manager().get_build_info()


def update_version(new_version: str, reason: str = "") -> bool:
    """更新版本号"""
    return get_version_manager().update_version(new_version, reason)


def check_version_consistency() -> Dict[str, List[str]]:
    """检查版本一致性"""
    return get_version_manager().check_version_consistency()


def generate_version_report() -> str:
    """生成版本报告"""
    return get_version_manager().generate_version_report()


# 模块级别的版本信息（向后兼容）
__version__ = get_version()
__version_info__ = get_version_manager().get_version_info()

# 导出公共接口
__all__ = [
    "VersionInfo",
    "VersionManager",
    "get_version",
    "get_version_tuple",
    "get_build_info",
    "update_version",
    "check_version_consistency",
    "generate_version_report",
    "get_version_manager",
    "__version__",
    "__version_info__",
]

#!/usr/bin/env python3
"""
Simplified System 核心功能完整性验证器
验证简化系统架构的核心功能完整性
"""

import os
import sys
import json
import importlib.util
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import subprocess
import logging

class SimplifiedSystemIntegrityTester:
    """简化系统完整性测试器"""

    def __init__(self, simplified_system_path: str = None):
        self.project_root = Path.cwd()
        self.simplified_system = Path(simplified_system_path) if simplified_system_path else self.project_root / "simplified_system"

        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        # 核心模块验证清单
        self.core_modules = {
            "api": {
                "required_files": [
                    "stock_api.py",
                    "government_data.py",
                    "daily_tasks_api.py"
                ],
                "description": "数据接入层"
            },
            "indicators": {
                "required_files": [
                    "core_indicators.py",
                    "technical_analyzer.py"
                ],
                "description": "技术指标引擎"
            },
            "backtest": {
                "required_files": [
                    "vectorbt_engine.py",
                    "strategy_builder.py"
                ],
                "description": "回测执行层"
            },
            "telegram": {
                "required_files": [
                    "telegram_bot.py"
                ],
                "description": "用户接口层"
            }
        }

        # 核心配置文件
        self.core_configs = [
            "requirements.txt",
            "integration_test.py",
            "test_backtest_simple.py"
        ]

    def test_directory_structure(self) -> Tuple[bool, Dict]:
        """测试目录结构完整性"""
        self.logger.info("🏗️ 测试目录结构完整性...")

        results = {
            "status": "passed",
            "missing_dirs": [],
            "existing_dirs": []
        }

        required_dirs = [
            "src/api",
            "src/indicators",
            "src/backtest",
            "src/telegram",
            "src/data",
            "src/strategies",
            "src/risk",
            "src/utils",
            "config"
        ]

        for dir_path in required_dirs:
            full_path = self.simplified_system / dir_path
            if full_path.exists() and full_path.is_dir():
                results["existing_dirs"].append(dir_path)
                self.logger.info(f"✅ 目录存在: {dir_path}")
            else:
                results["missing_dirs"].append(dir_path)
                self.logger.error(f"❌ 目录缺失: {dir_path}")

        if results["missing_dirs"]:
            results["status"] = "failed"

        return len(results["missing_dirs"]) == 0, results

    def test_core_modules(self) -> Tuple[bool, Dict]:
        """测试核心模块完整性"""
        self.logger.info("📦 测试核心模块完整性...")

        results = {
            "status": "passed",
            "modules": {},
            "missing_files": []
        }

        for module_name, module_info in self.core_modules.items():
            module_results = {
                "status": "passed",
                "existing_files": [],
                "missing_files": []
            }

            module_path = self.simplified_system / "src" / module_name

            if not module_path.exists():
                module_results["missing_files"].extend(module_info["required_files"])
                module_results["status"] = "failed"
                results["missing_files"].extend([f"{module_name}/{file}" for file in module_info["required_files"]])
            else:
                for file_name in module_info["required_files"]:
                    file_path = module_path / file_name
                    if file_path.exists():
                        module_results["existing_files"].append(file_name)
                        self.logger.info(f"✅ 核心文件存在: {module_name}/{file_name}")
                    else:
                        module_results["missing_files"].append(file_name)
                        results["missing_files"].append(f"{module_name}/{file_name}")
                        self.logger.error(f"❌ 核心文件缺失: {module_name}/{file_name}")

                if module_results["missing_files"]:
                    module_results["status"] = "failed"

            results["modules"][module_name] = module_results

        if results["missing_files"]:
            results["status"] = "failed"

        return len(results["missing_files"]) == 0, results

    def test_configuration_files(self) -> Tuple[bool, Dict]:
        """测试配置文件完整性"""
        self.logger.info("⚙️ 测试配置文件完整性...")

        results = {
            "status": "passed",
            "existing_files": [],
            "missing_files": []
        }

        for config_file in self.core_configs:
            file_path = self.simplified_system / config_file
            if file_path.exists():
                results["existing_files"].append(config_file)
                self.logger.info(f"✅ 配置文件存在: {config_file}")
            else:
                results["missing_files"].append(config_file)
                self.logger.error(f"❌ 配置文件缺失: {config_file}")

        if results["missing_files"]:
            results["status"] = "failed"

        return len(results["missing_files"]) == 0, results

    def test_python_imports(self) -> Tuple[bool, Dict]:
        """测试Python模块导入"""
        self.logger.info("🐍 测试Python模块导入...")

        results = {
            "status": "passed",
            "successful_imports": [],
            "failed_imports": [],
            "import_errors": {}
        }

        # 添加simplified_system到Python路径
        if str(self.simplified_system) not in sys.path:
            sys.path.insert(0, str(self.simplified_system))

        # 测试核心模块导入
        test_modules = [
            ("src.api.stock_api", "stock_api"),
            ("src.api.government_data", "government_data"),
            ("src.indicators.core_indicators", "core_indicators"),
            ("src.backtest.vectorbt_engine", "vectorbt_engine")
        ]

        for module_path, module_name in test_modules:
            try:
                # 尝试导入模块
                spec = importlib.util.spec_from_file_location(
                    module_name,
                    self.simplified_system / f"{module_path.replace('.', '/')}.py"
                )

                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    results["successful_imports"].append(module_name)
                    self.logger.info(f"✅ 模块导入成功: {module_name}")
                else:
                    results["failed_imports"].append(module_name)
                    results["import_errors"][module_name] = "无法创建模块规范"

            except Exception as e:
                results["failed_imports"].append(module_name)
                results["import_errors"][module_name] = str(e)
                self.logger.error(f"❌ 模块导入失败: {module_name} - {e}")

        if results["failed_imports"]:
            results["status"] = "failed"

        return len(results["failed_imports"]) == 0, results

    def test_dependencies(self) -> Tuple[bool, Dict]:
        """测试依赖包可用性"""
        self.logger.info("📚 测试依赖包可用性...")

        results = {
            "status": "passed",
            "available_packages": [],
            "missing_packages": [],
            "package_errors": {}
        }

        # 核心依赖包列表
        required_packages = [
            "requests",
            "pandas",
            "numpy",
            "vectorbt",  # 可选
            "matplotlib",
            "plotly",
            "python-telegram-bot"  # 可选
        ]

        for package in required_packages:
            try:
                # 尝试导入包
                if package == "python-telegram-bot":
                    import telegram
                else:
                    __import__(package)

                results["available_packages"].append(package)
                self.logger.info(f"✅ 依赖包可用: {package}")

            except ImportError as e:
                results["missing_packages"].append(package)
                results["package_errors"][package] = str(e)
                self.logger.warning(f"⚠️ 依赖包缺失: {package} - {e}")

        # 检查requirements.txt
        requirements_path = self.simplified_system / "requirements.txt"
        if requirements_path.exists():
            try:
                with open(requirements_path, 'r', encoding='utf-8') as f:
                    requirements_content = f.read()
                results["requirements_exists"] = True
                results["requirements_content"] = requirements_content
                self.logger.info("✅ requirements.txt 存在且可读")
            except Exception as e:
                results["requirements_exists"] = False
                results["requirements_error"] = str(e)
                self.logger.error(f"❌ requirements.txt 读取失败: {e}")

        # 如果核心依赖缺失，标记为失败
        core_packages = ["requests", "pandas", "numpy"]
        missing_core = [pkg for pkg in core_packages if pkg in results["missing_packages"]]

        if missing_core:
            results["status"] = "failed"
            self.logger.error(f"❌ 核心依赖缺失: {missing_core}")

        return len(missing_core) == 0, results

    def test_basic_functionality(self) -> Tuple[bool, Dict]:
        """测试基本功能"""
        self.logger.info("🧪 测试基本功能...")

        results = {
            "status": "passed",
            "functionality_tests": {},
            "errors": {}
        }

        try:
            # 切换到simplified_system目录
            original_cwd = os.getcwd()
            os.chdir(self.simplified_system)

            # 测试1: Python环境基础测试
            test1_result = subprocess.run([
                sys.executable, "-c",
                """
import sys
print(f'Python版本: {sys.version}')
print('基础语法测试通过')
print('数字运算测试:', 1 + 1 == 2)
print('字符串测试:', 'hello' + ' world' == 'hello world')
"""
            ], capture_output=True, text=True, timeout=30)

            results["functionality_tests"]["python_basics"] = {
                "success": test1_result.returncode == 0,
                "output": test1_result.stdout,
                "error": test1_result.stderr
            }

            if test1_result.returncode == 0:
                self.logger.info("✅ Python基础功能测试通过")
            else:
                self.logger.error(f"❌ Python基础功能测试失败: {test1_result.stderr}")
                results["errors"]["python_basics"] = test1_result.stderr

            # 测试2: 模块结构测试
            test2_result = subprocess.run([
                sys.executable, "-c",
                """
import os
import sys

# 检查src目录结构
src_path = 'src'
required_subdirs = ['api', 'indicators', 'backtest', 'telegram']

missing_dirs = []
for subdir in required_subdirs:
    if not os.path.exists(os.path.join(src_path, subdir)):
        missing_dirs.append(subdir)

if missing_dirs:
    print(f'缺少目录: {missing_dirs}')
    sys.exit(1)
else:
    print('所有核心目录结构正确')
"""
            ], capture_output=True, text=True, timeout=30)

            results["functionality_tests"]["directory_structure"] = {
                "success": test2_result.returncode == 0,
                "output": test2_result.stdout,
                "error": test2_result.stderr
            }

            if test2_result.returncode == 0:
                self.logger.info("✅ 目录结构测试通过")
            else:
                self.logger.error(f"❌ 目录结构测试失败: {test2_result.stderr}")
                results["errors"]["directory_structure"] = test2_result.stderr

            # 测试3: 配置文件读取测试
            test3_result = subprocess.run([
                sys.executable, "-c",
                """
try:
    # 尝试读取requirements.txt
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        requirements = f.read()

    print('requirements.txt 读取成功')
    print(f'依赖行数: {len(requirements.splitlines())}')

except FileNotFoundError:
    print('requirements.txt 不存在')
except Exception as e:
    print(f'读取错误: {e}')
"""
            ], capture_output=True, text=True, timeout=30)

            results["functionality_tests"]["config_reading"] = {
                "success": test3_result.returncode == 0,
                "output": test3_result.stdout,
                "error": test3_result.stderr
            }

            if test3_result.returncode == 0:
                self.logger.info("✅ 配置文件读取测试通过")
            else:
                self.logger.warning(f"⚠️ 配置文件读取测试警告: {test3_result.stderr}")

        except Exception as e:
            results["status"] = "failed"
            results["errors"]["execution"] = str(e)
            self.logger.error(f"❌ 基本功能测试执行异常: {e}")

        finally:
            # 切换回原目录
            os.chdir(original_cwd)

        # 检查是否有致命错误
        failed_tests = [
            name for name, test in results["functionality_tests"].items()
            if not test.get("success", False) and name in ["python_basics", "directory_structure"]
        ]

        if failed_tests:
            results["status"] = "failed"
            self.logger.error(f"❌ 关键功能测试失败: {failed_tests}")

        return len(failed_tests) == 0, results

    def run_comprehensive_test(self) -> Dict:
        """运行完整测试套件"""
        self.logger.info("🎯 开始Simplified System完整性测试")
        self.logger.info(f"📍 测试路径: {self.simplified_system}")

        test_results = {
            "test_timestamp": datetime.now().isoformat(),
            "simplified_system_path": str(self.simplified_system),
            "overall_status": "passed",
            "test_results": {}
        }

        test_methods = [
            ("directory_structure", self.test_directory_structure),
            ("core_modules", self.test_core_modules),
            ("configuration_files", self.test_configuration_files),
            ("python_imports", self.test_python_imports),
            ("dependencies", self.test_dependencies),
            ("basic_functionality", self.test_basic_functionality)
        ]

        failed_tests = []

        for test_name, test_method in test_methods:
            self.logger.info(f"\n{'='*50}")
            self.logger.info(f"🧪 执行测试: {test_name}")

            try:
                success, result = test_method()
                test_results["test_results"][test_name] = {
                    "status": "passed" if success else "failed",
                    "details": result
                }

                if success:
                    self.logger.info(f"✅ {test_name} 测试通过")
                else:
                    self.logger.error(f"❌ {test_name} 测试失败")
                    failed_tests.append(test_name)

            except Exception as e:
                self.logger.error(f"❌ {test_name} 测试异常: {e}")
                test_results["test_results"][test_name] = {
                    "status": "error",
                    "error": str(e)
                }
                failed_tests.append(test_name)

        # 确定整体状态
        if failed_tests:
            test_results["overall_status"] = "failed"
            test_results["failed_tests"] = failed_tests

        # 生成测试报告
        report_path = self.simplified_system / "integrity_test_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(test_results, f, indent=2, ensure_ascii=False)

        # 打印测试摘要
        self._print_test_summary(test_results)

        return test_results

    def _print_test_summary(self, test_results: Dict):
        """打印测试摘要"""
        self.logger.info("\n" + "="*60)
        self.logger.info("📊 Simplified System 完整性测试摘要")
        self.logger.info("="*60)

        overall_status = test_results["overall_status"]
        status_icon = "✅" if overall_status == "passed" else "❌"
        self.logger.info(f"{status_icon} 整体状态: {overall_status.upper()}")

        self.logger.info("\n📋 详细测试结果:")
        for test_name, result in test_results["test_results"].items():
            status = result["status"]
            icon = "✅" if status == "passed" else "❌" if status == "failed" else "⚠️"
            self.logger.info(f"{icon} {test_name}: {status}")

        if overall_status == "failed" and "failed_tests" in test_results:
            self.logger.info(f"\n❌ 失败的测试: {', '.join(test_results['failed_tests'])}")

        self.logger.info(f"\n📁 测试路径: {test_results['simplified_system_path']}")
        self.logger.info(f"📅 测试时间: {test_results['test_timestamp']}")
        self.logger.info(f"📊 报告文件: {self.simplified_system}/integrity_test_report.json")

        # 提供修复建议
        if overall_status == "failed":
            self._provide_fix_suggestions(test_results)

    def _provide_fix_suggestions(self, test_results: Dict):
        """提供修复建议"""
        self.logger.info("\n💡 修复建议:")

        suggestions = []

        for test_name, result in test_results["test_results"].items():
            if result["status"] == "failed":
                if test_name == "directory_structure":
                    suggestions.append("创建缺失的核心目录结构")
                elif test_name == "core_modules":
                    suggestions.append("恢复缺失的核心模块文件")
                elif test_name == "configuration_files":
                    suggestions.append("创建缺失的配置文件")
                elif test_name == "dependencies":
                    suggestions.append("安装缺失的依赖包: pip install -r requirements.txt")
                elif test_name == "basic_functionality":
                    suggestions.append("检查Python环境和基本配置")

        for i, suggestion in enumerate(suggestions, 1):
            self.logger.info(f"  {i}. {suggestion}")

        self.logger.info("\n🔄 如需恢复，请使用备份目录中的文件")

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Simplified System完整性测试器")
    parser.add_argument("--path", help="Simplified System路径")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    tester = SimplifiedSystemIntegrityTester(args.path)
    results = tester.run_comprehensive_test()

    # 返回适当的退出代码
    sys.exit(0 if results["overall_status"] == "passed" else 1)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
依賴管理菜單系統
提供用戶友好的依賴管理界面
"""

import sys
from typing import Dict, Any, Optional
from .dependency_manager import DependencyManager

class DependencyMenu:
    """依賴菜單管理器"""

    def __init__(self, dependency_manager: DependencyManager):
        self.dependency_manager = dependency_manager

    def show_dependency_menu(self, trader_instance):
        """顯示依賴管理菜單"""
        while True:
            trader_instance._print_header()

            menu_items = [
                ("1", "📋 查看依賴狀態"),
                ("2", "🔧 依賴兼容性檢查"),
                ("3", "⚡ 性能配置檢查"),
                ("4", "📦 安裝缺失依賴"),
                ("5", "🔍 詳細依賴信息"),
                ("6", "🚀 系統信息"),
                ("0", "🔙 返回主菜單")
            ]

            print(f"{trader_instance._get_colored_text('🛠️  依賴管理', 'bold')}")
            print("="*50)

            for key, description in menu_items:
                print(f"  {key}. {description}")

            # 顯示狀態摘要
            status = self.dependency_manager.get_dependency_status()
            print(f"\n{trader_instance._get_colored_text('依賴狀態摘要:', 'yellow')}")
            print(f"  必需依賴: {'✅ 完整' if status['all_required_available'] else '❌ 缺失'}")
            print(f"  可選依賴: {status['optional_available']}/{status['optional_total']}")
            print(f"  GPU支持: {'✅ 可用' if status['gpu_available'] else '❌ 不可用'}")
            print(f"  VectorBT: {'✅ 可用' if status['vectorbt_available'] else '❌ 不可用'}")

            choice = trader_instance._get_user_input("請選擇功能", [str(i) for i in range(7)])

            if choice == '0':
                break
            elif choice == '1':
                self._show_dependency_status(trader_instance)
            elif choice == '2':
                self._show_compatibility_check(trader_instance)
            elif choice == '3':
                self._show_performance_profile(trader_instance)
            elif choice == '4':
                self._install_dependencies(trader_instance)
            elif choice == '5':
                self._show_detailed_info(trader_instance)
            elif choice == '6':
                self._show_system_info(trader_instance)

    def _show_dependency_status(self, trader_instance):
        """顯示依賴狀態"""
        print(f"\n{trader_instance._get_colored_text('📋 依賴狀態', 'bold')}")
        print("="*60)

        # 獲取依賴狀態
        deps = self.dependency_manager.dependencies
        status = self.dependency_manager.get_dependency_status()

        # 顯示必需依賴
        print(f"\n{trader_instance._get_colored_text('🔴 必需依賴', 'red') if not status['all_required_available'] else trader_instance._get_colored_text('🟢 必需依賴', 'green')}")
        print("-" * 30)

        required_deps = [(name, dep) for name, dep in deps.items() if dep['required']]

        if trader_instance.tabulate_available:
            from tabulate import tabulate
            headers = ["依賴", "狀態", "版本", "最低要求", "功能"]
            table_data = []

            for name, dep in required_deps:
                status_icon = "✅" if dep['available'] else "❌"
                version = dep['version'] if dep['version'] else "N/A"
                min_version = dep['min_version'] if dep['min_version'] else "N/A"
                features = ", ".join(dep['features']) if dep['features'] else "N/A"
                version_status = "✅" if dep['version_ok'] else "⚠️"

                table_data.append([name, f"{status_icon} {version_status}", f"{version}", f"{min_version}", features])

            print(tabulate(table_data, headers=headers, tablefmt="grid"))
        else:
            for name, dep in required_deps:
                status_icon = "✅" if dep['available'] else "❌"
                version_status = "✅" if dep['version_ok'] else "⚠️"
                print(f"  {name}: {status_icon} {dep.get('version', 'N/A')} {version_status}")

        # 顯示可選依賴
        print(f"\n{trader_instance._get_colored_text('🔵 可選依賴', 'blue')}")
        print("-" * 30)

        optional_deps = [(name, dep) for name, dep in deps.items() if not dep['required']]

        if trader_instance.tabulate_available:
            headers = ["依賴", "狀態", "版本", "功能"]
            table_data = []

            for name, dep in optional_deps:
                status_icon = "✅" if dep['available'] else "⭕"
                version = dep['version'] if dep['version'] else "N/A"
                features = ", ".join(dep['features']) if dep['features'] else "N/A"

                table_data.append([name, status_icon, version, features])

            print(tabulate(table_data, headers=headers, tablefmt="grid"))
        else:
            for name, dep in optional_deps:
                status_icon = "✅" if dep['available'] else "⭕"
                features = f" ({', '.join(dep['features'])})" if dep['features'] else ""
                print(f"  {name}: {status_icon}{features}")

        # 顯示缺失依賴的安裝建議
        missing = self.dependency_manager.get_missing_dependencies()
        if missing:
            print(f"\n{trader_instance._get_colored_text('⚠️  缺失依賴安裝建議:', 'yellow')}")
            for dep in missing:
                print(f"  {dep['name']}: {dep['install_command']}")

        input(f"\n{trader_instance._get_colored_text('按Enter繼續...', 'cyan')}")

    def _show_compatibility_check(self, trader_instance):
        """顯示兼容性檢查"""
        print(f"\n{trader_instance._get_colored_text('🔧 依賴兼容性檢查', 'bold')}")
        print("="*60)

        report = self.dependency_manager.get_compatibility_report()

        # 顯示基本信息
        print(f"\n{trader_instance._get_colored_text('系統信息:', 'yellow')}")
        print(f"  操作系統: {report['platform']}")
        print(f"  Python版本: {report['python_version']}")
        print(f"  兼容性分數: {report['compatibility_score']}/100")
        print(f"  性能等級: {report['performance_tier']}")

        # 顯示兼容性問題
        if report['issues']:
            print(f"\n{trader_instance._get_colored_text('⚠️  兼容性問題:', 'yellow')}")
            for i, issue in enumerate(report['issues'], 1):
                print(f"  {i}. {issue}")

        # 顯示建議
        if report['recommendations']:
            print(f"\n{trader_instance._get_colored_text('💡 優化建議:', 'green')}")
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"  {i}. {rec}")

        # 顯示性能等級說明
        print(f"\n{trader_instance._get_colored_text('📊 性能等級說明:', 'blue')}")
        tier_descriptions = {
            'Basic': '基礎功能 - 所有核心功能可用',
            'Enhanced': '增強功能 - 基礎回測和分析可用',
            'Advanced': '高級功能 - GPU加速可用',
            'Professional': '專業級 - 所有功能可用，最佳性能'
        }

        tier_desc = tier_descriptions.get(report['performance_tier'], '未知')
        print(f"  {report['performance_tier']}: {tier_desc}")

        input(f"\n{trader_instance._get_colored_text('按Enter繼續...', 'cyan')}")

    def _show_performance_profile(self, trader_instance):
        """顯示性能配置"""
        print(f"\n{trader_instance._get_colored_text('⚡ 性能配置檢查', 'bold')}")
        print("="*60)

        profile = self.dependency_manager.get_performance_profile()

        print(f"\n{trader_instance._get_colored_text('🚀 加速配置:', 'yellow')}")
        print(f"  加速級別: {profile['acceleration_level']}")
        print(f"  多進程並行: {'啟用' if profile['parallelization'] else '禁用'}")
        print(f"  內存優化: {'啟用' if profile['memory_optimization'] else '禁用'}")

        if profile['recommendations']:
            print(f"\n{trader_instance._get_colored_text('💡 性能建議:', 'green')}")
            for i, rec in enumerate(profile['recommendations'], 1):
                print(f"  {i}. {rec}")

        # 顯示GPU詳細信息
        if profile['acceleration_level'] == 'GPU':
            print(f"\n{trader_instance._get_colored_text('🎮 GPU詳細信息:', 'blue')}")
            try:
                import cupy as cp
                device = cp.cuda.Device()
                print(f"  GPU名稱: {device.name}")
                print(f"  GPU ID: {device.id}")
                print(f"  計算能力: {device.compute_capability}")
                print(f"  內存大小: {device.mem_info[1] / (1024**3):.1f} GB")
            except Exception as e:
                print(f"  無法獲取GPU詳細信息: {e}")

        # 顯示CPU信息
        print(f"\n{trader_instance._get_colored_text('🖥️  CPU信息:', 'blue')}")
        import multiprocessing
        cpu_count = multiprocessing.cpu_count()
        print(f"  CPU核心數: {cpu_count}")
        print(f"  並行處理: {'可用' if cpu_count >= 4 else '有限'}")

        # 顯示內存信息
        try:
            import psutil
            memory = psutil.virtual_memory()
            print(f"\n{trader_instance._get_colored_text('💾 內存信息:', 'blue')}")
            print(f"  總內存: {memory.total / (1024**3):.1f} GB")
            print(f"  可用內存: {memory.available / (1024**3):.1f} GB")
            print(f"  使用率: {memory.percent:.1f}%")
        except:
            print(f"\n{trader_instance._get_colored_text('💾 內存信息:', 'blue')}")
            print(f"  psutil不可用，無法獲取詳細內存信息")

        input(f"\n{trader_instance._get_colored_text('按Enter繼續...', 'cyan')}")

    def _install_dependencies(self, trader_instance):
        """安裝缺失依賴"""
        print(f"\n{trader_instance._get_colored_text('📦 安裝缺失依賴', 'bold')}")
        print("="*60)

        missing = self.dependency_manager.get_missing_dependencies()

        if not missing:
            print(f"{trader_instance._get_colored_text('✅ 所有必需依賴都已安裝!', 'green')}")
            input(f"\n{trader_instance._get_colored_text('按Enter繼續...', 'cyan')}")
            return

        print(f"{trader_instance._get_colored_text('⚠️  發現缺失依賴:', 'yellow')}")
        for i, dep in enumerate(missing, 1):
            print(f"  {i}. {dep['name']}")
            print(f"     安裝命令: {dep['install_command']}")
            if dep['error']:
                print(f"     錯誤信息: {dep['error']}")

        auto_install = trader_instance._get_user_input("\n是否自動安裝缺失的依賴? (y/n)", ['y', 'n', 'Y', 'N'])

        if auto_install.lower() == 'y':
            print(f"\n{trader_instance._get_colored_text('開始安裝缺失依賴...', 'yellow')}")

            results = self.dependency_manager.install_missing_dependencies(auto_install=True)

            print(f"\n{trader_instance._get_colored_text('安裝結果:', 'bold')}")
            for name, result in results.items():
                if result['success']:
                    print(f"  ✅ {name}: 安裝成功")
                else:
                    print(f"  ❌ {name}: 安裝失敗")
                    if result.get('error'):
                        print(f"     錯誤: {result['error']}")

            print(f"\n{trader_instance._get_colored_text('⚠️  注意事項:', 'yellow')}")
            print("  1. 安裝完成後請重啟程序以載入新依賴")
            print("  2. 某些依賴可能需要系統級別的安裝（如CUDA）")
            print("  3. 如果安裝失敗，請手動運行安裝命令")
        else:
            print(f"\n{trader_instance._get_colored_text('手動安裝指南:', 'yellow')}")
            for dep in missing:
                print(f"  {dep['install_command']}")

        input(f"\n{trader_instance._get_colored_text('按Enter繼續...', 'cyan')}")

    def _show_detailed_info(self, trader_instance):
        """顯示詳細依賴信息"""
        print(f"\n{trader_instance._get_colored_text('🔍 詳細依賴信息', 'bold')}")
        print("="*60)

        deps = self.dependency_manager.dependencies

        # 按類別分組顯示
        categories = {
            '核心依賴': ['pandas', 'numpy', 'requests'],
            '分析引擎': ['vectorbt', 'scipy', 'scikit-learn'],
            'GPU加速': ['cupy', 'numba'],
            '可視化': ['matplotlib', 'plotly', 'seaborn'],
            '界面增強': ['tabulate', 'colorama', 'rich'],
            '系統工具': ['psutil', 'tqdm']
        }

        for category, dep_names in categories.items():
            print(f"\n{trader_instance._get_colored_text(f'📂 {category}:', 'green')}")
            print("-" * 30)

            for dep_name in dep_names:
                if dep_name in deps:
                    dep = deps[dep_name]
                    status_color = 'green' if dep['available'] else 'red'
                    status_text = '✅ 可用' if dep['available'] else '❌ 不可用'

                    print(f"  {dep_name}: {trader_instance._get_colored_text(status_text, status_color)}")

                    if dep['available']:
                        print(f"    版本: {dep['version']}")
                        if dep['features']:
                            print(f"    功能: {', '.join(dep['features'])}")
                    else:
                        if dep['error']:
                            print(f"    錯誤: {dep['error']}")
                        print(f"    安裝: {self.dependency_manager._get_install_command(dep_name)}")

        input(f"\n{trader_instance._get_colored_text('按Enter繼續...', 'cyan')}")

    def _show_system_info(self, trader_instance):
        """顯示系統信息"""
        print(f"\n{trader_instance._get_colored_text('🚀 系統信息', 'bold')}")
        print("="*60)

        info = self.dependency_manager.system_info

        # 系統基本信息
        print(f"\n{trader_instance._get_colored_text('🖥️  系統基本信息:', 'yellow')}")
        print(f"  操作系統: {info['platform']} {info['platform_version']}")
        print(f"  架構: {info['architecture']}")
        print(f"  處理器: {info['processor']}")

        # Python信息
        print(f"\n{trader_instance._get_colored_text('🐍 Python環境:', 'yellow')}")
        print(f"  實現: {info['python_implementation']}")
        print(f"  版本: {info['python_version']}")
        print(f"  執行路徑: {info['python_executable']}")

        # 路徑信息
        print(f"\n{trader_instance._get_colored_text('📁 路徑信息:', 'yellow')}")
        print(f"  當前工作目錄: {sys.path[0] if sys.path else 'N/A'}")
        print(f"  模塊搜索路徑數量: {len(sys.path)}")

        # 環境變量
        import os
        env_vars = ['PYTHONPATH', 'CUDA_HOME', 'PATH', 'VIRTUAL_ENV']
        relevant_env = {k: v for k, v in os.environ.items() if k in env_vars}

        if relevant_env:
            print(f"\n{trader_instance._get_colored_text('🌍 相關環境變量:', 'yellow')}")
            for key, value in relevant_env.items():
                if key == 'PATH':
                    # 只顯示前幾個路徑
                    paths = value.split(os.pathsep)[:3]
                    print(f"  {key}: {os.pathsep.join(paths)}...")
                else:
                    print(f"  {key}: {value}")

        input(f"\n{trader_instance._get_colored_text('按Enter繼續...', 'cyan')}")
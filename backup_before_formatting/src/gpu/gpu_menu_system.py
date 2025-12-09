#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU菜單系統
GPU Menu System

提供用戶友好的GPU設置和配置界面
Provides user-friendly GPU settings and configuration interface
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 修復導入路徑
try:
    from .gpu_acceleration_support import get_gpu_acceleration_manager, GPUSafetyConfig
except ImportError:
    gpu_acceleration_support = None
    get_gpu_acceleration_manager = None
    GPUSafetyConfig = None

try:
    from src.utils.dependency_manager import DependencyManager
except ImportError:
    utils_path = project_root / "src" / "utils"
    sys.path.insert(0, str(utils_path))
    try:
        from dependency_manager import DependencyManager
    except ImportError:
        DependencyManager = None

logger = logging.getLogger(__name__)

class GPUMenuSystem:
    """GPU菜單系統"""

    def __init__(self):
        self.gpu_manager = get_gpu_acceleration_manager() if get_gpu_acceleration_manager else None
        self.dependency_manager = DependencyManager() if DependencyManager else None

    def display_gpu_status_menu(self):
        """顯示GPU狀態菜單"""
        while True:
            self._clear_screen()
            print("=" * 60)
            print("🖥️  GPU加速支持系統")
            print("=" * 60)
            print()

            # 顯示當前狀態
            self._display_current_status()

            print("\n📋 GPU功能菜單:")
            print("1. 📊 查看GPU詳細信息")
            print("2. 🚀 運行性能基準測試")
            print("3. ⚙️  GPU安全設置")
            print("4. 🔧 GPU優化配置")
            print("5. 💾 保存/加載配置")
            print("6. 🧹 清理GPU資源")
            print("7. 📈 查看性能報告")
            print("0. 📱 返回主菜單")
            print("-" * 60)

            choice = input("請選擇操作 (0-7): ").strip()

            if choice == "1":
                self._show_gpu_details()
            elif choice == "2":
                self._run_performance_benchmark()
            elif choice == "3":
                self._show_safety_settings()
            elif choice == "4":
                self._show_optimization_settings()
            elif choice == "5":
                self._config_management()
            elif choice == "6":
                self._cleanup_gpu_resources()
            elif choice == "7":
                self._show_performance_report()
            elif choice == "0":
                break
            else:
                print("⚠️  無效選擇，請重新輸入")
                self._wait_for_enter()

    def _display_current_status(self):
        """顯示當前GPU狀態"""
        status = self.gpu_manager.get_acceleration_status()

        print("📋 當前狀態:")

        # GPU可用性
        gpu_icon = "✅" if status.get("gpu_available", False) else "❌"
        print(f"  {gpu_icon} GPU可用性: {'可用' if status.get('gpu_available', False) else '不可用'}")

        # 安全檢查
        safety_icon = "✅" if status.get("safety_check_passed", False) else "❌"
        print(f"  {safety_icon} 安全檢查: {'通過' if status.get('safety_check_passed', False) else '失敗'}")

        # 加速狀態
        if status.get("status") == "enabled":
            accel_icon = "🚀"
            accel_status = "已啟用"
        elif status.get("status") == "disabled":
            accel_icon = "⏸️"
            accel_status = "已禁用"
        else:
            accel_icon = "⚠️"
            accel_status = "未初始化"

        print(f"  {accel_icon} 加速狀態: {accel_status}")

        # GPU設備信息
        if status.get("performance_profile"):
            profile = status["performance_profile"]
            print(f"  🖥️  設備: {profile['device_name']}")
            print(f"  💾 內存: {profile['memory_available_mb']}/{profile['memory_total_mb']} MB")
            print(f"  ⚡ 計算能力: {profile['compute_capability']}")

        # 內存使用
        memory_usage = status.get("memory_usage", {})
        if "usage_ratio" in memory_usage:
            usage_percent = memory_usage["usage_ratio"] * 100
            memory_bar = self._get_progress_bar(usage_percent, 20)
            print(f"  📊 內存使用: {memory_bar} {usage_percent:.1f}%")

        # 依賴狀態
        dep_status = self.dependency_manager.get_dependency_status()
        print(f"  📦 VectorBT: {'✅' if dep_status.get('vectorbt_available', False) else '❌'}")
        print(f"  📦 CuPy: {'✅' if dep_status.get('gpu_available', False) else '❌'}")

    def _get_progress_bar(self, percentage: float, width: int = 20) -> str:
        """生成進度條"""
        filled = int(percentage * width / 100)
        bar = "█" * filled + "░" * (width - filled)
        return bar

    def _show_gpu_details(self):
        """顯示GPU詳細信息"""
        self._clear_screen()
        print("🖥️  GPU詳細信息")
        print("=" * 50)
        print()

        status = self.gpu_manager.get_acceleration_status()

        if not status.get("gpu_available", False):
            print("❌ GPU不可用")
            print("\n可能的原因:")
            print("- 未安裝CUDA驅動程序")
            print("- 未安裝CuPy")
            print("- 硬件不支持CUDA")
            print()
            self._wait_for_enter()
            return

        if status.get("performance_profile"):
            profile = status["performance_profile"]

            print("📊 設備信息:")
            print(f"  設備名稱: {profile['device_name']}")
            print(f"  設備ID: {profile.get('device_id', 'N/A')}")
            print(f"  計算能力: {profile['compute_capability']}")
            print(f"  多處理器數量: {profile['multiprocessor_count']}")

            print("\n💾 內存信息:")
            print(f"  總內存: {profile['memory_total_mb']:,} MB")
            print(f"  可用內存: {profile['memory_available_mb']:,} MB")
            print(f"  使用率: {((profile['memory_total_mb'] - profile['memory_available_mb']) / profile['memory_total_mb'] * 100):.1f}%")

            print("\n🔧 軟件信息:")
            print(f"  CUDA版本: {profile.get('cuda_version', 'N/A')}")
            print(f"  驅動版本: {profile.get('driver_version', 'N/A')}")

        # 系統信息
        dep_status = self.dependency_manager.get_dependency_status()
        system_info = dep_status.get("system_info", {})

        print("\n🖥️  系統信息:")
        print(f"  操作系統: {system_info.get('platform', 'N/A')}")
        print(f"  Python版本: {system_info.get('python_version', 'N/A')}")

        print()
        self._wait_for_enter()

    def _run_performance_benchmark(self):
        """運行性能基準測試"""
        self._clear_screen()
        print("🚀 性能基準測試")
        print("=" * 50)
        print()

        if not self.gpu_manager.gpu_enabled:
            print("⚠️  GPU未啟用，正在嘗試初始化...")
            if not self.gpu_manager.initialize():
                print("❌ GPU初始化失敗")
                self._wait_for_enter()
                return

        print("正在運行性能基準測試...")
        print("這可能需要幾秒鐘時間...")
        print()

        try:
            # 運行基準測試
            benchmarks = self.gpu_manager.performance_manager.run_comprehensive_benchmark(10000)

            if not benchmarks:
                print("❌ 基準測試失敗")
                self._wait_for_enter()
                return

            print("📊 測試結果:")
            print("-" * 30)

            for test_name, result in benchmarks.items():
                if result.success:
                    speedup_icon = "🚀" if result.speedup_ratio > 2.0 else "📈" if result.speedup_ratio > 1.0 else "⚖️"
                    print(f"  {speedup_icon} {test_name.replace('_', ' ').title()}")
                    print(f"     CPU時間: {result.cpu_time:.4f}s")
                    print(f"     GPU時間: {result.gpu_time:.4f}s")
                    print(f"     加速比: {result.speedup_ratio:.2f}x")
                    print(f"     內存使用: {result.memory_usage_mb:.1f} MB")
                else:
                    print(f"  ❌ {test_name.replace('_', ' ').title()}: {result.error_message}")
                print()

            # 總結
            successful_tests = [b for b in benchmarks.values() if b.success]
            if successful_tests:
                avg_speedup = sum(b.speedup_ratio for b in successful_tests) / len(successful_tests)
                print(f"📈 平均加速比: {avg_speedup:.2f}x")
                print(f"✅ 成功測試: {len(successful_tests)}/{len(benchmarks)}")
            else:
                print("❌ 所有測試均失敗")

        except Exception as e:
            print(f"❌ 基準測試出錯: {e}")

        print()
        self._wait_for_enter()

    def _show_safety_settings(self):
        """顯示安全設置"""
        self._clear_screen()
        print("⚙️  GPU安全設置")
        print("=" * 50)
        print()

        config = self.gpu_manager.config.get("safety", {})

        print("🛡️  當前安全配置:")
        print(f"  1. 最大GPU內存使用率: {config.get('max_gpu_memory_usage', 0.8) * 100:.0f}%")
        print(f"  2. 最大GPU溫度: {config.get('max_gpu_temperature', 85.0):.0f}°C")
        print(f"  3. 內存檢查: {'啟用' if config.get('enable_memory_check', True) else '禁用'}")
        print(f"  4. 溫度檢查: {'啟用' if config.get('enable_temperature_check', True) else '禁用'}")
        print(f"  5. 驅動程序驗證: {'啟用' if config.get('enable_driver_validation', True) else '禁用'}")
        print(f"  6. 自動降級到CPU: {'啟用' if config.get('auto_fallback_to_cpu', True) else '禁用'}")
        print(f"  7. 性能監控: {'啟用' if config.get('performance_monitoring', True) else '禁用'}")

        print("\n🔧 配置選項:")
        print("1. 修改最大內存使用率")
        print("2. 修改最大溫度限制")
        print("3. 切換內存檢查")
        print("4. 切換溫度檢查")
        print("5. 切換驅動程序驗證")
        print("6. 切換自動降級")
        print("7. 切換性能監控")
        print("8. 重置為默認設置")
        print("0. 返回")

        choice = input("\n請選擇操作 (0-8): ").strip()

        if choice == "1":
            self._modify_memory_usage_limit()
        elif choice == "2":
            self._modify_temperature_limit()
        elif choice == "3":
            self._toggle_setting("enable_memory_check")
        elif choice == "4":
            self._toggle_setting("enable_temperature_check")
        elif choice == "5":
            self._toggle_setting("enable_driver_validation")
        elif choice == "6":
            self._toggle_setting("auto_fallback_to_cpu")
        elif choice == "7":
            self._toggle_setting("performance_monitoring")
        elif choice == "8":
            self._reset_safety_settings()
        elif choice == "0":
            return

        self.gpu_manager.save_config()

    def _modify_memory_usage_limit(self):
        """修改最大內存使用率"""
        try:
            current = self.gpu_manager.config.get("safety", {}).get("max_gpu_memory_usage", 0.8)
            new_value = input(f"當前最大內存使用率: {current * 100:.0f}%\n請輸入新的值 (50-95%): ").strip()

            if new_value:
                value = float(new_value)
                if 50 <= value <= 95:
                    self.gpu_manager.config["safety"]["max_gpu_memory_usage"] = value / 100
                    print(f"✅ 已更新為 {value:.0f}%")
                else:
                    print("❌ 值必須在50-95%之間")
        except ValueError:
            print("❌ 輸入無效")

        self._wait_for_enter()

    def _modify_temperature_limit(self):
        """修改最大溫度限制"""
        try:
            current = self.gpu_manager.config.get("safety", {}).get("max_gpu_temperature", 85.0)
            new_value = input(f"當前最大溫度: {current:.0f}°C\n請輸入新的值 (70-90°C): ").strip()

            if new_value:
                value = float(new_value)
                if 70 <= value <= 90:
                    self.gpu_manager.config["safety"]["max_gpu_temperature"] = value
                    print(f"✅ 已更新為 {value:.0f}°C")
                else:
                    print("❌ 值必須在70-90°C之間")
        except ValueError:
            print("❌ 輸入無效")

        self._wait_for_enter()

    def _toggle_setting(self, setting_name: str):
        """切換設置"""
        current = self.gpu_manager.config.get("safety", {}).get(setting_name, True)
        new_value = not current
        self.gpu_manager.config["safety"][setting_name] = new_value

        setting_display = {
            "enable_memory_check": "內存檢查",
            "enable_temperature_check": "溫度檢查",
            "enable_driver_validation": "驅動程序驗證",
            "auto_fallback_to_cpu": "自動降級到CPU",
            "performance_monitoring": "性能監控"
        }

        print(f"✅ {setting_display.get(setting_name, setting_name)}: {'啟用' if new_value else '禁用'}")
        self._wait_for_enter()

    def _reset_safety_settings(self):
        """重置安全設置"""
        confirm = input("確定要重置為默認設置嗎? (y/N): ").strip().lower()
        if confirm == "y":
            self.gpu_manager.config["safety"] = {
                "max_gpu_memory_usage": 0.8,
                "max_gpu_temperature": 85.0,
                "enable_memory_check": True,
                "enable_temperature_check": True,
                "enable_driver_validation": True,
                "auto_fallback_to_cpu": True,
                "performance_monitoring": True
            }
            print("✅ 已重置為默認安全設置")
        else:
            print("❌ 操作已取消")

        self._wait_for_enter()

    def _show_optimization_settings(self):
        """顯示優化設置"""
        self._clear_screen()
        print("🔧 GPU優化配置")
        print("=" * 50)
        print()

        config = self.gpu_manager.config.get("optimization", {})

        print("⚡ 當前優化配置:")
        print(f"  1. 自動選擇模式: {'啟用' if config.get('auto_select_mode', True) else '禁用'}")
        print(f"  2. 優先使用GPU: {'啟用' if config.get('prefer_gpu', True) else '禁用'}")
        print(f"  3. 最小加速比閾值: {config.get('min_speedup_threshold', 1.5):.1f}x")

        print("\n🔧 配置選項:")
        print("1. 切換自動選擇模式")
        print("2. 切換GPU優先")
        print("3. 修改最小加速比閾值")
        print("0. 返回")

        choice = input("\n請選擇操作 (0-3): ").strip()

        if choice == "1":
            self._toggle_optimization_setting("auto_select_mode")
        elif choice == "2":
            self._toggle_optimization_setting("prefer_gpu")
        elif choice == "3":
            self._modify_speedup_threshold()
        elif choice == "0":
            return

        self.gpu_manager.save_config()

    def _toggle_optimization_setting(self, setting_name: str):
        """切換優化設置"""
        current = self.gpu_manager.config.get("optimization", {}).get(setting_name, True)
        new_value = not current
        self.gpu_manager.config["optimization"][setting_name] = new_value

        setting_display = {
            "auto_select_mode": "自動選擇模式",
            "prefer_gpu": "優先使用GPU"
        }

        print(f"✅ {setting_display.get(setting_name, setting_name)}: {'啟用' if new_value else '禁用'}")
        self._wait_for_enter()

    def _modify_speedup_threshold(self):
        """修改最小加速比閾值"""
        try:
            current = self.gpu_manager.config.get("optimization", {}).get("min_speedup_threshold", 1.5)
            new_value = input(f"當前最小加速比閾值: {current:.1f}x\n請輸入新的值 (1.0-5.0): ").strip()

            if new_value:
                value = float(new_value)
                if 1.0 <= value <= 5.0:
                    self.gpu_manager.config["optimization"]["min_speedup_threshold"] = value
                    print(f"✅ 已更新為 {value:.1f}x")
                else:
                    print("❌ 值必須在1.0-5.0之間")
        except ValueError:
            print("❌ 輸入無效")

        self._wait_for_enter()

    def _config_management(self):
        """配置管理"""
        self._clear_screen()
        print("💾 配置管理")
        print("=" * 50)
        print()

        print("🔧 配置選項:")
        print("1. 保存當前配置")
        print("2. 重新加載配置")
        print("3. 導出配置到文件")
        print("4. 從文件導入配置")
        print("0. 返回")

        choice = input("\n請選擇操作 (0-4): ").strip()

        if choice == "1":
            self.gpu_manager.save_config()
            print("✅ 配置已保存")
            self._wait_for_enter()
        elif choice == "2":
            # 重新加載配置
            self.gpu_manager.config = self.gpu_manager._load_config()
            print("✅ 配置已重新加載")
            self._wait_for_enter()
        elif choice == "3":
            self._export_config()
        elif choice == "4":
            self._import_config()
        elif choice == "0":
            return

    def _export_config(self):
        """導出配置"""
        try:
            filename = input("請輸入導出文件名 (默認: gpu_config_export.json): ").strip()
            if not filename:
                filename = "gpu_config_export.json"

            export_path = Path(filename)
            with open(export_path, 'w', encoding='utf-8') as f:
                import json
                json.dump(self.gpu_manager.config, f, indent=2, ensure_ascii=False)

            print(f"✅ 配置已導出到: {export_path.absolute()}")
        except Exception as e:
            print(f"❌ 導出失敗: {e}")

        self._wait_for_enter()

    def _import_config(self):
        """導入配置"""
        try:
            filename = input("請輸入導入文件名: ").strip()
            if not filename:
                print("❌ 文件名不能為空")
                self._wait_for_enter()
                return

            import_path = Path(filename)
            if not import_path.exists():
                print(f"❌ 文件不存在: {import_path}")
                self._wait_for_enter()
                return

            with open(import_path, 'r', encoding='utf-8') as f:
                import json
                new_config = json.load(f)

            # 簡單驗證配置結構
            if not isinstance(new_config, dict):
                print("❌ 無效的配置文件格式")
                self._wait_for_enter()
                return

            confirm = input("確定要導入此配置嗎? 當前配置將被覆蓋 (y/N): ").strip().lower()
            if confirm == "y":
                self.gpu_manager.config = new_config
                self.gpu_manager.save_config()
                print("✅ 配置已導入並保存")
            else:
                print("❌ 操作已取消")

        except Exception as e:
            print(f"❌ 導入失敗: {e}")

        self._wait_for_enter()

    def _cleanup_gpu_resources(self):
        """清理GPU資源"""
        self._clear_screen()
        print("🧹 清理GPU資源")
        print("=" * 50)
        print()

        confirm = input("確定要清理GPU資源嗎? (y/N): ").strip().lower()
        if confirm == "y":
            try:
                print("正在清理GPU資源...")
                self.gpu_manager.cleanup()
                print("✅ GPU資源清理完成")
            except Exception as e:
                print(f"❌ 清理失敗: {e}")
        else:
            print("❌ 操作已取消")

        print()
        self._wait_for_enter()

    def _show_performance_report(self):
        """顯示性能報告"""
        self._clear_screen()
        print("📈 性能報告")
        print("=" * 50)
        print()

        report = self.gpu_manager.get_performance_report()

        if "error" in report:
            print(f"❌ {report['error']}")
            print("請先運行性能基準測試")
            self._wait_for_enter()
            return

        # 顯示總結
        summary = report.get("summary", {})
        print("📊 測試總結:")
        print(f"  總測試數: {summary.get('total_tests', 0)}")
        print(f"  成功測試: {summary.get('successful_tests', 0)}")
        print(f"  失敗測試: {summary.get('failed_tests', 0)}")
        print(f"  成功率: {summary.get('success_rate', 0):.1%}")
        print(f"  平均加速比: {summary.get('average_speedup', 0):.2f}x")
        print(f"  最大加速比: {summary.get('max_speedup', 0):.2f}x")
        print(f"  最小加速比: {summary.get('min_speedup', 0):.2f}x")

        # 內存使用
        memory = report.get("memory_usage", {})
        print(f"\n💾 內存使用:")
        print(f"  平均使用: {memory.get('average_mb', 0):.1f} MB")
        print(f"  峰值使用: {memory.get('peak_mb', 0):.1f} MB")

        # 測試結果詳情
        test_results = report.get("test_results", [])
        if test_results:
            print(f"\n🔍 詳細結果:")
            for result in test_results:
                speedup_icon = "🚀" if result['speedup'] > 2.0 else "📈" if result['speedup'] > 1.0 else "⚖️"
                print(f"  {speedup_icon} {result['name']}: {result['speedup']:.2f}x")

        # 建議
        recommendations = report.get("recommendations", [])
        if recommendations:
            print(f"\n💡 優化建議:")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")

        print()
        self._wait_for_enter()

    def _clear_screen(self):
        """清屏"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def _wait_for_enter(self):
        """等待用戶按回車"""
        input("\n按回車鍵繼續...")

def show_gpu_menu():
    """顯示GPU菜單（便捷函數）"""
    menu_system = GPUMenuSystem()
    menu_system.display_gpu_status_menu()

if __name__ == "__main__":
    # 測試菜單系統
    show_gpu_menu()
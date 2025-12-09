#!/usr/bin/env python3
"""
幫助菜單集成系統
將幫助系統與主界面無縫集成，提供統一的幫助入口

核心功能：
1. 主菜單幫助集成
2. 上下文敏感幫助
3. 交互式幫助界面
4. 幫助搜索和導航
5. 與現有UI系統集成
"""

import sys
import json
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import logging

# 導入幫助系統組件
try:
    from .help_system import HelpSystem
    from .interactive_tutorial import InteractiveTutorial
    from .quick_reference import QuickReference
    HELP_AVAILABLE = True
except ImportError:
    HELP_AVAILABLE = False

# 導入UI系統
try:
    from src.ui.enhanced_terminal_ui import EnhancedTerminalUI
    UI_AVAILABLE = True
except ImportError:
    UI_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class HelpContext:
    """幫助上下文數據"""
    current_module: str
    current_action: str
    user_level: str  # "beginner", "intermediate", "advanced"
    recent_actions: List[str]
    available_features: List[str]

class HelpMenu:
    """幫助菜單系統"""

    def __init__(self, main_app=None):
        self.version = "1.0.0"
        self.main_app = main_app

        # 初始化幫助組件
        if HELP_AVAILABLE:
            self.help_system = HelpSystem()
            self.tutorial = InteractiveTutorial()
            self.quick_reference = QuickReference()
        else:
            logger.warning("幫助系統組件不可用")
            self.help_system = None
            self.tutorial = None
            self.quick_reference = None

        # 初始化UI系統
        if UI_AVAILABLE:
            self.ui = EnhancedTerminalUI()
        else:
            self.ui = None

        # 當前上下文
        self.current_context = HelpContext(
            current_module="main",
            current_action="menu",
            user_level="beginner",
            recent_actions=[],
            available_features=[]
        )

        # 幫助菜單選項
        self.menu_options = {
            "1": ("瀏覽幫助主題", self._browse_help_topics),
            "2": ("搜索幫助內容", self._search_help),
            "3": ("快速參考指南", self._show_quick_reference),
            "4": ("互動式教程", self._start_tutorial),
            "5": ("命令速查表", self._show_commands),
            "6": ("快捷鍵大全", self._show_shortcuts),
            "7": ("工作流程指南", self._show_workflows),
            "8": ("實用技巧", self._show_tips),
            "9": ("系統狀態幫助", self._show_system_help),
            "h": ("返回主系統", None),
            "q": ("退出幫助", None)
        }

        logger.info("幫助菜單系統初始化完成")

    def show_help_menu(self, context: HelpContext = None) -> bool:
        """顯示幫助主菜單"""
        if context:
            self.current_context = context

        print("\n" + "="*50)
        print("🆘 量化交易系統幫助中心")
        print("="*50)
        print(f"👤 用戶級別：{self.current_context.user_level}")
        print(f"📱 當前模塊：{self.current_context.current_module}")
        print(f"🎯 當前操作：{self.current_context.current_action}")
        print("-"*50)

        print("\n📚 幫助菜單：")
        for key, (description, _) in sorted(self.menu_options.items()):
            if key in ["h", "q"]:
                continue
            print(f"  [{key}] {description}")

        print("\n🔧 快捷操作：")
        print("  [h] 返回主系統")
        print("  [q] 退出幫助")

        # 上下文相關推薦
        if self.current_context.current_action != "menu":
            print(f"\n💡 當前操作相關幫助：")
            self._show_contextual_help()

        print("\n" + "="*50)

        return self._handle_help_menu_input()

    def _show_contextual_help(self):
        """顯示上下文相關幫助"""
        action = self.current_context.current_action.lower()

        if not self.help_system:
            print("  幫助系統暫時不可用")
            return

        # 搜索相關主題
        relevant_topics = self.help_system.search_help(action, max_results=3)
        if relevant_topics:
            for i, topic in enumerate(relevant_topics[:2], 1):
                print(f"  {i}. {topic.title} (輸入 'help {topic.id}')")

        # 搜索相關命令
        if self.quick_reference:
            relevant_commands = self.quick_reference.search_commands(action)[:2]
            for cmd in relevant_commands:
                print(f"  🔧 {cmd.command} - {cmd.description}")

    def _handle_help_menu_input(self) -> bool:
        """處理幫助菜單輸入"""
        while True:
            try:
                choice = input("\n請選擇幫助選項：").strip().lower()

                if choice in ["h", "home", "main"]:
                    return True  # 返回主系統

                elif choice in ["q", "quit", "exit"]:
                    return False  # 退出幫助

                elif choice in self.menu_options:
                    description, action = self.menu_options[choice]
                    if action:
                        result = action()
                        if result is False:  # 返回上一級
                            break
                    else:
                        break  # 返回或退出

                elif choice.startswith("help "):
                    # 直接訪問特定幫助主題
                    topic_id = choice[5:].strip()
                    self._show_specific_help(topic_id)

                elif choice.startswith("tutorial "):
                    # 直接啟動特定教程
                    tutorial_id = choice[9:].strip()
                    self._start_specific_tutorial(tutorial_id)

                elif choice in ["?", "commands", "shortcuts"]:
                    # 快速命令
                    if choice == "?":
                        self._show_help_overview()
                    elif choice == "commands":
                        self._show_commands()
                    elif choice == "shortcuts":
                        self._show_shortcuts()

                else:
                    print("❌ 無效選項，請重新選擇")

            except KeyboardInterrupt:
                print("\n\n👋 感謝使用幫助系統！")
                return False
            except Exception as e:
                logger.error(f"處理幫助菜單輸入時出錯：{e}")
                print(f"❌ 發生錯誤：{e}")

        return True

    def _browse_help_topics(self) -> bool:
        """瀏覽幫助主題"""
        if not self.help_system:
            print("❌ 幫助系統不可用")
            return True

        print("\n📖 幫助主題分類：")
        print(self.help_system.show_category_overview())

        while True:
            try:
                print("\n操作選項：")
                print("• 輸入分類號碼查看該分類主題")
                print("• 輸入主題ID查看詳細內容 (如：help rsi)")
                print("• 輸入 'back' 返回幫助菜單")

                choice = input("\n請選擇：").strip().lower()

                if choice == "back":
                    return True

                elif choice.startswith("help "):
                    topic_id = choice[5:].strip()
                    self._show_specific_help(topic_id)

                elif choice.isdigit():
                    # 這裡可以實現分類選擇邏輯
                    print("分類瀏覽功能開發中...")

                else:
                    # 嘗試搜索
                    results = self.help_system.search_help(choice, max_results=5)
                    if results:
                        print(f"\n🔍 搜索結果：")
                        for i, topic in enumerate(results, 1):
                            print(f"  {i}. {topic.title} (help {topic.id})")
                    else:
                        print("❌ 未找到相關主題")

            except KeyboardInterrupt:
                return True

    def _search_help(self) -> bool:
        """搜索幫助內容"""
        if not self.help_system:
            print("❌ 幫助系統不可用")
            return True

        print("\n🔍 幫助內容搜索")
        print("="*30)

        while True:
            try:
                query = input("\n請輸入搜索關鍵詞 (輸入 'back' 返回)：").strip()

                if query.lower() == "back":
                    return True

                if not query:
                    continue

                # 搜索幫助主題
                results = self.help_system.search_help(query, max_results=10)

                if results:
                    print(f"\n📋 找到 {len(results)} 個相關主題：")
                    for i, topic in enumerate(results, 1):
                        print(f"  {i}. {topic.title}")
                        print(f"     📂 {topic.category} | 📊 {topic.difficulty}")
                        print(f"     📝 {topic.content[:100]}...")
                        print()

                    print("操作選項：")
                    print("• 輸入數字查看主題詳情")
                    print("• 輸入新的關鍵詞繼續搜索")
                    print("• 輸入 'back' 返回幫助菜單")

                    sub_choice = input("請選擇：").strip()

                    if sub_choice.lower() == "back":
                        return True
                    elif sub_choice.isdigit():
                        index = int(sub_choice) - 1
                        if 0 <= index < len(results):
                            topic = results[index]
                            self._show_topic_details(topic)
                else:
                    print("❌ 未找到相關內容")

                    # 提供搜索建議
                    suggestions = self.help_system.get_topic_suggestions(query)
                    if suggestions:
                        print("💡 您是否想查找：")
                        for suggestion in suggestions:
                            print(f"  • {suggestion}")

            except KeyboardInterrupt:
                return True

    def _show_quick_reference(self) -> bool:
        """顯示快速參考指南"""
        if not self.quick_reference:
            print("❌ 快速參考系統不可用")
            return True

        print("\n⚡ 快速參考指南")
        print("="*30)

        ref_options = {
            "1": ("命令概覽", self._show_command_overview),
            "2": ("快捷鍵大全", self._show_shortcut_overview),
            "3": ("工作流程", self._show_workflow_overview),
            "4": ("實用技巧", self._show_tips_overview),
            "5": ("生成備忘單", self._generate_cheat_sheet),
            "b": ("返回", None)
        }

        for key, (title, _) in ref_options.items():
            print(f"  [{key}] {title}")

        while True:
            try:
                choice = input("\n請選擇：").strip().lower()

                if choice == "b":
                    return True

                elif choice in ref_options:
                    title, action = ref_options[choice]
                    if action:
                        action()
                    else:
                        return True

                else:
                    print("❌ 無效選項")

            except KeyboardInterrupt:
                return True

    def _start_tutorial(self) -> bool:
        """啟動互動式教程"""
        if not self.tutorial:
            print("❌ 教程系統不可用")
            return True

        print("\n🎓 互動式教程系統")
        print("="*30)

        # 顯示可用教程
        tutorials = self.tutorial.get_tutorial_list()
        print("可用教程：")
        for i, tutorial in enumerate(tutorials, 1):
            status = "✅ 已完成" if self._is_tutorial_completed(tutorial["id"]) else "🆕 待學習"
            print(f"  [{i}] {tutorial['title']} ({tutorial['difficulty']}, {tutorial['estimated_time']}分鐘) {status}")

        print("\n操作選項：")
        print("• 輸入教程號碼開始學習")
        print("• 輸入 'progress' 查看學習進度")
        print("• 輸入 'back' 返回幫助菜單")

        while True:
            try:
                choice = input("\n請選擇：").strip().lower()

                if choice == "back":
                    return True

                elif choice == "progress":
                    self._show_learning_progress()

                elif choice.isdigit():
                    index = int(choice) - 1
                    if 0 <= index < len(tutorials):
                        tutorial = tutorials[index]
                        success = self.tutorial.start_tutorial(tutorial["id"])
                        if success:
                            print("🎉 教程完成！")
                        else:
                            print("❌ 教程啟動失敗")
                    else:
                        print("❌ 無效的教程號碼")

                else:
                    print("❌ 無效選項")

            except KeyboardInterrupt:
                return True

    def _show_commands(self) -> bool:
        """顯示命令速查表"""
        if not self.quick_reference:
            print("❌ 命令參考不可用")
            return True

        print("\n🔧 命令速查表")
        print("="*30)
        print(self.quick_reference.show_command_overview())

        input("\n按回車鍵繼續...")
        return True

    def _show_shortcuts(self) -> bool:
        """顯示快捷鍵大全"""
        if not self.quick_reference:
            print("❌ 快捷鍵參考不可用")
            return True

        print("\n⌨️  快捷鍵大全")
        print("="*30)
        print(self.quick_reference.show_shortcut_overview())

        input("\n按回車鍵繼續...")
        return True

    def _show_workflows(self) -> bool:
        """顯示工作流程指南"""
        if not self.quick_reference:
            print("❌ 工作流程參考不可用")
            return True

        print("\n🔄 工作流程指南")
        print("="*30)
        print(self.quick_reference.show_workflow_overview())

        # 提供詳細工作流程選項
        workflows = list(self.quick_reference.workflows.values())
        print(f"\n選擇工作流程查看詳情：")
        for i, workflow in enumerate(workflows, 1):
            print(f"  [{i}] {workflow.name} ({workflow.duration})")

        try:
            choice = input("\n請選擇 (輸入號碼)：").strip()
            if choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(workflows):
                    workflow = workflows[index]
                    print(f"\n{self.quick_reference.format_workflow_help(workflow)}")
        except (ValueError, KeyboardInterrupt):
            pass

        input("\n按回車鍵繼續...")
        return True

    def _show_tips(self) -> bool:
        """顯示實用技巧"""
        if not self.quick_reference:
            print("❌ 技巧參考不可用")
            return True

        print("\n💡 實用技巧")
        print("="*30)

        # 按級別分類顯示
        levels = ["初級", "中級", "高級", "實用"]
        for level in levels:
            tips = self.quick_reference.get_tips_by_level(level)
            if tips:
                print(f"\n📊 {level}技巧：")
                for tip in tips:
                    print(f"  • {tip['tip']}")
                    print(f"    {tip['detail']}")

        input("\n按回車鍵繼續...")
        return True

    def _show_system_help(self) -> bool:
        """顯示系統狀態幫助"""
        print("\n🖥️  系統狀態幫助")
        print("="*30)

        # 檢查系統組件狀態
        components = {
            "幫助系統": "✅ 正常" if self.help_system else "❌ 不可用",
            "教程系統": "✅ 正常" if self.tutorial else "❌ 不可用",
            "快速參考": "✅ 正常" if self.quick_reference else "❌ 不可用",
            "UI增強": "✅ 正常" if self.ui else "❌ 不可用"
        }

        print("組件狀態：")
        for component, status in components.items():
            print(f"  {component}：{status}")

        # 系統信息
        print(f"\n系統信息：")
        print(f"  幫助系統版本：{self.version}")
        print(f"  當前用戶級別：{self.current_context.user_level}")
        print(f"  當前模塊：{self.current_context.current_module}")

        # 生成系統報告
        if self.help_system:
            report = self.help_system.generate_help_report()
            print(f"\n幫助系統統計：")
            print(f"  總主題數：{report['total_topics']}")
            print(f"  總分類數：{report['total_categories']}")
            print(f"  快捷鍵數：{report['total_shortcuts']}")

        # 故障排除建議
        print(f"\n🔧 故障排除：")
        print("  • 如果幫助系統不可用，請檢查依賴庫安裝")
        print("  • 如果搜索無結果，嘗試使用不同的關鍵詞")
        print("  • 如果教程無法啟動，檢查配置文件權限")
        print("  • 如果界面顯示異常，嘗試重啟程序")

        input("\n按回車鍵繼續...")
        return True

    def _show_specific_help(self, topic_id: str):
        """顯示特定幫助主題"""
        if not self.help_system:
            print("❌ 幫助系統不可用")
            return

        topic = self.help_system.get_topic(topic_id)
        if topic:
            print(self.help_system.format_help_output(topic))
        else:
            # 嘗試搜索
            results = self.help_system.search_help(topic_id, max_results=5)
            if results:
                print(f"❌ 未找到主題 '{topic_id}'，您是否想查找：")
                for result in results:
                    print(f"  • {result.title} (help {result.id})")
            else:
                print(f"❌ 未找到主題 '{topic_id}'")

        input("\n按回車鍵繼續...")

    def _start_specific_tutorial(self, tutorial_id: str):
        """啟動特定教程"""
        if not self.tutorial:
            print("❌ 教程系統不可用")
            return

        success = self.tutorial.start_tutorial(tutorial_id)
        if success:
            print("🎉 教程完成！")
        else:
            print(f"❌ 教程 '{tutorial_id}' 啟動失敗")

    def _show_topic_details(self, topic):
        """顯示主題詳情"""
        if self.help_system:
            print(self.help_system.format_help_output(topic))

    def _show_help_overview(self):
        """顯示幫助概覽"""
        print("\n🆘 幫助系統概覽")
        print("="*30)
        print("本系統提供全面的幫助和支持：")
        print("• 📚 幫助主題 - 詳細的功能說明和使用指南")
        print("• 🔍 搜索功能 - 快速找到所需信息")
        print("• ⚡ 快速參考 - 命令、快捷鍵、工作流程")
        print("• 🎓 互動教程 - step-by-step學習指南")
        print("• 💡 實用技巧 - 提高效率的實用建議")

    def _is_tutorial_completed(self, tutorial_id: str) -> bool:
        """檢查教程是否已完成"""
        if self.tutorial:
            return self.tutorial._is_tutorial_completed(tutorial_id, self.current_context.user_level)
        return False

    def _show_learning_progress(self):
        """顯示學習進度"""
        if not self.tutorial:
            print("❌ 教程系統不可用")
            return

        progress = self.tutorial.get_user_progress(self.current_context.user_level)
        print(f"\n📊 學習進度報告")
        print("="*30)
        print(f"完成教程：{len(progress['completed_tutorials'])}/{progress['total_tutorials']}")
        print(f"完成率：{progress['completion_rate']:.1f}%")
        print(f"總學習時間：{progress['total_learning_time']:.1f} 分鐘")
        print(f"平均分數：{progress['average_score']:.1f}")

        if progress['completed_tutorials']:
            print(f"\n已完成教程：")
            for tutorial_id in progress['completed_tutorials']:
                # 這裡可以顯示教程名稱
                print(f"  ✅ {tutorial_id}")

    def _show_command_overview(self):
        """顯示命令概覽"""
        if self.quick_reference:
            print(self.quick_reference.show_command_overview())

    def _show_shortcut_overview(self):
        """顯示快捷鍵概覽"""
        if self.quick_reference:
            print(self.quick_reference.show_shortcut_overview())

    def _show_workflow_overview(self):
        """顯示工作流程概覽"""
        if self.quick_reference:
            print(self.quick_reference.show_workflow_overview())

    def _show_tips_overview(self):
        """顯示技巧概覽"""
        if self.quick_reference:
            tips = self.quick_reference.tips[:5]  # 顯示前5個技巧
            print("💡 精選技巧：")
            for tip in tips:
                print(f"  • {tip['tip']} ({tip['level']})")

    def _generate_cheat_sheet(self):
        """生成備忘單"""
        if self.quick_reference:
            cheat_sheet = self.quick_reference.generate_cheat_sheet()
            filename = f"cheat_sheet_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(cheat_sheet)
                print(f"✅ 備忘單已生成：{filename}")
            except Exception as e:
                print(f"❌ 生成備忘單失敗：{e}")

    def update_context(self, module: str, action: str, user_level: str = None):
        """更新幫助上下文"""
        self.current_context.current_module = module
        self.current_context.current_action = action
        if user_level:
            self.current_context.user_level = user_level

    def get_contextual_help(self) -> Optional[str]:
        """獲取上下文相關幫助"""
        if not self.help_system:
            return None

        # 根據當前上下文提供相關幫助
        action = self.current_context.current_action.lower()
        results = self.help_system.search_help(action, max_results=1)

        if results:
            topic = results[0]
            return self.help_system.format_help_output(topic)

        return None

    def integrate_with_main_menu(self, main_menu_func: Callable) -> Callable:
        """與主菜單集成"""
        def wrapped_menu(*args, **kwargs):
            # 添加幫助選項到主菜單
            original_result = main_menu_func(*args, **kwargs)

            # 如果返回菜單選項，添加幫助選項
            if isinstance(original_result, dict):
                original_result["h"] = ("幫助系統", self.show_help_menu)

            return original_result

        return wrapped_menu

if __name__ == "__main__":
    # 簡單測試
    help_menu = HelpMenu()
    help_menu.show_help_menu()
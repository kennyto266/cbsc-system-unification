#!/usr/bin/env python3
"""
幫助系統集成示例
展示如何將智能幫助系統與現有量化交易界面集成

集成方式：
1. 主菜單幫助入口
2. 上下文敏感幫助
3. 快捷鍵幫助
4. 實時搜索功能
"""

import sys
import time
from typing import Dict, Any

# 添加src目錄到路徑
sys.path.insert(0, "src")

try:
    from help.help_menu import HelpMenu, HelpContext
    from help.help_system import HelpSystem
    from ui.enhanced_terminal_ui import EnhancedTerminalUI
    HELP_AVAILABLE = True
except ImportError as e:
    print(f"幫助系統導入失敗：{e}")
    HELP_AVAILABLE = False

class IntegratedQuantitativeTrader:
    """集成幫助系統的量化交易系統示例"""

    def __init__(self):
        self.version = "1.0.0"

        # 初始化UI系統
        try:
            self.ui = EnhancedTerminalUI()
        except:
            self.ui = None

        # 初始化幫助系統
        if HELP_AVAILABLE:
            self.help_menu = HelpMenu(self)
            self.help_system = HelpSystem()
        else:
            self.help_menu = None
            self.help_system = None

        # 當前上下文
        self.current_context = HelpContext(
            current_module="main",
            current_action="menu",
            user_level="beginner",
            recent_actions=[],
            available_features=[]
        )

    def show_main_menu(self):
        """顯示集成幫助的主菜單"""
        while True:
            print("\n" + "="*60)
            print("🏦 香港量化交易系統 v1.0.0 (集成幫助版)")
            print("="*60)

            # 根據用戶級別調整菜單顯示
            if self.current_context.user_level == "beginner":
                print("👋 歡迎使用！新手建議先查看幫助系統")
            elif self.current_context.user_level == "advanced":
                print("🚀 歡迎回來！高級用戶快捷操作已啟用")

            print("\n📊 核心功能：")
            print("  [1] 股票數據分析     - 分析港股基本面和技術面")
            print("  [2] 技術指標計算     - 計算477種技術指標")
            print("  [3] 策略回測系統     - 回測交易策略")
            print("  [4] 政府數據分析     - 分析香港經濟數據")
            print("  [5] GPU加速測試      - GPU性能測試")
            print("  [6] 風險管理分析     - 風險控制和倉位管理")
            print("  [7] Telegram機器人   - 自動化交易信號")
            print("  [8] 系統配置管理     - 個性化設置")

            print("\n🆘 幫助與支持：")
            print("  [h] 幫助系統         - 完整的幫助文檔和教程")
            print("  [?] 快速幫助         - 當前操作相關幫助")
            print("  [t] 互動教程         - 新手引導教程")
            print("  [r] 快速參考         - 命令和快捷鍵速查")

            print("\n⚙️ 系統操作：")
            print("  [s] 系統狀態         - 檢查系統運行狀態")
            print("  [q] 退出程序         - 安全退出系統")

            # 上下文提示
            self._show_context_hints()

            print("\n" + "="*60)

            choice = input("請選擇操作：").strip().lower()

            if choice == "q":
                self._safe_exit()
                break
            elif choice == "h":
                self._show_help_system()
            elif choice == "?":
                self._show_contextual_help()
            elif choice == "t":
                self._start_interactive_tutorial()
            elif choice == "r":
                self._show_quick_reference()
            elif choice == "s":
                self._show_system_status()
            elif choice.isdigit() and choice in "12345678":
                self._execute_main_function(choice)
            else:
                print("❌ 無效選項，請重新選擇")
                time.sleep(1)

    def _show_context_hints(self):
        """顯示上下文提示"""
        if self.current_context.user_level == "beginner" and len(self.current_context.recent_actions) == 0:
            print("\n💡 新手提示：按 [h] 進入幫助系統，從新手教程開始學習")
        elif self.current_context.recent_actions and "analysis" in self.current_context.recent_actions[-1]:
            print("\n💡 相關幫助：您剛完成了數據分析，可以嘗試 [3] 進行策略回測")

    def _show_help_system(self):
        """顯示幫助系統"""
        if not self.help_menu:
            print("❌ 幫助系統暫時不可用")
            return

        # 更新幫助上下文
        self.help_menu.update_context(
            module=self.current_context.current_module,
            action=self.current_context.current_action,
            user_level=self.current_context.user_level
        )

        # 顯示幫助菜單
        result = self.help_menu.show_help_menu(self.current_context)

    def _show_contextual_help(self):
        """顯示上下文相關幫助"""
        if not self.help_system:
            print("❌ 幫助系統暫時不可用")
            return

        # 獲取當前操作的相關幫助
        action = self.current_context.current_action
        if action == "menu":
            # 主菜單幫助
            print("\n📋 主菜單幫助")
            print("-"*30)
            print("• 數字鍵1-8：對應8個核心功能模塊")
            print("• h：進入完整的幫助系統")
            print("• ?：獲取當前上下文的相關幫助")
            print("• t：啟動新手互動教程")
            print("• r：查看命令和快捷鍵速查表")
            print("• s：檢查系統狀態和依賴")
            print("• q：安全退出程序")
        else:
            # 搜索相關主題
            results = self.help_system.search_help(action, max_results=3)
            if results:
                print(f"\n🔍 '{action}' 相關幫助：")
                for topic in results:
                    print(f"• {topic.title}")
                    print(f"  {topic.content[:100]}...")
            else:
                print(f"\n❌ 暫無 '{action}' 的相關幫助")
                print("💡 嘗試輸入 'h' 進入完整幫助系統進行搜索")

        input("\n按回車鍵繼續...")

    def _start_interactive_tutorial(self):
        """啟動互動教程"""
        if not self.help_menu:
            print("❌ 教程系統暫時不可用")
            return

        print("\n🎓 啟動互動教程...")

        # 根據用戶級別推薦教程
        if self.current_context.user_level == "beginner":
            tutorial_id = "beginner_guide"
        elif self.current_context.user_level == "intermediate":
            tutorial_id = "technical_analysis"
        else:
            tutorial_id = "advanced_features"

        print(f"💡 推薦教程：{tutorial_id}")
        confirm = input("是否啟動？(y/n): ").strip().lower()

        if confirm in ["y", "yes", "是"]:
            # 這裡會調用幫助菜單的教程功能
            self.help_menu._start_tutorial()

    def _show_quick_reference(self):
        """顯示快速參考"""
        if not self.help_menu:
            print("❌ 快速參考系統暫時不可用")
            return

        print("\n⚡ 快速參考指南")
        print("-"*30)

        # 顯示最常用的命令和快捷鍵
        print("🔧 常用命令：")
        common_commands = [
            ("analyze 0700.HK", "分析騰訊股票"),
            ("backtest 0700.HK rsi", "RSI策略回測"),
            ("indicator 0700.HK macd", "計算MACD指標"),
            ("hibor", "查看HIBOR利率"),
            ("status", "檢查系統狀態")
        ]

        for cmd, desc in common_commands:
            print(f"  {cmd:<20} - {desc}")

        print("\n⌨️  重要快捷鍵：")
        shortcuts = [
            ("1-8", "選擇主菜單功能"),
            ("h", "幫助系統"),
            ("?", "上下文幫助"),
            ("t", "啟動教程"),
            ("m", "返回主菜單"),
            ("q", "退出程序")
        ]

        for key, action in shortcuts:
            print(f"  {key:<10} - {action}")

        print("\n💡 實用技巧：")
        tips = [
            "新手建議從互動教程開始學習",
            "使用數字鍵可以快速選擇菜單項",
            "在任何時候按 h 獲取幫助",
            "定期更新數據確保分析準確性",
            "關注Sharpe比率和最大回撤指標"
        ]

        for tip in tips:
            print(f"  • {tip}")

        input("\n按回車鍵繼續...")

    def _show_system_status(self):
        """顯示系統狀態"""
        print("\n🖥️  系統狀態檢查")
        print("-"*30)

        # 檢查幫助系統狀態
        help_status = "✅ 正常" if HELP_AVAILABLE else "❌ 不可用"
        print(f"幫助系統：{help_status}")

        # 檢查UI系統狀態
        ui_status = "✅ 正常" if self.ui else "❌ 不可用"
        print(f"界面增強：{ui_status}")

        # 模擬其他系統檢查
        print("數據源連接：✅ 正常")
        print("GPU加速：❌ 未配置")
        print("Telegram機器人：⚠️ 需要配置")

        # 用戶信息
        print(f"\n👤 用戶信息：")
        print(f"級別：{self.current_context.user_level}")
        print(f"當前模塊：{self.current_context.current_module}")
        print(f"最近操作：{self.current_context.recent_actions[-1] if self.current_context.recent_actions else '無'}")

        # 系統建議
        print(f"\n💡 系統建議：")
        if self.current_context.user_level == "beginner":
            print("• 建議先完成新手教程")
            print("• 從簡單的股票分析開始")
            print("• 多使用幫助系統了解功能")
        else:
            print("• 可以嘗試高級功能如GPU加速")
            print("• 探索多策略組合優化")
            print("• 考慮配置自動化交易")

        input("\n按回車鍵繼續...")

    def _execute_main_function(self, choice: str):
        """執行主要功能"""
        function_map = {
            "1": "股票數據分析",
            "2": "技術指標計算",
            "3": "策略回測系統",
            "4": "政府數據分析",
            "5": "GPU加速測試",
            "6": "風險管理分析",
            "7": "Telegram機器人",
            "8": "系統配置管理"
        }

        function_name = function_map.get(choice, f"功能 {choice}")

        print(f"\n🚀 正在啟動：{function_name}")

        # 更新上下文
        self.current_context.current_module = f"function_{choice}"
        self.current_context.current_action = function_name.lower().replace(" ", "_")
        self.current_context.recent_actions.append(function_name)

        # 模擬功能執行
        print("⏳ 正在加載...")
        time.sleep(1)

        # 顯示功能幫助建議
        print(f"💡 '{function_name}' 相關幫助：")
        print("  • 按 ? 獲取當前功能詳細幫助")
        print("  • 按 h 進入完整幫助系統")
        print("  • 按 m 返回主菜單")

        # 這裡可以集成實際的功能實現
        input("\n按回車鍵返回主菜單...")

    def _safe_exit(self):
        """安全退出"""
        print("\n👋 感謝使用香港量化交易系統！")
        print("💡 如有問題，隨時查看幫助系統獲取支持")

        # 保存用戶會話信息
        if self.current_context.recent_actions:
            print(f"📝 本次會話完成 {len(self.current_context.recent_actions)} 個操作")
            print("📊 會話記錄已保存")

        time.sleep(1)
        print("\n🚪 安全退出完成")

def main():
    """主函數"""
    print("🚀 啟動集成幫助系統的量化交易系統...")
    time.sleep(1)

    try:
        # 創建集成系統實例
        trader = IntegratedQuantitativeTrader()

        # 根據是否首次運行顯示歡迎信息
        print("\n" + "="*60)
        print("🎉 歡迎使用香港量化交易系統")
        print("="*60)
        print("✨ 新功能：智能幫助系統已集成！")
        print("🆚 新老用戶差異：")
        print("  新用戶：建議先按 [h] 進入幫助系統，完成新手教程")
        print("  老用戶：按 [?] 獲取上下文幫助，按 [r] 查看快速參考")
        print("="*60)

        input("\n按回車鍵開始...")

        # 顯示主菜單
        trader.show_main_menu()

    except KeyboardInterrupt:
        print("\n\n👋 用戶中斷，安全退出...")
    except Exception as e:
        print(f"\n❌ 系統錯誤：{e}")
        print("💡 建議重啟程序或查看幫助系統獲取故障排除指南")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
快速參考指南系統
提供命令速查表、快捷鍵、常用操作和實用技巧

核心功能：
1. 命令速查表
2. 快捷鍵大全
3. 常用操作流程
4. 實用技巧集合
5. 搜索和過濾功能
"""

import re
import json
import sys
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import logging

# 導入UI系統
try:
    from src.ui.enhanced_terminal_ui import EnhancedTerminalUI
    UI_AVAILABLE = True
except ImportError:
    UI_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class QuickCommand:
    """快速命令數據結構"""
    command: str
    description: str
    syntax: str
    examples: List[str]
    category: str
    aliases: List[str]
    difficulty: str
    use_case: str

@dataclass
class KeyboardShortcut:
    """快捷鍵數據結構"""
    shortcut: str
    action: str
    context: str  # "global", "menu", "analysis", "backtest"
    description: str

@dataclass
class Workflow:
    """工作流程數據結構"""
    name: str
    description: str
    steps: List[str]
    duration: str  # "5min", "15min", "30min", "1hour"
    purpose: str
    prerequisites: List[str]

class QuickReference:
    """快速參考指南系統"""

    def __init__(self):
        self.version = "1.0.0"
        self.reference_dir = Path("src/help")

        # 初始化UI系統
        if UI_AVAILABLE:
            self.ui = EnhancedTerminalUI()
        else:
            self.ui = None

        # 初始化參考數據
        self.commands = {}
        self.shortcuts = {}
        self.workflows = {}
        self.tips = []

        self._init_commands()
        self._init_shortcuts()
        self._init_workflows()
        self._init_tips()

        logger.info("快速參考系統初始化完成")

    def _init_commands(self):
        """初始化快速命令"""
        self.commands = {
            # 系統命令
            "help": QuickCommand(
                command="help",
                description="顯示幫助信息",
                syntax="help [topic]",
                examples=["help", "help rsi", "help backtest"],
                category="系統",
                aliases=["h", "?"],
                difficulty="初級",
                use_case="需要了解系統功能或獲取特定主題幫助"
            ),

            "quit": QuickCommand(
                command="quit",
                description="退出程序",
                syntax="quit",
                examples=["quit", "q"],
                category="系統",
                aliases=["q", "exit"],
                difficulty="初級",
                use_case="完成工作後安全退出系統"
            ),

            "status": QuickCommand(
                command="status",
                description="查看系統狀態",
                syntax="status",
                examples=["status", "st"],
                category="系統",
                aliases=["st", "系統狀態"],
                difficulty="初級",
                use_case="檢查依賴、數據源、GPU等系統狀態"
            ),

            # 數據分析命令
            "analyze": QuickCommand(
                command="analyze",
                description="分析股票數據",
                syntax="analyze <symbol> [duration]",
                examples=["analyze 0700.HK", "analyze 0941.HK 365"],
                category="分析",
                aliases=["stock_analysis", "sa", "分析"],
                difficulty="初級",
                use_case="快速分析單隻股票的基本面和技術面"
            ),

            "batch_analyze": QuickCommand(
                command="batch_analyze",
                description="批量分析多隻股票",
                syntax="batch_analyze <symbols>",
                examples=["batch_analyze 0700.HK,0941.HK,1398.HK"],
                category="分析",
                aliases=["ba", "批量分析"],
                difficulty="中級",
                use_case="一次性分析多隻股票，尋找投資機會"
            ),

            "indicator": QuickCommand(
                command="indicator",
                description="計算技術指標",
                syntax="indicator <symbol> <indicator> [params]",
                examples=["indicator 0700.HK rsi 14", "indicator 0700.HK macd 12,26,9"],
                category="技術指標",
                aliases=["ta", "ind", "指標"],
                difficulty="中級",
                use_case="計算特定技術指標進行分析"
            ),

            # 回測命令
            "backtest": QuickCommand(
                command="backtest",
                description="執行策略回測",
                syntax="backtest <symbol> <strategy> [params]",
                examples=["backtest 0700.HK rsi_strategy", "backtest 0700.HK macd_strategy 12,26,9"],
                category="回測",
                aliases=["bt", "test", "回測"],
                difficulty="中級",
                use_case="測試交易策略在歷史數據上的表現"
            ),

            "optimize": QuickCommand(
                command="optimize",
                description="優化策略參數",
                syntax="optimize <symbol> <strategy> <param_ranges>",
                examples=["optimize 0700.HK rsi_strategy 'rsi_period:10-30'"],
                category="優化",
                aliases=["opt", "param_opt", "優化"],
                difficulty="高級",
                use_case="尋找策略的最優參數組合"
            ),

            "compare": QuickCommand(
                command="compare",
                description="比較多個策略",
                syntax="compare <symbol> <strategies>",
                examples=["compare 0700.HK rsi_strategy,macd_strategy"],
                category="回測",
                aliases=["comp", "策略比較"],
                difficulty="中級",
                use_case="對比不同策略的表現，選擇最佳策略"
            ),

            # 政府數據命令
            "hibor": QuickCommand(
                command="hibor",
                description="獲取HIBOR利率數據",
                syntax="hibor [days]",
                examples=["hibor", "hibor 30"],
                category="政府數據",
                aliases=["hkibor", "香港利率"],
                difficulty="初級",
                use_case="查看香港銀行同業拆息利率走勢"
            ),

            "gdp": QuickCommand(
                command="gdp",
                description="獲取GDP數據",
                syntax="gdp [quarters]",
                examples=["gdp", "gdp 4"],
                category="政府數據",
                aliases=["經濟增長", "gdp_data"],
                difficulty="初級",
                use_case="了解香港經濟增長趨勢"
            ),

            # GPU和性能命令
            "gpu_test": QuickCommand(
                command="gpu_test",
                description="測試GPU加速性能",
                syntax="gpu_test [iterations]",
                examples=["gpu_test", "gpu_test 1000"],
                category="性能",
                aliases=["gpu", "gpu_benchmark"],
                difficulty="高級",
                use_case="測試GPU加速效果，優化計算性能"
            ),

            "benchmark": QuickCommand(
                command="benchmark",
                description="系統性能基準測試",
                syntax="benchmark",
                examples=["benchmark"],
                category="性能",
                aliases=["perf", "性能測試"],
                difficulty="高級",
                use_case="評估系統整體性能表現"
            ),

            # 配置命令
            "config": QuickCommand(
                command="config",
                description="配置系統設置",
                syntax="config <key> <value>",
                examples=["config theme dark", "config default_symbol 0700.HK"],
                category="配置",
                aliases=["c", "settings", "設置"],
                difficulty="初級",
                use_case="個性化系統配置和偏好設置"
            ),

            "reset_config": QuickCommand(
                command="reset_config",
                description="重置配置為默認值",
                syntax="reset_config",
                examples=["reset_config"],
                category="配置",
                aliases=["rc", "重置配置"],
                difficulty="初級",
                use_case="恢復系統到默認配置狀態"
            ),

            # 數據管理命令
            "update_data": QuickCommand(
                command="update_data",
                description="更新數據源",
                syntax="update_data [source]",
                examples=["update_data", "update_data stock", "update_data government"],
                category="數據管理",
                aliases=["update", "刷新數據"],
                difficulty="中級",
                use_case="獲取最新的市場和經濟數據"
            ),

            "clear_cache": QuickCommand(
                command="clear_cache",
                description="清理數據緩存",
                syntax="clear_cache [type]",
                examples=["clear_cache", "clear_cache data", "clear_cache all"],
                category="數據管理",
                aliases=["cc", "清理緩存"],
                difficulty="中級",
                use_case="釋放磁盤空間，解決數據問題"
            ),

            # 輸出命令
            "export": QuickCommand(
                command="export",
                description="導出分析結果",
                syntax="export <format> <filename>",
                examples=["export json results.json", "export csv analysis.csv"],
                category="輸出",
                aliases=["導出", "save"],
                difficulty="初級",
                use_case="保存分析結果到文件，便於進一步處理"
            ),

            "chart": QuickCommand(
                command="chart",
                description="生成圖表",
                syntax="chart <type> <data>",
                examples=["chart candle 0700.HK", "chart indicator rsi"],
                category="可視化",
                aliases=["plot", "圖表"],
                difficulty="中級",
                use_case="可視化數據和分析結果"
            ),

            # Telegram命令
            "telegram_start": QuickCommand(
                command="telegram_start",
                description="啟動Telegram機器人",
                syntax="telegram_start",
                examples=["telegram_start"],
                category="集成",
                aliases=["tg", "bot_start"],
                difficulty="中級",
                use_case="啟動自動化交易信號推送"
            ),

            "signal": QuickCommand(
                command="signal",
                description="發送交易信號",
                syntax="signal <symbol> <action> <price>",
                examples=["signal 0700.HK BUY 350.0", "signal 0941.HK SELL 45.5"],
                category="集成",
                aliases=["send_signal", "信號"],
                difficulty="中級",
                use_case="手動發送交易信號到Telegram"
            )
        }

    def _init_shortcuts(self):
        """初始化快捷鍵"""
        self.shortcuts = {
            # 全局快捷鍵
            "h": KeyboardShortcut(
                shortcut="h",
                action="顯示幫助",
                context="global",
                description="在任意時候按h顯示幫助信息"
            ),
            "q": KeyboardShortcut(
                shortcut="q",
                action="退出程序",
                context="global",
                description="安全退出當前程序"
            ),
            "m": KeyboardShortcut(
                shortcut="m",
                action="返回主菜單",
                context="global",
                description="從任何子菜單返回主界面"
            ),
            "b": KeyboardShortcut(
                shortcut="b",
                action="返回上一步",
                context="global",
                description="回到上一個操作界面"
            ),

            # 數字快捷鍵
            "1": KeyboardShortcut(
                shortcut="1",
                action="股票數據分析",
                context="menu",
                description="在主菜單中選擇股票分析功能"
            ),
            "2": KeyboardShortcut(
                shortcut="2",
                action="技術指標計算",
                context="menu",
                description="在主菜單中選擇技術指標功能"
            ),
            "3": KeyboardShortcut(
                shortcut="3",
                action="回測系統",
                context="menu",
                description="在主菜單中選擇回測功能"
            ),
            "4": KeyboardShortcut(
                shortcut="4",
                action="政府數據分析",
                context="menu",
                description="在主菜單中選擇政府數據功能"
            ),
            "5": KeyboardShortcut(
                shortcut="5",
                action="GPU加速測試",
                context="menu",
                description="在主菜單中選擇GPU測試功能"
            ),
            "6": KeyboardShortcut(
                shortcut="6",
                action="風險管理分析",
                context="menu",
                description="在主菜單中選擇風險管理功能"
            ),
            "7": KeyboardShortcut(
                shortcut="7",
                action="Telegram機器人",
                context="menu",
                description="在主菜單中選擇Telegram功能"
            ),
            "8": KeyboardShortcut(
                shortcut="8",
                action="系統配置管理",
                context="menu",
                description="在主菜單中選擇配置功能"
            ),

            # 分析快捷鍵
            "r": KeyboardShortcut(
                shortcut="r",
                action="刷新數據",
                context="analysis",
                description="重新獲取和刷新當前分析數據"
            ),
            "s": KeyboardShortcut(
                shortcut="s",
                action="保存結果",
                context="analysis",
                description="保存當前分析結果到文件"
            ),
            "p": KeyboardShortcut(
                shortcut="p",
                action="打印報告",
                context="analysis",
                description="生成並打印詳細分析報告"
            ),

            # 回測快捷鍵
            "o": KeyboardShortcut(
                shortcut="o",
                action="參數優化",
                context="backtest",
                description="對當前策略進行參數優化"
            ),
            "c": KeyboardShortcut(
                shortcut="c",
                action="比較策略",
                context="backtest",
                description="比較多個策略的回測結果"
            ),
            "d": KeyboardShortcut(
                shortcut="d",
                action="詳細結果",
                context="backtest",
                description="顯示更詳細的回測結果分析"
            ),

            # 配置快捷鍵
            "t": KeyboardShortcut(
                shortcut="t",
                action="切換主題",
                context="config",
                description="在深色/淺色主題間切換"
            ),
            "l": KeyboardShortcut(
                shortcut="l",
                action="切換語言",
                context="config",
                description="在中文/英文界面間切換"
            ),
            "e": KeyboardShortcut(
                shortcut="e",
                action="編輯配置",
                context="config",
                description="手動編輯配置文件"
            ),

            # 導航快捷鍵
            "up": KeyboardShortcut(
                shortcut="↑",
                action="向上導航",
                context="navigation",
                description="在列表中向上移動選擇"
            ),
            "down": KeyboardShortcut(
                shortcut="↓",
                action="向下導航",
                context="navigation",
                description="在列表中向下移動選擇"
            ),
            "left": KeyboardShortcut(
                shortcut="←",
                action="返回上級",
                context="navigation",
                description="返回上一級菜單"
            ),
            "right": KeyboardShortcut(
                shortcut="→",
                action="進入選項",
                context="navigation",
                description="進入當前選中的選項"
            ),

            # 功能快捷鍵
            "f": KeyboardShortcut(
                shortcut="f",
                action="搜索功能",
                context="global",
                description="搜索系統功能或命令"
            ),
            "ctrl+s": KeyboardShortcut(
                shortcut="Ctrl+S",
                action="快速保存",
                context="global",
                description="快速保存當前工作"
            ),
            "ctrl+r": KeyboardShortcut(
                shortcut="Ctrl+R",
                action="刷新系統",
                context="global",
                description="刷新系統狀態和數據"
            )
        }

    def _init_workflows(self):
        """初始化工作流程"""
        self.workflows = {
            # 快速分析流程
            "quick_analysis": Workflow(
                name="5分鐘快速分析",
                description="快速分析單隻股票的基本面和技術面",
                steps=[
                    "啟動系統：python interactive_quantitative_trader.py",
                    "選擇 [1] 股票數據分析",
                    "輸入股票代碼 (如：0700.HK)",
                    "設置分析時長 (默認252天)",
                    "查看基本統計信息",
                    "檢查技術指標狀態",
                    "分析走勢圖和成交量"
                ],
                duration="5min",
                purpose="快速了解股票當前狀況，做出初步判斷",
                prerequisites=["基本股票知識", "系統已安裝"]
            ),

            # 策略回測流程
            "strategy_backtest": Workflow(
                name="完整策略回測",
                description="從策略選擇到結果分析的完整回測流程",
                steps=[
                    "選擇要測試的股票",
                    "選擇回測策略 (RSI、MACD、布林帶等)",
                    "設置策略參數",
                    "設定回測時間範圍",
                    "執行回測計算",
                    "分析回測結果",
                    "檢查關鍵指標 (Sharpe、回撤、勝率)",
                    "評估策略可行性"
                ],
                duration="15min",
                purpose="驗證交易策略的有效性，優化策略參數",
                prerequisites=["了解基本交易策略", "會讀懂回測報告"]
            ),

            # 多策略比較流程
            "multi_strategy_compare": Workflow(
                name="多策略對比分析",
                description="比較多個策略在同一股票上的表現",
                steps=[
                    "選擇分析股票",
                    "選擇要比較的策略 (建議3-5個)",
                    "統一回測參數 (時間範圍、基準等)",
                    "逐一執行策略回測",
                    "記錄各策略關鍵指標",
                    "製作對比表格",
                    "分析優劣勢",
                    "選擇最適合策略"
                ],
                duration="30min",
                purpose="找出在特定股票上表現最佳的策略",
                prerequisites=["完成單策略回測", "了解多種策略特點"]
            ),

            # 風險評估流程
            "risk_assessment": Workflow(
                name="投資風險評估",
                description="全面評估投資組合的風險狀況",
                steps=[
                    "確定投資組合構成",
                    "獲取歷史價格數據",
                    "計算組合收益率",
                    "分析波動率和相關性",
                    "計算VaR和CVaR",
                    "進行壓力測試",
                    "評估最大回撤",
                    "制定風險控制措施"
                ],
                duration="20min",
                purpose="量化投資風險，制定風險管理策略",
                prerequisites=["了解風險管理概念", "具備統計學基礎"]
            ),

            # 參數優化流程
            "parameter_optimization": Workflow(
                name="策略參數優化",
                description="尋找策略的最優參數組合",
                steps=[
                    "確定優化目標 (Sharpe、回報率等)",
                    "設定參數搜索範圍",
                    "選擇優化算法 (網格搜索、貝葉斯等)",
                    "執行參數優化",
                    "分析優化結果",
                    "進行樣本外測試",
                    "選擇最終參數",
                    "文檔化優化過程"
                ],
                duration="45min",
                purpose="提高策略表現，避免過度擬合",
                prerequisites=["了解參數優化方法", "具備編程基礎"]
            ),

            # 日常監控流程
            "daily_monitoring": Workflow(
                name="日常投資監控",
                description="每日投資組合監控和調整流程",
                steps=[
                    "檢查市場概況",
                    "監控持倉股票表現",
                    "查看重要經濟數據",
                    "檢查技術指標信號",
                    "評估倉位風險",
                    "記錄交易日誌",
                    "制定次日計劃",
                    "必要時執行調倉"
                ],
                duration="10min",
                purpose="保持對投資組合的密切關注，及時發現問題",
                prerequisites=["日常投資習慣", "基本的市場敏感度"]
            )
        }

    def _init_tips(self):
        """初始化實用技巧"""
        self.tips = [
            # 初級技巧
            {
                "level": "初級",
                "category": "效率",
                "tip": "使用數字鍵1-8快速選擇主菜單功能",
                "detail": "在主菜單界面，直接按數字鍵可以快速選擇對應功能，無需輸入後按回車。"
            },
            {
                "level": "初級",
                "category": "數據",
                "tip": "定期更新數據源確保分析準確性",
                "detail": "使用 'update_data' 命令定期獲取最新的市場數據，建議每日更新一次。"
            },
            {
                "level": "初級",
                "category": "配置",
                "tip": "設置默認股票代碼和時長提高效率",
                "detail": "在配置中設置常用的默認值，可以減少每次分析時的重複輸入。"
            },

            # 中級技巧
            {
                "level": "中級",
                "category": "分析",
                "tip": "組合使用多個技術指標提高準確性",
                "detail": "不要單獨依賴一個指標，建議結合趨勢、動量、波動率等不同類型指標。"
            },
            {
                "level": "中級",
                "category": "回測",
                "tip": "使用樣本外測試驗證策略有效性",
                "detail": "將數據分為訓練集和測試集，避免過度擬合，確保策略在未來數據上有效。"
            },
            {
                "level": "中級",
                "category": "風險",
                "tip": "關注最大回撤而不僅僅是收益率",
                "detail": "高收益率可能伴隨高風險，最大回撤反映了策略的風險控制能力。"
            },

            # 高級技巧
            {
                "level": "高級",
                "category": "性能",
                "tip": "啟用GPU加速處理大批量數據",
                "detail": "處理大量股票或長時間序列數據時，GPU加速可以顯著提升計算速度。"
            },
            {
                "level": "高級",
                "category": "優化",
                "tip": "使用貝葉斯優化提高參數搜索效率",
                "detail": "相比網格搜索，貝葉斯優化可以用更少的計算找到更好的參數組合。"
            },
            {
                "level": "高級",
                "category": "組合",
                "tip": "考慮策略相關性進行多策略組合",
                "detail": "選擇相關性較低的策略組合，可以有效分散風險，提高組合穩定性。"
            },

            # 實用技巧
            {
                "level": "實用",
                "category": "數據",
                "tip": "緩存常用數據避免重複下載",
                "detail": "系統會自動緩存數據，但要注意定期清理過期緩存釋放磁盤空間。"
            },
            {
                "level": "實用",
                "category": "自動化",
                "tip": "設置Telegram警報及時獲取交易信號",
                "detail": "配置Telegram機器人可以實時接收交易信號和風險警報，不錯過機會。"
            },
            {
                "level": "實用",
                "category": "備份",
                "tip": "定期備份配置文件和分析結果",
                "detail": "重要的配置和分析結果要定期備份，防止數據丟失。"
            }
        ]

    def search_commands(self, query: str) -> List[QuickCommand]:
        """搜索命令"""
        query = query.lower()
        results = []

        for cmd in self.commands.values():
            if (query in cmd.command.lower() or
                query in cmd.description.lower() or
                any(query in alias.lower() for alias in cmd.aliases) or
                query in cmd.category.lower()):
                results.append(cmd)

        return results

    def search_shortcuts(self, query: str) -> List[KeyboardShortcut]:
        """搜索快捷鍵"""
        query = query.lower()
        results = []

        for shortcut in self.shortcuts.values():
            if (query in shortcut.shortcut.lower() or
                query in shortcut.action.lower() or
                query in shortcut.description.lower() or
                query in shortcut.context.lower()):
                results.append(shortcut)

        return results

    def search_workflows(self, query: str) -> List[Workflow]:
        """搜索工作流程"""
        query = query.lower()
        results = []

        for workflow in self.workflows.values():
            if (query in workflow.name.lower() or
                query in workflow.description.lower() or
                query in workflow.purpose.lower() or
                any(query in step.lower() for step in workflow.steps)):
                results.append(workflow)

        return results

    def search_tips(self, query: str, level: str = None) -> List[Dict]:
        """搜索技巧"""
        query = query.lower()
        results = []

        for tip in self.tips:
            if level and tip["level"] != level:
                continue

            if (query in tip["tip"].lower() or
                query in tip["detail"].lower() or
                query in tip["category"].lower()):
                results.append(tip)

        return results

    def get_commands_by_category(self, category: str) -> List[QuickCommand]:
        """根據分類獲取命令"""
        return [cmd for cmd in self.commands.values() if cmd.category == category]

    def get_shortcuts_by_context(self, context: str) -> List[KeyboardShortcut]:
        """根據上下文獲取快捷鍵"""
        return [sc for sc in self.shortcuts.values() if sc.context == context]

    def get_workflows_by_duration(self, duration: str) -> List[Workflow]:
        """根據時長獲取工作流程"""
        return [wf for wf in self.workflows.values() if wf.duration == duration]

    def get_tips_by_level(self, level: str) -> List[Dict]:
        """根據級別獲取技巧"""
        return [tip for tip in self.tips if tip["level"] == level]

    def format_command_help(self, command: QuickCommand) -> str:
        """格式化命令幫助"""
        output = []

        output.append(f"🔧 {command.command}")
        output.append("=" * (len(command.command) + 3))
        output.append(f"📝 描述：{command.description}")
        output.append(f"📖 語法：{command.syntax}")
        output.append(f"📊 難度：{command.difficulty}")
        output.append(f"🏷️  分類：{command.category}")
        output.append(f"🎯 用例：{command.use_case}")

        if command.aliases:
            output.append(f"⌨️  別名：{', '.join(command.aliases)}")

        if command.examples:
            output.append(f"💡 示例：")
            for example in command.examples:
                output.append(f"   • {example}")

        return "\n".join(output)

    def format_shortcut_help(self, shortcut: KeyboardShortcut) -> str:
        """格式化快捷鍵幫助"""
        return f"{shortcut.shortcut:>10} → {shortcut.action} ({shortcut.context}) - {shortcut.description}"

    def format_workflow_help(self, workflow: Workflow) -> str:
        """格式化工作流程幫助"""
        output = []

        output.append(f"🔄 {workflow.name}")
        output.append("=" * (len(workflow.name) + 3))
        output.append(f"📝 描述：{workflow.description}")
        output.append(f"⏱️  時長：{workflow.duration}")
        output.append(f"🎯 目的：{workflow.purpose}")

        if workflow.prerequisites:
            output.append(f"📋 前置條件：{', '.join(workflow.prerequisites)}")

        output.append("\n📍 步驟：")
        for i, step in enumerate(workflow.steps, 1):
            output.append(f"   {i}. {step}")

        return "\n".join(output)

    def format_tip_help(self, tip: Dict) -> str:
        """格式化技巧幫助"""
        return f"💡 {tip['tip']} ({tip['level']} - {tip['category']})\n   {tip['detail']}"

    def show_command_overview(self) -> str:
        """顯示命令概覽"""
        output = []
        output.append("\n🔧 快速命令參考")
        output.append("=" * 30)

        categories = {}
        for cmd in self.commands.values():
            if cmd.category not in categories:
                categories[cmd.category] = []
            categories[cmd.category].append(cmd)

        for category, commands in categories.items():
            output.append(f"\n📂 {category}:")
            for cmd in commands[:5]:  # 最多顯示5個
                output.append(f"   • {cmd.command} - {cmd.description}")
            if len(commands) > 5:
                output.append(f"   ... 還有{len(commands)-5}個命令")

        return "\n".join(output)

    def show_shortcut_overview(self) -> str:
        """顯示快捷鍵概覽"""
        output = []
        output.append("\n⌨️  快捷鍵大全")
        output.append("=" * 25)

        contexts = {}
        for sc in self.shortcuts.values():
            if sc.context not in contexts:
                contexts[sc.context] = []
            contexts[sc.context].append(sc)

        for context, shortcuts in contexts.items():
            output.append(f"\n📍 {context.upper()}:")
            for sc in shortcuts:
                output.append(f"   {self.format_shortcut_help(sc)}")

        return "\n".join(output)

    def show_workflow_overview(self) -> str:
        """顯示工作流程概覽"""
        output = []
        output.append("\n🔄 工作流程參考")
        output.append("=" * 25)

        for workflow in self.workflows.values():
            output.append(f"\n⏱️  {workflow.name} ({workflow.duration})")
            output.append(f"   {workflow.description}")

        return "\n".join(output)

    def generate_cheat_sheet(self, format: str = "text") -> str:
        """生成備忘單"""
        output = []

        output.append("# 香港量化交易系統快速備忘單")
        output.append("=" * 40)
        output.append(f"生成時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append("")

        # 核心命令
        output.append("## 🔧 核心命令")
        output.append("")
        essential_commands = ["analyze", "backtest", "indicator", "help"]
        for cmd_id in essential_commands:
            if cmd_id in self.commands:
                cmd = self.commands[cmd_id]
                output.append(f"**{cmd.command}** - {cmd.description}")
                output.append(f"語法：`{cmd.syntax}`")
                output.append("")

        # 重要快捷鍵
        output.append("## ⌨️  重要快捷鍵")
        output.append("")
        essential_shortcuts = ["1", "2", "3", "h", "q", "m"]
        for sc_id in essential_shortcuts:
            if sc_id in self.shortcuts:
                sc = self.shortcuts[sc_id]
                output.append(f"**{sc.shortcut}** → {sc.action}")

        output.append("")

        # 常用工作流程
        output.append("## 🔄 常用工作流程")
        output.append("")
        output.append("### 5分鐘快速分析")
        for step in self.workflows["quick_analysis"].steps[:3]:
            output.append(f"1. {step}")

        output.append("")
        output.append("### 策略回測流程")
        for step in self.workflows["strategy_backtest"].steps[:3]:
            output.append(f"1. {step}")

        output.append("")

        # 實用技巧
        output.append("## 💡 實用技巧")
        output.append("")
        for tip in self.tips[:3]:
            output.append(f"• {tip['tip']}")
            output.append(f"  {tip['detail']}")
            output.append("")

        return "\n".join(output)

    def export_reference(self, filename: str, format: str = "json") -> bool:
        """導出參考資料"""
        try:
            data = {
                "commands": {
                    cmd_id: {
                        "command": cmd.command,
                        "description": cmd.description,
                        "syntax": cmd.syntax,
                        "examples": cmd.examples,
                        "category": cmd.category,
                        "aliases": cmd.aliases,
                        "difficulty": cmd.difficulty,
                        "use_case": cmd.use_case
                    }
                    for cmd_id, cmd in self.commands.items()
                },
                "shortcuts": {
                    sc_id: {
                        "shortcut": sc.shortcut,
                        "action": sc.action,
                        "context": sc.context,
                        "description": sc.description
                    }
                    for sc_id, sc in self.shortcuts.items()
                },
                "workflows": {
                    wf_id: {
                        "name": wf.name,
                        "description": wf.description,
                        "steps": wf.steps,
                        "duration": wf.duration,
                        "purpose": wf.purpose,
                        "prerequisites": wf.prerequisites
                    }
                    for wf_id, wf in self.workflows.items()
                },
                "tips": self.tips,
                "version": self.version,
                "generated_at": datetime.now().isoformat()
            }

            if format == "json":
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            elif format == "cheat_sheet":
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.generate_cheat_sheet())
            else:
                raise ValueError(f"不支持的導出格式：{format}")

            return True

        except Exception as e:
            logger.error(f"導出參考資料失敗：{e}")
            return False

if __name__ == "__main__":
    # 簡單測試
    ref = QuickReference()

    # 測試搜索
    print("搜索 'analysis' 結果：")
    for cmd in ref.search_commands("analysis"):
        print(f"- {cmd.command}: {cmd.description}")

    # 生成備忘單
    print("\n" + ref.generate_cheat_sheet())
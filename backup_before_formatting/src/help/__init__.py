#!/usr/bin/env python3
"""
幫助系統模塊
提供完整的文檔、教程和快速參考功能

模塊組成：
- help_system.py: 核心幫助系統
- interactive_tutorial.py: 互動式教程
- quick_reference.py: 快速參考指南
- help_menu.py: 幫助菜單集成
"""

from .help_system import HelpSystem, HelpTopic
from .interactive_tutorial import InteractiveTutorial, TutorialStep
from .quick_reference import QuickReference, QuickCommand, KeyboardShortcut, Workflow
from .help_menu import HelpMenu, HelpContext

__version__ = "1.0.0"
__author__ = "Claude Code Assistant"

# 導出主要類
__all__ = [
    # 核心幫助系統
    'HelpSystem',
    'HelpTopic',

    # 教程系統
    'InteractiveTutorial',
    'TutorialStep',

    # 快速參考
    'QuickReference',
    'QuickCommand',
    'KeyboardShortcut',
    'Workflow',

    # 幫助菜單
    'HelpMenu',
    'HelpContext'
]

# 便捷函數
def get_help_system():
    """獲取幫助系統實例"""
    return HelpSystem()

def get_tutorial_system():
    """獲取教程系統實例"""
    return InteractiveTutorial()

def get_quick_reference():
    """獲取快速參考實例"""
    return QuickReference()

def get_help_menu(main_app=None):
    """獲取幫助菜單實例"""
    return HelpMenu(main_app)

def show_help_main_menu():
    """顯示幫助主菜單的便捷函數"""
    help_menu = HelpMenu()
    return help_menu.show_help_menu()

def search_help(query: str):
    """搜索幫助內容的便捷函數"""
    help_system = HelpSystem()
    return help_system.search_help(query)

def start_tutorial(tutorial_id: str = "beginner_guide"):
    """啟動教程的便捷函數"""
    tutorial = InteractiveTutorial()
    return tutorial.start_tutorial(tutorial_id)

# 模塊信息
def get_module_info():
    """獲取模塊信息"""
    return {
        "name": "幫助系統模塊",
        "version": __version__,
        "author": __author__,
        "description": "提供完整的量化交易系統幫助、教程和快速參考功能",
        "components": [
            "HelpSystem - 核心幫助系統，提供幫助主題管理和搜索",
            "InteractiveTutorial - 互動式教程系統，提供step-by-step學習指南",
            "QuickReference - 快速參考指南，提供命令、快捷鍵和工作流程",
            "HelpMenu - 幫助菜單系統，與主界面無縫集成"
        ],
        "features": [
            "477種技術指標說明和使用指南",
            "6種內置交易策略詳解",
            "8個系統模塊完整文檔",
            "中英文雙語支持",
            "智能搜索功能",
            "上下文敏感幫助",
            "交互式學習教程",
            "命令別名和快捷鍵支持"
        ]
    }

# 初始化日誌
import logging
logger = logging.getLogger(__name__)
logger.info(f"幫助系統模塊 v{__version__} 已加載")
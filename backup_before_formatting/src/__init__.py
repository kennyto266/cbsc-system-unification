"""
香港量化交易系統 - 核心包初始化
Hong Kong Quantitative Trading System - Core Package Initialization

一个专业的量化交易系统，集成多層架構、RSI優化器、AI Agent協作等先進功能。
主要特性：
- 三層架構設計 (Data Access, Business Logic, Presentation)
- RSI策略優化器 (多進行並行優化)
- 7個專業AI Agent協作
- 11個香港政府數據源集成
- 80 + 港股實時數據支持
- 企業級用戶界面和可視化

系統目標：提供高性能、高可靠性的量化交易解決方案
"""

import os
from typing import Dict, Tuple

# 導入統一版本管理系統
try:
    from .version import __version__ as _system_version
    from .version import __version_info__ as _version_info
    from .version import get_build_info as _get_build_info
    from .version import get_version as _get_version
    from .version import get_version_tuple as _get_version_tuple

    # 使用統一版本管理
    __version__ = _get_version()
    __version_info__ = _version_info
except ImportError:
    # 回退到硬編碼版本（向後兼容）
    __version__ = "2.1.0"
    __version_info__ = None  # type: ignore

# 模組信息
__author__ = "香港量化交易團隊"
__description__ = "香港量化交易系統 - 專業級三層架構量化平台"


# 向後兼容的版本函數
def get_version() -> str:
    """獲取當前版本號（使用統一版本管理）"""
    try:
        from .version import get_version as _version_get_version

        return _version_get_version()
    except ImportError:
        return __version__


def get_version_tuple() -> Tuple[int, int, int]:
    """獲取版本號元組 (major, minor, patch)"""
    try:
        from .version import get_version_tuple as _version_get_tuple

        return _version_get_tuple()
    except ImportError:
        # 回退解析
        version = __version__
        if version.startswith("v"):
            version = version[1:]
        parts = version.split(".")
        try:
            return (int(parts[0]), int(parts[1]), int(parts[2])) if len(parts) >= 3 else (2, 1, 0)
        except Exception:
            return (2, 1, 0)


def get_build_info() -> Dict:
    """獲取構建信息（使用統一版本管理）"""
    try:
        from .version import get_build_info as _version_build_info

        return _version_build_info()
    except ImportError:
        # 回退到簡化版本信息
        return {
            "version": __version__,
            "version_tuple": get_version_tuple(),
            "author": __author__,
            "description": __description__,
            "environment": "development" if os.getenv("DEVELOPMENT") else "production",
            "features": [
                "三層架構設計",
                "RSI策略優化器",
                "多智能體協作系統",
                "實時數據集成",
                "專業可視化界面",
                "AI智能分析",
                "企業級安全框架",
            ],
        }


# 導出主要變量
__all__ = [
    "__version__",
    "__author__",
    "__description__",
    "get_version",
    "get_version_tuple",
    "get_build_info",
]

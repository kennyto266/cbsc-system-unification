#!/usr / bin / env python3
"""
Simplified System - Cookbook移動平均線交叉策略
基於Python Algorithmic Trading Cookbook的MA Crossover策略實現

雙移動平均線交叉策略是一種經典的趨勢跟蹤策略：
- 當快線向上穿越慢線時買入
- 當快線向下穿越慢線時賣出
- 適合趨勢明顯的市場環境
"""

import logging
from typing import Any, Dict, List

import numpy as np
import pandas as pd

try:
    import vectorbt as vbt

    VECTORBT_AVAILABLE = True
except ImportError:
    VECTORBT_AVAILABLE = False
    logging.warning("VectorBT not available. Install with: pip install vectorbt")
    vbt = None

logger = logging.getLogger(__name__)


def ma_crossover_strategy(
    price: pd.Series, fast_window: int = 10, slow_window: int = 30, **kwargs
) -> "vbt.Portfolio":
    """
    雙移動平均線交叉策略

    基於Python Algorithmic Trading Cookbook 06a章節的實現

    Args:
        price: 價格數據
        fast_window: 快線週期
        slow_window: 慢線週期
        **kwargs: 其他VectorBT參數

    Returns:
        vbt.Portfolio: 投資組合對象
    """
    if not VECTORBT_AVAILABLE:
        raise ImportError("VectorBT is required for MA crossover strategy")

    # 驗證參數
    if fast_window >= slow_window:
        raise ValueError("快線週期必須小於慢線週期")

    logger.info(f"執行MA交叉策略: 快線={fast_window}, 慢線={slow_window}")

    # 計算移動平均線
    fast_ma = vbt.MA.run(price, window = fast_window, short_name="fast")
    slow_ma = vbt.MA.run(price, window = slow_window, short_name="slow")

    # 生成交易信號
    entries = fast_ma.ma_crossed_above(slow_ma)
    exits = fast_ma.ma_crossed_below(slow_ma)

    # 創建投資組合
    pf = vbt.Portfolio.from_signals(price, entries, exits, **kwargs)

    return pf


def optimize_ma_crossover(
    price: pd.Series,
    fast_range: List[int] = None,
    slow_range: List[int] = None,
    **portfolio_kwargs,
) -> Dict[str, Any]:
    """
    優化MA交叉策略參數

    Args:
        price: 價格數據
        fast_range: 快線參數範圍
        slow_range: 慢線參數範圍
        **portfolio_kwargs: 投資組合參數

    Returns:
        Dict[str, Any]: 優化結果
    """
    if fast_range is None:
        fast_range = list(range(5, 21, 5))  # [5, 10, 15, 20]
    if slow_range is None:
        slow_range = list(range(20, 61, 10))  # [20, 30, 40, 50, 60]

    logger.info(f"優化MA交叉策略: 快線範圍={fast_range}, 慢線範圍={slow_range}")

    # 生成所有參數組合
    fast_ma, slow_ma = vbt.MA.run_combs(
        price, [fast_range, slow_range], r = 2, short_names=["fast", "slow"]
    )

    # 生成信號
    entries = fast_ma.ma_crossed_above(slow_ma)
    exits = fast_ma.ma_crossed_below(slow_ma)

    # 創建投資組合
    pf = vbt.Portfolio.from_signals(price, entries, exits, **portfolio_kwargs)

    # 計算性能指標
    sharpe_ratio = pf.sharpe_ratio()
    total_return = pf.total_return()
    max_drawdown = pf.max_drawdown()

    # 找到最佳參數
    best_sharpe_idx = sharpe_ratio.idxmax()
    best_params = {
        "fast_window": best_sharpe_idx[0],
        "slow_window": best_sharpe_idx[1],
        "sharpe_ratio": sharpe_ratio[best_sharpe_idx],
        "total_return": total_return[best_sharpe_idx],
        "max_drawdown": max_drawdown[best_sharpe_idx],
    }

    logger.info(f"最佳MA參數: {best_params}")

    return {
        "best_params": best_params,
        "all_results": {
            "sharpe_ratio": sharpe_ratio,
            "total_return": total_return,
            "max_drawdown": max_drawdown,
        },
        "portfolio": pf,
    }

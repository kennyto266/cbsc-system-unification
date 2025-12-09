#!/usr / bin / env python3
"""
Simplified System - Cookbook RSI均值回歸策略
基於Python Algorithmic Trading Cookbook的RSI策略實現

RSI均值回歸策略是一種經典的震盪策略：
- RSI超賣時買入（通常RSI < 30）
- RSI超買時賣出（通常RSI > 70）
- 適合區間震盪的市場環境
- 利用價格向均值回歸的特性
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


def rsi_mean_reversion_strategy(
    price: pd.Series,
    rsi_period: int = 14,
    oversold: int = 30,
    overbought: int = 70,
    **kwargs,
) -> "vbt.Portfolio":
    """
    RSI均值回歸策略

    基於Python Algorithmic Trading Cookbook的實現

    Args:
        price: 價格數據
        rsi_period: RSI計算週期
        oversold: 超賣閾值
        overbought: 超買閾值
        **kwargs: 其他VectorBT參數

    Returns:
        vbt.Portfolio: 投資組合對象
    """
    if not VECTORBT_AVAILABLE:
        raise ImportError("VectorBT is required for RSI mean reversion strategy")

    # 驗證參數
    if oversold >= overbought:
        raise ValueError("超賣閾值必須小於超買閾值")

    if not (0 < oversold < 100) or not (0 < overbought < 100):
        raise ValueError("RSI閾值必須在0 - 100之間")

    logger.info(
        f"執行RSI均值回歸策略: RSI={rsi_period}, 超賣={oversold}, 超買={overbought}"
    )

    # 計算RSI
    rsi = vbt.RSI.run(price, window = rsi_period)

    # 生成交易信號
    entries = rsi.rsi_crossed_below(oversold)  # RSI跌破超賣線時買入
    exits = rsi.rsi_crossed_above(overbought)  # RSI突破超買線時賣出

    # 創建投資組合
    pf = vbt.Portfolio.from_signals(price, entries, exits, **kwargs)

    return pf


def optimize_rsi_strategy(
    price: pd.Series,
    rsi_range: List[int] = None,
    oversold_range: List[int] = None,
    overbought_range: List[int] = None,
    **portfolio_kwargs,
) -> Dict[str, Any]:
    """
    優化RSI均值回歸策略參數

    Args:
        price: 價格數據
        rsi_range: RSI週期範圍
        oversold_range: 超賣閾值範圍
        overbought_range: 超買閾值範圍
        **portfolio_kwargs: 投資組合參數

    Returns:
        Dict[str, Any]: 優化結果
    """
    if rsi_range is None:
        rsi_range = [10, 14, 20, 30]
    if oversold_range is None:
        oversold_range = [20, 25, 30]
    if overbought_range is None:
        overbought_range = [70, 75, 80]

    logger.info(
        f"優化RSI策略: RSI={rsi_range}, 超賣={oversold_range}, 超買={overbought_range}"
    )

    # 計算RSI
    rsi = vbt.RSI.run(price, window = rsi_range)

    # 生成交易信號矩陣
    entries = rsi.rsi_crossed_below(oversold_range)
    exits = rsi.rsi_crossed_above(overbought_range)

    # 創建投資組合
    pf = vbt.Portfolio.from_signals(price, entries, exits, **portfolio_kwargs)

    # 計算性能指標
    sharpe_ratio = pf.sharpe_ratio()
    total_return = pf.total_return()
    max_drawdown = pf.max_drawdown()

    # 找到最佳參數
    best_sharpe_idx = sharpe_ratio.idxmax()
    best_params = {
        "rsi_period": best_sharpe_idx[0],
        "oversold": best_sharpe_idx[1],
        "overbought": best_sharpe_idx[2],
        "sharpe_ratio": sharpe_ratio[best_sharpe_idx],
        "total_return": total_return[best_sharpe_idx],
        "max_drawdown": max_drawdown[best_sharpe_idx],
    }

    logger.info(f"最佳RSI參數: {best_params}")

    return {
        "best_params": best_params,
        "all_results": {
            "sharpe_ratio": sharpe_ratio,
            "total_return": total_return,
            "max_drawdown": max_drawdown,
        },
        "portfolio": pf,
    }


def rsi_with_stop_loss_strategy(
    price: pd.Series,
    rsi_period: int = 14,
    oversold: int = 30,
    overbought: int = 70,
    stop_loss: float = 0.05,
    **kwargs,
) -> "vbt.Portfolio":
    """
    帶止損的RSI均值回歸策略

    增強版本，增加止損機制來控制風險

    Args:
        price: 價格數據
        rsi_period: RSI計算週期
        oversold: 超賣閾值
        overbought: 超買閾值
        stop_loss: 止損百分比（例如0.05表示5%）
        **kwargs: 其他VectorBT參數

    Returns:
        vbt.Portfolio: 投資組合對象
    """
    if not VECTORBT_AVAILABLE:
        raise ImportError("VectorBT is required for RSI with stop loss strategy")

    logger.info(f"執行帶止損RSI策略: RSI={rsi_period}, 止損={stop_loss * 100:.1f}%")

    # 計算RSI
    rsi = vbt.RSI.run(price, window = rsi_period)

    # 生成基礎交易信號
    entries = rsi.rsi_crossed_below(oversold)
    exits = rsi.rsi_crossed_above(overbought)

    # 創建投資組合（包含止損）
    pf = vbt.Portfolio.from_signals(
        price, entries, exits, stop_loss = stop_loss, **kwargs
    )

    return pf

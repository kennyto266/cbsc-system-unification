#!/usr / bin / env python3
"""
RSI策略優化器 - 集成版本
RSI Strategy Optimizer - Integrated Version
"""

import asyncio
import logging
import multiprocessing as mp
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import aiohttp
import numpy as np
import pandas as pd
import requests

logger = logging.getLogger(__name__)


@dataclass
class OptimizationConfig:
    """優化配置"""

    rsi_period_range: Tuple[int, int] = (5, 30)
    rsi_oversold_range: Tuple[float, float] = (20, 40)
    rsi_overbought_range: Tuple[float, float] = (60, 80)
    sma_period_range: Tuple[int, int] = (5, 50)
    initial_capital: float = 100000
    commission_rate: float = 0.001
    max_processes: int = 4


@dataclass
class OptimizationResult:
    """優化結果"""

    rsi_period: int
    rsi_oversold: float
    rsi_overbought: float
    sma_period: int
    total_return: float
    annualized_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    total_trades: int
    optimization_score: float


class RSIOptimizer:
    """RSI策略優化器"""

    def __init__(self, config: Optional[OptimizationConfig] = None):
        self.config = config or OptimizationConfig()
        self.data_cache = {}

    async def get_stock_data(
        self, symbol: str, duration: int = 365
    ) -> Optional[List[Dict]]:
        """獲取股票數據"""
        try:
            # 先嘗試從Layer 1獲取數據
            layer1_url = "http://localhost:8001 / api / v1 / stock / data"
            params = {"symbol": symbol, "duration": duration}

            async with aiohttp.ClientSession() as session:
                async with session.post(layer1_url, json=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("success"):
                            return result.get("data", [])

            # 備用到直接API
            api_url = "http://18.180.162.113:9191 / inst / getInst"
            params = {"symbol": symbol.lower(), "duration": duration}

            response = requests.get(api_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("data", [])

        except Exception as e:
            logger.error(f"獲取股票數據失敗 {symbol}: {e}")
            return None

    def calculate_rsi(self, df: pd.DataFrame, period: int) -> pd.Series:
        """計算RSI指標"""
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_sma(self, df: pd.DataFrame, period: int) -> pd.Series:
        """計算簡單移動平均線"""
        return df["close"].rolling(window=period).mean()

    def backtest_strategy(
        self,
        data: List[Dict],
        rsi_period: int,
        rsi_oversold: float,
        rsi_overbought: float,
        sma_period: int,
    ) -> Dict:
        """回測策略"""
        try:
            if not data:
                return {"error": "No data available"}

            df = pd.DataFrame(data)
            df["close"] = pd.to_numeric(df["close"], errors="coerce")
            df = df.dropna(subset=["close"])

            if len(df) < rsi_period * 2:
                return {"error": "Insufficient data"}

            # 計算技術指標
            df["rsi"] = self.calculate_rsi(df, rsi_period)
            df["sma"] = self.calculate_sma(df, sma_period)

            # 生成交易信號
            df["signal"] = 0
            buy_condition = (df["rsi"] < rsi_oversold) & (df["close"] > df["sma"])
            sell_condition = (df["rsi"] > rsi_overbought) & (df["close"] < df["sma"])

            df.loc[buy_condition, "signal"] = 1
            df.loc[sell_condition, "signal"] = -1

            # 計算交易結果
            capital = self.config.initial_capital
            position = 0
            trades = []
            equity_curve = []

            for i, row in df.iterrows():
                equity_curve.append(capital)

                if row["signal"] == 1 and position <= 0:  # 買入信號
                    if position < 0:  # 平空倉
                        capital += (
                            position * row["close"] * (1 - self.config.commission_rate)
                        )
                    shares = capital // (
                        row["close"] * (1 + self.config.commission_rate)
                    )
                    if shares > 0:
                        capital -= (
                            shares * row["close"] * (1 + self.config.commission_rate)
                        )
                        position = shares
                        trades.append(
                            {
                                "date": row.get("date", i),
                                "type": "BUY",
                                "price": row["close"],
                                "shares": shares,
                            }
                        )

                elif row["signal"] == -1 and position > 0:  # 賣出信號
                    capital += (
                        position * row["close"] * (1 - self.config.commission_rate)
                    )
                    trades.append(
                        {
                            "date": row.get("date", i),
                            "type": "SELL",
                            "price": row["close"],
                            "shares": position,
                        }
                    )
                    position = 0

            # 最後平倉
            if position > 0:
                capital += (
                    position * df["close"].iloc[-1] * (1 - self.config.commission_rate)
                )

            # 計算績效指標
            total_return = (
                capital - self.config.initial_capital
            ) / self.config.initial_capital

            if len(equity_curve) > 1:
                equity_series = pd.Series(equity_curve)
                rolling_max = equity_series.expanding().max()
                drawdown = (equity_series - rolling_max) / rolling_max
                max_drawdown = drawdown.min()

                # 計算年化收益率
                days = len(df)
                annualized_return = (1 + total_return) ** (365 / days) - 1

                # 計算夏普比率（假設無風險利率為0）
                returns = equity_series.pct_change().dropna()
                if len(returns) > 1 and returns.std() > 0:
                    sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252)
                else:
                    sharpe_ratio = 0
            else:
                max_drawdown = 0
                annualized_return = total_return
                sharpe_ratio = 0

            # 計算勝率
            winning_trades = sum(1 for trade in trades if len(trades) >= 2)
            win_rate = winning_trades / len(trades) if trades else 0

            # 綜合評分（權重：回報40%，夏普30%，最大回撤 - 20%，勝率10%）
            score = (
                total_return * 40
                + sharpe_ratio * 30
                - abs(max_drawdown) * 20
                + win_rate * 100 * 10
            ) / 100

            return {
                "total_return": total_return,
                "annualized_return": annualized_return,
                "max_drawdown": max_drawdown,
                "sharpe_ratio": sharpe_ratio,
                "win_rate": win_rate,
                "total_trades": len(trades),
                "optimization_score": score,
                "final_capital": capital,
                "equity_curve": equity_curve,
                "trades": trades,
            }

        except Exception as e:
            logger.error(f"回測失敗: {e}")
            return {"error": str(e)}

    def optimize_single_combination(self, params: Tuple) -> OptimizationResult:
        """優化單個參數組合"""
        symbol, rsi_period, rsi_oversold, rsi_overbought, sma_period = params

        # 獲取數據
        if symbol not in self.data_cache:
            data = (
                requests.get(
                    "http://18.180.162.113:9191 / inst / getInst",
                    params={"symbol": symbol.lower(), "duration": 365},
                    timeout=10,
                )
                .json()
                .get("data", [])
            )
            self.data_cache[symbol] = data
        else:
            data = self.data_cache[symbol]

        if not data:
            return OptimizationResult(
                rsi_period=rsi_period,
                rsi_oversold=rsi_oversold,
                rsi_overbought=rsi_overbought,
                sma_period=sma_period,
                total_return=0,
                annualized_return=0,
                max_drawdown=0,
                sharpe_ratio=0,
                win_rate=0,
                total_trades=0,
                optimization_score=-999,
            )

        # 回測
        result = self.backtest_strategy(
            data, rsi_period, rsi_oversold, rsi_overbought, sma_period
        )

        if "error" in result:
            return OptimizationResult(
                rsi_period=rsi_period,
                rsi_oversold=rsi_oversold,
                rsi_overbought=rsi_overbought,
                sma_period=sma_period,
                total_return=0,
                annualized_return=0,
                max_drawdown=0,
                sharpe_ratio=0,
                win_rate=0,
                total_trades=0,
                optimization_score=-999,
            )

        return OptimizationResult(
            rsi_period=rsi_period,
            rsi_oversold=rsi_oversold,
            rsi_overbought=rsi_overbought,
            sma_period=sma_period,
            total_return=result["total_return"],
            annualized_return=result["annualized_return"],
            max_drawdown=result["max_drawdown"],
            sharpe_ratio=result["sharpe_ratio"],
            win_rate=result["win_rate"],
            total_trades=result["total_trades"],
            optimization_score=result["optimization_score"],
        )

    async def optimize_strategy(self, symbol: str) -> Dict:
        """執行策略優化"""
        start_time = time.time()

        try:
            # 生成參數組合
            rsi_periods = list(
                range(
                    self.config.rsi_period_range[0],
                    self.config.rsi_period_range[1] + 1,
                    2,
                )
            )
            oversold_levels = np.round(
                np.linspace(
                    self.config.rsi_oversold_range[0],
                    self.config.rsi_oversold_range[1],
                    3,
                ),
                1,
            )
            overbought_levels = np.round(
                np.linspace(
                    self.config.rsi_overbought_range[0],
                    self.config.rsi_overbought_range[1],
                    3,
                ),
                1,
            )
            sma_periods = list(
                range(
                    self.config.sma_period_range[0],
                    self.config.sma_period_range[1] + 1,
                    5,
                )
            )

            # 生成所有組合
            param_combinations = []
            for rsi_period in rsi_periods:
                for oversold in oversold_levels:
                    for overbought in overbought_levels:
                        if oversold < overbought:
                            for sma_period in sma_periods:
                                param_combinations.append(
                                    (
                                        symbol,
                                        rsi_period,
                                        oversold,
                                        overbought,
                                        sma_period,
                                    )
                                )

            # 使用進程池並行優化
            results = []
            with ProcessPoolExecutor(max_workers=self.config.max_processes) as executor:
                futures = {
                    executor.submit(self.optimize_single_combination, combo): combo
                    for combo in param_combinations
                }

                for future in as_completed(futures):
                    try:
                        result = future.result(timeout=30)
                        if result.optimization_score > -999:
                            results.append(result)
                    except Exception as e:
                        logger.error(f"優化組合失敗: {e}")

            # 排序並返回最佳結果
            results.sort(key=lambda x: x.optimization_score, reverse=True)

            best_result = results[0] if results else None

            end_time = time.time()
            optimization_time = end_time - start_time

            return {
                "success": True,
                "symbol": symbol,
                "best_parameters": best_result._asdict() if best_result else None,
                "total_combinations_tested": len(param_combinations),
                "optimization_time": optimization_time,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"策略優化失敗 {symbol}: {e}")
            return {
                "success": False,
                "error": str(e),
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
            }

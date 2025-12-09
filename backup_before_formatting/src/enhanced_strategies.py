# 增強策略優化器 - 整合來自新倉庫的改進
import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import quantstats as qs

logger = logging.getLogger(__name__)


class EnhancedStrategyOptimizer:
    """增強策略優化器 - 整合多種策略類型以提高真實性"""

    def __init__(self):
        self.initial_capital = 100000
        self.commission_rate = 0.001

    def optimize_strategies(
        self, data: List[Dict], strategy_types: List[str] = None
    ) -> List[Dict]:
        """運行多策略優化"""
        if strategy_types is None:
            strategy_types = ["ma", "rsi", "macd", "bollinger", "north_south"]

        results = []

        for strategy_type in strategy_types:
            if strategy_type == "ma":
                results.extend(self._optimize_ma_strategies(data))
            elif strategy_type == "rsi":
                results.extend(self._optimize_rsi_strategies(data))
            elif strategy_type == "macd":
                results.extend(self._optimize_macd_strategies(data))
            elif strategy_type == "bollinger":
                results.extend(self._optimize_bollinger_strategies(data))
            elif strategy_type == "north_south":
                results.extend(self._optimize_north_south_strategies(data))

        # 按Sharpe比率排序
        results.sort(key=lambda x: x.get("sharpe_ratio", 0), reverse=True)
        return results

    def _optimize_ma_strategies(self, data: List[Dict]) -> List[Dict]:
        """優化MA交叉策略"""
        results = []
        df = pd.DataFrame(data)

        for short_window in range(5, 21, 2):  # 5, 7, 9, ..., 19
            for long_window in range(20, 51, 5):  # 20, 25, 30, ..., 50
                if short_window < long_window:
                    try:
                        result = self._run_ma_strategy(
                            df.copy(), short_window, long_window
                        )
                        if result:
                            results.append(result)
                    except Exception as e:
                        logger.error(f"MA策略優化失敗: {e}")
                        continue

        return results

    def _optimize_rsi_strategies(self, data: List[Dict]) -> List[Dict]:
        """優化RSI策略"""
        results = []
        df = pd.DataFrame(data)

        for oversold in range(20, 41, 5):  # 20, 25, 30, 35, 40
            for overbought in range(60, 81, 5):  # 60, 65, 70, 75, 80
                if oversold < overbought:
                    try:
                        result = self._run_rsi_strategy(df.copy(), oversold, overbought)
                        if result:
                            results.append(result)
                    except Exception as e:
                        logger.error(f"RSI策略優化失敗: {e}")
                        continue

        return results

    def _optimize_macd_strategies(self, data: List[Dict]) -> List[Dict]:
        """優化MACD策略"""
        results = []
        df = pd.DataFrame(data)

        macd_configs = [(12, 26, 9), (8, 21, 8), (10, 22, 9), (15, 30, 10)]

        for fast, slow, signal in macd_configs:
            try:
                result = self._run_macd_strategy(df.copy(), fast, slow, signal)
                if result:
                    results.append(result)
            except Exception as e:
                logger.error(f"MACD策略優化失敗: {e}")
                continue

        return results

    def _optimize_bollinger_strategies(self, data: List[Dict]) -> List[Dict]:
        """優化布林帶策略"""
        results = []
        df = pd.DataFrame(data)

        for period in range(15, 26, 2):  # 15, 17, 19, 21, 23, 25
            for std_dev in [1.5, 2.0, 2.5]:
                try:
                    result = self._run_bollinger_strategy(df.copy(), period, std_dev)
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.error(f"布林帶策略優化失敗: {e}")
                    continue

        return results

    def _optimize_north_south_strategies(self, data: List[Dict]) -> List[Dict]:
        """優化南北向資金策略"""
        # 這裡可以整合北向資金數據
        # 目前返回空列表，之後可以擴展
        return []

    def _run_ma_strategy(
        self, df: pd.DataFrame, short_window: int, long_window: int
    ) -> Optional[Dict]:
        """運行MA交叉策略"""
        try:
            df[f"ma_short_{short_window}"] = df["close"].rolling(short_window).mean()
            df[f"ma_long_{long_window}"] = df["close"].rolling(long_window).mean()
            df.dropna(inplace=True)

            if len(df) < 50:
                return None

            # 生成交易信號
            df["signal"] = np.where(
                df[f"ma_short_{short_window}"] > df[f"ma_long_{long_window}"], 1, -1
            )
            df["position"] = df["signal"].diff().fillna(0)

            return self._calculate_performance(
                df, f"MA交叉({short_window},{long_window})"
            )

        except Exception as e:
            logger.error(f"MA策略運行失敗: {e}")
            return None

    def _run_rsi_strategy(
        self, df: pd.DataFrame, oversold: int, overbought: int
    ) -> Optional[Dict]:
        """運行RSI策略"""
        try:
            # 計算RSI
            delta = df["close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df["rsi"] = 100 - (100 / (1 + rs))
            df.dropna(inplace=True)

            if len(df) < 50:
                return None

            # 生成交易信號
            df["signal"] = 0
            df.loc[df["rsi"] < oversold, "signal"] = 1
            df.loc[df["rsi"] > overbought, "signal"] = -1
            df["position"] = df["signal"].diff().fillna(0)

            return self._calculate_performance(df, f"RSI({oversold},{overbought})")

        except Exception as e:
            logger.error(f"RSI策略運行失敗: {e}")
            return None

    def _run_macd_strategy(
        self, df: pd.DataFrame, fast: int, slow: int, signal: int
    ) -> Optional[Dict]:
        """運行MACD策略"""
        try:
            # 計算MACD
            ema_fast = df["close"].ewm(span=fast).mean()
            ema_slow = df["close"].ewm(span=slow).mean()
            df["macd"] = ema_fast - ema_slow
            df["macd_signal"] = df["macd"].ewm(span=signal).mean()
            df.dropna(inplace=True)

            if len(df) < 50:
                return None

            # 生成交易信號
            df["signal"] = np.where(df["macd"] > df["macd_signal"], 1, -1)
            df["position"] = df["signal"].diff().fillna(0)

            return self._calculate_performance(df, f"MACD({fast},{slow},{signal})")

        except Exception as e:
            logger.error(f"MACD策略運行失敗: {e}")
            return None

    def _run_bollinger_strategy(
        self, df: pd.DataFrame, period: int, std_dev: float
    ) -> Optional[Dict]:
        """運行布林帶策略"""
        try:
            # 計算布林帶
            df["bb_middle"] = df["close"].rolling(window=period).mean()
            bb_std = df["close"].rolling(window=period).std()
            df["bb_upper"] = df["bb_middle"] + (bb_std * std_dev)
            df["bb_lower"] = df["bb_middle"] - (bb_std * std_dev)
            df.dropna(inplace=True)

            if len(df) < 50:
                return None

            # 生成交易信號
            df["signal"] = 0
            df.loc[df["close"] < df["bb_lower"], "signal"] = 1
            df.loc[df["close"] > df["bb_upper"], "signal"] = -1
            df["position"] = df["signal"].diff().fillna(0)

            return self._calculate_performance(df, f"布林帶({period},{std_dev})")

        except Exception as e:
            logger.error(f"布林帶策略運行失敗: {e}")
            return None

    def _calculate_performance(self, df: pd.DataFrame, strategy_name: str) -> Dict:
        """計算策略績效 - 使用quantstats提高真實性"""
        try:
            # 計算回報
            df["returns"] = df["close"].pct_change()
            df["strategy_returns"] = df["position"].shift(1) * df["returns"]
            df["cumulative_returns"] = (1 + df["strategy_returns"]).cumprod()

            # 使用quantstats計算進階指標
            strategy_returns = df["strategy_returns"].dropna()

            if len(strategy_returns) < 30:
                # 如果數據不足，使用基本計算
                total_return = (df["cumulative_returns"].iloc[-1] - 1) * 100
                annual_return = (
                    (df["cumulative_returns"].iloc[-1] ** (252 / len(df))) - 1
                ) * 100
                volatility = df["strategy_returns"].std() * np.sqrt(252) * 100
                sharpe_ratio = annual_return / volatility if volatility > 0 else 0

                # 最大回撤
                cumulative = df["cumulative_returns"]
                running_max = cumulative.expanding().max()
                drawdown = (cumulative - running_max) / running_max
                max_drawdown = drawdown.min() * 100

                # 勝率
                winning_trades = (df["strategy_returns"] > 0).sum()
                total_trades = (df["strategy_returns"] != 0).sum()
                win_rate = (
                    (winning_trades / total_trades * 100) if total_trades > 0 else 0
                )

                # 交易次數
                trade_count = (df["position"] != 0).sum()

                return {
                    "strategy_name": strategy_name,
                    "sharpe_ratio": round(sharpe_ratio, 3),
                    "total_return": round(total_return, 2),
                    "annual_return": round(annual_return, 2),
                    "volatility": round(volatility, 2),
                    "max_drawdown": round(max_drawdown, 2),
                    "win_rate": round(win_rate, 2),
                    "trade_count": int(trade_count),
                    "final_value": round(
                        df["cumulative_returns"].iloc[-1] * self.initial_capital, 2
                    ),
                }

            # 使用quantstats計算
            try:
                qs_returns = qs.utils.to_returns(strategy_returns)

                sharpe_ratio = qs.stats.sharpe(qs_returns)
                total_return = qs.stats.comp(qs_returns) * 100
                annual_return = qs.stats.cagr(qs_returns) * 100
                volatility = qs.stats.volatility(qs_returns) * 100
                max_drawdown = qs.stats.max_drawdown(qs_returns) * 100
                win_rate = qs.stats.win_rate(qs_returns) * 100

                # 計算交易次數
                trade_count = (df["position"] != 0).sum()

                return {
                    "strategy_name": strategy_name,
                    "sharpe_ratio": round(float(sharpe_ratio), 3),
                    "total_return": round(float(total_return), 2),
                    "annual_return": round(float(annual_return), 2),
                    "volatility": round(float(volatility), 2),
                    "max_drawdown": round(float(max_drawdown), 2),
                    "win_rate": round(float(win_rate), 2),
                    "trade_count": int(trade_count),
                    "final_value": round(
                        df["cumulative_returns"].iloc[-1] * self.initial_capital, 2
                    ),
                }

            except Exception as qs_error:
                logger.warning(f"quantstats計算失敗，使用基本計算: {qs_error}")
                # 返回基本計算結果
                return self._calculate_basic_performance(df, strategy_name)

        except Exception as e:
            logger.error(f"績效計算失敗: {e}")
            return None

    def _calculate_basic_performance(
        self, df: pd.DataFrame, strategy_name: str
    ) -> Dict:
        """基本績效計算（備用）"""
        total_return = (df["cumulative_returns"].iloc[-1] - 1) * 100
        annual_return = (
            (df["cumulative_returns"].iloc[-1] ** (252 / len(df))) - 1
        ) * 100
        volatility = df["strategy_returns"].std() * np.sqrt(252) * 100
        sharpe_ratio = annual_return / volatility if volatility > 0 else 0

        cumulative = df["cumulative_returns"]
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min() * 100

        winning_trades = (df["strategy_returns"] > 0).sum()
        total_trades = (df["strategy_returns"] != 0).sum()
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        trade_count = (df["position"] != 0).sum()

        return {
            "strategy_name": strategy_name,
            "sharpe_ratio": round(sharpe_ratio, 3),
            "total_return": round(total_return, 2),
            "annual_return": round(annual_return, 2),
            "volatility": round(volatility, 2),
            "max_drawdown": round(max_drawdown, 2),
            "win_rate": round(win_rate, 2),
            "trade_count": int(trade_count),
            "final_value": round(
                df["cumulative_returns"].iloc[-1] * self.initial_capital, 2
            ),
        }


# 實例化優化器
enhanced_optimizer = EnhancedStrategyOptimizer()

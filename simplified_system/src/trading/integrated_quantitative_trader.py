#!/usr / bin / env python3
"""
集成量化交易平台
Integrated Quantitative Trading Platform

整合高级技术分析信号到完整的量化交易系统
Integrate advanced technical analysis signals into a complete quantitative trading system
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from api.government_data import get_hibor_data, get_latest_hibor
from api.stock_api import get_hk_stock_data
from data.historical_data_extender import extend_data_records

# Import our advanced analysis components
from indicators.advanced_ta_signals import AdvancedTechnicalSignals

from backtest.vectorbt_engine import VectorBTEngine
from telegram.telegram_bot import TelegramBot

# Setup logging
logging.basicConfig(
    level = logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SignalType(Enum):
    """信號類型枚舉"""

    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    STRONG_BUY = "strong_buy"
    STRONG_SELL = "strong_sell"


class OrderType(Enum):
    """訂單類型枚舉"""

    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


@dataclass
class TradingSignal:
    """交易信號數據結構"""

    symbol: str
    signal_type: SignalType
    confidence: float  # 0 - 1
    signal_strength: float  # 信號強度
    price: float
    timestamp: datetime
    indicators: Dict[str, Any]
    risk_score: float
    expected_return: float
    time_horizon: str  # short, medium, long

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "symbol": self.symbol,
            "signal_type": self.signal_type.value,
            "confidence": self.confidence,
            "signal_strength": self.signal_strength,
            "price": self.price,
            "timestamp": self.timestamp.isoformat(),
            "indicators": self.indicators,
            "risk_score": self.risk_score,
            "expected_return": self.expected_return,
            "time_horizon": self.time_horizon,
        }


@dataclass
class Position:
    """持倉數據結構"""

    symbol: str
    quantity: int
    entry_price: float
    current_price: float
    unrealized_pnl: float
    entry_date: datetime
    last_signal: Optional[TradingSignal] = None


class IntegratedQuantitativeTrader:
    """集成量化交易員"""

    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions: Dict[str, Position] = {}
        self.trade_history: List[Dict] = []
        self.signals_history: List[TradingSignal] = []

        # 初始化組件
        self.advanced_signals = AdvancedTechnicalSignals()
        self.vectorbt_engine = VectorBTEngine()
        self.telegram_bot = TelegramBot()

        # 交易配置
        self.config = {
            "max_position_size": 0.1,  # 最大持倉比例10%
            "stop_loss_pct": 0.05,  # 止損5%
            "take_profit_pct": 0.15,  # 止盈15%
            "min_signal_confidence": 0.6,  # 最小信號置信度
            "max_positions": 5,  # 最大持倉數量
            "rebalance_frequency": "daily",  # 再平衡頻率
            "risk_limit": 0.02,  # 風險限制2%
        }

        logger.info(
            f"Integrated Quantitative Trader initialized with capital: ${initial_capital:,.2f}"
        )

    async def analyze_symbol(
        self, symbol: str, extend_data: bool = True
    ) -> Optional[TradingSignal]:
        """分析單個股票符號並生成交易信號"""
        try:
            logger.info(f"Analyzing symbol: {symbol}")

            # 獲取股票數據
            stock_data = get_hk_stock_data(symbol, 365)  # 1年數據
            if not stock_data:
                logger.error(f"No data available for {symbol}")
                return None

            # 獲取政府數據
            gov_data = get_hibor_data(365)
            if not gov_data:
                logger.warning("No government data available, using stock data only")
                gov_data = []

            # 擴展數據（如果需要）
            if extend_data and len(stock_data) < 1000:
                # 轉換股票數據為擴展器格式
                stock_records = []
                for i, row in stock_data.iterrows():
                    stock_records.append(
                        {
                            "date": row.name.strftime("%Y-%m-%d"),
                            "price": row["close"],
                            "volume": row["volume"],
                            "high": row["high"],
                            "low": row["low"],
                            "open": row["open"],
                        }
                    )

                extension_result = extend_data_records(
                    stock_records, 1000, "hybrid_approach"
                )
                if extension_result.get("success"):
                    # 轉換回DataFrame格式
                    extended_records = extension_result["data"]
                    extended_df = pd.DataFrame(extended_records)
                    extended_df["date"] = pd.to_datetime(extended_df["date"])
                    extended_df.set_index("date", inplace = True)
                    stock_data = extended_df
                    logger.info(f"Extended {symbol} data to {len(stock_data)} records")

            # 生成高級技術分析信號
            price_series = stock_data["close"]
            analysis_result = self.advanced_signals.generate_enhanced_signals(
                data=(
                    stock_records
                    if len(stock_data) < 1000
                    else stock_data.to_dict("records")
                ),
                data_type="price",
                extend_to_1000 = False,  # 已經擴展過
                optimize_signals = True,
            )

            if not analysis_result.get("success"):
                logger.error(f"Signal analysis failed for {symbol}")
                return None

            # 提取關鍵信號信息
            signal_quality = analysis_result.get("signal_quality_score", 0)
            composite_signals = analysis_result.get("composite_signals", {})

            # 決定信號類型和置信度
            signal_type, confidence = self._determine_signal_type(
                composite_signals, signal_quality
            )

            if confidence < self.config["min_signal_confidence"]:
                logger.info(f"Signal confidence too low for {symbol}: {confidence:.2f}")
                return None

            # 計算當前價格和相關指標
            current_price = price_series.iloc[-1]
            risk_score = self._calculate_position_risk(composite_signals)
            expected_return = self._calculate_expected_return(
                composite_signals, risk_score
            )
            time_horizon = self._determine_time_horizon(composite_signals)

            # 創建交易信號
            signal = TradingSignal(
                symbol = symbol,
                signal_type = signal_type,
                confidence = confidence,
                signal_strength = signal_quality / 10.0,  # 轉換為0 - 1範圍
                price = current_price,
                timestamp = datetime.now(),
                indicators = composite_signals,
                risk_score = risk_score,
                expected_return = expected_return,
                time_horizon = time_horizon,
            )

            logger.info(
                f"Generated {signal_type.value} signal for {symbol} with confidence {confidence:.2f}"
            )
            return signal

        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return None

    def _determine_signal_type(
        self, composite_signals: Dict, signal_quality: float
    ) -> Tuple[SignalType, float]:
        """確定信號類型和置信度"""
        try:
            buy_signals = 0
            sell_signals = 0
            total_signals = 0

            for column, signals in composite_signals.items():
                if isinstance(signals, dict):
                    final_signal = signals.get("final_signal", 0)
                    if final_signal > 0:
                        buy_signals += 1
                    elif final_signal < 0:
                        sell_signals += 1
                    total_signals += 1

            if total_signals == 0:
                return SignalType.HOLD, 0.0

            # 計算淨信號
            net_signal = (buy_signals - sell_signals) / total_signals

            # 結合信號質量
            confidence = min(1.0, signal_quality / 10.0 * abs(net_signal))

            # 確定信號類型
            if net_signal > 0.6:
                return SignalType.STRONG_BUY, confidence
            elif net_signal > 0.2:
                return SignalType.BUY, confidence
            elif net_signal < -0.6:
                return SignalType.STRONG_SELL, confidence
            elif net_signal < -0.2:
                return SignalType.SELL, confidence
            else:
                return SignalType.HOLD, confidence

        except Exception as e:
            logger.error(f"Error determining signal type: {e}")
            return SignalType.HOLD, 0.0

    def _calculate_position_risk(self, composite_signals: Dict) -> float:
        """計算持倉風險分數"""
        try:
            risk_scores = []

            for column, signals in composite_signals.items():
                if isinstance(signals, dict) and "risk_assessment" in signals:
                    risk_data = signals["risk_assessment"]
                    if (
                        isinstance(risk_data, dict)
                        and "overall_risk_score" in risk_data
                    ):
                        risk_scores.append(risk_data["overall_risk_score"])

            if risk_scores:
                return np.mean(risk_scores)
            else:
                return 0.5  # 默認中等風險

        except Exception as e:
            logger.error(f"Error calculating position risk: {e}")
            return 0.5

    def _calculate_expected_return(
        self, composite_signals: Dict, risk_score: float
    ) -> float:
        """計算預期回報"""
        try:
            # 基於信號強度和風險調整預期回報
            signal_strength = 0.0
            signal_count = 0

            for column, signals in composite_signals.items():
                if isinstance(signals, dict):
                    final_signal = signals.get("final_signal", 0)
                    signal_strength += abs(final_signal)
                    signal_count += 1

            if signal_count > 0:
                avg_signal_strength = signal_strength / signal_count
                # 風險調整
                base_return = avg_signal_strength * 0.2  # 基礎20%回報
                risk_adjusted_return = base_return * (1 - risk_score * 0.5)
                return max(0.0, risk_adjusted_return)
            else:
                return 0.0

        except Exception as e:
            logger.error(f"Error calculating expected return: {e}")
            return 0.0

    def _determine_time_horizon(self, composite_signals: Dict) -> str:
        """確定時間範圍"""
        try:
            timeframe_weights = {"short": 0, "medium": 0, "long": 0}

            for column, signals in composite_signals.items():
                if isinstance(signals, dict) and "multi_timeframe_signals" in signals:
                    timeframes = signals["multi_timeframe_signals"]
                    if isinstance(timeframes, dict):
                        # 簡化處理：基於時間框架信號的強度來決定主要時間範圍
                        for tf_type, tf_signals in timeframes.items():
                            if tf_type == "short_term":
                                timeframe_weights["short"] += (
                                    len(tf_signals)
                                    if isinstance(tf_signals, dict)
                                    else 0
                                )
                            elif tf_type == "medium_term":
                                timeframe_weights["medium"] += (
                                    len(tf_signals)
                                    if isinstance(tf_signals, dict)
                                    else 0
                                )
                            elif tf_type == "long_term":
                                timeframe_weights["long"] += (
                                    len(tf_signals)
                                    if isinstance(tf_signals, dict)
                                    else 0
                                )

            # 選擇權重最大的時間範圍
            max_weight = max(timeframe_weights.values())
            if max_weight == 0:
                return "medium"  # 默認中期

            for tf, weight in timeframe_weights.items():
                if weight == max_weight:
                    return tf

            return "medium"

        except Exception as e:
            logger.error(f"Error determining time horizon: {e}")
            return "medium"

    async def execute_trading_decision(
        self, signal: TradingSignal
    ) -> Optional[Dict[str, Any]]:
        """執行交易決策"""
        try:
            if signal.confidence < self.config["min_signal_confidence"]:
                return None

            current_position = self.positions.get(signal.symbol)

            # 檢查是否已達最大持倉數量
            if (
                not current_position
                and len(self.positions) >= self.config["max_positions"]
            ):
                logger.info(f"Maximum positions reached, skipping {signal.symbol}")
                return None

            # 檢查持倉比例限制
            position_value = self.current_capital * self.config["max_position_size"]

            if signal.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
                return await self._execute_buy_order(signal, position_value)
            elif signal.signal_type in [SignalType.SELL, SignalType.STRONG_SELL]:
                return await self._execute_sell_order(signal)
            else:
                logger.info(f"HOLD signal for {signal.symbol}")
                return None

        except Exception as e:
            logger.error(f"Error executing trading decision for {signal.symbol}: {e}")
            return None

    async def _execute_buy_order(
        self, signal: TradingSignal, position_value: float
    ) -> Dict[str, Any]:
        """執行買入訂單"""
        try:
            if signal.symbol in self.positions:
                logger.info(f"Already holding position in {signal.symbol}")
                return None

            # 計算股數
            quantity = int(position_value / signal.price)
            if quantity <= 0:
                return None

            # 執行訂單（模擬）
            order_cost = quantity * signal.price
            if order_cost > self.current_capital:
                logger.warning(f"Insufficient capital for {signal.symbol} order")
                return None

            # 創建持倉
            position = Position(
                symbol = signal.symbol,
                quantity = quantity,
                entry_price = signal.price,
                current_price = signal.price,
                unrealized_pnl = 0.0,
                entry_date = datetime.now(),
                last_signal = signal,
            )

            # 更新資金和持倉
            self.current_capital -= order_cost
            self.positions[signal.symbol] = position

            # 記錄交易
            trade_record = {
                "symbol": signal.symbol,
                "action": "BUY",
                "quantity": quantity,
                "price": signal.price,
                "total_cost": order_cost,
                "timestamp": datetime.now().isoformat(),
                "signal_confidence": signal.confidence,
                "expected_return": signal.expected_return,
            }

            self.trade_history.append(trade_record)
            self.signals_history.append(signal)

            # 發送Telegram通知
            await self.telegram_bot.send_trade_alert(trade_record)

            logger.info(
                f"Executed BUY order for {quantity} shares of {signal.symbol} at ${signal.price:.2f}"
            )

            return trade_record

        except Exception as e:
            logger.error(f"Error executing buy order: {e}")
            return None

    async def _execute_sell_order(self, signal: TradingSignal) -> Dict[str, Any]:
        """執行賣出訂單"""
        try:
            if signal.symbol not in self.positions:
                logger.info(f"No position to sell in {signal.symbol}")
                return None

            position = self.positions[signal.symbol]

            # 檢查止損止盈
            current_return = (
                signal.price - position.entry_price
            ) / position.entry_price

            should_sell = False
            sell_reason = "signal"

            if current_return <= -self.config["stop_loss_pct"]:
                should_sell = True
                sell_reason = "stop_loss"
            elif current_return >= self.config["take_profit_pct"]:
                should_sell = True
                sell_reason = "take_profit"
            elif signal.signal_type in [SignalType.SELL, SignalType.STRONG_SELL]:
                should_sell = True
                sell_reason = "signal"

            if not should_sell:
                return None

            # 執行賣出訂單（模擬）
            sell_proceeds = position.quantity * signal.price
            position.unrealized_pnl = sell_proceeds - (
                position.quantity * position.entry_price
            )

            # 更新資金和持倉
            self.current_capital += sell_proceeds
            del self.positions[signal.symbol]

            # 記錄交易
            trade_record = {
                "symbol": signal.symbol,
                "action": "SELL",
                "quantity": position.quantity,
                "price": signal.price,
                "total_proceeds": sell_proceeds,
                "realized_pnl": position.unrealized_pnl,
                "pnl_percentage": (
                    (signal.price - position.entry_price) / position.entry_price
                )
                * 100,
                "holding_period_days": (datetime.now() - position.entry_date).days,
                "timestamp": datetime.now().isoformat(),
                "sell_reason": sell_reason,
                "signal_confidence": signal.confidence,
            }

            self.trade_history.append(trade_record)

            # 發送Telegram通知
            await self.telegram_bot.send_trade_alert(trade_record)

            logger.info(
                f"Executed SELL order for {position.quantity} shares of {signal.symbol} at ${signal.price:.2f}, PnL: ${position.unrealized_pnl:.2f}"
            )

            return trade_record

        except Exception as e:
            logger.error(f"Error executing sell order: {e}")
            return None

    async def run_trading_cycle(self, symbols: List[str]) -> Dict[str, Any]:
        """運行一個完整的交易週期"""
        try:
            logger.info(f"Starting trading cycle for {len(symbols)} symbols")

            cycle_results = {
                "start_time": datetime.now().isoformat(),
                "symbols_analyzed": len(symbols),
                "signals_generated": 0,
                "trades_executed": 0,
                "successful_trades": 0,
                "total_pnl": 0.0,
                "capital_utilization": 0.0,
                "open_positions": len(self.positions),
                "errors": [],
            }

            # 分析每個股票符號
            for symbol in symbols:
                try:
                    # 生成交易信號
                    signal = await self.analyze_symbol(symbol)

                    if signal:
                        cycle_results["signals_generated"] += 1

                        # 執行交易決策
                        trade_result = await self.execute_trading_decision(signal)

                        if trade_result:
                            cycle_results["trades_executed"] += 1

                            if (
                                trade_result["action"] == "SELL"
                                and trade_result.get("realized_pnl", 0) > 0
                            ):
                                cycle_results["successful_trades"] += 1
                                cycle_results["total_pnl"] += trade_result.get(
                                    "realized_pnl", 0
                                )

                except Exception as e:
                    error_msg = f"Error processing {symbol}: {str(e)}"
                    logger.error(error_msg)
                    cycle_results["errors"].append(error_msg)

            # 更新持倉價值
            total_position_value = 0.0
            for position in self.positions.values():
                position.current_price = position.entry_price * (
                    1
                    + position.unrealized_pnl
                    / (position.quantity * position.entry_price)
                )
                total_position_value += position.quantity * position.current_price

            cycle_results["capital_utilization"] = total_position_value / (
                self.current_capital + total_position_value
            )
            cycle_results["end_time"] = datetime.now().isoformat()

            # 生成週期報告
            await self._generate_cycle_report(cycle_results)

            logger.info(
                f"Trading cycle completed: {cycle_results['trades_executed']} trades, ${cycle_results['total_pnl']:.2f} PnL"
            )

            return cycle_results

        except Exception as e:
            logger.error(f"Error in trading cycle: {e}")
            return {"error": str(e)}

    async def _generate_cycle_report(self, cycle_results: Dict[str, Any]):
        """生成交易週期報告"""
        try:
            report = {
                "trading_cycle_summary": cycle_results,
                "portfolio_status": {
                    "current_capital": self.current_capital,
                    "total_return": (
                        (self.current_capital - self.initial_capital)
                        / self.initial_capital
                    )
                    * 100,
                    "open_positions": len(self.positions),
                    "positions": [
                        {
                            "symbol": pos.symbol,
                            "quantity": pos.quantity,
                            "entry_price": pos.entry_price,
                            "current_price": pos.current_price,
                            "unrealized_pnl": pos.unrealized_pnl,
                            "pnl_percentage": (
                                (pos.current_price - pos.entry_price) / pos.entry_price
                            )
                            * 100,
                        }
                        for pos in self.positions.values()
                    ],
                },
                "recent_trades": self.trade_history[-10:],  # 最近10筆交易
                "top_signals": [
                    {
                        "symbol": signal.symbol,
                        "signal_type": signal.signal_type.value,
                        "confidence": signal.confidence,
                        "expected_return": signal.expected_return,
                    }
                    for signal in sorted(
                        self.signals_history[-10:],
                        key = lambda x: x.confidence,
                        reverse = True,
                    )
                ],
            }

            # 保存報告
            report_file = (
                f"trading_cycle_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(report_file, "w") as f:
                json.dump(report, f, indent = 2, default = str)

            logger.info(f"Trading cycle report saved to {report_file}")

        except Exception as e:
            logger.error(f"Error generating cycle report: {e}")

    def get_performance_metrics(self) -> Dict[str, Any]:
        """獲取性能指標"""
        try:
            if not self.trade_history:
                return {
                    "total_trades": 0,
                    "win_rate": 0.0,
                    "total_return": 0.0,
                    "sharpe_ratio": 0.0,
                    "max_drawdown": 0.0,
                }

            # 計算基本指標
            total_trades = len(self.trade_history)
            profitable_trades = len(
                [t for t in self.trade_history if t.get("realized_pnl", 0) > 0]
            )
            win_rate = profitable_trades / total_trades if total_trades > 0 else 0.0

            total_return = (
                (self.current_capital - self.initial_capital) / self.initial_capital
            ) * 100

            # 計算日回報率序列
            daily_returns = []
            for trade in self.trade_history:
                if trade.get("pnl_percentage"):
                    daily_returns.append(trade["pnl_percentage"] / 100)

            if daily_returns:
                sharpe_ratio = (
                    np.mean(daily_returns) / np.std(daily_returns) * np.sqrt(252)
                    if np.std(daily_returns) > 0
                    else 0.0
                )
                cumulative_returns = np.cumprod(1 + np.array(daily_returns))
                running_max = np.maximum.accumulate(cumulative_returns)
                drawdowns = (cumulative_returns - running_max) / running_max
                max_drawdown = np.min(drawdowns) if len(drawdowns) > 0 else 0.0
            else:
                sharpe_ratio = 0.0
                max_drawdown = 0.0

            return {
                "total_trades": total_trades,
                "win_rate": win_rate,
                "total_return": total_return,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
                "current_capital": self.current_capital,
                "open_positions": len(self.positions),
            }

        except Exception as e:
            logger.error(f"Error calculating performance metrics: {e}")
            return {}


# 全局實例
integrated_trader = IntegratedQuantitativeTrader


# 便捷函數
async def run_comprehensive_trading_analysis(symbols: List[str]) -> Dict[str, Any]:
    """運行綜合交易分析"""
    trader = integrated_trader()
    return await trader.run_trading_cycle(symbols)


if __name__ == "__main__":
    print("=" * 80)
    print("Integrated Quantitative Trading Platform")
    print("集成量化交易平台")
    print("=" * 80)
    print("Starting comprehensive trading analysis...")
    print()

    # 示例股票符號
    symbols = ["0700.HK", "0941.HK", "1398.HK"]

    # 運行分析
    async def main():
        results = await run_comprehensive_trading_analysis(symbols)

        print(f"Analysis Results:")
        print(f"Symbols Analyzed: {results.get('symbols_analyzed', 0)}")
        print(f"Signals Generated: {results.get('signals_generated', 0)}")
        print(f"Trades Executed: {results.get('trades_executed', 0)}")
        print(f"Total PnL: ${results.get('total_pnl', 0):.2f}")
        print(f"Capital Utilization: {results.get('capital_utilization', 0):.1%}")

        # 獲取性能指標
        trader = integrated_trader()
        metrics = trader.get_performance_metrics()

        print(f"\nPerformance Metrics:")
        print(f"Total Return: {metrics.get('total_return', 0):.2f}%")
        print(f"Win Rate: {metrics.get('win_rate', 0):.1%}")
        print(f"Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.3f}")
        print(f"Max Drawdown: {metrics.get('max_drawdown', 0):.1%}")

    asyncio.run(main())

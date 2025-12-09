"""
港股量化交易 AI Agent 系统 - 量化分析师Agent

负责开发数学模型、进行统计分析、执行回测和预测市场波动。
这是系统的核心分析引擎，提供专业的量化分析能力。
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ..agents.base_agent import AgentConfig, BaseAgent
from ..agents.protocol import AgentProtocol, MessagePriority, MessageType
from ..core import SystemConfig, SystemConstants
from ..core.message_queue import Message, MessageQueue
from ..models.base import BaseModel, MarketData, SignalType, TradingSignal


@dataclass
class TechnicalIndicators:
    """技术指标计算结果"""

    # 趋势指标
    sma_20: float = 0.0
    sma_50: float = 0.0
    ema_12: float = 0.0
    ema_26: float = 0.0
    macd: float = 0.0
    macd_signal: float = 0.0
    macd_histogram: float = 0.0

    # 动量指标
    rsi: float = 0.0
    stochastic_k: float = 0.0
    stochastic_d: float = 0.0
    williams_r: float = 0.0

    # 波动性指标
    bollinger_upper: float = 0.0
    bollinger_middle: float = 0.0
    bollinger_lower: float = 0.0
    atr: float = 0.0

    # 成交量指标
    volume_sma: float = 0.0
    volume_ratio: float = 0.0


@dataclass
class BacktestResult:
    """回测结果"""

    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    profitable_trades: int
    average_win: float
    average_loss: float
    profit_factor: float
    start_date: datetime
    end_date: datetime


class QuantitativeAnalysisEngine:
    """量化分析引擎"""

    def __init__(self):
        self.logger = logging.getLogger("hk_quant_system.quantitative_analyst.engine")

    def calculate_technical_indicators(self, data: pd.DataFrame) -> TechnicalIndicators:
        """计算技术指标 - 优化版本"""
        try:
            if len(data) < 50:  # 需要足够的数据点
                raise ValueError("数据点不足，至少需要50个数据点")

            # 使用向量化操作提高性能
            close = data["close"].values
            high = data["high"].values
            low = data["low"].values
            volume = data["volume"].values

            indicators = TechnicalIndicators()

            # 移动平均线 - 使用pandas内置函数
            indicators.sma_20 = data["close"].rolling(window=20).mean().iloc[-1]
            indicators.sma_50 = data["close"].rolling(window=50).mean().iloc[-1]

            # EMA计算 - 使用pandas内置函数
            indicators.ema_12 = data["close"].ewm(span=12).mean().iloc[-1]
            indicators.ema_26 = data["close"].ewm(span=26).mean().iloc[-1]

            # MACD
            indicators.macd = indicators.ema_12 - indicators.ema_26
            macd_signal_alpha = 2 / (9 + 1)
            indicators.macd_signal = self._calculate_ema(
                [indicators.macd], macd_signal_alpha
            )
            indicators.macd_histogram = indicators.macd - indicators.macd_signal

            # RSI - 使用向量化计算
            indicators.rsi = self._calculate_rsi_vectorized(data["close"])

            # 布林带 - 使用pandas内置函数
            bb_period = 20
            bb_std = 2
            rolling_mean = data["close"].rolling(window=bb_period).mean()
            rolling_std = data["close"].rolling(window=bb_period).std()
            indicators.bollinger_middle = rolling_mean.iloc[-1]
            indicators.bollinger_upper = (rolling_mean + bb_std * rolling_std).iloc[-1]
            indicators.bollinger_lower = (rolling_mean - bb_std * rolling_std).iloc[-1]

            # ATR (平均真实波幅) - 优化版本
            indicators.atr = self._calculate_atr_vectorized(data)

            # 成交量指标 - 使用pandas内置函数
            indicators.volume_sma = data["volume"].rolling(window=20).mean().iloc[-1]
            indicators.volume_ratio = (
                volume[-1] / indicators.volume_sma if indicators.volume_sma > 0 else 1.0
            )

            return indicators

        except Exception as e:
            self.logger.error(f"计算技术指标失败: {e}")
            return TechnicalIndicators()

    def _calculate_ema(self, prices: List[float], alpha: float) -> float:
        """计算指数移动平均 - 保持向后兼容"""
        if len(prices) == 1:
            return prices[0]

        ema = prices[0]
        for price in prices[1:]:
            ema = alpha * price + (1 - alpha) * ema
        return ema

    def _calculate_rsi_vectorized(self, prices: pd.Series, period: int = 14) -> float:
        """向量化RSI计算 - 性能优化版本"""
        if len(prices) < period + 1:
            return 50.0

        # 计算价格变化
        delta = prices.diff()

        # 分离上涨和下跌
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)

        # 计算平均收益和损失
        avg_gains = gains.rolling(window=period).mean()
        avg_losses = losses.rolling(window=period).mean()

        # 计算RSI
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))

        return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50.0

    def _calculate_atr_vectorized(self, data: pd.DataFrame, period: int = 14) -> float:
        """向量化ATR计算 - 性能优化版本"""
        if len(data) < period + 1:
            return 0.0

        # 计算真实波幅
        high = data["high"]
        low = data["low"]
        close = data["close"]

        # 计算三个值
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))

        # 取最大值
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # 计算ATR
        atr = true_range.rolling(window=period).mean()

        return atr.iloc[-1] if not pd.isna(atr.iloc[-1]) else 0.0

    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """计算RSI指标"""
        if len(prices) < period + 1:
            return 50.0

        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_atr(
        self, high: List[float], low: List[float], close: List[float], period: int = 14
    ) -> float:
        """计算ATR指标"""
        if len(high) < period + 1:
            return 0.0

        tr_list = []
        for i in range(1, len(high)):
            tr = max(
                high[i] - low[i],
                abs(high[i] - close[i - 1]),
                abs(low[i] - close[i - 1]),
            )
            tr_list.append(tr)

        return np.mean(tr_list[-period:])

    def analyze_market_trend(self, indicators: TechnicalIndicators) -> Dict[str, Any]:
        """分析市场趋势"""
        trend_analysis = {
            "trend_direction": "neutral",
            "trend_strength": 0.0,
            "confidence": 0.0,
            "signals": [],
        }

        try:
            signals = []
            confidence_factors = []

            # 移动平均线趋势
            if indicators.sma_20 > indicators.sma_50:
                signals.append("bullish_sma")
                confidence_factors.append(0.3)
            elif indicators.sma_20 < indicators.sma_50:
                signals.append("bearish_sma")
                confidence_factors.append(-0.3)

            # MACD趋势
            if (
                indicators.macd > indicators.macd_signal
                and indicators.macd_histogram > 0
            ):
                signals.append("bullish_macd")
                confidence_factors.append(0.4)
            elif (
                indicators.macd < indicators.macd_signal
                and indicators.macd_histogram < 0
            ):
                signals.append("bearish_macd")
                confidence_factors.append(-0.4)

            # RSI超买超卖
            if indicators.rsi > 70:
                signals.append("overbought_rsi")
                confidence_factors.append(-0.2)
            elif indicators.rsi < 30:
                signals.append("oversold_rsi")
                confidence_factors.append(0.2)

            # 布林带位置
            if indicators.bollinger_middle > 0:
                price_position = (indicators.sma_20 - indicators.bollinger_lower) / (
                    indicators.bollinger_upper - indicators.bollinger_lower
                )
                if price_position > 0.8:
                    signals.append("near_upper_band")
                    confidence_factors.append(-0.1)
                elif price_position < 0.2:
                    signals.append("near_lower_band")
                    confidence_factors.append(0.1)

            # 计算总体趋势
            total_confidence = sum(confidence_factors)
            trend_strength = abs(total_confidence)

            if total_confidence > 0.3:
                trend_direction = "bullish"
            elif total_confidence < -0.3:
                trend_direction = "bearish"
            else:
                trend_direction = "neutral"

            trend_analysis.update(
                {
                    "trend_direction": trend_direction,
                    "trend_strength": trend_strength,
                    "confidence": min(abs(total_confidence), 1.0),
                    "signals": signals,
                }
            )

        except Exception as e:
            self.logger.error(f"趋势分析失败: {e}")

        return trend_analysis

    def generate_trading_signals(
        self, indicators: TechnicalIndicators, trend_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成交易信号"""
        signals = []

        try:
            confidence = trend_analysis.get("confidence", 0.0)
            trend_direction = trend_analysis.get("trend_direction", "neutral")

            # 基础信号生成逻辑
            if confidence > 0.6:  # 高置信度
                if trend_direction == "bullish":
                    signal = {
                        "signal_type": SignalType.BUY,
                        "confidence": confidence,
                        "reasoning": f"强看涨信号，置信度: {confidence:.2f}",
                        "indicators": {
                            "sma_trend": indicators.sma_20 > indicators.sma_50,
                            "macd_bullish": indicators.macd > indicators.macd_signal,
                            "rsi_level": indicators.rsi,
                        },
                    }
                    signals.append(signal)

                elif trend_direction == "bearish":
                    signal = {
                        "signal_type": SignalType.SELL,
                        "confidence": confidence,
                        "reasoning": f"强看跌信号，置信度: {confidence:.2f}",
                        "indicators": {
                            "sma_trend": indicators.sma_20 < indicators.sma_50,
                            "macd_bearish": indicators.macd < indicators.macd_signal,
                            "rsi_level": indicators.rsi,
                        },
                    }
                    signals.append(signal)

            elif confidence > 0.3:  # 中等置信度
                if trend_direction in ["bullish", "bearish"]:
                    signal_type = (
                        SignalType.BUY
                        if trend_direction == "bullish"
                        else SignalType.SELL
                    )
                    signal = {
                        "signal_type": signal_type,
                        "confidence": confidence,
                        "reasoning": f"中等{signal_type}信号，置信度: {confidence:.2f}",
                        "indicators": {
                            "trend_strength": trend_analysis.get("trend_strength", 0.0),
                            "signal_count": len(trend_analysis.get("signals", [])),
                        },
                    }
                    signals.append(signal)

        except Exception as e:
            self.logger.error(f"生成交易信号失败: {e}")

        return signals

    def predict_volatility(
        self, data: pd.DataFrame, horizon_days: int = 5
    ) -> Dict[str, float]:
        """预测波动率"""
        try:
            if len(data) < 30:
                return {"predicted_volatility": 0.0, "confidence": 0.0}

            returns = data["close"].pct_change().dropna()

            # 计算历史波动率
            historical_vol = returns.std() * np.sqrt(252)  # 年化波动率

            # 使用GARCH模型预测（简化版本）
            # 这里使用简单的移动平均作为替代
            recent_vol = returns.tail(10).std() * np.sqrt(252)

            # 预测未来波动率
            predicted_vol = historical_vol * 0.7 + recent_vol * 0.3

            # 置信度基于数据质量
            confidence = min(len(data) / 100, 1.0)

            return {
                "predicted_volatility": predicted_vol,
                "historical_volatility": historical_vol,
                "recent_volatility": recent_vol,
                "confidence": confidence,
            }

        except Exception as e:
            self.logger.error(f"波动率预测失败: {e}")
            return {"predicted_volatility": 0.0, "confidence": 0.0}


class BacktestEngine:
    """回测引擎"""

    def __init__(self):
        self.logger = logging.getLogger("hk_quant_system.quantitative_analyst.backtest")

    def run_backtest(
        self,
        data: pd.DataFrame,
        signals: List[Dict[str, Any]],
        initial_capital: float = 100000.0,
        commission: float = 0.001,
    ) -> BacktestResult:
        """运行回测"""
        try:
            if len(data) == 0 or len(signals) == 0:
                raise ValueError("数据或信号为空")

            # 初始化回测参数
            capital = initial_capital
            position = 0
            trades = []
            portfolio_values = []

            # 创建信号时间索引
            signal_dict = {}
            for signal in signals:
                timestamp = signal.get("timestamp", data.index[0])
                signal_dict[timestamp] = signal

            # 遍历数据执行回测
            for i, (timestamp, row) in enumerate(data.iterrows()):
                current_price = row["close"]

                # 检查是否有信号
                if timestamp in signal_dict:
                    signal = signal_dict[timestamp]
                    signal_type = signal["signal_type"]
                    confidence = signal["confidence"]

                    # 执行交易
                    if signal_type == SignalType.BUY and position == 0:
                        # 买入
                        shares = int((capital * 0.95) / current_price)  # 95 % 资金
                        if shares > 0:
                            cost = shares * current_price * (1 + commission)
                            capital -= cost
                            position = shares

                            trades.append(
                                {
                                    "timestamp": timestamp,
                                    "type": "buy",
                                    "price": current_price,
                                    "shares": shares,
                                    "cost": cost,
                                    "confidence": confidence,
                                }
                            )

                    elif signal_type == SignalType.SELL and position > 0:
                        # 卖出
                        proceeds = position * current_price * (1 - commission)
                        capital += proceeds

                        trades.append(
                            {
                                "timestamp": timestamp,
                                "type": "sell",
                                "price": current_price,
                                "shares": position,
                                "proceeds": proceeds,
                                "confidence": confidence,
                            }
                        )

                        position = 0

                # 计算当前组合价值
                portfolio_value = capital + (position * current_price)
                portfolio_values.append(portfolio_value)

            # 计算绩效指标
            result = self._calculate_performance_metrics(
                initial_capital, portfolio_values, trades, data.index[0], data.index[-1]
            )

            return result

        except Exception as e:
            self.logger.error(f"回测执行失败: {e}")
            # 返回默认结果
            return BacktestResult(
                total_return=0.0,
                annualized_return=0.0,
                volatility=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                win_rate=0.0,
                total_trades=0,
                profitable_trades=0,
                average_win=0.0,
                average_loss=0.0,
                profit_factor=0.0,
                start_date=data.index[0] if len(data) > 0 else datetime.now(),
                end_date=data.index[-1] if len(data) > 0 else datetime.now(),
            )

    def _calculate_performance_metrics(
        self,
        initial_capital: float,
        portfolio_values: List[float],
        trades: List[Dict[str, Any]],
        start_date: datetime,
        end_date: datetime,
    ) -> BacktestResult:
        """计算绩效指标"""

        if len(portfolio_values) == 0:
            return BacktestResult(
                total_return=0.0,
                annualized_return=0.0,
                volatility=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                win_rate=0.0,
                total_trades=0,
                profitable_trades=0,
                average_win=0.0,
                average_loss=0.0,
                profit_factor=0.0,
                start_date=start_date,
                end_date=end_date,
            )

        # 基础指标
        final_value = portfolio_values[-1]
        total_return = (final_value - initial_capital) / initial_capital

        # 年化收益率
        days = (end_date - start_date).days
        years = days / 365.25
        annualized_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0.0

        # 波动率
        returns = []
        for i in range(1, len(portfolio_values)):
            ret = (portfolio_values[i] - portfolio_values[i - 1]) / portfolio_values[
                i - 1
            ]
            returns.append(ret)

        volatility = np.std(returns) * np.sqrt(252) if returns else 0.0

        # 夏普比率 (假设无风险利率为3%)
        risk_free_rate = 0.03
        sharpe_ratio = (
            (annualized_return - risk_free_rate) / volatility if volatility > 0 else 0.0
        )

        # 最大回撤
        peak = initial_capital
        max_drawdown = 0.0
        for value in portfolio_values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            max_drawdown = max(max_drawdown, drawdown)

        # 交易统计
        total_trades = len(trades) // 2  # 买卖配对
        profitable_trades = 0
        total_wins = 0.0
        total_losses = 0.0

        # 计算盈亏
        for i in range(0, len(trades), 2):
            if i + 1 < len(trades):
                buy_trade = trades[i]
                sell_trade = trades[i + 1]

                if buy_trade["type"] == "buy" and sell_trade["type"] == "sell":
                    pnl = sell_trade["proceeds"] - buy_trade["cost"]
                    if pnl > 0:
                        profitable_trades += 1
                        total_wins += pnl
                    else:
                        total_losses += abs(pnl)

        win_rate = profitable_trades / total_trades if total_trades > 0 else 0.0
        average_win = total_wins / profitable_trades if profitable_trades > 0 else 0.0
        average_loss = (
            total_losses / (total_trades - profitable_trades)
            if (total_trades - profitable_trades) > 0
            else 0.0
        )
        profit_factor = (
            total_wins / total_losses
            if total_losses > 0
            else float("inf") if total_wins > 0 else 0.0
        )

        return BacktestResult(
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            total_trades=total_trades,
            profitable_trades=profitable_trades,
            average_win=average_win,
            average_loss=average_loss,
            profit_factor=profit_factor,
            start_date=start_date,
            end_date=end_date,
        )


class QuantitativeAnalystAgent(BaseAgent):
    """量化分析师Agent"""

    def __init__(
        self,
        config: AgentConfig,
        message_queue: MessageQueue,
        system_config: SystemConfig = None,
    ):
        super().__init__(config, message_queue, system_config)

        # 初始化分析引擎
        self.analysis_engine = QuantitativeAnalysisEngine()
        self.backtest_engine = BacktestEngine()

        # 数据存储
        self.market_data_cache: Dict[str, pd.DataFrame] = {}
        self.analysis_results: Dict[str, Dict[str, Any]] = {}

        # 协议
        self.protocol = AgentProtocol(config.agent_id, message_queue)

    async def initialize(self) -> bool:
        """初始化Agent"""
        try:
            # 初始化协议
            await self.protocol.initialize()

            # 注册消息处理器
            self.protocol.register_handler(MessageType.DATA, self._handle_market_data)
            self.protocol.register_handler(
                MessageType.CONTROL, self._handle_analysis_request
            )

            self.logger.info(f"量化分析师Agent初始化成功: {self.config.agent_id}")
            return True

        except Exception as e:
            self.logger.error(f"量化分析师Agent初始化失败: {e}")
            return False

    async def process_message(self, message: Message) -> bool:
        """处理消息"""
        try:
            await self.protocol.handle_incoming_message(message)
            return True

        except Exception as e:
            self.logger.error(f"处理消息失败: {e}")
            return False

    async def cleanup(self):
        """清理资源"""
        self.logger.info("清理量化分析师Agent资源")
        # 可以在这里保存分析结果到数据库

    async def _handle_market_data(self, protocol_message):
        """处理市场数据"""
        try:
            data_type = protocol_message.payload.get("data_type")
            data = protocol_message.payload.get("data", {})

            if data_type == "market_data":
                symbol = data.get("symbol")
                market_data = data.get("market_data")

                if symbol and market_data:
                    await self._process_market_data(symbol, market_data)

        except Exception as e:
            self.logger.error(f"处理市场数据失败: {e}")

    async def _handle_analysis_request(self, protocol_message):
        """处理分析请求"""
        try:
            command = protocol_message.payload.get("command")
            parameters = protocol_message.payload.get("parameters", {})

            if command == "analyze_symbol":
                symbol = parameters.get("symbol")
                if symbol:
                    await self._analyze_symbol(symbol)

            elif command == "backtest_strategy":
                strategy_params = parameters.get("strategy_params", {})
                await self._run_backtest(strategy_params)

        except Exception as e:
            self.logger.error(f"处理分析请求失败: {e}")

    async def _process_market_data(self, symbol: str, market_data: Dict[str, Any]):
        """处理市场数据"""
        try:
            # 转换为DataFrame格式
            df_data = {
                "timestamp": [datetime.fromisoformat(market_data["timestamp"])],
                "open": [market_data["open_price"]],
                "high": [market_data["high_price"]],
                "low": [market_data["low_price"]],
                "close": [market_data["close_price"]],
                "volume": [market_data["volume"]],
            }

            new_row = pd.DataFrame(df_data)

            # 更新缓存数据
            if symbol in self.market_data_cache:
                self.market_data_cache[symbol] = pd.concat(
                    [self.market_data_cache[symbol], new_row], ignore_index=True
                )
            else:
                self.market_data_cache[symbol] = new_row

            # 保持最近1000个数据点
            if len(self.market_data_cache[symbol]) > 1000:
                self.market_data_cache[symbol] = self.market_data_cache[symbol].tail(
                    1000
                )

            # 如果有足够的数据，进行分析
            if len(self.market_data_cache[symbol]) >= 50:
                await self._analyze_symbol(symbol)

        except Exception as e:
            self.logger.error(f"处理市场数据失败: {e}")

    async def _analyze_symbol(self, symbol: str):
        """分析股票符号"""
        try:
            if (
                symbol not in self.market_data_cache
                or len(self.market_data_cache[symbol]) < 50
            ):
                self.logger.warning(f"数据不足，无法分析: {symbol}")
                return

            data = self.market_data_cache[symbol].copy()

            # 计算技术指标
            indicators = self.analysis_engine.calculate_technical_indicators(data)

            # 分析趋势
            trend_analysis = self.analysis_engine.analyze_market_trend(indicators)

            # 生成交易信号
            signals = self.analysis_engine.generate_trading_signals(
                indicators, trend_analysis
            )

            # 预测波动率
            volatility_prediction = self.analysis_engine.predict_volatility(data)

            # 保存分析结果
            analysis_result = {
                "symbol": symbol,
                "timestamp": datetime.now(),
                "indicators": indicators.__dict__,
                "trend_analysis": trend_analysis,
                "signals": signals,
                "volatility_prediction": volatility_prediction,
            }

            self.analysis_results[symbol] = analysis_result

            # 如果有交易信号，发送给交易员
            for signal in signals:
                await self.protocol.send_signal(
                    signal_type=signal["signal_type"],
                    symbol=symbol,
                    confidence=signal["confidence"],
                    reasoning=signal["reasoning"],
                )

            # 广播分析结果
            await self.protocol.broadcast_message(
                message_type=MessageType.DATA,
                payload={"analysis_result": analysis_result},
                priority=MessagePriority.NORMAL,
            )

            self.logger.info(f"完成股票分析: {symbol}")

        except Exception as e:
            self.logger.error(f"分析股票失败: {symbol}, 错误: {e}")

    async def _run_backtest(self, strategy_params: Dict[str, Any]):
        """运行回测"""
        try:
            symbol = strategy_params.get("symbol")
            initial_capital = strategy_params.get("initial_capital", 100000.0)
            commission = strategy_params.get("commission", 0.001)

            if symbol not in self.market_data_cache:
                self.logger.warning(f"没有数据可用于回测: {symbol}")
                return

            data = self.market_data_cache[symbol].copy()

            # 生成历史信号
            all_signals = []
            for i in range(50, len(data)):
                window_data = data.iloc[: i + 1]
                indicators = self.analysis_engine.calculate_technical_indicators(
                    window_data
                )
                trend_analysis = self.analysis_engine.analyze_market_trend(indicators)
                signals = self.analysis_engine.generate_trading_signals(
                    indicators, trend_analysis
                )

                for signal in signals:
                    signal["timestamp"] = data.iloc[i]["timestamp"]
                    all_signals.append(signal)

            # 运行回测
            backtest_result = self.backtest_engine.run_backtest(
                data, all_signals, initial_capital, commission
            )

            # 发送回测结果
            await self.protocol.broadcast_message(
                message_type=MessageType.DATA,
                payload={
                    "backtest_result": backtest_result.__dict__,
                    "strategy_params": strategy_params,
                },
                priority=MessagePriority.NORMAL,
            )

            self.logger.info(f"回测完成: {symbol}")

        except Exception as e:
            self.logger.error(f"回测失败: {e}")

    def get_analysis_summary(self) -> Dict[str, Any]:
        """获取分析摘要"""
        return {
            "agent_id": self.config.agent_id,
            "cached_symbols": list(self.market_data_cache.keys()),
            "analysis_results": len(self.analysis_results),
            "protocol_stats": self.protocol.get_protocol_stats(),
        }


# 导出主要组件
__all__ = [
    "QuantitativeAnalysisEngine",
    "BacktestEngine",
    "QuantitativeAnalystAgent",
    "TechnicalIndicators",
    "BacktestResult",
]

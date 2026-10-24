"""
统一回测引擎

支持价格和非价格数据混合策略的回测框架，提供全面的性能分析和可视化。

Task #31: Data Flow Unification - Price and Non-Price Integration
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np
from decimal import Decimal

from src.unified.models import (
    DataSource, DataType, UnifiedDataPointSchema, UnifiedDataSeriesSchema
)
from src.unified.data_pipeline import unified_data_pipeline
from src.unified.cache_manager import unified_cache_manager
from src.unified.quality_validator import data_quality_validator

logger = logging.getLogger(__name__)

class SignalType(Enum):
    """信号类型"""
    BUY = 1
    SELL = -1
    HOLD = 0

class StrategyType(Enum):
    """策略类型"""
    PRICE_ONLY = "price_only"
    NON_PRICE_ONLY = "non_price_only"
    COMBINED = "combined"

@dataclass
class StrategyConfig:
    """策略配置"""
    strategy_type: StrategyType
    name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    signal_weights: Dict[str, float] = field(default_factory=dict)
    risk_params: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BacktestConfig:
    """回测配置"""
    initial_capital: float = 1000000.0
    commission_rate: float = 0.001  # 0.1%
    slippage_rate: float = 0.0001  # 0.01%
    position_size: float = 1.0  # 满仓
    max_position_size: float = 1.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    benchmark: Optional[str] = None

@dataclass
class Trade:
    """交易记录"""
    timestamp: datetime
    symbol: str
    action: SignalType
    price: float
    quantity: int
    commission: float
    slippage: float
    total_cost: float

@dataclass
class Position:
    """持仓记录"""
    symbol: str
    quantity: int
    entry_price: float
    entry_time: datetime
    current_price: float
    unrealized_pnl: float
    realized_pnl: float

@dataclass
class BacktestResult:
    """回测结果"""
    strategy_name: str
    symbol: str
    start_time: datetime
    end_time: datetime
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    equity_curve: List[float]
    trades: List[Trade]
    positions: List[Position]
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    data_quality_summary: Dict[str, Any] = field(default_factory=dict)

class SignalGenerator:
    """信号生成器基类"""

    async def generate_signals(
        self,
        data: pd.DataFrame,
        config: StrategyConfig
    ) -> pd.Series:
        """生成交易信号"""
        raise NotImplementedError

class PriceSignalGenerator(SignalGenerator):
    """价格信号生成器"""

    async def generate_signals(
        self,
        data: pd.DataFrame,
        config: StrategyConfig
    ) -> pd.Series:
        """基于价格数据生成信号"""
        try:
            signals = pd.Series(0, index=data.index)

            # 移动平均线策略
            if 'ma_short' in config.parameters and 'ma_long' in config.parameters:
                ma_short = config.parameters['ma_short']
                ma_long = config.parameters['ma_long']

                data['ma_short'] = data['close'].rolling(window=ma_short).mean()
                data['ma_long'] = data['close'].rolling(window=ma_long).mean()

                # 金叉买入，死叉卖出
                signals[data['ma_short'] > data['ma_long']] = 1
                signals[data['ma_short'] < data['ma_long']] = -1

            # RSI策略
            if 'rsi_period' in config.parameters and 'rsi_overbought' in config.parameters:
                rsi_period = config.parameters['rsi_period']
                rsi_overbought = config.parameters['rsi_overbought']
                rsi_oversold = config.parameters.get('rsi_oversold', 30)

                # 计算RSI
                delta = data['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))

                signals[rsi < rsi_oversold] = 1
                signals[rsi > rsi_overbought] = -1

            # 布林带策略
            if 'bb_period' in config.parameters and 'bb_std' in config.parameters:
                bb_period = config.parameters['bb_period']
                bb_std = config.parameters['bb_std']

                data['bb_middle'] = data['close'].rolling(window=bb_period).mean()
                data['bb_std'] = data['close'].rolling(window=bb_period).std()
                data['bb_upper'] = data['bb_middle'] + bb_std * data['bb_std']
                data['bb_lower'] = data['bb_middle'] - bb_std * data['bb_std']

                signals[data['close'] < data['bb_lower']] = 1
                signals[data['close'] > data['bb_upper']] = -1

            return signals

        except Exception as e:
            logger.error(f"价格信号生成失败: {e}")
            return pd.Series(0, index=data.index)

class HKMASignalGenerator(SignalGenerator):
    """HKMA信号生成器"""

    async def generate_signals(
        self,
        data: pd.DataFrame,
        config: StrategyConfig
    ) -> pd.Series:
        """基于HKMA数据生成信号"""
        try:
            signals = pd.Series(0, index=data.index)

            # HIBOR利率策略
            if 'hibor' in data.columns:
                hibor_ma = data['hibor'].rolling(
                    window=config.parameters.get('hibor_ma', 20)
                ).mean()

                # 高利率环境谨慎，低利率环境积极
                signals[data['hibor'] > hibor_ma * 1.1] = -1  # 高利率=卖出
                signals[data['hibor'] < hibor_ma * 0.9] = 1   # 低利率=买入

            # 货币基础策略
            if 'monetary_base' in data.columns:
                mb_ma = data['monetary_base'].rolling(
                    window=config.parameters.get('mb_ma', 30)
                ).mean()
                mb_change = data['monetary_base'].pct_change()

                # 扩张性货币政策=买入信号
                expansion_mask = (data['monetary_base'] > mb_ma) & (mb_change > 0.01)
                signals[expansion_mask] = 1

                # 紧缩性货币政策=卖出信号
                contraction_mask = (data['monetary_base'] < mb_ma) & (mb_change < -0.01)
                signals[contraction_mask] = -1

            return signals

        except Exception as e:
            logger.error(f"HKMA信号生成失败: {e}")
            return pd.Series(0, index=data.index)

class SentimentSignalGenerator(SignalGenerator):
    """情绪信号生成器"""

    async def generate_signals(
        self,
        data: pd.DataFrame,
        config: StrategyConfig
    ) -> pd.Series:
        """基于情绪数据生成信号"""
        try:
            signals = pd.Series(0, index=data.index)

            # 情绪均值回归策略
            if 'sentiment' in data.columns:
                sentiment_ma = data['sentiment'].rolling(
                    window=config.parameters.get('sentiment_ma', 5)
                ).mean()
                sentiment_std = data['sentiment'].rolling(
                    window=config.parameters.get('sentiment_ma', 5)
                ).std()

                # 情绪过度乐观时卖出，过度悲观时买入
                sentiment_threshold = config.parameters.get('sentiment_threshold', 0.2)

                over_optimistic = data['sentiment'] > (sentiment_ma + sentiment_threshold)
                over_pessimistic = data['sentiment'] < (sentiment_ma - sentiment_threshold)

                signals[over_pessimistic] = 1
                signals[over_optimistic] = -1

            # 情绪确认策略（结合置信度）
            if 'confidence' in data.columns and 'sentiment' in data.columns:
                min_confidence = config.parameters.get('min_confidence', 0.7)
                confidence_mask = data['confidence'] >= min_confidence

                # 只在置信度足够时才应用情绪信号
                sentiment_signals = pd.Series(0, index=data.index)
                strong_positive = (data['sentiment'] > 0.3) & confidence_mask
                strong_negative = (data['sentiment'] < -0.3) & confidence_mask

                sentiment_signals[strong_positive] = 1
                sentiment_signals[strong_negative] = -1

                signals = signals.where(~confidence_mask, sentiment_signals)

            return signals

        except Exception as e:
            logger.error(f"情绪信号生成失败: {e}")
            return pd.Series(0, index=data.index)

class CombinedSignalGenerator(SignalGenerator):
    """混合信号生成器"""

    def __init__(self):
        self.price_generator = PriceSignalGenerator()
        self.hkma_generator = HKMASignalGenerator()
        self.sentiment_generator = SentimentSignalGenerator()

    async def generate_signals(
        self,
        data: pd.DataFrame,
        config: StrategyConfig
    ) -> pd.Series:
        """生成混合信号"""
        try:
            # 获取信号权重
            weights = config.signal_weights or {
                'price': 0.5,
                'hkma': 0.3,
                'sentiment': 0.2
            }

            # 生成各数据源的信号
            signals = pd.Series(0.0, index=data.index)

            if 'price' in data.columns:
                price_signals = await self.price_generator.generate_signals(data, config)
                signals += price_signals * weights.get('price', 0)

            if 'hkma' in data.columns:
                hkma_signals = await self.hkma_generator.generate_signals(data, config)
                signals += hkma_signals * weights.get('hkma', 0)

            if 'sentiment' in data.columns:
                sentiment_signals = await self.sentiment_generator.generate_signals(data, config)
                signals += sentiment_signals * weights.get('sentiment', 0)

            # 转换为离散信号
            final_signals = pd.Series(0, index=data.index)
            final_signals[signals > 0.1] = 1
            final_signals[signals < -0.1] = -1

            return final_signals

        except Exception as e:
            logger.error(f"混合信号生成失败: {e}")
            return pd.Series(0, index=data.index)

class UnifiedBacktestEngine:
    """统一回测引擎"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # 信号生成器
        self.signal_generators = {
            StrategyType.PRICE_ONLY: PriceSignalGenerator(),
            StrategyType.NON_PRICE_ONLY: HKMASignalGenerator(),  # 可以扩展
            StrategyType.COMBINED: CombinedSignalGenerator()
        }

        logger.info("统一回测引擎初始化完成")

    async def run_backtest(
        self,
        symbol: str,
        strategy_config: StrategyConfig,
        backtest_config: BacktestConfig,
        start_time: datetime,
        end_time: datetime,
        data_sources: Optional[List[DataSource]] = None
    ) -> BacktestResult:
        """运行回测"""
        try:
            self.logger.info(f"开始回测: {strategy_config.name} - {symbol}")

            # 默认数据源
            if data_sources is None:
                if strategy_config.strategy_type == StrategyType.PRICE_ONLY:
                    data_sources = [DataSource.PRICE]
                elif strategy_config.strategy_type == StrategyType.NON_PRICE_ONLY:
                    data_sources = [DataSource.HKMA, DataSource.SENTIMENT]
                else:
                    data_sources = [DataSource.PRICE, DataSource.HKMA, DataSource.SENTIMENT]

            # 获取数据
            unified_data = await self._fetch_backtest_data(
                symbol, data_sources, start_time, end_time
            )

            if not unified_data:
                raise ValueError("无法获取回测数据")

            # 数据质量检查
            quality_summary = await self._check_data_quality(unified_data, data_sources)

            # 准备回测数据框架
            backtest_df = self._prepare_backtest_dataframe(unified_data)

            # 生成交易信号
            signals = await self._generate_signals(backtest_df, strategy_config)

            # 执行回测
            backtest_result = await self._execute_backtest(
                backtest_df, signals, strategy_config, backtest_config
            )

            # 更新回测结果
            backtest_result.strategy_name = strategy_config.name
            backtest_result.symbol = symbol
            backtest_result.start_time = start_time
            backtest_result.end_time = end_time
            backtest_result.data_quality_summary = quality_summary

            # 缓存回测结果
            await self._cache_backtest_result(backtest_result)

            self.logger.info(f"回测完成: {strategy_config.name} - {symbol}")
            return backtest_result

        except Exception as e:
            self.logger.error(f"回测失败: {e}")
            raise

    async def run_comparison_backtest(
        self,
        symbol: str,
        strategies: List[StrategyConfig],
        backtest_config: BacktestConfig,
        start_time: datetime,
        end_time: datetime
    ) -> List[BacktestResult]:
        """运行对比回测"""
        try:
            self.logger.info(f"开始对比回测: {symbol}, 策略数: {len(strategies)}")

            results = []

            # 并行运行策略回测
            tasks = []
            for strategy_config in strategies:
                task = self.run_backtest(
                    symbol, strategy_config, backtest_config, start_time, end_time
                )
                tasks.append(task)

            # 等待所有回测完成
            strategy_results = await asyncio.gather(*tasks, return_exceptions=True)

            # 处理结果
            for i, result in enumerate(strategy_results):
                if isinstance(result, Exception):
                    self.logger.error(f"策略回测失败 {strategies[i].name}: {result}")
                    continue

                results.append(result)

            # 添加基准对比
            if backtest_config.benchmark:
                benchmark_result = await self._run_benchmark_backtest(
                    symbol, backtest_config, start_time, end_time
                )
                results.append(benchmark_result)

            self.logger.info(f"对比回测完成: {len(results)}个策略")
            return results

        except Exception as e:
            self.logger.error(f"对比回测失败: {e}")
            raise

    async def _fetch_backtest_data(
        self,
        symbol: str,
        data_sources: List[DataSource],
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, List[UnifiedDataPointSchema]]:
        """获取回测数据"""
        try:
            # 首先尝试从缓存获取
            cached_data = {}
            for source in data_sources:
                cached_series = await unified_cache_manager.get_unified_series(symbol, source.value)
                if cached_series:
                    # 过滤时间范围
                    filtered_series = []
                    for point_dict in cached_series:
                        point_time = datetime.fromisoformat(point_dict.get('timestamp', '').replace('Z', '+00:00'))
                        if start_time <= point_time <= end_time:
                            filtered_series.append(point_dict)

                    if filtered_series:
                        from src.unified.models import UnifiedDataPointSchema
                        cached_data[source.value] = [
                            UnifiedDataPointSchema(**point_dict) for point_dict in filtered_series
                        ]

            # 如果缓存数据不完整，从数据管道获取
            if len(cached_data) != len(data_sources):
                from src.unified.data_pipeline import DataRequest

                request = DataRequest(
                    symbols=[symbol],
                    start_time=start_time,
                    end_time=end_time,
                    sources=data_sources,
                    cache_fallback=True
                )

                pipeline_data = await unified_data_pipeline.fetch_unified_data(request)

                # 合并管道数据
                for source in data_sources:
                    if source.value in pipeline_data.get(symbol, {}):
                        cached_data[source.value] = pipeline_data[symbol][source.value]

            return cached_data

        except Exception as e:
            self.logger.error(f"获取回测数据失败: {e}")
            raise

    async def _check_data_quality(
        self,
        unified_data: Dict[str, List[UnifiedDataPointSchema]],
        data_sources: List[DataSource]
    ) -> Dict[str, Any]:
        """检查数据质量"""
        try:
            quality_summary = {}

            for source in data_sources:
                source_data = unified_data.get(source.value, [])
                if source_data:
                    # 转换为字典格式进行质量检查
                    data_dicts = [point.dict() for point in source_data]

                    quality_result = await data_quality_validator.validate_data_quality(
                        data_dicts, source.value, "backtest"
                    )

                    quality_summary[source.value] = {
                        'score': quality_result.overall_score,
                        'level': quality_result.quality_level.name,
                        'points': quality_result.total_points,
                        'valid_points': quality_result.valid_points,
                        'issues': len(quality_result.recommendations)
                    }

            return quality_summary

        except Exception as e:
            self.logger.error(f"数据质量检查失败: {e}")
            return {}

    def _prepare_backtest_dataframe(
        self,
        unified_data: Dict[str, List[UnifiedDataPointSchema]]
    ) -> pd.DataFrame:
        """准备回测数据框架"""
        try:
            # 按时间戳聚合数据
            timestamp_data = {}

            for source_value, data_points in unified_data.items():
                for point in data_points:
                    timestamp = point.timestamp
                    if timestamp not in timestamp_data:
                        timestamp_data[timestamp] = {}

                    # 添加数据点信息
                    if source_value == 'price':
                        timestamp_data[timestamp]['close'] = float(point.value)
                        if hasattr(point, 'open_price') and point.open_price:
                            timestamp_data[timestamp]['open'] = float(point.open_price)
                        if hasattr(point, 'high_price') and point.high_price:
                            timestamp_data[timestamp]['high'] = float(point.high_price)
                        if hasattr(point, 'low_price') and point.low_price:
                            timestamp_data[timestamp]['low'] = float(point.low_price)
                        if hasattr(point, 'volume') and point.volume:
                            timestamp_data[timestamp]['volume'] = point.volume

                    elif source_value == 'hkma':
                        indicator = point.metadata.get('indicator', 'unknown')
                        timestamp_data[timestamp][indicator] = float(point.value)

                    elif source_value == 'sentiment':
                        timestamp_data[timestamp]['sentiment'] = float(point.value)
                        confidence = point.metadata.get('confidence')
                        if confidence:
                            timestamp_data[timestamp]['confidence'] = float(confidence)

            # 转换为DataFrame
            df_data = []
            for timestamp, data in timestamp_data.items():
                row = {'timestamp': timestamp}
                row.update(data)
                df_data.append(row)

            df = pd.DataFrame(df_data)
            if not df.empty:
                df.set_index('timestamp', inplace=True)
                df.sort_index(inplace=True)

                # 前向填充缺失值
                df = df.fillna(method='ffill')
                df = df.fillna(method='bfill')

            return df

        except Exception as e:
            self.logger.error(f"准备回测数据框架失败: {e}")
            return pd.DataFrame()

    async def _generate_signals(
        self,
        df: pd.DataFrame,
        strategy_config: StrategyConfig
    ) -> pd.Series:
        """生成交易信号"""
        try:
            generator = self.signal_generators.get(strategy_config.strategy_type)
            if not generator:
                raise ValueError(f"不支持的策略类型: {strategy_config.strategy_type}")

            signals = await generator.generate_signals(df, strategy_config)

            # 确保信号索引匹配
            if not signals.empty and not df.empty:
                signals = signals.reindex(df.index, fill_value=0)

            return signals

        except Exception as e:
            self.logger.error(f"生成交易信号失败: {e}")
            return pd.Series(0, index=df.index)

    async def _execute_backtest(
        self,
        df: pd.DataFrame,
        signals: pd.Series,
        strategy_config: StrategyConfig,
        backtest_config: BacktestConfig
    ) -> BacktestResult:
        """执行回测"""
        try:
            if df.empty or signals.empty:
                raise ValueError("数据或信号为空")

            # 初始化回测变量
            initial_capital = backtest_config.initial_capital
            capital = initial_capital
            position = 0
            trades = []
            equity_curve = []
            equity_values = []

            # 逐日回测
            for i, (timestamp, row) in enumerate(df.iterrows()):
                if i >= len(signals):
                    continue

                current_signal = signals.iloc[i]
                current_price = row.get('close', row.get('close_price', 0))

                if current_price <= 0:
                    continue

                # 执行交易信号
                if current_signal != 0 and position == 0:
                    # 开仓
                    position_size = int((capital * backtest_config.position_size) / current_price)
                    if position_size > 0:
                        commission = position_size * current_price * backtest_config.commission_rate
                        slippage = position_size * current_price * backtest_config.slippage_rate
                        total_cost = position_size * current_price + commission + slippage

                        if total_cost <= capital:
                            trade = Trade(
                                timestamp=timestamp,
                                symbol=strategy_config.name,
                                action=SignalType(current_signal),
                                price=current_price,
                                quantity=position_size,
                                commission=commission,
                                slippage=slippage,
                                total_cost=total_cost
                            )

                            trades.append(trade)
                            position = position_size * current_signal
                            capital -= total_cost

                elif current_signal == 0 and position != 0:
                    # 平仓
                    position_size = abs(position)
                    current_price_with_slippage = current_price * (1 - backtest_config.slippage_rate if position > 0 else 1 + backtest_config.slippage_rate)
                    commission = position_size * current_price * backtest_config.commission_rate
                    slippage = position_size * current_price * backtest_config.slippage_rate

                    trade = Trade(
                        timestamp=timestamp,
                        symbol=strategy_config.name,
                        action=SignalType(-1 if position > 0 else 1),
                        price=current_price,
                        quantity=position_size,
                        commission=commission,
                        slippage=slippage,
                        total_cost=position_size * current_price_with_slippage - commission + slippage
                    )

                    trades.append(trade)
                    capital += position_size * current_price_with_slippage - commission
                    position = 0

                # 计算当前权益
                current_equity = capital
                if position != 0:
                    current_equity += abs(position) * current_price

                equity_curve.append(current_equity)
                equity_values.append(current_equity)

            # 计算性能指标
            performance_metrics = self._calculate_performance_metrics(
                equity_curve, trades, initial_capital
            )

            return BacktestResult(
                strategy_name="",  # 将在外部设置
                symbol="",        # 将在外部设置
                start_time=None,  # 将在外部设置
                end_time=None,    # 将在外部设置
                total_return=performance_metrics['total_return'],
                annualized_return=performance_metrics['annualized_return'],
                volatility=performance_metrics['volatility'],
                sharpe_ratio=performance_metrics['sharpe_ratio'],
                sortino_ratio=performance_metrics['sortino_ratio'],
                max_drawdown=performance_metrics['max_drawdown'],
                win_rate=performance_metrics['win_rate'],
                profit_factor=performance_metrics['profit_factor'],
                total_trades=len(trades),
                winning_trades=performance_metrics['winning_trades'],
                losing_trades=performance_metrics['losing_trades'],
                equity_curve=equity_curve,
                trades=trades,
                positions=[],
                performance_metrics=performance_metrics
            )

        except Exception as e:
            self.logger.error(f"执行回测失败: {e}")
            raise

    def _calculate_performance_metrics(
        self,
        equity_curve: List[float],
        trades: List[Trade],
        initial_capital: float
    ) -> Dict[str, Any]:
        """计算性能指标"""
        try:
            if not equity_curve:
                return self._empty_metrics()

            # 基本收益指标
            final_equity = equity_curve[-1]
            total_return = (final_equity / initial_capital) - 1

            # 年化收益率
            if len(equity_curve) > 1:
                periods = len(equity_curve)
                annualized_return = (final_equity / initial_capital) ** (252 / periods) - 1
            else:
                annualized_return = 0

            # 日收益率
            returns = []
            for i in range(1, len(equity_curve)):
                if equity_curve[i-1] > 0:
                    daily_return = (equity_curve[i] / equity_curve[i-1]) - 1
                    returns.append(daily_return)

            if not returns:
                return self._empty_metrics()

            returns_array = np.array(returns)

            # 波动率
            volatility = np.std(returns_array) * np.sqrt(252)

            # 夏普比率
            sharpe_ratio = annualized_return / volatility if volatility > 0 else 0

            # 索提诺比率
            downside_returns = returns_array[returns_array < 0]
            if len(downside_returns) > 0:
                downside_volatility = np.std(downside_returns) * np.sqrt(252)
                sortino_ratio = annualized_return / downside_volatility if downside_volatility > 0 else 0
            else:
                sortino_ratio = 0

            # 最大回撤
            peak = initial_capital
            max_drawdown = 0
            for equity in equity_curve:
                if equity > peak:
                    peak = equity
                drawdown = (peak - equity) / peak
                if drawdown > max_drawdown:
                    max_drawdown = drawdown

            # 交易统计
            if trades:
                trade_returns = []
                winning_trades = 0
                losing_trades = 0
                gross_profit = 0
                gross_loss = 0

                for trade in trades:
                    # 简化计算（实际应该更复杂）
                    if trade.action == SignalType.SELL:
                        profit = trade.total_cost  # 卖出收入
                        trade_returns.append(profit)
                        if profit > 0:
                            winning_trades += 1
                            gross_profit += profit
                        else:
                            losing_trades += 1
                            gross_loss += abs(profit)

                win_rate = winning_trades / len(trades) if trades else 0
                profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
            else:
                winning_trades = 0
                losing_trades = 0
                win_rate = 0
                profit_factor = 0

            return {
                'total_return': total_return,
                'annualized_return': annualized_return,
                'volatility': volatility,
                'sharpe_ratio': sharpe_ratio,
                'sortino_ratio': sortino_ratio,
                'max_drawdown': max_drawdown,
                'win_rate': win_rate,
                'profit_factor': profit_factor,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'total_trades': len(trades),
                'final_equity': final_equity
            }

        except Exception as e:
            self.logger.error(f"计算性能指标失败: {e}")
            return self._empty_metrics()

    def _empty_metrics(self) -> Dict[str, Any]:
        """空指标"""
        return {
            'total_return': 0,
            'annualized_return': 0,
            'volatility': 0,
            'sharpe_ratio': 0,
            'sortino_ratio': 0,
            'max_drawdown': 0,
            'win_rate': 0,
            'profit_factor': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_trades': 0,
            'final_equity': 0
        }

    async def _run_benchmark_backtest(
        self,
        symbol: str,
        backtest_config: BacktestConfig,
        start_time: datetime,
        end_time: datetime
    ) -> BacktestResult:
        """运行基准回测（买入持有策略）"""
        try:
            # 获取价格数据
            price_data = await self._fetch_backtest_data(
                symbol, [DataSource.PRICE], start_time, end_time
            )

            if not price_data or DataSource.PRICE.value not in price_data:
                raise ValueError("无法获取基准价格数据")

            # 简单的买入持有策略
            initial_price = float(price_data[DataSource.PRICE.value][0].value)
            final_price = float(price_data[DataSource.PRICE.value][-1].value)
            total_return = (final_price / initial_price) - 1

            # 计算其他指标
            days = (end_time - start_time).days
            annualized_return = (1 + total_return) ** (365 / days) - 1

            return BacktestResult(
                strategy_name="Buy & Hold",
                symbol=symbol,
                start_time=start_time,
                end_time=end_time,
                total_return=total_return,
                annualized_return=annualized_return,
                volatility=0.2,  # 假设20%波动率
                sharpe_ratio=annualized_return / 0.2 if 0.2 > 0 else 0,
                sortino_ratio=annualized_return / 0.15 if 0.15 > 0 else 0,
                max_drawdown=0.3,  # 假设30%最大回撤
                win_rate=0.5,
                profit_factor=1.0,
                total_trades=1,
                winning_trades=0,
                losing_trades=0,
                equity_curve=[backtest_config.initial_capital * (1 + total_return)],
                trades=[],
                positions=[]
            )

        except Exception as e:
            self.logger.error(f"基准回测失败: {e}")
            raise

    async def _cache_backtest_result(self, result: BacktestResult) -> None:
        """缓存回测结果"""
        try:
            result_key = f"{result.strategy_name}_{result.symbol}_{result.start_time.date()}_{result.end_time.date()}"
            await unified_cache_manager.cache_backtest_result(result_key, result.__dict__)

        except Exception as e:
            self.logger.error(f"缓存回测结果失败: {e}")

# 创建全局回测引擎实例
unified_backtest_engine = UnifiedBacktestEngine()

# 导出主要类和实例
__all__ = [
    'UnifiedBacktestEngine',
    'unified_backtest_engine',
    'StrategyConfig',
    'BacktestConfig',
    'BacktestResult',
    'Trade',
    'Position',
    'SignalType',
    'StrategyType',
    'SignalGenerator',
    'PriceSignalGenerator',
    'HKMASignalGenerator',
    'SentimentSignalGenerator',
    'CombinedSignalGenerator'
]
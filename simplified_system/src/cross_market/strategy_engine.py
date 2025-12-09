#!/usr/bin/env python3
"""
跨市场策略引擎 - Cross-Market Strategy Engine
实现套利、相关性、动量等跨市场交易策略
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import json
from abc import ABC, abstractmethod

from ..multi_asset.asset_models import AssetClass, MarketData, MultiAssetPortfolio
from ..multi_asset.multi_asset_adapter import MultiAssetDataAdapter

# Setup logging
logger = logging.getLogger(__name__)

class CrossMarketStrategyType(Enum):
    """跨市场策略类型枚举"""
    ARBITRAGE = "arbitrage"
    CORRELATION = "correlation"
    MOMENTUM = "momentum"
    RISK_PARITY = "risk_parity"
    RELATIVE_VALUE = "relative_value"
    MACRO_THEME = "macro_theme"

class TradingAction(Enum):
    """交易动作"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

@dataclass
class TradingSignal:
    """交易信号"""
    strategy_name: str
    asset: str
    action: TradingAction
    quantity: float
    price: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    confidence: float = 1.0
    reason: str = ""
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    time_in_force: str = "GTC"
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Trade:
    """交易记录"""
    signal: TradingSignal
    executed_price: float
    executed_quantity: float
    execution_time: datetime
    commission: float = 0.0
    status: str = "filled"
    trade_id: str = field(default_factory=lambda: f"trade_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}")

@dataclass
class ArbitrageOpportunity:
    """套利机会"""
    type: str
    pairs: List[str]
    theoretical_price: float
    actual_price: float
    spread: float
    percentage: float
    execution_plan: List[Tuple[str, str, float]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)

class BaseCrossMarketStrategy(ABC):
    """跨市场策略基类"""

    def __init__(self, name: str, strategy_type: CrossMarketStrategyType):
        self.name = name
        self.strategy_type = strategy_type
        self.parameters = {}
        self.performance_metrics = {}
        self.is_initialized = False
        self.last_update_time = None

    @abstractmethod
    async def initialize(self, market_data: Dict[str, pd.DataFrame]):
        """策略初始化"""
        pass

    @abstractmethod
    async def generate_signals(
        self,
        market_data: Dict[str, pd.DataFrame],
        current_time: datetime
    ) -> List[TradingSignal]:
        """生成交易信号"""
        pass

    def update_parameters(self, parameters: Dict[str, Any]):
        """更新策略参数"""
        self.parameters.update(parameters)
        logger.info(f"Updated parameters for strategy {self.name}: {parameters}")

    def calculate_performance(self, returns: pd.Series) -> Dict[str, float]:
        """计算策略绩效"""
        if len(returns) == 0:
            return {}

        total_return = (1 + returns).prod() - 1
        annualized_return = returns.mean() * 252
        volatility = returns.std() * np.sqrt(252)
        sharpe_ratio = annualized_return / volatility if volatility > 0 else 0

        # Calculate max drawdown
        cumulative_returns = returns.cumsum()
        running_max = cumulative_returns.expanding().max()
        max_drawdown = (cumulative_returns - running_max).min()

        return {
            "total_return": total_return,
            "annualized_return": annualized_return,
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "calmar_ratio": annualized_return / abs(max_drawdown) if max_drawdown != 0 else float('inf')
        }

class TriangularArbitrageStrategy(BaseCrossMarketStrategy):
    """三角套利策略"""

    def __init__(self, currency_pairs: List[str], min_spread_pct: float = 0.1):
        super().__init__("triangular_arbitrage", CrossMarketStrategyType.ARBITRAGE)
        self.currency_pairs = currency_pairs
        self.min_spread_pct = min_spread_pct
        self.parameters = {
            "min_spread_pct": min_spread_pct,
            "currency_pairs": currency_pairs
        }

    async def initialize(self, market_data: Dict[str, pd.DataFrame]):
        """初始化三角套利策略"""
        self.is_initialized = True
        self.last_update_time = datetime.utcnow()
        logger.info(f"Triangular arbitrage strategy initialized with pairs: {self.currency_pairs}")

    async def generate_signals(
        self,
        market_data: Dict[str, pd.DataFrame],
        current_time: datetime
    ) -> List[TradingSignal]:
        """生成三角套利信号"""
        signals = []

        # 获取最新bid/ask数据
        bid_ask_data = {}
        for pair in self.currency_pairs:
            if pair in market_data and len(market_data[pair]) > 0:
                latest = market_data[pair].iloc[-1]
                # 模拟bid/ask数据 (实际应从实时数据获取)
                bid_ask_data[pair] = (
                    latest.close * 0.999,  # bid
                    latest.close * 1.001   # ask
                )

        # 计算三角套利机会
        if "EURUSD" in bid_ask_data and "USDJPY" in bid_ask_data and "EURJPY" in bid_ask_data:
            opportunity = self._calculate_triangular_arbitrage(bid_ask_data, ["EURUSD", "USDJPY", "EURJPY"])

            if opportunity and opportunity.percentage > self.min_spread_pct:
                # 生成套利信号
                for action, pair, price in opportunity.execution_plan:
                    signal = TradingSignal(
                        strategy_name=self.name,
                        asset=pair,
                        action=TradingAction(action),
                        quantity=100000,  # 标准化交易量
                        price=price,
                        confidence=min(opportunity.percentage / 0.5, 1.0),  # 基于套利空间的信心度
                        reason=f"Triangular arbitrage opportunity: {opportunity.percentage:.3f}% spread",
                        metadata={
                            "arbitrage_type": "triangular",
                            "spread_percentage": opportunity.percentage,
                            "execution_plan": opportunity.execution_plan
                        }
                    )
                    signals.append(signal)

        return signals

    def _calculate_triangular_arbitrage(
        self,
        bid_ask_data: Dict[str, Tuple[float, float]],
        pairs: List[str]
    ) -> Optional[ArbitrageOpportunity]:
        """计算三角套利机会"""
        try:
            # 解析bid/ask数据
            if len(pairs) != 3:
                return None

            # 假设pairs顺序: [base_quote1, quote1_quote2, base_quote2]
            base_quote1_bid, base_quote1_ask = bid_ask_data.get(pairs[0], (0, 0))
            quote1_quote2_bid, quote1_quote2_ask = bid_ask_data.get(pairs[1], (0, 0))
            base_quote2_bid, base_quote2_ask = bid_ask_data.get(pairs[2], (0, 0))

            # 计算理论价格
            # 通过base_quote1 -> quote1_quote2得到base_quote2理论价格
            theoretical_price = base_quote1_bid * quote1_quote2_bid
            actual_price = base_quote2_ask

            # 套利空间
            spread = theoretical_price - actual_price
            arbitrage_percentage = (spread / actual_price) * 100

            if arbitrage_percentage > self.min_spread_pct:
                return ArbitrageOpportunity(
                    type="triangular",
                    pairs=pairs,
                    theoretical_price=theoretical_price,
                    actual_price=actual_price,
                    spread=spread,
                    percentage=arbitrage_percentage,
                    execution_plan=[
                        ("sell", pairs[2], actual_price),      #卖出实际较贵的货币对
                        ("buy", pairs[0], base_quote1_ask),    #买入较便宜的货币对1
                        ("buy", pairs[1], quote1_quote2_ask)   #买入较便宜的货币对2
                    ]
                )

            # 检查反向套利
            reverse_theoretical = base_quote2_bid / quote1_quote2_bid
            reverse_actual = base_quote1_ask
            reverse_spread = reverse_theoretical - reverse_actual
            reverse_percentage = (reverse_spread / reverse_actual) * 100

            if reverse_percentage > self.min_spread_pct:
                return ArbitrageOpportunity(
                    type="triangular_reverse",
                    pairs=pairs,
                    theoretical_price=reverse_theoretical,
                    actual_price=reverse_actual,
                    spread=reverse_spread,
                    percentage=reverse_percentage,
                    execution_plan=[
                        ("sell", pairs[0], reverse_actual),
                        ("sell", pairs[1], quote1_quote2_bid),
                        ("buy", pairs[2], base_quote2_bid)
                    ]
                )

        except Exception as e:
            logger.error(f"Error calculating triangular arbitrage: {e}")

        return None

class PairsTradingStrategy(BaseCrossMarketStrategy):
    """配对交易策略"""

    def __init__(
        self,
        asset1: str,
        asset2: str,
        lookback_period: int = 252,
        entry_threshold: float = 2.0,
        exit_threshold: float = 0.5,
        zscore_method: str = "ratio"
    ):
        super().__init__("pairs_trading", CrossMarketStrategyType.CORRELATION)
        self.asset1 = asset1
        self.asset2 = asset2
        self.lookback_period = lookback_period
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold
        self.zscore_method = zscore_method

        self.parameters = {
            "lookback_period": lookback_period,
            "entry_threshold": entry_threshold,
            "exit_threshold": exit_threshold,
            "zscore_method": zscore_method
        }

    async def initialize(self, market_data: Dict[str, pd.DataFrame]):
        """初始化配对交易策略"""
        # 验证必要数据存在
        if self.asset1 not in market_data or self.asset2 not in market_data:
            raise ValueError(f"Missing market data for {self.asset1} or {self.asset2}")

        self.is_initialized = True
        self.last_update_time = datetime.utcnow()
        logger.info(f"Pairs trading strategy initialized for {self.asset1}/{self.asset2}")

    async def generate_signals(
        self,
        market_data: Dict[str, pd.DataFrame],
        current_time: datetime
    ) -> List[TradingSignal]:
        """生成配对交易信号"""
        signals = []

        if not self.is_initialized:
            return signals

        try:
            # 提取价格数据
            df1 = market_data[self.asset1]
            df2 = market_data[self.asset2]

            # 计算价差Z-score
            zscore_series = self._calculate_spread_zscore(df1, df2)

            if len(zscore_series) == 0:
                return signals

            current_zscore = zscore_series.iloc[-1]

            # 生成交易信号
            if current_zscore > self.entry_threshold:
                # 做空价差 (卖出asset1，买入asset2)
                signals.append(TradingSignal(
                    strategy_name=self.name,
                    asset=self.asset1,
                    action=TradingAction.SELL,
                    quantity=1000,
                    price=df1['close'].iloc[-1],
                    confidence=min(abs(current_zscore) / 3.0, 1.0),
                    reason=f"Z-score {current_zscore:.2f} > entry threshold {self.entry_threshold}",
                    stop_loss=df1['close'].iloc[-1] * 1.02,  # 2%止损
                    take_profit=df1['close'].iloc[-1] * 0.98,  # 2%止盈
                    metadata={
                        "pair": f"{self.asset1}/{self.asset2}",
                        "zscore": current_zscore,
                        "spread_direction": "short"
                    }
                ))

            elif current_zscore < -self.entry_threshold:
                # 做多价差 (买入asset1，卖出asset2)
                signals.append(TradingSignal(
                    strategy_name=self.name,
                    asset=self.asset1,
                    action=TradingAction.BUY,
                    quantity=1000,
                    price=df1['close'].iloc[-1],
                    confidence=min(abs(current_zscore) / 3.0, 1.0),
                    reason=f"Z-score {current_zscore:.2f} < -entry threshold {self.entry_threshold}",
                    stop_loss=df1['close'].iloc[-1] * 0.98,
                    take_profit=df1['close'].iloc[-1] * 1.02,
                    metadata={
                        "pair": f"{self.asset1}/{self.asset2}",
                        "zscore": current_zscore,
                        "spread_direction": "long"
                    }
                ))

            # 平仓信号 (Z-score回到正常范围)
            elif abs(current_zscore) < self.exit_threshold:
                signals.append(TradingSignal(
                    strategy_name=self.name,
                    asset=self.asset1,
                    action=TradingAction.HOLD,
                    quantity=0,
                    reason=f"Z-score {current_zscore:.2f} within exit threshold {self.exit_threshold}",
                    metadata={
                        "pair": f"{self.asset1}/{self.asset2}",
                        "zscore": current_zscore,
                        "action": "close_position"
                    }
                ))

        except Exception as e:
            logger.error(f"Error generating pairs trading signals: {e}")

        return signals

    def _calculate_spread_zscore(self, df1: pd.DataFrame, df2: pd.DataFrame) -> pd.Series:
        """计算价差的Z-score"""
        try:
            prices1 = df1['close']
            prices2 = df2['close']

            # 确保数据长度一致
            min_length = min(len(prices1), len(prices2))
            if min_length < self.lookback_period:
                return pd.Series()

            prices1 = prices1.iloc[-min_length:]
            prices2 = prices2.iloc[-min_length:]

            if self.zscore_method == "ratio":
                spread = prices1 / prices2
            elif self.zscore_method == "difference":
                spread = prices1 - prices2
            elif self.zscore_method == "beta_neutral":
                # Beta中性价差
                beta = self._calculate_beta(prices1, prices2)
                spread = prices1 - beta * prices2
            else:
                spread = prices1 / prices2

            # 计算移动平均和标准差
            spread_mean = spread.rolling(window=self.lookback_period, min_periods=20).mean()
            spread_std = spread.rolling(window=self.lookback_period, min_periods=20).std()

            # Z-score计算
            zscore = (spread - spread_mean) / spread_std
            return zscore.dropna()

        except Exception as e:
            logger.error(f"Error calculating spread z-score: {e}")
            return pd.Series()

    def _calculate_beta(self, prices1: pd.Series, prices2: pd.Series) -> float:
        """计算Beta系数"""
        try:
            returns1 = prices1.pct_change().dropna()
            returns2 = prices2.pct_change().dropna()

            # 确保数据对齐
            common_index = returns1.index.intersection(returns2.index)
            returns1 = returns1.loc[common_index]
            returns2 = returns2.loc[common_index]

            if len(returns1) < 30:  # 至少30个数据点
                return 1.0

            # 简单线性回归计算Beta
            covariance = np.cov(returns1, returns2)[0, 1]
            variance = np.var(returns2)

            return covariance / variance if variance != 0 else 1.0

        except Exception as e:
            logger.error(f"Error calculating beta: {e}")
            return 1.0

class CrossAssetMomentumStrategy(BaseCrossMarketStrategy):
    """跨资产动量策略"""

    def __init__(
        self,
        assets: List[str],
        lookback_periods: List[int] = [21, 63, 126],
        rebalance_frequency: str = "M",
        strategy_type: str = "long_short"
    ):
        super().__init__("cross_asset_momentum", CrossMarketStrategyType.MOMENTUM)
        self.assets = assets
        self.lookback_periods = lookback_periods
        self.rebalance_frequency = rebalance_frequency
        self.strategy_type = strategy_type

        self.parameters = {
            "assets": assets,
            "lookback_periods": lookback_periods,
            "rebalance_frequency": rebalance_frequency,
            "strategy_type": strategy_type
        }

    async def initialize(self, market_data: Dict[str, pd.DataFrame]):
        """初始化跨资产动量策略"""
        # 验证所有资产数据存在
        missing_assets = [asset for asset in self.assets if asset not in market_data]
        if missing_assets:
            raise ValueError(f"Missing market data for assets: {missing_assets}")

        self.is_initialized = True
        self.last_update_time = datetime.utcnow()
        logger.info(f"Cross-asset momentum strategy initialized for {len(self.assets)} assets")

    async def generate_signals(
        self,
        market_data: Dict[str, pd.DataFrame],
        current_time: datetime
    ) -> List[TradingSignal]:
        """生成跨资产动量信号"""
        signals = []

        if not self.is_initialized:
            return signals

        try:
            # 计算动量评分
            momentum_scores = self._calculate_momentum_scores(market_data, current_time)

            if not momentum_scores:
                return signals

            # 生成组合权重
            portfolio_weights = self._generate_portfolio_weights(momentum_scores)

            # 生成交易信号
            for asset, target_weight in portfolio_weights.items():
                if abs(target_weight) > 0.01:  # 最小1%权重阈值
                    df = market_data[asset]
                    current_price = df['close'].iloc[-1]

                    signal = TradingSignal(
                        strategy_name=self.name,
                        asset=asset,
                        action=TradingAction.BUY if target_weight > 0 else TradingAction.SELL,
                        quantity=abs(target_weight) * 100000,  # 假设100万组合
                        price=current_price,
                        confidence=min(abs(target_weight) * 2, 1.0),
                        reason=f"Momentum score: {momentum_scores.get(asset, 0):.4f}, Target weight: {target_weight:.2%}",
                        metadata={
                            "momentum_score": momentum_scores.get(asset, 0),
                            "target_weight": target_weight,
                            "strategy_type": self.strategy_type
                        }
                    )
                    signals.append(signal)

        except Exception as e:
            logger.error(f"Error generating cross-asset momentum signals: {e}")

        return signals

    def _calculate_momentum_scores(
        self,
        market_data: Dict[str, pd.DataFrame],
        current_time: datetime
    ) -> Dict[str, float]:
        """计算动量评分"""
        try:
            scores = {}

            for asset in self.assets:
                if asset not in market_data:
                    continue

                df = market_data[asset]
                if len(df) < max(self.lookback_periods):
                    continue

                prices = df['close']

                # 多周期动量计算
                momentum_components = []
                valid_periods = []

                for period in self.lookback_periods:
                    if len(prices) > period:
                        past_price = prices.iloc[-period]
                        current_price = prices.iloc[-1]
                        momentum = (current_price - past_price) / past_price
                        momentum_components.append(momentum)
                        valid_periods.append(period)

                if momentum_components:
                    # 加权平均 (近期动量权重更高)
                    weights = [p / sum(valid_periods) for p in valid_periods]
                    weighted_momentum = sum(m * w for m, w in zip(momentum_components, weights))
                    scores[asset] = weighted_momentum

            return scores

        except Exception as e:
            logger.error(f"Error calculating momentum scores: {e}")
            return {}

    def _generate_portfolio_weights(self, momentum_scores: Dict[str, float]) -> Dict[str, float]:
        """生成组合权重"""
        try:
            if self.strategy_type == "long_short":
                # 多空策略：做多动量最高，做空动量最低
                sorted_assets = sorted(momentum_scores.items(), key=lambda x: x[1])
                n_assets = len(sorted_assets)

                if n_assets == 0:
                    return {}

                # 前三分之一做多，后三分之一做空
                long_threshold = int(n_assets / 3)
                short_threshold = 2 * int(n_assets / 3)

                weights = {}
                long_assets = sorted_assets[long_threshold:]
                short_assets = sorted_assets[:short_threshold]

                # 等权重分配
                long_weight = 1.0 / len(long_assets) if long_assets else 0
                short_weight = -1.0 / len(short_assets) if short_assets else 0

                for asset, score in long_assets:
                    weights[asset] = long_weight
                for asset, score in short_assets:
                    weights[asset] = short_weight

            elif self.strategy_type == "long_only":
                # 只做多策略：基于动量排名分配权重
                positive_scores = {asset: score for asset, score in momentum_scores.items() if score > 0}

                if not positive_scores:
                    return {}

                total_score = sum(abs(s) for s in positive_scores.values())
                if total_score > 0:
                    weights = {
                        asset: score / total_score
                        for asset, score in positive_scores.items()
                    }
                else:
                    weights = {}

            else:
                weights = {}

            return weights

        except Exception as e:
            logger.error(f"Error generating portfolio weights: {e}")
            return {}

class CrossMarketStrategyManager:
    """跨市场策略管理器"""

    def __init__(self):
        self.strategies: Dict[str, BaseCrossMarketStrategy] = {}
        self.active_signals: List[TradingSignal] = []
        self.trade_history: List[Trade] = []
        self.portfolio = MultiAssetPortfolio("cross_market_portfolio")
        self.performance_metrics: Dict[str, Dict] = {}

    def add_strategy(self, strategy: BaseCrossMarketStrategy):
        """添加策略"""
        self.strategies[strategy.name] = strategy
        logger.info(f"Added strategy: {strategy.name}")

    def remove_strategy(self, strategy_name: str):
        """移除策略"""
        if strategy_name in self.strategies:
            del self.strategies[strategy_name]
            logger.info(f"Removed strategy: {strategy_name}")

    async def initialize_strategies(self, market_data: Dict[str, pd.DataFrame]):
        """初始化所有策略"""
        for strategy in self.strategies.values():
            try:
                await strategy.initialize(market_data)
                logger.info(f"Initialized strategy: {strategy.name}")
            except Exception as e:
                logger.error(f"Failed to initialize strategy {strategy.name}: {e}")

    async def run_strategies(
        self,
        market_data: Dict[str, pd.DataFrame],
        current_time: Optional[datetime] = None
    ) -> List[TradingSignal]:
        """运行所有策略"""
        if current_time is None:
            current_time = datetime.utcnow()

        all_signals = []

        for strategy in self.strategies.values():
            try:
                if not strategy.is_initialized:
                    logger.warning(f"Strategy {strategy.name} not initialized, skipping")
                    continue

                signals = await strategy.generate_signals(market_data, current_time)
                all_signals.extend(signals)

                # 记录策略活动
                self.performance_metrics[strategy.name] = {
                    "last_run": current_time,
                    "signals_generated": len(signals),
                    "status": "active"
                }

            except Exception as e:
                logger.error(f"Strategy {strategy.name} failed: {e}")
                self.performance_metrics[strategy.name] = {
                    "last_run": current_time,
                    "error": str(e),
                    "status": "error"
                }

        self.active_signals.extend(all_signals)
        return all_signals

    def get_portfolio_exposure(self) -> Dict[str, float]:
        """获取组合敞口"""
        exposure = {}

        for signal in self.active_signals:
            if signal.action != TradingAction.HOLD:
                direction = 1 if signal.action == TradingAction.BUY else -1
                exposure[signal.asset] = exposure.get(signal.asset, 0) + direction * signal.quantity

        return exposure

    def get_risk_metrics(self) -> Dict[str, Any]:
        """获取风险指标"""
        exposure = self.get_portfolio_exposure()

        return {
            "gross_exposure": sum(abs(v) for v in exposure.values()),
            "net_exposure": sum(exposure.values()),
            "asset_count": len(exposure),
            "active_strategies": len([s for s in self.strategies.values() if s.is_initialized]),
            "active_signals": len(self.active_signals),
            "total_trades": len(self.trade_history),
            "strategies": list(self.strategies.keys())
        }

    def calculate_strategy_performance(self, strategy_name: str, returns: pd.Series) -> Dict[str, float]:
        """计算策略绩效"""
        if strategy_name in self.strategies:
            return self.strategies[strategy_name].calculate_performance(returns)
        return {}

    def get_active_signals_summary(self) -> List[Dict[str, Any]]:
        """获取活跃信号摘要"""
        return [
            {
                "strategy": signal.strategy_name,
                "asset": signal.asset,
                "action": signal.action.value,
                "quantity": signal.quantity,
                "price": signal.price,
                "confidence": signal.confidence,
                "reason": signal.reason,
                "timestamp": signal.timestamp.isoformat()
            }
            for signal in self.active_signals
            if signal.action != TradingAction.HOLD
        ]

# 使用示例
async def main():
    """测试跨市场策略引擎"""
    print("Cross-Market Strategy Engine Test")
    print("=" * 60)

    # 创建策略管理器
    strategy_manager = CrossMarketStrategyManager()

    # 添加策略
    triangular_arb = TriangularArbitrageStrategy(
        currency_pairs=["EURUSD", "USDJPY", "EURJPY"],
        min_spread_pct=0.1
    )
    strategy_manager.add_strategy(triangular_arb)

    pairs_trading = PairsTradingStrategy(
        asset1="EURUSD",
        asset2="GBPUSD",
        lookback_period=60,
        entry_threshold=1.5,
        exit_threshold=0.5
    )
    strategy_manager.add_strategy(pairs_trading)

    momentum_strategy = CrossAssetMomentumStrategy(
        assets=["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"],
        lookback_periods=[21, 63],
        strategy_type="long_short"
    )
    strategy_manager.add_strategy(momentum_strategy)

    print(f"[OK] Added {len(strategy_manager.strategies)} strategies")

    # 创建模拟市场数据
    market_data = create_sample_market_data()

    # 初始化策略
    await strategy_manager.initialize_strategies(market_data)
    print("[OK] Strategies initialized")

    # 运行策略
    signals = await strategy_manager.run_strategies(market_data)
    print(f"[OK] Generated {len(signals)} trading signals")

    # 显示信号摘要
    for signal in signals[:5]:  # 显示前5个信号
        print(f"[SIGNAL] {signal.strategy_name}: {signal.action.value} {signal.quantity} {signal.asset}")
        print(f"  Reason: {signal.reason}")
        print(f"  Confidence: {signal.confidence:.2f}")

    # 显示风险指标
    risk_metrics = strategy_manager.get_risk_metrics()
    print(f"\n[RISK METRICS]")
    for metric, value in risk_metrics.items():
        print(f"  {metric}: {value}")

    print("\n[SUCCESS] Cross-Market Strategy Engine Test Complete!")

def create_sample_market_data() -> Dict[str, pd.DataFrame]:
    """创建示例市场数据"""
    import numpy as np
    from datetime import datetime, timedelta

    # 生成时间序列
    dates = pd.date_range(start=datetime.utcnow() - timedelta(days=100),
                          end=datetime.utcnow(), freq='H')

    market_data = {}

    # 生成不同资产的价格数据
    assets = ["EURUSD", "GBPUSD", "USDJPY", "EURJPY", "XAUUSD"]
    base_prices = [1.08, 1.27, 150.0, 162.0, 2300.0]

    for i, asset in enumerate(assets):
        # 生成随机游走价格
        returns = np.random.normal(0, 0.001, len(dates))
        prices = [base_prices[i]]

        for ret in returns:
            prices.append(prices[-1] * (1 + ret))

        # 创建OHLCV数据
        df = pd.DataFrame({
            'open': prices[:-1],
            'high': [p * (1 + abs(np.random.normal(0, 0.002))) for p in prices[:-1]],
            'low': [p * (1 - abs(np.random.normal(0, 0.002))) for p in prices[:-1]],
            'close': prices[1:],
            'volume': np.random.randint(1000000, 5000000, len(dates)-1)
        }, index=dates[:-1])

        market_data[asset] = df

    return market_data

if __name__ == "__main__":
    asyncio.run(main())
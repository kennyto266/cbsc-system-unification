#!/usr / bin / env python3
"""
動態資產配置系統 - 核心配置引擎
Dynamic Asset Allocation System - Core Allocation Engine

基於市場制度的動態資產配置，包含交易成本分析和平滑過渡
"""

import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .market_regime import (
    MarketRegimeDetector,
    RegimeConfig,
    RegimePrediction,
    RegimeState,
)
from .vectorbt_engine import BacktestConfig, BacktestResult, VectorBTEngine

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from indicators.core_indicators import CoreIndicators

logger = logging.getLogger(__name__)


class AllocationStrategy(Enum):
    """配置策略枚舉"""

    CONSTANT_MIX = "constant_mix"
    VOLATILITY_TARGETING = "volatility_targeting"
    RISK_PARITY = "risk_parity"
    MOMENTUM_BIAS = "momentum_bias"
    MEAN_REVERSION = "mean_reversion"
    REGIME_SWITCHING = "regime_switching"


@dataclass
class AssetConfig:
    """資產配置"""

    symbol: str
    name: str
    asset_class: str  # 'equity', 'bond', 'commodity', 'currency', 'alternative'

    # 配置約束
    min_weight: float = 0.0
    max_weight: float = 1.0

    # 交易成本
    commission_rate: float = 0.001  # 0.1%
    bid_ask_spread: float = 0.0005  # 0.05%
    market_impact: float = 0.0001  # 0.01%

    # 風險參數
    expected_volatility: float = 0.15  # 15%年化波動率
    max_drawdown_limit: float = 0.20  # 20%最大回撤限制

    # 相關性
    correlation_matrix: Optional[np.ndarray] = None


@dataclass
class AllocationConfig:
    """配置策略配置"""

    # 基礎參數
    rebalance_frequency: str = "monthly"  # 'daily', 'weekly', 'monthly', 'quarterly'
    lookback_period: int = 252  # 回看期（天數）

    # 交易成本管理
    min_trade_size: float = 0.01  # 最小交易比例
    cost_threshold: float = 0.005  # 成本閾值
    slippage_model: str = "linear"  # 'linear', 'square_root', 'percentage'

    # 風險控制
    max_leverage: float = 1.0  # 最大槓桿
    volatility_target: float = 0.12  # 目標波動率
    max_position_change: float = 0.3  # 最大單次倉位變化

    # 制度切換參數
    regime_weight_factor: float = 0.7  # 制度權重因子
    transition_smoothing: int = 5  # 平滑過渡天數

    # 緊急機制
    emergency_rebalance_threshold: float = 0.1  # 緊急再平衡閾值
    max_drawdown_rebalance: float = 0.15  # 最大回撤再平衡


@dataclass
class AllocationResult:
    """配置結果"""

    timestamp: datetime
    target_weights: Dict[str, float]
    current_weights: Dict[str, float]
    trades: Dict[str, float]

    # 成本分析
    expected_transaction_costs: Dict[str, float]
    total_transaction_cost: float
    cost_impact: float

    # 風險指標
    portfolio_volatility: float
    portfolio_beta: float
    expected_return: float
    sharpe_ratio: float

    # 制度信息
    current_regime: Optional[RegimeState] = None
    allocation_strategy: str = ""

    # 執行計劃
    execution_schedule: Dict[str, List[Tuple[datetime, float]]] = field(
        default_factory = dict
    )


class DynamicAssetAllocator:
    """
    動態資產配置器

    根據市場制度動態調整資產配置，考慮交易成本和風險管理
    """

    def __init__(
        self,
        assets: List[AssetConfig],
        config: Optional[AllocationConfig] = None,
        regime_detector: Optional[MarketRegimeDetector] = None,
    ):
        """初始化動態資產配置器"""
        self.assets = {asset.symbol: asset for asset in assets}
        self.config = config or AllocationConfig()
        self.regime_detector = regime_detector

        # 核心組件
        self.indicators = CoreIndicators()
        self.backtest_engine = VectorBTEngine(BacktestConfig())

        # 配置歷史
        self.allocation_history = []
        self.regime_history = []

        # 緩存
        self._cache = {}
        self._last_rebalance = None

        # 制度特定策略
        self.regime_strategies = self._initialize_regime_strategies()

        logger.info(f"Dynamic Asset Allocator initialized with {len(assets)} assets")

    def _initialize_regime_strategies(self) -> Dict[str, Dict[str, float]]:
        """初始化制度特定策略"""
        return {
            "Bull Market": {
                # 激進配置，偏向權益
                "equity_weight": 0.8,
                "bond_weight": 0.15,
                "alternative_weight": 0.05,
                "volatility_scaling": 1.2,
            },
            "Bear Market": {
                # 防禦配置，偏向債券
                "equity_weight": 0.3,
                "bond_weight": 0.6,
                "alternative_weight": 0.1,
                "volatility_scaling": 0.8,
            },
            "Sideways / Range - Bound": {
                # 平衡配置
                "equity_weight": 0.6,
                "bond_weight": 0.35,
                "alternative_weight": 0.05,
                "volatility_scaling": 1.0,
            },
        }

    def calculate_optimal_allocation(
        self,
        market_data: Dict[str, pd.DataFrame],
        current_weights: Optional[Dict[str, float]] = None,
        regime_prediction: Optional[RegimePrediction] = None,
    ) -> AllocationResult:
        """
        計算最優資產配置

        Args:
            market_data: 市場數據
            current_weights: 當前權重
            regime_prediction: 制度預測

        Returns:
            配置結果
        """
        if current_weights is None:
            current_weights = {symbol: 0.0 for symbol in self.assets.keys()}

        logger.info("Calculating optimal asset allocation...")

        # 獲取當前市場制度
        if regime_prediction is None and self.regime_detector is not None:
            regime_prediction = self.regime_detector.predict(market_data)

        current_regime = regime_prediction.current_regime if regime_prediction else None

        # 計算基礎權重
        base_weights = self._calculate_base_weights(market_data, current_regime)

        # 應用制度調整
        if current_regime:
            regime_adjusted_weights = self._apply_regime_adjustment(
                base_weights, current_regime, regime_prediction
            )
        else:
            regime_adjusted_weights = base_weights

        # 風險管理調整
        risk_adjusted_weights = self._apply_risk_adjustments(
            regime_adjusted_weights, market_data
        )

        # 交易成本優化
        cost_optimized_weights = self._optimize_for_transaction_costs(
            risk_adjusted_weights, current_weights, market_data
        )

        # 計算交易計劃
        trades = self._calculate_trades(cost_optimized_weights, current_weights)

        # 計算交易成本
        transaction_costs = self._calculate_transaction_costs(trades, market_data)

        # 計算風險指標
        risk_metrics = self._calculate_portfolio_risk(
            cost_optimized_weights, market_data
        )

        # 生成執行計劃
        execution_schedule = self._create_execution_schedule(trades)

        result = AllocationResult(
            timestamp = datetime.now(),
            target_weights = cost_optimized_weights,
            current_weights = current_weights,
            trades = trades,
            expected_transaction_costs = transaction_costs,
            total_transaction_cost = sum(transaction_costs.values()),
            cost_impact=(
                sum(transaction_costs.values()) / sum(trades.values()) if trades else 0
            ),
            portfolio_volatility = risk_metrics["volatility"],
            portfolio_beta = risk_metrics["beta"],
            expected_return = risk_metrics["expected_return"],
            sharpe_ratio = risk_metrics["sharpe_ratio"],
            current_regime = current_regime,
            allocation_strategy = self._get_strategy_name(current_regime),
            execution_schedule = execution_schedule,
        )

        # 記錄配置歷史
        self.allocation_history.append(result)

        logger.info(
            f"Allocation calculated. Total cost: {result.total_transaction_cost:.4f}"
        )

        return result

    def _calculate_base_weights(
        self,
        market_data: Dict[str, pd.DataFrame],
        current_regime: Optional[RegimeState] = None,
    ) -> Dict[str, float]:
        """計算基礎權重"""
        weights = {}

        # 按資產類別分組
        asset_classes = {}
        for symbol, asset in self.assets.items():
            if asset.asset_class not in asset_classes:
                asset_classes[asset.asset_class] = []
            asset_classes[asset.asset_class].append(symbol)

        # 使用制度特定策略
        if current_regime and current_regime.regime_name in self.regime_strategies:
            strategy = self.regime_strategies[current_regime.regime_name]

            # 為每個資產類別分配權重
            for asset_class, symbols in asset_classes.items():
                class_weight_key = f"{asset_class}_weight"
                class_weight = strategy.get(class_weight_key, 1.0 / len(asset_classes))

                # 在類別內平均分配
                weight_per_asset = class_weight / len(symbols)
                for symbol in symbols:
                    weights[symbol] = weight_per_asset
        else:
            # 默認等權重配置
            equal_weight = 1.0 / len(self.assets)
            weights = {symbol: equal_weight for symbol in self.assets.keys()}

        # 應用波動率縮放
        if current_regime and self.regime_strategies.get(current_regime.regime_name):
            vol_scaling = self.regime_strategies[current_regime.regime_name].get(
                "volatility_scaling", 1.0
            )
            weights = {k: v * vol_scaling for k, v in weights.items()}

        # 正規化權重
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}

        return weights

    def _apply_regime_adjustment(
        self,
        base_weights: Dict[str, float],
        current_regime: RegimeState,
        regime_prediction: RegimePrediction,
    ) -> Dict[str, float]:
        """應用制度調整"""
        adjusted_weights = base_weights.copy()

        # 基於制度特徵調整權重
        regime_factor = self.config.regime_weight_factor

        # 波動率調整
        if current_regime.volatility_level == "High":
            # 高波動率時降低風險資產權重
            for symbol, asset in self.assets.items():
                if asset.asset_class == "equity":
                    adjusted_weights[symbol] *= 1 - regime_factor * 0.3
                elif asset.asset_class == "bond":
                    adjusted_weights[symbol] *= 1 + regime_factor * 0.2

        # 趨勢調整
        if current_regime.trend_strength == "Strong":
            if current_regime.momentum_direction == "Positive":
                # 強勢上漲時增加權益暴露
                for symbol, asset in self.assets.items():
                    if asset.asset_class == "equity":
                        adjusted_weights[symbol] *= 1 + regime_factor * 0.2
            else:
                # 強勢下跌時減少權益暴露
                for symbol, asset in self.assets.items():
                    if asset.asset_class == "equity":
                        adjusted_weights[symbol] *= 1 - regime_factor * 0.3

        # 基於預測置信度調整
        if regime_prediction.prediction_confidence > 0.8:
            # 高置信度時增加調整幅度
            adjustment_multiplier = 1.2
        elif regime_prediction.prediction_confidence < 0.5:
            # 低置信度時減少調整幅度
            adjustment_multiplier = 0.5
        else:
            adjustment_multiplier = 1.0

        for symbol in adjusted_weights:
            base = base_weights[symbol]
            adjusted = adjusted_weights[symbol]
            adjusted_weights[symbol] = base + (adjusted - base) * adjustment_multiplier

        # 正規化權重
        total_weight = sum(adjusted_weights.values())
        if total_weight > 0:
            adjusted_weights = {
                k: v / total_weight for k, v in adjusted_weights.items()
            }

        return adjusted_weights

    def _apply_risk_adjustments(
        self, weights: Dict[str, float], market_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, float]:
        """應用風險管理調整"""
        adjusted_weights = weights.copy()

        # 計算資產風險
        asset_risks = {}
        for symbol, data in market_data.items():
            if symbol in self.assets:
                # 計歷史波動率
                returns = data["close"].pct_change().dropna()
                volatility = returns.std() * np.sqrt(252)

                # 檢查最大回撤
                cumulative = (1 + returns).cumprod()
                rolling_max = cumulative.expanding().max()
                drawdown = (cumulative - rolling_max) / rolling_max
                max_drawdown = drawdown.min()

                asset_risks[symbol] = {
                    "volatility": volatility,
                    "max_drawdown": max_drawdown,
                }

        # 波動率目標調整
        if self.config.volatility_target > 0:
            portfolio_volatility = self._calculate_portfolio_volatility(
                weights, asset_risks, market_data
            )

            if portfolio_volatility > self.config.volatility_target:
                scaling_factor = self.config.volatility_target / portfolio_volatility
                adjusted_weights = {
                    k: v * scaling_factor for k, v in adjusted_weights.items()
                }

        # 最大回撤限制
        for symbol, asset in self.assets.items():
            if symbol in asset_risks:
                max_dd = asset_risks[symbol]["max_drawdown"]
                if abs(max_dd) > asset.max_drawdown_limit:
                    # 減少超限資產的權重
                    reduction_factor = asset.max_drawdown_limit / abs(max_dd)
                    adjusted_weights[symbol] *= reduction_factor

        # 應用權重約束
        for symbol, asset in self.assets.items():
            if symbol in adjusted_weights:
                adjusted_weights[symbol] = max(
                    asset.min_weight, min(asset.max_weight, adjusted_weights[symbol])
                )

        # 正規化權重
        total_weight = sum(adjusted_weights.values())
        if total_weight > 0:
            adjusted_weights = {
                k: v / total_weight for k, v in adjusted_weights.items()
            }

        return adjusted_weights

    def _optimize_for_transaction_costs(
        self,
        target_weights: Dict[str, float],
        current_weights: Dict[str, float],
        market_data: Dict[str, pd.DataFrame],
    ) -> Dict[str, float]:
        """優化交易成本"""
        optimized_weights = target_weights.copy()

        # 計算初步交易
        trades = self._calculate_trades(target_weights, current_weights)

        # 計算交易成本
        total_costs = 0
        for symbol, trade_size in trades.items():
            if symbol in self.assets and abs(trade_size) > self.config.min_trade_size:
                asset = self.assets[symbol]
                cost = abs(trade_size) * (
                    asset.commission_rate
                    + asset.bid_ask_spread / 2
                    + asset.market_impact * abs(trade_size)
                )
                total_costs += cost

        # 如果總成本超過閾值，進行成本優化
        if total_costs > self.config.cost_threshold:
            # 減少小額交易
            for symbol, trade_size in trades.items():
                if abs(trade_size) < self.config.cost_threshold / len(trades):
                    # 跳過小額交易
                    optimized_weights[symbol] = current_weights.get(symbol, 0)

        # 應用最大倉位變化限制
        for symbol in optimized_weights:
            current_weight = current_weights.get(symbol, 0)
            max_change = self.config.max_position_change

            if abs(optimized_weights[symbol] - current_weight) > max_change:
                # 限制變化幅度
                direction = 1 if optimized_weights[symbol] > current_weight else -1
                optimized_weights[symbol] = current_weight + direction * max_change

        # 正規化權重
        total_weight = sum(optimized_weights.values())
        if total_weight > 0:
            optimized_weights = {
                k: v / total_weight for k, v in optimized_weights.items()
            }

        return optimized_weights

    def _calculate_trades(
        self, target_weights: Dict[str, float], current_weights: Dict[str, float]
    ) -> Dict[str, float]:
        """計算交易計劃"""
        trades = {}

        for symbol in self.assets.keys():
            target = target_weights.get(symbol, 0)
            current = current_weights.get(symbol, 0)
            trade = target - current

            if abs(trade) > self.config.min_trade_size:
                trades[symbol] = trade

        return trades

    def _calculate_transaction_costs(
        self, trades: Dict[str, float], market_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, float]:
        """計算交易成本"""
        costs = {}

        for symbol, trade_size in trades.items():
            if symbol in self.assets:
                asset = self.assets[symbol]

                # 獲取當前價格
                if symbol in market_data and len(market_data[symbol]) > 0:
                    current_price = market_data[symbol]["close"].iloc[-1]
                else:
                    current_price = 1.0  # 默認價格

                # 計算各項成本
                commission = abs(trade_size) * asset.commission_rate
                spread_cost = abs(trade_size) * asset.bid_ask_spread / 2
                market_impact_cost = (
                    abs(trade_size) * asset.market_impact * abs(trade_size)
                )

                total_cost = commission + spread_cost + market_impact_cost
                costs[symbol] = total_cost

        return costs

    def _calculate_portfolio_risk(
        self, weights: Dict[str, float], market_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, float]:
        """計算投資組合風險指標"""
        if not weights:
            return {
                "volatility": 0.0,
                "beta": 0.0,
                "expected_return": 0.0,
                "sharpe_ratio": 0.0,
            }

        # 計算資產回報率
        returns_data = {}
        for symbol, data in market_data.items():
            if symbol in weights and len(data) > 1:
                returns = data["close"].pct_change().dropna()
                returns_data[symbol] = returns

        if not returns_data:
            return {
                "volatility": 0.0,
                "beta": 0.0,
                "expected_return": 0.0,
                "sharpe_ratio": 0.0,
            }

        # 對齊時間序列
        returns_df = pd.DataFrame(returns_data)
        returns_df = returns_df.dropna()

        if returns_df.empty:
            return {
                "volatility": 0.0,
                "beta": 0.0,
                "expected_return": 0.0,
                "sharpe_ratio": 0.0,
            }

        # 構建權重向量
        weight_vector = np.array([weights.get(col, 0) for col in returns_df.columns])

        # 計算投資組合回報率
        portfolio_returns = (returns_df * weight_vector).sum(axis = 1)

        # 風險指標
        volatility = portfolio_returns.std() * np.sqrt(252)
        expected_return = portfolio_returns.mean() * 252

        # 簡化的Beta計算（假設市場回報率為等權重組合）
        market_returns = returns_df.mean(axis = 1)
        covariance = np.cov(portfolio_returns, market_returns)[0, 1]
        market_variance = market_returns.var()
        beta = covariance / market_variance if market_variance > 0 else 0

        # Sharpe比率（假設無風險利率為3%）
        risk_free_rate = 0.03
        sharpe_ratio = (
            (expected_return - risk_free_rate) / volatility if volatility > 0 else 0
        )

        return {
            "volatility": float(volatility),
            "beta": float(beta),
            "expected_return": float(expected_return),
            "sharpe_ratio": float(sharpe_ratio),
        }

    def _calculate_portfolio_volatility(
        self,
        weights: Dict[str, float],
        asset_risks: Dict[str, Dict[str, float]],
        market_data: Dict[str, pd.DataFrame],
    ) -> float:
        """計算投資組合波動率"""
        if not weights:
            return 0.0

        # 簡化計算：使用資產波動率的加權平均
        weighted_volatility = 0
        total_weight = sum(weights.values())

        for symbol, weight in weights.items():
            if symbol in asset_risks:
                vol = asset_risks[symbol]["volatility"]
                weighted_volatility += weight * vol

        return weighted_volatility if total_weight > 0 else 0.0

    def _create_execution_schedule(
        self, trades: Dict[str, float]
    ) -> Dict[str, List[Tuple[datetime, float]]]:
        """創建執行時間表"""
        schedule = {}

        for symbol, trade_size in trades.items():
            if abs(trade_size) > 0:
                # 分批執行以減少市場衝擊
                n_batches = min(
                    5, int(abs(trade_size) / self.config.min_trade_size) + 1
                )
                batch_size = trade_size / n_batches

                execution_times = []
                for i in range(n_batches):
                    # 均勻分布在未來幾天
                    days_ahead = i * 2  # 每2天一批
                    execution_time = datetime.now() + timedelta(days = days_ahead)
                    execution_times.append((execution_time, batch_size))

                schedule[symbol] = execution_times

        return schedule

    def _get_strategy_name(self, current_regime: Optional[RegimeState]) -> str:
        """獲取策略名稱"""
        if current_regime:
            return f"Regime - based ({current_regime.regime_name})"
        else:
            return "Strategic"

    def run_backtest(
        self,
        market_data: Dict[str, pd.DataFrame],
        start_date: datetime,
        end_date: datetime,
        initial_weights: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        運行回測

        Args:
            market_data: 市場數據
            start_date: 開始日期
            end_date: 結束日期
            initial_weights: 初始權重

        Returns:
            回測結果
        """
        logger.info(f"Running backtest from {start_date} to {end_date}")

        # 初始化
        if initial_weights is None:
            initial_weights = {
                symbol: 1.0 / len(self.assets) for symbol in self.assets.keys()
            }

        current_weights = initial_weights.copy()

        # 生成再平衡日期
        rebalance_dates = self._generate_rebalance_dates(start_date, end_date)

        results = []
        portfolio_values = []

        for rebalance_date in rebalance_dates:
            # 獲取截至該日期的數據
            historical_data = self._get_historical_data(market_data, rebalance_date)

            if not historical_data:
                continue

            try:
                # 計算配置
                allocation = self.calculate_optimal_allocation(
                    historical_data, current_weights
                )

                # 模擬交易執行
                execution_result = self._execute_allocation(allocation, historical_data)

                # 更新權重
                current_weights = allocation.target_weights.copy()

                # 記錄結果
                results.append(
                    {
                        "date": rebalance_date,
                        "allocation": allocation,
                        "execution": execution_result,
                    }
                )

                # 計算投資組合價值（簡化）
                portfolio_value = self._calculate_portfolio_value(
                    current_weights, historical_data
                )
                portfolio_values.append(
                    {"date": rebalance_date, "value": portfolio_value}
                )

            except Exception as e:
                logger.error(f"Error in rebalance on {rebalance_date}: {e}")
                continue

        # 計算性能指標
        performance_metrics = self._calculate_backtest_performance(portfolio_values)

        return {
            "results": results,
            "portfolio_values": portfolio_values,
            "performance": performance_metrics,
            "summary": {
                "total_rebalances": len(results),
                "average_transaction_cost": (
                    np.mean([r["allocation"].total_transaction_cost for r in results])
                    if results
                    else 0
                ),
                "final_weights": current_weights,
            },
        }

    def _generate_rebalance_dates(
        self, start_date: datetime, end_date: datetime
    ) -> List[datetime]:
        """生成再平衡日期"""
        dates = []
        current_date = start_date

        if self.config.rebalance_frequency == "daily":
            delta = timedelta(days = 1)
        elif self.config.rebalance_frequency == "weekly":
            delta = timedelta(weeks = 1)
        elif self.config.rebalance_frequency == "monthly":
            delta = timedelta(days = 30)
        else:  # quarterly
            delta = timedelta(days = 90)

        while current_date <= end_date:
            dates.append(current_date)
            current_date += delta

        return dates

    def _get_historical_data(
        self, market_data: Dict[str, pd.DataFrame], date: datetime
    ) -> Dict[str, pd.DataFrame]:
        """獲取歷史數據"""
        historical_data = {}

        for symbol, data in market_data.items():
            # 篩選截至指定日期的數據
            mask = data.index <= date
            filtered_data = data[mask].copy()

            if len(filtered_data) >= self.config.lookback_period:
                # 使用回看期數據
                historical_data[symbol] = filtered_data.tail(
                    self.config.lookback_period
                )

        return historical_data

    def _execute_allocation(
        self, allocation: AllocationResult, market_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, Any]:
        """模擬執行配置"""
        execution_result = {
            "executed_trades": {},
            "actual_costs": {},
            "slippage": {},
            "execution_time": datetime.now(),
        }

        for symbol, trade_size in allocation.trades.items():
            if symbol in market_data and len(market_data[symbol]) > 0:
                # 模擬執行
                current_price = market_data[symbol]["close"].iloc[-1]

                # 計算滑點
                slippage_pct = np.random.normal(0, 0.001)  # 0.1%標準差
                execution_price = current_price * (1 + slippage_pct)

                execution_result["executed_trades"][symbol] = {
                    "size": trade_size,
                    "price": execution_price,
                    "value": trade_size * execution_price,
                }

                execution_result["slippage"][symbol] = abs(slippage_pct)

                # 實際成本
                actual_cost = allocation.expected_transaction_costs.get(symbol, 0) * (
                    1 + abs(slippage_pct)
                )
                execution_result["actual_costs"][symbol] = actual_cost

        return execution_result

    def _calculate_portfolio_value(
        self, weights: Dict[str, float], market_data: Dict[str, pd.DataFrame]
    ) -> float:
        """計算投資組合價值（簡化）"""
        total_value = 0

        for symbol, weight in weights.items():
            if symbol in market_data and len(market_data[symbol]) > 0:
                price = market_data[symbol]["close"].iloc[-1]
                total_value += weight * price

        return total_value

    def _calculate_backtest_performance(
        self, portfolio_values: List[Dict]
    ) -> Dict[str, float]:
        """計算回測性能指標"""
        if len(portfolio_values) < 2:
            return {
                "total_return": 0.0,
                "annualized_return": 0.0,
                "volatility": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
            }

        # 轉換為DataFrame
        df = pd.DataFrame(portfolio_values)
        df.set_index("date", inplace = True)

        # 計算回報率
        returns = df["value"].pct_change().dropna()

        # 性能指標
        total_return = (df["value"].iloc[-1] / df["value"].iloc[0]) - 1
        days = (df.index[-1] - df.index[0]).days
        annualized_return = (1 + total_return) ** (365 / days) - 1 if days > 0 else 0
        volatility = returns.std() * np.sqrt(365)

        # Sharpe比率
        risk_free_rate = 0.03
        sharpe_ratio = (
            (annualized_return - risk_free_rate) / volatility if volatility > 0 else 0
        )

        # 最大回撤
        cumulative = (1 + returns).cumprod()
        rolling_max = cumulative.expanding().max()
        drawdown = (cumulative - rolling_max) / rolling_max
        max_drawdown = drawdown.min()

        return {
            "total_return": float(total_return),
            "annualized_return": float(annualized_return),
            "volatility": float(volatility),
            "sharpe_ratio": float(sharpe_ratio),
            "max_drawdown": float(max_drawdown),
        }


# 便利函數
def create_dynamic_allocator(
    asset_configs: List[AssetConfig],
    regime_config: Optional[RegimeConfig] = None,
    allocation_config: Optional[AllocationConfig] = None,
) -> DynamicAssetAllocator:
    """便利函數：創建動態資產配置器"""
    # 創建制度檢測器
    regime_detector = MarketRegimeDetector(regime_config)

    # 創建配置器
    allocator = DynamicAssetAllocator(asset_configs, allocation_config, regime_detector)

    return allocator


def backtest_dynamic_allocation(
    assets: List[AssetConfig],
    market_data: Dict[str, pd.DataFrame],
    start_date: datetime,
    end_date: datetime,
) -> Dict[str, Any]:
    """便利函數：回測動態配置"""
    allocator = create_dynamic_allocator(assets)
    return allocator.run_backtest(market_data, start_date, end_date)

#!/usr / bin / env python3
"""
Factor Investment Portfolio
因子投資組合管理

實現專業級的因子投資組合管理功能：
- 因子選股策略
- 權重分配算法
- 風險控制機制
- 投資組合績效分析
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class PortfolioStrategy(Enum):
    """投資組合策略枚舉"""

    TOP_QUANTILES = "top_quantiles"  # 頂部分位數
    BOTTOM_QUANTILES = "bottom_quantiles"  # 底部分位數
    LONG_SHORT = "long_short"  # 多空組合
    FACTOR_TILT = "factor_tilt"  # 因子傾斜
    RISK_PARITY = "risk_parity"  # 風險平價
    EQUAL_WEIGHT = "equal_weight"  # 等權重


@dataclass
class PortfolioConfig:
    """投資組合配置"""

    strategy: PortfolioStrategy = PortfolioStrategy.TOP_QUANTILES
    top_quantile_threshold: float = 0.8  # 頂部分位數閾值
    bottom_quantile_threshold: float = 0.2  # 底部分位數閾值
    max_position_size: float = 0.05  # 最大持倉比例
    min_position_size: float = 0.01  # 最小持倉比例
    max_positions: int = 50  # 最大持倉數量
    rebalance_frequency: str = "monthly"  # 再平衡頻率
    transaction_costs: float = 0.001  # 交易成本
    risk_limit: float = 0.15  # 風險限制
    leverage_limit: float = 1.0  # 槓桿限制


@dataclass
class Position:
    """持倉信息"""

    symbol: str
    weight: float
    entry_price: float
    entry_date: pd.Timestamp
    factor_scores: Dict[str, float]
    sector: Optional[str] = None


@dataclass
class PortfolioMetrics:
    """投資組合指標"""

    total_return: float = 0.0
    annualized_return: float = 0.0
    volatility: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    turnover_rate: float = 0.0
    position_count: int = 0
    concentration_ratio: float = 0.0


class FactorInvestmentPortfolio:
    """
    因子投資組合管理器

    提供專業級的因子投資組合管理功能，包括選股、權重分配、風險控制等。
    """

    def __init__(self, config: Optional[PortfolioConfig] = None):
        """
        初始化因子投資組合管理器

        Args:
            config: 投資組合配置
        """
        self.config = config or PortfolioConfig()
        self.positions: Dict[str, Position] = {}
        self.portfolio_history: List[Dict] = []
        self.performance_metrics = PortfolioMetrics()

        logger.info(
            f"Factor Investment Portfolio initialized with strategy: {self.config.strategy.value}"
        )

    def select_stocks(
        self, factor_scores: pd.DataFrame, universe: Optional[List[str]] = None
    ) -> List[str]:
        """
        基於因子分數選擇股票

        Args:
            factor_scores: 因子分數數據 (assets x factors)
            universe: 可投資股票宇宙

        Returns:
            List[str]: 選中的股票列表
        """
        logger.info("Selecting stocks based on factor scores")

        # 計算綜合因子分數
        composite_scores = self._calculate_composite_scores(factor_scores)

        # 應用股票宇宙限制
        if universe:
            composite_scores = composite_scores[composite_scores.index.isin(universe)]

        if composite_scores.empty:
            logger.warning("No stocks available for selection")
            return []

        # 根據策略選擇股票
        if self.config.strategy == PortfolioStrategy.TOP_QUANTILES:
            selected = self._select_top_quantiles(composite_scores)
        elif self.config.strategy == PortfolioStrategy.BOTTOM_QUANTILES:
            selected = self._select_bottom_quantiles(composite_scores)
        elif self.config.strategy == PortfolioStrategy.LONG_SHORT:
            selected = self._select_long_short(composite_scores)
        elif self.config.strategy == PortfolioStrategy.FACTOR_TILT:
            selected = self._select_factor_tilt(composite_scores)
        else:
            selected = self._select_top_quantiles(composite_scores)

        # 限制持倉數量
        if len(selected) > self.config.max_positions:
            if self.config.strategy in [
                PortfolioStrategy.TOP_QUANTILES,
                PortfolioStrategy.FACTOR_TILT,
            ]:
                selected = selected[: self.config.max_positions]
            else:
                # 對於其他策略，選擇分數最極端的股票
                scores = composite_scores.loc[selected]
                if self.config.strategy == PortfolioStrategy.BOTTOM_QUANTILES:
                    selected = scores.nsmallest(
                        self.config.max_positions
                    ).index.tolist()
                else:
                    selected = scores.nlargest(self.config.max_positions).index.tolist()

        logger.info(f"Selected {len(selected)} stocks")
        return selected

    def _calculate_composite_scores(self, factor_scores: pd.DataFrame) -> pd.Series:
        """計算綜合因子分數"""
        # 簡單的等權重綜合分數
        composite_scores = factor_scores.mean(axis = 1)

        # 處理缺失值
        composite_scores = composite_scores.fillna(0)

        # 標準化分數
        mean_score = composite_scores.mean()
        std_score = composite_scores.std()

        if std_score > 0:
            composite_scores = (composite_scores - mean_score) / std_score

        return composite_scores

    def _select_top_quantiles(self, scores: pd.Series) -> List[str]:
        """選擇頂部分位數股票"""
        threshold = scores.quantile(self.config.top_quantile_threshold)
        selected = scores[scores >= threshold].index.tolist()
        return selected

    def _select_bottom_quantiles(self, scores: pd.Series) -> List[str]:
        """選擇底部分位數股票"""
        threshold = scores.quantile(self.config.bottom_quantile_threshold)
        selected = scores[scores <= threshold].index.tolist()
        return selected

    def _select_long_short(self, scores: pd.Series) -> List[str]:
        """選擇多空組合股票"""
        top_threshold = scores.quantile(self.config.top_quantile_threshold)
        bottom_threshold = scores.quantile(self.config.bottom_quantile_threshold)

        top_stocks = scores[scores >= top_threshold].index.tolist()
        bottom_stocks = scores[scores <= bottom_threshold].index.tolist()

        # 為多空組合添加標識
        selected = []
        for stock in top_stocks:
            selected.append(f"LONG_{stock}")
        for stock in bottom_stocks:
            selected.append(f"SHORT_{stock}")

        return selected

    def _select_factor_tilt(self, scores: pd.Series) -> List[str]:
        """因子傾斜選股"""
        # 選擇因子分數最高的一半，但權重傾斜
        threshold = scores.quantile(0.5)
        selected = scores[scores >= threshold].index.tolist()
        return selected

    def allocate_weights(
        self,
        selected_stocks: List[str],
        factor_scores: pd.DataFrame,
        price_data: Optional[pd.DataFrame] = None,
    ) -> Dict[str, float]:
        """
        分配權重

        Args:
            selected_stocks: 選中的股票列表
            factor_scores: 因子分數數據
            price_data: 價格數據（可選，用於市值加權）

        Returns:
            Dict[str, float]: 權重分配字典
        """
        logger.info(f"Allocating weights for {len(selected_stocks)} stocks")

        weights = {}

        if self.config.strategy == PortfolioStrategy.LONG_SHORT:
            # 多空組合權重分配
            long_stocks = [s[5:] for s in selected_stocks if s.startswith("LONG_")]
            short_stocks = [s[6:] for s in selected_stocks if s.startswith("SHORT_")]

            # 多頭權重
            if long_stocks:
                long_weights = self._allocate_equal_weights(long_stocks, factor_scores)
                weights.update(
                    {f"LONG_{stock}": weight for stock, weight in long_weights.items()}
                )

            # 空頭權重（負權重）
            if short_stocks:
                short_weights = self._allocate_equal_weights(
                    short_stocks, factor_scores
                )
                weights.update(
                    {
                        f"SHORT_{stock}": -weight
                        for stock, weight in short_weights.items()
                    }
                )

        elif self.config.strategy == PortfolioStrategy.FACTOR_TILT:
            # 因子傾斜權重分配
            weights = self._allocate_factor_tilt_weights(selected_stocks, factor_scores)

        elif self.config.strategy == PortfolioStrategy.RISK_PARITY:
            # 風險平價權重分配
            weights = self._allocate_risk_parity_weights(
                selected_stocks, factor_scores, price_data
            )

        else:
            # 等權重或頂部分位數權重分配
            weights = self._allocate_equal_weights(selected_stocks, factor_scores)

        # 應用權重限制
        weights = self._apply_weight_constraints(weights)

        # 標準化權重
        total_weight = sum(abs(w) for w in weights.values())
        if total_weight > 0:
            if self.config.strategy == PortfolioStrategy.LONG_SHORT:
                # 多空組合保持淨值為0
                weights = {
                    k: v * self.config.leverage_limit for k, v in weights.items()
                }
            else:
                # 單向組合標準化到1
                weights = {k: v / total_weight for k, v in weights.items()}

        logger.info(f"Allocated weights to {len(weights)} positions")
        return weights

    def _allocate_equal_weights(
        self, stocks: List[str], factor_scores: pd.DataFrame
    ) -> Dict[str, float]:
        """等權重分配"""
        available_stocks = [s for s in stocks if s in factor_scores.index]
        weight = 1.0 / len(available_stocks)
        return {stock: weight for stock in available_stocks}

    def _allocate_factor_tilt_weights(
        self, stocks: List[str], factor_scores: pd.DataFrame
    ) -> Dict[str, float]:
        """因子傾斜權重分配"""
        available_stocks = [s for s in stocks if s in factor_scores.index]

        if not available_stocks:
            return {}

        # 使用綜合因子分數進行傾斜加權
        composite_scores = self._calculate_composite_scores(
            factor_scores.loc[available_stocks]
        )

        # 將分數轉換為權重
        positive_scores = composite_scores[composite_scores > 0]
        if len(positive_scores) > 0:
            weights = positive_scores / positive_scores.sum()
            return weights.to_dict()
        else:
            # 如果沒有正分數，使用等權重
            return {stock: 1.0 / len(available_stocks) for stock in available_stocks}

    def _allocate_risk_parity_weights(
        self,
        stocks: List[str],
        factor_scores: pd.DataFrame,
        price_data: Optional[pd.DataFrame] = None,
    ) -> Dict[str, float]:
        """風險平價權重分配"""
        available_stocks = [s for s in stocks if s in factor_scores.index]

        if not available_stocks:
            return {}

        # 簡化的風險平價：基於因子分數的反比權重
        # 更複雜的實現可以使用歷史收益率協方差矩陣
        composite_scores = self._calculate_composite_scores(
            factor_scores.loc[available_stocks]
        )

        # 使用分數的倒數作為權重（分數越高，風險越低，權重越大）
        risk_weights = 1.0 / (abs(composite_scores) + 1e - 6)  # 加上小數避免除零
        weights = risk_weights / risk_weights.sum()

        return weights.to_dict()

    def _apply_weight_constraints(self, weights: Dict[str, float]) -> Dict[str, float]:
        """應用權重約束"""
        constrained_weights = {}

        for stock, weight in weights.items():
            # 應用最大持倉限制
            if abs(weight) > self.config.max_position_size:
                weight = np.sign(weight) * self.config.max_position_size

            # 應用最小持倉限制
            if abs(weight) < self.config.min_position_size and abs(weight) > 0:
                weight = 0  # 移除太小的倉位

            constrained_weights[stock] = weight

        return constrained_weights

    def calculate_portfolio_metrics(
        self,
        weights: Dict[str, float],
        returns_data: pd.DataFrame,
        benchmark_returns: Optional[pd.Series] = None,
    ) -> PortfolioMetrics:
        """
        計算投資組合指標

        Args:
            weights: 權重分配
            returns_data: 收益率數據
            benchmark_returns: 基準收益率

        Returns:
            PortfolioMetrics: 投資組合指標
        """
        logger.info("Calculating portfolio metrics")

        try:
            # 計算投資組合收益率
            portfolio_returns = self._calculate_portfolio_returns(weights, returns_data)

            if portfolio_returns.empty:
                logger.warning("No portfolio returns calculated")
                return PortfolioMetrics()

            # 計算基本指標
            total_return = portfolio_returns.sum()
            annualized_return = portfolio_returns.mean() * 252
            volatility = portfolio_returns.std() * np.sqrt(252)

            # 計算Sharpe比率
            risk_free_rate = 0.03  # 3%無風險利率
            sharpe_ratio = (
                (annualized_return - risk_free_rate) / volatility
                if volatility > 0
                else 0
            )

            # 計算最大回撤
            cumulative_returns = (1 + portfolio_returns).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdowns = (cumulative_returns - running_max) / running_max
            max_drawdown = drawdowns.min()

            # 計算勝率
            win_rate = (portfolio_returns > 0).mean()

            # 計算盈利因子
            winning_returns = portfolio_returns[portfolio_returns > 0]
            losing_returns = portfolio_returns[portfolio_returns < 0]

            if len(losing_returns) > 0:
                profit_factor = abs(winning_returns.sum()) / abs(losing_returns.sum())
            else:
                profit_factor = float("inf") if len(winning_returns) > 0 else 0

            # 計算換手率
            turnover_rate = self._calculate_turnover_rate(weights, returns_data)

            # 其他指標
            position_count = len(weights)
            concentration_ratio = (
                max(abs(w) for w in weights.values()) if weights else 0
            )

            metrics = PortfolioMetrics(
                total_return = total_return,
                annualized_return = annualized_return,
                volatility = volatility,
                sharpe_ratio = sharpe_ratio,
                max_drawdown = max_drawdown,
                win_rate = win_rate,
                profit_factor = profit_factor,
                turnover_rate = turnover_rate,
                position_count = position_count,
                concentration_ratio = concentration_ratio,
            )

            logger.info(
                f"Portfolio metrics calculated: Sharpe={sharpe_ratio:.3f}, Return={annualized_return:.2%}"
            )
            return metrics

        except Exception as e:
            logger.error(f"Portfolio metrics calculation failed: {e}")
            return PortfolioMetrics()

    def _calculate_portfolio_returns(
        self, weights: Dict[str, float], returns_data: pd.DataFrame
    ) -> pd.Series:
        """計算投資組合收益率"""
        if returns_data.empty:
            return pd.Series()

        # 對齊權重和收益率數據
        available_assets = [
            w[5:] if w.startswith(("LONG_", "SHORT_")) else w for w in weights.keys()
        ]
        available_assets = [a for a in available_assets if a in returns_data.columns]

        if not available_assets:
            return pd.Series()

        # 構建權重向量
        aligned_weights = pd.Series(0.0, index = returns_data.columns)

        for weighted_stock, weight in weights.items():
            # 移除策略前綴
            if weighted_stock.startswith("LONG_"):
                stock = weighted_stock[5:]
                sign = 1
            elif weighted_stock.startswith("SHORT_"):
                stock = weighted_stock[6:]
                sign = -1
            else:
                stock = weighted_stock
                sign = 1

            if stock in aligned_weights.index:
                aligned_weights[stock] = weight * sign

        # 計算投資組合收益率
        portfolio_returns = (
            returns_data[available_assets] * aligned_weights[available_assets]
        ).sum(axis = 1)

        return portfolio_returns

    def _calculate_turnover_rate(
        self, weights: Dict[str, float], returns_data: pd.DataFrame
    ) -> float:
        """計算換手率"""
        # 這是一個簡化的換手率計算
        # 實際應用中需要歷史權重數據

        if len(weights) <= 1:
            return 0.0

        # 假設平均換手率基於持倉數量
        avg_positions = len(weights)
        max_positions = self.config.max_positions

        if max_positions > 0:
            turnover_rate = avg_positions / max_positions
        else:
            turnover_rate = 0.0

        return min(turnover_rate, 1.0)

    def rebalance_portfolio(
        self, current_weights: Dict[str, float], target_weights: Dict[str, float]
    ) -> Dict[str, float]:
        """
        再平衡投資組合

        Args:
            current_weights: 當前權重
            target_weights: 目標權重

        Returns:
            Dict[str, float]: 再平衡後的權重
        """
        logger.info("Rebalancing portfolio")

        # 計算權重變化
        trades = {}
        for stock, target_weight in target_weights.items():
            current_weight = current_weights.get(stock, 0)
            trade = target_weight - current_weight

            if abs(trade) > 0.001:  # 只進行有意義的交易
                trades[stock] = trade

        # 應用交易成本（簡化處理）
        for stock in trades:
            if abs(trades[stock]) < self.config.min_position_size:
                trades[stock] = 0

        # 計算再平衡後的權重
        rebalanced_weights = current_weights.copy()
        for stock, trade in trades.items():
            if trade != 0:
                rebalanced_weights[stock] = current_weights.get(stock, 0) + trade

        # 移除零權重
        rebalanced_weights = {k: v for k, v in rebalanced_weights.items() if abs(v) > 0}

        logger.info(f"Rebalanced portfolio with {len(trades)} trades")
        return rebalanced_weights

    def generate_performance_report(self) -> Dict[str, Any]:
        """生成投資組合績效報告"""
        report = {
            "portfolio_config": {
                "strategy": self.config.strategy.value,
                "max_positions": self.config.max_positions,
                "risk_limit": self.config.risk_limit,
            },
            "current_positions": {
                "count": len(self.positions),
                "total_exposure": sum(abs(p.weight) for p in self.positions.values()),
            },
            "performance_metrics": {
                "total_return": self.performance_metrics.total_return,
                "annualized_return": self.performance_metrics.annualized_return,
                "volatility": self.performance_metrics.volatility,
                "sharpe_ratio": self.performance_metrics.sharpe_ratio,
                "max_drawdown": self.performance_metrics.max_drawdown,
                "win_rate": self.performance_metrics.win_rate,
                "turnover_rate": self.performance_metrics.turnover_rate,
            },
            "position_breakdown": self._analyze_position_breakdown(),
        }

        return report

    def _analyze_position_breakdown(self) -> Dict[str, Any]:
        """分析持倉分布"""
        if not self.positions:
            return {"message": "No positions held"}

        long_positions = sum(p.weight for p in self.positions.values() if p.weight > 0)
        short_positions = sum(
            abs(p.weight) for p in self.positions.values() if p.weight < 0
        )

        top_positions = sorted(
            self.positions.values(), key = lambda x: abs(x.weight), reverse = True
        )[:10]

        return {
            "long_exposure": long_positions,
            "short_exposure": short_positions,
            "net_exposure": long_positions - short_positions,
            "gross_exposure": long_positions + short_positions,
            "top_positions": [
                {
                    "symbol": p.symbol,
                    "weight": p.weight,
                    "entry_date": p.entry_date,
                    "sector": p.sector,
                }
                for p in top_positions
            ],
        }

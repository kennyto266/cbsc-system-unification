#!/usr / bin / env python3
"""
Liquidity Risk Analysis System
流動性風險分析系統

Comprehensive liquidity risk assessment and monitoring
全面的流動性風險評估和監控系統

Features:
- Market liquidity analysis
- Funding liquidity assessment
- Liquidity stress testing
- Liquidity - adjusted VaR (L - VaR)
- Liquidity coverage ratio (LCR)
- Net stable funding ratio (NSFR)
- Liquidity risk monitoring dashboard
- Early warning indicators
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


class LiquidityType(Enum):
    """流動性類型枚舉"""

    MARKET_LIQUIDITY = "市場流動性"
    FUNDING_LIQUIDITY = "融資流動性"
    CONTINGENT_LIQUIDITY = "或有流動性"


class AssetLiquidityClass(Enum):
    """資產流動性分級"""

    HIGHLY_LIQUID = "高流動性"
    LIQUID = "流動性"
    LESS_LIQUID = "較低流動性"
    ILLIQUID = "非流動性"
    VERY_ILLIQUID = "高度非流動性"


class LiquidityRiskLevel(Enum):
    """流動性風險等級"""

    VERY_LOW = "極低"
    LOW = "低"
    MODERATE = "中等"
    HIGH = "高"
    VERY_HIGH = "極高"


@dataclass
class LiquidityMetrics:
    """流動性指標"""

    asset_name: str
    bid_ask_spread: float  # Bid - ask spread
    market_depth: float  # Market depth (average daily volume)
    price_impact: float  # Price impact coefficient
    roll_convenience_yield: float  # Roll's convenience yield
    amihud_illiquidity: float  # Amihud illiquidity measure
    kyle_lambda: float  # Kyle's lambda
    zero_return_days: float  # Percentage of zero return days
    turnover_ratio: float  # Turnover ratio
    liquidity_score: float  # Overall liquidity score (0 - 100)
    liquidity_class: AssetLiquidityClass
    liquidity_adjustment_factor: float  # For L - VaR calculation


@dataclass
class FundingLiquidityMetrics:
    """融資流動性指標"""

    funding_source: str
    funding_amount: float
    funding_cost: float  # Spread over benchmark
    maturity_profile: Dict[str, float]  # Maturity buckets
    collateral_requirements: float  # Collateral percentage
    renewal_probability: float  # Probability of renewal
    funding_concentration: float  # Concentration risk measure
    rollover_risk: float  # Rollover risk indicator


@dataclass
class LiquidityRiskResult:
    """流動性風險分析結果"""

    analysis_date: datetime
    portfolio_id: str
    market_liquidity_risk: float  # 0 - 100
    funding_liquidity_risk: float  # 0 - 100
    overall_liquidity_risk: float  # 0 - 100
    liquidity_adjusted_var: float
    liquidity_coverage_ratio: float
    net_stable_funding_ratio: float
    cash_flow_gap_analysis: Dict[str, float]
    early_warning_indicators: List[str]
    risk_level: LiquidityRiskLevel
    recommendations: List[str]


@dataclass
class LiquidityStressTestResult:
    """流動性壓力測試結果"""

    scenario_name: str
    stress_duration_days: int
    liquidity_shortfall: float
    funding_gap: float
    asset_fire_sale_loss: float
    additional_funding_needed: float
    lvr_under_stress: float  # Liquidity - adjusted VaR ratio
    recovery_time_days: int
    contingency_actions: List[str]


class LiquidityRiskAnalyzer:
    """
    流動性風險分析器

    Comprehensive liquidity risk assessment and monitoring system
    全面的流動性風險評估和監控系統
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化流動性風險分析器"""
        self.config = config or self._default_config()
        self.liquidity_thresholds = self._initialize_liquidity_thresholds()

        logger.info("Liquidity Risk Analyzer initialized successfully")

    def _default_config(self) -> Dict[str, Any]:
        """默認配置"""
        return {
            "liquidity_horizons": [1, 7, 30, 90, 180],  # days
            "lvr_confidence_level": 0.95,
            "minimum_turnover_days": 20,  # Minimum days to liquidate position
            "price_impact_threshold": 0.05,  # 5% price impact threshold
            "bid_ask_spread_threshold": 0.02,  # 2% bid - ask spread threshold
            "funding_concentration_limit": 0.25,  # 25% concentration limit
            "lcr_requirement": 0.10,  # 10% LCR requirement
            "nsfr_requirement": 1.0,  # 100% NSFR requirement
            "early_warning_threshold": 70,  # Risk score threshold for early warning
        }

    def _initialize_liquidity_thresholds(self) -> Dict[str, Dict[str, float]]:
        """初始化流動性閾值"""
        return {
            "highly_liquid": {
                "bid_ask_spread": 0.001,  # 0.1%
                "daily_volume_ratio": 0.1,  # 10% of position can be traded daily
                "price_impact": 0.01,  # 1% price impact
                "turnover_ratio": 0.1,  # 10% daily turnover
            },
            "liquid": {
                "bid_ask_spread": 0.005,  # 0.5%
                "daily_volume_ratio": 0.05,  # 5% daily
                "price_impact": 0.025,  # 2.5% price impact
                "turnover_ratio": 0.05,  # 5% daily turnover
            },
            "less_liquid": {
                "bid_ask_spread": 0.01,  # 1%
                "daily_volume_ratio": 0.02,  # 2% daily
                "price_impact": 0.05,  # 5% price impact
                "turnover_ratio": 0.02,  # 2% daily turnover
            },
            "illiquid": {
                "bid_ask_spread": 0.02,  # 2%
                "daily_volume_ratio": 0.01,  # 1% daily
                "price_impact": 0.1,  # 10% price impact
                "turnover_ratio": 0.01,  # 1% daily turnover
            },
            "very_illiquid": {
                "bid_ask_spread": 0.05,  # 5%
                "daily_volume_ratio": 0.005,  # 0.5% daily
                "price_impact": 0.2,  # 20% price impact
                "turnover_ratio": 0.005,  # 0.5% daily turnover
            },
        }

    def analyze_liquidity_risk(
        self,
        portfolio_positions: pd.DataFrame,
        market_data: Dict[str, pd.DataFrame],
        funding_data: Optional[Dict[str, Any]] = None,
    ) -> LiquidityRiskResult:
        """
        綜合流動性風險分析

        Args:
            portfolio_positions: 投資組合持倉數據
            market_data: 市場數據字典，包含交易量、價格等
            funding_data: 融資數據，包含資金來源、期限等

        Returns:
            LiquidityRiskResult: 完整的流動性風險分析結果
        """
        try:
            logger.info("Starting comprehensive liquidity risk analysis")

            # 1. 市場流動性分析
            market_liquidity_metrics = self._analyze_market_liquidity(
                portfolio_positions, market_data
            )
            market_liquidity_risk = self._calculate_market_liquidity_risk(
                market_liquidity_metrics
            )

            # 2. 融資流動性分析
            funding_liquidity_metrics = self._analyze_funding_liquidity(
                funding_data or {}
            )
            funding_liquidity_risk = self._calculate_funding_liquidity_risk(
                funding_liquidity_metrics
            )

            # 3. 流動性調整VaR計算
            liquidity_adjusted_var = self._calculate_liquidity_adjusted_var(
                portfolio_positions, market_liquidity_metrics
            )

            # 4. 監管流動性比率計算
            lcr = self._calculate_liquidity_coverage_ratio(
                portfolio_positions, market_data, funding_data
            )
            nsfr = self._calculate_net_stable_funding_ratio(
                portfolio_positions, funding_data
            )

            # 5. 現金流缺口分析
            cash_flow_gaps = self._analyze_cash_flow_gaps(
                portfolio_positions, funding_data
            )

            # 6. 早期預警指標
            early_warning_indicators = self._identify_early_warning_indicators(
                market_liquidity_risk, funding_liquidity_risk, lcr, nsfr
            )

            # 7. 綜合風險評估
            overall_liquidity_risk = self._calculate_overall_liquidity_risk(
                market_liquidity_risk, funding_liquidity_risk, lcr, nsfr
            )

            # 8. 風險等級評估
            risk_level = self._assess_liquidity_risk_level(overall_liquidity_risk)

            # 9. 生成建議
            recommendations = self._generate_liquidity_recommendations(
                market_liquidity_risk,
                funding_liquidity_risk,
                lcr,
                nsfr,
                early_warning_indicators,
            )

            result = LiquidityRiskResult(
                analysis_date = datetime.now(),
                portfolio_id = portfolio_positions.get("portfolio_id", "default"),
                market_liquidity_risk = market_liquidity_risk,
                funding_liquidity_risk = funding_liquidity_risk,
                overall_liquidity_risk = overall_liquidity_risk,
                liquidity_adjusted_var = liquidity_adjusted_var,
                liquidity_coverage_ratio = lcr,
                net_stable_funding_ratio = nsfr,
                cash_flow_gap_analysis = cash_flow_gaps,
                early_warning_indicators = early_warning_indicators,
                risk_level = risk_level,
                recommendations = recommendations,
            )

            logger.info("Liquidity risk analysis completed successfully")
            return result

        except Exception as e:
            logger.error(f"Liquidity risk analysis failed: {e}")
            raise

    def _analyze_market_liquidity(
        self, portfolio_positions: pd.DataFrame, market_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, LiquidityMetrics]:
        """分析市場流動性"""
        liquidity_metrics = {}

        try:
            for _, position in portfolio_positions.iterrows():
                asset_name = position.get("asset", "unknown")
                asset_type = position.get("asset_type", "equity")
                position_value = position.get("market_value", 0)

                # 獲取市場數據
                if asset_name in market_data:
                    asset_market_data = market_data[asset_name]
                    prices = asset_market_data.get("close", pd.Series())
                    volumes = asset_market_data.get("volume", pd.Series())
                    bid_prices = asset_market_data.get("bid", pd.Series())
                    ask_prices = asset_market_data.get("ask", pd.Series())
                else:
                    # 使用模擬數據
                    prices = pd.Series([100] * 252)
                    volumes = pd.Series([1000000] * 252)
                    bid_prices = pd.Series([99.5] * 252)
                    ask_prices = pd.Series([100.5] * 252)

                # 計算流動性指標
                metrics = self._calculate_liquidity_metrics(
                    asset_name,
                    asset_type,
                    prices,
                    volumes,
                    bid_prices,
                    ask_prices,
                    position_value,
                )
                liquidity_metrics[asset_name] = metrics

        except Exception as e:
            logger.error(f"Market liquidity analysis failed: {e}")
            # Return empty metrics if analysis fails

        return liquidity_metrics

    def _calculate_liquidity_metrics(
        self,
        asset_name: str,
        asset_type: str,
        prices: pd.Series,
        volumes: pd.Series,
        bid_prices: pd.Series,
        ask_prices: pd.Series,
        position_value: float,
    ) -> LiquidityMetrics:
        """計算單個資產的流動性指標"""
        try:
            # 1. Bid - Ask Spread
            if len(bid_prices) > 0 and len(ask_prices) > 0:
                spreads = (ask_prices - bid_prices) / ((ask_prices + bid_prices) / 2)
                bid_ask_spread = spreads.mean()
            else:
                # 模擬買賣價差
                if asset_type.lower() in ["stock", "equity"]:
                    bid_ask_spread = 0.005  # 0.5%
                elif asset_type.lower() in ["bond", "fixed_income"]:
                    bid_ask_spread = 0.01  # 1%
                elif asset_type.lower() in ["commodity"]:
                    bid_ask_spread = 0.015  # 1.5%
                else:
                    bid_ask_spread = 0.02  # 2%

            # 2. Market Depth (Average Daily Volume)
            if len(volumes) > 0:
                market_depth = volumes.mean()
            else:
                market_depth = 1000000  # Default 1M

            # 3. Price Impact (Amihud illiquidity measure)
            if len(prices) > 1 and len(volumes) > 0:
                returns = prices.pct_change().dropna()
                volumes_aligned = volumes.reindex(returns.index, method="ffill").fillna(
                    1
                )
                price_impact = (
                    abs(returns) / volumes_aligned
                ).mean() * 1e6  # Scale factor
            else:
                price_impact = 0.1  # Default

            # 4. Roll's Convenience Yield
            if len(prices) > 1:
                price_changes = prices.diff().dropna()
                autocov = np.cov(price_changes[:-1], price_changes[1:])[0, 1]
                roll_convenience_yield = 2 * np.sqrt(-autocov) if autocov < 0 else 0
            else:
                roll_convenience_yield = 0.01

            # 5. Amihud Illiquidity
            if len(prices) > 1 and len(volumes) > 0:
                returns = prices.pct_change().dropna()
                volumes_aligned = volumes.reindex(returns.index, method="ffill").fillna(
                    1
                )
                amihud_illiquidity = (abs(returns) / volumes_aligned).mean()
            else:
                amihud_illiquidity = 1e - 6

            # 6. Kyle's Lambda (Price impact coefficient)
            kyle_lambda = price_impact / 1e6  # Simplified calculation

            # 7. Zero Return Days
            if len(prices) > 1:
                returns = prices.pct_change().dropna()
                zero_return_days = (returns == 0).sum() / len(returns)
            else:
                zero_return_days = 0.05

            # 8. Turnover Ratio
            if len(volumes) > 0 and len(prices) > 0:
                avg_volume = volumes.mean()
                avg_price = prices.mean()
                market_cap = (
                    avg_price * avg_volume if position_value == 0 else position_value
                )
                turnover_ratio = avg_volume / market_cap if market_cap > 0 else 0.01
            else:
                turnover_ratio = 0.01

            # 9. Liquidity Score (0 - 100)
            liquidity_score = self._calculate_liquidity_score(
                bid_ask_spread, price_impact, turnover_ratio, zero_return_days
            )

            # 10. Liquidity Class
            liquidity_class = self._classify_liquidity(
                liquidity_score, bid_ask_spread, turnover_ratio
            )

            # 11. Liquidity Adjustment Factor (for L - VaR)
            liquidity_adjustment_factor = self._calculate_liquidity_adjustment_factor(
                liquidity_class, bid_ask_spread, price_impact
            )

            return LiquidityMetrics(
                asset_name = asset_name,
                bid_ask_spread = bid_ask_spread,
                market_depth = market_depth,
                price_impact = price_impact,
                roll_convenience_yield = roll_convenience_yield,
                amihud_illiquidity = amihud_illiquidity,
                kyle_lambda = kyle_lambda,
                zero_return_days = zero_return_days,
                turnover_ratio = turnover_ratio,
                liquidity_score = liquidity_score,
                liquidity_class = liquidity_class,
                liquidity_adjustment_factor = liquidity_adjustment_factor,
            )

        except Exception as e:
            logger.error(f"Liquidity metrics calculation failed for {asset_name}: {e}")
            # Return default metrics
            return LiquidityMetrics(
                asset_name = asset_name,
                bid_ask_spread = 0.02,
                market_depth = 1000000,
                price_impact = 0.1,
                roll_convenience_yield = 0.01,
                amihud_illiquidity = 1e - 6,
                kyle_lambda = 1e - 7,
                zero_return_days = 0.05,
                turnover_ratio = 0.01,
                liquidity_score = 50.0,
                liquidity_class = AssetLiquidityClass.LESS_LIQUID,
                liquidity_adjustment_factor = 1.5,
            )

    def _calculate_liquidity_score(
        self,
        bid_ask_spread: float,
        price_impact: float,
        turnover_ratio: float,
        zero_return_days: float,
    ) -> float:
        """計算流動性評分 (0 - 100)"""
        # Normalize metrics to 0 - 100 scale
        spread_score = max(
            0, 100 - bid_ask_spread * 5000
        )  # Lower spread = higher score
        impact_score = max(0, 100 - price_impact * 1000)  # Lower impact = higher score
        turnover_score = min(
            100, turnover_ratio * 10000
        )  # Higher turnover = higher score
        activity_score = max(
            0, 100 - zero_return_days * 2000
        )  # Fewer zero days = higher score

        # Weighted average
        weights = [0.3, 0.3, 0.25, 0.15]  # Spread, Impact, Turnover, Activity
        scores = [spread_score, impact_score, turnover_score, activity_score]

        liquidity_score = sum(w * s for w, s in zip(weights, scores))
        return min(100, max(0, liquidity_score))

    def _classify_liquidity(
        self, liquidity_score: float, bid_ask_spread: float, turnover_ratio: float
    ) -> AssetLiquidityClass:
        """分類資產流動性等級"""
        if liquidity_score >= 80 and bid_ask_spread < 0.002:
            return AssetLiquidityClass.HIGHLY_LIQUID
        elif liquidity_score >= 60 and bid_ask_spread < 0.005:
            return AssetLiquidityClass.LIQUID
        elif liquidity_score >= 40 and bid_ask_spread < 0.01:
            return AssetLiquidityClass.LESS_LIQUID
        elif liquidity_score >= 20 and bid_ask_spread < 0.02:
            return AssetLiquidityClass.ILLIQUID
        else:
            return AssetLiquidityClass.VERY_ILLIQUID

    def _calculate_liquidity_adjustment_factor(
        self,
        liquidity_class: AssetLiquidityClass,
        bid_ask_spread: float,
        price_impact: float,
    ) -> float:
        """計算流動性調整因子 (用於L - VaR)"""
        base_factors = {
            AssetLiquidityClass.HIGHLY_LIQUID: 1.05,
            AssetLiquidityClass.LIQUID: 1.10,
            AssetLiquidityClass.LESS_LIQUID: 1.25,
            AssetLiquidityClass.ILLIQUID: 1.50,
            AssetLiquidityClass.VERY_ILLIQUID: 2.00,
        }

        base_factor = base_factors.get(liquidity_class, 1.25)

        # Adjust based on specific metrics
        spread_adjustment = 1 + bid_ask_spread * 10  # 10% adjustment per 1% spread
        impact_adjustment = 1 + price_impact * 5  # 5% adjustment per 1% impact

        return base_factor * spread_adjustment * impact_adjustment

    def _analyze_funding_liquidity(
        self, funding_data: Dict[str, Any]
    ) -> List[FundingLiquidityMetrics]:
        """分析融資流動性"""
        funding_metrics = []

        try:
            funding_sources = funding_data.get("funding_sources", [])

            for source in funding_sources:
                funding_metrics.append(
                    FundingLiquidityMetrics(
                        funding_source = source.get("name", "unknown"),
                        funding_amount = source.get("amount", 0),
                        funding_cost = source.get("cost", 0.02),  # Default 2%
                        maturity_profile = source.get("maturity_profile", {}),
                        collateral_requirements = source.get("collateral_ratio", 1.0),
                        renewal_probability = source.get("renewal_probability", 0.8),
                        funding_concentration = source.get("concentration", 0.1),
                        rollover_risk = source.get("rollover_risk", 0.2),
                    )
                )

        except Exception as e:
            logger.error(f"Funding liquidity analysis failed: {e}")
            # Return empty list if analysis fails

        return funding_metrics

    def _calculate_market_liquidity_risk(
        self, liquidity_metrics: Dict[str, LiquidityMetrics]
    ) -> float:
        """計算市場流動性風險評分 (0 - 100)"""
        if not liquidity_metrics:
            return 50.0  # Default medium risk

        total_weight = 0.0
        weighted_risk = 0.0

        for asset_name, metrics in liquidity_metrics.items():
            # Risk score is inverse of liquidity score
            asset_risk = 100 - metrics.liquidity_score
            weight = 1.0  # Equal weight for simplicity

            weighted_risk += asset_risk * weight
            total_weight += weight

        if total_weight > 0:
            market_liquidity_risk = weighted_risk / total_weight
        else:
            market_liquidity_risk = 50.0

        return min(100, max(0, market_liquidity_risk))

    def _calculate_funding_liquidity_risk(
        self, funding_metrics: List[FundingLiquidityMetrics]
    ) -> float:
        """計算融資流動性風險評分 (0 - 100)"""
        if not funding_metrics:
            return 30.0  # Default low risk if no funding data

        risk_factors = []

        for metrics in funding_metrics:
            # Funding cost risk
            cost_risk = min(100, metrics.funding_cost * 2000)  # 2% = 40 points

            # Maturity risk
            short_term_weight = sum(
                amount
                for period, amount in metrics.maturity_profile.items()
                if period in ["1D", "1W", "1M"]
            )
            maturity_risk = min(100, short_term_weight * 100)

            # Concentration risk
            concentration_risk = min(100, metrics.funding_concentration * 200)

            # Rollover risk
            rollover_risk = min(100, (1 - metrics.renewal_probability) * 100)

            # Combined risk for this funding source
            source_risk = np.mean(
                [cost_risk, maturity_risk, concentration_risk, rollover_risk]
            )
            risk_factors.append(source_risk)

        if risk_factors:
            funding_liquidity_risk = np.mean(risk_factors)
        else:
            funding_liquidity_risk = 30.0

        return min(100, max(0, funding_liquidity_risk))

    def _calculate_liquidity_adjusted_var(
        self,
        portfolio_positions: pd.DataFrame,
        liquidity_metrics: Dict[str, LiquidityMetrics],
    ) -> float:
        """計算流動性調整VaR (L - VaR)"""
        try:
            total_portfolio_value = portfolio_positions["market_value"].sum()

            if total_portfolio_value == 0:
                return 0.0

            # Calculate liquidity - adjusted VaR for each position
            total_l_var = 0.0

            for _, position in portfolio_positions.iterrows():
                asset_name = position.get("asset", "unknown")
                position_value = position.get("market_value", 0)
                weight = position_value / total_portfolio_value

                if asset_name in liquidity_metrics:
                    metrics = liquidity_metrics[asset_name]

                    # Simple VaR calculation (would normally use historical VaR)
                    simple_var = weight * 0.02  # Assume 2% daily VaR

                    # Apply liquidity adjustment
                    liquidity_adjustment = metrics.liquidity_adjustment_factor
                    position_l_var = simple_var * liquidity_adjustment

                    total_l_var += position_l_var
                else:
                    # Use default adjustment for unknown assets
                    simple_var = weight * 0.02
                    position_l_var = simple_var * 1.25
                    total_l_var += position_l_var

            return total_l_var * total_portfolio_value

        except Exception as e:
            logger.error(f"Liquidity - adjusted VaR calculation failed: {e}")
            # Fallback to simple calculation
            return portfolio_positions["market_value"].sum() * 0.025  # 2.5% default

    def _calculate_liquidity_coverage_ratio(
        self,
        portfolio_positions: pd.DataFrame,
        market_data: Dict[str, pd.DataFrame],
        funding_data: Optional[Dict[str, Any]] = None,
    ) -> float:
        """計算流動性覆蓋比率 (LCR)"""
        try:
            # LCR = High Quality Liquid Assets / Net Cash Outflows (30 - day horizon)

            # Calculate High Quality Liquid Assets (HQLA)
            hqla = 0.0
            for _, position in portfolio_positions.iterrows():
                asset_type = position.get("asset_type", "").lower()
                market_value = position.get("market_value", 0)

                if asset_type in ["cash", "government_bond"]:
                    hqla += market_value * 1.0  # 100% haircut
                elif asset_type in ["corporate_bond"]:
                    hqla += market_value * 0.8  # 80% haircut
                elif asset_type in ["equity"]:
                    hqla += market_value * 0.5  # 50% haircut
                else:
                    hqla += market_value * 0.3  # 30% haircut for other assets

            # Calculate Net Cash Outflows (30 - day horizon)
            net_outflows = 0.0

            # Funding outflows
            if funding_data:
                funding_sources = funding_data.get("funding_sources", [])
                for source in funding_sources:
                    source.get("amount", 0)
                    maturity_profile = source.get("maturity_profile", {})

                    # Calculate outflows for maturities within 30 days
                    thirty_day_outflows = sum(
                        amount
                        for period, amount in maturity_profile.items()
                        if period in ["1D", "1W", "2W", "1M"]
                    )
                    net_outflows += thirty_day_outflows

            # Add operational expenses (assume 0.1% of portfolio value)
            portfolio_value = portfolio_positions["market_value"].sum()
            operational_expenses = portfolio_value * 0.001
            net_outflows += operational_expenses

            # Calculate LCR
            if net_outflows > 0:
                lcr = hqla / net_outflows
            else:
                lcr = float("inf")  # No outflows, infinite ratio

            return lcr

        except Exception as e:
            logger.error(f"LCR calculation failed: {e}")
            return 1.2  # Default healthy ratio

    def _calculate_net_stable_funding_ratio(
        self,
        portfolio_positions: pd.DataFrame,
        funding_data: Optional[Dict[str, Any]] = None,
    ) -> float:
        """計算潔穩定融資比率 (NSFR)"""
        try:
            # NSFR = Available Stable Funding / Required Stable Funding

            # Calculate Available Stable Funding (ASF)
            asf = 0.0
            if funding_data:
                funding_sources = funding_data.get("funding_sources", [])
                for source in funding_sources:
                    source.get("amount", 0)
                    maturity_profile = source.get("maturity_profile", {})

                    # Calculate ASF based on funding stability
                    stable_funding = 0.0
                    for period, funding_amount in maturity_profile.items():
                        if period in ["1Y", "2Y", "5Y", "10Y"]:
                            stable_funding += funding_amount * 1.0  # 100% ASF factor
                        elif period in ["6M", "9M"]:
                            stable_funding += funding_amount * 0.5  # 50% ASF factor
                        elif period in ["3M"]:
                            stable_funding += funding_amount * 0.0  # 0% ASF factor

                    asf += stable_funding

            # Calculate Required Stable Funding (RSF)
            rsf = 0.0
            for _, position in portfolio_positions.iterrows():
                asset_type = position.get("asset_type", "").lower()
                market_value = position.get("market_value", 0)

                if asset_type in ["cash"]:
                    rsf += market_value * 0.0  # 0% RSF factor
                elif asset_type in ["government_bond"]:
                    rsf += market_value * 0.0  # 0% RSF factor
                elif asset_type in ["corporate_bond"]:
                    rsf += market_value * 0.5  # 50% RSF factor
                elif asset_type in ["equity"]:
                    rsf += market_value * 1.0  # 100% RSF factor
                else:
                    rsf += market_value * 1.0  # 100% RSF factor

            # Calculate NSFR
            if rsf > 0:
                nsfr = asf / rsf
            else:
                nsfr = float("inf")  # No required funding, infinite ratio

            return nsfr

        except Exception as e:
            logger.error(f"NSFR calculation failed: {e}")
            return 1.1  # Default healthy ratio

    def _analyze_cash_flow_gaps(
        self,
        portfolio_positions: pd.DataFrame,
        funding_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, float]:
        """分析現金流缺口"""
        try:
            cash_flow_gaps = {}
            time_buckets = ["1D", "1W", "2W", "1M", "3M", "6M", "1Y"]

            # Initialize gaps
            for bucket in time_buckets:
                cash_flow_gaps[bucket] = 0.0

            # Project cash inflows from assets
            for _, position in portfolio_positions.iterrows():
                asset_type = position.get("asset_type", "").lower()
                market_value = position.get("market_value", 0)

                # Simple projection (would be more sophisticated in practice)
                if asset_type in ["bond", "fixed_income"]:
                    # Assume regular coupon payments
                    cash_flow_gaps["1M"] += market_value * 0.005  # 0.5% monthly
                    cash_flow_gaps["3M"] += market_value * 0.015  # 1.5% quarterly

            # Project cash outflows from funding
            if funding_data:
                funding_sources = funding_data.get("funding_sources", [])
                for source in funding_sources:
                    maturity_profile = source.get("maturity_profile", {})

                    for bucket, amount in maturity_profile.items():
                        if bucket in cash_flow_gaps:
                            cash_flow_gaps[bucket] -= amount  # Outflows are negative

            # Add operational expenses (assume constant rate)
            portfolio_value = portfolio_positions["market_value"].sum()
            daily_expense = portfolio_value * 0.0001  # 0.01% daily

            cash_flow_gaps["1D"] -= daily_expense
            cash_flow_gaps["1W"] -= daily_expense * 7
            cash_flow_gaps["2W"] -= daily_expense * 14
            cash_flow_gaps["1M"] -= daily_expense * 30
            cash_flow_gaps["3M"] -= daily_expense * 90
            cash_flow_gaps["6M"] -= daily_expense * 180
            cash_flow_gaps["1Y"] -= daily_expense * 365

            return cash_flow_gaps

        except Exception as e:
            logger.error(f"Cash flow gap analysis failed: {e}")
            # Return empty gaps
            return {
                bucket: 0.0 for bucket in ["1D", "1W", "2W", "1M", "3M", "6M", "1Y"]
            }

    def _identify_early_warning_indicators(
        self,
        market_liquidity_risk: float,
        funding_liquidity_risk: float,
        lcr: float,
        nsfr: float,
    ) -> List[str]:
        """識別早期預警指標"""
        indicators = []

        if market_liquidity_risk > 80:
            indicators.append("市場流動性風險極高")

        if funding_liquidity_risk > 70:
            indicators.append("融資流動性風險較高")

        if lcr < 0.8:  # Below 80%
            indicators.append("流動性覆蓋比率不足")

        if nsfr < 0.9:  # Below 90%
            indicators.append("潔穩定融資比率偏低")

        # Combined risk indicators
        combined_risk = (market_liquidity_risk + funding_liquidity_risk) / 2
        if combined_risk > self.config["early_warning_threshold"]:
            indicators.append("整體流動性風險超出預警閾值")

        return indicators

    def _calculate_overall_liquidity_risk(
        self,
        market_liquidity_risk: float,
        funding_liquidity_risk: float,
        lcr: float,
        nsfr: float,
    ) -> float:
        """計算整體流動性風險評分 (0 - 100)"""
        # Weight market and funding liquidity risk
        weighted_liquidity_risk = (
            market_liquidity_risk * 0.6 + funding_liquidity_risk * 0.4
        )

        # Adjust based on regulatory ratios
        lcr_adjustment = max(0, (1.0 - lcr) * 50)  # Penalty for low LCR
        nsfr_adjustment = max(0, (1.0 - nsfr) * 30)  # Penalty for low NSFR

        overall_risk = weighted_liquidity_risk + lcr_adjustment + nsfr_adjustment

        return min(100, max(0, overall_risk))

    def _assess_liquidity_risk_level(self, overall_risk: float) -> LiquidityRiskLevel:
        """評估流動性風險等級"""
        if overall_risk < 20:
            return LiquidityRiskLevel.VERY_LOW
        elif overall_risk < 40:
            return LiquidityRiskLevel.LOW
        elif overall_risk < 60:
            return LiquidityRiskLevel.MODERATE
        elif overall_risk < 80:
            return LiquidityRiskLevel.HIGH
        else:
            return LiquidityRiskLevel.VERY_HIGH

    def _generate_liquidity_recommendations(
        self,
        market_liquidity_risk: float,
        funding_liquidity_risk: float,
        lcr: float,
        nsfr: float,
        early_warning_indicators: List[str],
    ) -> List[str]:
        """生成流動性風險管理建議"""
        recommendations = []

        # Market liquidity recommendations
        if market_liquidity_risk > 70:
            recommendations.append("增加高流動性資產配置")
            recommendations.append("減少非流動性資產倉位")
        elif market_liquidity_risk > 50:
            recommendations.append("定期監控市場流動性狀況")

        # Funding liquidity recommendations
        if funding_liquidity_risk > 70:
            recommendations.append("多元化融資來源")
            recommendations.append("延長融資期限結構")
        elif funding_liquidity_risk > 50:
            recommendations.append("建立應急融資計劃")

        # Regulatory ratio recommendations
        if lcr < 1.0:
            recommendations.append("增加高質量流動資產")
            recommendations.append("減少短期資金外流預期")

        if nsfr < 1.0:
            recommendations.append("增加長期穩定資金來源")
            recommendations.append("調整資產負債期限匹配")

        # Early warning specific recommendations
        if early_warning_indicators:
            recommendations.append("密切監控預警指標變化")
            recommendations.append("制定應急流動性管理方案")

        # General recommendations
        if not recommendations:
            recommendations.append("當前流動性狀況良好，維持現有管理策略")
            recommendations.append("定期進行流動性壓力測試")

        return recommendations

    def run_liquidity_stress_test(
        self,
        portfolio_positions: pd.DataFrame,
        market_data: Dict[str, pd.DataFrame],
        funding_data: Optional[Dict[str, Any]] = None,
        stress_scenarios: Optional[List[Dict[str, Any]]] = None,
    ) -> List[LiquidityStressTestResult]:
        """
        運行流動性壓力測試

        評估在壓力情景下的流動性狀況
        """
        try:
            # Default stress scenarios
            if stress_scenarios is None:
                stress_scenarios = [
                    {
                        "name": "Market Crisis",
                        "duration_days": 30,
                        "liquidity_deterioration": 0.5,  # Liquidity worsens by 50%
                        "funding_withdrawal": 0.3,  # 30% funding withdrawal
                        "price_impact_multiplier": 2.0,  # Price impact doubles
                    },
                    {
                        "name": "Credit Crunch",
                        "duration_days": 60,
                        "liquidity_deterioration": 0.7,
                        "funding_withdrawal": 0.5,
                        "price_impact_multiplier": 3.0,
                    },
                    {
                        "name": "Contagion Event",
                        "duration_days": 90,
                        "liquidity_deterioration": 0.6,
                        "funding_withdrawal": 0.4,
                        "price_impact_multiplier": 2.5,
                    },
                ]

            stress_results = []

            for scenario in stress_scenarios:
                result = self._run_single_liquidity_stress_test(
                    portfolio_positions, market_data, funding_data, scenario
                )
                stress_results.append(result)

            return stress_results

        except Exception as e:
            logger.error(f"Liquidity stress test failed: {e}")
            raise

    def _run_single_liquidity_stress_test(
        self,
        portfolio_positions: pd.DataFrame,
        market_data: Dict[str, pd.DataFrame],
        funding_data: Optional[Dict[str, Any]],
        scenario: Dict[str, Any],
    ) -> LiquidityStressTestResult:
        """運行單個流動性壓力測試"""
        try:
            scenario_name = scenario["name"]
            duration_days = scenario["duration_days"]
            liquidity_deterioration = scenario["liquidity_deterioration"]
            funding_withdrawal = scenario["funding_withdrawal"]
            price_impact_multiplier = scenario["price_impact_multiplier"]

            # Calculate liquidity shortfall under stress
            normal_liquidity_metrics = self._analyze_market_liquidity(
                portfolio_positions, market_data
            )
            stressed_liquidity_score = 0

            for asset_name, metrics in normal_liquidity_metrics.items():
                stressed_score = metrics.liquidity_score * (1 - liquidity_deterioration)
                stressed_liquidity_score += stressed_score

            # Calculate funding gap
            funding_gap = 0
            if funding_data:
                total_funding = sum(
                    source.get("amount", 0)
                    for source in funding_data.get("funding_sources", [])
                )
                funding_gap = total_funding * funding_withdrawal

            # Calculate asset fire sale losses
            fire_sale_loss = 0
            for _, position in portfolio_positions.iterrows():
                position_value = position.get("market_value", 0)
                # Simplified fire sale loss calculation
                position_loss = position_value * 0.05 * price_impact_multiplier
                fire_sale_loss += position_loss

            # Calculate additional funding needed
            portfolio_positions["market_value"].sum()
            additional_funding_needed = funding_gap + fire_sale_loss

            # Calculate LVR under stress
            stress_lvr = self._calculate_lvr_under_stress(
                portfolio_positions, scenario, normal_liquidity_metrics
            )

            # Estimate recovery time
            recovery_time = self._estimate_recovery_time_under_stress(scenario)

            # Generate contingency actions
            contingency_actions = self._generate_contingency_actions(
                scenario, funding_gap, fire_sale_loss
            )

            return LiquidityStressTestResult(
                scenario_name = scenario_name,
                stress_duration_days = duration_days,
                liquidity_shortfall = stressed_liquidity_score,
                funding_gap = funding_gap,
                asset_fire_sale_loss = fire_sale_loss,
                additional_funding_needed = additional_funding_needed,
                lvr_under_stress = stress_lvr,
                recovery_time_days = recovery_time,
                contingency_actions = contingency_actions,
            )

        except Exception as e:
            logger.error(
                f"Single liquidity stress test failed for {scenario.get('name', 'unknown')}: {e}"
            )
            raise

    def _calculate_lvr_under_stress(
        self,
        portfolio_positions: pd.DataFrame,
        scenario: Dict[str, Any],
        liquidity_metrics: Dict[str, LiquidityMetrics],
    ) -> float:
        """計算壓力下的流動性調整VaR比率"""
        try:
            # Simplified LVR calculation under stress
            portfolio_value = portfolio_positions["market_value"].sum()

            if portfolio_value == 0:
                return 0.0

            # Calculate stressed liquidity adjustment factors
            stressed_l_var = 0
            liquidity_deterioration = scenario["liquidity_deterioration"]
            price_impact_multiplier = scenario["price_impact_multiplier"]

            for _, position in portfolio_positions.iterrows():
                asset_name = position.get("asset", "unknown")
                position_value = position.get("market_value", 0)
                weight = position_value / portfolio_value

                if asset_name in liquidity_metrics:
                    metrics = liquidity_metrics[asset_name]

                    # Adjust liquidity adjustment factor for stress
                    base_laf = metrics.liquidity_adjustment_factor
                    stressed_laf = (
                        base_laf
                        * (1 + liquidity_deterioration)
                        * price_impact_multiplier
                    )

                    # Calculate stressed position VaR
                    stressed_position_var = weight * 0.02 * stressed_laf  # 2% base VaR
                    stressed_l_var += stressed_position_var
                else:
                    # Use stressed default factor
                    stressed_position_var = weight * 0.02 * 2.0
                    stressed_l_var += stressed_position_var

            return stressed_l_var

        except Exception as e:
            logger.error(f"Stress LVR calculation failed: {e}")
            return 0.05  # Default 5% LVR

    def _estimate_recovery_time_under_stress(self, scenario: Dict[str, Any]) -> int:
        """估算壓力下的恢復時間"""
        # Simplified recovery time estimation
        base_recovery_time = scenario.get("duration_days", 30)
        liquidity_deterioration = scenario.get("liquidity_deterioration", 0.5)

        # Recovery time increases with liquidity deterioration
        recovery_multiplier = 1 + liquidity_deterioration
        recovery_time = int(base_recovery_time * recovery_multiplier)

        return min(recovery_time, 365)  # Cap at 1 year

    def _generate_contingency_actions(
        self, scenario: Dict[str, Any], funding_gap: float, fire_sale_loss: float
    ) -> List[str]:
        """生成應急行動建議"""
        actions = []

        if funding_gap > 0:
            actions.append("啟動應急融資安排")
            actions.append("動用流動性緩沖")

        if fire_sale_loss > 0:
            actions.append("有序處置非核心資產")
            assets.append("尋求資產抵押融資")

        if scenario.get("duration_days", 30) > 60:
            actions.append("實施業務連續性計劃")
            actions.append("與監管機構保持溝通")

        # General contingency actions
        actions.extend(
            [
                "加強現金流監控",
                "評估資產負債匹配",
                "審視投資組合策略",
                "準備投資者溝通材料",
            ]
        )

        return list(set(actions))  # Remove duplicates


# 便利函數
def quick_liquidity_assessment(
    portfolio_value: float,
    bid_ask_spreads: Dict[str, float],
    daily_volumes: Dict[str, float],
) -> Dict[str, Any]:
    """便利函數：快速流動性評估"""
    analyzer = LiquidityRiskAnalyzer()

    # Create simple portfolio positions
    positions = pd.DataFrame(
        [
            {"asset": asset, "market_value": value}
            for asset, value in daily_volumes.items()
        ]
    )

    # Create simple market data
    market_data = {}
    for asset in daily_volumes.keys():
        market_data[asset] = pd.DataFrame(
            {"close": [100] * 10, "volume": [daily_volumes.get(asset, 1000000)] * 10}
        )

    # Quick analysis
    result = analyzer.analyze_liquidity_risk(positions, market_data)

    return {
        "overall_liquidity_risk": result.overall_liquidity_risk,
        "liquidity_coverage_ratio": result.liquidity_coverage_ratio,
        "risk_level": result.risk_level.value,
        "key_recommendations": result.recommendations[:3],  # Top 3 recommendations
    }

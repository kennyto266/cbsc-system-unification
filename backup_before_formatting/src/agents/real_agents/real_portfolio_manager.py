"""Real Portfolio Manager Agent for Hong Kong quantitative trading system.

This agent manages investment portfolios with dynamic asset allocation, risk budgeting,
and performance optimization based on real market data and trading results.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field
from scipy.optimize import minimize

from ...data_adapters.base_adapter import RealMarketData
from .base_real_agent import BaseRealAgent, RealAgentConfig, RealAgentStatus
from .ml_integration import MLModelManager, ModelType
from .real_data_analyzer import AnalysisResult, SignalStrength


class AssetClass(str, Enum):
    """Asset class categories."""

    EQUITY = "equity"
    BOND = "bond"
    COMMODITY = "commodity"
    CURRENCY = "currency"
    ALTERNATIVE = "alternative"
    CASH = "cash"


class OptimizationMethod(str, Enum):
    """Portfolio optimization methods."""

    MEAN_VARIANCE = "mean_variance"
    RISK_PARITY = "risk_parity"
    MAX_SHARPE = "max_sharpe"
    MIN_VARIANCE = "min_variance"
    BLACK_LITTERMAN = "black_litterman"
    EQUAL_WEIGHT = "equal_weight"


class RebalanceTrigger(str, Enum):
    """Portfolio rebalancing triggers."""

    TIME_BASED = "time_based"
    DRIFT_BASED = "drift_based"
    VOLATILITY_BASED = "volatility_based"
    CORRELATION_BASED = "correlation_based"
    PERFORMANCE_BASED = "performance_based"
    RISK_BUDGET_BASED = "risk_budget_based"


class Asset(BaseModel):
    """Asset model for portfolio management."""

    symbol: str = Field(..., description="Asset symbol")
    name: str = Field(..., description="Asset name")
    asset_class: AssetClass = Field(..., description="Asset class")

    # Current position
    current_weight: float = Field(
        0.0, ge=0.0, le=1.0, description="Current portfolio weight"
    )
    target_weight: float = Field(
        0.0, ge=0.0, le=1.0, description="Target portfolio weight"
    )
    quantity: float = Field(0.0, description="Current quantity held")
    market_value: float = Field(0.0, description="Current market value")

    # Performance metrics
    expected_return: float = Field(0.0, description="Expected return")
    volatility: float = Field(0.0, description="Asset volatility")
    sharpe_ratio: float = Field(0.0, description="Sharpe ratio")

    # Risk metrics
    var_95: float = Field(0.0, description="95% Value at Risk")
    beta: float = Field(1.0, description="Beta coefficient")
    correlation_with_portfolio: float = Field(
        0.0, description="Correlation with portfolio"
    )

    # Metadata
    last_updated: datetime = Field(
        default_factory=datetime.now, description="Last update time"
    )

    class Config:
        use_enum_values = True


class RiskBudget(BaseModel):
    """Risk budget model."""

    asset_class: AssetClass = Field(..., description="Asset class")
    risk_budget: float = Field(
        ..., ge=0.0, le=1.0, description="Risk budget allocation"
    )
    current_risk_contribution: float = Field(
        0.0, ge=0.0, description="Current risk contribution"
    )
    risk_limit: float = Field(0.5, ge=0.0, le=1.0, description="Risk limit")

    # Dynamic adjustment
    volatility_adjustment: float = Field(
        1.0, ge=0.1, le=3.0, description="Volatility adjustment factor"
    )
    correlation_adjustment: float = Field(
        1.0, ge=0.1, le=3.0, description="Correlation adjustment factor"
    )

    class Config:
        use_enum_values = True


class Portfolio(BaseModel):
    """Portfolio model."""

    portfolio_id: str = Field(..., description="Portfolio identifier")
    name: str = Field(..., description="Portfolio name")

    # Assets
    assets: Dict[str, Asset] = Field(
        default_factory=dict, description="Portfolio assets"
    )
    asset_classes: Dict[AssetClass, List[str]] = Field(
        default_factory=dict, description="Assets by class"
    )

    # Portfolio metrics
    total_value: float = Field(0.0, description="Total portfolio value")
    total_return: float = Field(0.0, description="Total return")
    volatility: float = Field(0.0, description="Portfolio volatility")
    sharpe_ratio: float = Field(0.0, description="Portfolio Sharpe ratio")
    max_drawdown: float = Field(0.0, description="Maximum drawdown")

    # Risk metrics
    portfolio_var_95: float = Field(0.0, description="Portfolio 95% VaR")
    portfolio_var_99: float = Field(0.0, description="Portfolio 99% VaR")
    beta: float = Field(1.0, description="Portfolio beta")

    # Risk budget
    risk_budgets: Dict[AssetClass, RiskBudget] = Field(
        default_factory=dict, description="Risk budgets by asset class"
    )

    # Rebalancing
    last_rebalance: Optional[datetime] = Field(
        None, description="Last rebalancing time"
    )
    rebalance_frequency: int = Field(30, description="Rebalancing frequency in days")
    rebalance_threshold: float = Field(0.05, description="Rebalancing threshold")

    # Performance tracking
    benchmark_return: float = Field(0.0, description="Benchmark return")
    tracking_error: float = Field(0.0, description="Tracking error")
    information_ratio: float = Field(0.0, description="Information ratio")

    class Config:
        arbitrary_types_allowed = True


class RebalanceDecision(BaseModel):
    """Rebalancing decision model."""

    decision_id: str = Field(..., description="Decision identifier")
    portfolio_id: str = Field(..., description="Portfolio identifier")
    trigger: RebalanceTrigger = Field(..., description="Rebalancing trigger")

    # Rebalancing actions
    trades: List[Dict[str, Any]] = Field(
        default_factory=list, description="Required trades"
    )
    total_trades: int = Field(0, description="Total number of trades")
    estimated_cost: float = Field(0.0, description="Estimated transaction costs")

    # Expected impact
    expected_return_improvement: float = Field(
        0.0, description="Expected return improvement"
    )
    risk_reduction: float = Field(0.0, description="Expected risk reduction")

    # Decision metadata
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Decision confidence")
    reasoning: str = Field(..., description="Decision reasoning")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Decision time"
    )

    class Config:
        use_enum_values = True


class RealPortfolioManager(BaseRealAgent):
    """Real Portfolio Manager Agent with advanced portfolio optimization capabilities."""

    def __init__(self, config: RealAgentConfig):
        super().__init__(config)
        self.ml_manager = MLModelManager(config)

        # Portfolio management components
        self.portfolios: Dict[str, Portfolio] = {}
        self.optimization_models: Dict[str, Any] = {}
        self.rebalance_history: List[RebalanceDecision] = []

        # Optimization parameters
        self.optimization_method = OptimizationMethod.RISK_PARITY
        self.rebalance_triggers = [
            RebalanceTrigger.TIME_BASED,
            RebalanceTrigger.DRIFT_BASED,
        ]
        self.transaction_cost_rate = 0.001  # 0.1% transaction cost
        self.risk_free_rate = 0.02  # 2% risk - free rate

        # Performance tracking
        self.performance_history: List[Dict[str, Any]] = []
        self.optimization_history: List[Dict[str, Any]] = []

    async def _initialize_specific(self) -> bool:
        """Initialize portfolio manager specific components."""
        try:
            self.logger.info("Initializing portfolio manager specific components...")

            # Initialize ML model manager
            if not await self.ml_manager.initialize():
                self.logger.error("Failed to initialize ML model manager")
                return False

            # Initialize optimization models
            await self._initialize_optimization_models()

            # Create default portfolio
            await self._create_default_portfolio()

            # Initialize risk budgets
            await self._initialize_risk_budgets()

            self.logger.info("Portfolio manager initialization completed")
            return True

        except Exception as e:
            self.logger.exception(f"Failed to initialize portfolio manager: {e}")
            return False

    async def _initialize_optimization_models(self) -> None:
        """Initialize portfolio optimization models."""
        try:
            # Initialize different optimization approaches
            self.optimization_models = {
                "mean_variance": self._mean_variance_optimizer,
                "risk_parity": self._risk_parity_optimizer,
                "max_sharpe": self._max_sharpe_optimizer,
                "min_variance": self._min_variance_optimizer,
                "black_litterman": self._black_litterman_optimizer,
            }

            self.logger.info("Portfolio optimization models initialized")

        except Exception as e:
            self.logger.error(f"Error initializing optimization models: {e}")

    async def _create_default_portfolio(self) -> None:
        """Create default portfolio for Hong Kong market."""
        try:
            # Create default Hong Kong equity portfolio
            default_assets = {
                "0700.HK": Asset(
                    symbol="0700.HK",
                    name="腾讯控股",
                    asset_class=AssetClass.EQUITY,
                    current_weight=0.0,
                    target_weight=0.15,
                ),
                "0005.HK": Asset(
                    symbol="0005.HK",
                    name="汇丰控股",
                    asset_class=AssetClass.EQUITY,
                    current_weight=0.0,
                    target_weight=0.12,
                ),
                "1299.HK": Asset(
                    symbol="1299.HK",
                    name="友邦保险",
                    asset_class=AssetClass.EQUITY,
                    current_weight=0.0,
                    target_weight=0.10,
                ),
                "2800.HK": Asset(
                    symbol="2800.HK",
                    name="盈富基金",
                    asset_class=AssetClass.EQUITY,
                    current_weight=0.0,
                    target_weight=0.25,
                ),
                "CASH": Asset(
                    symbol="CASH",
                    name="现金",
                    asset_class=AssetClass.CASH,
                    current_weight=0.0,
                    target_weight=0.38,
                ),
            }

            # Group assets by class
            asset_classes = {
                AssetClass.EQUITY: ["0700.HK", "0005.HK", "1299.HK", "2800.HK"],
                AssetClass.CASH: ["CASH"],
            }

            # Create risk budgets
            risk_budgets = {
                AssetClass.EQUITY: RiskBudget(
                    asset_class=AssetClass.EQUITY, risk_budget=0.8, risk_limit=0.6
                ),
                AssetClass.CASH: RiskBudget(
                    asset_class=AssetClass.CASH, risk_budget=0.2, risk_limit=0.4
                ),
            }

            portfolio = Portfolio(
                portfolio_id="hk_equity_portfolio",
                name="香港股票投资组合",
                assets=default_assets,
                asset_classes=asset_classes,
                total_value=1000000.0,  # 1M HKD starting value
                risk_budgets=risk_budgets,
                rebalance_frequency=30,
                rebalance_threshold=0.05,
            )

            self.portfolios["hk_equity_portfolio"] = portfolio
            self.logger.info("Default Hong Kong equity portfolio created")

        except Exception as e:
            self.logger.error(f"Error creating default portfolio: {e}")

    async def _initialize_risk_budgets(self) -> None:
        """Initialize risk budgets for different asset classes."""
        try:
            # Default risk budget allocation
            default_risk_budgets = {
                AssetClass.EQUITY: 0.6,  # 60% risk budget for equities
                AssetClass.BOND: 0.2,  # 20% risk budget for bonds
                AssetClass.COMMODITY: 0.1,  # 10% risk budget for commodities
                AssetClass.ALTERNATIVE: 0.05,  # 5% risk budget for alternatives
                AssetClass.CASH: 0.05,  # 5% risk budget for cash
            }

            for portfolio in self.portfolios.values():
                for asset_class, risk_budget in default_risk_budgets.items():
                    if asset_class not in portfolio.risk_budgets:
                        portfolio.risk_budgets[asset_class] = RiskBudget(
                            asset_class=asset_class, risk_budget=risk_budget
                        )

            self.logger.info("Risk budgets initialized")

        except Exception as e:
            self.logger.error(f"Error initializing risk budgets: {e}")

    async def _enhance_analysis(
        self, base_result: AnalysisResult, market_data: List[RealMarketData]
    ) -> AnalysisResult:
        """Enhance analysis with portfolio management specific logic."""
        try:
            # Calculate portfolio - specific metrics
            portfolio_metrics = await self._calculate_portfolio_metrics(market_data)

            # Update base result
            enhanced_result = base_result.copy()

            # Add portfolio insights
            portfolio_insights = await self._generate_portfolio_insights(
                portfolio_metrics, enhanced_result
            )
            enhanced_result.insights.extend(portfolio_insights)

            return enhanced_result

        except Exception as e:
            self.logger.error(f"Error enhancing analysis for portfolio management: {e}")
            return base_result

    async def _calculate_portfolio_metrics(
        self, market_data: List[RealMarketData]
    ) -> Dict[str, Any]:
        """Calculate portfolio - specific metrics."""
        try:
            metrics = {}

            # Update portfolio asset prices
            for portfolio in self.portfolios.values():
                portfolio_metrics = await self._update_portfolio_asset_prices(
                    portfolio, market_data
                )
                metrics[portfolio.portfolio_id] = portfolio_metrics

            return metrics

        except Exception as e:
            self.logger.error(f"Error calculating portfolio metrics: {e}")
            return {}

    async def _update_portfolio_asset_prices(
        self, portfolio: Portfolio, market_data: List[RealMarketData]
    ) -> Dict[str, Any]:
        """Update portfolio asset prices and calculate metrics."""
        try:
            # Create price lookup
            price_lookup = {
                data.symbol: float(data.close_price) for data in market_data
            }

            portfolio_metrics = {
                "total_value": 0.0,
                "total_return": 0.0,
                "volatility": 0.0,
                "asset_metrics": {},
            }

            # Update each asset
            for symbol, asset in portfolio.assets.items():
                if symbol in price_lookup:
                    asset.market_value = asset.quantity * price_lookup[symbol]
                    portfolio_metrics["total_value"] += asset.market_value

                    # Calculate asset metrics
                    if asset.quantity > 0:
                        asset.current_weight = (
                            asset.market_value / portfolio.total_value
                            if portfolio.total_value > 0
                            else 0
                        )

                        # Calculate returns (simplified)
                        asset.expected_return = np.random.normal(
                            0.08, 0.2
                        )  # Placeholder
                        asset.volatility = np.random.uniform(0.15, 0.35)  # Placeholder
                        asset.sharpe_ratio = (
                            asset.expected_return / asset.volatility
                            if asset.volatility > 0
                            else 0
                        )

                        portfolio_metrics["asset_metrics"][symbol] = {
                            "weight": asset.current_weight,
                            "expected_return": asset.expected_return,
                            "volatility": asset.volatility,
                            "sharpe_ratio": asset.sharpe_ratio,
                        }

            # Calculate portfolio - level metrics
            portfolio.total_value = portfolio_metrics["total_value"]

            # Calculate portfolio volatility (simplified)
            weights = [asset.current_weight for asset in portfolio.assets.values()]
            volatilities = [asset.volatility for asset in portfolio.assets.values()]

            if weights and volatilities:
                # Simplified portfolio volatility calculation
                portfolio.volatility = np.sqrt(
                    sum(w ** 2 * v ** 2 for w, v in zip(weights, volatilities))
                )
                portfolio.sharpe_ratio = (
                    sum(
                        w * asset.expected_return
                        for w, asset in zip(weights, portfolio.assets.values())
                    )
                    / portfolio.volatility
                    if portfolio.volatility > 0
                    else 0
                )

            return portfolio_metrics

        except Exception as e:
            self.logger.error(f"Error updating portfolio asset prices: {e}")
            return {}

    async def _generate_portfolio_insights(
        self, portfolio_metrics: Dict[str, Any], analysis_result: AnalysisResult
    ) -> List[str]:
        """Generate portfolio - specific insights."""
        try:
            insights = []

            for portfolio_id, metrics in portfolio_metrics.items():
                portfolio = self.portfolios.get(portfolio_id)
                if not portfolio:
                    continue

                # Portfolio value insights
                total_value = metrics.get("total_value", 0)
                if total_value > 0:
                    insights.append(f"{portfolio.name}: 总价值 {total_value:,.0f} 港元")

                # Weight drift insights
                weight_drift = await self._calculate_weight_drift(portfolio)
                if weight_drift > portfolio.rebalance_threshold:
                    insights.append(
                        f"{portfolio.name}: 权重偏离超过阈值 {weight_drift:.1%}"
                    )

                # Risk budget insights
                risk_budget_violations = await self._check_risk_budget_violations(
                    portfolio
                )
                if risk_budget_violations:
                    insights.append(
                        f"{portfolio.name}: 风险预算违规 - {', '.join(risk_budget_violations)}"
                    )

                # Performance insights
                if portfolio.sharpe_ratio > 1.0:
                    insights.append(
                        f"{portfolio.name}: 夏普比率优秀 {portfolio.sharpe_ratio:.2f}"
                    )
                elif portfolio.sharpe_ratio < 0.5:
                    insights.append(
                        f"{portfolio.name}: 夏普比率偏低 {portfolio.sharpe_ratio:.2f}"
                    )

            return insights

        except Exception as e:
            self.logger.error(f"Error generating portfolio insights: {e}")
            return []

    async def _calculate_weight_drift(self, portfolio: Portfolio) -> float:
        """Calculate weight drift from target allocation."""
        try:
            total_drift = 0.0

            for asset in portfolio.assets.values():
                weight_drift = abs(asset.current_weight - asset.target_weight)
                total_drift += weight_drift

            return total_drift / 2.0  # Normalize by 2

        except Exception as e:
            self.logger.error(f"Error calculating weight drift: {e}")
            return 0.0

    async def _check_risk_budget_violations(self, portfolio: Portfolio) -> List[str]:
        """Check for risk budget violations."""
        try:
            violations = []

            for asset_class, risk_budget in portfolio.risk_budgets.items():
                current_risk = risk_budget.current_risk_contribution
                risk_limit = risk_budget.risk_limit

                if current_risk > risk_limit:
                    violations.append(
                        f"{asset_class.value} 风险贡献 {current_risk:.1%} > 限制 {risk_limit:.1%}"
                    )

            return violations

        except Exception as e:
            self.logger.error(f"Error checking risk budget violations: {e}")
            return []

    async def _enhance_signals(
        self, base_signals: List[Dict[str, Any]], analysis_result: AnalysisResult
    ) -> List[Dict[str, Any]]:
        """Enhance signals with portfolio management logic."""
        try:
            enhanced_signals = []

            # Check for rebalancing opportunities
            rebalance_signals = await self._generate_rebalance_signals(analysis_result)
            enhanced_signals.extend(rebalance_signals)

            # Check for optimization opportunities
            optimization_signals = await self._generate_optimization_signals(
                analysis_result
            )
            enhanced_signals.extend(optimization_signals)

            return enhanced_signals

        except Exception as e:
            self.logger.error(f"Error enhancing signals for portfolio management: {e}")
            return base_signals

    async def _generate_rebalance_signals(
        self, analysis_result: AnalysisResult
    ) -> List[Dict[str, Any]]:
        """Generate rebalancing signals."""
        try:
            rebalance_signals = []

            for portfolio in self.portfolios.values():
                # Check time - based rebalancing
                if self._should_rebalance_time_based(portfolio):
                    signal = {
                        "signal_id": f"rebalance_time_{portfolio.portfolio_id}_{datetime.now().strftime('%Y % m % d_ % H % M % S')}",
                        "symbol": portfolio.portfolio_id,
                        "side": "rebalance",
                        "strength": 0.8,
                        "confidence": 0.9,
                        "reasoning": f"定期再平衡触发 - {portfolio.name}",
                        "portfolio_id": portfolio.portfolio_id,
                        "signal_type": "rebalance",
                        "trigger": RebalanceTrigger.TIME_BASED,
                    }
                    rebalance_signals.append(signal)

                # Check drift - based rebalancing
                weight_drift = await self._calculate_weight_drift(portfolio)
                if weight_drift > portfolio.rebalance_threshold:
                    signal = {
                        "signal_id": f"rebalance_drift_{portfolio.portfolio_id}_{datetime.now().strftime('%Y % m % d_ % H % M % S')}",
                        "symbol": portfolio.portfolio_id,
                        "side": "rebalance",
                        "strength": min(weight_drift * 2, 1.0),
                        "confidence": 0.8,
                        "reasoning": f"权重偏离触发再平衡 - {portfolio.name} 偏离度 {weight_drift:.1%}",
                        "portfolio_id": portfolio.portfolio_id,
                        "signal_type": "rebalance",
                        "trigger": RebalanceTrigger.DRIFT_BASED,
                    }
                    rebalance_signals.append(signal)

                # Check risk budget violations
                risk_violations = await self._check_risk_budget_violations(portfolio)
                if risk_violations:
                    signal = {
                        "signal_id": f"rebalance_risk_{portfolio.portfolio_id}_{datetime.now().strftime('%Y % m % d_ % H % M % S')}",
                        "symbol": portfolio.portfolio_id,
                        "side": "rebalance",
                        "strength": 0.9,
                        "confidence": 0.95,
                        "reasoning": f"风险预算违规触发再平衡 - {portfolio.name}",
                        "portfolio_id": portfolio.portfolio_id,
                        "signal_type": "rebalance",
                        "trigger": RebalanceTrigger.RISK_BUDGET_BASED,
                    }
                    rebalance_signals.append(signal)

            return rebalance_signals

        except Exception as e:
            self.logger.error(f"Error generating rebalance signals: {e}")
            return []

    async def _generate_optimization_signals(
        self, analysis_result: AnalysisResult
    ) -> List[Dict[str, Any]]:
        """Generate portfolio optimization signals."""
        try:
            optimization_signals = []

            for portfolio in self.portfolios.values():
                # Check if optimization is needed
                if await self._should_optimize_portfolio(portfolio, analysis_result):
                    signal = {
                        "signal_id": f"optimize_{portfolio.portfolio_id}_{datetime.now().strftime('%Y % m % d_ % H % M % S')}",
                        "symbol": portfolio.portfolio_id,
                        "side": "optimize",
                        "strength": 0.7,
                        "confidence": 0.8,
                        "reasoning": f"投资组合优化机会 - {portfolio.name} 夏普比率 {portfolio.sharpe_ratio:.2f}",
                        "portfolio_id": portfolio.portfolio_id,
                        "signal_type": "optimization",
                        "optimization_method": self.optimization_method,
                    }
                    optimization_signals.append(signal)

            return optimization_signals

        except Exception as e:
            self.logger.error(f"Error generating optimization signals: {e}")
            return []

    def _should_rebalance_time_based(self, portfolio: Portfolio) -> bool:
        """Check if time - based rebalancing is needed."""
        if not portfolio.last_rebalance:
            return True

        days_since_rebalance = (datetime.now() - portfolio.last_rebalance).days
        return days_since_rebalance >= portfolio.rebalance_frequency

    async def _should_optimize_portfolio(
        self, portfolio: Portfolio, analysis_result: AnalysisResult
    ) -> bool:
        """Check if portfolio optimization is needed."""
        try:
            # Check Sharpe ratio threshold
            if portfolio.sharpe_ratio < 0.5:
                return True

            # Check volatility threshold
            if portfolio.volatility > 0.25:
                return True

            # Check market regime changes
            market_regime = analysis_result.market_regime.regime_type
            if market_regime in ["high_volatility", "bear_market"]:
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error checking optimization need: {e}")
            return False

    async def _execute_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Execute portfolio management signal."""
        try:
            signal_type = signal.get("signal_type", "")

            if signal_type == "rebalance":
                return await self._execute_rebalance_signal(signal)
            elif signal_type == "optimization":
                return await self._execute_optimization_signal(signal)
            else:
                return {
                    "signal_id": signal.get("signal_id", "unknown"),
                    "status": "ignored",
                    "reason": f"Unknown signal type: {signal_type}",
                }

        except Exception as e:
            self.logger.error(f"Error executing portfolio signal: {e}")
            return {
                "signal_id": signal.get("signal_id", "unknown"),
                "status": "failed",
                "error": str(e),
            }

    async def _execute_rebalance_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Execute rebalancing signal."""
        try:
            portfolio_id = signal.get("portfolio_id", "")
            portfolio = self.portfolios.get(portfolio_id)

            if not portfolio:
                return {
                    "signal_id": signal.get("signal_id", "unknown"),
                    "status": "failed",
                    "reason": f"Portfolio not found: {portfolio_id}",
                }

            # Create rebalance decision
            decision = await self._create_rebalance_decision(portfolio, signal)

            # Execute rebalancing trades
            execution_result = await self._execute_rebalancing_trades(
                portfolio, decision
            )

            # Update portfolio
            if execution_result["status"] == "success":
                portfolio.last_rebalance = datetime.now()
                self.rebalance_history.append(decision)

                self.logger.info(f"Portfolio rebalanced: {portfolio.name}")

            return execution_result

        except Exception as e:
            self.logger.error(f"Error executing rebalance signal: {e}")
            return {
                "signal_id": signal.get("signal_id", "unknown"),
                "status": "failed",
                "error": str(e),
            }

    async def _execute_optimization_signal(
        self, signal: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute portfolio optimization signal."""
        try:
            portfolio_id = signal.get("portfolio_id", "")
            portfolio = self.portfolios.get(portfolio_id)

            if not portfolio:
                return {
                    "signal_id": signal.get("signal_id", "unknown"),
                    "status": "failed",
                    "reason": f"Portfolio not found: {portfolio_id}",
                }

            # Perform optimization
            optimization_result = await self._optimize_portfolio(portfolio)

            # Apply optimization if successful
            if optimization_result["success"]:
                await self._apply_portfolio_optimization(portfolio, optimization_result)

                self.logger.info(f"Portfolio optimized: {portfolio.name}")

                return {
                    "signal_id": signal.get("signal_id", "unknown"),
                    "status": "success",
                    "optimization_result": optimization_result,
                }
            else:
                return {
                    "signal_id": signal.get("signal_id", "unknown"),
                    "status": "failed",
                    "reason": optimization_result.get("error", "Optimization failed"),
                }

        except Exception as e:
            self.logger.error(f"Error executing optimization signal: {e}")
            return {
                "signal_id": signal.get("signal_id", "unknown"),
                "status": "failed",
                "error": str(e),
            }

    async def _create_rebalance_decision(
        self, portfolio: Portfolio, signal: Dict[str, Any]
    ) -> RebalanceDecision:
        """Create rebalancing decision."""
        try:
            decision_id = (
                f"rebalance_decision_{datetime.now().strftime('%Y % m % d_ % H % M % S')}"
            )
            trigger = RebalanceTrigger(signal.get("trigger", "time_based"))

            # Calculate required trades
            trades = []
            total_cost = 0.0

            for symbol, asset in portfolio.assets.items():
                current_weight = asset.current_weight
                target_weight = asset.target_weight
                weight_diff = target_weight - current_weight

                if abs(weight_diff) > 0.01:  # 1% threshold
                    trade_value = weight_diff * portfolio.total_value
                    trade_cost = abs(trade_value) * self.transaction_cost_rate

                    trades.append(
                        {
                            "symbol": symbol,
                            "action": "buy" if weight_diff > 0 else "sell",
                            "value": trade_value,
                            "weight_change": weight_diff,
                            "cost": trade_cost,
                        }
                    )

                    total_cost += trade_cost

            decision = RebalanceDecision(
                decision_id=decision_id,
                portfolio_id=portfolio.portfolio_id,
                trigger=trigger,
                trades=trades,
                total_trades=len(trades),
                estimated_cost=total_cost,
                confidence=signal.get("confidence", 0.8),
                reasoning=signal.get("reasoning", "Portfolio rebalancing"),
            )

            return decision

        except Exception as e:
            self.logger.error(f"Error creating rebalance decision: {e}")
            raise

    async def _execute_rebalancing_trades(
        self, portfolio: Portfolio, decision: RebalanceDecision
    ) -> Dict[str, Any]:
        """Execute rebalancing trades."""
        try:
            # Simulate trade execution
            executed_trades = []
            total_cost = 0.0

            for trade in decision.trades:
                # Update asset weights
                symbol = trade["symbol"]
                weight_change = trade["weight_change"]

                if symbol in portfolio.assets:
                    asset = portfolio.assets[symbol]
                    asset.current_weight = asset.target_weight
                    asset.quantity = (
                        asset.quantity * (1 + weight_change / asset.current_weight)
                        if asset.current_weight > 0
                        else 0
                    )

                    executed_trades.append(
                        {
                            "symbol": symbol,
                            "weight_change": weight_change,
                            "new_weight": asset.current_weight,
                            "cost": trade["cost"],
                        }
                    )

                    total_cost += trade["cost"]

            return {
                "status": "success",
                "decision_id": decision.decision_id,
                "executed_trades": executed_trades,
                "total_cost": total_cost,
                "execution_time": datetime.now(),
            }

        except Exception as e:
            self.logger.error(f"Error executing rebalancing trades: {e}")
            return {"status": "failed", "error": str(e)}

    async def _optimize_portfolio(self, portfolio: Portfolio) -> Dict[str, Any]:
        """Optimize portfolio allocation."""
        try:
            # Get optimization method
            optimizer = self.optimization_models.get(self.optimization_method.value)
            if not optimizer:
                return {
                    "success": False,
                    "error": f"Unknown optimization method: {self.optimization_method}",
                }

            # Prepare optimization data
            symbols = list(portfolio.assets.keys())
            returns = np.array(
                [asset.expected_return for asset in portfolio.assets.values()]
            )
            cov_matrix = self._calculate_covariance_matrix(portfolio)

            # Run optimization
            optimal_weights = await optimizer(returns, cov_matrix, symbols)

            if optimal_weights is not None:
                # Calculate expected improvement
                current_return = sum(
                    asset.current_weight * asset.expected_return
                    for asset in portfolio.assets.values()
                )
                optimal_return = sum(w * r for w, r in zip(optimal_weights, returns))

                return {
                    "success": True,
                    "optimal_weights": dict(zip(symbols, optimal_weights)),
                    "expected_return_improvement": optimal_return - current_return,
                    "method": self.optimization_method.value,
                }
            else:
                return {"success": False, "error": "Optimization failed to converge"}

        except Exception as e:
            self.logger.error(f"Error optimizing portfolio: {e}")
            return {"success": False, "error": str(e)}

    def _calculate_covariance_matrix(self, portfolio: Portfolio) -> np.ndarray:
        """Calculate covariance matrix for portfolio assets."""
        try:
            n_assets = len(portfolio.assets)
            cov_matrix = np.eye(n_assets) * 0.01  # Base diagonal covariance

            # Add some correlation structure (simplified)
            for i in range(n_assets):
                for j in range(i + 1, n_assets):
                    correlation = np.random.uniform(0.1, 0.7)
                    vol_i = list(portfolio.assets.values())[i].volatility
                    vol_j = list(portfolio.assets.values())[j].volatility
                    cov_matrix[i, j] = cov_matrix[j, i] = correlation * vol_i * vol_j

            return cov_matrix

        except Exception as e:
            self.logger.error(f"Error calculating covariance matrix: {e}")
            return np.eye(len(portfolio.assets)) * 0.01

    async def _mean_variance_optimizer(
        self, returns: np.ndarray, cov_matrix: np.ndarray, symbols: List[str]
    ) -> Optional[np.ndarray]:
        """Mean - variance optimization."""
        try:
            n_assets = len(returns)

            # Objective function: maximize Sharpe ratio
            def objective(weights):
                portfolio_return = np.dot(weights, returns)
                portfolio_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
                return (
                    -(portfolio_return - self.risk_free_rate) / portfolio_vol
                    if portfolio_vol > 0
                    else -1000
                )

            # Constraints: weights sum to 1
            constraints = {"type": "eq", "fun": lambda x: np.sum(x) - 1}

            # Bounds: weights between 0 and 1
            bounds = [(0, 1) for _ in range(n_assets)]

            # Initial guess: equal weights
            x0 = np.ones(n_assets) / n_assets

            # Optimize
            result = minimize(
                objective, x0, method="SLSQP", bounds=bounds, constraints=constraints
            )

            if result.success:
                return result.x
            else:
                return None

        except Exception as e:
            self.logger.error(f"Error in mean - variance optimization: {e}")
            return None

    async def _risk_parity_optimizer(
        self, returns: np.ndarray, cov_matrix: np.ndarray, symbols: List[str]
    ) -> Optional[np.ndarray]:
        """Risk parity optimization."""
        try:
            n_assets = len(returns)

            # Objective function: minimize risk contribution variance
            def objective(weights):
                portfolio_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
                risk_contributions = (
                    (weights * np.dot(cov_matrix, weights)) / (portfolio_vol ** 2)
                    if portfolio_vol > 0
                    else np.zeros(n_assets)
                )
                return np.var(risk_contributions)

            # Constraints: weights sum to 1
            constraints = {"type": "eq", "fun": lambda x: np.sum(x) - 1}

            # Bounds: weights between 0 and 1
            bounds = [(0, 1) for _ in range(n_assets)]

            # Initial guess: equal weights
            x0 = np.ones(n_assets) / n_assets

            # Optimize
            result = minimize(
                objective, x0, method="SLSQP", bounds=bounds, constraints=constraints
            )

            if result.success:
                return result.x
            else:
                return None

        except Exception as e:
            self.logger.error(f"Error in risk parity optimization: {e}")
            return None

    async def _max_sharpe_optimizer(
        self, returns: np.ndarray, cov_matrix: np.ndarray, symbols: List[str]
    ) -> Optional[np.ndarray]:
        """Maximum Sharpe ratio optimization."""
        try:
            # This is similar to mean - variance but with different objective
            return await self._mean_variance_optimizer(returns, cov_matrix, symbols)

        except Exception as e:
            self.logger.error(f"Error in max Sharpe optimization: {e}")
            return None

    async def _min_variance_optimizer(
        self, returns: np.ndarray, cov_matrix: np.ndarray, symbols: List[str]
    ) -> Optional[np.ndarray]:
        """Minimum variance optimization."""
        try:
            n_assets = len(returns)

            # Objective function: minimize portfolio variance
            def objective(weights):
                return np.dot(weights, np.dot(cov_matrix, weights))

            # Constraints: weights sum to 1
            constraints = {"type": "eq", "fun": lambda x: np.sum(x) - 1}

            # Bounds: weights between 0 and 1
            bounds = [(0, 1) for _ in range(n_assets)]

            # Initial guess: equal weights
            x0 = np.ones(n_assets) / n_assets

            # Optimize
            result = minimize(
                objective, x0, method="SLSQP", bounds=bounds, constraints=constraints
            )

            if result.success:
                return result.x
            else:
                return None

        except Exception as e:
            self.logger.error(f"Error in min variance optimization: {e}")
            return None

    async def _black_litterman_optimizer(
        self, returns: np.ndarray, cov_matrix: np.ndarray, symbols: List[str]
    ) -> Optional[np.ndarray]:
        """Black - Litterman optimization (simplified)."""
        try:
            # Simplified Black - Litterman implementation
            # In practice, this would incorporate market views and uncertainty
            return await self._mean_variance_optimizer(returns, cov_matrix, symbols)

        except Exception as e:
            self.logger.error(f"Error in Black - Litterman optimization: {e}")
            return None

    async def _apply_portfolio_optimization(
        self, portfolio: Portfolio, optimization_result: Dict[str, Any]
    ) -> None:
        """Apply portfolio optimization results."""
        try:
            optimal_weights = optimization_result.get("optimal_weights", {})

            # Update target weights
            for symbol, optimal_weight in optimal_weights.items():
                if symbol in portfolio.assets:
                    portfolio.assets[symbol].target_weight = optimal_weight

            # Record optimization
            optimization_record = {
                "timestamp": datetime.now(),
                "portfolio_id": portfolio.portfolio_id,
                "method": optimization_result.get("method", "unknown"),
                "expected_improvement": optimization_result.get(
                    "expected_return_improvement", 0
                ),
                "optimal_weights": optimal_weights,
            }
            self.optimization_history.append(optimization_record)

            self.logger.info(f"Applied optimization to {portfolio.name}")

        except Exception as e:
            self.logger.error(f"Error applying portfolio optimization: {e}")

    async def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get comprehensive portfolio summary."""
        try:
            summary = {
                "agent_id": self.config.agent_id,
                "agent_name": self.config.name,
                "status": self.real_status,
                # Portfolio information
                "total_portfolios": len(self.portfolios),
                "portfolio_details": {},
                # Performance metrics
                "total_portfolio_value": sum(
                    p.total_value for p in self.portfolios.values()
                ),
                "average_sharpe_ratio": (
                    np.mean([p.sharpe_ratio for p in self.portfolios.values()])
                    if self.portfolios
                    else 0
                ),
                "average_volatility": (
                    np.mean([p.volatility for p in self.portfolios.values()])
                    if self.portfolios
                    else 0
                ),
                # Rebalancing information
                "total_rebalances": len(self.rebalance_history),
                "last_rebalance": (
                    max(
                        [
                            p.last_rebalance
                            for p in self.portfolios.values()
                            if p.last_rebalance
                        ]
                    )
                    if any(p.last_rebalance for p in self.portfolios.values())
                    else None
                ),
                # Optimization information
                "total_optimizations": len(self.optimization_history),
                "optimization_method": self.optimization_method.value,
                # Risk management
                "risk_budgets_active": len(
                    [
                        rb
                        for p in self.portfolios.values()
                        for rb in p.risk_budgets.values()
                    ]
                ),
                "transaction_cost_rate": self.transaction_cost_rate,
            }

            # Add individual portfolio details
            for portfolio_id, portfolio in self.portfolios.items():
                summary["portfolio_details"][portfolio_id] = {
                    "name": portfolio.name,
                    "total_value": portfolio.total_value,
                    "total_return": portfolio.total_return,
                    "volatility": portfolio.volatility,
                    "sharpe_ratio": portfolio.sharpe_ratio,
                    "max_drawdown": portfolio.max_drawdown,
                    "asset_count": len(portfolio.assets),
                    "last_rebalance": portfolio.last_rebalance,
                    "rebalance_frequency": portfolio.rebalance_frequency,
                }

            return summary

        except Exception as e:
            self.logger.error(f"Error getting portfolio summary: {e}")
            return {"error": str(e)}

    async def cleanup(self) -> None:
        """Cleanup portfolio manager resources."""
        try:
            self.logger.info(f"Cleaning up portfolio manager: {self.config.name}")

            # Clear all collections
            self.portfolios.clear()
            self.optimization_models.clear()
            self.rebalance_history.clear()
            self.performance_history.clear()
            self.optimization_history.clear()

            # Call parent cleanup
            await super().cleanup()

            self.logger.info("Portfolio manager cleanup completed")

        except Exception as e:
            self.logger.exception(f"Error during cleanup: {e}")

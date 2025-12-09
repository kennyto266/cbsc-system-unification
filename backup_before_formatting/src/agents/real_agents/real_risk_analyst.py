"""Real Risk Analyst Agent for Hong Kong quantitative trading system.

This agent performs comprehensive risk analysis, monitoring, and early warning
based on real market data and portfolio positions.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field
from scipy import stats

from ...data_adapters.base_adapter import RealMarketData
from .base_real_agent import BaseRealAgent, RealAgentConfig, RealAgentStatus
from .ml_integration import MLModelManager, ModelType
from .real_data_analyzer import AnalysisResult, SignalStrength


class RiskLevel(str, Enum):
    """Risk level classifications."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskType(str, Enum):
    """Types of financial risk."""

    MARKET = "market"
    CREDIT = "credit"
    LIQUIDITY = "liquidity"
    OPERATIONAL = "operational"
    CONCENTRATION = "concentration"
    CORRELATION = "correlation"


class AlertLevel(str, Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class RiskMetric(BaseModel):
    """Risk metric model."""

    metric_name: str = Field(..., description="Risk metric name")
    metric_type: RiskType = Field(..., description="Risk type")
    value: float = Field(..., description="Metric value")
    threshold: float = Field(..., description="Alert threshold")
    level: RiskLevel = Field(..., description="Risk level")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level")
    calculation_method: str = Field(..., description="Calculation method")
    last_updated: datetime = Field(
        default_factory=datetime.now, description="Last update time"
    )

    class Config:
        use_enum_values = True


class RiskAlert(BaseModel):
    """Risk alert model."""

    alert_id: str = Field(..., description="Alert identifier")
    alert_type: RiskType = Field(..., description="Risk type")
    alert_level: AlertLevel = Field(..., description="Alert severity")
    symbol: Optional[str] = Field(None, description="Related symbol")
    portfolio_id: Optional[str] = Field(None, description="Related portfolio")

    # Alert content
    title: str = Field(..., description="Alert title")
    message: str = Field(..., description="Alert message")
    current_value: float = Field(..., description="Current risk value")
    threshold: float = Field(..., description="Risk threshold")

    # Recommendations
    recommendations: List[str] = Field(
        default_factory=list, description="Risk mitigation recommendations"
    )

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.now, description="Alert creation time"
    )
    acknowledged: bool = Field(False, description="Alert acknowledgment status")
    resolved: bool = Field(False, description="Alert resolution status")

    class Config:
        use_enum_values = True


class StressTestScenario(BaseModel):
    """Stress test scenario model."""

    scenario_id: str = Field(..., description="Scenario identifier")
    scenario_name: str = Field(..., description="Scenario name")
    description: str = Field(..., description="Scenario description")

    # Scenario parameters
    market_shock: float = Field(..., description="Market shock magnitude")
    volatility_multiplier: float = Field(1.0, description="Volatility multiplier")
    correlation_shift: float = Field(0.0, description="Correlation shift")
    liquidity_impact: float = Field(0.0, description="Liquidity impact factor")

    # Results
    portfolio_impact: float = Field(0.0, description="Portfolio impact")
    var_impact: float = Field(0.0, description="VaR impact")
    max_drawdown: float = Field(0.0, description="Maximum drawdown")

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.now, description="Scenario creation time"
    )

    class Config:
        use_enum_values = True


class VaRAnalysis(BaseModel):
    """VaR analysis model."""

    analysis_id: str = Field(..., description="Analysis identifier")
    portfolio_id: str = Field(..., description="Portfolio identifier")

    # VaR metrics
    var_95: float = Field(..., description="95% VaR")
    var_99: float = Field(..., description="99% VaR")
    cvar_95: float = Field(..., description="95% Conditional VaR")
    cvar_99: float = Field(..., description="99% Conditional VaR")

    # Historical VaR
    historical_var_95: float = Field(..., description="Historical 95% VaR")
    historical_var_99: float = Field(..., description="Historical 99% VaR")

    # Parametric VaR
    parametric_var_95: float = Field(..., description="Parametric 95% VaR")
    parametric_var_99: float = Field(..., description="Parametric 99% VaR")

    # Monte Carlo VaR
    monte_carlo_var_95: float = Field(..., description="Monte Carlo 95% VaR")
    monte_carlo_var_99: float = Field(..., description="Monte Carlo 99% VaR")

    # Analysis metadata
    time_horizon: int = Field(1, description="Time horizon in days")
    confidence_levels: List[float] = Field(
        default_factory=lambda: [0.95, 0.99], description="Confidence levels"
    )
    calculation_method: str = Field("historical", description="Calculation method")

    # Risk attribution
    risk_contributions: Dict[str, float] = Field(
        default_factory=dict, description="Risk contributions by asset"
    )

    class Config:
        arbitrary_types_allowed = True


class RealRiskAnalyst(BaseRealAgent):
    """Real Risk Analyst Agent with comprehensive risk analysis capabilities."""

    def __init__(self, config: RealAgentConfig):
        super().__init__(config)
        self.ml_manager = MLModelManager(config)

        # Risk management components
        self.risk_metrics: Dict[str, RiskMetric] = {}
        self.active_alerts: List[RiskAlert] = []
        self.alert_history: List[RiskAlert] = []
        self.stress_scenarios: List[StressTestScenario] = []
        self.var_analyses: Dict[str, VaRAnalysis] = {}

        # Risk thresholds
        self.risk_thresholds = {
            RiskType.MARKET: {"warning": 0.05, "critical": 0.10},
            RiskType.CREDIT: {"warning": 0.02, "critical": 0.05},
            RiskType.LIQUIDITY: {"warning": 0.03, "critical": 0.07},
            RiskType.CONCENTRATION: {"warning": 0.20, "critical": 0.30},
            RiskType.CORRELATION: {"warning": 0.80, "critical": 0.90},
        }

        # Risk models
        self.risk_models: Dict[str, Any] = {}

        # Performance tracking
        self.risk_history: List[Dict[str, Any]] = []

    async def _initialize_specific(self) -> bool:
        """Initialize risk analyst specific components."""
        try:
            self.logger.info("Initializing risk analyst specific components...")

            # Initialize ML model manager
            if not await self.ml_manager.initialize():
                self.logger.error("Failed to initialize ML model manager")
                return False

            # Initialize risk models
            await self._initialize_risk_models()

            # Create default stress test scenarios
            await self._create_default_stress_scenarios()

            # Initialize risk monitoring
            await self._initialize_risk_monitoring()

            self.logger.info("Risk analyst initialization completed")
            return True

        except Exception as e:
            self.logger.exception(f"Failed to initialize risk analyst: {e}")
            return False

    async def _initialize_risk_models(self) -> None:
        """Initialize risk calculation models."""
        try:
            # Initialize various risk models
            self.risk_models = {
                "historical_var": self._calculate_historical_var,
                "parametric_var": self._calculate_parametric_var,
                "monte_carlo_var": self._calculate_monte_carlo_var,
                "stress_test": self._perform_stress_test,
                "correlation_analysis": self._analyze_correlations,
                "concentration_analysis": self._analyze_concentration,
                "liquidity_analysis": self._analyze_liquidity,
            }

            self.logger.info("Risk models initialized")

        except Exception as e:
            self.logger.error(f"Error initializing risk models: {e}")

    async def _create_default_stress_scenarios(self) -> None:
        """Create default stress test scenarios."""
        try:
            # Market crash scenario
            market_crash = StressTestScenario(
                scenario_id="market_crash_2008",
                scenario_name="2008年金融危机",
                description="模拟2008年金融危机的市场冲击",
                market_shock=-0.30,
                volatility_multiplier=3.0,
                correlation_shift=0.3,
                liquidity_impact=0.5,
            )
            self.stress_scenarios.append(market_crash)

            # COVID - 19 scenario
            covid_scenario = StressTestScenario(
                scenario_id="covid_19_2020",
                scenario_name="2020年COVID - 19疫情",
                description="模拟2020年COVID - 19疫情的市场冲击",
                market_shock=-0.25,
                volatility_multiplier=2.5,
                correlation_shift=0.2,
                liquidity_impact=0.3,
            )
            self.stress_scenarios.append(covid_scenario)

            # Interest rate shock
            rate_shock = StressTestScenario(
                scenario_id="rate_shock",
                scenario_name="利率冲击",
                description="模拟利率大幅上升的影响",
                market_shock=-0.15,
                volatility_multiplier=2.0,
                correlation_shift=0.1,
                liquidity_impact=0.2,
            )
            self.stress_scenarios.append(rate_shock)

            self.logger.info(
                f"Created {len(self.stress_scenarios)} default stress test scenarios"
            )

        except Exception as e:
            self.logger.error(f"Error creating default stress scenarios: {e}")

    async def _initialize_risk_monitoring(self) -> None:
        """Initialize risk monitoring system."""
        try:
            # Initialize monitoring parameters
            self.monitoring_frequency = 300  # 5 minutes
            self.alert_cooldown = 3600  # 1 hour

            self.logger.info("Risk monitoring initialized")

        except Exception as e:
            self.logger.error(f"Error initializing risk monitoring: {e}")

    async def _enhance_analysis(
        self, base_result: AnalysisResult, market_data: List[RealMarketData]
    ) -> AnalysisResult:
        """Enhance analysis with risk analysis specific logic."""
        try:
            # Calculate comprehensive risk metrics
            risk_metrics = await self._calculate_comprehensive_risk_metrics(market_data)

            # Update base result
            enhanced_result = base_result.copy()

            # Add risk insights
            risk_insights = await self._generate_risk_insights(
                risk_metrics, enhanced_result
            )
            enhanced_result.insights.extend(risk_insights)

            # Add risk warnings
            risk_warnings = await self._generate_risk_warnings(risk_metrics)
            enhanced_result.warnings.extend(risk_warnings)

            return enhanced_result

        except Exception as e:
            self.logger.error(f"Error enhancing analysis for risk analysis: {e}")
            return base_result

    async def _calculate_comprehensive_risk_metrics(
        self, market_data: List[RealMarketData]
    ) -> Dict[str, RiskMetric]:
        """Calculate comprehensive risk metrics."""
        try:
            risk_metrics = {}

            # Market risk metrics
            market_risk = await self._calculate_market_risk_metrics(market_data)
            risk_metrics.update(market_risk)

            # Concentration risk metrics
            concentration_risk = await self._calculate_concentration_risk_metrics(
                market_data
            )
            risk_metrics.update(concentration_risk)

            # Correlation risk metrics
            correlation_risk = await self._calculate_correlation_risk_metrics(
                market_data
            )
            risk_metrics.update(correlation_risk)

            # Liquidity risk metrics
            liquidity_risk = await self._calculate_liquidity_risk_metrics(market_data)
            risk_metrics.update(liquidity_risk)

            # Update risk metrics storage
            self.risk_metrics.update(risk_metrics)

            return risk_metrics

        except Exception as e:
            self.logger.error(f"Error calculating comprehensive risk metrics: {e}")
            return {}

    async def _calculate_market_risk_metrics(
        self, market_data: List[RealMarketData]
    ) -> Dict[str, RiskMetric]:
        """Calculate market risk metrics."""
        try:
            metrics = {}

            if len(market_data) < 20:
                return metrics

            # Convert to DataFrame
            df = pd.DataFrame(
                [
                    {
                        "timestamp": d.timestamp,
                        "symbol": d.symbol,
                        "close": float(d.close_price),
                        "volume": d.volume,
                    }
                    for d in market_data
                ]
            )

            df.set_index("timestamp", inplace=True)
            df.sort_index(inplace=True)

            # Calculate returns by symbol
            symbol_returns = {}
            for symbol in df["symbol"].unique():
                symbol_data = df[df["symbol"] == symbol]
                if len(symbol_data) > 1:
                    returns = symbol_data["close"].pct_change().dropna()
                    if len(returns) > 0:
                        symbol_returns[symbol] = returns

            if not symbol_returns:
                return metrics

            # Portfolio volatility (simplified)
            portfolio_vol = np.mean(
                [returns.std() for returns in symbol_returns.values()]
            )
            metrics["portfolio_volatility"] = RiskMetric(
                metric_name="Portfolio Volatility",
                metric_type=RiskType.MARKET,
                value=portfolio_vol,
                threshold=self.risk_thresholds[RiskType.MARKET]["warning"],
                level=self._classify_risk_level(portfolio_vol, RiskType.MARKET),
                confidence=0.8,
                calculation_method="Standard Deviation",
            )

            # Maximum drawdown
            max_dd = await self._calculate_maximum_drawdown(symbol_returns)
            metrics["maximum_drawdown"] = RiskMetric(
                metric_name="Maximum Drawdown",
                metric_type=RiskType.MARKET,
                value=max_dd,
                threshold=0.10,  # 10% threshold
                level=self._classify_risk_level(max_dd, RiskType.MARKET),
                confidence=0.9,
                calculation_method="Peak - to - Trough",
            )

            # VaR calculations
            var_95 = await self._calculate_historical_var(symbol_returns, 0.95)
            metrics["var_95"] = RiskMetric(
                metric_name="95% Value at Risk",
                metric_type=RiskType.MARKET,
                value=var_95,
                threshold=self.risk_thresholds[RiskType.MARKET]["warning"],
                level=self._classify_risk_level(abs(var_95), RiskType.MARKET),
                confidence=0.85,
                calculation_method="Historical",
            )

            return metrics

        except Exception as e:
            self.logger.error(f"Error calculating market risk metrics: {e}")
            return {}

    async def _calculate_concentration_risk_metrics(
        self, market_data: List[RealMarketData]
    ) -> Dict[str, RiskMetric]:
        """Calculate concentration risk metrics."""
        try:
            metrics = {}

            # Group by symbol to calculate weights
            symbol_volumes = {}
            total_volume = 0

            for data in market_data:
                symbol = data.symbol
                volume = data.volume
                if symbol not in symbol_volumes:
                    symbol_volumes[symbol] = 0
                symbol_volumes[symbol] += volume
                total_volume += volume

            if total_volume == 0:
                return metrics

            # Calculate concentration metrics
            weights = [volume / total_volume for volume in symbol_volumes.values()]

            # Herfindahl - Hirschman Index (HHI)
            hhi = sum(w ** 2 for w in weights)
            metrics["concentration_hhi"] = RiskMetric(
                metric_name="Concentration HHI",
                metric_type=RiskType.CONCENTRATION,
                value=hhi,
                threshold=self.risk_thresholds[RiskType.CONCENTRATION]["warning"],
                level=self._classify_risk_level(hhi, RiskType.CONCENTRATION),
                confidence=0.9,
                calculation_method="Herfindahl - Hirschman Index",
            )

            # Maximum weight
            max_weight = max(weights) if weights else 0
            metrics["max_weight"] = RiskMetric(
                metric_name="Maximum Weight",
                metric_type=RiskType.CONCENTRATION,
                value=max_weight,
                threshold=0.30,  # 30% threshold
                level=self._classify_risk_level(max_weight, RiskType.CONCENTRATION),
                confidence=0.95,
                calculation_method="Maximum Position Weight",
            )

            return metrics

        except Exception as e:
            self.logger.error(f"Error calculating concentration risk metrics: {e}")
            return {}

    async def _calculate_correlation_risk_metrics(
        self, market_data: List[RealMarketData]
    ) -> Dict[str, RiskMetric]:
        """Calculate correlation risk metrics."""
        try:
            metrics = {}

            # Group data by symbol
            symbol_data = {}
            for data in market_data:
                symbol = data.symbol
                if symbol not in symbol_data:
                    symbol_data[symbol] = []
                symbol_data[symbol].append(float(data.close_price))

            if len(symbol_data) < 2:
                return metrics

            # Calculate correlations
            symbols = list(symbol_data.keys())
            correlations = []

            for i in range(len(symbols)):
                for j in range(i + 1, len(symbols)):
                    symbol1, symbol2 = symbols[i], symbols[j]
                    data1 = symbol_data[symbol1]
                    data2 = symbol_data[symbol2]

                    # Align data lengths
                    min_len = min(len(data1), len(data2))
                    if min_len < 10:
                        continue

                    data1 = data1[:min_len]
                    data2 = data2[:min_len]

                    # Calculate correlation
                    correlation = np.corrcoef(data1, data2)[0, 1]
                    if not np.isnan(correlation):
                        correlations.append(abs(correlation))

            if correlations:
                avg_correlation = np.mean(correlations)
                max_correlation = np.max(correlations)

                metrics["avg_correlation"] = RiskMetric(
                    metric_name="Average Correlation",
                    metric_type=RiskType.CORRELATION,
                    value=avg_correlation,
                    threshold=self.risk_thresholds[RiskType.CORRELATION]["warning"],
                    level=self._classify_risk_level(
                        avg_correlation, RiskType.CORRELATION
                    ),
                    confidence=0.8,
                    calculation_method="Average Absolute Correlation",
                )

                metrics["max_correlation"] = RiskMetric(
                    metric_name="Maximum Correlation",
                    metric_type=RiskType.CORRELATION,
                    value=max_correlation,
                    threshold=self.risk_thresholds[RiskType.CORRELATION]["critical"],
                    level=self._classify_risk_level(
                        max_correlation, RiskType.CORRELATION
                    ),
                    confidence=0.85,
                    calculation_method="Maximum Absolute Correlation",
                )

            return metrics

        except Exception as e:
            self.logger.error(f"Error calculating correlation risk metrics: {e}")
            return {}

    async def _calculate_liquidity_risk_metrics(
        self, market_data: List[RealMarketData]
    ) -> Dict[str, RiskMetric]:
        """Calculate liquidity risk metrics."""
        try:
            metrics = {}

            # Group by symbol
            symbol_volumes = {}
            symbol_prices = {}

            for data in market_data:
                symbol = data.symbol
                if symbol not in symbol_volumes:
                    symbol_volumes[symbol] = []
                    symbol_prices[symbol] = []
                symbol_volumes[symbol].append(data.volume)
                symbol_prices[symbol].append(float(data.close_price))

            if not symbol_volumes:
                return metrics

            # Calculate liquidity metrics
            liquidity_scores = []

            for symbol in symbol_volumes:
                volumes = symbol_volumes[symbol]
                prices = symbol_prices[symbol]

                if len(volumes) < 5 or len(prices) < 5:
                    continue

                # Volume volatility
                volume_volatility = (
                    np.std(volumes) / np.mean(volumes) if np.mean(volumes) > 0 else 0
                )

                # Price impact (simplified)
                price_changes = [
                    abs(prices[i] - prices[i - 1]) / prices[i - 1]
                    for i in range(1, len(prices))
                ]
                avg_price_change = np.mean(price_changes) if price_changes else 0

                # Liquidity score (lower is better)
                liquidity_score = volume_volatility + avg_price_change * 10
                liquidity_scores.append(liquidity_score)

            if liquidity_scores:
                avg_liquidity_risk = np.mean(liquidity_scores)
                max_liquidity_risk = np.max(liquidity_scores)

                metrics["avg_liquidity_risk"] = RiskMetric(
                    metric_name="Average Liquidity Risk",
                    metric_type=RiskType.LIQUIDITY,
                    value=avg_liquidity_risk,
                    threshold=self.risk_thresholds[RiskType.LIQUIDITY]["warning"],
                    level=self._classify_risk_level(
                        avg_liquidity_risk, RiskType.LIQUIDITY
                    ),
                    confidence=0.7,
                    calculation_method="Volume Volatility + Price Impact",
                )

                metrics["max_liquidity_risk"] = RiskMetric(
                    metric_name="Maximum Liquidity Risk",
                    metric_type=RiskType.LIQUIDITY,
                    value=max_liquidity_risk,
                    threshold=self.risk_thresholds[RiskType.LIQUIDITY]["critical"],
                    level=self._classify_risk_level(
                        max_liquidity_risk, RiskType.LIQUIDITY
                    ),
                    confidence=0.75,
                    calculation_method="Maximum Liquidity Score",
                )

            return metrics

        except Exception as e:
            self.logger.error(f"Error calculating liquidity risk metrics: {e}")
            return {}

    def _classify_risk_level(self, value: float, risk_type: RiskType) -> RiskLevel:
        """Classify risk level based on value and thresholds."""
        try:
            thresholds = self.risk_thresholds.get(
                risk_type, {"warning": 0.05, "critical": 0.10}
            )
            warning_threshold = thresholds["warning"]
            critical_threshold = thresholds["critical"]

            if value <= warning_threshold:
                return RiskLevel.LOW
            elif value <= critical_threshold:
                return RiskLevel.MEDIUM
            elif value <= critical_threshold * 2:
                return RiskLevel.HIGH
            else:
                return RiskLevel.CRITICAL

        except Exception:
            return RiskLevel.MEDIUM

    async def _calculate_maximum_drawdown(
        self, symbol_returns: Dict[str, pd.Series]
    ) -> float:
        """Calculate maximum drawdown across all symbols."""
        try:
            max_drawdowns = []

            for symbol, returns in symbol_returns.items():
                if len(returns) < 2:
                    continue

                # Calculate cumulative returns
                cumulative_returns = (1 + returns).cumprod()

                # Calculate running maximum
                running_max = cumulative_returns.expanding().max()

                # Calculate drawdown
                drawdown = (cumulative_returns - running_max) / running_max

                # Get maximum drawdown
                max_dd = drawdown.min()
                if not np.isnan(max_dd):
                    max_drawdowns.append(abs(max_dd))

            return max(max_drawdowns) if max_drawdowns else 0.0

        except Exception as e:
            self.logger.error(f"Error calculating maximum drawdown: {e}")
            return 0.0

    async def _calculate_historical_var(
        self, symbol_returns: Dict[str, pd.Series], confidence_level: float
    ) -> float:
        """Calculate historical VaR."""
        try:
            # Combine all returns
            all_returns = []
            for returns in symbol_returns.values():
                all_returns.extend(returns.tolist())

            if not all_returns:
                return 0.0

            # Calculate VaR
            var_percentile = (1 - confidence_level) * 100
            var_value = np.percentile(all_returns, var_percentile)

            return var_value

        except Exception as e:
            self.logger.error(f"Error calculating historical VaR: {e}")
            return 0.0

    async def _generate_risk_insights(
        self, risk_metrics: Dict[str, RiskMetric], analysis_result: AnalysisResult
    ) -> List[str]:
        """Generate risk - specific insights."""
        try:
            insights = []

            for metric_name, metric in risk_metrics.items():
                if metric.level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                    insights.append(
                        f"高风险指标: {metric.metric_name} = {metric.value:.3f} ({metric.level.value})"
                    )
                elif metric.level == RiskLevel.MEDIUM:
                    insights.append(
                        f"中等风险: {metric.metric_name} = {metric.value:.3f}"
                    )
                else:
                    insights.append(
                        f"低风险: {metric.metric_name} = {metric.value:.3f}"
                    )

            # Market regime insights
            regime = analysis_result.market_regime.regime_type
            if regime == "high_volatility":
                insights.append("高风险环境: 市场波动率显著上升")
            elif regime == "low_volatility":
                insights.append("低波动环境: 可能存在波动率聚集风险")

            return insights

        except Exception as e:
            self.logger.error(f"Error generating risk insights: {e}")
            return []

    async def _generate_risk_warnings(
        self, risk_metrics: Dict[str, RiskMetric]
    ) -> List[str]:
        """Generate risk warnings."""
        try:
            warnings = []

            for metric_name, metric in risk_metrics.items():
                if metric.level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                    if metric.level == RiskLevel.CRITICAL:
                        warnings.append(
                            f"⚠️ 严重风险警告: {metric.metric_name} 超出临界阈值"
                        )
                    else:
                        warnings.append(
                            f"⚠️ 高风险警告: {metric.metric_name} 超出警告阈值"
                        )

                # Generate alerts for critical risks
                if metric.level == RiskLevel.CRITICAL:
                    await self._create_risk_alert(metric)

            return warnings

        except Exception as e:
            self.logger.error(f"Error generating risk warnings: {e}")
            return []

    async def _create_risk_alert(self, metric: RiskMetric) -> None:
        """Create risk alert for critical metrics."""
        try:
            # Check if alert already exists
            existing_alert = any(
                alert.alert_type == metric.metric_type
                and not alert.resolved
                and (datetime.now() - alert.created_at).total_seconds()
                < self.alert_cooldown
                for alert in self.active_alerts
            )

            if existing_alert:
                return

            # Determine alert level
            if metric.level == RiskLevel.CRITICAL:
                alert_level = AlertLevel.CRITICAL
            elif metric.level == RiskLevel.HIGH:
                alert_level = AlertLevel.WARNING
            else:
                return

            # Create alert
            alert = RiskAlert(
                alert_id=f"risk_alert_{datetime.now().strftime('%Y % m % d_ % H % M % S')}",
                alert_type=metric.metric_type,
                alert_level=alert_level,
                title=f"风险警告: {metric.metric_name}",
                message=f"{metric.metric_name} 当前值 {metric.value:.3f} 超出阈值 {metric.threshold:.3f}",
                current_value=metric.value,
                threshold=metric.threshold,
                recommendations=self._generate_risk_recommendations(metric),
            )

            self.active_alerts.append(alert)
            self.alert_history.append(alert)

            self.logger.warning(f"Risk alert created: {alert.title}")

        except Exception as e:
            self.logger.error(f"Error creating risk alert: {e}")

    def _generate_risk_recommendations(self, metric: RiskMetric) -> List[str]:
        """Generate risk mitigation recommendations."""
        try:
            recommendations = []

            if metric.metric_type == RiskType.MARKET:
                recommendations.extend(
                    ["考虑减少仓位大小", "增加对冲策略", "提高现金比例"]
                )
            elif metric.metric_type == RiskType.CONCENTRATION:
                recommendations.extend(
                    ["分散投资组合", "减少最大仓位权重", "增加资产多样性"]
                )
            elif metric.metric_type == RiskType.CORRELATION:
                recommendations.extend(
                    ["寻找低相关性资产", "调整资产配置", "考虑另类投资"]
                )
            elif metric.metric_type == RiskType.LIQUIDITY:
                recommendations.extend(
                    ["提高现金储备", "减少低流动性资产", "优化交易策略"]
                )

            return recommendations

        except Exception as e:
            self.logger.error(f"Error generating risk recommendations: {e}")
            return ["请咨询风险管理专家"]

    async def _enhance_signals(
        self, base_signals: List[Dict[str, Any]], analysis_result: AnalysisResult
    ) -> List[Dict[str, Any]]:
        """Enhance signals with risk analysis logic."""
        try:
            enhanced_signals = []

            # Generate risk - based signals
            risk_signals = await self._generate_risk_signals(analysis_result)
            enhanced_signals.extend(risk_signals)

            # Filter signals based on risk assessment
            filtered_signals = await self._filter_signals_by_risk(
                base_signals, analysis_result
            )
            enhanced_signals.extend(filtered_signals)

            return enhanced_signals

        except Exception as e:
            self.logger.error(f"Error enhancing signals for risk analysis: {e}")
            return base_signals

    async def _generate_risk_signals(
        self, analysis_result: AnalysisResult
    ) -> List[Dict[str, Any]]:
        """Generate risk - based signals."""
        try:
            risk_signals = []

            # Check for risk threshold breaches
            for metric_name, metric in self.risk_metrics.items():
                if metric.level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                    signal = {
                        "signal_id": f"risk_signal_{metric_name}_{datetime.now().strftime('%Y % m % d_ % H % M % S')}",
                        "symbol": "PORTFOLIO",
                        "side": "risk_reduction",
                        "strength": 0.8 if metric.level == RiskLevel.CRITICAL else 0.6,
                        "confidence": metric.confidence,
                        "reasoning": f"风险控制信号: {metric.metric_name} 风险等级 {metric.level.value}",
                        "signal_type": "risk_management",
                        "risk_type": metric.metric_type.value,
                        "risk_level": metric.level.value,
                        "recommendations": self._generate_risk_recommendations(metric),
                    }
                    risk_signals.append(signal)

            return risk_signals

        except Exception as e:
            self.logger.error(f"Error generating risk signals: {e}")
            return []

    async def _filter_signals_by_risk(
        self, base_signals: List[Dict[str, Any]], analysis_result: AnalysisResult
    ) -> List[Dict[str, Any]]:
        """Filter signals based on risk assessment."""
        try:
            filtered_signals = []

            for signal in base_signals:
                # Risk - based filtering
                if await self._is_signal_acceptable_by_risk(signal):
                    # Add risk assessment to signal
                    enhanced_signal = signal.copy()
                    enhanced_signal["risk_assessment"] = await self._assess_signal_risk(
                        signal
                    )
                    filtered_signals.append(enhanced_signal)
                else:
                    self.logger.warning(
                        f"Signal filtered due to risk concerns: {signal.get('signal_id', 'unknown')}"
                    )

            return filtered_signals

        except Exception as e:
            self.logger.error(f"Error filtering signals by risk: {e}")
            return base_signals

    async def _is_signal_acceptable_by_risk(self, signal: Dict[str, Any]) -> bool:
        """Check if signal is acceptable from risk perspective."""
        try:
            # Check portfolio - level risk metrics
            for metric in self.risk_metrics.values():
                if metric.level == RiskLevel.CRITICAL:
                    # Reject all new signals during critical risk conditions
                    return False

            # Check signal - specific risk
            signal_strength = signal.get("strength", 0)
            signal_confidence = signal.get("confidence", 0)

            # Reject low - quality signals during high - risk periods
            high_risk_period = any(
                metric.level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
                for metric in self.risk_metrics.values()
            )
            if high_risk_period and (signal_strength < 0.8 or signal_confidence < 0.8):
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error checking signal acceptability: {e}")
            return False

    async def _assess_signal_risk(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk associated with a trading signal."""
        try:
            risk_assessment = {
                "overall_risk": "low",
                "risk_factors": [],
                "risk_score": 0.0,
            }

            signal_strength = signal.get("strength", 0)
            signal_confidence = signal.get("confidence", 0)

            # Calculate risk score
            risk_score = (1 - signal_strength) + (1 - signal_confidence)
            risk_assessment["risk_score"] = risk_score

            # Assess overall risk
            if risk_score > 0.6:
                risk_assessment["overall_risk"] = "high"
                risk_assessment["risk_factors"].append("Low signal quality")
            elif risk_score > 0.3:
                risk_assessment["overall_risk"] = "medium"
            else:
                risk_assessment["overall_risk"] = "low"

            # Add portfolio risk factors
            for metric in self.risk_metrics.values():
                if metric.level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                    risk_assessment["risk_factors"].append(f"{metric.metric_name} risk")

            return risk_assessment

        except Exception as e:
            self.logger.error(f"Error assessing signal risk: {e}")
            return {
                "overall_risk": "medium",
                "risk_factors": ["Assessment error"],
                "risk_score": 0.5,
            }

    async def _execute_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Execute risk management signal."""
        try:
            signal_type = signal.get("signal_type", "")

            if signal_type == "risk_management":
                return await self._execute_risk_management_signal(signal)
            else:
                # For other signal types, just validate from risk perspective
                return {
                    "signal_id": signal.get("signal_id", "unknown"),
                    "status": "risk_validated",
                    "risk_assessment": signal.get("risk_assessment", {}),
                }

        except Exception as e:
            self.logger.error(f"Error executing risk signal: {e}")
            return {
                "signal_id": signal.get("signal_id", "unknown"),
                "status": "failed",
                "error": str(e),
            }

    async def _execute_risk_management_signal(
        self, signal: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute risk management signal."""
        try:
            risk_type = signal.get("risk_type", "")
            risk_level = signal.get("risk_level", "")
            recommendations = signal.get("recommendations", [])

            # Create risk management action
            action_result = {
                "signal_id": signal.get("signal_id", "unknown"),
                "status": "executed",
                "action_type": "risk_management",
                "risk_type": risk_type,
                "risk_level": risk_level,
                "recommendations": recommendations,
                "execution_time": datetime.now(),
            }

            # Log risk management action
            self.logger.warning(
                f"Risk management action executed: {risk_type} - {risk_level}"
            )

            return action_result

        except Exception as e:
            self.logger.error(f"Error executing risk management signal: {e}")
            return {
                "signal_id": signal.get("signal_id", "unknown"),
                "status": "failed",
                "error": str(e),
            }

    async def perform_stress_test(
        self, scenario_id: str, portfolio_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform stress test using specified scenario."""
        try:
            scenario = next(
                (s for s in self.stress_scenarios if s.scenario_id == scenario_id), None
            )
            if not scenario:
                return {"success": False, "error": f"Scenario not found: {scenario_id}"}

            # Apply stress test scenario
            stress_result = await self._apply_stress_scenario(scenario, portfolio_data)

            # Update scenario with results
            scenario.portfolio_impact = stress_result.get("portfolio_impact", 0)
            scenario.var_impact = stress_result.get("var_impact", 0)
            scenario.max_drawdown = stress_result.get("max_drawdown", 0)

            return {
                "success": True,
                "scenario_id": scenario_id,
                "scenario_name": scenario.scenario_name,
                "results": stress_result,
            }

        except Exception as e:
            self.logger.error(f"Error performing stress test: {e}")
            return {"success": False, "error": str(e)}

    async def _apply_stress_scenario(
        self, scenario: StressTestScenario, portfolio_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply stress test scenario to portfolio."""
        try:
            # Simulate stress test impact
            market_shock = scenario.market_shock
            volatility_multiplier = scenario.volatility_multiplier

            # Calculate portfolio impact (simplified)
            portfolio_impact = market_shock * 0.7  # Assume 70% exposure to market shock

            # Calculate VaR impact
            var_impact = abs(market_shock) * volatility_multiplier * 0.5

            # Calculate maximum drawdown
            max_drawdown = abs(portfolio_impact) + var_impact * 0.3

            return {
                "portfolio_impact": portfolio_impact,
                "var_impact": var_impact,
                "max_drawdown": max_drawdown,
                "scenario_applied": scenario.scenario_name,
            }

        except Exception as e:
            self.logger.error(f"Error applying stress scenario: {e}")
            return {"portfolio_impact": 0, "var_impact": 0, "max_drawdown": 0}

    async def get_risk_summary(self) -> Dict[str, Any]:
        """Get comprehensive risk summary."""
        try:
            summary = {
                "agent_id": self.config.agent_id,
                "agent_name": self.config.name,
                "status": self.real_status,
                # Risk metrics
                "total_risk_metrics": len(self.risk_metrics),
                "high_risk_metrics": len(
                    [
                        m
                        for m in self.risk_metrics.values()
                        if m.level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
                    ]
                ),
                "critical_risk_metrics": len(
                    [
                        m
                        for m in self.risk_metrics.values()
                        if m.level == RiskLevel.CRITICAL
                    ]
                ),
                # Active alerts
                "active_alerts": len(self.active_alerts),
                "critical_alerts": len(
                    [
                        a
                        for a in self.active_alerts
                        if a.alert_level == AlertLevel.CRITICAL
                    ]
                ),
                "unacknowledged_alerts": len(
                    [a for a in self.active_alerts if not a.acknowledged]
                ),
                # Risk metrics by type
                "risk_by_type": {},
                # Stress testing
                "stress_scenarios": len(self.stress_scenarios),
                "var_analyses": len(self.var_analyses),
                # Historical data
                "alert_history_count": len(self.alert_history),
                "risk_history_count": len(self.risk_history),
            }

            # Group risk metrics by type
            for metric in self.risk_metrics.values():
                risk_type = metric.metric_type.value
                if risk_type not in summary["risk_by_type"]:
                    summary["risk_by_type"][risk_type] = {
                        "count": 0,
                        "high_risk_count": 0,
                        "critical_risk_count": 0,
                    }

                summary["risk_by_type"][risk_type]["count"] += 1
                if metric.level == RiskLevel.HIGH:
                    summary["risk_by_type"][risk_type]["high_risk_count"] += 1
                elif metric.level == RiskLevel.CRITICAL:
                    summary["risk_by_type"][risk_type]["critical_risk_count"] += 1

            return summary

        except Exception as e:
            self.logger.error(f"Error getting risk summary: {e}")
            return {"error": str(e)}

    async def cleanup(self) -> None:
        """Cleanup risk analyst resources."""
        try:
            self.logger.info(f"Cleaning up risk analyst: {self.config.name}")

            # Clear all collections
            self.risk_metrics.clear()
            self.active_alerts.clear()
            self.alert_history.clear()
            self.stress_scenarios.clear()
            self.var_analyses.clear()
            self.risk_models.clear()
            self.risk_history.clear()

            # Call parent cleanup
            await super().cleanup()

            self.logger.info("Risk analyst cleanup completed")

        except Exception as e:
            self.logger.exception(f"Error during cleanup: {e}")

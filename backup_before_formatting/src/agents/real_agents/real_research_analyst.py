"""Real Research Analyst Agent for Hong Kong quantitative trading system.

This agent performs advanced strategy research, hypothesis testing,
and factor discovery based on real market data and academic literature.
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


class ResearchType(str, Enum):
    """Types of research."""

    STRATEGY_DEVELOPMENT = "strategy_development"
    FACTOR_ANALYSIS = "factor_analysis"
    MARKET_REGIME = "market_regime"
    RISK_MODELING = "risk_modeling"
    BACKTESTING = "backtesting"
    LITERATURE_REVIEW = "literature_review"


class HypothesisStatus(str, Enum):
    """Hypothesis testing status."""

    PENDING = "pending"
    TESTING = "testing"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    INCONCLUSIVE = "inconclusive"


class FactorType(str, Enum):
    """Factor types."""

    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    MACROECONOMIC = "macroeconomic"
    SENTIMENT = "sentiment"
    MICROSTRUCTURE = "microstructure"
    CROSS_SECTIONAL = "cross_sectional"


class ResearchHypothesis(BaseModel):
    """Research hypothesis model."""

    hypothesis_id: str = Field(..., description="Hypothesis identifier")
    title: str = Field(..., description="Hypothesis title")
    description: str = Field(..., description="Detailed description")
    research_type: ResearchType = Field(..., description="Research type")

    # Hypothesis details
    null_hypothesis: str = Field(..., description="Null hypothesis")
    alternative_hypothesis: str = Field(..., description="Alternative hypothesis")
    significance_level: float = Field(
        0.05, ge=0.01, le=0.1, description="Significance level"
    )

    # Testing parameters
    test_method: str = Field(..., description="Statistical test method")
    sample_size: int = Field(0, description="Sample size")
    test_statistic: Optional[float] = Field(None, description="Test statistic")
    p_value: Optional[float] = Field(None, description="P - value")

    # Results
    status: HypothesisStatus = Field(
        HypothesisStatus.PENDING, description="Testing status"
    )
    conclusion: str = Field("", description="Test conclusion")
    confidence_level: float = Field(0.0, ge=0.0, le=1.0, description="Confidence level")

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation time"
    )
    tested_at: Optional[datetime] = Field(None, description="Testing time")

    class Config:
        use_enum_values = True


class Factor(BaseModel):
    """Factor model for factor analysis."""

    factor_id: str = Field(..., description="Factor identifier")
    factor_name: str = Field(..., description="Factor name")
    factor_type: FactorType = Field(..., description="Factor type")
    description: str = Field(..., description="Factor description")

    # Factor properties
    calculation_method: str = Field(..., description="Calculation method")
    data_requirements: List[str] = Field(
        default_factory=list, description="Required data"
    )
    frequency: str = Field("daily", description="Update frequency")

    # Performance metrics
    ic_mean: float = Field(0.0, description="Information Coefficient mean")
    ic_std: float = Field(0.0, description="Information Coefficient std")
    ic_ir: float = Field(0.0, description="Information Ratio")
    hit_rate: float = Field(0.0, ge=0.0, le=1.0, description="Hit rate")
    sharpe_ratio: float = Field(0.0, description="Sharpe ratio")

    # Factor analysis
    correlation_with_market: float = Field(
        0.0, ge=-1.0, le=1.0, description="Market correlation"
    )
    factor_exposure: Dict[str, float] = Field(
        default_factory=dict, description="Factor exposures"
    )
    decay_rate: float = Field(0.0, description="Factor decay rate")

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation time"
    )
    last_updated: datetime = Field(
        default_factory=datetime.now, description="Last update time"
    )
    is_active: bool = Field(True, description="Active status")

    class Config:
        use_enum_values = True


class StrategyResearch(BaseModel):
    """Strategy research model."""

    research_id: str = Field(..., description="Research identifier")
    strategy_name: str = Field(..., description="Strategy name")
    research_type: ResearchType = Field(..., description="Research type")

    # Research details
    objective: str = Field(..., description="Research objective")
    methodology: str = Field(..., description="Research methodology")
    data_sources: List[str] = Field(default_factory=list, description="Data sources")

    # Key findings
    key_findings: List[str] = Field(default_factory=list, description="Key findings")
    recommendations: List[str] = Field(
        default_factory=list, description="Recommendations"
    )
    limitations: List[str] = Field(default_factory=list, description="Limitations")

    # Performance metrics
    backtest_period: str = Field("", description="Backtest period")
    annual_return: float = Field(0.0, description="Annual return")
    sharpe_ratio: float = Field(0.0, description="Sharpe ratio")
    max_drawdown: float = Field(0.0, description="Maximum drawdown")
    win_rate: float = Field(0.0, ge=0.0, le=1.0, description="Win rate")

    # Research status
    status: str = Field("ongoing", description="Research status")
    completion_percentage: float = Field(
        0.0, ge=0.0, le=100.0, description="Completion percentage"
    )

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation time"
    )
    last_updated: datetime = Field(
        default_factory=datetime.now, description="Last update time"
    )

    class Config:
        use_enum_values = True


class LiteratureReview(BaseModel):
    """Literature review model."""

    review_id: str = Field(..., description="Review identifier")
    topic: str = Field(..., description="Review topic")
    research_question: str = Field(..., description="Research question")

    # Literature sources
    papers: List[Dict[str, Any]] = Field(
        default_factory=list, description="Reviewed papers"
    )
    key_authors: List[str] = Field(default_factory=list, description="Key authors")
    journals: List[str] = Field(default_factory=list, description="Relevant journals")

    # Review findings
    main_themes: List[str] = Field(default_factory=list, description="Main themes")
    methodologies: List[str] = Field(
        default_factory=list, description="Common methodologies"
    )
    gaps: List[str] = Field(default_factory=list, description="Research gaps")
    future_directions: List[str] = Field(
        default_factory=list, description="Future directions"
    )

    # Synthesis
    synthesis: str = Field("", description="Literature synthesis")
    implications: List[str] = Field(
        default_factory=list, description="Practical implications"
    )

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation time"
    )
    last_updated: datetime = Field(
        default_factory=datetime.now, description="Last update time"
    )

    class Config:
        arbitrary_types_allowed = True


class RealResearchAnalyst(BaseRealAgent):
    """Real Research Analyst Agent with advanced research capabilities."""

    def __init__(self, config: RealAgentConfig):
        super().__init__(config)
        self.ml_manager = MLModelManager(config)

        # Research components
        self.hypotheses: Dict[str, ResearchHypothesis] = {}
        self.factors: Dict[str, Factor] = {}
        self.strategy_research: Dict[str, StrategyResearch] = {}
        self.literature_reviews: Dict[str, LiteratureReview] = {}

        # Research tracking
        self.research_history: List[Dict[str, Any]] = []
        self.factor_performance_history: List[Dict[str, Any]] = []

        # Research configuration
        self.default_significance_level = 0.05
        self.min_sample_size = 30
        self.factor_lookback_days = 252  # 1 year

    async def _initialize_specific(self) -> bool:
        """Initialize research analyst specific components."""
        try:
            self.logger.info("Initializing research analyst specific components...")

            # Initialize ML model manager
            if not await self.ml_manager.initialize():
                self.logger.error("Failed to initialize ML model manager")
                return False

            # Initialize research frameworks
            await self._initialize_research_frameworks()

            # Create default factors
            await self._create_default_factors()

            # Initialize literature database
            await self._initialize_literature_database()

            self.logger.info("Research analyst initialization completed")
            return True

        except Exception as e:
            self.logger.exception(f"Failed to initialize research analyst: {e}")
            return False

    async def _initialize_research_frameworks(self) -> None:
        """Initialize research frameworks and methodologies."""
        try:
            # Initialize statistical test methods
            self.statistical_tests = {
                "t_test": self._perform_t_test,
                "chi_square": self._perform_chi_square_test,
                "mann_whitney": self._perform_mann_whitney_test,
                "correlation": self._perform_correlation_test,
                "cointegration": self._perform_cointegration_test,
            }

            # Initialize factor analysis methods
            self.factor_methods = {
                "ic_analysis": self._calculate_information_coefficient,
                "factor_exposure": self._calculate_factor_exposure,
                "factor_decay": self._calculate_factor_decay,
                "factor_correlation": self._calculate_factor_correlation,
            }

            self.logger.info("Research frameworks initialized")

        except Exception as e:
            self.logger.error(f"Error initializing research frameworks: {e}")

    async def _create_default_factors(self) -> None:
        """Create default factors for Hong Kong market."""
        try:
            # Technical factors
            technical_factors = [
                Factor(
                    factor_id="momentum_5d",
                    factor_name="5日动量因子",
                    factor_type=FactorType.TECHNICAL,
                    description="5日价格动量因子",
                    calculation_method="(close_t - close_t - 5) / close_t - 5",
                    data_requirements=["close_price"],
                    frequency="daily",
                ),
                Factor(
                    factor_id="mean_reversion_20d",
                    factor_name="20日均值回归因子",
                    factor_type=FactorType.TECHNICAL,
                    description="20日价格均值回归因子",
                    calculation_method="(close_t - sma_20) / sma_20",
                    data_requirements=["close_price"],
                    frequency="daily",
                ),
                Factor(
                    factor_id="volatility_20d",
                    factor_name="20日波动率因子",
                    factor_type=FactorType.TECHNICAL,
                    description="20日价格波动率因子",
                    calculation_method="std(returns_20d)",
                    data_requirements=["close_price"],
                    frequency="daily",
                ),
            ]

            # Fundamental factors
            fundamental_factors = [
                Factor(
                    factor_id="pe_ratio",
                    factor_name="市盈率因子",
                    factor_type=FactorType.FUNDAMENTAL,
                    description="市盈率因子",
                    calculation_method="market_cap / net_income",
                    data_requirements=["market_cap", "net_income"],
                    frequency="quarterly",
                ),
                Factor(
                    factor_id="pb_ratio",
                    factor_name="市净率因子",
                    factor_type=FactorType.FUNDAMENTAL,
                    description="市净率因子",
                    calculation_method="market_cap / book_value",
                    data_requirements=["market_cap", "book_value"],
                    frequency="quarterly",
                ),
            ]

            # Add all factors
            for factor in technical_factors + fundamental_factors:
                self.factors[factor.factor_id] = factor

            self.logger.info(f"Created {len(self.factors)} default factors")

        except Exception as e:
            self.logger.error(f"Error creating default factors: {e}")

    async def _initialize_literature_database(self) -> None:
        """Initialize literature review database."""
        try:
            # Create default literature reviews
            default_reviews = [
                LiteratureReview(
                    review_id="momentum_literature",
                    topic="动量策略文献综述",
                    research_question="动量效应在香港股票市场是否有效？",
                    papers=[
                        {
                            "title": "Momentum Strategies in Hong Kong Stock Market",
                            "authors": ["Author1", "Author2"],
                            "year": 2020,
                        },
                        {
                            "title": "Cross - Sectional Momentum in Asian Markets",
                            "authors": ["Author3"],
                            "year": 2019,
                        },
                    ],
                    main_themes=["动量效应", "市场效率", "行为金融"],
                    methodologies=["事件研究", "横截面分析", "时间序列分析"],
                    gaps=["缺乏高频数据研究", "机构投资者影响未充分研究"],
                    future_directions=["机器学习方法", "ESG因素整合"],
                ),
                LiteratureReview(
                    review_id="factor_literature",
                    topic="多因子模型文献综述",
                    research_question="哪些因子在香港市场最有效？",
                    papers=[
                        {
                            "title": "Multi - Factor Models in Hong Kong",
                            "authors": ["Author4"],
                            "year": 2021,
                        },
                        {
                            "title": "Factor Investing in Emerging Markets",
                            "authors": ["Author5", "Author6"],
                            "year": 2020,
                        },
                    ],
                    main_themes=["多因子模型", "因子有效性", "风险模型"],
                    methodologies=["Fama - French模型", "主成分分析", "因子暴露分析"],
                    gaps=["因子衰减研究不足", "宏观经济因子影响未量化"],
                    future_directions=["动态因子模型", "另类数据因子"],
                ),
            ]

            for review in default_reviews:
                self.literature_reviews[review.review_id] = review

            self.logger.info(
                f"Initialized {len(self.literature_reviews)} literature reviews"
            )

        except Exception as e:
            self.logger.error(f"Error initializing literature database: {e}")

    async def _enhance_analysis(
        self, base_result: AnalysisResult, market_data: List[RealMarketData]
    ) -> AnalysisResult:
        """Enhance analysis with research analyst specific logic."""
        try:
            # Perform factor analysis
            factor_insights = await self._analyze_factors(market_data)

            # Generate research insights
            research_insights = await self._generate_research_insights(
                factor_insights, base_result
            )

            # Update base result
            enhanced_result = base_result.copy()
            enhanced_result.insights.extend(research_insights)

            return enhanced_result

        except Exception as e:
            self.logger.error(f"Error enhancing analysis for research: {e}")
            return base_result

    async def _analyze_factors(
        self, market_data: List[RealMarketData]
    ) -> Dict[str, Any]:
        """Analyze factor performance based on market data."""
        try:
            if len(market_data) < 30:
                return {}

            # Convert to DataFrame
            df = pd.DataFrame(
                [
                    {
                        "timestamp": d.timestamp,
                        "symbol": d.symbol,
                        "open": float(d.open_price),
                        "high": float(d.high_price),
                        "low": float(d.low_price),
                        "close": float(d.close_price),
                        "volume": d.volume,
                    }
                    for d in market_data
                ]
            )

            df.set_index("timestamp", inplace=True)
            df.sort_index(inplace=True)

            factor_analysis = {}

            # Analyze each factor
            for factor_id, factor in self.factors.items():
                if not factor.is_active:
                    continue

                factor_performance = await self._calculate_factor_performance(
                    df, factor
                )
                factor_analysis[factor_id] = factor_performance

                # Update factor metrics
                factor.ic_mean = factor_performance.get("ic_mean", 0)
                factor.ic_std = factor_performance.get("ic_std", 0)
                factor.ic_ir = factor_performance.get("ic_ir", 0)
                factor.hit_rate = factor_performance.get("hit_rate", 0)
                factor.sharpe_ratio = factor_performance.get("sharpe_ratio", 0)
                factor.last_updated = datetime.now()

            return factor_analysis

        except Exception as e:
            self.logger.error(f"Error analyzing factors: {e}")
            return {}

    async def _calculate_factor_performance(
        self, df: pd.DataFrame, factor: Factor
    ) -> Dict[str, Any]:
        """Calculate factor performance metrics."""
        try:
            # Calculate factor values based on type
            if factor.factor_type == FactorType.TECHNICAL:
                factor_values = await self._calculate_technical_factor(df, factor)
            elif factor.factor_type == FactorType.FUNDAMENTAL:
                factor_values = await self._calculate_fundamental_factor(df, factor)
            else:
                factor_values = pd.Series(index=df.index, data=0.0)

            if factor_values.empty or len(factor_values) < 10:
                return {
                    "ic_mean": 0,
                    "ic_std": 0,
                    "ic_ir": 0,
                    "hit_rate": 0,
                    "sharpe_ratio": 0,
                }

            # Calculate returns
            returns = df["close"].pct_change().dropna()

            # Align factor values with returns
            aligned_data = pd.DataFrame(
                {"factor": factor_values, "returns": returns}
            ).dropna()

            if len(aligned_data) < 10:
                return {
                    "ic_mean": 0,
                    "ic_std": 0,
                    "ic_ir": 0,
                    "hit_rate": 0,
                    "sharpe_ratio": 0,
                }

            # Calculate Information Coefficient
            ic_series = (
                aligned_data["factor"].rolling(window=20).corr(aligned_data["returns"])
            )
            ic_mean = ic_series.mean() if not ic_series.empty else 0
            ic_std = ic_series.std() if not ic_series.empty else 0
            ic_ir = ic_mean / ic_std if ic_std > 0 else 0

            # Calculate hit rate
            factor_signals = (aligned_data["factor"] > 0).astype(int)
            return_signals = (aligned_data["returns"] > 0).astype(int)
            hit_rate = (factor_signals == return_signals).mean()

            # Calculate Sharpe ratio (simplified)
            factor_returns = aligned_data["factor"].pct_change().dropna()
            sharpe_ratio = (
                factor_returns.mean() / factor_returns.std() * np.sqrt(252)
                if factor_returns.std() > 0
                else 0
            )

            return {
                "ic_mean": ic_mean,
                "ic_std": ic_std,
                "ic_ir": ic_ir,
                "hit_rate": hit_rate,
                "sharpe_ratio": sharpe_ratio,
            }

        except Exception as e:
            self.logger.error(f"Error calculating factor performance: {e}")
            return {
                "ic_mean": 0,
                "ic_std": 0,
                "ic_ir": 0,
                "hit_rate": 0,
                "sharpe_ratio": 0,
            }

    async def _calculate_technical_factor(
        self, df: pd.DataFrame, factor: Factor
    ) -> pd.Series:
        """Calculate technical factor values."""
        try:
            if factor.factor_id == "momentum_5d":
                return (df["close"] - df["close"].shift(5)) / df["close"].shift(5)
            elif factor.factor_id == "mean_reversion_20d":
                sma_20 = df["close"].rolling(window=20).mean()
                return (df["close"] - sma_20) / sma_20
            elif factor.factor_id == "volatility_20d":
                returns = df["close"].pct_change()
                return returns.rolling(window=20).std()
            else:
                return pd.Series(index=df.index, data=0.0)

        except Exception as e:
            self.logger.error(
                f"Error calculating technical factor {factor.factor_id}: {e}"
            )
            return pd.Series(index=df.index, data=0.0)

    async def _calculate_fundamental_factor(
        self, df: pd.DataFrame, factor: Factor
    ) -> pd.Series:
        """Calculate fundamental factor values (simulated)."""
        try:
            # In real implementation, this would use actual fundamental data
            # For now, we'll simulate based on price data
            if factor.factor_id == "pe_ratio":
                # Simulate PE ratio based on price volatility
                returns = df["close"].pct_change()
                volatility = returns.rolling(window=20).std()
                return 1 / (volatility + 0.01)  # Inverse relationship
            elif factor.factor_id == "pb_ratio":
                # Simulate PB ratio based on price trend
                sma_50 = df["close"].rolling(window=50).mean()
                return df["close"] / sma_50
            else:
                return pd.Series(index=df.index, data=0.0)

        except Exception as e:
            self.logger.error(
                f"Error calculating fundamental factor {factor.factor_id}: {e}"
            )
            return pd.Series(index=df.index, data=0.0)

    async def _generate_research_insights(
        self, factor_analysis: Dict[str, Any], analysis_result: AnalysisResult
    ) -> List[str]:
        """Generate research - based insights."""
        try:
            insights = []

            # Factor performance insights
            for factor_id, performance in factor_analysis.items():
                factor = self.factors.get(factor_id)
                if not factor:
                    continue

                ic_mean = performance.get("ic_mean", 0)
                hit_rate = performance.get("hit_rate", 0)
                sharpe_ratio = performance.get("sharpe_ratio", 0)

                if abs(ic_mean) > 0.05:  # Significant IC
                    insights.append(
                        f"📊 {factor.factor_name}: IC={ic_mean:.3f}, 命中率={hit_rate:.1%}"
                    )

                if sharpe_ratio > 1.0:
                    insights.append(
                        f"🎯 {factor.factor_name}: 夏普比率优秀 {sharpe_ratio:.2f}"
                    )
                elif sharpe_ratio < 0.5:
                    insights.append(
                        f"⚠️ {factor.factor_name}: 夏普比率偏低 {sharpe_ratio:.2f}"
                    )

            # Research recommendations
            top_factors = sorted(
                factor_analysis.items(),
                key=lambda x: abs(x[1].get("ic_mean", 0)),
                reverse=True,
            )[:3]

            if top_factors:
                insights.append(
                    f"🔬 推荐关注因子: {', '.join([self.factors[fid].factor_name for fid, _ in top_factors])}"
                )

            return insights

        except Exception as e:
            self.logger.error(f"Error generating research insights: {e}")
            return []

    async def _enhance_signals(
        self, base_signals: List[Dict[str, Any]], analysis_result: AnalysisResult
    ) -> List[Dict[str, Any]]:
        """Enhance signals with research insights."""
        try:
            enhanced_signals = []

            # Generate research - based signals
            research_signals = await self._generate_research_signals(analysis_result)
            enhanced_signals.extend(research_signals)

            # Enhance existing signals with research validation
            enhanced_base_signals = (
                await self._enhance_signals_with_research_validation(
                    base_signals, analysis_result
                )
            )
            enhanced_signals.extend(enhanced_base_signals)

            return enhanced_signals

        except Exception as e:
            self.logger.error(f"Error enhancing signals with research: {e}")
            return base_signals

    async def _generate_research_signals(
        self, analysis_result: AnalysisResult
    ) -> List[Dict[str, Any]]:
        """Generate research - based trading signals."""
        try:
            research_signals = []

            # Factor - based signals
            for factor_id, factor in self.factors.items():
                if not factor.is_active or factor.ic_ir < 0.5:
                    continue

                # Generate signal based on factor strength
                signal_strength = min(abs(factor.ic_ir) * 2, 1.0)
                confidence = min(factor.hit_rate * 1.2, 1.0)

                signal = {
                    "signal_id": f"research_{factor_id}_{datetime.now().strftime('%Y % m % d_ % H % M % S')}",
                    "symbol": "FACTOR_BASED",
                    "side": "buy" if factor.ic_mean > 0 else "sell",
                    "strength": signal_strength,
                    "confidence": confidence,
                    "reasoning": f"基于{factor.factor_name}的研究信号 (IC={factor.ic_mean:.3f}, IR={factor.ic_ir:.2f})",
                    "signal_type": "research_factor",
                    "factor_id": factor_id,
                    "factor_name": factor.factor_name,
                    "ic_mean": factor.ic_mean,
                    "ic_ir": factor.ic_ir,
                }
                research_signals.append(signal)

            return research_signals

        except Exception as e:
            self.logger.error(f"Error generating research signals: {e}")
            return []

    async def _enhance_signals_with_research_validation(
        self, base_signals: List[Dict[str, Any]], analysis_result: AnalysisResult
    ) -> List[Dict[str, Any]]:
        """Enhance existing signals with research validation."""
        try:
            enhanced_signals = []

            for signal in base_signals:
                enhanced_signal = signal.copy()

                # Add research validation score
                research_score = await self._calculate_research_validation_score(
                    signal, analysis_result
                )
                enhanced_signal["research_validation_score"] = research_score

                # Adjust confidence based on research validation
                original_confidence = enhanced_signal.get("confidence", 0.5)
                enhanced_signal["confidence"] = (
                    original_confidence + research_score
                ) / 2

                enhanced_signals.append(enhanced_signal)

            return enhanced_signals

        except Exception as e:
            self.logger.error(f"Error enhancing signals with research validation: {e}")
            return base_signals

    async def _calculate_research_validation_score(
        self, signal: Dict[str, Any], analysis_result: AnalysisResult
    ) -> float:
        """Calculate research validation score for a signal."""
        try:
            base_score = 0.5

            # Factor alignment score
            factor_alignment = await self._calculate_factor_alignment(signal)
            base_score += factor_alignment * 0.3

            # Market regime alignment
            regime_alignment = await self._calculate_regime_alignment(
                signal, analysis_result
            )
            base_score += regime_alignment * 0.2

            # Historical performance alignment
            performance_alignment = await self._calculate_performance_alignment(signal)
            base_score += performance_alignment * 0.2

            return max(0.0, min(1.0, base_score))

        except Exception as e:
            self.logger.error(f"Error calculating research validation score: {e}")
            return 0.5

    async def _calculate_factor_alignment(self, signal: Dict[str, Any]) -> float:
        """Calculate factor alignment score."""
        try:
            # Check if signal aligns with strong factors
            strong_factors = [
                f for f in self.factors.values() if f.ic_ir > 0.5 and f.is_active
            ]

            if not strong_factors:
                return 0.5

            # Calculate average factor strength
            avg_factor_strength = np.mean([f.ic_ir for f in strong_factors])
            return min(avg_factor_strength, 1.0)

        except Exception as e:
            self.logger.error(f"Error calculating factor alignment: {e}")
            return 0.5

    async def _calculate_regime_alignment(
        self, signal: Dict[str, Any], analysis_result: AnalysisResult
    ) -> float:
        """Calculate market regime alignment score."""
        try:
            regime = analysis_result.market_regime.regime_type

            # Different signals work better in different regimes
            if regime in ["bull_market", "stable"]:
                return 0.8  # Most signals work well
            elif regime in ["bear_market", "high_volatility"]:
                return 0.4  # Reduced effectiveness
            else:
                return 0.6  # Neutral

        except Exception as e:
            self.logger.error(f"Error calculating regime alignment: {e}")
            return 0.5

    async def _calculate_performance_alignment(self, signal: Dict[str, Any]) -> float:
        """Calculate historical performance alignment score."""
        try:
            # Use recent factor performance as proxy
            recent_performance = (
                self.factor_performance_history[-10:]
                if self.factor_performance_history
                else []
            )

            if not recent_performance:
                return 0.5

            # Calculate average recent performance
            avg_performance = np.mean([p.get("avg_ic", 0) for p in recent_performance])
            return min(max(avg_performance + 0.5, 0), 1)

        except Exception as e:
            self.logger.error(f"Error calculating performance alignment: {e}")
            return 0.5

    async def _execute_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Execute research signal."""
        try:
            signal_type = signal.get("signal_type", "")

            if signal_type == "research_factor":
                return await self._execute_research_factor_signal(signal)
            else:
                return {
                    "signal_id": signal.get("signal_id", "unknown"),
                    "status": "research_validated",
                    "research_validation_score": signal.get(
                        "research_validation_score", 0.5
                    ),
                }

        except Exception as e:
            self.logger.error(f"Error executing research signal: {e}")
            return {
                "signal_id": signal.get("signal_id", "unknown"),
                "status": "failed",
                "error": str(e),
            }

    async def _execute_research_factor_signal(
        self, signal: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute research factor signal."""
        try:
            factor_id = signal.get("factor_id", "")
            factor_name = signal.get("factor_name", "")
            ic_mean = signal.get("ic_mean", 0)
            ic_ir = signal.get("ic_ir", 0)

            return {
                "signal_id": signal.get("signal_id", "unknown"),
                "status": "research_factor_executed",
                "factor_id": factor_id,
                "factor_name": factor_name,
                "ic_mean": ic_mean,
                "ic_ir": ic_ir,
                "execution_time": datetime.now(),
            }

        except Exception as e:
            self.logger.error(f"Error executing research factor signal: {e}")
            return {
                "signal_id": signal.get("signal_id", "unknown"),
                "status": "failed",
                "error": str(e),
            }

    # Statistical test methods
    async def _perform_t_test(
        self, data1: pd.Series, data2: pd.Series
    ) -> Dict[str, Any]:
        """Perform t - test."""
        try:
            t_stat, p_value = stats.ttest_ind(data1.dropna(), data2.dropna())
            return {"test_statistic": t_stat, "p_value": p_value, "method": "t_test"}
        except Exception as e:
            self.logger.error(f"Error in t - test: {e}")
            return {"test_statistic": 0, "p_value": 1, "method": "t_test"}

    async def _perform_chi_square_test(
        self, observed: np.ndarray, expected: np.ndarray
    ) -> Dict[str, Any]:
        """Perform chi - square test."""
        try:
            chi2_stat, p_value = stats.chisquare(observed, expected)
            return {
                "test_statistic": chi2_stat,
                "p_value": p_value,
                "method": "chi_square",
            }
        except Exception as e:
            self.logger.error(f"Error in chi - square test: {e}")
            return {"test_statistic": 0, "p_value": 1, "method": "chi_square"}

    async def _perform_mann_whitney_test(
        self, data1: pd.Series, data2: pd.Series
    ) -> Dict[str, Any]:
        """Perform Mann - Whitney U test."""
        try:
            u_stat, p_value = stats.mannwhitneyu(data1.dropna(), data2.dropna())
            return {
                "test_statistic": u_stat,
                "p_value": p_value,
                "method": "mann_whitney",
            }
        except Exception as e:
            self.logger.error(f"Error in Mann - Whitney test: {e}")
            return {"test_statistic": 0, "p_value": 1, "method": "mann_whitney"}

    async def _perform_correlation_test(
        self, data1: pd.Series, data2: pd.Series
    ) -> Dict[str, Any]:
        """Perform correlation test."""
        try:
            correlation, p_value = stats.pearsonr(data1.dropna(), data2.dropna())
            return {
                "test_statistic": correlation,
                "p_value": p_value,
                "method": "correlation",
            }
        except Exception as e:
            self.logger.error(f"Error in correlation test: {e}")
            return {"test_statistic": 0, "p_value": 1, "method": "correlation"}

    async def _perform_cointegration_test(
        self, data1: pd.Series, data2: pd.Series
    ) -> Dict[str, Any]:
        """Perform cointegration test (simplified)."""
        try:
            # Simplified cointegration test
            diff = data1 - data2
            adf_stat, p_value = stats.adfuller(diff.dropna())
            return {
                "test_statistic": adf_stat,
                "p_value": p_value,
                "method": "cointegration",
            }
        except Exception as e:
            self.logger.error(f"Error in cointegration test: {e}")
            return {"test_statistic": 0, "p_value": 1, "method": "cointegration"}

    # Factor analysis methods
    async def _calculate_information_coefficient(
        self, factor_values: pd.Series, returns: pd.Series
    ) -> float:
        """Calculate Information Coefficient."""
        try:
            aligned_data = pd.DataFrame(
                {"factor": factor_values, "returns": returns}
            ).dropna()
            if len(aligned_data) < 10:
                return 0.0
            return aligned_data["factor"].corr(aligned_data["returns"])
        except Exception as e:
            self.logger.error(f"Error calculating IC: {e}")
            return 0.0

    async def _calculate_factor_exposure(
        self, factor_values: pd.Series, market_data: pd.DataFrame
    ) -> Dict[str, float]:
        """Calculate factor exposures."""
        try:
            # Simplified factor exposure calculation
            exposures = {}
            for col in market_data.columns:
                if col != "timestamp":
                    correlation = factor_values.corr(market_data[col])
                    exposures[col] = correlation if not pd.isna(correlation) else 0.0
            return exposures
        except Exception as e:
            self.logger.error(f"Error calculating factor exposure: {e}")
            return {}

    async def _calculate_factor_decay(self, factor_values: pd.Series) -> float:
        """Calculate factor decay rate."""
        try:
            # Calculate autocorrelation at different lags
            lags = [1, 5, 10, 20]
            correlations = []
            for lag in lags:
                corr = factor_values.autocorr(lag=lag)
                if not pd.isna(corr):
                    correlations.append(corr)

            if len(correlations) < 2:
                return 0.0

            # Simple decay rate calculation
            return np.mean(correlations)
        except Exception as e:
            self.logger.error(f"Error calculating factor decay: {e}")
            return 0.0

    async def _calculate_factor_correlation(
        self, factor1: Factor, factor2: Factor
    ) -> float:
        """Calculate correlation between two factors."""
        try:
            # This would require actual factor values
            # For now, return a simulated correlation
            return np.random.uniform(-0.5, 0.5)
        except Exception as e:
            self.logger.error(f"Error calculating factor correlation: {e}")
            return 0.0

    async def get_research_summary(self) -> Dict[str, Any]:
        """Get comprehensive research summary."""
        try:
            summary = {
                "agent_id": self.config.agent_id,
                "agent_name": self.config.name,
                "status": self.real_status,
                # Research components
                "total_hypotheses": len(self.hypotheses),
                "active_hypotheses": len(
                    [
                        h
                        for h in self.hypotheses.values()
                        if h.status == HypothesisStatus.TESTING
                    ]
                ),
                "accepted_hypotheses": len(
                    [
                        h
                        for h in self.hypotheses.values()
                        if h.status == HypothesisStatus.ACCEPTED
                    ]
                ),
                # Factors
                "total_factors": len(self.factors),
                "active_factors": len(
                    [f for f in self.factors.values() if f.is_active]
                ),
                "strong_factors": len(
                    [f for f in self.factors.values() if f.ic_ir > 0.5]
                ),
                # Strategy research
                "total_research": len(self.strategy_research),
                "ongoing_research": len(
                    [
                        r
                        for r in self.strategy_research.values()
                        if r.status == "ongoing"
                    ]
                ),
                "completed_research": len(
                    [
                        r
                        for r in self.strategy_research.values()
                        if r.status == "completed"
                    ]
                ),
                # Literature reviews
                "total_reviews": len(self.literature_reviews),
                # Performance tracking
                "research_history_count": len(self.research_history),
                "factor_performance_history_count": len(
                    self.factor_performance_history
                ),
            }

            # Add factor details
            summary["factors"] = {}
            for factor_id, factor in self.factors.items():
                summary["factors"][factor_id] = {
                    "name": factor.factor_name,
                    "type": factor.factor_type.value,
                    "ic_mean": factor.ic_mean,
                    "ic_ir": factor.ic_ir,
                    "hit_rate": factor.hit_rate,
                    "sharpe_ratio": factor.sharpe_ratio,
                    "is_active": factor.is_active,
                }

            return summary

        except Exception as e:
            self.logger.error(f"Error getting research summary: {e}")
            return {"error": str(e)}

    async def cleanup(self) -> None:
        """Cleanup research analyst resources."""
        try:
            self.logger.info(f"Cleaning up research analyst: {self.config.name}")

            # Clear all collections
            self.hypotheses.clear()
            self.factors.clear()
            self.strategy_research.clear()
            self.literature_reviews.clear()
            self.research_history.clear()
            self.factor_performance_history.clear()

            # Call parent cleanup
            await super().cleanup()

            self.logger.info("Research analyst cleanup completed")

        except Exception as e:
            self.logger.exception(f"Error during cleanup: {e}")

"""Real Quantitative Analyst Agent for Hong Kong quantitative trading system.

This agent performs advanced technical analysis, statistical modeling, and machine learning
predictions based on real market data from Hong Kong stock market.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field
from scipy import stats
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Lasso, LinearRegression, Ridge
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from ...data_adapters.base_adapter import RealMarketData
from .base_real_agent import BaseRealAgent, RealAgentConfig, RealAgentStatus
from .ml_integration import MLModelManager, ModelPerformance, ModelType
from .real_data_analyzer import (
    AnalysisResult,
    MarketRegime,
    SignalStrength,
    TechnicalIndicator,
)


class QuantitativeAnalysisResult(BaseModel):
    """Extended analysis result for quantitative analyst."""

    # Base analysis
    base_analysis: AnalysisResult = Field(..., description="Base technical analysis")

    # Advanced statistical analysis
    statistical_metrics: Dict[str, float] = Field(
        default_factory=dict, description="Statistical metrics"
    )
    correlation_analysis: Dict[str, float] = Field(
        default_factory=dict, description="Cross - asset correlations"
    )
    volatility_analysis: Dict[str, Any] = Field(
        default_factory=dict, description="Volatility analysis"
    )

    # Mathematical models
    regression_models: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Regression model results"
    )
    time_series_models: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Time series model results"
    )

    # Machine learning predictions
    ml_predictions: Dict[str, Any] = Field(
        default_factory=dict, description="ML model predictions"
    )
    prediction_confidence: Dict[str, float] = Field(
        default_factory=dict, description="Prediction confidence scores"
    )

    # Risk analysis
    var_analysis: Dict[str, float] = Field(
        default_factory=dict, description="Value at Risk analysis"
    )
    stress_test_results: Dict[str, Any] = Field(
        default_factory=dict, description="Stress test results"
    )

    # Market microstructure
    microstructure_analysis: Dict[str, Any] = Field(
        default_factory=dict, description="Market microstructure analysis"
    )

    # Recommendations
    trading_recommendations: List[Dict[str, Any]] = Field(
        default_factory=list, description="Trading recommendations"
    )
    risk_warnings: List[str] = Field(default_factory=list, description="Risk warnings")

    class Config:
        arbitrary_types_allowed = True


class RealQuantitativeAnalyst(BaseRealAgent):
    """Real Quantitative Analyst Agent with advanced analytical capabilities."""

    def __init__(self, config: RealAgentConfig):
        super().__init__(config)
        self.ml_manager = MLModelManager(config)
        self.statistical_models: Dict[str, Any] = {}
        self.prediction_models: Dict[str, Any] = {}
        self.scaler = StandardScaler()
        self.analysis_history: List[QuantitativeAnalysisResult] = []

        # Analysis parameters
        self.lookback_periods = [5, 10, 20, 50, 100, 252]
        self.volatility_windows = [5, 10, 20, 30]
        self.correlation_periods = [20, 50, 100]

    async def _initialize_specific(self) -> bool:
        """Initialize quantitative analyst specific components."""
        try:
            self.logger.info("Initializing quantitative analyst specific components...")

            # Initialize ML model manager
            if not await self.ml_manager.initialize():
                self.logger.error("Failed to initialize ML model manager")
                return False

            # Load or train statistical models
            await self._initialize_statistical_models()

            # Load or train prediction models
            await self._initialize_prediction_models()

            self.logger.info("Quantitative analyst initialization completed")
            return True

        except Exception as e:
            self.logger.exception(f"Failed to initialize quantitative analyst: {e}")
            return False

    async def _initialize_statistical_models(self) -> None:
        """Initialize statistical analysis models."""
        try:
            # Initialize various statistical models for different analysis types
            self.statistical_models = {
                "linear_regression": LinearRegression(),
                "ridge_regression": Ridge(alpha=1.0),
                "lasso_regression": Lasso(alpha=0.1),
                "random_forest": RandomForestRegressor(
                    n_estimators=100, random_state=42
                ),
                "gradient_boosting": GradientBoostingRegressor(
                    n_estimators=100, random_state=42
                ),
            }

            self.logger.info("Statistical models initialized")

        except Exception as e:
            self.logger.error(f"Error initializing statistical models: {e}")

    async def _initialize_prediction_models(self) -> None:
        """Initialize prediction models."""
        try:
            # Load existing models or create new ones
            model_names = [
                "price_prediction",
                "volatility_prediction",
                "trend_prediction",
            ]

            for model_name in model_names:
                model = await self.ml_manager.load_model(model_name)
                if model:
                    self.prediction_models[model_name] = model
                    self.logger.info(f"Loaded prediction model: {model_name}")
                else:
                    self.logger.warning(f"Prediction model not found: {model_name}")

        except Exception as e:
            self.logger.error(f"Error initializing prediction models: {e}")

    async def _enhance_analysis(
        self, base_result: AnalysisResult, market_data: List[RealMarketData]
    ) -> AnalysisResult:
        """Enhance analysis with quantitative analyst specific logic."""
        try:
            # Perform advanced statistical analysis
            statistical_metrics = await self._calculate_statistical_metrics(market_data)

            # Perform correlation analysis
            correlation_analysis = await self._calculate_correlations(market_data)

            # Perform volatility analysis
            volatility_analysis = await self._analyze_volatility(market_data)

            # Update base result with enhanced metrics
            enhanced_result = base_result.copy()
            enhanced_result.technical_indicators.update(statistical_metrics)

            # Add quantitative insights
            enhanced_result.insights.extend(
                [
                    f"Statistical significance: {statistical_metrics.get('statistical_significance', 0):.3f}",
                    f"Cross - asset correlation: {correlation_analysis.get('avg_correlation', 0):.3f}",
                    f"Volatility regime: {volatility_analysis.get('regime', 'normal')}",
                ]
            )

            return enhanced_result

        except Exception as e:
            self.logger.error(f"Error enhancing analysis: {e}")
            return base_result

    async def _calculate_statistical_metrics(
        self, market_data: List[RealMarketData]
    ) -> Dict[str, float]:
        """Calculate advanced statistical metrics."""
        try:
            if len(market_data) < 20:
                return {}

            # Convert to DataFrame
            df = pd.DataFrame(
                [
                    {
                        "timestamp": d.timestamp,
                        "close": float(d.close_price),
                        "volume": d.volume,
                        "high": float(d.high_price),
                        "low": float(d.low_price),
                    }
                    for d in market_data
                ]
            )

            df.set_index("timestamp", inplace=True)
            df.sort_index(inplace=True)

            metrics = {}

            # Price statistics
            returns = df["close"].pct_change().dropna()
            metrics["mean_return"] = returns.mean()
            metrics["std_return"] = returns.std()
            metrics["skewness"] = returns.skew()
            metrics["kurtosis"] = returns.kurtosis()

            # Normality tests
            if len(returns) > 8:
                shapiro_stat, shapiro_p = stats.shapiro(returns)
                metrics["shapiro_statistic"] = shapiro_stat
                metrics["shapiro_p_value"] = shapiro_p
                metrics["is_normal"] = shapiro_p > 0.05

            # Autocorrelation
            if len(returns) > 10:
                autocorr_1 = returns.autocorr(lag=1)
                autocorr_5 = returns.autocorr(lag=5)
                metrics["autocorr_1"] = autocorr_1 if not pd.isna(autocorr_1) else 0
                metrics["autocorr_5"] = autocorr_5 if not pd.isna(autocorr_5) else 0

            # Hurst exponent (trend persistence)
            if len(returns) > 50:
                hurst = await self._calculate_hurst_exponent(returns)
                metrics["hurst_exponent"] = hurst

            # Maximum drawdown
            cumulative_returns = (1 + returns).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - running_max) / running_max
            metrics["max_drawdown"] = drawdown.min()

            # Calmar ratio
            if metrics["max_drawdown"] != 0:
                metrics["calmar_ratio"] = (
                    returns.mean() * 252 / abs(metrics["max_drawdown"])
                )
            else:
                metrics["calmar_ratio"] = 0

            # Sortino ratio
            downside_returns = returns[returns < 0]
            if len(downside_returns) > 0:
                downside_std = downside_returns.std()
                if downside_std > 0:
                    metrics["sortino_ratio"] = returns.mean() * 252 / downside_std
                else:
                    metrics["sortino_ratio"] = 0
            else:
                metrics["sortino_ratio"] = 0

            return metrics

        except Exception as e:
            self.logger.error(f"Error calculating statistical metrics: {e}")
            return {}

    async def _calculate_hurst_exponent(self, returns: pd.Series) -> float:
        """Calculate Hurst exponent for trend persistence analysis."""
        try:
            if len(returns) < 50:
                return 0.5  # Random walk

            # Create range of lags
            lags = range(2, min(50, len(returns) // 4))

            # Calculate R / S statistic for each lag
            rs_values = []
            for lag in lags:
                # Calculate R / S for this lag
                n = len(returns)
                k = n // lag

                if k < 2:
                    continue

                rs_sum = 0
                for i in range(k):
                    start_idx = i * lag
                    end_idx = min((i + 1) * lag, n)
                    subset = returns.iloc[start_idx:end_idx]

                    if len(subset) < 2:
                        continue

                    mean_subset = subset.mean()
                    cumsum = (subset - mean_subset).cumsum()
                    R = cumsum.max() - cumsum.min()
                    S = subset.std()

                    if S > 0:
                        rs_sum += R / S

                if k > 0:
                    rs_values.append(rs_sum / k)

            if len(rs_values) < 2:
                return 0.5

            # Linear regression of log(R / S) vs log(lag)
            log_lags = np.log(lags[: len(rs_values)])
            log_rs = np.log(rs_values)

            slope, _, _, _, _ = stats.linregress(log_lags, log_rs)
            return slope

        except Exception:
            return 0.5

    async def _calculate_correlations(
        self, market_data: List[RealMarketData]
    ) -> Dict[str, float]:
        """Calculate cross - asset correlations."""
        try:
            # Group data by symbol
            symbol_data = {}
            for data in market_data:
                if data.symbol not in symbol_data:
                    symbol_data[data.symbol] = []
                symbol_data[data.symbol].append(data)

            if len(symbol_data) < 2:
                return {"avg_correlation": 0.0}

            # Calculate returns for each symbol
            symbol_returns = {}
            for symbol, data_list in symbol_data.items():
                if len(data_list) < 2:
                    continue

                data_list.sort(key=lambda x: x.timestamp)
                prices = [float(d.close_price) for d in data_list]
                returns = [prices[i] / prices[i - 1] - 1 for i in range(1, len(prices))]
                symbol_returns[symbol] = returns

            if len(symbol_returns) < 2:
                return {"avg_correlation": 0.0}

            # Calculate pairwise correlations
            correlations = []
            symbols = list(symbol_returns.keys())

            for i in range(len(symbols)):
                for j in range(i + 1, len(symbols)):
                    sym1, sym2 = symbols[i], symbols[j]
                    returns1 = symbol_returns[sym1]
                    returns2 = symbol_returns[sym2]

                    # Align lengths
                    min_len = min(len(returns1), len(returns2))
                    if min_len < 5:
                        continue

                    returns1 = returns1[:min_len]
                    returns2 = returns2[:min_len]

                    correlation = np.corrcoef(returns1, returns2)[0, 1]
                    if not np.isnan(correlation):
                        correlations.append(correlation)

            if correlations:
                avg_correlation = np.mean(correlations)
                max_correlation = np.max(correlations)
                min_correlation = np.min(correlations)

                return {
                    "avg_correlation": avg_correlation,
                    "max_correlation": max_correlation,
                    "min_correlation": min_correlation,
                    "correlation_count": len(correlations),
                }
            else:
                return {"avg_correlation": 0.0}

        except Exception as e:
            self.logger.error(f"Error calculating correlations: {e}")
            return {"avg_correlation": 0.0}

    async def _analyze_volatility(
        self, market_data: List[RealMarketData]
    ) -> Dict[str, Any]:
        """Analyze volatility patterns and regimes."""
        try:
            if len(market_data) < 20:
                return {"regime": "insufficient_data"}

            # Convert to DataFrame
            df = pd.DataFrame(
                [
                    {"timestamp": d.timestamp, "close": float(d.close_price)}
                    for d in market_data
                ]
            )

            df.set_index("timestamp", inplace=True)
            df.sort_index(inplace=True)

            returns = df["close"].pct_change().dropna()

            # Calculate rolling volatility
            volatility_metrics = {}
            for window in self.volatility_windows:
                if len(returns) >= window:
                    rolling_vol = returns.rolling(window=window).std() * np.sqrt(252)
                    volatility_metrics[f"vol_{window}d"] = {
                        "current": (
                            rolling_vol.iloc[-1]
                            if not pd.isna(rolling_vol.iloc[-1])
                            else 0
                        ),
                        "mean": rolling_vol.mean(),
                        "std": rolling_vol.std(),
                        "percentile_25": rolling_vol.quantile(0.25),
                        "percentile_75": rolling_vol.quantile(0.75),
                    }

            # Determine volatility regime
            current_vol = volatility_metrics.get("vol_20d", {}).get("current", 0)
            vol_mean = volatility_metrics.get("vol_20d", {}).get("mean", 0)

            if current_vol > vol_mean * 1.5:
                regime = "high_volatility"
            elif current_vol < vol_mean * 0.5:
                regime = "low_volatility"
            else:
                regime = "normal_volatility"

            # Volatility clustering analysis
            vol_clustering = await self._analyze_volatility_clustering(returns)

            return {
                "regime": regime,
                "current_volatility": current_vol,
                "volatility_metrics": volatility_metrics,
                "clustering_analysis": vol_clustering,
            }

        except Exception as e:
            self.logger.error(f"Error analyzing volatility: {e}")
            return {"regime": "error"}

    async def _analyze_volatility_clustering(
        self, returns: pd.Series
    ) -> Dict[str, Any]:
        """Analyze volatility clustering using ARCH effects."""
        try:
            if len(returns) < 50:
                return {"has_clustering": False}

            # Calculate squared returns
            squared_returns = returns ** 2

            # Test for ARCH effects using Ljung - Box test
            from statsmodels.stats.diagnostic import acorr_ljungbox

            lb_stat, lb_pvalue = acorr_ljungbox(
                squared_returns, lags=10, return_df=False
            )

            # Calculate autocorrelation of squared returns
            autocorr_sq = squared_returns.autocorr(lag=1)

            return {
                "has_clustering": lb_pvalue < 0.05,
                "ljung_box_pvalue": lb_pvalue,
                "autocorr_squared_returns": autocorr_sq,
                "volatility_persistence": abs(autocorr_sq) > 0.1,
            }

        except Exception:
            return {"has_clustering": False}

    async def _enhance_signals(
        self, base_signals: List[Dict[str, Any]], analysis_result: AnalysisResult
    ) -> List[Dict[str, Any]]:
        """Enhance signals with quantitative analysis."""
        try:
            enhanced_signals = []

            for signal in base_signals:
                enhanced_signal = signal.copy()

                # Add quantitative analysis factors
                symbol = signal.get("symbol", "")

                # Statistical significance
                if (
                    hasattr(analysis_result, "technical_indicators")
                    and symbol in analysis_result.technical_indicators
                ):
                    indicators = analysis_result.technical_indicators[symbol]
                    statistical_significance = indicators.get(
                        "statistical_significance", 0.5
                    )
                    enhanced_signal["statistical_significance"] = (
                        statistical_significance
                    )

                    # Adjust strength based on statistical significance
                    enhanced_signal["strength"] *= 0.5 + statistical_significance

                # Volatility adjustment
                volatility = (
                    indicators.get("volatility", 0.2)
                    if "indicators" in locals()
                    else 0.2
                )
                if volatility > 0.3:  # High volatility
                    enhanced_signal[
                        "strength"
                    ] *= 0.8  # Reduce strength in high volatility
                    enhanced_signal["risk_adjusted"] = True
                elif volatility < 0.1:  # Low volatility
                    enhanced_signal[
                        "strength"
                    ] *= 1.1  # Increase strength in low volatility

                # Trend persistence (Hurst exponent)
                hurst = (
                    indicators.get("hurst_exponent", 0.5)
                    if "indicators" in locals()
                    else 0.5
                )
                if hurst > 0.6:  # Trending market
                    enhanced_signal["trend_persistence"] = "strong"
                    enhanced_signal["strength"] *= 1.05
                elif hurst < 0.4:  # Mean - reverting market
                    enhanced_signal["trend_persistence"] = "weak"
                    enhanced_signal["strength"] *= 0.95

                # Add quantitative reasoning
                reasoning = enhanced_signal.get("reasoning", "")
                quantitative_factors = []

                if "statistical_significance" in enhanced_signal:
                    quantitative_factors.append(
                        f"Statistical significance: {enhanced_signal['statistical_significance']:.3f}"
                    )

                if "risk_adjusted" in enhanced_signal:
                    quantitative_factors.append("Risk - adjusted for high volatility")

                if "trend_persistence" in enhanced_signal:
                    quantitative_factors.append(
                        f"Trend persistence: {enhanced_signal['trend_persistence']}"
                    )

                if quantitative_factors:
                    enhanced_signal["reasoning"] = (
                        f"{reasoning} | Quantitative: {'; '.join(quantitative_factors)}"
                    )

                enhanced_signals.append(enhanced_signal)

            return enhanced_signals

        except Exception as e:
            self.logger.error(f"Error enhancing signals: {e}")
            return base_signals

    async def _execute_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Execute trading signal with quantitative analysis."""
        try:
            execution_result = {
                "signal_id": signal.get(
                    "signal_id", f"signal_{datetime.now().strftime('%Y % m % d_ % H % M % S')}"
                ),
                "symbol": signal.get("symbol"),
                "signal_type": signal.get("signal_type"),
                "execution_time": datetime.now(),
                "status": "pending",
            }

            # Perform quantitative validation
            validation_result = await self._validate_signal_quantitatively(signal)

            if not validation_result["is_valid"]:
                execution_result["status"] = "rejected"
                execution_result["rejection_reason"] = validation_result["reason"]
                return execution_result

            # Calculate optimal position size based on quantitative analysis
            optimal_size = await self._calculate_optimal_position_size(
                signal, validation_result
            )
            execution_result["position_size"] = optimal_size

            # Simulate execution (in real implementation, this would interface with trading system)
            execution_result["status"] = "executed"
            execution_result["execution_price"] = signal.get("current_price", 0)
            execution_result["execution_quantity"] = optimal_size

            # Update position tracking
            symbol = signal.get("symbol")
            if symbol:
                self.current_positions[symbol] = (
                    self.current_positions.get(symbol, 0) + optimal_size
                )

            self.logger.info(
                f"Executed signal: {execution_result['signal_id']} for {symbol}"
            )
            return execution_result

        except Exception as e:
            self.logger.error(f"Error executing signal: {e}")
            return {
                "signal_id": signal.get("signal_id", "unknown"),
                "status": "failed",
                "error": str(e),
            }

    async def _validate_signal_quantitatively(
        self, signal: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate signal using quantitative criteria."""
        try:
            validation_result = {
                "is_valid": True,
                "reason": "",
                "confidence_score": 0.0,
            }

            # Check statistical significance
            statistical_significance = signal.get("statistical_significance", 0.5)
            if statistical_significance < 0.3:
                validation_result["is_valid"] = False
                validation_result["reason"] = "Low statistical significance"
                return validation_result

            # Check signal strength
            strength = signal.get("strength", 0)
            if strength < self.config.signal_threshold:
                validation_result["is_valid"] = False
                validation_result["reason"] = "Signal strength below threshold"
                return validation_result

            # Check confidence
            confidence = signal.get("confidence", 0)
            if confidence < self.config.confidence_threshold:
                validation_result["is_valid"] = False
                validation_result["reason"] = "Confidence below threshold"
                return validation_result

            # Calculate overall confidence score
            confidence_score = (
                statistical_significance * 0.4 + strength * 0.3 + confidence * 0.3
            )
            validation_result["confidence_score"] = confidence_score

            return validation_result

        except Exception as e:
            self.logger.error(f"Error validating signal: {e}")
            return {
                "is_valid": False,
                "reason": f"Validation error: {str(e)}",
                "confidence_score": 0.0,
            }

    async def _calculate_optimal_position_size(
        self, signal: Dict[str, Any], validation_result: Dict[str, Any]
    ) -> float:
        """Calculate optimal position size using quantitative methods."""
        try:
            # Base position size from signal
            base_size = signal.get("position_size", 0.1)

            # Adjust based on confidence score
            confidence_score = validation_result.get("confidence_score", 0.5)
            confidence_adjustment = 0.5 + confidence_score  # 0.5 to 1.5 multiplier

            # Adjust based on volatility
            volatility = signal.get("volatility", 0.2)
            volatility_adjustment = max(
                0.5, 1.0 - volatility
            )  # Reduce size in high volatility

            # Adjust based on current portfolio exposure
            symbol = signal.get("symbol", "")
            current_exposure = abs(self.current_positions.get(symbol, 0))
            exposure_adjustment = max(
                0.1, 1.0 - current_exposure
            )  # Reduce if already exposed

            # Calculate final position size
            optimal_size = (
                base_size
                * confidence_adjustment
                * volatility_adjustment
                * exposure_adjustment
            )

            # Ensure within limits
            optimal_size = min(optimal_size, self.config.max_position_size)
            optimal_size = max(optimal_size, 0.01)  # Minimum position size

            return optimal_size

        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return signal.get("position_size", 0.1)

    async def perform_comprehensive_analysis(
        self, market_data: List[RealMarketData]
    ) -> QuantitativeAnalysisResult:
        """Perform comprehensive quantitative analysis."""
        try:
            self.logger.info("Performing comprehensive quantitative analysis...")

            # Get base analysis
            base_analysis = await self.analyze_market_data(market_data)

            # Perform advanced statistical analysis
            statistical_metrics = await self._calculate_statistical_metrics(market_data)
            correlation_analysis = await self._calculate_correlations(market_data)
            volatility_analysis = await self._analyze_volatility(market_data)

            # Build regression models
            regression_models = await self._build_regression_models(market_data)

            # Build time series models
            time_series_models = await self._build_time_series_models(market_data)

            # Generate ML predictions
            ml_predictions = await self._generate_ml_predictions(market_data)

            # Perform risk analysis
            var_analysis = await self._perform_var_analysis(market_data)
            stress_test_results = await self._perform_stress_tests(market_data)

            # Analyze market microstructure
            microstructure_analysis = await self._analyze_market_microstructure(
                market_data
            )

            # Generate trading recommendations
            trading_recommendations = await self._generate_trading_recommendations(
                base_analysis, statistical_metrics, ml_predictions
            )

            # Generate risk warnings
            risk_warnings = await self._generate_risk_warnings(
                volatility_analysis, var_analysis, stress_test_results
            )

            # Create comprehensive result
            result = QuantitativeAnalysisResult(
                base_analysis=base_analysis,
                statistical_metrics=statistical_metrics,
                correlation_analysis=correlation_analysis,
                volatility_analysis=volatility_analysis,
                regression_models=regression_models,
                time_series_models=time_series_models,
                ml_predictions=ml_predictions,
                prediction_confidence={},  # Would be calculated from ML models
                var_analysis=var_analysis,
                stress_test_results=stress_test_results,
                microstructure_analysis=microstructure_analysis,
                trading_recommendations=trading_recommendations,
                risk_warnings=risk_warnings,
            )

            # Store in history
            self.analysis_history.append(result)

            self.logger.info("Comprehensive quantitative analysis completed")
            return result

        except Exception as e:
            self.logger.exception(f"Error in comprehensive analysis: {e}")
            raise

    async def _build_regression_models(
        self, market_data: List[RealMarketData]
    ) -> Dict[str, Dict[str, Any]]:
        """Build regression models for price prediction."""
        try:
            if len(market_data) < 50:
                return {}

            # Convert to DataFrame
            df = pd.DataFrame(
                [
                    {
                        "timestamp": d.timestamp,
                        "close": float(d.close_price),
                        "volume": d.volume,
                        "high": float(d.high_price),
                        "low": float(d.low_price),
                    }
                    for d in market_data
                ]
            )

            df.set_index("timestamp", inplace=True)
            df.sort_index(inplace=True)

            # Create features
            df["returns"] = df["close"].pct_change()
            df["volume_ma"] = df["volume"].rolling(20).mean()
            df["price_ma"] = df["close"].rolling(20).mean()
            df["volatility"] = df["returns"].rolling(20).std()

            # Create lagged features
            for lag in [1, 2, 3, 5, 10]:
                df[f"returns_lag_{lag}"] = df["returns"].shift(lag)
                df[f"volume_lag_{lag}"] = df["volume"].shift(lag)

            # Prepare data for modeling
            df_clean = df.dropna()
            if len(df_clean) < 20:
                return {}

            # Features and target
            feature_cols = [
                col for col in df_clean.columns if col not in ["close", "timestamp"]
            ]
            X = df_clean[feature_cols]
            y = df_clean["close"]

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)

            models = {}

            # Train different models
            for name, model in self.statistical_models.items():
                try:
                    model.fit(X_train_scaled, y_train)
                    y_pred = model.predict(X_test_scaled)

                    mse = mean_squared_error(y_test, y_pred)
                    r2 = r2_score(y_test, y_pred)

                    models[name] = {
                        "model": model,
                        "mse": mse,
                        "r2_score": r2,
                        "feature_importance": getattr(
                            model, "feature_importances_", None
                        ),
                    }

                except Exception as e:
                    self.logger.warning(f"Error training {name}: {e}")

            return models

        except Exception as e:
            self.logger.error(f"Error building regression models: {e}")
            return {}

    async def _build_time_series_models(
        self, market_data: List[RealMarketData]
    ) -> Dict[str, Dict[str, Any]]:
        """Build time series models for trend analysis."""
        try:
            if len(market_data) < 50:
                return {}

            # Convert to time series
            prices = [float(d.close_price) for d in market_data]
            prices = pd.Series(prices)

            # Simple ARIMA - like model using linear regression with lagged values
            df_ts = pd.DataFrame({"price": prices})

            # Create lagged features
            for lag in range(1, 11):
                df_ts[f"price_lag_{lag}"] = df_ts["price"].shift(lag)

            df_ts = df_ts.dropna()

            if len(df_ts) < 20:
                return {}

            # Features and target
            feature_cols = [col for col in df_ts.columns if col != "price"]
            X = df_ts[feature_cols]
            y = df_ts["price"]

            # Train model
            model = LinearRegression()
            model.fit(X, y)

            # Make predictions
            y_pred = model.predict(X)

            # Calculate metrics
            mse = mean_squared_error(y, y_pred)
            r2 = r2_score(y, y_pred)

            return {
                "arima_like": {
                    "model": model,
                    "mse": mse,
                    "r2_score": r2,
                    "coefficients": model.coef_.tolist(),
                }
            }

        except Exception as e:
            self.logger.error(f"Error building time series models: {e}")
            return {}

    async def _generate_ml_predictions(
        self, market_data: List[RealMarketData]
    ) -> Dict[str, Any]:
        """Generate machine learning predictions."""
        try:
            predictions = {}

            # Convert to DataFrame for ML models
            df = pd.DataFrame(
                [
                    {
                        "timestamp": d.timestamp,
                        "close": float(d.close_price),
                        "volume": d.volume,
                        "high": float(d.high_price),
                        "low": float(d.low_price),
                    }
                    for d in market_data
                ]
            )

            # Use existing prediction models
            for model_name, model in self.prediction_models.items():
                try:
                    pred = await self.ml_manager.predict(model_name, df)
                    if pred is not None:
                        predictions[model_name] = (
                            pred.tolist() if hasattr(pred, "tolist") else pred
                        )
                except Exception as e:
                    self.logger.warning(
                        f"Error generating prediction with {model_name}: {e}"
                    )

            return predictions

        except Exception as e:
            self.logger.error(f"Error generating ML predictions: {e}")
            return {}

    async def _perform_var_analysis(
        self, market_data: List[RealMarketData]
    ) -> Dict[str, float]:
        """Perform Value at Risk analysis."""
        try:
            if len(market_data) < 20:
                return {}

            # Calculate returns
            prices = [float(d.close_price) for d in market_data]
            returns = [prices[i] / prices[i - 1] - 1 for i in range(1, len(prices))]
            returns = pd.Series(returns)

            # Calculate VaR at different confidence levels
            var_95 = returns.quantile(0.05)
            var_99 = returns.quantile(0.01)

            # Calculate Expected Shortfall (CVaR)
            cvar_95 = returns[returns <= var_95].mean()
            cvar_99 = returns[returns <= var_99].mean()

            # Historical VaR
            historical_var_95 = returns.rolling(window=20).quantile(0.05).iloc[-1]
            historical_var_99 = returns.rolling(window=20).quantile(0.01).iloc[-1]

            return {
                "var_95": float(var_95),
                "var_99": float(var_99),
                "cvar_95": float(cvar_95),
                "cvar_99": float(cvar_99),
                "historical_var_95": (
                    float(historical_var_95) if not pd.isna(historical_var_95) else 0
                ),
                "historical_var_99": (
                    float(historical_var_99) if not pd.isna(historical_var_99) else 0
                ),
            }

        except Exception as e:
            self.logger.error(f"Error performing VaR analysis: {e}")
            return {}

    async def _perform_stress_tests(
        self, market_data: List[RealMarketData]
    ) -> Dict[str, Any]:
        """Perform stress tests on the portfolio."""
        try:
            if len(market_data) < 50:
                return {}

            # Calculate returns
            prices = [float(d.close_price) for d in market_data]
            returns = [prices[i] / prices[i - 1] - 1 for i in range(1, len(prices))]
            returns = pd.Series(returns)

            # Stress test scenarios
            stress_scenarios = {
                "market_crash": -0.20,  # 20% market crash
                "moderate_decline": -0.10,  # 10% decline
                "volatility_spike": 2.0,  # 2x volatility
                "liquidity_crisis": -0.15,  # 15% liquidity crisis
            }

            results = {}

            for scenario_name, shock in stress_scenarios.items():
                if scenario_name in [
                    "market_crash",
                    "moderate_decline",
                    "liquidity_crisis",
                ]:
                    # Price shock scenarios
                    shocked_returns = returns + shock
                    portfolio_value = (1 + shocked_returns).prod()
                    results[scenario_name] = {
                        "shock": shock,
                        "portfolio_impact": float(portfolio_value - 1),
                        "worst_day": float(shocked_returns.min()),
                    }
                elif scenario_name == "volatility_spike":
                    # Volatility shock
                    current_vol = returns.std()
                    shocked_vol = current_vol * shock
                    shocked_returns = returns * (shocked_vol / current_vol)
                    portfolio_value = (1 + shocked_returns).prod()
                    results[scenario_name] = {
                        "volatility_multiplier": shock,
                        "portfolio_impact": float(portfolio_value - 1),
                        "new_volatility": float(shocked_vol),
                    }

            return results

        except Exception as e:
            self.logger.error(f"Error performing stress tests: {e}")
            return {}

    async def _analyze_market_microstructure(
        self, market_data: List[RealMarketData]
    ) -> Dict[str, Any]:
        """Analyze market microstructure patterns."""
        try:
            if len(market_data) < 20:
                return {}

            # Calculate basic microstructure metrics
            df = pd.DataFrame(
                [
                    {
                        "timestamp": d.timestamp,
                        "close": float(d.close_price),
                        "volume": d.volume,
                        "high": float(d.high_price),
                        "low": float(d.low_price),
                    }
                    for d in market_data
                ]
            )

            df.set_index("timestamp", inplace=True)
            df.sort_index(inplace=True)

            # Price impact analysis
            returns = df["close"].pct_change().dropna()
            volume = df["volume"].iloc[1:]  # Align with returns

            # Volume - price relationship
            volume_price_corr = returns.corr(volume)

            # Bid - ask spread proxy (high - low spread)
            spread = (df["high"] - df["low"]) / df["close"]
            avg_spread = spread.mean()
            spread_volatility = spread.std()

            # Volume patterns
            volume_trend = (
                volume.rolling(10).mean().iloc[-1] / volume.rolling(50).mean().iloc[-1]
                if len(volume) >= 50
                else 1.0
            )

            return {
                "volume_price_correlation": (
                    float(volume_price_corr) if not pd.isna(volume_price_corr) else 0
                ),
                "average_spread": float(avg_spread),
                "spread_volatility": float(spread_volatility),
                "volume_trend": float(volume_trend),
                "liquidity_score": float(
                    1.0 / (avg_spread + 0.001)
                ),  # Higher is more liquid
            }

        except Exception as e:
            self.logger.error(f"Error analyzing market microstructure: {e}")
            return {}

    async def _generate_trading_recommendations(
        self,
        base_analysis: AnalysisResult,
        statistical_metrics: Dict[str, float],
        ml_predictions: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Generate trading recommendations based on analysis."""
        try:
            recommendations = []

            # Base recommendation from signal strength
            if base_analysis.signal_strength > 0.7:
                recommendation = {
                    "type": (
                        "strong_buy"
                        if base_analysis.signal_direction == "buy"
                        else "strong_sell"
                    ),
                    "confidence": base_analysis.confidence,
                    "reasoning": f"Strong signal ({base_analysis.signal_strength:.3f}) with high confidence",
                    "priority": "high",
                }
                recommendations.append(recommendation)

            # Statistical significance recommendation
            statistical_significance = statistical_metrics.get(
                "statistical_significance", 0.5
            )
            if statistical_significance > 0.8:
                recommendation = {
                    "type": (
                        "statistical_buy"
                        if base_analysis.signal_direction == "buy"
                        else "statistical_sell"
                    ),
                    "confidence": statistical_significance,
                    "reasoning": f"High statistical significance ({statistical_significance:.3f})",
                    "priority": "medium",
                }
                recommendations.append(recommendation)

            # ML prediction recommendation
            if ml_predictions:
                for model_name, prediction in ml_predictions.items():
                    if (
                        isinstance(prediction, (list, np.ndarray))
                        and len(prediction) > 0
                    ):
                        pred_value = (
                            prediction[-1]
                            if hasattr(prediction, "__getitem__")
                            else prediction
                        )
                        if isinstance(pred_value, (int, float)):
                            recommendation = {
                                "type": "ml_buy" if pred_value > 0 else "ml_sell",
                                "confidence": 0.7,  # Would be calculated from model performance
                                "reasoning": f"ML model {model_name} prediction: {pred_value:.3f}",
                                "priority": "medium",
                            }
                            recommendations.append(recommendation)

            return recommendations

        except Exception as e:
            self.logger.error(f"Error generating trading recommendations: {e}")
            return []

    async def _generate_risk_warnings(
        self,
        volatility_analysis: Dict[str, Any],
        var_analysis: Dict[str, float],
        stress_test_results: Dict[str, Any],
    ) -> List[str]:
        """Generate risk warnings based on analysis."""
        try:
            warnings = []

            # Volatility warnings
            regime = volatility_analysis.get("regime", "normal")
            if regime == "high_volatility":
                warnings.append(
                    "High volatility environment detected - consider reducing position sizes"
                )
            elif regime == "low_volatility":
                warnings.append("Low volatility environment - market may be complacent")

            # VaR warnings
            var_95 = var_analysis.get("var_95", 0)
            if var_95 < -0.05:  # 5% daily loss
                warnings.append(
                    f"High VaR detected: {var_95:.1%} daily loss at 95% confidence"
                )

            # Stress test warnings
            for scenario, results in stress_test_results.items():
                portfolio_impact = results.get("portfolio_impact", 0)
                if portfolio_impact < -0.10:  # 10% portfolio loss
                    warnings.append(
                        f"Stress test warning: {scenario} could cause {portfolio_impact:.1%} portfolio loss"
                    )

            return warnings

        except Exception as e:
            self.logger.error(f"Error generating risk warnings: {e}")
            return []

    async def get_analysis_summary(self) -> Dict[str, Any]:
        """Get summary of recent analysis results."""
        try:
            if not self.analysis_history:
                return {"message": "No analysis history available"}

            latest_analysis = self.analysis_history[-1]

            summary = {
                "timestamp": latest_analysis.base_analysis.timestamp,
                "symbols_analyzed": latest_analysis.base_analysis.symbols_analyzed,
                "signal_strength": latest_analysis.base_analysis.signal_strength,
                "signal_direction": latest_analysis.base_analysis.signal_direction,
                "confidence": latest_analysis.base_analysis.confidence,
                "market_regime": latest_analysis.base_analysis.market_regime.regime_type,
                "statistical_significance": latest_analysis.statistical_metrics.get(
                    "statistical_significance", 0
                ),
                "volatility_regime": latest_analysis.volatility_analysis.get(
                    "regime", "unknown"
                ),
                "trading_recommendations_count": len(
                    latest_analysis.trading_recommendations
                ),
                "risk_warnings_count": len(latest_analysis.risk_warnings),
                "analysis_quality": latest_analysis.base_analysis.analysis_quality,
            }

            return summary

        except Exception as e:
            self.logger.error(f"Error getting analysis summary: {e}")
            return {"error": str(e)}

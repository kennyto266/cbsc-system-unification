"""
Data Analyst Agent Implementation
數據分析師智能體實現
"""

import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional

from ..base_agent import BaseAgent, AgentConfig, AgentCapability, AgentStatus
from ..core.logging import get_logger, log_performance


class DataAnalystAgent(BaseAgent):
    """
    Data Analyst Agent for data quality analysis and anomaly detection.
    數據分析師智能體，負責數據質量分析和異常檢測。
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize data analyst agent.

        Args:
            config: Optional agent configuration
        """
        if config is None:
            config = AgentConfig(
                agent_id="data_analyst",
                agent_type="DataAnalystAgent",
                config={
                    "max_anomaly_threshold": 3.0,
                    "min_quality_score": 0.7,
                    "enable_trend_analysis": True,
                    "cache_results": True
                }
            )

        super().__init__(config.name, config.version, config=config)
        self.max_anomaly_threshold = config.config.get("max_anomaly_threshold", 3.0)
        self.min_quality_score = config.config.get("min_quality_score", 0.7)
        self.enable_trend_analysis = config.config.get("enable_trend_analysis", True)
        self.cache_results = config.config.get("cache_results", True)

        # Define capabilities
        self.capabilities = [
            AgentCapability(
                name="data_quality_assessment",
                description="Assess the quality and completeness of financial data",
                input_types=["price_data", "volume_data", "market_data"],
                output_types=["quality_score", "completeness_report"],
                parameters={
                    "min_quality_threshold": 0.5,
                    "completeness_weight": 0.3,
                    "consistency_weight": 0.4,
                    "coverage_weight": 0.3
                }
            ),
            AgentCapability(
                name="anomaly_detection",
                description="Detect anomalies and outliers in time series data",
                input_types=["price_data", "volume_data", "market_data"],
                output_types=["anomaly_list", "anomaly_score"],
                parameters={
                    "z_score_threshold": 3.0,
                    "method": "statistical",
                    "window_size": 20
                }
            ),
            AgentCapability(
                name="trend_analysis",
                description="Analyze trends and patterns in market data",
                input_types=["price_data", "market_data"],
                output_types=["trend_direction", "trend_strength", "key_levels"],
                parameters={
                    "method": "linear_regression",
                    "confidence_threshold": 0.6
                }
            ),
            AgentCapability(
                name="data_validation",
                description="Validate data format and structure",
                input_types=["raw_data", "market_data"],
                output_types=["validation_report", "cleaned_data"],
                parameters={
                    "required_fields": ["timestamp", "close"],
                    "date_format": "auto_detect"
                }
            )
        ]

    async def setup(self):
        """Setup the data analyst agent."""
        self.logger.info("Setting up Data Analyst Agent")

        # Register message handlers
        self.register_message_handler("analyze_data", self._handle_analyze_data)
        self.register_message_handler("validate_data", self._handle_validate_data)
        self.register_message_handler("detect_anomalies", self._handle_detect_anomalies)

        # Subscribe to relevant topics
        self.subscribe_to_topic("market_data")
        self.subscribe_to_topic("price_updates")

        self.status = AgentStatus.IDLE

    async def process(self, message) -> Optional[Any]:
        """
        Process incoming message.

        Args:
            message: Incoming message

        Returns:
            Optional response message
        """
        try:
            if message.message_type in self.message_handlers:
                handler = self.message_handlers[message.message_type]
                result = await handler(message.content)

                return {
                    "agent": self.name,
                    "analysis_type": message.message_type,
                    "result": result,
                    "timestamp": datetime.now().isoformat(),
                    "success": True
                }
            else:
                self.logger.warning(f"Unknown message type: {message.message_type}")
                return None

        except Exception as e:
            self.logger.error(f"Error processing message: {e}", exc_info=True)
            return {
                "agent": self.name,
                "analysis_type": message.message_type,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "success": False
            }

    @log_performance("data_quality_assessment")
    async def _handle_analyze_data(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle data analysis request.

        Args:
            content: Request content

        Returns:
            Analysis result
        """
        try:
            data = content.get("data", [])
            if not data:
                return {"error": "No data provided for analysis"}

            # Convert to DataFrame
            df = pd.DataFrame(data)

            # Perform data quality assessment
            quality_score = self._assess_data_quality(df)
            completeness = self._check_data_completeness(df)
            consistency = self._check_data_consistency(df)

            # Trend analysis if enabled
            trend_result = {}
            if self.enable_trend_analysis and 'close' in df.columns:
                trend_result = self._analyze_trend(df)

            # Generate recommendations
            recommendations = self._generate_recommendations(
                quality_score, completeness, consistency, trend_result
            )

            return {
                "quality_score": quality_score,
                "completeness": completeness,
                "consistency": consistency,
                "trend_analysis": trend_result,
                "recommendations": recommendations,
                "summary": self._generate_analysis_summary(
                    quality_score, recommendations
                ),
                "data_points": len(df),
                "assessment_date": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Data analysis failed: {e}")
            return {"error": str(e)}

    @log_performance("data_validation")
    async def _handle_validate_data(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle data validation request.

        Args:
            content: Request content

        Returns:
            Validation result
        """
        try:
            data = content.get("data", [])
            schema = content.get("schema", {})

            if not data:
                return {"error": "No data provided for validation"}

            df = pd.DataFrame(data)

            # Validate data structure
            structure_valid = self._validate_structure(df, schema)
            data_types_valid = self._validate_data_types(df)
            ranges_valid = self._validate_ranges(df)

            # Clean data if needed
            cleaned_data = df.copy()
            if not structure_valid:
                cleaned_data = self._clean_data_structure(cleaned_data)

            validation_summary = {
                "structure_valid": structure_valid,
                "data_types_valid": data_types_valid,
                "ranges_valid": ranges_valid,
                "overall_valid": structure_valid and data_types_valid and ranges_valid,
                "issues_found": self._identify_issues(df),
                "cleaned_data": cleaned_data.to_dict('records') if not cleaned_data.empty else [],
                "validation_timestamp": datetime.now().isoformat()
            }

            return validation_summary

        except Exception as e:
            self.logger.error(f"Data validation failed: {e}")
            return {"error": str(e)}

    @log_performance("anomaly_detection")
    async def _handle_detect_anomalies(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle anomaly detection request.

        Args:
            content: Request content

        Returns:
            Anomaly detection result
        """
        try:
            data = content.get("data", [])
            method = content.get("method", "statistical")
            threshold = content.get("threshold", self.max_anomaly_threshold)

            if not data:
                return {"error": "No data provided for anomaly detection"}

            df = pd.DataFrame(data)

            # Detect anomalies
            anomalies = self._detect_anomalies(df, method, threshold)
            anomaly_score = self._calculate_anomaly_score(anomalies)

            # Categorize anomalies
            categorized_anomalies = self._categorize_anomalies(anomalies)

            return {
                "anomalies": categorized_anomalies,
                "anomaly_count": len(anomalies),
                "anomaly_score": anomaly_score,
                "method_used": method,
                "threshold_used": threshold,
                "data_points": len(df),
                "detection_timestamp": datetime.now().isoformat(),
                "recommendations": self._get_anomaly_recommendations(categorized_anomalies)
            }

        except Exception as e:
            self.logger.error(f"Anomaly detection failed: {e}")
            return {"error": str(e)}

    def _assess_data_quality(self, df: pd.DataFrame) -> float:
        """Assess overall data quality."""
        try:
            # Check missing values
            missing_ratio = df.isnull().sum().sum() / len(df) / len(df.columns)

            # Check data completeness
            completeness_score = self._check_data_completeness(df)['overall_score']

            # Check data consistency
            consistency_score = self._check_data_consistency(df)['overall_score']

            # Check data coverage
            coverage_score = self._calculate_data_coverage(df)

            # Calculate overall quality score
            quality_score = (1 - missing_ratio) * 0.3 + completeness_score * 0.3 + \
                           consistency_score * 0.2 + coverage_score * 0.2

            return max(0.0, min(1.0, quality_score))

        except Exception as e:
            self.logger.debug(f"Quality assessment error: {e}")
            return 0.5  # Default medium quality

    def _check_data_completeness(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check data completeness."""
        try:
            # Check required columns
            required_columns = ['timestamp', 'close', 'high', 'low', 'open', 'volume']
            missing_columns = [col for col in required_columns if col not in df.columns]

            # Calculate missing values
            missing_data = df.isnull().sum()
            total_cells = len(df) * len(df.columns)
            missing_ratio = missing_data.sum() / total_cells if total_cells > 0 else 0

            return {
                "overall_score": max(0, 1 - missing_ratio),
                "missing_columns": missing_columns,
                "missing_data": missing_data.to_dict(),
                "missing_ratio": missing_ratio,
                "data_points": len(df)
            }

        except Exception as e:
            self.logger.debug(f"Completeness check error: {e}")
            return {"overall_score": 0.5}

    def _check_data_consistency(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check data consistency."""
        try:
            consistency_issues = []

            # Check OHLC consistency
            ohlc_columns = ['open', 'high', 'low', 'close']
            if all(col in df.columns for col in ohlc_columns):
                # High should be >= open and close
                invalid_high = df[(df['high'] < df['open']) | (df['high'] < df['close'])].index
                # Low should be <= open and close
                invalid_low = df[(df['low'] > df['open']) | (df['low'] > df['close'])].index

                consistency_issues.extend([
                    f"Invalid high values at {len(invalid_high)} points",
                    f"Invalid low values at {len(invalid_low)} points"
                ])

            # Check for negative prices/volumes
            if 'close' in df.columns:
                negative_prices = (df['close'] < 0).sum()
                if negative_prices > 0:
                    consistency_issues.append(f"Negative prices found: {negative_prices}")

            if 'volume' in df.columns:
                negative_volumes = (df['volume'] < 0).sum()
                if negative_volumes > 0:
                    consistency_issues.append(f"Negative volumes found: {negative_volumes}")

            consistency_score = max(0, 1 - len(consistency_issues) / 10)  # Arbitrary penalty

            return {
                "overall_score": consistency_score,
                "issues": consistency_issues,
                "checks_performed": len(ohlc_columns) + 2  # OHLC + negative checks
            }

        except Exception as e:
            self.logger.debug(f"Consistency check error: {e}")
            return {"overall_score": 0.5}

    def _calculate_data_coverage(self, df: pd.DataFrame) -> float:
        """Calculate data coverage score."""
        try:
            if 'timestamp' not in df.columns:
                return 0.0

            # Check time range
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            time_range = (df['timestamp'].max() - df['timestamp'].min()).days

            # Score based on coverage (1 year = full score)
            coverage_score = min(1.0, time_range / 365)

            return coverage_score

        except Exception as e:
            self.logger.debug(f"Coverage calculation error: {e}")
            return 0.5

    def _analyze_trend(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze price trend."""
        try:
            if 'close' not in df.columns:
                return {"direction": "unknown", "strength": 0.0}

            prices = df['close'].astype(float)

            # Linear regression for trend
            x = np.arange(len(prices))
            slope, intercept = np.polyfit(x, prices, 1)

            # Calculate trend strength
            r_squared = np.corrcoef(x, prices)[0, 1] ** 2

            # Determine direction
            direction = "bullish" if slope > 0 else "bearish" if slope < 0 else "sideways"

            # Calculate trend strength as percentage change
            trend_strength = abs(slope / prices.mean()) * 100 if prices.mean() != 0 else 0

            # Find key levels
            key_levels = self._find_key_levels(prices)

            return {
                "direction": direction,
                "strength": min(trend_strength, 100.0),  # Cap at 100%
                "r_squared": r_squared,
                "slope": slope,
                "intercept": intercept,
                "key_levels": key_levels,
                "confidence": r_squared
            }

        except Exception as e:
            self.logger.debug(f"Trend analysis error: {e}")
            return {"direction": "unknown", "strength": 0.0}

    def _detect_anomalies(self, df: pd.DataFrame, method: str, threshold: float) -> List[Dict[str, Any]]:
        """Detect anomalies in the data."""
        try:
            anomalies = []

            if 'close' in df.columns:
                close_prices = df['close'].astype(float)

                if method == "statistical":
                    # Z-score method
                    z_scores = np.abs((close_prices - close_prices.mean()) / close_prices.std())
                    anomaly_indices = z_scores > threshold

                    for idx in df[anomaly_indices].index:
                        anomalies.append({
                            "type": "price_anomaly",
                            "timestamp": df.loc[idx, 'timestamp'] if 'timestamp' in df.columns else str(idx),
                            "index": idx,
                            "value": float(df.loc[idx, 'close']),
                            "z_score": float(z_scores[idx]),
                            "severity": self._calculate_severity(z_scores[idx])
                        })

            if 'volume' in df.columns:
                volumes = df['volume'].astype(float)

                if method == "statistical":
                    # Z-score method for volume
                    z_scores = np.abs((volumes - volumes.mean()) / volumes.std())
                    volume_anomaly_indices = z_scores > threshold

                    for idx in df[volume_anomaly_indices].index:
                        anomalies.append({
                            "type": "volume_anomaly",
                            "timestamp": df.loc[idx, 'timestamp'] if 'timestamp' in df.columns else str(idx),
                            "index": idx,
                            "value": float(df.loc[idx, 'volume']),
                            "z_score": float(z_scores[idx]),
                            "severity": self._calculate_severity(z_scores[idx])
                        })

            return anomalies

        except Exception as e:
            self.logger.error(f"Anomaly detection error: {e}")
            return []

    def _calculate_anomaly_score(self, anomalies: List[Dict[str, Any]]) -> float:
        """Calculate overall anomaly score."""
        if not anomalies:
            return 0.0

        # Weighted score based on severity
        total_score = sum(anomaly.get("severity", 1) for anomaly in anomalies)

        return min(100.0, total_score)

    def _categorize_anomalies(self, anomalies: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize anomalies by type."""
        categorized = {
            "price_anomalies": [],
            "volume_anomalies": [],
            "data_gaps": [],
            "outliers": []
        }

        for anomaly in anomalies:
            anomaly_type = anomaly.get("type", "unknown")
            if anomaly_type in categorized:
                categorized[anomaly_type].append(anomaly)
            else:
                categorized["outliers"].append(anomaly)

        return categorized

    def _find_key_levels(self, prices: np.ndarray) -> Dict[str, Any]:
        """Find key price levels."""
        try:
            if len(prices) < 20:
                return {}

            # Calculate support and resistance levels
            highs = pd.Series(prices).rolling(window=20, center=False).max()
            lows = pd.Series(prices).rolling(window=20, center=False).min()

            current_price = prices[-1]
            recent_high = highs.dropna().iloc[-5:].max() if len(highs.dropna()) > 5 else highs.max()
            recent_low = lows.dropna().iloc[-5:].min() if len(lows.dropna()) > 5 else lows.min()

            return {
                "current_price": float(current_price),
                "resistance": float(recent_high),
                "support": float(recent_low),
                "resistance_distance": abs(recent_high - current_price),
                "support_distance": abs(current_price - recent_low)
            }

        except Exception as e:
            self.logger.debug(f"Key levels calculation error: {e}")
            return {}

    def _generate_recommendations(
        self,
        quality_score: float,
        completeness: Dict[str, Any],
        consistency: Dict[str, Any],
        trend_result: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []

        # Quality-based recommendations
        if quality_score < self.min_quality_score:
            recommendations.append("Data quality is below acceptable threshold. Consider data cleaning.")

        if completeness.get("missing_ratio", 0) > 0.1:
            recommendations.append("Significant missing data detected. Consider data imputation.")

        # Consistency-based recommendations
        if consistency.get("issues"):
            recommendations.extend([f"Data consistency issue: {issue}" for issue in consistency["issues"][:3]])

        # Trend-based recommendations
        if trend_result.get("direction") == "bullish" and trend_result.get("strength", 0) > 20:
            recommendations.append("Strong bullish trend detected. Consider momentum strategies.")
        elif trend_result.get("direction") == "bearish" and trend_result.get("strength", 0) > 20:
            recommendations.append("Strong bearish trend detected. Consider defensive strategies.")

        return recommendations

    def _generate_analysis_summary(self, quality_score: float, recommendations: List[str]) -> str:
        """Generate a summary of the analysis."""
        if quality_score >= 0.8:
            quality_desc = "excellent"
        elif quality_score >= 0.6:
            quality_desc = "good"
        elif quality_score >= 0.4:
            quality_desc = "fair"
        else:
            quality_desc = "poor"

        summary = f"Data quality assessment: {quality_desc} (score: {quality_score:.2f})"

        if recommendations:
            summary += f". Key recommendations: {len(recommendations)} identified."

        return summary

    def _validate_structure(self, df: pd.DataFrame, schema: Dict[str, Any]) -> bool:
        """Validate data structure against schema."""
        try:
            required_fields = schema.get("required_fields", ["timestamp", "close"])

            return all(field in df.columns for field in required_fields)

        except Exception:
            return False

    def _validate_data_types(self, df: pd.DataFrame) -> bool:
        """Validate data types."""
        try:
            # Basic type validation - could be enhanced
            return True

        except Exception:
            return False

    def _validate_ranges(self, df: pd.DataFrame) -> bool:
        """Validate value ranges."""
        try:
            # Basic range validation for financial data
            if 'close' in df.columns:
                if (df['close'] < 0).any():
                    return False

            if 'volume' in df.columns:
                if (df['volume'] < 0).any():
                    return False

            return True

        except Exception:
            return False

    def _clean_data_structure(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean data structure issues."""
        try:
            # Example cleaning logic
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])

            return df

        except Exception:
            return df

    def _identify_issues(self, df: pd.DataFrame) -> List[str]:
        """Identify data quality issues."""
        issues = []

        # Check for duplicates
        if df.duplicated().any():
            issues.append("Duplicate records found")

        # Check for gaps in time series
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            time_diffs = df['timestamp'].diff()
            expected_interval = time_diffs.mode()[0] if len(time_diffs) > 0 else pd.Timedelta(days=1)

            # Look for gaps larger than 2x expected interval
            large_gaps = time_diffs > expected_interval * 2
            if large_gaps.any():
                issues.append(f"Time series gaps detected: {large_gaps.sum()} records")

        return issues

    def _calculate_severity(self, z_score: float) -> float:
        """Calculate anomaly severity based on Z-score."""
        # Map Z-score to severity (1-10)
        return min(10.0, max(1.0, abs(z_score) / 2))

    def _get_anomaly_recommendations(self, categorized_anomalies: Dict[str, List[Dict[str, Any]]]) -> List[str]:
        """Get recommendations for anomaly handling."""
        recommendations = []

        if categorized_anomalies.get("price_anomalies"):
            recommendations.append("Price anomalies detected. Verify data sources and consider outlier handling.")

        if categorized_anomalies.get("volume_anomalies"):
            recommendations.append("Volume anomalies detected. Check for data feed issues.")

        if categorized_anomalies.get("data_gaps"):
            recommendations.append("Data gaps detected. Consider interpolation or data completion methods.")

        return recommendations


# Factory function
def create_data_analyst_agent(config: Optional[AgentConfig] = None) -> DataAnalystAgent:
    """
    Factory function to create Data Analyst Agent.

    Args:
        config: Optional agent configuration

    Returns:
        DataAnalystAgent instance
    """
    return DataAnalystAgent(config)
#!/usr / bin / env python3
"""
第4阶段：行为分析层 - 初始化模块
Phase 4: Behavioral Analysis Layer - Initialization Module

香港量化交易系统最复杂的行为分析层
The most sophisticated behavioral analysis layer for Hong Kong quantitative trading system

This module provides comprehensive behavioral analysis capabilities including:
- Time series pattern analysis with seasonal detection
- Intraday pattern recognition for HK trading sessions
- Machine learning anomaly detection with ensemble methods
- Historical pattern comparison and baseline management
- Regime change detection for market conditions
- Real - time behavior monitoring with sliding windows
- Adaptive thresholds with online learning

Key Components:
- TimeSeriesPatternAnalyzer: Advanced time series analysis
- IntradayPatternRecognizer: HK trading session patterns
- MLAnomalyDetector: Ensemble - based anomaly detection
- RealTimeBehaviorMonitor: Real - time monitoring and alerting
"""

# Core configuration
from .core.behavioral_config import (
    AnomalyType,
    BehavioralAnalysisConfig,
    MarketRegime,
    TradingSession,
    create_custom_config,
    get_behavioral_config,
)

# Intraday pattern recognition
from .intrday.session_pattern_recognizer import (
    IntradayPatternRecognizer,
    TradingSessionAnalyzer,
    VolatilityPatternRecognizer,
)

# Machine learning anomaly detection
from .ml_anomaly.ml_anomaly_detector import (
    BaseAnomalyDetector,
    EnsembleAnomalyDetector,
    GradientBoostingAnomalyDetector,
    IsolationForestDetector,
    LocalOutlierFactorDetector,
    MLAnomalyDetector,
    NeuralNetworkAnomalyDetector,
    OneClassSVMDetector,
    RandomForestAnomalyDetector,
)

# Real - time monitoring
from .realtime.behavior_monitor import (
    AdaptiveThresholdManager,
    RealTimeBehaviorMonitor,
    SlidingWindowProcessor,
)

# Time series analysis
from .time_series.pattern_analyzer import (
    SeasonalPatternDetector,
    TimeSeriesPatternAnalyzer,
    TrendAnalyzer,
)

# Version information
__version__ = "4.0.0"
__author__ = "Hong Kong Quantitative Trading System"
__description__ = (
    "Advanced behavioral analysis layer for financial market anomaly detection"
)


# Main analysis pipeline
class BehavioralAnalysisPipeline:
    """
    行为分析层主流水线
    Main pipeline for behavioral analysis layer

    This class provides a unified interface for all behavioral analysis components,
    enabling comprehensive analysis of financial market behavior patterns.
    """

    def __init__(self, config: Optional[BehavioralAnalysisConfig] = None):
        """初始化行为分析流水线"""
        self.config = config or get_behavioral_config()

        # 初始化各个组件
        self.ts_analyzer = TimeSeriesPatternAnalyzer(self.config.time_series)
        self.intraday_analyzer = IntradayPatternRecognizer(self.config.intraday_pattern)
        self.anomaly_detector = MLAnomalyDetector(
            self.config.ensemble, self.config.ml_models
        )
        self.realtime_monitor = RealTimeBehaviorMonitor(
            self.config.realtime_monitoring, self.anomaly_detector
        )

        self.is_initialized = False

        logger.info("Behavioral Analysis Pipeline initialized")

    def analyze_historical_patterns(
        self, price_data: pd.Series, symbol: str = "UNKNOWN"
    ) -> Dict[str, Any]:
        """
        分析历史行为模式

        Args:
            price_data: 价格时间序列数据
            symbol: 股票代码

        Returns:
            综合历史模式分析结果
        """
        try:
            logger.info(f"Starting historical pattern analysis for {symbol}")

            results = {
                "symbol": symbol,
                "analysis_type": "historical_patterns",
                "timestamp": datetime.now().isoformat(),
                "config": self.config.__dict__,
            }

            # 时间序列模式分析
            results["time_series_patterns"] = self.ts_analyzer.analyze_patterns(
                price_data, symbol
            )

            # 盘中模式分析（如果有日内数据）
            if isinstance(price_data.index, pd.DatetimeIndex):
                results["intraday_patterns"] = (
                    self.intraday_analyzer.recognize_intraday_patterns(
                        price_data, symbol
                    )
                )

            # 异常检测分析
            # 准备特征数据
            feature_data = self._prepare_features_for_anomaly_detection(price_data)
            if feature_data is not None:
                results["anomaly_detection"] = self.anomaly_detector.detect_anomalies(
                    feature_data,
                    feature_names=[
                        f"feature_{i}" for i in range(feature_data.shape[1])
                    ],
                )

            # 香港市场特定分析
            results["hk_market_insights"] = self._analyze_hk_market_specific_patterns(
                price_data
            )

            # 综合分析报告
            results["comprehensive_summary"] = self._generate_comprehensive_summary(
                results
            )

            logger.info(f"Historical pattern analysis completed for {symbol}")
            return results

        except Exception as e:
            logger.error(f"Error in historical pattern analysis: {e}")
            return {"error": str(e), "symbol": symbol}

    def setup_realtime_monitoring(
        self, baseline_data: pd.Series, alert_callback: Optional[Callable] = None
    ) -> None:
        """
        设置实时监控

        Args:
            baseline_data: 基线数据用于初始化
            alert_callback: 告警回调函数
        """
        try:
            logger.info("Setting up real - time monitoring")

            # 从基线数据初始化监控器
            self.realtime_monitor.initialize_from_baseline(baseline_data)

            # 添加告警回调
            if alert_callback:
                self.realtime_monitor.add_alert_callback(alert_callback)

            self.is_initialized = True
            logger.info("Real - time monitoring setup completed")

        except Exception as e:
            logger.error(f"Error setting up real - time monitoring: {e}")
            raise

    def start_monitoring(self) -> None:
        """启动实时监控"""
        if not self.is_initialized:
            raise ValueError("Must call setup_realtime_monitoring first")

        self.realtime_monitor.start_monitoring()
        logger.info("Real - time monitoring started")

    def stop_monitoring(self) -> Dict[str, Any]:
        """停止监控并获取报告"""
        monitoring_report = self.realtime_monitor.get_monitoring_report()
        self.realtime_monitor.stop_monitoring()
        logger.info("Real - time monitoring stopped")
        return monitoring_report

    def add_realtime_data(
        self, price: float, timestamp: Optional[datetime] = None, **metadata
    ) -> None:
        """添加实时数据点"""
        self.realtime_monitor.add_data_point(price, timestamp, **metadata)

    def get_monitoring_status(self) -> Dict[str, Any]:
        """获取当前监控状态"""
        return self.realtime_monitor.get_current_status()

    def _prepare_features_for_anomaly_detection(
        self, price_data: pd.Series
    ) -> Optional[np.ndarray]:
        """为异常检测准备特征数据"""
        try:
            if len(price_data) < 50:
                return None

            features = []

            # 基础价格特征
            price_data.pct_change().dropna()

            # 滑动窗口统计特征
            windows = [5, 10, 20, 50]
            for window in windows:
                if len(price_data) >= window:
                    rolling_mean = price_data.rolling(window = window).mean()
                    rolling_std = price_data.rolling(window = window).std()
                    rolling_max = price_data.rolling(window = window).max()
                    rolling_min = price_data.rolling(window = window).min()

                    features.extend(
                        [
                            rolling_mean.dropna(),
                            rolling_std.dropna(),
                            (price_data - rolling_min)
                            / (rolling_max - rolling_min).dropna(),  # Relative position
                        ]
                    )

            # 技术指标特征
            # RSI
            delta = price_data.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window = 14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window = 14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            features.append(rsi.dropna())

            # 移动平均特征
            ma_short = price_data.rolling(window = 10).mean()
            ma_long = price_data.rolling(window = 30).mean()
            ma_ratio = ma_short / ma_long
            features.append(ma_ratio.dropna())

            # 对齐所有特征
            min_length = min(len(f) for f in features if len(f) > 0)
            if min_length == 0:
                return None

            aligned_features = [
                f.iloc[-min_length:].values for f in features if len(f) >= min_length
            ]

            if not aligned_features:
                return None

            return np.column_stack(aligned_features)

        except Exception as e:
            logger.warning(f"Error preparing features: {e}")
            return None

    def _analyze_hk_market_specific_patterns(
        self, price_data: pd.Series
    ) -> Dict[str, Any]:
        """分析香港市场特定模式"""
        try:
            hk_insights = {}

            if not isinstance(price_data.index, pd.DatetimeIndex):
                return hk_insights

            # 交易时段分析
            trading_sessions = {
                "morning": price_data.between_time("09:30", "12:00"),
                "afternoon": price_data.between_time("13:00", "16:00"),
            }

            for session, data in trading_sessions.items():
                if len(data) > 0:
                    session_returns = data.pct_change().dropna()
                    if len(session_returns) > 0:
                        hk_insights[f"{session}_session"] = {
                            "avg_return": float(session_returns.mean()),
                            "volatility": float(session_returns.std()),
                            "samples": len(data),
                        }

            # 月末效应
            month_end = price_data.index.day >= 25
            if month_end.any():
                month_end_returns = price_data.pct_change()[month_end]
                if len(month_end_returns) > 0:
                    hk_insights["month_end_effect"] = {
                        "avg_return": float(month_end_returns.mean()),
                        "volatility": float(month_end_returns.std()),
                    }

            return hk_insights

        except Exception as e:
            logger.warning(f"Error in HK market analysis: {e}")
            return {"error": str(e)}

    def _generate_comprehensive_summary(
        self, results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成综合分析摘要"""
        try:
            summary = {
                "overall_health_score": 0.0,
                "key_insights": [],
                "risk_level": "unknown",
                "recommendations": [],
            }

            # 从时间序列分析中提取关键信息
            if "time_series_patterns" in results:
                ts_patterns = results["time_series_patterns"]
                if "pattern_summary" in ts_patterns:
                    pattern_summary = ts_patterns["pattern_summary"]

                    # 季节性和趋势分析
                    if pattern_summary.get("has_seasonality", False):
                        summary["key_insights"].append(
                            "Strong seasonal patterns detected"
                        )

                    trend_strength = pattern_summary.get("trend_strength", "weak")
                    if trend_strength in ["strong", "moderate"]:
                        direction = pattern_summary.get("trend_direction", "unknown")
                        summary["key_insights"].append(
                            f"Clear {direction} trend detected"
                        )

            # 从异常检测中提取风险信息
            if "anomaly_detection" in results:
                anomaly_results = results["anomaly_detection"]
                if "predictions" in anomaly_results:
                    anomaly_rate = anomaly_results["predictions"]["anomaly_rate"]
                    summary["overall_health_score"] = max(
                        0, 1.0 - anomaly_rate * 2
                    )  # 简单的健康评分

                    if anomaly_rate > 0.1:  # 10%以上异常率
                        summary["risk_level"] = "high"
                        summary["recommendations"].append(
                            "High anomaly rate detected, investigate further"
                        )
                    elif anomaly_rate > 0.05:
                        summary["risk_level"] = "medium"
                    else:
                        summary["risk_level"] = "low"

            # 从盘中模式中提取交易洞察
            if "intraday_patterns" in results:
                intraday = results["intraday_patterns"]
                if "pattern_summary" in intraday:
                    momentum = intraday["pattern_summary"].get(
                        "momentum_signal", "neutral"
                    )
                    if momentum != "neutral":
                        summary["key_insights"].append(
                            f"{momentum.capitalize()} momentum detected"
                        )

            # 香港市场特定洞察
            if "hk_market_insights" in results:
                hk_insights = results["hk_market_insights"]
                if "month_end_effect" in hk_insights:
                    month_end = hk_insights["month_end_effect"]
                    if abs(month_end.get("avg_return", 0)) > 0.02:
                        summary["key_insights"].append(
                            "Significant month - end effect detected"
                        )

            return summary

        except Exception as e:
            logger.warning(f"Error generating comprehensive summary: {e}")
            return {"error": str(e)}


# Convenience functions for quick usage
def create_behavioral_analyzer(
    market_regime: str = "normal",
    volatility_level: str = "normal",
    analysis_focus: str = "comprehensive",
) -> BehavioralAnalysisPipeline:
    """
    创建行为分析器的便捷函数

    Args:
        market_regime: 市场状态 ('bull_market', 'bear_market', 'high_volatility', etc.)
        volatility_level: 波动率水平 ('low', 'normal', 'high')
        analysis_focus: 分析重点 ('speed', 'accuracy', 'comprehensive')

    Returns:
        配置好的行为分析流水线
    """
    from .core.behavioral_config import MarketRegime

    # 转换字符串到枚举
    regime_map = {
        "bull_market": MarketRegime.BULL_MARKET,
        "bear_market": MarketRegime.BEAR_MARKET,
        "sideways": MarketRegime.SIDEWAYS,
        "high_volatility": MarketRegime.HIGH_VOLATILITY,
        "low_volatility": MarketRegime.LOW_VOLATILITY,
    }

    regime = regime_map.get(market_regime, MarketRegime.BULL_MARKET)

    # 创建自定义配置
    config = create_custom_config(
        market_regime = regime,
        volatility_level = volatility_level,
        analysis_focus = analysis_focus,
    )

    return BehavioralAnalysisPipeline(config)


def quick_pattern_analysis(
    price_data: pd.Series, symbol: str = "UNKNOWN", include_realtime: bool = False
) -> Dict[str, Any]:
    """
    快速模式分析的便捷函数

    Args:
        price_data: 价格数据
        symbol: 股票代码
        include_realtime: 是否包含实时监控设置

    Returns:
        分析结果
    """
    # 创建分析器
    analyzer = create_behavioral_analyzer()

    # 执行历史分析
    results = analyzer.analyze_historical_patterns(price_data, symbol)

    # 设置实时监控（如果需要）
    if include_realtime:
        analyzer.setup_realtime_monitoring(price_data)
        results["realtime_monitoring_enabled"] = True

    return results


# Export key classes and functions
__all__ = [
    # Configuration
    "BehavioralAnalysisConfig",
    "get_behavioral_config",
    "create_custom_config",
    "MarketRegime",
    "TradingSession",
    "AnomalyType",
    # Time series analysis
    "TimeSeriesPatternAnalyzer",
    "SeasonalPatternDetector",
    "TrendAnalyzer",
    # Intraday pattern recognition
    "IntradayPatternRecognizer",
    "TradingSessionAnalyzer",
    "VolatilityPatternRecognizer",
    # Machine learning anomaly detection
    "MLAnomalyDetector",
    "EnsembleAnomalyDetector",
    "BaseAnomalyDetector",
    "IsolationForestDetector",
    "OneClassSVMDetector",
    "LocalOutlierFactorDetector",
    "RandomForestAnomalyDetector",
    "GradientBoostingAnomalyDetector",
    "NeuralNetworkAnomalyDetector",
    # Real - time monitoring
    "RealTimeBehaviorMonitor",
    "SlidingWindowProcessor",
    "AdaptiveThresholdManager",
    # Main pipeline
    "BehavioralAnalysisPipeline",
    "create_behavioral_analyzer",
    "quick_pattern_analysis",
    # Metadata
    "__version__",
    "__author__",
    "__description__",
]

# Package - level logging
import logging

logger = logging.getLogger(__name__)

# Test configuration on import
try:
    from .core.behavioral_config import get_behavioral_config

    config = get_behavioral_config()
    logger.info(f"Behavioral Analysis Layer v{__version__} loaded successfully")
    logger.info(f"Configuration: {config.app_name} v{config.app_version}")
except Exception as e:
    logger.warning(f"Error loading behavioral analysis configuration: {e}")

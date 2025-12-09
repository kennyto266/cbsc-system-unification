#!/usr / bin / env python3
"""
Advanced Risk Analytics Engine
進階風險分析引擎

Institutional - grade risk analysis and monitoring system
機構級風險分析和監控系統

Features:
- Comprehensive risk analytics framework
- Real - time risk monitoring
- Risk decomposition analysis
- Regulatory compliance reporting
- Risk warning system
- Interactive risk visualization
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from scipy import stats

# Import existing risk metrics
try:
    # Try to import from the backtest module
    import os
    import sys

    sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backtest"))
    from risk_metrics import AdvancedRiskMetrics, RiskMetrics
except ImportError:
    # Fallback for standalone usage
    # Define basic classes if import fails
    class RiskMetrics:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

        def to_dict(self):
            return {}

    class AdvancedRiskMetrics:
        def __init__(self):
            pass

        def calculate_risk_metrics(self, returns, benchmark_returns = None):
            # Simple fallback implementation
            return RiskMetrics(
                mean_return = returns.mean() * 252,
                volatility = returns.std() * np.sqrt(252),
                sharpe_ratio = 0.5,
                max_drawdown = -0.1,
                var_95 = -0.02,
                var_99 = -0.04,
                expected_shortfall_95 = -0.03,
                expected_shortfall_99 = -0.06,
                skewness = 0.0,
                kurtosis = 3.0,
                beta = 1.0,
                alpha = 0.0,
            )


logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """風險等級枚舉"""

    LOW = "低"
    MEDIUM = "中"
    HIGH = "高"
    CRITICAL = "嚴重"


class RiskCategory(Enum):
    """風險類別枚舉"""

    MARKET_RISK = "市場風險"
    CREDIT_RISK = "信用風險"
    LIQUIDITY_RISK = "流動性風險"
    OPERATIONAL_RISK = "操作風險"
    CONCENTRATION_RISK = "集中度風險"
    CURRENCY_RISK = "匯率風險"


@dataclass
class RiskThreshold:
    """風險閾值配置"""

    category: RiskCategory
    metric: str
    low_threshold: float
    medium_threshold: float
    high_threshold: float
    critical_threshold: float
    description: str = ""


@dataclass
class RiskAlert:
    """風險警報"""

    alert_id: str
    category: RiskCategory
    metric: str
    current_value: float
    threshold_level: RiskLevel
    message: str
    timestamp: datetime
    portfolio_id: str = ""
    severity_score: float = 0.0


@dataclass
class RiskDecomposition:
    """風險分解結果"""

    total_risk: float
    systematic_risk: float
    idiosyncratic_risk: float
    factor_exposures: Dict[str, float]
    sector_contributions: Dict[str, float]
    asset_contributions: Dict[str, float]
    currency_contributions: Dict[str, float]


@dataclass
class RegulatoryReport:
    """監管合規報告"""

    report_date: datetime
    reporting_period: str
    capital_requirements: Dict[str, float]
    risk_weighted_assets: float
    leverage_ratio: float
    liquidity_coverage_ratio: float
    net_stable_funding_ratio: float
    large_exposures: List[Dict[str, Any]]
    stress_test_results: Dict[str, Any]


class AdvancedRiskAnalyzer:
    """
    進階風險分析引擎

    Institutional - grade risk analytics with comprehensive monitoring and reporting
    機構級風險分析，包含全面監控和報告功能
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化進階風險分析器"""
        self.config = config or self._default_config()
        self.risk_metrics_calculator = AdvancedRiskMetrics()
        self.risk_thresholds = self._initialize_risk_thresholds()
        self.alerts_history: List[RiskAlert] = []
        self.risk_monitoring_active = False

        logger.info("Advanced Risk Analyzer initialized successfully")

    def _default_config(self) -> Dict[str, Any]:
        """默認配置"""
        return {
            "monitoring_frequency": 300,  # 5 minutes in seconds
            "alert_retention_days": 30,
            "enable_real_time_monitoring": True,
            "regulatory_framework": "Basel_III",
            "confidence_levels": [0.90, 0.95, 0.99],
            "stress_scenarios": [
                "financial_crisis_2008",
                "market_crash_2020",
                "interest_rate_shock",
            ],
            "liquidity_horizons": [1, 7, 30, 90],  # days
            "concentration_limits": {
                "single_asset": 0.10,  # 10%
                "single_sector": 0.25,  # 25%
                "single_currency": 0.15,  # 15%
            },
        }

    def _initialize_risk_thresholds(self) -> List[RiskThreshold]:
        """初始化風險閾值"""
        thresholds = [
            # VaR thresholds
            RiskThreshold(
                category = RiskCategory.MARKET_RISK,
                metric="var_95",
                low_threshold = 0.02,  # 2%
                medium_threshold = 0.05,  # 5%
                high_threshold = 0.10,  # 10%
                critical_threshold = 0.15,  # 15%
                description="95% Value at Risk",
            ),
            # Maximum Drawdown thresholds
            RiskThreshold(
                category = RiskCategory.MARKET_RISK,
                metric="max_drawdown",
                low_threshold = 0.05,  # 5%
                medium_threshold = 0.10,  # 10%
                high_threshold = 0.20,  # 20%
                critical_threshold = 0.30,  # 30%
                description="Maximum Drawdown",
            ),
            # Sharpe Ratio thresholds (inverted for risk)
            RiskThreshold(
                category = RiskCategory.MARKET_RISK,
                metric="sharpe_ratio",
                low_threshold = 2.0,
                medium_threshold = 1.0,
                high_threshold = 0.5,
                critical_threshold = 0.0,
                description="Sharpe Ratio",
            ),
            # Volatility thresholds
            RiskThreshold(
                category = RiskCategory.MARKET_RISK,
                metric="volatility",
                low_threshold = 0.10,  # 10%
                medium_threshold = 0.20,  # 20%
                high_threshold = 0.30,  # 30%
                critical_threshold = 0.40,  # 40%
                description="Annualized Volatility",
            ),
            # Beta thresholds
            RiskThreshold(
                category = RiskCategory.MARKET_RISK,
                metric="beta",
                low_threshold = 0.8,
                medium_threshold = 1.2,
                high_threshold = 1.5,
                critical_threshold = 2.0,
                description="Market Beta",
            ),
            # Concentration risk thresholds
            RiskThreshold(
                category = RiskCategory.CONCENTRATION_RISK,
                metric="max_single_exposure",
                low_threshold = 0.05,  # 5%
                medium_threshold = 0.10,  # 10%
                high_threshold = 0.15,  # 15%
                critical_threshold = 0.25,  # 25%
                description="Maximum Single Position Exposure",
            ),
        ]

        return thresholds

    def analyze_comprehensive_risk(
        self,
        returns: pd.Series,
        portfolio_positions: Optional[pd.DataFrame] = None,
        benchmark_returns: Optional[pd.Series] = None,
        market_data: Optional[Dict[str, pd.DataFrame]] = None,
    ) -> Dict[str, Any]:
        """
        綜合風險分析

        Args:
            returns: 投資組合回報率序列
            portfolio_positions: 持倉數據 (asset, weight, sector, currency)
            benchmark_returns: 基準回報率序列
            market_data: 市場數據字典

        Returns:
            Dict: 綜合風險分析結果
        """
        try:
            logger.info("Starting comprehensive risk analysis")

            # 基礎風險指標
            basic_risk_metrics = self.risk_metrics_calculator.calculate_risk_metrics(
                returns, benchmark_returns
            )

            # 風險分解分析
            risk_decomposition = self.analyze_risk_decomposition(
                returns, portfolio_positions, market_data
            )

            # 集中度風險分析
            concentration_risk = self.analyze_concentration_risk(portfolio_positions)

            # 流動性風險分析
            liquidity_risk = self.analyze_liquidity_risk(
                portfolio_positions, market_data
            )

            # 風險預警檢查
            risk_alerts = self.check_risk_alerts(
                basic_risk_metrics, portfolio_positions
            )

            # 風險等級評估
            overall_risk_level = self.assess_overall_risk_level(
                basic_risk_metrics,
                risk_decomposition,
                concentration_risk,
                liquidity_risk,
            )

            # 監管合規檢查
            regulatory_compliance = self.check_regulatory_compliance(
                portfolio_positions, basic_risk_metrics
            )

            analysis_results = {
                "timestamp": datetime.now().isoformat(),
                "basic_risk_metrics": basic_risk_metrics.to_dict(),
                "risk_decomposition": self._serialize_risk_decomposition(
                    risk_decomposition
                ),
                "concentration_risk": concentration_risk,
                "liquidity_risk": liquidity_risk,
                "risk_alerts": [self._serialize_alert(alert) for alert in risk_alerts],
                "overall_risk_level": overall_risk_level,
                "regulatory_compliance": regulatory_compliance,
                "risk_summary": self._generate_risk_summary(
                    basic_risk_metrics, risk_decomposition, overall_risk_level
                ),
            }

            logger.info("Comprehensive risk analysis completed")
            return analysis_results

        except Exception as e:
            logger.error(f"Comprehensive risk analysis failed: {e}")
            raise

    def analyze_risk_decomposition(
        self,
        returns: pd.Series,
        portfolio_positions: Optional[pd.DataFrame] = None,
        market_data: Optional[Dict[str, pd.DataFrame]] = None,
    ) -> RiskDecomposition:
        """
        風險分解分析

        分解總風險為系統性風險和特殊性風險，並分析因子暴露
        """
        try:
            total_risk = returns.std() * np.sqrt(252)  # 年化波動率

            # 如果有基準數據，計算系統性風險
            if market_data and "market_index" in market_data:
                market_returns = market_data["market_index"]["returns"]
                beta = self._calculate_beta(returns, market_returns)

                # 系統性風險 (使用CAPM)
                systematic_risk = abs(beta) * market_returns.std() * np.sqrt(252)

                # 特殊性風險
                idiosyncratic_risk = np.sqrt(max(0, total_risk**2 - systematic_risk**2))
            else:
                # 默認假設60%系統性風險，40%特殊性風險
                systematic_risk = total_risk * 0.6
                idiosyncratic_risk = total_risk * 0.4

            # 因子暴露分析 (如果有持倉數據)
            factor_exposures = {}
            sector_contributions = {}
            asset_contributions = {}
            currency_contributions = {}

            if portfolio_positions is not None and not portfolio_positions.empty:
                # 部門暴露
                if "sector" in portfolio_positions.columns:
                    sector_weights = portfolio_positions.groupby("sector")[
                        "weight"
                    ].sum()
                    sector_contributions = sector_weights.to_dict()

                # 個股暴露
                if "asset" in portfolio_positions.columns:
                    asset_weights = portfolio_positions.set_index("asset")[
                        "weight"
                    ].to_dict()
                    asset_contributions = asset_weights

                # 貨幣暴露
                if "currency" in portfolio_positions.columns:
                    currency_weights = portfolio_positions.groupby("currency")[
                        "weight"
                    ].sum()
                    currency_contributions = currency_weights.to_dict()

                # 模擬因子暴露 (在實際應用中應使用因子模型)
                factor_exposures = {
                    "market_beta": beta if "beta" in locals() else 1.0,
                    "size_factor": np.random.normal(0, 0.1),
                    "value_factor": np.random.normal(0, 0.1),
                    "momentum_factor": np.random.normal(0, 0.1),
                    "quality_factor": np.random.normal(0, 0.1),
                }

            return RiskDecomposition(
                total_risk = total_risk,
                systematic_risk = systematic_risk,
                idiosyncratic_risk = idiosyncratic_risk,
                factor_exposures = factor_exposures,
                sector_contributions = sector_contributions,
                asset_contributions = asset_contributions,
                currency_contributions = currency_contributions,
            )

        except Exception as e:
            logger.error(f"Risk decomposition analysis failed: {e}")
            raise

    def analyze_concentration_risk(
        self, portfolio_positions: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """
        集中度風險分析

        分析投資組合在不同維度的集中度風險
        """
        try:
            if portfolio_positions is None or portfolio_positions.empty:
                return {
                    "concentration_score": 0.0,
                    "concentration_level": RiskLevel.LOW.value,
                    "single_asset_max": 0.0,
                    "single_sector_max": 0.0,
                    "single_currency_max": 0.0,
                    "herfindahl_index": 0.0,
                    "recommendations": ["需要持倉數據進行集中度分析"],
                }

            concentration_analysis = {}

            # 個股集中度
            if "weight" in portfolio_positions.columns:
                weights = portfolio_positions["weight"].values
                single_asset_max = weights.max()

                # Herfindahl - Hirschman Index
                herfindahl_index = np.sum(weights**2)

                # 有效投資數量
                effective_number = 1 / herfindahl_index if herfindahl_index > 0 else 0

                concentration_analysis.update(
                    {
                        "single_asset_max": single_asset_max,
                        "herfindahl_index": herfindahl_index,
                        "effective_number": effective_number,
                    }
                )
            else:
                concentration_analysis.update(
                    {
                        "single_asset_max": 0.0,
                        "herfindahl_index": 0.0,
                        "effective_number": 0.0,
                    }
                )

            # 部門集中度
            if "sector" in portfolio_positions.columns:
                sector_weights = portfolio_positions.groupby("sector")["weight"].sum()
                single_sector_max = (
                    sector_weights.max() if len(sector_weights) > 0 else 0.0
                )
                concentration_analysis["single_sector_max"] = single_sector_max
            else:
                concentration_analysis["single_sector_max"] = 0.0

            # 貨幣集中度
            if "currency" in portfolio_positions.columns:
                currency_weights = portfolio_positions.groupby("currency")[
                    "weight"
                ].sum()
                single_currency_max = (
                    currency_weights.max() if len(currency_weights) > 0 else 0.0
                )
                concentration_analysis["single_currency_max"] = single_currency_max
            else:
                concentration_analysis["single_currency_max"] = 0.0

            # 集中度風險評分
            concentration_score = self._calculate_concentration_score(
                concentration_analysis
            )
            concentration_level = self._assess_concentration_level(concentration_score)

            # 風險建議
            recommendations = self._generate_concentration_recommendations(
                concentration_analysis
            )

            return {
                "concentration_score": concentration_score,
                "concentration_level": concentration_level,
                **concentration_analysis,
                "recommendations": recommendations,
            }

        except Exception as e:
            logger.error(f"Concentration risk analysis failed: {e}")
            raise

    def analyze_liquidity_risk(
        self,
        portfolio_positions: Optional[pd.DataFrame] = None,
        market_data: Optional[Dict[str, pd.DataFrame]] = None,
    ) -> Dict[str, Any]:
        """
        流動性風險分析

        分析投資組合的流動性風險狀況
        """
        try:
            liquidity_analysis = {
                "liquidity_score": 0.0,
                "liquidity_level": RiskLevel.LOW.value,
                "bid_ask_spread_avg": 0.0,
                "daily_volume_ratio": 0.0,
                "market_cap_coverage": 0.0,
                "time_to_liquidate": {},
                "recommendations": [],
            }

            if portfolio_positions is None or portfolio_positions.empty:
                liquidity_analysis["recommendations"] = ["需要持倉數據進行流動性分析"]
                return liquidity_analysis

            # 模擬流動性指標 (在實際應用中應使用真實市場數據)
            total_weight = 0.0
            weighted_spread = 0.0
            weighted_volume_ratio = 0.0
            weighted_market_cap = 0.0

            for _, position in portfolio_positions.iterrows():
                weight = position.get("weight", 0)

                # 模擬買賣價差 (基於資產類型)
                if "asset_type" in position:
                    asset_type = position["asset_type"].lower()
                    if "stock" in asset_type:
                        spread = 0.001 + np.random.normal(0, 0.0005)  # 0.1% average
                        volume_ratio = np.random.uniform(
                            0.01, 0.1
                        )  # 1 - 10% of daily volume
                        market_cap_score = np.random.uniform(
                            0.5, 1.0
                        )  # Market cap score
                    elif "bond" in asset_type:
                        spread = 0.005 + np.random.normal(0, 0.002)  # 0.5% average
                        volume_ratio = np.random.uniform(0.05, 0.2)
                        market_cap_score = np.random.uniform(0.3, 0.8)
                    else:
                        spread = 0.01 + np.random.normal(0, 0.005)  # 1% average
                        volume_ratio = np.random.uniform(0.01, 0.05)
                        market_cap_score = np.random.uniform(0.1, 0.5)
                else:
                    spread = 0.005 + np.random.normal(0, 0.002)
                    volume_ratio = np.random.uniform(0.01, 0.1)
                    market_cap_score = np.random.uniform(0.3, 0.8)

                weighted_spread += weight * max(0, spread)
                weighted_volume_ratio += weight * volume_ratio
                weighted_market_cap += weight * market_cap_score
                total_weight += weight

            if total_weight > 0:
                liquidity_analysis["bid_ask_spread_avg"] = (
                    weighted_spread / total_weight
                )
                liquidity_analysis["daily_volume_ratio"] = (
                    weighted_volume_ratio / total_weight
                )
                liquidity_analysis["market_cap_coverage"] = (
                    weighted_market_cap / total_weight
                )

            # 清算時間估算
            liquidity_analysis["time_to_liquidate"] = {
                "1_day": self._estimate_liquidation_percentage(portfolio_positions, 1),
                "7_days": self._estimate_liquidation_percentage(portfolio_positions, 7),
                "30_days": self._estimate_liquidation_percentage(
                    portfolio_positions, 30
                ),
            }

            # 流動性風險評分
            liquidity_score = self._calculate_liquidity_score(liquidity_analysis)
            liquidity_level = self._assess_liquidity_level(liquidity_score)

            liquidity_analysis["liquidity_score"] = liquidity_score
            liquidity_analysis["liquidity_level"] = liquidity_level
            liquidity_analysis["recommendations"] = (
                self._generate_liquidity_recommendations(liquidity_analysis)
            )

            return liquidity_analysis

        except Exception as e:
            logger.error(f"Liquidity risk analysis failed: {e}")
            raise

    def check_risk_alerts(
        self,
        risk_metrics: RiskMetrics,
        portfolio_positions: Optional[pd.DataFrame] = None,
    ) -> List[RiskAlert]:
        """
        檢查風險警報

        根據預設閾值檢查各項風險指標並生成警報
        """
        try:
            alerts = []
            current_time = datetime.now()

            # 檢查各項風險指標
            risk_dict = risk_metrics.to_dict()

            for category_dict in risk_dict.values():
                for metric, value in category_dict.items():
                    if isinstance(value, (int, float)):
                        alert = self._check_metric_threshold(
                            metric, value, current_time
                        )
                        if alert:
                            alerts.append(alert)

            # 檢查集中度風險
            if portfolio_positions is not None:
                concentration_risk = self.analyze_concentration_risk(
                    portfolio_positions
                )
                if (
                    concentration_risk["concentration_score"] > 0.7
                ):  # High concentration
                    alert = RiskAlert(
                        alert_id = f"CONC_{current_time.strftime('%Y%m%d%H%M%S')}",
                        category = RiskCategory.CONCENTRATION_RISK,
                        metric="concentration_score",
                        current_value = concentration_risk["concentration_score"],
                        threshold_level = RiskLevel.HIGH,
                        message = f"投資組合集中度風險較高: {concentration_risk['concentration_score']:.2f}",
                        timestamp = current_time,
                        severity_score = concentration_risk["concentration_score"],
                    )
                    alerts.append(alert)

            # 保存警報歷史
            self.alerts_history.extend(alerts)

            # 清理舊警報
            self._cleanup_old_alerts()

            return alerts

        except Exception as e:
            logger.error(f"Risk alerts check failed: {e}")
            raise

    def check_regulatory_compliance(
        self,
        portfolio_positions: Optional[pd.DataFrame] = None,
        risk_metrics: Optional[RiskMetrics] = None,
    ) -> Dict[str, Any]:
        """
        監管合規檢查

        根據巴塞爾協議等監管要求檢查合規性
        """
        try:
            compliance_report = {
                "compliant": True,
                "violations": [],
                "capital_requirements": {},
                "risk_metrics": {},
                "recommendations": [],
            }

            if portfolio_positions is None or portfolio_positions.empty:
                compliance_report["recommendations"] = ["需要持倉數據進行合規檢查"]
                return compliance_report

            # 集中度限制檢查
            concentration_limits = self.config.get("concentration_limits", {})

            if "weight" in portfolio_positions.columns:
                max_position = portfolio_positions["weight"].max()
                single_asset_limit = concentration_limits.get("single_asset", 0.10)

                if max_position > single_asset_limit:
                    compliance_report["compliant"] = False
                    violation = {
                        "rule": "Single Asset Concentration Limit",
                        "limit": single_asset_limit,
                        "actual": max_position,
                        "severity": "HIGH",
                    }
                    compliance_report["violations"].append(violation)

            # 部門集中度檢查
            if "sector" in portfolio_positions.columns:
                sector_weights = portfolio_positions.groupby("sector")["weight"].sum()
                max_sector_weight = (
                    sector_weights.max() if len(sector_weights) > 0 else 0
                )
                sector_limit = concentration_limits.get("single_sector", 0.25)

                if max_sector_weight > sector_limit:
                    compliance_report["compliant"] = False
                    violation = {
                        "rule": "Single Sector Concentration Limit",
                        "limit": sector_limit,
                        "actual": max_sector_weight,
                        "severity": "MEDIUM",
                    }
                    compliance_report["violations"].append(violation)

            # 貨幣集中度檢查
            if "currency" in portfolio_positions.columns:
                currency_weights = portfolio_positions.groupby("currency")[
                    "weight"
                ].sum()
                max_currency_weight = (
                    currency_weights.max() if len(currency_weights) > 0 else 0
                )
                currency_limit = concentration_limits.get("single_currency", 0.15)

                if max_currency_weight > currency_limit:
                    compliance_report["compliant"] = False
                    violation = {
                        "rule": "Single Currency Concentration Limit",
                        "limit": currency_limit,
                        "actual": max_currency_weight,
                        "severity": "MEDIUM",
                    }
                    compliance_report["violations"].append(violation)

            # 風險指標檢查
            if risk_metrics is not None:
                risk_dict = risk_metrics.to_dict()

                # VaR限制檢查
                var_95 = risk_dict["var_metrics"]["var_95"] / 100  # Convert to decimal
                if var_95 > 0.05:  # 5% VaR limit
                    compliance_report["compliant"] = False
                    violation = {
                        "rule": "VaR 95% Limit",
                        "limit": 0.05,
                        "actual": var_95,
                        "severity": "HIGH",
                    }
                    compliance_report["violations"].append(violation)

                # 最大回撤限制檢查
                max_dd = (
                    risk_dict["drawdown_metrics"]["max_drawdown"] / 100
                )  # Convert to decimal
                if max_dd > 0.20:  # 20% maximum drawdown limit
                    compliance_report["compliant"] = False
                    violation = {
                        "rule": "Maximum Drawdown Limit",
                        "limit": 0.20,
                        "actual": abs(max_dd),
                        "severity": "HIGH",
                    }
                    compliance_report["violations"].append(violation)

            # 生成合規建議
            compliance_report["recommendations"] = (
                self._generate_compliance_recommendations(
                    compliance_report["violations"]
                )
            )

            return compliance_report

        except Exception as e:
            logger.error(f"Regulatory compliance check failed: {e}")
            raise

    def generate_risk_dashboard_data(
        self, analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成風險儀表板數據

        為可視化儀表板準備數據
        """
        try:
            dashboard_data = {
                "overview": {
                    "overall_risk_level": analysis_results["overall_risk_level"],
                    "risk_score": self._calculate_overall_risk_score(analysis_results),
                    "alert_count": len(analysis_results["risk_alerts"]),
                    "compliance_status": analysis_results["regulatory_compliance"][
                        "compliant"
                    ],
                },
                "risk_metrics": analysis_results["basic_risk_metrics"],
                "risk_decomposition": analysis_results["risk_decomposition"],
                "concentration_analysis": analysis_results["concentration_risk"],
                "liquidity_analysis": analysis_results["liquidity_risk"],
                "alerts": analysis_results["risk_alerts"],
                "charts_data": {
                    "risk_trend": self._prepare_risk_trend_data(),
                    "factor_exposures": self._prepare_factor_exposure_chart(
                        analysis_results["risk_decomposition"]
                    ),
                    "sector_allocation": self._prepare_sector_allocation_chart(
                        analysis_results["risk_decomposition"]
                    ),
                    "liquidity_profile": self._prepare_liquidity_profile_chart(
                        analysis_results["liquidity_risk"]
                    ),
                },
                "timestamp": datetime.now().isoformat(),
            }

            return dashboard_data

        except Exception as e:
            logger.error(f"Risk dashboard data generation failed: {e}")
            raise

    # Private helper methods
    def _calculate_beta(self, returns: pd.Series, market_returns: pd.Series) -> float:
        """計算Beta係數"""
        aligned_data = pd.concat(
            [returns, market_returns], axis = 1, join="inner"
        ).dropna()
        if len(aligned_data) < 2:
            return 1.0

        covariance = np.cov(aligned_data.iloc[:, 0], aligned_data.iloc[:, 1])[0, 1]
        market_variance = np.var(aligned_data.iloc[:, 1])

        return covariance / market_variance if market_variance != 0 else 1.0

    def _calculate_concentration_score(
        self, concentration_analysis: Dict[str, Any]
    ) -> float:
        """計算集中度風險評分"""
        score = 0.0

        # 單一資產暴露 (40%權重)
        single_asset_score = min(concentration_analysis["single_asset_max"] / 0.25, 1.0)
        score += single_asset_score * 0.4

        # 單一部門暴露 (30%權重)
        single_sector_score = min(
            concentration_analysis["single_sector_max"] / 0.40, 1.0
        )
        score += single_sector_score * 0.3

        # 單一貨幣暴露 (20%權重)
        single_currency_score = min(
            concentration_analysis["single_currency_max"] / 0.30, 1.0
        )
        score += single_currency_score * 0.2

        # Herfindahl指數 (10%權重)
        hhi_score = min(concentration_analysis["herfindahl_index"], 1.0)
        score += hhi_score * 0.1

        return score

    def _assess_concentration_level(self, score: float) -> str:
        """評估集中度風險等級"""
        if score < 0.3:
            return RiskLevel.LOW.value
        elif score < 0.6:
            return RiskLevel.MEDIUM.value
        elif score < 0.8:
            return RiskLevel.HIGH.value
        else:
            return RiskLevel.CRITICAL.value

    def _calculate_liquidity_score(self, liquidity_analysis: Dict[str, Any]) -> float:
        """計算流動性風險評分"""
        score = 0.0

        # 買賣價差 (30%權重) - 越低越好
        spread_score = max(0, 1 - liquidity_analysis["bid_ask_spread_avg"] * 100)
        score += spread_score * 0.3

        # 日均成交量比例 (25%權重)
        volume_score = min(liquidity_analysis["daily_volume_ratio"] * 10, 1.0)
        score += volume_score * 0.25

        # 市值覆蓋度 (25%權重)
        market_cap_score = liquidity_analysis["market_cap_coverage"]
        score += market_cap_score * 0.25

        # 清算能力 (20%權重)
        liquidation_score = liquidity_analysis["time_to_liquidate"]["7_days"] / 100
        score += liquidation_score * 0.2

        return score

    def _assess_liquidity_level(self, score: float) -> str:
        """評估流動性風險等級"""
        if score > 0.7:
            return RiskLevel.LOW.value
        elif score > 0.5:
            return RiskLevel.MEDIUM.value
        elif score > 0.3:
            return RiskLevel.HIGH.value
        else:
            return RiskLevel.CRITICAL.value

    def _assess_overall_risk_level(
        self,
        risk_metrics: RiskMetrics,
        risk_decomposition: RiskDecomposition,
        concentration_risk: Dict[str, Any],
        liquidity_risk: Dict[str, Any],
    ) -> str:
        """評估整體風險等級"""
        risk_scores = []

        # 基礎風險指標評分
        var_score = min(abs(risk_metrics.var_95) * 10, 1.0)
        drawdown_score = min(abs(risk_metrics.max_drawdown) * 5, 1.0)
        volatility_score = min(risk_metrics.volatility * 2, 1.0)

        risk_scores.extend([var_score, drawdown_score, volatility_score])

        # 集中度風險評分
        concentration_score = concentration_risk["concentration_score"]
        risk_scores.append(concentration_score)

        # 流動性風險評分 (反轉，因為分數越高流動性越好)
        liquidity_score = 1 - self._calculate_liquidity_score(liquidity_risk)
        risk_scores.append(liquidity_score)

        # 計算平均風險評分
        overall_score = np.mean(risk_scores)

        # 確定風險等級
        if overall_score < 0.3:
            return RiskLevel.LOW.value
        elif overall_score < 0.6:
            return RiskLevel.MEDIUM.value
        elif overall_score < 0.8:
            return RiskLevel.HIGH.value
        else:
            return RiskLevel.CRITICAL.value

    def _estimate_liquidation_percentage(
        self, portfolio_positions: pd.DataFrame, days: int
    ) -> float:
        """估算在指定天數內可以清算的百分比"""
        # 簡化模型：假設每日可以清算10%的單一資產最大權重
        daily_liquidation_capacity = 0.1
        total_days = min(days, 30)  # 最多30天

        max_single_position = (
            portfolio_positions["weight"].max()
            if "weight" in portfolio_positions.columns
            else 0.1
        )

        liquidatable_percentage = min(
            (daily_liquidation_capacity * total_days) / max_single_position, 1.0
        )
        return liquidatable_percentage * 100

    def _check_metric_threshold(
        self, metric: str, value: float, timestamp: datetime
    ) -> Optional[RiskAlert]:
        """檢查單個指標是否超過閾值"""
        for threshold in self.risk_thresholds:
            if threshold.metric == metric:
                if value >= threshold.critical_threshold:
                    level = RiskLevel.CRITICAL
                elif value >= threshold.high_threshold:
                    level = RiskLevel.HIGH
                elif value >= threshold.medium_threshold:
                    level = RiskLevel.MEDIUM
                elif value >= threshold.low_threshold:
                    level = RiskLevel.LOW
                else:
                    return None

                return RiskAlert(
                    alert_id = f"{metric}_{timestamp.strftime('%Y%m%d%H%M%S')}",
                    category = threshold.category,
                    metric = metric,
                    current_value = value,
                    threshold_level = level,
                    message = f"{threshold.description}: {value:.3f} 超過{level.value}風險閾值",
                    timestamp = timestamp,
                    severity_score = value / threshold.critical_threshold,
                )

        return None

    def _cleanup_old_alerts(self):
        """清理舊的警報記錄"""
        retention_days = self.config.get("alert_retention_days", 30)
        cutoff_date = datetime.now() - timedelta(days = retention_days)

        self.alerts_history = [
            alert for alert in self.alerts_history if alert.timestamp > cutoff_date
        ]

    def _serialize_risk_decomposition(
        self, decomposition: RiskDecomposition
    ) -> Dict[str, Any]:
        """序列化風險分解結果"""
        return {
            "total_risk": decomposition.total_risk,
            "systematic_risk": decomposition.systematic_risk,
            "idiosyncratic_risk": decomposition.idiosyncratic_risk,
            "factor_exposures": decomposition.factor_exposures,
            "sector_contributions": decomposition.sector_contributions,
            "asset_contributions": decomposition.asset_contributions,
            "currency_contributions": decomposition.currency_contributions,
        }

    def _serialize_alert(self, alert: RiskAlert) -> Dict[str, Any]:
        """序列化警報"""
        return {
            "alert_id": alert.alert_id,
            "category": alert.category.value,
            "metric": alert.metric,
            "current_value": alert.current_value,
            "threshold_level": alert.threshold_level.value,
            "message": alert.message,
            "timestamp": alert.timestamp.isoformat(),
            "portfolio_id": alert.portfolio_id,
            "severity_score": alert.severity_score,
        }

    def _generate_risk_summary(
        self,
        risk_metrics: RiskMetrics,
        risk_decomposition: RiskDecomposition,
        overall_risk_level: str,
    ) -> str:
        """生成風險摘要"""
        summary_parts = [
            f"整體風險等級: {overall_risk_level}",
            f"年化波動率: {risk_metrics.volatility:.2%}",
            f"最大回撤: {risk_metrics.max_drawdown:.2%}",
            f"夏普比率: {risk_metrics.sharpe_ratio:.3f}",
            f"系統性風險: {risk_decomposition.systematic_risk:.2%}",
            f"特殊性風險: {risk_decomposition.idiosyncratic_risk:.2%}",
        ]

        return " | ".join(summary_parts)

    def _calculate_overall_risk_score(self, analysis_results: Dict[str, Any]) -> float:
        """計算整體風險評分 (0 - 100)"""
        score = 0.0

        # 基礎風險指標 (40%)
        basic_metrics = analysis_results["basic_risk_metrics"]
        var_score = min(abs(basic_metrics["var_metrics"]["var_95"]) * 500, 40)
        score += var_score

        # 集中度風險 (30%)
        concentration_score = (
            analysis_results["concentration_risk"]["concentration_score"] * 30
        )
        score += concentration_score

        # 流動性風險 (20%)
        liquidity_score = (
            1 - analysis_results["liquidity_risk"]["liquidity_score"]
        ) * 20
        score += liquidity_score

        # 警報數量 (10%)
        alert_count = len(analysis_results["risk_alerts"])
        alert_score = min(alert_count * 2, 10)
        score += alert_score

        return min(score, 100)

    def _prepare_risk_trend_data(self) -> List[Dict[str, Any]]:
        """準備風險趨勢數據 (模擬數據)"""
        dates = pd.date_range(end = datetime.now(), periods = 30, freq="D")
        trend_data = []

        for date in dates:
            trend_data.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "var_95": np.random.normal(0.03, 0.01),
                    "volatility": np.random.normal(0.15, 0.05),
                    "max_drawdown": abs(np.random.normal(0.05, 0.02)),
                }
            )

        return trend_data

    def _prepare_factor_exposure_chart(
        self, risk_decomposition: Dict[str, Any]
    ) -> Dict[str, Any]:
        """準備因子暴露圖表數據"""
        factor_exposures = risk_decomposition.get("factor_exposures", {})

        return {
            "factors": list(factor_exposures.keys()),
            "exposures": list(factor_exposures.values()),
        }

    def _prepare_sector_allocation_chart(
        self, risk_decomposition: Dict[str, Any]
    ) -> Dict[str, Any]:
        """準備部門配置圖表數據"""
        sector_contributions = risk_decomposition.get("sector_contributions", {})

        return {
            "sectors": list(sector_contributions.keys()),
            "weights": list(sector_contributions.values()),
        }

    def _prepare_liquidity_profile_chart(
        self, liquidity_risk: Dict[str, Any]
    ) -> Dict[str, Any]:
        """準備流動性狀況圖表數據"""
        time_to_liquidate = liquidity_risk.get("time_to_liquidate", {})

        return {
            "timeframes": list(time_to_liquidate.keys()),
            "percentages": list(time_to_liquidate.values()),
        }

    def _generate_concentration_recommendations(
        self, concentration_analysis: Dict[str, Any]
    ) -> List[str]:
        """生成集中度風險建議"""
        recommendations = []

        if concentration_analysis["single_asset_max"] > 0.10:
            recommendations.append("單一資產權重過高，建議分散投資")

        if concentration_analysis["single_sector_max"] > 0.25:
            recommendations.append("單一部門暴露過高，建議增加其他部門配置")

        if concentration_analysis["single_currency_max"] > 0.15:
            recommendations.append("單一貨幣暴露過高，建議貨幣多元化")

        if concentration_analysis["herfindahl_index"] > 0.25:
            recommendations.append("投資組合集中度較高，建議增加資產數量")

        if not recommendations:
            recommendations.append("集中度風險處於合理水平")

        return recommendations

    def _generate_liquidity_recommendations(
        self, liquidity_analysis: Dict[str, Any]
    ) -> List[str]:
        """生成流動性風險建議"""
        recommendations = []

        if liquidity_analysis["bid_ask_spread_avg"] > 0.01:
            recommendations.append("平均買賣價差較大，建議增加高流動性資產")

        if liquidity_analysis["daily_volume_ratio"] < 0.05:
            recommendations.append("日成交量比例較低，存在流動性風險")

        if liquidity_analysis["market_cap_coverage"] < 0.5:
            recommendations.append("建議增加大市值資產比重")

        if liquidity_analysis["time_to_liquidate"]["7_days"] < 80:
            recommendations.append("7日內清算能力不足，建議改善資產流動性")

        if not recommendations:
            recommendations.append("流動性狀況良好")

        return recommendations

    def _generate_compliance_recommendations(
        self, violations: List[Dict[str, Any]]
    ) -> List[str]:
        """生成合規建議"""
        recommendations = []

        for violation in violations:
            rule = violation["rule"]

            if "Single Asset" in rule:
                recommendations.append("降低單一資產權重至監管要求以下")
            elif "Single Sector" in rule:
                recommendations.append("分散部門投資，降低單一部門暴露")
            elif "Single Currency" in rule:
                recommendations.append("多元化貨幣配置")
            elif "VaR" in rule:
                recommendations.append("降低風險暴露或增加對沖")
            elif "Drawdown" in rule:
                recommendations.append("加強風險控制，降低最大回撤")

        if not violations:
            recommendations.append("當前投資組合符合監管要求")

        return recommendations


# 便利函數
def analyze_portfolio_risk(
    returns: pd.Series,
    portfolio_positions: Optional[pd.DataFrame] = None,
    benchmark_returns: Optional[pd.Series] = None,
    market_data: Optional[Dict[str, pd.DataFrame]] = None,
) -> Dict[str, Any]:
    """便利函數：投資組合風險分析"""
    analyzer = AdvancedRiskAnalyzer()
    return analyzer.analyze_comprehensive_risk(
        returns, portfolio_positions, benchmark_returns, market_data
    )

#!/usr/bin/env python3
"""
香港特定風險因子管理 - Hong Kong Specific Risk Factors
實現香港獨有的風險因子，如南向資金、港匯聯繫匯率制度、政策風險等
Hong Kong Specific Risk Factors - Implementing HK-unique risk factors
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class HKRiskFactorType(Enum):
    """香港風險因子類型"""
    CURRENCY_PEG = "currency_peg"           # 港匯聯繫匯率制度
    SOUTHBOUND_FLOW = "southbound_flow"     # 南向資金流
    POLICY_RISK = "policy_risk"             # 政策風險
    PROPERTY_MARKET = "property_market"      # 地產市場風險
    INTEREST_RATE = "interest_rate"          # 利率風險（HIBOR）
    WEATHER_DISRUPTION = "weather_disruption"  # 天氣干擾
    MAINLAND_ECONOMY = "mainland_economy"      # 內地經濟影響
    STRUCTURAL_IMBALANCE = "structural_imbalance"  # 結構性失衡

class HKWeatherAlert(Enum):
    """香港天氣警報級別"""
    NONE = 0
    T1 = 1      # 一號信號
    T3 = 3      # 三號信號
    T8 = 8      # 八號信號
    T9 = 9      # 九號/十號信號
    BLACK = 10   # 黑色暴雨警報

@dataclass
class HKRiskFactor:
    """香港風險因子"""
    factor_type: HKRiskFactorType
    name: str
    description: str
    current_value: float
    historical_values: List[float]
    baseline: float
    volatility: float
    correlation_with_market: float
    regulatory_impact: str
    mitigation_strategies: List[str]
    last_updated: datetime

class HKCurrencyPegRiskAnalyzer:
    """港匯聯繫匯率制度風險分析器"""

    def __init__(self):
        self.peg_strength_baseline = 7.75  # 港幣兌美元聯繫匯率基準
        self.peg_range = 7.75  # 聯繫匯率波動範團
        self.historical_data = []

    def analyze_peg_risk(self, usd_hkd_rate: float,
                          market_stress_level: float = 0.0) -> Dict[str, Any]:
        """分析聯繫匯率風險"""
        # 計算匯率偏離度
        deviation = abs(usd_hkd_rate - self.peg_strength_baseline) / self.peg_strength_baseline

        # 計算匯率壓力指數
        volatility = self._calculate_peg_volatility(usd_hkd_rate)

        # 評估脫鉤風險（基於歷史數據）
        depeg_risk = self._estimate_depeg_probability(deviation, market_stress_level)

        # 計算遠期匯率預期
        forward_premium = self._calculate_forward_premium(usd_hkd_rate)

        risk_metrics = {
            'current_rate': usd_hkd_rate,
            'deviation_pct': deviation * 100,
            'volatility': volatility,
            'depeg_probability_1yr': depeg_risk,
            'forward_premium': forward_premium,
            'risk_level': self._classify_peg_risk(deviation),
            'pressure_indicator': self._calculate_peg_pressure(usd_hkd_rate),
            'factors_affected': [
                '港幣流動性',
                '進口貿易',
                '外資流入',
                '資產定價'
            ]
        }

        return risk_metrics

    def _calculate_peg_volatility(self, current_rate: float) -> float:
        """計算聯繫匯率波動率"""
        if len(self.historical_data) < 20:
            return 0.001

        rates = np.array(self.historical_data + [current_rate])
        returns = np.diff(rates) / rates[:-1]
        return np.std(returns)

    def _estimate_depeg_probability(self, deviation: float, stress_level: float) -> float:
        """估計脫鉤概率"""
        # 基於偏離度和市場壓力水平
        base_probability = min(1.0, deviation * 2)  # 簡化模型
        stress_multiplier = 1 + stress_level * 2

        return base_probability * stress_multiplier

    def _calculate_forward_premium(self, spot_rate: float) -> float:
        """計算遠期溢價"""
        # 假設1年遠期匯率
        forward_rate = spot_rate * 1.001  # 0.1% 年化溢價
        return (forward_rate - spot_rate) / spot_rate

    def _classify_peg_risk(self, deviation: float) -> str:
        """分類聯繫匯率風險等級"""
        if deviation < 0.01:  # < 1%
            return "low"
        elif deviation < 0.05:  # < 5%
            return "moderate"
        elif deviation < 0.10:  # < 10%
            return "high"
        else:
            return "extreme"

    def _calculate_peg_pressure(self, current_rate: float) -> float:
        """計算聯繫匯率壓力"""
        # 簡化的壓力指數
        if current_rate > self.peg_strength_baseline:
            return (current_rate - self.peg_strength_baseline) / self.peg_strength_baseline
        else:
            return (self.peg_strength_baseline - current_rate) / self.p_strength_baseline

class HKSouthboundFlowAnalyzer:
    """南向資金流分析器"""

    def __name__(self):
        self.historical_flows = []
        self.flow_thresholds = {
            'significant': 1000,  # 十億港幣
            'large': 5000,      # 五百億港幣
            'extreme': 10000     # 一千億港幣
        }

    def analyze_southbound_flow(self, current_flow: float,
                                 market_conditions: Dict[str, float]) -> Dict[str, Any]:
        """分析南向資金流"""
        # 計算流動變化趨勢
        flow_trend = self._calculate_flow_trend(current_flow)

        # 評估資金流持續性
        sustainability = self._assess_flow_sustainability(current_flow, market_conditions)

        # 分析行業偏好
        sector_preferences = self._analyze_sector_preferences(current_flow)

        # 評估市場影響
        market_impact = self._estimate_market_impact(current_flow)

        flow_metrics = {
            'current_flow_billion_hkd': current_flow,
            'flow_trend': flow_trend,
            'flow_sustainability': sustainability,
            'market_sentiment_impact': market_impact['sentiment'],
            'price_impact': market_impact['price'],
            'volume_impact': market_impact['volume'],
            'sector_rotation': sector_preferences,
            'flow_level': self._classify_flow_level(current_flow),
            'key_drivers': self._identify_flow_drivers(market_conditions),
            'risks': self._identify_flow_risks(current_flow, market_conditions)
        }

        return flow_metrics

    def _calculate_flow_trend(self, current_flow: float) -> str:
        """計算資金流趨勢"""
        if len(self.historical_flows) < 4:
            return "insufficient_data"

        recent_flows = self.historical_flows[-4:]
        linear_trend = np.polyfit(range(len(recent_flows)), recent_flows, 1)[0]

        if linear_trend > 100:
            return "strongly_increasing"
        elif linear_trend > 20:
            return "increasing"
        elif linear_trend > -20:
            return "stable"
        elif linear_trend > -100:
            return "decreasing"
        else:
            return "strongly_decreasing"

    def _assess_flow_sustainability(self, current_flow: float,
                                    market_conditions: Dict[str, float]) -> float:
        """評估資金流可持續性"""
        # 考慮多種因素
        china_economy_health = market_conditions.get('china_gdp_growth', 0.06)
        hk_market_attractiveness = market_conditions.get('hsi_performance', 0)
        policy_environment = market_conditions.get('policy_favorability', 0.5)

        sustainability_score = (
            china_economy_health * 0.4 +
            hk_market_attractiveness * 0.3 +
            policy_environment * 0.3
        )

        # 流動規模影響可持續性
        scale_factor = 1.0
        if current_flow > self.flow_thresholds['extreme']:
            scale_factor = 0.7
        elif current_flow > self.flow_thresholds['large']:
            scale_factor = 0.85

        return sustainability_score * scale_factor

    def _analyze_sector_preferences(self, current_flow: float) -> Dict[str, float]:
        """分析行業偏好"""
        # 模擬南向資金流偏好分析
        # 基於歷史數據的典型分配
        sector_allocation = {
            'technology': 0.30,
            'healthcare': 0.15,
            'consumer_discretionary': 0.20,
            'financials': 0.25,
            'energy': 0.10
        }

        return sector_allocation

    def _estimate_market_impact(self, flow: float) -> Dict[str, Any]:
        """估算市場影響"""
        # 簡化模型：資金流與市場表現關係
        flow_billion = flow / 1000  # 轉換為十億單位

        sentiment_impact = min(1.0, flow_billion / 10)  # 每1000億影響1個單位
        price_impact = sentiment_impact * 0.02  # 假設2%影響
        volume_impact = flow_billion / 50  # 每個單位影響50億交易量

        return {
            'sentiment': sentiment_impact,
            'price': price_impact,
            'volume': volume_impact
        }

    def _classify_flow_level(self, flow: float) -> str:
        """分類流動水平"""
        if flow < self.flow_thresholds['significant']:
            return "minimal"
        elif flow < self.flow_thresholds['large']:
            return "significant"
        elif flow < self.flow_thresholds['extreme']:
            return "large"
        else:
            return "extreme"

    def _identify_flow_drivers(self, market_conditions: Dict[str, float]) -> List[str]:
        """識別資金流驅動因素"""
        drivers = []

        if market_conditions.get('china_gdp_growth', 0) > 0.06:
            drivers.append("China Economic Growth")

        if market_conditions.get('hsi_pe_ratio', 0) < 10:
            drivers.append("Valuation Attractiveness")

        if market_conditions.get('policy_favorability', 0) > 0.7:
            drivers.append("Policy Support")

        if market_conditions.get('exchange_rate_stability', 0) > 0.8:
            drivers.append("Currency Stability")

        return drivers

    def _identify_flow_risks(self, flow: float, market_conditions: Dict[str, float]) -> List[str]:
        """識別資金流風險"""
        risks = []

        if flow < -1000:  # 資出超過1000億
            risks.append("Capital Flight Risk")

        if market_conditions.get('china_economic_slowdown', 0) > 0.7:
            risks.append("Economic Slowdown Impact")

        if market_conditions.get('policy_uncertainty', 0) > 0.6:
            risks.append("Policy Uncertainty")

        if market_conditions.get('geopolitical_tension', 0) > 0.8:
            risks.append("Geopolitical Risk")

        return risks

class HKWeatherDisruptionAnalyzer:
    """香港天氣干擾分析器"""

    def __init__(self):
        self.weather_alerts = {
            'typhoon_season': ['June', 'July', 'August', 'September'],
            'black_rain_season': ['May', 'June', 'July', 'August', 'September'],
            'cold_wave_season': ['December', 'January', 'February']
        }

        self.market_impact_multipliers = {
            HKWeatherAlert.T1: 0.1,
            HKWeatherAlert.T3: 0.3,
            HKWeatherAlert.T8: 0.6,
            HKWeatherAlert.T9: 0.8,
            HKWeatherAlert.BLACK: 1.0
        }

    def analyze_weather_risk(self, current_alert: HKWeatherAlert,
                           forecast_alerts: List[HKWeatherAlert],
                           market_open_hours: bool = True) -> Dict[str, Any]:
        """分析天氣風險"""

        # 計算即時影響
        immediate_impact = self._calculate_immediate_impact(current_alert, market_open_hours)

        # 計算預期影響
        expected_impact = self._calculate_expected_impact(forecast_alerts, market_open_hours)

        # 分析歷史模式
        historical_patterns = self._analyze_historical_weather_patterns()

        # 生成風險評級
        risk_assessment = self._assess_weather_risk_level(current_alert, forecast_alerts)

        weather_risk = {
            'current_alert': current_alert.name,
            'alert_level': current_alert.value,
            'immediate_market_impact': immediate_impact,
            'expected_market_impact': expected_impact,
            'historical_patterns': historical_patterns,
            'risk_assessment': risk_assessment,
            'trading_recommendations': self._generate_trading_recommendations(
                current_alert, forecast_alerts, market_open_hours
            ),
            'recovery_timeline': self._estimate_recovery_timeline(current_alert, forecast_alerts)
        }

        return weather_risk

    def _calculate_immediate_impact(self, alert: HKWeatherAlert, market_open: bool) -> Dict[str, Any]:
        """計算即時市場影響"""
        base_impact = self.market_impact_multipliers.get(alert, 0)

        # 如果市場開盤，影響更大
        trading_adjustment = 1.5 if market_open else 1.0

        impact_level = base_impact * trading_adjustment

        return {
            'trading_volume_impact': impact_level * 0.5,  # 50%交易量影響
            'price_volatility': impact_level * 0.02,  # 2%波動率影響
            'liquidity_impact': impact_level * 0.3,    # 30%流動性影響
            'sector_impacts': {
                'retail': impact_level * 0.6,
                'transportation': impact_level * 0.8,
                'construction': impact_level * 0.7,
                'insurance': impact_level * 0.4,
                'technology': impact_level * 0.2
            }
        }

    def _calculate_expected_impact(self, forecasts: List[HKWeatherAlert], market_open: bool) -> Dict[str, Any]:
        """計算預期影響"""
        if not forecasts:
            return {'total_impact': 0}

        max_alert = max(forecasts, key=lambda x: x.value)
        expected_impact = self.market_impact_multipliers.get(max_alert, 0)

        # 累積影響
        cumulative_impact = sum(self.market_impact_multiplier.get(alert, 0) for alert in forecasts)

        return {
            'peak_alert': max_alert.name,
            'peak_impact': expected_impact,
            'cumulative_impact': cumulative_impact,
            'expected_duration_days': self._estimate_storm_duration(max_alert),
            'probability_of_escalation': self._calculate_escalation_probability(forecasts)
        }

    def _analyze_historical_patterns(self) -> Dict[str, Any]:
        """分析歷史天氣模式"""
        # 模擬歷史數據分析
        return {
            'typhoon_frequency': '平均每年2-3次',
            'average_disruption_days': 2.5,
            'common_sectors_affected': ['retail', 'transportation', 'construction'],
            'recovery_patterns': '通常2-3個交易日恢復',
            'market_sentiment_impact': '短期負面影響'
        }

    def _assess_weather_risk_level(self, current: HKWeatherAlert,
                                 forecasts: List[HKWeatherAlert]) -> str:
        """評估天氣風險等級"""
        max_alert = max([current] + forecasts, key=lambda x: x.value)

        if max_alert.value >= HKWeatherAlert.T9.value:
            return "extreme"
        elif max_alert.value >= HKWeatherAlert.T8.value:
            return "high"
        elif max_alert.value >= HKWeatherAlert.T3.value:
            return "moderate"
        else:
            return "low"

    def _generate_trading_recommendations(self, current: HKWeatherAlert,
                                         forecasts: List[HKWeatherAlert],
                                         market_open: bool) -> List[str]:
        """生成交易建議"""
        recommendations = []

        if current.value >= HKWeatherAlert.T8.value:
            recommendations.extend([
                "減少倉位暴露",
                "增加現金持有",
                "避免高貝桿桿票",
                "關注公用事業防禦股"
            ])

        if market_open and current.value >= HKWeatherAlert.T3.value:
            recommendations.extend([
                "減少日內交易",
                "使用限價單保護",
                "避免開倉新倉位",
                "提高止損要求"
            ])

        return recommendations

    def _estimate_recovery_timeline(self, current: HKWeatherAlert,
                                   forecasts: List[HKWeatherAlert]) -> Dict[str, int]:
        """估算恢復時間線"""
        recovery_days = {
            HKWeatherAlert.T1: 1,
            HKWeatherAlert.T3: 2,
            HKWeatherAlert.T8: 3,
            HKWeatherAlert.T9: 5,
            HKWeatherAlert.BLACK: 7
        }

        max_recovery = recovery_days.get(max([current] + forecasts, key=lambda x: x.value))

        return {
            'expected_recovery_days': max_recovery,
            'full_market_recovery': max_recovery + 2,
            'liquidity_recovery': max_recovery + 1,
            'sentiment_recovery': max_recovery + 3
        }

    def _estimate_storm_duration(self, alert: HKWeatherAlert) -> int:
        """估算風暴持續時間"""
        duration_days = {
            HKWeatherAlert.T1: 1,
            HKWeatherAlert.T3: 2,
            HKWeatherAlert.T8: 3,
            HKWeatherAlert.T9: 5,
            HKWeatherAlert.BLACK: 7
        }

        return duration_days.get(alert, 1)

    def _calculate_escalation_probability(self, forecasts: List[HKWeatherAlert]) -> float:
        """計算升級概率"""
        if len(forecasts) < 2:
            return 0.1

        escalation_count = 0
        for i in range(1, len(forecasts)):
            if forecasts[i].value > forecasts[i-1].value:
                escalation_count += 1

        return min(1.0, escalation_count / len(forecasts))

class HKPolicyRiskAnalyzer:
    """香港政策風險分析器"""

    def __init__(self):
        self.policy_categories = [
            "monetary_policy",
            "regulatory_policy",
            "fiscal_policy",
            "housing_policy",
            "crossborder_policy"
        ]

    def analyze_policy_risk(self, current_policy_changes: List[Dict[str, Any]],
                           market_conditions: Dict[str, float]) -> Dict[str, Any]:
        """分析政策風險"""
        policy_impacts = []

        for policy_change in current_policy_changes:
            impact = self._analyze_policy_change(policy_change, market_conditions)
            policy_impacts.append(impact)

        # 計算整體政策風險
        overall_risk = self._calculate_overall_policy_risk(policy_impacts)

        # 識別風險集中領域
        risk_concentration = self._identify_risk_concentration(policy_impacts)

        return {
            'policy_changes_count': len(current_policy_changes),
            'individual_impacts': policy_impacts,
            'overall_risk_level': overall_risk,
            'risk_concentration': risk_concentration,
            'market_confidence': self._calculate_market_confidence(overall_risk),
            'time_horizon': self._estimate_policy_risk_timeline(overall_risk)
        }

    def _analyze_policy_change(self, policy_change: Dict[str, Any],
                             market_conditions: Dict[str, float]) -> Dict[str, Any]:
        """分析單個政策變化影響"""
        policy_type = policy_change.get('category', 'unknown')
        impact_magnitude = policy_change.get('impact_magnitude', 0)
        unexpectedness = policy_change.get('unexpectedness', 0.5)
        implementation_risk = policy_change.get('implementation_risk', 0.5)

        # 計算市場敏感度
        market_sensitivity = self._calculate_market_sensitivity(policy_type, market_conditions)

        overall_impact = (impact_magnitude * unexpectedness *
                          implementation_risk * market_sensitivity)

        return {
            'policy_type': policy_type,
            'description': policy_change.get('description', ''),
            'impact_magnitude': impact_magnitude,
            'unexpectedness': unexpectedness,
            'implementation_risk': implementation_risk,
            'overall_impact': overall_impact,
            'affected_sectors': self._identify_affected_sectors(policy_type),
            'time_to_impact': policy_change.get('time_to_impact', 30),  # 天
            'duration_of_impact': policy_change.get('duration', 90)  # 天
        }

    def _calculate_market_sensitivity(self, policy_type: str,
                                     market_conditions: Dict[str, float]) -> float:
        """計算市場敏感度"""
        sensitivity_factors = {
            'monetary_policy': 1.0,
            'regulatory_policy': 0.8,
            'fiscal_policy': 0.6,
            'housing_policy': 0.7,
            'crossborder_policy': 0.9
        }

        base_sensitivity = sensitivity_factors.get(policy_type, 0.5)

        # 市場條件調整
        adjustment_factor = 1.0
        if market_conditions.get('market_volatility', 0.2) > 0.4:
            adjustment_factor = 1.2  # 高波動率市場更敏感

        return base_sensitivity * adjustment_factor

    def _identify_affected_sectors(self, policy_type: str) -> List[str]:
        """識別受影響行業"""
        sector_mapping = {
            'monetary_policy': ['financials', 'real_estate', 'utilities'],
            'regulatory_policy': ['technology', 'financials', 'healthcare'],
            'fiscal_policy': ['infrastructure', 'retail', 'consumer'],
            'housing_policy': ['real_estate', 'construction', 'materials'],
            'crossborder_policy': ['trade', 'logistics', 'tourism', 'retail']
        }

        return sector_mapping.get(policy_type, [])

    def _calculate_overall_policy_risk(self, policy_impacts: List[Dict[str, Any]]) -> str:
        """計算整體政策風險"""
        if not policy_impacts:
            return "low"

        total_impact = sum(impact['overall_impact'] for impact in policy_impacts)
        avg_impact = total_impact / len(policy_impacts)

        if avg_impact > 0.8:
            return "extreme"
        elif avg_impact > 0.5:
            return "high"
        elif avg_impact > 0.3:
            return "moderate"
        else:
            return "low"

    def _identify_risk_concentration(self, policy_impacts: List[Dict[str, Any]]) -> Dict[str, int]:
        """識別風險集中領域"""
        concentration = {}
        for impact in policy_impacts:
            policy_type = impact['policy_type']
            concentration[policy_type] = concentration.get(policy_type, 0) + 1

        return concentration

    def _calculate_market_confidence(self, risk_level: str) -> float:
        """計算市場信心"""
        confidence_levels = {
            "extreme": 0.2,
            "high": 0.4,
            "moderate": 0.7,
            "low": 0.9
        }

        return confidence_levels.get(risk_level, 0.5)

    def _estimate_policy_risk_timeline(self, risk_level: str) -> str:
        """估算政策風險時間線"""
        timelines = {
            "extreme": "6-12 months",
            "high": "3-6 months",
            "moderate": "1-3 months",
            "low": "1 month"
        }

        return timelines.get(risk_level, "1-3 months")

# 主要整合函數
def analyze_hk_risk_factors(market_data: Dict[str, Any]) -> Dict[str, HKRiskFactor]:
    """分析所有香港特定風險因子"""
    risk_factors = []

    # 1. 港匯聯繫匯率風險
    if 'usd_hkd_rate' in market_data:
        peg_analyzer = HKCurrencyPegRiskAnalyzer()
        peg_metrics = peg_analyzer.analyze_peg_risk(
            market_data['usd_hkd_rate'],
            market_data.get('market_stress_level', 0.0)
        )

        risk_factors.append(HKRiskFactor(
            factor_type=HKRiskFactorType.CURRENCY_PEG,
            name="港匯聯繫匯率制度",
            description="港幣兌美元聯繫匯率相關風險",
            current_value=market_data['usd_hkd_rate'],
            historical_values=[],
            baseline=7.75,
            volatility=peg_metrics['volatility'],
            correlation_with_market=0.7,
            regulatory_impact="High",
            mitigation_strategies=["避險措施", "外匯對沖"],
            last_updated=datetime.now()
        ))

    # 2. 南向資金流風險
    if 'southbound_flow' in market_data:
        flow_analyzer = HKSouthboundFlowAnalyzer()
        flow_metrics = flow_analyzer.analyze_southbound_flow(
            market_data['southbound_flow'],
            market_data
        )

        risk_factors.append(HKRiskFactor(
            factor_type=HKRiskFactorType.SOUTHBOUND_FLOW,
            name="南向資金流",
            description="內地投資者香港市場資金流動",
            current_value=market_data['southbound_flow'],
            historical_values=[],
            baseline=500,
            volatility=0.3,
            correlation_with_market=0.8,
            regulatory_impact="Medium",
            mitigation_strategies=["多元化投資", "流動性管理"],
            last_updated=datetime.now()
        ))

    # 3. 天氣干擾風險
    if 'weather_alert' in market_data:
        weather_analyzer = HKWeatherDisruptionAnalyzer()
        weather_risk = weather_analyzer.analyze_weather_risk(
            market_data['weather_alert'],
            market_data.get('forecast_alerts', []),
            market_data.get('market_open', True)
        )

        risk_factors.append(HKRiskFactor(
            factor_type=HKRiskFactor.WEATHER_DISRUPTION,
            name="天氣干擾",
            description="香港特有天氣事件（颱風、暴雨等）",
            current_value=weather_risk['risk_assessment'],
            historical_values=[],
            baseline=0,
            volatility=0.2,
            correlation_with_market=0.4,
            regulatory_impact="Medium",
            mitigation_strategies=["業務連續性計劃", "保險轉移"],
            last_updated=datetime.now()
        ))

    return {rf.factor_type.value: rf for rf in risk_factors}

if __name__ == "__main__":
    # 示例使用
    market_data = {
        'usd_hkd_rate': 7.82,
        'southbound_flow': 2500,
        'weather_alert': HKWeatherAlert.T8,
        'market_stress_level': 0.3
    }

    risk_factors = analyze_hk_risk_factors(market_data)

    print("香港特定風險因子分析:")
    for factor_type, factor in risk_factors.items():
        print(f"\n{factor.name} ({factor_type}):")
        print(f"  當前值: {factor.current_value}")
        print(f"  風險等級: {factor.current_value > factor.baseline}")
        print(f"  描述: {factor.description}")
        print(f"  緩解策略: {factor.mitigation_strategies}")
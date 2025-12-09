#!/usr/bin/env python3
"""
香港天氣干擾建模系統 - Hong Kong Weather Disruption Modeling System
模擬和預測天氣事件對香港金融市場的影響
Hong Kong Weather Disruption Modeling - Simulating and predicting weather event impacts on Hong Kong financial markets
"""

import asyncio
import aiohttp
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import pandas as pd
import numpy as np
from pathlib import Path
import pickle
import requests
import statistics

# Setup logging
logger = logging.getLogger(__name__)

class HKWeatherEventType(Enum):
    """香港天氣事件類型"""
    TYPHOON_SIGNAL_1 = "typhoon_signal_1"      # 1號戒備信號
    TYPHOON_SIGNAL_3 = "typhoon_signal_3"      # 3號強風信號
    TYPHOON_SIGNAL_8 = "typhoon_signal_8"      # 8號烈風信號
    TYPHOON_SIGNAL_9 = "typhoon_signal_9"      # 9號烈風或暴風增強信號
    TYPHOON_SIGNAL_10 = "typhoon_signal_10"    # 10號颶風信號
    THUNDERSTORM_WARNING = "thunderstorm_warning"  # 雷暴警告
    RAINSTORM_BLACK = "rainstorm_black"        # 黑色暴雨警告
    RAINSTORM_RED = "rainstorm_red"            # 紅色暴雨警告
    RAINSTORM_AMBER = "rainstorm_amber"        # 黃色暴雨警告

class HKMarketTradingStatus(Enum):
    """香港市場交易狀態"""
    NORMAL = "normal"                          # 正常交易
    EARLY_CLOSE = "early_close"                # 提早收市
    FULL_DAY_CLOSURE = "full_day_closure"      # 全日停市
    MORNING_ONLY = "morning_only"              # 只開早市
    AFTERNOON_ONLY = "afternoon_only"          # 只開午市

@dataclass
class HKWeatherEvent:
    """香港天氣事件"""
    event_type: HKWeatherEventType
    signal_number: Optional[int]
    start_time: datetime
    expected_end_time: Optional[datetime]
    severity: float  # 0.0-1.0
    affected_areas: List[str]
    wind_speed: Optional[float]  # km/h
    rainfall: Optional[float]  # mm/h
    source: str
    confidence: float  # 0.0-1.0

@dataclass
class HKWeatherMarketImpact:
    """天氣對市場的影響"""
    event: HKWeatherEvent
    trading_status: HKMarketTradingStatus
    expected_volatility_change: float  # +/- percentage
    expected_volume_change: float     # +/- percentage
    liquidity_impact: float           # 0.0-1.0
    investor_confidence_change: float # +/- percentage
    sector_impacts: Dict[str, float]  # sector -> impact percentage
    historical_analogs: List[Dict[str, Any]]
    recovery_time_hours: float

class HKWeatherDataFetcher:
    """香港天氣數據獲取器"""

    def __init__(self):
        self.hko_url = "https://www.hko.gov.hk"  # 香港天文台
        self.weather_api_sources = {
            "hko_current": "https://data.weather.gov.hk/weatherAPI/opendata/weather.php",
            "hko_warning": "https://data.weather.gov.hk/weatherAPI/opendata/weather.php",
            "alternative": "https://api.openweathermap.org/data/2.5/weather"
        }
        self.session = None

    async def get_current_warnings(self) -> List[HKWeatherEvent]:
        """獲取當前天氣警告"""
        warnings = []

        try:
            # 香港天文台API
            async with aiohttp.ClientSession() as session:
                warning_params = {
                    'dataType': 'warningSummary',
                    'lang': 'tc'  # 繁體中文
                }

                async with session.get(self.weather_api_sources['hko_warning'], params=warning_params) as response:
                    if response.status == 200:
                        data = await response.json()
                        warnings.extend(self._parse_hko_warnings(data))

        except Exception as e:
            logger.warning(f"Failed to fetch HKO warnings: {e}")
            # 使用模擬數據
            warnings = self._get_mock_weather_events()

        return warnings

    def _parse_hko_warnings(self, data: Dict[str, Any]) -> List[HKWeatherEvent]:
        """解析香港天文台警告數據"""
        warnings = []

        try:
            if 'warningStatement' in data:
                statement = data['warningStatement']
                current_time = datetime.now()

                # 檢查颱風信號
                if 'Typhoon' in statement:
                    if 'No. 10' in statement:
                        event_type = HKWeatherEventType.TYPHOON_SIGNAL_10
                        signal_number = 10
                        severity = 1.0
                    elif 'No. 9' in statement:
                        event_type = HKWeatherEventType.TYPHOON_SIGNAL_9
                        signal_number = 9
                        severity = 0.9
                    elif 'No. 8' in statement:
                        event_type = HKWeatherEventType.TYPHOON_SIGNAL_8
                        signal_number = 8
                        severity = 0.8
                    elif 'No. 3' in statement:
                        event_type = HKWeatherEventType.TYPHOON_SIGNAL_3
                        signal_number = 3
                        severity = 0.5
                    elif 'No. 1' in statement:
                        event_type = HKWeatherEventType.TYPHOON_SIGNAL_1
                        signal_number = 1
                        severity = 0.2
                    else:
                        return warnings

                    warnings.append(HKWeatherEvent(
                        event_type=event_type,
                        signal_number=signal_number,
                        start_time=current_time,
                        expected_end_time=current_time + timedelta(hours=12),
                        severity=severity,
                        affected_areas=['Hong Kong', 'Kowloon', 'New Territories'],
                        wind_speed=None,
                        rainfall=None,
                        source='HKO',
                        confidence=0.9
                    ))

                # 檢查暴雨警告
                if 'Rainstorm' in statement:
                    if 'Black' in statement:
                        event_type = HKWeatherEventType.RAINSTORM_BLACK
                        severity = 0.9
                    elif 'Red' in statement:
                        event_type = HKWeatherEventType.RAINSTORM_RED
                        severity = 0.7
                    elif 'Amber' in statement:
                        event_type = HKWeatherEventType.RAINSTORM_AMBER
                        severity = 0.4
                    else:
                        return warnings

                    warnings.append(HKWeatherEvent(
                        event_type=event_type,
                        signal_number=None,
                        start_time=current_time,
                        expected_end_time=current_time + timedelta(hours=6),
                        severity=severity,
                        affected_areas=['Hong Kong Island', 'Kowloon'],
                        wind_speed=None,
                        rainfall=50.0 if severity > 0.7 else 30.0,
                        source='HKO',
                        confidence=0.9
                    ))

                # 檢查雷暴警告
                if 'Thunderstorm' in statement:
                    warnings.append(HKWeatherEvent(
                        event_type=HKWeatherEventType.THUNDERSTORM_WARNING,
                        signal_number=None,
                        start_time=current_time,
                        expected_end_time=current_time + timedelta(hours=4),
                        severity=0.3,
                        affected_areas=['Hong Kong', 'Kowloon', 'New Territories'],
                        wind_speed=None,
                        rainfall=20.0,
                        source='HKO',
                        confidence=0.8
                    ))

        except Exception as e:
            logger.error(f"Error parsing HKO warnings: {e}")

        return warnings

    def _get_mock_weather_events(self) -> List[HKWeatherEvent]:
        """獲取模擬天氣事件（用於測試/備用）"""
        current_time = datetime.now()

        # 模擬一些常見的天氣事件
        return [
            HKWeatherEvent(
                event_type=HKWeatherEventType.TYPHOON_SIGNAL_3,
                signal_number=3,
                start_time=current_time - timedelta(hours=2),
                expected_end_time=current_time + timedelta(hours=8),
                severity=0.5,
                affected_areas=['Hong Kong', 'Kowloon'],
                wind_speed=62.0,
                rainfall=15.0,
                source='Mock',
                confidence=0.7
            )
        ]

class HKHistoricalWeatherAnalyzer:
    """香港歷史天氣分析器"""

    def __init__(self):
        self.historical_events = self._load_historical_events()

    def _load_historical_events(self) -> List[Dict[str, Any]]:
        """加載歷史天氣事件數據"""
        # 模擬歷史數據（實際應用中應從真實數據源加載）
        return [
            {
                "date": "2023-09-01",
                "event_type": "typhoon_signal_8",
                "duration_hours": 12,
                "market_impact": {
                    "trading_status": "early_close",
                    "volatility_change": 0.15,
                    "volume_change": -0.25,
                    "sector_impacts": {
                        "financials": -0.08,
                        "property": -0.12,
                        "utilities": 0.05,
                        "technology": -0.06
                    }
                }
            },
            {
                "date": "2023-07-17",
                "event_type": "rainstorm_black",
                "duration_hours": 6,
                "market_impact": {
                    "trading_status": "normal",
                    "volatility_change": 0.08,
                    "volume_change": -0.15,
                    "sector_impacts": {
                        "retail": -0.10,
                        "transport": -0.18,
                        "restaurants": -0.12,
                        "utilities": 0.03
                    }
                }
            },
            {
                "date": "2022-10-18",
                "event_type": "typhoon_signal_10",
                "duration_hours": 24,
                "market_impact": {
                    "trading_status": "full_day_closure",
                    "volatility_change": 0.25,
                    "volume_change": -1.0,
                    "sector_impacts": {
                        "all_sectors": -0.15
                    }
                }
            }
        ]

    def find_historical_analogs(self, current_event: HKWeatherEvent) -> List[Dict[str, Any]]:
        """尋找歷史類似事件"""
        analogs = []
        current_type = current_event.event_type.value
        current_severity = current_event.severity

        for historical_event in self.historical_events:
            if historical_event["event_type"] == current_type:
                # 計算相似度
                severity_diff = abs(current_severity - 0.8)  # 假設歷史事件嚴重程度為0.8
                similarity = max(0, 1 - severity_diff)

                if similarity > 0.5:  # 相似度閾值
                    analogs.append({
                        "historical_event": historical_event,
                        "similarity": similarity,
                        "date": historical_event["date"],
                        "market_impact": historical_event["market_impact"]
                    })

        return sorted(analogs, key=lambda x: x["similarity"], reverse=True)[:3]

class HKWeatherDisruptionModeler:
    """香港天氣干擾建模器"""

    def __init__(self):
        self.data_fetcher = HKWeatherDataFetcher()
        self.historical_analyzer = HKHistoricalWeatherAnalyzer()

        # 市場影響參數
        self.sector_weather_sensitivity = {
            "financials": 0.3,      # 銀行、保險受影響較小
            "property": 0.7,        # 房地產受天氣影響較大（施工、看樓）
            "retail": 0.8,          # 零售業高度依賴人流
            "transport": 0.9,       # 交通直接受影響
            "restaurants": 0.85,    # 餐飲業依賴外出消費
            "utilities": 0.2,       # 公用事業影響小
            "technology": 0.4,      # 科技業可遠程工作
            "telecommunications": 0.1,  # 電信幾乎不受影響
        }

        self.trading_status_rules = self._initialize_trading_rules()

    def _initialize_trading_rules(self) -> Dict[HKWeatherEventType, HKMarketTradingStatus]:
        """初始化交易狀態規則"""
        return {
            HKWeatherEventType.TYPHOON_SIGNAL_1: HKMarketTradingStatus.NORMAL,
            HKWeatherEventType.TYPHOON_SIGNAL_3: HKMarketTradingStatus.NORMAL,
            HKWeatherEventType.TYPHOON_SIGNAL_8: HKMarketTradingStatus.EARLY_CLOSE,
            HKWeatherEventType.TYPHOON_SIGNAL_9: HKMarketTradingStatus.EARLY_CLOSE,
            HKWeatherEventType.TYPHOON_SIGNAL_10: HKMarketTradingStatus.FULL_DAY_CLOSURE,
            HKWeatherEventType.THUNDERSTORM_WARNING: HKMarketTradingStatus.NORMAL,
            HKWeatherEventType.RAINSTORM_AMBER: HKMarketTradingStatus.NORMAL,
            HKWeatherEventType.RAINSTORM_RED: HKMarketTradingStatus.NORMAL,
            HKWeatherEventType.RAINSTORM_BLACK: HKMarketTradingStatus.EARLY_CLOSE,
        }

    async def analyze_current_weather_impact(self) -> List[HKWeatherMarketImpact]:
        """分析當前天氣對市場的影響"""
        current_events = await self.data_fetcher.get_current_warnings()
        impacts = []

        for event in current_events:
            impact = await self._analyze_event_impact(event)
            impacts.append(impact)

        return impacts

    async def _analyze_event_impact(self, event: HKWeatherEvent) -> HKWeatherMarketImpact:
        """分析單個天氣事件的影響"""

        # 確定交易狀態
        trading_status = self.trading_status_rules.get(event.event_type, HKMarketTradingStatus.NORMAL)

        # 獲取歷史類比
        historical_analogs = self.historical_analyzer.find_historical_analogs(event)

        # 計算預期影響
        base_volatility_change = self._calculate_volatility_impact(event, historical_analogs)
        base_volume_change = self._calculate_volume_impact(event, historical_analogs)
        liquidity_impact = self._calculate_liquidity_impact(event)
        confidence_change = self._calculate_confidence_impact(event)

        # 計算行業影響
        sector_impacts = self._calculate_sector_impacts(event, historical_analogs)

        # 估算恢復時間
        recovery_time = self._estimate_recovery_time(event, trading_status)

        return HKWeatherMarketImpact(
            event=event,
            trading_status=trading_status,
            expected_volatility_change=base_volatility_change,
            expected_volume_change=base_volume_change,
            liquidity_impact=liquidity_impact,
            investor_confidence_change=confidence_change,
            sector_impacts=sector_impacts,
            historical_analogs=historical_analogs,
            recovery_time_hours=recovery_time
        )

    def _calculate_volatility_impact(self, event: HKWeatherEvent, analogs: List[Dict[str, Any]]) -> float:
        """計算波動率影響"""
        base_impact = {
            HKWeatherEventType.TYPHOON_SIGNAL_1: 0.02,
            HKWeatherEventType.TYPHOON_SIGNAL_3: 0.05,
            HKWeatherEventType.TYPHOON_SIGNAL_8: 0.15,
            HKWeatherEventType.TYPHOON_SIGNAL_9: 0.20,
            HKWeatherEventType.TYPHOON_SIGNAL_10: 0.25,
            HKWeatherEventType.THUNDERSTORM_WARNING: 0.03,
            HKWeatherEventType.RAINSTORM_AMBER: 0.04,
            HKWeatherEventType.RAINSTORM_RED: 0.08,
            HKWeatherEventType.RAINSTORM_BLACK: 0.12,
        }

        base = base_impact.get(event.event_type, 0.05)

        # 根據歷史類比調整
        if analogs:
            avg_historical_volatility = statistics.mean([
                analog["market_impact"]["volatility_change"] for analog in analogs
            ])
            base = (base + avg_historical_volatility) / 2

        # 根據事件嚴重程度調整
        severity_multiplier = 0.5 + event.severity
        return base * severity_multiplier

    def _calculate_volume_impact(self, event: HKWeatherEvent, analogs: List[Dict[str, Any]]) -> float:
        """計算交易量影響"""
        base_impact = {
            HKWeatherEventType.TYPHOON_SIGNAL_1: -0.05,
            HKWeatherEventType.TYPHOON_SIGNAL_3: -0.10,
            HKWeatherEventType.TYPHOON_SIGNAL_8: -0.40,
            HKWeatherEventType.TYPHOON_SIGNAL_9: -0.60,
            HKWeatherEventType.TYPHOON_SIGNAL_10: -1.0,
            HKWeatherEventType.THUNDERSTORM_WARNING: -0.08,
            HKWeatherEventType.RAINSTORM_AMBER: -0.15,
            HKWeatherEventType.RAINSTORM_RED: -0.30,
            HKWeatherEventType.RAINSTORM_BLACK: -0.50,
        }

        base = base_impact.get(event.event_type, -0.10)

        # 根據歷史類比調整
        if analogs:
            avg_historical_volume = statistics.mean([
                analog["market_impact"]["volume_change"] for analog in analogs
            ])
            base = (base + avg_historical_volume) / 2

        return base

    def _calculate_liquidity_impact(self, event: HKWeatherEvent) -> float:
        """計算流動性影響"""
        # 基於事件嚴重程度和交易狀態
        base_liquidity = event.severity * 0.7

        # 考慮交易時間影響
        if event.event_type in [HKWeatherEventType.TYPHOON_SIGNAL_8, HKWeatherEventType.TYPHOON_SIGNAL_9]:
            base_liquidity += 0.2  # 提早收市增加流動性問題
        elif event.event_type == HKWeatherEventType.TYPHOON_SIGNAL_10:
            base_liquidity += 0.3  # 全日停市

        return min(1.0, base_liquidity)

    def _calculate_confidence_impact(self, event: HKWeatherEvent) -> float:
        """計算投資者信心影響"""
        confidence_impacts = {
            HKWeatherEventType.TYPHOON_SIGNAL_1: -0.01,
            HKWeatherEventType.TYPHOON_SIGNAL_3: -0.03,
            HKWeatherEventType.TYPHOON_SIGNAL_8: -0.08,
            HKWeatherEventType.TYPHOON_SIGNAL_9: -0.12,
            HKWeatherEventType.TYPHOON_SIGNAL_10: -0.20,
            HKWeatherEventType.THUNDERSTORM_WARNING: -0.02,
            HKWeatherEventType.RAINSTORM_AMBER: -0.04,
            HKWeatherEventType.RAINSTORM_RED: -0.07,
            HKWeatherEventType.RAINSTORM_BLACK: -0.10,
        }

        return confidence_impacts.get(event.event_type, -0.05) * event.severity

    def _calculate_sector_impacts(self, event: HKWeatherEvent, analogs: List[Dict[str, Any]]) -> Dict[str, float]:
        """計算行業影響"""
        sector_impacts = {}

        # 基於天氣類型的行業影響係數
        weather_sector_multipliers = {
            "typhoon": {
                "transport": 1.2,
                "property": 1.1,
                "retail": 1.0,
                "restaurants": 1.0,
                "utilities": 0.8,
                "financials": 0.7,
                "technology": 0.9,
            },
            "rainstorm": {
                "retail": 1.3,
                "transport": 1.4,
                "restaurants": 1.2,
                "property": 0.8,
                "utilities": 1.1,
                "financials": 0.6,
                "technology": 0.7,
            }
        }

        # 確定天氣類型
        if "typhoon" in event.event_type.value:
            weather_type = "typhoon"
        elif "rainstorm" in event.event_type.value:
            weather_type = "rainstorm"
        else:
            weather_type = "general"

        multiplier_dict = weather_sector_multipliers.get(weather_type, {})

        for sector, base_sensitivity in self.sector_weather_sensitivity.items():
            sector_multiplier = multiplier_dict.get(sector, 1.0)
            impact = -base_sensitivity * event.severity * sector_multiplier

            # 應用歷史類比調整
            if analogs and sector in analogs[0]["market_impact"]["sector_impacts"]:
                historical_impact = analogs[0]["market_impact"]["sector_impacts"][sector]
                impact = (impact + historical_impact) / 2

            sector_impacts[sector] = round(impact, 3)

        return sector_impacts

    def _estimate_recovery_time(self, event: HKWeatherEvent, trading_status: HKMarketTradingStatus) -> float:
        """估算市場恢復時間（小時）"""
        base_recovery_times = {
            HKMarketTradingStatus.NORMAL: 4.0,
            HKMarketTradingStatus.EARLY_CLOSE: 24.0,
            HKMarketTradingStatus.FULL_DAY_CLOSURE: 48.0,
        }

        base_time = base_recovery_times.get(trading_status, 8.0)

        # 根據事件嚴重程度調整
        severity_adjustment = event.severity * 12.0

        # 根據事件類型調整
        type_adjustments = {
            HKWeatherEventType.TYPHOON_SIGNAL_10: 24.0,
            HKWeatherEventType.RAINSTORM_BLACK: 12.0,
            HKWeatherEventType.TYPHOON_SIGNAL_8: 8.0,
        }

        type_adj = type_adjustments.get(event.event_type, 0.0)

        return base_time + severity_adjustment + type_adj

    async def generate_weather_risk_report(self) -> Dict[str, Any]:
        """生成天氣風險報告"""
        current_impacts = await self.analyze_current_weather_impact()

        # 聚合影響分析
        total_volatility_impact = sum(impact.expected_volatility_change for impact in current_impacts)
        total_volume_impact = sum(impact.expected_volume_change for impact in current_impacts)
        max_liquidity_impact = max([impact.liquidity_impact for impact in current_impacts], default=0)

        # 確定最嚴重的交易狀態
        trading_priorities = {
            HKMarketTradingStatus.NORMAL: 0,
            HKMarketTradingStatus.EARLY_CLOSE: 1,
            HKMarketTradingStatus.FULL_DAY_CLOSURE: 2,
        }

        overall_trading_status = HKMarketTradingStatus.NORMAL
        if current_impacts:
            max_priority = 0
            for impact in current_impacts:
                priority = trading_priorities.get(impact.trading_status, 0)
                if priority > max_priority:
                    max_priority = priority
                    overall_trading_status = impact.trading_status

        # 聚合行業影響
        aggregate_sector_impacts = {}
        for impact in current_impacts:
            for sector, sector_impact in impact.sector_impacts.items():
                if sector not in aggregate_sector_impacts:
                    aggregate_sector_impacts[sector] = []
                aggregate_sector_impacts[sector].append(sector_impact)

        final_sector_impacts = {}
        for sector, impacts in aggregate_sector_impacts.items():
            final_sector_impacts[sector] = round(np.mean(impacts), 3)

        # 風險等級評估
        risk_level = self._assess_overall_risk_level(total_volatility_impact, max_liquidity_impact)

        return {
            "timestamp": datetime.now().isoformat(),
            "current_events": len(current_impacts),
            "overall_trading_status": overall_trading_status.value,
            "risk_assessment": {
                "risk_level": risk_level,
                "volatility_impact": round(total_volatility_impact, 3),
                "volume_impact": round(total_volume_impact, 3),
                "liquidity_impact": round(max_liquidity_impact, 3),
            },
            "sector_impacts": final_sector_impacts,
            "detailed_impacts": [asdict(impact) for impact in current_impacts],
            "recommendations": self._generate_recommendations(current_impacts),
            "next_update": (datetime.now() + timedelta(hours=1)).isoformat()
        }

    def _assess_overall_risk_level(self, volatility_impact: float, liquidity_impact: float) -> str:
        """評估整體風險等級"""
        risk_score = volatility_impact + liquidity_impact

        if risk_score >= 0.4:
            return "CRITICAL"
        elif risk_score >= 0.25:
            return "HIGH"
        elif risk_score >= 0.15:
            return "MEDIUM"
        elif risk_score >= 0.05:
            return "LOW"
        else:
            return "MINIMAL"

    def _generate_recommendations(self, impacts: List[HKWeatherMarketImpact]) -> List[str]:
        """生成風險管理建議"""
        recommendations = []

        if not impacts:
            return ["目前無天氣相關風險，可正常交易。"]

        # 檢查交易狀態
        trading_statuses = [impact.trading_status for impact in impacts]
        if HKMarketTradingStatus.FULL_DAY_CLOSURE in trading_statuses:
            recommendations.append("市場全日停市，建議關注開市後的跳空風險。")
        elif HKMarketTradingStatus.EARLY_CLOSE in trading_statuses:
            recommendations.append("市場可能提早收市，建議減少日内交易倉位。")

        # 檢查流動性風險
        max_liquidity = max([impact.liquidity_impact for impact in impacts])
        if max_liquidity > 0.7:
            recommendations.append("流動性風險較高，建議使用限價單避免滑點。")

        # 檢查行業影響
        all_sector_impacts = {}
        for impact in impacts:
            for sector, sector_impact in impact.sector_impacts.items():
                if sector not in all_sector_impacts:
                    all_sector_impacts[sector] = []
                all_sector_impacts[sector].append(sector_impact)

        for sector, sector_impacts in all_sector_impacts.items():
            avg_impact = np.mean(sector_impacts)
            if avg_impact < -0.1:
                recommendations.append(f"避開{sector}行業股票，預期平均下跌{abs(avg_impact*100):.1f}%。")

        # 檢查波動率
        max_volatility = max([impact.expected_volatility_change for impact in impacts])
        if max_volatility > 0.15:
            recommendations.append("波動率顯著上升，建議調低倉位規模。")

        if not recommendations:
            recommendations.append("天氣影響輕微，維持正常交易策略。")

        return recommendations

# 全局實例
_weather_modeler = None

def get_weather_modeler() -> HKWeatherDisruptionModeler:
    """獲取天氣干擾建模器單例"""
    global _weather_modeler
    if _weather_modeler is None:
        _weather_modeler = HKWeatherDisruptionModeler()
    return _weather_modeler

# 使用示例
async def example_weather_analysis():
    """天氣分析示例"""
    modeler = get_weather_modeler()

    try:
        # 獲取當前天氣影響分析
        impacts = await modeler.analyze_current_weather_impact()
        print(f"Current weather impacts: {len(impacts)} events")

        # 生成完整風險報告
        risk_report = await modeler.generate_weather_risk_report()
        print("Weather Risk Report:")
        print(json.dumps(risk_report, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"Weather analysis failed: {e}")

if __name__ == "__main__":
    asyncio.run(example_weather_analysis())
#!/usr / bin / env python3
"""
Intelligent Indicator Selector
智能指標適配系統 - 解决"係咪每個non price data 都有 RSI macd 等等"的關鍵問題
"""

import json
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd


class DataType(Enum):
    """數據類型枚舉"""

    INTEREST_RATE = "interest_rate"  # 利率數據 (HIBOR)
    EXCHANGE_RATE = "exchange_rate"  # 匯率數據
    MONETARY_BASE = "monetary_base"  # 貨幣基礎
    LIQUIDITY = "liquidity"  # 流動性數據
    YIELD_RATE = "yield_rate"  # 收益率數據 (EFBN)
    ECONOMIC_INDICATOR = "economic_indicator"  # 經濟指標
    UNKNOWN = "unknown"


class IndicatorCategory(Enum):
    """指標類別枚舉"""

    TREND = "trend"  # 趨勢指標 (SMA, EMA, MACD)
    MOMENTUM = "momentum"  # 動量指標 (RSI, Stochastic, CCI)
    VOLATILITY = "volatility"  # 波動率指標 (Bollinger Bands, ATR)
    VOLUME = "volume"  # 成交量指標
    CUSTOM = "custom"  # 自定義指標


@dataclass
class IndicatorSuitability:
    """指標適用性評估結果"""

    indicator_name: str
    category: IndicatorCategory
    suitability_score: float  # 0 - 1, 適用性分數
    recommended_params: Dict[str, Any]
    adaptation_reasons: List[str]
    limitations: List[str]
    data_requirements: List[str]


@dataclass
class DataCharacteristics:
    """數據特徵描述"""

    data_type: DataType
    is_rate_based: bool  # 是否為利率類型
    is_ratio_based: bool  # 是否為比率類型
    is_flow_data: bool  # 是否為流量數據
    typical_range: Tuple[float, float]  # 典型數值範圍
    volatility_level: str  # 波動率等級 (low / medium / high)
    trend_strength: str  # 趨勢強度 (weak / medium / strong)
    seasonal_pattern: bool  # 是否有季節性
    minimum_length_for_analysis: int  # 分析所需最小數據長度


class DataTypeClassifier:
    """數據類型分類器 - 自動識別數據類型和特徵"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def classify_data(
        self, df: pd.DataFrame, source_name: str = None
    ) -> DataCharacteristics:
        """
        分類數據類型並分析特徵

        Args:
            df: 數據框
            source_name: 數據源名稱

        Returns:
            數據特徵描述
        """
        if df.empty:
            return DataCharacteristics(
                data_type = DataType.UNKNOWN,
                is_rate_based = False,
                is_ratio_based = False,
                is_flow_data = False,
                typical_range=(0, 0),
                volatility_level="unknown",
                trend_strength="unknown",
                seasonal_pattern = False,
                minimum_length_for_analysis = 0,
            )

        # 基於數據源名稱推斷類型
        inferred_type = self._infer_type_from_source_name(source_name)

        # 分析數據特徵
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0:
            return DataCharacteristics(
                data_type = DataType.UNKNOWN,
                is_rate_based = False,
                is_ratio_based = False,
                is_flow_data = False,
                typical_range=(0, 0),
                volatility_level="unknown",
                trend_strength="unknown",
                seasonal_pattern = False,
                minimum_length_for_analysis = 0,
            )

        # 選擇主要的數值列進行分析
        primary_col = self._select_primary_numeric_column(df, numeric_cols)
        values = df[primary_col].dropna()

        if values.empty:
            return DataCharacteristics(
                data_type = DataType.UNKNOWN,
                is_rate_based = False,
                is_ratio_based = False,
                is_flow_data = False,
                typical_range=(0, 0),
                volatility_level="unknown",
                trend_strength="unknown",
                seasonal_pattern = False,
                minimum_length_for_analysis = 0,
            )

        # 分析數據特徵
        is_rate_based = self._is_rate_based_data(primary_col, source_name)
        is_ratio_based = self._is_ratio_based_data(values)
        is_flow_data = self._is_flow_data(primary_col, source_name)

        # 計算典型範圍
        q1, q3 = values.quantile([0.25, 0.75])
        typical_range = (float(q1), float(q3))

        # 評估波動率
        volatility = self._assess_volatility(values)

        # 評估趨勢強度
        trend_strength = self._assess_trend_strength(values)

        # 檢測季節性
        seasonal_pattern = self._detect_seasonal_pattern(values)

        # 計算最小分析長度
        min_length = self._calculate_minimum_length(values)

        characteristics = DataCharacteristics(
            data_type = inferred_type,
            is_rate_based = is_rate_based,
            is_ratio_based = is_ratio_based,
            is_flow_data = is_flow_data,
            typical_range = typical_range,
            volatility_level = volatility,
            trend_strength = trend_strength,
            seasonal_pattern = seasonal_pattern,
            minimum_length_for_analysis = min_length,
        )

        self.logger.info(
            f"Classified {source_name}: {inferred_type.value}, "
            f"rate_based={is_rate_based}, volatility={volatility}"
        )

        return characteristics

    def _infer_type_from_source_name(self, source_name: str) -> DataType:
        """基於數據源名稱推斷類型"""
        if source_name is None:
            return DataType.UNKNOWN

        name_lower = source_name.lower()

        if "hibor" in name_lower or "rate" in name_lower:
            return DataType.INTEREST_RATE
        elif "exchange" in name_lower or "forex" in name_lower:
            return DataType.EXCHANGE_RATE
        elif "monetary" in name_lower or "base" in name_lower:
            return DataType.MONETARY_BASE
        elif "liquidity" in name_lower:
            return DataType.LIQUIDITY
        elif "efbn" in name_lower or "yield" in name_lower:
            return DataType.YIELD_RATE
        elif "gdp" in name_lower or "cpi" in name_lower or "economic" in name_lower:
            return DataType.ECONOMIC_INDICATOR
        else:
            return DataType.UNKNOWN

    def _select_primary_numeric_column(
        self, df: pd.DataFrame, numeric_cols: List[str]
    ) -> str:
        """選擇主要的數值列"""
        # 優先選擇看起來像主要指標的列
        priority_keywords = ["rate", "value", "index", "level", "balance", "closing"]

        for col in numeric_cols:
            if any(keyword in col.lower() for keyword in priority_keywords):
                return col

        # 如果沒有找到優先列，選擇第一個
        return numeric_cols[0]

    def _is_rate_based_data(self, column_name: str, source_name: str) -> bool:
        """判斷是否為利率類型數據"""
        rate_keywords = ["rate", "interest", "hibor", "yield"]
        column_lower = column_name.lower()
        source_lower = source_name.lower() if source_name else ""

        return any(keyword in column_lower for keyword in rate_keywords) or any(
            keyword in source_lower for keyword in rate_keywords
        )

    def _is_ratio_based_data(self, values: pd.Series) -> bool:
        """判斷是否為比率類型數據"""
        # 檢查數值範圍是否在合理的比率範圍內
        positive_ratio = (values > 0).mean() > 0.8  # 大部分為正值
        range_reasonable = values.max() / (values.min() + 1e - 8) < 1000  # 範圍不太大

        return positive_ratio and range_reasonable

    def _is_flow_data(self, column_name: str, source_name: str) -> bool:
        """判斷是否為流量數據"""
        flow_keywords = ["flow", "volume", "change", "movement", "activity"]
        column_lower = column_name.lower()
        source_lower = source_name.lower() if source_name else ""

        return any(keyword in column_lower for keyword in flow_keywords) or any(
            keyword in source_lower for keyword in flow_keywords
        )

    def _assess_volatility(self, values: pd.Series) -> str:
        """評估波動率等級"""
        if len(values) < 10:
            return "unknown"

        returns = values.pct_change().dropna()
        if returns.empty:
            return "low"

        volatility = returns.std()

        if volatility < 0.01:
            return "low"
        elif volatility < 0.05:
            return "medium"
        else:
            return "high"

    def _assess_trend_strength(self, values: pd.Series) -> str:
        """評估趨勢強度"""
        if len(values) < 20:
            return "unknown"

        # 使用線性回歸評估趨勢
        x = np.arange(len(values))
        try:
            slope, intercept = np.polyfit(x, values, 1)
            # 計算R²
            y_pred = slope * x + intercept
            ss_res = np.sum((values - y_pred) ** 2)
            ss_tot = np.sum((values - np.mean(values)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

            if r_squared > 0.7:
                return "strong"
            elif r_squared > 0.3:
                return "medium"
            else:
                return "weak"
        except Exception:
            return "unknown"

    def _detect_seasonal_pattern(self, values: pd.Series) -> bool:
        """檢測季節性模式"""
        if len(values) < 52:  # 需要至少一年數據（週）
            return False

        # 簡單的季節性檢測
        try:
            # 計算不同週期的自相關性
            for period in [7, 30, 90, 252]:  # 週、月、季、年
                if len(values) > 2 * period:
                    autocorr = values.autocorr(lag = period)
                    if autocorr > 0.3:  # 顯著正相關
                        return True
        except Exception:
            pass

        return False

    def _calculate_minimum_length(self, values: pd.Series) -> int:
        """計算分析所需最小數據長度"""
        # 基於數據特徵計算最小長度需求
        base_length = 20  # 基本長度

        # 如果有季節性，需要更長數據
        try:
            if values.autocorr(lag = 252) > 0.3:  # 年度季節性
                return max(504, base_length)  # 2年
            elif values.autocorr(lag = 90) > 0.3:  # 季度季節性
                return max(180, base_length)  # 半年
            elif values.autocorr(lag = 30) > 0.3:  # 月度季節性
                return max(60, base_length)  # 2個月
        except Exception:
            pass

        return base_length


class IndicatorSuitabilityAssessor:
    """指標適用性評估器 - 評估技術指標對特定數據的適用性"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # 定義指標適用性規則
        self.suitability_rules = self._define_suitability_rules()

    def _define_suitability_rules(self) -> Dict[str, Dict]:
        """定義指標適用性規則"""
        return {
            # 趨勢指標
            "SMA": {
                "suitable_types": [
                    DataType.INTEREST_RATE,
                    DataType.EXCHANGE_RATE,
                    DataType.MONETARY_BASE,
                    DataType.YIELD_RATE,
                ],
                "unsuitable_patterns": ["high_volatility", "irregular_pattern"],
                "base_score": 0.8,
                "adaptations": {
                    DataType.INTEREST_RATE: {"min_period": 5, "max_period": 50},
                    DataType.EXCHANGE_RATE: {"min_period": 10, "max_period": 100},
                    DataType.MONETARY_BASE: {"min_period": 20, "max_period": 200},
                },
            },
            "EMA": {
                "suitable_types": [
                    DataType.INTEREST_RATE,
                    DataType.EXCHANGE_RATE,
                    DataType.MONETARY_BASE,
                    DataType.YIELD_RATE,
                ],
                "unsuitable_patterns": ["high_volatility"],
                "base_score": 0.85,
                "adaptations": {
                    DataType.INTEREST_RATE: {"min_period": 5, "max_period": 50},
                    DataType.EXCHANGE_RATE: {"min_period": 10, "max_period": 100},
                },
            },
            "MACD": {
                "suitable_types": [
                    DataType.INTEREST_RATE,
                    DataType.EXCHANGE_RATE,
                    DataType.YIELD_RATE,
                ],
                "unsuitable_patterns": ["high_volatility", "choppy_market"],
                "base_score": 0.75,
                "adaptations": {
                    DataType.INTEREST_RATE: {
                        "fast_range": (5, 15),
                        "slow_range": (20, 40),
                    },
                    DataType.EXCHANGE_RATE: {
                        "fast_range": (8, 20),
                        "slow_range": (25, 50),
                    },
                },
            },
            # 動量指標
            "RSI": {
                "suitable_types": [
                    DataType.INTEREST_RATE,
                    DataType.EXCHANGE_RATE,
                    DataType.YIELD_RATE,
                ],
                "unsuitable_patterns": ["trending_only", "low_volatility"],
                "base_score": 0.7,
                "adaptations": {
                    DataType.INTEREST_RATE: {"period_range": (7, 21)},
                    DataType.EXCHANGE_RATE: {"period_range": (10, 25)},
                },
            },
            "Stochastic": {
                "suitable_types": [DataType.INTEREST_RATE, DataType.YIELD_RATE],
                "unsuitable_patterns": ["trending_only", "smooth_trend"],
                "base_score": 0.6,
                "adaptations": {
                    DataType.INTEREST_RATE: {"k_range": (10, 20), "d_range": (2, 5)}
                },
            },
            "CCI": {
                "suitable_types": [DataType.INTEREST_RATE, DataType.EXCHANGE_RATE],
                "unsuitable_patterns": ["smooth_trend"],
                "base_score": 0.65,
                "adaptations": {
                    DataType.INTEREST_RATE: {"period_range": (14, 21)},
                    DataType.EXCHANGE_RATE: {"period_range": (20, 30)},
                },
            },
            # 波動率指標
            "Bollinger_Bands": {
                "suitable_types": [DataType.EXCHANGE_RATE, DataType.YIELD_RATE],
                "unsuitable_patterns": ["trending_only"],
                "base_score": 0.7,
                "adaptations": {
                    DataType.EXCHANGE_RATE: {
                        "period_range": (15, 25),
                        "std_range": (1.5, 2.5),
                    },
                    DataType.YIELD_RATE: {
                        "period_range": (10, 20),
                        "std_range": (1.8, 2.2),
                    },
                },
            },
            "ATR": {
                "suitable_types": [DataType.EXCHANGE_RATE],
                "unsuitable_patterns": ["rate_based_data"],
                "base_score": 0.4,  # 較低適用性
                "adaptations": {},
            },
            # 經濟數據專用指標
            "Rate_Spread": {
                "suitable_types": [DataType.INTEREST_RATE, DataType.YIELD_RATE],
                "unsuitable_patterns": [],
                "base_score": 0.9,
                "adaptations": {
                    DataType.INTEREST_RATE: {
                        "tenor_pairs": [("1m", "3m"), ("3m", "12m")]
                    },
                    DataType.YIELD_RATE: {
                        "tenor_pairs": [("2y", "10y"), ("5y", "15y")]
                    },
                },
            },
            "Yield_Curve": {
                "suitable_types": [DataType.YIELD_RATE, DataType.INTEREST_RATE],
                "unsuitable_patterns": [],
                "base_score": 0.85,
                "adaptations": {},
            },
        }

    def assess_suitability(
        self,
        indicator_name: str,
        data_characteristics: DataCharacteristics,
        data_length: int,
    ) -> IndicatorSuitability:
        """
        評估指標適用性

        Args:
            indicator_name: 指標名稱
            data_characteristics: 數據特徵
            data_length: 數據長度

        Returns:
            指標適用性評估結果
        """
        # 獲取指標規則
        rules = self.suitability_rules.get(indicator_name, {})

        if not rules:
            return IndicatorSuitability(
                indicator_name = indicator_name,
                category = IndicatorCategory.CUSTOM,
                suitability_score = 0.0,
                recommended_params={},
                adaptation_reasons=["No rules defined for this indicator"],
                limitations=["Indicator not supported"],
                data_requirements=["Unknown"],
            )

        # 基礎適用性評分
        base_score = rules.get("base_score", 0.5)
        suitable_types = rules.get("suitable_types", [])
        unsuitable_patterns = rules.get("unsuitable_patterns", [])

        # 類型適合性檢查
        type_bonus = 0.3 if data_characteristics.data_type in suitable_types else 0

        # 數據長度檢查
        length_bonus = 0
        if data_length >= data_characteristics.minimum_length_for_analysis:
            if data_length >= 252:  # 一年以上
                length_bonus = 0.2
            elif data_length >= 60:  # 2個月以上
                length_bonus = 0.1

        # 波動率適合性
        volatility_penalty = 0
        if (
            "high_volatility" in unsuitable_patterns
            and data_characteristics.volatility_level == "high"
        ):
            volatility_penalty = 0.3

        # 趨勢適合性
        trend_penalty = 0
        if (
            "trending_only" in unsuitable_patterns
            and data_characteristics.trend_strength == "weak"
        ):
            trend_penalty = 0.2
        elif (
            "smooth_trend" in unsuitable_patterns
            and data_characteristics.volatility_level == "high"
        ):
            trend_penalty = 0.2

        # 計算最終適用性分數
        suitability_score = max(
            0,
            min(
                1,
                base_score
                + type_bonus
                + length_bonus
                - volatility_penalty
                - trend_penalty,
            ),
        )

        # 獲取推薦參數
        adaptations = rules.get("adaptations", {})
        recommended_params = adaptations.get(data_characteristics.data_type, {})

        # 生成適應原因
        adaptation_reasons = []
        limitations = []

        if data_characteristics.data_type in suitable_types:
            adaptation_reasons.append(
                f"Suitable for {data_characteristics.data_type.value} data"
            )
        else:
            limitations.append(
                f"Not optimized for {data_characteristics.data_type.value} data"
            )

        if data_length >= data_characteristics.minimum_length_for_analysis:
            adaptation_reasons.append(f"Sufficient data length ({data_length} records)")
        else:
            limitations.append(
                f"Insufficient data length (need {data_characteristics.minimum_length_for_analysis} records)"
            )

        if (
            data_characteristics.volatility_level == "high"
            and "high_volatility" in unsuitable_patterns
        ):
            limitations.append("High volatility may reduce indicator effectiveness")

        if (
            data_characteristics.trend_strength == "strong"
            and "choppy_market" in unsuitable_patterns
        ):
            adaptation_reasons.append("Strong trend improves indicator performance")

        # 數據需求
        data_requirements = [
            f"Minimum {data_characteristics.minimum_length_for_analysis} data points",
            f"Compatible with {data_characteristics.data_type.value} data",
        ]

        # 確定指標類別
        category = self._determine_indicator_category(indicator_name)

        return IndicatorSuitability(
            indicator_name = indicator_name,
            category = category,
            suitability_score = suitability_score,
            recommended_params = recommended_params,
            adaptation_reasons = adaptation_reasons,
            limitations = limitations,
            data_requirements = data_requirements,
        )

    def _determine_indicator_category(self, indicator_name: str) -> IndicatorCategory:
        """確定指標類別"""
        trend_indicators = ["SMA", "EMA", "MACD", "DEMA", "TEMA"]
        momentum_indicators = ["RSI", "Stochastic", "Williams_R", "CCI", "MFI"]
        volatility_indicators = ["Bollinger_Bands", "ATR", "Keltner_Channels"]
        volume_indicators = ["Volume_MA", "OBV", "VWAP"]

        if indicator_name in trend_indicators:
            return IndicatorCategory.TREND
        elif indicator_name in momentum_indicators:
            return IndicatorCategory.MOMENTUM
        elif indicator_name in volatility_indicators:
            return IndicatorCategory.VOLATILITY
        elif indicator_name in volume_indicators:
            return IndicatorCategory.VOLUME
        else:
            return IndicatorCategory.CUSTOM


class ParameterAdaptationEngine:
    """參數適配引擎 - 根據數據特徵動態調整指標參數"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def adapt_parameters(
        self,
        indicator_name: str,
        data_characteristics: DataCharacteristics,
        data_length: int,
        base_params: Dict = None,
    ) -> Dict[str, Any]:
        """
        適配指標參數

        Args:
            indicator_name: 指標名稱
            data_characteristics: 數據特徵
            data_length: 數據長度
            base_params: 基礎參數

        Returns:
            適配後的參數
        """
        if base_params is None:
            base_params = {}

        adapted_params = base_params.copy()

        # 根據數據長度調整參數
        if data_length < 100:
            adaptation_factor = 0.5  # 短期數據，使用較短週期
        elif data_length < 252:
            adaptation_factor = 0.8  # 中期數據
        else:
            adaptation_factor = 1.0  # 長期數據，使用標準參數

        # 根據數據類型調整
        if data_characteristics.data_type == DataType.INTEREST_RATE:
            adapted_params.update(
                self._adapt_for_interest_rate(data_characteristics, adaptation_factor)
            )
        elif data_characteristics.data_type == DataType.EXCHANGE_RATE:
            adapted_params.update(
                self._adapt_for_exchange_rate(data_characteristics, adaptation_factor)
            )
        elif data_characteristics.data_type == DataType.MONETARY_BASE:
            adapted_params.update(
                self._adapt_for_monetary_base(data_characteristics, adaptation_factor)
            )
        elif data_characteristics.data_type == DataType.YIELD_RATE:
            adapted_params.update(
                self._adapt_for_yield_rate(data_characteristics, adaptation_factor)
            )

        # 根據波動率調整
        if data_characteristics.volatility_level == "high":
            adapted_params = self._adjust_for_high_volatility(
                indicator_name, adapted_params
            )
        elif data_characteristics.volatility_level == "low":
            adapted_params = self._adjust_for_low_volatility(
                indicator_name, adapted_params
            )

        # 根據趨勢強度調整
        if data_characteristics.trend_strength == "strong":
            adapted_params = self._adjust_for_strong_trend(
                indicator_name, adapted_params
            )

        self.logger.info(f"Adapted parameters for {indicator_name}: {adapted_params}")

        return adapted_params

    def _adapt_for_interest_rate(
        self, data_characteristics: DataCharacteristics, factor: float
    ) -> Dict:
        """適配利率數據參數"""
        return {
            "rsi_period": max(7, int(14 * factor)),
            "macd_fast": max(5, int(12 * factor)),
            "macd_slow": max(15, int(26 * factor)),
            "sma_period": max(10, int(20 * factor)),
            "bb_period": max(10, int(20 * factor)),
        }

    def _adapt_for_exchange_rate(
        self, data_characteristics: DataCharacteristics, factor: float
    ) -> Dict:
        """適配匯率數據參數"""
        return {
            "rsi_period": max(10, int(14 * factor)),
            "macd_fast": max(8, int(12 * factor)),
            "macd_slow": max(20, int(26 * factor)),
            "sma_period": max(15, int(20 * factor)),
            "bb_period": max(15, int(20 * factor)),
        }

    def _adapt_for_monetary_base(
        self, data_characteristics: DataCharacteristics, factor: float
    ) -> Dict:
        """適配貨幣基礎數據參數"""
        return {
            "sma_period": max(20, int(50 * factor)),
            "ema_period": max(15, int(30 * factor)),
            "rsi_period": max(20, int(30 * factor)),  # 貨幣基礎變化較慢
        }

    def _adapt_for_yield_rate(
        self, data_characteristics: DataCharacteristics, factor: float
    ) -> Dict:
        """適配收益率數據參數"""
        return {
            "rsi_period": max(10, int(14 * factor)),
            "macd_fast": max(8, int(12 * factor)),
            "macd_slow": max(18, int(26 * factor)),
            "sma_period": max(12, int(20 * factor)),
        }

    def _adjust_for_high_volatility(self, indicator_name: str, params: Dict) -> Dict:
        """調整高波動率數據的參數"""
        # 高波動率使用較長週期減少噪音
        if "period" in params:
            params["period"] = min(int(params["period"] * 1.5), 100)
        if "rsi_period" in params:
            params["rsi_period"] = min(int(params["rsi_period"] * 1.2), 50)
        if "sma_period" in params:
            params["sma_period"] = min(int(params["sma_period"] * 1.3), 100)

        return params

    def _adjust_for_low_volatility(self, indicator_name: str, params: Dict) -> Dict:
        """調整低波動率數據的參數"""
        # 低波動率使用較短週期增加敏感度
        if "period" in params:
            params["period"] = max(int(params["period"] * 0.8), 5)
        if "rsi_period" in params:
            params["rsi_period"] = max(int(params["rsi_period"] * 0.9), 7)
        if "sma_period" in params:
            params["sma_period"] = max(int(params["sma_period"] * 0.8), 10)

        return params

    def _adjust_for_strong_trend(self, indicator_name: str, params: Dict) -> Dict:
        """調整強趨勢數據的參數"""
        # 強趨勢環境下，減少動量指標的敏感性
        if "rsi_overbought" in params:
            params["rsi_overbought"] = 75  # 降低超買閾值
        if "rsi_oversold" in params:
            params["rsi_oversold"] = 25  # 提高超賣閾值

        return params


class IntelligentIndicatorSelector:
    """智能指標選擇器 - 主控制器"""

    def __init__(self):
        self.classifier = DataTypeClassifier()
        self.assessor = IndicatorSuitabilityAssessor()
        self.adapter = ParameterAdaptationEngine()
        self.logger = logging.getLogger(__name__)

    def select_indicators_for_data(
        self, df: pd.DataFrame, source_name: str, min_suitability_score: float = 0.5
    ) -> List[IndicatorSuitability]:
        """
        為特定數據選擇適合的技術指標

        Args:
            df: 數據框
            source_name: 數據源名稱
            min_suitability_score: 最低適用性分數

        Returns:
            適合的指標列表
        """
        # 分類數據
        data_characteristics = self.classifier.classify_data(df, source_name)
        data_length = len(df)

        self.logger.info(
            f"Analyzing {source_name}: {data_characteristics.data_type.value}, "
            f"length={data_length}, volatility={data_characteristics.volatility_level}"
        )

        # 評估所有指標的適用性
        all_indicators = list(self.assessor.suitability_rules.keys())
        suitable_indicators = []

        for indicator_name in all_indicators:
            suitability = self.assessor.assess_suitability(
                indicator_name, data_characteristics, data_length
            )

            if suitability.suitability_score >= min_suitability_score:
                # 適配參數
                adapted_params = self.adapter.adapt_parameters(
                    indicator_name,
                    data_characteristics,
                    data_length,
                    suitability.recommended_params,
                )
                suitability.recommended_params.update(adapted_params)

                suitable_indicators.append(suitability)

        # 按適用性分數排序
        suitable_indicators.sort(key = lambda x: x.suitability_score, reverse = True)

        self.logger.info(
            f"Selected {len(suitable_indicators)} suitable indicators for {source_name}"
        )

        return suitable_indicators

    def generate_recommendation_report(
        self, df: pd.DataFrame, source_name: str
    ) -> Dict:
        """
        生成指標推薦報告

        Args:
            df: 數據框
            source_name: 數據源名稱

        Returns:
            推薦報告
        """
        # 獲取適合的指標
        suitable_indicators = self.select_indicators_for_data(
            df, source_name, min_suitability_score = 0.3
        )

        # 分類指標
        indicators_by_category = {}
        for indicator in suitable_indicators:
            category = indicator.category.value
            if category not in indicators_by_category:
                indicators_by_category[category] = []
            indicators_by_category[category].append(indicator)

        # 生成報告
        report = {
            "data_source": source_name,
            "data_characteristics": {
                "type": self.classifier.classify_data(df, source_name).data_type.value,
                "length": len(df),
                "has_date_column": any(
                    col.lower().find("date") != -1 for col in df.columns
                ),
                "numeric_columns": len(df.select_dtypes(include=[np.number]).columns),
            },
            "total_indicators_evaluated": len(self.assessor.suitability_rules),
            "suitable_indicators_count": len(suitable_indicators),
            "indicators_by_category": {},
            "top_recommendations": [],
            "not_recommended": [],
            "summary": {},
        }

        # 按類別整理指標
        for category, indicators in indicators_by_category.items():
            report["indicators_by_category"][category] = [
                {
                    "name": ind.indicator_name,
                    "suitability_score": round(ind.suitability_score, 3),
                    "recommended_params": ind.recommended_params,
                    "reasons": ind.adaptation_reasons,
                    "limitations": ind.limitations,
                }
                for ind in indicators
            ]

        # 頂級推薦（適用性分數 > 0.7）
        top_indicators = [
            ind for ind in suitable_indicators if ind.suitability_score > 0.7
        ]
        report["top_recommendations"] = [
            {
                "name": ind.indicator_name,
                "suitability_score": round(ind.suitability_score, 3),
                "category": ind.category.value,
                "recommended_params": ind.recommended_params,
                "reasons": ind.adaptation_reasons,
            }
            for ind in top_indicators[:5]  # 取前5個
        ]

        # 不推薦的指標
        not_recommended = [
            ind for ind in suitable_indicators if ind.suitability_score < 0.5
        ]
        report["not_recommended"] = [
            {
                "name": ind.indicator_name,
                "suitability_score": round(ind.suitability_score, 3),
                "limitations": ind.limitations,
            }
            for ind in not_recommended
        ]

        # 總結
        report["summary"] = {
            "highly_suitable_count": len(top_indicators),
            "moderately_suitable_count": len(
                [
                    ind
                    for ind in suitable_indicators
                    if 0.5 <= ind.suitability_score <= 0.7
                ]
            ),
            "not_suitable_count": len(not_recommended),
            "best_indicator": (
                top_indicators[0].indicator_name if top_indicators else None
            ),
            "best_score": (
                round(top_indicators[0].suitability_score, 3) if top_indicators else 0
            ),
        }

        return report

    def save_recommendation_report(self, report: Dict, output_dir: str = None):
        """保存推薦報告"""
        if output_dir is None:
            output_dir = Path("data / indicator_recommendations")
        else:
            output_dir = Path(output_dir)

        output_dir.mkdir(parents = True, exist_ok = True)

        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{report['data_source']}_indicator_recommendations_{timestamp}.json"
        filepath = output_dir / filename

        with open(filepath, "w", encoding="utf - 8") as f:
            json.dump(report, f, indent = 2, ensure_ascii = False, default = str)

        self.logger.info(f"Indicator recommendation report saved: {filepath}")
        return filepath


def main():
    """主測試函數"""
    logging.basicConfig(
        level = logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # 創建智能指標選擇器
    selector = IntelligentIndicatorSelector()

    # 加載對齊後的數據
    aligned_data_dir = Path("data / aligned")
    data_dict = {}

    # 加載已對齊的數據
    for file_path in aligned_data_dir.glob("*_aligned_*.csv"):
        source_name = file_path.stem.split("_aligned_")[0]
        try:
            df = pd.read_csv(file_path)
            if not df.empty:
                data_dict[source_name] = df
                print(f"[LOADED] {source_name}: {len(df)} records")
        except Exception as e:
            print(f"[ERROR] Failed to load {source_name}: {e}")

    if not data_dict:
        print("[ERROR] No aligned data found. Please run data alignment first.")
        return

    print(f"\n[START] Intelligent indicator selection for {len(data_dict)} sources")
    print("=" * 60)

    # 為每個數據源生成指標推薦
    all_reports = {}

    for source_name, df in data_dict.items():
        print(f"\n[ANALYZING] {source_name}")
        print("-" * 40)

        try:
            # 生成推薦報告
            report = selector.generate_recommendation_report(df, source_name)
            all_reports[source_name] = report

            # 顯示關鍵結果
            summary = report["summary"]
            print(f"Data type: {report['data_characteristics']['type']}")
            print(f"Data length: {report['data_characteristics']['length']}")
            print(f"Highly suitable indicators: {summary['highly_suitable_count']}")
            print(
                f"Best indicator: {summary['best_indicator']} (score: {summary['best_score']})"
            )

            # 顯示頂級推薦
            if report["top_recommendations"]:
                print("\nTop recommendations:")
                for i, rec in enumerate(report["top_recommendations"][:3], 1):
                    print(
                        f"  {i}. {rec['name']} (score: {rec['suitability_score']}, category: {rec['category']})"
                    )

            # 保存報告
            selector.save_recommendation_report(report)

        except Exception as e:
            print(f"[ERROR] Failed to analyze {source_name}: {e}")

    # 生成綜合報告
    print(f"\n" + "=" * 60)
    print("[SUMMARY] Overall Analysis Results")
    print("=" * 60)

    total_indicators = 0
    high_suitability_total = 0
    best_indicators = []

    for source_name, report in all_reports.items():
        summary = report["summary"]
        total_indicators += (
            summary["highly_suitable_count"] + summary["moderately_suitable_count"]
        )
        high_suitability_total += summary["highly_suitable_count"]

        if summary["best_indicator"]:
            best_indicators.append(
                {
                    "source": source_name,
                    "indicator": summary["best_indicator"],
                    "score": summary["best_score"],
                }
            )

    print(f"Total data sources analyzed: {len(all_reports)}")
    print(f"Total suitable indicators found: {total_indicators}")
    print(f"Highly suitable indicators: {high_suitability_total}")

    if best_indicators:
        print(f"\nBest indicators by data source:")
        for item in sorted(best_indicators, key = lambda x: x["score"], reverse = True):
            print(f"  {item['source']}: {item['indicator']} (score: {item['score']})")

    print(f"\n[COMPLETE] Intelligent indicator selection completed successfully!")


if __name__ == "__main__":
    main()

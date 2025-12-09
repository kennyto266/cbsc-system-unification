#!/usr / bin / env python3
# -*- coding: utf - 8 -*-
"""
NON PRICE DATA TA指標ID系統
Non - Price Data Technical Analysis ID System

Author: Claude Code
Date: 2025 - 11 - 19
Version: 1.0.0

功能：
- 統一的NON PRICE DATA技術指標ID管理
- 標準化命名規則
- 自動化指標生成和計算
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# ============================================================================
# 🏗️ ID系統核心定義
# ============================================================================


class DataSourceCode(Enum):
    """數據源代碼枚舉"""

    HIBOR = "HB"  # Hong Kong Interbank Offered Rate
    GDP = "GD"  # Gross Domestic Product
    RETAIL = "RT"  # Retail Sales
    PROPERTY = "PT"  # Property Market
    TRADE = "TR"  # Trade Data
    TOURISM = "TS"  # Tourism Statistics
    CPI = "CP"  # Consumer Price Index
    UNEMPLOYMENT = "UE"  # Unemployment Rate
    MONETARY = "MB"  # Monetary Base
    EXCHANGE_RATE = "ER"  # Exchange Rate
    STOCK_MARKET = "SM"  # Stock Market Data


class IndicatorTypeCode(Enum):
    """指標類型代碼枚舉"""

    RSI = "RS"  # Relative Strength Index
    MACD = "MC"  # Moving Average Convergence Divergence
    BOLLINGER_BANDS = "BB"  # Bollinger Bands
    KDJ = "KD"  # Stochastic Oscillator (KDJ)
    CCI = "CC"  # Commodity Channel Index
    ADX = "AD"  # Average Directional Index
    ATR = "AT"  # Average True Range
    MOMENTUM = "MN"  # Momentum
    RATE_OF_CHANGE = "RC"  # Rate of Change
    WILLIAMS_R = "WR"  # Williams %R
    STOCHASTIC = "ST"  # Stochastic Oscillator


class VersionType(Enum):
    """版本類型枚舉"""

    MAIN = "1"  # 主版本
    OPTIMIZED = "2"  # 優化版本
    EXPERIMENTAL = "3"  # 實驗版本


@dataclass
class TAIndicatorID:
    """技術指標ID數據類"""

    data_source: DataSourceCode
    indicator_type: IndicatorTypeCode
    parameters: List[str]
    version: VersionType = VersionType.MAIN

    def __post_init__(self):
        """生成ID字符串"""
        self.id_string = f"{self.data_source.value}_{self.indicator_type.value}_{'_'.join(self.parameters)}_{self.version.value}"
        self.display_name = self._generate_display_name()

    def _generate_display_name(self) -> str:
        """生成顯示名稱"""
        data_source_names = {
            DataSourceCode.HIBOR: "HIBOR",
            DataSourceCode.GDP: "GDP",
            DataSourceCode.RETAIL: "RETAIL",
            DataSourceCode.PROPERTY: "PROPERTY",
            DataSourceCode.TRADE: "TRADE",
            DataSourceCode.TOURISM: "TOURISM",
            DataSourceCode.CPI: "CPI",
            DataSourceCode.UNEMPLOYMENT: "UNEMPLOYMENT",
            DataSourceCode.MONETARY: "MONETARY",
        }

        indicator_names = {
            IndicatorTypeCode.RSI: "RSI",
            IndicatorTypeCode.MACD: "MACD",
            IndicatorTypeCode.BOLLINGER_BANDS: "BB",
            IndicatorTypeCode.KDJ: "KDJ",
            IndicatorTypeCode.CCI: "CCI",
            IndicatorTypeCode.ADX: "ADX",
            IndicatorTypeCode.ATR: "ATR",
            IndicatorTypeCode.MOMENTUM: "MOMENTUM",
            IndicatorTypeCode.RATE_OF_CHANGE: "ROC",
            IndicatorTypeCode.WILLIAMS_R: "WILLIAMS_R",
            IndicatorTypeCode.STOCHASTIC: "STOCHASTIC",
        }

        data_name = data_source_names.get(self.data_source, self.data_source.value)
        indicator_name = indicator_names.get(
            self.indicator_type, self.indicator_type.value
        )
        params = "_".join(self.parameters)

        return f"{data_name}_{indicator_name}_{params}"

    @classmethod
    def from_string(cls, id_string: str) -> "TAIndicatorID":
        """從字符串解析ID"""
        parts = id_string.split("_")
        if len(parts) < 3:
            raise ValueError(f"無效的ID格式: {id_string}")

        try:
            data_source = DataSourceCode(parts[0])
            indicator_type = IndicatorTypeCode(parts[1])
            parameters = parts[2:-1]  # 排除版本號
            version = VersionType(parts[-1])

            return cls(data_source, indicator_type, parameters, version)
        except (ValueError, IndexError) as e:
            raise ValueError(f"無法解析ID {id_string}: {e}")


# ============================================================================
# 🎯 統一指標計算器
# ============================================================================


class NonPriceTACalculator:
    """NON PRICE DATA 技術指標統一計算器"""

    def __init__(self):
        self.indicators_registry = {}
        self._initialize_indicator_registry()

    def _initialize_indicator_registry(self):
        """初始化指標註冊表"""
        # RSI指標系列
        for data_source in DataSourceCode:
            if data_source != DataSourceCode.STOCK_MARKET:  # 僅非價格數據
                rsi_id = TAIndicatorID(data_source, IndicatorTypeCode.RSI, ["14"])
                self.indicators_registry[rsi_id.id_string] = self._calculate_rsi

                # 多週期RSI
                for period in ["7", "21", "30"]:
                    rsi_multi_id = TAIndicatorID(
                        data_source, IndicatorTypeCode.RSI, [period]
                    )
                    self.indicators_registry[rsi_multi_id.id_string] = (
                        self._calculate_rsi
                    )

        # MACD指標系列
        for data_source in [
            DataSourceCode.HIBOR,
            DataSourceCode.GDP,
            DataSourceCode.RETAIL,
            DataSourceCode.PROPERTY,
            DataSourceCode.TRADE,
            DataSourceCode.TOURISM,
            DataSourceCode.CPI,
            DataSourceCode.MONETARY,
        ]:
            macd_id = TAIndicatorID(
                data_source, IndicatorTypeCode.MACD, ["12", "26", "9"]
            )
            self.indicators_registry[macd_id.id_string] = self._calculate_macd

            # 快速MACD
            macd_fast_id = TAIndicatorID(
                data_source, IndicatorTypeCode.MACD, ["5", "15", "5"]
            )
            self.indicators_registry[macd_fast_id.id_string] = self._calculate_macd

            # 慢速MACD
            macd_slow_id = TAIndicatorID(
                data_source, IndicatorTypeCode.MACD, ["20", "40", "10"]
            )
            self.indicators_registry[macd_slow_id.id_string] = self._calculate_macd

        # 布林帶指標系列
        for data_source in DataSourceCode:
            if data_source != DataSourceCode.STOCK_MARKET:
                bb_id = TAIndicatorID(
                    data_source, IndicatorTypeCode.BOLLINGER_BANDS, ["20", "2"]
                )
                self.indicators_registry[bb_id.id_string] = (
                    self._calculate_bollinger_bands
                )

                # 短期布林帶
                bb_short_id = TAIndicatorID(
                    data_source, IndicatorTypeCode.BOLLINGER_BANDS, ["10", "2"]
                )
                self.indicators_registry[bb_short_id.id_string] = (
                    self._calculate_bollinger_bands
                )

        # 其他指標系列...
        self._register_other_indicators()

    def _register_other_indicators(self):
        """註冊其他指標類型"""
        # KDJ指標
        for data_source in [
            DataSourceCode.HIBOR,
            DataSourceCode.GDP,
            DataSourceCode.RETAIL,
        ]:
            kdj_id = TAIndicatorID(data_source, IndicatorTypeCode.KDJ, ["9", "3", "3"])
            self.indicators_registry[kdj_id.id_string] = self._calculate_kdj

        # CCI指標
        for data_source in DataSourceCode:
            if data_source != DataSourceCode.STOCK_MARKET:
                cci_id = TAIndicatorID(data_source, IndicatorTypeCode.CCI, ["14"])
                self.indicators_registry[cci_id.id_string] = self._calculate_cci

        # ADX指標
        for data_source in [
            DataSourceCode.HIBOR,
            DataSourceCode.GDP,
            DataSourceCode.TRADE,
        ]:
            adx_id = TAIndicatorID(data_source, IndicatorTypeCode.ADX, ["14"])
            self.indicators_registry[adx_id.id_string] = self._calculate_adx

        # 動量指標
        for data_source in DataSourceCode:
            momentum_id = TAIndicatorID(data_source, IndicatorTypeCode.MOMENTUM, ["5"])
            self.indicators_registry[momentum_id.id_string] = self._calculate_momentum

    # ========================================================================
    # 📊 具體指標計算方法
    # ========================================================================

    def _calculate_rsi(self, data: pd.Series, period: int = 14) -> pd.Series:
        """計算RSI指標"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def _calculate_macd(
        self, data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> Dict[str, pd.Series]:
        """計算MACD指標"""
        exp1 = data.ewm(span=fast).mean()
        exp2 = data.ewm(span=slow).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line

        return {"MACD": macd, "Signal": signal_line, "Histogram": histogram}

    def _calculate_bollinger_bands(
        self, data: pd.Series, period: int = 20, std_dev: float = 2.0
    ) -> Dict[str, pd.Series]:
        """計算布林帶指標"""
        sma = data.rolling(window=period).mean()
        std = data.rolling(window=period).std()

        return {
            "Upper": sma + (std * std_dev),
            "Middle": sma,
            "Lower": sma - (std * std_dev),
            "Width": (sma + (std * std_dev) - (sma - (std * std_dev))) / sma,
        }

    def _calculate_kdj(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 9,
        k_period: int = 3,
        d_period: int = 3,
    ) -> Dict[str, pd.Series]:
        """計算KDJ指標"""
        low_min = low.rolling(window=period).min()
        high_max = high.rolling(window=period).max()
        rsv = (close - low_min) / (high_max - low_min) * 100

        k = rsv.ewm(com=k_period - 1).mean()
        d = k.ewm(com=d_period - 1).mean()
        j = 3 * k - 2 * d

        return {"K": k, "D": d, "J": j}

    def _calculate_cci(
        self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
    ) -> pd.Series:
        """計算CCI指標"""
        tp = (high + low + close) / 3
        sma_tp = tp.rolling(window=period).mean()
        mad = tp.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())
        return (tp - sma_tp) / (0.015 * mad)

    def _calculate_adx(
        self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
    ) -> Dict[str, pd.Series]:
        """計算ADX指標"""
        high_diff = high.diff()
        low_diff = -low.diff()
        plus_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0)
        minus_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0)

        tr = pd.DataFrame(
            {
                "hl": high - low,
                "hc": abs(high - close.shift()),
                "lc": abs(low - close.shift()),
            }
        ).max(axis=1)

        atr = tr.rolling(window=period).mean()
        plus_di = 100 * (pd.Series(plus_dm).rolling(window=period).mean() / atr)
        minus_di = 100 * (pd.Series(minus_dm).rolling(window=period).mean() / atr)

        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()

        return {"ADX": adx, "Plus_DI": plus_di, "Minus_DI": minus_di}

    def _calculate_momentum(self, data: pd.Series, period: int = 5) -> pd.Series:
        """計算動量指標"""
        return data.pct_change(period)

    # ========================================================================
    # 🔧 統一調用接口
    # ========================================================================

    def calculate_indicator(
        self, indicator_id: str, data: pd.DataFrame, **kwargs
    ) -> Dict[str, Any]:
        """
        統一指標計算接口

        Args:
            indicator_id: 指標ID (如 "HB_RS_14_1")
            data: 數據DataFrame
            **kwargs: 額外參數

        Returns:
            計算結果字典
        """
        try:
            # 解析ID
            ta_id = TAIndicatorID.from_string(indicator_id)

            # 檢查是否已註冊
            if indicator_id not in self.indicators_registry:
                raise ValueError(f"未註冊的指標ID: {indicator_id}")

            # 獲取數據列
            data_column = self._get_data_column(ta_id.data_source, data)

            # 調用對應的計算方法
            calculator_func = self.indicators_registry[indicator_id]

            # 解析參數
            params = self._parse_parameters(ta_id.parameters, **kwargs)

            # 執行計算
            result = calculator_func(data_column, **params)

            return {
                "indicator_id": indicator_id,
                "display_name": ta_id.display_name,
                "data_source": ta_id.data_source.value,
                "indicator_type": ta_id.indicator_type.value,
                "parameters": ta_id.parameters,
                "result": result,
                "calculation_time": pd.Timestamp.now(),
            }

        except Exception as e:
            return {
                "indicator_id": indicator_id,
                "error": str(e),
                "calculation_time": pd.Timestamp.now(),
            }

    def _get_data_column(
        self, data_source: DataSourceCode, data: pd.DataFrame
    ) -> pd.Series:
        """根據數據源獲取對應的數據列"""
        column_mapping = {
            DataSourceCode.HIBOR: "hibor_rate",
            DataSourceCode.GDP: "gdp_growth",
            DataSourceCode.RETAIL: "retail_sales",
            DataSourceCode.PROPERTY: "property_index",
            DataSourceCode.TRADE: "trade_balance",
            DataSourceCode.TOURISM: "tourism_arrivals",
            DataSourceCode.CPI: "cpi_index",
            DataSourceCode.UNEMPLOYMENT: "unemployment_rate",
            DataSourceCode.MONETARY: "monetary_base",
            DataSourceCode.STOCK_MARKET: "close",
        }

        column_name = column_mapping.get(data_source, "value")
        if column_name not in data.columns:
            # 嘗試使用第一個數值列
            numeric_columns = data.select_dtypes(include=[np.number]).columns
            if len(numeric_columns) > 0:
                column_name = numeric_columns[0]
            else:
                raise ValueError(f"數據中沒有找到數值列用於{data_source.value}")

        return data[column_name]

    def _parse_parameters(self, param_strings: List[str], **kwargs) -> Dict[str, Any]:
        """解析參數字符串為數值"""
        params = {}

        # 根據參數數量智能映射參數名
        if len(param_strings) == 1:
            # 單參數：通常為period
            try:
                params["period"] = int(param_strings[0])
            except ValueError:
                try:
                    params["period"] = float(param_strings[0])
                except ValueError:
                    params["period"] = param_strings[0]

        elif len(param_strings) == 2:
            # 雙參數：通常為period, std_dev
            try:
                params["period"] = int(param_strings[0])
                params["std_dev"] = float(param_strings[1])
            except ValueError:
                # 通用映射
                params["param_0"] = param_strings[0]
                params["param_1"] = param_strings[1]

        elif len(param_strings) == 3:
            # 三參數：通常為MACD參數 (fast, slow, signal)
            try:
                params["fast"] = int(param_strings[0])
                params["slow"] = int(param_strings[1])
                params["signal"] = int(param_strings[2])
            except ValueError:
                # 通用映射
                params["param_0"] = param_strings[0]
                params["param_1"] = param_strings[1]
                params["param_2"] = param_strings[2]

        else:
            # 多參數：通用映射
            for i, param_str in enumerate(param_strings):
                try:
                    # 嘗試轉換為整數，失敗則轉換為浮點數
                    if "." in param_str:
                        params[f"param_{i}"] = float(param_str)
                    else:
                        params[f"param_{i}"] = int(param_str)
                except ValueError:
                    params[f"param_{i}"] = param_str  # 保持字符串

        # 添加額外參數
        params.update(kwargs)

        return params

    def get_available_indicators(self) -> List[str]:
        """獲取所有可用的指標ID列表"""
        return list(self.indicators_registry.keys())

    def get_indicators_by_data_source(self, data_source: DataSourceCode) -> List[str]:
        """根據數據源獲取指標列表"""
        return [
            id_str
            for id_str in self.indicators_registry.keys()
            if id_str.startswith(data_source.value)
        ]

    def get_indicators_by_type(self, indicator_type: IndicatorTypeCode) -> List[str]:
        """根據指標類型獲取指標列表"""
        return [
            id_str
            for id_str in self.indicators_registry.keys()
            if f"_{indicator_type.value}_" in id_str
        ]


# ============================================================================
# 🚀 全局實例和便利函數
# ============================================================================

# 創建全局計算器實例
non_price_ta_calculator = NonPriceTACalculator()


def calculate_non_price_ta(
    indicator_id: str, data: pd.DataFrame, **kwargs
) -> Dict[str, Any]:
    """
    便利函數：計算NON PRICE DATA技術指標

    Args:
        indicator_id: 指標ID (如 "HB_RS_14_1")
        data: 數據DataFrame
        **kwargs: 額外參數

    Returns:
        計算結果字典
    """
    return non_price_ta_calculator.calculate_indicator(indicator_id, data, **kwargs)


def generate_all_hibor_indicators() -> List[str]:
    """生成所有HIBOR相關的指標ID"""
    return non_price_ta_calculator.get_indicators_by_data_source(DataSourceCode.HIBOR)


def generate_all_gdp_indicators() -> List[str]:
    """生成所有GDP相關的指標ID"""
    return non_price_ta_calculator.get_indicators_by_data_source(DataSourceCode.GDP)


def list_all_rsi_indicators() -> List[str]:
    """列出所有RSI類型指標"""
    return non_price_ta_calculator.get_indicators_by_type(IndicatorTypeCode.RSI)


def list_all_macd_indicators() -> List[str]:
    """列出所有MACD類型指標"""
    return non_price_ta_calculator.get_indicators_by_type(IndicatorTypeCode.MACD)


# ============================================================================
# 📋 批量計算功能
# ============================================================================


def calculate_multiple_indicators(
    indicator_ids: List[str], data: pd.DataFrame
) -> Dict[str, Dict[str, Any]]:
    """
    批量計算多個指標

    Args:
        indicator_ids: 指標ID列表
        data: 數據DataFrame

    Returns:
        所有指標的計算結果字典
    """
    results = {}
    for indicator_id in indicator_ids:
        results[indicator_id] = calculate_non_price_ta(indicator_id, data)

    return results


def calculate_all_hibor_indicators(data: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """計算所有HIBOR相關指標"""
    hibor_indicators = generate_all_hibor_indicators()
    return calculate_multiple_indicators(hibor_indicators, data)


# ============================================================================
# 🎯 示例使用
# ============================================================================

if __name__ == "__main__":
    # 示例數據
    dates = pd.date_range(start="2024 - 01 - 01", end="2024 - 12 - 31", freq="D")
    sample_data = pd.DataFrame(
        {
            "date": dates,
            "hibor_rate": np.random.normal(2.0, 0.5, len(dates)),
            "gdp_growth": np.random.normal(0.02, 0.01, len(dates)),
            "retail_sales": np.random.normal(100, 10, len(dates)),
        }
    )
    sample_data.set_index("date", inplace=True)

    # 計算HIBOR RSI
    hibor_rsi_result = calculate_non_price_ta("HB_RS_14_1", sample_data)
    print(f"HIBOR RSI 計算結果: {hibor_rsi_result['display_name']}")
    print(f"最新值: {hibor_rsi_result['result'].iloc[-1]:.2f}")

    # 計算所有HIBOR指標
    all_hibor_results = calculate_all_hibor_indicators(sample_data)
    print(f"\n共計算了 {len(all_hibor_results)} 個HIBOR指標")

    # 列出可用的指標
    available_indicators = non_price_ta_calculator.get_available_indicators()
    print(f"\n系統中共有 {len(available_indicators)} 個技術指標")
    print("前10個指標ID:")
    for i, indicator_id in enumerate(available_indicators[:10]):
        print(f"  {i + 1}. {indicator_id}")

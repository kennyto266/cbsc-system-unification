#!/usr / bin / env python3
"""
Enhanced Core Indicators - 支持非價格數據的核心技術指標引擎
Enhanced Core Indicators - Core Technical Indicators Engine with Non - Price Data Support

擴展原有的CoreIndicators以支持香港政府經濟數據的技術分析
Extended CoreIndicators to support technical analysis of Hong Kong government economic data
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Union

import numpy as np
import pandas as pd

# Import the original CoreIndicators
from .core_indicators import CoreIndicators

logger = logging.getLogger(__name__)


class EnhancedCoreIndicators(CoreIndicators):
    """
    增強核心技術指標計算引擎

    在原有基礎上增加：
    - 非價格數據適配
    - 經濟數據專用指標
    - 智能參數適配
    - 數據類型檢測
    """

    def __init__(self):
        """初始化增強核心指標引擎"""
        super().__init__()

        # 數據類型檢測配置
        self.rate_data_keywords = ["rate", "interest", "hibor", "yield", "liquidity"]
        self.flow_data_keywords = ["flow", "change", "movement", "activity"]
        self.ratio_data_keywords = ["ratio", "index", "level"]

        logger.info(
            "Enhanced Core Technical Indicators Engine initialized with non - price data support"
        )

    def detect_data_type(self, data: pd.Series, column_name: str = None) -> str:
        """
        檢測數據類型並返回適配策略

        Args:
            data: 數據序列
            column_name: 列名稱

        Returns:
            數據類型字符串
        """
        if data.empty:
            return "unknown"

        # 基於列名判斷
        if column_name:
            col_lower = column_name.lower()
            if any(keyword in col_lower for keyword in self.rate_data_keywords):
                return "rate_data"
            elif any(keyword in col_lower for keyword in self.flow_data_keywords):
                return "flow_data"
            elif any(keyword in col_lower for keyword in self.ratio_data_keywords):
                return "ratio_data"

        # 基於數據特徵判斷
        values = data.dropna()
        if len(values) < 10:
            return "unknown"

        # 檢查是否為利率類型 (通常為正值，範圍合理)
        positive_ratio = (values > 0).mean()
        if positive_ratio > 0.9 and values.max() < 100:
            return "rate_data"

        # 檢查是否為流量數據 (可能有正有負)
        has_negative = (values < 0).any()
        if has_negative:
            return "flow_data"

        # 默認為比率數據
        return "ratio_data"

    def adapt_parameters_for_data_type(
        self, data_type: str, base_params: Dict = None
    ) -> Dict:
        """
        根據數據類型適配參數

        Args:
            data_type: 數據類型
            base_params: 基礎參數

        Returns:
            適配後的參數
        """
        if base_params is None:
            base_params = {}

        adapted_params = base_params.copy()

        if data_type == "rate_data":
            # 利率數據：通常較穩定，使用中等週期
            adapted_params.update(
                {
                    "rsi_period": base_params.get("rsi_period", 14),
                    "macd_fast": base_params.get("macd_fast", 12),
                    "macd_slow": base_params.get("macd_slow", 26),
                    "sma_period": base_params.get("sma_period", 20),
                    "adaptation": "利率數據適配：使用標準參數，適合穩定趨勢",
                }
            )
        elif data_type == "flow_data":
            # 流量數據：波動較大，使用較長週期平滑
            adapted_params.update(
                {
                    "rsi_period": max(21, base_params.get("rsi_period", 14) * 1.5),
                    "macd_fast": max(15, base_params.get("macd_fast", 12) * 1.2),
                    "macd_slow": max(35, base_params.get("macd_slow", 26) * 1.3),
                    "sma_period": max(30, base_params.get("sma_period", 20) * 1.5),
                    "adaptation": "流量數據適配：延長週期以平滑波動",
                }
            )
        elif data_type == "ratio_data":
            # 比率數據：介於兩者之間
            adapted_params.update(
                {
                    "rsi_period": max(16, base_params.get("rsi_period", 14) * 1.1),
                    "macd_fast": max(10, base_params.get("macd_fast", 12) * 0.8),
                    "macd_slow": max(22, base_params.get("macd_slow", 26) * 0.9),
                    "sma_period": max(15, base_params.get("sma_period", 20) * 0.8),
                    "adaptation": "比率數據適配：平衡參數設置",
                }
            )

        return adapted_params

    # ==================== 增強趨勢指標 ====================

    def calculate_sma_non_price(
        self, data: pd.Series, period: int = None, column_name: str = None
    ) -> Tuple[pd.Series, Dict]:
        """
        為非價格數據計算SMA

        Args:
            data: 數據序列
            period: 週期
            column_name: 列名稱

        Returns:
            (SMA序列, 適配信息)
        """
        data_type = self.detect_data_type(data, column_name)

        # 自動適配週期
        if period is None:
            adapted_params = self.adapt_parameters_for_data_type(data_type)
            period = adapted_params.get("sma_period", 20)
        else:
            adapted_params = self.adapt_parameters_for_data_type(
                data_type, {"sma_period": period}
            )

        # 計算SMA
        sma = self.calculate_sma(data, int(period))

        # 添加適配信息
        adaptation_info = {
            "data_type": data_type,
            "period_used": int(period),
            "adaptation_reason": adapted_params.get(
                "adaptation", "Standard adaptation"
            ),
            "data_length": len(data),
            "data_quality": self._assess_data_quality(data),
        }

        return sma, adaptation_info

    def calculate_ema_non_price(
        self, data: pd.Series, period: int = None, column_name: str = None
    ) -> Tuple[pd.Series, Dict]:
        """
        為非價格數據計算EMA

        Args:
            data: 數據序列
            period: 週期
            column_name: 列名稱

        Returns:
            (EMA序列, 適配信息)
        """
        data_type = self.detect_data_type(data, column_name)

        if period is None:
            adapted_params = self.adapt_parameters_for_data_type(data_type)
            period = adapted_params.get("ema_period", 26)
        else:
            adapted_params = self.adapt_parameters_for_data_type(
                data_type, {"ema_period": period}
            )

        ema = self.calculate_ema(data, int(period))

        adaptation_info = {
            "data_type": data_type,
            "period_used": int(period),
            "adaptation_reason": adapted_params.get(
                "adaptation", "Standard adaptation"
            ),
            "data_length": len(data),
        }

        return ema, adaptation_info

    def calculate_macd_non_price(
        self,
        data: pd.Series,
        fast: int = None,
        slow: int = None,
        signal: int = None,
        column_name: str = None,
    ) -> Dict[str, Union[Dict, pd.Series]]:
        """
        為非價格數據計算MACD

        Args:
            data: 數據序列
            fast: 快線週期
            slow: 慢線週期
            signal: 信號線週期
            column_name: 列名稱

        Returns:
            包含MACD結果和適配信息的字典
        """
        data_type = self.detect_data_type(data, column_name)

        # 自動適配參數
        if fast is None or slow is None:
            adapted_params = self.adapt_parameters_for_data_type(data_type)
            fast = int(adapted_params.get("macd_fast", 12))
            slow = int(adapted_params.get("macd_slow", 26))
        else:
            adapted_params = self.adapt_parameters_for_data_type(
                data_type, {"macd_fast": fast, "macd_slow": slow}
            )
            fast = int(fast)
            slow = int(slow)

        if signal is None:
            signal = 9

        # 計算MACD
        macd_result = self.calculate_macd(data, fast, slow, signal)

        # 添加適配信息
        adaptation_info = {
            "data_type": data_type,
            "parameters_used": {"fast": fast, "slow": slow, "signal": signal},
            "adaptation_reason": adapted_params.get(
                "adaptation", "Standard adaptation"
            ),
            "data_length": len(data),
            "signal_quality": self._assess_macd_signal_quality(macd_result),
        }

        return {
            "macd": macd_result["macd"],
            "signal": macd_result["signal"],
            "histogram": macd_result["histogram"],
            "adaptation_info": adaptation_info,
        }

    # ==================== 增強動量指標 ====================

    def calculate_rsi_non_price(
        self, data: pd.Series, period: int = None, column_name: str = None
    ) -> Tuple[pd.Series, Dict]:
        """
        為非價格數據計算RSI

        Args:
            data: 數據序列
            period: 週期
            column_name: 列名稱

        Returns:
            (RSI序列, 適配信息)
        """
        data_type = self.detect_data_type(data, column_name)

        if period is None:
            adapted_params = self.adapt_parameters_for_data_type(data_type)
            period = int(adapted_params.get("rsi_period", 14))
        else:
            adapted_params = self.adapt_parameters_for_data_type(
                data_type, {"rsi_period": period}
            )

        rsi = self.calculate_rsi(data, int(period))

        adaptation_info = {
            "data_type": data_type,
            "period_used": int(period),
            "adaptation_reason": adapted_params.get(
                "adaptation", "Standard adaptation"
            ),
            "data_length": len(data),
            "rsi_characteristics": self._analyze_rsi_characteristics(rsi),
        }

        return rsi, adaptation_info

    # ==================== 經濟數據專用指標 ====================

    def calculate_rate_spread(
        self,
        rate_data_short: pd.Series,
        rate_data_long: pd.Series,
        short_name: str = "short_term",
        long_name: str = "long_term",
    ) -> Dict:
        """
        計算利率期限結構利差

        Args:
            rate_data_short: 短期利率數據
            rate_data_long: 長期利率數據
            short_name: 短期名稱
            long_name: 長期名稱

        Returns:
            利差分析結果
        """
        # 確保數據對齊
        common_index = rate_data_short.index.intersection(rate_data_long.index)
        short_aligned = rate_data_short.loc[common_index]
        long_aligned = rate_data_long.loc[common_index]

        # 計算利差
        spread = long_aligned - short_aligned
        spread_mean = spread.rolling(window = 20, min_periods = 1).mean()
        spread_std = spread.rolling(window = 20, min_periods = 1).std()

        # 計算Z - score
        spread_zscore = (spread - spread_mean) / spread_std
        spread_zscore = spread_zscore.replace([np.inf, -np.inf], 0).fillna(0)

        # 計算百分位數
        spread_percentile = (
            spread.rolling(window = 252, min_periods = 1).rank(pct = True) * 100
        )

        return {
            "spread": spread,
            "spread_mean": spread_mean,
            "spread_zscore": spread_zscore,
            "spread_percentile": spread_percentile,
            "metadata": {
                "short_term_mean": short_aligned.mean(),
                "long_term_mean": long_aligned.mean(),
                "average_spread": spread.mean(),
                "spread_volatility": spread.std(),
                "data_points": len(spread),
            },
        }

    def calculate_yield_curve_indicator(
        self, yield_rates: Dict[str, pd.Series]
    ) -> Dict:
        """
        計算收益率曲線指標

        Args:
            yield_rates: 不同期限的收益率數據 {'2y': Series, '10y': Series, ...}

        Returns:
            收益率曲線分析結果
        """
        if not yield_rates:
            return {}

        # 確保所有數據對齊
        common_index = None
        for series in yield_rates.values():
            if common_index is None:
                common_index = series.index
            else:
                common_index = common_index.intersection(series.index)

        aligned_rates = {
            tenor: rates.loc[common_index] for tenor, rates in yield_rates.items()
        }

        # 計算曲線斜率 (2年 vs 10年)
        if "2y" in aligned_rates and "10y" in aligned_rates:
            slope_2y_10y = aligned_rates["10y"] - aligned_rates["2y"]
            slope_2y_10y_ma = slope_2y_10y.rolling(window = 20, min_periods = 1).mean()
        else:
            slope_2y_10y = pd.Series([0] * len(common_index), index = common_index)
            slope_2y_10y_ma = slope_2y_10y

        # 計算曲率 (2y, 10y, 30y)
        if "2y" in aligned_rates and "10y" in aligned_rates and "30y" in aligned_rates:
            curvature = (
                2 * aligned_rates["10y"] - aligned_rates["2y"] - aligned_rates["30y"]
            )
            curvature_ma = curvature.rolling(window = 20, min_periods = 1).mean()
        else:
            curvature = pd.Series([0] * len(common_index), index = common_index)
            curvature_ma = curvature

        # 計算整體水平 (所有期限的平均)
        all_rates_df = pd.DataFrame(aligned_rates)
        level = all_rates_df.mean(axis = 1)
        level_ma = level.rolling(window = 20, min_periods = 1).mean()

        return {
            "slope_2y_10y": slope_2y_10y,
            "slope_ma": slope_2y_10y_ma,
            "curvature": curvature,
            "curvature_ma": curvature_ma,
            "level": level,
            "level_ma": level_ma,
            "metadata": {
                "available_tenors": list(aligned_rates.keys()),
                "curve_characteristics": {
                    "avg_slope": slope_2y_10y.mean(),
                    "slope_volatility": slope_2y_10y.std(),
                    "avg_curvature": curvature.mean(),
                    "curvature_volatility": curvature.std(),
                    "avg_level": level.mean(),
                    "level_volatility": level.std(),
                },
            },
        }

    def calculate_monetary_momentum(
        self, monetary_data: pd.Series, period: int = 20
    ) -> Dict:
        """
        計算貨幣數據動量指標

        Args:
            monetary_data: 貨幣數據序列
            period: 計算週期

        Returns:
            動量分析結果
        """
        # 計算變化率
        change_rate = monetary_data.pct_change(period)
        change_rate_ma = change_rate.rolling(window = 10, min_periods = 1).mean()

        # 計算加速率 (變化率的變化)
        acceleration = change_rate.diff()
        acceleration_ma = acceleration.rolling(window = 10, min_periods = 1).mean()

        # 計算趨勢強度
        trend_strength = monetary_data.rolling(window = period, min_periods = 1).apply(
            lambda x: abs(np.corrcoef(np.arange(len(x)), x)[0, 1]) if len(x) > 1 else 0
        )

        # 計算相對強度 (相對於歷史水平)
        historical_median = monetary_data.expanding().median()
        relative_strength = (monetary_data - historical_median) / historical_median
        relative_strength = relative_strength.replace([np.inf, -np.inf], 0).fillna(0)

        return {
            "change_rate": change_rate,
            "change_rate_ma": change_rate_ma,
            "acceleration": acceleration,
            "acceleration_ma": acceleration_ma,
            "trend_strength": trend_strength,
            "relative_strength": relative_strength,
            "metadata": {
                "avg_change_rate": change_rate.mean(),
                "change_rate_volatility": change_rate.std(),
                "avg_trend_strength": trend_strength.mean(),
                "data_trend": (
                    "increasing"
                    if monetary_data.iloc[-1] > monetary_data.iloc[0]
                    else "decreasing"
                ),
            },
        }

    # ==================== 輔助方法 ====================

    def _assess_data_quality(self, data: pd.Series) -> Dict:
        """評估數據質量"""
        values = data.dropna()
        if values.empty:
            return {"quality_score": 0, "issues": ["Empty data"]}

        # 計算質量指標
        completeness = len(values) / len(data)
        has_negative = (values < 0).any()
        has_outliers = self._detect_outliers(values)
        trend_consistency = self._assess_trend_consistency(values)

        quality_score = completeness
        if has_negative:
            quality_score *= 0.9
        if has_outliers:
            quality_score *= 0.8
        if trend_consistency < 0.5:
            quality_score *= 0.9

        issues = []
        if completeness < 0.9:
            issues.append("Missing data")
        if has_outliers:
            issues.append("Outliers detected")
        if has_negative:
            issues.append("Negative values present")

        return {
            "quality_score": quality_score,
            "completeness": completeness,
            "has_negative_values": has_negative,
            "has_outliers": has_outliers,
            "trend_consistency": trend_consistency,
            "issues": issues,
        }

    def _detect_outliers(self, values: pd.Series, threshold: float = 3.0) -> bool:
        """檢測異常值"""
        if len(values) < 10:
            return False

        z_scores = np.abs((values - values.mean()) / values.std())
        return (z_scores > threshold).any()

    def _assess_trend_consistency(self, values: pd.Series) -> float:
        """評估趨勢一致性"""
        if len(values) < 20:
            return 0.5

        # 計算短期和長期趨勢的相關性
        short_trend = values.rolling(window = 10, min_periods = 1).mean()
        long_trend = values.rolling(window = len(values) // 4, min_periods = 1).mean()

        correlation = short_trend.corr(long_trend)
        return abs(correlation) if not pd.isna(correlation) else 0.5

    def _assess_macd_signal_quality(self, macd_result: Dict) -> Dict:
        """評估MACD信號質量"""
        macd_line = macd_result["macd"].dropna()
        signal_line = macd_result["signal"].dropna()
        histogram = macd_result["histogram"].dropna()

        if len(histogram) == 0:
            return {"signal_quality": 0, "issues": ["Insufficient data"]}

        # 計算信號變化頻率
        signal_changes = (histogram > 0).astype(int).diff().abs().sum()
        signal_frequency = signal_changes / len(histogram)

        # 計算MACD和信號線的收斂性
        convergence = abs(macd_line - signal_line).mean()

        # 計算柱狀圖的平衡性
        positive_ratio = (histogram > 0).mean()

        signal_quality = max(0, 1 - signal_frequency) * 0.6 + (1 - convergence) * 0.4

        return {
            "signal_quality": signal_quality,
            "signal_frequency": signal_frequency,
            "convergence_level": convergence,
            "positive_ratio": positive_ratio,
            "assessment": (
                "Good"
                if signal_quality > 0.7
                else "Fair" if signal_quality > 0.5 else "Poor"
            ),
        }

    def _analyze_rsi_characteristics(self, rsi: pd.Series) -> Dict:
        """分析RSI特性"""
        clean_rsi = rsi.dropna()
        if len(clean_rsi) == 0:
            return {"analysis": "Insufficient data"}

        # 計算統計特性
        mean_rsi = clean_rsi.mean()
        std_rsi = clean_rsi.std()
        overbought_ratio = (clean_rsi > 70).mean()
        oversold_ratio = (clean_rsi < 30).mean()

        # 分析均衡性
        neutrality_ratio = ((clean_rsi >= 40) & (clean_rsi <= 60)).mean()

        return {
            "mean_rsi": mean_rsi,
            "std_rsi": std_rsi,
            "overbought_frequency": overbought_ratio,
            "oversold_frequency": oversold_ratio,
            "neutrality_ratio": neutrality_ratio,
            "assessment": self._classify_rsi_pattern(
                mean_rsi, std_rsi, overbought_ratio, oversold_ratio
            ),
        }

    def _classify_rsi_pattern(
        self,
        mean_rsi: float,
        std_rsi: float,
        overbought_ratio: float,
        oversold_ratio: float,
    ) -> str:
        """分類RSI模式"""
        if mean_rsi > 55:
            return "Bullish tendency"
        elif mean_rsi < 45:
            return "Bearish tendency"
        elif overbought_ratio < 0.1 and oversold_ratio < 0.1:
            return "Range - bound, low volatility"
        elif overbought_ratio > 0.2 or oversold_ratio > 0.2:
            return "High volatility, frequent extremes"
        else:
            return "Balanced behavior"

    # ==================== 批量計算方法 ====================

    def calculate_comprehensive_indicators(
        self, df: pd.DataFrame, target_columns: List[str] = None
    ) -> Dict[str, Dict]:
        """
        為DataFrame計算全面的技術指標

        Args:
            df: 數據框
            target_columns: 目標列名，如果為None則自動選擇

        Returns:
            全面指標結果字典
        """
        if target_columns is None:
            # 自動選擇數值列
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            # 排除日期列
            target_columns = [col for col in numeric_cols if "date" not in col.lower()]

        results = {}

        for column in target_columns:
            if column not in df.columns:
                continue

            data = df[column].dropna()
            if len(data) < 20:  # 數據不足
                continue

            logger.info(f"Calculating indicators for column: {column}")

            column_results = {
                "data_type": self.detect_data_type(data, column),
                "data_length": len(data),
                "indicators": {},
            }

            try:
                # 趨勢指標
                sma, sma_info = self.calculate_sma_non_price(data, column_name = column)
                ema, ema_info = self.calculate_ema_non_price(data, column_name = column)
                macd_result = self.calculate_macd_non_price(data, column_name = column)

                column_results["indicators"]["sma"] = {"values": sma, "info": sma_info}
                column_results["indicators"]["ema"] = {"values": ema, "info": ema_info}
                column_results["indicators"]["macd"] = macd_result

                # 動量指標
                rsi, rsi_info = self.calculate_rsi_non_price(data, column_name = column)
                column_results["indicators"]["rsi"] = {"values": rsi, "info": rsi_info}

                # 根據數據類型計算專用指標
                if "rate" in column.lower() and "yield" in column.lower():
                    # 收益率數據的特殊處理
                    if len(data) > 100:  # 數據足夠長
                        # 模擬不同期限的收益率曲線
                        column_results["indicators"]["yield_analysis"] = {
                            "trend_strength": self._calculate_trend_strength(data),
                            "volatility_analysis": self._calculate_volatility_analysis(
                                data
                            ),
                        }

                results[column] = column_results

            except Exception as e:
                logger.error(f"Error calculating indicators for column {column}: {e}")
                results[column] = {
                    "error": str(e),
                    "data_type": self.detect_data_type(data, column),
                    "data_length": len(data),
                }

        return results

    def _calculate_trend_strength(self, data: pd.Series, window: int = 50) -> Dict:
        """計算趨勢強度"""
        if len(data) < window:
            return {"strength": 0, "direction": "unknown"}

        # 使用線性回歸計算趨勢強度
        x = np.arange(len(data))
        slope, intercept = np.polyfit(x[-window:], data.iloc[-window:], 1)

        # 計算R²
        y_pred = slope * x[-window:] + intercept
        ss_res = np.sum((data.iloc[-window:] - y_pred) ** 2)
        ss_tot = np.sum((data.iloc[-window:] - data.iloc[-window:].mean()) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        return {
            "strength": abs(r_squared),
            "direction": "increasing" if slope > 0 else "decreasing",
            "slope": slope,
            "r_squared": r_squared,
        }

    def _calculate_volatility_analysis(self, data: pd.Series) -> Dict:
        """計算波動率分析"""
        returns = data.pct_change().dropna()
        if len(returns) == 0:
            return {"volatility": 0, "analysis": "No data"}

        volatility = returns.std()
        mean_return = returns.mean()

        # 分類波動率等級
        if volatility < 0.01:
            volatility_level = "Low"
        elif volatility < 0.05:
            volatility_level = "Medium"
        else:
            volatility_level = "High"

        return {
            "volatility": volatility,
            "volatility_level": volatility_level,
            "mean_return": mean_return,
            "analysis": f'{volatility_level} volatility with {"positive" if mean_return > 0 else "negative"} trend',
        }

    def save_indicators_results(self, results: Dict, output_path: str = None):
        """保存指標計算結果"""
        if output_path is None:
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"data / indicators_results_{timestamp}.json"

        output_path = Path(output_path)
        output_path.parent.mkdir(parents = True, exist_ok = True)

        # 準備可序列化的結果
        serializable_results = {}
        for column, data in results.items():
            if "error" in data:
                serializable_results[column] = data
            else:
                serializable_data = {
                    "data_type": data["data_type"],
                    "data_length": data["data_length"],
                }

                if "indicators" in data:
                    serializable_data["indicators"] = {}
                    for indicator_name, indicator_data in data["indicators"].items():
                        if (
                            isinstance(indicator_data, dict)
                            and "values" in indicator_data
                        ):
                            # 保存統計信息而不是原始數據
                            values = indicator_data["values"].dropna()
                            if not values.empty:
                                serializable_data["indicators"][indicator_name] = {
                                    "mean": float(values.mean()),
                                    "std": float(values.std()),
                                    "min": float(values.min()),
                                    "max": float(values.max()),
                                    "latest": float(values.iloc[-1]),
                                    "info": indicator_data.get("info", {}),
                                    "data_points": len(values),
                                }
                        else:
                            serializable_data["indicators"][
                                indicator_name
                            ] = indicator_data

                serializable_results[column] = serializable_data

        with open(output_path, "w", encoding="utf - 8") as f:
            json.dump(
                serializable_results, f, indent = 2, ensure_ascii = False, default = str
            )

        logger.info(f"Indicators results saved to: {output_path}")
        return output_path


def main():
    """主測試函數"""
    logging.basicConfig(
        level = logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # 創建增強核心指標引擎
    enhanced_indicators = EnhancedCoreIndicators()

    # 加載對齊後的數據
    aligned_data_dir = Path("data / aligned")
    data_dict = {}

    print("[START] Enhanced Core Indicators Testing")
    print("=" * 60)

    # 加載已對齊的數據
    for file_path in aligned_data_dir.glob("*_aligned_*.csv"):
        source_name = file_path.stem.split("_aligned_")[0]
        try:
            df = pd.read_csv(file_path)
            if not df.empty and "date" in df.columns:
                data_dict[source_name] = df
                print(
                    f"[LOADED] {source_name}: {len(df)} records, {len(df.columns)} columns"
                )
        except Exception as e:
            print(f"[ERROR] Failed to load {source_name}: {e}")

    if not data_dict:
        print("[ERROR] No aligned data found. Please run data alignment first.")
        return

    # 為每個數據源計算全面指標
    for source_name, df in data_dict.items():
        print(f"\n[PROCESSING] {source_name}")
        print("-" * 40)

        try:
            # 計算全面指標
            results = enhanced_indicators.calculate_comprehensive_indicators(df)

            print(f"Data type analysis:")
            for column, data in results.items():
                if "error" not in data:
                    print(
                        f"  {column}: {data['data_type']} ({data['data_length']} points)"
                    )

                    if "indicators" in data:
                        indicators = data["indicators"]
                        print(f"    Calculated indicators: {list(indicators.keys())}")

                        # 顯示RSI信息
                        if "rsi" in indicators and "info" in indicators["rsi"]:
                            rsi_info = indicators["rsi"]["info"]
                            print(
                                f"    RSI pattern: {rsi_info.get('assessment', 'Unknown')}"
                            )

                        # 顯示MACD信息
                        if (
                            "macd" in indicators
                            and "adaptation_info" in indicators["macd"]
                        ):
                            macd_info = indicators["macd"]["adaptation_info"]
                            print(
                                f"    MACD signal quality: {macd_info.get('signal_quality', {}).get('assessment', 'Unknown')}"
                            )

            # 保存結果
            output_path = enhanced_indicators.save_indicators_results(
                results, f"data / enhanced_indicators_{source_name}.json"
            )
            print(f"[SAVED] Results saved to: {output_path}")

        except Exception as e:
            print(f"[ERROR] Failed to process {source_name}: {e}")

    print(f"\n[COMPLETE] Enhanced Core Indicators testing completed successfully!")


if __name__ == "__main__":
    main()

#!/usr / bin / env python3
# -*- coding: utf - 8 -*-
"""
HKMA金融數據性能分析器 - 整合到現有系統
為現有三層架構提供HKMA宏觀經濟數據分析能力

Author: Claude AI Assistant
Date: 2025 - 11 - 19
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class HKMAPerformanceAnalyzer:
    """HKMA宏觀經濟數據性能分析器"""

    def __init__(self):
        self.data_dir = Path("hkma_data")
        self.analysis_cache = {}

    def calculate_hibor_indicators(self, data: pd.DataFrame) -> Dict[str, float]:
        """
        計算HIBOR相關技術指標

        Args:
            data: 銀行流動性數據

        Returns:
            技術指標字典
        """
        if data.empty or "hibor_overnight" not in data.columns:
            return {}

        data = data.sort_values("end_of_date")
        hibor_series = data["hibor_overnight"].dropna()

        indicators = {
            # 基礎統計
            "hibor_current": float(hibor_series.iloc[-1]),
            "hibor_change_1d": float(hibor_series.diff().iloc[-1]),
            "hibor_change_7d": float(hibor_series.diff(7).iloc[-1]),
            # 移動平均線
            "hibor_ma7": float(hibor_series.rolling(7).mean().iloc[-1]),
            "hibor_ma30": float(hibor_series.rolling(30).mean().iloc[-1]),
            "hibor_ma90": float(hibor_series.rolling(90).mean().iloc[-1]),
            # RSI指標
            "hibor_rsi_14": self._calculate_rsi(hibor_series, 14),
            "hibor_rsi_30": self._calculate_rsi(hibor_series, 30),
            # 波動率
            "hibor_volatility_7d": float(hibor_series.rolling(7).std().iloc[-1]),
            "hibor_volatility_30d": float(hibor_series.rolling(30).std().iloc[-1]),
            # 趨勢指標
            "hibor_trend_7d": self._calculate_trend(hibor_series, 7),
            "hibor_trend_30d": self._calculate_trend(hibor_series, 30),
            # 價差指標
            "hibor_zscore_30d": self._calculate_zscore(hibor_series, 30),
            # 布林帶
            "hibor_bb_position": self._calculate_bb_position(hibor_series),
        }

        return indicators

    def calculate_liquidity_indicators(self, data: pd.DataFrame) -> Dict[str, float]:
        """
        計算流動性指標

        Args:
            data: 銀行流動性數據

        Returns:
            流動性指標字典
        """
        if data.empty or "closing_balance" not in data.columns:
            return {}

        data = data.sort_values("end_of_date")
        balance_series = data["closing_balance"].dropna()

        indicators = {
            # 基礎指標
            "balance_current": float(balance_series.iloc[-1]),
            "balance_change_1d": float(balance_series.diff().iloc[-1]),
            "balance_change_7d": float(balance_series.diff(7).iloc[-1]),
            "balance_change_pct_7d": float(balance_series.pct_change(7).iloc[-1]),
            # 移動平均
            "balance_ma7": float(balance_series.rolling(7).mean().iloc[-1]),
            "balance_ma30": float(balance_series.rolling(30).mean().iloc[-1]),
            # 標準化指標
            "balance_zscore_30d": self._calculate_zscore(balance_series, 30),
            "balance_percentile_30d": self._calculate_percentile(balance_series, 30),
            # 波動性
            "balance_volatility_7d": float(balance_series.rolling(7).std().iloc[-1]),
            "balance_volatility_30d": float(balance_series.rolling(30).std().iloc[-1]),
            # 趨勢
            "balance_trend_7d": self._calculate_trend(balance_series, 7),
            "balance_trend_30d": self._calculate_trend(balance_series, 30),
            # 匯率價差
            "exchange_spread_current": self._calculate_exchange_spread(data),
            "exchange_spread_ma7": self._calculate_exchange_spread_ma(data, 7),
        }

        return indicators

    def calculate_monetary_base_indicators(
        self, data: pd.DataFrame
    ) -> Dict[str, float]:
        """
        計算貨幣基礎指標

        Args:
            data: 貨幣基礎數據

        Returns:
            貨幣基礎指標字典
        """
        if data.empty or "mb_bf_disc_win_total" not in data.columns:
            return {}

        data = data.sort_values("end_of_date")
        mb_series = data["mb_bf_disc_win_total"].dropna()

        indicators = {
            # 基礎指標
            "mb_current": float(mb_series.iloc[-1]),
            "mb_change_1d": float(mb_series.diff().iloc[-1]),
            "mb_change_7d": float(mb_series.diff(7).iloc[-1]),
            "mb_growth_rate_30d": float(mb_series.pct_change(30).iloc[-1]),
            # 移動平均
            "mb_ma7": float(mb_series.rolling(7).mean().iloc[-1]),
            "mb_ma30": float(mb_series.rolling(30).mean().iloc[-1]),
            # 增長率
            "mb_growth_trend_7d": self._calculate_growth_trend(mb_series, 7),
            "mb_growth_trend_30d": self._calculate_growth_trend(mb_series, 30),
            # 貨幣乘數
            "money_multiplier": self._calculate_money_multiplier(data),
            "money_multiplier_ma30": self._calculate_money_multiplier_ma(data, 30),
            # 波動性
            "mb_volatility_7d": float(mb_series.rolling(7).std().iloc[-1]),
            "mb_volatility_30d": float(mb_series.rolling(30).std().iloc[-1]),
            # 標準化
            "mb_zscore_30d": self._calculate_zscore(mb_series, 30),
            # EFBN指標
            "efbn_ratio": self._calculate_efbn_ratio(data),
            "efbn_ratio_ma30": self._calculate_efbn_ratio_ma(data, 30),
        }

        return indicators

    def calculate_rmb_liquidity_indicators(
        self, data: pd.DataFrame
    ) -> Dict[str, float]:
        """
        計算人民幣流動性指標

        Args:
            data: 人民幣流動性數據

        Returns:
            人民幣流動性指標字典
        """
        if data.empty:
            return {}

        # 計算總流動性
        intraday_columns = [col for col in data.columns if "intraday_repo_at_" in col]
        overnight_columns = [col for col in data.columns if "overnight_repo_at_" in col]
        plp_columns = [col for col in data.columns if "plp_fac_at_" in col]

        data["rmb_total_intraday"] = data[intraday_columns].sum(axis=1)
        data["rmb_total_overnight"] = data[overnight_columns].sum(axis=1)
        data["rmb_total_plp"] = data[plp_columns].sum(axis=1)
        data["rmb_total_liquidity"] = (
            data["rmb_total_intraday"]
            + data["rmb_total_overnight"]
            + data["rmb_total_plp"]
        )

        indicators = {
            # 總流動性
            "rmb_liquidity_total": float(data["rmb_total_liquidity"].iloc[-1]),
            "rmb_liquidity_intraday": float(data["rmb_total_intraday"].iloc[-1]),
            "rmb_liquidity_overnight": float(data["rmb_total_overnight"].iloc[-1]),
            "rmb_liquidity_plp": float(data["rmb_total_plp"].iloc[-1]),
            # 變化趨勢
            "rmb_liquidity_change_1d": float(
                data["rmb_total_liquidity"].diff().iloc[-1]
            ),
            "rmb_liquidity_change_7d": float(
                data["rmb_total_liquidity"].diff(7).iloc[-1]
            ),
            "rmb_liquidity_growth_rate_7d": float(
                data["rmb_total_liquidity"].pct_change(7).iloc[-1]
            ),
            # 移動平均
            "rmb_liquidity_ma7": float(
                data["rmb_total_liquidity"].rolling(7).mean().iloc[-1]
            ),
            "rmb_liquidity_ma30": float(
                data["rmb_total_liquidity"].rolling(30).mean().iloc[-1]
            ),
            # 比例指標
            "rmb_intraday_ratio": float(
                data["rmb_total_intraday"].iloc[-1]
                / data["rmb_total_liquidity"].iloc[-1]
            ),
            "rmb_overnight_ratio": float(
                data["rmb_total_overnight"].iloc[-1]
                / data["rmb_total_liquidity"].iloc[-1]
            ),
            "rmb_plp_ratio": float(
                data["rmb_total_plp"].iloc[-1] / data["rmb_total_liquidity"].iloc[-1]
            ),
            # 波動性
            "rmb_liquidity_volatility_7d": float(
                data["rmb_total_liquidity"].rolling(7).std().iloc[-1]
            ),
            "rmb_liquidity_volatility_30d": float(
                data["rmb_total_liquidity"].rolling(30).std().iloc[-1]
            ),
            # 活躍度指標
            "rmb_liquidity_activity_index": self._calculate_activity_index(data),
        }

        return indicators

    def calculate_bond_yield_indicators(
        self, closing_data: pd.DataFrame, indicative_data: pd.DataFrame
    ) -> Dict[str, float]:
        """
        計算債券收益率指標

        Args:
            closing_data: 收市價數據
            indicative_data: 參考價數據

        Returns:
            債券收益率指標字典
        """
        indicators = {}

        # 處理收市價數據
        if not closing_data.empty and "yield" in closing_data.columns:
            closing_yields = closing_data[closing_data["segment"] == "Bills"]["yield"]
            if not closing_yields.empty:
                indicators.update(
                    {
                        "bond_yield_bills_current": float(closing_yields.iloc[-1]),
                        "bond_yield_bills_ma7": float(
                            closing_yields.rolling(7).mean().iloc[-1]
                        ),
                        "bond_yield_bills_volatility": float(
                            closing_yields.rolling(7).std().iloc[-1]
                        ),
                        "bond_yield_bills_trend": self._calculate_trend(
                            closing_yields, 7
                        ),
                    }
                )

        # 處理參考價數據
        if not indicative_data.empty and "yield" in indicative_data.columns:
            indicative_yields = indicative_data[
                indicative_data["segment"] == "IndicativePrice"
            ]["yield"]
            if not indicative_yields.empty:
                indicators.update(
                    {
                        "bond_yield_indicative_current": float(
                            indicative_yields.iloc[-1]
                        ),
                        "bond_yield_indicative_ma7": float(
                            indicative_yields.rolling(7).mean().iloc[-1]
                        ),
                        "bond_yield_indicative_volatility": float(
                            indicative_yields.rolling(7).std().iloc[-1]
                        ),
                    }
                )

        return indicators

    def calculate_macro_composite_indicators(
        self,
        hibor_indicators: Dict[str, float],
        liquidity_indicators: Dict[str, float],
        monetary_indicators: Dict[str, float],
        rmb_indicators: Dict[str, float],
        bond_indicators: Dict[str, float],
    ) -> Dict[str, float]:
        """
        計算綜合宏觀指標

        Args:
            各種類別的指標

        Returns:
            綜合宏觀指標字典
        """
        composite_indicators = {}

        try:
            # 金融壓力指數 (0 - 100, 越高越壓力大)
            stress_score = 0
            stress_factors = 0

            if "hibor_current" in hibor_indicators:
                hibor_score = min(
                    100, (hibor_indicators["hibor_current"] - 2.0) * 20
                )  # 基準2%
                stress_score += hibor_score
                stress_factors += 1

            if "balance_zscore_30d" in liquidity_indicators:
                balance_score = min(
                    100, abs(liquidity_indicators["balance_zscore_30d"]) * 25
                )
                stress_score += balance_score
                stress_factors += 1

            if "mb_zscore_30d" in monetary_indicators:
                mb_score = min(100, abs(monetary_indicators["mb_zscore_30d"]) * 25)
                stress_score += mb_score
                stress_factors += 1

            if stress_factors > 0:
                composite_indicators["financial_stress_index"] = (
                    stress_score / stress_factors
                )
                composite_indicators["financial_stress_level"] = (
                    self._classify_stress_level(
                        composite_indicators["financial_stress_index"]
                    )
                )

            # 流動性狀況指數 (0 - 100, 越高流動性越好)
            liquidity_score = 0
            liquidity_factors = 0

            if "rmb_liquidity_total" in rmb_indicators:
                # 正規化RMB流動性
                rmb_liquidity_score = min(
                    100, rmb_indicators["rmb_liquidity_total"] / 500 * 100
                )  # 假設500億為滿分
                liquidity_score += rmb_liquidity_score
                liquidity_factors += 1

            if "balance_current" in liquidity_indicators:
                # 正規化銀行結餘
                balance_score = min(
                    100, liquidity_indicators["balance_current"] / 100000 * 100
                )  # 假設1000億為滿分
                liquidity_score += balance_score
                liquidity_factors += 1

            if liquidity_factors > 0:
                composite_indicators["liquidity_condition_index"] = (
                    liquidity_score / liquidity_factors
                )
                composite_indicators["liquidity_condition_level"] = (
                    self._classify_liquidity_level(
                        composite_indicators["liquidity_condition_index"]
                    )
                )

            # 貨幣政策立場指數
            if (
                "hibor_current" in hibor_indicators
                and "mb_current" in monetary_indicators
            ):
                policy_stance = "neutral"  # 默認中性
                if hibor_indicators["hibor_current"] > 4.0:
                    policy_stance = "tight"  # 緊縮
                elif hibor_indicators["hibor_current"] < 2.0:
                    policy_stance = "loose"  # 宽松

                composite_indicators["monetary_policy_stance"] = policy_stance
                composite_indicators["policy_tightness_score"] = (
                    hibor_indicators["hibor_current"] / 5.0 * 100
                )  # 5 % 為緊縮極限

            # 無風險利率基準
            if "bond_yield_bills_current" in bond_indicators:
                composite_indicators["risk_free_rate"] = (
                    bond_indicators["bond_yield_bills_current"] / 100
                )  # 轉換為小數
            elif "bond_yield_indicative_current" in bond_indicators:
                composite_indicators["risk_free_rate"] = (
                    bond_indicators["bond_yield_indicative_current"] / 100
                )
            else:
                composite_indicators["risk_free_rate"] = 0.03  # 默認3%

            # 市場風險溢價估算
            if (
                "risk_free_rate" in composite_indicators
                and "hibor_current" in hibor_indicators
            ):
                composite_indicators["market_risk_premium"] = (
                    hibor_indicators["hibor_current"] / 100
                    - composite_indicators["risk_free_rate"]
                )

            # 綜合市場指數
            market_score = 0
            market_factors = 0

            # 考慮各種因素
            if "liquidity_condition_index" in composite_indicators:
                market_score += composite_indicators["liquidity_condition_index"]
                market_factors += 1

            if "financial_stress_index" in composite_indicators:
                # 壓力指數轉換為市場信心 (反向關係)
                market_score += 100 - composite_indicators["financial_stress_index"]
                market_factors += 1

            if "rmb_liquidity_total" in rmb_indicators:
                # RMB流動性積極影響
                rmb_score = min(100, rmb_indicators["rmb_liquidity_total"] / 300 * 100)
                market_score += rmb_score
                market_factors += 1

            if market_factors > 0:
                composite_indicators["market_confidence_index"] = (
                    market_score / market_factors
                )
                composite_indicators["market_sentiment"] = (
                    self._classify_market_sentiment(
                        composite_indicators["market_confidence_index"]
                    )
                )

        except Exception as e:
            logger.error(f"計算綜合指標時出錯: {e}")

        return composite_indicators

    # 輔助方法
    def _calculate_rsi(self, series: pd.Series, periods: int = 14) -> float:
        """計算RSI指標"""
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1]) if not rsi.empty else 50.0

    def _calculate_trend(self, series: pd.Series, periods: int) -> float:
        """計算趨勢 (正數上升，負數下降)"""
        if len(series) < periods:
            return 0.0

        x = np.arange(periods)
        y = series.iloc[-periods:].values
        if len(y) != periods:
            return 0.0

        slope, _ = np.polyfit(x, y, 1)
        return float(slope)

    def _calculate_zscore(self, series: pd.Series, periods: int) -> float:
        """計算Z分數"""
        if len(series) < periods:
            return 0.0

        mean = series.iloc[-periods:].mean()
        std = series.iloc[-periods:].std()
        current = series.iloc[-1]

        return float((current - mean) / std) if std != 0 else 0.0

    def _calculate_percentile(self, series: pd.Series, periods: int) -> float:
        """計算百分位數"""
        if len(series) < periods:
            return 50.0

        current = series.iloc[-1]
        percentile = (
            (series.iloc[-periods:] < current).sum() / len(series.iloc[-periods:]) * 100
        )
        return float(percentile)

    def _calculate_bollinger_bands(
        self, series: pd.Series, periods: int = 20, std_dev: int = 2
    ) -> Tuple:
        """計算布林帶"""
        if len(series) < periods:
            return series.iloc[-1], series.iloc[-1], series.iloc[-1]

        middle = series.rolling(window=periods).mean()
        std = series.rolling(window=periods).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)

        return upper, lower, middle

    def _calculate_bb_position(self, series: pd.Series) -> float:
        """計算在布林帶中的位置 (簡化版)"""
        if len(series) < 20:
            return 0.5

        current = series.iloc[-1]
        ma = series.rolling(20).mean().iloc[-1]
        std = series.rolling(20).std().iloc[-1]

        if std > 0:
            return float((current - ma) / (2 * std))
        return 0.5

    def _calculate_exchange_spread(self, data: pd.DataFrame) -> float:
        """計算匯率價差"""
        if "cu_weakside" in data.columns and "cu_strongside" in data.columns:
            latest_data = data.iloc[-1]
            return float(latest_data["cu_weakside"] - latest_data["cu_strongside"])
        return 0.1

    def _calculate_exchange_spread_ma(self, data: pd.DataFrame, periods: int) -> float:
        """計算匯率價差移動平均"""
        if "cu_weakside" in data.columns and "cu_strongside" in data.columns:
            spread = data["cu_weakside"] - data["cu_strongside"]
            return float(spread.rolling(periods).mean().iloc[-1])
        return 0.1

    def _calculate_money_multiplier(self, data: pd.DataFrame) -> float:
        """計算貨幣乘數"""
        if (
            "mb_bf_disc_win_total" in data.columns
            and "cert_of_indebt" in data.columns
            and "gov_notes_coins_circulation" in data.columns
        ):
            latest = data.iloc[-1]
            base_money = (
                latest["cert_of_indebt"] + latest["gov_notes_coins_circulation"]
            )
            if base_money > 0:
                return float(latest["mb_bf_disc_win_total"] / base_money)
        return 5.0  # 默認貨幣乘數

    def _calculate_money_multiplier_ma(self, data: pd.DataFrame, periods: int) -> float:
        """計算貨幣乘數移動平均"""
        multipliers = []
        for _, row in data.iterrows():
            base_money = row.get("cert_of_indebt", 0) + row.get(
                "gov_notes_coins_circulation", 0
            )
            if base_money > 0:
                multiplier = row["mb_bf_disc_win_total"] / base_money
                multipliers.append(multiplier)

        if multipliers:
            multiplier_series = pd.Series(multipliers)
            return float(multiplier_series.rolling(periods).mean().iloc[-1])
        return 5.0

    def _calculate_growth_trend(self, series: pd.Series, periods: int) -> float:
        """計算增長趨勢"""
        if len(series) < periods:
            return 0.0

        recent_growth = series.pct_change(periods).iloc[-1]
        return float(recent_growth * 100)  # 轉換為百分比

    def _calculate_efbn_ratio(self, data: pd.DataFrame) -> float:
        """計算EFBN佔比"""
        if (
            "outstanding_efbn" in data.columns
            and "mb_bf_disc_win_total" in data.columns
        ):
            latest = data.iloc[-1]
            if latest["mb_bf_disc_win_total"] > 0:
                return float(
                    latest["outstanding_efbn"] / latest["mb_bf_disc_win_total"]
                )
        return 0.65  # 默認EFBN佔比

    def _calculate_efbn_ratio_ma(self, data: pd.DataFrame, periods: int) -> float:
        """計算EFBN佔比移動平均"""
        ratios = []
        for _, row in data.iterrows():
            if (
                "outstanding_efbn" in row
                and "mb_bf_disc_win_total" in row
                and row["mb_bf_disc_win_total"] > 0
            ):
                ratio = row["outstanding_efbn"] / row["mb_bf_disc_win_total"]
                ratios.append(ratio)

        if ratios:
            ratio_series = pd.Series(ratios)
            return float(ratio_series.rolling(periods).mean().iloc[-1])
        return 0.65

    def _calculate_activity_index(self, data: pd.DataFrame) -> float:
        """計算人民幣流動性活躍度指標"""
        if "rmb_total_liquidity" in data.columns:
            # 基於活動強度計算指數 (0 - 100)
            max_liquidity = data["rmb_total_liquidity"].max()
            if max_liquidity > 0:
                return float(data["rmb_total_liquidity"].iloc[-1] / max_liquidity * 100)
        return 50.0

    def _classify_stress_level(self, score: float) -> str:
        """分類金融壓力等級"""
        if score >= 80:
            return "critical"
        elif score >= 60:
            return "high"
        elif score >= 40:
            return "moderate"
        elif score >= 20:
            return "low"
        else:
            return "minimal"

    def _classify_liquidity_level(self, score: float) -> str:
        """分類流動性水平"""
        if score >= 80:
            return "abundant"
        elif score >= 60:
            return "ample"
        elif score >= 40:
            return "adequate"
        elif score >= 20:
            return "tight"
        else:
            return "scarce"

    def _classify_market_sentiment(self, score: float) -> str:
        """分類市場情緒"""
        if score >= 75:
            return "bullish"
        elif score >= 60:
            return "optimistic"
        elif score >= 40:
            return "neutral"
        elif score >= 25:
            return "cautious"
        else:
            return "bearish"

    def get_comprehensive_analysis(self) -> Dict[str, Any]:
        """
        獲取綜合分析結果

        Returns:
            包含所有指標的字典
        """
        try:
            # 加載數據
            interbank_data = self._load_hkma_data("interbank_liquidity")
            monetary_data = self._load_hkma_data("monetary_base")
            rmb_data = self._load_hkma_data("rmb_liquidity")
            efbn_closing_data = self._load_hkma_data("efbn_closing")
            efbn_indicative_data = self._load_hkma_data("efbn_indicative")

            # 計算各類指標
            hibor_indicators = self.calculate_hibor_indicators(interbank_data)
            liquidity_indicators = self.calculate_liquidity_indicators(interbank_data)
            monetary_indicators = self.calculate_monetary_base_indicators(monetary_data)
            rmb_indicators = self.calculate_rmb_liquidity_indicators(rmb_data)
            bond_indicators = self.calculate_bond_yield_indicators(
                efbn_closing_data, efbn_indicative_data
            )

            # 計算綜合指標
            composite_indicators = self.calculate_macro_composite_indicators(
                hibor_indicators,
                liquidity_indicators,
                monetary_indicators,
                rmb_indicators,
                bond_indicators,
            )

            # 組合結果
            result = {
                "timestamp": datetime.now().isoformat(),
                "hibor_indicators": hibor_indicators,
                "liquidity_indicators": liquidity_indicators,
                "monetary_indicators": monetary_indicators,
                "rmb_liquidity_indicators": rmb_indicators,
                "bond_yield_indicators": bond_indicators,
                "composite_indicators": composite_indicators,
                "data_quality": self._assess_data_quality(
                    interbank_data, monetary_data, rmb_data
                ),
            }

            return result

        except Exception as e:
            logger.error(f"獲取綜合分析時出錯: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "hibor_indicators": {},
                "liquidity_indicators": {},
                "monetary_indicators": {},
                "rmb_liquidity_indicators": {},
                "bond_yield_indicators": {},
                "composite_indicators": {},
                "data_quality": "poor",
            }

    def _load_hkma_data(self, data_type: str) -> pd.DataFrame:
        """加載HKMA數據"""
        try:
            file_path = self.data_dir / f"{data_type}_20251119_20251119.json"
            if file_path.exists():
                with open(file_path, "r", encoding="utf - 8") as f:
                    data = json.load(f)
                df = pd.DataFrame(data)
                df["end_of_date"] = pd.to_datetime(df["end_of_date"])
                return df
        except Exception as e:
            logger.error(f"加載 {data_type} 數據時出錯: {e}")

        return pd.DataFrame()

    def _assess_data_quality(self, *data_frames) -> str:
        """評估數據質量"""
        total_records = sum(len(df) for df in data_frames if not df.empty)
        if total_records >= 300:
            return "excellent"
        elif total_records >= 200:
            return "good"
        elif total_records >= 100:
            return "fair"
        else:
            return "poor"

#!/usr / bin / env python3
"""
Factor Validator
Alpha因子有效性檢驗和統計分析

這個模塊實現了專業級的因子有效性檢驗功能：
- IC係數計算和檢驗
- Sharpe比率計算
- 勝率統計分析
- 因子穩定性測試
- 因子衰減分析
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

from ..factor_engine.alpha_factor_engine import FactorMetrics, FactorTypes

logger = logging.getLogger(__name__)


@dataclass
class FactorValidationResult:
    """因子有效性檢驗結果"""

    factor_name: str

    # 基本統計指標
    ic_mean: float = 0.0  # IC均值
    ic_std: float = 0.0  # IC標準差
    ic_ir: float = 0.0  # IC信息比率
    ic_skew: float = 0.0  # IC偏度
    ic_kurtosis: float = 0.0  # IC峰度

    # 有效性指標
    ic_positive_rate: float = 0.0  # IC正值率
    ic_significance: float = 0.0  # IC顯著性
    sharpe_ratio: float = 0.0  # 因子Sharpe比率
    hit_rate: float = 0.0  # 勝率
    max_drawdown: float = 0.0  # 最大回撤

    # 穩定性指標
    decay_rate: float = 0.0  # 因子衰減率
    stability_score: float = 0.0  # 穩定性評分
    turnover_rate: float = 0.0  # 換手率

    # 統計檢驗
    t_stat: float = 0.0  # t統計量
    p_value: float = 1.0  # p值
    confidence_interval: Tuple[float, float] = (0.0, 0.0)  # 置信區間

    # 元數據
    total_periods: int = 0  # 總檢驗期數
    valid_periods: int = 0  # 有效期數
    validation_start: str = ""  # 檢驗開始日期
    validation_end: str = ""  # 檢驗結束日期


class FactorValidator:
    """
    因子有效性檢驗器

    提供專業級的因子有效性檢驗功能，包括IC分析、Sharpe計算、穩定性測試等。
    基於量化投資行業標準實現。
    """

    def __init__(self, risk_free_rate: float = 0.03, confidence_level: float = 0.95):
        """
        初始化因子檢驗器

        Args:
            risk_free_rate: 無風險利率（年化）
            confidence_level: 置信水平
        """
        self.risk_free_rate = risk_free_rate
        self.confidence_level = confidence_level
        self.alpha = 1 - confidence_level

        logger.info(
            f"Factor Validator initialized with risk - free rate: {risk_free_rate}"
        )

    def validate_factor(
        self,
        factor_metrics: FactorMetrics,
        price_data: pd.DataFrame,
        returns_data: Optional[pd.Series] = None,
        holding_period: int = 1,
    ) -> FactorValidationResult:
        """
        驗證單個因子的有效性

        Args:
            factor_metrics: 因子指標對象
            price_data: 價格數據
            returns_data: 收益率數據（可選）
            holding_period: 持有期

        Returns:
            FactorValidationResult: 檢驗結果
        """
        logger.info(f"Validating factor: {factor_metrics.factor_name}")

        # 準備數據
        factor_data = factor_metrics.factor_data.copy()

        if returns_data is None:
            # 計算收益率
            if "Close" in price_data.columns:
                returns_data = price_data["Close"].pct_change(holding_period)
            else:
                returns_data = price_data.iloc[:, 0].pct_change(
                    holding_period
                )  # 假設第一列是價格

        # 對齊數據
        aligned_data = pd.concat([factor_data, returns_data], axis = 1, join="inner")
        if len(aligned_data.columns) < 2:
            logger.warning(
                f"Insufficient aligned data for factor {factor_metrics.factor_name}"
            )
            return FactorValidationResult(factor_name = factor_metrics.factor_name)

        factor_aligned = aligned_data.iloc[:, 0]
        returns_aligned = aligned_data.iloc[:, 1]

        # 移除缺失值
        valid_mask = ~(factor_aligned.isna() | returns_aligned.isna())
        factor_valid = factor_aligned[valid_mask]
        returns_valid = returns_aligned[valid_mask]

        if len(factor_valid) < 30:  # 最少需要30個觀察值
            logger.warning(
                f"Insufficient data points for factor {factor_metrics.factor_name}: {len(factor_valid)}"
            )
            return FactorValidationResult(factor_name = factor_metrics.factor_name)

        # 計算IC分析
        ic_analysis = self._calculate_ic_analysis(factor_valid, returns_valid)

        # 計算Sharpe比率
        sharpe_analysis = self._calculate_factor_sharpe(factor_valid, returns_valid)

        # 計算穩定性分析
        stability_analysis = self._calculate_stability_metrics(
            factor_valid, returns_valid
        )

        # 統計檢驗
        statistical_test = self._perform_statistical_test(factor_valid, returns_valid)

        # 創建結果對象
        result = FactorValidationResult(
            factor_name = factor_metrics.factor_name,
            # IC分析結果
            ic_mean = ic_analysis["ic_mean"],
            ic_std = ic_analysis["ic_std"],
            ic_ir = ic_analysis["ic_ir"],
            ic_skew = ic_analysis["ic_skew"],
            ic_kurtosis = ic_analysis["ic_kurtosis"],
            ic_positive_rate = ic_analysis["positive_rate"],
            ic_significance = ic_analysis["significance"],
            # Sharpe分析結果
            sharpe_ratio = sharpe_analysis["sharpe"],
            hit_rate = sharpe_analysis["hit_rate"],
            max_drawdown = sharpe_analysis["max_dd"],
            # 穩定性分析結果
            decay_rate = stability_analysis["decay_rate"],
            stability_score = stability_analysis["stability_score"],
            turnover_rate = stability_analysis["turnover_rate"],
            # 統計檢驗結果
            t_stat = statistical_test["t_stat"],
            p_value = statistical_test["p_value"],
            confidence_interval = statistical_test["conf_interval"],
            # 元數據
            total_periods = len(aligned_data),
            valid_periods = len(factor_valid),
            validation_start = str(factor_valid.index.min().date()),
            validation_end = str(factor_valid.index.max().date()),
        )

        logger.info(f"Factor {factor_metrics.factor_name} validation completed")
        return result

    def _calculate_ic_analysis(
        self, factor_values: pd.Series, returns: pd.Series
    ) -> Dict[str, float]:
        """
        計算IC（Information Coefficient）分析

        Args:
            factor_values: 因子值
            returns: 收益率

        Returns:
            Dict[str, float]: IC分析結果
        """
        # 計算IC（相關係數）
        ic = factor_values.corr(returns)

        # 滾動IC計算
        rolling_ic = factor_values.rolling(window = 20).corr(returns)

        results = {
            "ic_mean": ic if not np.isnan(ic) else 0.0,
            "ic_std": rolling_ic.std() if len(rolling_ic.dropna()) > 0 else 0.0,
            "positive_rate": (
                (rolling_ic > 0).mean() if len(rolling_ic.dropna()) > 0 else 0.0
            ),
            "significance": 0.0,  # 將在統計檢驗中計算
        }

        # 計算IC信息比率
        if results["ic_std"] > 0:
            results["ic_ir"] = results["ic_mean"] / results["ic_std"]
        else:
            results["ic_ir"] = 0.0

        # 計算偏度和峰度
        if len(rolling_ic.dropna()) > 2:
            results["ic_skew"] = rolling_ic.skew()
            results["ic_kurtosis"] = rolling_ic.kurtosis()
        else:
            results["ic_skew"] = 0.0
            results["ic_kurtosis"] = 0.0

        return results

    def _calculate_factor_sharpe(
        self, factor_values: pd.Series, returns: pd.Series
    ) -> Dict[str, float]:
        """
        計算因子Sharpe比率相關指標

        Args:
            factor_values: 因子值
            returns: 收益率

        Returns:
            Dict[str, float]: Sharpe分析結果
        """
        # 根據因子值分組（五分位）
        factor_ranks = factor_values.rank(pct = True)

        # 計算多空組合收益
        top_quantile = factor_ranks >= 0.8
        bottom_quantile = factor_ranks <= 0.2

        # 計算每日多空收益序列
        daily_long_returns = returns[top_quantile]
        daily_short_returns = returns[bottom_quantile]
        daily_ls_returns = daily_long_returns - daily_short_returns

        # 過濾缺失值
        daily_ls_returns = daily_ls_returns.dropna()

        if len(daily_ls_returns) < 30:
            return {
                "sharpe": 0.0,
                "hit_rate": 0.0,
                "max_dd": 0.0,
                "annual_return": 0.0,
                "annual_vol": 0.0,
            }

        # 計算正確的年化收益率（基於複合收益率）
        total_period_return = (1 + daily_ls_returns).prod() - 1
        trading_days = len(daily_ls_returns)
        annual_return = (1 + total_period_return) ** (252 / trading_days) - 1

        # 計算年化波動率
        annual_vol = daily_ls_returns.std() * np.sqrt(252)

        # 計算正確的Sharpe比率（使用3%年化無風險利率）
        daily_rf_rate = self.risk_free_rate / 252
        excess_returns = daily_ls_returns - daily_rf_rate

        if annual_vol > 0 and len(excess_returns) > 0:
            # 使用正確的年化Sharpe計算
            sharpe = excess_returns.mean() / excess_returns.std() * np.sqrt(252)
        else:
            sharpe = 0.0

        # 計算勝率（多空組合）
        hit_rate = (daily_ls_returns > 0).mean()

        # 計算累積收益和最大回撤
        cumulative_returns = (1 + daily_ls_returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdowns = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdowns.min()

        return {
            "sharpe": sharpe,
            "hit_rate": hit_rate,
            "max_dd": max_drawdown,
            "annual_return": annual_return,
            "annual_vol": annual_vol,
            "total_period_return": total_period_return,
            "trading_days": trading_days,
        }

    def _calculate_stability_metrics(
        self, factor_values: pd.Series, returns: pd.Series
    ) -> Dict[str, float]:
        """
        計算因子穩定性指標

        Args:
            factor_values: 因子值
            returns: 收益率

        Returns:
            Dict[str, float]: 穩定性分析結果
        """
        # 計算因子衰減（不同持有期的IC衰減）
        decay_rates = []
        for holding_period in [1, 5, 10, 20]:
            shifted_returns = returns.shift(-holding_period)
            if len(shifted_returns.dropna()) > 10:
                ic_decay = factor_values.corr(shifted_returns)
                if not np.isnan(ic_decay):
                    decay_rates.append(ic_decay)

        # 計算衰減率
        if len(decay_rates) > 1:
            decay_rate = (
                (decay_rates[0] - decay_rates[-1]) / abs(decay_rates[0])
                if decay_rates[0] != 0
                else 0
            )
        else:
            decay_rate = 0.0

        # 計算穩定性評分
        rolling_ic = factor_values.rolling(window = 20).corr(returns)
        if len(rolling_ic.dropna()) > 10:
            stability_score = (
                1.0 - rolling_ic.std() / abs(rolling_ic.mean())
                if rolling_ic.mean() != 0
                else 0
            )
            stability_score = max(0, min(1, stability_score))  # 限制在0 - 1範圍
        else:
            stability_score = 0.0

        # 計算換手率
        factor_ranks = factor_values.rank(pct = True)
        top_quantile = factor_ranks >= 0.8

        # 計算選中股票的變化
        if len(top_quantile) > 1:
            selection_changes = top_quantile.astype(int).diff().abs().sum()
            turnover_rate = selection_changes / len(top_quantile)
        else:
            turnover_rate = 0.0

        return {
            "decay_rate": decay_rate,
            "stability_score": stability_score,
            "turnover_rate": turnover_rate,
        }

    def _perform_statistical_test(
        self, factor_values: pd.Series, returns: pd.Series
    ) -> Dict[str, Any]:
        """
        執行統計檢驗

        Args:
            factor_values: 因子值
            returns: 收益率

        Returns:
            Dict[str, Any]: 統計檢驗結果
        """
        # 計算相關係數和p值
        try:
            ic, p_value = stats.pearsonr(factor_values, returns)

            # 計算t統計量
            n = len(factor_values)
            if n > 2:
                t_stat = ic * np.sqrt((n - 2) / (1 - ic * *2)) if ic != 1 else 0
            else:
                t_stat = 0.0

            # 計算置信區間
            if n > 3:
                se = np.sqrt((1 - ic * *2) / (n - 2))
                t_critical = stats.t.ppf(1 - self.alpha / 2, n - 2)
                margin = t_critical * se
                conf_interval = (ic - margin, ic + margin)
            else:
                conf_interval = (0.0, 0.0)

        except Exception as e:
            logger.warning(f"Statistical test failed: {e}")
            ic = 0.0
            p_value = 1.0
            t_stat = 0.0
            conf_interval = (0.0, 0.0)

        return {
            "t_stat": t_stat,
            "p_value": p_value,
            "conf_interval": conf_interval,
            "correlation": ic,
        }

    def validate_multiple_factors(
        self,
        factor_metrics_dict: Dict[str, FactorMetrics],
        price_data: pd.DataFrame,
        returns_data: Optional[pd.Series] = None,
    ) -> Dict[str, FactorValidationResult]:
        """
        批量驗證多個因子

        Args:
            factor_metrics_dict: 因子指標字典
            price_data: 價格數據
            returns_data: 收益率數據

        Returns:
            Dict[str, FactorValidationResult]: 檢驗結果字典
        """
        results = {}

        for factor_name, factor_metrics in factor_metrics_dict.items():
            try:
                validation_result = self.validate_factor(
                    factor_metrics, price_data, returns_data
                )
                results[factor_name] = validation_result
                logger.debug(f"Validated factor: {factor_name}")

            except Exception as e:
                logger.error(f"Failed to validate factor {factor_name}: {e}")
                results[factor_name] = FactorValidationResult(factor_name = factor_name)

        logger.info(f"Validated {len(results)} factors")
        return results

    def generate_validation_report(
        self, validation_results: Dict[str, FactorValidationResult]
    ) -> pd.DataFrame:
        """
        生成因子檢驗報告

        Args:
            validation_results: 檢驗結果字典

        Returns:
            pd.DataFrame: 檢驗報告
        """
        report_data = []

        for factor_name, result in validation_results.items():
            # 計算綜合評分
            composite_score = self._calculate_composite_score(result)

            report_data.append(
                {
                    "factor_name": factor_name,
                    "ic_mean": result.ic_mean,
                    "ic_ir": result.ic_ir,
                    "ic_positive_rate": result.ic_positive_rate,
                    "sharpe_ratio": result.sharpe_ratio,
                    "hit_rate": result.hit_rate,
                    "max_drawdown": result.max_drawdown,
                    "stability_score": result.stability_score,
                    "p_value": result.p_value,
                    "valid_periods": result.valid_periods,
                    "composite_score": composite_score,
                }
            )

        report_df = pd.DataFrame(report_data)

        # 按綜合評分排序
        if not report_df.empty:
            report_df = report_df.sort_values("composite_score", ascending = False)

        return report_df

    def _calculate_composite_score(self, result: FactorValidationResult) -> float:
        """
        計算因子綜合評分

        Args:
            result: 檢驗結果

        Returns:
            float: 綜合評分 (0 - 100)
        """
        # 權重設置
        ic_weight = 0.3
        sharpe_weight = 0.25
        stability_weight = 0.2
        hit_rate_weight = 0.15
        significance_weight = 0.1

        # 標準化各項指標到0 - 100分
        ic_score = min(100, max(0, abs(result.ic_mean) * 1000))  # IC均值
        ir_score = min(100, max(0, abs(result.ic_ir) * 100))  # IR比率
        sharpe_score = min(100, max(0, abs(result.sharpe_ratio) * 25))  # Sharpe
        stability_score = result.stability_score * 100  # 穩定性
        hit_rate_score = result.hit_rate * 100  # 勝率
        significance_score = (1 - result.p_value) * 100  # 顯著性

        # IC相關綜合分
        ic_composite = (ic_score + ir_score) / 2

        # 計算最終評分
        final_score = (
            ic_composite * ic_weight
            + sharpe_score * sharpe_weight
            + stability_score * stability_weight
            + hit_rate_score * hit_rate_weight
            + significance_score * significance_weight
        )

        return round(final_score, 2)

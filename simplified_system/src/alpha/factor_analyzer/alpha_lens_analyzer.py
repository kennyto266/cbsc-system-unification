#!/usr / bin / env python3
"""
AlphaLens Analyzer
AlphaLens分析框架集成

提供專業級的Alpha因子分析功能，包括：
- Tear Sheet生成
- 分層因子分析
- 因子回測分析
- 機構級報告輸出
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

# 檢查AlphaLens可用性
try:
    import alphalens as al

    ALPHALENS_AVAILABLE = True
except ImportError:
    ALPHALENS_AVAILABLE = False
    logging.warning("AlphaLens not available, using built - in analysis")

logger = logging.getLogger(__name__)


@dataclass
class AlphaLensConfig:
    """AlphaLens分析配置"""

    quantiles: int = 5  # 分位數
    periods: List[int] = field(default_factory = lambda: [1, 5, 10, 20])  # 分析期數
    factor_name: str = "Alpha Factor"  # 因子名稱
    max_loss: float = 0.25  # 最大損失閾值
    grouping: Optional[str] = None  # 分組字段
    demeaned: bool = True  # 是否去均值
    groupby: Optional[str] = None  # 分組依據
    binning_by_group: bool = False  # 按組分箱


class AlphaLensAnalyzer:
    """
    AlphaLens分析器

    提供機構級的Alpha因子分析功能，支持完整的Tear Sheet生成。
    當AlphaLens不可用時，提供內置的分析功能。
    """

    def __init__(self, config: Optional[AlphaLensConfig] = None):
        """
        初始化AlphaLens分析器

        Args:
            config: 分析配置
        """
        self.config = config or AlphaLensConfig()
        self.alphalens_available = ALPHALENS_AVAILABLE

        if self.alphalens_available:
            logger.info("AlphaLens analyzer initialized with full functionality")
        else:
            logger.info("AlphaLens analyzer initialized with built - in functionality")

    def create_tear_sheet(
        self,
        factor_data: pd.DataFrame,
        pricing_data: pd.DataFrame,
        sector_data: Optional[pd.DataFrame] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        創建Alpha因子Tear Sheet

        Args:
            factor_data: 因子數據，格式為(date, asset) -> factor_value
            pricing_data: 價格數據，格式為(date, asset) -> price
            sector_data: 行業分類數據，格式為(asset) -> sector
            start_date: 開始日期
            end_date: 結束日期

        Returns:
            Dict[str, Any]: 分析結果
        """
        if self.alphalens_available:
            return self._create_alphalens_tear_sheet(
                factor_data, pricing_data, sector_data, start_date, end_date
            )
        else:
            return self._create_builtin_tear_sheet(
                factor_data, pricing_data, sector_data, start_date, end_date
            )

    def _create_alphalens_tear_sheet(
        self,
        factor_data: pd.DataFrame,
        pricing_data: pd.DataFrame,
        sector_data: Optional[pd.DataFrame] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """使用AlphaLens創建Tear Sheet"""
        try:
            # 準備數據
            factor_data_prepared = self._prepare_factor_data(
                factor_data, start_date, end_date
            )
            pricing_data_prepared = self._prepare_pricing_data(
                pricing_data, start_date, end_date
            )

            # 創建因子數據對象
            factor_data_al = al.utils.get_clean_factor_and_forward_returns(
                factor_data_prepared,
                pricing_data_prepared,
                quantiles = self.config.quantiles,
                periods = self.config.periods,
                max_loss = self.config.max_loss,
                groupby = sector_data,
                binning_by_group = self.config.binning_by_group,
            )

            # 生成Tear Sheet
            results = {}

            # 基本因子統計
            results["basic_stats"] = al.tears.create_factor_tear_sheet(
                factor_data_al,
                long_short = False,
                group_neutral = self.config.demeaned,
                by_group = bool(sector_data is not None),
            )

            # 收益率分析
            results["returns_analysis"] = al.tears.create_returns_tear_sheet(
                factor_data_al,
                long_short = False,
                group_neutral = self.config.demeaned,
                by_group = bool(sector_data is not None),
            )

            # 信息係數分析
            results["ic_analysis"] = al.tears.create_information_tear_sheet(
                factor_data_al,
                group_neutral = self.config.demeaned,
                by_group = bool(sector_data is not None),
            )

            # 換手率分析
            results["turnover_analysis"] = al.tears.create_turnover_tear_sheet(
                factor_data_al,
                group_neutral = self.config.demeaned,
                by_group = bool(sector_data is not None),
            )

            if sector_data is not None:
                # 行業分析
                results["sector_analysis"] = al.tears.create_group_returns_tear_sheet(
                    factor_data_al
                )

            logger.info("AlphaLens tear sheet created successfully")
            return results

        except Exception as e:
            logger.error(f"AlphaLens tear sheet creation failed: {e}")
            # 降級到內置分析
            return self._create_builtin_tear_sheet(
                factor_data, pricing_data, sector_data, start_date, end_date
            )

    def _create_builtin_tear_sheet(
        self,
        factor_data: pd.DataFrame,
        pricing_data: pd.DataFrame,
        sector_data: Optional[pd.DataFrame] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """使用內置功能創建Tear Sheet"""
        logger.info("Creating built - in tear sheet analysis")

        results = {}

        try:
            # 準備數據
            factor_clean = self._prepare_factor_data(factor_data, start_date, end_date)
            pricing_clean = self._prepare_pricing_data(
                pricing_data, start_date, end_date
            )

            # 基本統計分析
            results["basic_stats"] = self._analyze_basic_stats(factor_clean)

            # 收益率分析
            results["returns_analysis"] = self._analyze_returns(
                factor_clean, pricing_clean
            )

            # IC分析
            results["ic_analysis"] = self._analyze_information_coefficient(
                factor_clean, pricing_clean
            )

            # 換手率分析
            results["turnover_analysis"] = self._analyze_turnover(factor_clean)

            if sector_data is not None:
                results["sector_analysis"] = self._analyze_by_sector(
                    factor_clean, sector_data
                )

            logger.info("Built - in tear sheet analysis completed")
            return results

        except Exception as e:
            logger.error(f"Built - in tear sheet creation failed: {e}")
            return {"error": str(e)}

    def _prepare_factor_data(
        self,
        factor_data: pd.DataFrame,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """準備因子數據"""
        # 應用日期過濾
        if start_date:
            factor_data = factor_data[factor_data.index >= start_date]
        if end_date:
            factor_data = factor_data[factor_data.index <= end_date]

        # 確保數據格式正確
        if isinstance(factor_data.index, pd.MultiIndex):
            # 已經是正確格式
            return factor_data
        else:
            # 需要轉換為multi - index格式
            # 假設columns是assets，index是dates
            return factor_data.stack().rename("factor").to_frame()

    def _prepare_pricing_data(
        self,
        pricing_data: pd.DataFrame,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """準備價格數據"""
        # 應用日期過濾
        if start_date:
            pricing_data = pricing_data[pricing_data.index >= start_date]
        if end_date:
            pricing_data = pricing_data[pricing_data.index <= end_date]

        # 確保數據格式正確
        if isinstance(pricing_data.index, pd.MultiIndex):
            # 已經是正確格式
            return pricing_data
        else:
            # 需要轉換為multi - index格式
            return pricing_data.stack().rename("price").to_frame()

    def _analyze_basic_stats(self, factor_data: pd.DataFrame) -> Dict[str, Any]:
        """分析基本統計信息"""
        factor_values = factor_data["factor"].dropna()

        return {
            "count": len(factor_values),
            "mean": factor_values.mean(),
            "std": factor_values.std(),
            "min": factor_values.min(),
            "max": factor_values.max(),
            "skewness": factor_values.skew(),
            "kurtosis": factor_values.kurtosis(),
            "missing_ratio": factor_data["factor"].isna().mean(),
            "unique_values": factor_values.nunique(),
        }

    def _analyze_returns(
        self, factor_data: pd.DataFrame, pricing_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """分析收益率"""
        try:
            # 計算收益率
            returns = pricing_data["price"].unstack().pct_change()

            # 對齊因子和收益率數據
            aligned_data = pd.concat(
                [factor_data["factor"].unstack(), returns], axis = 1, join="inner"
            )

            if len(aligned_data) < 2:
                return {"error": "Insufficient data for returns analysis"}

            factor_aligned = aligned_data.iloc[:, 0]
            returns_aligned = aligned_data.iloc[:, 1:]

            # 按因子值分組
            factor_aligned_clean = factor_aligned.dropna()
            returns_aligned_clean = returns_aligned.loc[factor_aligned_clean.index]

            # 分位數分組
            quantiles = factor_aligned_clean.rank(pct = True)
            quantile_groups = pd.cut(
                quantiles, bins = self.config.quantiles, labels = False
            )

            # 計算分組收益率
            group_returns = []
            for q in range(self.config.quantiles):
                mask = quantile_groups == q
                if mask.any():
                    group_return = returns_aligned_clean[mask].mean()
                    group_returns.append(group_return)
                else:
                    group_returns.append(0.0)

            # 計算多空組合收益率
            if len(group_returns) >= 2:
                long_short_return = group_returns[-1] - group_returns[0]
                long_short_sharpe = (
                    long_short_return / returns_aligned_clean.std()
                    if returns_aligned_clean.std() > 0
                    else 0
                )
            else:
                long_short_return = 0.0
                long_short_sharpe = 0.0

            return {
                "quantile_returns": group_returns,
                "long_short_return": long_short_return,
                "long_short_sharpe": long_short_sharpe,
                "annualized_return": long_short_return * 252,
                "annualized_volatility": returns_aligned_clean.std() * np.sqrt(252),
            }

        except Exception as e:
            logger.error(f"Returns analysis failed: {e}")
            return {"error": str(e)}

    def _analyze_information_coefficient(
        self, factor_data: pd.DataFrame, pricing_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """分析信息係數"""
        try:
            # 計算收益率
            returns = pricing_data["price"].unstack().pct_change()

            # 對齊數據
            aligned_data = pd.concat(
                [factor_data["factor"].unstack(), returns], axis = 1, join="inner"
            )

            if len(aligned_data) < 10:
                return {"error": "Insufficient data for IC analysis"}

            factor_aligned = aligned_data.iloc[:, 0]
            returns_aligned = aligned_data.iloc[:, 1:]

            # 計算IC
            ic_series = []
            for date in factor_aligned.index:
                if date in returns_aligned.index:
                    factor_vals = factor_aligned.loc[date].dropna()
                    return_vals = (
                        returns_aligned.loc[date].reindex(factor_vals.index).dropna()
                    )

                    if len(factor_vals) > 5 and len(return_vals) > 5:
                        common_idx = factor_vals.index.intersection(return_vals.index)
                        if len(common_idx) > 5:
                            ic = factor_vals.loc[common_idx].corr(
                                return_vals.loc[common_idx]
                            )
                            if not np.isnan(ic):
                                ic_series.append(ic)

            if ic_series:
                ic_array = np.array(ic_series)
                return {
                    "ic_mean": np.mean(ic_array),
                    "ic_std": np.std(ic_array),
                    "ic_ir": (
                        np.mean(ic_array) / np.std(ic_array)
                        if np.std(ic_array) > 0
                        else 0
                    ),
                    "ic_positive_rate": np.mean(ic_array > 0),
                    "ic_skewness": pd.Series(ic_array).skew(),
                    "ic_kurtosis": pd.Series(ic_array).kurtosis(),
                    "ic_count": len(ic_array),
                }
            else:
                return {"error": "No valid IC calculations"}

        except Exception as e:
            logger.error(f"IC analysis failed: {e}")
            return {"error": str(e)}

    def _analyze_turnover(self, factor_data: pd.DataFrame) -> Dict[str, Any]:
        """分析換手率"""
        try:
            # 重塑數據為dates x assets格式
            factor_matrix = factor_data["factor"].unstack()

            # 計算因子排名
            factor_ranks = factor_matrix.rank(pct = True, axis = 1)

            # 計算換手率
            turnover_rates = []
            for i in range(1, len(factor_ranks)):
                prev_ranks = factor_ranks.iloc[i - 1]
                curr_ranks = factor_ranks.iloc[i]

                # 找到共同的資產
                common_assets = prev_ranks.index.intersection(curr_ranks.index)
                if len(common_assets) > 0:
                    prev_common = prev_ranks.loc[common_assets]
                    curr_common = curr_ranks.loc[common_assets]

                    # 計算排名變化
                    rank_change = np.abs(curr_common - prev_common).sum() / len(
                        common_assets
                    )
                    turnover_rates.append(rank_change)

            if turnover_rates:
                return {
                    "average_turnover": np.mean(turnover_rates),
                    "turnover_std": np.std(turnover_rates),
                    "max_turnover": np.max(turnover_rates),
                    "min_turnover": np.min(turnover_rates),
                }
            else:
                return {"error": "Insufficient data for turnover analysis"}

        except Exception as e:
            logger.error(f"Turnover analysis failed: {e}")
            return {"error": str(e)}

    def _analyze_by_sector(
        self, factor_data: pd.DataFrame, sector_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """按行業分析因子"""
        try:
            # 獲取因子數據
            factor_matrix = factor_data["factor"].unstack()

            sector_results = {}

            for sector in sector_data.unique():
                if pd.isna(sector):
                    continue

                # 獲取該行業的資產
                sector_assets = sector_data[sector_data == sector].index
                sector_factor_data = factor_matrix[
                    sector_assets.intersection(factor_matrix.columns)
                ]

                if len(sector_factor_data.columns) > 0:
                    sector_mean = sector_factor_data.mean(axis = 1).mean()
                    sector_std = sector_factor_data.std(axis = 1).mean()

                    sector_results[sector] = {
                        "mean": sector_mean,
                        "std": sector_std,
                        "asset_count": len(sector_factor_data.columns),
                        "data_points": len(sector_factor_data),
                    }

            return {
                "sector_analysis": sector_results,
                "sector_count": len(sector_results),
            }

        except Exception as e:
            logger.error(f"Sector analysis failed: {e}")
            return {"error": str(e)}

    def stratified_analysis(
        self,
        factor_data: pd.DataFrame,
        pricing_data: pd.DataFrame,
        group_by: str,
        group_data: pd.DataFrame,
    ) -> Dict[str, Any]:
        """
        分層因子分析

        Args:
            factor_data: 因子數據
            pricing_data: 價格數據
            group_by: 分組依據 ('sector', 'market_cap', etc.)
            group_data: 分組數據

        Returns:
            Dict[str, Any]: 分層分析結果
        """
        logger.info(f"Performing stratified analysis by {group_by}")

        if group_by == "sector":
            return self._analyze_by_sector(factor_data, group_data)
        else:
            # 通用分層分析
            return self._create_stratified_analysis(
                factor_data, pricing_data, group_by, group_data
            )

    def _create_stratified_analysis(
        self,
        factor_data: pd.DataFrame,
        pricing_data: pd.DataFrame,
        group_by: str,
        group_data: pd.DataFrame,
    ) -> Dict[str, Any]:
        """創建通用分層分析"""
        try:
            # 基本分組統計
            factor_matrix = factor_data["factor"].unstack()
            group_results = {}

            for group in group_data.unique():
                if pd.isna(group):
                    continue

                group_assets = group_data[group_data == group].index
                group_factor_data = factor_matrix[
                    group_assets.intersection(factor_matrix.columns)
                ]

                if len(group_factor_data.columns) > 0:
                    # 計算該組的基本統計
                    group_stats = {
                        "factor_mean": group_factor_data.mean(axis = 1).mean(),
                        "factor_std": group_factor_data.std(axis = 1).mean(),
                        "asset_count": len(group_factor_data.columns),
                    }

                    # 計算該組的IC
                    try:
                        returns = pricing_data["price"].unstack().pct_change()
                        aligned_returns = returns[group_factor_data.columns]

                        ic_values = []
                        for date in group_factor_data.index:
                            if date in aligned_returns.index:
                                factor_vals = group_factor_data.loc[date].dropna()
                                return_vals = (
                                    aligned_returns.loc[date]
                                    .reindex(factor_vals.index)
                                    .dropna()
                                )

                                if len(factor_vals) > 3:
                                    ic = factor_vals.corr(return_vals)
                                    if not np.isnan(ic):
                                        ic_values.append(ic)

                        if ic_values:
                            group_stats["ic_mean"] = np.mean(ic_values)
                            group_stats["ic_positive_rate"] = np.mean(
                                np.array(ic_values) > 0
                            )

                    except Exception:
                        group_stats["ic_mean"] = 0.0
                        group_stats["ic_positive_rate"] = 0.0

                    group_results[group] = group_stats

            return {
                "stratified_analysis": group_results,
                "group_count": len(group_results),
                "group_by": group_by,
            }

        except Exception as e:
            logger.error(f"Stratified analysis failed: {e}")
            return {"error": str(e)}

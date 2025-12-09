#!/usr / bin / env python3
"""
Simplified System - Walk - Forward優化引擎
基於Python Algorithmic Trading Cookbook的高級Walk - Forward優化技術

Walk - Forward優化是一種防止過擬合的高級技術，通過將數據分割為
In - Sample和Out - of - Sample窗口，在真實市場條件下測試策略的穩健性。
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import scipy.stats as stats

try:
    import vectorbt as vbt

    VECTORBT_AVAILABLE = True
except ImportError:
    VECTORBT_AVAILABLE = False
    logging.warning("VectorBT not available. Install with: pip install vectorbt")
    vbt = None

logger = logging.getLogger(__name__)


@dataclass
class WalkForwardConfig:
    """Walk - Forward優化配置"""

    # 窗口配置
    window_len: int = 252 * 2  # 2年窗口
    n_splits: int = 30  # 分割數量
    set_lens: Tuple[int] = (180,)  # Out - of - Sample長度

    # 優化配置
    param_ranges: Dict[str, List] = field(default_factory = dict)
    objective: str = "sharpe_ratio"  # 優化目標
    direction: str = "both"  # 交易方向

    # 回測配置
    fees: float = 0.001  # 0.1%手續費
    slippage: float = 0.0005  # 0.05%滑點
    freq: str = "d"  # 頻率


@dataclass
class WalkForwardResult:
    """Walk - Forward優化結果"""

    # 優化結果
    best_params: Dict[str, Any] = field(default_factory = dict)
    in_sample_performance: pd.Series = field(default_factory = pd.Series)
    out_sample_performance: pd.Series = field(default_factory = pd.Series)

    # 統計結果
    sharpe_improvement: float = 0.0
    stability_score: float = 0.0
    t_statistic: float = 0.0
    p_value: float = 1.0

    # 元數據
    optimization_time: float = 0.0
    total_splits: int = 0
    successful_splits: int = 0


class WalkForwardOptimizer:
    """
    Walk - Forward優化引擎

    基於Python Algorithmic Trading Cookbook的實現，提供：
    - 自動時間窗口分割
    - In - Sample參數優化
    - Out - of - Sample策略測試
    - 統計分析和穩定性評估
    """

    def __init__(
        self,
        data: pd.Series,
        strategy_func: callable,
        config: Optional[WalkForwardConfig] = None,
    ):
        """
        初始化Walk - Forward優化器

        Args:
            data: 價格數據 (pd.Series)
            strategy_func: 策略函數，接受(data, params)返回投資組合
            config: Walk - Forward配置
        """
        if not VECTORBT_AVAILABLE:
            raise ImportError("VectorBT is required for WalkForward optimization")

        self.data = data
        self.strategy_func = strategy_func
        self.config = config or WalkForwardConfig()

        # 驗證數據
        self._validate_data()

        logger.info(f"初始化Walk - Forward優化器，數據長度: {len(data)}")

    def _validate_data(self):
        """驗證輸入數據"""
        if not isinstance(self.data, pd.Series):
            raise ValueError("數據必須是pd.Series格式")

        if len(self.data) < self.config.window_len:
            raise ValueError(
                f"數據長度 {len(self.data)} 小於窗口長度 {self.config.window_len}"
            )

    def optimize(self) -> WalkForwardResult:
        """
        執行Walk - Forward優化

        Returns:
            WalkForwardResult: 優化結果
        """
        start_time = datetime.now()
        logger.info("開始Walk - Forward優化")

        # 步驟1: 分割數據
        in_data, out_data = self._split_data()

        # 步驟2: In - Sample參數優化
        in_performance = self._optimize_in_sample(in_data)

        # 步驟3: 獲取最佳參數
        best_params = self._extract_best_params(in_performance)

        # 步驟4: Out - of - Sample測試
        out_performance = self._test_out_sample(out_data, best_params)

        # 步驟5: 統計分析
        stats_result = self._perform_statistical_analysis(
            in_performance, out_performance
        )

        # 步驟6: 計算穩定性評分
        stability_score = self._calculate_stability_score(
            in_performance, out_performance
        )

        optimization_time = (datetime.now() - start_time).total_seconds()

        result = WalkForwardResult(
            best_params = best_params,
            in_sample_performance = in_performance,
            out_sample_performance = out_performance,
            stability_score = stability_score,
            optimization_time = optimization_time,
            total_splits = len(in_performance),
            successful_splits = len(out_performance.dropna()),
            **stats_result,
        )

        logger.info(f"Walk - Forward優化完成，耗時: {optimization_time:.2f}秒")
        return result

    def _split_data(self) -> Tuple[pd.Series, pd.Series]:
        """
        分割數據為In - Sample和Out - of - Sample

        Returns:
            Tuple[pd.Series, pd.Series]: (in_data, out_data)
        """
        logger.info(f"分割數據為 {self.config.n_splits} 個窗口")

        (in_price, in_indexes), (out_price, out_indexes) = self.data.vbt.rolling_split(
            n = self.config.n_splits,
            window_len = self.config.window_len,
            set_lens = self.config.set_lens,
            left_to_right = False,
        )

        logger.info(
            f"創建了 {len(in_indexes)} 個In - Sample窗口，{len(out_indexes)} 個Out - of - Sample窗口"
        )

        return (in_price, in_indexes), (out_price, out_indexes)

    def _optimize_in_sample(
        self, in_data: Tuple[pd.Series, pd.MultiIndex]
    ) -> pd.Series:
        """
        In - Sample參數優化

        Args:
            in_data: In - Sample數據

        Returns:
            pd.Series: In - Sample績效指標
        """
        in_price, in_indexes = in_data

        if not self.config.param_ranges:
            # 如果沒有指定參數範圍，使用默認RSI參數
            self.config.param_ranges = {
                "rsi_period": [10, 14, 20, 30],
                "oversold": [20, 25, 30],
                "overbought": [70, 75, 80],
            }

        logger.info(f"In - Sample優化，參數範圍: {self.config.param_ranges}")

        # 使用VectorBT進行參數優化
        param_names = list(self.config.param_ranges.keys())
        param_values = list(self.config.param_ranges.values())

        # 生成所有參數組合
        import itertools

        param_combinations = list(itertools.product(*param_values))

        # 計算每個參數組合的績效
        performances = []

        for i, params in enumerate(param_combinations):
            param_dict = dict(zip(param_names, params))

            try:
                # 調用策略函數
                pf = self.strategy_func(in_price, **param_dict)

                # 獲取績效指標
                if self.config.objective == "sharpe_ratio":
                    perf = pf.sharpe_ratio()
                elif self.config.objective == "total_return":
                    perf = pf.total_return()
                elif self.config.objective == "sortino_ratio":
                    perf = pf.sortino_ratio()
                else:
                    perf = pf.sharpe_ratio()  # 默認使用Sharpe比率

                performances.append(perf)

            except Exception as e:
                logger.warning(f"參數組合 {param_dict} 計算失敗: {e}")
                performances.append(np.nan)

        # 轉換為多索引Series
        index = pd.MultiIndex.from_tuples(param_combinations, names = param_names)
        performance_series = pd.Series(performances, index = index)

        logger.info(f"In - Sample優化完成，測試了 {len(param_combinations)} 個參數組合")

        return performance_series

    def _extract_best_params(self, performance: pd.Series) -> Dict[str, Any]:
        """
        從In - Sample性能中提取最佳參數

        Args:
            performance: In - Sample性能結果

        Returns:
            Dict[str, Any]: 最佳參數
        """
        # 獲取每個分割窗口的最佳參數
        if not performance.empty:
            try:
                best_idx = performance.groupby("split_idx").idxmax()
                best_params = {}

                for split_idx, param_idx in best_idx.items():
                    if isinstance(param_idx, tuple):
                        param_dict = dict(zip(performance.index.names, param_idx))
                        best_params[split_idx] = param_dict

                logger.info(f"提取了 {len(best_params)} 個最佳參數組合")
                return best_params

            except Exception as e:
                logger.warning(f"提取最佳參數失敗: {e}")

        # 返回默認參數
        return {0: {"rsi_period": 14, "oversold": 30, "overbought": 70}}

    def _test_out_sample(
        self, out_data: Tuple[pd.Series, pd.MultiIndex], best_params: Dict[str, Any]
    ) -> pd.Series:
        """
        Out - of - Sample策略測試

        Args:
            out_data: Out - of - Sample數據
            best_params: 最佳參數

        Returns:
            pd.Series: Out - of - Sample性能結果
        """
        out_price, out_indexes = out_data

        out_performance = []

        for split_idx in out_indexes.get_level_values("split_idx").unique():
            if split_idx in best_params:
                try:
                    # 獲取對應的Out - of - Sample數據
                    split_data = out_price.xs(split_idx, level="split_idx")

                    # 使用最佳參數
                    params = best_params[split_idx]
                    pf = self.strategy_func(split_data, **params)

                    # 計算性能
                    if self.config.objective == "sharpe_ratio":
                        perf = pf.sharpe_ratio()
                    elif self.config.objective == "total_return":
                        perf = pf.total_return()
                    else:
                        perf = pf.sharpe_ratio()

                    out_performance.append(perf)

                except Exception as e:
                    logger.warning(f"Out - of - Sample測試失敗 (split {split_idx}): {e}")
                    out_performance.append(np.nan)
            else:
                out_performance.append(np.nan)

        # 創建索引
        split_indices = out_indexes.get_level_values("split_idx").unique()
        out_series = pd.Series(out_performance, index = split_indices)

        logger.info(f"Out - of - Sample測試完成，成功測試 {len(out_performance)} 個窗口")

        return out_series

    def _perform_statistical_analysis(
        self, in_performance: pd.Series, out_performance: pd.Series
    ) -> Dict[str, float]:
        """
        執行統計分析

        Args:
            in_performance: In - Sample性能
            out_performance: Out - of - Sample性能

        Returns:
            Dict[str, float]: 統計結果
        """
        try:
            # 獲取最佳In - Sample性能
            best_idx = in_performance.groupby("split_idx").idxmax()
            in_best = in_performance[best_idx.values].dropna()

            # 獲取對應的Out - of - Sample性能
            out_test = out_performance.dropna()

            # 計算平均值
            in_mean = in_best.mean()
            out_mean = out_test.mean()

            # 計算改善程度
            sharpe_improvement = (
                out_mean - in_mean
                if not np.isnan(out_mean) and not np.isnan(in_mean)
                else 0.0
            )

            # 執行t檢驗
            if len(in_best) > 1 and len(out_test) > 1:
                t_stat, p_value = stats.ttest_ind(
                    a = out_test.values, b = in_best.values, alternative="greater"
                )
            else:
                t_stat = 0.0
                p_value = 1.0

            return {
                "sharpe_improvement": sharpe_improvement,
                "t_statistic": t_stat,
                "p_value": p_value,
            }

        except Exception as e:
            logger.warning(f"統計分析失敗: {e}")
            return {"sharpe_improvement": 0.0, "t_statistic": 0.0, "p_value": 1.0}

    def _calculate_stability_score(
        self, in_performance: pd.Series, out_performance: pd.Series
    ) -> float:
        """
        計算穩定性評分

        Args:
            in_performance: In - Sample性能
            out_performance: Out - of - Sample性能

        Returns:
            float: 穩定性評分 (0 - 100)
        """
        try:
            # 獲取有效數據
            out_valid = out_performance.dropna()

            if len(out_valid) == 0:
                return 0.0

            # 計算基本統計量
            mean_performance = out_valid.mean()
            std_performance = out_valid.std()

            # 計算勝率（正值比例）
            win_rate = (out_valid > 0).mean()

            # 計算穩定性評分
            # 基於：平均性能 + 勝率 - 波動率懲罰
            stability_score = (
                mean_performance * 50  # 平均性能權重
                + win_rate * 30  # 勝率權重
                + max(0, 20 - std_performance * 10)  # 穩定性權重
            )

            return max(0, min(100, stability_score))

        except Exception as e:
            logger.warning(f"穩定性評分計算失敗: {e}")
            return 0.0

    def generate_report(self, result: WalkForwardResult) -> str:
        """
        生成優化報告

        Args:
            result: Walk - Forward優化結果

        Returns:
            str: 優化報告
        """
        report = f"""
# Walk - Forward優化報告

## 優化配置
- 窗口長度: {self.config.window_len}
- 分割數量: {self.config.n_splits}
- Out - of - Sample長度: {self.config.set_lens[0]}
- 優化目標: {self.config.objective}

## 優化結果
- 總分割數: {result.total_splits}
- 成功分割數: {result.successful_splits}
- 優化耗時: {result.optimization_time:.2f}秒

## 性能指標
- Sharpe改善: {result.sharpe_improvement:.4f}
- 穩定性評分: {result.stability_score:.2f}/100
- t統計量: {result.t_statistic:.4f}
- p值: {result.p_value:.4f}

## 最佳參數
"""

        for split_idx, params in result.best_params.items():
            report += f"### 分割 {split_idx}:\n"
            for param, value in params.items():
                report += f"- {param}: {value}\n"
            report += "\n"

        return report

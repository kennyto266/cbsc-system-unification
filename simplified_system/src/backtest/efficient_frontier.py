#!/usr / bin / env python3
"""
Efficient Frontier Calculator
有效邊界計算器

Professional implementation of efficient frontier calculation and analysis
專業有效邊界計算和分析實現

Features:
- Efficient frontier calculation
- Capital Market Line (CML) calculation
- Multiple optimal portfolios identification
- Risk - return tradeoff analysis
- Efficient frontier visualization
- Portfolio performance metrics
"""

import logging
import time
import warnings
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

try:
    import matplotlib.pyplot as plt
    import seaborn as sns

    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False
    logging.warning(
        "Matplotlib not available. Install with: pip install matplotlib seaborn"
    )

from .mpt_optimizer import MPTConfig, MPTOptimizer, OptimizationResult

logger = logging.getLogger(__name__)


@dataclass
class EfficientFrontierConfig:
    """有效邊界配置"""

    # 計算參數
    num_portfolios: int = 200  # 投資組合數量
    target_return_range: Optional[Tuple[float, float]] = None  # 目標回報範圍

    # 視覺化參數
    figsize: Tuple[int, int] = (12, 8)
    style: str = "seaborn - v0_8"
    color_palette: str = "viridis"

    # 基準設定
    benchmark_weights: Optional[np.ndarray] = None  # 基準投資組合權重
    benchmark_name: str = "Benchmark"

    # 顯示選項
    show_optimal_portfolios: bool = True  # 顯示最優投資組合
    show_individual_assets: bool = True  # 顯示個別資產
    show_cml: bool = True  # 顯示資本市場線


@dataclass
class EfficientFrontierResult:
    """有效邊界結果"""

    # 有效邊界數據
    portfolios: pd.DataFrame  # 所有可能投資組合
    efficient_portfolios: pd.DataFrame  # 有效邊界投資組合

    # 最優投資組合
    max_sharpe_portfolio: OptimizationResult
    min_volatility_portfolio: OptimizationResult

    # 個別資產點
    asset_returns: np.ndarray
    asset_volatilities: np.ndarray
    asset_names: List[str]

    # 風險免利率和市場投資組合
    risk_free_rate: float

    # 統計信息
    total_portfolios: int
    efficient_portfolios_count: int
    calculation_time: float
    timestamp: str

    # 資本市場線 (可選)
    cml_slope: Optional[float] = None
    cml_intercept: Optional[float] = None
    market_portfolio: Optional[OptimizationResult] = None

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "efficient_frontier": {
                "total_portfolios": self.total_portfolios,
                "efficient_portfolios_count": self.efficient_portfolios_count,
                "min_volatility": {
                    "return": round(
                        self.min_volatility_portfolio.expected_return * 100, 2
                    ),
                    "volatility": round(
                        self.min_volatility_portfolio.volatility * 100, 2
                    ),
                    "sharpe": round(self.min_volatility_portfolio.sharpe_ratio, 3),
                },
                "max_sharpe": {
                    "return": round(self.max_sharpe_portfolio.expected_return * 100, 2),
                    "volatility": round(self.max_sharpe_portfolio.volatility * 100, 2),
                    "sharpe": round(self.max_sharpe_portfolio.sharpe_ratio, 3),
                },
            },
            "capital_market_line": {
                "slope": round(self.cml_slope, 4) if self.cml_slope else None,
                "intercept": (
                    round(self.cml_intercept, 4) if self.cml_intercept else None
                ),
                "risk_free_rate": round(self.risk_free_rate * 100, 2),
            },
            "asset_characteristics": {
                asset: {
                    "return": round(ret * 100, 2),
                    "volatility": round(vol * 100, 2),
                }
                for asset, ret, vol in zip(
                    self.asset_names, self.asset_returns, self.asset_volatilities
                )
            },
            "metadata": {
                "calculation_time": round(self.calculation_time, 3),
                "timestamp": self.timestamp,
            },
        }


class EfficientFrontierCalculator:
    """
    有效邊界計算器

    Professional efficient frontier calculation with advanced features:
    - Monte Carlo simulation of portfolio combinations
    - Efficient frontier identification
    - Capital Market Line calculation
    - Multiple optimal portfolios identification
    - Comprehensive visualization
    """

    def __init__(
        self,
        mpt_config: Optional[MPTConfig] = None,
        ef_config: Optional[EfficientFrontierConfig] = None,
    ):
        """初始化有效邊界計算器"""
        self.mpt_config = mpt_config or MPTConfig()
        self.ef_config = ef_config or EfficientFrontierConfig()
        self.optimizer = MPTOptimizer(self.mpt_config)

        logger.info("Efficient Frontier Calculator initialized")

    def calculate_efficient_frontier(
        self, returns: pd.DataFrame, risk_free_rate: Optional[float] = None
    ) -> EfficientFrontierResult:
        """
        計算有效邊界

        Args:
            returns: 資產回報率矩陣 (time x assets)
            risk_free_rate: 無風險利率 (覆蓋MPT配置)

        Returns:
            EfficientFrontierResult: 有效邊界結果
        """
        start_time = time.time()

        try:
            logger.info(
                f"Starting efficient frontier calculation for {returns.shape[1]} assets"
            )

            # 更新無風險利率
            if risk_free_rate is not None:
                self.optimizer.config.risk_free_rate = risk_free_rate
                self.mpt_config.risk_free_rate = risk_free_rate

            # 準備數據
            mean_returns, cov_matrix = self._prepare_data(returns)
            num_assets = len(mean_returns)

            # 計算個別資產特性
            asset_volatilities = np.sqrt(np.diag(cov_matrix))
            asset_returns = mean_returns

            # 生成隨機投資組合
            portfolios_df = self._generate_random_portfolios(
                mean_returns, cov_matrix, num_assets
            )

            # 計算最優投資組合
            max_sharpe_portfolio = self.optimizer.maximize_sharpe_ratio(returns)
            min_volatility_portfolio = self.optimizer.minimize_volatility(returns)

            # 識別有效邊界
            efficient_portfolios_df = self._identify_efficient_frontier(portfolios_df)

            # 計算資本市場線
            cml_slope, cml_intercept = self._calculate_capital_market_line(
                efficient_portfolios_df, max_sharpe_portfolio
            )

            # 創建結果
            result = EfficientFrontierResult(
                portfolios = portfolios_df,
                efficient_portfolios = efficient_portfolios_df,
                max_sharpe_portfolio = max_sharpe_portfolio,
                min_volatility_portfolio = min_volatility_portfolio,
                asset_returns = asset_returns,
                asset_volatilities = asset_volatilities,
                asset_names = list(returns.columns),
                cml_slope = cml_slope,
                cml_intercept = cml_intercept,
                risk_free_rate = self.mpt_config.risk_free_rate,
                market_portfolio = max_sharpe_portfolio,  # 最大夏普比率投資組合即為市場投資組合
                total_portfolios = len(portfolios_df),
                efficient_portfolios_count = len(efficient_portfolios_df),
                calculation_time = time.time() - start_time,
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )

            logger.info(
                f"Efficient frontier calculation completed in {result.calculation_time:.3f}s"
            )
            return result

        except Exception as e:
            logger.error(f"Efficient frontier calculation failed: {e}")
            raise

    def calculate_target_risk_portfolios(
        self,
        returns: pd.DataFrame,
        target_volatilities: np.ndarray,
        risk_free_rate: Optional[float] = None,
    ) -> List[OptimizationResult]:
        """
        計算目標波動率投資組合

        Args:
            returns: 資產回報率矩陣
            target_volatilities: 目標波動率數組
            risk_free_rate: 無風險利率

        Returns:
            List[OptimizationResult]: 目標波動率投資組合列表
        """
        start_time = time.time()

        try:
            logger.info(
                f"Calculating {len(target_volatilities)} target volatility portfolios"
            )

            # 更新無風險利率
            if risk_free_rate is not None:
                self.optimizer.config.risk_free_rate = risk_free_rate

            target_portfolios = []
            mean_returns, cov_matrix = self._prepare_data(returns)
            num_assets = len(mean_returns)

            for target_vol in target_volatilities:
                # 計算在目標波動率下的最優投資組合
                portfolio_result = self._optimize_for_target_volatility(
                    mean_returns,
                    cov_matrix,
                    target_vol,
                    num_assets,
                    list(returns.columns),
                )
                target_portfolios.append(portfolio_result)

            logger.info(
                f"Target volatility portfolios calculated in {time.time() - start_time:.3f}s"
            )
            return target_portfolios

        except Exception as e:
            logger.error(f"Target volatility optimization failed: {e}")
            raise

    def plot_efficient_frontier(
        self,
        ef_result: EfficientFrontierResult,
        save_path: Optional[str] = None,
        show_plot: bool = True,
    ) -> None:
        """
        繪製有效邊界圖

        Args:
            ef_result: 有效邊界結果
            save_path: 保存路徑 (可選)
            show_plot: 是否顯示圖表
        """
        if not PLOTTING_AVAILABLE:
            logger.warning("Plotting not available. Install matplotlib and seaborn.")
            return

        try:
            # 設置圖表風格
            plt.style.use(self.ef_config.style)
            plt.figure(figsize = self.ef_config.figsize)

            # 繪製所有投資組合
            scatter = plt.scatter(
                ef_result.portfolios["Volatility"],
                ef_result.portfolios["Return"],
                c = ef_result.portfolios["Sharpe"],
                cmap = self.ef_config.color_palette,
                alpha = 0.6,
                s = 20,
                label="All Portfolios",
            )

            # 繪製有效邊界
            if len(ef_result.efficient_portfolios) > 0:
                plt.plot(
                    ef_result.efficient_portfolios["Volatility"],
                    ef_result.efficient_portfolios["Return"],
                    "r - -",
                    linewidth = 2,
                    label="Efficient Frontier",
                )

            # 繪製最優投資組合
            if self.ef_config.show_optimal_portfolios:
                # 最大夏普比率投資組合
                plt.scatter(
                    ef_result.max_sharpe_portfolio.volatility,
                    ef_result.max_sharpe_portfolio.expected_return,
                    marker="*",
                    color="gold",
                    s = 300,
                    edgecolors="black",
                    linewidth = 2,
                    label = f"Max Sharpe ({ef_result.max_sharpe_portfolio.sharpe_ratio:.3f})",
                )

                # 最小波動率投資組合
                plt.scatter(
                    ef_result.min_volatility_portfolio.volatility,
                    ef_result.min_volatility_portfolio.expected_return,
                    marker="o",
                    color="green",
                    s = 200,
                    edgecolors="black",
                    linewidth = 2,
                    label = f"Min Volatility ({ef_result.min_volatility_portfolio.volatility:.3f})",
                )

            # 繪製個別資產
            if self.ef_config.show_individual_assets:
                for i, asset in enumerate(ef_result.asset_names):
                    plt.scatter(
                        ef_result.asset_volatilities[i],
                        ef_result.asset_returns[i],
                        marker="s",
                        s = 100,
                        alpha = 0.8,
                        label = asset,
                    )
                    # 添加資產名稱標籤
                    plt.annotate(
                        asset,
                        (ef_result.asset_volatilities[i], ef_result.asset_returns[i]),
                        xytext=(5, 5),
                        textcoords="offset points",
                        fontsize = 8,
                        alpha = 0.8,
                    )

            # 繪製資本市場線
            if self.ef_config.show_cml and ef_result.cml_slope is not None:
                max_vol = ef_result.portfolios["Volatility"].max() * 1.1
                vol_range = np.linspace(0, max_vol, 100)
                cml_returns = ef_result.cml_intercept + ef_result.cml_slope * vol_range
                plt.plot(
                    vol_range,
                    cml_returns,
                    "b-",
                    linewidth = 2,
                    label = f"Capital Market Line (rf={ef_result.risk_free_rate * 100:.1f}%)",
                )

            # 設置圖表標題和標籤
            plt.title(
                "Efficient Frontier and Optimal Portfolios",
                fontsize = 16,
                fontweight="bold",
            )
            plt.xlabel("Expected Volatility (Risk)", fontsize = 12)
            plt.ylabel("Expected Return", fontsize = 12)

            # 添加顏色條
            cbar = plt.colorbar(scatter)
            cbar.set_label("Sharpe Ratio", fontsize = 12)

            # 添加圖例
            plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize = 10)

            # 添加網格
            plt.grid(True, alpha = 0.3)

            # 調整佈局
            plt.tight_layout()

            # 保存或顯示圖表
            if save_path:
                plt.savefig(save_path, dpi = 300, bbox_inches="tight")
                logger.info(f"Efficient frontier plot saved to {save_path}")

            if show_plot:
                plt.show()
            else:
                plt.close()

        except Exception as e:
            logger.error(f"Failed to plot efficient frontier: {e}")
            raise

    def generate_efficient_frontier_report(
        self, ef_result: EfficientFrontierResult, save_path: Optional[str] = None
    ) -> str:
        """
        生成有效邊界分析報告

        Args:
            ef_result: 有效邊界結果
            save_path: 保存路徑 (可選)

        Returns:
            str: 分析報告
        """
        try:
            report_lines = []

            # 報告標題
            report_lines.append("=" * 60)
            report_lines.append("EFFICIENT FRONTIER ANALYSIS REPORT")
            report_lines.append("=" * 60)
            report_lines.append(f"Generated on: {ef_result.timestamp}")
            report_lines.append(
                f"Calculation Time: {ef_result.calculation_time:.3f} seconds"
            )
            report_lines.append(
                f"Risk - free Rate: {ef_result.risk_free_rate * 100:.2f}%"
            )
            report_lines.append("")

            # 投資組合統計
            report_lines.append("PORTFOLIO STATISTICS")
            report_lines.append("-" * 30)
            report_lines.append(
                f"Total Portfolios Generated: {ef_result.total_portfolios:,}"
            )
            report_lines.append(
                f"Efficient Portfolios: {ef_result.efficient_portfolios_count:,}"
            )
            report_lines.append(
                f"Efficiency Ratio: {ef_result.efficient_portfolios_count / ef_result.total_portfolios:.2%}"
            )
            report_lines.append("")

            # 最優投資組合
            report_lines.append("OPTIMAL PORTFOLIOS")
            report_lines.append("-" * 20)

            # 最大夏普比率投資組合
            max_sharpe = ef_result.max_sharpe_portfolio
            report_lines.append("Maximum Sharpe Ratio Portfolio:")
            report_lines.append(
                f"  Expected Return: {max_sharpe.expected_return * 100:.2f}%"
            )
            report_lines.append(f"  Volatility: {max_sharpe.volatility * 100:.2f}%")
            report_lines.append(f"  Sharpe Ratio: {max_sharpe.sharpe_ratio:.3f}")

            # Top 5 holdings
            weights_dict = {
                asset: weight
                for asset, weight in zip(max_sharpe.assets, max_sharpe.weights)
            }
            top_assets = sorted(weights_dict.items(), key = lambda x: x[1], reverse = True)[
                :5
            ]
            report_lines.append("  Top 5 Holdings:")
            for asset, weight in top_assets:
                report_lines.append(f"    {asset}: {weight * 100:.2f}%")
            report_lines.append("")

            # 最小波動率投資組合
            min_vol = ef_result.min_volatility_portfolio
            report_lines.append("Minimum Volatility Portfolio:")
            report_lines.append(
                f"  Expected Return: {min_vol.expected_return * 100:.2f}%"
            )
            report_lines.append(f"  Volatility: {min_vol.volatility * 100:.2f}%")
            report_lines.append(f"  Sharpe Ratio: {min_vol.sharpe_ratio:.3f}")

            # Top 5 holdings
            weights_dict = {
                asset: weight for asset, weight in zip(min_vol.assets, min_vol.weights)
            }
            top_assets = sorted(weights_dict.items(), key = lambda x: x[1], reverse = True)[
                :5
            ]
            report_lines.append("  Top 5 Holdings:")
            for asset, weight in top_assets:
                report_lines.append(f"    {asset}: {weight * 100:.2f}%")
            report_lines.append("")

            # 資本市場線
            if ef_result.cml_slope is not None:
                report_lines.append("CAPITAL MARKET LINE")
                report_lines.append("-" * 23)
                report_lines.append(f"Slope: {ef_result.cml_slope:.4f}")
                report_lines.append(f"Intercept: {ef_result.cml_intercept:.4f}")
                report_lines.append(
                    f"Market Return Premium: {ef_result.cml_slope * 100:.2f}% per unit of risk"
                )
                report_lines.append("")

            # 個別資產分析
            report_lines.append("INDIVIDUAL ASSET ANALYSIS")
            report_lines.append("-" * 28)

            asset_data = []
            for asset, ret, vol in zip(
                ef_result.asset_names,
                ef_result.asset_returns,
                ef_result.asset_volatilities,
            ):
                asset_sharpe = (ret - ef_result.risk_free_rate) / vol if vol > 0 else 0
                asset_data.append((asset, ret, vol, asset_sharpe))

            # 按夏普比率排序
            asset_data.sort(key = lambda x: x[3], reverse = True)

            for asset, ret, vol, sharpe in asset_data:
                report_lines.append(
                    f"{asset}: Return={ret * 100:6.2f}%, "
                    f"Vol={vol * 100:6.2f}%, "
                    f"Sharpe={sharpe:6.3f}"
                )
            report_lines.append("")

            # 投資建議
            report_lines.append("INVESTMENT RECOMMENDATIONS")
            report_lines.append("-" * 30)

            if max_sharpe.sharpe_ratio > 1.0:
                report_lines.append(
                    "✓ Maximum Sharpe portfolio shows excellent risk - adjusted returns"
                )
            elif max_sharpe.sharpe_ratio > 0.5:
                report_lines.append(
                    "✓ Maximum Sharpe portfolio shows good risk - adjusted returns"
                )
            else:
                report_lines.append(
                    "⚠ Consider additional assets or different time periods"
                )

            if max_sharpe.volatility < 0.20:
                report_lines.append(
                    "✓ Optimal portfolio has acceptable volatility level"
                )
            elif max_sharpe.volatility < 0.30:
                report_lines.append("⚠ Optimal portfolio has moderate volatility level")
            else:
                report_lines.append("⚠ Optimal portfolio has high volatility level")

            # 報告結尾
            report_lines.append("=" * 60)
            report_lines.append("END OF REPORT")
            report_lines.append("=" * 60)

            report_text = "\n".join(report_lines)

            # 保存報告
            if save_path:
                with open(save_path, "w", encoding="utf - 8") as f:
                    f.write(report_text)
                logger.info(f"Efficient frontier report saved to {save_path}")

            return report_text

        except Exception as e:
            logger.error(f"Failed to generate efficient frontier report: {e}")
            raise

    def _prepare_data(self, returns: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """準備數據"""
        returns_clean = returns.dropna()

        if len(returns_clean) == 0:
            raise ValueError("No valid return data after removing NaN values")

        mean_returns = returns_clean.mean() * self.mpt_config.trading_days_per_year
        cov_matrix = returns_clean.cov() * self.mpt_config.trading_days_per_year

        return mean_returns.values, cov_matrix.values

    def _generate_random_portfolios(
        self, mean_returns: np.ndarray, cov_matrix: np.ndarray, num_assets: int
    ) -> pd.DataFrame:
        """生成隨機投資組合"""
        portfolios_data = []

        for _ in range(self.ef_config.num_portfolios):
            # 生成隨機權重
            weights = np.random.random(num_assets)
            weights = weights / np.sum(weights)

            # 計算投資組合統計
            portfolio_return = np.sum(mean_returns * weights)
            portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
            portfolio_volatility = np.sqrt(portfolio_variance)

            if portfolio_volatility > 0:
                sharpe_ratio = (
                    portfolio_return - self.mpt_config.risk_free_rate
                ) / portfolio_volatility
            else:
                sharpe_ratio = 0

            portfolios_data.append(
                {
                    "Return": portfolio_return,
                    "Volatility": portfolio_volatility,
                    "Sharpe": sharpe_ratio,
                    "Weights": weights.copy(),
                }
            )

        return pd.DataFrame(portfolios_data)

    def _identify_efficient_frontier(self, portfolios_df: pd.DataFrame) -> pd.DataFrame:
        """識別有效邊界"""
        # 按波動率排序
        sorted_portfolios = portfolios_df.sort_values("Volatility")

        efficient_portfolios = []
        max_return = -float("inf")

        for _, portfolio in sorted_portfolios.iterrows():
            if portfolio["Return"] > max_return:
                efficient_portfolios.append(portfolio)
                max_return = portfolio["Return"]

        return pd.DataFrame(efficient_portfolios)

    def _calculate_capital_market_line(
        self,
        efficient_portfolios_df: pd.DataFrame,
        max_sharpe_portfolio: OptimizationResult,
    ) -> Tuple[Optional[float], Optional[float]]:
        """計算資本市場線"""
        try:
            if len(efficient_portfolios_df) == 0:
                return None, None

            # CML斜率 = (市場投資組合回報 - 無風險利率) / 市場投資組合波動率
            if max_sharpe_portfolio.volatility > 0:
                cml_slope = (
                    max_sharpe_portfolio.expected_return
                    - self.mpt_config.risk_free_rate
                ) / max_sharpe_portfolio.volatility
                cml_intercept = self.mpt_config.risk_free_rate
                return cml_slope, cml_intercept
            else:
                return None, None

        except Exception as e:
            logger.warning(f"Failed to calculate Capital Market Line: {e}")
            return None, None

    def _optimize_for_target_volatility(
        self,
        mean_returns: np.ndarray,
        cov_matrix: np.ndarray,
        target_volatility: float,
        num_assets: int,
        asset_names: List[str],
    ) -> OptimizationResult:
        """為目標波動率優化投資組合"""
        from scipy.optimize import minimize

        def objective(weights):
            portfolio_return = np.sum(mean_returns * weights)
            # 最大化回報率 (或等價地，最小化負回報率)
            return -portfolio_return

        def volatility_constraint(weights):
            portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
            portfolio_volatility = np.sqrt(portfolio_variance)
            return target_volatility - portfolio_volatility

        # 約束條件
        constraints = [
            {"type": "eq", "fun": lambda w: np.sum(w) - 1.0},  # 權重總和為1
            {"type": "ineq", "fun": volatility_constraint},  # 波動率約束
        ]

        # 邊界
        bounds = tuple([(0.0, 1.0) for _ in range(num_assets)])

        # 初始權重
        initial_weights = np.array([1.0 / num_assets] * num_assets)

        # 執行優化
        result = minimize(
            objective,
            initial_weights,
            method="SLSQP",
            bounds = bounds,
            constraints = constraints,
            options={"maxiter": 1000},
        )

        if result.success:
            weights = result.x
            portfolio_return = np.sum(mean_returns * weights)
            portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
            portfolio_volatility = np.sqrt(portfolio_variance)
            sharpe_ratio = (
                portfolio_return - self.mpt_config.risk_free_rate
            ) / portfolio_volatility

            # 計算風險貢獻
            portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
            if portfolio_variance > 0:
                marginal_contributions = (
                    np.dot(cov_matrix, weights) / portfolio_variance
                )
                risk_contributions = weights * marginal_contributions
                total_risk = np.sum(risk_contributions)
                if total_risk > 0:
                    risk_contributions = risk_contributions / total_risk
            else:
                marginal_contributions = np.zeros(num_assets)
                risk_contributions = np.zeros(num_assets)

            return OptimizationResult(
                weights = weights,
                expected_return = portfolio_return,
                volatility = portfolio_volatility,
                sharpe_ratio = sharpe_ratio,
                optimization_method="TARGET_VOLATILITY",
                success = result.success,
                iterations = result.nit,
                objective_value = -result.fun,
                marginal_contributions = marginal_contributions,
                risk_contributions = risk_contributions,
                assets = asset_names,
                calculation_time = 0.0,
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
        else:
            # 如果優化失敗，返回等權重
            weights = initial_weights
            portfolio_return = np.sum(mean_returns * weights)
            portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
            portfolio_volatility = np.sqrt(portfolio_variance)
            sharpe_ratio = (
                portfolio_return - self.mpt_config.risk_free_rate
            ) / portfolio_volatility

            return OptimizationResult(
                weights = weights,
                expected_return = portfolio_return,
                volatility = portfolio_volatility,
                sharpe_ratio = sharpe_ratio,
                optimization_method="TARGET_VOLATILITY",
                success = False,
                iterations = 0,
                objective_value = portfolio_return,
                marginal_contributions = np.zeros(num_assets),
                risk_contributions = np.zeros(num_assets),
                assets = asset_names,
                calculation_time = 0.0,
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )


# 便利函數
def create_efficient_frontier_calculator(
    mpt_config: Optional[MPTConfig] = None,
    ef_config: Optional[EfficientFrontierConfig] = None,
) -> EfficientFrontierCalculator:
    """創建有效邊界計算器"""
    return EfficientFrontierCalculator(mpt_config, ef_config)


def calculate_efficient_frontier(
    returns: pd.DataFrame, num_portfolios: int = 200, risk_free_rate: float = 0.03
) -> EfficientFrontierResult:
    """便利函數：計算有效邊界"""
    ef_config = EfficientFrontierConfig(num_portfolios = num_portfolios)
    mpt_config = MPTConfig(risk_free_rate = risk_free_rate)

    calculator = EfficientFrontierCalculator(mpt_config, ef_config)
    return calculator.calculate_efficient_frontier(returns)

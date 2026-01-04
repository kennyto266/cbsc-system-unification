"""
Dynamic Weight Adjustment Strategy
動態權重調整策略

實現基於市場狀況的動態權重調整：
- 市場狀態識別（牛市、熊市、盤整）
- 動態風險預算
- 自適應權重調整
- 條件性再平衡
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, date, timedelta
from dataclasses import dataclass, field
from enum import Enum
from scipy import stats
import warnings

from .multi_asset_optimizer import (
    MultiAssetOptimizer,
    OptimizationMethod,
    OptimizationConstraints,
    BlackLittermanConfig
)
from ..base import BaseStrategy
from ..enhanced_factory import StrategyMetadata, StrategyType

logger = logging.getLogger(__name__)


class MarketRegime(str, Enum):
    """市場狀態枚舉"""
    BULL = "bull"           # 牛市
    BEAR = "bear"           # 熊市
    SIDEWAYS = "sideways"   # 盤整
    VOLATILE = "volatile"   # 高波動
    CRISIS = "crisis"       # 危機模式


class RebalanceTrigger(str, Enum):
    """再平衡觸發條件"""
    TIME_BASED = "time_based"       # 定期
    THRESHOLD = "threshold"         # 權重偏離閾值
    VOLATILITY = "volatility"       # 波動率觸發
    DRAWDOWN = "drawdown"           # 回撤觸發
    CORRELATION = "correlation"     # 相關性變化
    COMBINED = "combined"           # 綜合觸發


@dataclass
class DynamicWeightConfig:
    """動態權重配置"""
    # 市場狀態配置
    market_regime_config: Dict[MarketRegime, Dict[str, Any]] = field(default_factory=dict)
    # 每個狀態對應的優化參數

    # 再平衡觸發配置
    rebalance_triggers: List[RebalanceTrigger] = field(default_factory=lambda: [RebalanceTrigger.TIME_BASED])
    rebalance_frequency: str = "M"  # W, M, Q

    # 閾值配置
    weight_deviation_threshold: float = 0.05  # 5%
    volatility_threshold: float = 0.25  # 25%
    drawdown_threshold: float = 0.10  # 10%
    correlation_change_threshold: float = 0.1  # 0.1

    # 動態風險配置
    base_risk_target: float = 0.15  # 基礎風險目標
    max_risk_target: float = 0.30   # 最大風險目標
    min_risk_target: float = 0.05   # 最小風險目標
    risk_adjustment_factor: float = 1.5  # 風險調整因子

    # 條件性配置
    crisis_mode_enabled: bool = True
    crisis_indicators: List[str] = field(default_factory=lambda: ["VIX", "credit_spread", "liquidity"])
    protective_asset: str = "cash"  # 阦禦性資產

    # 自適應參數
    lookback_windows: Dict[str, int] = field(default_factory=lambda: {
        "short": 20,    # 短期窗口
        "medium": 60,   # 中期窗口
        "long": 252     # 長期窗口
    })

    # 機器學習配置
    use_ml_prediction: bool = False
    prediction_horizon: int = 5  # 預測天數


class MarketRegimeDetector:
    """市場狀態檢測器"""

    def __init__(self, lookback_periods: Dict[str, int]):
        """
        初始化市場狀態檢測器

        Args:
            lookback_periods: 不同時間窗口的回溯期
        """
        self.lookback_periods = lookback_periods
        self.market_indicators = {}

    def detect_regime(
        self,
        market_data: pd.DataFrame,
        benchmark_returns: pd.Series,
        volatility_index: Optional[pd.Series] = None
    ) -> MarketRegime:
        """
        檢測當前市場狀態

        Args:
            market_data: 市場數據
            benchmark_returns: 基準收益率
            volatility_index: 波動率指數（如VIX）

        Returns:
            當前市場狀態
        """
        try:
            # 計算市場指標
            indicators = self._calculate_market_indicators(
                market_data, benchmark_returns, volatility_index
            )

            # 基於規則的狀態判斷
            regime = self._rule_based_regime_detection(indicators)

            # 更新內部狀態
            self.market_indicators = indicators

            return regime

        except Exception as e:
            logger.error(f"Regime detection failed: {e}")
            return MarketRegime.SIDEWAYS

    def _calculate_market_indicators(
        self,
        market_data: pd.DataFrame,
        benchmark_returns: pd.Series,
        volatility_index: Optional[pd.Series] = None
    ) -> Dict[str, float]:
        """計算市場指標"""
        indicators = {}

        # 趨勢指標
        for period_name, lookback in self.lookback_periods.items():
            if len(benchmark_returns) >= lookback:
                period_returns = benchmark_returns.tail(lookback)
                indicators[f"{period_name}_return"] = period_returns.sum()
                indicators[f"{period_name}_volatility"] = period_returns.std() * np.sqrt(252)

        # 動量指標
        if len(benchmark_returns) >= 20:
            indicators["momentum_20"] = benchmark_returns.tail(20).mean() / benchmark_returns.std()
            indicators["momentum_60"] = benchmark_returns.tail(60).mean() / benchmark_returns.std()

        # 波動率指標
        if volatility_index is not None and len(volatility_index) > 0:
            indicators["current_vix"] = volatility_index.iloc[-1]
            indicators["vix_ma"] = volatility_index.tail(20).mean()
            indicators["vix_ratio"] = indicators["current_vix"] / indicators["vix_ma"]

        # 廣度指標（如果有行業數據）
        if isinstance(market_data, pd.DataFrame) and len(market_data.columns) > 1:
            returns = market_data.pct_change().dropna()
            if len(returns) > 0:
                indicators["market_breadth"] = (returns > 0).mean(axis=1).tail(20).mean()
                indicators["correlation_avg"] = returns.corr().mean().mean()

        # 回撤指標
        cumulative = (1 + benchmark_returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        indicators["max_drawdown"] = drawdown.min()
        indicators["current_drawdown"] = drawdown.iloc[-1]

        return indicators

    def _rule_based_regime_detection(self, indicators: Dict[str, float]) -> MarketRegime:
        """基於規則的市場狀態檢測"""
        # 危機模式檢測
        if indicators.get("current_drawdown", 0) < -0.20:
            return MarketRegime.CRISIS
        if indicators.get("vix_ratio", 1) > 1.5:
            return MarketRegime.CRISIS

        # 熊市檢測
        if (indicators.get("long_return", 0) < -0.10 and
            indicators.get("current_drawdown", 0) < -0.15):
            return MarketRegime.BEAR

        # 牛市檢測
        if (indicators.get("long_return", 0) > 0.20 and
            indicators.get("momentum_60", 0) > 0.5 and
            indicators.get("current_drawdown", 0) > -0.05):
            return MarketRegime.BULL

        # 高波動檢測
        if indicators.get("long_volatility", 0.15) > 0.25:
            return MarketRegime.VOLATILE

        # 默認為盤整
        return MarketRegime.SIDEWAYS


class DynamicWeightAdjustmentStrategy:
    """動態權重調整策略"""

    def __init__(
        self,
        config: DynamicWeightConfig,
        base_optimizer: Optional[MultiAssetOptimizer] = None
    ):
        """
        初始化動態權重調整策略

        Args:
            config: 動態權重配置
            base_optimizer: 基礎優化器
        """
        self.config = config
        self.optimizer = base_optimizer or MultiAssetOptimizer()
        self.regime_detector = MarketRegimeDetector(config.lookback_windows)

        # 內部狀態
        self.current_regime = MarketRegime.SIDEWAYS
        self.current_weights = {}
        self.last_rebalance_date = None
        self.weight_history = []
        self.regime_history = []
        self.performance_metrics = []

        # 狀態特定配置
        self._initialize_regime_configs()

        logger.info("Dynamic Weight Adjustment Strategy initialized")

    def _initialize_regime_configs(self):
        """初始化各市場狀態的配置"""
        if not self.config.market_regime_config:
            # 使用默認配置
            self.config.market_regime_config = {
                MarketRegime.BULL: {
                    "risk_target": self.config.base_risk_target * 1.2,
                    "method": OptimizationMethod.TARGET_RETURN,
                    "max_weight_per_asset": 0.4
                },
                MarketRegime.BEAR: {
                    "risk_target": self.config.base_risk_target * 0.6,
                    "method": OptimizationMethod.MIN_VARIANCE,
                    "max_weight_per_asset": 0.3
                },
                MarketRegime.SIDEWAYS: {
                    "risk_target": self.config.base_risk_target,
                    "method": OptimizationMethod.RISK_PARITY,
                    "max_weight_per_asset": 0.35
                },
                MarketRegime.VOLATILE: {
                    "risk_target": self.config.base_risk_target * 0.8,
                    "method": OptimizationMethod.MIN_VARIANCE,
                    "max_weight_per_asset": 0.25
                },
                MarketRegime.CRISIS: {
                    "risk_target": self.config.min_risk_target,
                    "method": OptimizationMethod.MIN_VARIANCE,
                    "max_weight_per_asset": 0.2,
                    "cash_allocation": 0.5  # 50%現金
                }
            }

    def adjust_weights(
        self,
        price_data: Dict[str, pd.DataFrame],
        benchmark_data: pd.DataFrame,
        current_date: Optional[datetime] = None
    ) -> Dict[str, float]:
        """
        執行動態權重調整

        Args:
            price_data: 資產價格數據
            benchmark_data: 基準數據
            current_date: 當前日期

        Returns:
            調整後的權重
        """
        try:
            # 檢測市場狀態
            benchmark_returns = benchmark_data['close'].pct_change().dropna()
            market_df = pd.concat([df['close'] for df in price_data.values()], axis=1)
            market_df.columns = price_data.keys()

            # 檢測波動率指數（如果有）
            volatility_index = None
            if 'VIX' in price_data:
                volatility_index = price_data['VIX']['close']

            new_regime = self.regime_detector.detect_regime(
                market_df, benchmark_returns, volatility_index
            )

            # 檢查是否需要再平衡
            if not self._should_rebalance(current_date, new_regime):
                return self.current_weights

            # 記錄狀態變化
            if new_regime != self.current_regime:
                logger.info(f"Regime changed: {self.current_regime} -> {new_regime}")
                self.regime_history.append({
                    'date': current_date or datetime.now(),
                    'old_regime': self.current_regime,
                    'new_regime': new_regime,
                    'indicators': self.regime_detector.market_indicators
                })

            self.current_regime = new_regime

            # 獲取狀態特定配置
            regime_config = self.config.market_regime_config[new_regime]

            # 更新優化器配置
            self._update_optimizer_config(regime_config)

            # 執行權重優化
            self.optimizer.prepare_data(price_data)

            # 計算目標風險水平
            target_risk = self._calculate_dynamic_risk_target(regime_config)

            # 根據狀態執行不同的優化策略
            if regime_config["method"] == OptimizationMethod.TARGET_RETURN:
                # 計算目標收益率
                target_return = self._calculate_target_return(regime_config)
                new_weights = self.optimizer.optimize_weights(target_return=target_return)
            elif regime_config["method"] == OptimizationMethod.TARGET_VOLATILITY:
                new_weights = self.optimizer.optimize_weights(target_volatility=target_risk)
            else:
                new_weights = self.optimizer.optimize_weights()

            # 危機模式特殊處理
            if new_regime == MarketRegime.CRISIS and self.config.crisis_mode_enabled:
                new_weights = self._apply_crisis_allocation(new_weights, regime_config)

            # 應用交易成本約束
            if self.current_weights:
                turnover = self.optimizer._calculate_turnover(self.current_weights, new_weights)
                if turnover > 0.2:  # 如果周轉率超過20%
                    new_weights = self._smooth_weight_transition(
                        self.current_weights, new_weights, 0.5
                    )

            # 更新狀態
            self.current_weights = new_weights
            self.last_rebalance_date = current_date or datetime.now()

            # 記錄權重歷史
            self.weight_history.append({
                'date': self.last_rebalance_date,
                'regime': self.current_regime,
                'weights': new_weights.copy(),
                'risk_target': target_risk
            })

            # 計算性能指標
            self._update_performance_metrics(price_data, new_weights)

            return new_weights

        except Exception as e:
            logger.error(f"Weight adjustment failed: {e}")
            return self.current_weights

    def _should_rebalance(
        self,
        current_date: Optional[datetime],
        new_regime: MarketRegime
    ) -> bool:
        """判斷是否需要再平衡"""
        # 如果市場狀態改變，立即再平衡
        if new_regime != self.current_regime:
            return True

        # 檢查各種觸發條件
        triggers = self.config.rebalance_triggers

        # 時間觸發
        if RebalanceTrigger.TIME_BASED in triggers:
            if self.last_rebalance_date is None:
                return True

            # 計算時間間隔
            freq_map = {"D": 1, "W": 7, "M": 30, "Q": 90}
            days_since_rebalance = (current_date - self.last_rebalance_date).days
            if days_since_rebalance >= freq_map.get(self.config.rebalance_frequency, 30):
                return True

        # 權重偏離觸發
        if RebalanceTrigger.THRESHOLD in triggers and self.current_weights:
            # 需要實時權重數據來判斷，這裡簡化處理
            pass

        # 波動率觸發
        if RebalanceTrigger.VOLATILITY in triggers:
            current_vol = self.regime_detector.market_indicators.get("long_volatility", 0)
            if current_vol > self.config.volatility_threshold:
                return True

        # 回撤觸發
        if RebalanceTrigger.DRAWDOWN in triggers:
            current_dd = self.regime_detector.market_indicators.get("current_drawdown", 0)
            if current_dd < -self.config.drawdown_threshold:
                return True

        return False

    def _update_optimizer_config(self, regime_config: Dict[str, Any]):
        """更新優化器配置以適應市場狀態"""
        # 更新風險目標
        if "risk_target" in regime_config:
            self.optimizer.risk_target = regime_config["risk_target"]

        # 更新優化方法
        if "method" in regime_config:
            self.optimizer.method = regime_config["method"]

        # 更新約束條件
        if "max_weight_per_asset" in regime_config:
            self.optimizer.constraints.max_weight_per_asset = regime_config["max_weight_per_asset"]

    def _calculate_dynamic_risk_target(self, regime_config: Dict[str, Any]) -> float:
        """計算動態風險目標"""
        base_risk = regime_config.get("risk_target", self.config.base_risk_target)

        # 基於市場指標調整
        indicators = self.regime_detector.market_indicators

        # 波動率調整
        vol_multiplier = 1.0
        if "long_volatility" in indicators:
            vol = indicators["long_volatility"]
            if vol > 0.30:  # 高波動
                vol_multiplier = 0.7
            elif vol < 0.10:  # 低波動
                vol_multiplier = 1.3

        # 回撤調整
        dd_multiplier = 1.0
        if "current_drawdown" in indicators:
            dd = abs(indicators["current_drawdown"])
            if dd > 0.15:  # 大幅回撤
                dd_multiplier = 0.6

        # 計算最終風險目標
        adjusted_risk = base_risk * vol_multiplier * dd_multiplier
        adjusted_risk = np.clip(
            adjusted_risk,
            self.config.min_risk_target,
            self.config.max_risk_target
        )

        return adjusted_risk

    def _calculate_target_return(self, regime_config: Dict[str, Any]) -> float:
        """計算目標收益率"""
        # 基於市場狀態和歷史數據計算目標
        indicators = self.regime_detector.market_indicators

        if self.current_regime == MarketRegime.BULL:
            # 牛市：追求高收益
            base_return = 0.15
            if "long_return" in indicators:
                base_return = max(base_return, indicators["long_return"])
        elif self.current_regime == MarketRegime.BEAR:
            # 熊市：保本為主
            base_return = 0.03
        elif self.current_regime == MarketRegime.CRISIS:
            # 危機：絕對收益
            base_return = 0.01
        else:
            # 正常情況
            base_return = 0.08

        return base_return

    def _apply_crisis_allocation(
        self,
        weights: Dict[str, float],
        regime_config: Dict[str, Any]
    ) -> Dict[str, float]:
        """應用危機模式配置"""
        cash_allocation = regime_config.get("cash_allocation", 0.3)

        # 減少所有資產權重，騰出現金空間
        scale_factor = 1 - cash_allocation
        for asset in weights:
            weights[asset] *= scale_factor

        # 添加現金
        weights["cash"] = cash_allocation

        return weights

    def _smooth_weight_transition(
        self,
        current_weights: Dict[str, float],
        target_weights: Dict[str, float],
        smoothing_factor: float
    ) -> Dict[str, float]:
        """平滑權重過渡"""
        smoothed_weights = {}
        all_assets = set(current_weights.keys()) | set(target_weights.keys())

        for asset in all_assets:
            current = current_weights.get(asset, 0)
            target = target_weights.get(asset, 0)
            smoothed = current + smoothing_factor * (target - current)
            smoothed_weights[asset] = smoothed

        return smoothed_weights

    def _update_performance_metrics(
        self,
        price_data: Dict[str, pd.DataFrame],
        weights: Dict[str, float]
    ):
        """更新性能指標"""
        # 計算投資組合收益率
        portfolio_return = 0.0
        portfolio_volatility = self.optimizer._calculate_portfolio_volatility(weights)
        sharpe_ratio = self.optimizer._calculate_sharpe_ratio(weights)

        # 計算風險貢獻
        risk_contributions = self.optimizer.analyze_risk_contributions(weights)

        # 記錄指標
        self.performance_metrics.append({
            'date': datetime.now(),
            'regime': self.current_regime,
            'weights': weights.copy(),
            'portfolio_return': portfolio_return,
            'portfolio_volatility': portfolio_volatility,
            'sharpe_ratio': sharpe_ratio,
            'risk_contributions': risk_contributions,
            'num_assets': len([w for w in weights.values() if w > 0.01])
        })

    def get_strategy_state(self) -> Dict[str, Any]:
        """獲取策略當前狀態"""
        return {
            "current_regime": self.current_regime,
            "current_weights": self.current_weights,
            "last_rebalance_date": self.last_rebalance_date,
            "optimization_method": self.optimizer.method.value,
            "risk_target": self.optimizer.risk_target,
            "regime_indicators": self.regime_detector.market_indicators,
            "total_rebalances": len(self.weight_history),
            "regime_changes": len(self.regime_history)
        }

    def get_performance_summary(self) -> Dict[str, Any]:
        """獲取性能摘要"""
        if not self.performance_metrics:
            return {}

        # 計算平均指標
        metrics_df = pd.DataFrame(self.performance_metrics)

        summary = {
            "total_metrics": len(metrics_df),
            "average_return": metrics_df["portfolio_return"].mean(),
            "average_volatility": metrics_df["portfolio_volatility"].mean(),
            "average_sharpe": metrics_df["sharpe_ratio"].mean(),
            "current_sharpe": metrics_df["sharpe_ratio"].iloc[-1] if len(metrics_df) > 0 else 0,
            "regime_distribution": metrics_df["regime"].value_counts().to_dict()
        }

        # 按狀態統計性能
        regime_performance = {}
        for regime in MarketRegime:
            regime_data = metrics_df[metrics_df["regime"] == regime]
            if len(regime_data) > 0:
                regime_performance[regime.value] = {
                    "count": len(regime_data),
                    "avg_return": regime_data["portfolio_return"].mean(),
                    "avg_volatility": regime_data["portfolio_volatility"].mean(),
                    "avg_sharpe": regime_data["sharpe_ratio"].mean()
                }

        summary["regime_performance"] = regime_performance

        return summary

    def backtest_dynamic_strategy(
        self,
        price_data: Dict[str, pd.DataFrame],
        benchmark_data: pd.DataFrame,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        回測動態權重策略

        Args:
            price_data: 資產價格數據
            benchmark_data: 基準數據
            start_date: 開始日期
            end_date: 結束日期

        Returns:
            回測結果
        """
        results = {
            "strategy_name": "Dynamic Weight Adjustment",
            "start_date": start_date,
            "end_date": end_date,
            "initial_capital": 100000,
            "weights_history": [],
            "regime_history": [],
            "performance_data": [],
            "transactions": []
        }

        # 初始化
        current_capital = results["initial_capital"]
        current_weights = {}
        current_positions = {}

        # 按時間回測
        date_range = pd.date_range(start_date, end_date, freq="D")

        for date in date_range:
            try:
                # 檢查是否有交易日數據
                if date not in benchmark_data.index:
                    continue

                # 檢查是否需要再平衡
                current_date = date.to_pydatetime()
                new_weights = self.adjust_weights(price_data, benchmark_data, current_date)

                # 如果權重發生變化，記錄交易
                if new_weights != current_weights:
                    # 計算交易（簡化版本）
                    for asset, target_weight in new_weights.items():
                        current_weight = current_weights.get(asset, 0)
                        if abs(target_weight - current_weight) > 0.01:  # 1%閾值
                            results["transactions"].append({
                                "date": current_date,
                                "asset": asset,
                                "action": "buy" if target_weight > current_weight else "sell",
                                "weight_change": target_weight - current_weight
                            })

                    current_weights = new_weights

                # 計算日收益
                daily_return = 0.0
                for asset, weight in current_weights.items():
                    if asset in price_data and date in price_data[asset].index:
                        asset_return = price_data[asset].loc[date, "close"] / price_data[asset].loc[date, "close"] - 1
                        daily_return += weight * asset_return

                # 更新資本
                current_capital *= (1 + daily_return)

                # 記錄每日數據
                results["performance_data"].append({
                    "date": current_date,
                    "portfolio_value": current_capital,
                    "daily_return": daily_return,
                    "cumulative_return": current_capital / results["initial_capital"] - 1,
                    "regime": self.current_regime,
                    "weights": current_weights.copy()
                })

            except Exception as e:
                logger.warning(f"Error processing date {date}: {e}")
                continue

        # 轉換為DataFrame
        results["performance_df"] = pd.DataFrame(results["performance_data"]).set_index("date")
        results["weights_history"] = self.weight_history.copy()
        results["regime_history"] = self.regime_history.copy()

        # 計算回測統計
        if results["performance_df"] is not None and len(results["performance_df"]) > 0:
            perf = results["performance_df"]
            results["statistics"] = {
                "total_return": perf["cumulative_return"].iloc[-1],
                "annualized_return": perf["daily_return"].mean() * 252,
                "annualized_volatility": perf["daily_return"].std() * np.sqrt(252),
                "sharpe_ratio": perf["daily_return"].mean() / perf["daily_return"].std() * np.sqrt(252),
                "max_drawdown": (perf["cumulative_return"] + 1).div(
                    (perf["cumulative_return"] + 1).expanding().max()
                ).min() - 1,
                "total_rebalances": len(self.weight_history),
                "regime_changes": len(self.regime_history)
            }

        return results
#!/usr / bin / env python3
"""
簡化系統 - 動態權重管理器
Simplified System - Dynamic Weight Manager

Phase 4.2: 多指標權重管理
- 實現DynamicWeightManager類
- 支持靜態權重配置和動態權重調整
- 實現基於性能的權重優化算法
- 添加權重約束條件和風險控制
- 實現權重性能評估和回測
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class WeightType(Enum):
    """權重類型枚舉"""

    STATIC = "STATIC"
    DYNAMIC = "DYNAMIC"
    PERFORMANCE_BASED = "PERFORMANCE_BASED"
    RISK_ADJUSTED = "RISK_ADJUSTED"


@dataclass
class IndicatorWeight:
    """指標權重數據類"""

    indicator_name: str
    base_weight: float  # 基礎權重
    current_weight: float  # 當前權重
    weight_type: WeightType

    # 性能指標
    accuracy: float = 0.0  # 準確率
    profitability: float = 0.0  # 盈利能力
    stability: float = 0.0  # 穩定性

    # 約束條件
    min_weight: float = 0.0
    max_weight: float = 1.0
    volatility_penalty: float = 0.0

    # 歷史記錄
    performance_history: List[float] = field(default_factory = list)
    weight_history: List[float] = field(default_factory = list)
    last_updated: datetime = field(default_factory = datetime.now)


@dataclass
class WeightPortfolio:
    """權重投資組合"""

    symbol: str
    weights: Dict[str, IndicatorWeight]
    total_weight: float
    performance_metrics: Dict[str, float]
    rebalance_frequency: int = 5  # 天
    last_rebalance: datetime = field(default_factory = datetime.now)


class DynamicWeightManager:
    """
    動態權重管理器

    核心功能：
    1. 管理多個技術指標的權重配置
    2. 基於性能動態調整權重
    3. 實施風險控制和約束條件
    4. 追蹤權重歷史和性能
    5. 提供權重優化建議
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化權重管理器"""
        self.config = config or self._get_default_config()

        # 權重投資組合（按股票分組）
        self.portfolios: Dict[str, WeightPortfolio] = {}

        # 全局權重配置
        self.global_weights: Dict[str, IndicatorWeight] = {}

        # 性能追蹤器
        self.performance_tracker: Dict[str, Dict[str, float]] = {}

        # 權重調整策略
        self.rebalance_strategies = {
            "performance_based": self._performance_based_rebalance,
            "risk_parity": self._risk_parity_rebalance,
            "momentum_based": self._momentum_based_rebalance,
            "regime_based": self._regime_based_rebalance,
            "volatility_adjusted": self._volatility_adjusted_rebalance,
        }

        # 初始化默認權重
        self._initialize_default_weights()

        logger.info("Dynamic Weight Manager initialized")

    def _get_default_config(self) -> Dict[str, Any]:
        """獲取默認配置"""
        return {
            "default_weights": {
                "RSI": 0.2,
                "MACD": 0.15,
                "BOLLINGER": 0.15,
                "SMA": 0.1,
                "EMA": 0.1,
                "VOLUME": 0.1,
                "STOCH": 0.1,
                "WILLIAMS_R": 0.05,
                "ATR": 0.05,
            },
            "weight_constraints": {
                "min_weight": 0.01,  # 最小權重1%
                "max_weight": 0.4,  # 最大權重40%
                "max_change_per_period": 0.1,  # 單次最大變化10%
                "volatility_threshold": 0.2,  # 波動率閾值
            },
            "performance_window": 30,  # 性能評估窗口（天）
            "rebalance_frequency": 5,  # 重平衡頻率（天）
            "performance_decay": 0.95,  # 性能衰減因子
            "risk_adjustment_factor": 0.8,  # 風險調整因子
            "momentum_factor": 0.1,  # 動量因子
            "regime_sensitivity": 0.2,  # 市場狀態敏感度
        }

    def _initialize_default_weights(self):
        """初始化默認權重配置"""
        for indicator, base_weight in self.config["default_weights"].items():
            min_weight = self.config["weight_constraints"]["min_weight"]
            max_weight = self.config["weight_constraints"]["max_weight"]

            self.global_weights[indicator] = IndicatorWeight(
                indicator_name = indicator,
                base_weight = base_weight,
                current_weight = base_weight,
                weight_type = WeightType.STATIC,
                min_weight = min_weight,
                max_weight = max_weight,
                last_updated = datetime.now(),
            )

    def create_portfolio(
        self,
        symbol: str,
        custom_weights: Optional[Dict[str, float]] = None,
        weight_type: WeightType = WeightType.STATIC,
    ) -> WeightPortfolio:
        """
        創建權重投資組合

        Args:
            symbol: 股票代碼
            custom_weights: 自定義權重配置
            weight_type: 權重類型

        Returns:
            權重投資組合
        """
        weights = {}

        # 使用自定義權重或全局權重
        weight_source = (
            custom_weights if custom_weights else self.config["default_weights"]
        )

        for indicator, weight_value in weight_source.items():
            min_weight = self.config["weight_constraints"]["min_weight"]
            max_weight = self.config["weight_constraints"]["max_weight"]

            # 應用約束條件
            weight_value = max(min_weight, min(max_weight, weight_value))

            weights[indicator] = IndicatorWeight(
                indicator_name = indicator,
                base_weight = weight_value,
                current_weight = weight_value,
                weight_type = weight_type,
                min_weight = min_weight,
                max_weight = max_weight,
                last_updated = datetime.now(),
            )

        # 計算總權重並標準化
        total_weight = sum(w.current_weight for w in weights.values())
        if total_weight > 0:
            for w in weights.values():
                w.current_weight = w.current_weight / total_weight
                w.base_weight = w.base_weight / sum(weight_source.values())

        portfolio = WeightPortfolio(
            symbol = symbol,
            weights = weights,
            total_weight = 1.0,
            performance_metrics={},
            rebalance_frequency = self.config["rebalance_frequency"],
        )

        self.portfolios[symbol] = portfolio

        logger.info(f"Created weight portfolio for {symbol}")
        return portfolio

    def update_weights(
        self,
        symbol: str,
        performance_data: Dict[str, Dict[str, float]],
        strategy: str = "performance_based",
    ) -> Dict[str, float]:
        """
        更新權重配置

        Args:
            symbol: 股票代碼
            performance_data: 性能數據 {indicator: {accuracy, profitability, stability}}
            strategy: 重平衡策略

        Returns:
            更新後的權重配置
        """
        if symbol not in self.portfolios:
            self.create_portfolio(symbol, weight_type = WeightType.DYNAMIC)

        portfolio = self.portfolios[symbol]

        # 更新性能指標
        self._update_performance_metrics(portfolio, performance_data)

        # 應用重平衡策略
        if strategy in self.rebalance_strategies:
            new_weights = self.rebalance_strategies[strategy](portfolio)
        else:
            logger.warning(f"Unknown rebalance strategy: {strategy}")
            new_weights = self.rebalance_strategies["performance_based"](portfolio)

        # 應用權重約束
        new_weights = self._apply_weight_constraints(new_weights)

        # 更新投資組合
        self._update_portfolio_weights(portfolio, new_weights)

        # 記錄重平衡
        portfolio.last_rebalance = datetime.now()

        logger.info(f"Updated weights for {symbol} using {strategy} strategy")
        return {
            name: weight.current_weight for name, weight in portfolio.weights.items()
        }

    def _update_performance_metrics(
        self, portfolio: WeightPortfolio, performance_data: Dict[str, Dict[str, float]]
    ):
        """更新性能指標"""
        for indicator, perf in performance_data.items():
            if indicator in portfolio.weights:
                weight = portfolio.weights[indicator]

                # 更新性能指標
                weight.accuracy = perf.get("accuracy", weight.accuracy)
                weight.profitability = perf.get("profitability", weight.profitability)
                weight.stability = perf.get("stability", weight.stability)

                # 記錄性能歷史
                performance_score = (
                    weight.accuracy * 0.4
                    + weight.profitability * 0.4
                    + weight.stability * 0.2
                )
                weight.performance_history.append(performance_score)

                # 限制歷史記錄長度
                max_history = self.config["performance_window"]
                if len(weight.performance_history) > max_history:
                    weight.performance_history = weight.performance_history[
                        -max_history:
                    ]

    def _performance_based_rebalance(
        self, portfolio: WeightPortfolio
    ) -> Dict[str, IndicatorWeight]:
        """基於性能的重平衡"""
        new_weights = {}
        weights = portfolio.weights.copy()

        # 計算性能加權分數
        performance_scores = {}
        total_score = 0

        for indicator, weight in weights.items():
            if weight.performance_history:
                # 使用加權平均（近期性能權重更高）
                recent_performance = np.mean(weight.performance_history[-5:])
                long_term_performance = np.mean(weight.performance_history)

                # 結合短期和長期性能
                combined_score = recent_performance * 0.6 + long_term_performance * 0.4

                # 應用性能衰減因子
                decay_factor = self.config["performance_decay"] ** len(
                    weight.performance_history
                )
                adjusted_score = combined_score * decay_factor
            else:
                # 無歷史數據，使用默認權重
                adjusted_score = weight.base_weight

            performance_scores[indicator] = adjusted_score
            total_score += adjusted_score

        # 標準化權重
        if total_score > 0:
            for indicator, weight in weights.items():
                new_weight = performance_scores[indicator] / total_score
                weight.current_weight = new_weight
                weight.weight_type = WeightType.PERFORMANCE_BASED
                weight.last_updated = datetime.now()
                new_weights[indicator] = weight

        return new_weights

    def _risk_parity_rebalance(
        self, portfolio: WeightPortfolio
    ) -> Dict[str, IndicatorWeight]:
        """風險平價重平衡"""
        weights = portfolio.weights.copy()

        # 計算每個指標的風險（基於穩定性和波動率）
        risk_measures = {}
        for indicator, weight in weights.items():
            # 風險 = 1 / 穩定性，結合波動率懲罰
            stability_risk = 1.0 / max(0.1, weight.stability)
            volatility_risk = 1.0 + weight.volatility_penalty
            total_risk = stability_risk * volatility_risk
            risk_measures[indicator] = total_risk

        # 風險平價：權重與風險成反比
        inverse_risks = {k: 1.0 / v for k, v in risk_measures.items()}
        total_inverse_risk = sum(inverse_risks.values())

        if total_inverse_risk > 0:
            for indicator, weight in weights.items():
                risk_parity_weight = inverse_risks[indicator] / total_inverse_risk
                weight.current_weight = risk_parity_weight
                weight.weight_type = WeightType.RISK_ADJUSTED
                weight.last_updated = datetime.now()

        return weights

    def _momentum_based_rebalance(
        self, portfolio: WeightPortfolio
    ) -> Dict[str, IndicatorWeight]:
        """基於動量的重平衡"""
        weights = portfolio.weights.copy()
        momentum_factor = self.config["momentum_factor"]

        for indicator, weight in weights.items():
            if len(weight.performance_history) >= 3:
                # 計算動量（近期性能改善程度）
                recent_performance = np.mean(weight.performance_history[-3:])
                older_performance = (
                    np.mean(weight.performance_history[-10:-3])
                    if len(weight.performance_history) >= 10
                    else np.mean(weight.performance_history[:-3])
                )

                momentum = (recent_performance - older_performance) * momentum_factor

                # 動量調整權重
                momentum_adjustment = 1.0 + momentum
                new_weight = weight.base_weight * momentum_adjustment

                weight.current_weight = new_weight
                weight.weight_type = WeightType.DYNAMIC
                weight.last_updated = datetime.now()

        return self._apply_weight_constraints(weights)

    def _regime_based_rebalance(
        self, portfolio: WeightPortfolio
    ) -> Dict[str, IndicatorWeight]:
        """基於市場狀態的重平衡"""
        weights = portfolio.weights.copy()
        regime_sensitivity = self.config["regime_sensitivity"]

        # 簡化的市場狀態檢測
        avg_performance = np.mean(
            [
                np.mean(w.performance_history[-5:]) if w.performance_history else 0.5
                for w in weights.values()
            ]
        )

        # 根據市場狀態調整權重
        if avg_performance > 0.6:  # 牛市
            # 偏向趨勢指標
            for indicator, weight in weights.items():
                if indicator in ["SMA", "EMA", "MACD"]:
                    weight.current_weight = weight.base_weight * (
                        1 + regime_sensitivity
                    )
                else:
                    weight.current_weight = weight.base_weight * (
                        1 - regime_sensitivity * 0.5
                    )

        elif avg_performance < 0.4:  # 熊市
            # 偏向逆向指標
            for indicator, weight in weights.items():
                if indicator in ["RSI", "BOLLINGER", "WILLIAMS_R"]:
                    weight.current_weight = weight.base_weight * (
                        1 + regime_sensitivity
                    )
                else:
                    weight.current_weight = weight.base_weight * (
                        1 - regime_sensitivity * 0.5
                    )

        else:  # 震盪市
            # 等權重
            equal_weight = 1.0 / len(weights)
            for weight in weights.values():
                weight.current_weight = equal_weight

        for weight in weights.values():
            weight.weight_type = WeightType.DYNAMIC
            weight.last_updated = datetime.now()

        return self._apply_weight_constraints(weights)

    def _volatility_adjusted_rebalance(
        self, portfolio: WeightPortfolio
    ) -> Dict[str, IndicatorWeight]:
        """基於波動率調整的重平衡"""
        weights = portfolio.weights.copy()
        risk_adjustment_factor = self.config["risk_adjustment_factor"]

        for indicator, weight in weights.items():
            # 基於穩定性調整權重
            stability_adjustment = weight.stability * risk_adjustment_factor + (
                1 - risk_adjustment_factor
            )

            # 應用波動率懲罰
            volatility_adjustment = 1.0 / (1.0 + weight.volatility_penalty)

            combined_adjustment = stability_adjustment * volatility_adjustment
            new_weight = weight.base_weight * combined_adjustment

            weight.current_weight = new_weight
            weight.weight_type = WeightType.RISK_ADJUSTED
            weight.last_updated = datetime.now()

        return self._apply_weight_constraints(weights)

    def _apply_weight_constraints(
        self, weights: Dict[str, IndicatorWeight]
    ) -> Dict[str, IndicatorWeight]:
        """應用權重約束條件"""
        min_weight = self.config["weight_constraints"]["min_weight"]
        max_weight = self.config["weight_constraints"]["max_weight"]
        max_change = self.config["weight_constraints"]["max_change_per_period"]

        # 應用最小最大權重約束
        for weight in weights.values():
            weight.current_weight = max(
                min_weight, min(max_weight, weight.current_weight)
            )

        # 應用單次變化約束
        for weight in weights.values():
            change = abs(weight.current_weight - weight.base_weight)
            if change > max_change:
                direction = 1 if weight.current_weight > weight.base_weight else -1
                weight.current_weight = weight.base_weight + direction * max_change

        # 重新標準化
        total_weight = sum(w.current_weight for w in weights.values())
        if total_weight > 0:
            for weight in weights.values():
                weight.current_weight = weight.current_weight / total_weight

        return weights

    def _update_portfolio_weights(
        self, portfolio: WeightPortfolio, new_weights: Dict[str, IndicatorWeight]
    ):
        """更新投資組合權重"""
        for indicator, new_weight in new_weights.items():
            if indicator in portfolio.weights:
                old_weight = portfolio.weights[indicator]
                old_weight.current_weight = new_weight.current_weight
                old_weight.weight_type = new_weight.weight_type
                old_weight.last_updated = new_weight.last_updated

                # 記錄權重歷史
                old_weight.weight_history.append(new_weight.current_weight)
                if len(old_weight.weight_history) > 50:  # 限制歷史長度
                    old_weight.weight_history = old_weight.weight_history[-50:]

        # 重新計算總權重
        portfolio.total_weight = sum(
            w.current_weight for w in portfolio.weights.values()
        )

    def get_weights(self, symbol: str) -> Dict[str, float]:
        """獲取股票的權重配置"""
        if symbol not in self.portfolios:
            return self.get_global_weights()

        return {
            name: weight.current_weight
            for name, weight in self.portfolios[symbol].weights.items()
        }

    def get_global_weights(self) -> Dict[str, float]:
        """獲取全局權重配置"""
        return {
            name: weight.current_weight for name, weight in self.global_weights.items()
        }

    def analyze_weight_performance(self, symbol: str) -> Dict[str, Any]:
        """分析權重性能"""
        if symbol not in self.portfolios:
            return {"error": f"Portfolio for {symbol} not found"}

        portfolio = self.portfolios[symbol]
        analysis = {
            "symbol": symbol,
            "total_weight": portfolio.total_weight,
            "last_rebalance": portfolio.last_rebalance.isoformat(),
            "indicator_analysis": {},
        }

        for indicator, weight in portfolio.weights.items():
            indicator_analysis = {
                "current_weight": weight.current_weight,
                "base_weight": weight.base_weight,
                "weight_change": weight.current_weight - weight.base_weight,
                "weight_type": weight.weight_type.value,
                "accuracy": weight.accuracy,
                "profitability": weight.profitability,
                "stability": weight.stability,
                "performance_trend": (
                    self._calculate_trend(weight.performance_history)
                    if weight.performance_history
                    else 0
                ),
                "volatility": (
                    np.std(weight.performance_history)
                    if len(weight.performance_history) > 1
                    else 0
                ),
                "recommendation": self._generate_weight_recommendation(weight),
            }

            analysis["indicator_analysis"][indicator] = indicator_analysis

        return analysis

    def _calculate_trend(self, values: List[float]) -> float:
        """計算趨勢（簡化的線性回歸斜率）"""
        if len(values) < 2:
            return 0

        x = np.arange(len(values))
        y = np.array(values)

        # 計算線性回歸斜率
        slope = np.polyfit(x, y, 1)[0]
        return slope

    def _generate_weight_recommendation(self, weight: IndicatorWeight) -> str:
        """生成權重調整建議"""
        if not weight.performance_history:
            return "需要更多數據進行分析"

        recent_performance = np.mean(weight.performance_history[-5:])
        weight_change = weight.current_weight - weight.base_weight

        if recent_performance > 0.7 and weight_change < 0.1:
            return "表現優異，建議增加權重"
        elif recent_performance > 0.6 and abs(weight_change) < 0.05:
            return "表現良好，維持當前權重"
        elif recent_performance < 0.4 and weight_change > -0.1:
            return "表現不佳，建議降低權重"
        elif abs(weight_change) > 0.2:
            return "權重變化過大，建議逐步調整"
        else:
            return "權重配置合理"

    def rebalance_all_portfolios(
        self, performance_data: Dict[str, Dict[str, Dict[str, float]]]
    ):
        """
        重平衡所有投資組合

        Args:
            performance_data: 性能數據 {symbol: {indicator: performance_metrics}}
        """
        for symbol, perf_data in performance_data.items():
            try:
                self.update_weights(symbol, perf_data)
                logger.info(f"Rebalanced portfolio for {symbol}")
            except Exception as e:
                logger.error(f"Error rebalancing portfolio for {symbol}: {e}")

    def export_weights(self, filepath: str):
        """導出權重配置"""
        export_data = {
            "export_time": datetime.now().isoformat(),
            "global_weights": self.get_global_weights(),
            "portfolio_weights": {
                symbol: self.get_weights(symbol) for symbol in self.portfolios.keys()
            },
            "config": self.config,
        }

        with open(filepath, "w") as f:
            json.dump(export_data, f, indent = 2)

        logger.info(f"Weights exported to {filepath}")

    def import_weights(self, filepath: str):
        """導入權重配置"""
        try:
            with open(filepath, "r") as f:
                import_data = json.load(f)

            # 恢復全局權重
            if "global_weights" in import_data:
                for indicator, weight_value in import_data["global_weights"].items():
                    if indicator in self.global_weights:
                        self.global_weights[indicator].current_weight = weight_value

            # 恢復投資組合權重
            if "portfolio_weights" in import_data:
                for symbol, weights in import_data["portfolio_weights"].items():
                    if symbol not in self.portfolios:
                        self.create_portfolio(symbol)

                    portfolio = self.portfolios[symbol]
                    for indicator, weight_value in weights.items():
                        if indicator in portfolio.weights:
                            portfolio.weights[indicator].current_weight = weight_value

            logger.info(f"Weights imported from {filepath}")

        except Exception as e:
            logger.error(f"Error importing weights from {filepath}: {e}")


# 全局實例
weight_manager = DynamicWeightManager()


# 便利函數
def get_indicator_weights(symbol: str) -> Dict[str, float]:
    """便利函數：獲取指標權重"""
    return weight_manager.get_weights(symbol)

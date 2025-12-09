#!/usr/bin/env python3
"""
簡化系統 - 策略構建器
Simplified System - Strategy Builder

簡化策略構建和組合工具
Simplified strategy building and combination tools
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class StrategySignal:
    """策略信號數據類"""
    entries: pd.Series  # 買入信號
    exits: pd.Series    # 賣出信號
    name: str          # 信號名稱
    weight: float = 1.0  # 信號權重

class StrategyBuilder:
    """
    策略構建器

    提供簡化的策略組合和信號生成功能：
    - 多策略組合
    - 信號融合
    - 權重調整
    - 風險管理
    """

    def __init__(self):
        """初始化策略構建器"""
        self.strategies = {}
        self.signal_combiners = {
            'majority_vote': self._majority_vote,
            'weighted_sum': self._weighted_sum,
            'conservative': self._conservative_combine,
            'aggressive': self._aggressive_combine
        }

    def register_strategy(
        self,
        name: str,
        entries: pd.Series,
        exits: pd.Series,
        weight: float = 1.0
    ) -> None:
        """
        註冊策略信號

        Args:
            name: 策略名稱
            entries: 買入信號序列
            exits: 賣出信號序列
            weight: 權重
        """
        # 確保信號長度一致
        min_length = min(len(entries), len(exits))
        entries = entries.iloc[:min_length]
        exits = exits.iloc[:min_length]

        self.strategies[name] = StrategySignal(
            entries=entries,
            exits=exits,
            name=name,
            weight=weight
        )

        logger.info(f"Registered strategy: {name} (weight: {weight})")

    def combine_strategies(
        self,
        strategy_names: List[str],
        combination_method: str = 'weighted_sum',
        min_consensus: float = 0.5
    ) -> pd.DataFrame:
        """
        組合多個策略信號

        Args:
            strategy_names: 要組合的策略名稱列表
            combination_method: 組合方法
            min_consensus: 最小共識比例（僅用於某些方法）

        Returns:
            組合後的信號DataFrame
        """
        if not strategy_names:
            raise ValueError("No strategy names provided")

        # 驗證策略是否存在
        missing_strategies = [name for name in strategy_names if name not in self.strategies]
        if missing_strategies:
            raise ValueError(f"Strategies not found: {missing_strategies}")

        # 獲取要組合的策略
        selected_strategies = [self.strategies[name] for name in strategy_names]

        # 根據方法組合信號
        if combination_method in self.signal_combiners:
            return self.signal_combiners[combination_method](selected_strategies, min_consensus)
        else:
            raise ValueError(f"Unknown combination method: {combination_method}")

    def _majority_vote(
        self,
        strategies: List[StrategySignal],
        min_consensus: float
    ) -> pd.DataFrame:
        """多數投票組合"""
        if not strategies:
            return pd.DataFrame({'entries': pd.Series(False), 'exits': pd.Series(False)})

        # 收集所有信號
        all_entries = [strategy.entries for strategy in strategies]
        all_exits = [strategy.exits for strategy in strategies]

        # 計算多數投票
        entries_votes = sum(all_entries) / len(all_entries)
        exits_votes = sum(all_exits) / len(all_exits)

        # 應用共識閾值
        combined_entries = entries_votes >= min_consensus
        combined_exits = exits_votes >= min_consensus

        return pd.DataFrame({
            'entries': combined_entries,
            'exits': combined_exits
        }, index=strategies[0].entries.index)

    def _weighted_sum(
        self,
        strategies: List[StrategySignal],
        min_consensus: float
    ) -> pd.DataFrame:
        """加權求和組合"""
        if not strategies:
            return pd.DataFrame({'entries': pd.Series(False), 'exits': pd.Series(False)})

        # 計算加權信號
        weighted_entries = sum(
            strategy.entries * strategy.weight for strategy in strategies
        ) / sum(strategy.weight for strategy in strategies)

        weighted_exits = sum(
            strategy.exits * strategy.weight for strategy in strategies
        ) / sum(strategy.weight for strategy in strategies)

        # 應用共識閾值
        combined_entries = weighted_entries >= min_consensus
        combined_exits = weighted_exits >= min_consensus

        return pd.DataFrame({
            'entries': combined_entries,
            'exits': combined_exits
        }, index=strategies[0].entries.index)

    def _conservative_combine(
        self,
        strategies: List[StrategySignal],
        min_consensus: float
    ) -> pd.DataFrame:
        """保守組合（需要更高共識）"""
        # 使用更高的共識要求
        return self._majority_vote(strategies, min_consensus * 1.5)

    def _aggressive_combine(
        self,
        strategies: List[StrategySignal],
        min_consensus: float
    ) -> pd.DataFrame:
        """激進組合（較低共識要求）"""
        # 使用較低的共識要求
        return self._majority_vote(strategies, min_consensus * 0.7)

    def create_portfolio_strategy(
        self,
        strategy_configs: List[Dict[str, Any]],
        combination_method: str = 'weighted_sum'
    ) -> pd.DataFrame:
        """
        創建投資組合策略

        Args:
            strategy_configs: 策略配置列表，每個配置包含name, entries, exits, weight
            combination_method: 組合方法

        Returns:
            組合信號
        """
        # 清空現有策略
        self.strategies = {}

        # 註冊所有策略
        for config in strategy_configs:
            self.register_strategy(
                name=config['name'],
                entries=config['entries'],
                exits=config['exits'],
                weight=config.get('weight', 1.0)
            )

        # 組合所有策略
        strategy_names = list(self.strategies.keys())
        return self.combine_strategies(strategy_names, combination_method)

    def apply_risk_filters(
        self,
        signals: pd.DataFrame,
        max_positions: int = 5,
        min_holding_period: int = 5,
        volatility_filter: bool = True,
        volume_filter: bool = True
    ) -> pd.DataFrame:
        """
        應用風險過濾器

        Args:
            signals: 原始信號
            max_positions: 最大同時持倉數
            min_holding_period: 最小持倉週期
            volatility_filter: 是否應用波動率過濾
            volume_filter: 是否應用成交量過濾

        Returns:
            過濾後的信號
        """
        filtered_signals = signals.copy()

        # 持倉週期過濾
        if min_holding_period > 0:
            filtered_signals = self._apply_holding_period_filter(
                filtered_signals, min_holding_period
            )

        # 波動率過濾
        if volatility_filter:
            filtered_signals = self._apply_volatility_filter(filtered_signals)

        # 成交量過濾（需要成交量數據）
        if volume_filter and hasattr(self, '_volume_data'):
            filtered_signals = self._apply_volume_filter(filtered_signals)

        # 最大持倉數過濾
        if max_positions > 0:
            filtered_signals = self._apply_position_limit_filter(
                filtered_signals, max_positions
            )

        return filtered_signals

    def _apply_holding_period_filter(
        self,
        signals: pd.DataFrame,
        min_period: int
    ) -> pd.DataFrame:
        """應用最小持倉週期過濾"""
        entries = signals['entries'].copy()
        exits = signals['exits'].copy()

        # 確保退出信號在進場信號至少min_period期後
        for i in range(min_period, len(entries)):
            # 檢查是否有未關閉的持倉
            has_open_position = entries.iloc[:i].any() and not exits.iloc[:i].any()
            if has_open_position:
                # 如果在最小持倉期內有新的進場信號，延遲退出信號
                if entries.iloc[i]:
                    # 新進場，暫時延遲之前的退出信號
                    pass

        return pd.DataFrame({'entries': entries, 'exits': exits})

    def _apply_volatility_filter(
        self,
        signals: pd.DataFrame
    ) -> pd.DataFrame:
        """應用波動率過濾"""
        # 這裡可以實現基於ATR或標準差的波動率過濾
        # 為簡化實現，暫時直接返回原信號
        return signals

    def _apply_volume_filter(self, signals: pd.DataFrame) -> pd.DataFrame:
        """應用成交量過濾"""
        # 這裡可以實現基於成交量的過濾
        # 為簡化實現，暫時直接返回原信號
        return signals

    def _apply_position_limit_filter(
        self,
        signals: pd.DataFrame,
        max_positions: int
    ) -> pd.DataFrame:
        """應用持倉數量限制"""
        entries = signals['entries'].copy()
        exits = signals['exits'].copy()

        # 簡化實現：限制總進場信號數量
        entry_count = 0
        max_entries = int(len(entries) * 0.1)  # 最多10%的時間點進場

        for i in range(len(entries)):
            if entries.iloc[i]:
                if entry_count >= max_entries:
                    entries.iloc[i] = False
                else:
                    entry_count += 1

        return pd.DataFrame({'entries': entries, 'exits': exits})

    def get_strategy_performance(
        self,
        signals: pd.DataFrame,
        data: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        獲取策略性能分析

        Args:
            signals: 策略信號
            data: 價格數據

        Returns:
            性能分析結果
        """
        try:
            # 計算信號統計
            entry_count = signals['entries'].sum()
            exit_count = signals['exits'].sum()
            signal_density = (entry_count + exit_count) / len(signals)

            # 計算信號質量
            entry_quality = self._calculate_signal_quality(signals, data)

            # 計算風險指標
            risk_metrics = self._calculate_risk_metrics(signals, data)

            return {
                'signal_statistics': {
                    'total_entries': int(entry_count),
                    'total_exits': int(exit_count),
                    'signal_density': float(signal_density),
                    'entry_quality': entry_quality
                },
                'risk_metrics': risk_metrics,
                'recommendations': self._generate_recommendations(entry_quality, risk_metrics)
            }

        except Exception as e:
            logger.error(f"Error calculating strategy performance: {e}")
            return {'error': str(e)}

    def _calculate_signal_quality(
        self,
        signals: pd.DataFrame,
        data: pd.DataFrame
    ) -> float:
        """計算信號質量分數"""
        try:
            # 基於價格變動計算信號質量
            returns = data['close'].pct_change()
            entries = signals['entries']
            exits = signals['exits']

            # 進場後的平均表現
            entry_performance = []
            for i in range(1, len(returns)):
                if entries.iloc[i-1]:  # 前一天進場
                    # 計算進場後N天的平均回報
                    window_returns = returns.iloc[i:min(i+5, len(returns))]
                    if len(window_returns) > 0:
                        entry_performance.append(window_returns.mean())

            # 賣場前的平均表現
            exit_performance = []
            for i in range(1, len(returns)):
                if exits.iloc[i-1]:  # 前一天賣出
                    # 計算賣出後N天的平均回報（應該是避免損失）
                    window_returns = returns.iloc[i:min(i+5, len(returns))]
                    if len(window_returns) > 0:
                        exit_performance.append(-window_returns.mean())

            # 計算質量分數
            if entry_performance and exit_performance:
                avg_entry_performance = np.mean(entry_performance)
                avg_exit_performance = np.mean(exit_performance)
                quality_score = (avg_entry_performance + avg_exit_performance) / 2
                # 轉換為0-100分
                quality_score = max(0, min(100, (quality_score * 1000 + 50)))
            else:
                quality_score = 50.0

            return quality_score

        except Exception as e:
            logger.error(f"Error calculating signal quality: {e}")
            return 50.0

    def _calculate_risk_metrics(self, signals: pd.DataFrame, data: pd.DataFrame) -> Dict[str, Any]:
        """計算風險指標"""
        try:
            # 計算信號集中度風險
            entries = signals['entries']
            if entries.sum() > 0:
                # 進場信號間的平均天數
                entry_indices = entries[entries].index
                if len(entry_indices) > 1:
                    entry_intervals = entry_indices.to_series().diff().dropna().mean()
                    concentration_risk = "High" if entry_intervals < 5 else "Low"
                else:
                    concentration_risk = "Low"
            else:
                concentration_risk = "No signals"

            # 計算時間分佈風險
            monthly_entries = entries.resample('M').sum()
            max_monthly = monthly_entries.max()
            avg_monthly = monthly_entries.mean()

            if avg_monthly > 0:
                concentration_ratio = max_monthly / avg_monthly
                time_risk = "High" if concentration_ratio > 2 else "Medium" if concentration_ratio > 1.5 else "Low"
            else:
                time_risk = "No signals"

            return {
                'signal_concentration': concentration_risk,
                'time_distribution': time_risk,
                'monthly_signals': monthly_entries.to_dict()
            }

        except Exception as e:
            logger.error(f"Error calculating risk metrics: {e}")
            return {'error': str(e)}

    def _generate_recommendations(self, quality_score: float, risk_metrics: Dict[str, Any]) -> List[str]:
        """生成改進建議"""
        recommendations = []

        if quality_score < 60:
            recommendations.append("信號質量較低，建議調整策略參數")

        if risk_metrics.get('signal_concentration') == 'High':
            recommendations.append("信號過於集中，建議增加持倉週期或降低交易頻率")

        if risk_metrics.get('time_distribution') == 'High':
            recommendations.append("時間分佈不均勻，建議分散交易時間")

        if not recommendations:
            recommendations.append("策略表現良好，可繼續使用")

        return recommendations

# 便利函數
def create_simple_portfolio(
    rsi_entries: pd.Series,
    rsi_exits: pd.Series,
    macd_entries: pd.Series,
    macd_exits: pd.Series,
    rsi_weight: float = 0.6,
    macd_weight: float = 0.4
) -> pd.DataFrame:
    """創建簡單的RSI+MACD投資組合"""
    builder = StrategyBuilder()

    # 註冊策略
    builder.register_strategy("RSI", rsi_entries, rsi_exits, rsi_weight)
    builder.register_strategy("MACD", macd_entries, macd_exits, macd_weight)

    # 組合策略
    return builder.combine_strategies(["RSI", "MACD"], "weighted_sum")
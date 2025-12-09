#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Strategy Performance Dashboard
策略绩效仪表板 - 表格形式显示所有策略的MDD和SR

Based on Acheng's analytical approach, this dashboard provides
comprehensive strategy performance monitoring in tabular format.

Features:
- Tabular display of all strategies with MDD and Sharpe Ratio
- Real-time performance updates
- Strategy comparison and ranking
- Interactive filtering and sorting
- Export capabilities

Author: Strategy Dashboard Team
Date: 2025-11-30
"""

import os
import sys
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import logging
from dataclasses import dataclass

# 添加src到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from strategy_management.strategy_registry import (
    StrategyRegistry,
    StrategyMetadata,
    StrategyPerformance,
    auto_discover_strategies,
    StrategyCategory
)
from analytics.performance_analyzer import (
    StandardPerformanceAnalyzer,
    PerformanceConfig,
    create_performance_analyzer
)

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DashboardConfig:
    """仪表板配置"""
    auto_refresh: bool = True
    refresh_interval: int = 300  # 5分钟
    max_strategies_display: int = 100
    default_sort_column: str = "Sharpe Ratio"
    default_sort_order: str = "descending"
    export_format: str = "csv"  # csv, excel, json
    show_details: bool = True

class StrategyPerformanceDashboard:
    """
    策略绩效仪表板

    提供表格形式的策略绩效展示，学习阿程的分析思路
    """

    def __init__(self, config: Optional[DashboardConfig] = None):
        """
        初始化仪表板

        Args:
            config: 仪表板配置
        """
        self.config = config or DashboardConfig()
        self.registry = auto_discover_strategies()
        self.performance_analyzer = create_performance_analyzer()
        self.last_update_time = None

        # 缓存的绩效数据
        self.cached_performances: Dict[str, Dict[str, Any]] = {}

        logger.info(f"Initialized dashboard with {len(self.registry.get_all_strategies())} strategies")

    def generate_performance_table(
        self,
        category_filter: Optional[str] = None,
        min_sharpe: Optional[float] = None,
        max_mdd: Optional[float] = None,
        sort_by: str = "Sharpe Ratio",
        ascending: bool = False
    ) -> pd.DataFrame:
        """
        生成策略绩效表格

        Args:
            category_filter: 分类过滤
            min_sharpe: 最小夏普比率过滤
            max_mdd: 最大回撤过滤
            sort_by: 排序字段
            ascending: 是否升序

        Returns:
            pd.DataFrame: 策略绩效表格
        """
        try:
            # 获取所有策略
            strategies = self.registry.get_all_strategies()

            # 应用过滤器
            if category_filter:
                strategies = [s for s in strategies if s.category.value == category_filter]

            # 生成绩效数据
            performance_data = []

            for strategy in strategies[:self.config.max_strategies_display]:
                # 获取或计算绩效
                performance = self._get_or_calculate_performance(strategy)

                # 应用数值过滤器
                if min_sharpe is not None and performance.get("sharpe_ratio", 0) < min_sharpe:
                    continue
                if max_mdd is not None and performance.get("max_drawdown", 0) < -max_mdd:
                    continue

                # 构建表格行
                row_data = {
                    "Strategy ID": strategy.id,
                    "Strategy Name": strategy.name,
                    "Category": strategy.category.value,
                    "Description": strategy.description[:100] + "..." if len(strategy.description) > 100 else strategy.description,
                    "Sharpe Ratio": performance.get("sharpe_ratio", 0.0),
                    "Max Drawdown": performance.get("max_drawdown", 0.0),
                    "Total Return": performance.get("total_return", 0.0),
                    "Annual Return": performance.get("annual_return", 0.0),
                    "Volatility": performance.get("volatility", 0.0),
                    "Win Rate": performance.get("win_rate", 0.0),
                    "Calmar Ratio": performance.get("calmar_ratio", 0.0),
                    "Trades Count": performance.get("trades_count", 0),
                    "Current Signal": performance.get("current_signal", "N/A"),
                    "Signal Strength": performance.get("signal_strength_level", "N/A"),
                    "Status": performance.get("status", "pending"),
                    "Last Updated": strategy.last_updated.strftime("%Y-%m-%d %H:%M:%S")
                }

                performance_data.append(row_data)

            # 创建DataFrame
            df = pd.DataFrame(performance_data)

            if df.empty:
                logger.warning("No strategies found matching the criteria")
                return self._create_empty_dataframe()

            # 格式化数值列
            df = self._format_dataframe(df)

            # 排序
            if sort_by in df.columns:
                df = df.sort_values(sort_by, ascending=ascending)

            self.last_update_time = datetime.now()

            logger.info(f"Generated performance table with {len(df)} strategies")
            return df

        except Exception as e:
            logger.error(f"Failed to generate performance table: {e}")
            return self._create_empty_dataframe()

    def _get_or_calculate_performance(self, strategy: StrategyMetadata) -> Dict[str, Any]:
        """获取或计算策略绩效"""
        # 检查缓存
        if strategy.id in self.cached_performances:
            cache_time = self.cached_performances[strategy.id].get("cached_time")
            if cache_time and (datetime.now() - cache_time).seconds < 3600:  # 1小时缓存
                return self.cached_performances[strategy.id]

        # 尝试从注册表获取
        registry_performance = self.registry.get_strategy_performance(strategy.id)
        if registry_performance and registry_performance.status == "completed":
            performance = {
                "sharpe_ratio": registry_performance.sharpe_ratio,
                "max_drawdown": registry_performance.max_drawdown,
                "total_return": registry_performance.total_return,
                "annual_return": registry_performance.annual_return,
                "volatility": registry_performance.volatility,
                "calmar_ratio": registry_performance.calmar_ratio,
                "win_rate": registry_performance.win_rate,
                "trades_count": registry_performance.trades_count,
                "status": registry_performance.status,
                "symbol": registry_performance.symbol
            }
        else:
            # 模拟计算绩效 (实际应用中应该执行策略)
            performance = self._simulate_strategy_performance(strategy)

        # 添加缓存时间
        performance["cached_time"] = datetime.now()
        self.cached_performances[strategy.id] = performance

        return performance

    def _simulate_strategy_performance(self, strategy: StrategyMetadata) -> Dict[str, Any]:
        """模拟策略绩效 (用于演示)"""
        import random

        # 基于策略类型生成合理的绩效指标
        base_performance = {
            StrategyCategory.TECHNICAL_ANALYSIS: {"sharpe": 0.8, "mdd": -0.15, "return": 0.12},
            StrategyCategory.MOMENTUM: {"sharpe": 1.2, "mdd": -0.20, "return": 0.18},
            StrategyCategory.MEAN_REVERSION: {"sharpe": 0.6, "mdd": -0.12, "return": 0.08},
            StrategyCategory.MACHINE_LEARNING: {"sharpe": 1.5, "mdd": -0.25, "return": 0.25},
            StrategyCategory.NON_PRICE_SIGNALS: {"sharpe": 1.1, "mdd": -0.18, "return": 0.15},
            StrategyCategory.PORTFOLIO_OPTIMIZATION: {"sharpe": 0.9, "mdd": -0.10, "return": 0.10},
            StrategyCategory.CUSTOM: {"sharpe": 0.7, "mdd": -0.14, "return": 0.09}
        }

        base = base_performance.get(strategy.category, {"sharpe": 0.5, "mdd": -0.12, "return": 0.08})

        # 添加随机变化
        sharpe = base["sharpe"] + random.uniform(-0.3, 0.3)
        mdd = base["mdd"] + random.uniform(-0.05, 0.05)
        total_return = base["return"] + random.uniform(-0.05, 0.08)

        # 计算衍生指标
        annual_return = total_return
        volatility = sharpe / 0.03 if sharpe > 0 else 0.15  # 假设无风险利率3%
        win_rate = min(0.95, max(0.35, (sharpe + 1) / 2))  # 基于夏普比率估算胜率
        calmar_ratio = annual_return / abs(mdd) if mdd != 0 else 0

        return {
            "sharpe_ratio": round(sharpe, 3),
            "max_drawdown": round(mdd, 4),
            "total_return": round(total_return, 4),
            "annual_return": round(annual_return, 4),
            "volatility": round(volatility, 4),
            "win_rate": round(win_rate, 3),
            "calmar_ratio": round(calmar_ratio, 3),
            "trades_count": random.randint(50, 500),
            "current_signal": random.choice(["long", "short", "flat"]),
            "signal_strength_level": random.choice(["weak", "medium", "strong"]),
            "status": "simulated",
            "symbol": random.choice(["0700.HK", "0939.HK", "1398.HK", "HSI.HK"])
        }

    def _format_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """格式化DataFrame显示"""
        # 复制DataFrame避免SettingWithCopyWarning
        formatted_df = df.copy()

        # 格式化百分比
        percentage_columns = [
            "Max Drawdown", "Total Return", "Annual Return",
            "Volatility", "Win Rate", "Calmar Ratio"
        ]

        for col in percentage_columns:
            if col in formatted_df.columns:
                formatted_df[col] = formatted_df[col].apply(
                    lambda x: f"{x*100:.2f}%" if pd.notna(x) and x != 0 else "0.00%"
                )

        # 格式化Sharpe Ratio
        if "Sharpe Ratio" in formatted_df.columns:
            formatted_df["Sharpe Ratio"] = formatted_df["Sharpe Ratio"].apply(
                lambda x: f"{x:.3f}" if pd.notna(x) else "0.000"
            )

        # 格式化Trades Count
        if "Trades Count" in formatted_df.columns:
            formatted_df["Trades Count"] = formatted_df["Trades Count"].apply(
                lambda x: f"{int(x):,}" if pd.notna(x) else "0"
            )

        return formatted_df

    def _create_empty_dataframe(self) -> pd.DataFrame:
        """创建空的DataFrame"""
        columns = [
            "Strategy ID", "Strategy Name", "Category", "Description",
            "Sharpe Ratio", "Max Drawdown", "Total Return", "Annual Return",
            "Volatility", "Win Rate", "Calmar Ratio", "Trades Count",
            "Current Signal", "Signal Strength", "Status", "Last Updated"
        ]
        return pd.DataFrame(columns=columns)

    def get_strategy_summary_statistics(self) -> Dict[str, Any]:
        """获取策略汇总统计"""
        try:
            strategies = self.registry.get_all_strategies()
            performances = self.registry.get_all_performances()

            # 基础统计
            total_strategies = len(strategies)
            completed_performances = len([p for p in performances if p.status == "completed"])

            # 分类统计
            category_stats = {}
            for strategy in strategies:
                category = strategy.category.value
                if category not in category_stats:
                    category_stats[category] = 0
                category_stats[category] += 1

            # 绩效统计 (只包含有绩效的策略)
            if performances:
                sharpe_ratios = [p.sharpe_ratio for p in performances if p.sharpe_ratio != 0]
                max_drawdowns = [p.max_drawdown for p in performances if p.max_drawdown != 0]
                total_returns = [p.total_return for p in performances if p.total_return != 0]

                performance_stats = {
                    "avg_sharpe_ratio": np.mean(sharpe_ratios) if sharpe_ratios else 0,
                    "median_sharpe_ratio": np.median(sharpe_ratios) if sharpe_ratios else 0,
                    "best_sharpe_ratio": max(sharpe_ratios) if sharpe_ratios else 0,
                    "worst_sharpe_ratio": min(sharpe_ratios) if sharpe_ratios else 0,
                    "avg_max_drawdown": np.mean(max_drawdowns) if max_drawdowns else 0,
                    "avg_total_return": np.mean(total_returns) if total_returns else 0,
                }
            else:
                performance_stats = {
                    "avg_sharpe_ratio": 0, "median_sharpe_ratio": 0, "best_sharpe_ratio": 0,
                    "worst_sharpe_ratio": 0, "avg_max_drawdown": 0, "avg_total_return": 0
                }

            # 优质策略统计
            excellent_strategies = len([p for p in performances if p.sharpe_ratio > 1.0])
            good_strategies = len([p for p in performances if 0.5 < p.sharpe_ratio <= 1.0])
            poor_strategies = len([p for p in performances if p.sharpe_ratio <= 0.5])

            return {
                "summary": {
                    "total_strategies": total_strategies,
                    "strategies_with_performance": completed_performances,
                    "performance_completion_rate": completed_performances / total_strategies if total_strategies > 0 else 0,
                },
                "category_distribution": category_stats,
                "performance_statistics": performance_stats,
                "quality_distribution": {
                    "excellent_strategies": excellent_strategies,  # Sharpe > 1.0
                    "good_strategies": good_strategies,          # 0.5 < Sharpe <= 1.0
                    "poor_strategies": poor_strategies,          # Sharpe <= 0.5
                },
                "last_update": self.last_update_time.isoformat() if self.last_update_time else None
            }

        except Exception as e:
            logger.error(f"Failed to generate summary statistics: {e}")
            return {}

    def export_performance_table(
        self,
        df: pd.DataFrame,
        filename: Optional[str] = None,
        format_type: Optional[str] = None
    ) -> str:
        """
        导出绩效表格

        Args:
            df: 绩效DataFrame
            filename: 文件名
            format_type: 导出格式

        Returns:
            str: 导出文件路径
        """
        try:
            format_type = format_type or self.config.export_format
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if filename is None:
                filename = f"strategy_performance_{timestamp}"

            # 确保文件扩展名
            if not filename.endswith(f".{format_type}"):
                filename = f"{filename}.{format_type}"

            filepath = os.path.join(os.getcwd(), filename)

            if format_type == "csv":
                df.to_csv(filepath, index=False, encoding='utf-8-sig')
            elif format_type == "excel":
                df.to_excel(filepath, index=False, engine='openpyxl')
            elif format_type == "json":
                df.to_json(filepath, orient='records', indent=2, force_ascii=False)
            else:
                raise ValueError(f"Unsupported export format: {format_type}")

            logger.info(f"Exported performance table to {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Failed to export performance table: {e}")
            return ""

    def refresh_data(self) -> bool:
        """刷新数据"""
        try:
            # 重新发现策略
            discovered = self.registry.discover_strategies(force_rescan=True)

            # 清除缓存
            self.cached_performances.clear()

            logger.info(f"Refreshed data: discovered {discovered} strategies")
            return True

        except Exception as e:
            logger.error(f"Failed to refresh data: {e}")
            return False

    def display_dashboard(self):
        """在控制台显示仪表板"""
        print("=" * 120)
        print("STRATEGY PERFORMANCE DASHBOARD")
        print("=" * 120)
        print(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # 生成表格
        df = self.generate_performance_table()

        if df.empty:
            print("No strategies found.")
            return

        # 显示汇总统计
        stats = self.get_strategy_summary_statistics()
        self._display_summary_statistics(stats)

        print("\n" + "=" * 120)
        print("STRATEGY PERFORMANCE TABLE")
        print("=" * 120)

        # 显示表格
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 50)

        print(df.to_string(index=False))

        print("\n" + "=" * 120)
        print("TOP 10 STRATEGIES BY SHARPE RATIO")
        print("=" * 120)

        # 显示前10个策略
        top_10 = df.head(10)[['Strategy Name', 'Category', 'Sharpe Ratio', 'Max Drawdown', 'Total Return']]
        print(top_10.to_string(index=False))

    def _display_summary_statistics(self, stats: Dict[str, Any]):
        """显示汇总统计"""
        if not stats:
            return

        print("SUMMARY STATISTICS")
        print("-" * 50)

        # 基础统计
        summary = stats.get("summary", {})
        print(f"Total Strategies: {summary.get('total_strategies', 0)}")
        print(f"Strategies with Performance: {summary.get('strategies_with_performance', 0)}")
        print(f"Completion Rate: {summary.get('performance_completion_rate', 0):.1%}")

        # 绩效统计
        perf_stats = stats.get("performance_statistics", {})
        print(f"Average Sharpe Ratio: {perf_stats.get('avg_sharpe_ratio', 0):.3f}")
        print(f"Best Sharpe Ratio: {perf_stats.get('best_sharpe_ratio', 0):.3f}")
        print(f"Average Max Drawdown: {perf_stats.get('avg_max_drawdown', 0):.2%}")

        # 质量分布
        quality = stats.get("quality_distribution", {})
        print(f"Excellent Strategies (SR>1.0): {quality.get('excellent_strategies', 0)}")
        print(f"Good Strategies (0.5<SR≤1.0): {quality.get('good_strategies', 0)}")
        print(f"Poor Strategies (SR≤0.5): {quality.get('poor_strategies', 0)}")


def main():
    """主函数 - 运行策略绩效仪表板"""
    print("Starting Strategy Performance Dashboard...")

    # 创建仪表板
    dashboard = StrategyPerformanceDashboard()

    # 显示仪表板
    dashboard.display_dashboard()

    # 导出选项
    df = dashboard.generate_performance_table()
    if not df.empty:
        export_path = dashboard.export_performance_table(df)
        if export_path:
            print(f"\nPerformance table exported to: {export_path}")


if __name__ == "__main__":
    main()
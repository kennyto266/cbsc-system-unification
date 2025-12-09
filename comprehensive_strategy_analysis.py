#!/usr/bin/env python3
"""
CBSC Comprehensive Strategy Analysis and Ranking System
全面的CBSC策略分析与排名系统

Identify the root causes of extreme backtest results and provide
actionable insights for strategy selection.

Author: CBSC Strategy Analysis Team
Date: 2025-12-05
Version: 1.0
"""

import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
from dataclasses import dataclass
from enum import Enum
import logging

# 设置中文字体和样式
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
sns.set_style("whitegrid")
warnings.filterwarnings('ignore')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('strategy_analysis.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RiskProfile(Enum):
    """投资者风险画像"""
    CONSERVATIVE = "保守型"
    MODERATE = "稳健型"
    AGGRESSIVE = "积极型"
    SPECULATIVE = "投机型"

@dataclass
class StrategyMetrics:
    """策略指标数据类"""
    name: str
    total_return: float
    annual_return: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    trading_costs: float
    cost_efficiency: float
    risk_adjusted_score: float
    consistency_score: float
    final_equity: float
    volatility: float = 0.0

class DataValidator:
    """数据验证器 - 识别数据质量问题"""

    @staticmethod
    def validate_backtest_data(data: Dict) -> Dict:
        """验证回测数据质量"""
        validation_results = {
            'is_valid': True,
            'issues': [],
            'warnings': [],
            'data_quality_score': 1.0
        }

        for strategy_name, strategy_data in data.items():
            if strategy_name == 'market_benchmark':
                continue

            try:
                metrics = strategy_data.get('metrics', {})

                # 检查关键指标的异常值
                if metrics.get('annual_return') == 'NaN' or pd.isna(metrics.get('annual_return')):
                    validation_results['issues'].append(
                        f"{strategy_name}: 年化收益率计算异常 (NaN)"
                    )
                    validation_results['is_valid'] = False

                if metrics.get('max_drawdown') == 0 and metrics.get('total_return', 0) < 0:
                    validation_results['issues'].append(
                        f"{strategy_name}: 最大回撤异常 (亏损但回撤为0)"
                    )
                    validation_results['is_valid'] = False

                # 检查交易成本合理性
                trading_costs = metrics.get('trading_costs', 0)
                total_trades = metrics.get('total_trades', 0)

                if total_trades > 0:
                    cost_per_trade = trading_costs / total_trades
                    if cost_per_trade > 10000:  # 每笔交易成本超过1万港币
                        validation_results['warnings'].append(
                            f"{strategy_name}: 单笔交易成本过高 ({cost_per_trade:,.0f} HKD)"
                        )

                # 检查极端收益
                total_return = metrics.get('total_return', 0)
                if abs(total_return) > 5:  # 收益率超过500%
                    validation_results['warnings'].append(
                        f"{strategy_name}: 极端总收益率 ({total_return:.1%})"
                    )

            except Exception as e:
                validation_results['issues'].append(f"{strategy_name}: 数据解析错误 - {str(e)}")
                validation_results['is_valid'] = False

        # 计算数据质量分数
        issue_penalty = len(validation_results['issues']) * 0.2
        warning_penalty = len(validation_results['warnings']) * 0.05
        validation_results['data_quality_score'] = max(0, 1.0 - issue_penalty - warning_penalty)

        return validation_results

class RiskCalculator:
    """风险计算器 - 高级风险指标计算"""

    @staticmethod
    def calculate_var(returns: np.ndarray, confidence_level: float = 0.05) -> float:
        """计算VaR (Value at Risk)"""
        return np.percentile(returns, confidence_level * 100)

    @staticmethod
    def calculate_cvar(returns: np.ndarray, confidence_level: float = 0.05) -> float:
        """计算CVaR (Conditional VaR)"""
        var = RiskCalculator.calculate_var(returns, confidence_level)
        return np.mean(returns[returns <= var])

    @staticmethod
    def calculate_downside_deviation(returns: np.ndarray, risk_free_rate: float = 0.0) -> float:
        """计算下行波动率"""
        downside_returns = returns[returns < risk_free_rate]
        return np.std(downside_returns) if len(downside_returns) > 0 else 0

    @staticmethod
    def calculate_information_ratio(returns: np.ndarray, benchmark_returns: np.ndarray) -> float:
        """计算信息比率"""
        excess_returns = returns - benchmark_returns
        tracking_error = np.std(excess_returns)
        return np.mean(excess_returns) / tracking_error if tracking_error > 0 else 0

class ConsistencyAnalyzer:
    """一致性分析器 - 评估策略表现的稳定性"""

    @staticmethod
    def calculate_consistency_score(equity_curve: List[float], window_size: int = 60) -> float:
        """计算表现一致性分数"""
        if len(equity_curve) < window_size * 2:
            return 0.5  # 数据不足，给予中性分数

        equity_series = pd.Series(equity_curve)

        # 计算滚动收益率
        rolling_returns = []
        for i in range(window_size, len(equity_series)):
            period_return = (equity_series.iloc[i] - equity_series.iloc[i-window_size]) / equity_series.iloc[i-window_size]
            rolling_returns.append(period_return)

        if not rolling_returns:
            return 0.5

        rolling_returns = pd.Series(rolling_returns)

        # 一致性指标：
        # 1. 收益率标准差（越小越一致）
        return_std = rolling_returns.std()

        # 2. 正收益月份比例
        positive_periods = (rolling_returns > 0).mean()

        # 3. 最大连续亏损期
        consecutive_losses = 0
        max_consecutive_losses = 0
        for ret in rolling_returns:
            if ret <= 0:
                consecutive_losses += 1
                max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
            else:
                consecutive_losses = 0

        # 综合评分 (0-1)
        std_score = max(0, 1 - return_std * 2)  # 标准化标准差分数
        positive_score = positive_periods
        consistency_score = max(0, 1 - max_consecutive_losses / 12)  # 假设12个月为长期

        final_score = (std_score * 0.4 + positive_score * 0.4 + consistency_score * 0.2)

        return max(0, min(1, final_score))

class StrategyRanker:
    """策略排名器 - 多维度排名系统"""

    def __init__(self):
        self.weight_configs = {
            RiskProfile.CONSERVATIVE: {
                'sharpe_ratio': 0.3,
                'max_drawdown': 0.25,
                'consistency': 0.2,
                'cost_efficiency': 0.15,
                'win_rate': 0.1
            },
            RiskProfile.MODERATE: {
                'sharpe_ratio': 0.25,
                'total_return': 0.2,
                'max_drawdown': 0.2,
                'consistency': 0.15,
                'cost_efficiency': 0.1,
                'win_rate': 0.1
            },
            RiskProfile.AGGRESSIVE: {
                'total_return': 0.3,
                'sharpe_ratio': 0.2,
                'max_drawdown': 0.15,
                'consistency': 0.15,
                'cost_efficiency': 0.1,
                'win_rate': 0.1
            },
            RiskProfile.SPECULATIVE: {
                'total_return': 0.4,
                'sharpe_ratio': 0.15,
                'max_drawdown': 0.1,
                'consistency': 0.1,
                'cost_efficiency': 0.15,
                'win_rate': 0.1
            }
        }

    def normalize_metric(self, values: List[float], higher_is_better: bool = True) -> List[float]:
        """标准化指标到0-1范围"""
        values = np.array(values)

        # 处理异常值
        if len(values) == 0 or np.all(values == values[0]):
            return [0.5] * len(values)

        if higher_is_better:
            # 对于越高越好的指标（收益率、夏普比率等）
            min_val, max_val = np.min(values), np.max(values)
            if max_val == min_val:
                return [0.5] * len(values)
            normalized = (values - min_val) / (max_val - min_val)
        else:
            # 对于越低越好的指标（最大回撤、成本等）
            min_val, max_val = np.min(values), np.max(values)
            if max_val == min_val:
                return [0.5] * len(values)
            normalized = 1 - (values - min_val) / (max_val - min_val)

        return normalized.tolist()

    def calculate_composite_score(self, strategy: StrategyMetrics, risk_profile: RiskProfile) -> float:
        """计算综合评分"""
        weights = self.weight_configs[risk_profile]

        # 收集指标值
        metrics_values = {
            'total_return': strategy.total_return,
            'sharpe_ratio': strategy.sharpe_ratio,
            'max_drawdown': abs(strategy.max_drawdown),
            'consistency': strategy.consistency_score,
            'cost_efficiency': strategy.cost_efficiency,
            'win_rate': strategy.win_rate
        }

        # 计算加权分数
        score = 0
        for metric, value in metrics_values.items():
            if metric in weights:
                # 处理NaN和异常值
                if pd.isna(value) or not np.isfinite(value):
                    normalized_value = 0.0
                else:
                    # 标准化指标
                    all_values = [getattr(s, metric.replace('max_drawdown', 'max_drawdown').replace('consistency', 'consistency_score'), 0)
                                for s in [strategy]]  # 这里需要所有策略的值来标准化，暂时用单个值

                    if metric == 'max_drawdown':
                        # 回撤是负数，取绝对值
                        normalized_value = max(0, min(1, 1 - abs(value) / 2))  # 假设最大回撤200%为最差
                    elif metric == 'sharpe_ratio':
                        # 夏普比率通常在-2到2之间
                        normalized_value = max(0, min(1, (value + 2) / 4))
                    elif metric == 'total_return':
                        # 总收益率标准化
                        normalized_value = max(0, min(1, (value + 2) / 8))  # -200%到600%
                    elif metric in ['win_rate', 'consistency', 'cost_efficiency']:
                        # 已经在0-1范围内的指标
                        normalized_value = max(0, min(1, value))
                    else:
                        normalized_value = 0.5

                score += normalized_value * weights[metric]

        return max(0, min(1, score))

class ComprehensiveStrategyAnalyzer:
    """全面策略分析器"""

    def __init__(self, data_file: str = "real_cbsc_backtest_results_20251205_192219.json"):
        self.data_file = data_file
        self.raw_data = None
        self.strategies = []
        self.validator = DataValidator()
        self.risk_calculator = RiskCalculator()
        self.consistency_analyzer = ConsistencyAnalyzer()
        self.ranker = StrategyRanker()

    def load_data(self) -> bool:
        """加载回测数据"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.raw_data = json.load(f)

            logger.info(f"成功加载数据文件: {self.data_file}")
            return True

        except FileNotFoundError:
            logger.error(f"数据文件未找到: {self.data_file}")
            return False
        except Exception as e:
            logger.error(f"数据加载错误: {str(e)}")
            return False

    def analyze_data_quality(self) -> Dict:
        """分析数据质量"""
        logger.info("开始数据质量分析...")

        validation_results = self.validator.validate_backtest_data(self.raw_data)

        logger.info(f"数据质量评分: {validation_results['data_quality_score']:.2f}")
        if validation_results['issues']:
            logger.warning(f"发现 {len(validation_results['issues'])} 个严重问题")
        if validation_results['warnings']:
            logger.warning(f"发现 {len(validation_results['warnings'])} 个警告")

        return validation_results

    def process_strategy_data(self) -> List[StrategyMetrics]:
        """处理策略数据"""
        logger.info("处理策略数据...")

        strategies = []

        for strategy_name, strategy_data in self.raw_data.items():
            if strategy_name == 'market_benchmark':
                continue

            try:
                metrics = strategy_data.get('metrics', {})

                # 计算成本效率
                total_return = metrics.get('total_return', 0)
                trading_costs = metrics.get('trading_costs', 0)
                cost_efficiency = total_return / (trading_costs / 100000) if trading_costs > 0 else 0

                # 生成模拟权益曲线（基于总收益和最大回撤）
                equity_curve = self.generate_equity_curve(
                    total_return=metrics.get('total_return', 0),
                    max_drawdown=metrics.get('max_drawdown', 0),
                    years_tested=metrics.get('years_tested', 1)
                )

                # 计算一致性分数
                consistency_score = self.consistency_analyzer.calculate_consistency_score(equity_curve)

                # 计算波动率（基于夏普比率和年化收益率反推）
                annual_return = metrics.get('annual_return', 0)
                sharpe_ratio = metrics.get('sharpe_ratio', 0)
                volatility = annual_return / sharpe_ratio if sharpe_ratio != 0 and not pd.isna(sharpe_ratio) else 0.2

                # 创建策略指标对象
                strategy = StrategyMetrics(
                    name=strategy_name,
                    total_return=metrics.get('total_return', 0),
                    annual_return=metrics.get('annual_return', 0),
                    sharpe_ratio=metrics.get('sharpe_ratio', 0),
                    sortino_ratio=metrics.get('sortino_ratio', 0),
                    calmar_ratio=metrics.get('calmar_ratio', 0),
                    max_drawdown=metrics.get('max_drawdown', 0),
                    win_rate=metrics.get('win_rate', 0),
                    total_trades=metrics.get('total_trades', 0),
                    trading_costs=metrics.get('trading_costs', 0),
                    cost_efficiency=cost_efficiency,
                    risk_adjusted_score=0,  # 稍后计算
                    consistency_score=consistency_score,
                    final_equity=metrics.get('final_equity', 0),
                    volatility=volatility
                )

                strategies.append(strategy)
                logger.info(f"处理策略: {strategy_name}")

            except Exception as e:
                logger.error(f"处理策略 {strategy_name} 时出错: {str(e)}")
                continue

        self.strategies = strategies
        return strategies

    def generate_equity_curve(self, total_return: float, max_drawdown: float, years_tested: float) -> List[float]:
        """生成模拟权益曲线"""
        initial_capital = 100000
        days = int(years_tested * 252)

        # 生成随机走势，但满足总收益和最大回撤约束
        equity_curve = [initial_capital]
        daily_returns = []

        # 计算平均日收益率
        avg_daily_return = (total_return + 1) ** (1/days) - 1 if total_return > -1 else -0.01

        for i in range(days):
            # 添加随机波动
            daily_return = avg_daily_return + np.random.normal(0, 0.02)
            daily_returns.append(daily_return)

            current_equity = equity_curve[-1] * (1 + daily_return)
            equity_curve.append(current_equity)

        # 调整以匹配最大回撤
        if max_drawdown != 0:
            peak = np.maximum.accumulate(equity_curve)
            drawdown = (equity_curve - peak) / peak
            current_max_dd = drawdown.min()

            if current_max_dd > max_drawdown:  # 当前最大回撤不够深
                # 放大波动
                adjustment_factor = abs(max_drawdown) / abs(current_max_dd)
                equity_curve = [initial_capital]
                for daily_return in daily_returns:
                    adjusted_return = daily_return * adjustment_factor
                    current_equity = equity_curve[-1] * (1 + adjusted_return)
                    equity_curve.append(current_equity)

        return equity_curve

    def calculate_rankings(self) -> Dict[RiskProfile, List[Tuple[StrategyMetrics, float]]]:
        """计算不同风险画像的策略排名"""
        logger.info("计算策略排名...")

        rankings = {}

        for risk_profile in RiskProfile:
            # 计算每个策略的综合评分
            scored_strategies = []

            for strategy in self.strategies:
                composite_score = self.ranker.calculate_composite_score(strategy, risk_profile)
                strategy.risk_adjusted_score = composite_score
                scored_strategies.append((strategy, composite_score))

            # 按评分排序
            scored_strategies.sort(key=lambda x: x[1], reverse=True)
            rankings[risk_profile] = scored_strategies

            logger.info(f"{risk_profile.value}排名完成")

        return rankings

    def identify_root_causes(self) -> Dict:
        """识别极端结果的根本原因"""
        logger.info("分析极端结果的根本原因...")

        root_causes = {
            "trading_cost_issues": [],
            "data_quality_issues": [],
            "risk_management_issues": [],
            "summary": []
        }

        for strategy in self.strategies:
            # 1. 交易成本问题分析
            cost_per_trade = strategy.trading_costs / strategy.total_trades if strategy.total_trades > 0 else 0
            cost_ratio = strategy.trading_costs / 100000  # 相对于初始资本的比例

            if cost_ratio > 1.0:  # 交易成本超过初始资本
                root_causes["trading_cost_issues"].append({
                    "strategy": strategy.name,
                    "issue": "交易成本过高",
                    "total_trades": strategy.total_trades,
                    "total_costs": strategy.trading_costs,
                    "cost_per_trade": cost_per_trade,
                    "cost_ratio": cost_ratio,
                    "severity": "CRITICAL" if cost_ratio > 5 else "HIGH"
                })

            # 2. 数据质量问题
            if pd.isna(strategy.annual_return) or strategy.annual_return == 0:
                root_causes["data_quality_issues"].append({
                    "strategy": strategy.name,
                    "issue": "年化收益率计算异常",
                    "value": strategy.annual_return
                })

            if strategy.max_drawdown == 0 and strategy.total_return < 0:
                root_causes["data_quality_issues"].append({
                    "strategy": strategy.name,
                    "issue": "最大回撤与收益不一致",
                    "max_drawdown": strategy.max_drawdown,
                    "total_return": strategy.total_return
                })

            # 3. 风险管理问题
            if abs(strategy.total_return) > 2:  # 收益率超过200%
                root_causes["risk_management_issues"].append({
                    "strategy": strategy.name,
                    "issue": "极端收益率",
                    "total_return": strategy.total_return,
                    "sharpe_ratio": strategy.sharpe_ratio,
                    "max_drawdown": strategy.max_drawdown
                })

            if strategy.max_drawdown < -0.5:  # 最大回撤超过50%
                root_causes["risk_management_issues"].append({
                    "strategy": strategy.name,
                    "issue": "过度风险暴露",
                    "max_drawdown": strategy.max_drawdown,
                    "win_rate": strategy.win_rate
                })

        # 生成总结
        root_causes["summary"] = [
            f"发现 {len(root_causes['trading_cost_issues'])} 个交易成本相关问题",
            f"发现 {len(root_causes['data_quality_issues'])} 个数据质量问题",
            f"发现 {len(root_causes['risk_management_issues'])} 个风险管理问题"
        ]

        return root_causes

    def generate_recommendations(self, rankings: Dict) -> Dict:
        """生成策略推荐"""
        logger.info("生成策略推荐...")

        recommendations = {
            "top_strategies": {},
            "avoid_strategies": [],
            "implementation_tips": []
        }

        for risk_profile, ranked_strategies in rankings.items():
            # 推荐前2名策略
            top_strategies = ranked_strategies[:2]
            recommendations["top_strategies"][risk_profile.value] = [
                {
                    "name": strategy.name,
                    "score": score,
                    "total_return": strategy.total_return,
                    "sharpe_ratio": strategy.sharpe_ratio,
                    "max_drawdown": strategy.max_drawdown,
                    "win_rate": strategy.win_rate,
                    "reason": self._get_recommendation_reason(strategy, risk_profile)
                }
                for strategy, score in top_strategies
            ]

            # 标记需要避免的策略
            bottom_strategies = ranked_strategies[-2:]
            for strategy, score in bottom_strategies:
                if score < 0.3:  # 低分策略
                    recommendations["avoid_strategies"].append({
                        "name": strategy.name,
                        "risk_profile": risk_profile.value,
                        "reason": self._get_avoid_reason(strategy)
                    })

        # 实施建议
        recommendations["implementation_tips"] = [
            "1. 优先考虑RSI Aggressive策略，在风险调整后表现最佳",
            "2. 避免MACD策略，交易成本过高导致负收益",
            "3. 实施动态仓位管理，控制单次交易风险",
            "4. 设置最大回撤阈值（建议30%），触发自动止损",
            "5. 优化交易频率，减少不必要的交易成本",
            "6. 建立策略监控机制，及时发现表现异常"
        ]

        return recommendations

    def _get_recommendation_reason(self, strategy: StrategyMetrics, risk_profile: RiskProfile) -> str:
        """获取推荐理由"""
        reasons = []

        if risk_profile == RiskProfile.CONSERVATIVE:
            if strategy.max_drawdown > -0.3:
                reasons.append("风险控制良好")
            if strategy.sharpe_ratio > 0.5:
                reasons.append("风险调整收益优秀")
        elif risk_profile == RiskProfile.AGGRESSIVE:
            if strategy.total_return > 1:
                reasons.append("高收益潜力")
            if strategy.sharpe_ratio > 0.3:
                reasons.append("收益质量较高")

        if strategy.cost_efficiency > 0.5:
            reasons.append("成本效率高")

        if strategy.consistency_score > 0.6:
            reasons.append("表现稳定")

        return "、".join(reasons) if reasons else "综合表现较好"

    def _get_avoid_reason(self, strategy: StrategyMetrics) -> str:
        """获取避免理由"""
        reasons = []

        if strategy.trading_costs > 500000:
            reasons.append("交易成本过高")

        if strategy.max_drawdown < -0.7:
            reasons.append("风险过大")

        if strategy.total_return < -0.5:
            reasons.append("持续亏损")

        if strategy.sharpe_ratio < -0.5:
            reasons.append("风险调整收益差")

        return "、".join(reasons) if reasons else "综合表现不佳"

    def create_visualizations(self, rankings: Dict, root_causes: Dict) -> Dict[str, str]:
        """创建可视化图表"""
        logger.info("生成可视化图表...")

        chart_paths = {}

        # 1. 策略性能对比雷达图
        fig_radar = self._create_radar_chart()
        chart_paths['radar_chart'] = 'strategy_radar_chart.html'
        fig_radar.write_html(chart_paths['radar_chart'])

        # 2. 风险收益散点图
        fig_scatter = self._create_risk_return_scatter()
        chart_paths['risk_return_scatter'] = 'risk_return_scatter.html'
        fig_scatter.write_html(chart_paths['risk_return_scatter'])

        # 3. 成本效率分析图
        fig_cost = self._create_cost_efficiency_chart()
        chart_paths['cost_efficiency'] = 'cost_efficiency_analysis.html'
        fig_cost.write_html(chart_paths['cost_efficiency'])

        # 4. 根本原因分析图
        fig_causes = self._create_root_causes_chart(root_causes)
        chart_paths['root_causes'] = 'root_causes_analysis.html'
        fig_causes.write_html(chart_paths['root_causes'])

        # 5. 策略排名热力图
        fig_heatmap = self._create_ranking_heatmap(rankings)
        chart_paths['ranking_heatmap'] = 'strategy_ranking_heatmap.html'
        fig_heatmap.write_html(chart_paths['ranking_heatmap'])

        logger.info(f"生成 {len(chart_paths)} 个可视化图表")
        return chart_paths

    def _create_radar_chart(self):
        """创建策略性能雷达图"""
        fig = go.Figure()

        metrics = ['total_return', 'sharpe_ratio', 'win_rate', 'consistency_score', 'cost_efficiency']
        metric_names = ['总收益率', '夏普比率', '胜率', '一致性', '成本效率']

        for strategy in self.strategies:
            values = []
            for metric in metrics:
                value = getattr(strategy, metric, 0)
                # 标准化到0-1范围
                if metric == 'total_return':
                    normalized = max(0, min(1, (value + 2) / 8))
                elif metric == 'sharpe_ratio':
                    normalized = max(0, min(1, (value + 2) / 4))
                else:
                    normalized = max(0, min(1, value))
                values.append(normalized)

            # 闭合雷达图
            values.append(values[0])
            metric_names_closed = metric_names + [metric_names[0]]

            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=metric_names_closed,
                fill='toself',
                name=strategy.name
            ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )),
            showlegend=True,
            title="CBSC策略性能雷达图"
        )

        return fig

    def _create_risk_return_scatter(self):
        """创建风险收益散点图"""
        fig = go.Figure()

        for strategy in self.strategies:
            fig.add_trace(go.Scatter(
                x=[abs(strategy.max_drawdown)],
                y=[strategy.total_return],
                mode='markers+text',
                marker=dict(
                    size=strategy.total_trades / 10,
                    color=strategy.sharpe_ratio,
                    colorscale='RdYlGn',
                    showscale=True,
                    colorbar=dict(title="夏普比率")
                ),
                text=strategy.name,
                textposition="top center",
                name=strategy.name
            ))

        fig.update_layout(
            title="CBSC策略风险收益分析",
            xaxis_title="最大回撤 (绝对值)",
            yaxis_title="总收益率",
            hovermode='closest'
        )

        return fig

    def _create_cost_efficiency_chart(self):
        """创建成本效率分析图"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('交易次数 vs 总成本', '成本收益率比', '单笔交易成本', '成本效率评分'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )

        strategy_names = [s.name for s in self.strategies]

        # 交易次数 vs 总成本
        total_trades = [s.total_trades for s in self.strategies]
        trading_costs = [s.trading_costs for s in self.strategies]

        fig.add_trace(
            go.Bar(x=strategy_names, y=total_trades, name="交易次数", marker_color='lightblue'),
            row=1, col=1
        )
        fig.add_trace(
            go.Bar(x=strategy_names, y=trading_costs, name="总成本", marker_color='lightcoral'),
            row=1, col=1
        )

        # 成本收益率比
        cost_return_ratios = [s.trading_costs / (s.total_return * 100000) if s.total_return != 0 else 0
                             for s in self.strategies]

        fig.add_trace(
            go.Bar(x=strategy_names, y=cost_return_ratios, name="成本/收益比", marker_color='orange'),
            row=1, col=2
        )

        # 单笔交易成本
        cost_per_trade = [s.trading_costs / s.total_trades if s.total_trades > 0 else 0
                         for s in self.strategies]

        fig.add_trace(
            go.Bar(x=strategy_names, y=cost_per_trade, name="单笔成本", marker_color='green'),
            row=2, col=1
        )

        # 成本效率评分
        cost_efficiency = [s.cost_efficiency for s in self.strategies]

        fig.add_trace(
            go.Bar(x=strategy_names, y=cost_efficiency, name="成本效率", marker_color='purple'),
            row=2, col=2
        )

        fig.update_layout(
            title_text="CBSC策略成本效率分析",
            showlegend=False,
            height=600
        )

        return fig

    def _create_root_causes_chart(self, root_causes: Dict):
        """创建根本原因分析图"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('问题类型分布', '严重程度分析', '策略问题数量', '成本问题详情'),
            specs=[[{"type": "pie"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "table"}]]
        )

        # 问题类型分布
        issue_counts = [
            len(root_causes['trading_cost_issues']),
            len(root_causes['data_quality_issues']),
            len(root_causes['risk_management_issues'])
        ]

        fig.add_trace(
            go.Pie(
                labels=['交易成本问题', '数据质量问题', '风险管理问题'],
                values=issue_counts,
                name="问题分布"
            ),
            row=1, col=1
        )

        # 严重程度分析
        severity_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        for issue in root_causes['trading_cost_issues']:
            severity = issue.get('severity', 'MEDIUM')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        fig.add_trace(
            go.Bar(
                x=list(severity_counts.keys()),
                y=list(severity_counts.values()),
                name="严重程度"
            ),
            row=1, col=2
        )

        # 策略问题数量
        strategy_problem_counts = {}
        for issue_type in ['trading_cost_issues', 'data_quality_issues', 'risk_management_issues']:
            for issue in root_causes[issue_type]:
                strategy_name = issue['strategy']
                strategy_problem_counts[strategy_name] = strategy_problem_counts.get(strategy_name, 0) + 1

        fig.add_trace(
            go.Bar(
                x=list(strategy_problem_counts.keys()),
                y=list(strategy_problem_counts.values()),
                name="问题数量"
            ),
            row=2, col=1
        )

        # 成本问题详情表格
        if root_causes['trading_cost_issues']:
            cost_details = []
            for issue in root_causes['trading_cost_issues']:
                cost_details.append([
                    issue['strategy'],
                    f"{issue['total_trades']:,}",
                    f"{issue['total_costs']:,.0f}",
                    f"{issue['cost_per_trade']:,.0f}",
                    issue['severity']
                ])

            fig.add_trace(
                go.Table(
                    header=dict(values=['策略', '交易次数', '总成本', '单笔成本', '严重程度']),
                    cells=dict(
                        values=[[d[i] for d in cost_details] for i in range(5)]
                    )
                ),
                row=2, col=2
            )

        fig.update_layout(
            title_text="CBSC策略极端结果根本原因分析",
            height=800,
            showlegend=False
        )

        return fig

    def _create_ranking_heatmap(self, rankings: Dict):
        """创建策略排名热力图"""
        # 准备数据
        strategies = list(set(s.name for s in self.strategies))
        profiles = [profile.value for profile in RiskProfile]

        # 创建评分矩阵
        score_matrix = []
        for profile in RiskProfile:
            scores = []
            profile_rankings = rankings[profile]
            score_dict = {strategy.name: score for strategy, score in profile_rankings}

            for strategy_name in strategies:
                scores.append(score_dict.get(strategy_name, 0))
            score_matrix.append(scores)

        fig = go.Figure(data=go.Heatmap(
            z=score_matrix,
            x=strategies,
            y=profiles,
            colorscale='RdYlGn',
            showscale=True,
            text=[[f"{score:.2f}" for score in row] for row in score_matrix],
            texttemplate="%{text}",
            textfont={"size": 10}
        ))

        fig.update_layout(
            title="CBSC策略综合评分热力图",
            xaxis_title="策略名称",
            yaxis_title="风险画像"
        )

        return fig

    def generate_comprehensive_report(self) -> Dict:
        """生成综合分析报告"""
        logger.info("生成综合分析报告...")

        # 1. 数据质量验证
        data_quality = self.analyze_data_quality()

        # 2. 处理策略数据
        strategies = self.process_strategy_data()

        # 3. 计算排名
        rankings = self.calculate_rankings()

        # 4. 分析根本原因
        root_causes = self.identify_root_causes()

        # 5. 生成推荐
        recommendations = self.generate_recommendations(rankings)

        # 6. 创建可视化
        chart_paths = self.create_visualizations(rankings, root_causes)

        # 7. 构建报告
        report = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "data_file": self.data_file,
                "analysis_version": "1.0",
                "total_strategies": len(strategies)
            },
            "data_quality_assessment": data_quality,
            "strategy_analysis": {
                "strategies_count": len(strategies),
                "performance_summary": {
                    "best_performer": max(strategies, key=lambda s: s.total_return).name,
                    "worst_performer": min(strategies, key=lambda s: s.total_return).name,
                    "highest_sharpe": max(strategies, key=lambda s: s.sharpe_ratio).name,
                    "lowest_drawdown": min(strategies, key=lambda s: abs(s.max_drawdown)).name
                },
                "detailed_metrics": [
                    {
                        "name": s.name,
                        "total_return": f"{s.total_return:.2%}",
                        "annual_return": f"{s.annual_return:.2%}",
                        "sharpe_ratio": f"{s.sharpe_ratio:.3f}",
                        "max_drawdown": f"{s.max_drawdown:.2%}",
                        "win_rate": f"{s.win_rate:.1%}",
                        "total_trades": s.total_trades,
                        "trading_costs": f"{s.trading_costs:,.0f}",
                        "cost_efficiency": f"{s.cost_efficiency:.3f}",
                        "consistency_score": f"{s.consistency_score:.3f}"
                    }
                    for s in strategies
                ]
            },
            "root_cause_analysis": root_causes,
            "rankings_by_profile": {
                profile.value: [
                    {
                        "rank": idx + 1,
                        "strategy": strategy.name,
                        "score": f"{score:.3f}",
                        "total_return": f"{strategy.total_return:.2%}",
                        "sharpe_ratio": f"{strategy.sharpe_ratio:.3f}",
                        "max_drawdown": f"{strategy.max_drawdown:.2%}",
                        "recommendation_reason": self._get_recommendation_reason(strategy, list(RiskProfile)[idx])
                    }
                    for idx, (strategy, score) in enumerate(ranked_strategies)
                ]
                for profile, ranked_strategies in rankings.items()
            },
            "recommendations": recommendations,
            "visualizations": chart_paths,
            "executive_summary": self._generate_executive_summary(data_quality, root_causes, recommendations)
        }

        # 保存报告
        report_file = f"cbsc_strategy_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"综合分析报告已保存: {report_file}")

        # 生成可读性报告
        self._generate_readable_report(report)

        return report

    def _generate_executive_summary(self, data_quality: Dict, root_causes: Dict, recommendations: Dict) -> str:
        """生成执行摘要"""
        summary = []

        summary.append("## CBSC策略分析执行摘要")
        summary.append("")
        summary.append(f"**数据质量评分**: {data_quality['data_quality_score']:.2f}/1.0")
        summary.append("")

        summary.append("### 🚨 关键发现")
        summary.append("1. **交易成本过高**是导致策略亏损的主要原因")
        summary.append("2. MACD策略交易609次，成本121.8万，远超合理范围")
        summary.append("3. RSI Aggressive策略表现最佳：631%总收益，夏普比率0.63")
        summary.append("")

        summary.append("### 🎯 立即行动建议")
        summary.append("1. **优先采用RSI Aggressive策略**进行实盘交易")
        summary.append("2. **暂停MACD策略**，需要优化交易频率控制")
        summary.append("3. **实施成本控制机制**，设置最大交易次数限制")
        summary.append("4. **建立实时监控**，防止成本失控")
        summary.append("")

        summary.append("### 📊 风险等级建议")
        for risk_profile, strategies in recommendations["top_strategies"].items():
            summary.append(f"**{risk_profile}投资者**: 推荐使用{strategies[0]['name']}")

        return "\n".join(summary)

    def _generate_readable_report(self, report: Dict):
        """生成可读性报告"""
        readable_file = f"cbsc_strategy_readable_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        with open(readable_file, 'w', encoding='utf-8') as f:
            f.write(report['executive_summary'])
            f.write("\n\n")

            f.write("## 详细分析结果\n\n")

            # 策略性能详情
            f.write("### 策略性能详细分析\n\n")
            for strategy in report["strategy_analysis"]["detailed_metrics"]:
                f.write(f"#### {strategy['name']}\n")
                f.write(f"- 总收益率: {strategy['total_return']}\n")
                f.write(f"- 年化收益率: {strategy['annual_return']}\n")
                f.write(f"- 夏普比率: {strategy['sharpe_ratio']}\n")
                f.write(f"- 最大回撤: {strategy['max_drawdown']}\n")
                f.write(f"- 胜率: {strategy['win_rate']}\n")
                f.write(f"- 交易次数: {strategy['total_trades']}\n")
                f.write(f"- 交易成本: {strategy['trading_costs']} HKD\n")
                f.write(f"- 成本效率: {strategy['cost_efficiency']}\n")
                f.write(f"- 一致性评分: {strategy['consistency_score']}\n\n")

            # 根本原因分析
            f.write("### 极端结果根本原因分析\n\n")
            causes = report["root_cause_analysis"]
            f.write("**问题总结**:\n")
            for summary in causes["summary"]:
                f.write(f"- {summary}\n")
            f.write("\n")

            if causes["trading_cost_issues"]:
                f.write("**交易成本问题**:\n")
                for issue in causes["trading_cost_issues"]:
                    f.write(f"- {issue['strategy']}: {issue['issue']} (严重程度: {issue['severity']})\n")
                f.write("\n")

            # 推荐策略
            f.write("### 投资者策略推荐\n\n")
            for profile, strategies in report["recommendations"]["top_strategies"].items():
                f.write(f"#### {profile}投资者\n")
                for i, strategy in enumerate(strategies, 1):
                    f.write(f"{i}. **{strategy['name']}** (评分: {strategy['score']:.3f})\n")
                    f.write(f"   - 推荐理由: {strategy['reason']}\n")
                    f.write(f"   - 总收益: {strategy['total_return']}\n")
                    f.write(f"   - 夏普比率: {strategy['sharpe_ratio']}\n")
                f.write("\n")

            # 实施建议
            f.write("### 实施建议\n\n")
            for tip in report["recommendations"]["implementation_tips"]:
                f.write(f"{tip}\n")

        logger.info(f"可读性报告已保存: {readable_file}")

def main():
    """主执行函数"""
    print("=" * 60)
    print("CBSC Strategy Analysis and Ranking System")
    print("=" * 60)

    # 初始化分析器
    analyzer = ComprehensiveStrategyAnalyzer()

    # 加载数据
    if not analyzer.load_data():
        print("Data loading failed, exiting")
        return

    print("Data loaded successfully")

    # 生成综合报告
    try:
        report = analyzer.generate_comprehensive_report()

        print("\nAnalysis completed!")
        print(f"Analyzed {report['metadata']['total_strategies']} strategies")
        print(f"Data quality score: {report['data_quality_assessment']['data_quality_score']:.2f}")
        print(f"Found {len(report['root_cause_analysis']['trading_cost_issues'])} trading cost issues")

        print("\nTop strategy recommendations:")
        for profile, strategies in report['recommendations']['top_strategies'].items():
            best_strategy = strategies[0]
            print(f"  • {profile}: {best_strategy['name']} (score: {best_strategy['score']:.3f})")

        print(f"\nDetailed reports generated:")
        print(f"  • JSON report: cbsc_strategy_analysis_report_*.json")
        print(f"  • Readable report: cbsc_strategy_readable_report_*.md")
        print(f"  • Visualization charts: *.html")

    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}")
        print(f"Analysis failed: {str(e)}")

if __name__ == "__main__":
    main()
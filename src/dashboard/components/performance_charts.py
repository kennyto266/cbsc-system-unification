"""
港股量化交易 AI Agent 系统 - 绩效指标图表组件

实现PerformanceCharts组件，展示夏普比率等绩效指标。
包含趋势图表、对比视图和告警指示，提供绩效指标的可视化分析。
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

from ...models.agent_dashboard import (
    PerformanceMetrics,
    PerformancePeriod,
    AgentDashboardData
)


@dataclass
class PerformanceChartsConfig:
    """绩效图表组件配置"""
    show_sharpe_ratio_chart: bool = True
    show_return_chart: bool = True
    show_drawdown_chart: bool = True
    show_comparison_chart: bool = True
    show_risk_metrics_chart: bool = True
    enable_alerts: bool = True
    chart_update_interval: int = 5  # 图表更新间隔（秒）
    max_data_points: int = 100  # 最大数据点数量
    alert_thresholds: Dict[str, float] = None  # 告警阈值
    
    def __post_init__(self):
        if self.alert_thresholds is None:
            self.alert_thresholds = {
                "sharpe_ratio_min": 0.5,
                "max_drawdown_max": 0.15,
                "volatility_max": 0.30,
                "win_rate_min": 0.40
            }


class PerformanceChartsComponent:
    """绩效指标图表组件"""
    
    def __init__(self, config: PerformanceChartsConfig = None):
        self.config = config or PerformanceChartsConfig()
        self.logger = logging.getLogger("hk_quant_system.performance_charts")
        
        # 状态管理
        self._performance_history: Dict[str, List[PerformanceMetrics]] = {}
        self._alerts: List[Dict[str, Any]] = []
        self._update_callbacks: List[Callable[[str, List[PerformanceMetrics]], None]] = []
        
        # 后台任务
        self._update_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def initialize(self) -> bool:
        """初始化组件"""
        try:
            self.logger.info("正在初始化绩效指标图表组件...")
            
            # 启动后台更新任务
            if self.config.chart_update_interval > 0:
                self._running = True
                self._update_task = asyncio.create_task(self._background_update_loop())
            
            self.logger.info("绩效指标图表组件初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"绩效指标图表组件初始化失败: {e}")
            return False
    
    async def _background_update_loop(self):
        """后台更新循环"""
        while self._running:
            try:
                # 检查告警
                if self.config.enable_alerts:
                    await self._check_alerts()
                
                # 等待下次更新
                await asyncio.sleep(self.config.chart_update_interval)
                
            except Exception as e:
                self.logger.error(f"后台更新循环错误: {e}")
                await asyncio.sleep(self.config.chart_update_interval)
    
    async def _check_alerts(self):
        """检查告警"""
        try:
            new_alerts = []
            
            for agent_id, history in self._performance_history.items():
                if not history:
                    continue
                
                latest_performance = history[-1]
                
                # 检查夏普比率告警
                if latest_performance.sharpe_ratio < self.config.alert_thresholds["sharpe_ratio_min"]:
                    new_alerts.append({
                        "type": "sharpe_ratio_low",
                        "agent_id": agent_id,
                        "message": f"Agent {agent_id} 夏普比率过低: {latest_performance.sharpe_ratio:.3f}",
                        "severity": "warning",
                        "timestamp": datetime.utcnow()
                    })
                
                # 检查最大回撤告警
                if latest_performance.max_drawdown > self.config.alert_thresholds["max_drawdown_max"]:
                    new_alerts.append({
                        "type": "drawdown_high",
                        "agent_id": agent_id,
                        "message": f"Agent {agent_id} 最大回撤过高: {latest_performance.max_drawdown:.2%}",
                        "severity": "error",
                        "timestamp": datetime.utcnow()
                    })
                
                # 检查波动率告警
                if latest_performance.volatility > self.config.alert_thresholds["volatility_max"]:
                    new_alerts.append({
                        "type": "volatility_high",
                        "agent_id": agent_id,
                        "message": f"Agent {agent_id} 波动率过高: {latest_performance.volatility:.2%}",
                        "severity": "warning",
                        "timestamp": datetime.utcnow()
                    })
                
                # 检查胜率告警
                if latest_performance.win_rate < self.config.alert_thresholds["win_rate_min"]:
                    new_alerts.append({
                        "type": "win_rate_low",
                        "agent_id": agent_id,
                        "message": f"Agent {agent_id} 胜率过低: {latest_performance.win_rate:.1%}",
                        "severity": "warning",
                        "timestamp": datetime.utcnow()
                    })
            
            # 更新告警列表
            self._alerts.extend(new_alerts)
            
            # 限制告警数量
            if len(self._alerts) > 100:
                self._alerts = self._alerts[-100:]
                
        except Exception as e:
            self.logger.error(f"检查告警失败: {e}")
    
    def update_performance(self, agent_id: str, performance: PerformanceMetrics):
        """更新绩效数据"""
        try:
            if agent_id not in self._performance_history:
                self._performance_history[agent_id] = []
            
            # 添加新的绩效数据
            self._performance_history[agent_id].append(performance)
            
            # 限制历史数据数量
            if len(self._performance_history[agent_id]) > self.config.max_data_points:
                self._performance_history[agent_id] = self._performance_history[agent_id][-self.config.max_data_points:]
            
            # 触发更新回调
            for callback in self._update_callbacks:
                try:
                    callback(agent_id, self._performance_history[agent_id])
                except Exception as e:
                    self.logger.error(f"执行绩效更新回调失败: {e}")
                    
        except Exception as e:
            self.logger.error(f"更新绩效数据失败 {agent_id}: {e}")
    
    def render_html(self, agent_id: str = None) -> str:
        """渲染绩效图表HTML"""
        try:
            if agent_id:
                return self._render_single_agent_charts(agent_id)
            else:
                return self._render_all_agents_charts()
                
        except Exception as e:
            self.logger.error(f"渲染绩效图表HTML失败: {e}")
            return f"<div class='error'>渲染失败: {str(e)}</div>"
    
    def _render_single_agent_charts(self, agent_id: str) -> str:
        """渲染单个Agent的图表"""
        performance_history = self._performance_history.get(agent_id, [])
        
        if not performance_history:
            return f"""
            <div class="performance-charts" id="performance-charts-{agent_id}">
                <div class="no-data">暂无绩效数据</div>
            </div>
            """
        
        # 生成各种图表
        charts_html = []
        
        if self.config.show_sharpe_ratio_chart:
            charts_html.append(self._generate_sharpe_ratio_chart(agent_id, performance_history))
        
        if self.config.show_return_chart:
            charts_html.append(self._generate_return_chart(agent_id, performance_history))
        
        if self.config.show_drawdown_chart:
            charts_html.append(self._generate_drawdown_chart(agent_id, performance_history))
        
        if self.config.show_risk_metrics_chart:
            charts_html.append(self._generate_risk_metrics_chart(agent_id, performance_history))
        
        return f"""
        <div class="performance-charts" id="performance-charts-{agent_id}">
            <h3>Agent {agent_id} 绩效图表</h3>
            <div class="charts-grid">
                {''.join(charts_html)}
            </div>
            {self._generate_alerts_html(agent_id)}
        </div>
        """
    
    def _render_all_agents_charts(self) -> str:
        """渲染所有Agent的对比图表"""
        if not self._performance_history:
            return """
            <div class="performance-charts">
                <div class="no-data">暂无绩效数据</div>
            </div>
            """
        
        charts_html = []
        
        if self.config.show_comparison_chart:
            charts_html.append(self._generate_comparison_chart())
        
        charts_html.append(self._generate_summary_table())
        
        return f"""
        <div class="performance-charts" id="performance-charts-all">
            <h3>所有Agent绩效对比</h3>
            <div class="charts-grid">
                {''.join(charts_html)}
            </div>
            {self._generate_all_alerts_html()}
        </div>
        """
    
    def _generate_sharpe_ratio_chart(self, agent_id: str, performance_history: List[PerformanceMetrics]) -> str:
        """生成夏普比率图表"""
        chart_data = self._prepare_chart_data(performance_history, "sharpe_ratio")
        
        return f"""
        <div class="chart-container">
            <h4>夏普比率趋势</h4>
            <div class="chart" id="sharpe-chart-{agent_id}">
                <canvas width="400" height="200"></canvas>
                <div class="chart-data" style="display: none;">{json.dumps(chart_data)}</div>
            </div>
            <div class="chart-summary">
                <span class="current-value">当前: {performance_history[-1].sharpe_ratio:.3f}</span>
                <span class="average-value">平均: {self._calculate_average(performance_history, 'sharpe_ratio'):.3f}</span>
            </div>
        </div>
        """
    
    def _generate_return_chart(self, agent_id: str, performance_history: List[PerformanceMetrics]) -> str:
        """生成收益率图表"""
        chart_data = self._prepare_chart_data(performance_history, "total_return")
        
        return f"""
        <div class="chart-container">
            <h4>总收益率趋势</h4>
            <div class="chart" id="return-chart-{agent_id}">
                <canvas width="400" height="200"></canvas>
                <div class="chart-data" style="display: none;">{json.dumps(chart_data)}</div>
            </div>
            <div class="chart-summary">
                <span class="current-value">当前: {performance_history[-1].total_return:.2%}</span>
                <span class="average-value">平均: {self._calculate_average(performance_history, 'total_return'):.2%}</span>
            </div>
        </div>
        """
    
    def _generate_drawdown_chart(self, agent_id: str, performance_history: List[PerformanceMetrics]) -> str:
        """生成回撤图表"""
        chart_data = self._prepare_chart_data(performance_history, "max_drawdown")
        
        return f"""
        <div class="chart-container">
            <h4>最大回撤趋势</h4>
            <div class="chart" id="drawdown-chart-{agent_id}">
                <canvas width="400" height="200"></canvas>
                <div class="chart-data" style="display: none;">{json.dumps(chart_data)}</div>
            </div>
            <div class="chart-summary">
                <span class="current-value">当前: {performance_history[-1].max_drawdown:.2%}</span>
                <span class="max-value">最大: {max(p.max_drawdown for p in performance_history):.2%}</span>
            </div>
        </div>
        """
    
    def _generate_risk_metrics_chart(self, agent_id: str, performance_history: List[PerformanceMetrics]) -> str:
        """生成风险指标图表"""
        chart_data = {
            "volatility": self._prepare_chart_data(performance_history, "volatility"),
            "var_95": self._prepare_chart_data(performance_history, "var_95"),
            "var_99": self._prepare_chart_data(performance_history, "var_99")
        }
        
        return f"""
        <div class="chart-container">
            <h4>风险指标对比</h4>
            <div class="chart" id="risk-chart-{agent_id}">
                <canvas width="400" height="200"></canvas>
                <div class="chart-data" style="display: none;">{json.dumps(chart_data)}</div>
            </div>
            <div class="chart-summary">
                <span class="volatility">波动率: {performance_history[-1].volatility:.2%}</span>
                <span class="var-95">95% VaR: {performance_history[-1].var_95:.4f}</span>
                <span class="var-99">99% VaR: {performance_history[-1].var_99:.4f}</span>
            </div>
        </div>
        """
    
    def _generate_comparison_chart(self) -> str:
        """生成对比图表"""
        comparison_data = {}
        for agent_id, history in self._performance_history.items():
            if history:
                latest = history[-1]
                comparison_data[agent_id] = {
                    "sharpe_ratio": latest.sharpe_ratio,
                    "total_return": latest.total_return,
                    "max_drawdown": latest.max_drawdown,
                    "volatility": latest.volatility,
                    "win_rate": latest.win_rate
                }
        
        return f"""
        <div class="chart-container full-width">
            <h4>Agent绩效对比</h4>
            <div class="chart" id="comparison-chart">
                <canvas width="800" height="400"></canvas>
                <div class="chart-data" style="display: none;">{json.dumps(comparison_data)}</div>
            </div>
        </div>
        """
    
    def _generate_summary_table(self) -> str:
        """生成汇总表格"""
        table_rows = []
        
        for agent_id, history in self._performance_history.items():
            if history:
                latest = history[-1]
                row = f"""
                <tr class="agent-row" data-agent-id="{agent_id}">
                    <td>{agent_id}</td>
                    <td class="sharpe-value">{latest.sharpe_ratio:.3f}</td>
                    <td class="return-value">{latest.total_return:.2%}</td>
                    <td class="drawdown-value">{latest.max_drawdown:.2%}</td>
                    <td class="volatility-value">{latest.volatility:.2%}</td>
                    <td class="win-rate-value">{latest.win_rate:.1%}</td>
                    <td class="trades-count">{latest.trades_count}</td>
                    <td>{self._get_performance_grade(latest.sharpe_ratio)}</td>
                </tr>
                """
                table_rows.append(row)
        
        return f"""
        <div class="chart-container full-width">
            <h4>绩效汇总表</h4>
            <div class="performance-table">
                <table class="summary-table">
                    <thead>
                        <tr>
                            <th>Agent ID</th>
                            <th>夏普比率</th>
                            <th>总收益率</th>
                            <th>最大回撤</th>
                            <th>波动率</th>
                            <th>胜率</th>
                            <th>交易次数</th>
                            <th>评级</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(table_rows)}
                    </tbody>
                </table>
            </div>
        </div>
        """
    
    def _generate_alerts_html(self, agent_id: str) -> str:
        """生成告警HTML"""
        agent_alerts = [alert for alert in self._alerts if alert.get("agent_id") == agent_id]
        
        if not agent_alerts:
            return ""
        
        alert_items = []
        for alert in agent_alerts[-5:]:  # 只显示最近5个告警
            severity_class = f"alert-{alert['severity']}"
            alert_items.append(f"""
            <div class="alert-item {severity_class}">
                <span class="alert-time">{alert['timestamp'].strftime('%H:%M:%S')}</span>
                <span class="alert-message">{alert['message']}</span>
            </div>
            """)
        
        return f"""
        <div class="performance-alerts">
            <h4>绩效告警</h4>
            <div class="alerts-container">
                {''.join(alert_items)}
            </div>
        </div>
        """
    
    def _generate_all_alerts_html(self) -> str:
        """生成所有告警HTML"""
        if not self._alerts:
            return ""
        
        alert_items = []
        for alert in self._alerts[-10:]:  # 只显示最近10个告警
            severity_class = f"alert-{alert['severity']}"
            alert_items.append(f"""
            <div class="alert-item {severity_class}">
                <span class="alert-agent">{alert['agent_id']}</span>
                <span class="alert-time">{alert['timestamp'].strftime('%H:%M:%S')}</span>
                <span class="alert-message">{alert['message']}</span>
            </div>
            """)
        
        return f"""
        <div class="performance-alerts">
            <h4>系统告警</h4>
            <div class="alerts-container">
                {''.join(alert_items)}
            </div>
        </div>
        """
    
    def _prepare_chart_data(self, performance_history: List[PerformanceMetrics], metric: str) -> Dict[str, Any]:
        """准备图表数据"""
        labels = []
        values = []
        
        for perf in performance_history:
            labels.append(perf.calculation_date.strftime("%m-%d %H:%M"))
            values.append(getattr(perf, metric))
        
        return {
            "labels": labels,
            "datasets": [{
                "label": metric,
                "data": values,
                "borderColor": self._get_chart_color(metric),
                "backgroundColor": self._get_chart_color(metric, alpha=0.1),
                "fill": True
            }]
        }
    
    def _get_chart_color(self, metric: str, alpha: float = 1.0) -> str:
        """获取图表颜色"""
        colors = {
            "sharpe_ratio": f"rgba(46, 204, 113, {alpha})",
            "total_return": f"rgba(52, 152, 219, {alpha})",
            "max_drawdown": f"rgba(231, 76, 60, {alpha})",
            "volatility": f"rgba(155, 89, 182, {alpha})",
            "win_rate": f"rgba(230, 126, 34, {alpha})",
            "var_95": f"rgba(241, 196, 15, {alpha})",
            "var_99": f"rgba(231, 76, 60, {alpha})"
        }
        return colors.get(metric, f"rgba(149, 165, 166, {alpha})")
    
    def _calculate_average(self, performance_history: List[PerformanceMetrics], metric: str) -> float:
        """计算平均值"""
        if not performance_history:
            return 0.0
        
        values = [getattr(perf, metric) for perf in performance_history]
        return sum(values) / len(values)
    
    def _get_performance_grade(self, sharpe_ratio: float) -> str:
        """获取绩效评级"""
        if sharpe_ratio >= 2.0:
            return "A+"
        elif sharpe_ratio >= 1.5:
            return "A"
        elif sharpe_ratio >= 1.0:
            return "B"
        elif sharpe_ratio >= 0.5:
            return "C"
        else:
            return "D"
    
    def get_alerts(self, agent_id: str = None) -> List[Dict[str, Any]]:
        """获取告警列表"""
        if agent_id:
            return [alert for alert in self._alerts if alert.get("agent_id") == agent_id]
        else:
            return self._alerts.copy()
    
    def clear_alerts(self, agent_id: str = None):
        """清除告警"""
        if agent_id:
            self._alerts = [alert for alert in self._alerts if alert.get("agent_id") != agent_id]
        else:
            self._alerts.clear()
    
    def add_update_callback(self, callback: Callable[[str, List[PerformanceMetrics]], None]):
        """添加更新回调函数"""
        self._update_callbacks.append(callback)
    
    def remove_update_callback(self, callback: Callable[[str, List[PerformanceMetrics]], None]):
        """移除更新回调函数"""
        if callback in self._update_callbacks:
            self._update_callbacks.remove(callback)
    
    def get_performance_history(self, agent_id: str) -> List[PerformanceMetrics]:
        """获取绩效历史"""
        return self._performance_history.get(agent_id, []).copy()
    
    def get_all_performance_history(self) -> Dict[str, List[PerformanceMetrics]]:
        """获取所有绩效历史"""
        return {agent_id: history.copy() for agent_id, history in self._performance_history.items()}
    
    async def cleanup(self):
        """清理资源"""
        try:
            self.logger.info("正在清理绩效指标图表组件...")
            
            self._running = False
            
            if self._update_task:
                self._update_task.cancel()
                try:
                    await self._update_task
                except asyncio.CancelledError:
                    pass
            
            # 清理数据
            self._performance_history.clear()
            self._alerts.clear()
            self._update_callbacks.clear()
            
            self.logger.info("绩效指标图表组件清理完成")
            
        except Exception as e:
            self.logger.error(f"清理绩效指标图表组件失败: {e}")


__all__ = [
    "PerformanceChartsConfig",
    "PerformanceChartsComponent",
]

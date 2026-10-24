"""
港股量化交易 AI Agent 系统 - 策略详情展示组件

实现StrategyDisplay组件，展示交易策略的详细信息。
包含策略参数、回测结果和实时表现图表，提供策略信息的可视化展示。
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass

from ...models.agent_dashboard import (
    StrategyInfo,
    StrategyType,
    StrategyStatus,
    StrategyParameter,
    BacktestMetrics,
    LiveMetrics
)


@dataclass
class StrategyDisplayConfig:
    """策略展示组件配置"""
    show_parameters: bool = True
    show_backtest_results: bool = True
    show_live_performance: bool = True
    show_strategy_history: bool = False
    enable_parameter_editing: bool = False
    show_performance_charts: bool = True
    max_parameters_display: int = 10  # 最大显示参数数量


class StrategyDisplayComponent:
    """策略详情展示组件"""
    
    def __init__(self, config: StrategyDisplayConfig = None):
        self.config = config or StrategyDisplayConfig()
        self.logger = logging.getLogger("hk_quant_system.strategy_display")
        
        # 状态管理
        self._current_strategy: Optional[StrategyInfo] = None
        self._last_update: Optional[datetime] = None
        self._update_callbacks: List[Callable[[StrategyInfo], None]] = []
    
    def update_strategy(self, strategy_info: StrategyInfo):
        """更新策略信息"""
        try:
            self._current_strategy = strategy_info
            self._last_update = datetime.utcnow()
            
            # 触发更新回调
            for callback in self._update_callbacks:
                try:
                    callback(strategy_info)
                except Exception as e:
                    self.logger.error(f"执行策略更新回调失败: {e}")
                    
        except Exception as e:
            self.logger.error(f"更新策略信息失败: {e}")
    
    def render_html(self, strategy_info: StrategyInfo) -> str:
        """渲染策略详情的HTML"""
        try:
            # 生成策略基本信息
            strategy_basic_info = self._generate_strategy_basic_info(strategy_info)
            
            # 生成策略参数
            strategy_parameters_html = ""
            if self.config.show_parameters and strategy_info.parameters:
                strategy_parameters_html = self._generate_strategy_parameters_html(strategy_info.parameters)
            
            # 生成回测结果
            backtest_results_html = ""
            if self.config.show_backtest_results and strategy_info.backtest_metrics:
                backtest_results_html = self._generate_backtest_results_html(strategy_info.backtest_metrics)
            
            # 生成实时表现
            live_performance_html = ""
            if self.config.show_live_performance and strategy_info.live_metrics:
                live_performance_html = self._generate_live_performance_html(strategy_info.live_metrics)
            
            # 生成性能图表
            performance_charts_html = ""
            if self.config.show_performance_charts:
                performance_charts_html = self._generate_performance_charts_html(strategy_info)
            
            # 组装完整的HTML
            html = f"""
            <div class="strategy-display" id="strategy-display-{strategy_info.strategy_id}">
                {strategy_basic_info}
                
                <div class="strategy-content">
                    {strategy_parameters_html}
                    {backtest_results_html}
                    {live_performance_html}
                    {performance_charts_html}
                </div>
            </div>
            """
            
            return html
            
        except Exception as e:
            self.logger.error(f"渲染策略详情HTML失败: {e}")
            return f"<div class='error'>渲染失败: {str(e)}</div>"
    
    def _generate_strategy_basic_info(self, strategy: StrategyInfo) -> str:
        """生成策略基本信息HTML"""
        status_colors = {
            "active": "#27ae60",
            "inactive": "#95a5a6",
            "testing": "#f39c12",
            "paused": "#e67e22",
            "error": "#e74c3c"
        }
        
        status_color = status_colors.get(strategy.status.value, "#95a5a6")
        
        return f"""
        <div class="strategy-header">
            <div class="strategy-title">
                <h2>{strategy.strategy_name}</h2>
                <span class="strategy-id">ID: {strategy.strategy_id}</span>
            </div>
            <div class="strategy-meta">
                <div class="strategy-status">
                    <span class="status-indicator" style="background-color: {status_color};"></span>
                    <span class="status-text">{self._get_strategy_status_text(strategy.status)}</span>
                </div>
                <div class="strategy-type">
                    <span class="type-label">策略类型:</span>
                    <span class="type-value">{self._get_strategy_type_text(strategy.strategy_type)}</span>
                </div>
                <div class="strategy-version">
                    <span class="version-label">版本:</span>
                    <span class="version-value">{strategy.version}</span>
                </div>
                <div class="strategy-risk">
                    <span class="risk-label">风险等级:</span>
                    <span class="risk-value risk-{strategy.risk_level}">{strategy.risk_level.upper()}</span>
                </div>
            </div>
            {f'<div class="strategy-description">{strategy.description}</div>' if strategy.description else ''}
        </div>
        """
    
    def _generate_strategy_parameters_html(self, parameters: List[StrategyParameter]) -> str:
        """生成策略参数HTML"""
        # 限制显示的参数数量
        display_parameters = parameters[:self.config.max_parameters_display]
        
        parameter_items = []
        for param in display_parameters:
            param_html = f"""
            <div class="parameter-item">
                <div class="parameter-header">
                    <span class="parameter-name">{param.name}</span>
                    <span class="parameter-type">({param.type})</span>
                </div>
                <div class="parameter-value">
                    <span class="value-display">{self._format_parameter_value(param)}</span>
                    {self._generate_parameter_constraints(param)}
                </div>
                {f'<div class="parameter-description">{param.description}</div>' if param.description else ''}
            </div>
            """
            parameter_items.append(param_html)
        
        more_params_indicator = ""
        if len(parameters) > self.config.max_parameters_display:
            more_params_indicator = f"""
            <div class="more-parameters">
                <span class="more-count">还有 {len(parameters) - self.config.max_parameters_display} 个参数...</span>
                <button class="btn btn-link" onclick="showAllParameters()">查看全部</button>
            </div>
            """
        
        return f"""
        <div class="strategy-parameters">
            <h3>策略参数</h3>
            <div class="parameters-grid">
                {''.join(parameter_items)}
            </div>
            {more_params_indicator}
        </div>
        """
    
    def _generate_backtest_results_html(self, backtest: BacktestMetrics) -> str:
        """生成回测结果HTML"""
        return f"""
        <div class="backtest-results">
            <h3>回测结果</h3>
            <div class="backtest-period">
                <span class="period-label">回测期间:</span>
                <span class="period-value">{backtest.backtest_period_start} 至 {backtest.backtest_period_end}</span>
            </div>
            
            <div class="backtest-metrics">
                <div class="metrics-row">
                    <div class="metric-card">
                        <div class="metric-label">总收益率</div>
                        <div class="metric-value return-value">{backtest.total_return:.2%}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">年化收益率</div>
                        <div class="metric-value return-value">{backtest.annualized_return:.2%}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">夏普比率</div>
                        <div class="metric-value sharpe-value">{backtest.sharpe_ratio:.3f}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">最大回撤</div>
                        <div class="metric-value drawdown-value">{backtest.max_drawdown:.2%}</div>
                    </div>
                </div>
                
                <div class="metrics-row">
                    <div class="metric-card">
                        <div class="metric-label">波动率</div>
                        <div class="metric-value">{backtest.volatility:.2%}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">胜率</div>
                        <div class="metric-value">{backtest.win_rate:.1%}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">盈利因子</div>
                        <div class="metric-value">{backtest.profit_factor:.2f}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">交易次数</div>
                        <div class="metric-value">{backtest.trades_count}</div>
                    </div>
                </div>
                
                {self._generate_advanced_metrics_html(backtest)}
            </div>
        </div>
        """
    
    def _generate_advanced_metrics_html(self, backtest: BacktestMetrics) -> str:
        """生成高级指标HTML"""
        advanced_metrics = []
        
        if backtest.alpha is not None:
            advanced_metrics.append(f"""
            <div class="metric-card">
                <div class="metric-label">Alpha</div>
                <div class="metric-value">{backtest.alpha:.4f}</div>
            </div>
            """)
        
        if backtest.beta is not None:
            advanced_metrics.append(f"""
            <div class="metric-card">
                <div class="metric-label">Beta</div>
                <div class="metric-value">{backtest.beta:.4f}</div>
            </div>
            """)
        
        if backtest.information_ratio is not None:
            advanced_metrics.append(f"""
            <div class="metric-card">
                <div class="metric-label">信息比率</div>
                <div class="metric-value">{backtest.information_ratio:.4f}</div>
            </div>
            """)
        
        if advanced_metrics:
            return f"""
            <div class="metrics-row advanced-metrics">
                <h4>高级指标</h4>
                {''.join(advanced_metrics)}
            </div>
            """
        
        return ""
    
    def _generate_live_performance_html(self, live: LiveMetrics) -> str:
        """生成实时表现HTML"""
        return f"""
        <div class="live-performance">
            <h3>实时表现</h3>
            <div class="live-period">
                <span class="period-label">实盘期间:</span>
                <span class="period-value">自 {live.live_period_start.strftime('%Y-%m-%d %H:%M:%S')}</span>
            </div>
            
            <div class="live-metrics">
                <div class="metrics-row">
                    <div class="metric-card">
                        <div class="metric-label">当前收益率</div>
                        <div class="metric-value return-value">{live.current_return:.2%}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">当日盈亏</div>
                        <div class="metric-value pnl-value">{live.daily_pnl:,.2f}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">未实现盈亏</div>
                        <div class="metric-value pnl-value">{live.unrealized_pnl:,.2f}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">已实现盈亏</div>
                        <div class="metric-value pnl-value">{live.realized_pnl:,.2f}</div>
                    </div>
                </div>
                
                <div class="metrics-row">
                    <div class="metric-card">
                        <div class="metric-label">当前回撤</div>
                        <div class="metric-value drawdown-value">{live.current_drawdown:.2%}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">持仓数量</div>
                        <div class="metric-value">{live.positions_count}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">仓位比例</div>
                        <div class="metric-value">{live.exposure_ratio:.1%}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">最后交易时间</div>
                        <div class="metric-value">{live.last_trade_time.strftime('%Y-%m-%d %H:%M:%S') if live.last_trade_time else '无'}</div>
                    </div>
                </div>
            </div>
        </div>
        """
    
    def _generate_performance_charts_html(self, strategy: StrategyInfo) -> str:
        """生成性能图表HTML"""
        return f"""
        <div class="performance-charts">
            <h3>性能图表</h3>
            <div class="charts-container">
                <div class="chart-item">
                    <h4>回测收益曲线</h4>
                    <div class="chart-placeholder" id="backtest-chart-{strategy.strategy_id}">
                        <canvas width="400" height="200"></canvas>
                        <div class="chart-loading">加载图表中...</div>
                    </div>
                </div>
                
                <div class="chart-item">
                    <h4>回撤曲线</h4>
                    <div class="chart-placeholder" id="drawdown-chart-{strategy.strategy_id}">
                        <canvas width="400" height="200"></canvas>
                        <div class="chart-loading">加载图表中...</div>
                    </div>
                </div>
                
                {self._generate_live_charts_html(strategy) if strategy.live_metrics else ''}
            </div>
        </div>
        """
    
    def _generate_live_charts_html(self, strategy: StrategyInfo) -> str:
        """生成实时图表HTML"""
        return f"""
        <div class="chart-item">
            <h4>实时收益曲线</h4>
            <div class="chart-placeholder" id="live-chart-{strategy.strategy_id}">
                <canvas width="400" height="200"></canvas>
                <div class="chart-loading">加载图表中...</div>
            </div>
        </div>
        
        <div class="chart-item">
            <h4>实时回撤</h4>
            <div class="chart-placeholder" id="live-drawdown-chart-{strategy.strategy_id}">
                <canvas width="400" height="200"></canvas>
                <div class="chart-loading">加载图表中...</div>
            </div>
        </div>
        """
    
    def _format_parameter_value(self, param: StrategyParameter) -> str:
        """格式化参数值"""
        if param.type == "number":
            return str(param.value)
        elif param.type == "boolean":
            return "是" if param.value else "否"
        elif param.type == "array":
            if isinstance(param.value, list):
                return f"[{', '.join(map(str, param.value))}]"
            else:
                return str(param.value)
        else:
            return str(param.value)
    
    def _generate_parameter_constraints(self, param: StrategyParameter) -> str:
        """生成参数约束信息"""
        constraints = []
        
        if param.min_value is not None and param.max_value is not None:
            constraints.append(f"范围: {param.min_value} - {param.max_value}")
        elif param.min_value is not None:
            constraints.append(f"最小值: {param.min_value}")
        elif param.max_value is not None:
            constraints.append(f"最大值: {param.max_value}")
        
        if param.options:
            constraints.append(f"选项: {', '.join(map(str, param.options))}")
        
        if constraints:
            return f"""
            <div class="parameter-constraints">
                <small>{' | '.join(constraints)}</small>
            </div>
            """
        
        return ""
    
    def _get_strategy_status_text(self, status: StrategyStatus) -> str:
        """获取策略状态文本"""
        status_texts = {
            StrategyStatus.ACTIVE: "活跃",
            StrategyStatus.INACTIVE: "非活跃",
            StrategyStatus.TESTING: "测试中",
            StrategyStatus.PAUSED: "暂停",
            StrategyStatus.ERROR: "错误"
        }
        return status_texts.get(status, "未知")
    
    def _get_strategy_type_text(self, strategy_type: StrategyType) -> str:
        """获取策略类型文本"""
        type_texts = {
            StrategyType.MOMENTUM: "动量策略",
            StrategyType.MEAN_REVERSION: "均值回归策略",
            StrategyType.ARBITRAGE: "套利策略",
            StrategyType.MARKET_MAKING: "做市策略",
            StrategyType.TREND_FOLLOWING: "趋势跟踪策略",
            StrategyType.STATISTICAL_ARBITRAGE: "统计套利策略",
            StrategyType.MACHINE_LEARNING: "机器学习策略"
        }
        return type_texts.get(strategy_type, "未知策略")
    
    def add_update_callback(self, callback: Callable[[StrategyInfo], None]):
        """添加更新回调函数"""
        self._update_callbacks.append(callback)
    
    def remove_update_callback(self, callback: Callable[[StrategyInfo], None]):
        """移除更新回调函数"""
        if callback in self._update_callbacks:
            self._update_callbacks.remove(callback)
    
    def get_current_strategy(self) -> Optional[StrategyInfo]:
        """获取当前策略"""
        return self._current_strategy
    
    def get_last_update(self) -> Optional[datetime]:
        """获取最后更新时间"""
        return self._last_update
    
    def is_data_stale(self, max_age_seconds: int = 60) -> bool:
        """检查数据是否过期"""
        if not self._last_update:
            return True
        
        age = (datetime.utcnow() - self._last_update).total_seconds()
        return age > max_age_seconds
    
    async def cleanup(self):
        """清理资源"""
        try:
            self.logger.info("正在清理策略详情展示组件...")
            
            # 清理数据
            self._current_strategy = None
            self._last_update = None
            self._update_callbacks.clear()
            
            self.logger.info("策略详情展示组件清理完成")
            
        except Exception as e:
            self.logger.error(f"清理策略详情展示组件失败: {e}")


__all__ = [
    "StrategyDisplayConfig",
    "StrategyDisplayComponent",
]

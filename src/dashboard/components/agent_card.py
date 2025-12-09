"""
港股量化交易 AI Agent 系统 - Agent状态卡片组件

实现AgentCard组件，显示单个Agent的详细状态。
包含状态指示器、绩效指标和快速操作按钮，提供可复用的Agent状态显示组件。
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass

from ...models.agent_dashboard import (
    AgentDashboardData,
    AgentStatus,
    PerformanceMetrics,
    StrategyInfo,
    ResourceUsage
)
from ..agent_control import AgentControlService, ControlActionType


@dataclass
class AgentCardConfig:
    """Agent卡片配置"""
    show_performance_metrics: bool = True
    show_resource_usage: bool = True
    show_strategy_info: bool = True
    enable_controls: bool = True
    auto_refresh_interval: int = 5  # 自动刷新间隔（秒）
    show_detailed_info: bool = False  # 是否显示详细信息


class AgentCardComponent:
    """Agent状态卡片组件"""
    
    def __init__(
        self,
        agent_control_service: Optional[AgentControlService] = None,
        config: AgentCardConfig = None
    ):
        self.agent_control_service = agent_control_service
        self.config = config or AgentCardConfig()
        self.logger = logging.getLogger("hk_quant_system.agent_card")
        
        # 状态管理
        self._current_data: Optional[AgentDashboardData] = None
        self._last_update: Optional[datetime] = None
        self._update_callbacks: List[Callable[[AgentDashboardData], None]] = []
        
        # 后台任务
        self._refresh_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def initialize(self) -> bool:
        """初始化组件"""
        try:
            self.logger.info("正在初始化Agent状态卡片组件...")
            
            # 启动自动刷新任务
            if self.config.auto_refresh_interval > 0:
                self._running = True
                self._refresh_task = asyncio.create_task(self._auto_refresh_loop())
            
            self.logger.info("Agent状态卡片组件初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"Agent状态卡片组件初始化失败: {e}")
            return False
    
    async def _auto_refresh_loop(self):
        """自动刷新循环"""
        while self._running:
            try:
                # 触发数据更新回调
                if self._current_data:
                    for callback in self._update_callbacks:
                        try:
                            callback(self._current_data)
                        except Exception as e:
                            self.logger.error(f"执行更新回调失败: {e}")
                
                # 等待下次刷新
                await asyncio.sleep(self.config.auto_refresh_interval)
                
            except Exception as e:
                self.logger.error(f"自动刷新循环错误: {e}")
                await asyncio.sleep(self.config.auto_refresh_interval)
    
    def update_data(self, agent_data: AgentDashboardData):
        """更新Agent数据"""
        try:
            self._current_data = agent_data
            self._last_update = datetime.utcnow()
            
            # 触发更新回调
            for callback in self._update_callbacks:
                try:
                    callback(agent_data)
                except Exception as e:
                    self.logger.error(f"执行更新回调失败: {e}")
                    
        except Exception as e:
            self.logger.error(f"更新Agent数据失败: {e}")
    
    def render_html(self, agent_data: AgentDashboardData) -> str:
        """渲染Agent卡片的HTML"""
        try:
            # 生成状态指示器
            status_indicator = self._generate_status_indicator(agent_data.status)
            
            # 生成绩效指标
            performance_metrics_html = ""
            if self.config.show_performance_metrics and agent_data.performance_metrics:
                performance_metrics_html = self._generate_performance_metrics_html(agent_data.performance_metrics)
            
            # 生成资源使用情况
            resource_usage_html = ""
            if self.config.show_resource_usage and agent_data.resource_usage:
                resource_usage_html = self._generate_resource_usage_html(agent_data.resource_usage)
            
            # 生成策略信息
            strategy_info_html = ""
            if self.config.show_strategy_info and agent_data.current_strategy:
                strategy_info_html = self._generate_strategy_info_html(agent_data.current_strategy)
            
            # 生成控制按钮
            control_buttons_html = ""
            if self.config.enable_controls and self.agent_control_service:
                control_buttons_html = self._generate_control_buttons_html(agent_data.agent_id, agent_data.status)
            
            # 生成详细信息
            detailed_info_html = ""
            if self.config.show_detailed_info:
                detailed_info_html = self._generate_detailed_info_html(agent_data)
            
            # 组装完整的HTML
            html = f"""
            <div class="agent-card" id="agent-card-{agent_data.agent_id}" data-agent-id="{agent_data.agent_id}">
                <div class="agent-card-header">
                    <div class="agent-title">
                        <h3>{agent_data.agent_type}</h3>
                        <span class="agent-id">ID: {agent_data.agent_id}</span>
                    </div>
                    <div class="agent-status">
                        {status_indicator}
                        <span class="status-text">{self._get_status_text(agent_data.status)}</span>
                    </div>
                </div>
                
                <div class="agent-card-body">
                    <div class="agent-basic-info">
                        <div class="info-item">
                            <span class="label">运行时间:</span>
                            <span class="value">{self._format_uptime(agent_data.uptime_seconds)}</span>
                        </div>
                        <div class="info-item">
                            <span class="label">最后心跳:</span>
                            <span class="value">{self._format_datetime(agent_data.last_heartbeat)}</span>
                        </div>
                        <div class="info-item">
                            <span class="label">处理消息:</span>
                            <span class="value">{agent_data.messages_processed:,}</span>
                        </div>
                        <div class="info-item">
                            <span class="label">错误计数:</span>
                            <span class="value error-count">{agent_data.error_count}</span>
                        </div>
                    </div>
                    
                    {performance_metrics_html}
                    {resource_usage_html}
                    {strategy_info_html}
                    {detailed_info_html}
                </div>
                
                <div class="agent-card-footer">
                    {control_buttons_html}
                    <div class="last-updated">
                        最后更新: {self._format_datetime(agent_data.last_updated)}
                    </div>
                </div>
            </div>
            """
            
            return html
            
        except Exception as e:
            self.logger.error(f"渲染Agent卡片HTML失败: {e}")
            return f"<div class='error'>渲染失败: {str(e)}</div>"
    
    def _generate_status_indicator(self, status: AgentStatus) -> str:
        """生成状态指示器"""
        status_classes = {
            AgentStatus.RUNNING: "status-indicator running",
            AgentStatus.IDLE: "status-indicator idle",
            AgentStatus.ERROR: "status-indicator error",
            AgentStatus.STOPPED: "status-indicator stopped"
        }
        
        status_colors = {
            AgentStatus.RUNNING: "#27ae60",
            AgentStatus.IDLE: "#f39c12",
            AgentStatus.ERROR: "#e74c3c",
            AgentStatus.STOPPED: "#95a5a6"
        }
        
        status_class = status_classes.get(status, "status-indicator unknown")
        status_color = status_colors.get(status, "#95a5a6")
        
        return f"""
        <div class="{status_class}" style="background-color: {status_color};"></div>
        """
    
    def _generate_performance_metrics_html(self, performance: PerformanceMetrics) -> str:
        """生成绩效指标HTML"""
        return f"""
        <div class="performance-metrics">
            <h4>绩效指标</h4>
            <div class="metrics-grid">
                <div class="metric-item">
                    <span class="metric-label">夏普比率</span>
                    <span class="metric-value sharpe-ratio">{performance.sharpe_ratio:.3f}</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">总收益率</span>
                    <span class="metric-value total-return">{performance.total_return:.2%}</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">最大回撤</span>
                    <span class="metric-value max-drawdown">{performance.max_drawdown:.2%}</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">胜率</span>
                    <span class="metric-value win-rate">{performance.win_rate:.1%}</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">交易次数</span>
                    <span class="metric-value trades-count">{performance.trades_count}</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">波动率</span>
                    <span class="metric-value volatility">{performance.volatility:.2%}</span>
                </div>
            </div>
        </div>
        """
    
    def _generate_resource_usage_html(self, resource_usage: ResourceUsage) -> str:
        """生成资源使用情况HTML"""
        return f"""
        <div class="resource-usage">
            <h4>资源使用</h4>
            <div class="resource-grid">
                <div class="resource-item">
                    <span class="resource-label">CPU使用率</span>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {resource_usage.cpu_usage}%; background-color: {self._get_progress_color(resource_usage.cpu_usage)};"></div>
                        <span class="progress-text">{resource_usage.cpu_usage:.1f}%</span>
                    </div>
                </div>
                <div class="resource-item">
                    <span class="resource-label">内存使用率</span>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {resource_usage.memory_usage}%; background-color: {self._get_progress_color(resource_usage.memory_usage)};"></div>
                        <span class="progress-text">{resource_usage.memory_usage:.1f}%</span>
                    </div>
                </div>
                <div class="resource-item">
                    <span class="resource-label">消息处理速度</span>
                    <span class="resource-value">{resource_usage.messages_per_second:.1f} msg/s</span>
                </div>
                <div class="resource-item">
                    <span class="resource-label">队列长度</span>
                    <span class="resource-value">{resource_usage.queue_length}</span>
                </div>
            </div>
        </div>
        """
    
    def _generate_strategy_info_html(self, strategy: StrategyInfo) -> str:
        """生成策略信息HTML"""
        status_colors = {
            "active": "#27ae60",
            "inactive": "#95a5a6",
            "testing": "#f39c12",
            "paused": "#e67e22",
            "error": "#e74c3c"
        }
        
        status_color = status_colors.get(strategy.status.value, "#95a5a6")
        
        return f"""
        <div class="strategy-info">
            <h4>当前策略</h4>
            <div class="strategy-header">
                <span class="strategy-name">{strategy.strategy_name}</span>
                <span class="strategy-status" style="color: {status_color};">{self._get_strategy_status_text(strategy.status)}</span>
            </div>
            <div class="strategy-details">
                <div class="strategy-type">类型: {strategy.strategy_type.value}</div>
                <div class="strategy-version">版本: {strategy.version}</div>
                <div class="strategy-risk">风险等级: {strategy.risk_level}</div>
                {f'<div class="strategy-description">{strategy.description}</div>' if strategy.description else ''}
            </div>
        </div>
        """
    
    def _generate_control_buttons_html(self, agent_id: str, status: AgentStatus) -> str:
        """生成控制按钮HTML"""
        buttons = []
        
        if status != AgentStatus.RUNNING:
            buttons.append(f"""
                <button class="btn btn-success" onclick="controlAgent('{agent_id}', 'start')">
                    <i class="icon-play"></i> 启动
                </button>
            """)
        
        if status == AgentStatus.RUNNING:
            buttons.append(f"""
                <button class="btn btn-warning" onclick="controlAgent('{agent_id}', 'pause')">
                    <i class="icon-pause"></i> 暂停
                </button>
            """)
            
            buttons.append(f"""
                <button class="btn btn-danger" onclick="controlAgent('{agent_id}', 'stop')">
                    <i class="icon-stop"></i> 停止
                </button>
            """)
        
        buttons.append(f"""
            <button class="btn btn-info" onclick="restartAgent('{agent_id}')">
                <i class="icon-refresh"></i> 重启
            </button>
        """)
        
        buttons.append(f"""
            <button class="btn btn-secondary" onclick="showAgentDetails('{agent_id}')">
                <i class="icon-info"></i> 详情
            </button>
        """)
        
        return f"""
        <div class="control-buttons">
            {''.join(buttons)}
        </div>
        """
    
    def _generate_detailed_info_html(self, agent_data: AgentDashboardData) -> str:
        """生成详细信息HTML"""
        return f"""
        <div class="detailed-info">
            <h4>详细信息</h4>
            <div class="detail-grid">
                <div class="detail-item">
                    <span class="detail-label">Agent版本:</span>
                    <span class="detail-value">{agent_data.version}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">配置信息:</span>
                    <span class="detail-value">{len(agent_data.configuration)} 项配置</span>
                </div>
                {f'<div class="detail-item"><span class="detail-label">最后错误:</span><span class="detail-value error-message">{agent_data.last_error}</span></div>' if agent_data.last_error else ''}
                <div class="detail-item">
                    <span class="detail-label">待处理操作:</span>
                    <span class="detail-value">{len(agent_data.pending_actions)}</span>
                </div>
            </div>
        </div>
        """
    
    def _get_status_text(self, status: AgentStatus) -> str:
        """获取状态文本"""
        status_texts = {
            AgentStatus.RUNNING: "运行中",
            AgentStatus.IDLE: "空闲",
            AgentStatus.ERROR: "错误",
            AgentStatus.STOPPED: "已停止"
        }
        return status_texts.get(status, "未知")
    
    def _get_strategy_status_text(self, status) -> str:
        """获取策略状态文本"""
        status_texts = {
            "active": "活跃",
            "inactive": "非活跃",
            "testing": "测试中",
            "paused": "暂停",
            "error": "错误"
        }
        return status_texts.get(status.value if hasattr(status, 'value') else status, "未知")
    
    def _format_uptime(self, uptime_seconds: float) -> str:
        """格式化运行时间"""
        if uptime_seconds < 60:
            return f"{uptime_seconds:.0f}秒"
        elif uptime_seconds < 3600:
            return f"{uptime_seconds/60:.0f}分钟"
        elif uptime_seconds < 86400:
            return f"{uptime_seconds/3600:.1f}小时"
        else:
            return f"{uptime_seconds/86400:.1f}天"
    
    def _format_datetime(self, dt: datetime) -> str:
        """格式化日期时间"""
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    
    def _get_progress_color(self, percentage: float) -> str:
        """获取进度条颜色"""
        if percentage < 50:
            return "#27ae60"  # 绿色
        elif percentage < 80:
            return "#f39c12"  # 橙色
        else:
            return "#e74c3c"  # 红色
    
    async def control_agent(self, agent_id: str, action: str) -> bool:
        """控制Agent"""
        try:
            if not self.agent_control_service:
                self.logger.error("Agent控制服务未初始化")
                return False
            
            if action == "start":
                await self.agent_control_service.start_agent(agent_id, "dashboard_user")
            elif action == "stop":
                await self.agent_control_service.stop_agent(agent_id, "dashboard_user")
            elif action == "restart":
                await self.agent_control_service.restart_agent(agent_id, "dashboard_user")
            elif action == "pause":
                await self.agent_control_service.pause_agent(agent_id, "dashboard_user")
            elif action == "resume":
                await self.agent_control_service.resume_agent(agent_id, "dashboard_user")
            else:
                self.logger.error(f"未知的控制操作: {action}")
                return False
            
            self.logger.info(f"执行Agent控制操作: {action} -> {agent_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"控制Agent失败 {agent_id} {action}: {e}")
            return False
    
    def add_update_callback(self, callback: Callable[[AgentDashboardData], None]):
        """添加更新回调函数"""
        self._update_callbacks.append(callback)
    
    def remove_update_callback(self, callback: Callable[[AgentDashboardData], None]):
        """移除更新回调函数"""
        if callback in self._update_callbacks:
            self._update_callbacks.remove(callback)
    
    def get_current_data(self) -> Optional[AgentDashboardData]:
        """获取当前数据"""
        return self._current_data
    
    def get_last_update(self) -> Optional[datetime]:
        """获取最后更新时间"""
        return self._last_update
    
    def is_data_stale(self, max_age_seconds: int = 30) -> bool:
        """检查数据是否过期"""
        if not self._last_update:
            return True
        
        age = (datetime.utcnow() - self._last_update).total_seconds()
        return age > max_age_seconds
    
    async def cleanup(self):
        """清理资源"""
        try:
            self.logger.info("正在清理Agent状态卡片组件...")
            
            self._running = False
            
            if self._refresh_task:
                self._refresh_task.cancel()
                try:
                    await self._refresh_task
                except asyncio.CancelledError:
                    pass
            
            # 清理数据
            self._current_data = None
            self._last_update = None
            self._update_callbacks.clear()
            
            self.logger.info("Agent状态卡片组件清理完成")
            
        except Exception as e:
            self.logger.error(f"清理Agent状态卡片组件失败: {e}")


__all__ = [
    "AgentCardConfig",
    "AgentCardComponent",
]

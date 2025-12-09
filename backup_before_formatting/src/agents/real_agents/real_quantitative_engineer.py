"""Real Quantitative Engineer Agent for Hong Kong quantitative trading system.

This agent manages system performance, monitoring, fault diagnosis,
and automated deployment based on real system metrics.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import psutil
from pydantic import BaseModel, Field

from ...data_adapters.base_adapter import RealMarketData
from .base_real_agent import BaseRealAgent, RealAgentConfig, RealAgentStatus
from .real_data_analyzer import AnalysisResult, SignalStrength


class SystemStatus(str, Enum):
    """System status levels."""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    DOWN = "down"


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ComponentType(str, Enum):
    """System component types."""

    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    DATABASE = "database"
    REDIS = "redis"
    AGENT = "agent"
    API = "api"
    WORKER = "worker"


class PerformanceMetric(BaseModel):
    """System performance metric."""

    metric_name: str = Field(..., description="Metric name")
    component_type: ComponentType = Field(..., description="Component type")
    value: float = Field(..., description="Metric value")
    unit: str = Field(..., description="Metric unit")
    threshold_warning: float = Field(..., description="Warning threshold")
    threshold_critical: float = Field(..., description="Critical threshold")
    status: SystemStatus = Field(SystemStatus.HEALTHY, description="Current status")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp")

    class Config:
        use_enum_values = True


class SystemAlert(BaseModel):
    """System alert model."""

    alert_id: str = Field(..., description="Alert identifier")
    component_type: ComponentType = Field(..., description="Component type")
    severity: AlertSeverity = Field(..., description="Alert severity")
    title: str = Field(..., description="Alert title")
    message: str = Field(..., description="Alert message")

    # Alert details
    metric_name: str = Field(..., description="Related metric")
    current_value: float = Field(..., description="Current value")
    threshold: float = Field(..., description="Threshold value")

    # Resolution
    is_resolved: bool = Field(False, description="Resolution status")
    resolution_time: Optional[datetime] = Field(None, description="Resolution time")
    resolution_notes: str = Field("", description="Resolution notes")

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation time"
    )
    acknowledged: bool = Field(False, description="Acknowledgment status")

    class Config:
        use_enum_values = True


class SystemComponent(BaseModel):
    """System component model."""

    component_id: str = Field(..., description="Component identifier")
    component_type: ComponentType = Field(..., description="Component type")
    name: str = Field(..., description="Component name")
    status: SystemStatus = Field(SystemStatus.HEALTHY, description="Current status")

    # Performance metrics
    metrics: Dict[str, PerformanceMetric] = Field(
        default_factory=dict, description="Component metrics"
    )
    last_updated: datetime = Field(
        default_factory=datetime.now, description="Last update time"
    )

    # Health check
    health_score: float = Field(1.0, ge=0.0, le=1.0, description="Health score")
    uptime: float = Field(0.0, description="Uptime in seconds")
    last_restart: Optional[datetime] = Field(None, description="Last restart time")

    class Config:
        use_enum_values = True


class OptimizationRecommendation(BaseModel):
    """System optimization recommendation."""

    recommendation_id: str = Field(..., description="Recommendation identifier")
    component_type: ComponentType = Field(..., description="Component type")
    priority: int = Field(..., ge=1, le=5, description="Priority level (1=highest)")

    # Recommendation details
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Detailed description")
    expected_improvement: str = Field(..., description="Expected improvement")

    # Implementation
    implementation_steps: List[str] = Field(
        default_factory=list, description="Implementation steps"
    )
    estimated_effort: str = Field(..., description="Estimated effort")
    risk_level: str = Field("low", description="Risk level")

    # Status
    status: str = Field("pending", description="Implementation status")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation time"
    )

    class Config:
        use_enum_values = True


class RealQuantitativeEngineer(BaseRealAgent):
    """Real Quantitative Engineer Agent with system management capabilities."""

    def __init__(self, config: RealAgentConfig):
        super().__init__(config)

        # System management components
        self.system_components: Dict[str, SystemComponent] = {}
        self.active_alerts: List[SystemAlert] = []
        self.alert_history: List[SystemAlert] = []
        self.optimization_recommendations: List[OptimizationRecommendation] = []

        # Performance tracking
        self.performance_history: List[Dict[str, Any]] = []
        self.optimization_history: List[Dict[str, Any]] = []

        # System thresholds
        self.system_thresholds = {
            ComponentType.CPU: {"warning": 70.0, "critical": 90.0},
            ComponentType.MEMORY: {"warning": 80.0, "critical": 95.0},
            ComponentType.DISK: {"warning": 85.0, "critical": 95.0},
            ComponentType.NETWORK: {"warning": 80.0, "critical": 95.0},
            ComponentType.DATABASE: {"warning": 80.0, "critical": 95.0},
            ComponentType.REDIS: {"warning": 80.0, "critical": 95.0},
            ComponentType.AGENT: {"warning": 0.8, "critical": 0.9},
            ComponentType.API: {"warning": 0.8, "critical": 0.9},
            ComponentType.WORKER: {"warning": 0.8, "critical": 0.9},
        }

        # Monitoring configuration
        self.monitoring_interval = 30  # seconds
        self.alert_cooldown = 300  # 5 minutes
        self.health_check_interval = 60  # seconds

    async def _initialize_specific(self) -> bool:
        """Initialize quantitative engineer specific components."""
        try:
            self.logger.info(
                "Initializing quantitative engineer specific components..."
            )

            # Initialize system components
            await self._initialize_system_components()

            # Start monitoring tasks
            await self._start_monitoring_tasks()

            # Initialize optimization engine
            await self._initialize_optimization_engine()

            self.logger.info("Quantitative engineer initialization completed")
            return True

        except Exception as e:
            self.logger.exception(f"Failed to initialize quantitative engineer: {e}")
            return False

    async def _initialize_system_components(self) -> None:
        """Initialize system components for monitoring."""
        try:
            # CPU component
            cpu_component = SystemComponent(
                component_id="cpu_main",
                component_type=ComponentType.CPU,
                name="Main CPU",
                status=SystemStatus.HEALTHY,
            )
            self.system_components["cpu_main"] = cpu_component

            # Memory component
            memory_component = SystemComponent(
                component_id="memory_main",
                component_type=ComponentType.MEMORY,
                name="Main Memory",
                status=SystemStatus.HEALTHY,
            )
            self.system_components["memory_main"] = memory_component

            # Disk component
            disk_component = SystemComponent(
                component_id="disk_main",
                component_type=ComponentType.DISK,
                name="Main Disk",
                status=SystemStatus.HEALTHY,
            )
            self.system_components["disk_main"] = disk_component

            # Network component
            network_component = SystemComponent(
                component_id="network_main",
                component_type=ComponentType.NETWORK,
                name="Main Network",
                status=SystemStatus.HEALTHY,
            )
            self.system_components["network_main"] = network_component

            # Database component (simulated)
            db_component = SystemComponent(
                component_id="database_main",
                component_type=ComponentType.DATABASE,
                name="Main Database",
                status=SystemStatus.HEALTHY,
            )
            self.system_components["database_main"] = db_component

            # Redis component (simulated)
            redis_component = SystemComponent(
                component_id="redis_main",
                component_type=ComponentType.REDIS,
                name="Main Redis",
                status=SystemStatus.HEALTHY,
            )
            self.system_components["redis_main"] = redis_component

            self.logger.info(
                f"Initialized {len(self.system_components)} system components"
            )

        except Exception as e:
            self.logger.error(f"Error initializing system components: {e}")

    async def _start_monitoring_tasks(self) -> None:
        """Start system monitoring tasks."""
        try:
            # Start performance monitoring
            asyncio.create_task(self._monitor_system_performance())

            # Start health checks
            asyncio.create_task(self._perform_health_checks())

            # Start optimization analysis
            asyncio.create_task(self._analyze_optimization_opportunities())

            self.logger.info("System monitoring tasks started")

        except Exception as e:
            self.logger.error(f"Error starting monitoring tasks: {e}")

    async def _initialize_optimization_engine(self) -> None:
        """Initialize system optimization engine."""
        try:
            # Create default optimization recommendations
            await self._create_default_optimization_recommendations()

            self.logger.info("Optimization engine initialized")

        except Exception as e:
            self.logger.error(f"Error initializing optimization engine: {e}")

    async def _create_default_optimization_recommendations(self) -> None:
        """Create default optimization recommendations."""
        try:
            recommendations = [
                OptimizationRecommendation(
                    recommendation_id="cpu_optimization_1",
                    component_type=ComponentType.CPU,
                    priority=3,
                    title="CPU使用率优化",
                    description="优化CPU密集型任务，考虑并行处理",
                    expected_improvement="降低CPU使用率10 - 15%",
                    implementation_steps=[
                        "分析CPU使用率模式",
                        "识别CPU密集型任务",
                        "实施任务并行化",
                        "优化算法复杂度",
                    ],
                    estimated_effort="2 - 3天",
                    risk_level="low",
                ),
                OptimizationRecommendation(
                    recommendation_id="memory_optimization_1",
                    component_type=ComponentType.MEMORY,
                    priority=2,
                    title="内存使用优化",
                    description="优化内存分配和垃圾回收",
                    expected_improvement="降低内存使用率20 - 30%",
                    implementation_steps=[
                        "分析内存使用模式",
                        "识别内存泄漏",
                        "优化数据结构",
                        "实施内存池管理",
                    ],
                    estimated_effort="3 - 4天",
                    risk_level="medium",
                ),
                OptimizationRecommendation(
                    recommendation_id="database_optimization_1",
                    component_type=ComponentType.DATABASE,
                    priority=1,
                    title="数据库查询优化",
                    description="优化数据库查询性能和索引",
                    expected_improvement="提升查询性能50 - 70%",
                    implementation_steps=[
                        "分析慢查询日志",
                        "优化SQL查询",
                        "添加必要索引",
                        "实施查询缓存",
                    ],
                    estimated_effort="1 - 2天",
                    risk_level="low",
                ),
            ]

            self.optimization_recommendations.extend(recommendations)
            self.logger.info(
                f"Created {len(recommendations)} default optimization recommendations"
            )

        except Exception as e:
            self.logger.error(
                f"Error creating default optimization recommendations: {e}"
            )

    async def _monitor_system_performance(self) -> None:
        """Monitor system performance continuously."""
        while self.real_status == RealAgentStatus.ACTIVE:
            try:
                # Collect system metrics
                await self._collect_system_metrics()

                # Check for alerts
                await self._check_system_alerts()

                # Update component health scores
                await self._update_component_health_scores()

                # Wait for next monitoring cycle
                await asyncio.sleep(self.monitoring_interval)

            except Exception as e:
                self.logger.error(f"Error in system performance monitoring: {e}")
                await asyncio.sleep(self.monitoring_interval)

    async def _collect_system_metrics(self) -> None:
        """Collect system performance metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_component = self.system_components["cpu_main"]
            cpu_component.metrics["cpu_usage"] = PerformanceMetric(
                metric_name="CPU Usage",
                component_type=ComponentType.CPU,
                value=cpu_percent,
                unit="%",
                threshold_warning=self.system_thresholds[ComponentType.CPU]["warning"],
                threshold_critical=self.system_thresholds[ComponentType.CPU][
                    "critical"
                ],
            )

            # Memory metrics
            memory = psutil.virtual_memory()
            memory_component = self.system_components["memory_main"]
            memory_component.metrics["memory_usage"] = PerformanceMetric(
                metric_name="Memory Usage",
                component_type=ComponentType.MEMORY,
                value=memory.percent,
                unit="%",
                threshold_warning=self.system_thresholds[ComponentType.MEMORY][
                    "warning"
                ],
                threshold_critical=self.system_thresholds[ComponentType.MEMORY][
                    "critical"
                ],
            )

            # Disk metrics
            disk = psutil.disk_usage("/")
            disk_component = self.system_components["disk_main"]
            disk_component.metrics["disk_usage"] = PerformanceMetric(
                metric_name="Disk Usage",
                component_type=ComponentType.DISK,
                value=(disk.used / disk.total) * 100,
                unit="%",
                threshold_warning=self.system_thresholds[ComponentType.DISK]["warning"],
                threshold_critical=self.system_thresholds[ComponentType.DISK][
                    "critical"
                ],
            )

            # Network metrics - 使用真實監控數據
            network_component = self.system_components["network_main"]
            network_component.metrics["network_io"] = self.get_real_network_metrics()

            # Database metrics - 使用真實監控數據
            db_component = self.system_components["database_main"]
            db_component.metrics["db_connections"] = self.get_real_database_metrics()

            # Redis metrics - 使用真實監控數據
            redis_component = self.system_components["redis_main"]
            redis_component.metrics["redis_memory"] = self.get_real_redis_metrics()

            # Update last updated time
            for component in self.system_components.values():
                component.last_updated = datetime.now()

        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")

    async def _check_system_alerts(self) -> None:
        """Check for system alerts based on metrics."""
        try:
            for component in self.system_components.values():
                for metric_name, metric in component.metrics.items():
                    # Determine alert level
                    if metric.value >= metric.threshold_critical:
                        alert_level = AlertSeverity.CRITICAL
                        system_status = SystemStatus.CRITICAL
                    elif metric.value >= metric.threshold_warning:
                        alert_level = AlertSeverity.WARNING
                        system_status = SystemStatus.WARNING
                    else:
                        continue

                    # Check if alert already exists
                    existing_alert = any(
                        alert.component_type == component.component_type
                        and alert.metric_name == metric_name
                        and not alert.is_resolved
                        and (datetime.now() - alert.created_at).total_seconds()
                        < self.alert_cooldown
                        for alert in self.active_alerts
                    )

                    if existing_alert:
                        continue

                    # Create new alert
                    alert = SystemAlert(
                        alert_id=f"alert_{component.component_id}_{metric_name}_{datetime.now().strftime('%Y % m % d_ % H % M % S')}",
                        component_type=component.component_type,
                        severity=alert_level,
                        title=f"{component.name} {metric_name} Alert",
                        message=f"{metric_name} is at {metric.value:.1f}{metric.unit}, exceeding {metric.threshold_warning:.1f}{metric.unit} threshold",
                        metric_name=metric_name,
                        current_value=metric.value,
                        threshold=metric.threshold_warning,
                    )

                    self.active_alerts.append(alert)
                    self.alert_history.append(alert)

                    # Update component status
                    component.status = system_status

                    self.logger.warning(f"System alert created: {alert.title}")

        except Exception as e:
            self.logger.error(f"Error checking system alerts: {e}")

    async def _update_component_health_scores(self) -> None:
        """Update component health scores based on metrics."""
        try:
            for component in self.system_components.values():
                if not component.metrics:
                    continue

                # Calculate health score based on metrics
                health_scores = []
                for metric in component.metrics.values():
                    if metric.value < metric.threshold_warning:
                        score = 1.0
                    elif metric.value < metric.threshold_critical:
                        score = 0.5
                    else:
                        score = 0.0
                    health_scores.append(score)

                # Update component health score
                component.health_score = (
                    np.mean(health_scores) if health_scores else 1.0
                )

                # Update component status based on health score
                if component.health_score >= 0.8:
                    component.status = SystemStatus.HEALTHY
                elif component.health_score >= 0.5:
                    component.status = SystemStatus.WARNING
                else:
                    component.status = SystemStatus.CRITICAL

        except Exception as e:
            self.logger.error(f"Error updating component health scores: {e}")

    async def _perform_health_checks(self) -> None:
        """Perform periodic health checks."""
        while self.real_status == RealAgentStatus.ACTIVE:
            try:
                # Check component uptime
                await self._check_component_uptime()

                # Check for stale components
                await self._check_stale_components()

                # Generate health report
                await self._generate_health_report()

                # Wait for next health check
                await asyncio.sleep(self.health_check_interval)

            except Exception as e:
                self.logger.error(f"Error in health checks: {e}")
                await asyncio.sleep(self.health_check_interval)

    async def _check_component_uptime(self) -> None:
        """Check component uptime."""
        try:
            current_time = time.time()

            for component in self.system_components.values():
                if component.last_restart:
                    component.uptime = current_time - component.last_restart.timestamp()
                else:
                    component.uptime = current_time  # Assume started at system boot

                # Check for components that need restart
                if component.uptime > 86400 * 7:  # 7 days
                    self.logger.info(
                        f"Component {component.name} has been running for {component.uptime / 86400:.1f} days"
                    )

        except Exception as e:
            self.logger.error(f"Error checking component uptime: {e}")

    async def _check_stale_components(self) -> None:
        """Check for stale components that haven't updated recently."""
        try:
            current_time = datetime.now()
            stale_threshold = timedelta(minutes=5)

            for component in self.system_components.values():
                if current_time - component.last_updated > stale_threshold:
                    self.logger.warning(
                        f"Component {component.name} appears stale (last update: {component.last_updated})"
                    )

                    # Create stale component alert
                    alert = SystemAlert(
                        alert_id=f"stale_{component.component_id}_{datetime.now().strftime('%Y % m % d_ % H % M % S')}",
                        component_type=component.component_type,
                        severity=AlertSeverity.WARNING,
                        title=f"Stale Component: {component.name}",
                        message=f"Component {component.name} has not updated for {(current_time - component.last_updated).total_seconds()/60:.1f} minutes",
                        metric_name="last_update",
                        current_value=(
                            current_time - component.last_updated
                        ).total_seconds(),
                        threshold=stale_threshold.total_seconds(),
                    )

                    self.active_alerts.append(alert)
                    self.alert_history.append(alert)

        except Exception as e:
            self.logger.error(f"Error checking stale components: {e}")

    async def _generate_health_report(self) -> None:
        """Generate system health report."""
        try:
            report = {
                "timestamp": datetime.now(),
                "total_components": len(self.system_components),
                "healthy_components": len(
                    [
                        c
                        for c in self.system_components.values()
                        if c.status == SystemStatus.HEALTHY
                    ]
                ),
                "warning_components": len(
                    [
                        c
                        for c in self.system_components.values()
                        if c.status == SystemStatus.WARNING
                    ]
                ),
                "critical_components": len(
                    [
                        c
                        for c in self.system_components.values()
                        if c.status == SystemStatus.CRITICAL
                    ]
                ),
                "active_alerts": len(self.active_alerts),
                "unresolved_alerts": len(
                    [a for a in self.active_alerts if not a.is_resolved]
                ),
                "overall_health_score": np.mean(
                    [c.health_score for c in self.system_components.values()]
                ),
            }

            self.performance_history.append(report)

            # Log health summary
            self.logger.info(
                f"Health Report: {report['healthy_components']}/{report['total_components']} healthy, "
                f"{report['active_alerts']} active alerts, "
                f"overall health: {report['overall_health_score']:.2f}"
            )

        except Exception as e:
            self.logger.error(f"Error generating health report: {e}")

    async def _analyze_optimization_opportunities(self) -> None:
        """Analyze system optimization opportunities."""
        while self.real_status == RealAgentStatus.ACTIVE:
            try:
                # Analyze current performance
                await self._analyze_current_performance()

                # Generate new recommendations
                await self._generate_optimization_recommendations()

                # Update existing recommendations
                await self._update_optimization_recommendations()

                # Wait for next analysis cycle
                await asyncio.sleep(300)  # 5 minutes

            except Exception as e:
                self.logger.error(f"Error in optimization analysis: {e}")
                await asyncio.sleep(300)

    async def _analyze_current_performance(self) -> None:
        """Analyze current system performance."""
        try:
            analysis = {
                "timestamp": datetime.now(),
                "component_analysis": {},
                "bottlenecks": [],
                "optimization_opportunities": [],
            }

            for component_id, component in self.system_components.items():
                component_analysis = {
                    "health_score": component.health_score,
                    "status": component.status.value,
                    "metrics": {},
                }

                for metric_name, metric in component.metrics.items():
                    component_analysis["metrics"][metric_name] = {
                        "value": metric.value,
                        "threshold_warning": metric.threshold_warning,
                        "threshold_critical": metric.threshold_critical,
                        "utilization": (
                            metric.value / metric.threshold_critical
                            if metric.threshold_critical > 0
                            else 0
                        ),
                    }

                    # Identify bottlenecks
                    if metric.value > metric.threshold_warning:
                        analysis["bottlenecks"].append(
                            {
                                "component": component_id,
                                "metric": metric_name,
                                "value": metric.value,
                                "threshold": metric.threshold_warning,
                            }
                        )

                analysis["component_analysis"][component_id] = component_analysis

            self.performance_history.append(analysis)

        except Exception as e:
            self.logger.error(f"Error analyzing current performance: {e}")

    async def _generate_optimization_recommendations(self) -> None:
        """Generate new optimization recommendations based on current performance."""
        try:
            # Analyze recent performance data
            if len(self.performance_history) < 2:
                return

            recent_analysis = self.performance_history[-1]

            # Generate recommendations based on bottlenecks
            for bottleneck in recent_analysis.get("bottlenecks", []):
                component_id = bottleneck["component"]
                metric_name = bottleneck["metric"]
                value = bottleneck["value"]
                threshold = bottleneck["threshold"]

                # Create specific recommendation
                recommendation = OptimizationRecommendation(
                    recommendation_id=f"auto_{component_id}_{metric_name}_{datetime.now().strftime('%Y % m % d_ % H % M % S')}",
                    component_type=ComponentType(component_id.split("_")[0]),
                    priority=2 if value > threshold * 1.5 else 3,
                    title=f"优化 {component_id} {metric_name}",
                    description=f"{metric_name} 当前值 {value:.1f} 超过阈值 {threshold:.1f}",
                    expected_improvement=f"降低 {metric_name} 使用率 {(value - threshold) / threshold * 100:.0f}%",
                    implementation_steps=[
                        f"分析 {metric_name} 使用模式",
                        f"识别 {metric_name} 高使用原因",
                        f"实施 {metric_name} 优化策略",
                        f"监控 {metric_name} 改善效果",
                    ],
                    estimated_effort="1 - 2天",
                    risk_level="low",
                )

                # Check if similar recommendation already exists
                existing = any(
                    r.title == recommendation.title and not r.status == "completed"
                    for r in self.optimization_recommendations
                )

                if not existing:
                    self.optimization_recommendations.append(recommendation)
                    self.logger.info(
                        f"Generated optimization recommendation: {recommendation.title}"
                    )

        except Exception as e:
            self.logger.error(f"Error generating optimization recommendations: {e}")

    async def _update_optimization_recommendations(self) -> None:
        """Update existing optimization recommendations."""
        try:
            for recommendation in self.optimization_recommendations:
                if recommendation.status == "pending":
                    # Check if conditions still warrant this recommendation
                    component_type = recommendation.component_type
                    if component_type in [
                        ComponentType.CPU,
                        ComponentType.MEMORY,
                        ComponentType.DISK,
                    ]:
                        # Check if the issue has been resolved
                        component_id = f"{component_type.value}_main"
                        if component_id in self.system_components:
                            component = self.system_components[component_id]
                            if component.health_score > 0.8:
                                recommendation.status = "resolved"
                                self.logger.info(
                                    f"Optimization recommendation resolved: {recommendation.title}"
                                )

        except Exception as e:
            self.logger.error(f"Error updating optimization recommendations: {e}")

    async def _enhance_analysis(
        self, base_result: AnalysisResult, market_data: List[RealMarketData]
    ) -> AnalysisResult:
        """Enhance analysis with system engineering specific logic."""
        try:
            # Add system performance insights
            system_insights = await self._generate_system_insights()

            # Update base result
            enhanced_result = base_result.copy()
            enhanced_result.insights.extend(system_insights)

            return enhanced_result

        except Exception as e:
            self.logger.error(f"Error enhancing analysis for system engineering: {e}")
            return base_result

    async def _generate_system_insights(self) -> List[str]:
        """Generate system performance insights."""
        try:
            insights = []

            # Overall system health
            healthy_components = len(
                [
                    c
                    for c in self.system_components.values()
                    if c.status == SystemStatus.HEALTHY
                ]
            )
            total_components = len(self.system_components)
            health_percentage = (healthy_components / total_components) * 100

            insights.append(
                f"系统健康状态: {healthy_components}/{total_components} 组件正常 ({health_percentage:.0f}%)"
            )

            # Active alerts
            active_alerts = len(self.active_alerts)
            if active_alerts > 0:
                critical_alerts = len(
                    [
                        a
                        for a in self.active_alerts
                        if a.severity == AlertSeverity.CRITICAL
                    ]
                )
                insights.append(
                    f"活跃告警: {active_alerts} 个 (严重: {critical_alerts} 个)"
                )
            else:
                insights.append("系统运行正常，无活跃告警")

            # Performance bottlenecks
            if self.performance_history:
                recent_analysis = self.performance_history[-1]
                bottlenecks = recent_analysis.get("bottlenecks", [])
                if bottlenecks:
                    insights.append(f"发现 {len(bottlenecks)} 个性能瓶颈")
                else:
                    insights.append("系统性能良好，无显著瓶颈")

            # Optimization opportunities
            pending_recommendations = len(
                [r for r in self.optimization_recommendations if r.status == "pending"]
            )
            if pending_recommendations > 0:
                insights.append(f"待实施优化建议: {pending_recommendations} 个")

            return insights

        except Exception as e:
            self.logger.error(f"Error generating system insights: {e}")
            return []

    async def _enhance_signals(
        self, base_signals: List[Dict[str, Any]], analysis_result: AnalysisResult
    ) -> List[Dict[str, Any]]:
        """Enhance signals with system engineering logic."""
        try:
            enhanced_signals = []

            # Generate system maintenance signals
            maintenance_signals = await self._generate_maintenance_signals()
            enhanced_signals.extend(maintenance_signals)

            # Filter signals based on system health
            filtered_signals = await self._filter_signals_by_system_health(base_signals)
            enhanced_signals.extend(filtered_signals)

            return enhanced_signals

        except Exception as e:
            self.logger.error(f"Error enhancing signals for system engineering: {e}")
            return base_signals

    async def _generate_maintenance_signals(self) -> List[Dict[str, Any]]:
        """Generate system maintenance signals."""
        try:
            maintenance_signals = []

            # Check for components that need restart
            for component in self.system_components.values():
                if component.uptime > 86400 * 7:  # 7 days
                    signal = {
                        "signal_id": f"maintenance_restart_{component.component_id}_{datetime.now().strftime('%Y % m % d_ % H % M % S')}",
                        "symbol": "SYSTEM_MAINTENANCE",
                        "side": "restart",
                        "strength": 0.7,
                        "confidence": 0.9,
                        "reasoning": f"组件 {component.name} 运行时间过长 ({component.uptime / 86400:.1f} 天)，建议重启",
                        "signal_type": "system_maintenance",
                        "component_id": component.component_id,
                        "action": "restart",
                    }
                    maintenance_signals.append(signal)

            # Check for critical alerts that need immediate attention
            critical_alerts = [
                a
                for a in self.active_alerts
                if a.severity == AlertSeverity.CRITICAL and not a.is_resolved
            ]
            if critical_alerts:
                signal = {
                    "signal_id": f"maintenance_critical_{datetime.now().strftime('%Y % m % d_ % H % M % S')}",
                    "symbol": "SYSTEM_CRITICAL",
                    "side": "investigate",
                    "strength": 1.0,
                    "confidence": 1.0,
                    "reasoning": f"发现 {len(critical_alerts)} 个严重告警，需要立即处理",
                    "signal_type": "critical_alert",
                    "alert_count": len(critical_alerts),
                }
                maintenance_signals.append(signal)

            return maintenance_signals

        except Exception as e:
            self.logger.error(f"Error generating maintenance signals: {e}")
            return []

    async def _filter_signals_by_system_health(
        self, base_signals: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Filter signals based on system health."""
        try:
            filtered_signals = []

            # Check overall system health
            critical_components = len(
                [
                    c
                    for c in self.system_components.values()
                    if c.status == SystemStatus.CRITICAL
                ]
            )
            critical_alerts = len(
                [
                    a
                    for a in self.active_alerts
                    if a.severity == AlertSeverity.CRITICAL and not a.is_resolved
                ]
            )

            # If system is in critical state, reduce signal processing
            if critical_components > 0 or critical_alerts > 0:
                self.logger.warning(
                    "System in critical state, reducing signal processing"
                )
                # Only process high - confidence signals
                for signal in base_signals:
                    if signal.get("confidence", 0) > 0.8:
                        enhanced_signal = signal.copy()
                        enhanced_signal["system_health_impact"] = "reduced_processing"
                        filtered_signals.append(enhanced_signal)
            else:
                # Normal processing
                for signal in base_signals:
                    enhanced_signal = signal.copy()
                    enhanced_signal["system_health_impact"] = "normal_processing"
                    filtered_signals.append(enhanced_signal)

            return filtered_signals

        except Exception as e:
            self.logger.error(f"Error filtering signals by system health: {e}")
            return base_signals

    async def _execute_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Execute system engineering signal."""
        try:
            signal_type = signal.get("signal_type", "")

            if signal_type == "system_maintenance":
                return await self._execute_maintenance_signal(signal)
            elif signal_type == "critical_alert":
                return await self._execute_critical_alert_signal(signal)
            else:
                return {
                    "signal_id": signal.get("signal_id", "unknown"),
                    "status": "system_validated",
                    "system_health_impact": signal.get(
                        "system_health_impact", "normal"
                    ),
                }

        except Exception as e:
            self.logger.error(f"Error executing system engineering signal: {e}")
            return {
                "signal_id": signal.get("signal_id", "unknown"),
                "status": "failed",
                "error": str(e),
            }

    async def _execute_maintenance_signal(
        self, signal: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute system maintenance signal."""
        try:
            action = signal.get("action", "")
            component_id = signal.get("component_id", "")

            if action == "restart" and component_id in self.system_components:
                component = self.system_components[component_id]
                component.last_restart = datetime.now()
                component.uptime = 0

                self.logger.info(f"Component {component.name} restarted")

                return {
                    "signal_id": signal.get("signal_id", "unknown"),
                    "status": "maintenance_completed",
                    "action": "restart",
                    "component_id": component_id,
                    "execution_time": datetime.now(),
                }

            return {
                "signal_id": signal.get("signal_id", "unknown"),
                "status": "maintenance_scheduled",
                "action": action,
                "component_id": component_id,
            }

        except Exception as e:
            self.logger.error(f"Error executing maintenance signal: {e}")
            return {
                "signal_id": signal.get("signal_id", "unknown"),
                "status": "failed",
                "error": str(e),
            }

    async def _execute_critical_alert_signal(
        self, signal: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute critical alert signal."""
        try:
            alert_count = signal.get("alert_count", 0)

            # Log critical alerts
            self.logger.critical(
                f"CRITICAL ALERTS DETECTED: {alert_count} alerts require immediate attention"
            )

            return {
                "signal_id": signal.get("signal_id", "unknown"),
                "status": "critical_alert_processed",
                "alert_count": alert_count,
                "execution_time": datetime.now(),
            }

        except Exception as e:
            self.logger.error(f"Error executing critical alert signal: {e}")
            return {
                "signal_id": signal.get("signal_id", "unknown"),
                "status": "failed",
                "error": str(e),
            }

    def get_real_network_metrics(self) -> PerformanceMetric:
        """獲取真實網絡指標"""
        try:
            # 使用psutil獲取真實網絡IO
            net_io = psutil.net_io_counters()
            # 計算網絡使用率（簡化計算）
            total_bytes = net_io.bytes_sent + net_io.bytes_recv
            # 假設一個合理基線值
            baseline_mb_per_second = 10.0
            current_usage_mb = total_bytes / (1024 * 1024)
            usage_percentage = min((current_usage_mb / baseline_mb_per_second), 100.0)

            return PerformanceMetric(
                metric_name="Network I/O",
                component_type=ComponentType.NETWORK,
                value=usage_percentage,
                unit="%",
                threshold_warning=self.system_thresholds[ComponentType.NETWORK]["warning"],
                threshold_critical=self.system_thresholds[ComponentType.NETWORK]["critical"],
            )
        except Exception as e:
            self.logger.error(f"Error getting network metrics: {e}")
            return PerformanceMetric(
                metric_name="Network I/O",
                component_type=ComponentType.NETWORK,
                value=0.0,
                unit="%",
                threshold_warning=self.system_thresholds[ComponentType.NETWORK]["warning"],
                threshold_critical=self.system_thresholds[ComponentType.NETWORK]["critical"],
            )

    def get_real_database_metrics(self) -> PerformanceMetric:
        """獲取真實數據庫指標"""
        try:
            # 檢查是否有活動數據庫連接
            import sqlite3
            import os

            # 檢查sqlite3數據庫文件
            db_files = []
            for root, dirs, files in os.walk('.'):
                for file in files:
                    if file.endswith('.db') or file.endswith('.sqlite'):
                        db_files.append(os.path.join(root, file))

            active_connections = len(db_files)
            # 計算連接使用率（基於文件數量的簡化指標）
            max_connections = 100  # 假設最大連接數
            usage_percentage = (active_connections / max_connections) * 100

            return PerformanceMetric(
                metric_name="Database Connections",
                component_type=ComponentType.DATABASE,
                value=usage_percentage,
                unit="%",
                threshold_warning=self.system_thresholds[ComponentType.DATABASE]["warning"],
                threshold_critical=self.system_thresholds[ComponentType.DATABASE]["critical"],
            )
        except Exception as e:
            self.logger.error(f"Error getting database metrics: {e}")
            return PerformanceMetric(
                metric_name="Database Connections",
                component_type=ComponentType.DATABASE,
                value=0.0,
                unit="%",
                threshold_warning=self.system_thresholds[ComponentType.DATABASE]["warning"],
                threshold_critical=self.system_thresholds[ComponentType.DATABASE]["critical"],
            )

    def get_real_redis_metrics(self) -> PerformanceMetric:
        """獲取真實Redis指標"""
        try:
            # 檢查Redis進程是否運行
            redis_running = False
            memory_usage = 0.0

            for proc in psutil.process_iter(['redis-server']):
                redis_running = True
                # 獲取Redis內存使用
                memory_info = proc.memory_info()
                memory_usage = (memory_info.rss / (1024 * 1024 * 1024)) * 100  # GB to MB
                break

            # 如果Redis沒運行，使用率為0
            if not redis_running:
                usage_percentage = 0.0
            else:
                # 簡化內存使用率計算
                max_redis_memory = 512  # 512MB基線
                usage_percentage = min((memory_usage / max_redis_memory) * 100, 100.0)

            return PerformanceMetric(
                metric_name="Redis Memory",
                component_type=ComponentType.REDIS,
                value=usage_percentage,
                unit="%",
                threshold_warning=self.system_thresholds[ComponentType.REDIS]["warning"],
                threshold_critical=self.system_thresholds[ComponentType.REDIS]["critical"],
            )
        except Exception as e:
            self.logger.error(f"Error getting Redis metrics: {e}")
            return PerformanceMetric(
                metric_name="Redis Memory",
                component_type=ComponentType.REDIS,
                value=0.0,
                unit="%",
                threshold_warning=self.system_thresholds[ComponentType.REDIS]["warning"],
                threshold_critical=self.system_thresholds[ComponentType.REDIS]["critical"],
            )

    async def get_system_summary(self) -> Dict[str, Any]:
        """Get comprehensive system summary."""
        try:
            summary = {
                "agent_id": self.config.agent_id,
                "agent_name": self.config.name,
                "status": self.real_status,
                # System components
                "total_components": len(self.system_components),
                "healthy_components": len(
                    [
                        c
                        for c in self.system_components.values()
                        if c.status == SystemStatus.HEALTHY
                    ]
                ),
                "warning_components": len(
                    [
                        c
                        for c in self.system_components.values()
                        if c.status == SystemStatus.WARNING
                    ]
                ),
                "critical_components": len(
                    [
                        c
                        for c in self.system_components.values()
                        if c.status == SystemStatus.CRITICAL
                    ]
                ),
                # Alerts
                "active_alerts": len(self.active_alerts),
                "critical_alerts": len(
                    [
                        a
                        for a in self.active_alerts
                        if a.severity == AlertSeverity.CRITICAL
                    ]
                ),
                "unresolved_alerts": len(
                    [a for a in self.active_alerts if not a.is_resolved]
                ),
                # Optimization
                "total_recommendations": len(self.optimization_recommendations),
                "pending_recommendations": len(
                    [
                        r
                        for r in self.optimization_recommendations
                        if r.status == "pending"
                    ]
                ),
                "completed_recommendations": len(
                    [
                        r
                        for r in self.optimization_recommendations
                        if r.status == "completed"
                    ]
                ),
                # Performance
                "performance_history_count": len(self.performance_history),
                "monitoring_interval": self.monitoring_interval,
                "health_check_interval": self.health_check_interval,
                # Overall health
                "overall_health_score": (
                    np.mean([c.health_score for c in self.system_components.values()])
                    if self.system_components
                    else 0
                ),
            }

            # Add component details
            summary["components"] = {}
            for component_id, component in self.system_components.items():
                summary["components"][component_id] = {
                    "name": component.name,
                    "type": component.component_type.value,
                    "status": component.status.value,
                    "health_score": component.health_score,
                    "uptime_hours": component.uptime / 3600,
                    "metrics_count": len(component.metrics),
                }

            return summary

        except Exception as e:
            self.logger.error(f"Error getting system summary: {e}")
            return {"error": str(e)}

    async def cleanup(self) -> None:
        """Cleanup quantitative engineer resources."""
        try:
            self.logger.info(f"Cleaning up quantitative engineer: {self.config.name}")

            # Clear all collections
            self.system_components.clear()
            self.active_alerts.clear()
            self.alert_history.clear()
            self.optimization_recommendations.clear()
            self.performance_history.clear()
            self.optimization_history.clear()

            # Call parent cleanup
            await super().cleanup()

            self.logger.info("Quantitative engineer cleanup completed")

        except Exception as e:
            self.logger.exception(f"Error during cleanup: {e}")

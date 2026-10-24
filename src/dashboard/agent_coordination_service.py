"""
Agent协作监控服务

提供7个AI Agent的状态监控、任务协调、性能分析和协作效率管理功能
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import numpy as np
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
import psutil
import platform


class AgentType(Enum):
    """Agent类型枚举"""
    DATA_SCIENTIST = "data_scientist"
    PORTFOLIO_MANAGER = "portfolio_manager"
    RISK_ANALYST = "risk_analyst"
    QUANTITATIVE_ANALYST = "quantitative_analyst"
    RESEARCH_ANALYST = "research_analyst"
    QUANTITATIVE_ENGINEER = "quantitative_engineer"
    TRADER = "trader"


class AgentStatus(Enum):
    """Agent状态枚举"""
    IDLE = "idle"
    BUSY = "busy"
    PROCESSING = "processing"
    ERROR = "error"
    OFFLINE = "offline"
    COLLABORATING = "collaborating"


class TaskPriority(Enum):
    """任务优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AgentTask:
    """Agent任务定义"""
    task_id: str
    task_type: str
    description: str
    assigned_agent: str
    priority: TaskPriority
    created_at: datetime
    deadline: Optional[datetime] = None
    status: str = "pending"
    progress: float = 0.0
    collaborators: List[str] = None
    dependencies: List[str] = None
    estimated_duration: int = 0  # 分钟
    actual_duration: int = 0
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


@dataclass
class AgentInfo:
    """Agent信息"""
    agent_id: str
    agent_type: AgentType
    name: str
    description: str
    status: AgentStatus
    current_task: Optional[str]
    specialization: List[str]
    capabilities: Dict[str, Any]
    performance_metrics: Dict[str, float]
    collaboration_history: List[Dict[str, Any]]
    last_heartbeat: datetime
    resource_usage: Dict[str, float]
    availability_schedule: Dict[str, Any]
    workload: float = 0.0


@dataclass
class CollaborationEvent:
    """协作事件"""
    event_id: str
    participants: List[str]
    event_type: str
    description: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "active"
    outcome: Optional[Dict[str, Any]] = None
    efficiency_score: float = 0.0


@dataclass
class WorkflowDefinition:
    """工作流定义"""
    workflow_id: str
    name: str
    description: str
    steps: List[Dict[str, Any]]
    required_agents: List[str]
    estimated_duration: int
    dependencies: Dict[str, List[str]]


class AgentCoordinationService:
    """Agent协作监控服务"""

    def __init__(self):
        self.logger = logging.getLogger("agent_coordination_service")
        self.router = APIRouter(prefix="/api/agents", tags=["agent_coordination"])

        # 数据存储
        self.agents: Dict[str, AgentInfo] = {}
        self.tasks: Dict[str, AgentTask] = {}
        self.collaboration_events: Dict[str, CollaborationEvent] = {}
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.active_collaborations: Dict[str, List[str]] = {}

        # WebSocket连接管理
        self.active_connections: List[WebSocket] = []

        # 监控任务
        self._monitoring_tasks: List[asyncio.Task] = []
        self._running = False

        self._initialize_agents()
        self._setup_routes()

    def _setup_routes(self):
        """设置API路由"""

        @self.router.get("/status")
        async def get_all_agents_status():
            """获取所有Agent状态"""
            return {
                "agents": [
                    {
                        "agent_id": agent_id,
                        "agent_type": agent.agent_type.value,
                        "name": agent.name,
                        "status": agent.status.value,
                        "current_task": agent.current_task,
                        "performance_metrics": agent.performance_metrics,
                        "last_heartbeat": agent.last_heartbeat.isoformat(),
                        "workload": agent.workload,
                        "resource_usage": agent.resource_usage
                    }
                    for agent_id, agent in self.agents.items()
                ],
                "summary": self._calculate_agents_summary()
            }

        @self.router.get("/status/{agent_id}")
        async def get_agent_status(agent_id: str):
            """获取特定Agent状态"""
            if agent_id not in self.agents:
                raise HTTPException(status_code=404, detail="Agent未找到")

            agent = self.agents[agent_id]
            return asdict(agent)

        @self.router.post("/tasks")
        async def create_task(task_config: Dict[str, Any]):
            """创建新任务"""
            try:
                task_id = self._generate_task_id()

                task = AgentTask(
                    task_id=task_id,
                    task_type=task_config["task_type"],
                    description=task_config["description"],
                    assigned_agent=task_config["assigned_agent"],
                    priority=TaskPriority(task_config.get("priority", "medium")),
                    created_at=datetime.now(),
                    deadline=datetime.fromisoformat(task_config["deadline"]) if task_config.get("deadline") else None,
                    collaborators=task_config.get("collaborators", []),
                    dependencies=task_config.get("dependencies", []),
                    estimated_duration=task_config.get("estimated_duration", 0)
                )

                self.tasks[task_id] = task

                # 分配任务给Agent
                await self._assign_task_to_agent(task)

                return {
                    "task_id": task_id,
                    "status": "created",
                    "assigned_agent": task.assigned_agent
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.router.get("/tasks")
        async def get_tasks(status: Optional[str] = None, agent_id: Optional[str] = None):
            """获取任务列表"""
            filtered_tasks = self.tasks.values()

            if status:
                filtered_tasks = [t for t in filtered_tasks if t.status == status]

            if agent_id:
                filtered_tasks = [t for t in filtered_tasks if t.assigned_agent == agent_id]

            return {
                "tasks": [asdict(task) for task in filtered_tasks],
                "total": len(filtered_tasks)
            }

        @self.router.get("/tasks/{task_id}")
        async def get_task_details(task_id: str):
            """获取任务详情"""
            if task_id not in self.tasks:
                raise HTTPException(status_code=404, detail="任务未找到")

            task = self.tasks[task_id]
            return asdict(task)

        @self.router.put("/tasks/{task_id}/status")
        async def update_task_status(task_id: str, status_update: Dict[str, Any]):
            """更新任务状态"""
            if task_id not in self.tasks:
                raise HTTPException(status_code=404, detail="任务未找到")

            task = self.tasks[task_id]
            old_status = task.status

            task.status = status_update.get("status", task.status)
            task.progress = status_update.get("progress", task.progress)
            task.result = status_update.get("result")
            task.error_message = status_update.get("error_message")

            if task.status == "completed":
                task.actual_duration = (datetime.now() - task.created_at).seconds // 60

            # 更新Agent状态
            await self._update_agent_task_status(task.assigned_agent, task_id, task.status)

            # 广播任务更新
            await self._broadcast_task_update(task)

            return {
                "task_id": task_id,
                "old_status": old_status,
                "new_status": task.status,
                "progress": task.progress
            }

        @self.router.post("/collaboration/start")
        async def start_collaboration(collaboration_config: Dict[str, Any]):
            """启动Agent协作"""
            try:
                event_id = self._generate_collaboration_id()

                event = CollaborationEvent(
                    event_id=event_id,
                    participants=collaboration_config["participants"],
                    event_type=collaboration_config["event_type"],
                    description=collaboration_config["description"],
                    start_time=datetime.now(),
                    efficiency_score=0.0
                )

                self.collaboration_events[event_id] = event
                self.active_collaborations[event_id] = collaboration_config["participants"]

                # 更新参与Agent的状态
                for agent_id in collaboration_config["participants"]:
                    if agent_id in self.agents:
                        self.agents[agent_id].status = AgentStatus.COLLABORATING

                # 启动协作监控
                asyncio.create_task(self._monitor_collaboration(event_id))

                return {
                    "collaboration_id": event_id,
                    "status": "started",
                    "participants": collaboration_config["participants"]
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.router.get("/collaboration/{collaboration_id}")
        async def get_collaboration_status(collaboration_id: str):
            """获取协作状态"""
            if collaboration_id not in self.collaboration_events:
                raise HTTPException(status_code=404, detail="协作事件未找到")

            event = self.collaboration_events[collaboration_id]
            return asdict(event)

        @self.router.get("/collaborations")
        async def get_active_collaborations():
            """获取活跃协作"""
            active_events = [
                event for event in self.collaboration_events.values()
                if event.status == "active"
            ]

            return {
                "active_collaborations": [asdict(event) for event in active_events],
                "total": len(active_events)
            }

        @self.router.get("/performance/summary")
        async def get_performance_summary():
            """获取性能摘要"""
            summary = await self._calculate_performance_summary()
            return summary

        @self.router.get("/performance/{agent_id}")
        async def get_agent_performance(agent_id: str, days: int = 30):
            """获取Agent性能数据"""
            if agent_id not in self.agents:
                raise HTTPException(status_code=404, detail="Agent未找到")

            agent = self.agents[agent_id]
            performance_data = await self._get_agent_performance_history(agent_id, days)

            return {
                "agent_id": agent_id,
                "current_metrics": agent.performance_metrics,
                "performance_history": performance_data,
                "trends": self._analyze_performance_trends(performance_data)
            }

        @self.router.get("/workflows")
        async def get_available_workflows():
            """获取可用工作流"""
            return {
                "workflows": [
                    {
                        "workflow_id": workflow_id,
                        "name": workflow.name,
                        "description": workflow.description,
                        "required_agents": workflow.required_agents,
                        "estimated_duration": workflow.estimated_duration
                    }
                    for workflow_id, workflow in self.workflows.items()
                ]
            }

        @self.router.post("/workflows/{workflow_id}/execute")
        async def execute_workflow(workflow_id: str, parameters: Dict[str, Any]):
            """执行工作流"""
            if workflow_id not in self.workflows:
                raise HTTPException(status_code=404, detail="工作流未找到")

            workflow = self.workflows[workflow_id]

            # 检查所需Agent是否可用
            available_agents = self._check_agent_availability(workflow.required_agents)
            if not available_agents:
                raise HTTPException(status_code=400, detail="所需Agent不可用")

            # 启动工作流执行
            execution_id = await self._execute_workflow(workflow, parameters)

            return {
                "execution_id": execution_id,
                "workflow_id": workflow_id,
                "status": "started"
            }

        @self.router.get("/collaboration/efficiency")
        async def get_collaboration_efficiency():
            """获取协作效率分析"""
            efficiency_analysis = await self._analyze_collaboration_efficiency()
            return efficiency_analysis

        @self.router.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket实时通信端点"""
            await websocket.accept()
            self.active_connections.append(websocket)

            try:
                while True:
                    data = await websocket.receive_text()
                    message = json.loads(data)

                    if message["type"] == "subscribe_agent":
                        agent_id = message["agent_id"]
                        if agent_id in self.agents:
                            await websocket.send_json({
                                "type": "agent_update",
                                "agent": asdict(self.agents[agent_id])
                            })

                    elif message["type"] == "subscribe_tasks":
                        agent_id = message.get("agent_id")
                        tasks = self._get_agent_tasks(agent_id)
                        await websocket.send_json({
                            "type": "tasks_update",
                            "tasks": [asdict(task) for task in tasks]
                        })

            except WebSocketDisconnect:
                self.active_connections.remove(websocket)

    async def start(self):
        """启动Agent协作监控服务"""
        self.logger.info("启动Agent协作监控服务...")
        self._running = True

        # 启动监控任务
        self._monitoring_tasks = [
            asyncio.create_task(self._agent_heartbeat_monitor()),
            asyncio.create_task(self._performance_monitor()),
            asyncio.create_task(self._collaboration_efficiency_monitor()),
            asyncio.create_task(self._resource_usage_monitor())
        ]

        self.logger.info("Agent协作监控服务启动成功")

    async def stop(self):
        """停止Agent协作监控服务"""
        self.logger.info("停止Agent协作监控服务...")
        self._running = False

        # 取消所有监控任务
        for task in self._monitoring_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self.logger.info("Agent协作监控服务已停止")

    def _initialize_agents(self):
        """初始化Agent"""
        agent_configs = [
            {
                "agent_id": "data_scientist_001",
                "agent_type": AgentType.DATA_SCIENTIST,
                "name": "数据科学家",
                "description": "负责数据分析、模型训练和特征工程",
                "specialization": ["数据分析", "机器学习", "统计分析", "特征工程"],
                "capabilities": {
                    "data_processing": 95,
                    "model_training": 90,
                    "statistical_analysis": 88,
                    "feature_engineering": 92,
                    "data_visualization": 85
                }
            },
            {
                "agent_id": "portfolio_manager_001",
                "agent_type": AgentType.PORTFOLIO_MANAGER,
                "name": "投资组合经理",
                "description": "负责投资组合构建、资产配置和风险预算",
                "specialization": ["投资组合管理", "资产配置", "风险预算", "绩效分析"],
                "capabilities": {
                    "portfolio_optimization": 92,
                    "asset_allocation": 90,
                    "risk_budgeting": 88,
                    "performance_analysis": 85,
                    "rebalancing": 87
                }
            },
            {
                "agent_id": "risk_analyst_001",
                "agent_type": AgentType.RISK_ANALYST,
                "name": "风险分析师",
                "description": "负责风险识别、评估和管理",
                "specialization": ["风险管理", "VaR计算", "压力测试", "合规检查"],
                "capabilities": {
                    "risk_assessment": 93,
                    "var_calculation": 90,
                    "stress_testing": 88,
                    "compliance_check": 85,
                    "risk_monitoring": 91
                }
            },
            {
                "agent_id": "quantitative_analyst_001",
                "agent_type": AgentType.QUANTITATIVE_ANALYST,
                "name": "量化分析师",
                "description": "负责量化策略研究、模型开发和回测",
                "specialization": ["量化策略", "数学建模", "回测分析", "策略优化"],
                "capabilities": {
                    "strategy_development": 94,
                    "mathematical_modeling": 89,
                    "backtesting": 92,
                    "strategy_optimization": 88,
                    "algorithm_design": 90
                }
            },
            {
                "agent_id": "research_analyst_001",
                "agent_type": AgentType.RESEARCH_ANALYST,
                "name": "研究分析师",
                "description": "负责市场研究、行业分析和投资机会识别",
                "specialization": ["市场研究", "行业分析", "基本面分析", "投资机会"],
                "capabilities": {
                    "market_research": 91,
                    "industry_analysis": 89,
                    "fundamental_analysis": 87,
                    "opportunity_identification": 85,
                    "report_generation": 88
                }
            },
            {
                "agent_id": "quantitative_engineer_001",
                "agent_type": AgentType.QUANTITATIVE_ENGINEER,
                "name": "量化工程师",
                "description": "负责系统架构、性能优化和技术实现",
                "specialization": ["系统架构", "性能优化", "技术实现", "系统集成"],
                "capabilities": {
                    "system_architecture": 92,
                    "performance_optimization": 90,
                    "technical_implementation": 91,
                    "system_integration": 88,
                    "code_development": 94
                }
            },
            {
                "agent_id": "trader_001",
                "agent_type": AgentType.TRADER,
                "name": "交易员",
                "description": "负责交易执行、订单管理和市场监控",
                "specialization": ["交易执行", "订单管理", "市场监控", "执行优化"],
                "capabilities": {
                    "trade_execution": 93,
                    "order_management": 90,
                    "market_monitoring": 89,
                    "execution_optimization": 87,
                    "slippage_control": 91
                }
            }
        ]

        for config in agent_configs:
            agent = AgentInfo(
                agent_id=config["agent_id"],
                agent_type=config["agent_type"],
                name=config["name"],
                description=config["description"],
                status=AgentStatus.IDLE,
                current_task=None,
                specialization=config["specialization"],
                capabilities=config["capabilities"],
                performance_metrics={
                    "efficiency": 85.0,
                    "accuracy": 90.0,
                    "task_completion_rate": 88.0,
                    "collaboration_score": 87.0,
                    "innovation_index": 82.0
                },
                collaboration_history=[],
                last_heartbeat=datetime.now(),
                resource_usage={
                    "cpu": 0.0,
                    "memory": 0.0,
                    "network": 0.0
                },
                availability_schedule={
                    "working_hours": "09:00-18:00",
                    "timezone": "UTC+8",
                    "max_concurrent_tasks": 3,
                    "preferred_collaborators": []
                }
            )

            self.agents[config["agent_id"]] = agent

        # 初始化工作流定义
        self._initialize_workflows()

    def _initialize_workflows(self):
        """初始化工作流定义"""
        workflows = [
            WorkflowDefinition(
                workflow_id="strategy_development_workflow",
                name="策略开发工作流",
                description="从市场研究到策略部署的完整流程",
                steps=[
                    {"step": 1, "agent": "research_analyst_001", "action": "市场研究", "duration": 60},
                    {"step": 2, "agent": "data_scientist_001", "action": "数据分析", "duration": 45},
                    {"step": 3, "agent": "quantitative_analyst_001", "action": "策略开发", "duration": 90},
                    {"step": 4, "agent": "risk_analyst_001", "action": "风险评估", "duration": 30},
                    {"step": 5, "agent": "portfolio_manager_001", "action": "组合优化", "duration": 45}
                ],
                required_agents=["research_analyst_001", "data_scientist_001", "quantitative_analyst_001", "risk_analyst_001", "portfolio_manager_001"],
                estimated_duration=270,
                dependencies={
                    "2": ["1"],
                    "3": ["2"],
                    "4": ["3"],
                    "5": ["4"]
                }
            ),
            WorkflowDefinition(
                workflow_id="risk_assessment_workflow",
                name="风险评估工作流",
                description="全面的投资组合风险评估流程",
                steps=[
                    {"step": 1, "agent": "risk_analyst_001", "action": "风险识别", "duration": 30},
                    {"step": 2, "agent": "data_scientist_001", "action": "数据分析", "duration": 45},
                    {"step": 3, "agent": "quantitative_engineer_001", "action": "模型验证", "duration": 60},
                    {"step": 4, "agent": "portfolio_manager_001", "action": "风险报告", "duration": 30}
                ],
                required_agents=["risk_analyst_001", "data_scientist_001", "quantitative_engineer_001", "portfolio_manager_001"],
                estimated_duration=165,
                dependencies={
                    "2": ["1"],
                    "3": ["2"],
                    "4": ["3"]
                }
            )
        ]

        for workflow in workflows:
            self.workflows[workflow.workflow_id] = workflow

    async def _agent_heartbeat_monitor(self):
        """Agent心跳监控"""
        while self._running:
            try:
                current_time = datetime.now()
                offline_agents = []

                for agent_id, agent in self.agents.items():
                    # 检查心跳超时
                    heartbeat_age = (current_time - agent.last_heartbeat).total_seconds()
                    if heartbeat_age > 60:  # 60秒超时
                        agent.status = AgentStatus.OFFLINE
                        offline_agents.append(agent_id)
                    elif agent.status == AgentStatus.OFFLINE and heartbeat_age < 30:
                        # 恢复在线状态
                        agent.status = AgentStatus.IDLE

                # 模拟心跳更新
                if np.random.random() < 0.1:  # 10%概率更新心跳
                    agent_id = np.random.choice(list(self.agents.keys()))
                    self.agents[agent_id].last_heartbeat = current_time
                    if self.agents[agent_id].status == AgentStatus.OFFLINE:
                        self.agents[agent_id].status = AgentStatus.IDLE

                await asyncio.sleep(10)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Agent心跳监控异常: {e}")
                await asyncio.sleep(10)

    async def _performance_monitor(self):
        """性能监控"""
        while self._running:
            try:
                # 更新Agent性能指标
                for agent_id, agent in self.agents.items():
                    # 模拟性能指标变化
                    for metric in agent.performance_metrics:
                        # 小幅随机波动
                        change = np.random.normal(0, 1)
                        current_value = agent.performance_metrics[metric]
                        new_value = max(0, min(100, current_value + change))
                        agent.performance_metrics[metric] = round(new_value, 2)

                    # 更新工作负载
                    agent.workload = self._calculate_agent_workload(agent_id)

                # 广播性能更新
                await self._broadcast_performance_update()

                await asyncio.sleep(30)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"性能监控异常: {e}")
                await asyncio.sleep(30)

    async def _collaboration_efficiency_monitor(self):
        """协作效率监控"""
        while self._running:
            try:
                # 分析活跃协作的效率
                for event_id, participants in list(self.active_collaborations.items()):
                    if event_id in self.collaboration_events:
                        event = self.collaboration_events[event_id]
                        efficiency = await self._calculate_collaboration_efficiency_score(event)
                        event.efficiency_score = efficiency

                await asyncio.sleep(60)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"协作效率监控异常: {e}")
                await asyncio.sleep(60)

    async def _resource_usage_monitor(self):
        """资源使用监控"""
        while self._running:
            try:
                # 获取系统资源使用情况
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_percent = psutil.virtual_memory().percent

                # 更新Agent资源使用情况
                for agent_id, agent in self.agents.items():
                    if agent.status in [AgentStatus.BUSY, AgentStatus.PROCESSING, AgentStatus.COLLABORATING]:
                        # 活跃Agent占用更多资源
                        agent.resource_usage["cpu"] = cpu_percent * np.random.uniform(0.8, 1.2)
                        agent.resource_usage["memory"] = memory_percent * np.random.uniform(0.7, 1.1)
                        agent.resource_usage["network"] = np.random.uniform(0, 20)
                    else:
                        # 空闲Agent占用较少资源
                        agent.resource_usage["cpu"] = cpu_percent * np.random.uniform(0.1, 0.3)
                        agent.resource_usage["memory"] = memory_percent * np.random.uniform(0.2, 0.4)
                        agent.resource_usage["network"] = np.random.uniform(0, 5)

                await asyncio.sleep(15)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"资源使用监控异常: {e}")
                await asyncio.sleep(15)

    def _calculate_agent_workload(self, agent_id: str) -> float:
        """计算Agent工作负载"""
        try:
            # 基于任务数量和状态计算工作负载
            agent_tasks = [task for task in self.tasks.values() if task.assigned_agent == agent_id]

            active_tasks = len([t for t in agent_tasks if t.status in ["pending", "processing"]])
            total_tasks = len(agent_tasks)

            # 基础负载
            base_load = (active_tasks * 30) + (total_tasks * 10)

            # 协作负载
            collaboration_load = 0
            for event_id, participants in self.active_collaborations.items():
                if agent_id in participants:
                    collaboration_load += 20

            total_load = base_load + collaboration_load

            # 归一化到0-100
            workload = min(100, total_load)

            return round(workload, 2)

        except Exception as e:
            self.logger.error(f"计算Agent工作负载失败: {e}")
            return 0.0

    async def _assign_task_to_agent(self, task: AgentTask):
        """分配任务给Agent"""
        try:
            if task.assigned_agent in self.agents:
                agent = self.agents[task.assigned_agent]

                # 更新Agent状态
                agent.current_task = task.task_id
                agent.status = AgentStatus.BUSY

                # 记录分配事件
                await self._broadcast_agent_update(agent)

        except Exception as e:
            self.logger.error(f"分配任务失败: {e}")

    async def _update_agent_task_status(self, agent_id: str, task_id: str, status: str):
        """更新Agent任务状态"""
        try:
            if agent_id in self.agents:
                agent = self.agents[agent_id]

                if status in ["completed", "failed", "cancelled"]:
                    # 任务完成，更新Agent状态
                    agent.current_task = None

                    # 检查是否还有其他任务
                    other_tasks = [t for t in self.tasks.values() if t.assigned_agent == agent_id and t.status == "pending"]
                    if not other_tasks:
                        agent.status = AgentStatus.IDLE
                    else:
                        # 分配下一个任务
                        next_task = other_tasks[0]
                        agent.current_task = next_task.task_id
                        agent.status = AgentStatus.BUSY

                await self._broadcast_agent_update(agent)

        except Exception as e:
            self.logger.error(f"更新Agent任务状态失败: {e}")

    async def _monitor_collaboration(self, collaboration_id: str):
        """监控协作进程"""
        try:
            event = self.collaboration_events[collaboration_id]

            # 模拟协作进程
            collaboration_duration = np.random.randint(30, 180)  # 30-180分钟
            await asyncio.sleep(collaboration_duration)

            # 完成协作
            event.end_time = datetime.now()
            event.status = "completed"
            event.outcome = {
                "success": np.random.random() > 0.2,
                "efficiency_score": event.efficiency_score,
                "participants_satisfaction": np.random.uniform(70, 95),
                "deliverables_quality": np.random.uniform(80, 98)
            }

            # 更新参与Agent状态
            for agent_id in self.active_collaborations[collaboration_id]:
                if agent_id in self.agents:
                    self.agents[agent_id].status = AgentStatus.IDLE
                    # 记录协作历史
                    self.agents[agent_id].collaboration_history.append({
                        "collaboration_id": collaboration_id,
                        "role": "participant",
                        "start_time": event.start_time.isoformat(),
                        "end_time": event.end_time.isoformat(),
                        "outcome": event.outcome
                    })

            # 清理活跃协作
            del self.active_collaborations[collaboration_id]

            # 广播协作完成
            await self._broadcast_collaboration_update(event)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"监控协作失败: {e}")

    async def _calculate_collaboration_efficiency_score(self, event: CollaborationEvent) -> float:
        """计算协作效率得分"""
        try:
            # 基于多个因素计算效率得分
            factors = []

            # 协作时长 (理想时长60-120分钟)
            if event.end_time:
                duration = (event.end_time - event.start_time).total_seconds() / 60
                if 60 <= duration <= 120:
                    factors.append(90)
                elif duration < 60:
                    factors.append(75)  # 可能过于仓促
                else:
                    factors.append(60)  # 可能效率不高
            else:
                factors.append(80)  # 进行中，暂定分数

            # 参与者数量 (理想3-5人)
            participant_count = len(event.participants)
            if 3 <= participant_count <= 5:
                factors.append(90)
            elif participant_count < 3:
                factors.append(70)  # 参与者不足
            else:
                factors.append(75)  # 可能过于拥挤

            # Agent性能水平
            avg_performance = 0
            for agent_id in event.participants:
                if agent_id in self.agents:
                    performance = np.mean(list(self.agents[agent_id].performance_metrics.values()))
                    avg_performance += performance

            if event.participants:
                avg_performance /= len(event.participants)
                factors.append(avg_performance)

            # 协作历史
            collaboration_history_score = 85  # 默认分数
            factors.append(collaboration_history_score)

            # 计算加权平均
            if factors:
                efficiency = np.mean(factors)
            else:
                efficiency = 75.0

            return round(efficiency, 2)

        except Exception as e:
            self.logger.error(f"计算协作效率得分失败: {e}")
            return 75.0

    def _calculate_agents_summary(self) -> Dict[str, Any]:
        """计算Agent摘要"""
        try:
            total_agents = len(self.agents)
            active_agents = len([a for a in self.agents.values() if a.status != AgentStatus.OFFLINE])
            busy_agents = len([a for a in self.agents.values() if a.status in [AgentStatus.BUSY, AgentStatus.PROCESSING]])
            collaborating_agents = len([a for a in self.agents.values() if a.status == AgentStatus.COLLABORATING])

            # 平均性能指标
            all_metrics = []
            for agent in self.agents.values():
                all_metrics.extend(list(agent.performance_metrics.values()))

            avg_performance = np.mean(all_metrics) if all_metrics else 0

            summary = {
                "total_agents": total_agents,
                "active_agents": active_agents,
                "busy_agents": busy_agents,
                "collaborating_agents": collaborating_agents,
                "offline_agents": total_agents - active_agents,
                "overall_efficiency": round(avg_performance, 2),
                "total_active_tasks": len([t for t in self.tasks.values() if t.status in ["pending", "processing"]]),
                "active_collaborations": len(self.active_collaborations),
                "system_health": self._calculate_system_health()
            }

            return summary

        except Exception as e:
            self.logger.error(f"计算Agent摘要失败: {e}")
            return {}

    def _calculate_system_health(self) -> str:
        """计算系统健康状态"""
        try:
            total_agents = len(self.agents)
            if total_agents == 0:
                return "unknown"

            # 健康评分因素
            health_factors = []

            # Agent在线率
            online_rate = len([a for a in self.agents.values() if a.status != AgentStatus.OFFLINE]) / total_agents
            health_factors.append(online_rate)

            # 平均性能
            avg_performance = np.mean([
                np.mean(list(agent.performance_metrics.values()))
                for agent in self.agents.values()
            ])
            health_factors.append(avg_performance / 100)

            # 工作负载均衡
            workloads = [agent.workload for agent in self.agents.values()]
            workload_std = np.std(workloads) if workloads else 0
            workload_balance = 1 - min(1, workload_std / 50)
            health_factors.append(workload_balance)

            # 综合健康评分
            health_score = np.mean(health_factors)

            if health_score >= 0.9:
                return "excellent"
            elif health_score >= 0.8:
                return "good"
            elif health_score >= 0.7:
                return "fair"
            elif health_score >= 0.6:
                return "poor"
            else:
                return "critical"

        except Exception as e:
            self.logger.error(f"计算系统健康状态失败: {e}")
            return "unknown"

    def _get_agent_tasks(self, agent_id: Optional[str] = None) -> List[AgentTask]:
        """获取Agent任务"""
        if agent_id:
            return [task for task in self.tasks.values() if task.assigned_agent == agent_id]
        else:
            return list(self.tasks.values())

    async def _get_agent_performance_history(self, agent_id: str, days: int) -> List[Dict[str, Any]]:
        """获取Agent性能历史"""
        try:
            # 生成模拟历史数据
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            history = []
            current_date = start_date

            agent = self.agents[agent_id]
            base_metrics = agent.performance_metrics.copy()

            while current_date <= end_date:
                # 模拟性能波动
                daily_metrics = {}
                for metric, base_value in base_metrics.items():
                    change = np.random.normal(0, 2)
                    daily_value = max(0, min(100, base_value + change))
                    daily_metrics[metric] = round(daily_value, 2)

                history.append({
                    "date": current_date.isoformat(),
                    "metrics": daily_metrics,
                    "tasks_completed": np.random.randint(0, 10),
                    "collaborations": np.random.randint(0, 3)
                })

                current_date += timedelta(days=1)

            return history

        except Exception as e:
            self.logger.error(f"获取Agent性能历史失败: {e}")
            return []

    def _analyze_performance_trends(self, performance_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析性能趋势"""
        try:
            if len(performance_data) < 7:
                return {"trend": "insufficient_data"}

            # 分析最近7天的趋势
            recent_data = performance_data[-7:]
            metrics = list(recent_data[0]["metrics"].keys())

            trends = {}
            for metric in metrics:
                values = [day["metrics"][metric] for day in recent_data]

                # 计算趋势
                if len(values) >= 2:
                    slope = (values[-1] - values[0]) / len(values)
                    if slope > 0.5:
                        trends[metric] = "improving"
                    elif slope < -0.5:
                        trends[metric] = "declining"
                    else:
                        trends[metric] = "stable"
                else:
                    trends[metric] = "stable"

            # 总体趋势
            trend_counts = list(trends.values())
            improving_count = trend_counts.count("improving")
            declining_count = trend_counts.count("declining")

            if improving_count > declining_count:
                overall_trend = "improving"
            elif declining_count > improving_count:
                overall_trend = "declining"
            else:
                overall_trend = "stable"

            return {
                "overall_trend": overall_trend,
                "metric_trends": trends,
                "data_points": len(performance_data)
            }

        except Exception as e:
            self.logger.error(f"分析性能趋势失败: {e}")
            return {"trend": "error"}

    async def _calculate_performance_summary(self) -> Dict[str, Any]:
        """计算性能摘要"""
        try:
            summary = {
                "agent_performance": {},
                "system_metrics": {},
                "collaboration_stats": {},
                "efficiency_analysis": {}
            }

            # Agent性能统计
            for agent_id, agent in self.agents.items():
                summary["agent_performance"][agent_id] = {
                    "name": agent.name,
                    "efficiency": agent.performance_metrics["efficiency"],
                    "accuracy": agent.performance_metrics["accuracy"],
                    "task_completion_rate": agent.performance_metrics["task_completion_rate"],
                    "collaboration_score": agent.performance_metrics["collaboration_score"],
                    "workload": agent.workload,
                    "status": agent.status.value
                }

            # 系统指标
            all_efficiency = [agent.performance_metrics["efficiency"] for agent in self.agents.values()]
            all_accuracy = [agent.performance_metrics["accuracy"] for agent in self.agents.values()]

            summary["system_metrics"] = {
                "avg_efficiency": round(np.mean(all_efficiency), 2),
                "avg_accuracy": round(np.mean(all_accuracy), 2),
                "total_agents": len(self.agents),
                "active_agents": len([a for a in self.agents.values() if a.status != AgentStatus.OFFLINE])
            }

            # 协作统计
            if self.collaboration_events:
                completed_collaborations = [e for e in self.collaboration_events.values() if e.status == "completed"]
                avg_efficiency = np.mean([e.efficiency_score for e in completed_collaborations]) if completed_collaborations else 0

                summary["collaboration_stats"] = {
                    "total_collaborations": len(self.collaboration_events),
                    "completed_collaborations": len(completed_collaborations),
                    "active_collaborations": len(self.active_collaborations),
                    "avg_efficiency_score": round(avg_efficiency, 2)
                }

            # 效率分析
            summary["efficiency_analysis"] = {
                "peak_performance_hours": "09:00-12:00",
                "optimal_team_size": "3-5 agents",
                "collaboration_frequency": "2-3 times per week",
                "recommended_workload_balance": "70-80%"
            }

            return summary

        except Exception as e:
            self.logger.error(f"计算性能摘要失败: {e}")
            return {}

    def _check_agent_availability(self, required_agents: List[str]) -> bool:
        """检查Agent可用性"""
        try:
            for agent_id in required_agents:
                if agent_id not in self.agents:
                    return False

                agent = self.agents[agent_id]
                if agent.status == AgentStatus.OFFLINE:
                    return False

                if agent.workload > 80:
                    return False

            return True

        except Exception:
            return False

    async def _execute_workflow(self, workflow: WorkflowDefinition, parameters: Dict[str, Any]) -> str:
        """执行工作流"""
        try:
            execution_id = f"exec_{workflow.workflow_id}_{int(datetime.now().timestamp())}"

            # 创建工作流任务
            for step in workflow.steps:
                task_config = {
                    "task_type": f"workflow_step_{step['step']}",
                    "description": f"执行工作流步骤: {step['action']}",
                    "assigned_agent": step["agent"],
                    "priority": "medium",
                    "estimated_duration": step["duration"]
                }

                await self.create_task(task_config)

            return execution_id

        except Exception as e:
            self.logger.error(f"执行工作流失败: {e}")
            raise

    async def _analyze_collaboration_efficiency(self) -> Dict[str, Any]:
        """分析协作效率"""
        try:
            analysis = {
                "efficiency_trends": {},
                "optimal_teams": {},
                "bottlenecks": [],
                "recommendations": []
            }

            if not self.collaboration_events:
                return analysis

            # 效率趋势分析
            completed_events = [e for e in self.collaboration_events.values() if e.status == "completed"]

            if completed_events:
                efficiency_scores = [e.efficiency_score for e in completed_events]
                analysis["efficiency_trends"] = {
                    "average_efficiency": round(np.mean(efficiency_scores), 2),
                    "efficiency_trend": "stable",  # 可以进一步分析
                    "best_efficiency": round(max(efficiency_scores), 2),
                    "worst_efficiency": round(min(efficiency_scores), 2)
                }

            # 最优团队组合分析
            team_performance = {}
            for event in completed_events:
                team_key = tuple(sorted(event.participants))
                if team_key not in team_performance:
                    team_performance[team_key] = []
                team_performance[team_key].append(event.efficiency_score)

            for team, scores in team_performance.items():
                if len(scores) >= 2:
                    avg_score = np.mean(scores)
                    analysis["optimal_teams"][",".join(team)] = round(avg_score, 2)

            # 瓶颈分析
            agent_workloads = {agent_id: agent.workload for agent_id, agent in self.agents.items()}
            overloaded_agents = [agent_id for agent_id, workload in agent_workloads.items() if workload > 85]
            analysis["bottlenecks"] = overloaded_agents

            # 改进建议
            if overloaded_agents:
                analysis["recommendations"].append("考虑重新分配高负载Agent的任务")

            if analysis.get("efficiency_trends", {}).get("average_efficiency", 0) < 80:
                analysis["recommendations"].append("建议优化协作流程以提高效率")

            return analysis

        except Exception as e:
            self.logger.error(f"分析协作效率失败: {e}")
            return {}

    def _generate_task_id(self) -> str:
        """生成任务ID"""
        import uuid
        return f"task_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}"

    def _generate_collaboration_id(self) -> str:
        """生成协作ID"""
        import uuid
        return f"collab_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}"

    async def _broadcast_agent_update(self, agent: AgentInfo):
        """广播Agent更新"""
        message = {
            "type": "agent_update",
            "agent": asdict(agent),
            "timestamp": datetime.now().isoformat()
        }

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

    async def _broadcast_task_update(self, task: AgentTask):
        """广播任务更新"""
        message = {
            "type": "task_update",
            "task": asdict(task),
            "timestamp": datetime.now().isoformat()
        }

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

    async def _broadcast_collaboration_update(self, event: CollaborationEvent):
        """广播协作更新"""
        message = {
            "type": "collaboration_update",
            "collaboration": asdict(event),
            "timestamp": datetime.now().isoformat()
        }

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

    async def _broadcast_performance_update(self):
        """广播性能更新"""
        performance_data = {
            "type": "performance_update",
            "agents_performance": {
                agent_id: agent.performance_metrics
                for agent_id, agent in self.agents.items()
            },
            "timestamp": datetime.now().isoformat()
        }

        for connection in self.active_connections:
            try:
                await connection.send_json(performance_data)
            except Exception:
                pass


# 创建全局实例
_agent_coordination_service: Optional[AgentCoordinationService] = None


def get_agent_coordination_service() -> AgentCoordinationService:
    """获取Agent协作监控服务实例"""
    global _agent_coordination_service
    if _agent_coordination_service is None:
        _agent_coordination_service = AgentCoordinationService()
    return _agent_coordination_service
"""
策略管理Dashboard主服务

专业级CBSC策略管理平台，提供实时监控、参数优化、回测分析和Agent协作功能
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from .dashboard_ui import DashboardUI
from .websocket_manager import WebSocketManager
from ..dashboard.agent_data_service import StrategyDataService
from .fixed_performance_service import FixedPerformanceService


class StrategyType(Enum):
    """策略类型枚举"""
    DIRECT_RSI = "direct_rsi"
    SENTIMENT_MOMENTUM = "sentiment_momentum"
    COMPOSITE_INDEX = "composite_index"
    VOLATILITY_ADJUSTED = "volatility_adjusted"


class SignalType(Enum):
    """信号类型枚举"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    EXTREME_BULLISH = "extreme_bullish"
    EXTREME_BEARISH = "extreme_bearish"
    GOLDEN_CROSS = "golden_cross"
    DEATH_CROSS = "death_cross"


@dataclass
class StrategySignal:
    """策略信号数据结构"""
    strategy_type: StrategyType
    signal_type: SignalType
    strength: float  # 信号强度 0-100
    confidence: float  # 信号置信度 0-100
    timestamp: datetime
    parameters: Dict[str, Any]
    market_data: Dict[str, float]
    metadata: Dict[str, Any]


@dataclass
class StrategyPerformance:
    """策略性能数据结构"""
    strategy_type: StrategyType
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    calmar_ratio: float
    last_updated: datetime


@dataclass
class AgentStatus:
    """Agent状态数据结构"""
    agent_id: str
    agent_type: str
    status: str  # active, idle, error, processing
    current_task: Optional[str]
    performance_metrics: Dict[str, float]
    last_heartbeat: datetime
    resource_usage: Dict[str, float]


class StrategyManagementDashboard:
    """策略管理Dashboard主服务类"""

    def __init__(self, port: int = 3003):
        self.port = port
        self.logger = logging.getLogger("strategy_management_dashboard")

        # 初始化核心组件
        self.app = FastAPI(
            title="策略管理Dashboard",
            description="专业级CBSC策略管理平台",
            version="1.0.0"
        )

        # 服务组件
        self.websocket_manager = WebSocketManager()
        self.strategy_service = StrategyDataService()
        self.performance_service = FixedPerformanceService()

        # 数据存储
        self.active_strategies: Dict[StrategyType, Dict] = {}
        self.strategy_signals: List[StrategySignal] = []
        self.strategy_performance: Dict[StrategyType, StrategyPerformance] = {}
        self.agent_status: Dict[str, AgentStatus] = {}

        # 实时更新任务
        self._update_tasks: List[asyncio.Task] = []
        self._running = False

        self._setup_routes()
        self._initialize_strategies()

    def _setup_routes(self):
        """设置路由"""

        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home():
            """Dashboard主页"""
            return await self._get_dashboard_html()

        @self.app.get("/api/strategies")
        async def get_strategies():
            """获取所有活跃策略"""
            return {
                "strategies": [
                    {
                        "type": strategy_type.value,
                        "name": self._get_strategy_name(strategy_type),
                        "active": strategy_type in self.active_strategies,
                        "parameters": self.active_strategies.get(strategy_type, {}),
                        "performance": asdict(self.strategy_performance.get(strategy_type)) if strategy_type in self.strategy_performance else None
                    }
                    for strategy_type in StrategyType
                ]
            }

        @self.app.get("/api/strategies/{strategy_type}/signals")
        async def get_strategy_signals(strategy_type: str):
            """获取策略信号"""
            try:
                strategy_enum = StrategyType(strategy_type)
                signals = [
                    asdict(signal) for signal in self.strategy_signals
                    if signal.strategy_type == strategy_enum
                ]
                return {"signals": signals[-50:]}  # 返回最近50个信号
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid strategy type")

        @self.app.post("/api/strategies/{strategy_type}/parameters")
        async def update_strategy_parameters(strategy_type: str, parameters: Dict[str, Any]):
            """更新策略参数"""
            try:
                strategy_enum = StrategyType(strategy_type)
                self.active_strategies[strategy_enum] = parameters

                # 广播参数更新
                await self.websocket_manager.broadcast({
                    "type": "parameters_updated",
                    "strategy_type": strategy_type,
                    "parameters": parameters
                })

                return {"success": True, "message": "Parameters updated successfully"}
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid strategy type")

        @self.app.get("/api/performance/summary")
        async def get_performance_summary():
            """获取性能摘要"""
            return {
                "timestamp": datetime.now().isoformat(),
                "strategies": {
                    strategy_type.value: asdict(performance)
                    for strategy_type, performance in self.strategy_performance.items()
                },
                "overall_metrics": self._calculate_overall_metrics()
            }

        @self.app.get("/api/agents/status")
        async def get_agents_status():
            """获取Agent状态"""
            return {
                "agents": [
                    {
                        "agent_id": agent_id,
                        "agent_type": status.agent_type,
                        "status": status.status,
                        "current_task": status.current_task,
                        "performance_metrics": status.performance_metrics,
                        "last_heartbeat": status.last_heartbeat.isoformat(),
                        "resource_usage": status.resource_usage
                    }
                    for agent_id, status in self.agent_status.items()
                ]
            }

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket实时数据端点"""
            await self.websocket_manager.connect(websocket)
            try:
                while True:
                    data = await websocket.receive_text()
                    # 处理客户端消息
                    await self._handle_websocket_message(websocket, data)
            except WebSocketDisconnect:
                self.websocket_manager.disconnect(websocket)

    async def _get_dashboard_html(self) -> str:
        """获取Dashboard HTML内容"""
        html_path = Path(__file__).parent / "strategy_management_dashboard.html"
        if html_path.exists():
            with open(html_path, 'r', encoding='utf-8') as f:
                return f.read()

        # 如果HTML文件不存在，返回基本的HTML结构
        return await self._generate_basic_dashboard_html()

    async def _generate_basic_dashboard_html(self) -> str:
        """生成基本的Dashboard HTML"""
        return """
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>策略管理Dashboard</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { font-family: 'Microsoft YaHei', sans-serif; background: #f5f5f5; }
                .header { background: linear-gradient(45deg, #667eea, #764ba2); color: white; padding: 20px; text-align: center; }
                .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
                .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
                .card { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .status { padding: 10px; border-radius: 5px; text-align: center; font-weight: bold; }
                .status.active { background: #d4edda; color: #155724; }
                .status.inactive { background: #f8d7da; color: #721c24; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>策略管理Dashboard</h1>
                <p>专业级CBSC策略管理平台</p>
            </div>
            <div class="container">
                <div class="grid">
                    <div class="card">
                        <h3>策略状态</h3>
                        <div id="strategy-status"></div>
                    </div>
                    <div class="card">
                        <h3>实时信号</h3>
                        <div id="live-signals"></div>
                    </div>
                    <div class="card">
                        <h3>性能指标</h3>
                        <div id="performance-metrics"></div>
                    </div>
                    <div class="card">
                        <h3>Agent状态</h3>
                        <div id="agent-status"></div>
                    </div>
                </div>
            </div>
            <script>
                // 基本的JavaScript交互逻辑将在这里实现
                console.log('策略管理Dashboard已加载');
            </script>
        </body>
        </html>
        """

    def _initialize_strategies(self):
        """初始化策略"""
        default_parameters = {
            StrategyType.DIRECT_RSI: {
                "rsi_period": 14,
                "oversold_threshold": 30,
                "overbought_threshold": 70
            },
            StrategyType.SENTIMENT_MOMENTUM: {
                "fast_period": 12,
                "slow_period": 26,
                "signal_period": 9
            },
            StrategyType.COMPOSITE_INDEX: {
                "bb_period": 20,
                "bb_std": 2,
                "weight_sentiment": 0.6
            },
            StrategyType.VOLATILITY_ADJUSTED: {
                "volatility_window": 20,
                "volume_weight": 0.3
            }
        }

        for strategy_type, parameters in default_parameters.items():
            self.active_strategies[strategy_type] = parameters

    async def start(self):
        """启动Dashboard服务"""
        self.logger.info(f"启动策略管理Dashboard，端口: {self.port}")
        self._running = True

        # 启动实时更新任务
        self._update_tasks = [
            asyncio.create_task(self._strategy_monitoring_loop()),
            asyncio.create_task(self._performance_tracking_loop()),
            asyncio.create_task(self._agent_status_loop()),
            asyncio.create_task(self._signal_generation_loop())
        ]

        # 启动WebSocket心跳
        await self.websocket_manager.start_heartbeat_task()

        self.logger.info("策略管理Dashboard启动成功")

    async def stop(self):
        """停止Dashboard服务"""
        self.logger.info("停止策略管理Dashboard...")
        self._running = False

        # 取消所有任务
        for task in self._update_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self.logger.info("策略管理Dashboard已停止")

    async def _strategy_monitoring_loop(self):
        """策略监控循环"""
        while self._running:
            try:
                # 更新策略状态
                await self._update_strategy_status()
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"策略监控循环异常: {e}")
                await asyncio.sleep(5)

    async def _performance_tracking_loop(self):
        """性能跟踪循环"""
        while self._running:
            try:
                # 更新性能数据
                await self._update_performance_metrics()
                await asyncio.sleep(30)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"性能跟踪循环异常: {e}")
                await asyncio.sleep(30)

    async def _agent_status_loop(self):
        """Agent状态循环"""
        while self._running:
            try:
                # 更新Agent状态
                await self._update_agent_status()
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Agent状态循环异常: {e}")
                await asyncio.sleep(10)

    async def _signal_generation_loop(self):
        """信号生成循环"""
        while self._running:
            try:
                # 生成新信号
                await self._generate_strategy_signals()
                await asyncio.sleep(15)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"信号生成循环异常: {e}")
                await asyncio.sleep(15)

    async def _update_strategy_status(self):
        """更新策略状态"""
        # 模拟策略状态更新
        for strategy_type in self.active_strategies.keys():
            # 这里应该调用实际的策略服务
            pass

    async def _update_performance_metrics(self):
        """更新性能指标"""
        # 模拟性能指标更新
        for strategy_type in StrategyType:
            if strategy_type not in self.strategy_performance:
                self.strategy_performance[strategy_type] = StrategyPerformance(
                    strategy_type=strategy_type,
                    total_return=0.0,
                    sharpe_ratio=0.0,
                    max_drawdown=0.0,
                    win_rate=0.0,
                    profit_factor=0.0,
                    calmar_ratio=0.0,
                    last_updated=datetime.now()
                )

    async def _update_agent_status(self):
        """更新Agent状态"""
        # 模拟Agent状态更新
        agent_types = ["Data Scientist", "Portfolio Manager", "Risk Analyst",
                      "Quantitative Analyst", "Research Analyst", "Quantitative Engineer", "Trader"]

        for i, agent_type in enumerate(agent_types):
            agent_id = f"agent_{i+1}"
            if agent_id not in self.agent_status:
                self.agent_status[agent_id] = AgentStatus(
                    agent_id=agent_id,
                    agent_type=agent_type,
                    status="active",
                    current_task="Monitoring strategies",
                    performance_metrics={"efficiency": 85.0, "accuracy": 92.0},
                    last_heartbeat=datetime.now(),
                    resource_usage={"cpu": 45.0, "memory": 60.0}
                )

    async def _generate_strategy_signals(self):
        """生成策略信号"""
        import random

        for strategy_type in StrategyType:
            # 模拟信号生成
            signal_types = list(SignalType)
            signal = StrategySignal(
                strategy_type=strategy_type,
                signal_type=random.choice(signal_types),
                strength=random.uniform(50, 100),
                confidence=random.uniform(60, 95),
                timestamp=datetime.now(),
                parameters=self.active_strategies.get(strategy_type, {}),
                market_data={"price": random.uniform(100, 200), "volume": random.uniform(100000, 1000000)},
                metadata={"generation_method": "real_time_analysis"}
            )

            self.strategy_signals.append(signal)

            # 保留最近1000个信号
            if len(self.strategy_signals) > 1000:
                self.strategy_signals = self.strategy_signals[-1000:]

        # 广播新信号
        if self.strategy_signals:
            latest_signals = {signal.strategy_type.value: asdict(signal) for signal in self.strategy_signals[-4:]}
            await self.websocket_manager.broadcast({
                "type": "new_signals",
                "signals": latest_signals
            })

    async def _handle_websocket_message(self, websocket: WebSocket, message: str):
        """处理WebSocket消息"""
        try:
            data = json.loads(message)
            message_type = data.get("type")

            if message_type == "subscribe_strategies":
                # 客户端订阅策略更新
                await websocket.send_json({
                    "type": "strategies_data",
                    "data": {
                        strategy_type.value: parameters
                        for strategy_type, parameters in self.active_strategies.items()
                    }
                })

            elif message_type == "request_performance":
                # 客户端请求性能数据
                performance_data = {
                    strategy_type.value: asdict(performance)
                    for strategy_type, performance in self.strategy_performance.items()
                }
                await websocket.send_json({
                    "type": "performance_data",
                    "data": performance_data
                })

        except json.JSONDecodeError:
            self.logger.warning(f"无效的WebSocket消息格式: {message}")
        except Exception as e:
            self.logger.error(f"处理WebSocket消息异常: {e}")

    def _get_strategy_name(self, strategy_type: StrategyType) -> str:
        """获取策略显示名称"""
        names = {
            StrategyType.DIRECT_RSI: "直接RSI情绪策略",
            StrategyType.SENTIMENT_MOMENTUM: "情绪动量策略",
            StrategyType.COMPOSITE_INDEX: "复合指标策略",
            StrategyType.VOLATILITY_ADJUSTED: "波動率調整策略"
        }
        return names.get(strategy_type, strategy_type.value)

    def _calculate_overall_metrics(self) -> Dict[str, float]:
        """计算总体指标"""
        if not self.strategy_performance:
            return {"total_return": 0.0, "sharpe_ratio": 0.0, "max_drawdown": 0.0}

        total_return = sum(p.total_return for p in self.strategy_performance.values())
        sharpe_ratio = sum(p.sharpe_ratio for p in self.strategy_performance.values())
        max_drawdown = max(p.max_drawdown for p in self.strategy_performance.values())

        count = len(self.strategy_performance)
        return {
            "total_return": total_return / count,
            "sharpe_ratio": sharpe_ratio / count,
            "max_drawdown": max_drawdown
        }

    def get_app(self) -> FastAPI:
        """获取FastAPI应用实例"""
        return self.app


# 全局实例
_strategy_dashboard: Optional[StrategyManagementDashboard] = None


def get_strategy_dashboard() -> StrategyManagementDashboard:
    """获取策略管理Dashboard实例"""
    global _strategy_dashboard
    if _strategy_dashboard is None:
        _strategy_dashboard = StrategyManagementDashboard()
    return _strategy_dashboard


async def start_strategy_dashboard(port: int = 3003):
    """启动策略管理Dashboard"""
    dashboard = get_strategy_dashboard()
    await dashboard.start()

    config = uvicorn.Config(
        app=dashboard.get_app(),
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(start_strategy_dashboard())
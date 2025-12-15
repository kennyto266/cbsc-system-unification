#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo Strategy Service
演示策略服务

用于展示API端点的具体业务逻辑实现
For demonstrating concrete business logic implementation for API endpoints
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import uuid
import asyncio
import json

class DemoStrategyService:
    """演示策略服务类，提供完整的业务逻辑实现"""

    def __init__(self):
        # 模拟内存数据存储
        self.strategies = {}
        self.executions = {}
        self.templates = self._init_templates()
        self._init_demo_data()

    def _init_templates(self) -> Dict[str, Dict]:
        """初始化策略模板"""
        return {
            "ma_cross": {
                "id": "ma_cross",
                "name": "移动平均线交叉策略",
                "description": "基于短期和长期移动平均线交叉的买卖信号策略",
                "type": "technical",
                "default_parameters": {
                    "short_period": 10,
                    "long_period": 20,
                    "symbol": "BTC/USDT"
                },
                "risk_level": "medium"
            },
            "rsi_oversold": {
                "id": "rsi_oversold",
                "name": "RSI超卖反弹策略",
                "description": "基于RSI指标的超卖反弹买入策略",
                "type": "technical",
                "default_parameters": {
                    "rsi_period": 14,
                    "oversold_threshold": 30,
                    "overbought_threshold": 70,
                    "symbol": "ETH/USDT"
                },
                "risk_level": "high"
            },
            "grid_trading": {
                "id": "grid_trading",
                "name": "网格交易策略",
                "description": "在价格区间内自动低买高卖的网格策略",
                "type": "quantitative",
                "default_parameters": {
                    "grid_count": 20,
                    "price_range": "0.9-1.1",
                    "base_amount": 100,
                    "symbol": "BNB/USDT"
                },
                "risk_level": "low"
            }
        }

    def _init_demo_data(self):
        """初始化演示数据"""
        # 创建演示策略
        demo_strategies = [
            {
                "name": "比特币MA交叉策略",
                "description": "基于移动平均线的比特币交易策略",
                "type": "technical",
                "parameters": {"short_period": 5, "long_period": 15, "symbol": "BTC/USDT"},
                "risk_level": "medium",
                "user_id": 1
            },
            {
                "name": "以太坊RSI策略",
                "description": "RSI超卖反弹的以太坊策略",
                "type": "technical",
                "parameters": {"rsi_period": 14, "oversold_threshold": 25, "symbol": "ETH/USDT"},
                "risk_level": "high",
                "user_id": 1
            }
        ]

        for strategy_data in demo_strategies:
            strategy_id = str(uuid.uuid4())
            self.strategies[strategy_id] = {
                **strategy_data,
                "id": strategy_id,
                "status": "active",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "performance": {
                    "total_return": 0.15,
                    "win_rate": 0.65,
                    "max_drawdown": -0.08,
                    "sharpe_ratio": 1.2
                }
            }

    async def list_strategies(
        self,
        page: int = 1,
        page_size: int = 20,
        strategy_type: Optional[str] = None,
        status: Optional[str] = None,
        user_id: int = 1,
        is_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        """获取策略列表"""
        # 模拟分页和过滤
        filtered_strategies = []
        for strategy in self.strategies.values():
            # 过滤条件
            if strategy.get("user_id") != user_id:
                continue
            if strategy_type and strategy.get("type") != strategy_type:
                continue
            if status and strategy.get("status") != status:
                continue
            if is_active is not None:
                strategy_active = strategy.get("status") == "active"
                if strategy_active != is_active:
                    continue

            filtered_strategies.append(strategy)

        # 分页
        total = len(filtered_strategies)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_strategies = filtered_strategies[start:end]

        return {
            "strategies": paginated_strategies,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }

    async def create_strategy(self, request_data: Dict, user_id: int) -> Dict[str, Any]:
        """创建新策略"""
        strategy_id = str(uuid.uuid4())

        # 验证策略名称唯一性
        existing_names = [s.get("name") for s in self.strategies.values()
                          if s.get("user_id") == user_id]
        if request_data.get("name") in existing_names:
            raise ValueError("策略名称已存在")

        strategy = {
            "id": strategy_id,
            "name": request_data["name"],
            "description": request_data.get("description", ""),
            "type": request_data.get("type", "technical"),
            "parameters": request_data.get("parameters", {}),
            "risk_level": request_data.get("risk_level", "medium"),
            "status": "inactive",  # 新策略默认非激活
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "performance": {
                "total_return": 0.0,
                "win_rate": 0.0,
                "max_drawdown": 0.0,
                "sharpe_ratio": 0.0
            }
        }

        self.strategies[strategy_id] = strategy

        # 触发事件
        await self._emit_event("strategy_created", {
            "strategy_id": strategy_id,
            "user_id": user_id,
            "name": strategy["name"]
        })

        return strategy

    async def get_strategy_detail(self, strategy_id: str, user_id: int) -> Dict[str, Any]:
        """获取策略详情"""
        if strategy_id not in self.strategies:
            raise ValueError("策略不存在")

        strategy = self.strategies[strategy_id]
        if strategy.get("user_id") != user_id:
            raise PermissionError("无权限访问此策略")

        # 模拟最近信号
        recent_signals = [
            {
                "id": str(uuid.uuid4()),
                "type": "buy",
                "price": 45000.0,
                "time": (datetime.now() - timedelta(hours=2)).isoformat(),
                "confidence": 0.85
            },
            {
                "id": str(uuid.uuid4()),
                "type": "sell",
                "price": 46500.0,
                "time": (datetime.now() - timedelta(hours=5)).isoformat(),
                "confidence": 0.75
            }
        ]

        # 模拟执行历史
        execution_history = [
            {
                "id": str(uuid.uuid4()),
                "start_time": (datetime.now() - timedelta(days=1)).isoformat(),
                "end_time": (datetime.now() - timedelta(hours=23)).isoformat(),
                "status": "completed",
                "return": 0.025,
                "signals_count": 3
            }
        ]

        return {
            "strategy": strategy,
            "recent_signals": recent_signals,
            "execution_history": execution_history,
            "detailed_performance": {
                **strategy["performance"],
                "total_signals": len(recent_signals) + 5,
                "avg_hold_time": "2.5h",
                "profit_factor": 1.8
            }
        }

    async def update_strategy(self, strategy_id: str, request_data: Dict, user_id: int) -> Dict[str, Any]:
        """更新策略"""
        if strategy_id not in self.strategies:
            raise ValueError("策略不存在")

        strategy = self.strategies[strategy_id]
        if strategy.get("user_id") != user_id:
            raise PermissionError("无权限修改此策略")

        # 更新字段
        updateable_fields = ["name", "description", "parameters", "risk_level", "status"]
        for field in updateable_fields:
            if field in request_data:
                strategy[field] = request_data[field]

        strategy["updated_at"] = datetime.now().isoformat()

        # 如果状态变为激活，触发事件
        if request_data.get("status") == "active":
            await self._emit_event("strategy_activated", {
                "strategy_id": strategy_id,
                "user_id": user_id
            })

        return strategy

    async def delete_strategy(self, strategy_id: str, user_id: int):
        """删除策略"""
        if strategy_id not in self.strategies:
            raise ValueError("策略不存在")

        strategy = self.strategies[strategy_id]
        if strategy.get("user_id") != user_id:
            raise PermissionError("无权限删除此策略")

        # 检查是否正在运行
        if strategy.get("status") == "active":
            # 模拟检查是否有执行中的任务
            running_executions = [e for e in self.executions.values()
                                 if e.get("strategy_id") == strategy_id and e.get("status") == "running"]
            if running_executions:
                raise ValueError("策略正在运行中，无法删除")

        # 删除策略
        del self.strategies[strategy_id]

        # 触发事件
        await self._emit_event("strategy_deleted", {
            "strategy_id": strategy_id,
            "user_id": user_id
        })

    async def batch_operation(self, strategy_ids: List[str], operation: str, user_id: int, parameters: Dict = None) -> Dict[str, Any]:
        """批量操作策略"""
        success = []
        failed = []

        for strategy_id in strategy_ids:
            try:
                strategy = self.strategies.get(strategy_id)
                if not strategy or strategy.get("user_id") != user_id:
                    failed.append({"strategy_id": strategy_id, "error": "策略不存在或无权限"})
                    continue

                if operation == "activate":
                    strategy["status"] = "active"
                elif operation == "deactivate":
                    strategy["status"] = "inactive"
                elif operation == "delete":
                    del self.strategies[strategy_id]
                else:
                    raise ValueError(f"不支持的操作: {operation}")

                success.append(strategy_id)

            except Exception as e:
                failed.append({"strategy_id": strategy_id, "error": str(e)})

        return {
            "success": success,
            "failed": failed,
            "total_success": len(success),
            "total_failed": len(failed)
        }

    async def get_templates(self, strategy_type: Optional[str] = None) -> List[Dict]:
        """获取策略模板"""
        templates = list(self.templates.values())

        if strategy_type:
            templates = [t for t in templates if t.get("type") == strategy_type]

        return templates

    async def get_template(self, template_id: str) -> Optional[Dict]:
        """获取特定模板"""
        return self.templates.get(template_id)

    async def execute_strategy(self, strategy_id: str, user_id: int, parameters: Dict = None) -> Dict[str, Any]:
        """执行策略"""
        if strategy_id not in self.strategies:
            raise ValueError("策略不存在")

        strategy = self.strategies[strategy_id]
        if strategy.get("user_id") != user_id:
            raise PermissionError("无权限执行此策略")

        if strategy.get("status") != "active":
            raise ValueError("策略未激活")

        execution_id = str(uuid.uuid4())

        # 创建执行记录
        execution = {
            "id": execution_id,
            "strategy_id": strategy_id,
            "user_id": user_id,
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "parameters": parameters or {},
            "signals": [],
            "performance": {}
        }

        self.executions[execution_id] = execution

        # 模拟异步执行
        asyncio.create_task(self._simulate_execution(execution_id))

        # 触发事件
        await self._emit_event("strategy_execution_started", {
            "execution_id": execution_id,
            "strategy_id": strategy_id,
            "user_id": user_id
        })

        return execution

    async def _simulate_execution(self, execution_id: str):
        """模拟策略执行"""
        await asyncio.sleep(2)  # 模拟执行时间

        execution = self.executions.get(execution_id)
        if execution:
            execution["status"] = "completed"
            execution["end_time"] = datetime.now().isoformat()
            execution["performance"] = {
                "return": 0.015,
                "signals_generated": 5,
                "execution_time": "2.0s"
            }

    async def get_execution_status(self, execution_id: str, user_id: int) -> Dict[str, Any]:
        """获取执行状态"""
        execution = self.executions.get(execution_id)
        if not execution or execution.get("user_id") != user_id:
            raise ValueError("执行记录不存在或无权限")

        return execution

    async def _emit_event(self, event_type: str, data: Dict):
        """触发事件"""
        # 模拟事件发布
        print(f"[EVENT] {event_type}: {json.dumps(data, ensure_ascii=False)}")

# 创建全局服务实例
demo_strategy_service = DemoStrategyService()
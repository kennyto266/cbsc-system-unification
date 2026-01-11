#!/usr/bin/env python3
"""
獨立CBSC策略管理器 (Task #005)
Standalone CBSC Strategy Manager

不依賴外部認證系統的獨立策略管理器
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import uuid

# 導入策略模型
from .strategy_management_api import (
    Strategy, StrategyType, StrategyStatus, StrategyParameters,
    StrategySignal, StrategyPerformance, StrategyExecutionResult,
    StrategyExecutionRequest, CreateStrategyRequest, UpdateStrategyRequest,
    DataCompatibilityAdapter, StrategyTemplates, CBSCStrategyTemplate
)

logger = logging.getLogger(__name__)

# ============================================================================
# 簡化的用戶模型 (Simplified User Model)
# ============================================================================

@dataclass
class SimpleUser:
    """簡化的用戶模型"""
    id: int
    username: str
    email: str

# ============================================================================
# 獨立策略管理器 (Standalone Strategy Manager)
# ============================================================================

class StandaloneStrategyManager:
    """獨立的CBSC策略管理器"""

    def __init__(self):
        self.strategies: Dict[str, Strategy] = {}
        self.strategy_statuses: Dict[str, Dict[str, Any]] = {}
        self.execution_history: Dict[str, List[StrategyExecutionResult]] = {}
        self.strategy_templates: Dict[str, CBSCStrategyTemplate] = {}
        self.performance_cache: Dict[str, StrategyPerformance] = {}

        # 初始化模板
        self._initialize_templates()

    def _initialize_templates(self):
        """初始化策略模板"""
        templates = StrategyTemplates.get_all_templates()
        for template in templates:
            self.strategy_templates[template.id] = template
            logger.info(f"已加載策略模板: {template.name}")

    async def create_strategy(self, request: CreateStrategyRequest, user_id: int) -> Strategy:
        """創建新策略"""
        try:
            # 生成策略ID
            strategy_id = f"cbsc_{request.strategy_type.value}_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # 基於模板創建策略
            template = None
            if request.template_id and request.template_id in self.strategy_templates:
                template = self.strategy_templates[request.template_id]
                parameters = template.default_parameters
                # 覆蓋用戶提供的參數
                if request.parameters:
                    parameters_dict = parameters.dict()
                    parameters_dict.update(request.parameters.dict())
                    parameters = StrategyParameters(**parameters_dict)
            else:
                parameters = request.parameters

            # 創建策略
            strategy = Strategy(
                id=strategy_id,
                name=request.name,
                description=request.description,
                strategy_type=request.strategy_type,
                parameters=parameters,
                status=StrategyStatus.INACTIVE,
                is_active=False
            )

            # 驗證策略配置
            validation_result = await self.validate_strategy_config(strategy)
            if not validation_result["is_valid"]:
                raise ValueError(f"策略配置驗證失敗: {'; '.join(validation_result['validation_errors'])}")

            # 保存策略
            self.strategies[strategy_id] = strategy

            # 初始化狀態
            self.strategy_statuses[strategy_id] = {
                "strategy_id": strategy_id,
                "is_running": False,
                "current_pnl": 0.0,
                "daily_pnl": 0.0,
                "unrealized_pnl": 0.0,
                "last_updated": datetime.now(),
                "execution_status": "pending"
            }

            # 初始化執行歷史
            self.execution_history[strategy_id] = []

            logger.info(f"用戶 {user_id} 創建策略成功: {strategy_id}")
            return strategy

        except Exception as e:
            logger.error(f"創建策略失敗: {e}")
            raise

    async def get_strategies(
        self,
        user_id: int,
        strategy_type: Optional[StrategyType] = None,
        status: Optional[StrategyStatus] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20
    ) -> List[Strategy]:
        """獲取策略列表"""
        try:
            # 過濾用戶策略
            user_strategies = [
                strategy for strategy in self.strategies.values()
                if f"_{user_id}_" in strategy.id
            ]

            # 應用過濾條件
            if strategy_type:
                user_strategies = [s for s in user_strategies if s.strategy_type == strategy_type]

            if status:
                user_strategies = [s for s in user_strategies if s.status == status]

            if is_active is not None:
                user_strategies = [s for s in user_strategies if s.is_active == is_active]

            # 分頁
            start_index = (page - 1) * page_size
            end_index = start_index + page_size

            return user_strategies[start_index:end_index]

        except Exception as e:
            logger.error(f"獲取策略列表失敗: {e}")
            raise

    async def get_strategy(self, strategy_id: str, user_id: int) -> Strategy:
        """獲取策略詳情"""
        try:
            if strategy_id not in self.strategies:
                raise ValueError(f"策略不存在: {strategy_id}")

            # 驗證權限
            if f"_{user_id}_" not in strategy_id:
                raise ValueError("無權限訪問此策略")

            return self.strategies[strategy_id]

        except Exception as e:
            logger.error(f"獲取策略詳情失敗: {e}")
            raise

    async def update_strategy(
        self,
        strategy_id: str,
        request: UpdateStrategyRequest,
        user_id: int
    ) -> Strategy:
        """更新策略"""
        try:
            if strategy_id not in self.strategies:
                raise ValueError(f"策略不存在: {strategy_id}")

            # 驗證權限
            if f"_{user_id}_" not in strategy_id:
                raise ValueError("無權限訪問此策略")

            strategy = self.strategies[strategy_id]

            # 更新字段
            if request.name is not None:
                strategy.name = request.name

            if request.description is not None:
                strategy.description = request.description

            if request.parameters is not None:
                strategy.parameters = request.parameters

            if request.status is not None:
                strategy.status = request.status

            if request.is_active is not None:
                strategy.is_active = request.is_active

            strategy.updated_at = datetime.now()

            # 重新驗證配置
            validation_result = await self.validate_strategy_config(strategy)
            if not validation_result["is_valid"]:
                logger.warning(f"策略配置驗證失敗: {validation_result['validation_errors']}")

            logger.info(f"用戶 {user_id} 更新策略成功: {strategy_id}")
            return strategy

        except Exception as e:
            logger.error(f"更新策略失敗: {e}")
            raise

    async def delete_strategy(self, strategy_id: str, user_id: int) -> bool:
        """刪除策略"""
        try:
            if strategy_id not in self.strategies:
                raise ValueError(f"策略不存在: {strategy_id}")

            # 驗證權限
            if f"_{user_id}_" not in strategy_id:
                raise ValueError("無權限訪問此策略")

            # 檢查策略是否正在運行
            if strategy_id in self.strategy_statuses and self.strategy_statuses[strategy_id]["is_running"]:
                raise ValueError("無法刪除正在運行的策略，請先停止策略")

            # 刪除策略數據
            del self.strategies[strategy_id]
            if strategy_id in self.strategy_statuses:
                del self.strategy_statuses[strategy_id]
            if strategy_id in self.execution_history:
                del self.execution_history[strategy_id]
            if strategy_id in self.performance_cache:
                del self.performance_cache[strategy_id]

            logger.info(f"用戶 {user_id} 刪除策略成功: {strategy_id}")
            return True

        except Exception as e:
            logger.error(f"刪除策略失敗: {e}")
            raise

    async def execute_strategy(
        self,
        strategy_id: str,
        execution_request: StrategyExecutionRequest,
        user_id: int
    ) -> StrategyExecutionResult:
        """執行策略"""
        try:
            if strategy_id not in self.strategies:
                raise ValueError(f"策略不存在: {strategy_id}")

            # 驗證權限
            if f"_{user_id}_" not in strategy_id:
                raise ValueError("無權限訪問此策略")

            strategy = self.strategies[strategy_id]

            # 生成執行ID
            execution_id = f"exec_{strategy_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # 更新策略狀態
            strategy.status = StrategyStatus.ACTIVE
            strategy.is_active = True
            strategy.last_executed = datetime.now()

            # 更新實時狀態
            if strategy_id in self.strategy_statuses:
                self.strategy_statuses[strategy_id]["is_running"] = True
                self.strategy_statuses[strategy_id]["execution_status"] = "running"

            # 模擬執行結果
            execution_result = await self._simulate_strategy_execution(
                execution_id, strategy, execution_request
            )

            # 保存執行歷史
            if strategy_id not in self.execution_history:
                self.execution_history[strategy_id] = []
            self.execution_history[strategy_id].append(execution_result)

            logger.info(f"用戶 {user_id} 執行策略成功: {strategy_id}")
            return execution_result

        except Exception as e:
            logger.error(f"執行策略失敗: {e}")
            raise

    async def stop_strategy(self, strategy_id: str, user_id: int) -> bool:
        """停止策略執行"""
        try:
            if strategy_id not in self.strategies:
                raise ValueError(f"策略不存在: {strategy_id}")

            # 驗證權限
            if f"_{user_id}_" not in strategy_id:
                raise ValueError("無權限訪問此策略")

            strategy = self.strategies[strategy_id]

            # 更新策略狀態
            strategy.status = StrategyStatus.INACTIVE
            strategy.is_active = False

            # 更新實時狀態
            if strategy_id in self.strategy_statuses:
                self.strategy_statuses[strategy_id]["is_running"] = False
                self.strategy_statuses[strategy_id]["execution_status"] = "stopped"

            logger.info(f"用戶 {user_id} 停止策略成功: {strategy_id}")
            return True

        except Exception as e:
            logger.error(f"停止策略失敗: {e}")
            raise

    async def get_strategy_status(self, strategy_id: str, user_id: int) -> Dict[str, Any]:
        """獲取策略狀態"""
        try:
            if strategy_id not in self.strategies:
                raise ValueError(f"策略不存在: {strategy_id}")

            # 驗證權限
            if f"_{user_id}_" not in strategy_id:
                raise ValueError("無權限訪問此策略")

            return self.strategy_statuses.get(strategy_id, {
                "strategy_id": strategy_id,
                "is_running": False,
                "last_updated": datetime.now(),
                "execution_status": "pending"
            })

        except Exception as e:
            logger.error(f"獲取策略狀態失敗: {e}")
            raise

    async def get_strategy_metrics(self, strategy_id: str, user_id: int) -> StrategyPerformance:
        """獲取策略性能指標"""
        try:
            if strategy_id not in self.strategies:
                raise ValueError(f"策略不存在: {strategy_id}")

            # 驗證權限
            if f"_{user_id}_" not in strategy_id:
                raise ValueError("無權限訪問此策略")

            # 檢查緩存
            if strategy_id in self.performance_cache:
                return self.performance_cache[strategy_id]

            # 計算性能指標
            performance = await self._calculate_strategy_performance(strategy_id)

            # 緩存結果
            self.performance_cache[strategy_id] = performance

            return performance

        except Exception as e:
            logger.error(f"獲取策略性能指標失敗: {e}")
            raise

    async def get_strategy_templates(self) -> List[CBSCStrategyTemplate]:
        """獲取策略模板列表"""
        return list(self.strategy_templates.values())

    async def validate_strategy_config(self, strategy: Strategy) -> Dict[str, Any]:
        """驗證策略配置"""
        try:
            validation_errors = []
            validation_warnings = []

            # 參數範圍驗證
            params = strategy.parameters

            if params.rsi_period and (params.rsi_period < 2 or params.rsi_period > 50):
                validation_errors.append("RSI週期必須在2-50之間")

            if params.oversold_threshold and params.overbought_threshold:
                if params.oversold_threshold >= params.overbought_threshold:
                    validation_errors.append("超賣閾值必須小於超買閾值")

            if params.fast_period and params.slow_period:
                if params.fast_period >= params.slow_period:
                    validation_errors.append("快速週期必須小於慢速週期")

            # 策略類型特定驗證
            if strategy.strategy_type == StrategyType.DIRECT_RSI:
                if not params.rsi_period or not params.oversold_threshold or not params.overbought_threshold:
                    validation_errors.append("直接RSI策略需要設置RSI週期、超賣和超買閾值")

            # 警告檢查
            if params.weight_sentiment and params.weight_sentiment > 0.8:
                validation_warnings.append("情緒權重過高可能增加策略風險")

            # 推薦參數
            recommended_parameters = None
            if validation_errors:
                template = self.strategy_templates.get(f"{strategy.strategy_type.value}_template")
                if template:
                    recommended_parameters = template.default_parameters

            return {
                "is_valid": len(validation_errors) == 0,
                "validation_errors": validation_errors,
                "validation_warnings": validation_warnings,
                "recommended_parameters": recommended_parameters
            }

        except Exception as e:
            logger.error(f"驗證策略配置失敗: {e}")
            return {
                "is_valid": False,
                "validation_errors": [f"驗證過程中發生錯誤: {str(e)}"]
            }

    async def _simulate_strategy_execution(
        self,
        execution_id: str,
        strategy: Strategy,
        execution_request: StrategyExecutionRequest
    ) -> StrategyExecutionResult:
        """模擬策略執行"""
        try:
            # 模擬執行延遲
            await asyncio.sleep(0.1)

            # 生成模擬信號
            signals = []
            base_time = datetime.now() - timedelta(days=30)

            import random
            for i in range(10):  # 生成10個模擬信號
                signal_types = ["buy", "sell", "hold"]
                signal_type = random.choice(signal_types)

                signal = StrategySignal(
                    signal_id=f"{execution_id}_signal_{i+1:03d}",
                    strategy_type=strategy.strategy_type,
                    signal_type=signal_type,
                    strength=random.uniform(50, 90),
                    confidence=random.uniform(60, 95),
                    timestamp=base_time + timedelta(days=i*3),
                    market_data={
                        "price": random.uniform(140, 160),
                        "volume": random.randint(800000, 1200000),
                        "rsi": random.uniform(20, 80)
                    },
                    parameters=strategy.parameters,
                    metadata={"execution_id": execution_id, "simulated": True}
                )
                signals.append(signal)

            # 計算模擬性能
            performance = StrategyPerformance(
                strategy_type=strategy.strategy_type,
                total_return=random.uniform(-0.15, 0.25),  # -15% to 25%
                annual_return=random.uniform(-0.20, 0.30),  # -20% to 30%
                sharpe_ratio=random.uniform(0.5, 2.0),
                max_drawdown=random.uniform(0.05, 0.20),  # 5% to 20%
                win_rate=random.uniform(0.4, 0.7),  # 40% to 70%
                profit_factor=random.uniform(1.1, 2.5),
                calmar_ratio=random.uniform(0.5, 1.5),
                total_trades=len(signals),
                profit_trades=int(len(signals) * random.uniform(0.4, 0.7)),
                avg_profit=random.uniform(0.01, 0.03),  # 1% to 3%
                avg_loss=random.uniform(-0.02, -0.01),  # -1% to -2%
            )

            return StrategyExecutionResult(
                execution_id=execution_id,
                strategy_id=strategy.id,
                status="completed",
                start_time=execution_request.start_time or datetime.now() - timedelta(days=30),
                end_time=execution_request.end_time or datetime.now(),
                signals=signals,
                performance=performance,
                execution_metadata={
                    "execution_mode": execution_request.execution_mode,
                    "data_source": execution_request.data_source,
                    "simulated": True,
                    "total_processing_time": 0.1
                }
            )

        except Exception as e:
            logger.error(f"模擬策略執行失敗: {e}")
            return StrategyExecutionResult(
                execution_id=execution_id,
                strategy_id=strategy.id,
                status="failed",
                start_time=datetime.now(),
                error_message=f"執行失敗: {str(e)}",
                execution_metadata={"error": True}
            )

    async def _calculate_strategy_performance(self, strategy_id: str) -> StrategyPerformance:
        """計算策略性能指標"""
        try:
            execution_history = self.execution_history.get(strategy_id, [])

            if not execution_history:
                # 返回默認性能
                return StrategyPerformance(
                    strategy_type=StrategyType.DIRECT_RSI,
                    total_return=0.0,
                    annual_return=0.0,
                    sharpe_ratio=0.0,
                    max_drawdown=0.0,
                    win_rate=0.0,
                    profit_factor=0.0,
                    calmar_ratio=0.0,
                    total_trades=0,
                    profit_trades=0,
                    avg_profit=0.0,
                    avg_loss=0.0,
                )

            # 聚合所有執行結果的性能
            total_return = 0.0
            total_trades = 0
            profit_trades = 0

            for result in execution_history:
                if result.performance:
                    total_return += result.performance.total_return
                    total_trades += result.performance.total_trades
                    profit_trades += result.performance.profit_trades

            # 計算平均性能
            avg_return = total_return / len(execution_history) if execution_history else 0.0
            win_rate = profit_trades / total_trades if total_trades > 0 else 0.0

            return StrategyPerformance(
                strategy_type=self.strategies[strategy_id].strategy_type,
                total_return=avg_return,
                annual_return=avg_return * 252 / 30,  # 簡單年化
                sharpe_ratio=1.0 + avg_return * 5,  # 簡化計算
                max_drawdown=max(0.05, abs(avg_return) * 2),  # 簡化計算
                win_rate=win_rate,
                profit_factor=1.0 + win_rate,  # 簡化計算
                calmar_ratio=max(0.1, avg_return * 3),  # 簡化計算
                total_trades=total_trades,
                profit_trades=profit_trades,
                avg_profit=0.02,  # 模擬值
                avg_loss=-0.015,  # 模擬值
            )

        except Exception as e:
            logger.error(f"計算策略性能失敗: {e}")
            raise

# 全局獨立策略管理器實例
standalone_strategy_manager = StandaloneStrategyManager()

# ============================================================================
# 導出 (Exports)
# ============================================================================

__all__ = [
    "StandaloneStrategyManager",
    "standalone_strategy_manager",
    "SimpleUser"
]
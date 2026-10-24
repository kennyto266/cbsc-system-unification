#!/usr/bin/env python3
"""
統一策略管理服務
Unified Strategy Management Service

整合CBSC策略管理功能到統一架構中，提供完整的策略生命周期管理
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass
import uuid
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

# 導入統一數據模型
from ..models.strategy import (
    Strategy, StrategyConfig, StrategyPerformance, StrategyCategory,
    StrategyCreateSchema, StrategyUpdateSchema, StrategyResponseSchema,
    StrategyConfigCreateSchema, StrategyConfigResponseSchema,
    StrategyPerformanceResponseSchema
)
from ..models.unified_base import StatusEnum, RiskLevelEnum

# 導入認證系統
try:
    from auth_simple import get_current_user, User
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from auth_simple import get_current_user, User

# 導入現有策略管理模型
from .strategy_management_api import (
    StrategyType, SignalType, StrategyStatus as CBSCStrategyStatus,
    StrategyParameters, StrategySignal, StrategyPerformance,
    StrategyExecutionRequest, StrategyExecutionResult
)

logger = logging.getLogger(__name__)

# ============================================================================
# 擴展的數據模型 (Extended Data Models)
# ============================================================================

class StrategyExecutionState(str, Enum):
    """策略執行狀態"""
    IDLE = "idle"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"

class StrategySignal(BaseModel):
    """策略信號"""
    signal_id: str = Field(..., description="信號ID")
    strategy_id: str = Field(..., description="策略ID")
    signal_type: str = Field(..., description="信號類型")
    strength: float = Field(..., ge=0, le=100, description="信號強度")
    confidence: float = Field(..., ge=0, le=100, description="信號置信度")
    timestamp: datetime = Field(..., description="生成時間")
    market_data: Dict[str, Any] = Field(default_factory=dict, description="市場數據")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元數據")

class StrategyExecutionRequest(BaseModel):
    """策略執行請求"""
    strategy_id: str = Field(..., description="策略ID")
    start_time: Optional[datetime] = Field(None, description="開始時間")
    end_time: Optional[datetime] = Field(None, description="結束時間")
    execution_mode: str = Field("backtest", description="執行模式")
    data_source: str = Field("default", description="數據源")
    parameters: Optional[Dict[str, Any]] = Field(None, description="覆蓋參數")

class StrategyMetrics(BaseModel):
    """策略性能指標"""
    total_return: float = Field(0.0, description="總收益率")
    annual_return: float = Field(0.0, description="年化收益率")
    sharpe_ratio: Optional[float] = Field(None, description="夏普比率")
    sortino_ratio: Optional[float] = Field(None, description="索提諾比率")
    max_drawdown: float = Field(0.0, description="最大回撤")
    volatility: Optional[float] = Field(None, description="波動率")
    win_rate: float = Field(0.0, description="勝率")
    profit_factor: Optional[float] = Field(None, description="盈利因子")
    calmar_ratio: Optional[float] = Field(None, description="卡瑪比率")
    total_trades: int = Field(0, description="總交易次數")
    profit_trades: int = Field(0, description="盈利交易次數")

class StrategyTemplate(BaseModel):
    """策略模板"""
    id: str = Field(..., description="模板ID")
    name: str = Field(..., description="模板名稱")
    description: str = Field(..., description="模板描述")
    strategy_type: StrategyType = Field(..., description="策略類型")
    default_parameters: StrategyParameters = Field(..., description="默認參數")
    required_indicators: List[str] = Field(default_factory=list, description="必需指標")
    risk_level: RiskLevelEnum = Field(RiskLevelEnum.MEDIUM, description="風險等級")

# ============================================================================
# 統一策略管理器 (Unified Strategy Manager)
# ============================================================================

class UnifiedStrategyManager:
    """統一策略管理器"""

    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
        self.active_strategies: Dict[str, StrategyExecutionState] = {}
        self.strategy_cache: Dict[str, StrategyResponseSchema] = {}
        self.performance_cache: Dict[str, StrategyMetrics] = {}
        self.templates: Dict[str, StrategyTemplate] = {}

        # 初始化策略模板
        self._initialize_templates()

        logger.info("統一策略管理器已初始化")

    def _initialize_templates(self):
        """初始化策略模板"""
        # 直接RSI策略模板
        rsi_template = StrategyTemplate(
            id="direct_rsi_template",
            name="直接RSI策略",
            description="基於RSI指標的直接交易策略",
            strategy_type=StrategyType.DIRECT_RSI,
            default_parameters=StrategyParameters(
                rsi_period=14,
                oversold_threshold=30,
                overbought_threshold=70
            ),
            required_indicators=["RSI"],
            risk_level=RiskLevelEnum.MEDIUM
        )

        # 情緒動量策略模板
        sentiment_template = StrategyTemplate(
            id="sentiment_momentum_template",
            name="情緒動量策略",
            description="結合市場情緒和動量因子的複合策略",
            strategy_type=StrategyType.SENTIMENT_MOMENTUM,
            default_parameters=StrategyParameters(
                rsi_period=14,
                fast_period=12,
                slow_period=26,
                weight_sentiment=0.6,
                volume_weight=0.3
            ),
            required_indicators=["RSI", "MACD", "Volume", "Sentiment"],
            risk_level=RiskLevelEnum.HIGH
        )

        # 複合指標策略模板
        composite_template = StrategyTemplate(
            id="composite_index_template",
            name="複合指標策略",
            description="多指標綜合分析的複合策略",
            strategy_type=StrategyType.COMPOSITE_INDEX,
            default_parameters=StrategyParameters(
                rsi_period=14,
                fast_period=12,
                slow_period=26,
                signal_period=9,
                bb_period=20,
                bb_std=2
            ),
            required_indicators=["RSI", "MACD", "Bollinger Bands"],
            risk_level=RiskLevelEnum.MEDIUM
        )

        self.templates = {
            rsi_template.id: rsi_template,
            sentiment_template.id: sentiment_template,
            composite_template.id: composite_template
        }

        logger.info(f"已加載 {len(self.templates)} 個策略模板")

    def get_db_session(self) -> Session:
        """獲取數據庫會話"""
        return self.db_session_factory()

    # 策略CRUD操作
    async def create_strategy(
        self,
        request: StrategyCreateSchema,
        user_id: str
    ) -> StrategyResponseSchema:
        """創建新策略"""
        try:
            db = self.get_db_session()

            # 生成策略代碼
            strategy_code = f"STRAT_{request.strategy_type.upper()}_{user_id[:8]}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

            # 創建策略記錄
            strategy = Strategy(
                name=request.name,
                code=strategy_code,
                description=request.description,
                strategy_type=request.strategy_type,
                risk_level=request.risk_level,
                default_parameters=request.default_parameters,
                required_indicators=request.required_indicators,
                supported_timeframes=request.supported_timeframes,
                status=StatusEnum.INACTIVE,
                is_public=False,
                total_users=0,
                active_users=0,
                total_signals=0
            )

            db.add(strategy)
            db.commit()
            db.refresh(strategy)

            # 構建響應
            response = StrategyResponseSchema.from_orm(strategy)

            # 更新緩存
            self.strategy_cache[strategy.id] = response

            logger.info(f"用戶 {user_id} 創建策略成功: {strategy.id}")
            return response

        except Exception as e:
            db.rollback()
            logger.error(f"創建策略失敗: {e}")
            raise
        finally:
            db.close()

    async def get_strategies(
        self,
        user_id: str,
        strategy_type: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> List[StrategyResponseSchema]:
        """獲取策略列表"""
        try:
            db = self.get_db_session()

            query = db.query(Strategy)

            # 應用過濾條件
            if strategy_type:
                query = query.filter(Strategy.strategy_type == strategy_type)
            if status:
                query = query.filter(Strategy.status == status)

            # 分頁
            offset = (page - 1) * page_size
            strategies = query.offset(offset).limit(page_size).all()

            # 構建響應
            response_list = [StrategyResponseSchema.from_orm(s) for s in strategies]

            return response_list

        except Exception as e:
            logger.error(f"獲取策略列表失敗: {e}")
            raise
        finally:
            db.close()

    async def get_strategy(self, strategy_id: str, user_id: str) -> StrategyResponseSchema:
        """獲取策略詳情"""
        try:
            # 檢查緩存
            if strategy_id in self.strategy_cache:
                return self.strategy_cache[strategy_id]

            db = self.get_db_session()
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()

            if not strategy:
                raise HTTPException(status_code=404, detail=f"策略不存在: {strategy_id}")

            response = StrategyResponseSchema.from_orm(strategy)

            # 更新緩存
            self.strategy_cache[strategy_id] = response

            return response

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"獲取策略詳情失敗: {e}")
            raise
        finally:
            db.close()

    async def update_strategy(
        self,
        strategy_id: str,
        request: StrategyUpdateSchema,
        user_id: str
    ) -> StrategyResponseSchema:
        """更新策略"""
        try:
            db = self.get_db_session()
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()

            if not strategy:
                raise HTTPException(status_code=404, detail=f"策略不存在: {strategy_id}")

            # 更新字段
            if request.name is not None:
                strategy.name = request.name
            if request.description is not None:
                strategy.description = request.description
            if request.status is not None:
                strategy.status = request.status
            if request.default_parameters is not None:
                strategy.default_parameters = request.default_parameters

            strategy.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(strategy)

            # 更新緩存
            response = StrategyResponseSchema.from_orm(strategy)
            self.strategy_cache[strategy_id] = response

            logger.info(f"用戶 {user_id} 更新策略成功: {strategy_id}")
            return response

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"更新策略失敗: {e}")
            raise
        finally:
            db.close()

    async def delete_strategy(self, strategy_id: str, user_id: str) -> bool:
        """刪除策略"""
        try:
            db = self.get_db_session()
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()

            if not strategy:
                raise HTTPException(status_code=404, detail=f"策略不存在: {strategy_id}")

            # 檢查策略是否正在運行
            if strategy_id in self.active_strategies:
                if self.active_strategies[strategy_id] != StrategyExecutionState.STOPPED:
                    raise HTTPException(status_code=400, detail="無法刪除正在運行的策略")

            # 刪除相關記錄
            # 刪除策略配置
            db.query(StrategyConfig).filter(StrategyConfig.strategy_id == strategy_id).delete()
            # 刪除性能記錄
            db.query(StrategyPerformance).filter(StrategyPerformance.strategy_id == strategy_id).delete()
            # 刪除策略
            db.delete(strategy)

            db.commit()

            # 清理緩存
            if strategy_id in self.strategy_cache:
                del self.strategy_cache[strategy_id]
            if strategy_id in self.active_strategies:
                del self.active_strategies[strategy_id]
            if strategy_id in self.performance_cache:
                del self.performance_cache[strategy_id]

            logger.info(f"用戶 {user_id} 刪除策略成功: {strategy_id}")
            return True

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"刪除策略失敗: {e}")
            raise
        finally:
            db.close()

    # 策略執行控制
    async def execute_strategy(
        self,
        strategy_id: str,
        execution_request: StrategyExecutionRequest,
        user_id: str
    ) -> Dict[str, Any]:
        """執行策略"""
        try:
            db = self.get_db_session()
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()

            if not strategy:
                raise HTTPException(status_code=404, detail=f"策略不存在: {strategy_id}")

            # 檢查策略狀態
            if strategy_id in self.active_strategies:
                if self.active_strategies[strategy_id] == StrategyExecutionState.RUNNING:
                    raise HTTPException(status_code=400, detail="策略已在運行中")

            # 更新策略狀態
            strategy.status = StatusEnum.ACTIVE
            strategy.last_executed = datetime.utcnow()

            # 設置執行狀態
            self.active_strategies[strategy_id] = StrategyExecutionState.INITIALIZING

            # 模擬策略執行（實際應該調用策略引擎）
            execution_result = await self._execute_strategy_internal(
                strategy, execution_request
            )

            # 更新執行狀態
            self.active_strategies[strategy_id] = StrategyExecutionState.RUNNING

            db.commit()

            logger.info(f"用戶 {user_id} 執行策略成功: {strategy_id}")
            return execution_result

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            if strategy_id in self.active_strategies:
                self.active_strategies[strategy_id] = StrategyExecutionState.ERROR
            logger.error(f"執行策略失敗: {e}")
            raise
        finally:
            db.close()

    async def stop_strategy(self, strategy_id: str, user_id: str) -> bool:
        """停止策略執行"""
        try:
            db = self.get_db_session()
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()

            if not strategy:
                raise HTTPException(status_code=404, detail=f"策略不存在: {strategy_id}")

            # 更新策略狀態
            strategy.status = StatusEnum.INACTIVE

            # 更新執行狀態
            if strategy_id in self.active_strategies:
                self.active_strategies[strategy_id] = StrategyExecutionState.STOPPED

            db.commit()

            logger.info(f"用戶 {user_id} 停止策略成功: {strategy_id}")
            return True

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"停止策略失敗: {e}")
            raise
        finally:
            db.close()

    async def get_strategy_status(self, strategy_id: str, user_id: str) -> Dict[str, Any]:
        """獲取策略狀態"""
        try:
            db = self.get_db_session()
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()

            if not strategy:
                raise HTTPException(status_code=404, detail=f"策略不存在: {strategy_id}")

            # 獲取執行狀態
            execution_state = self.active_strategies.get(strategy_id, StrategyExecutionState.IDLE)

            # 獲取最新性能指標
            latest_performance = db.query(StrategyPerformance)\
                .filter(StrategyPerformance.strategy_id == strategy_id)\
                .order_by(desc(StrategyPerformance.date))\
                .first()

            status_data = {
                "strategy_id": strategy_id,
                "status": strategy.status,
                "execution_state": execution_state,
                "is_running": execution_state == StrategyExecutionState.RUNNING,
                "last_executed": strategy.last_executed,
                "latest_performance": latest_performance.date if latest_performance else None,
                "total_return": latest_performance.total_return if latest_performance else 0.0,
                "current_pnl": latest_performance.daily_return if latest_performance else 0.0
            }

            return status_data

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"獲取策略狀態失敗: {e}")
            raise
        finally:
            db.close()

    async def get_strategy_metrics(self, strategy_id: str, user_id: str) -> StrategyMetrics:
        """獲取策略性能指標"""
        try:
            # 檢查緩存
            if strategy_id in self.performance_cache:
                return self.performance_cache[strategy_id]

            db = self.get_db_session()
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()

            if not strategy:
                raise HTTPException(status_code=404, detail=f"策略不存在: {strategy_id}")

            # 聚合性能數據
            performances = db.query(StrategyPerformance)\
                .filter(StrategyPerformance.strategy_id == strategy_id)\
                .order_by(desc(StrategyPerformance.date))\
                .limit(252)  # 過去一年的數據（交易日）
                .all()

            if not performances:
                # 返回默認指標
                return StrategyMetrics()

            # 計算聚合指標
            total_return = performances[0].cumulative_return if performances[0] else 0.0
            daily_returns = [p.daily_return for p in performances if p.daily_return is not None]

            # 計算年化收益率
            annual_return = total_return * 252 / len(performances) if performances else 0.0

            # 計算波動率
            volatility = np.std(daily_returns) * np.sqrt(252) if daily_returns else None

            # 計算夏普比率
            sharpe_ratio = annual_return / volatility if volatility and volatility > 0 else None

            # 其他指標
            win_rate = performances[0].win_rate if performances else 0.0
            max_drawdown = max([p.max_drawdown for p in performances]) if performances else 0.0
            total_trades = sum([p.total_trades for p in performances]) if performances else 0
            profit_trades = sum([p.winning_trades for p in performances]) if performances else 0

            metrics = StrategyMetrics(
                total_return=total_return,
                annual_return=annual_return,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                volatility=volatility,
                win_rate=win_rate,
                total_trades=total_trades,
                profit_trades=profit_trades
            )

            # 更新緩存
            self.performance_cache[strategy_id] = metrics

            return metrics

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"獲取策略性能指標失敗: {e}")
            raise
        finally:
            db.close()

    async def get_strategy_templates(self) -> List[StrategyTemplate]:
        """獲取策略模板列表"""
        return list(self.templates.values())

    async def validate_strategy_config(self, strategy_data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證策略配置"""
        try:
            validation_errors = []
            validation_warnings = []

            # 基本驗證
            if not strategy_data.get("name"):
                validation_errors.append("策略名稱不能為空")

            if not strategy_data.get("strategy_type"):
                validation_errors.append("策略類型不能為空")

            # 參數驗證
            parameters = strategy_data.get("default_parameters", {})

            if parameters.get("rsi_period"):
                rsi_period = parameters["rsi_period"]
                if rsi_period < 2 or rsi_period > 50:
                    validation_errors.append("RSI週期必須在2-50之間")

            # 超買超賣閾值驗證
            oversold = parameters.get("oversold_threshold", 30)
            overbought = parameters.get("overbought_threshold", 70)
            if oversold >= overbought:
                validation_errors.append("超賣閾值必須小於超買閾值")

            # 快速慢速週期驗證
            fast_period = parameters.get("fast_period")
            slow_period = parameters.get("slow_period")
            if fast_period and slow_period and fast_period >= slow_period:
                validation_errors.append("快速週期必須小於慢速週期")

            # 風險警告
            if parameters.get("weight_sentiment", 0) > 0.8:
                validation_warnings.append("情緒權重過高可能增加策略風險")

            return {
                "is_valid": len(validation_errors) == 0,
                "validation_errors": validation_errors,
                "validation_warnings": validation_warnings
            }

        except Exception as e:
            logger.error(f"驗證策略配置失敗: {e}")
            return {
                "is_valid": False,
                "validation_errors": [f"驗證過程中發生錯誤: {str(e)}"],
                "validation_warnings": []
            }

    async def _execute_strategy_internal(
        self,
        strategy: Strategy,
        execution_request: StrategyExecutionRequest
    ) -> Dict[str, Any]:
        """內部策略執行邏輯"""
        try:
            # 模擬執行延遲
            await asyncio.sleep(0.1)

            # 生成執行ID
            execution_id = f"exec_{strategy.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # 模擬執行結果
            result = {
                "execution_id": execution_id,
                "strategy_id": strategy.id,
                "status": "completed",
                "start_time": execution_request.start_time or datetime.now() - timedelta(days=30),
                "end_time": execution_request.end_time or datetime.now(),
                "total_signals": np.random.randint(10, 50),
                "executed_signals": np.random.randint(8, 45),
                "success_rate": np.random.uniform(0.7, 0.95),
                "performance": {
                    "total_return": np.random.normal(0.05, 0.15),
                    "sharpe_ratio": np.random.normal(1.2, 0.5),
                    "max_drawdown": abs(np.random.normal(0.08, 0.03))
                }
            }

            # 保存性能記錄到數據庫
            db = self.get_db_session()

            performance = StrategyPerformance(
                strategy_id=strategy.id,
                date=datetime.utcnow(),
                total_return=result["performance"]["total_return"],
                cumulative_return=result["performance"]["total_return"],
                sharpe_ratio=result["performance"]["sharpe_ratio"],
                max_drawdown=result["performance"]["max_drawdown"],
                total_trades=result["total_signals"],
                win_rate=result["success_rate"]
            )

            db.add(performance)
            db.commit()

            return result

        except Exception as e:
            logger.error(f"內部策略執行失敗: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
            finally:
                db.close()

# 全局策略管理器實例
_unified_strategy_manager: Optional[UnifiedStrategyManager] = None

def get_unified_strategy_manager() -> UnifiedStrategyManager:
    """獲取統一策略管理器單例"""
    global _unified_strategy_manager
    if _unified_strategy_manager is None:
        from auth_simple import auth_service
        _unified_strategy_manager = UnifiedStrategyManager(auth_service.get_db)
    return _unified_strategy_manager

def init_unified_strategy_manager():
    """初始化統一策略管理器"""
    get_unified_strategy_manager()
    logger.info("統一策略管理器已初始化")

# 導出
__all__ = [
    "UnifiedStrategyManager",
    "get_unified_strategy_manager",
    "init_unified_strategy_manager",
    "StrategyExecutionState",
    "StrategySignal",
    "StrategyExecutionRequest",
    "StrategyMetrics",
    "StrategyTemplate"
]
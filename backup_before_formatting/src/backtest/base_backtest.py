"""
基礎回測引擎 - 回測框架基礎類

定義回測引擎的標準接口和基礎功能
"""

import asyncio
import logging
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BacktestStatus(str, Enum):
    """回測狀態"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BacktestConfig(BaseModel):
    """回測配置"""

    strategy_name: str = Field(..., description="策略名稱")
    symbols: List[str] = Field(..., description="交易標的列表")
    start_date: date = Field(..., description="開始日期")
    end_date: date = Field(..., description="結束日期")
    initial_capital: float = Field(1000000, gt=0, description="初始資本")
    benchmark: Optional[str] = Field(None, description="基準標的")
    config: Dict[str, Any] = Field(default_factory=dict, description="額外配置")


class BacktestResult(BaseModel):
    """回測結果"""

    strategy_name: str = Field(..., description="策略名稱")
    start_date: date = Field(..., description="開始日期")
    end_date: date = Field(..., description="結束日期")
    initial_capital: float = Field(..., description="初始資本")
    final_capital: float = Field(..., description="最終資本")
    total_return: float = Field(..., description="總收益率")
    annualized_return: float = Field(..., description="年化收益率")
    sharpe_ratio: float = Field(..., description="夏普比率")
    max_drawdown: float = Field(..., description="最大回撤")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="詳細指標")
    trades: List[Dict[str, Any]] = Field(default_factory=list, description="交易記錄")
    portfolio_values: List[float] = Field(
        default_factory=list, description="組合價值序列"
    )
    daily_returns: List[float] = Field(default_factory=list, description="日收益率序列")


class BaseBacktestEngine:
    """回測引擎基礎類"""

    def __init__(self, config: BacktestConfig):
        self.config = config
        self.logger = logging.getLogger(
            f"hk_quant_system.backtest.{config.strategy_name}"
        )
        self.status = BacktestStatus.PENDING
        self.historical_data: Dict[str, Any] = {}
        self.benchmark_data: Optional[Any] = None

    async def initialize(self) -> bool:
        """初始化回測引擎"""
        try:
            self.logger.info(
                f"Initializing backtest engine for {self.config.strategy_name}"
            )
            self.status = BacktestStatus.PENDING
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize backtest engine: {e}")
            return False

    async def run_backtest(self, strategy_func) -> BacktestResult:
        """運行回測"""
        try:
            self.status = BacktestStatus.RUNNING
            self.logger.info(f"Starting backtest for {self.config.strategy_name}")

            # 這裡應該實現具體的回測邏輯
            # 子類需要重寫這個方法

            result = BacktestResult(
                strategy_name=self.config.strategy_name,
                start_date=self.config.start_date,
                end_date=self.config.end_date,
                initial_capital=self.config.initial_capital,
                final_capital=self.config.initial_capital,
                total_return=0.0,
                annualized_return=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
            )

            self.status = BacktestStatus.COMPLETED
            self.logger.info(f"Backtest completed for {self.config.strategy_name}")
            return result

        except Exception as e:
            self.status = BacktestStatus.FAILED
            self.logger.error(f"Backtest failed for {self.config.strategy_name}: {e}")
            raise

    async def cleanup(self) -> None:
        """清理資源"""
        try:
            self.logger.info(
                f"Cleaning up backtest engine for {self.config.strategy_name}"
            )
            self.status = BacktestStatus.PENDING
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

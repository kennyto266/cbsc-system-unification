#!/usr/bin/env python3
"""
CBSC策略管理统一API (Task 005)
CBSC Strategy Management Unified API

整合现有CBSC策略管理功能到统一架构中，确保向后兼容性和数据平滑迁移
"""

from datetime import datetime, date
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, validator
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# 核心数据模型 (Core Data Models)
# ============================================================================

class StrategyType(str, Enum):
    """策略类型枚举"""
    DIRECT_RSI = "direct_rsi"
    SENTIMENT_MOMENTUM = "sentiment_momentum"
    COMPOSITE_INDEX = "composite_index"
    VOLATILITY_ADJUSTED = "volatility_adjusted"
    TECHNICAL_RSI = "technical_rsi"
    TECHNICAL_MACD = "technical_macd"
    TECHNICAL_BOLLINGER = "technical_bollinger"

class SignalType(str, Enum):
    """信号类型枚举"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    EXTREME_BULLISH = "extreme_bullish"
    EXTREME_BEARISH = "extreme_bearish"
    GOLDEN_CROSS = "golden_cross"
    DEATH_CROSS = "death_cross"
    SQUEEZE = "squeeze"
    BREAKTHROUGH = "breakthrough"

class StrategyStatus(str, Enum):
    """策略状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    TESTING = "testing"
    ERROR = "error"
    STOPPED = "stopped"

class RiskLevel(str, Enum):
    """风险等级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"

class CBSCContract(BaseModel):
    """CBSC合约信息"""
    ticker: str = Field(..., description="牛熊证代码")
    underlying_ticker: str = Field(..., description="标的资产代码")
    cbsc_type: str = Field(..., description="CBSC类型: BULL/BEAR")
    call_price: float = Field(..., gt=0, description="收回价")
    strike_price: float = Field(..., gt=0, description="行使价")
    leverage_ratio: float = Field(..., gt=1, description="杠杆倍数")
    issue_date: date = Field(..., description="发行日期")
    maturity_date: date = Field(..., description="到期日期")
    issuer: str = Field(..., description="发行商")

class StrategyParameters(BaseModel):
    """策略参数"""
    rsi_period: Optional[int] = Field(14, ge=2, le=50, description="RSI周期")
    oversold_threshold: Optional[float] = Field(30, ge=0, le=50, description="超卖阈值")
    overbought_threshold: Optional[float] = Field(70, ge=50, le=100, description="超买阈值")
    fast_period: Optional[int] = Field(12, ge=5, le=30, description="快速周期")
    slow_period: Optional[int] = Field(26, ge=10, le=50, description="慢速周期")
    signal_period: Optional[int] = Field(9, ge=5, le=20, description="信号周期")
    bb_period: Optional[int] = Field(20, ge=10, le=50, description="布林带周期")
    bb_std: Optional[float] = Field(2, ge=1, le=3, description="布林带标准差")
    weight_sentiment: Optional[float] = Field(0.6, ge=0, le=1, description="情绪权重")
    volatility_window: Optional[int] = Field(20, ge=5, le=50, description="波动率窗口")
    volume_weight: Optional[float] = Field(0.3, ge=0, le=1, description="成交量权重")

class StrategySignal(BaseModel):
    """策略信号"""
    signal_id: str = Field(..., description="信号唯一ID")
    strategy_type: StrategyType = Field(..., description="策略类型")
    signal_type: SignalType = Field(..., description="信号类型")
    strength: float = Field(..., ge=0, le=100, description="信号强度")
    confidence: float = Field(..., ge=0, le=100, description="信号置信度")
    timestamp: datetime = Field(..., description="生成时间")
    market_data: Dict[str, float] = Field(..., description="市场数据")
    parameters: StrategyParameters = Field(..., description="策略参数")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")

    @validator('signal_id', pre=True, always=True)
    def generate_signal_id(cls, v, values):
        """生成信号ID"""
        if not v:
            timestamp = datetime.now()
            strategy_type = values.get('strategy_type', StrategyType.DIRECT_RSI)
            signal_type = values.get('signal_type', SignalType.HOLD)
            confidence = values.get('confidence', 50)
            return f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{strategy_type.value}_{signal_type.value}_{confidence:.0f}"
        return v

class StrategyPerformance(BaseModel):
    """策略性能"""
    strategy_type: StrategyType = Field(..., description="策略类型")
    total_return: float = Field(..., description="总收益率")
    annual_return: float = Field(..., description="年化收益率")
    sharpe_ratio: float = Field(..., description="夏普比率")
    max_drawdown: float = Field(..., description="最大回撤")
    win_rate: float = Field(..., ge=0, le=1, description="胜率")
    profit_factor: float = Field(..., description="盈利因子")
    calmar_ratio: float = Field(..., description="卡玛比率")
    total_trades: int = Field(..., ge=0, description="总交易次数")
    profit_trades: int = Field(..., ge=0, description="盈利交易次数")
    avg_profit: float = Field(..., description="平均盈利")
    avg_loss: float = Field(..., description="平均亏损")
    last_updated: datetime = Field(default_factory=datetime.now, description="最后更新时间")

class Strategy(BaseModel):
    """策略定义"""
    id: str = Field(..., description="策略ID")
    name: str = Field(..., description="策略名称")
    description: str = Field(..., description="策略描述")
    strategy_type: StrategyType = Field(..., description="策略类型")
    parameters: StrategyParameters = Field(..., description="策略参数")
    status: StrategyStatus = Field(default=StrategyStatus.INACTIVE, description="策略状态")
    is_active: bool = Field(default=False, description="是否激活")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    last_executed: Optional[datetime] = Field(None, description="最后执行时间")

    class Config:
        use_enum_values = True

class StrategyExecutionRequest(BaseModel):
    """策略执行请求"""
    strategy_id: str = Field(..., description="策略ID")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    execution_mode: str = Field("backtest", description="执行模式: backtest/real_time")
    data_source: Optional[str] = Field(None, description="数据源")
    parameters_override: Optional[StrategyParameters] = Field(None, description="参数覆盖")

class StrategyExecutionResult(BaseModel):
    """策略执行结果"""
    execution_id: str = Field(..., description="执行ID")
    strategy_id: str = Field(..., description="策略ID")
    status: str = Field(..., description="执行状态")
    start_time: datetime = Field(..., description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    signals: List[StrategySignal] = Field(default_factory=list, description="生成的信号")
    performance: Optional[StrategyPerformance] = Field(None, description="性能指标")
    error_message: Optional[str] = Field(None, description="错误信息")
    execution_metadata: Dict[str, Any] = Field(default_factory=dict, description="执行元数据")

# ============================================================================
# CBSC情绪数据模型 (CBSC Sentiment Data Models)
# ============================================================================

class WarrantSentiment(BaseModel):
    """牛熊证市场情绪数据"""
    date: datetime = Field(..., description="数据日期")
    afternoon_close: float = Field(..., gt=0, description="午后收盘价")
    bull_ratio: float = Field(..., ge=0, le=1, description="牛证占比")
    bull_bear_ratio: float = Field(..., gt=0, description="牛熊证成交额比率")
    bull_turnover_hkd: float = Field(..., ge=0, description="牛证成交额(港元)")
    bear_turnover_hkd: float = Field(..., ge=0, description="熊证成交额(港元)")
    total_turnover: float = Field(..., ge=0, description="总成交额")
    sentiment_strength: float = Field(..., ge=-1, le=1, description="情绪强度")

    @validator('total_turnover', pre=True, always=True)
    def calculate_total_turnover(cls, v, values):
        """计算总成交额"""
        if not v:
            bull_turnover = values.get('bull_turnover_hkd', 0)
            bear_turnover = values.get('bear_turnover_hkd', 0)
            return bull_turnover + bear_turnover
        return v

    @validator('sentiment_strength', pre=True, always=True)
    def calculate_sentiment_strength(cls, v, values):
        """计算情绪强度"""
        if not v:
            bull_turnover = values.get('bull_turnover_hkd', 0)
            bear_turnover = values.get('bear_turnover_hkd', 0)
            total = bull_turnover + bear_turnover
            if total > 0:
                return (bull_turnover - bear_turnover) / total
            return 0.0
        return v

class CBSCStrategyTemplate(BaseModel):
    """CBSC策略模板"""
    id: str = Field(..., description="模板ID")
    name: str = Field(..., description="模板名称")
    description: str = Field(..., description="模板描述")
    strategy_type: StrategyType = Field(..., description="策略类型")
    default_parameters: StrategyParameters = Field(..., description="默认参数")
    parameter_constraints: Dict[str, Dict[str, Any]] = Field(..., description="参数约束")
    category: str = Field(..., description="策略分类")
    tags: List[str] = Field(default_factory=list, description="标签")
    is_system_template: bool = Field(default=True, description="是否系统模板")

# ============================================================================
# API请求/响应模型 (API Request/Response Models)
# ============================================================================

class StrategyListResponse(BaseModel):
    """策略列表响应"""
    strategies: List[Strategy] = Field(..., description="策略列表")
    total_count: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页")
    page_size: int = Field(..., description="每页大小")

class StrategyDetailResponse(BaseModel):
    """策略详情响应"""
    strategy: Strategy = Field(..., description="策略信息")
    recent_signals: List[StrategySignal] = Field(..., description="最近信号")
    performance: Optional[StrategyPerformance] = Field(None, description="性能指标")
    execution_history: List[StrategyExecutionResult] = Field(..., description="执行历史")

class CreateStrategyRequest(BaseModel):
    """创建策略请求"""
    name: str = Field(..., min_length=1, max_length=100, description="策略名称")
    description: str = Field(..., min_length=1, max_length=500, description="策略描述")
    strategy_type: StrategyType = Field(..., description="策略类型")
    parameters: StrategyParameters = Field(..., description="策略参数")
    template_id: Optional[str] = Field(None, description="模板ID")

class UpdateStrategyRequest(BaseModel):
    """更新策略请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="策略名称")
    description: Optional[str] = Field(None, min_length=1, max_length=500, description="策略描述")
    parameters: Optional[StrategyParameters] = Field(None, description="策略参数")
    status: Optional[StrategyStatus] = Field(None, description="策略状态")
    is_active: Optional[bool] = Field(None, description="是否激活")

class BatchStrategyOperation(BaseModel):
    """批量策略操作"""
    strategy_ids: List[str] = Field(..., min_items=1, description="策略ID列表")
    operation: str = Field(..., description="操作类型: activate/deactivate/delete")
    parameters: Optional[Dict[str, Any]] = Field(None, description="操作参数")

class StrategyOptimizationRequest(BaseModel):
    """策略优化请求"""
    strategy_id: str = Field(..., description="策略ID")
    optimization_method: str = Field(..., description="优化方法: grid/random/bayes")
    parameter_ranges: Dict[str, Dict[str, float]] = Field(..., description="参数范围")
    objective_metric: str = Field(..., description="优化目标: sharpe_ratio/total_return/win_rate")
    max_iterations: int = Field(100, ge=1, le=1000, description="最大迭代次数")
    time_range: Dict[str, str] = Field(..., description="时间范围")

class StrategyOptimizationResult(BaseModel):
    """策略优化结果"""
    optimization_id: str = Field(..., description="优化ID")
    strategy_id: str = Field(..., description="策略ID")
    best_parameters: StrategyParameters = Field(..., description="最优参数")
    best_performance: StrategyPerformance = Field(..., description="最优性能")
    optimization_history: List[Dict[str, Any]] = Field(..., description="优化历史")
    convergence_info: Dict[str, Any] = Field(..., description="收敛信息")

# ============================================================================
# 数据兼容性适配器 (Data Compatibility Adapter)
# ============================================================================

class DataCompatibilityAdapter:
    """数据兼容性适配器"""

    @staticmethod
    def adapt_legacy_strategy_format(legacy_data: Dict[str, Any]) -> Strategy:
        """适配旧版策略格式"""
        logger.info(f"适配旧版策略格式: {legacy_data}")

        # 映射旧版策略类型
        strategy_type_mapping = {
            "direct_rsi": StrategyType.DIRECT_RSI,
            "sentiment_momentum": StrategyType.SENTIMENT_MOMENTUM,
            "composite_index": StrategyType.COMPOSITE_INDEX,
            "volatility_adjusted": StrategyType.VOLATILITY_ADJUSTED,
        }

        # 提取参数
        legacy_params = legacy_data.get("parameters", {})
        parameters = StrategyParameters(
            rsi_period=legacy_params.get("rsi_period", 14),
            oversold_threshold=legacy_params.get("oversold_threshold", 30),
            overbought_threshold=legacy_params.get("overbought_threshold", 70),
            fast_period=legacy_params.get("fast_period", 12),
            slow_period=legacy_params.get("slow_period", 26),
            signal_period=legacy_params.get("signal_period", 9),
            bb_period=legacy_params.get("bb_period", 20),
            bb_std=legacy_params.get("bb_std", 2),
            weight_sentiment=legacy_params.get("weight_sentiment", 0.6),
            volatility_window=legacy_params.get("volatility_window", 20),
            volume_weight=legacy_params.get("volume_weight", 0.3)
        )

        return Strategy(
            id=legacy_data.get("id", f"legacy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
            name=legacy_data.get("name", "Legacy Strategy"),
            description=legacy_data.get("description", "Migrated from legacy system"),
            strategy_type=strategy_type_mapping.get(
                legacy_data.get("strategy_type"),
                StrategyType.DIRECT_RSI
            ),
            parameters=parameters,
            status=StrategyStatus.ACTIVE if legacy_data.get("is_active", False) else StrategyStatus.INACTIVE,
            is_active=legacy_data.get("is_active", False),
            created_at=legacy_data.get("created_at", datetime.now()),
            updated_at=legacy_data.get("updated_at", datetime.now())
        )

    @staticmethod
    def adapt_legacy_signal_format(legacy_data: Dict[str, Any]) -> StrategySignal:
        """适配旧版信号格式"""
        logger.info(f"适配旧版信号格式: {legacy_data}")

        # 映射信号类型
        signal_type_mapping = {
            "buy": SignalType.BUY,
            "sell": SignalType.SELL,
            "hold": SignalType.HOLD,
            "extreme_bullish": SignalType.EXTREME_BULLISH,
            "extreme_bearish": SignalType.EXTREME_BEARISH,
        }

        # 创建策略参数
        parameters = StrategyParameters(
            rsi_period=legacy_data.get("parameters", {}).get("rsi_period", 14),
            oversold_threshold=legacy_data.get("parameters", {}).get("oversold_threshold", 30),
            overbought_threshold=legacy_data.get("parameters", {}).get("overbought_threshold", 70)
        )

        return StrategySignal(
            signal_id=legacy_data.get("signal_id", ""),
            strategy_type=StrategyType(legacy_data.get("strategy_type", "direct_rsi")),
            signal_type=signal_type_mapping.get(
                legacy_data.get("signal_type"),
                SignalType.HOLD
            ),
            strength=legacy_data.get("strength", 50),
            confidence=legacy_data.get("confidence", 50),
            timestamp=legacy_data.get("timestamp", datetime.now()),
            market_data=legacy_data.get("market_data", {}),
            parameters=parameters,
            metadata=legacy_data.get("metadata", {})
        )

# ============================================================================
# 预定义策略模板 (Predefined Strategy Templates)
# ============================================================================

class StrategyTemplates:
    """预定义策略模板"""

    @staticmethod
    def get_direct_rsi_template() -> CBSCStrategyTemplate:
        """直接RSI策略模板"""
        return CBSCStrategyTemplate(
            id="direct_rsi_template",
            name="直接RSI情绪策略",
            description="基于牛熊比例直接计算RSI，识别极端情绪信号",
            strategy_type=StrategyType.DIRECT_RSI,
            default_parameters=StrategyParameters(
                rsi_period=14,
                oversold_threshold=30,
                overbought_threshold=70
            ),
            parameter_constraints={
                "rsi_period": {"min": 5, "max": 30, "step": 1},
                "oversold_threshold": {"min": 10, "max": 40, "step": 1},
                "overbought_threshold": {"min": 60, "max": 90, "step": 1}
            },
            category="情绪策略",
            tags=["RSI", "情绪", "反转"],
            is_system_template=True
        )

    @staticmethod
    def get_sentiment_momentum_template() -> CBSCStrategyTemplate:
        """情绪动量策略模板"""
        return CBSCStrategyTemplate(
            id="sentiment_momentum_template",
            name="情绪动量策略",
            description="MACD风格的情绪变化率分析，捕捉情绪转折点",
            strategy_type=StrategyType.SENTIMENT_MOMENTUM,
            default_parameters=StrategyParameters(
                fast_period=12,
                slow_period=26,
                signal_period=9
            ),
            parameter_constraints={
                "fast_period": {"min": 5, "max": 20, "step": 1},
                "slow_period": {"min": 15, "max": 40, "step": 1},
                "signal_period": {"min": 5, "max": 15, "step": 1}
            },
            category="情绪策略",
            tags=["动量", "MACD", "趋势"],
            is_system_template=True
        )

    @staticmethod
    def get_composite_index_template() -> CBSCStrategyTemplate:
        """复合指标策略模板"""
        return CBSCStrategyTemplate(
            id="composite_index_template",
            name="复合指标策略",
            description="多维度情绪布林带分析，识别情绪挤压和突破",
            strategy_type=StrategyType.COMPOSITE_INDEX,
            default_parameters=StrategyParameters(
                bb_period=20,
                bb_std=2,
                weight_sentiment=0.6
            ),
            parameter_constraints={
                "bb_period": {"min": 10, "max": 30, "step": 1},
                "bb_std": {"min": 1.5, "max": 3, "step": 0.1},
                "weight_sentiment": {"min": 0, "max": 1, "step": 0.1}
            },
            category="情绪策略",
            tags=["布林带", "复合", "波动"],
            is_system_template=True
        )

    @staticmethod
    def get_volatility_adjusted_template() -> CBSCStrategyTemplate:
        """波动率调整策略模板"""
        return CBSCStrategyTemplate(
            id="volatility_adjusted_template",
            name="波动率调整策略",
            description="成交量加权的情绪分析，考虑市场信心度",
            strategy_type=StrategyType.VOLATILITY_ADJUSTED,
            default_parameters=StrategyParameters(
                volatility_window=20,
                volume_weight=0.3
            ),
            parameter_constraints={
                "volatility_window": {"min": 10, "max": 40, "step": 1},
                "volume_weight": {"min": 0, "max": 1, "step": 0.1}
            },
            category="情绪策略",
            tags=["波动率", "成交量", "风险调整"],
            is_system_template=True
        )

    @classmethod
    def get_all_templates(cls) -> List[CBSCStrategyTemplate]:
        """获取所有模板"""
        return [
            cls.get_direct_rsi_template(),
            cls.get_sentiment_momentum_template(),
            cls.get_composite_index_template(),
            cls.get_volatility_adjusted_template()
        ]

if __name__ == "__main__":
    # 测试代码
    print("=== CBSC策略管理API模型测试 ===")

    # 测试策略创建
    strategy = Strategy(
        id="test_strategy_001",
        name="测试策略",
        description="这是一个测试策略",
        strategy_type=StrategyType.DIRECT_RSI,
        parameters=StrategyParameters(rsi_period=14, oversold_threshold=30, overbought_threshold=70),
        status=StrategyStatus.ACTIVE,
        is_active=True
    )
    print(f"策略创建成功: {strategy.name} ({strategy.id})")

    # 测试信号创建
    signal = StrategySignal(
        signal_id="test_signal_001",
        strategy_type=StrategyType.DIRECT_RSI,
        signal_type=SignalType.BUY,
        strength=85.5,
        confidence=92.3,
        timestamp=datetime.now(),
        market_data={"price": 150.0, "volume": 1000000},
        parameters=StrategyParameters(rsi_period=14),
        metadata={"source": "real_time"}
    )
    print(f"信号创建成功: {signal.signal_id} ({signal.signal_type})")

    # 测试模板
    templates = StrategyTemplates.get_all_templates()
    print(f"可用策略模板: {len(templates)}个")
    for template in templates:
        print(f"  - {template.name}: {template.description}")

    # 测试兼容性适配器
    legacy_strategy_data = {
        "id": "legacy_001",
        "name": "Legacy RSI Strategy",
        "strategy_type": "direct_rsi",
        "parameters": {"rsi_period": 10, "oversold_threshold": 25},
        "is_active": True
    }
    adapted_strategy = DataCompatibilityAdapter.adapt_legacy_strategy_format(legacy_strategy_data)
    print(f"适配策略成功: {adapted_strategy.name}")

    print("CBSC策略管理API模型测试完成！")
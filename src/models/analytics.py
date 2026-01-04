"""
分析報告模型

定義分析報告、回測結果、性能指標等相關的數據模型。
"""

from datetime import datetime, timezone, date
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB, NUMERIC
from pydantic import BaseModel, Field, validator
from decimal import Decimal
import enum

from .unified_base import UnifiedBaseModel, UnifiedSchema, StatusEnum

class ReportType(str, enum.Enum):
    """報告類型"""
    PERFORMANCE = "performance"
    RISK = "risk"
    COMPLIANCE = "compliance"
    AUDIT = "audit"
    BACKTEST = "backtest"
    STRATEGY = "strategy"
    PORTFOLIO = "portfolio"

class ReportFrequency(str, enum.Enum):
    """報告頻率"""
    REALTIME = "realtime"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    ADHOC = "adhoc"

class BacktestStatus(str, enum.Enum):
    """回測狀態"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AnalysisReport(UnifiedBaseModel):
    """分析報告模型"""

    __tablename__ = 'analysis_reports'

    # 基本信息標識
    title = Column(String(200), nullable=False)
    report_type = Column(String(50), nullable=False, index=True)
    frequency = Column(String(20), nullable=False, index=True)

    # 關聯信息
    user_id = Column(String(36), ForeignKey('users.id'), nullable=True)
    portfolio_id = Column(String(36), ForeignKey('portfolios.id'), nullable=True)
    strategy_id = Column(String(36), ForeignKey('strategies.id'), nullable=True)

    # 報告時間範圍
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    generated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # 報告狀態
    status = Column(String(20), default=StatusEnum.COMPLETED, nullable=False, index=True)
    is_published = Column(Boolean, default=False, nullable=False)
    is_template = Column(Boolean, default=False, nullable=False)

    # 報告內容
    summary = Column(Text, nullable=True)
    executive_summary = Column(Text, nullable=True)
    content = Column(JSONB, nullable=True)  # 結構化報告內容
    insights = Column(JSONB, nullable=True)  # 關鍵洞察
    recommendations = Column(JSONB, nullable=True)  # 建議

    # 數據質量和完整性
    data_quality_score = Column(Float, default=1.0, nullable=False)
    completeness_score = Column(Float, default=1.0, nullable=False)
    confidence_level = Column(Float, default=0.95, nullable=False)

    # 文件和輸出
    file_path = Column(String(500), nullable=True)
    file_format = Column(String(20), nullable=True)  # pdf, html, json, excel
    file_size = Column(Integer, nullable=True)

    # 共享和權限
    is_public = Column(Boolean, default=False, nullable=False)
    shared_with = Column(JSONB, nullable=True)  # 用戶ID列表
    access_count = Column(Integer, default=0, nullable=False)

    # 生成參數
    generation_parameters = Column(JSONB, nullable=True)
    template_version = Column(String(20), nullable=True)
    algorithm_version = Column(String(20), nullable=True)

    # 審計信息
    reviewed_by = Column(String(36), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    approved = Column(Boolean, nullable=True)
    approved_by = Column(String(36), nullable=True)
    approved_at = Column(DateTime, nullable=True)

    # 複合索引
    __table_args__ = (
        Index('idx_reports_type_period', 'report_type', 'period_start', 'period_end'),
        Index('idx_reports_user_date', 'user_id', 'generated_at'),
        Index('idx_reports_status_published', 'status', 'is_published'),
    )

class BacktestResult(UnifiedBaseModel):
    """回測結果模型"""

    __tablename__ = 'backtest_results'

    # 關聯信息
    strategy_id = Column(String(36), ForeignKey('strategies.id'), nullable=False)
    strategy_config_id = Column(String(36), ForeignKey('strategy_configs.id'), nullable=True)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=True)

    # 回測基本信息
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default=BacktestStatus.PENDING, nullable=False, index=True)

    # 回測參數
    initial_capital = Column(NUMERIC(20, 4), nullable=False)
    commission_rate = Column(Float, default=0.001, nullable=False)
    slippage_rate = Column(Float, default=0.0005, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    # 執行信息
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    execution_time_seconds = Column(Integer, nullable=True)
    data_points_processed = Column(Integer, nullable=True)

    # 性能指標 - 收益
    total_return = Column(Float, nullable=False)
    annualized_return = Column(Float, nullable=True)
    benchmark_return = Column(Float, nullable=True)
    alpha = Column(Float, nullable=True)
    cagr = Column(Float, nullable=True)  # 複合年增長率

    # 風險指標
    volatility = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    sortino_ratio = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    max_drawdown_duration = Column(Integer, nullable=True)  # 天數
    var_95 = Column(Float, nullable=True)
    cvar_95 = Column(Float, nullable=True)
    beta = Column(Float, nullable=True)

    # 交易統計
    total_trades = Column(Integer, default=0, nullable=False)
    winning_trades = Column(Integer, default=0, nullable=False)
    losing_trades = Column(Integer, default=0, nullable=False)
    win_rate = Column(Float, default=0.0, nullable=False)
    profit_factor = Column(Float, nullable=True)
    average_trade_return = Column(Float, nullable=True)
    average_win = Column(Float, nullable=True)
    average_loss = Column(Float, nullable=True)
    largest_win = Column(Float, nullable=True)
    largest_loss = Column(Float, nullable=True)

    # 持倉統計
    average_positions = Column(Float, nullable=True)
    max_positions = Column(Integer, nullable=True)
    turnover_rate = Column(Float, nullable=True)

    # 資金管理
    average_position_size = Column(Float, nullable=True)
    max_position_size = Column(Float, nullable=True)
    leverage_used = Column(Float, nullable=True)

    # 市場環境分析
    market_conditions = Column(JSONB, nullable=True)
    performance_by_market = Column(JSONB, nullable=True)  # 按市場狀況分類的表現
    sector_performance = Column(JSONB, nullable=True)  # 行業表現

    # 回測配置和參數
    strategy_parameters = Column(JSONB, nullable=True)
    data_configuration = Column(JSONB, nullable=True)
    execution_settings = Column(JSONB, nullable=True)

    # 結果文件
    result_data_path = Column(String(500), nullable=True)
    charts_path = Column(String(500), nullable=True)
    report_path = Column(String(500), nullable=True)

    # 驗證和質量
    validation_results = Column(JSONB, nullable=True)
    quality_score = Column(Float, default=1.0, nullable=False)
    is_statistically_significant = Column(Boolean, nullable=True)

    # 比較和基準
    benchmark_assets = Column(JSONB, nullable=True)  # 基準資產列表
    comparison_metrics = Column(JSONB, nullable=True)  # 比較指標

    # 複合索引
    __table_args__ = (
        Index('idx_backtest_strategy_date', 'strategy_id', 'start_date', 'end_date'),
        Index('idx_backtest_status_completed', 'status', 'completed_at'),
        Index('idx_backtest_return_sharpe', 'total_return', 'sharpe_ratio'),
    )

class PerformanceMetrics(UnifiedBaseModel):
    """性能指標模型"""

    __tablename__ = 'performance_metrics'

    # 關聯信息
    portfolio_id = Column(String(36), ForeignKey('portfolios.id'), nullable=True)
    strategy_id = Column(String(36), ForeignKey('strategies.id'), nullable=True)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=True)

    # 指標基本信息
    metric_type = Column(String(50), nullable=False, index=True)  # return, risk, trading, custom
    metric_name = Column(String(100), nullable=False, index=True)
    metric_category = Column(String(50), nullable=False, index=True)  # daily, weekly, monthly, ytd, all_time

    # 時間範圍
    calculation_date = Column(DateTime, nullable=False, index=True)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    # 指標值
    value = Column(Float, nullable=False)
    benchmark_value = Column(Float, nullable=True)
    percentile_rank = Column(Float, nullable=True)  # 在所有投資組合中的百分位排名

    # 統計信息
    sample_size = Column(Integer, nullable=True)
    confidence_interval_lower = Column(Float, nullable=True)
    confidence_interval_upper = Column(Float, nullable=True)
    standard_error = Column(Float, nullable=True)

    # 計算參數
    calculation_method = Column(String(100), nullable=True)
    parameters = Column(JSONB, nullable=True)
    data_quality_score = Column(Float, default=1.0, nullable=False)

    # 比較分析
    yoy_change = Column(Float, nullable=True)  # 同比變化
    mom_change = Column(Float, nullable=True)  # 環比變化
    rolling_30d_avg = Column(Float, nullable=True)
    rolling_90d_avg = Column(Float, nullable=True)

    # 複合索引
    __table_args__ = (
        Index('idx_metrics_portfolio_type_date', 'portfolio_id', 'metric_type', 'calculation_date'),
        Index('idx_metrics_strategy_type_date', 'strategy_id', 'metric_type', 'calculation_date'),
        Index('idx_metrics_name_category_date', 'metric_name', 'metric_category', 'calculation_date'),
    )

# Pydantic Schemas
class AnalysisReportBaseSchema(UnifiedSchema):
    """分析報告基礎Schema"""
    title: str = Field(..., min_length=1, max_length=200, description="報告標題")
    report_type: ReportType = Field(..., description="報告類型")
    frequency: ReportFrequency = Field(..., description="報告頻率")
    period_start: datetime
    period_end: datetime
    summary: Optional[str] = Field(None, description="報告摘要")

class AnalysisReportCreateSchema(AnalysisReportBaseSchema):
    """創建分析報告Schema"""
    portfolio_id: Optional[str] = None
    strategy_id: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    insights: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None

class AnalysisReportResponseSchema(AnalysisReportBaseSchema):
    """分析報告響應Schema"""
    user_id: Optional[str] = None
    portfolio_id: Optional[str] = None
    strategy_id: Optional[str] = None
    generated_at: datetime
    status: str
    is_published: bool
    is_template: bool
    executive_summary: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    insights: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None
    data_quality_score: float
    file_format: Optional[str] = None
    is_public: bool
    access_count: int

    class Config:
        from_attributes = True

class BacktestResultBaseSchema(UnifiedSchema):
    """回測結果基礎Schema"""
    name: str = Field(..., min_length=1, max_length=200, description="回測名稱")
    description: Optional[str] = None
    strategy_id: str
    initial_capital: Decimal = Field(..., gt=0, description="初始資本")
    start_date: datetime
    end_date: datetime

class BacktestResultCreateSchema(BacktestResultBaseSchema):
    """創建回測Schema"""
    strategy_config_id: Optional[str] = None
    commission_rate: float = Field(0.001, ge=0, description="佣金率")
    slippage_rate: float = Field(0.0005, ge=0, description="滑點率")
    strategy_parameters: Optional[Dict[str, Any]] = None

class BacktestResultResponseSchema(BacktestResultBaseSchema):
    """回測結果響應Schema"""
    strategy_config_id: Optional[str] = None
    status: BacktestStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time_seconds: Optional[int] = None
    total_return: float
    annualized_return: Optional[float] = None
    benchmark_return: Optional[float] = None
    alpha: Optional[float] = None
    volatility: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    total_trades: int
    win_rate: float
    profit_factor: Optional[float] = None
    strategy_name: Optional[str] = None

    class Config:
        from_attributes = True

class PerformanceMetricsBaseSchema(UnifiedSchema):
    """性能指標基礎Schema"""
    metric_type: str = Field(..., description="指標類型")
    metric_name: str = Field(..., description="指標名稱")
    metric_category: str = Field(..., description="指標分類")
    calculation_date: datetime
    period_start: datetime
    period_end: datetime
    value: float

class PerformanceMetricsResponseSchema(PerformanceMetricsBaseSchema):
    """性能指標響應Schema"""
    portfolio_id: Optional[str] = None
    strategy_id: Optional[str] = None
    benchmark_value: Optional[float] = None
    percentile_rank: Optional[float] = None
    sample_size: Optional[int] = None
    confidence_interval_lower: Optional[float] = None
    confidence_interval_upper: Optional[float] = None
    calculation_method: Optional[str] = None
    yoy_change: Optional[float] = None
    mom_change: Optional[float] = None
    rolling_30d_avg: Optional[float] = None

    class Config:
        from_attributes = True
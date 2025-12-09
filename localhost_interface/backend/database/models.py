#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
數據庫模型
Phase 4: 參數優化系統的數據庫模型定義
"""

from datetime import datetime, date
from typing import Dict, List, Any, Optional
from enum import Enum
import json

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, Boolean,
    ForeignKey, JSON, Numeric, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel, Field, validator
import uuid

Base = declarative_base()

# === 枚舉定義 ===

class OptimizationStatusEnum(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class UserRoleEnum(str, Enum):
    ADMIN = "admin"
    TRADER = "trader"
    ANALYST = "analyst"
    GUEST = "guest"

class SamplingMethodEnum(str, Enum):
    GRID_SEARCH = "grid_search"
    RANDOM_SEARCH = "random_search"
    BAYESIAN = "bayesian"
    GENETIC = "genetic"
    SMART_SAMPLING = "smart_sampling"

class GPUBackendEnum(str, Enum):
    CUDA = "cuda"
    CUPY = "cupy"
    NUMBA = "numba"
    MOCK = "mock"

# === SQLAlchemy模型 ===

class User(Base):
    """用戶模型"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default=UserRoleEnum.TRADER.value)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # 時間戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)

    # 用戶設置
    preferences = Column(JSON, default={})
    permissions = Column(JSON, default=[])

    # 關聯關係
    optimizations = relationship("OptimizationRequest", back_populates="user")
    sessions = relationship("UserSession", back_populates="user")

    def __repr__(self):
        return f"<User(username='{self.username}', role='{self.role}')>"

class UserSession(Base):
    """用戶會話模型"""
    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)

    # 會話信息
    ip_address = Column(String(45))
    user_agent = Column(Text)
    device_info = Column(JSON)

    # 時間戳
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow)

    # 關聯關係
    user = relationship("User", back_populates="sessions")

    def __repr__(self):
        return f"<UserSession(user_id='{self.user_id}', expires_at='{self.expires_at}')>"

class OptimizationRequest(Base):
    """參數優化請求模型"""
    __tablename__ = "optimization_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(String(100), unique=True, nullable=False, index=True)

    # 用戶信息
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # 優化基本信息
    symbol = Column(String(20), nullable=False, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    description = Column(Text)
    tags = Column(JSON, default=[])
    priority = Column(Integer, default=1)

    # 優化配置
    objective = Column(String(50), nullable=False)
    secondary_objectives = Column(JSON, default=[])
    max_combinations = Column(Integer, default=1000)
    sampling_method = Column(String(50), default=SamplingMethodEnum.SMART_SAMPLING.value)
    n_samples = Column(Integer, default=200)

    # GPU配置
    enable_gpu = Column(Boolean, default=True)
    gpu_backend = Column(String(20), default=GPUBackendEnum.CUDA.value)
    gpu_device = Column(Integer, default=0)

    # 回測配置
    initial_capital = Column(Numeric(20, 2), default=1000000)
    commission = Column(Numeric(10, 6), default=0.001)
    slippage = Column(Numeric(10, 6), default=0.0001)
    benchmark_symbol = Column(String(20), default="HSI.HK")

    # 交叉驗證配置
    enable_cross_validation = Column(Boolean, default=True)
    cv_folds = Column(Integer, default=5)

    # 並行配置
    max_workers = Column(Integer, default=4)
    chunk_size = Column(Integer, default=100)

    # 參數範圍配置（JSON格式）
    parameter_ranges = Column(JSON, nullable=False)

    # 狀態和時間戳
    status = Column(String(20), default=OptimizationStatusEnum.PENDING.value, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    execution_time = Column(Float)  # 秒

    # 統計信息
    total_combinations = Column(Integer, default=0)
    evaluated_combinations = Column(Integer, default=0)
    failed_combinations = Column(Integer, default=0)

    # 最佳結果ID
    best_result_id = Column(UUID(as_uuid=True), ForeignKey("optimization_results.id"))

    # 文件路徑
    results_file = Column(String(500))
    log_file = Column(String(500))

    # 系統性能
    gpu_utilization = Column(Float)
    memory_usage = Column(Float)
    avg_combination_time = Column(Float)

    # 關聯關係
    user = relationship("User", back_populates="optimizations")
    best_result = relationship("OptimizationResult", foreign_keys=[best_result_id])
    results = relationship("OptimizationResult", back_populates="request", foreign_keys="OptimizationResult.request_id")

    # 索引
    __table_args__ = (
        Index('idx_optimization_symbol_status', 'symbol', 'status'),
        Index('idx_optimization_user_created', 'user_id', 'created_at'),
    )

    def __repr__(self):
        return f"<OptimizationRequest(id='{self.request_id}', symbol='{self.symbol}', status='{self.status}')>"

class OptimizationResult(Base):
    """參數優化結果模型"""
    __tablename__ = "optimization_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    combination_id = Column(String(50), nullable=False, index=True)

    # 關聯的優化請求
    request_id = Column(UUID(as_uuid=True), ForeignKey("optimization_requests.id"), nullable=False, index=True)

    # 參數組合
    rsi_period = Column(Integer, nullable=False)
    rsi_oversold = Column(Float, nullable=False)
    rsi_overbought = Column(Float, nullable=False)
    rsi_weight = Column(Float, nullable=False)

    macd_fast = Column(Integer, nullable=False)
    macd_slow = Column(Integer, nullable=False)
    macd_signal = Column(Integer, nullable=False)
    macd_weight = Column(Float, nullable=False)

    bb_period = Column(Integer, nullable=False)
    bb_std = Column(Float, nullable=False)
    bb_weight = Column(Float, nullable=False)

    # 性能指標
    sharpe_ratio = Column(Float, nullable=False, index=True)
    sortino_ratio = Column(Float)
    max_drawdown = Column(Float, nullable=False)
    total_return = Column(Float, nullable=False, index=True)
    annualized_return = Column(Float)
    profit_factor = Column(Float)
    win_rate = Column(Float)
    total_trades = Column(Integer)

    # 執行信息
    execution_time = Column(Float)  # 秒
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # 詳細性能數據（JSON格式）
    detailed_metrics = Column(JSON)
    equity_curve = Column(JSON)  # 資產曲線數據
    trade_records = Column(JSON)  # 交易記錄

    # 關聯關係
    request = relationship("OptimizationRequest", back_populates="results", foreign_keys=[request_id])

    # 索引
    __table_args__ = (
        Index('idx_result_request_sharpe', 'request_id', 'sharpe_ratio'),
        Index('idx_result_combination_unique', 'request_id', 'combination_id', unique=True),
    )

    def __repr__(self):
        return f"<OptimizationResult(combination_id='{self.combination_id}', sharpe={self.sharpe_ratio:.3f})>"

class ParameterSensitivity(Base):
    """參數敏感性分析結果"""
    __tablename__ = "parameter_sensitivity"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 關聯的優化請求
    request_id = Column(UUID(as_uuid=True), ForeignKey("optimization_requests.id"), nullable=False, index=True)

    # 參數名稱和敏感性分析
    parameter_name = Column(String(50), nullable=False)
    sensitivity_score = Column(Float, nullable=False)

    # 敏感性數據（JSON格式）
    parameter_values = Column(JSON)  # 參數值列表
    performance_values = Column(JSON)  # 對應的性能值列表
    correlation_coefficient = Column(Float)

    # 分析結果
    optimal_value = Column(Float)
    optimal_range = Column(JSON)  # [min, max]

    # 時間戳
    created_at = Column(DateTime, default=datetime.utcnow)

    # 關聯關係
    request = relationship("OptimizationRequest")

class BestParameters(Base):
    """最佳參數記錄"""
    __tablename__ = "best_parameters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 符號和目標
    symbol = Column(String(20), nullable=False, index=True)
    objective = Column(String(50), nullable=False, index=True)

    # 最佳參數
    best_sharpe_ratio = Column(Float, nullable=False)
    parameters = Column(JSON, nullable=False)  # 完整的參數組合
    performance_metrics = Column(JSON)  # 完整的性能指標

    # 來源信息
    source_request_id = Column(UUID(as_uuid=True), ForeignKey("optimization_requests.id"))
    updated_at = Column(DateTime, default=datetime.utcnow)

    # 關聯關係
    source_request = relationship("OptimizationRequest")

    # 唯一約束
    __table_args__ = (
        UniqueConstraint('symbol', 'objective', name='uq_best_parameters_symbol_objective'),
    )

    def __repr__(self):
        return f"<BestParameters(symbol='{self.symbol}', objective='{self.objective}', sharpe={self.best_sharpe_ratio:.3f})>"

class OptimizationHistory(Base):
    """優化歷史記錄"""
    __tablename__ = "optimization_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 基本信息記錄
    request_id = Column(String(100), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    status = Column(String(20), nullable=False)

    # 時間記錄
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # 結果摘要
    total_combinations = Column(Integer)
    best_sharpe_ratio = Column(Float)
    best_total_return = Column(Float)
    execution_time = Column(Float)

    # 系統信息
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    worker_id = Column(String(50))

    # 關聯關係
    user = relationship("User")

class SystemMetrics(Base):
    """系統性能指標"""
    __tablename__ = "system_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 時間戳
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # 系統資源
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    disk_usage = Column(Float)
    gpu_usage = Column(Float)
    gpu_memory_usage = Column(Float)

    # 應用程序指標
    active_optimizations = Column(Integer)
    active_websocket_connections = Column(Integer)
    queue_length = Column(Integer)
    avg_response_time = Column(Float)

    # 錯誤統計
    error_rate = Column(Float)
    error_count = Column(Integer)

    # 數據庫性能
    db_connections = Column(Integer)
    db_query_time = Column(Float)

class AuditLog(Base):
    """審計日誌"""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 用戶和操作
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(100))

    # 詳細信息
    description = Column(Text)
    ip_address = Column(String(45))
    user_agent = Column(Text)

    # 请求和响应数据
    request_data = Column(JSON)
    response_data = Column(JSON)

    # 結果
    success = Column(Boolean, default=True)
    error_message = Column(Text)

    # 時間戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # 關聯關係
    user = relationship("User")

# === Pydantic模型 ===

class UserCreate(BaseModel):
    """創建用戶請求"""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    full_name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=8)
    role: UserRoleEnum = UserRoleEnum.TRADER

class UserResponse(BaseModel):
    """用戶響應"""
    id: str
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    permissions: List[str]

    class Config:
        from_attributes = True

class OptimizationRequestCreate(BaseModel):
    """創建優化請求"""
    symbol: str = Field(default="0700.HK")
    start_date: date
    end_date: date
    description: Optional[str] = None
    tags: List[str] = []
    priority: int = Field(default=1, ge=1, le=10)
    objective: str = Field(default="sharpe_ratio")
    secondary_objectives: List[str] = []
    max_combinations: int = Field(default=1000, ge=1, le=100000)
    sampling_method: SamplingMethodEnum = SamplingMethodEnum.SMART_SAMPLING
    n_samples: int = Field(default=200, ge=10, le=10000)
    enable_gpu: bool = Field(default=True)
    gpu_backend: GPUBackendEnum = GPUBackendEnum.CUDA
    gpu_device: int = Field(default=0, ge=0, le=7)
    initial_capital: float = Field(default=1000000, gt=0)
    commission: float = Field(default=0.001, ge=0)
    slippage: float = Field(default=0.0001, ge=0)
    benchmark_symbol: str = Field(default="HSI.HK")
    enable_cross_validation: bool = Field(default=True)
    cv_folds: int = Field(default=5, ge=2, le=10)
    max_workers: int = Field(default=4, ge=1, le=32)
    chunk_size: int = Field(default=100, ge=10, le=1000)
    parameter_ranges: Dict[str, Any]

    @validator('end_date')
    def validate_date_range(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v

class OptimizationRequestResponse(BaseModel):
    """優化請求響應"""
    id: str
    request_id: str
    symbol: str
    start_date: date
    end_date: date
    description: Optional[str]
    status: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    execution_time: Optional[float]
    total_combinations: int
    evaluated_combinations: int
    best_sharpe_ratio: Optional[float]

    class Config:
        from_attributes = True

class OptimizationResultResponse(BaseModel):
    """優化結果響應"""
    id: str
    combination_id: str
    request_id: str
    parameters: Dict[str, Any]
    sharpe_ratio: float
    sortino_ratio: Optional[float]
    max_drawdown: float
    total_return: float
    annualized_return: Optional[float]
    profit_factor: Optional[float]
    win_rate: Optional[float]
    total_trades: Optional[int]
    execution_time: Optional[float]
    timestamp: datetime

    class Config:
        from_attributes = True

class BestParametersResponse(BaseModel):
    """最佳參數響應"""
    symbol: str
    objective: str
    best_sharpe_ratio: float
    parameters: Dict[str, Any]
    performance_metrics: Optional[Dict[str, Any]]
    updated_at: datetime

    class Config:
        from_attributes = True

class SystemMetricsResponse(BaseModel):
    """系統指標響應"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    active_optimizations: int
    active_websocket_connections: int
    queue_length: int
    avg_response_time: float

    class Config:
        from_attributes = True

# === 數據庫操作輔助函數 ===

async def create_user(db: Session, user_data: UserCreate, hashed_password: str) -> User:
    """創建用戶"""
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        role=user_data.role.value,
        permissions=_get_default_permissions(user_data.role)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def _get_default_permissions(role: UserRoleEnum) -> List[str]:
    """獲取角色默認權限"""
    permission_map = {
        UserRoleEnum.ADMIN: ["*"],
        UserRoleEnum.TRADER: ["backtest", "read", "optimize"],
        UserRoleEnum.ANALYST: ["read", "analyze"],
        UserRoleEnum.GUEST: ["read"]
    }
    return permission_map.get(role, ["read"])

async def create_optimization_request(
    db: Session,
    request_data: OptimizationRequestCreate,
    user_id: str,
    request_id: str
) -> OptimizationRequest:
    """創建優化請求"""
    db_request = OptimizationRequest(
        request_id=request_id,
        user_id=user_id,
        symbol=request_data.symbol,
        start_date=request_data.start_date,
        end_date=request_data.end_date,
        description=request_data.description,
        tags=request_data.tags,
        priority=request_data.priority,
        objective=request_data.objective,
        secondary_objectives=request_data.secondary_objectives,
        max_combinations=request_data.max_combinations,
        sampling_method=request_data.sampling_method.value,
        n_samples=request_data.n_samples,
        enable_gpu=request_data.enable_gpu,
        gpu_backend=request_data.gpu_backend.value,
        gpu_device=request_data.gpu_device,
        initial_capital=request_data.initial_capital,
        commission=request_data.commission,
        slippage=request_data.slippage,
        benchmark_symbol=request_data.benchmark_symbol,
        enable_cross_validation=request_data.enable_cross_validation,
        cv_folds=request_data.cv_folds,
        max_workers=request_data.max_workers,
        chunk_size=request_data.chunk_size,
        parameter_ranges=request_data.parameter_ranges
    )
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request

async def save_optimization_result(
    db: Session,
    request_id: str,
    result_data: Dict[str, Any]
) -> OptimizationResult:
    """保存優化結果"""
    db_result = OptimizationResult(
        request_id=request_id,
        **result_data
    )
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    return db_result

async def update_best_parameters(
    db: Session,
    symbol: str,
    objective: str,
    sharpe_ratio: float,
    parameters: Dict[str, Any],
    performance_metrics: Optional[Dict[str, Any]] = None,
    source_request_id: Optional[str] = None
) -> BestParameters:
    """更新最佳參數記錄"""
    # 使用UPSERT邏輯
    existing = db.query(BestParameters).filter(
        BestParameters.symbol == symbol,
        BestParameters.objective == objective
    ).first()

    if existing and sharpe_ratio > existing.best_sharpe_ratio:
        # 更新現有記錄
        existing.best_sharpe_ratio = sharpe_ratio
        existing.parameters = parameters
        existing.performance_metrics = performance_metrics
        existing.source_request_id = source_request_id
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    elif not existing:
        # 創建新記錄
        db_best = BestParameters(
            symbol=symbol,
            objective=objective,
            best_sharpe_ratio=sharpe_ratio,
            parameters=parameters,
            performance_metrics=performance_metrics,
            source_request_id=source_request_id
        )
        db.add(db_best)
        db.commit()
        db.refresh(db_best)
        return db_best
    else:
        return existing

async def log_audit_event(
    db: Session,
    user_id: Optional[str],
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    description: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    request_data: Optional[Dict[str, Any]] = None,
    response_data: Optional[Dict[str, Any]] = None,
    success: bool = True,
    error_message: Optional[str] = None
):
    """記錄審計日誌"""
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
        request_data=request_data,
        response_data=response_data,
        success=success,
        error_message=error_message
    )
    db.add(audit_log)
    db.commit()
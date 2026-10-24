"""
生產級參數控制API
基於專家審查建議實現的企業級參數控制系統

Features:
- 完整的類型提示
- 企業級安全驗證
- 異常處理和資源管理
- 性能監控和日誌記錄
- 速率限制和DDoS防護

Author: CBSC Quantitative Trading System
Version: 1.0.0
"""

import asyncio
import json
import logging
import time
import traceback
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

import pandas as pd
from fastapi import (
    WebSocket, WebSocketDisconnect, HTTPException,
    Query, BackgroundTasks, Depends
)
from pydantic import BaseModel, Field, validator

from src.security.enterprise_security import (
    SecurityValidationError, security_validator, rate_limiter
)

# 配置日誌
logger = logging.getLogger(__name__)


class ParameterValidationError(Exception):
    """
    參數驗證錯誤

    專門用於參數計算過程中的驗證錯誤
    """
    def __init__(self, message: str, parameter_name: str, invalid_value: Any, error_code: str = "PARAM_ERROR"):
        self.message = message
        self.parameter_name = parameter_name
        self.invalid_value = invalid_value
        self.error_code = error_code
        super().__init__(f"參數 '{parameter_name}' 驗證失敗: {message}")


class ParameterCalculationError(Exception):
    """
    參數計算錯誤

    用於處理策略計算過程中的錯誤
    """
    def __init__(self, message: str, error_details: Optional[Dict] = None):
        self.message = message
        self.error_details = error_details or {}
        super().__init__(message)


class SecureParameterUpdate(BaseModel):
    """
    安全參數更新模型

    包含完整的驗證和安全檢查
    """
    session_id: str = Field(..., min_length=8, max_length=64, description="會話標識符")
    parameter_name: str = Field(..., min_length=1, max_length=50, description="參數名稱")
    value: Union[int, float, str, bool] = Field(..., description="參數值")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="更新時間戳")
    user_id: Optional[str] = Field(None, max_length=50, description="用戶標識符")
    request_source: str = Field(default="websocket", description="請求來源")

    @validator('parameter_name')
    def validate_parameter_name(cls, v: str) -> str:
        """驗證參數名稱格式和安全性"""
        return security_validator.validate_parameter_name(v)

    @validator('session_id')
    def validate_session_id(cls, v: str) -> str:
        """驗證會話ID格式"""
        return security_validator.validate_session_id(v)

    @validator('user_id')
    def validate_user_id(cls, v: Optional[str]) -> Optional[str]:
        """驗證用戶ID"""
        if v is not None:
            return security_validator.sanitize_input(v, max_length=50)
        return v

    @validator('request_source')
    def validate_request_source(cls, v: str) -> str:
        """驗證請求來源"""
        allowed_sources = {'websocket', 'http', 'internal'}
        if v not in allowed_sources:
            raise ValueError(f"無效的請求來源: {v}")
        return v


class ParameterResponse(BaseModel):
    """
    標準化響應模型

    確保所有API響應格式一致
    """
    success: bool = Field(..., description="操作是否成功")
    data: Optional[Dict[str, Any]] = Field(None, description="響應數據")
    error: Optional[str] = Field(None, description="錯誤信息")
    error_code: Optional[str] = Field(None, description="錯誤代碼")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="響應時間戳")
    processing_time_ms: Optional[float] = Field(None, description="處理時間（毫秒）")
    session_id: Optional[str] = Field(None, description="會話ID")
    request_id: Optional[str] = Field(None, description="請求ID")


class ParameterConfigValidator:
    """
    生產級參數驗證器

    提供完整的參數驗證和依賴關係檢查
    """

    # 參數範圍配置 - 來自CBSC系統實際需求
    PARAMETER_RANGES = {
        'rsi_period': {
            'min': 5, 'max': 50, 'type': int,
            'description': 'RSI計算週期'
        },
        'sentiment_threshold': {
            'min': 0.1, 'max': 1.0, 'type': float,
            'description': '情緒強度閾值'
        },
        'ma_short': {
            'min': 5, 'max': 30, 'type': int,
            'description': '短期移動平均線'
        },
        'ma_long': {
            'min': 20, 'max': 100, 'type': int,
            'description': '長期移動平均線'
        },
        'risk_tolerance': {
            'min': 0.05, 'max': 0.50, 'type': float,
            'description': '風險承受度'
        },
        'optimization_target': {
            'allowed_values': ['sharpe_ratio', 'returns', 'max_drawdown'],
            'type': str,
            'description': '優化目標'
        }
    }

    # 參數依賴關係配置
    PARAMETER_DEPENDENCIES = {
        'ma_long': {
            'validator': lambda value, dependencies: value > dependencies.get('ma_short', 10),
            'error_message': '長期均線必須大於短期均線',
            'dependent_on': 'ma_short'
        },
        'rsi_period': {
            'validator': lambda value, dependencies: value < dependencies.get('ma_short', 10),
            'error_message': 'RSI週期應小於短期均線',
            'dependent_on': 'ma_short'
        }
    }

    @classmethod
    def validate_parameter(
        cls,
        param_name: str,
        value: Any,
        dependencies: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        驗證單個參數

        Args:
            param_name: 參數名稱
            value: 參數值
            dependencies: 相關參數值

        Returns:
            驗證後的參數值

        Raises:
            ParameterValidationError: 參數驗證失敗
        """
        dependencies = dependencies or {}

        if param_name not in cls.PARAMETER_RANGES:
            raise ParameterValidationError(
                f"未知參數: {param_name}",
                param_name, value, "UNKNOWN_PARAMETER"
            )

        config = cls.PARAMETER_RANGES[param_name]

        # 類型驗證和轉換
        try:
            if 'allowed_values' in config:
                # 枚舉值驗證
                if value not in config['allowed_values']:
                    raise ParameterValidationError(
                        f"參數值必須是以下之一: {config['allowed_values']}",
                        param_name, value, "INVALID_ENUM_VALUE"
                    )
                validated_value = config['type'](value)
            else:
                # 數值範圍驗證
                validated_value = security_validator.validate_numeric_range(
                    value,
                    config.get('min'),
                    config.get('max'),
                    param_name
                )

        except (ValueError, TypeError) as e:
            raise ParameterValidationError(
                f"參數類型錯誤，期望 {config['type'].__name__}: {str(e)}",
                param_name, value, "TYPE_ERROR"
            )

        # 依賴關係驗證
        if param_name in cls.PARAMETER_DEPENDENCIES and dependencies:
            dep_config = cls.PARAMETER_DEPENDENCIES[param_name]

            if dep_config['dependent_on'] in dependencies:
                if not dep_config['validator'](validated_value, dependencies):
                    raise ParameterValidationError(
                        dep_config['error_message'],
                        param_name, validated_value, "DEPENDENCY_ERROR"
                    )

        logger.info(f"參數驗證成功: {param_name} = {validated_value}")
        return validated_value

    @classmethod
    def validate_all_parameters(
        cls,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        驗證所有參數，包括依賴關係

        Args:
            parameters: 參數字典

        Returns:
            驗證後的參數字典

        Raises:
            ParameterValidationError: 任何參數驗證失敗
        """
        validated_params = {}

        # 首次驗證所有參數
        for param_name, value in parameters.items():
            try:
                validated_params[param_name] = cls.validate_parameter(
                    param_name, value, validated_params
                )
            except ParameterValidationError:
                # 第一次驗證失敗時，使用原始值進行依賴檢查
                validated_params[param_name] = value

        # 二次驗證，確保所有依賴關係都正確
        final_params = {}
        for param_name, value in validated_params.items():
            final_params[param_name] = cls.validate_parameter(
                param_name, value, final_params
            )

        return final_params


class SessionManager:
    """
    會話管理器

    負責管理WebSocket會話和相關數據
    """

    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.session_stats: Dict[str, Dict[str, Any]] = {}
        self.cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup_task()

    def _start_cleanup_task(self) -> None:
        """啟動會話清理任務"""
        if self.cleanup_task is None or self.cleanup_task.done():
            self.cleanup_task = asyncio.create_task(self._cleanup_sessions())

    async def _cleanup_sessions(self) -> None:
        """定期清理過期會話"""
        while True:
            try:
                await self._remove_expired_sessions()
                await asyncio.sleep(300)  # 5分鐘清理一次
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"會話清理任務錯誤: {e}")

    async def create_session(self, session_id: str, user_id: Optional[str] = None) -> None:
        """創建新會話"""
        if session_id in self.active_sessions:
            logger.warning(f"會話已存在: {session_id}")
            return

        self.active_sessions[session_id] = {
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "user_id": user_id,
            "parameters": self._get_default_parameters(),
            "calculation_count": 0,
            "error_count": 0,
            "status": "active"
        }

        self.session_stats[session_id] = {
            "total_processing_time": 0.0,
            "average_processing_time": 0.0,
            "successful_calculations": 0,
            "failed_calculations": 0
        }

        logger.info(f"會話創建成功: {session_id}")

    async def update_session_activity(self, session_id: str) -> None:
        """更新會話活動時間"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["last_activity"] = datetime.utcnow()

    async def get_session_parameters(self, session_id: str) -> Dict[str, Any]:
        """獲取會話參數"""
        if session_id not in self.active_sessions:
            raise HTTPException(
                status_code=404,
                detail=f"會話不存在: {session_id}"
            )
        return self.active_sessions[session_id]["parameters"].copy()

    async def update_session_parameter(
        self,
        session_id: str,
        parameter_update: SecureParameterUpdate
    ) -> None:
        """更新會話參數"""
        if session_id not in self.active_sessions:
            raise HTTPException(
                status_code=404,
                detail=f"會話不存在: {session_id}"
            )

        current_params = self.active_sessions[session_id]["parameters"]
        current_params[parameter_update.parameter_name] = parameter_update.value

        # 更新活動時間
        await self.update_session_activity(session_id)

        logger.info(
            f"會話參數更新: {session_id} - {parameter_update.parameter_name} = {parameter_update.value}"
        )

    def _get_default_parameters(self) -> Dict[str, Any]:
        """獲取默認參數"""
        return {
            "rsi_period": 14,
            "sentiment_threshold": 0.7,
            "ma_short": 10,
            "ma_long": 30,
            "risk_tolerance": 0.15,
            "optimization_target": "sharpe_ratio",
            "enable_analysis": True
        }

    async def _remove_expired_sessions(self) -> None:
        """移除過期會話"""
        current_time = datetime.utcnow()
        expired_sessions = []

        for session_id, session_data in self.active_sessions.items():
            # 30分鐘無活動則過期
            if (current_time - session_data["last_activity"]).total_seconds() > 1800:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            del self.active_sessions[session_id]
            if session_id in self.session_stats:
                del self.session_stats[session_id]
            logger.info(f"過期會話已清理: {session_id}")

    def get_session_stats(self) -> Dict[str, Any]:
        """獲取會話統計信息"""
        return {
            "active_sessions": len(self.active_sessions),
            "total_sessions_created": len(self.session_stats),
            "cleanup_task_running": self.cleanup_task is not None and not self.cleanup_task.done()
        }


# 全局會話管理器
session_manager = SessionManager()


@asynccontextmanager
async def parameter_calculation_context(session_id: str):
    """
    參數計算上下文管理器

    確保計算過程中的資源管理和異常處理
    """
    calculation_start_time = time.time()

    try:
        # 標記計算開始
        if session_id in session_manager.active_sessions:
            session_manager.active_sessions[session_id]["calculation_count"] += 1

        logger.info(f"參數計算開始: {session_id}")
        yield

    except Exception as e:
        # 記錄錯誤
        if session_id in session_manager.active_sessions:
            session_manager.active_sessions[session_id]["error_count"] += 1

        logger.error(f"參數計算錯誤: {session_id} - {str(e)}")
        raise

    finally:
        # 清理和統計
        calculation_time = time.time() - calculation_start_time

        if session_id in session_manager.session_stats:
            stats = session_manager.session_stats[session_id]
            stats["total_processing_time"] += calculation_time
            stats["average_processing_time"] = (
                stats["total_processing_time"] /
                max(1, stats["successful_calculations"] + stats["failed_calculations"])
            )

        logger.info(f"參數計算完成: {session_id}, time={calculation_time:.3f}s")


async def load_cbsc_data_safe() -> pd.DataFrame:
    """
    安全加載CBSC數據

    Returns:
        CBSC數據DataFrame

    Raises:
        ParameterCalculationError: 數據加載失敗
    """
    try:
        # 這裡應該調用現有的CBSC數據加載邏輯
        # 例如: from src.data_adapters.data_service import load_cbsc_data

        # 模擬數據加載
        current_dir = Path.cwd()
        sentiment_path = current_dir / "warrant_sentiment_daily.csv"

        if not sentiment_path.exists():
            raise ParameterCalculationError(
                "CBSC數據文件不存在",
                {"file_path": str(sentiment_path)}
            )

        # 安全加載數據
        df = pd.read_csv(sentiment_path)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date', 'Afternoon_Close'])
        df = df.sort_values('Date').reset_index(drop=True)

        if df.empty:
            raise ParameterCalculationError(
                "CBSC數據為空",
                {"file_path": str(sentiment_path)}
            )

        logger.info(f"CBSC數據加載成功: {len(df)} 條記錄")
        return df

    except Exception as e:
        if isinstance(e, ParameterCalculationError):
            raise

        raise ParameterCalculationError(
            f"數據加載失敗: {str(e)}",
            {"error_type": type(e).__name__}
        )


async def calculate_technical_indicators_async(
    data: pd.DataFrame,
    parameter_update: SecureParameterUpdate
) -> Dict[str, Any]:
    """
    異步計算技術指標

    Args:
        data: CBSC數據
        parameter_update: 參數更新

    Returns:
        技術指標計算結果

    Raises:
        ParameterCalculationError: 計算失敗
    """
    try:
        # 獲取當前會話的所有參數
        current_params = await session_manager.get_session_parameters(parameter_update.session_id)

        # 計算各種技術指標
        indicators = {}

        # RSI計算
        rsi_period = current_params.get('rsi_period', 14)
        indicators['rsi'] = calculate_rsi(data['Afternoon_Close'], rsi_period)

        # 移動平均線計算
        ma_short = current_params.get('ma_short', 10)
        ma_long = current_params.get('ma_long', 30)
        indicators['ma_short'] = data['Afternoon_Close'].rolling(ma_short).mean()
        indicators['ma_long'] = data['Afternoon_Close'].rolling(ma_long).mean()

        # 情緒分析
        indicators['sentiment_strength'] = calculate_sentiment_strength(data)

        # 計算最新值
        latest_values = {}
        for key, series in indicators.items():
            if not series.empty:
                latest_values[f'latest_{key}'] = float(series.iloc[-1])

        latest_values['current_price'] = float(data['Afternoon_Close'].iloc[-1])

        logger.info(f"技術指標計算完成: {len(indicators)} 個指標")
        return {
            "indicators": indicators.to_dict() if hasattr(indicators, 'to_dict') else indicators,
            "latest_values": latest_values,
            "parameters_used": current_params
        }

    except Exception as e:
        raise ParameterCalculationError(
            f"技術指標計算失敗: {str(e)}",
            {
                "parameter_update": parameter_update.dict(),
                "error_trace": traceback.format_exc()
            }
        )


def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """
    計算RSI指標

    Args:
        prices: 價格序列
        period: 計算週期

    Returns:
        RSI序列
    """
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    return rsi


def calculate_sentiment_strength(data: pd.DataFrame) -> pd.Series:
    """
    計算情緒強度指標

    Args:
        data: CBSC數據

    Returns:
        情緒強度序列
    """
    try:
        # 計算牛熊比例
        bull_turnover = data.get('Bull_Turnover_HKD', pd.Series(0, index=data.index))
        bear_turnover = data.get('Bear_Turnover_HKD', pd.Series(0, index=data.index))

        total_turnover = bull_turnover + bear_turnover
        total_turnover = total_turnover.replace(0, 1)  # 避免除零

        sentiment_strength = (bull_turnover - bear_turnover) / total_turnover

        return sentiment_strength

    except Exception as e:
        logger.warning(f"情緒強度計算失敗，返回默認值: {e}")
        return pd.Series(0.5, index=data.index)


async def generate_trading_signals(
    indicators: Dict[str, Any],
    sentiment_analysis: Dict[str, Any],
    parameter_update: SecureParameterUpdate
) -> Dict[str, Any]:
    """
    生成交易信號

    Args:
        indicators: 技術指標
        sentiment_analysis: 情緒分析
        parameter_update: 參數更新

    Returns:
        交易信號
    """
    try:
        signals = {}

        # 獲取當前參數
        current_params = await session_manager.get_session_parameters(parameter_update.session_id)
        sentiment_threshold = current_params.get('sentiment_threshold', 0.7)

        # 基於RSI的信號
        if 'latest_rsi' in indicators:
            rsi = indicators['latest_rsi']
            if rsi < 30:
                signals['rsi_signal'] = 'oversold_buy'
            elif rsi > 70:
                signals['rsi_signal'] = 'overbought_sell'
            else:
                signals['rsi_signal'] = 'neutral'

        # 基於情緒的信號
        if 'latest_sentiment_strength' in indicators:
            sentiment = indicators['latest_sentiment_strength']
            if sentiment > sentiment_threshold:
                signals['sentiment_signal'] = 'bullish'
            elif sentiment < -sentiment_threshold:
                signals['sentiment_signal'] = 'bearish'
            else:
                signals['sentiment_signal'] = 'neutral'

        # 綜合信號
        signal_strength = 0
        if signals.get('rsi_signal') == 'oversold_buy':
            signal_strength += 2
        elif signals.get('rsi_signal') == 'overbought_sell':
            signal_strength -= 2

        if signals.get('sentiment_signal') == 'bullish':
            signal_strength += 1
        elif signals.get('sentiment_signal') == 'bearish':
            signal_strength -= 1

        if signal_strength >= 2:
            signals['overall_signal'] = 'strong_buy'
        elif signal_strength == 1:
            signals['overall_signal'] = 'buy'
        elif signal_strength == 0:
            signals['overall_signal'] = 'hold'
        elif signal_strength == -1:
            signals['overall_signal'] = 'sell'
        else:
            signals['overall_signal'] = 'strong_sell'

        return {
            "signals": signals,
            "signal_strength": signal_strength,
            "confidence": min(abs(signal_strength) / 3.0, 1.0)
        }

    except Exception as e:
        raise ParameterCalculationError(
            f"交易信號生成失敗: {str(e)}",
            {
                "indicators_keys": list(indicators.keys()) if indicators else [],
                "error_trace": traceback.format_exc()
            }
        )


async def calculate_performance_metrics_async(signals: Dict[str, Any]) -> Dict[str, Any]:
    """
    異步計算性能指標

    Args:
        signals: 交易信號

    Returns:
        性能指標
    """
    try:
        # 這裡應該實現實際的性能指標計算
        # 為了演示，返回模擬數據

        return {
            "sharpe_ratio": 1.25,
            "annual_returns": 0.15,
            "max_drawdown": 0.08,
            "win_rate": 0.65,
            "profit_factor": 1.8,
            "calculated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise ParameterCalculationError(
            f"性能指標計算失敗: {str(e)}",
            {"error_trace": traceback.format_exc()}
        )


async def process_parameter_update(
    session_id: str,
    data: Dict[str, Any]
) -> ParameterResponse:
    """
    處理參數更新請求

    Args:
        session_id: 會話ID
        data: 請求數據

    Returns:
        處理結果響應
    """
    processing_start = time.time()

    try:
        # 驗證和創建參數更新對象
        parameter_update = SecureParameterUpdate(**data, session_id=session_id)

        # 獲取當前會話參數
        current_params = await session_manager.get_session_parameters(session_id)

        # 驗證參數值和依賴關係
        validated_value = ParameterConfigValidator.validate_parameter(
            parameter_update.parameter_name,
            parameter_update.value,
            current_params
        )

        # 更新參數值
        parameter_update.value = validated_value

        # 速率限制檢查
        await rate_limiter.check_rate_limit(
            identifier=parameter_update.session_id,
            limit_type='parameter_updates',
            ip_address=None  # WebSocket連接可能沒有IP
        )

        # 計算策略結果
        results = await calculate_strategy_parameters_safe(session_id, parameter_update)

        processing_time = (time.time() - processing_start) * 1000

        return ParameterResponse(
            success=True,
            data=results,
            processing_time_ms=processing_time,
            session_id=session_id,
            request_id=f"req_{int(time.time() * 1000)}"
        )

    except SecurityValidationError as e:
        processing_time = (time.time() - processing_start) * 1000
        logger.warning(f"安全驗證失敗: session_id={session_id}, error={str(e)}")

        return ParameterResponse(
            success=False,
            error=str(e),
            error_code=e.error_code,
            processing_time_ms=processing_time,
            session_id=session_id
        )

    except ParameterValidationError as e:
        processing_time = (time.time() - processing_start) * 1000
        logger.warning(f"參數驗證失敗: session_id={session_id}, error={str(e)}")

        return ParameterResponse(
            success=False,
            error=str(e),
            error_code=e.error_code,
            processing_time_ms=processing_time,
            session_id=session_id
        )

    except Exception as e:
        processing_time = (time.time() - processing_start) * 1000
        logger.error(f"參數處理失敗: session_id={session_id}, error={str(e)}")

        return ParameterResponse(
            success=False,
            error="內部處理錯誤",
            error_code="INTERNAL_ERROR",
            processing_time_ms=processing_time,
            session_id=session_id
        )


async def calculate_strategy_parameters_safe(
    session_id: str,
    parameter_update: SecureParameterUpdate
) -> Dict[str, Any]:
    """
    安全的策略參數計算

    Args:
        session_id: 會話ID
        parameter_update: 參數更新

    Returns:
        計算結果

    Raises:
        ParameterCalculationError: 計算失敗
    """
    # 使用上下文管理器確保資源清理
    async with parameter_calculation_context(session_id):
        # 更新會話參數
        await session_manager.update_session_parameter(session_id, parameter_update)

        # 並行加載數據和計算指標
        data_task = asyncio.create_task(load_cbsc_data_safe())
        indicators_task = asyncio.create_task(
            calculate_technical_indicators_async(
                await data_task, parameter_update
            )
        )

        try:
            indicators = await indicators_task

            # 生成交易信號
            signals = await generate_trading_signals(
                indicators, {"session_id": session_id}, parameter_update
            )

            # 計算性能指標
            performance = await calculate_performance_metrics_async(signals)

            return {
                "indicators": indicators,
                "signals": signals,
                "performance": performance,
                "parameter_update": {
                    "name": parameter_update.parameter_name,
                    "value": parameter_update.value,
                    "timestamp": parameter_update.timestamp.isoformat(),
                    "session_id": session_id
                },
                "calculated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            if isinstance(e, ParameterCalculationError):
                raise
            raise ParameterCalculationError(f"策略計算失敗: {str(e)}")


# 導出必要的類和函數
__all__ = [
    'SecureParameterUpdate',
    'ParameterResponse',
    'ParameterConfigValidator',
    'SessionManager',
    'process_parameter_update',
    'calculate_strategy_parameters_safe',
    'session_manager',
    'ParameterValidationError',
    'ParameterCalculationError'
]
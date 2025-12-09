"""
機器學習API
提供4個ML端點：訓練、模型列表、預測、模型指標
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

from ..data_adapters.base_adapter import BaseAdapter
from ..ml.prediction_engine import MLPredictionEngine, ModelType, PredictionHorizon
from .models.api_response import APIResponse

# ========== Pydantic 模型 ==========


class MLModelType(str, Enum):
    """ML模型類型"""

    LSTM = "lstm"
    RANDOM_FOREST = "random_forest"
    XGBOOST = "xgboost"
    HYBRID = "hybrid"


class TrainModelRequest(BaseModel):
    """訓練模型請求"""

    symbol: str = Field(..., description="股票代碼")
    model_type: MLModelType = Field(..., description="模型類型")
    start_date: str = Field(..., description="開始日期")
    end_date: str = Field(..., description="結束日期")
    hyperparameters: Optional[Dict[str, Any]] = Field(None, description="超參數")


class ModelMetricsResponse(BaseModel):
    """模型指標響應"""

    model_id: str
    model_type: str
    accuracy: float
    mae: float
    mse: float
    rmse: float
    r2_score: float
    sharpe_ratio: float
    max_drawdown: float
    training_time: float
    last_trained: datetime


class PredictionRequest(BaseModel):
    """預測請求"""

    symbol: str = Field(..., description="股票代碼")
    model_type: MLModelType = Field(default=MLModelType.HYBRID, description="模型類型")
    horizon: str = Field(default="short", description="預測範圍")
    days_ahead: int = Field(default=5, ge=1, le=60, description="預測天數")
    confidence_threshold: float = Field(
        default=0.6, ge=0.5, le=0.95, description="信心閾值"
    )


class PredictionResultResponse(BaseModel):
    """預測結果響應"""

    prediction_id: str
    symbol: str
    model_type: str
    current_price: float
    predicted_price: float
    confidence: float
    upper_bound: float
    lower_bound: float
    trend_direction: str
    risk_level: str
    expected_return: float
    generated_at: datetime


class ModelInfoResponse(BaseModel):
    """模型信息響應"""

    model_id: str
    symbol: str
    model_type: str
    status: str  # "training", "ready", "failed", "deprecated"
    created_at: datetime
    last_trained: Optional[datetime] = None
    training_samples: int
    accuracy: Optional[float] = None
    version: str


class ModelVersionResponse(BaseModel):
    """模型版本響應"""

    version_id: str
    model_id: str
    version_number: str
    created_at: datetime
    metrics: Optional[Dict[str, float]] = None
    changelog: Optional[str] = None


# ========== ML服務管理器 ==========


class MLServiceManager:
    """ML服務管理器"""

    def __init__(
        self, data_adapter: BaseAdapter, ml_engine: Optional[MLPredictionEngine] = None
    ):
        self.data_adapter = data_adapter
        self.ml_engine = ml_engine
        self.logger = logging.getLogger("hk_quant_system.ml_service")

        # 模擬模型存儲
        self.models: Dict[str, ModelInfoResponse] = {}
        self.training_jobs: Dict[str, Dict[str, Any]] = {}

    async def train_model(
        self, request: TrainModelRequest, background_tasks: BackgroundTasks
    ) -> Dict[str, Any]:
        """訓練模型"""
        try:
            model_id = f"MODEL_{request.symbol}_{request.model_type}_{datetime.now().strftime('%Y % m % d % H % M % S')}"

            # 創建模型記錄
            model_info = ModelInfoResponse(
                model_id=model_id,
                symbol=request.symbol,
                model_type=request.model_type,
                status="training",
                created_at=datetime.now(),
                training_samples=0,
                version="1.0.0",
            )

            self.models[model_id] = model_info
            self.training_jobs[model_id] = {
                "status": "running",
                "progress": 0,
                "start_time": datetime.now(),
            }

            # 添加後台任務
            background_tasks.add_task(self._train_model_background, model_id, request)

            return {
                "model_id": model_id,
                "status": "training",
                "message": "模型訓練已開始",
                "estimated_time": "10 - 30分鐘",
            }

        except Exception as e:
            self.logger.error(f"啟動模型訓練失敗: {str(e)}")
            raise

    async def _train_model_background(self, model_id: str, request: TrainModelRequest):
        """後台模型訓練"""
        try:
            self.training_jobs[model_id]["progress"] = 10

            if self.ml_engine:
                # 使用實際的ML引擎訓練
                metrics = await self.ml_engine.train_lstm_model(
                    request.symbol, request.start_date, request.end_date
                )

                # 更新模型信息
                model_info = self.models[model_id]
                model_info.status = "ready"
                model_info.last_trained = datetime.now()
                model_info.training_samples = 1000  # 模擬
                model_info.accuracy = metrics.accuracy if metrics else 0.75

                self.training_jobs[model_id]["status"] = "completed"
                self.training_jobs[model_id]["progress"] = 100
            else:
                # 模擬訓練過程
                import time

                for progress in range(10, 101, 10):
                    self.training_jobs[model_id]["progress"] = progress
                    time.sleep(2)  # 模擬訓練時間

                # 更新模型信息
                model_info = self.models[model_id]
                model_info.status = "ready"
                model_info.last_trained = datetime.now()
                model_info.training_samples = 1000
                model_info.accuracy = 0.78

                self.training_jobs[model_id]["status"] = "completed"

        except Exception as e:
            self.logger.error(f"模型訓練失敗 {model_id}: {str(e)}")
            model_info = self.models[model_id]
            model_info.status = "failed"
            self.training_jobs[model_id]["status"] = "failed"
            self.training_jobs[model_id]["error"] = str(e)

    async def get_models(self, symbol: Optional[str] = None) -> List[ModelInfoResponse]:
        """獲取模型列表"""
        models = list(self.models.values())

        if symbol:
            models = [m for m in models if m.symbol == symbol]

        # 按創建時間排序
        models.sort(key=lambda x: x.created_at, reverse=True)

        return models

    async def get_model_details(self, model_id: str) -> Optional[ModelInfoResponse]:
        """獲取模型詳情"""
        return self.models.get(model_id)

    async def predict_price(
        self, request: PredictionRequest
    ) -> PredictionResultResponse:
        """預測價格"""
        try:
            prediction_id = (
                f"PRED_{request.symbol}_{datetime.now().strftime('%Y % m % d % H % M % S')}"
            )

            # 使用ML引擎進行預測
            if self.ml_engine:
                # 映射預測範圍
                horizon_map = {
                    "short": PredictionHorizon.SHORT_TERM,
                    "medium": PredictionHorizon.MEDIUM_TERM,
                    "long": PredictionHorizon.LONG_TERM,
                }

                prediction = await self.ml_engine.predict_price(
                    symbol=request.symbol,
                    model_type=ModelType.HYBRID,
                    horizon=horizon_map.get(
                        request.horizon, PredictionHorizon.SHORT_TERM
                    ),
                    days_ahead=request.days_ahead,
                )

                current_price = 350.0  # 模擬
                if prediction:
                    result = PredictionResultResponse(
                        prediction_id=prediction_id,
                        symbol=request.symbol,
                        model_type=request.model_type,
                        current_price=current_price,
                        predicted_price=prediction.predicted_price,
                        confidence=prediction.confidence,
                        upper_bound=prediction.predicted_price * 1.05,
                        lower_bound=prediction.predicted_price * 0.95,
                        trend_direction=prediction.trend_direction,
                        risk_level=prediction.risk_level,
                        expected_return=(prediction.predicted_price - current_price)
                        / current_price,
                        generated_at=datetime.now(),
                    )
                else:
                    # 模擬預測結果
                    result = self._simulate_prediction(request, prediction_id)
            else:
                # 模擬預測
                result = self._simulate_prediction(request, prediction_id)

            return result

        except Exception as e:
            self.logger.error(f"價格預測失敗: {str(e)}")
            raise

    def _simulate_prediction(
        self, request: PredictionRequest, prediction_id: str
    ) -> PredictionResultResponse:
        """模擬預測結果"""
        import random

        random.seed(hash(request.symbol) % 1000)

        current_price = 300.0 + random.uniform(-50, 100)
        price_change = random.uniform(-0.1, 0.15)  # -10% 到 +15%
        predicted_price = current_price * (1 + price_change)
        confidence = random.uniform(0.6, 0.95)

        trend = (
            "up"
            if price_change > 0.02
            else "down" if price_change < -0.02 else "sideways"
        )
        risk_level = (
            "high"
            if abs(price_change) > 0.1
            else "medium" if abs(price_change) > 0.05 else "low"
        )

        return PredictionResultResponse(
            prediction_id=prediction_id,
            symbol=request.symbol,
            model_type=request.model_type,
            current_price=current_price,
            predicted_price=predicted_price,
            confidence=confidence,
            upper_bound=predicted_price * 1.05,
            lower_bound=predicted_price * 0.95,
            trend_direction=trend,
            risk_level=risk_level,
            expected_return=price_change,
            generated_at=datetime.now(),
        )

    async def get_model_metrics(self, model_id: str) -> Optional[ModelMetricsResponse]:
        """獲取模型指標"""
        if model_id not in self.models:
            return None

        model_info = self.models[model_id]

        # 模擬指標
        metrics = ModelMetricsResponse(
            model_id=model_id,
            model_type=model_info.model_type,
            accuracy=model_info.accuracy or 0.75,
            mae=15.5,
            mse=420.3,
            rmse=20.5,
            r2_score=0.78,
            sharpe_ratio=1.2,
            max_drawdown=8.5,
            training_time=600.0,  # 10分鐘
            last_trained=model_info.last_trained or datetime.now(),
        )

        return metrics

    async def get_training_status(self, model_id: str) -> Optional[Dict[str, Any]]:
        """獲取訓練狀態"""
        return self.training_jobs.get(model_id)

    async def delete_model(self, model_id: str) -> bool:
        """刪除模型"""
        if model_id in self.models:
            del self.models[model_id]

        if model_id in self.training_jobs:
            del self.training_jobs[model_id]

        return True


# ========== FastAPI 路由 ==========


def create_ml_router(
    data_adapter: BaseAdapter, ml_engine: Optional[MLPredictionEngine] = None
) -> APIRouter:
    """創建機器學習路由"""
    router = APIRouter(prefix="/api / v2 / ml", tags=["machine_learning"])
    logger = logging.getLogger("hk_quant_system.ml_api")

    # ML服務管理器
    ml_manager = MLServiceManager(data_adapter, ml_engine)

    @router.post("/train - model", response_model=APIResponse)
    async def train_model_endpoint(
        request: TrainModelRequest, background_tasks: BackgroundTasks
    ):
        """訓練模型"""
        try:
            result = await ml_manager.train_model(request, background_tasks)
            return APIResponse(success=True, data=result, message="模型訓練已啟動")
        except Exception as e:
            logger.error(f"啟動模型訓練失敗: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/models", response_model=APIResponse)
    async def get_models(symbol: Optional[str] = None):
        """模型列表"""
        try:
            models = await ml_manager.get_models(symbol)
            return APIResponse(
                success=True,
                data={"models": [m.dict() for m in models], "total_count": len(models)},
                message="模型列表查詢成功",
            )
        except Exception as e:
            logger.error(f"查詢模型列表失敗: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/models/{model_id}", response_model=APIResponse)
    async def get_model_details(model_id: str):
        """模型詳情"""
        try:
            model = await ml_manager.get_model_details(model_id)
            if not model:
                raise HTTPException(status_code=404, detail="模型不存在")

            return APIResponse(
                success=True, data=model.dict(), message="模型詳情查詢成功"
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"查詢模型詳情失敗: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/predict", response_model=APIResponse)
    async def predict_endpoint(request: PredictionRequest):
        """價格預測"""
        try:
            result = await ml_manager.predict_price(request)
            return APIResponse(
                success=True,
                data=result.dict(),
                message=f"{request.symbol} 價格預測完成",
            )
        except Exception as e:
            logger.error(f"價格預測失敗: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/models/{model_id}/metrics", response_model=APIResponse)
    async def get_model_metrics(model_id: str):
        """模型指標"""
        try:
            metrics = await ml_manager.get_model_metrics(model_id)
            if not metrics:
                raise HTTPException(status_code=404, detail="模型不存在或指標不可用")

            return APIResponse(
                success=True, data=metrics.dict(), message="模型指標查詢成功"
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"查詢模型指標失敗: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/training - status/{model_id}", response_model=APIResponse)
    async def get_training_status(model_id: str):
        """訓練狀態"""
        try:
            status = await ml_manager.get_training_status(model_id)
            if not status:
                raise HTTPException(status_code=404, detail="訓練任務不存在")

            return APIResponse(success=True, data=status, message="訓練狀態查詢成功")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"查詢訓練狀態失敗: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.delete("/models/{model_id}", response_model=APIResponse)
    async def delete_model_endpoint(model_id: str):
        """刪除模型"""
        try:
            success = await ml_manager.delete_model(model_id)
            return APIResponse(
                success=success,
                data={"model_id": model_id},
                message="模型刪除成功" if success else "模型刪除失敗",
            )
        except Exception as e:
            logger.error(f"刪除模型失敗: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    return router

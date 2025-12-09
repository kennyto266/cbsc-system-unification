"""
ML編排器主控系統
統一管理所有機器學習組件的主控制器

功能:
- 統一ML工作流程編排
- 多模型協調和集成
- 實時推理服務
- 模型生命周期管理
- 自動化A / B測試
- 端到端ML流水線
"""

import asyncio
import json
import logging
import pickle
import uuid
import warnings
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# 內部ML組件
from .feature_store import AdvancedFeatureStore, FeatureType
from .ml_monitoring import AlertSeverity, DriftType, MLMonitoringSystem
from .ml_pipeline import PipelineOrchestrator, PipelineStatus, PipelineType
from .model_registry import DeploymentStrategy, ModelRegistry, ModelStatus, ModelType
from .reinforcement_learning import (
    AgentType,
    MultiAgentSystem,
    RLTrainingManager,
    TradingEnvironment,
)
from .trading_models import (
    AdvancedPricePredictor,
    MarketRegimeDetector,
    ModelPrediction,
    SentimentAnalyzer,
    VolatilityForecaster,
)


class SystemMode(Enum):
    """系統模式"""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class InferenceMode(Enum):
    """推理模式"""

    SINGLE_MODEL = "single_model"
    ENSEMBLE = "ensemble"
    MULTI_AGENT = "multi_agent"
    HYBRID = "hybrid"


@dataclass
class PredictionRequest:
    """預測請求"""

    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    symbol: str = ""
    data: Optional[pd.DataFrame] = None
    model_names: Optional[List[str]] = None
    inference_mode: InferenceMode = InferenceMode.SINGLE_MODEL
    parameters: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    priority: int = 1  # 1 - 10, 10為最高優先級


@dataclass
class PredictionResponse:
    """預測響應"""

    request_id: str
    symbol: str
    predictions: List[ModelPrediction]
    confidence: float
    ensemble_weight: Optional[float] = None
    reasoning: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None


@dataclass
class SystemStatus:
    """系統狀態"""

    mode: SystemMode
    active_models: int
    total_predictions: int
    avg_latency_ms: float
    error_rate: float
    last_updated: datetime
    health_score: float
    active_alerts: int


class MLModelOrchestrator:
    """
    ML模型編排器

    統一管理所有ML組件，提供統一的API接口
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        system_mode: SystemMode = SystemMode.DEVELOPMENT,
    ):
        self.logger = logging.getLogger("hk_quant_system.ml_orchestrator")
        self.config = config or self._default_config()
        self.system_mode = system_mode

        # 初始化所有ML組件
        self._initialize_components()

        # 推理服務狀態
        self.inference_cache: Dict[str, PredictionResponse] = {}
        self.prediction_queue: asyncio.Queue = asyncio.Queue()
        self.prediction_history: deque = deque(maxlen=10000)

        # 系統統計
        self.system_stats = {
            "total_predictions": 0,
            "total_errors": 0,
            "total_latency": 0.0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

        # 線程池
        self.executor = ThreadPoolExecutor(max_workers=4)

        self.logger.info(f"ML Orchestrator initialized in {system_mode.value} mode")

    def _default_config(self) -> Dict[str, Any]:
        """默認配置"""
        return {
            "feature_store": {"cache_expiry_minutes": 5, "batch_size": 100},
            "model_registry": {"enable_mlflow": False, "auto_deployment": False},
            "inference": {
                "cache_enabled": True,
                "cache_ttl_seconds": 300,
                "timeout_seconds": 30,
                "max_concurrent_requests": 100,
            },
            "monitoring": {
                "enable_monitoring": True,
                "alert_thresholds": {
                    "error_rate": 0.05,
                    "latency_ms": 1000,
                    "accuracy_drop": 0.1,
                },
            },
            "ensemble": {
                "default_weights": {
                    "lstm": 0.4,
                    "xgboost": 0.3,
                    "random_forest": 0.2,
                    "sentiment": 0.1,
                }
            },
        }

    def _initialize_components(self):
        """初始化所有ML組件"""
        try:
            # 特徵存儲
            self.feature_store = AdvancedFeatureStore(
                config=self.config.get("feature_store", {})
            )

            # 模型註冊中心
            self.model_registry = ModelRegistry(
                enable_mlflow=self.config.get("model_registry", {}).get(
                    "enable_mlflow", False
                )
            )

            # 交易模型
            self.price_predictor = AdvancedPricePredictor(
                config=self.config.get("price_predictor", {})
            )
            self.volatility_forecaster = VolatilityForecaster(
                config=self.config.get("volatility_forecaster", {})
            )
            self.regime_detector = MarketRegimeDetector(
                config=self.config.get("regime_detector", {})
            )
            self.sentiment_analyzer = SentimentAnalyzer(
                config=self.config.get("sentiment_analyzer", {})
            )

            # 流水線編排器
            self.pipeline_orchestrator = PipelineOrchestrator(
                config=self.config.get("pipeline", {})
            )

            # 監控系統
            if self.config.get("monitoring", {}).get("enable_monitoring", True):
                self.monitoring_system = MLMonitoringSystem(
                    config=self.config.get("monitoring", {})
                )

            self.logger.info("All ML components initialized successfully")

        except Exception as e:
            self.logger.error(f"Component initialization failed: {str(e)}")
            raise

    async def start_system(self):
        """啟動ML系統"""
        try:
            self.logger.info("Starting ML orchestrator system...")

            # 啟動監控系統
            if hasattr(self, "monitoring_system"):
                monitoring_task = asyncio.create_task(
                    self.monitoring_system.start_monitoring()
                )
                self.logger.info("Monitoring system started")

            # 啟動推理服務
            inference_task = asyncio.create_task(self._inference_service_loop())
            self.logger.info("Inference service started")

            # 啟動流水線調度器
            pipeline_task = asyncio.create_task(
                self.pipeline_orchestrator.start_scheduler()
            )
            self.logger.info("Pipeline scheduler started")

            self.logger.info("ML orchestrator system started successfully")

            # 返回所有任務以供管理
            return {
                "monitoring_task": monitoring_task,
                "inference_task": inference_task,
                "pipeline_task": pipeline_task,
            }

        except Exception as e:
            self.logger.error(f"System startup failed: {str(e)}")
            raise

    async def stop_system(self):
        """停止ML系統"""
        try:
            self.logger.info("Stopping ML orchestrator system...")

            # 停止監控系統
            if hasattr(self, "monitoring_system"):
                await self.monitoring_system.stop_monitoring()

            # 停止流水線編排器
            self.pipeline_orchestrator.stop_scheduler()

            # 關閉線程池
            self.executor.shutdown(wait=True)

            self.logger.info("ML orchestrator system stopped")

        except Exception as e:
            self.logger.error(f"System shutdown failed: {str(e)}")

    async def predict(self, request: PredictionRequest) -> PredictionResponse:
        """
        統一預測接口

        Args:
            request: 預測請求

        Returns:
            預測響應
        """
        try:
            start_time = datetime.now()

            # 檢查緩存
            if self.config.get("inference", {}).get("cache_enabled", True):
                cached_response = self._get_cached_prediction(request)
                if cached_response:
                    self.system_stats["cache_hits"] += 1
                    return cached_response
                else:
                    self.system_stats["cache_misses"] += 1

            # 根據推理模式執行預測
            if request.inference_mode == InferenceMode.SINGLE_MODEL:
                response = await self._single_model_prediction(request)
            elif request.inference_mode == InferenceMode.ENSEMBLE:
                response = await self._ensemble_prediction(request)
            elif request.inference_mode == InferenceMode.MULTI_AGENT:
                response = await self._multi_agent_prediction(request)
            elif request.inference_mode == InferenceMode.HYBRID:
                response = await self._hybrid_prediction(request)
            else:
                raise ValueError(
                    f"Unsupported inference mode: {request.inference_mode}"
                )

            # 計算延遲
            end_time = datetime.now()
            response.latency_ms = (end_time - start_time).total_seconds() * 1000

            # 更新統計
            self._update_system_stats(response)

            # 緩存結果
            if self.config.get("inference", {}).get("cache_enabled", True):
                self._cache_prediction(request, response)

            # 記錄預測歷史
            self.prediction_history.append(response)

            # 監控預測質量
            if hasattr(self, "monitoring_system"):
                await self.monitoring_system.performance_monitor.record_prediction(
                    model_name=(
                        response.predictions[0].model_name
                        if response.predictions
                        else "unknown"
                    ),
                    prediction=(
                        response.predictions[0].prediction
                        if response.predictions
                        else 0.0
                    ),
                    latency_ms=response.latency_ms,
                )

            self.logger.info(
                f"Prediction completed for {request.symbol}: "
                f"mode={request.inference_mode.value}, "
                f"latency={response.latency_ms:.2f}ms"
            )

            return response

        except Exception as e:
            self.logger.error(f"Prediction failed: {str(e)}")
            self.system_stats["total_errors"] += 1

            return PredictionResponse(
                request_id=request.request_id,
                symbol=request.symbol,
                predictions=[],
                confidence=0.0,
                error=str(e),
                timestamp=datetime.now(),
            )

    async def _single_model_prediction(
        self, request: PredictionRequest
    ) -> PredictionResponse:
        """單模型預測"""
        try:
            if not request.model_names or len(request.model_names) != 1:
                raise ValueError("Single model mode requires exactly one model name")

            model_name = request.model_names[0]
            symbol = request.symbol

            # 獲取數據和計算特徵
            features_df = await self._get_features_for_prediction(symbol, request.data)

            # 使用模型註冊中心進行預測
            prediction_value = await self.model_registry.predict(
                model_name=model_name, features=features_df, return_confidence=True
            )

            if isinstance(prediction_value, tuple):
                prediction, confidence = prediction_value
            else:
                prediction = prediction_value
                confidence = 0.8  # 默認置信度

            # 創建預測結果
            model_prediction = ModelPrediction(
                model_name=model_name,
                prediction=prediction[-1] if len(prediction) > 0 else prediction,
                confidence=confidence[-1] if len(confidence) > 0 else confidence,
                timestamp=datetime.now(),
            )

            return PredictionResponse(
                request_id=request.request_id,
                symbol=symbol,
                predictions=[model_prediction],
                confidence=model_prediction.confidence,
                reasoning=f"Single model prediction using {model_name}",
                metadata={"model_type": "single"},
            )

        except Exception as e:
            self.logger.error(f"Single model prediction failed: {str(e)}")
            raise

    async def _ensemble_prediction(
        self, request: PredictionRequest
    ) -> PredictionResponse:
        """集成預測"""
        try:
            symbol = request.symbol
            model_names = request.model_names or ["lstm", "xgboost", "random_forest"]

            # 獲取特徵
            features_df = await self._get_features_for_prediction(symbol, request.data)

            # 收集各模型預測
            predictions = []
            weights = self.config.get("ensemble", {}).get("default_weights", {})

            for model_name in model_names:
                try:
                    prediction_value = await self.model_registry.predict(
                        model_name=model_name, features=features_df
                    )

                    if isinstance(prediction_value, tuple):
                        prediction, confidence = prediction_value
                    else:
                        prediction = prediction_value
                        confidence = 0.8

                    model_prediction = ModelPrediction(
                        model_name=model_name,
                        prediction=(
                            prediction[-1] if len(prediction) > 0 else prediction
                        ),
                        confidence=(
                            confidence[-1] if len(confidence) > 0 else confidence
                        ),
                        timestamp=datetime.now(),
                    )
                    predictions.append(model_prediction)

                except Exception as e:
                    self.logger.warning(
                        f"Model {model_name} prediction failed: {str(e)}"
                    )
                    continue

            if not predictions:
                raise ValueError("No models produced successful predictions")

            # 計算集成預測
            ensemble_prediction = self._calculate_ensemble_prediction(
                predictions, weights
            )

            return PredictionResponse(
                request_id=request.request_id,
                symbol=symbol,
                predictions=predictions,
                confidence=ensemble_prediction["confidence"],
                ensemble_weight=ensemble_prediction["weight"],
                reasoning=f"Ensemble prediction using {len(predictions)} models",
                metadata={
                    "model_type": "ensemble",
                    "individual_predictions": [p.model_name for p in predictions],
                },
            )

        except Exception as e:
            self.logger.error(f"Ensemble prediction failed: {str(e)}")
            raise

    async def _multi_agent_prediction(
        self, request: PredictionRequest
    ) -> PredictionResponse:
        """多智能體預測"""
        try:
            symbol = request.symbol

            # 獲取市場狀態
            regime_info = self.regime_detector.get_current_regime(symbol)

            # 獲取情緒分析
            sentiment_data = []  # 這裡需要真實的新聞數據
            sentiment_result = self.sentiment_analyzer.analyze_news_sentiment(
                sentiment_data, method="bert"
            )

            # 創建多智能體系統 (簡化版本)
            agents = {
                "price_predictor": self.price_predictor,
                "volatility_forecaster": self.volatility_forecaster,
                "regime_detector": self.regime_detector,
            }

            # 這裡需要創建MultiAgentSystem的實例
            # multi_agent_system = MultiAgentSystem(agents)

            # 獲取數據和特徵
            features_df = await self._get_features_for_prediction(symbol, request.data)

            # 執行多智能體預測
            predictions = []

            # 價格預測智能體
            price_predictions = await self.price_predictor.predict_price(
                data=request.data, model_types=["lstm", "xgboost"]
            )
            predictions.extend(price_predictions)

            # 轉換為標準格式
            model_predictions = []
            for pred in price_predictions:
                model_predictions.append(
                    ModelPrediction(
                        model_name=pred.model_name,
                        prediction=pred.prediction,
                        confidence=pred.confidence,
                        timestamp=pred.timestamp,
                    )
                )

            # 計算綜合預測
            if model_predictions:
                ensemble_pred = self._calculate_ensemble_prediction(
                    model_predictions, {"price_predictor": 0.7, "volatility": 0.3}
                )
            else:
                ensemble_pred = {"prediction": 0.0, "confidence": 0.0, "weight": 0.0}

            return PredictionResponse(
                request_id=request.request_id,
                symbol=symbol,
                predictions=model_predictions,
                confidence=ensemble_pred["confidence"],
                reasoning=f"Multi - agent prediction with {len(model_predictions)} agents",
                metadata={
                    "model_type": "multi_agent",
                    "regime": regime_info,
                    "sentiment": sentiment_result.get("overall_sentiment", "neutral"),
                },
            )

        except Exception as e:
            self.logger.error(f"Multi - agent prediction failed: {str(e)}")
            raise

    async def _hybrid_prediction(
        self, request: PredictionRequest
    ) -> PredictionResponse:
        """混合預測 (結合多種方法)"""
        try:
            # 執行集成預測
            ensemble_request = PredictionRequest(
                request_id=request.request_id + "_ensemble",
                symbol=request.symbol,
                data=request.data,
                model_names=request.model_names,
                inference_mode=InferenceMode.ENSEMBLE,
            )
            ensemble_response = await self._ensemble_prediction(ensemble_request)

            # 執行情緒分析
            sentiment_adjustment = await self._get_sentiment_adjustment(request.symbol)

            # 調整集成預測
            if ensemble_response.predictions:
                base_prediction = ensemble_response.predictions[0].prediction
                adjusted_prediction = base_prediction * (1 + sentiment_adjustment)

                # 更新預測
                ensemble_response.predictions[0].prediction = adjusted_prediction
                ensemble_response.reasoning += (
                    f" with sentiment adjustment ({sentiment_adjustment:.3f})"
                )
                ensemble_response.metadata["sentiment_adjustment"] = (
                    sentiment_adjustment
                )

            return ensemble_response

        except Exception as e:
            self.logger.error(f"Hybrid prediction failed: {str(e)}")
            raise

    async def _get_features_for_prediction(
        self, symbol: str, data: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """獲取預測特徵"""
        try:
            if data is not None:
                # 使用提供的數據計算特徵
                features_df = await self.feature_store.compute_features(
                    symbol=symbol,
                    data=data,
                    feature_types=[
                        FeatureType.PRICE,
                        FeatureType.VOLUME,
                        FeatureType.TECHNICAL,
                    ],
                )
            else:
                # 從特徵存儲獲取最新特徵
                end_date = datetime.now()
                start_date = end_date - timedelta(days=90)
                features_df = await self.feature_store.get_features(
                    symbol=symbol, start_date=start_date, end_date=end_date
                )

            if features_df.empty:
                raise ValueError(f"No features available for symbol {symbol}")

            return features_df.tail(1)  # 返回最新的特徵

        except Exception as e:
            self.logger.error(f"Feature extraction failed: {str(e)}")
            raise

    def _calculate_ensemble_prediction(
        self, predictions: List[ModelPrediction], weights: Dict[str, float]
    ) -> Dict[str, float]:
        """計算集成預測"""
        try:
            if not predictions:
                return {"prediction": 0.0, "confidence": 0.0, "weight": 0.0}

            # 加權平均預測
            weighted_prediction = 0.0
            weighted_confidence = 0.0
            total_weight = 0.0

            for pred in predictions:
                weight = weights.get(pred.model_name, 1.0)
                weighted_prediction += pred.prediction * weight * pred.confidence
                weighted_confidence += pred.confidence * weight
                total_weight += weight

            if total_weight > 0:
                final_prediction = weighted_prediction / (weighted_confidence + 1e-8)
                final_confidence = weighted_confidence / total_weight
            else:
                final_prediction = 0.0
                final_confidence = 0.0

            return {
                "prediction": final_prediction,
                "confidence": final_confidence,
                "weight": total_weight,
            }

        except Exception as e:
            self.logger.error(f"Ensemble calculation failed: {str(e)}")
            return {"prediction": 0.0, "confidence": 0.0, "weight": 0.0}

    async def _get_sentiment_adjustment(self, symbol: str) -> float:
        """獲取情緒調整因子"""
        try:
            # 這裡需要真實的新聞數據
            # news_data = await self._get_news_for_symbol(symbol)
            # sentiment_result = self.sentiment_analyzer.analyze_news_sentiment(news_data)

            # 佔位符實現
            return np.random.normal(0, 0.02)  # 小幅隨機調整

        except Exception as e:
            self.logger.warning(f"Sentiment adjustment failed: {str(e)}")
            return 0.0

    def _get_cached_prediction(
        self, request: PredictionRequest
    ) -> Optional[PredictionResponse]:
        """獲取緩存的預測"""
        try:
            cache_key = self._generate_cache_key(request)
            cached = self.inference_cache.get(cache_key)

            if cached:
                # 檢查緩存是否過期
                cache_ttl = self.config.get("inference", {}).get(
                    "cache_ttl_seconds", 300
                )
                if (datetime.now() - cached.timestamp).total_seconds() < cache_ttl:
                    return cached
                else:
                    # 移除過期緩存
                    del self.inference_cache[cache_key]

            return None

        except Exception as e:
            self.logger.warning(f"Cache retrieval failed: {str(e)}")
            return None

    def _cache_prediction(
        self, request: PredictionRequest, response: PredictionResponse
    ):
        """緩存預測結果"""
        try:
            cache_key = self._generate_cache_key(request)
            self.inference_cache[cache_key] = response

            # 限制緩存大小
            max_cache_size = self.config.get("inference", {}).get(
                "max_cache_size", 1000
            )
            if len(self.inference_cache) > max_cache_size:
                # 移除最舊的緩存項
                oldest_key = min(
                    self.inference_cache.keys(),
                    key=lambda k: self.inference_cache[k].timestamp,
                )
                del self.inference_cache[oldest_key]

        except Exception as e:
            self.logger.warning(f"Cache storage failed: {str(e)}")

    def _generate_cache_key(self, request: PredictionRequest) -> str:
        """生成緩存鍵"""
        key_parts = [
            request.symbol,
            request.inference_mode.value,
            str(sorted(request.model_names or [])),
            str(hash(str(request.parameters))),
        ]
        return "_".join(key_parts)

    def _update_system_stats(self, response: PredictionResponse):
        """更新系統統統計"""
        try:
            self.system_stats["total_predictions"] += 1
            self.system_stats["total_latency"] += response.latency_ms

            if response.error:
                self.system_stats["total_errors"] += 1

        except Exception as e:
            self.logger.warning(f"Stats update failed: {str(e)}")

    async def _inference_service_loop(self):
        """推理服務循環"""
        while True:
            try:
                # 處理預測隊列中的請求
                while not self.prediction_queue.empty():
                    request = await self.prediction_queue.get()
                    response = await self.predict(request)
                    # 這裡可以將響應發送回客戶端

                # 短暫休眠避免CPU占用過高
                await asyncio.sleep(0.01)

            except Exception as e:
                self.logger.error(f"Inference service loop error: {str(e)}")
                await asyncio.sleep(1)

    def get_system_status(self) -> SystemStatus:
        """獲取系統狀態"""
        try:
            total_predictions = self.system_stats["total_predictions"]
            total_errors = self.system_stats["total_errors"]
            total_latency = self.system_stats["total_latency"]

            avg_latency = total_latency / max(1, total_predictions)
            error_rate = total_errors / max(1, total_predictions)

            # 計算健康分數
            health_score = max(0, 1 - (error_rate * 10 + avg_latency / 1000))

            # 獲取活躍警報數
            active_alerts = 0
            if hasattr(self, "monitoring_system"):
                active_alerts = len(
                    self.monitoring_system.alert_manager.get_active_alerts()
                )

            return SystemStatus(
                mode=self.system_mode,
                active_models=len(self.model_registry.production_models),
                total_predictions=total_predictions,
                avg_latency_ms=avg_latency,
                error_rate=error_rate,
                last_updated=datetime.now(),
                health_score=health_score,
                active_alerts=active_alerts,
            )

        except Exception as e:
            self.logger.error(f"System status check failed: {str(e)}")
            return SystemStatus(
                mode=self.system_mode,
                active_models=0,
                total_predictions=0,
                avg_latency_ms=0.0,
                error_rate=1.0,
                last_updated=datetime.now(),
                health_score=0.0,
                active_alerts=0,
            )

    async def train_models(self, training_config: Dict[str, Any]) -> Dict[str, Any]:
        """訓練模型"""
        try:
            self.logger.info("Starting model training pipeline...")

            # 創建訓練流水線
            pipeline_config = PipelineConfig(
                name="model_training",
                type=PipelineType.MODEL_TRAINING,
                parameters=training_config,
            )

            # 運行流水線
            result = await self.pipeline_orchestrator.run_pipeline(
                pipeline_config.pipeline_id, training_config
            )

            return {
                "pipeline_id": result.pipeline_id,
                "run_id": result.run_id,
                "status": result.status.value,
                "metrics": result.metrics,
                "artifacts": result.artifacts,
            }

        except Exception as e:
            self.logger.error(f"Model training failed: {str(e)}")
            raise

    def add_model_for_monitoring(
        self,
        model_name: str,
        reference_data: pd.DataFrame,
        monitoring_config: Optional[Dict[str, Any]] = None,
    ):
        """添加模型監控"""
        try:
            if hasattr(self, "monitoring_system"):
                self.monitoring_system.add_model_monitoring(
                    model_name=model_name,
                    reference_data=reference_data,
                    monitoring_config=monitoring_config,
                )
                self.logger.info(f"Model monitoring added: {model_name}")
            else:
                self.logger.warning("Monitoring system not available")

        except Exception as e:
            self.logger.error(f"Failed to add model monitoring: {str(e)}")

    async def run_ab_test(
        self,
        model_a: str,
        model_b: str,
        traffic_split: float = 0.5,
        duration_days: int = 7,
    ) -> Dict[str, Any]:
        """運行A / B測試"""
        try:
            # 創建A / B測試流水線
            ab_test_config = {
                "type": "ab_test",
                "models": {"model_a": model_a, "model_b": model_b},
                "traffic_split": traffic_split,
                "duration_days": duration_days,
            }

            # 這裡需要實現完整的A / B測試邏輯
            # 包括流量分配、指標收集、統計顯著性檢驗等

            self.logger.info(f"A / B test started: {model_a} vs {model_b}")

            return {
                "test_id": str(uuid.uuid4()),
                "model_a": model_a,
                "model_b": model_b,
                "traffic_split": traffic_split,
                "duration_days": duration_days,
                "status": "running",
                "start_time": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"A / B test setup failed: {str(e)}")
            raise


# 全局ML編排器實例
ml_orchestrator = MLModelOrchestrator()

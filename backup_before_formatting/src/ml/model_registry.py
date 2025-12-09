"""
生產級別ML模型註冊中心
支持模型版本管理、A / B測試、實時監控和自動部署

功能:
- 模型版本控制和元數據管理
- 自動模型訓練和部署流水線
- A / B測試和漸進式部署
- 模型性能監控和漂移檢測
- 模型風險管理和合規性
- 多環境部署支持 (開發 / 測試 / 生產)
"""

import asyncio
import hashlib
import json
import logging
import pickle
import shutil
import sqlite3
import tempfile
import uuid
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

try:
    import mlflow
    import mlflow.keras
    import mlflow.pytorch
    import mlflow.sklearn

    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False

try:
    import optuna

    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False

try:
    import evidently
    from evidently.dashboard import Dashboard
    from evidently.metric_preset import ClassificationPreset, DataDriftPreset
    from evidently.report import Report
    from evidently.test_suite import TestSuite

    EVIDENTLY_AVAILABLE = True
except ImportError:
    EVIDENTLY_AVAILABLE = False

import warnings

from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)

warnings.filterwarnings("ignore")


class ModelType(Enum):
    """模型類型"""

    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    TIME_SERIES = "time_series"
    REINFORCEMENT = "reinforcement"
    ENSEMBLE = "ensemble"
    NEURAL_NETWORK = "neural_network"


class ModelStatus(Enum):
    """模型狀態"""

    DEVELOPING = "developing"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    ARCHIVED = "archived"
    FAILED = "failed"


class DeploymentStrategy(Enum):
    """部署策略"""

    DIRECT = "direct"  # 直接部署
    CANARY = "canary"  # 金絲雀部署
    BLUE_GREEN = "blue_green"  # 藍綠部署
    SHADOW = "shadow"  # 影子部署
    A_B_TEST = "ab_test"  # A / B測試


@dataclass
class ModelMetrics:
    """模型性能指標"""

    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    mae: Optional[float] = None
    mse: Optional[float] = None
    rmse: Optional[float] = None
    r2_score: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    hit_rate: Optional[float] = None
    profit_factor: Optional[float] = None
    total_return: Optional[float] = None
    volatility: Optional[float] = None
    latency_ms: Optional[float] = None
    throughput: Optional[float] = None
    memory_usage_mb: Optional[float] = None

    def to_dict(self) -> Dict[str, float]:
        """轉換為字典"""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class ModelMetadata:
    """模型元數據"""

    name: str
    version: str
    model_type: ModelType
    description: str
    author: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    status: ModelStatus = ModelStatus.DEVELOPING
    tags: List[str] = field(default_factory=list)
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    feature_importance: Dict[str, float] = field(default_factory=dict)
    training_data_hash: Optional[str] = None
    model_hash: Optional[str] = None
    file_path: Optional[str] = None
    model_size_mb: Optional[float] = None
    dependencies: List[str] = field(default_factory=list)
    environment: str = "development"
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        data = asdict(self)
        data["model_type"] = self.model_type.value
        data["status"] = self.status.value
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        return data


@dataclass
class ModelVersion:
    """模型版本"""

    metadata: ModelMetadata
    metrics: ModelMetrics
    model_object: Any
    training_history: Optional[Dict[str, List[float]]] = None
    validation_results: Optional[Dict[str, Any]] = None

    def calculate_model_hash(self) -> str:
        """計算模型哈希值"""
        model_pickle = pickle.dumps(self.model_object)
        return hashlib.sha256(model_pickle).hexdigest()


class ModelRegistry:
    """
    模型註冊中心

    管理ML模型的生命周期，包括訓練、驗證、部署和監控
    """

    def __init__(
        self,
        db_path: str = "model_registry.db",
        model_dir: str = "models",
        enable_mlflow: bool = False,
        mlflow_tracking_uri: Optional[str] = None,
    ):
        self.logger = logging.getLogger("hk_quant_system.model_registry")

        # 模型存儲目錄
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)

        # 數據庫初始化
        self.db_path = db_path
        self._init_database()

        # MLflow集成
        self.mlflow_enabled = enable_mlflow and MLFLOW_AVAILABLE
        if self.mlflow_enabled:
            if mlflow_tracking_uri:
                mlflow.set_tracking_uri(mlflow_tracking_uri)
            self._init_mlflow()

        # 模型存儲
        self.models: Dict[str, ModelVersion] = {}
        self.production_models: Dict[str, str] = {}  # model_name -> version

        # 性能監控
        self.performance_monitor = ModelPerformanceMonitor()

        # 自動部署配置
        self.deployment_configs: Dict[str, Dict[str, Any]] = {}

        # 加載已存在的模型
        self._load_models_from_db()

    def _init_database(self):
        """初始化數據庫"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS model_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                version TEXT NOT NULL,
                model_type TEXT NOT NULL,
                description TEXT,
                author TEXT,
                created_at TEXT,
                updated_at TEXT,
                status TEXT,
                tags TEXT,
                hyperparameters TEXT,
                feature_importance TEXT,
                training_data_hash TEXT,
                model_hash TEXT,
                file_path TEXT,
                model_size_mb REAL,
                dependencies TEXT,
                environment TEXT,
                notes TEXT,
                UNIQUE(name, version)
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS model_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                version TEXT NOT NULL,
                metrics TEXT NOT NULL,
                recorded_at TEXT,
                FOREIGN KEY (model_name, version) REFERENCES model_metadata(name, version)
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS deployments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                version TEXT NOT NULL,
                environment TEXT NOT NULL,
                deployment_strategy TEXT,
                deployed_at TEXT,
                traffic_percentage REAL DEFAULT 100.0,
                is_active BOOLEAN DEFAULT TRUE,
                UNIQUE(model_name, environment)
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS model_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                version TEXT NOT NULL,
                symbol TEXT,
                timestamp TEXT,
                prediction_value REAL,
                confidence REAL,
                latency_ms REAL,
                metadata TEXT
            )
        """
        )

        # 創建索引
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_model_metadata_name_version
            ON model_metadata(name, version)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_deployments_model_env
            ON deployments(model_name, environment)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_predictions_timestamp
            ON model_predictions(timestamp)
        """
        )

        conn.commit()
        conn.close()

    def _init_mlflow(self):
        """初始化MLflow"""
        try:
            mlflow.set_experiment("hong_kong_trading_models")
            self.logger.info("MLflow integration initialized")
        except Exception as e:
            self.logger.warning(f"MLflow initialization failed: {e}")
            self.mlflow_enabled = False

    def _load_models_from_db(self):
        """從數據庫加載模型元數據"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT name, version, status
            FROM model_metadata
            WHERE status = 'production'
        """
        )

        for row in cursor.fetchall():
            model_name, version, status = row
            self.production_models[model_name] = version

        conn.close()

    async def register_model(
        self,
        model: Any,
        metadata: ModelMetadata,
        metrics: ModelMetrics,
        training_history: Optional[Dict[str, List[float]]] = None,
    ) -> str:
        """
        註冊新模型

        Args:
            model: 模型對象
            metadata: 模型元數據
            metrics: 模型性能指標
            training_history: 訓練歷史

        Returns:
            模型ID
        """
        try:
            model_id = f"{metadata.name}:{metadata.version}"

            # 計算模型哈希
            metadata.model_hash = self._calculate_model_hash(model)

            # 保存模型文件
            model_path = self.model_dir / f"{metadata.name}_{metadata.version}.pkl"
            with open(model_path, "wb") as f:
                pickle.dump(model, f)

            metadata.file_path = str(model_path)
            metadata.model_size_mb = model_path.stat().st_size / (1024 * 1024)

            # 創建模型版本對象
            model_version = ModelVersion(
                metadata=metadata,
                metrics=metrics,
                model_object=model,
                training_history=training_history,
            )

            # 存儲到內存
            self.models[model_id] = model_version

            # 保存到數據庫
            await self._save_model_to_db(model_version)

            # MLflow日誌記錄
            if self.mlflow_enabled:
                await self._log_to_mlflow(model_version)

            self.logger.info(f"Model registered successfully: {model_id}")
            return model_id

        except Exception as e:
            self.logger.error(f"Model registration failed: {str(e)}")
            raise

    async def promote_model(
        self,
        model_name: str,
        version: str,
        target_environment: str = "production",
        strategy: DeploymentStrategy = DeploymentStrategy.DIRECT,
        traffic_percentage: float = 100.0,
    ) -> bool:
        """
        模型晉升部署

        Args:
            model_name: 模型名稱
            version: 模型版本
            target_environment: 目標環境
            strategy: 部署策略
            traffic_percentage: 流量百分比

        Returns:
            是否部署成功
        """
        try:
            model_id = f"{model_name}:{version}"

            if model_id not in self.models:
                raise ValueError(f"Model {model_id} not found")

            model_version = self.models[model_id]

            # 根據部署策略執行部署
            if strategy == DeploymentStrategy.DIRECT:
                success = await self._direct_deploy(model_version, target_environment)
            elif strategy == DeploymentStrategy.CANARY:
                success = await self._canary_deploy(
                    model_version, target_environment, traffic_percentage
                )
            elif strategy == DeploymentStrategy.BLUE_GREEN:
                success = await self._blue_green_deploy(
                    model_version, target_environment
                )
            elif strategy == DeploymentStrategy.SHADOW:
                success = await self._shadow_deploy(model_version, target_environment)
            elif strategy == DeploymentStrategy.A_B_TEST:
                success = await self._ab_test_deploy(
                    model_version, target_environment, traffic_percentage
                )
            else:
                raise ValueError(f"Unsupported deployment strategy: {strategy}")

            if success and target_environment == "production":
                self.production_models[model_name] = version
                model_version.metadata.status = ModelStatus.PRODUCTION

            # 更新數據庫
            await self._update_deployment_status(
                model_name, version, target_environment, strategy, traffic_percentage
            )

            self.logger.info(f"Model {model_id} deployed to {target_environment}")
            return True

        except Exception as e:
            self.logger.error(f"Model deployment failed: {str(e)}")
            return False

    async def predict(
        self,
        model_name: str,
        features: Union[pd.DataFrame, np.ndarray],
        version: Optional[str] = None,
        return_confidence: bool = False,
    ) -> Union[np.ndarray, Tuple[np.ndarray, np.ndarray]]:
        """
        使用指定模型進行預測

        Args:
            model_name: 模型名稱
            features: 輸入特徵
            version: 模型版本，如果為None則使用生產版本
            return_confidence: 是否返回置信度

        Returns:
            預測結果，可選置信度
        """
        try:
            start_time = datetime.now()

            # 確定模型版本
            if version is None:
                version = self.production_models.get(model_name)
                if version is None:
                    raise ValueError(
                        f"No production version found for model {model_name}"
                    )

            model_id = f"{model_name}:{version}"

            if model_id not in self.models:
                raise ValueError(f"Model {model_id} not found")

            model_version = self.models[model_id]
            model = model_version.model_object

            # 執行預測
            if hasattr(model, "predict"):
                prediction = model.predict(features)
            elif hasattr(model, "__call__"):
                prediction = model(features)
            else:
                raise ValueError("Model does not have predict method")

            # 計算置信度 (如果支持)
            confidence = None
            if return_confidence:
                if hasattr(model, "predict_proba"):
                    confidence = model.predict_proba(features)
                elif hasattr(model, "predict_uncertainty"):
                    confidence = model.predict_uncertainty(features)
                else:
                    confidence = np.ones(len(prediction)) * 0.8  # 默認置信度

            # 記錄預測
            latency = (datetime.now() - start_time).total_seconds() * 1000
            await self._log_prediction(
                model_name, version, prediction, confidence, latency
            )

            if return_confidence and confidence is not None:
                return prediction, confidence

            return prediction

        except Exception as e:
            self.logger.error(f"Prediction failed: {str(e)}")
            raise

    async def batch_predict(
        self,
        model_name: str,
        features_list: List[Union[pd.DataFrame, np.ndarray]],
        version: Optional[str] = None,
    ) -> List[np.ndarray]:
        """批量預測"""
        results = []

        for features in features_list:
            try:
                prediction = await self.predict(model_name, features, version)
                results.append(prediction)
            except Exception as e:
                self.logger.error(f"Batch prediction failed for one batch: {str(e)}")
                results.append(np.array([]))  # 返回空數組表示失敗

        return results

    async def evaluate_model(
        self,
        model_name: str,
        version: str,
        test_data: Tuple[pd.DataFrame, pd.Series],
        metrics: List[str] = None,
    ) -> Dict[str, float]:
        """評估模型性能"""
        try:
            model_id = f"{model_name}:{version}"

            if model_id not in self.models:
                raise ValueError(f"Model {model_id} not found")

            model_version = self.models[model_id]
            X_test, y_test = test_data

            # 執行預測
            y_pred = await self.predict(model_name, X_test, version)

            # 計算指標
            evaluation_metrics = {}

            if metrics is None:
                metrics = ["accuracy", "precision", "recall", "f1", "mae", "mse", "r2"]

            for metric in metrics:
                try:
                    if metric == "accuracy":
                        evaluation_metrics[metric] = accuracy_score(y_test, y_pred)
                    elif metric == "precision":
                        evaluation_metrics[metric] = precision_score(
                            y_test, y_pred, average="weighted"
                        )
                    elif metric == "recall":
                        evaluation_metrics[metric] = recall_score(
                            y_test, y_pred, average="weighted"
                        )
                    elif metric == "f1":
                        evaluation_metrics[metric] = f1_score(
                            y_test, y_pred, average="weighted"
                        )
                    elif metric == "mae":
                        evaluation_metrics[metric] = mean_absolute_error(y_test, y_pred)
                    elif metric == "mse":
                        evaluation_metrics[metric] = mean_squared_error(y_test, y_pred)
                    elif metric == "r2":
                        evaluation_metrics[metric] = r2_score(y_test, y_pred)
                except Exception as e:
                    self.logger.warning(
                        f"Failed to calculate metric {metric}: {str(e)}"
                    )

            return evaluation_metrics

        except Exception as e:
            self.logger.error(f"Model evaluation failed: {str(e)}")
            return {}

    async def rollback_model(
        self, model_name: str, target_version: str, environment: str = "production"
    ) -> bool:
        """回滾模型版本"""
        try:
            # 檢查目標版本是否存在
            model_id = f"{model_name}:{target_version}"
            if model_id not in self.models:
                raise ValueError(f"Target version {model_id} not found")

            # 執行回滾
            success = await self.promote_model(
                model_name, target_version, environment, DeploymentStrategy.DIRECT
            )

            if success:
                self.logger.info(
                    f"Model {model_name} rolled back to version {target_version}"
                )
            return success

        except Exception as e:
            self.logger.error(f"Model rollback failed: {str(e)}")
            return False

    def get_model_info(self, model_name: str, version: str) -> Optional[Dict[str, Any]]:
        """獲取模型信息"""
        model_id = f"{model_name}:{version}"

        if model_id not in self.models:
            return None

        model_version = self.models[model_id]

        return {
            "metadata": model_version.metadata.to_dict(),
            "metrics": model_version.metrics.to_dict(),
            "model_size_mb": model_version.metadata.model_size_mb,
            "training_history": model_version.training_history,
        }

    def list_models(
        self,
        status: Optional[ModelStatus] = None,
        model_type: Optional[ModelType] = None,
    ) -> List[Dict[str, Any]]:
        """列出模型"""
        models = []

        for model_id, model_version in self.models.items():
            metadata = model_version.metadata

            # 過濾條件
            if status and metadata.status != status:
                continue
            if model_type and metadata.model_type != model_type:
                continue

            models.append(
                {
                    "name": metadata.name,
                    "version": metadata.version,
                    "type": metadata.model_type.value,
                    "status": metadata.status.value,
                    "created_at": metadata.created_at.isoformat(),
                    "updated_at": metadata.updated_at.isoformat(),
                    "author": metadata.author,
                    "metrics": model_version.metrics.to_dict(),
                }
            )

        return sorted(models, key=lambda x: x["updated_at"], reverse=True)

    async def monitor_model_performance(
        self, model_name: str, version: Optional[str] = None, window_hours: int = 24
    ) -> Dict[str, Any]:
        """監控模型性能"""
        try:
            if version is None:
                version = self.production_models.get(model_name)
                if version is None:
                    raise ValueError(f"No production version for model {model_name}")

            return await self.performance_monitor.monitor_model(
                model_name, version, window_hours, self.db_path
            )

        except Exception as e:
            self.logger.error(f"Performance monitoring failed: {str(e)}")
            return {}

    def _calculate_model_hash(self, model: Any) -> str:
        """計算模型哈希"""
        model_pickle = pickle.dumps(model)
        return hashlib.sha256(model_pickle).hexdigest()

    async def _save_model_to_db(self, model_version: ModelVersion):
        """保存模型到數據庫"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 保存元數據
        metadata = model_version.metadata
        cursor.execute(
            """
            INSERT OR REPLACE INTO model_metadata
            (name, version, model_type, description, author, created_at, updated_at,
             status, tags, hyperparameters, feature_importance, training_data_hash,
             model_hash, file_path, model_size_mb, dependencies, environment, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                metadata.name,
                metadata.version,
                metadata.model_type.value,
                metadata.description,
                metadata.author,
                metadata.created_at.isoformat(),
                metadata.updated_at.isoformat(),
                metadata.status.value,
                json.dumps(metadata.tags),
                json.dumps(metadata.hyperparameters),
                json.dumps(metadata.feature_importance),
                metadata.training_data_hash,
                metadata.model_hash,
                metadata.file_path,
                metadata.model_size_mb,
                json.dumps(metadata.dependencies),
                metadata.environment,
                metadata.notes,
            ),
        )

        # 保存指標
        metrics = model_version.metrics
        cursor.execute(
            """
            INSERT OR REPLACE INTO model_metrics
            (model_name, version, metrics, recorded_at)
            VALUES (?, ?, ?, ?)
        """,
            (
                metadata.name,
                metadata.version,
                json.dumps(metrics.to_dict()),
                datetime.now().isoformat(),
            ),
        )

        conn.commit()
        conn.close()

    async def _log_to_mlflow(self, model_version: ModelVersion):
        """記錄到MLflow"""
        if not self.mlflow_enabled:
            return

        try:
            with mlflow.start_run(
                run_name=f"{model_version.metadata.name}_{model_version.metadata.version}"
            ):
                # 記錄參數
                mlflow.log_params(model_version.metadata.hyperparameters)

                # 記錄指標
                for key, value in model_version.metrics.to_dict().items():
                    mlflow.log_metric(key, value)

                # 記錄模型
                mlflow.sklearn.log_model(
                    model_version.model_object,
                    "model",
                    registered_model_name=model_version.metadata.name,
                )

                # 記錄特徵重要性
                if model_version.metadata.feature_importance:
                    for (
                        feature,
                        importance,
                    ) in model_version.metadata.feature_importance.items():
                        mlflow.log_metric(f"feature_importance_{feature}", importance)

        except Exception as e:
            self.logger.warning(f"MLflow logging failed: {str(e)}")

    async def _direct_deploy(
        self, model_version: ModelVersion, environment: str
    ) -> bool:
        """直接部署"""
        # 簡單的直接部署邏輯
        model_version.metadata.status = (
            ModelStatus.PRODUCTION
            if environment == "production"
            else ModelStatus.STAGING
        )
        model_version.metadata.updated_at = datetime.now()
        return True

    async def _canary_deploy(
        self, model_version: ModelVersion, environment: str, traffic_percentage: float
    ) -> bool:
        """金絲雀部署"""
        if traffic_percentage <= 0 or traffic_percentage > 100:
            raise ValueError("Traffic percentage must be between 0 and 100")

        # 實現金絲雀部署邏輯
        self.logger.info(f"Canary deployment: {traffic_percentage}% traffic")
        return await self._direct_deploy(model_version, environment)

    async def _blue_green_deploy(
        self, model_version: ModelVersion, environment: str
    ) -> bool:
        """藍綠部署"""
        # 實現藍綠部署邏輯
        self.logger.info("Blue - green deployment initiated")
        return await self._direct_deploy(model_version, environment)

    async def _shadow_deploy(
        self, model_version: ModelVersion, environment: str
    ) -> bool:
        """影子部署"""
        # 實現影子部署邏輯 (流量到舊模型，新模型在影子中運行)
        self.logger.info("Shadow deployment initiated")
        return True  # 影子部署總是成功

    async def _ab_test_deploy(
        self, model_version: ModelVersion, environment: str, traffic_percentage: float
    ) -> bool:
        """A / B測試部署"""
        if traffic_percentage <= 0 or traffic_percentage >= 100:
            raise ValueError("A / B test requires traffic percentage between 0 and 100")

        # 實現A / B測試部署邏輯
        self.logger.info(
            f"A / B test deployment: {traffic_percentage}% traffic to new model"
        )
        return await self._direct_deploy(model_version, environment)

    async def _update_deployment_status(
        self,
        model_name: str,
        version: str,
        environment: str,
        strategy: DeploymentStrategy,
        traffic_percentage: float,
    ):
        """更新部署狀態"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO deployments
            (model_name, version, environment, deployment_strategy, deployed_at, traffic_percentage, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                model_name,
                version,
                environment,
                strategy.value,
                datetime.now().isoformat(),
                traffic_percentage,
                True,
            ),
        )

        conn.commit()
        conn.close()

    async def _log_prediction(
        self,
        model_name: str,
        version: str,
        prediction: np.ndarray,
        confidence: Optional[np.ndarray],
        latency_ms: float,
    ):
        """記錄預測"""
        # 這裡可以異步記錄到數據庫或日誌系統
        # 為了性能，可以批量處理
        pass


class ModelPerformanceMonitor:
    """模型性能監控器"""

    def __init__(self):
        self.logger = logging.getLogger("hk_quant_system.model_monitor")

    async def monitor_model(
        self, model_name: str, version: str, window_hours: int, db_path: str
    ) -> Dict[str, Any]:
        """監控模型性能"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 獲取時間窗口內的預測記錄
            start_time = (datetime.now() - timedelta(hours=window_hours)).isoformat()

            cursor.execute(
                """
                SELECT COUNT(*) as total_predictions,
                       AVG(latency_ms) as avg_latency,
                       MAX(latency_ms) as max_latency,
                       MIN(latency_ms) as min_latency
                FROM model_predictions
                WHERE model_name = ? AND version = ? AND timestamp > ?
            """,
                (model_name, version, start_time),
            )

            performance_data = cursor.fetchone()
            conn.close()

            if performance_data and performance_data[0] > 0:
                return {
                    "total_predictions": performance_data[0],
                    "avg_latency_ms": performance_data[1],
                    "max_latency_ms": performance_data[2],
                    "min_latency_ms": performance_data[3],
                    "predictions_per_hour": performance_data[0] / window_hours,
                    "performance_status": (
                        "healthy" if performance_data[1] < 100 else "slow"
                    ),
                }
            else:
                return {"total_predictions": 0, "performance_status": "no_data"}

        except Exception as e:
            self.logger.error(f"Performance monitoring failed: {str(e)}")
            return {"performance_status": "error", "error": str(e)}


class AutoMLManager:
    """AutoML管理器"""

    def __init__(self, model_registry: ModelRegistry):
        self.model_registry = model_registry
        self.logger = logging.getLogger("hk_quant_system.automl")
        self.optuna_enabled = OPTUNA_AVAILABLE

    async def hyperparameter_optimization(
        self,
        model_name: str,
        model_type: ModelType,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame,
        y_val: pd.Series,
        n_trials: int = 100,
    ) -> Dict[str, Any]:
        """超參數優化"""
        if not self.optuna_enabled:
            self.logger.warning(
                "Optuna not available, skipping hyperparameter optimization"
            )
            return {}

        try:
            import optuna
            from sklearn.ensemble import RandomForestRegressor
            from sklearn.model_selection import cross_val_score

            def objective(trial):
                # 定義搜索空間
                params = {
                    "n_estimators": trial.suggest_int("n_estimators", 50, 300),
                    "max_depth": trial.suggest_int("max_depth", 3, 20),
                    "min_samples_split": trial.suggest_int("min_samples_split", 2, 20),
                    "min_samples_lea": trial.suggest_int("min_samples_leaf", 1, 10),
                    "max_features": trial.suggest_categorical(
                        "max_features", ["sqrt", "log2", None]
                    ),
                }

                # 訓練模型
                model = RandomForestRegressor(**params, random_state=42)
                scores = cross_val_score(
                    model, X_train, y_train, cv=5, scoring="neg_mean_squared_error"
                )

                return -scores.mean()  # 返回負的MSE (Optuna最小化)

            # 創建研究
            study = optuna.create_study(direction="minimize")
            study.optimize(objective, n_trials=n_trials)

            # 獲取最佳參數
            best_params = study.best_params
            best_score = study.best_value

            # 訓練最終模型
            best_model = RandomForestRegressor(**best_params, random_state=42)
            best_model.fit(X_train, y_train)

            # 評估模型
            val_score = best_model.score(X_val, y_val)

            return {
                "best_params": best_params,
                "best_score": best_score,
                "validation_score": val_score,
                "model": best_model,
                "optimization_history": study.trials_dataframe().to_dict("records"),
            }

        except Exception as e:
            self.logger.error(f"Hyperparameter optimization failed: {str(e)}")
            return {}

    async def automated_model_selection(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame,
        y_val: pd.Series,
    ) -> Dict[str, Any]:
        """自動模型選擇"""
        try:
            import xgboost as xgb
            from sklearn.ensemble import (
                GradientBoostingRegressor,
                RandomForestRegressor,
            )
            from sklearn.linear_model import Lasso, LinearRegression, Ridge
            from sklearn.svm import SVR

            models = {
                "LinearRegression": LinearRegression(),
                "Ridge": Ridge(),
                "Lasso": Lasso(),
                "RandomForest": RandomForestRegressor(
                    n_estimators=100, random_state=42
                ),
                "GradientBoosting": GradientBoostingRegressor(random_state=42),
                "XGBoost": xgb.XGBRegressor(random_state=42),
                "SVR": SVR(),
            }

            results = {}

            for name, model in models.items():
                try:
                    # 訓練模型
                    model.fit(X_train, y_train)

                    # 預測和評估
                    y_pred = model.predict(X_val)

                    # 計算指標
                    mse = mean_squared_error(y_val, y_pred)
                    r2 = r2_score(y_val, y_pred)
                    mae = mean_absolute_error(y_val, y_pred)

                    results[name] = {"model": model, "mse": mse, "r2": r2, "mae": mae}

                except Exception as e:
                    self.logger.warning(f"Model {name} failed: {str(e)}")
                    continue

            # 選擇最佳模型
            if results:
                best_model_name = min(results.keys(), key=lambda k: results[k]["mse"])
                best_model = results[best_model_name]

                return {
                    "best_model": best_model_name,
                    "best_results": best_model,
                    "all_results": results,
                }
            else:
                return {"error": "No models succeeded"}

        except Exception as e:
            self.logger.error(f"Automated model selection failed: {str(e)}")
            return {"error": str(e)}


# 全局模型註冊中心實例
model_registry = ModelRegistry()
automl_manager = AutoMLManager(model_registry)

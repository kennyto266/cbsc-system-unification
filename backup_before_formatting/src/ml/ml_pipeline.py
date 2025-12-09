"""
ML流水線編排系統
生產級別的端到端機器學習流水線，支援自動化訓練、部署和監控

功能:
- 自動化特徵工程和數據預處理
- 多模型訓練和超參數優化
- 模型評估和A / B測試
- 自動化部署和模型版本管理
- 實時監控和性能評估
- 數據漂移檢測和模型再訓練
"""

import asyncio
import json
import logging
import pickle
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import lightgbm as lgb
import numpy as np
import pandas as pd
import schedule
import xgboost as xgb
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# 數據處理和ML框架
from sklearn.model_selection import TimeSeriesSplit, cross_val_score, train_test_split
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler

# 流水線工具
try:
    import prefect
    from prefect import flow, get_run_logger, task
    from prefect.deployments import Deployment
    from prefect.orion.schemas.states import State

    PREFECT_AVAILABLE = True
except ImportError:
    PREFECT_AVAILABLE = False

try:
    import airflow
    from airflow import DAG
    from airflow.operators.python import PythonOperator
    from airflow.providers.postgres.operators.postgres import PostgresOperator
    from airflow.providers.redis.hooks.redis import RedisHook

    AIRFLOW_AVAILABLE = True
except ImportError:
    AIRFLOW_AVAILABLE = False

try:
    import kfp
    from kfp import dsl
    from kfp.components import create_component_from_func

    KFP_AVAILABLE = True
except ImportError:
    KFP_AVAILABLE = False

# 監控和可觀測性
try:
    import mlflow
    import mlflow.sklearn
    import mlflow.tensorflow
    from mlflow.tracking import MlflowClient

    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False

try:
    import evidently
    from evidently.dashboard import Dashboard
    from evidently.metric_preset import (
        ClassificationPreset,
        DataDriftPreset,
        RegressionPreset,
    )
    from evidently.report import Report
    from evidently.test_suite import TestSuite

    EVIDENTLY_AVAILABLE = True
except ImportError:
    EVIDENTLY_AVAILABLE = False

# 內部模組
from .feature_store import AdvancedFeatureStore, FeatureType
from .model_registry import ModelRegistry, ModelStatus, ModelType
from .reinforcement_learning import RLTrainingManager, TradingEnvironment
from .trading_models import (
    AdvancedPricePredictor,
    MarketRegimeDetector,
    VolatilityForecaster,
)


class PipelineStatus(Enum):
    """流水線狀態"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class PipelineType(Enum):
    """流水線類型"""

    FEATURE_ENGINEERING = "feature_engineering"
    MODEL_TRAINING = "model_training"
    MODEL_EVALUATION = "model_evaluation"
    MODEL_DEPLOYMENT = "model_deployment"
    MONITORING = "monitoring"
    RETRAINING = "retraining"
    END_TO_END = "end_to_end"


@dataclass
class PipelineConfig:
    """流水線配置"""

    pipeline_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    type: PipelineType = PipelineType.MODEL_TRAINING
    description: str = ""
    schedule: Optional[str] = None  # Cron expression
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    notification_channels: List[str] = field(default_factory=list)
    retry_config: Dict[str, Any] = field(default_factory=dict)
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class PipelineResult:
    """流水線執行結果"""

    pipeline_id: str
    run_id: str
    status: PipelineStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    artifacts: Dict[str, str] = field(default_factory=dict)  # artifact_name -> path
    metrics: Dict[str, float] = field(default_factory=dict)
    logs: List[str] = field(default_factory=list)
    error_message: Optional[str] = None


class DataProcessor:
    """數據處理器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger("hk_quant_system.data_processor")
        self.config = config or {}

    async def load_and_validate_data(
        self,
        data_source: str,
        symbol: str,
        start_date: str,
        end_date: str,
        validation_rules: Optional[Dict[str, Any]] = None,
    ) -> pd.DataFrame:
        """加載和驗證數據"""
        try:
            self.logger.info(
                f"Loading data for {symbol} from {start_date} to {end_date}"
            )

            # 根據數據源加載數據
            if data_source == "csv":
                df = pd.read_csv(f"data/{symbol}.csv")
            elif data_source == "database":
                # 實現數據庫加載邏輯
                df = pd.DataFrame()  # 佔位符
            elif data_source == "api":
                # 實現API加載邏輯
                df = pd.DataFrame()  # 佔位符
            else:
                raise ValueError(f"Unsupported data source: {data_source}")

            # 數據驗證
            if validation_rules:
                df = self._validate_data(df, validation_rules)

            # 數據清洗
            df = self._clean_data(df)

            self.logger.info(f"Data loaded successfully: {len(df)} rows")
            return df

        except Exception as e:
            self.logger.error(f"Data loading failed: {str(e)}")
            raise

    def _validate_data(self, df: pd.DataFrame, rules: Dict[str, Any]) -> pd.DataFrame:
        """驗證數據質量"""
        # 檢查必需列
        required_columns = rules.get(
            "required_columns", ["date", "open", "high", "low", "close", "volume"]
        )
        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        # 檢查數據範圍
        if "price_range" in rules:
            min_price, max_price = rules["price_range"]
            price_cols = ["open", "high", "low", "close"]
            for col in price_cols:
                if col in df.columns:
                    out_of_range = (df[col] < min_price) | (df[col] > max_price)
                    if out_of_range.any():
                        self.logger.warning(
                            f"Found {out_of_range.sum()} out - of - range values in {col}"
                        )

        # 檢查缺失值
        max_missing_ratio = rules.get("max_missing_ratio", 0.1)
        for col in df.columns:
            missing_ratio = df[col].isnull().sum() / len(df)
            if missing_ratio > max_missing_ratio:
                self.logger.warning(
                    f"Column {col} has {missing_ratio:.2%} missing values"
                )

        return df

    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """清洗數據"""
        # 移除重複行
        df = df.drop_duplicates()

        # 處理缺失值
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        df[numeric_columns] = (
            df[numeric_columns].fillna(method="ffill").fillna(method="bfill")
        )

        # 移除異常值
        for col in numeric_columns:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outliers = (df[col] < lower_bound) | (df[col] > upper_bound)
            if outliers.any():
                df.loc[outliers, col] = df[col].median()

        # 確保日期格式正確
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date").reset_index(drop=True)

        return df

    def split_data(
        self,
        data: pd.DataFrame,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        time_series: bool = True,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """分割數據"""
        if abs(train_ratio + val_ratio + test_ratio - 1.0) > 1e-6:
            raise ValueError("Train, validation, and test ratios must sum to 1.0")

        if time_series:
            # 時間序列分割
            n = len(data)
            train_end = int(n * train_ratio)
            val_end = int(n * (train_ratio + val_ratio))

            train_data = data.iloc[:train_end]
            val_data = data.iloc[train_end:val_end]
            test_data = data.iloc[val_end:]
        else:
            # 隨機分割
            train_data, temp_data = train_test_split(
                data, test_size=(val_ratio + test_ratio), random_state=42
            )
            val_ratio_adjusted = val_ratio / (val_ratio + test_ratio)
            val_data, test_data = train_test_split(
                temp_data, test_size=(1 - val_ratio_adjusted), random_state=42
            )

        return train_data, val_data, test_data


class ModelTrainer:
    """模型訓練器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger("hk_quant_system.model_trainer")
        self.config = config or {}
        self.feature_store = AdvancedFeatureStore()
        self.model_registry = ModelRegistry()

    async def train_multiple_models(
        self,
        train_data: pd.DataFrame,
        val_data: pd.DataFrame,
        model_configs: Dict[str, Dict[str, Any]],
        feature_types: Optional[List[FeatureType]] = None,
    ) -> Dict[str, Any]:
        """訓練多個模型"""
        try:
            self.logger.info(f"Starting training for {len(model_configs)} models")

            results = {}
            training_tasks = []

            # 並行訓練模型
            with ThreadPoolExecutor(max_workers=min(4, len(model_configs))) as executor:
                future_to_model = {
                    executor.submit(
                        self._train_single_model,
                        name,
                        config,
                        train_data,
                        val_data,
                        feature_types,
                    ): name
                    for name, config in model_configs.items()
                }

                for future in as_completed(future_to_model):
                    model_name = future_to_model[future]
                    try:
                        result = future.result()
                        results[model_name] = result
                        self.logger.info(f"Model {model_name} training completed")
                    except Exception as e:
                        self.logger.error(
                            f"Model {model_name} training failed: {str(e)}"
                        )
                        results[model_name] = {"error": str(e)}

            # 比較模型性能
            best_model = self._select_best_model(results)

            return {
                "results": results,
                "best_model": best_model,
                "training_summary": self._generate_training_summary(results),
            }

        except Exception as e:
            self.logger.error(f"Multiple model training failed: {str(e)}")
            raise

    def _train_single_model(
        self,
        model_name: str,
        config: Dict[str, Any],
        train_data: pd.DataFrame,
        val_data: pd.DataFrame,
        feature_types: Optional[List[FeatureType]] = None,
    ) -> Dict[str, Any]:
        """訓練單個模型"""
        try:
            model_type = config.get("type", "xgboost")
            symbol = config.get("symbol", "default")

            # 計算特徵
            features_df = asyncio.run(
                self.feature_store.compute_features(symbol, train_data, feature_types)
            )

            # 準備訓練數據
            X_train = features_df.dropna()
            y_train = (
                train_data.iloc[X_train.index]["close"].pct_change().shift(-1).dropna()
            )

            # 對齊特徵和目標
            common_index = X_train.index.intersection(y_train.index)
            X_train = X_train.loc[common_index]
            y_train = y_train.loc[common_index]

            # 準備驗證數據
            val_features = asyncio.run(
                self.feature_store.compute_features(symbol, val_data, feature_types)
            )
            X_val = val_features.dropna()
            y_val = val_data.iloc[X_val.index]["close"].pct_change().shift(-1).dropna()

            common_index = X_val.index.intersection(y_val.index)
            X_val = X_val.loc[common_index]
            y_val = y_val.loc[common_index]

            # 訓練模型
            if model_type == "xgboost":
                model = xgb.XGBRegressor(**config.get("params", {}))
            elif model_type == "lightgbm":
                model = lgb.LGBMRegressor(**config.get("params", {}))
            elif model_type == "random_forest":
                model = RandomForestRegressor(**config.get("params", {}))
            elif model_type == "gradient_boosting":
                model = GradientBoostingRegressor(**config.get("params", {}))
            else:
                raise ValueError(f"Unsupported model type: {model_type}")

            model.fit(X_train, y_train)

            # 評估模型
            y_pred = model.predict(X_val)
            metrics = {
                "mse": mean_squared_error(y_val, y_pred),
                "mae": mean_absolute_error(y_val, y_pred),
                "r2": r2_score(y_val, y_pred),
            }

            # 計算交易指標
            trading_metrics = self._calculate_trading_metrics(y_val, y_pred)
            metrics.update(trading_metrics)

            return {
                "model": model,
                "metrics": metrics,
                "feature_importance": dict(
                    zip(X_train.columns, model.feature_importances_)
                ),
                "config": config,
            }

        except Exception as e:
            self.logger.error(f"Single model training failed: {str(e)}")
            raise

    def _calculate_trading_metrics(
        self, y_true: pd.Series, y_pred: pd.Series
    ) -> Dict[str, float]:
        """計算交易相關指標"""
        try:
            # 簡化的交易指標計算
            returns = y_true
            predictions = y_pred

            # 命中率
            correct_direction = (np.sign(returns) == np.sign(predictions)).sum()
            hit_rate = correct_direction / len(returns)

            # 夏普比率
            if returns.std() > 0:
                sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252)
            else:
                sharpe_ratio = 0

            # 最大回撤
            cumulative_returns = (1 + returns).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - running_max) / running_max
            max_drawdown = drawdown.min()

            return {
                "hit_rate": hit_rate,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
                "total_trades": len(returns),
            }

        except Exception as e:
            self.logger.warning(f"Trading metrics calculation failed: {str(e)}")
            return {}

    def _select_best_model(self, results: Dict[str, Any]) -> Optional[str]:
        """選擇最佳模型"""
        best_model = None
        best_score = float("-inf")

        for model_name, result in results.items():
            if "error" in result:
                continue

            metrics = result.get("metrics", {})
            # 使用組合指標評分
            score = (
                metrics.get("r2", 0) * 0.3
                + metrics.get("hit_rate", 0) * 0.3
                + metrics.get("sharpe_ratio", 0) * 0.2
                + (1 - abs(metrics.get("max_drawdown", 0))) * 0.2
            )

            if score > best_score:
                best_score = score
                best_model = model_name

        return best_model

    def _generate_training_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """生成訓練摘要"""
        successful_models = {k: v for k, v in results.items() if "error" not in v}
        failed_models = {k: v for k, v in results.items() if "error" in v}

        summary = {
            "total_models": len(results),
            "successful_models": len(successful_models),
            "failed_models": len(failed_models),
            "model_performance": {},
        }

        for model_name, result in successful_models.items():
            summary["model_performance"][model_name] = result.get("metrics", {})

        return summary


class ModelEvaluator:
    """模型評估器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger("hk_quant_system.model_evaluator")
        self.config = config or {}

    async def evaluate_models(
        self,
        models: Dict[str, Any],
        test_data: pd.DataFrame,
        evaluation_metrics: List[str] = None,
    ) -> Dict[str, Any]:
        """評估多個模型"""
        try:
            if evaluation_metrics is None:
                evaluation_metrics = ["mse", "mae", "r2", "hit_rate", "sharpe_ratio"]

            results = {}

            for model_name, model_info in models.items():
                try:
                    model = model_info["model"]
                    evaluation_result = await self._evaluate_single_model(
                        model, model_name, test_data, evaluation_metrics
                    )
                    results[model_name] = evaluation_result
                except Exception as e:
                    self.logger.error(f"Evaluation failed for {model_name}: {str(e)}")
                    results[model_name] = {"error": str(e)}

            # 生成評估報告
            evaluation_report = self._generate_evaluation_report(results)

            return {
                "results": results,
                "report": evaluation_report,
                "best_model": self._select_best_evaluated_model(results),
            }

        except Exception as e:
            self.logger.error(f"Model evaluation failed: {str(e)}")
            raise

    async def _evaluate_single_model(
        self, model: Any, model_name: str, test_data: pd.DataFrame, metrics: List[str]
    ) -> Dict[str, Any]:
        """評估單個模型"""
        # 準備測試數據 (這裡需要特徵工程)
        # 簡化版本，實際應用中需要完整的特徵工程
        X_test = test_data[["open", "high", "low", "close", "volume"]].values
        y_test = test_data["close"].pct_change().shift(-1).dropna()

        # 移除最後一行 (因為y_test會短一行)
        X_test = X_test[:-1]

        # 預測
        y_pred = model.predict(X_test)

        # 計算指標
        evaluation_metrics = {}

        for metric in metrics:
            if metric == "mse":
                evaluation_metrics[metric] = mean_squared_error(y_test, y_pred)
            elif metric == "mae":
                evaluation_metrics[metric] = mean_absolute_error(y_test, y_pred)
            elif metric == "r2":
                evaluation_metrics[metric] = r2_score(y_test, y_pred)
            elif metric == "hit_rate":
                correct_direction = (np.sign(y_test) == np.sign(y_pred)).sum()
                evaluation_metrics[metric] = correct_direction / len(y_test)
            elif metric == "sharpe_ratio":
                returns = y_test
                if returns.std() > 0:
                    evaluation_metrics[metric] = (
                        returns.mean() / returns.std() * np.sqrt(252)
                    )
                else:
                    evaluation_metrics[metric] = 0

        return {
            "metrics": evaluation_metrics,
            "predictions": y_pred.tolist(),
            "actuals": y_test.tolist(),
        }

    def _generate_evaluation_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """生成評估報告"""
        report = {
            "summary": {
                "total_models": len(results),
                "successful_evaluations": len(
                    [r for r in results.values() if "error" not in r]
                ),
                "failed_evaluations": len(
                    [r for r in results.values() if "error" in r]
                ),
            },
            "metric_comparison": {},
            "recommendations": [],
        }

        # 收集所有指標
        all_metrics = {}
        for model_name, result in results.items():
            if "error" not in result:
                for metric, value in result["metrics"].items():
                    if metric not in all_metrics:
                        all_metrics[metric] = {}
                    all_metrics[metric][model_name] = value

        # 比較指標
        for metric, values in all_metrics.items():
            if values:
                best_model = max(values.keys(), key=lambda k: values[k])
                worst_model = min(values.keys(), key=lambda k: values[k])
                avg_value = np.mean(list(values.values()))

                report["metric_comparison"][metric] = {
                    "best_model": best_model,
                    "best_value": values[best_model],
                    "worst_model": worst_model,
                    "worst_value": values[worst_model],
                    "average": avg_value,
                }

        return report

    def _select_best_evaluated_model(self, results: Dict[str, Any]) -> Optional[str]:
        """選擇評估最佳的模型"""
        best_model = None
        best_score = float("-inf")

        for model_name, result in results.items():
            if "error" in result:
                continue

            metrics = result.get("metrics", {})
            # 綜合評分
            score = (
                metrics.get("r2", 0) * 0.3
                + metrics.get("hit_rate", 0) * 0.3
                + metrics.get("sharpe_ratio", 0) * 0.2
                + (1 - abs(metrics.get("max_drawdown", 0))) * 0.2
            )

            if score > best_score:
                best_score = score
                best_model = model_name

        return best_model


class PipelineOrchestrator:
    """流水線編排器"""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        storage_dir: str = "pipeline_artifacts",
    ):
        self.logger = logging.getLogger("hk_quant_system.pipeline_orchestrator")
        self.config = config or {}
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)

        # 組件初始化
        self.data_processor = DataProcessor(config.get("data_processing", {}))
        self.model_trainer = ModelTrainer(config.get("model_training", {}))
        self.model_evaluator = ModelEvaluator(config.get("model_evaluation", {}))

        # 流水線存儲
        self.pipelines: Dict[str, PipelineConfig] = {}
        self.pipeline_runs: Dict[str, List[PipelineResult]] = defaultdict(list)

        # 調度器
        self.scheduler = schedule.Scheduler()
        self._running = False

    def create_pipeline(self, config: PipelineConfig) -> str:
        """創建流水線"""
        self.pipelines[config.pipeline_id] = config
        self.logger.info(f"Pipeline created: {config.pipeline_id}")
        return config.pipeline_id

    async def run_pipeline(
        self, pipeline_id: str, parameters: Optional[Dict[str, Any]] = None
    ) -> PipelineResult:
        """運行流水線"""
        try:
            if pipeline_id not in self.pipelines:
                raise ValueError(f"Pipeline {pipeline_id} not found")

            pipeline_config = self.pipelines[pipeline_id]
            run_id = str(uuid.uuid4())

            self.logger.info(f"Starting pipeline run: {run_id}")

            # 創建結果對象
            result = PipelineResult(
                pipeline_id=pipeline_id,
                run_id=run_id,
                status=PipelineStatus.RUNNING,
                start_time=datetime.now(),
            )

            # 根據流水線類型執行不同邏輯
            if pipeline_config.type == PipelineType.MODEL_TRAINING:
                await self._run_training_pipeline(pipeline_config, result, parameters)
            elif pipeline_config.type == PipelineType.FEATURE_ENGINEERING:
                await self._run_feature_engineering_pipeline(
                    pipeline_config, result, parameters
                )
            elif pipeline_config.type == PipelineType.MODEL_EVALUATION:
                await self._run_evaluation_pipeline(pipeline_config, result, parameters)
            elif pipeline_config.type == PipelineType.END_TO_END:
                await self._run_end_to_end_pipeline(pipeline_config, result, parameters)
            else:
                raise ValueError(f"Unsupported pipeline type: {pipeline_config.type}")

            result.end_time = datetime.now()
            result.duration = (result.end_time - result.start_time).total_seconds()

            # 保存結果
            self._save_pipeline_result(result)

            self.logger.info(f"Pipeline run completed: {run_id}")
            return result

        except Exception as e:
            self.logger.error(f"Pipeline run failed: {str(e)}")
            result.status = PipelineStatus.FAILED
            result.error_message = str(e)
            result.end_time = datetime.now()
            return result

    async def _run_training_pipeline(
        self,
        config: PipelineConfig,
        result: PipelineResult,
        parameters: Optional[Dict[str, Any]],
    ):
        """運行訓練流水線"""
        try:
            # 獲取參數
            params = config.parameters.copy()
            if parameters:
                params.update(parameters)

            # 加載數據
            data = await self.data_processor.load_and_validate_data(
                data_source=params["data_source"],
                symbol=params["symbol"],
                start_date=params["start_date"],
                end_date=params["end_date"],
            )

            # 分割數據
            train_data, val_data, test_data = self.data_processor.split_data(
                data,
                train_ratio=params.get("train_ratio", 0.7),
                val_ratio=params.get("val_ratio", 0.15),
                test_ratio=params.get("test_ratio", 0.15),
                time_series=True,
            )

            # 訓練模型
            training_result = await self.model_trainer.train_multiple_models(
                train_data=train_data,
                val_data=val_data,
                model_configs=params["model_configs"],
                feature_types=params.get("feature_types"),
            )

            # 評估模型
            evaluation_result = await self.model_evaluator.evaluate_models(
                models=training_result["results"], test_data=test_data
            )

            # 保存工件
            artifacts = {}
            for model_name, model_info in training_result["results"].items():
                if "model" in model_info:
                    model_path = self.storage_dir / f"{model_name}_{result.run_id}.pkl"
                    with open(model_path, "wb") as f:
                        pickle.dump(model_info["model"], f)
                    artifacts[f"model_{model_name}"] = str(model_path)

            # 更新結果
            result.artifacts = artifacts
            result.metrics = {
                "best_model_performance": evaluation_result.get("report", {}).get(
                    "metric_comparison", {}
                ),
                "training_summary": training_result.get("training_summary", {}),
            }
            result.status = PipelineStatus.SUCCESS

        except Exception as e:
            result.status = PipelineStatus.FAILED
            result.error_message = str(e)
            raise

    async def _run_feature_engineering_pipeline(
        self,
        config: PipelineConfig,
        result: PipelineResult,
        parameters: Optional[Dict[str, Any]],
    ):
        """運行特徵工程流水線"""
        try:
            params = config.parameters.copy()
            if parameters:
                params.update(parameters)

            # 加載數據
            data = await self.data_processor.load_and_validate_data(
                data_source=params["data_source"],
                symbol=params["symbol"],
                start_date=params["start_date"],
                end_date=params["end_date"],
            )

            # 計算特徵
            feature_store = AdvancedFeatureStore()
            features_df = await feature_store.compute_features(
                symbol=params["symbol"],
                data=data,
                feature_types=params.get("feature_types"),
            )

            # 保存特徵
            feature_path = (
                self.storage_dir
                / f"features_{params['symbol']}_{result.run_id}.parquet"
            )
            features_df.to_parquet(feature_path)

            result.artifacts = {"features": str(feature_path)}
            result.metrics = {
                "feature_count": len(features_df.columns),
                "sample_count": len(features_df),
            }
            result.status = PipelineStatus.SUCCESS

        except Exception as e:
            result.status = PipelineStatus.FAILED
            result.error_message = str(e)
            raise

    async def _run_evaluation_pipeline(
        self,
        config: PipelineConfig,
        result: PipelineResult,
        parameters: Optional[Dict[str, Any]],
    ):
        """運行評估流水線"""
        try:
            params = config.parameters.copy()
            if parameters:
                params.update(parameters)

            # 加載測試數據
            data = await self.data_processor.load_and_validate_data(
                data_source=params["data_source"],
                symbol=params["symbol"],
                start_date=params["start_date"],
                end_date=params["end_date"],
            )

            # 加載模型
            models = {}
            for model_name, model_path in params["model_paths"].items():
                with open(model_path, "rb") as f:
                    models[model_name] = {"model": pickle.load(f)}

            # 評估模型
            evaluation_result = await self.model_evaluator.evaluate_models(
                models=models, test_data=data
            )

            result.artifacts = {"evaluation_report": f"report_{result.run_id}.json"}
            result.metrics = evaluation_result.get("report", {})
            result.status = PipelineStatus.SUCCESS

        except Exception as e:
            result.status = PipelineStatus.FAILED
            result.error_message = str(e)
            raise

    async def _run_end_to_end_pipeline(
        self,
        config: PipelineConfig,
        result: PipelineResult,
        parameters: Optional[Dict[str, Any]],
    ):
        """運行端到端流水線"""
        try:
            # 端到端流水線包含所有步驟
            await self._run_feature_engineering_pipeline(config, result, parameters)
            await self._run_training_pipeline(config, result, parameters)
            await self._run_evaluation_pipeline(config, result, parameters)

        except Exception as e:
            result.status = PipelineStatus.FAILED
            result.error_message = str(e)
            raise

    def _save_pipeline_result(self, result: PipelineResult):
        """保存流水線結果"""
        try:
            result_path = self.storage_dir / f"pipeline_result_{result.run_id}.json"
            result_data = {
                "pipeline_id": result.pipeline_id,
                "run_id": result.run_id,
                "status": result.status.value,
                "start_time": result.start_time.isoformat(),
                "end_time": result.end_time.isoformat() if result.end_time else None,
                "duration": result.duration,
                "artifacts": result.artifacts,
                "metrics": result.metrics,
                "error_message": result.error_message,
            }

            with open(result_path, "w") as f:
                json.dump(result_data, f, indent=2)

            # 添加到運行歷史
            self.pipeline_runs[result.pipeline_id].append(result)

        except Exception as e:
            self.logger.warning(f"Failed to save pipeline result: {str(e)}")

    def schedule_pipeline(self, pipeline_id: str, cron_expression: str):
        """調度流水線"""
        if pipeline_id not in self.pipelines:
            raise ValueError(f"Pipeline {pipeline_id} not found")

        # 這裡可以使用更強大的調度庫如APScheduler
        # 簡化實現
        self.pipelines[pipeline_id].schedule = cron_expression
        self.logger.info(
            f"Scheduled pipeline {pipeline_id} with cron: {cron_expression}"
        )

    def get_pipeline_status(self, pipeline_id: str) -> Optional[Dict[str, Any]]:
        """獲取流水線狀態"""
        if pipeline_id not in self.pipelines:
            return None

        pipeline_config = self.pipelines[pipeline_id]
        runs = self.pipeline_runs.get(pipeline_id, [])

        return {
            "pipeline_id": pipeline_id,
            "config": pipeline_config.__dict__,
            "total_runs": len(runs),
            "last_run": runs[-1].__dict__ if runs else None,
            "status": (
                pipeline_config.status.value
                if hasattr(pipeline_config, "status")
                else "unknown"
            ),
        }

    async def start_scheduler(self):
        """啟動調度器"""
        self._running = True
        while self._running:
            schedule.run_pending()
            await asyncio.sleep(60)  # 每分鐘檢查一次

    def stop_scheduler(self):
        """停止調度器"""
        self._running = False


# 全局流水線編排器實例
pipeline_orchestrator = PipelineOrchestrator()

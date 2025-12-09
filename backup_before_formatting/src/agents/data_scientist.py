"""
港股量化交易 AI Agent 系统 - 数据科学家Agent

负责机器学习模型开发、特征工程、数据挖掘和预测分析。
提供AI驱动的预测分析能力，支持多种机器学习算法。
"""

import asyncio
import logging
import os
import warnings
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.feature_selection import SelectKBest, f_regression, mutual_info_regression
from sklearn.linear_model import Lasso, LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, cross_val_score, train_test_split
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler
from sklearn.svm import SVR

from ..agents.base_agent import AgentConfig, BaseAgent
from ..agents.protocol import AgentProtocol, MessagePriority, MessageType
from ..core import SystemConfig, SystemConstants
from ..core.message_queue import Message, MessageQueue
from ..models.base import BaseModel, MarketData, TradingSignal


class ModelType(str, Enum):
    """模型类型"""

    LINEAR_REGRESSION = "linear_regression"
    RIDGE_REGRESSION = "ridge_regression"
    LASSO_REGRESSION = "lasso_regression"
    RANDOM_FOREST = "random_forest"
    GRADIENT_BOOSTING = "gradient_boosting"
    SUPPORT_VECTOR = "support_vector"
    NEURAL_NETWORK = "neural_network"


class FeatureType(str, Enum):
    """特征类型"""

    TECHNICAL_INDICATORS = "technical_indicators"
    PRICE_FEATURES = "price_features"
    VOLUME_FEATURES = "volume_features"
    MARKET_FEATURES = "market_features"
    SENTIMENT_FEATURES = "sentiment_features"
    MACRO_FEATURES = "macro_features"


@dataclass
class ModelPerformance(BaseModel):
    """模型性能指标"""

    model_id: str
    model_type: ModelType
    symbol: str
    target: str  # 预测目标：price, return, volatility等

    # 性能指标
    mse: float = 0.0
    rmse: float = 0.0
    mae: float = 0.0
    r2_score: float = 0.0
    cv_score: float = 0.0

    # 训练信息
    training_samples: int = 0
    feature_count: int = 0
    training_time: float = 0.0

    # 预测信息
    last_prediction: float = 0.0
    prediction_confidence: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class FeatureImportance(BaseModel):
    """特征重要性"""

    feature_name: str
    importance_score: float
    feature_type: FeatureType
    correlation: float = 0.0
    mutual_info: float = 0.0


@dataclass
class PredictionResult(BaseModel):
    """预测结果"""

    model_id: str
    symbol: str
    prediction: float
    confidence: float
    features_used: List[str]
    prediction_type: str  # price, return, volatility等
    timestamp: datetime = field(default_factory=datetime.now)


class FeatureEngineer:
    """特征工程器"""

    def __init__(self):
        self.logger = logging.getLogger(
            "hk_quant_system.data_scientist.feature_engineer"
        )
        self.scalers: Dict[str, Any] = {}

    def create_features(
        self, data: pd.DataFrame, symbol: str, feature_types: List[FeatureType] = None
    ) -> pd.DataFrame:
        """创建特征"""

        try:
            if feature_types is None:
                feature_types = [
                    FeatureType.TECHNICAL_INDICATORS,
                    FeatureType.PRICE_FEATURES,
                    FeatureType.VOLUME_FEATURES,
                ]

            features_df = data.copy()

            # 技术指标特征
            if FeatureType.TECHNICAL_INDICATORS in feature_types:
                features_df = self._add_technical_indicators(features_df)

            # 价格特征
            if FeatureType.PRICE_FEATURES in feature_types:
                features_df = self._add_price_features(features_df)

            # 成交量特征
            if FeatureType.VOLUME_FEATURES in feature_types:
                features_df = self._add_volume_features(features_df)

            # 市场特征
            if FeatureType.MARKET_FEATURES in feature_types:
                features_df = self._add_market_features(features_df)

            # 清理无效值
            features_df = features_df.dropna()

            self.logger.info(f"为 {symbol} 创建了 {len(features_df.columns)} 个特征")

            return features_df

        except Exception as e:
            self.logger.error(f"特征创建失败: {e}")
            return data

    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加技术指标特征"""
        try:
            # 移动平均线
            df["sma_5"] = df["close"].rolling(window=5).mean()
            df["sma_10"] = df["close"].rolling(window=10).mean()
            df["sma_20"] = df["close"].rolling(window=20).mean()
            df["sma_50"] = df["close"].rolling(window=50).mean()

            # 指数移动平均线
            df["ema_12"] = df["close"].ewm(span=12).mean()
            df["ema_26"] = df["close"].ewm(span=26).mean()

            # MACD
            df["macd"] = df["ema_12"] - df["ema_26"]
            df["macd_signal"] = df["macd"].ewm(span=9).mean()
            df["macd_histogram"] = df["macd"] - df["macd_signal"]

            # RSI
            delta = df["close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df["rsi"] = 100 - (100 / (1 + rs))

            # 布林带
            df["bb_middle"] = df["close"].rolling(window=20).mean()
            bb_std = df["close"].rolling(window=20).std()
            df["bb_upper"] = df["bb_middle"] + (bb_std * 2)
            df["bb_lower"] = df["bb_middle"] - (bb_std * 2)
            df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_middle"]
            df["bb_position"] = (df["close"] - df["bb_lower"]) / (
                df["bb_upper"] - df["bb_lower"]
            )

            # KDJ指标
            low_min = df["low"].rolling(window=9).min()
            high_max = df["high"].rolling(window=9).max()
            df["k"] = 100 * (df["close"] - low_min) / (high_max - low_min)
            df["d"] = df["k"].rolling(window=3).mean()
            df["j"] = 3 * df["k"] - 2 * df["d"]

            # 威廉指标
            df["williams_r"] = -100 * (high_max - df["close"]) / (high_max - low_min)

        except Exception as e:
            self.logger.error(f"添加技术指标失败: {e}")

        return df

    def _add_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加价格特征"""
        try:
            # 收益率
            df["return_1d"] = df["close"].pct_change(1)
            df["return_5d"] = df["close"].pct_change(5)
            df["return_10d"] = df["close"].pct_change(10)
            df["return_20d"] = df["close"].pct_change(20)

            # 对数收益率
            df["log_return_1d"] = np.log(df["close"] / df["close"].shift(1))
            df["log_return_5d"] = np.log(df["close"] / df["close"].shift(5))

            # 价格位置
            df["price_position_5d"] = (df["close"] - df["low"].rolling(5).min()) / (
                df["high"].rolling(5).max() - df["low"].rolling(5).min()
            )
            df["price_position_20d"] = (df["close"] - df["low"].rolling(20).min()) / (
                df["high"].rolling(20).max() - df["low"].rolling(20).min()
            )

            # 波动率
            df["volatility_5d"] = df["return_1d"].rolling(5).std()
            df["volatility_20d"] = df["return_1d"].rolling(20).std()
            df["volatility_annual"] = df["return_1d"].rolling(20).std() * np.sqrt(252)

            # 价格动量
            df["momentum_5d"] = df["close"] / df["close"].shift(5) - 1
            df["momentum_10d"] = df["close"] / df["close"].shift(10) - 1
            df["momentum_20d"] = df["close"] / df["close"].shift(20) - 1

        except Exception as e:
            self.logger.error(f"添加价格特征失败: {e}")

        return df

    def _add_volume_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加成交量特征"""
        try:
            # 成交量移动平均
            df["volume_sma_5"] = df["volume"].rolling(window=5).mean()
            df["volume_sma_20"] = df["volume"].rolling(window=20).mean()

            # 成交量比率
            df["volume_ratio_5d"] = df["volume"] / df["volume_sma_5"]
            df["volume_ratio_20d"] = df["volume"] / df["volume_sma_20"]

            # 价量关系
            df["price_volume_trend"] = df["close"].diff() * df["volume"]
            df["volume_price_correlation"] = df["close"].rolling(20).corr(df["volume"])

            # 成交量波动率
            df["volume_volatility"] = df["volume"].rolling(10).std()

            # OBV (On - Balance Volume)
            df["obv"] = (
                df["volume"] * np.where(df["close"] > df["close"].shift(1), 1, -1)
            ).cumsum()

        except Exception as e:
            self.logger.error(f"添加成交量特征失败: {e}")

        return df

    def _add_market_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加市场特征"""
        try:
            # 市场情绪指标（简化版本）
            df["market_sentiment"] = np.random.uniform(-1, 1, len(df))  # 模拟市场情绪

            # 相对强弱指数
            df["relative_strength"] = df["close"] / df["close"].rolling(50).mean()

            # 市场趋势
            df["trend_5d"] = np.where(df["close"] > df["close"].shift(5), 1, 0)
            df["trend_20d"] = np.where(df["close"] > df["close"].shift(20), 1, 0)

        except Exception as e:
            self.logger.error(f"添加市场特征失败: {e}")

        return df

    def select_features(
        self, X: pd.DataFrame, y: pd.Series, method: str = "mutual_info", k: int = 20
    ) -> Tuple[pd.DataFrame, List[str]]:
        """特征选择"""

        try:
            if method == "mutual_info":
                selector = SelectKBest(score_func=mutual_info_regression, k=k)
            elif method == "f_regression":
                selector = SelectKBest(score_func=f_regression, k=k)
            else:
                raise ValueError(f"不支持的特征选择方法: {method}")

            # 处理缺失值
            X_clean = X.fillna(X.mean())
            y_clean = y.fillna(y.mean())

            # 特征选择
            X_selected = selector.fit_transform(X_clean, y_clean)
            selected_features = X.columns[selector.get_support()].tolist()

            self.logger.info(
                f"选择了 {len(selected_features)} 个特征: {selected_features}"
            )

            return (
                pd.DataFrame(X_selected, columns=selected_features, index=X.index),
                selected_features,
            )

        except Exception as e:
            self.logger.error(f"特征选择失败: {e}")
            return X, X.columns.tolist()

    def scale_features(self, X: pd.DataFrame, method: str = "standard") -> pd.DataFrame:
        """特征缩放"""
        try:
            if method == "standard":
                scaler = StandardScaler()
            elif method == "minmax":
                scaler = MinMaxScaler()
            elif method == "robust":
                scaler = RobustScaler()
            else:
                raise ValueError(f"不支持的缩放方法: {method}")

            # 保存缩放器
            scaler_key = f"{method}_scaler"
            self.scalers[scaler_key] = scaler

            # 缩放特征
            X_scaled = scaler.fit_transform(X.fillna(X.mean()))

            return pd.DataFrame(X_scaled, columns=X.columns, index=X.index)

        except Exception as e:
            self.logger.error(f"特征缩放失败: {e}")
            return X


class ModelTrainer:
    """模型训练器"""

    def __init__(self):
        self.logger = logging.getLogger("hk_quant_system.data_scientist.model_trainer")
        self.models: Dict[str, Any] = {}
        self.model_performance: Dict[str, ModelPerformance] = {}

    def train_model(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        model_type: ModelType,
        symbol: str,
        target: str = "price",
        test_size: float = 0.2,
        random_state: int = 42,
    ) -> Tuple[Any, ModelPerformance]:
        """训练模型"""

        try:
            start_time = datetime.now()

            # 分割数据
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state, shuffle=False
            )

            # 创建模型
            model = self._create_model(model_type)

            # 训练模型
            model.fit(X_train, y_train)

            # 预测和评估
            y_pred_train = model.predict(X_train)
            y_pred_test = model.predict(X_test)

            # 计算性能指标
            mse_train = mean_squared_error(y_train, y_pred_train)
            mse_test = mean_squared_error(y_test, y_pred_test)
            rmse_test = np.sqrt(mse_test)
            mae_test = mean_absolute_error(y_test, y_pred_test)
            r2_test = r2_score(y_test, y_pred_test)

            # 交叉验证
            cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring="r2")
            cv_score = cv_scores.mean()

            # 训练时间
            training_time = (datetime.now() - start_time).total_seconds()

            # 创建模型ID
            model_id = f"{model_type.value}_{symbol}_{target}_{datetime.now().strftime('%Y % m % d_ % H % M % S')}"

            # 保存模型
            self.models[model_id] = model

            # 创建性能记录
            performance = ModelPerformance(
                model_id=model_id,
                model_type=model_type,
                symbol=symbol,
                target=target,
                mse=mse_test,
                rmse=rmse_test,
                mae=mae_test,
                r2_score=r2_test,
                cv_score=cv_score,
                training_samples=len(X_train),
                feature_count=len(X.columns),
                training_time=training_time,
            )

            self.model_performance[model_id] = performance

            self.logger.info(f"模型训练完成: {model_id}, R² = {r2_test:.4f}")

            return model, performance

        except Exception as e:
            self.logger.error(f"模型训练失败: {e}")
            return None, None

    def _create_model(self, model_type: ModelType) -> Any:
        """创建模型"""
        if model_type == ModelType.LINEAR_REGRESSION:
            return LinearRegression()
        elif model_type == ModelType.RIDGE_REGRESSION:
            return Ridge(alpha=1.0)
        elif model_type == ModelType.LASSO_REGRESSION:
            return Lasso(alpha=1.0)
        elif model_type == ModelType.RANDOM_FOREST:
            return RandomForestRegressor(n_estimators=100, random_state=42)
        elif model_type == ModelType.GRADIENT_BOOSTING:
            return GradientBoostingRegressor(n_estimators=100, random_state=42)
        elif model_type == ModelType.SUPPORT_VECTOR:
            return SVR(kernel="rbf")
        elif model_type == ModelType.NEURAL_NETWORK:
            return MLPRegressor(
                hidden_layer_sizes=(100, 50), random_state=42, max_iter=500
            )
        else:
            raise ValueError(f"不支持的模型类型: {model_type}")

    def hyperparameter_tuning(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        model_type: ModelType,
        param_grid: Dict[str, List] = None,
    ) -> Tuple[Any, Dict[str, Any]]:
        """超参数调优"""

        try:
            if param_grid is None:
                param_grid = self._get_default_param_grid(model_type)

            # 创建基础模型
            base_model = self._create_model(model_type)

            # 网格搜索
            grid_search = GridSearchCV(
                base_model, param_grid, cv=5, scoring="r2", n_jobs=-1
            )

            grid_search.fit(X, y)

            best_model = grid_search.best_estimator_
            best_params = grid_search.best_params_
            best_score = grid_search.best_score_

            self.logger.info(
                f"超参数调优完成: {model_type}, 最佳分数: {best_score:.4f}"
            )

            return best_model, best_params

        except Exception as e:
            self.logger.error(f"超参数调优失败: {e}")
            return None, {}

    def _get_default_param_grid(self, model_type: ModelType) -> Dict[str, List]:
        """获取默认参数网格"""
        param_grids = {
            ModelType.RIDGE_REGRESSION: {"alpha": [0.1, 1.0, 10.0, 100.0]},
            ModelType.LASSO_REGRESSION: {"alpha": [0.1, 1.0, 10.0, 100.0]},
            ModelType.RANDOM_FOREST: {
                "n_estimators": [50, 100, 200],
                "max_depth": [10, 20, None],
                "min_samples_split": [2, 5, 10],
            },
            ModelType.GRADIENT_BOOSTING: {
                "n_estimators": [50, 100, 200],
                "learning_rate": [0.01, 0.1, 0.2],
                "max_depth": [3, 5, 7],
            },
            ModelType.SUPPORT_VECTOR: {
                "C": [0.1, 1, 10, 100],
                "gamma": ["scale", "auto", 0.001, 0.01, 0.1],
            },
            ModelType.NEURAL_NETWORK: {
                "hidden_layer_sizes": [(50,), (100,), (100, 50), (100, 50, 25)],
                "learning_rate": ["constant", "adaptive"],
                "alpha": [0.0001, 0.001, 0.01],
            },
        }

        return param_grids.get(model_type, {})

    def predict(self, model_id: str, X: pd.DataFrame) -> Optional[PredictionResult]:
        """模型预测"""

        try:
            if model_id not in self.models:
                self.logger.error(f"模型不存在: {model_id}")
                return None

            model = self.models[model_id]
            performance = self.model_performance.get(model_id)

            if performance is None:
                self.logger.error(f"模型性能信息不存在: {model_id}")
                return None

            # 预测
            prediction = model.predict(X.iloc[-1:].values.reshape(1, -1))[0]

            # 计算置信度（基于R²分数）
            confidence = max(0.0, min(1.0, performance.r2_score))

            # 更新性能记录
            performance.last_prediction = prediction
            performance.prediction_confidence = confidence
            performance.last_updated = datetime.now()

            # 创建预测结果
            result = PredictionResult(
                model_id=model_id,
                symbol=performance.symbol,
                prediction=prediction,
                confidence=confidence,
                features_used=X.columns.tolist(),
                prediction_type=performance.target,
            )

            self.logger.info(
                f"预测完成: {model_id}, 预测值: {prediction:.4f}, 置信度: {confidence:.4f}"
            )

            return result

        except Exception as e:
            self.logger.error(f"模型预测失败: {e}")
            return None

    def save_model(self, model_id: str, filepath: str):
        """保存模型"""
        try:
            if model_id not in self.models:
                self.logger.error(f"模型不存在: {model_id}")
                return False

            model = self.models[model_id]
            joblib.dump(model, filepath)

            self.logger.info(f"模型已保存: {filepath}")
            return True

        except Exception as e:
            self.logger.error(f"保存模型失败: {e}")
            return False

    def load_model(self, model_id: str, filepath: str):
        """加载模型"""
        try:
            if not os.path.exists(filepath):
                self.logger.error(f"模型文件不存在: {filepath}")
                return False

            model = joblib.load(filepath)
            self.models[model_id] = model

            self.logger.info(f"模型已加载: {filepath}")
            return True

        except Exception as e:
            self.logger.error(f"加载模型失败: {e}")
            return False


class DataScientistAgent(BaseAgent):
    """数据科学家Agent"""

    def __init__(
        self,
        config: AgentConfig,
        message_queue: MessageQueue,
        system_config: SystemConfig = None,
    ):
        super().__init__(config, message_queue, system_config)

        # 初始化组件
        self.feature_engineer = FeatureEngineer()
        self.model_trainer = ModelTrainer()

        # 数据缓存
        self.market_data_cache: Dict[str, pd.DataFrame] = {}
        self.feature_cache: Dict[str, pd.DataFrame] = {}
        self.prediction_cache: Dict[str, PredictionResult] = {}

        # 模型配置
        self.active_models: Dict[str, List[str]] = {}  # symbol -> model_ids
        self.model_configs = {
            "default_models": [ModelType.RANDOM_FOREST, ModelType.GRADIENT_BOOSTING],
            "feature_selection_k": 20,
            "test_size": 0.2,
            "retrain_frequency": 7,  # 天
        }

        # 协议
        self.protocol = AgentProtocol(config.agent_id, message_queue)

    async def initialize(self) -> bool:
        """初始化Agent"""
        try:
            # 初始化协议
            await self.protocol.initialize()

            # 注册消息处理器
            self.protocol.register_handler(MessageType.DATA, self._handle_market_data)
            self.protocol.register_handler(MessageType.CONTROL, self._handle_ml_control)

            self.logger.info(f"数据科学家Agent初始化成功: {self.config.agent_id}")
            return True

        except Exception as e:
            self.logger.error(f"数据科学家Agent初始化失败: {e}")
            return False

    async def process_message(self, message: Message) -> bool:
        """处理消息"""
        try:
            await self.protocol.handle_incoming_message(message)
            return True

        except Exception as e:
            self.logger.error(f"处理消息失败: {e}")
            return False

    async def cleanup(self):
        """清理资源"""
        self.logger.info("清理数据科学家Agent资源")

        # 保存模型和缓存
        await self._save_models_and_cache()

    async def _handle_market_data(self, protocol_message):
        """处理市场数据"""
        try:
            data_type = protocol_message.payload.get("data_type")
            data = protocol_message.payload.get("data", {})

            if data_type == "market_data":
                symbol = data.get("symbol")
                market_data = data.get("market_data")

                if symbol and market_data:
                    await self._process_market_data(symbol, market_data)

        except Exception as e:
            self.logger.error(f"处理市场数据失败: {e}")

    async def _handle_ml_control(self, protocol_message):
        """处理机器学习控制消息"""
        try:
            command = protocol_message.payload.get("command")
            parameters = protocol_message.payload.get("parameters", {})

            if command == "train_models":
                symbol = parameters.get("symbol")
                model_types = parameters.get(
                    "model_types", self.model_configs["default_models"]
                )
                await self._train_models_for_symbol(symbol, model_types)

            elif command == "make_prediction":
                symbol = parameters.get("symbol")
                model_id = parameters.get("model_id")
                await self._make_prediction(symbol, model_id)

            elif command == "retrain_models":
                await self._retrain_all_models()

            elif command == "get_model_performance":
                symbol = parameters.get("symbol")
                await self._send_model_performance(symbol)

        except Exception as e:
            self.logger.error(f"处理机器学习控制消息失败: {e}")

    async def _process_market_data(self, symbol: str, market_data: Dict[str, Any]):
        """处理市场数据"""
        try:
            # 转换为DataFrame格式
            df_data = {
                "timestamp": [datetime.fromisoformat(market_data["timestamp"])],
                "open": [market_data["open_price"]],
                "high": [market_data["high_price"]],
                "low": [market_data["low_price"]],
                "close": [market_data["close_price"]],
                "volume": [market_data["volume"]],
            }

            new_row = pd.DataFrame(df_data)

            # 更新缓存数据
            if symbol in self.market_data_cache:
                self.market_data_cache[symbol] = pd.concat(
                    [self.market_data_cache[symbol], new_row], ignore_index=True
                )
            else:
                self.market_data_cache[symbol] = new_row

            # 保持最近500个数据点
            if len(self.market_data_cache[symbol]) > 500:
                self.market_data_cache[symbol] = self.market_data_cache[symbol].tail(
                    500
                )

            # 检查是否需要训练新模型
            await self._check_model_training_needs(symbol)

            # 如果有模型，进行预测
            await self._make_latest_prediction(symbol)

        except Exception as e:
            self.logger.error(f"处理市场数据失败: {e}")

    async def _check_model_training_needs(self, symbol: str):
        """检查是否需要训练新模型"""
        try:
            # 检查是否有足够的数据
            if (
                symbol not in self.market_data_cache
                or len(self.market_data_cache[symbol]) < 100
            ):
                return

            # 检查是否已有模型
            if symbol in self.active_models and len(self.active_models[symbol]) > 0:
                # 检查模型是否需要重新训练
                latest_performance = None
                for model_id in self.active_models[symbol]:
                    if model_id in self.model_trainer.model_performance:
                        performance = self.model_trainer.model_performance[model_id]
                        if (
                            latest_performance is None
                            or performance.last_updated
                            > latest_performance.last_updated
                        ):
                            latest_performance = performance

                if latest_performance:
                    days_since_training = (
                        datetime.now() - latest_performance.last_updated
                    ).days
                    if days_since_training < self.model_configs["retrain_frequency"]:
                        return

            # 训练新模型
            await self._train_models_for_symbol(
                symbol, self.model_configs["default_models"]
            )

        except Exception as e:
            self.logger.error(f"检查模型训练需求失败: {e}")

    async def _train_models_for_symbol(self, symbol: str, model_types: List[ModelType]):
        """为指定股票训练模型"""
        try:
            if (
                symbol not in self.market_data_cache
                or len(self.market_data_cache[symbol]) < 100
            ):
                self.logger.warning(f"数据不足，无法为 {symbol} 训练模型")
                return

            # 准备数据
            data = self.market_data_cache[symbol].copy()

            # 创建特征
            features_df = self.feature_engineer.create_features(data, symbol)

            if len(features_df) < 50:
                self.logger.warning(f"特征数据不足，无法为 {symbol} 训练模型")
                return

            # 定义目标变量（预测下一日收盘价）
            y = features_df["close"].shift(-1).dropna()
            X = features_df.drop(["close"], axis=1).iloc[:-1]

            # 特征选择
            X_selected, selected_features = self.feature_engineer.select_features(
                X, y, method="mutual_info", k=self.model_configs["feature_selection_k"]
            )

            # 特征缩放
            X_scaled = self.feature_engineer.scale_features(
                X_selected, method="standard"
            )

            # 训练多个模型
            trained_models = []
            for model_type in model_types:
                model, performance = self.model_trainer.train_model(
                    X_scaled, y, model_type, symbol, target="price"
                )

                if model and performance:
                    trained_models.append(performance.model_id)

            # 更新活跃模型列表
            self.active_models[symbol] = trained_models

            # 缓存特征数据
            self.feature_cache[symbol] = X_scaled

            # 广播训练结果
            await self.protocol.broadcast_message(
                message_type=MessageType.DATA,
                payload={
                    "model_training_complete": {
                        "symbol": symbol,
                        "trained_models": trained_models,
                        "feature_count": len(selected_features),
                        "training_samples": len(X_scaled),
                        "timestamp": datetime.now().isoformat(),
                    }
                },
            )

            self.logger.info(f"为 {symbol} 训练了 {len(trained_models)} 个模型")

        except Exception as e:
            self.logger.error(f"为 {symbol} 训练模型失败: {e}")

    async def _make_latest_prediction(self, symbol: str):
        """进行最新预测"""
        try:
            if symbol not in self.active_models or not self.active_models[symbol]:
                return

            if symbol not in self.feature_cache:
                return

            # 使用最佳模型进行预测
            best_model_id = self._get_best_model(symbol)
            if best_model_id:
                await self._make_prediction(symbol, best_model_id)

        except Exception as e:
            self.logger.error(f"进行最新预测失败: {e}")

    async def _make_prediction(self, symbol: str, model_id: str):
        """进行预测"""
        try:
            if symbol not in self.feature_cache:
                self.logger.warning(f"没有 {symbol} 的特征数据")
                return

            # 获取最新特征
            latest_features = self.feature_cache[symbol].iloc[-1:]

            # 进行预测
            prediction_result = self.model_trainer.predict(model_id, latest_features)

            if prediction_result:
                # 缓存预测结果
                self.prediction_cache[f"{symbol}_{model_id}"] = prediction_result

                # 广播预测结果
                await self.protocol.broadcast_message(
                    message_type=MessageType.DATA,
                    payload={
                        "prediction_result": {
                            "symbol": symbol,
                            "model_id": model_id,
                            "prediction": prediction_result.prediction,
                            "confidence": prediction_result.confidence,
                            "prediction_type": prediction_result.prediction_type,
                            "timestamp": prediction_result.timestamp.isoformat(),
                        }
                    },
                )

                self.logger.info(
                    f"预测完成: {symbol} -> {prediction_result.prediction:.4f}"
                )

        except Exception as e:
            self.logger.error(f"预测失败: {e}")

    def _get_best_model(self, symbol: str) -> Optional[str]:
        """获取最佳模型"""
        try:
            if symbol not in self.active_models or not self.active_models[symbol]:
                return None

            best_model_id = None
            best_score = -float("inf")

            for model_id in self.active_models[symbol]:
                if model_id in self.model_trainer.model_performance:
                    performance = self.model_trainer.model_performance[model_id]
                    if performance.r2_score > best_score:
                        best_score = performance.r2_score
                        best_model_id = model_id

            return best_model_id

        except Exception as e:
            self.logger.error(f"获取最佳模型失败: {e}")
            return None

    async def _retrain_all_models(self):
        """重新训练所有模型"""
        try:
            for symbol in self.active_models.keys():
                if symbol in self.market_data_cache:
                    await self._train_models_for_symbol(
                        symbol, self.model_configs["default_models"]
                    )

            self.logger.info("所有模型重新训练完成")

        except Exception as e:
            self.logger.error(f"重新训练所有模型失败: {e}")

    async def _send_model_performance(self, symbol: str):
        """发送模型性能信息"""
        try:
            if symbol not in self.active_models:
                return

            performance_data = []
            for model_id in self.active_models[symbol]:
                if model_id in self.model_trainer.model_performance:
                    performance = self.model_trainer.model_performance[model_id]
                    performance_data.append(
                        {
                            "model_id": performance.model_id,
                            "model_type": performance.model_type.value,
                            "r2_score": performance.r2_score,
                            "rmse": performance.rmse,
                            "mae": performance.mae,
                            "cv_score": performance.cv_score,
                            "training_samples": performance.training_samples,
                            "feature_count": performance.feature_count,
                            "training_time": performance.training_time,
                            "last_updated": performance.last_updated.isoformat(),
                        }
                    )

            # 广播性能信息
            await self.protocol.broadcast_message(
                message_type=MessageType.DATA,
                payload={
                    "model_performance": {
                        "symbol": symbol,
                        "performance_data": performance_data,
                        "timestamp": datetime.now().isoformat(),
                    }
                },
            )

        except Exception as e:
            self.logger.error(f"发送模型性能信息失败: {e}")

    async def _save_models_and_cache(self):
        """保存模型和缓存"""
        try:
            # 保存模型
            for model_id, model in self.model_trainer.models.items():
                filepath = f"models/{model_id}.joblib"
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                self.model_trainer.save_model(model_id, filepath)

            self.logger.info(f"保存了 {len(self.model_trainer.models)} 个模型")

        except Exception as e:
            self.logger.error(f"保存模型和缓存失败: {e}")

    def get_ml_summary(self) -> Dict[str, Any]:
        """获取机器学习摘要"""
        return {
            "agent_id": self.config.agent_id,
            "total_models": len(self.model_trainer.models),
            "active_symbols": len(self.active_models),
            "cached_symbols": list(self.market_data_cache.keys()),
            "feature_cache_size": len(self.feature_cache),
            "prediction_cache_size": len(self.prediction_cache),
            "model_configs": self.model_configs,
            "protocol_stats": self.protocol.get_protocol_stats(),
        }


# 导出主要组件
__all__ = [
    "DataScientistAgent",
    "FeatureEngineer",
    "ModelTrainer",
    "ModelPerformance",
    "FeatureImportance",
    "PredictionResult",
]

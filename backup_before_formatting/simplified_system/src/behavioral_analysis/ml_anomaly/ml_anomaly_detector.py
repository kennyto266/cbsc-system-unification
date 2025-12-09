#!/usr/bin/env python3
"""
第4阶段 Task 21 & 22: ML异常检测器和集成方法
Phase 4 Task 21 & 22: ML Anomaly Detector and Ensemble Methods

使用机器学习算法进行异常检测，包括无监督学习、集成方法和置信度校准
Machine learning based anomaly detection with unsupervised learning, ensemble methods, and confidence calibration
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Machine learning libraries
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.svm import OneClassSVM
from sklearn.neighbors import LocalOutlierFactor
from sklearn.ensemble import GradientBoostingClassifier, VotingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.feature_selection import SelectKBest, f_classif

# Deep learning (optional)
try:
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Dense, Dropout, BatchNormalization
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False

# Calibration and confidence
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.isotonic import IsotonicRegression

# Statistical methods
from scipy import stats
from scipy.spatial.distance import mahalanobis

# Visualization
import matplotlib.pyplot as plt
import seaborn as sns

# Logging
import logging
logger = logging.getLogger(__name__)

from ..core.behavioral_config import get_behavioral_config, MLModelConfig, EnsembleConfig, AnomalyType


class BaseAnomalyDetector:
    """异常检测器基类"""

    def __init__(self, config: Optional[MLModelConfig] = None):
        self.config = config or get_behavioral_config().ml_models
        self.model = None
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.feature_names = []

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> 'BaseAnomalyDetector':
        """训练模型"""
        raise NotImplementedError("Subclasses must implement fit method")

    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测异常"""
        raise NotImplementedError("Subclasses must implement predict method")

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """预测异常概率"""
        raise NotImplementedError("Subclasses must implement predict_proba method")

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """决策函数"""
        raise NotImplementedError("Subclasses must implement decision_function method")

    def get_feature_importance(self) -> Optional[np.ndarray]:
        """获取特征重要性"""
        return None


class IsolationForestDetector(BaseAnomalyDetector):
    """Isolation Forest异常检测器"""

    def __init__(self, config: Optional[MLModelConfig] = None):
        super().__init__(config)
        self.model = IsolationForest(
            n_estimators=self.config.isolation_n_estimators,
            contamination=self.config.isolation_contamination,
            max_features=self.config.isolation_max_features,
            random_state=42,
            n_jobs=-1
        )

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> 'IsolationForestDetector':
        """训练Isolation Forest模型"""
        try:
            # 标准化数据
            X_scaled = self.scaler.fit_transform(X)

            # 训练模型
            self.model.fit(X_scaled)
            self.is_fitted = True

            logger.info(f"Isolation Forest trained with {X.shape[0]} samples, {X.shape[1]} features")
            return self

        except Exception as e:
            logger.error(f"Error fitting Isolation Forest: {e}")
            raise

    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测异常 (-1为异常，1为正常)"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")

        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """预测异常概率"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")

        X_scaled = self.scaler.transform(X)
        # 将决策函数转换为概率
        scores = self.model.decision_function(X_scaled)
        # 标准化到0-1范围
        probs = 1 / (1 + np.exp(scores))
        return probs.reshape(-1, 1)

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """决策函数"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")

        X_scaled = self.scaler.transform(X)
        return self.model.decision_function(X_scaled)


class OneClassSVMDetector(BaseAnomalyDetector):
    """One-Class SVM异常检测器"""

    def __init__(self, config: Optional[MLModelConfig] = None):
        super().__init__(config)
        self.model = OneClassSVM(
            kernel=self.config.svm_kernel,
            gamma=self.config.svm_gamma,
            nu=self.config.svm_nu
        )

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> 'OneClassSVMDetector':
        """训练One-Class SVM模型"""
        try:
            # 标准化数据
            X_scaled = self.scaler.fit_transform(X)

            # 训练模型
            self.model.fit(X_scaled)
            self.is_fitted = True

            logger.info(f"One-Class SVM trained with {X.shape[0]} samples, {X.shape[1]} features")
            return self

        except Exception as e:
            logger.error(f"Error fitting One-Class SVM: {e}")
            raise

    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测异常"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")

        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """预测异常概率"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")

        X_scaled = self.scaler.transform(X)
        scores = self.model.decision_function(X_scaled)
        # 将得分转换为概率
        probs = 1 / (1 + np.exp(scores))
        return probs.reshape(-1, 1)

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """决策函数"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")

        X_scaled = self.scaler.transform(X)
        return self.model.decision_function(X_scaled)


class LocalOutlierFactorDetector(BaseAnomalyDetector):
    """Local Outlier Factor异常检测器"""

    def __init__(self, config: Optional[MLModelConfig] = None):
        super().__init__(config)
        self.model = LocalOutlierFactor(
            n_neighbors=self.config.lof_n_neighbors,
            contamination=self.config.lof_contamination,
            novelty=self.config.lof_novelty,
            n_jobs=-1
        )

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> 'LocalOutlierFactorDetector':
        """训练LOF模型"""
        try:
            # 标准化数据
            X_scaled = self.scaler.fit_transform(X)

            # 训练模型
            self.model.fit(X_scaled)
            self.is_fitted = True

            logger.info(f"LOF trained with {X.shape[0]} samples, {X.shape[1]} features")
            return self

        except Exception as e:
            logger.error(f"Error fitting LOF: {e}")
            raise

    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测异常"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")

        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """预测异常概率"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")

        X_scaled = self.scaler.transform(X)
        # LOF的负异常因子作为异常得分
        scores = -self.model.decision_function(X_scaled)
        # 标准化到0-1范围
        min_score, max_score = scores.min(), scores.max()
        if max_score > min_score:
            probs = (scores - min_score) / (max_score - min_score)
        else:
            probs = np.zeros_like(scores)
        return probs.reshape(-1, 1)

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """决策函数"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")

        X_scaled = self.scaler.transform(X)
        return self.model.decision_function(X_scaled)


class RandomForestAnomalyDetector(BaseAnomalyDetector):
    """随机森林异常检测器（监督学习）"""

    def __init__(self, config: Optional[MLModelConfig] = None):
        super().__init__(config)
        self.model = RandomForestClassifier(
            n_estimators=self.config.rf_n_estimators,
            max_depth=self.config.rf_max_depth,
            min_samples_split=self.config.rf_min_samples_split,
            min_samples_leaf=self.config.rf_min_samples_leaf,
            random_state=42,
            n_jobs=-1
        )
        self.is_supervised = True

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> 'RandomForestAnomalyDetector':
        """训练随机森林模型"""
        try:
            if y is None:
                raise ValueError("RandomForest requires labels (y parameter)")

            # 标准化数据
            X_scaled = self.scaler.fit_transform(X)

            # 训练模型
            self.model.fit(X_scaled, y)
            self.is_fitted = True

            logger.info(f"Random Forest trained with {X.shape[0]} samples, {X.shape[1]} features")
            return self

        except Exception as e:
            logger.error(f"Error fitting Random Forest: {e}")
            raise

    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测异常"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")

        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """预测异常概率"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")

        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """决策函数"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")

        X_scaled = self.scaler.transform(X)
        # 返回异常类别的概率
        probas = self.model.predict_proba(X_scaled)
        return probas[:, 1] if probas.shape[1] > 1 else probas[:, 0]

    def get_feature_importance(self) -> np.ndarray:
        """获取特征重要性"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        return self.model.feature_importances_


class GradientBoostingAnomalyDetector(BaseAnomalyDetector):
    """梯度提升异常检测器（监督学习）"""

    def __init__(self, config: Optional[MLModelConfig] = None):
        super().__init__(config)
        self.model = GradientBoostingClassifier(
            n_estimators=self.config.gb_n_estimators,
            learning_rate=self.config.gb_learning_rate,
            max_depth=self.config.gb_max_depth,
            subsample=self.config.gb_subsample,
            random_state=42
        )
        self.is_supervised = True

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> 'GradientBoostingAnomalyDetector':
        """训练梯度提升模型"""
        try:
            if y is None:
                raise ValueError("GradientBoosting requires labels (y parameter)")

            # 标准化数据
            X_scaled = self.scaler.fit_transform(X)

            # 训练模型
            self.model.fit(X_scaled, y)
            self.is_fitted = True

            logger.info(f"Gradient Boosting trained with {X.shape[0]} samples, {X.shape[1]} features")
            return self

        except Exception as e:
            logger.error(f"Error fitting Gradient Boosting: {e}")
            raise

    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测异常"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")

        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """预测异常概率"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")

        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """决策函数"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")

        X_scaled = self.scaler.transform(X)
        probas = self.model.predict_proba(X_scaled)
        return probas[:, 1] if probas.shape[1] > 1 else probas[:, 0]

    def get_feature_importance(self) -> np.ndarray:
        """获取特征重要性"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        return self.model.feature_importances_


class NeuralNetworkAnomalyDetector(BaseAnomalyDetector):
    """神经网络异常检测器"""

    def __init__(self, config: Optional[MLModelConfig] = None):
        super().__init__(config)
        self.config = config or get_behavioral_config().ml_models
        self.model = None
        self.is_supervised = True

        if not TENSORFLOW_AVAILABLE:
            logger.warning("TensorFlow not available, Neural Network detector will not work")

    def _build_model(self, input_shape: int) -> None:
        """构建神经网络模型"""
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow is required for Neural Network detector")

        self.model = Sequential([
            Dense(self.config.nn_hidden_layers[0], input_shape=(input_shape,), activation=self.config.nn_activation),
            BatchNormalization(),
            Dropout(self.config.nn_dropout),

            Dense(self.config.nn_hidden_layers[1], activation=self.config.nn_activation),
            BatchNormalization(),
            Dropout(self.config.nn_dropout),

            Dense(self.config.nn_hidden_layers[2], activation=self.config.nn_activation),
            BatchNormalization(),
            Dropout(self.config.nn_dropout),

            Dense(1, activation='sigmoid')  # 二分类输出
        ])

        self.model.compile(
            optimizer=Adam(learning_rate=self.config.nn_learning_rate),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> 'NeuralNetworkAnomalyDetector':
        """训练神经网络模型"""
        try:
            if not TENSORFLOW_AVAILABLE:
                raise ImportError("TensorFlow is required for Neural Network detector")

            if y is None:
                raise ValueError("Neural Network requires labels (y parameter)")

            # 标准化数据
            X_scaled = self.scaler.fit_transform(X)

            # 构建模型
            self._build_model(X_scaled.shape[1])

            # 训练模型
            early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)

            self.model.fit(
                X_scaled, y,
                epochs=self.config.nn_epochs,
                batch_size=self.config.nn_batch_size,
                validation_split=0.2,
                callbacks=[early_stopping],
                verbose=0
            )

            self.is_fitted = True
            logger.info(f"Neural Network trained with {X.shape[0]} samples, {X.shape[1]} features")
            return self

        except Exception as e:
            logger.error(f"Error fitting Neural Network: {e}")
            raise

    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测异常"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")

        X_scaled = self.scaler.transform(X)
        predictions = self.model.predict(X_scaled, verbose=0)
        return (predictions.flatten() > 0.5).astype(int)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """预测异常概率"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")

        X_scaled = self.scaler.transform(X)
        probabilities = self.model.predict(X_scaled, verbose=0)
        return np.column_stack([1 - probabilities.flatten(), probabilities.flatten()])

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """决策函数"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")

        X_scaled = self.scaler.transform(X)
        probabilities = self.model.predict(X_scaled, verbose=0)
        return probabilities.flatten()


class EnsembleAnomalyDetector:
    """集成异常检测器"""

    def __init__(self, config: Optional[EnsembleConfig] = None, ml_config: Optional[MLModelConfig] = None):
        self.config = config or get_behavioral_config().ensemble
        self.ml_config = ml_config or get_behavioral_config().ml_models
        self.detectors = {}
        self.weights = {}
        self.is_fitted = False
        self.calibrator = None

        # 初始化各个检测器
        self._initialize_detectors()

    def _initialize_detectors(self) -> None:
        """初始化各个异常检测器"""
        try:
            # 无监督检测器
            self.detectors['isolation_forest'] = IsolationForestDetector(self.ml_config)
            self.detectors['one_class_svm'] = OneClassSVMDetector(self.ml_config)
            self.detectors['lof'] = LocalOutlierFactorDetector(self.ml_config)

            # 监督检测器（这些需要标签数据）
            self.detectors['random_forest'] = RandomForestAnomalyDetector(self.ml_config)
            self.detectors['gradient_boosting'] = GradientBoostingAnomalyDetector(self.ml_config)

            # 神经网络检测器（如果TensorFlow可用）
            if TENSORFLOW_AVAILABLE:
                self.detectors['neural_network'] = NeuralNetworkAnomalyDetector(self.ml_config)

            # 设置权重
            self.weights = {
                'isolation_forest': self.config.isolation_weight,
                'one_class_svm': self.config.svm_weight,
                'lof': self.config.lof_weight,
                'random_forest': self.config.rf_weight,
                'gradient_boosting': self.config.gb_weight,
                'neural_network': self.config.nn_weight
            }

            logger.info(f"Initialized {len(self.detectors)} anomaly detectors")

        except Exception as e:
            logger.error(f"Error initializing detectors: {e}")
            raise

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> 'EnsembleAnomalyDetector':
        """训练集成模型"""
        try:
            logger.info(f"Training ensemble with {X.shape[0]} samples, {X.shape[1]} features")

            # 训练无监督检测器
            unsupervised_detectors = ['isolation_forest', 'one_class_svm', 'lof']
            for name in unsupervised_detectors:
                if name in self.detectors:
                    try:
                        self.detectors[name].fit(X)
                        logger.info(f"Trained {name} detector")
                    except Exception as e:
                        logger.warning(f"Failed to train {name}: {e}")
                        self.weights[name] = 0  # 设置权重为0

            # 训练监督检测器（如果有标签）
            if y is not None:
                supervised_detectors = ['random_forest', 'gradient_boosting', 'neural_network']
                for name in supervised_detectors:
                    if name in self.detectors:
                        try:
                            self.detectors[name].fit(X, y)
                            logger.info(f"Trained {name} detector")
                        except Exception as e:
                            logger.warning(f"Failed to train {name}: {e}")
                            self.weights[name] = 0  # 设置权重为0

            # 标准化权重
            total_weight = sum(self.weights.values())
            if total_weight > 0:
                for name in self.weights:
                    self.weights[name] /= total_weight
            else:
                # 如果所有权重都为0，设置平均权重
                n_detectors = len([w for w in self.weights.values() if w > 0])
                if n_detectors > 0:
                    for name in self.weights:
                        self.weights[name] = 1.0 / n_detectors if self.weights[name] > 0 else 0

            # 置信度校准
            if y is not None and self.config.confidence_calibration:
                self._calibrate_confidence(X, y)

            self.is_fitted = True
            logger.info("Ensemble training completed")
            return self

        except Exception as e:
            logger.error(f"Error fitting ensemble: {e}")
            raise

    def _calibrate_confidence(self, X: np.ndarray, y: np.ndarray) -> None:
        """校准置信度"""
        try:
            # 获取集成预测概率
            ensemble_probas = self.predict_proba(X)[:, 1]

            # 使用Platt缩放或Isotonic回归进行校准
            if len(np.unique(y)) == 2:
                self.calibrator = IsotonicRegression(out_of_bounds='clip')
                self.calibrator.fit(ensemble_probas, y)
                logger.info("Confidence calibration completed")

        except Exception as e:
            logger.warning(f"Confidence calibration failed: {e}")

    def predict(self, X: np.ndarray) -> np.ndarray:
        """集成预测"""
        if not self.is_fitted:
            raise ValueError("Ensemble must be fitted before prediction")

        # 获取各个检测器的预测
        predictions = {}
        for name, detector in self.detectors.items():
            if self.weights[name] > 0:
                try:
                    if hasattr(detector, 'predict') and detector.is_fitted:
                        pred = detector.predict(X)
                        predictions[name] = pred
                except Exception as e:
                    logger.warning(f"Prediction failed for {name}: {e}")
                    predictions[name] = np.zeros(len(X))

        # 加权投票
        if not predictions:
            return np.zeros(len(X))

        weighted_predictions = np.zeros(len(X))
        total_weight = 0

        for name, pred in predictions.items():
            weight = self.weights[name]
            if weight > 0:
                weighted_predictions += weight * pred
                total_weight += weight

        if total_weight > 0:
            weighted_predictions /= total_weight
            return (weighted_predictions > 0.5).astype(int)
        else:
            return np.zeros(len(X))

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """集成概率预测"""
        if not self.is_fitted:
            raise ValueError("Ensemble must be fitted before prediction")

        # 获取各个检测器的概率预测
        probabilities = {}
        for name, detector in self.detectors.items():
            if self.weights[name] > 0:
                try:
                    if hasattr(detector, 'predict_proba') and detector.is_fitted:
                        proba = detector.predict_proba(X)
                        # 确保是异常概率（通常是第1列）
                        if proba.shape[1] > 1:
                            probabilities[name] = proba[:, 1]
                        else:
                            probabilities[name] = proba.flatten()
                except Exception as e:
                    logger.warning(f"Probability prediction failed for {name}: {e}")
                    probabilities[name] = np.zeros(len(X))

        # 加权平均概率
        if not probabilities:
            return np.column_stack([np.ones(len(X)), np.zeros(len(X))])

        weighted_probabilities = np.zeros(len(X))
        total_weight = 0

        for name, proba in probabilities.items():
            weight = self.weights[name]
            if weight > 0:
                weighted_probabilities += weight * proba
                total_weight += weight

        if total_weight > 0:
            weighted_probabilities /= total_weight
        else:
            weighted_probabilities = np.zeros(len(X))

        # 应用置信度校准
        if self.calibrator is not None:
            weighted_probabilities = self.calibrator.transform(weighted_probabilities)

        # 确保概率在合理范围内
        weighted_probabilities = np.clip(weighted_probabilities, 0.001, 0.999)

        return np.column_stack([1 - weighted_probabilities, weighted_probabilities])

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """集成决策函数"""
        probas = self.predict_proba(X)
        return probas[:, 1] - 0.5  # 返回与0.5的偏差

    def get_feature_importance(self) -> Dict[str, np.ndarray]:
        """获取各检测器的特征重要性"""
        importance = {}
        for name, detector in self.detectors.items():
            if hasattr(detector, 'get_feature_importance') and detector.is_fitted:
                try:
                    importance[name] = detector.get_feature_importance()
                except Exception as e:
                    logger.warning(f"Failed to get feature importance for {name}: {e}")
        return importance

    def get_ensemble_weights(self) -> Dict[str, float]:
        """获取集成权重"""
        return self.weights.copy()


class MLAnomalyDetector:
    """ML异常检测器主类"""

    def __init__(self,
                 config: Optional[EnsembleConfig] = None,
                 ml_config: Optional[MLModelConfig] = None):
        self.config = config or get_behavioral_config().ensemble
        self.ml_config = ml_config or get_behavioral_config().ml_models
        self.ensemble = EnsembleAnomalyDetector(self.config, self.ml_config)
        self.feature_selector = None

    def detect_anomalies(self,
                        X: np.ndarray,
                        y: Optional[np.ndarray] = None,
                        feature_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        检测异常

        Args:
            X: 特征矩阵
            y: 标签（可选，用于监督学习）
            feature_names: 特征名称列表

        Returns:
            异常检测结果
        """
        try:
            logger.info(f"Starting ML anomaly detection with {X.shape[0]} samples, {X.shape[1]} features")

            results = {
                'detection_time': datetime.now().isoformat(),
                'data_shape': X.shape,
                'has_labels': y is not None
            }

            # 特征选择
            if feature_names:
                self.feature_names = feature_names
                X_selected, selected_features = self._select_features(X, y)
                results['feature_selection'] = {
                    'original_features': len(feature_names),
                    'selected_features': len(selected_features),
                    'selected_feature_names': selected_features
                }
            else:
                X_selected = X

            # 训练集成模型
            self.ensemble.fit(X_selected, y)

            # 预测异常
            predictions = self.ensemble.predict(X_selected)
            probabilities = self.ensemble.predict_proba(X_selected)
            decision_scores = self.ensemble.decision_function(X_selected)

            # 分析结果
            results['predictions'] = {
                'binary_predictions': predictions.tolist(),
                'anomaly_probabilities': probabilities[:, 1].tolist(),
                'decision_scores': decision_scores.tolist(),
                'num_anomalies': int(np.sum(predictions)),
                'anomaly_rate': float(np.mean(predictions))
            }

            # 特征重要性
            feature_importance = self.ensemble.get_feature_importance()
            if feature_importance:
                results['feature_importance'] = {}
                for name, importance_scores in feature_importance.items():
                    if feature_names:
                        importance_dict = dict(zip(feature_names, importance_scores))
                        # 取前N个最重要的特征
                        top_features = sorted(importance_dict.items(), key=lambda x: abs(x[1]), reverse=True)[:self.config.top_features_count]
                        results['feature_importance'][name] = top_features
                    else:
                        results['feature_importance'][name] = importance_scores.tolist()

            # 集成权重信息
            results['ensemble_weights'] = self.ensemble.get_ensemble_weights()

            # 异常类型分析
            results['anomaly_analysis'] = self._analyze_anomalies(X_selected, predictions, probabilities)

            # 模型性能评估（如果有标签）
            if y is not None:
                results['performance_metrics'] = self._evaluate_performance(y, predictions, probabilities)

            logger.info(f"Anomaly detection completed, found {results['predictions']['num_anomalies']} anomalies")
            return results

        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")
            return {'error': str(e)}

    def _select_features(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> Tuple[np.ndarray, List[str]]:
        """特征选择"""
        try:
            if y is not None and len(np.unique(y)) > 1:
                # 监督特征选择
                selector = SelectKBest(f_classif, k=min(self.config.top_features_count, X.shape[1]))
                X_selected = selector.fit_transform(X, y)
                selected_indices = selector.get_support(indices=True)
            else:
                # 无监督特征选择（使用方差分析）
                feature_variances = np.var(X, axis=0)
                top_indices = np.argsort(feature_variances)[-self.config.top_features_count:]
                X_selected = X[:, top_indices]
                selected_indices = top_indices

            selected_features = [self.feature_names[i] for i in selected_indices]
            return X_selected, selected_features

        except Exception as e:
            logger.warning(f"Feature selection failed: {e}, using all features")
            return X, self.feature_names

    def _analyze_anomalies(self, X: np.ndarray, predictions: np.ndarray, probabilities: np.ndarray) -> Dict[str, Any]:
        """分析异常特征"""
        try:
            anomaly_analysis = {}

            # 异常样本的统计特征
            anomaly_mask = predictions == 1
            normal_mask = predictions == 0

            if np.sum(anomaly_mask) > 0:
                anomaly_data = X[anomaly_mask]
                normal_data = X[normal_mask] if np.sum(normal_mask) > 0 else None

                # 计算异常和正常样本的特征差异
                feature_differences = {}
                for i in range(X.shape[1]):
                    feature_name = self.feature_names[i] if self.feature_names else f"feature_{i}"
                    anomaly_values = anomaly_data[:, i]
                    normal_values = normal_data[:, i] if normal_data is not None else None

                    if normal_values is not None:
                        # 计算统计差异
                        diff_stats = {
                            'mean_difference': float(np.mean(anomaly_values) - np.mean(normal_values)),
                            'std_difference': float(np.std(anomaly_values) - np.std(normal_values)),
                            'effect_size': float((np.mean(anomaly_values) - np.mean(normal_values)) / np.sqrt((np.var(anomaly_values) + np.var(normal_values)) / 2))
                        }
                        feature_differences[feature_name] = diff_stats

                anomaly_analysis['feature_differences'] = feature_differences

            # 异常置信度分析
            anomaly_confidences = probabilities[anomaly_mask, 1] if np.sum(anomaly_mask) > 0 else np.array([])
            if len(anomaly_confidences) > 0:
                anomaly_analysis['confidence_analysis'] = {
                    'mean_confidence': float(np.mean(anomaly_confidences)),
                    'std_confidence': float(np.std(anomaly_confidences)),
                    'high_confidence_anomalies': int(np.sum(anomaly_confidences > 0.8)),
                    'low_confidence_anomalies': int(np.sum(anomaly_confidences < 0.6))
                }

            # 异常聚类分析
            if np.sum(anomaly_mask) > 1:
                anomaly_data = X[anomaly_mask]
                # 简单的聚类分析（使用K-means）
                try:
                    from sklearn.cluster import KMeans
                    n_clusters = min(5, len(anomaly_data))
                    if n_clusters > 1:
                        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
                        cluster_labels = kmeans.fit_predict(anomaly_data)

                        anomaly_analysis['clustering_analysis'] = {
                            'num_clusters': n_clusters,
                            'cluster_sizes': [int(np.sum(cluster_labels == i)) for i in range(n_clusters)],
                            'cluster_centers': kmeans.cluster_centers_.tolist()
                        }
                except Exception as e:
                    logger.warning(f"Clustering analysis failed: {e}")

            return anomaly_analysis

        except Exception as e:
            logger.warning(f"Error in anomaly analysis: {e}")
            return {'error': str(e)}

    def _evaluate_performance(self, y_true: np.ndarray, y_pred: np.ndarray, y_proba: np.ndarray) -> Dict[str, Any]:
        """评估模型性能"""
        try:
            performance = {}

            # 基础分类指标
            if len(np.unique(y_true)) == 2:
                performance['classification_report'] = classification_report(y_true, y_pred, output_dict=True)
                performance['confusion_matrix'] = confusion_matrix(y_true, y_pred).tolist()

                # ROC AUC
                if y_proba.shape[1] > 1:
                    performance['roc_auc'] = float(roc_auc_score(y_true, y_proba[:, 1]))

            # 交叉验证
            if len(np.unique(y_true)) > 1 and len(y_true) > 10:
                try:
                    cv_scores = cross_val_score(
                        self.ensemble.detectors.get('random_forest', self.ensemble.detectors.get('gradient_boosting')),
                        self.ensemble.scaler.transform(self.ensemble.feature_selector.transform(X) if hasattr(self.ensemble, 'feature_selector') else X),
                        y_true,
                        cv=5,
                        scoring='f1'
                    )
                    performance['cross_validation'] = {
                        'mean_f1_score': float(np.mean(cv_scores)),
                        'std_f1_score': float(np.std(cv_scores)),
                        'cv_scores': cv_scores.tolist()
                    }
                except Exception as e:
                    logger.warning(f"Cross validation failed: {e}")

            return performance

        except Exception as e:
            logger.warning(f"Error in performance evaluation: {e}")
            return {'error': str(e)}


if __name__ == "__main__":
    # 测试代码
    print("Testing ML Anomaly Detector...")

    # 生成测试数据
    np.random.seed(42)
    n_samples = 1000
    n_features = 20

    # 生成正常数据
    normal_data = np.random.multivariate_normal(
        mean=[0] * n_features,
        cov=np.eye(n_features),
        size=int(n_samples * 0.9)
    )

    # 生成异常数据
    anomaly_data = np.random.multivariate_normal(
        mean=[3] * n_features,  # 异常数据有明显的均值偏移
        cov=np.eye(n_features) * 2,  # 更大的方差
        size=int(n_samples * 0.1)
    )

    # 合并数据
    X = np.vstack([normal_data, anomaly_data])
    y = np.hstack([np.zeros(len(normal_data)), np.ones(len(anomaly_data))])

    # 创建特征名称
    feature_names = [f"feature_{i}" for i in range(n_features)]

    # 创建检测器
    detector = MLAnomalyDetector()

    # 运行异常检测
    results = detector.detect_anomalies(X, y, feature_names)

    # 显示结果摘要
    print("\n=== Anomaly Detection Results ===")
    if 'predictions' in results:
        predictions = results['predictions']
        print(f"Total samples: {len(y)}")
        print(f"Detected anomalies: {predictions['num_anomalies']}")
        print(f"Actual anomalies: {int(np.sum(y))}")
        print(f"Anomaly rate: {predictions['anomaly_rate']:.3f}")

    print("\n=== Feature Importance ===")
    if 'feature_importance' in results:
        for model_name, importance in results['feature_importance'].items():
            print(f"\n{model_name} top features:")
            for feature, score in importance[:5]:
                print(f"  {feature}: {score:.4f}")

    print("\n=== Ensemble Weights ===")
    if 'ensemble_weights' in results:
        weights = results['ensemble_weights']
        for model, weight in weights.items():
            if weight > 0:
                print(f"{model}: {weight:.4f}")

    print("\n=== Anomaly Analysis ===")
    if 'anomaly_analysis' in results:
        analysis = results['anomaly_analysis']
        if 'confidence_analysis' in analysis:
            conf = analysis['confidence_analysis']
            print(f"Mean anomaly confidence: {conf['mean_confidence']:.3f}")
            print(f"High confidence anomalies: {conf['high_confidence_anomalies']}")
            print(f"Low confidence anomalies: {conf['low_confidence_anomalies']}")

    print("\n=== Performance Metrics ===")
    if 'performance_metrics' in results:
        perf = results['performance_metrics']
        if 'roc_auc' in perf:
            print(f"ROC AUC Score: {perf['roc_auc']:.4f}")
        if 'cross_validation' in perf:
            cv = perf['cross_validation']
            print(f"Cross-validation F1 Score: {cv['mean_f1_score']:.4f} ± {cv['std_f1_score']:.4f}")

    print("\n✅ ML Anomaly Detector test completed successfully!")
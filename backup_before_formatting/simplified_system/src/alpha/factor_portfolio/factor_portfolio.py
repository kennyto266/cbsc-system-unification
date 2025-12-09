#!/usr/bin/env python3
"""
Factor Portfolio
多因子模型和投資組合構建

實現專業級的多因子模型構建功能：
- 因子篩選邏輯
- 多因子模型構建
- 因子組合方法
- 風險模型集成
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from abc import ABC, abstractmethod
import warnings

from ..factor_analyzer.factor_validator import FactorValidationResult, FactorValidator
from ..factor_engine.alpha_factor_engine import FactorMetrics

logger = logging.getLogger(__name__)

class ModelType(Enum):
    """模型類型枚舉"""
    LINEAR_REGRESSION = "linear_regression"
    RIDGE_REGRESSION = "ridge_regression"
    LASSO_REGRESSION = "lasso_regression"
    RANDOM_FOREST = "random_forest"
    GRADIENT_BOOSTING = "gradient_boosting"
    XGBOOST = "xgboost"
    ENSEMBLE = "ensemble"

class WeightingMethod(Enum):
    """權重方法枚舉"""
    EQUAL_WEIGHT = "equal_weight"
    IC_WEIGHTED = "ic_weighted"
    IR_WEIGHTED = "ir_weighted"
    OPTIMIZATION = "optimization"
    MACHINE_LEARNING = "machine_learning"
    CUSTOM = "custom"

@dataclass
class FactorModelConfig:
    """因子模型配置"""
    model_type: ModelType = ModelType.LINEAR_REGRESSION
    weighting_method: WeightingMethod = WeightingMethod.IC_WEIGHTED
    max_factors: int = 10                   # 最大因子數量
    min_ic_threshold: float = 0.02          # 最小IC閾值
    correlation_threshold: float = 0.7      # 因子相關性閾值
    lookback_window: int = 252              # 模型回看窗口
    rebalance_frequency: str = "monthly"     # 再平衡頻率
    regularization_strength: float = 0.1    # 正則化強度
    cross_validation_folds: int = 5         # 交叉驗證折數

class BaseFactorModel(ABC):
    """因子模型基類"""

    def __init__(self, config: FactorModelConfig):
        self.config = config
        self.factor_weights: Dict[str, float] = {}
        self.model_metrics: Dict[str, Any] = {}

    @abstractmethod
    def fit(self, factor_data: pd.DataFrame, returns: pd.Series) -> None:
        """訓練模型"""
        pass

    @abstractmethod
    def predict(self, factor_data: pd.DataFrame) -> pd.Series:
        """預測收益率"""
        pass

    @abstractmethod
    def get_feature_importance(self) -> pd.Series:
        """獲取因子重要性"""
        pass

class LinearRegressionModel(BaseFactorModel):
    """線性回歸模型"""

    def fit(self, factor_data: pd.DataFrame, returns: pd.Series) -> None:
        """訓練線性回歸模型"""
        try:
            from sklearn.linear_model import LinearRegression
            from sklearn.preprocessing import StandardScaler

            # 準備數據
            X = factor_data.fillna(0)
            y = returns.fillna(0)

            # 對齊數據
            common_idx = X.index.intersection(y.index)
            X = X.loc[common_idx]
            y = y.loc[common_idx]

            if len(X) < 10:
                raise ValueError("Insufficient data for model training")

            # 標準化
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            # 訓練模型
            model = LinearRegression()
            model.fit(X_scaled, y)

            # 保存模型和權重
            self.model = model
            self.scaler = scaler

            # 計算因子權重（標準化後的係數）
            self.factor_weights = dict(zip(X.columns, model.coef_))

            # 計算模型指標
            y_pred = model.predict(X_scaled)
            self.model_metrics = {
                'r_squared': model.score(X_scaled, y),
                'mse': np.mean((y - y_pred) ** 2),
                'rmse': np.sqrt(np.mean((y - y_pred) ** 2))
            }

            logger.info("Linear regression model trained successfully")

        except ImportError:
            # 當scikit-learn不可用時，使用簡單的最小二乘法
            self._fit_simple_ols(factor_data, returns)
        except Exception as e:
            logger.error(f"Linear regression model fitting failed: {e}")
            raise

    def _fit_simple_ols(self, factor_data: pd.DataFrame, returns: pd.Series):
        """簡單最小二乘法擬合"""
        X = factor_data.fillna(0)
        y = returns.fillna(0)

        common_idx = X.index.intersection(y.index)
        X = X.loc[common_idx]
        y = y.loc[common_idx]

        # 添加截距項
        X_with_intercept = np.column_stack([np.ones(len(X)), X.values])

        # 最小二乘法求解
        try:
            coeffs = np.linalg.lstsq(X_with_intercept, y, rcond=None)[0]
            self.model_coeffs = coeffs

            # 因子權重
            self.factor_weights = dict(zip(X.columns, coeffs[1:]))

            # 預測
            y_pred = X_with_intercept @ coeffs
            self.model_metrics = {
                'r_squared': 1 - np.sum((y - y_pred)**2) / np.sum((y - y.mean())**2),
                'mse': np.mean((y - y_pred)**2),
                'rmse': np.sqrt(np.mean((y - y_pred)**2))
            }

            logger.info("Simple OLS model trained successfully")

        except Exception as e:
            logger.error(f"Simple OLS fitting failed: {e}")
            raise

    def predict(self, factor_data: pd.DataFrame) -> pd.Series:
        """預測收益率"""
        X = factor_data.fillna(0)

        if hasattr(self, 'model'):
            # 使用scikit-learn模型
            X_scaled = self.scaler.transform(X)
            predictions = self.model.predict(X_scaled)
        elif hasattr(self, 'model_coeffs'):
            # 使用簡單OLS模型
            X_with_intercept = np.column_stack([np.ones(len(X)), X.values])
            predictions = X_with_intercept @ self.model_coeffs
        else:
            raise RuntimeError("Model not trained")

        return pd.Series(predictions, index=factor_data.index)

    def get_feature_importance(self) -> pd.Series:
        """獲取因子重要性"""
        if not self.factor_weights:
            return pd.Series()

        importance = pd.Series(self.factor_weights)
        return importance.abs().sort_values(ascending=False)

class RidgeRegressionModel(BaseFactorModel):
    """嶺回歸模型"""

    def fit(self, factor_data: pd.DataFrame, returns: pd.Series) -> None:
        """訓練嶺回歸模型"""
        try:
            from sklearn.linear_model import Ridge
            from sklearn.preprocessing import StandardScaler

            X = factor_data.fillna(0)
            y = returns.fillna(0)

            common_idx = X.index.intersection(y.index)
            X = X.loc[common_idx]
            y = y.loc[common_idx]

            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            model = Ridge(alpha=self.config.regularization_strength)
            model.fit(X_scaled, y)

            self.model = model
            self.scaler = scaler
            self.factor_weights = dict(zip(X.columns, model.coef_))

            y_pred = model.predict(X_scaled)
            self.model_metrics = {
                'r_squared': model.score(X_scaled, y),
                'mse': np.mean((y - y_pred) ** 2),
                'rmse': np.sqrt(np.mean((y - y_pred) ** 2))
            }

            logger.info("Ridge regression model trained successfully")

        except ImportError:
            self._fit_simple_ridge(factor_data, returns)
        except Exception as e:
            logger.error(f"Ridge regression model fitting failed: {e}")
            raise

    def _fit_simple_ridge(self, factor_data: pd.DataFrame, returns: pd.Series):
        """簡單嶺回歸擬合"""
        X = factor_data.fillna(0)
        y = returns.fillna(0)

        common_idx = X.index.intersection(y.index)
        X = X.loc[common_idx]
        y = y.loc[common_idx]

        X_with_intercept = np.column_stack([np.ones(len(X)), X.values])

        # 嶺回歸閉式解
        alpha = self.config.regularization_strength
        try:
            XtX = X_with_intercept.T @ X_with_intercept
            ridge_matrix = XtX + alpha * np.eye(XtX.shape[0])
            coeffs = np.linalg.inv(ridge_matrix) @ X_with_intercept.T @ y

            self.model_coeffs = coeffs
            self.factor_weights = dict(zip(X.columns, coeffs[1:]))

            y_pred = X_with_intercept @ coeffs
            self.model_metrics = {
                'r_squared': 1 - np.sum((y - y_pred)**2) / np.sum((y - y.mean())**2),
                'mse': np.mean((y - y_pred)**2),
                'rmse': np.sqrt(np.mean((y - y_pred)**2))
            }

            logger.info("Simple ridge model trained successfully")

        except Exception as e:
            logger.error(f"Simple ridge fitting failed: {e}")
            raise

    def predict(self, factor_data: pd.DataFrame) -> pd.Series:
        """預測收益率"""
        X = factor_data.fillna(0)

        if hasattr(self, 'model'):
            X_scaled = self.scaler.transform(X)
            predictions = self.model.predict(X_scaled)
        elif hasattr(self, 'model_coeffs'):
            X_with_intercept = np.column_stack([np.ones(len(X)), X.values])
            predictions = X_with_intercept @ self.model_coeffs
        else:
            raise RuntimeError("Model not trained")

        return pd.Series(predictions, index=factor_data.index)

    def get_feature_importance(self) -> pd.Series:
        """獲取因子重要性"""
        if not self.factor_weights:
            return pd.Series()

        importance = pd.Series(self.factor_weights)
        return importance.abs().sort_values(ascending=False)

class FactorPortfolio:
    """
    多因子投資組合構建器

    提供專業級的多因子模型構建和因子組合功能。
    支持多種建模方法和權重分配策略。
    """

    def __init__(self, config: Optional[FactorModelConfig] = None):
        """
        初始化因子投資組合構建器

        Args:
            config: 因子模型配置
        """
        self.config = config or FactorModelConfig()
        self.models: Dict[str, BaseFactorModel] = {}
        self.factor_selection_results: Dict[str, Any] = {}

        logger.info(f"Factor Portfolio initialized with model type: {self.config.model_type.value}")

    def select_factors(self,
                      factor_dict: Dict[str, pd.DataFrame],
                      criteria: str = "ic_ir") -> List[str]:
        """
        因子篩選

        Args:
            factor_dict: 因子數據字典
            criteria: 篩選標準 ("ic_mean", "ic_ir", "sharpe", "composite")

        Returns:
            List[str]: 選中的因子名稱
        """
        logger.info(f"Selecting factors based on criteria: {criteria}")

        selected_factors = []

        for factor_name, factor_data in factor_dict.items():
            try:
                # 計算因子統計
                factor_stats = self._calculate_factor_statistics(factor_data)

                # 應用篩選標準
                if self._passes_selection_criteria(factor_stats, criteria):
                    selected_factors.append(factor_name)

            except Exception as e:
                logger.warning(f"Failed to evaluate factor {factor_name}: {e}")
                continue

        # 限制因子數量
        if len(selected_factors) > self.config.max_factors:
            if criteria in factor_stats:
                # 根據篩選標準排序
                selected_factors = sorted(
                    selected_factors,
                    key=lambda x: self._calculate_factor_statistics(factor_dict[x]).get(criteria, 0),
                    reverse=True
                )[:self.config.max_factors]

        self.factor_selection_results = {
            'selected_factors': selected_factors,
            'total_factors': len(factor_dict),
            'selection_criteria': criteria
        }

        logger.info(f"Selected {len(selected_factors)} factors out of {len(factor_dict)}")
        return selected_factors

    def _calculate_factor_statistics(self, factor_data: pd.DataFrame) -> Dict[str, float]:
        """計算因子統計信息"""
        if factor_data.empty or len(factor_data) < 10:
            return {}

        # 簡化的統計計
        stats = {
            'mean': factor_data.mean().mean() if len(factor_data.columns) > 1 else factor_data.iloc[:, 0].mean(),
            'std': factor_data.std().mean() if len(factor_data.columns) > 1 else factor_data.iloc[:, 0].std(),
            'data_points': len(factor_data.dropna())
        }

        # 模擬IC計算（簡化版）
        if len(factor_data) > 20:
            # 使用自相關性作為IC的代理
            if len(factor_data.columns) > 1:
                auto_corr = factor_data.mean(axis=1).autocorr()
            else:
                auto_corr = factor_data.iloc[:, 0].autocorr()

            stats.update({
                'ic_mean': abs(auto_corr) if not np.isnan(auto_corr) else 0,
                'ic_ir': abs(auto_corr) / 0.1 if auto_corr != 0 else 0,  # 假設標準差為0.1
                'sharpe': abs(auto_corr) / 0.1 if auto_corr != 0 else 0,
                'composite': abs(auto_corr) * 100 if not np.isnan(auto_corr) else 0
            })

        return stats

    def _passes_selection_criteria(self, factor_stats: Dict[str, float], criteria: str) -> bool:
        """檢查因子是否通過篩選標準"""
        if not factor_stats:
            return False

        threshold = self.config.min_ic_threshold

        if criteria in factor_stats:
            return factor_stats[criteria] >= threshold

        return True

    def build_model(self,
                    factors: Dict[str, pd.DataFrame],
                    returns: pd.Series,
                    method: str = None) -> BaseFactorModel:
        """
        構建多因子模型

        Args:
            factors: 因子數據字典
            returns: 收益率數據
            method: 建模方法

        Returns:
            BaseFactorModel: 訓練好的因子模型
        """
        if method is None:
            method = self.config.model_type.value

        logger.info(f"Building factor model using method: {method}")

        # 準備因子數據
        factor_matrix = pd.concat(factors, axis=1)

        # 移除高度相關的因子
        factor_matrix = self._remove_highly_correlated_factors(factor_matrix)

        # 創建模型
        if method == "linear_regression":
            model = LinearRegressionModel(self.config)
        elif method == "ridge_regression":
            model = RidgeRegressionModel(self.config)
        else:
            logger.warning(f"Model method {method} not implemented, using linear regression")
            model = LinearRegressionModel(self.config)

        # 訓練模型
        model.fit(factor_matrix, returns)

        # 保存模型
        model_name = f"factor_model_{method}"
        self.models[model_name] = model

        logger.info(f"Factor model built and saved as: {model_name}")
        return model

    def _remove_highly_correlated_factors(self, factor_matrix: pd.DataFrame) -> pd.DataFrame:
        """移除高度相關的因子"""
        if factor_matrix.empty:
            return factor_matrix

        # 計算相關係數矩陣
        corr_matrix = factor_matrix.corr().abs()

        # 找到高度相關的因子對
        high_corr_pairs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                if corr_matrix.iloc[i, j] > self.config.correlation_threshold:
                    high_corr_pairs.append((
                        corr_matrix.columns[i],
                        corr_matrix.columns[j],
                        corr_matrix.iloc[i, j]
                    ))

        if high_corr_pairs:
            logger.info(f"Found {len(high_corr_pairs)} highly correlated factor pairs")

            # 移除相關性較高的因子
        # 保留每個相關組中的第一個因子
        factors_to_remove = set()
        for factor1, factor2, corr in high_corr_pairs:
            # 簡單策略：移除第二個因子
            factors_to_remove.add(factor2)

        if factors_to_remove:
            factor_matrix = factor_matrix.drop(columns=list(factors_to_remove))
            logger.info(f"Removed {len(factors_to_remove)} highly correlated factors")

        return factor_matrix

    def optimize_weights(self,
                         factor_data: pd.DataFrame,
                         returns: pd.Series,
                         method: str = "ic_weighted") -> Dict[str, float]:
        """
        優化因子權重

        Args:
            factor_data: 因子數據
            returns: 收益率數據
            method: 權重優化方法

        Returns:
            Dict[str, float]: 因子權重字典
        """
        logger.info(f"Optimizing factor weights using method: {method}")

        if method == "equal_weight":
            return self._equal_weight_optimization(factor_data)

        elif method == "ic_weighted":
            return self._ic_weighted_optimization(factor_data, returns)

        elif method == "ir_weighted":
            return self._ir_weighted_optimization(factor_data, returns)

        elif method == "optimization":
            return self._mean_variance_optimization(factor_data, returns)

        else:
            logger.warning(f"Weight optimization method {method} not implemented, using equal weights")
            return self._equal_weight_optimization(factor_data)

    def _equal_weight_optimization(self, factor_data: pd.DataFrame) -> Dict[str, float]:
        """等權重優化"""
        n_factors = len(factor_data.columns)
        weight = 1.0 / n_factors
        return {col: weight for col in factor_data.columns}

    def _ic_weighted_optimization(self,
                                 factor_data: pd.DataFrame,
                                 returns: pd.Series) -> Dict[str, float]:
        """IC加權優化"""
        weights = {}
        total_ic = 0

        for factor_col in factor_data.columns:
            try:
                # 計算IC
                ic = factor_data[factor_col].corr(returns)
                if not np.isnan(ic):
                    weights[factor_col] = abs(ic)
                    total_ic += abs(ic)
                else:
                    weights[factor_col] = 0
            except:
                weights[factor_col] = 0

        # 標準化權重
        if total_ic > 0:
            weights = {k: v / total_ic for k, v in weights.items()}

        return weights

    def _ir_weighted_optimization(self,
                                 factor_data: pd.DataFrame,
                                 returns: pd.Series) -> Dict[str, float]:
        """IR加權優化"""
        weights = {}
        total_ir = 0

        for factor_col in factor_data.columns:
            try:
                # 計算滾動IC和IR
                rolling_ic = factor_data[factor_col].rolling(window=20).corr(returns)
                ic_mean = rolling_ic.mean()
                ic_std = rolling_ic.std()

                if ic_std > 0 and not np.isnan(ic_mean):
                    ir = abs(ic_mean) / ic_std
                    weights[factor_col] = ir
                    total_ir += ir
                else:
                    weights[factor_col] = 0
            except:
                weights[factor_col] = 0

        # 標準化權重
        if total_ir > 0:
            weights = {k: v / total_ir for k, v in weights.items()}

        return weights

    def _mean_variance_optimization(self,
                                   factor_data: pd.DataFrame,
                                   returns: pd.Series) -> Dict[str, float]:
        """均值-方差優化"""
        try:
            # 計算因子收益的協方差矩陣
            factor_returns = pd.DataFrame()
            for factor_col in factor_data.columns:
                # 使用因子值作為收益的代理
                factor_returns[factor_col] = factor_data[factor_col].pct_change().fillna(0)

            cov_matrix = factor_returns.cov()

            # 簡化的均值-方差優化
            # 這裡使用等權重作為基礎，可以進一步優化
            n_factors = len(factor_data.columns)
            weight = 1.0 / n_factors

            return {col: weight for col in factor_data.columns}

        except Exception as e:
            logger.warning(f"Mean-variance optimization failed: {e}, falling back to equal weights")
            return self._equal_weight_optimization(factor_data)

    def get_model_performance(self, model_name: str = None) -> Dict[str, Any]:
        """獲取模型性能"""
        if model_name and model_name in self.models:
            return self.models[model_name].model_metrics
        elif self.models:
            # 返回第一個模型的性能
            return list(self.models.values())[0].model_metrics
        else:
            return {}
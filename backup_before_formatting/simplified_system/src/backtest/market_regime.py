#!/usr/bin/env python3
"""
動態資產配置系統 - 市場制度檢測和預測
Dynamic Asset Allocation System - Market Regime Detection and Prediction

使用Hidden Markov Model識別市場制度，包含制度預測和置信區間
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

try:
    from hmmlearn import hmm
    HMM_AVAILABLE = True
except ImportError:
    HMM_AVAILABLE = False
    logging.warning("hmmlearn not available. Install with: pip install hmmlearn")

from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from scipy import stats
import joblib
import os

logger = logging.getLogger(__name__)

@dataclass
class RegimeConfig:
    """市場制度檢測配置"""
    # HMM參數
    n_regimes: int = 3  # 制度數量
    n_components: int = 5  # 觀測特徵維度
    covariance_type: str = 'full'  # 'full', 'tied', 'diag', 'spherical'
    n_iter: int = 100  # EM迭代次數
    random_state: int = 42

    # 特徵工程參數
    volatility_window: int = 20  # 波動率計算窗口
    trend_window: int = 50  # 趨勢計算窗口
    momentum_window: int = 10  # 動量計算窗口
    correlation_window: int = 30  # 相關性計算窗口

    # 預測參數
    prediction_horizon: int = 5  # 預測天數
    confidence_threshold: float = 0.7  # 置信度閾值

    # 平滑參數
    transition_smoothing: float = 0.1  # 轉移矩陣平滑因子

@dataclass
class RegimeState:
    """市場制度狀態"""
    regime_id: int
    regime_name: str
    probability: float
    characteristics: Dict[str, float]

    # 制度特徵
    volatility_level: float  # 波動率水平 (Low/Medium/High)
    trend_strength: float    # 趨勢強度 (Weak/Neutral/Strong)
    correlation_level: float # 相關性水平 (Low/Medium/High)
    momentum_direction: float # 動量方向 (Negative/Neutral/Positive)

@dataclass
class RegimePrediction:
    """制度預測結果"""
    current_regime: RegimeState
    predicted_regimes: List[Tuple[RegimeState, float]]  # (regime, probability)
    confidence_intervals: Dict[str, Tuple[float, float]]  # 置信區間
    transition_probabilities: np.ndarray  # 轉移概率矩陣

    # 預測統計
    prediction_confidence: float
    regime_stability: float  # 制度穩定性
    expected_duration: float  # 預期持續時間

class MarketRegimeDetector:
    """
    市場制度檢測器

    使用Hidden Markov Model檢測和預測市場制度
    """

    # 預定義制度類型
    REGIME_TYPES = {
        0: "Bull Market",
        1: "Bear Market",
        2: "Sideways/Range-Bound"
    }

    def __init__(self, config: Optional[RegimeConfig] = None):
        """初始化市場制度檢測器"""
        self.config = config or RegimeConfig()

        if not HMM_AVAILABLE:
            logger.warning("hmmlearn not available, using simplified detection")
            self.hmm_model = None
        else:
            self.hmm_model = hmm.GaussianHMM(
                n_components=self.config.n_regimes,
                covariance_type=self.config.covariance_type,
                n_iter=self.config.n_iter,
                random_state=self.config.random_state
            )

        # 數據預處理器
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=self.config.n_components)

        # 模型狀態
        self.is_fitted = False
        self.feature_columns = []
        self.regime_history = []

        # 緩存
        self._cache = {}

        logger.info("Market Regime Detector initialized")

    def extract_features(self, data: Union[pd.DataFrame, Dict[str, pd.DataFrame]]) -> np.ndarray:
        """
        提取市場制度特徵

        Args:
            data: OHLCV數據，可以是單個DataFrame或多個資產的字典

        Returns:
            特徵矩陣
        """
        if isinstance(data, dict):
            # 多資產情況，計算市場級特徵
            return self._extract_multi_asset_features(data)
        else:
            # 單資產情況
            return self._extract_single_asset_features(data)

    def _extract_single_asset_features(self, data: pd.DataFrame) -> np.ndarray:
        """提取單資產特徵"""
        features = []

        close = data['close']
        high = data['high']
        low = data['low']
        volume = data['volume']

        # 1. 波動率特徵
        returns = close.pct_change()
        volatility = returns.rolling(self.config.volatility_window).std()
        features.extend([
            volatility,
            volatility.rolling(5).mean(),  # 短期波動率
            volatility.rolling(20).mean()  # 長期波動率
        ])

        # 2. 趨勢特徵
        sma_short = close.rolling(self.config.trend_window // 2).mean()
        sma_long = close.rolling(self.config.trend_window).mean()
        trend_strength = (sma_short / sma_long - 1)
        features.extend([
            trend_strength,
            trend_strength.rolling(5).mean(),
            trend_strength.diff()  # 趨勢變化
        ])

        # 3. 動量特徵
        momentum = close.pct_change(self.config.momentum_window)
        features.extend([
            momentum,
            momentum.rolling(5).mean(),
            momentum.rolling(20).std()  # 動量波動率
        ])

        # 4. 價格特徵
        price_position = (close - low.rolling(20).min()) / (high.rolling(20).max() - low.rolling(20).min())
        features.extend([
            price_position,
            high.rolling(20).max() / close - 1,  # 距離高點距離
            close / low.rolling(20).min() - 1    # 距離低點距離
        ])

        # 5. 成交量特徵
        volume_ma = volume.rolling(20).mean()
        volume_ratio = volume / volume_ma
        features.extend([
            volume_ratio,
            volume_ratio.rolling(5).mean(),
            volume_ratio.rolling(5).std()
        ])

        # 組合特徵並轉置
        feature_matrix = np.array([f.values for f in features]).T

        # 處理NaN值
        feature_matrix = pd.DataFrame(feature_matrix).fillna(method='ffill').fillna(0).values

        return feature_matrix

    def _extract_multi_asset_features(self, data_dict: Dict[str, pd.DataFrame]) -> np.ndarray:
        """提取多資產特徵"""
        # 計算市場級特徵
        returns_list = []
        volumes_list = []

        for symbol, data in data_dict.items():
            returns = data['close'].pct_change()
            returns_list.append(returns)
            volumes_list.append(data['volume'])

        # 創建回報率矩陣
        returns_matrix = pd.concat(returns_list, axis=1)
        volumes_matrix = pd.concat(volumes_list, axis=1)

        features = []

        # 1. 市場波動率特徵
        market_vol = returns_matrix.std(axis=1)
        features.extend([
            market_vol,
            market_vol.rolling(5).mean(),
            market_vol.rolling(20).mean()
        ])

        # 2. 相關性特徵
        rolling_corr = returns_matrix.rolling(self.config.correlation_window).corr()
        avg_correlation = []
        for date in rolling_corr.index.levels[0]:
            date_corr = rolling_corr.loc[date]
            avg_corr = date_corr.values[np.triu_indices_from(date_corr.values, k=1)].mean()
            avg_correlation.append(avg_corr)

        avg_correlation = pd.Series(avg_correlation, index=market_vol.index)
        features.extend([
            avg_correlation,
            avg_correlation.rolling(5).mean(),
            avg_correlation.diff()
        ])

        # 3. 市場趨勢特徵
        market_return = returns_matrix.mean(axis=1)
        trend_features = self._calculate_trend_features(market_return)
        features.extend(trend_features)

        # 4. 成交量特徵
        total_volume = volumes_matrix.sum(axis=1)
        volume_features = self._calculate_volume_features(total_volume)
        features.extend(volume_features)

        # 5. 市場廣度特徵
        positive_returns = (returns_matrix > 0).sum(axis=1) / len(returns_matrix.columns)
        features.extend([
            positive_returns,
            positive_returns.rolling(5).mean(),
            positive_returns.rolling(20).std()
        ])

        # 組合特徵
        feature_matrix = np.array([f.values if hasattr(f, 'values') else f for f in features]).T

        # 處理NaN值
        feature_matrix = pd.DataFrame(feature_matrix).fillna(method='ffill').fillna(0).values

        return feature_matrix

    def _calculate_trend_features(self, series: pd.Series) -> List[pd.Series]:
        """計算趨勢特徵"""
        sma_short = series.rolling(self.config.trend_window // 2).mean()
        sma_long = series.rolling(self.config.trend_window).mean()

        return [
            sma_short - sma_long,
            (sma_short / sma_long - 1).rolling(5).mean(),
            series.diff().rolling(5).mean()
        ]

    def _calculate_volume_features(self, volume: pd.Series) -> List[pd.Series]:
        """計算成交量特徵"""
        volume_ma = volume.rolling(20).mean()

        return [
            volume / volume_ma,
            (volume / volume_ma).rolling(5).mean(),
            volume.rolling(20).std()
        ]

    def fit(self, data: Union[pd.DataFrame, Dict[str, pd.DataFrame]]) -> None:
        """
        訓練HMM模型

        Args:
            data: 訓練數據
        """
        logger.info("Training market regime detection model...")

        # 提取特徵
        features = self.extract_features(data)

        # 標準化特徵
        features_scaled = self.scaler.fit_transform(features)

        # 降維（如果特徵維度太高）
        if features_scaled.shape[1] > self.config.n_components:
            features_scaled = self.pca.fit_transform(features_scaled)

        if HMM_AVAILABLE and self.hmm_model is not None:
            # 訓練HMM模型
            self.hmm_model.fit(features_scaled)
            self.is_fitted = True

            # 平滑轉移矩陣
            self._smooth_transition_matrix()

            logger.info(f"HMM model trained with {self.config.n_regimes} regimes")
        else:
            # 使用簡化的K-means分類
            self._fit_simplified_model(features_scaled)

        # 保存特徵列信息
        self.feature_columns = [f"feature_{i}" for i in range(features_scaled.shape[1])]

    def _smooth_transition_matrix(self) -> None:
        """平滑轉移矩陣"""
        if self.hmm_model is None:
            return

        transmat = self.hmm_model.transmat_
        smoothed = transmat * (1 - self.config.transition_smoothing) + \
                  np.ones_like(transmat) * self.config.transition_smoothing / self.config.n_regimes

        # 確保行和為1
        smoothed = smoothed / smoothed.sum(axis=1, keepdims=True)
        self.hmm_model.transmat_ = smoothed

    def _fit_simplified_model(self, features: np.ndarray) -> None:
        """擬合簡化模型（當hmmlearn不可用時）"""
        from sklearn.cluster import KMeans

        self.simple_model = KMeans(n_clusters=self.config.n_regimes, random_state=42)
        self.simple_model.fit(features)
        self.is_fitted = True
        logger.info("Simplified regime detection model trained")

    def predict(self, data: Union[pd.DataFrame, Dict[str, pd.DataFrame]]) -> RegimePrediction:
        """
        預測市場制度

        Args:
            data: 預測數據

        Returns:
            制度預測結果
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")

        # 提取特徵
        features = self.extract_features(data)
        features_scaled = self.scaler.transform(features)

        if hasattr(self, 'pca') and features_scaled.shape[1] > self.config.n_components:
            features_scaled = self.pca.transform(features_scaled)

        if HMM_AVAILABLE and self.hmm_model is not None:
            return self._predict_with_hmm(features_scaled)
        else:
            return self._predict_simplified(features_scaled)

    def _predict_with_hmm(self, features: np.ndarray) -> RegimePrediction:
        """使用HMM進行預測"""
        # 獲取潛在狀態序列
        hidden_states = self.hmm_model.predict(features)
        state_probabilities = self.hmm_model.predict_proba(features)

        # 當前制度
        current_regime_id = hidden_states[-1]
        current_prob = state_probabilities[-1, current_regime_id]

        current_regime = self._create_regime_state(
            current_regime_id, current_prob, features[-1:]
        )

        # 預測未來制度
        predicted_states, prediction_confidence = self._predict_future_regimes(
            current_regime_id
        )

        predicted_regimes = []
        for state_id, prob in predicted_states:
            regime = self._create_regime_state(state_id, prob, features[-1:])
            predicted_regimes.append((regime, prob))

        # 計算置信區間
        confidence_intervals = self._calculate_confidence_intervals(
            features[-20:]  # 使用最近20個數據點
        )

        # 制度穩定性
        regime_stability = self._calculate_regime_stability(hidden_states[-50:])

        # 預期持續時間
        expected_duration = self._calculate_expected_duration(current_regime_id)

        return RegimePrediction(
            current_regime=current_regime,
            predicted_regimes=predicted_regimes,
            confidence_intervals=confidence_intervals,
            transition_probabilities=self.hmm_model.transmat_,
            prediction_confidence=prediction_confidence,
            regime_stability=regime_stability,
            expected_duration=expected_duration
        )

    def _predict_simplified(self, features: np.ndarray) -> RegimePrediction:
        """使用簡化模型進行預測"""
        current_state = self.simple_model.predict(features[-1:].reshape(1, -1))[0]
        current_prob = 1.0  # 簡化模型不提供概率

        current_regime = self._create_regime_state(current_state, current_prob, features[-1:])

        # 簡單的預測邏輯：基於最近狀態的頻率
        recent_states = self.simple_model.predict(features[-10:])
        unique, counts = np.unique(recent_states, return_counts=True)

        predicted_regimes = []
        for state_id, count in zip(unique, counts):
            prob = count / len(recent_states)
            regime = self._create_regime_state(state_id, prob, features[-1:])
            predicted_regimes.append((regime, prob))

        return RegimePrediction(
            current_regime=current_regime,
            predicted_regimes=predicted_regimes,
            confidence_intervals={},
            transition_probabilities=np.eye(self.config.n_regimes),
            prediction_confidence=current_prob,
            regime_stability=0.5,
            expected_duration=10.0
        )

    def _create_regime_state(self, regime_id: int, probability: float, features: np.ndarray) -> RegimeState:
        """創建制度狀態對象"""
        regime_name = self.REGIME_TYPES.get(regime_id, f"Regime_{regime_id}")

        # 基於特徵計算制度特徵
        if len(features.shape) > 1:
            features = features.flatten()

        characteristics = {
            'volatility': float(features[0]) if len(features) > 0 else 0.0,
            'trend': float(features[3]) if len(features) > 3 else 0.0,
            'momentum': float(features[6]) if len(features) > 6 else 0.0,
            'volume': float(features[9]) if len(features) > 9 else 0.0
        }

        # 分類特徵
        volatility_level = self._classify_level(characteristics['volatility'], [-0.02, 0.02])
        trend_strength = self._classify_level(characteristics['trend'], [-0.01, 0.01])
        momentum_direction = self._classify_level(characteristics['momentum'], [-0.01, 0.01])
        correlation_level = 0.0  # 簡化處理

        return RegimeState(
            regime_id=regime_id,
            regime_name=regime_name,
            probability=probability,
            characteristics=characteristics,
            volatility_level=volatility_level,
            trend_strength=trend_strength,
            correlation_level=correlation_level,
            momentum_direction=momentum_direction
        )

    def _classify_level(self, value: float, thresholds: List[float]) -> str:
        """將數值分類為水平"""
        if value < thresholds[0]:
            return "Low"
        elif value > thresholds[1]:
            return "High"
        else:
            return "Medium"

    def _predict_future_regimes(self, current_state: int) -> Tuple[List[Tuple[int, float]], float]:
        """預測未來制度"""
        if self.hmm_model is None:
            return [(current_state, 1.0)], 1.0

        transition_probs = self.hmm_model.transmat_[current_state]

        # 預測未來N步
        future_probs = []
        current_dist = transition_probs.copy()

        for _ in range(self.config.prediction_horizon):
            future_probs.append(current_dist.copy())
            current_dist = current_dist @ self.hmm_model.transmat_

        # 計算平均預測概率
        avg_probs = np.mean(future_probs, axis=0)

        # 排序並返回
        sorted_indices = np.argsort(avg_probs)[::-1]
        predictions = [(int(idx), float(avg_probs[idx])) for idx in sorted_indices[:3]]

        # 預測置信度
        confidence = float(np.max(avg_probs))

        return predictions, confidence

    def _calculate_confidence_intervals(self, features: np.ndarray) -> Dict[str, Tuple[float, float]]:
        """計算置信區間"""
        if len(features) < 10:
            return {}

        confidence_intervals = {}

        for i in range(min(5, features.shape[1])):
            feature_values = features[:, i]
            mean = np.mean(feature_values)
            std = np.std(feature_values)

            # 95%置信區間
            ci_lower = mean - 1.96 * std
            ci_upper = mean + 1.96 * std

            confidence_intervals[f"feature_{i}"] = (float(ci_lower), float(ci_upper))

        return confidence_intervals

    def _calculate_regime_stability(self, recent_states: np.ndarray) -> float:
        """計算制度穩定性"""
        if len(recent_states) < 5:
            return 0.5

        # 計算狀態變化的頻率
        changes = np.sum(recent_states[1:] != recent_states[:-1])
        stability = 1.0 - (changes / len(recent_states))

        return float(stability)

    def _calculate_expected_duration(self, regime_id: int) -> float:
        """計算制度預期持續時間"""
        if self.hmm_model is None:
            return 10.0

        # 使用轉移矩陣對角線元素的倒數
        stay_prob = self.hmm_model.transmat_[regime_id, regime_id]
        if stay_prob >= 1.0:
            return float('inf')

        expected_duration = 1.0 / (1.0 - stay_prob)

        return float(expected_duration)

    def save_model(self, filepath: str) -> None:
        """保存模型"""
        model_data = {
            'config': self.config,
            'scaler': self.scaler,
            'pca': self.pca if hasattr(self, 'pca') else None,
            'hmm_model': self.hmm_model,
            'is_fitted': self.is_fitted,
            'feature_columns': self.feature_columns,
            'simple_model': getattr(self, 'simple_model', None)
        }

        joblib.dump(model_data, filepath)
        logger.info(f"Model saved to {filepath}")

    def load_model(self, filepath: str) -> None:
        """加載模型"""
        model_data = joblib.load(filepath)

        self.config = model_data['config']
        self.scaler = model_data['scaler']
        self.pca = model_data.get('pca')
        self.hmm_model = model_data['hmm_model']
        self.is_fitted = model_data['is_fitted']
        self.feature_columns = model_data['feature_columns']

        if 'simple_model' in model_data:
            self.simple_model = model_data['simple_model']

        logger.info(f"Model loaded from {filepath}")

    def analyze_regime_history(self, data: Union[pd.DataFrame, Dict[str, pd.DataFrame]]) -> pd.DataFrame:
        """
        分析歷史制度

        Args:
            data: 歷史數據

        Returns:
            制度歷史DataFrame
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before analysis")

        # 提取特徵
        features = self.extract_features(data)
        features_scaled = self.scaler.transform(features)

        if hasattr(self, 'pca') and features_scaled.shape[1] > self.config.n_components:
            features_scaled = self.pca.transform(features_scaled)

        # 獲取歷史制度
        if HMM_AVAILABLE and self.hmm_model is not None:
            hidden_states = self.hmm_model.predict(features_scaled)
            state_probabilities = self.hmm_model.predict_proba(features_scaled)
        else:
            hidden_states = self.simple_model.predict(features_scaled)
            state_probabilities = np.zeros((len(features_scaled), self.config.n_regimes))
            for i, state in enumerate(hidden_states):
                state_probabilities[i, state] = 1.0

        # 創建歷史DataFrame
        if isinstance(data, pd.DataFrame):
            index = data.index
        else:
            # 使用第一個資產的索引
            first_symbol = list(data.keys())[0]
            index = data[first_symbol].index

        history_data = []
        for i, (date, state) in enumerate(zip(index, hidden_states)):
            regime = self._create_regime_state(
                state,
                float(state_probabilities[i, state]),
                features_scaled[i:i+1]
            )

            history_data.append({
                'date': date,
                'regime_id': state,
                'regime_name': regime.regime_name,
                'probability': float(state_probabilities[i, state]),
                'volatility_level': regime.volatility_level,
                'trend_strength': regime.trend_strength,
                'momentum_direction': regime.momentum_direction
            })

        return pd.DataFrame(history_data)

    def get_regime_statistics(self) -> Dict[str, Any]:
        """獲取制度統計信息"""
        if not self.is_fitted or self.hmm_model is None:
            return {}

        stats = {
            'n_regimes': self.config.n_regimes,
            'regime_names': [self.REGIME_TYPES.get(i, f"Regime_{i}") for i in range(self.config.n_regimes)],
            'transition_matrix': self.hmm_model.transmat_.tolist(),
            'stationary_distribution': self._calculate_stationary_distribution()
        }

        return stats

    def _calculate_stationary_distribution(self) -> np.ndarray:
        """計算穩態分布"""
        if self.hmm_model is None:
            return np.ones(self.config.n_regimes) / self.config.n_regimes

        # 特徵分解轉移矩陣
        eigenvals, eigenvecs = np.linalg.eig(self.hmm_model.transmat_.T)

        # 找到特徵值為1的特徵向量
        stationary_idx = np.argmin(np.abs(eigenvals - 1))
        stationary = np.real(eigenvecs[:, stationary_idx])

        # 標準化
        stationary = stationary / stationary.sum()

        return stationary

# 便利函數
def detect_market_regimes(
    data: Union[pd.DataFrame, Dict[str, pd.DataFrame]],
    n_regimes: int = 3
) -> RegimePrediction:
    """便利函數：檢測市場制度"""
    config = RegimeConfig(n_regimes=n_regimes)
    detector = MarketRegimeDetector(config)
    detector.fit(data)
    return detector.predict(data)

def analyze_regime_transitions(
    data: Union[pd.DataFrame, Dict[str, pd.DataFrame]],
    model_path: Optional[str] = None
) -> pd.DataFrame:
    """便利函數：分析制度轉換歷史"""
    detector = MarketRegimeDetector()

    if model_path and os.path.exists(model_path):
        detector.load_model(model_path)
    else:
        detector.fit(data)

    return detector.analyze_regime_history(data)
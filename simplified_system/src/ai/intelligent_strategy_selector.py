"""
AI智能策略选择器
基于机器学习的策略优化和自动选择系统
"""

import asyncio
import numpy as np
import pandas as pd
import pickle
import gzip
import hashlib
from typing import Dict, List, Any, Tuple, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import cross_val_score, train_test_split, GridSearchCV
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import joblib
import threading
from collections import deque
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class MarketEnvironment:
    """市场环境特征"""
    timestamp: datetime
    volatility_20d: float
    trend_20d: float
    volume_profile: float
    price_level: float
    market_regime: str  # 'bull', 'bear', 'sideways'
    volatility_regime: str  # 'low', 'normal', 'high'
    liquidity_level: float
    correlation_avg: float
    
@dataclass
class StrategyPerformance:
    """策略性能数据"""
    strategy_name: str
    parameters_hash: str
    sharpe_ratio: float
    total_return: float
    max_drawdown: float
    win_rate: float
    sortino_ratio: float
    calmar_ratio: float
    information_ratio: float
    execution_time: float
    market_environment: MarketEnvironment
    
@dataclass
class PredictionInput:
    """预测输入数据"""
    market_features: np.ndarray
    strategy_features: np.ndarray
    historical_performance: np.ndarray

@dataclass
class PredictionResult:
    """预测结果"""
    predicted_sharpe: float
    predicted_return: float
    predicted_risk: float
    confidence_score: float
    recommended_strategy: str
    optimal_parameters: Dict[str, Any]
    feature_importance: Dict[str, float]

class IntelligentStrategySelector:
    """AI智能策略选择器"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.models = {}
        self.scalers = {}
        self.feature_names = []
        self.is_trained = False
        
        # 模型配置
        self.model_configs = {
            'sharpe_ratio': {
                'models': [
                    GradientBoostingRegressor(n_estimators=100, max_depth=6, random_state=42),
                    RandomForestRegressor(n_estimators=100, max_depth=8, random_state=42),
                    MLPRegressor(hidden_layer_sizes=(100, 50), max_iter=1000, random_state=42)
                ],
                'scaler': StandardScaler(),
                'target_column': 'sharpe_ratio'
            },
            'total_return': {
                'models': [
                    GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42),
                    RandomForestRegressor(n_estimators=150, max_depth=6, random_state=42),
                    SVR(kernel='rbf', C=1.0, gamma='scale')
                ],
                'scaler': MinMaxScaler(),
                'target_column': 'total_return'
            },
            'max_drawdown': {
                'models': [
                    GradientBoostingRegressor(n_estimators=80, max_depth=5, random_state=42),
                    RandomForestRegressor(n_estimators=100, max_depth=7, random_state=42),
                    Ridge(alpha=1.0, random_state=42)
                ],
                'scaler': StandardScaler(),
                'target_column': 'max_drawdown'
            }
        }
        
        # 特征工程配置
        self.feature_engineers = {
            'market_features': [
                'volatility_20d', 'volatility_5d', 'volatility_ratio',
                'trend_20d', 'trend_5d', 'trend_acceleration',
                'volume_ratio_20d', 'volume_ratio_5d',
                'price_position_20d', 'price_position_5d',
                'rsi_14d', 'macd_signal', 'bollinger_position',
                'market_regime_encoded', 'volatility_regime_encoded',
                'day_of_week', 'month_of_year', 'quarter'
            ],
            'strategy_features': [
                'strategy_type_encoded', 'parameter_complexity',
                'risk_level', 'time_horizon', 'market_sensitivity',
                'parameter_regularity', 'adaptation_score'
            ],
            'historical_features': [
                'recent_sharpe_10d', 'recent_sharpe_30d', 'recent_sharpe_90d',
                'recent_return_10d', 'recent_return_30d', 'recent_return_90d',
                'volatility_consistency', 'performance_stability',
                'drawdown_recovery_time', 'win_rate_trend'
            ]
        }
        
        # 数据缓存
        self.training_data_cache = deque(maxlen=10000)
        self.prediction_cache = {}
        self.feature_cache = {}
        
        # 性能监控
        self.performance_stats = {
            'predictions_made': 0,
            'cache_hits': 0,
            'avg_prediction_time': 0.0,
            'model_accuracy': {}
        }
        
        # 自适应学习配置
        self.adaptive_learning = {
            'enabled': True,
            'retrain_threshold': 1000,  # 每1000个新数据点重新训练
            'data_window': 5000,  # 使用最近5000个数据点
            'performance_decay': 0.95  # 性能衰减因子
        }
        
        self.last_retrain_time = datetime.now()
        
        # 如果有预训练模型，加载它们
        if self.model_path:
            self.load_models()
    
    def extract_market_features(self, data: pd.DataFrame, 
                              current_time: Optional[datetime] = None) -> Dict[str, float]:
        """提取市场特征"""
        if current_time is None:
            current_time = datetime.now()
        
        features = {}
        
        # 基础价格特征
        returns = data['close'].pct_change().dropna()
        features['volatility_5d'] = returns.tail(5).std() * np.sqrt(252)
        features['volatility_20d'] = returns.tail(20).std() * np.sqrt(252)
        features['volatility_ratio'] = features['volatility_5d'] / max(features['volatility_20d'], 0.001)
        
        # 趋势特征
        features['trend_5d'] = (data['close'].iloc[-1] / data['close'].iloc[-6] - 1) if len(data) > 5 else 0
        features['trend_20d'] = (data['close'].iloc[-1] / data['close'].iloc[-21] - 1) if len(data) > 20 else 0
        features['trend_acceleration'] = features['trend_5d'] - features['trend_20d'] if features['trend_20d'] != 0 else 0
        
        # 成交量特征
        features['volume_ratio_5d'] = data['volume'].tail(5).mean() / max(data['volume'].tail(20).mean(), 1)
        features['volume_ratio_20d'] = data['volume'].tail(20).mean() / max(data['volume'].tail(60).mean(), 1)
        
        # 价格位置特征
        features['price_position_5d'] = (data['close'].iloc[-1] - data['close'].tail(5).min()) / max(data['close'].tail(5).max() - data['close'].tail(5).min(), 0.001)
        features['price_position_20d'] = (data['close'].iloc[-1] - data['close'].tail(20).min()) / max(data['close'].tail(20).max() - data['close'].tail(20).min(), 0.001)
        
        # 技术指标特征
        features['rsi_14d'] = self._calculate_rsi(data['close'], 14)
        features['macd_signal'] = self._calculate_macd_signal(data['close'])
        features['bollinger_position'] = self._calculate_bollinger_position(data['close'])
        
        # 市场状态特征
        features['market_regime_encoded'] = self._encode_market_regime(data)
        features['volatility_regime_encoded'] = self._encode_volatility_regime(data)
        
        # 时间特征
        features['day_of_week'] = current_time.weekday() / 6.0
        features['month_of_year'] = current_time.month / 12.0
        features['quarter'] = ((current_time.month - 1) // 3) / 3.0
        
        return features
    
    def extract_strategy_features(self, strategy_name: str, 
                                parameters: Dict[str, Any]) -> Dict[str, float]:
        """提取策略特征"""
        features = {}
        
        # 策略类型编码
        strategy_encoding = {
            'RSI': 0, 'MACD': 1, 'BOLLINGER': 2, 
            'SMA_CROSS': 3, 'STOCHASTIC': 4
        }
        features['strategy_type_encoded'] = strategy_encoding.get(strategy_name, -1)
        
        # 参数复杂度
        features['parameter_complexity'] = len(parameters)
        
        # 风险水平（基于参数值估算）
        if strategy_name == 'RSI':
            features['risk_level'] = (parameters.get('overbought', 70) - parameters.get('oversold', 30)) / 40.0
        elif strategy_name == 'MACD':
            features['risk_level'] = (parameters.get('slow', 26) - parameters.get('fast', 12)) / 20.0
        else:
            features['risk_level'] = 0.5
        
        # 时间视野
        features['time_horizon'] = self._estimate_time_horizon(strategy_name, parameters)
        
        # 市场敏感性
        features['market_sensitivity'] = self._estimate_market_sensitivity(strategy_name, parameters)
        
        # 参数规律性
        features['parameter_regularity'] = self._calculate_parameter_regularity(parameters)
        
        # 适应性评分
        features['adaptation_score'] = self._calculate_adaptation_score(strategy_name, parameters)
        
        return features
    
    def extract_historical_features(self, historical_performances: List[StrategyPerformance]) -> Dict[str, float]:
        """提取历史性能特征"""
        if not historical_performances:
            return {}
        
        features = {}
        performances = [p.sharpe_ratio for p in historical_performances]
        returns = [p.total_return for p in historical_performances]
        
        # 不同时间窗口的性能
        if len(performances) >= 10:
            features['recent_sharpe_10d'] = np.mean(performances[-10:])
            features['recent_return_10d'] = np.mean(returns[-10:])
        
        if len(performances) >= 30:
            features['recent_sharpe_30d'] = np.mean(performances[-30:])
            features['recent_return_30d'] = np.mean(returns[-30:])
        
        if len(performances) >= 90:
            features['recent_sharpe_90d'] = np.mean(performances[-90:])
            features['recent_return_90d'] = np.mean(returns[-90:])
        
        # 性能稳定性指标
        features['volatility_consistency'] = 1.0 / (1.0 + np.std(performances)) if np.std(performances) > 0 else 1.0
        features['performance_stability'] = 1.0 - np.std(returns) / (np.mean(np.abs(returns)) + 1e-8)
        
        # 胜率趋势
        win_rates = [p.win_rate for p in historical_performances]
        if len(win_rates) >= 5:
            recent_win_rate = np.mean(win_rates[-5:])
            older_win_rate = np.mean(win_rates[:-5]) if len(win_rates) > 5 else recent_win_rate
            features['win_rate_trend'] = recent_win_rate - older_win_rate
        
        return features
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """计算RSI指标"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1] if not rsi.empty else 50.0
    
    def _calculate_macd_signal(self, prices: pd.Series) -> float:
        """计算MACD信号"""
        exp1 = prices.ewm(span=12).mean()
        exp2 = prices.ewm(span=26).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9).mean()
        return (macd - signal).iloc[-1] if not macd.empty else 0.0
    
    def _calculate_bollinger_position(self, prices: pd.Series) -> float:
        """计算布林带位置"""
        sma = prices.rolling(window=20).mean()
        std = prices.rolling(window=20).std()
        upper = sma + (std * 2)
        lower = sma - (std * 2)
        
        current_price = prices.iloc[-1]
        position = (current_price - lower) / (upper - lower)
        return position if not position.empty else 0.5
    
    def _encode_market_regime(self, data: pd.DataFrame) -> float:
        """编码市场趋势状态"""
        returns = data['close'].pct_change().tail(20)
        
        if len(returns) < 20:
            return 0.5  # unknown
        
        trend = (1 + returns).prod() - 1
        volatility = returns.std()
        
        # 基于趋势和波动率判断市场状态
        if trend > 0.05 and volatility < returns.std() * 1.2:
            return 1.0  # bull
        elif trend < -0.05 and volatility < returns.std() * 1.2:
            return 0.0  # bear
        else:
            return 0.5  # sideways
    
    def _encode_volatility_regime(self, data: pd.DataFrame) -> float:
        """编码波动率状态"""
        returns = data['close'].pct_change().tail(20)
        
        if len(returns) < 20:
            return 1.0
        
        current_vol = returns.std()
        historical_vol = returns.rolling(window=60).std().iloc[-1] if len(returns) >= 60 else current_vol
        
        if current_vol > historical_vol * 1.5:
            return 2.0  # high
        elif current_vol < historical_vol * 0.7:
            return 0.0  # low
        else:
            return 1.0  # normal
    
    def _estimate_time_horizon(self, strategy_name: str, parameters: Dict[str, Any]) -> float:
        """估算策略时间视野"""
        horizon_map = {
            'RSI': 14, 'MACD': 26, 'BOLLINGER': 20,
            'SMA_CROSS': 30, 'STOCHASTIC': 14
        }
        
        base_horizon = horizon_map.get(strategy_name, 20)
        
        # 根据参数调整
        if 'period' in parameters:
            return parameters['period'] / base_horizon
        elif 'short_period' in parameters:
            return parameters['short_period'] / base_horizon
        
        return 1.0
    
    def _estimate_market_sensitivity(self, strategy_name: str, parameters: Dict[str, Any]) -> float:
        """估算市场敏感性"""
        # 基于策略类型的敏感性
        sensitivity_map = {
            'RSI': 0.7, 'MACD': 0.6, 'BOLLINGER': 0.5,
            'SMA_CROSS': 0.4, 'STOCHASTIC': 0.8
        }
        
        base_sensitivity = sensitivity_map.get(strategy_name, 0.5)
        
        # 根据参数调整
        if 'period' in parameters:
            period = parameters['period']
            if period < 10:
                base_sensitivity *= 1.2  # 短期更敏感
            elif period > 30:
                base_sensitivity *= 0.8  # 长期较稳定
        
        return min(1.0, base_sensitivity)
    
    def _calculate_parameter_regularity(self, parameters: Dict[str, Any]) -> float:
        """计算参数规律性"""
        # 计算参数是否为"标准"值
        standard_values = {
            5: 0.9, 10: 0.9, 14: 1.0, 20: 0.9, 26: 0.9,
            30: 0.9, 50: 0.8, 70: 0.9, 75: 0.9, 80: 0.9,
            12: 0.9, 21: 0.9, 9: 0.9, 2: 0.9, 3: 0.9
        }
        
        regularity_score = 0
        param_count = 0
        
        for key, value in parameters.items():
            if isinstance(value, (int, float)):
                regularity_score += standard_values.get(int(value), 0.5)
                param_count += 1
        
        return regularity_score / max(param_count, 1)
    
    def _calculate_adaptation_score(self, strategy_name: str, parameters: Dict[str, Any]) -> float:
        """计算适应性评分"""
        # 基于策略的适应能力评分
        adaptation_map = {
            'RSI': 0.7, 'MACD': 0.8, 'BOLLINGER': 0.9,
            'SMA_CROSS': 0.6, 'STOCHASTIC': 0.5
        }
        
        base_score = adaptation_map.get(strategy_name, 0.5)
        
        # 根据参数调整
        if 'period' in parameters:
            period = parameters['period']
            if 10 <= period <= 30:
                base_score *= 1.2  # 中期参数适应性更强
        
        return min(1.0, base_score)
    
    def create_training_data(self, strategy_performances: List[StrategyPerformance],
                            market_data_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """创建训练数据"""
        training_data = []
        
        for perf in strategy_performances:
            # 提取市场特征
            market_data = market_data_dict.get(perf.strategy_name)
            if market_data is None:
                continue
                
            market_features = self.extract_market_features(market_data, perf.market_environment.timestamp)
            
            # 提取策略特征
            strategy_features = self.extract_strategy_features(perf.strategy_name, {})
            
            # 提取历史特征（这里简化处理）
            historical_features = {
                'recent_sharpe_30d': perf.sharpe_ratio,
                'recent_return_30d': perf.total_return,
                'performance_stability': 1.0 - abs(perf.max_drawdown),
                'volatility_consistency': 1.0 / (1.0 + perf.sortino_ratio) if perf.sortino_ratio > 0 else 1.0
            }
            
            # 合并所有特征
            all_features = {**market_features, **strategy_features, **historical_features}
            
            # 添加目标变量
            all_features.update({
                'sharpe_ratio': perf.sharpe_ratio,
                'total_return': perf.total_return,
                'max_drawdown': perf.max_drawdown
            })
            
            training_data.append(all_features)
        
        return pd.DataFrame(training_data)
    
    def train_models(self, training_data: pd.DataFrame) -> Dict[str, Any]:
        """训练预测模型"""
        logger.info("开始训练AI预测模型...")
        
        # 特征选择
        feature_columns = []
        for feature_list in self.feature_engineers.values():
            feature_columns.extend([f for f in feature_list if f in training_data.columns])
        
        X = training_data[feature_columns]
        
        trained_models = {}
        training_metrics = {}
        
        for target_name, config in self.model_configs.items():
            logger.info(f"训练 {target_name} 预测模型...")
            
            y = training_data[config['target_column']]
            
            # 数据预处理
            scaler = config['scaler']
            X_scaled = scaler.fit_transform(X)
            
            # 训练集成模型
            models = config['models']
            trained_model_list = []
            
            for i, model in enumerate(models):
                try:
                    # 交叉验证评估
                    cv_scores = cross_val_score(model, X_scaled, y, cv=5, scoring='neg_mean_squared_error')
                    
                    # 训练完整模型
                    model.fit(X_scaled, y)
                    trained_model_list.append(model)
                    
                    logger.info(f"  模型 {i+1}: CV RMSE = {np.sqrt(-cv_scores.mean()):.4f}")
                    
                except Exception as e:
                    logger.warning(f"模型 {i+1} 训练失败: {e}")
            
            if trained_model_list:
                # 使用模型平均进行预测
                trained_models[target_name] = {
                    'models': trained_model_list,
                    'scaler': scaler,
                    'feature_columns': feature_columns,
                    'cv_scores': cv_scores
                }
                
                # 计算训练指标
                y_pred = np.mean([model.predict(X_scaled) for model in trained_model_list], axis=0)
                training_metrics[target_name] = {
                    'mse': mean_squared_error(y, y_pred),
                    'mae': mean_absolute_error(y, y_pred),
                    'r2': r2_score(y, y_pred)
                }
                
                logger.info(f"{target_name} 训练完成 - R²: {training_metrics[target_name]['r2']:.4f}")
        
        # 保存模型和特征名称
        self.models = trained_models
        self.scalers = {name: config['scaler'] for name, config in self.model_configs.items() if name in trained_models}
        self.feature_names = feature_columns
        self.is_trained = True
        
        # 保存训练指标
        self.performance_stats['model_accuracy'] = training_metrics
        
        logger.info("AI模型训练完成")
        return trained_models, training_metrics
    
    def predict_strategy_performance(self, market_data: pd.DataFrame, 
                                     strategy_name: str, parameters: Dict[str, Any],
                                     historical_performances: Optional[List[StrategyPerformance]] = None) -> PredictionResult:
        """预测策略性能"""
        if not self.is_trained:
            raise ValueError("模型尚未训练，请先调用 train_models()")
        
        # 检查缓存
        cache_key = self._generate_prediction_cache_key(market_data, strategy_name, parameters, historical_performances)
        if cache_key in self.prediction_cache:
            self.performance_stats['cache_hits'] += 1
            return self.prediction_cache[cache_key]
        
        start_time = time.perf_counter()
        
        # 提取特征
        market_features = self.extract_market_features(market_data)
        strategy_features = self.extract_strategy_features(strategy_name, parameters)
        
        if historical_performances:
            historical_features = self.extract_historical_features(historical_performances)
        else:
            historical_features = {
                'recent_sharpe_30d': 0.0, 'recent_return_30d': 0.0,
                'performance_stability': 0.5, 'volatility_consistency': 1.0
            }
        
        # 构建特征向量
        feature_vector = []
        for feature_name in self.feature_names:
            if feature_name in market_features:
                feature_vector.append(market_features[feature_name])
            elif feature_name in strategy_features:
                feature_vector.append(strategy_features[feature_name])
            elif feature_name in historical_features:
                feature_vector.append(historical_features[feature_name])
            else:
                feature_vector.append(0.0)  # 默认值
        
        X = np.array(feature_vector).reshape(1, -1)
        
        # 进行预测
        predictions = {}
        confidences = {}
        
        for target_name, model_info in self.models.items():
            scaler = model_info['scaler']
            models = model_info['models']
            
            # 特征缩放
            X_scaled = scaler.transform(X)
            
            # 集成预测
            model_predictions = [model.predict(X_scaled)[0] for model in models]
            predictions[target_name] = np.mean(model_predictions)
            confidences[target_name] = 1.0 - (np.std(model_predictions) / (abs(np.mean(model_predictions)) + 1e-8))
        
        # 计算综合置信度
        avg_confidence = np.mean(list(confidences.values()))
        
        # 推荐最优策略（基于预测Sharpe比率）
        predicted_sharpe = predictions['sharpe_ratio']
        predicted_return = predictions['total_return']
        predicted_drawdown = predictions['max_drawdown']
        
        # 计算综合评分
        composite_score = (
            0.5 * predicted_sharpe + 
            0.3 * predicted_return + 
            0.2 * (1.0 - abs(predicted_drawdown))
        )
        
        # 特征重要性分析（基于随机森林模型）
        feature_importance = {}
        if 'sharpe_ratio' in self.models and len(self.models['sharpe_ratio']['models']) > 0:
            rf_model = self.models['sharpe_ratio']['models'][0]
            if hasattr(rf_model, 'feature_importances_'):
                importances = rf_model.feature_importances_
                for i, feature_name in enumerate(self.feature_names):
                    feature_importance[feature_name] = importances[i]
        
        # 创建预测结果
        result = PredictionResult(
            predicted_sharpe=predicted_sharpe,
            predicted_return=predicted_return,
            predicted_risk=abs(predicted_drawdown),
            confidence_score=avg_confidence,
            recommended_strategy=strategy_name,
            optimal_parameters=parameters,
            feature_importance=feature_importance
        )
        
        # 缓存结果
        self.prediction_cache[cache_key] = result
        self.performance_stats['predictions_made'] += 1
        
        # 更新平均预测时间
        prediction_time = time.perf_counter() - start_time
        self.performance_stats['avg_prediction_time'] = (
            (self.performance_stats['avg_prediction_time'] * (self.performance_stats['predictions_made'] - 1) + prediction_time) /
            self.performance_stats['predictions_made']
        )
        
        # 限制缓存大小
        if len(self.prediction_cache) > 10000:
            # 删除最旧的5000个条目
            keys_to_remove = list(self.prediction_cache.keys())[:5000]
            for key in keys_to_remove:
                del self.prediction_cache[key]
        
        return result
    
    def optimize_strategy_parameters(self, market_data: pd.DataFrame, strategy_name: str,
                                     parameter_space: Dict[str, List[Any]], 
                                     optimization_method: str = 'bayesian',
                                     max_iterations: int = 100) -> Tuple[Dict[str, Any], PredictionResult]:
        """优化策略参数"""
        logger.info(f"开始优化 {strategy_name} 策略参数...")
        
        best_parameters = None
        best_score = float('-inf')
        best_result = None
        
        # 预定义一些有希望的参数组合
        if strategy_name == 'RSI':
            promising_params = [
                {'period': 12, 'oversold': 25, 'overbought': 75},
                {'period': 14, 'oversold': 30, 'overbought': 70},
                {'period': 10, 'oversold': 20, 'overbought': 80},
                {'period': 16, 'oversold': 35, 'overbought': 65},
                {'period': 8, 'oversold': 15, 'overbought': 85}
            ]
        elif strategy_name == 'MACD':
            promising_params = [
                {'fast': 8, 'slow': 21, 'signal': 9},
                {'fast': 12, 'slow': 26, 'signal': 9},
                {'fast': 10, 'slow': 24, 'signal': 8},
                {'fast': 6, 'slow': 19, 'signal': 7}
            ]
        else:
            # 为其他策略生成随机参数
            promising_params = []
            for _ in range(20):
                params = {}
                for param_name, param_values in parameter_space.items():
                    params[param_name] = np.random.choice(param_values)
                promising_params.append(params)
        
        # 评估参数组合
        for params in promising_params:
            try:
                result = self.predict_strategy_performance(market_data, strategy_name, params)
                
                # 使用综合评分
                score = (
                    0.6 * result.predicted_sharpe + 
                    0.3 * result.predicted_return + 
                    0.1 * result.confidence_score
                )
                
                if score > best_score:
                    best_score = score
                    best_parameters = params
                    best_result = result
                    
            except Exception as e:
                logger.warning(f"参数评估失败: {e}")
                continue
        
        logger.info(f"参数优化完成 - 最佳评分: {best_score:.4f}")
        
        return best_parameters, best_result
    
    def generate_optimized_strategy_recommendations(self, market_data: pd.DataFrame,
                                                   num_recommendations: int = 5) -> List[PredictionResult]:
        """生成优化策略推荐"""
        logger.info("生成智能策略推荐...")
        
        strategies = ['RSI', 'MACD', 'BOLLINGER', 'SMA_CROSS', 'STOCHASTIC']
        all_recommendations = []
        
        for strategy in strategies:
            # 优化参数
            if strategy == 'RSI':
                parameter_space = {
                    'period': list(range(5, 31)),
                    'oversold': list(range(15, 36)),
                    'overbought': list(range(65, 86))
                }
            elif strategy == 'MACD':
                parameter_space = {
                    'fast': list(range(5, 16)),
                    'slow': list(range(17, 31)),
                    'signal': list(range(5, 13))
                }
            else:
                # 为其他策略提供基础参数空间
                parameter_space = {
                    'period': list(range(10, 31)),
                    'std_dev': [1.5, 2.0, 2.5, 3.0]
                }
            
            try:
                best_params, result = self.optimize_strategy_parameters(
                    market_data, strategy, parameter_space
                )
                
                if result and result.confidence_score > 0.3:
                    all_recommendations.append(result)
                    
            except Exception as e:
                logger.warning(f"策略 {strategy} 优化失败: {e}")
                continue
        
        # 按综合评分排序
        all_recommendations.sort(
            key=lambda x: (0.5 * x.predicted_sharpe + 0.3 * x.predicted_return + 0.2 * x.confidence_score),
            reverse=True
        )
        
        return all_recommendations[:num_recommendations]
    
    def _generate_prediction_cache_key(self, market_data: pd.DataFrame, strategy_name: str,
                                      parameters: Dict[str, Any], 
                                      historical_performances: Optional[List[StrategyPerformance]]) -> str:
        """生成预测缓存键"""
        # 使用市场数据的哈希和策略信息生成缓存键
        market_hash = hashlib.md5(str(market_data['close'].tail(20).values).encode()).hexdigest()
        param_str = "_".join(f"{k}:{v}" for k, v in sorted(parameters.items()))
        hist_hash = hashlib.md5(str(len(historical_performances) if historical_performances else 0).encode()).hexdigest()
        
        return f"{strategy_name}_{market_hash}_{param_str}_{hist_hash}"
    
    def save_models(self, filepath: str):
        """保存训练好的模型"""
        if not self.is_trained:
            raise ValueError("没有训练好的模型可以保存")
        
        model_data = {
            'models': self.models,
            'scalers': self.scalers,
            'feature_names': self.feature_names,
            'performance_stats': self.performance_stats,
            'model_configs': self.model_configs,
            'training_timestamp': datetime.now().isoformat()
        }
        
        # 压缩保存
        with gzip.open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"模型已保存到 {filepath}")
    
    def load_models(self, filepath: Optional[str] = None):
        """加载训练好的模型"""
        if filepath is None:
            filepath = self.model_path
        
        if filepath is None:
            raise ValueError("没有指定模型文件路径")
        
        try:
            with gzip.open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            
            self.models = model_data['models']
            self.scalers = model_data['scalers']
            self.feature_names = model_data['feature_names']
            self.performance_stats = model_data.get('performance_stats', {})
            
            # 验证模型完整性
            required_keys = ['sharpe_ratio', 'total_return', 'max_drawdown']
            for key in required_keys:
                if key not in self.models:
                    raise ValueError(f"缺少必要的模型: {key}")
            
            self.is_trained = True
            logger.info(f"模型已从 {filepath} 加载")
            
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            self.is_trained = False
    
    def get_model_performance_summary(self) -> Dict[str, Any]:
        """获取模型性能摘要"""
        if not self.is_trained:
            return {"error": "模型尚未训练"}
        
        return {
            "is_trained": self.is_trained,
            "model_count": len(self.models),
            "feature_count": len(self.feature_names),
            "performance_stats": self.performance_stats,
            "model_accuracy": self.performance_stats.get('model_accuracy', {}),
            "cache_stats": {
                "predictions_made": self.performance_stats['predictions_made'],
                "cache_hits": self.performance_stats['cache_hits'],
                "cache_hit_rate": (
                    self.performance_stats['cache_hits'] / max(1, self.performance_stats['predictions_made'])
                ),
                "avg_prediction_time_ms": self.performance_stats['avg_prediction_time'] * 1000
            }
        }

async def main():
    """主函数 - 智能策略选择器测试"""
    print("🤖 AI智能策略选择器测试")
    print("=" * 50)
    
    # 创建测试数据
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', periods=3000, freq='D')
    
    # 生成更真实的价格数据
    trend = np.random.normal(0.0001, 0.001, 3000)
    seasonal = 0.0001 * np.sin(2 * np.pi * np.arange(3000) / 252)
    volatility = np.random.normal(0, 0.02, 3000)
    
    returns = trend + seasonal + volatility
    prices = 100 * np.exp(np.cumsum(returns))
    
    market_data = pd.DataFrame({
        'open': prices,
        'high': prices * (1 + np.random.uniform(0, 0.02, 3000)),
        'low': prices * (1 - np.random.uniform(0, 0.02, 3000)),
        'close': prices,
        'volume': np.random.lognormal(14, 0.5, 3000).astype(int)
    }, index=dates)
    
    # 创建智能策略选择器
    selector = IntelligentStrategySelector()
    
    print("📊 生成历史性能数据...")
    
    # 模拟历史性能数据
    historical_performances = []
    strategies = ['RSI', 'MACD', 'BOLLINGER', 'SMA_CROSS', 'STOCHASTIC']
    
    for strategy in strategies:
        for i in range(100):  # 每个策略100个历史记录
            # 生成随机参数
            if strategy == 'RSI':
                params = {
                    'period': np.random.randint(5, 30),
                    'oversold': np.random.randint(20, 40),
                    'overbought': np.random.randint(60, 80)
                }
            elif strategy == 'MACD':
                params = {
                    'fast': np.random.randint(5, 15),
                    'slow': np.random.randint(20, 30),
                    'signal': np.random.randint(5, 12)
                }
            else:
                params = {'period': np.random.randint(10, 30)}
            
            # 生成性能数据（带一些噪声）
            base_sharpe = np.random.normal(0.8, 0.5)
            base_return = np.random.normal(0.15, 0.1)
            base_drawdown = -abs(np.random.normal(0.1, 0.05))
            base_win_rate = np.random.normal(0.55, 0.15)
            
            # 根据参数调整性能
            param_hash = hash(str(params)) % 1000
            performance_adjustment = param_hash / 1000.0 - 0.5
            
            performance = StrategyPerformance(
                strategy_name=strategy,
                parameters_hash=hash(str(params)),
                sharpe_ratio=max(0.0, base_sharpe + performance_adjustment * 0.3),
                total_return=base_return + performance_adjustment * 0.05,
                max_drawdown=base_drawdown - performance_adjustment * 0.02,
                win_rate=np.clip(0.0, base_win_rate + performance_adjustment * 0.1, 1.0),
                sortino_ratio=max(0.0, base_sharpe * 0.8),
                calmar_ratio=max(0.0, base_return / abs(base_drawdown) + 1e-8),
                information_ratio=np.random.normal(0.3, 0.2),
                execution_time=np.random.uniform(0.01, 0.05),
                market_environment=MarketEnvironment(
                    timestamp=dates[-1],
                    volatility_20d=market_data['close'].pct_change().tail(20).std(),
                    trend_20d=(market_data['close'].iloc[-1] / market_data['close'].iloc[-21] - 1),
                    volume_profile=1.0,
                    price_level=market_data['close'].iloc[-1],
                    market_regime='bull',
                    volatility_regime='normal',
                    liquidity_level=1.0,
                    correlation_avg=0.3
                )
            )
            
            historical_performances.append(performance)
    
    print(f"✅ 历史数据生成完成: {len(historical_performances)} 条记录")
    
    # 训练模型
    print("\n🧠 训练AI预测模型...")
    training_data = selector.create_training_data(historical_performances, {strategy: market_data for strategy in strategies})
    
    if len(training_data) > 0:
        models, metrics = selector.train_models(training_data)
        
        print("📈 训练结果:")
        for target, metric in metrics.items():
            print(f"  {target}: R² = {metric['r2']:.4f}, MAE = {metric['mae']:.4f}")
    else:
        print("⚠️  训练数据不足，跳过模型训练")
    
    # 生成策略推荐
    print("\n🎯 生成智能策略推荐...")
    
    try:
        recommendations = selector.generate_optimized_strategy_recommendations(
            market_data, 
            num_recommendations=5
        )
        
        print(f"✅ 生成了 {len(recommendations)} 个策略推荐:")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"\n🏆 推荐 {i}: {rec.recommended_strategy}")
            print(f"   预测Sharpe: {rec.predicted_sharpe:.3f}")
            print(f"   预测收益: {rec.predicted_return:.2%}")
            print(f"   预测风险: {rec.predicted_risk:.2%}")
            print(f"   置信度: {rec.confidence_score:.3f}")
            print(f"   最优参数: {rec.optimal_parameters}")
        
        # 特征重要性分析
        if recommendations and recommendations[0].feature_importance:
            print(f"\n📊 关键特征重要性 (Top 5):")
            important_features = sorted(
                recommendations[0].feature_importance.items(),
                key=lambda x: x[1], reverse=True
            )[:5]
            
            for feature, importance in important_features:
                print(f"   {feature}: {importance:.4f}")
        
        # 性能摘要
        print(f"\n📊 模型性能摘要:")
        summary = selector.get_model_performance_summary()
        for key, value in summary.items():
            if key != 'model_accuracy':
                print(f"   {key}: {value}")
            
        if 'model_accuracy' in summary:
            print(f"   模型精度:")
            for model, acc in summary['model_accuracy'].items():
                print(f"     {model}: R²={acc['r2']:.4f}")
        
    except Exception as e:
        print(f"❌ 策略推荐失败: {e}")
    
    print(f"\n🎉 AI智能策略选择器测试完成!")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    exit_code = 0 if success else 1
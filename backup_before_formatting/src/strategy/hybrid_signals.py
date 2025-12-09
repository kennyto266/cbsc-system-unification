#!/usr/bin/env python3
"""
混合策略信号框架
结合VectorBT技术指标与CODEX--政府经济数据
"""

import logging
import numpy as np
import pandas as pd
import vectorbt as vbt
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum

from ..data.vectorbt_adapter import VectorBTDataAdapter, VectorBTEconomicIndicators

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """市场状态枚举"""
    BULL = "bull"      # 牛市
    BEAR = "bear"      # 熊市
    SIDEWAYS = "sideways"  # 盘整
    VOLATILE = "volatile"  # 高波动


@dataclass
class SignalConfig:
    """信号配置"""
    price_weight: float = 0.6
    economic_weight: float = 0.4
    adaptive_weights: bool = True
    regime_aware: bool = True
    risk_adjustment: bool = True
    lookback_period: int = 20


@dataclass
class SignalResult:
    """信号结果"""
    signals: pd.DataFrame
    quality_score: float
    regime: MarketRegime
    weights: Dict[str, float]
    performance_metrics: Dict[str, float]


class HybridSignalFramework:
    """混合策略信号框架"""
    
    def __init__(self, config: Optional[SignalConfig] = None):
        self.config = config or SignalConfig()
        self.vbt_adapter = VectorBTDataAdapter()
        self.econ_indicators = VectorBTEconomicIndicators()
        self._cache = {}
        
        # VectorBT技术指标配置
        self.vbt_indicators = {
            'rsi': {'window': [14, 21, 30], 'threshold': [30, 70]},
            'macd': {'fast': [12, 26], 'slow': [26, 50], 'signal': [9, 12]},
            'bollinger': {'window': [20, 50], 'std': [2, 2.5]},
            'adx': {'window': [14, 21], 'threshold': [25, 40]},
            'atr': {'window': [14, 21]},
            'stoch': {'k_window': [14, 21], 'd_window': [3, 5]},
            'cci': {'window': [14, 21], 'threshold': [-100, 100]},
            'williams': {'window': [14, 21]}
        }
    
    async def generate_hybrid_signals(self, 
                                     symbol: str, 
                                     price_data: pd.DataFrame,
                                     economic_data: Dict[str, pd.DataFrame],
                                     start_date: datetime,
                                     end_date: datetime) -> SignalResult:
        """生成混合信号"""
        try:
            logger.info(f"开始为 {symbol} 生成混合信号...")
            
            # 1. 检测市场状态
            market_regime = self._detect_market_regime(price_data)
            
            # 2. 计算动态权重
            signal_weights = self._calculate_signal_weights(market_regime)
            
            # 3. 生成价格技术信号
            price_signals = await self._generate_price_signals(price_data, signal_weights)
            
            # 4. 生成经济信号
            economic_signals = await self._generate_economic_signals(economic_data, signal_weights)
            
            # 5. 信号融合
            hybrid_signals = self._fuse_signals(price_signals, economic_signals, signal_weights)
            
            # 6. 风险调整
            risk_adjusted_signals = self._apply_risk_adjustment(hybrid_signals, price_data)
            
            # 7. 质量评估
            quality_score = self._calculate_signal_quality(risk_adjusted_signals, price_data)
            
            # 8. 性能指标
            performance_metrics = self._calculate_performance_metrics(risk_adjusted_signals, price_data)
            
            return SignalResult(
                signals=risk_adjusted_signals,
                quality_score=quality_score,
                regime=market_regime,
                weights=signal_weights,
                performance_metrics=performance_metrics
            )
            
        except Exception as e:
            logger.error(f"生成混合信号失败 {symbol}: {e}")
            raise
    
    def _detect_market_regime(self, price_data: pd.DataFrame) -> MarketRegime:
        """检测市场状态"""
        if price_data.empty or 'close' not in price_data.columns:
            return MarketRegime.SIDEWAYS
        
        close = price_data['close']
        
        # 计算趋势指标
        sma_20 = close.rolling(20).mean()
        sma_50 = close.rolling(50).mean()
        sma_200 = close.rolling(200).mean()
        
        # 计算波动率
        returns = close.pct_change()
        volatility = returns.rolling(20).std()
        
        # 计算动量
        momentum_20 = close.pct_change(20)
        
        latest_price = close.iloc[-1]
        latest_sma20 = sma_20.iloc[-1]
        latest_sma50 = sma_50.iloc[-1]
        latest_sma200 = sma_200.iloc[-1]
        latest_vol = volatility.iloc[-1]
        latest_momentum = momentum_20.iloc[-1]
        
        # 市场状态判断逻辑
        if latest_vol > volatility.quantile(0.8):
            return MarketRegime.VOLATILE
        
        if (latest_price > latest_sma20 > latest_sma50 > latest_sma200 
            and latest_momentum > 0.05):
            return MarketRegime.BULL
        
        if (latest_price < latest_sma20 < latest_sma50 < latest_sma200 
            and latest_momentum < -0.05):
            return MarketRegime.BEAR
        
        return MarketRegime.SIDEWAYS
    
    def _calculate_signal_weights(self, market_regime: MarketRegime) -> Dict[str, float]:
        """计算信号权重"""
        base_weights = {
            'price': self.config.price_weight,
            'economic': self.config.economic_weight
        }
        
        if not self.config.adaptive_weights:
            return base_weights
        
        # 根据市场状态调整权重
        regime_adjustments = {
            MarketRegime.BULL: {'price': 0.7, 'economic': 0.3},
            MarketRegime.BEAR: {'price': 0.5, 'economic': 0.5},
            MarketRegime.SIDEWAYS: {'price': 0.6, 'economic': 0.4},
            MarketRegime.VOLATILE: {'price': 0.4, 'economic': 0.6}
        }
        
        adjustment = regime_adjustments.get(market_regime, base_weights)
        
        # 平滑过渡
        for key in base_weights:
            base_weights[key] = 0.7 * base_weights[key] + 0.3 * adjustment[key]
        
        return base_weights
    
    async def _generate_price_signals(self, 
                                    price_data: pd.DataFrame, 
                                    weights: Dict[str, float]) -> pd.DataFrame:
        """生成价格技术信号"""
        if price_data.empty:
            return pd.DataFrame()
        
        signals = pd.DataFrame(index=price_data.index)
        
        try:
            # RSI信号
            for window in self.vbt_indicators['rsi']['window']:
                rsi = vbt.RSI.run(price_data['close'], window=window)
                signals[f'rsi_{window}'] = rsi.rsi
            
            # MACD信号
            for fast, slow in zip(self.vbt_indicators['macd']['fast'], 
                                self.vbt_indicators['macd']['slow']):
                macd = vbt.MACD.run(price_data['close'], fast=fast, slow=slow, 
                                  signal=self.vbt_indicators['macd']['signal'][0])
                signals[f'macd_{fast}_{slow}'] = macd.macd
                signals[f'macd_signal_{fast}_{slow}'] = macd.signal
            
            # 布林带信号
            for window in self.vbt_indicators['bollinger']['window']:
                bbands = vbt.BBANDS.run(price_data['close'], window=window, 
                                       std=self.vbt_indicators['bollinger']['std'][0])
                signals[f'bb_upper_{window}'] = bbands.upper
                signals[f'bb_lower_{window}'] = bbands.lower
                signals[f'bb_middle_{window}'] = bbands.middle
            
            # ADX信号
            for window in self.vbt_indicators['adx']['window']:
                adx = vbt.ADX.run(price_data['high'], price_data['low'], 
                                price_data['close'], window=window)
                signals[f'adx_{window}'] = adx.adx
            
            # ATR信号
            for window in self.vbt_indicators['atr']['window']:
                atr = vbt.ATR.run(price_data['high'], price_data['low'], 
                                price_data['close'], window=window)
                signals[f'atr_{window}'] = atr.atr
            
            # Stochastic信号
            for k_window in self.vbt_indicators['stoch']['k_window']:
                stoch = vbt.STOCH.run(price_data['high'], price_data['low'], 
                                    price_data['close'], k_window=k_window, 
                                    d_window=self.vbt_indicators['stoch']['d_window'][0])
                signals[f'stoch_k_{k_window}'] = stoch.k
                signals[f'stoch_d_{k_window}'] = stoch.d
            
            # 综合价格信号
            signals['price_momentum'] = price_data['close'].pct_change()
            signals['price_trend'] = (price_data['close'] / price_data['close'].rolling(20).mean() - 1)
            
            logger.info(f"生成价格信号成功: {len(signals.columns)} 个指标")
            return signals.fillna(method='ffill').fillna(0)
            
        except Exception as e:
            logger.error(f"生成价格信号失败: {e}")
            return pd.DataFrame()
    
    async def _generate_economic_signals(self, 
                                       economic_data: Dict[str, pd.DataFrame], 
                                       weights: Dict[str, float]) -> pd.DataFrame:
        """生成经济信号"""
        if not economic_data:
            return pd.DataFrame()
        
        # 使用VectorBT适配器创建信号
        aligned_data = pd.DataFrame()
        
        try:
            # 对齐所有经济数据的时间索引
            common_index = None
            for name, df in economic_data.items():
                if not df.empty:
                    if common_index is None:
                        common_index = df.index
                    else:
                        common_index = common_index.intersection(df.index)
            
            if common_index is None or len(common_index) == 0:
                return pd.DataFrame()
            
            signals = pd.DataFrame(index=common_index)
            
            # 处理HIBOR数据
            if 'hibor' in economic_data:
                hibor_df = economic_data['hibor']
                if not hibor_df.empty:
                    hibor_aligned = hibor_df.reindex(common_index, method='ffill')
                    
                    # HIBOR技术指标
                    if 'rate' in hibor_aligned.columns:
                        hibor_rates = hibor_aligned['rate'].fillna(method='ffill')
                        
                        # RSI
                        for window in [14, 21]:
                            hibor_rsi = vbt.RSI.run(hibor_rates, window=window)
                            signals[f'hibor_rsi_{window}'] = hibor_rsi.rsi
                        
                        # MACD
                        hibor_macd = vbt.MACD.run(hibor_rates, fast=12, slow=26, signal=9)
                        signals['hibor_macd'] = hibor_macd.macd
                        signals['hibor_macd_signal'] = hibor_macd.signal
                        
                        # 动量
                        signals['hibor_momentum'] = hibor_rates.pct_change()
                        signals['hibor_ma_20'] = hibor_rates.rolling(20).mean()
            
            # 处理GDP数据
            if 'gdp' in economic_data:
                gdp_df = economic_data['gdp']
                if not gdp_df.empty:
                    gdp_aligned = gdp_df.reindex(common_index, method='ffill')
                    
                    if 'gdp_value' in gdp_aligned.columns:
                        gdp_values = gdp_aligned['gdp_value'].fillna(method='ffill')
                        
                        # GDP动量和趋势
                        signals['gdp_momentum'] = gdp_values.pct_change(periods=4)  # 季度同比
                        signals['gdp_trend'] = gdp_values.rolling(4).mean()
                        signals['gdp_acceleration'] = signals['gdp_momentum'].pct_change()
            
            # 处理贸易数据
            if 'trade' in economic_data:
                trade_df = economic_data['trade']
                if not trade_df.empty:
                    trade_aligned = trade_df.reindex(common_index, method='ffill')
                    
                    if 'trade_balance' in trade_aligned.columns:
                        trade_balance = trade_aligned['trade_balance'].fillna(method='ffill')
                        
                        # 贸易平衡技术指标
                        signals['trade_balance_ma'] = trade_balance.rolling(20).mean()
                        signals['trade_balance_volatility'] = trade_balance.rolling(20).std()
                        signals['trade_balance_momentum'] = trade_balance.pct_change()
            
            logger.info(f"生成经济信号成功: {len(signals.columns)} 个指标")
            return signals.fillna(method='ffill').fillna(0)
            
        except Exception as e:
            logger.error(f"生成经济信号失败: {e}")
            return pd.DataFrame()
    
    def _fuse_signals(self, 
                     price_signals: pd.DataFrame, 
                     economic_signals: pd.DataFrame, 
                     weights: Dict[str, float]) -> pd.DataFrame:
        """融合价格和经济信号"""
        if price_signals.empty and economic_signals.empty:
            return pd.DataFrame()
        
        # 统一时间索引
        common_index = price_signals.index
        if not economic_signals.empty:
            common_index = common_index.intersection(economic_signals.index)
        
        if len(common_index) == 0:
            return pd.DataFrame()
        
        hybrid_signals = pd.DataFrame(index=common_index)
        
        # 标准化信号
        def normalize_signals(signals: pd.DataFrame) -> pd.DataFrame:
            """标准化信号到[-1, 1]范围"""
            normalized = pd.DataFrame(index=signals.index)
            
            for col in signals.columns:
                series = signals[col].dropna()
                if len(series) > 1 and series.std() > 0:
                    # Z-score标准化
                    z_score = (series - series.mean()) / series.std()
                    # 限制到[-1, 1]范围
                    z_score = np.clip(z_score, -1, 1)
                    normalized[col] = z_score.reindex(signals.index)
                else:
                    normalized[col] = 0
            
            return normalized.fillna(0)
        
        # 标准化价格信号
        if not price_signals.empty:
            price_normalized = normalize_signals(price_signals.reindex(common_index))
            price_weighted = price_normalized * weights['price']
            hybrid_signals = pd.concat([hybrid_signals, price_weighted], axis=1)
        
        # 标准化经济信号
        if not economic_signals.empty:
            econ_normalized = normalize_signals(economic_signals.reindex(common_index))
            econ_weighted = econ_normalized * weights['economic']
            hybrid_signals = pd.concat([hybrid_signals, econ_weighted], axis=1)
        
        # 生成综合信号
        signal_cols = hybrid_signals.columns.tolist()
        if signal_cols:
            hybrid_signals['hybrid_signal'] = hybrid_signals[signal_cols].mean(axis=1)
            hybrid_signals['signal_strength'] = hybrid_signals[signal_cols].abs().mean(axis=1)
            hybrid_signals['signal_consensus'] = (hybrid_signals[signal_cols] > 0).sum(axis=1) / len(signal_cols)
        
        return hybrid_signals
    
    def _apply_risk_adjustment(self, 
                             signals: pd.DataFrame, 
                             price_data: pd.DataFrame) -> pd.DataFrame:
        """应用风险调整"""
        if signals.empty or price_data.empty:
            return signals
        
        try:
            # 计算波动率
            returns = price_data['close'].pct_change()
            volatility = returns.rolling(20).std()
            
            # 计算最大回撤
            cum_returns = (1 + returns).cumprod()
            rolling_max = cum_returns.rolling(50).max()
            drawdown = (cum_returns - rolling_max) / rolling_max
            
            # 风险调整因子
            risk_factor = 1 - volatility * 2  # 波动率调整
            risk_factor = np.clip(risk_factor, 0.5, 1.5)  # 限制范围
            
            # 回撤调整
            drawdown_adjustment = 1 + drawdown  # 回撤时降低信号强度
            drawdown_adjustment = np.clip(drawdown_adjustment, 0.7, 1.3)
            
            # 应用风险调整
            adjusted_signals = signals.copy()
            signal_cols = [col for col in signals.columns if 'signal' in col]
            
            for col in signal_cols:
                adjusted_signals[col] = signals[col] * risk_factor * drawdown_adjustment
            
            # 添加风险指标
            adjusted_signals['risk_volatility'] = volatility
            adjusted_signals['risk_drawdown'] = drawdown
            adjusted_signals['risk_adjustment_factor'] = risk_factor
            
            return adjusted_signals
            
        except Exception as e:
            logger.error(f"风险调整失败: {e}")
            return signals
    
    def _calculate_signal_quality(self, 
                                signals: pd.DataFrame, 
                                price_data: pd.DataFrame) -> float:
        """计算信号质量评分"""
        if signals.empty or price_data.empty:
            return 0.0
        
        try:
            quality_factors = {}
            
            # 1. 信号稳定性 (低波动率)
            if 'hybrid_signal' in signals.columns:
                signal_vol = signals['hybrid_signal'].rolling(20).std().mean()
                quality_factors['stability'] = max(0, 1 - signal_vol * 10)
            
            # 2. 信号覆盖率
            signal_coverage = signals.notna().mean().mean()
            quality_factors['coverage'] = signal_coverage
            
            # 3. 信号强度分布
            if 'signal_strength' in signals.columns:
                avg_strength = signals['signal_strength'].mean()
                quality_factors['strength'] = min(1, avg_strength * 2)
            
            # 4. 信号一致性
            if 'signal_consensus' in signals.columns:
                avg_consensus = signals['signal_consensus'].mean()
                quality_factors['consensus'] = avg_consensus
            
            # 5. 历史表现 (简化版本)
            returns = price_data['close'].pct_change()
            if 'hybrid_signal' in signals.columns:
                # 信号与收益的相关性
                aligned_signals = signals['hybrid_signal'].reindex(returns.index, method='ffill')
                correlation = aligned_signals.corr(returns.shift(1))  # 信号预测下一期收益
                quality_factors['predictive'] = max(0, abs(correlation))
            
            # 综合评分
            weights = {
                'stability': 0.2,
                'coverage': 0.2,
                'strength': 0.2,
                'consensus': 0.2,
                'predictive': 0.2
            }
            
            total_score = 0
            total_weight = 0
            
            for factor, weight in weights.items():
                if factor in quality_factors:
                    total_score += quality_factors[factor] * weight
                    total_weight += weight
            
            quality_score = total_score / total_weight if total_weight > 0 else 0
            
            return min(100, quality_score * 100)  # 转换为100分制
            
        except Exception as e:
            logger.error(f"计算信号质量失败: {e}")
            return 0.0
    
    def _calculate_performance_metrics(self, 
                                     signals: pd.DataFrame, 
                                     price_data: pd.DataFrame) -> Dict[str, float]:
        """计算性能指标"""
        if signals.empty or price_data.empty:
            return {}
        
        try:
            metrics = {}
            returns = price_data['close'].pct_change()
            
            if 'hybrid_signal' in signals.columns:
                # 基于信号的简单交易策略
                aligned_signals = signals['hybrid_signal'].reindex(returns.index, method='ffill')
                
                # 买入信号：信号>阈值
                buy_threshold = aligned_signals.quantile(0.6)
                sell_threshold = aligned_signals.quantile(0.4)
                
                strategy_returns = pd.Series(0, index=returns.index)
                long_positions = aligned_signals > buy_threshold
                short_positions = aligned_signals < sell_threshold
                
                strategy_returns[long_positions] = returns[long_positions]
                strategy_returns[short_positions] = -returns[short_positions]
                
                # 计算策略性能
                total_return = (1 + strategy_returns).prod() - 1
                sharpe_ratio = strategy_returns.mean() / strategy_returns.std() * np.sqrt(252) if strategy_returns.std() > 0 else 0
                max_drawdown = (strategy_returns.cumsum().cummax() - strategy_returns.cumsum()).max()
                
                metrics['total_return'] = total_return
                metrics['sharpe_ratio'] = sharpe_ratio
                metrics['max_drawdown'] = max_drawdown
                metrics['win_rate'] = (strategy_returns > 0).mean()
                metrics['signal_frequency'] = (aligned_signals.diff().abs() > 0.1).mean()
            
            return metrics
            
        except Exception as e:
            logger.error(f"计算性能指标失败: {e}")
            return {}
    
    def get_signal_interpretation(self, signals: pd.DataFrame, current_index: int = -1) -> Dict[str, Any]:
        """获取信号解读"""
        if signals.empty:
            return {"status": "no_signals", "interpretation": "无可用信号"}
        
        try:
            current_signals = signals.iloc[current_index]
            interpretation = {}
            
            # 信号强度评估
            if 'hybrid_signal' in current_signals:
                signal_value = current_signals['hybrid_signal']
                if signal_value > 0.3:
                    interpretation['action'] = "强烈买入"
                    interpretation['confidence'] = min(0.95, abs(signal_value))
                elif signal_value > 0.1:
                    interpretation['action'] = "买入"
                    interpretation['confidence'] = min(0.8, abs(signal_value))
                elif signal_value > -0.1:
                    interpretation['action'] = "持有"
                    interpretation['confidence'] = 0.5
                elif signal_value > -0.3:
                    interpretation['action'] = "卖出"
                    interpretation['confidence'] = min(0.8, abs(signal_value))
                else:
                    interpretation['action'] = "强烈卖出"
                    interpretation['confidence'] = min(0.95, abs(signal_value))
            
            # 信号质量评估
            if 'signal_strength' in current_signals:
                strength = current_signals['signal_strength']
                interpretation['signal_strength'] = "强" if strength > 0.5 else "弱" if strength > 0.2 else "很弱"
            
            if 'signal_consensus' in current_signals:
                consensus = current_signals['signal_consensus']
                interpretation['signal_consensus'] = f"{consensus*100:.1f}%"
            
            # 风险评估
            if 'risk_volatility' in current_signals:
                vol = current_signals['risk_volatility']
                interpretation['risk_level'] = "高" if vol > 0.03 else "中" if vol > 0.015 else "低"
            
            return interpretation
            
        except Exception as e:
            logger.error(f"信号解读失败: {e}")
            return {"status": "error", "interpretation": f"解读失败: {str(e)}"}
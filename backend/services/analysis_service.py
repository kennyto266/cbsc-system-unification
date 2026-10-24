"""
技术分析服务模块 - 处理技术指标计算和分析
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class TechnicalAnalysisService:
    """技术分析服务类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_technical_indicators(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算技术指标"""
        try:
            if not data or len(data) < 20:
                self.logger.warning("数据不足，无法计算技术指标")
                return {}
            
            # 转换为DataFrame
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            # 计算各种技术指标
            indicators = {}
            
            # 移动平均线
            indicators.update(self._calculate_moving_averages(df))
            
            # RSI
            indicators['rsi'] = self._calculate_rsi(df['close'])
            
            # MACD
            indicators.update(self._calculate_macd(df['close']))
            
            # 布林带
            indicators.update(self._calculate_bollinger_bands(df['close']))
            
            # ATR
            indicators['atr'] = self._calculate_atr(df)
            
            # 成交量指标
            indicators.update(self._calculate_volume_indicators(df))
            
            return indicators
            
        except Exception as e:
            self.logger.error(f"计算技术指标失败: {e}")
            return {}
    
    def _calculate_moving_averages(self, df: pd.DataFrame) -> Dict[str, float]:
        """计算移动平均线"""
        close = df['close']
        
        return {
            'sma_20': float(close.rolling(window=20).mean().iloc[-1]) if len(close) >= 20 else None,
            'sma_50': float(close.rolling(window=50).mean().iloc[-1]) if len(close) >= 50 else None,
            'ema_12': float(close.ewm(span=12).mean().iloc[-1]) if len(close) >= 12 else None,
            'ema_26': float(close.ewm(span=26).mean().iloc[-1]) if len(close) >= 26 else None
        }
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> Optional[float]:
        """计算RSI"""
        try:
            if len(prices) < period + 1:
                return None
            
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None
            
        except Exception as e:
            self.logger.error(f"计算RSI失败: {e}")
            return None
    
    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, Optional[float]]:
        """计算MACD"""
        try:
            if len(prices) < slow:
                return {'macd': None, 'macd_signal': None, 'macd_histogram': None}
            
            ema_fast = prices.ewm(span=fast).mean()
            ema_slow = prices.ewm(span=slow).mean()
            
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal).mean()
            histogram = macd_line - signal_line
            
            return {
                'macd': float(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else None,
                'macd_signal': float(signal_line.iloc[-1]) if not pd.isna(signal_line.iloc[-1]) else None,
                'macd_histogram': float(histogram.iloc[-1]) if not pd.isna(histogram.iloc[-1]) else None
            }
            
        except Exception as e:
            self.logger.error(f"计算MACD失败: {e}")
            return {'macd': None, 'macd_signal': None, 'macd_histogram': None}
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: float = 2) -> Dict[str, Optional[float]]:
        """计算布林带"""
        try:
            if len(prices) < period:
                return {'bollinger_upper': None, 'bollinger_middle': None, 'bollinger_lower': None}
            
            sma = prices.rolling(window=period).mean()
            std = prices.rolling(window=period).std()
            
            return {
                'bollinger_upper': float(sma.iloc[-1] + std_dev * std.iloc[-1]) if not pd.isna(sma.iloc[-1]) else None,
                'bollinger_middle': float(sma.iloc[-1]) if not pd.isna(sma.iloc[-1]) else None,
                'bollinger_lower': float(sma.iloc[-1] - std_dev * std.iloc[-1]) if not pd.isna(sma.iloc[-1]) else None
            }
            
        except Exception as e:
            self.logger.error(f"计算布林带失败: {e}")
            return {'bollinger_upper': None, 'bollinger_middle': None, 'bollinger_lower': None}
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> Optional[float]:
        """计算ATR (平均真实波幅)"""
        try:
            if len(df) < period + 1:
                return None
            
            high = df['high']
            low = df['low']
            close = df['close']
            
            # 计算真实波幅
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            
            true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = true_range.rolling(window=period).mean()
            
            return float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else None
            
        except Exception as e:
            self.logger.error(f"计算ATR失败: {e}")
            return None
    
    def _calculate_volume_indicators(self, df: pd.DataFrame) -> Dict[str, Optional[float]]:
        """计算成交量指标"""
        try:
            volume = df['volume']
            
            if len(volume) < 20:
                return {'volume_sma': None, 'volume_ratio': None}
            
            volume_sma = volume.rolling(window=20).mean()
            volume_ratio = volume.iloc[-1] / volume_sma.iloc[-1] if volume_sma.iloc[-1] > 0 else 1.0
            
            return {
                'volume_sma': float(volume_sma.iloc[-1]) if not pd.isna(volume_sma.iloc[-1]) else None,
                'volume_ratio': float(volume_ratio) if not pd.isna(volume_ratio) else None
            }
            
        except Exception as e:
            self.logger.error(f"计算成交量指标失败: {e}")
            return {'volume_sma': None, 'volume_ratio': None}
    
    def analyze_trend(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析趋势"""
        try:
            if not data or len(data) < 50:
                return {"trend": "insufficient_data", "strength": 0}
            
            df = pd.DataFrame(data)
            close = df['close']
            
            # 计算短期和长期移动平均线
            sma_20 = close.rolling(window=20).mean()
            sma_50 = close.rolling(window=50).mean()
            
            if len(sma_20) < 2 or len(sma_50) < 2:
                return {"trend": "insufficient_data", "strength": 0}
            
            # 判断趋势
            current_price = close.iloc[-1]
            sma_20_current = sma_20.iloc[-1]
            sma_50_current = sma_50.iloc[-1]
            
            if current_price > sma_20_current > sma_50_current:
                trend = "uptrend"
                strength = min(100, ((current_price - sma_50_current) / sma_50_current) * 100)
            elif current_price < sma_20_current < sma_50_current:
                trend = "downtrend"
                strength = min(100, ((sma_50_current - current_price) / sma_50_current) * 100)
            else:
                trend = "sideways"
                strength = 0
            
            return {
                "trend": trend,
                "strength": round(strength, 2),
                "current_price": float(current_price),
                "sma_20": float(sma_20_current),
                "sma_50": float(sma_50_current)
            }
            
        except Exception as e:
            self.logger.error(f"分析趋势失败: {e}")
            return {"trend": "error", "strength": 0}
    
    def generate_trading_signals(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成交易信号"""
        try:
            if not data or len(data) < 50:
                return []
            
            df = pd.DataFrame(data)
            close = df['close']
            
            signals = []
            
            # RSI信号
            rsi = self._calculate_rsi(close)
            if rsi is not None:
                if rsi < 30:
                    signals.append({
                        "type": "buy",
                        "indicator": "RSI",
                        "value": rsi,
                        "strength": "strong",
                        "description": "RSI超卖，建议买入"
                    })
                elif rsi > 70:
                    signals.append({
                        "type": "sell",
                        "indicator": "RSI",
                        "value": rsi,
                        "strength": "strong",
                        "description": "RSI超买，建议卖出"
                    })
            
            # 移动平均线交叉信号
            sma_20 = close.rolling(window=20).mean()
            sma_50 = close.rolling(window=50).mean()
            
            if len(sma_20) >= 2 and len(sma_50) >= 2:
                if sma_20.iloc[-1] > sma_50.iloc[-1] and sma_20.iloc[-2] <= sma_50.iloc[-2]:
                    signals.append({
                        "type": "buy",
                        "indicator": "MA_CROSS",
                        "value": None,
                        "strength": "medium",
                        "description": "短期均线上穿长期均线，买入信号"
                    })
                elif sma_20.iloc[-1] < sma_50.iloc[-1] and sma_20.iloc[-2] >= sma_50.iloc[-2]:
                    signals.append({
                        "type": "sell",
                        "indicator": "MA_CROSS",
                        "value": None,
                        "strength": "medium",
                        "description": "短期均线下穿长期均线，卖出信号"
                    })
            
            return signals
            
        except Exception as e:
            self.logger.error(f"生成交易信号失败: {e}")
            return []
    
    def predict_volatility(self, data: List[Dict[str, Any]], days: int = 5) -> Dict[str, Any]:
        """预测波动率"""
        try:
            if not data or len(data) < 20:
                return {"volatility": None, "confidence": 0}
            
            df = pd.DataFrame(data)
            close = df['close']
            
            # 计算历史波动率
            returns = close.pct_change().dropna()
            historical_vol = returns.std() * np.sqrt(252)  # 年化波动率
            
            # 简单的波动率预测（基于历史数据）
            recent_vol = returns.tail(10).std() * np.sqrt(252)
            
            # 预测未来波动率
            predicted_vol = (historical_vol + recent_vol) / 2
            
            return {
                "volatility": round(predicted_vol * 100, 2),
                "confidence": 70,  # 简单的置信度
                "historical_volatility": round(historical_vol * 100, 2),
                "recent_volatility": round(recent_vol * 100, 2)
            }
            
        except Exception as e:
            self.logger.error(f"预测波动率失败: {e}")
            return {"volatility": None, "confidence": 0}

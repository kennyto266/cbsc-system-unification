#!/usr/bin/env python3
"""
增强技术指标库
VectorBT内置指标封装 + 自定义指标 + 经济数据技术指标
"""

import logging
import numpy as np
import pandas as pd
import vectorbt as vbt
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class IndicatorConfig:
    """技术指标配置"""
    rsi_windows: List[int] = None
    macd_params: List[Tuple[int, int, int]] = None
    bollinger_windows: List[int] = None
    adx_windows: List[int] = None
    cci_windows: List[int] = None
    stoch_params: List[Tuple[int, int]] = None
    
    def __post_init__(self):
        if self.rsi_windows is None:
            self.rsi_windows = [14, 21, 30]
        if self.macd_params is None:
            self.macd_params = [(12, 26, 9), (5, 35, 5)]
        if self.bollinger_windows is None:
            self.bollinger_windows = [20, 50]
        if self.adx_windows is None:
            self.adx_windows = [14, 21]
        if self.cci_windows is None:
            self.cci_windows = [14, 21]
        if self.stoch_params is None:
            self.stoch_params = [(14, 3), (21, 5)]


class VectorBTTechnicalIndicators:
    """VectorBT技术指标封装"""
    
    def __init__(self, config: Optional[IndicatorConfig] = None):
        self.config = config or IndicatorConfig()
        
    def calculate_rsi_indicators(self, price_data: pd.DataFrame) -> pd.DataFrame:
        """计算RSI指标系列"""
        if price_data.empty or 'close' not in price_data.columns:
            return pd.DataFrame()
        
        indicators = pd.DataFrame(index=price_data.index)
        
        try:
            for window in self.config.rsi_windows:
                # RSI指标
                rsi = vbt.RSI.run(price_data['close'], window=window)
                indicators[f'rsi_{window}'] = rsi.rsi
                
                # RSI动量
                indicators[f'rsi_momentum_{window}'] = rsi.rsi.pct_change()
                
                # RSI信号
                indicators[f'rsi_oversold_{window}'] = (rsi.rsi < 30).astype(int)
                indicators[f'rsi_overbought_{window}'] = (rsi.rsi > 70).astype(int)
                
                # RSI背离检测
                price_highs = price_data['close'].rolling(window).max()
                price_lows = price_data['close'].rolling(window).min()
                rsi_highs = rsi.rsi.rolling(window).max()
                rsi_lows = rsi.rsi.rolling(window).min()
                
                # 看跌背离：价格创新高但RSI没有
                bearish_divergence = (price_data['close'] == price_highs) & (rsi.rsi < rsi_highs)
                # 看涨背离：价格创新低但RSI没有
                bullish_divergence = (price_data['close'] == price_lows) & (rsi.rsi > rsi_lows)
                
                indicators[f'rsi_bearish_div_{window}'] = bearish_divergence.astype(int)
                indicators[f'rsi_bullish_div_{window}'] = bullish_divergence.astype(int)
            
            logger.info(f"计算RSI指标完成: {len(indicators.columns)} 个指标")
            return indicators.fillna(method='ffill').fillna(0)
            
        except Exception as e:
            logger.error(f"计算RSI指标失败: {e}")
            return pd.DataFrame()
    
    def calculate_macd_indicators(self, price_data: pd.DataFrame) -> pd.DataFrame:
        """计算MACD指标系列"""
        if price_data.empty or 'close' not in price_data.columns:
            return pd.DataFrame()
        
        indicators = pd.DataFrame(index=price_data.index)
        
        try:
            for fast, slow, signal in self.config.macd_params:
                # MACD指标
                macd = vbt.MACD.run(price_data['close'], fast=fast, slow=slow, signal=signal)
                
                indicators[f'macd_{fast}_{slow}'] = macd.macd
                indicators[f'macd_signal_{fast}_{slow}'] = macd.signal
                indicators[f'macd_histogram_{fast}_{slow}'] = macd.histogram
                
                # MACD动量
                indicators[f'macd_momentum_{fast}_{slow}'] = macd.macd.pct_change()
                
                # MACD信号
                macd_bullish = (macd.macd > macd.signal) & (macd.histogram > 0)
                macd_bearish = (macd.macd < macd.signal) & (macd.histogram < 0)
                
                indicators[f'macd_bullish_{fast}_{slow}'] = macd_bullish.astype(int)
                indicators[f'macd_bearish_{fast}_{slow}'] = macd_bearish.astype(int)
                
                # MACD背离检测
                price_highs = price_data['close'].rolling(20).max()
                price_lows = price_data['close'].rolling(20).min()
                macd_highs = macd.macd.rolling(20).max()
                macd_lows = macd.macd.rolling(20).min()
                
                bearish_divergence = (price_data['close'] == price_highs) & (macd.macd < macd_highs)
                bullish_divergence = (price_data['close'] == price_lows) & (macd.macd > macd_lows)
                
                indicators[f'macd_div_bearish_{fast}_{slow}'] = bearish_divergence.astype(int)
                indicators[f'macd_div_bullish_{fast}_{slow}'] = bullish_divergence.astype(int)
            
            logger.info(f"计算MACD指标完成: {len(indicators.columns)} 个指标")
            return indicators.fillna(method='ffill').fillna(0)
            
        except Exception as e:
            logger.error(f"计算MACD指标失败: {e}")
            return pd.DataFrame()
    
    def calculate_bollinger_indicators(self, price_data: pd.DataFrame) -> pd.DataFrame:
        """计算布林带指标系列"""
        if price_data.empty or 'close' not in price_data.columns:
            return pd.DataFrame()
        
        indicators = pd.DataFrame(index=price_data.index)
        
        try:
            for window in self.config.bollinger_windows:
                for std in [2.0, 2.5]:
                    # 布林带指标
                    bbands = vbt.BBANDS.run(price_data['close'], window=window, std=std)
                    
                    indicators[f'bb_upper_{window}_{std}'] = bbands.upper
                    indicators[f'bb_middle_{window}_{std}'] = bbands.middle
                    indicators[f'bb_lower_{window}_{std}'] = bbands.lower
                    
                    # 布林带位置
                    bb_position = (price_data['close'] - bbands.lower) / (bbands.upper - bbands.lower)
                    indicators[f'bb_position_{window}_{std}'] = bb_position
                    
                    # 布林带宽度
                    bb_width = (bbands.upper - bbands.lower) / bbands.middle
                    indicators[f'bb_width_{window}_{std}'] = bb_width
                    
                    # 布林带信号
                    bb_squeeze = bb_width < bb_width.rolling(50).mean() * 0.8  # 收缩
                    bb_breakout_up = price_data['close'] > bbands.upper
                    bb_breakout_down = price_data['close'] < bbands.lower
                    
                    indicators[f'bb_squeeze_{window}_{std}'] = bb_squeeze.astype(int)
                    indicators[f'bb_breakout_up_{window}_{std}'] = bb_breakout_up.astype(int)
                    indicators[f'bb_breakout_down_{window}_{std}'] = bb_breakout_down.astype(int)
            
            logger.info(f"计算布林带指标完成: {len(indicators.columns)} 个指标")
            return indicators.fillna(method='ffill').fillna(0)
            
        except Exception as e:
            logger.error(f"计算布林带指标失败: {e}")
            return pd.DataFrame()
    
    def calculate_adx_indicators(self, price_data: pd.DataFrame) -> pd.DataFrame:
        """计算ADX指标系列"""
        if price_data.empty or all(col not in price_data.columns for col in ['high', 'low', 'close']):
            return pd.DataFrame()
        
        indicators = pd.DataFrame(index=price_data.index)
        
        try:
            for window in self.config.adx_windows:
                # ADX指标
                adx = vbt.ADX.run(price_data['high'], price_data['low'], price_data['close'], window=window)
                
                indicators[f'adx_{window}'] = adx.adx
                indicators[f'adx_plus_{window}'] = adx.adx_pos
                indicators[f'adx_minus_{window}'] = adx.adx_neg
                
                # ADX趋势强度
                strong_trend = adx.adx > 25
                weak_trend = (adx.adx >= 20) & (adx.adx <= 25)
                no_trend = adx.adx < 20
                
                indicators[f'adx_strong_trend_{window}'] = strong_trend.astype(int)
                indicators[f'adx_weak_trend_{window}'] = weak_trend.astype(int)
                indicators[f'adx_no_trend_{window}'] = no_trend.astype(int)
                
                # ADX方向
                bullish_trend = (adx.adx_pos > adx.adx_neg) & strong_trend
                bearish_trend = (adx.adx_neg > adx.adx_pos) & strong_trend
                
                indicators[f'adx_bullish_{window}'] = bullish_trend.astype(int)
                indicators[f'adx_bearish_{window}'] = bearish_trend.astype(int)
            
            logger.info(f"计算ADX指标完成: {len(indicators.columns)} 个指标")
            return indicators.fillna(method='ffill').fillna(0)
            
        except Exception as e:
            logger.error(f"计算ADX指标失败: {e}")
            return pd.DataFrame()
    
    def calculate_cci_indicators(self, price_data: pd.DataFrame) -> pd.DataFrame:
        """计算CCI指标系列"""
        if price_data.empty or all(col not in price_data.columns for col in ['high', 'low', 'close']):
            return pd.DataFrame()
        
        indicators = pd.DataFrame(index=price_data.index)
        
        try:
            for window in self.config.cci_windows:
                # CCI指标
                cci = vbt.CCI.run(price_data['high'], price_data['low'], price_data['close'], window=window)
                indicators[f'cci_{window}'] = cci.cci
                
                # CCI信号
                cci_overbought = cci.cci > 100
                cci_oversold = cci.cci < -100
                
                indicators[f'cci_overbought_{window}'] = cci_overbought.astype(int)
                indicators[f'cci_oversold_{window}'] = cci_oversold.astype(int)
                
                # CCI背离检测
                price_highs = price_data['high'].rolling(window).max()
                price_lows = price_data['low'].rolling(window).min()
                cci_highs = cci.cci.rolling(window).max()
                cci_lows = cci.cci.rolling(window).min()
                
                bearish_divergence = (price_data['high'] == price_highs) & (cci.cci < cci_highs)
                bullish_divergence = (price_data['low'] == price_lows) & (cci.cci > cci_lows)
                
                indicators[f'cci_bearish_div_{window}'] = bearish_divergence.astype(int)
                indicators[f'cci_bullish_div_{window}'] = bullish_divergence.astype(int)
            
            logger.info(f"计算CCI指标完成: {len(indicators.columns)} 个指标")
            return indicators.fillna(method='ffill').fillna(0)
            
        except Exception as e:
            logger.error(f"计算CCI指标失败: {e}")
            return pd.DataFrame()
    
    def calculate_stochastic_indicators(self, price_data: pd.DataFrame) -> pd.DataFrame:
        """计算随机指标系列"""
        if price_data.empty or all(col not in price_data.columns for col in ['high', 'low', 'close']):
            return pd.DataFrame()
        
        indicators = pd.DataFrame(index=price_data.index)
        
        try:
            for k_window, d_window in self.config.stoch_params:
                # 随机指标
                stoch = vbt.STOCH.run(price_data['high'], price_data['low'], price_data['close'], 
                                     k_window=k_window, d_window=d_window)
                
                indicators[f'stoch_k_{k_window}_{d_window}'] = stoch.k
                indicators[f'stoch_d_{k_window}_{d_window}'] = stoch.d
                
                # 随机指标信号
                stoch_overbought = stoch.k > 80
                stoch_oversold = stoch.k < 20
                
                indicators[f'stoch_overbought_{k_window}_{d_window}'] = stoch_overbought.astype(int)
                indicators[f'stoch_oversold_{k_window}_{d_window}'] = stoch_oversold.astype(int)
                
                # 随机指标交叉
                golden_cross = (stoch.k > stoch.d) & (stoch.k.shift(1) <= stoch.d.shift(1))
                death_cross = (stoch.k < stoch.d) & (stoch.k.shift(1) >= stoch.d.shift(1))
                
                indicators[f'stoch_golden_cross_{k_window}_{d_window}'] = golden_cross.astype(int)
                indicators[f'stoch_death_cross_{k_window}_{d_window}'] = death_cross.astype(int)
            
            logger.info(f"计算随机指标完成: {len(indicators.columns)} 个指标")
            return indicators.fillna(method='ffill').fillna(0)
            
        except Exception as e:
            logger.error(f"计算随机指标失败: {e}")
            return pd.DataFrame()
    
    def calculate_atr_indicators(self, price_data: pd.DataFrame) -> pd.DataFrame:
        """计算ATR指标系列"""
        if price_data.empty or all(col not in price_data.columns for col in ['high', 'low', 'close']):
            return pd.DataFrame()
        
        indicators = pd.DataFrame(index=price_data.index)
        
        try:
            for window in [14, 21]:
                # ATR指标
                atr = vbt.ATR.run(price_data['high'], price_data['low'], price_data['close'], window=window)
                indicators[f'atr_{window}'] = atr.atr
                
                # ATR百分比
                atr_pct = atr.atr / price_data['close'] * 100
                indicators[f'atr_pct_{window}'] = atr_pct
                
                # ATR信号
                high_volatility = atr_pct > atr_pct.rolling(50).mean() * 1.5
                low_volatility = atr_pct < atr_pct.rolling(50).mean() * 0.5
                
                indicators[f'atr_high_vol_{window}'] = high_volatility.astype(int)
                indicators[f'atr_low_vol_{window}'] = low_volatility.astype(int)
                
                # ATR动态止损
                atr_stop_long = price_data['close'] - 2 * atr.atr
                atr_stop_short = price_data['close'] + 2 * atr.atr
                
                indicators[f'atr_stop_long_{window}'] = atr_stop_long
                indicators[f'atr_stop_short_{window}'] = atr_stop_short
            
            logger.info(f"计算ATR指标完成: {len(indicators.columns)} 个指标")
            return indicators.fillna(method='ffill').fillna(0)
            
        except Exception as e:
            logger.error(f"计算ATR指标失败: {e}")
            return pd.DataFrame()
    
    def calculate_all_indicators(self, price_data: pd.DataFrame) -> pd.DataFrame:
        """计算所有技术指标"""
        logger.info("开始计算所有VectorBT技术指标...")
        
        all_indicators = pd.DataFrame(index=price_data.index)
        
        # 计算各类指标
        rsi_indicators = self.calculate_rsi_indicators(price_data)
        macd_indicators = self.calculate_macd_indicators(price_data)
        bollinger_indicators = self.calculate_bollinger_indicators(price_data)
        adx_indicators = self.calculate_adx_indicators(price_data)
        cci_indicators = self.calculate_cci_indicators(price_data)
        stoch_indicators = self.calculate_stochastic_indicators(price_data)
        atr_indicators = self.calculate_atr_indicators(price_data)
        
        # 合并指标
        indicator_dfs = [
            rsi_indicators, macd_indicators, bollinger_indicators,
            adx_indicators, cci_indicators, stoch_indicators, atr_indicators
        ]
        
        for df in indicator_dfs:
            if not df.empty:
                all_indicators = pd.concat([all_indicators, df], axis=1)
        
        # 添加综合指标
        if not all_indicators.empty:
            all_indicators = self._calculate_composite_indicators(all_indicators)
        
        logger.info(f"VectorBT技术指标计算完成，总计: {len(all_indicators.columns)} 个指标")
        return all_indicators.fillna(method='ffill').fillna(0)
    
    def _calculate_composite_indicators(self, indicators: pd.DataFrame) -> pd.DataFrame:
        """计算综合指标"""
        try:
            # 动量指标
            momentum_cols = [col for col in indicators.columns if 'momentum' in col]
            if momentum_cols:
                indicators['composite_momentum'] = indicators[momentum_cols].mean(axis=1)
            
            # 趋势指标
            trend_cols = [col for col in indicators.columns if any(x in col for x in ['adx', 'macd'])]
            if trend_cols:
                # 只选择数值列
                trend_numeric_cols = [col for col in trend_cols if indicators[col].dtype in ['float64', 'int64']]
                if trend_numeric_cols:
                    indicators['composite_trend'] = indicators[trend_numeric_cols].mean(axis=1)
            
            # 超买超卖指标
            overbought_cols = [col for col in indicators.columns if 'overbought' in col]
            oversold_cols = [col for col in indicators.columns if 'oversold' in col]
            
            if overbought_cols:
                indicators['composite_overbought'] = indicators[overbought_cols].mean(axis=1)
            if oversold_cols:
                indicators['composite_oversold'] = indicators[oversold_cols].mean(axis=1)
            
            # 背离指标
            divergence_cols = [col for col in indicators.columns if 'div' in col]
            if divergence_cols:
                indicators['composite_divergence'] = indicators[divergence_cols].mean(axis=1)
            
            # 波动率指标
            volatility_cols = [col for col in indicators.columns if 'vol' in col or 'atr' in col]
            if volatility_cols:
                # 只选择数值列
                vol_numeric_cols = [col for col in volatility_cols if indicators[col].dtype in ['float64', 'int64']]
                if vol_numeric_cols:
                    indicators['composite_volatility'] = indicators[vol_numeric_cols].mean(axis=1)
            
            return indicators
            
        except Exception as e:
            logger.error(f"计算综合指标失败: {e}")
            return indicators


class EconomicTechnicalIndicators:
    """经济数据技术指标"""
    
    @staticmethod
    def hibor_rsi(hibor_data: pd.Series, period: int = 14) -> pd.Series:
        """HIBOR相对强弱指标"""
        if hibor_data.empty:
            return pd.Series()
        
        try:
            # 使用VectorBT的RSI计算
            rsi = vbt.RSI.run(hibor_data, window=period)
            return rsi.rsi.fillna(method='ffill').fillna(50)
        except Exception as e:
            logger.error(f"HIBOR RSI计算失败: {e}")
            return pd.Series(index=hibor_data.index, dtype=float)
    
    @staticmethod
    def hibor_macd(hibor_data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """HIBOR MACD指标"""
        if hibor_data.empty:
            return pd.DataFrame()
        
        try:
            macd = vbt.MACD.run(hibor_data, fast=fast, slow=slow, signal=signal)
            result = pd.DataFrame({
                'hibor_macd': macd.macd,
                'hibor_macd_signal': macd.signal,
                'hibor_macd_histogram': macd.histogram
            }, index=hibor_data.index)
            
            return result.fillna(method='ffill').fillna(0)
        except Exception as e:
            logger.error(f"HIBOR MACD计算失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def hibor_bollinger(hibor_data: pd.Series, window: int = 20, std: float = 2.0) -> pd.DataFrame:
        """HIBOR布林带指标"""
        if hibor_data.empty:
            return pd.DataFrame()
        
        try:
            bbands = vbt.BBANDS.run(hibor_data, window=window, std=std)
            result = pd.DataFrame({
                'hibor_bb_upper': bbands.upper,
                'hibor_bb_middle': bbands.middle,
                'hibor_bb_lower': bbands.lower,
                'hibor_bb_position': (hibor_data - bbands.lower) / (bbands.upper - bbands.lower)
            }, index=hibor_data.index)
            
            return result.fillna(method='ffill').fillna(0)
        except Exception as e:
            logger.error(f"HIBOR布林带计算失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def gdp_momentum(gdp_data: pd.Series, periods: int = 4) -> pd.Series:
        """GDP动量指标"""
        if gdp_data.empty:
            return pd.Series()
        
        try:
            # 同比增长率
            momentum = gdp_data.pct_change(periods=periods)
            return momentum.fillna(method='ffill').fillna(0)
        except Exception as e:
            logger.error(f"GDP动量计算失败: {e}")
            return pd.Series(index=gdp_data.index, dtype=float)
    
    @staticmethod
    def gdp_trend_strength(gdp_data: pd.Series, short_window: int = 4, long_window: int = 12) -> pd.Series:
        """GDP趋势强度指标"""
        if gdp_data.empty:
            return pd.Series()
        
        try:
            short_ma = gdp_data.rolling(short_window).mean()
            long_ma = gdp_data.rolling(long_window).mean()
            
            # 趋势强度 = (短期均线 - 长期均线) / 长期均线
            trend_strength = (short_ma - long_ma) / long_ma
            return trend_strength.fillna(method='ffill').fillna(0)
        except Exception as e:
            logger.error(f"GDP趋势强度计算失败: {e}")
            return pd.Series(index=gdp_data.index, dtype=float)
    
    @staticmethod
    def trade_flow_index(export_data: pd.Series, import_data: pd.Series, window: int = 20) -> pd.Series:
        """贸易流量指标"""
        if export_data.empty or import_data.empty:
            return pd.Series()
        
        try:
            # 贸易余额 = 出口 - 进口
            trade_balance = export_data - import_data
            
            # 贸易流量指数 = 贸易余额 / 进口额
            trade_index = trade_balance / import_data
            
            # 平滑处理
            smoothed_index = trade_index.rolling(window).mean()
            return smoothed_index.fillna(method='ffill').fillna(0)
        except Exception as e:
            logger.error(f"贸易流量指标计算失败: {e}")
            return pd.Series(index=export_data.index, dtype=float)
    
    @staticmethod
    def composite_economic_signal(economic_data: Dict[str, pd.Series], 
                                 weights: Optional[Dict[str, float]] = None) -> pd.Series:
        """复合经济信号"""
        if not economic_data:
            return pd.Series()
        
        if weights is None:
            weights = {
                'hibor': 0.3,
                'gdp': 0.3,
                'trade': 0.2,
                'cpi': 0.1,
                'unemployment': 0.1
            }
        
        try:
            # 找到共同的索引
            common_index = None
            for name, series in economic_data.items():
                if not series.empty:
                    if common_index is None:
                        common_index = series.index
                    else:
                        common_index = common_index.intersection(series.index)
            
            if common_index is None or len(common_index) == 0:
                return pd.Series()
            
            composite_signal = pd.Series(0, index=common_index)
            
            for name, series in economic_data.items():
                if name in weights and not series.empty:
                    # 标准化数据到[-1, 1]范围
                    aligned_series = series.reindex(common_index, method='ffill')
                    if aligned_series.std() > 0:
                        normalized_data = (aligned_series - aligned_series.mean()) / aligned_series.std()
                        normalized_data = np.clip(normalized_data, -1, 1)
                        composite_signal += normalized_data * weights[name]
            
            return composite_signal.fillna(method='ffill').fillna(0)
            
        except Exception as e:
            logger.error(f"复合经济信号计算失败: {e}")
            return pd.Series()


class CustomIndicators:
    """自定义技术指标"""
    
    @staticmethod
    def vwap(price_data: pd.DataFrame) -> pd.Series:
        """成交量加权平均价格 (VWAP)"""
        if price_data.empty or all(col not in price_data.columns for col in ['high', 'low', 'close', 'volume']):
            return pd.Series()
        
        try:
            # VWAP计算
            typical_price = (price_data['high'] + price_data['low'] + price_data['close']) / 3
            vwap = (typical_price * price_data['volume']).cumsum() / price_data['volume'].cumsum()
            return vwap.fillna(method='ffill')
        except Exception as e:
            logger.error(f"VWAP计算失败: {e}")
            return pd.Series()
    
    @staticmethod
    def money_flow_index(price_data: pd.DataFrame, window: int = 14) -> pd.Series:
        """资金流量指标 (MFI)"""
        if price_data.empty or all(col not in price_data.columns for col in ['high', 'low', 'close', 'volume']):
            return pd.Series()
        
        try:
            # 典型价格
            typical_price = (price_data['high'] + price_data['low'] + price_data['close']) / 3
            raw_money_flow = typical_price * price_data['volume']
            
            # 正负资金流
            positive_mf = pd.Series(0, index=price_data.index)
            negative_mf = pd.Series(0, index=price_data.index)
            
            # 前一日典型价格
            prev_tp = typical_price.shift(1)
            
            # 计算正负资金流
            positive_mask = typical_price > prev_tp
            negative_mask = typical_price < prev_tp
            
            positive_mf[positive_mask] = raw_money_flow[positive_mask]
            negative_mf[negative_mask] = raw_money_flow[negative_mask]
            
            # 资金流量比率
            positive_mf_sum = positive_mf.rolling(window).sum()
            negative_mf_sum = negative_mf.rolling(window).sum()
            
            money_flow_ratio = positive_mf_sum / negative_mf_sum
            
            # MFI计算
            mfi = 100 - (100 / (1 + money_flow_ratio))
            
            return mfi.fillna(method='ffill').fillna(50)
        except Exception as e:
            logger.error(f"MFI计算失败: {e}")
            return pd.Series()
    
    @staticmethod
    def williams_r(price_data: pd.DataFrame, window: int = 14) -> pd.Series:
        """威廉指标 %R"""
        if price_data.empty or all(col not in price_data.columns for col in ['high', 'low', 'close']):
            return pd.Series()
        
        try:
            # 威廉指标计算
            highest_high = price_data['high'].rolling(window).max()
            lowest_low = price_data['low'].rolling(window).min()
            
            williams_r = -100 * (highest_high - price_data['close']) / (highest_high - lowest_low)
            
            return williams_r.fillna(method='ffill').fillna(-50)
        except Exception as e:
            logger.error(f"威廉%R计算失败: {e}")
            return pd.Series()


# 便利函数
def calculate_all_vectorbt_indicators(price_data: pd.DataFrame, 
                                    config: Optional[IndicatorConfig] = None) -> pd.DataFrame:
    """计算所有VectorBT技术指标的便利函数"""
    indicator_engine = VectorBTTechnicalIndicators(config)
    return indicator_engine.calculate_all_indicators(price_data)


def calculate_economic_indicators(economic_data: Dict[str, pd.Series]) -> pd.DataFrame:
    """计算所有经济技术指标的便利函数"""
    econ_indicators = EconomicTechnicalIndicators()
    all_econ_indicators = pd.DataFrame()
    
    try:
        # HIBOR指标
        if 'hibor' in economic_data:
            hibor_data = economic_data['hibor']
            if not hibor_data.empty:
                # RSI
                hibor_rsi = econ_indicators.hibor_rsi(hibor_data)
                if not hibor_rsi.empty:
                    all_econ_indicators['hibor_rsi'] = hibor_rsi
                
                # MACD
                hibor_macd = econ_indicators.hibor_macd(hibor_data)
                if not hibor_macd.empty:
                    all_econ_indicators = pd.concat([all_econ_indicators, hibor_macd], axis=1)
                
                # 布林带
                hibor_bb = econ_indicators.hibor_bollinger(hibor_data)
                if not hibor_bb.empty:
                    all_econ_indicators = pd.concat([all_econ_indicators, hibor_bb], axis=1)
        
        # GDP指标
        if 'gdp' in economic_data:
            gdp_data = economic_data['gdp']
            if not gdp_data.empty:
                gdp_momentum = econ_indicators.gdp_momentum(gdp_data)
                gdp_trend = econ_indicators.gdp_trend_strength(gdp_data)
                
                all_econ_indicators['gdp_momentum'] = gdp_momentum
                all_econ_indicators['gdp_trend_strength'] = gdp_trend
        
        # 贸易指标
        if 'export' in economic_data and 'import' in economic_data:
            export_data = economic_data['export']
            import_data = economic_data['import']
            
            if not export_data.empty and not import_data.empty:
                trade_index = econ_indicators.trade_flow_index(export_data, import_data)
                all_econ_indicators['trade_flow_index'] = trade_index
        
        # 复合信号
        composite_signal = econ_indicators.composite_economic_signal(economic_data)
        if not composite_signal.empty:
            all_econ_indicators['composite_economic_signal'] = composite_signal
        
        logger.info(f"经济技术指标计算完成: {len(all_econ_indicators.columns)} 个指标")
        return all_econ_indicators.fillna(method='ffill').fillna(0)
        
    except Exception as e:
        logger.error(f"计算经济技术指标失败: {e}")
        return pd.DataFrame()
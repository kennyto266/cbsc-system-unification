#!/usr/bin/env python3
"""
VectorBT Data Adapter
将CODEX--政府数据转换为VectorBT兼容格式
"""

import logging
import numpy as np
import pandas as pd
import vectorbt as vbt
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

from .real_government_data_collector import RealGovernmentDataCollector

logger = logging.getLogger(__name__)


class VectorBTDataAdapter:
    """VectorBT数据适配器"""

    def __init__(self):
        self.gov_collector = RealGovernmentDataCollector()
        self._cache = {}

    def convert_hibor_data(self, hibor_data: List[Dict]) -> pd.DataFrame:
        """转换HIBOR数据为VectorBT格式"""
        if not hibor_data:
            return pd.DataFrame()

        df = pd.DataFrame(hibor_data)

        # 确保时间戳
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)

        # VectorBT需要的OHLCV格式
        if 'rate' in df.columns:
            df['close'] = df['rate']
            df['open'] = df['close'].shift(1).fillna(df['close'])
            df['high'] = df['close'] * 1.001  # 假设小幅波动
            df['low'] = df['close'] * 0.999
            df['volume'] = 1000  # 默认成交量

        return df.sort_index()

    def convert_gdp_data(self, gdp_data: List[Dict]) -> pd.DataFrame:
        """转换GDP数据为VectorBT格式"""
        if not gdp_data:
            return pd.DataFrame()

        df = pd.DataFrame(gdp_data)

        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)

        if 'value' in df.columns:
            df['gdp_value'] = df['value']
            df['gdp_growth'] = df['gdp_value'].pct_change()

        return df.sort_index()

    def convert_trade_data(self, trade_data: List[Dict]) -> pd.DataFrame:
        """转换贸易数据为VectorBT格式"""
        if not trade_data:
            return pd.DataFrame()

        df = pd.DataFrame(trade_data)

        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)

        # 计算贸易平衡
        if 'export_value' in df.columns and 'import_value' in df.columns:
            df['trade_balance'] = df['export_value'] - df['import_value']
            df['trade_growth'] = df['export_value'].pct_change()

        return df.sort_index()

    def align_price_economic_data(self, price_data: pd.DataFrame,
                                   economic_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """对齐价格数据和经济数据"""
        if price_data.empty:
            return price_data

        aligned_data = price_data.copy()

        # 对齐每个经济数据源
        for source_name, econ_df in economic_data.items():
            if econ_df.empty:
                continue

            # 重采样到价格数据的频率（假设每日）
            econ_resampled = econ_df.reindex(price_data.index, method='ffill')

            # 添加到价格数据中
            for col in econ_df.columns:
                aligned_data[f'{source_name}_{col}'] = econ_resampled[col]

        return aligned_data

    def create_vectorbt_signals(self, price_data: pd.DataFrame,
                                economic_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """创建VectorBT兼容的信号数据"""
        if price_data.empty:
            return pd.DataFrame()

        signals = pd.DataFrame(index=price_data.index)

        # 价格信号
        signals['sma_20'] = price_data['close'].rolling(20).mean()
        signals['sma_50'] = price_data['close'].rolling(50).mean()
        signals['price_momentum'] = price_data['close'].pct_change()

        # 经济信号
        if 'hibor' in economic_data:
            hibor_df = economic_data['hibor']
            hibor_aligned = hibor_df.reindex(price_data.index, method='ffill')
            if 'rate' in hibor_aligned.columns:
                signals['hibor_rate'] = hibor_aligned['rate']
                signals['hibor_ma'] = hibor_aligned['rate'].rolling(10).mean()
                signals['hibor_momentum'] = hibor_aligned['rate'].pct_change()

        if 'gdp' in economic_data:
            gdp_df = economic_data['gdp']
            gdp_aligned = gdp_df.reindex(price_data.index, method='ffill')
            if 'gdp_growth' in gdp_aligned.columns:
                signals['gdp_growth'] = gdp_aligned['gdp_growth']

        if 'trade' in economic_data:
            trade_df = economic_data['trade']
            trade_aligned = trade_df.reindex(price_data.index, method='ffill')
            if 'trade_growth' in trade_aligned.columns:
                signals['trade_growth'] = trade_aligned['trade_growth']

        # 混合信号
        signals['hybrid_signal'] = self._calculate_hybrid_signal(signals)

        return signals.dropna()

    def _calculate_hybrid_signal(self, signals: pd.DataFrame) -> pd.Series:
        """计算混合信号"""
        # 价格动量权重
        price_weight = 0.6

        # 经济信号权重
        econ_weight = 0.4

        # 标准化信号
        price_signal = signals['price_momentum'].fillna(0)
        econ_signals = pd.Series(0, index=signals.index)

        # 聚合经济信号
        econ_cols = [col for col in signals.columns if 'hibor' in col or 'gdp' in col or 'trade' in col]
        if econ_cols:
            econ_signal = signals[econ_cols].mean(axis=1).fillna(0)
        else:
            econ_signal = pd.Series(0, index=signals.index)

        # 混合信号计算
        hybrid_signal = (price_signal * price_weight + econ_signal * econ_weight) / (price_weight + econ_weight)

        return hybrid_signal

    async def get_vectorbt_data(self, symbol: str, start_date: datetime,
                               end_date: datetime) -> Dict[str, pd.DataFrame]:
        """获取VectorBT格式的数据"""
        try:
            # 获取价格数据
            price_data = await self._get_price_data(symbol, start_date, end_date)

            # 获取政府数据
            economic_data = {}
            economic_data['hibor'] = await self._get_hibor_data(start_date, end_date)
            economic_data['gdp'] = await self._get_gdp_data(start_date, end_date)
            economic_data['trade'] = await self._get_trade_data(start_date, end_date)

            # 转换为VectorBT格式
            vbt_price_data = self._convert_to_vbt_format(price_data)
            vbt_economic_data = {k: self._convert_to_vbt_format(v) for k, v in economic_data.items()}

            # 对齐数据并创建信号
            aligned_data = self.align_price_economic_data(vbt_price_data, vbt_economic_data)
            signals = self.create_vectorbt_signals(vbt_price_data, vbt_economic_data)

            return {
                'price': vbt_price_data,
                'economic': vbt_economic_data,
                'aligned': aligned_data,
                'signals': signals
            }

        except Exception as e:
            logger.error(f"Error getting VectorBT data for {symbol}: {e}")
            return {'price': pd.DataFrame(), 'economic': {}, 'aligned': pd.DataFrame(), 'signals': pd.DataFrame()}

    def _convert_to_vbt_format(self, data: Any) -> pd.DataFrame:
        """转换为VectorBT格式"""
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, pd.DataFrame):
            df = data.copy()
        else:
            df = pd.DataFrame()

        # 确保OHLCV格式
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in df.columns:
                df[col] = np.nan

        return df

    async def _get_price_data(self, symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """获取真实价格数据 - 使用中央API"""
        try:
            # 使用真实的中央API获取港股数据
            import requests

            url = "http://18.180.162.113:9191/inst/getInst"
            params = {
                "symbol": symbol.lower(),
                "duration": (end_date - start_date).days
            }

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            # 解析嵌套数据结构
            if 'data' in data and 'close' in data['data']:
                dates = list(data['data']['close'].keys())
                close_prices = list(data['data']['close'].values())

                # 构建OHLCV数据 - 仅使用真实close价格，其他字段设为空值
                df_data = []
                for i, date in enumerate(dates):
                    close = close_prices[i]

                    # 只使用真实的close价格，其他OHLC字段标记为None
                    # 等待更多真实数据源时再完善
                    df_data.append({
                        'open': None,  # 等待真实开盘价数据源
                        'high': None,  # 等待真实最高价数据源
                        'low': None,   # 等待真实最低价数据源
                        'close': round(close, 2),  # 真实收盘价
                        'volume': None  # 等待真实交易量数据源
                    })

                df = pd.DataFrame(df_data)
                df.index = pd.to_datetime(dates)
                return df
            else:
                logger.error(f"Invalid data format from central API for {symbol}")
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error getting real price data for {symbol}: {e}")
            # 如果API失败，拒绝返回模拟数据
            raise ValueError(f"无法获取真实股价数据: {symbol}. 系统拒绝使用模拟数据。")

    async def _get_hibor_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """获取HIBOR数据"""
        try:
            data = await self.gov_collector.fetch_hibor_data(start_date, end_date)
            return self.convert_hibor_data(data)
        except Exception as e:
            logger.error(f"Error getting HIBOR data: {e}")
            return pd.DataFrame()

    async def _get_gdp_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """获取GDP数据"""
        try:
            data = await self.gov_collector.fetch_gdp_data(start_date, end_date)
            return self.convert_gdp_data(data)
        except Exception as e:
            logger.error(f"Error getting GDP data: e")
            return pd.DataFrame()

    async def _get_trade_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """获取贸易数据"""
        try:
            data = await self.gov_collector.fetch_trade_data(start_date, end_date)
            return self.convert_trade_data(data)
        except Exception as e:
            logger.error(f"Error getting trade data: {e}")
            return pd.DataFrame()

    def calculate_economic_indicators(self, economic_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.Series]:
        """计算经济指标"""
        indicators = {}

        # HIBOR相关指标
        if 'hibor' in economic_data:
            hibor_df = economic_data['hibor']
            if not hibor_df.empty and 'rate' in hibor_df.columns:
                indicators['hibor_rsi'] = vbt.RSI.run(hibor_df['rate'], window=14)
                indicators['hibor_ma_20'] = hibor_df['rate'].rolling(20).mean()
                indicators['hibor_ma_50'] = hibor_df['rate'].rolling(50).mean()

        # GDP相关指标
        if 'gdp' in economic_data:
            gdp_df = economic_data['gdp']
            if not gdp_df.empty and 'gdp_value' in gdp_df.columns:
                indicators['gdp_momentum'] = gdp_df['gdp_value'].pct_change(periods=4)
                indicators['gdp_ma_4'] = gdp_df['gdp_value'].rolling(4).mean()
                indicators['gdp_ma_12'] = gdp_df['gdp_value'].rolling(12).mean()

        # 贸易相关指标
        if 'trade' in economic_data:
            trade_df = economic_data['trade']
            if not trade_df.empty and 'trade_balance' in trade_df.columns:
                indicators['trade_balance_ma'] = trade_df['trade_balance'].rolling(20).mean()
                indicators['trade_balance_volatility'] = trade_df['trade_balance'].rolling(20).std()

        return indicators


class VectorBTEconomicIndicators:
    """VectorBT经济技术指标"""

    @staticmethod
    def hibor_momentum(hibor_rates: pd.Series, lookback: int = 20) -> pd.Series:
        """HIBOR动量指标"""
        return hibor_rates.pct_change(lookback)

    @staticmethod
    def hibor_trend_strength(hibor_rates: pd.Series, short_window: int = 10, long_window: int = 30) -> pd.Series:
        """HIBOR趋势强度指标"""
        short_ma = hibor_rates.rolling(short_window).mean()
        long_ma = hibor_rates.rolling(long_window).mean()
        return (short_ma - long_ma) / long_ma

    @staticmethod
    def gdp_acceleration(gdp_data: pd.Series) -> pd.Series:
        """GDP加速度指标"""
        return gdp_data.pct_change().pct_change()

    @staticmethod
    def trade_flow_index(export_data: pd.Series, import_data: pd.Series) -> pd.Series:
        """贸易流量指标"""
        trade_balance = export_data - import_data
        return trade_balance / import_data

    @staticmethod
    def composite_economic_signal(economic_data: Dict[str, pd.Series],
                                   weights: Optional[Dict[str, float]] = None) -> pd.Series:
        """复合经济信号"""
        if weights is None:
            weights = {'hibor': 0.4, 'gdp': 0.3, 'trade': 0.3}

        signal = pd.Series(0, index=next(iter(economic_data.values())).index)

        for source, data in economic_data.items():
            if source in weights and not data.empty:
                # 标准化数据
                normalized_data = (data - data.mean()) / data.std()
                signal += normalized_data * weights[source]

        return signal
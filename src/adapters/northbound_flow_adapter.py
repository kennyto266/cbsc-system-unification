#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
北向资金数据适配器
将北向资金数据整合到现有的量化系统
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class NorthboundFlowAdapter:
    """北向资金数据适配器"""

    def __init__(self, db_path: str = "data/quant_system.db", northbound_db_path: str = "data/northbound_flow.db"):
        self.db_path = db_path
        self.northbound_db_path = northbound_db_path

    def integrate_northbound_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        将北向资金数据整合到股票数据中
        """
        # 获取股票价格数据
        price_data = self._get_price_data(symbol, start_date, end_date)

        # 获取北向资金数据
        flow_data = self._get_northbound_flow_data(start_date, end_date)

        # 获取个股北向资金数据
        stock_flow_data = self._get_stock_northbound_data(symbol, start_date, end_date)

        # 合并数据
        merged_data = self._merge_data(price_data, flow_data, stock_flow_data)

        # 计算北向资金指标
        if not merged_data.empty:
            merged_data = self._calculate_northbound_indicators(merged_data)

        return merged_data

    def _get_price_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """从主数据库获取价格数据"""
        conn = sqlite3.connect(self.db_path)

        query = """
            SELECT timestamp as date, close_price, volume
            FROM market_data
            WHERE symbol = ? AND timestamp BETWEEN ? AND ?
            ORDER BY timestamp
        """

        df = pd.read_sql_query(query, conn, params=(symbol, start_date, end_date))
        conn.close()

        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)

        return df

    def _get_northbound_flow_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """获取整体北向资金流向数据"""
        if not Path(self.northbound_db_path).exists():
            logger.warning("北向资金数据库不存在")
            return pd.DataFrame()

        conn = sqlite3.connect(self.northbound_db_path)

        query = """
            SELECT trade_date, market, total_turnover, net_inflow, turnover_change
            FROM northbound_flow
            WHERE trade_date BETWEEN ? AND ?
            ORDER BY trade_date
        """

        df = pd.read_sql_query(query, conn, params=(start_date, end_date))
        conn.close()

        if not df.empty:
            # 转换为时间序列
            df['trade_date'] = pd.to_datetime(df['trade_date'])

            # 合并两个市场的数据
            pivot_df = df.pivot(index='trade_date', columns='market', values=['total_turnover', 'net_inflow'])
            pivot_df.columns = ['sh_turnover', 'sz_turnover', 'sh_net_inflow', 'sz_net_inflow']

            # 计算总计
            pivot_df['total_turnover'] = pivot_df['sh_turnover'] + pivot_df['sz_turnover']
            pivot_df['total_net_inflow'] = pivot_df['sh_net_inflow'] + pivot_df['sz_net_inflow']

            df = pivot_df.fillna(method='ffill').fillna(0)

        return df

    def _get_stock_northbound_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取个股北向资金数据"""
        if not Path(self.northbound_db_path).exists():
            return pd.DataFrame()

        # 转换股票代码格式
        stock_code = self._convert_symbol_format(symbol)
        if not stock_code:
            return pd.DataFrame()

        conn = sqlite3.connect(self.northbound_db_path)

        query = """
            SELECT trade_date, buy_volume, sell_volume, net_volume, turnover, holding_ratio
            FROM stock_northbound_flow
            WHERE stock_code = ? AND trade_date BETWEEN ? AND ?
            ORDER BY trade_date
        """

        df = pd.read_sql_query(query, conn, params=(stock_code, start_date, end_date))
        conn.close()

        if not df.empty:
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            df.set_index('trade_date', inplace=True)

        return df

    def _convert_symbol_format(self, symbol: str) -> Optional[str]:
        """转换股票代码格式"""
        # 例如：0700.HK -> 600519（腾讯控股的A股对应，如果有）
        # 这需要维护一个映射表
        symbol_mapping = {
            # 示例映射，需要根据实际情况更新
            '0700.HK': None,  # 腾讯控股在A股没有直接对应
            '0388.HK': None,  # 港交所
            '1398.HK': '601398',  # 工商银行
            '0941.HK': '601988',  # 中国银行
            '1299.HK': None,  # 友邦保险
        }

        return symbol_mapping.get(symbol)

    def _merge_data(self, price_data: pd.DataFrame, flow_data: pd.DataFrame, stock_flow: pd.DataFrame) -> pd.DataFrame:
        """合并价格数据和北向资金数据"""
        # 以价格数据为基础
        merged = price_data.copy()

        # 合并整体北向数据
        if not flow_data.empty:
            merged = pd.merge(merged, flow_data, left_index=True, right_index=True, how='left')

        # 合并个股北向数据
        if not stock_flow.empty:
            merged = pd.merge(merged, stock_flow, left_index=True, right_index=True, how='left')

        # 前向填充缺失值
        merged = merged.fillna(method='ffill').fillna(0)

        return merged

    def _calculate_northbound_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算北向资金相关指标"""
        # 1. 北向资金与价格的相关性
        if 'total_net_inflow' in df.columns:
            df['northbound_price_corr'] = df['close_price'].rolling(window=20).corr(df['total_net_inflow'])

        # 2. 北向资金强度指标
        if 'total_turnover' in df.columns:
            df['turnover_ma5'] = df['total_turnover'].rolling(window=5).mean()
            df['turnover_ma20'] = df['total_turnover'].rolling(window=20).mean()
            df['northbound_intensity'] = df['total_turnover'] / df['turnover_ma20'] - 1

        # 3. 个股北向资金占比
        if 'turnover' in df.columns and 'total_turnover' in df.columns:
            df['stock_northbound_ratio'] = df['turnover'] / (df['total_turnover'] + 1e-10)

        # 4. 北向资金流入信号
        if 'total_net_inflow' in df.columns:
            df['northbound_signal'] = 0
            df.loc[df['total_net_inflow'] > df['total_net_inflow'].quantile(0.8), 'northbound_signal'] = 1
            df.loc[df['total_net_inflow'] < df['total_net_inflow'].quantile(0.2), 'northbound_signal'] = -1

        # 5. 个股持有比例变化
        if 'holding_ratio' in df.columns:
            df['holding_ratio_change'] = df['holding_ratio'].diff()
            df['holding_trend'] = df['holding_ratio'].rolling(window=5).mean()

        # 6. 北向资金成交量占比
        if 'net_volume' in df.columns and 'volume' in df.columns:
            df['northbound_volume_ratio'] = df['net_volume'] / (df['volume'] + 1e-10)

        # 7. 北向资金动量指标
        if 'total_net_inflow' in df.columns:
            df['northbound_momentum'] = df['total_net_inflow'].rolling(window=5).sum()

        # 8. 北向资金异常检测
        if 'total_turnover' in df.columns:
            turnover_mean = df['total_turnover'].rolling(window=20).mean()
            turnover_std = df['total_turnover'].rolling(window=20).std()
            df['turnover_zscore'] = (df['total_turnover'] - turnover_mean) / (turnover_std + 1e-10)
            df['northbound_anomaly'] = abs(df['turnover_zscore']) > 2

        return df

class NorthboundStrategySignals:
    """基于北向资金的交易信号生成器"""

    @staticmethod
    def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
        """生成基于北向资金的交易信号"""
        signals = pd.DataFrame(index=df.index)

        # 信号1: 北向资金持续流入
        if 'total_net_inflow' in df.columns:
            signals['northbound_inflow_signal'] = 0
            inflow_positive = df['total_net_inflow'] > 0
            inflow_trend = df['total_net_inflow'].rolling(window=3).mean() > 0
            signals.loc[inflow_positive & inflow_trend, 'northbound_inflow_signal'] = 1

        # 信号2: 北向资金异常流入
        if 'turnover_zscore' in df.columns:
            signals['anomaly_inflow_signal'] = 0
            signals.loc[df['turnover_zscore'] > 2, 'anomaly_inflow_signal'] = 1

        # 信号3: 个股北向资金增持
        if 'holding_ratio_change' in df.columns:
            signals['holding_increase_signal'] = 0
            signals.loc[df['holding_ratio_change'] > 0.01, 'holding_increase_signal'] = 1

        # 信号4: 北向资金与价格背离
        if 'northbound_price_corr' in df.columns and 'total_net_inflow' in df.columns:
            signals['divergence_signal'] = 0
            price_falling = df['close_price'] < df['close_price'].shift(1)
            northflow_rising = df['total_net_inflow'] > df['total_net_inflow'].shift(1)
            signals.loc[price_falling & northflow_rising, 'divergence_signal'] = 1

        # 信号5: 北向资金突破
        if 'northbound_intensity' in df.columns:
            signals['breakout_signal'] = 0
            signals.loc[df['northbound_intensity'] > 0.5, 'breakout_signal'] = 1

        # 综合信号
        signal_columns = [col for col in signals.columns if col.endswith('_signal')]
        if signal_columns:
            signals['combined_signal'] = signals[signal_columns].sum(axis=1)
            signals['final_signal'] = 0
            signals.loc[signals['combined_signal'] >= 2, 'final_signal'] = 1
            signals.loc[signals['combined_signal'] <= -2, 'final_signal'] = -1

        return signals

# 测试代码
if __name__ == "__main__":
    # 创建适配器
    adapter = NorthboundFlowAdapter()

    # 测试数据整合
    test_symbol = "1398.HK"  # 工商银行，有A股对应
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

    # 获取整合后的数据
    integrated_data = adapter.integrate_northbound_data(test_symbol, start_date, end_date)

    if not integrated_data.empty:
        print(f"✅ 成功整合 {test_symbol} 的北向资金数据")
        print("\n数据预览:")
        print(integrated_data.head())

        # 生成交易信号
        signals = NorthboundStrategySignals.generate_signals(integrated_data)
        print("\n交易信号:")
        print(signals.tail(10))

        # 保存数据供后续使用
        output_path = f"data/northbound_integrated_{test_symbol}.csv"
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        integrated_data.to_csv(output_path)
        print(f"\n数据已保存到: {output_path}")
    else:
        print(f"❌ 未能获取 {test_symbol} 的数据")
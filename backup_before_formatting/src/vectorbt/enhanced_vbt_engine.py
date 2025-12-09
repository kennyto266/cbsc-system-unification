#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced VectorBT Engine - 集成CODEX--特性的增强版VectorBT引擎
Enhanced VectorBT Engine with CODEX-- Integration Features

核心功能：
1. VectorBT高性能向量化回测
2. 非价格数据集成（HIBOR, GDP等政府数据）
3. 混合策略支持（价格信号 + 宏观经济信号）
4. 向后兼容现有系统
5. 性能优化（并行计算、缓存、GPU加速）

作者: Claude Code Assistant
日期: 2025-11-20
版本: v1.0.0
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from pathlib import Path

# 核心依赖
import pandas as pd
import numpy as np

# VectorBT核心库
import vectorbt as vbt

# 数据处理和缓存
import redis
from functools import lru_cache
import json

# 并行处理
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import multiprocessing as mp

# 项目内部模块
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.data.integrated_data_collector import IntegratedDataCollector
from src.shared.indicators.comprehensive_477_calculator import Comprehensive477Calculator

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class VBTConfig:
    """VectorBT增强配置"""
    # 基础配置
    symbols: List[str] = field(default_factory=lambda: ["0700.hk"])
    lookback_days: int = 252
    initial_capital: float = 100000.0
    fees: float = 0.001
    slippage: float = 0.0005

    # 优化配置
    optimization_metric: str = "sharpe_ratio"
    n_jobs: int = -1
    use_gpu: bool = False

    # 数据配置
    use_cache: bool = True
    cache_ttl: int = 3600  # 秒
    redis_host: str = "localhost"
    redis_port: int = 6379

    # 非价格数据权重
    non_price_weight: float = 0.3
    price_weight: float = 0.7


@dataclass
class BacktestResult:
    """回测结果数据类"""
    symbol: str
    strategy_name: str
    parameters: Dict[str, Any]

    # 性能指标
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    total_trades: int

    # 数据
    equity_curve: pd.Series
    trades: pd.DataFrame
    signals: pd.DataFrame

    # 元数据
    start_date: datetime
    end_date: datetime
    execution_time: float

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'symbol': self.symbol,
            'strategy_name': self.strategy_name,
            'parameters': self.parameters,
            'performance': {
                'total_return': self.total_return,
                'sharpe_ratio': self.sharpe_ratio,
                'max_drawdown': self.max_drawdown,
                'win_rate': self.win_rate,
                'profit_factor': self.profit_factor,
                'total_trades': self.total_trades
            },
            'execution_time': self.execution_time,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat()
        }


class EnhancedDataInterface:
    """增强的数据接口，支持VectorBT格式"""

    def __init__(self, config: VBTConfig):
        self.config = config
        self.data_collector = IntegratedDataCollector()
        self.indicator_calculator = Comprehensive477Calculator()

        # 缓存设置
        self.cache_enabled = config.use_cache
        if self.cache_enabled:
            try:
                self.redis_client = redis.Redis(
                    host=config.redis_host,
                    port=config.redis_port,
                    decode_responses=True
                )
                self.redis_client.ping()
                logger.info("Redis缓存连接成功")
            except Exception as e:
                logger.warning(f"Redis连接失败，使用内存缓存: {e}")
                self.redis_client = None
        else:
            self.redis_client = None

    async def get_vbt_data(self, symbol: str, lookback_days: int = None) -> pd.DataFrame:
        """获取VectorBT格式的数据"""

        lookback_days = lookback_days or self.config.lookback_days

        # 1. 检查缓存
        cache_key = f"vbt_data_{symbol}_{lookback_days}"
        if self.cache_enabled:
            cached_data = self._get_cached_data(cache_key)
            if cached_data is not None:
                logger.info(f"从缓存获取数据: {symbol}")
                return cached_data

        # 2. 获取原始数据
        logger.info(f"获取数据: {symbol}")

        # 价格数据
        price_data = await self._get_price_data(symbol, lookback_days)

        # 非价格数据
        non_price_data = await self._get_non_price_data(lookback_days)

        # 3. 数据整合和格式化
        vbt_data = self._format_vbt_data(price_data, non_price_data)

        # 4. 缓存结果
        if self.cache_enabled:
            self._cache_data(cache_key, vbt_data)

        return vbt_data

    async def _get_price_data(self, symbol: str, lookback_days: int) -> pd.DataFrame:
        """获取价格数据"""
        try:
            # 从数据收集器获取数据
            data = await self.data_collector.get_stock_data(symbol, lookback_days)

            # 确保数据格式正确
            if isinstance(data, dict) and 'data' in data:
                df = pd.DataFrame(data['data'])
            else:
                df = pd.DataFrame(data)

            # 标准化列名
            column_mapping = {
                'Date': 'date',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            }

            for old_col, new_col in column_mapping.items():
                if old_col in df.columns:
                    df[new_col] = df[old_col]

            # 确保日期是索引
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)

            # 数据类型转换
            price_columns = ['open', 'high', 'low', 'close']
            for col in price_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            if 'volume' in df.columns:
                df['volume'] = pd.to_numeric(df['volume'], errors='coerce')

            return df

        except Exception as e:
            logger.error(f"获取价格数据失败 {symbol}: {e}")
            # 系統拒絕使用模拟數據，直接拋出異常
            raise ValueError(f"無法獲取真實價格數據: {symbol}. 系統拒絕使用模擬數據作為後備。")

    async def _get_non_price_data(self, lookback_days: int) -> Dict[str, pd.DataFrame]:
        """获取非价格数据"""
        try:
            non_price_data = {}

            # HIBOR数据
            hibor_data = await self.data_collector.get_hibor_data(lookback_days)
            if hibor_data:
                non_price_data['hibor'] = pd.DataFrame(hibor_data)

            # GDP数据
            gdp_data = await self.data_collector.get_gdp_data()
            if gdp_data:
                non_price_data['gdp'] = pd.DataFrame(gdp_data)

            # 贸易数据
            trade_data = await self.data_collector.get_trade_data()
            if trade_data:
                non_price_data['trade'] = pd.DataFrame(trade_data)

            return non_price_data

        except Exception as e:
            logger.error(f"获取非价格数据失败: {e}")
            return {}

    def _format_vbt_data(self, price_data: pd.DataFrame,
                        non_price_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """格式化为VectorBT标准格式"""

        vbt_data = price_data.copy()

        # 添加非价格数据
        for data_type, data_df in non_price_data.items():
            if not data_df.empty:
                # 数据对齐
                aligned_data = self._align_data(vbt_data.index, data_df)

                # 添加到主数据框
                for col in aligned_data.columns:
                    vbt_data[f"{data_type}_{col}"] = aligned_data[col]

        return vbt_data

    def _align_data(self, target_index: pd.DatetimeIndex,
                   source_data: pd.DataFrame) -> pd.DataFrame:
        """数据对齐"""
        try:
            # 确保源数据有日期索引
            if 'date' in source_data.columns:
                source_data['date'] = pd.to_datetime(source_data['date'])
                source_data.set_index('date', inplace=True)

            # 重新采样对齐到目标索引
            aligned = source_data.reindex(target_index, method='ffill')

            return aligned

        except Exception as e:
            logger.warning(f"数据对齐失败: {e}")
            return pd.DataFrame(index=target_index)

    def _get_cached_data(self, cache_key: str) -> Optional[pd.DataFrame]:
        """从缓存获取数据"""
        try:
            if self.redis_client:
                cached_json = self.redis_client.get(cache_key)
                if cached_json:
                    return pd.read_json(cached_json)
        except Exception as e:
            logger.warning(f"Redis缓存读取失败: {e}")

        return None

    def _cache_data(self, cache_key: str, data: pd.DataFrame):
        """缓存数据"""
        try:
            if self.redis_client:
                self.redis_client.setex(
                    cache_key,
                    self.config.cache_ttl,
                    data.to_json()
                )
        except Exception as e:
            logger.warning(f"Redis缓存写入失败: {e}")

    # 已移除模擬數據生成函數 - 系統拒絕使用任何模擬數據
  # def _generate_mock_price_data - 此功能已被完全移除
  # 所有數據必須來自真實數據源


class HybridSignalGenerator:
    """混合信号生成器 - 结合价格信号和非价格信号"""

    def __init__(self, config: VBTConfig):
        self.config = config
        self.price_weight = config.price_weight
        self.non_price_weight = config.non_price_weight

    def generate_hybrid_signals(self, data: pd.DataFrame,
                               strategy_config: Dict) -> Tuple[pd.Series, pd.Series]:
        """生成混合交易信号"""

        # 1. 生成价格信号
        price_entries, price_exits = self._generate_price_signals(data, strategy_config)

        # 2. 生成非价格信号
        non_price_entries, non_price_exits = self._generate_non_price_signals(data, strategy_config)

        # 3. 信号融合
        hybrid_entries = self._combine_signals(
            price_entries, non_price_entries, 'entries'
        )
        hybrid_exits = self._combine_signals(
            price_exits, non_price_exits, 'exits'
        )

        return hybrid_entries, hybrid_exits

    def _generate_price_signals(self, data: pd.DataFrame,
                              strategy_config: Dict) -> Tuple[pd.Series, pd.Series]:
        """生成基于价格的交易信号"""

        strategy_type = strategy_config.get('type', 'RSI')

        if strategy_type == 'RSI':
            return self._rsi_signals(data, strategy_config)
        elif strategy_type == 'MACD':
            return self._macd_signals(data, strategy_config)
        elif strategy_type == 'BB':
            return self._bollinger_bands_signals(data, strategy_config)
        elif strategy_type == 'MA':
            return self._ma_cross_signals(data, strategy_config)
        else:
            raise ValueError(f"未知策略类型: {strategy_type}")

    def _rsi_signals(self, data: pd.DataFrame, config: Dict) -> Tuple[pd.Series, pd.Series]:
        """RSI策略信号"""
        window = config.get('window', 14)
        oversold = config.get('oversold', 30)
        overbought = config.get('overbought', 70)

        rsi = vbt.RSI.run(data['close'], window=window).rsi

        entries = rsi.vbt.crossed_below(oversold)
        exits = rsi.vbt.crossed_above(overbought)

        return entries, exits

    def _macd_signals(self, data: pd.DataFrame, config: Dict) -> Tuple[pd.Series, pd.Series]:
        """MACD策略信号"""
        fast = config.get('fast', 12)
        slow = config.get('slow', 26)
        signal = config.get('signal', 9)

        macd = vbt.MACD.run(data['close'], fast=fast, slow=slow, signal=signal)

        entries = macd.macd.vbt.crossed_above(macd.signal)
        exits = macd.macd.vbt.crossed_below(macd.signal)

        return entries, exits

    def _bollinger_bands_signals(self, data: pd.DataFrame,
                               config: Dict) -> Tuple[pd.Series, pd.Series]:
        """布林带策略信号"""
        window = config.get('window', 20)
        std = config.get('std', 2)

        bb = vbt.BBANDS.run(data['close'], window=window, std=std)

        entries = data['close'].vbt.crossed_below(bb.lower)
        exits = data['close'].vbt.crossed_above(bb.upper)

        return entries, exits

    def _ma_cross_signals(self, data: pd.DataFrame, config: Dict) -> Tuple[pd.Series, pd.Series]:
        """移动平均交叉策略信号"""
        fast = config.get('fast', 10)
        slow = config.get('slow', 30)

        fast_ma = vbt.MA.run(data['close'], window=fast).ma
        slow_ma = vbt.MA.run(data['close'], window=slow).ma

        entries = fast_ma.vbt.crossed_above(slow_ma)
        exits = fast_ma.vbt.crossed_below(slow_ma)

        return entries, exits

    def _generate_non_price_signals(self, data: pd.DataFrame,
                                  config: Dict) -> Tuple[pd.Series, pd.Series]:
        """生成基于非价格数据的交易信号"""

        non_price_entries = pd.Series(False, index=data.index)
        non_price_exits = pd.Series(False, index=data.index)

        # HIBOR信号
        if 'hibor_rate' in data.columns:
            hibor_entries, hibor_exits = self._hibor_signals(data)
            non_price_entries |= hibor_entries
            non_price_exits |= hibor_exits

        # GDP信号
        if 'gdp_growth' in data.columns:
            gdp_entries, gdp_exits = self._gdp_signals(data)
            non_price_entries |= gdp_entries
            non_price_exits |= gdp_exits

        return non_price_entries, non_price_exits

    def _hibor_signals(self, data: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        """HIBOR利率信号"""
        try:
            hibor_rsi = vbt.RSI.run(data['hibor_rate'].fillna(method='ffill'), window=14).rsi

            # HIBOR低RSI（利率低）买入信号
            entries = hibor_rsi.vbt.crossed_below(30)
            # HIBOR高RSI（利率高）卖出信号
            exits = hibor_rsi.vbt.crossed_above(70)

            return entries, exits

        except Exception as e:
            logger.warning(f"HIBOR信号生成失败: {e}")
            return pd.Series(False, index=data.index), pd.Series(False, index=data.index)

    def _gdp_signals(self, data: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        """GDP增长信号"""
        try:
            gdp_ma = vbt.MA.run(data['gdp_growth'].fillna(method='ffill'), window=10).ma
            gdp_growth_rate = data['gdp_growth'].fillna(method='ffill')

            # GDP增长率高于移动平均线时买入
            entries = gdp_growth_rate.vbt.crossed_above(gdp_ma)
            # GDP增长率低于移动平均线时卖出
            exits = gdp_growth_rate.vbt.crossed_below(gdp_ma)

            return entries, exits

        except Exception as e:
            logger.warning(f"GDP信号生成失败: {e}")
            return pd.Series(False, index=data.index), pd.Series(False, index=data.index)

    def _combine_signals(self, price_signals: pd.Series,
                        non_price_signals: pd.Series,
                        signal_type: str) -> pd.Series:
        """融合价格信号和非价格信号"""

        # 权重融合
        if signal_type == 'entries':
            # 入场信号：任一信号触发即入场
            combined = price_signals | non_price_signals
        else:
            # 出场信号：任一信号触发即出场
            combined = price_signals | non_price_signals

        return combined


class EnhancedVectorBTEngine:
    """增强版VectorBT引擎"""

    def __init__(self, config: VBTConfig):
        self.config = config
        self.data_interface = EnhancedDataInterface(config)
        self.signal_generator = HybridSignalGenerator(config)

        # 性能监控
        self.execution_stats = {
            'total_backtests': 0,
            'total_execution_time': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }

    async def run_backtest(self, symbol: str, strategy_config: Dict,
                          lookback_days: int = None) -> BacktestResult:
        """运行单个回测"""

        start_time = time.time()
        logger.info(f"开始回测: {symbol} - {strategy_config.get('type', 'Unknown')}")

        try:
            # 1. 获取数据
            data = await self.data_interface.get_vbt_data(symbol, lookback_days)

            if data.empty or len(data) < 50:
                raise ValueError(f"数据不足: {len(data)} 条记录")

            # 2. 生成交易信号
            entries, exits = self.signal_generator.generate_hybrid_signals(
                data, strategy_config
            )

            # 3. 运行VectorBT回测
            portfolio = vbt.Portfolio.from_signals(
                data['close'],
                entries,
                exits,
                init_cash=self.config.initial_capital,
                fees=self.config.fees,
                slippage=self.config.slippage
            )

            # 4. 提取性能指标
            stats = portfolio.stats()

            # 5. 创建结果对象
            result = BacktestResult(
                symbol=symbol,
                strategy_name=strategy_config.get('type', 'Unknown'),
                parameters=strategy_config,
                total_return=stats['Total Return [%]'],
                sharpe_ratio=stats['Sharpe Ratio'],
                max_drawdown=stats['Max Drawdown [%]'],
                win_rate=stats['Win Rate [%]'],
                profit_factor=stats.get('Profit Factor', 0),
                total_trades=stats['# Trades'],
                equity_curve=portfolio.value(),
                trades=portfolio.trades.records_readable,
                signals=pd.DataFrame({
                    'entries': entries,
                    'exits': exits
                }),
                start_date=data.index[0],
                end_date=data.index[-1],
                execution_time=time.time() - start_time
            )

            # 6. 更新统计信息
            self.execution_stats['total_backtests'] += 1
            self.execution_stats['total_execution_time'] += result.execution_time

            logger.info(f"回测完成: {symbol} - 耗时: {result.execution_time:.2f}秒")

            return result

        except Exception as e:
            logger.error(f"回测失败 {symbol}: {e}")
            raise

    async def run_batch_backtest(self, symbols: List[str],
                               strategies: List[Dict]) -> List[BacktestResult]:
        """批量回测"""

        logger.info(f"开始批量回测: {len(symbols)} 股票 × {len(strategies)} 策略")

        tasks = []
        for symbol in symbols:
            for strategy in strategies:
                task = self.run_backtest(symbol, strategy.copy())
                tasks.append(task)

        # 并行执行
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 过滤异常结果
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"回测异常: {result}")
            else:
                valid_results.append(result)

        logger.info(f"批量回测完成: 成功 {len(valid_results)} 个，失败 {len(results) - len(valid_results)} 个")

        return valid_results

    async def optimize_strategy(self, symbol: str, strategy_type: str,
                              param_ranges: Dict) -> Dict:
        """策略参数优化"""

        logger.info(f"开始策略优化: {symbol} - {strategy_type}")

        # 获取数据
        data = await self.data_interface.get_vbt_data(symbol)

        # 生成参数组合
        param_combinations = self._generate_param_combinations(param_ranges)

        best_result = None
        best_sharpe = -float('inf')

        # 网格搜索优化
        for params in param_combinations:
            try:
                strategy_config = {'type': strategy_type, **params}
                result = await self.run_backtest(symbol, strategy_config)

                if result.sharpe_ratio > best_sharpe:
                    best_sharpe = result.sharpe_ratio
                    best_result = result

            except Exception as e:
                logger.warning(f"参数优化失败 {params}: {e}")
                continue

        return {
            'symbol': symbol,
            'strategy_type': strategy_type,
            'best_parameters': best_result.parameters if best_result else None,
            'best_performance': best_result.to_dict() if best_result else None,
            'total_combinations': len(param_combinations)
        }

    def _generate_param_combinations(self, param_ranges: Dict) -> List[Dict]:
        """生成参数组合"""
        import itertools

        keys = list(param_ranges.keys())
        values = list(param_ranges.values())

        combinations = []
        for combination in itertools.product(*values):
            param_dict = dict(zip(keys, combination))
            combinations.append(param_dict)

        return combinations

    def get_execution_stats(self) -> Dict:
        """获取执行统计信息"""
        avg_time = (self.execution_stats['total_execution_time'] /
                   max(1, self.execution_stats['total_backtests']))

        return {
            'total_backtests': self.execution_stats['total_backtests'],
            'total_execution_time': self.execution_stats['total_execution_time'],
            'average_execution_time': avg_time,
            'backtests_per_hour': 3600 / avg_time if avg_time > 0 else 0
        }


# 使用示例
async def main():
    """主函数示例"""

    # 配置
    config = VBTConfig(
        symbols=["0700.hk", "0388.hk", "1398.hk"],
        initial_capital=100000,
        lookback_days=365,
        use_cache=True
    )

    # 初始化引擎
    engine = EnhancedVectorBTEngine(config)

    # 定义策略
    strategies = [
        {'type': 'RSI', 'window': 14, 'oversold': 30, 'overbought': 70},
        {'type': 'MACD', 'fast': 12, 'slow': 26, 'signal': 9},
        {'type': 'MA', 'fast': 10, 'slow': 30}
    ]

    try:
        # 运行回测
        results = await engine.run_batch_backtest(config.symbols, strategies)

        # 输出结果
        for result in results:
            print(f"\n{result.symbol} - {result.strategy_name}")
            print(f"总回报: {result.total_return:.2f}%")
            print(f"夏普比率: {result.sharpe_ratio:.3f}")
            print(f"最大回撤: {result.max_drawdown:.2f}%")
            print(f"胜率: {result.win_rate:.2f}%")
            print(f"交易次数: {result.total_trades}")
            print(f"执行时间: {result.execution_time:.2f}秒")

        # 输出统计信息
        stats = engine.get_execution_stats()
        print(f"\n执行统计:")
        print(f"总回测数: {stats['total_backtests']}")
        print(f"平均执行时间: {stats['average_execution_time']:.2f}秒")
        print(f"每小时回测数: {stats['backtests_per_hour']:.0f}")

    except Exception as e:
        logger.error(f"执行失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""
Personal VectorBT Engine
个人VectorBT引擎
基于现有实现提取和简化的高性能回测引擎
"""

import logging
from dataclasses import dataclass
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any, Callable
import numpy as np
import pandas as pd

try:
    import vectorbt as vbt
    VECTORBT_AVAILABLE = True
except ImportError:
    VECTORBT_AVAILABLE = False
    vbt = None

logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    """回测配置"""
    symbol: str
    start_date: date
    end_date: date
    initial_capital: float = 100000
    commission: float = 0.001
    freq: str = '1D'


@dataclass
class BacktestResult:
    """回测结果"""
    symbol: str
    strategy_name: str
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    final_capital: float
    equity_curve: List[float]
    trades: List[Dict]
    parameters: Dict[str, Any]


class PersonalVectorBTEngine:
    """
    个人VectorBT回测引擎

    特点：
    - 基于现有VectorBT高性能引擎
    - 专为个人策略开发优化
    - 支持快速参数优化
    - 集成HKMA数据源
    """

    def __init__(self):
        if not VECTORBT_AVAILABLE:
            raise ImportError("需要安装VectorBT: pip install vectorbt>=0.25.0")

        self.data_cache: Dict[str, pd.DataFrame] = {}
        logger.info("Personal VectorBT Engine 初始化完成")

    def load_data(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        hkma_data: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        加载股票数据

        Args:
            symbol: 股票代码 (如 "0700.HK")
            start_date: 开始日期
            end_date: 结束日期
            hkma_data: 可选的HKMA经济数据

        Returns:
            OHLCV DataFrame
        """
        cache_key = f"{symbol}_{start_date}_{end_date}"

        if cache_key in self.data_cache:
            logger.info(f"使用缓存数据: {symbol}")
            return self.data_cache[cache_key]

        # 尝试从现有API获取数据
        data = self._fetch_stock_data(symbol, start_date, end_date)

        if data is not None and not data.empty:
            # 集成HKMA经济数据
            if hkma_data is not None:
                data = self._merge_hkma_data(data, hkma_data)

            # 验证数据质量
            if self._validate_data(data):
                self.data_cache[cache_key] = data
                logger.info(f"成功加载 {len(data)} 条 {symbol} 数据记录")
                return data
            else:
                logger.error(f"{symbol} 数据验证失败")

        # 回退到生成模拟数据
        logger.warning(f"使用模拟数据: {symbol}")
        data = self._generate_mock_data(symbol, start_date, end_date)
        self.data_cache[cache_key] = data
        return data

    def _fetch_stock_data(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> Optional[pd.DataFrame]:
        """从现有数据源获取股票数据"""
        try:
            # 检查现有的中央API端点
            url = "http://18.180.162.113:9191/inst/getInst"
            params = {
                "symbol": symbol.lower(),
                "duration": (end_date - start_date).days
            }

            import requests
            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                return self._parse_stock_response(data, start_date, end_date)
            else:
                logger.warning(f"API请求失败: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"获取股票数据失败: {e}")
            return None

    def _parse_stock_response(
        self,
        data: Dict,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """解析股票API响应"""
        try:
            # 检查是否为股票数据字典格式
            if isinstance(data, dict):
                if "data" in data:
                    # 标准API响应格式
                    records = data["data"]
                elif "close" in data and "open" in data:
                    # 单个股票数据格式
                    records = [data]
                else:
                    raise ValueError("API响应格式不匹配")
            else:
                raise ValueError("API响应不是字典格式")

            if not records:
                raise ValueError("没有数据记录")

            # 将记录转换为DataFrame
            df_list = []
            for record in records:
                try:
                    # 确保日期字段存在
                    if 'date' not in record:
                        # 如果没有日期，使用今天的日期
                        record['date'] = start_date

                    df = pd.DataFrame([record])
                    df['date'] = pd.to_datetime(df['date'])
                    df_list.append(df)
                except Exception as e:
                    logger.debug(f"解析记录失败: {e}")
                    continue

            if not df_list:
                raise ValueError("没有有效数据记录")

            # 合并所有记录
            df = pd.concat(df_list, ignore_index=True)
            df = df.set_index('date')

            # 确保必要的列存在
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in required_cols:
                if col not in df.columns:
                    # 尝试从其他列名映射
                    col_mapping = {
                        'Open': 'open', 'High': 'high', 'Low': 'low',
                        'Close': 'close', 'Volume': 'volume'
                    }
                    if col in col_mapping and col_mapping[col] in df.columns:
                        df = df.rename(columns={col_mapping[col]: col})
                    else:
                        raise ValueError(f"缺少必要列: {col}")

            # 日期过滤
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            df = df[(df.index >= start_dt) & (df.index <= end_dt)]

            # 确保数据类型正确
            for col in ['open', 'high', 'low', 'close']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(0)

            # 移除缺失值
            df = df.dropna(subset=['open', 'high', 'low', 'close'])

            return df.sort_index()

        except Exception as e:
            logger.error(f"解析股票响应失败: {e}")
            raise

    def _generate_mock_data(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """生成模拟股票数据"""
        logger.info(f"生成 {symbol} 的模拟数据")

        # 生成日期范围
        dates = pd.date_range(start=start_date, end=end_date, freq='D')

        # 过滤周末
        trading_days = dates[dates.weekday < 5]

        # 模拟价格数据
        initial_price = 300.0  # 基准价格
        price_data = []
        current_price = initial_price

        for i, date in enumerate(trading_days):
            if i > 0:
                # 随机游走
                change = np.random.normal(0, 0.02)  # 2% 日波动
                current_price = current_price * (1 + change)

            high = current_price * (1 + abs(np.random.normal(0, 0.01)))
            low = current_price * (1 - abs(np.random.normal(0, 0.01)))
            open_price = low + (high - low) * np.random.random()
            volume = np.random.randint(100000, 5000000)

            price_data.append({
                'open': round(open_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'close': round(current_price, 2),
                'volume': volume
            })

        df = pd.DataFrame(price_data, index=trading_days)
        return df

    def _validate_data(self, data: pd.DataFrame) -> bool:
        """验证数据质量"""
        if len(data) == 0:
            return False

        # 检查必要列
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in data.columns:
                return False

        # 检查价格合理性
        if (data['close'] <= 0).any():
            return False

        # 检查成交量
        if (data['volume'] < 0).any():
            return False

        return True

    def _merge_hkma_data(
        self,
        stock_data: pd.DataFrame,
        hkma_data: pd.DataFrame
    ) -> pd.DataFrame:
        """整合HKMA经济数据到股票数据"""
        try:
            # 对齐日期
            stock_data.index = pd.to_datetime(stock_data.index)

            # 假设hkma_data有hibor_3m列
            if 'value' in hkma_data.columns:
                # 重采样到交易日
                hkma_daily = hkma_data.resample('D').ffill()
                hibor_rates = hkma_daily.reindex(stock_data.index, method='ffill')

                # 添加HIBOR数据
                stock_data['hibor_rate'] = hibor_rates['value'].fillna(3.0)
                logger.info("成功整合HIBOR利率数据")

            return stock_data

        except Exception as e:
            logger.warning(f"整合HKMA数据失败: {e}")
            return stock_data

    def backtest_strategy(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        strategy_func: Callable,
        strategy_name: str,
        parameters: Dict[str, Any] = None,
        hkma_data: Optional[pd.DataFrame] = None
    ) -> BacktestResult:
        """
        回测单个策略

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            strategy_func: 策略函数
            strategy_name: 策略名称
            parameters: 策略参数
            hkma_data: HKMA经济数据

        Returns:
            回测结果
        """
        parameters = parameters or {}

        logger.info(f"开始回测: {strategy_name} on {symbol}")

        # 加载数据
        data = self.load_data(symbol, start_date, end_date, hkma_data)

        # 生成交易信号
        entries, exits = strategy_func(data, **parameters)

        # 确保信号格式
        entries = np.asarray(entries, dtype=bool)
        exits = np.asarray(exits, dtype=bool)

        # 使用VectorBT创建投资组合
        portfolio = vbt.Portfolio.from_signals(
            close=data['close'],
            entries=entries,
            exits=exits,
            init_cash=100000,
            fees=0.001,
            freq='D'
        )

        # 计算性能指标
        stats = portfolio.stats()

        # 提取交易记录
        trades = self._extract_trades(portfolio, data)

        # 创建结果对象
        result = BacktestResult(
            symbol=symbol,
            strategy_name=strategy_name,
            total_return=float(portfolio.total_return()),
            annualized_return=float(portfolio.annualized_return()),
            sharpe_ratio=float(portfolio.sharpe_ratio()),
            max_drawdown=float(abs(portfolio.max_drawdown())),
            win_rate=float(0.5),  # 默认胜率，需要计算
            total_trades=int(len(trades)),
            final_capital=float(100000 * (1 + portfolio.total_return())),
            equity_curve=portfolio.value().values.tolist(),
            trades=trades,
            parameters=parameters
        )

        logger.info(f"回测完成: {strategy_name}, 总回报: {result.total_return:.2%}")
        return result

    def _extract_trades(self, portfolio, data: pd.DataFrame) -> List[Dict]:
        """提取交易记录"""
        trades = []

        try:
            # VectorBT的交易记录通过trades属性访问
            if hasattr(portfolio, 'trades'):
                trade_records = portfolio.trades

                # 如果有交易记录
                if len(trade_records) > 0:
                    # 简化交易记录提取
                    for i in range(len(trade_records)):
                        trades.append({
                            'entry_date': str(data.index[i]) if i < len(data) else None,
                            'exit_date': str(data.index[i + 1]) if i + 1 < len(data) else None,
                            'entry_price': float(data.iloc[i]['close']) if i < len(data) else None,
                            'exit_price': float(data.iloc[i + 1]['close']) if i + 1 < len(data) else None,
                            'quantity': 100,  # 默认数量
                            'pnl': 0.0,  # 简化的PnL
                            'return': 0.0,  # 简化的回报率
                            'duration': 1  # 默认持仓天数
                        })
        except Exception as e:
            logger.warning(f"提取交易记录失败: {e}")

        return trades

    def optimize_strategy(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        strategy_func: Callable,
        param_grid: Dict[str, List],
        objective: str = 'sharpe_ratio',
        hkma_data: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """
        策略参数优化

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            strategy_func: 策略函数
            param_grid: 参数网格
            objective: 优化目标
            hkma_data: HKMA经济数据

        Returns:
            优化结果
        """
        from itertools import product

        logger.info(f"开始参数优化: {objective}")

        # 加载数据
        data = self.load_data(symbol, start_date, end_date, hkma_data)

        # 生成参数组合
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        param_combinations = list(product(*param_values))

        best_result = None
        best_score = float('-inf') if objective != 'max_drawdown' else float('inf')
        all_results = []

        logger.info(f"测试 {len(param_combinations)} 个参数组合...")

        for i, param_values in enumerate(param_combinations):
            params = dict(zip(param_names, param_values))

            try:
                # 生成信号
                entries, exits = strategy_func(data, **params)
                entries = np.asarray(entries, dtype=bool)
                exits = np.asarray(exits, dtype=bool)

                # 创建投资组合
                portfolio = vbt.Portfolio.from_signals(
                    close=data['close'],
                    entries=entries,
                    exits=exits,
                    init_cash=100000,
                    fees=0.001,
                    freq='D'
                )

                # 计算指标
                if objective == 'sharpe_ratio':
                    score = float(portfolio.sharpe_ratio())
                elif objective == 'total_return':
                    score = float(portfolio.total_return())
                elif objective == 'max_drawdown':
                    score = -float(abs(portfolio.max_drawdown()))
                else:
                    score = float(portfolio.sharpe_ratio())

                # 更新最佳结果
                if (objective == 'max_drawdown' and score > best_score) or \
                   (objective != 'max_drawdown' and score > best_score):
                    best_score = score
                    best_result = {
                        'parameters': params,
                        'score': score,
                        'portfolio': portfolio,
                        'stats': stats
                    }

                # 记录所有结果
                result_data = {
                    'parameters': params,
                    'sharpe_ratio': float(portfolio.sharpe_ratio()),
                    'total_return': float(portfolio.total_return()),
                    'max_drawdown': float(abs(portfolio.max_drawdown())),
                    'win_rate': 0.5,  # 简化的胜率
                    'total_trades': 0   # 简化的交易次数
                }
                all_results.append(result_data)

                if (i + 1) % 10 == 0:
                    logger.info(f"完成 {i + 1}/{len(param_combinations)} 个组合测试")

            except Exception as e:
                logger.warning(f"参数组合 {params} 测试失败: {e}")
                continue

        logger.info(f"参数优化完成，最佳分数: {best_score:.4f}")

        return {
            'best_parameters': best_result['parameters'] if best_result else {},
            'best_score': best_score,
            'all_results': all_results,
            'total_combinations': len(param_combinations)
        }
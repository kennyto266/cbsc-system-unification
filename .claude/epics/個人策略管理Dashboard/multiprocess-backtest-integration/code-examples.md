# VectorBT多進程回測集成 - 代碼示例

## 1. 核心VectorBT適配器實現

### 1.1 基礎適配器類

```python
# src/backtest/vectorbt_adapter.py
"""
VectorBT適配器 - 核心實現
將VectorBT功能集成到CBSC回測系統
"""

import vectorbt as vbt
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
import asyncio
from functools import partial
import logging
import time
from datetime import datetime
import pickle
import warnings

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 抑制VectorBT警告
warnings.filterwarnings('ignore', category=FutureWarning)

@dataclass
class VectorBTConfig:
    """VectorBT配置參數"""
    # 基礎參數
    init_capital: float = 1000000.0
    cash_sharing: bool = True
    call_seq: str = 'auto'
    segment_reps: int = 1

    # 交易成本
    fees: float = 0.001
    slippage: float = 0.0005

    # 數據參數
    freq: str = '1D'
    init_cash: Optional[float] = None

    # 高級參數
    size_type: str = 'amount'  # 'amount', 'value', 'percent'
    size: float = 1.0

    # 風險管理
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    trailing_stop: Optional[float] = None

class VectorBTAdapter:
    """VectorBT適配器主類"""

    def __init__(self, config: Optional[VectorBTConfig] = None):
        self.config = config or VectorBTConfig()
        self.data = None
        self.portfolio = None
        self.results = {}

    def load_data(self, price_data: pd.DataFrame) -> 'VectorBTAdapter':
        """
        加載和預處理價格數據

        Args:
            price_data: 包含OHLCV的DataFrame

        Returns:
            Self for chaining
        """
        try:
            # 數據驗證
            required_columns = ['open', 'high', 'low', 'close']
            if not all(col in price_data.columns for col in required_columns):
                raise ValueError(f"數據缺少必要列: {required_columns}")

            # 創建VectorBT Data對象
            self.data = vbt.Data.from_data(price_data)

            # 數據優化
            self._optimize_data()

            logger.info(f"成功加載數據: {len(price_data)}行, {len(price_data.columns.unique(level=0) if hasattr(price_data.columns, 'unique') else ['single'])}個資產")

        except Exception as e:
            logger.error(f"加載數據失敗: {e}")
            raise

        return self

    def _optimize_data(self):
        """優化數據格式以節省內存"""
        if self.data is None:
            return

        # 轉換為更高效的數據類型
        for attr in ['open', 'high', 'low', 'close']:
            if hasattr(self.data, attr):
                data = getattr(self.data, attr)
                if data.dtype == 'float64':
                    setattr(self.data, attr, data.astype('float32'))

    def prepare_signals(self, strategy_func: callable, **kwargs) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        使用策略函數生成交易信號

        Args:
            strategy_func: 策略函數
            **kwargs: 策略參數

        Returns:
            (進場信號, 出場信號)
        """
        try:
            # 執行策略函數
            entries, exits = strategy_func(self.data, **kwargs)

            # 信號驗證
            if not isinstance(entries, pd.DataFrame) or not isinstance(exits, pd.DataFrame):
                raise TypeError("策略函數必須返回(entries, exits)的DataFrame元組")

            # 信號優化
            entries, exits = self._optimize_signals(entries, exits)

            logger.info(f"生成信號: 進場{entries.sum().sum()}個, 出場{exits.sum().sum()}個")

            return entries, exits

        except Exception as e:
            logger.error(f"生成信號失敗: {e}")
            raise

    def _optimize_signals(self, entries: pd.DataFrame, exits: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """優化交易信號"""
        # 移除重複信號
        entries = entries & (~entries.shift(1).fillna(False))
        exits = exits & (~exits.shift(1).fillna(False))

        # 確保出場在進場之後
        for col in entries.columns:
            entry_dates = entries[col][entries[col]].index
            exit_dates = exits[col][exits[col]].index

            for entry_date in entry_dates:
                # 找到下一個出場日期
                future_exits = exit_dates[exit_dates > entry_date]
                if len(future_exits) > 0:
                    exits[col].loc[:future_exits[0]] = False

        return entries, exits

    def run_backtest(
        self,
        entries: pd.DataFrame,
        exits: pd.DataFrame,
        **portfolio_kwargs
    ) -> Dict[str, Any]:
        """
        執行回測

        Args:
            entries: 進場信號
            exits: 出場信號
            **portfolio_kwargs: Portfolio額外參數

        Returns:
            回測結果字典
        """
        try:
            start_time = time.time()

            # 創建投資組合
            portfolio_kwargs = {
                'init_cash': self.config.init_capital,
                'cash_sharing': self.config.cash_sharing,
                'call_seq': self.config.call_seq,
                'fees': self.config.fees,
                'slippage': self.config.slippage,
                'freq': self.config.freq,
                'segment_reps': self.config.segment_reps,
                **portfolio_kwargs
            }

            self.portfolio = vbt.Portfolio.from_signals(
                self.data.close,
                entries,
                exits,
                **portfolio_kwargs
            )

            # 計算結果
            self.results = self._calculate_results()
            self.results['execution_time'] = time.time() - start_time

            logger.info(f"回測完成，耗時: {self.results['execution_time']:.2f}秒")

            return self.results

        except Exception as e:
            logger.error(f"回測執行失敗: {e}")
            raise

    def _calculate_results(self) -> Dict[str, Any]:
        """計算回測結果指標"""
        if self.portfolio is None:
            raise ValueError("必須先運行回測")

        results = {}

        # 基礎指標
        results['total_return'] = float(self.portfolio.total_return())
        results['annualized_return'] = float(self.portfolio.annualized_return())
        results['sharpe_ratio'] = float(self.portfolio.sharpe_ratio())
        results['sortino_ratio'] = float(self.portfolio.sortino_ratio())
        results['max_drawdown'] = float(self.portfolio.max_drawdown())
        results['calmar_ratio'] = float(self.portfolio.calmar_ratio())

        # 交易統計
        results['total_trades'] = int(len(self.portfolio.trades))
        results['win_rate'] = float(self.portfolio.trades.win_rate())
        results['profit_factor'] = float(self.portfolio.trades.profit_factor())
        results['avg_win'] = float(self.portfolio.trades.wins.mean() if len(self.portfolio.trades.wins) > 0 else 0)
        results['avg_loss'] = float(self.portfolio.trades.losses.mean() if len(self.portfolio.trades.losses) > 0 else 0)

        # 風險指標
        results['volatility'] = float(self.portfolio.annualized_volatility())

        # 時間序列數據
        results['equity_curve'] = self.portfolio.value().to_dict()
        results['returns'] = self.portfolio.returns().to_dict()

        # 交易記錄
        if len(self.portfolio.trades) > 0:
            results['trades'] = self.portfolio.trades.records_readable.to_dict('records')
        else:
            results['trades'] = []

        # 持倉信息
        results['positions'] = self.portfolio.positions.to_dict()

        # 詳細統計
        results['stats'] = self.portfolio.stats().to_dict()

        return results

    def optimize_parameters(
        self,
        strategy_func: callable,
        param_ranges: Dict[str, List[Any]],
        optimization_metric: str = 'sharpe_ratio',
        **kwargs
    ) -> Dict[str, Any]:
        """
        參數優化

        Args:
            strategy_func: 策略函數
            param_ranges: 參數範圍字典
            optimization_metric: 優化目標指標
            **kwargs: 其他參數

        Returns:
            優化結果
        """
        try:
            from itertools import product

            # 生成參數組合
            param_names = list(param_ranges.keys())
            param_values = list(param_ranges.values())
            param_combinations = list(product(*param_values))

            logger.info(f"開始參數優化: {len(param_combinations)}個組合")

            best_result = None
            best_score = float('-inf')
            best_params = None

            for combination in param_combinations:
                param_dict = dict(zip(param_names, combination))

                try:
                    # 生成信號
                    entries, exits = self.prepare_signals(strategy_func, **param_dict)

                    # 運行回測
                    result = self.run_backtest(entries, exits)

                    # 評分
                    score = result.get(optimization_metric, 0)

                    if score > best_score:
                        best_score = score
                        best_result = result
                        best_params = param_dict

                except Exception as e:
                    logger.warning(f"參數組合失敗 {param_dict}: {e}")
                    continue

            logger.info(f"優化完成，最佳參數: {best_params}, 最佳{optimization_metric}: {best_score}")

            return {
                'best_params': best_params,
                'best_result': best_result,
                'best_score': best_score,
                'optimization_metric': optimization_metric
            }

        except Exception as e:
            logger.error(f"參數優化失敗: {e}")
            raise

    @staticmethod
    def parallel_backtest_worker(
        task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        並行回測工作函數

        Args:
            task_data: 任務數據

        Returns:
            回測結果
        """
        try:
            # 解包任務
            task_id = task_data['task_id']
            data = task_data['data']
            config = VectorBTConfig(**task_data['config'])
            strategy_func = task_data['strategy_func']
            strategy_params = task_data['strategy_params']

            # 創建適配器
            adapter = VectorBTAdapter(config)

            # 如果data是字節，需要反序列化
            if isinstance(data, bytes):
                data = pickle.loads(data)

            # 加載數據
            adapter.load_data(data)

            # 生成信號
            entries, exits = adapter.prepare_signals(strategy_func, **strategy_params)

            # 運行回測
            result = adapter.run_backtest(entries, exits)

            # 添加任務信息
            result['task_id'] = task_id
            result['status'] = 'completed'

            return result

        except Exception as e:
            logger.error(f"並行回測失敗 {task_data.get('task_id', 'unknown')}: {e}")
            return {
                'task_id': task_data.get('task_id', 'unknown'),
                'status': 'failed',
                'error': str(e),
                'execution_time': 0
            }
```

### 1.2 向量化策略庫

```python
# src/backtest/vectorbt_strategies.py
"""
VectorBT向量化策略庫
預置常用技術指標和策略模板
"""

import vectorbt as vbt
import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any, Optional
import talib

class VectorBTStrategies:
    """向量化策略集合"""

    @staticmethod
    def moving_average_crossover(
        data: vbt.Data,
        fast_window: int = 20,
        slow_window: int = 50,
        signal_threshold: float = 0
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        移動平均線交叉策略

        Args:
            data: 價格數據
            fast_window: 快線窗口
            slow_window: 慢線窗口
            signal_threshold: 信號閾值

        Returns:
            (進場信號, 出場信號)
        """
        # 計算移動平均線
        fast_ma = vbt.MA.run(data.close, window=fast_window)
        slow_ma = vbt.MA.run(data.close, window=slow_window)

        # 計算交叉信號
        if signal_threshold > 0:
            # 帶閾值的交叉
            ma_diff = (fast_ma.ma - slow_ma.ma) / slow_ma.ma
            entries = ma_diff > signal_threshold
            exits = ma_diff < -signal_threshold
        else:
            # 普通交叉
            entries = fast_ma.ma_crossed_above(slow_ma.ma)
            exits = fast_ma.ma_crossed_below(slow_ma.ma)

        return entries, exits

    @staticmethod
    def rsi_strategy(
        data: vbt.Data,
        rsi_window: int = 14,
        oversold: float = 30,
        overbought: float = 70,
        exit_oversold: float = 50,
        exit_overbought: float = 50
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        RSI策略

        Args:
            data: 價格數據
            rsi_window: RSI計算窗口
            oversold: 超賣線
            overbought: 超買線
            exit_oversold: 超賣反彈線
            exit_overbought: 超買回落線

        Returns:
            (進場信號, 出場信號)
        """
        # 計算RSI
        rsi = vbt.RSI.run(data.close, window=rsi_window)

        # 生成信號
        entries = rsi.rsi_crossed_below(oversold)  # RSI跌破超賣線
        exits = rsi.rsi_crossed_above(exit_oversold)  # RSI反彈超過退出線

        return entries, exits

    @staticmethod
    def bollinger_bands_strategy(
        data: vbt.Data,
        window: int = 20,
        num_std: float = 2.0,
        use_mean_reversion: bool = True
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        布林帶策略

        Args:
            data: 價格數據
            window: 窗口大小
            num_std: 標準差倍數
            use_mean_reversion: 是否使用均值回歸

        Returns:
            (進場信號, 出場信號)
        """
        # 計算布林帶
        bb = vbt.BBANDS.run(data.close, window=window, num_std=num_std)

        if use_mean_reversion:
            # 均值回歸策略
            entries = data.close_crossed_below(bb.lower)  # 價格跌破下軌
            exits = data.close_crossed_above(bb.middle)  # 價格回到中軌
        else:
            # 趨勢跟蹤策略
            entries = data.close_crossed_above(bb.upper)  # 價格突破上軌
            exits = data.close_crossed_below(bb.middle)  # 價格回落到中軌

        return entries, exits

    @staticmethod
    def macd_strategy(
        data: vbt.Data,
        fast_window: int = 12,
        slow_window: int = 26,
        signal_window: int = 9,
        cross_threshold: float = 0
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        MACD策略

        Args:
            data: 價格數據
            fast_window: 快線窗口
            slow_window: 慢線窗口
            signal_window: 信號線窗口
            cross_threshold: 交叉閾值

        Returns:
            (進場信號, 出場信號)
        """
        # 計算MACD
        macd = vbt.MACD.run(
            data.close,
            fast_window=fast_window,
            slow_window=slow_window,
            signal_window=signal_window
        )

        # 生成信號
        if cross_threshold > 0:
            # 帶閾值的交叉
            macd_diff = macd.macd - macd.signal
            entries = macd_diff > cross_threshold
            exits = macd_diff < -cross_threshold
        else:
            # 普通交叉
            entries = macd.macd_crossed_above(macd.signal)
            exits = macd.macd_crossed_below(macd.signal)

        return entries, exits

    @staticmethod
    def stochastic_oscillator_strategy(
        data: vbt.Data,
        k_window: int = 14,
        d_window: int = 3,
        oversold: float = 20,
        overbought: float = 80
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        隨機振盪器策略

        Args:
            data: 價格數據
            k_window: %K窗口
            d_window: %D窗口
            oversold: 超賣線
            overbought: 超買線

        Returns:
            (進場信號, 出場信號)
        """
        # 計算隨機振盪器
        stoch = vbt.STOCH.run(
            data.high,
            data.low,
            data.close,
            k_window=k_window,
            d_window=d_window
        )

        # 生成信號
        entries = (stoch.percent_k < oversold) & (stoch.percent_k.shift(1) >= oversold)
        exits = (stoch.percent_k > overbought) & (stoch.percent_k.shift(1) <= overbought)

        return entries, exits

    @staticmethod
    def dual_thrust_strategy(
        data: vbt.Data,
        lookback_period: int = 5,
        k1: float = 0.5,
        k2: float = 0.5
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Dual Thrust策略

        Args:
            data: 價格數據
            lookback_period: 回看期
            k1: 上軌系數
            k2: 下軌系數

        Returns:
            (進場信號, 出場信號)
        """
        # 計算Dual Thrust指標
        hh = data.high.rolling(lookback_period).max()
        ll = data.low.rolling(lookback_period).min()
        hc = data.high.shift(1).rolling(lookback_period).max()
        lc = data.low.shift(1).rolling(lookback_period).min()

        # 計算上下軌
        range_max = (hh - lc).abs()
        range_min = (hc - ll).abs()
        trigger_range = range_max.combine(range_min, max)

        upper_bound = data.open.shift(1) + k1 * trigger_range
        lower_bound = data.open.shift(1) - k2 * trigger_range

        # 生成信號
        entries = data.high > upper_bound
        exits = data.low < lower_bound

        return entries, exits

    @staticmethod
    def pair_trading_strategy(
        data_a: pd.Series,
        data_b: pd.Series,
        lookback: int = 20,
        z_entry: float = 2.0,
        z_exit: float = 0.5
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        配對交易策略

        Args:
            data_a: 資產A價格
            data_b: 資產B價格
            lookback: 回看期
            z_entry: 進場Z分數
            z_exit: 出場Z分數

        Returns:
            (進場信號, 出場信號)
        """
        # 計算價格比率
        ratio = data_a / data_b

        # 計算移動平均和標準差
        ratio_mean = ratio.rolling(lookback).mean()
        ratio_std = ratio.rolling(lookback).std()
        z_score = (ratio - ratio_mean) / ratio_std

        # 生成信號
        long_signal = z_score < -z_entry  # 資產A相對被低估
        short_signal = z_score > z_entry  # 資產A相對被高估

        # 出場信號
        exit_long = z_score > -z_exit
        exit_short = z_score < z_exit

        # 創建信號DataFrame
        entries = pd.DataFrame({
            'asset_a': long_signal,
            'asset_b': short_signal
        })

        exits = pd.DataFrame({
            'asset_a': exit_long | z_score > z_exit,
            'asset_b': exit_short | z_score < -z_exit
        })

        return entries, exits

    @staticmethod
    def multi_indicator_strategy(
        data: vbt.Data,
        ma_config: Dict[str, int] = None,
        rsi_config: Dict[str, float] = None,
        bb_config: Dict[str, Any] = None
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        多指標組合策略

        Args:
            data: 價格數據
            ma_config: 移動平均線配置
            rsi_config: RSI配置
            bb_config: 布林帶配置

        Returns:
            (進場信號, 出場信號)
        """
        entries = pd.DataFrame(False, index=data.index, columns=data.close.columns)
        exits = pd.DataFrame(False, index=data.index, columns=data.close.columns)

        # 移動平均線
        if ma_config:
            ma_entries, ma_exits = VectorBTStrategies.moving_average_crossover(
                data, **ma_config
            )
            entries |= ma_entries
            exits |= ma_exits

        # RSI
        if rsi_config:
            rsi_entries, rsi_exits = VectorBTStrategies.rsi_strategy(
                data, **rsi_config
            )
            entries &= rsi_entries
            exits |= rsi_exits

        # 布林帶
        if bb_config:
            bb_entries, bb_exits = VectorBTStrategies.bollinger_bands_strategy(
                data, **bb_config
            )
            entries |= bb_entries
            exits |= bb_exits

        return entries, exits
```

### 1.3 並行處理增強

```python
# src/backtest/vectorbt_parallel.py
"""
VectorBT並行處理模塊
提供高性能並行回測能力
"""

import asyncio
import multiprocessing as mp
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ProcessPoolExecutor, as_completed
import time
import pickle
from functools import partial
import logging
from pathlib import Path

from .vectorbt_adapter import VectorBTAdapter, VectorBTConfig

logger = logging.getLogger(__name__)

class VectorBTParallel:
    """VectorBT並行處理器"""

    def __init__(
        self,
        max_workers: Optional[int] = None,
        chunk_size: Optional[int] = None,
        use_gpu: bool = False
    ):
        """
        初始化並行處理器

        Args:
            max_workers: 最大工作進程數
            chunk_size: 數據塊大小
            use_gpu: 是否使用GPU
        """
        self.max_workers = max_workers or min(32, (mp.cpu_count() or 1) + 4)
        self.chunk_size = chunk_size
        self.use_gpu = use_gpu

        # 初始化進程池
        self.executor = ProcessPoolExecutor(max_workers=self.max_workers)

        logger.info(f"並行處理器初始化: {self.max_workers}個工作進程")

    def parallel_parameter_optimization(
        self,
        data: pd.DataFrame,
        strategy_func: callable,
        param_combinations: List[Dict[str, Any]],
        config: Optional[VectorBTConfig] = None
    ) -> List[Dict[str, Any]]:
        """
        並行參數優化

        Args:
            data: 價格數據
            strategy_func: 策略函數
            param_combinations: 參數組合列表
            config: VectorBT配置

        Returns:
            優化結果列表
        """
        try:
            start_time = time.time()

            # 準備任務
            tasks = []
            for i, params in enumerate(param_combinations):
                task_data = {
                    'task_id': f'opt_{i}',
                    'data': pickle.dumps(data) if len(data) > 10000 else data,
                    'config': config.__dict__ if config else VectorBTConfig().__dict__,
                    'strategy_func': strategy_func,
                    'strategy_params': params
                }
                tasks.append(task_data)

            # 提交任務
            futures = []
            for task in tasks:
                future = self.executor.submit(
                    VectorBTAdapter.parallel_backtest_worker,
                    task
                )
                futures.append(future)

            # 收集結果
            results = []
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=300)  # 5分鐘超時
                    results.append(result)
                except Exception as e:
                    logger.error(f"任務執行失敗: {e}")
                    continue

            # 排序結果
            results.sort(key=lambda x: x.get('sharpe_ratio', 0), reverse=True)

            logger.info(f"並行優化完成: {len(results)}/{len(tasks)}個成功, 耗時: {time.time()-start_time:.2f}秒")

            return results

        except Exception as e:
            logger.error(f"並行優化失敗: {e}")
            raise

    def parallel_cross_validation(
        self,
        data: pd.DataFrame,
        strategy_func: callable,
        strategy_params: Dict[str, Any],
        n_splits: int = 5,
        config: Optional[VectorBTConfig] = None
    ) -> Dict[str, Any]:
        """
        並行交叉驗證

        Args:
            data: 價格數據
            strategy_func: 策略函數
            strategy_params: 策略參數
            n_splits: 分割數
            config: VectorBT配置

        Returns:
            交叉驗證結果
        """
        try:
            # 時間序列分割
            split_size = len(data) // n_splits
            splits = []

            for i in range(n_splits):
                start_idx = i * split_size
                end_idx = (i + 1) * split_size if i < n_splits - 1 else len(data)

                train_data = data.iloc[:start_idx + split_size//2]
                test_data = data.iloc[start_idx + split_size//2:end_idx]

                splits.append({
                    'train': train_data,
                    'test': test_data
                })

            # 準備任務
            tasks = []
            for i, split in enumerate(splits):
                task_data = {
                    'task_id': f'cv_{i}',
                    'data': pickle.dumps(split['train']) if len(split['train']) > 10000 else split['train'],
                    'config': config.__dict__ if config else VectorBTConfig().__dict__,
                    'strategy_func': strategy_func,
                    'strategy_params': strategy_params,
                    'test_data': split['test']
                }
                tasks.append(task_data)

            # 並行執行
            futures = []
            for task in tasks:
                future = self.executor.submit(
                    self._cv_worker,
                    task
                )
                futures.append(future)

            # 收集結果
            results = []
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=300)
                    results.append(result)
                except Exception as e:
                    logger.error(f"CV任務失敗: {e}")
                    continue

            # 聚合結果
            aggregated = self._aggregate_cv_results(results)

            logger.info(f"交叉驗證完成: {len(results)}/{n_splits}折")

            return aggregated

        except Exception as e:
            logger.error(f"交叉驗證失敗: {e}")
            raise

    def _cv_worker(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """交叉驗證工作函數"""
        try:
            task_id = task_data['task_id']
            train_data = pickle.loads(task_data['data']) if isinstance(task_data['data'], bytes) else task_data['data']
            test_data = task_data['test_data']
            config = VectorBTConfig(**task_data['config'])
            strategy_func = task_data['strategy_func']
            strategy_params = task_data['strategy_params']

            # 訓練集回測
            adapter = VectorBTAdapter(config)
            adapter.load_data(train_data)
            entries, exits = adapter.prepare_signals(strategy_func, **strategy_params)
            train_result = adapter.run_backtest(entries, exits)

            # 測試集回測
            adapter_test = VectorBTAdapter(config)
            adapter_test.load_data(test_data)
            entries_test, exits_test = adapter_test.prepare_signals(strategy_func, **strategy_params)
            test_result = adapter_test.run_backtest(entries_test, exits_test)

            return {
                'task_id': task_id,
                'train_result': train_result,
                'test_result': test_result,
                'status': 'completed'
            }

        except Exception as e:
            return {
                'task_id': task_data.get('task_id', 'unknown'),
                'status': 'failed',
                'error': str(e)
            }

    def _aggregate_cv_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """聚合交叉驗證結果"""
        if not results:
            return {}

        # 提取指標
        metrics = ['total_return', 'sharpe_ratio', 'max_drawdown', 'win_rate']

        train_metrics = {metric: [] for metric in metrics}
        test_metrics = {metric: [] for metric in metrics}

        for result in results:
            if result['status'] == 'completed':
                for metric in metrics:
                    train_metrics[metric].append(result['train_result'].get(metric, 0))
                    test_metrics[metric].append(result['test_result'].get(metric, 0))

        # 計算統計
        aggregated = {}
        for metric in metrics:
            aggregated[f'train_{metric}_mean'] = np.mean(train_metrics[metric])
            aggregated[f'train_{metric}_std'] = np.std(train_metrics[metric])
            aggregated[f'test_{metric}_mean'] = np.mean(test_metrics[metric])
            aggregated[f'test_{metric}_std'] = np.std(test_metrics[metric])

        # 計算過擬合指標
        for metric in ['sharpe_ratio', 'total_return']:
            train_mean = aggregated[f'train_{metric}_mean']
            test_mean = aggregated[f'test_{metric}_mean']
            overfitting = (train_mean - test_mean) / abs(train_mean) if train_mean != 0 else 0
            aggregated[f'{metric}_overfitting'] = overfitting

        return aggregated

    async def parallel_monte_carlo(
        self,
        data: pd.DataFrame,
        strategy_func: callable,
        strategy_params: Dict[str, Any],
        n_simulations: int = 1000,
        config: Optional[VectorBTConfig] = None
    ) -> Dict[str, Any]:
        """
        並行蒙地卡羅模擬

        Args:
            data: 價格數據
            strategy_func: 策略函數
            strategy_params: 策略參數
            n_simulations: 模擬次數
            config: VectorBT配置

        Returns:
            蒙地卡羅模擬結果
        """
        try:
            # 計算回報率
            returns = data.pct_change().dropna()

            # 分批模擬
            batch_size = min(100, n_simulations // self.max_workers)
            n_batches = (n_simulations + batch_size - 1) // batch_size

            # 準備任務
            tasks = []
            for i in range(n_batches):
                start_sim = i * batch_size
                end_sim = min((i + 1) * batch_size, n_simulations)

                task_data = {
                    'task_id': f'mc_{i}',
                    'returns': returns,
                    'start_sim': start_sim,
                    'end_sim': end_sim,
                    'config': config.__dict__ if config else VectorBTConfig().__dict__,
                    'strategy_func': strategy_func,
                    'strategy_params': strategy_params
                }
                tasks.append(task_data)

            # 並行執行
            loop = asyncio.get_event_loop()
            futures = []

            for task in tasks:
                future = loop.run_in_executor(
                    self.executor,
                    self._monte_carlo_worker,
                    task
                )
                futures.append(future)

            # 收集結果
            results = await asyncio.gather(*futures)

            # 聚合結果
            all_returns = []
            for result in results:
                all_returns.extend(result['returns'])

            # 計算統計
            final_result = {
                'n_simulations': len(all_returns),
                'mean': np.mean(all_returns),
                'std': np.std(all_returns),
                'min': np.min(all_returns),
                'max': np.max(all_returns),
                'percentile_5': np.percentile(all_returns, 5),
                'percentile_95': np.percentile(all_returns, 95),
                'var_95': np.percentile(all_returns, 5),
                'var_99': np.percentile(all_returns, 1)
            }

            logger.info(f"蒙地卡羅模擬完成: {len(all_returns)}個樣本")

            return final_result

        except Exception as e:
            logger.error(f"蒙地卡羅模擬失敗: {e}")
            raise

    def _monte_carlo_worker(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """蒙地卡羅工作函數"""
        try:
            task_id = task_data['task_id']
            returns = task_data['returns']
            start_sim = task_data['start_sim']
            end_sim = task_data['end_sim']
            config = VectorBTConfig(**task_data['config'])
            strategy_func = task_data['strategy_func']
            strategy_params = task_data['strategy_params']

            sim_returns = []

            for i in range(start_sim, end_sim):
                # 隨機重採樣
                sim_returns_sample = returns.sample(frac=1, replace=True).reset_index(drop=True)

                # 生成價格路徑
                initial_price = 100
                prices = [initial_price]

                for ret in sim_returns_sample.iloc[:, 0]:
                    prices.append(prices[-1] * (1 + ret))

                # 創建模擬數據
                sim_data = pd.DataFrame({
                    'open': prices[1:],
                    'high': prices[1:],
                    'low': prices[1:],
                    'close': prices[1:]
                }, index=returns.index)

                # 運行回測
                adapter = VectorBTAdapter(config)
                adapter.load_data(sim_data)
                entries, exits = adapter.prepare_signals(strategy_func, **strategy_params)
                result = adapter.run_backtest(entries, exits)

                sim_returns.append(result.get('total_return', 0))

            return {
                'task_id': task_id,
                'returns': sim_returns
            }

        except Exception as e:
            logger.error(f"蒙地卡羅任務失敗 {task_id}: {e}")
            return {
                'task_id': task_id,
                'returns': []
            }

    def shutdown(self):
        """關閉並行處理器"""
        self.executor.shutdown(wait=True)
        logger.info("並行處理器已關閉")
```

### 1.4 性能優化工具

```python
# src/backtest/vectorbt_optimizer.py
"""
VectorBT性能優化工具
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import gc
import psutil
import time
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class VectorBTOptimizer:
    """VectorBT性能優化器"""

    @staticmethod
    def optimize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """
        優化DataFrame內存使用

        Args:
            df: 輸入DataFrame

        Returns:
            優化後的DataFrame
        """
        memory_before = df.memory_usage(deep=True).sum() / 1024 / 1024  # MB

        # 優化數值類型
        for col in df.select_dtypes(include=['int64']).columns:
            df[col] = pd.to_numeric(df[col], downcast='integer')

        for col in df.select_dtypes(include=['float64']).columns:
            df[col] = df[col].astype('float32')

        # 優化字符串類型
        for col in df.select_dtypes(include=['object']).columns:
            num_unique_values = len(df[col].unique())
            num_total_values = len(df[col])

            if num_unique_values / num_total_values < 0.5:
                df[col] = df[col].astype('category')

        memory_after = df.memory_usage(deep=True).sum() / 1024 / 1024  # MB
        memory_saved = memory_before - memory_after

        if memory_saved > 0:
            logger.info(f"內存優化: 節省 {memory_saved:.2f} MB ({memory_saved/memory_before*100:.1f}%)")

        return df

    @staticmethod
    def chunk_data(
        data: pd.DataFrame,
        chunk_size: int,
        overlap: int = 0
    ) -> List[pd.DataFrame]:
        """
        將數據分塊

        Args:
            data: 輸入數據
            chunk_size: 塊大小
            overlap: 重疊大小

        Returns:
            數據塊列表
        """
        chunks = []
        start = 0

        while start < len(data):
            end = min(start + chunk_size, len(data))
            chunks.append(data.iloc[start:end])

            if end >= len(data):
                break

            start = end - overlap

        return chunks

    @staticmethod
    def prefetch_data(data: pd.DataFrame, columns: List[str]) -> Dict[str, Any]:
        """
        預取數據到內存

        Args:
            data: 輸入數據
            columns: 需要預取的列

        Returns:
            預取的數據字典
        """
        prefetched = {}

        for col in columns:
            if col in data.columns:
                # 將數據轉換為numpy數組以提高性能
                prefetched[col] = data[col].values

        return prefetched

    @staticmethod
    def cache_results(
        func: callable,
        cache_key: str,
        cache_dir: str = "./cache"
    ):
        """
        結果緩存裝飾器

        Args:
            func: 要緩存的函數
            cache_key: 緩存鍵
            cache_dir: 緩存目錄
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            import os
            import pickle
            from pathlib import Path

            cache_file = Path(cache_dir) / f"{cache_key}.pkl"

            # 檢查緩存
            if cache_file.exists():
                try:
                    with open(cache_file, 'rb') as f:
                        result = pickle.load(f)
                    logger.info(f"從緩存加載: {cache_key}")
                    return result
                except Exception as e:
                    logger.warning(f"加載緩存失敗: {e}")

            # 執行函數
            result = func(*args, **kwargs)

            # 保存到緩存
            try:
                cache_file.parent.mkdir(parents=True, exist_ok=True)
                with open(cache_file, 'wb') as f:
                    pickle.dump(result, f)
                logger.info(f"保存到緩存: {cache_key}")
            except Exception as e:
                logger.warning(f"保存緩存失敗: {e}")

            return result

        return wrapper

    @staticmethod
    def monitor_performance(func: callable) -> callable:
        """
        性能監控裝飾器

        Args:
            func: 要監控的函數

        Returns:
            裝飾後的函數
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 開始監控
            start_time = time.time()
            process = psutil.Process()
            start_memory = process.memory_info().rss / 1024 / 1024  # MB

            try:
                # 執行函數
                result = func(*args, **kwargs)

                # 記錄成功
                success = True
                error = None

            except Exception as e:
                result = None
                success = False
                error = str(e)
                raise

            finally:
                # 結束監控
                end_time = time.time()
                end_memory = process.memory_info().rss / 1024 / 1024  # MB

                # 計算指標
                duration = end_time - start_time
                memory_delta = end_memory - start_memory

                # 記錄指標
                metrics = {
                    'function': func.__name__,
                    'duration': duration,
                    'memory_delta': memory_delta,
                    'peak_memory': end_memory,
                    'success': success,
                    'error': error
                }

                logger.info(f"性能指標 {func.__name__}: {duration:.2f}秒, {memory_delta:.1f}MB")

            return result

        return wrapper

    @staticmethod
    def memory_efficient_backtest(
        data: pd.DataFrame,
        strategy_func: callable,
        chunk_size: int = 10000,
        **kwargs
    ) -> Dict[str, Any]:
        """
        內存高效的回測實現

        Args:
            data: 價格數據
            strategy_func: 策略函數
            chunk_size: 數據塊大小
            **kwargs: 其他參數

        Returns:
            回測結果
        """
        from .vectorbt_adapter import VectorBTAdapter

        # 分塊處理
        chunks = VectorBTOptimizer.chunk_data(data, chunk_size, overlap=100)

        results = []
        for i, chunk in enumerate(chunks):
            logger.info(f"處理塊 {i+1}/{len(chunks)}")

            # 優化數據
            chunk = VectorBTOptimizer.optimize_dataframe(chunk)

            # 執行回測
            adapter = VectorBTAdapter()
            adapter.load_data(chunk)
            entries, exits = adapter.prepare_signals(strategy_func, **kwargs)
            chunk_result = adapter.run_backtest(entries, exits)

            results.append(chunk_result)

            # 清理內存
            del chunk, adapter, chunk_result
            gc.collect()

        # 聚合結果
        final_result = VectorBTOptimizer._aggregate_chunk_results(results)

        return final_result

    @staticmethod
    def _aggregate_chunk_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """聚合分塊回測結果"""
        if not results:
            return {}

        # 提取指標
        metrics = [
            'total_return', 'sharpe_ratio', 'max_drawdown',
            'win_rate', 'profit_factor', 'volatility'
        ]

        aggregated = {}

        # 計算加權平均
        for metric in metrics:
            values = [r.get(metric, 0) for r in results]
            weights = [len(r.get('returns', {})) for r in results]

            if sum(weights) > 0:
                aggregated[metric] = np.average(values, weights=weights)
            else:
                aggregated[metric] = np.mean(values)

        # 合併時間序列
        all_returns = {}
        for result in results:
            returns = result.get('returns', {})
            all_returns.update(returns)

        aggregated['returns'] = all_returns

        # 重新計算總體指標
        if all_returns:
            returns_series = pd.Series(all_returns)
            aggregated['volatility'] = returns_series.std() * np.sqrt(252)
            aggregated['sharpe_ratio'] = (returns_series.mean() * 252) / aggregated['volatility']

        return aggregated
```

## 2. 使用示例

### 2.1 基礎回測示例

```python
# examples/basic_backtest.py
"""
基礎VectorBT回測示例
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.backtest.vectorbt_adapter import VectorBTAdapter, VectorBTConfig
from src.backtest.vectorbt_strategies import VectorBTStrategies

# 生成示例數據
def generate_sample_data(symbols=['AAPL', 'GOOGL', 'MSFT'], days=252):
    """生成示例價格數據"""
    dates = pd.date_range('2023-01-01', periods=days, freq='D')
    np.random.seed(42)

    data = {}
    for symbol in symbols:
        # 生成隨機價格路徑
        returns = np.random.normal(0.001, 0.02, days)
        prices = [100]

        for ret in returns:
            prices.append(prices[-1] * (1 + ret))

        # 生成OHLCV數據
        df = pd.DataFrame({
            'open': prices[:-1],
            'high': [p * (1 + np.random.uniform(0, 0.02)) for p in prices[:-1]],
            'low': [p * (1 - np.random.uniform(0, 0.02)) for p in prices[:-1]],
            'close': prices[1:],
            'volume': np.random.randint(1000000, 10000000, days)
        }, index=dates)

        data[symbol] = df

    # 合併多個資產
    multi_data = pd.concat(data, axis=1)
    multi_data.columns = pd.MultiIndex.from_product([symbols, ['open', 'high', 'low', 'close', 'volume']])

    return multi_data

# 主程序
def main():
    # 生成數據
    data = generate_sample_data()

    # 創建配置
    config = VectorBTConfig(
        init_capital=1000000,
        fees=0.001,
        slippage=0.0005
    )

    # 創建適配器
    adapter = VectorBTAdapter(config)
    adapter.load_data(data)

    # 選擇策略
    strategy_func = VectorBTStrategies.moving_average_crossover
    strategy_params = {
        'fast_window': 20,
        'slow_window': 50
    }

    # 生成信號
    entries, exits = adapter.prepare_signals(strategy_func, **strategy_params)

    # 運行回測
    result = adapter.run_backtest(entries, exits)

    # 打印結果
    print("\n回測結果:")
    print(f"總收益率: {result['total_return']:.2%}")
    print(f"年化收益率: {result['annualized_return']:.2%}")
    print(f"夏普比率: {result['sharpe_ratio']:.2f}")
    print(f"最大回撤: {result['max_drawdown']:.2%}")
    print(f"勝率: {result['win_rate']:.2%}")
    print(f"總交易次數: {result['total_trades']}")

    # 可視化（如果需要）
    try:
        import matplotlib.pyplot as plt

        # 提取資產曲線
        equity_curve = pd.DataFrame(result['equity_curve'])

        # 繪製資產曲線
        plt.figure(figsize=(12, 6))
        for symbol in equity_curve.columns:
            plt.plot(equity_curve.index, equity_curve[symbol], label=symbol)

        plt.title('資產曲線')
        plt.xlabel('日期')
        plt.ylabel('資產價值')
        plt.legend()
        plt.grid(True)
        plt.show()

    except ImportError:
        print("\nmatplotlib未安裝，跳過可視化")

if __name__ == "__main__":
    main()
```

### 2.2 參數優化示例

```python
# examples/parameter_optimization.py
"""
VectorBT參數優化示例
"""

import pandas as pd
import numpy as np
from itertools import product

from src.backtest.vectorbt_adapter import VectorBTAdapter, VectorBTConfig
from src.backtest.vectorbt_strategies import VectorBTStrategies
from src.backtest.vectorbt_parallel import VectorBTParallel

def main():
    # 加載數據（使用基礎示例中的函數）
    from examples.basic_backtest import generate_sample_data
    data = generate_sample_data(['AAPL'], days=252*2)  # 2年數據

    # 定義參數範圍
    param_ranges = {
        'fast_window': [5, 10, 15, 20, 25],
        'slow_window': [30, 40, 50, 60, 70],
        'signal_threshold': [0, 0.01, 0.02]
    }

    # 生成所有參數組合
    param_names = list(param_ranges.keys())
    param_values = list(param_ranges.values())
    param_combinations = list(product(*param_values))

    # 過濾無效組合（快線必須小於慢線）
    valid_combinations = [
        combo for combo in param_combinations
        if combo[0] < combo[1]
    ]

    print(f"有效參數組合數: {len(valid_combinations)}")

    # 創建並行處理器
    parallel = VectorBTParallel(max_workers=4)

    # 配置
    config = VectorBTConfig(init_capital=1000000)

    # 並行優化
    results = parallel.parallel_parameter_optimization(
        data=data,
        strategy_func=VectorBTStrategies.moving_average_crossover,
        param_combinations=[
            dict(zip(param_names, combo)) for combo in valid_combinations[:20]  # 限制數量以便演示
        ],
        config=config
    )

    # 打印最佳結果
    print("\n前5個最佳參數組合:")
    for i, result in enumerate(results[:5]):
        params = result.get('strategy_params', {})
        print(f"\n{i+1}. 參數: {params}")
        print(f"   夏普比率: {result.get('sharpe_ratio', 0):.3f}")
        print(f"   總收益率: {result.get('total_return', 0):.2%}")
        print(f"   最大回撤: {result.get('max_drawdown', 0):.2%}")

    # 清理
    parallel.shutdown()

if __name__ == "__main__":
    main()
```

### 2.3 蒙地卡羅模擬示例

```python
# examples/monte_carlo.py
"""
VectorBT蒙地卡羅模擬示例
"""

import asyncio
import pandas as pd
import numpy as np

from src.backtest.vectorbt_adapter import VectorBTAdapter, VectorBTConfig
from src.backtest.vectorbt_strategies import VectorBTStrategies
from src.backtest.vectorbt_parallel import VectorBTParallel

async def main():
    # 加載數據
    from examples.basic_backtest import generate_sample_data
    data = generate_sample_data(['AAPL'], days=252)

    # 配置和策略
    config = VectorBTConfig(init_capital=1000000)
    strategy_params = {
        'fast_window': 20,
        'slow_window': 50
    }

    # 創建並行處理器
    parallel = VectorBTParallel(max_workers=4)

    # 運行蒙地卡羅模擬
    print("開始蒙地卡羅模擬...")
    mc_result = await parallel.parallel_monte_carlo(
        data=data,
        strategy_func=VectorBTStrategies.moving_average_crossover,
        strategy_params=strategy_params,
        n_simulations=1000,
        config=config
    )

    # 打印結果
    print("\n蒙地卡羅模擬結果:")
    print(f"模擬次數: {mc_result['n_simulations']}")
    print(f"平均收益率: {mc_result['mean']:.2%}")
    print(f"收益率標準差: {mc_result['std']:.2%}")
    print(f"最好表現: {mc_result['max']:.2%}")
    print(f"最差表現: {mc_result['min']:.2%}")
    print(f"5%分位數: {mc_result['percentile_5']:.2%}")
    print(f"95%分位數: {mc_result['percentile_95']:.2%}")
    print(f"VaR 95%: {mc_result['var_95']:.2%}")
    print(f"VaR 99%: {mc_result['var_99']:.2%}")

    # 可視化分布（可選）
    try:
        import matplotlib.pyplot as plt

        # 模擬分布需要重新運行以獲取所有樣本
        print("\n生成模擬數據用於可視化...")

        # 簡化的模擬僅用於演示
        returns = np.random.normal(mc_result['mean'], mc_result['std'], 1000)

        plt.figure(figsize=(10, 6))
        plt.hist(returns, bins=50, density=True, alpha=0.7)
        plt.axvline(mc_result['percentile_5'], color='r', linestyle='--', label='5%分位')
        plt.axvline(mc_result['percentile_95'], color='g', linestyle='--', label='95%分位')
        plt.axvline(mc_result['mean'], color='b', linestyle='-', label='平均值')

        plt.title('收益率分布')
        plt.xlabel('收益率')
        plt.ylabel('密度')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.show()

    except ImportError:
        print("\nmatplotlib未安裝，跳過可視化")

    # 清理
    parallel.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

### 2.4 多資產組合策略示例

```python
# examples/portfolio_strategy.py
"""
多資產組合策略示例
"""

import pandas as pd
import numpy as np

from src.backtest.vectorbt_adapter import VectorBTAdapter, VectorBTConfig
from src.backtest.vectorbt_strategies import VectorBTStrategies

def main():
    # 生成多資產數據
    symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']
    from examples.basic_backtest import generate_sample_data
    data = generate_sample_data(symbols, days=252)

    # 配置
    config = VectorBTConfig(
        init_capital=1000000,
        fees=0.001,
        slippage=0.0005,
        cash_sharing=True  # 允許現金共享
    )

    # 創建適配器
    adapter = VectorBTAdapter(config)
    adapter.load_data(data)

    # 多指標策略
    strategy_params = {
        'ma_config': {
            'fast_window': 20,
            'slow_window': 50
        },
        'rsi_config': {
            'rsi_window': 14,
            'oversold': 30,
            'overbought': 70
        },
        'bb_config': {
            'window': 20,
            'num_std': 2.0,
            'use_mean_reversion': True
        }
    }

    # 生成信號
    entries, exits = adapter.prepare_signals(
        VectorBTStrategies.multi_indicator_strategy,
        **strategy_params
    )

    # 運行回測
    result = adapter.run_backtest(entries, exits)

    # 打印結果
    print("\n多資產組合回測結果:")
    print(f"總收益率: {result['total_return']:.2%}")
    print(f"年化收益率: {result['annualized_return']:.2%}")
    print(f"夏普比率: {result['sharpe_ratio']:.2f}")
    print(f"最大回撤: {result['max_drawdown']:.2%}")
    print(f"勝率: {result['win_rate']:.2%}")
    print(f"總交易次數: {result['total_trades']}")

    # 單獨分析每個資產
    print("\n各資產表現:")
    trades_df = pd.DataFrame(result['trades'])

    if not trades_df.empty:
        asset_performance = trades_df.groupby('Symbol')['PnL'].agg([
            'sum', 'count', 'mean'
        ]).round(2)
        asset_performance.columns = ['總盈虧', '交易次數', '平均盈虧']
        print(asset_performance)

    # 可視化
    try:
        import matplotlib.pyplot as plt

        # 資產曲線
        equity_df = pd.DataFrame(result['equity_curve'])

        plt.figure(figsize=(12, 8))

        # 子圖1: 資產曲線
        plt.subplot(2, 1, 1)
        for symbol in equity_df.columns:
            plt.plot(equity_df.index, equity_df[symbol], label=symbol)
        plt.title('各資產資產曲線')
        plt.xlabel('日期')
        plt.ylabel('資產價值')
        plt.legend()
        plt.grid(True)

        # 子圖2: 投資組合價值
        plt.subplot(2, 1, 2)
        portfolio_value = equity_df.sum(axis=1)
        plt.plot(portfolio_value.index, portfolio_value, 'b-', linewidth=2)
        plt.title('投資組合總價值')
        plt.xlabel('日期')
        plt.ylabel('組合價值')
        plt.grid(True)

        plt.tight_layout()
        plt.show()

    except ImportError:
        print("\nmatplotlib未安裝，跳過可視化")

if __name__ == "__main__":
    main()
```

## 3. 測試用例

### 3.1 單元測試

```python
# tests/test_vectorbt_adapter.py
"""
VectorBT適配器單元測試
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.backtest.vectorbt_adapter import VectorBTAdapter, VectorBTConfig
from src.backtest.vectorbt_strategies import VectorBTStrategies

@pytest.fixture
def sample_data():
    """創建測試數據"""
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    np.random.seed(42)

    data = pd.DataFrame({
        'open': 100 + np.random.randn(100).cumsum() * 0.5,
        'high': lambda x: x['open'] * (1 + np.random.rand(100) * 0.02),
        'low': lambda x: x['open'] * (1 - np.random.rand(100) * 0.02),
        'close': lambda x: x['open'] + np.random.randn(100) * 0.5,
        'volume': np.random.randint(100000, 1000000, 100)
    }, index=dates)

    return data

@pytest.fixture
def multiasset_data():
    """創建多資產測試數據"""
    symbols = ['AAPL', 'GOOGL']
    dates = pd.date_range('2023-01-01', periods=100, freq='D')

    data_dict = {}
    for symbol in symbols:
        np.random.seed(hash(symbol) % 2**32)
        prices = 100 + np.random.randn(100).cumsum() * 0.5

        df = pd.DataFrame({
            'open': prices,
            'high': prices * 1.02,
            'low': prices * 0.98,
            'close': prices + np.random.randn(100) * 0.1,
            'volume': np.random.randint(100000, 1000000, 100)
        }, index=dates)

        data_dict[symbol] = df

    # 創建多索引DataFrame
    multi_data = pd.concat(data_dict, axis=1)
    multi_data.columns = pd.MultiIndex.from_product(
        [symbols, ['open', 'high', 'low', 'close', 'volume']]
    )

    return multi_data

def test_adapter_initialization():
    """測試適配器初始化"""
    config = VectorBTConfig(init_capital=1000000)
    adapter = VectorBTAdapter(config)

    assert adapter.config.init_capital == 1000000
    assert adapter.data is None
    assert adapter.portfolio is None

def test_load_data(sample_data):
    """測試數據加載"""
    adapter = VectorBTAdapter()
    adapter.load_data(sample_data)

    assert adapter.data is not None
    assert len(adapter.data.close) == len(sample_data)

def test_load_multiasset_data(multiasset_data):
    """測試多資產數據加載"""
    adapter = VectorBTAdapter()
    adapter.load_data(multiasset_data)

    assert adapter.data is not None
    assert len(adapter.data.close.columns) == 2

def test_moving_average_strategy(sample_data):
    """測試移動平均線策略"""
    adapter = VectorBTAdapter()
    adapter.load_data(sample_data)

    entries, exits = adapter.prepare_signals(
        VectorBTStrategies.moving_average_crossover,
        fast_window=10,
        slow_window=30
    )

    assert isinstance(entries, pd.DataFrame)
    assert isinstance(exits, pd.DataFrame)
    assert len(entries) == len(sample_data)
    assert len(exits) == len(sample_data)

def test_run_backtest(sample_data):
    """測試運行回測"""
    config = VectorBTConfig(init_capital=1000000)
    adapter = VectorBTAdapter(config)
    adapter.load_data(sample_data)

    # 創建簡單信號
    entries = pd.DataFrame(False, index=sample_data.index, columns=['close'])
    exits = pd.DataFrame(False, index=sample_data.index, columns=['close'])

    entries.iloc[10] = True
    exits.iloc[20] = True

    result = adapter.run_backtest(entries, exits)

    assert 'total_return' in result
    assert 'sharpe_ratio' in result
    assert 'max_drawdown' in result
    assert isinstance(result['total_trades'], int)

def test_optimize_parameters(sample_data):
    """測試參數優化"""
    adapter = VectorBTAdapter()
    adapter.load_data(sample_data)

    param_ranges = {
        'fast_window': [5, 10, 15],
        'slow_window': [20, 25, 30]
    }

    result = adapter.optimize_parameters(
        VectorBTStrategies.moving_average_crossover,
        param_ranges,
        optimization_metric='sharpe_ratio'
    )

    assert 'best_params' in result
    assert 'best_result' in result
    assert 'best_score' in result

def test_parallel_backtest_worker():
    """測試並行回測工作進程"""
    from src.backtest.vectorbt_adapter import VectorBTAdapter

    # 創建測試任務
    dates = pd.date_range('2023-01-01', periods=50, freq='D')
    data = pd.DataFrame({
        'open': 100 + np.random.randn(50) * 0.5,
        'high': lambda x: x['open'] * 1.02,
        'low': lambda x: x['open'] * 0.98,
        'close': lambda x: x['open'] + np.random.randn(50) * 0.1,
        'volume': np.random.randint(100000, 1000000, 50)
    }, index=dates)

    task_data = {
        'task_id': 'test_001',
        'data': data,
        'config': VectorBTConfig().__dict__,
        'strategy_func': VectorBTStrategies.moving_average_crossover,
        'strategy_params': {'fast_window': 10, 'slow_window': 20}
    }

    result = VectorBTAdapter.parallel_backtest_worker(task_data)

    assert result['task_id'] == 'test_001'
    assert result['status'] == 'completed'
    assert 'error' not in result

def test_rsi_strategy(sample_data):
    """測試RSI策略"""
    adapter = VectorBTAdapter()
    adapter.load_data(sample_data)

    entries, exits = adapter.prepare_signals(
        VectorBTStrategies.rsi_strategy,
        rsi_window=14,
        oversold=30,
        overbought=70
    )

    assert isinstance(entries, pd.DataFrame)
    assert isinstance(exits, pd.DataFrame)
    assert len(entries) == len(sample_data)

def test_bollinger_bands_strategy(sample_data):
    """測試布林帶策略"""
    adapter = VectorBTAdapter()
    adapter.load_data(sample_data)

    entries, exits = adapter.prepare_signals(
        VectorBTStrategies.bollinger_bands_strategy,
        window=20,
        num_std=2.0
    )

    assert isinstance(entries, pd.DataFrame)
    assert isinstance(exits, pd.DataFrame)
    assert len(entries) == len(sample_data)

@pytest.mark.performance
def test_performance_large_dataset():
    """性能測試：大數據集"""
    import time

    # 生成大量數據
    dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')
    data = pd.DataFrame({
        'open': 100 + np.random.randn(len(dates)).cumsum() * 0.5,
        'high': lambda x: x['open'] * 1.02,
        'low': lambda x: x['open'] * 0.98,
        'close': lambda x: x['open'] + np.random.randn(len(dates)) * 0.1,
        'volume': np.random.randint(100000, 1000000, len(dates))
    }, index=dates)

    # 測試執行時間
    start_time = time.time()

    adapter = VectorBTAdapter()
    adapter.load_data(data)

    entries, exits = adapter.prepare_signals(
        VectorBTStrategies.moving_average_crossover,
        fast_window=20,
        slow_window=50
    )

    result = adapter.run_backtest(entries, exits)

    execution_time = time.time() - start_time

    # 驗證性能（應該在合理時間內完成）
    assert execution_time < 10  # 10秒內完成
    assert result['total_trades'] >= 0

    print(f"\n性能測試結果:")
    print(f"數據量: {len(data)}行")
    print(f"執行時間: {execution_time:.2f}秒")
    print(f"內存使用: {data.memory_usage(deep=True).sum() / 1024 / 1024:.1f}MB")

if __name__ == "__main__":
    pytest.main([__file__, '-v'])
```

## 4. 部署配置

### 4.1 Docker Compose配置

```yaml
# docker-compose.vectorbt.yml
version: '3.8'

services:
  vectorbt-backtest:
    build:
      context: .
      dockerfile: Dockerfile.vectorbt
    ports:
      - "8002:8002"
    environment:
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/backtest
      - VECTORBT_LICENSE_KEY=${VECTORBT_LICENSE_KEY}
    volumes:
      - ./src:/app/src
      - ./data:/app/data
      - ./cache:/app/cache
    depends_on:
      - redis
      - postgres
    deploy:
      resources:
        reservations:
          cpus: '2'
          memory: 4G
        limits:
          cpus: '4'
          memory: 8G

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=backtest
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  jupyter:
    image: python:3.9-slim
    ports:
      - "8888:8888"
    volumes:
      - ./notebooks:/app/notebooks
      - ./src:/app/src
    command: >
      bash -c "
        pip install jupyter pandas numpy matplotlib &&
        cd /app &&
        jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser --allow-root
      "

volumes:
  redis_data:
  postgres_data:
```

### 4.2 環境變量配置

```bash
# .env.vectorbt
# VectorBT配置
VECTORBT_LICENSE_KEY=your_license_key_here

# 數據庫配置
DATABASE_URL=postgresql://user:password@localhost:5432/backtest

# Redis配置
REDIS_URL=redis://localhost:6379

# API配置
API_HOST=0.0.0.0
API_PORT=8002

# 並行處理配置
MAX_WORKERS=8
CHUNK_SIZE=10000

# 緩存配置
CACHE_DIR=./cache
CACHE_TTL=3600

# 日誌配置
LOG_LEVEL=INFO
LOG_FILE=./logs/vectorbt.log

# 性能配置
ENABLE_PROFILING=True
MEMORY_LIMIT_GB=8

# GPU配置（可選）
CUDA_VISIBLE_DEVICES=0
```

## 總結

本代碼示例庫提供了VectorBT與CBSC系統集成的完整實現，包括：

1. **核心適配器**：VectorBTAdapter類提供與現有系統兼容的接口
2. **策略庫**：預置10+常用技術指標和策略
3. **並行處理**：支持多進程參數優化和蒙地卡羅模擬
4. **性能優化**：內存優化和計算加速
5. **完整測試**：單元測試和性能測試
6. **部署方案**：Docker和Kubernetes配置

通過使用這些示例，可以快速實現高性能的向量化回測系統，並根據實際需求進行定制和擴展。
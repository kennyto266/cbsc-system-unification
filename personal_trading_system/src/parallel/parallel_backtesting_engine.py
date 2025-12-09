#!/usr/bin/env python3
"""
Parallel Backtesting Engine with VectorBT Integration
High-performance 32-core parallel backtesting with intelligent resource allocation
"""

import os
import sys
import time
import uuid
import logging
import warnings
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np
import pandas as pd

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Try to import VectorBT
try:
    import vectorbt as vbt
    VECTOREBT_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("VectorBT successfully imported")
except ImportError:
    VECTOREBT_AVAILABLE = False
    vbt = None
    logger = logging.getLogger(__name__)
    logger.warning("VectorBT not available, using fallback implementation")

from .multi_process_scheduler import MultiProcessScheduler, TaskPriority
from .parallel_data_processor import ParallelDataProcessor
from .interprocess_communication import InterProcessCommunication, MessageType

logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    """Configuration for parallel backtesting"""
    symbols: List[str]
    start_date: datetime
    end_date: datetime
    initial_cash: float = 1000000.0
    commission: float = 0.001
    slippage: float = 0.0001
    data_frequency: str = '1D'
    benchmark: Optional[str] = None

    # Parallel processing settings
    num_workers: int = 32
    chunk_size: Optional[int] = None
    memory_limit_gb: float = 16.0
    enable_shared_memory: bool = True

    # Strategy settings
    strategy_class: Optional[str] = None
    strategy_params: Dict[str, Any] = field(default_factory=dict)

    # Output settings
    enable_progress_tracking: bool = True
    save_intermediate_results: bool = False
    output_format: str = 'json'


@dataclass
class BacktestChunk:
    """Represents a chunk of backtesting work"""
    chunk_id: str
    symbols: List[str]
    start_date: datetime
    end_date: datetime
    data: pd.DataFrame
    strategy_params: Dict[str, Any]
    chunk_index: int
    total_chunks: int


@dataclass
class BacktestResult:
    """Results from a backtest chunk"""
    chunk_id: str
    symbols: List[str]
    start_date: datetime
    end_date: datetime

    # Performance metrics
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    total_trades: int

    # Portfolio metrics
    final_portfolio_value: float
    equity_curve: pd.Series
    drawdown_curve: pd.Series

    # Trade details
    trades: pd.DataFrame
    positions: pd.DataFrame

    # Execution statistics
    execution_time: float
    memory_usage_mb: float
    warnings: List[str] = field(default_factory=list)


class ParallelBacktestingEngine:
    """
    High-performance parallel backtesting engine

    Features:
    - VectorBT integration for professional backtesting
    - 32-core parallel processing with intelligent load balancing
    - Memory-efficient data chunking and processing
    - Advanced performance metrics and analytics
    - Real-time progress tracking and monitoring
    - Fault tolerance and recovery mechanisms
    - Support for complex multi-asset strategies
    """

    def __init__(
        self,
        config: BacktestConfig,
        scheduler: Optional[MultiProcessScheduler] = None,
        data_processor: Optional[ParallelDataProcessor] = None
    ):
        self.config = config

        # Initialize components
        self.scheduler = scheduler or MultiProcessScheduler(
            max_workers=config.num_workers,
            memory_limit_gb=config.memory_limit_gb
        )

        self.data_processor = data_processor or ParallelDataProcessor(
            scheduler=self.scheduler,
            max_chunk_size_mb=config.memory_limit_gb * 1024 / config.num_workers
        )

        # IPC for data sharing
        if config.enable_shared_memory:
            self.ipc = InterProcessCommunication(
                process_id=0,  # Main process
                max_shared_memory_mb=int(config.memory_limit_gb * 512)  # Use half for shared memory
            )
        else:
            self.ipc = None

        # Backtesting state
        self.active_backtests: Dict[str, BacktestChunk] = {}
        self.backtest_results: Dict[str, BacktestResult] = {}
        self.aggregated_results: Optional[BacktestResult] = None

        # Performance tracking
        self.stats = {
            'total_backtests_run': 0,
            'total_symbols_processed': 0,
            'total_data_processed_gb': 0.0,
            'average_backtest_time': 0.0,
            'peak_memory_usage_mb': 0.0,
            'vector_benchmarks': {}
        }

        logger.info(f"ParallelBacktestingEngine initialized for {len(config.symbols)} symbols")

    def run_parallel_backtest(
        self,
        data: pd.DataFrame,
        strategy_function: Callable,
        strategy_params: Dict[str, Any] = None
    ) -> BacktestResult:
        """
        Run parallel backtesting on the provided data

        Args:
            data: Multi-index DataFrame with price data
            strategy_function: Strategy function to backtest
            strategy_params: Additional strategy parameters

        Returns:
            Aggregated backtest results
        """
        start_time = time.time()
        logger.info(f"Starting parallel backtest on {len(data)} rows for {len(self.config.symbols)} symbols")

        try:
            # Create data chunks
            chunks = self._create_backtest_chunks(data, strategy_params or {})
            logger.info(f"Created {len(chunks)} backtest chunks")

            # Process chunks in parallel
            chunk_results = self._process_chunks_parallel(chunks, strategy_function)

            # Aggregate results
            self.aggregated_results = self._aggregate_results(chunk_results)

            # Update statistics
            processing_time = time.time() - start_time
            self._update_backtest_statistics(processing_time, len(data), len(chunks))

            logger.info(f"Parallel backtest completed in {processing_time:.2f}s")
            return self.aggregated_results

        except Exception as e:
            logger.error(f"Parallel backtest failed: {e}")
            raise

    def run_symbol_parallel_backtest(
        self,
        data_dict: Dict[str, pd.DataFrame],
        strategy_function: Callable,
        strategy_params: Dict[str, Any] = None
    ) -> Dict[str, BacktestResult]:
        """
        Run backtests in parallel across symbols

        Args:
            data_dict: Dictionary mapping symbols to DataFrames
            strategy_function: Strategy function to backtest
            strategy_params: Additional strategy parameters

        Returns:
            Dictionary mapping symbols to backtest results
        """
        start_time = time.time()
        logger.info(f"Starting symbol-parallel backtest on {len(data_dict)} symbols")

        results = {}

        # Create tasks for each symbol
        task_ids = []
        for symbol, symbol_data in data_dict.items():
            task_id = self.scheduler.submit_task(
                function=self._backtest_single_symbol,
                args=(symbol, symbol_data, strategy_function, strategy_params or {}),
                priority=TaskPriority.NORMAL,
                estimated_memory_mb=self._estimate_symbol_memory_usage(symbol_data),
                estimated_cpu_time=self._estimate_symbol_processing_time(symbol_data)
            )
            task_ids.append((symbol, task_id))

        # Wait for completion and collect results
        for symbol, task_id in task_ids:
            try:
                result = self.scheduler.get_task_result(task_id)
                if result:
                    results[symbol] = result
                else:
                    logger.warning(f"No result for symbol {symbol}")
            except Exception as e:
                logger.error(f"Failed to get result for symbol {symbol}: {e}")

        # Update statistics
        processing_time = time.time() - start_time
        self.stats['total_backtests_run'] += len(results)
        self.stats['total_symbols_processed'] += len(results)
        self.stats['average_backtest_time'] = processing_time / max(1, len(results))

        logger.info(f"Symbol-parallel backtest completed in {processing_time:.2f}s")
        return results

    def run_parameter_sweep(
        self,
        data: pd.DataFrame,
        strategy_function: Callable,
        parameter_grid: Dict[str, List[Any]],
        combination_limit: Optional[int] = None
    ) -> List[BacktestResult]:
        """
        Run parameter sweep with parallel processing

        Args:
            data: Backtesting data
            strategy_function: Strategy function
            parameter_grid: Grid of parameters to test
            combination_limit: Limit number of parameter combinations

        Returns:
            List of backtest results for each parameter combination
        """
        start_time = time.time()

        # Generate parameter combinations
        combinations = self._generate_parameter_combinations(parameter_grid, combination_limit)
        logger.info(f"Running parameter sweep with {len(combinations)} combinations")

        # Submit tasks for each combination
        task_ids = []
        for i, params in enumerate(combinations):
            task_id = self.scheduler.submit_task(
                function=self._backtest_parameter_combination,
                args=(data, strategy_function, params),
                priority=TaskPriority.NORMAL,
                estimated_memory_mb=50,  # Conservative estimate
                estimated_cpu_time=5.0   # Conservative estimate
            )
            task_ids.append((i, params, task_id))

        # Collect results
        results = []
        for i, params, task_id in task_ids:
            try:
                result = self.scheduler.get_task_result(task_id)
                if result:
                    result.strategy_params = params
                    results.append(result)
            except Exception as e:
                logger.error(f"Failed to get result for combination {i}: {e}")

        # Sort by performance metric (e.g., Sharpe ratio)
        results.sort(key=lambda x: x.sharpe_ratio, reverse=True)

        processing_time = time.time() - start_time
        logger.info(f"Parameter sweep completed in {processing_time:.2f}s, {len(results)} successful results")

        return results

    def _create_backtest_chunks(
        self,
        data: pd.DataFrame,
        strategy_params: Dict[str, Any]
    ) -> List[BacktestChunk]:
        """Create backtesting chunks from data"""
        chunks = []

        # Determine optimal chunking strategy
        if isinstance(data.index, pd.MultiIndex):
            # Multi-asset data - chunk by time
            date_range = pd.date_range(self.config.start_date, self.config.end_date, freq='D')
            chunk_size = len(date_range) // self.config.num_workers

            for i in range(0, len(date_range), chunk_size):
                chunk_start = date_range[i]
                chunk_end = date_range[min(i + chunk_size, len(date_range) - 1)]

                # Filter data for this time chunk
                chunk_data = data.loc[(slice(None), chunk_start:chunk_end), :]

                chunk = BacktestChunk(
                    chunk_id=f"chunk_{i//chunk_size:04d}",
                    symbols=self.config.symbols,
                    start_date=chunk_start,
                    end_date=chunk_end,
                    data=chunk_data,
                    strategy_params=strategy_params,
                    chunk_index=len(chunks),
                    total_chunks=(len(date_range) + chunk_size - 1) // chunk_size
                )
                chunks.append(chunk)

        else:
            # Single asset or pre-grouped data - chunk by rows
            chunk_size = len(data) // self.config.num_workers

            for i in range(0, len(data), chunk_size):
                chunk_data = data.iloc[i:i + chunk_size]

                chunk = BacktestChunk(
                    chunk_id=f"chunk_{i//chunk_size:04d}",
                    symbols=self.config.symbols,
                    start_date=chunk_data.index.min(),
                    end_date=chunk_data.index.max(),
                    data=chunk_data,
                    strategy_params=strategy_params,
                    chunk_index=len(chunks),
                    total_chunks=(len(data) + chunk_size - 1) // chunk_size
                )
                chunks.append(chunk)

        return chunks

    def _process_chunks_parallel(
        self,
        chunks: List[BacktestChunk],
        strategy_function: Callable
    ) -> List[BacktestResult]:
        """Process backtesting chunks in parallel"""
        # Submit tasks
        task_ids = []
        for chunk in chunks:
            task_id = self.scheduler.submit_task(
                function=self._backtest_chunk_worker,
                args=(chunk, strategy_function),
                priority=TaskPriority.HIGH,
                estimated_memory_mb=self._estimate_chunk_memory_usage(chunk),
                estimated_cpu_time=self._estimate_chunk_processing_time(chunk.data)
            )
            task_ids.append((chunk.chunk_id, task_id))

        # Wait for completion
        results = []
        for chunk_id, task_id in task_ids:
            try:
                result = self.scheduler.get_task_result(task_id)
                if result:
                    results.append(result)
                    self.backtest_results[chunk_id] = result
            except Exception as e:
                logger.error(f"Failed to get result for chunk {chunk_id}: {e}")

        # Sort results by chunk index to maintain order
        results.sort(key=lambda x: int(x.chunk_id.split('_')[-1]))

        return results

    def _backtest_chunk_worker(self, chunk: BacktestChunk, strategy_function: Callable) -> BacktestResult:
        """Worker function for processing a single backtest chunk"""
        start_time = time.time()

        try:
            # Execute backtesting using VectorBT if available
            if VECTOREBT_AVAILABLE and vbt:
                result = self._vectorbt_backtest(chunk, strategy_function)
            else:
                # Fallback implementation
                result = self._fallback_backtest(chunk, strategy_function)

            # Update execution statistics
            result.execution_time = time.time() - start_time

            return result

        except Exception as e:
            logger.error(f"Backtesting failed for chunk {chunk.chunk_id}: {e}")

            # Return error result
            return BacktestResult(
                chunk_id=chunk.chunk_id,
                symbols=chunk.symbols,
                start_date=chunk.start_date,
                end_date=chunk.end_date,
                total_return=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                win_rate=0.0,
                profit_factor=0.0,
                total_trades=0,
                final_portfolio_value=self.config.initial_cash,
                equity_curve=pd.Series(),
                drawdown_curve=pd.Series(),
                trades=pd.DataFrame(),
                positions=pd.DataFrame(),
                execution_time=time.time() - start_time,
                memory_usage_mb=0,
                warnings=[f"Backtesting failed: {str(e)}"]
            )

    def _vectorbt_backtest(self, chunk: BacktestChunk, strategy_function: Callable) -> BacktestResult:
        """Perform backtesting using VectorBT"""
        data = chunk.data

        # Extract price data
        if isinstance(data.index, pd.MultiIndex):
            # Multi-asset data
            close_data = data['close'].unstack(level=0) if 'close' in data.columns else data.xs('close', level=1, axis=1)
        else:
            # Single asset data
            close_data = data['close'] if 'close' in data.columns else data

        # Generate signals using strategy function
        signals = strategy_function(close_data, **chunk.strategy_params)

        # Convert signals to entries and exits
        if isinstance(signals, pd.DataFrame):
            entries = signals > 0
            exits = signals < 0
        elif isinstance(signals, pd.Series):
            entries = signals > 0
            exits = signals < 0
        else:
            raise ValueError("Strategy function must return pandas Series or DataFrame")

        # Create VectorBT portfolio
        portfolio = vbt.Portfolio.from_signals(
            close=close_data,
            entries=entries,
            exits=exits,
            init_cash=self.config.initial_cash,
            fees=self.config.commission,
            slippage=self.config.slippage,
            freq=self.config.data_frequency
        )

        # Extract results
        stats = portfolio.stats()

        return BacktestResult(
            chunk_id=chunk.chunk_id,
            symbols=chunk.symbols,
            start_date=chunk.start_date,
            end_date=chunk.end_date,
            total_return=stats['Total Return [%]'] / 100,
            sharpe_ratio=stats['Sharpe Ratio'],
            max_drawdown=stats['Max Drawdown [%]'] / 100,
            win_rate=stats['Win Rate [%]'] / 100,
            profit_factor=stats.get('Profit Factor', 0),
            total_trades=int(stats['# Trades']),
            final_portfolio_value=portfolio.value()[-1],
            equity_curve=portfolio.value(),
            drawdown_curve=portfolio.drawdown(),
            trades=portfolio.trades.records_readable,
            positions=portfolio.positions.records_readable,
            execution_time=0,  # Will be set by caller
            memory_usage_mb=close_data.memory_usage(deep=True).sum() / (1024 * 1024),
            warnings=[]
        )

    def _fallback_backtest(self, chunk: BacktestChunk, strategy_function: Callable) -> BacktestResult:
        """Fallback backtesting implementation without VectorBT"""
        data = chunk.data

        # Simple fallback implementation
        if isinstance(data.index, pd.MultiIndex):
            close_data = data['close'].unstack(level=0) if 'close' in data.columns else data.xs('close', level=1, axis=1)
        else:
            close_data = data['close'] if 'close' in data.columns else data

        # Generate simple signals
        signals = strategy_function(close_data, **chunk.strategy_params)

        # Simple backtesting logic
        portfolio_value = pd.Series(self.config.initial_cash, index=close_data.index)
        positions = pd.DataFrame(0, index=close_data.index, columns=close_data.columns)

        # Basic signal processing
        if isinstance(signals, pd.DataFrame):
            entries = signals > 0
            exits = signals < 0

            for symbol in close_data.columns:
                for i in range(1, len(close_data)):
                    if entries.iloc[i][symbol]:
                        positions.iloc[i][symbol] = 1
                    elif exits.iloc[i][symbol]:
                        positions.iloc[i][symbol] = 0
                    else:
                        positions.iloc[i][symbol] = positions.iloc[i-1][symbol]

        # Calculate portfolio value
        returns = close_data.pct_change().fillna(0)
        portfolio_returns = (positions.shift(1) * returns).sum(axis=1)
        portfolio_value = self.config.initial_cash * (1 + portfolio_returns).cumprod()

        # Calculate basic metrics
        total_return = (portfolio_value.iloc[-1] / portfolio_value.iloc[0]) - 1
        portfolio_returns_clean = portfolio_returns[portfolio_returns != 0]
        sharpe_ratio = portfolio_returns_clean.mean() / portfolio_returns_clean.std() * np.sqrt(252) if len(portfolio_returns_clean) > 1 else 0
        drawdown = (portfolio_value / portfolio_value.cummax() - 1)
        max_drawdown = drawdown.min()

        return BacktestResult(
            chunk_id=chunk.chunk_id,
            symbols=chunk.symbols,
            start_date=chunk.start_date,
            end_date=chunk.end_date,
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=0.5,  # Placeholder
            profit_factor=1.0,  # Placeholder
            total_trades=0,  # Placeholder
            final_portfolio_value=portfolio_value.iloc[-1],
            equity_curve=portfolio_value,
            drawdown_curve=drawdown,
            trades=pd.DataFrame(),  # Empty for fallback
            positions=positions,
            execution_time=0,  # Will be set by caller
            memory_usage_mb=close_data.memory_usage(deep=True).sum() / (1024 * 1024),
            warnings=['Using fallback backtesting implementation - VectorBT not available']
        )

    def _aggregate_results(self, chunk_results: List[BacktestResult]) -> BacktestResult:
        """Aggregate results from multiple chunks"""
        if not chunk_results:
            raise ValueError("No chunk results to aggregate")

        if len(chunk_results) == 1:
            return chunk_results[0]

        # Combine equity curves
        combined_equity = pd.concat([r.equity_curve for r in chunk_results]).sort_index()
        combined_drawdown = pd.concat([r.drawdown_curve for r in chunk_results]).sort_index()

        # Calculate aggregate metrics
        total_return = (combined_equity.iloc[-1] / combined_equity.iloc[0]) - 1
        returns = combined_equity.pct_change().dropna()
        sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) if len(returns) > 1 else 0
        max_drawdown = combined_drawdown.min()

        # Combine trades
        all_trades = pd.concat([r.trades for r in chunk_results], ignore_index=True)
        total_trades = len(all_trades)

        # Calculate win rate and profit factor
        winning_trades = len(all_trades[all_trades['pnl'] > 0]) if 'pnl' in all_trades.columns else total_trades // 2
        win_rate = winning_trades / max(1, total_trades)
        profit_factor = 1.0  # Placeholder calculation

        return BacktestResult(
            chunk_id="aggregated",
            symbols=list(set(sum([r.symbols for r in chunk_results], []))),
            start_date=min(r.start_date for r in chunk_results),
            end_date=max(r.end_date for r in chunk_results),
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_trades=total_trades,
            final_portfolio_value=combined_equity.iloc[-1],
            equity_curve=combined_equity,
            drawdown_curve=combined_drawdown,
            trades=all_trades,
            positions=pd.DataFrame(),  # Would need more complex aggregation
            execution_time=sum(r.execution_time for r in chunk_results),
            memory_usage_mb=sum(r.memory_usage_mb for r in chunk_results),
            warnings=list(set(sum([r.warnings for r in chunk_results], [])))
        )

    def _generate_parameter_combinations(
        self,
        parameter_grid: Dict[str, List[Any]],
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Generate parameter combinations for parameter sweep"""
        import itertools

        keys = list(parameter_grid.keys())
        values = list(parameter_grid.values())

        combinations = []
        for combination in itertools.product(*values):
            params = dict(zip(keys, combination))
            combinations.append(params)

            if limit and len(combinations) >= limit:
                break

        return combinations

    def _backtest_single_symbol(
        self,
        symbol: str,
        data: pd.DataFrame,
        strategy_function: Callable,
        strategy_params: Dict[str, Any]
    ) -> BacktestResult:
        """Backtest a single symbol"""
        chunk = BacktestChunk(
            chunk_id=f"symbol_{symbol}",
            symbols=[symbol],
            start_date=data.index.min(),
            end_date=data.index.max(),
            data=data,
            strategy_params=strategy_params,
            chunk_index=0,
            total_chunks=1
        )

        return self._backtest_chunk_worker(chunk, strategy_function)

    def _backtest_parameter_combination(
        self,
        data: pd.DataFrame,
        strategy_function: Callable,
        params: Dict[str, Any]
    ) -> BacktestResult:
        """Backtest a single parameter combination"""
        chunk = BacktestChunk(
            chunk_id=f"params_{hash(str(params)) % 10000:04d}",
            symbols=self.config.symbols,
            start_date=self.config.start_date,
            end_date=self.config.end_date,
            data=data,
            strategy_params=params,
            chunk_index=0,
            total_chunks=1
        )

        return self._backtest_chunk_worker(chunk, strategy_function)

    def _estimate_chunk_memory_usage(self, chunk: BacktestChunk) -> int:
        """Estimate memory usage for a backtest chunk"""
        data_size_mb = chunk.data.memory_usage(deep=True).sum() / (1024 * 1024)
        return int(data_size_mb * 4)  # 4x buffer for processing

    def _estimate_chunk_processing_time(self, data: pd.DataFrame) -> float:
        """Estimate processing time for a data chunk"""
        rows = len(data)
        cols = len(data.columns) if hasattr(data, 'columns') else 1

        # Base time estimation (adjust based on your system performance)
        base_time = rows * cols / 100000  # 100k cells per second
        return max(0.5, base_time)  # Minimum 0.5 seconds

    def _estimate_symbol_memory_usage(self, data: pd.DataFrame) -> int:
        """Estimate memory usage for single symbol backtest"""
        return int(data.memory_usage(deep=True).sum() / (1024 * 1024) * 3)  # 3x buffer

    def _estimate_symbol_processing_time(self, data: pd.DataFrame) -> float:
        """Estimate processing time for single symbol backtest"""
        rows = len(data)
        cols = len(data.columns) if hasattr(data, 'columns') else 1
        return max(1.0, rows * cols / 50000)  # 50k cells per second

    def _update_backtest_statistics(
        self,
        processing_time: float,
        data_rows: int,
        num_chunks: int
    ):
        """Update backtesting statistics"""
        self.stats['total_backtests_run'] += 1
        self.stats['total_symbols_processed'] += len(self.config.symbols)
        self.stats['total_data_processed_gb'] = data_rows * 8 / (1024**3)  # Rough estimate
        self.stats['average_backtest_time'] = processing_time

    def get_results(self) -> Optional[BacktestResult]:
        """Get the latest aggregated backtest results"""
        return self.aggregated_results

    def get_statistics(self) -> Dict[str, Any]:
        """Get engine statistics"""
        return {
            'engine_stats': self.stats.copy(),
            'config': {
                'symbols': self.config.symbols,
                'num_workers': self.config.num_workers,
                'memory_limit_gb': self.config.memory_limit_gb
            },
            'scheduler_stats': self.scheduler.get_statistics(),
            'data_processor_stats': self.data_processor.get_statistics()
        }

    def cleanup(self):
        """Clean up resources"""
        if self.scheduler:
            self.scheduler.stop()
        if self.ipc:
            self.ipc.stop()
        logger.info("ParallelBacktestingEngine cleaned up")


# Strategy function examples
def simple_ma_crossover_strategy(prices: pd.DataFrame, fast_period: int = 10, slow_period: int = 30) -> pd.DataFrame:
    """Simple moving average crossover strategy"""
    signals = pd.DataFrame(0, index=prices.index, columns=prices.columns)

    for symbol in prices.columns:
        price_series = prices[symbol]
        fast_ma = price_series.rolling(window=fast_period).mean()
        slow_ma = price_series.rolling(window=slow_period).mean()

        # Generate signals: 1 for buy, -1 for sell, 0 for hold
        signals[symbol] = np.where(fast_ma > slow_ma, 1, -1)

    return signals


def rsi_mean_reversion_strategy(prices: pd.DataFrame, rsi_period: int = 14, oversold: float = 30, overbought: float = 70) -> pd.DataFrame:
    """RSI mean reversion strategy"""
    signals = pd.DataFrame(0, index=prices.index, columns=prices.columns)

    for symbol in prices.columns:
        price_series = prices[symbol]

        # Calculate RSI
        delta = price_series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        # Generate signals
        signals[symbol] = np.where(rsi < oversold, 1, np.where(rsi > overbought, -1, 0))

    return signals
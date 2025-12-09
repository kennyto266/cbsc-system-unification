"""
Enhanced Multi-Process VectorBT Engine for Unified Backtesting

High-performance VectorBT engine with multi-process support for handling
large-scale parameter optimization (120,832+ combinations) with memory
management and fault tolerance.

Key Features:
- Multi-process VectorBT execution with configurable worker pools
- Adaptive memory management for large parameter spaces
- Batch processing and chunking for memory efficiency
- Real-time progress tracking and result aggregation
- Fault tolerance and error recovery
- Support for 0-300 parameter ranges with step 5
"""

import os
import time
import logging
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Dict, List, Tuple, Optional, Any, Iterator, Union
from dataclasses import dataclass, asdict
import numpy as np
import pandas as pd
from functools import partial
import json
import traceback

# Import VectorBT (will need to be installed)
try:
    import vectorbt as vbt
    VECTORBT_AVAILABLE = True
except ImportError:
    VECTORBT_AVAILABLE = False
    logging.warning("VectorBT not available. Install with: pip install vectorbt")

logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    """Individual backtest result structure"""
    parameters: Dict[str, Any]
    strategy_name: str
    combination_index: int
    sharpe_ratio: float
    max_drawdown: float
    total_return: float
    win_rate: float
    profit_factor: float
    calmar_ratio: float
    sortino_ratio: float
    annualized_return: float
    volatility: float
    trades_count: int
    execution_time: float
    error: Optional[str] = None
    metrics: Optional[Dict[str, float]] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return asdict(self)


@dataclass
class BatchResult:
    """Batch processing result"""
    results: List[BacktestResult]
    batch_index: int
    total_combinations: int
    processing_time: float
    successful_count: int
    failed_count: int

    @property
    def success_rate(self) -> float:
        """Calculate success rate for this batch"""
        return self.successful_count / len(self.results) if self.results else 0.0


class MemoryMonitor:
    """Monitor and manage memory usage during backtesting"""

    def __init__(self, memory_limit_gb: float = 4.0):
        self.memory_limit_gb = memory_limit_gb
        self.memory_limit_bytes = memory_limit_gb * 1024**3

    def check_memory_usage(self) -> Tuple[float, bool]:
        """Check current memory usage and return (usage_gb, is_safe)"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_gb = memory_info.rss / 1024**3
            is_safe = memory_gb < self.memory_limit_gb
            return memory_gb, is_safe
        except ImportError:
            logger.warning("psutil not available, cannot monitor memory")
            return 0.0, True

    def suggest_batch_size(self, current_batch_size: int, memory_usage: float) -> int:
        """Suggest optimal batch size based on current memory usage"""
        if memory_usage > self.memory_limit_gb * 0.8:
            # Reduce batch size if using too much memory
            return max(current_batch_size // 2, 10)
        elif memory_usage < self.memory_limit_gb * 0.5:
            # Can increase batch size if using little memory
            return min(current_batch_size * 2, 1000)
        return current_batch_size


class EnhancedVectorBTEngine:
    """
    Enhanced multi-process VectorBT engine for large-scale backtesting

    Designed to handle the computational requirements of 0-300 parameter
    range optimization with efficient resource utilization.
    """

    def __init__(self, config=None):
        """Initialize the enhanced VectorBT engine"""
        if config is None:
            from ..core.config import DEFAULT_CONFIG
            config = DEFAULT_CONFIG

        self.config = config
        self.max_workers = config.max_workers
        self.chunk_size = config.chunk_size
        self.memory_monitor = MemoryMonitor(config.memory_limit_gb)

        if not VECTORBT_AVAILABLE:
            raise ImportError("VectorBT is required. Install with: pip install vectorbt")

        logger.info(f"Initialized Enhanced VectorBT Engine with {self.max_workers} workers")
        logger.info(f"Memory limit: {config.memory_limit_gb}GB")

    def prepare_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare data for VectorBT processing"""
        # Ensure data has proper datetime index
        if not isinstance(data.index, pd.DatetimeIndex):
            if 'date' in data.columns:
                data = data.set_index('date')
                data.index = pd.to_datetime(data.index)

        # Handle missing values
        data = data.fillna(method='ffill').fillna(method='bfill')

        # Ensure required columns exist
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in data.columns:
                logger.warning(f"Column {col} not found, using close prices")
                data[col] = data['close']

        return data

    def _execute_single_backtest(self, strategy_data: Tuple[str, Dict, int, pd.DataFrame]) -> BacktestResult:
        """
        Execute a single backtest combination

        Args:
            strategy_data: Tuple of (strategy_name, parameters, index, price_data)

        Returns:
            BacktestResult with performance metrics
        """
        strategy_name, parameters, index, price_data = strategy_data
        start_time = time.time()

        try:
            # Generate signals based on strategy
            signals = self._generate_signals(strategy_name, parameters, price_data)

            if signals.empty:
                return BacktestResult(
                    parameters=parameters,
                    strategy_name=strategy_name,
                    combination_index=index,
                    sharpe_ratio=0.0,
                    max_drawdown=0.0,
                    total_return=0.0,
                    win_rate=0.0,
                    profit_factor=0.0,
                    calmar_ratio=0.0,
                    sortino_ratio=0.0,
                    annualized_return=0.0,
                    volatility=0.0,
                    trades_count=0,
                    execution_time=time.time() - start_time,
                    error="No signals generated"
                )

            # Create portfolio using VectorBT
            portfolio = vbt.Portfolio.from_signals(
                close=price_data['close'],
                entries=signals['entry'],
                exits=signals['exit'],
                init_cash=100000,
                fees=0.001,  # 0.1% fees
                slippage=0.0005  # 0.05% slippage
            )

            # Calculate metrics
            stats = portfolio.stats()
            metrics = self._calculate_comprehensive_metrics(portfolio, stats)

            execution_time = time.time() - start_time

            return BacktestResult(
                parameters=parameters,
                strategy_name=strategy_name,
                combination_index=index,
                sharpe_ratio=metrics['sharpe_ratio'],
                max_drawdown=metrics['max_drawdown'],
                total_return=metrics['total_return'],
                win_rate=metrics['win_rate'],
                profit_factor=metrics['profit_factor'],
                calmar_ratio=metrics['calmar_ratio'],
                sortino_ratio=metrics['sortino_ratio'],
                annualized_return=metrics['annualized_return'],
                volatility=metrics['volatility'],
                trades_count=metrics['trades_count'],
                execution_time=execution_time,
                metrics=metrics
            )

        except Exception as e:
            logger.error(f"Error in backtest {index}: {str(e)}")
            return BacktestResult(
                parameters=parameters,
                strategy_name=strategy_name,
                combination_index=index,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                total_return=0.0,
                win_rate=0.0,
                profit_factor=0.0,
                calmar_ratio=0.0,
                sortino_ratio=0.0,
                annualized_return=0.0,
                volatility=0.0,
                trades_count=0,
                execution_time=time.time() - start_time,
                error=str(e)
            )

    def _generate_signals(self, strategy_name: str, parameters: Dict, price_data: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals based on strategy and parameters"""
        if strategy_name == 'rsi_strategy':
            return self._generate_rsi_signals(parameters, price_data)
        elif strategy_name == 'macd_strategy':
            return self._generate_macd_signals(parameters, price_data)
        elif strategy_name == 'bollinger_strategy':
            return self._generate_bollinger_signals(parameters, price_data)
        elif strategy_name == 'sentiment_strategy':
            return self._generate_sentiment_signals(parameters, price_data)
        else:
            raise ValueError(f"Unknown strategy: {strategy_name}")

    def _generate_rsi_signals(self, parameters: Dict, price_data: pd.DataFrame) -> pd.DataFrame:
        """Generate RSI-based trading signals"""
        period = parameters.get('rsi_period', 14)
        overbought = parameters.get('rsi_overbought', 70)
        oversold = parameters.get('rsi_oversold', 30)

        # Calculate RSI using VectorBT
        rsi = vbt.RSI.run(price_data['close'], window=period).rsi

        # Generate signals
        entry_signals = rsi < oversold
        exit_signals = rsi > overbought

        return pd.DataFrame({
            'entry': entry_signals,
            'exit': exit_signals
        })

    def _generate_macd_signals(self, parameters: Dict, price_data: pd.DataFrame) -> pd.DataFrame:
        """Generate MACD-based trading signals"""
        fast = parameters.get('macd_fast', 12)
        slow = parameters.get('macd_slow', 26)
        signal = parameters.get('macd_signal', 9)

        # Calculate MACD using VectorBT
        macd = vbt.MACD.run(
            price_data['close'],
            fast_window=fast,
            slow_window=slow,
            signal_window=signal
        )

        # Generate signals (golden cross and death cross)
        entry_signals = macd.macd_crossed_above(macd.signal)
        exit_signals = macd.macd_crossed_below(macd.signal)

        return pd.DataFrame({
            'entry': entry_signals,
            'exit': exit_signals
        })

    def _generate_bollinger_signals(self, parameters: Dict, price_data: pd.DataFrame) -> pd.DataFrame:
        """Generate Bollinger Bands-based trading signals"""
        period = parameters.get('bb_period', 20)
        std_dev = parameters.get('bb_std_dev', 2.0)

        # Calculate Bollinger Bands using VectorBT
        bb = vbt.BBANDS.run(
            price_data['close'],
            window=period,
            std=std_dev
        )

        # Generate signals (price below lower band = buy, above upper band = sell)
        entry_signals = price_data['close'] < bb.lower
        exit_signals = price_data['close'] > bb.upper

        return pd.DataFrame({
            'entry': entry_signals,
            'exit': exit_signals
        })

    def _generate_sentiment_signals(self, parameters: Dict, price_data: pd.DataFrame) -> pd.DataFrame:
        """Generate CBSC sentiment-based trading signals"""
        # For now, simulate sentiment signals with price-based indicators
        # In a real implementation, this would use CBSC sentiment data
        period = parameters.get('sentiment_rsi_period', 14)
        threshold = parameters.get('sentiment_threshold', 50)

        # Use price momentum as proxy for sentiment
        price_change = price_data['close'].pct_change(period)
        sentiment_score = (price_change - price_change.rolling(period).mean()) / price_change.rolling(period).std()

        entry_signals = sentiment_score < -threshold / 100
        exit_signals = sentiment_score > threshold / 100

        return pd.DataFrame({
            'entry': entry_signals,
            'exit': exit_signals
        })

    def _calculate_comprehensive_metrics(self, portfolio, stats) -> Dict[str, float]:
        """Calculate comprehensive performance metrics"""
        return {
            'sharpe_ratio': stats['Sharpe Ratio'],
            'max_drawdown': stats['Max Drawdown'],
            'total_return': stats['Total Return [%]'] / 100,
            'win_rate': stats['Win Rate [%]'] / 100,
            'profit_factor': stats.get('Profit Factor', 1.0),
            'calmar_ratio': stats.get('Calmar Ratio', 0.0),
            'sortino_ratio': stats.get('Sortino Ratio', 0.0),
            'annualized_return': stats['Annual Return [%]'] / 100,
            'volatility': stats['Volatility (Ann.) [%]'] / 100,
            'trades_count': stats['# Trades']
        }

    def run_backtest_batch(self, strategy_name: str, parameter_combinations: List[Tuple[Dict, int]],
                         price_data: pd.DataFrame) -> BatchResult:
        """
        Run a batch of backtest combinations

        Args:
            strategy_name: Name of the strategy to test
            parameter_combinations: List of (parameters, index) tuples
            price_data: Historical price data

        Returns:
            BatchResult with all backtest results
        """
        start_time = time.time()
        batch_index = parameter_combinations[0][1] // len(parameter_combinations) if parameter_combinations else 0

        # Prepare data for multiprocessing
        strategy_data = [
            (strategy_name, params, index, price_data)
            for params, index in parameter_combinations
        ]

        results = []
        successful_count = 0
        failed_count = 0

        # Execute in parallel using ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_index = {
                executor.submit(self._execute_single_backtest, strategy_data_item): strategy_data_item[2]
                for strategy_data_item in strategy_data
            }

            # Collect results as they complete
            for future in as_completed(future_to_index):
                try:
                    result = future.result()
                    results.append(result)

                    if result.error is None:
                        successful_count += 1
                    else:
                        failed_count += 1

                    # Check memory usage and adjust if needed
                    memory_usage, is_safe = self.memory_monitor.check_memory_usage()
                    if not is_safe:
                        logger.warning(f"High memory usage: {memory_usage:.2f}GB")

                except Exception as e:
                    logger.error(f"Future failed: {str(e)}")
                    failed_count += 1

        processing_time = time.time() - start_time

        batch_result = BatchResult(
            results=results,
            batch_index=batch_index,
            total_combinations=len(parameter_combinations),
            processing_time=processing_time,
            successful_count=successful_count,
            failed_count=failed_count
        )

        logger.info(f"Batch {batch_index} completed: {successful_count}/{len(parameter_combinations)} successful "
                   f"in {processing_time:.2f}s")

        return batch_result

    def run_optimization(self, strategy_name: str, parameter_space, price_data: pd.DataFrame,
                        progress_callback=None) -> Iterator[BatchResult]:
        """
        Run complete parameter optimization with progress tracking

        Args:
            strategy_name: Name of the strategy to optimize
            parameter_space: ParameterSpace instance
            price_data: Historical price data
            progress_callback: Optional progress callback function

        Yields:
            BatchResult for each processed chunk
        """
        total_combinations = parameter_space.get_parameter_combinations_count(strategy_name)
        processed_combinations = 0

        logger.info(f"Starting optimization for {strategy_name}")
        logger.info(f"Total combinations to process: {total_combinations}")

        # Process combinations in chunks
        for chunk in parameter_space.generate_chunked_combinations(
            strategy_name, chunk_size=self.chunk_size
        ):
            batch_result = self.run_backtest_batch(strategy_name, chunk, price_data)
            processed_combinations += len(chunk)

            # Call progress callback if provided
            if progress_callback:
                progress_callback(processed_combinations, total_combinations, batch_result)

            yield batch_result

        logger.info(f"Optimization completed for {strategy_name}")

    def save_results(self, results: List[BatchResult], filepath: str) -> None:
        """Save optimization results to file"""
        all_results = []
        for batch in results:
            all_results.extend([result.to_dict() for result in batch.results])

        output_data = {
            'config': self.config.to_dict(),
            'total_combinations': len(all_results),
            'results': all_results,
            'summary': self._generate_summary(all_results)
        }

        with open(filepath, 'w') as f:
            json.dump(output_data, f, indent=2)

        logger.info(f"Results saved to {filepath}")

    def _generate_summary(self, results: List[Dict]) -> Dict:
        """Generate summary statistics from results"""
        if not results:
            return {}

        df = pd.DataFrame(results)
        successful_results = df[df['error'].isna()]

        if successful_results.empty:
            return {'error': 'No successful results'}

        summary = {
            'total_combinations': len(results),
            'successful_combinations': len(successful_results),
            'success_rate': len(successful_results) / len(results),
            'best_sharpe_ratio': successful_results['sharpe_ratio'].max(),
            'best_total_return': successful_results['total_return'].max(),
            'best_calmar_ratio': successful_results['calmar_ratio'].max(),
            'avg_sharpe_ratio': successful_results['sharpe_ratio'].mean(),
            'avg_max_drawdown': successful_results['max_drawdown'].mean(),
            'avg_trades_count': successful_results['trades_count'].mean()
        }

        # Find best performing parameters
        best_params = successful_results.loc[successful_results['sharpe_ratio'].idxmax()]
        summary['best_parameters'] = best_params['parameters']

        return summary
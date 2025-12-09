"""
Phase 2: 5+ Year Backtesting Engine with VectorBT Integration
Professional long-term backtesting system with advanced features
"""

import pandas as pd
import numpy as np
import vectorbt as vbt
import vectorbt.pro as vbtpro
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from pathlib import Path
import json
import warnings
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pickle
from joblib import Memory
import dask.dataframe as dd
from dask.distributed import Client, as_completed
import psutil
import gc

logger = logging.getLogger(__name__)

@dataclass
class BacktestConfig:
    """Configuration for long-term backtesting"""
    initial_cash: float = 1000000.0
    commission: float = 0.001  # 0.1% commission
    slippage: float = 0.0005  # 0.05% slippage
    cash_sharing: bool = True
    call_seq: str = 'auto'  # 'auto', 'size', 'value'
    freq: str = 'D'  # Daily frequency
    chunk_size: int = 50000  # Number of records per chunk
    max_workers: int = mp.cpu_count() - 1
    memory_limit_gb: float = 4.0  # Memory limit per worker in GB
    use_dask: bool = True
    cache_dir: str = "cache/backtest"
    enable_caching: bool = True
    benchmark: Optional[str] = "2800.HK"  # Default benchmark

@dataclass
class StrategySignal:
    """Trading strategy signal"""
    name: str
    entries: pd.Series
    exits: pd.Series
    parameters: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

@dataclass
class BacktestResult:
    """Comprehensive backtest result"""
    strategy_name: str
    symbol: str
    start_date: str
    end_date: str
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    calmar_ratio: float
    win_rate: float
    profit_factor: float
    total_trades: int
    avg_trade: float
    benchmark_return: float
    alpha: float
    beta: float
    information_ratio: float
    trades: pd.DataFrame
    equity_curve: pd.Series
    benchmark_equity: pd.Series
    detailed_stats: Dict[str, Any]
    backtest_timestamp: datetime

class MemoryManager:
    """Memory management for large-scale backtesting"""

    def __init__(self, memory_limit_gb: float = 4.0):
        self.memory_limit_bytes = memory_limit_gb * 1024**3
        self.process = psutil.Process()

    def get_memory_usage(self) -> float:
        """Get current memory usage in GB"""
        return self.process.memory_info().rss / 1024**3

    def check_memory_limit(self) -> bool:
        """Check if memory limit is exceeded"""
        current_usage = self.get_memory_usage()
        return current_usage > self.memory_limit_bytes / 1024**3

    def force_garbage_collection(self):
        """Force garbage collection"""
        gc.collect()

    def optimize_memory_usage(self):
        """Optimize memory usage"""
        if self.check_memory_limit():
            logger.warning("Memory limit exceeded, forcing garbage collection")
            self.force_garbage_collection()

class ChunkedBacktesting:
    """Chunked backtesting for large datasets"""

    def __init__(self, config: BacktestConfig):
        self.config = config
        self.memory_manager = MemoryManager(config.memory_limit_gb)

    def split_data_into_chunks(self, data: pd.DataFrame) -> List[pd.DataFrame]:
        """Split data into chunks for processing"""
        chunks = []
        for i in range(0, len(data), self.config.chunk_size):
            chunk = data.iloc[i:i + self.config.chunk_size]
            chunks.append(chunk)
        return chunks

    def process_chunk(self, chunk_data: pd.DataFrame, signals: StrategySignal,
                     symbol: str) -> Optional[Dict[str, Any]]:
        """Process a single chunk of data"""
        try:
            # Check memory before processing
            self.memory_manager.optimize_memory_usage()

            # Create VectorBT portfolio for chunk
            portfolio = vbt.Portfolio.from_signals(
                close=chunk_data['close'],
                entries=signals.entries.reindex(chunk_data.index),
                exits=signals.exits.reindex(chunk_data.index),
                init_cash=self.config.initial_cash,
                fees=self.config.commission,
                slippage=self.config.slippage,
                cash_sharing=self.config.cash_sharing,
                call_seq=self.config.call_seq,
                freq=self.config.freq
            )

            # Extract chunk results
            chunk_results = {
                'returns': portfolio.returns(),
                'equity': portfolio.value(),
                'trades': portfolio.trades.records_readable,
                'stats': portfolio.stats(),
                'start_date': chunk_data.index[0],
                'end_date': chunk_data.index[-1],
                'chunk_size': len(chunk_data)
            }

            return chunk_results

        except Exception as e:
            logger.error(f"Error processing chunk: {e}")
            return None

class LongTermBacktestingEngine:
    """Professional long-term backtesting engine with VectorBT"""

    def __init__(self, config: BacktestConfig = None):
        self.config = config or BacktestConfig()
        self.chunked_backtesting = ChunkedBacktesting(self.config)
        self._setup_caching()

    def _setup_caching(self):
        """Setup caching for performance optimization"""
        if self.config.enable_caching:
            Path(self.config.cache_dir).mkdir(parents=True, exist_ok=True)
            self.memory = Memory(self.config.cache_dir, verbose=0)
        else:
            self.memory = None

    def backtest_strategy(self, market_data: pd.DataFrame, signals: StrategySignal,
                         symbol: str, benchmark_data: Optional[pd.DataFrame] = None) -> BacktestResult:
        """
        Run comprehensive backtest with chunked processing

        Args:
            market_data: Market data with OHLCV
            signals: Trading signals
            symbol: Trading symbol
            benchmark_data: Optional benchmark data

        Returns:
            BacktestResult with comprehensive analysis
        """
        logger.info(f"Starting backtest for {symbol} with {len(market_data)} records")

        try:
            # Data preparation
            prepared_data = self._prepare_data(market_data, signals)

            # Prepare benchmark data
            benchmark_returns = self._prepare_benchmark(benchmark_data, prepared_data)

            # Choose processing method based on data size
            if len(prepared_data) > self.config.chunk_size:
                result = self._run_chunked_backtest(prepared_data, signals, symbol, benchmark_returns)
            else:
                result = self._run_standard_backtest(prepared_data, signals, symbol, benchmark_returns)

            logger.info(f"Backtest completed for {symbol}. Total return: {result.total_return:.2%}")
            return result

        except Exception as e:
            logger.error(f"Error in backtesting for {symbol}: {e}")
            raise

    def _prepare_data(self, market_data: pd.DataFrame, signals: StrategySignal) -> pd.DataFrame:
        """Prepare data for backtesting"""
        # Ensure data has required columns
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in market_data.columns:
                raise ValueError(f"Missing required column: {col}")

        # Align signals with market data
        aligned_data = market_data.copy()
        aligned_signals_entries = signals.entries.reindex(aligned_data.index, fill_value=False)
        aligned_signals_exits = signals.exits.reindex(aligned_data.index, fill_value=False)

        # Combine signals with data
        aligned_data['signal_entry'] = aligned_signals_entries
        aligned_data['signal_exit'] = aligned_signals_exits

        # Remove rows with missing data
        aligned_data = aligned_data.dropna(subset=required_columns)

        return aligned_data

    def _prepare_benchmark(self, benchmark_data: Optional[pd.DataFrame],
                         market_data: pd.DataFrame) -> Optional[pd.Series]:
        """Prepare benchmark returns"""
        if benchmark_data is None:
            return None

        try:
            # Calculate benchmark returns
            benchmark_returns = benchmark_data['close'].pct_change().fillna(0)

            # Align with market data
            aligned_benchmark = benchmark_returns.reindex(market_data.index, fill_value=0)

            return aligned_benchmark

        except Exception as e:
            logger.warning(f"Error preparing benchmark data: {e}")
            return None

    def _run_standard_backtest(self, data: pd.DataFrame, signals: StrategySignal,
                              symbol: str, benchmark_returns: Optional[pd.Series]) -> BacktestResult:
        """Run standard VectorBT backtest"""
        # Create portfolio
        portfolio = vbt.Portfolio.from_signals(
            close=data['close'],
            entries=data['signal_entry'],
            exits=data['signal_exit'],
            init_cash=self.config.initial_cash,
            fees=self.config.commission,
            slippage=self.config.slippage,
            cash_sharing=self.config.cash_sharing,
            call_seq=self.config.call_seq,
            freq=self.config.freq
        )

        # Extract results
        returns = portfolio.returns()
        equity = portfolio.value()
        trades = portfolio.trades.records_readable

        # Calculate comprehensive statistics
        stats = self._calculate_comprehensive_stats(
            returns, equity, trades, benchmark_returns
        )

        return BacktestResult(
            strategy_name=signals.name,
            symbol=symbol,
            start_date=data.index[0].strftime('%Y-%m-%d'),
            end_date=data.index[-1].strftime('%Y-%m-%d'),
            total_return=stats['total_return'],
            annualized_return=stats['annualized_return'],
            sharpe_ratio=stats['sharpe_ratio'],
            sortino_ratio=stats['sortino_ratio'],
            max_drawdown=stats['max_drawdown'],
            calmar_ratio=stats['calmar_ratio'],
            win_rate=stats['win_rate'],
            profit_factor=stats['profit_factor'],
            total_trades=stats['total_trades'],
            avg_trade=stats['avg_trade'],
            benchmark_return=stats['benchmark_return'],
            alpha=stats['alpha'],
            beta=stats['beta'],
            information_ratio=stats['information_ratio'],
            trades=trades,
            equity_curve=equity,
            benchmark_equity=self._calculate_benchmark_equity(benchmark_returns, len(equity)),
            detailed_stats=stats,
            backtest_timestamp=datetime.now()
        )

    def _run_chunked_backtest(self, data: pd.DataFrame, signals: StrategySignal,
                            symbol: str, benchmark_returns: Optional[pd.Series]) -> BacktestResult:
        """Run chunked backtest for large datasets"""
        logger.info(f"Running chunked backtest for {len(data)} records")

        # Create updated signals with data alignment
        aligned_signals = StrategySignal(
            name=signals.name,
            entries=data['signal_entry'],
            exits=data['signal_exit'],
            parameters=signals.parameters,
            description=signals.description
        )

        # Split data into chunks
        chunks = self.chunked_backtesting.split_data_into_chunks(data)

        # Process chunks in parallel
        all_results = []

        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            future_to_chunk = {
                executor.submit(
                    self.chunked_backtesting.process_chunk,
                    chunk_data,
                    aligned_signals,
                    symbol
                ): i for i, chunk_data in enumerate(chunks)
            }

            for future in as_completed(future_to_chunk):
                chunk_idx = future_to_chunk[future]
                try:
                    chunk_result = future.result()
                    if chunk_result:
                        all_results.append(chunk_result)
                        logger.info(f"Processed chunk {chunk_idx + 1}/{len(chunks)}")
                except Exception as e:
                    logger.error(f"Error processing chunk {chunk_idx}: {e}")

        # Combine chunk results
        if not all_results:
            raise ValueError("No chunks processed successfully")

        combined_result = self._combine_chunk_results(all_chunks=all_results, symbol=symbol)

        # Calculate benchmark comparison
        if benchmark_returns is not None:
            combined_result = self._add_benchmark_analysis(combined_result, benchmark_returns)

        return combined_result

    def _combine_chunk_results(self, all_chunks: List[Dict[str, Any]], symbol: str) -> BacktestResult:
        """Combine results from multiple chunks"""
        # Concatenate returns
        all_returns = []
        all_equity = []
        all_trades = []

        for chunk in all_chunks:
            all_returns.append(chunk['returns'])
            all_equity.append(chunk['equity'])
            all_trades.append(chunk['trades'])

        combined_returns = pd.concat(all_returns).sort_index()
        combined_equity = pd.concat(all_equity).sort_index()
        combined_trades = pd.concat(all_trades).ignore_index(drop=True)

        # Calculate comprehensive statistics
        stats = self._calculate_comprehensive_stats(combined_returns, combined_equity, combined_trades)

        return BacktestResult(
            strategy_name=f"Chunked Strategy - {symbol}",
            symbol=symbol,
            start_date=combined_returns.index[0].strftime('%Y-%m-%d'),
            end_date=combined_returns.index[-1].strftime('%Y-%m-%d'),
            total_return=stats['total_return'],
            annualized_return=stats['annualized_return'],
            sharpe_ratio=stats['sharpe_ratio'],
            sortino_ratio=stats['sortino_ratio'],
            max_drawdown=stats['max_drawdown'],
            calmar_ratio=stats['calmar_ratio'],
            win_rate=stats['win_rate'],
            profit_factor=stats['profit_factor'],
            total_trades=stats['total_trades'],
            avg_trade=stats['avg_trade'],
            benchmark_return=stats['benchmark_return'],
            alpha=stats['alpha'],
            beta=stats['beta'],
            information_ratio=stats['information_ratio'],
            trades=combined_trades,
            equity_curve=combined_equity,
            benchmark_equity=combined_equity,  # Will be updated later
            detailed_stats=stats,
            backtest_timestamp=datetime.now()
        )

    def _calculate_comprehensive_stats(self, returns: pd.Series, equity: pd.Series,
                                     trades: pd.DataFrame, benchmark_returns: Optional[pd.Series] = None) -> Dict[str, Any]:
        """Calculate comprehensive backtest statistics"""
        stats = {}

        # Basic return metrics
        stats['total_return'] = float((equity.iloc[-1] / equity.iloc[0]) - 1)
        stats['annualized_return'] = float(returns.mean() * 252)
        stats['volatility'] = float(returns.std() * np.sqrt(252))

        # Risk-adjusted metrics
        stats['sharpe_ratio'] = float(returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0.0

        # Sortino ratio (downside deviation)
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 0:
            downside_dev = downside_returns.std()
            stats['sortino_ratio'] = float(returns.mean() / downside_dev * np.sqrt(252)) if downside_dev > 0 else 0.0
        else:
            stats['sortino_ratio'] = np.inf

        # Maximum drawdown
        cumulative_returns = (1 + returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        stats['max_drawdown'] = float(drawdown.min())
        stats['calmar_ratio'] = float(stats['annualized_return'] / abs(stats['max_drawdown'])) if stats['max_drawdown'] != 0 else np.inf

        # Trade statistics
        if len(trades) > 0:
            # Win rate
            winning_trades = trades[trades['PnL'] > 0]
            stats['win_rate'] = float(len(winning_trades) / len(trades))

            # Average trade
            stats['avg_trade'] = float(trades['PnL'].mean())

            # Profit factor
            gross_profit = trades[trades['PnL'] > 0]['PnL'].sum()
            gross_loss = abs(trades[trades['PnL'] < 0]['PnL'].sum())
            stats['profit_factor'] = float(gross_profit / gross_loss) if gross_loss > 0 else np.inf

            # Trade statistics
            stats['total_trades'] = len(trades)
            stats['winning_trades'] = len(winning_trades)
            stats['losing_trades'] = len(trades) - len(winning_trades)
            stats['avg_win'] = float(winning_trades['PnL'].mean()) if len(winning_trades) > 0 else 0.0
            stats['avg_loss'] = float(trades[trades['PnL'] < 0]['PnL'].mean()) if len(trades[trades['PnL'] < 0]) > 0 else 0.0
            stats['largest_win'] = float(trades['PnL'].max())
            stats['largest_loss'] = float(trades['PnL'].min())

            # Trade duration
            stats['avg_trade_duration'] = float((trades['Exit Time'] - trades['Entry Time']).dt.days.mean())
        else:
            stats.update({
                'win_rate': 0.0,
                'avg_trade': 0.0,
                'profit_factor': 0.0,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'largest_win': 0.0,
                'largest_loss': 0.0,
                'avg_trade_duration': 0.0
            })

        # Distribution metrics
        stats['skewness'] = float(returns.skew())
        stats['kurtosis'] = float(returns.kurtosis())
        stats['var_95'] = float(np.percentile(returns, 5))
        stats['var_99'] = float(np.percentile(returns, 1))

        # Benchmark comparison
        if benchmark_returns is not None:
            aligned_returns, aligned_benchmark = returns.align(benchmark_returns, join='inner')
            excess_returns = aligned_returns - aligned_benchmark

            stats['benchmark_return'] = float(aligned_benchmark.mean() * 252)
            stats['excess_return'] = float(excess_returns.mean() * 252)

            # Alpha and Beta (using regression)
            if len(aligned_returns) > 30:
                from sklearn.linear_model import LinearRegression
                model = LinearRegression()
                model.fit(aligned_benchmark.values.reshape(-1, 1), aligned_returns.values)
                beta = model.coef_[0]
                alpha = model.intercept_ * 252  # Annualized

                stats['beta'] = float(beta)
                stats['alpha'] = float(alpha)

                # Information ratio
                if excess_returns.std() > 0:
                    stats['information_ratio'] = float(excess_returns.mean() / excess_returns.std() * np.sqrt(252))
                else:
                    stats['information_ratio'] = 0.0
            else:
                stats.update({'beta': 0.0, 'alpha': 0.0, 'information_ratio': 0.0, 'benchmark_return': 0.0})
        else:
            stats.update({'beta': 0.0, 'alpha': 0.0, 'information_ratio': 0.0, 'benchmark_return': 0.0})

        return stats

    def _calculate_benchmark_equity(self, benchmark_returns: Optional[pd.Series],
                                 length: int) -> pd.Series:
        """Calculate benchmark equity curve"""
        if benchmark_returns is None:
            return pd.Series([self.config.initial_cash] * length)

        # Calculate cumulative returns
        cumulative_returns = (1 + benchmark_returns).cumprod()
        benchmark_equity = self.config.initial_cash * cumulative_returns

        return benchmark_equity

    def _add_benchmark_analysis(self, result: BacktestResult,
                               benchmark_returns: Optional[pd.Series]) -> BacktestResult:
        """Add benchmark analysis to backtest result"""
        if benchmark_returns is None:
            return result

        # Recalculate with benchmark
        stats = self._calculate_comprehensive_stats(
            pd.Series(result.detailed_stats.get('returns', [])),
            result.equity_curve,
            result.trades,
            benchmark_returns
        )

        # Update result
        result.benchmark_return = stats['benchmark_return']
        result.alpha = stats['alpha']
        result.beta = stats['beta']
        result.information_ratio = stats['information_ratio']
        result.benchmark_equity = self._calculate_benchmark_equity(benchmark_returns, len(result.equity_curve))
        result.detailed_stats.update(stats)

        return result

    def backtest_multiple_strategies(self, market_data: pd.DataFrame,
                                   strategies: List[StrategySignal], symbol: str,
                                   benchmark_data: Optional[pd.DataFrame] = None) -> Dict[str, BacktestResult]:
        """Backtest multiple strategies simultaneously"""
        logger.info(f"Backtesting {len(strategies)} strategies for {symbol}")

        results = {}

        # Prepare benchmark once
        benchmark_returns = self._prepare_benchmark(benchmark_data, market_data)

        for strategy in strategies:
            try:
                result = self.backtest_strategy(market_data, strategy, symbol, benchmark_data)
                results[strategy.name] = result
                logger.info(f"Completed backtest for {strategy.name}")
            except Exception as e:
                logger.error(f"Error backtesting strategy {strategy.name}: {e}")

        return results

    def backtest_multiple_symbols(self, market_data_dict: Dict[str, pd.DataFrame],
                                 strategy_func: Callable, symbols: List[str],
                                 benchmark_data_dict: Optional[Dict[str, pd.DataFrame]] = None) -> Dict[str, BacktestResult]:
        """Backtest strategy across multiple symbols"""
        logger.info(f"Backtesting strategy across {len(symbols)} symbols")

        results = {}

        with ThreadPoolExecutor(max_workers=min(self.config.max_workers, len(symbols))) as executor:
            future_to_symbol = {}

            for symbol in symbols:
                if symbol not in market_data_dict:
                    logger.warning(f"No data available for {symbol}")
                    continue

                market_data = market_data_dict[symbol]
                benchmark_data = benchmark_data_dict.get(symbol) if benchmark_data_dict else None

                # Generate signals for this symbol
                signals = strategy_func(market_data, symbol)

                future = executor.submit(
                    self.backtest_strategy,
                    market_data, signals, symbol, benchmark_data
                )
                future_to_symbol[future] = symbol

            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    result = future.result()
                    results[symbol] = result
                    logger.info(f"Completed backtest for {symbol}")
                except Exception as e:
                    logger.error(f"Error backtesting {symbol}: {e}")

        return results

    def generate_backtest_report(self, results: Union[BacktestResult, Dict[str, BacktestResult]]) -> str:
        """Generate comprehensive backtest report"""
        if isinstance(results, BacktestResult):
            # Single strategy report
            return self._generate_single_report(results)
        else:
            # Multiple strategies report
            return self._generate_comparison_report(results)

    def _generate_single_report(self, result: BacktestResult) -> str:
        """Generate report for single strategy"""
        report = f"""
# Backtest Report: {result.strategy_name}

## Strategy Overview
- Symbol: {result.symbol}
- Period: {result.start_date} to {result.end_date}
- Initial Capital: ${self.config.initial_cash:,.2f}
- Commission: {self.config.commission*100:.2f}%
- Slippage: {self.config.slippage*100:.2f}%

## Performance Metrics
- Total Return: {result.total_return:.2%}
- Annualized Return: {result.annualized_return:.2%}
- Sharpe Ratio: {result.sharpe_ratio:.2f}
- Sortino Ratio: {result.sortino_ratio:.2f}
- Maximum Drawdown: {result.max_drawdown:.2%}
- Calmar Ratio: {result.calmar_ratio:.2f}

## Trading Statistics
- Total Trades: {result.total_trades}
- Win Rate: {result.win_rate:.2%}
- Profit Factor: {result.profit_factor:.2f}
- Average Trade: ${result.avg_trade:,.2f}
"""
        if result.benchmark_return != 0:
            report += f"""
## Benchmark Comparison
- Benchmark Return: {result.benchmark_return:.2%}
- Alpha: {result.alpha:.2%}
- Beta: {result.beta:.2f}
- Information Ratio: {result.information_ratio:.2f}
"""

        return report

    def _generate_comparison_report(self, results: Dict[str, BacktestResult]) -> str:
        """Generate comparison report for multiple strategies"""
        report = "# Strategy Comparison Report\n\n"

        # Create comparison table
        comparison_data = []
        for name, result in results.items():
            comparison_data.append({
                'Strategy': name,
                'Symbol': result.symbol,
                'Total Return': f"{result.total_return:.2%}",
                'Sharpe Ratio': f"{result.sharpe_ratio:.2f}",
                'Max Drawdown': f"{result.max_drawdown:.2%}",
                'Win Rate': f"{result.win_rate:.2%}",
                'Total Trades': result.total_trades
            })

        df = pd.DataFrame(comparison_data)
        report += df.to_string(index=False) + "\n\n"

        # Detailed reports for each strategy
        for name, result in results.items():
            report += f"## {name}\n"
            report += self._generate_single_report(result) + "\n"

        return report

    def save_backtest_results(self, results: Union[BacktestResult, Dict[str, BacktestResult]],
                            file_path: str):
        """Save backtest results to file"""
        if isinstance(results, BacktestResult):
            results_dict = {results.strategy_name: results}
        else:
            results_dict = results

        serializable_results = {}
        for name, result in results_dict.items():
            serializable_results[name] = {
                'strategy_name': result.strategy_name,
                'symbol': result.symbol,
                'start_date': result.start_date,
                'end_date': result.end_date,
                'total_return': result.total_return,
                'annualized_return': result.annualized_return,
                'sharpe_ratio': result.sharpe_ratio,
                'sortino_ratio': result.sortino_ratio,
                'max_drawdown': result.max_drawdown,
                'calmar_ratio': result.calmar_ratio,
                'win_rate': result.win_rate,
                'profit_factor': result.profit_factor,
                'total_trades': result.total_trades,
                'avg_trade': result.avg_trade,
                'benchmark_return': result.benchmark_return,
                'alpha': result.alpha,
                'beta': result.beta,
                'information_ratio': result.information_ratio,
                'detailed_stats': result.detailed_stats,
                'backtest_timestamp': result.backtest_timestamp.isoformat()
            }

        with open(file_path, 'w') as f:
            json.dump(serializable_results, f, indent=2)

        logger.info(f"Backtest results saved to {file_path}")

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Create configuration
    config = BacktestConfig(
        initial_cash=1000000,
        commission=0.001,
        chunk_size=50000,
        max_workers=4
    )

    # Create sample market data (5 years)
    dates = pd.date_range('2019-01-01', '2024-01-01', freq='D')
    n_days = len(dates)

    market_data = pd.DataFrame({
        'open': np.random.uniform(100, 500, n_days),
        'high': np.random.uniform(101, 505, n_days),
        'low': np.random.uniform(99, 495, n_days),
        'close': np.random.uniform(100, 500, n_days),
        'volume': np.random.randint(1000000, 10000000, n_days)
    }, index=dates)

    # Create sample strategy signals (SMA crossover)
    def generate_sma_signals(data: pd.DataFrame, symbol: str) -> StrategySignal:
        """Generate SMA crossover signals"""
        close = data['close']
        sma_short = close.rolling(window=20).mean()
        sma_long = close.rolling(window=50).mean()

        entries = sma_short > sma_long
        exits = sma_short < sma_long

        return StrategySignal(
            name=f"SMA_Crossover_{symbol}",
            entries=entries,
            exits=exits,
            parameters={'short_window': 20, 'long_window': 50},
            description="Simple Moving Average Crossover Strategy"
        )

    # Initialize backtesting engine
    engine = LongTermBacktestingEngine(config)

    # Generate signals
    signals = generate_sma_signals(market_data, "0700.HK")

    # Run backtest
    result = engine.backtest_strategy(market_data, signals, "0700.HK")

    # Print results
    print(engine.generate_backtest_report(result))

    # Save results
    engine.save_backtest_results(result, "backtest_results.json")
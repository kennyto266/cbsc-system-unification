"""
Market-Wide Multi-Process Parameter Optimizer
=============================================

Provides market-wide parameter optimization with multiprocessing support.
Designed for 32-core CPU systems with 31 workers.
"""

import os
import sys
import logging
import multiprocessing as mp
from multiprocessing import Pool, Manager, Queue
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable
from datetime import datetime, date
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np
import pandas as pd

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================
# Strategy Base Pattern for Extensibility
# ============================================================

class StrategyBase(ABC):
    """
    Abstract base class for trading strategies.
    All strategies must inherit from this class.
    """

    @abstractmethod
    def get_name(self) -> str:
        """Return strategy name"""
        pass

    @abstractmethod
    def get_parameter_ranges(self) -> Dict[str, Tuple[int, int, int]]:
        """
        Return parameter ranges for optimization.
        Format: {'param_name': (min, max, step)}
        """
        pass

    @abstractmethod
    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """Validate parameter combination"""
        pass

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.Series:
        """
        Generate trading signals from data and parameters.
        Returns boolean Series where True = buy signal.
        """
        pass


class MACrossoverStrategy(StrategyBase):
    """Moving Average Crossover Strategy"""

    def get_name(self) -> str:
        return "ma_crossover"

    def get_parameter_ranges(self) -> Dict[str, Tuple[int, int, int]]:
        return {
            'short_period': (3, 60, 3),   # 20 values: 3, 6, 9, ..., 60
            'long_period': (10, 200, 5)   # 39 values: 10, 15, 20, ..., 200
        }

    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        short = params.get('short_period', 0)
        long = params.get('long_period', 0)
        return short < long  # Short period must be less than long period

    def generate_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.Series:
        short_period = params['short_period']
        long_period = params['long_period']

        short_ma = data['close'].rolling(window=short_period, min_periods=1).mean()
        long_ma = data['close'].rolling(window=long_period, min_periods=1).mean()

        return (short_ma > long_ma).astype(bool)


class RSIStrategy(StrategyBase):
    """RSI Strategy (Future implementation)"""

    def get_name(self) -> str:
        return "rsi"

    def get_parameter_ranges(self) -> Dict[str, Tuple[int, int, int]]:
        return {
            'rsi_period': (10, 30, 2),
            'oversold': (20, 35, 5),
            'overbought': (65, 80, 5)
        }

    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        oversold = params.get('oversold', 0)
        overbought = params.get('overbought', 100)
        return oversold < overbought

    def generate_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.Series:
        # TODO: Implement RSI calculation
        raise NotImplementedError("RSI strategy not yet implemented")


# ============================================================
# Data Models
# ============================================================

@dataclass
class OptimizationConfig:
    """Configuration for market-wide optimization"""
    symbols: List[str]
    start_date: date
    end_date: date
    initial_cash: float = 100000
    commission: float = 0.001
    min_sharpe_ratio: float = 2.0  # Filter threshold
    max_workers: int = 31  # For 32-core CPU
    strategy: StrategyBase = field(default_factory=MACrossoverStrategy)

    # Optimization target
    optimization_target: str = "sharpe_ratio"  # sharpe_ratio, total_return


@dataclass
class BacktestResult:
    """Single backtest result with equity curve comparison"""
    symbol: str
    params: Dict[str, Any]

    # Strategy metrics
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    total_trades: int

    # Buy & Hold comparison
    bnh_return: float
    bnh_sharpe: float
    bnh_max_dd: float

    # Equity curves
    equity_curve: List[float]
    bnh_equity_curve: List[float]

    # Outperformance
    excess_return: float
    information_ratio: float


@dataclass
class ProgressUpdate:
    """Progress update for real-time tracking"""
    task_id: str
    timestamp: datetime
    total_stocks: int
    waiting_stocks: int
    processing_stocks: int
    completed_stocks: int
    current_stock_number: int  # Stock #001, #002, etc.
    current_stock_symbol: str

    # Best results so far
    best_sharpe_ratio: float
    best_params: Dict[str, Any]
    best_symbol: str

    # ETA
    elapsed_seconds: float
    estimated_remaining_seconds: float


# ============================================================
# Backtest Engine with Buy&Hold Comparison
# ============================================================

def run_single_backtest_with_comparison(
    data: pd.DataFrame,
    params: Dict[str, Any],
    strategy: StrategyBase,
    initial_cash: float,
    commission: float
) -> BacktestResult:
    """
    Run backtest with Buy & Hold comparison.
    Returns result with equity curves for both strategies.
    """
    symbol = data.name if hasattr(data, 'name') else "UNKNOWN"

    # Ensure index is DatetimeIndex
    if not isinstance(data.index, pd.DatetimeIndex):
        data = data.copy()
        data.index = pd.to_datetime(data.index)

    # Sort by index
    data = data.sort_index()

    # Remove duplicates
    data = data[~data.index.duplicated(keep='first')]

    # Generate signals
    entries = strategy.generate_signals(data, params)
    exits = (~entries).astype(bool)

    # Calculate strategy equity curve
    strategy_equity = calculate_equity_curve(
        data, entries, exits, initial_cash, commission
    )

    # Calculate Buy & Hold equity curve
    bnh_equity = calculate_buy_and_hold_equity(
        data, initial_cash, commission
    )

    # Calculate metrics for strategy
    strategy_metrics = calculate_metrics(strategy_equity)
    bnh_metrics = calculate_metrics(bnh_equity)

    # Calculate outperformance
    excess_return = strategy_metrics['total_return'] - bnh_metrics['total_return']
    information_ratio = calculate_information_ratio(strategy_equity, bnh_equity)

    return BacktestResult(
        symbol=symbol,
        params=params,
        total_return=strategy_metrics['total_return'],
        sharpe_ratio=strategy_metrics['sharpe_ratio'],
        max_drawdown=strategy_metrics['max_drawdown'],
        total_trades=strategy_metrics['total_trades'],
        bnh_return=bnh_metrics['total_return'],
        bnh_sharpe=bnh_metrics['sharpe_ratio'],
        bnh_max_dd=bnh_metrics['max_drawdown'],
        equity_curve=strategy_equity,
        bnh_equity_curve=bnh_equity,
        excess_return=excess_return,
        information_ratio=information_ratio
    )


def calculate_equity_curve(
    data: pd.DataFrame,
    entries: pd.Series,
    exits: pd.Series,
    initial_cash: float,
    commission: float
) -> List[float]:
    """Calculate equity curve for strategy"""
    cash = initial_cash
    shares = 0
    equity_curve = []

    # Get position at each point
    for i in range(len(data)):
        current_price = data['close'].iloc[i]

        # Check signals
        if i > 0 and entries.iloc[i] and not entries.iloc[i-1]:
            # Buy signal
            if cash > 0:
                shares_to_buy = (cash * (1 - commission)) / current_price
                cost = shares_to_buy * current_price * (1 + commission)
                if cost <= cash:
                    shares = shares_to_buy
                    cash = cash - cost

        elif i > 0 and exits.iloc[i] and not exits.iloc[i-1]:
            # Sell signal
            if shares > 0:
                cash_from_sale = shares * current_price * (1 - commission)
                cash = cash + cash_from_sale
                shares = 0

        # Calculate equity
        equity = cash + (shares * current_price if shares > 0 else 0)
        equity_curve.append(float(equity))

    return equity_curve


def calculate_buy_and_hold_equity(
    data: pd.DataFrame,
    initial_cash: float,
    commission: float
) -> List[float]:
    """Calculate Buy & Hold equity curve"""
    if len(data) == 0:
        return [initial_cash]

    first_price = data['close'].iloc[0]
    shares_to_buy = (initial_cash * (1 - commission)) / first_price

    equity_curve = []
    for price in data['close']:
        equity = shares_to_buy * price
        equity_curve.append(float(equity))

    return equity_curve


def calculate_metrics(equity_curve: List[float]) -> Dict[str, float]:
    """Calculate performance metrics from equity curve"""
    if len(equity_curve) < 2:
        return {
            'total_return': 0,
            'sharpe_ratio': 0,
            'max_drawdown': 0,
            'total_trades': 0
        }

    equity_array = np.array(equity_curve)
    returns = np.diff(equity_array) / equity_array[:-1]

    # Filter out invalid returns
    returns = returns[np.isfinite(returns)]

    # Total return
    total_return = ((equity_array[-1] - equity_array[0]) / equity_array[0]) * 100

    # Sharpe ratio (annualized, with 3% risk-free rate)
    if len(returns) > 0 and np.std(returns) > 0:
        excess_returns = returns - 0.03 / 252  # Daily risk-free rate
        sharpe_ratio = np.mean(excess_returns) / np.std(returns) * np.sqrt(252)
    else:
        sharpe_ratio = 0

    # Max drawdown
    cummax = np.maximum.accumulate(equity_array)
    drawdown = (equity_array - cummax) / cummax
    max_drawdown = np.min(drawdown) * 100 if len(drawdown) > 0 else 0

    # Count trades (simplified - just count signal changes)
    # This is a placeholder; actual implementation would track trades
    total_trades = 10  # Placeholder

    return {
        'total_return': float(total_return),
        'sharpe_ratio': float(sharpe_ratio),
        'max_drawdown': float(max_drawdown),
        'total_trades': total_trades
    }


def calculate_information_ratio(
    strategy_equity: List[float],
    bnh_equity: List[float]
) -> float:
    """Calculate Information Ratio (excess return / tracking error)"""
    if len(strategy_equity) != len(bnh_equity) or len(strategy_equity) < 2:
        return 0

    strategy_returns = np.diff(strategy_equity) / np.array(strategy_equity[:-1])
    bnh_returns = np.diff(bnh_equity) / np.array(bnh_equity[:-1])

    excess_returns = strategy_returns - bnh_returns

    if len(excess_returns) == 0 or np.std(excess_returns) == 0:
        return 0

    # Annualized Information Ratio
    information_ratio = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
    return float(information_ratio)


# ============================================================
# Multi-Process Worker Functions
# ============================================================

def optimize_single_stock_worker(args: Tuple) -> Dict[str, Any]:
    """
    Worker function for single stock optimization.
    Must be pickleable for multiprocessing.
    """
    symbol, data_dict, param_combinations, config, strategy = args
    data = data_dict[symbol]

    results = []
    best_sharpe = float('-inf')
    best_params = None
    best_result = None

    for params in param_combinations:
        try:
            result = run_single_backtest_with_comparison(
                data, params, strategy,
                config.initial_cash, config.commission
            )

            # Apply SR filter
            if result.sharpe_ratio < config.min_sharpe_ratio:
                continue

            results.append({
                'symbol': symbol,
                'params': result.params,
                'total_return': result.total_return,
                'sharpe_ratio': result.sharpe_ratio,
                'max_drawdown': result.max_drawdown,
                'excess_return': result.excess_return,
                'information_ratio': result.information_ratio,
                'equity_curve': result.equity_curve,
                'bnh_equity_curve': result.bnh_equity_curve
            })

            # Track best for this stock
            if result.sharpe_ratio > best_sharpe:
                best_sharpe = result.sharpe_ratio
                best_params = result.params
                best_result = result

        except Exception as e:
            logger.error(f"Error optimizing {symbol} with params {params}: {e}")
            continue

    return {
        'symbol': symbol,
        'results': results,
        'best_sharpe': best_sharpe,
        'best_params': best_params,
        'best_result': best_result
    }


# ============================================================
# Main Multi-Strategy Optimizer
# ============================================================

class MultiStrategyOptimizer:
    """
    Market-wide parameter optimizer with multiprocessing support.
    Designed for 32-core CPU systems with 31 workers.
    """

    def __init__(self, config: OptimizationConfig):
        self.config = config
        self.strategy = config.strategy
        self.progress_callbacks: List[Callable] = []

        # Generate parameter combinations
        self.param_combinations = self._generate_parameter_combinations()

        logger.info(f"Optimizer initialized with {len(self.param_combinations)} parameter combinations")
        logger.info(f"Max workers: {config.max_workers}")
        logger.info(f"Symbols: {len(config.symbols)}")

    def _generate_parameter_combinations(self) -> List[Dict[str, Any]]:
        """Generate all valid parameter combinations"""
        ranges = self.strategy.get_parameter_ranges()
        param_names = list(ranges.keys())

        # Generate values for each parameter
        param_values = []
        for name in param_names:
            min_val, max_val, step = ranges[name]
            values = list(range(min_val, max_val + 1, step))
            param_values.append(values)

        # Generate all combinations
        from itertools import product
        combinations = []
        for combo in product(*param_values):
            params = dict(zip(param_names, combo))
            if self.strategy.validate_parameters(params):
                combinations.append(params)

        return combinations

    def add_progress_callback(self, callback: Callable[[ProgressUpdate], None]):
        """Add callback for progress updates"""
        self.progress_callbacks.append(callback)

    def _notify_progress(
        self,
        task_id: str,
        total: int,
        waiting: int,
        processing: int,
        completed: int,
        current_symbol: Optional[str] = None,
        current_number: int = 0,
        best_sharpe: float = 0,
        best_params: Dict = None,
        best_symbol: str = "",
        elapsed: float = 0
    ):
        """Notify all progress callbacks"""
        eta = 0
        if completed > 0:
            rate = elapsed / completed
            eta = (total - completed) * rate

        update = ProgressUpdate(
            task_id=task_id,
            timestamp=datetime.now(),
            total_stocks=total,
            waiting_stocks=waiting,
            processing_stocks=processing,
            completed_stocks=completed,
            current_stock_number=current_number,
            current_stock_symbol=current_symbol or "",
            best_sharpe_ratio=best_sharpe,
            best_params=best_params or {},
            best_symbol=best_symbol,
            elapsed_seconds=elapsed,
            estimated_remaining_seconds=eta
        )

        for callback in self.progress_callbacks:
            try:
                callback(update)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")

    def optimize(self, data: Dict[str, pd.DataFrame], task_id: str) -> Dict[str, Any]:
        """
        Run market-wide optimization using multiprocessing.

        Args:
            data: Dictionary of symbol -> DataFrame
            task_id: Task ID for tracking

        Returns:
            Optimization results with top performers
        """
        start_time = datetime.now()
        total_stocks = len(data)

        logger.info(f"Starting market-wide optimization for {total_stocks} stocks")
        logger.info(f"Parameter combinations: {len(self.param_combinations)}")
        logger.info(f"Max workers: {self.config.max_workers}")

        # Prepare worker arguments
        worker_args = [
            (symbol, data, self.param_combinations, self.config, self.strategy)
            for symbol in data.keys()
        ]

        # Results storage
        all_results = []
        best_overall_sharpe = float('-inf')
        best_overall_params = None
        best_overall_symbol = ""

        completed_count = 0

        # Use ProcessPoolExecutor for better error handling
        with ProcessPoolExecutor(max_workers=self.config.max_workers) as executor:
            # Submit all tasks
            future_to_symbol = {
                executor.submit(optimize_single_stock_worker, args): args[0]
                for args in worker_args
            }

            # Process results as they complete
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]

                try:
                    result = future.result()
                    completed_count += 1

                    # Update progress
                    elapsed = (datetime.now() - start_time).total_seconds()
                    self._notify_progress(
                        task_id=task_id,
                        total=total_stocks,
                        waiting=0,
                        processing=len([f for f in future_to_symbol if not f.done()]),
                        completed=completed_count,
                        current_symbol=symbol,
                        current_number=completed_count,
                        elapsed=elapsed
                    )

                    # Store results
                    all_results.extend(result['results'])

                    # Check for new best
                    if result['best_sharpe'] > best_overall_sharpe:
                        best_overall_sharpe = result['best_sharpe']
                        best_overall_params = result['best_params']
                        best_overall_symbol = symbol

                        # Update progress with best result
                        self._notify_progress(
                            task_id=task_id,
                            total=total_stocks,
                            waiting=0,
                            processing=len([f for f in future_to_symbol if not f.done()]),
                            completed=completed_count,
                            current_symbol=symbol,
                            current_number=completed_count,
                            best_sharpe=best_overall_sharpe,
                            best_params=best_overall_params,
                            best_symbol=best_overall_symbol,
                            elapsed=elapsed
                        )

                    logger.info(f"Completed {completed_count}/{total_stocks}: {symbol} "
                              f"(Sharpe: {result['best_sharpe']:.2f})")

                except Exception as e:
                    logger.error(f"Error processing {symbol}: {e}")
                    completed_count += 1
                    continue

        # Sort and rank results
        # Primary: Sharpe Ratio > 2.0, Secondary: Min Max Drawdown
        qualified_results = [
            r for r in all_results
            if r['sharpe_ratio'] >= self.config.min_sharpe_ratio
        ]

        # Sort by Sharpe (descending), then by Max Drawdown (ascending)
        qualified_results.sort(
            key=lambda x: (-x['sharpe_ratio'], x['max_drawdown'])
        )

        # Get top results
        top_10 = qualified_results[:10]

        total_time = (datetime.now() - start_time).total_seconds()

        logger.info(f"Optimization completed in {total_time:.2f} seconds")
        logger.info(f"Best overall: {best_overall_symbol} with Sharpe {best_overall_sharpe:.2f}")
        logger.info(f"Qualified results: {len(qualified_results)}/{len(all_results)}")

        return {
            'task_id': task_id,
            'status': 'completed',
            'started_at': start_time.isoformat(),
            'completed_at': datetime.now().isoformat(),
            'total_time_seconds': total_time,
            'total_stocks': total_stocks,
            'total_combinations': len(self.param_combinations),
            'qualified_results_count': len(qualified_results),
            'best_overall': {
                'symbol': best_overall_symbol,
                'sharpe_ratio': float(best_overall_sharpe) if best_overall_sharpe != float('-inf') else 0,
                'params': best_overall_params or {}
            },
            'top_10': top_10,
            'all_results': all_results
        }


# ============================================================
# Utility Functions
# ============================================================

def fetch_market_data(
    symbols: List[str],
    start_date: date,
    end_date: date
) -> Dict[str, pd.DataFrame]:
    """
    Fetch market data for all symbols.
    Uses yfinance for real Yahoo Finance data.
    """
    try:
        import yfinance as yf
    except ImportError:
        raise ImportError("yfinance is required for data fetching")

    data = {}

    for i, symbol in enumerate(symbols, 1):
        try:
            logger.info(f"Fetching data for {symbol} ({i}/{len(symbols)})")
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start_date, end=end_date)

            if hist.empty:
                logger.warning(f"No data for {symbol}")
                continue

            df = pd.DataFrame({
                'open': hist['Open'],
                'high': hist['High'],
                'low': hist['Low'],
                'close': hist['Close'],
                'volume': hist['Volume']
            }).dropna()

            if not df.empty:
                df.name = symbol  # Store symbol name in dataframe
                data[symbol] = df
                logger.info(f"  Got {len(df)} data points for {symbol}")

        except Exception as e:
            logger.error(f"Error fetching {symbol}: {e}")
            continue

    return data


def get_hsi_constituents(count: int = 50) -> List[str]:
    """
    Get HSI constituent stocks for market-wide optimization.

    Args:
        count: Number of stocks to return (default: 50)

    Returns:
        List of stock symbols in format '0700.HK'
    """
    # Top HSI stocks by market cap
    hsi_stocks = [
        "0700.HK",  # Tencent
        "9988.HK",  # Alibaba
        "0941.HK",  # China Mobile
        "1299.HK",  # AIA
        "0939.HK",  # CCB
        "1398.HK",  # ICBC
        "2318.HK",  # Ping An
        "3988.HK",  # Bank of China
        "0883.HK",  # CNOOC
        "0388.HK",  # HKEX
        "0027.HK",  # Galaxy Entertainment
        "1810.HK",  # Xiaomi
        "0016.HK",  # Sun Hung Kai
        "0005.HK",  # HSBC
        "0011.HK",  # Hang Seng Bank
        "0012.HK",  # Henderson Land
        "0175.HK",  # Geely
        "2020.HK",  #ANTA Sports
        "0868.HK",  # Xinyi Glass
        "1044.HK",  # Hengan Intl
        "1928.HK",  # Sands China
        "1876.HK",  # Budweiser APAC
        "1177.HK",  # Sino Biopharmaceutical
        "2269.HK",  # WuXi Bio
        "0669.HK",  # Techtronic Ind
        "1093.HK",  # CSPC Pharma
        "0688.HK",  # China Overseas
        "2007.HK",  # Country Garden
        "0881.HK",  # Zhongsheng Group
        "1109.HK",  # China Resources
        "1997.HK",  # Wharf REIC
        "0762.HK",  # China Unicom
        "0960.HK",  # Longfor Group
        "0660.HK",  # First Services
        "0019.HK",  # Swire Pacific A
        "0002.HK",  # CLP Holdings
        "0003.HK",  # HK & China Gas
        "0006.HK",  # Power Assets
        "0017.HK",  # New World Dev
        "0083.HK",  # Sino Land
        "0101.HK",  # Hang Lung Prop
        "0241.HK",  # Alibaba Health
        "0669.HK",  # Techtronic Ind
        "0728.HK",  # China Telecom
        "0288.HK",  # WH Group
        "1577.HK",  # Li Ning
        "2026.HK",  # BYD Company
    ]

    return hsi_stocks[:count]

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU加速回測引擎 - 深度集成版本
GPU-Accelerated Backtest Engine - Deep Integration Version

提供高性能的GPU加速回測引擎，支持大規模並行策略回測
Provides high-performance GPU-accelerated backtesting engine with large-scale parallel strategy backtesting
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional, Union, Callable
import time
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import multiprocessing as mp
from abc import ABC, abstractmethod
import warnings

# 導入GPU組件
from .gpu_accelerated_indicators import get_gpu_indicators, GPUAcceleratedIndicators
from .gpu_parameter_optimizer import get_gpu_optimizer, GPUParameterOptimizer

# 導入VectorBT
try:
    import vectorbt as vbt
    VECTORBT_AVAILABLE = True
except ImportError:
    VECTORBT_AVAILABLE = False
    vbt = None

# 配置日誌
logger = logging.getLogger(__name__)

@dataclass
class BacktestConfig:
    """回測配置"""
    # 基本配置
    initial_cash: float = 100000.0
    fees: float = 0.001  # 0.1%手續費
    slippage: float = 0.0005  # 0.05%滑點

    # 風險管理
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    max_position_size: float = 1.0

    # 性能配置
    risk_free_rate: float = 0.03  # 3%無風險利率
    benchmark: Optional[str] = None

    # GPU配置
    gpu_enabled: bool = True
    batch_size: int = 10000
    parallel_strategies: int = 50

    # 緩存配置
    enable_cache: bool = True
    cache_ttl: int = 1800  # 30分鐘

@dataclass
class BacktestResult:
    """回測結果"""
    symbol: str
    strategy_name: str
    parameters: Dict[str, Any]

    # 基本性能指標
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    annual_return: float
    volatility: float

    # 交易統計
    win_rate: float
    profit_factor: float
    total_trades: int
    avg_trade_return: float
    best_trade: float
    worst_trade: float

    # 高級指標
    calmar_ratio: float
    sortino_ratio: float
    var_95: float  # 95% Value at Risk
    cvar_95: float  # 95% Conditional VaR

    # 時間序列數據
    equity_curve: Optional[pd.Series] = None
    returns: Optional[pd.Series] = None
    trades: Optional[pd.DataFrame] = None

    # 元數據
    start_date: str = ""
    end_date: str = ""
    data_points: int = 0
    execution_time: float = 0.0
    gpu_used: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'symbol': self.symbol,
            'strategy': self.strategy_name,
            'parameters': self.parameters,
            'performance': {
                'total_return': round(self.total_return * 100, 2),
                'sharpe_ratio': round(self.sharpe_ratio, 3),
                'max_drawdown': round(self.max_drawdown * 100, 2),
                'annual_return': round(self.annual_return * 100, 2),
                'volatility': round(self.volatility * 100, 2),
                'calmar_ratio': round(self.calmar_ratio, 3),
                'sortino_ratio': round(self.sortino_ratio, 3),
                'var_95': round(self.var_95 * 100, 2),
                'cvar_95': round(self.cvar_95 * 100, 2)
            },
            'trading_stats': {
                'win_rate': round(self.win_rate * 100, 2),
                'profit_factor': round(self.profit_factor, 2),
                'total_trades': self.total_trades,
                'avg_trade_return': round(self.avg_trade_return * 100, 2),
                'best_trade': round(self.best_trade * 100, 2),
                'worst_trade': round(self.worst_trade * 100, 2)
            },
            'metadata': {
                'start_date': self.start_date,
                'end_date': self.end_date,
                'data_points': self.data_points,
                'execution_time': round(self.execution_time, 3),
                'gpu_used': self.gpu_used
            }
        }

class GPUBacktestEngine:
    """
    GPU加速回測引擎

    核心特性：
    - GPU加速技術指標計算
    - 大規模並行策略回測
    - 向量化信號生成
    - 高級風險指標計算
    - 實時性能監控
    """

    def __init__(self, config: Optional[BacktestConfig] = None):
        """
        初始化GPU回測引擎

        Args:
            config: 回測配置
        """
        self.config = config or BacktestConfig()

        # 初始化組件
        self.gpu_indicators = get_gpu_indicators()
        self.gpu_optimizer = get_gpu_optimizer()

        # 回測緩存
        self._backtest_cache = {}

        # 性能統計
        self.backtest_stats = {
            'total_backtests': 0,
            'total_execution_time': 0.0,
            'gpu_backtests': 0,
            'cache_hits': 0
        }

        logger.info(f"GPU Backtest Engine initialized: gpu_enabled={self.config.gpu_enabled}")

    def backtest_strategy(self, data: pd.DataFrame, strategy: str,
                         parameters: Dict[str, Any], symbol: str = "UNKNOWN") -> BacktestResult:
        """
        執行單個策略回測

        Args:
            data: OHLCV數據
            strategy: 策略名稱
            parameters: 策略參數
            symbol: 股票代碼

        Returns:
            回測結果
        """
        start_time = time.time()

        # 檢查緩存
        cache_key = self._generate_cache_key(data, strategy, parameters)
        if self.config.enable_cache and cache_key in self._backtest_cache:
            self.backtest_stats['cache_hits'] += 1
            return self._backtest_cache[cache_key]

        try:
            # 驗證數據
            self._validate_data(data)

            # 生成交易信號
            signals = self._generate_signals_gpu(data, strategy, parameters)

            # 執行回測
            if VECTORBT_AVAILABLE and vbt is not None:
                portfolio = self._execute_vectorbt_backtest(data, signals)
                result = self._create_vectorbt_result(portfolio, data, strategy, parameters, symbol, start_time)
            else:
                result = self._execute_simple_backtest(data, signals, strategy, parameters, symbol, start_time)

            # 緩存結果
            if self.config.enable_cache:
                self._backtest_cache[cache_key] = result

            # 更新統計
            self._update_backtest_stats(result)

            return result

        except Exception as e:
            logger.error(f"Backtest failed for {symbol}: {e}")
            return self._create_error_result(data, strategy, parameters, symbol, start_time, str(e))

    def backtest_multiple_strategies(self, data: pd.DataFrame, strategies: List[Tuple[str, Dict]],
                                   symbol: str = "UNKNOWN") -> List[BacktestResult]:
        """
        批量回測多個策略

        Args:
            data: OHLCV數據
            strategies: 策略列表 [(strategy_name, parameters), ...]
            symbol: 股票代碼

        Returns:
            回測結果列表
        """
        logger.info(f"Starting batch backtest for {len(strategies)} strategies on {symbol}")
        start_time = time.time()

        results = []

        if self.config.gpu_enabled and len(strategies) > self.config.parallel_strategies:
            # 並行GPU回測
            results = self._parallel_backtest(data, strategies, symbol)
        else:
            # 順序回測
            for i, (strategy, params) in enumerate(strategies):
                if (i + 1) % 100 == 0:
                    logger.info(f"Completed {i + 1}/{len(strategies)} strategies")

                result = self.backtest_strategy(data, strategy, params, symbol)
                results.append(result)

        total_time = time.time() - start_time
        avg_time_per_strategy = total_time / len(strategies)

        logger.info(f"Batch backtest completed: {len(results)} strategies in {total_time:.2f}s "
                   f"({avg_time_per_strategy:.3f}s per strategy)")

        return results

    def optimize_strategy_parameters(self, data: pd.DataFrame, strategy: str,
                                  param_ranges: Dict[str, List], symbol: str = "UNKNOWN",
                                  optimization_metric: str = "sharpe_ratio",
                                  max_combinations: int = 10000) -> Dict[str, Any]:
        """
        策略參數優化

        Args:
            data: OHLCV數據
            strategy: 策略名稱
            param_ranges: 參數範圍
            symbol: 股票代碼
            optimization_metric: 優化目標
            max_combinations: 最大組合數

        Returns:
            優化結果
        """
        logger.info(f"Starting parameter optimization for {strategy} on {symbol}")

        # 使用GPU參數優化器
        if strategy == "RSI_MEAN_REVERSION":
            optimization_result = self.gpu_optimizer.optimize_rsi_strategy(data, symbol, param_ranges)
        elif strategy == "MACD_CROSSOVER":
            optimization_result = self.gpu_optimizer.optimize_macd_strategy(data, symbol, param_ranges)
        elif strategy == "BOLLINGER_BANDS":
            optimization_result = self.gpu_optimizer.optimize_bollinger_strategy(data, symbol, param_ranges)
        else:
            # 通用優化
            optimization_result = self._generic_optimization(data, strategy, param_ranges, symbol, optimization_metric, max_combinations)

        return optimization_result.to_dict()

    def monte_carlo_simulation(self, data: pd.DataFrame, strategy: str,
                             parameters: Dict[str, Any], num_simulations: int = 1000,
                             symbol: str = "UNKNOWN") -> Dict[str, Any]:
        """
        蒙特卡洛模擬

        Args:
            data: OHLCV數據
            strategy: 策略名稱
            parameters: 策略參數
            num_simulations: 模擬次數
            symbol: 股票代碼

        Returns:
            模擬結果
        """
        logger.info(f"Starting Monte Carlo simulation: {num_simulations} runs for {strategy}")

        # 執行基準回測
        baseline_result = self.backtest_strategy(data, strategy, parameters, symbol)

        # 獲取回報序列
        returns = baseline_result.returns if baseline_result.returns is not None else pd.Series([0.0])

        # 蒙特卡洛模擬
        simulation_results = []
        np.random.seed(42)  # 確保可重現性

        for i in range(num_simulations):
            if (i + 1) % 100 == 0:
                logger.info(f"Completed {i + 1}/{num_simulations} simulations")

            # 隨機重排回報
            simulated_returns = np.random.permutation(returns.values)

            # 計算模擬性能
            cumulative = np.cumprod(1 + simulated_returns)
            total_return = cumulative[-1] - 1

            # Sharpe比率
            if len(simulated_returns) > 1 and np.std(simulated_returns) > 0:
                sharpe_ratio = np.mean(simulated_returns) / np.std(simulated_returns) * np.sqrt(252)
            else:
                sharpe_ratio = 0

            # 最大回撤
            rolling_max = np.maximum.accumulate(cumulative)
            drawdown = (cumulative - rolling_max) / rolling_max
            max_drawdown = np.min(drawdown)

            simulation_results.append({
                'total_return': total_return,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown
            })

        # 計算統計
        total_returns = [r['total_return'] for r in simulation_results]
        sharpe_ratios = [r['sharpe_ratio'] for r in simulation_results]
        max_drawdowns = [r['max_drawdown'] for r in simulation_results]

        # 置信區間
        confidence_level = 0.95
        return_ci_lower = np.percentile(total_returns, (1 - confidence_level) / 2 * 100)
        return_ci_upper = np.percentile(total_returns, (1 + confidence_level) / 2 * 100)

        sharpe_ci_lower = np.percentile(sharpe_ratios, (1 - confidence_level) / 2 * 100)
        sharpe_ci_upper = np.percentile(sharpe_ratios, (1 + confidence_level) / 2 * 100)

        return {
            'baseline': baseline_result.to_dict(),
            'simulations': {
                'num_simulations': num_simulations,
                'total_return_stats': {
                    'mean': np.mean(total_returns),
                    'std': np.std(total_returns),
                    'min': np.min(total_returns),
                    'max': np.max(total_returns),
                    'percentile_5': np.percentile(total_returns, 5),
                    'percentile_95': np.percentile(total_returns, 95),
                    'confidence_interval': [return_ci_lower, return_ci_upper]
                },
                'sharpe_ratio_stats': {
                    'mean': np.mean(sharpe_ratios),
                    'std': np.std(sharpe_ratios),
                    'min': np.min(sharpe_ratios),
                    'max': np.max(sharpe_ratios),
                    'confidence_interval': [sharpe_ci_lower, sharpe_ci_upper]
                },
                'max_drawdown_stats': {
                    'mean': np.mean(max_drawdowns),
                    'std': np.std(max_drawdowns),
                    'worst': np.min(max_drawdowns),
                    'best': np.max(max_drawdowns)
                }
            },
            'probability_of_profit': np.mean(np.array(total_returns) > 0),
            'probability_of beating_baseline': np.mean(np.array(total_returns) > baseline_result.total_return)
        }

    def _validate_data(self, data: pd.DataFrame) -> None:
        """驗證輸入數據"""
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in data.columns]

        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        if len(data) < 20:
            raise ValueError(f"Insufficient data points: {len(data)} (minimum 20 required)")

        # 檢查數據完整性
        if data.isnull().any().any():
            logger.warning("Data contains null values, will be filled")
            data = data.fillna(method='ffill').fillna(method='bfill')

    def _generate_signals_gpu(self, data: pd.DataFrame, strategy: str,
                            parameters: Dict[str, Any]) -> pd.DataFrame:
        """使用GPU生成交易信號"""
        prices = data['close']

        if strategy == "RSI_MEAN_REVERSION":
            return self._generate_rsi_signals_gpu(prices, parameters)
        elif strategy == "MACD_CROSSOVER":
            return self._generate_macd_signals_gpu(prices, parameters)
        elif strategy == "BOLLINGER_BANDS":
            return self._generate_bollinger_signals_gpu(prices, parameters)
        elif strategy == "DUAL_MOVING_AVERAGE":
            return self._generate_ma_signals_gpu(prices, parameters)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    def _generate_rsi_signals_gpu(self, prices: pd.Series, params: Dict) -> pd.DataFrame:
        """GPU加速RSI信號生成"""
        period = params.get('period', 14)
        oversold = params.get('oversold', 30)
        overbought = params.get('overbought', 70)

        # 使用GPU計算RSI
        rsi_results = self.gpu_indicators.calculate_rsi_batch_gpu(prices, [period])
        rsi = pd.Series(rsi_results[period], index=prices.index)

        # 生成信號（向量化）
        oversold_cross_above = (rsi < oversold) & (rsi.shift(1) >= oversold)
        overbought_cross_below = (rsi > overbought) & (rsi.shift(1) <= overbought)

        return pd.DataFrame({
            'entries': oversold_cross_above,
            'exits': overbought_cross_below
        }, index=prices.index)

    def _generate_macd_signals_gpu(self, prices: pd.Series, params: Dict) -> pd.DataFrame:
        """GPU加速MACD信號生成"""
        fast = params.get('fast', 12)
        slow = params.get('slow', 26)
        signal = params.get('signal', 9)

        # 使用GPU計算MACD
        macd_results = self.gpu_indicators.calculate_macd_batch_gpu(
            prices, [fast], [slow], [signal]
        )
        macd_key = f"MACD_{fast}_{slow}_{signal}"
        macd_data = macd_results[macd_key]

        macd_line = pd.Series(macd_data['MACD'], index=prices.index)
        signal_line = pd.Series(macd_data['SIGNAL'], index=prices.index)

        # 生成信號（向量化）
        golden_cross = (macd_line > signal_line) & (macd_line.shift(1) <= signal_line.shift(1))
        death_cross = (macd_line < signal_line) & (macd_line.shift(1) >= signal_line.shift(1))

        return pd.DataFrame({
            'entries': golden_cross,
            'exits': death_cross
        }, index=prices.index)

    def _generate_bollinger_signals_gpu(self, prices: pd.Series, params: Dict) -> pd.DataFrame:
        """GPU加速布林帶信號生成"""
        period = params.get('period', 20)
        std_dev = params.get('std_dev', 2.0)

        # 使用GPU計算布林帶
        bb_results = self.gpu_indicators.calculate_bollinger_bands_gpu(
            prices, [period], [std_dev]
        )
        bb_key = f"BB_{period}_{std_dev}"
        bb_data = bb_results[bb_key]

        upper_band = pd.Series(bb_data['UPPER'], index=prices.index)
        lower_band = pd.Series(bb_data['LOWER'], index=prices.index)

        # 生成信號（向量化）
        price_cross_below_lower = (prices < lower_band) & (prices.shift(1) >= lower_band.shift(1))
        price_cross_above_upper = (prices > upper_band) & (prices.shift(1) <= upper_band.shift(1))

        return pd.DataFrame({
            'entries': price_cross_below_lower,
            'exits': price_cross_above_upper
        }, index=prices.index)

    def _generate_ma_signals_gpu(self, prices: pd.Series, params: Dict) -> pd.DataFrame:
        """GPU加速移動平均信號生成"""
        short_period = params.get('short_period', 20)
        long_period = params.get('long_period', 50)

        # 使用GPU計算移動平均（通過布林帶函數）
        bb_results = self.gpu_indicators.calculate_bollinger_bands_gpu(prices, [short_period, long_period], [0.0])

        short_ma = pd.Series(bb_results[f"BB_{short_period}_0.0"]['MIDDLE'], index=prices.index)
        long_ma = pd.Series(bb_results[f"BB_{long_period}_0.0"]['MIDDLE'], index=prices.index)

        # 生成信號（向量化）
        golden_cross = (short_ma > long_ma) & (short_ma.shift(1) <= long_ma.shift(1))
        death_cross = (short_ma < long_ma) & (short_ma.shift(1) >= long_ma.shift(1))

        return pd.DataFrame({
            'entries': golden_cross,
            'exits': death_cross
        }, index=prices.index)

    def _execute_vectorbt_backtest(self, data: pd.DataFrame, signals: pd.DataFrame):
        """執行VectorBT回測"""
        close_prices = data['close']

        portfolio = vbt.Portfolio.from_signals(
            close=close_prices,
            entries=signals['entries'],
            exits=signals['exits'],
            init_cash=self.config.initial_cash,
            fees=self.config.fees,
            slippage=self.config.slippage,
            freq='1D'
        )

        return portfolio

    def _execute_simple_backtest(self, data: pd.DataFrame, signals: pd.DataFrame,
                                strategy: str, params: Dict, symbol: str, start_time: float) -> BacktestResult:
        """執行簡單回測（VectorBT不可用時）"""
        close_prices = data['close']
        returns = close_prices.pct_change().dropna()

        # 簡化的回測邏輯
        cash = self.config.initial_cash
        position = 0
        equity_values = []
        trade_returns = []

        for i, (date, row) in enumerate(data.iterrows()):
            if i < len(signals):
                if signals['entries'].iloc[i] and position == 0:
                    # 買入
                    position = cash / close_prices.iloc[i]
                    cash = 0
                elif signals['exits'].iloc[i] and position > 0:
                    # 賣出
                    cash = position * close_prices.iloc[i] * (1 - self.config.fees)
                    trade_return = (position * close_prices.iloc[i] / (position * close_prices.iloc[i-1] if i > 0 else 1)) - 1
                    trade_returns.append(trade_return)
                    position = 0

            portfolio_value = cash + position * close_prices.iloc[i]
            equity_values.append(portfolio_value)

        # 計算性能指標
        equity_series = pd.Series(equity_values, index=data.index)
        portfolio_returns = equity_series.pct_change().dropna()

        total_return = (equity_values[-1] / equity_values[0]) - 1
        annual_return = (1 + total_return) ** (252 / len(equity_values)) - 1

        if len(portfolio_returns) > 0 and portfolio_returns.std() > 0:
            sharpe_ratio = (portfolio_returns.mean() - self.config.risk_free_rate / 252) / portfolio_returns.std() * np.sqrt(252)
            volatility = portfolio_returns.std() * np.sqrt(252)
        else:
            sharpe_ratio = 0
            volatility = 0

        # 最大回撤
        running_max = equity_series.expanding().max()
        drawdown = (equity_series - running_max) / running_max
        max_drawdown = drawdown.min()

        # 交易統計
        win_rate = np.mean(np.array(trade_returns) > 0) if trade_returns else 0
        profit_factor = np.sum([r for r in trade_returns if r > 0]) / abs(np.sum([r for r in trade_returns if r < 0])) if trade_returns else 1
        avg_trade_return = np.mean(trade_returns) if trade_returns else 0
        best_trade = np.max(trade_returns) if trade_returns else 0
        worst_trade = np.min(trade_returns) if trade_returns else 0

        # 高級指標
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0

        downside_returns = portfolio_returns[portfolio_returns < 0]
        sortino_ratio = (portfolio_returns.mean() - self.config.risk_free_rate / 252) / downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 and downside_returns.std() > 0 else 0

        var_95 = np.percentile(portfolio_returns, 5) if len(portfolio_returns) > 0 else 0
        cvar_95 = portfolio_returns[portfolio_returns <= var_95].mean() if len(portfolio_returns[portfolio_returns <= var_95]) > 0 else 0

        return BacktestResult(
            symbol=symbol,
            strategy_name=strategy,
            parameters=params,
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            annual_return=annual_return,
            volatility=volatility,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_trades=len(trade_returns),
            avg_trade_return=avg_trade_return,
            best_trade=best_trade,
            worst_trade=worst_trade,
            calmar_ratio=calmar_ratio,
            sortino_ratio=sortino_ratio,
            var_95=var_95,
            cvar_95=cvar_95,
            equity_curve=equity_series,
            returns=portfolio_returns,
            trades=pd.DataFrame(),  # 簡化版本
            start_date=data.index[0].strftime('%Y-%m-%d') if len(data) > 0 else "",
            end_date=data.index[-1].strftime('%Y-%m-%d') if len(data) > 0 else "",
            data_points=len(data),
            execution_time=time.time() - start_time,
            gpu_used=self.gpu_indicators.available
        )

    def _create_vectorbt_result(self, portfolio, data: pd.DataFrame, strategy: str,
                              params: Dict, symbol: str, start_time: float) -> BacktestResult:
        """從VectorBT結果創建BacktestResult"""
        try:
            # 基本指標
            total_return = float(portfolio.total_return())
            returns = portfolio.returns()
            annual_return = float(returns.mean() * 252)
            volatility = float(returns.std() * np.sqrt(252))
            max_drawdown = float(portfolio.max_drawdown())

            # Sharpe比率（3%無風險利率）
            excess_returns = returns - self.config.risk_free_rate / 252
            sharpe_ratio = float(excess_returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0

            # 交易統計
            trades = portfolio.trades
            win_rate = float(trades.win_rate()) if len(trades) > 0 else 0
            profit_factor = float(trades.profit_factor()) if len(trades) > 0 else 1
            total_trades = len(trades.records_readable) if len(trades) > 0 else 0

            # 交易回報統計
            if len(trades) > 0 and len(trades.returns_readable) > 0:
                trade_returns = trades.returns_readable
                avg_trade_return = float(trade_returns.mean())
                best_trade = float(trade_returns.max())
                worst_trade = float(trade_returns.min())
            else:
                avg_trade_return = 0
                best_trade = 0
                worst_trade = 0

            # 高級指標
            calmar_ratio = float(total_return / abs(max_drawdown)) if max_drawdown != 0 else 0

            downside_returns = returns[returns < 0]
            sortino_ratio = float(excess_returns.mean() / downside_returns.std() * np.sqrt(252)) if len(downside_returns) > 0 and downside_returns.std() > 0 else 0

            var_95 = float(np.percentile(returns, 5))
            cvar_95 = float(returns[returns <= var_95].mean()) if len(returns[returns <= var_95]) > 0 else 0

            return BacktestResult(
                symbol=symbol,
                strategy_name=strategy,
                parameters=params,
                total_return=total_return,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                annual_return=annual_return,
                volatility=volatility,
                win_rate=win_rate,
                profit_factor=profit_factor,
                total_trades=total_trades,
                avg_trade_return=avg_trade_return,
                best_trade=best_trade,
                worst_trade=worst_trade,
                calmar_ratio=calmar_ratio,
                sortino_ratio=sortino_ratio,
                var_95=var_95,
                cvar_95=cvar_95,
                equity_curve=portfolio.value(),
                returns=returns,
                trades=trades.records_readable if len(trades) > 0 else pd.DataFrame(),
                start_date=data.index[0].strftime('%Y-%m-%d') if len(data) > 0 else "",
                end_date=data.index[-1].strftime('%Y-%m-%d') if len(data) > 0 else "",
                data_points=len(data),
                execution_time=time.time() - start_time,
                gpu_used=self.gpu_indicators.available
            )

        except Exception as e:
            logger.error(f"Error creating VectorBT result: {e}")
            return self._create_error_result(data, strategy, params, symbol, start_time, str(e))

    def _create_error_result(self, data: pd.DataFrame, strategy: str, params: Dict,
                           symbol: str, start_time: float, error_msg: str) -> BacktestResult:
        """創建錯誤結果"""
        equity_curve = pd.Series(self.config.initial_cash, index=data.index)
        returns = pd.Series(0.0, index=data.index)

        return BacktestResult(
            symbol=symbol,
            strategy_name=strategy,
            parameters=params,
            total_return=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.0,
            annual_return=0.0,
            volatility=0.0,
            win_rate=0.0,
            profit_factor=1.0,
            total_trades=0,
            avg_trade_return=0.0,
            best_trade=0.0,
            worst_trade=0.0,
            calmar_ratio=0.0,
            sortino_ratio=0.0,
            var_95=0.0,
            cvar_95=0.0,
            equity_curve=equity_curve,
            returns=returns,
            trades=pd.DataFrame(),
            start_date=data.index[0].strftime('%Y-%m-%d') if len(data) > 0 else "",
            end_date=data.index[-1].strftime('%Y-%m-%d') if len(data) > 0 else "",
            data_points=len(data),
            execution_time=time.time() - start_time,
            gpu_used=False
        )

    def _parallel_backtest(self, data: pd.DataFrame, strategies: List[Tuple[str, Dict]],
                         symbol: str) -> List[BacktestResult]:
        """並行回測"""
        results = []

        with ProcessPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = []

            # 提交任務
            for strategy, params in strategies:
                future = executor.submit(self.backtest_strategy, data, strategy, params, symbol)
                futures.append(future)

            # 收集結果
            for i, future in enumerate(as_completed(futures)):
                try:
                    result = future.result()
                    results.append(result)

                    if (i + 1) % 50 == 0:
                        logger.info(f"Completed {i + 1}/{len(strategies)} parallel backtests")

                except Exception as e:
                    logger.warning(f"Parallel backtest failed: {e}")

        return results

    def _generic_optimization(self, data: pd.DataFrame, strategy: str, param_ranges: Dict[str, List],
                            symbol: str, optimization_metric: str, max_combinations: int):
        """通用優化方法"""
        # 生成參數組合
        import itertools
        param_names = list(param_ranges.keys())
        param_values = list(param_ranges.values())
        combinations = list(itertools.product(*param_values))
        param_combinations = [dict(zip(param_names, combo)) for combo in combinations]

        # 限制組合數量
        if len(param_combinations) > max_combinations:
            param_combinations = param_combinations[:max_combinations]

        # 執行回測
        strategies = [(strategy, params) for params in param_combinations]
        results = self.backtest_multiple_strategies(data, strategies, symbol)

        # 找到最佳結果
        if optimization_metric == "sharpe_ratio":
            best_result = max(results, key=lambda x: x.sharpe_ratio)
        elif optimization_metric == "total_return":
            best_result = max(results, key=lambda x: x.total_return)
        elif optimization_metric == "max_drawdown":
            best_result = min(results, key=lambda x: x.max_drawdown)
        else:
            best_result = results[0]

        # 統計信息
        metric_values = [getattr(r, optimization_metric, 0) for r in results]

        from .gpu_parameter_optimizer import OptimizationResult

        return OptimizationResult(
            strategy_name=strategy,
            symbol=symbol,
            best_parameters=best_result.parameters,
            best_score=getattr(best_result, optimization_metric, 0),
            best_performance=best_result.to_dict(),
            total_combinations=len(param_combinations),
            successful_combinations=len(results),
            execution_time=sum(r.execution_time for r in results),
            strategies_per_second=len(results) / sum(r.execution_time for r in results) if sum(r.execution_time for r in results) > 0 else 0,
            performance_stats=self.gpu_indicators.get_performance_stats(),
            top_results=results[:10],
            optimization_method="GPU Generic Optimization",
            gpu_used=self.gpu_indicators.available
        )

    def _generate_cache_key(self, data: pd.DataFrame, strategy: str, params: Dict) -> str:
        """生成緩存鍵"""
        import hashlib
        data_hash = hashlib.md5(f"{data.shape}{strategy}{str(params)}".encode()).hexdigest()
        return data_hash

    def _update_backtest_stats(self, result: BacktestResult):
        """更新回測統計"""
        self.backtest_stats['total_backtests'] += 1
        self.backtest_stats['total_execution_time'] += result.execution_time

        if result.gpu_used:
            self.backtest_stats['gpu_backtests'] += 1

    def get_backtest_stats(self) -> Dict[str, Any]:
        """獲取回測統計"""
        stats = self.backtest_stats.copy()

        if stats['total_backtests'] > 0:
            stats['average_execution_time'] = stats['total_execution_time'] / stats['total_backtests']
            stats['gpu_utilization_rate'] = stats['gpu_backtests'] / stats['total_backtests']
        else:
            stats['average_execution_time'] = 0
            stats['gpu_utilization_rate'] = 0

        return stats

    def clear_cache(self):
        """清除緩存"""
        self._backtest_cache.clear()
        logger.info("Backtest cache cleared")

# 全局回測引擎實例
_gpu_backtest_instance = None

def get_gpu_backtest_engine(config: Optional[BacktestConfig] = None) -> GPUBacktestEngine:
    """獲取全局GPU回測引擎實例"""
    global _gpu_backtest_instance
    if _gpu_backtest_instance is None:
        _gpu_backtest_instance = GPUBacktestEngine(config)
    return _gpu_backtest_instance

def reset_gpu_backtest_engine():
    """重置全局GPU回測引擎"""
    global _gpu_backtest_instance
    _gpu_backtest_instance = None
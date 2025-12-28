"""
Enhanced Backtest Engine with Integrated Risk Management
========================================================

An enhanced version of the CBSC backtest engine that integrates advanced risk management
capabilities including real-time monitoring, dynamic adjustments, and comprehensive analysis.

Author: CBSC Quant Team
Version: 2.0.0
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

# Import risk management modules
try:
    from .enhanced_risk_analyzer import EnhancedRiskAnalyzer, RiskMetrics
    from .real_time_risk_monitor import RealTimeRiskMonitor, RiskThreshold, RiskLevel, AdjustmentType
    from .dynamic_risk_adjuster import DynamicRiskAdjustmentSystem, PositionScalingAdjuster, VolatilityTargetingAdjuster
except ImportError:
    # Fallback for running as script
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    try:
        from enhanced_risk_analyzer import EnhancedRiskAnalyzer, RiskMetrics
        from real_time_risk_monitor import RealTimeRiskMonitor, RiskThreshold, RiskLevel, AdjustmentType
        from dynamic_risk_adjuster import DynamicRiskAdjustmentSystem, PositionScalingAdjuster, VolatilityTargetingAdjuster
    except ImportError:
        EnhancedRiskAnalyzer = None
        RiskMetrics = None
        RealTimeRiskMonitor = None
        RiskThreshold = None
        RiskLevel = None
        AdjustmentType = None
        DynamicRiskAdjustmentSystem = None
        PositionScalingAdjuster = None
        VolatilityTargetingAdjuster = None

# Import new advanced modules
try:
    from .vectorized_backtest_engine import VectorizedBacktestEngine, VectorizedBacktestMode, PortfolioConfig
    from .transaction_cost_model import TransactionCostModel, create_default_cost_config
    from .advanced_monte_carlo import AdvancedMonteCarlo, AdvancedMCConfig, create_stress_scenarios
    from .portfolio_optimizer import PortfolioOptimizer, create_optimization_config
    from .performance_attribution_analyzer import PerformanceAttributionAnalyzer, create_attribution_config
    from .parallel_processor_new import ParallelProcessor, create_parallel_config
    from .visualization_reports import BacktestVisualizer, ReportGenerator
    from .parameter_optimizer import ParameterOptimizer, create_optimization_config
except ImportError:
    logger.warning("Some advanced modules not available. Enhanced features may be limited.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BacktestMode(Enum):
    """Backtest execution modes"""
    STANDARD = "standard"
    RISK_MANAGED = "risk_managed"
    STRESS_TEST = "stress_test"
    MONTE_CARLO = "monte_carlo"

@dataclass
class BacktestConfig:
    """Configuration for enhanced backtest"""
    # Basic parameters
    start_date: datetime
    end_date: datetime
    initial_capital: float = 1000000.0
    commission_rate: float = 0.001
    slippage_rate: float = 0.0005

    # Risk management parameters
    enable_risk_management: bool = True
    var_limit: float = 0.02  # 2% daily VaR limit
    max_drawdown_limit: float = 0.15  # 15% max drawdown
    leverage_limit: float = 2.0
    position_size_limit: float = 0.3  # Max 30% in single position

    # Dynamic adjustment parameters
    enable_dynamic_adjustments: bool = True
    volatility_targeting: bool = True
    target_volatility: float = 0.15  # 15% annualized
    rebalance_frequency: str = "weekly"  # daily, weekly, monthly

    # Monitoring parameters
    enable_real_time_monitoring: bool = True
    monitoring_frequency: int = 3600  # seconds

    # Advanced features
    enable_stress_testing: bool = True
    enable_regime_detection: bool = True
    enable_correlation_analysis: bool = True

@dataclass
class Position:
    """Position representation"""
    symbol: str
    quantity: float
    entry_price: float
    current_price: float
    entry_date: datetime

    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price

    @property
    def unrealized_pnl(self) -> float:
        return self.quantity * (self.current_price - self.entry_price)

    @property
    def return_pct(self) -> float:
        return (self.current_price - self.entry_price) / self.entry_price if self.entry_price > 0 else 0

@dataclass
class Trade:
    """Trade execution record"""
    timestamp: datetime
    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: float
    price: float
    commission: float
    slippage: float

@dataclass
class BacktestResult:
    """Comprehensive backtest results"""
    # Basic metrics
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    calmar_ratio: float

    # Risk metrics
    var_95: float
    var_99: float
    expected_shortfall_95: float
    expected_shortfall_99: float

    # Trade statistics
    total_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float

    # Advanced metrics
    information_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    tail_ratio: Optional[float] = None

    # Risk analysis
    risk_metrics: Optional[RiskMetrics] = None
    stress_test_results: Optional[Dict] = None

    # Time series data
    equity_curve: Optional[pd.Series] = None
    returns: Optional[pd.Series] = None
    positions: Optional[List[Position]] = None
    trades: Optional[List[Trade]] = None

class EnhancedBacktestEngine:
    """
    Enhanced backtest engine with integrated risk management
    """

    def __init__(self, config: BacktestConfig):
        self.config = config
        self.risk_analyzer = EnhancedRiskAnalyzer()
        self.dynamic_adjuster = DynamicRiskAdjustmentSystem()

        # Initialize components based on configuration
        self.risk_monitor = None
        if config.enable_real_time_monitoring:
            self._setup_risk_monitor()

        # State variables
        self.current_capital = config.initial_capital
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.equity_curve: List[Tuple[datetime, float]] = []
        self.returns_history: List[float] = []

        # Performance tracking
        self.high_water_mark = config.initial_capital
        self.current_drawdown = 0.0

        # Risk management state
        self.last_rebalance_date = None
        self.current_volatility_estimate = 0.0

        logger.info(f"Enhanced backtest engine initialized with {config.start_date} to {config.end_date}")

    def _setup_risk_monitor(self):
        """Setup real-time risk monitor"""
        # Define risk thresholds
        thresholds = {
            "var_95": RiskThreshold("var_95", RiskLevel.MEDIUM, self.config.var_limit, " VaR 95% limit"),
            "max_drawdown": RiskThreshold("max_drawdown", RiskLevel.HIGH, self.config.max_drawdown_limit, "Max drawdown limit"),
            "leverage": RiskThreshold("leverage", RiskLevel.MEDIUM, self.config.leverage_limit, "Leverage limit"),
            "position_concentration": RiskThreshold("position_concentration", RiskLevel.LOW,
                                                   self.config.position_size_limit, "Position size limit")
        }

        self.risk_monitor = RealTimeRiskMonitor(
            strategy_id="backtest_engine",
            thresholds=thresholds,
            update_frequency=self.config.monitoring_frequency,
            auto_adjust=self.config.enable_dynamic_adjustments
        )

        # Add adjustment rules
        if self.config.enable_dynamic_adjustments:
            self._setup_adjustment_rules()

    def _setup_adjustment_rules(self):
        """Setup dynamic adjustment rules"""
        if self.config.volatility_targeting:
            # Volatility targeting rule
            vt_adjuster = VolatilityTargetingAdjuster(target_volatility=self.config.target_volatility)
            self.dynamic_adjuster.add_adjuster(vt_adjuster)

        # Position scaling rule
        ps_adjuster = PositionScalingAdjuster(
            scaling_factor=0.5,
            max_position_size=self.config.position_size_limit
        )
        self.dynamic_adjuster.add_adjuster(ps_adjuster)

    def run_backtest(self,
                    strategy: Callable,
                    data: pd.DataFrame,
                    benchmark_data: Optional[pd.DataFrame] = None,
                    mode: BacktestMode = BacktestMode.RISK_MANAGED) -> BacktestResult:
        """
        Run enhanced backtest with integrated risk management

        Args:
            strategy: Strategy function that returns target positions
            data: Market data with OHLCV
            benchmark_data: Benchmark data for comparison
            mode: Backtest execution mode

        Returns:
            BacktestResult: Comprehensive backtest results
        """
        logger.info(f"Starting backtest in {mode.value} mode")

        try:
            if mode == BacktestMode.STANDARD:
                return self._run_standard_backtest(strategy, data, benchmark_data)
            elif mode == BacktestMode.RISK_MANAGED:
                return self._run_risk_managed_backtest(strategy, data, benchmark_data)
            elif mode == BacktestMode.STRESS_TEST:
                return self._run_stress_test_backtest(strategy, data, benchmark_data)
            elif mode == BacktestMode.MONTE_CARLO:
                return self._run_monte_carlo_backtest(strategy, data, benchmark_data)
            else:
                raise ValueError(f"Unsupported backtest mode: {mode}")

        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            raise

    def _run_risk_managed_backtest(self,
                                  strategy: Callable,
                                  data: pd.DataFrame,
                                  benchmark_data: Optional[pd.DataFrame] = None) -> BacktestResult:
        """Run backtest with integrated risk management"""

        # Start risk monitoring
        if self.risk_monitor:
            asyncio.create_task(self.risk_monitor.start_monitoring())

        # Process data day by day
        for date, row in data.iterrows():
            # Update current prices for all positions
            self._update_position_prices(date, row)

            # Calculate current portfolio state
            current_portfolio_value = self._calculate_portfolio_value()
            current_positions = {symbol: pos.quantity for symbol, pos in self.positions.items()}

            # Get strategy signals
            target_positions = strategy(date, row, self._get_portfolio_state())

            # Apply risk management
            if self.config.enable_risk_management:
                target_positions = self._apply_risk_management(target_positions, date, row)

            # Execute trades
            self._execute_trades(target_positions, date, row, current_portfolio_value)

            # Update equity curve
            portfolio_value = self._calculate_portfolio_value()
            self.equity_curve.append((date, portfolio_value))

            # Calculate daily return
            if len(self.equity_curve) > 1:
                daily_return = (portfolio_value - self.equity_curve[-2][1]) / self.equity_curve[-2][1]
                self.returns_history.append(daily_return)

            # Update high water mark and drawdown
            if portfolio_value > self.high_water_mark:
                self.high_water_mark = portfolio_value
                self.current_drawdown = 0.0
            else:
                self.current_drawdown = (self.high_water_mark - portfolio_value) / self.high_water_mark

            # Dynamic rebalancing
            if self._should_rebalance(date):
                target_positions = self._apply_dynamic_adjustments(date, row)
                self._execute_trades(target_positions, date, row, portfolio_value)

            # Real-time monitoring update
            if self.risk_monitor and len(self.returns_history) > 0:
                self.risk_monitor.update_risk_metrics(
                    portfolio_values=[portfolio_value],
                    positions=current_positions,
                    returns=[self.returns_history[-1]]
                )

        # Stop monitoring
        if self.risk_monitor:
            self.risk_monitor.stop_monitoring()

        # Generate comprehensive results
        return self._generate_results(benchmark_data)

    def _apply_risk_management(self,
                             target_positions: Dict[str, float],
                             date: datetime,
                             market_data: pd.Series) -> Dict[str, float]:
        """Apply risk management rules to target positions"""

        # Calculate portfolio metrics
        total_exposure = sum(abs(pos) for pos in target_positions.values())
        current_portfolio_value = self._calculate_portfolio_value()

        # Apply position size limits
        for symbol, target_size in target_positions.items():
            max_size = self.config.position_size_limit * current_portfolio_value / market_data.get(symbol, 1)
            target_positions[symbol] = min(abs(target_size), max_size) * (1 if target_size >= 0 else -1)

        # Apply leverage limits
        if total_exposure > self.config.leverage_limit * current_portfolio_value:
            scaling_factor = (self.config.leverage_limit * current_portfolio_value) / total_exposure
            for symbol in target_positions:
                target_positions[symbol] *= scaling_factor

        # Check drawdown limits
        if self.current_drawdown > self.config.max_drawdown_limit:
            # Reduce positions proportionally
            reduction_factor = 1 - self.current_drawdown
            for symbol in target_positions:
                target_positions[symbol] *= reduction_factor
            logger.warning(f"Drawdown limit exceeded. Reducing positions by factor {reduction_factor:.2f}")

        return target_positions

    def _apply_dynamic_adjustments(self,
                                 date: datetime,
                                 market_data: pd.Series) -> Dict[str, float]:
        """Apply dynamic adjustments based on current market conditions"""

        if not self.config.enable_dynamic_adjustments or len(self.returns_history) < 30:
            return {symbol: pos.quantity for symbol, pos in self.positions.items()}

        current_positions = {symbol: pos.quantity for symbol, pos in self.positions.items()}
        recent_returns = np.array(self.returns_history[-30:])  # Last 30 days

        # Evaluate adjustments
        adjustments = self.dynamic_adjuster.evaluate_and_adjust(
            current_positions=current_positions,
            returns=recent_returns,
            portfolio_values=[self._calculate_portfolio_value()],
            risk_budget=self.config.var_limit,
            target_leverage=1.0
        )

        # Apply adjustments
        adjusted_positions = current_positions.copy()
        for adj in adjustments:
            adjusted_positions[adj.asset] = adj.suggested_size

        return adjusted_positions

    def _should_rebalance(self, date: datetime) -> bool:
        """Check if rebalancing should occur"""
        if not self.last_rebalance_date:
            self.last_rebalance_date = date
            return True

        if self.config.rebalance_frequency == "daily":
            return date.date() > self.last_rebalance_date.date()
        elif self.config.rebalance_frequency == "weekly":
            return (date - self.last_rebalance_date).days >= 7
        elif self.config.rebalance_frequency == "monthly":
            return (date - self.last_rebalance_date).days >= 30

        return False

    def _execute_trades(self,
                       target_positions: Dict[str, float],
                       date: datetime,
                       market_data: pd.Series,
                       portfolio_value: float):
        """Execute trades to reach target positions"""

        for symbol, target_quantity in target_positions.items():
            current_quantity = self.positions.get(symbol, Position(symbol, 0, 0, 0, date)).quantity

            if abs(target_quantity - current_quantity) > 0.01:  # Minimum trade size
                trade_quantity = target_quantity - current_quantity
                price = market_data.get(symbol, 1)

                # Calculate commission and slippage
                trade_value = abs(trade_quantity * price)
                commission = trade_value * self.config.commission_rate
                slippage = trade_value * self.config.slippage_rate

                # Execute trade
                if trade_quantity > 0:  # Buy
                    self.current_capital -= (trade_quantity * price + commission + slippage)
                else:  # Sell
                    self.current_capital += (abs(trade_quantity) * price - commission - slippage)

                # Record trade
                trade = Trade(
                    timestamp=date,
                    symbol=symbol,
                    side="buy" if trade_quantity > 0 else "sell",
                    quantity=trade_quantity,
                    price=price,
                    commission=commission,
                    slippage=slippage
                )
                self.trades.append(trade)

                # Update position
                if symbol not in self.positions:
                    self.positions[symbol] = Position(symbol, 0, price, price, date)

                if abs(target_quantity) < 0.01:  # Close position
                    del self.positions[symbol]
                else:
                    self.positions[symbol].quantity = target_quantity

    def _update_position_prices(self, date: datetime, market_data: pd.Series):
        """Update current prices for all positions"""
        for symbol, position in self.positions.items():
            if symbol in market_data:
                position.current_price = market_data[symbol]

    def _calculate_portfolio_value(self) -> float:
        """Calculate total portfolio value"""
        position_value = sum(pos.market_value for pos in self.positions.values())
        return self.current_capital + position_value

    def _get_portfolio_state(self) -> Dict[str, Any]:
        """Get current portfolio state for strategy"""
        return {
            "capital": self.current_capital,
            "positions": {symbol: pos.quantity for symbol, pos in self.positions.items()},
            "portfolio_value": self._calculate_portfolio_value(),
            "drawdown": self.current_drawdown,
            "returns": self.returns_history[-10:] if self.returns_history else []
        }

    def _generate_results(self, benchmark_data: Optional[pd.DataFrame] = None) -> BacktestResult:
        """Generate comprehensive backtest results"""

        # Create time series
        equity_series = pd.Series(
            [value for date, value in self.equity_curve],
            index=[date for date, value in self.equity_curve]
        )

        returns_series = pd.Series(self.returns_history)

        # Basic metrics
        total_return = (equity_series.iloc[-1] - self.config.initial_capital) / self.config.initial_capital
        n_days = len(equity_series)
        annualized_return = (1 + total_return) ** (252 / n_days) - 1 if n_days > 0 else 0

        volatility = returns_series.std() * np.sqrt(252) if len(returns_series) > 0 else 0
        sharpe_ratio = annualized_return / volatility if volatility > 0 else 0

        # Drawdown calculation
        rolling_max = equity_series.expanding().max()
        drawdown = (equity_series - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0

        # Trade statistics
        if self.trades:
            profits = [t.quantity * (t.price - self.positions.get(t.symbol, Position(t.symbol, 0, t.price, t.price, t.timestamp)).entry_price)
                      for t in self.trades if t.side == "sell"]
            wins = [p for p in profits if p > 0]
            losses = [p for p in profits if p < 0]

            win_rate = len(wins) / len(profits) if profits else 0
            avg_win = np.mean(wins) if wins else 0
            avg_loss = np.mean(losses) if losses else 0
            profit_factor = abs(sum(wins) / sum(losses)) if losses else float('inf')
        else:
            win_rate = avg_win = avg_loss = profit_factor = 0

        # Risk analysis
        risk_metrics = None
        var_95 = var_99 = expected_shortfall_95 = expected_shortfall_99 = 0

        if len(returns_series) > 30:
            risk_metrics = self.risk_analyzer.calculate_comprehensive_risk_metrics(
                returns=returns_series.values,
                portfolio_values=equity_series.values,
                positions={symbol: pos.quantity for symbol, pos in self.positions.items()},
                benchmark_returns=benchmark_data['returns'].values if benchmark_data is not None else None
            )

            var_95 = risk_metrics.var.confidence_levels.get(0.95, 0)
            var_99 = risk_metrics.var.confidence_levels.get(0.99, 0)
            expected_shortfall_95 = risk_metrics.expected_shortfall.confidence_levels.get(0.95, 0)
            expected_shortfall_99 = risk_metrics.expected_shortfall.confidence_levels.get(0.99, 0)

        # Advanced ratios
        sortino_ratio = annualized_return / (returns_series[returns_series < 0].std() * np.sqrt(252)) if len(returns_series[returns_series < 0]) > 0 else 0
        tail_ratio = np.percentile(returns_series, 95) / abs(np.percentile(returns_series, 5)) if len(returns_series) > 0 else 0

        # Information ratio (if benchmark provided)
        information_ratio = None
        if benchmark_data is not None and len(returns_series) == len(benchmark_data):
            excess_returns = returns_series - benchmark_data['returns']
            information_ratio = excess_returns.mean() / excess_returns.std() if excess_returns.std() > 0 else 0

        return BacktestResult(
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            calmar_ratio=calmar_ratio,
            var_95=var_95,
            var_99=var_99,
            expected_shortfall_95=expected_shortfall_95,
            expected_shortfall_99=expected_shortfall_99,
            total_trades=len(self.trades),
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            information_ratio=information_ratio,
            sortino_ratio=sortino_ratio,
            tail_ratio=tail_ratio,
            risk_metrics=risk_metrics,
            equity_curve=equity_series,
            returns=returns_series,
            positions=list(self.positions.values()),
            trades=self.trades
        )

    def _run_standard_backtest(self,
                             strategy: Callable,
                             data: pd.DataFrame,
                             benchmark_data: Optional[pd.DataFrame] = None) -> BacktestResult:
        """Run standard backtest without risk management"""

        # Temporarily disable risk management
        original_config = self.config.enable_risk_management
        self.config.enable_risk_management = False

        result = self._run_risk_managed_backtest(strategy, data, benchmark_data)

        # Restore original config
        self.config.enable_risk_management = original_config

        return result

    def _run_stress_test_backtest(self,
                                strategy: Callable,
                                data: pd.DataFrame,
                                benchmark_data: Optional[pd.DataFrame] = None) -> BacktestResult:
        """Run backtest with stress scenarios"""

        # Define stress periods
        stress_periods = {
            "2008_crisis": ("2008-09-01", "2009-03-31"),
            "covid_crash": ("2020-02-20", "2020-04-30"),
            "dot_com_bubble": ("2000-03-10", "2002-10-09")
        }

        results = {}

        for scenario, (start_date, end_date) in stress_periods.items():
            # Filter data for stress period
            stress_data = data.loc[start_date:end_date]

            if len(stress_data) > 0:
                logger.info(f"Running stress test for scenario: {scenario}")

                # Reset engine state
                self.__init__(self.config)

                # Run backtest for stress period
                scenario_result = self._run_risk_managed_backtest(strategy, stress_data, benchmark_data)
                results[scenario] = scenario_result

        # Combine results (use full period results as base)
        base_result = self._run_risk_managed_backtest(strategy, data, benchmark_data)
        base_result.stress_test_results = results

        return base_result

    def _run_monte_carlo_backtest(self,
                                strategy: Callable,
                                data: pd.DataFrame,
                                benchmark_data: Optional[pd.DataFrame] = None,
                                n_simulations: int = 1000) -> BacktestResult:
        """Run Monte Carlo simulation"""

        logger.info(f"Running Monte Carlo simulation with {n_simulations} iterations")

        # Get returns from original data
        returns = data.pct_change().dropna()

        simulation_results = []

        for i in range(n_simulations):
            # Generate random path
            simulated_returns = returns.sample(n=len(returns), replace=True).reset_index(drop=True)
            simulated_data = data.iloc[0:1]  # Keep first row

            for ret in simulated_returns.iloc[:, 0]:  # Use first column
                new_row = simulated_data.iloc[-1] * (1 + ret)
                simulated_data = pd.concat([simulated_data, new_row.to_frame().T], ignore_index=True)

            # Reset engine state
            self.__init__(self.config)

            # Run backtest on simulated data
            result = self._run_risk_managed_backtest(strategy, simulated_data, benchmark_data)
            simulation_results.append(result.total_return)

        # Calculate statistics
        simulation_results = np.array(simulation_results)

        # Update base result with Monte Carlo statistics
        base_result = self._run_risk_managed_backtest(strategy, data, benchmark_data)

        # Add Monte Carlo metrics to result
        base_result.monte_carlo_mean = np.mean(simulation_results)
        base_result.monte_carlo_std = np.std(simulation_results)
        base_result.monte_carlo_var_95 = np.percentile(simulation_results, 5)
        base_result.monte_carlo_var_99 = np.percentile(simulation_results, 1)

        return base_result

# Example usage and test functions
def example_strategy(date: datetime, market_data: pd.Series, portfolio_state: Dict[str, Any]) -> Dict[str, float]:
    """
    Example simple moving average crossover strategy
    """
    # This is a placeholder - in reality, you'd have access to historical data
    # for calculating moving averages and other indicators

    # Simple buy and hold for AAPL
    if "AAPL" in market_data:
        current_price = market_data["AAPL"]
        target_value = portfolio_state["portfolio_value"] * 0.6  # 60% allocation
        return {"AAPL": target_value / current_price}

    return {}

def run_example_backtest():
    """Run example backtest with enhanced risk management"""

    # Create sample data
    dates = pd.date_range(start="2023-01-01", end="2023-12-31", freq="D")
    np.random.seed(42)

    # Simulate AAPL price data
    aapl_prices = 150 * np.cumprod(1 + np.random.normal(0.0005, 0.02, len(dates)))

    data = pd.DataFrame({
        "AAPL": aapl_prices
    }, index=dates)

    # Create configuration
    config = BacktestConfig(
        start_date=dates[0],
        end_date=dates[-1],
        initial_capital=1000000,
        enable_risk_management=True,
        enable_dynamic_adjustments=True,
        var_limit=0.02,
        max_drawdown_limit=0.15
    )

    # Create engine
    engine = EnhancedBacktestEngine(config)

    # Run backtest
    result = engine.run_backtest(
        strategy=example_strategy,
        data=data,
        mode=BacktestMode.RISK_MANAGED
    )

    # Print results
    print(f"Total Return: {result.total_return:.2%}")
    print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
    print(f"Max Drawdown: {result.max_drawdown:.2%}")
    print(f"VaR 95%: {result.var_95:.2%}")
    print(f"Total Trades: {result.total_trades}")
    print(f"Win Rate: {result.win_rate:.2%}")

    if result.risk_metrics:
        print(f"Calmar Ratio: {result.risk_metrics.calmar_ratio:.2f}")
        print(f"Sortino Ratio: {result.risk_metrics.sortino_ratio:.2f}")

    return result

if __name__ == "__main__":
    # Run example backtest
    result = run_example_backtest()

    print("\nEnhanced Backtest Complete!")
    print("=" * 50)
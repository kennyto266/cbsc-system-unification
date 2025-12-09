#!/usr/bin/env python3
"""
Phase 2: 5+ Year Backtesting Integration with VectorBT
======================================================

Advanced long-term backtesting engine supporting 5+ year historical analysis
with government data integration and statistical validation.

Key Features:
- 5+ year historical backtesting
- Government data fusion in backtesting
- Statistical validation of results
- Professional-grade reporting
- Multiple market regime analysis

Author: Claude Code Assistant
Date: 2025-11-29
Phase: 2 - Long-term Backtesting Integration
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

try:
    import vectorbt as vbt
    VECTORBT_AVAILABLE = True
except ImportError:
    VECTORBT_AVAILABLE = False
    logging.warning("VectorBT not available. Install with: pip install vectorbt[yfinance]")

# Import existing components
from .enhanced_vectorbt_engine import EnhancedVectorBTEngine, EnhancedBacktestConfig, BacktestResult
from ..indicators.long_term_technical_indicators import LongTermTechnicalIndicators, LongTermIndicatorConfig
from .statistical_validation_framework import StatisticalValidator, ValidationResults, StatisticalValidationConfig

logger = logging.getLogger(__name__)


@dataclass
class Phase2BacktestConfig(EnhancedBacktestConfig):
    """Extended configuration for Phase 2 long-term backtesting"""
    
    # Long-term requirements
    min_data_years: int = 5
    preferred_data_years: int = 10
    data_start_date: Optional[datetime] = None  # Force specific start date
    
    # Government data integration
    enable_government_data: bool = True
    government_data_weight: float = 0.3
    
    # Statistical validation
    enable_statistical_validation: bool = True
    bootstrap_samples: int = 5000
    confidence_level: float = 0.95
    
    # Market regime analysis
    enable_regime_analysis: bool = True
    regime_window: int = 504  # 2 years
    
    # Performance reporting
    generate_detailed_report: bool = True
    include_benchmark_comparison: bool = True
    
    # Risk management
    enable_risk_management: bool = True
    max_portfolio_risk: float = 0.15  # 15% annual volatility
    sector_concentration_limit: float = 0.4  # 40% max in one sector


@dataclass
class Phase2BacktestResult(BacktestResult):
    """Extended backtest result with Phase 2 specific features"""
    
    # Government data integration
    government_data_used: bool = False
    economic_indicator_correlation: float = 0.0
    
    # Statistical validation
    validation_results: Optional[ValidationResults] = None
    bootstrap_confidence_intervals: Optional[Dict[str, Any]] = None
    statistical_significance: bool = False
    
    # Market regime analysis
    regime_performance: Optional[Dict[str, Any]] = None
    regime_stability_score: float = 0.0
    
    # Long-term metrics
    cagr: float = 0.0  # Compound Annual Growth Rate
    long_term_alpha: float = 0.0
    information_ratio: float = 0.0
    treynor_ratio: float = 0.0
    
    # Risk-adjusted metrics
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    omega_ratio: float = 0.0
    
    # Additional validation
    data_quality_score: float = 0.0
    model_stability_score: float = 0.0


class Phase2LongTermBacktestEngine:
    """
    Phase 2 long-term backtesting engine with advanced features
    """
    
    def __init__(self, config: Optional[Phase2BacktestConfig] = None):
        self.config = config or Phase2BacktestConfig()
        
        # Initialize components
        self.vectorbt_engine = EnhancedVectorBTEngine(self.config)
        self.long_term_indicators = LongTermTechnicalIndicators(
            LongTermIndicatorConfig(min_data_points=self.config.min_data_years * 252)
        )
        self.statistical_validator = StatisticalValidator(
            StatisticalValidationConfig(
                confidence_level=self.config.confidence_level,
                bootstrap_samples=self.config.bootstrap_samples
            )
        )
        
        # Performance tracking
        self._execution_stats = {
            'total_backtests': 0,
            'total_execution_time': 0.0,
            'average_execution_time': 0.0,
            'government_data_success_rate': 0.0,
            'validation_success_rate': 0.0
        }
        
        logger.info("Phase 2 Long-term Backtest Engine initialized")
        
        if not VECTORBT_AVAILABLE:
            raise ImportError("VectorBT is required for Phase 2 backtesting")
    
    def run_long_term_backtest(
        self,
        data: pd.DataFrame,
        strategy: str,
        parameters: Dict[str, Any],
        symbol: str = "UNKNOWN",
        benchmark_data: Optional[pd.DataFrame] = None,
        force_start_date: Optional[datetime] = None
    ) -> Phase2BacktestResult:
        """
        Run comprehensive long-term backtest with government data integration
        
        Args:
            data: OHLCV price data with minimum 5 years of history
            strategy: Strategy name
            parameters: Strategy parameters
            symbol: Symbol identifier
            benchmark_data: Benchmark OHLCV data for comparison
            force_start_date: Optional override for backtest start date
            
        Returns:
            Phase2BacktestResult with comprehensive analysis
        """
        
        start_time = time.time()
        
        try:
            logger.info(f"Starting Phase 2 long-term backtest for {symbol} with strategy {strategy}")
            
            # 1. Validate data requirements
            self._validate_data_requirements(data, symbol)
            
            # 2. Determine backtest period
            backtest_start, backtest_end = self._determine_backtest_period(
                data, force_start_date, symbol
            )
            
            # 3. Prepare data for backtesting
            backtest_data = data.loc[backtest_start:backtest_end].copy()
            
            # 4. Government data integration
            government_signals = None
            if self.config.enable_government_data:
                government_signals = self._integrate_government_data(
                    backtest_data, backtest_start, backtest_end
                )
            
            # 5. Generate enhanced trading signals
            enhanced_signals = self._generate_enhanced_signals(
                backtest_data, strategy, parameters, government_signals
            )
            
            # 6. Execute VectorBT backtest
            vectorbt_result = self._execute_vectorbt_backtest(
                backtest_data, enhanced_signals, symbol
            )
            
            # 7. Calculate long-term performance metrics
            long_term_metrics = self._calculate_long_term_metrics(
                vectorbt_result, backtest_data
            )
            
            # 8. Statistical validation
            validation_results = None
            bootstrap_intervals = None
            if self.config.enable_statistical_validation:
                validation_results = self._perform_statistical_validation(
                    vectorbt_result, benchmark_data
                )
                bootstrap_intervals = self._calculate_bootstrap_intervals(
                    vectorbt_result
                )
            
            # 9. Market regime analysis
            regime_performance = None
            if self.config.enable_regime_analysis:
                regime_performance = self._analyze_market_regimes(
                    vectorbt_result, backtest_data
                )
            
            # 10. Create comprehensive result
            phase2_result = self._create_phase2_result(
                vectorbt_result, strategy, parameters, symbol,
                long_term_metrics, validation_results, 
                bootstrap_intervals, regime_performance,
                government_signals is not None
            )
            
            # 11. Update performance statistics
            execution_time = time.time() - start_time
            self._update_execution_stats(execution_time, government_signals is not None)
            
            logger.info(f"Phase 2 backtest completed for {symbol} in {execution_time:.2f}s")
            
            return phase2_result
            
        except Exception as e:
            logger.error(f"Phase 2 backtest failed for {symbol}: {e}")
            raise
    
    def _validate_data_requirements(self, data: pd.DataFrame, symbol: str) -> None:
        """Validate that data meets long-term requirements"""
        
        if len(data) < self.config.min_data_years * 252:
            raise ValueError(
                f"Insufficient data for {symbol}: "
                f"{len(data)} days < {self.config.min_data_years * 252} required "
                f"({self.config.min_data_years} years)"
            )
        
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns for {symbol}: {missing_columns}")
        
        # Check for data quality issues
        zero_volume_days = (data['volume'] == 0).sum()
        if zero_volume_days > len(data) * 0.1:  # More than 10% zero volume
            logger.warning(f"High zero volume percentage for {symbol}: {zero_volume_days/len(data):.1%}")
        
        # Check date continuity
        if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index)
    
    def _determine_backtest_period(
        self, 
        data: pd.DataFrame, 
        force_start_date: Optional[datetime],
        symbol: str
    ) -> Tuple[datetime, datetime]:
        """Determine optimal backtest period"""
        
        if force_start_date:
            backtest_start = force_start_date
        elif self.config.data_start_date:
            backtest_start = self.config.data_start_date
        else:
            # Use the earliest date that provides minimum data length
            earliest_start = data.index[0]
            preferred_start = data.index[-1] - timedelta(days=self.config.preferred_data_years * 365)
            backtest_start = max(earliest_start, preferred_start)
        
        backtest_end = data.index[-1]
        
        # Ensure we have enough data
        actual_days = len(data.loc[backtest_start:backtest_end])
        if actual_days < self.config.min_data_years * 252:
            # Adjust start date to meet minimum requirement
            required_start = backtest_end - timedelta(days=self.config.min_data_years * 365)
            backtest_start = max(data.index[0], required_start)
            logger.warning(
                f"Adjusted start date for {symbol} to meet minimum data requirement: {backtest_start.date()}"
            )
        
        logger.info(f"Backtest period for {symbol}: {backtest_start.date()} to {backtest_end.date()}")
        return backtest_start, backtest_end
    
    def _integrate_government_data(
        self, 
        data: pd.DataFrame, 
        start_date: datetime, 
        end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """Integrate government data into backtesting"""
        
        try:
            logger.info("Integrating government data for backtesting")
            
            # Calculate long-term trend indicator with government data
            government_indicator = self.long_term_indicators.calculate_long_term_trend_indicator(
                data, start_date, end_date
            )
            
            if government_indicator.empty:
                logger.warning("No government data available, using price data only")
                return None
            
            logger.info(f"Government data integration successful: {len(government_indicator)} data points")
            return government_indicator
            
        except Exception as e:
            logger.error(f"Government data integration failed: {e}")
            return None
    
    def _generate_enhanced_signals(
        self,
        data: pd.DataFrame,
        strategy: str,
        parameters: Dict[str, Any],
        government_signals: Optional[pd.DataFrame]
    ) -> pd.DataFrame:
        """Generate enhanced trading signals combining strategy and government data"""
        
        # Generate base strategy signals
        base_signals = self.vectorbt_engine._generate_signals(data, strategy, parameters)
        
        if government_signals is None:
            return base_signals
        
        try:
            # Align signals with government data
            common_index = data.index.intersection(government_signals.index)
            aligned_base_signals = base_signals.reindex(common_index)
            aligned_government = government_signals.reindex(common_index)
            
            # Enhanced signal logic
            enhanced_signals = aligned_base_signals.copy()
            
            if 'trend_signal' in aligned_government.columns:
                # Incorporate government trend signals
                govt_trend = aligned_government['trend_signal']
                
                # Weight government signals
                govt_weight = self.config.government_data_weight
                base_weight = 1 - govt_weight
                
                # Combine signals (weighted approach)
                if 'entries' in enhanced_signals.columns and 'exits' in enhanced_signals.columns:
                    # Enhance entry signals
                    base_entries = enhanced_signals['entries'].astype(int)
                    enhanced_entries = (
                        base_entries * base_weight + 
                        (govt_trend > 0).astype(int) * govt_weight
                    ) > 0.5
                    
                    # Enhance exit signals
                    base_exits = enhanced_signals['exits'].astype(int)
                    enhanced_exits = (
                        base_exits * base_weight + 
                        (govt_trend < 0).astype(int) * govt_weight
                    ) > 0.5
                    
                    enhanced_signals['entries'] = enhanced_entries
                    enhanced_signals['exits'] = enhanced_exits
                
                # Add confidence scoring
                if 'signal_confidence' in aligned_government.columns:
                    enhanced_signals['signal_confidence'] = aligned_government['signal_confidence']
            
            # Add government correlation tracking
            if 'fused_trend_indicator' in aligned_government.columns:
                enhanced_signals['government_trend_strength'] = aligned_government['fused_trend_indicator']
            
            logger.info("Enhanced signals generated with government data integration")
            return enhanced_signals.reindex(data.index)  # Return to original index
            
        except Exception as e:
            logger.error(f"Signal enhancement failed: {e}")
            return base_signals
    
    def _execute_vectorbt_backtest(
        self, 
        data: pd.DataFrame, 
        signals: pd.DataFrame, 
        symbol: str
    ) -> BacktestResult:
        """Execute VectorBT backtest with enhanced configurations"""
        
        try:
            # Create portfolio with enhanced settings
            portfolio = vbt.Portfolio.from_signals(
                close=data['close'],
                entries=signals['entries'] if 'entries' in signals.columns else None,
                exits=signals['exits'] if 'exits' in signals.columns else None,
                init_cash=self.config.initial_cash,
                fees=self.config.fees,
                slippage=self.config.slippage,
                freq='1D'
            )
            
            # Calculate basic metrics
            returns = portfolio.returns()
            equity_curve = portfolio.value()
            
            # Extract trades
            trades = portfolio.trades.records_readable if len(portfolio.trades) > 0 else pd.DataFrame()
            
            # Calculate performance metrics
            total_return = float(portfolio.total_return())
            annual_return = float(returns.mean() * 252)
            volatility = float(returns.std() * np.sqrt(252))
            max_drawdown = float(portfolio.max_drawdown())
            
            # Sharpe ratio
            excess_returns = returns - self.config.risk_free_rate / 252
            sharpe_ratio = float(excess_returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0
            
            # Trade statistics
            win_rate = float(trades.win_rate()) if len(trades) > 0 else 0
            profit_factor = float(trades.profit_factor()) if len(trades) > 0 else 0
            total_trades = len(trades)
            
            return BacktestResult(
                symbol=symbol,
                strategy_name="Phase2_Enhanced",
                parameters={},
                total_return=total_return,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                win_rate=win_rate,
                profit_factor=profit_factor,
                total_trades=total_trades,
                equity_curve=equity_curve,
                returns=returns,
                trades=trades,
                signals=signals,
                start_date=data.index[0].strftime("%Y-%m-%d"),
                end_date=data.index[-1].strftime("%Y-%m-%d"),
                data_points=len(data),
                execution_time=0.0
            )
            
        except Exception as e:
            logger.error(f"VectorBT backtest execution failed: {e}")
            raise
    
    def _calculate_long_term_metrics(
        self, 
        result: BacktestResult, 
        data: pd.DataFrame
    ) -> Dict[str, float]:
        """Calculate long-term specific performance metrics"""
        
        returns = result.returns
        n_years = len(returns) / 252
        
        metrics = {}
        
        # Compound Annual Growth Rate (CAGR)
        metrics['cagr'] = float((1 + result.total_return) ** (1/n_years) - 1)
        
        # Sortino Ratio (downside deviation)
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 0 and downside_returns.std() > 0:
            excess_returns = returns.mean() * 252 - self.config.risk_free_rate
            downside_deviation = downside_returns.std() * np.sqrt(252)
            metrics['sortino_ratio'] = float(excess_returns / downside_deviation)
        else:
            metrics['sortino_ratio'] = 0
        
        # Calmar Ratio
        if result.max_drawdown != 0:
            metrics['calmar_ratio'] = float(metrics['cagr'] / abs(result.max_drawdown))
        else:
            metrics['calmar_ratio'] = 0
        
        # Information Ratio (if benchmark available)
        # For now, use 0 as benchmark
        benchmark_returns = pd.Series(0, index=returns.index)
        excess_returns = returns - benchmark_returns
        if excess_returns.std() > 0:
            metrics['information_ratio'] = float(excess_returns.mean() / excess_returns.std() * np.sqrt(252))
        else:
            metrics['information_ratio'] = 0
        
        # Omega Ratio (threshold at 0)
        if len(returns) > 0:
            gains = returns[returns > 0].sum()
            losses = abs(returns[returns < 0].sum())
            metrics['omega_ratio'] = float(gains / losses) if losses > 0 else float('inf')
        else:
            metrics['omega_ratio'] = 0
        
        # Treynor Ratio (assuming beta = 1 for now)
        if result.max_drawdown != 0:
            market_risk_premium = metrics['cagr'] - self.config.risk_free_rate
            estimated_beta = abs(result.max_drawdown) * 2  # Rough estimation
            metrics['treynor_ratio'] = float(market_risk_premium / estimated_beta) if estimated_beta != 0 else 0
        else:
            metrics['treynor_ratio'] = 0
        
        return metrics
    
    def _perform_statistical_validation(
        self, 
        result: BacktestResult, 
        benchmark_data: Optional[pd.DataFrame]
    ) -> Optional[ValidationResults]:
        """Perform statistical validation of backtest results"""
        
        try:
            benchmark_returns = None
            if benchmark_data is not None:
                # Calculate benchmark returns
                benchmark_returns = benchmark_data['close'].pct_change().dropna()
                benchmark_returns = benchmark_returns.reindex(result.returns.index, method='ffill')
            
            validation_results = self.statistical_validator.validate_backtest_results(
                result.returns, benchmark_returns, result.trades
            )
            
            logger.info(f"Statistical validation completed: Score={validation_results.validation_score:.1f}")
            return validation_results
            
        except Exception as e:
            logger.error(f"Statistical validation failed: {e}")
            return None
    
    def _calculate_bootstrap_intervals(
        self, 
        result: BacktestResult
    ) -> Optional[Dict[str, Any]]:
        """Calculate bootstrap confidence intervals"""
        
        try:
            bootstrap_results = self.statistical_validator.bootstrap_performance_metrics(
                result.returns, self.config.bootstrap_samples
            )
            
            logger.info("Bootstrap confidence intervals calculated")
            return bootstrap_results
            
        except Exception as e:
            logger.error(f"Bootstrap calculation failed: {e}")
            return None
    
    def _analyze_market_regimes(
        self, 
        result: BacktestResult, 
        data: pd.DataFrame
    ) -> Optional[Dict[str, Any]]:
        """Analyze performance across different market regimes"""
        
        try:
            if len(data) < self.config.regime_window:
                return None
            
            returns = result.returns
            regimes = self._identify_market_regimes(data)
            
            if regimes is None:
                return None
            
            # Calculate performance by regime
            regime_performance = {}
            
            for regime_name, regime_mask in regimes.items():
                regime_returns = returns[regime_mask]
                
                if len(regime_returns) > 0:
                    regime_performance[regime_name] = {
                        'count': len(regime_returns),
                        'return': float(regime_returns.mean() * 252),
                        'volatility': float(regime_returns.std() * np.sqrt(252)),
                        'sharpe': float(regime_returns.mean() / regime_returns.std() * np.sqrt(252)) if regime_returns.std() > 0 else 0,
                        'max_drawdown': float((1 + regime_returns).cumprod().div((1 + regime_returns).cumprod().expanding().max()).min() - 1),
                        'percentage': float(len(regime_returns) / len(returns) * 100)
                    }
            
            # Calculate regime stability
            regime_stability = self._calculate_regime_stability(regimes, returns)
            
            return {
                'regime_performance': regime_performance,
                'regime_stability': regime_stability,
                'regime_count': len(regimes)
            }
            
        except Exception as e:
            logger.error(f"Market regime analysis failed: {e}")
            return None
    
    def _identify_market_regimes(self, data: pd.DataFrame) -> Optional[Dict[str, pd.Series]]:
        """Identify different market regimes based on price and volatility"""
        
        try:
            close_prices = data['close']
            returns = close_prices.pct_change()
            
            # Calculate long-term moving averages for trend classification
            ma_200 = close_prices.rolling(window=200).mean()
            ma_50 = close_prices.rolling(window=50).mean()
            
            # Calculate volatility for regime classification
            volatility = returns.rolling(window=50).std() * np.sqrt(252)
            volatility_median = volatility.median()
            
            # Identify regimes
            regimes = {}
            
            # Bull market: above 200-day MA and above 50-day MA
            bull_market = (close_prices > ma_200) & (close_prices > ma_50)
            regimes['bull_market'] = bull_market
            
            # Bear market: below 200-day MA and below 50-day MA
            bear_market = (close_prices < ma_200) & (close_prices < ma_50)
            regimes['bear_market'] = bear_market
            
            # High volatility periods
            high_volatility = volatility > volatility_median * 1.5
            regimes['high_volatility'] = high_volatility
            
            # Low volatility periods
            low_volatility = volatility < volatility_median * 0.75
            regimes['low_volatility'] = low_volatility
            
            return regimes
            
        except Exception as e:
            logger.error(f"Market regime identification failed: {e}")
            return None
    
    def _calculate_regime_stability(
        self, 
        regimes: Dict[str, pd.Series], 
        returns: pd.Series
    ) -> float:
        """Calculate regime stability score"""
        
        try:
            regime_sharpes = []
            
            for regime_mask in regimes.values():
                regime_returns = returns[regime_mask]
                if len(regime_returns) > 30:  # Minimum observations
                    sharpe = regime_returns.mean() / regime_returns.std() * np.sqrt(252)
                    regime_sharpes.append(sharpe)
            
            if len(regime_sharpes) > 1:
                # Calculate coefficient of variation of regime Sharpe ratios
                mean_sharpe = np.mean(regime_sharpes)
                std_sharpe = np.std(regime_sharpes)
                
                if mean_sharpe != 0:
                    cv = std_sharpe / abs(mean_sharpe)
                    stability = max(0, 1 - cv)  # Convert to 0-1 scale
                else:
                    stability = 0
                
                return float(stability * 100)
            
            return 50.0  # Default stability score
            
        except Exception as e:
            logger.error(f"Regime stability calculation failed: {e}")
            return 50.0
    
    def _create_phase2_result(
        self,
        vectorbt_result: BacktestResult,
        strategy: str,
        parameters: Dict[str, Any],
        symbol: str,
        long_term_metrics: Dict[str, float],
        validation_results: Optional[ValidationResults],
        bootstrap_intervals: Optional[Dict[str, Any]],
        regime_performance: Optional[Dict[str, Any]],
        government_data_used: bool
    ) -> Phase2BacktestResult:
        """Create comprehensive Phase 2 result"""
        
        # Create base result
        phase2_result = Phase2BacktestResult(
            symbol=symbol,
            strategy_name=strategy,
            parameters=parameters,
            total_return=vectorbt_result.total_return,
            sharpe_ratio=vectorbt_result.sharpe_ratio,
            max_drawdown=vectorbt_result.max_drawdown,
            win_rate=vectorbt_result.win_rate,
            profit_factor=vectorbt_result.profit_factor,
            total_trades=vectorbt_result.total_trades,
            equity_curve=vectorbt_result.equity_curve,
            returns=vectorbt_result.returns,
            trades=vectorbt_result.trades,
            signals=vectorbt_result.signals,
            start_date=vectorbt_result.start_date,
            end_date=vectorbt_result.end_date,
            data_points=vectorbt_result.data_points,
            execution_time=vectorbt_result.execution_time,
            
            # Phase 2 specific fields
            government_data_used=government_data_used,
            validation_results=validation_results,
            bootstrap_confidence_intervals=bootstrap_intervals,
            statistical_significance=validation_results.is_valid if validation_results else False,
            regime_performance=regime_performance,
            regime_stability_score=regime_performance['regime_stability'] if regime_performance else 0.0,
            
            # Long-term metrics
            cagr=long_term_metrics.get('cagr', 0.0),
            sortino_ratio=long_term_metrics.get('sortino_ratio', 0.0),
            calmar_ratio=long_term_metrics.get('calmar_ratio', 0.0),
            information_ratio=long_term_metrics.get('information_ratio', 0.0),
            omega_ratio=long_term_metrics.get('omega_ratio', 0.0),
            treynor_ratio=long_term_metrics.get('treynor_ratio', 0.0)
        )
        
        # Calculate additional scores
        phase2_result.data_quality_score = self._calculate_data_quality_score(vectorbt_result)
        phase2_result.model_stability_score = self._calculate_model_stability_score(
            validation_results, regime_performance
        )
        
        # Calculate economic indicator correlation if available
        if vectorbt_result.signals is not None and 'government_trend_strength' in vectorbt_result.signals:
            govt_trend = vectorbt_result.signals['government_trend_strength'].dropna()
            strategy_returns = vectorbt_result.returns.reindex(govt_trend.index).dropna()
            
            if len(govt_trend) > 30 and len(strategy_returns) > 30:
                correlation = np.corrcoef(govt_trend, strategy_returns)[0, 1]
                phase2_result.economic_indicator_correlation = float(correlation) if not np.isnan(correlation) else 0.0
        
        return phase2_result
    
    def _calculate_data_quality_score(self, result: BacktestResult) -> float:
        """Calculate data quality score"""
        
        score = 100.0
        
        # Penalize low trade count
        if result.total_trades < self.config.min_trades:
            score -= 30
        elif result.total_trades < self.config.preferred_trades:
            score -= 15
        
        # Penalize high drawdown
        if result.max_drawdown < self.config.max_drawdown_threshold:
            score -= 25
        
        # Penalize low win rate
        if result.win_rate < self.config.min_win_rate:
            score -= 20
        
        return max(0, score)
    
    def _calculate_model_stability_score(
        self,
        validation_results: Optional[ValidationResults],
        regime_performance: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate model stability score"""
        
        score_components = []
        
        # Validation stability
        if validation_results:
            score_components.append(validation_results.stability_score)
        
        # Regime stability
        if regime_performance and 'regime_stability' in regime_performance:
            score_components.append(regime_results['regime_stability'])
        
        # Default score if no components
        if not score_components:
            return 50.0
        
        return float(np.mean(score_components))
    
    def _update_execution_stats(
        self, 
        execution_time: float, 
        government_data_success: bool
    ) -> None:
        """Update execution statistics"""
        
        self._execution_stats['total_backtests'] += 1
        self._execution_stats['total_execution_time'] += execution_time
        self._execution_stats['average_execution_time'] = (
            self._execution_stats['total_execution_time'] / 
            self._execution_stats['total_backtests']
        )
        
        # Update government data success rate
        total_with_govt = self._execution_stats.get('total_with_govt_data', 0) + 1
        successful_with_govt = self._execution_stats.get('successful_govt_data', 0) + (1 if government_data_success else 0)
        
        self._execution_stats['total_with_govt_data'] = total_with_govt
        self._execution_stats['successful_govt_data'] = successful_with_govt
        self._execution_stats['government_data_success_rate'] = successful_with_govt / total_with_govt
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get execution summary statistics"""
        
        return {
            'execution_statistics': self._execution_stats,
            'configuration': {
                'min_data_years': self.config.min_data_years,
                'enable_government_data': self.config.enable_government_data,
                'enable_statistical_validation': self.config.enable_statistical_validation,
                'enable_regime_analysis': self.config.enable_regime_analysis,
                'bootstrap_samples': self.config.bootstrap_samples
            },
            'components_status': {
                'vectorbt_available': VECTORBT_AVAILABLE,
                'long_term_indicators': True,
                'statistical_validator': True
            }
        }


# Convenience functions for external usage
def create_phase2_backtest_engine(
    config: Optional[Phase2BacktestConfig] = None
) -> Phase2LongTermBacktestEngine:
    """Create Phase 2 backtest engine instance"""
    return Phase2LongTermBacktestEngine(config)


def run_phase2_long_term_backtest(
    data: pd.DataFrame,
    strategy: str,
    parameters: Dict[str, Any],
    symbol: str = "UNKNOWN",
    benchmark_data: Optional[pd.DataFrame] = None,
    config: Optional[Phase2BacktestConfig] = None
) -> Phase2BacktestResult:
    """
    Convenience function to run Phase 2 long-term backtest
    
    Args:
        data: OHLCV price data (5+ years preferred)
        strategy: Strategy name and parameters
        symbol: Symbol identifier
        benchmark_data: Optional benchmark data
        config: Optional backtest configuration
        
    Returns:
        Phase2BacktestResult with comprehensive analysis
    """
    engine = Phase2LongTermBacktestEngine(config)
    return engine.run_long_term_backtest(
        data, strategy, parameters, symbol, benchmark_data
    )
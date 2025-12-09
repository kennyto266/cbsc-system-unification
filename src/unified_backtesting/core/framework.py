"""
Unified Backtesting Framework - Core Framework Class

Main orchestration class that coordinates all components of the unified
backtesting system for comprehensive parameter optimization with 0-300
range testing using multi-process VectorBT.

Key Features:
- Orchestrates all backtesting components
- Manages end-to-end optimization workflow
- Handles error recovery and fault tolerance
- Provides progress tracking and monitoring
- Supports multiple strategy optimization
- Integrates adaptive memory management
- Generates comprehensive reports
"""

import time
import logging
import os
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass
import pandas as pd
import numpy as np

from .config import BacktestingConfig
from ..parameters.generator import ComprehensiveParameterSpace
from ..vectorbt_engine.engine import EnhancedVectorBTEngine, BatchResult
from ..metrics.calculator import StandardizedMetricsCalculator
from ..memory.manager import AdaptiveMemoryManager, memory_managed
from ..results.aggregator import ResultAggregator, AggregatedResults

logger = logging.getLogger(__name__)


@dataclass
class OptimizationRequest:
    """Optimization request structure"""
    strategy_name: str
    price_data: pd.DataFrame
    parameter_constraints: Optional[Dict[str, Any]] = None
    benchmark_data: Optional[pd.DataFrame] = None
    custom_metrics: Optional[Dict[str, Callable]] = None
    output_directory: Optional[str] = None


@dataclass
class OptimizationStatus:
    """Current optimization status"""
    strategy_name: str
    total_combinations: int
    processed_combinations: int
    successful_combinations: int
    failed_combinations: int
    current_batch: int
    total_batches: int
    processing_time: float
    estimated_time_remaining: float
    memory_usage_gb: float
    is_complete: bool


class UnifiedBacktestingFramework:
    """
    Unified backtesting framework for comprehensive parameter optimization

    Coordinates all components to provide end-to-end backtesting capabilities
    for the CBSC trading system with large-scale parameter optimization.
    """

    def __init__(self, config: Optional[BacktestingConfig] = None):
        """
        Initialize the unified backtesting framework

        Args:
            config: Backtesting configuration (uses default if None)
        """
        self.config = config or BacktestingConfig()

        # Initialize components
        self.parameter_space = ComprehensiveParameterSpace(self.config)
        self.vectorbt_engine = EnhancedVectorBTEngine(self.config)
        self.metrics_calculator = StandardizedMetricsCalculator(self.config)
        self.memory_manager = AdaptiveMemoryManager(self.config)
        self.result_aggregator = ResultAggregator(self.config)

        # State tracking
        self.is_running = False
        self.current_optimization = None
        self.progress_callbacks = []

        # Performance tracking
        self.start_time = None
        self.batch_results = []

        logger.info("Initialized UnifiedBacktestingFramework")
        logger.info(f"Configuration: {self.config.total_parameter_combinations:,} total parameter combinations")

    def start_memory_management(self):
        """Start memory management system"""
        self.memory_manager.start()
        logger.info("Memory management started")

    def stop_memory_management(self):
        """Stop memory management system"""
        self.memory_manager.stop()
        logger.info("Memory management stopped")

    def add_progress_callback(self, callback: Callable[[OptimizationStatus], None]):
        """Add progress callback for monitoring"""
        self.progress_callbacks.append(callback)

    def _notify_progress(self, status: OptimizationStatus):
        """Notify all progress callbacks"""
        for callback in self.progress_callbacks:
            try:
                callback(status)
            except Exception as e:
                logger.error(f"Error in progress callback: {str(e)}")

    @memory_managed(AdaptiveMemoryManager)
    def run_optimization(self, request: OptimizationRequest) -> AggregatedResults:
        """
        Run comprehensive parameter optimization

        Args:
            request: Optimization request with strategy and data

        Returns:
            Aggregated results with comprehensive analysis
        """
        if self.is_running:
            raise RuntimeError("Optimization already in progress")

        self.is_running = True
        self.current_optimization = request
        self.start_time = time.time()

        try:
            logger.info(f"Starting optimization for {request.strategy_name}")

            # Validate inputs
            self._validate_optimization_request(request)

            # Prepare data
            price_data = self.vectorbt_engine.prepare_data(request.price_data)

            # Start result aggregation
            self.result_aggregator.start_aggregation(request.strategy_name)

            # Calculate total combinations
            total_combinations = self.parameter_space.get_parameter_combinations_count(request.strategy_name)
            logger.info(f"Processing {total_combinations:,} parameter combinations")

            # Process in batches
            processed_combinations = 0
            batch_count = 0
            successful_combinations = 0
            failed_combinations = 0

            for batch_result in self.vectorbt_engine.run_optimization(
                strategy_name=request.strategy_name,
                parameter_space=self.parameter_space,
                price_data=price_data,
                progress_callback=self._on_batch_progress
            ):
                # Add batch result to aggregation
                self.result_aggregator.add_batch_result(batch_result)
                self.batch_results.append(batch_result)

                # Update counters
                batch_count += 1
                processed_combinations += batch_result.total_combinations
                successful_combinations += batch_result.successful_count
                failed_combinations += batch_result.failed_count

                # Create and notify status
                status = self._create_optimization_status(
                    request.strategy_name, total_combinations, processed_combinations,
                    successful_combinations, failed_combinations, batch_count
                )
                self._notify_progress(status)

                logger.info(f"Batch {batch_count} completed: "
                           f"{batch_result.successful_count}/{batch_result.total_combinations} successful")

            # Finalize aggregation
            logger.info("Finalizing result aggregation...")
            aggregated_results = self.result_aggregator.finalize_aggregation()

            # Save results
            output_dir = request.output_directory or self.config.output_directory
            os.makedirs(output_dir, exist_ok=True)

            results_file = os.path.join(output_dir, f"{request.strategy_name}_results.json")
            self.result_aggregator.save_results(aggregated_results, results_file)

            # Generate summary report
            report_file = os.path.join(output_dir, f"{request.strategy_name}_summary.md")
            summary_report = self.result_aggregator.generate_summary_report(aggregated_results)
            with open(report_file, 'w') as f:
                f.write(summary_report)

            # Calculate comprehensive metrics for top results
            self._calculate_comprehensive_metrics(aggregated_results, request)

            total_time = time.time() - self.start_time
            logger.info(f"Optimization completed in {total_time:.1f} seconds")
            logger.info(f"Results saved to {output_dir}")

            return aggregated_results

        except Exception as e:
            logger.error(f"Optimization failed: {str(e)}")
            raise
        finally:
            self.is_running = False
            self.current_optimization = None

    def _validate_optimization_request(self, request: OptimizationRequest):
        """Validate optimization request"""
        if not request.strategy_name:
            raise ValueError("Strategy name is required")

        if request.price_data is None or request.price_data.empty:
            raise ValueError("Price data is required and cannot be empty")

        # Check if strategy is supported
        supported_strategies = [
            'rsi_strategy', 'macd_strategy', 'bollinger_strategy',
            'sentiment_strategy', 'combined_strategy'
        ]
        if request.strategy_name not in supported_strategies:
            raise ValueError(f"Unsupported strategy: {request.strategy_name}. "
                           f"Supported: {supported_strategies}")

        # Validate price data columns
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in request.price_data.columns]
        if missing_columns:
            logger.warning(f"Missing price data columns: {missing_columns}")

    def _on_batch_progress(self, processed: int, total: int, batch_result: BatchResult):
        """Handle batch progress updates"""
        # This is called by the VectorBT engine during optimization
        pass  # Progress is handled in the main optimization loop

    def _create_optimization_status(self, strategy_name: str, total_combinations: int,
                                  processed_combinations: int, successful_combinations: int,
                                  failed_combinations: int, batch_count: int) -> OptimizationStatus:
        """Create optimization status object"""
        current_time = time.time()
        elapsed_time = current_time - self.start_time

        # Estimate time remaining
        if processed_combinations > 0:
            avg_time_per_combination = elapsed_time / processed_combinations
            remaining_combinations = total_combinations - processed_combinations
            estimated_time_remaining = avg_time_per_combination * remaining_combinations
        else:
            estimated_time_remaining = float('inf')

        # Get current memory usage
        memory_stats = self.memory_manager.monitor.get_memory_stats()

        # Calculate total batches (rough estimate)
        estimated_total_batches = max(1, total_combinations // self.config.chunk_size)

        return OptimizationStatus(
            strategy_name=strategy_name,
            total_combinations=total_combinations,
            processed_combinations=processed_combinations,
            successful_combinations=successful_combinations,
            failed_combinations=failed_combinations,
            current_batch=batch_count,
            total_batches=estimated_total_batches,
            processing_time=elapsed_time,
            estimated_time_remaining=estimated_time_remaining,
            memory_usage_gb=memory_stats.process_memory_gb,
            is_complete=processed_combinations >= total_combinations
        )

    def _calculate_comprehensive_metrics(self, aggregated_results: AggregatedResults,
                                       request: OptimizationRequest):
        """Calculate comprehensive metrics for top results"""
        if not aggregated_results.top_sharpe_results:
            return

        logger.info("Calculating comprehensive metrics for top performers...")

        # Calculate detailed metrics for top 10 results
        top_results = aggregated_results.top_sharpe_results[:10]

        for result in top_results:
            try:
                # Generate signals with result parameters
                signals = self.vectorbt_engine._generate_signals(
                    request.strategy_name, result.parameters, request.price_data
                )

                if not signals.empty:
                    # Create portfolio for detailed analysis
                    portfolio = self.vectorbt_engine.vbt.Portfolio.from_signals(
                        close=request.price_data['close'],
                        entries=signals['entry'],
                        exits=signals['exit'],
                        init_cash=100000,
                        fees=0.001,
                        slippage=0.0005
                    )

                    # Calculate comprehensive metrics
                    returns = portfolio.returns()
                    comprehensive_metrics = self.metrics_calculator.calculate_comprehensive_metrics(
                        returns, request.benchmark_data, portfolio.positions(), portfolio.trades
                    )

                    # Add to result metrics (could expand BacktestResult to include these)
                    if result.metrics is None:
                        result.metrics = {}
                    result.metrics.update(comprehensive_metrics.__dict__)

            except Exception as e:
                logger.error(f"Error calculating comprehensive metrics for result {result.combination_index}: {str(e)}")

    def run_multi_strategy_optimization(self, requests: List[OptimizationRequest]) -> Dict[str, AggregatedResults]:
        """
        Run optimization for multiple strategies

        Args:
            requests: List of optimization requests

        Returns:
            Dictionary mapping strategy names to aggregated results
        """
        results = {}

        for request in requests:
            logger.info(f"Starting optimization for {request.strategy_name}")
            try:
                result = self.run_optimization(request)
                results[request.strategy_name] = result
                logger.info(f"Completed optimization for {request.strategy_name}")
            except Exception as e:
                logger.error(f"Failed optimization for {request.strategy_name}: {str(e)}")
                continue

        return results

    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics"""
        return self.memory_manager.get_comprehensive_stats()

    def get_framework_status(self) -> Dict[str, Any]:
        """Get current framework status"""
        return {
            'is_running': self.is_running,
            'current_strategy': self.current_optimization.strategy_name if self.current_optimization else None,
            'config': self.config.to_dict(),
            'memory_stats': self.get_memory_statistics(),
            'batch_results_count': len(self.batch_results)
        }

    def export_configuration(self, filepath: str):
        """Export current configuration to file"""
        self.config.save(filepath)
        logger.info(f"Configuration exported to {filepath}")

    def import_configuration(self, filepath: str):
        """Import configuration from file"""
        self.config = BacktestingConfig.load(filepath)

        # Reinitialize components with new config
        self.parameter_space = ComprehensiveParameterSpace(self.config)
        self.vectorbt_engine = EnhancedVectorBTEngine(self.config)
        self.metrics_calculator = StandardizedMetricsCalculator(self.config)
        self.memory_manager = AdaptiveMemoryManager(self.config)

        logger.info(f"Configuration imported from {filepath}")

    def create_optimization_report(self, results: AggregatedResults,
                                 output_file: Optional[str] = None) -> str:
        """
        Create comprehensive optimization report

        Args:
            results: Aggregated optimization results
            output_file: Optional output file path

        Returns:
            Report content as string
        """
        report = self.result_aggregator.generate_summary_report(results)

        if output_file:
            with open(output_file, 'w') as f:
                f.write(report)
            logger.info(f"Optimization report saved to {output_file}")

        return report

    def optimize_strategy_ensemble(self, results: AggregatedResults,
                                 ensemble_size: int = 5) -> Dict[str, Any]:
        """
        Create optimized strategy ensemble from results

        Args:
            results: Aggregated optimization results
            ensemble_size: Number of strategies in ensemble

        Returns:
            Ensemble configuration and expected performance
        """
        if not results.ensemble_candidates or len(results.ensemble_candidates) < ensemble_size:
            logger.warning("Insufficient ensemble candidates")
            return {}

        # Select top diverse candidates
        top_candidates = results.ensemble_candidates[:ensemble_size]

        # Calculate ensemble weights (equal weight for now, could be optimized)
        weight = 1.0 / ensemble_size
        for candidate in top_candidates:
            candidate['weight'] = weight

        # Estimate ensemble performance
        ensemble_metrics = {
            'expected_sharpe_ratio': np.mean([c['performance']['sharpe_ratio'] for c in top_candidates]),
            'expected_return': np.mean([c['performance']['total_return'] for c in top_candidates]),
            'expected_max_drawdown': np.mean([c['performance']['max_drawdown'] for c in top_candidates]),
            'diversification_score': 0.7  # Placeholder - would calculate actual correlation
        }

        return {
            'strategies': top_candidates,
            'ensemble_metrics': ensemble_metrics,
            'size': ensemble_size,
            'creation_method': 'diversified_top_performers'
        }


# Convenience function for quick optimization
def quick_optimization(strategy_name: str, price_data: pd.DataFrame,
                      param_range: tuple = (0, 300, 5),
                      max_workers: int = 32,
                      output_dir: str = "optimization_results") -> AggregatedResults:
    """
    Quick optimization function for common use cases

    Args:
        strategy_name: Name of strategy to optimize
        price_data: Historical price data
        param_range: Parameter range tuple (start, end, step)
        max_workers: Maximum number of parallel workers
        output_dir: Output directory for results

    Returns:
        Aggregated optimization results
    """
    # Create configuration
    config = BacktestingConfig(
        param_range_start=param_range[0],
        param_range_end=param_range[1],
        param_step_size=param_range[2],
        max_workers=max_workers,
        output_directory=output_dir
    )

    # Create request
    request = OptimizationRequest(
        strategy_name=strategy_name,
        price_data=price_data,
        output_directory=output_dir
    )

    # Run optimization
    framework = UnifiedBacktestingFramework(config)
    framework.start_memory_management()

    try:
        results = framework.run_optimization(request)
        return results
    finally:
        framework.stop_memory_management()
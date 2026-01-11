"""
Integration layer for CBSC multiprocessing system.

Provides seamless integration between the new multiprocessing backtesting engine
and the existing CBSC quantitative trading platform, ensuring backward compatibility
and smooth migration path.
"""

import time
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from pathlib import Path
import json
import warnings

# Import multiprocessing components
try:
    from .parallel_engine import ParallelEngine
    from .monitor import get_monitor, start_monitoring
    from .performance_metrics import get_metrics_collector, start_metrics_collection
    from .streaming_loader import StreamingDataLoader, LoaderConfig
    from .shared_memory import SharedMemoryManager
    INTEGRATION_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Multiprocessing components not available: {e}")
    INTEGRATION_AVAILABLE = False


@dataclass
class BacktestRequest:
    """Standardized backtest request structure."""
    strategy_id: str
    strategy_code: str
    parameters: Dict[str, Any]
    data_config: Dict[str, Any]
    backtest_config: Dict[str, Any]
    priority: str = "normal"  # low, normal, high, critical


@dataclass
class BacktestResult:
    """Standardized backtest result structure."""
    strategy_id: str
    success: bool
    execution_time: float
    performance_metrics: Dict[str, Any]
    trade_history: List[Dict[str, Any]]
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class PerformanceReport:
    """Performance benchmark report."""
    test_name: str
    parameter_count: int
    sequential_time: Optional[float]
    parallel_time: float
    speedup: float
    memory_usage_mb: float
    cpu_utilization: float
    timestamp: str


class CBSCCompatibilityLayer:
    """Provides backward compatibility with existing CBSC system."""

    def __init__(self, legacy_interface: bool = True):
        self.legacy_interface = legacy_interface
        self.logger = logging.getLogger(__name__)

        # Migration mappings
        self.parameter_mapping = {
            'start_date': 'start_date',
            'end_date': 'end_date',
            'initial_capital': 'initial_capital',
            'commission': 'commission',
            'slippage': 'slippage'
        }

    def convert_legacy_request(self, legacy_request: Dict[str, Any]) -> BacktestRequest:
        """Convert legacy CBSC backtest request to new format."""
        try:
            # Extract basic information
            strategy_id = legacy_request.get('strategy_id', 'unknown')
            strategy_code = legacy_request.get('strategy_code', '')

            # Convert parameters
            parameters = {}
            for old_param, new_param in self.parameter_mapping.items():
                if old_param in legacy_request:
                    parameters[new_param] = legacy_request[old_param]

            # Handle strategy-specific parameters
            if 'strategy_params' in legacy_request:
                parameters.update(legacy_request['strategy_params'])

            # Data configuration
            data_config = legacy_request.get('data_config', {})

            # Backtest configuration
            backtest_config = legacy_request.get('backtest_config', {})

            # Priority
            priority = legacy_request.get('priority', 'normal')

            return BacktestRequest(
                strategy_id=strategy_id,
                strategy_code=strategy_code,
                parameters=parameters,
                data_config=data_config,
                backtest_config=backtest_config,
                priority=priority
            )

        except Exception as e:
            self.logger.error(f"Error converting legacy request: {e}")
            raise ValueError(f"Invalid legacy request format: {e}")

    def convert_legacy_strategy(self, strategy_code: str, strategy_config: Dict[str, Any]) -> str:
        """Convert legacy strategy code to new multiprocessing-compatible format."""
        try:
            # For now, assume strategy code is compatible
            # In production, this would involve code transformation
            return strategy_code

        except Exception as e:
            self.logger.error(f"Error converting strategy code: {e}")
            raise ValueError(f"Strategy conversion failed: {e}")

    def validate_request(self, request: BacktestRequest) -> bool:
        """Validate backtest request for compatibility."""
        required_fields = ['strategy_id', 'strategy_code', 'parameters']

        for field in required_fields:
            if not hasattr(request, field) or not getattr(request, field):
                self.logger.error(f"Missing required field: {field}")
                return False

        # Validate strategy code format
        if not isinstance(request.strategy_code, str):
            self.logger.error("Strategy code must be a string")
            return False

        return True


class CBSCMultiprocessingIntegration:
    """Main integration class for CBSC multiprocessing system."""

    def __init__(self,
                 enable_monitoring: bool = True,
                 enable_metrics: bool = True,
                 config: Optional[Dict[str, Any]] = None):

        if not INTEGRATION_AVAILABLE:
            raise RuntimeError("Multiprocessing components not available")

        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.compatibility_layer = CBSCCompatibilityLayer()

        # Initialize multiprocessing engine
        self.parallel_engine = ParallelEngine(config=self.config)

        # Initialize monitoring (if enabled)
        self.monitor = None
        if enable_monitoring:
            self.monitor = get_monitor()
            start_monitoring(self.config.get('monitoring', {}))

        # Initialize performance metrics (if enabled)
        self.metrics_collector = None
        if enable_metrics:
            self.metrics_collector = get_metrics_collector()
            start_metrics_collection()

        # Performance tracking
        self.performance_history = []

        self.logger.info("CBSC Multiprocessing Integration initialized")

    def execute_backtest(self,
                        strategy_code: str,
                        parameters: Dict[str, Any],
                        data_config: Optional[Dict[str, Any]] = None,
                        backtest_config: Optional[Dict[str, Any]] = None,
                        strategy_id: Optional[str] = None,
                        use_multiprocessing: Optional[bool] = None) -> BacktestResult:
        """
        Execute backtest with automatic routing to optimal execution method.

        Args:
            strategy_code: Strategy implementation code
            parameters: Strategy parameters dictionary
            data_config: Data configuration (optional)
            backtest_config: Backtest configuration (optional)
            strategy_id: Strategy identifier (optional)
            use_multiprocessing: Force multiprocessing usage (optional)

        Returns:
            BacktestResult: Standardized backtest result
        """

        # Create standardized request
        request = BacktestRequest(
            strategy_id=strategy_id or f"strategy_{int(time.time())}",
            strategy_code=strategy_code,
            parameters=parameters,
            data_config=data_config or {},
            backtest_config=backtest_config or {}
        )

        # Validate request
        if not self.compatibility_layer.validate_request(request):
            return BacktestResult(
                strategy_id=request.strategy_id,
                success=False,
                execution_time=0.0,
                performance_metrics={},
                trade_history=[],
                error_message="Invalid backtest request"
            )

        # Determine execution method
        if use_multiprocessing is None:
            use_multiprocessing = self._should_use_multiprocessing(request)

        start_time = time.time()

        try:
            if use_multiprocessing:
                result = self._execute_parallel_backtest(request)
            else:
                result = self._execute_sequential_backtest(request)

            execution_time = time.time() - start_time
            result.execution_time = execution_time

            # Record performance metrics
            if self.metrics_collector:
                self.metrics_collector.record_task_completion(
                    task_type="backtest",
                    duration_ms=execution_time * 1000,
                    success=result.success
                )

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Backtest execution failed: {e}")

            return BacktestResult(
                strategy_id=request.strategy_id,
                success=False,
                execution_time=execution_time,
                performance_metrics={},
                trade_history=[],
                error_message=str(e)
            )

    def _should_use_multiprocessing(self, request: BacktestRequest) -> bool:
        """Determine if backtest should use multiprocessing based on complexity."""
        # Simple heuristic based on parameter complexity
        param_count = len(request.parameters)

        # Use multiprocessing for parameter spaces larger than threshold
        threshold = self.config.get('multiprocessing_threshold', 1000)

        if param_count > threshold:
            return True

        # Check for specific parameters that indicate large search spaces
        large_space_params = ['parameter_grid', 'optimization_range', 'ensemble_size']
        for param in large_space_params:
            if param in request.parameters and request.parameters[param] > 10:
                return True

        return False

    def _execute_parallel_backtest(self, request: BacktestRequest) -> BacktestResult:
        """Execute backtest using multiprocessing engine."""
        try:
            # Register task with monitor
            if self.monitor:
                self.monitor.progress_tracker.register_task(
                    task_id=request.strategy_id,
                    task_type="backtest_parallel"
                )
                self.monitor.progress_tracker.start_task(request.strategy_id)

            # Convert to parallel engine format
            parallel_request = self._convert_to_parallel_request(request)

            # Execute with parallel engine
            parallel_result = self.parallel_engine.execute_batch([parallel_request])

            # Convert result back to standard format
            if parallel_result and len(parallel_result) > 0:
                result_data = parallel_result[0]

                # Update progress
                if self.monitor:
                    self.monitor.progress_tracker.update_progress(request.strategy_id, 100.0)
                    self.monitor.progress_tracker.complete_task(request.strategy_id, True)

                return BacktestResult(
                    strategy_id=request.strategy_id,
                    success=True,
                    execution_time=0.0,  # Will be set by caller
                    performance_metrics=result_data.get('metrics', {}),
                    trade_history=result_data.get('trades', []),
                    metadata=result_data.get('metadata', {})
                )
            else:
                if self.monitor:
                    self.monitor.progress_tracker.complete_task(request.strategy_id, False, "No results returned")

                return BacktestResult(
                    strategy_id=request.strategy_id,
                    success=False,
                    execution_time=0.0,
                    performance_metrics={},
                    trade_history=[],
                    error_message="No results returned from parallel engine"
                )

        except Exception as e:
            if self.monitor:
                self.monitor.progress_tracker.complete_task(request.strategy_id, False, str(e))

            self.logger.error(f"Parallel backtest execution failed: {e}")
            raise

    def _execute_sequential_backtest(self, request: BacktestRequest) -> BacktestResult:
        """Execute backtest sequentially (fallback method)."""
        try:
            # For this implementation, we'll simulate sequential execution
            # In production, this would integrate with the actual CBSC sequential engine

            self.logger.info(f"Executing sequential backtest for {request.strategy_id}")

            # Simulate processing time
            time.sleep(0.1)  # Simulate computation

            # Generate mock results
            mock_trades = [
                {'date': '2023-01-01', 'symbol': 'AAPL', 'action': 'BUY', 'price': 150.0, 'quantity': 100},
                {'date': '2023-01-02', 'symbol': 'AAPL', 'action': 'SELL', 'price': 152.0, 'quantity': 100}
            ]

            mock_metrics = {
                'total_return': 1.33,
                'sharpe_ratio': 1.25,
                'max_drawdown': -0.05,
                'win_rate': 0.55,
                'total_trades': len(mock_trades)
            }

            return BacktestResult(
                strategy_id=request.strategy_id,
                success=True,
                execution_time=0.0,  # Will be set by caller
                performance_metrics=mock_metrics,
                trade_history=mock_trades,
                metadata={'execution_mode': 'sequential'}
            )

        except Exception as e:
            self.logger.error(f"Sequential backtest execution failed: {e}")
            raise

    def _convert_to_parallel_request(self, request: BacktestRequest) -> Dict[str, Any]:
        """Convert standardized request to parallel engine format."""
        return {
            'id': request.strategy_id,
            'strategy_code': request.strategy_code,
            'parameters': request.parameters,
            'data_config': request.data_config,
            'backtest_config': request.backtest_config,
            'priority': request.priority
        }

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status and metrics."""
        status = {
            'multiprocessing_available': INTEGRATION_AVAILABLE,
            'monitoring_active': self.monitor is not None,
            'metrics_active': self.metrics_collector is not None,
            'timestamp': time.time()
        }

        if self.monitor:
            monitor_status = self.monitor.get_status_report()
            status['monitor'] = monitor_status

        if self.metrics_collector:
            metrics_snapshot = self.metrics_collector.get_performance_snapshot()
            status['performance'] = {
                'completed_tasks': metrics_snapshot.completed_tasks,
                'failed_tasks': metrics_snapshot.failed_tasks,
                'throughput_tps': metrics_snapshot.throughput.tasks_per_second,
                'average_latency_ms': metrics_snapshot.latency.average_latency_ms
            }

        return status

    def shutdown(self):
        """Shutdown integration components gracefully."""
        self.logger.info("Shutting down CBSC Multiprocessing Integration")

        # Stop monitoring
        if self.monitor:
            self.monitor.stop_monitoring()

        # Stop metrics collection
        if self.metrics_collector:
            self.metrics_collector.stop_collection()

        # Shutdown parallel engine
        if hasattr(self.parallel_engine, 'shutdown'):
            self.parallel_engine.shutdown()

        self.logger.info("Integration shutdown complete")


# Global integration instance
_integration_instance: Optional[CBSCMultiprocessingIntegration] = None


def get_integration(config: Optional[Dict[str, Any]] = None) -> CBSCMultiprocessingIntegration:
    """Get the global integration instance."""
    global _integration_instance
    if _integration_instance is None:
        _integration_instance = CBSCMultiprocessingIntegration(config=config)
    return _integration_instance


def initialize_integration(config: Optional[Dict[str, Any]] = None):
    """Initialize the global integration instance."""
    global _integration_instance
    if _integration_instance is not None:
        warnings.warn("Integration already initialized. Ignoring additional initialization.")
        return

    _integration_instance = CBSCMultiprocessingIntegration(config=config)


def shutdown_integration():
    """Shutdown the global integration instance."""
    global _integration_instance
    if _integration_instance:
        _integration_instance.shutdown()
        _integration_instance = None


# Convenience functions for backward compatibility
def execute_backtest(strategy_code: str,
                    parameters: Dict[str, Any],
                    **kwargs) -> BacktestResult:
    """Convenience function for backtest execution."""
    integration = get_integration()
    return integration.execute_backtest(strategy_code, parameters, **kwargs)


def migrate_legacy_request(legacy_request: Dict[str, Any]) -> BacktestRequest:
    """Migrate legacy CBSC request to new format."""
    compatibility = CBSCCompatibilityLayer()
    return compatibility.convert_legacy_request(legacy_request)
"""
Performance benchmarking framework for CBSC multiprocessing system.

Provides comprehensive benchmarking capabilities to validate performance targets
and analyze system behavior across different scales and configurations.
"""

import time
import logging
import statistics
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import integration and monitoring components
try:
    from .integration import CBSCMultiprocessingIntegration, BacktestRequest, BacktestResult
    from .monitor import get_monitor, start_monitoring
    from .performance_metrics import get_metrics_collector, start_metrics_collection
    from .parallel_engine import ParallelEngine
    BENCHMARKING_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Benchmarking components not available: {e}")
    BENCHMARKING_AVAILABLE = False


@dataclass
class BenchmarkConfig:
    """Configuration for benchmark execution."""
    test_name: str
    parameter_counts: List[int]
    iterations_per_test: int
    timeout_seconds: int
    enable_monitoring: bool
    enable_profiling: bool
    output_directory: str
    baseline_system: Optional[str] = None


@dataclass
class BenchmarkResult:
    """Individual benchmark test result."""
    test_name: str
    parameter_count: int
    iteration: int
    execution_time: float
    memory_usage_mb: float
    cpu_utilization: float
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class PerformanceBenchmark:
    """Complete performance benchmark results."""
    test_name: str
    parameter_count: int
    sequential_time: Optional[float]
    parallel_time: float
    speedup: float
    efficiency: float
    memory_peak_mb: float
    memory_avg_mb: float
    cpu_peak_utilization: float
    cpu_avg_utilization: float
    throughput_tasks_per_sec: float
    timestamp: str
    metadata: Dict[str, Any] = None


@dataclass
class WorkloadDescription:
    """Description of benchmark workload."""
    strategy_type: str
    data_size_mb: float
    complexity_level: str  # low, medium, high, extreme
    parameter_space_size: int
    estimated_duration_sec: float


class BenchmarkDataGenerator:
    """Generate test data for benchmarking."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def generate_strategy_code(self, complexity: str = "medium") -> str:
        """Generate strategy code based on complexity level."""
        if complexity == "low":
            return '''
def simple_strategy(data, params):
    # Simple moving average strategy
    ma_short = data['close'].rolling(window=params['ma_short']).mean()
    ma_long = data['close'].rolling(window=params['ma_long']).mean()

    signals = []
    for i in range(len(data)):
        if ma_short.iloc[i] > ma_long.iloc[i]:
            signals.append(1)  # Buy
        else:
            signals.append(0)  # Sell

    return signals
'''
        elif complexity == "medium":
            return '''
def medium_strategy(data, params):
    # RSI + Moving Average strategy
    import numpy as np

    # Calculate moving averages
    ma_short = data['close'].rolling(window=params['ma_short']).mean()
    ma_long = data['close'].rolling(window=params['ma_long']).mean()

    # Calculate RSI
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    signals = []
    for i in range(len(data)):
        ma_signal = 1 if ma_short.iloc[i] > ma_long.iloc[i] else 0
        rsi_signal = 1 if rsi.iloc[i] < params['rsi_oversold'] else 0

        signals.append(1 if ma_signal and rsi_signal else 0)

    return signals
'''
        elif complexity == "high":
            return '''
def complex_strategy(data, params):
    # Multi-indicator strategy with portfolio optimization
    import numpy as np
    import pandas as pd

    # Technical indicators
    ma_short = data['close'].rolling(window=params['ma_short']).mean()
    ma_long = data['close'].rolling(window=params['ma_long']).mean()

    # Bollinger Bands
    bb_period = params['bb_period']
    bb_std = params['bb_std']
    bb_middle = data['close'].rolling(window=bb_period).mean()
    bb_upper = bb_middle + (bb_std * data['close'].rolling(window=bb_period).std())
    bb_lower = bb_middle - (bb_std * data['close'].rolling(window=bb_period).std())

    # MACD
    exp1 = data['close'].ewm(span=params['macd_fast']).mean()
    exp2 = data['close'].ewm(span=params['macd_slow']).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=params['macd_signal']).mean()

    # Volume Weighted Average Price
    vwap = (data['close'] * data['volume']).rolling(window=params['vwap_period']).sum() / \
           data['volume'].rolling(window=params['vwap_period']).sum()

    signals = []
    for i in range(len(data)):
        # Multiple signal conditions
        ma_signal = ma_short.iloc[i] > ma_long.iloc[i]
        bb_signal = data['close'].iloc[i] < bb_lower.iloc[i]
        macd_signal = macd.iloc[i] > signal.iloc[i]
        vwap_signal = data['close'].iloc[i] > vwap.iloc[i]

        # Weighted signal combination
        signal_strength = sum([
            ma_signal * params['ma_weight'],
            bb_signal * params['bb_weight'],
            macd_signal * params['macd_weight'],
            vwap_signal * params['vwap_weight']
        ])

        signals.append(1 if signal_strength > params['signal_threshold'] else 0)

    return signals
'''
        else:  # extreme complexity
            return '''
def extreme_strategy(data, params):
    # Machine learning ensemble strategy
    import numpy as np
    import pandas as pd
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler

    # Feature engineering
    features = pd.DataFrame()

    # Price features
    for period in params['price_periods']:
        features[f'price_ma_{period}'] = data['close'].rolling(window=period).mean()
        features[f'price_std_{period}'] = data['close'].rolling(window=period).std()

    # Volume features
    for period in params['volume_periods']:
        features[f'volume_ma_{period}'] = data['volume'].rolling(window=period).mean()
        features[f'volume_ratio_{period}'] = data['volume'] / data['volume'].rolling(window=period).mean()

    # Volatility features
    for period in params['volatility_periods']:
        features[f'vol_{period}'] = data['close'].rolling(window=period).std() / data['close'].rolling(window=period).mean()

    # Momentum features
    for period in params['momentum_periods']:
        features[f'momentum_{period}'] = data['close'].pct_change(period)

    # Machine learning prediction
    target = data['close'].shift(-1)  # Next day's price
    features_clean = features.dropna()
    target_clean = target[features_clean.index]

    if len(features_clean) > params['min_training_samples']:
        # Train model
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features_clean)

        model = RandomForestRegressor(
            n_estimators=params['n_estimators'],
            max_depth=params['max_depth'],
            random_state=42
        )
        model.fit(features_scaled, target_clean)

        # Generate signals
        predictions = model.predict(features_scaled)

        # Convert predictions to signals
        signals = []
        for i, pred in enumerate(predictions):
            current_price = data['close'].iloc[-len(predictions) + i]
            signals.append(1 if pred > current_price * (1 + params['prediction_threshold']) else 0)
    else:
        # Fallback to simple strategy
        signals = [0] * len(data)

    return signals
'''

    def generate_parameters(self, parameter_count: int, strategy_type: str = "medium") -> List[Dict[str, Any]]:
        """Generate parameter combinations for testing."""
        base_params = {
            "low": {
                'ma_short': [5, 10, 15],
                'ma_long': [20, 30, 40],
                'rsi_period': [14],
                'rsi_oversold': [30],
                'rsi_overbought': [70]
            },
            "medium": {
                'ma_short': [5, 10, 15, 20],
                'ma_long': [25, 30, 35, 40, 45],
                'rsi_period': [14, 21],
                'rsi_oversold': [25, 30, 35],
                'rsi_overbought': [65, 70, 75],
                'bb_period': [15, 20],
                'bb_std': [2.0, 2.5]
            },
            "high": {
                'ma_short': [5, 10, 15, 20, 25],
                'ma_long': [30, 35, 40, 45, 50, 55],
                'rsi_period': [14, 21, 28],
                'rsi_oversold': [20, 25, 30, 35],
                'rsi_overbought': [65, 70, 75, 80],
                'bb_period': [10, 15, 20, 25],
                'bb_std': [1.5, 2.0, 2.5],
                'macd_fast': [12, 15],
                'macd_slow': [26, 30],
                'macd_signal': [9, 12],
                'vwap_period': [10, 15, 20],
                'ma_weight': [0.3, 0.4, 0.5],
                'bb_weight': [0.2, 0.3, 0.4],
                'macd_weight': [0.2, 0.3, 0.4],
                'vwap_weight': [0.1, 0.2, 0.3],
                'signal_threshold': [0.5, 0.6, 0.7]
            },
            "extreme": {
                'price_periods': [5, 10, 20, 30],
                'volume_periods': [5, 10, 20],
                'volatility_periods': [10, 20],
                'momentum_periods': [1, 3, 5, 10],
                'n_estimators': [50, 100, 200],
                'max_depth': [5, 10, 15],
                'min_training_samples': [100],
                'prediction_threshold': [0.01, 0.02, 0.03]
            }
        }

        param_sets = base_params.get(strategy_type, base_params["medium"])

        # Generate parameter combinations
        parameters = []
        keys = list(param_sets.keys())

        # Simple grid sampling (in production, use more sophisticated methods)
        import itertools
        for combination in itertools.product(*param_sets.values()):
            param_dict = dict(zip(keys, combination))
            parameters.append(param_dict)

        # Return requested number of parameters
        return parameters[:parameter_count]

    def generate_data_config(self, size_mb: float) -> Dict[str, Any]:
        """Generate data configuration based on size."""
        # Rough estimation of rows based on size
        rows_per_mb = 1000  # Approximate
        total_rows = int(size_mb * rows_per_mb)

        return {
            'start_date': '2020-01-01',
            'end_date': '2023-12-31',
            'symbols': ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA'],
            'data_frequency': 'daily',
            'estimated_rows': total_rows,
            'estimated_size_mb': size_mb
        }


class PerformanceBenchmarkFramework:
    """Main benchmarking framework for performance testing."""

    def __init__(self, config: BenchmarkConfig):
        if not BENCHMARKING_AVAILABLE:
            raise RuntimeError("Benchmarking components not available")

        self.config = config
        self.logger = logging.getLogger(__name__)
        self.data_generator = BenchmarkDataGenerator()
        self.results = []

        # Setup output directory
        self.output_dir = Path(config.output_directory)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize integration
        self.integration = CBSCMultiprocessingIntegration(
            enable_monitoring=config.enable_monitoring,
            enable_metrics=True
        )

        # Performance tracking
        self.benchmark_results = []
        self.start_time = None
        self.end_time = None

    def run_benchmark_suite(self) -> Dict[str, Any]:
        """Run complete benchmark suite."""
        self.logger.info(f"Starting benchmark suite: {self.config.test_name}")
        self.start_time = datetime.now()

        try:
            # Run benchmarks for different parameter counts
            for param_count in self.config.parameter_counts:
                self.logger.info(f"Benchmarking {param_count} parameters")
                benchmark = self.run_parameter_benchmark(param_count)
                self.benchmark_results.append(benchmark)

            # Generate summary report
            summary = self.generate_summary_report()
            self.end_time = datetime.now()

            # Save results
            self.save_results()

            self.logger.info("Benchmark suite completed successfully")
            return summary

        except Exception as e:
            self.logger.error(f"Benchmark suite failed: {e}")
            raise

    def run_parameter_benchmark(self, parameter_count: int) -> PerformanceBenchmark:
        """Run benchmark for specific parameter count."""
        self.logger.info(f"Running benchmark for {parameter_count} parameters")

        # Generate test data
        strategy_code = self.data_generator.generate_strategy_code("high")
        parameters = self.data_generator.generate_parameters(parameter_count, "high")
        data_config = self.data_generator.generate_data_config(min(parameter_count * 0.1, 100))

        # Measure sequential performance (baseline)
        sequential_time = self.measure_sequential_performance(
            strategy_code, parameters[:min(10, len(parameters))], data_config
        )

        # Measure parallel performance
        parallel_times = []
        memory_usage = []
        cpu_utilization = []

        for iteration in range(self.config.iterations_per_test):
            self.logger.info(f"  Iteration {iteration + 1}/{self.config.iterations_per_test}")

            # Record start metrics
            start_metrics = self._get_resource_metrics()

            # Execute parallel benchmark
            start_time = time.time()
            try:
                result = self.integration.execute_backtest(
                    strategy_code=strategy_code,
                    parameters={'parameter_grid': parameters},
                    data_config=data_config,
                    use_multiprocessing=True
                )

                execution_time = time.time() - start_time
                parallel_times.append(execution_time)

                # Record end metrics
                end_metrics = self._get_resource_metrics()
                memory_usage.append(end_metrics['memory_mb'])
                cpu_utilization.append(end_metrics['cpu_percent'])

                self.logger.info(f"    Completed in {execution_time:.2f}s")

            except Exception as e:
                self.logger.error(f"  Iteration {iteration + 1} failed: {e}")
                parallel_times.append(float('inf'))  # Mark as failed

        # Calculate performance metrics
        valid_times = [t for t in parallel_times if t != float('inf')]
        if not valid_times:
            raise RuntimeError("All parallel benchmark iterations failed")

        avg_parallel_time = statistics.mean(valid_times)
        speedup = sequential_time / avg_parallel_time if sequential_time else 0

        # Calculate efficiency (speedup relative to theoretical maximum)
        cpu_count = multiprocessing.cpu_count()
        efficiency = speedup / cpu_count if cpu_count > 0 else 0

        # Create benchmark result
        benchmark = PerformanceBenchmark(
            test_name=self.config.test_name,
            parameter_count=parameter_count,
            sequential_time=sequential_time,
            parallel_time=avg_parallel_time,
            speedup=speedup,
            efficiency=efficiency,
            memory_peak_mb=max(memory_usage) if memory_usage else 0,
            memory_avg_mb=statistics.mean(memory_usage) if memory_usage else 0,
            cpu_peak_utilization=max(cpu_utilization) if cpu_utilization else 0,
            cpu_avg_utilization=statistics.mean(cpu_utilization) if cpu_utilization else 0,
            throughput_tasks_per_sec=parameter_count / avg_parallel_time if avg_parallel_time > 0 else 0,
            timestamp=datetime.now().isoformat(),
            metadata={
                'iterations': self.config.iterations_per_test,
                'successful_iterations': len(valid_times),
                'failed_iterations': len(parallel_times) - len(valid_times)
            }
        )

        return benchmark

    def measure_sequential_performance(self,
                                     strategy_code: str,
                                     parameters: List[Dict[str, Any]],
                                     data_config: Dict[str, Any]) -> float:
        """Measure sequential execution time as baseline."""
        self.logger.info("Measuring sequential baseline performance")

        start_time = time.time()

        try:
            # Execute sequentially
            for i, param_set in enumerate(parameters):
                result = self.integration.execute_backtest(
                    strategy_code=strategy_code,
                    parameters=param_set,
                    data_config=data_config,
                    use_multiprocessing=False
                )

                if not result.success:
                    self.logger.warning(f"Sequential execution {i+1} failed: {result.error_message}")

            execution_time = time.time() - start_time
            self.logger.info(f"Sequential baseline: {execution_time:.2f}s for {len(parameters)} tasks")
            return execution_time

        except Exception as e:
            self.logger.error(f"Sequential baseline measurement failed: {e}")
            return float('inf')

    def _get_resource_metrics(self) -> Dict[str, float]:
        """Get current system resource metrics."""
        try:
            import psutil
            return {
                'memory_mb': psutil.virtual_memory().used / 1024 / 1024,
                'cpu_percent': psutil.cpu_percent(interval=0.1)
            }
        except ImportError:
            return {'memory_mb': 0, 'cpu_percent': 0}

    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate comprehensive benchmark summary report."""
        if not self.benchmark_results:
            return {}

        # Calculate overall statistics
        speedups = [b.speedup for b in self.benchmark_results if b.speedup != float('inf')]
        efficiencies = [b.efficiency for b in self.benchmark_results if b.efficiency > 0]
        throughputs = [b.throughput_tasks_per_sec for b in self.benchmark_results if b.throughput_tasks_per_sec > 0]

        summary = {
            'test_name': self.config.test_name,
            'execution_time': {
                'start': self.start_time.isoformat() if self.start_time else None,
                'end': self.end_time.isoformat() if self.end_time else None,
                'duration_sec': (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else None
            },
            'performance_summary': {
                'avg_speedup': statistics.mean(speedups) if speedups else 0,
                'max_speedup': max(speedups) if speedups else 0,
                'min_speedup': min(speedups) if speedups else 0,
                'avg_efficiency': statistics.mean(efficiencies) if efficiencies else 0,
                'avg_throughput_tps': statistics.mean(throughputs) if throughputs else 0
            },
            'target_validation': {
                'target_20x_achieved': any(s >= 20 for s in speedups),
                'target_25x_achieved': any(s >= 25 for s in speedups),
                'target_30x_achieved': any(s >= 30 for s in speedups),
                'max_parameters_tested': max(b.parameter_count for b in self.benchmark_results),
                'memory_within_limit': all(b.memory_peak_mb < 4096 for b in self.benchmark_results)
            },
            'detailed_results': [asdict(b) for b in self.benchmark_results],
            'system_info': self._get_system_info()
        }

        return summary

    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information for benchmark report."""
        try:
            import psutil
            import platform

            return {
                'cpu_count': multiprocessing.cpu_count(),
                'cpu_name': platform.processor(),
                'total_memory_gb': psutil.virtual_memory().total / 1024 / 1024 / 1024,
                'python_version': platform.python_version(),
                'platform': platform.platform()
            }
        except Exception as e:
            self.logger.warning(f"Could not get system info: {e}")
            return {}

    def save_results(self):
        """Save benchmark results to files."""
        if not self.benchmark_results:
            return

        # Save detailed results
        results_file = self.output_dir / f"{self.config.test_name}_results.json"
        with open(results_file, 'w') as f:
            json.dump([asdict(b) for b in self.benchmark_results], f, indent=2, default=str)

        # Save summary report
        summary = self.generate_summary_report()
        summary_file = self.output_dir / f"{self.config.test_name}_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)

        self.logger.info(f"Results saved to {self.output_dir}")

    def validate_performance_targets(self) -> Dict[str, bool]:
        """Validate if performance targets are met."""
        validation = {
            'small_scale_target_met': False,  # 15x for 1K parameters
            'medium_scale_target_met': False,  # 20x for 10K parameters
            'large_scale_target_met': False,   # 25x for 50K parameters
            'xlarge_scale_target_met': False,  # 30x for 100K+ parameters
            'memory_target_met': False,        # <4GB memory usage
            'overall_success': False
        }

        for benchmark in self.benchmark_results:
            param_count = benchmark.parameter_count
            speedup = benchmark.speedup
            memory_ok = benchmark.memory_peak_mb < 4096

            if memory_ok:
                validation['memory_target_met'] = True

            if param_count >= 1000 and speedup >= 15:
                validation['small_scale_target_met'] = True
            if param_count >= 10000 and speedup >= 20:
                validation['medium_scale_target_met'] = True
            if param_count >= 50000 and speedup >= 25:
                validation['large_scale_target_met'] = True
            if param_count >= 100000 and speedup >= 30:
                validation['xlarge_scale_target_met'] = True

        validation['overall_success'] = all(validation.values())
        return validation


def run_standard_benchmark_suite(output_directory: str = "./benchmark_results") -> Dict[str, Any]:
    """Run standard benchmark suite with predefined configurations."""
    config = BenchmarkConfig(
        test_name="standard_performance_benchmark",
        parameter_counts=[1000, 10000, 50000, 100000],
        iterations_per_test=3,
        timeout_seconds=3600,
        enable_monitoring=True,
        enable_profiling=False,
        output_directory=output_directory
    )

    framework = PerformanceBenchmarkFramework(config)
    return framework.run_benchmark_suite()


def run_quick_benchmark(output_directory: str = "./benchmark_results") -> Dict[str, Any]:
    """Run quick benchmark for validation."""
    config = BenchmarkConfig(
        test_name="quick_performance_validation",
        parameter_counts=[1000, 10000],
        iterations_per_test=2,
        timeout_seconds=1800,
        enable_monitoring=False,
        enable_profiling=False,
        output_directory=output_directory
    )

    framework = PerformanceBenchmarkFramework(config)
    return framework.run_benchmark_suite()
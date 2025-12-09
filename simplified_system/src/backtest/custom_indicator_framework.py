#!/usr / bin / env python3
"""
Custom Indicator Framework
Phase 4.3: Custom Indicator Framework

Implements standardized interface for custom indicators,
vectorized computation support, indicator testing and validation,
and performance benchmarking tools.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class IndicatorCategory(Enum):
    """Custom indicator categories"""

    MOMENTUM = "momentum"
    TREND = "trend"
    VOLATILITY = "volatility"
    VOLUME = "volume"
    SENTIMENT = "sentiment"
    MARKET_STRUCTURE = "market_structure"
    REGIME_DETECTION = "regime_detection"
    STATISTICAL = "statistical"


class ParameterType(Enum):
    """Parameter types for custom indicators"""

    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    STRING = "string"
    LIST = "list"
    RANGE = "range"


@dataclass
class ParameterDefinition:
    """Parameter definition for custom indicators"""

    name: str
    type: ParameterType
    default_value: Any
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    description: str = ""
    choices: Optional[List[Any]] = None


@dataclass
class IndicatorSpecification:
    """Complete specification for a custom indicator"""

    name: str
    description: str
    category: IndicatorCategory
    author: str
    version: str
    created_date: datetime
    parameters: List[ParameterDefinition]
    required_data: List[str]  # ['open', 'high', 'low', 'close', 'volume']
    vectorizable: bool = True
    supports_realtime: bool = True
    benchmark_performance: Optional[Dict[str, float]] = None


class BaseCustomIndicator(ABC):
    """Base class for custom indicators"""

    def __init__(self, spec: IndicatorSpecification):
        """
        Initialize custom indicator

        Args:
            spec: Indicator specification
        """
        self.spec = spec
        self.parameters = {param.name: param.default_value for param in spec.parameters}
        self.is_validated = False
        self.performance_cache = {}

    @abstractmethod
    def calculate(self, data: pd.DataFrame) -> Union[pd.Series, Dict[str, pd.Series]]:
        """
        Calculate indicator values

        Args:
            data: Market data

        Returns:
            Calculated indicator values
        """

    @abstractmethod
    def validate_data(self, data: pd.DataFrame) -> bool:
        """
        Validate input data

        Args:
            data: Market data to validate

        Returns:
            True if data is valid
        """

    @abstractmethod
    def generate_signals(
        self, indicator_values: Union[pd.Series, Dict[str, pd.Series]]
    ) -> pd.Series:
        """
        Generate trading signals from indicator values

        Args:
            indicator_values: Calculated indicator values

        Returns:
            Trading signals (-1, 0, 1)
        """

    def set_parameter(self, name: str, value: Any) -> bool:
        """
        Set indicator parameter

        Args:
            name: Parameter name
            value: Parameter value

        Returns:
            True if parameter was set successfully
        """
        param_def = next((p for p in self.spec.parameters if p.name == name), None)
        if not param_def:
            logger.error(
                f"Parameter '{name}' not found in indicator '{self.spec.name}'"
            )
            return False

        # Validate parameter value
        if not self._validate_parameter_value(param_def, value):
            logger.error(f"Invalid value for parameter '{name}': {value}")
            return False

        self.parameters[name] = value
        return True

    def get_parameters(self) -> Dict[str, Any]:
        """Get current parameter values"""
        return self.parameters.copy()

    def _validate_parameter_value(
        self, param_def: ParameterDefinition, value: Any
    ) -> bool:
        """Validate parameter value against definition"""
        # Type checking
        if param_def.type == ParameterType.INTEGER:
            if not isinstance(value, int):
                return False
        elif param_def.type == ParameterType.FLOAT:
            if not isinstance(value, (int, float)):
                return False
        elif param_def.type == ParameterType.BOOLEAN:
            if not isinstance(value, bool):
                return False
        elif param_def.type == ParameterType.STRING:
            if not isinstance(value, str):
                return False
        elif param_def.type == ParameterType.LIST:
            if not isinstance(value, list):
                return False
        elif param_def.type == ParameterType.RANGE:
            if not isinstance(value, (list, tuple)) or len(value) != 2:
                return False

        # Range checking
        if param_def.min_value is not None and value < param_def.min_value:
            return False
        if param_def.max_value is not None and value > param_def.max_value:
            return False

        # Choice checking
        if param_def.choices and value not in param_def.choices:
            return False

        return True


class VectorizedIndicatorMixin:
    """Mixin for vectorized indicator implementations"""

    def vectorized_calculate(
        self, data: pd.DataFrame
    ) -> Union[pd.Series, Dict[str, pd.Series]]:
        """
        Vectorized calculation implementation

        Args:
            data: Market data

        Returns:
            Vectorized indicator calculation
        """
        # Default implementation - override in subclasses
        return self.calculate(data)

    def batch_calculate(
        self, data_list: List[pd.DataFrame]
    ) -> List[Union[pd.Series, Dict[str, pd.Series]]]:
        """
        Batch calculate indicator for multiple datasets

        Args:
            data_list: List of market data DataFrames

        Returns:
            List of calculated indicator values
        """
        results = []
        for data in data_list:
            if self.validate_data(data):
                result = self.vectorized_calculate(data)
                results.append(result)
            else:
                results.append(None)

        return results


class CustomIndicatorRegistry:
    """Registry for managing custom indicators"""

    def __init__(self):
        """Initialize indicator registry"""
        self.indicators = {}
        self.categories = {}
        self.performance_benchmarks = {}

    def register_indicator(self, indicator: BaseCustomIndicator) -> bool:
        """
        Register a custom indicator

        Args:
            indicator: Custom indicator instance

        Returns:
            True if registered successfully
        """
        # Validate indicator
        if not self._validate_indicator(indicator):
            return False

        # Register indicator
        self.indicators[indicator.spec.name] = indicator

        # Update category mapping
        category = indicator.spec.category
        if category not in self.categories:
            self.categories[category] = []
        self.categories[category].append(indicator.spec.name)

        logger.info(f"Registered custom indicator: {indicator.spec.name}")
        return True

    def get_indicator(self, name: str) -> Optional[BaseCustomIndicator]:
        """Get registered indicator by name"""
        return self.indicators.get(name)

    def get_indicators_by_category(self, category: IndicatorCategory) -> List[str]:
        """Get indicator names by category"""
        return self.categories.get(category, [])

    def list_all_indicators(self) -> List[str]:
        """List all registered indicator names"""
        return list(self.indicators.keys())

    def _validate_indicator(self, indicator: BaseCustomIndicator) -> bool:
        """Validate indicator before registration"""
        # Check if indicator already exists
        if indicator.spec.name in self.indicators:
            logger.error(f"Indicator '{indicator.spec.name}' already registered")
            return False

        # Check specification completeness
        if not indicator.spec.name or not indicator.spec.description:
            logger.error(
                f"Indicator '{indicator.spec.name}' missing name or description"
            )
            return False

        # Check if required methods are implemented
        required_methods = ["calculate", "validate_data", "generate_signals"]
        for method_name in required_methods:
            if not hasattr(indicator, method_name):
                logger.error(
                    f"Indicator '{indicator.spec.name}' missing required method: {method_name}"
                )
                return False

        return True


class IndicatorTester:
    """Testing and validation framework for custom indicators"""

    def __init__(self, registry: CustomIndicatorRegistry):
        """
        Initialize indicator tester

        Args:
            registry: Indicator registry
        """
        self.registry = registry
        self.test_results = {}

    def test_indicator(
        self,
        indicator_name: str,
        test_data: pd.DataFrame,
        benchmark_data: Optional[pd.DataFrame] = None,
    ) -> Dict[str, Any]:
        """
        Test a custom indicator comprehensively

        Args:
            indicator_name: Name of indicator to test
            test_data: Test data
            benchmark_data: Optional benchmark data

        Returns:
            Test results
        """
        indicator = self.registry.get_indicator(indicator_name)
        if not indicator:
            return {"error": f"Indicator {indicator_name} not found"}

        test_results = {
            "indicator_name": indicator_name,
            "test_timestamp": datetime.now(),
            "validation_results": {},
            "performance_results": {},
            "signal_results": {},
            "error_results": {},
        }

        # Test data validation
        test_results["validation_results"] = self._test_data_validation(
            indicator, test_data
        )

        # Test calculation
        if test_results["validation_results"]["data_valid"]:
            calculation_results = self._test_calculation(indicator, test_data)
            test_results["performance_results"] = calculation_results

            # Test signal generation
            if calculation_results["calculation_success"]:
                signal_results = self._test_signal_generation(
                    indicator, calculation_results["values"]
                )
                test_results["signal_results"] = signal_results

        # Test error handling
        error_results = self._test_error_handling(indicator)
        test_results["error_results"] = error_results

        # Store results
        self.test_results[indicator_name] = test_results

        return test_results

    def _test_data_validation(
        self, indicator: BaseCustomIndicator, test_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """Test data validation"""
        # Test with valid data
        valid_result = indicator.validate_data(test_data)

        # Test with invalid data
        invalid_data = test_data.copy()
        invalid_data.loc[invalid_data.index[0], "close"] = -1  # Invalid price

        invalid_result = indicator.validate_data(invalid_data)

        # Test with insufficient data
        insufficient_data = test_data.head(2)
        insufficient_result = indicator.validate_data(insufficient_data)

        return {
            "data_valid": valid_result,
            "invalid_data_rejected": not invalid_result,
            "insufficient_data_rejected": not insufficient_result,
        }

    def _test_calculation(
        self, indicator: BaseCustomIndicator, test_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """Test indicator calculation"""
        try:
            # Test calculation
            start_time = datetime.now()
            values = indicator.calculate(test_data)
            calculation_time = (datetime.now() - start_time).total_seconds()

            # Validate calculation results
            if isinstance(values, pd.Series):
                results_valid = len(values) == len(test_data)
                has_nulls = values.isnull().any()
            elif isinstance(values, dict):
                results_valid = all(len(v) == len(test_data) for v in values.values())
                has_nulls = any(v.isnull().any() for v in values.values())
            else:
                results_valid = False
                has_nulls = True

            return {
                "calculation_success": True,
                "calculation_time": calculation_time,
                "results_valid": results_valid,
                "has_null_values": has_nulls,
                "values": values,
            }

        except Exception as e:
            return {"calculation_success": False, "error": str(e)}

    def _test_signal_generation(
        self,
        indicator: BaseCustomIndicator,
        indicator_values: Union[pd.Series, Dict[str, pd.Series]],
    ) -> Dict[str, Any]:
        """Test signal generation"""
        try:
            # Generate signals
            signals = indicator.generate_signals(indicator_values)

            # Validate signals
            if isinstance(signals, pd.Series):
                valid_range = signals.isin([-1, 0, 1]).all()
                signal_distribution = signals.value_counts().to_dict()
            else:
                valid_range = False
                signal_distribution = {}

            return {
                "signal_generation_success": True,
                "valid_signal_range": valid_range,
                "signal_distribution": signal_distribution,
                "signals": signals,
            }

        except Exception as e:
            return {"signal_generation_success": False, "error": str(e)}

    def _test_error_handling(self, indicator: BaseCustomIndicator) -> Dict[str, Any]:
        """Test error handling"""
        error_tests = {}

        # Test with invalid parameters
        invalid_params = {"invalid_param": "invalid_value"}
        error_tests["invalid_parameter"] = not indicator.set_parameter(
            "invalid_param", "invalid_value"
        )

        # Test with out - of - range parameters
        if indicator.spec.parameters:
            first_param = indicator.spec.parameters[0]
            if first_param.min_value is not None:
                error_tests["out_of_range_parameter"] = not indicator.set_parameter(
                    first_param.name, first_param.min_value - 1
                )

        # Test calculation with missing data
        missing_data = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
        error_tests["missing_data_handling"] = not indicator.validate_data(missing_data)

        return error_tests

    def run_all_tests(self, test_data: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """Run tests for all registered indicators"""
        all_results = {}

        for indicator_name in self.registry.list_all_indicators():
            logger.info(f"Testing indicator: {indicator_name}")
            all_results[indicator_name] = self.test_indicator(indicator_name, test_data)

        return all_results


class PerformanceBenchmark:
    """Performance benchmarking for custom indicators"""

    def __init__(self, registry: CustomIndicatorRegistry):
        """
        Initialize performance benchmark

        Args:
            registry: Indicator registry
        """
        self.registry = registry
        self.benchmark_results = {}

    def benchmark_indicator(
        self,
        indicator_name: str,
        data_sizes: List[int] = [1000, 5000, 10000, 50000],
        iterations: int = 5,
    ) -> Dict[str, Any]:
        """
        Benchmark indicator performance

        Args:
            indicator_name: Name of indicator to benchmark
            data_sizes: List of data sizes to test
            iterations: Number of iterations per test

        Returns:
            Benchmark results
        """
        indicator = self.registry.get_indicator(indicator_name)
        if not indicator:
            return {"error": f"Indicator {indicator_name} not found"}

        benchmark_results = {
            "indicator_name": indicator_name,
            "benchmark_timestamp": datetime.now(),
            "data_sizes": {},
            "summary": {},
        }

        for size in data_sizes:
            # Generate test data
            test_data = self._generate_test_data(size)

            # Run benchmark iterations
            times = []
            for _ in range(iterations):
                start_time = datetime.now()
                indicator.calculate(test_data)
                end_time = datetime.now()
                times.append((end_time - start_time).total_seconds())

            # Calculate statistics
            avg_time = np.mean(times)
            std_time = np.std(times)
            min_time = np.min(times)
            max_time = np.max(times)

            benchmark_results["data_sizes"][size] = {
                "average_time": avg_time,
                "std_deviation": std_time,
                "min_time": min_time,
                "max_time": max_time,
                "iterations": iterations,
                "records_per_second": size / avg_time if avg_time > 0 else 0,
            }

        # Calculate summary statistics
        all_records_per_second = [
            results["records_per_second"]
            for results in benchmark_results["data_sizes"].values()
        ]

        benchmark_results["summary"] = {
            "total_data_sizes_tested": len(data_sizes),
            "avg_records_per_second": np.mean(all_records_per_second),
            "max_records_per_second": np.max(all_records_per_second),
            "min_records_per_second": np.min(all_records_per_second),
        }

        self.benchmark_results[indicator_name] = benchmark_results
        return benchmark_results

    def compare_indicators(
        self, indicator_names: List[str], data_size: int = 10000, iterations: int = 5
    ) -> Dict[str, Any]:
        """
        Compare performance of multiple indicators

        Args:
            indicator_names: List of indicator names to compare
            data_size: Data size for comparison
            iterations: Number of iterations

        Returns:
            Comparison results
        """
        comparison_results = {
            "comparison_timestamp": datetime.now(),
            "data_size": data_size,
            "iterations": iterations,
            "indicator_results": {},
        }

        # Benchmark each indicator
        for indicator_name in indicator_names:
            if indicator_name in self.registry.list_all_indicators():
                results = self.benchmark_indicator(
                    indicator_name, [data_size], iterations
                )
                comparison_results["indicator_results"][indicator_name] = results

        # Generate ranking
        records_per_second = {
            name: results["data_sizes"][data_size]["records_per_second"]
            for name, results in comparison_results["indicator_results"].items()
            if "data_sizes" in results and data_size in results["data_sizes"]
        }

        sorted_indicators = sorted(
            records_per_second.items(), key = lambda x: x[1], reverse = True
        )

        comparison_results["performance_ranking"] = [
            {"indicator": name, "records_per_second": rps}
            for name, rps in sorted_indicators
        ]

        comparison_results["best_performer"] = (
            sorted_indicators[0][0] if sorted_indicators else None
        )
        comparison_results["worst_performer"] = (
            sorted_indicators[-1][0] if sorted_indicators else None
        )

        return comparison_results

    def _generate_test_data(self, size: int) -> pd.DataFrame:
        """Generate test data for benchmarking"""
        np.random.seed(42)
        dates = pd.date_range("2020 - 01 - 01", periods = size, freq="D")

        # Generate price data with realistic characteristics
        returns = np.random.normal(0.0005, 0.02, size)
        prices = 100 + np.cumsum(returns)

        data = pd.DataFrame(
            {
                "open": prices * (1 + np.random.normal(0, 0.005, size)),
                "high": prices * (1 + np.abs(np.random.normal(0, 0.01, size))),
                "low": prices * (1 - np.abs(np.random.normal(0, 0.01, size))),
                "close": prices,
                "volume": np.random.randint(1000000, 10000000, size),
            },
            index = dates,
        )

        return data


# Example custom indicators


class CustomMeanReversionIndicator(BaseCustomIndicator, VectorizedIndicatorMixin):
    """Custom mean reversion indicator example"""

    def __init__(self):
        spec = IndicatorSpecification(
            name="custom_mean_reversion",
            description="Custom mean reversion indicator with adaptive thresholds",
            category = IndicatorCategory.MOMENTUM,
            author="System",
            version="1.0.0",
            created_date = datetime.now(),
            parameters=[
                ParameterDefinition(
                    name="lookback_period",
                    type = ParameterType.INTEGER,
                    default_value = 20,
                    min_value = 5,
                    max_value = 200,
                    description="Lookback period for mean calculation",
                ),
                ParameterDefinition(
                    name="std_multiplier",
                    type = ParameterType.FLOAT,
                    default_value = 2.0,
                    min_value = 0.5,
                    max_value = 5.0,
                    description="Standard deviation multiplier for thresholds",
                ),
            ],
            required_data=["close"],
            vectorizable = True,
            supports_realtime = True,
        )
        super().__init__(spec)

    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """Calculate custom mean reversion indicator"""
        lookback = self.parameters["lookback_period"]
        std_mult = self.parameters["std_multiplier"]

        # Calculate rolling mean and standard deviation
        rolling_mean = data["close"].rolling(window = lookback).mean()
        rolling_std = data["close"].rolling(window = lookback).std()

        # Calculate z - score
        z_score = (data["close"] - rolling_mean) / rolling_std

        # Normalize to -1 to 1 range
        indicator = np.tanh(z_score / std_mult)

        return indicator

    def validate_data(self, data: pd.DataFrame) -> bool:
        """Validate input data"""
        required_columns = ["close"]
        return (
            all(col in data.columns for col in required_columns)
            and len(data) >= self.parameters["lookback_period"]
        )

    def generate_signals(self, indicator_values: pd.Series) -> pd.Series:
        """Generate signals from indicator values"""
        signals = pd.Series(0, index = indicator_values.index)
        signals[indicator_values > 0.5] = 1  # Buy signal
        signals[indicator_values < -0.5] = -1  # Sell signal
        return signals


class CustomVolatilityRegimeIndicator(BaseCustomIndicator, VectorizedIndicatorMixin):
    """Custom volatility regime detection indicator"""

    def __init__(self):
        spec = IndicatorSpecification(
            name="custom_volatility_regime",
            description="Detects volatility regimes for adaptive trading",
            category = IndicatorCategory.VOLATILITY,
            author="System",
            version="1.0.0",
            created_date = datetime.now(),
            parameters=[
                ParameterDefinition(
                    name="short_window",
                    type = ParameterType.INTEGER,
                    default_value = 10,
                    min_value = 5,
                    max_value = 50,
                    description="Short - term volatility window",
                ),
                ParameterDefinition(
                    name="long_window",
                    type = ParameterType.INTEGER,
                    default_value = 50,
                    min_value = 20,
                    max_value = 200,
                    description="Long - term volatility window",
                ),
            ],
            required_data=["close"],
            vectorizable = True,
            supports_realtime = True,
        )
        super().__init__(spec)

    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """Calculate volatility regime indicator"""
        short_window = self.parameters["short_window"]
        long_window = self.parameters["long_window"]

        # Calculate returns
        returns = data["close"].pct_change()

        # Calculate short and long - term volatility
        short_vol = returns.rolling(window = short_window).std()
        long_vol = returns.rolling(window = long_window).std()

        # Calculate volatility ratio
        vol_ratio = short_vol / long_vol

        # Normalize indicator
        indicator = (vol_ratio - 1) / 2  # Center around 0
        indicator = np.tanh(indicator)  # Bound between -1 and 1

        return indicator

    def validate_data(self, data: pd.DataFrame) -> bool:
        """Validate input data"""
        required_columns = ["close"]
        return (
            all(col in data.columns for col in required_columns)
            and len(data) >= self.parameters["long_window"]
        )

    def generate_signals(self, indicator_values: pd.Series) -> pd.Series:
        """Generate signals from volatility regime"""
        signals = pd.Series(0, index = indicator_values.index)
        signals[indicator_values > 0.3] = 1  # High volatility signal
        signals[indicator_values < -0.3] = -1  # Low volatility signal
        return signals


# Factory functions


def create_indicator_registry() -> CustomIndicatorRegistry:
    """Create and populate indicator registry with example indicators"""
    registry = CustomIndicatorRegistry()

    # Register example indicators
    registry.register_indicator(CustomMeanReversionIndicator())
    registry.register_indicator(CustomVolatilityRegimeIndicator())

    return registry


# Example usage and testing


def test_custom_indicator_framework():
    """Test custom indicator framework"""
    logger.info("Testing custom indicator framework...")

    # Create registry and register example indicators
    registry = create_indicator_registry()

    # Initialize tester
    tester = IndicatorTester(registry)

    # Create test data
    test_data = tester._generate_test_data(1000)

    # Test all indicators
    test_results = tester.run_all_tests(test_data)

    # Initialize performance benchmark
    benchmark = PerformanceBenchmark(registry)

    # Run performance benchmarks
    benchmark_results = {}
    for indicator_name in registry.list_all_indicators():
        logger.info(f"Benchmarking indicator: {indicator_name}")
        results = benchmark.benchmark_indicator(indicator_name, [1000, 5000], 3)
        benchmark_results[indicator_name] = results

    # Compare indicator performance
    comparison = benchmark.compare_indicators(registry.list_all_indicators(), 5000, 3)

    logger.info(f"Custom indicator framework test completed:")
    logger.info(f"  Registered indicators: {len(registry.list_all_indicators())}")
    logger.info(f"  Test results: {len(test_results)} indicators tested")
    logger.info(f"  Performance benchmarks: {len(benchmark_results)}")
    logger.info(f"  Best performer: {comparison.get('best_performer')}")
    logger.info(
        f"  Records / sec: {comparison.get('performance_ranking', [{}])[0].get('records_per_second', 0):.0f}"
    )

    return {
        "registry": registry,
        "test_results": test_results,
        "benchmark_results": benchmark_results,
        "performance_comparison": comparison,
    }


if __name__ == "__main__":
    # Test custom indicator framework
    results = test_custom_indicator_framework()

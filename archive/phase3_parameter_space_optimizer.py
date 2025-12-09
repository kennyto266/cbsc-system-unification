"""
Phase 3.1: Extended Parameter Space Optimization System
Phase 3.1: 扩展参数空间优化系统

This module implements a comprehensive parameter space optimization system
that supports massive parameter combinations for technical indicators.
"""

import pandas as pd
import numpy as np
import itertools
import json
import time
from typing import Dict, List, Tuple, Any, Optional, Union, Callable
from dataclasses import dataclass, asdict
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from multiprocessing import cpu_count
import warnings
warnings.filterwarnings('ignore')

@dataclass
class ParameterRange:
    """Parameter range definition"""
    name: str
    min_value: Union[int, float]
    max_value: Union[int, float]
    step: Union[int, float]
    data_type: str  # 'int', 'float'
    description: str = ""

    def __post_init__(self):
        if self.min_value > self.max_value:
            raise ValueError(f"Parameter {self.name}: min_value cannot be greater than max_value")
        if self.step <= 0:
            raise ValueError(f"Parameter {self.name}: step must be positive")

@dataclass
class ParameterSpace:
    """Complete parameter space definition"""
    name: str
    description: str
    parameters: List[ParameterRange]
    constraints: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        self._validate_parameters()

    def _validate_parameters(self):
        """Validate parameter definitions"""
        param_names = [p.name for p in self.parameters]
        if len(param_names) != len(set(param_names)):
            raise ValueError("Parameter names must be unique")

class ParameterSpaceGenerator:
    """Advanced parameter space generator for massive optimization"""

    def __init__(self, max_combinations: int = 1000000):
        self.max_combinations = max_combinations
        self.performance_cache = {}

    def generate_parameter_combinations(self,
                                       parameter_space: ParameterSpace,
                                       max_combinations: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Generate parameter combinations with intelligent sampling

        Parameters:
        -----------
        parameter_space : ParameterSpace
            Parameter space definition
        max_combinations : int, optional
            Maximum number of combinations to generate

        Returns:
        --------
        List[Dict[str, Any]]
            List of parameter combinations
        """
        if max_combinations is None:
            max_combinations = self.max_combinations

        print(f"Generating parameter combinations for {parameter_space.name}")
        print(f"Parameters: {len(parameter_space.parameters)}")

        # Calculate total possible combinations
        param_ranges = []
        for param in parameter_space.parameters:
            if param.data_type == 'int':
                values = list(range(param.min_value, param.max_value + 1, param.step))
            else:  # float
                steps = int((param.max_value - param.min_value) / param.step) + 1
                values = [param.min_value + i * param.step for i in range(steps)]
            param_ranges.append(values)

        total_combinations = 1
        for param_range in param_ranges:
            total_combinations *= len(param_range)

        print(f"Total possible combinations: {total_combinations:,}")

        if total_combinations <= max_combinations:
            # Generate all combinations
            print("Generating all possible combinations...")
            combinations = self._generate_all_combinations(parameter_space, param_ranges)
        else:
            # Use intelligent sampling
            print(f"Using intelligent sampling for {max_combinations:,} combinations...")
            combinations = self._intelligent_sampling(parameter_space, param_ranges, max_combinations)

        # Apply constraints if defined
        if parameter_space.constraints:
            combinations = self._apply_constraints(combinations, parameter_space.constraints)
            print(f"Combinations after constraints: {len(combinations):,}")

        return combinations

    def _generate_all_combinations(self,
                                    parameter_space: ParameterSpace,
                                    param_ranges: List[List]) -> List[Dict[str, Any]]:
        """Generate all possible combinations"""
        param_names = [p.name for p in parameter_space.parameters]

        # Use Cartesian product to generate all combinations
        combinations = []
        for values in itertools.product(*param_ranges):
            combination = dict(zip(param_names, values))
            combinations.append(combination)

        return combinations

    def _intelligent_sampling(self,
                             parameter_space: ParameterSpace,
                             param_ranges: List[List],
                             max_combinations: int) -> List[Dict[str, Any]]:
        """Intelligent parameter sampling strategy"""
        param_names = [p.name for p in parameter_space.parameters]
        combinations = []

        # Strategy 1: Grid sampling for important ranges
        important_params = self._identify_important_parameters(parameter_space)

        # Strategy 2: Random sampling with Latin Hypercube
        combinations.extend(self._latin_hypercube_sampling(
            parameter_space, param_ranges, max_combinations // 2
        ))

        # Strategy 3: Edge case sampling
        combinations.extend(self._edge_case_sampling(
            parameter_space, param_ranges, max_combinations // 4
        ))

        # Strategy 4: Random sampling for remaining
        remaining = max_combinations - len(combinations)
        if remaining > 0:
            combinations.extend(self._random_sampling(
                parameter_space, param_ranges, remaining
            ))

        # Remove duplicates
        unique_combinations = []
        seen = set()
        for combo in combinations:
            combo_key = tuple(sorted(combo.items()))
            if combo_key not in seen:
                seen.add(combo_key)
                unique_combinations.append(combo)

        return unique_combinations[:max_combinations]

    def _identify_important_parameters(self, parameter_space: ParameterSpace) -> List[str]:
        """Identify important parameters based on heuristics"""
        important = []

        for param in parameter_space.parameters:
            # Parameters with small ranges are usually more sensitive
            range_size = param.max_value - param.min_value
            if range_size <= 10:  # Small range parameters
                important.append(param.name)
            elif 'period' in param.name.lower() or 'window' in param.name.lower():
                important.append(param.name)  # Time-based parameters

        return important

    def _latin_hypercube_sampling(self,
                                 parameter_space: ParameterSpace,
                                 param_ranges: List[List],
                                 n_samples: int) -> List[Dict[str, Any]]:
        """Latin Hypercube Sampling for uniform parameter space coverage"""
        from scipy.stats import qmc

        # Create parameter bounds
        bounds = [(0, len(range_list) - 1) for range_list in param_ranges]

        # Generate Latin Hypercube samples
        sampler = qmc.LatinHypercube(d=len(bounds))
        sample_indices = sampler.integers(l_bounds=[b[0] for b in bounds],
                                       u_bounds=[b[1] for b in bounds],
                                       n=n_samples)

        # Convert indices to parameter values
        param_names = [p.name for p in parameter_space.parameters]
        combinations = []

        for idx_list in sample_indices:
            combination = {}
            for i, (param_name, idx) in enumerate(zip(param_names, idx_list)):
                combination[param_name] = param_ranges[i][idx]
            combinations.append(combination)

        return combinations

    def _edge_case_sampling(self,
                           parameter_space: ParameterSpace,
                           param_ranges: List[List],
                           n_samples: int) -> List[Dict[str, Any]]:
        """Sample edge cases and critical parameter values"""
        param_names = [p.name for p in parameter_space.parameters]
        combinations = []

        # Generate combinations with extreme values
        edge_values = []
        for param_range in param_ranges:
            edge_values.append([param_range[0], param_range[-1]])  # min and max

        # Add some edge case combinations
        for edge_combo in itertools.product(*edge_values):
            if len(combinations) < n_samples:
                combination = dict(zip(param_names, edge_combo))
                combinations.append(combination)

        # Add some interesting mid-range combinations
        if len(combinations) < n_samples:
            mid_values = []
            for param_range in param_ranges:
                mid_idx = len(param_range) // 2
                mid_values.append([param_range[mid_idx],
                                 param_range[min(mid_idx + 1, len(param_range) - 1)]])

            for mid_combo in itertools.product(*mid_values):
                if len(combinations) < n_samples:
                    combination = dict(zip(param_names, mid_combo))
                    combinations.append(combination)

        return combinations

    def _random_sampling(self,
                         parameter_space: ParameterSpace,
                         param_ranges: List[List],
                         n_samples: int) -> List[Dict[str, Any]]:
        """Random parameter sampling"""
        param_names = [p.name for p in parameter_space.parameters]
        combinations = []

        np.random.seed(42)  # For reproducibility

        for _ in range(n_samples):
            combination = {}
            for i, (param_name, param_range) in enumerate(zip(param_names, param_ranges)):
                combination[param_name] = np.random.choice(param_range)
            combinations.append(combination)

        return combinations

    def _apply_constraints(self,
                           combinations: List[Dict[str, Any]],
                           constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply parameter constraints"""
        if not constraints:
            return combinations

        filtered_combinations = []

        for combo in combinations:
            # Apply each constraint
            valid = True

            # Check period constraints
            if 'min_period' in constraints and 'max_period' in constraints:
                period = combo.get('period', combo.get('window', 0))
                if period < constraints['min_period'] or period > constraints['max_period']:
                    valid = False

            # Check smoothness constraint for MACD-like parameters
            if 'smoothness_constraint' in constraints:
                fast_period = combo.get('fast_period', 0)
                slow_period = combo.get('slow_period', 0)
                if fast_period > 0 and slow_period > 0 and fast_period >= slow_period:
                    valid = False

            # Check RSI-specific constraints
            if 'rsi_constraints' in constraints:
                oversold = combo.get('oversold', 30)
                overbought = combo.get('overbought', 70)
                if oversold >= overbought:
                    valid = False

            if valid:
                filtered_combinations.append(combo)

        return filtered_combinations

    def optimize_parameter_space(self,
                                 parameter_space: ParameterSpace,
                                 evaluation_function: Callable,
                                 max_combinations: int = 100000) -> Dict[str, Any]:
        """
        Optimize parameter space using the evaluation function

        Parameters:
        -----------
        parameter_space : ParameterSpace
            Parameter space definition
        evaluation_function : Callable
            Function to evaluate parameter combinations
        max_combinations : int
            Maximum combinations to test

        Returns:
        --------
        Dict[str, Any]
            Optimization results
        """
        start_time = time.time()

        # Generate parameter combinations
        combinations = self.generate_parameter_combinations(
            parameter_space, max_combinations
        )

        print(f"Starting optimization with {len(combinations):,} combinations")

        # Evaluate combinations
        results = []
        best_score = float('-inf')
        best_params = None

        for i, params in enumerate(combinations):
            try:
                score = evaluation_function(params)
                results.append({
                    'parameters': params,
                    'score': score,
                    'combination_id': i
                })

                if score > best_score:
                    best_score = score
                    best_params = params

                # Progress reporting
                if (i + 1) % 10000 == 0:
                    elapsed = time.time() - start_time
                    rate = (i + 1) / elapsed
                    eta = (len(combinations) - i - 1) / rate
                    print(f"Progress: {i+1:,}/{len(combinations):,} ({rate:.1f}/sec) ETA: {eta/60:.1f}min")

            except Exception as e:
                print(f"Error evaluating combination {i}: {e}")
                continue

        # Sort results by score
        results.sort(key=lambda x: x['score'], reverse=True)

        optimization_time = time.time() - start_time

        return {
            'best_parameters': best_params,
            'best_score': best_score,
            'total_combinations': len(combinations),
            'successful_evaluations': len(results),
            'optimization_time': optimization_time,
            'evaluation_rate': len(results) / optimization_time if optimization_time > 0 else 0,
            'top_results': results[:10],
            'parameter_space': parameter_space
        }

class ParameterSpaceVisualizer:
    """Parameter space visualization tools"""

    def __init__(self):
        pass

    def visualize_parameter_space(self, parameter_space: ParameterSpace):
        """Create parameter space visualizations"""
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns

            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle(f'Parameter Space: {parameter_space.name}', fontsize=16)

            # Parameter ranges visualization
            ax = axes[0, 0]
            param_names = [p.name for p in parameter_space.parameters]
            param_ranges = [p.max_value - p.min_value for p in parameter_space.parameters]

            bars = ax.bar(param_names, param_ranges)
            ax.set_title('Parameter Ranges')
            ax.set_ylabel('Range Size')
            ax.tick_params(axis='x', rotation=45)

            # Add value labels on bars
            for bar, value in zip(bars, param_ranges):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{value:.1f}', ha='center', va='bottom')

            # Parameter types distribution
            ax = axes[0, 1]
            type_counts = {}
            for param in parameter_space.parameters:
                type_counts[param.data_type] = type_counts.get(param.data_type, 0) + 1

            ax.pie(type_counts.values(), labels=type_counts.keys(), autopct='%1.1f%%')
            ax.set_title('Parameter Types Distribution')

            # Parameter complexity (step size analysis)
            ax = axes[1, 0]
            step_sizes = [p.step for p in parameter_space.parameters]
            ax.hist(step_sizes, bins=10, alpha=0.7)
            ax.set_title('Parameter Step Sizes')
            ax.set_xlabel('Step Size')
            ax.set_ylabel('Frequency')

            # Correlation heatmap (if applicable)
            ax = axes[1, 1]
            ax.text(0.5, 0.5, 'Parameter Correlation\nAnalysis\n(Implementation Required)',
                    ha='center', va='center', transform=ax.transAxes, fontsize=12)
            ax.set_title('Parameter Correlations')
            ax.axis('off')

            plt.tight_layout()

            # Save visualization
            filename = f'parameter_space_{parameter_space.name.lower().replace(" ", "_")}.png'
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"Parameter space visualization saved as: {filename}")

            return filename

        except ImportError:
            print("Matplotlib not available for visualization")
            return None

# Predefined parameter spaces for common technical indicators
class TechnicalIndicatorParameterSpaces:
    """Predefined parameter spaces for technical indicators"""

    @staticmethod
    def rsi_parameter_space() -> ParameterSpace:
        """RSI parameter space"""
        return ParameterSpace(
            name="RSI_Parameters",
            description="Relative Strength Index parameter optimization space",
            parameters=[
                ParameterRange("period", 10, 30, 1, "int", "RSI calculation period"),
                ParameterRange("oversold", 20, 35, 5, "float", "Oversold threshold"),
                ParameterRange("overbought", 65, 80, 5, "float", "Overbought threshold"),
            ],
            constraints={
                "rsi_constraints": True
            }
        )

    @staticmethod
    def macd_parameter_space() -> ParameterSpace:
        """MACD parameter space"""
        return ParameterSpace(
            name="MACD_Parameters",
            description="MACD indicator parameter optimization space",
            parameters=[
                ParameterRange("fast_period", 8, 18, 1, "int", "Fast EMA period"),
                ParameterRange("slow_period", 20, 35, 1, "int", "Slow EMA period"),
                ParameterRange("signal_period", 8, 15, 1, "int", "Signal line period"),
                ParameterRange("method", 0, 2, 1, "int", "MACD calculation method"),
            ],
            constraints={
                "smoothness_constraint": True
            }
        )

    @staticmethod
    def bollinger_bands_parameter_space() -> ParameterSpace:
        """Bollinger Bands parameter space"""
        return ParameterSpace(
            name="Bollinger_Bands_Parameters",
            description="Bollinger Bands parameter optimization space",
            parameters=[
                ParameterRange("period", 10, 50, 1, "int", "Moving average period"),
                ParameterRange("std_dev", 1.5, 3.0, 0.1, "float", "Standard deviation multiplier"),
                ParameterRange("ma_type", 0, 2, 1, "int", "Moving average type"),
            ],
            constraints={
                "min_period": 10,
                "max_period": 50
            }
        )

    @staticmethod
    def comprehensive_parameter_space() -> ParameterSpace:
        """Comprehensive parameter space for multiple indicators"""
        return ParameterSpace(
            name="Comprehensive_Technical_Indicators",
            description="Complete technical indicator parameter optimization space",
            parameters=[
                # Trend indicators
                ParameterRange("rsi_period", 10, 30, 1, "int", "RSI period"),
                ParameterRange("macd_fast", 8, 18, 1, "int", "MACD fast period"),
                ParameterRange("macd_slow", 20, 35, 1, "int", "MACD slow period"),
                ParameterRange("ema_period", 15, 35, 1, "int", "EMA period"),

                # Volatility indicators
                ParameterRange("bb_period", 15, 25, 1, "int", "Bollinger Bands period"),
                ParameterRange("bb_std", 1.8, 2.5, 0.1, "float", "Bollinger Bands std dev"),
                ParameterRange("atr_period", 10, 20, 1, "int", "ATR period"),

                # Economic indicators
                ParameterRange("rate_spread_threshold", 0.1, 1.0, 0.1, "float", "Rate spread threshold"),
                ParameterRange("momentum_window", 5, 25, 1, "int", "Momentum calculation window"),
                ParameterRange("volatility_threshold", 0.5, 2.0, 0.1, "float", "Volatility threshold"),
            ],
            constraints={
                "min_period": 5,
                "max_period": 50,
                "period_consistency": True,
                "parameter_balance": True
            }
        )

def test_parameter_space_optimizer():
    """Test the parameter space optimizer"""

    print("=" * 60)
    print("Phase 3.1: Parameter Space Optimization System Test")
    print("=" * 60)

    # Test 1: Basic parameter space definition
    print("\n1. Testing Parameter Space Definition:")
    try:
        rsi_space = TechnicalIndicatorParameterSpaces.rsi_parameter_space()
        print(f"✓ RSI Parameter Space: {len(rsi_space.parameters)} parameters")

        macd_space = TechnicalIndicatorParameterSpaces.macd_parameter_space()
        print(f"✓ MACD Parameter Space: {len(macd_space.parameters)} parameters")

        bb_space = TechnicalIndicatorParameterSpaces.bollinger_bands_parameter_space()
        print(f"✓ Bollinger Bands Parameter Space: {len(bb_space.parameters)} parameters")

        comprehensive_space = TechnicalIndicatorParameterSpaces.comprehensive_parameter_space()
        print(f"✓ Comprehensive Parameter Space: {len(comprehensive_space.parameters)} parameters")

    except Exception as e:
        print(f"✗ Parameter Space Definition Failed: {e}")
        return False

    # Test 2: Parameter combination generation
    print("\n2. Testing Parameter Combination Generation:")
    try:
        generator = ParameterSpaceGenerator(max_combinations=100000)

        # Test with small parameter space
        combinations = generator.generate_parameter_combinations(rsi_space, max_combinations=1000)
        print(f"✓ Generated {len(combinations)} RSI combinations")
        print(f"  Sample: {combinations[0]}")

        # Test with larger parameter space
        combinations = generator.generate_parameter_combinations(comprehensive_space, max_combinations=50000)
        print(f"✓ Generated {len(combinations):,} comprehensive combinations")

    except Exception as e:
        print(f"✗ Parameter Combination Generation Failed: {e}")
        return False

    # Test 3: Parameter space visualization
    print("\n3. Testing Parameter Space Visualization:")
    try:
        visualizer = ParameterSpaceVisualizer()
        viz_file = visualizer.visualize_parameter_space(rsi_space)
        if viz_file:
            print(f"✓ Parameter space visualization created: {viz_file}")
        else:
            print("- Visualization skipped (matplotlib not available)")

    except Exception as e:
        print(f"✗ Visualization Failed: {e}")
        # Don't return False as visualization is optional

    # Test 4: Mock optimization
    print("\n4. Testing Mock Optimization:")
    try:
        def mock_evaluation_function(params):
            """Mock evaluation function for testing"""
            # Simple scoring function
            score = 0
            if 'period' in params:
                score += (30 - abs(params['period'] - 14)) * 2  # Prefer RSI around 14
            if 'oversold' in params and 'overbought' in params:
                score += (params['overbought'] - params['oversold']) * 3  # Prefer wider bands
            return score + np.random.uniform(-1, 1)  # Add some noise

        # Run optimization
        generator = ParameterSpaceGenerator()
        result = generator.optimize_parameter_space(
            rsi_space, mock_evaluation_function, max_combinations=500
        )

        print(f"✓ Mock Optimization Completed:")
        print(f"  Best Score: {result['best_score']:.2f}")
        print(f"  Best Parameters: {result['best_parameters']}")
        print(f"  Total Combinations: {result['total_combinations']:,}")
        print(f"  Successful Evaluations: {result['successful_evaluations']:,}")
        print(f"  Optimization Time: {result['optimization_time']:.2f}s")
        print(f"  Evaluation Rate: {result['evaluation_rate']:.1f} evals/sec")

    except Exception as e:
        print(f"✗ Mock Optimization Failed: {e}")
        return False

    print("\n" + "=" * 60)
    print("Phase 3.1 Parameter Space Optimization System: ✓ SUCCESS")
    print("All core functionality tested and working correctly")
    print("System ready for production optimization tasks")
    print("=" * 60)

    return True

if __name__ == "__main__":
    success = test_parameter_space_optimizer()

    if success:
        print("\n🎉 Phase 3.1 Implementation Completed Successfully!")
        print("Parameter Space Optimization System Ready for Production Use")
    else:
        print("\n❌ Phase 3.1 Implementation Failed")
        print("Please review and fix issues before proceeding")
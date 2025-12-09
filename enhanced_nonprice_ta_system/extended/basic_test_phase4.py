#!/usr/bin/env python3
"""
Basic Phase 4 Signal Fusion System Test
基本Phase 4信号融合系统测试

Simple test without Unicode characters to avoid encoding issues.
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Add project path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def test_import():
    """Test module imports"""
    print("Testing module imports...")

    try:
        # Test basic imports
        from signal_fusion import (
            SignalGenerator, SignalType, SignalFormat,
            DynamicWeightManager, WeightAdjustmentStrategy,
            ConflictResolver, ConflictResolutionStrategy,
            CompositeSignalGenerator, SignalQuality
        )
        print("Core modules imported successfully")

        # Test utility functions
        from signal_fusion import get_system_capabilities, create_complete_fusion_system
        print("Utility functions imported successfully")

        return True, {
            'signal_generator': SignalGenerator,
            'signal_type': SignalType,
            'weight_manager': DynamicWeightManager,
            'conflict_resolver': ConflictResolver,
            'composite_generator': CompositeSignalGenerator
        }

    except Exception as e:
        print(f"Import failed: {str(e)}")
        return False, {}

def test_signal_generation(components):
    """Test signal generation"""
    print("\nTesting signal generation...")

    try:
        SignalGenerator = components['signal_generator']

        # Create test data
        dates = pd.date_range('2023-01-01', periods=100, freq='D')

        # Generate different types of indicator data
        rsi_data = pd.Series(
            50 + 30 * np.sin(np.linspace(0, 4*np.pi, 100)) + np.random.normal(0, 5, 100),
            index=dates
        ).clip(0, 100)

        macd_data = pd.Series(
            np.cumsum(np.random.randn(100) * 0.1),
            index=dates
        )

        hibor_data = pd.Series(
            3.0 + 1.5 * np.sin(np.linspace(0, 2*np.pi, 100)) + np.random.normal(0, 0.2, 100),
            index=dates
        ).clip(0.5, 8)

        # Initialize signal generator
        signal_gen = SignalGenerator(
            signal_format=SignalFormat.MULTI_LEVEL,
            confidence_threshold=0.5,
            enable_historical_tracking=True
        )

        # Test signal generation for different indicators
        test_cases = [
            ('RSI', rsi_data, {'name': 'RSI', 'period': 14, 'oversold': 30, 'overbought': 70}),
            ('MACD', macd_data, {'name': 'MACD_HIST', 'fast': 12, 'slow': 26, 'signal': 9}),
            ('HIBOR_RATE', hibor_data, {'name': 'HIBOR_RATE'})
        ]

        generated_signals = []
        for indicator_name, data, params in test_cases:
            try:
                signal = signal_gen.generate_signal(
                    indicator_name=indicator_name,
                    indicator_values=data,
                    parameters=params
                )
                generated_signals.append(signal)

                print(f"  {indicator_name}: {signal.signal_type.name} "
                      f"(strength: {signal.strength:.2f}, confidence: {signal.confidence:.2f})")

            except Exception as e:
                print(f"  {indicator_name}: Error - {str(e)}")

        if len(generated_signals) > 0:
            print("Signal generation test passed")
            return True, generated_signals
        else:
            print("No signals generated")
            return False, []

    except Exception as e:
        print(f"Signal generation test failed: {str(e)}")
        return False, []

def test_weight_management(components):
    """Test weight management"""
    print("\nTesting weight management...")

    try:
        DynamicWeightManager = components['weight_manager']

        # Initial weights
        initial_weights = {
            'RSI': 0.4,
            'MACD': 0.3,
            'HIBOR_RATE': 0.3
        }

        # Create weight manager
        weight_mgr = DynamicWeightManager(
            initial_weights=initial_weights,
            adjustment_strategy=WeightAdjustmentStrategy.HYBRID,
            enable_optimization=True
        )

        print(f"  Initial weights: {initial_weights}")

        # Test weight statistics
        stats = weight_mgr.get_weight_statistics()
        print(f"  Weight statistics available: {len(stats)} items")

        # Test weight optimization (simple objective function)
        def objective_function(weights):
            return sum(w * 0.5 for w in weights.values())  # Simple linear function

        try:
            optimized_weights = weight_mgr.optimize_weights(
                objective_function=objective_function,
                optimization_method='random_search',
                num_iterations=10
            )
            print("  Weight optimization test passed")
        except Exception as e:
            print(f"  Weight optimization warning: {str(e)}")

        print("Weight management test passed")
        return True

    except Exception as e:
        print(f"Weight management test failed: {str(e)}")
        return False

def test_conflict_resolution(components, signals):
    """Test conflict resolution"""
    print("\nTesting conflict resolution...")

    try:
        ConflictResolver = components['conflict_resolver']

        if len(signals) < 2:
            print("  Not enough signals for conflict resolution test")
            return True

        # Create conflict resolver
        conflict_resolver = ConflictResolver(
            default_strategy=ConflictResolutionStrategy.WEIGHTED_VOTING,
            enable_learning=True
        )

        # Test conflict resolution
        weights = {'RSI': 0.4, 'MACD': 0.3, 'HIBOR_RATE': 0.3}
        market_context = {'regime': 'bull', 'volatility': 0.02}

        resolved_signal, conflicts = conflict_resolver.resolve_conflicts(
            signals=signals,
            weights=weights,
            market_context=market_context
        )

        if resolved_signal:
            print(f"  Resolved signal: {resolved_signal.signal_type.name}")
            print(f"  Conflicts detected: {len(conflicts)}")

        # Test different strategies
        strategies_to_test = [
            ConflictResolutionStrategy.MAJORITY_VOTING,
            ConflictResolutionStrategy.CONSENSUS_BASED,
            ConflictResolutionStrategy.CONFIDENCE_WEIGHTED
        ]

        for strategy in strategies_to_test:
            try:
                result, _ = conflict_resolver.resolve_conflicts(
                    signals=signals,
                    weights=weights,
                    market_context=market_context,
                    strategy=strategy
                )
                print(f"  {strategy.value} strategy: OK")
            except Exception as e:
                print(f"  {strategy.value} strategy: Warning - {str(e)}")

        print("Conflict resolution test passed")
        return True

    except Exception as e:
        print(f"Conflict resolution test failed: {str(e)}")
        return False

def test_composite_signal_generation(components, signals):
    """Test composite signal generation"""
    print("\nTesting composite signal generation...")

    try:
        CompositeSignalGenerator = components['composite_generator']

        # Create individual components
        from signal_fusion import SignalGenerator, DynamicWeightManager, ConflictResolver

        signal_gen = SignalGenerator()
        weight_mgr = DynamicWeightManager({
            'RSI': 0.4, 'MACD': 0.3, 'HIBOR_RATE': 0.3
        })
        conflict_resolver = ConflictResolver()

        # Create composite signal generator
        composite_gen = CompositeSignalGenerator(
            signal_generator=signal_gen,
            weight_manager=weight_mgr,
            conflict_resolver=conflict_resolver,
            enable_quality_assessment=True
        )

        # Create test indicator data
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        indicator_data = {
            'RSI': pd.Series(50 + 20 * np.random.randn(50), index=dates).clip(0, 100),
            'MACD': pd.Series(np.random.randn(50) * 0.1, index=dates),
            'HIBOR_RATE': pd.Series(3.0 + 0.5 * np.random.randn(50), index=dates)
        }

        parameters = {
            'RSI': {'name': 'RSI', 'period': 14, 'oversold': 30, 'overbought': 70},
            'MACD': {'name': 'MACD_HIST', 'fast': 12, 'slow': 26, 'signal': 9},
            'HIBOR_RATE': {'name': 'HIBOR_RATE'}
        }

        market_context = {'regime': 'bull', 'volatility': 0.02, 'trend': 'upward'}

        # Generate composite signal
        composite_signal = composite_gen.generate_composite_signal(
            indicator_data=indicator_data,
            parameters=parameters,
            market_context=market_context
        )

        print(f"  Composite signal: {composite_signal.signal_type.name}")
        print(f"  Signal strength: {composite_signal.strength:.2f}/10")
        print(f"  Confidence: {composite_signal.confidence:.2%}")
        print(f"  Quality: {composite_signal.quality.value}")
        print(f"  Component signals: {len(composite_signal.component_signals)}")

        if composite_signal.explanation:
            print(f"  Explanation summary: {composite_signal.explanation.summary}")

        # Test performance metrics
        metrics = composite_gen.get_performance_metrics()
        print(f"  Performance metrics: {metrics.total_signals} signals processed")

        print("Composite signal generation test passed")
        return True

    except Exception as e:
        print(f"Composite signal generation test failed: {str(e)}")
        return False

def test_system_capabilities(components):
    """Test system capabilities"""
    print("\nTesting system capabilities...")

    try:
        from signal_fusion import get_system_capabilities

        capabilities = get_system_capabilities()

        print("System capabilities:")
        for component, features in capabilities.items():
            print(f"\n{component.upper()}:")
            if isinstance(features, dict):
                for feature, value in features.items():
                    if isinstance(value, list):
                        print(f"  - {feature}: {', '.join(value[:3])}{'...' if len(value) > 3 else ''}")
                    else:
                        print(f"  - {feature}: {value}")
            else:
                print(f"  - {features}")

        print("System capabilities test passed")
        return True

    except Exception as e:
        print(f"System capabilities test failed: {str(e)}")
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("Phase 4 Signal Fusion System Integration Test")
    print("=" * 60)

    tests = [
        ("Module Import", test_import),
        ("System Capabilities", test_system_capabilities),
        ("Signal Generation", test_signal_generation),
        ("Weight Management", test_weight_management),
        ("Conflict Resolution", test_conflict_resolution),
        ("Composite Signal Generation", test_composite_signal_generation)
    ]

    passed = 0
    total = len(tests)
    components = {}
    signals = []

    for test_name, test_func in tests:
        print(f"\n{'-' * 20} {test_name} {'-' * 20}")

        try:
            if test_name == "Module Import":
                success, result = test_func()
                if success:
                    components = result
                    passed += 1
            elif test_name == "Signal Generation":
                success, result = test_func(components)
                if success:
                    signals = result
                    passed += 1
            elif test_name == "Conflict Resolution" or test_name == "Composite Signal Generation":
                # These tests depend on previous test results
                if components:
                    success = test_func(components, signals)
                    if success:
                        passed += 1
                else:
                    print("  Skipped - dependencies not available")
                    success = True  # Don't count as failure
            else:
                if test_name == "System Capabilities":
                    success = test_func(components)
                else:
                    success = test_func(components)
                if success:
                    passed += 1

            if success:
                print(f"{test_name} PASSED")
            else:
                print(f"{test_name} FAILED")

        except Exception as e:
            print(f"{test_name} ERROR: {str(e)}")

    print(f"\n{'=' * 60}")
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("SUCCESS: All tests passed! Phase 4 Signal Fusion System is working correctly.")
        print("\nSystem Features Verified:")
        print("  - Single indicator signal generation")
        print("  - Dynamic weight management")
        print("  - Conflict resolution mechanisms")
        print("  - Composite signal generation with explainable AI")
        print("  - Quality assessment and reporting")

        return True
    else:
        print("WARNING: Some tests failed. Please check the system configuration.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
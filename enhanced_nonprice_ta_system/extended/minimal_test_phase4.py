#!/usr/bin/env python3
"""
Minimal Phase 4 Test - Test core functionality without complex imports
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

def test_basic_imports():
    """Test only the most basic imports"""
    print("Testing basic imports...")

    try:
        # Try to import signal_generator directly
        import signal_fusion.signal_generator as sg
        print("✓ signal_generator imported")

        import signal_fusion.weight_manager as wm
        print("✓ weight_manager imported")

        import signal_fusion.conflict_resolver as cr
        print("✓ conflict_resolver imported")

        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_signal_generation():
    """Test basic signal generation"""
    print("\nTesting signal generation...")

    try:
        # Import directly to avoid package issues
        from signal_fusion.signal_generator import SignalGenerator, SignalType

        # Create simple test data
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        rsi_data = pd.Series([45, 50, 55, 60, 58] * 10, index=dates)

        # Create signal generator
        signal_gen = SignalGenerator()

        # Generate signal
        signal = signal_gen.generate_signal(
            indicator_name='RSI',
            indicator_values=rsi_data,
            parameters={'name': 'RSI', 'period': 14, 'oversold': 30, 'overbought': 70}
        )

        print(f"✓ Signal generated: {signal.signal_type.name}")
        print(f"  Strength: {signal.strength:.2f}")
        print(f"  Confidence: {signal.confidence:.2f}")

        return True

    except Exception as e:
        print(f"✗ Signal generation failed: {e}")
        return False

def test_weight_management():
    """Test basic weight management"""
    print("\nTesting weight management...")

    try:
        from signal_fusion.weight_manager import DynamicWeightManager

        # Create weight manager
        weights = {'RSI': 0.6, 'MACD': 0.4}
        weight_mgr = DynamicWeightManager(initial_weights=weights)

        # Test basic functionality
        stats = weight_mgr.get_weight_statistics()

        print(f"✓ Weight manager created with {len(weights)} indicators")
        print(f"✓ Statistics available: {len(stats)} items")

        return True

    except Exception as e:
        print(f"✗ Weight management failed: {e}")
        return False

def test_conflict_resolution():
    """Test basic conflict resolution"""
    print("\nTesting conflict resolution...")

    try:
        from signal_fusion.conflict_resolver import ConflictResolver
        from signal_fusion.signal_generator import SignalGenerator, SignalType

        # Create resolver
        resolver = ConflictResolver()

        # Create test signals
        signal_gen = SignalGenerator()
        dates = pd.date_range('2023-01-01', periods=10, freq='D')

        # Generate conflicting signals
        rsi_signal = signal_gen.generate_signal(
            'RSI', pd.Series([25, 30, 35] + [50]*7, index=dates),
            {'name': 'RSI', 'period': 14, 'oversold': 30, 'overbought': 70}
        )

        macd_signal = signal_gen.generate_signal(
            'MACD', pd.Series([0.1, 0.2, 0.3] + [0.0]*7, index=dates),
            {'name': 'MACD_HIST', 'fast': 12, 'slow': 26, 'signal': 9}
        )

        # Test conflict resolution
        signals = [rsi_signal, macd_signal]
        weights = {'RSI': 0.6, 'MACD': 0.4}

        resolved, conflicts = resolver.resolve_conflicts(signals, weights)

        print(f"✓ Conflict resolution completed")
        print(f"  Input signals: {len(signals)}")
        print(f"  Conflicts detected: {len(conflicts)}")
        if resolved:
            print(f"  Resolved signal: {resolved.signal_type.name}")

        return True

    except Exception as e:
        print(f"✗ Conflict resolution failed: {e}")
        return False

def main():
    """Main test function"""
    print("=" * 50)
    print("Minimal Phase 4 Signal Fusion System Test")
    print("=" * 50)

    tests = [
        ("Basic Imports", test_basic_imports),
        ("Signal Generation", test_signal_generation),
        ("Weight Management", test_weight_management),
        ("Conflict Resolution", test_conflict_resolution)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n{'-' * 20} {test_name} {'-' * 20}")

        try:
            success = test_func()
            if success:
                passed += 1
                print(f"{test_name} PASSED")
            else:
                print(f"{test_name} FAILED")
        except Exception as e:
            print(f"{test_name} ERROR: {e}")

    print(f"\n{'=' * 50}")
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("SUCCESS: Core Phase 4 functionality is working!")
        print("\nVerified features:")
        print("  - Signal generation")
        print("  - Weight management")
        print("  - Conflict resolution")
        print("  - Basic imports and structure")
        return True
    else:
        print("Some tests failed. Check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
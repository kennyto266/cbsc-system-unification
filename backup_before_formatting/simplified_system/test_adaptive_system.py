"""
Adaptive System Test - Simplified Version
"""

import sys
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime

# Add to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'workflow'))

def test_adaptive_system():
    """Test the adaptive market system with sample data"""
    print("Starting Adaptive System Test...")
    print("=" * 50)

    try:
        # Import the adaptive system
        from adaptive_market_system import AdaptiveMarketSystem

        # Create system instance
        system = AdaptiveMarketSystem()

        # Generate sample market data
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        np.random.seed(42)

        # Simulate different market conditions for different sources
        market_data = {
            "hibor_rates": pd.Series(
                np.cumsum(np.random.normal(0.001, 0.02, 100)) + 3.5,
                index=dates
            ),
            "monetary_base": pd.Series(
                np.cumsum(np.random.normal(0.0005, 0.01, 100)) + 1000,
                index=dates
            ),
            "exchange_rates": pd.Series(
                np.cumsum(np.random.normal(-0.0002, 0.015, 100)) + 7.8,
                index=dates
            ),
            "interbank_liquidity": pd.Series(
                np.cumsum(np.random.normal(0.0003, 0.025, 100)) + 500,
                index=dates
            ),
            "efbn_indicative": pd.Series(
                np.cumsum(np.random.normal(0.0001, 0.018, 100)) + 4.5,
                index=dates
            ),
            "rmb_liquidity": pd.Series(
                np.cumsum(np.random.normal(-0.0001, 0.012, 100)) + 100,
                index=dates
            )
        }

        print(f"Generated {len(market_data)} market data sources")
        for name, data in market_data.items():
            print(f"  - {name}: {len(data)} data points")

        # Run adaptive analysis
        print("\nRunning adaptive market analysis...")
        results = system.run_adaptive_analysis(market_data)

        # Display results
        print("\nAdaptive Analysis Results:")
        print("=" * 50)

        final_signal = results.get('final_signal', {})
        print(f"Final Signal: {final_signal.get('signal', 'N/A')}")
        print(f"Confidence: {final_signal.get('confidence', 0):.2%}")

        market_state = results.get('consensus_market_state', {})
        print(f"\nMarket Regime: {market_state.get('regime', 'N/A')}")
        print(f"Volatility Level: {market_state.get('volatility_level', 0):.4f}")
        print(f"Trend Strength: {market_state.get('trend_strength', 0):.4f}")
        print(f"Momentum Score: {market_state.get('momentum_score', 0):.4f}")
        print(f"Confidence: {market_state.get('confidence', 0):.4f}")

        # Adaptive weights
        weights = results.get('adaptive_weights', {})
        if weights:
            print(f"\nAdaptive Weights:")
            for source, weight in weights.items():
                print(f"  - {source}: {weight:.3f}")

        # Source analyses summary
        source_analyses = results.get('source_analyses', {})
        if source_analyses:
            print(f"\nSource Analyses Summary:")
            for source_name, analysis in source_analyses.items():
                market_state = analysis.get('market_state', {})
                indicators = analysis.get('adaptive_indicators', {})
                total_score = indicators.get('total_score', 0)

                print(f"  - {source_name}:")
                print(f"    Regime: {market_state.get('regime', 'N/A')}")
                print(f"    Total Score: {total_score:.3f}")

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"adaptive_system_test_{timestamp}.json"

        try:
            with open(f"results/{filename}", 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2, default=str)
            print(f"\nResults saved to: results/{filename}")
        except Exception as e:
            print(f"Failed to save results: {e}")

        print("\nAdaptive System Test Completed Successfully!")
        return True

    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_individual_components():
    """Test individual components of the adaptive system"""
    print("\nTesting Individual Components...")
    print("=" * 50)

    try:
        from adaptive_market_system import (
            MarketRegimeDetector,
            AdaptiveParameterOptimizer,
            AdaptiveTechnicalAnalyzer
        )

        # Test Market Regime Detector
        print("1. Testing Market Regime Detector...")
        detector = MarketRegimeDetector()

        # Test with different market conditions
        dates = pd.date_range('2024-01-01', periods=100, freq='D')

        # Bull market data
        bull_data = pd.Series(
            np.cumsum(np.random.normal(0.002, 0.01, 100)) + 100,
            index=dates
        )

        # Bear market data
        bear_data = pd.Series(
            np.cumsum(np.random.normal(-0.0015, 0.015, 100)) + 100,
            index=dates
        )

        # Sideways market data
        sideways_data = pd.Series(
            np.cumsum(np.random.normal(0.0, 0.008, 100)) + 100,
            index=dates
        )

        bull_state = detector.detect_market_regime(bull_data)
        bear_state = detector.detect_market_regime(bear_data)
        sideways_state = detector.detect_market_regime(sideways_data)

        print(f"  Bull Market Detection: {bull_state.regime.value}")
        print(f"  Bear Market Detection: {bear_state.regime.value}")
        print(f"  Sideways Market Detection: {sideways_state.regime.value}")

        # Test Adaptive Parameter Optimizer
        print("\n2. Testing Adaptive Parameter Optimizer...")
        optimizer = AdaptiveParameterOptimizer()

        optimal_bull_params = optimizer.get_optimal_parameters(bull_state)
        optimal_bear_params = optimizer.get_optimal_parameters(bear_state)

        print(f"  Bull Market Parameters: RSI={optimal_bull_params.rsi_periods}, Sensitivity={optimal_bull_params.sensitivity_level:.2f}")
        print(f"  Bear Market Parameters: RSI={optimal_bear_params.rsi_periods}, Sensitivity={optimal_bear_params.sensitivity_level:.2f}")

        # Test Adaptive Technical Analyzer
        print("\n3. Testing Adaptive Technical Analyzer...")
        analyzer = AdaptiveTechnicalAnalyzer()

        bull_analysis = analyzer.analyze_with_adaptation(bull_data, "bull_test")
        bear_analysis = analyzer.analyze_with_adaptation(bear_data, "bear_test")

        print(f"  Bull Analysis Score: {bull_analysis['adaptive_indicators'].get('total_score', 0):.3f}")
        print(f"  Bear Analysis Score: {bear_analysis['adaptive_indicators'].get('total_score', 0):.3f}")

        print("\nIndividual Components Test Passed!")
        return True

    except Exception as e:
        print(f"Error in component testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Adaptive System Test Suite")
    print("=" * 50)

    # Test individual components first
    component_success = test_individual_components()

    if component_success:
        # Test full system
        system_success = test_adaptive_system()

        if system_success:
            print("\n" + "=" * 50)
            print("ALL TESTS PASSED!")
            print("Phase 3: Adaptive System Implementation - COMPLETED")
            print("=" * 50)
        else:
            print("\nSystem test failed!")
    else:
        print("\nComponent tests failed, skipping system test!")
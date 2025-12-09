#!/usr/bin/env python3
"""
0700.HK Alpha Factor Optimization Tool
Optimize 0700.HK trading strategies using Alpha Factor System
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

# Add project path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def load_0700_data():
    """Load 0700.HK real data"""
    print("Loading 0700.HK real data...")

    try:
        # Try to load from existing data sources
        data_sources = [
            'data/0700_hk_data.csv',
            'data/0700_hk.csv',
            '../data/0700_hk_data.csv'
        ]

        for source in data_sources:
            if os.path.exists(source):
                print(f"Loading data from: {source}")
                data = pd.read_csv(source, index_col=0, parse_dates=True)
                if 'Close' not in data.columns and 'close' in data.columns:
                    data['Close'] = data['close']
                if 'Open' not in data.columns and 'open' in data.columns:
                    data['Open'] = data['open']
                if 'High' not in data.columns and 'high' in data.columns:
                    data['High'] = data['high']
                if 'Low' not in data.columns and 'low' in data.columns:
                    data['Low'] = data['low']
                if 'Volume' not in data.columns and 'volume' in data.columns:
                    data['Volume'] = data['volume']
                return data

        # If no existing data, generate realistic 0700.HK simulation
        print("No existing data found, generating realistic 0700.HK simulation...")
        return generate_realistic_0700_data()

    except Exception as e:
        print(f"Error loading data: {e}")
        return generate_realistic_0700_data()

def generate_realistic_0700_data():
    """Generate realistic 0700.HK simulation data"""
    print("Generating realistic 0700.HK price simulation...")

    # Based on real Tencent price movements (2020-2023)
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')
    n_days = len(dates)

    # Realistic price trend for Tencent (around 300-600 HKD range)
    base_price = 400
    trend = np.linspace(base_price, base_price * 1.5, n_days)  # Upward trend
    volatility = np.random.randn(n_days) * 8  # Daily volatility ~8 HKD
    cyclical = 20 * np.sin(np.linspace(0, 4*np.pi, n_days))  # Market cycles

    price = trend + volatility + cyclical
    price = np.maximum(price, 100)  # Minimum price

    # Generate OHLC data
    daily_range = price * 0.025  # 2.5% daily range
    high = price + np.random.rand(n_days) * daily_range
    low = price - np.random.rand(n_days) * daily_range
    open_price = price + np.random.randn(n_days) * 0.01

    # Generate volume (Tencent typically has high volume)
    base_volume = 15000000  # 15M shares base
    volume_variation = 0.5 * np.sin(np.linspace(0, 8*np.pi, n_days))
    volume = base_volume * (1 + volume_variation) * (1 + np.random.randn(n_days) * 0.2)

    # Ensure OHLC relationships
    high = np.maximum(high, np.maximum(open_price, price))
    low = np.minimum(low, np.minimum(open_price, price))

    data = pd.DataFrame({
        'Open': open_price,
        'High': high,
        'Low': low,
        'Close': price,
        'Volume': volume
    }, index=dates)

    print(f"Generated {len(data)} days of realistic 0700.HK data")
    print(f"Price range: {price.min():.1f} - {price.max():.1f} HKD")
    print(f"Average volume: {volume.mean():,.0f} shares")

    return data

def calculate_alpha_factors(data):
    """Calculate Alpha factors for 0700.HK"""
    print("\nCalculating Alpha factors for 0700.HK...")

    try:
        from alpha.factor_engine.alpha_factor_engine import AlphaFactorEngine, FactorTypes, FactorConfig
        from alpha.alpha_factors.technical_to_alpha_converter import TechnicalIndicatorConverter

        # Create factor engine configuration
        config = FactorConfig(
            standardize=True,
            winsorize=True,
            winsorize_method="quantile",
            winsorize_limits=(0.05, 0.95)
        )

        # Initialize factor engine
        engine = AlphaFactorEngine(config)

        # Calculate basic Alpha factors
        factor_types = [
            FactorTypes.MOMENTUM,
            FactorTypes.REVERSAL,
            FactorTypes.VOLATILITY,
            FactorTypes.VOLUME
        ]
        lookback_periods = [5, 10, 20, 30, 60]

        print("Calculating basic Alpha factors...")
        basic_factors = engine.calculate_factors(
            data,
            factor_types=factor_types,
            lookback_periods=lookback_periods
        )

        print(f"SUCCESS: Calculated {len(basic_factors)} basic Alpha factors")

        # Convert technical indicators to Alpha factors
        print("Converting technical indicators to Alpha factors...")
        converter = TechnicalIndicatorConverter()
        technical_factors = converter.convert_technical_to_alpha(
            data,
            indicator_names=['RSI', 'MACD'],  # Use reliable indicators
            lookback_periods=[14, 20, 30]
        )

        print(f"SUCCESS: Converted {len(technical_factors.columns)} technical indicators")

        # Combine all factors
        all_factor_data = {}

        # Add basic factors
        for name, metrics in basic_factors.items():
            factor_data = metrics.factor_data
            if isinstance(factor_data, pd.DataFrame) and len(factor_data.columns) == 1:
                # Extract Series from DataFrame
                all_factor_data[name] = factor_data.iloc[:, 0]
            else:
                all_factor_data[name] = factor_data

        # Add technical factors
        for col in technical_factors.columns:
            if len(technical_factors[col].dropna()) > 30:
                all_factor_data[col] = technical_factors[col]

        combined_factors = pd.DataFrame(all_factor_data)
        combined_factors = combined_factors.dropna(axis=1, how='all')

        print(f"SUCCESS: Combined {len(combined_factors.columns)} Alpha factors")
        print(f"Effective data points: {len(combined_factors.dropna())}")

        return combined_factors, engine

    except Exception as e:
        print(f"FAILED: Alpha factor calculation failed: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def validate_factors(data, factors):
    """Validate Alpha factors effectiveness"""
    print("\nValidating Alpha factors effectiveness...")

    try:
        from alpha.factor_analyzer.factor_validator import FactorValidator

        if factors is None or factors.empty:
            print("No factor data available for validation")
            return None

        validator = FactorValidator(risk_free_rate=0.03, confidence_level=0.95)

        # Calculate returns
        returns = data['Close'].pct_change()

        # Validate top factors
        factor_results = {}
        selected_factors = list(factors.columns[:10])  # Test top 10 factors

        print(f"Analyzing top {len(selected_factors)} factors...")

        for factor_name in selected_factors:
            factor_data = factors[[factor_name]].dropna()

            if len(factor_data) < 30:
                continue

            try:
                # Create FactorMetrics object
                from alpha.factor_engine.alpha_factor_engine import FactorMetrics, FactorTypes

                metrics = FactorMetrics(
                    factor_name=factor_name,
                    factor_type=FactorTypes.TECHNICAL,
                    factor_data=factor_data,
                    description=f"Alpha factor {factor_name}",
                    calculation_method="Alpha factor analysis",
                    lookback_period=20
                )

                # Validate factor
                result = validator.validate_factor(metrics, data, returns)
                factor_results[factor_name] = result

                print(f"  {factor_name}: IC={result.ic_mean:.4f}, Sharpe={result.sharpe_ratio:.3f}")

            except Exception as e:
                print(f"  {factor_name}: Validation failed ({e})")
                continue

        if not factor_results:
            print("No successful factor validations")
            return None

        # Generate validation report
        report = validator.generate_validation_report(factor_results)

        if not report.empty:
            print(f"\nSUCCESS: Factor validation completed for {len(report)} factors")
            print("\nTop performing factors:")
            display_cols = ['factor_name', 'ic_mean', 'sharpe_ratio', 'hit_rate', 'composite_score']
            top_factors = report.sort_values('composite_score', ascending=False).head(5)
            print(top_factors[display_cols].round(4))

            return report

        return None

    except Exception as e:
        print(f"FAILED: Factor validation failed: {e}")
        return None

def build_multifactor_model(data, factors, validation_report):
    """Build multi-factor model for 0700.HK"""
    print("\nBuilding multi-factor model...")

    try:
        from alpha.factor_portfolio.factor_portfolio import FactorPortfolio, FactorModelConfig, ModelType

        if factors is None or factors.empty:
            print("No factor data available")
            return None

        # Create model configuration
        config = FactorModelConfig(
            model_type=ModelType.LINEAR_REGRESSION,
            max_factors=5,
            min_ic_threshold=0.01,
            correlation_threshold=0.7
        )

        portfolio = FactorPortfolio(config)

        # Prepare factor data dictionary
        factor_dict = {}
        for col in factors.columns:
            if len(factors[col].dropna()) > 30:
                factor_dict[col] = factors[[col]]

        # Select best factors
        selected_factors = portfolio.select_factors(factor_dict, criteria="composite_score")
        print(f"SUCCESS: Selected {len(selected_factors)} best factors")

        # Calculate returns
        returns = data['Close'].pct_change()

        # Build multi-factor model
        model = portfolio.build_model(factor_dict, returns)
        print("SUCCESS: Multi-factor model built")

        # Get model performance
        performance = portfolio.get_model_performance()
        print("Model performance:")
        for metric, value in performance.items():
            print(f"  {metric}: {value:.4f}")

        # Get factor importance
        factor_importance = model.get_feature_importance()
        print("\nFactor importance ranking:")
        print(factor_importance.head(10))

        return {
            'model': model,
            'performance': performance,
            'factor_importance': factor_importance,
            'selected_factors': selected_factors
        }

    except Exception as e:
        print(f"FAILED: Multi-factor model building failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def generate_optimization_recommendations(data, factor_analysis, multifactor_model):
    """Generate 0700.HK strategy optimization recommendations"""
    print("\nGenerating 0700.HK optimization recommendations...")

    try:
        # Create optimization report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        recommendations = {
            'timestamp': timestamp,
            'stock': '0700.HK',
            'analysis_period': f"{data.index[0].date()} to {data.index[-1].date()}",
            'data_points': len(data),
            'price_range': {
                'min': float(data['Close'].min()),
                'max': float(data['Close'].max()),
                'current': float(data['Close'].iloc[-1])
            }
        }

        # Factor analysis results
        if factor_analysis is not None and not factor_analysis.empty:
            top_factors = factor_analysis.sort_values('composite_score', ascending=False).head(5)
            recommendations['top_factors'] = [
                {
                    'name': row['factor_name'],
                    'ic_mean': float(row['ic_mean']),
                    'sharpe_ratio': float(row['sharpe_ratio']),
                    'hit_rate': float(row['hit_rate']),
                    'composite_score': float(row['composite_score'])
                }
                for _, row in top_factors.iterrows()
            ]

        # Multi-factor model results
        if multifactor_model is not None:
            recommendations['multifactor_model'] = {
                'performance': multifactor_model['performance'],
                'selected_factors': multifactor_model['selected_factors'],
                'factor_importance': multifactor_model['factor_importance'].to_dict()
            }

        # Generate strategic recommendations
        recommendations['strategic_recommendations'] = generate_strategic_advice(recommendations)

        # Save results
        filename = f"0700_hk_alpha_optimization_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(recommendations, f, indent=2, ensure_ascii=False)

        print(f"SUCCESS: Optimization recommendations saved to {filename}")

        # Display summary
        display_recommendations(recommendations)

        return recommendations

    except Exception as e:
        print(f"FAILED: Recommendation generation failed: {e}")
        return None

def generate_strategic_advice(recommendations):
    """Generate strategic advice based on analysis"""
    advice = []

    # Factor-based advice
    if 'top_factors' in recommendations and recommendations['top_factors']:
        best_factor = recommendations['top_factors'][0]
        if best_factor['sharpe_ratio'] > 1.0:
            advice.append(f"STRONG: {best_factor['name']} shows excellent predictive power (Sharpe: {best_factor['sharpe_ratio']:.3f})")
        elif best_factor['sharpe_ratio'] > 0.5:
            advice.append(f"MODERATE: {best_factor['name']} shows good predictive power (Sharpe: {best_factor['sharpe_ratio']:.3f})")

    # Model performance advice
    if 'multifactor_model' in recommendations:
        r_squared = recommendations['multifactor_model']['performance']['r_squared']
        if r_squared > 0.05:
            advice.append(f"Model explains {r_squared:.1%} of return variance - good predictive power")
        elif r_squared > 0.02:
            advice.append(f"Model explains {r_squared:.1%} of return variance - moderate predictive power")

    # General advice
    advice.extend([
        "CONSIDER: Implement factor-based position sizing based on IC scores",
        "MONITOR: Regular factor validation to maintain effectiveness",
        "RISK: Use stop-losses and position sizing to control downside",
        "DIVERSIFY: Combine alpha factors with other strategies"
    ])

    return advice

def display_recommendations(recommendations):
    """Display optimization recommendations"""
    print("\n" + "=" * 70)
    print("0700.HK Alpha Factor Optimization Results")
    print("=" * 70)

    print(f"\nAnalysis Summary:")
    print(f"  Stock: {recommendations['stock']}")
    print(f"  Period: {recommendations['analysis_period']}")
    print(f"  Data Points: {recommendations['data_points']:,}")
    print(f"  Price Range: ${recommendations['price_range']['min']:.1f} - ${recommendations['price_range']['max']:.1f} HKD")

    if 'top_factors' in recommendations:
        print(f"\nTop Alpha Factors:")
        for i, factor in enumerate(recommendations['top_factors'], 1):
            print(f"  {i}. {factor['name']}")
            print(f"     IC: {factor['ic_mean']:.4f}, Sharpe: {factor['sharpe_ratio']:.3f}, Hit Rate: {factor['hit_rate']:.1%}")

    if 'multifactor_model' in recommendations:
        print(f"\nMulti-Factor Model:")
        perf = recommendations['multifactor_model']['performance']
        print(f"  R-squared: {perf['r_squared']:.1%}")
        print(f"  MSE: {perf['mse']:.6f}")
        print(f"  Selected Factors: {len(recommendations['multifactor_model']['selected_factors'])}")

    print(f"\nStrategic Recommendations:")
    for advice in recommendations['strategic_recommendations']:
        print(f"  - {advice}")

def main():
    """Main function"""
    print("=" * 70)
    print("0700.HK Alpha Factor Optimization")
    print("=" * 70)
    print("Optimizing 0700.HK trading strategies using Alpha Factor System")
    print("=" * 70)

    # 1. Load 0700.HK data
    data = load_0700_data()
    if data is None:
        print("FAILED: Could not load 0700.HK data")
        return

    # 2. Calculate Alpha factors
    factors, engine = calculate_alpha_factors(data)
    if factors is None:
        print("FAILED: Alpha factor calculation failed")
        return

    # 3. Validate factors
    validation_report = validate_factors(data, factors)

    # 4. Build multi-factor model
    multifactor_model = build_multifactor_model(data, factors, validation_report)

    # 5. Generate optimization recommendations
    recommendations = generate_optimization_recommendations(data, validation_report, multifactor_model)

    print("\n" + "=" * 70)
    print("0700.HK Alpha Factor Optimization Complete!")
    print("=" * 70)

if __name__ == '__main__':
    main()
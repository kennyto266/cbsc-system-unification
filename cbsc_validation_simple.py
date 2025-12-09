#!/usr/bin/env python3
"""
CBSC Strategy Validation Report - Simplified Version
Comprehensive validation of CBSC strategy performance results
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

def main():
    print("="*80)
    print("CBSC STRATEGY VALIDATION REPORT")
    print("="*80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Load data for validation
    data_file = "CODEX--/warrant_sentiment_merged.csv"
    results_file = "real_cbsc_backtest_results_20251205_192219.json"

    critical_issues = []
    methodology_issues = []
    data_quality_issues = []

    print(f"\n1. DATA QUALITY ANALYSIS")
    print("-" * 50)

    if Path(data_file).exists():
        try:
            data = pd.read_csv(data_file)
            data['Date'] = pd.to_datetime(data['Date'])
            data = data.dropna(subset=['Afternoon_Close', 'Date'])
            data = data.drop_duplicates(subset=['Date'], keep='last')
            data = data.sort_values('Date')

            print(f"[OK] Loaded {len(data)} records")
            print(f"[OK] Date range: {data['Date'].min().date()} to {data['Date'].max().date()}")

            # Check for duplicates
            duplicates = data.duplicated(subset=['Date']).sum()
            if duplicates > 0:
                critical_issues.append(f"Duplicate dates: {duplicates} records")
                print(f"[ERROR] Duplicate dates: {duplicates}")

            # Check data consistency
            if 'Bull_Ratio' in data.columns:
                invalid_ratios = data[(data['Bull_Ratio'] < 0) | (data['Bull_Ratio'] > 1)]
                if len(invalid_ratios) > 0:
                    critical_issues.append(f"Invalid bull ratios: {len(invalid_ratios)} records")
                    print(f"[ERROR] Invalid bull ratios: {len(invalid_ratios)} records")

        except Exception as e:
            critical_issues.append(f"Data loading failed: {e}")
            print(f"[ERROR] Data loading failed: {e}")
    else:
        critical_issues.append(f"Data file not found: {data_file}")
        print(f"[ERROR] Data file not found: {data_file}")

    print(f"\n2. STRATEGY RESULTS ANALYSIS")
    print("-" * 50)

    if Path(results_file).exists():
        try:
            with open(results_file, 'r') as f:
                strategy_results = json.load(f)

            print(f"[OK] Loaded strategy results")

            # Analyze each strategy
            for strategy_name, results in strategy_results.items():
                if strategy_name == 'market_benchmark':
                    continue

                metrics = results['metrics']
                total_return = metrics['total_return']
                sharpe_ratio = metrics['sharpe_ratio']
                total_trades = metrics['total_trades']
                trading_costs = metrics.get('trading_costs', 0)

                print(f"\n{strategy_name}:")
                print(f"  Total Return: {total_return:.2%}")
                print(f"  Sharpe Ratio: {sharpe_ratio:.3f}")
                print(f"  Total Trades: {total_trades}")
                print(f"  Trading Costs: HKD {trading_costs:,.0f}")

                # Critical issues
                if abs(total_return) > 5.0:  # > 500% return
                    critical_issues.append(f"{strategy_name}: Return > 500% - unrealistic")
                    print(f"  [CRITICAL] Return > 500% - highly suspicious")

                if total_return == 6.313007773100371:
                    critical_issues.append(f"{strategy_name}: Exact return suggests calculation error")
                    print(f"  [CRITICAL] Exact return suggests calculation issue")

                # Methodology issues
                if trading_costs > 0:
                    cost_per_trade = trading_costs / total_trades if total_trades > 0 else 0
                    if cost_per_trade > 1000:
                        methodology_issues.append(f"{strategy_name}: Trading cost HKD {cost_per_trade:.0f}/trade - unrealistic")
                        print(f"  [WARNING] Trading cost HKD {cost_per_trade:.0f}/trade - unrealistic")

                if total_trades > 500:
                    methodology_issues.append(f"{strategy_name}: Excessive trading ({total_trades} trades)")
                    print(f"  [WARNING] Excessive trading ({total_trades} trades)")

                if total_trades < 10 and total_trades > 0:
                    methodology_issues.append(f"{strategy_name}: Very few trades ({total_trades}) - low significance")
                    print(f"  [WARNING] Very few trades ({total_trades})")

                # Statistical issues
                if sharpe_ratio > 3.0:
                    critical_issues.append(f"{strategy_name}: Sharpe ratio > 3 - potentially unrealistic")
                    print(f"  [CRITICAL] Sharpe ratio > 3 - exceptional and rare")

            # Check for identical strategies
            if 'MACD Standard' in strategy_results and 'MACD Sensitive' in strategy_results:
                macd_std = strategy_results['MACD Standard']['metrics']['total_return']
                macd_sens = strategy_results['MACD Sensitive']['metrics']['total_return']
                if macd_std == macd_sens:
                    critical_issues.append("MACD Standard and Sensitive have identical results")
                    print(f"  [CRITICAL] MACD Standard and Sensitive are identical")

        except Exception as e:
            critical_issues.append(f"Results loading failed: {e}")
            print(f"[ERROR] Results loading failed: {e}")
    else:
        critical_issues.append(f"Results file not found: {results_file}")
        print(f"[ERROR] Results file not found: {results_file}")

    print(f"\n3. METHODOLOGY ANALYSIS")
    print("-" * 50)

    print("Trading Cost Analysis:")
    print("  Current assumption: HKD 2,000 per trade")
    print("  Typical retail cost: 0.1-0.3% of trade value")
    print("  For HKD 100,000 position: HKD 100-300 (vs HKD 2,000 assumed)")
    methodology_issues.append("Trading cost assumption is 6-20x higher than realistic")

    print("\nReturn Calculation Issues:")
    if Path(results_file).exists():
        with open(results_file, 'r') as f:
            results = json.load(f)

        for strategy in ['MACD Standard', 'MACD Sensitive']:
            if strategy in results:
                metrics = results[strategy]['metrics']
                if pd.isna(metrics['annual_return']):
                    methodology_issues.append(f"{strategy}: Annual return calculation results in NaN")
                    print(f"  [ERROR] {strategy}: Annual return calculation error")

                total_return = metrics['total_return']
                max_drawdown = metrics['max_drawdown']
                if total_return < -1.9 and max_drawdown == 0.0:
                    methodology_issues.append(f"{strategy}: Drawdown inconsistent with returns")
                    print(f"  [ERROR] {strategy}: -{abs(total_return):.1%} return but 0% drawdown")

    print(f"\n4. PRODUCTION READINESS ASSESSMENT")
    print("-" * 50)

    total_critical = len(critical_issues)
    total_methodology = len(methodology_issues)
    total_data_issues = len(data_quality_issues)

    print(f"Issues Summary:")
    print(f"  Critical Issues: {total_critical}")
    print(f"  Methodology Issues: {total_methodology}")
    print(f"  Data Quality Issues: {total_data_issues}")

    print(f"\nCritical Issues Found:")
    for i, issue in enumerate(critical_issues[:10], 1):  # Show first 10
        print(f"  {i}. {issue}")

    print(f"\nMethodology Issues Found:")
    for i, issue in enumerate(methodology_issues[:10], 1):  # Show first 10
        print(f"  {i}. {issue}")

    # Readiness Assessment
    print(f"\n5. READINESS ASSESSMENT")
    print("-" * 50)

    if total_critical > 10:
        readiness_score = "CRITICAL - NOT READY FOR PRODUCTION"
        risk_level = "EXTREME"
        recommendation = "MAJOR REDESIGN REQUIRED"
    elif total_critical > 5:
        readiness_score = "HIGH RISK - NOT RECOMMENDED"
        risk_level = "HIGH"
        recommendation = "SIGNIFICANT FIXES NEEDED"
    elif total_critical > 2:
        readiness_score = "MODERATE RISK - FIXES REQUIRED"
        risk_level = "MODERATE"
        recommendation = "THOROUGH VALIDATION NEEDED"
    elif total_critical > 0:
        readiness_score = "LOW RISK - MINOR FIXES"
        risk_level = "LOW"
        recommendation = "LIMITED DEPLOYMENT POSSIBLE"
    else:
        readiness_score = "ACCEPTABLE - READY FOR TESTING"
        risk_level = "MINIMAL"
        recommendation = "PROCEED WITH CAUTION"

    print(f"Readiness Score: {readiness_score}")
    print(f"Risk Level: {risk_level}")
    print(f"Recommendation: {recommendation}")

    print(f"\nImmediate Actions Required:")
    print(f"1. Fix trading cost model (currently unrealistic)")
    print(f"2. Resolve calculation inconsistencies")
    print(f"3. Add proper slippage and market impact modeling")
    print(f"4. Implement realistic position sizing")
    print(f"5. Conduct out-of-sample validation")
    print(f"6. Add proper risk management constraints")

    # Save validation report
    report_data = {
        'validation_timestamp': datetime.now().isoformat(),
        'summary': {
            'critical_issues': total_critical,
            'methodology_issues': total_methodology,
            'data_quality_issues': total_data_issues,
            'readiness_score': readiness_score,
            'risk_level': risk_level
        },
        'critical_issues': critical_issues,
        'methodology_issues': methodology_issues,
        'data_quality_issues': data_quality_issues
    }

    report_file = f"cbsc_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2)

    print(f"\nDetailed report saved to: {report_file}")

    return report_data

if __name__ == "__main__":
    main()
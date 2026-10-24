#!/usr/bin/env python3
"""
API Historical Limits Verification
Verify API historical data limits for 5+ year backtesting feasibility
"""

import sys
import requests
import pandas as pd
from datetime import datetime, timedelta
import json
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from hkma_data_adapter import HKMADataAdapter
    HKMA_AVAILABLE = True
except ImportError:
    HKMA_AVAILABLE = False
    print("Warning: HKMA adapter not available")

class APILimitsVerifier:
    """API Historical Limits Verification Tool"""

    def __init__(self):
        self.results = {}
        if HKMA_AVAILABLE:
            self.hkma_adapter = HKMADataAdapter()

    def test_hkma_hibor_limits(self):
        """Test HKMA HIBOR data availability for different periods"""
        print("Testing HKMA HIBOR Data Availability...")
        print("=" * 50)

        hibor_results = {}
        test_years = [5, 7, 10]

        for years in test_years:
            print(f"Testing {years} years of HIBOR data...")

            try:
                start_date = datetime.now() - timedelta(days=years*365)
                end_date = datetime.now() - timedelta(days=1)

                start_time = time.time()
                hibor_data = self.hkma_adapter.get_hibor_data(start_date, end_date)
                end_time = time.time()

                if hibor_data is not None and len(hibor_data) > 0:
                    data_points = len(hibor_data)
                    date_range = (hibor_data.index.max() - hibor_data.index.min()).days
                    completeness = self._calculate_data_completeness(hibor_data, start_date, end_date)

                    hibor_results[years] = {
                        'success': True,
                        'data_points': data_points,
                        'date_range_days': date_range,
                        'completeness_percentage': completeness * 100,
                        'fetch_time_seconds': end_time - start_time,
                        'tenors_available': hibor_data['tenor'].nunique() if 'tenor' in hibor_data.columns else 0,
                        'start_date_actual': str(hibor_data.index.min().date()),
                        'end_date_actual': str(hibor_data.index.max().date())
                    }

                    print(f"  SUCCESS: {data_points} records, {date_range} days, {completeness:.1%} complete")
                else:
                    hibor_results[years] = {
                        'success': False,
                        'error': 'No data returned',
                        'data_points': 0
                    }
                    print(f"  FAILED: No data returned")

            except Exception as e:
                hibor_results[years] = {
                    'success': False,
                    'error': str(e),
                    'data_points': 0
                }
                print(f"  ERROR: {e}")

        self.results['hkma_hibor'] = hibor_results
        return hibor_results

    def test_central_api_limits(self):
        """Test Central API stock data availability"""
        print("\nTesting Central API Stock Data Availability...")
        print("=" * 50)

        api_results = {}
        test_symbols = ['0700.hk', '0941.hk', '1398.hk']  # Tencent, China Mobile, ICBC
        test_years = [5, 7, 10]

        for symbol in test_symbols:
            print(f"\nTesting {symbol}...")
            symbol_results = {}

            for years in test_years:
                print(f"  {years} years...", end=" ")

                try:
                    url = "http://18.180.162.113:9191/inst/getInst"
                    params = {
                        "symbol": symbol.lower(),
                        "duration": int(years * 365)
                    }

                    start_time = time.time()
                    response = requests.get(url, params=params, timeout=30)
                    end_time = time.time()

                    if response.status_code == 200:
                        data = response.json()

                        if isinstance(data, dict) and 'data' in data:
                            data_points = len(data['data'])
                        elif isinstance(data, list):
                            data_points = len(data)
                        else:
                            data_points = 1 if data else 0

                        symbol_results[years] = {
                            'success': True,
                            'data_points': data_points,
                            'fetch_time_seconds': end_time - start_time,
                            'status_code': response.status_code,
                            'response_type': type(data).__name__
                        }

                        print(f"SUCCESS: {data_points} points")
                    else:
                        symbol_results[years] = {
                            'success': False,
                            'status_code': response.status_code,
                            'data_points': 0
                        }
                        print(f"FAILED: HTTP {response.status_code}")

                except Exception as e:
                    symbol_results[years] = {
                        'success': False,
                        'error': str(e),
                        'data_points': 0
                    }
                    print(f"ERROR: {e}")

            api_results[symbol] = symbol_results

        self.results['central_api'] = api_results
        return api_results

    def test_alternative_sources(self):
        """Test alternative data sources"""
        print("\nTesting Alternative Data Sources...")
        print("=" * 50)

        alt_sources = {}

        # Test Yahoo Finance availability
        print("Testing Yahoo Finance...")
        try:
            import yfinance as yf
            symbol = '0700.HK'
            start_date = datetime.now() - timedelta(days=5*365)

            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start_date)

            if len(hist) > 0:
                alt_sources['yahoo_finance'] = {
                    'success': True,
                    'data_points': len(hist),
                    'date_range_days': (hist.index.max() - hist.index.min()).days,
                    'start_date': str(hist.index.min().date()),
                    'end_date': str(hist.index.max().date())
                }
                print(f"  SUCCESS: {len(hist)} records available")
            else:
                alt_sources['yahoo_finance'] = {
                    'success': False,
                    'error': 'No data returned'
                }
                print(f"  FAILED: No data returned")

        except ImportError:
            alt_sources['yahoo_finance'] = {
                'success': False,
                'error': 'yfinance library not available'
            }
            print(f"  FAILED: yfinance library not available")
        except Exception as e:
            alt_sources['yahoo_finance'] = {
                'success': False,
                'error': str(e)
            }
            print(f"  ERROR: {e}")

        # Test local cache
        print("Testing local cache...")
        cache_dir = Path("C:/Users/Penguin8n/CODEX--/data/cache")
        if cache_dir.exists():
            hsi_file = cache_dir / "hsi_constituents_82.json"
            if hsi_file.exists():
                alt_sources['local_cache'] = {
                    'success': True,
                    'file_path': str(hsi_file),
                    'file_size_bytes': hsi_file.stat().st_size
                }
                print(f"  SUCCESS: HSI constituents data found")
            else:
                alt_sources['local_cache'] = {
                    'success': False,
                    'error': 'No cached data files found'
                }
                print(f"  FAILED: No cached data files found")
        else:
            alt_sources['local_cache'] = {
                'success': False,
                'error': 'Cache directory not found'
            }
            print(f"  FAILED: Cache directory not found")

        self.results['alternative_sources'] = alt_sources
        return alt_sources

    def _calculate_data_completeness(self, data, start_date, end_date):
        """Calculate data completeness as percentage of expected trading days"""
        try:
            expected_dates = pd.date_range(start=start_date, end=end_date, freq='D')
            expected_weekdays = expected_dates[expected_dates.weekday < 5]  # Weekdays only

            if hasattr(data.index, 'normalize'):
                actual_dates = data.index.normalize()
            else:
                actual_dates = data.index

            actual_weekdays = actual_dates[actual_dates.weekday < 5]

            if len(expected_weekdays) == 0:
                return 1.0

            return len(actual_weekdays) / len(expected_weekdays)
        except:
            return 0.0

    def generate_report(self):
        """Generate comprehensive verification report"""
        print("\n" + "=" * 60)
        print("API HISTORICAL LIMITS VERIFICATION REPORT")
        print("=" * 60)

        # HKMA HIBOR Results
        if 'hkma_hibor' in self.results:
            print("\nHKMA HIBOR Data:")
            print("-" * 20)
            hibor_results = self.results['hkma_hibor']

            successful_years = [year for year, result in hibor_results.items() if result.get('success', False)]

            if successful_years:
                print(f"Available periods: {sorted(successful_years)} years")
                print("Data quality: EXCELLENT" if len(successful_years) >= 3 else "LIMITED")

                for year, result in hibor_results.items():
                    if result.get('success', False):
                        print(f"  {year} years: {result['data_points']} records, "
                              f"{result['completeness_percentage']:.1f}% complete")
            else:
                print("No HIBOR data available")

        # Central API Results
        if 'central_api' in self.results:
            print("\nCentral Stock API Data:")
            print("-" * 25)
            api_results = self.results['central_api']

            for symbol, symbol_results in api_results.items():
                successful_years = [year for year, result in symbol_results.items() if result.get('success', False)]
                total_points = sum(result.get('data_points', 0) for result in symbol_results.values() if result.get('success', False))

                print(f"{symbol}: {len(successful_years)}/3 years available, {total_points} total records")

        # Alternative Sources
        if 'alternative_sources' in self.results:
            print("\nAlternative Data Sources:")
            print("-" * 30)
            alt_results = self.results['alternative_sources']

            for source, result in alt_results.items():
                status = "AVAILABLE" if result.get('success', False) else "UNAVAILABLE"
                print(f"{source}: {status}")

        # Overall Assessment
        print("\nOVERALL ASSESSMENT:")
        print("-" * 20)

        has_hkma = any(result.get('success', False) for result in self.results.get('hkma_hibor', {}).values())
        has_central = any(any(result.get('success', False) for result in symbol_results.values())
                         for symbol_results in self.results.get('central_api', {}).values())
        has_alternatives = any(result.get('success', False) for result in self.results.get('alternative_sources', {}).values())

        if has_hkma and (has_central or has_alternatives):
            print("STATUS: FEASIBLE for 5+ year backtesting")
            print("RECOMMENDATION: Proceed with implementation")
            print("\nNext steps:")
            print("1. Implement multi-source data integration")
            print("2. Set up data quality monitoring")
            print("3. Optimize storage for long-term data")
        else:
            print("STATUS: LIMITED - need enhancement")
            print("RECOMMENDATION: Strengthen data acquisition")
            print("\nRequired actions:")
            print("1. Integrate additional data sources")
            print("2. Implement data caching strategy")
            print("3. Consider commercial data providers")

        print("\n" + "=" * 60)

    def save_results(self, filename="api_limits_verification_results.json"):
        """Save verification results to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2, default=str)
            print(f"Results saved to: {filename}")
        except Exception as e:
            print(f"Failed to save results: {e}")

def main():
    """Main verification function"""
    print("API HISTORICAL LIMITS VERIFICATION")
    print("For 5+ Year Backtesting Feasibility")
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    verifier = APILimitsVerifier()

    # Run all tests
    if HKMA_AVAILABLE:
        verifier.test_hkma_hibor_limits()
    else:
        print("\nHKMA adapter not available - skipping HIBOR tests")

    verifier.test_central_api_limits()
    verifier.test_alternative_sources()

    # Generate report
    verifier.generate_report()

    # Save results
    verifier.save_results()

    print("\nVerification completed!")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
多资产数据适配器测试 - Multi-Asset Adapter Test
测试外汇、商品、加密货币数据获取功能
"""

import sys
import os
import asyncio
import time
import logging
from datetime import datetime, timedelta
import pandas as pd

# Add to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.multi_asset.multi_asset_adapter import (
    MultiAssetDataAdapter, ForexAdapter, CryptoAdapter, CommodityAdapter
)
from src.multi_asset.asset_models import AssetClass, Timeframe, parse_symbol

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiAssetTester:
    """多资产测试类"""

    def __init__(self):
        self.adapter = MultiAssetDataAdapter()
        self.test_results = {}

    async def test_basic_functionality(self):
        """测试基本功能"""
        print("=" * 60)
        print("Multi-Asset Adapter Basic Functionality Test")
        print("=" * 60)

        try:
            # Initialize adapter
            await self.adapter.initialize()
            print("[OK] Multi-asset adapter initialized successfully")

            # Test symbol parsing
            test_symbols = ["EURUSD", "BTCUSD", "XAUUSD", "0700.HK", "AAPL"]
            for symbol in test_symbols:
                parsed = parse_symbol(symbol)
                print(f"[OK] {symbol} -> {parsed['asset_class'].value}")

            self.test_results["basic_functionality"] = True
            return True

        except Exception as e:
            print(f"[FAIL] Basic functionality test failed: {e}")
            self.test_results["basic_functionality"] = False
            return False

    async def test_forex_data(self):
        """测试外汇数据获取"""
        print("\n" + "=" * 60)
        print("Forex Data Test")
        print("=" * 60)

        try:
            symbols = ["EURUSD", "GBPUSD", "USDJPY"]
            forex_data = {}

            for symbol in symbols:
                print(f"\nTesting {symbol}...")
                start_time = time.time()

                data = await self.adapter.get_market_data(
                    symbol=symbol,
                    timeframe=Timeframe.TICK_1H,
                    limit=50
                )

                execution_time = time.time() - start_time
                forex_data[symbol] = data

                if data:
                    print(f"[OK] {symbol}: Retrieved {len(data)} records in {execution_time:.3f}s")
                    latest = data[-1]
                    print(f"  Latest price: {latest.close:.5f}")
                    print(f"  Volume: {latest.volume:,.0f}")
                    print(f"  Time range: {data[0].timestamp} to {data[-1].timestamp}")
                else:
                    print(f"[FAIL] {symbol}: No data retrieved")

            # Test batch retrieval
            print(f"\nTesting batch forex data retrieval...")
            start_time = time.time()
            batch_data = await self.adapter.get_multiple_market_data(
                symbols=symbols,
                timeframe=Timeframe.TICK_1H,
                limit=50
            )
            execution_time = time.time() - start_time

            success_rate = len([d for d in batch_data.values() if d]) / len(symbols)
            print(f"[OK] Batch retrieval: {success_rate:.1%} success rate in {execution_time:.3f}s")

            self.test_results["forex_data"] = success_rate > 0.5
            return success_rate > 0.5

        except Exception as e:
            print(f"[FAIL] Forex data test failed: {e}")
            self.test_results["forex_data"] = False
            return False

    async def test_crypto_data(self):
        """测试加密货币数据获取"""
        print("\n" + "=" * 60)
        print("Crypto Data Test")
        print("=" * 60)

        try:
            symbols = ["BTCUSD", "ETHUSD", "BNBUSDT"]
            crypto_data = {}

            for symbol in symbols:
                print(f"\nTesting {symbol}...")
                start_time = time.time()

                data = await self.adapter.get_market_data(
                    symbol=symbol,
                    timeframe=Timeframe.TICK_1H,
                    limit=100
                )

                execution_time = time.time() - start_time
                crypto_data[symbol] = data

                if data:
                    print(f"[OK] {symbol}: Retrieved {len(data)} records in {execution_time:.3f}s")
                    latest = data[-1]
                    print(f"  Latest price: ${latest.close:,.2f}")
                    print(f"  24h Volume: {latest.volume:,.0f}")
                    print(f"  Time range: {data[0].timestamp} to {data[-1].timestamp}")
                else:
                    print(f"[FAIL] {symbol}: No data retrieved")

            # Test DataFrame conversion
            print(f"\nTesting DataFrame conversion...")
            for symbol, data in crypto_data.items():
                if data:
                    df = self.adapter.to_dataframe(data)
                    print(f"[OK] {symbol} DataFrame: {df.shape}, columns: {list(df.columns)}")
                    break

            success_rate = len([d for d in crypto_data.values() if d]) / len(symbols)
            self.test_results["crypto_data"] = success_rate > 0.5
            return success_rate > 0.5

        except Exception as e:
            print(f"[FAIL] Crypto data test failed: {e}")
            self.test_results["crypto_data"] = False
            return False

    async def test_commodity_data(self):
        """测试商品数据获取"""
        print("\n" + "=" * 60)
        print("Commodity Data Test")
        print("=" * 60)

        try:
            symbols = ["XAUUSD", "XAGUSD", "CLUSD"]  # Gold, Silver, Crude Oil
            commodity_data = {}

            for symbol in symbols:
                print(f"\nTesting {symbol}...")
                start_time = time.time()

                data = await self.adapter.get_market_data(
                    symbol=symbol,
                    timeframe=Timeframe.TICK_1D,
                    limit=30  # Daily data for commodities
                )

                execution_time = time.time() - start_time
                commodity_data[symbol] = data

                if data:
                    print(f"[OK] {symbol}: Retrieved {len(data)} records in {execution_time:.3f}s")
                    latest = data[-1]
                    commodity_name = {
                        "XAUUSD": "Gold",
                        "XAGUSD": "Silver",
                        "CLUSD": "Crude Oil"
                    }.get(symbol, symbol)
                    print(f"  {commodity_name} price: ${latest.close:.2f}")
                    print(f"  Volume: {latest.volume:,.0f}")
                    print(f"  Time range: {data[0].timestamp} to {data[-1].timestamp}")
                else:
                    print(f"[FAIL] {symbol}: No data retrieved")

            success_rate = len([d for d in commodity_data.values() if d]) / len(symbols)
            self.test_results["commodity_data"] = success_rate > 0.3  # Lower threshold for commodities
            return success_rate > 0.3

        except Exception as e:
            print(f"[FAIL] Commodity data test failed: {e}")
            self.test_results["commodity_data"] = False
            return False

    async def test_performance_benchmark(self):
        """性能基准测试"""
        print("\n" + "=" * 60)
        print("Performance Benchmark Test")
        print("=" * 60)

        try:
            # Test batch retrieval performance
            test_symbols = ["EURUSD", "BTCUSD", "XAUUSD"]
            batch_sizes = [1, 3, 5, 10]

            performance_results = {}

            for batch_size in batch_sizes:
                symbols = test_symbols * (batch_size // len(test_symbols) + 1)
                symbols = symbols[:batch_size]

                print(f"\nTesting batch size: {batch_size}")
                start_time = time.time()

                data = await self.adapter.get_multiple_market_data(
                    symbols=symbols,
                    timeframe=Timeframe.TICK_1H,
                    limit=50
                )

                execution_time = time.time() - start_time
                success_count = len([d for d in data.values() if d])
                success_rate = success_count / len(symbols)
                throughput = batch_size / execution_time

                performance_results[batch_size] = {
                    "execution_time": execution_time,
                    "success_rate": success_rate,
                    "throughput": throughput
                }

                print(f"  Execution time: {execution_time:.3f}s")
                print(f"  Success rate: {success_rate:.1%}")
                print(f"  Throughput: {throughput:.1f} symbols/sec")

            # Performance target: 5+ symbols/sec
            best_throughput = max(r["throughput"] for r in performance_results.values())
            performance_target_met = best_throughput >= 5

            print(f"\n[OK] Best throughput: {best_throughput:.1f} symbols/sec")
            print(f"[OK] Performance target met (5+ symbols/sec): {performance_target_met}")

            self.test_results["performance_benchmark"] = performance_target_met
            return performance_target_met

        except Exception as e:
            print(f"[FAIL] Performance benchmark failed: {e}")
            self.test_results["performance_benchmark"] = False
            return False

    async def test_cache_functionality(self):
        """测试缓存功能"""
        print("\n" + "=" * 60)
        print("Cache Functionality Test")
        print("=" * 60)

        try:
            symbol = "EURUSD"
            timeframe = Timeframe.TICK_1H
            limit = 50

            # First request (should fetch from API)
            print("First request (fetching from API)...")
            start_time = time.time()
            data1 = await self.adapter.get_market_data(symbol, timeframe, limit, use_cache=True)
            first_request_time = time.time() - start_time

            # Second request (should use cache)
            print("Second request (using cache)...")
            start_time = time.time()
            data2 = await self.adapter.get_market_data(symbol, timeframe, limit, use_cache=True)
            second_request_time = time.time() - start_time

            # Verify cache effectiveness
            cache_working = (
                len(data1) == len(data2) and
                len(data1) > 0 and
                second_request_time < first_request_time * 0.5  # At least 2x faster
            )

            print(f"[OK] First request: {first_request_time:.3f}s, {len(data1)} records")
            print(f"[OK] Second request: {second_request_time:.3f}s, {len(data2)} records")
            print(f"[OK] Cache speedup: {first_request_time/second_request_time:.1f}x")
            print(f"[OK] Cache working: {cache_working}")

            # Test cache clearing
            self.adapter.clear_cache()
            print("[OK] Cache cleared")

            self.test_results["cache_functionality"] = cache_working
            return cache_working

        except Exception as e:
            print(f"[FAIL] Cache functionality test failed: {e}")
            self.test_results["cache_functionality"] = False
            return False

    async def test_data_quality(self):
        """测试数据质量"""
        print("\n" + "=" * 60)
        print("Data Quality Test")
        print("=" * 60)

        try:
            # Get sample data
            symbols = ["EURUSD", "BTCUSD", "XAUUSD"]
            quality_issues = {}

            for symbol in symbols:
                print(f"\nTesting data quality for {symbol}...")
                data = await self.adapter.get_market_data(symbol, limit=100)

                if not data:
                    quality_issues[symbol] = "No data retrieved"
                    continue

                issues = []

                # Check data consistency
                for i, record in enumerate(data):
                    # OHLC consistency
                    if not (record.low <= record.open <= record.high):
                        issues.append(f"Record {i}: Open not within High-Low range")
                    if not (record.low <= record.close <= record.high):
                        issues.append(f"Record {i}: Close not within High-Low range")

                    # Price positivity
                    if any(x <= 0 for x in [record.open, record.high, record.low, record.close]):
                        issues.append(f"Record {i}: Non-positive price")

                    # Volume non-negativity
                    if record.volume < 0:
                        issues.append(f"Record {i}: Negative volume")

                    # Chronological order
                    if i > 0 and record.timestamp <= data[i-1].timestamp:
                        issues.append(f"Record {i}: Timestamp not in chronological order")

                # Check for gaps
                for i in range(1, len(data)):
                    time_diff = data[i].timestamp - data[i-1].timestamp
                    expected_diff = timedelta(hours=1)  # 1-hour data
                    if time_diff > expected_diff * 1.5:
                        issues.append(f"Gap between records {i-1} and {i}")

                quality_issues[symbol] = issues
                if issues:
                    print(f"[WARNING] {symbol}: {len(issues)} quality issues found")
                    for issue in issues[:3]:  # Show first 3 issues
                        print(f"  - {issue}")
                    if len(issues) > 3:
                        print(f"  - ... and {len(issues) - 3} more issues")
                else:
                    print(f"[OK] {symbol}: No quality issues detected")

            # Overall quality assessment
            total_issues = sum(len(issues) for issues in quality_issues.values())
            data_quality_good = total_issues < 10  # Allow for minor issues

            print(f"\n[OK] Total quality issues: {total_issues}")
            print(f"[OK] Data quality acceptable: {data_quality_good}")

            self.test_results["data_quality"] = data_quality_good
            return data_quality_good

        except Exception as e:
            print(f"[FAIL] Data quality test failed: {e}")
            self.test_results["data_quality"] = False
            return False

    def print_test_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 60)
        print("Multi-Asset Adapter Test Summary")
        print("=" * 60)

        total_tests = len(self.test_results)
        passed_tests = len([result for result in self.test_results.values() if result])
        failed_tests = total_tests - passed_tests

        print(f"Total tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success rate: {passed_tests/total_tests:.1%}")

        print("\nTest Details:")
        for test_name, result in self.test_results.items():
            status = "[OK]" if result else "[FAIL]"
            print(f"  {status} {test_name}")

        # Overall assessment
        success_rate = passed_tests / total_tests
        if success_rate >= 0.8:
            print(f"\n[SUCCESS] Multi-asset adapter is production ready!")
            print("System successfully handles forex, crypto, and commodity data.")
        elif success_rate >= 0.6:
            print(f"\n[PARTIAL SUCCESS] Multi-asset adapter mostly functional.")
            print("Some minor issues detected but core functionality works.")
        else:
            print(f"\n[NEEDS IMPROVEMENT] Multi-asset adapter requires fixes.")
            print("Significant issues detected that need to be addressed.")

        return success_rate >= 0.6

async def main():
    """主测试函数"""
    print("Multi-Asset Data Adapter Comprehensive Test")
    print("=" * 60)
    print("Testing forex, crypto, and commodity data acquisition...")
    print()

    tester = MultiAssetTester()

    try:
        # Run all tests
        test_functions = [
            tester.test_basic_functionality,
            tester.test_forex_data,
            tester.test_crypto_data,
            tester.test_commodity_data,
            tester.test_performance_benchmark,
            tester.test_cache_functionality,
            tester.test_data_quality
        ]

        for test_func in test_functions:
            try:
                await test_func()
            except Exception as e:
                logger.error(f"Test {test_func.__name__} failed with exception: {e}")
                # Continue with other tests even if one fails

        # Print summary
        success_rate = tester.print_test_summary()

        return success_rate

    except Exception as e:
        print(f"\n[CRITICAL ERROR] Test suite failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit_code = 0 if success else 1
    sys.exit(exit_code)
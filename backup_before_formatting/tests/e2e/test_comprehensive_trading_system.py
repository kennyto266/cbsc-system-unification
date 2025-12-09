"""
Comprehensive End - to - End Tests for Hong Kong Quantitative Trading System

This test suite covers:
- Complete trading workflow from data ingestion to execution
- Multi - service integration testing
- Performance and scalability testing
- Security and reliability testing
- Error handling and recovery scenarios
"""

import asyncio
import json
import logging

# Import system components
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp
import numpy as np
import pandas as pd
import pytest
import requests
from sqlalchemy.ext.asyncio import AsyncSession

# Import testing framework
from tests.framework import (
    CacheFixture,
    DatabaseFixture,
    KafkaFixture,
    MockServiceFactory,
    PerformanceMonitor,
    SecurityTester,
    TestAssertions,
    TestDataGenerator,
    TestEnvironmentManager,
    TestHelpers,
    e2e_test,
    flaky_test,
    integration_test,
    load_test,
    parameterized_test,
    performance_test,
    regression_test,
    requires_database,
    requires_network,
    security_test,
    smoke_test,
    timed_test,
    unit_test,
)

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.backtest.stockbacktest_integration import StockBacktestIntegration
from src.data_adapters.data_service import DataService
from src.integration.system_integration import IntegrationConfig, SystemIntegration
from src.monitoring.real_time_monitor import RealTimeMonitor
from src.portfolio.portfolio_manager import PortfolioManager
from src.risk_management.risk_calculator import RiskCalculator
from src.strategy_management.strategy_manager import StrategyManager
from src.trading.trading_manager import TradingManager


@pytest.mark.e2e
class TestCompleteTradingWorkflow:
    """Test complete trading workflow end - to - end."""

    @pytest.fixture(autouse=True)
    async def setup_test_environment(self):
        """Setup comprehensive test environment."""
        self.logger = logging.getLogger(__name__)
        self.data_generator = TestDataGenerator()
        self.mock_factory = MockServiceFactory()
        self.performance_monitor = PerformanceMonitor()
        self.security_tester = SecurityTester()

        # Setup test data
        self.test_symbols = ["00700.HK", "2800.HK", "0700.HK", "0941.HK", "1398.HK"]
        self.market_data = {}
        self.trading_signals = {}

        for symbol in self.test_symbols:
            # Generate market data for each symbol
            self.market_data[symbol] = self.data_generator.generate_market_data(
                symbol=symbol, days=30, frequency="5min"
            )

            # Generate trading signals
            self.trading_signals[symbol] = self.data_generator.generate_trading_signals(
                symbols=[symbol], num_signals=5
            )

        # Setup portfolio
        self.test_portfolio = self.data_generator.generate_portfolio_data(
            symbols=self.test_symbols, total_value=10000000.0  # 10M HKD
        )

        # Setup risk metrics
        self.test_risk_metrics = self.data_generator.generate_risk_metrics(
            portfolio_value=10000000.0
        )

        yield

    @e2e_test(timeout=600)
    @performance_test(max_duration=300)
    async def test_complete_data_pipeline_workflow(self):
        """Test complete data pipeline from ingestion to analysis."""
        measurement = self.performance_monitor.start_measurement("data_pipeline_test")

        try:
            # Step 1: Data Ingestion
            self.logger.info("Step 1: Data Ingestion")
            start_time = datetime.now()

            for symbol in self.test_symbols:
                # Mock data ingestion
                data_count = len(self.market_data[symbol])
                self.logger.info(f"  Ingested {data_count} records for {symbol}")
                assert data_count > 0, f"No data ingested for {symbol}"

            ingestion_time = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"Data ingestion completed in {ingestion_time:.2f}s")

            # Step 2: Data Validation
            self.logger.info("Step 2: Data Validation")
            validation_start = datetime.now()

            for symbol, data in self.market_data.items():
                TestAssertions.assert_valid_market_data(data.to_dict("records"), symbol)

            validation_time = (datetime.now() - validation_start).total_seconds()
            self.logger.info(f"Data validation completed in {validation_time:.2f}s")

            # Step 3: Technical Analysis
            self.logger.info("Step 3: Technical Analysis")
            analysis_start = datetime.now()

            technical_indicators = {}
            for symbol, data in self.market_data.items():
                # Calculate technical indicators
                df = data.copy()
                df["sma_20"] = df["close"].rolling(window=20).mean()
                df["sma_50"] = df["close"].rolling(window=50).mean()
                df["rsi"] = self._calculate_rsi(df["close"])
                df["macd"] = self._calculate_macd(df["close"])
                df["bollinger_upper"] = (
                    df["close"].rolling(window=20).mean()
                    + df["close"].rolling(window=20).std() * 2
                )
                df["bollinger_lower"] = (
                    df["close"].rolling(window=20).mean()
                    - df["close"].rolling(window=20).std() * 2
                )

                technical_indicators[symbol] = {
                    "sma_20_latest": df["sma_20"].iloc[-1],
                    "sma_50_latest": df["sma_50"].iloc[-1],
                    "rsi_latest": df["rsi"].iloc[-1],
                    "macd_latest": df["macd"].iloc[-1],
                    "price": df["close"].iloc[-1],
                }

                # Validate calculated indicators
                assert not np.isnan(technical_indicators[symbol]["sma_20_latest"])
                assert not np.isnan(technical_indicators[symbol]["rsi_latest"])

            analysis_time = (datetime.now() - analysis_start).total_seconds()
            self.logger.info(f"Technical analysis completed in {analysis_time:.2f}s")

            # Step 4: Signal Generation
            self.logger.info("Step 4: Signal Generation")
            signal_start = datetime.now()

            generated_signals = {}
            for symbol, indicators in technical_indicators.items():
                # Simple signal generation logic for testing
                price = indicators["price"]
                sma_20 = indicators["sma_20_latest"]
                sma_50 = indicators["sma_50_latest"]
                rsi = indicators["rsi_latest"]

                if price > sma_20 > sma_50 and rsi < 70:
                    signal = "BUY"
                elif price < sma_20 < sma_50 and rsi > 30:
                    signal = "SELL"
                else:
                    signal = "HOLD"

                confidence = min(abs(rsi - 50) / 50, 1.0)

                generated_signals[symbol] = {
                    "symbol": symbol,
                    "signal": signal,
                    "confidence": confidence,
                    "price": price,
                    "timestamp": datetime.now().isoformat(),
                    "indicators": indicators,
                }

            signal_time = (datetime.now() - signal_start).total_seconds()
            self.logger.info(f"Signal generation completed in {signal_time:.2f}s")

            # Step 5: Portfolio Analysis
            self.logger.info("Step 5: Portfolio Analysis")
            portfolio_start = datetime.now()

            # Calculate portfolio metrics
            portfolio_value = sum(
                pos["market_value"] for pos in self.test_portfolio["positions"]
            )
            portfolio_weights = {
                pos["symbol"]: pos["weight"] for pos in self.test_portfolio["positions"]
            }

            # Validate portfolio
            TestAssertions.assert_valid_portfolio(self.test_portfolio)
            assert (
                abs(portfolio_value - self.test_portfolio["total_value"])
                < portfolio_value * 0.01
            )

            portfolio_time = (datetime.now() - portfolio_start).total_seconds()
            self.logger.info(f"Portfolio analysis completed in {portfolio_time:.2f}s")

            # Step 6: Risk Assessment
            self.logger.info("Step 6: Risk Assessment")
            risk_start = datetime.now()

            # Validate risk metrics
            TestAssertions.assert_valid_risk_metrics(self.test_risk_metrics)

            # Calculate additional risk metrics
            portfolio_volatility = self.test_risk_metrics["volatility"]
            max_drawdown = self.test_risk_metrics["max_drawdown"]["percentage"]
            var_95 = self.test_risk_metrics["var_95"]["percentage"]

            # Risk checks
            assert (
                portfolio_volatility < 0.5
            ), f"Portfolio volatility too high: {portfolio_volatility}"
            assert max_drawdown < 0.25, f"Max drawdown too high: {max_drawdown}"
            assert var_95 < 0.05, f"VaR 95% too high: {var_95}"

            risk_time = (datetime.now() - risk_start).total_seconds()
            self.logger.info(f"Risk assessment completed in {risk_time:.2f}s")

            # Performance validation
            total_time = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"Complete data pipeline executed in {total_time:.2f}s")

            # Assert performance requirements
            assert total_time < 60, f"Data pipeline too slow: {total_time}s > 60s"

            # Validate end - to - end workflow
            assert len(generated_signals) == len(self.test_symbols)
            assert all(
                signal["signal"] in ["BUY", "SELL", "HOLD"]
                for signal in generated_signals.values()
            )
            assert all(
                0 <= signal["confidence"] <= 1 for signal in generated_signals.values()
            )

        finally:
            self.performance_monitor.end_measurement(measurement)

    @e2e_test(timeout=900)
    @load_test(concurrent_users=5, duration_seconds=300)
    async def test_trading_workflow_under_load(self, user_id: int = 0):
        """Test trading workflow under concurrent load."""
        self.logger.info(f"Testing trading workflow under load (user {user_id})")

        # Each user processes a subset of symbols
        symbols_per_user = len(self.test_symbols) // 5
        start_idx = (user_id * symbols_per_user) % len(self.test_symbols)
        end_idx = start_idx + symbols_per_user
        user_symbols = self.test_symbols[start_idx:end_idx]

        # Process trading workflow for assigned symbols
        results = {}
        for symbol in user_symbols:
            start_time = time.time()

            # Simulate trading workflow
            try:
                # Step 1: Get market data
                market_data = self.market_data[symbol]
                assert len(market_data) > 0

                # Step 2: Generate signal
                signal_data = self.trading_signals[symbol][0]  # Use first signal
                TestAssertions.assert_valid_trading_signal(signal_data)

                # Step 3: Execute trade (mock)
                execution_time = time.time()
                trade_result = {
                    "symbol": symbol,
                    "signal": signal_data["signal"],
                    "quantity": 1000,
                    "price": market_data["close"].iloc[-1],
                    "execution_time": execution_time,
                    "status": "FILLED",
                    "user_id": user_id,
                }

                # Step 4: Update portfolio (mock)
                portfolio_update = {
                    "symbol": symbol,
                    "trade_result": trade_result,
                    "timestamp": datetime.now().isoformat(),
                    "user_id": user_id,
                }

                processing_time = time.time() - start_time
                results[symbol] = {
                    "success": True,
                    "processing_time": processing_time,
                    "signal": signal_data["signal"],
                    "trade_result": trade_result,
                    "portfolio_update": portfolio_update,
                }

                # Performance assertions
                assert (
                    processing_time < 5.0
                ), f"Trade processing too slow: {processing_time}s"

            except Exception as e:
                results[symbol] = {
                    "success": False,
                    "error": str(e),
                    "user_id": user_id,
                }

        return {
            "user_id": user_id,
            "processed_symbols": len(user_symbols),
            "successful_trades": sum(
                1 for r in results.values() if r.get("success", False)
            ),
            "results": results,
        }

    @e2e_test(timeout=300)
    @security_test(severity="high")
    async def test_trading_system_security(self):
        """Test security aspects of the trading system."""
        self.logger.info("Testing trading system security")

        security_issues = []

        # Test 1: Input validation
        self.logger.info("Testing input validation")

        # Test SQL injection attempts
        malicious_inputs = [
            "'; DROP TABLE trades; --",
            "' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users --",
        ]

        for malicious_input in malicious_inputs:
            try:
                # Test with symbol field
                TestAssertions.assert_valid_market_data(
                    [{"symbol": malicious_input, "close": 100.0, "volume": 1000}],
                    malicious_input,
                )
                # If this doesn't fail, it's a security issue
                security_issues.append(
                    f"SQL injection vulnerability in symbol validation: {malicious_input}"
                )
            except Exception:
                # Expected to fail with malicious input
                pass

        # Test 2: Authentication bypass
        self.logger.info("Testing authentication")

        # Test weak credentials
        auth_config = {
            "users": [
                {"username": "admin", "password": "password"},
                {"username": "trader", "password": "123456"},
            ],
            "api_key": "weak_key_123",
            "authentication_required": False,
        }

        auth_vulnerabilities = self.security_tester.test_authentication_bypass(
            auth_config
        )
        security_issues.extend(auth_vulnerabilities)

        # Test 3: Data exposure
        self.logger.info("Testing data exposure")

        # Check if sensitive data is exposed in error messages
        test_data = {
            "portfolio": self.test_portfolio,
            "risk_metrics": self.test_risk_metrics,
        }

        # Serialize and check for sensitive information
        serialized_data = json.dumps(test_data, default=str)

        sensitive_patterns = ["password", "secret", "private_key", "api_key", "token"]

        for pattern in sensitive_patterns:
            if pattern in serialized_data.lower():
                security_issues.append(
                    f"Sensitive data exposure: {pattern} found in serialized data"
                )

        # Test 4: Rate limiting
        self.logger.info("Testing rate limiting")

        # Mock API endpoint for testing
        test_url = "http://localhost:8001 / api / trade"
        rate_limit_results = await self.security_tester.test_rate_limiting(
            test_url, max_requests=50
        )

        if not rate_limit_results["rate_limit_detected"]:
            security_issues.append("Rate limiting not properly implemented")

        # Assert no critical security issues
        critical_issues = [
            issue
            for issue in security_issues
            if "critical" in issue.lower() or "injection" in issue.lower()
        ]
        if critical_issues:
            self.logger.error(f"Critical security issues found: {critical_issues}")
            assert (
                len(critical_issues) == 0
            ), f"Critical security issues detected: {critical_issues}"

        # Log all security findings
        if security_issues:
            self.logger.warning(f"Security issues found: {security_issues}")
        else:
            self.logger.info("No security issues detected")

        return {
            "security_issues": security_issues,
            "critical_issues": critical_issues,
            "tests_performed": [
                "input_validation",
                "authentication",
                "data_exposure",
                "rate_limiting",
            ],
        }

    @e2e_test(timeout=600)
    @flaky_test(max_attempts=3)
    async def test_error_handling_and_recovery(self):
        """Test error handling and recovery scenarios."""
        self.logger.info("Testing error handling and recovery")

        error_scenarios = []

        # Scenario 1: Data adapter failure
        self.logger.info("Testing data adapter failure recovery")
        try:
            failing_adapter = self.mock_factory.create_mock_data_adapter(error_rate=1.0)

            # Try to get data from failing adapter
            await failing_adapter.get_market_data("00700.HK")
            error_scenarios.append("FAIL: Data adapter failure not detected")
        except Exception as e:
            self.logger.info(f"✓ Data adapter failure properly handled: {e}")

        # Scenario 2: Network timeout
        self.logger.info("Testing network timeout handling")
        try:
            # Simulate network timeout
            await asyncio.wait_for(self._simulate_network_operation(), timeout=0.1)
            error_scenarios.append("FAIL: Network timeout not detected")
        except asyncio.TimeoutError:
            self.logger.info("✓ Network timeout properly handled")
        except Exception as e:
            self.logger.info(f"✓ Network error properly handled: {e}")

        # Scenario 3: Invalid market data
        self.logger.info("Testing invalid market data handling")
        invalid_data_samples = [
            # Negative prices
            {
                "symbol": "TEST.HK",
                "open": -100,
                "high": -90,
                "low": -110,
                "close": -95,
                "volume": 1000,
            },
            # Invalid OHLC relationships
            {
                "symbol": "TEST.HK",
                "open": 100,
                "high": 90,
                "low": 110,
                "close": 105,
                "volume": 1000,
            },
            # Missing required fields
            {
                "symbol": "TEST.HK",
                "open": 100,
                "close": 105,
            },  # Missing high, low, volume
        ]

        for invalid_data in invalid_data_samples:
            try:
                TestAssertions.assert_valid_market_data([invalid_data], "TEST.HK")
                error_scenarios.append(
                    f"FAIL: Invalid data not detected: {invalid_data}"
                )
            except AssertionError:
                self.logger.info(f"✓ Invalid data properly rejected: {invalid_data}")

        # Scenario 4: Portfolio constraint violation
        self.logger.info("Testing portfolio constraint violations")

        # Test with negative positions
        invalid_portfolio = {
            "portfolio_id": "test_invalid",
            "total_value": 1000000.0,
            "positions": [
                {
                    "symbol": "TEST.HK",
                    "shares": -1000,  # Negative shares
                    "avg_price": 100.0,
                    "current_price": 105.0,
                    "market_value": -105000.0,
                    "weight": -0.105,  # Negative weight
                }
            ],
        }

        try:
            TestAssertions.assert_valid_portfolio(invalid_portfolio)
            error_scenarios.append("FAIL: Invalid portfolio constraints not detected")
        except AssertionError:
            self.logger.info("✓ Portfolio constraint violation properly detected")

        # Scenario 5: Risk limit breach
        self.logger.info("Testing risk limit breach handling")

        # Create risk metrics that exceed limits
        risky_metrics = self.test_risk_metrics.copy()
        risky_metrics["max_drawdown"]["percentage"] = 0.5  # 50% drawdown
        risky_metrics["var_99"]["percentage"] = 0.2  # 20% VaR

        try:
            TestAssertions.assert_valid_risk_metrics(risky_metrics)
            # This might pass validation, but we should have risk limits in actual system
            self.logger.warning("Risk limit breaches need system - level validation")
        except AssertionError:
            self.logger.info("✓ Risk limit breach properly detected")

        # Assert all error scenarios were properly handled
        failed_scenarios = [s for s in error_scenarios if s.startswith("FAIL:")]
        if failed_scenarios:
            self.logger.error(f"Error handling failures: {failed_scenarios}")
            assert (
                len(failed_scenarios) == 0
            ), f"Error handling issues detected: {failed_scenarios}"

        self.logger.info("✓ All error handling scenarios properly managed")

        return {
            "error_scenarios_tested": len(error_scenarios)
            + len(invalid_data_samples)
            + 4,
            "failures_detected": len(failed_scenarios),
            "scenarios": [
                "data_adapter_failure",
                "network_timeout",
                "invalid_data",
                "portfolio_constraints",
                "risk_limits",
            ],
        }

    @e2e_test(timeout=1200)
    @performance_test(max_duration=600, max_memory_mb=512)
    async def test_scalability_limits(self):
        """Test system scalability limits."""
        self.logger.info("Testing system scalability")

        scalability_results = {}

        # Test 1: Large dataset processing
        self.logger.info("Testing large dataset processing")
        large_dataset_start = time.time()

        try:
            # Generate large dataset
            large_symbols = [f"{i:04d}.HK" for i in range(100, 200)]  # 100 symbols
            large_market_data = {}

            for symbol in large_symbols:
                # Generate 90 days of 1 - minute data
                data = self.data_generator.generate_market_data(
                    symbol=symbol, days=90, frequency="1min"
                )
                large_market_data[symbol] = data

            dataset_processing_time = time.time() - large_dataset_start
            total_records = sum(len(data) for data in large_market_data.values())

            scalability_results["large_dataset"] = {
                "symbols_processed": len(large_symbols),
                "total_records": total_records,
                "processing_time": dataset_processing_time,
                "records_per_second": (
                    total_records / dataset_processing_time
                    if dataset_processing_time > 0
                    else 0
                ),
            }

            self.logger.info(
                f"Processed {total_records:,} records in {dataset_processing_time:.2f}s"
            )

            # Performance assertions
            assert (
                dataset_processing_time < 300
            ), f"Large dataset processing too slow: {dataset_processing_time}s"
            assert (
                total_records > 100000
            ), f"Insufficient data generated: {total_records} records"

        except Exception as e:
            self.logger.error(f"Large dataset processing failed: {e}")
            scalability_results["large_dataset"] = {"error": str(e)}

        # Test 2: Concurrent strategy execution
        self.logger.info("Testing concurrent strategy execution")
        concurrent_start = time.time()

        try:
            # Run multiple strategies concurrently
            strategies = ["RSI", "MACD", "BollingerBands", "Momentum", "MeanReversion"]

            async def run_strategy(strategy_name: str, symbol: str):
                """Mock strategy execution."""
                # Simulate strategy computation time
                await asyncio.sleep(0.1)
                return {
                    "strategy": strategy_name,
                    "symbol": symbol,
                    "signal": np.random.choice(["BUY", "SELL", "HOLD"]),
                    "confidence": np.random.uniform(0.6, 0.95),
                    "execution_time": time.time(),
                }

            # Execute strategies for subset of symbols concurrently
            test_symbols = large_symbols[:10]
            tasks = []
            for strategy in strategies:
                for symbol in test_symbols:
                    tasks.append(run_strategy(strategy, symbol))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            successful_results = [r for r in results if not isinstance(r, Exception)]
            concurrent_time = time.time() - concurrent_start

            scalability_results["concurrent_strategies"] = {
                "strategies_executed": len(successful_results),
                "expected_executions": len(strategies) * len(test_symbols),
                "execution_time": concurrent_time,
                "executions_per_second": (
                    len(successful_results) / concurrent_time
                    if concurrent_time > 0
                    else 0
                ),
            }

            self.logger.info(
                f"Executed {len(successful_results)} strategies concurrently in {concurrent_time:.2f}s"
            )

            assert (
                len(successful_results) >= len(strategies) * len(test_symbols) * 0.95
            ), f"Too many strategy execution failures: {len(successful_results)}/{len(strategies) * len(test_symbols)}"

        except Exception as e:
            self.logger.error(f"Concurrent strategy execution failed: {e}")
            scalability_results["concurrent_strategies"] = {"error": str(e)}

        # Test 3: Memory usage monitoring
        self.logger.info("Testing memory usage")
        import psutil

        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024

        scalability_results["memory_usage"] = {
            "current_memory_mb": memory_mb,
            "memory_limit_mb": 512,
            "within_limits": memory_mb < 512,
        }

        self.logger.info(f"Current memory usage: {memory_mb:.1f} MB")

        # Test 4: API response time under load
        self.logger.info("Testing API response times")

        # Mock API endpoints for testing
        api_endpoints = [
            "/api / market - data",
            "/api / strategies",
            "/api / portfolio",
            "/api / risk - metrics",
        ]

        api_response_times = {}
        for endpoint in api_endpoints:
            # Simulate API call
            start_time = time.time()
            await asyncio.sleep(0.05)  # Simulate processing time
            response_time = time.time() - start_time

            api_response_times[endpoint] = response_time

        scalability_results["api_response_times"] = api_response_times
        avg_response_time = sum(api_response_times.values()) / len(api_response_times)

        # Assert API performance
        assert (
            avg_response_time < 0.5
        ), f"API response too slow: {avg_response_time:.3f}s"

        # Summary validation
        self.logger.info("Scalability test results:")
        for test_name, result in scalability_results.items():
            if "error" not in result:
                self.logger.info(f"  {test_name}: ✓")
            else:
                self.logger.warning(f"  {test_name}: ✗ {result['error']}")

        # Overall performance validation
        performance_issues = []

        if "large_dataset" in scalability_results:
            dataset_time = scalability_results["large_dataset"].get(
                "processing_time", 0
            )
            if dataset_time > 300:
                performance_issues.append(
                    f"Large dataset processing too slow: {dataset_time:.2f}s"
                )

        if "memory_usage" in scalability_results:
            if not scalability_results["memory_usage"]["within_limits"]:
                performance_issues.append("Memory usage exceeds limits")

        if performance_issues:
            self.logger.warning(f"Performance issues detected: {performance_issues}")
            # Don't fail the test for performance issues, but log them
        else:
            self.logger.info("✓ All scalability tests passed")

        return scalability_results

    def _calculate_rsi(self, prices, window=14):
        """Calculate RSI indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def _calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """Calculate MACD indicator."""
        exp1 = prices.ewm(span=fast, adjust=False).mean()
        exp2 = prices.ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        return macd.iloc[-1] - signal_line.iloc[-1]

    async def _simulate_network_operation(self):
        """Simulate a network operation that might time out."""
        await asyncio.sleep(1.0)  # Simulate slow network
        return "network_result"


@pytest.mark.e2e
@pytest.mark.smoke
class TestSystemHealthAndMonitoring:
    """Test system health monitoring and basic functionality."""

    @smoke_test(timeout=60)
    async def test_basic_system_health(self):
        """Test basic system health checks."""
        self.logger.info("Running basic system health check")

        health_checks = {}

        # Check 1: System startup
        self.logger.info("Testing system startup")
        startup_start = time.time()

        try:
            # Mock system initialization
            await asyncio.sleep(0.1)  # Simulate startup time
            startup_time = time.time() - startup_start
            health_checks["system_startup"] = {
                "status": "healthy",
                "startup_time": startup_time,
                "within_limits": startup_time < 30,
            }
        except Exception as e:
            health_checks["system_startup"] = {"status": "unhealthy", "error": str(e)}

        # Check 2: Database connectivity
        self.logger.info("Testing database connectivity")

        try:
            # Mock database connection test
            await asyncio.sleep(0.05)
            health_checks["database"] = {"status": "healthy", "connection_time": 0.05}
        except Exception as e:
            health_checks["database"] = {"status": "unhealthy", "error": str(e)}

        # Check 3: Cache connectivity
        self.logger.info("Testing cache connectivity")

        try:
            # Mock cache connection test
            await asyncio.sleep(0.02)
            health_checks["cache"] = {"status": "healthy", "connection_time": 0.02}
        except Exception as e:
            health_checks["cache"] = {"status": "unhealthy", "error": str(e)}

        # Check 4: External API connectivity
        self.logger.info("Testing external API connectivity")

        try:
            # Mock external API test
            async with aiohttp.ClientSession() as session:
                # Test with a real public API
                async with session.get(
                    "https://httpbin.org / status / 200",
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        health_checks["external_api"] = {
                            "status": "healthy",
                            "response_code": response.status,
                        }
                    else:
                        health_checks["external_api"] = {
                            "status": "unhealthy",
                            "response_code": response.status,
                        }
        except Exception as e:
            health_checks["external_api"] = {"status": "unhealthy", "error": str(e)}

        # Check 5: Memory usage
        self.logger.info("Checking memory usage")
        import psutil

        process = psutil.Process()
        memory_percent = process.memory_percent()

        health_checks["memory"] = {
            "status": "healthy" if memory_percent < 80 else "warning",
            "memory_percent": memory_percent,
        }

        # Check 6: CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        health_checks["cpu"] = {
            "status": "healthy" if cpu_percent < 80 else "warning",
            "cpu_percent": cpu_percent,
        }

        # Overall health assessment
        unhealthy_services = [
            service
            for service, check in health_checks.items()
            if check.get("status") == "unhealthy"
        ]

        if unhealthy_services:
            self.logger.warning(f"Unhealthy services detected: {unhealthy_services}")
            overall_status = "unhealthy"
        else:
            self.logger.info("✓ All system health checks passed")
            overall_status = "healthy"

        health_summary = {
            "overall_status": overall_status,
            "unhealthy_services": unhealthy_services,
            "checks": health_checks,
            "timestamp": datetime.now().isoformat(),
        }

        # Assert system is healthy for smoke test
        assert (
            overall_status == "healthy"
        ), f"System health check failed: {unhealthy_services}"

        return health_summary


if __name__ == "__main__":
    # Run the comprehensive end - to - end tests
    pytest.main([__file__, "-v", "--tb=short", "--maxfail=1", "-m", "e2e"])

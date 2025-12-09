"""
Comprehensive End - to - End Testing Framework for Hong Kong Quantitative Trading System

This framework provides:
- Complete testing pyramid (unit, integration, e2e)
- Test data management and generation
- Service orchestration and mocking
- Performance and load testing
- Security testing
- Automated test pipeline integration
"""

__version__ = "1.0.0"
__author__ = "Quantitative Trading System Testing Team"

from .core import TestConfig, TestEnvironment, TestFramework, TestReport, TestResult
from .decorators import (
    e2e_test,
    flaky_test,
    integration_test,
    performance_test,
    security_test,
    unit_test,
)
from .fixtures import (
    CacheFixture,
    DatabaseFixture,
    KafkaFixture,
    MockServiceFactory,
    TestDataGenerator,
    TestEnvironmentManager,
)
from .utils import (
    CoverageAnalyzer,
    PerformanceMonitor,
    SecurityTester,
    TestAssertions,
    TestHelpers,
)

__all__ = [
    # Core framework
    "TestFramework",
    "TestConfig",
    "TestEnvironment",
    "TestResult",
    "TestReport",
    # Fixtures
    "TestDataGenerator",
    "MockServiceFactory",
    "TestEnvironmentManager",
    "DatabaseFixture",
    "CacheFixture",
    "KafkaFixture",
    # Utilities
    "TestAssertions",
    "TestHelpers",
    "PerformanceMonitor",
    "SecurityTester",
    "CoverageAnalyzer",
    # Decorators
    "unit_test",
    "integration_test",
    "e2e_test",
    "performance_test",
    "security_test",
    "flaky_test",
]

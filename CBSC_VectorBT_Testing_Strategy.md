# VectorBT-native CBSC Backtesting System Testing Strategy
# VectorBT原生CBSC回测系统测试策略

**Author:** CBSC Backtesting System Team
**Date:** 2025-12-04
**Version:** 1.0

## 🎯 Testing Objectives & Scope

### Primary Objectives
1. **Functional Verification**: Ensure all components work as specified
2. **Integration Testing**: Validate seamless interaction between components
3. **Performance Benchmarking**: Meet <30 seconds processing requirement for 1-year data
4. **CBSC-Specific Logic**: Test knockout risk, leverage effects, and time decay
5. **Data Quality Assurance**: Validate sentiment data alignment and integrity
6. **Production Readiness**: Ensure system stability for deployment

### Testing Scope
- **Core Components**: data_loader.py, signal_generator.py, cbsc_backtester.py, optimizer.py
- **Data Pipeline**: CBSC sentiment data → Price data alignment → Feature engineering
- **Signal Generation**: Multiple strategy types (sentiment, technical, CBSC-aware)
- **Backtesting Engine**: VectorBT portfolio creation and performance calculation
- **Optimization**: Parameter search and performance validation

## 🏗️ System Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  data_loader.py │───▶│ signal_generator │───▶│cbsc_backtester.py│
│                 │    │.py              │    │                 │
│ • CBSC CSV Load │    │ • 5 Strategy     │    │ • VectorBT Engine│
│ • Yahoo Finance │    │   Generation     │    │ • Performance   │
│ • Data Alignment│    │ • Signal Quality │    │   Metrics       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                ▲                        ▲
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   optimizer.py   │───▶│  Performance    │
                       │                  │    │  Reports        │
                       │ • Grid Search    │    │                 │
                       │ • Random Search  │    │ • Risk Metrics  │
                       │ • Bayesian Opt.  │    │ • Validation    │
                       └──────────────────┘    └─────────────────┘
```

## 📋 Detailed Test Plan

### 1. Functional Testing

#### 1.1 Data Loader Tests (`test_data_loader_functionality.py`)

**Test Cases:**
- **TC-DL-001**: Valid CBSC CSV file loading
  - Input: Valid warrant_sentiment_daily.csv
  - Expected: Successful load with correct data types
  - Validation: Row count, column presence, data type validation

- **TC-DL-002**: Invalid file path handling
  - Input: Non-existent file path
  - Expected: Graceful error handling with empty DataFrame
  - Validation: Exception handling, error message

- **TC-DL-003**: Missing data columns handling
  - Input: CSV missing required columns (Date, Bull_Ratio, etc.)
  - Expected: Error or filtered dataset
  - Validation: Column existence check

- **TC-DL-004**: Price data loading from Yahoo Finance
  - Input: Valid symbol (0700.HK)
  - Expected: Successful price data retrieval
  - Validation: OHLCV data completeness, date range

- **TC-DL-005**: Data alignment functionality
  - Input: Sentiment and price data with different date ranges
  - Expected: Properly aligned datasets
  - Validation: Common dates, correct data length

- **TC-DL-006**: Feature engineering
  - Input: Aligned sentiment and price data
  - Expected: CBSC features calculated correctly
  - Validation: RSI calculation, sentiment scores, technical indicators

#### 1.2 Signal Generator Tests (`test_signal_generator_functionality.py`)

**Test Cases:**
- **TC-SG-001**: Sentiment signal generation
  - Input: Features DataFrame with sentiment data
  - Expected: Valid buy/sell/hold signals
  - Validation: Signal distribution, threshold application

- **TC-SG-002**: Technical signal generation
  - Input: Features DataFrame with technical indicators
  - Expected: RSI, MA, and momentum signals
  - Validation: Signal logic, threshold comparisons

- **TC-SG-003**: CBSC-aware signal generation
  - Input: Features DataFrame with call price calculations
  - Expected: Risk-adjusted signals
  - Validation: Knockout risk consideration, leverage effects

- **TC-SG-004**: Multiple strategy generation
  - Input: Same features DataFrame
  - Expected: 5 different strategy outputs
  - Validation: Strategy uniqueness, signal consistency

- **TC-SG-005**: VectorBT signal format
  - Input: Generated signals
  - Expected: Boolean entries/exits arrays
  - Validation: Array dimensions, data types, signal counts

- **TC-SG-006**: Signal quality analysis
  - Input: Signals and performance data
  - Expected: Quality metrics calculated
  - Validation: Signal frequency, correlation analysis

#### 1.3 CBSC Backtester Tests (`test_cbsc_backtester_functionality.py`)

**Test Cases:**
- **TC-CB-001**: Single strategy backtesting
  - Input: Valid entries/exits signals
  - Expected: VectorBT Portfolio object
  - Validation: Portfolio creation, trade execution

- **TC-CB-002**: Multiple strategy comparison
  - Input: Multiple signal sets
  - Expected: Performance comparison table
  - Validation: Metrics calculation, ranking logic

- **TC-CB-003**: Performance metrics calculation
  - Input: Portfolio results
  - Expected: Complete performance metrics
  - Validation: Sharpe ratio, drawdown, returns calculations

- **TC-CB-004**: Report generation
  - Input: Backtest results
  - Expected: Formatted report text
  - Validation: Report completeness, accuracy

- **TC-CB-005**: Visualization functionality
  - Input: Portfolio results
  - Expected: Strategy plots and charts
  - Validation: Plot generation, data visualization

#### 1.4 Optimizer Tests (`test_optimizer_functionality.py`)

**Test Cases:**
- **TC-OPT-001**: Grid search optimization
  - Input: Parameter ranges
  - Expected: Comprehensive parameter testing
  - Validation: Parameter coverage, result ranking

- **TC-OPT-002**: Random search optimization
  - Input: Parameter ranges and iteration count
  - Expected: Random parameter exploration
  - Validation: Randomness, result diversity

- **TC-OPT-003**: Bayesian optimization
  - Input: Initial parameter ranges
  - Expected: Intelligent parameter search
  - Validation: Convergence behavior, optimization efficiency

- **TC-OPT-004**: Parameter sensitivity analysis
  - Input: Optimization results
  - Expected: Parameter importance ranking
  - Validation: Sensitivity metrics, analysis accuracy

### 2. Integration Testing

#### 2.1 Component Integration Tests (`test_integration_components.py`)

**Test Cases:**
- **TC-INT-001**: End-to-end workflow
  - Input: CBSC CSV file and symbol
  - Expected: Complete backtest results
  - Validation: Data flow integrity, result consistency

- **TC-INT-002**: Data pipeline integration
  - Input: Raw CBSC data
  - Expected: Clean, aligned features
  - Validation: Data transformations, quality checks

- **TC-INT-003**: Strategy integration
  - Input: Multiple signal generation methods
  - Expected: Coherent strategy outputs
  - Validation: Signal compatibility, performance comparison

#### 2.2 External API Integration Tests (`test_integration_external.py`)

**Test Cases:**
- **TC-API-001**: Yahoo Finance API connectivity
  - Input: Various stock symbols
  - Expected: Successful data retrieval
  - Validation: API response handling, error recovery

- **TC-API-002**: Network failure handling
  - Input: Simulated network failures
  - Expected: Graceful degradation
  - Validation: Error handling, retry mechanisms

### 3. Performance Testing

#### 3.1 Speed Benchmark Tests (`test_performance_speed.py`)

**Performance Targets:**
- **Data Loading**: < 5 seconds for 1-year data
- **Signal Generation**: < 3 seconds for all strategies
- **Backtesting**: < 20 seconds for all strategies
- **Total Process**: < 30 seconds (requirement)

**Test Cases:**
- **TC-PERF-001**: Single stock performance
  - Input: 1-year 0700.HK data
  - Expected: Processing within time limits
  - Validation: Timing measurements, throughput analysis

- **TC-PERF-002**: Multiple stock scaling
  - Input: 10 stocks with 1-year data
  - Expected: Linear scaling performance
  - Validation: Scalability metrics, resource usage

- **TC-PERF-003**: Large data handling
  - Input: 5-year historical data
  - Expected: Maintained performance levels
  - Validation: Memory usage, processing time

#### 3.2 Resource Utilization Tests (`test_performance_resources.py`)

**Test Cases:**
- **TC-RES-001**: Memory usage monitoring
  - Validation: Peak memory < 2GB for typical workloads
  - Monitoring: Memory profiling, leak detection

- **TC-RES-002**: CPU utilization analysis
  - Validation: Efficient CPU usage during computation
  - Monitoring: CPU profiling, optimization opportunities

### 4. CBSC-Specific Testing

#### 4.1 CBSC Logic Tests (`test_cbsc_specific_logic.py`)

**CBSC-Specific Features to Test:**
- **Knockout Risk**: Call price proximity effects
- **Leverage Effects**: Amplified returns and volatility
- **Time Decay**: Daily erosion of warrant value
- **Sentiment Integration**: Bull/Bear ratio impact on signals

**Test Cases:**
- **TC-CBSC-001**: Knockout risk calculation
  - Input: Price levels near simulated call prices
  - Expected: Risk-adjusted signal reduction
  - Validation: Call distance calculations, risk adjustments

- **TC-CBSC-002**: Leverage effect modeling
  - Input: Base returns with leverage factors
  - Expected: Amplified performance metrics
  - Validation: Leverage calculations, risk-adjusted metrics

- **TC-CBSC-003**: Time decay simulation
  - Input: Holding periods with decay factors
  - Expected: Performance degradation over time
  - Validation: Decay calculations, holding period analysis

- **TC-CBSC-004**: Sentiment signal weighting
  - Input: Various sentiment strength levels
  - Expected: Proportional signal adjustments
  - Validation: Sentiment scoring, extreme情绪 handling

#### 4.2 Risk Management Tests (`test_risk_management.py`)

**Test Cases:**
- **TC-RISK-001**: Position sizing limits
  - Input: Large capital allocations
  - Expected: Maximum position constraints
  - Validation: Position limits, risk controls

- **TC-RISK-002**: Drawdown monitoring
  - Input: Historical drawdown scenarios
  - Expected: Real-time drawdown tracking
  - Validation: Drawdown calculations, alert thresholds

### 5. Data Quality Testing

#### 5.1 Data Integrity Tests (`test_data_quality_integrity.py`)

**Test Cases:**
- **TC-DQ-001**: Missing data handling
  - Input: Datasets with gaps
  - Expected: Proper missing data treatment
  - Validation: Gap filling, forward/backward fill

- **TC-DQ-002**: Outlier detection
  - Input: Data with extreme values
  - Expected: Outlier identification and handling
  - Validation: Statistical outlier detection, impact analysis

- **TC-DQ-003**: Data consistency checks
  - Input: Cross-referenced data sources
  - Expected: Consistent data alignment
  - Validation: Cross-validation, consistency metrics

#### 5.2 Sentiment Data Validation (`test_data_quality_sentiment.py`)

**Test Cases:**
- **TC-DQS-001**: Sentiment score validation
  - Input: Raw bull/bear turnover data
  - Expected: Valid sentiment calculations
  - Validation: Formula correctness, range validation

- **TC-DQS-002**: Turnover threshold filtering
  - Input: Various turnover levels
  - Expected: Minimum liquidity filtering
  - Validation: Threshold logic, data filtering

### 6. Edge Case Testing

#### 6.1 Extreme Conditions Tests (`test_edge_cases_extreme.py`)

**Test Cases:**
- **TC-EDGE-001**: Zero/negative turnover scenarios
  - Input: Days with zero market activity
  - Expected: Graceful handling of no-trade scenarios
  - Validation: Zero-division prevention, fallback logic

- **TC-EDGE-002**: Extreme market volatility
  - Input: High volatility periods (crash scenarios)
  - Expected: Robust performance under stress
  - Validation: Volatility handling, signal stability

- **TC-EDGE-003**: Minimal data scenarios
  - Input: Very short time periods (< 30 days)
  - Expected: Degraded but functional operation
  - Validation: Minimum data requirements, functionality preservation

#### 6.2 Error Handling Tests (`test_edge_cases_errors.py`)

**Test Cases:**
- **TC-ERR-001**: Corrupted data files
  - Input: Malformed CSV files
  - Expected: Error detection and recovery
  - Validation: File parsing, error recovery mechanisms

- **TC-ERR-002**: API service failures
  - Input: Simulated API timeouts/errors
  - Expected: Fallback behavior
  - Validation: Error handling, retry logic, graceful degradation

### 7. Strategy Comparison Tests

#### 7.1 Strategy Differentiation Tests (`test_strategy_comparison.py`)

**Test Cases:**
- **TC-STRAT-001**: Strategy uniqueness validation
  - Input: Same data for all strategies
  - Expected: Distinct performance characteristics
  - Validation: Strategy differentiation, correlation analysis

- **TC-STRAT-002**: Strategy consistency checks
  - Input: Multiple runs with same parameters
  - Expected: Reproducible results
  - Validation: Deterministic behavior, result consistency

- **TC-STRAT-003**: Strategy ranking validation
  - Input: Various performance metrics
  - Expected: Logical ranking based on objectives
  - Validation: Ranking logic, metric calculations

### 8. Parameter Optimization Tests

#### 8.1 Optimization Algorithm Tests (`test_parameter_optimization.py`)

**Test Cases:**
- **TC-OPTALG-001**: Optimization convergence
  - Input: Known objective function
  - Expected: Convergence to optimal parameters
  - Validation: Convergence behavior, optimization quality

- **TC-OPTALG-002**: Parameter space exploration
  - Input: Multi-dimensional parameter ranges
  - Expected: Comprehensive space coverage
  - Validation: Space coverage, diversity of solutions

- **TC-OPTALG-003**: Optimization reproducibility
  - Input: Same optimization setup
  - Expected: Consistent results
  - Validation: Random seed handling, reproducibility

## 📊 Performance Benchmarks & Validation Criteria

### Performance Targets

| Metric | Target | Acceptance Criteria | Test Method |
|--------|--------|-------------------|-------------|
| **Data Loading Time** | < 5 seconds | ≤ 5s for 1-year data | TC-PERF-001 |
| **Signal Generation** | < 3 seconds | ≤ 3s for all strategies | TC-PERF-001 |
| **Backtesting Execution** | < 20 seconds | ≤ 20s for all strategies | TC-PERF-001 |
| **Total Processing Time** | < 30 seconds | ≤ 30s end-to-end | TC-PERF-001 |
| **Memory Usage** | < 2GB peak | ≤ 2GB for typical workloads | TC-RES-001 |
| **CPU Utilization** | < 80% average | Efficient CPU usage | TC-RES-002 |

### Functional Validation Criteria

| Component | Success Criteria | Measurement Method |
|-----------|------------------|-------------------|
| **Data Loader** | 100% data integrity | Data validation checks |
| **Signal Generator** | 95%+ signal quality | Signal analysis metrics |
| **Backtester** | Accurate performance | Benchmark comparison |
| **Optimizer** | Convergence to optimum | Optimization quality metrics |

### CBSC-Specific Validation Criteria

| Feature | Validation Requirement | Test Case |
|---------|----------------------|-----------|
| **Knockout Risk** | Correct call price modeling | TC-CBSC-001 |
| **Leverage Effects** | Accurate amplification modeling | TC-CBSC-002 |
| **Time Decay** | Realistic erosion simulation | TC-CBSC-003 |
| **Sentiment Integration** | Valid sentiment scoring | TC-CBSC-004 |

## 🔍 Test Environment Setup

### Test Data Requirements

1. **CBSC Sentiment Data**
   - File: `warrant_sentiment_daily.csv`
   - Required columns: Date, Bull_Ratio, Bull_Bear_Ratio, Bull_Turnover_HKD, Bear_Turnover_HKD, Afternoon_Close, Signal, Sentiment_Level
   - Data range: Minimum 6 months for meaningful testing
   - Quality: Complete data with minimal gaps

2. **Price Data**
   - Source: Yahoo Finance API
   - Symbols: 0700.HK (primary), additional symbols for scaling tests
   - Required fields: OHLCV data with proper date alignment
   - Fallback: Local cached data for offline testing

3. **Test Scenarios**
   - Normal market conditions (baseline)
   - High volatility periods (stress testing)
   - Low sentiment periods (edge cases)
   - Missing data scenarios (robustness testing)

### Test Infrastructure

1. **Python Environment**
   ```bash
   # Required packages for testing
   pip install pytest>=7.4.0
   pip install pytest-cov>=4.1.0
   pip install pytest-xdist>=3.3.0
   pip install pandas>=2.0.0
   pip install vectorbt>=0.25.0
   pip install yfinance>=0.2.18
   ```

2. **Test Configuration**
   ```python
   # pytest.ini
   [tool:pytest]
   testpaths = tests
   python_files = test_*.py
   python_classes = Test*
   python_functions = test_*
   addopts = --cov=src --cov-report=html --cov-report=term
   markers =
       unit: Unit tests
       integration: Integration tests
       performance: Performance tests
       cbsc_specific: CBSC-specific tests
       slow: Slow running tests
   ```

3. **Continuous Integration**
   - GitHub Actions or similar CI/CD pipeline
   - Automated test execution on code changes
   - Performance regression detection
   - Code coverage monitoring

## 🚀 Test Execution Plan

### Phase 1: Unit Testing (Week 1)
1. **Day 1-2**: Core component unit tests
   - Data loader functionality (TC-DL-001 to TC-DL-006)
   - Signal generator basic functionality (TC-SG-001 to TC-SG-006)

2. **Day 3-4**: Advanced component tests
   - Backtester engine tests (TC-CB-001 to TC-CB-005)
   - Optimizer algorithm tests (TC-OPT-001 to TC-OPT-004)

3. **Day 5**: Unit test coverage and quality
   - Code coverage analysis (target: >90%)
   - Test quality review
   - Documentation of test cases

### Phase 2: Integration Testing (Week 2)
1. **Day 6-7**: Component integration
   - End-to-end workflow testing (TC-INT-001 to TC-INT-003)
   - External API integration (TC-API-001 to TC-API-002)

2. **Day 8-9**: Performance validation
   - Speed benchmark testing (TC-PERF-001 to TC-PERF-003)
   - Resource utilization monitoring (TC-RES-001 to TC-RES-002)

3. **Day 10**: Integration test completion
   - Cross-component functionality validation
   - Performance benchmark establishment
   - Integration test report

### Phase 3: Specialized Testing (Week 3)
1. **Day 11-12**: CBSC-specific testing
   - CBSC logic validation (TC-CBSC-001 to TC-CBSC-004)
   - Risk management testing (TC-RISK-001 to TC-RISK-002)

2. **Day 13-14**: Data quality and edge cases
   - Data integrity validation (TC-DQ-001 to TC-DQ-003)
   - Sentiment data testing (TC-DQS-001 to TC-DQS-002)
   - Edge case handling (TC-EDGE-001 to TC-ERR-002)

3. **Day 15**: Specialized test completion
   - CBSC feature validation
   - Data quality assurance
   - Edge case robustness verification

### Phase 4: Strategy & Optimization Testing (Week 4)
1. **Day 16-17**: Strategy comparison
   - Strategy differentiation (TC-STRAT-001 to TC-STRAT-003)
   - Performance comparison validation

2. **Day 18-19**: Parameter optimization
   - Optimization algorithm testing (TC-OPTALG-001 to TC-OPTALG-003)
   - Parameter sensitivity analysis

3. **Day 20**: Final validation
   - Complete system validation
   - Production readiness assessment
   - Final test report generation

## 📋 Test Deliverables

### 1. Test Plan Document
- ✅ Comprehensive test strategy (this document)
- ✅ Test case specifications
- ✅ Performance benchmarks
- ✅ Validation criteria

### 2. Test Implementation Files
- `test_data_loader_functionality.py`
- `test_signal_generator_functionality.py`
- `test_cbsc_backtester_functionality.py`
- `test_optimizer_functionality.py`
- `test_integration_components.py`
- `test_performance_speed.py`
- `test_cbsc_specific_logic.py`
- `test_data_quality_integrity.py`
- `test_edge_cases_extreme.py`
- `test_strategy_comparison.py`

### 3. Test Configuration
- `pytest.ini` configuration
- `conftest.py` fixtures and helpers
- Test data setup scripts
- CI/CD pipeline configuration

### 4. Test Reports
- Unit test coverage report
- Integration test results
- Performance benchmark report
- CBSC-specific validation report
- Production readiness assessment

## ⚠️ Risk Assessment & Mitigation

### Production Deployment Risks

| Risk Category | Risk Level | Impact | Mitigation Strategy |
|---------------|------------|--------|-------------------|
| **Data Quality Issues** | Medium | High | Comprehensive data validation, fallback data sources |
| **Performance Degradation** | Low | Medium | Continuous performance monitoring, automated regression tests |
| **CBSC Logic Errors** | High | High | Extensive CBSC-specific testing, domain expert validation |
| **External API Dependencies** | Medium | Medium | API error handling, cached data fallbacks |
| **Memory/CPU Overload** | Low | Low | Resource monitoring, scaling limits |
| **Calculation Accuracy** | High | High | Mathematical validation, benchmark comparisons |

### Testing Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Insufficient Test Coverage** | Low | High | Coverage monitoring, regular test audits |
| **Test Data Availability** | Medium | Medium | Synthetic data generation, data mocking |
| **Performance Test Environment** | Medium | Medium | Staging environment replication |
| **CBSC Domain Knowledge Gap** | Low | High | Domain expert involvement, documentation review |

## ✅ Success Criteria

### Functional Success
- All unit tests pass (>90% code coverage)
- All integration tests execute successfully
- CBSC-specific logic validates correctly
- Edge cases handled gracefully

### Performance Success
- End-to-end processing < 30 seconds for 1-year data
- Memory usage < 2GB for typical workloads
- CPU utilization < 80% average
- Linear scaling for multiple stocks

### Quality Success
- Zero critical defects in production
- Data quality issues < 1% of records
- Performance regression < 5%
- User acceptance criteria met

### Production Readiness
- All automated tests passing in CI/CD
- Performance benchmarks established
- Monitoring and alerting configured
- Rollback procedures documented

## 📚 Appendix

### A. Test Case Template
```python
def test_function_name():
    """
    Test Case ID: TC-XXX-XXX
    Description: [Brief description of test]
    Input: [Test input data]
    Expected: [Expected output/behavior]
    Validation: [How success is measured]
    """
    # Test implementation
    assert result == expected
```

### B. Performance Test Framework
```python
import time
import psutil
import pytest

@pytest.mark.performance
def test_performance_benchmark():
    start_time = time.time()
    start_memory = psutil.Process().memory_info().rss

    # Execute function to benchmark
    result = function_to_test()

    end_time = time.time()
    end_memory = psutil.Process().memory_info().rss

    execution_time = end_time - start_time
    memory_used = end_memory - start_memory

    assert execution_time < MAX_TIME, f"Too slow: {execution_time}s"
    assert memory_used < MAX_MEMORY, f"Too much memory: {memory_used} bytes"
```

### C. Mock Data Generator
```python
def generate_mock_cbsc_data(days=252):
    """Generate mock CBSC sentiment data for testing"""
    dates = pd.date_range('2024-01-01', periods=days, freq='D')

    data = pd.DataFrame({
        'Date': dates,
        'Bull_Ratio': np.random.uniform(0.2, 0.8, days),
        'Bull_Bear_Ratio': np.random.uniform(0.5, 2.0, days),
        'Bull_Turnover_HKD': np.random.uniform(1e6, 1e7, days),
        'Bear_Turnover_HKD': np.random.uniform(1e6, 1e7, days),
        'Afternoon_Close': 25000 + np.cumsum(np.random.randn(days) * 100),
        'Signal': np.random.choice([-1, 0, 1], days),
        'Sentiment_Level': np.random.choice(['EXTREME BULL', 'MOD BULL', 'NEUTRAL', 'MOD BEAR', 'EXTREME BEAR'], days)
    })

    return data
```

---

## 🎯 Next Steps

1. **Immediate Actions (Today)**
   - Review and approve this test strategy
   - Set up test environment and dependencies
   - Begin implementing Phase 1 unit tests

2. **This Week**
   - Complete Phase 1 unit testing
   - Establish performance benchmarks
   - Set up CI/CD pipeline

3. **Next Two Weeks**
   - Execute integration and specialized testing
   - Validate CBSC-specific functionality
   - Complete performance optimization

4. **Final Week**
   - Complete all testing phases
   - Generate final test reports
   - Prepare production deployment checklist

---

**Document Status:** Complete
**Next Review Date:** 2025-12-05
**Approval Required:** Yes
**Implementation Priority:** High
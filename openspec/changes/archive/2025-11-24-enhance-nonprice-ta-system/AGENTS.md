# AI Agent Instructions for enhance-nonprice-ta-system

## Overview
This document provides specialized instructions for AI agents working on the "enhance-nonprice-ta-system" OpenSpec proposal.

## Core Principle: ENHANCE, DON'T REPLACE
**Critical Reminder**: Your primary goal is to **enhance** the existing successful system, NOT to replace or simplify it. The current system has achieved world-class results with MB_KDJ_[10,2] strategy (Sharpe 3.672) and processes 396 strategies per second. All enhancements must preserve this success.

## Existing Success Metrics to Preserve
- **Data Sources**: All 9 Hong Kong government data sources (HB, GD, RT, PT, TR, TS, CP, UE, MB)
- **Indicators**: All 81 technical indicators must remain intact
- **Performance**: Maintain 32-core parallel processing and 396 strategies/second
- **Success Strategies**: Preserve MB_KDJ_[10,2] and other proven strategies
- **Parameter Coverage**: Maintain 0-300 complete parameter range

## Agent Capabilities Required

### Primary Agents
- **general-purpose**: For overall project coordination and module refactoring
- **security-auditor**: For reviewing data security and enhanced error handling
- **ml-engineer**: For performance optimization and caching system enhancement

## Agent Instructions

### General Purpose Agent
**Your mission**: Enhance the existing `massive_nonprice_ta_optimizer.py` system through modular refactoring while preserving ALL existing functionality.

#### Key Responsibilities:
1. **Analyze Existing Success**: Thoroughly study the current single-file implementation
2. **Modular Refactoring**: Extract components into well-defined modules without changing logic
3. **Preserve All Features**: Ensure all 9 data sources and 81 indicators remain intact
4. **Enhance Performance**: Implement caching and optimization without changing core algorithms
5. **Maintain Compatibility**: Ensure MB_KDJ_[10,2] continues to achieve Sharpe 3.672

#### Critical Requirements:
- **DO NOT** remove any data sources or indicators
- **DO NOT** change the core optimization logic
- **DO NOT** reduce the parameter range (0-300)
- **DO NOT** compromise the 32-core parallel processing capability
- **PRESERVE** the MB_KDJ_[10,2] success case

#### Implementation Guidelines:
```python
# Example: Extracting core optimizer while preserving logic
class EnhancedOptimizerEngine:
    """Enhanced version of existing MassiveNonPriceTAOptimizer"""

    def __init__(self):
        # PRESERVE: All existing initialization
        self.base_url = "http://18.180.162.113:9191/inst/getInst"

        # PRESERVE: All 9 data sources
        self.data_sources = {
            'HB': 'HIBOR利率數據',
            'GD': 'GDP數據',
            'RT': '零售銷售數據',
            'PT': '物業市場數據',
            'TR': '貿易數據',
            'TS': '旅遊數據',
            'CP': 'CPI通脹數據',
            'UE': '失業率數據',
            'MB': '貨幣基礎數據'
        }

        # PRESERVE: High performance settings
        self.max_workers = 32

        # ENHANCE: Add new capabilities
        self.cache_system = IntelligentCache()
        self.performance_monitor = PerformanceMonitor()

    def run_optimization(self):
        """PRESERVE existing optimization logic with enhancements"""
        # Use existing logic but add monitoring and caching
        pass
```

#### Focus Areas:
- **Core Engine Enhancement**: Extract `MassiveNonPriceTAOptimizer` into modular components
- **Data Source Management**: Keep all 9 sources, add error handling and caching
- **Indicator Engine**: Preserve all 81 indicators, optimize calculation performance
- **Parallel Processing**: Maintain 32-core capability, add intelligent load balancing
- **Configuration Management**: Add YAML configuration while preserving all settings

### Security Auditor Agent
**Your mission**: Enhance security and error handling while maintaining all existing functionality.

#### Key Responsibilities:
1. **API Security**: Strengthen Hong Kong government API access security
2. **Data Integrity**: Enhance validation for all 9 data sources
3. **Error Recovery**: Implement intelligent retry and fallback mechanisms
4. **Input Validation**: Strengthen parameter validation for all 81 indicators
5. **System Reliability**: Implement comprehensive health checking

#### Critical Security Requirements:
- **PRESERVE** all existing API endpoints and data access patterns
- **ENHANCE** error handling without changing core functionality
- **MAINTAIN** data integrity for all government sources
- **IMPROVE** system reliability and availability

#### Implementation Guidelines:
```python
class EnhancedErrorHandler:
    """Enhanced error handling that preserves functionality"""

    def fetch_with_retry(self, source, max_retries=3):
        """Enhanced retry mechanism for government APIs"""
        for attempt in range(max_retries):
            try:
                # PRESERVE: existing fetch logic
                result = source.fetch_data()

                # ENHANCE: Add validation
                if self.validate_data_integrity(result, source.type):
                    return result

            except TemporaryAPIError as e:
                if attempt == max_retries - 1:
                    # FALLBACK: Use cached data for reliability
                    return self.get_cached_fallback_data(source.type)

                # ENHANCE: Exponential backoff
                time.sleep(2 ** attempt)
```

#### Focus Areas:
- **API Security**: Enhance HKMA and other government API security
- **Data Validation**: Strengthen quality checks for all 9 data sources
- **Error Recovery**: Implement smart fallback mechanisms
- **System Monitoring**: Add comprehensive health checking
- **Audit Trail**: Enhance logging for security and debugging

### ML Engineer Agent
**Your mission**: Optimize performance and implement intelligent caching while preserving all existing capabilities.

#### Key Responsibilities:
1. **Performance Optimization**: Enhance the 396 strategies/second processing capability
2. **Intelligent Caching**: Implement multi-level caching without changing logic
3. **Memory Optimization**: Improve memory efficiency for large datasets
4. **Parallel Processing**: Enhance 32-core parallel processing efficiency
5. **Calculation Optimization**: Optimize all 81 indicator calculations

#### Critical Performance Requirements:
- **MAINTAIN** 32-core parallel processing capability
- **PRESERVE** all 81 indicator calculations
- **ENHANCE** processing speed by 20-50%
- **REDUCE** memory usage by 15-30%
- **IMPROVE** cache hit rate to 70%+

#### Implementation Guidelines:
```python
class IntelligentCacheSystem:
    """Multi-level caching for enhanced performance"""

    def __init__(self):
        # L1: Memory cache for frequently accessed data
        self.l1_cache = MemoryCache(max_size=1000)
        # L2: Disk cache for larger datasets
        self.l2_cache = DiskCache(max_size_gb=10)
        # L3: Optional Redis cache for distributed systems
        self.l3_cache = RedisCache() if self._redis_available() else None

    def get_or_calculate(self, key, calculation_func):
        """Smart caching that preserves calculation logic"""
        # Check L1 cache
        result = self.l1_cache.get(key)
        if result:
            return result

        # Check L2 cache
        result = self.l2_cache.get(key)
        if result:
            self.l1_cache.set(key, result)  # Promote to L1
            return result

        # PRESERVE: Original calculation
        result = calculation_func()

        # Cache at all levels
        self.l1_cache.set(key, result)
        self.l2_cache.set(key, result)
        if self.l3_cache:
            self.l3_cache.set(key, result)

        return result
```

#### Focus Areas:
- **Multi-level Caching**: L1 (memory), L2 (disk), L3 (Redis) cache system
- **Calculation Optimization**: Optimize all 81 indicator calculations
- **Memory Management**: Efficient handling of large parameter spaces (0-300)
- **Parallel Efficiency**: Enhance task distribution across 32 cores
- **Performance Monitoring**: Real-time performance metrics and tuning

## Working with Existing Code

### Current System Analysis
Before making enhancements, thoroughly analyze:
- `massive_nonprice_ta_optimizer.py` - understand current single-file architecture
- Success of MB_KDJ_[10,2] strategy (Sharpe 3.672)
- 32-core parallel processing implementation
- 9 government data source integrations
- 81 technical indicator calculations

### Enhancement Strategy
- **Preserve First**: Never remove or simplify existing successful features
- **Modular Extraction**: Extract components without changing logic
- **Additive Enhancement**: Only add new capabilities (caching, monitoring, etc.)
- **Backward Compatibility**: Maintain compatibility with existing usage patterns

### Testing Strategy
- **Regression Testing**: Ensure MB_KDJ_[10,2] maintains Sharpe 3.672
- **Performance Testing**: Verify 396 strategies/second baseline is maintained
- **Integration Testing**: Test all 9 data sources and 81 indicators
- **Load Testing**: Verify 32-core parallel processing efficiency

## Configuration Management

### Enhancement Configuration Structure
The enhanced system should use YAML for configuration while preserving all existing settings:

```yaml
# enhanced_config.yml - Preserve ALL existing functionality
data_sources:
  # PRESERVE: All 9 government data sources
  hibor:
    code: "HB"
    name: "HIBOR利率數據"
    enabled: true  # Always true - preserve functionality
    # ENHANCE: Add better error handling
    retry_count: 3
    timeout: 30

  gdp:
    code: "GD"
    name: "GDP數據"
    enabled: true  # Always true - preserve functionality

  # ... preserve all 7 other data sources

indicators:
  # PRESERVE: All 81 indicators
  rsi_series:
    enabled: true  # Always true - preserve functionality
    range_start: 1
    range_end: 300  # Preserve 0-300 coverage

  # ... preserve all other indicator configurations

performance:
  # PRESERVE: 32-core parallel processing
  max_workers: 32

  # ENHANCE: Add new capabilities
  caching:
    enabled: true
    multi_level: true

  monitoring:
    enabled: true
    real_time: true

successful_strategies:
  # PRESERVE: MB_KDJ_[10,2] and other proven strategies
  mb_kdj:
    name: "MB_KDJ_[10,2]"
    expected_sharpe: 3.672  # Preserve this success
    protected: true  # Never modify this strategy
```

## Success Metrics

### Functional Success Metrics (Must Preserve)
- **9 Data Sources**: 100% retention and functionality
- **81 Indicators**: 100% retention and accuracy
- **MB_KDJ Performance**: Sharpe 3.672 or better
- **Processing Speed**: 396 strategies/second or better
- **Parameter Range**: 0-300 complete coverage

### Enhancement Success Metrics (Target)
- **Performance Improvement**: 20-50% faster processing
- **Memory Optimization**: 15-30% less memory usage
- **Cache Hit Rate**: 70%+ for repeated calculations
- **System Reliability**: 99.9% uptime
- **Code Quality**: 90%+ modularization

## Common Pitfalls to Avoid

### Critical Don'ts
- **DON'T** remove any data sources or indicators
- **DON'T** reduce parameter ranges or processing capabilities
- **DON'T** compromise existing successful strategies
- **DON'T** change core optimization algorithms
- **DON'T** sacrifice performance for "simplicity"

### Recommended Enhancements
- **DO** add intelligent caching while preserving logic
- **DO** enhance error handling while maintaining reliability
- **DO** improve monitoring without changing functionality
- **DO** optimize memory usage without reducing capabilities
- **DO** add configuration flexibility while preserving defaults

## When to Ask for Help

Escalate to human oversight if:
- You need to modify core optimization logic
- You're considering removing any data sources or indicators
- Performance enhancements might affect existing success cases
- You're unsure about preserving MB_KDJ_[10,2] performance
- Configuration changes might break existing functionality

## Conclusion

This enhancement project focuses on **improving an already successful system**. Every decision must be evaluated against the question:

**"Does this enhancement preserve the existing success of MB_KDJ_[10,2] (Sharpe 3.672) and all 9 data sources/81 indicators?"**

The goal is to make a world-class system even better through intelligent enhancements, not to compromise its proven success through simplification or replacement.
# Design Document: Real HKMA Data Integration for Non-Price Technical Analysis Optimizer

## Context

This design addresses the critical gap between the massive non-price technical analysis optimizer's fake data generation and the existing real HKMA API infrastructure available in `daily_data_crawler.py`. The optimizer currently uses simulated economic data (`np.random.normal`) which produces unreliable strategy results, while real HKMA APIs are already implemented and proven to work.

## Goals / Non-Goals

### Goals
- Replace 100% of fake government data generation with real HKMA API calls
- Maintain existing optimizer architecture and workflow without breaking changes
- Leverage proven HKMACrawler implementation from daily_data_crawler.py
- Ensure performance degradation is minimal (<2x execution time)
- Provide credible, actionable strategy optimization results
- Implement robust error handling for production reliability

### Non-Goals
- Complete rewrite of the optimizer architecture
- Addition of new technical indicators or strategies
- Major performance optimization beyond what's needed for integration
- User interface changes or new visualization features
- Expansion to other government data sources beyond HKMA

## Decisions

### Decision 1: Extract-Adapt-Integrate Pattern
**What**: Extract the working HKMACrawler from `daily_data_crawler.py`, adapt it for optimizer consumption, and integrate as a standalone module.

**Why**:
- The HKMACrawler is already proven to work with 7 real HKMA endpoints
- Reinventing the API integration would introduce unnecessary risk and duplication
- Adaptation allows for optimizer-specific optimizations while leveraging existing reliability

**Alternatives considered**:
- Direct dependency on daily_data_crawler.py: Rejected due to tight coupling and unnecessary complexity
- Complete rewrite of API integration: Rejected due to high risk and duplicated effort
- External API service: Rejected due to additional complexity and dependency management

### Decision 2: Minimal Architecture Changes
**What**: Keep the existing optimizer workflow and only replace the data source layer.

**Why**:
- The current optimizer architecture (RSI, MACD, Bollinger Bands, etc.) is sound and well-tested
- Strategy optimization logic doesn't need to change - only the data source
- Minimizes risk of breaking existing functionality
- Faster implementation and validation cycle

**Architecture impact**:
```
BEFORE:
generate_real_gov_data() → Technical Indicators → Strategy Optimization

AFTER:
HKMA API Integration → Technical Indicators → Strategy Optimization
```

### Decision 3: Data Source Mapping Strategy
**What**: Direct mapping for available endpoints, intelligent fallback for others.

**Why**:
- HKMA provides 7 high-quality endpoints that directly map to some optimizer data sources
- Not all optimizer data sources have direct HKMA equivalents
- Intelligent fallback ensures complete data coverage while maximizing real data usage

**Mapping Strategy**:
```python
# Direct Mappings (100% Real Data)
'HB' (HIBOR) → hibor_fixing endpoint
'MB' (Monetary Base) → monetary_base endpoint

# Enhanced Mappings (Real Data + Calculations)
Exchange Rate → exchange_rate endpoint (USD/HKD, CNY/HKD)
Liquidity → interbank_liquidity endpoint

# Intelligent Fallbacks (Limited Real Data + Smart Simulation)
'GD', 'RT', 'PT', 'TR', 'TS', 'CP', 'UE' → Use available endpoints + smart interpolation
```

### Decision 4: Performance-First Integration
**What**: Prioritize performance through caching, async calls, and parallel processing.

**Why**:
- Current optimizer execution time is already significant
- Real API calls will add network latency
- Users expect reasonable execution times for strategy optimization

**Performance Optimizations**:
- **Caching**: Cache API responses with TTL to avoid repeated calls
- **Async Processing**: Parallel API calls for multiple data sources
- **Rate Limiting**: Respect HKMA API limits while maximizing throughput
- **Smart Refresh**: Only update data when sources have new information

## Risks / Trade-offs

### Risk 1: API Reliability
**Risk**: HKMA APIs may experience downtime or rate limiting

**Mitigation**:
- Implement robust caching with extended TTL for API failures
- Add graceful degradation to cached data during outages
- Monitor API health and implement alerting
- Provide clear error messages and fallback strategies

### Risk 2: Performance Impact
**Risk**: Real API calls may significantly slow down optimization

**Mitigation**:
- Implement intelligent caching to minimize API calls
- Use async processing to parallelize data retrieval
- Add progress indicators for long-running operations
- Provide performance monitoring and optimization

### Trade-off 1: Real Data Coverage vs. Data Source Mapping
**Trade-off**: Not all optimizer data sources have direct HKMA equivalents

**Approach**:
- Maximize real data usage for available sources (HB, MB, Exchange Rates)
- Implement intelligent interpolation for missing sources using correlated real data
- Clearly document which data sources use real vs. interpolated data
- Provide options to exclude interpolated sources if desired

### Trade-off 2: Integration Complexity vs. Reliability
**Trade-off**: More complex integration provides better reliability but increases development time

**Approach**:
- Start with simple integration using existing HKMACrawler
- Add complexity incrementally based on testing and performance requirements
- Prioritize the most critical data sources first (HIBOR, Monetary Base)
- Use iterative improvement approach

## Migration Plan

### Phase 1: Foundation (Week 1)
**Goal**: Replace core fake data with real API integration

**Steps**:
1. Extract HKMACrawler as standalone module
2. Replace `generate_real_gov_data()` with real API calls for HB and MB
3. Add basic error handling and caching
4. Test with existing optimizer workflow
5. Validate results show realistic improvements

**Success Criteria**:
- HB and MB data sources use 100% real HKMA data
- Optimizer execution time increases <50%
- No breaking changes to existing workflow

### Phase 2: Expansion (Week 2)
**Goal**: Map remaining data sources and enhance reliability

**Steps**:
1. Map exchange rate endpoints to optimizer data sources
2. Implement intelligent interpolation for remaining sources
3. Add comprehensive error handling and retry logic
4. Enhance caching with smart refresh strategies
5. Add API health monitoring

**Success Criteria**:
- All optimizer data sources use at least 50% real data
- API failure scenarios handled gracefully
- Performance impact acceptable (<2x execution time)

### Phase 3: Optimization (Week 3)
**Goal**: Performance optimization and production readiness

**Steps**:
1. Implement async API calls and parallel processing
2. Optimize caching strategies based on usage patterns
3. Add comprehensive monitoring and alerting
4. Complete documentation and deployment preparation
5. Final performance validation and tuning

**Success Criteria**:
- Optimizer performance optimized for production use
- Complete monitoring and observability implemented
- Documentation ready for production deployment

## Open Questions

1. **API Rate Limiting Strategy**: What are the official HKMA API rate limits, and how should we implement rate limiting to respect them while maintaining performance?

2. **Data Source Preferences**: Should users be able to configure which data sources must use real data vs. interpolated data?

3. **Caching Strategy**: What is the optimal TTL for cached HKMA data considering data freshness vs. performance requirements?

4. **Error Handling Policies**: At what point should API failures trigger optimizer termination vs. graceful degradation?

5. **Performance Baselines**: What are the acceptable performance degradation thresholds for real data integration?

6. **Data Quality Thresholds**: What criteria should determine when real data quality is unacceptable and fallback should be triggered?

## Technical Implementation Details

### Data Flow Architecture
```
HKMA API Endpoints (7 sources)
    ↓ [Rate Limiting & Retry]
Data Standardization Layer
    ↓ [Validation & Quality Checks]
Cache Layer (Redis/File)
    ↓ [Smart Refresh Logic]
Optimizer Data Sources (9 sources)
    ↓ [Technical Indicator Calculation]
Strategy Optimization & Results
```

### Key Components

1. **HKMADataIntegration Class**:
   - Wrapper around extracted HKMACrawler
   - Optimized for optimizer consumption patterns
   - Built-in caching and error handling

2. **DataMappingEngine Class**:
   - Maps optimizer data sources to HKMA endpoints
   - Handles interpolation for unmapped sources
   - Configurable mapping strategies

3. **PerformanceOptimizer Class**:
   - Async API call management
   - Parallel processing coordination
   - Cache optimization strategies

4. **QualityController Class**:
   - Data validation and quality scoring
   - Anomaly detection and alerting
   - Fallback trigger management

### Integration Points

**Modified Files**:
- `massive_nonprice_ta_optimizer.py`: Replace fake data generation
- `daily_data_crawler.py`: Extract HKMACrawler (minimal changes)

**New Files**:
- `hkma_data_integration.py`: Core integration module
- `data_mapping_engine.py`: Data source mapping logic
- `performance_optimizer.py`: Performance optimization layer

This design ensures a robust, maintainable integration that maximizes real data usage while preserving the optimizer's existing capabilities and performance characteristics.
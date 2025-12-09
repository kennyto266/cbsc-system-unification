## Context

The current project has evolved into a sophisticated quantitative trading system with multiple successful backtesting implementations. However, code duplication and inconsistency have emerged as issues. We have proven the technical viability with systems like `universal_backtest_sop.py` (delivering 95.5 quality scores) and `correct_data_source_optimizer.py` (achieving 396+ strategies/second performance), but lack a unified framework.

The system processes real data from:
- Central API for stock prices (724 verified 0700.HK records)
- 9 Hong Kong government data sources (HIBOR, HKMA, etc.)
- 81 technical indicators converted from non-price data

Current successful performance:
- HKMA_RSI_245_T_0.5: 95.5 quality score, 2.235 Sharpe ratio
- 540 strategies tested with 100% success rate
- 32-core parallel processing achieving 396 strategies/second

## Goals / Non-Goals

**Goals:**
- Create a unified, reusable backtesting SOP that eliminates code duplication
- Standardize trading logic and performance calculations across all implementations
- Maintain current high-performance characteristics
- Ensure all backtesting uses only verified real data
- Provide consistent, professional reporting formats
- Support rapid development of new strategies with proven framework

**Non-Goals:**
- Replace existing working systems before the new SOP is fully validated
- Change the successful data source configurations
- Modify the proven trading logic patterns
- Alter the existing performance metrics calculations

## Decisions

### 1. Architecture: Modular Component Design
**Decision:** Create a modular SOP framework with separate components for data loading, strategy execution, and report generation.

**Rationale:** The current implementations mix concerns, making them difficult to maintain and extend. A modular design will allow:
- Independent testing of components
- Reuse across different strategies and symbols
- Easier maintenance and debugging
- Clear separation of data, logic, and presentation

### 2. Data Processing: Real Data Validation Layer
**Decision:** Implement a comprehensive data validation layer that ensures only authentic real data is used.

**Rationale:** The project has demonstrated success with real data sources (verified 724 0700.HK records, authentic government statistics). A validation layer will:
- Prevent accidental use of mock data
- Ensure data quality standards are met
- Provide clear error messages for data issues
- Support audit trails for data provenance

**Data Source Coverage:** Support all existing non-price data sources including:
- HIBOR (Hong Kong Interbank Offered Rate)
- HKMA (Hong Kong Monetary Authority) data
- GDP (Gross Domestic Product) statistics
- Trade data and government statistics
- All 9 verified Hong Kong government data sources

### 3. Performance: Preserve 32-Core Parallel Processing
**Decision:** Maintain and optimize the existing parallel processing architecture that achieves 396+ strategies/second.

**Rationale:** The current performance is exceptional and provides significant competitive advantage. The framework will:
- Use ProcessPoolExecutor with configurable worker count
- Implement efficient chunking for memory management
- Provide progress reporting for long-running optimizations
- Optimize for the current 32-core architecture

### 4. Trading Logic: Standardized One-Buy-One-Sell Implementation
**Decision:** Codify the successful one-buy-one-sell logic without HOLD positions as the standard approach.

**Rationale:** The existing implementations have proven the effectiveness of this approach through:
- High quality scores (95.5)
- Consistent Sharpe ratios (>2.0)
- Clear, interpretable signals
- Realistic trading simulation

**Implementation:** All strategies will use unified signal generation rules with consistent buy/sell logic across all non-price data sources.

### 4.1 Parameter Configuration: Fixed Range Standardization
**Decision:** Standardize on fixed parameter range 0-300 with step size 5 (61 individual parameters, 3,721 combinations for 2-parameter strategies) for all optimizations.

**Rationale:**
- Ensures consistency and comparability across all strategies
- Provides sufficient granularity for optimization (61 parameter options per dimension)
- Leverages existing high-performance capabilities (396+ strategies/second)
- Eliminates parameter range confusion across different data sources
- Comprehensive search space while maintaining computational feasibility

**Implementation:** All non-price data sources (HIBOR, HKMA, GDP, Trade Data, etc.) will use the identical parameter configuration for standardized testing.

**Performance Impact:**
- 3,721 combinations × 1 strategy × 32 cores ≈ 9.4 seconds processing time
- Scales proportionally with multiple strategies and data sources
- Well within current system performance capabilities

### 5. Reporting: Dual HTML/JSON Output Format
**Decision:** Standardize on both human-readable HTML reports and machine-readable JSON exports.

**Rationale:** Different stakeholders have different needs:
- HTML reports provide visual analysis and immediate insights
- JSON exports enable programmatic processing and integration
- Consistent formats ensure comparability across strategies
- Supports both manual analysis and automated workflows

## Risks / Trade-offs

### Risk: Performance Regression During Refactoring
**Mitigation:** Implement comprehensive performance benchmarks that must meet or exceed current 396 strategies/second standard. Use profiling tools to identify bottlenecks during development.

### Risk: Data Source Integration Complexity
**Mitigation:** Create adapter pattern for existing data sources. Maintain current data source configurations and add validation layers gradually.

### Risk: Breaking Existing Successful Systems
**Mitigation:** Implement parallel development approach. Keep existing systems running while building the SOP. Validate new framework against known good results before migration.

### Trade-off: Standardization vs. Flexibility
**Decision:** Prioritize standardization for common use cases while providing extension points for specialized strategies. Create configuration system that allows customization without breaking core framework.

### Trade-off: Complexity vs. Maintainability
**Decision:** Accept increased initial complexity in exchange for long-term maintainability. The modular design will pay dividends as the system grows.

## Migration Plan

### Phase 1: Core Framework (Week 1-2)
1. Create `UniversalBacktestSOP` base class with interface definitions
2. Implement data validation layer with existing data sources
3. Build parameter optimization engine with default configurations
4. Create basic test suite with known successful scenarios

### Phase 2: Strategy Execution (Week 2-3)
1. Implement VectorBT integration with parallel processing
2. Port trading logic from existing successful implementations
3. Add performance metrics calculation and quality scoring
4. Optimize for 32-core performance with benchmarking

### Phase 3: Complete Rewrite & Validation (Week 3-4)
1. Build new `UniversalBacktestSOP` system from scratch based on proven patterns
2. Extract and reimplement successful logic from existing systems
3. Validate against known successful results (HKMA_RSI_245_T_0.5, etc.)
4. Performance benchmarking to ensure 396+ strategies/second standard

### Phase 4: Deployment & Replacement (Week 4-5)
1. Finalize new system and deprecate old implementations
2. Create comprehensive documentation and usage examples
3. Implement command-line interface and configuration system
4. Complete system replacement with new standardized framework

### Decommissioning Strategy
- Archive existing successful implementations for reference
- Remove deprecated code after validation completion
- No backward compatibility requirements for new standardized system
- Clean break from old patterns to ensure consistency

## Open Questions

### 1. Configuration Schema Complexity
**Question:** How complex should the configuration system be to support different strategy types while maintaining simplicity?

**Considerations:**
- Current successful systems use relatively simple configurations
- Need flexibility for different indicator types and parameter ranges
- Risk of over-engineering the configuration system

### 2. Testing Strategy
**Question:** What level of test coverage is needed to validate that the new SOP produces identical results to existing systems?

**Considerations:**
- Need to test against known successful strategies (HKMA_RSI_245_T_0.5, etc.)
- Performance testing is critical to maintain 396+ strategies/second
- Integration testing with all data sources required

### 3. Extension Points
**Question:** What extension points should be built into the framework for future strategy types?

**Considerations:**
- Current focus is on RSI-based strategies with proven success
- Need to anticipate other indicator types without over-engineering
- Plugin architecture vs. inheritance hierarchy decision
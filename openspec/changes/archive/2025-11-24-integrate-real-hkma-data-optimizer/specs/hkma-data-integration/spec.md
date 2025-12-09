## ADDED Requirements

### Requirement: HKMA Real Data Integration
The system SHALL replace fake government data generation with real Hong Kong Monetary Authority (HKMA) API data for the massive non-price technical analysis optimizer.

#### Scenario: Successful HKMA API Integration
- **WHEN** the optimizer requests government economic data
- **THEN** the system SHALL retrieve real data from HKMA API endpoints
- **AND** the system SHALL cache API responses with appropriate TTL
- **AND** the system SHALL provide data quality validation and scoring

#### Scenario: API Error Handling
- **WHEN** HKMA API calls fail or experience rate limiting
- **THEN** the system SHALL implement exponential backoff retry logic
- **AND** the system SHALL fall back to cached data if available
- **AND** the system SHALL log appropriate error messages and continue optimization

#### Scenario: Data Source Mapping
- **WHEN** the optimizer requests data for specific economic indicators
- **THEN** the system SHALL map optimizer data sources to appropriate HKMA endpoints
- **AND** the system SHALL implement intelligent interpolation for unmapped sources
- **AND** the system SHALL clearly indicate which data uses real vs. interpolated values

### Requirement: Performance Optimized Data Retrieval
The system SHALL implement performance optimizations to minimize the impact of real API calls on optimizer execution time.

#### Scenario: Parallel API Processing
- **WHEN** multiple government data sources are requested simultaneously
- **THEN** the system SHALL execute API calls in parallel to minimize total retrieval time
- **AND** the system SHALL respect HKMA API rate limits while maximizing throughput
- **AND** the system SHALL provide progress indicators for long-running data collection

#### Scenario: Intelligent Caching Strategy
- **WHEN** HKMA data is requested multiple times within the cache TTL period
- **THEN** the system SHALL return cached data instead of making new API calls
- **AND** the system SHALL implement cache invalidation based on data freshness requirements
- **AND** the system SHALL optimize cache hit rates for common optimization scenarios

### Requirement: Data Quality and Validation
The system SHALL ensure that HKMA API data meets quality standards before use in technical analysis calculations.

#### Scenario: Data Quality Validation
- **WHEN** HKMA API responses are received
- **THEN** the system SHALL validate data structure, format, and completeness
- **AND** the system SHALL detect and flag anomalous data points or patterns
- **AND** the system SHALL provide quality scores for each data source and timeframe

#### Scenario: Data Consistency Checks
- **WHEN** multiple API calls are made for related economic data
- **THEN** the system SHALL verify temporal consistency across data sources
- **AND** the system SHALL detect and handle missing or corrupted data points
- **AND** the system SHALL provide interpolation options for gaps in time series data

### Requirement: Backward Compatibility
The system SHALL maintain backward compatibility with existing optimizer workflow and interfaces.

#### Scenario: Interface Preservation
- **WHEN** existing optimizer code requests government data
- **THEN** the system SHALL provide the same interface and data format as the previous fake data generator
- **AND** the system SHALL not require changes to existing strategy optimization logic
- **AND** the system SHALL maintain the same data source naming and structure conventions

#### Scenario: Configuration Flexibility
- **WHEN** users need to configure data integration preferences
- **THEN** the system SHALL provide options to enable/disable real data integration
- **AND** the system SHALL allow configuration of cache TTL and retry parameters
- **AND** the system SHALL provide options to force real data refresh vs. using cached values

## MODIFIED Requirements

### Requirement: Government Data Source Processing
The massive non-price technical analysis optimizer SHALL process government economic data sources for technical indicator calculations.

#### Scenario: Real Data Processing
- **WHEN** the optimizer fetches government data for technical analysis
- **THEN** the system SHALL retrieve real HKMA API data instead of generating simulated data
- **AND** the system SHALL apply the same technical indicator calculations (RSI, MACD, Bollinger Bands, CCI, KDJ) to real economic data
- **AND** the system SHALL maintain the same parameter ranges and optimization logic as the original implementation

#### Scenario: Data Source Coverage
- **WHEN** processing the 9 optimizer data sources (HB, GD, RT, PT, TR, TS, CP, UE, MB)
- **THEN** the system SHALL use 100% real HKMA data for directly mapped sources (HB, MB, exchange rates)
- **AND** the system SHALL use intelligent interpolation with real data components for remaining sources
- **AND** the system SHALL document the real data percentage for each data source in optimization results

### Requirement: Strategy Optimization Workflow
The system SHALL execute the complete non-price technical analysis optimization workflow using integrated real government data.

#### Scenario: Complete Optimization with Real Data
- **WHEN** users run the massive non-price technical analysis optimizer
- **THEN** the system SHALL execute the same strategy optimization workflow using real HKMA economic data
- **AND** the system SHALL generate strategy performance metrics based on real economic indicators
- **AND** the system SHALL provide comparison metrics between previous fake data and current real data results

#### Scenario: Performance Impact Management
- **WHEN** real data integration impacts optimizer execution performance
- **THEN** the system SHALL measure and report performance changes compared to baseline fake data execution
- **AND** the system SHALL provide optimization recommendations for cache configuration and data refresh strategies
- **AND** the system SHALL ensure execution time remains within acceptable thresholds for interactive use

## REMOVED Requirements

### Requirement: Fake Government Data Generation
**Reason**: The requirement to generate simulated government data using random normal distributions is being replaced with real API data integration.

**Migration**: All references to `generate_real_gov_data()` method will be removed from the massive non-price technical analysis optimizer and replaced with HKMA API integration calls.

### Requirement: Simulated Economic Data Patterns
**Reason**: Simulated economic data patterns using predetermined volatility and trend parameters are no longer needed with real API data.

**Migration**: Configuration parameters for fake data generation (base values, volatility, trend parameters) will be removed from the optimizer configuration and replaced with API endpoint configuration and cache settings.
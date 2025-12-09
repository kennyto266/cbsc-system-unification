## ADDED Requirements

### Requirement: Universal Backtesting SOP
The system SHALL provide a standardized operating procedure for quantitative strategy backtesting that works across all data sources and strategy types.

#### Scenario: Successful SOP Execution
- **WHEN** a user initiates the universal backtesting SOP
- **THEN** the system SHALL load real data from configured sources, execute parameter optimization with parallel processing, and generate standardized performance reports

#### Scenario: Data Validation
- **WHEN** loading data for backtesting
- **THEN** the system SHALL validate data authenticity, reject mock data, and ensure data quality meets defined thresholds

### Requirement: Real Data Only Policy
The system SHALL enforce the use of only real market data and government statistics for all backtesting activities.

#### Scenario: Mock Data Detection
- **WHEN** mock or simulated data is detected in the pipeline
- **THEN** the system SHALL reject the data and log a violation alert

#### Scenario: Real Data Verification
- **WHEN** loading data from any source
- **THEN** the system SHALL verify data authenticity against known data source signatures

### Requirement: Standardized Trading Logic
The system SHALL implement one-buy-one-sell trading logic without HOLD positions as the default across all backtesting engines.

#### Scenario: Signal Generation
- **WHEN** generating trading signals
- **THEN** the system SHALL create non-overlapping buy and sell signals that follow one-buy-one-sell logic

#### Scenario: Position Management
- **WHEN** managing positions during backtesting
- **THEN** the system SHALL not allow HOLD states and ensure positions are either long or flat

### Requirement: Sharpe Ratio Standardization
The system SHALL calculate Sharpe ratio using a 3% risk-free rate as the standard across all performance evaluations.

#### Scenario: Performance Calculation
- **WHEN** calculating strategy performance metrics
- **THEN** the system SHALL use the standardized 3% risk-free rate for Sharpe ratio calculations

#### Scenario: Strategy Comparison
- **WHEN** comparing multiple strategies
- **THEN** the system SHALL ensure all strategies use the same risk-free rate for fair comparison

### Requirement: Fixed Parameter Optimization Framework
The system SHALL use fixed parameter optimization with standardized 0-300 range and step 5 for all strategies.

#### Scenario: Standardized Parameter Grid
- **WHEN** running parameter optimization for any strategy
- **THEN** the system SHALL use the fixed 0-300 range with step 5 (61 individual parameters, 3,721 total combinations for 2-parameter strategies)

#### Scenario: Cross-Source Consistency
- **WHEN** testing strategies across different non-price data sources
- **THEN** the system SHALL apply identical parameter ranges to ensure fair comparison and consistency

#### Scenario: Performance Optimization
- **WHEN** processing 3,721 parameter combinations
- **THEN** the system SHALL leverage 32-core parallel processing to complete optimization within reasonable timeframe

### Requirement: Parallel Processing Performance
The system SHALL maintain high-performance parallel processing capabilities supporting 32-core execution.

#### Scenario: Parallel Execution
- **WHEN** running multiple strategy backtests
- **THEN** the system SHALL distribute work across available CPU cores up to 32 workers

#### Scenario: Performance Monitoring
- **WHEN** executing backtests
- **THEN** the system SHALL report processing speed and maintain current 396+ strategies/second benchmark

### Requirement: Standardized Report Generation
The system SHALL generate consistent HTML and JSON reports for all backtesting results.

#### Scenario: HTML Report Generation
- **WHEN** backtesting completes
- **THEN** the system SHALL generate an HTML report with visualization charts and performance metrics

#### Scenario: JSON Export
- **WHEN** backtesting completes
- **THEN** the system SHALL export results in JSON format with standardized schema for programmatic access

### Requirement: Quality Scoring System
The system SHALL implement a standardized quality scoring mechanism for strategy evaluation.

#### Scenario: Strategy Ranking
- **WHEN** evaluating multiple strategies
- **THEN** the system SHALL calculate quality scores based on Sharpe ratio, total return, max drawdown, and win rate

#### Scenario: Best Practices Selection
- **WHEN** identifying top performing strategies
- **THEN** the system SHALL rank strategies by quality score and provide detailed analysis

## MODIFIED Requirements

### Requirement: Data Source Integration
The system SHALL integrate with all existing data sources including HIBOR, HKMA, and unified government data sources.

#### Scenario: Multi-Source Loading
- **WHEN** initializing the backtesting SOP
- **THEN** the system SHALL load and validate data from all configured data sources (hibor, hkma, unified)

#### Scenario: Data Source Validation
- **WHEN** loading from data sources
- **THEN** the system SHALL verify data completeness and quality for each source before proceeding

### Requirement: VectorBT Integration
The system SHALL leverage VectorBT framework for high-performance backtesting execution.

#### Scenario: VectorBT Portfolio Creation
- **WHEN** executing strategy backtests
- **THEN** the system SHALL use VectorBT Portfolio.from_signals() with proper transaction costs and realistic market assumptions

#### Scenario: Performance Metrics
- **WHEN** calculating strategy metrics
- **THEN** the system SHALL use VectorBT's built-in calculations for returns, volatility, and drawdowns
## MODIFIED Requirements

### Requirement: Non-Price Technical Analysis Data Sources
The massive non-price technical analysis optimizer SHALL utilize government economic data sources for calculating technical indicators and generating trading strategies.

#### Scenario: Real Data Source Integration
- **WHEN** the optimizer initializes government data sources (HB, GD, RT, PT, TR, TS, CP, UE, MB)
- **THEN** the system SHALL replace fake data generation with real HKMA API integration
- **AND** the system SHALL maintain the same data source identifiers and structure for backward compatibility
- **AND** the system SHALL validate that each data source provides sufficient historical data for technical indicator calculations

#### Scenario: Data Source Quality Assurance
- **WHEN** government data is retrieved from HKMA APIs
- **THEN** the system SHALL perform quality checks on data completeness and consistency
- **AND** the system SHALL handle missing or invalid data points through appropriate interpolation or exclusion
- **AND** the system SHALL log data quality metrics for monitoring and debugging purposes

### Requirement: Technical Indicator Calculation on Economic Data
The system SHALL calculate technical indicators (RSI, MACD, Bollinger Bands, CCI, KDJ) using real government economic data instead of simulated values.

#### Scenario: Real Data Technical Analysis
- **WHEN** calculating RSI indicators on HIBOR rate data
- **THEN** the system SHALL use actual HKMA HIBOR time series data with proper rate calculations
- **AND** the system SHALL apply standard RSI formula with configurable periods from 1-300
- **AND** the system SHALL generate realistic overbought/oversold signals based on actual interest rate movements

#### Scenario: Multi-Indicator Strategy Optimization
- **WHEN** optimizing strategy parameters across multiple technical indicators
- **THEN** the system SHALL use real economic data for all indicator calculations
- **AND** the system SHALL maintain the same parameter optimization ranges (RSI: 1-300, MACD: fast 1-50/slow 51-300/signal 1-20, etc.)
- **AND** the system SHALL generate strategy performance metrics based on actual economic data patterns

### Requirement: Strategy Backtesting with Real Economic Data
The optimizer SHALL backtest trading strategies using a combination of real stock price data and real government economic indicators.

#### Scenario: Realistic Performance Metrics
- **WHEN** backtesting strategies using real government data
- **THEN** the system SHALL calculate returns, Sharpe ratios, and drawdowns based on actual economic market conditions
- **AND** the system SHALL provide realistic strategy performance metrics that reflect true economic data patterns
- **AND** the system SHALL identify strategies that perform well under actual economic conditions rather than simulated patterns

#### Scenario: Economic Cycle Analysis
- **WHEN** analyzing strategy performance across different economic conditions
- **THEN** the system SHALL use real monetary base, HIBOR, and exchange rate data to identify economic cycle phases
- **AND** the system SHALL evaluate strategy performance during actual interest rate changes and monetary policy shifts
- **AND** the system SHALL provide insights into strategy robustness under real economic stress scenarios

### Requirement: Optimization Results Validation
The system SHALL validate that optimization results using real data provide credible and actionable trading insights.

#### Scenario: Results Quality Assessment
- **WHEN** optimization completes using real government data
- **THEN** the system SHALL compare key metrics against expected ranges for real market data
- **AND** the system SHALL flag unrealistic performance metrics that may indicate data quality issues
- **AND** the system SHALL provide confidence scores for optimization results based on data quality and coverage

#### Scenario: Benchmark Comparison
- **WHEN** presenting optimization results to users
- **THEN** the system SHALL provide comparison between real data results and previous fake data baseline
- **AND** the system SHALL highlight improvements in result credibility and actionability
- **AND** the system SHALL explain the impact of real data integration on strategy selection and performance expectations

## REMOVED Requirements

### Requirement: Simulated Government Data Generation
**Reason**: The system no longer needs to generate fake economic data using statistical models.

**Migration**: All fake data generation logic including `generate_real_gov_data()` method with random normal distributions, predetermined volatility parameters, and trend simulations will be removed and replaced with HKMA API integration.

### Requirement: Synthetic Economic Data Patterns
**Reason**: Pre-programmed economic data patterns with quarterly effects, trend shifts, and simulated volatility are no longer needed.

**Migration**: Pattern generation code that simulates economic cycles, seasonal effects, and random market movements will be replaced with real API data processing that captures actual economic patterns and market dynamics.
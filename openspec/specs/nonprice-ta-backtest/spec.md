# nonprice-ta-backtest Specification

## Purpose
TBD - created by archiving change gpu-accelerated-0700-backtest. Update Purpose after archive.
## Requirements
### Requirement: HIBOR-RSI Strategy Implementation
The system SHALL implement a GPU-accelerated HIBOR-RSI trading strategy using Hong Kong Interbank Offered Rate data.

#### Scenario: HIBOR-RSI Signal Generation
- **WHEN** executing HIBOR-RSI strategy backtest
- **THEN** it SHALL calculate RSI on HIBOR interest rate data using GPU computation
- **AND** SHALL generate buy signals when RSI crosses below oversold threshold (30)
- **AND** SHALL generate sell signals when RSI crosses above overbought threshold (70)

#### Scenario: HIBOR Trend Confirmation
- **WHEN** generating HIBOR-RSI trading signals
- **THEN** it SHALL calculate HIBOR moving average for trend confirmation
- **AND** SHALL filter RSI signals based on HIBOR trend direction
- **AND** SHALL implement GPU-accelerated parallel computation for multiple timeframes

### Requirement: Monetary Base MACD Strategy
The system SHALL implement a GPU-accelerated MACD strategy using Hong Kong monetary base data as leading economic indicator.

#### Scenario: Monetary Base MACD Calculation
- **WHEN** executing monetary base strategy
- **THEN** it SHALL calculate MACD indicators on monetary base time series
- **AND** SHALL identify monetary expansion/contraction cycles
- **AND** SHALL generate trading signals based on MACD crossovers

#### Scenario: Economic Momentum Detection
- **WHEN** analyzing monetary base changes
- **THEN** it SHALL detect acceleration in monetary base growth
- **AND** SHALL weigh recent changes more heavily than historical patterns
- **AND** SHALL utilize GPU parallel processing for multiple parameter combinations

### Requirement: GPU Backtest Execution
The system SHALL execute GPU-accelerated backtest for non-price technical analysis strategies.

#### Scenario: GPU-Integrated Backtest Pipeline
- **WHEN** executing non-price TA backtest
- **THEN** it SHALL integrate GPU computation results with VectorBT framework
- **AND** SHALL maintain full compatibility with existing backtest metrics
- **AND** SHALL enable rapid parameter iteration using GPU acceleration

#### Scenario: Performance Optimization Execution
- **WHEN** running parameter optimization for non-price strategies
- **THEN** it SHALL leverage GPU parallel processing for multiple parameter sets
- **AND** SHALL provide real-time progress tracking and intermediate results
- **AND** SHALL support early termination strategies based on performance thresholds

### Requirement: Risk Management Integration
The system SHALL integrate comprehensive risk management specifically for non-price TA strategies.

#### Scenario: Economic Indicator Risk Assessment
- **WHEN** applying non-price TA strategies
- **THEN** it SHALL assess economic indicator reliability and stability
- **AND** SHALL implement signal validation using historical indicator performance
- **AND** SHALL adjust strategy exposure based on economic indicator confidence

#### Scenario: Drawdown Control for Economic Strategies
- **WHEN** managing portfolio risk with non-price signals
- **THEN** it SHALL implement dynamic position sizing based on economic volatility
- **AND** SHALL apply stop-loss mechanisms specific to economic indicator failures
- **AND** SHALL calculate maximum drawdown limits based on historical backtest results


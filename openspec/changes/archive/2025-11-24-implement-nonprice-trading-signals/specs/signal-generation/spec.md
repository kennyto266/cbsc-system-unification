# Signal Generation Specification

## ADDED Requirements

### Requirement: MB_KDJ_[10,2] Signal Generation
Generate trading signals using the proven MB_KDJ_[10,2] strategy with Sharpe ratio 3.672.

#### Scenario: Real-time Signal Generation
When monetary base data is updated, the system must:
1. Calculate KDJ indicator with period=10 and smoothing=2
2. Generate BUY signal when KDJ < 20
3. Generate SELL signal when KDJ > 80
4. Output signal within 100ms of data availability

#### Scenario: Multi-Stock Signal Processing
When processing multiple stocks simultaneously, the system must:
1. Generate individual signals for each stock using same monetary base data
2. Apply stock-specific position sizing based on volatility
3. Aggregate portfolio-level signals for risk management
4. Maintain signal consistency across correlated stocks

### Requirement: Technical Indicator Calculations
Implement KDJ indicator calculations on non-price monetary base data.

#### Scenario: KDJ Calculation
When calculating KDJ on monetary base data, the system must:
1. Calculate %K line using 10-period lookback
2. Calculate %D line using 2-period smoothing
3. Calculate %J line based on %K and %D
4. Handle data gaps and missing values gracefully

#### Scenario: Historical Signal Validation
When validating historical signal performance, the system must:
1. Recalculate past signals using historical monetary base data
2. Compare against actual price movements
3. Calculate win rate and signal accuracy metrics
4. Maintain signal generation logs for audit purposes

### Requirement: Data Source Integration
Integrate with Hong Kong government monetary base data sources.

#### Scenario: Real-time Data Processing
When new monetary base data becomes available, the system must:
1. Fetch latest data from government API
2. Validate data completeness and accuracy
3. Update KDJ calculations incrementally
4. Trigger signal evaluation if thresholds are crossed

#### Scenario: Data Quality Assurance
When processing monetary base data, the system must:
1. Detect and handle data anomalies or outliers
2. Implement data validation rules for monetary base values
3. Fall back to cached values if real-time data fails
4. Log data quality issues for monitoring

### Requirement: Signal Output Formatting
Standardize signal output format for system integration.

#### Scenario: Trading Signal Output
When a trading signal is generated, the system must:
1. Output signal type (BUY/SELL/HOLD)
2. Include confidence level based on indicator strength
3. Provide recommended position size
4. Include timestamp and data source metadata

#### Scenario: Alert System Integration
When integrating with alert systems, the system must:
1. Format signals for Telegram notifications
2. Provide email alert options for high-confidence signals
3. Support webhook callbacks for external systems
4. Maintain alert history and frequency controls

### Requirement: Performance Monitoring
Track signal generation performance and effectiveness.

#### Scenario: Signal Performance Metrics
When monitoring signal performance, the system must:
1. Track signal accuracy against market movements
2. Calculate real-time Sharpe ratio using 3% risk-free rate
3. Monitor maximum drawdown and volatility metrics
4. Generate performance reports daily/weekly/monthly

#### Scenario: System Health Monitoring
When monitoring system health, the system must:
1. Track signal generation latency (<100ms target)
2. Monitor data source availability and quality
3. Alert on calculation errors or system failures
4. Maintain uptime and performance statistics
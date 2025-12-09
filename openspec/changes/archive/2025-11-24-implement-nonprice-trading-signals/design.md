# Non-Price Trading Signals System Design

## Architecture Overview

### Core Components

1. **NonPriceSignalGenerator**: Generates trading signals using MB_KDJ_[10,2] strategy
2. **MonetaryBaseDataProcessor**: Processes Hong Kong government monetary base data
3. **RiskManager**: Implements position sizing and drawdown controls
4. **PortfolioManager**: Manages multi-stock positions and allocations
5. **SignalValidator**: Validates signal accuracy and timing

### Data Flow

```
HK Government Data → Monetary Base Processing → KDJ Calculation → Signal Generation → Risk Management → Trading Signal
```

## Strategy Implementation

### MB_KDJ_[10,2] Strategy Details

**Parameters:**
- Monetary Base (MB) data as primary input
- KDJ period: 10 days
- KDJ smoothing: 2 days
- Signal thresholds: 20 (oversold), 80 (overbought)

**Signal Logic:**
1. Calculate KDJ indicator on monetary base data
2. Generate BUY signal when KDJ < 20
3. Generate SELL signal when KDJ > 80
4. Apply risk management filters (position size, drawdown limits)

### Risk Management Framework

**Position Sizing:**
- Base position: 10% of portfolio
- Dynamic adjustment based on volatility
- Maximum exposure: 30% per stock

**Drawdown Protection:**
- Stop loss: 10% from entry price
- Portfolio-level maximum drawdown: 9.16% (proven)
- Daily loss limits: 5%

## Integration Points

### Existing System Integration
- Reuse massive_nonprice_ta_optimizer.py calculation methods
- Integrate with existing HK government data sources
- Connect to real-time stock price API (18.180.162.113:9191)
- Use proven Sharpe calculation with 3% risk-free rate

### External Systems
- Trading execution APIs (future expansion)
- Alert systems (Telegram, email)
- Portfolio tracking dashboards

## Performance Optimization

### Calculation Efficiency
- Pre-computed KDJ values for common periods
- Batch processing for multiple stocks
- Cached monetary base data with incremental updates

### Latency Management
- Signal generation within 100ms of data availability
- Position updates every trading session
- Real-time risk monitoring

## Scalability Considerations

### Multi-Stock Support
- Parallel signal generation across stocks
- Individual risk parameters per stock
- Portfolio-level aggregation and monitoring

### Data Source Expansion
- Framework for adding new non-price data sources
- Configurable indicator combinations
- A/B testing for strategy variants
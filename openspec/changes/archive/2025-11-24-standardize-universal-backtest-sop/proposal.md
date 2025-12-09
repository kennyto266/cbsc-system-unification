# Change: Standardize Universal Backtesting SOP

## Why
The current project has multiple backtesting implementations with inconsistent approaches, leading to code duplication and maintenance complexity. While we have successful systems like `universal_backtest_sop.py` and `correct_data_source_optimizer.py` that deliver excellent results (95.5 quality scores, 2.235 Sharpe ratios), we need a standardized, reusable SOP that can be applied across all strategies and data sources.

## What Changes
- Create a unified Standard Operating Procedure (SOP) for backtesting that works with all real data sources
- Standardize the one-buy-one-sell trading logic without HOLD positions across all backtesting engines
- Implement proper Sharpe ratio calculation with 3% risk-free rate as the standard
- Create a configurable parameter optimization framework (0-300 range with step 5 as default)
- Ensure all backtesting uses only real data (no mock data) with proper validation
- Standardize report generation and visualization output formats
- Create modular components that can be reused across different strategies and symbols

## Impact
- **Affected specs:** `backtest/` (new capability), `data-sources/` (integration)
- **Affected code:** 
  - `universal_backtest_sop.py` (refactor into standardized SOP)
  - `correct_data_source_optimizer.py` (integrate with standard SOP)
  - `src/backtest/` (enhance with new standard interface)
  - `src/shared/indicators/` (standardized indicator processing)
- **Benefits:** 
  - Eliminate code duplication across multiple backtesting implementations
  - Ensure consistent results and reporting formats
  - Enable rapid strategy development with proven backtesting framework
  - Maintain the excellent performance characteristics (396+ strategies/second)
  - Support all existing data sources (HIBOR, HKMA, unified government data)
- **Performance impact:** Maintain or improve current 32-core parallel processing capabilities
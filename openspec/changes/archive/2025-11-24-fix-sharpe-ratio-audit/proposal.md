# Change: Fix Sharpe Ratio Calculation and Full System Audit

## Why
Critical mathematical error discovered in Sharpe Ratio calculation affecting all 24,044 strategy evaluations. Current implementation uses incorrect risk-free rate conversion, wrong annualization factors, and non-standard statistical methods, potentially invalidating all "world-class" strategy claims including the purported Sharpe 3.672 MB_KDJ_[10,2] strategy.

## What Changes
- **BREAKING**: Replace all Sharpe Ratio calculations with industry-standard methods
- Implement professional financial libraries (empyrical, quantlib) for validation
- Recalculate all 24,044 strategy performances with corrected metrics
- Add comprehensive calculation validation and testing framework
- Update all results files, documentation, and performance claims
- Implement ongoing calculation integrity monitoring

## Impact
- **Affected specs**: quantitative-analysis, strategy-evaluation, risk-metrics
- **Affected code**:
  - `massive_nonprice_ta_optimizer.py:421-428` (core calculation error)
  - All strategy result files (`massive_nonprice_ta_results_*.json`)
  - Performance documentation and claims
- **Risk**: All current strategy rankings and performance metrics may be invalid
- **Timeline**: 2-4 weeks for complete system audit and recalculation
- **Data**: All 24,044 strategies require full recalculation
# Change: Integrate VectorBT for High-Performance Backtesting

## Why
The current custom backtesting implementation using NumPy/Pandas has achieved excellent results (Sharpe 3.369, 120.14% returns) but faces performance limitations for large-scale parameter optimization. VectorBT offers industry-standard vectorized backtesting that can provide 4-10x performance improvements and professional-grade metrics standardization while maintaining our existing parameter space and entry condition systems.

## What Changes
- Integrate VectorBT core engine for strategy backtesting
- Replace custom technical indicator calculations with VectorBT's optimized implementations
- Maintain existing parameter space design (0-300 range, step 5) and three-tier entry conditions
- Add GPU acceleration support for large-scale parameter optimization
- Upgrade performance metrics to VectorBT professional standards
- Preserve all existing data integration (0700.HK + government data)

**BREAKING**: Strategy implementation interface changes - internal refactoring only, no API changes for users.

## Impact
- Affected capabilities: strategy-backtest-implementation
- Affected code: `strategy_backtest_implementations.py`
- Performance improvement: 4-10x speed increase expected
- Dependencies: Add vectorbt library requirement
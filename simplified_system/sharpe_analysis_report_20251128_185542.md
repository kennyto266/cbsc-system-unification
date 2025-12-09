# Sharpe Ratio Analysis Report

Generated: 2025-11-28 18:55:42

## Problematic Files

### 0700_hk_alpha_optimization_20251127_141138.json
- Unrealistic Sharpe ratios: 5
- Maximum Sharpe: 23.390

## Recommended Fixes

1. **Sharpe Formula Verification**:
   ```python
   # Correct formula:
   excess_returns = returns - risk_free_rate / 252
   sharpe = excess_returns.mean() / excess_returns.std() * sqrt(252)
   ```

2. **Risk-Free Rate**: Use 3% annual rate (0.03)
3. **Annualization**: Use sqrt(252) for daily returns
4. **Data Quality**: Ensure sufficient data points (>30 days)

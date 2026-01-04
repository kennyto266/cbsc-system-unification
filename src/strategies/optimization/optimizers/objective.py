# src/strategies/optimization/optimizers/objective.py
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

class ObjectiveFunction:
    """
    Objective function for strategy optimization

    Score = α × Sharpe Ratio - β × Max Drawdown + γ × Calmar Ratio
    """

    def __init__(self, alpha: float = 0.5, beta: float = 0.3, gamma: float = 0.2,
                 risk_free_rate: float = 0.02):
        """
        Initialize objective function

        Args:
            alpha: Weight for Sharpe Ratio (default: 0.5)
            beta: Weight for Max Drawdown (default: 0.3)
            gamma: Weight for Calmar Ratio (default: 0.2)
            risk_free_rate: Annual risk-free rate (default: 0.02)
        """
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.risk_free_rate = risk_free_rate

    def calculate_score(self, returns: pd.Series) -> float:
        """
        Calculate composite optimization score

        Args:
            returns: Series of returns (daily or needs annualization)

        Returns:
            Composite score (higher is better)
        """
        if len(returns) < 2:
            return 0.0

        # Calculate metrics
        sharpe = self._calculate_sharpe_ratio(returns)
        mdd = self._calculate_max_drawdown(returns)
        calmar = self._calculate_calmar_ratio(returns, mdd)

        # Handle edge cases
        if np.isnan(sharpe) or np.isinf(sharpe):
            sharpe = 0.0
        if np.isnan(mdd) or mdd == 0:
            mdd = 0.0001  # Avoid division by zero
        if np.isnan(calmar) or np.isinf(calmar):
            calmar = 0.0

        # Calculate composite score
        score = (
            self.alpha * sharpe
            - self.beta * abs(mdd)
            + self.gamma * calmar
        )

        return float(score)

    def _calculate_sharpe_ratio(self, returns: pd.Series) -> float:
        """Calculate annualized Sharpe Ratio"""
        if len(returns) < 2:
            return 0.0

        # Annualize (assuming daily returns)
        mean_return = returns.mean() * 252
        std_return = returns.std() * np.sqrt(252)

        if std_return == 0:
            return 0.0

        sharpe = (mean_return - self.risk_free_rate) / std_return
        return sharpe

    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Calculate Maximum Drawdown"""
        if len(returns) < 2:
            return 0.0

        # Calculate cumulative returns
        cumulative = (1 + returns).cumprod()

        # Calculate running maximum
        running_max = cumulative.expanding().max()

        # Calculate drawdown
        drawdown = (cumulative - running_max) / running_max

        # Maximum drawdown
        mdd = drawdown.min()

        return float(mdd)

    def _calculate_calmar_ratio(self, returns: pd.Series,
                               mdd: float = None) -> float:
        """Calculate Calmar Ratio (annual return / abs(max drawdown))"""
        if len(returns) < 2:
            return 0.0

        # Annualized return
        annual_return = (1 + returns.mean()) ** 252 - 1

        # Use provided MDD or calculate
        if mdd is None:
            mdd = self._calculate_max_drawdown(returns)

        if abs(mdd) < 0.0001:  # Avoid division by zero
            return 0.0

        calmar = annual_return / abs(mdd)
        return float(calmar)

    def calculate_metrics(self, returns: pd.Series) -> Dict[str, float]:
        """
        Calculate all individual metrics

        Returns:
            Dictionary with Sharpe, MDD, Calmar, and composite score
        """
        if len(returns) < 2:
            return {
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'calmar_ratio': 0.0,
                'composite_score': 0.0,
                'total_return': 0.0,
                'win_rate': 0.0
            }

        sharpe = self._calculate_sharpe_ratio(returns)
        mdd = self._calculate_max_drawdown(returns)
        calmar = self._calculate_calmar_ratio(returns, mdd)
        score = self.calculate_score(returns)

        return {
            'sharpe_ratio': float(sharpe) if not np.isnan(sharpe) else 0.0,
            'max_drawdown': float(mdd) if not np.isnan(mdd) else 0.0,
            'calmar_ratio': float(calmar) if not np.isnan(calmar) else 0.0,
            'composite_score': float(score) if not np.isnan(score) else 0.0,
            'total_return': float(((1 + returns).prod() - 1)) if not np.isnan(returns.sum()) else 0.0,
            'win_rate': float((returns > 0).sum() / len(returns)) if len(returns) > 0 else 0.0
        }

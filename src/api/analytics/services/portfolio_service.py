"""
Portfolio analysis service for analytics API
"""
import asyncio
import numpy as np
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
from decimal import Decimal
from dataclasses import dataclass
import logging

from ..models.analytics import (
    PortfolioOverview,
    AssetAllocation,
    SectorAllocation
)

logger = logging.getLogger(__name__)


@dataclass
class RebalancingSuggestion:
    """Rebalancing suggestion for an asset"""
    symbol: str
    current_weight: float
    target_weight: float
    action: str  # 'buy' or 'sell'
    amount: Decimal


class PortfolioAnalysisService:
    """Service for portfolio analysis and allocation"""

    def __init__(self):
        # Sector mapping for common stock symbols
        self.sector_mapping = {
            "AAPL": "Technology",
            "MSFT": "Technology",
            "GOOGL": "Technology",
            "AMZN": "Consumer Discretionary",
            "TSLA": "Consumer Discretionary",
            "NVDA": "Technology",
            "META": "Technology",
            "BRK.B": "Financial Services",
            "JPM": "Financial Services",
            "JNJ": "Healthcare",
            "UNH": "Healthcare",
            "PG": "Consumer Staples",
            "KO": "Consumer Staples",
            "WMT": "Consumer Staples",
            "XOM": "Energy",
            "CVX": "Energy",
            "BA": "Industrials",
            "CAT": "Industrials",
        }

    async def get_portfolio_overview(
        self,
        user_id: int,
        holdings: List[Dict],
        cash_balance: Decimal,
        historical_data: Optional[List[Dict]] = None
    ) -> PortfolioOverview:
        """
        Generate comprehensive portfolio overview

        Args:
            user_id: User identifier
            holdings: List of position holdings
            cash_balance: Current cash balance
            historical_data: Optional historical portfolio values

        Returns:
            PortfolioOverview with analysis
        """
        try:
            # Calculate allocations
            asset_allocations, sector_allocations = self._calculate_allocations(holdings)

            # Calculate portfolio metrics
            total_value = sum(h['value'] for h in holdings) + cash_balance
            invested_amount = sum(h['cost_basis'] * h['quantity'] for h in holdings)

            # Calculate performance
            today_change = self._calculate_daily_change(holdings)
            today_change_pct = (today_change / (total_value - today_change)) * 100 if total_value > today_change else 0
            total_return = total_value - invested_amount
            total_return_pct = (total_return / invested_amount) * 100 if invested_amount > 0 else 0

            # Identify top performers
            top_gainers, top_losers = self._identify_top_performers(holdings)

            return PortfolioOverview(
                user_id=user_id,
                total_value=Decimal(str(total_value)),
                cash_balance=cash_balance,
                invested_amount=Decimal(str(invested_amount)),
                asset_allocations=asset_allocations,
                sector_allocations=sector_allocations,
                today_change=Decimal(str(today_change)),
                today_change_pct=Decimal(str(today_change_pct)),
                total_return=Decimal(str(total_return)),
                total_return_pct=Decimal(str(total_return_pct)),
                top_gainers=top_gainers[:5],  # Top 5
                top_losers=top_losers[:5],   # Bottom 5
                last_updated=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"Error generating portfolio overview: {e}")
            raise

    def _calculate_allocations(
        self,
        holdings: List[Dict]
    ) -> Tuple[List[AssetAllocation], List[SectorAllocation]]:
        """Calculate asset and sector allocations"""
        total_value = sum(h['value'] for h in holdings)

        # Asset allocations
        asset_allocations = []
        for holding in holdings:
            weight = (holding['value'] / total_value) * 100 if total_value > 0 else 0
            asset_allocations.append(AssetAllocation(
                symbol=holding['symbol'],
                name=holding.get('name', holding['symbol']),
                value=Decimal(str(holding['value'])),
                weight=Decimal(str(weight)),
                sector=self._get_sector(holding['symbol'])
            ))

        # Sector allocations
        sector_totals = {}
        for allocation in asset_allocations:
            sector = allocation.sector or "Other"
            if sector not in sector_totals:
                sector_totals[sector] = 0
            sector_totals[sector] += float(allocation.value)

        sector_allocations = []
        for sector, value in sector_totals.items():
            weight = (value / total_value) * 100 if total_value > 0 else 0
            sector_allocations.append(SectorAllocation(
                sector=sector,
                weight=Decimal(str(weight)),
                value=Decimal(str(value))
            ))

        return asset_allocations, sector_allocations

    def _get_sector(self, symbol: str) -> Optional[str]:
        """Get sector for a symbol"""
        return self.sector_mapping.get(symbol.upper())

    def _calculate_daily_change(self, holdings: List[Dict]) -> float:
        """Calculate daily change in portfolio value"""
        total_change = 0
        for holding in holdings:
            # For demo purposes, use a simple change calculation
            # In real implementation, this would use today's price change
            daily_return = holding.get('daily_return', 0)
            change = holding['value'] * daily_return
            total_change += change
        return total_change

    def _identify_top_performers(
        self,
        holdings: List[Dict]
    ) -> Tuple[List[AssetAllocation], List[AssetAllocation]]:
        """Identify top gaining and losing assets"""
        assets_with_returns = []

        for holding in holdings:
            daily_return = holding.get('daily_return', 0)
            if daily_return != 0:
                assets_with_returns.append({
                    'symbol': holding['symbol'],
                    'name': holding.get('name', holding['symbol']),
                    'value': holding['value'],
                    'daily_return': daily_return
                })

        # Sort by daily return
        sorted_assets = sorted(assets_with_returns, key=lambda x: x['daily_return'], reverse=True)

        # Create AssetAllocation objects
        gainers = []
        losers = []

        for asset in sorted_assets[:10]:  # Top 10
            allocation = AssetAllocation(
                symbol=asset['symbol'],
                name=asset['name'],
                value=Decimal(str(asset['value'])),
                weight=Decimal('0'),  # Not needed for this context
                sector=None
            )
            if asset['daily_return'] > 0:
                gainers.append(allocation)
            else:
                losers.append(allocation)

        return gainers, losers

    async def generate_rebalancing_suggestions(
        self,
        current_allocations: List[AssetAllocation],
        target_allocations: Dict[str, float],  # symbol -> target_weight
        total_portfolio_value: Decimal
    ) -> List[RebalancingSuggestion]:
        """
        Generate rebalancing suggestions

        Args:
            current_allocations: Current asset allocations
            target_allocations: Target allocation weights (percentages)
            total_portfolio_value: Total portfolio value

        Returns:
            List of rebalancing suggestions
        """
        suggestions = []

        for allocation in current_allocations:
            symbol = allocation.symbol
            current_weight = float(allocation.weight)
            target_weight = target_allocations.get(symbol, current_weight)

            # Only suggest if difference is significant (>1%)
            if abs(current_weight - target_weight) > 1.0:
                current_value = float(allocation.value)
                target_value = total_portfolio_value * (target_weight / 100)

                if current_value < target_value:
                    # Need to buy
                    action = "buy"
                    amount = Decimal(str(target_value - current_value))
                else:
                    # Need to sell
                    action = "sell"
                    amount = Decimal(str(current_value - target_value))

                suggestions.append(RebalancingSuggestion(
                    symbol=symbol,
                    current_weight=current_weight,
                    target_weight=target_weight,
                    action=action,
                    amount=amount
                ))

        # Sort by absolute difference (priority)
        suggestions.sort(key=lambda x: abs(x.current_weight - x.target_weight), reverse=True)

        return suggestions

    async def calculate_portfolio_risk(
        self,
        allocations: List[AssetAllocation],
        correlation_matrix: Optional[np.ndarray] = None,
        volatilities: Optional[List[float]] = None
    ) -> Dict:
        """
        Calculate portfolio risk metrics

        Args:
            allocations: Asset allocations
            correlation_matrix: Correlation matrix between assets
            volatilities: Asset volatilities

        Returns:
            Dictionary with risk metrics
        """
        if not allocations:
            return {}

        weights = [float(a.weight) / 100 for a in allocations]  # Convert to decimal

        # Simple risk calculation (without correlation matrix)
        if not correlation_matrix or not volatilities:
            portfolio_volatility = np.average([v for v in volatilities] if volatilities else [0.2] * len(weights))
        else:
            # Full portfolio variance calculation
            weights_array = np.array(weights)
            vol_array = np.array(volatilities)
            cov_matrix = np.outer(vol_array, vol_array) * correlation_matrix
            portfolio_variance = np.dot(weights_array, np.dot(cov_matrix, weights_array))
            portfolio_volatility = np.sqrt(portfolio_variance)

        # Calculate risk metrics
        risk_metrics = {
            "portfolio_volatility": portfolio_volatility,
            "annualized_volatility": portfolio_volatility * np.sqrt(252),  # Annualize
            "value_at_risk_95": portfolio_volatility * 1.65,  # 95% VaR
            "expected_shortfall_95": portfolio_volatility * 2.33,  # 95% ES
            "max_drawdown_estimate": portfolio_volatility * 2.0,  # Rough estimate
        }

        return risk_metrics

    async def analyze_diversification(
        self,
        allocations: List[AssetAllocation]
    ) -> Dict:
        """
        Analyze portfolio diversification

        Args:
            allocations: Asset allocations

        Returns:
            Diversification metrics
        """
        if not allocations:
            return {}

        weights = [float(a.weight) for a in allocations]

        # Concentration metrics
        top_10_weight = sum(sorted(weights, reverse=True)[:10])
        herfindahl_index = sum(w**2 for w in weights)

        # Effective number of assets
        effective_assets = 1 / herfindahl_index if herfindahl_index > 0 else 0

        # Sector diversification
        sectors = {}
        for allocation in allocations:
            sector = allocation.sector or "Other"
            if sector not in sectors:
                sectors[sector] = 0
            sectors[sector] += float(allocation.weight)

        sector_concentration = max(sectors.values()) if sectors else 0

        diversification_metrics = {
            "total_assets": len(allocations),
            "effective_assets": effective_assets,
            "top_10_weight": top_10_weight,
            "herfindahl_index": herfindahl_index,
            "sector_count": len(sectors),
            "largest_sector_weight": sector_concentration,
            "diversification_score": min(100, effective_assets * 10),  # Simple score
        }

        return diversification_metrics
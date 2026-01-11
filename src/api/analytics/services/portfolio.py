"""
Portfolio Analytics Service
Handles portfolio-level analytics and aggregations
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text, func

from ..models import (
    PortfolioAnalytics,
    AssetAllocation,
    SectorAllocation
)


class PortfolioService:
    """Service for calculating portfolio analytics"""

    def __init__(self):
        self.confidence_levels = {
            "90%": 1.282,
            "95%": 1.645,
            "99%": 2.326
        }

    async def get_portfolio_analytics(
        self,
        user_id: str,
        include_correlations: bool,
        risk_level: str,
        db: Session
    ) -> PortfolioAnalytics:
        """
        Get comprehensive portfolio analytics

        Args:
            user_id: User identifier
            include_correlations: Whether to include correlation matrix
            risk_level: VaR confidence level
            db: Database session

        Returns:
            PortfolioAnalytics object
        """
        # Get all user strategies
        strategies = await self._get_user_strategies(user_id, db)

        # Get current positions
        positions = await self._get_portfolio_positions(user_id, db)

        # Calculate portfolio value and allocation
        total_value = sum(p['market_value'] for p in positions)
        cash = sum(p['cash'] for p in strategies)
        invested = total_value - cash

        # Get available margin
        available_margin = await self._get_available_margin(user_id, db)

        # Calculate day change
        day_change, day_change_percent = await self._get_portfolio_day_change(
            user_id, total_value, db
        )

        # Calculate total return
        total_return, total_return_percent = await self._get_total_return(
            user_id, db
        )

        # Asset allocation
        assets = self._calculate_asset_allocation(positions, total_value)

        # Sector allocation
        sectors = self._calculate_sector_allocation(assets)

        # Risk metrics
        var_95 = None
        cvar_95 = None
        if risk_level in self.confidence_levels:
            var_95, cvar_95 = await self._calculate_var_cvar(
                positions, self.confidence_levels[risk_level], db
            )

        # Correlation matrix
        correlations = None
        if include_correlations and len(assets) > 1:
            correlations = await self._calculate_correlation_matrix(
                assets, db
            )

        return PortfolioAnalytics(
            total_value=total_value,
            cash=cash,
            invested=invested,
            available_margin=available_margin,
            day_change=day_change,
            day_change_percent=day_change_percent,
            total_return=total_return,
            total_return_percent=total_return_percent,
            assets=assets,
            sectors=sectors,
            var_95=var_95,
            cvar_95=cvar_95,
            correlations=correlations
        )

    async def _get_user_strategies(self, user_id: str, db: Session) -> List[Dict]:
        """Get all strategies for a user"""
        query = text("""
            SELECT
                strategy_id,
                name,
                cash,
                status,
                created_at
            FROM strategies
            WHERE user_id = :user_id
                AND status IN ('active', 'paused')
        """)

        result = db.execute(query, {"user_id": user_id})
        return [dict(row) for row in result]

    async def _get_portfolio_positions(self, user_id: str, db: Session) -> List[Dict]:
        """Get all current positions for user's portfolio"""
        query = text("""
            SELECT
                p.symbol,
                p.name,
                p.quantity,
                p.market_value,
                p.cost_basis,
                p.sector,
                p.daily_change,
                p.daily_change_percent,
                s.strategy_id
            FROM current_positions p
            JOIN strategies s ON p.strategy_id = s.strategy_id
            WHERE s.user_id = :user_id
                AND p.quantity != 0
            ORDER BY p.market_value DESC
        """)

        result = db.execute(query, {"user_id": user_id})
        return [dict(row) for row in result]

    async def _get_available_margin(self, user_id: str, db: Session) -> float:
        """Calculate available margin for user"""
        query = text("""
            SELECT
                SUM(available_margin) as total_margin
            FROM strategy_margin
            WHERE user_id = :user_id
        """)

        result = db.execute(query, {"user_id": user_id})
        row = result.first()
        return float(row['total_margin']) if row else 0.0

    async def _get_portfolio_day_change(
        self,
        user_id: str,
        total_value: float,
        db: Session
    ) -> Tuple[float, float]:
        """Calculate portfolio day change and percentage"""
        query = text("""
            SELECT
                SUM(daily_pnl) as total_pnl
            FROM strategy_daily_pnl
            WHERE user_id = :user_id
                AND date = CURRENT_DATE
        """)

        result = db.execute(query, {"user_id": user_id})
        row = result.first()

        if not row or row['total_pnl'] is None:
            return 0.0, 0.0

        day_change = float(row['total_pnl'])
        day_change_percent = (day_change / total_value) * 100 if total_value > 0 else 0.0

        return day_change, day_change_percent

    async def _get_total_return(self, user_id: str, db: Session) -> Tuple[float, float]:
        """Calculate total portfolio return"""
        query = text("""
            SELECT
                SUM(initial_capital) as total_initial,
                SUM(current_value) as total_current
            FROM portfolio_snapshots
            WHERE user_id = :user_id
        """)

        result = db.execute(query, {"user_id": user_id})
        row = result.first()

        if not row or not row['total_initial']:
            return 0.0, 0.0

        initial = float(row['total_initial'])
        current = float(row['total_current'])
        total_return = current - initial
        total_return_percent = (total_return / initial) * 100 if initial > 0 else 0.0

        return total_return, total_return_percent

    def _calculate_asset_allocation(
        self,
        positions: List[Dict],
        total_value: float
    ) -> List[AssetAllocation]:
        """Calculate asset allocation breakdown"""
        assets = []
        seen_symbols = set()

        for pos in positions:
            if pos['symbol'] in seen_symbols:
                # Aggregate positions for same symbol
                existing = next(a for a in assets if a.symbol == pos['symbol'])
                existing.value += pos['market_value']
                existing.weight = (existing.value / total_value) * 100
                existing.change += pos['daily_change']
                continue

            seen_symbols.add(pos['symbol'])

            # Calculate target weight (could be from user preferences)
            target_weight = self._get_target_weight(pos['symbol'], pos['sector'])

            assets.append(AssetAllocation(
                symbol=pos['symbol'],
                name=pos['name'],
                value=pos['market_value'],
                weight=(pos['market_value'] / total_value) * 100,
                target_weight=target_weight,
                sector=pos['sector'],
                change=pos['daily_change'],
                change_percent=pos['daily_change_percent']
            ))

        return assets

    def _get_target_weight(self, symbol: str, sector: str) -> float:
        """Get target allocation weight for an asset"""
        # This could come from user's allocation preferences
        # Simplified implementation
        sector_targets = {
            "Technology": 35.0,
            "Financial": 15.0,
            "Healthcare": 12.0,
            "Consumer Discretionary": 15.0,
            "Consumer Staples": 7.0,
            "Energy": 5.0,
            "Utilities": 3.0,
            "Real Estate": 5.0,
            "Materials": 3.0
        }
        return sector_targets.get(sector, 10.0)

    def _calculate_sector_allocation(self, assets: List[AssetAllocation]) -> List[SectorAllocation]:
        """Calculate sector allocation breakdown"""
        sectors = {}
        total_value = sum(a.value for a in assets)

        for asset in assets:
            sector = asset.sector
            if sector not in sectors:
                sectors[sector] = {
                    "value": 0,
                    "assets": []
                }

            sectors[sector]["value"] += asset.value
            sectors[sector]["assets"].append(asset.symbol)

        sector_list = []
        for sector_name, data in sectors.items():
            weight = (data["value"] / total_value) * 100
            target_weight = self._get_sector_target_weight(sector_name)

            sector_list.append(SectorAllocation(
                name=sector_name,
                value=data["value"],
                weight=weight,
                target_weight=target_weight,
                assets=data["assets"]
            ))

        return sorted(sector_list, key=lambda s: s.value, reverse=True)

    def _get_sector_target_weight(self, sector: str) -> float:
        """Get target allocation weight for a sector"""
        targets = {
            "Technology": 35.0,
            "Financial": 18.0,
            "Healthcare": 13.0,
            "Consumer Discretionary": 20.0,
            "Consumer Staples": 7.0,
            "Energy": 5.0,
            "Utilities": 3.0,
            "Real Estate": 5.0,
            "Materials": 3.0,
            "Communication Services": 8.0,
            "Industrials": 10.0
        }
        return targets.get(sector, 5.0)

    async def _calculate_var_cvar(
        self,
        positions: List[Dict],
        confidence_level: float,
        db: Session
    ) -> Tuple[float, float]:
        """Calculate Value at Risk and Conditional VaR"""
        # Get historical returns for portfolio
        returns = await self._get_portfolio_returns(positions, db)

        if len(returns) < 30:  # Need sufficient data
            return 0.0, 0.0

        returns_array = np.array(returns)
        portfolio_value = sum(p['market_value'] for p in positions)

        # Calculate VaR
        var_percentile = (1 - confidence_level) * 100
        var_return = np.percentile(returns_array, var_percentile)
        var = portfolio_value * var_return

        # Calculate CVaR (Expected Shortfall)
        cvar_returns = returns_array[returns_array <= var_return]
        cvar_return = np.mean(cvar_returns) if len(cvar_returns) > 0 else var_return
        cvar = portfolio_value * cvar_return

        return var, cvar

    async def _get_portfolio_returns(
        self,
        positions: List[Dict],
        db: Session
    ) -> List[float]:
        """Get historical returns for the current portfolio"""
        if not positions:
            return []

        # Get daily returns for last 252 trading days (1 year)
        query = text("""
            SELECT
                date,
                SUM(daily_return * weight) as portfolio_return
            FROM asset_daily_returns
            WHERE symbol IN :symbols
                AND date >= DATE_SUB(CURRENT_DATE, INTERVAL 1 YEAR)
            GROUP BY date
            ORDER BY date ASC
        """)

        symbols = [p['symbol'] for p in positions]
        weights = {p['symbol']: p['market_value'] for p in positions}
        total_value = sum(weights.values())

        # Normalize weights
        for symbol in weights:
            weights[symbol] = weights[symbol] / total_value

        # This is simplified - actual implementation would join with weights
        result = db.execute(query, {"symbols": symbols})
        returns = [float(row['portfolio_return']) for row in result]

        return returns

    async def _calculate_correlation_matrix(
        self,
        assets: List[AssetAllocation],
        db: Session
    ) -> Dict[str, Dict[str, float]]:
        """Calculate correlation matrix for assets"""
        if len(assets) < 2:
            return {}

        symbols = [a.symbol for a in assets]

        # Get correlation data
        query = text("""
            SELECT
                symbol1,
                symbol2,
                correlation
            FROM asset_correlations
            WHERE symbol1 IN :symbols
                AND symbol2 IN :symbols
        """)

        result = db.execute(query, {"symbols": symbols})

        # Build correlation matrix
        correlations = {}
        for symbol in symbols:
            correlations[symbol] = {symbol: 1.0}  # Self-correlation

        for row in result:
            sym1 = row['symbol1']
            sym2 = row['symbol2']
            corr = float(row['correlation'])

            correlations[sym1][sym2] = corr
            correlations[sym2][sym1] = corr  # Symmetric

        return correlations

    async def get_portfolio_summary(
        self,
        user_id: str,
        db: Session
    ) -> Dict:
        """Get quick portfolio summary"""
        # This would be a lighter version of get_portfolio_analytics
        # Used for dashboard quick stats
        return {
            "total_value": 1000000,
            "day_change": 2500,
            "day_change_percent": 0.25,
            "active_strategies": 8,
            "total_return_percent": 12.5
        }
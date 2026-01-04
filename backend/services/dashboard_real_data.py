"""
Dashboard Real Data Service
使用真實市場數據的 Dashboard 統計服務
"""
import logging
import asyncio
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np
import yfinance as yf

from services.data_validator import DataValidator
from data_config import DataSourceConfig

logger = logging.getLogger(__name__)


class DashboardDataError(Exception):
    """Dashboard 數據錯誤"""
    pass


class DashboardDataService:
    """Dashboard 真實數據服務"""

    def __init__(self, data_config: Optional[DataSourceConfig] = None):
        self.data_config = data_config or DataSourceConfig()
        self.validator = DataValidator()

    async def get_market_overview(self, symbols: List[str]) -> Dict[str, Any]:
        """
        獲取市場概覽數據

        Args:
            symbols: 股票代碼列表 (e.g., ["0700.HK", "AAPL", "0941.HK"])

        Returns:
            市場概覽數據
        """
        try:
            market_data = {}
            total_return = 0.0
            valid_symbols = 0

            for symbol in symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    # 獲取最近數據
                    hist = ticker.history(period="5d", timeout=10)

                    if hist.empty:
                        logger.warning(f"No data for {symbol}")
                        continue

                    # 計算日收益率
                    hist.columns = [col.lower() for col in hist.columns]
                    if len(hist) >= 2:
                        daily_return = (hist['close'].iloc[-1] / hist['close'].iloc[-2] - 1) * 100
                    else:
                        daily_return = 0.0

                    # 獲取股票信息
                    info = ticker.info
                    market_cap = info.get('marketCap', 0) if info else 0

                    market_data[symbol] = {
                        "price": float(hist['close'].iloc[-1]),
                        "change": float(daily_return),
                        "volume": int(hist['volume'].iloc[-1]) if 'volume' in hist.columns else 0,
                        "market_cap": market_cap,
                        "high_52w": info.get('fiftyTwoWeekHigh', 0) if info else 0,
                        "low_52w": info.get('fiftyTwoWeekLow', 0) if info else 0,
                    }

                    total_return += daily_return
                    valid_symbols += 1

                except Exception as e:
                    logger.error(f"Error fetching data for {symbol}: {e}")
                    continue

            # 計算平均收益率
            avg_return = total_return / valid_symbols if valid_symbols > 0 else 0.0

            return {
                "success": True,
                "data": {
                    "symbols": market_data,
                    "avg_daily_return": round(avg_return, 2),
                    "market_status": "open" if self._is_market_open() else "closed",
                    "last_updated": datetime.utcnow().isoformat()
                },
                "data_source": "yahoo_finance",
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting market overview: {e}")
            # 返回模擬數據作為後備
            return self._get_mock_market_overview(symbols)

    async def get_portfolio_performance(
        self,
        holdings: Dict[str, int]  # symbol -> quantity
    ) -> Dict[str, Any]:
        """
        獲取投資組合表現

        Args:
            holdings: 持倉字典 {symbol: quantity}

        Returns:
            投資組合表現數據
        """
        try:
            portfolio_value = 0.0
            cost_basis = 0.0
            holdings_data = []

            for symbol, quantity in holdings.items():
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period="1mo", timeout=10)

                    if hist.empty:
                        continue

                    hist.columns = [col.lower() for col in hist.columns]
                    current_price = hist['close'].iloc[-1]
                    cost_price = hist['open'].iloc[0]  # 一個月前的開盤價作為成本價

                    market_value = current_price * quantity
                    cost = cost_price * quantity
                    profit_loss = market_value - cost
                    profit_loss_pct = (profit_loss / cost * 100) if cost > 0 else 0

                    portfolio_value += market_value
                    cost_basis += cost

                    holdings_data.append({
                        "symbol": symbol,
                        "quantity": quantity,
                        "current_price": float(current_price),
                        "cost_price": float(cost_price),
                        "market_value": float(market_value),
                        "profit_loss": float(profit_loss),
                        "profit_loss_pct": float(profit_loss_pct)
                    })

                except Exception as e:
                    logger.error(f"Error fetching {symbol}: {e}")
                    continue

            total_profit_loss = portfolio_value - cost_basis
            total_profit_loss_pct = (total_profit_loss / cost_basis * 100) if cost_basis > 0 else 0

            return {
                "success": True,
                "data": {
                    "portfolio_value": float(portfolio_value),
                    "cost_basis": float(cost_basis),
                    "total_profit_loss": float(total_profit_loss),
                    "total_profit_loss_pct": float(total_profit_loss_pct),
                    "holdings": holdings_data
                },
                "data_source": "yahoo_finance",
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting portfolio performance: {e}")
            return self._get_mock_portfolio_performance()

    async def get_strategy_performance_summary(
        self,
        strategy_id: str,
        symbol: str = "0700.HK",
        period_days: int = 30
    ) -> Dict[str, Any]:
        """
        獲取策略表現摘要

        Args:
            strategy_id: 策略ID
            symbol: 標的代碼
            period_days: 分析週期（天）

        Returns:
            策略表現摘要
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days)

            ticker = yf.Ticker(symbol)
            hist = ticker.history(
                start=start_date.strftime("%Y-%m-%d"),
                end=end_date.strftime("%Y-%m-%d"),
                timeout=10
            )

            if hist.empty:
                raise Exception(f"No data for {symbol}")

            hist.columns = [col.lower() for col in hist.columns]

            # 計算指標
            total_return = (hist['close'].iloc[-1] / hist['close'].iloc[0] - 1) * 100
            daily_returns = hist['close'].pct_change().dropna()
            volatility = daily_returns.std() * np.sqrt(252) * 100  # 年化波動率
            sharpe_ratio = (daily_returns.mean() / daily_returns.std() * np.sqrt(252)) if daily_returns.std() > 0 else 0

            # 最大回撤
            cummax = hist['close'].cummax()
            drawdown = (hist['close'] - cummax) / cummax * 100
            max_drawdown = drawdown.min()

            return {
                "success": True,
                "data": {
                    "strategy_id": strategy_id,
                    "symbol": symbol,
                    "period_days": period_days,
                    "total_return": float(total_return),
                    "volatility": float(volatility),
                    "sharpe_ratio": float(sharpe_ratio),
                    "max_drawdown": float(max_drawdown),
                    "current_price": float(hist['close'].iloc[-1]),
                    "start_price": float(hist['close'].iloc[0]),
                },
                "data_source": "yahoo_finance",
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting strategy performance: {e}")
            return self._get_mock_strategy_performance(strategy_id)

    def _is_market_open(self) -> bool:
        """檢查市場是否開市"""
        now = datetime.now()
        # 簡單檢查：週末休市
        if now.weekday() >= 5:  # 週六=5, 週日=6
            return False
        # 交易時間 9:30-16:00 (簡化)
        return 9 <= now.hour < 16

    def _get_mock_market_overview(self, symbols: List[str]) -> Dict[str, Any]:
        """後備模擬市場概覽"""
        return {
            "success": True,
            "data": {
                "symbols": {s: {
                    "price": 100.0,
                    "change": 0.0,
                    "volume": 1000000,
                    "market_cap": 1000000000,
                } for s in symbols},
                "avg_daily_return": 0.0,
                "market_status": "unknown",
                "last_updated": datetime.utcnow().isoformat(),
                "warning": "使用模擬數據 - 無法連接 Yahoo Finance"
            },
            "data_source": "mock",
            "timestamp": datetime.utcnow().isoformat()
        }

    def _get_mock_portfolio_performance(self) -> Dict[str, Any]:
        """後備模擬投資組合表現"""
        return {
            "success": True,
            "data": {
                "portfolio_value": 100000.0,
                "cost_basis": 100000.0,
                "total_profit_loss": 0.0,
                "total_profit_loss_pct": 0.0,
                "holdings": [],
                "warning": "使用模擬數據 - 無法連接 Yahoo Finance"
            },
            "data_source": "mock",
            "timestamp": datetime.utcnow().isoformat()
        }

    def _get_mock_strategy_performance(self, strategy_id: str) -> Dict[str, Any]:
        """後備模擬策略表現"""
        return {
            "success": True,
            "data": {
                "strategy_id": strategy_id,
                "symbol": "0700.HK",
                "period_days": 30,
                "total_return": 0.0,
                "volatility": 15.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "current_price": 100.0,
                "start_price": 100.0,
                "warning": "使用模擬數據 - 無法連接 Yahoo Finance"
            },
            "data_source": "mock",
            "timestamp": datetime.utcnow().isoformat()
        }

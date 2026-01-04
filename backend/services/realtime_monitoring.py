"""
Real-Time Monitoring Service
實時監控服務 - 使用真實市場數據
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np
import yfinance as yf

from services.data_validator import DataValidator
from data_config import DataSourceConfig

logger = logging.getLogger(__name__)


class MonitoringDataError(Exception):
    """監控數據錯誤"""
    pass


class RealTimeMonitoringService:
    """實時監控服務"""

    def __init__(self, data_config: Optional[DataSourceConfig] = None):
        self.data_config = data_config or DataSourceConfig()
        self.validator = DataValidator()
        self.cache = {}  # symbol -> data
        self.cache_ttl = 60  # seconds

    async def get_market_watchlist(
        self,
        symbols: List[str]
    ) -> Dict[str, Any]:
        """
        獲取監控列表數據

        Args:
            symbols: 監控股票列表

        Returns:
            監控數據
        """
        try:
            watchlist_data = {}
            now = datetime.utcnow()

            for symbol in symbols:
                # 檢查緩存
                cached = self.cache.get(symbol)
                if cached and (now - cached['timestamp']).total_seconds() < self.cache_ttl:
                    watchlist_data[symbol] = cached['data']
                    continue

                # 獲取新數據
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period="1d", interval="1m", timeout=10)

                    if hist.empty:
                        logger.warning(f"No data for {symbol}")
                        continue

                    hist.columns = [col.lower() for col in hist.columns]
                    latest = hist.iloc[-1]

                    # 計算技術指標
                    data = {
                        "symbol": symbol,
                        "price": float(latest['close']),
                        "change": 0.0,  # 需要對比前一日收盤價
                        "volume": int(latest['volume']),
                        "high": float(latest['high']),
                        "low": float(latest['low']),
                        "open": float(latest['open']),
                        "timestamp": now.isoformat()
                    }

                    # 獲取前一日收盤價計算變化
                    prev_hist = ticker.history(period="5d", timeout=10)
                    if not prev_hist.empty and len(prev_hist) > 1:
                        prev_hist.columns = [col.lower() for col in prev_hist.columns]
                        prev_close = prev_hist['close'].iloc[-2]
                        data['change'] = round((data['price'] - prev_close) / prev_close * 100, 2)
                        data['prev_close'] = float(prev_close)

                    # 緩存數據
                    self.cache[symbol] = {
                        'data': data,
                        'timestamp': now
                    }

                    watchlist_data[symbol] = data

                except Exception as e:
                    logger.error(f"Error fetching {symbol}: {e}")
                    continue

            return {
                "success": True,
                "data": {
                    "watchlist": watchlist_data,
                    "count": len(watchlist_data),
                    "market_status": self._get_market_status()
                },
                "data_source": "yahoo_finance_realtime",
                "cache_info": {
                    "cached": len([s for s in symbols if s in self.cache]),
                    "total": len(symbols)
                }
            }

        except Exception as e:
            logger.error(f"Market watchlist error: {e}")
            raise MonitoringDataError(f"Failed to get watchlist data: {str(e)}")

    async def get_strategy_monitoring_data(
        self,
        strategy_id: str,
        symbols: List[str]
    ) -> Dict[str, Any]:
        """
        獲取策略監控數據

        Args:
            strategy_id: 策略ID
            symbols: 相關標的列表

        Returns:
            策略監控數據
        """
        try:
            # 獲取市場數據
            watchlist_result = await self.get_market_watchlist(symbols)

            # 計算策略級別指標
            total_value = 0.0
            profitable_count = 0
            loss_count = 0

            for symbol, data in watchlist_result["data"]["watchlist"].items():
                total_value += data["price"] * 100  # 假設100股
                if data["change"] > 0:
                    profitable_count += 1
                elif data["change"] < 0:
                    loss_count += 1

            win_rate = (profitable_count / len(symbols) * 100) if symbols else 0

            return {
                "success": True,
                "data": {
                    "strategy_id": strategy_id,
                    "total_value": total_value,
                    "profitable_positions": profitable_count,
                    "loss_positions": loss_count,
                    "win_rate": round(win_rate, 1),
                    "positions": watchlist_result["data"]["watchlist"],
                    "market_status": watchlist_result["data"]["market_status"]
                },
                "data_source": "yahoo_finance_realtime",
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Strategy monitoring error: {e}")
            raise MonitoringDataError(f"Failed to get monitoring data: {str(e)}")

    async def get_performance_metrics(
        self,
        strategy_id: str,
        symbol: str,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """
        獲取績效指標

        Args:
            strategy_id: 策略ID
            symbol: 標的代碼
            period_days: 分析週期

        Returns:
            績效指標數據
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
                raise MonitoringDataError(f"No data for {symbol}")

            hist.columns = [col.lower() for col in hist.columns]

            # 計算各種指標
            daily_returns = hist['close'].pct_change().dropna()

            # 波動率
            volatility = daily_returns.std() * np.sqrt(252)

            # 最大回撤
            cummax = hist['close'].cummax()
            drawdown = (hist['close'] - cummax) / cummax
            max_drawdown = drawdown.min()

            # 夏普比率（假設無風險利率為3%）
            risk_free_rate = 0.03 / 252  # 日無風險利率
            excess_returns = daily_returns - risk_free_rate
            sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252) if excess_returns.std() > 0 else 0

            # 總收益率
            total_return = (hist['close'].iloc[-1] / hist['close'].iloc[0] - 1)

            # 胜率（假設每日交易）
            winning_days = (daily_returns > 0).sum()
            total_days = len(daily_returns)
            win_rate = (winning_days / total_days * 100) if total_days > 0 else 0

            return {
                "success": True,
                "data": {
                    "strategy_id": strategy_id,
                    "symbol": symbol,
                    "period_days": period_days,
                    "total_return": round(total_return * 100, 2),
                    "annual_return": round(total_return * 100, 2),  # 簡化
                    "volatility": round(volatility * 100, 2),
                    "max_drawdown": round(max_drawdown * 100, 2),
                    "sharpe_ratio": round(sharpe_ratio, 2),
                    "win_rate": round(win_rate, 1),
                    "current_price": float(hist['close'].iloc[-1]),
                    "period_high": float(hist['high'].max()),
                    "period_low": float(hist['low'].min()),
                },
                "data_source": "yahoo_finance",
                "data_points": len(hist),
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Performance metrics error: {e}")
            raise MonitoringDataError(f"Failed to calculate metrics: {str(e)}")

    def _get_market_status(self) -> str:
        """獲取市場狀態"""
        now = datetime.now()

        # 檢查是否是週末
        if now.weekday() >= 5:  # 週六=5, 週日=6
            return "closed"

        # 檢查是否在交易時間
        # 香港市場: 9:30-16:00 HKT
        hour = now.hour
        if 9 <= hour < 16:
            return "open"

        return "closed"

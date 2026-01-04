#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service Interfaces
服務接口定義

定義所有服務的接口契約，實現依賴倒置原則
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


# Type variables for generic responses
T = TypeVar('T')
R = TypeVar('R')


class ServiceResponse(Generic[T]):
    """
    Service response wrapper
    服務響應包裝器
    """

    def __init__(
        self,
        success: bool,
        data: Optional[T] = None,
        error: Optional[str] = None,
        message: Optional[str] = None
    ):
        self.success = success
        self.data = data
        self.error = error
        self.message = message

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'success': self.success,
            'data': self.data,
            'error': self.error,
            'message': self.message
        }

    @classmethod
    def success_response(cls, data: T, message: str = None) -> 'ServiceResponse[T]':
        """Create success response"""
        return cls(success=True, data=data, message=message)

    @classmethod
    def error_response(cls, error: str, message: str = None) -> 'ServiceResponse[T]':
        """Create error response"""
        return cls(success=False, error=error, message=message)


class IService(ABC):
    """
    Base service interface
    基礎服務接口
    """

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize service"""
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown service"""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check service health"""
        pass


class IAuthService(IService):
    """
    Authentication service interface
    認證服務接口
    """

    @abstractmethod
    async def login(self, username: str, password: str) -> ServiceResponse[Dict]:
        """Login user"""
        pass

    @abstractmethod
    async def logout(self, token: str) -> ServiceResponse[None]:
        """Logout user"""
        pass

    @abstractmethod
    async def verify_token(self, token: str) -> ServiceResponse[Dict]:
        """Verify JWT token"""
        pass

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> ServiceResponse[str]:
        """Refresh access token"""
        pass

    @abstractmethod
    async def register(self, username: str, email: str, password: str) -> ServiceResponse[Dict]:
        """Register new user"""
        pass


class IStrategyService(IService):
    """
    Strategy service interface
    策略服務接口
    """

    @abstractmethod
    async def create_strategy(
        self,
        user_id: int,
        name: str,
        strategy_type: str,
        config: Dict
    ) -> ServiceResponse[Dict]:
        """Create new strategy"""
        pass

    @abstractmethod
    async def get_strategy(self, strategy_id: int, user_id: int) -> ServiceResponse[Dict]:
        """Get strategy by ID"""
        pass

    @abstractmethod
    async def list_strategies(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict] = None
    ) -> ServiceResponse[List[Dict]]:
        """List user's strategies"""
        pass

    @abstractmethod
    async def update_strategy(
        self,
        strategy_id: int,
        user_id: int,
        updates: Dict
    ) -> ServiceResponse[Dict]:
        """Update strategy"""
        pass

    @abstractmethod
    async def delete_strategy(self, strategy_id: int, user_id: int) -> ServiceResponse[None]:
        """Delete strategy"""
        pass

    @abstractmethod
    async def execute_strategy(self, strategy_id: int, user_id: int) -> ServiceResponse[Dict]:
        """Execute strategy"""
        pass

    @abstractmethod
    async def stop_strategy(self, strategy_id: int, user_id: int) -> ServiceResponse[None]:
        """Stop strategy execution"""
        pass

    @abstractmethod
    async def get_strategy_status(
        self,
        strategy_id: int,
        user_id: int
    ) -> ServiceResponse[Dict]:
        """Get strategy execution status"""
        pass


class IBacktestService(IService):
    """
    Backtest service interface
    回測服務接口
    """

    @abstractmethod
    async def create_backtest(
        self,
        user_id: int,
        strategy_id: int,
        config: Dict
    ) -> ServiceResponse[Dict]:
        """Create new backtest"""
        pass

    @abstractmethod
    async def run_backtest(
        self,
        backtest_id: int,
        user_id: int
    ) -> ServiceResponse[Dict]:
        """Run backtest"""
        pass

    @abstractmethod
    async def get_backtest(self, backtest_id: int, user_id: int) -> ServiceResponse[Dict]:
        """Get backtest results"""
        pass

    @abstractmethod
    async def list_backtests(
        self,
        user_id: int,
        strategy_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> ServiceResponse[List[Dict]]:
        """List backtests"""
        pass

    @abstractmethod
    async def delete_backtest(self, backtest_id: int, user_id: int) -> ServiceResponse[None]:
        """Delete backtest"""
        pass


class IDataService(IService):
    """
    Data service interface
    數據服務接口
    """

    @abstractmethod
    async def get_market_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = '1d'
    ) -> ServiceResponse[List[Dict]]:
        """Get market data"""
        pass

    @abstractmethod
    async def get_latest_data(self, symbols: List[str]) -> ServiceResponse[Dict]:
        """Get latest market data"""
        pass

    @abstractmethod
    async def subscribe_to_data(
        self,
        symbols: List[str],
        callback: callable
    ) -> ServiceResponse[None]:
        """Subscribe to real-time data updates"""
        pass

    @abstractmethod
    async def unsubscribe_from_data(self, subscription_id: str) -> ServiceResponse[None]:
        """Unsubscribe from data updates"""
        pass


class INotificationService(IService):
    """
    Notification service interface
    通知服務接口
    """

    @abstractmethod
    async def send_notification(
        self,
        user_id: int,
        title: str,
        message: str,
        notification_type: str = 'info'
    ) -> ServiceResponse[None]:
        """Send notification to user"""
        pass

    @abstractmethod
    async def list_notifications(
        self,
        user_id: int,
        unread_only: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> ServiceResponse[List[Dict]]:
        """List user notifications"""
        pass

    @abstractmethod
    async def mark_as_read(self, notification_id: int, user_id: int) -> ServiceResponse[None]:
        """Mark notification as read"""
        pass

    @abstractmethod
    async def mark_all_as_read(self, user_id: int) -> ServiceResponse[None]:
        """Mark all notifications as read"""
        pass


class ICacheService(IService):
    """
    Cache service interface
    緩存服務接口
    """

    @abstractmethod
    async def get(self, key: str) -> ServiceResponse[Any]:
        """Get value from cache"""
        pass

    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> ServiceResponse[None]:
        """Set value in cache"""
        pass

    @abstractmethod
    async def delete(self, key: str) -> ServiceResponse[None]:
        """Delete value from cache"""
        pass

    @abstractmethod
    async def clear(self) -> ServiceResponse[None]:
        """Clear all cache"""
        pass

    @abstractmethod
    async def exists(self, key: str) -> ServiceResponse[bool]:
        """Check if key exists in cache"""
        pass


class IRepository(ABC):
    """
    Base repository interface
    基礎倉儲接口
    """

    @abstractmethod
    async def get(self, id: int) -> ServiceResponse[Dict]:
        """Get entity by ID"""
        pass

    @abstractmethod
    async def list(
        self,
        filters: Optional[Dict] = None,
        skip: int = 0,
        limit: int = 100
    ) -> ServiceResponse[List[Dict]]:
        """List entities"""
        pass

    @abstractmethod
    async def create(self, data: Dict) -> ServiceResponse[Dict]:
        """Create new entity"""
        pass

    @abstractmethod
    async def update(self, id: int, data: Dict) -> ServiceResponse[Dict]:
        """Update entity"""
        pass

    @abstractmethod
    async def delete(self, id: int) -> ServiceResponse[None]:
        """Delete entity"""
        pass

    @abstractmethod
    async def count(self, filters: Optional[Dict] = None) -> ServiceResponse[int]:
        """Count entities"""
        pass

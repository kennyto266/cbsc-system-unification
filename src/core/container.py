#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dependency Injection Container
依賴注入容器

實現依賴注入模式，消除循環依賴，提高可測試性
"""

from typing import AsyncGenerator, Optional
from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject

from .config import settings, get_settings
from .database import AsyncSessionLocal, engine
# Temporarily disabled due to syntax errors
# from .events.event_bus import EventBus, get_event_bus
# from .repository.base_repository import BaseRepository

# Unified services - temporarily disabled
# from ..services.cache_manager import get_cache_manager, CacheManager
# from ..services.unified_auth import AuthService, JWTManager, MFAManager, PasswordManager
# from ..strategies.unified_factory import get_unified_factory, UnifiedStrategyFactory


class CoreContainer(containers.DeclarativeContainer):
    """
    Core dependency injection container
    核心依賴注入容器
    """

    # Configuration
    config = providers.Configuration()

    # Database
    database_engine = providers.Singleton(lambda: engine)
    database_session = providers.Factory(
        lambda: AsyncSessionLocal()
    )

    # Event Bus - temporarily disabled
    # event_bus = providers.Singleton(get_event_bus)

    # Unified Cache Manager - temporarily disabled
    # cache_manager = providers.Singleton(get_cache_manager)

    # Unified Auth Managers - temporarily disabled
    # jwt_manager = providers.Singleton(JWTManager)
    # mfa_manager = providers.Singleton(MFAManager)
    # password_manager = providers.Singleton(PasswordManager)

    # Unified Strategy Factory - temporarily disabled
    # strategy_factory = providers.Singleton(get_unified_factory)


class ServiceContainer(containers.DeclarativeContainer):
    """
    Service layer dependency injection container
    服務層依賴注入容器
    """

    # Core dependencies
    core = providers.Container(CoreContainer)

    # Configuration
    config = providers.Configuration()

    # Repository Layer (will be populated)
    repositories = providers.Dictionary()

    # Service Layer (will be populated)
    services = providers.Dictionary()

    # Unified Auth Service
    auth_service = providers.Factory(
        AuthService,
        db=core.database_session,
        jwt_manager=core.jwt_manager,
        mfa_manager=core.mfa_manager,
        password_manager=core.password_manager
    )

    # Strategy Service
    # strategy_service = providers.Factory(
    #     StrategyService,
    #     db=core.database_session,
    #     event_bus=core.event_bus,
    #     factory=core.strategy_factory,
    #     repository=repositories.strategy_repository
    # )

    # Backtest Service
    # backtest_service = providers.Factory(
    #     BacktestService,
    #     db=core.database_session,
    #     event_bus=core.event_bus,
    #     strategy_service=services.strategy_service
    # )


class APIContainer(containers.DeclarativeContainer):
    """
    API layer dependency injection container
    API 層依賴注入容器
    """

    # Service dependencies
    services = providers.Container(ServiceContainer)

    # Configuration
    config = providers.Configuration()

    # API dependencies (will be populated)
    # routers = providers.Dictionary()


# Global container instances
core_container: Optional[CoreContainer] = None
service_container: Optional[ServiceContainer] = None
api_container: Optional[APIContainer] = None


def init_containers() -> None:
    """
    Initialize all containers
    初始化所有容器
    """
    global core_container, service_container, api_container

    core_container = CoreContainer()
    service_container = ServiceContainer(core=core_container)
    api_container = APIContainer(services=service_container)


def get_core_container() -> CoreContainer:
    """Get core container"""
    if core_container is None:
        init_containers()
    return core_container


def get_service_container() -> ServiceContainer:
    """Get service container"""
    if service_container is None:
        init_containers()
    return service_container


def get_api_container() -> APIContainer:
    """Get API container"""
    if api_container is None:
        init_containers()
    return api_container


# Dependency injection helper functions
@inject
def get_db_session(
    session = Provide[CoreContainer.database_session]
) -> AsyncGenerator:
    """
    Get database session via dependency injection
    通過依賴注入獲取數據庫會話
    """
    return session


@inject
def get_event_bus_service(
    event_bus: EventBus = Provide[CoreContainer.event_bus]
) -> EventBus:
    """
    Get event bus via dependency injection
    通過依賴注入獲取事件總線
    """
    return event_bus


# FastAPI dependency helper
from fastapi import Depends


async def get_db():
    """
    FastAPI dependency for database session
    FastAPI 數據庫會話依賴
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_event_bus() -> EventBus:
    """
    FastAPI dependency for event bus
    FastAPI 事件總線依賴
    """
    from .events.event_bus import get_event_bus as get_global_event_bus
    return get_global_event_bus()


# Unified service helpers via dependency injection
@inject
def get_cache_manager_service(
    cache_manager: CacheManager = Provide[CoreContainer.cache_manager]
) -> CacheManager:
    """Get cache manager via dependency injection"""
    return cache_manager


@inject
def get_jwt_manager_service(
    jwt_manager: JWTManager = Provide[CoreContainer.jwt_manager]
) -> JWTManager:
    """Get JWT manager via dependency injection"""
    return jwt_manager


@inject
def get_mfa_manager_service(
    mfa_manager: MFAManager = Provide[CoreContainer.mfa_manager]
) -> MFAManager:
    """Get MFA manager via dependency injection"""
    return mfa_manager


@inject
def get_password_manager_service(
    password_manager: PasswordManager = Provide[CoreContainer.password_manager]
) -> PasswordManager:
    """Get password manager via dependency injection"""
    return password_manager


@inject
def get_strategy_factory_service(
    strategy_factory: UnifiedStrategyFactory = Provide[CoreContainer.strategy_factory]
) -> UnifiedStrategyFactory:
    """Get strategy factory via dependency injection"""
    return strategy_factory


@inject
def get_auth_service_di(
    auth_service: AuthService = Provide[ServiceContainer.auth_service]
) -> AuthService:
    """Get auth service via dependency injection"""
    return auth_service

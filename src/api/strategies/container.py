"""
Dependency Injection Container
依赖注入容器

Provides centralized dependency management for the strategies module.
"""

from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject

from .repositories.strategy_repository import StrategyRepository
from .repositories.user_repository import UserRepository
from .repositories.execution_repository import ExecutionRepository
from .services.strategy_service import BaseStrategyService
from .services.execution_service import ExecutionService
from .services.personal_service import PersonalService
from .services.websocket_service import WebSocketService
from .services.performance_service import PerformanceService
from .utils.cache import CacheManager
from .utils.validators import StrategyValidator
from .utils.permissions import PermissionManager
from .database.database import Database


class Container(containers.DeclarativeContainer):
    """
    Main dependency injection container for the strategies module
    """

    # Configuration
    config = providers.Configuration()

    # Database
    database = providers.Singleton(
        Database,
        db_url=config.database_url,
    )

    # Cache
    cache_manager = providers.Singleton(
        CacheManager,
        redis_url=config.redis_url,
        default_ttl=config.cache_ttl_default,
    )

    # Validators
    strategy_validator = providers.Factory(
        StrategyValidator,
    )

    # Permission Manager
    permission_manager = providers.Singleton(
        PermissionManager,
    )

    # Repositories
    strategy_repository = providers.Factory(
        StrategyRepository,
        db=database,
        cache=cache_manager,
    )

    user_repository = providers.Factory(
        UserRepository,
        db=database,
        cache=cache_manager,
    )

    execution_repository = providers.Factory(
        ExecutionRepository,
        db=database,
        cache=cache_manager,
    )

    # Services
    base_strategy_service = providers.Factory(
        BaseStrategyService,
        strategy_repo=strategy_repository,
        user_repo=user_repository,
        cache_manager=cache_manager,
        validator=strategy_validator,
    )

    execution_service = providers.Factory(
        ExecutionService,
        execution_repo=execution_repository,
        strategy_repo=strategy_repository,
        cache_manager=cache_manager,
    )

    personal_service = providers.Factory(
        PersonalService,
        strategy_service=base_strategy_service,
        user_repo=user_repository,
        cache_manager=cache_manager,
    )

    performance_service = providers.Factory(
        PerformanceService,
        strategy_repo=strategy_repository,
        execution_repo=execution_repository,
        cache_manager=cache_manager,
    )

    websocket_service = providers.Singleton(
        WebSocketService,
        strategy_service=base_strategy_service,
        execution_service=execution_service,
        permission_manager=permission_manager,
    )


# Global container instance
container = Container()


def init_container(
    database_url: str,
    redis_url: str = "redis://localhost:6379/0",
    cache_ttl_default: int = 300,
):
    """
    Initialize the dependency injection container with configuration
    """
    container.config.database_url.from_value(database_url)
    container.config.redis_url.from_value(redis_url)
    container.config.cache_ttl_default.from_value(cache_ttl_default)

    # Initialize database connection
    db = container.database()
    db.connect()

    # Initialize cache
    cache = container.cache_manager()
    cache.initialize()

    return container


# Convenience injection decorators
@inject
async def get_strategy_service(
    strategy_service: BaseStrategyService = Provide[Container.base_strategy_service],
) -> BaseStrategyService:
    """Inject strategy service"""
    return strategy_service


@inject
async def get_execution_service(
    execution_service: ExecutionService = Provide[Container.execution_service],
) -> ExecutionService:
    """Inject execution service"""
    return execution_service


@inject
async def get_personal_service(
    personal_service: PersonalService = Provide[Container.personal_service],
) -> PersonalService:
    """Inject personal service"""
    return personal_service


@inject
async def get_websocket_service(
    websocket_service: WebSocketService = Provide[Container.websocket_service],
) -> WebSocketService:
    """Inject websocket service"""
    return websocket_service


@inject
async def get_performance_service(
    performance_service: PerformanceService = Provide[Container.performance_service],
) -> PerformanceService:
    """Inject performance service"""
    return performance_service


# Export the container and injection functions
__all__ = [
    "Container",
    "container",
    "init_container",
    "Provide",
    "inject",
    "get_strategy_service",
    "get_execution_service",
    "get_personal_service",
    "get_websocket_service",
    "get_performance_service",
]
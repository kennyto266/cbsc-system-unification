"""
Base Service Classes

Common base classes for all service layers.
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Type, Optional, Dict, Any, List
from datetime import datetime, timezone
import logging

from .config import get_settings
from .exceptions import CBSCError, NotFoundError, ValidationError

T = TypeVar('T')
ModelType = TypeVar('ModelType')
CreateSchemaType = TypeVar('CreateSchemaType')
UpdateSchemaType = TypeVar('UpdateSchemaType')


class BaseService(ABC):
    """
    Base service class with common functionality.
    All services should inherit from this class.
    """

    def __init__(self):
        """Initialize base service"""
        self.settings = get_settings()
        self.logger = logging.getLogger(self.__class__.__name__)

    def log_operation(self, operation: str, **context):
        """Log service operation"""
        self.logger.info(f"{operation}", extra=context)

    def log_error(self, operation: str, error: Exception, **context):
        """Log service error"""
        self.logger.error(f"{operation} failed: {error}", exc_info=error, extra=context)


class BaseServiceWithRepository(Generic[ModelType], ABC):
    """
    Base service class with repository pattern.
    Services that use a single repository should inherit from this.
    """

    def __init__(self, repository):
        """
        Initialize service with repository.

        Args:
            repository: Repository instance
        """
        self.repository = repository
        self.settings = get_settings()
        self.logger = logging.getLogger(self.__class__.__name__)

    async def get_by_id(self, id: str) -> Optional[ModelType]:
        """
        Get entity by ID.

        Args:
            id: Entity ID

        Returns:
            Entity or None if not found
        """
        try:
            entity = await self.repository.get(id)
            if not entity:
                raise NotFoundError(
                    message=f"{self.__class__.__name__.replace('Service', '')} not found",
                    resource_id=id
                )
            return entity
        except Exception as e:
            if isinstance(e, NotFoundError):
                raise
            self.logger.error(f"Failed to get entity by ID {id}: {e}", exc_info=e)
            raise

    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """
        Get multiple entities with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Optional filters

        Returns:
            List of entities
        """
        try:
            return await self.repository.get_multi(skip=skip, limit=limit, filters=filters)
        except Exception as e:
            self.logger.error(f"Failed to get entities: {e}", exc_info=e)
            raise

    async def create(self, data: Dict[str, Any]) -> ModelType:
        """
        Create new entity.

        Args:
            data: Entity data

        Returns:
            Created entity
        """
        try:
            # Validate data before creation
            validation_errors = await self.validate_create(data)
            if validation_errors:
                raise ValidationError(
                    message="Validation failed",
                    details={"errors": validation_errors}
                )

            entity = await self.repository.create(data)
            self.logger.info(f"Created entity with ID: {getattr(entity, 'id', 'unknown')}")
            return entity
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            self.logger.error(f"Failed to create entity: {e}", exc_info=e)
            raise

    async def update(self, id: str, data: Dict[str, Any]) -> Optional[ModelType]:
        """
        Update entity.

        Args:
            id: Entity ID
            data: Update data

        Returns:
            Updated entity or None if not found
        """
        try:
            # Validate data before update
            validation_errors = await self.validate_update(id, data)
            if validation_errors:
                raise ValidationError(
                    message="Validation failed",
                    details={"errors": validation_errors}
                )

            entity = await self.repository.update(id, data)
            if not entity:
                raise NotFoundError(
                    message=f"{self.__class__.__name__.replace('Service', '')} not found",
                    resource_id=id
                )
            self.logger.info(f"Updated entity with ID: {id}")
            return entity
        except Exception as e:
            if isinstance(e, (NotFoundError, ValidationError)):
                raise
            self.logger.error(f"Failed to update entity {id}: {e}", exc_info=e)
            raise

    async def delete(self, id: str) -> bool:
        """
        Delete entity.

        Args:
            id: Entity ID

        Returns:
            True if deleted, False if not found
        """
        try:
            result = await self.repository.delete(id)
            if result:
                self.logger.info(f"Deleted entity with ID: {id}")
            return result
        except Exception as e:
            self.logger.error(f"Failed to delete entity {id}: {e}", exc_info=e)
            raise

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count entities.

        Args:
            filters: Optional filters

        Returns:
            Number of entities
        """
        try:
            return await self.repository.count(filters=filters)
        except Exception as e:
            self.logger.error(f"Failed to count entities: {e}", exc_info=e)
            raise

    # Validation hooks - override in subclasses
    async def validate_create(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate data before creation.

        Args:
            data: Data to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        return []

    async def validate_update(self, id: str, data: Dict[str, Any]) -> List[str]:
        """
        Validate data before update.

        Args:
            id: Entity ID
            data: Data to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        return []


class CachedServiceMixin:
    """
    Mixin for adding caching functionality to services.
    """

    def __init__(self, cache_service=None):
        """
        Initialize with cache service.

        Args:
            cache_service: Cache service instance
        """
        self.cache = cache_service
        self.logger = logging.getLogger(self.__class__.__name__)

    async def get_cached(self, key: str, default=None):
        """Get value from cache"""
        if not self.cache:
            return default
        try:
            value = await self.cache.get(key)
            return value if value is not None else default
        except Exception as e:
            self.logger.warning(f"Cache get failed for key {key}: {e}")
            return default

    async def set_cached(self, key: str, value: Any, ttl: int = 3600):
        """Set value in cache"""
        if not self.cache:
            return
        try:
            await self.cache.set(key, value, ttl=ttl)
        except Exception as e:
            self.logger.warning(f"Cache set failed for key {key}: {e}")

    async def invalidate_cached(self, key: str):
        """Invalidate cache entry"""
        if not self.cache:
            return
        try:
            await self.cache.delete(key)
        except Exception as e:
            self.logger.warning(f"Cache invalidation failed for key {key}: {e}")

    async def invalidate_pattern(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        if not self.cache:
            return
        try:
            # Implementation depends on cache backend
            await self.cache.delete_pattern(pattern)
        except Exception as e:
            self.logger.warning(f"Cache pattern invalidation failed for {pattern}: {e}")


class BusinessRule:
    """Business rule definition"""

    def __init__(
        self,
        name: str,
        description: str,
        validator: callable,
        error_message: str
    ):
        self.name = name
        self.description = description
        self.validator = validator
        self.error_message = error_message


class BusinessRuleMixin:
    """
    Mixin for adding business rule validation to services.
    """

    def __init__(self):
        self.business_rules: List[BusinessRule] = []

    def add_business_rule(self, rule: BusinessRule):
        """Add a business rule"""
        self.business_rules.append(rule)

    async def validate_business_rules(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate all business rules.

        Args:
            data: Data to validate

        Returns:
            List of error messages (empty if all rules pass)
        """
        errors = []
        for rule in self.business_rules:
            try:
                if not rule.validator(data):
                    errors.append(rule.error_message)
            except Exception as e:
                errors.append(f"{rule.name}: Validation error - {str(e)}")
        return errors
